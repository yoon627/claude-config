---
title: doc-slim — Workstream C: 주입·로드 문서 슬림화 (토큰 최적화, 규칙 손실 0)
status: done
started: 2026-07-04
updated: 2026-07-05
---

# Goal
매 세션/매 작업마다 로드되는 운영 문서의 토큰을 줄인다 — **규칙(제약·절차)은 하나도 잃지 않고** 산문·사례·3중 기술만 제거. 목표: 4대 타깃 합계 **30%+ 감소** (실측 기준선: CLAUDE.md 21,898B/216줄 · skills/dlc/SKILL.md 18,225B/147줄 · skills/e/SKILL.md 16,127B/100줄 · agents/architecture-reviewer.md 14,346B/186줄 = 70.6KB). 상위: `plans/2026-07-02-workflow-loopify/` Workstream C.

# Progress
- 2026-07-04: Fable 세션에서 실측·전략·수용기준 확정(이 plan). **구현은 opus 세션이 `/c` 로 이어받아 wt(slug `doc-slim`)→dlc 로 진행** — 사용자 모델 전략(memory `model-strategy-fable-plan-opus-impl`).
- 2026-07-04(opus): `/c` 로 이어받아 dlc structural 진입(이미 `doc-slim` worktree — self-check). **조사 완료**: docs/codex-review.md(codex 세부 완비)·wiki(`codex-bash-invocation`)·improve.sh 점검항목·CI lint.yml 확인. **plan-reviewer(+codex 병행, 46.7k tok) = CONDITIONAL** — blocker 4건(아래 Review Disposition). 편집 미착수 → `/e` 체크포인트. working tree clean(임시 커밋 없음).
- 2026-07-05(opus): `/c`→dlc 재개, **구현 완료**. ① 규칙 manifest 추출(scratchpad, 항상주입 등급 표시) ② docs/codex-review.md §3 codex-Bash MUST 선추가 + §4 양립 명시(이관처 확보) ③ 4파일 편집(CLAUDE §1~10 산문 압축·dlc-first 전환·§9 codex 세부 docs 참조화+안전문 잔존 / dlc 진입매트릭스·요구명확화·격리경계·자기진단·WF 압축 / e collect-state / arch codex 중복 4문단 docs 위임+"먼저 Read" 명령형 잔존·관점 예시 압축) ④ **사후탐지 #1(삭제라인 51줄 manifest 1:1 대조)·#2(핵심 문구 grep) → 규칙 손실 0 입증**. Acceptance #5(dlc-first 전환)·#8(step 4/12/13/15/16 불변) 통과. **감소 6.8%(70,596→65,810B) — #2(30%) 크게 미달**.
- 2026-07-05(opus, 2차): 사용자 "더 압축" 선택 → **dlc 전면 재작성**(B.1~B.16 41문구 grep 검증)·e 6단계·arch 심각도/관점·CLAUDE §11/§12 압축. **구현 후 리뷰: code-reviewer APPROVE(규칙 손실 0) + codex(규칙 손실 3건 지적)** → codex 3건 전부 fix(docs §1 환경이슈 fallback·CLAUDE Setup 레포작업·dlc 16단계 표 복원). B-defer #2(small 규모표 simplify 추가, §5 정합)·#6-1(wt SKILL codegraph staleness·projectPath — README 는 조회규칙 미문서화라 N/A) 반영. **최종 검증**: lint.yml 재현 RC=0(node·unit 3종·json)·improve error=0·shellcheck(shell 미변경 무영향). **감소 11.2%(70,596→62,706B) — 규칙 손실 0(hard gate) 충족, #2(30%) 미달은 규칙 밀도상 상한(4파일이 압축된 규칙 명세)**.
- 2026-07-05(opus): 커밋 `6b81a1a`(6 files, +157/-191) → push → **PR #73 머지 완료(main)**. `status: done`. 상위 `plans/2026-07-02-workflow-loopify/` Workstream C 완료 표시 대상.
- 2026-07-14(opus): 끊긴 세션 후속 마무리 — **wiki ingest 완료**([[ops-doc-slimming]] decision 신규 + evidence-gate 상호링크·index·log, check_links.py clean). worktree `doc-slim-wiki` 커밋 `77d13b3`(4 files). 상위 plan Workstream C 완료 마커도 정정.
- 2026-07-14(opus): **PR #78 머지 완료**(merge commit `102ec70`, rebase 불필요 — origin/main 과 wiki 파일 무겹침 확인). 원격+로컬 브랜치·worktree `doc-slim-wiki` 정리 완료, local main ff. **doc-slim 후속 전부 종결.**

# Next
편집·리뷰·simplify·검증·wiki ingest 완료 — **규칙 손실 0(hard gate), 감소 11.2%**. 남은 것:
1. ✅ 완료 — 커밋 `6b81a1a` → PR #73 머지(main).
2. ✅ 완료 — wiki ingest([[ops-doc-slimming]], worktree `doc-slim-wiki` 커밋 `77d13b3`). **push/PR 은 사용자 확인 대기**(§8: push 는 요청 시).

# Decisions
- **단일 소스 원칙**: 같은 규약이 CLAUDE.md·SKILL.md·README 에 3중 기술된 것은 **가장 상세한 곳을 단일 소스로 지정**하고 나머지는 1줄 참조로. 배분: 작업 절차 상세=skills/dlc(§3 은 원칙+참조만), codex 규약=docs/codex-review.md(§9 는 역할·매트릭스만), worktree 규칙=§8 로 단일화(§3-1 의 반복 서술 제거), plan 규약 §10=유지하되 압축(모든 세션에 필요해 위임 불가).
- **삭제 금지 원칙**: 규칙·제약·금지·트리거 조건은 표현만 압축하고 삭제하지 않는다. 삭제 대상은 ① 경위·배경 서술 ② 동일 규칙의 중복 기술 ③ 사례 나열(대표 1개만 유지) ④ 괄호 부연 중 자명한 것.
- **Opus 준수 고려**: 슬림화가 명시성을 해치면 역효과 — 각 규칙은 "명령형 1문장 + (필요시) 근거 1구"로. fablize 관찰(긴 산문 지시일수록 준수 저하)과 정합.
- **dlc-first 문구 전환** (사용자 요청 2026-07-03): CLAUDE.md §3-1·§8 의 "/wt(→dlc) 경유" 표현을 "dlc 진입(비trivial 이면 내부에서 wt 자동 경유)"로 — 기능 동일, 입구 서술만 정정.
- **B 에서 defer 된 3건 포함**: ① docs/codex-review.md §4(PowerShell fallback)에 "Bash 도구 부재 환경 한정 — §9 의 Bash 강제와 양립" 1줄 명시 ② dlc small 경로에도 simplify 체크 명시(§5 "모든 코드 변경 필수"와 정합) ③ agents/architecture-reviewer.md 의 codex 블록을 code/plan-reviewer 와 동일한 "절대경로 참조+선행 Read+고유 프롬프트만" 구조로 축약.
- **README 는 이번 범위 제외**: 주입되지 않아 토큰 무관, drift 표면 축소는 후속(우선순위 낮음). wiki 도 로드 조건부라 제외. (단 아래 codegraph 항목의 README 1줄은 예외 — 해당 절 정확성 수정)
- **[스코프 추가 2026-07-04] wt SKILL codegraph 절 정확화 (사용자 승인 — 기존 worktree plan 에 추가)**: `skills/wt/SKILL.md` 의 codegraph 인덱스 bullet(§4.6)에 실측 확인된 staleness 주의를 반영 — "**MCP 세션 기본 조회는 세션 시작 시점 인덱스에 고정**되어 EnterWorktree 이후·merge 반영 후에도 stale 할 수 있다 → codegraph 조회는 `projectPath`(현재 worktree 절대경로) 명시, 오래돼 보이면 그 repo 에서 `codegraph init` 재실행(비파괴)". 근거 실측(2026-07-04): 같은 커밋에서 기본 조회 17파일/172노드(세션 시작 전 스냅샷) vs projectPath 명시 20파일/221노드(정확). README 의 codegraph 언급부 1줄 동기화. 즉시 완화는 memory `codegraph-projectpath-explicit` 로 이미 주입 중 — 이 항목은 영속 반영. (선택) researcher 로 upstream @colbymchenry/codegraph 신버전의 cwd 추적 개선 여부 확인 후 있으면 업그레이드 권고만 기록.
- **RTK.md(1KB·untracked·머신로컬) 제외** — 효과 미미.
- **측정 방법**: 편집 전후 `wc -c` 4파일 합계. 토큰 환산은 근사(한국어 위주 ≈ bytes/2.5)로 참고만 — acceptance 는 bytes 기준.
- **[2026-07-05 opus] 30% 목표 미달 판정**: 규칙 손실 0(#1 hard gate) 유지하며 1차 압축한 결과 **6.8%**(65,810B). 4파일이 이미 **압축된 규칙 명세**라 산문·중복·사례·괄호부연을 걷어내도 이 수준.
- **[2026-07-05 opus] 사용자 결정: "더 압축 시도"**: 6.8% 가 목표와 괴리 커 규칙 통합/재구조화를 통한 추가 압축 선택. 방침 — 규칙 **의미는 보존**하되 (a) 중복·과세분 규칙 통합 (b) 예시·괄호부연·메타설명 대량 제거 (c) 여러 문장→한 문장. **CLAUDE.md 항상주입 규칙은 조건부 위임 여전히 금지**(로드 등급 하락=손실) — 내부 표현 압축만. SKILL/agent/docs 는 내부 통합·재구조화 허용. 손실 리스크는 사후탐지 3겹 + code-reviewer 로 방어. 목표 15~25%.

### [2026-07-04 리뷰 반영 — plan-reviewer(+codex) CONDITIONAL]
- **안전 규칙 잔존 원칙 (신설, 최우선)**: 실행/안전/트리거 규칙(§9 codex=Bash 강제, §3 dlc-필수·worktree-밖이면-wt-먼저, main 직접 금지 등)은 **조건부 로드 문서(skill/docs/wiki)로 위임 금지** — CLAUDE.md 에 명령형 1문장을 반드시 잔존시킨다. 이유: skill/docs 는 조건부 로드라 "규칙을 항상-주입에서 조건부-로드로 옮기는 것"도 손실(=항상 주입 손실). "규칙 손실 0" 정의에 *로드 등급 하락*을 포함한다.
- **§9 세부 이관은 docs 선보강 후에만**: docs/codex-review.md 에 현재 `hang`/`반드시 Bash`/`PowerShell 금지`가 **부재**(§3 "Bash 1차 경로"·§4 "PowerShell fallback"은 오히려 반대 뉘앙스). → docs §3 에 hang→Bash MUST 를 **먼저 추가**하고, CLAUDE.md §9 엔 안전 규칙 요지 1문장 잔존 후 세부만 참조화(dangling 방지). wiki `codex-bash-invocation` 은 sources=`CLAUDE.md §9`(§9 가 원천)이라 대체 근거 아님. → 편집전략 §1 의 §9 문구("경위는 wiki 에 이미 있음")를 이 원칙으로 대체.
- **Acceptance 재정렬**: #1(규칙 손실 0)이 **hard gate**, #2(bytes 30%)는 **#1 100% 통과 후 보조목표로 격하** — 30% 를 hard gate 로 두면 규칙을 참조화/배경위장으로 밀어내는 삭제 압력. 충돌 시 규칙 보존 우선(30% 미달해도 규칙 손실 0 이면 통과).
- **§10 "실패 사례 → wiki 이동"을 "삭제(경위)"로 정정**: 편집전략 §1 의 "§10 실패 사례를 wiki 로 이동"은 wiki 편집(범위 밖) 유발 → 실패 사례는 경위라 **삭제 허용 대상**이므로 "삭제"로 정정(active plan 추적 *규칙* 자체는 §10 에 잔존).
- **B-defer #2 는 압축이 아닌 순증**: small 경로에 simplify 단계 추가는 "규칙 손실 0" 범위 밖 동작 변경 → 정당하나(§5 정합) 규모 gate 표 일관성 미니 검증 별도.
- **hook 발동 예고**: 이 4파일 편집은 dlc-doc-drift(CLAUDE.md·SKILL.md 를 README 표면으로 판정)·early-stop hook 을 발동(fail-open — blocker 아님). 구현자 혼동 방지 예고. Acceptance #4 의 "테스트 무영향"은 hook JS 단위테스트 얘기지 이 경고와 무관.

# 편집 전략·순서 (구현 세션용 상세)
1. **CLAUDE.md (21.9KB → 목표 ≤14KB)**
   - §0·§1: 유지(핵심 규칙 — 압축만, 예: §1 각 bullet 의 괄호 부연 정리).
   - §2: "긴 명령 tool 파라미터 금지" 항목의 장문 사례 서술을 3줄로 압축(규칙+대응+재발 시 행동). `/clear`·`/rewind` 항목 압축.
   - §3: 표만 남기고 단계별 상세는 dlc SKILL 참조 1줄로. 문서 동기화 blockquote 압축. §3-1 dlc-first 전환. **단 "비trivial 코드 변경은 dlc 필수·worktree 밖이면 wt 먼저·main 직접 금지" 명령형 1문장 잔존**(안전 규칙 잔존 원칙). **"주석·docstring·commit message 가 현재 동작과 어긋나지 않게 확인"(§3-5) 규칙은 dlc 에 없으므로 삭제 금지 — CLAUDE.md 에 잔존**.
   - §5: B 반영 후 상태 유지, 표현 압축.
   - §8: worktree 규칙 단일화(§3 과 중복 제거), gitignored 삭제 경고는 유지.
   - §9: 역할·리뷰 매트릭스·공유 채널만 남기고 codex 호출 세부는 docs/codex-review.md 로 이동 후 참조. **단 "codex 는 Bash 도구로 호출(PowerShell 금지)" 안전 규칙 1문장은 CLAUDE.md 에 잔존**, 세부만 참조화. 이관 전 **docs §3 에 hang→Bash MUST 선추가**(현재 부재 — 리뷰 반영).
   - §10·§11·§12: 규약 유지, 사례·괄호 압축. §10 의 실패 사례 서술("실패 사례: 한 plan 작업 중...")은 **삭제(경위)** — wiki 이동 아님(범위 밖 회피). active plan 추적 규칙은 §10 에 잔존.
2. **skills/dlc/SKILL.md (18.2KB → 목표 ≤12KB)**: 진입 매트릭스·규모 gate·16단계 표·격리 경계·evidence gate 는 구조 유지. **step 번호(4/12/13/15/16) 불변**(외부 cross-ref — Acceptance #8). 각 절의 중복 상호참조("CLAUDE.md §x 의 구체화"류 반복)·괄호 부연·경위 서술 압축. wiki 연계·Workflow Findings·자기진단 절은 규칙만 남기고 배경 제거.
3. **skills/e/SKILL.md (16.1KB → 목표 ≤11KB)**: collect-state 필드 나열·폴백 명령 괄호가 대부분 — 폴백 명령을 표 1개로 통합, 각 조건의 산문 압축. ⚠️ 실측 기반 경고(ExitWorktree no-op·gitignored 삭제·EnterWorktree 거부)·묻힌 규칙(`dirty=unknown 생략`·`ExitWorktree no-op 강제이동 금지`·`이동 전 값 캡처`)은 규칙이므로 보존.
4. **agents/architecture-reviewer.md (14.3KB → 목표 ≤10KB)**: codex 블록 참조화(위 defer ③) + 검토 관점 8개의 예시 압축 + 출력 형식 유지. **"docs/codex-review.md 를 먼저 Read" 명령형 지시 잔존**(subagent 는 docs 자동 로드 안 함).
5. 문서 동기화: 변경이 README 서술(§5 요약·dlc step 번호 등)과 어긋나면 같은 브랜치에서 README 해당 줄만 갱신. wiki: [[dlc-development-cycle]] 등 요지 변화 없으면 무변경(구조 불변).

# Key Files
- CLAUDE.md · skills/dlc/SKILL.md · skills/e/SKILL.md · agents/architecture-reviewer.md — 4대 슬림화 대상
- skills/wt/SKILL.md — codegraph 절 정확화만(슬림화 대상 아님 — 스코프 추가분)
- docs/codex-review.md — §9 이관 수신 + §4 양립 문구 + **§3 에 hang→Bash MUST 선추가**(현재 부재)
- wiki/pages/decision/codex-bash-invocation.md — §9 원천이 CLAUDE.md(대체 근거 아님, 참고)
- scripts/dlc-doc-drift.js:40,62 — 편집이 이 hook 발동(fail-open)
- skills/improve/improve.sh · .github/workflows/lint.yml — 실존/형식·JS 테스트만, 의미 규칙 미검증 → 사후탐지 3겹 별도
- README.md:261,276 / architecture-reviewer.md:8,24 / wiki — `dlc 4/12/13/15/16단계` 번호 외부 참조(renumber 금지) + 어긋나는 줄만 최소 동기화
- (참고) plans/2026-07-02-workflow-loopify/ — 상위 plan, 완료 시 Workstream C 표시

# Blockers
(없음 — 리뷰 blocker 4건은 plan 보정으로 해소, 편집은 다음 세션에서 위 Next 순서로)

# Acceptance
1. **규칙 손실 0 (hard gate — 최우선, #2 보다 먼저)**: 편집 전 각 파일 규칙을 **삭제-diff 기반 manifest** 로 추출(키워드 목록만으로 부족 — 산문에 묻힌 규칙 다수). 각 규칙 = `ID · 원본 위치 · 새 위치 · 항상주입 여부 · (조건부면) 강제 Read 트리거 · 검증법`. 편집 후 전 항목이 (a) 잔존 또는 (b) 명시 단일 소스로 이동 + 참조·강제Read 트리거 존재 임을 1:1 대조. **사후탐지 3겹**(manifest diff · 핵심 문구 grep 세트 · reviewer 전용 "삭제 원문 중 새 위치 없는 규칙만") + 완료 후 baseline 대비 `git diff -U0` 삭제 라인 전부 규칙 관점 재검토. 누락 발견 시 완료 금지.
2. **(보조 — #1 100% 통과 후)** 4파일 합계 bytes 30%+ 감소 (`wc -c` 전후 — 기준선 70,596B → ≤49,400B). **#1 과 충돌 시 규칙 보존 우선**(미달해도 규칙 손실 0 이면 통과).
3. `bash skills/improve/improve.sh` error=0 (CLAUDE.md→agent 실존·SKILL name 등 기계 점검 통과).
4. 기존 테스트 3종 비회귀 + CI lint.yml 통과 (문서 변경이라 JS 테스트 무영향 — 확인만). dlc-doc-drift/early-stop hook 경고는 fail-open blocker 아님(예고됨).
5. dlc-first 문구 전환 반영: **grep 타깃을 실제 문자열 `` /wt`(→dlc) `` 로 교정**(`git grep "wt(→dlc)"` 는 백틱 때문에 편집 전에도 0건 = false-pass) + §3-1·§8 이 dlc-first 의미로 읽히는지 의미검사 병행.
6. B defer 3건 반영: docs §4 양립 문구 · dlc small simplify 명시 · arch codex 참조화(선행 Read 지시 잔존) 각각 diff 존재.
6-1. wt SKILL codegraph 절에 staleness 주의·projectPath 지침·재init 안내 반영 + README 해당 줄 동기화 (diff 존재).
7. plan-reviewer(+codex) 통과 — 특히 "압축으로 의미가 바뀐 규칙 없음" 관점 지시 포함.
8. **(신규) dlc step 번호 불변**: `dlc 4/12/13/15/16단계` 가 README·wiki·architecture-reviewer 에서 같은 step 에 매핑되는지 grep 체크(슬림화가 renumber 하면 조용히 깨짐).

# Review Disposition
### plan-reviewer(+codex) CONDITIONAL — 강한 우려 4건 (전부 fix)
- **[fix] Acceptance #5 false-pass**: `git grep "wt(→dlc)"` 는 실제 문자열 `` `/wt`(→dlc) `` 의 백틱 때문에 항상 0건 → grep 타깃 교정 + 의미검사. (#5 보정)
- **[fix] §9 codex-Bash MUST 이관처 부재**: docs 에 규칙 부재 → docs §3 선추가 + CLAUDE.md §9 안전문 잔존. (Decisions·Next#2·편집전략 §1)
- **[fix] Acceptance #1 산문 규칙 누락 맹점**: comment/docstring/commit-sync(§3-5, dlc 에 없음)·`dirty=unknown`·`single writer re-read`·`ExitWorktree no-op` 등 → 삭제-diff manifest + 3겹. (#1 재정의, 편집전략 §1·§3)
- **[fix] Acceptance #2 삭제 압력**: bytes 30% hard gate → #1 후 보조목표 격하. (#2 보정)
### 약한 우려 (fix)
- **[fix] dlc step 번호 외부 cross-ref 붕괴** → Acceptance #8 신설.
- **[fix] §3→dlc 참조 축소 시 규칙 약화** → "dlc 필수·wt 먼저" CLAUDE.md 잔존. (편집전략 §1)
- **[fix] arch codex 참조화 시 선행 Read 잔존** → 편집전략 §4·Acceptance #6.
- **[fix] dlc-doc-drift/early-stop hook 발동** → 예고(Decisions·#4).
- **[fix] B-defer #2 동작변경** → 규모 gate 표 일관성 미니 검증(Decisions).
### 누락 시나리오 (fix)
- **[fix] 사후탐지 부재** → 3겹 + git diff -U0 재검토(#1).
- **[fix] §10 이동↔제외 모순** → "삭제(경위)"로 정정(Decisions·편집전략 §1).

### [2026-07-05 opus] 구현 후 리뷰 (code-reviewer + codex 병행)
- **code-reviewer = APPROVE 규칙 손실 0** (섹션 헤더 집합·dlc step 표 verbatim·e 안전규칙·docs 위임처 §1~§7 실재). Minor 4건(capped "1회"/과일반화 전례 삭제/진입매트릭스 부정가드/§9 codex smoke·hang 로드등급 이동) = **wontfix** — 압축 의도이거나 manifest 사전 허가(by-design).
- **codex = 규칙 손실 3건 → 전부 fix**:
  - **[fix] Major**: arch "실패 fallback→docs" 위임 시 원본 "환경 이슈(stdin·git-repo·sandbox)"가 docs 부재 → docs §1 에 추가(dangling 해소).
  - **[fix] Minor**: CLAUDE Setup "코드 변경/리뷰/레포 작업" 중 "레포 작업" 복원.
  - **[fix] Minor**: dlc "16단계 표는 안 늘린다" 복원.

# Workflow Findings
(없음 — dlc 정상 진행, 이탈 없음)
