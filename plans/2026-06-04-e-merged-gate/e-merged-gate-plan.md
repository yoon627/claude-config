---
title: e-merged-gate — e 스킬 worktree 삭제 제안에 base merged 조건 추가
status: done
started: 2026-06-04
updated: 2026-06-04
---

# Goal
e 스킬 5단계 worktree 삭제 제안이 `pushed`(원격 보존)까지만 보고 `merged`(base 통합)는 안 봐서, PR push 후 리뷰 중(미머지)에 `/e`+done 확정 시 worktree 삭제가 제안돼 리뷰 작업 공간이 사라질 위험을 막는다. `push ≠ merge` 를 삭제 조건에 반영.

# Progress
- 2026-06-04: worktree `e-merged-gate`(base ca59c54/#26) 생성. 탐색 — 자동 삭제 제안은 e 5단계가 유일(wt rm 은 수동·unpushed 만, c 는 진단 only). 편집 지점 6곳 확정.
- 2026-06-04: 구현 — SKILL.md 6곳(조건5 신설·조건6 번호·2단계 참조·경계·frontmatter)·README:304. code-reviewer(격리 temp repo 6종 재현)+codex 병행 → 조건5 에 BASE 유효성 선확인(fatal 회피)·한계(squash/rebase·stale·비-기본 베이스) 보강. git 명령 동작 검증(무효 ref fatal 회피 실증). 커밋 `902eb91`.
- 2026-06-04: push(origin/e-merged-gate) → PR #27 머지(no-ff merge commit `8383e00`, origin/main 갱신). 조건5 self-test 통과(머지 후 `origin/main..HEAD` 빔 → merged 판정). worktree 정리(plan 을 main 으로 이동 후 worktree+브랜치 삭제), main 복귀.

# Next
- 완료(머지 #27). main worktree(`C:\Users\USER\.claude`)에서 `git pull` 하면 e 스킬 신조건 적용(현재 main `64d2502`, `M settings.json` 미커밋 변경과 무관 → fast-forward).

# Decisions
- `BASE` = `git symbolic-ref --short refs/remotes/origin/HEAD`(실패 시 `origin/main` 폴백; wt 4단계와 동일). 이유: origin default branch 를 base 로, ref 부재 시 안전 폴백.
- merged 판정 = `git log <BASE>..HEAD` 빔(브랜치 모든 커밋이 BASE 에 포함). 이유: merge-commit(no-ff) 방식에서 정확. 비면 미머지 → 생략·유지.
- 조건5 폴백 fatal 방어(리뷰 반영): `git rev-parse --verify --quiet <BASE>` 로 유효성 선확인 후에만 `git log` — origin/main 부재 시 fatal(exit128) 회피(조건4 와 대칭). 이유: reviewer/codex 가 default=master·origin/main 부재 repo 에서 fatal 재현.
- squash/rebase·stale 은 false-negative(유지=안전) 방향이라 보수적 유지(수동 `/wt rm`). 비-기본 베이스(release/develop) worktree 는 BASE 오판 가능 — 한계로 명시(done·clean·AskUserQuestion 1차 방어, wt 가 기본 브랜치 분기라 빈도 낮음). gh CLI PR 조회는 범위 확대라 미도입.
- 조건4(unpushed=유실방지) 유지 + 조건5(merged=완료) 신설. merged⟹pushed 지만 ref(@{u} vs origin/BASE)·관점이 달라 둘 다 둠(조건4=안전망). reviewer 가 중복 아님 확인.

# Key Files
- skills/e/SKILL.md — 5단계 조건5(신규 merged)·조건6 번호, 2단계 수집 표현, 경계 섹션, frontmatter description
- README.md:304 — e 스킬 삭제 조건 미러 (동기화)

# Review Disposition (code-reviewer + codex 병행)
- Major1 BASE 폴백 fatal → **fix** (`rev-parse --verify` 선확인, 조건4 와 대칭).
- Major2 squash/rebase false-negative → **fix** (조건5 'no-ff 전제' 명시; 의도된 보수 동작).
- Minor3 비-기본 베이스 false-positive → **fix** (한계 단서).
- Minor4 fetch stale → **fix** (안전 방향 명시).
- Nit5 2단계 참조 → **fix** (`BASE` 정의=조건5 로 좁힘).
- 조건4·5 중복 아님 / frontmatter·README·경계 일관성 → 확인(no-op).

# Blockers
(없음)
