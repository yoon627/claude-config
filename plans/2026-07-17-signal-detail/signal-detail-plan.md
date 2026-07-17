---
title: signal-detail — dlc telemetry 신호에 trigger 파일 detail 기록 + doc-drift FP 추적
status: in_progress
started: 2026-07-17
updated: 2026-07-17
---

# Goal
/improve 백로그 분석에서 나온 개선 후보 1+2 구현: (1) dlc telemetry 신호(early-stop-verify·doc-drift-readme·doc-drift-index)가 `detail:null` 이라 오탐 vs 실제 갭 구분 불가 → **trigger 파일을 detail 로 기록**. (2) doc-drift-readme 내부-dedup 오탐 class 를 workflow-failures.md 에 기록.

# Progress
- 2026-07-17: Explore 완료. emit() 은 이미 detail 필드 지원 — 호출부만 채우면 됨. TDD Red→구현→Green(33·32·20). 커밋 07d2745. code-review(Claude APPROVE·codex 문제 없음) Critical/Major 0, Minor 2 처분(wontfix·defer). README 동기화. **acceptance 전 항목 증거 충족.**

# Next
- push → PR → merge → 정리 (사용자 확인 후)

# Decisions
- **emit detail 인프라 재사용**: emit() 의 `detail: c.detail ? tildeify(c.detail) : null` 이미 존재 → 새 스키마 안 만들고 호출부만 채운다.
- **trigger 파일 추적**: doc-drift 는 classify 의 rel(repo-relative, PII 없음) 사용. changed 는 basename(간결·경로유출 회피).
- **detail 시맨틱**: 마지막 trigger 파일(dirty 순서 반영 — target 오면 null 리셋). /improve 가 "readmeTrigger=CLAUDE.md 내부dedup" 같은 FP 패턴 식별 가능.
- 후보 3(07-16 스파이크 근인)은 detail 쌓인 뒤 다음 /improve 로 — 이 PR 범위 밖.

# Key Files
- `scripts/dlc-ledger.js` — DEFAULT 스키마(readmeTrigger/indexTrigger/changedTrigger 추가)
- `scripts/dlc-doc-drift.js` — applyChange 에서 trigger rel 기록
- `scripts/dlc-evidence-ledger.js` — changed 시 changedTrigger 기록
- `scripts/dlc-early-stop.js` — emit 에 detail 전달
- `scripts/{dlc-doc-drift,dlc-evidence-ledger}.test.js` — TDD
- `wiki/pages/decision/workflow-failures.md` — 후보 2 기록

# Blockers
(없음)

# Acceptance
- [x] applyChange(readme-trigger) → data.readmeTrigger === rel, target → null (dlc-doc-drift.test.js +4, 33 pass)
- [x] evidence-ledger changed 파일 → data.changedTrigger === basename (dlc-evidence-ledger.test.js +1, 32 pass)
- [x] early-stop emit 이 detail 전달 (코드 확인 + emit→jsonl round-trip 스모크: doc-drift→CLAUDE.md·early-stop→plan-lint.js)
- [x] DEFAULT 새 필드 → read/reset 회귀 없음 (read `{...DEFAULT,...json}` 구 파일 null 보강 — 양 리뷰어 확인, 기존 테스트 green 유지)
- [x] 전 테스트 3종 green(33·32·20) + node --check 5 스크립트
- [x] workflow-failures.md 에 doc-drift FP class row 추가 + check_links clean
- [x] README 스키마+payload 동기화

# Review Disposition
- code-reviewer(Claude) APPROVE·codex 문제 없음 — Critical/Major 0.
- Minor `changedTrigger` root-gate 없음 → **wontfix**(의도된 설계: basename-only·cwd 이미 기록·타repo 마진 정보 미미, root-gate 시 temp-repo 테스트 파괴·doc-drift 커플링).
- Minor emit-detail seam 미검증(dlc-early-stop.test.js 부재는 pre-existing) → **defer**(구성요소 개별 커버 + 통합 스모크 통과, early-stop 테스트 하네스 신설은 범위 밖).
