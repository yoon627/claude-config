---
title: worklog-per-session — worklog 항목을 세션 단위로 나눠 등록한다
status: in_progress
started: 2026-08-11
updated: 2026-08-11
---

# Goal

worklog 등록 단위를 (티켓, 날짜, worktree) → **(티켓, 날짜, worktree, 세션)** 으로 바꾼다.
세션이 끝날 때마다 그 세션 몫이 독립 worklog 항목으로 남아, "이 작업을 언제 얼마나 했나"를
세션 단위로 되짚을 수 있게 한다.

# Progress

- 2026-08-11: `jira-worklog-wait-filter`(PR #137) 위에 stacked worktree 생성, 설계 수립.
- 2026-08-11: markers(세션 차원 + `parse_scope`) → session_time(세션별 구간 유지 +
  `session_key`) → worklog_register(세션×날짜 plan/upsert, rival 재정의) → CLI 통합 순으로 구현.
- 2026-08-11: dry-run 실행에서 **앞 8자 축약이 Codex UUIDv7 과 구조적으로 충돌**함을 발견
  (수십 건). 뒤 8자로 정정하고 재실행해 충돌 0 확인.
- 2026-08-11: 테스트 3종 통과(session_time 60 / scope 29 / gate 19), dry-run 관찰 정상.

# Next

PR #137 머지 후 이 브랜치를 rebase 하고 PR 생성.

# Decisions

- **세션 id 를 마커에 넣는다** — 워터마크가 필요 없어진다. 세션 id 자체가 자연스러운 분할
  키라, 같은 세션을 두 번 등록해도 그 항목을 찾아 갱신하므로 **멱등성이 유지**된다.
  마커: `[jira-kit] worklog <티켓> <날짜> (<worktree>) [<세션>]`
- **세션 식별 근거는 파일명**: Claude `<uuid>.jsonl`, Codex `rollout-<ts>-<uuid>.jsonl`.
  둘 다 이미 파일 단위로 파싱하고 있어 추가 스캔이 없다.
- **겹침 union 포기는 수용한다.** 세션별로 쪼개면 동시 실행 세션의 겹치는 시간을 union 으로
  지울 수 없다. 실측(knowledge_base): 전체로는 77.66% 과다지만 그 대부분이 `main` bucket
  (티켓 없음 → 등록 대상 아님)이고, **등록 대상 worktree 만 보면 합계 약 2.3h**
  (review-show-original 71분, CSTP1-2812 58분, 나머지 8분). worktree 94개 중 89개는 겹침 0.
- **stacked on PR #137.** 대기 필터가 아직 머지 전이고 `session_time.py` 를 같이 건드리므로
  main 이 아니라 그 브랜치를 base 로 한다. #137 머지 후 rebase.
- 항목 수 증가는 감수한다 — CSTP1-2812 기준 3항목 → 22항목(7/22 하루가 15항목). 티켓 총
  Time Spent 는 Jira 가 합산하므로 동일하다.
- **구형 마커는 중단이 아니라 경고**(사용자 판단 2026-08-11: "예전 기록과 누적돼 더 계산돼도
  상관없다"). `legacy_worklog_marker`(worktree 없음)의 기존 **중단**은 그대로 두고, 이번에
  생기는 "세션 없는 구형"만 경고로 흘린다 — 전자는 귀속 자체를 알 수 없어 성격이 다르다.
- **세션 id 는 8자 축약**(사용자 결정) — 단 **앞이 아니라 뒤 8자**로 간다(2026-08-11 실측으로
  정정). Codex rollout id 는 **UUIDv7** 이라 앞 48비트가 timestamp 라서, 앞 8자로 줄이면 수 초
  안에 시작된 세션끼리 그대로 겹친다 — 실제 코퍼스에서 **수십 건**이 충돌했다. 뒤 8자는 두
  형식 모두 랜덤 영역이라 같은 가독성으로 충돌이 0이 된다(재실행 확인).
- 그래도 겹칠 수 있으므로 등록 전에 **축약 충돌을 감지해 경고**한다(합쳐져도 시간은 합산되어
  남지만 세션 단위 추적이 깨진다).

# Key Files

- `skills/jira-worklog/jira_kit/markers.py` — 마커에 세션 차원 추가, 구형 탐지 2단계
- `skills/jira-worklog/jira_kit/session_time.py` — bucket 별 구간을 세션 단위로 유지
- `skills/jira-worklog/jira_kit/worklog_register.py` — 세션×날짜 단위 plan/upsert, rival 판정
- `skills/jira-worklog/jira_worklog.py` — process/_register/출력
- `skills/jira-worklog/test_worklog_scope.py`, `test_register_gate.py` — `worklog_marker`
  호출부가 20여 곳이라 시그니처 변경의 영향을 받는다

# Blockers

(없음)

# Acceptance

- [x] 세션마다 worklog 항목이 따로 생긴다 — `test_other_session_entry_is_not_overwritten`,
      `test_each_session_keeps_its_own_intervals`
- [x] 같은 세션을 두 번 등록해도 항목이 늘지 않고 갱신된다(멱등) —
      `test_same_session_rerun_updates_only_that_entry`
- [x] 세션 id 없는 구형 마커는 **중단이 아니라 경고**(사용자 결정으로 변경) —
      `test_sessionless_entry_does_not_abort`, `test_sessionless_entry_is_reported_for_warning`
- [x] 같은 worktree 의 다른 세션을 rival 로 오판하지 않는다 —
      `test_other_session_of_same_worktree_is_not_a_rival`
- [x] CI 의 Python 테스트 3종 — session_time 60건(Windows baseline 1건 제외 통과),
      worklog_scope 29건 OK, register_gate 19건 OK
- [x] dry-run 실행·관찰 — 세션별 항목이 `[claude:xxxxxxxx]` 로 나뉘어 출력되고, 축약 충돌
      경고 0건

# Deferred

- `test_malformed_cwd_does_not_abort` 는 Windows 한정 baseline failure(main 재현 확인,
  CI ubuntu 통과). PR #137 의 plan 에도 같은 항목이 있다.
