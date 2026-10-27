---
title: translate-skill-c — skills/c/SKILL.md 를 규칙 손실 없이 영어로 옮긴다
status: done
started: 2026-10-27
updated: 2026-10-27
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
`skills/c/SKILL.md`(frontmatter description 포함)를 영어로 옮긴다. 규칙은 빠지거나 약해지거나 강해지지 않고, 단계 번호·예외 번호·점검 표는 그대로다.
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-repo 단위의 세 번째 파일. 방법은 `plans/2026-10-26-translate-skill-e/` 와 같다.
- Constraints(델타): c 는 이어받을 manifest 가 없어 이 단위가 한국어 원문으로 만든다(`plans/2026-10-27-translate-skill-c/manifest.md`). 입력·출력 문자열은 원문 그대로 — c 에는 해당이 없다(사용자 입력 토큰은 `/c` 뿐이고, 스크립트 출력과 글자로 맞출 문구가 없다 — 리뷰가 확인). 사용자 지시(2026-10-26): 추천안대로 끝까지 진행.
- Out of scope(델타): 규칙 내용 변경(찾은 결함은 plan log Deferred) · `scripts/frontmatter-lint.test.js` 의 OLD_C(0efce86 이전 description 을 고정한 테스트 입력이라 현재 파일과 무관).
- Split: none — 번역과 그것을 확인하는 대조가 한 머지에서만 유효하고, 저장소 안에서 c 를 글자로 인용하는 곳이 없어 나눌 단위가 없다. 공용 wiki 의 인용은 별도 repo 라 [post-merge] 로 한다(pointers.md).

# Tasks
- [x] 범위 확인 (2026-10-27) — 사용자 "다음 skill 번역"(추천: skills/c)
- [x] 대조 기준 — `plans/2026-10-27-translate-skill-c/manifest.md`(조항 74개, 핵심 문구 34개 — 한국어 없음), `plans/2026-10-27-translate-skill-c/check-c.js` (2026-10-27)
- [x] 계획 리뷰 (2026-10-27) — plan-reviewer CONDITIONAL, 처분은 plan log
- [x] 번역 (2026-10-27) — `skills/c/SKILL.md` 82줄 → 같은 줄 구조(리뷰 전에 적용해 리뷰 4개를 병렬로 돌렸다)
- [x] 새 위치 (2026-10-27) — `plans/2026-10-27-translate-skill-c/locations-en.txt`(조항 전체를 덮도록 여러 인용 허용)
- [x] 기계 대조 (2026-10-27) — Acceptance 1~4 PASS, 변형 시험 8/8 FAIL(scratch `mut-c.js`)
- [x] 독립 대조 (2026-10-27) — 게이트 줄 21줄 OK, 조항 75개 OK, manifest 감사 12개 중 위치 검사 밖 5개를 보탰다
- [x] code-reviewer, fix loop 1회 (2026-10-27) — APPROVE, 문구 반영. 처분은 plan log
- [x] simplify 점검 (2026-10-27) — 생략: 코드 변경 없음
- [x] 사용자 diff 확인 (2026-10-27) — 사용자 "커밋"(69행·60행 문구 포함)
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-27) — 격리 runner: `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 미설치, .ps1 변경 없음), check-c PASS(조항 75·핵심 문구 34·한글 0), 변형 8/8, plan-lint·frontmatter-lint 통과. 판정 DONE
- [x] 기록 커밋(plan·log·manifest·locations·check-c·intent), commit-check (2026-10-27) — 커밋 2개(번역·기록), 정리할 커밋 없음
- [x] 머지 (`/e merge`) (2026-10-27) — PR #245
- [ ] [post-merge] 새 세션에서 관찰 — 한국어 요청("진행하던 작업 이어가자")에 맞는 skill 로 c 가 골라지는지
- [ ] [post-merge] main 세션에서 공용 wiki 갱신 — pointers.md 의 [post-merge] 절(`pages/concept/feedback-memory.md:30`), log

# Acceptance
1. 규칙 손실 0 — manifest 조항(75개)마다 locations-en.txt 의 영어 인용(조항 전체를 덮는 하나 이상)이 새 SKILL 에 글자 그대로, 그리고 변형을 넣으면 잡힌다 — `check-c.js` 1절 + 변형 시험(조항 일부를 바꾼 사본 8개가 각각 FAIL) — missing·not found 0, 변형 8/8 FAIL
2. 식별자·명령은 그대로 — manifest 핵심 문구 34개가 새 SKILL 에 글자 그대로 — `check-c.js` 2절 — 전부 찾음
3. 한국어 없음 — `check-c.js` 3절 — 0
4. 표지 — 줄 수가 원문과 같음, `### 1.`~`### 3.`, 예외 1~5 번호, 점검 표 6행, 예외 4·5 참조 개수, 원문자 없음, description 평문에 `: ` 없음(frontmatter-lint) — `check-c.js` 4절 + `node scripts/frontmatter-lint.js skills/c/SKILL.md` — 누락 0
5. 독립 대조 — 게이트 줄 전담 1개 + 조항별(manifest 누락 찾기 포함) 1개 — OK 아닌 판정마다 반영하거나 반박해 plan log 에 — 미처분 0
6. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
7. [post-merge] 공용 wiki 의 c 인용 — pointers.md 의 [post-merge] 절 반영
8. [post-merge] 관찰 — 새 세션에서 한국어 요청에 맞는 skill 로 c 가 골라진다 — 아니면 description 예시를 한국어로 되돌리는 안을 제안

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다. translate-claude-md·translate-skill-e 의 방법과 묶음 Constraints(따옴표 안도 영어, 입력·출력 문자열은 원문, 한국어 파일 안 영어 인용은 섞기 아님)를 그대로 쓴다.
- description 의 사용자 요청 예시("진행하던 작업 이어가자")는 영어로 옮긴다 — e 와 같은 처리(뜻으로 알아보는 예시, e 는 머지 뒤 한국어 요청에 맞는 skill 로 골라졌다). 기각: 한국어로 두기(사용자 결정과 어긋남).
- plan 에 쓰는 Task 문구 `- [ ] PR#n 리뷰 반영: <요지>` → `- [ ] PR#n address review: <gist>` — 접두 `PR#n address review:` 는 영어 고정 문자열(e 의 Task 문구와 같은 처리, 이 문구를 찾는 스크립트는 없다), `<gist>` 는 plan 의 언어(한국어)로 쓴다. 기각: 접두를 한국어로 두기(사용자 결정 "전부 영어로"와 어긋나고, 다른 skill 의 Task 문구와 표기가 갈린다).
- 보고 문구("이어갈 plan 없음"·"intent 링크 끊김"·"PR 리뷰: 확인 불가(<사유>)")는 영어로 — CLAUDE.md §0 에 따라 사용자 답에서는 한국어로 쓴다. 기각: 한국어로 두기(같은 이유).
- README 는 바꾸지 않는다 — 동작이 바뀌지 않고 README 는 §0 언어 정책 밖이다. `dlc-doc-drift` Stop hook 경고는 예상된 오탐.
- ⚠️ (구현) 원문이 모호하거나 영어에서 다르게 읽히는 곳을 dlc·e 의 실제 문구에 맞췄다 — :69 "dlc 가 main 밖이면" → "whenever it is not in a work worktree (on main or outside)"(dlc 진입 조건), :60 e 의 "세션종료 done 확인" → "the done confirmation of e's step 4"(e 에 있는 라벨). 원문 그대로 옮기는 안도 있었다 — 영어 "outside main" 은 dlc 규칙과 반대로만 읽혀 택했다(규칙 변경 아님) — `skills/c/SKILL.md` 3단계·보정 bullet. [리뷰 미경유] 사용자 diff 확인으로 검증.
- 커밋 단위: 1개 — `docs(c): translate skills/c into English`. plan·log·대조 파일은 기록 커밋.
- 테스트: 문서라 새 테스트 없음(§7 예외 — 수동 검증은 Acceptance 1~5). 사용자 diff 확인이 행동 검증.
- Codex 미가용 — reviewer 는 Claude 단독. architecture-reviewer 는 부르지 않는다(문서만).
- 롤백: `git revert -m 1 <merge sha>`.

# Blockers
