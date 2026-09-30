---
title: worklog-deletion-safety — worktree 를 지울 때 등록하지 못한 AI 작업시간을 잃지 않게
status: open
started: 2026-09-30
updated: 2026-09-30
---

# Problem
worktree 를 지우면 그 worktree 의 AI 작업시간은 Jira worklog 에 등록할 수 없다. 등록은 이름(또는 cwd)으로 살아 있는 worktree 를 고를 때만 되고, 지운 worktree 의 시간은 "삭제된 worktree" 로 표시만 된다. 지우는 경로는 `/e` 7단계 자동 정리와 `/wt rm` 두 가지다.

# Proposed outcome
두 삭제 경로 모두 지우기 전에 등록하지 않은 시간을 막거나 알린다. `/e` 의 게이트가 기대는 `jira_worklog` 종료코드 계약은 테스트로 고정한다.

# Constraints
- worklog 등록은 사용자가 동의한 경로에서만 한다 — `/e` 6단계(`/e` 호출이 등록 표준 동의)와 사용자가 직접 부르는 `--register`. 삭제 경로가 등록을 대신 하지 않는다.
- `jira_worklog.py` 의 동작은 바꾸지 않는다 — 계약을 문서와 테스트로 고정한다.

# Out of scope
- Windows 에서 `run_worklog.ps1` 의 비0 종료가 도구 결과에 보이는지 — Windows 에서만 확인할 수 있어 이슈 #190 댓글로 옮겼다(2026-09-30).
- Jira 에 이미 등록됐는지 조회하는 모드 — 등록이 upsert(멱등)라 "먼저 `--register`" 안내로 충분하다.

# Open questions

# Plans
- `plans/2026-09-30-e-worklog-gate/e-worklog-gate-plan.md` — `/e` 6단계 worklog 가 실패하면 7단계 자동 정리를 생략한다(문서). 이 묶음은 그 plan 의 `# Deferred` 에서 소급으로 만들었다.
- `plans/2026-09-30-worklog-followups/worklog-followups-plan.md` — 종료코드 계약 테스트, `--all` 기전 문구 정정(jira-worklog SKILL·CLAUDE.md §8), `/wt rm` 의 worklog 미리보기 경고.
