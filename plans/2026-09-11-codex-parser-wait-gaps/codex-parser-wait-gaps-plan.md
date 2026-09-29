---
title: codex-parser-wait-gaps — Codex 파서의 사용자 대기·turn 사이 공백을 작업시간에서 제외
status: done
started: 2026-09-11
updated: 2026-09-28
---

# Goal
jira-worklog 의 Codex 세션 파서가 turn 사이 공백(사용자 응답 대기)과 `request_user_input` 대기 구간을 AI 작업시간으로 계상하지 않게 한다. worklog-gap-24h plan `# Deferred` 1·2 승계.

# Intent
- **Problem**: Codex 파서는 `event_msg user_message` 만 사용자 입력 신호로 본다. 2026-08 부터 Codex 는 이 이벤트를 기록하지 않고(8월 rollout 450개 중 353개, 9월 47/47 이 `response_item role=user` 만) 사용자 입력이 `response_item` 으로만 남는다. 그 결과 turn 종료 후 다음 turn 시작까지의 대기(밤새 16시간 포함)가 전부 작업으로 잡힌다. 실측(rollout 1004개, 설계 규칙 task_started→user 로 재계산): 현행 합계 1029.5h → 469.9h, 1분 초과 변동 파일 302개(날짜 단위까지 세면 998/1004), 증가 0건, 합계가 0 이 되는 세션 0건, 사라지는 (세션,날짜) 0건. **과거 Jira 등록의 원천 값도 전부 바뀐다** — 3~7월 rollout 도 거의 전부 lifecycle 이벤트를 갖는다. `request_user_input` 대기도 같은 이유로 포함된다(코퍼스에 호출 1건 — 영향은 작지만 같은 결함 계열).
- **Constraints**: stdlib only 유지. Claude 파서·`_is_work_gap`·`ai_intervals` 계약은 바꾸지 않는다(Codex 이벤트가 role 을 정확히 달아 기존 필터에 태운다). lifecycle 이벤트가 없는 rollout(5/1004)만 현행과 같은 결과다 — user_message 유무는 불변식의 기준이 아니다(3~7월 파일도 `task_started` 를 가져 값이 바뀐다). Jira 쓰기는 하지 않는다.
- **Out of scope**: Deferred 3(부모/자식 subagent 세션 중복 합산), Deferred 4(`.env` override 보안), Codex 세션 중 cwd 이동 분할(실측 0건).
- **Open questions**: 없음 — 사용자가 Deferred 1+2 진행을 선택(2026-09-11).

# Progress
- 2026-09-28: 통합 재개(사용자 승인). 선행 worklog-gap-24h 가 PR #197 로 origin 에 들어가 이 브랜치의 옛 gap-24h 커밋(c7cdc8d·6d91c68)과 같은 내용이 다른 sha 로 존재 → origin/main 병합, 충돌 3곳(README 1·SKILL 2)은 이 브랜치 문장이 origin 문장을 포함하고 Codex 설명을 더한 형태라 이 브랜치 쪽으로. 병합 트리에서 jira 테스트 4파일 OK.
- 2026-09-29: 전체 verify(Windows) — jira 축 전부 ok, 실패 3건은 origin/main 과 같은 기존 결함(#190). `/e merge` — PR #198.
- 2026-09-14: `/e` 체크포인트. 정식 커밋 1b1ae38 이 브랜치에 있고 tree clean(WIP 없음). 사용자가 변경 확인 후 통합은 보류·종료 선택. 미머지라 worktree 유지.
- 2026-09-11: simplify 점검(상수 3개+generator 1개, 정리 대상 없음 — docstring 과장 1곳만 수정). 격리 runner: `bash scripts/verify.sh` exit 0 `ALL PASS`(skip 없음), unittest 119개 OK. evidence gate 7항목 전부 증거 충족 → DONE(통합 대기). 커밋 후 로컬 ff-merge 는 medium 이라 `/e merge` 또는 사용자 판단.
- 2026-09-11: code-reviewer REQUEST CHANGES(Critical 0·Major 1·Minor 6) → 전부 반영. 독립 재계산으로 Acceptance 5 재현, verify.sh ALL PASS·118 tests 확인(리뷰어 실행).
- 2026-09-11: TDD Red(9 실패) → 구현 → 118개 통과. 실코퍼스 HEAD vs 구현 비교: 1029.5h → 469.9h, 0 이 되는 세션 0, 1분 초과 증가 0(최대 +13초/파일 — `task_complete`가 마지막 응답 뒤 ~0.3초에 찍혀 그 꼬리가 새로 계상됨), `codex:b86f994b` 1038.5m → 16.6m. SKILL·README 갱신.
- 2026-09-11: 로컬 main@6d91c68 에서 worktree 생성(origin/main 은 gap-24h 미포함이라 로컬 기준). 코퍼스 조사로 형식 전환·영향 실측. plan 작성.
- 2026-09-11: plan-reviewer CONDITIONAL — 초기 실측(494.7h)이 설계와 다른 변형(task_started→assistant)에서 나온 것을 지적, 설계 규칙 재계산 469.9h(차이 24.79h/7파일). `codex:b86f994b` 1038.5m → 16.6m 확인. pending 미종료·구형식 불변식 오기·기각 대안 누락을 아래에 반영. Codex 병행은 `out of credits` 로 생략(세션 마커).

# Next
머지 후 첫 `--register` 는 과거 Codex 항목이 게이트에 걸리는 것이 정상 — `--allow-large-change` 판단.

# Decisions
- **lifecycle 이벤트를 role 로 번역해 기존 `_is_work_gap` 에 태운다** — `task_started` → `user`(직전 gap 제외. turn 시작 전은 실측상 대기다 — 예외 상한은 자동 compaction turn 44건으로 24.79h 안. `task_complete` 없이 끊긴 turn 208건도 덮는다), `task_complete`/`turn_aborted` → `await_user`(직후 gap 제외). 별도 active-turn 상태기계는 두지 않는다(이유: Claude 쪽 `await_user` 와 같은 메커니즘이라 코드·테스트가 한 규칙으로 설명되고, 상태기계는 turn 미종료 케이스마다 분기가 늘어난다). 기각 대안 1: "complete/abort 만 await_user, task_started 는 계상 이벤트 유지" — `task_complete 10:00:22 → RI:message/user 10:00:29 → 15시간 공백 → task_started 다음날 01:05`(01a056c3) 형태가 실존해 첫 6초만 제외되고 15시간이 남는다(7파일 24.79h). 기각 대안 2: `response_item role=user` 를 사용자 입력으로 보기 — Codex 는 `<environment_context>`·AGENTS.md 등 시스템 컨텍스트도 role=user 로 넣어 구분 불가(기존 docstring 의 근거 유지).
- **`request_user_input` 은 call_id 로 대기 구간을 묶는다** — function_call 을 `await_user` 로 표시하고, 같은 call_id 의 function_call_output 이 올 때까지 사이 response_item 도 `await_user`. 코퍼스엔 호출·출력이 인접해 role 표시만으로도 충분하지만, 사이에 reasoning 이 끼면 두 번째 gap 부터 새므로 call_id 로 닫는다. **pending 은 turn 경계(`task_started`/`task_complete`/`turn_aborted`)와 파일 경계에서 비운다** — output 없이 끝나는 function_call 이 코퍼스 세션 중간에 4건 있어, 안 비우면 그 시점 이후 세션 전체가 await_user 로 0 이 된다. `codex_events` 는 파일 list 를 받으므로 파일마다 초기화한다.
- role `user` 는 Codex 파서에서 "진짜 사용자 입력"이 아니라 "직전 gap 을 대기로 판정하라"는 표시로 쓴다 — `_is_work_gap` 계약은 그대로 두고 의미 과부하를 `codex_session.py` docstring 에 명시한다.
- **lifecycle 없는 rollout(5/1004) 은 현행 동작 유지** — 새 규칙은 이벤트가 있을 때만 작동하므로 별도 fallback 코드가 필요 없다.
- 과거 Jira 등록값과의 차이는 등록 게이트(30분 & 50% 변동 시 중단)가 잡는다. 재등록되는 과거 날짜는 50% 감소가 정상 방향이라 **사실상 전부 게이트에 걸린다** — 첫 `--register` 에서 `--allow-large-change` 가 필요한 것이 이상 징후가 아님과, 복구 근거가 `~/.claude/logs/jira-worklog-<날짜>.jsonl` 임을 SKILL 에 적는다.

# Key Files
- skills/jira-worklog/jira_kit/codex_session.py — `codex_events` role 판정(변경 대상). 모듈 docstring 의 "user_message 로만 판별" 서술 갱신.
- skills/jira-worklog/test_session_time.py — Codex 이벤트 테스트 추가(`rollout` helper 확장).
- skills/jira-worklog/SKILL.md, README.md `### skills/jira-worklog/` — Codex 대기 제외 규칙 서술 동기화.
- plans/2026-09-11-worklog-gap-24h/worklog-gap-24h-plan.md — 승계 원본(Deferred 1·2).

# Blockers
없음.

# Acceptance
1. `task_complete` → (공백) → `task_started` 사이가 작업구간에서 제외된다 — 단위 테스트: complete 후 120분 뒤 started 인 rollout 의 합이 0, started 이후 response_item 간격만 계상. 통과 기준: assert 통과.
2. `turn_aborted` 뒤 공백도 제외된다 — 단위 테스트 1과 동형.
3. `request_user_input` function_call 부터 같은 call_id 의 function_call_output 까지가 제외되고, 사이에 다른 response_item 이 끼어도 새지 않는다 — 단위 테스트.
4. user_message 만 있고 lifecycle·request_user_input 이 없는 rollout 의 결과가 변경 전과 동일하다 — 기존 Codex 테스트 무수정 통과 + 새 회귀 테스트. (코퍼스의 lifecycle 없는 5개는 전부 빈 파일이라 이 범위 밖 불변식은 주장하지 않는다.)
4a. pending 이 output 없이 끝나도(turn_aborted 후) 다음 turn 의 시간이 계상된다 — 단위 테스트. 파일 2개를 한 list 로 넘겨도 앞 파일의 pending 이 뒤 파일에 새지 않는다 — 단위 테스트.
4b. 같은 timestamp 의 `task_complete` 가 response 뒤에 남는다(안정 정렬) — tie 가 뒤집히면 값이 달라지는 판별형 입력(10분 vs 20분) 단위 테스트. `task_complete` 와 다음 `task_started` 사이에 계상 이벤트가 2개 이상이면 그 사이 gap 은 제외되지 않는다 — 경계 고정 테스트.
5. 실코퍼스 dry-run: 세션 `codex:b86f994b`(2026-09-10 부모 세션) 합계가 현행 약 1038m 에서 1시간 미만으로 내려가고, 전 rollout 에서 1분 초과 증가 0건(turn 경계 이벤트가 마지막 응답 뒤 수 초를 더해 파일당 최대 13초 증가는 있다) — `--all` 실행 관찰 + 구현 모듈로 old/new 전수 비교 스크립트.
6. README·SKILL.md·codex_session.py docstring 의 Codex 대기 제외 서술이 구현과 일치한다 — diff 대조.
7. `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음) + `py -3 -m unittest discover -s skills/jira-worklog -p 'test_*.py'` 전부 통과 — 격리 runner.

# Review Disposition
- plan-reviewer 강한 1(실측 변형 불일치) → fix: 469.9h 로 갱신, 임계값 명시. 강한 2(pending 미종료) → fix: turn·파일 경계 clear + 테스트 4a. 강한 3(구형식 불변식) → fix: Constraints·Acceptance 4 재서술, 과거값 변경 명시.
- code-reviewer Major 1(tie 테스트 판별력 없음) → fix: 판별형 입력으로 교체. Minor 6 → 전부 fix: call_id str 가드(+테스트), legacy 테스트명·Acceptance 4 범위 정정, SKILL "Claude 에서"/"이 대기들"/8월 전환기 수치, README 동일, `_is_work_gap` 포인터, user_message 유지 근거 docstring. Nit(상수 비대칭) → fix: `_GAP_BEFORE_IS_WAIT`/`_GAP_AFTER_IS_WAIT` 로 통일.
- 약한: role 의미 과부하 docstring → fix. 기각 대안·핵심 시퀀스 → fix(Decisions). Codex 승인 대기 315m·compaction·review_mode → defer(# Deferred). 누락 시나리오(동일 ts 정렬·2개+ 이벤트·단조성) → fix(Acceptance 4b·5).

# Deferred
- worklog-gap-24h Deferred 3(부모/자식 중복)·4(.env override 보안)는 그대로 미착수 — 그 plan 참조.
- Codex 승인·hang 대기는 여전히 전액 계상: `019ff402` 에 `exec` call → output 단일 구간 315.2분 실존. Claude `_AWAIT_USER_TOOLS` 에 대응하는 Codex 필터 없음(중간·codex_session.py).
- 자동 compaction turn 의 직전 작업 공백 제외 — code-reviewer 전수 측정 3건·합계 36초(무시 가능, 닫음). turn 종료 후 작업이 이어지는 형태의 과소계상도 4건·0.03h.
- `request_user_input` 이 Codex 의 유일한 사용자 응답 대기 도구인지 미확인(코퍼스 1건). lifecycle 이벤트가 미래에 사라지면 파서는 경고 없이 옛 과다계상으로 돌아간다 — "response_item 은 있는데 lifecycle·user_message 가 없는 rollout" 을 dry-run 에서 알리는 것은 별도 작업.
- `entered_review_mode`(10건) 직후 task_started 는 제외 대상으로 두었으나 별도 검증 없음(낮음).
