---
description: 변경사항을 5개 관점으로 병렬 리뷰. active plan 의 reviews/ 에 저장. 메인 컨텍스트 보호.
argument-hint: [base-ref=upstream]
---

# Local Multi-Perspective Review

push 범위 변경분을 5개 관점에서 **병렬 subagent** 로 검토하고 통합 리포트 작성.

## 핵심 원칙 (메인 컨텍스트 보호)

- 각 perspective subagent 는 결과를 **파일에 저장**. 메인엔 `(파일경로, 항목수, 최고위험 1줄)` 만 반환.
- Synthesis 도 **별도 subagent**. 메인은 최종 통합본만 본다.
- 메인 컨텍스트에 raw perspective 출력 끌어오기 금지.

## 0. Hook 설치 확인

이 슬래시 명령은 프로젝트의 `.claude/hooks/` 헬퍼를 사용한다. 다음 파일이 없으면 안내 후 종료:

```bash
missing=()
for f in active-plan.sh resolve-range.sh; do
  [ -x ".claude/hooks/$f" ] || missing+=("$f")
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "Error: 이 프로젝트에 리뷰 hooks (active-plan.sh, resolve-range.sh) 가 설치되지 않았습니다."
  echo "필요: ${missing[*]}"
  echo ""
  echo "설치 방법: 기존 프로젝트에서 .claude/hooks/*.sh 복사 + chmod +x"
  echo "  mkdir -p .claude/hooks"
  echo "  cp <기존프로젝트>/.claude/hooks/*.sh .claude/hooks/"
  echo "  chmod +x .claude/hooks/*.sh"
  exit 1
fi
```

## 1. 환경 변수 확보 (헬퍼 위임)

```bash
PLAN_DIR="$(bash .claude/hooks/active-plan.sh)"
PLAN_SLUG="$(basename "$PLAN_DIR")"

# RANGE / HEAD_SHA / SHA7 / UPSTREAM / TOTAL_COMMITS 결정
eval "$(bash .claude/hooks/resolve-range.sh)" || { echo "range 결정 실패"; exit 1; }

# $ARGUMENTS 으로 base ref override (검증 포함)
if [ -n "$ARGUMENTS" ]; then
  if git rev-parse --verify --quiet "$ARGUMENTS" >/dev/null 2>&1; then
    UPSTREAM="$ARGUMENTS"
    RANGE="${ARGUMENTS}..HEAD"
    TOTAL_COMMITS="$(git rev-list --count "$RANGE" 2>/dev/null || echo 0)"
  else
    echo "Warning: '$ARGUMENTS' 가 유효한 ref 가 아님 — 기본 RANGE 사용 ($RANGE)"
  fi
fi

TS="$(date +%Y-%m-%dT%H%M)"
REVIEW_DIR="$PLAN_DIR/reviews/${TS}-${SHA7}"
mkdir -p "$REVIEW_DIR/perspectives"

echo "PLAN_SLUG=$PLAN_SLUG"
echo "RANGE=$RANGE ($TOTAL_COMMITS commits)"
echo "HEAD_SHA=$HEAD_SHA"
echo "REVIEW_DIR=$REVIEW_DIR"
```

## 2. 변경 범위 파악

```bash
git diff "$RANGE" --stat
git log "$RANGE" --oneline
```

50파일 초과면 사용자에게 진행 여부 확인 (큰 변경은 토큰 비용 ↑).

## 3. 5개 perspective subagent 병렬 spawn

**중요: 단일 메시지의 5개 병렬 tool_use 블록으로 발송. 순차 호출 금지.**

각 Agent 공통 (subagent_type: general-purpose):

- 변경 파일을 직접 Read 로 검토
- 출력 파일: `<REVIEW_DIR>/perspectives/<perspective>.md`
- 파일 frontmatter:
  ```yaml
  ---
  type: perspective-<name>
  plan: <PLAN_SLUG>
  range: <RANGE>
  head_sha: <HEAD_SHA>
  status: pending
  created: <ISO 8601>
  caller: claude_code
  ---
  ```
- 본문 항목 형식: `- (file:line) [CRITICAL|HIGH|MEDIUM|LOW] description. 권장 수정: ...`
- 발견 없으면 본문에 "특이사항 없음" 한 줄
- **메인에 반환 (간결!): 파일 경로 + 항목수 + 최고위험 1줄**

### Agent 1 — Security
변경 파일에서 점검:
- 인증/인가 우회 가능성 (권한 escalation, 누락된 체크)
- 입력 검증 누락: SQLi, XSS, command injection, path traversal, deserialization, SSRF
- 비밀값/credentials/API 키 하드코딩
- 로깅에 민감정보 누출 (PII, token, password, session)
- 새 의존성의 알려진 CVE
- 암호학 약점 (MD5, ECB, weak random, hardcoded keys)

### Agent 2 — Correctness
- 엣지 케이스 (null/empty/boundary, 음수, overflow, unicode)
- off-by-one, race condition, 비동기 처리 오류
- 에러 처리 누락, exception 삼킴
- 가정-실제 데이터 흐름 불일치
- 락/트랜잭션 경계 오류
- 자원 누수 (file/socket/connection 미닫힘)

### Agent 3 — Tests
- 새 함수/분기에 단위 테스트 추가됐는지
- 기존 테스트가 변경을 커버하는지
- 통합/회귀 테스트 필요성
- CLAUDE.md TDD 원칙 준수 (로직 변경엔 테스트 필수, 예외 사유 명시)
- 테스트 자체의 결정성/품질
- 테스트 누락이 합리적인 예외 (UI/외부 인프라/포매팅) 면 명시 후 LOW 처리

### Agent 4 — Impact
- 변경된 함수/API/스키마의 호출자 (Grep 으로 추적, 단순 추측 금지)
- Public API breaking change
- DB 스키마 마이그레이션 필요성
- 배포 순서 / 롤백 가능성
- 다운타임 영향
- 환경변수/설정/CI 변경 영향

### Agent 5 — Maintainability
- 명명, 가독성, 적정 추상화 (과도/부족)
- 중복 / DRY 위반
- 주석 적정성 (CLAUDE.md: WHY 만, 자명한 WHAT 금지)
- 프로젝트 컨벤션 (uv, pytest, ruff 패턴)
- 함수/파일 길이

대부분 LOW. 명백히 가독성 해치는 것만 MEDIUM 이상.

## 4. Synthesis subagent 호출

5개 perspective 결과 도착 후, **6번째 subagent** 발송 (메인이 직접 통합 금지):

- subagent_type: general-purpose
- description: "5 perspective 통합"
- prompt:
  ```
  5개 파일을 read 후 통합:
  - <REVIEW_DIR>/perspectives/{security,correctness,tests,impact,maintainability}.md
  
  통합 규칙:
  1. 같은 (파일, 라인, 종류) 항목 dedupe — perspective 들 합쳐 표시
  2. 심각도가 다르면 max 선택
  3. 정렬: CRITICAL > HIGH > MEDIUM > LOW
  4. 일부 perspective 파일이 없으면 (subagent 실패) "실행 실패" 명시 후 진행
  
  출력: <REVIEW_DIR>/local.md
  
  Frontmatter:
  ---
  type: local-review
  plan: <PLAN_SLUG>
  range: <RANGE>
  head_sha: <HEAD_SHA>
  status: pending
  created: <ISO>
  caller: claude_code
  findings_total: <n>
  by_severity:
    critical: <n>
    high: <n>
    medium: <n>
    low: <n>
  ---
  
  본문:
  # Local Review — <TS>
  
  ## Range
  <range> (<n> commits)
  
  ## 🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM / ⚪ LOW
  - [perspective] (file:line) 설명. 수정: ...
  
  ## 📊 perspective 별 요약
  - Security: <n>건
  ... (5개)
  
  빈 카테고리는 "특이사항 없음".
  
  메인 반환 (간결!): local.md 경로 + by_severity 한 줄 + 최고위험 1~2.
  ```

## 5. 사용자 결과 보고

Synthesis 반환 받아 사용자에게 (메인이 본 유일한 상세 컨텍스트):

```
[Local Review Result]
Plan:    <PLAN_SLUG>
Range:   <RANGE>
Findings: CRITICAL=n / HIGH=n / MEDIUM=n / LOW=n
Report:  <REVIEW_DIR>/local.md
Top:
  1. [perspective] severity at file:line — headline
  2. ...
```

다음 단계 안내:
- CRITICAL/HIGH 있음: "수정 권장. local.md 확인 후 자동 수정 원하면 알려달라"
- 모두 MEDIUM/LOW: "참고용. 진행 가능"

상세는 사용자 요청 시 local.md 직접 read. **메인 컨텍스트에 raw 항목 끌어오기 금지.**
