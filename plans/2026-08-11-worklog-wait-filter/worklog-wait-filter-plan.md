---
title: worklog-wait-filter — 사용자 대기시간을 정면으로 걸러 AI 작업시간만 남긴다
status: in_progress
started: 2026-08-11
updated: 2026-08-11
---

# Goal

jira-worklog 의 시간 측정에서 **사용자 응답 대기**를 role 단계에서 정면으로 제외한다.
지금은 `max_gap`(60분)이라는 거친 백스톱이 그 역할을 대신하느라, 60분 넘게 도는 정상
작업까지 함께 잘라낸다.

# Progress

- 2026-08-11: 실측으로 원인 확정 후 worktree 생성, plan 수립.
- 2026-08-11: 테스트 7건 추가(Red) → `_message_role`(`await_user` role)·`_is_work_gap` 수정 →
  Green. 백스톱 기본값 480분으로 완화하고 `DEFAULT_MAX_GAP_MINUTES` 를 `session_time` 단일
  소스로 통합(config 가 import). SKILL.md·README 동기화.
- 2026-08-11: 실코퍼스 신·구 비교(동일 union 방식) — 구 규칙 60분 66.4h / 480분 78.6h /
  무제한 106.4h 대 **신 규칙 59.0h(백스톱 무관 동일)**. 대기가 role 로 전부 걸러짐을 확인.

# Next

병합 방식 확인(PR vs 로컬 병합) 후 main 반영.

# Decisions

- **대기 제외를 max_gap 이 아니라 role 로 한다.** 실측(세션 157개 전수): 60분 초과 gap 중
  사용자 입력 대기가 아닌 것이 13건뿐이고, 그중 12건이 `AskUserQuestion` 응답 대기,
  1건이 `user→user` 였다. max_gap 은 이 둘의 백스톱 역할만 하고 있었다.
- **규칙 A — `cur == user` 면 prev 가 무엇이든 그 앞 gap 은 대기.** 현행은
  `prev == assistant` 일 때만 대기로 봐서 `user→user`(실측 132분)가 작업시간으로 샜다.
- **규칙 B — `AskUserQuestion`·`ExitPlanMode` 의 tool_use→tool_result 구간은 대기.**
  두 도구는 사용자가 답하기 전에는 tool_result 가 오지 않는다. tool_result 를 assistant 로
  분류(과소계상 방지)한 대가로 생긴 구멍을 여기서 막는다. 실측 `AskUserQuestion` 5분 초과
  49건 / 합 76.6h / 최대 908분 — 전체 대기의 92%.
- **max_gap 은 제거하지 않고 기본값 60분 → 480분(8h).** 제거하자는 의견이 있었고 현
  코퍼스 기준으론 결과가 같지만, 앞으로 추가될 대화형 도구가 같은 구멍을 내면 막을
  백스톱이 필요하다. 완화만으로 현 코퍼스 영향은 0이다.
- **권한 승인 대기는 제외하지 않는다(못 한다).** tool_result 에는
  `type/content/tool_use_id/is_error` 뿐이라 *거부*(`rejected` 132건)는 식별되지만 *승인*은
  정상 결과와 구분되지 않는다. 실측 규모도 작다 — Bash 는 8177건 중 5분 초과 16건,
  최대 17분(실제 실행시간 포함). 이 한계는 SKILL.md 에 명시한다.
- **등록 방식은 현행 upsert 유지.** 세션마다 실행하면 그날 총합이 재계산·갱신되므로
  "매번 시간이 추가된다"는 결과는 이미 충족된다. append 로 바꾸면 재실행 시 이중계상이
  생기고, Jira 쓰기는 revert 가 안 돼 그 대가가 크다.
- **`DEFAULT_MAX_GAP_MINUTES` 는 `session_time` 이 단일 소스**, `config` 가 import 한다.
  반대 방향은 session_time 이 jira_client(네트워크)까지 끌어온다.

# Key Files

- `skills/jira-worklog/jira_kit/session_time.py` — `_message_role`·`_is_work_gap` 이 수정 지점
- `skills/jira-worklog/jira_kit/config.py` — `_DEFAULT_MAX_GAP`
- `skills/jira-worklog/test_session_time.py` — 단위 테스트(stdlib unittest)
- `skills/jira-worklog/SKILL.md` — 측정 규칙·한계 문서

# Blockers

(없음)

# Acceptance

- [x] `user→user` gap 이 작업시간에서 빠진다 — `test_gap_before_user_input_is_wait_whatever_precedes_it`
- [x] `AskUserQuestion`/`ExitPlanMode` 의 tool_use→tool_result 구간이 빠진다 — 각 테스트 통과
- [x] 일반 도구(Bash 등)의 tool_use→tool_result 는 **여전히 작업시간**이다(과소계상 회귀 방지)
      — `test_ordinary_tool_run_is_still_work`
- [x] CI 의 Python 테스트 3종 실행 — session_time 51건(baseline 1건 제외 전부 통과),
      worklog_scope 21건 OK, register_gate 18건 OK
- [x] 실코퍼스 검증 — 신 규칙 총합이 백스톱 60분/480분/무제한에서 모두 59.0h 로 동일(대기가
      role 로 전부 걸러짐). 현행 66.4h 대비 7.4h 감소분이 60분 미만이라 백스톱을 통과하던 대기다.
      `--all` dry-run 실행·출력 관찰 정상.

# Deferred

- `jira-worklog-cwd-attribution` worktree/브랜치는 이미 main 에 반영된 잔재(main 에
  `WorktreeIndex` 존재, 브랜치는 main 보다 80 커밋 뒤처짐). 정리 대상이나 이 작업 범위 밖.
- **baseline failure**: `test_malformed_cwd_does_not_abort` 는 Windows 에서 실패한다
  (`Path("/repo/\0bad").resolve()` 가 OSError 를 내지 않아 MAIN 으로 분류). **main 에서
  동일하게 재현**되어 이번 변경과 무관하고, CI(ubuntu)에서는 통과한다.
