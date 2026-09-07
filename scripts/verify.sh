#!/bin/sh
# verify.sh — 이 repo 의 단일 검증 타깃. 로컬과 CI 가 같은 것을 돈다.
#
# 왜: 검증 명령이 lint.yml 에만 있어 로컬에서 재현하려면 워크플로를 읽어야 했고,
# 테스트 목록이 수기라 새 테스트가 조용히 CI 밖에 남았다(2026-09-07 실측: 실존
# 테스트 3개 누락, 그중 하나가 시크릿 유출 가드의 테스트). 여기서는 **glob 으로
# 발견**해 목록을 없앤다 — 파일을 추가하면 자동으로 검증 대상이 된다.
#
# 사용: bash scripts/verify.sh [축]
#   축: syntax | node | bash | python | shell   (생략 시 전부)
# 종료코드: 실패 1건이라도 있으면 1.
#
# 미설치 도구는 **조용히 건너뛰지 않는다** — `[skip]` 을 찍고 마지막 줄 요약에
# 남긴다. 스킵을 통과로 오인하면 로컬 초록이 CI 실패를 못 잡는다.
set -u

cd "$(dirname "$0")/.." || exit 1

axis="${1:-all}"
fail=0
skipped=''

run() { # run <label> <command...>
  label="$1"
  shift
  if out=$("$@" 2>&1); then
    printf 'ok   %s\n' "$label"
  else
    fail=$((fail + 1))
    printf 'FAIL %s\n' "$label"
    printf '%s\n' "$out" | tail -20 | sed 's/^/       /'
  fi
}

# worktree 사본을 검증 대상에서 뺀다 — 같은 파일을 두 번 돌고, 다른 브랜치의
# 깨진 중간 상태가 이 브랜치 검증을 실패시킨다.
find_repo() { find "$@" -not -path './.claude/*' -not -path './.git/*' | sort; }

if [ "$axis" = all ] || [ "$axis" = syntax ]; then
  echo '== syntax (node --check) =='
  for f in $(find_repo . -maxdepth 1 -name '*.js') $(find_repo ./scripts -name '*.js'); do
    run "$f" node --check "$f"
  done
fi

if [ "$axis" = all ] || [ "$axis" = node ]; then
  echo '== node tests =='
  for f in $(find_repo ./scripts -name '*.test.js'); do
    run "$f" node "$f"
  done
fi

if [ "$axis" = all ] || [ "$axis" = bash ]; then
  echo '== bash tests =='
  for f in $(find_repo . -name '*.test.sh') $(find_repo . -name 'test_*.sh'); do
    run "$f" bash "$f"
  done
fi

if [ "$axis" = all ] || [ "$axis" = python ]; then
  echo '== python tests =='
  if py=$(command -v python3 || command -v python); then
    for f in $(find_repo . -name 'test_*.py'); do
      run "$f" "$py" "$f"
    done
  else
    echo '[skip] python3 미설치'
    skipped="$skipped python"
  fi
fi

if [ "$axis" = all ] || [ "$axis" = shell ]; then
  echo '== shellcheck =='
  if command -v shellcheck >/dev/null 2>&1; then
    # 파일 목록을 한 번에 넘겨야 exit code 가 합쳐진다(`# shellcheck` 로 시작하는
    # 주석은 디렉티브로 파싱되므로 문장을 그 단어로 시작하지 않는다).
    sh_files=$(find_repo . -name '*.sh')
    # shellcheck disable=SC2086
    run 'shellcheck' shellcheck $sh_files
  else
    echo '[skip] shellcheck 미설치'
    skipped="$skipped shellcheck"
  fi
fi

echo
if [ "$fail" -eq 0 ]; then
  if [ -n "$skipped" ]; then
    echo "ALL PASS (skip:$skipped)"
  else
    echo 'ALL PASS'
  fi
else
  echo "FAILED: $fail"
fi
[ "$fail" -eq 0 ]
