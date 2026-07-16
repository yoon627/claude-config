param([string]$Mode = 'pre-commit')

$ErrorActionPreference = 'Stop'

# Block direct push to protected branches first (pre-push). pre-push receives
# "<local ref> <local sha> <remote ref> <remote sha>" lines on stdin.
if ($Mode -eq 'pre-push') {
    foreach ($line in ([Console]::In.ReadToEnd() -split "`n")) {
        $rref = ($line.Trim() -split '\s+')[2]
        if ($rref -eq 'refs/heads/main' -or $rref -eq 'refs/heads/master') {
            Write-Host ""
            Write-Host "[BLOCKED] Direct push to $rref is not allowed. Open a PR instead." -ForegroundColor Red
            Write-Host "Bypass once (NOT recommended): git push --no-verify" -ForegroundColor DarkGray
            exit 1
        }
    }
}

$violations = @()

# Token/secret patterns. Structured, high-confidence secrets only — free-form PII/prose is NOT scanned.
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
    @{ Name = 'PEM private key';   Pattern = '-----BEGIN [A-Z ]*PRIVATE KEY-----' },
    @{ Name = 'DB URL with credentials'; Pattern = '(postgres|postgresql|mysql|mongodb|mongodb\+srv|redis|rediss|amqp|amqps)://[^:@/ ]+:[^@/ ]+@' },
    @{ Name = 'Bearer token';      Pattern = '[Bb]earer\s+[A-Za-z0-9._~+/=-]{20,}' },
    @{ Name = 'Quoted secret assignment'; Pattern = '(password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|client[_-]?secret)"?\s*[:=]\s*"[^"]{8,}"' }
)

# Scan-Tokens: append token-pattern violations found in $Content, tagged with $Label.
function Scan-Tokens([string]$Content, [string]$Label) {
    if ([string]::IsNullOrEmpty($Content)) { return }
    foreach ($p in $script:tokenPatterns) {
        if ($Content -match $p.Pattern) {
            $sample = $Matches[0]
            if ($sample.Length -gt 30) { $sample = $sample.Substring(0, 30) + '...' }
            $script:violations += "${Label}: token pattern ($($p.Name)): $sample"
        }
    }
}

# Scan-Keys: settings.json forbidden-key check (canonical "key": form).
function Scan-Keys([string]$Content) {
    if ([string]::IsNullOrEmpty($Content)) { return }
    foreach ($key in @('mcpServers', 'apiKeyHelper', 'awsCredentialExport', 'awsAuthRefresh')) {
        $pattern = '"' + [regex]::Escape($key) + '"\s*:'
        if ($Content -match $pattern) {
            $script:violations += "settings.json: forbidden key `"$key`"  (move to settings.local.json or ~/.claude.json)"
        }
    }
}

if ($Mode -eq 'pre-commit') {
    $staged = git diff --cached --name-only --diff-filter=ACMR
    if ($staged -contains 'settings.json') {
        $sj = (git show ":settings.json") -join "`n"
        Scan-Keys $sj
        Scan-Tokens $sj 'settings.json'
    }
    # plans/*.md are tracked (approach A) and free-form → scan each staged plan for pasted secrets.
    foreach ($f in @($staged | Where-Object { $_ -match '^plans/.*\.md$' })) {
        $pc = (git show ":$f") -join "`n"
        Scan-Tokens $pc $f
    }
} else {
    $tracked = git ls-tree --name-only HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and $tracked -contains 'settings.json') {
        $sj = (git show HEAD:settings.json) -join "`n"
        Scan-Keys $sj
        Scan-Tokens $sj 'settings.json'
    }
}

if ($violations.Count -gt 0) {
    Write-Host ""
    Write-Host "[BLOCKED] Forbidden content detected. $Mode aborted." -ForegroundColor Red
    Write-Host ""
    foreach ($v in $violations) { Write-Host "  - $v" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "Move secrets/machine-specific values out of tracked files (settings.local.json is gitignored)." -ForegroundColor Cyan
    Write-Host "MCP servers belong in ~/.claude.json (managed by 'claude mcp add'), never in settings.json." -ForegroundColor Cyan
    Write-Host "Plans are committed under approach A — never paste raw tokens/credentials into plan files." -ForegroundColor Cyan
    Write-Host "To bypass once (NOT recommended): git $Mode --no-verify" -ForegroundColor DarkGray
    exit 1
}

exit 0
