param([string]$Mode = 'pre-commit')

$ErrorActionPreference = 'Stop'

if ($Mode -eq 'pre-commit') {
    $staged = git diff --cached --name-only --diff-filter=ACMR
    if ($staged -notcontains 'settings.json') { exit 0 }
    $content = (git show ":settings.json") -join "`n"
} else {
    $tracked = git ls-tree --name-only HEAD 2>$null
    if ($LASTEXITCODE -ne 0 -or $tracked -notcontains 'settings.json') { exit 0 }
    $content = (git show HEAD:settings.json) -join "`n"
}

$violations = @()

# Blacklist JSON keys — textual match against canonical "key": form.
$blacklistKeys = @('mcpServers', 'apiKeyHelper', 'awsCredentialExport', 'awsAuthRefresh')
foreach ($key in $blacklistKeys) {
    $pattern = '"' + [regex]::Escape($key) + '"\s*:'
    if ($content -match $pattern) {
        $violations += "Forbidden key in settings.json: `"$key`"  (move to settings.local.json or ~/.claude.json)"
    }
}

# Token patterns.
$tokenPatterns = @(
    @{ Name = 'Anthropic key';     Pattern = 'sk-ant-[A-Za-z0-9_-]{20,}' },
    @{ Name = 'OpenAI project key';Pattern = 'sk-proj-[A-Za-z0-9_-]{20,}' },
    @{ Name = 'OpenAI key';        Pattern = 'sk-[A-Za-z0-9]{32,}' },
    @{ Name = 'GitHub PAT (fine)'; Pattern = 'github_pat_[A-Za-z0-9_]{20,}' },
    @{ Name = 'GitHub token';      Pattern = 'gh[opsu]_[A-Za-z0-9_]{30,}' },
    @{ Name = 'GitLab PAT';        Pattern = 'glpat-[A-Za-z0-9_-]{20,}' },
    @{ Name = 'AWS key';           Pattern = '(AKIA|ASIA)[A-Z0-9]{16}' },
    @{ Name = 'Google API key';    Pattern = 'AIza[A-Za-z0-9_-]{35}' },
    @{ Name = 'Slack token';       Pattern = 'xox[baprs]-[A-Za-z0-9-]{20,}' },
    @{ Name = 'JWT';               Pattern = 'eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}' },
    @{ Name = 'PEM private key';   Pattern = '-----BEGIN [A-Z ]*PRIVATE KEY-----' }
)
foreach ($p in $tokenPatterns) {
    if ($content -match $p.Pattern) {
        $sample = $Matches[0]
        if ($sample.Length -gt 30) { $sample = $sample.Substring(0, 30) + '...' }
        $violations += "Token pattern matched ($($p.Name)): $sample"
    }
}

if ($violations.Count -gt 0) {
    Write-Host ""
    Write-Host "[BLOCKED] settings.json contains forbidden content. $Mode aborted." -ForegroundColor Red
    Write-Host ""
    foreach ($v in $violations) { Write-Host "  - $v" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "Move sensitive/machine-specific values to ~/.claude/settings.local.json (gitignored)." -ForegroundColor Cyan
    Write-Host "MCP servers belong in ~/.claude.json (managed by 'claude mcp add'), never in settings.json." -ForegroundColor Cyan
    Write-Host "To bypass once (NOT recommended): git $Mode --no-verify" -ForegroundColor DarkGray
    exit 1
}

exit 0
