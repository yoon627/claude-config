#!/usr/bin/env bash
# Fixture-based tests for pre-commit-check.sh and pre-commit-check.ps1.
# Builds throwaway git repos with real commits and asserts the guard blocks/allows correctly.
# A block only counts when the output carries "[BLOCKED]" and the expected reason, so a
# crash (non-zero exit without a verdict) never passes as a block.
# ps1 cases run when pwsh is found ($PWSH or PATH); otherwise they are reported as skipped.
set -u

DIR="$(cd "$(dirname "$0")" && pwd)"
GUARD_SH="$DIR/pre-commit-check.sh"
GUARD_PS1="$DIR/pre-commit-check.ps1"
PWSH="${PWSH:-$(command -v pwsh 2>/dev/null || true)}"
ZERO=0000000000000000000000000000000000000000
TOKEN='sk-ant-0123456789abcdefghij0123'

export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE FAKE_HOME GUARD_ENV

T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

pass=0; fail=0; ps1_ran=0
ENGINES=(sh); [ -n "$PWSH" ] && ENGINES+=(ps1)

g() { git -C "$REPO" -c user.email=t@t -c user.name=t -c commit.gpgsign=false -c tag.gpgsign=false "$@"; }

run_guard() { # <engine> <mode> <stdin>; GUARD_ENV (one NAME=value) is exported to the guard only
  local home="${FAKE_HOME:-$HOME}" extra=()
  [ -n "${GUARD_ENV-}" ] && extra=("$GUARD_ENV")
  if [ "$1" = sh ]; then
    ( cd "$REPO" && printf '%s' "$3" | env ${extra[@]+"${extra[@]}"} HOME="$home" bash "$GUARD_SH" "$2" 2>&1 )
  else
    ( cd "$REPO" && printf '%s' "$3" | env ${extra[@]+"${extra[@]}"} HOME="$home" "$PWSH" -NoLogo -NoProfile -NonInteractive -File "$GUARD_PS1" -Mode "$2" 2>&1 )
  fi
}

check() { # <engine> <block|allow|clean> <reason substring or -> <desc> <mode> [stdin]; clean = allow with no output
  local engine="$1" expect="$2" reason="$3" desc="$4" mode="$5" input="${6-}" out rc ok=0
  out="$(run_guard "$engine" "$mode" "$input")"; rc=$?
  [ "$engine" = ps1 ] && ps1_ran=$((ps1_ran+1))
  if [ "$expect" = allow ]; then
    [ $rc -eq 0 ] && ok=1
  elif [ "$expect" = clean ]; then
    [ $rc -eq 0 ] && [ -z "$out" ] && ok=1
  elif [ $rc -ne 0 ] && [[ "$out" == *"[BLOCKED]"* ]] && { [ "$reason" = - ] || [[ "$out" == *"$reason"* ]]; }; then
    ok=1
  fi
  if [ $ok -eq 1 ]; then
    pass=$((pass+1))
  else
    fail=$((fail+1))
    printf '✗ [%s] %s (expected %s %s, exit=%d)\n%s\n' "$engine" "$desc" "$expect" "$reason" "$rc" "$(printf '%s\n' "$out" | head -6 | sed 's/^/    /')"
  fi
}
both() { local e; for e in "${ENGINES[@]}"; do check "$e" "$@"; done; }

newrepo() { REPO="$(mktemp -d "$T/r.XXXXXX")"; git -C "$REPO" init -q -b feat "$@"; }
stage() { mkdir -p "$REPO/$(dirname "$1")"; printf '%s' "$2" > "$REPO/$1"; g add -f "$1"; }
commit() { stage "$1" "$2"; g commit -q -m "c $1"; git -C "$REPO" rev-parse HEAD; }
line() { printf '%s %s %s %s\n' "refs/heads/$1" "$2" "refs/heads/$1" "${3:-$ZERO}"; }

# --- pre-commit: settings.json ---
newrepo; stage settings.json '{"model":"opus"}'
both allow - 'clean settings.json' pre-commit
newrepo; stage settings.json '{"mcpServers":{}}'
both block 'forbidden key' 'settings.json forbidden key' pre-commit
newrepo; stage settings.json "{\"k\":\"$TOKEN\"}"
both block 'Anthropic key' 'settings.json anthropic token' pre-commit

# --- pre-commit: plans/*.md ---
newrepo; stage plans/2026-07-05-x/x-plan.md '# Goal
정상 plan 내용, 시크릿 없음.'
both allow - 'clean plan' pre-commit
newrepo; stage plans/2026-07-05-x/x-plan.md "debug 로그: $TOKEN 붙여넣음"
both block 'Anthropic key' 'plan with anthropic key' pre-commit
both block 'git commit --no-verify' 'pre-commit bypass hint names git commit' pre-commit
newrepo; stage plans/2026-07-05-x/x-plan.md 'DB: postgres://admin:s3cretpw@db.host:5432/app'
both block 'DB URL with credentials' 'plan with DB URL creds' pre-commit
newrepo; stage plans/2026-07-05-x/x-plan.md 'curl -H "Authorization: Bearer abcdefghij0123456789xyz"'
both block 'Bearer token' 'plan with bearer token' pre-commit
newrepo; stage plans/2026-07-05-x/x-plan.md 'config: "password": "hunter2xyz"'
both block 'Quoted secret assignment' 'plan with quoted secret' pre-commit
newrepo; stage plans/2026-07-05-x/x-plan.md 'password 규칙과 token 순환에 대한 설명 (프로즈, 값 없음)'
both allow - 'plan prose mentioning password/token (no value)' pre-commit
newrepo; stage plans/2026-07-05-x/x-plan.md 'AKIAIOSFODNN7EXAMPLE'; stage README.md 'x'
both block 'AWS key' 'plan AWS key without settings.json staged' pre-commit
# an invalid UTF-8 byte on the line must not make the scanner skip it
newrepo; mkdir -p "$REPO/plans/x"; printf 'leak \377 %s\n' "$TOKEN" > "$REPO/plans/x/x-plan.md"; g add -f plans/x/x-plan.md
both block 'Anthropic key' 'plan token next to an invalid UTF-8 byte' pre-commit
# a replace ref must not substitute what the scan reads for what gets committed
newrepo; stage plans/x/x-plan.md "leak $TOKEN"
g replace "$(git -C "$REPO" rev-parse :plans/x/x-plan.md)" "$(printf 'clean' | git -C "$REPO" hash-object -w --stdin)"
both block 'Anthropic key' 'git replace on the staged blob' pre-commit

# --- pre-push: lines added in the pushed range ---
newrepo; s=$(commit plans/a/a-plan.md 'clean plan')
both allow - 'push clean plan' pre-push "$(line feat "$s")"
newrepo; s=$(commit plans/a/a-plan.md "leak $TOKEN")
both block 'Anthropic key' 'push plan token' pre-push "$(line feat "$s")"
both block 'git push --no-verify' 'pre-push bypass hint names git push' pre-push "$(line feat "$s")"
newrepo; commit plans/a/a-plan.md "leak $TOKEN" >/dev/null; s=$(commit plans/a/a-plan.md 'cleaned')
both block 'Anthropic key' 'token added then removed inside the range' pre-push "$(line feat "$s")"
newrepo; s=$(commit settings.json '{"mcpServers":{}}')
both block 'forbidden key' 'push settings.json forbidden key' pre-push "$(line feat "$s")"

# merge topology: side branch adds then deletes the file, merged with --no-ff (history simplification)
newrepo; commit README.md base >/dev/null
g checkout -q -b side; commit plans/s/s-plan.md "leak $TOKEN" >/dev/null; g rm -q plans/s/s-plan.md; g commit -q -m del
g checkout -q feat; commit other.txt x >/dev/null; g merge -q --no-ff side -m merge
s=$(git -C "$REPO" rev-parse HEAD)
both block 'Anthropic key' 'side branch add+delete merged --no-ff' pre-push "$(line feat "$s")"

# evil merge: the token exists only in the merge resolution
newrepo; commit plans/x/x-plan.md 'a' >/dev/null
g checkout -q -b side; commit side.txt s >/dev/null
g checkout -q feat; commit feat.txt f >/dev/null
g merge -q --no-ff --no-commit side >/dev/null; printf 'evil %s\n' "$TOKEN" >> "$REPO/plans/x/x-plan.md"; g add plans/x/x-plan.md; g commit -q -m merge
s=$(git -C "$REPO" rev-parse HEAD)
both block 'Anthropic key' 'token only in merge resolution' pre-push "$(line feat "$s")"
g config log.diffMerges off
both block 'Anthropic key' 'evil merge with log.diffMerges=off' pre-push "$(line feat "$s")"

# user diff/log config, attributes and env must not hide added lines
newrepo; g config color.ui always; g config diff.noprefix true; g config diff.mnemonicPrefix true
s=$(commit plans/a/a-plan.md "leak $TOKEN")
both block 'Anthropic key' 'color.ui=always / noprefix / mnemonicPrefix' pre-push "$(line feat "$s")"
g config log.showRoot false
both block 'Anthropic key' 'token in a root commit with log.showRoot=false' pre-push "$(line feat "$s")"
g config core.bigFileThreshold 1
both block 'Anthropic key' 'core.bigFileThreshold=1' pre-push "$(line feat "$s")"
GUARD_ENV=GIT_LITERAL_PATHSPECS=1
both block 'Anthropic key' 'GIT_LITERAL_PATHSPECS=1 in the environment' pre-push "$(line feat "$s")"
GUARD_ENV=GIT_GLOB_PATHSPECS=1
both block 'Anthropic key' 'GIT_GLOB_PATHSPECS=1 in the environment' pre-push "$(line feat "$s")"
unset GUARD_ENV

newrepo; mkdir -p "$REPO/plans/a"; printf 'leak %s\000tail\n' "$TOKEN" > "$REPO/plans/a/a-plan.md"; g add -f plans/a/a-plan.md; g commit -q -m nul
s=$(git -C "$REPO" rev-parse HEAD)
both block 'Anthropic key' 'plan with a NUL byte (binary)' pre-push "$(line feat "$s")"

newrepo; commit .gitattributes 'plans/** -diff' >/dev/null; s=$(commit plans/a/a-plan.md "leak $TOKEN")
both block 'Anthropic key' 'plans marked -diff in .gitattributes' pre-push "$(line feat "$s")"

newrepo; mkdir -p "$REPO/plans/a"; printf 'leak \377 %s\n' "$TOKEN" > "$REPO/plans/a/a-plan.md"; g add -f plans/a/a-plan.md; g commit -q -m bytes
s=$(git -C "$REPO" rev-parse HEAD)
both block 'Anthropic key' 'pushed token next to an invalid UTF-8 byte' pre-push "$(line feat "$s")"

# a replace ref must not substitute what the scan reads for what push sends
newrepo; commit README.md base >/dev/null
g checkout -q -b decoy; clean=$(commit plans/a/a-plan.md 'clean')
g checkout -q feat; s=$(commit plans/a/a-plan.md "leak $TOKEN"); g replace "$s" "$clean"
both block 'Anthropic key' 'git replace hides the pushed commit' pre-push "$(line feat "$s")"

# "already published" = what the destination refs have now (the remote sha on stdin), not tracking refs
newrepo; s1=$(commit plans/a/a-plan.md "leak $TOKEN"); g update-ref refs/remotes/origin/other "$s1"
s=$(commit other.txt ok)
both block 'Anthropic key' 'token only on another branch'"'"'s tracking ref, new branch push' pre-push "$(line feat "$s")"
g update-ref -d refs/remotes/origin/other
both allow - 'token only in the commit the destination already has' pre-push "$(line feat "$s" "$s1")"

# after a history rewrite the fetched tracking ref still holds the token; the remote no longer does
newrepo; commit README.md base >/dev/null; t=$(commit plans/a/a-plan.md "leak $TOKEN")
g update-ref refs/remotes/origin/feat "$t"
g checkout -q -b rewritten HEAD~1; c=$(commit plans/a/a-plan.md 'scrubbed'); g checkout -q feat
s=$(commit other.txt ok)
both block 'Anthropic key' 'stale tracking ref after a history rewrite' pre-push "$(line feat "$s" "$c")"

# a remote sha this repo lacks excludes nothing
UNKNOWN=1234567890abcdef1234567890abcdef12345678
newrepo; s=$(commit plans/a/a-plan.md "leak $TOKEN")
both block 'Anthropic key' 'remote sha not in this repo, token in range' pre-push "$(line feat "$s" "$UNKNOWN")"
newrepo; s=$(commit plans/a/a-plan.md 'clean')
both clean - 'remote sha not in this repo, clean range' pre-push "$(line feat "$s" "$UNKNOWN")"
both block 'malformed' 'remote sha not hex' pre-push "$(line feat "$s" zzzz567890abcdef1234567890abcdef12345678)"
both block 'malformed' 'short remote sha' pre-push "$(line feat "$s" beef)"
both block 'malformed' 'short local sha' pre-push "refs/heads/feat beef refs/heads/feat $ZERO"
both block 'malformed' 'sha256-length remote sha in a sha1 repo' pre-push "$(line feat "$s" "$s${s:0:24}")"
both block 'malformed' 'deletion line with a malformed remote sha' pre-push "(delete) $ZERO refs/heads/gone not-a-sha"
b=$(printf 'x' | git -C "$REPO" hash-object -w --stdin); tree=$(git -C "$REPO" rev-parse 'HEAD^{tree}')
both clean - 'remote sha is a blob' pre-push "refs/tags/b $s refs/tags/b $b"
both clean - 'remote sha is a tree' pre-push "refs/tags/tr $s refs/tags/tr $tree"

# an annotated tag as the remote sha is peeled to its commit
newrepo; s1=$(commit plans/a/a-plan.md "leak $TOKEN"); g tag -a v1 -m v1 "$s1"; old=$(git -C "$REPO" rev-parse v1)
s=$(commit other.txt ok); g tag -f -a v1 -m v1b "$s" >/dev/null; new=$(git -C "$REPO" rev-parse v1)
both allow - 'retargeted annotated tag' pre-push "refs/tags/v1 $new refs/tags/v1 $old"

# every line's remote sha is on the same remote, deletions included
newrepo; t=$(commit plans/a/a-plan.md "leak $TOKEN"); s=$(commit other.txt ok)
both allow - 'deleted ref'"'"'s remote value counts, deletion first' pre-push "(delete) $ZERO refs/heads/old $t
$(line feat "$s")"
both allow - 'deleted ref'"'"'s remote value counts, deletion last' pre-push "$(line feat "$s")
(delete) $ZERO refs/heads/old $t"
newrepo; m=$(commit plans/a/a-plan.md "leak $TOKEN"); m2=$(commit README.md next)
g checkout -q -b side "$m"; s=$(commit other.txt ok)
both allow - 'one line'"'"'s remote sha is excluded for the others' pre-push "refs/heads/feat $m2 refs/heads/feat $m
$(line side "$s")"

# sha256 repos pass 64-character object names
ZERO64=$ZERO$ZERO; ZERO64=${ZERO64:0:64}
newrepo --object-format=sha256; s1=$(commit plans/a/a-plan.md "leak $TOKEN"); s=$(commit other.txt ok)
both block 'Anthropic key' 'sha256 repo, new branch' pre-push "$(line feat "$s" "$ZERO64")"
both allow - 'sha256 repo, token only in what the destination has' pre-push "$(line feat "$s" "$s1")"

# a replace ref must not turn the remote's tag into a commit it does not have
newrepo; c0=$(commit README.md base); g tag -a va -m a "$c0"; A=$(git -C "$REPO" rev-parse va)
t=$(commit plans/a/a-plan.md "leak $TOKEN"); g tag -a vb -m b "$t"; B=$(git -C "$REPO" rev-parse vb)
s=$(commit other.txt ok); g replace -f "$A" "$B"
both block 'Anthropic key' 'replace ref on the remote'"'"'s tag' pre-push "refs/tags/va $A refs/tags/va $A
$(line feat "$s")"

# ref deletion, tags, malformed input, unresolvable and corrupt objects
newrepo; s=$(commit plans/a/a-plan.md 'clean')
both allow - 'branch deletion push' pre-push "(delete) $ZERO refs/heads/gone $s"
g tag -a v1 -m v1; t=$(git -C "$REPO" rev-parse v1)
both allow - 'clean annotated tag push' pre-push "refs/tags/v1 $t refs/tags/v1 $ZERO"
b=$(printf 'x' | git -C "$REPO" hash-object -w --stdin)
both block 'not a resolvable commit' 'tag pointing at a blob' pre-push "refs/tags/b $b refs/tags/b $ZERO"
both block 'malformed' 'ref line with two fields' pre-push "refs/heads/feat $s"
both block 'not a resolvable commit' 'unknown local sha' pre-push "$(line feat 1234567890abcdef1234567890abcdef12345678)"
blob=$(git -C "$REPO" rev-parse HEAD:plans/a/a-plan.md); rm -f "$REPO/.git/objects/${blob:0:2}/${blob:2}"
both block 'git log failed' 'missing blob in the pushed range' pre-push "$(line feat "$s")"

newrepo; s1=$(commit plans/a/a-plan.md 'clean'); g checkout -q -b other; s2=$(commit plans/b/b-plan.md "leak $TOKEN")
both block 'Anthropic key' 'two refs, one bad' pre-push "$(line feat "$s1")
$(line other "$s2")"

# patch parsing: a body line starting with "++" shows up as "+++ ..." in the patch
newrepo; s=$(commit plans/a/a-plan.md "++ $TOKEN")
both block 'Anthropic key' 'added line starting with ++' pre-push "$(line feat "$s")"

# rename of a published plan into settings.json must still be key-checked
newrepo; s1=$(commit plans/a/a-plan.md '{"mcpServers":{}}')
g mv plans/a/a-plan.md settings.json; g commit -q -m rename; s=$(git -C "$REPO" rev-parse HEAD)
both block 'forbidden key' 'plans -> settings.json rename' pre-push "$(line feat "$s" "$s1")"
g config log.follow true
both block 'forbidden key' 'rename with log.follow=true' pre-push "$(line feat "$s" "$s1")"

# --- pre-push: protected-branch block, scoped to non-~/.claude repos ---
# The guard resolves "$HOME/.claude" as the exempt repo, so tests point HOME at a fixture dir.
FAKE_HOME="$(cd "$(mktemp -d "$T/h.XXXXXX")" && pwd -P)"
REPO="$FAKE_HOME/.claude"; mkdir -p "$REPO"; git -C "$REPO" init -q -b main; s=$(commit README.md x)
both allow - 'HOME/.claude repo main push' pre-push "$(line main "$s")"
both allow - 'HOME/.claude repo master push' pre-push "$(line master "$s")"
REPO="$FAKE_HOME/other-project"; mkdir -p "$REPO"; git -C "$REPO" init -q -b main; s=$(commit README.md x)
both block 'Direct push to refs/heads/main' 'other repo main push' pre-push "$(line main "$s")"
both block 'Direct push to refs/heads/master' 'other repo master push' pre-push "$(line master "$s")"
both allow - 'other repo feature branch push' pre-push "$(line feat "$s")"
unset FAKE_HOME

if [ -n "$PWSH" ]; then printf 'ps1: ran %d\n' "$ps1_ran"; else printf 'ps1: skipped (no pwsh)\n'; fi
printf '\npre-commit-check.test.sh: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
