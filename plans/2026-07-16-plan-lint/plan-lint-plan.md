---
title: plan-lint — plan 참조 무결성 기계 검증 (Workstream E)
status: in_progress
started: 2026-07-16
updated: 2026-07-16
---

# Goal
plan(§10) 무결성이 "모델 주의력"에만 의존하던 것을 기계 게이트로 이관한다. `scripts/plan-lint.js` 순수 판정 + CI(PR) + skill(/c·/e·/improve) 통합으로 frontmatter·섹션·**끊긴 내부 참조**를 자동 검출한다. 의미 판정(title↔Goal 정합 등)은 LLM 몫으로 남긴다.

# Progress
- 2026-07-16 (opus, 착수): plan-lint worktree 진입·baseline 7 test green. Explore — dlc-doc-drift.js(순수판정+exports 선례)·plan 실형태·참조패턴(①②·P4·# Acceptance) 확인. **발견: plans-sync(#83)가 .gitignore 만 un-ignore, plan 파일 미커밋(tracked 0) → CI 는 plan 커밋 시 유효화**(Deferred). 사용자 스코프 확정(CI+스킬통합). draft plan 작성.
- 2026-07-16 (opus, 구현 완료): dlc 전체 — plan-review(codex 5 Major+Minor·Claude CONDITIONAL 반영)→TDD Red→구현(scripts/plan-lint.js 순수+CLI)→Green→통합(lint.yml diff기반 CI·/c 2·/e 3·improve.sh check8·README)→code-review(codex Major3·Claude Major 실증 false-negative)→fix loop 2회(apostrophe silent-miss·CI fetch·혼합run·한글 non-empty·frontmatter H1)→simplify(변경0)→최종검증. **plan-lint.test.js 27/27 PASS·dogfood clean·improve.sh check8 [ok]·baseline 전건**. 이 plan 을 tracked 커밋해 dogfood(CI/improve 실대상). status: 구현 done, 머지 대기.

# Next
구현·리뷰·검증 완료. **다음: push + PR → 머지**(사용자 확인, §8). 머지 후 이 plan(dogfood)이 tracked 로 남아 CI/improve check8 의 실대상. Deferred 의 plans-sync 완결(기존 plan 커밋)은 별건.

# Decisions
- **scripts/plan-lint.js = 순수 모듈 + CLI** (dlc-doc-drift 패턴 + dlc-signal CLI 패턴): `lintPlan(text)`→위반 문자열 배열(빈=clean) export + `require.main===module` 시 파일 인자 CLI(위반 출력·있으면 exit 1). 파일 IO 는 CLI 만, 판정은 순수(테스트 용이).
- **검사 4종** (순수·기계적만; 의미 판정 제외):
  1. frontmatter 필수키 `title·status·started·updated` **non-empty**(값 있음, `\w`; RP4). frontmatter 파싱 `\r?\n`(CRLF).
  2. `status` ∈ {in_progress, blocked, done}.
  3. 6 섹션 헤더 `# Goal·Progress·Next·Decisions·Key Files·Blockers` 존재 — **H1(`^# `) 고정**(`## Goal` 은 위반; 선택 섹션은 무관, RP4).
  4. **Acceptance 참조 무결성(핵심)**: 본문(frontmatter·헤더 라인·`# Acceptance` 섹션 본문 **제외** — 자기참조 오탐 방지)에서 `Acceptance` 뒤 같은 run 의 숫자/원문자를 **전부** 추출(M2: "⑤⑥"→{5,6}). 원문자는 ①-⑳(U+2460~)만 지원, ㉑+ 는 "미지원 참조 형식" 위반(m2). 단, **계량사(개/종/줄) 뒤따르는 숫자는 참조 아님**("Acceptance 3개 항목"의 3 배제, RP5). 참조 N 이 있으면 `# Acceptance` 섹션 존재 + top-level 항목 수 ≥ N, 아니면 위반. 항목 수 = **`# Acceptance` 섹션 내(다음 `^# ` 헤더 전까지, RP3)**의 `^\s*\d+\.\s+` 라인 수(M3: dot escape·sub-item ⓐ·타 섹션 숫자라인 제외).
- **§N 참조는 검사 안 함** — CLAUDE.md 섹션(외부) 참조라 plan 구조 대상 아님(오탐 방지).
- **강제 지점(사용자 확정 = CI + 스킬)**:
  - (a) CI: lint.yml 에 **그 PR 에서 변경된 plan 만** lint — `git diff --name-only <base>...HEAD -- 'plans/*/*-plan.md' | xargs -r node scripts/plan-lint.js`(RP1: legacy plan 이 무관 PR 차단 방지·`-r` 로 0개→exit 0). **`continue-on-error: true`(초기 비차단, RP2)** + `CLAUDE_PLAN_LINT_OFF` env 게이트(CLI 초입, RP2). node --check + .test.js 실행 등록.
  - (b) 스킬 통합: **improve.sh 1단계 = 전 tracked plan lint**(M5/RP6: 셸엔 active-plan 개념 없음). **/c 2단계 = 채택 plan·/e 3단계 = active plan(plan write *후*, RP6)** 대상. **/c·/e 위반은 노출·보정(hard-stop 아님, RP6)**.
- **dogfood**: 이 plan 자체를 tracked plan 으로 커밋(§10) → plan-lint 첫 검증 대상. 그러므로 이 plan 은 plan-lint-clean 유지.

# Key Files
- scripts/plan-lint.js (+.test.js) — 신규 (순수 판정 + CLI)
- .github/workflows/lint.yml — plan-lint 스텝·node --check·test 등록
- skills/c/SKILL.md 2단계 · skills/e/SKILL.md 3단계 · skills/improve/improve.sh 1단계 — 통합
- README.md — plan-lint 절 동기화

# Blockers
(없음 — 즉시 착수. CI 실효는 plans 커밋에 의존하나 그건 별건, plan-lint 는 독립 유효.)

# Acceptance
1. TDD plan-lint.test.js (node·fixture 문자열): ⓐ valid plan → clean(위반 0) ⓑ frontmatter 키 누락 → 위반 ⓒ status 값 오류 → 위반 ⓓ 6섹션 중 누락 → 위반 ⓔ "Acceptance 5" 인데 항목 3개 → 위반 ⓕ "Acceptance ⑤" 원문자 → 정확히 5 로 해석 ⓖ "Acceptance 2" 인데 항목 3개 → clean ⓗ # Acceptance 섹션 없는데 "Acceptance 1" 참조 → 위반 ⓘ §8 등 §N 참조 → 무시(오탐 없음) ⓙ **# Acceptance 섹션 내부의 "Acceptance N" 자기참조 → 스캔 제외(오탐 0, M1)** ⓚ **"Acceptance ⑤⑥" → 5·6 둘 다 검사(M2)** ⓛ **㉑ 등 ①-⑳ 밖 → "미지원 형식" 위반(m2)** ⓜ **"1x." 같은 라인은 항목 미카운트(`^\s*\d+\.\s+`, M3)** ⓝ **# Progress 등 타 섹션의 숫자 시작 라인은 Acceptance 항목으로 미카운트(섹션 경계, RP3)** ⓞ **CRLF plan 정상 처리(RP4)** ⓟ **빈 frontmatter 값(`title:`) → 위반(RP4)** ⓠ **`## Goal`(H2) → 섹션 누락 위반(H1 고정, RP4)** ⓡ **"Acceptance 3개 항목" 계량사 → 참조 아님·clean(RP5)**.
2. CLI: `<valid.md>` → exit 0·무출력; `<broken.md>` → exit 1·위반 파일명+사유; 인자 0개 → exit 0; **다중 파일(valid+broken) → broken 만 출력·exit 1(파일별·exit 집계, RP7)**; **미존재 경로 → skip+경고, ENOENT 크래시 없음(RP7)**; **`CLAUDE_PLAN_LINT_OFF=1` → 무출력 exit 0(RP2)**.
3. dogfood: 이 plan 을 **커밋해 tracked 화** → `git ls-files 'plans/**/*-plan.md'` 에 포착됨 + `node scripts/plan-lint.js <이 plan>` → clean (m3: "CI 강제"가 실제로 ≥1 plan 을 대상 삼음).
4. lint.yml: node --check plan-lint.js/.test.js OK, .test.js PASS. plan-lint 스텝은 **변경 plan 만**(diff 기반, RP1) + `continue-on-error: true`(RP2). 로컬에서 diff 명령·CLI 파이프 재현.
5. 통합: /c 2단계·/e 3단계·improve.sh 1단계 서술에 plan-lint 호출 반영 + README 동기화. improve.sh 실행 시 error=0.
6. 기존 테스트 전종 비회귀.

# Deferred
- **plans-sync(#83) 미완**: `.gitignore !/plans/` 로 un-ignore 됐으나 기존 plan 파일이 미커밋(`git status`=`?? plans/`, tracked 0). plan-lint CI 가 실효하려면 plan 들을 커밋해야 함 — 별건(plans-sync 완결). severity: medium. plans/ 전반.

# Review Disposition
**codex 0.134.0 (2026-07-16, medium) — plan-review:**
- **M1 [fix] 스캔 범위**: Acceptance 참조 스캔이 frontmatter·헤더 라인·`# Acceptance` 섹션 본문을 **제외**(섹션 내부 자기참조 오탐 방지). 테스트 추가.
- **M2 [fix] 연속 원문자**: "Acceptance ⑤⑥" 처럼 `Acceptance` 뒤 같은 run 의 숫자/원문자를 **전부** 참조로 추출(첫 토큰만 잡으면 ⑥ 누락).
- **M3 [fix] 항목 카운트 regex**: `^\d+.`(dot 미escape → "1x" 오탐) → `^\s*\d+\.\s+`. sub-item(ⓐ) 제외 유지.
- **M4 [fix] CI 산출**: bare glob 은 0매치 시 literal→ENOENT. → `git ls-files 'plans/**/*-plan.md' | xargs -r node scripts/plan-lint.js`(`-r`=빈 입력이면 미실행 → tracked 0 → exit 0 보장).
- **M5 [fix] skill 통합 경로**: improve.sh(셸)엔 세션 active-plan 개념 없음 → improve.sh 는 **전 tracked plan lint**(CI 와 동형). /c(채택 plan)·/e(active plan)만 특정 plan 대상.
- **m1 [accept]** §N·끊긴 #섹션 참조 제외는 타당(scope creep 방지) — 별 workstream.
- **m2 [fix]** 원문자 경계: ①-⑳ 지원, ㉑+ 는 무시 아니라 **"미지원 Acceptance 참조 형식" 위반**(누락 축소).
- **m3 [fix]** dogfood: 이 plan 을 실제 커밋해 tracked 화 + Acceptance 에 `git ls-files` 포착 확인 추가(안 그러면 "CI 강제" 과장).

**Claude plan-reviewer (2026-07-16, CONDITIONAL) — 신규:**
- **RP1 [fix] #83 상호작용(영향범위 갭)**: CI 가 전 tracked plan 을 매 PR lint 하면 plans-sync 가 legacy plan 커밋 시 오래된 plan 하나가 **무관한 모든 PR merge 를 차단**. → CI 는 **그 PR 에서 변경된 plan 만** lint(`git diff --name-only <base>...HEAD` ∩ `plans/*/*-plan.md`). improve.sh 는 전수(수동 감사라 무관).
- **RP2 [fix] rollback 부재**: 동류(dlc-doc-drift/signal)는 다 `CLAUDE_*_OFF` kill-switch. plan-lint CI 엔 없음. → `CLAUDE_PLAN_LINT_OFF` env 게이트(CLI 초입 체크→무출력 exit 0) + CI 스텝 **`continue-on-error: true`(초기 비차단 도입)**. required check 여부 불명이라 비차단 시작이 안전.
- **RP3 [fix] 항목 카운트 섹션 경계**: `^\s*\d+\.\s+` 를 **`# Acceptance` 섹션 내(다음 `# ` 헤더 전)로 한정** — # Progress 등의 숫자 시작 라인 누출 방지. 테스트 추가.
- **RP4 [fix] 검사1 빈값·CRLF·H1**: 필수키는 **non-empty**(`\w`, dlc-signal 선례). frontmatter 정규식 `\r?\n`(CRLF). 섹션 헤더는 **H1(`^# `) 고정**(`## Goal` 은 위반).
- **RP5 [fix] 계량사 오탐**: "Acceptance 3개/종/줄" 의 3 은 참조 아님 → 계량사 뒤따르면 배제.
- **RP6 [fix] skill 실패 처리**: /c·/e 는 LLM 오케라 **위반=노출·보정(hard-stop 아님)** 명시. **/e 는 plan write *후* lint**(write 전은 stale). improve.sh=전수(RP/M5 합의).
- **RP7 [fix] CLI 견고성**: 다중 파일 인자(파일별 출력·exit 집계) + **미존재 경로는 skip+경고**(ENOENT 크래시 금지). `xargs -r`+`git ls-files`(존재 파일만)로 CI 는 미존재 안 넘김.
- [confirmed] §N/#섹션 제외 타당(검사3 이 6섹션 보장→dangling 불가). 원문자 ⑳ 경계 minor.

**codex 0.134.0 code-review (2026-07-16, medium) — 구현 후:**
- **CM1 [fix] CI fetch**: `git fetch origin $BASE` 는 origin/BASE ref 미생성(FETCH_HEAD 만) → `git diff origin/$BASE` unknown revision → continue-on-error 로 조용히 미실행. → 명시 refspec `$GITHUB_BASE_REF:refs/remotes/origin/$GITHUB_BASE_REF`.
- **CM2 [fix] xargs -r GNU 전용**: macOS improve.sh 에서 BSD xargs 가 `-r` 미지원→깨짐. `[ -z "$plans" ]` 가드가 이미 있어 `-r` 제거(빈 입력→node 무인자→exit 0). lint.yml 도 제거(통일).
- **CM3 [fix] 혼합 run 숫자 무시**: "Acceptance 21①" 가 21 버리고 1만 검사 → 누락. 혼합·㉑+ 는 **미지원 위반**(조용히 안 버림). 테스트 ⓣ.
- **Cm1 [fix] 한글 non-empty**: `/\w/` 가 `title: 계획 정리`(한글-only) 를 빈값 오탐(한국어 repo!). → `.trim()` 비어있음 판정. 테스트 ⓢ.
- **Cm2 [fix] h1Sections frontmatter 포함**: YAML 내 `# ...` 가 본문 H1 누락 가림. → fmEnd 후 라인만 스캔.
- 재검증: plan-lint.test.js 26/26 PASS·dogfood rc0·improve.sh check8 [ok].

**Claude code-reviewer (2026-07-16, REQUEST CHANGES→해소) — 구현 후:**
- **RC-M1 [fix] 실증 silent false-negative**: `'[^']*'`(작은따옴표) span 제거가 **개행 넘어** 매칭 → 산문 소유격·축약(`plan's`·`wasn't`) 사이에 낀 정당한 "Acceptance N" 참조를 통째로 삼켜 **조용히 미검출**(실증: `plan's bug, Acceptance 5 참조, wasn't` → `[]`). → **apostrophe span 제거 삭제**(delimiter 로 신뢰 불가) + 백틱·큰따옴표를 **라인 내(`[^"\n]`)로 국한**(개행 넘는 삼킴 차단). 회귀 테스트 ⓤ(Red→Green 실증: 수정 후 `["Acceptance 5 …항목 2개뿐"]`).
- **RC-m1 [fix] CI refspec 보강**: `+refs/heads/$BASE:refs/remotes/origin/$BASE`(force·명시 dest — checkout depth1 에서도 origin/BASE 생성 보장).
- **RC-nit [fix] H2~H6 미제외**: scannableText 를 `^# ` → `^#{1,6} ` 로(모든 헤더 라인 제외).
- **[미채택] 미등록 계량사(단계/번)·per-ref unsupported·원문자+계량사**: over-flag(노출) 방향이라 silent 아님 + 빈도 낮음 → wontfix(노이즈 감수). 
- **[confirmed 실측]** macOS `xargs -r` 실은 정상(BSD `--no-run-if-empty` 호환) — 단 codex CM2 대로 `-r` 제거는 유지(가드 있어 무해·통일). shellcheck 는 CI 커버. check 8 `while <<<"$out"` here-string 안전(subshell 아님·warn 카운트 보존).
- 재검증: plan-lint.test.js **27/27 PASS**(ⓤ 포함)·apostrophe 케이스 위반 검출·dogfood rc0.

# Workflow Findings
(발생 시 기록)
