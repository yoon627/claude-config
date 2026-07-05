# gwl — list git worktrees, marking the one that contains the current directory with '→'.
#
# zsh mirror of scripts/gwl.ps1 / scripts/prompt-gwl.py (the Claude Code `gwl`
# prompt hook): same purpose, runs in the shell with no model round-trip.
# Sourced into ~/.zshrc by scripts/install-gwl.zsh.
#
# Scope: personal worktrees under the .claude/worktrees/<name> convention, whose
# paths have no spaces — so splitting each `git worktree list` row at its first
# space yields the worktree path. The current row is matched by exact equality
# with `git rev-parse --show-toplevel`, NOT by prefix: worktrees here nest under
# the main checkout (~/.claude/.claude/worktrees/<name>), so a prefix test would
# also mark the main row whenever cwd is inside a worktree.

gwl() {
  emulate -L zsh
  local top line lpath
  top="$(git rev-parse --show-toplevel 2>/dev/null)"
  top="${top%/}"
  git worktree list | while IFS= read -r line; do
    lpath="${line%% *}"
    lpath="${lpath%/}"
    if [[ -n "$top" && "$lpath" == "$top" ]]; then
      print -r -- "→ $line"
    else
      print -r -- "  $line"
    fi
  done
}
