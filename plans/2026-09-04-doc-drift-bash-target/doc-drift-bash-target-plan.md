---
title: doc-drift-bash-target — README 를 Bash 로 고치면 문서 drift 게이트가 오탐하는 문제
status: done
started: 2026-09-04
updated: 2026-09-04
---

# Goal

dlc 문서 drift 게이트(Stop hook)가 "README 를 갱신하지 않았다"고 **오탐**하는 것을 없앤다.
판정을 *어떤 도구로 고쳤나*가 아니라 *파일이 실제로 갱신됐나*로 옮긴다.

# Progress

- 2026-09-04 **한 세션에서 2회 발동**(autopull-hang-guard 작업 중). 매번 오탐이었고 README 는
  실제로 갱신·머지돼 있었다. 사용자가 "수정해" 로 지시.
- 2026-09-04 **근본 원인 확정(코드)**: `scripts/dlc-evidence-ledger.js:127` 의
  `Edit|Write|NotebookEdit` 분기에서만 `drift.applyChange` 가 호출된다. `Bash` 분기(156행)는
  `verified` 만 세팅하고 drift 를 건드리지 않는다. → README 를 **Bash**(`node -e`·`sed`·heredoc)로
  고치면 `readme-target` 이 안 잡혀 `markTarget` 이 안 불리고 `readmeDirty` 가 안 풀린다.
  반면 trigger 를 Edit 로 고치면 dirty 는 세워진다 — **비대칭**.
  (그 세션에서 README 를 Bash 로 고친 이유: Python 편집이 LF→CRLF 를 깨뜨려 shellcheck 가 터졌고,
  README 의 해당 줄이 570~920자 단일 줄이라 도구를 바꿔 다뤘다.)
- 2026-09-04 구현 + TDD(9케이스 추가, 56→65 assertions) + 실제 훅 spawn 관찰.
- 2026-09-04 **code-reviewer REQUEST CHANGES → 전건 fix**(처분표는 `# Review Disposition`).
  규모를 small → **medium** 으로 재판정(모듈 리팩토링 + 신규 테스트 파일 + CI 등록).
  `dlc-doc-drift` 56→**76** assertions, `dlc-early-stop.test.js` **신규 9케이스**.
- 2026-09-04 로컬 CI 전량 재현: unit 14종·JSON·shellcheck·plan-lint 통과.
  유일한 실패는 `test_session_time.py` — **Windows 한정 baseline**(PR #159 의 CI 는 초록,
  `plans/2026-09-04-autopull-hang-guard` 에 입증 기록).
  **Linux 미검증**: 이 세션이 worktree 격리라 가드가 WSL 실행을 거부한다 → CI 가 판정한다.

- 2026-09-04 최신 `origin/main` 재확인 — `0ec47a1`·`5f64718` 이 2커밋 앞서 있었으나 **dlc 훅
  파일은 무변경**(README·settings.json·wiki 만)이라 버그는 그대로였고 충돌도 없었다
  (`git merge-tree` 깨끗). 그 위로 rebase 후 재검증. 부수 확인: 그 커밋들이
  `plans/2026-09-04-autopull-hang-guard` 의 `# Deferred` "배달 순환"(tracked `settings.json`
  이 머신마다 더러워져 커밋이 배달되지 않음, 심각도 상)을 실제로 닫았다.
- 2026-09-04 **PR #160** 생성·머지 → `status: done`.

# Next

(없음 — PR #160 로 머지 완료.)

# Decisions

## 판정을 상태로 옮긴다 — 새 장부 필드 없이

`evaluate(data, mtimeOf)` 에 선택 인자를 더해, dirty 여도 **target(`README.md`/`wiki/index.md`)의
mtime 이 `*Pending` trigger 전부보다 최신이면** 동기화된 것으로 본다. `mtimeOf(rel)→ms|null` 은
호출부가 주입한다(`dlc-early-stop.js` 가 `resolveRoot` + `fs.statSync`) — 모듈은 순수하게 유지되고,
기존 `isNewFile` 주입과 같은 패턴이다.

**장부 필드를 안 늘린 이유**: 시각을 장부에 적으면 "언제 dirty 가 됐나"라는 *순서* 정보를 또 하나
들이게 된다. 모듈 주석(55~56행)이 이미 "문서 동기화는 편집 *순서*가 아니라 *상태*"라고 못박았고,
mtime 비교는 그 원칙의 직접 구현이다. covered-set 과도 독립적으로 겹쳐 동작한다.

**판정 불가는 전부 경고 유지**: `mtimeOf` 미제공(하위호환)·stat 실패·`pending` 비어 있음.
이 게이트는 보조망이라 미탐(조용히 통과)이 오탐보다 나쁘다.

## 알려진 한계 — mtime 은 "내용이 바뀌었나"가 아니다

`touch README.md` 만 해도, 또는 `git checkout`·`merge`·`stash` 가 README 를 재작성해도 mtime 이
갱신돼 통과할 수 있다. 이것은 **의도된 트레이드오프**다: (a) 이 게이트는 capped 1회 soft nudge 이고
fail-open 이라 미탐 비용이 낮다, (b) 종전 구현도 "Bash 로 고친 trigger 는 아예 안 잡힌다"는
더 큰 미탐 구멍을 이미 갖고 있었다. 단일 소스는 CLAUDE.md §3 문서 동기화 규약이고 hook 은 보조망이다.

# Key Files

- `scripts/dlc-doc-drift.js` — `AXIS` 에 `target` 추가, `syncedByMtime()` 신규, `evaluate(data, mtimeOf)`.
- `scripts/dlc-early-stop.js` — `fs`/`path` require, `resolveRoot`+`statSync` 로 `mtimeOf` 주입.
- `scripts/dlc-doc-drift.test.js` — mtime 판정 9케이스(하위호환·동시각·판정불가 3종·index 축·throw).
- `scripts/dlc-evidence-ledger.js` — **수정 안 함**. 원인 지점이지만 Bash 명령에서 편집 경로를
  신뢰성 있게 파싱할 수 없다(임의 셸). 하류에서 상태로 판정하는 쪽이 옳다.
- `README.md` — `dlc-early-stop.js`·`dlc-doc-drift.js` 서술 2곳.

# Blockers

(없음)

# Acceptance

1. **오탐 해소** — dirty + README 가 pending trigger 보다 최신이면 경고 없음. 실제 훅 spawn 으로 관찰.
2. **미탐 미도입** — trigger 가 README 보다 최신이면 여전히 경고. 실제 훅 spawn 으로 관찰.
3. **판정 불가는 경고 유지** — `mtimeOf` 미제공·stat 실패·pending 없음 3종.
4. **fail-open 유지** — `mtimeOf` 가 throw 해도 훅이 죽지 않는다.
5. **하위호환** — `evaluate(data)` 단일 인자 호출이 종전대로 동작(기존 테스트 불변).
6. **문서 동기화** — `README.md` 두 서술을 같은 브랜치에서 갱신.

# Review Disposition

code-reviewer 2026-09-04 (REQUEST CHANGES) — 전건 fix. Codex 는 크레딧 소진으로 생략(§9).
리뷰가 훅을 직접 spawn 해 **CONFIRMED Major 2건을 재현**했다. 둘 다 순수 모듈 테스트 9케이스를
전부 통과한 채 존재했다 — 그 사실 자체가 "훅 쪽 절반이 미검증"이라는 증거였다.

| # | 지적 | 처분 | 조치 |
|---|---|---|---|
| M1 | 축별 억제 후에도 신호를 dirty flag 로 emit → 출력 안 한 경고의 failure telemetry 잔존 | **fix** | `evaluate` 가 `[{axis, message}]` 반환, early-stop 이 그 축으로만 emit |
| M2 | `*Pending` 의 rel 은 편집 시점 root 기준인데 Stop 시점 root 로 stat → main 으로 옮기면 게이트 무력화(실측 scripts 23/26·wiki 46/47) | **fix** | `driftRoot` 를 ledger 에 핀 고정(두 root 를 오가면 `''`), Stop 시점 root 와 다르면 mtime 판정 포기 |
| m1 | mtime 동기 시 covered-set 미갱신 → 재편집 오탐 잔존 | **fix** | `settle()` 신규 — trigger 단위로 갈라 covered 로 이동, 남은 게 없으면 dirty 해제 |
| m2 | README 의 "비대칭이 사라진다"·"미탐 미도입" 과장 + 트레이드오프 미기재 | **fix** | 과장 정정 + 미탐 클래스(`touch`·`git checkout/stash/restore`·포매터) 명시 |
| m3 | `typeof !== 'number'` 가 NaN 통과 → 판정 불가가 미탐 쪽으로 | **fix** | `Number.isFinite` |
| m4 | `dlc-early-stop.js` 테스트 부재 | **fix** | `dlc-early-stop.test.js` 신규 9케이스 + `lint.yml` 양쪽 등록 |
| n1 | pending 상한(50) 절삭이 이제 미탐 경로 | **fix** | 상한 도달 시 판정 불가로 처리 |
| n2 | rel 이 stat 에 쓰이는데 `..` 미검사 | **fix** | `classify` 에서 `..` 세그먼트 거름 |
| n3 | AXIS 주석이 "ledger 필드명"인데 target 경로도 담김 | **fix** | 주석 정정 |
| n4 | 최대 102 syscall | **wontfix** | 리뷰도 "무시할 수준, 기록만" |

## M1 은 이제 테스트로 잠기지 않는다 (정직한 기록)

mutation 으로 확인한 결과, 신호 emit 을 dirty flag 로 되돌려도 **테스트가 잡지 못한다**.
`settle` 이 `evaluate` 보다 먼저 dirty 를 해제하므로 두 구현이 현재 **동치**이기 때문이다.
즉 M1 의 결함 경로는 m1 의 `settle` 도입으로 이미 닫혔고, 축 기반 emit 은 그 위의 **구조적 보증**
(출력한 것만 신호로 남긴다)이다. 테스트로 못 잠근다는 사실을 숨기지 않고 여기 남긴다 —
나중에 `settle` 을 걷어내면 M1 이 되살아나므로, 그때 이 항목을 근거로 축 emit 을 지켜야 한다.

## mutation 검증 (고친 뒤 실제로 잡히는가)

| mutation | 결과 |
|---|---|
| `driftRoot` 대조 삭제 (M2 되돌리기) | **FAIL = 잡힘** |
| 신호를 dirty flag 로 emit (M1 되돌리기) | PASS = 안 잡힘 → 위 절에 사유 기록 |
| `settle` 결과 저장 제거 | **FAIL = 잡힘** |
| NaN 가드를 `typeof` 로 완화 | **FAIL = 잡힘** |

# Deferred

(없음)

# Workflow Findings

- 같은 Stop hook 오탐이 **한 세션에 2회** 발동했고, 나는 두 번 다 "오탐 — 조치 불필요"로 닫았다.
  CLAUDE.md §3-6 이 오탐 대응을 결론 1줄로 제한하고 있어 그 자체는 규약대로였지만, **2회 반복은
  운영 자산을 고칠 신호**(dlc "Workflow Findings" 의 트리거 ②·③)였는데 승격 판정을 하지 않았다.
  사용자가 "수정해"로 지시하고서야 착수했다.
