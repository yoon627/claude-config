#!/usr/bin/env bash
# pre-commit-check.sh — guard settings.json against forbidden keys / token patterns
# Usage: pre-commit-check.sh [pre-commit|pre-push]

set -e

MODE="${1:-pre-commit}"

if [ "$MODE" = "pre-commit" ]; then
  staged="$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)"
  echo "$staged" | grep -qx 'settings.json' || exit 0
  content="$(git show :settings.json 2>/dev/null || true)"
else
  tracked="$(git ls-tree --name-only HEAD 2>/dev/null || true)"
  echo "$tracked" | grep -qx 'settings.json' || exit 0
  content="$(git show HEAD:settings.json 2>/dev/null || true)"
fi

[ -z "$content" ] && exit 0

violations=()

# Blacklist JSON keys — textual match against canonical "key": form.
for key in mcpServers apiKeyHelper awsCredentialExport awsAuthRefresh; do
  if printf '%s' "$content" | grep -Eq "\"${key}\"[[:space:]]*:"; then
    violations+=("Forbidden key in settings.json: \"${key}\"  (move to settings.local.json or ~/.claude.json)")
  fi
done

# Token patterns. Each entry: name|regex
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
)

for entry in "${patterns[@]}"; do
  name="${entry%%|*}"
  rx="${entry#*|}"
  match="$(printf '%s' "$content" | grep -Eo "$rx" | head -n 1 || true)"
  if [ -n "$match" ]; then
    sample="$match"
    [ ${#sample} -gt 30 ] && sample="${sample:0:30}..."
    violations+=("Token pattern matched (${name}): ${sample}")
  fi
done

if [ ${#violations[@]} -gt 0 ]; then
  printf '\n\033[31m[BLOCKED] settings.json contains forbidden content. %s aborted.\033[0m\n\n' "$MODE" >&2
  for v in "${violations[@]}"; do
    printf '\033[33m  - %s\033[0m\n' "$v" >&2
  done
  printf '\n\033[36mMove sensitive/machine-specific values to ~/.claude/settings.local.json (gitignored).\033[0m\n' >&2
  printf '\033[36mMCP servers belong in ~/.claude.json (managed by '"'"'claude mcp add'"'"'), never in settings.json.\033[0m\n' >&2
  printf '\033[90mTo bypass once (NOT recommended): git %s --no-verify\033[0m\n' "$MODE" >&2
  exit 1
fi

exit 0
