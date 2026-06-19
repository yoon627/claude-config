---
name: audit
description: 운영 자산(skills·agents·CLAUDE.md·settings.json·MEMORY.md·README·wiki)의 정합성을 읽기전용으로 점검해 심각도와 함께 보고하는 오케스트레이션. 자산 *간* 참조 정합(settings↔scripts·MEMORY↔memory·문서↔agents·죽은 스크립트)을 기계 점검(audit.sh)으로, 문서 모순·중복·개선점을 의미 점검(LLM)으로 본다. 발견은 보고하고 수정은 제안만(운영 자산 자가수정 금지 §1 — 자동 수정 안 함). `/audit` 명시 호출 시 사용. 단순 질문·코드 변경에는 쓰지 않는다.
---

# audit — 운영 자산 정합성 점검 (읽기전용·보고·제안)

`/audit` 으로 `~/.claude` 운영 자산의 **자산 간 참조 정합**을 점검해 심각도와 함께 보고한다. **수정은 제안만** — 발견을 고치는 건 사용자 승인 후 별 작업(§1 운영 자산 자가수정 금지). c/e 처럼 메인이 직접 수행(subagent 위임 아님).

## 적용
- `/audit` 명시 호출 시. 자산 추가/리네임/삭제 후, 또는 정합성이 의심될 때.
- 단순 질문·탐색·코드 변경에는 쓰지 않는다.

## 역할 경계 (중복 회피 — 중요)
audit 은 **아무도 안 보는 자산 간 참조**만 본다. 다른 메커니즘과 겹치지 않는다:
- **README ↔ surface(scripts·agents·SKILL·settings·CLAUDE 섹션) drift** → `dlc-doc-drift` hook(세션 중 Stop 경고) 영역. audit 은 **안 본다**.
- **wiki 내부 무결성**(orphan·dead link·모순) → `/wiki lint` 영역. audit 은 index↔pages **개수만** 보고 lint 를 권장.
- audit 고유: settings↔scripts 실존·MEMORY↔memory 양방향·문서가 참조한 agent 실존·SKILL name·죽은 스크립트 후보 — hook/lint 가 안 보는 크로스참조.

## 동작 (3단계)

### 1. 기계 점검 — `audit.sh`
repo root 에서 `bash skills/audit/audit.sh` 를 **1회** 실행(개별 grep 왕복을 묶음, read-only). 출력은 심각도 prefix 라인:
- `[error]` — **실행경로 깨짐**: settings 가 참조한 hook script 부재, MEMORY 고아 인덱스(→파일 없음), CLAUDE.md 가 참조한 agent 부재, SKILL frontmatter name 누락.
- `[warn]` — 미등록·한쪽 누락: memory 파일이 인덱스에 없음, wiki 개수 불일치.
- `[info]` — 인벤토리·약참조(**단정 아님**): 어디서도 안 보이는 scripts 후보(죽은코드 *후보* — require 그래프·문서·CI·수동유틸 화이트리스트 통과분만, 수동 확인 권고).
- `[ok]` — 정합.

요약줄(`error=N warn=N`)로 집계. 점검 대상 디렉토리가 없으면(MEMORY 머신종속 경로 등) 그 점검만 skip 하고 명시.

### 2. 의미 점검 — LLM 판단 (audit.sh 가 못 잡는 것)
기계로 못 보는 것을 메인이 직접 점검:
- **문서 간 모순**: CLAUDE.md 와 SKILL.md 의 규칙 충돌(예: 같은 절차를 다르게 서술), README 설명과 실제 동작 불일치.
- **중복/과잉**: 같은 trigger 를 가진 skill, 역할이 겹치는 agent, 죽은 규칙(더는 유효하지 않은 CLAUDE.md 항목).
- **개선점**: 누락된 문서화, 일관성 깨진 네이밍·형식.
관련 파일을 read 해 근거로 판단한다(추측 금지 §1).

### 3. 보고 + 제안 (수정 안 함)
- **보고**: error/warn/info 를 분류해 요약. 각 발견 = `무엇이 · 어디서(파일) · 왜 문제`.
- **제안만**: 수정안을 제시하되 **자동 적용하지 않는다**(§1). 사용자가 승인하면 그 수정은 **별 작업(wt→dlc)** 으로 — 운영 자산 변경은 비trivial 이라 worktree 필수.
- error 0 이면 "정합" 보고. info 는 "수동 확인 권고"로 남긴다(단정·자동삭제 금지).

## 경계 (안 하는 것)
- **수정 안 함** — 점검·보고·제안까지. 운영 자산 자가수정 금지(§1). audit.sh 에 수정/파괴 명령 없음(read-only).
- **README↔surface drift·wiki 내부 무결성은 안 본다** — 각각 hook·`/wiki lint` 영역(위 역할 경계).
- **죽은 스크립트 단정·삭제 안 함** — info 후보로만(require 그래프 등 4축 통과분), 실제 판단은 사람.
- subagent 위임 아님 — 메인이 직접 실행·판단·보고.
