param([string]$Mode = 'pre-commit')

$ErrorActionPreference = 'Stop'

# Resolve git from PATH up front: Process.Start with a bare 'git' lets Windows CreateProcess
# pick a git.exe from the current directory (the repo root) before PATH. Prefer a real
# executable over a .cmd/.bat shim, which would run through cmd.exe and eat the '^' in '^{commit}'.
$gitExe = (Get-Command git -CommandType Application -ErrorAction Stop |
    Where-Object { $_.Extension -eq '.exe' -or $_.Extension -eq '' } | Select-Object -First 1).Path
if (-not $gitExe) { throw 'git executable not found on PATH' }

# Pathspec magic variables would change what 'plans/*.md' matches in the push scan; drop them
# from this process so every git child inherits the cleaned environment. (Editing
# ProcessStartInfo.EnvironmentVariables instead throws on Windows PowerShell 5.1 when two
# variables differ only by case, e.g. tmp/TMP under MSYS2.)
foreach ($v in @('GIT_LITERAL_PATHSPECS', 'GIT_GLOB_PATHSPECS', 'GIT_NOGLOB_PATHSPECS', 'GIT_ICASE_PATHSPECS')) {
    Remove-Item -Path "Env:$v" -ErrorAction SilentlyContinue
}

# Invoke-Git: run git without the PowerShell native-command pipeline. Windows PowerShell 5.1
# turns redirected native stderr into terminating errors under EAP=Stop and decodes stdout
# with the console code page; a Process with UTF-8 stdout avoids both. stderr is left
# attached to the hook's stderr. Arguments must not contain spaces (joined as-is).
function Invoke-Git([string[]]$GitArgs) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $script:gitExe
    $psi.Arguments = ($GitArgs -join ' ')
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.StandardOutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $proc = [System.Diagnostics.Process]::Start($psi)
    $out = $proc.StandardOutput.ReadToEnd()
    $proc.WaitForExit()
    return @{ Code = $proc.ExitCode; Out = $out }
}

# pre-push receives "<local ref> <local sha> <remote ref> <remote sha>" lines on stdin;
# read them once because both the protected-branch block and the scan need them.
# Read as UTF-8: [Console]::In would decode with the console code page (CP949 on Korean Windows).
$pushLines = @()
if ($Mode -eq 'pre-push') {
    $stdin = New-Object System.IO.StreamReader([Console]::OpenStandardInput(), (New-Object System.Text.UTF8Encoding($false)))
    $pushLines = @($stdin.ReadToEnd() -split "`n" | ForEach-Object { $_.TrimEnd("`r") } | Where-Object { $_.Trim() -ne '' })
}

# Block direct push to protected branches first (pre-push).
# ~/.claude is exempt (user-authorized 2026-08-05, CLAUDE.md §8): this guard is
# shared by every repo that ran install-hooks, so the exemption is scoped by repo
# root rather than removed. Paths are resolved because either side can be a link.
if ($Mode -eq 'pre-push') {
    $resolve = { param($p) if ($p -and (Test-Path $p)) { (Resolve-Path $p).Path.TrimEnd('\', '/') } else { $p } }
    $top = Invoke-Git @('rev-parse', '--show-toplevel')
    $repoRoot = $null
    if ($top.Code -eq 0) { $repoRoot = $top.Out.Trim() }
    $isClaudeRepo = $repoRoot -and ((& $resolve $repoRoot) -eq (& $resolve (Join-Path $HOME '.claude')))
    if (-not $isClaudeRepo) {
        foreach ($line in $pushLines) {
            $rref = ($line.Trim() -split '\s+')[2]
            if ($rref -eq 'refs/heads/main' -or $rref -eq 'refs/heads/master') {
                Write-Host ""
                Write-Host "[BLOCKED] Direct push to $rref is not allowed. Open a PR instead." -ForegroundColor Red
                Write-Host "Bypass once (NOT recommended): git push --no-verify" -ForegroundColor DarkGray
                exit 1
            }
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

# Get-AddedLines: lines added under $Pathspec by the pushed commits that no remote-tracking
# ref already has, or $null when git fails. Options mirror pre-commit-check.sh added_lines.
function Get-AddedLines([string]$Pathspec) {
    $gitArgs = @('--no-replace-objects', '-c', 'core.quotePath=false', '-c', 'log.diffMerges=separate',
        '-c', 'log.showRoot=true', '-c', 'log.follow=false',
        'log', '-p', '--text', '--no-color', '--no-ext-diff', '--no-textconv',
        '--full-history', '-m', '-U0', '--src-prefix=a/', '--dst-prefix=b/', '--format=') +
        $script:pushCommits + @('--not', '--remotes', '--', $Pathspec)
    $r = Invoke-Git $gitArgs
    if ($r.Code -ne 0) { return $null }
    $added = New-Object System.Collections.Generic.List[string]
    $header = $false
    foreach ($l in ($r.Out -split "`n")) {
        if ($l.StartsWith('diff --git ', [System.StringComparison]::Ordinal)) { $header = $true; continue }
        if ($l.StartsWith('@@', [System.StringComparison]::Ordinal)) { $header = $false; continue }
        if (-not $header -and $l.StartsWith('+', [System.StringComparison]::Ordinal)) { $added.Add($l.Substring(1).TrimEnd("`r")) }
    }
    return ($added -join "`n")
}

# Scan-Pushed: scan added lines for $Pathspec; git failure blocks (fail-closed).
function Scan-Pushed([string]$Pathspec, [string]$Label, [bool]$Keys) {
    $added = Get-AddedLines $Pathspec
    if ($null -eq $added) {
        $script:violations += "pre-push: git log failed while scanning $Pathspec (fail-closed)"
        return
    }
    if ($Keys) { Scan-Keys $added }
    Scan-Tokens $added $Label
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
    # Anything the guard cannot interpret is blocked: a real pre-push always passes four
    # fields and local objects, so a mismatch means the scan cannot be trusted.
    $pushCommits = @()
    foreach ($line in $pushLines) {
        $f = @($line.Trim() -split '\s+')
        if ($f.Count -ne 4 -or $f[1] -notmatch '^[0-9a-fA-F]{4,}$') {
            $violations += "pre-push: malformed ref line: $line"
            continue
        }
        if ($f[1] -match '^0+$') { continue }
        $r = Invoke-Git @('rev-parse', '--verify', '--quiet', "$($f[1])^{commit}")
        if ($r.Code -ne 0) {
            $violations += "$($f[0]): pushed object $($f[1]) is not a resolvable commit"
            continue
        }
        $pushCommits += $r.Out.Trim()
    }
    if ($pushCommits.Count -gt 0) {
        Scan-Pushed 'settings.json' 'settings.json (pushed)' $true
        Scan-Pushed 'plans/*.md' 'plans/*.md (pushed)' $false
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
    $cmd = 'commit'
    if ($Mode -eq 'pre-push') { $cmd = 'push' }
    Write-Host "To bypass once (NOT recommended): git $cmd --no-verify" -ForegroundColor DarkGray
    exit 1
}

exit 0
