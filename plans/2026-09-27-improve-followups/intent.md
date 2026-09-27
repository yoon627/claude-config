---
title: improve-followups — /improve deep(2026-09-27)이 찾은 하니스 결함·비용을 주인 있게 추적
status: closed
started: 2026-09-27
updated: 2026-09-28
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

- (해소) UserPromptSubmit hook 의 `prompt` 필드가 transcript 의 user 턴 텍스트와 같은가(평문 접두어 포함 여부) — stdin 캡처는 못 했지만, router-agent-message 머지 뒤 실제 hand-back 턴에서 앞머리 판별식이 맞아 라우팅·리셋이 건너뛰어졌다(plan Acceptance 6). 즉 hook 이 받는 `prompt` 도 걷어낸 뒤 접두어나 `<agent-message` 로 시작한다 ⚠️(건너뛴 경로는 기록이 없어 간접 증거).

# Plans

- `plans/2026-09-27-router-agent-message/router-agent-message-plan.md` — `scripts/dlc-task-router.js` 가 subagent 보고(hand-back) 턴을 사용자 턴으로 보고 라우팅 힌트를 오발동하고 장부를 리셋한다(workflow-failures 의 라우터 알림 턴 행 — 2026-09-15 부터 auto mode 14개 세션에서 130건). 이 턴은 v2.1.271 의 auto mode 전용 hand-back 호출에서 생겼고, transcript 에서는 `Another Claude session sent a message:` + 개행 + `<agent-message from="…">` 형태다(`<system-reminder>` 래퍼 없음). 태그만 걷어내면 평문 접두어가 남아 리셋이 계속될 수 있다 ⚠️ — 텍스트 제거 대신 턴의 출처를 판별하는 방식도 후보. 재현 테스트 먼저, small 예상. 감사 묶음의 ledger-bash-edits 가 이 단위 뒤에 온다.
- `plans/2026-09-27-claude-md-dedupe/claude-md-dedupe-plan.md` — 이 repo 의 worktree 세션에 `CLAUDE.md`(42KB)가 전역 사본과 worktree 사본으로 두 번 주입되던 것(컨텍스트 ~18.5k 토큰, headless 실측)을 user `settings.json` `claudeMdExcludes` 의 `**/.claude/.claude/worktrees/*/CLAUDE.md`·`*/AGENTS.md`(CLAUDE.md 를 빼면 AGENTS.md 폴백이 켜짐)로 뺀다. worktree 세션은 main checkout 의 CLAUDE.md 로 돌고 branch 변경은 main 반영 뒤 새 세션부터 적용된다.
- `plans/2026-09-27-guard-deny-removal/guard-deny-removal-plan.md` — 원안은 `scripts/guard-worktree-edit.js` 의 worktree 밖 편집 `deny` 분기 제거(`native-overlap-ledger` 1b `retire`)였다. 착수 조건인 2.1.283 재실측에서 네이티브 격리가 EnterWorktree 세션은 덮지만 worktree 디렉토리에서 시작한 세션은 덮지 않음을 확인해, 제거 대신 **main checkout 의 추적 파일 편집과 새 not-ignored 파일 생성만 막게 좁히고**(관측 오탐 4건은 전부 gitignored 경로) 대장 1b 를 정정한다(사용자 결정). worktree 세션 memory 쓰기는 2.1.283 에서도 막힌다. 기능 ①(main 편집 ask)은 남긴다.
