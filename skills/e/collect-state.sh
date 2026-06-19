#!/usr/bin/env bash
# e(plan-end) 마무리용 읽기전용 git 신호 수집 — 평문 `key: value` 출력(jq 불필요, LLM 직접 파싱).
# 호출측(skills/e/SKILL.md)이 이 신호로 판정한다. 이 스크립트는 raw 사실만 — 판정·삭제 결정·
# 파괴 명령(worktree remove·branch -d/-D·commit·add)은 하지 않는다(read-only).
# cwd(또는 대상 worktree) 기준. 각 점검 독립 fail-safe: 실패 필드는 none/unknown, 스크립트는 exit 0.
# bool 평탄화 금지 — isMainWorktree·mergedToBase 판정은 호출측이 raw(root/mainWorktree path, inBase, remoteContainingHead)로 수행.
set -u

root=$(git rev-parse --show-toplevel 2>/dev/null || true)
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)
detached=false
[ "$branch" = "HEAD" ] && detached=true
# substr($0,10): "worktree " 는 9자 → 경로는 10번째부터. $2 는 공백 포함 경로를 잘라 mainWorktree 오판(비-메인 오발) 유발.
main=$(git worktree list --porcelain 2>/dev/null | awk '/^worktree /{print substr($0,10); exit}')

# dirty = working tree 변경 여부(untracked `??` 포함; status --porcelain). quotePath=false 로 공백 경로 따옴표 래핑 방지.
# 명령 실패는 false 로 평탄화하지 않고 unknown 노출(false→clean 오인→삭제 false-positive 차단).
if status=$(git -c core.quotePath=false status --porcelain 2>/dev/null); then
  if [ -n "$status" ]; then dirty=true; else dirty=false; fi
else
  dirty=unknown; status=""
fi

# upstream / unpushed — "false(없음)" 와 "unknown(못 판단)" 분리(false-positive 삭제 차단).
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
unpushed=""
if [ -n "$upstream" ]; then
  upstreamStatus=upstream
  unpushedStatus=upstream
  unpushed=$(git log --format='%h %s' '@{u}..HEAD' 2>/dev/null || true)
else
  upstreamStatus=none
  if [ -n "$(git remote 2>/dev/null || true)" ] && [ "$detached" = false ] && [ -n "$branch" ] && [ "$branch" != "HEAD" ]; then
    unpushedStatus=allRemotes
    unpushed=$(git log --format='%h %s' "$branch" --not --remotes 2>/dev/null || true)
  else
    unpushedStatus=unknown
  fi
fi

# base 폴백은 origin/HEAD → origin/main 만(과욕 금지). inBase = log base..HEAD 빈지(baseValid 일 때만).
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo "origin/main")
if git rev-parse --verify --quiet "$base" >/dev/null 2>&1; then
  baseValid=true
  if [ "$detached" = false ]; then
    if [ -z "$(git log --format='%h' "$base..HEAD" 2>/dev/null || true)" ]; then inBase=true; else inBase=false; fi
  else
    inBase=unknown
  fi
else
  baseValid=false
  inBase=unknown
fi

# HEAD 를 포함하는 원격 브랜치(self 포함 raw — self 제외·(a)/(b) 판정은 호출측).
remoteContaining=$(git branch -r --contains HEAD 2>/dev/null | sed 's/^[ *]*//' || true)

# ignored 인벤토리(repo-relative; worktree remove 가 무경고 동반삭제하는 대상 점검용). 실패는 unknown(없음으로 평탄화 금지).
if ig=$(git -c core.quotePath=false status --porcelain --ignored 2>/dev/null); then
  ignoredStatus=known
  ignored=$(printf '%s\n' "$ig" | awk '/^!! /{print substr($0,4)}')
else
  ignoredStatus=unknown; ignored=""
fi

emit_list() {
  if [ -n "$2" ]; then printf '%s:\n' "$1"; printf '%s\n' "$2" | sed 's/^/  /'; else printf '%s:\n  (none)\n' "$1"; fi
}

echo "root: ${root:-none}"
echo "branch: ${branch:-none}"
echo "detached: $detached"
echo "mainWorktree: ${main:-none}"
echo "dirty: $dirty"
echo "upstreamStatus: $upstreamStatus"
echo "upstream: ${upstream:-none}"
echo "unpushedStatus: $unpushedStatus"
echo "base: $base"
echo "baseValid: $baseValid"
echo "inBase: $inBase"
echo "ignoredStatus: $ignoredStatus"
emit_list "status" "$status"
emit_list "unpushed" "$unpushed"
emit_list "remoteContainingHead" "$remoteContaining"
emit_list "ignored" "$ignored"

exit 0
