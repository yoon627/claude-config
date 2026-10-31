---
title: translate-memory — 이 머신의 MEMORY.md·memory 를 영어로 옮기고 묶음을 닫는다
status: done
started: 2026-10-31
updated: 2026-10-31
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
이 머신의 memory(`~/.claude/projects/*/memory/` — `MEMORY.md` 색인과 memory 파일)를 영어로 옮기고, ops-docs-rework 묶음의 남은 Open question 을 처분해 intent 를 닫는다(사용자 2026-10-31 "물어보지 말고 이번 세션 작업 모두 마무리해서 main 반영").
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-memory 단위와 묶음 마무리.
- Constraints(델타): memory 는 gitignored 전역 상태라 main 세션에서 직접 고친다(CLAUDE.md §3-1) — 커밋 대상은 이 plan 과 intent·terms 뿐. 뜻·날짜·근거·링크·경로·명령은 그대로.
- Out of scope(델타): 다른 머신의 memory(이 세션에서 닿지 않는다 — [post-merge] Task).
- Split: none — memory 번역(커밋 없음)과 묶음 마무리 기록은 한 번의 기록 커밋으로 끝난다.

# Tasks
- [x] memory 번역 — `~/.claude/projects/-root--claude/memory/`(3개 + 색인, 넷째는 처음부터 영어), `~/.claude/projects/-root-repos-coin-trading-bot/memory/`(5개 + 색인, 하나는 이미 영어), `~/.claude/projects/-root-repos-garden-random-defense/memory/`(1개 + 색인) (2026-10-31) — frontmatter `name`·metadata 유지, 인용한 README 문구·plan 표지는 원문
- [x] intent 마무리 — `plans/2026-10-21-ops-docs-rework/intent.md`(`# Plans` 실제 경로, Open questions 처분, Constraints 갱신, status) (2026-10-31)
- [x] 용어표 추가 — `plans/2026-10-21-ops-docs-rework/terms.md`(translate-wiki-docs·translate-skill-dlc 단위가 정한 용어) (2026-10-31)
- [ ] [post-merge] 다른 머신에서 그 머신의 main 세션이 `~/.claude/projects/*/memory/` 를 같은 방식으로 영어로 옮긴다

# Acceptance
1. 이 머신의 memory 에 한국어가 남지 않는다(인용한 원문·plan 표지 제외) — `grep -c '[가-힣]'` 파일별 확인 — `-root--claude` 0(인용 `⚠️ (구현)` 1줄), coin-trading-bot 은 README 인용 1줄만, garden-random-defense 0
2. intent 의 모든 plan 이 done 또는 dropped 이고 Open question 이 모두 처분됐다 — intent 를 읽어 대조 — `status: closed`
3. `bash scripts/verify.sh changed` 가 `ALL PASS`, plan-lint 통과

# Decisions
- memory 파일은 git 밖이라 번역 자체는 커밋이 없다. 이 plan 이 기록이다.
- 다른 머신의 memory 는 이 세션에서 닿지 않아 [post-merge] Task 로 넘긴다(intent Open question 을 carried over 로 처분).
- intent 를 닫는다 — 모든 plan 이 done, Open question 은 resolved 또는 carried over(§10 수명 규칙).

# Blockers
