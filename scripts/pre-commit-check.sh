#!/usr/bin/env bash
# pre-commit-check.sh — guard settings.json (forbidden keys) and settings.json + plans/*.md (secret/token patterns)
# Usage: pre-commit-check.sh [pre-commit|pre-push]
# pre-commit scans the staged versions; pre-push scans the lines added by the commits being pushed
# (not yet on any remote-tracking ref), so commits that skipped pre-commit are still checked.
# plans/ is tracked under approach A (plans-sync), so plan files are scanned for pasted secrets.

set -e

# Match bytes, not characters: in a UTF-8 locale awk aborts and grep skips lines that carry an
# invalid byte, which would hide a token on the same line.
export LC_ALL=C
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

violations=()

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

# added_lines <pathspec> — lines added under <pathspec> by the pushed commits that no
# remote-tracking ref already has. Every option guards a way the scan could go blind:
# --full-history keeps side branches that net to no change; -m with log.diffMerges=separate
# shows what a merge adds against each parent; log.showRoot=true includes root commits;
# log.follow=false keeps a rename into the pathspec from being paired with its source;
# --text reads binary / -diff / bigFileThreshold files as text; --no-replace-objects reads
# the objects push actually sends; the color/prefix/textconv flags override diff config.
# Each pathspec is scanned in its own call, so a file renamed into it from outside shows
# its lines as added.
added_lines() {
  local out
  out="$(git --no-replace-objects -c core.quotePath=false -c log.diffMerges=separate \
    -c log.showRoot=true -c log.follow=false \
    log -p --text --no-color --no-ext-diff --no-textconv \
    --full-history -m -U0 --src-prefix=a/ --dst-prefix=b/ --format= \
    "${push_commits[@]}" --not --remotes -- "$1")" || return 1
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
  # Anything the guard cannot interpret is blocked: a real pre-push always passes four
  # fields and local objects, so a mismatch means the scan cannot be trusted.
  push_commits=()
  for _line in "${push_lines[@]+"${push_lines[@]}"}"; do
    [ -z "${_line//[[:space:]]/}" ] && continue
    read -r lref lsha rref rsha extra <<<"$_line" || true
    if [ -z "${rsha-}" ] || [ -n "${extra-}" ] || ! [[ "$lsha" =~ ^[0-9a-fA-F]{4,}$ ]]; then
      violations+=("pre-push: malformed ref line: ${_line}")
      continue
    fi
    [[ "$lsha" =~ ^0+$ ]] && continue
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

if [ ${#violations[@]} -gt 0 ]; then
  printf '\n\033[31m[BLOCKED] Forbidden content detected. %s aborted.\033[0m\n\n' "$MODE" >&2
  for v in "${violations[@]}"; do
    printf '\033[33m  - %s\033[0m\n' "$v" >&2
  done
  printf '\n\033[36mMove secrets/machine-specific values out of tracked files (settings.local.json is gitignored).\033[0m\n' >&2
  printf '\033[36mMCP servers belong in ~/.claude.json (managed by '"'"'claude mcp add'"'"'), never in settings.json.\033[0m\n' >&2
  printf '\033[36mPlans are committed under approach A — never paste raw tokens/credentials into plan files.\033[0m\n' >&2
  [ "$MODE" = "pre-push" ] && _cmd=push || _cmd=commit
  printf '\033[90mTo bypass once (NOT recommended): git %s --no-verify\033[0m\n' "$_cmd" >&2
  exit 1
fi

exit 0
