#!/bin/sh
# verify.sh — 이 repo 의 단일 검증 타깃. 로컬과 CI 가 같은 것을 돈다.
#
# 왜: 검증 명령이 lint.yml 에만 있어 로컬에서 재현하려면 워크플로를 읽어야 했고,
# 테스트 목록이 수기라 새 테스트가 조용히 CI 밖에 남았다(2026-09-07 실측: 실존
# 테스트 3개 누락, 그중 하나가 시크릿 유출 가드의 테스트). 여기서는 **git 이 아는
# 파일 중 glob 에 맞는 것**을 발견해 목록을 없앤다 — 파일을 추가하면 자동으로 검증
# 대상이 된다.
#
# 사용: bash scripts/verify.sh [축]
#   축: syntax | node | bash | python | shell   (생략 시 전부)
# 종료코드: 실패 1건이라도 있으면 1.
#
# 미설치 도구는 **조용히 건너뛰지 않는다** — `[skip]` 을 찍고 마지막 줄 요약에
# 남긴다. 스킵을 통과로 오인하면 로컬 초록이 CI 실패를 못 잡는다.
set -u

cd "$(dirname "$0")/.." || exit 1
# 검증 대상 목록을 git 에서 얻으므로, git 이 이 디렉토리를 모르면 0개를 돌고 통과해 버린다.
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo 'FAIL: git 작업트리가 아니라 검증 대상을 찾을 수 없다'
  exit 1
fi

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

# 대상은 git 이 아는 파일(추적 + 아직 add 안 한 새 파일)만이다. find 로 훑으면
# main checkout 의 ignored 런타임 산출물(shell-snapshots·plugins·backups)까지 돌아
# CI·worktree 와 결과가 갈리고, 중첩 worktree(.claude/worktrees) 사본도 끌려온다.
# 작업트리에서 지운 추적 파일은 존재 검사로 뺀다. -z 는 비ASCII·특수문자 경로의
# quoting(core.quotePath)을 꺼 존재 검사에서 조용히 빠지는 것을 막는다.
repo_files() { # repo_files <pathspec...>
  git ls-files -z --cached --others --exclude-standard -- "$@" | tr '\0' '\n' | sort -u |
    while IFS= read -r f; do [ -f "$f" ] && printf '%s\n' "$f"; done
}

if [ "$axis" = all ] || [ "$axis" = syntax ]; then
  echo '== syntax (node --check) =='
  for f in $(repo_files ':(glob)*.js' ':(glob)scripts/**/*.js'); do
    run "$f" node --check "$f"
  done
fi

if [ "$axis" = all ] || [ "$axis" = node ]; then
  echo '== node tests =='
  for f in $(repo_files ':(glob)scripts/**/*.test.js'); do
    run "$f" node "$f"
  done
fi

if [ "$axis" = all ] || [ "$axis" = bash ]; then
  echo '== bash tests =='
  for f in $(repo_files ':(glob)**/*.test.sh' ':(glob)**/test_*.sh'); do
    run "$f" bash "$f"
  done
fi

if [ "$axis" = all ] || [ "$axis" = python ]; then
  echo '== python tests =='
  if py=$(command -v python3 || command -v python); then
    for f in $(repo_files ':(glob)**/test_*.py'); do
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
    sh_files=$(repo_files ':(glob)**/*.sh')
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
