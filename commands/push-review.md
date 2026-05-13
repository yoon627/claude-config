---
description: codex(bg) + local 5관점(parallel) 동시 리뷰 → 통합 리포트. 사용자가 직접 push.
argument-hint: [base-ref=upstream]
---

# Push Review Orchestration

push 직전 codex 리뷰(background) + local 다중관점 리뷰(parallel subagents) 동시 실행, 통합 리포트로 push 결정.

## 핵심 원칙

- **자동 push 안 함**. 통합 리포트 출력 후 종료. 사용자가 직접 git push.
- 메인 컨텍스트 보호: subagent 가 파일에 저장, 메인엔 요약만.
- codex 와 local 을 **진짜 병렬**: codex 는 Bash bg, local 5개는 단일 메시지 5 tool_use.
- TS 동기화: REVIEW_TS env export 로 codex hook 과 같은 디렉토리 사용.

## 0. Hook 설치 확인

```bash
missing=()
for f in active-plan.sh resolve-range.sh run-codex-review.sh review-codex.sh clear-review.sh; do
  [ -x ".claude/hooks/$f" ] || missing+=("$f")
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "Error: 이 프로젝트에 push-review hooks 가 설치되지 않았습니다."
  echo "필요: ${missing[*]}"
  echo ""
  echo "설치 방법: 기존 프로젝트에서 .claude/hooks/*.sh 복사 + chmod +x"
  echo "  mkdir -p .claude/hooks"
  echo "  cp <기존프로젝트>/.claude/hooks/*.sh .claude/hooks/"
  echo "  chmod +x .claude/hooks/*.sh"
  exit 1
fi
```

## 1. 환경 변수 확보 + 사전 체크 (헬퍼 위임)

```bash
PLAN_DIR="$(bash .claude/hooks/active-plan.sh)"
PLAN_SLUG="$(basename "$PLAN_DIR")"

# RANGE / HEAD_SHA / SHA7 / UPSTREAM / TOTAL_COMMITS 결정
eval "$(bash .claude/hooks/resolve-range.sh)" || { echo "range 결정 실패"; exit 1; }

# $ARGUMENTS override (검증 포함)
if [ -n "$ARGUMENTS" ]; then
  if git rev-parse --verify --quiet "$ARGUMENTS" >/dev/null 2>&1; then
    UPSTREAM="$ARGUMENTS"
    RANGE="${ARGUMENTS}..HEAD"
    TOTAL_COMMITS="$(git rev-list --count "$RANGE" 2>/dev/null || echo 0)"
  else
    echo "Warning: '$ARGUMENTS' 가 유효한 ref 가 아님 — 기본 RANGE 사용 ($RANGE)"
  fi
fi

# 사전 체크: 변경 있는지 (RANGE 기반 — upstream 미설정도 처리)
if [ -z "$(git log "$RANGE" --oneline 2>/dev/null)" ]; then
  echo "push 할 변경 없음 (range: $RANGE) — /push-review 종료"
  exit 0
fi
git log "$RANGE" --oneline

# REVIEW_TS export — hook 과 동기화
export REVIEW_TS="$(date +%Y-%m-%dT%H%M)"
REVIEW_DIR="$PLAN_DIR/reviews/${REVIEW_TS}-${SHA7}"

# bg codex 시작 시각 캡처 — 이전 리뷰 잘못 통합 방지용
REVIEW_START_TS="$(date +%s)"

# perspectives 디렉토리만 미리 생성. REVIEW_DIR 자체는 hook 의 atomic mkdir 가 처리.
mkdir -p "$REVIEW_DIR/perspectives"

echo "PLAN_SLUG=$PLAN_SLUG"
echo "RANGE=$RANGE ($TOTAL_COMMITS commits)"
echo "HEAD_SHA=$HEAD_SHA"
echo "REVIEW_DIR=$REVIEW_DIR"
echo "REVIEW_TS=$REVIEW_TS"
echo "REVIEW_START_TS=$REVIEW_START_TS"
```

## 2. 두 리뷰 병렬 시작 (단일 메시지 6 tool_use)

**같은 메시지에서 동시 발송**:

### A. Codex 리뷰 (Bash, run_in_background=true)

```bash
REVIEW_TS="$REVIEW_TS" bash .claude/hooks/run-codex-review.sh
```

이 hook 은:
- `active-plan.sh` 로 같은 PLAN_DIR 자동 결정
- REVIEW_TS env 가 있으므로 `$REVIEW_DIR/codex.md` 에 결과 작성 (TS 동기화)
- exit 2 로 push 차단 의도 — 우리는 직접 push 안 하므로 의미 없음. **무시**.

bg 실행이라 메인은 즉시 다음 단계 진행.

### B. Local 5 perspective (parallel subagents)

/local-review 의 Agent 1~5 와 동일.

각 Agent prompt 에 PLAN_SLUG / RANGE / HEAD_SHA / REVIEW_DIR 명시 포함.
각 Agent 출력: `<REVIEW_DIR>/perspectives/<perspective>.md`

## 3. 양쪽 완료 대기

- Local 5: foreground 라 자동 도착
- Codex: bg → REVIEW_DIR/codex.md 출현 폴링 (REVIEW_START_TS 보다 새 것)

```bash
CODEX_FILE=""
for try in $(seq 1 24); do  # 최대 ~2분 대기 (5초 × 24)
  if [ -f "$REVIEW_DIR/codex.md" ]; then
    # mtime 이 시작 이후인지 확인 (이전 리뷰 잘못 잡지 않도록)
    ftime=$(stat -c %Y "$REVIEW_DIR/codex.md" 2>/dev/null || stat -f %m "$REVIEW_DIR/codex.md" 2>/dev/null || echo 0)
    if [ "$ftime" -ge "$REVIEW_START_TS" ]; then
      CODEX_FILE="$REVIEW_DIR/codex.md"
      break
    fi
  fi
  sleep 5
done

if [ -z "$CODEX_FILE" ]; then
  echo "[push-review] codex 결과 미도착 (timeout) — local 만으로 진행"
fi
```

## 4. Synthesis subagent (codex + local 통합)

별도 subagent 발송:

- subagent_type: general-purpose
- description: "codex+local 통합"
- prompt:
  ```
  다음 입력 통합:
  - codex.md: <CODEX_FILE> (없으면 codex 실패로 처리, local 만 통합)
  - perspectives: <REVIEW_DIR>/perspectives/*.md (5개, 일부 없을 수 있음)
  
  통합 규칙:
  1. codex 항목 파싱: `- [SEVERITY] description (file:line)` 형식
  2. perspective 파일들 파싱
  3. 같은 (파일, 라인, 종류) 항목 dedupe
     - codex+local 둘 다 → [BOTH] (신뢰도↑)
     - codex 만 → [CODEX]
     - local 만 → [LOCAL]
     - local 안 여러 perspective → 합쳐 표시 ([Security][Correctness])
  4. 심각도 max
  5. 정렬: CRITICAL > HIGH > MEDIUM > LOW
  6. 누락 입력 (codex 부재 / perspective 부재) 명시
  
  출력: <REVIEW_DIR>/combined.md
  
  Frontmatter:
  ---
  type: combined-review
  plan: <PLAN_SLUG>
  range: <RANGE>
  head_sha: <HEAD_SHA>
  status: pending
  created: <ISO>
  caller: claude_code
  codex_findings: <n>          # codex 부재 시 0
  local_findings: <n>
  shared: <n>                   # BOTH
  unique_codex: <n>
  unique_local: <n>
  recommendation: PROCEED | FIX_REQUIRED | REVIEW_NEEDED
  ---
  
  본문 형식: 직전 self-test 의 combined.md 와 동일 구조
  (CRITICAL/HIGH/MEDIUM/LOW + 신뢰도 분석 + 핵심 패턴 + 권고).
  
  권고 기준:
  - CRITICAL ≥ 1 또는 HIGH ≥ 1 → FIX_REQUIRED
  - MEDIUM ≥ 5 → REVIEW_NEEDED
  - 그 외 → PROCEED
  
  메인 반환 (간결!): combined.md 경로 + 카운트 + recommendation + 최고위험 1~2.
  ```

## 5. 사용자 보고 + 결정 안내 (자동 push 없음)

Synthesis 반환을 받아 사용자에게:

```
[Push Review Result]
Plan:           <PLAN_SLUG>
Range:          <RANGE>
Findings:       CRITICAL=n / HIGH=n / MEDIUM=n / LOW=n
                BOTH=n / CODEX-only=n / LOCAL-only=n
Recommendation: <PROCEED|FIX_REQUIRED|REVIEW_NEEDED>
Report:         <REVIEW_DIR>/combined.md
Top issues:
  1. [BOTH] Security HIGH at api.py:42 — SQL injection
  2. [LOCAL] Tests HIGH at svc.py — no test for new branch
```

분기:

- **`FIX_REQUIRED`**:
  ```
  CRITICAL/HIGH 발견. 위 항목 수정 후 재커밋, /push-review 재실행 권장.
  자동 수정 원하시면 알려주세요.
  ```
  
- **`REVIEW_NEEDED`**:
  ```
  MEDIUM 다수. combined.md 직접 검토 후 결정 권장.
  진행해도 무방하면:
    bash .claude/hooks/clear-review.sh <REVIEW_DIR>/combined.md
    git push
  ```

- **`PROCEED`**:
  ```
  리뷰 통과. push 진행 가능. 명령:
    bash .claude/hooks/clear-review.sh <REVIEW_DIR>/combined.md
    git push
  hook 이 cleared 감지하여 통과합니다.
  ```

**자동 push 안 함** — 사용자가 직접 위 명령 실행.
