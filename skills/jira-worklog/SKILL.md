---
name: jira-worklog
description: worktree 의 Claude·Codex 세션 로그에서 AI 작업시간(사용자 응답 대기 제외)을 추정해 Jira worklog 로 등록한다. "worklog 등록", "작업시간 기록", "이 작업 몇 시간 걸렸는지 Jira에 남겨줘", worktree 를 옮기거나 작업을 마칠 때 시간 기록에 사용. Claude·Codex 세션 지원.
---

# jira-worklog — worktree 작업시간 → Jira worklog

그 worktree 의 Claude·Codex 세션 로그(Claude `~/.claude/projects/<slug>` + Codex `~/.codex/sessions`)
에서 AI 가 실제 작업한 시간(사용자 응답 대기·긴 공백 제외)을 날짜별로 추정해 Jira worklog 에 등록한다.
두 소스가 다 있으면 시간을 union 한다. 기본은 미리보기(dry-run) — 시간이 합리적인지 확인한 뒤 등록한다.

설치 불필요 — 이 스킬 디렉토리의 `jira_worklog.py`(stdlib only)를 직접 실행한다. **반드시 대상 worktree
안에서(cwd = 그 worktree) 실행**해야 그 worktree 세션 시간이 잡힌다(main 에서 돌리고 worktree 파일만
고치면 안 잡힘).

## 실행

이 스킬 디렉토리의 `jira_worklog.py` 를 현재 worktree(cwd)에서 실행한다. 경로는 이 SKILL.md 가 있는
디렉토리 기준(아래는 이 환경의 절대경로 — 공유 시 각자 홈 경로로 조정):

```bash
# 미리보기 (토큰 없이 시간·대상 티켓 확인 — 안전)
python "C:/Users/yoon627/.claude/skills/jira-worklog/jira_worklog.py"

# 실제 Jira 등록 (그 worktree 의 그날 항목 upsert — 같은 날 재실행 시 시간 갱신)
python "C:/Users/yoon627/.claude/skills/jira-worklog/jira_worklog.py" --register
```

## 설정 (최초 1회)

등록(`--register`) 시에만 토큰이 필요하다(미리보기는 불필요). `~/.jira-kit/.env` 에 한 번만:

```
JIRA_BASE_URL=https://your-site.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=<Atlassian API token>
```

- 발급: https://id.atlassian.com/manage-profile/security/api-tokens (앱 = **Jira**). 토큰은 프롬프트에 넣지 말 것.
- scoped 토큰이면 cloudId 자동 조회(`api.atlassian.com/ex/jira/{cloudId}`). 조회 skip 하려면 `JIRA_CLOUD_ID` 설정.
- 정확한 IANA 타임존이 필요하면 `pip install tzdata`(없으면 시스템 로컬 tz fallback).
- 비민감 설정(ticket_pattern/timezone/max_gap)은 선택 — `~/.jira-kit/jira-kit.toml`.

## 동작·옵션

- 대상 티켓은 **worktree 디렉토리 이름(prefix)** 에서 우선 추출(anchored), 없으면 브랜치명으로 fallback 한다(기본 `[A-Z][A-Z0-9]+-\d+`). detached HEAD 처럼 브랜치가 없어도 worktree 이름의 티켓으로 잡힌다. 어느 쪽에도 매치가 없으면 등록을 skip 한다(안전).
- `--all` 모든 worktree 미리보기 · `--max-gap` idle gap(분) · `--ticket-pattern` 패턴 · `--timezone` IANA 타임존 · `--comment` worklog 코멘트.
- 실제 등록(`--register`)은 외부 반영이니 **먼저 미리보기로 확인**할 것.
- **upsert(멱등)**: (티켓, 날짜, worktree) 마커로 **그 worktree 의** 본인 worklog 를 찾아 없으면 생성, 있으면 시간만 갱신한다(재실행해도 중복 없음). 갱신 시 기존 comment 는 보존. 타인의 worklog(같은 마커·다른 author)는 건드리지 않는다.
- **같은 티켓 · 여러 worktree**: `CSTP1-1234-abc` 와 `CSTP1-1234-def` 처럼 한 티켓을 여러 worktree 에서 작업하면 **worktree 마다 worklog 항목이 따로** 생긴다. 티켓의 총 작업시간은 Jira 가 항목들을 합산하므로 각 worktree 시간이 서로 덮이지 않고 누적된다. 두 worktree 를 **같은 시각에 병렬로** 돌렸다면 겹치는 시간이 양쪽에 각각 잡혀 합계가 실제 경과시간보다 커진다.
- worktree 를 지워도 그 항목은 Jira 에 남는다(코드가 정정·삭제하지 않음 — 필요하면 수동 정리). 반대로 worktree 도입 전 형식(worktree 없는 마커)의 **본인** 항목이 남아 있으면 귀속을 알 수 없어 그 (티켓, 날짜) 등록을 중단하고 수동 정리를 요구한다.
- Jira UI 에서 worklog 코멘트를 수동 편집해 마커 줄을 지우면 다음 실행이 같은 날 항목을 새로 만든다.

## /e 등 다른 스킬에서 호출

작업을 마칠 때(예: `/e`) 이 스킬을 호출해 그 worktree 의 AI 작업시간을 기록할 수 있다. 먼저 dry-run 으로
시간을 보여주고, 사용자 승인 후 `--register` 로 등록한다(외부 반영이라 승인 게이트 유지).
