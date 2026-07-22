---
title: hook-recall-lesson — 실수-로그 recall hook ① 구현
status: blocked
started: 2026-06-24
updated: 2026-06-24
---

# Goal
구현 작업 시작 시 관련 lesson/feedback 인덱스를 컨텍스트에 **능동 주입**하는 recall hook 을 `dlc-task-router.js` 확장으로 구현. CLAUDE.md §13(실수·교훈 로그)의 "재참고" 강제 경로 — MEMORY.md 인덱스 수동 주입의 약점(권고일 뿐)을 보완.

# Progress
- 2026-06-24: §13 규약·lesson·feedback 적립 완료(PR #65 + 메인 memory). hook 범위·강도 결정 확정. 구현은 PR #65 머지 후 별도 worktree·dlc 로.

# Next
1. PR #65 (https://github.com/yoon627/claude-config/pull/65) 머지 확인.
2. 별도 worktree(`/wt hook recall lesson` — slug 에 hook-recall 포함) → dlc 진입.
3. `scripts/dlc-task-router.js` 읽고 작업 분류 로직 파악 → 구현 작업 감지 분기에서 MEMORY.md 의 lesson/feedback 인덱스 줄(또는 wiki decision/lesson-* 제목)을 stdout 주입.

# Decisions
- **범위 = ① recall 먼저** (사용자 결정 2026-06-24). ② capture(종료 시 미적립 경고, dlc-early-stop 확장)는 보류.
- **강도 = 주입·경고** (fail-open·capped, 기존 dlc hook 4개와 일관). `exit 2` 하드블록은 휴리스틱 오탐 비용 커서 비채택.
- **위치 = `dlc-task-router.js` 확장** (신규 스크립트 아님). 단 확장 vs 신규는 라우터 내부 read 후 확정 — 추측 금지. router 가 이미 UserPromptSubmit 에서 작업 분류하므로 분기 추가가 자연스러움.
- 주입 소스: MEMORY.md 는 매 세션 이미 주입되므로 중복 우려 — 차별점은 "그 작업 시점 명령으로 등장". 구현 시 중복/노이즈 최소화(관련 lesson 만 선별) 설계 필요.

# Key Files
- `scripts/dlc-task-router.js` — UserPromptSubmit hook, 확장 대상.
- `scripts/dlc-early-stop.js` — ② capture 확장 시 대상(보류).
- `projects/.../memory/MEMORY.md` — lesson/feedback 인덱스 소스 (gitignored).
- `wiki/pages/decision/lesson-*.md` — lesson 상세.
- `CLAUDE.md` §13 — 규약 단일 소스(PR #65).

# Blockers
- PR #65 머지 대기 — 머지되면 §13 규약이 반영된 baseline 위에서 hook 작업(사용자 선택: 머지 후 착수).
