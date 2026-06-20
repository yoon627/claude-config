#!/usr/bin/env bash
# Claude Code 환경 부트스트랩 (macOS, 비-conda).
# 새 머신에서 한 번 실행하면 도구 + 설정 + (옵션)memory 를 재현한다. idempotent.
# 사용법:  bash scripts/bootstrap/setup.sh [--memory-from <기존 ~/.claude 경로>] [--dry-run]
#
# 전제: claude(공식 설치), brew, git 이 이미 있어야 한다(이 repo 를 clone·실행하는 환경).
# rtk 는 별도 설치가 아니라 headroom 번들(~/.headroom/bin/rtk)을 심링크+서명한다.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# codegraph 인덱스·memory 복원 대상은 Claude Code 가 실제 읽는 ~/.claude 로 고정 —
# 스크립트를 worktree/다른 경로에서 실행해도 엉뚱한 곳에 안 만들도록 REPO_ROOT 와 분리.
CLAUDE_DIR="$HOME/.claude"
LOCAL_BIN="$HOME/.local/bin"
DRY_RUN=0
MEMORY_FROM=""

# --- args ---
while [ $# -gt 0 ]; do
  case "$1" in
    --memory-from) [ $# -ge 2 ] || { echo "--memory-from 에 경로 인자 필요" >&2; exit 2; }; MEMORY_FROM="$2"; shift 2 ;;
    --dry-run)     DRY_RUN=1; shift ;;
    -h|--help)
      sed -n '2,9p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# --- logging ---
c_ok=$'\033[32m'; c_skip=$'\033[2m'; c_warn=$'\033[33m'; c_run=$'\033[36m'; c_off=$'\033[0m'
ok()   { printf "%s[ OK ]%s %s\n"   "$c_ok"   "$c_off" "$*"; }
skip() { printf "%s[SKIP]%s %s\n"   "$c_skip" "$c_off" "$*"; }
warn() { printf "%s[WARN]%s %s\n"   "$c_warn" "$c_off" "$*" >&2; }
run()  { printf "%s[ .. ]%s %s\n"   "$c_run"  "$c_off" "$*"; }
# 절대경로/명령 존재 (PATH 미반영 환경 대비 — 절대경로 우선)
have() { command -v "$1" >/dev/null 2>&1; }
do_cmd() { if [ "$DRY_RUN" = 1 ]; then echo "    (dry-run) $*"; else "$@"; fi; }

[ "$(uname)" = "Darwin" ] || { warn "이 스크립트는 macOS 전용이다. Windows 는 setup.ps1, Linux 는 미지원."; exit 1; }

echo "== Claude Code 환경 부트스트랩 (macOS, 비-conda) =="
echo "   repo: $REPO_ROOT"
[ "$DRY_RUN" = 1 ] && echo "   (DRY-RUN: 실제 변경 없음)"

# --- 0. 전제: claude / brew / git ---
prereq_ok=1
if [ -x "$LOCAL_BIN/claude" ] || have claude; then ok "claude 있음"; else
  warn "claude 미설치 — 공식 설치 후 재실행: https://docs.claude.com/claude-code (이 repo 실행 전제)"; prereq_ok=0; fi
if have brew; then ok "brew 있음"; else
  warn "Homebrew 미설치 — 설치: https://brew.sh 후 재실행"; prereq_ok=0; fi
have git || { warn "git 미설치"; prereq_ok=0; }
[ "$prereq_ok" = 1 ] || { warn "전제 미충족 — 위 항목 해결 후 재실행."; exit 1; }

# --- 1. PATH: ~/.local/bin (현재 셸에 즉시 반영 — 이후 단계가 절대경로/PATH 둘 다 쓰게) ---
mkdir -p "$LOCAL_BIN"
case ":$PATH:" in *":$LOCAL_BIN:"*) : ;; *) export PATH="$LOCAL_BIN:$PATH" ;; esac

# --- 2. brew: node (codegraph npm 전 선행) ---
if have node; then skip "node 있음 ($(node --version 2>/dev/null))"; else
  run "brew install node"; do_cmd brew install node && ok "node 설치"; fi

# --- 2b. jq (rtk hook rtk-rewrite.sh 가 stdin JSON 파싱에 의존) ---
if have jq; then skip "jq 있음"; else
  run "brew install jq"; do_cmd brew install jq && ok "jq 설치"; fi

# --- 3. uv (astral, 비-conda) ---
if [ -x "$LOCAL_BIN/uv" ] || have uv; then skip "uv 있음"; else
  run "uv 설치 (astral)"; do_cmd sh -c 'curl -LsSf https://astral.sh/uv/install.sh | sh' && ok "uv 설치"; fi

# --- 4. headroom (uv tool install headroom-ai) — rtk 번들 전 선행 ---
if have headroom; then skip "headroom 있음 ($(headroom --version 2>/dev/null | head -1))"; else
  run "uv tool install headroom-ai"; do_cmd uv tool install headroom-ai && ok "headroom 설치"; fi

# --- 5. codegraph (npm -g) ---
if have codegraph; then skip "codegraph 있음"; else
  run "npm install -g @colbymchenry/codegraph"; do_cmd npm install -g @colbymchenry/codegraph && ok "codegraph 설치"; fi

# --- 6. rtk (headroom 번들 → 심링크 + 서명; memory rtk-headroom-path-fix 규약) ---
HEADROOM_RTK="$HOME/.headroom/bin/rtk"; RTK_LINK="$LOCAL_BIN/rtk"
if [ -x "$HEADROOM_RTK" ]; then
  # dangling 심링크 guard: 심링크이고(-L) 타겟 살아있고(-e) 타겟이 정확히 headroom rtk 여야 정상
  if [ -L "$RTK_LINK" ] && [ -e "$RTK_LINK" ] && [ "$(readlink "$RTK_LINK")" = "$HEADROOM_RTK" ]; then skip "rtk 심링크 정상"; else
    run "rtk 심링크 $RTK_LINK -> $HEADROOM_RTK"; do_cmd rm -f "$RTK_LINK"; do_cmd ln -s "$HEADROOM_RTK" "$RTK_LINK" && ok "rtk 심링크"; fi
  # hook 서명: verify 통과면 skip, 아니면 init(서명). hook 파일 직접편집 금지.
  if [ "$DRY_RUN" = 1 ]; then skip "rtk hook 검증/서명(dry-run)"
  elif "$RTK_LINK" verify >/dev/null 2>&1; then skip "rtk hook 무결성 OK"
  else run "rtk init -g --hook-only --no-patch"; "$RTK_LINK" init -g --hook-only --no-patch && ok "rtk hook 등록·서명"; fi
else
  warn "headroom 번들 rtk 없음 ($HEADROOM_RTK) — headroom 설치/기동 후 재실행하면 생성됨"
fi

# --- 7. MCP 등록 (홈 ~/.claude.json) ---
mcp_list="$(claude mcp list 2>/dev/null || true)"
if printf '%s\n' "$mcp_list" | grep -qi '^codegraph'; then skip "codegraph MCP 등록됨"; else
  run "codegraph install -y"; do_cmd codegraph install -y && ok "codegraph MCP 등록"; fi
if printf '%s\n' "$mcp_list" | grep -qi '^headroom'; then skip "headroom MCP 등록됨"; else
  run "claude mcp add headroom"; do_cmd claude mcp add headroom -- headroom mcp serve && ok "headroom MCP 등록"; fi

# --- 8. headroom proxy (launchd service, token mode) ---
hr_status="$(headroom install status 2>/dev/null || true)"
# 'Status:   running' 줄만 정확 매칭 — 'not running'·로그 잔재 오매칭 회피 (BSD grep: \s 미지원 → [[:space:]])
if printf '%s\n' "$hr_status" | grep -qiE '^status:[[:space:]]+running'; then skip "headroom proxy running"; else
  run "headroom install apply (persistent-service, token)"
  do_cmd headroom install apply --preset persistent-service --mode token
  do_cmd headroom install start && ok "headroom proxy 기동"; fi

# --- 9. codegraph init (~/.claude 인덱스) ---
if [ -d "$CLAUDE_DIR/.codegraph" ]; then skip "codegraph 인덱스 있음"; else
  run "codegraph init $CLAUDE_DIR"; do_cmd codegraph init "$CLAUDE_DIR" && ok "codegraph init"; fi

# --- 10. zshrc env (marker 블록 멱등 교체; headroom 블록은 install 이 따로 관리) ---
ZSHRC="$HOME/.zshrc"; M_START="# >>> claude-bootstrap env >>>"; M_END="# <<< claude-bootstrap env <<<"
read -r -d '' BLOCK <<EOF || true
$M_START
export PATH="\$HOME/.local/bin:\$PATH"
[ -f "\$HOME/.cargo/env" ] && source "\$HOME/.cargo/env"
export ANTHROPIC_MODEL='opus[1m]'
export CLAUDE_CODE_EFFORT_LEVEL=max
$M_END
EOF
touch "$ZSHRC"
if grep -qF "$M_START" "$ZSHRC"; then
  if [ "$DRY_RUN" = 1 ]; then skip "zshrc marker 블록 갱신(dry-run)"; else
    tmp="$(mktemp)"
    # 블록 제거 후 재추가. M_START 만 있고 M_END 가 없으면(손상) exit 3 → 원본 보존(데이터 손실 방지).
    if awk -v s="$M_START" -v e="$M_END" '
        $0==s{inb=1; seen=1; next}
        $0==e && inb{inb=0; ended=1; next}
        !inb{print}
        END{ if(seen && !ended) exit 3 }' "$ZSHRC" > "$tmp"; then
      printf '%s\n' "$BLOCK" >> "$tmp"
      cat "$tmp" > "$ZSHRC"; rm -f "$tmp"   # cat>: symlink 인 .zshrc 보존(mv 는 치환)
      ok "zshrc marker 블록 갱신(멱등)"
    else
      rm -f "$tmp"; warn "zshrc 의 '$M_START' 블록이 '$M_END' 로 종결되지 않음 — 손상 의심, 건드리지 않음. 수동 확인 필요."
    fi
  fi
else
  if [ "$DRY_RUN" = 1 ]; then skip "zshrc marker 블록 추가(dry-run)"; else
    printf '\n%s\n' "$BLOCK" >> "$ZSHRC"; ok "zshrc marker 블록 추가"; fi
fi

# --- 11. memory 복원 (옵션; git 미추적이라 소스 필요) ---
if [ -n "$MEMORY_FROM" ]; then
  src="$MEMORY_FROM/projects"
  if [ -d "$src" ]; then
    run "memory 복원: $src → $CLAUDE_DIR/projects (overwrite, 소스에 없는 파일은 보존)"
    do_cmd rsync -a --include='*/' --include='memory/***' --exclude='*' "$src/" "$CLAUDE_DIR/projects/" && ok "memory 복원"
  else warn "memory 소스 없음: $src"; fi
else
  skip "memory: --memory-from 미지정 (새 머신은 비어있음 — 기존 머신 ~/.claude 경로를 주면 복원)"
fi

# --- 12. git / gh 안내 ---
git config --global user.name  >/dev/null 2>&1 || warn "git user.name 미설정 — git config --global user.name '...'"
git config --global user.email >/dev/null 2>&1 || warn "git user.email 미설정 — git config --global user.email '...'"
if have gh; then gh auth status >/dev/null 2>&1 || warn "gh 미인증 — gh auth login"; else warn "gh 미설치 — brew install gh"; fi

echo
ok "부트스트랩 완료. 새 셸을 열거나 'source ~/.zshrc' 후 'claude' 실행."
