---
title: claude-code-agents-md-loading
category: entity
created: 2026-09-25
updated: 2026-09-27
sources:
  - https://code.claude.com/docs/en/memory (AGENTS.md 절, 2026-09-25 조회 · claudeMdExcludes 절, 2026-09-27 조회)
  - headless 실측 2026-09-25 (Claude Code 2.1.282)
  - headless 실측 2026-09-27 (Claude Code 2.1.283 — worktree CLAUDE.md 이중 주입, plan claude-md-dedupe)
  - 커밋 a3d7bdc (2026-06-10 사용자 결정 — ~/.codex/AGENTS.md 는 CLAUDE.md 심링크)
---

# claude-code-agents-md-loading

**Claude Code v2.1.277+ 는 `AGENTS.md` 를 직접 읽는다. 기본값은 "작업 디렉토리나 그 위에 CLAUDE.md 가 없을 때만"이고, `~/.claude/CLAUDE.md` 는 그 판정에서 세지 않는다.** 그래서 `~/.claude` 처럼 user 지침 디렉토리 자체가 작업 디렉토리이면 같은 곳의 `AGENTS.md` 가 user CLAUDE.md 와 함께 주입된다.

## 규칙 (✅ memory 문서)

- 기본(Project instructions = `claude-md-or-agents-md`): cwd 또는 상위에 `CLAUDE.md`·`.claude/CLAUDE.md`·`CLAUDE.local.md` 가 있으면 CLAUDE.md 만, 없으면 `AGENTS.md`.
- 판정에서 **세지 않는** 것: `~/.claude/CLAUDE.md`, managed CLAUDE.md, `.claude/rules/` — 이들은 AGENTS.md 와 함께 계속 로드된다.
- 로드 범위: 세션 시작 시 cwd 와 상위의 모든 `AGENTS.md`·`.claude/AGENTS.md`. 하위 디렉토리 것은 Read 할 때.
- `claudeMdExcludes`(절대경로 glob, 모든 settings 레이어, 배열은 병합)가 AGENTS.md 에도 적용된다.
- `/config` → Project instructions 값: `claude-md-or-agents-md`(기본) · `claude-md-and-agents-md` · `claude-md` · `managed-only`. user 설정이라 모든 repo 에 걸린다.
- 필요 버전 v2.1.277+. v2.1.281 전에는 Bedrock·telemetry 비활성 세션 등에서 못 읽는 경우가 있었다. 업그레이드 직후 첫 세션은 읽지 않을 수 있다.

## 이 repo 에 미친 영향 (✅ 실측)

- `~/.claude/AGENTS.md` 는 gitignored 로컬 파일이었고, 2026-08-01 Codex 앱의 Claude 설정 import 가 만든 CLAUDE.md 단어 치환본(`Claude`→`Codex`)에 손 패치를 얹은 사본이었다(2026-09-25 제거). main checkout 세션에 CLAUDE.md 와 함께 들어가 서로 다른 규칙(결론 블록 위치, 자동 커밋·intent 규칙 부재, "Codex ↔ Codex 협업" 등)이 동시에 주입됐다.
- worktree 세션은 자기 cwd 에 `CLAUDE.md` 가 있어 영향이 없다(규칙상).
- 대응(2026-09-25): user `settings.json` 에 `claudeMdExcludes: ["/Users/jongyoonlee/.claude/AGENTS.md"]`. headless 세션에 "AGENTS.md 에만 있는 제목이 컨텍스트에 있나"를 물어 적용 전 YES → 적용 후 NO, CLAUDE.md 에만 있는 제목은 전후 모두 YES 로 확인했다.
- 기각: Project instructions = `claude-md` — 다른 repo 의 AGENTS.md 까지 끊는다.
- 후속(2026-09-25): Codex 쪽 정리에서 `~/.codex/AGENTS.md` 를 `~/.claude/CLAUDE.md` 심링크로 되돌리고(2026-06-10 단일 소스 결정) 이 repo 의 `AGENTS.md` 미러는 치웠다(백업 `backups/codex-resync-20260925/`). `claudeMdExcludes` 줄은 Codex 앱 import 가 미러를 다시 만들 때를 대비해 남겨 둔다.

## worktree 세션의 CLAUDE.md 이중 주입 (✅ 실측 2026-09-27)

- 이 repo 의 worktree(`~/.claude/.claude/worktrees/<n>`) 세션은 `~/.claude/CLAUDE.md` 를 **user 지침**으로, worktree 의 `CLAUDE.md` 를 **프로젝트 지침**으로 둘 다 싣는다 — 경로가 달라 중복으로 보지 않는다. worktree 사본 끝에 임시 표식을 붙이고 headless `claude -p --model haiku` 로 물어 확인했다: 기본 = 표식 있음·입력 62,827 토큰, `--settings` 로 `claudeMdExcludes: ["**/.claude/.claude/worktrees/*/CLAUDE.md"]` 주입 = 표식 없음·44,300 토큰(전역 사본 내용은 그대로), main 세션 + 같은 패턴 = 전역 사본 내용 있음·44,097 토큰. 컨텍스트 약 18.5k 토큰(haiku 기준)이 중복이었다.
- **worktree `CLAUDE.md` 를 빼면 그 worktree 의 `AGENTS.md` 폴백이 켜진다**: 표식을 넣은 임시 `AGENTS.md` 로 재니 기본 = 없음, `CLAUDE.md` 만 제외 = **있음**, `AGENTS.md` 도 제외 = 없음. 제외된 CLAUDE.md 는 폴백 판정("CLAUDE.md 가 있으면 AGENTS.md 를 안 읽는다")에서 세지 않는다.
- 대응: user `settings.json` `claudeMdExcludes` 에 `**/.claude/.claude/worktrees/*/CLAUDE.md` 와 `**/.claude/.claude/worktrees/*/AGENTS.md`. worktree 사본을 빼는 이유는 전역 사본이 main 세션에서 프로젝트 파일과 같은 경로라서다. `.claude` 가 두 번 이어지는 경로만 맞아 다른 repo 의 worktree 는 걸리지 않는다. 결과: worktree 세션과 그 subagent 는 main checkout 의 `CLAUDE.md` 로 돌고, branch 에서 고친 규칙은 main 작업트리에 반영된 뒤 새 세션부터 적용된다. macOS 에서만 실측했다(Windows 경로 매칭 미검증).
- 기각: main `settings.local.json` 에 두기 — project 범위라 `/wt` 가 복사한 새 worktree 에만 따라가고 기존 worktree 는 수동 복사가 필요하다. 기각: worktree 에서만 전역 사본을 빼 branch 편집을 바로 반영하기 — worktree 전용 settings 파일이 필요한데 `/wt` 가 복사하는 main `settings.local.json` 은 main 세션에도 적용돼 main 이 전역 사본을 잃는다.

## 연계

Codex 와의 역할 분담은 [[claude-codex-collaboration]], 항상 주입되는 문서의 크기 관리는 [[ops-doc-slimming]].

Codex 용 AGENTS.md 는 **심링크**로 결정됐다(2026-06-10 `a3d7bdc` 결정을 2026-09-25 복원). 생성 스크립트·별도 유지는 두 사본이 다시 갈라지므로 택하지 않았다.
