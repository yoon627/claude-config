---
title: translate-wiki-docs — 공용 wiki docs/ 5개를 규칙 손실 없이 영어로 옮긴다
status: done
started: 2026-10-31
updated: 2026-10-31
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
공용 wiki `~/.claude/wiki/docs/` 의 `codex-review.md`·`dlc-details.md`·`headroom-proxy-session-lifecycle.md`·`wiki-inbox.md`·`worktree-lifecycle.md` 를 영어로 옮긴다. skill·agent 가 읽는 절차·조건·명령은 빠지거나 약해지거나 강해지지 않는다(사용자 2026-10-31 "물어보지 말고 이번 세션 작업 모두 마무리해서 main 반영").
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-wiki-docs 단위. terms.md 와 공통 대조 검사를 쓴다.
- Constraints(델타): 번역은 공용 wiki repo main 에 직접 커밋한다(CLAUDE.md §11 — 문서 계층). 대조 파일(manifest·locations·check.json)과 이 plan 은 `~/.claude` 에 둔다(공통 검사가 여기 있다). skill 이 가리키는 절 표지(§A~§E, §1~§7 등)는 그대로 둔다. 공개 점검(§11)을 지킨다.
- Out of scope(델타): `wiki/pages/`(intent Open question) · wiki repo 의 코드 계층.
- Split: none — 문서 5개는 같은 출처(intent 의 translate-wiki-docs 줄)이고 공용 wiki 는 문서마다 따로 되돌릴 수 있는 커밋으로 둔다(purpose-commit bundle: intent translate-wiki-docs · 문서 5개 · 한 plan 고정비 절약).

# Tasks
- [x] 대조 기준·번역·위치·설정 — 문서마다 `plans/2026-10-31-translate-wiki-docs/<doc>/`(manifest·locations-en.txt·check.json), 번역은 `~/.claude/wiki/docs/<doc>.md` (2026-10-31) — 조항 68·48·30·41·176
- [x] 공통 검사 PASS·변형 전부 잡힘(문서마다) (2026-10-31)
- [x] 포인터 — skill·agent·README 가 가리키는 절 표지가 그대로인지 확인 (2026-10-31) — 불일치 0
- [x] 리뷰 — 조항별 대조 2개 + code-reviewer, 처분은 `plans/2026-10-31-translate-wiki-docs/translate-wiki-docs-log.md` (2026-10-31) — 지적 5건 fix, code-reviewer APPROVE
- [x] 공용 wiki 커밋(문서마다) · check_links·schema clean (2026-10-31) — 번역 5 + §E M5 동기화 1 + repo 이름 1
- [x] 기록 커밋, ff-merge (2026-10-31)

# Acceptance
1. 문서마다 `node plans/2026-10-21-ops-docs-rework/check-translation.js /root/.claude/wiki <check.json>` PASS, `mut-translation.js` 가 원본 PASS 뒤 변형 전부 FAIL, 종료 코드 0
2. 독립 대조의 OK 아닌 판정을 모두 반영하거나 반박해 plan log 에 — 미처분 0
3. 포인터 — `rg "<doc>.md" skills agents CLAUDE.md README.md` 로 찾은 절 표지가 번역본에 그대로 있다
4. 공용 wiki `check_links.py`·`wiki_check.py schema` clean
5. 이 worktree `bash scripts/verify.sh changed` 가 `ALL PASS`

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다.
- 커밋: 공용 wiki 에 문서마다 `docs(<doc>): translate into English` 1개(따로 되돌릴 수 있게). `~/.claude` 쪽은 기록 커밋 1개.
- 대조 파일 위치: 공통 검사는 설정의 경로를 root 기준으로 붙이므로 root=`/root/.claude/wiki` 로 두고 설정 경로는 `../.claude/worktrees/translate-wiki-docs/plans/...` 처럼 상대로 적는다. 기각: wiki repo 에 대조 파일 두기(wiki repo 의 `plans/` 는 worktree+PR 계층 — WIKI.md).
- 테스트: 문서 번역이라 새 테스트 없음(§7 예외 — Acceptance 1~4).
- §E M5 를 skills/e(deferred-small-fixes)에 맞춘 것과 codex-review 의 repo 이름은 번역과 다른 목적이라 공용 wiki 에 별도 커밋으로 남겼다(번역만 따로 되돌릴 수 있게).
- 롤백: 공용 wiki 의 문서별 커밋을 `git -C ~/.claude/wiki revert <sha>`.

# Blockers
