---
title: read-points — 작업 뒤 꼭 볼 코드만 골라 VS Code CodeTour 로 따라가며 확인하게 한다
status: in_progress
started: 2026-10-14
updated: 2026-10-15
---

# Goal
작업이 끝나면 사용자가 모든 코드를 읽지 않고, 구조·핵심 로직처럼 사람이 봐야 할 코드만 VS Code(원격 SSH)의 CodeTour 로 따라가며 확인한다. main agent 가 꼭 볼 곳을 골라 투어를 만들고, code-reviewer 가 그 투어를 검사한다.

# Intent
- Problem: 지금 보고의 "읽을 곳"은 위치 목록만 채팅에 나열한다. 바뀐 코드 중 무엇을 꼭 읽어야 하는지 고르지 않고, VS Code 로 바로 이어지지도 않는다.
- Constraints(사용자 결정 2026-10-14~15): 중요한 코드만 · PR 이 아니라 작업 뒤 본인 확인용 · VS Code 원격 SSH + CodeTour · main 이 고르고 code-reviewer 가 검사 · 상한 없음 · 채팅은 짧게 · CLAUDE.md 는 그대로.
- Out of scope: 안 고친 리뷰 지적·미룬 일까지 보고에 모으는 것(처음 설계안 — 이번엔 안 함) · PR·GitHub 연동 · 훅 추가.
- Open questions: 없음.
- 분할: 없음 — 투어 스크립트·main 선별 규칙·리뷰어 검사는 하나만 있으면 쓸모가 없다.

# Progress
- 2026-10-14: 착수(worktree `read-points`, base `origin/main@2fc4b8f`). 사용자와 범위를 세 번 좁혀 확정. CodeTour 스키마·`ref` 재생 동작 확인.
- 2026-10-15: 역할 분담 변경(main 작성·reviewer 검사), plan 을 결정과 이유 위주로 줄임.

# Next
- 계획 리뷰(plan-reviewer·architecture-reviewer) → 지적 반영 → 테스트 먼저 → 구현 → 실측.

# Decisions
- wiki 결정 조회: ops-doc-slimming(상시 문서 증가 최소)·remove-quiz-option(opt-in 금지)·dual-review(작성자와 검사자 분리)·workflow-failures(훅 오탐 — 훅 안 더함)를 모두 따른다.
- **세부의 정본은 코드다** — 판정 범주·투어 초안 형식·검증 규칙은 `scripts/review-tour.js` 머리 주석, 투어 검사 관점은 `agents/code-reviewer.md` 에만 적는다. plan 과 SKILL 은 그곳을 가리킨다(이유: 세부를 여러 곳에 쓰면 구현 중 어긋난다 — 사용자 지적 2026-10-15).
- 역할: 처음엔 code-reviewer 가 고르게 했으나, 사용자 안대로 main 이 고른다(의도를 알아 질문을 정확히 씀). 자기 채점 위험은 reviewer 의 독립 검사로 막는다.
- 판정 기준(요지): 꼭 읽기 = 구조·핵심 로직·경계·AI 가 혼자 정한 것. 건너뛰기 = 테스트·이름 변경·포맷·문서·생성 파일. 경로가 아니라 코드 내용으로 판단.
- 흐름: 구현 후 main 이 투어 초안 작성 → code-reviewer 가 코드와 함께 검사(빠진 곳·잘못 건너뛴 곳·위치·질문) → 커밋 후 스크립트가 검증해 `<main checkout>/.tours/` 에 투어 기록(최종 커밋에 묶음, git 에는 안 잡히게) → 채팅엔 투어 이름·단계 제목만.
- 기각: 채팅에 diff 조각 · PR·GitHub 링크 · `vscode://` 링크(원격 줄 이동 미확인) · Markdown 링크 파일 · 별도 판정 agent · 상위 N 제한 · 투어를 worktree 안에 두기(머지 후 정리 때 지워짐).
- ⚠️ 잘못 "건너뛰기"로 매기면 사람이 그 코드를 안 본다 — reviewer 가 따로 보고, 실측으로 확인한다.
- 커밋 단위: 1) 스크립트+테스트 2) code-reviewer·dlc SKILL·README.

# Acceptance
1. `scripts/review-tour.js` 동작(투어 쓰기·잘못된 줄이면 안 씀·0곳이면 안 씀·최신 5개 유지·git 무시 처리) — `node scripts/review-tour.test.js` 전부 통과.
2. 만든 투어가 CodeTour 스키마 필수 항목을 지킨다 — 같은 테스트에서 대조.
3. code-reviewer 에 투어 검사 관점과 출력 절 — `git grep -n '투어 검사' agents/code-reviewer.md`.
4. dlc SKILL 에 main 선별·리뷰어 전달·투어 쓰기·새 "읽을 곳" — diff 대조.
5. README 동기화 — `git grep -n -e review-tour -e CodeTour README.md`.
6. 실측: 머지된 diff 2개로 초안 → 리뷰어 검사 → 투어 생성까지 돌려 분류가 맞는지 본다 — 결과를 Progress 에.
7. 사용자가 VS Code 에서 이 작업의 투어를 재생해 줄 이동을 확인한다.
8. `bash scripts/verify.sh changed` → `ALL PASS`, plan-lint 통과.

# Key Files
- scripts/review-tour.js — 신규, 세부 규칙의 정본
- scripts/review-tour.test.js — 신규
- agents/code-reviewer.md — 투어 검사
- skills/dlc/SKILL.md — 흐름·"읽을 곳"
- README.md

# Deferred
- 안 고친 리뷰 지적·확인 못 한 검증·미룬 일까지 보고에 모으는 안(처음 workflow 설계, scratchpad `read-points-design.md`) — 필요해지면 별도 작업.
- 공용 wiki 갱신(main 세션): dlc 의 "읽을 곳" 서술, CodeTour 사용 사실.

# Blockers
