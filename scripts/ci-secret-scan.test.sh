#!/usr/bin/env bash
# Tests for ci-secret-scan.sh on fixtures shaped like a CI checkout: the branch under test is
# already on a remote-tracking ref, so a guard that trusted tracking refs would scan nothing.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
SCAN="$DIR/ci-secret-scan.sh"
T="$(mktemp -d)" || exit 1
trap 'rm -rf "$T"' EXIT
TOKEN='sk-ant-''0123456789abcdefghij0123'
PAT='github_pat_''ABCDEFGHIJKLMNOPQRSTUV0123'   # pattern name has parentheses: GitHub PAT (fine)
BEARER=$'Bearer\tzyxwvutsrqponmlkjihgfedcba98'  # the guard keeps the tab inside the matched value
ZERO=0000000000000000000000000000000000000000
pass=0; fail=0

g() { git -C "$1" -c user.email=t@t -c user.name=t -c commit.gpgsign=false "${@:2}"; }
commit() { mkdir -p "$1/$(dirname "$2")"; printf '%s\n' "$3" > "$1/$2"; g "$1" add -f "$2"; g "$1" commit -q -m "c $2"; g "$1" rev-parse HEAD; }
check() { # <desc> <expected rc> <output must contain each of 'a&&b', or -> <cmd...>
  local desc="$1" want="$2" needle="$3" out rc ok=1 part
  shift 3
  out="$("$@" 2>&1)"; rc=$?
  [ "$rc" = "$want" ] || ok=0
  if [ "$needle" != - ]; then
    while IFS= read -r part; do [[ "$out" == *"$part"* ]] || ok=0; done <<<"${needle//&&/$'\n'}"
  fi
  if [ "$ok" = 1 ]; then
    pass=$((pass+1))
  else
    fail=$((fail+1))
    printf '✗ %s (expected rc=%s with "%s", got %s)\n%s\n' "$desc" "$want" "$needle" "$rc" "$(printf '%s\n' "$out" | head -5 | sed 's/^/    /')"
  fi
}
scan_in() { (cd "$1" && bash "$SCAN" "${@:2}"); }

# origin + a CI-like clone whose remote-tracking refs already hold the branch under test
git init -q --bare -b main "$T/origin.git"
git clone -q "$T/origin.git" "$T/src" 2>/dev/null
commit "$T/src" plans/2026-01-01-old/old-plan.md "old $TOKEN" >/dev/null
base="$(commit "$T/src" README.md 'base')"
g "$T/src" push -q origin main
g "$T/src" switch -q -c leak
commit "$T/src" plans/2026-09-26-x/x-plan.md "pasted $TOKEN and $PAT and $BEARER" >/dev/null
g "$T/src" push -q origin leak
g "$T/src" switch -q -c clean main
pr="$(commit "$T/src" plans/2026-09-26-y/y-plan.md 'nothing secret')"
g "$T/src" push -q origin clean
g "$T/src" switch -q main   # main moves on after the PR branched off, and gains a token of its own
main_tip="$(commit "$T/src" plans/2026-09-26-z/z-plan.md "main side $TOKEN")"
g "$T/src" push -q origin main
# a token outside plans/: this repo's scope scans every added line — the token is assembled at run
# time so this file never holds a second token shape
WIDE_TOKEN='sk-ant-''zyxwvutsrqponmlkjihgfedcba9876'
g "$T/src" switch -q -c wide main
commit "$T/src" docs/notes.md "see $WIDE_TOKEN" >/dev/null
g "$T/src" push -q origin wide
g "$T/src" switch -q main
# two more direct pushes to main, as CI then sees them: the checkout is at the pushed tip under the
# name origin/main and the base is the previous tip — one adds a token outside plans/, the next only
# in its commit message (tokens assembled at run time)
MAIN_TOKEN='sk-ant-''0123456789zyxwvutsrqponmlkjih'
main_tip2="$(commit "$T/src" src/config.sh "KEY=$MAIN_TOKEN")"
g "$T/src" push -q origin main
mkdir -p "$T/src/src"; printf 'clean\n' > "$T/src/src/notes.md"; g "$T/src" add src/notes.md
g "$T/src" commit -q -m "debug: $MAIN_TOKEN"; main_tip3="$(g "$T/src" rev-parse HEAD)"
g "$T/src" push -q origin main
git clone -q "$T/origin.git" "$T/ci" 2>/dev/null
g "$T/ci" fetch -q origin '+refs/heads/*:refs/remotes/origin/*'

g "$T/ci" switch -q --detach origin/leak
check 'token added in base..HEAD is blocked even though origin/leak already has it' 1 'token pattern' scan_in "$T/ci" "$base"
log_clean() { ! scan_in "$1" "$2" 2>&1 | grep -qE 'sk-ant-|github_pat_|zyxwvutsrq|no-verify'; }
check 'matched values (a pattern name with parentheses, a tab inside the value) and the --no-verify hint stay out of the CI log' 0 - log_clean "$T/ci" "$base"
g "$T/ci" switch -q --detach origin/wide
check 'a token outside plans/ is reported by pattern, path and line (this repo scans every added line)' 1 \
  'token pattern (Anthropic key): pushed docs/notes.md:1' scan_in "$T/ci" "$main_tip"
check 'the path:line report passes the CI log mask unmasked and the value stays out' 0 - log_clean "$T/ci" "$main_tip"
log_clean2() { ! scan_in "$1" "$2" "$3" 2>&1 | grep -qE 'sk-ant-|0123456789zyxw|no-verify'; }
g "$T/ci" switch -q --detach origin/main
check 'CI main push: HEAD is origin/main, base is the previous tip — a token outside plans/ is still blocked' 1 \
  'token pattern (Anthropic key): pushed src/config.sh:1' scan_in "$T/ci" "$main_tip" "$main_tip2"
check 'CI main push: a token only in the commit message is blocked, reported by short sha' 1 \
  "token pattern (Anthropic key): message $(g "$T/ci" rev-parse --short "$main_tip3")" scan_in "$T/ci" "$main_tip2" "$main_tip3"
check 'CI main push: neither report shows the value' 0 - log_clean2 "$T/ci" "$main_tip" "$main_tip3"
g "$T/ci" switch -q --detach origin/leak
git clone -q --depth 1 --branch leak "file://$T/origin.git" "$T/shallow" 2>/dev/null
check 'a shallow checkout is refused rather than scanned from its cut-off' 1 'shallow checkout' scan_in "$T/shallow" "$ZERO"

g "$T/ci" switch -q --detach origin/clean
check 'clean range passes; a token only before base is not rescanned' 0 - scan_in "$T/ci" "$base"
check 'all-zero base (new branch) scans the whole history' 1 'no base in checkout&&whole history&&token pattern' scan_in "$T/ci" "$ZERO"
check 'empty base scans the whole history' 1 'no base in checkout&&whole history&&token pattern' scan_in "$T/ci" ''
check 'a base missing from the checkout (force push) scans the whole history instead of failing' 1 'not in this checkout&&no base in checkout&&token pattern' \
  scan_in "$T/ci" 1234567890abcdef1234567890abcdef12345678

# a pull_request run checks out a merge of the PR into main; scanning that merge would blame the
# PR for main's own additions, so the workflow scans the PR head against the base tip instead
g "$T/ci" switch -q --detach "$main_tip"
g "$T/ci" merge -q --no-edit "$pr" >/dev/null
check 'PR head vs base tip: main-side token is not the PR'"'"'s' 0 - scan_in "$T/ci" "$main_tip" "$pr"
check 'scanning the merge commit instead would blame the PR for it' 1 'token pattern' scan_in "$T/ci" "$main_tip" HEAD

printf 'ci-secret-scan.test.sh: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
