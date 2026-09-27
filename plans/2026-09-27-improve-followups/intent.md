---
title: improve-followups — /improve deep(2026-09-27)이 찾은 하니스 결함·비용을 주인 있게 추적
status: open
started: 2026-09-27
updated: 2026-09-27
---

# Problem

`/improve deep`(2026-09-27, plan `plans/2026-09-27-native-overlap-recheck/native-overlap-recheck-plan.md`)이 두 감사 묶음(`plans/2026-09-25-repo-audit-followups/intent.md`) 밖의 새 개선 3개를 찾았다. 사용자가 셋 다 작업 단위로 올리기로 했다(2026-09-27). 감사 묶음의 Out of scope 가 "감사에서 나오지 않은 새 개선은 별도 요청"이라 거기 넣지 않고 이 묶음에서 추적한다.

# Proposed outcome

각 단위가 자기 plan 으로 착수·머지된다. 근거와 수치는 공용 wiki `workflow-failures`·`native-overlap-ledger`·`claude-code-hook-notification-turns` 에 있다.

# Constraints

- hook·guard 는 운영 자산이라 `/wt` → dlc 로 고치고, 고치기 전에 현재 버전에서 재현·실측한다(근거 관측은 2.1.281 런타임·2.1.283 설치 시점).
- fixture 는 실물에서 뜬다 — hook 입력은 transcript 가 아니라 실제 hook stdin 을 캡처해 만든다.

# Out of scope

- 감사 묶음의 단위(ledger-bash-edits 등) — 그쪽에서 추적한다. 순서 의존만 아래 메모에 적는다.

# Open questions

- (열림) UserPromptSubmit hook 의 `prompt` 필드가 transcript 의 user 턴 텍스트와 같은가(평문 접두어 포함 여부) — router-agent-message 가 hook stdin 캡처로 답한다.

# Plans

- `plans/2026-09-27-router-agent-message/router-agent-message-plan.md` — `scripts/dlc-task-router.js` 가 subagent 보고(hand-back) 턴을 사용자 턴으로 보고 라우팅 힌트를 오발동하고 장부를 리셋한다(workflow-failures 의 라우터 알림 턴 행 — 2026-09-15 부터 auto mode 14개 세션에서 130건). 이 턴은 v2.1.271 의 auto mode 전용 hand-back 호출에서 생겼고, transcript 에서는 `Another Claude session sent a message:` + 개행 + `<agent-message from="…">` 형태다(`<system-reminder>` 래퍼 없음). 태그만 걷어내면 평문 접두어가 남아 리셋이 계속될 수 있다 ⚠️ — 텍스트 제거 대신 턴의 출처를 판별하는 방식도 후보. 재현 테스트 먼저, small 예상. 감사 묶음의 ledger-bash-edits 가 이 단위 뒤에 온다.
- claude-md-dedupe (미착수) — 이 repo 의 worktree 세션에 `CLAUDE.md`(42KB)가 전역 사본(`~/.claude/CLAUDE.md`)과 worktree 사본으로 두 번 주입된다. 수단 후보 `claudeMdExcludes`(절대경로 glob, 계층 간 배열 병합 — 공식 memory 문서). 함정: user 계층에 일반 패턴(`**/worktrees/*/CLAUDE.md` 꼴)을 넣으면 다른 repo worktree 의 `CLAUDE.md` 도 빠지고(이 repo 의 worktree 절대경로로 고정한 glob 이면 안 걸린다), user 사본 경로를 빼면 main 세션(두 경로가 같다)에서 둘 다 빠진다 → 이 repo 에만 걸리는 계층·패턴을 정하고 headless 세션으로 전후를 실측(2026-09-25 AGENTS.md 제외 때와 같은 방식). branch 에서 CLAUDE.md 를 고칠 때 세션이 어느 사본을 보는지도 결정 사항.
- guard-deny-removal (미착수) — `scripts/guard-worktree-edit.js` 의 worktree 밖 편집 `deny` 분기 제거(`native-overlap-ledger` 1b `retire`, 2026-08-12 판정 뒤 미이행). **착수 조건**: 대장 1b 의 2026-08-12 관측표를 현재 버전에서 다시 실측한다(그 뒤 v2.1.251·257·259·274 에서 네이티브 격리 경계가, v2.1.283 에서 auto-memory 쓰기 판정이 바뀌었다). 같은 실측으로 대장 1b 콜아웃의 worktree 세션 memory 쓰기 막힘도 확인한다. 함께 사라지는 것(`guard-worktree-deny` 신호, <2.1.222 보호, 테스트의 ② 케이스)은 대장 1b 절에 있다. 기능 ①(main 편집 ask)은 남긴다.
