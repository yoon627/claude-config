#!/usr/bin/env bash
# pre-commit-check.sh — guard settings.json (forbidden keys) and settings.json + plans/*.md (secret/token patterns)
# Usage: pre-commit-check.sh [pre-commit|pre-push]
# pre-commit scans the staged versions; pre-push scans the lines added by the commits being pushed
# that the destination refs do not already have, so commits that skipped pre-commit are still checked.
# plans/ is tracked under approach A (plans-sync), so plan files are scanned for pasted secrets.

set -e

# Match bytes, not characters: in a UTF-8 locale awk aborts and grep skips lines that carry an
# invalid byte, which would hide a token on the same line.
export LC_ALL=C
# A replace ref would let every git call below read a substitute object — a tag peeled to a
# commit the remote does not have, or a staged blob other than the one being committed.
export GIT_NO_REPLACE_OBJECTS=1
# Pathspec magic from the environment would change what 'plans/*.md' matches in the push scan.
unset GIT_LITERAL_PATHSPECS GIT_GLOB_PATHSPECS GIT_NOGLOB_PATHSPECS GIT_ICASE_PATHSPECS

MODE="${1:-pre-commit}"

# pre-push receives "<local ref> <local sha> <remote ref> <remote sha>" lines on stdin;
# read them once because both the protected-branch block and the scan need them.
# Direct pushes to protected branches are blocked first. ~/.claude is exempt
# (user-authorized 2026-08-05, CLAUDE.md §8): this guard is shared by every repo that
# ran install-hooks.sh, so the exemption is scoped by repo root rather than removed.
# Both paths are resolved because macOS $TMPDIR and $HOME can be symlinks while
# `--show-toplevel` returns the physical path.
push_lines=()
if [ "$MODE" = "pre-push" ]; then
  while IFS= read -r _line || [ -n "$_line" ]; do
    push_lines+=("$_line")
  done
  resolve() { [ -d "$1" ] && (cd "$1" && pwd -P) || printf '%s' "$1"; }
  _repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [ -z "$_repo_root" ] || [ "$(resolve "$_repo_root")" != "$(resolve "$HOME/.claude")" ]; then
    for _line in "${push_lines[@]+"${push_lines[@]}"}"; do
      read -r _lref _lsha rref _rsha <<<"$_line" || true
      case "$rref" in
        refs/heads/main|refs/heads/master)
          printf '\n\033[31m[BLOCKED] Direct push to %s is not allowed. Open a PR instead.\033[0m\n' "$rref" >&2
          printf '\033[90mBypass once (NOT recommended): git push --no-verify\033[0m\n' >&2
          exit 1
          ;;
      esac
    done
  fi
fi

# ~/.claude is a public repo, so what is committed there is also checked against
# $HOME/.claude/private-terms.txt: an untracked, per-machine list of names that must not be
# published. Other repos never open the list. Unlike the exemption above, which compares
# --show-toplevel and so only matches the main checkout, this compares common git dirs so
# linked worktrees count, and asks git for ~/.claude's so a gitfile .git counts too. That
# query runs without git's variables: a hook in a linked worktree inherits GIT_DIR for the
# current repo, which would answer for it instead. If git cannot answer, block inside
# ~/.claude and pass elsewhere — git before 2.31 echoes --path-format back instead of a
# directory, which counts as no answer.
PT_LIST="$HOME/.claude/private-terms.txt"
claude_repo=no
if [ -e "$HOME/.claude/.git" ]; then
  if common="$(git rev-parse --git-common-dir 2>/dev/null)" && [ -n "$common" ] &&
    claude_common="$(unset GIT_DIR GIT_COMMON_DIR GIT_WORK_TREE GIT_INDEX_FILE
      cd "$HOME/.claude" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" &&
    [ -d "$claude_common" ]; then
    if [ "$common" -ef "$claude_common" ]; then claude_repo=yes; fi
  else
    case "$(pwd -P)/" in "$(cd "$HOME/.claude" && pwd -P)"/*) claude_repo=unknown ;; esac
  fi
fi

violations=()
pt_hit=0
pt_term_hits=0
pt_named=0

# Token/secret patterns. Each entry: name|regex (ERE, case-sensitive).
# Structured, high-confidence secrets only — free-form PII/prose is NOT scanned (unreliable, noisy).
patterns=(
  'Anthropic key|sk-ant-[A-Za-z0-9_-]{20,}'
  'OpenAI project key|sk-proj-[A-Za-z0-9_-]{20,}'
  'OpenAI key|sk-[A-Za-z0-9]{32,}'
  'GitHub PAT (fine)|github_pat_[A-Za-z0-9_]{20,}'
  'GitHub token|gh[opsu]_[A-Za-z0-9_]{30,}'
  'GitLab PAT|glpat-[A-Za-z0-9_-]{20,}'
  'AWS key|(AKIA|ASIA)[A-Z0-9]{16}'
  'Google API key|AIza[A-Za-z0-9_-]{35}'
  'Slack token|xox[baprs]-[A-Za-z0-9-]{20,}'
  'JWT|eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}'
  'PEM private key|-----BEGIN [A-Z ]*PRIVATE KEY-----'
  'DB URL with credentials|(postgres|postgresql|mysql|mongodb|mongodb\+srv|redis|rediss|amqp|amqps)://[^:@/ ]+:[^@/ ]+@'
  'Bearer token|[Bb]earer[[:space:]]+[A-Za-z0-9._~+/=-]{20,}'
  'Quoted secret assignment|(password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|client[_-]?secret)"?[[:space:]]*[:=][[:space:]]*"[^"]{8,}"'
)

# scan_tokens <content> <label> — append token-pattern violations found in content.
scan_tokens() {
  local content="$1" label="$2" entry name rx match sample
  [ -z "$content" ] && return 0
  for entry in "${patterns[@]}"; do
    name="${entry%%|*}"
    rx="${entry#*|}"
    match="$(printf '%s' "$content" | grep -Eo -e "$rx" | head -n 1 || true)"
    if [ -n "$match" ]; then
      sample="$match"
      [ ${#sample} -gt 30 ] && sample="${sample:0:30}..."
      violations+=("${label}: token pattern (${name}): ${sample}")
    fi
  done
}

# scan_keys <content> — settings.json forbidden-key check (canonical "key": form).
scan_keys() {
  local content="$1" key
  [ -z "$content" ] && return 0
  for key in mcpServers apiKeyHelper awsCredentialExport awsAuthRefresh; do
    if printf '%s' "$content" | grep -Eq "\"${key}\"[[:space:]]*:"; then
      violations+=("settings.json: forbidden key \"${key}\"  (move to settings.local.json or ~/.claude.json)")
    fi
  done
}

# rev_input — the revisions for `git log --stdin`: pushed commits, then exclusions marked
# with `^`, deduplicated in order. They go on stdin because as arguments a new remote with
# hundreds of refs exceeds the Windows command-line limit. `git log --stdin` falls back to
# HEAD on empty input or a leading blank line, so added_lines builds this first and blocks
# when it is empty.
rev_input() {
  {
    printf '%s\n' "${push_commits[@]}"
    if [ ${#published[@]} -gt 0 ]; then printf '^%s\n' "${published[@]}"; fi
  } | awk 'NF && !seen[$0]++'
}

# added_lines <pathspec> — lines added under <pathspec> by the pushed commits that the
# destination refs do not already have. Every option guards a way the scan could go blind:
# --full-history keeps side branches that net to no change; -m with log.diffMerges=separate
# shows what a merge adds against each parent; log.showRoot=true includes root commits;
# log.follow=false keeps a rename into the pathspec from being paired with its source;
# --text reads binary / -diff / bigFileThreshold files as text; --no-replace-objects reads
# the objects push actually sends; the color/prefix/textconv flags override diff config.
# Each pathspec is scanned in its own call, so a file renamed into it from outside shows
# its lines as added.
added_lines() {
  local out revs
  revs="$(rev_input)" && [ -n "$revs" ] || return 1
  out="$(printf '%s\n' "$revs" | git --no-replace-objects -c core.quotePath=false \
    -c log.diffMerges=separate -c log.showRoot=true -c log.follow=false \
    log --stdin -p --text --no-color --no-ext-diff --no-textconv \
    --full-history -m -U0 --src-prefix=a/ --dst-prefix=b/ --format= -- "$1")" || return 1
  # Header lines run from "diff --git" to the first "@@"; a body line starting with "++"
  # appears as "+++" and must not be mistaken for a header.
  printf '%s\n' "$out" | awk '/^diff --git /{h=1; next} /^@@/{h=0; next} !h && /^\+/{print substr($0, 2)}'
}

# scan_pushed <pathspec> <label> [keys]
scan_pushed() {
  local added
  if ! added="$(added_lines "$1")"; then
    violations+=("pre-push: git log failed while scanning $1 (fail-closed)")
    return 0
  fi
  [ "${3-}" = keys ] && scan_keys "$added"
  scan_tokens "$added" "$2"
}

# pt_violation <message> — private-term violations never echo the term or the matched text.
pt_violation() { violations+=("$1"); pt_hit=$((pt_hit + 1)); }

# pt_load — parse the list into "line<TAB>=|*<TAB>lowercased term" rows in pt_terms; returns 1
# when there is nothing to match. One entry per line (BOM, CR and surrounding blanks stripped,
# blank and "#" lines skipped); a leading "*" makes it a substring entry. A list that exists but
# cannot be read, or has an entry under 3 bytes or with a control character, blocks: skipping
# it would let every term through.
pt_load() {
  local rows bad n
  pt_terms=''
  if ! [ -e "$PT_LIST" ] && ! [ -L "$PT_LIST" ]; then
    printf '\033[90mnote: private-terms list not found (%s); private-term check skipped\033[0m\n' "$PT_LIST" >&2
    return 1
  fi
  if ! [ -f "$PT_LIST" ] || ! [ -r "$PT_LIST" ] || ! rows="$(awk '
    NR == 1 && substr($0, 1, 3) == "\357\273\277" { $0 = substr($0, 4) }
    {
      gsub(/^[ \t\r]+|[ \t\r]+$/, "")
      if ($0 == "" || substr($0, 1, 1) == "#") next
      any = substr($0, 1, 1) == "*"
      t = $0
      if (any) { t = substr(t, 2); gsub(/^[ \t]+/, "", t) }
      if (length(t) < 3 || t ~ /[[:cntrl:]]/) print "E\t" NR
      else print NR "\t" (any ? "*" : "=") "\t" tolower(t)
    }' "$PT_LIST")"; then
    pt_violation "private-terms list unreadable: $PT_LIST"
    return 1
  fi
  bad="$(printf '%s\n' "$rows" | awk -F '\t' '$1 == "E" { print $2 }')"
  if [ -n "$bad" ]; then
    for n in $bad; do
      pt_violation "private-terms.txt line $n: invalid entry (under 3 bytes or has a control character)"
    done
    return 1
  fi
  pt_terms="$rows"
  [ -n "$pt_terms" ]
}

# pt_match — read "kind<TAB>where<TAB>text" records and print "line<TAB>surface" once per list
# entry and surface. An entry matches ASCII case-insensitively where the bytes on both sides
# are not ASCII letters or digits ("_", "-" and non-ASCII bytes are boundaries), so it does not
# match inside a longer word or a hash; a "*" entry matches anywhere. A path that holds an
# entry anywhere, even inside a longer word, is shown as "path (hidden)".
pt_match() {
  PT_TERMS="$pt_terms" awk '
    # quote — an entry as an ERE that matches it literally.
    function quote(t,   r, c, k) {
      for (k = 1; k <= length(t); k++) {
        c = substr(t, k, 1)
        r = r (index("\\^$.[|()*+?{", c) ? "\\" c : c)
      }
      return r
    }
    BEGIN {
      n = split(ENVIRON["PT_TERMS"], rows, "\n")
      for (i = 1; i <= n; i++) {
        split(rows[i], f, "\t"); ln[i] = f[1]; any[i] = (f[2] == "*"); term[i] = f[3]
        bounded[i] = "[^a-z0-9]" quote(term[i]) "[^a-z0-9]"
      }
    }
    # One regex search per line keeps a long line linear. The padding stands in for line start
    # and end.
    function found(s, i) {
      if (!index(s, term[i])) return 0
      return any[i] || match(" " s " ", bounded[i]) > 0
    }
    function secret(s,   i) {
      s = tolower(s)
      for (i = 1; i <= n; i++) if (index(s, term[i])) return 1
      return 0
    }
    {
      t = index($0, "\t"); kind = substr($0, 1, t - 1); rest = substr($0, t + 1)
      t = index(rest, "\t"); where = substr(rest, 1, t - 1); text = tolower(substr(rest, t + 1))
      for (i = 1; i <= n; i++) {
        if (!found(text, i)) continue
        if (kind == "S" || kind == "s") {
          if (!(where in hid)) hid[where] = secret(where)
          label = (kind == "S" ? "staged " : "pushed ") (hid[where] ? "path (hidden)" : where)
        } else if (kind == "P") label = "staged path (hidden)"
        else if (kind == "p") label = "pushed path (hidden)"
        else if (kind == "M") label = "commit " where " message"
        else if (kind == "I") label = "commit " where " identity"
        else label = "push ref (hidden)"
        if (!seen[ln[i], label]++) print ln[i] "\t" label
      }
    }'
}

# pt_patch_records <kind> — "kind<TAB>path<TAB>added line" for each added line of a patch.
# The path comes from the "+++ b/<path>" header, which git quotes for special characters and
# ends with a tab when the path has a space.
pt_patch_records() {
  awk -v k="$1" '
    /^diff --git /{h=1; next}
    h && /^\+\+\+ /{p = substr($0, 5); sub(/\t$/, "", p); sub(/^"?b\//, "", p); sub(/"$/, "", p); next}
    /^@@/{h=0; next}
    !h && /^\+/{print k "\t" p "\t" substr($0, 2)}'
}

# pt_new_paths <kind> — "kind<TAB><TAB>path" for NUL-separated paths on stdin (newlines in a
# path become "?").
pt_new_paths() { tr '\n\0' '?\n' | awk -v k="$1" 'length { print k "\t\t" $0 }'; }

# pt_record <hits> — turn pt_match output into violations.
pt_record() {
  local n label
  while IFS=$'\t' read -r n label; do
    if [ -n "$n" ]; then pt_violation "private term (list line $n) in $label"; pt_term_hits=$((pt_term_hits + 1)); fi
  done <<<"$1"
}

pt_list_named() { # <path records> <where> — the list itself must never be committed, list or not
  if printf '%s\n' "$1" | awk -F '\t' '$3 ~ /(^|\/)private-terms\.txt$/ { f = 1 } END { exit !f }'; then
    pt_violation "a file named private-terms.txt is in the $2 - the list must stay untracked"
    pt_named=1
  fi
}

# pre-commit is an early warning: merge, cherry-pick, rebase and commit-check's plumbing never
# run it. pre-push is the gate.
pt_scan_staged() {
  local paths patch hits
  set -- -c core.quotePath=false -c diff.renames=true diff --cached -M --no-ext-diff
  if ! paths="$(set -o pipefail; git "$@" --name-only -z --diff-filter=ACR | pt_new_paths P)" ||
    ! patch="$(git "$@" -U0 --text --no-color --no-textconv --src-prefix=a/ --dst-prefix=b/)"; then
    pt_violation "pre-commit: git diff failed while checking private terms (fail-closed)"
    return 0
  fi
  pt_list_named "$paths" 'staged changes'
  pt_load || return 0
  hits="$( { printf '%s\n' "$paths"; printf '%s\n' "$patch" | pt_patch_records S; } | pt_match)" ||
    { pt_violation "pre-commit: private-term match failed (fail-closed)"; return 0; }
  pt_record "$hits"
}

# private_rev_input — rev_input minus what origin/main has. The secret scan above trusts only
# the remote's own shas; this scan also skips the public default branch's history, because
# anything there is already published and force-push to it is forbidden. A missing or stale
# origin/main widens the range (a false block — 'git fetch origin' clears it).
private_rev_input() {
  local base
  rev_input
  if base="$(git rev-parse --verify --quiet 'refs/remotes/origin/main^{commit}' 2>/dev/null)"; then
    printf '^%s\n' "$base"
  fi
}

pt_log() { # <git log args> — over the private push range, revisions on stdin
  local revs
  revs="$(private_rev_input)" && [ -n "$revs" ] || return 1
  printf '%s\n' "$revs" | git --no-replace-objects -c core.quotePath=false -c diff.renames=true \
    -c log.diffMerges=separate -c log.showRoot=true -c log.follow=false -c i18n.logOutputEncoding=UTF-8 \
    log --stdin --full-history "$@"
}

# pt_scan_pushed — ref names (every non-delete line), then the new paths, added lines, messages
# and author/committer identities of the pushed commits origin/main does not have.
pt_scan_pushed() {
  local paths='' patch='' msgs='' hits
  if [ ${#push_commits[@]} -gt 0 ]; then
    if ! paths="$(set -o pipefail; pt_log -m --name-only -z -M --diff-filter=ACR --no-ext-diff --format= | pt_new_paths p)" ||
      ! patch="$(pt_log -m -p -M -U0 --text --no-color --no-ext-diff --no-textconv --src-prefix=a/ --dst-prefix=b/ --format=)" ||
      ! msgs="$(pt_log '--format=%x01%h%n%an%x20<%ae>%n%cn%x20<%ce>%n%B')"; then
      pt_violation "pre-push: git log failed while checking private terms (fail-closed)"
      return 0
    fi
    pt_list_named "$paths" 'pushed commits'
  fi
  pt_load || return 0
  hits="$( {
    [ ${#pt_refs[@]} -gt 0 ] && printf 'R\t\t%s\n' "${pt_refs[@]}"
    printf '%s\n' "$paths"
    printf '%s\n' "$patch" | pt_patch_records s
    printf '%s\n' "$msgs" | awk '
      substr($0, 1, 1) == "\001" { sha = substr($0, 2); id = 2; next }
      id > 0 { print "I\t" sha "\t" $0; id--; next }
      { print "M\t" sha "\t" $0 }'
  } | pt_match)" || { pt_violation "pre-push: private-term match failed (fail-closed)"; return 0; }
  pt_record "$hits"
}

if [ "$MODE" = "pre-commit" ]; then
  staged="$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)"
  if printf '%s\n' "$staged" | grep -qx 'settings.json'; then
    sj="$(git show :settings.json 2>/dev/null || true)"
    scan_keys "$sj"
    scan_tokens "$sj" 'settings.json'
  fi
  # plans/*.md are tracked (approach A) and free-form → scan each staged plan for pasted secrets.
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    scan_tokens "$(git show ":$f" 2>/dev/null || true)" "$f"
  done < <(printf '%s\n' "$staged" | grep -E '^plans/.*\.md$' || true)
else
  # Anything the guard cannot interpret is blocked: a real pre-push always passes four fields
  # with object names exactly as long as this repo's hash, and pushes local objects, so a
  # mismatch means the scan cannot be trusted. (Any other hex string could resolve to a ref of
  # the same name instead.)
  # "Already published" is what the destination refs hold right now: the remote sha of every
  # line, deletions included, comes from the remote itself — unlike tracking refs, which can
  # be stale, belong to another remote, or not match a pushurl. git sends at most the commits
  # none of the remote's refs have, so excluding only these keeps the scan a superset of it.
  push_commits=()
  published=()
  pt_refs=()
  case "$(git rev-parse --show-object-format 2>/dev/null)" in
    sha256) oid='^[0-9a-fA-F]{64}$' ;;
    *) oid='^[0-9a-fA-F]{40}$' ;;
  esac
  for _line in "${push_lines[@]+"${push_lines[@]}"}"; do
    [ -z "${_line//[[:space:]]/}" ] && continue
    read -r lref lsha rref rsha extra <<<"$_line" || true
    if [ -n "${extra-}" ] || ! [[ "$lsha" =~ $oid ]] || ! [[ "${rsha-}" =~ $oid ]]; then
      violations+=("pre-push: malformed ref line: ${_line}")
      continue
    fi
    # A remote value that is not a commit here (not fetched, a blob or tree) excludes nothing.
    # stderr is dropped because peeling a blob or tree prints an error even with --quiet.
    if ! [[ "$rsha" =~ ^0+$ ]] && remote_commit="$(git rev-parse --verify --quiet "${rsha}^{commit}" 2>/dev/null)"; then
      published+=("$remote_commit")
    fi
    [[ "$lsha" =~ ^0+$ ]] && continue
    pt_refs+=("$rref")
    if ! commit="$(git rev-parse --verify --quiet "${lsha}^{commit}")"; then
      violations+=("${lref}: pushed object ${lsha} is not a resolvable commit")
      continue
    fi
    push_commits+=("$commit")
  done
  if [ ${#push_commits[@]} -gt 0 ]; then
    scan_pushed 'settings.json' 'settings.json (pushed)' keys
    scan_pushed 'plans/*.md' 'plans/*.md (pushed)'
  fi
fi

case "$claude_repo" in
  yes) if [ "$MODE" = pre-commit ]; then pt_scan_staged; else pt_scan_pushed; fi ;;
  unknown) pt_violation "private-terms scope check failed: git could not name the git dir of this ~/.claude checkout (fail-closed)" ;;
esac

if [ ${#violations[@]} -gt 0 ]; then
  printf '\n\033[31m[BLOCKED] Forbidden content detected. %s aborted.\033[0m\n\n' "$MODE" >&2
  for v in "${violations[@]}"; do
    printf '\033[33m  - %s\033[0m\n' "$v" >&2
  done
  printf '\n' >&2
  if [ "$pt_hit" -lt ${#violations[@]} ]; then
    printf '\033[36mMove secrets/machine-specific values out of tracked files (settings.local.json is gitignored).\033[0m\n' >&2
    printf '\033[36mMCP servers belong in ~/.claude.json (managed by '"'"'claude mcp add'"'"'), never in settings.json.\033[0m\n' >&2
    printf '\033[36mPlans are committed under approach A — never paste raw tokens/credentials into plan files.\033[0m\n' >&2
  fi
  if [ "$pt_term_hits" -gt 0 ]; then
    printf '\033[36mPrivate terms come from %s (untracked) — do not open or quote it with tools.\033[0m\n' "$PT_LIST" >&2
    printf '\033[36mReplace each hit with a generic label (e.g. "회사 repo") and keep terms out of commit messages.\033[0m\n' >&2
    printf '\033[36mA message or identity hit means rewriting that commit before pushing (git commit --amend [--reset-author], or the commit-check skill for older unpushed commits).\033[0m\n' >&2
    printf '\033[36mA hit in commits that are already on the remote main means origin/main is stale — run git fetch origin.\033[0m\n' >&2
  fi
  if [ "$pt_named" -gt 0 ]; then
    printf '\033[36mTake the file named private-terms.txt out: git rm --cached <path> before committing, or drop it from the unpushed commits.\033[0m\n' >&2
  fi
  if [ "$pt_hit" -gt $((pt_term_hits + pt_named)) ]; then
    printf '\033[36mPrivate-term check error: the reported line of %s needs fixing by hand (do not open or rewrite the list with tools); a scope or git failure means git could not read this repo.\033[0m\n' "$PT_LIST" >&2
  fi
  if [ "$pt_hit" -eq 0 ]; then
    [ "$MODE" = "pre-push" ] && _cmd=push || _cmd=commit
    printf '\033[90mTo bypass once (NOT recommended): git %s --no-verify\033[0m\n' "$_cmd" >&2
  fi
  exit 1
fi

exit 0
