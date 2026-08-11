---
title: native-overlap-followups — 대장 1행 판정 확정 + §13 lesson 적립 + orphan 해소
status: in_progress
started: 2026-08-12
updated: 2026-08-12
---

# Goal

`improve-native-overlap`(PR #139) 이 남긴 후속 3건을 닫는다: (1) 네이티브 격리 실측으로 대장 1행 판정 확정 (2) §13 TDD 순서 위반 lesson 적립 (3) wiki orphan 2건 해소.

# Progress

- 2026-08-12: worktree 생성(base main@84b6c6c). **네이티브 격리 실측 완료** — 아래 Decisions 1.

# Next

대장 1행 `retire` 반영 → lesson 페이지 신설 + MEMORY 인덱스 → orphan 2건 inbound 링크 → index·log 동기화 → 검증.

# Decisions

1. **[실측 확정] 자작 guard 기능 ②(worktree 밖 편집 deny) = `retire`.** worktree 세션에서 main checkout 경로에 Write 를 시도해 관측:

   | 경로 | 자작 guard(`guard-worktree-edit.js` 직접 호출) | 네이티브(실제 Write 시도) |
   |---|---|---|
   | `<main>/plans/native-isolation-probe.md` | **ALLOW** | **DENY** |
   | `<main>/scripts/native-isolation-probe.txt` | DENY | **DENY** |

   네이티브 거부 문구: "This session is isolated in the worktree … Edit the worktree copy of this file instead of the shared-checkout path." — 자작 hook 문자열이 아니다(`scripts/`·`settings.json` 에 부재). 즉 **네이티브 ⊇ 자작 ②, 그것도 진상위집합**(자작이 허용하는 `plans/` 까지 네이티브가 막는다).
   - 정본(changelog v2.1.222)은 "isolation now applies file edits" 라고만 하고 차단/범위를 안 밝혀 **실측이 유일한 근거**였다. 이 경로를 대장에 남긴다.
2. **기능 ①(비-worktree 세션에서 main/master tracked 편집 → `ask`)은 `keep`.** 네이티브 worktree 격리는 *worktree 세션*에만 적용되는데 ①은 worktree 가 아예 없는 세션이 대상이라 교집합이 없다. 대장 1행을 ①/② 로 갈라 서로 다른 verdict 를 준다.
3. **코드 제거는 이번 범위 아님.** `retire` 는 "제거 후보로 랭킹에 올림, 자동 제거 없음"(대장 정의·CLAUDE.md §1). 제거는 승인 후 별도 `wt→dlc`. 이번엔 **판정 기록까지**.
   - 제거 시 함께 사라지는 것: `guard-worktree-deny` telemetry 신호, 구버전 CC 에서의 보호. 별도 작업의 검토 항목으로 남긴다.
4. **lesson 은 §13 형식**(`wiki/pages/decision/lesson-<주제>.md` + `MEMORY.md` 인덱스 한 줄, 명령형). 주제 = "테스트를 나중에 쓰면 경계 결함이 구현 후에야 드러난다".
5. **orphan 2건은 inbound 링크로 해소** — 페이지를 고치는 게 아니라 *관련 페이지에서 링크를 건다*. `lesson-parser-precedent-partial-mirror` 는 새 lesson 과 같은 계열(검증 규율)이라 새 lesson 에서 링크. `lesson-parallel-duplicate-implementation` 은 [[worktree-per-task]] 계열이라 거기서 링크.
6. **리뷰 subagent 생략** — 코드 변경 0(순수 문서·지식 적립). code-reviewer 는 대상이 없고, plan 은 실측 증거가 이미 확정돼 설계 선택지가 없다. 대신 `check_links.py`·`plan-lint`·`improve.sh` 로 기계 검증.

# Key Files

- `wiki/pages/decision/native-overlap-ledger.md` — 1행을 ①/② 로 분리, ② `retire` + 실측 근거. `checked` 갱신.
- `wiki/pages/decision/lesson-test-after-implementation.md` — **신규** §13 lesson.
- `~/.claude/projects/-Users-jongyoonlee--claude/memory/` + `MEMORY.md` — feedback memory 1건 + 인덱스 줄(gitignored, 이 브랜치 밖).
- `wiki/pages/concept/worktree-per-task.md` — `lesson-parallel-duplicate-implementation` inbound 링크.
- `wiki/index.md` · `wiki/log.md` — 동기화(WIKI.md 불변규칙 1·5).

# Acceptance

1. 대장 1행이 ①/② 로 분리되고 ②가 `retire`, 근거에 **관측 표 + 네이티브 원문 거부 문구**가 들어간다. `retire` 집계 줄도 0건 → 1건으로 갱신. 검증: 페이지 read.
2. lesson 페이지가 §13 형식(원인 최소 3 Whys·재현 조건·잘못된 방법·올바른 방법)을 채우고 outbound 링크 ≥2. 검증: read + `check_links.py`.
3. `MEMORY.md` 에 **명령형 행동지시문** 한 줄 + 대응 memory 파일 존재(§12 2단계 둘 다). 검증: 파일 실존 + 인덱스 grep.
4. `check_links.py` **orphan 0건**(현재 2건 → 0). dead link 0 유지. 검증: 실행.
5. `wiki/index.md` 에 신규 lesson 등재 + `wiki/log.md` append. 검증: 실행·read.
6. `bash skills/improve/improve.sh` 가 점검 6(pages=index 개수)·9(대장 신선도) 모두 정상, `error=0 warn=0`. 검증: 실행.

# Blockers

없음.

# Workflow Findings

- **worktree 세션에서 §12 memory 적립이 불가능하다** (2026-08-12 실측, 신규). 네이티브 worktree 격리가 `<main>/projects/…/memory/*.md` write 를 막는데, 그 파일들은 **gitignored 전역 상태라 worktree 복사본이 존재하지 않는다** — 네이티브 안내문("Edit the worktree copy of this file instead")이 가리키는 대상이 없다. 자작 guard 는 이 경로를 의도적으로 예외 처리했으나 네이티브가 먼저 막으므로 hook 으로는 못 푼다.
  - **현재 우회**: memory 적립은 worktree 를 나온 뒤(main 세션에서) 수행. 이번 작업도 그렇게 처리했다.
  - **영향 범위**: §12(feedback memory)·§13(lesson 인덱스 줄)이 dlc 흐름 안에서 완결되지 않는다 — dlc 는 비trivial 을 worktree 로 강제(§3-1)하는데 그 안에서 memory 를 못 쓴다. 구조적 충돌이라 1회로 끝나지 않는다.
  - **후속 후보**: `/e` 마무리 단계에 "main 복귀 후 memory 적립" 스텝을 명시하거나, dlc Report 판정에 이 제약을 적어 둔다. 운영 자산 변경이라 별도 승인·작업.

# Review Disposition

# Deferred

- **자작 guard 기능 ② 제거** — 이번 실측으로 `retire` 확정됐으나 코드 제거는 §1 상 별도 승인·작업(D3). 검토 항목: `guard-worktree-deny` telemetry 상실, 구버전 CC 보호 상실, `guard-worktree-edit.test.js` 중 ② 케이스 정리.
- **문서 내 원문자(⑨⑩⑪⑫) 일괄 전환** — `19a4b56` 규칙은 §0 응답 표기 대상이고 "기존 문서 인용 시 원문 유지" 예외를 두었다. 전환하면 방금 세운 번호 계약(improve.sh↔SKILL↔README)을 동시에 건드려야 해 위험 대비 이득이 낮다. 별도 판단.
