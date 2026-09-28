---
title: lesson-parallel-duplicate-implementation
category: decision
created: 2026-08-05
updated: 2026-09-25
sources:
  - PR #118 (worklog-cwd-attribution, 2026-08-04 머지)
  - PR #120 (jira-worklog-cwd-attribution, 2026-08-05 생성 → 미머지 close)
  - CLAUDE.md §9 (Claude ↔ Codex 협업) · §10 (plans/ 핸드오프)
  - origin/commit-split (2026-09-22 push, 2026-09-25 close — 로컬 태그 archive/commit-split 51d55d9) · PR #171·#172 (2026-09-24 머지)
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

## 두 번째 사례 — commit-split vs #171·#172 (2026-09, ✅확실)

규칙이 memory 인덱스(`check-inflight-work-before-starting`)에 있었는데도 재발했다. 이번에는 **같은 도구(Claude) 안에서**, 앞선 세션의 미머지 원격 브랜치를 뒤 세션이 보지 않았다.

| | origin/commit-split | #171 commit-check · #172 dlc-unit-commits |
|---|---|---|
| 시작 | 2026-09-22 push(WIP 5커밋, plan `in_progress`) | 2026-09-24 착수·머지 |
| 내용 | `/cs` hunk 분할 skill + dlc 중간 커밋 + `/e` M3 연결 | commit-check(plumbing+CAS, 승인 후 재구성) + dlc 목적 단위 커밋·fixup |
| 결과 | close — 5파일 텍스트 충돌, 설계 3곳이 main 결정과 충돌 | main |

- 왜 놓쳤나: 09-24 세션은 사용자가 "저번에 … 했던 것 같은데" 라고 앞선 작업을 암시했는데도 로컬 plan 만 보고 새로 설계했다. 원격 브랜치 목록 확인이 없었다 — 규칙은 인덱스 한 줄로 주입됐지만 착수 시점에 실행되는 절차가 없다.
- 비용: 버린 WIP 는 작았지만(+244/−17), 뒤 작업이 앞 작업의 결정(hunk 분할)을 모르고 **기각**해 두 설계가 정면 충돌했다. 전체 감사(2026-09-25)에서야 드러났다.
- 이번에 살린 것: `/e merge` 의 push 전 `fixup!`·`wip:` 검사 아이디어 → `plans/2026-09-25-e-merge-unfolded-commits/`.

두 사례 모두 "착수 전 열린 PR·원격 브랜치·in_progress plan 확인"을 기억에 맡겨 생겼다. 세 번째가 나오면 규약 한 줄이 아니라 착수 시점의 기계적 점검(예: dlc 요구사항 명확화 단계의 원격 브랜치 목록 출력)으로 올린다(CLAUDE.md §13 "반복되면 게이트로 승격").

## 비용

폐기 553줄이 전부는 아니다 — #120 은 `CONFLICTING` 상태로 남아 있었고, 처분 판단(트리 대조·순증분 식별)에 별도 세션 작업이 들었다. 중복 구현의 비용은 **버린 코드 + 버릴지 판단하는 비용**이다.

## 연계

협업 역할 분담은 [[claude-codex-collaboration]], 핸드오프 채널의 설계 의도는 [[plan-handoff]], 작업 단위 격리는 [[worktree-per-task]]. 반복 신호로 세는 실패는 [[workflow-failures]] 쪽이다(이 건은 신호 없는 1회성 설계 공백이라 표가 아니라 lesson 으로 남긴다).
