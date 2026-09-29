---
title: intent-bundles — 한 요구가 여러 plan 으로 갈라질 때 요구를 한 파일에 둔다
status: closed
started: 2026-09-15
updated: 2026-09-29
---

# Problem

plan `# Intent`(2026-09-07)는 plan 과 1:1 을 전제했는데, 실제 작업은 한 요구가 하루에 plan 3~4개로 갈라진다(회사 repo 2026-09-14: 한 요구에서 plan 4개, 다른 요구에서 3개가 차례로 갈라졌다). 각 plan 이 Problem 을 처음부터 다시 쓰고, 계보는 "이전 브랜치 종료 후"·"별도 브랜치 X" 산문으로만 남으며, 공통 제약("회사 repo read-only")이 plan 마다 복제된다. 앞 plan 의 Out of scope 를 뒤 plan 이 이어받는지 확인할 단일 위치가 없다.

# Proposed outcome

묶음(요구) 하나에 `intent.md` 하나. 그 요구에서 나온 plan 들은 frontmatter 로 그 파일을 가리키고, 공통 제약·후속 목록·Open questions 는 intent.md 한 곳에서만 관리된다. 단발 작업은 지금처럼 plan `# Intent` 만 쓴다.

# Constraints

- 별도 `intent/` 홈은 만들지 않는다(2026-09-07 결정 유지 — plan 과 다른 트리에 두면 drift). `plans/` 아래 dir 하나.
- plan 매칭 규칙(`branch ⊂ dir 이름` → 그 dir 의 `*-plan.md` 1개)과 `scripts/plan-match.js`·`session-brief.js`·`plan-lint.js` 는 바꾸지 않는다 — intent dir 에는 `*-plan.md` 를 두지 않아 기존 스캔이 무시한다.
- 운영 자산 자가 수정 금지(§1) — 사용자가 2026-09-15 "묶음 단위 intent.md (권장)" 를 선택해 CLAUDE.md §10·dlc·c·e·wt·README·wiki 범위를 승인했다.
- CLAUDE.md §0 — 원문자 금지, 수사 대신 직설.

# Out of scope

- 플레이북의 조직 장치(PO 승인 게이트·survival rate·VCS 커넥터)·`spec.md` 단계.
- 기존 plan 의 본문 소급 변환(소급 생성 시 선행 plan 에는 `intent:` 1줄만).
- intent.md 스키마 lint.

# Open questions

- (이월 → #207) 회사 repo 의 `plans/` gitignore 를 풀 것인가 — public 여부·비밀 스캔 범위 확인 뒤 판단(사용자 "왜 tracked 로 바꾼다는거야?" 2026-09-15). 풀지 않으면 그 repo 의 intent.md 는 로컬에만 남는다. 처분(2026-09-29): `plans/` 가 gitignore 된 repo 에서 묶음 intent.md 가 worktree 에만 있는 사례가 이미 생겼고, 그 보존 절차는 #207 에서 다룬다.
- (해소) 두지 않음. `intent:` 참조 무결성 검사를 `plan-lint` CLI 에 둘 것인가 — 첫 사용례 뒤 판단. 처분(2026-09-29): origin/main 의 `plans/*/*-plan.md` 중 `intent:` 키가 있는 25개 전부가 존재하는 intent.md 를 가리킨다(dangling 0, 이력상 `intent:` 추가도 4개 묶음 대상뿐). CI 의 plan-lint 는 비차단이라 검사를 넣어도 막지 못한다. CLAUDE.md §10 한계 절이 선행 브랜치의 intent.md 를 가져오라고 요구하므로 dangling 참조는 허용 상태가 아니라 빠뜨린 단계다. 재개 조건: dangling 참조 1건 관찰.
- (해소) 유지. 분할 판정(2026-09-16)이 plan 을 실제로 작게 만드는가 — medium 이상 5회 사용 뒤 분할 발생 횟수와 `분할: 없음` 정형문화 여부를 관찰. 분할 0회·정형문이면 bullet 회수. 처분(2026-09-29): origin/main 에서 2026-09-16 이후 시작한 plan 중 `# Intent` 규모가 medium 인 7개(structural 0)는 `분할: 묶음` 1 · `분할: 없음` 6, `분할:` 줄 전체(`- ` 없는 줄 포함 26개)로는 묶음 4 · 없음 21 · 해당 없음 1. 분할이 0회가 아니고 `없음` 사유는 모두 그 plan 의 결합 관계나 고정비를 구체적으로 적어 정형문이 아니므로 회수 조건에 걸리지 않는다. "작게 만드는지" 자체는 측정하지 않았다.
- (해소) 기각. 묶음 단위 architecture-reviewer 를 "plan 사이에 걸친 구조 의사결정이 있을 때만" 조건부로 둘 것인가 — 사용자 확인 필요(`agents/architecture-reviewer.md` 적용 범위 수정 동반). 처분(2026-09-29): 기록된 plan-reviewer 묶음 모드 검토는 1회이고 그 지적은 계층·DI·수명주기 문제가 아니었다. dlc 는 분할이 단위의 규모 판정을 면제하지 않는다고 정하므로 structural 단위는 각자 architecture 검토를 받는다. 재개 조건: 묶음 경계에 걸친 계층·의존 방향 결정이 나타나거나, plan-reviewer 묶음 모드가 구조 결함을 1회 놓침.

# Plans

- `plans/2026-09-15-intent-md-bundle/intent-md-bundle-plan.md` — 규약 도입(§10·dlc·c·e·plan-reviewer·README·wiki)
- `plans/2026-09-16-intent-split-check/intent-split-check-plan.md` — 트리거 2 를 능동 분할 판정으로(dlc bullet·§10 `분할:` 필드·plan-reviewer 묶음 모드·`/e` 미착수 안내)
