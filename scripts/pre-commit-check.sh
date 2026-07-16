#!/usr/bin/env bash
# pre-commit-check.sh — guard settings.json (forbidden keys) and settings.json + staged plans/*.md (secret/token patterns)
# Usage: pre-commit-check.sh [pre-commit|pre-push]
# plans/ is tracked under approach A (plans-sync), so plan files are scanned for pasted secrets.

set -e

MODE="${1:-pre-commit}"

# Block direct push to protected branches first (pre-push). pre-push receives
# "<local ref> <local sha> <remote ref> <remote sha>" lines on stdin.
if [ "$MODE" = "pre-push" ]; then
  while read -r _lref _lsha rref _rsha || [ -n "$rref" ]; do
    case "$rref" in
      refs/heads/main|refs/heads/master)
        printf '\n\033[31m[BLOCKED] Direct push to %s is not allowed. Open a PR instead.\033[0m\n' "$rref" >&2
        printf '\033[90mBypass once (NOT recommended): git push --no-verify\033[0m\n' >&2
        exit 1
        ;;
    esac
  done
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
  tracked="$(git ls-tree --name-only HEAD 2>/dev/null || true)"
  if printf '%s\n' "$tracked" | grep -qx 'settings.json'; then
    sj="$(git show HEAD:settings.json 2>/dev/null || true)"
    scan_keys "$sj"
    scan_tokens "$sj" 'settings.json'
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
  printf '\033[90mTo bypass once (NOT recommended): git %s --no-verify\033[0m\n' "$MODE" >&2
  exit 1
fi

exit 0
