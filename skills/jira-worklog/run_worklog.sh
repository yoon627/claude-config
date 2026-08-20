#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$BASH_SOURCE")" && pwd -P)"
script_path="$script_dir/jira_worklog.py"

if command -v uv >/dev/null 2>&1; then
  uv_cache_dir="$HOME/.claude/.tmp/jira-worklog-uv-cache"
  if [ -n "$(printenv UV_CACHE_DIR 2>/dev/null)" ]; then
    uv_cache_dir="$(printenv UV_CACHE_DIR)"
  fi
  exec uv --cache-dir "$uv_cache_dir" run --no-project python "$script_path" "$@"
fi
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$script_path" "$@"
fi
if command -v python >/dev/null 2>&1; then
  exec python "$script_path" "$@"
fi

echo "jira-worklog 실행기 없음: uv, python3, python 중 하나가 필요합니다." >&2
exit 127
