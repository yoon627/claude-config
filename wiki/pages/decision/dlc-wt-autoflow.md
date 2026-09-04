---
title: dlc-wt-autoflow
category: decision
created: 2026-06-19
updated: 2026-09-04
sources:
  - skills/dlc/SKILL.md (진입 매트릭스·dlc→wt)
  - skills/wt/SKILL.md
  - CLAUDE.md (§3-1, §8 커밋 규약)
  - plans/2026-09-04-auto-commit-rule
---

# dlc-wt-autoflow

dlc 가 **코드/파일을 바꾸는데 작업 worktree 밖이면 자동으로 wt 를 경유**해 worktree 안에서 진행한다. 기존에는 wt→dlc(한 방향)만 있어, `/dlc` 직접 진입 시 main 에서 작업할 여지가 있었다 — 이를 양방향으로 닫는다.

## 진입 매트릭스
요청 유형을 단일 기준 **"코드/파일을 바꾸는가"**로 분기([[worktree-per-task]] 의 강제 기준과 일치):
- 질문·탐색·읽기 전용 → dlc 미적용, 직접.
- trivial(오타·로그 1줄) → **wt 경유 worktree → dlc trivial**(절차만 생략, worktree 는 필요).
- 비trivial(small 이상) → **wt 경유 worktree → dlc 전체**.

## 순환 방지
wt→dlc(정상)와 dlc→wt(보강)는 **worktree 위치로 구분**한다. wt 가 요청사항으로 dlc 를 invoke 한 경우는 이미 worktree 안 → dlc 가 이 단계를 건너뛴다. `git worktree list --porcelain` 첫 worktree(=main)와 현재 cwd 비교로 판정.

## 생성 확인 → 무확인 (2026-08-03 변경)
당초(2026-06-19)는 "자동은 *경로 선택*이 자동일 뿐, wt 의 slug 확인(`AskUserQuestion`)은 유지 — 무확인 생성 금지(실수 생성 방지)"였다. **2026-08-03 무확인 생성으로 뒤집었다.**

이유: ① 사용자가 slug 승인을 마찰로 지목. ② [[risk-based-approval]] 기준상 worktree 생성은 로컬·비파괴·`/wt rm` 한 번으로 가역이라 확인 대상이 아니다 — 확인은 비가역·외부공개·파괴적에만. ③ 원래 근거였던 "이름 오타로 인한 오생성"은 승인이 아니라 **정보**로 막는다: wt request §4 가 base·stale·충돌 suffix·near-miss(단일 토큰이 기존 worktree 와 유사)와 `/wt rm <slug>` 되돌리기를 생성 직후 보고한다.

삭제 계열(`wt rm`·`--force`·`branch -D`·원격 삭제)의 확인은 **그대로 유지** — 비가역이라 같은 기준의 반대편이다.

## trivial 도 worktree (2026-09-04 변경)
당초(2026-06-19~08-03)는 "trivial 은 새 worktree 불필요 — 현재 worktree 에서 즉시통과"였다. **2026-09-04 trivial 도 wt 경유로 뒤집었다.**

이유: 같은 날 CLAUDE.md §8 에 "검증 통과한 작업 단위는 요청 없이 커밋한다"를 신설하면서 main/master 직접 커밋을 금지했는데, trivial 이 main 에서 돌면 **커밋이 도달 불가**해진다 — 가장 흔한 소소한 수정에서 "매번 커밋하라고 지시해야 하는" 원래 문제가 그대로 남는 사각이었다(code-reviewer 가 지적, 사용자 결정으로 해소).

바뀐 것은 **작업 장소뿐**이다. trivial 의 절차 생략(리뷰·plan·TDD 면제)은 그대로 — 규모는 *도는 단계*를 정하고, worktree 여부는 *코드/파일을 바꾸는가*가 정한다. 오타 1줄에도 worktree 생성 비용이 붙는 것은 감수한 트레이드오프다.

**종결 경로**: trivial·small 은 push·PR 없이 **로컬 `git merge --ff-only <slug>`** 로 default 에 반영하고 §8(a) 자동 정리로 닫는다(CLAUDE.md §8). 그러지 않으면 "커밋 도달 불가"가 "머지 도달 불가"로 옮겨갈 뿐이고 — PR 왕복 비용 탓에 머지가 미뤄지면 (a) 의 merged 조건이 안 걸려 worktree 가 누적된다([[lesson-fix-scoped-to-one-repo]] 의 68개 중 60개 미push 기록). medium 이상·CI 검증·외부 공유는 `/e merge`([[e-merge-mode]]).

**예외**: worktree 사본이 없는 gitignored 글로벌 상태(`projects/…/memory/`·`settings.local.json`)와 비-git 디렉토리는 이 강제에서 제외 — 만들어도 커밋될 것이 없다.

다만 예외를 규약에 적는 것만으로는 부족하다. **이미 worktree 세션 안이면 하네스 네이티브 격리가 이들의 main 경로 편집을 거부**한다("worktree 사본을 편집하라" — 그런데 gitignored 라 사본이 없다). `scripts/guard-worktree-edit.js` 는 allow 하지만 네이티브 격리가 그 위에 있다. **2026-09-04 이 작업 중 실제로 재현**됐다 — [[lesson-grep-absence-not-proof]] 를 적립하려고 `MEMORY.md` 인덱스를 갱신하다 차단당했고, [[native-overlap-ledger]] 의 2026-08-12 실측이 현행 하네스에서도 유효함이 확인됐다. 그래서 [[feedback-memory]] 적립은 **worktree 안에서 시도하지 말고 main 복귀 후** 한다.

## 연계
완료 게이트는 [[evidence-gate]], dlc 파이프라인은 [[dlc-development-cycle]], plan 채널은 [[plan-handoff]].
