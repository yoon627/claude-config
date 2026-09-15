---
title: intent-md-bundle — 묶음 단위 intent.md 규약 도입(§10·dlc·c·e·README·wiki)
status: in_progress
started: 2026-09-15
updated: 2026-09-15
intent: plans/2026-09-15-intent-bundles/intent.md
---

# Intent

→ `plans/2026-09-15-intent-bundles/intent.md` (Problem·Proposed outcome·공통 Constraints·Out of scope·Open questions 는 거기).

이 plan 에만 더해지는 것:
- Constraints: 이 plan 자체가 새 규약의 첫 사용례(dogfooding) — 규약대로 `intent:` 링크 + 델타만 적는다.
- Out of scope: `skills/wt` 변경 — 기존 묶음 발견·연결은 dlc 요구사항 명확화(0단계 스캔·트리거 3)가 하므로 wt 는 손댈 것이 없다(사용자 승인 범위에 있었으나 조사 결과 불필요 — Report 에 통지).

# Goal

CLAUDE.md §10 에 묶음 intent.md 규약(위치·생성 트리거·템플릿·plan 과의 관계·수명·한계)을 정의하고, dlc(발견·생성·링크)·c(복원 시 읽기)·e(closed 판정)·plan-reviewer(§10 위임 1줄)가 그것을 따르게 한 뒤 README·wiki 를 동기화한다.

# Progress

- 2026-09-15: 조사 — `plan-match.js`·`session-brief.js` 는 `*-plan.md` 만 스캔, `pre-commit-check` 는 `plans/*.md` 전부 스캔, `guard-worktree-edit` 는 plans/ allow, `dlc-evidence-ledger` 는 plans/ 제외 → intent dir 을 `plans/` 아래 두면 코드 변경 0. 공식 출처 재확인(Claude Academy capture-intent). knowledge_base 12 plan 실측(묶음 2개, 제약 복제). worktree `intent-md-bundle` 생성, intent.md + 이 plan 작성.
- 2026-09-15: 구현(§10 새 절·dlc·c·e·plan-reviewer·README·wiki 5) → 검증 전부 통과 → code-reviewer(단독 — codex 한도 소진, 세션 마커 기록) REQUEST CHANGES: Major 2(`/e` closed 판정 시점이 M4 done 커밋과 어긋남·intent.md 커밋 단계 부재 / 발견 스캔이 미머지 형제 worktree 를 못 봄), Minor 6. fix loop 1회차로 전부 반영(아래 Review Disposition).
- 2026-09-15: fix loop 반영 후 재검증 — `verify.sh` ALL PASS(skip 없음) · `improve.sh --ci` error=0 warn=0 · `check_links.py` clean · plan-lint exit 0 · `CLAUDE_BRIEF_REPO=$PWD session-brief.js` exit 0 · grep 관찰(CLAUDE.md `intent.md` 7건, dlc/c/e 각 2, plan-reviewer/README 각 1). simplify: 추가 수정 없음. evidence gate Acceptance 1~5 충족 → DONE(status 는 머지 시 done).
- 2026-09-15: plan-reviewer + codex(medium) 병행 → CONDITIONAL GO, 강한 우려 6(C1 closed 판정 불능·C2 후속 plan 의 intent 발견 경로 없음+미머지 가시성·C3 `# Plans` status 복제·C4 동시편집 소유권·C5 Acceptance 경로 오기/vacuous·C6 소급 경계 모순). 전부 `# Review Disposition` 대로 반영. baseline 실측(리뷰어): `verify.sh` ALL PASS(skip 없음), `skills/wiki/check_links.py` clean, `improve.sh --ci` error=0 warn=0.

# Next

1. `/e merge`(medium — push·PR·머지). 머지 시 이 plan done + 묶음 판정(Open questions 2건 `(열림)` → intent 는 open 유지).

# Decisions

- **intent dir 은 `plans/<date>-<intent-slug>/` 에 `intent.md` 만, plan 은 자기 dir 유지** — 기각안: intent dir 안에 여러 `<slug>-plan.md`. `plan-match.js:36-40` 은 slug 첫 매칭을 즉시 반환하고 `/c`·`/e` 절차는 "dir 당 `*-plan.md` 1개, 2개+ 는 후보 제시" 라 한 dir 에 plan 여럿은 매칭 의미를 바꾼다. dir 분리는 코드 변경 0.
- **연결은 plan frontmatter `intent:`(선택 키, 스칼라 1개 — 한 plan 이 두 묶음에 걸치는 것은 금지) + `# Intent` 첫 줄 링크** — `plan-lint` 는 REQUIRED_KEYS 만 검사해 추가 키에 무관(코드 확인). 기각안 1: `# Intent` 링크만 — 기계 판독이 본문 파싱에 의존. 기각안 2: 묶음 파일 없이 plan 간 `follows:`/`supersedes:` 링크만 — 계보는 생기지만 공통 제약·Open questions 의 단일 위치가 없어 복제 문제(실측)가 그대로다. 기각안 3: 첫 plan 의 `# Intent` 를 정본으로 두고 후속이 그 plan 을 가리킨다 — 파일은 안 늘지만 첫 plan 이 done 으로 닫힌 뒤에도 정본이 그 안에 살아 "plan 은 종료 시 닫힌다"(§11)와 충돌하고, 첫 plan 고유 델타와 공통 제약이 한 섹션에 섞인다.
- **생성 트리거는 닫힌 목록 3개** — 1) 사용자 지시 2) 요구사항 명확화 시점에 plan 이 2개 이상 예상됨(후속·병렬 분할 포함) 3) 기존 plan 의 Out of scope·`# Deferred`·"별도 작업" 에서 새 plan 을 시작 → 소급 생성. **소급 생성 시 선행 plan 에는 frontmatter `intent:` 1줄만 추가하고 본문은 손대지 않는다**(변환 아님 — `/c` 가 묶음을 찾게만 한다). 그 외 단발 작업은 plan `# Intent` 만.
- **발견 경로(C2)** — dlc 요구사항 명확화 0단계에서 `plans/*/intent.md` 중 `status: open` 을 스캔해 해당 묶음이 있으면 연결한다(코드 변경 0). **한계**: 선행 브랜치가 미머지면 후속 worktree(default 기준)에 intent.md 가 없다 → `git show <선행브랜치>:<경로>` 로 가져와 같은 경로에 둔다(동일 내용 추가는 머지 시 충돌 없음). §10 에 명시.
- **템플릿은 Problem·Proposed outcome·Constraints·Out of scope·Open questions·Plans** — 플레이북 5항목에서 `Affected users and systems` 는 뺀다(2026-09-07 과 같은 이유). `Out of scope` 는 **경계**(하지 않을 것)만 — 이어서 할 후속은 `# Plans` 에 `(미착수)` 로 둔다(C1: 둘을 섞으면 closed 판정 불능). `# Plans` 는 **경로 + 한 줄 메모만, status 복제 금지**(C3 — 정본은 plan frontmatter, `/e merge` M4 복구가 intent 까지 닿지 않아 유령 done 이 남는다). 폐기한 plan 은 메모에 `폐기` 표기.
- **plan `# Intent` 는 링크 + 델타만, 공통 제약 복제 금지** — 복제가 실측 문제였다. 델타가 없으면 `델타 없음 — <근거>`(dlc 의 `없음 — <근거>` 규칙과 동형, 맨 "없음" 금지). 충돌·변경은 plan `# Decisions` 에 적고 intent.md 를 갱신.
- **동시편집 소유권(C4)** — 각 세션은 intent.md 에서 자기 plan 의 `# Plans` 줄과 자기가 연 Open question 만 고친다. 공통 Constraints 변경은 진행 중인 다른 plan 의 `# Decisions` 에 영향 통지를 남긴다(§3 subagent 파일 소유권 분리와 같은 원리).
- **수명(C1): plan done ≠ intent closed** — closed = `# Plans` 의 모든 plan 이 frontmatter `done`(또는 메모 `폐기`) **그리고** Open questions 전부 처분(`(해소)` 또는 `(이월 → <새 묶음>)`). Out of scope 는 조건에 넣지 않는다(영구 경계라 영원히 안 닫힘). `/e` 4단계가 plan done 확정 시 판정 — 조건 충족이면 사용자 확인 없이 closed(객관 판정), 미충족이면 open 유지.
- **intent.md 는 plan 이 아니다 — `plan-lint` 대상 아님**(실측: 돌리면 7건 위반). `status:` 값은 `open|closed`, 값 라인에 인라인 주석 금지(2026-07-26 stale-plan-signal 영구 무음 선례).
- **intent.md 스키마 lint 는 안 만든다**(사용례 0 에서 굳히면 첫 실사용에서 고친다). **`intent:` 참조 무결성(파일 존재) 검사도 이번엔 안 넣는다** — `lintPlan(text)` 는 fs 없는 순수 함수라 존재 확인엔 root 컨텍스트가 필요해 CLI 래퍼 변경 + 테스트가 따른다. intent.md Open question 으로 이월.
- **`agents/plan-reviewer.md` 14항은 규칙 복제 대신 "§10 위임 1줄"** — ⚠️ self-flag 해소(`resolved`): §1 의 "요청" 정의는 `# Goal`/`# Key Files` 등재를 포함하나 스스로 넣은 것을 근거로 삼으면 순환이라, Report 에 범위 확대를 1줄 통지한다. 안 고치면 "링크+델타" 를 아무도 검사하지 않는다(14항이 `# Intent` 검사의 유일한 정본).
- **`skills/wt` 미변경** — Intent 델타 참조.
- **rollback** — 문서 전용이라 브랜치 revert 로 충분하나 비대칭: 되돌릴 때 (1) 신규 연결 중단 (2) 기존 intent.md 는 삭제하지 않고 보존 (3) 진행 중 plan `# Intent` 에 공통 Constraints 를 되복사.

# Review Disposition

- C1 closed 판정 불능 → `fix`(Out of scope 를 조건에서 제외, 후속은 `# Plans` `(미착수)`, Open question 처분 어휘)
- C2 발견 경로 없음·미머지 가시성 → `fix`(dlc 0단계 스캔 + §10 한계·`git show` 처리)
- C3 `# Plans` status 복제 → `fix`(경로+메모만, 정본 plan frontmatter)
- C4 동시편집 소유권 → `fix`(1줄 규칙)
- C5 Acceptance 오기·vacuous → `fix`(`skills/wiki/check_links.py`, `CLAUDE_BRIEF_REPO="$PWD"`, `improve.sh --ci` 추가)
- C6 소급 경계 모순 → `fix`(선행 plan 에 `intent:` 1줄만)
- ⚠️ self-flag 14항 범위 → `resolved`(위임 1줄 + Report 통지)
- 약: `status` 어휘·인라인 주석 → `fix` / plan-match 서술 오류 → `fix` / 기각안 2건 → `fix`(Decisions) / `intent:` 참조 검사 → `defer`(위 Decisions 사유) / MAX_PLANS 예산 → `defer`(`# Deferred`) / 시나리오 4(두 묶음)·6(델타 없음) → `fix`(Decisions)

code-reviewer(1회차):
- Major F1 `/e` closed 판정 시점 → `fix`(done 을 쓰는 지점 — 체크포인트 4단계 확인 done / 머지 M4 — 에서 판정, 같은 커밋, M4 복구 시 함께 open 복구; §10 수명 문장도 동일하게)
- Major F2 발견 스캔이 미머지 형제 worktree 를 못 봄 → `fix`(dlc·§10 한계: `git worktree list` 모든 worktree `plans/` 스캔 → 그 뒤 `git show`)
- Minor §10:181 단일 진실 소스 문장 → `fix`(괄호 조정) / c 2단계 "3단계 보정 대상" 미정의 → `fix`(3단계 항목 추가) / 규칙 4곳 복제 → `fix`(wiki plan-handoff 는 왜·기각안만 + §10 링크, dlc 는 트리거 재서술 제거; e 는 실행 절차라 조건 재서술 유지) / H3 삽입으로 리뷰 문단 편입 → `fix`(문단을 H3 앞으로) / `# Plans` 읽기 실패 기본값 → `fix`(done 아님 fail-safe) / plan-reviewer 14항 게이트 상속 → `fix`("규모와 무관하게") / `(열림)` 어휘 → `fix`(§10 에 추가) / open 묶음 잔존 신호 부재 → `defer`(`# Deferred`)
- Open(wt 미변경 근거) → `no-change`: `skills/wt/SKILL.md` 는 조사 시 읽었고 plan/intent 부트스트랩이 없다(생성 후 dlc 로 위임) — Intent 델타에 기재.

# Acceptance

1. CLAUDE.md §10 에 묶음 intent 절이 있고 위치·트리거 3·템플릿 6섹션·`intent:` 키·델타 규칙·closed 조건·소유권·미머지 한계를 담는다 — `grep -n 'intent.md' CLAUDE.md` 관찰.
2. dlc(0단계 스캔·트리거·3단계 링크), c 2단계, e 4단계, plan-reviewer 14항이 intent.md 를 다룬다 — 각 파일 `grep -n 'intent' ` 관찰.
3. README §10 요약줄·wiki(`plan-handoff`·`ai-native-sdlc-playbook-intent`·`dlc-development-cycle`·`index.md`·`log.md`) 동기화 — grep + `python3 skills/wiki/check_links.py` → `clean`.
4. `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음) + `bash skills/improve/improve.sh --ci` → `error=0 warn=0`.
5. dogfood: `plans/2026-09-15-intent-bundles/intent.md` 가 템플릿대로 있고 이 plan 이 `intent:` 로 가리키며, `node scripts/plan-lint.js <이 plan>` exit 0, `CLAUDE_BRIEF_REPO="$PWD" node scripts/session-brief.js` 가 정상 출력(실행 관찰). closed 사고실험: 이 plan 이 done 이 되면 Open questions 2건이 열려 있어 open 유지 — 판정 가능함을 확인.

# Deferred

- `session-brief.js` `MAX_PLANS`(200) 디렉토리 예산을 intent dir 이 잠식 — 낮음, `scripts/session-brief.js:38,248`. 현재 dir 수로는 원거리.
- `status: open` 묶음이 영구 잔존해도 알리는 신호가 없다(session-brief "닫히지 않은 plan" 은 plan 만 본다) — 낮음, `scripts/session-brief.js:198-281`. intent lint 판단(Open question)과 함께 첫 사용례 뒤.

# Key Files

- `CLAUDE.md` §10 — 규약 정의(단일 소스)
- `skills/dlc/SKILL.md` 요구사항 명확화 + 3단계 — 발견·생성·링크
- `skills/c/SKILL.md` 2단계 — 복원 시 intent.md read
- `skills/e/SKILL.md` 4단계 — closed 판정
- `agents/plan-reviewer.md` 14항 — §10 위임 1줄
- `README.md` §10 요약줄
- `wiki/pages/concept/plan-handoff.md` · `wiki/pages/source/ai-native-sdlc-playbook-intent.md` · `wiki/pages/concept/dlc-development-cycle.md` · `wiki/index.md` · `wiki/log.md`
- 불변(확인): `scripts/plan-match.js`·`session-brief.js`·`plan-lint.js`·`pre-commit-check.sh`·`guard-worktree-edit.js`·`dlc-evidence-ledger.js`·`skills/wt/SKILL.md`

# Blockers

(없음)
