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
expect_output() {
  case "$1" in
    *"$2"*) ;;
    *) echo "expected output containing '$2', got: $1" >&2; exit 1 ;;
  esac
}

out="$("$helper" --source "$source_path" --target "$target_path")"
if [ ! -L "$target_path" ]; then
  echo 'symlink creation unsupported in this shell; Unix helper assertions skipped'
  exit 0
fi
expect_output "$out" 'Created Codex symlink'
test -L "$target_path"
test "$(cd "$(readlink "$target_path")" && pwd -P)" = "$(cd "$source_path" && pwd -P)"
expect_output "$("$helper" --source "$source_path" --target "$target_path")" 'already points to source'

if out="$("$helper" --source "$source_path" --target "$dry_run_target" --dry-run)"; then
  expect_output "$out" '[dry-run] create symlink'
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

# --file: 파일 source(~/.codex/AGENTS.md -> ~/.claude/CLAUDE.md)
file_source="$root/claude dir/CLAUDE.md"
codex_home="$root/codex home"
mkdir -p "$root/claude dir"
printf 'rules\n' > "$file_source"
expect_output "$("$helper" --file --source "$file_source" --target "$codex_home/AGENTS.md")" 'Created Codex symlink'
test -L "$codex_home/AGENTS.md"
test "$(cat "$codex_home/AGENTS.md")" = rules
expect_output "$("$helper" --file --source "$file_source" --target "$codex_home/AGENTS.md")" 'already points to source'

ln -s "../claude dir/CLAUDE.md" "$codex_home/RELATIVE.md"
expect_output "$("$helper" --file --source "$file_source" --target "$codex_home/RELATIVE.md")" 'already points to source'

expect_output "$("$helper" --file --source "$file_source" --target "$codex_home/DRY.md" --dry-run)" '[dry-run] create symlink'
if [ -e "$codex_home/DRY.md" ] || [ -L "$codex_home/DRY.md" ]; then
  echo 'file dry-run changed the target' >&2
  exit 1
fi

printf 'imported copy\n' > "$codex_home/REAL.md"
if "$helper" --file --source "$file_source" --target "$codex_home/REAL.md"; then
  echo 'real file conflict was not rejected' >&2
  exit 1
fi
test "$(cat "$codex_home/REAL.md")" = 'imported copy'

if "$helper" --file --source "$source_path" --target "$codex_home/FROM-DIR.md"; then
  echo 'directory source with --file was not rejected' >&2
  exit 1
fi

ln -s "$other_path" "$codex_home/OTHER.md"
ln -s "$root/missing-dir/AGENTS.md" "$codex_home/DANGLING.md"
for conflict in OTHER.md DANGLING.md; do
  if "$helper" --file --source "$file_source" --target "$codex_home/$conflict"; then
    echo "--file conflict $conflict was not rejected" >&2
    exit 1
  fi
done
if "$helper" --file --source "$root/missing.md" --target "$codex_home/MISSING.md"; then
  echo '--file missing source was not rejected' >&2
  exit 1
fi

# 부모가 symlink 인 자리의 `..` 상대 링크는 커널처럼 물리 경로로 풀어야 한다 — 논리 경로로 풀면
# 다른 파일(decoy)을 가리키는데도 source 로 오판한다.
mkdir -p "$root/elsewhere/codex" "$root/elsewhere/claude dir"
printf 'decoy\n' > "$root/elsewhere/claude dir/CLAUDE.md"
ln -s "$root/elsewhere/codex" "$root/codex-link"
ln -s "../claude dir/CLAUDE.md" "$root/codex-link/AGENTS.md"
if "$helper" --file --source "$file_source" --target "$root/codex-link/AGENTS.md"; then
  echo 'relative link through a symlinked parent was judged as pointing to source' >&2
  exit 1
fi

# setup.sh 의 CODEX_SKILLS 는 실제 skill 이어야 한다
codex_skills="$(sed -n 's/^CODEX_SKILLS="\(.*\)"$/\1/p' scripts/bootstrap/setup.sh)"
[ -n "$codex_skills" ] || { echo 'CODEX_SKILLS not found in setup.sh' >&2; exit 1; }
for name in $codex_skills; do
  [ -f "skills/$name/SKILL.md" ] || { echo "CODEX_SKILLS lists missing skill: $name" >&2; exit 1; }
done

echo 'install-codex-skill.sh state matrix passed'
