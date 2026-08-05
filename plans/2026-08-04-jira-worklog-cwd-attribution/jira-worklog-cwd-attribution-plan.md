---
title: jira-worklog-cwd-attribution — 세션 줄 단위 cwd로 worktree별 시간 귀속
status: in_progress
started: 2026-08-04
updated: 2026-08-05
---

# Goal

Claude 세션 하나가 여러 worktree를 오갈 때 세션 파일이 마지막 위치로 이동해 시간이 한 worktree에 몰리는 문제를 고친다. 각 로그 이벤트의 `cwd`를 가장 구체적으로 일치하는 Git worktree에 귀속해 Jira worklog 시간이 worktree별로 누락·중복 없이 누적되게 한다.

# Progress

- 2026-08-04: 원인과 실측을 확인했다. 현재 파서는 세션 파일이 있는 프로젝트 폴더의 모든 이벤트를 한 worktree 시간으로 합산하며, 실제 Claude `user`/`assistant` 이벤트에는 줄 단위 top-level `cwd`가 있다. 별도 `jira-worklog-cwd-attribution` worktree에서 구현을 시작했다.
- 2026-08-05: A→B→A·중첩 worktree·단일 worktree fixture를 먼저 추가해 Red(`ai_worklogs_by_worktree` 미구현 ImportError)를 확인했다. 이후 Claude 줄 단위 cwd 매핑, 관련 project slug 탐색, Codex 다중 worktree 탐색, CLI 단일 스캔 배선을 구현했다.
- 2026-08-05: Green 검증으로 `test_session_time.py` 7개, `test_worklog_scope.py` 21개가 통과했고, 운영 모듈 `py_compile`과 `ruff check skills/jira-worklog`도 통과했다.
- 2026-08-05: 실제 `jira_worklog.py --all --timezone UTC`가 exit 0으로 실행됐고 `.claude`와 `plan-done-cleanup` worktree를 별도 결과로 출력했다. 환경에 `tzdata`가 없어 UTC 해석 경고만 발생했다.
- 2026-08-05: `skills/jira-worklog/SKILL.md`, `skills/e/SKILL.md`, `README.md`에 Claude 줄 단위 귀속·Codex 파일 단위 한계·`--all` 단일 계산 경로를 동기화했다.
- 2026-08-05: 최종 검증 중 Codex fixture의 동일 `mtime` 순서 가정을 발견해 포함 집합 검증으로 고쳤고, 세션 귀속 7개·기존 worklog 21개·`py_compile`·`ruff`·`git diff --check`를 다시 통과했다.

# Next

구현·문서·검증 결과를 현재 worktree에 보존하고 사용자에게 handoff한다. merge/push는 하지 않는다.

# Decisions

- Claude 이벤트는 파일 위치가 아니라 각 JSONL 줄의 top-level `cwd`를 기준으로 귀속한다. 파일은 세션 중 마지막 cwd의 프로젝트 디렉토리로 이동하므로 파일 폴더를 기준으로 삼으면 A→B 이동 시간이 B에 몰린다.
- cwd가 worktree 내부 하위 디렉토리여도 가장 긴 worktree path prefix를 선택한다. 중첩 worktree에서 짧은 상위 prefix로 오귀속되는 것을 막는다.
- worktree 경계를 가로지르는 이벤트 간 gap은 어느 worktree에도 배정하지 않는다. 이동 시간을 A 또는 B에 넣으면 중복·오귀속이 생긴다.
- Codex는 rollout 첫 줄의 `session_meta.payload.cwd`만 제공하므로 기존 파일 단위 귀속을 유지하고, 세션 중 worktree 이동은 지원 한계로 문서화한다.
- `--all`은 관련 Claude/Codex 세션을 한 번 발견·파싱해 worktree별 결과를 나눠 반복 스캔을 피한다.
- `SessionFiles`에 현재 대상과 저장소 worktree 목록을 보존한다. 새 discovery 호출은 줄 단위 귀속을 사용하고, 외부에서 직접 만든 구형 `SessionFiles` 호출은 기존 파일 단위 합산을 유지한다.

# Key Files

- `skills/jira-worklog/jira_kit/session_time.py` — Claude 세션 파일 범위, 줄 단위 cwd 파싱, longest-prefix 매핑, worktree별 시간 합산.
- `skills/jira-worklog/jira_worklog.py` — 선택된 worktree 집합에 대한 단일 세션 스캔 결과 배선.
- `skills/jira-worklog/test_session_time.py` — A→B→A, 중첩 prefix, 단일 worktree 회귀 fixture.
- `skills/jira-worklog/SKILL.md` — Claude/Codex 귀속 기준과 한계 문서화.
- `skills/e/SKILL.md` — worklog 실행 순서의 의미와 Claude 줄 단위/Codex 파일 단위 차이 동기화.
- `README.md` — jira-worklog 구성요소 설명 동기화.

# Blockers

없음.

# Acceptance

- [x] 한 JSONL에 A→B→A 이벤트가 섞인 fixture에서 A/B가 자기 구간만 받고 합계가 실제 AI 구간을 넘지 않는다. (`test_a_to_b_to_a_intervals_are_not_mixed`)
- [x] 중첩 worktree fixture에서 하위 worktree 이벤트가 상위 worktree로 새지 않는다. (`test_longest_worktree_prefix_wins`)
- [x] cwd 이동이 없는 단일 worktree 세션의 계산 결과가 기존 interval 규칙과 동일하다. (`test_single_worktree_keeps_existing_interval_rules`)
- [x] 실제 Claude 세션 dry-run에서 `.claude`와 `plan-done-cleanup` worktree 시간이 별도 결과로 관찰된다. (`--all --timezone UTC`, exit 0)
- [x] `--all` dry-run이 관련 세션을 저장소 단위로 한 번 계산하는 경로로 실행되고 기존 CLI 출력·티켓 marker 계약을 유지한다. (실행 exit 0, marker 출력 경로 유지)
- [x] 대상 테스트와 운영 스크립트 문법·정적 검사가 통과한다. (7+21 tests, `py_compile`, `ruff`, `git diff --check`)
- [x] merge/push를 수행하지 않고 작업 브랜치에 변경을 보존한다. (현재 `jira-worklog-cwd-attribution` worktree)

# Review Disposition

# Deferred

# Workflow Findings
