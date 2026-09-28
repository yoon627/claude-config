$ErrorActionPreference = 'Stop'

# git runs through a Process, as in pre-commit-check.ps1: Windows PowerShell 5.1 turns redirected
# native stderr into a terminating error under EAP=Stop and decodes native stdout with the console
# code page. Resolved from PATH up front so a git.exe in the current directory is never picked.
$gitExe = (Get-Command git -CommandType Application -ErrorAction Stop |
    Where-Object { $_.Extension -eq '.exe' -or $_.Extension -eq '' } | Select-Object -First 1).Path
if (-not $gitExe) { throw 'git executable not found on PATH' }
function Invoke-Git([string[]]$GitArgs) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $script:gitExe
    $psi.Arguments = ($GitArgs -join ' ')
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $proc = [System.Diagnostics.Process]::Start($psi)
    $err = $proc.StandardError.ReadToEndAsync()  # read both pipes at once so neither can fill and block git
    $out = $proc.StandardOutput.ReadToEnd()
    $proc.WaitForExit()
    return @{ Code = $proc.ExitCode; Out = $out.Trim(); Err = (($err.Result -split "`n")[0]).Trim() }
}
function Stop-Install([string]$Message) {
    Write-Host $Message -ForegroundColor Red
    exit 1
}
$norm = { param($p) ($p -replace '\\', '/').TrimEnd('/') }

# git's own reason (e.g. safe.directory "dubious ownership") goes with the message.
$top = Invoke-Git @('rev-parse', '--show-toplevel')
if ($top.Code -ne 0 -or -not $top.Out) { Stop-Install "Not inside a git repo. $($top.Err)" }
function Get-GitPath([string[]]$GitArgs) {
    $r = Invoke-Git $GitArgs
    if ($r.Code -ne 0) { Stop-Install "git $($GitArgs -join ' ') failed: $($r.Err)" }
    $r.Out
}

# The hooks git actually runs: shared by linked worktrees, redirected by core.hooksPath (any
# config scope). When core.hooksPath moves them away from the repo's own hooks dir, another tool
# (husky, lefthook, ...) owns that directory -- writing there would replace that tool's hooks, and
# .git/hooks would never run.
$hookDir = & $norm (Get-GitPath @('rev-parse', '--path-format=absolute', '--git-path', 'hooks'))
# git < 2.31 echoes the unknown option back on stdout instead of failing.
if ($hookDir.StartsWith('--')) { Stop-Install 'git 2.31 or newer is required (git rev-parse --path-format).' }
$defaultDir = (& $norm (Get-GitPath @('rev-parse', '--path-format=absolute', '--git-common-dir'))) + '/hooks'
$hooksPath = (Invoke-Git @('config', '--get', 'core.hooksPath')).Out
# Case-insensitive on purpose: Windows paths, and a hooksPath that spells the default dir differently.
if ($hooksPath -and -not $hookDir.Equals($defaultDir, [System.StringComparison]::OrdinalIgnoreCase)) {
    Stop-Install ("core.hooksPath points git at $hookDir, so hooks in $defaultDir would never run. " +
        "Not installing. Call ~/.claude/scripts/pre-commit-check.ps1 from the tool that manages that directory.")
}
if (-not (Test-Path -LiteralPath $hookDir)) {
    New-Item -ItemType Directory -Path $hookDir -Force | Out-Null
}

# Guard lives in ~/.claude (guards settings.json), regardless of which repo the
# hooks are installed into — mirrors install-hooks.sh.
$guard = Join-Path $HOME '.claude\scripts\pre-commit-check.ps1'
if (-not (Test-Path -LiteralPath $guard)) {
    Write-Error "Guard script not found: $guard"
    exit 1
}
$guardForHook = ($guard -replace '\\', '/')

# First free "<hook>.bak.<UTC time>[.<n>]" -- every reinstall keeps the previous backups.
function Get-BackupPath {
    param([string]$Path)
    $base = "$Path.bak." + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ', [Globalization.CultureInfo]::InvariantCulture)
    $candidate = $base
    $n = 1
    while (Test-Path -LiteralPath $candidate) {
        $candidate = "$base.$n"
        $n++
    }
    $candidate
}

function Write-LfFile {
    param([string]$Path, [string]$Content)
    $normalized = $Content -replace "`r`n", "`n"
    if (Test-Path -LiteralPath $Path) {
        $existing = [System.IO.File]::ReadAllText($Path)
        if ($existing -eq $normalized) { return }
        $backup = Get-BackupPath $Path
        Move-Item -LiteralPath $Path -Destination $backup
        Write-Host "Existing hook backed up: $backup" -ForegroundColor Yellow
    }
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($normalized)
    [System.IO.File]::WriteAllBytes($Path, $bytes)
}

$preCommit = @"
#!/bin/sh
exec powershell -NoProfile -ExecutionPolicy Bypass -File "$guardForHook" -Mode pre-commit
"@

$prePush = @"
#!/bin/sh
exec powershell -NoProfile -ExecutionPolicy Bypass -File "$guardForHook" -Mode pre-push
"@

# post-checkout is pure shell (runs under Git Bash sh on Windows) — literal here-string,
# no PowerShell interpolation. Byte-identical logic to install-hooks.sh.
$postCheckout = @'
#!/bin/sh
# Fast-forward main/master to origin on branch checkout. Never blocks (exit 0 always).
# Disable without deleting the file: export CLAUDE_AUTOPULL_OFF=1
[ "${CLAUDE_AUTOPULL_OFF:-}" = 1 ] && exit 0
[ "$3" = 1 ] || exit 0
git_dir="$(git rev-parse --git-dir 2>/dev/null)" || exit 0
for _st in rebase-merge rebase-apply MERGE_HEAD BISECT_LOG; do
  [ -e "$git_dir/$_st" ] && exit 0
done
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
case "$branch" in
  main|master) ;;
  *) exit 0 ;;
esac
git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null || exit 0
git remote get-url origin >/dev/null 2>&1 || exit 0
# Never hang the checkout: no credential prompt, SSH connect capped, HTTP stall capped,
# and a portable ~20s watchdog (macOS has no timeout(1)) that kills a stuck pull.
export GIT_TERMINAL_PROMPT=0
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh} -o BatchMode=yes -o ConnectTimeout=10"
_before="$(git rev-parse HEAD 2>/dev/null)"
# Run the pull in the background (stdio detached from the checkout) and poll it, killing
# it past ~20s. Gives a wall-clock cap without timeout(1) (macOS) and leaves no orphan.
git -c core.askpass= -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=10 \
  pull --ff-only --quiet origin "$branch" >/dev/null 2>&1 </dev/null &
_pid=$!
_n=0
while kill -0 "$_pid" 2>/dev/null; do
  [ "$_n" -ge 100 ] && { kill "$_pid" 2>/dev/null; break; }
  sleep 0.2
  _n=$((_n + 1))
done
wait "$_pid" 2>/dev/null
_rc=$?
if [ "$_rc" = 0 ]; then
  _after="$(git rev-parse HEAD 2>/dev/null)"
  [ "$_before" != "$_after" ] && echo "post-checkout: $branch fast-forwarded to origin/$branch"
else
  echo "post-checkout: '$branch' ff from origin skipped (offline/timeout, or local commits on $branch)."
fi
exit 0
'@

Write-LfFile -Path (Join-Path $hookDir 'pre-commit')    -Content $preCommit
Write-LfFile -Path (Join-Path $hookDir 'pre-push')      -Content $prePush
Write-LfFile -Path (Join-Path $hookDir 'post-checkout') -Content $postCheckout

Write-Host "Installed pre-commit, pre-push, and post-checkout hooks at $hookDir" -ForegroundColor Green
Write-Host "Guards check plans/*.md (and settings.json if ever tracked): staged content on commit, lines added by the pushed commits on push; post-checkout fast-forwards main/master from origin." -ForegroundColor Gray
Write-Host "Bypass guard once: git commit --no-verify / git push --no-verify" -ForegroundColor DarkGray
Write-Host "Disable auto-pull: `$env:CLAUDE_AUTOPULL_OFF=1  |  Remove: del `"$hookDir\post-checkout`"" -ForegroundColor DarkGray
