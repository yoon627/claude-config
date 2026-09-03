---
title: wiki-session-ingest — 2026-09-02 세션 확정 사실 3건 + e-merge-mode 결정 wiki 적립
status: done
started: 2026-09-03
updated: 2026-09-03
---

# Goal
`/wiki ingest`: UserPromptSubmit 알림 턴 발동(entity), worktree 격리 Bash 가드 관찰(entity), `/e` 머지 모드 설계(decision)를 페이지로 적립하고 workflow-failures(rtk fixed·라우터 fixed·codex 정본 거부 proposed)·headroom(삭제된 memory 참조) 를 갱신, index/log 동기화.

# Progress
- 2026-09-03: 페이지 3 신규·2 갱신, index 3 등재, log append. `check_links.py` 위반 1(기존 orphan `lesson-fix-scoped-to-one-repo`, 범위 밖). 시크릿 스캔 0. 커밋 `18e1fe7` → `/e merge` PR #150.

# Next
- 없음 (PR #150 머지 시 완료).

# Decisions
- wiki 페이지는 tracked 라 main 직접 편집 대신 worktree 브랜치에서 ingest 하고 `/e merge` 로 닫는다 (이유: §8 비trivial 은 worktree; guard-worktree-edit 는 auto 모드에서 hard gate 가 아니라 규약만 남음).
- index.md 의 `headroom` 줄은 건드리지 않는다 (이유: 로컬 main 의 미push 커밋 `01c42c5` 가 그 줄을 바꾸므로 인접 편집이 충돌을 만든다 — 신규 entity 는 `claude-code-subagent-config` 앞에 삽입).

# Key Files
- `wiki/pages/entity/claude-code-hook-notification-turns.md` · `wiki/pages/entity/worktree-isolation-bash-guard.md` · `wiki/pages/decision/e-merge-mode.md` — 신규
- `wiki/pages/decision/workflow-failures.md` · `wiki/pages/entity/headroom.md` · `wiki/index.md` · `wiki/log.md` — 갱신

# Blockers
(없음)

# Acceptance
- [x] 신규 3 페이지가 frontmatter·outbound 링크 ≥2·sources 를 갖춤 — 검증: `check_links.py` 신규 페이지 위반 0.
- [x] index/log 동기화 — 검증: index 3줄 등재, log 헤더 `[2026-09-03] ingest`.
- [x] 시크릿 없음 — 검증: 신규 페이지 grep 0.

# Deferred
- `lesson-fix-scoped-to-one-repo` orphan(08-31 ingest 부터) — inbound 링크 1개 필요. 심각도 minor.
