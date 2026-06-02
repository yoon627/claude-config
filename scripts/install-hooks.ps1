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

Write-LfFile -Path (Join-Path $hookDir 'pre-commit') -Content $preCommit
Write-LfFile -Path (Join-Path $hookDir 'pre-push')   -Content $prePush

Write-Host "Installed pre-commit and pre-push hooks at $hookDir" -ForegroundColor Green
Write-Host "These guards check staged/HEAD settings.json for forbidden keys and token patterns." -ForegroundColor Gray
Write-Host "Bypass once (NOT recommended): git commit --no-verify  /  git push --no-verify" -ForegroundColor DarkGray
