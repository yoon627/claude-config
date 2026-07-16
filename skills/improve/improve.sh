#!/usr/bin/env bash
# /improve 기계 점검 — ① 운영 자산 *간* 참조 정합(구 /audit 승계, read-only) ② dlc 신호 집계.
# 심각도 prefix: [error]=실행경로 깨짐 / [warn]=미등록·한쪽누락 / [info]=인벤토리·약참조(단정 아님) / [ok].
# 경계: README↔surface drift 는 dlc-doc-drift hook, wiki 내부 무결성은 /wiki lint 영역 — 여기서 안 본다(개수만).
#   신호 집계는 hook 이 emit 한 판정의 *사후 집계*다(재판정 아님).
# 수정·파괴 명령 없음(read-only). 부분 실패는 그 점검만 skip + 명시, 스크립트는 exit 0.
# check 8 = plan-lint(tracked plans, 항상). deep 모드(`improve.sh deep`): ⑨ 표면 크기 ⑩ 사용량 카운트 ⑪ MCP 인벤토리 추가(광역 관측, 여전히 read-only·secret 미출력).
set -u

case "${1:-}" in deep | --deep) DEEP=1 ;; *) DEEP=0 ;; esac

# repo root 로 self-cd — 어디서 호출해도 cwd 의존 거짓통과(점검 다수가 빈 결과로 error=0) 차단.
# skills/improve/improve.sh 구조 가정 → ../.. = repo root. git 비의존(가드로 검증).
SELF=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$SELF/../.." 2>/dev/null && pwd)  # cd 실패 시 빈값 → 아래 가드가 처리
if [ -n "$ROOT" ] && [ -f "$ROOT/CLAUDE.md" ] && [ -d "$ROOT/skills" ]; then
  cd "$ROOT" || { echo "[error] repo root 진입 실패: $ROOT"; exit 2; }
else
  echo "[error] repo root(~/.claude 류) 를 찾지 못함 — skills/improve/ 구조 안에서 실행하세요"
  exit 2
fi

err=0
warn=0
E() { echo "[error] $*"; err=$((err + 1)); }
W() { echo "[warn] $*"; warn=$((warn + 1)); }
I() { echo "[info] $*"; }
OK() { echo "[ok] $*"; }

echo "== 1. settings hooks → scripts 실존 (error if missing) =="
for sf in settings.json settings.local.json; do
  [ -f "$sf" ] || continue
  # command 안의 scripts/*.js 만 추출(inline darwin rtk-rewrite·SessionStart git pull 은 파일 아니라 제외).
  while read -r s; do
    [ -n "$s" ] || continue
    if [ -f "$s" ]; then OK "$sf: $s"; else E "$sf 가 참조한 $s 없음"; fi
  done < <(grep -oE 'scripts/[A-Za-z0-9_.-]+\.js' "$sf" 2>/dev/null | sort -u)
done

echo "== 2. MEMORY.md 인덱스 ↔ memory 파일 (양방향; gitignored 절대경로 발견) =="
MEMDIR=""
for d in "$HOME"/.claude/projects/*--claude/memory; do [ -d "$d" ] && { MEMDIR=$d; break; }; done
if [ -z "$MEMDIR" ] || [ ! -f "$MEMDIR/MEMORY.md" ]; then
  I "MEMORY 디렉토리 못 찾음(머신종속·gitignored) → 이 점검 skip"
else
  while read -r f; do
    [ -n "$f" ] || continue
    if [ -f "$MEMDIR/$f.md" ]; then OK "index→file: $f"; else W "MEMORY.md 인덱스가 가리킨 $f.md 없음(고아 인덱스)"; fi
  done < <(grep -oE '\]\([a-z0-9-]+\.md\)' "$MEMDIR/MEMORY.md" | sed 's/[][)(]//g; s/\.md$//')
  for p in "$MEMDIR"/*.md; do
    [ -e "$p" ] || continue
    b=$(basename "$p" .md)
    [ "$b" = MEMORY ] && continue
    grep -q "($b.md)" "$MEMDIR/MEMORY.md" || W "memory $b.md 가 MEMORY.md 인덱스에 없음(인덱스 누락)"
  done
fi

echo "== 3. CLAUDE.md 가 참조한 agent 실존 (단방향 — 추측 참조 방지) =="
if [ -f CLAUDE.md ]; then
  while read -r name; do
    [ -n "$name" ] || continue
    if [ -f "agents/$name.md" ]; then OK "agent $name 실존"; else E "CLAUDE.md 가 참조한 agent '$name' 의 agents/$name.md 없음"; fi
  done < <(grep -oE '\*\*[a-z][a-z-]+\*\*' CLAUDE.md | sed 's/\*//g' | grep -E 'reviewer|simplifier|researcher' | sort -u)
fi

echo "== 4. skills/*/SKILL.md frontmatter name (error if 없음) =="
for sk in skills/*/SKILL.md; do
  [ -f "$sk" ] || continue
  d=$(basename "$(dirname "$sk")")
  if grep -qE '^name:[[:space:]]*[^[:space:]]' "$sk"; then OK "skill $d: name 있음"; else E "skill $d: SKILL.md frontmatter name 없음/빔"; fi
done

echo "== 5. 미참조 scripts/*.js 후보 (info — 단정 아님; *.ps1/*.py 수동유틸·*.test.js 제외) =="
for js in scripts/*.js; do
  [ -f "$js" ] || continue
  case "$js" in *.test.js) continue ;; esac        # 테스트는 후보 아님
  b=$(basename "$js")
  stem=${b%.js}
  esc=$(printf '%s' "$stem" | sed 's/[][\.*^$/]/\\&/g')  # 정규식 특수문자 이스케이프(. → 리터럴)
  ref=no
  grep -q "$b" settings.json 2>/dev/null && ref=yes                                  # (a) settings 등록
  grep -rqE "require\(['\"][./]*${esc}(\.js)?['\"]" scripts/ 2>/dev/null && ref=yes   # (b) require 피호출(.js 경계 — 부분일치 차단)
  grep -rq "$b" README.md .github/ 2>/dev/null && ref=yes                            # (c) 문서·CI 언급
  [ "$ref" = no ] && I "scripts/$b: settings·require·문서·CI 어디에도 안 보임(죽은코드 후보 — 수동 확인)"
done

echo "== 6. wiki index ↔ pages 개수 (내부 무결성은 /wiki lint 권장) =="
if [ -d wiki/pages ] && [ -f wiki/index.md ]; then
  pc=$(find wiki/pages -name '*.md' | wc -l | tr -d ' ')
  ic=$(grep -cE '^- \[\[' wiki/index.md 2>/dev/null || true)
  ic=${ic:-0}
  if [ "$pc" = "$ic" ]; then OK "wiki pages=$pc = index 등재=$ic"; else W "wiki pages=$pc ≠ index 등재=$ic → /wiki lint 권장"; fi
  I "wiki 내부 무결성(orphan·dead link·모순)은 /wiki lint 로 점검(improve 는 개수만)"
else
  I "wiki 없음 → skip"
fi

echo "== 7. dlc 신호 집계 (telemetry — hook 판정의 사후 집계, 재판정 아님) =="
SIGDIR=${CLAUDE_DLC_SIGNAL_DIR:-$HOME/.claude/telemetry}
if [ -f "$SIGDIR/dlc-signals.jsonl" ]; then
  node scripts/dlc-signal.js summary || I "신호 집계 실행 실패(node) → skip"
else
  I "신호 파일 없음($SIGDIR/dlc-signals.jsonl) → 집계 skip — 신호는 hook 발동 시 자동 누적"
fi

echo "== 8. plan 참조 무결성 (tracked plans — plan-lint; §10 plan 스펙 검증) =="
if [ -f scripts/plan-lint.js ]; then
  plans=$(git ls-files 'plans/*/*-plan.md' 2>/dev/null)
  if [ -z "$plans" ]; then
    I "tracked plan 없음(plans/ 미커밋?) → plan-lint skip"
  else
    out=$(printf '%s\n' "$plans" | xargs node scripts/plan-lint.js 2>&1)
    if [ -z "$out" ]; then
      OK "plan-lint: tracked plan 무결성 통과"
    else
      while IFS= read -r ln; do [ -n "$ln" ] && W "plan-lint: $ln"; done <<<"$out"
    fi
  fi
else
  I "scripts/plan-lint.js 없음 → skip"
fi

if [ "$DEEP" = 1 ]; then
  echo "== 9. 주입·로드 표면 크기 (deep — wc -c; 토큰 압박 관측, 상대경로·카운트만) =="
  tot=0
  for f in CLAUDE.md skills/*/SKILL.md agents/*.md; do
    [ -f "$f" ] || continue
    b=$(wc -c < "$f" | tr -d ' ')
    tot=$((tot + b))
    I "${b}B  $f"
  done
  I "표면 합계: ${tot}B"

  echo "== 10. 사용량 카운트 (deep — transcript JSONL 파싱; 카운트·slug 만, 원문·파일명 미출력) =="
  if [ -f scripts/usage-count.js ]; then
    node scripts/usage-count.js || I "usage-count 실행 실패 → skip"
  else
    I "scripts/usage-count.js 없음 → skip"
  fi

  echo "== 11. MCP 서버 인벤토리 (deep — 이름만; ~/.claude.json, args·env·secret 미출력) =="
  if [ -f "$HOME/.claude.json" ]; then
    node -e '
      const fs = require("fs");
      let j;
      try { j = JSON.parse(fs.readFileSync(process.env.HOME + "/.claude.json", "utf8")); }
      catch { console.log("[info] ~/.claude.json 파싱 실패 → skip"); process.exit(0); }
      const names = new Set();
      const add = (o) => { if (o && typeof o === "object") for (const k of Object.keys(o)) names.add(k); };
      add(j.mcpServers);
      const projs = j.projects || {};
      for (const p of Object.keys(projs)) add(projs[p] && projs[p].mcpServers);
      const arr = [...names].sort();
      console.log("[info] MCP 서버 " + arr.length + "종: " + (arr.join(", ") || "(없음)"));
    ' || I "MCP 인벤토리 실행 실패 → skip"
  else
    I "홈 .claude.json 없음 → MCP 인벤토리 skip"
  fi
fi

echo "== 요약: error=$err warn=$warn (info 는 수동 확인 권고; deep=$DEEP) =="
exit 0
