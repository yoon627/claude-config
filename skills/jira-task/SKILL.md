---
name: jira-task
description: Update the current Jira task's description with a concise summary of what was added or changed. Use from /e when finishing a Claude or Codex task, after previewing the description change and receiving explicit user approval before updating the task body.
---

# Jira Task Description

`jira-worklog`는 AI 작업시간을 기록하고, 이 skill은 기존 Jira task 본문(description)에 작업 내용만 반영한다. 별도 Jira comment는 생성하지 않는다.

## Workflow

1. 현재 worktree의 active plan과 작업 상태를 확인한다. WIP commit이 이미 있으면 그 commit의 diff와 plan의 `# Progress`를 기준으로 삼는다. 확인하지 못한 변경은 요약에 넣지 않는다.
2. 작업 내용을 줄 하나에 항목 하나로 스크래치 파일에 적는다(`Write`). 날짜와 `- ` 접두는 스크립트가 붙이므로 내용만 적는다(이미 붙인 `-`·`*`·`•`·`1.`·`1)` 목록 표시와 `작업 내용:` 접두는 벗겨진다). 요약을 명령 인자로 넣지 않는다 — backtick·`$` 같은 셸 메타문자가 POSIX 셸·PowerShell 에서 해석돼 요약이 바뀌거나 명령이 실행된다. 작성 규칙:
   - task 목표에 해당하는 기능·동작 변경만 적는다. 리베이스·머지·CI·리뷰 반영·테스트 정비·리팩토링은 task 가 그 자체를 요구한 경우가 아니면 적지 않는다.
   - 커밋 메시지처럼 구현 경위를 옮기지 말고, 무엇이 어떻게 달라졌는지 결과로 항목당 한 줄, 1~4개.
   - 변경 파일 목록, 검증 명령, 작업시간, 내부 진행 과정은 넣지 않는다.
   - 적을 항목이 없으면 description 을 갱신하지 않고 이 skill 을 끝낸다(preview 도 생략).
3. 티켓을 worktree 디렉터리 이름 prefix 또는 branch에서 찾지 못하면 `--ticket`을 명시한다.
4. 항상 preview를 먼저 실행한다. Jira 를 읽기만 하고 쓰지 않는다. 그 날짜의 기존 항목(교체될 내용), 기존 항목 지문, 교체 후 내용을 출력한다.

   ```text
   uv run --no-project python "<skill-dir>/jira_task.py" --summary-file "<요약 파일>"
   ```

   `<skill-dir>`는 이 `SKILL.md`가 있는 `skills/jira-task` 디렉터리로 해석한다.
5. 그 날짜 기존 항목이 있으면 그것과 이번 작업을 합쳐 2단계 규칙(1~4개)대로 요약 파일을 다시 쓰고 preview 를 다시 실행한다. 그날 항목은 이 요약 하나로 **교체**되므로, 기존 항목 중 남길 것을 빠뜨리지 않는다. 지문이 `unknown`(자격증명 없음·조회 실패)이면 기존 항목을 확인할 수 없으므로 게시하지 않는다.
6. preview 의 티켓·기존 항목·교체 후 내용을 사용자에게 보여주고 명시적 승인을 받는다. 승인 전에는 `--post`를 실행하지 않는다. `/e`가 호출된 경우 이 승인은 worktree 정리 선택지와 별개의 외부 Jira 쓰기 승인이다.
7. 승인받은 경우 마지막 preview와 같은 인자에 preview 가 출력한 날짜(`--date`)와 지문, `--post` 를 더해 실행한다. 날짜를 고정하지 않으면 자정을 넘긴 승인이 다른 날짜로 게시된다. 그 사이 다른 세션이 그날 항목을 바꿔 지문이 다르면 쓰지 않고 중단한다 — 반영하려면 4단계부터 다시 하고, 아니면 게시하지 않았다고 보고한다.

   ```text
   uv run --no-project python "<skill-dir>/jira_task.py" --summary-file "<요약 파일>" --date <preview 날짜> --post --expect-existing <지문>
   ```

## Description behavior

- Jira Cloud REST API v3로 현재 `description`을 조회한 뒤 기존 ADF 본문을 보존한다.
- `작업 내용` heading(같은 레벨 이하의 다음 heading 전까지)이 섹션이다. 섹션이 없으면 문서 끝에 만들고, 새 날짜 항목은 섹션 끝에 넣는다. 섹션 밖 본문은 건드리지 않는다.
- 항목은 한 문단으로 `날짜`(굵게) → `- 항목` 줄들이다. 식별용 marker 줄은 없다.
- 섹션 안에서 첫 줄이 그 날짜(`YYYY-MM-DD`)인 블록부터 다음 날짜 블록·이전 형식 marker 블록·하위 heading 전까지가 그날 항목이다. 이전 형식의 `[jira-task] … date=<그 날짜> …` marker 블록도 그날 항목으로 보고, 교체할 때 함께 걷어낸다.
- 그날 항목이 있으면 새 요약 하나로 교체하고, 없으면 추가한다. 요약이 같으면 쓰지 않는다. 사람이 그날 항목을 직접 편집했어도 다음 게시 때 새 요약으로 교체된다 — preview 의 기존 항목을 보고 요약에 반영한다.
- description PUT 후 다시 조회해 그날 항목이 하나이고 요약과 같은지 확인한다. 저장값이 다르면 성공으로 보고하지 않는다.
- `--post` 안의 조회와 저장 사이에 다른 편집이 끼면 막지 못한다.
- API 오류에는 credential을 출력하지 않는다. `--post` 실패를 숨기거나 무의미하게 재시도하지 않는다.

## Configuration

preview 의 기존 항목 조회와 `--post` 에 다음 설정이 필요하다(없으면 preview 는 지문 `unknown` 으로 끝난다). 우선순위는 process environment → project `.env` → `~/.jira-kit/.env` → `jira-kit.toml`(cwd 위의 프로젝트 파일, 없으면 `~/.jira-kit/jira-kit.toml`)이며 기존 `jira-worklog`와 같은 경로를 사용한다. `jira-kit.toml` 에서는 `[jira]` 의 `base_url`·`email`·`cloud_id` 와 `[worklog]` 의 `timezone`·`ticket_pattern` 만 읽는다.

```text
JIRA_BASE_URL=https://your-site.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=<Atlassian API token>
```

선택 설정: `JIRA_CLOUD_ID`, `JIRA_TIMEZONE`, `JIRA_TICKET_PATTERN`. API token은 TOML이나 skill 파일에 저장하지 않는다.

`--ticket`, `--worktree`(티켓 추출용), `--date`로 자동 추론값을 덮어쓸 수 있다.

## Relationship to jira-worklog

`jira-worklog`는 AI 작업시간을 Jira worklog로 upsert하고, `jira-task`는 기존 Jira task description에 작업 내용 요약을 upsert한다. `/e`는 두 작업을 별도로 처리하며, description 갱신에는 매번 사용자 승인을 요구한다.
