#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "사용법: $0 --source <skills/<name>> --target <~/.agents/skills/<name>> [--dry-run]" >&2
  echo "        $0 --file --source <~/.claude/CLAUDE.md> --target <~/.codex/AGENTS.md> [--dry-run]" >&2
}

source_path=''
target_path=''
dry_run=0
file_mode=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --source) [ "$#" -ge 2 ] || { usage; exit 2; }; source_path="$2"; shift 2 ;;
    --target) [ "$#" -ge 2 ] || { usage; exit 2; }; target_path="$2"; shift 2 ;;
    --file) file_mode=1; shift ;;
    --dry-run) dry_run=1; shift ;;
    *) usage; exit 2 ;;
  esac
done

if [ -z "$source_path" ] || [ -z "$target_path" ]; then
  usage
  exit 2
fi
conflict_help='resolve it as described in scripts/bootstrap/README.md (Codex 연결 충돌)'

if [ "$file_mode" -eq 1 ]; then
  [ -f "$source_path" ] || { echo "Codex link source missing or not a file: $source_path" >&2; exit 1; }
  source_path="$(cd -P "$(dirname "$source_path")" && pwd -P)/$(basename "$source_path")"
else
  [ -f "$source_path/SKILL.md" ] || { echo "Codex skill source missing or invalid: $source_path (SKILL.md 없음)" >&2; exit 1; }
  source_path="$(cd -P "$source_path" && pwd -P)"
fi
target_parent="$(dirname "$target_path")"

if [ -e "$target_path" ] || [ -L "$target_path" ]; then
  if [ ! -L "$target_path" ]; then
    echo "Codex link target exists and is not a link; left unchanged: $target_path — $conflict_help" >&2
    exit 1
  fi
  link_target="$(readlink "$target_path")"
  if [[ "$link_target" != /* ]]; then
    link_target="$target_parent/$link_target"
  fi
  # cd -P: `..` 를 글자로 지우지 않고 커널처럼 부모 symlink 를 먼저 푼다.
  if [ -d "$link_target" ]; then
    link_target="$(cd -P "$link_target" && pwd -P)"
  elif link_dir="$(cd -P "$(dirname "$link_target")" 2>/dev/null && pwd -P)"; then
    link_target="$link_dir/$(basename "$link_target")"
  fi
  if [ "$link_target" = "$source_path" ]; then
    echo "Codex link already points to source: $target_path"
    exit 0
  fi
  echo "Codex link target is an existing link to another or unknown source; left unchanged: $target_path — $conflict_help" >&2
  exit 1
fi

if [ "$dry_run" -eq 1 ]; then
  echo "[dry-run] create symlink: $target_path -> $source_path"
  exit 0
fi

mkdir -p "$target_parent"
ln -s "$source_path" "$target_path"
echo "Created Codex symlink: $target_path -> $source_path"
