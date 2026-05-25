#!/usr/bin/env bash
# notify-hook.sh — macOS notification hook for Claude Code
# Usage: notify-hook.sh <Event> <Sound>
#   Event: Stop | Notification
#   Sound: macOS system sound name (without .aiff). Default: Glass.
# Reads JSON from stdin (optional); uses .message and .cwd if present.

set +e

EVENT="${1:-Stop}"
SOUND="${2:-Glass}"

input=""
if [ ! -t 0 ]; then
  input="$(cat 2>/dev/null || true)"
fi

msg=""
cwd=""
if [ -n "$input" ] && command -v /usr/bin/python3 >/dev/null 2>&1; then
  parsed="$(/usr/bin/python3 -c '
import json, sys
try:
    d = json.loads(sys.stdin.read() or "{}")
except Exception:
    sys.exit(0)
print((d.get("message") or "").replace("\n", " "))
print(d.get("cwd") or "")
' <<<"$input" 2>/dev/null)"
  msg="$(printf '%s' "$parsed" | sed -n '1p')"
  cwd="$(printf '%s' "$parsed" | sed -n '2p')"
fi

if [ -z "$msg" ]; then
  if [ "$EVENT" = "Notification" ]; then
    msg="입력 대기"
  else
    msg="응답 완료"
  fi
fi

title="Claude"
if [ -n "$cwd" ]; then
  base="$(basename "$cwd" 2>/dev/null)"
  [ -n "$base" ] && title="$base"
fi

sound_file="/System/Library/Sounds/${SOUND}.aiff"
if [ -f "$sound_file" ]; then
  /usr/bin/afplay "$sound_file" >/dev/null 2>&1 &
fi

if command -v /usr/bin/osascript >/dev/null 2>&1; then
  esc_title="${title//\"/\\\"}"
  esc_msg="${msg//\"/\\\"}"
  /usr/bin/osascript -e "display notification \"${esc_msg}\" with title \"${esc_title}\"" >/dev/null 2>&1 &
fi

exit 0
