---
title: translate-hooks — hook 이 모델에게 주입하는 문구를 영어로 옮긴다
status: done
started: 2026-10-31
updated: 2026-10-31
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
hook 이 모델 컨텍스트로 보내는 한국어 문구(SessionStart stdout·UserPromptSubmit additionalContext·Stop block reason·PreToolUse deny reason — 35곳)를 영어로 옮기고, 그 문구를 확인하는 테스트와 글자로 인용하는 문서를 같은 머지에서 맞춘다. 문구의 뜻(조건·행동 지시·통과 방법)은 바뀌지 않는다(사용자 2026-10-31 "물어보지 말고 이번 세션 작업 모두 마무리해서 main 반영").
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-hooks 단위.
- Constraints(델타): 사용자가 주 독자인 문구(PreToolUse `ask` reason 2곳 — 대화형 세션의 확인 창, 데스크톱 알림 `입력 대기`·`응답 완료`)는 한국어로 둔다 — intent Open question 을 이렇게 닫는다(§0: 사용자에게 보이는 글은 한국어). 태그(`[dlc:investigation]` 등)·환경 변수·파일 이름·명령은 그대로. dlc 절 이름을 가리키는 곳은 translate-skill-dlc 의 영어 제목에 맞춘다.
- Out of scope(델타): `/improve` 가 읽는 CLI 출력(`dlc-signal.js` mark·`usage-count.js`·`improve.sh` — hook 이 아니다, terms.md 원문 유지 표) · 코드 주석 · 입력 쪽 한국어(`dlc-signal.js` 의 plan 자리표시자 `(리뷰 후 기록)` 대조).
- Split: none — 문구·그 테스트·그 문구를 글자로 인용하는 README·`skills/improve/SKILL.md` 7단계는 같은 머지에서만 맞는다.

# Tasks
- [x] 테스트 먼저(Red) — `scripts/session-brief.test.js`·`scripts/session-fetch.test.js`·`scripts/dlc-early-stop.test.js`·`scripts/dlc-task-router.test.js`·`scripts/guard-worktree-edit.test.js` 의 한국어 문구 assertion 을 영어로 바꾸고 실패 확인 (2026-10-31) — 50개 실패(log Review Disposition)
- [x] 구현(Green) — `scripts/session-brief.js`·`scripts/dlc-task-router.js`·`scripts/dlc-early-stop.js`·`scripts/dlc-doc-drift.js`·`scripts/guard-worktree-edit.js` (2026-10-31) — 해당 테스트 전부 통과, `plural` 도우미 추가
- [x] 인용 맞추기 — `README.md`·`skills/improve/SKILL.md` 7단계·`plans/2026-10-21-ops-docs-rework/terms.md`·`plans/2026-10-21-ops-docs-rework/intent.md`(Open question resolved) (2026-10-31)
- [x] code-reviewer, simplify 점검 (2026-10-31) — APPROVE, 지적 반영(log)
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 (2026-10-31)
- [x] 기록 커밋, ff-merge(translate-skill-dlc 다음) (2026-10-31)

# Acceptance
1. 모델 쪽 문구에 한글이 없다 — 위 5개 스크립트에서 출력 문자열(주석 제외)의 한글 0, 사용자 쪽 3곳은 한국어 그대로 — `rg` + 사람 대조
2. 바뀐 문구마다 테스트가 영어 문구를 assert 하고, 바꾸기 전에는 실패했다 — Red 실행 기록 → Green 에서 해당 테스트 전부 통과
3. 뜻 보존 — 문구마다 원문·번역 대조표를 plan log 에 두고 code-reviewer 가 조건·지시·통과 방법이 바뀌지 않았음을 확인
4. 인용 — `rg` 로 옛 한국어 문구를 repo 에서 찾아 0(원문 유지로 남긴 사용자 쪽 문구 제외), `skills/improve/SKILL.md` 7단계가 새 L 신호 문구를 글자 그대로 인용
5. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다.
- 사용자 쪽 문구는 한국어로 둔다 — `ask` reason 은 대화형 세션에서 사용자 확인 창에 보이고, 알림은 사용자 데스크톱에만 뜬다. headless `claude -p` 에서는 아무도 답할 수 없어 호출이 거부되고 모델이 그 reason 을 읽지만(hooks 문서, code-reviewer), 주 독자는 대화형 사용자이고 모델은 한국어도 읽으므로 두 언어를 섞지 않는다. 기각: 모두 영어(§0 의 "사용자에게 보이는 답은 한국어" 와 어긋난다), 두 언어 병기(문구가 길어지고 사용자 창에 영어가 섞인다).
- 커밋 단위: 1개 — `feat(hooks): send model-facing hook text in English`(문구·테스트·인용이 같은 머지에서만 맞는다). plan·log 는 기록 커밋.
- 롤백: 그 커밋 `git revert <sha>`.

# Blockers
