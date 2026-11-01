#!/usr/bin/env bash
# collect-state.sh 회귀 테스트 — mergedToLocalBase 는 브랜치 이름을 글자 그대로 맞춰야 한다:
# `feat.x` 가 정규식으로 읽히면 로컬 default 에 머지된 `featax` 에 맞아 true(삭제 false-positive)가 된다.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d)" || exit 1
trap 'rm -rf "$T"' EXIT
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE
R="$T/repo"
g() { git -C "$R" -c user.name=t -c user.email=t@t -c commit.gpgsign=false "$@" >/dev/null 2>&1; }
commit() { echo x >"$R/$1" && g add "$1" && g commit -qm "$1"; }

git init -q -b main "$R"
commit base
g switch -qc featax && commit featax
g switch -q main && g merge -q --ff-only featax
g switch -qc feat.x && commit feat.x

fail=0
field() { (cd "$R" && bash "$DIR/collect-state.sh") | sed -n "s/^$1: //p"; }
check() { # check <branch> <want mergedToLocalBase>
  g switch -q "$1"
  got=$(field mergedToLocalBase)
  if [ "$got" != "$2" ]; then
    echo "FAIL $1: mergedToLocalBase want=$2 got=$got"
    fail=1
  fi
}
check feat.x false
check featax true

[ "$fail" -eq 0 ] && echo 'collect-state: ok'
exit "$fail"
