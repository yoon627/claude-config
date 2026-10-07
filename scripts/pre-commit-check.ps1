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
# A replace ref would let every git call below read a substitute object — a tag peeled to a
# commit the remote does not have, or a staged blob other than the one being committed.
$env:GIT_NO_REPLACE_OBJECTS = '1'

# Invoke-Git: run git without the PowerShell native-command pipeline. Windows PowerShell 5.1
# turns redirected native stderr into terminating errors under EAP=Stop and decodes stdout
# with the console code page; a Process with UTF-8 stdout avoids both. stderr is left
# attached to the hook's stderr unless -DropStderr. Arguments must not contain spaces (joined as-is).
# -Stdin (object names, ASCII) is written to git's stdin. .NET Framework (5.1) builds that
# writer from [Console]::InputEncoding and writes its preamble at once, so a UTF-8 console
# input code page (chcp 65001, "Beta: UTF-8") would put a BOM before the first object name
# and git log would fail; the console encoding is BOM-less UTF-8 while the process starts.
# -Cwd runs git in that directory instead of the current one.
function Invoke-Git([string[]]$GitArgs, [switch]$DropStderr, [string]$Stdin, [string]$Cwd) {
    $withStdin = $PSBoundParameters.ContainsKey('Stdin')
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $script:gitExe
    $psi.Arguments = ($GitArgs -join ' ')
    if ($Cwd) { $psi.WorkingDirectory = $Cwd }
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.StandardOutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $psi.RedirectStandardError = [bool]$DropStderr
    $psi.RedirectStandardInput = $withStdin
    $consoleIn = $null
    if ($withStdin) {
        try {
            $consoleIn = [Console]::InputEncoding
            [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
        } catch { $consoleIn = $null }  # no console: the default writer encoding has no preamble
    }
    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
    } finally {
        if ($consoleIn) { [Console]::InputEncoding = $consoleIn }
    }
    # Reading starts before stdin is written: git cat-file --batch-check answers each line as it
    # comes, and with nobody reading, full pipes would leave git and this writer waiting on
    # each other.
    $err = $null
    if ($DropStderr) { $err = $proc.StandardError.ReadToEndAsync() }
    $out = $proc.StandardOutput.ReadToEndAsync()
    if ($withStdin) {
        $proc.StandardInput.Write($Stdin)
        $proc.StandardInput.Close()
    }
    $out = $out.Result
    $proc.WaitForExit()
    if ($err) { [void]$err.Result }
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

# ~/.claude is a public repo, so what is committed there is also checked against
# $HOME/.claude/private-terms.txt: an untracked, per-machine list of names that must not be
# published. Other repos never open the list. Unlike the exemption above, which compares
# --show-toplevel and so only matches the main checkout, this compares common git dirs so
# linked worktrees and a gitfile .git count; git prints both sides as resolved absolute paths.
# The ~/.claude query runs without git's variables: a hook in a linked worktree inherits
# GIT_DIR for the current repo, which would answer for it instead. If git cannot answer,
# block inside ~/.claude and pass elsewhere. Mirrors pre-commit-check.sh.
$claudeDir = Join-Path $HOME '.claude'
$ptList = Join-Path $claudeDir 'private-terms.txt'
$claudeRepo = 'no'
if (Test-Path -LiteralPath (Join-Path $claudeDir '.git')) {
    $known = $false
    try {
        $commonArgs = @('rev-parse', '--path-format=absolute', '--git-common-dir')
        $here = Invoke-Git $commonArgs -DropStderr
        $gitVars = @{}
        try {
            foreach ($v in @('GIT_DIR', 'GIT_COMMON_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE')) {
                $gitVars[$v] = [Environment]::GetEnvironmentVariable($v)
                Remove-Item -Path "Env:$v" -ErrorAction SilentlyContinue
            }
            $there = Invoke-Git $commonArgs -DropStderr -Cwd $claudeDir
        } finally {
            foreach ($v in $gitVars.Keys) {
                if ($null -ne $gitVars[$v]) { [Environment]::SetEnvironmentVariable($v, $gitVars[$v]) }
            }
        }
        $a = $here.Out.Trim().TrimEnd('/', '\')
        $b = $there.Out.Trim().TrimEnd('/', '\')
        if ($here.Code -eq 0 -and $there.Code -eq 0 -and $a -and $b -and -not $a.Contains("`n") -and -not $b.Contains("`n")) {
            $known = $true
            if ([string]::Equals($a, $b, [StringComparison]::OrdinalIgnoreCase)) { $claudeRepo = 'yes' }
        }
    } catch { $known = $false }
    if (-not $known) {
        $sep = [IO.Path]::DirectorySeparatorChar
        $cwd = [IO.Path]::GetFullPath((Get-Location).ProviderPath).TrimEnd('/', '\') + $sep
        $root = [IO.Path]::GetFullPath($claudeDir).TrimEnd('/', '\') + $sep
        if ($cwd.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) { $claudeRepo = 'unknown' }
    }
}

$violations = @()
$ptHit = 0
$ptTermHits = 0
$ptNamed = 0

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

# Options the added-line scans share; pre-commit-check.sh git_global / git_walk / git_patch say
# what each one guards against.
$gitGlobal = @('--no-replace-objects', '-c', 'core.quotePath=false', '-c', 'log.diffMerges=separate',
    '-c', 'log.showRoot=true', '-c', 'log.follow=false')
$gitWalk = @('log', '--stdin', '--full-history')
$gitPatch = @('-U0', '--text', '--no-color', '--no-ext-diff', '--no-textconv', '--src-prefix=a/', '--dst-prefix=b/')

# Get-RevInput: the revisions for `git log --stdin` — pushed commits, then exclusions marked
# with `^`, deduplicated in order. They go on stdin because as arguments a new remote with
# hundreds of refs exceeds the Windows command-line limit (32,767 chars). Mirrors
# pre-commit-check.sh rev_input.
function Get-RevInput {
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
    $revs = New-Object System.Collections.Generic.List[string]
    foreach ($r in @($script:pushCommits) + @($script:published | ForEach-Object { "^$_" })) {
        if ($r -and $seen.Add($r)) { $revs.Add($r) }
    }
    return ($revs -join "`n")
}

# Get-AddedLines: lines added under $Pathspec by the pushed commits that the destination refs
# do not already have, or $null when git fails. Options mirror pre-commit-check.sh added_lines.
function Get-AddedLines([string]$Pathspec) {
    # `git log --stdin` falls back to HEAD on empty input or a leading blank line: block instead.
    $revs = Get-RevInput
    if (-not $revs) { return $null }
    $gitArgs = $script:gitGlobal + $script:gitWalk + @('-p', '-m') + $script:gitPatch + @('--format=', '--', $Pathspec)
    $r = Invoke-Git $gitArgs -Stdin ($revs + "`n")
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

# Private-term functions mirror pre-commit-check.sh (pt_*): the violation strings are
# character-identical, and none of them echoes a term or the matched text.
function Add-PrivateViolation([string]$Message) { $script:violations += $Message; $script:ptHit++ }

# Records to match, as parallel lists: kind (staged, pushed, stagedPath, pushedPath, message,
# identity, ref), where (path or short sha), text.
$ptKind = New-Object System.Collections.Generic.List[string]
$ptWhere = New-Object System.Collections.Generic.List[string]
$ptText = New-Object System.Collections.Generic.List[string]
function Add-PrivateRecord([string]$Kind, [string]$Where, [string]$Text) {
    $script:ptKind.Add($Kind); $script:ptWhere.Add($Where); $script:ptText.Add($Text)
}

# Get-PrivateTerms: parse the list into $script:ptTerms (@{ Line; Any; Term }); $false when there
# is nothing to match. Same rules and blocking states as pt_load. Terms are lowered with
# ToLowerInvariant, so unlike the sh engine non-ASCII letters also match case-insensitively.
function Get-PrivateTerms {
    $path = $script:ptList
    $isLink = $false
    try {
        $attr = (New-Object System.IO.FileInfo $path).Attributes
        $isLink = ([int]$attr -ne -1) -and (($attr -band [IO.FileAttributes]::ReparsePoint) -ne 0)
    } catch { $isLink = $false }
    if (-not [IO.File]::Exists($path) -and -not [IO.Directory]::Exists($path) -and -not $isLink) {
        Write-Host "note: private-terms list not found ($path); private-term check skipped" -ForegroundColor DarkGray
        return $false
    }
    $bytes = $null
    if ([IO.File]::Exists($path)) { try { $bytes = [IO.File]::ReadAllBytes($path) } catch { $bytes = $null } }
    if ($null -eq $bytes) { Add-PrivateViolation "private-terms list unreadable: $path"; return $false }
    $text = (New-Object System.Text.UTF8Encoding($false)).GetString($bytes)
    if ($text.Length -gt 0 -and [int]$text[0] -eq 0xFEFF) { $text = $text.Substring(1) }
    $terms = New-Object System.Collections.Generic.List[object]
    $bad = @()
    $lines = $text.Split([char]"`n")
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $t = $lines[$i].Trim([char[]]@(' ', "`t", "`r"))
        if ($t -eq '' -or $t.StartsWith('#', [StringComparison]::Ordinal)) { continue }
        $any = $t.StartsWith('*', [StringComparison]::Ordinal)
        if ($any) { $t = $t.Substring(1).TrimStart([char[]]@(' ', "`t")) }
        if ([Text.Encoding]::UTF8.GetByteCount($t) -lt 3 -or $t -match '[\x00-\x1F\x7F]') { $bad += $i + 1 }
        else { $terms.Add(@{ Line = $i + 1; Any = $any; Term = $t.ToLowerInvariant() }) }
    }
    if ($bad.Count -gt 0) {
        foreach ($n in $bad) { Add-PrivateViolation "private-terms.txt line ${n}: invalid entry (under 3 bytes or has a control character)" }
        return $false
    }
    $script:ptTerms = $terms
    return ($terms.Count -gt 0)
}

function Test-AsciiAlnum([int]$C) {
    return ($C -ge 97 -and $C -le 122) -or ($C -ge 65 -and $C -le 90) -or ($C -ge 48 -and $C -le 57)
}

# Test-PrivateTerm: pt_match's found() on $Text (lowered). The neighbours are read from $Orig,
# the same string before lowering (same length): ToLowerInvariant turns some non-ASCII letters,
# such as the Kelvin sign, into ASCII ones, which sh would still count as a boundary.
function Test-PrivateTerm([string]$Text, [string]$Orig, $Entry) {
    $term = $Entry.Term
    if ($Entry.Any) { return $Text.IndexOf($term, [StringComparison]::Ordinal) -ge 0 }
    $from = 0
    while ($true) {
        $p = $Text.IndexOf($term, $from, [StringComparison]::Ordinal)
        if ($p -lt 0) { return $false }
        $end = $p + $term.Length
        $before = ($p -gt 0) -and (Test-AsciiAlnum ([int]$Orig[$p - 1]))
        $after = ($end -lt $Orig.Length) -and (Test-AsciiAlnum ([int]$Orig[$end]))
        if (-not $before -and -not $after) { return $true }
        $from = $p + 1
    }
}

# Find-PrivateTerms: pt_match over the collected records.
function Find-PrivateTerms {
    $n = $script:ptKind.Count
    # The record loop runs in script, so entries found in no record at all are dropped first.
    $all = New-Object System.Text.StringBuilder
    for ($i = 0; $i -lt $n; $i++) { [void]$all.Append($script:ptWhere[$i]).Append("`n").Append($script:ptText[$i]).Append("`n") }
    $haystack = $all.ToString().ToLowerInvariant()
    $cands = @($script:ptTerms | Where-Object { $haystack.IndexOf($_.Term, [StringComparison]::Ordinal) -ge 0 })
    if ($cands.Count -eq 0) { return }
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
    $hidden = New-Object 'System.Collections.Generic.Dictionary[string,bool]' ([StringComparer]::Ordinal)
    for ($i = 0; $i -lt $n; $i++) {
        $kind = $script:ptKind[$i]; $where = $script:ptWhere[$i]
        $orig = $script:ptText[$i]
        $text = $orig.ToLowerInvariant()
        foreach ($e in $cands) {
            if (-not (Test-PrivateTerm $text $orig $e)) { continue }
            if ($kind -ceq 'staged' -or $kind -ceq 'pushed') {
                if (-not $hidden.ContainsKey($where)) {
                    $lw = $where.ToLowerInvariant()
                    $hidden[$where] = @($cands | Where-Object { $lw.IndexOf($_.Term, [StringComparison]::Ordinal) -ge 0 }).Count -gt 0
                }
                if ($hidden[$where]) { $label = "$kind path (hidden)" } else { $label = "$kind $where" }
            } elseif ($kind -ceq 'stagedPath') { $label = 'staged path (hidden)' }
            elseif ($kind -ceq 'pushedPath') { $label = 'pushed path (hidden)' }
            elseif ($kind -ceq 'message') { $label = "commit $where message" }
            elseif ($kind -ceq 'identity') { $label = "commit $where identity" }
            else { $label = 'push ref (hidden)' }
            if ($seen.Add("$($e.Line)`t$label")) {
                Add-PrivateViolation "private term (list line $($e.Line)) in $label"
                $script:ptTermHits++
            }
        }
    }
}

# Add-PatchRecords: pt_patch_records — the path comes from the "+++ b/<path>" header.
function Add-PatchRecords([string]$Patch, [string]$Kind) {
    $header = $false; $path = ''
    foreach ($l in $Patch.Split([char]"`n")) {
        if ($l.StartsWith('diff --git ', [StringComparison]::Ordinal)) { $header = $true; continue }
        if ($header -and $l.StartsWith('+++ ', [StringComparison]::Ordinal)) {
            $path = $l.Substring(4)
            if ($path.EndsWith("`t", [StringComparison]::Ordinal)) { $path = $path.Substring(0, $path.Length - 1) }
            $path = ($path -creplace '^"?b/', '') -creplace '"$', ''
            continue
        }
        if ($l.StartsWith('@@', [StringComparison]::Ordinal)) { $header = $false; continue }
        if (-not $header -and $l.StartsWith('+', [StringComparison]::Ordinal)) { Add-PrivateRecord $Kind $path $l.Substring(1) }
    }
}

# Add-PathRecords: pt_new_paths — NUL-separated paths, a newline in a path becomes "?".
function Add-PathRecords([string]$Out, [string]$Kind) {
    foreach ($p in $Out.Split([char]0)) { if ($p.Length -gt 0) { Add-PrivateRecord $Kind '' $p.Replace("`n", '?') } }
}

# Add-MessageRecords: "\x01<sha>", author and committer lines, then the message.
function Add-MessageRecords([string]$Out) {
    $sha = ''; $id = 0
    foreach ($l in $Out.Split([char]"`n")) {
        if ($l.Length -gt 0 -and [int]$l[0] -eq 1) { $sha = $l.Substring(1); $id = 2; continue }
        if ($id -gt 0) { Add-PrivateRecord 'identity' $sha $l; $id--; continue }
        Add-PrivateRecord 'message' $sha $l
    }
}

# Test-ListNamed: pt_list_named — the list itself must never be committed, list or not.
function Test-ListNamed([string]$Where) {
    for ($i = 0; $i -lt $script:ptKind.Count; $i++) {
        if (($script:ptKind[$i] -ceq 'stagedPath' -or $script:ptKind[$i] -ceq 'pushedPath') -and
            $script:ptText[$i] -cmatch '(^|/)private-terms\.txt$') {
            Add-PrivateViolation "a file named private-terms.txt is in the $Where - the list must stay untracked"
            $script:ptNamed = 1
            return
        }
    }
}

# Invoke-PrivateStaged: pt_scan_staged.
function Invoke-PrivateStaged {
    $base = @('-c', 'core.quotePath=false', '-c', 'diff.renames=true', 'diff', '--cached', '-M', '--no-ext-diff')
    $names = Invoke-Git ($base + @('--name-only', '-z', '--diff-filter=ACR'))
    $patch = $null
    if ($names.Code -eq 0) { $patch = Invoke-Git ($base + $script:gitPatch) }
    if ($null -eq $patch -or $patch.Code -ne 0) {
        Add-PrivateViolation 'pre-commit: git diff failed while checking private terms (fail-closed)'
        return
    }
    Add-PathRecords $names.Out 'stagedPath'
    Test-ListNamed 'staged changes'
    if (-not (Get-PrivateTerms)) { return }
    Add-PatchRecords $patch.Out 'staged'
    Find-PrivateTerms
}

# Get-PrivateRevInput: private_rev_input — Get-RevInput minus what origin/main has.
function Get-PrivateRevInput {
    $revs = Get-RevInput
    if (-not $revs) { return $null }
    $b = Invoke-Git @('rev-parse', '--verify', '--quiet', 'refs/remotes/origin/main^{commit}') -DropStderr
    if ($b.Code -eq 0 -and $b.Out.Trim()) { $revs += "`n^" + $b.Out.Trim() }
    return $revs
}

# Invoke-PrivateLog: pt_log — git log over the private push range, or $null when git fails.
function Invoke-PrivateLog([string[]]$LogArgs) {
    $revs = Get-PrivateRevInput
    if (-not $revs) { return $null }
    $gitArgs = $script:gitGlobal + @('-c', 'diff.renames=true', '-c', 'i18n.logOutputEncoding=UTF-8') + $script:gitWalk + $LogArgs
    $r = Invoke-Git $gitArgs -Stdin ($revs + "`n")
    if ($r.Code -ne 0) { return $null }
    return $r.Out
}

# Invoke-PrivatePushed: pt_scan_pushed.
function Invoke-PrivatePushed {
    foreach ($r in $script:ptRefs) { Add-PrivateRecord 'ref' '' $r }
    $patch = ''; $msgs = ''
    if ($script:pushCommits.Count -gt 0) {
        $names = Invoke-PrivateLog @('-m', '--name-only', '-z', '-M', '--diff-filter=ACR', '--no-ext-diff', '--format=')
        $patch = $null; $msgs = $null
        if ($null -ne $names) { $patch = Invoke-PrivateLog (@('-m', '-p', '-M') + $script:gitPatch + @('--format=')) }
        if ($null -ne $patch) { $msgs = Invoke-PrivateLog @('--format=%x01%h%n%an%x20<%ae>%n%cn%x20<%ce>%n%B') }
        if ($null -eq $msgs) {
            Add-PrivateViolation 'pre-push: git log failed while checking private terms (fail-closed)'
            return
        }
        Add-PathRecords $names 'pushedPath'
        Test-ListNamed 'pushed commits'
    }
    if (-not (Get-PrivateTerms)) { return }
    Add-PatchRecords $patch 'pushed'
    Add-MessageRecords $msgs
    Find-PrivateTerms
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
    # Anything the guard cannot interpret is blocked: a real pre-push always passes four fields
    # with object names exactly as long as this repo's hash, and pushes local objects, so a
    # mismatch means the scan cannot be trusted. (Any other hex string could resolve to a ref of
    # the same name instead.)
    # "Already published" is what the destination refs hold right now: the remote sha of every
    # line, deletions included, comes from the remote itself — unlike tracking refs, which can
    # be stale, belong to another remote, or not match a pushurl. git sends at most the commits
    # none of the remote's refs have, so excluding only these keeps the scan a superset of it.
    $pushCommits = @()
    $published = @()
    $ptRefs = @()
    $oid = '^[0-9a-fA-F]{40}$'
    if ((Invoke-Git @('rev-parse', '--show-object-format') -DropStderr).Out.Trim() -eq 'sha256') { $oid = '^[0-9a-fA-F]{64}$' }
    # Every object name is peeled to a commit by one cat-file call, which answers one line per
    # query in order, instead of a rev-parse per name. A remote value that is not a commit here
    # (not fetched, a blob or tree) excludes nothing; stderr is dropped because peeling a blob or
    # tree prints an error. If cat-file fails, nothing resolves: pushed objects block and remote
    # values exclude nothing.
    $refLines = @(foreach ($line in $pushLines) { , @($line.Trim() -split '\s+') })
    $queries = @(foreach ($f in $refLines) {
        if ($f.Count -ne 4 -or $f[1] -notmatch $oid -or $f[3] -notmatch $oid) { continue }
        if ($f[3] -notmatch '^0+$') { "$($f[3])^{commit}" }
        if ($f[1] -notmatch '^0+$') { "$($f[1])^{commit}" }
    })
    $answers = @()
    if ($queries.Count -gt 0) {
        # The default "<oid> <type> <size>" format: Invoke-Git arguments cannot hold spaces.
        $r = Invoke-Git @('cat-file', '--batch-check') -DropStderr -Stdin (($queries -join "`n") + "`n")
        if ($r.Code -eq 0) {
            $answers = @($r.Out.TrimEnd("`n") -split "`n" | ForEach-Object { $_.TrimEnd("`r") })
            if ($answers.Count -ne $queries.Count) { $answers = @() }
        }
    }
    $q = 0
    $nextPeeled = {
        $a = @(([string]$answers[$script:q]) -split ' ')
        $script:q++
        if ($a.Count -eq 3 -and $a[1] -eq 'commit' -and $a[0] -match $oid) { $a[0] } else { $null }
    }
    for ($i = 0; $i -lt $pushLines.Count; $i++) {
        $f = $refLines[$i]
        if ($f.Count -ne 4 -or $f[1] -notmatch $oid -or $f[3] -notmatch $oid) {
            $violations += "pre-push: malformed ref line: $($pushLines[$i])"
            continue
        }
        if ($f[3] -notmatch '^0+$') {
            $c = & $nextPeeled
            if ($c) { $published += $c }
        }
        if ($f[1] -match '^0+$') { continue }
        $ptRefs += $f[2]
        $c = & $nextPeeled
        if (-not $c) {
            $violations += "$($f[0]): pushed object $($f[1]) is not a resolvable commit"
            continue
        }
        $pushCommits += $c
    }
    if ($pushCommits.Count -gt 0) {
        Scan-Pushed 'settings.json' 'settings.json (pushed)' $true
        Scan-Pushed 'plans/*.md' 'plans/*.md (pushed)' $false
    }
}

if ($claudeRepo -eq 'yes') {
    if ($Mode -eq 'pre-commit') { Invoke-PrivateStaged } else { Invoke-PrivatePushed }
} elseif ($claudeRepo -eq 'unknown') {
    Add-PrivateViolation 'private-terms scope check failed: git could not name the git dir of this ~/.claude checkout (fail-closed)'
}

if ($violations.Count -gt 0) {
    Write-Host ""
    Write-Host "[BLOCKED] Forbidden content detected. $Mode aborted." -ForegroundColor Red
    Write-Host ""
    foreach ($v in $violations) { Write-Host "  - $v" -ForegroundColor Yellow }
    Write-Host ""
    if ($ptHit -lt $violations.Count) {
        Write-Host "Move secrets/machine-specific values out of tracked files (settings.local.json is gitignored)." -ForegroundColor Cyan
        Write-Host "MCP servers belong in ~/.claude.json (managed by 'claude mcp add'), never in settings.json." -ForegroundColor Cyan
        Write-Host "Plans are committed under approach A — never paste raw tokens/credentials into plan files." -ForegroundColor Cyan
    }
    if ($ptTermHits -gt 0) {
        Write-Host "Private terms come from $ptList (untracked) — do not open or quote it with tools." -ForegroundColor Cyan
        Write-Host "Replace each hit with a generic label (e.g. `"회사 repo`") and keep terms out of commit messages." -ForegroundColor Cyan
        Write-Host "A message or identity hit means rewriting that commit before pushing (git commit --amend [--reset-author], or the commit-check skill for older unpushed commits)." -ForegroundColor Cyan
        Write-Host "A hit in commits that are already on the remote main means origin/main is stale — run git fetch origin." -ForegroundColor Cyan
    }
    if ($ptNamed -gt 0) {
        Write-Host "Take the file named private-terms.txt out: git rm --cached <path> before committing, or drop it from the unpushed commits." -ForegroundColor Cyan
    }
    if ($ptHit -gt ($ptTermHits + $ptNamed)) {
        Write-Host "Private-term check error: the reported line of $ptList needs fixing by hand (do not open or rewrite the list with tools); a scope or git failure means git could not read this repo." -ForegroundColor Cyan
    }
    if ($ptHit -eq 0) {
        $cmd = 'commit'
        if ($Mode -eq 'pre-push') { $cmd = 'push' }
        Write-Host "To bypass once (NOT recommended): git $cmd --no-verify" -ForegroundColor DarkGray
    }
    exit 1
}

exit 0
