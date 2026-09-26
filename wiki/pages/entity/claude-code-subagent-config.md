---
title: claude-code-subagent-config
category: entity
created: 2026-06-19
updated: 2026-09-26
sources:
  - Anthropic docs (sub-agents.md, settings.md, env-vars.md, effort.md)
  - https://code.claude.com/docs/en/statusline#subagent-status-lines (2026-09-25 확인 — 패널 표시 절)
  - claude-code-guide (2026-06 확인)
---

# claude-code-subagent-config

Claude Code의 subagent 설정·effort 환경변수에 관한 확정 사실(2026-06 기준). [[subagent-model-effort-tiering]] 구현의 근거.

## subagent frontmatter
`agents/<name>.md`의 YAML frontmatter에서 `model`·`effort`·`temperature`를 지원(sub-agents.md). 
- 미지정 시 **세션 effort/model 상속**.
- `model` 별칭: `opus`/`sonnet`/`haiku`/`fable`·`inherit`·전체 모델 ID 유효.
- `effort` 값: `low`/`medium`/`high`/`xhigh`/`max`.

## env 우선순위
- **shell/OS 환경변수 > settings.json `env` 블록**(settings.md "shell variable takes precedence over the env block"). → [[effort-os-env-single-source]].
- 공식 effort 변수명은 `CLAUDE_CODE_EFFORT_LEVEL`. `CLAUDE_EFFORT`는 파생/내부 별칭.

## Haiku effort
Haiku 4.5는 effort 파라미터 미지원([[anthropic-claude-models]]). 단 researcher=haiku에 세션 effort(max) 상속 상태 smoke 결과 **에러 없이 정상 응답** → Claude Code가 haiku에 effort를 무시/제거. effort 명시·sonnet 폴백 불필요.

## 패널 표시
subagent 패널 행을 커스텀하는 `subagentStatusLine` 의 입력·출력 스키마(`tasks[]`·`{"id","content"}`, `name` 은 이름을 등록한 agent 에만)는 [[claude-code-statusline-input]].
