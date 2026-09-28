# gwl — list git worktrees, marking the one that contains the current directory with '→'.
#
# A PowerShell shortcut mirroring scripts/prompt-gwl.py (the Claude Code `gwl`
# prompt hook): same purpose, runs in the shell with no model round-trip.
# Dot-sourced into $PROFILE by scripts/install-gwl.ps1.
#
# Scope: personal worktrees under the .claude/worktrees/<name> convention, whose
# paths have no spaces — so a simple `git worktree list` split is enough.
# (prompt-gwl.py uses --porcelain because it must handle arbitrary projects.)
# Saved as UTF-8 with BOM so '→' survives Windows PowerShell 5.1; PS 7 reads either.

function gwl {
    # git's own toplevel, like gwl.zsh: `git worktree list` prints the same physical path, so a
    # symlinked cwd or a differently cased drive letter still matches.
    $top = git rev-parse --show-toplevel 2>$null
    $cwd = ($(if ($LASTEXITCODE -eq 0 -and $top) { $top } else { (Get-Location).Path }) -replace '\\', '/').TrimEnd('/')
    $rows = @(git worktree list | ForEach-Object {
        [pscustomobject]@{ Line = $_; Path = (($_ -split '\s+', 2)[0] -replace '\\', '/').TrimEnd('/') }
    })
    # Worktrees nest under the main checkout (.claude/worktrees/<name>), so only the longest matching path is current.
    $current = $rows |
        Where-Object { $cwd.Equals($_.Path, [System.StringComparison]::OrdinalIgnoreCase) -or $cwd.StartsWith("$($_.Path)/", [System.StringComparison]::OrdinalIgnoreCase) } |
        Sort-Object { $_.Path.Length } -Descending | Select-Object -First 1
    foreach ($row in $rows) { if ([object]::ReferenceEquals($row, $current)) { "→ $($row.Line)" } else { "  $($row.Line)" } }
}
