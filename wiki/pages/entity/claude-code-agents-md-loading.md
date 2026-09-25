---
title: claude-code-agents-md-loading
category: entity
created: 2026-09-25
updated: 2026-09-25
sources:
  - https://code.claude.com/docs/en/memory (AGENTS.md 절, 2026-09-25 조회)
  - headless 실측 2026-09-25 (Claude Code 2.1.282)
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

## 연계

Codex 와의 역할 분담은 [[claude-codex-collaboration]], 항상 주입되는 문서의 크기 관리는 [[ops-doc-slimming]].

Codex 용 AGENTS.md 는 **심링크**로 결정됐다(2026-06-10 `a3d7bdc` 결정을 2026-09-25 복원). 생성 스크립트·별도 유지는 두 사본이 다시 갈라지므로 택하지 않았다.
