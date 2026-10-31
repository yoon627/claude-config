---
title: translate-agent-code-reviewer — agents/code-reviewer 를 규칙 손실 없이 영어로 옮긴다
status: done
started: 2026-10-31
updated: 2026-10-31
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
`agents/code-reviewer.md`(frontmatter description 포함, 147줄)를 영어로 옮긴다. 검토 관점·Find→Verify 2-pass·verdict 대응·출력 형식·Codex 병행·금지 사항은 빠지거나 약해지거나 강해지지 않는다(사용자 2026-10-31 "물어보지 말고 이번 세션 작업 모두 마무리해서 main 반영").
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-repo 단위(agent 4개 중 마지막). `plans/2026-10-21-ops-docs-rework/terms.md` 와 공통 대조 검사를 쓴다.
- Constraints(델타): `## Codex 병행` 접두는 원문(`sync_codex_agents.py` 가 이 제목으로 뗀다). plan 파일 표지(`⚠️ (구현)`·`[리뷰 미경유]`·`[plan 대비]` 등 plan 에 한국어로 남는 글자)는 원문. 다른 파일이 가리키는 절 이름·라벨을 바꾸면 같은 머지에서 그 포인터를 고친다(dlc 는 translate-skill-dlc 가 같은 날 옮기므로 그 단위와 맞춘다).
- Out of scope(델타): `skills/dlc/SKILL.md` 본문(translate-skill-dlc) · 옛 이름 "plan 반영용 요약" 지우기(agent 4개가 다 옮겨진 뒤 dlc 단위가 지운다 — terms.md) · 공용 wiki 페이지(main 세션).
- Split: none — 번역과 그 포인터는 같은 머지에서만 맞는다.

# Tasks
- [x] 대조 기준 — `plans/2026-10-31-translate-agent-code-reviewer/manifest.md`(번역 초안 전) (2026-10-31) — 84조항
- [x] 번역 — `agents/code-reviewer.md`, 줄 구조 유지 (2026-10-31) — 147줄, 원문 유지 4개(`## Codex 병행`·`[plan 대비]`·`⚠️ (구현)`·`"읽을 곳"`)
- [x] 위치·설정·변형 시험 — `plans/2026-10-31-translate-agent-code-reviewer/locations-en.txt`·`check.json` (2026-10-31) — 공통 검사 PASS, 변형 R 30/30·G 전부
- [x] 포인터 — `scripts/bootstrap/test_sync_codex_agents.py`(영어 문자열로), `plans/2026-10-21-ops-docs-rework/terms.md`(원문 유지 3줄·용어·기계 대조 4줄), dlc·공용 wiki 는 Deferred (2026-10-31) — sync 테스트 11 OK
- [x] 리뷰 — 게이트 줄 전담·조항별 대조·code-reviewer(Codex 미가용), 처분은 `plans/2026-10-31-translate-agent-code-reviewer/translate-agent-code-reviewer-log.md` (2026-10-31) — 3건 fix, code-reviewer APPROVE
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 (2026-10-31) — ALL PASS(skip: install-codex-skill.test.ps1 — PowerShell 미설치), Acceptance 1~5 충족
- [x] 기록 커밋, ff-merge (2026-10-31)
- [ ] [post-merge] 새 세션에서 code-reviewer 영어 보고 관찰 (Acceptance 6)

# Acceptance
1. 규칙 손실 0 — `node plans/2026-10-21-ops-docs-rework/check-translation.js <root> plans/2026-10-31-translate-agent-code-reviewer/check.json` PASS, `node plans/2026-10-21-ops-docs-rework/mut-translation.js <root> <check.json> <scratch>` 가 원본 PASS 뒤 변형(R·G) 전부 FAIL, 종료 코드 0
2. 독립 대조(게이트 줄 전담 1개 + 조항별 1개)의 OK 아닌 판정을 모두 반영하거나 반박해 plan log 에 — 미처분 0
3. 포인터 — 바뀐 절 이름·라벨을 `rg` 로 repo 에서 찾아 걸린 곳마다 처분(이 머지에서 고침 / 그대로 맞음 / dlc 단위 / main 세션 공용 wiki)
4. `node scripts/frontmatter-lint.js agents/code-reviewer.md` 통과, `python3 scripts/bootstrap/test_sync_codex_agents.py` 통과
5. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
6. [post-merge] 새 세션에서 code-reviewer 를 불러 영어 보고가 출력 형식대로 나오는지 관찰

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다. terms.md 와 공통 대조 검사를 쓴다.
- read-points worktree(다른 세션, 2026-10-14 시작·10-15 이후 정지, plan 파일만 있고 구현 없음)가 이 파일을 고칠 계획이지만 막지 않는다 — 구현이 없어 충돌할 코드가 없고, 그 작업은 어차피 오래된 base(2fc4b8f)를 새 main 위로 옮겨야 한다. 그 worktree 는 건드리지 않는다. 기각: read-points 머지를 기다리기(2주 넘게 멈춰 있어 번역이 무기한 막힌다).
- 순서: 이 단위를 dlc 단위보다 먼저 머지한다 — dlc 단위가 "agent 4개를 다 옮긴 뒤" 옛 이름을 지운다(terms.md).
- 커밋 단위: 1개 — `docs(code-reviewer): translate agents/code-reviewer into English`. plan·log·대조 파일은 기록 커밋.
- 테스트: 문서 번역이라 새 테스트 없음(§7 예외 — 수동 검증은 Acceptance 1~4).
- 문구 검증: CLAUDE.md §8 위임 예외 — 단 `agents/*-reviewer.md` 의 검토 기준·verdict 를 빼거나 약하게 하면 예외 밖이다. 번역은 규칙을 바꾸지 않는 것이 목표이고 이를 Acceptance 1·2 로 확인하며, code-reviewer 에게 완화 여부를 명시적으로 묻는다.
- 롤백: 번역 커밋만 `git revert <sha>`.

# Blockers
