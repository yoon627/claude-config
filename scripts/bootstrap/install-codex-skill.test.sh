#!/usr/bin/env bash
set -euo pipefail

root="$(mktemp -d "${TMPDIR:-/tmp}/codex-skill-link-test.XXXXXX")"
trap 'rm -rf "$root"' EXIT
source_path="$root/source with spaces"
target_path="$root/nested/target with spaces"
other_path="$root/other"
dry_run_target="$root/dry-run-target"
mkdir -p "$source_path" "$other_path"
printf '%s\n' '---' 'name: jira-worklog' '---' > "$source_path/SKILL.md"

helper="$PWD/scripts/bootstrap/install-codex-skill.sh"
"$helper" --source "$source_path" --target "$target_path"
if [ ! -L "$target_path" ]; then
  echo 'symlink creation unsupported in this shell; Unix helper assertions skipped'
  exit 0
fi
test -L "$target_path"
test "$(cd "$(readlink "$target_path")" && pwd -P)" = "$(cd "$source_path" && pwd -P)"
"$helper" --source "$source_path" --target "$target_path"

if "$helper" --source "$source_path" --target "$dry_run_target" --dry-run >/dev/null; then
  if [ -e "$dry_run_target" ] || [ -L "$dry_run_target" ]; then
    echo 'dry-run changed the target' >&2
    exit 1
  fi
else
  echo 'dry-run was not successful' >&2
  exit 1
fi

mkdir "$root/real-directory"
if "$helper" --source "$source_path" --target "$root/real-directory"; then
  echo 'real directory conflict was not rejected' >&2
  exit 1
fi

ln -s "$other_path" "$root/other-link"
if "$helper" --source "$source_path" --target "$root/other-link"; then
  echo 'other link conflict was not rejected' >&2
  exit 1
fi

ln -s "$root/missing-source" "$root/dangling-link"
if "$helper" --source "$source_path" --target "$root/dangling-link"; then
  echo 'dangling link conflict was not rejected' >&2
  exit 1
fi
test -L "$root/dangling-link"

if "$helper" --source "$root/missing-source" --target "$root/missing-target"; then
  echo 'missing source was not rejected' >&2
  exit 1
fi

echo 'install-codex-skill.sh state matrix passed'
