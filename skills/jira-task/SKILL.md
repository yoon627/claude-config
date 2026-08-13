---
name: jira-task
description: Record a concise summary of what was added or changed on the current Jira issue as an idempotent comment. Use from /e when finishing a Claude or Codex task, after previewing the summary and receiving explicit user approval before posting.
---

# Jira Task Notes

`jira-worklog`는 AI 작업시간을 기록하고, 이 skill은 Jira issue comment에 작업 내용만 남긴다. Jira issue description은 수정하지 않는다.

## Workflow

1. 현재 worktree의 active plan과 작업 상태를 확인한다. WIP commit이 이미 있으면 그 commit의 diff와 plan의 `# Progress`를 기준으로 삼는다. 확인하지 못한 변경은 요약에 넣지 않는다.
2. 실제로 추가·수정한 내용을 `작업 내용:` 한 줄, 최대 1~3문장으로 요약한다. 변경 파일 목록, 검증 명령, 작업시간, 내부 진행 과정은 이 comment에 넣지 않는다.
3. 티켓을 worktree 디렉터리 이름 prefix 또는 branch에서 찾지 못하면 `--ticket`을 명시한다.
4. 항상 preview를 먼저 실행한다. 기본 동작은 dry-run이며 Jira 외부 변경이 없다.

   ```powershell
   uv run --no-project python "<skill-dir>\jira_task.py" `
     --summary "작업 내용: <추가·수정한 내용 1~3문장>"
   ```

   `--summary-file` 또는 `--summary-file -`로 같은 요약을 여러 줄 전달할 수도 있지만, `/e`에서는 단일 `--summary`를 사용한다. `<skill-dir>`는 이 `SKILL.md`가 있는 `skills/jira-task` 디렉터리로 해석한다.
5. preview의 티켓·marker·comment 본문을 사용자에게 보여주고 명시적 승인을 받는다. 승인 전에는 `--post`를 실행하지 않는다. `/e`가 호출된 경우 이 승인 질문은 worktree 정리 선택지와 별개의 외부 Jira 쓰기 승인이다.
6. 승인받은 경우 preview와 같은 인자에 `--post`만 추가해 게시한다.

   ```powershell
   uv run --no-project python "<skill-dir>\jira_task.py" `
     --summary "작업 내용: <추가·수정한 내용 1~3문장>" `
     --post
   ```

## Posting behavior

- `--post`는 Jira Cloud REST API v3의 issue comment `POST`/`PUT`만 사용한다.
- comment에는 `[jira-task] ticket=... date=... worktree=... session=...` marker를 붙인다.
- 같은 marker의 본인 comment가 하나면 새 요약으로 갱신하고, 없으면 새 comment를 만든다. marker가 여러 개이거나 다른 사용자의 comment에 있으면 중복·오귀속 방지를 위해 중단한다.
- marker comment를 다음 실행에서 갱신할 수 있으므로, 사람이 그 comment를 직접 편집한 경우 다음 게시 때 해당 내용이 새 요약으로 대체될 수 있음을 알린다.
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

`jira-worklog`는 AI 작업시간을 Jira worklog로 upsert하고, `jira-task`는 작업 내용 요약을 issue comment로 upsert한다. `/e`는 둘을 별도로 처리하며, 시간 등록과 달리 작업 내용 comment 게시에는 매번 사용자 승인을 요구한다.
