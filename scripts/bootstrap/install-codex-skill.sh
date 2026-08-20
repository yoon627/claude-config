#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "사용법: $0 --source <skills/jira-worklog> --target <~/.agents/skills/jira-worklog> [--dry-run]" >&2
}

source_path=''
target_path=''
dry_run=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --source) [ "$#" -ge 2 ] || { usage; exit 2; }; source_path="$2"; shift 2 ;;
    --target) [ "$#" -ge 2 ] || { usage; exit 2; }; target_path="$2"; shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    *) usage; exit 2 ;;
  esac
done

[ -n "$source_path" ] && [ -n "$target_path" ] || { usage; exit 2; }
[ -f "$source_path/SKILL.md" ] || { echo "Codex skill source missing or invalid: $source_path (SKILL.md 없음)" >&2; exit 1; }

source_path="$(cd "$source_path" && pwd -P)"
target_parent="$(dirname "$target_path")"

if [ -e "$target_path" ] || [ -L "$target_path" ]; then
  if [ ! -L "$target_path" ]; then
    echo "Codex skill target exists and is not a link; left unchanged: $target_path" >&2
    exit 1
  fi
  link_target="$(readlink "$target_path")"
  if [[ "$link_target" != /* ]]; then
    link_target="$target_parent/$link_target"
  fi
  if [ -d "$link_target" ]; then
    link_target="$(cd "$link_target" && pwd -P)"
  else
    link_target="$(cd "$(dirname "$link_target")" && pwd -P)/$(basename "$link_target")"
  fi
  if [ "$link_target" = "$source_path" ]; then
    echo "Codex jira-worklog link already points to source: $target_path"
    exit 0
  fi
  echo "Codex skill target is an existing link to another or unknown source; left unchanged: $target_path" >&2
  exit 1
fi

if [ "$dry_run" -eq 1 ]; then
  echo "[dry-run] create symlink: $target_path -> $source_path"
  exit 0
fi

mkdir -p "$target_parent"
ln -s "$source_path" "$target_path"
echo "Created Codex jira-worklog symlink: $target_path -> $source_path"
