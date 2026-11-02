#!/usr/bin/env bash
# improve.sh 점검 1 — settings hook 이 가리키는 스크립트 실존. exec form(args 절대경로)은 그 경로 그대로 확인해야 한다:
# 다른 머신에서 복사해 사용자명이 틀린 경로도 `scripts/<이름>` 만 떼어 보면 [ok] 로 통과한다.
set -u
here=$(cd "$(dirname "$0")" && pwd)
root=$(mktemp -d) || exit 1
trap 'rm -rf "$root"' EXIT
mkdir -p "$root/skills/improve" "$root/scripts" "$root/elsewhere/scripts"
cp "$here/improve.sh" "$root/skills/improve/improve.sh"
: >"$root/CLAUDE.md"
: >"$root/scripts/ok.js"
: >"$root/elsewhere/scripts/only-abs.js"
# Claude Code 가 Windows 에서 쓰는 C:/ 표기(MSYS 의 pwd -W)를 우선한다.
abs=$( (cd "$root" && pwd -W 2>/dev/null) || echo "$root")
cat >"$root/settings.json" <<EOF
{"env": {"TOOL": "$abs/not-a-hook/run.sh"},
 "hooks": {"Stop": [{"hooks": [
  {"type": "command", "command": "node", "args": ["$abs/scripts/ok.js"]},
  {"type": "command", "command": "node", "args": ["$abs/other-home/.claude/scripts/ok.js", "Stop"]},
  {"type": "command", "command": "node", "args": ["$abs/elsewhere/scripts/only-abs.js"]},
  {"type": "command", "command": "node", "args": ["~/.claude/scripts/ok.js"]},
  {"type": "command", "command": "/usr/bin/env node $abs/scripts/ok.js"},
  {"type": "command", "command": "node ~/.claude/scripts/ok.js"}
]}]}}
EOF
out=$(bash "$root/skills/improve/improve.sh" 2>&1 | sed -n '/^== 1\./,/^== 2\./p')
fail=0
has() { # has <설명> <기대 줄(고정 문자열)>
  if printf '%s\n' "$out" | grep -qF -- "$2"; then echo "ok   $1"; else echo "FAIL $1 — 없음: $2"; fail=1; fi
}
lacks() { # lacks <설명> <나오면 안 되는 문자열>
  if printf '%s\n' "$out" | grep -qF -- "$2"; then echo "FAIL $1 — 나옴: $2"; fail=1; else echo "ok   $1"; fi
}
has '없는 절대경로는 error' "[error] settings.json 가 참조한 $abs/other-home/.claude/scripts/ok.js 없음"
has '있는 절대경로는 ok' "[ok] settings.json: $abs/scripts/ok.js"
has 'repo 밖의 있는 절대경로도 ok' "[ok] settings.json: $abs/elsewhere/scripts/only-abs.js"
lacks 'exec form 경로를 repo 기준으로 다시 보지 않는다' "scripts/only-abs.js 없음"
has 'exec form args 의 ~ 는 error' "[error] settings.json 의 exec form args '~/.claude/scripts/ok.js'"
lacks '절대경로 인터프리터로 시작하는 셸 형식을 경로로 오인하지 않는다' "/usr/bin/env node"
lacks 'hooks 밖의 절대경로는 보지 않는다' "not-a-hook"
has '셸 형식 ~ 경로는 repo 기준으로 확인' "[ok] settings.json: scripts/ok.js"
if [ "$fail" -ne 0 ]; then printf -- '--- 점검 1 출력 ---\n%s\n' "$out"; exit 1; fi

# 점검 2 — 전역 피드백 임시칸(~/.claude/FEEDBACK.local.md)의 승격 대기 규칙 수. 없으면 말하지 않는다.
home=$root/home
mkdir -p "$home/.claude"
sec2() { HOME=$home bash "$root/skills/improve/improve.sh" 2>&1 | sed -n '/^== 2\./,/^== 3\./p'; }
out=$(sec2)
has '점검 2 가 실행됨' "== 2. "
lacks '임시칸이 없으면 조용' "FEEDBACK.local.md"
printf '# inbox\n' >"$home/.claude/FEEDBACK.local.md"
out=$(sec2)
lacks '규칙이 없는 임시칸도 조용' "FEEDBACK.local.md"
printf '# inbox\n- rule one — why\n- rule two — why\n' >"$home/.claude/FEEDBACK.local.md"
out=$(sec2)
has '임시칸 규칙 수를 보고' "[info] FEEDBACK.local.md 승격 대기 규칙 2개"
if [ "$fail" -ne 0 ]; then printf -- '--- 점검 2 출력 ---\n%s\n' "$out"; exit 1; fi
echo "improve.test.sh: all passed"
