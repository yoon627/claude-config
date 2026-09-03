---
title: agent-hook-if-lesson — hook `if` best-effort 교훈 wiki 적립 + 격리 가드 페이지 구분
status: done
started: 2026-09-03
updated: 2026-09-03
---

# Goal

coin-trading-bot PR #165 에서 확정한 사실(agent hook `if` 오탐 37건이 code-reviewer codex 병행을 막음, `shell: powershell` 민감파일 hook 의 macOS fail-open)을 wiki lesson 으로 적립하고, `worktree-isolation-bash-guard` 에 두 기전의 구분을 추가한다. memory feedback 줄은 main 세션에서 별도 기록(worktree 에선 불가).

# Progress

- 2026-09-03: lesson 페이지 신규, 가드 페이지 구분 절 + open callout, workflow-failures fixed 행, index·log 동기화. check_links 위반은 baseline 과 동일 1건(orphan `lesson-fix-scoped-to-one-repo`, main 에서 재현) — 이번 변경과 무관.

# Next

- PR 머지로 종료.

# Decisions

- 가드 페이지의 `codex exec --skip-git-repo-check` 행은 삭제하지 않고 `[!open]` 으로 둔다 — ~/.claude 세션 실측이라 coin-trading-bot 트랜스크립트만으로 반증 못 함.

# Key Files

- `wiki/pages/decision/lesson-agent-hook-if-best-effort.md` — 신규 lesson.
- `wiki/pages/entity/worktree-isolation-bash-guard.md` — 혼동 구분 절.
- `wiki/pages/decision/workflow-failures.md`, `wiki/index.md`, `wiki/log.md` — 동기화.

# Blockers

# Deferred

- wiki orphan `lesson-fix-scoped-to-one-repo`(main 에서도 위반, 낮음) — 어느 페이지에서든 링크 1개 추가.
