<#
.SYNOPSIS
  Claude Code 환경 부트스트랩 (Windows). setup.sh 의 Windows 대응. idempotent.
.DESCRIPTION
  새 머신에서 한 번 실행하면 도구 + 설정 + (옵션)memory 를 재현한다. 재실행 안전.
  전제: claude(공식 설치), git, winget(또는 choco) 이 이미 있어야 한다.
  rtk 는 별도 설치가 아니라 headroom 번들(~\.headroom\bin\rtk.exe)을 PATH 노출 + 서명한다.

  ⚠️ 이 스크립트는 macOS 세션에서 작성돼 Windows 에서 실행 검증되지 않았다(로직·문서 기반).
     특히 ① headroom 번들 rtk 의 Windows 경로/PATH 노출 방식 ② headroom install 의
     Windows preset(persistent-task) ③ token mode 압축 timeout(과거 Windows 30s 이력)
     은 실제 실행으로 확인 후 사용할 것. README 의 한계 절 참조.
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

# --- 3. uv (astral) ---
if ((Test-Path (Join-Path $LocalBin 'uv.exe')) -or (Have 'uv')) { Skip 'uv 있음' }
else { Run 'uv 설치 (astral)'; RunCmd 'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'; Ok 'uv 설치' }

# --- 4. headroom (uv tool install) — rtk 번들 전 ---
if (Have 'headroom') { Skip "headroom 있음 ($(headroom --version 2>$null | Select-Object -First 1))" }
else { Run 'uv tool install headroom-ai'; RunCmd 'uv tool install headroom-ai'; Ok 'headroom 설치' }

# --- 5. codegraph (npm -g) ---
if (Have 'codegraph') { Skip 'codegraph 있음' }
else { Run 'npm install -g @colbymchenry/codegraph'; RunCmd 'npm install -g @colbymchenry/codegraph'; Ok 'codegraph 설치' }

# --- 6. rtk (headroom 번들 → PATH 노출 + 서명; memory rtk-headroom-path-fix 규약) ---
# ⚠️ Windows 의 headroom 번들 rtk 경로/PATH 노출은 미검증. 번들 위치 확인 후 PATH 추가가 필요할 수 있다.
$HeadroomRtk = Join-Path $env:USERPROFILE '.headroom\bin\rtk.exe'
if (Test-Path $HeadroomRtk) {
  $rtkDir = Split-Path $HeadroomRtk
  if (-not (Test-InPath $rtkDir $env:PATH)) {
    Run "rtk PATH 노출: $rtkDir"
    if (-not $DryRun) {
      $up = [Environment]::GetEnvironmentVariable('Path','User')
      if (-not (Test-InPath $rtkDir $up)) { [Environment]::SetEnvironmentVariable('Path', "$rtkDir;$up", 'User') }
      $env:PATH = "$rtkDir;$env:PATH"
    }
    Ok 'rtk PATH 노출'
  } else { Skip 'rtk PATH 노출됨' }
  # hook 서명: verify 통과면 skip, 아니면 init. hook 파일 직접편집 금지(sha256). call operator(argv 직접)로 인젝션 회피.
  if ($DryRun) { Skip 'rtk hook 검증/서명(dry-run)' }
  else {
    & $HeadroomRtk verify *> $null
    if ($LASTEXITCODE -eq 0) { Skip 'rtk hook 무결성 OK' }
    else { Run 'rtk init -g --hook-only --no-patch'; & $HeadroomRtk init -g --hook-only --no-patch; if ($LASTEXITCODE -ne 0) { throw 'rtk init 실패' }; Ok 'rtk hook 등록·서명' }
  }
} else { Warn "headroom 번들 rtk 없음 ($HeadroomRtk) — headroom 설치/기동 후 재실행" }

# --- 7. MCP 등록 (홈 ~\.claude.json) ---
$mcp = (claude mcp list 2>$null) -join "`n"
if ($mcp -match '(?im)^codegraph') { Skip 'codegraph MCP 등록됨' }
else { Run 'codegraph install -y'; RunCmd 'codegraph install -y'; Ok 'codegraph MCP 등록' }
if ($mcp -match '(?im)^headroom') { Skip 'headroom MCP 등록됨' }
else { Run 'claude mcp add headroom'; RunCmd 'claude mcp add headroom -- headroom mcp serve'; Ok 'headroom MCP 등록' }

# --- 8. headroom proxy (Windows: persistent-task, token mode) ---
# ⚠️ token mode 는 과거 Windows 에서 압축 30s timeout 으로 api_error 이력 — 첫 실행 후 관찰, 문제 시 --mode cache 재설치.
$hr = (headroom install status 2>$null) -join "`n"
if ($hr -match '(?im)^status:\s*running') { Skip 'headroom proxy running' }
else {
  Run 'headroom install apply (persistent-task, token)'
  RunCmd 'headroom install apply --preset persistent-task --mode token'
  RunCmd 'headroom install start'; Ok 'headroom proxy 기동'
}

# --- 9. codegraph init (~\.claude 인덱스) ---
if (Test-Path (Join-Path $ClaudeDir '.codegraph')) { Skip 'codegraph 인덱스 있음' }
else {
  Run "codegraph init $ClaudeDir"
  if ($DryRun) { Write-Host "    (dry-run) codegraph init $ClaudeDir" }
  else { & codegraph init $ClaudeDir; if ($LASTEXITCODE -ne 0) { throw 'codegraph init 실패' } }
  Ok 'codegraph init'
}

# --- 10. User env (레지스트리; headroom 블록은 install 이 따로 관리) ---
function Set-UserEnv($name, $val) {
  $cur = [Environment]::GetEnvironmentVariable($name, 'User')
  if ($cur -eq $val) { Skip "env $name 이미 설정" }
  elseif ($DryRun) { Skip "env $name=$val (dry-run)" }
  else { [Environment]::SetEnvironmentVariable($name, $val, 'User'); Ok "env $name 설정" }
}
Set-UserEnv 'ANTHROPIC_MODEL' 'opus[1m]'
Set-UserEnv 'CLAUDE_CODE_EFFORT_LEVEL' 'max'

# --- 11. memory 복원 (옵션) ---
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

# --- 12. git / gh 안내 ---
if (-not (git config --global user.name 2>$null))  { Warn "git user.name 미설정 — git config --global user.name '...'" }
if (-not (git config --global user.email 2>$null)) { Warn "git user.email 미설정 — git config --global user.email '...'" }
if (Have 'gh') { gh auth status *> $null; if ($LASTEXITCODE -ne 0) { Warn 'gh 미인증 — gh auth login' } }
else { Warn 'gh 미설치 — winget install GitHub.cli' }

Write-Host ''
Ok "부트스트랩 완료. 새 터미널을 열어(레지스트리 env 반영) 'claude' 실행."
