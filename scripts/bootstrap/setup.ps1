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
# codegraph 인덱스·memory 복원 대상은 Claude Code 가 실제 읽는 ~\.claude 로 고정 (RepoRoot 와 분리).
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

# --- 2. node (codegraph npm 전) ---
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

# --- 3b. Codex user-scope skill (stable source survives worktree removal) ---
$CodexSkillSource = Join-Path $ClaudeDir 'skills\jira-worklog'
$CodexSkillTarget = Join-Path $env:USERPROFILE '.agents\skills\jira-worklog'
$CodexSkillInstaller = Join-Path $PSScriptRoot 'install-codex-skill.ps1'
Run "Codex jira-worklog skill 연결: $CodexSkillTarget -> $CodexSkillSource"
$global:LASTEXITCODE = 0
if ($DryRun) {
  & $CodexSkillInstaller -Source $CodexSkillSource -Target $CodexSkillTarget -DryRun
} else {
  & $CodexSkillInstaller -Source $CodexSkillSource -Target $CodexSkillTarget
}
if ($LASTEXITCODE -ne 0) { throw "Codex jira-worklog skill 연결 실패(exit $LASTEXITCODE)" }
Ok 'Codex jira-worklog skill 연결'

# --- 4. codegraph (npm -g) ---
if (Have 'codegraph') { Skip 'codegraph 있음' }
else { Run 'npm install -g @colbymchenry/codegraph'; RunCmd 'npm install -g @colbymchenry/codegraph'; Ok 'codegraph 설치' }

# --- 5. rtk (standalone 설치본 선택) ---
if (Have 'rtk') {
  if ($DryRun) { Skip 'rtk hook 검증/서명(dry-run)' }
  else {
    & rtk verify *> $null
    if ($LASTEXITCODE -eq 0) { Skip 'rtk hook 무결성 OK' }
    else { Run 'rtk init -g --hook-only --no-patch'; RunCmd 'rtk init -g --hook-only --no-patch'; Ok 'rtk hook 등록·서명' }
  }
} else { Skip 'rtk 미설치(선택)' }

# --- 6. MCP 등록 (홈 ~\.claude.json) ---
$mcp = (claude mcp list 2>$null) -join "`n"
if ($mcp -match '(?im)^codegraph') { Skip 'codegraph MCP 등록됨' }
else { Run 'codegraph install -y'; RunCmd 'codegraph install -y'; Ok 'codegraph MCP 등록' }

# --- 7. codegraph init (~\.claude 인덱스) ---
if (Test-Path (Join-Path $ClaudeDir '.codegraph')) { Skip 'codegraph 인덱스 있음' }
else {
  Run "codegraph init $ClaudeDir"
  if ($DryRun) { Write-Host "    (dry-run) codegraph init $ClaudeDir" }
  else { & codegraph init $ClaudeDir; if ($LASTEXITCODE -ne 0) { throw 'codegraph init 실패' } }
  Ok 'codegraph init'
}

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
Ok "부트스트랩 완료. 새 터미널을 열어(레지스트리 env 반영) 'claude' 실행."
