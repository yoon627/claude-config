#!/usr/bin/env bash
set -euo pipefail
unset CDPATH  # 상대경로 cd 가 CDPATH 로 다른 곳에 가거나 경로를 찍지 않게

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

args=()
while IFS= read -r line; do args+=("$line"); done < "$args_file"  # mapfile 은 bash 4+ — macOS /bin/bash 3.2 호환
case "${args[0]}" in
  */skills/jira-worklog/jira_worklog.py) ;;
  *) echo "launcher did not pass its script path" >&2; exit 1 ;;
esac
test "${args[1]}" = '--all'
test "${args[2]}" = '--comment'
test "${args[3]}" = 'space value'

# 이름만으로 부르면 경로에 구분자가 없다 — 현재 디렉터리가 자기 위치다.
rm -f "$args_file"
(cd skills/jira-worklog && JIRA_WORKLOG_TEST_ARGS="$args_file" PATH="$fake_bin:/usr/bin:/bin" bash run_worklog.sh)
IFS= read -r called < "$args_file"
expected="$(cd skills/jira-worklog && pwd -P)/jira_worklog.py"
test "$called" = "$expected" || { echo "이름만으로 불렀을 때 넘긴 경로: $called (기대 $expected)" >&2; exit 1; }

# 종료코드는 /e 6단계가 정리 여부를 가르는 신호다: 실행기가 없으면 127, 있으면 그 종료코드를 그대로.
# PATH 는 이 디렉터리 하나뿐이다 — launcher 는 실행기를 고를 때까지 외부 명령 없이 가야 한다.
# bash 는 절대경로로 부른다(이름으로 부르면 bash 를 못 찾아 다른 127 이 난다). LC_ALL=C 는 "command not found" 번역을 막는다.
bash_bin="$(command -v bash)"
mkdir -p "$root/no-runner"
rc=0
LC_ALL=C PATH="$root/no-runner" "$bash_bin" "$PWD/skills/jira-worklog/run_worklog.sh" 2> "$root/no-runner.err" || rc=$?
if grep -q 'command not found' "$root/no-runner.err"; then
  echo "launcher 가 실행기를 고르기 전에 외부 명령을 불렀다:" >&2
  cat "$root/no-runner.err" >&2
  exit 1
fi
if [ "$rc" -ne 127 ] || ! grep -q '실행기 없음' "$root/no-runner.err"; then
  echo "실행기가 없는데 종료코드 $rc ('실행기 없음' 과 127 을 기대):" >&2
  cat "$root/no-runner.err" >&2
  exit 1
fi

mkdir -p "$root/failing"
printf '%s\n' '#!/bin/sh' 'exit 3' > "$root/failing/python3"
chmod +x "$root/failing/python3"
rc=0
PATH="$root/failing" "$bash_bin" "$PWD/skills/jira-worklog/run_worklog.sh" || rc=$?
test "$rc" -eq 3 || { echo "실행기 종료코드 3 을 전달하지 않았다: $rc" >&2; exit 1; }

echo 'run_worklog.sh Python fallback, argv forwarding and exit codes passed'
