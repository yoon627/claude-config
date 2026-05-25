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

write_hook() {
  local path="$1"
  local mode="$2"
  local content
  content="$(cat <<EOF
#!/bin/sh
exec "$guard" "$mode"
EOF
)"
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

write_hook "$hook_dir/pre-commit" pre-commit
write_hook "$hook_dir/pre-push"   pre-push

echo "Installed pre-commit and pre-push hooks at $hook_dir"
echo "These guards check staged/HEAD settings.json for forbidden keys and token patterns."
echo "Bypass once (NOT recommended): git commit --no-verify  /  git push --no-verify"
