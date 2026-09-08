---
title: intent-default-medium — medium 이상 작업은 plan `# Intent` 를 항상 채운다
status: done
started: 2026-09-09
updated: 2026-09-09
---

# Intent

## Problem

`# Intent`(2026-09-07 도입)는 "요구사항 명확화에서 공백을 발견했을 때만" 채우는 조건부 섹션이다(개정 전 `skills/dlc/SKILL.md:44` "선택 섹션이라 trivial·공백 없음이면 생략"). 그런데 도입 계기였던 2026-09-07 `settings.json` 건의 실패 형태는 "질문할 공백을 못 봤다"가 아니라 **"기각 근거인 제약 세 가지가 착수 시점에 어디에도 적혀 있지 않았다"**(2026-09-07 plan `# Intent` 원문)다 — 모델이 공백을 인지하지 못하면 규칙이 발동하지 않으므로, 공백-트리거로는 그 사례를 막지 못한다. 사용자도 Intent 가 기본 방식이 될 것으로 기대했다(2026-09-09 대화, AskUserQuestion 선택 "medium 이상 항상 채움").

## Constraints

- **단일 소스 배치 유지** — 섹션 정의는 `CLAUDE.md` §10, 채우는 조건·절차는 `skills/dlc/SKILL.md`. §10 추가분은 괄호 안 **한 구절 이하**, dlc 문장 복붙 0(2026-09-07 plan `# Decisions` "§10 은 한 줄 정의 + 절차 소유자 이름만", [[ops-doc-slimming]] "항상 주입 CLAUDE.md 를 늘리지 않는다").
- **plan 구조 불변** — 필수 6섹션·`scripts/plan-lint.js` `REQUIRED_SECTIONS` 를 바꾸지 않는다. Intent 는 구조상 계속 "선택"이고, 항상 채우는 것은 **dlc 절차의 규칙**이다(구조로 강제하면 기존 plan 전부가 lint 실패).
- **dlc 절 내부 정합** — 기록처 bullet 을 바꾸면 같은 절의 silent bullet 과 self-flag 절의 "명확화 silent 와 동형" 인용이 자기모순이 되므로 함께 한정한다(plan-reviewer 지적).
- **사용자 어휘 보존** — 조건은 사용자가 고른 기준 "medium 이상"(규모)으로 적는다. 다른 축(plan 존재)으로 치환하지 않는다(리뷰 Critical, 아래 Decisions).
- **승인된 자산 범위(§1)** — dlc 절 + §10 한 구절 + README/docs/wiki 동기화 + `agents/plan-reviewer.md`(2026-09-09 2차 AskUserQuestion 으로 포함 승인). 다른 agent 파일은 범위 밖.
- **빈 의례 금지** — [[self-diagnosis-and-improvement-status]] 가 기각한 "빈 체크리스트": `없음` 은 근거 한 구절 없이 쓰지 않고, Open questions 는 있을 때만.

## Out of scope

- small·trivial 에 plan 을 새로 두게 하는 규모 gate 표 변경(small 은 기본적으로 plan 이 없다 — 사용자 선택 "medium 이상").
- ⚠️ small 에 plan 이 있는 경우(§10 티켓)의 규칙 변경 — 현행(공백 발견 시만) 유지. 사용자 확인분이 아니라 리뷰·모델 판단(사용자 선택은 "medium 이상"까지) — 확대는 사용자 결정 사항.
- 별도 `intent.md` 파일·organizational 장치(2026-09-07 plan 에서 기각, 재개 안 함).
- ⚠️ 기존 plan 들에 `# Intent` 소급 추가 · **종료된 2026-09-07 plan 파일 수정** — 리뷰 판단(선행 plan Constraints "기존 plan 파일을 소급 수정하지 않는다"·`updated` 메타데이터 정합). supersede 기록은 `plan-handoff.md` callout·`log.md`·이 plan 에.
- `plan-lint` 에 Intent 검사 추가(구조 불변 제약).

# Goal

`skills/dlc/SKILL.md` 요구사항 명확화 절의 `# Intent` 기록 조건을 "공백 있을 때만" → "medium 이상은 공백 유무와 무관하게 항상"으로 바꾸고(Problem 은 내용, Constraints·Out of scope 는 내용 또는 `없음 — <근거>`, Open questions 는 있을 때만, 모델 추론분은 ⚠️ 표기), `agents/plan-reviewer.md` 에 그 Intent 를 반박하는 검토 항목을 넣고, `CLAUDE.md` §10 한 구절·README·docs·wiki 를 동기화한다.

# Acceptance

1. `skills/dlc/SKILL.md` 요구사항 명확화 절: 새 문구 존재(`grep -c "medium 이상은 공백 유무와 무관하게 항상" skills/dlc/SKILL.md` ≥ 1) · 옛 문구 부재(`grep -c "공백 없음이면 생략"` = 0) · 시점 괄호 "(plan 이 있으면 그때, 없으면 3단계 draft plan 시)" 보존 · `없음 — <근거 한 구절>` 규칙 · ⚠️ 추론분 구분 · "이 규칙 이전에 만들어진 plan·이어받는 plan 에는 소급하지 않는다" · trivial 은 "`# Intent` 기록 대상이 아니다"(절 진입 축 아님) — 일곱 요소 모두 read 로 확인, `# Decisions` 행동 매트릭스 6행과 어긋나는 문장 0.
2. 같은 절의 silent 문구에 "질문" 축 한정이 들어가고, self-flag 절의 인용이 "요구사항 명확화 silent 규약의 질문 축과 동형"으로 좁혀진다 — read.
3. `CLAUDE.md:202` 변경은 그 줄만(`git diff CLAUDE.md` +1/-1): 머리말 "선택 섹션 (절차가 요구할 때만)" + `# Intent` 괄호에 "규모 medium 이상은 항상" 한 구절 · dlc 문장 복붙 0.
4. `README.md` 변경은 244행(선택 섹션 열거 조건 구절)과 285행(plan-reviewer 책임칸 "`# Intent` 반박") 두 줄만(`git diff README.md` +2/-2) — README 편집이 `agents/plan-reviewer.md` 편집보다 나중이라 `dlc-doc-drift` readme 축 해제(mtime 순서).
5. `agents/plan-reviewer.md`: 체크리스트 항목 14(트리거 "plan 파일이 있는 medium 이상 계획" · 소급 제외 · 텍스트-only 제외 · 미표기 추론 · Constraints 누락 · `없음` 근거) 1개 추가 · `.claude/plans/` 표기 0건(`grep -c "\.claude/plans/" agents/plan-reviewer.md` = 0).
6. `docs/dlc-details.md:8` §A 요약이 매트릭스와 모순 없음 — "`# Intent` 기록" 에 "(medium 이상 항상)" 구절 추가, 그 외 불변.
7. wiki 2쪽: `wiki/pages/concept/dlc-development-cycle.md` 요구사항 명확화 게이트 절에 새 조건 + 정본 링크 · `wiki/pages/concept/plan-handoff.md` "선택 섹션은 …" 문단(구조상 선택 / 절차상 필수 이중 지위)·supersede callout(2026-09-09 조건 변경 — 열거 줄은 simplify 로 원문 유지) · 두 페이지 frontmatter `updated: 2026-09-09` + `sources` 에 `plans/2026-09-09-intent-default-medium` — `grep -c "medium 이상" wiki/pages/concept/dlc-development-cycle.md wiki/pages/concept/plan-handoff.md` 각 ≥ 1.
8. `wiki/index.md` 9행(`dlc-development-cycle`) 요약이 "항상" 조건 반영(10행은 중복 제거로 원문 유지 — `git diff wiki/index.md` +1/-1) · `wiki/log.md` 에 `## [2026-09-09] ingest | intent-default-medium` append(**구현 순서 마지막** — append-only 라 되돌림이 삭제가 아닌 추가 항목이 되므로 evidence gate 뒤에 쓴다) — `grep -n`.
9. 수정하지 않음(확인 완료) 목록이 `# Key Files` 에 있다: `wiki/pages/concept/unknowns-discovery.md:18` · `wiki/pages/source/ai-native-sdlc-playbook-intent.md:39` · `skills/{c,e,improve}/SKILL.md`(6 H1/plan-lint 재서술만) · `wiki/log.md` 기존 2026-09-07 항목 · `plans/2026-09-07-plan-intent-section/`(불변, `git status` 에 미등장).
10. 검증(격리 runner 실행·메인 판단): `bash scripts/verify.sh` 최종행 `ALL PASS` 또는 `ALL PASS (skip: shellcheck)` — skip 허용은 shellcheck 한 축만, 근거: `git diff --name-only origin/main...HEAD` 에 `.sh` 0건(이 변경은 셸 스크립트 표면을 건드리지 않는다) · `node scripts/plan-lint.js plans/2026-09-09-intent-default-medium/intent-default-medium-plan.md` exit 0 · `uv run --no-project python skills/wiki/check_links.py` 출력 `wiki link check: clean` · `bash skills/improve/improve.sh --ci` exit 0.
11. 이 plan 의 `# Intent` 가 새 문구 요건을 만족한다: Problem·Constraints·Out of scope 에 내용, Open questions 는 미해결이 없어 생략(조건부 규칙의 사용례), 사용자 확인분과 모델·리뷰 판단분이 ⚠️ 로 구분돼 있다(Out of scope 2·4, Decisions 매트릭스 주석).

# Progress

- 2026-09-09: 사용자 확인 — Intent 조건부(공백 트리거) ≠ 기대(기본). AskUserQuestion 으로 "medium 이상 항상 채움" 선택. `/wt intent-default-medium` 생성(base `origin/main@30be648`) → dlc medium.
- 2026-09-09: Explore — 동기화 지점 확정(§ Key Files). `check_links.py` 는 `skills/wiki/check_links.py` 에 **실존**(초안의 "없음" 은 오류 — plan-reviewer 가 실행해 baseline `clean` 확인) → 검증셋 = `verify.sh` + `plan-lint.js` + `check_links.py` + `improve.sh --ci`. `verify.sh` 실측 최종행은 `ALL PASS (skip: shellcheck)`(shellcheck 미설치).
- 2026-09-09: draft plan → plan-reviewer(Claude, CONDITIONAL 5건) + codex(medium, Critical 1·Major 6·Minor 3) 병행. 합의: "plan 존재" 재해석 철회 → 사용자 어휘 "medium 이상" / done plan 소급 수정 제거 / `없음` 은 근거 필수 / 45·54행 동시 정합 / README·plan-handoff:21 추가 / 검증셋 보강. 사용자 2차 AskUserQuestion → `agents/plan-reviewer.md` 포함 승인. 처분은 `# Review Disposition`.
- 2026-09-09: 구현 8파일(+19/−16) → 메인 grep 스모크(acceptance 1~8 문구 존재/부재 통과) → code-reviewer(Claude, Major 3·Minor 8) + codex(low, Major 3·Minor 3) 병행 → fix loop 1회차 반영(README:285·항목 14 재작성·`# Deferred` 신설·wiki 압축·44행 3분할·§10 머리말 교체 등 — `# Review Disposition` 2절). Stop hook README 경고는 편집 순서(agents 가 README 보다 나중) 탓이었고 285행 편집으로 해소.
- 2026-09-09: simplify(plan-handoff 페이지 내 조건 3회→2회) → code-reviewer targeted 재리뷰: Major 3 전부 해소, 신규 모순은 plan 내부 stale 행번호·Acceptance 7/8 문구만 → 정정. 항목 14 트리거를 "메인이 전달한 규모 기준(미전달이면 생략)"으로 fail-safe 화. `wiki/log.md` append, `wiki/index.md` mtime 갱신. 격리 runner: `verify.sh` → `ALL PASS (skip: shellcheck)`(`.sh` 변경 0건), `plan-lint` exit 0, `check_links.py` → `clean`, `improve.sh --ci` → `error=0 warn=0`. **evidence gate 11항 전부 충족 → 판정 DONE**(status 는 머지 시점까지 in_progress). 참고: dlc 요구사항 명확화 절 총량 696→815자(+119) — 3분할로 스캔성은 개선, 절 자체는 커짐.
- 2026-09-09: 커밋 `a5520a4` → `/e merge`: push, PR #164 생성(MERGEABLE). plan done 은 이 커밋에 실어 보낸다. 후속(별도 작업)은 `# Deferred`.

# Next

(없음 — PR #164 머지로 종료)

# Decisions

- **행동 매트릭스 (문서별 문구는 이 표에 대조한다)**

  | 규모 | plan | `# Intent` |
  |---|---|---|
  | trivial | 없음 / 있음(티켓) | 생략 — 요구사항 명확화 절 자체가 비-trivial 전용 |
  | small | 없음(기본) | 생략 — 담을 곳 없음 |
  | small | 있음(§10 티켓·명확한 컨텍스트) | 공백 발견 시만(현행 유지) |
  | medium·structural | 3단계 draft plan 항상 | **항상** — Problem 내용 · Constraints·Out of scope 내용 또는 `없음 — <근거>` · Open questions 있을 때만 · 사용자 확인분과 모델 추론분(⚠️) 구분 |
  | small→medium 승급 | 승급 시 draft plan 생성 | 그때 채움(시점 괄호 "없으면 draft plan 시" 보존 — 2026-09-07 리뷰 major fix) |
  | 기존 in_progress plan 이어받기 | 있음 | 소급 안 함 |

  행 4(medium 이상 항상)는 사용자 선택, 행 1·2 는 규모 gate 구조에서 따라옴, ⚠️ 행 3·5·6 은 리뷰·모델 판단(사용자 미확인).

- **조건은 사용자 어휘 "medium 이상"(규모)으로 적는다 — 초안의 "plan 존재" 재해석 철회** (이유: codex Critical — §10 은 규모 무관하게 plan 을 두므로 "plan 존재"는 trivial·비-dlc·수동 plan 까지 포함해 요구사항 명확화 절(비-trivial 전용)의 실행 주체와 어긋난다; plan-reviewer — 사용자가 고른 판정 기준을 다른 축으로 치환한 것은 `skills/dlc/SKILL.md:43` fail-safe 상 물어야 할 건이었고, small+plan 사각은 실측 없는 가정이다). 기각안 2: plan-reviewer 제안 "medium 이상 항상 + small·trivial 이라도 plan 을 두면 같이" — 사용자 선택 범위를 넘는 확대라 채택 안 함, small+plan 은 현행 유지. 기각안 3: "plan 을 write 하는 시점에 채운다"(행위 시점 트리거) — 승급 경로를 자동 포섭하지만 같은 확대 문제.
- **`없음` 은 근거 한 구절 필수 (`없음 — <근거>`), Problem 은 `없음` 불가** (이유: plan-reviewer — 이 repo 작업엔 §0·§1·worktree 제약이 사실상 항상 있어 맨 `Constraints: 없음` 은 거짓 기록이 되고, 반박자 없는 `없음` 은 반증 불가 주장이라 기각된 "빈 체크리스트 의례"와 실질이 같다; codex — `Problem: 없음` 은 plan 존재와 모순, `Out of scope: 없음` 은 무제한 범위로 오독). 근거 한 구절은 리뷰어 없이도 "고려했다 vs 잊었다"를 구분한다. **기각된 invariant-check 와의 차이**: 그 안은 작업마다 *새 내용*(불변식 2~3개)을 자의적 개수로 발명하게 했고, Intent 는 요청자가 *이미 가진 지식*(문제·제약·제외)을 고정 3항에 옮기는 것이다. **회귀 기준**: 이후 plan 에서 `없음` 이 실질 항목보다 많아지면 조건부로 되돌리는 것을 검토 — ⚠️ 재평가 주체·주기는 미확정(`/improve deep` 의 주기 재판정 축에 얹는 것이 후보).
- **사용자 확인분과 모델 추론분을 구분한다** (이유: plan-reviewer — §10 정의는 "착수 전 **확정한** 요구"인데 silent 로 끝난 경우 채워지는 내용은 모델 추론이라, 그것이 확정으로 박히면 다음 세션이 잘못된 근거로 선택지를 기각한다 — 원래 문제의 부호만 바뀐 재현). 추론분은 ⚠️ 표기(CLAUDE.md §1 확신도 표기와 동형) 또는 Open questions 로.
- **§10 은 괄호 안 한 구절만** ("dlc 요구사항 명확화가 채운다 — 규모 medium 이상은 항상" — "규모"는 §5 의 effort 값 `medium` 과의 동음이의를 끊기 위함, code-reviewer 지적). 머리말은 "해당 작업에서 필요할 때만" → "절차가 요구할 때만"으로 교체(codex 코드리뷰 Minor: 선택 선언 직후 "항상"이 모순으로 읽힘. 모든 선택 섹션이 절차 트리거 — Acceptance=evidence gate·Review Disposition=fix loop·Deferred=§3-4·Workflow Findings=확인된 실패 — 라 정확하고, Claude code-reviewer 는 기존 문구도 항목별 한정 패턴으로 읽힌다고 반박했으나 교체가 그 독법을 해치지 않아 채택). codex 는 "채움 조건은 절차라 §10 에 넣지 말라", plan-reviewer 는 "§10 을 아예 안 건드리면 머리말 '필요할 때만' 과 정면 모순이고 dlc 를 로드하지 않는 세션(수동 plan·`/c`)은 §10 만 읽는다" — 후자 채택. 선행 wontfix("§10 에 Constraints 라우팅 규칙 추가" 기각, 2026-09-07 plan:93)와의 구분: 그건 *절차 서술*을 넣는 안이었고, 이건 `# Acceptance` 항목이 "dlc evidence gate" 라고 소유자를 적는 것과 같은 고도의 4단어 조건이다.
- **`agents/plan-reviewer.md` 포함** (2026-09-09 사용자 승인). 이유: PR #162 → playbook-gaps 에서 2회 이월된 항목이고, `없음` 규칙의 실효성 절반이 반박자에 있다. 같은 파일 15행의 금지 표기 `.claude/plans/`(CLAUDE.md §10 이 이 repo 에서 빈 경로라 금지)도 승인 범위에 명시해 함께 정정.
- **구조(§10 선택 섹션·plan-lint) 불변, 절차(dlc)만 강화** — 필수 7섹션으로 올리면 기존 plan 전부가 lint 실패하고 2026-09-07 plan 이 supersede 한 wontfix 의 기각 사유("6섹션 구조 충돌")를 되살린다.
- **종료된 2026-09-07 plan 은 건드리지 않는다** (초안의 "Open question 에 supersede 포인터 +1" 철회 — 이유: codex — 선행 plan Constraints "기존 plan 파일을 소급 수정하지 않는다"와 모순, 본문을 고치면 `updated: 2026-09-07` 이 거짓이 되고 그것까지 고치면 "그 줄만" acceptance 가 깨진다. supersede 정본은 `plan-handoff.md` 의 `# Intent` callout).
- **구현 순서는 되돌림 비용 역순이 아니라 검토 밀도순** — dlc 문구(가장 많이 읽히는 지점, 깨지면 즉시 드러남) → §10 → README → agents → docs → wiki 2쪽·index → `log.md` append 는 evidence gate 뒤 맨 마지막(append-only, 되돌림 = 추가 항목).
- ⚠️ small+plan 조합이 실제로 발생하는지는 추정(§10 이 허용할 뿐 실측 없음) — 사용자 문구 "medium 이상"과 상충 — **처분: resolved** — 리뷰가 "추정된 사각을 근거로 사용자 기준을 치환했다"고 확인, 사용자 어휘로 복귀. `# Review Disposition` 참조.

# Review Disposition

plan-reviewer(Claude) + codex(medium) 병행, 2026-09-09.

- ⚠️ self-flag "plan 존재" 재해석 — **resolved**: 사용자 어휘 "medium 이상"으로 복귀(양쪽 합의).
- codex Critical 1 트리거 확대·실행 주체 불일치 — **fix**(위와 동일).
- codex Major 1 / plan-reviewer 약 1 §10 단일 소스 — **fix**: §10 은 괄호 안 한 구절, 절차 서술 없음(양쪽 근거 병기해 plan-reviewer 쪽 채택 — Decisions).
- codex Major 2 / plan-reviewer 강 `없음` 빈 의례·거짓 단정 — **fix**: `없음 — <근거>` 필수, Problem 불가, 기각안과의 차이·회귀 기준 기록.
- plan-reviewer 강 추론분 오염(확정 vs 추정) — **fix**: ⚠️ 구분 규정.
- codex Major 3 / plan-reviewer 약 done plan 소급 수정 — **fix**: 제거.
- codex Major 4 / plan-reviewer 약 `agents/plan-reviewer.md` 3회차 이월 — **fix**: 사용자 승인으로 포함.
- codex Major 5 작성 시점 — **fix**: 시점 괄호 보존 + 승급·이어받기 행을 매트릭스에.
- codex Major 6 / plan-reviewer 약 Acceptance 관찰성(grep 만·모순·자기참조) — **fix**: 11항 재작성(매트릭스 대조·새 문구 존재+옛 문구 부재·diff 범위·runner 4 명령).
- plan-reviewer 강 `check_links.py` 부재 오판·`verify.sh` 가 wiki 를 안 봄 — **fix**: Progress 정정, 검증셋 보강.
- plan-reviewer 강 Acceptance "skip 없음" 달성 불가 — **fix**: `(skip: shellcheck)` 허용 + `.sh` 0건 근거로 착수 전 확정(no-progress 카운터 리셋 금지 규칙에 걸리지 않게).
- plan-reviewer 강 45·54행 자기모순 — **fix**: Key Files·Acceptance 2.
- plan-reviewer 강 README doc-drift failure 신호 — **fix**: README:244 한 구절.
- plan-reviewer 약 plan-handoff.md:21 이중 지위 — **fix**.
- plan-reviewer 약 "수정하지 않음(확인 완료)" 목록 — **fix**: Key Files.
- plan-reviewer 약 `improve.sh --ci` 검증셋 — **fix**.
- plan-reviewer 약 범위 밖 `agents/plan-reviewer.md:15` 표기 — 포함 승인으로 **fix**(다른 agent 파일에 같은 표기가 있으면 `# Deferred`).
- codex Minor 1 파일 수 불일치 — **fix**(Key Files 를 변경/확인/불변으로 분리).
- codex Minor 2·plan-reviewer 재서술 지점 — **fix**(불변 확인 목록).
- codex Minor 3 "선택 섹션" 용어 이중 의미 — **fix**(plan-handoff:21 + §10 구절).
- plan-reviewer rollback "규칙 롤백 기준 부재" — **fix**(Decisions 회귀 기준).

code-reviewer(Claude, REQUEST CHANGES Major 3·Minor 8) + codex(low, Critical 0·Major 3·Minor 3) 병행, 2026-09-09 — fix loop 1회차.

- Claude Major 1 README:285 plan-reviewer 책임칸 미갱신 → doc-drift readme 축 미해제(mtime 재현) — **fix**: 285행 구절 추가, README 를 agents 편집 뒤에 편집. Acceptance 4 갱신.
- Claude Major 2 / codex Major 1·2 항목 14 에 소급·small+plan 예외 없음, 미표기 추론 미검사 — **fix**: 항목 14 재작성(트리거 관측 가능화·소급 제외·텍스트-only 제외·"⚠️ 없이 확정처럼" 검사).
- codex Major 1 의 나머지(§10·README·index·plan-handoff 에도 소급 예외를 적어라) — **wontfix**: 소급 예외는 규칙 전환기의 한시 사항이고, 오탐이 실제로 나는 지점은 리뷰어(항목 14)와 dlc 본문뿐. 정의·요약 레이어에 한시 예외를 얹으면 §10 한 구절 제약과 index 1줄 요약이 깨진다.
- Claude Major 3 `# Deferred` 약속 미이행 — **fix**: 섹션 신설.
- codex Major 3 / Claude Minor 규칙 3중 서술(wiki 두 페이지가 dlc 절차 복제) — **fix**: 두 wiki 문단을 "항상 + 이유 + 정본 링크"로 압축.
- Claude Minor 소급 문구 중의성("이미 있는 plan") — **fix**: "이 규칙 이전에 만들어진 plan·이어받는 plan".
- Claude Minor §10 "medium" 정의 부재(effort 동음이의) — **fix**: "규모 medium 이상".
- codex Minor 1 §10 머리말 모순 인상 vs Claude refuted — **fix**(교체, 사유 Decisions).
- Claude Minor trivial "절 진입" 축 충돌(47행) — **fix**: "`# Intent` 기록 대상이 아니다".
- Claude Minor 근거 문장 과잉단정("알던 제약") — **fix**: 원 기록 "어디에도 적혀 있지 않았다"로(SKILL·wiki 2쪽·이 plan Problem).
- Claude Minor 이 plan Intent 의 ⚠️ 0건 — **fix**: Out of scope 2·4 ⚠️, 매트릭스 주석, Acceptance 11 갱신.
- Claude Minor 항목 14 분량·판정 근거 — **fix**(재작성에 포함).
- codex Minor 2 / Claude Minor 44행 696자 simplify — **fix**: 3 bullet 분할(언제·무엇·예외, 내용 보존).
- codex Minor 3 / Claude Minor plan-handoff callout 과잉 — **fix**(압축).
- Claude Nit index 두 줄 중복 — **fix**: plan-handoff 줄에서 제거.
- Claude Nit 이 plan Constraints 의 기본 제약(§0) — **fix**: 제거, §1 줄은 "승인된 자산 범위"로.
- Claude Nit 44행 `없음` vs 59행 self-flag 0줄 반대 입장 — **fix**: `없음` 절에 구분 이유 한 구절.
- Claude Nit sources 가 untracked plan 을 가리킴 — **fix**: 같은 커밋에 plan 포함(커밋 절차).

# Deferred

- `.claude/plans/<dir>/<slug>-plan.md` 표기 잔존 — Minor — `agents/architecture-reviewer.md:168` · `agents/code-reviewer.md:138` · `agents/researcher.md:62`. CLAUDE.md §10 이 이 repo 에서 빈 경로라 금지한 표기(`<ROOT>/plans/`)인데 세 agent 의 "plan 반영용 요약" 헤더에 남아 있다. 승인 범위(`agents/plan-reviewer.md`) 밖이라 별도 작업.
- 소급 예외(`skills/dlc/SKILL.md` "이 규칙 이전에 만들어진 plan·이어받는 plan 에는 소급하지 않는다" · `agents/plan-reviewer.md` 항목 14)는 규칙 전환기의 한시 규정 — 2026-09-09 시점 `status: in_progress` plan 5건(`repo-audit-fixes`·`dlc-loop-redesign`·`stale-plan-signal`·`branch-merge-backlog`·`e-merge-path`)이 모두 닫히면 문구 제거 후보(code-reviewer 재리뷰 제안).

# Key Files

변경:
- `skills/dlc/SKILL.md` — 요구사항 명확화 절: 기록처 bullet(**핵심**, 3 bullet 로 분할 — 언제·무엇·예외)·silent 한정·self-flag 절 인용 한정
- `CLAUDE.md` — §10 선택 섹션 줄(202): 머리말 "절차가 요구할 때만" + 괄호 안 "규모 medium 이상은 항상"
- `README.md` — 244행 선택 섹션 열거 조건 구절 · 285행 plan-reviewer 책임칸 "`# Intent` 반박"
- `agents/plan-reviewer.md` — 체크리스트 항목 14 추가 · 15·82행 `.claude/plans/` → `<ROOT>/plans/`
- `docs/dlc-details.md` — §A 첫 줄(8) 한 구절
- `wiki/pages/concept/dlc-development-cycle.md` — 요구사항 명확화 게이트 절 + frontmatter
- `wiki/pages/concept/plan-handoff.md` — "선택 섹션은 …" 문단·`# Intent` callout + frontmatter(열거 줄은 원문 유지)
- `wiki/index.md` — 9행 요약(10행 원문 유지)
- `wiki/log.md` — append(마지막)

확인 후 불변(재서술 지점이나 조건을 서술하지 않음):
- `wiki/pages/concept/unknowns-discovery.md:18` — "결과를 plan `# Intent` 에 기록"(조건 무언급)
- `wiki/pages/source/ai-native-sdlc-playbook-intent.md:39` — 채택 형태 기록(2026-09-07 시점 사실)
- `skills/c/SKILL.md:43` · `skills/e/SKILL.md:39` · `skills/improve/SKILL.md:25` — 6 H1/plan-lint 재서술만
- `wiki/log.md` 2026-09-07 항목 — 당시 기록, 수정 금지(append-only)
- `plans/2026-09-07-plan-intent-section/` — 종료 plan, 불변
- `scripts/plan-lint.js` — 선택 섹션 미검증, 불변

# Blockers

(없음)
