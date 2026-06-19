#!/usr/bin/env bash
# /audit 기계 점검 — 운영 자산 *간* 참조 정합만(read-only). repo root 에서 실행.
# 심각도 prefix: [error]=실행경로 깨짐 / [warn]=미등록·한쪽누락 / [info]=인벤토리·약참조(단정 아님) / [ok].
# 경계: README↔surface drift 는 dlc-doc-drift hook, wiki 내부 무결성은 /wiki lint 영역 — 여기서 안 본다(개수만).
# 수정·파괴 명령 없음(read-only). 부분 실패는 그 점검만 skip + 명시, 스크립트는 exit 0.
set -u

# repo root 로 self-cd — 어디서 호출해도 cwd 의존 거짓통과(점검 다수가 빈 결과로 error=0) 차단.
# skills/audit/audit.sh 구조 가정 → ../.. = repo root. git 비의존(가드로 검증).
SELF=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$SELF/../.." 2>/dev/null && pwd)  # cd 실패 시 빈값 → 아래 가드가 처리
if [ -n "$ROOT" ] && [ -f "$ROOT/CLAUDE.md" ] && [ -d "$ROOT/skills" ]; then
  cd "$ROOT" || { echo "[error] repo root 진입 실패: $ROOT"; exit 2; }
else
  echo "[error] repo root(~/.claude 류) 를 찾지 못함 — skills/audit/ 구조 안에서 실행하세요"
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
  I "wiki 내부 무결성(orphan·dead link·모순)은 /wiki lint 로 점검(audit 은 개수만)"
else
  I "wiki 없음 → skip"
fi

echo "== 요약: error=$err warn=$warn (info 는 수동 확인 권고) =="
exit 0
