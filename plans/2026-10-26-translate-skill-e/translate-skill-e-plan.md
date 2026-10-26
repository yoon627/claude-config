---
title: translate-skill-e — skills/e/SKILL.md 를 규칙 손실 없이 영어로 옮긴다
status: done
started: 2026-10-26
updated: 2026-10-26
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
`skills/e/SKILL.md`(frontmatter description 포함)를 영어로 옮긴다. 규칙은 빠지거나 약해지거나 강해지지 않고, 단계 번호·M 코드·조건 번호는 그대로다.
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-repo 단위의 두 번째 파일. 방법은 `plans/2026-10-26-translate-claude-md/` 와 같다.
- Constraints(델타): 입력·출력 문자열은 원문 그대로 둔다 — 사용자가 입력하는 인자 토큰 `/e 머지`, 스크립트가 출력하는 `"등록 불가"`(jira-worklog, 테스트가 고정), `wip:`·`(e checkpoint)`(commit-check 가 찾는다), 라벨 `main-autopull ⓑ`. 목록은 `plans/2026-10-26-translate-skill-e/pointers.md`. 역방향 대응표의 "worktree 정리 규칙 → worktree cleanup rules" 를 e 의 제목에 적용한다(CLAUDE.md §8 이 "the worktree cleanup rules" 로 가리킨다). 사용자 지시(2026-10-26): 이번에 정한 작업은 추천안대로 끝까지 진행.
- Out of scope(델타): `skills/e/collect-state.sh`(코드) · 규칙 내용 변경(찾은 결함은 plan log Deferred) · 공용 wiki `docs/worktree-lifecycle.md` 가 e 를 인용한 곳(main 세션, [post-merge]).
- Split: none — 한 파일이다. 저장소 안에서 e 를 가리키는 곳은 단계 번호·M 코드·영어 라벨로만 가리켜 번역으로 끊기지 않는다(pointers.md). 글자로 인용하는 곳은 공용 wiki(별도 repo)뿐이다.

# Tasks
- [x] 범위 확인 (2026-10-26) — 사용자 "진행해"(추천 순서: skills/e 부터)
- [x] 계획 리뷰 (2026-10-26) — plan-reviewer CONDITIONAL(Codex 미가용), 처분은 plan log. 사용자 지시 "추천안대로" 에 따라 추천안으로 반영
- [x] 대조 기준 고정 (2026-10-26) — `plans/2026-10-26-translate-skill-e/phrases-en.txt`(한국어 핵심 문구 12개의 대응표, 사용자 지시 "추천안대로"로 승인), `plans/2026-10-26-translate-skill-e/pointers.md`, `plans/2026-10-26-translate-skill-e/check-e.js`
- [x] 번역 (2026-10-26) — `skills/e/SKILL.md` 138줄 → 같은 줄 구조
- [x] 새 위치 채우기 (2026-10-26) — `plans/2026-10-26-translate-skill-e/locations-en.txt`
- [x] 기계 대조 (2026-10-26) — Acceptance 1~4 PASS(조항 194, 핵심 문구 89, 입력·출력 문자열 밖 한글 0, 표지·내부 라벨 개수)
- [x] 독립 대조 (2026-10-26) — 게이트 줄 58줄 전부 OK(WEAKER 0), 조항 194개 전부 OK, 넘겨받은 한정어 전부 확인
- [x] code-reviewer, fix loop 1회 (2026-10-26) — APPROVE(Critical·Major 0), 문구 6곳 반영. 처분은 plan log
- [x] simplify 점검 (2026-10-26) — 생략: 코드 변경 없음(§5 는 코드 변경에 필수)
- [x] 사용자 diff 확인 (2026-10-26) — 사용자 "커밋"
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-26) — 격리 runner: `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 미설치, .ps1 변경 없음), check-e PASS, plan-lint·frontmatter-lint 통과. 크기 35,850B → 36,255B(보조). 판정 DONE
- [x] 기록 커밋(plan·log·phrases·locations·intent), commit-check (2026-10-26) — 커밋 2개(번역·기록), commit-check 이상 없음
- [x] 머지 (`/e merge`) (2026-10-26) — PR #244
- [ ] [post-merge] 새 세션에서 관찰 — 한국어 요청("오늘 여기까지")에 e 가 불리는지, e 의 보고·질문이 한국어인지
- [ ] [post-merge] main 세션에서 공용 wiki 갱신 — pointers.md 의 [post-merge] 절, log. 관찰 뒤에 한다

# Acceptance
1. 규칙 손실 0 — slim-skill-e-ko manifest 의 조항(194개)마다 locations-en.txt 에 새 SKILL 의 영어 인용이 있고 글자 그대로 찾힌다 — scratch `check-e.js` — missing·not found 0
2. 식별자·명령은 그대로 — manifest 핵심 문구 중 한국어가 없는 것은 새 SKILL 에 글자 그대로, 한국어가 든 것은 phrases-en.txt 의 영어 대응 문구가 있다(`/e 머지` 는 그대로) — `check-e.js` — 전부 찾음
3. 한국어 없음 — 새 SKILL 의 한글은 입력·출력 문자열(`/e 머지`·`"등록 불가"`)뿐 — `check-e.js` 3절 — 예외 밖 0
4. 표지와 내부 참조 — `### 1.`~`### 8.`·`### 6 pre.`·`M1~M6`(물결)·M1 (1)~(5)·7단계 조건 1~6 번호, `## Temporary commit rules`·`## Worktree cleanup rules`·`## Boundaries` 제목, CLAUDE.md 가 쓰는 "`/e` step 6/7/8"·"M4" 표현, 내부 라벨(pointers.md 대응표)의 개수가 원문과 같음, 원문자 ①②③ 없음(ⓑ 는 유지) — `check-e.js` 4·4b절 — 누락·불일치 0
5. 독립 대조 — subagent 2개: 게이트 줄의 강도를 줄 단위로 보는 것 하나, 나머지 조항 id 마다 OK/MISSING/WEAKER/STRONGER/CHANGED/LOCATION-WRONG 판정하는 것 하나(slim-skill-e-ko log 가 넘긴 한정어 S2·W5·W6 포함) — OK 아닌 판정마다 반영하거나 반박해 plan log 에 — 미처분 0
6. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
7. [post-merge] 공용 wiki 의 e 인용을 새 영어 문구로 — pointers.md 의 [post-merge] 절 항목마다 반영
8. [post-merge] 관찰 — 새 세션에서 한국어 요청에 e 가 불리고 보고·질문이 한국어 — 관찰 — 아니면 revert 또는 description 예시를 한국어로 되돌리는 안을 제안

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다(규칙 손실 0 hard gate, 크기는 보조). translate-claude-md 의 방법·결정(intent Constraints: 따옴표 안도 영어, 한국어 파일 안 영어 인용은 섞기가 아님, 역방향 대응표)을 그대로 쓴다.
- 문체: translate-claude-md 와 같다 — 줄 단위, 구조·굵게 표시 유지, 줄이기 없음, 새 규칙 없음. 이력 표시("2026-09-30 실측" 등)도 그대로 옮긴다(줄이기가 아니므로).
- ⚠️ 입력·출력 문자열은 원문 그대로 둔다(`/e 머지`·`"등록 불가"`·`wip:`·`(e checkpoint)`·`main-autopull ⓑ`) — "따옴표 안도 영어"(사용자 결정)와 상충하지만, 이것들은 사용자 입력이나 스크립트 출력과 글자로 맞아야 동작한다(CLAUDE.md §0 "error messages in their original form" 과 같은 이유). 특히 `"등록 불가"` 를 옮기면 모델이 실제 경고를 알아보지 못해 미등록 worktree 를 지울 수 있다(되돌릴 수 없음). 기각: `/e 머지` 를 빼고 `/e merge` 만 남기기(사용자 입력이 깨진다).
- ⚠️ frontmatter description 의 사용자 요청 예시("진행상황 기록하고 마무리 / …")는 영어로 옮긴다 — manifest F.1 "description 은 그대로"(줄이기 때의 제약)를 이 단위가 고친다. 근거: 사용자 결정 "전부 영어로", 예시는 뜻으로 알아보는 것이라 입력 문자열이 아니다(CLAUDE.md §12 트리거 예시와 같은 처리). 대가: description 이 자동 호출의 유일한 신호인데 사용자는 한국어로 말한다 — 머지 뒤 관찰(Acceptance 8)로 확인하고, 안 불리면 예시를 한국어로 되돌리는 안을 제안한다. 기각: 예시를 한국어로 두기(사용자 결정과 어긋나고, 2026-10-07 prompt-audit-fixes 의 "오늘 여기까지 유지" 는 한국어 문서 시절 결정).
- plan 파일에 쓰는 Task 문구("clean up the commits, then rerun `/e merge`"·"PR #N waiting for checks, rerun `/e merge`"·WIP Task)는 영어 고정 문자열로 둔다 — CLAUDE.md 의 WIP Task 와 같은 처리, 읽는 쪽(M1 (5)·`/c`)은 뜻으로 알아본다(스크립트는 이 문구를 찾지 않는다 — plan-reviewer 확인). 기각: "뜻을 한국어로 쓰라"(문구가 세션마다 달라져 사람이 찾기 어렵다).
- 원문자: ①②③ 은 §0 대로 1)2)3) 으로, `main-autopull ⓑ` 는 공용 wiki 가 가리키는 라벨이라 그대로. `M1~M6` 의 물결도 wiki 가 "SKILL M1~M6" 로 가리켜 그대로.
- 제목·라벨: pointers.md 대응표 — "worktree 정리 규칙" → "Worktree cleanup rules"(역방향 대응표), "6 전" → "6 pre" 등. 정의와 사용처가 같은 영어를 쓰는지 개수로 확인한다(Acceptance 4).
- 커밋 단위: 1개 — `docs(e): translate skills/e into English`. plan·log·대조 파일은 마지막 기록 커밋.
- 테스트: 문서라 새 테스트 없음(§7 예외 — 수동 검증은 Acceptance 1~5). skill 은 main checkout 에서 로드돼 새 문구의 동작은 머지 전 관찰할 수 없다 — 사용자 diff 확인이 행동 검증이다.
- Acceptance 변경(계획 리뷰 반영, 사용자 지시 "추천안대로"): 1 "184개" → "194개"(대조 스크립트가 `6p.*` id 를 빠뜨렸던 계산 오류) · 3 예외를 `/e 머지` 하나에서 입력·출력 문자열로 · 4 에 `### 6 pre.`·내부 라벨 개수·원문자 추가 · 5 를 게이트 줄 전담 + 나머지로 · 7 범위를 pointers.md 로 · 8 추가.
- Codex 미가용(`codex: command not found`) — reviewer 는 Claude 단독. architecture-reviewer 는 부르지 않는다(문서만).
- 롤백: `git revert -m 1 <merge sha>`. 공용 wiki 편집은 별도 repo 라 따로 되돌린다.

# Blockers
