---
title: e-merge-mode
category: decision
created: 2026-09-03
updated: 2026-09-03
sources:
  - PR #148 (skills/e/SKILL.md 머지 모드 M1~M6 · docs/worktree-lifecycle.md §E)
  - plans/2026-09-02-e-merge-path (plan-reviewer NO-GO→CONDITIONAL GO, code-reviewer fix loop 2회)
  - PR #147·#149 (규약 첫 실행 smoke 2회)
---

# e-merge-mode

`/e merge`·`/e 머지` 로만 켜지는 `/e` 의 머지 모드(2026-09-02). CLAUDE.md §3-6 과 dlc Report 는 push·PR·머지를 `/e` 에 위임했지만 `/e` 에는 체크포인트 흐름만 있어 매번 즉흥으로 수행했던 것을 규약화했다. 게이트·닫힌 목록은 `skills/e/SKILL.md`, gh 명령·시나리오 표는 `docs/worktree-lifecycle.md` §E.

## 핵심 결정과 이유 (리뷰로 뒤집힌 것 포함)
- **트리거는 `merge`·`머지` 토큰만.** `push`·`PR` 을 alias 로 두면 `/e push` 를 머지 승인으로 해석하게 되어 §1 비가역·외부공개 확인을 어긴다.
- **plan `done` 은 머지 전에 커밋해 PR 에 싣는다 + REJECTED 일 때만 `in_progress` 복구.** 머지 후엔 브랜치가 사라져 done 을 올릴 곳이 main 뿐이고 main push 는 §8 `ask` 대상. §10 "머지 시점에 done" 과의 간극은 복구 규칙이 메운다. 결과 불명(UNKNOWN)·큐 대기(QUEUED)·head 불일치는 done 을 유지하고 `# Next` 재실행 안내로 닫는다 — 여기서 복구 push 를 하면 머지된 base 와 어긋난다.
- **머지 성공 확인 + `git fetch` 는 hard invariant.** `collect-state.sh` 는 fetch 를 하지 않아 로컬 ref 만으로는 서버 머지를 영원히 못 본다 — PR #147 세션은 수동 fetch 로 우연히 통과했고, 리뷰어가 스크립트로 확정. 확인된 `mergedAt` 이 7단계 조건4(merged)를 직접 충족한다(squash 면 git 신호가 false 여도 재유도하지 않는다).
- **MERGED/CLOSED PR 은 재사용하지 않는다.** "이미 머지됐으면 skip" 경로는 plan done 커밋을 실을 PR 이 없어 7단계 조건 2·3·5(done·clean·미커밋 plan)를 못 넘는다. 남은 커밋으로 새 PR 을 만들고, 커밋 0 + done 이면 지름길(3단계 plan 편집을 `git restore`) — 브랜치를 base 보다 ahead 로 만들면 `git branch -d` 가 거부된다.
- **checks 는 exit code + `--json name,bucket` 별도 재조회.** `gh pr checks --watch` 는 `cancel` 을 exit 에 반영하지 않고, `--watch` 와 `--json` 은 병용 불가. "No checks reported" 는 done push 직후 check run 미등록 레이스일 수 있어 3회 재조회 후에만 required 없음으로 본다.
- **`--delete-branch` 금지.** 로컬·원격 삭제를 묶어 §8(b) 분리 승인을 우회하고, worktree 가 main 을 점유한 환경에선 로컬 삭제가 실패/스킵된다([[workflow-failures]] 2026-08-05 실측). 원격 삭제는 정리 후 항상 1회 AskUserQuestion.
- **`<default>` 폴백은 `gh repo view defaultBranchRef.name`.** `origin/main` 같은 remote-tracking ref 를 브랜치 이름 자리에 쓰면 `gh pr create --base` 가 실패한다.

## 스코프에서 뺀 것
CLAUDE.md §8 에 "worktree 세션은 상대경로만" 한 줄을 넣으려던 원안은 리뷰어 실측으로 인과가 틀린 것으로 판명되어 제외 — 관찰은 [[worktree-isolation-bash-guard]].

## 첫 실행 관찰
PR #148(규약 자체)·#149 두 번 모두 M1~M6 이 문서대로 진행됐다. 첫 번째는 하네스가 옛 `/e` 본문을 로드해 worktree 파일을 보며 수동 추적했고, 두 번째부터 자동. 관련: [[evidence-gate]], [[worktree-per-task]].
