---
title: plan-handoff
category: concept
created: 2026-06-19
updated: 2026-09-15
sources:
  - CLAUDE.md (§10 plans 핸드오프 규약)
  - skills/c/SKILL.md
  - skills/e/SKILL.md
  - [[ai-native-sdlc-playbook-intent]] (`# Intent` 도입 출처)
  - plans/2026-09-07-plan-intent-section
  - plans/2026-09-09-intent-default-medium (`# Intent` medium 이상 항상)
  - plans/2026-09-15-intent-md-bundle (묶음 intent.md)
  - plans/2026-09-16-intent-split-check (트리거 2 능동 판정·`분할:` 필드·plan-reviewer 묶음 모드)
---

# plan-handoff

세션·도구 간 작업 컨텍스트를 단일 plan 파일로 공유하는 규약(CLAUDE.md §10). 경로 `plans/<YYYY-MM-DD>-<slug>/<slug>-plan.md`. [[project-memory]]의 *일시적* 절반 — 작업이 끝나면 닫히고, 재사용 지식만 wiki로 일방향 승격된다.

## frontmatter + 6섹션
`title·status(in_progress|blocked|done)·started·updated` + `# Goal / Progress / Next / Decisions / Key Files / Blockers`. 선택 섹션: `# Intent`(착수 전 확정한 요구 — Problem·Constraints·Out of scope·Open questions, dlc 요구사항 명확화가 채운다 — [[dlc-development-cycle]]), `# Acceptance`(증거로 충족될 때만 완료 — [[evidence-gate]]), `# Review Disposition`(리뷰 finding 처분), `# Deferred`(범위 밖 발견 — [[deferred-and-scope-boundary]]), `# Workflow Findings`(확인된 workflow 실패 — [[workflow-failures]]).

선택 섹션은 필수 6섹션과 달리 "빈 채로라도 헤더 유지" 대상이 아니고, `plan-lint` 의 6 H1 검사에도 걸리지 않는다. "선택"은 구조(스키마·lint)의 성질이고 채우는 조건은 절차 소유자가 정한다 — `# Intent` 는 구조상 선택이지만 dlc medium 이상에서는 절차상 필수다.

> `# Intent`(2026-09-07 도입, 출처 Claude Academy *AI-Native SDLC Playbook* Stage 1)는 2026-07-07 `unknowns-pass` 의 wontfix("plan 에서 바뀔 결정 앞세우기")를 부분 supersede 한다. 그때 기각 사유는 6섹션 구조 충돌·`# Decisions` 중복·이득 대비 큰 변경이었는데, Intent 는 **선택** 섹션이라 필수 6이 불변이고, 담는 것이 *결정*이 아니라 **문제·제약**이라 `# Decisions` 와 겹치지 않는다. 채택 계기는 제약을 안 적어 같은 안이 3회 왕복한 2026-09-07 실측([[lesson-tracked-config-machine-paths]] 건). **2026-09-09 조건 변경**: 도입 시 "공백을 발견했을 때만" 채우던 것을 medium 이상은 항상 채우도록 바꿨다 — 계기가 된 실패는 공백을 못 본 것이 아니라 제약이 어디에도 적히지 않은 것이어서 공백-트리거로는 재발을 못 막았다. 형식(`없음 — <근거>`·Open questions 조건부·⚠️ 추론분)과 예외는 `skills/dlc/SKILL.md` 가 정본이고, [[self-diagnosis-and-improvement-status]]가 기각한 invariant-check 와의 구분은 plans/2026-09-09-intent-default-medium `# Decisions` 에 있다.

## 묶음 intent (`intent.md`, 2026-09-15)
`# Intent` 는 plan 과 1:1 을 전제했는데 실제 작업은 한 요구가 하루에 plan 3~4개로 갈라졌다(knowledge_base 2026-09-14 체인 2개 — Problem 재작성·계보 산문·공통 제약 복제). 그래서 요구 하나를 `plans/<YYYY-MM-DD>-<intent-slug>/intent.md` 에 두고 각 plan 이 frontmatter `intent:` 로 가리킨다(형식·트리거·수명·소유권·한계는 CLAUDE.md §10 "묶음 intent" 가 정본 — 여기 재서술하지 않는다). 설계상 비자명한 점 둘: plan 은 자기 dir 에 그대로 두고 intent dir 엔 `*-plan.md` 가 없어 매칭·`plan-match.js`·`session-brief.js`·`plan-lint` 가 불변(코드 변경 0)이라는 것, 그리고 `closed` 조건에서 Out of scope 를 뺀 것(영구 경계라 넣으면 영영 안 닫힌다 — plan-reviewer 가 초안에서 잡음). 기각안: intent dir 에 plan 여럿(매칭 의미 변경), plan 간 `follows:` 링크만(공통 제약 단일 위치 없음), 첫 plan `# Intent` 를 정본으로(plan 은 종료 시 닫히는데 정본이 그 안에 남음). 2026-09-07 의 "별도 `intent/` 홈 미채택" 은 유지 — `plans/` 아래라 다른 트리가 아니다.

2026-09-16 보강 — 트리거 2 는 "plan 이 2개 이상 예상됨"(수동)이었는데, 사용자가 "intent 하위 여러 plan 이 생겨야 plan 단위가 작아진다"고 제기해 medium 이상은 dlc 요구사항 명확화의 **분할 판정**이 능동으로 보게 했다([[dlc-development-cycle]]). 정의 측 변경은 둘: 트리거 2 의 의미를 "독립 검증·머지 가능한 복수 plan 으로 나뉠 때"로 두고 절차만 dlc 로 연결(CLAUDE.md 는 항상 주입, dlc 는 진입 시만 로드라 정의를 옮기면 미진입 세션이 조건을 잃는다), `# Intent` 정의에 분할 판정 결과(`분할: 없음 — <근거>`)를 넣었다(dlc 에만 두면 plan-reviewer 14항·`/c` 가 §10 항목 기준으로 읽어 그 줄을 모른다). 기각안: intent.md 상시화(사용례 1건에서 굳히지 않는다 — 5회 사용 후 재판단, intent.md Open question) · "각 plan ≤ medium" 목표(20줄 public API 도 structural 이라 규모를 규범값으로 바꾸고 우회 유인이 생긴다 → "작게 나누되 규모는 gate 로 독립 판정") · 묶음 단위 architecture-reviewer 1회(`architecture-reviewer.md` 적용 범위와 충돌, 사용자 미확인 → deferred). 미착수 형제가 잊히지 않도록 `/e` 보고가 `(미착수)` 후보를 `/wt` 착수 경로와 함께 열거한다(`/c` 는 plan 을 새로 만들지 않는다).

## 핵심 원칙
- **single-writer**: 메인 에이전트만 plan을 쓴다. subagent는 읽기만, 결과는 "plan 반영용 요약"으로 반환. 쓰기 직전 re-read로 외부 변경 merge. (이유: Claude↔Codex 동시 쓰기 충돌 방지 — [[claude-codex-collaboration]])
- **active plan tracking**: branch가 slug와 안 맞아도 세션에서 진행 중이던 plan을 계속 추적(branch 매칭은 *처음 찾는* 수단일 뿐).
- **진행 중 동기화**: 방향/스코프/결정 변경은 턴 종료까지 미루지 말고 **즉시** plan에 반영.

## 도구
- `/c`(plan-continue): plan 찾기 + plan↔실제(git/코드) sync 진단 + 다음 액션 제시(자동 실행 안 함).
- `/e`(plan-end): Progress/Next/status 기록 + uncommitted를 WIP 커밋 보존 + worktree 정리 제안 + main 복귀.

## 경계
plans/는 **tracked** 이고([[worktree-per-task]]별로 브랜치마다 내용이 다르다) 작업 브랜치와 함께 commit·push 되어 머신 경계를 넘는다 — 충돌·진행중 작업 판단의 실시간 소스. [[dlc-development-cycle]]이 이 채널로 작업을 추적한다. 이 tracked 전환이 옛 결정의 전제를 무효화한 사례는 [[lesson-stale-branch-premise]].
