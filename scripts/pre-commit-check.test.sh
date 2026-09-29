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
# Installed hooks run the guard with Windows PowerShell 5.1, and a UTF-8 console input code page
# (the default here; "Beta: UTF-8" or chcp 65001) makes .NET Framework prefix redirected stdin
# with a BOM — so 5.1 runs as its own engine with that console encoding.
PS51="$(command -v powershell.exe 2>/dev/null || true)"
[ -n "$PS51" ] && [ "$PS51" != "$PWSH" ] && ENGINES+=(ps51)

g() { git -C "$REPO" -c user.email=t@t -c user.name=t -c commit.gpgsign=false -c tag.gpgsign=false "$@"; }

run_guard() { # <engine> <mode> <stdin>; GUARD_ENV (one NAME=value) is exported to the guard only
  local home="${FAKE_HOME:-$HOME}" extra=()
  [ -n "${GUARD_ENV-}" ] && extra=("$GUARD_ENV")
  if [ "$1" = sh ]; then
    ( cd "$REPO" && printf '%s' "$3" | env ${extra[@]+"${extra[@]}"} HOME="$home" bash "$GUARD_SH" "$2" 2>&1 )
  elif [ "$1" = ps51 ]; then
    local profile guard
    profile="$(cygpath -w "$home")"; guard="$(cygpath -w "$GUARD_PS1")"
    ( cd "$REPO" && printf '%s' "$3" | env ${extra[@]+"${extra[@]}"} HOME="$home" USERPROFILE="$profile" "$PS51" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass \
      -Command "[Console]::InputEncoding = New-Object System.Text.UTF8Encoding \$true; & '$guard' -Mode $2; exit \$LASTEXITCODE" 2>&1 )
  else
    # Windows 의 PowerShell $HOME 은 HOME 이 아니라 USERPROFILE 을 따른다.
    local profile="$home"; command -v cygpath >/dev/null && profile="$(cygpath -w "$home")"
    ( cd "$REPO" && printf '%s' "$3" | env ${extra[@]+"${extra[@]}"} HOME="$home" USERPROFILE="$profile" "$PWSH" -NoLogo -NoProfile -NonInteractive -File "$GUARD_PS1" -Mode "$2" 2>&1 )
  fi
}

has_reason() { # <output> <reason> — "-" always; "=text" needs the violation line "  - text" exactly
  case "$2" in
    -) return 0 ;;
    =*) printf '%s\n' "$1" | sed $'s/\033\\[[0-9;]*m//g' | tr -d '\r' | grep -Fxq -- "  - ${2#=}" ;;
    *) [[ "$1" == *"$2"* ]] ;;
  esac
}

check() { # <engine> <block|allow|clean> <reason: substring, =violation line, or -> <desc> <mode> [stdin]; clean = allow with no output
  local out rc
  out="$(run_guard "$1" "$5" "${6-}")"; rc=$?
  verdict "$1" "$2" "$3" "$4" "$out" "$rc"
}

verdict() { # <engine> <expect> <reason> <desc> <output> <exit code>
  local engine="$1" expect="$2" reason="$3" desc="$4" out="$5" rc="$6" ok=0
  [ "$engine" != sh ] && ps1_ran=$((ps1_ran+1))
  if [ "$expect" = allow ]; then
    [ "$rc" -eq 0 ] && [[ "$out" != *"[BLOCKED]"* ]] && has_reason "$out" "$reason" && ok=1
  elif [ "$expect" = clean ]; then
    [ "$rc" -eq 0 ] && [ -z "$out" ] && ok=1
  elif [ "$rc" -ne 0 ] && [[ "$out" == *"[BLOCKED]"* ]] && has_reason "$out" "$reason"; then
    ok=1
  fi
  # FORBID (space-separated, lowercase): words the guard output must never contain in any case.
  if [ $ok -eq 1 ] && [ -n "${FORBID-}" ]; then
    local lo w; lo="$(printf '%s' "$out" | tr '[:upper:]' '[:lower:]')"
    for w in $FORBID; do [[ "$lo" == *"$w"* ]] && { ok=0; out="output leaked a forbidden word: $w"; }; done
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

# Pushed commits reach git log on stdin, not argv: a new remote with hundreds of refs must not
# hit the Windows command-line limit (32,767 chars). The shim records every git log argv (sh engine).
newrepo; b=$(commit plans/a/a-plan.md clean); s=$(commit plans/a/a-plan.md "$TOKEN")
many="$(for i in $(seq 1 50); do line "b$i" "$s"; done)"
both block 'Anthropic key' 'fifty ref lines for one commit' pre-push "$many"
SHIM="$T/shim"; mkdir -p "$SHIM"; REAL_GIT="$(command -v git)"
cat > "$SHIM/git" <<EOF
#!/usr/bin/env bash
case " \$* " in
  *" log "*) printf '%s\n' "\$@" >> "$SHIM/log-args"
             tee -a "$SHIM/log-stdin" | "$REAL_GIT" "\$@"; exit "\${PIPESTATUS[1]}" ;;
esac
exec "$REAL_GIT" "\$@"
EOF
chmod +x "$SHIM/git"
GUARD_ENV="PATH=$SHIM:$PATH"
shim_in="$(for i in $(seq 1 50); do line "b$i" "$s"; done; line feat "$s" "$b")"
check sh block 'Anthropic key' 'scan through a git shim' pre-push "$shim_in"
unset GUARD_ENV
if [ -s "$SHIM/log-args" ] && ! grep -Eq '^\^?[0-9a-f]{40}$' "$SHIM/log-args" \
  && grep -Fqx "^$b" "$SHIM/log-stdin"; then
  pass=$((pass+1))
else
  fail=$((fail+1)); printf '✗ [sh] commits and the exclusion must reach git log on stdin, not argv\n'
fi

# The shim above only works for the sh engine (Windows ps1 starts git.exe directly), so both
# engines also get a push of 800 distinct commits: as git log arguments that is ~33,000 chars,
# over the Windows command-line limit, and the guard would fail closed on a clean push.
newrepo; b=$(commit plans/m/m-plan.md clean)
{ for i in $(seq 1 800); do
    printf 'commit refs/heads/m%d\ncommitter t <t@t> 1700000000 +0000\ndata 2\nm\nfrom %s\n' "$i" "$b"
    printf 'M 644 inline plans/m/m-plan.md\ndata %d\nclean %d\n\n' "$(( ${#i} + 7 ))" "$i"
  done; } | git -C "$REPO" fast-import --quiet
wide="$(git -C "$REPO" for-each-ref --format='%(refname) %(objectname) %(refname)' 'refs/heads/m*' | sed "s/\$/ $ZERO/")"
both allow - 'eight hundred distinct pushed commits (clean)' pre-push "$wide"
# the token is only in the last of 801 ref lines — a truncated stdin would miss it
tok=$(commit plans/m/m-plan.md "$TOKEN")
both block 'Anthropic key' 'token on the last of 801 pushed commits' pre-push "$wide
$(line feat "$tok")"

# git log --stdin falls back to HEAD on empty input, so a failed input build must block — the
# token here is only on a branch that is not checked out.
newrepo; commit README.md clean >/dev/null; g checkout -q -b other
s=$(commit plans/a/a-plan.md "$TOKEN"); g checkout -q feat
both block 'Anthropic key' 'token only on a pushed ref that is not HEAD' pre-push "$(line other "$s")"
for tool in awk sort; do printf '#!/bin/sh\ncat >/dev/null\nexit 0\n' > "$SHIM/$tool"; chmod +x "$SHIM/$tool"; done
GUARD_ENV="PATH=$SHIM:$PATH"
check sh block 'fail-closed' 'dedupe prints nothing and exits 0' pre-push "$(line other "$s")"
unset GUARD_ENV; rm -f "$SHIM/awk" "$SHIM/sort"

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

# --- private terms: $HOME/.claude/private-terms.txt, checked only in the ~/.claude repo ---
# Synthetic terms only. List: BOM, CRLF, a comment and a blank line put the terms on physical
# lines 3-6 — "*" marks a substring entry, the rest match on ASCII letter/digit boundaries.
LIST='\xEF\xBB\xBF# comment\r\n\r\nzebracorp\r\n  qqxk  \r\n얼룩말사\r\n*mooncalf\r\n'
newclaude() { # [list-content] — fresh fake HOME whose .claude is a repo on main; REPO points at it
  FAKE_HOME="$(cd "$(mktemp -d "$T/h.XXXXXX")" && pwd -P)"
  REPO="$FAKE_HOME/.claude"; mkdir -p "$REPO"; git -C "$REPO" init -q -b main
  if [ $# -gt 0 ]; then printf '%b' "$1" > "$REPO/private-terms.txt"; fi
}
FORBID='zebracorp qqxk mooncalf 얼룩말사'

# scope: another repo under the same HOME never reads the list
newclaude "$LIST"; REPO="$FAKE_HOME/other"; mkdir -p "$REPO"; git -C "$REPO" init -q -b main
stage notes/a.md 'ZebraCorp here'
both clean - 'other repo is out of scope' pre-commit
# scope: no $HOME/.claude/.git at all (CI, other machines)
FAKE_HOME="$(cd "$(mktemp -d "$T/h.XXXXXX")" && pwd -P)"; newrepo; stage notes/a.md 'zebracorp'
both clean - 'no ~/.claude repo' pre-commit
# scope: main checkout and a linked worktree of ~/.claude
newclaude "$LIST"; stage notes/a.md 'see ZebraCorp docs'
both block '=private term (list line 3) in staged notes/a.md' 'main checkout, mixed case' pre-commit
commit README.md x >/dev/null; git -C "$FAKE_HOME/.claude" worktree add -q -b wt "$FAKE_HOME/.claude/.claude/worktrees/wt"
REPO="$FAKE_HOME/.claude/.claude/worktrees/wt"; stage notes/b.md 'qqxk_repo'
both block '=private term (list line 4) in staged notes/b.md' 'linked worktree' pre-commit
# scope: ~/.claude whose .git is a gitfile (clone --separate-git-dir)
FAKE_HOME="$(cd "$(mktemp -d "$T/h.XXXXXX")" && pwd -P)"; REPO="$FAKE_HOME/.claude"
git init -q -b main --separate-git-dir "$FAKE_HOME/dotclaude.git" "$REPO"; printf '%b' "$LIST" > "$REPO/private-terms.txt"
stage notes/a.md 'zebracorp'
both block '=private term (list line 3) in staged notes/a.md' '.git is a gitfile' pre-commit

# scope through real hooks: git exports GIT_DIR and GIT_INDEX_FILE to hooks in a linked worktree,
# which the direct calls above never see. ps51 is left out — its hook shim is Windows-only.
HOOK_ENGINES=(sh); [ -n "$PWSH" ] && HOOK_ENGINES+=(ps1)
for e in "${HOOK_ENGINES[@]}"; do
  mkdir -p "$T/hooks-$e"
  for m in pre-commit pre-push; do
    if [ "$e" = sh ]; then
      printf '#!/bin/sh\nexec bash "%s" %s\n' "$GUARD_SH" "$m"
    else
      guard="$GUARD_PS1"; command -v cygpath >/dev/null && guard="$(cygpath -w "$GUARD_PS1")"
      printf '#!/bin/sh\nexec "%s" -NoLogo -NoProfile -NonInteractive -File "%s" -Mode %s\n' "$PWSH" "$guard" "$m"
    fi > "$T/hooks-$e/$m"
    chmod +x "$T/hooks-$e/$m"
  done
done
hook_git() { # <engine> <git args...> — git in $REPO, with hooks that run the guard through <engine>
  local e="$1" profile="$FAKE_HOME"; shift
  command -v cygpath >/dev/null && profile="$(cygpath -w "$FAKE_HOME")"
  ( cd "$REPO" && env HOME="$FAKE_HOME" USERPROFILE="$profile" git -c core.hooksPath="$T/hooks-$e" \
      -c user.email=t@t -c user.name=t -c commit.gpgsign=false "$@" 2>&1 )
}
for e in "${HOOK_ENGINES[@]}"; do
  newclaude "$LIST"; commit README.md x >/dev/null
  OTHER="$FAKE_HOME/other"; mkdir -p "$OTHER"; git -C "$OTHER" init -q -b main
  REPO="$OTHER"; commit README.md x >/dev/null
  git -C "$OTHER" worktree add -q -b wt "$OTHER/wt"; REPO="$OTHER/wt"; stage notes/a.md 'zebracorp here'
  out="$(hook_git "$e" commit -q -m 'zebracorp note')"; verdict "$e" clean - 'other repo linked worktree commit (real hook)' "$out" $?
  git init -q --bare "$FAKE_HOME/other.git"
  out="$(hook_git "$e" push -q "$FAKE_HOME/other.git" HEAD:refs/heads/zebracorp)"; verdict "$e" clean - 'other repo linked worktree push (real hook)' "$out" $?
  REPO="$FAKE_HOME/.claude"; git -C "$REPO" worktree add -q -b wt "$REPO/.claude/worktrees/wt"
  REPO="$REPO/.claude/worktrees/wt"; stage notes/c.md 'see zebracorp'
  out="$(hook_git "$e" commit -q -m c)"; verdict "$e" block '=private term (list line 3) in staged notes/c.md' 'commit in a linked worktree of ~/.claude (real hook)' "$out" $?
  # commit -a hands the hook GIT_INDEX_FILE=<index.lock>: the guard must read that index again
  # after asking about ~/.claude with git's variables cleared.
  commit notes/d.md plain >/dev/null; printf 'plain\nqqxk\n' > "$REPO/notes/d.md"
  out="$(hook_git "$e" commit -q -a -m d)"; verdict "$e" block '=private term (list line 4) in staged notes/d.md' 'commit -a in a linked worktree of ~/.claude (real hook)' "$out" $?
done

# scope: when git cannot answer, block inside ~/.claude and pass elsewhere. The PATH shim only
# works where the guard can pick a git without an .exe (sh anywhere, ps1 off Windows).
SHIM_ENGINES=(sh); [ -n "$PWSH" ] && ! command -v cygpath >/dev/null && SHIM_ENGINES+=(ps1)
FAILSHIM="$T/failshim"; mkdir -p "$FAILSHIM"
printf '#!/usr/bin/env bash\ncase " $* " in *" --git-common-dir "*) exit 128 ;; esac\nexec "%s" "$@"\n' "$REAL_GIT" > "$FAILSHIM/git"; chmod +x "$FAILSHIM/git"
GUARD_ENV="PATH=$FAILSHIM:$PATH"
newclaude "$LIST"; stage notes/a.md clean
for e in "${SHIM_ENGINES[@]}"; do
  check "$e" block '=private-terms scope check failed: git could not name the git dir of this ~/.claude checkout (fail-closed)' 'rev-parse fails inside ~/.claude' pre-commit
done
REPO="$FAKE_HOME/other"; mkdir -p "$REPO"; git -C "$REPO" init -q -b main; stage notes/a.md clean
for e in "${SHIM_ENGINES[@]}"; do check "$e" clean - 'rev-parse fails outside ~/.claude' pre-commit; done
# git before 2.31 echoes an unknown --path-format on stdout and exits 0
OLDSHIM="$T/oldshim"; mkdir -p "$OLDSHIM"
cat > "$OLDSHIM/git" <<EOF
#!/usr/bin/env bash
args=(); for a in "\$@"; do [ "\$a" = --path-format=absolute ] && echo "\$a" || args+=("\$a"); done
exec "$REAL_GIT" "\${args[@]}"
EOF
chmod +x "$OLDSHIM/git"
GUARD_ENV="PATH=$OLDSHIM:$PATH"
newclaude "$LIST"; stage notes/a.md 'zebracorp'
for e in "${SHIM_ENGINES[@]}"; do
  check "$e" block '=private-terms scope check failed: git could not name the git dir of this ~/.claude checkout (fail-closed)' 'git without --path-format inside ~/.claude' pre-commit
done
unset GUARD_ENV

# list states
newclaude; stage notes/a.md 'zebracorp'
both allow 'private-terms list not found' 'no list: pass with a note' pre-commit
newclaude ''; stage notes/a.md 'zebracorp'
both clean - 'empty list' pre-commit
newclaude '# only a comment\n\n'; stage notes/a.md 'zebracorp'
both clean - 'comment-only list' pre-commit
newclaude '\xEF\xBB\xBFzebracorp\n'; stage notes/a.md 'zebracorp'
both block '=private term (list line 1) in staged notes/a.md' 'BOM right before the first entry' pre-commit
newclaude; mkdir "$REPO/private-terms.txt"; stage notes/a.md clean
both block 'private-terms list unreadable' 'list is a directory' pre-commit
newclaude; ln -s "$T/nowhere" "$REPO/private-terms.txt" 2>/dev/null; stage notes/a.md clean
[ -L "$REPO/private-terms.txt" ] && both block 'private-terms list unreadable' 'list is a dangling link' pre-commit
newclaude 'ok-term\nab\n*xy\n'; stage notes/a.md clean
both block '=private-terms.txt line 2: invalid entry (under 3 bytes or has a control character)' 'two-byte entry' pre-commit
FORBID="$FORBID generic"
both block 'needs fixing by hand (do not open or rewrite the list with tools)' 'a list error points at the list, not at rephrasing' pre-commit
FORBID="${FORBID% generic}"
both block '=private-terms.txt line 3: invalid entry (under 3 bytes or has a control character)' 'substring entry of two bytes after the star' pre-commit
newclaude 'tab\there\n'; stage notes/a.md clean
both block '=private-terms.txt line 1: invalid entry (under 3 bytes or has a control character)' 'entry with a tab' pre-commit
newclaude; stage docs/private-terms.txt 'anything'
both block '=a file named private-terms.txt is in the staged changes - the list must stay untracked' 'staging a file named like the list, no list present' pre-commit
FORBID="$FORBID reported"
both block 'git rm --cached' 'a staged list file gets the unstage hint, not the list-error hint' pre-commit
FORBID="${FORBID% reported}"
newclaude "$LIST"; g add -f private-terms.txt
both block '=a file named private-terms.txt is in the staged changes - the list must stay untracked' 'staging the list itself' pre-commit
newclaude; b=$(commit README.md x); s=$(commit backup/private-terms.txt 'anything')
both block '=a file named private-terms.txt is in the pushed commits - the list must stay untracked' 'pushing a file named like the list' pre-push "$(line feat "$s" "$b")"

# matching
newclaude "$LIST"; stage notes/a.md 'abc zebracorpx qqxkz 1qqxk 0db7fde'
both clean - 'terms inside longer words and hashes' pre-commit
newclaude "$LIST"; stage notes/a.md 'ticket QQXK-1234 filed'
both block '=private term (list line 4) in staged notes/a.md' 'term before a dash' pre-commit
newclaude "$LIST"; stage notes/a.md 'xmooncalfy'
both block '=private term (list line 6) in staged notes/a.md' 'substring entry' pre-commit
newclaude "$LIST"; stage notes/a.md "$(printf 'bad \377 byte 얼룩말사의 문서')"
both block '=private term (list line 5) in staged notes/a.md' 'invalid byte and a Korean term' pre-commit
newclaude "$LIST"; stage notes/a.md "$(printf 'unit \342\204\252zebracorp')"
both block '=private term (list line 3) in staged notes/a.md' 'non-ASCII letter (Kelvin sign) before a term is a boundary' pre-commit
newclaude 'a.b+c\n[q]x|y\n'; stage notes/a.md 'xa.b+cx axbbc z[q]x|yz y.'
both clean - 'regex characters in entries match literally' pre-commit
newclaude 'a.b+c\n[q]x|y\n'; stage notes/a.md 'see [q]x|y now'
both block '=private term (list line 2) in staged notes/a.md' 'entry with regex characters' pre-commit
# each entry also sits inside a longer word, so only its regex reading could match the decoys
# shellcheck disable=SC2016 # "$" is part of an entry, not an expansion
re_list='x{2}y\np(q)*r?\nb\\d\nc^e$f\n'
# shellcheck disable=SC2016
re_decoys='zx{2}yz xxy zp(q)*r?z p zb\dz bd zc^e$fz'
# shellcheck disable=SC2016
re_hit='see c^e$f now'
newclaude "$re_list"; stage notes/a.md "$re_decoys"
both clean - 'interval, group, star, question mark and backslash match literally' pre-commit
newclaude "$re_list"; stage notes/a.md "$re_hit"
both block '=private term (list line 4) in staged notes/a.md' 'anchors inside an entry match literally' pre-commit
newclaude "$LIST"; stage notes/zebracorpx-notes.md 'about qqxk'
both block '=private term (list line 4) in staged path (hidden)' 'path holding an entry inside a longer word is hidden' pre-commit

# pre-commit: added content and new paths only
newclaude "$LIST"; commit notes/a.md "$(printf 'zebracorp\nold\n')" >/dev/null; stage notes/a.md "$(printf 'zebracorp\nnew\n')"
both clean - 'editing another line of a file that already has a term' pre-commit
newclaude "$LIST"; stage plans/zebracorp-x/p.md clean
both block '=private term (list line 3) in staged path (hidden)' 'new path with a term' pre-commit
newclaude "$LIST"; stage 'notes/q q.md' 'qqxk'
both block '=private term (list line 4) in staged notes/q q.md' 'content hit in a path with a space' pre-commit
newclaude "$LIST"; commit docs/a.md hello >/dev/null; g mv docs/a.md docs/b.md
both clean - 'rename to a clean path' pre-commit
newclaude "$LIST"; commit docs/a.md hello >/dev/null; g mv docs/a.md docs/zebracorp.md
both block '=private term (list line 3) in staged path (hidden)' 'rename to a path with a term' pre-commit
newclaude "$LIST"; commit docs/a.md "$(printf 'one\ntwo\nthree\nfour\n')" >/dev/null; g mv docs/a.md docs/b.md
printf 'one\ntwo\nthree\nfour\nqqxk\n' > "$REPO/docs/b.md"; g add docs/b.md
both block '=private term (list line 4) in staged docs/b.md' 'rename plus an added term line' pre-commit

# pre-push: the private range excludes what origin/main already has
newclaude "$LIST"; b=$(commit README.md x); s=$(commit notes/a.md 'zebracorp')
both block '=private term (list line 3) in pushed notes/a.md' 'pushed commit adds a term' pre-push "$(line feat "$s" "$b")"
newclaude "$LIST"; b=$(commit README.md x); stage notes/a.md clean; g commit -q -m 'fix the Zebracorp thing'; s=$(git -C "$REPO" rev-parse HEAD)
both block "=private term (list line 3) in commit $(git -C "$REPO" rev-parse --short HEAD) message" 'commit message' pre-push "$(line feat "$s" "$b")"
newclaude "$LIST"; b=$(commit README.md x); stage notes/a.md clean
git -C "$REPO" -c user.email=dev@zebracorp.example -c user.name=t -c commit.gpgsign=false commit -q -m ok; s=$(git -C "$REPO" rev-parse HEAD)
both block "=private term (list line 3) in commit $(git -C "$REPO" rev-parse --short HEAD) identity" 'author email' pre-push "$(line feat "$s" "$b")"
newclaude "$LIST"; b=$(commit README.md x); s=$(commit notes/a.md clean)
both block '=private term (list line 3) in push ref (hidden)' 'ref name' pre-push "$(line zebracorp-fix "$s" "$b")"
both clean - 'deleting a ref with a term' pre-push "(delete) $ZERO refs/heads/zebracorp-fix $s"
g update-ref refs/remotes/origin/main "$s"
both block '=private term (list line 4) in push ref (hidden)' 'published commit under a new name' pre-push "$(line qqxk-2 "$s")"
newclaude "$LIST"; old=$(commit notes/a.md 'zebracorp'); g update-ref refs/remotes/origin/main "$old"; s=$(commit notes/b.md clean)
both clean - 'new branch over history origin/main already has' pre-push "$(line feat "$s")"
newclaude "$LIST"; old=$(commit notes/a.md 'zebracorp'); g update-ref refs/remotes/mirror/main "$old"; s=$(commit notes/b.md clean)
both block '=private term (list line 3) in pushed notes/a.md' 'history only another remote has' pre-push "$(line feat "$s")"
newclaude "$LIST"; old=$(commit notes/a.md 'zebracorp'); s=$(commit notes/b.md clean)
both clean - 'term only in what the destination already has' pre-push "$(line feat "$s" "$old")"
newclaude "$LIST"; b=$(commit README.md x); g checkout -q -b side; commit notes/a.md 'qqxk' >/dev/null
g checkout -q main; commit notes/b.md y >/dev/null; g merge -q --no-ff side -m merged; s=$(git -C "$REPO" rev-parse HEAD)
both block '=private term (list line 4) in pushed notes/a.md' 'term brought in by a merge' pre-push "$(line feat "$s" "$b")"
unset FAKE_HOME FORBID

if [ -n "$PWSH" ]; then printf 'ps1: ran %d\n' "$ps1_ran"; else printf 'ps1: skipped (no pwsh)\n'; fi
printf '\npre-commit-check.test.sh: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
