<#
.SYNOPSIS
  Claude Code 환경 부트스트랩 (Windows). setup.sh 의 Windows 대응. idempotent.
.DESCRIPTION
  새 머신에서 한 번 실행하면 도구 + 설정 + (옵션)memory 를 재현한다. 재실행 안전.
  전제: claude(공식 설치), git, winget(또는 choco) 이 이미 있어야 한다.
  rtk 는 별도 standalone 설치본이 있으면 hook 을 검증·서명한다.

  ⚠️ 이 스크립트는 macOS 세션에서 작성돼 Windows 에서 실행 검증되지 않았다(로직·문서 기반).
     Windows 실행 전제와 rtk 설치 경로는 README 의 한계 절 참조.
.PARAMETER MemoryFrom
  기존 머신의 ~\.claude 경로. 지정 시 projects\*\memory\ 복원.
.PARAMETER DryRun
  실제 변경 없이 수행할 동작만 출력.
.EXAMPLE
  pwsh -File scripts\bootstrap\setup.ps1
  pwsh -File scripts\bootstrap\setup.ps1 -MemoryFrom 'D:\backup\.claude'
#>
[CmdletBinding()]
param(
  [string]$MemoryFrom = '',
  [switch]$DryRun
)
$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
# memory 복원·Codex skill source 는 Claude Code 가 실제 읽는 ~\.claude 로 고정 (RepoRoot 와 분리).
$ClaudeDir = Join-Path $env:USERPROFILE '.claude'
$LocalBin = Join-Path $env:USERPROFILE '.local\bin'

function Ok($m)   { Write-Host "[ OK ] $m"   -ForegroundColor Green }
function Skip($m) { Write-Host "[SKIP] $m"   -ForegroundColor DarkGray }
function Warn($m) { Write-Host "[WARN] $m"   -ForegroundColor Yellow }
function Run($m)  { Write-Host "[ .. ] $m"   -ForegroundColor Cyan }
function Have($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
# PATH 포함 검사 (세미콜론 경계 — '...\bin' 이 '...\bin2' 에 오매칭되지 않도록)
function Test-InPath($dir, $pathStr) { return (";$pathStr;") -like "*;$dir;*" }
# native 명령 실행 + 실패(non-zero exit) 시 throw — 부분 실패 은폐 방지 (PS 는 native exit code 로 안 멈춤).
# 'Do' 는 PowerShell 예약어(do{}while)라 함수명으로 못 쓴다 → RunCmd.
function RunCmd($sb) {
  if ($DryRun) { Write-Host "    (dry-run) $sb"; return }
  $global:LASTEXITCODE = 0
  & ([scriptblock]::Create($sb))
  if ($LASTEXITCODE -ne 0) { throw "명령 실패(exit $LASTEXITCODE): $sb" }
}

Write-Host "== Claude Code 환경 부트스트랩 (Windows) =="
Write-Host "   repo: $RepoRoot"
if ($DryRun) { Write-Host "   (DRY-RUN: 실제 변경 없음)" }

# --- 0. 전제: claude / git / winget ---
$prereq = $true
if ((Test-Path (Join-Path $LocalBin 'claude.exe')) -or (Have 'claude')) { Ok 'claude 있음' }
else { Warn 'claude 미설치 — 공식 설치 후 재실행: https://docs.claude.com/claude-code'; $prereq = $false }
if (Have 'git') { Ok 'git 있음' } else { Warn 'git 미설치 — https://git-scm.com'; $prereq = $false }
$pkg = if (Have 'winget') { 'winget' } elseif (Have 'choco') { 'choco' } else { '' }
if ($pkg) { Ok "패키지매니저: $pkg" } else { Warn 'winget/choco 둘 다 없음 — 도구 자동 설치 불가'; $prereq = $false }
if (-not $prereq) { Warn '전제 미충족 — 해결 후 재실행.'; exit 1 }

# --- 1. PATH: ~\.local\bin (현재 프로세스 + User 레지스트리 영속) ---
New-Item -ItemType Directory -Force -Path $LocalBin | Out-Null
$userPath = [Environment]::GetEnvironmentVariable('Path','User')
if (-not (Test-InPath $LocalBin $userPath)) {
  if (-not $DryRun) { [Environment]::SetEnvironmentVariable('Path', "$LocalBin;$userPath", 'User') }
  Ok 'PATH 에 ~\.local\bin 추가(User 영속)'
} else { Skip 'PATH 에 ~\.local\bin 있음' }
if (-not (Test-InPath $LocalBin $env:PATH)) { $env:PATH = "$LocalBin;$env:PATH" }

# --- 2. node (hook 진입점 scripts\*.js 실행) ---
if (Have 'node') { Skip "node 있음 ($(node --version))" }
else {
  if ($pkg -eq 'winget') { Run 'winget install OpenJS.NodeJS'; RunCmd 'winget install -e --id OpenJS.NodeJS' }
  else { Run 'choco install -y nodejs'; RunCmd 'choco install -y nodejs' }
  Ok 'node 설치'
}

# --- 2b. jq (rtk hook 이 stdin JSON 파싱에 의존) ---
if (Have 'jq') { Skip 'jq 있음' }
else {
  if ($pkg -eq 'winget') { Run 'winget install jqlang.jq'; RunCmd 'winget install -e --id jqlang.jq' }
  else { Run 'choco install -y jq'; RunCmd 'choco install -y jq' }
  Ok 'jq 설치'
}

# --- 3. uv (astral) ---
if ((Test-Path (Join-Path $LocalBin 'uv.exe')) -or (Have 'uv')) { Skip 'uv 있음' }
else { Run 'uv 설치 (astral)'; RunCmd 'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'; Ok 'uv 설치' }

# --- 3b. Codex 연결: skill junction + AGENTS.md → CLAUDE.md + agent 정의 생성 (stable source survives worktree removal) ---
# setup.sh 와 같은 목록·순서. 충돌은 건드리지 않고 모아 두었다가 마지막에 exit 1 — Codex 연결은 뒤 단계의 전제가 아니다.
$CodexSkills = @('c', 'dlc', 'e', 'improve', 'jira-worklog', 'wiki', 'wt')
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$CodexLinker = Join-Path $PSScriptRoot 'install-codex-skill.ps1'
$codexFailed = @()
function Invoke-CodexStep([string]$Label, [scriptblock]$Step) {
  $global:LASTEXITCODE = 0
  try {
    & $Step
    if ($LASTEXITCODE -ne 0) { throw "exit $LASTEXITCODE" }
    Ok "Codex $Label"
  } catch {
    Warn "Codex $Label 연결 실패: $($_.Exception.Message)"
    $script:codexFailed += $Label
  }
}
foreach ($name in $CodexSkills) {
  $src = Join-Path $ClaudeDir "skills\$name"
  $dst = Join-Path $env:USERPROFILE ".agents\skills\$name"
  Run "Codex skill 연결: $dst -> $src"
  Invoke-CodexStep "skill:$name" { & $CodexLinker -Source $src -Target $dst -DryRun:$DryRun }
}
$CodexAgents = Join-Path $CodexHome 'AGENTS.md'
Run "Codex AGENTS.md 연결: $CodexAgents -> $ClaudeDir\CLAUDE.md"
Invoke-CodexStep 'AGENTS.md' { & $CodexLinker -File -Source (Join-Path $ClaudeDir 'CLAUDE.md') -Target $CodexAgents -DryRun:$DryRun }
# agent 정의는 링크가 아니라 생성 사본이다 — 원본의 Codex 병행 절이 Codex 안에서 자기 자신을 부르므로 뺀다.
$CodexAgentDir = Join-Path $CodexHome 'agents'
Run "Codex agent 정의 생성: $CodexAgentDir <- $ClaudeDir\agents"
# python.org 설치기는 기본으로 py 런처만 PATH 에 두고, WindowsApps 의 python 은 Store 로 보내는 별칭이다.
$pyCmd = @()
$py = Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*\WindowsApps\*' } | Select-Object -First 1
if ($py) { $pyCmd = @($py.Source) }
elseif (Have 'py') { $pyCmd = @((Get-Command py).Source, '-3') }
if ($pyCmd.Count -eq 0) {
  Warn 'python 없음 — Codex agent 정의 생성 건너뜀'
  $codexFailed += 'agents:python'
} else {
  $syncArgs = @($pyCmd | Select-Object -Skip 1) + @((Join-Path $PSScriptRoot 'sync_codex_agents.py'), '--source', (Join-Path $ClaudeDir 'agents'), '--out', $CodexAgentDir)
  if ($DryRun) { $syncArgs += '--dry-run' }
  # 생성기 출력의 비ASCII(—)가 로캘 코드페이지로 리다이렉트될 때 깨지지 않게 한다.
  $env:PYTHONUTF8 = '1'
  try { Invoke-CodexStep 'agents' { & $pyCmd[0] @syncArgs } } finally { Remove-Item Env:PYTHONUTF8 }
}

# --- 3c. Claude Code 플러그인 (enabledPlugins 는 untracked settings.json 에 있어 머신마다 켠다) ---
# enable·install 은 이미 켜졌거나 설치돼 있어도 성공으로 끝나 다시 돌려도 된다.
# 대화형 세션을 한 번도 연 적 없는 머신에는 공식 marketplace 가 등록돼 있지 않아 install 이 실패한다 — 없을 때만 등록한다.
# 실패는 경고만 남긴다 — $PSNativeCommandUseErrorActionPreference 가 켜진 PS 7.3+ 에서 비0 종료가 Stop 으로 스크립트를 끊지 않게 try/catch 로 감싼다.
function Invoke-PluginStep($Label, [string[]]$CmdArgs, $Hint) {
  Run "claude $($CmdArgs -join ' ')"
  if ($DryRun) { Skip "$Label (dry-run)"; return }
  $global:LASTEXITCODE = 0
  try { & claude @CmdArgs; $rc = $LASTEXITCODE } catch { $rc = 1 }
  if ($rc -eq 0) { Ok $Label } else { Warn "$Label 실패 — $Hint" }
}
if (Have 'claude') {
  $marketplaces = try { (& claude plugin marketplace list 2>$null) -join "`n" } catch { '' }
  if ($marketplaces -match 'claude-plugins-official') { Skip '공식 marketplace 등록됨' }
  else { Invoke-PluginStep '공식 marketplace 등록' @('plugin', 'marketplace', 'add', 'anthropics/claude-plugins-official') '위 claude 출력 참조(네트워크·git)' }
  Invoke-PluginStep 'plugin enable cc-plugin-you-should-know@builtin' @('plugin', 'enable', 'cc-plugin-you-should-know@builtin') 'you-should-know 는 Claude Code 2.1.287 이상이 필요하다'
  foreach ($name in @('session-report', 'receipts')) {
    Invoke-PluginStep "plugin install $name@claude-plugins-official" @('plugin', 'install', "$name@claude-plugins-official") '위 claude 출력 참조(marketplace 등록·네트워크)'
  }
} else {
  Skip 'claude 없음 — 플러그인 설정 건너뜀'
}

# --- 5. rtk (standalone 설치본 선택) ---
if (Have 'rtk') {
  if ($DryRun) { Skip 'rtk hook 검증/서명(dry-run)' }
  else {
    & rtk verify *> $null
    if ($LASTEXITCODE -eq 0) { Skip 'rtk hook 무결성 OK' }
    else { Run 'rtk init -g --hook-only --no-patch'; RunCmd 'rtk init -g --hook-only --no-patch'; Ok 'rtk hook 등록·서명' }
  }
} else { Skip 'rtk 미설치(선택)' }

# --- 8. User env (레지스트리) ---
function Set-UserEnv($name, $val) {
  $cur = [Environment]::GetEnvironmentVariable($name, 'User')
  if ($cur -eq $val) { Skip "env $name 이미 설정" }
  elseif ($DryRun) { Skip "env $name=$val (dry-run)" }
  else { [Environment]::SetEnvironmentVariable($name, $val, 'User'); Ok "env $name 설정" }
}
function Remove-UserEnv($name) {
  $userValue = [Environment]::GetEnvironmentVariable($name, 'User')
  $processValue = [Environment]::GetEnvironmentVariable($name, 'Process')
  if ($null -eq $userValue -and $null -eq $processValue) { Skip "env $name 미설정"; return }
  if ($DryRun) { Skip "env $name 제거(dry-run)"; return }
  [Environment]::SetEnvironmentVariable($name, $null, 'User')
  [Environment]::SetEnvironmentVariable($name, $null, 'Process')
  Ok "env $name 제거"
}
Set-UserEnv 'ANTHROPIC_MODEL' 'opus[1m]'
Remove-UserEnv 'CLAUDE_CODE_EFFORT_LEVEL'

# --- 9. memory 복원 (옵션) ---
if ($MemoryFrom) {
  $src = Join-Path $MemoryFrom 'projects'
  if (Test-Path $src) {
    Run "memory 복원: $src"
    if (-not $DryRun) {
      Get-ChildItem -Path $src -Directory | ForEach-Object {
        $m = Join-Path $_.FullName 'memory'
        if (Test-Path $m) {
          $dst = Join-Path (Join-Path $ClaudeDir "projects\$($_.Name)") 'memory'
          New-Item -ItemType Directory -Force -Path $dst | Out-Null   # dst 선생성 → Copy-Item 중첩(memory\memory) 방지
          Copy-Item (Join-Path $m '*') $dst -Recurse -Force
        }
      }
    }
    Ok 'memory 복원'
  } else { Warn "memory 소스 없음: $src" }
} else { Skip 'memory: -MemoryFrom 미지정 (새 머신은 비어있음)' }

# --- 10. git / gh 안내 ---
if (-not (git config --global user.name 2>$null))  { Warn "git user.name 미설정 — git config --global user.name '...'" }
if (-not (git config --global user.email 2>$null)) { Warn "git user.email 미설정 — git config --global user.email '...'" }
if (Have 'gh') { gh auth status *> $null; if ($LASTEXITCODE -ne 0) { Warn 'gh 미인증 — gh auth login' } }
else { Warn 'gh 미설치 — winget install GitHub.cli' }

Write-Host ''
if ($codexFailed.Count -gt 0) {
  Warn "Codex 연결 실패: $($codexFailed -join ' ') — 원인은 위 installer·생성기 메시지(충돌·python 부재·원본 형식·symlink 권한). 충돌은 scripts/bootstrap/README.md 'Codex 연결 충돌' 절에 따라 정리한 뒤 재실행."
  exit 1
}
Ok "부트스트랩 완료. 새 터미널을 열어(레지스트리 env 반영) 'claude' 실행."
