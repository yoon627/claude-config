---
title: unit-commit-followups — 단위 커밋·fixup 흐름에서 정리 안 된 커밋이 게시되지 않게
status: closed
started: 2026-09-25
updated: 2026-09-25
---

# Problem

dlc 목적 단위 커밋(2026-09-24, PR #172)은 후속 수정을 `fixup!` 으로 쌓고 마지막에 commit-check 가 합친다. `/e` 체크포인트는 `wip:` 커밋을 남긴다. commit-check 제안을 보류하거나 충돌이 나면 `fixup!`·`wip:` 커밋이 남고, 지금 `/e merge` 는 push 전에 이것을 확인하지 않아 그대로 게시될 수 있다. 한 번 push 되면 commit-check 범위(미게시 커밋) 밖이라 고칠 수 없다. `skills/e/SKILL.md` 는 여전히 WIP 정리를 "squash/amend" 로만 적어 commit-check 경로를 가리키지 않는다.

# Proposed outcome

push 하기 전에 정리 안 된 커밋(`fixup!`·`squash!`·`amend!`·`wip:`)을 발견하면 commit-check(승인 후 재구성)로 정리하거나, 중단하고 보고한다. WIP 정리 안내 문구는 commit-check 를 가리킨다.

# Constraints

- 커밋 재구성은 commit-check 한 도구로만 한다 — plumbing 재조립 + `update-ref` CAS, 사용자 index·작업트리를 건드리지 않는다(wiki `commit-restructure-plumbing-cas`). 재구성 전 사용자 승인(2026-09-24 사용자 결정, plans/2026-09-24-commit-check-skill).
- 이미 push 한 커밋은 고치지 않는다(CLAUDE.md §8, force-push 금지).
- 운영 자산 변경이라 착수는 `/wt` → dlc.

# Out of scope

- hunk 단위 분할. dlc-unit-commits 에서 기각한 안 D 이고, origin/commit-split 의 `/cs` 엔진(worktree reset 재구성·무승인 자동 호출)은 위 Constraints 와 충돌해 되살리지 않는다. 필요해지면 기각안 재개를 사용자가 먼저 결정한다.
- `/e` 체크포인트의 `wip:` 커밋 생성 방식 자체.

# Open questions

- (해소) 발견 시 기본 동작을 commit-check 자동 제안으로 할지, 중단·보고만 할지 — 2026-09-25 사용자 결정: commit-check 제안 → 승인(보류하면 중단). 게시분·로컬 ref 가 붙잡은 것은 진행 여부를 묻는다(`e-merge-unfolded-commits` plan).

# Plans

- `plans/2026-09-24-dlc-unit-commits/dlc-unit-commits-plan.md` — 목적 단위 중간 커밋·fixup·commit-check 합치기 도입(이 묶음의 출발점, Deferred 에서 후속이 나왔다)
- `plans/2026-09-25-e-merge-unfolded-commits/e-merge-unfolded-commits-plan.md` — `/e merge` push 전 정리 안 된 커밋 검사(`commit_units.py pending` + commit-check 제안) + e SKILL 문구
