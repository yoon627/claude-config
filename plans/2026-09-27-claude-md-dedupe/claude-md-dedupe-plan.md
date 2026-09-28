---
title: claude-md-dedupe — ~/.claude worktree 세션의 CLAUDE.md 이중 주입 제거
status: done
started: 2026-09-27
updated: 2026-09-27
intent: plans/2026-09-27-improve-followups/intent.md
---

# Goal
이 repo(`~/.claude`)의 worktree 세션이 `CLAUDE.md` 를 전역 사본과 worktree 사본으로 두 번 싣지 않게 한다(컨텍스트 약 18.5k 토큰, haiku 기준).

# Intent
- 묶음: `plans/2026-09-27-improve-followups/intent.md` 의 claude-md-dedupe 단위.
- 델타: user `settings.json` 의 `claudeMdExcludes` 에 `**/.claude/.claude/worktrees/*/CLAUDE.md` 와 `**/.claude/.claude/worktrees/*/AGENTS.md` 를 더해 worktree 사본을 뺀다(사용자 결정 2026-09-27, AGENTS.md 는 실측으로 추가). `settings.json` 은 untracked 머신 로컬이라 repo 변경은 README(머신 간 sync 기준)와 wiki 기록뿐이고, 설정 파일은 머지 뒤 main 세션에서 고친다.

# Acceptance
1. 실측(적용 전, `--settings` 주입): worktree 세션에서 worktree `CLAUDE.md` 표식이 제외 패턴으로 사라지고, 전역 사본 내용은 남고, main 세션은 전역 사본을 그대로 싣는다. `CLAUDE.md` 만 빼면 켜지는 worktree `AGENTS.md` 폴백이 `AGENTS.md` 패턴으로 꺼진다. 확인: headless `claude -p` — 결과·입력 토큰.
2. README `settings.json` 절의 `claudeMdExcludes` 설명이 두 worktree 패턴·이유·결과(worktree 세션은 main checkout 의 CLAUDE.md 로 돈다, branch 변경은 main 반영 뒤 새 세션부터)·한계(macOS 만 실측)를 서술하고, RTK 문단의 옛 근거를 고친다.
3. wiki `claude-code-agents-md-loading` 에 이중 주입·AGENTS.md 폴백 실측과 패턴을 적고 `wiki/index.md`·`wiki/log.md` 동기화, `check_links.py wiki` clean.
4. `bash scripts/verify.sh` 마지막 줄 `ALL PASS`.
5. - [x] [post-merge] main 세션에서 `~/.claude/settings.json` 에 두 패턴을 넣고(JSON 유효성 확인), 설정 주입 없이 headless 로 worktree 세션을 다시 재서 worktree CLAUDE.md 표식이 사라지고 토큰이 main 수준인지 확인.

# Progress
- 2026-09-27: worktree 생성(base `origin/main@cacdc7d`). 실측(✅, `claude -p --model haiku --settings`, worktree `CLAUDE.md` 끝에 임시 표식 — 실측 뒤 원복): worktree 기본 = 표식 YES·입력 62,827 토큰, 제외 패턴 = 표식 NO·44,300, 제외 패턴에서도 전역 사본 내용 YES, main + 제외 패턴 = 전역 사본 내용 YES·44,097. 사용자 결정: worktree 사본 제외, user `settings.json`.
- 2026-09-27: code-reviewer APPROVE — minor 3·nit 7. minor 1(AGENTS.md 폴백)을 실측으로 확인: 표식 넣은 임시 `AGENTS.md` 가 기본 = NO, `CLAUDE.md` 만 제외 = YES, `AGENTS.md` 도 제외 = NO → `AGENTS.md` 패턴 추가. README·wiki·plan 문구 정정. `verify.sh` ALL PASS·check_links clean·plan-lint 0.
- 2026-09-27: main 세션에서 `~/.claude/settings.json` `claudeMdExcludes` 에 두 패턴 적용(JSON 유효). Acceptance 5 통과 — 설정 주입 없이 worktree 세션: worktree 표식 NO·전역 내용 YES·입력 44,371 토큰, main 44,097. 임시 표식 원복. 설정 적용을 머지 전에 해(untracked 라 순서 무관) plan 을 한 번에 닫는다.

# Next


# Decisions
- worktree **사본**을 뺀다(사용자 결정 2026-09-27). 전역 사본(`~/.claude/CLAUDE.md`)은 main 세션에서 프로젝트 파일과 같은 경로라 빼면 main 이 통째로 잃는다. 결과: worktree 세션과 그 subagent 는 main checkout 의 `CLAUDE.md` 로 돌고, branch 에서 고친 규칙은 main 작업트리에 반영(머지·pull)된 뒤 새 세션부터 적용된다 — 지금도 옛·새 사본이 동시에 들어가 오히려 모호했다. 기각: worktree 에서만 전역 사본을 빼 branch 편집을 바로 반영하기 — worktree 전용 settings 가 필요한데 `/wt` 가 복사하는 main `settings.local.json` 은 main 세션에도 적용돼 main 이 전역 사본을 잃는다.
- worktree `AGENTS.md` 도 뺀다로 변경 (이유: code-reviewer 지적을 실측으로 확인 — 제외된 CLAUDE.md 는 AGENTS.md 폴백 판정에서 세지 않아, `CLAUDE.md` 만 빼면 worktree 의 `AGENTS.md` 가 켜진다. 지금은 worktree 에 AGENTS.md 가 없지만 Codex 앱 import 가 미러를 만들면 다시 규칙이 섞인다).
- 패턴은 `**/.claude/.claude/worktrees/*/{CLAUDE,AGENTS}.md` 두 줄 — `.claude` 가 두 번 이어지는 경로만 맞아 이 repo 의 worktree 사본만 걸린다(`*` 는 한 구간이라 worktree 안의 하위 파일도 안 걸린다). 홈 경로가 없어 README 에 그대로 적을 수 있다.
- 위치는 user `settings.json`(사용자 결정). user 범위라 기존·신규 worktree 세션 모두 한 곳에서 적용된다. 기각안: main `settings.local.json` — project 범위라 `/wt` 가 새 worktree 에 복사할 때만 따라가고 기존 worktree 는 수동 복사가 필요하다.
- 정정: 선택지 설명에 "user `settings.json` 은 repo 에 추적돼 모든 머신에 적용"이라고 적었으나 틀렸다 — 2026-09-07 부터 untracked 머신 로컬이고 README 가 sync 기준이다(worktree 에 파일이 없어 확인). 위 비교는 정정한 사실로도 같다.
- 커밋 단위: 1개 — README·wiki·plan 이 한 설정 변경의 기록이다.

# Review Disposition
- [code] APPROVE. minor 1 worktree CLAUDE.md 를 빼면 AGENTS.md 폴백이 켜질 수 있음 — fix(실측 확인, `AGENTS.md` 패턴 추가). minor 2 "머지 뒤 적용"이 조건(main 작업트리 반영·새 세션)을 빠뜨림 — fix. minor 3 macOS 만 실측 — fix(README·wiki 에 명시). nit 토큰 기준 모델·과금 차이 — fix(haiku 기준, 캐시로 과금 차이는 작다). nit wiki "추가"가 적용 전 — accepted(Acceptance 5 를 done 전에 한다). nit README RTK 문단 옛 근거 — fix. nit intent 줄 메모가 착수 전 문구 — fix. nit plan "main = YES" 무엇이 YES 인지 — fix. nit README 패턴 설명 순서 — fix. nit 반대 방향 대안 기각 기록 — fix(Decisions). native-overlap-ledger 의 "수단 후보" — wontfix(날짜 붙은 재판정 스냅샷).

# Key Files
- `README.md` — `settings.json` 절 `claudeMdExcludes`, RTK 문단
- `wiki/pages/entity/claude-code-agents-md-loading.md` — 지침 파일 로딩 사실
- `~/.claude/settings.json` — 실제 설정(untracked, main 세션에서 편집)

# Blockers
없음
