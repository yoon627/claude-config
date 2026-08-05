---
title: lesson-parallel-duplicate-implementation
category: decision
created: 2026-08-05
updated: 2026-08-05
sources:
  - PR #118 (worklog-cwd-attribution, 2026-08-04 머지)
  - PR #120 (jira-worklog-cwd-attribution, 2026-08-05 생성 → 미머지 close)
  - CLAUDE.md §9 (Claude ↔ Codex 협업) · §10 (plans/ 핸드오프)
---

# lesson-parallel-duplicate-implementation

**같은 기능을 두 에이전트가 각자 구현해 한쪽 553줄이 통째로 폐기됐다.** `plans/` 를 공유 채널로 두고도 막지 못했다 — 그 채널은 *이어받기*용이지 *동시 착수 감지*용이 아니기 때문이다.

## 무슨 일이 있었나 (✅확실)

| | PR #118 | PR #120 |
|---|---|---|
| 목표 | worktree 별 AI 작업시간 귀속 | **같은 것** |
| 머지 | 2026-08-04 14:42 | 미머지 → 2026-08-05 close |
| 분기점 | — | `d38c70b`(#116) — #118 머지 **이전** |
| 규모 | +1000 내외 | +553 / −52 |
| plan | `plans/2026-07-22-worklog-cwd-attribution/` | `plans/2026-08-04-jira-worklog-cwd-attribution/`(별도 신설) |

#120 트리를 main 에 취하면 `+545 / −2009` 로 이후 머지분(#117·#118·#119·#121~#123)이 삭제된다. 귀속 방식도 main 이 더 정밀했다(이벤트 **줄 단위** cwd bucketing). 살릴 값어치가 있던 순증분은 Codex rollout 1회 스캔 한 조각뿐이고, 그건 별도로 이식했다(#126 — [[workflow-failures]] 와 무관한 별건).

#120 커밋에는 `Co-Authored-By: Claude` 트레일러가 없다 → Claude 가 아닌 도구(Codex 계열)로 **⚠️추정**. 단정하지 않는다.

## 왜 (3 Whys)

1. **왜 553줄이 폐기됐나** → 같은 기능을 #118 이 먼저 머지했다.
2. **왜 중복 착수했나** → 착수 시점에 *같은 주제의 진행 중 작업*(열린 PR·원격 브랜치·다른 plan dir)을 확인하는 단계가 어디에도 없다.
3. **왜 그 단계가 없나** → `plans/` 매칭 규약(§10)은 **자기 branch → plan dir** 방향이다. 남이 다른 브랜치에서 열어둔 plan 은 매칭 대상이 아니고, 새 브랜치로 시작한 도구는 기존 plan 을 **못 찾고 새로 만든다**. 채널의 설계 목표가 "세션·도구 간 이어받기"였지 "동시 착수 충돌 방지"가 아니었다.

즉 근본 원인은 도구의 실수가 아니라 **채널 설계의 공백**이다. 같은 공백이 남아 있는 한 재발한다.

## 잘못된 방법 / 올바른 방법

- ❌ 요청을 받자마자 `/wt` 로 새 브랜치를 파고 구현에 들어간다. plan 이 매칭 안 되면 "없구나" 하고 새로 만든다.
- ✅ **비trivial 착수 전에 같은 주제가 이미 진행 중인지 본다** — `gh pr list --state open`, `git branch -r`, `plans/` 의 `status: in_progress` 목록. 하나라도 걸리면 새로 만들기 전에 사용자에게 확인한다.
- ✅ plan 이 branch 매칭에 실패해도 **"없다"의 근거로 쓰지 않는다**. 매칭 실패는 "내 브랜치 이름과 안 겹친다"는 뜻일 뿐이다.
- ✅ 병행 도구를 쓰는 중이면 착수 사실을 plan `# Progress` 에 먼저 적고 push 해, 다른 도구가 볼 수 있게 한다(채널이 작동하려면 *먼저 쓰는* 쪽이 있어야 한다).

## 비용

폐기 553줄이 전부는 아니다 — #120 은 `CONFLICTING` 상태로 남아 있었고, 처분 판단(트리 대조·순증분 식별)에 별도 세션 작업이 들었다. 중복 구현의 비용은 **버린 코드 + 버릴지 판단하는 비용**이다.

## 연계

협업 역할 분담은 [[claude-codex-collaboration]], 핸드오프 채널의 설계 의도는 [[plan-handoff]], 작업 단위 격리는 [[worktree-per-task]]. 반복 신호로 세는 실패는 [[workflow-failures]] 쪽이다(이 건은 신호 없는 1회성 설계 공백이라 표가 아니라 lesson 으로 남긴다).
