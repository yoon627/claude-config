#!/bin/bash
# Session base input tokens with and without the global CLAUDE.md (claudeMdExcludes).
cd "$(mktemp -d)" || exit 1
m() {
  claude -p "ok 라고만 답해" --model sonnet --output-format json --no-session-persistence --max-turns 1 --settings "$2" 2>/dev/null \
  | python3 -c 'import json,sys;d=json.load(sys.stdin);u=d["usage"];print(sys.argv[1], "total_in", u.get("cache_creation_input_tokens",0)+u.get("cache_read_input_tokens",0)+u.get("input_tokens",0))' "$1"
}
m with '{}'
m without '{"claudeMdExcludes":["'"$HOME"'/.claude/CLAUDE.md"]}'
m with2 '{}'
m without2 '{"claudeMdExcludes":["'"$HOME"'/.claude/CLAUDE.md"]}'
