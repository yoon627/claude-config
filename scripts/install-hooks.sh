#!/usr/bin/env bash
# install-hooks.sh — install pre-commit and pre-push hooks in current git repo
# These hooks invoke ~/.claude/scripts/pre-commit-check.sh to guard settings.json.

set -e

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  echo "Not inside a git repo." >&2
  # git's own reason (e.g. safe.directory "dubious ownership")
  git rev-parse --show-toplevel 2>&1 >/dev/null | head -n 1 >&2 || true
  exit 1
fi

# The hooks git actually runs: shared by linked worktrees, redirected by core.hooksPath (any
# config scope). When it is not the repo's own hooks dir, another tool (husky, lefthook, ...)
# owns it — writing there would replace that tool's hooks, and .git/hooks would never run.
hook_dir="$(git rev-parse --path-format=absolute --git-path hooks)"
case "$hook_dir" in
  # git < 2.31 echoes the unknown option back on stdout instead of failing.
  --*) echo "git 2.31 or newer is required (git rev-parse --path-format)." >&2; exit 1 ;;
esac
default_dir="$(git rev-parse --path-format=absolute --git-common-dir)/hooks"
# Only core.hooksPath moves the hooks elsewhere; a symlinked .git/hooks or a hooksPath that names
# the default dir under another spelling (case-insensitive FS) is still the repo's own hooks dir.
if [ -n "$(git config --get core.hooksPath || true)" ] &&
  ! [ "$hook_dir" -ef "$default_dir" ] && [ "$hook_dir" != "$default_dir" ]; then
  echo "core.hooksPath points git at $hook_dir, so hooks in $default_dir would never run." >&2
  echo "Not installing. Call $HOME/.claude/scripts/pre-commit-check.sh from the tool that manages that directory." >&2
  exit 1
fi
mkdir -p "$hook_dir"

guard="$HOME/.claude/scripts/pre-commit-check.sh"
if [ ! -x "$guard" ]; then
  echo "Guard script not found or not executable: $guard" >&2
  exit 1
fi

# First free "<hook>.bak.<UTC time>[.<n>]" — every reinstall keeps the previous backups.
backup_path() {
  local base candidate n=1
  base="$1.bak.$(date -u +%Y%m%dT%H%M%SZ)"
  candidate="$base"
  while [ -e "$candidate" ]; do
    candidate="$base.$n"
    n=$((n + 1))
  done
  printf '%s' "$candidate"
}

# Idempotent writer: no-op if identical, back up a differing existing hook, then write.
install_hook() {
  local path="$1"
  local content="$2"
  if [ -f "$path" ]; then
    local existing backup
    existing="$(cat "$path")"
    if [ "$existing" = "$content" ]; then
      return 0
    fi
    backup="$(backup_path "$path")"
    mv "$path" "$backup"
    echo "Existing hook backed up: $backup"
  fi
  printf '%s\n' "$content" >"$path"
  chmod +x "$path"
}

write_hook() {
  local path="$1"
  local mode="$2"
  local content
  content="$(cat <<EOF
#!/bin/sh
exec "$guard" "$mode"
EOF
)"
  install_hook "$path" "$content"
}

# post-checkout: fast-forward main/master to origin when checked out (main-autopull).
# Pure shell (runs under Git Bash sh on Windows too), independent of the settings.json guard.
IFS='' read -r -d '' post_checkout <<'EOF' || true
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
EOF
post_checkout="${post_checkout%$'\n'}"

write_hook "$hook_dir/pre-commit" pre-commit
write_hook "$hook_dir/pre-push"   pre-push
install_hook "$hook_dir/post-checkout" "$post_checkout"

echo "Installed pre-commit, pre-push, and post-checkout hooks at $hook_dir"
echo "Guards check plans/*.md (and settings.json if ever tracked): staged content on commit, lines added by the pushed commits on push; post-checkout fast-forwards main/master from origin."
echo "Bypass guard once (NOT recommended): git commit --no-verify  /  git push --no-verify"
echo "Disable auto-pull: export CLAUDE_AUTOPULL_OFF=1  |  Remove: rm $hook_dir/post-checkout"
