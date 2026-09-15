---
title: intent-bundles — 한 요구가 여러 plan 으로 갈라질 때 요구를 한 파일에 둔다
status: open
started: 2026-09-15
updated: 2026-09-15
---

# Problem

plan `# Intent`(2026-09-07)는 plan 과 1:1 을 전제했는데, 실제 작업은 한 요구가 하루에 plan 3~4개로 갈라진다(knowledge_base 2026-09-14: `proxy-peer-address` → `home-banner-query-agent` → `home-banner-simplify` + `login-session-400d`; `worker-default-options-dkms` → `security-workflow-redesign` → `wifi-bt-protocols`). 각 plan 이 Problem 을 처음부터 다시 쓰고, 계보는 "이전 브랜치 종료 후"·"별도 브랜치 X" 산문으로만 남으며, 공통 제약("cstp read-only")이 plan 마다 복제된다. 앞 plan 의 Out of scope 를 뒤 plan 이 이어받는지 확인할 단일 위치가 없다.

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

- (열림) knowledge_base 의 `plans/` gitignore 를 풀 것인가 — public 여부·비밀 스캔 범위 확인 뒤 판단(사용자 "왜 tracked 로 바꾼다는거야?" 2026-09-15). 풀지 않으면 그 repo 의 intent.md 는 로컬에만 남는다.
- (열림) `intent:` 참조 무결성 검사를 `plan-lint` CLI 에 둘 것인가 — 첫 사용례 뒤 판단.

# Plans

- `plans/2026-09-15-intent-md-bundle/intent-md-bundle-plan.md` — 규약 도입(§10·dlc·c·e·plan-reviewer·README·wiki)
