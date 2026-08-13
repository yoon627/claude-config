---
title: jira-task — Claude·Codex 작업내용 Jira comment 기록 skill
status: in_progress
started: 2026-08-13
updated: 2026-08-13
---

# Goal

Claude와 Codex에서 공통으로 호출할 수 있는 `jira-task` skill을 추가한다.
작업 요약을 Jira issue comment로 미리보기한 뒤 명시적으로 게시하고, 동일 표식으로 재실행 중복을 막는다.

# Progress

- 2026-08-13: 기존 `jira-worklog`, shared skill junction, 저장소 dirty 상태와 Jira 공식 comment API를 확인했다.
- 2026-08-13: 기존 `main` 변경을 보존하기 위해 `jira-task` worktree/브랜치를 생성했다.
- 2026-08-13: `skill-creator` 템플릿으로 `skills/jira-task`를 초기화하고 Jira comment preview/post/upsert CLI와 16개 단위 테스트를 구현했다.
- 2026-08-13: Unicode stdout, HTTPS credential 전송, marker 중복·타 author 보호를 보강했다. `ruff`, `quick_validate`, preview, 새 테스트가 통과했다.
- 2026-08-13: README와 GitHub Python test workflow를 동기화했다.
- 2026-08-13: `C:\Users\yoon627\.agents\skills\jira-task` junction을 생성해 Claude·Codex discovery 경로에서 동일 skill을 확인했다.
- 2026-08-13: staged secret guard·diff check 후 작업 브랜치에 commit으로 보존했다. main merge/push는 수행하지 않았다.

# Next

사용자 방향에 따라 `jira-task` branch를 main에 반영한다. 반영 후 Codex junction target을 main의 `skills/jira-task`로 변경하고 이 plan을 done으로 닫는다.

# Decisions

- 작업내용은 Jira issue description을 덮어쓰지 않고 append-only 성격의 issue comment로 기록한다.
- 외부 Jira 쓰기는 기본 dry-run이며 `--post`로만 실행한다. 게시 전 skill이 사용자 확인을 받는다.
- 인증은 기존 `~/.jira-kit/.env` 계약을 재사용하되, CLI는 `jira-worklog` 코드에 의존하지 않아 skill 단독 설치도 가능하게 한다.
- `skills/jira-task`를 저장소 정본으로 두고, 설치된 Codex discovery 경로에는 이 디렉터리를 가리키는 junction을 만든다.
- comment marker는 ticket·worktree·session을 포함해 조회/갱신에 사용한다. marker가 없는 기존 comment는 수정하지 않는다.

# Key Files

- `skills/jira-task/SKILL.md` — Claude·Codex용 사용 절차와 안전 게이트.
- `skills/jira-task/jira_task.py` — Jira comment preview/post/upsert CLI.
- `skills/jira-task/test_jira_task.py` — 인증·ADF·marker·API 요청 단위 테스트.
- `README.md` — skill 목록과 사용법.
- `plans/2026-08-13-jira-task/jira-task-plan.md` — 현재 작업 handoff.

# Acceptance

- [x] skill frontmatter가 `quick_validate.py`를 통과한다(`Skill is valid!`).
- [x] CLI가 token 없이 preview를 수행하고 comment 원문/대상/동작을 출력한다.
- [x] marker가 있는 본인 comment는 중복 POST 대신 update 경로를 사용한다.
- [x] API 오류와 인증 오류가 token 원문 없이 실패한다.
- [x] 새 skill `ruff check`, `ruff format --check`, Python 16개 테스트가 통과한다.
- [x] README와 GitHub Python test workflow가 새 skill을 설명·실행한다.
- [x] Claude 경로와 Codex discovery junction에서 같은 skill 파일을 읽을 수 있다(현재 junction target은 개발 worktree).

# Blockers

없음.

# Deferred

- Baseline `skills/jira-worklog/test_session_time.py::NestedAndOutOfRootTest::test_malformed_cwd_does_not_abort`는 새 변경과 무관하게 실패한다(새 worktree가 `origin/main` 기준이고 jira-worklog 파일 미변경). 별도 jira-worklog 작업에서 원인 확인 필요.
- Node.js가 현재 PowerShell PATH에 없어 저장소의 Node syntax/unit/plan-lint 명령은 실행하지 못했다. Node 설치 또는 PATH 복구 후 재검증한다.
