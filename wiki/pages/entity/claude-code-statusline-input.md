---
title: claude-code-statusline-input
category: entity
created: 2026-09-26
updated: 2026-09-26
sources:
  - https://code.claude.com/docs/en/statusline#subagent-status-lines (2026-09-25 확인)
  - Claude Code 공식 문서 env-vars — `CLAUDE_CODE_TMPDIR` (2026-09-25 확인)
  - plans/2026-09-25-repo-audit-g3-g4-live-bugs (재현·리뷰어 바이너리 확인)
  - PR #175, subagent-statusline.js, statusline.js
---

# claude-code-statusline-input

Claude Code 가 statusline 스크립트에 넘기는 입력과 그 주변 디렉토리의 실제 모습(2026-09-25, macOS 실측 + 공식 문서). 이 repo 의 `statusline.js`·`subagent-statusline.js` 가 옛 스키마를 읽어 매번 빈 출력을 내던 문제(G3)를 고치며 확인했다.

## subagentStatusLine
- **입력**: `{기본 hook 필드, columns, tasks[]}`. task 마다 `id, name, type, status, description, label, startTime, model, effort, contextWindowSize, tokenCount, tokenSamples, cwd`. 최상위 `status`·`context_window`·`cost` 는 없다 — 옛 스크립트가 이것을 읽었다.
- **출력**: 행마다 `{"id","content"}` JSON 한 줄. 평문을 쓰면 아무것도 표시되지 않는다.
- id 가 문자열이 아닌 줄은 host 가 버린다(plan-reviewer 바이너리 확인). `content` 가 비면 그 행을 숨긴다.
- `name` 은 **이름을 등록한 agent 에만** 온다. 기본 표시가 대신 쓰는 agent 종류는 입력에 없다(code-reviewer 바이너리 확인) — 이름 없는 행은 `description` 으로 구분한다.
- `startTime` 은 epoch ms. `label` 은 문서에 의미가 정의돼 있지 않다.
- `columns` 가 행 폭이다. 한글·CJK·이모지는 2칸으로 세어 잘라야 넘치지 않는다.

## 임시 디렉토리와 tasks
- 기준 디렉토리는 `CLAUDE_CODE_TMPDIR`, 기본값은 macOS `/tmp`, Linux·Windows `os.tmpdir()`. 그 아래 Unix 는 `/claude-{uid}/`, Windows 는 `/claude/` 가 붙는다(env-vars 문서). 실제 경로 예: `/private/tmp/claude-501/<slug>/<session id>/tasks`.
- slug 는 경로의 `/` 와 **`.` 도** `-` 로 바꾼다(`/Users/x/.claude` → `-Users-x--claude`). `$TMPDIR/claude/…` 로 추정한 옛 코드는 기준 디렉토리와 slug 가 둘 다 틀렸다.
- `tasks/` 에는 백그라운드 작업만 있는 것이 아니다. **foreground Bash 출력 파일**(9자 이름 `.output`)과 subagent symlink(`a`+16hex → subagent jsonl)가 섞여 있어, 파일 수로 "백그라운드 작업 N개" 를 세면 `refreshInterval` 마다 오표시가 난다. 이 repo 는 bg 표시를 제거했다(사용자 결정).
- `EnterWorktree` 뒤에는 `transcript_path` 와 `workspace.project_dir` 가 **worktree slug 로 옮겨지지만** tasks 디렉토리는 **시작 디렉토리 slug 에 남는다**(plan-reviewer 실측 — 처음 plan 에 적은 "transcript 상위와 같다" 는 틀렸다). `cwd` 로 slug 를 만들면 worktree 세션에서 틀린다.

## 운영 메모
- `refreshInterval: 2`(이 사용자 설정)면 스크립트가 2초마다 새로 뜬다. 입력이 `null`·깨진 JSON 이어도 exit 0 으로 그 조각만 빼야 하고, 외부 프로세스 spawn 은 비용이 곱해진다.
- 파일의 ctime 은 append 할 때 같이 움직인다 — "생성 후 경과" 를 ctime 으로 재면 "마지막 쓰기부터" 가 된다.

## 연계
subagent 설정 필드는 [[claude-code-subagent-config]], worktree 세션 구조는 [[worktree-per-task]], 스키마를 문서 정본에서 옮겨 적어야 하는 이유는 [[lesson-parser-precedent-partial-mirror]].
