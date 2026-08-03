---
title: risk-based-approval
category: decision
created: 2026-08-03
updated: 2026-08-03
sources:
  - CLAUDE.md (§1 승인은 위험기반)
  - skills/wt/SKILL.md (request §3~§4)
  - https://www.analyticsvidhya.com/blog/2026/07/graph-engineering/ (graph engineering, 2026-07-29)
---

# risk-based-approval

승인(human interrupt)을 **액션의 가역성**으로 가른다. 스킬마다 임의로 배치하던 `AskUserQuestion` 을 단일 기준으로 일원화한 결정.

- **확인한다** — 비가역·외부공개·파괴적: push·머지·원격/강제 삭제·배포·DB write·외부 전송·비용 발생.
- **묻지 않는다** — 로컬에서 한 명령으로 되돌릴 수 있고 기존 데이터를 지우지 않는 것: worktree/브랜치 생성, 파일 편집, 로컬 실행. 대신 **되돌리는 데 필요한 정보**(무엇을·어디에·되돌리는 명령·경고)를 보고에 담는다.
- 애매하면 확인(fail-safe).

## 왜

graph engineering(2026)의 human-in-the-loop 원칙: 사람 검토는 위험 기반이어야 하며, 무해한 단계마다 승인을 요구하면 안전은 그대로인 채 시스템만 느려진다(analyticsvidhya, 2026-07-29). 승인 피로는 정작 위험한 승인마저 무감각하게 만든다.

기준 어휘는 새로 만들지 않고 이미 `skills/c/SKILL.md` 예외 5종에 있던 "파괴적·비가역·외부공개"를 CLAUDE.md §1 로 승격한 것이다.

## 승인 대신 무엇으로 안전을 확보하나

없애는 게 아니라 **승인 → 사후 정보**로 옮긴다. [[dlc-wt-autoflow]] 의 무확인 worktree 생성이 표본: base ref·sha, `git fetch` 실패로 인한 stale base, `.env` 복사 수, 충돌 suffix, near-miss(공백 없는 요청이 기존 worktree 와 정규화 후 Levenshtein ≤2 이고 후보가 1개), `/wt rm <slug>` 되돌리기를 생성 직후 한 번에 보고한다. 사용자는 승인 프롬프트를 기다린 게 아니라, 잘못됐음을 **본 뒤 한 명령으로** 되돌린다.

## 침식하지 않는 것

"되돌리기 쉬우면 묻지 말라"는 **액션 확인**에만 적용된다. 다음은 위험도와 무관하게 그대로다:
- **방향 합의** — CLAUDE.md §3-3 plan 승인, dlc 요구사항 명확화. 편집이 가역이라고 합의 없이 방향을 정하지 않는다.
- **운영 자산 자가 수정 금지**(§1) — 가역성이 아니라 *권한* 게이트다.
- **삭제 계열 전부** — [[worktree-per-task]] 의 삭제 조건, `/e`·`wt rm` 의 worktree 삭제·`--force`·`branch -D`·원격 삭제(§8(b)). §8(a) 자동 정리만 예외이며 그건 5개 안전조건으로 이미 게이트돼 있다.

> [!open] `/improve` 의 "수정은 승인 후" 와 `/wiki lint` 의 "자동 수정 안 함" 은 가역적 로컬 편집인데도 승인을 유지한다 — 가역성이 아니라 자가수정 경계에 걸리기 때문. 두 게이트의 근거가 다르다는 점을 이 기준이 흐리지 않는지 다음 `/improve` 에서 재확인.
