---
title: codex-cli-agents-and-hooks
category: entity
created: 2026-09-28
updated: 2026-09-28
sources:
  - https://learn.chatgpt.com/docs/agent-configuration/subagents (developers.openai.com/codex/subagents 리다이렉트, 조회 2026-09-28 — living docs 라 설치 버전보다 최신일 수 있다)
  - https://learn.chatgpt.com/docs/hooks (developers.openai.com/codex/hooks 리다이렉트, 조회 2026-09-28)
  - https://learn.chatgpt.com/docs/environments/git-worktrees (Codex 앱 worktree, 조회 2026-09-28)
  - github.com/openai/codex issue #15250·#9912·#46704·#32027·#15524·#34289·#46455, PR #42652 (조회 2026-09-28)
  - 로컬 관찰 — codex-cli 0.154.0, `~/.codex/hooks.json` 형태와 `config.toml` `[hooks.state]` (2026-09-28)
  - plans/2026-09-28-codex-agents-hooks/codex-agents-hooks-plan.md (Decisions·Review Disposition), PR #186
---

# codex-cli-agents-and-hooks

Codex CLI(설치 0.154.0, 2026-09-28 조사)의 custom agent 정의와 hook 이 이 repo 의 Claude Code 자산과 어디서 맞고 어디서 다른지. 이 repo 가 Codex agent 정의를 **생성 사본**으로 두고 Codex `hooks.json` 에 dlc 훅을 **넣지 않은** 근거다(PR #186). 공식 문서는 living docs 라 설치 버전보다 앞선 내용일 수 있어, 버전 귀속이 불확실한 항목은 ⚠️ 로 표시한다.

## custom agent — `~/.codex/agents/*.toml`

- 공식 기능이다. 파일 하나가 agent 하나이고 필수 키는 `name`·`description`·`developer_instructions`. `config.toml` 의 키를 상속·override 할 수 있어 `model`·`model_reasoning_effort`·`sandbox_mode`·`mcp_servers` 등을 둘 수 있다(Subagents 문서).
- **tools 제한 키는 문서에서 찾지 못했다** ❌ — Claude Code agent 의 `tools:` 에 해당하는 것이 없어, 읽기 전용은 `sandbox_mode = "read-only"` 로만 옮길 수 있다. read-only 가 임시 디렉토리 쓰기도 막는다는 문서 서술이 있어(⚠️) 테스트를 돌려야 하는 리뷰어에는 맞지 않는다.
- **이름으로 직접 호출하지 못할 수 있다** — `spawn_agent` 가 이름 파라미터 없이 `agent_type`·prompt·model override 만 받는다는 보고(issue #15250, 2026-03-20). 0.154.0 에서 고쳐졌는지 ❌.
- **재귀 방지가 셸 경로를 덮지 않는다** — `agents.max_depth` 는 `spawn_agent` 경로만 제한하고(issue #9912), 인접 버전에서 그 강제조차 동작하지 않는다는 보고가 있다(0.144.1 #32027, 0.155.1 #46704 ⚠️). 셸로 `codex exec` 를 다시 부르는 것은 막지 않고, 중첩 실행에서 sandbox 가 새는 버그 보고도 있다(#15524). 그래서 agent 지시문에 "Codex 를 다시 불러 병행 검토하라"는 절이 있으면 Codex 안의 agent 가 자기 자신을 부른다 — 이 repo 는 [[claude-codex-collaboration]] 의 "Codex 병행" 절을 빼고 생성한다(`scripts/bootstrap/sync_codex_agents.py`).
- Codex 앱의 Claude 설정 import 는 링크를 **단어를 치환한 실파일 사본**으로 바꿔 놓는다(2026-08-01 — `~/.Codex/docs/…` 같은 경로). 생성 사본은 첫 줄 표식으로 구분해, import 가 되살린 사본을 생성기가 덮지 않고 충돌로 알린다.

## hooks — `~/.codex/hooks.json`

- 로컬에서 로드되는 형태는 `{"hooks": {<Event>: [{"matcher", "hooks": [{"type", "command", "timeout"}]}]}}` 다(0.154.0 — `config.toml` 의 `[hooks.state."…hooks.json:pre_tool_use:…"]` 에 `trusted_hash` 가 있다). hook 기능은 0.150.1 부터 기본 활성으로 보고된다 ⚠️.
- 이벤트: `PreToolUse`·`PostToolUse`·`PermissionRequest`·`UserPromptSubmit`·`Stop`·`SubagentStart`·`SubagentStop`·`SessionStart`·`SessionEnd`·`PreCompact`·`PostCompact`. 출력 필드(`hookSpecificOutput.permissionDecision`, `decision: "block"`, `continue`, `systemMessage`)는 Claude Code 와 철자·구조가 같다(Hooks 문서).
- **이 repo 의 훅이 읽는 입력과 다른 점:**
  - 파일 편집 도구가 `apply_patch` 라 `tool_input` 에 `file_path` 가 없고 경로가 `tool_input.command` 의 patch 본문 안에 있다(`*** Update File: <path>`) ⚠️(문서 요약·2차 자료) — `guard-worktree-edit.js` 의 `Edit|Write|NotebookEdit` + `file_path` 판정이 걸리지 않는다.
  - Claude Code 전용인 PostToolUse `tool_response.bashEditDiff` 와 Stop `background_tasks` 가 없다 — `dlc-evidence-ledger.js`·`dlc-early-stop.js` 가 기대는 입력이다.
  - PostToolUse 에 명령 출력·종료 코드가 실리지 않는다는 보고가 있다(#34289·#46455 ⚠️ — 문서는 local function tool 이 출력을 `tool_response` 로 보낸다고 서술).
  - 셸 도구가 hook 에 `tool_name: "Bash"` 로 노출된다는 서술이 있다 ⚠️(2차 자료, 소스 미확인).
- 결론(2026-09-28): dlc 훅을 옮기려면 `apply_patch` 파싱과 ledger 입력 적응이 필요한 별도 작업이다. 그 전까지 Codex 세션이 main checkout 을 worktree 없이 고쳐도 막는 게이트는 없다.

## worktree

Codex 앱에는 채팅별 worktree 기능이 있고(앱 전용 문서), CLI 는 experimental `--worktree` 가 있다(PR #42652, 2026-09-04 merge). 둘 다 동시 작업 충돌을 피하는 편의 기능으로 설명되고, 세션의 편집을 worktree 안으로 제한하는 경계로 문서화돼 있지 않다 — Claude Code 의 네이티브 격리([[worktree-isolation-bash-guard]])와 다르다.

> [!open] Codex 가 생성한 agent 정의를 실제로 로드하는지, `sandbox_mode = "read-only"` 가 researcher 의 웹 검색을 막는지는 확인하지 못했다(2026-09-28, Codex 크레딧 소진). 확인 방법은 Codex 세션에서 agent 목록과 로드 경고를 보는 것.

관련: Codex 쪽 `AGENTS.md` 연결은 [[claude-code-agents-md-loading]], 호출 규약은 [[codex-bash-invocation]].
