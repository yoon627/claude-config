#!/usr/bin/env bash
# install-hooks.sh — install pre-commit and pre-push hooks in current git repo
# These hooks invoke ~/.claude/scripts/pre-commit-check.sh to guard settings.json.

set -e

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  echo "Not inside a git repo." >&2
  exit 1
fi

hook_dir="$repo_root/.git/hooks"
mkdir -p "$hook_dir"

guard="$HOME/.claude/scripts/pre-commit-check.sh"
if [ ! -x "$guard" ]; then
  echo "Guard script not found or not executable: $guard" >&2
  exit 1
fi

# Idempotent writer: no-op if identical, back up a differing existing hook, then write.
install_hook() {
  local path="$1"
  local content="$2"
  if [ -f "$path" ]; then
    local existing
    existing="$(cat "$path")"
    if [ "$existing" = "$content" ]; then
      return 0
    fi
    mv "$path" "$path.bak"
    echo "Existing hook backed up: $path.bak"
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
echo "Guards check staged/HEAD settings.json; post-checkout fast-forwards main/master from origin."
echo "Bypass guard once (NOT recommended): git commit --no-verify  /  git push --no-verify"
echo "Disable auto-pull: export CLAUDE_AUTOPULL_OFF=1  |  Remove: rm $hook_dir/post-checkout"
