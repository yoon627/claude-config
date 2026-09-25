---
title: e-merge-unfolded-commits — /e merge 가 push 전에 fixup!·wip: 등 정리 안 된 커밋을 검사
status: in_progress
started: 2026-09-25
updated: 2026-09-25
intent: plans/2026-09-25-unit-commit-followups/intent.md
---

# Goal

`/e merge` 가 push(M3) 전에 `origin/<default>..HEAD` 에서 `fixup!`·`squash!`·`amend!`·`wip:` 커밋을 찾아, commit-check 로 정리(승인 후)하거나 중단·보고한다. `skills/e/SKILL.md` 의 WIP 정리 안내를 commit-check 로 바꾸고, `docs/worktree-lifecycle.md` §E 시나리오 표에 해당 행을 더한다.

# Intent

→ `plans/2026-09-25-unit-commit-followups/intent.md` (Problem·Proposed outcome·공통 Constraints·Out of scope·Open questions 는 거기).

델타 없음 — 묶음의 첫 후속 plan 이고 범위가 intent 의 Proposed outcome 과 같다.

# Progress

- 2026-09-25: 전체 감사 후 origin/commit-split 을 닫으면서 살릴 부분으로 생성(사용자 선택 "close + 살릴 것만 새 plan"). 착수 전.

# Next

`/wt e-merge-unfolded-commits` 로 착수 → dlc(규모 판정부터). 착수 시 intent 의 Open question(자동 제안 vs 중단·보고)을 먼저 사용자에게 확인한다.

# Decisions

- **초안 출처**: 로컬 태그 `archive/commit-split`(51d55d9, 원격 브랜치는 2026-09-25 삭제)의 `skills/e/SKILL.md` M3·M4 문구와 `docs/worktree-lifecycle.md` §E 2행을 참고 초안으로 쓴다. 단 `/cs` 호출 자리는 commit-check 로 바꾸고, 무승인 자동 재구성은 가져오지 않는다(intent Constraints).
- **검사 대상**: 제목 접두 `fixup! `·`squash! `·`amend! `·`wip:`. `fixup!` 계열 대상 매칭은 commit-check `collect` 의 `fixup_of` 를 재사용한다(git autosquash 규칙과 대조 완료, wiki `git-autosquash-target-selection`).
- 원 결함 기록: `plans/2026-09-24-dlc-unit-commits/dlc-unit-commits-plan.md` # Deferred 첫 줄.

# Key Files

- `skills/e/SKILL.md` — M1~M3(검사 위치), `:34` `# Next` 의 "WIP 이어서/squash", `:104` WIP 커밋 본문의 "squash/amend 대상"
- `docs/worktree-lifecycle.md` §E — 시나리오 표
- `skills/commit-check/SKILL.md`, `skills/commit-check/commit_units.py` — 호출 대상(`collect`·`apply`)

# Blockers

없음.
