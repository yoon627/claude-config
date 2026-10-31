# 가리키는 곳 (translate-skill-dlc)

dlc 의 절 이름·라벨을 가리키는 곳을 `rg` 로 찾았다(repo 는 worktree, `plans/` 제외 · 공용 wiki 는 `/root/.claude/wiki` 의 `pages/`·`docs/`·`index.md`·`WIKI.md` — `log.md` 는 역사 기록이라 그대로). 단계 번호 0~16 은 유지했으므로 "dlc 13단계"·"dlc step 4" 같은 번호 포인터는 모두 맞다. 원문자(①②③)를 가리키는 곳은 없다. dlc 문구를 글자로 assert 하는 테스트는 없다(`dlc-task-router.test.js` 는 태그 `[dlc:investigation]`·`[dlc:grounding]` 만 본다).

한국어 파일은 한국어 문장을 두고 가리키는 라벨만 바꾼다.

## 이 머지에서 고칠 곳 — 없음
- `CLAUDE.md`(영어): "dlc self-check"·"dlc size table"·"dlc step 13"·"commit units"·"step 16 commit rules"·"dlc evidence gate and fix loop"·"dlc split judgment (exception)"·"dlc requirement clarification"·"dlc's evidence-based self-improvement"·"dlc ⚠️ self-flag" — 번역본의 "self-check"(28줄)·"size table"·"Commit units"·"**Commit (step 16 …)**"·"Split judgment"/"Exception"·"Requirement clarification"·"Workflow Findings (evidence-based self-improvement)" 과 맞는다.
- `agents/plan-reviewer.md`·`agents/architecture-reviewer.md`·`agents/researcher.md`(영어): "dlc step 3/4/13"·"`skills/dlc/SKILL.md` requirement clarification"·"dlc split judgment exception"·"## Summary for the plan" — 맞다. plan-reviewer "item 15" ↔ 번역본 "`agents/plan-reviewer.md` item 15".
- `skills/wt`·`skills/e`·`skills/c`·`skills/commit-check`·`skills/improve`·`skills/wiki`(영어): "size gate"·"step 16 commit"·"dlc Report"·"dlc integration"(wiki skill 자신의 표현) — 맞다.
- `scripts/dlc-early-stop.js:190` "(dlc evidence gate 보조)" — 맞다.

## 다른 단위가 고칠 곳
- `agents/code-reviewer.md`(translate-agent-code-reviewer, 이 단위보다 먼저 머지): 49줄 `Report "읽을 곳" 출처` → `Report "Where to read"` 출처. 142줄 `## plan 반영용 요약` 은 그 단위가 "Summary for the plan" 으로 옮긴다 — 그 머지 뒤라야 dlc 영어본이 한국어 옛 이름을 지운 것이 맞다(terms.md). code-reviewer 가 출력하는 태그 `[plan 대비]`·입력 표지 `⚠️ (구현)` 은 두 단위 모두 원문 유지 — 글자가 같아야 한다.
- `scripts/dlc-task-router.js`(translate-hooks — 이 단위 Out of scope): 51줄 `(skills/dlc/SKILL.md 조사 프로토콜)` → `(skills/dlc/SKILL.md Investigation protocol)`, 57줄 `… verification grounding + 요구사항 명확화 '프로토타입-우선')` → `… verification grounding + Requirement clarification 'prototype-first')`. hook 이 바뀌기 전까지는 한국어 라벨로 영어 절을 가리킨다(찾기는 가능 — 뜻이 같다).
- `~/.claude/wiki/docs/dlc-details.md`(translate-wiki-docs — Out of scope): 7줄 `(SKILL 요구사항 명확화)` → `(SKILL Requirement clarification)`, 14줄 `(SKILL 조사 프로토콜 — …)` → `(SKILL Investigation protocol — …)`, 20줄 `(SKILL wiki 연계, …)` → `(SKILL wiki integration, …)`, 32·34줄 `SKILL 격리 경계` → `SKILL Isolation boundary`, 28줄(선택) 하위 라벨 → recording triggers · proposal on repetition · self-modification boundary.

## README(한국어, 언어 정책 밖 — 라벨만, 이 머지 또는 후속)
- 282줄 `dlc 분할 판정이` → `dlc Split judgment 이`
- 316줄 `묶음 모드(dlc 분할 판정의 # Plans 경계 — 15항)` → `dlc Split judgment 의`
- 334줄 백틱 인용 `` `evidence gate → 판정(DONE/BLOCKED/NEEDS-HUMAN) → plan 업데이트 → 정식 완료 커밋(DONE 만) → commit-check → 알림(필요할 때 최대 1회) → Report` `` — 번역본 16단계 글자와 다르다. 영어 글자 `` `evidence gate (…) → verdict (DONE/BLOCKED/NEEDS-HUMAN) → plan update → formal completion commit (DONE only) → commit-check → notification (at most once, when needed) → Report` `` 로 바꾸거나 백틱을 빼 설명문으로
- 335줄 `**Report "읽을 곳"**`·`` `## 읽을 곳` 블록 `` → `Report "Where to read"`·`` `## Where to read` 블록 ``, `확인 필요:` → `Needs confirmation:`(사용자에게 보이는 Report 에서는 CLAUDE.md §0 대로 한국어로 쓴다는 점은 같다)
- 그대로: 310·383줄 `dlc 13단계`·`dlc 16단계` · 327줄 self-flag 요약 · 332줄(dlc-details 의 한국어 절 이름) · 333줄 `커밋 단위:` · 457·458·460줄

## [post-merge] 공용 wiki — main 세션
- `pages/concept/plan-handoff.md`: 28줄 `dlc 요구사항 명확화가` → `dlc Requirement clarification 이`, 39줄 `dlc 요구사항 명확화의 **분할 판정**` → `dlc Requirement clarification 의 **Split judgment**`, 45줄 `"plan 반영용 요약"(영어로 옮긴 agent 는 "Summary for the plan")` → `"Summary for the plan"`
- `pages/concept/hub-and-spoke-isolation.md`: 7줄 `(격리 경계)` → `(Isolation boundary)`, 13줄 두 이름 → `"Summary for the plan"`
- `pages/concept/dlc-development-cycle.md`: 32줄 `` `## 읽을 곳` `` → `` `## Where to read` ``·`확인 필요:` → `Needs confirmation:`, 35줄 `skills/dlc/SKILL.md 요구사항 명확화가 정본` → `Requirement clarification 이 정본`, 30줄 제목(선택)
- `pages/concept/unknowns-discovery.md`: 19줄 `요구사항 명확화 게이트` → `Requirement clarification 게이트`, 21줄 `명확화 절 "blind-spot pass"` → `Requirement clarification 절 "blind-spot briefing"`, 22줄 `명확화 절 프로토타입-우선` → `Requirement clarification 절 prototype-first`, 24줄 `Report "읽을 곳"` → `Report "Where to read"`
- `pages/decision/dlc-wt-autoflow.md` 7줄 `(진입 매트릭스·dlc→wt)` → `(Entry matrix·dlc → wt)`
- `pages/decision/self-diagnosis-and-improvement-status.md` 7줄 `(자기 진단)` → `(Self-diagnosis)`
- `pages/decision/evidence-gate.md` 19줄 `Report "읽을 곳"` → `Report "Where to read"`
- `pages/decision/fablize-adopted-disciplines.md` 20줄 `dlc 조사 프로토콜` → `dlc Investigation protocol`
- `pages/decision/workflow-failures.md` 55줄 `` `skills/dlc/SKILL.md` 분할 판정 `` → `Split judgment`(같은 줄의 "dlc 분할 판정 예외" 는 역사)
- `pages/decision/lesson-verify-scaffold-purpose-before-removal.md` 74줄 `` `skills/dlc/SKILL.md` wiki 연계 `` → `wiki integration`
- `pages/decision/lesson-parallel-duplicate-implementation.md` 63·69줄 `dlc 요구사항 명확화` → `dlc Requirement clarification`
- `pages/decision/risk-based-approval.md` 34줄 `dlc 요구사항 명확화` → `dlc Requirement clarification`
- `pages/decision/native-overlap-ledger.md` 56줄(선택) `dlc 규모 gate` → `dlc Size gate`
- 그대로: `index.md` 9·15줄(요약 산문), 각 페이지 자신의 제목(`## 진입 매트릭스`·`## 요구사항 명확화 게이트` 등), `ops-doc-slimming.md` 63줄(두 이름 시기의 역사), 단계 번호 포인터, `log.md`

## 원문 그대로 둔 문자열
- `⚠️ (구현)`·`[리뷰 미경유]` — plan `# Decisions`·log 에 한국어로 남는 표지, code-reviewer 가 입력에서 이 글자로 알아본다.
- `[plan 대비]` — code-reviewer 가 finding 에 붙이는 태그(그 단위도 원문 유지).
- `` `코드` ``·`` `둘 다` ``·`` `없음` ``(`[plan 대비]` 처분의 바뀐 쪽 값) — plan log 처분 줄에 쓰는 값이라 plan 표지와 같게(terms.md `없음 — <…>` 줄의 선례).
- `커밋 단위:`·`커밋 단위: 1개` — plan `# Decisions` 표지(자리표시자만 영어).
- `` `없음 — <one-phrase reason>` ``·`` `없음` `` — plan `# Goal` 라벨 불릿 표지(terms.md).
- `생략:` — `- [x] <step> (YYYY-MM-DD) — 생략: <reason>`, plan `# Tasks` 에 한국어로 남는 표지(같은 선례).
- `` `Codex 미가용: … out of credits` `` — reviewer 가 찍는 줄. 형식은 `~/.claude/wiki/docs/codex-review.md` §1(아직 한국어)이 정한다.

## 영어로 옮긴 사용자용 라벨
- `## 읽을 곳` → `## Where to read`, `확인 필요:` → `Needs confirmation:`, `미충족`/`미검증` → `unmet`/`unverified`, "미식별" → "unidentified" — 스크립트가 읽지 않고, 사용자에게 보이는 보고에서는 CLAUDE.md §0 대로 한국어로 쓴다("unverified" 는 terms.md 기계 대조 짝).
