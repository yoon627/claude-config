---
name: improve
description: dlc 자기개선 loop 의 분석 축 — 운영 자산 정합성 기계 점검(구 /audit 승계)과 hook 이 자동 누적한 workflow 실패 신호(telemetry)·wiki workflow-failures·feedback memory 를 함께 읽어 개선 후보를 근거·빈도 기반으로 랭킹 제시하는 오케스트레이션. 발견은 보고·제안까지, 수정은 사용자 승인 후 wt→dlc(운영 자산 자가수정 금지 §1 — 자동 수정 안 함). `/improve` 명시 호출 시 사용. 단순 질문·코드 변경에는 쓰지 않는다.
---

# improve — 자기개선 loop 의 분석 축 (읽기전용·랭킹·제안)

`/improve` 로 ① 운영 자산 정합성(구 `/audit` 승계)과 ② hook 이 자동 누적한 신호(telemetry)를 함께 분석해 **개선 후보를 랭킹**으로 제시한다. loop 의 다른 축과의 관계: **수집**은 hook 이 자동(`scripts/dlc-signal.js` — early-stop·guard·doc-drift·router·plan 신호), **분석·제안**이 이 skill, **반영**은 사용자 승인 후 `wt→dlc` 별도 작업, **효과 확인**은 다음 `/improve` 의 신호 추이. c/e 처럼 메인이 직접 수행(subagent 위임 아님).

## 적용
- `/improve` 명시 호출 시. 자산 추가/리네임 후, workflow 마찰이 반복된다고 느낄 때, 개선 효과를 확인하고 싶을 때.
- 단순 질문·탐색·코드 변경에는 쓰지 않는다.

## 역할 경계 (중복 회피 — 중요)
- **README ↔ surface drift** → `dlc-doc-drift` hook(세션 중 Stop 경고) 영역. improve 는 **재판정하지 않고** hook 이 emit 한 `doc-drift-*` 신호를 **사후 집계**만 한다.
- **wiki 내부 무결성**(orphan·dead link·모순) → `/wiki lint` 영역. improve 는 index↔pages 개수만 보고 lint 를 권장.
- improve 고유: 자산 간 크로스참조(settings↔scripts·MEMORY↔memory·문서↔agents·죽은 스크립트 후보) + **신호·실패 이력의 종합 분석과 개선 후보 랭킹** — 다른 어떤 메커니즘도 안 하는 부분.

## 동작 (4단계)

### 1. 기계 점검 + 신호 집계 — `improve.sh`
repo root 에서 `bash skills/improve/improve.sh` 를 **1회** 실행(read-only). 출력:
- 점검 1~6(구 audit 승계): `[error]` 실행경로 깨짐(settings→scripts 부재, CLAUDE.md→agent 부재, SKILL name 누락) / `[warn]` 미등록·한쪽 누락(MEMORY 인덱스, wiki 개수) / `[info]` 죽은 스크립트 *후보*(단정 아님) / `[ok]`.
- 점검 7(신규): `~/.claude/telemetry/dlc-signals.jsonl` 집계 — kind 별 `sessions`(unique)·`raw`·기간. **failure 축**(early-stop-verify·doc-drift-*·guard-worktree-deny·main-edit-ask·plan-blocked)과 **activity 축**(router-*·review-disposition — 실패 아님, 활동량)을 분리 표시. 효과 판단은 sessions(unique) 우선 — raw 는 같은 세션 반복 발동에 지배될 수 있다.

### 2. 누적 이력 대조
- `wiki/pages/decision/workflow-failures.md` 추적 표(실패·횟수·상태) read — 신호와 대조해 **횟수 갱신이 누락된 실패**를 찾는다.
- `MEMORY.md` 인덱스(feedback 행동지시문) — 최근 작업에서 실제 반영됐는지, 죽은 규칙이 없는지.
- 현재/최근 plan 의 `# Workflow Findings`·`# Deferred` — plan 에만 있고 wiki 로 승격 안 된 반복 항목.

### 3. 의미 점검 — LLM 판단 (기계가 못 잡는 것)
- 문서 간 모순(CLAUDE.md ↔ SKILL.md 규칙 충돌), 같은 trigger 의 skill 중복, 죽은 규칙(더는 유효하지 않은 항목).
- 관련 파일을 read 해 근거로 판단(추측 금지 §1).

### 4. 개선 후보 랭킹 + 처분 제안 (수정 안 함)
- 각 후보 = `무엇이 문제 · 근거(신호 수치/파일:라인) · 제안 변경(어느 파일을 어떻게) · 예상 효과(어떤 신호가 줄어야 하나)`.
- 랭킹 기준: failure 신호 unique-session 빈도 × 심각도(실행경로 깨짐 > 반복 마찰 > 인벤토리) × 수정 비용(작을수록 위).
- **효과 확인**: 이전에 `fixed` 로 처리된 항목의 신호가 실제로 줄었는지 추이를 보고(안 줄었으면 재개선 후보로 복귀).
- **처분**: 사용자 승인 시 그 수정은 **별도 작업(wt→dlc)** — 운영 자산 변경은 비trivial 이라 worktree 필수. dlc 의 "같은 실패 2회+ 반복 시 해결 제안" 규칙(wiki workflow-failures)과 동일 경로로 합류. error 0 + 유의미 신호 없음이면 "개선 후보 없음" 보고.

## 경계 (안 하는 것)
- **수정 안 함** — 점검·집계·랭킹·제안까지. 운영 자산 자가수정 금지(§1). improve.sh 에 수정/파괴 명령 없음(read-only).
- **신호 재판정 안 함** — telemetry 는 hook 판정의 사후 집계. README drift·wiki 내부는 각각 hook·`/wiki lint` 영역.
- **죽은 스크립트 단정·삭제 안 함** — info 후보로만, 실제 판단은 사람.
- subagent 위임 아님 — 메인이 직접 실행·판단·보고.
