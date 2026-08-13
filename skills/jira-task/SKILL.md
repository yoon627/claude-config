---
name: jira-task
description: Record a concise Claude or Codex work summary on the current Jira issue as an idempotent comment. Use when finishing a task, handing work between agents, updating Jira with changed files and validation results, or when the user asks to record task details in Jira. Preview by default and post only after explicit user confirmation.
---

# Jira Task Notes

Jira 작업시간은 `jira-worklog`가 담당하고, 이 skill은 작업내용·변경 파일·검증 결과를 Jira issue comment로 남긴다. Jira issue description은 덮어쓰지 않는다.

## Workflow

1. 현재 worktree의 active plan, `git diff --stat`, 변경 파일, 실행한 검증 결과를 읽는다. 확인하지 못한 내용은 요약에 쓰지 않는다.
2. 비밀값(`JIRA_API_TOKEN`, access token, private key, `.env` 원문, PII)을 요약에 넣지 않는다. 코드 전체나 긴 로그 대신 사용자에게 유용한 결과만 3~8개 항목으로 정리한다.
3. 다음 형식으로 요약을 만든다.

   ```text
   작업: <무엇을 변경했는지>
   변경 파일: <핵심 파일 목록>
   검증: <실행한 명령과 결과>
   남은 리스크: <없음 또는 확인하지 못한 항목>
   ```

4. 먼저 preview를 실행한다. 티켓을 worktree 디렉터리 이름 prefix 또는 branch에서 찾지 못하면 `--ticket`을 명시한다.

   ```powershell
   uv run --no-project python "<skill-dir>\jira_task.py" `
     --summary "작업: ..." `
     --summary "변경 파일: ..." `
     --summary "검증: ..."
   ```

   `--summary`는 여러 번 지정할 수 있고, `--summary-file` 또는 `--summary-file -`로 여러 줄을 전달할 수도 있다. `<skill-dir>`는 이 `SKILL.md`가 있는 `skills/jira-task` 디렉터리로 해석한다.

5. preview에서 티켓·marker·comment 본문을 확인한 뒤, 외부 Jira 변경에 대해 사용자 확인을 받는다. 확인 전에는 `--post`를 실행하지 않는다.
6. 확인 후 같은 인자로 `--post`를 붙여 게시한다.

   ```powershell
   uv run --no-project python "<skill-dir>\jira_task.py" `
     --summary "작업: ..." `
     --summary "변경 파일: ..." `
     --summary "검증: ..." `
     --post
   ```

## Posting behavior

- 기본 동작은 dry-run이다. credential이 없어도 preview할 수 있다.
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

`jira-worklog`는 AI 작업시간을 Jira worklog로 upsert하고, `jira-task`는 작업내용을 issue comment로 upsert한다. 작업 마무리 시 시간 기록과 내용 기록을 각각 preview한 뒤 사용자의 확인을 받아 실행한다.
