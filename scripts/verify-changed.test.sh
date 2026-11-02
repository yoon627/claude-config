#!/usr/bin/env bash
# verify.sh changed — 바뀐 파일에서 돌릴 축을 고르는 규칙과, 실제 git 에서 바뀐 파일을 모으는 경로.
set -u
cd "$(dirname "$0")/.." || exit 1
REPO=$PWD
ALL='syntax node bash python shell'

fail=0
check() { # check <기대 축> [바뀐 파일...] — 목록을 주입해 규칙만 본다
  want="$1"
  shift
  got=$(VERIFY_PRINT_AXES=1 VERIFY_CHANGED_FILES="$(printf '%s\n' "$@")" sh scripts/verify.sh changed)
  rc=$?
  if [ "$rc" -ne 0 ] || [ "$got" != "$want" ]; then
    echo "FAIL [$*] want='$want' got='$got' rc=$rc"
    fail=1
  fi
}

check 'syntax node' scripts/a.js
check 'syntax' README.md
check 'node bash shell' scripts/a.sh
check 'node bash shell' scripts/a.ps1
check 'shell' scripts/a.zsh
check 'python' skills/x/test_a.py
check 'python' skills/wiki/templates/wiki-check.toml
check 'syntax python' agents/x.md
check 'syntax bash' skills/x/SKILL.md
check 'syntax node python' scripts/a.js skills/x/b.py
check 'syntax node bash shell' README.md scripts/a.sh
check "$ALL" scripts/verify.sh
check "$ALL" .github/workflows/lint.yml
check "$ALL" .gitattributes
check "$ALL" BASE_UNKNOWN
check 'syntax'

# 느린 테스트: 무관한 변경이면 로컬 changed 에서 건너뛰고, 그 테스트나 대상이 바뀌면 돌린다.
slow() { # slow <기대: 건너뛸 테스트 수> <꼭 돌려야 할 테스트(없으면 -)> [바뀐 파일...]
  want_n="$1" must="$2"
  shift 2
  got=$(VERIFY_PRINT_SLOW=1 VERIFY_CHANGED_FILES="$(printf '%s\n' "$@")" sh scripts/verify.sh changed)
  n=$(printf '%s\n' "$got" | grep -c .)
  if [ "$n" -ne "$want_n" ] || { [ "$must" != - ] && printf '%s\n' "$got" | grep -qxF "$must"; }; then
    echo "FAIL [slow $*] want=$want_n skipped (keep $must) got: $(printf '%s ' "$got")"
    fail=1
  fi
}
slow 6 - README.md
slow 5 skills/wiki/test_wiki_check.py skills/wiki/templates/wiki-check.toml
slow 5 skills/commit-check/test_commit_units.py skills/commit-check/commit_units.py
slow 5 scripts/pre-commit-check.test.sh scripts/pre-commit-check.ps1
slow 5 scripts/session-brief.test.js scripts/session-brief.js
slow 5 scripts/session-brief.test.js scripts/dlc-signal.js
slow 5 scripts/session-brief.test.js scripts/plan-match.js
slow 4 scripts/session-start-pull.test.js scripts/session-start-pull.sh scripts/hook-cwd.js
slow 5 scripts/install-hooks.test.js scripts/install-hooks.test.js
got=$(VERIFY_SLOW=1 VERIFY_PRINT_SLOW=1 VERIFY_CHANGED_FILES=README.md sh scripts/verify.sh changed)
if [ -n "$got" ]; then
  echo "FAIL [VERIFY_SLOW=1] 건너뛰는 테스트가 없어야 한다: $got"
  fail=1
fi

# 모르는 축은 아무것도 돌리지 않고 통과로 보이면 안 된다.
out=$(sh scripts/verify.sh bogus 2>&1)
if [ $? -ne 1 ]; then
  echo "FAIL [bogus] exit 1 이어야 한다: $out"
  fail=1
fi

# 실제 git: 기준 브랜치 뒤의 커밋·rename(옛 경로)·untracked 를 모으고, 기준이 없으면 전 축.
tmp=$(mktemp -d) || exit 1
trap 'rm -rf "$tmp"' EXIT

# CI 에서는 축 단위 도구 부재가 FAIL 이다 — shellcheck·zsh 가 없는 PATH 로 shell 축을 돌린다(로컬은 [skip] 으로 통과).
# 링크가 아니라 절대경로를 exec 하는 래퍼다: Git Bash 의 ln -s 는 복사본을 만들고, 복사된 exe 는 자기 DLL 을 못 찾는다(test_launcher.sh 와 같은 방식).
mkdir "$tmp/bin"
sh_bin=$(command -v sh)
for t in sh bash git grep sed awk tail head cut tr date basename dirname sort uniq wc cat ls rm mkdir; do
  p=$(command -v "$t" 2>/dev/null)
  case $p in /*) printf '#!/bin/sh\nexec "%s" "$@"\n' "$p" > "$tmp/bin/$t"; chmod +x "$tmp/bin/$t" ;; esac
done
out=$(CI=1 PATH="$tmp/bin" "$sh_bin" scripts/verify.sh shell 2>&1); rc=$?
if [ "$rc" -eq 0 ] || ! printf '%s\n' "$out" | grep -q '^FAIL shellcheck'; then
  echo "FAIL [CI missing tool] rc=$rc (want 1 + FAIL shellcheck): $(printf '%s' "$out" | tail -3)"
  fail=1
fi
out=$(CI='' PATH="$tmp/bin" "$sh_bin" scripts/verify.sh shell 2>&1); rc=$?
if [ "$rc" -ne 0 ] || ! printf '%s\n' "$out" | grep -q '^\[skip\] shellcheck'; then
  echo "FAIL [local missing tool] rc=$rc (want 0 + [skip] shellcheck): $(printf '%s' "$out" | tail -3)"
  fail=1
fi
g() { git -C "$tmp/work" -c user.name=t -c user.email=t@t "$@" >/dev/null 2>&1; }
git init -q --bare -b main "$tmp/origin.git"
git init -q -b main "$tmp/work"
mkdir -p "$tmp/work/scripts"
cp "$REPO/scripts/verify.sh" "$tmp/work/scripts/verify.sh"
echo x >"$tmp/work/scripts/old.js"
g add -A && g commit -qm base && g remote add origin "$tmp/origin.git" && g push -q origin main && g remote set-head origin main
g switch -qc feat
echo x >"$tmp/work/a.py" && g add a.py && g commit -qm py
g mv scripts/old.js scripts/old.txt && g commit -qm rename
# untracked 비ASCII .sh — untracked 수집과 quotePath 처리가 빠지면 bash·shell 이 사라진다.
echo x >"$tmp/work/한.sh"
got=$(cd "$tmp/work" && VERIFY_PRINT_AXES=1 sh scripts/verify.sh changed)
if [ "$got" != "$ALL" ]; then
  echo "FAIL [git] want='$ALL' got='$got'"
  fail=1
fi
g remote remove origin
got=$(cd "$tmp/work" && VERIFY_PRINT_AXES=1 sh scripts/verify.sh changed)
if [ "$got" != "$ALL" ]; then
  echo "FAIL [git, 기준 없음] want='$ALL' got='$got'"
  fail=1
fi

# 대상이 바뀐 느린 테스트는 건너뛰지 않고 그 경로로 돌아야 한다(빈 경로로 돌면 "bash: : No such file").
mkdir -p "$tmp/run/scripts"
git init -q -b main "$tmp/run"
cp "$REPO/scripts/verify.sh" "$tmp/run/scripts/verify.sh"
printf 'echo slow-ran\n' >"$tmp/run/scripts/pre-commit-check.test.sh"
echo x >"$tmp/run/scripts/pre-commit-check.ps1"
git -C "$tmp/run" add -A
# fixture 가 느린 목록에 있어야 이 검사가 뜻을 가진다(목록 밖이면 건너뛰기 경로를 아예 타지 않는다).
listed=$(cd "$tmp/run" && VERIFY_PRINT_SLOW=1 VERIFY_CHANGED_FILES=README.md sh scripts/verify.sh changed)
case "$listed" in
  *scripts/pre-commit-check.test.sh*) ;;
  *) echo "FAIL [slow 실행] fixture 가 느린 목록에 없다: $listed"; fail=1 ;;
esac
out=$(cd "$tmp/run" && VERIFY_CHANGED_FILES=scripts/pre-commit-check.ps1 sh scripts/verify.sh changed 2>&1)
case "$out" in
  *'ok   scripts/pre-commit-check.test.sh'*) ;;
  *) echo "FAIL [slow 실행] 대상이 바뀐 느린 테스트가 그 경로로 돌지 않았다: $out"; fail=1 ;;
esac

[ "$fail" -eq 0 ] && echo 'verify-changed: ok'
exit "$fail"
