$ErrorActionPreference = 'Stop'

# gwl is wired to the documented clone location, ~/.claude, so the $PROFILE line
# stays portable and picks up `git pull` updates to gwl.ps1. Verify and reference
# the SAME path ($claudeHome) to avoid wiring a path we never checked.
$claudeHome = Join-Path $HOME '.claude'
$gwlScript  = Join-Path $claudeHome 'scripts/gwl.ps1'

# If this repo lives somewhere other than ~/.claude, the dot-source target below
# won't point at it; warn rather than silently wire the wrong path.
$repoRoot = (& git rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -eq 0 -and $repoRoot) {
    $repoNorm   = ($repoRoot.Trim() -replace '\\', '/').TrimEnd('/')
    $homeNorm   = ($claudeHome   -replace '\\', '/').TrimEnd('/')
    if ($repoNorm -ne $homeNorm) {
        Write-Host "Warning: repo is at $repoNorm, not ~/.claude." -ForegroundColor Yellow
        Write-Host "         gwl will be wired to $gwlScript regardless (the documented location)." -ForegroundColor Yellow
    }
}

if (-not (Test-Path -LiteralPath $gwlScript)) {
    Write-Error "gwl.ps1 not found at $gwlScript. Clone this repo to ~/.claude (or copy scripts/gwl.ps1 there) first."
    exit 1
}

$sourceLine  = '. "$HOME/.claude/scripts/gwl.ps1"'
$beginMarker = '# >>> claude-config gwl >>>'
$endMarker   = '# <<< claude-config gwl <<<'

$profilePath = $PROFILE.CurrentUserCurrentHost
$profileDir  = Split-Path -Parent $profilePath
if (-not (Test-Path -LiteralPath $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}

$existing = ''
if (Test-Path -LiteralPath $profilePath) {
    $raw = Get-Content -Raw -LiteralPath $profilePath
    if ($raw) { $existing = $raw }
}

# Idempotency: both markers present = already installed; exactly one = corrupted.
$hasBegin = $existing -match [regex]::Escape($beginMarker)
$hasEnd   = $existing -match [regex]::Escape($endMarker)
if ($hasBegin -and $hasEnd) {
    Write-Host "gwl already installed in $profilePath - nothing to do." -ForegroundColor Green
    exit 0
}
if ($hasBegin -or $hasEnd) {
    Write-Error "Partial gwl marker block in $profilePath. Remove the stray '$beginMarker' / '$endMarker' line(s) and re-run."
    exit 1
}

# Heads-up if an inline `function gwl` already exists outside our managed block.
if ($existing -match '(?m)^\s*function\s+(global:)?gwl\b') {
    Write-Host "Note: an inline 'function gwl' already exists in your profile." -ForegroundColor Yellow
    Write-Host "      The dot-sourced copy is appended after it and wins; remove the old one to avoid confusion." -ForegroundColor Yellow
}

if ($existing -and -not $existing.EndsWith("`n")) {
    Add-Content -LiteralPath $profilePath -Value ''
}
Add-Content -LiteralPath $profilePath -Value @($beginMarker, $sourceLine, $endMarker)

Write-Host "Installed gwl into $profilePath" -ForegroundColor Green
Write-Host "Activate now:  . `$PROFILE   (or open a new PowerShell)" -ForegroundColor Gray
