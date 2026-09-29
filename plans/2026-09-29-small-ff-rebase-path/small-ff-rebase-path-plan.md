---
title: small-ff-rebase-path — small 작업이 ff 불가일 때 갈 경로를 CLAUDE.md §8 에 둔다 (#191)
status: in_progress
started: 2026-09-29
updated: 2026-09-29
---

# Goal

CLAUDE.md §8 의 trivial·small 종결 경로에서 ff 가 불가능할 때(그 사이 default 가 진행) 갈 경로를 정한다. 지금은 `/e merge` 로 가라고만 해서, plan 이 없는 small 작업은 `/e merge` M1 게이트에 걸려 규약대로 갈 길이 없다.

# Intent

- Problem: 이슈 #191. 2026-09-28 한 세션에서 두 번 재현 — wiki 적립(plan 없음)과 퀴즈 옵션 제거가 ff 불가였다. 첫 번째는 사용자 승인 뒤 rebase→ff, 두 번째는 `/e merge` 를 쓰려고 plan 을 따로 만들었다.
- Constraints: 운영 자산 변경 — 사용자 승인(2026-09-29 "다음 작업: #191"). push·force push 는 여전히 요청 시만. rebase 는 미게시 브랜치만(§8 의 "게시된 커밋은 고치지 않는다"와 같은 경계).
- Out of scope: `/e merge` M1 이 plan 없는 small 을 받게 하는 안(이슈의 대안) — M4 plan done·intent 판정 전체에 예외가 필요해 변경 범위가 크다(기각, Decisions).

# Acceptance

1. CLAUDE.md §8 trivial·small bullet: ff 불가 → 미게시면 worktree 에서 `git rebase <default>` → 검증 재실행 → `--ff-only`, 충돌(`--abort`)·게시됨·medium 이상이면 `/e merge`, plan 없는 small 이면 plan 먼저. 검증: 해당 줄 읽기.
2. `skills/dlc/SKILL.md` 정리 판정의 같은 서술이 §8 과 모순되지 않는다. 검증: grep `ff-only` 전수 — 다른 곳(post-checkout·SessionStart·`/e` 8단계 pull)은 main 최신화라 무관함을 확인.
3. `bash scripts/verify.sh` 가 이 변경으로 새 실패를 내지 않는다(Windows: `ALL PASS (skip: …)`), PR CI 통과.

# Progress

- 2026-09-29: 착수. CLAUDE.md:140, dlc:162 수정. README:242 요약은 그대로 참이라 유지.
- 2026-09-29: `ff-only` 전수 grep — 나머지(post-checkout·SessionStart·`/e` 8단계·README 수동 복구)는 main 최신화 서술이라 무관. Windows `verify.sh` rc 0 `ALL PASS (skip: install-hooks.test.js(case) record-verified.test.sh)`. plan-reviewer·code-reviewer 생략 — 규약 한 문장 확장이고 코드 변경 없음.

# Next

verify → 커밋 → `/e merge`.

# Decisions

- ff 불가면 미게시 브랜치를 default 위로 rebase 한다. 이유: 게시 전이라 이력 재작성이 누구에게도 보이지 않고, PR 왕복 없이 small 의 "로컬 ff" 원칙을 지킨다. rebase 뒤 검증을 다시 돌린다 — 새 base 위에서 깨질 수 있다.
- 기각: `/e merge` M1 이 plan 없는 small 을 받게 하는 안 — M4(plan done 커밋)·묶음 intent 판정·복구 규칙 전체에 plan 없음 예외가 필요하다(이슈 #191 본문).
- rebase 충돌·게시된 브랜치처럼 PR 로 가야 하는 경우, plan 이 없는 small 은 plan 을 먼저 만든다 — 이슈 제안만으로는 이 경우 여전히 `/e merge` M1 에 걸린다(2026-09-28 퀴즈 제거 때 실제로 이렇게 했다).

# Key Files

- `CLAUDE.md` — §8 trivial·small 종결 bullet
- `skills/dlc/SKILL.md` — 정리 판정의 같은 서술

# Blockers
