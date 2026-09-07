---
title: e-worktree-cleanup — /e 마무리 시 done+clean+pushed worktree 삭제 제안 추가
status: done
started: 2026-06-03
updated: 2026-06-03
---

# Goal
`/e`(plan-end) 스킬에, 현재 worktree 가 비-메인이고 작업이 `done` 이며 uncommitted·unpushed 가 모두 없을 때 worktree 삭제를 AskUserQuestion 으로 제안하는 단계 추가. README skills/e 섹션 동기화.

# Progress
- 2026-06-03: 요청 접수 → AskUserQuestion 으로 설계 합의(트리거=done+clean+pushed, wt rm 동일 옵션, main 으로 빠져나간 뒤 remove). main 기반 worktree `e-worktree-cleanup` 생성(최초 origin/main stale base + 외부 prune 으로 1회 재생성). e/SKILL.md·README·wt rm 섹션 read 완료. SKILL.md/README 편집 착수.
- 2026-06-03: SKILL.md(5단계+`## worktree 정리 규칙`+경계+desc)·README 편집 완료 → code-reviewer+codex **병행** 검토 → CRITICAL 2(C1 gitignored 무경고 삭제, C2 worktree 내부 plan 자기삭제)+MAJOR 3(M1 unpushed 판정 fatal/부정확, M2 clean 시점, M3 값캡처/가드)+Nit. **fix loop 1회차 전항목 반영**(조건 5개로 재작성: detached 가드, `@{u}`+`--not --remotes` 폴백, `--ignored` 인벤토리 점검, plan 내부면 제안생략, 이동 전 값캡처+EnterWorktree 실패 가드, path normalize). → 정식 커밋 `ea64615`(push 대기).
- 2026-06-03: (같은 세션·브랜치, 별개 주제) **config 정리** — CLAUDE.md §8 "비trivial 은 worktree-per-task" 강화 + gitignored worktree-remove 주의, lessons 메커니즘 폐기(§11·§3 Setup·README + `docs/lessons.md` 삭제 — 직전 `0157cf0` 으로 추가했던 lessons 항목도 이때 파일째 폐기), push-review ②(pre-push codex 리뷰) 제거(스킬 + §10 codex 규약 + README). ① 보안 가드(pre-commit-check·install-hooks)·local-review·docs/codex-review 는 유지. plan 모드 승인(`~/.claude/plans/happy-wandering-stearns.md`) 후 진행 → 커밋 `cc5d82c`.
- 2026-06-03: push 완료(`-u origin e-worktree-cleanup`, ① 가드 통과, ② 제거로 codex 마찰 없음) + **PR #20** 생성(https://github.com/yoon627/claude-config/pull/20) — 머지 대기.
- 2026-06-03: **PR #20 머지 완료**(merge commit, 08:00Z) → `status: done`. 로컬 main sync, plan 을 main `plans/` 로 보존 후 worktree `e-worktree-cleanup` 정리.
- 2026-06-03: 원격 브랜치 `e-worktree-cleanup` 삭제 + C2 근본해결(plan→main `plans/` write 정책)을 **issue #21** 로 등록. `/e` 로 세션 마무리 — 추가 진행 작업 없음(모든 plan done, tree clean).

# Next
- (완료) PR #20 머지 + worktree 정리까지 끝. 후속 작업 없음.

# Decisions
- 트리거 조건 = (1) cwd 비-메인 worktree + (2) plan status=done + (3) uncommitted 없음 + (4) unpushed 없음 — 4개 모두. 이유: 작업 미완(in_progress)이거나 원격 미보존(unpushed)인데 worktree 지우면 손실. 사용자 합의(done+clean+pushed).
- 삭제 옵션 = wt rm 과 동일(worktree만 / +브랜치 / 유지). 이유: 일관성·재사용. 기본=유지.
- 삭제 실행 = main worktree 로 EnterWorktree 후 `git worktree remove`. 이유: 자기 자신 worktree 안에선 remove 불가.
- `--force` / `git branch -D` 는 추가 AskUserQuestion. 이유: §8 + wt 주의 승계(묻지 않고 강제 금지).
- 작업 위치 = main 기반 별도 worktree(사용자 선택). 가능 이유: #18 로 e 스킬이 origin/main 에 머지돼 main 기반에 e/SKILL.md 존재.
- C2 근본해결(plan 을 항상 main worktree `plans/` 에 write)은 **defer** — e 단독 범위 밖(c/dlc/wt 전체 plan 위치 정책 변경). 이번엔 "plan 이 삭제 대상 worktree 내부면 제안 생략"으로 손실만 차단. 별도 이슈 후보.
- (스코프) config 정리(worktree 규칙·lessons·push-review)도 같은 `e-worktree-cleanup` 브랜치에 커밋 — 별개 주제지만 같은 "config 개선" 세션이고 e 작업과 한 PR 로 묶을 수 있어서. (역설적이지만 이번에 추가한 worktree-per-task 규칙은 *다음* 작업부터 적용.)

# Key Files
- skills/e/SKILL.md — e 작업 변경 대상(5단계 + 규칙 + 경계 + description).
- README.md — skills/e 섹션 동기화 + (config 정리) lessons·push-review 언급 제거.
- CLAUDE.md — (config 정리) §8 worktree-per-task 강화·gitignored 주의 / §3 Setup·§11 lessons 폐기 / §10 push-review→dlc 기본.
- commands/push-review.md, docs/lessons.md — 삭제됨(config 정리).
- skills/wt/SKILL.md rm 섹션 — 안전검사·옵션 구조 기준점(참고만, 변경 안 함).

# Review Disposition (code-reviewer + codex 병행, 1회차)
- C1 gitignored 무경고 삭제 → **fix**: 조건5 `git status --porcelain --ignored` 인벤토리 점검 + 본문 명시.
- C2 worktree 내부 plan 자기삭제 → **fix(차단)**: plan 이 대상 worktree 내부면 제안 생략. 근본해결(main 에 write)은 defer.
- M1 unpushed 판정 fatal/부정확 → **fix**: `@{u}` + `--not --remotes` 폴백(wt rm 일치), `origin/<branch>..HEAD` 제거.
- M2 clean 등식 시점 오류 → **fix**: 삭제 직전 재수집 명시(2단계 신뢰 안 함).
- M3 값 캡처/EnterWorktree 가드 누락 → **fix**: 이동 전 target/main path 캡처 + 이동 실패 시 중단.
- Nit detached HEAD → **fix**(조건2 가드). Windows path → **fix**(normalize). 위험파일 분리/upstream-only → **fix**(C1/M1 연동).

# Blockers
(없음)
