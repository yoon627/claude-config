---
title: codegraph-wt-doc-fix — worktree 인덱스 watcher-부재/staleness 문서 정확화
status: in_progress
started: 2026-07-19
updated: 2026-07-19
---

# Goal
worktree-local codegraph 인덱스가 **init 시점 스냅샷**(live watcher 없음)이라 편집 중 stale 해진다는 사실을, `곧 sync` 문구로 오해될 소지가 있는 운영 문서에 정확히 반영. 순수 문서 변경.

# Progress
- 2026-07-19: 조사·실증 완료(cgtest/cgtest2). memory `codegraph-projectpath-explicit` 갱신 + MEMORY.md 인덱스 갱신(worktree 밖, 별건). wt→dlc 진입, 이 plan 생성.
- 2026-07-19: 편집 4곳 완료(wt ref L16+staleness절, wiki codegraph page, wiki index, wiki log append). 검증: git diff 정확·일관, wiki page outbound 링크 2개 유지, 기존 실측 수치·근거 보존. parenthetical("cwd 바꿔도 MCP 서버 main 고정")을 MCP status(no-projectPath)=28파일=main 로 실측 확증. simplify: 편집 최소·중복 없음.
- 2026-07-19: commit `68204de` → push → **PR #96** (https://github.com/yoon627/claude-config/pull/96) main 대상 오픈.

# Next
PR #96 리뷰·머지 대기. 머지되면 worktree/브랜치 정리(/e step5).

# Decisions
- 규모 small(순수 문서, 로직/런타임 표면 없음) → TDD·code-reviewer subagent 생략, 대신 doc 일관성 자가검증. (이유: prose 정확성 검증이 acceptance)
- "곧 sync"(wt ref L16)는 *초기 background init 1회 완료*만 뜻하므로 문구 자체는 유지하되, "최초 1회뿐·이후 편집 자동 sync 아님"을 명시해 오독 차단. staleness 절에 watcher-부재 메커니즘(WHY) 추가.

# Key Files
- skills/wt/references/codegraph-worktree.md — L16 백그라운드 주의, L18-22 staleness 절
- wiki/pages/entity/codegraph.md — L21 worktree-local 인덱스 절 + frontmatter updated
- wiki/index.md — L20 codegraph 요약 동기화

# Acceptance
- [x] wt ref: "곧 sync"가 최초 init 1회뿐임을 명시 + staleness 절에 watcher-부재 메커니즘 반영 (관찰: 해당 줄 diff)
- [x] wiki codegraph page: init 스냅샷·watcher 부재·재-sync 필요 1~2줄 추가, updated 2026-07-19 (관찰: diff)
- [x] wiki/index.md: codegraph 요약이 페이지 변경과 동기 (관찰: diff), log.md 연산 로그 append
- [x] 링크 무결(≥2 outbound 유지), 기존 실측 수치·근거 링크 보존

# Blockers
(없음)
