$ErrorActionPreference = 'Stop'

$repoRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) {
    Write-Error "Not inside a git repo."
    exit 1
}

$hookDir = Join-Path $repoRoot '.git\hooks'
if (-not (Test-Path $hookDir)) {
    New-Item -ItemType Directory -Path $hookDir -Force | Out-Null
}

# Guard lives in ~/.claude (guards settings.json), regardless of which repo the
# hooks are installed into — mirrors install-hooks.sh.
$guard = Join-Path $HOME '.claude\scripts\pre-commit-check.ps1'
if (-not (Test-Path $guard)) {
    Write-Error "Guard script not found: $guard"
    exit 1
}
$guardForHook = ($guard -replace '\\', '/')

function Write-LfFile {
    param([string]$Path, [string]$Content)
    $normalized = $Content -replace "`r`n", "`n"
    if (Test-Path $Path) {
        $existing = [System.IO.File]::ReadAllText($Path)
        if ($existing -eq $normalized) { return }
        $backup = "$Path.bak"
        Move-Item -Path $Path -Destination $backup -Force
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
Write-Host "Guards check settings.json; post-checkout fast-forwards main/master from origin." -ForegroundColor Gray
Write-Host "Bypass guard once: git commit --no-verify / git push --no-verify" -ForegroundColor DarkGray
Write-Host "Disable auto-pull: `$env:CLAUDE_AUTOPULL_OFF=1  |  Remove: del `"$hookDir\post-checkout`"" -ForegroundColor DarkGray
