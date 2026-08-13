---
title: jira-task-description — Jira task 본문에 작업 내용 반영
status: done
started: 2026-08-13
updated: 2026-08-13
---

# Goal

`jira-task`가 별도 comment를 생성하지 않고 Jira issue description에 작업 내용 요약을 반영하도록 수정한다.
기존 description은 보존하고, 같은 marker를 재실행하면 해당 작업 항목만 갱신한다.

# Progress

- 2026-08-13: 기존 구현이 Jira comment POST/PUT를 사용하고 issue description은 건드리지 않는 것을 확인했다. 사용자 요구에 맞춰 description 갱신으로 방향을 변경한다.
- 2026-08-13: Jira Cloud REST v3의 issue `PUT`과 description ADF 지원을 공식 문서에서 확인했다.
- 2026-08-13: 기존 description 보존·marker 항목 upsert·PUT 후 GET 검증을 구현하고 `/e`/README/skill 설명을 task 본문 반영 기준으로 변경했다.
- 2026-08-13: Python 19개 테스트, `ruff check`, `ruff format --check`, `py_compile`, `quick_validate.py`, preview CLI, `git diff --check`를 통과했다. preview 접두어 중복도 회귀 테스트로 고정했다.

# Next

검증된 변경을 main에 fast-forward 반영하고 discovery junction을 main의 `skills/jira-task`로 유지한다. Jira 실제 PUT은 `/e` 승인 시에만 실행한다.

# Decisions

- 기존 description 전체를 덮어쓰지 않고 기존 ADF content를 보존한 뒤 `작업 내용` 항목을 append/update한다.
- 작업 항목은 ticket·date·worktree·session marker로 식별하며 같은 marker 재실행 시 중복 추가하지 않는다.
- preview는 Jira 외부 변경 없이 추가될 작업 내용만 보여주고, `/e`에서 사용자 승인 후에만 description PUT을 실행한다.
- comment API와 comment author 조회는 제거하고 issue description API만 사용한다.

# Key Files

- `skills/jira-task/jira_task.py` — Jira description 조회·갱신과 ADF 항목 upsert.
- `skills/jira-task/test_jira_task.py` — description API·ADF·멱등성 테스트.
- `skills/jira-task/SKILL.md` — description 갱신 사용 절차.
- `skills/e/SKILL.md` — `/e` preview·사용자 승인·description 게시 흐름.
- `README.md` — skill 설명과 API 동작 문서.

# Acceptance

- [x] 기존 description content가 보존되고 작업 내용 항목이 추가된다(`test_add_preserves_existing_description`).
- [x] 같은 marker 재실행은 중복 추가 대신 해당 항목을 갱신한다(`test_same_marker_is_idempotent`, `test_same_marker_updates_only_its_entry`).
- [x] preview에는 외부 변경이 없고 `/e` 사용자 승인 전에는 PUT하지 않는다(`test_preview_does_not_require_credentials_or_write`, `/e` 지침).
- [x] description PUT 후 저장값을 조회해 marker와 요약이 실제 반영됐는지 확인한다(`test_adds_and_verifies_description`, `test_saved_description_mismatch_is_not_reported_as_success`).
- [x] Python 19개 테스트·`ruff check`·`ruff format --check`·`py_compile`·`quick_validate.py`·`git diff --check`를 통과한다.

# Blockers

없음.
