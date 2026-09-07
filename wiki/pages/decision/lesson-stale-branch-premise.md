---
title: lesson-stale-branch-premise
category: decision
created: 2026-09-08
updated: 2026-09-08
sources:
  - 커밋 e787287 (docs(skills): dlc plan 경로 정정 + /wt rm 에 gitignored 산출물 점검)
  - plans/2026-06-16-dlc-loop-redesign (P0 · D1)
  - 브랜치 dlc-loop-redesign 6c703d2 (2026-06-16, 미머지 폐기)
---

# lesson-stale-branch-premise

**오래 묵은 브랜치를 머지하기 전에 diff 가 아니라 *전제*가 아직 유효한지 확인한다.** diff 는 깨끗하게 적용되고 테스트도 통과하는데, 그 변경이 **왜 필요했는가**가 그 사이 무효가 되어 있을 수 있다. 그러면 머지는 성공하고 문서·규약에는 **틀린 서술**이 들어간다 — 충돌이 안 나므로 git 도 리뷰도 경고하지 않는다.

## 사례 (이 lesson 의 발단)

`dlc-loop-redesign` 브랜치의 P0(커밋 `6c703d2`, 2026-06-16)은 2건을 고쳤다:

1. `skills/dlc/SKILL.md` 의 plan 경로를 **"항상 main worktree 의 `plans/` 에 둔다"** 로 고정
2. `skills/wt/SKILL.md` 의 `rm` 안전검사에 gitignored 산출물 점검 추가

두 변경의 공통 전제는 **"plan 은 gitignored 라 worktree 를 지우면 함께 소실된다"** 였다. 브랜치 문구도 그대로 적고 있었다 — "이 repo 는 whitelist `.gitignore` 라 `plans/`·`.env` 가 ignored → `git status` 엔 안 보인다".

2026-09-08 에 머지하려고 보니 그 사이 main 이 **371커밋** 나갔고, 전제가 무효였다:

- `.gitignore` 에 `!/plans/` 가 들어가 **`plans/` 는 tracked** 다. 미커밋 plan 은 `git status` 에 보이고 `git worktree remove` 가 거부한다(CLAUDE.md §8 이 이미 그렇게 기술).
- `skills/c/SKILL.md` 는 이미 다른 결론으로 정착했다 — "`<ROOT>/plans/` 와 main worktree 양쪽을 본다. plans/ 는 브랜치별 독립(tracked 지만 브랜치마다 내용이 다르다)".
- 같은 날 이 세션이 worktree 에서 만든 plan 을 브랜치와 함께 커밋·머지했다. 소실 경로 자체가 없다.

그대로 머지했다면 (1) 은 이미 폐기된 강제를 되살리고, (2) 는 **사실과 다른 설명**("plans/ 가 ignored")을 규약에 심었을 것이다. 실제로 남아 있던 결함은 따로 있었다 — dlc 의 경로 표기가 §10 의 dated-dir 형식과 어긋나고 이 repo 에서 double-nest 된다는 것, 그리고 `wt rm` 에 `--ignored` 점검이 여전히 없다는 것. **그 둘만** 현재 사실에 맞춰 재적용하고 브랜치는 폐기했다.

## 근본 원인 (3 Whys)

1. **왜 틀린 문서가 들어갈 뻔했나?** "미머지 브랜치 = 머지하면 되는 것" 으로 다뤘다.
2. **왜 그렇게 다뤘나?** 검증 신호(diff 적용됨·테스트 통과·`# Next` 가 "머지 대기")가 전부 초록이었다. 전제 유효성은 그중 어느 것도 보지 않는다.
3. **왜 아무도 안 잡나?** git 은 텍스트 충돌만 본다. 전제를 무효화한 변경(`plans/` tracked 전환)은 **다른 파일**에서 일어나 diff 가 겹치지 않았다.

## 올바른 방법

- 브랜치를 머지하기 전에 **base 이후 main 이 얼마나 갔는지 먼저 센다**: `git rev-list --count $(git merge-base main <br>)..main`. 수가 크면 전제 재검증을 절차에 넣는다.
- plan 의 `# Decisions` 에서 **그 변경의 근거 문장**을 뽑아, 그 문장이 지금도 참인지 하나씩 확인한다. 근거가 "X 는 gitignored 라" 같은 **환경 사실**이면 그 사실을 직접 재확인한다(`git check-ignore`·`git ls-files`).
- 브랜치가 건드리는 파일의 **현재 main 내용**을 읽는다. 같은 주제를 다루는 이웃 파일(여기서는 `skills/c/SKILL.md`)이 그 사이 다른 결론에 도달했을 수 있다.
- 전제가 무효면 **브랜치를 머지하지 말고 현재 기준으로 재적용**한다. 그리고 plan 의 그 결정을 "~로 변경 (이유: …)" 으로 덮되 **원문은 이력으로 남긴다**(CLAUDE.md §10) — 다음 세션이 같은 안을 다시 꺼내지 않게.
- 오래된 브랜치·plan 은 **닫히지 않은 것 자체가 신호**다. `session-brief` 가 미머지 로컬 브랜치와 stale plan 을 매 세션 알리는 이유가 이것이다 — 오래 방치될수록 머지 가치가 아니라 오염 위험이 커진다.

## 연계

plan 이 세션·도구를 건너 상태를 나르는 방식은 [[plan-handoff]], 결정을 덮되 이력을 남기는 규약도 같은 문서, 낡은 외부 사실을 그대로 쓴 사례는 [[lesson-stale-tool-version]], 같은 repo 에서 전제가 3회 재발한 사례는 [[lesson-tracked-config-machine-paths]].
