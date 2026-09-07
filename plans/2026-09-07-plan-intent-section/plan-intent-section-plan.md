---
title: plan-intent-section — plan 에 `# Intent` 선택 섹션을 두고 dlc 요구사항 명확화가 그것을 채우게 한다
status: done
started: 2026-09-07
updated: 2026-09-07
---

# Intent

> 이 plan 자체가 새로 도입하는 `# Intent` 섹션의 첫 사용례다(dogfooding).

## Problem

착수 전에 확정한 "무엇을 왜, 어떤 제약에서" 가 어디에도 남지 않는다. §10 plan 의 `# Goal` 은 1~3줄 해법 서술이라 문제·제약·범위 밖이 압축돼 사라지고, dlc 의 *요구사항 명확화* 는 `AskUserQuestion` 대화로 끝나 증발한다. 그 결과 같은 판단을 세션마다 처음부터 다시 하고, 이미 기각된 선택지가 되살아난다.

2026-09-07 `settings.json` 작업이 실측 사례다. "settings.local.json 으로 옮기자"가 세 번 제시·세 번 기각됐는데, 기각 근거인 제약 세 가지(autoMode 는 그 파일에서 안 읽힘 · repo 가 public · 관리자 권한 없음)가 착수 시점에 어디에도 적혀 있지 않았다. 제약을 먼저 적었다면 첫 라운드에서 걸러졌다.

## Constraints

- **단일 소스 유지** — §10 이 plan 구조의 단일 소스, dlc 는 절차. 기존 `# Acceptance` 가 이미 그렇게 갈려 있으므로 같은 선례를 따른다. 한쪽에 몰아넣으면 다른 자산이 그 섹션의 존재를 모른다(`/c`·`/e` 는 §10 을 본다).
- **운영 자산 자가 수정 금지(§1)** — 사용자가 지시한 자산(`skills/dlc`)과 그 정합에 필요한 최소 범위(`CLAUDE.md` §10·README·wiki)까지만.
- **CLAUDE.md §0** — 항목 번호에 원문자 금지, 수사 대신 직설.
- 기존 plan 파일을 소급 수정하지 않는다(선택 섹션이므로 없어도 유효).

## Out of scope

원문 playbook 의 조직 장치는 도입하지 않는다 — 별도 `intent/` 홈, product owner 승인 게이트, survival rate 지표, Git 없는 기여자용 VCS 커넥터. 1인 워크플로우에 해당 없고, 산출물을 plan 과 이원화하면 drift 가 생긴다.

## Open questions

- `# Intent` 를 비trivial 전체에 권하나, structural 에만 권하나? → 현재 판단: 선택 섹션이므로 강제하지 않고 dlc 가 "공백이 acceptance 에 영향 줄 때" 채우게 한다.

# Goal

`CLAUDE.md` §10 선택 섹션에 `# Intent` 를 추가하고, `skills/dlc/SKILL.md` 요구사항 명확화 체크리스트에 빠져 있는 Problem·Constraints 를 보강해 그 결과가 plan `# Intent` 로 남게 연결한다. README·wiki 동기화 포함.

# Progress

- 2026-09-07: 출처 확인 — Claude Academy, AI-Native SDLC Playbook, Stage 1 "Capture as intent.md". 브라우저로 렌더된 본문 취득(WebFetch 는 SPA 라 제목만 반환).
- 2026-09-07: `scripts/plan-lint.js` 확인 — `REQUIRED_SECTIONS` 6개와 Acceptance 참조 무결성만 검증하고 **선택 섹션은 열거하지 않음** → plan-lint 수정 불필요(당초 필요하다고 본 것을 정정).
- 2026-09-07: 동기화 지점 전수 스윕을 workflow(`intent-section-survey`, 7 agents)로 실행 — 5갈래 병렬 + 문체 규약 추출 + 누락 비평. 후보 63건 중 mustChange 11곳. 비평이 스윕의 편향("모두 같은 모달리티로 수렴")을 잡아내 `wiki/index.md`(hook 기계적 필수)·`wiki/log.md`(WIKI.md:43)·선행 wontfix·구속 결정을 추가로 발굴. 직접 grep 으로 9번째 지점(`unknowns-discovery.md:18`)을 더 찾음.
- 2026-09-07: 편집 9파일 완료(24줄). 로컬 CI 동등 스위트 OVERALL PASS.
- 2026-09-07: diff 적대적 리뷰 workflow(`intent-section-review`, 69 agents) 실행 — 6렌즈 × 반박 3인. 21건 중 confirmed 1건이나, **여러 렌즈가 독립 지목한 항목**은 개별 반박과 무관하게 실물 대조 후 4건 반영. 반박자 3명이 API safeguard 오류로 실패해(`style`·`precedent`·`doc-drift` 각 1) 그 렌즈는 2표로 판정 — `kept >= 2` 기준상 기각 편향이 있었다.
- 2026-09-07: 리뷰 반영 후 재검증 OVERALL PASS + `check_links.py` clean. 커밋 `d2ec8df`, PR #162.

# Next

(없음 — PR #162 머지로 종료)

# Decisions

- **선행 wontfix 를 supersede 한다 (가장 중요)** — `plans/2026-07-07-unknowns-pass/unknowns-pass-plan.md:26` 이 거의 같은 아이디어를 기각했다: *"plan 에서 바뀔 결정 앞세우기"(§10 6섹션 구조와 충돌 — `# Decisions`·AskUserQuestion 승인 흐름이 이미 결정 지점을 노출, 이득 대비 구조 변경 큼 → wontfix)*. 이번에 채택하는 근거는 셋:
  1. 기각 사유 "6섹션 구조와 충돌" 은 해당 없음 — `# Intent` 는 **선택 섹션**이라 필수 6 이 불변이고, `# Intent` 를 담은 plan 이 `plan-lint` 를 통과함을 실측했다.
  2. 기각 사유 "`# Decisions` 가 이미 결정 지점을 노출" 은 *결정*에 대해선 참이지만, `# Intent` 가 담는 것은 결정이 아니라 **문제·제약·범위 밖**이다. 둘의 경계는 제약이냐 아니냐가 아니라 **시점**이다 — §10:175 대로 *진행 중 새로 발견한* 제약은 그대로 `# Decisions`(변경 + 이유)로 가고, `# Intent` 는 *착수 전 확정한* 요구를 담는다. 착수 전 제약은 지금까지 어느 섹션도 담지 않았다.
  3. 기각 사유 "이득 대비 구조 변경 큼" 에 실측 반례가 생겼다 — 2026-09-07 `settings.json` 작업에서 제약 미기록으로 같은 선택지가 3회 제시·기각됐다. 변경 범위도 §10 한 줄 + dlc 절 보강으로 작다.
- **정의는 `CLAUDE.md` §10 에 둔다 (dlc 단독 배치 기각)** — `wiki/pages/decision/ops-doc-slimming.md:36` 의 구속 결정: *"조건부-로드 skill 이 참조하는 canonical always-injected 스펙(예 CLAUDE.md §10 plan frontmatter/6섹션)을 그 skill 로 이관하는 것은 방향 역전 … 참조원이 조건부 로드라 그 skill 미호출 세션은 스펙을 잃는다(로드 등급 하락 = 손실)"*. dlc 는 조건부 로드라 정의를 거기 두면 rule-loss.
- **§10 + dlc 2파일 분할** (이유: `# Acceptance` 선례 — §10 은 한 줄 정의 + 절차 소유자 이름만, dlc 는 절차만. 서술 중복 금지).
- **별도 `intent/` 홈 미도입** (이유: §10 의 "plan = 단일 진실 소스"와 충돌, 산출물 이원화는 drift 원인).
- **plan-lint 미수정** (이유: 선택 섹션은 검증 대상이 아님 — 코드 확인. `plan-lint` 검사 항목을 재서술하는 4곳(`README:414`·`skills/{c,e,improve}`)도 따라서 불변임을 확인).
- **dlc 16단계 표 미수정** (이유: Intent 는 요구사항 명확화(규모 gate 직후) 산출물이라 `3 draft plan` 행에 넣으면 시점이 어긋난다).
- **dlc 체크리스트를 원문자에서 `1)` 표기로 전환** (이유: CLAUDE.md §0 은 새로 쓰는 문장에 원문자를 금지한다. 인접 스타일을 흉내 내 ⑤⑥ 를 덧붙이는 것이 아니라 규칙을 따른다).
- **subagent 리뷰는 workflow 로 대체** — 이 세션은 ultracode 라 Workflow 도구로 다관점 검토를 돌린다.

# Key Files

스윕 + 비평으로 확정한 편집 대상 9곳. 선례 커밋 `05fb6dc`(`# Acceptance` 도입)의 파일 집합과 일치한다.

- `CLAUDE.md` — §10 "선택 섹션" 줄(202)
- `skills/dlc/SKILL.md` — "요구사항 명확화" 절(41~47), 체크리스트(43)
- `docs/dlc-details.md` — "체크리스트 4항" 재서술 2곳(8·10)
- `README.md` — CLAUDE.md 섹션 요약의 §10 줄(244)
- `wiki/pages/concept/plan-handoff.md` — 선택 섹션 열거(17). **기존 부분 drift 동반 수정**: 현재 목록에 `# Acceptance`·`# Workflow Findings` 가 빠져 있다
- `wiki/pages/concept/dlc-development-cycle.md` — 요구사항 명확화 게이트 요약(27)
- `wiki/pages/concept/unknowns-discovery.md` — "체크리스트 4항" 재서술(18)
- `wiki/index.md` — `wiki/pages/**` 편집은 `dlc-doc-drift.js:38` 이 index-trigger 로 분류하므로 **기계적 필수**
- `wiki/log.md` — `wiki/WIKI.md:43` "모든 ingest 는 log.md 에 append" 규약

수정하지 않음(확인 완료): `scripts/plan-lint.js`(선택 섹션 미검증), `README:414`·`skills/{c,e,improve}/SKILL.md`(plan-lint 검사 항목 재서술 — Intent 에 lint 없으므로 그대로 참), `skills/dlc/SKILL.md:66`(16단계 표 — 시점 불일치), `wiki/pages/concept/plan-handoff.md:16`("6섹션" 소제목 — 필수 6 불변).

# Blockers

(없음)

# Review Disposition

`intent-section-review` workflow(6렌즈 × 반박 3인, 21 findings). 반박 통과는 1건뿐이나 **독립 렌즈 다수가 같은 것을 지목한 항목**을 실물 대조해 처분했다.

- `fix` — dogfooding plan 의 `# Intent` 가 스펙에 없는 `## Proposed outcome` 을 씀(4렌즈 지목). 제거 — 내용은 `# Goal` 이 담고, 두면 같은 커밋이 새로 박은 `# Intent` ≠ `# Goal` 구분을 첫 예시부터 어긴다.
- `fix` — dlc 지시에 plan 부재 스코프 누락(3렌즈 major). `small` 은 16단계 표에 `draft plan` 행이 없어 plan 이 없을 수 있다. 선례 `# Acceptance` 의 `(draft plan 시)` 를 본떠 `(plan 이 있으면 그때, 없으면 draft plan 시)` 추가.
- `fix` — wiki 3페이지 `updated:` stale(유일한 confirmed, 5렌즈 지목). 2026-09-07 로 갱신. 반박자가 "미갱신 선례 17건" 을 들었으나 값이 사실과 다른 것은 그대로다.
- `fix` — 외부 출처가 `plans/`(종료 시 닫힘)와 append-only `log.md` 에만 남음. `wiki/pages/source/ai-native-sdlc-playbook-intent.md` 신설 + index 등재 + `plan-handoff.md` `sources:` 등재. `unknowns-pass` 가 `source/fable-field-guide-unknowns.md` 를 만든 선례와 동형이고, 이 변경이 막으려는 문제("근거가 사라져 기각안이 되살아난다")를 스스로 재현하지 않기 위함.
- `false-positive` — "dlc 가 §10 필드명을 재서술해 단일 소스 위반"(0/3). 선례인 `# Acceptance` 도 dlc 에서 3요소 형식을 그대로 적으므로 선례 위반이 아니다.
- `wontfix` — "§10 에 Constraints 라우팅 규칙 추가"(0/3). §10:175 는 *진행 중 새 제약* → `# Decisions`, `# Intent` 정의는 *착수 전 확정한 요구* 로 이미 시점이 갈린다. 항상 주입되는 CLAUDE.md 를 더 늘리지 않는다([[ops-doc-slimming]] 의 로드 등급 원칙). 대신 이 plan `# Decisions` 의 부정확한 서술("`# Decisions` 는 제약을 담지 않는다")을 시점 기준으로 정정했다.

# Acceptance

1. `CLAUDE.md` §10 선택 섹션 목록에 `# Intent` 가 기존 항목과 같은 표기 규약으로 포함 — 검증: 해당 줄 육안 대조
2. `skills/dlc/SKILL.md` 요구사항 명확화 체크리스트에 Problem·Constraints 축이 추가되고, 결과를 plan `# Intent` 에 기록하라는 연결이 명시 — 검증: 해당 절 확인
3. §10 과 dlc 가 같은 내용을 중복 서술하지 않고 역할이 갈림(단일 소스) — 검증: 두 문단 대조
4. 스윕·비평이 지목한 mustChange 지점이 빠짐없이 반영 — 검증: 목록 대조
5. `node scripts/plan-lint.js <이 plan>` 통과 (`# Intent` 가 필수 6섹션 검증을 깨지 않음) — 검증: 실행
6. CI 동등 스위트 통과 — 검증: 실행
7. 문서 drift 없음(README·wiki index 동기화) — 검증: 대상 파일 확인

# Deferred

- playbook 의 후행 지표(survival rate — Design 단계로 넘어간 intent 비율, spec 커밋 후 intent 변경 횟수)는 `/improve` 의 신호 축으로 쓸 여지가 있으나 이번 범위 밖.
- Playbook 나머지 5단계(Design·Build·Test·Deploy·Maintain)와 현재 설정의 격차 분석 미실시.

# Workflow Findings

(없음)
