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
#   축: syntax | node | bash | python | shell | changed   (생략 시 전부)
#   syntax 는 JS 문법(node --check)과 skill·agent frontmatter 형식(scripts/frontmatter-lint.js)을 본다.
#   changed 는 기준 브랜치(origin/HEAD)에서 갈라진 뒤 바뀐 파일(커밋·작업트리·untracked)로 축을 고른다 —
#   작업의 로컬 최종 검증용. 전 축은 CI(.github/workflows/lint.yml)와 사용자의 주기 실행이 맡는다
#   (Windows 에서 전 축은 약 50분). 테스트 줄 끝의 (Ns) 는 그 테스트의 소요 시간이다.
# 종료코드: 실패 1건이라도 있으면 1. 테스트가 77 로 끝나면 필요한 도구가 없다는 뜻이라 skip 으로 센다.
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
t_start=$(date +%s)
ALL_AXES='syntax node bash python shell'

changed_files() { # 기준 브랜치에서 갈라진 뒤 바뀐 파일(커밋·작업트리·untracked). 기준을 못 정하면 BASE_UNKNOWN 한 줄.
  def=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)
  if ! base=$(git merge-base HEAD "$def" 2>/dev/null); then
    echo BASE_UNKNOWN
    return
  fi
  # quotePath 를 꺼야 비ASCII 경로가 따옴표에 싸이지 않고, --no-renames 여야 옮기기 전 경로도 바뀐 것으로 센다.
  git -c core.quotePath=off diff --name-only --no-renames "$base"
  git -c core.quotePath=off ls-files --others --exclude-standard
}

# 바뀐 파일(stdin) → 축(ALL_AXES 순서). 확장자만이 아니라 다른 언어의 테스트가 그 파일을 읽는 경우도 넣는다:
# .sh·.ps1 → node(ps1-encoding·install-hooks·session-start-pull·native-overlap-lint 테스트),
# agents/*.md·*.toml → python(test_sync_codex_agents·test_wiki_check), SKILL.md → bash(install-codex-skill).
# 기준을 못 정했거나 verify.sh·CI·루트 git 설정이 바뀌면 전 축. 고른 축이 없으면 syntax — 빈 선택이 통과처럼 보이지 않게.
axes_for_changed() {
  pick=' '
  while IFS= read -r f; do
    case "$f" in
      '') ;;
      BASE_UNKNOWN | scripts/verify.sh | .github/* | .gitattributes | .gitignore | .editorconfig) pick=" $ALL_AXES " ;;
      *.js) pick="$pick syntax node " ;;
      *.sh | *.ps1) pick="$pick bash shell node " ;;
      *.py | *.toml) pick="$pick python " ;;
      agents/*.md) pick="$pick syntax python " ;;
      skills/*/SKILL.md) pick="$pick syntax bash " ;;
      *) pick="$pick syntax " ;;
    esac
  done
  chosen=''
  for a in $ALL_AXES; do
    case "$pick" in *" $a "*) chosen="$chosen $a" ;; esac
  done
  chosen="${chosen# }"
  echo "${chosen:-syntax}"
}

case "$axis" in
  all) axes=$ALL_AXES ;;
  changed)
    # VERIFY_CHANGED_FILES·VERIFY_PRINT_AXES 는 changed 축에서만 읽는다(테스트용 — 다른 축에 새지 않게).
    if [ "${VERIFY_CHANGED_FILES+set}" = set ]; then files=$VERIFY_CHANGED_FILES; else files=$(changed_files); fi
    axes=$(printf '%s\n' "$files" | axes_for_changed)
    if [ "${VERIFY_PRINT_AXES:-}" = 1 ]; then
      echo "$axes"
      exit 0
    fi
    [ "${VERIFY_PRINT_SLOW:-}" = 1 ] || case "$files" in
      *BASE_UNKNOWN*) echo "== changed: 기준 브랜치(origin/HEAD)와의 merge-base 를 찾지 못해 전 축 → $axes ==" ;;
      *) echo "== changed: 바뀐 파일 $(printf '%s\n' "$files" | grep -c .)개 → $axes ==" ;;
    esac
    ;;
  syntax | node | bash | python | shell) axes=$axis ;;
  *)
    echo "FAIL: 모르는 축 '$axis' — syntax | node | bash | python | shell | changed"
    exit 1
    ;;
esac
want() { case " $axes " in *" $1 "*) return 0 ;; esac; return 1; }
# 로컬 changed 에서 기본으로 건너뛰는 느린 테스트(Windows 단독 실측 30초 이상)와, 바뀌면 그래도 돌리는 경로.
# 프로세스 생성 비용(이 머신 1회 0.4~0.9초)에 수백~수천 번의 git·bash 호출이 곱해져 느리다 — 줄이는 작업은 따로.
# 형식: <테스트>|<그 테스트를 돌리게 하는 경로 패턴…>(테스트 자신은 자동 포함).
SLOW_TESTS='
scripts/pre-commit-check.test.sh|scripts/pre-commit-check.*
scripts/ci-secret-scan.test.sh|scripts/ci-secret-scan.sh scripts/pre-commit-check.*
scripts/session-start-pull.test.js|scripts/session-start-pull.sh
scripts/session-brief.test.js|scripts/session-brief.js scripts/session-start-pull.sh scripts/hook-cwd.js
scripts/session-fetch.test.js|scripts/session-fetch.js scripts/hook-cwd.js
scripts/install-hooks.test.js|scripts/install-hooks.*
scripts/native-overlap-lint.test.js|scripts/native-overlap-lint.js skills/improve/improve.sh
skills/commit-check/test_commit_units.py|skills/commit-check/commit_units.py
skills/wiki/test_wiki_check.py|skills/wiki/wiki_check.py skills/wiki/templates/*
'
slow_skipped=''
# 본문이 subshell 인 것은 호출부 루프도 f 를 쓰기 때문이다(POSIX sh 에는 local 이 없다).
slow_skip() ( # slow_skip <테스트> — changed 축이고 VERIFY_SLOW 가 아니며 그 테스트·대상이 안 바뀌었으면 0(건너뜀)
  [ "$axis" = changed ] || return 1
  [ "${VERIFY_SLOW:-}" = 1 ] && return 1
  line=$(printf '%s\n' "$SLOW_TESTS" | grep -F "$1|") || return 1
  pats="$1 ${line#*|}"
  keep=0 # 1 = 이 테스트나 대상이 바뀌어 돌린다
  set -f # 패턴이 파일시스템 glob 으로 펼쳐지지 않게
  while IFS= read -r f; do
    for p in $pats; do
      # shellcheck disable=SC2254 # $p 는 의도한 glob 패턴이다
      case "$f" in $p) keep=1 ;; esac
    done
  done <<EOF
$files
EOF
  return "$keep"
)
skip_slow() { # skip_slow <테스트> — 건너뛸 테스트면 알리고 0
  slow_skip "$1" || return 1
  printf '[slow] %s — 로컬 changed 에서 건너뜀(VERIFY_SLOW=1 로 포함, CI·전 축은 돈다)\n' "$1"
  slow_skipped="$slow_skipped $(basename "$1")"
  return 0
}
if [ "$axis" = changed ] && [ "${VERIFY_PRINT_SLOW:-}" = 1 ]; then
  printf '%s\n' "$SLOW_TESTS" | while IFS='|' read -r t _; do
    [ -n "$t" ] && slow_skip "$t" && echo "$t"
  done
  exit 0
fi

run() { # run <label> <command...> — 종료 코드 77 은 "필요한 도구 없음"(automake 관례)으로 skip 에 남긴다
  label="$1"
  shift
  t0=$(date +%s)
  out=$("$@" 2>&1)
  rc=$?
  dt=$(($(date +%s) - t0))
  if [ "$rc" -eq 0 ]; then
    printf 'ok   %s (%ss)\n' "$label" "$dt"
    # 무엇을 돌렸는지 알리는 `NOTE ` 줄(예: ps1 엔진 실행 수)은 보이기만 하고 skip 으로 세지 않는다.
    printf '%s\n' "$out" | grep '^NOTE ' | sed 's/^/       /'
    # 통과한 테스트 안의 케이스 단위 skip(`SKIP ` 줄)도 요약에 남긴다.
    if printf '%s\n' "$out" | grep -q '^SKIP '; then
      printf '%s\n' "$out" | grep '^SKIP ' | sed 's/^/       /'
      skipped="$skipped $(basename "$label")(case)"
    fi
  elif [ "$rc" -eq 77 ]; then
    printf '[skip] %s (%ss) — %s\n' "$label" "$dt" "$(printf '%s\n' "$out" | tail -1)"
    skipped="$skipped $(basename "$label")"
  else
    fail=$((fail + 1))
    printf 'FAIL %s (%ss)\n' "$label" "$dt"
    printf '%s\n' "$out" | tail -20 | sed 's/^/       /'
  fi
}

# 대상은 git 이 아는 파일(추적 + 아직 add 안 한 새 파일)만이다. find 로 훑으면
# main checkout 의 ignored 런타임 산출물(shell-snapshots·plugins·backups)까지 돌아
# CI·worktree 와 결과가 갈리고, 중첩 worktree(.claude/worktrees) 사본도 끌려온다.
# 작업트리에서 지운 추적 파일은 존재 검사로 뺀다. -z 는 비ASCII·특수문자 경로의
# quoting(core.quotePath)을 꺼 존재 검사에서 조용히 빠지는 것을 막는다.
# skills/improve/improve.sh 점검 4 가 이 발견을 bash 로 복제한다 — 바꾸면 같이 바꾼다.
repo_files() { # repo_files <pathspec...>
  git ls-files -z --cached --others --exclude-standard -- "$@" | tr '\0' '\n' | sort -u |
    while IFS= read -r f; do [ -f "$f" ] && printf '%s\n' "$f"; done
}

if want syntax; then
  echo '== syntax (node --check) =='
  for f in $(repo_files ':(glob)*.js' ':(glob)scripts/**/*.js'); do
    run "$f" node --check "$f"
  done
  # 대상 pathspec 은 skills/improve/improve.sh 점검 4 와 같다.
  echo '== syntax (frontmatter) =='
  n=0
  for f in $(repo_files ':(glob)skills/*/SKILL.md' ':(glob)agents/*.md'); do
    n=$((n + 1))
    run "$f" node scripts/frontmatter-lint.js "$f"
  done
  # 0개면 발견이 깨진 것이다 — 검사 없이 통과로 보이지 않게 실패로 센다.
  if [ "$n" -eq 0 ]; then
    fail=$((fail + 1))
    echo 'FAIL frontmatter — 대상 0개(skills/*/SKILL.md·agents/*.md)'
  fi
fi

if want node; then
  echo '== node tests =='
  for f in $(repo_files ':(glob)scripts/**/*.test.js'); do
    skip_slow "$f" && continue
    run "$f" node "$f"
  done
fi

if want bash; then
  echo '== bash tests =='
  for f in $(repo_files ':(glob)**/*.test.sh' ':(glob)**/test_*.sh'); do
    skip_slow "$f" && continue
    run "$f" bash "$f"
  done
  # ps1 tests run on every PowerShell present — Windows PowerShell 5.1 (what the hooks and most
  # users run) and pwsh differ in .NET behaviour. Windows-only tests end with 77 elsewhere.
  engines=''
  for e in pwsh powershell.exe; do command -v "$e" >/dev/null 2>&1 && engines="$engines $e"; done
  for f in $(repo_files ':(glob)**/*.test.ps1'); do
    if [ -z "$engines" ]; then
      echo "[skip] $f — PowerShell 미설치"
      skipped="$skipped $(basename "$f")"
    fi
    for e in $engines; do
      run "$f ($e)" "$e" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$f"
    done
  done
fi

if want python; then
  echo '== python tests =='
  if py=$(command -v python3 || command -v python); then
    for f in $(repo_files ':(glob)**/test_*.py'); do
      skip_slow "$f" && continue
      run "$f" "$py" "$f"
    done
  else
    echo '[skip] python3 미설치'
    skipped="$skipped python"
  fi
fi

if want shell; then
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

[ -n "$slow_skipped" ] && echo "느린 테스트 제외:$slow_skipped — CI 와 전 축(bash scripts/verify.sh)에서 돈다"
echo "총 $(($(date +%s) - t_start))s"
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
