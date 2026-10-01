#!/usr/bin/env bash
set -euo pipefail

# 실행기를 고르기 전에는 외부 명령(dirname 등)을 부르지 않는다 — PATH 에 아무것도 없어도 127 로 끝나야 한다.
# `\` 도 구분자로 본다: Git Bash 는 C:\… 경로로도 실행된다.
script_name=${BASH_SOURCE[0]##*[\\/]}
script_dir=${BASH_SOURCE[0]%"$script_name"}
script_dir="$(cd "${script_dir:-.}" && pwd -P)"
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
