#!/usr/bin/env bash
set -euo pipefail

root="$(mktemp -d "/tmp/jira-worklog-launcher-test.XXXXXX")"
trap 'rm -rf "$root"' EXIT
fake_bin="$root/bin"
args_file="$root/args"
mkdir -p "$fake_bin"

# shellcheck disable=SC2016  # 스텁 본문은 스텁 실행 시점에 확장돼야 한다
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'printf "%s\n" "$@" > "$JIRA_WORKLOG_TEST_ARGS"' \
  > "$fake_bin/python3"
chmod +x "$fake_bin/python3"

JIRA_WORKLOG_TEST_ARGS="$args_file" \
PATH="$fake_bin:/usr/bin:/bin" \
bash "$PWD/skills/jira-worklog/run_worklog.sh" --all --comment "space value"

mapfile -t args < "$args_file"
case "${args[0]}" in
  */skills/jira-worklog/jira_worklog.py) ;;
  *) echo "launcher did not pass its script path" >&2; exit 1 ;;
esac
test "${args[1]}" = '--all'
test "${args[2]}" = '--comment'
test "${args[3]}" = 'space value'

echo 'run_worklog.sh Python fallback and argv forwarding passed'
