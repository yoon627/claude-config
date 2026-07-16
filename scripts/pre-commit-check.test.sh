#!/usr/bin/env bash
# Fixture-based tests for pre-commit-check.sh.
# Stages real files in throwaway git repos and asserts the guard blocks/allows correctly.
set -u

GUARD="$(cd "$(dirname "$0")" && pwd)/pre-commit-check.sh"
pass=0; fail=0

# assert_precommit <expect: block|allow> <desc> — repo already prepared in $REPO with files staged.
run_precommit() { ( cd "$REPO" && bash "$GUARD" pre-commit >/dev/null 2>&1 ); }

check() { # <block|allow> <desc>
  local expect="$1" desc="$2" rc
  run_precommit; rc=$?
  if { [ "$expect" = block ] && [ $rc -ne 0 ]; } || { [ "$expect" = allow ] && [ $rc -eq 0 ]; }; then
    pass=$((pass+1))
  else
    fail=$((fail+1)); printf '✗ %s (expected %s, exit=%d)\n' "$desc" "$expect" "$rc"
  fi
}

newrepo() {
  REPO="$(mktemp -d)"
  git -C "$REPO" init -q
  git -C "$REPO" config user.email t@t; git -C "$REPO" config user.name t
}
stage() { mkdir -p "$REPO/$(dirname "$1")"; printf '%s' "$2" > "$REPO/$1"; git -C "$REPO" add -f "$1"; }

# --- regression: settings.json ---
newrepo; stage settings.json '{"model":"opus"}'
check allow 'clean settings.json → allow'
newrepo; stage settings.json '{"mcpServers":{}}'
check block 'settings.json forbidden key → block'
newrepo; stage settings.json '{"k":"sk-ant-0123456789abcdefghij0123"}'
check block 'settings.json anthropic token → block'

# --- new: plans/*.md secret scan ---
newrepo; stage plans/2026-07-05-x/x-plan.md '# Goal
정상 plan 내용, 시크릿 없음.'
check allow 'clean plan → allow'
newrepo; stage plans/2026-07-05-x/x-plan.md 'debug 로그: sk-ant-0123456789abcdefghij0123 붙여넣음'
check block 'plan with anthropic key → block'
newrepo; stage plans/2026-07-05-x/x-plan.md 'DB: postgres://admin:s3cretpw@db.host:5432/app'
check block 'plan with DB URL creds → block'
newrepo; stage plans/2026-07-05-x/x-plan.md 'curl -H "Authorization: Bearer abcdefghij0123456789xyz"'
check block 'plan with bearer token → block'
newrepo; stage plans/2026-07-05-x/x-plan.md 'config: "password": "hunter2xyz"'
check block 'plan with quoted secret → block'
newrepo; stage plans/2026-07-05-x/x-plan.md 'password 규칙과 token 순환에 대한 설명 (프로즈, 값 없음)'
check allow 'plan prose mentioning password/token (no value) → allow'

# --- plans scanned even when settings.json not staged ---
newrepo; stage plans/2026-07-05-x/x-plan.md 'AKIAIOSFODNN7EXAMPLE'; stage README.md 'x'
check block 'plan AWS key without settings.json staged → block'

printf '\npre-commit-check.test.sh: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
