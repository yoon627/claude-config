---
title: translate-skill-wt — skills/wt(본문·references 2개)를 규칙 손실 없이 영어로 옮긴다
status: done
started: 2026-10-27
updated: 2026-10-27
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
`skills/wt/SKILL.md`(frontmatter description 포함)와 `references/env-copy.md`·`references/rm-recovery.md` 를 영어로 옮긴다. 규칙은 빠지거나 약해지거나 강해지지 않고, 절 이름 `request`·`rm`·번호(request §1~§4·§3.0~§3.6·rm 1~7)는 그대로다.
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-repo 단위의 네 번째. 방법은 `plans/2026-10-27-translate-skill-c/` 와 같다(번역 전 manifest, 조항 전체를 덮는 위치 인용, 변형 시험).
- Constraints(델타): 스크립트 출력과 글자로 맞아야 하는 `세션 활동 없음`·`ticket=(없음)`·`합계`·`등록 차단`(jira-worklog 출력)과 비ASCII 입력 예시 `"로그인 리다이렉트 버그 수정"` 은 원문 그대로. 미뤄 둔 `skills/wt/SKILL.md` 의 "e 는 조건5 게이트"(지금 e 번호로 조건4)를 이 단위에서 고친다(translate-claude-md·translate-skill-e log Deferred). 사용자 지시(2026-10-26): 추천안대로 끝까지 진행.
- Out of scope(델타): 규칙 내용 변경(찾은 결함은 plan log Deferred) · `heal_submodules.py` 등 코드 · README.
- Split: none — 본문과 references 는 서로 절 이름(`## Cautions`·`rm §6`)으로 가리켜 같은 머지에서만 맞다.

# Tasks
- [x] 범위 확인 (2026-10-27) — 사용자 "skills/wt 번역"
- [x] 대조 기준 (2026-10-27) — `plans/2026-10-27-translate-skill-wt/manifest.md`(조항 118개를 번역 초안 전에 작성, 계획 리뷰 뒤 122개), `plans/2026-10-27-translate-skill-wt/check-wt.js`, `plans/2026-10-27-translate-skill-wt/pointers.md`
- [x] 번역 (2026-10-27) — `skills/wt/SKILL.md` 134줄·`skills/wt/references/env-copy.md` 33줄·`skills/wt/references/rm-recovery.md` 23줄, 줄 구조 유지
- [x] 새 위치·기계 대조·변형 시험 (2026-10-27) — `plans/2026-10-27-translate-skill-wt/locations-en.txt`, check-wt PASS, 변형 11/11 FAIL(scratch `mut-wt.js`)
- [x] 리뷰 4개 병렬 (2026-10-27) — 게이트 대조 OK 57·CHANGED 1, 조항 대조 OK 117·CHANGED 1(같은 :131 바로잡음), code-reviewer APPROVE, 계획 리뷰 CONDITIONAL — 처분은 `plans/2026-10-27-translate-skill-wt/translate-skill-wt-log.md`
- [x] 리뷰 반영 (2026-10-27) — `skills/wt/SKILL.md` 문구 8곳, check-wt 5절(덮이지 않은 구간)·인용 1회 검사, manifest 조항 4개 추가·12개 보강, 변형 A 21/21·문장 삭제 228/228 FAIL
- [x] simplify 점검 (2026-10-27) — 생략: 코드 변경 없음
- [x] 사용자 diff 확인 (2026-10-27) — 사용자 "커밋": 포인터 바로잡음 3곳·원문 그대로 둔 출력 글자·Acceptance 문구 강화 포함
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-27) — `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 미설치, 무관), check-wt PASS, 변형 21/21·228/228, Acceptance 1~4·6 관찰
- [x] 기록 커밋(plan·log·manifest·locations·check-wt·pointers·intent), commit-check (2026-10-27)
- [x] 머지 (`/e merge`) (2026-10-27) — PR #246
- [x] [post-merge] 새 세션에서 관찰 — 한국어 요청("로그인 버그 고쳐줘" 같은 작업 요청)과 `/wt` 호출에 맞는 skill 로 wt 가 골라지는지 (2026-10-27) — 새 headless 세션이 "로그인 리다이렉트 버그 고쳐줘"·"/wt rm old-branch" 둘 다 `wt` 를 골랐다(직접 질문 표본 1개 ⚠️)
- [x] [post-merge] main 세션에서 공용 wiki 확인·갱신 — pointers.md 의 [post-merge] 절 (2026-10-27) — wt 를 가리키는 곳은 모두 경로·절 번호라 고칠 인용 없음, 공용 wiki 커밋 4d674f1(ops-doc-slimming 4단계·log)

# Acceptance
1. 규칙 손실 0 — manifest 조항(122개)마다 locations-en.txt 의 영어 인용(조항 전체를 덮는 하나 이상, 파일 안에서 한 번)이 그 파일에 글자 그대로, 인용 밖에 규칙 문장이 없고, 변형을 넣으면 잡힌다 — `check-wt.js` 1절·5절 + 변형 시험(손으로 고른 변형과 모든 문장 삭제) — missing·not found·uncovered 0, 변형 전부 FAIL
2. 식별자·명령·글자로 맞추는 출력은 그대로 — 핵심 문구 56개가 세 파일 어딘가에 글자 그대로 — `check-wt.js` 2절 — 전부 찾음
3. 한국어 없음 — 원문 그대로 둔 문자열(`세션 활동 없음`·`ticket=(없음)`·`합계 <duration>`·`등록 차단`·한국어 입력 예시) 밖 한글 0 — `check-wt.js` 3절 — 0
4. 표지 — 세 파일 줄 수가 원문과 같음, 절 제목·request §3.0~§3.6·rm 1~7, references 가 `## Cautions` 를 가리킴, 원문자 없음, e 7단계 조건4 포인터, description 평문에 `: ` 없음 — `check-wt.js` 4절 + `node scripts/frontmatter-lint.js skills/wt/SKILL.md` — 누락 0
5. 독립 대조 — 게이트 줄 전담 1개 + 조항별(manifest 감사 포함) 1개 — OK 아닌 판정마다 반영하거나 반박해 plan log 에 — 미처분 0
6. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
7. [post-merge] 공용 wiki — pointers.md 의 [post-merge] 절 처리
8. [post-merge] 관찰 — 새 세션에서 한국어 작업 요청·`/wt` 호출에 맞는 skill 로 wt 가 골라진다 — 아니면 description 예시를 되돌리는 안을 제안

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다. 앞 번역 단위들(translate-claude-md·e·c)의 방법과 묶음 Constraints 를 그대로 쓴다.
- 원문 그대로 둔 문자열은 두 방향이다 — wt 가 읽는 스크립트 출력(`세션 활동 없음`·`ticket=(없음)`·`합계`·`등록 차단` — `skills/jira-worklog/jira_worklog.py:193,236,243-244`)과 git/OS stderr("modified or untracked files" 등 — 원래 영어라 핵심 문구로 지킨다). 바꾸면 wt rm 의 worklog 판정·stderr 분기가 깨진다. `"로그인 리다이렉트 버그 수정"` 은 비ASCII 입력 예시라서 그대로. 기각: 전부 영어로(출력 판정이 깨지고, 예시의 요점이 사라진다). 기각: 부재 판정에 쓰는 `세션 활동 없음`·`ticket=(없음)` 만 원문 유지(계획 리뷰 W — `합계`·`등록 차단` 도 모델이 출력에서 찾는 글자라 같은 이유가 적용된다).
- ⚠️ :131 원문 "삭제 계열(아래 첫 bullet)" 은 방향이 틀렸다(그 bullet 은 위) — 번역에서 "the first bullet above" 로 바로잡았다 — 원문 그대로 옮기는 안도 있었다 — 틀린 포인터를 영어로 옮길 이유가 없다(규칙 변경 아님). :21 "ask 섹션" 도 없는 절이라 "Question mode section" 으로(같은 이유). 사용자 diff 확인으로 검증.
- :53 "no active worktree session" 은 하네스 반환 원문을 확인하지 못해 설명으로 두고 핵심 문구에 넣지 않는다.
- 대조 방법 보강(계획 리뷰 S1): check-wt 5절(덮이지 않은 구간 검사)과 문장 삭제 sweep. Acceptance 1~4 문구를 바꿨다 — 1 "조항(118개)… 1절 + 변형 시험" → "조항(122개)… 1절·5절 + 변형 시험(손으로 고른 변형과 모든 문장 삭제)", 2 "47개" → "56개", 3 원문 그대로 둔 문자열에 `합계 <duration>`·`등록 차단` 추가, 4 "e 조건4" → "e 7단계 조건4" — 검사를 넓히는 쪽이라 통과 기준은 약해지지 않는다, 사용자 승인은 diff 확인에서.
- 원문자: 해석 순서의 ①②②.5③④⑤ → 1) 2) 2.5) 3) 4) 5), 복사 대상 ①② → 1) 2)("2) 를 복사하는 이유"). 다른 파일이 이 번호를 가리키지 않는다.
- `## 주의` → `## Cautions` — references 2곳이 이 제목을 가리켜 같은 머지에서 바꿨다.
- e 포인터: "e 는 조건5 게이트로 차단" → "e blocks it with its step 7 condition 4 (merged) gate"(지금 e 7단계 조건4 가 merged 게이트 — 단계 이름까지 적어 e 번호가 다시 바뀌어도 찾을 수 있게) — 앞 단위들의 Deferred 를 이 단위에서 처리.
- 보고·질문 문구("신규 생성: …"·"→ dlc 시작: …"·near-miss 줄·AskUserQuestion 옵션)는 영어로 — CLAUDE.md §0 에 따라 사용자 답에서는 한국어로 쓴다.
- README 는 바꾸지 않는다(동작 불변, README 는 §0 밖) — `dlc-doc-drift` 경고는 예상된 오탐.
- 커밋 단위: 1개 — `docs(wt): translate skills/wt into English`(본문·references 3개). plan·log·대조 파일은 기록 커밋.
- 테스트: 문서라 새 테스트 없음(§7 예외 — 수동 검증은 Acceptance 1~5). 사용자 diff 확인이 행동 검증.
- Codex 미가용. architecture-reviewer 는 부르지 않는다(문서만).
- 롤백: `git revert -m 1 <merge sha>`.

# Blockers
