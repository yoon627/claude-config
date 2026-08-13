---
name: jira-task
description: Update the current Jira task's description with a concise summary of what was added or changed. Use from /e when finishing a Claude or Codex task, after previewing the description change and receiving explicit user approval before updating the task body.
---

# Jira Task Description

`jira-worklog`는 AI 작업시간을 기록하고, 이 skill은 기존 Jira task 본문(description)에 작업 내용만 반영한다. 별도 Jira comment는 생성하지 않는다.

## Workflow

1. 현재 worktree의 active plan과 작업 상태를 확인한다. WIP commit이 이미 있으면 그 commit의 diff와 plan의 `# Progress`를 기준으로 삼는다. 확인하지 못한 변경은 요약에 넣지 않는다.
2. 실제로 추가·수정한 내용을 `작업 내용:` 한 줄, 최대 1~3문장으로 요약한다. 변경 파일 목록, 검증 명령, 작업시간, 내부 진행 과정은 task 본문에 넣지 않는다.
3. 티켓을 worktree 디렉터리 이름 prefix 또는 branch에서 찾지 못하면 `--ticket`을 명시한다.
4. 항상 preview를 먼저 실행한다. 기본 동작은 dry-run이며 Jira 외부 변경이 없다.

   ```powershell
   uv run --no-project python "<skill-dir>\jira_task.py" `
     --summary "작업 내용: <추가·수정한 내용 1~3문장>"
   ```

   `<skill-dir>`는 이 `SKILL.md`가 있는 `skills/jira-task` 디렉터리로 해석한다.
5. preview의 티켓·marker·description 추가 내용을 사용자에게 보여주고 명시적 승인을 받는다. 승인 전에는 `--post`를 실행하지 않는다. `/e`가 호출된 경우 이 승인은 worktree 정리 선택지와 별개의 외부 Jira 쓰기 승인이다.
6. 승인받은 경우 preview와 같은 인자에 `--post`만 추가해 기존 task description을 갱신한다.

   ```powershell
   uv run --no-project python "<skill-dir>\jira_task.py" `
     --summary "작업 내용: <추가·수정한 내용 1~3문장>" `
     --post
   ```

## Description behavior

- Jira Cloud REST API v3로 현재 `description`을 조회한 뒤 기존 ADF 본문을 보존한다.
- 본문에 `작업 내용` 섹션이 없으면 만들고, 작업 요약 항목을 추가한다.
- 항목은 `[jira-task] ticket=... date=... worktree=... session=...` marker로 식별한다.
- 같은 marker가 있으면 새 요약으로 그 항목만 갱신하고, 없으면 새 항목을 추가한다. 따라서 같은 `/e`를 반복해도 중복되지 않는다.
- description PUT 후 다시 조회해 marker와 요약이 실제 저장됐는지 확인한다. 저장값이 다르면 성공으로 보고하지 않는다.
- 기존 task description 전체를 덮어쓰지 않지만, 사람이 같은 marker 항목을 직접 편집한 경우 다음 게시 때 해당 항목이 새 요약으로 대체될 수 있다.
- API 오류에는 credential을 출력하지 않는다. `--post` 실패를 숨기거나 무의미하게 재시도하지 않는다.

## Configuration

`--post`에만 다음 설정이 필요하다. 우선순위는 process environment → project `.env` → `~/.jira-kit/.env`이며 기존 `jira-worklog`와 같은 경로를 사용한다.

```text
JIRA_BASE_URL=https://your-site.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=<Atlassian API token>
```

선택 설정: `JIRA_CLOUD_ID`, `JIRA_TIMEZONE`, `JIRA_TICKET_PATTERN`. API token은 TOML이나 skill 파일에 저장하지 않는다.

`--ticket`, `--worktree`, `--date`, `--session-id`로 자동 추론값을 덮어쓸 수 있다. 다른 세션이나 다른 worktree의 작업을 섞지 않으려면 `--session-id`를 명시한다.

## Relationship to jira-worklog

`jira-worklog`는 AI 작업시간을 Jira worklog로 upsert하고, `jira-task`는 기존 Jira task description에 작업 내용 요약을 upsert한다. `/e`는 두 작업을 별도로 처리하며, description 갱신에는 매번 사용자 승인을 요구한다.
