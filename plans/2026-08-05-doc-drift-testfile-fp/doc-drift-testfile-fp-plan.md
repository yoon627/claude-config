---
title: doc-drift-testfile-fp — `.test.js` 편집이 doc-drift-readme 오탐을 내는 문제 수정
status: in_progress
started: 2026-08-05
updated: 2026-08-05
---

# Goal

`scripts/*.test.js` **기존 파일 편집**만으로 `dlc-early-stop` 이 "README 미갱신" 경고를 내는 오탐을 없앤다. 단 **신규 테스트 파일 추가**는 README 파일 트리 한 줄이 실제로 필요하므로 계속 경고해야 한다.

# Progress

- 2026-08-05 근본 원인 확정(`classify()` 의 `^scripts\/[^/]+\.js$` 가 `.test.js` 를 포함) + telemetry 실측(doc-drift-readme unique-session 7건, 그 중 2026-08-04 건의 detail 이 `scripts/session-brief.test.js`).
- 2026-08-05 TDD Red→Green(Red 는 `classify` 가 `readme-trigger` 반환으로 재현). 통합테스트가 `cat-file -e` 의 exit-code 오판을 잡아 `ls-tree` 출력 판정으로 정정. CI 등가 전항목 통과, 실제 worktree 에서 hook 직접 실행 관찰(tracked `.test.js`→false / 신규 `.test.js`→true / 비-test 표면→true). codex 병행 리뷰 Critical·Major 0, Minor 2 반영. wiki·README 동기화 후 커밋.
- 2026-08-05 ⚠️ `code-reviewer` subagent 는 spawn 했으나 ~10분 대기 후에도 최종 리포트를 반환하지 않아(transcript idle, 재요청도 무응답) 리뷰 근거는 **codex 단독** + CI 등가 검증 + 실 hook 관찰로 대체했다(§9 리뷰 매트릭스 생략 사유 기록).

# Next

사용자 확인 후 push·PR (이 세션에서는 push·PR 하지 않는다 — 명시 지시).

# Decisions

- **근본 원인 (✅확실)** — `scripts/dlc-doc-drift.js` `classify()` 의 `/^scripts\/[^/]+\.js$/` 가 `.test.js` 도 매치한다. README 는 테스트를 `session-brief.js (+ .test.js)` 처럼 **접미 표기**로만 문서화하므로 테스트 *내용* 변경은 README 에 영향이 없다.
- **`.test.js` 를 통째로 제외하지는 않는다.** README 의 파일 트리는 **파일의 존재**를 문서화한다 — 신규 테스트 파일 추가는 트리 한 줄을 요구한다(실례: `scripts/session-start-pull.test.js` 추가 시 README 트리 갱신). 즉 판정축은 "테스트냐"가 아니라 **"신규 추가냐 기존 편집이냐"**.
- **판정 방식 = git HEAD 존재 여부** (`git cat-file -e HEAD:<rel>`), 대안 기각 이유:
  - *tool 이름(Write vs Edit)* — `Write` 는 기존 파일 전체 덮어쓰기에도 쓰이므로 오탐이 남는다. 판정축(파일이 repo 에 이미 있었나)과 신호(어떤 도구를 썼나)가 어긋난다.
  - *`.test.js` 전면 제외* — 신규 테스트 추가 시 README 트리가 조용히 drift 한다. 이를 잡는 다른 장치가 없다.
  - HEAD 기준이면 "이미 커밋된 파일"= 기존(그 파일을 추가한 커밋의 세션에서 이미 경고를 받았음), "HEAD 에 없음"= 신규 → 정확히 원하는 판정.
- **순수 모듈 경계 유지.** `dlc-doc-drift.js` 는 순수 모듈(README 에 그렇게 문서화됨)이라 git 을 직접 실행하지 않는다 → `classify()` 가 새 카테고리 `readme-trigger-new` 를 돌려주고, **신규 여부 판정은 호출부(`dlc-evidence-ledger.js`, 이미 git 을 쓰는 hook)** 가 주입 콜백 `isNewFile(rel, root)`(구현 `isNewInRepo`)으로 제공한다. 콜백 미제공 시 기본은 **트리거 안 함**(오탐 최소화가 이 수정의 목적).
- **판정 명령은 `git ls-tree --name-only -z HEAD -- :(literal)<rel>` 의 *출력*으로 (구현 중 정정).** 처음 쓴 `git cat-file -e HEAD:<rel>` 은 경로 부재도 **exit 128** 이라(직접 확인) git 오류와 구분되지 않는다 — 통합테스트가 이 오판을 잡았다. `:(literal)` 은 `:` 시작·와일드카드 파일명이 pathspec magic 으로 해석되는 것을 막는 방어(codex 리뷰 반영; `ls-tree` 는 실측상 glob 하지 않았으나 비용 0).
- **git 실패 시 무경고(fail-quiet).** 초기 커밋 전·timeout·git 부재는 "기존"으로 취급 — 이 게이트는 soft nudge(CAP 1회 경고, "불필요하면 재종료 시 통과" escape)라 오탐 비용이 미탐 비용보다 크다. 같은 파일의 `isIgnored` 는 정반대(실패 시 보수적 changed 유지)인데, 그쪽은 검증 게이트라 비대칭이 의도된 것이다.
- **의도적으로 남긴 미탐 구간 2곳** (버그로 오인 금지): ① git 조회 실패 시 신규 판정을 포기 → 신규 테스트 파일의 README 트리 한 줄이 조용히 누락될 수 있다(테스트 ⑫ 가 이 정책을 고정). ② 신규 추가 세션이 CAP 1회 경고를 무시하고 커밋하면, 그 뒤로는 HEAD 에 있으므로 영영 안 잡힌다.
- **`.spec.js` 는 포함, `.test.mjs` 는 제외.** spec 은 같은 부류라 동일 FP 가 재발하므로 정규식에 포함(codex·code-reviewer 공통 지적). 반면 `.mjs` 는 테스트가 아니어도(`scripts/x.mjs`) 애초에 표면이 아니라, 테스트만 표면으로 올리면 대칭이 깨진다.

# Key Files

- `scripts/dlc-doc-drift.js` — `classify()` 에 `readme-trigger-new` 카테고리 추가, `applyChange()` 5번째 인자 `isNewFile` 주입
- `scripts/dlc-doc-drift.test.js` — Red→Green 단위테스트
- `scripts/dlc-evidence-ledger.js` — `isNewInRepo()` + 콜백 주입
- `scripts/dlc-evidence-ledger.test.js` — HOME 주입 fixture 기반 통합테스트(신규/기존 테스트 파일)
- `wiki/pages/decision/workflow-failures.md` — doc-drift-readme 횟수 7·sub-class 행 추가, early-stop-verify fix 효과 확인 기록
- `README.md` — `dlc-doc-drift.js` 설명에 신규-한정 규칙 반영

# Blockers

(없음)

# Acceptance

| 항목 | 검증 | 통과 기준 |
|---|---|---|
| 1. 오탐 재현 테스트가 먼저 실패 | `node scripts/dlc-doc-drift.test.js` (수정 전) | 기존 `.test.js` 편집이 `readmeDirty=true` 로 실패(Red) |
| 2. 기존 테스트 편집 → 무경고 | `node scripts/dlc-doc-drift.test.js` | Green |
| 3. 신규 테스트 추가 → 경고 유지 | `node scripts/dlc-evidence-ledger.test.js` (실 git fixture) | 신규 파일 `readmeDirty=true`, 커밋된 파일 `false` |
| 4. 기존 동작 회귀 없음 | CI `lint.yml` 등가(node 단위테스트 9종 + `node --check` + JSON + shellcheck) | 전부 통과 |
| 5. 문서 동기화 | README·wiki 대조 | `dlc-doc-drift.js` 설명·workflow-failures 표가 실제 동작과 일치 |

# Review Disposition

- codex Minor 1 (git pathspec 특수문자로 신규 판정 오염) → **partly false-positive, 방어는 fix**. 직접 실측(`ls-tree` 에 `*`·`?`·`[]` pathspec) 결과 매치되지 않아 codex 의 재현 주장은 성립하지 않았으나, `:` 로 시작하는 파일명은 실제 magic 으로 해석되므로 `:(literal)` 을 붙였다(비용 0).
- codex Minor 2 (경계 회귀테스트 부족) → **fix**. `mytest.js`·`x.testxjs.js`·`x.test.jsx`·`x.test.mjs`·backslash 경로 케이스 추가.
- codex 지적 (plan↔코드 함수명·시그니처 drift) → **fix**. `# Decisions`·`# Key Files` 를 실제 구현(`isNewInRepo` / `isNewFile(rel, root)` / `ls-tree`)에 맞춰 정정.
- code-reviewer Major 2건 (README·wiki 동기화 미완 / plan↔구현 불일치) → **false-positive (stale snapshot)**. reviewer 가 읽은 시점이 문서 동기화 커밋 전이다. 현재 `README.md` 는 `readme-trigger-new` 를 2곳에서 서술하고 `workflow-failures.md` 는 sub-class 행 + 횟수 7 을 담고 있으며, plan 의 `cat-file`→`ls-tree` 결정 변경도 반영돼 있다. "커밋 없음"은 사실이었고 이 시점에 커밋한다.
- code-reviewer Minor (fail-quiet 미탐이 문서화 안 됨) → **fix**. `# Decisions` 에 "의도적으로 남긴 미탐 구간 2곳" 명시.
- code-reviewer Minor (`isNewInRepo` 주석의 "경고를 받았다" 단정 과함 — CAP=1 이라 기회는 1회) → **fix**. 문구 완화.
- code-reviewer Minor (`.spec.js`·`.test.mjs` 미커버) → **부분 fix**. `.spec.js` 는 포함, `.test.mjs` 는 위 Decisions 근거로 wontfix.
- code-reviewer Minor (HOME 주입 fixture 가 POSIX 전용) → **fix**. `USERPROFILE` 동시 주입.
- code-reviewer Minor (⑫ HEAD-없는-repo 테스트가 root 해석 실패와 구분 불가) → **fix**. 같은 fixture 에 비-test 표면 대조군 추가.
- code-reviewer Nit (pathspec glob) → **이미 fix** (codex Minor 1 과 동일 건, `:(literal)`).
- code-reviewer Nit (`ok()` 러너가 첫 실패에서 파일 전체 중단 / fixture cleanup 없음) → **wontfix**. 둘 다 이 파일들의 기존 관례이고 이번 변경이 만든 문제가 아니다(§3-4 범위 밖 → `# Deferred`).

# Deferred

- `wiki/index.md` 의 `[[workflow-failures]]` 1줄 요약은 이번 변경으로 바뀌지 않음(횟수·상태는 페이지 본문 소관) → index 편집 없음. `wiki/log.md` 에만 append(WIKI.md 불변규칙 5).
- (경미, 범위 밖) `scripts/*.test.js` 의 `ok()` 러너가 첫 실패에서 파일 전체를 중단시켜 뒤쪽 어서션이 가려진다 — 이번 Red 확인 때 실제로 겪음. 전 테스트 파일 공통 관례라 별도 작업.
- (경미, 범위 밖) `dlc-evidence-ledger.test.js` 가 tmp fixture repo 를 정리하지 않아 실행마다 누적. 기존 fixture 도 동일.

# Workflow Findings

- doc-drift 트리거를 "경로 패턴"으로만 잡으면 README 가 **내용**을 문서화하는 파일과 **존재**만 문서화하는 파일을 구분하지 못한다. 후자는 신규 추가 시에만 트리거해야 한다.
