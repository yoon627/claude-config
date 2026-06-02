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
    $cwd = ((Get-Location).Path -replace '\\', '/').TrimEnd('/')
    git worktree list | ForEach-Object {
        $path = (($_ -split '\s+', 2)[0] -replace '\\', '/').TrimEnd('/')
        if ($cwd -eq $path -or $cwd.StartsWith("$path/", [System.StringComparison]::OrdinalIgnoreCase)) { "→ $_" } else { "  $_" }
    }
}
