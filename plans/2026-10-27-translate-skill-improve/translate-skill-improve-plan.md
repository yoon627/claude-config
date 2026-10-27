---
title: translate-skill-improve — skills/improve 를 규칙 손실 없이 영어로 옮긴다
status: in_progress
started: 2026-10-27
updated: 2026-10-27
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
`skills/improve/SKILL.md`(frontmatter description 포함, 81줄)를 영어로 옮긴다. 역할 경계·동작 1~7·점검 번호 1~12·§6 절차 1~5·경계(안 하는 것)는 빠지거나 약해지거나 강해지지 않는다(사용자, 2026-10-27 "skills/improve 번역").
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-repo 단위. `plans/2026-10-21-ops-docs-rework/terms.md` 와 공통 대조 검사(용어 대조 포함)를 쓴다.
- Constraints(델타): 스크립트가 찍는 글자는 그대로 — `신호 집계 실행 실패`(`skills/improve/improve.sh` 점검 7), `last-improve 마커 갱신:`(`scripts/dlc-signal.js mark`), SessionStart 안내 `/improve 권장 — failure 신호 N세션 누적 (마커 이후)`(`scripts/session-brief.js`). 점검 태그 `[error]`·`[warn]`·`[info]`·`[ok]`, 신호 kind 이름, 환경 변수, 경로는 그대로. 원문자 ①②⑨⑩⑪⑫ 는 CLAUDE.md §0 대로 — 스크립트가 "== 9." 처럼 숫자로 찍으므로 "check 9" 처럼 숫자로. 절·점검 번호(§6·점검 9 등)는 그대로(improve.sh·대장이 가리킨다). 사용자 지시(2026-10-26): 추천안대로 끝까지 진행.
- Out of scope(델타): `improve.sh`·테스트·`dlc-signal.js`·`session-brief.js` 의 한국어 출력(코드) · README.
- Split: none — 대상 파일 하나이고 번역과 그 대조가 한 머지에서만 맞는다.

# Tasks
- [x] 범위 확인 (2026-10-27) — 사용자 "skills/improve 번역 (추천)", 스크립트 출력 글자·가리키는 곳 조사
- [x] 대조 기준 (2026-10-27) — `plans/2026-10-27-translate-skill-improve/manifest.md`(조항 62개, 번역 초안 전에 작성)
- [x] 번역 (2026-10-27) — `skills/improve/SKILL.md` 81줄, 줄 구조 유지
- [x] 위치·설정·변형 시험 (2026-10-27) — `plans/2026-10-27-translate-skill-improve/locations-en.txt`, `plans/2026-10-27-translate-skill-improve/check.json`, `plans/2026-10-21-ops-docs-rework/terms.md` 줄 추가 — 공통 검사 PASS(조항 62·핵심 문구 63·용어 1쌍), 변형 R 24/24·G 전부(swap 37·edge 126·blank 84·indent 11·del 106·term 2), `improve.test.sh` all passed
- [x] 리뷰 4개 병렬 (2026-10-27) — plan-reviewer, 게이트 줄 전담 대조, 조항별·manifest 감사 대조, code-reviewer(Codex 미가용), 처분은 `plans/2026-10-27-translate-skill-improve/translate-skill-improve-log.md` — 7단계 "Otherwise" 모호성 등 반영, 재검사 PASS(핵심 문구 69)
- [x] simplify 점검 (2026-10-27) — 생략: 코드 변경 없음(문서 번역), 번역문의 군더더기는 리뷰 4개가 문장 단위로 봤다
- [x] 사용자 diff 확인 (2026-10-27) — "커밋 (추천)", Acceptance 8 변경 포함
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-27) — 격리 runner: `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 미설치, 문서 번역과 무관), 공통 검사 PASS(조항 62·핵심 문구 69), 변형 전부 잡힘, `improve.test.sh`·frontmatter-lint·plan-lint 통과 — Acceptance 1~6 충족
- [ ] 기록 커밋(plan·log·manifest·locations·check.json·terms·intent), commit-check
- [ ] 머지 (`/e merge`)
- [ ] [post-merge] 새 세션에서 관찰 — `/improve` 명시 호출이 improve 를 불러 `improve.sh` 를 실행하는지, 단순 질문에는 골라지지 않는지
- [ ] [post-merge] main 세션에서 공용 wiki 확인 — improve 문구 인용 확인, ops-doc-slimming·log 기록

# Acceptance
1. 규칙 손실 0 — `node plans/2026-10-21-ops-docs-rework/check-translation.js <root> plans/2026-10-27-translate-skill-improve/check.json` 이 PASS(인용 글자 그대로·한 번·manifest 순서, 인용 밖은 공백과 줄 머리 목록 표시만, 줄 모양·들여쓰기·단어 없는 줄·코드 펜스가 원문과 같다, 용어표 대조), 그리고 `node plans/2026-10-21-ops-docs-rework/mut-translation.js <root> <check.json> <scratch>` 가 원본 PASS 를 확인한 뒤 규칙 변형(R)·생성 변형(G, 용어 포함) 전부 FAIL, 종료 코드 0. 뜻이 원문과 같다는 근거는 이 검사가 아니라 5(독립 대조)와 사용자 diff 확인이다
2. 식별자·스크립트와 맞추는 글자는 그대로 — manifest 핵심 문구가 backtick 째로 — 공통 검사 2절 — 전부 찾음
3. 한국어는 원문 유지 문자열(위 세 출력 글자) 안에만, 원문자 없음 — 공통 검사 3·4절 — 0
4. 표지 — 줄 수, frontmatter(`name` 불변), 제목 줄 목록 정확 일치(### 1.~7. 번호 포함), §6 절차 1~5, description 평문에 `: ` 없음 — 공통 검사 4절 + `node scripts/frontmatter-lint.js skills/improve/SKILL.md` + `bash skills/improve/improve.test.sh`(스크립트 불변 확인) — 누락 0
5. 독립 대조 — 게이트 줄 전담 1개 + 조항별(manifest 감사 포함) 1개 — OK 아닌 판정마다 반영하거나 반박해 plan log 에 — 미처분 0
6. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
7. [post-merge] 공용 wiki — improve 문구 인용 확인·기록
8. [post-merge] 관찰 — 새 세션에서 `/improve` 명시 호출이 이 skill 을 불러 `improve.sh` 를 실행하고, 단순 질문(예: "README 에 뭐가 있어?")에는 improve 가 골라지지 않는다 — headless 관찰 — 둘 다 맞으면 통과, 어긋나면 description 영어 문구를 고치거나 한국어로 되돌리는 안을 제안

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다. terms.md 와 공통 대조 검사를 쓴다.
- 원문 유지: `신호 집계 실행 실패`·`last-improve 마커 갱신:`·`/improve 권장 — failure 신호 N세션 누적 (마커 이후)` — 스크립트가 찍는 글자이고 모델이 그 글자로 마커 갱신 여부·성공을 판단한다(7단계). 기각: 영어로 옮기기(출력과 글자가 안 맞는다).
- 원문자 → 숫자("check 9" 등) — improve.sh 가 "== 9." 처럼 숫자로 찍는다. ①② 는 "1)"·"2)".
- 가장 위험한 곳: 7단계 마커 갱신 조건(신호를 보지 못했으면 실행하지 않는다)과 경계(수정 안 함·대장 write 금지) — 잘못 옮기면 권장 신호가 영영 사라지거나 무승인 수정이 생긴다. 게이트 대조가 따로 본다.
- description 을 영어로 옮겼다(앞 단위들과 같다) — 머지 뒤 Acceptance 8 로 선택을 확인한다.
- README 는 바꾸지 않는다(동작 불변, README 는 §0 밖).
- 커밋 단위: 1개 — `docs(improve): translate skills/improve into English`. plan·log·대조 파일·terms·intent 는 기록 커밋.
- 테스트: 문서라 새 테스트 없음(§7 예외 — 수동 검증은 Acceptance 1~5). 사용자 diff 확인이 행동 검증.
- Codex 미가용.
- Acceptance 8 변경: "점검 요청에 improve 가 골라진다" → "`/improve` 명시 호출이 불러 실행하고 단순 질문에는 안 골라진다 + 어긋나면 되돌림 제안" — description 이 원문부터 "명시 호출 시 사용"이라 자연어 선택은 의도된 동작이 아니다(plan-reviewer·code-reviewer). 사용자 승인(2026-10-27, diff 확인 "커밋 (추천)").
- Codex 쪽 사용처: `scripts/bootstrap/setup.sh` 가 `~/.agents/skills/improve` 를 이 폴더로 symlink 한다 — 머지만으로 반영되고 따로 동기화할 것이 없다.
- Stop 의 `dlc-doc-drift` 경고(README 미갱신)는 예상된 오탐 — 동작이 바뀌지 않아 README 는 그대로 둔다.
- 원문 유지 출력 글자는 한 방향 결합이다 — 스크립트 쪽이 바뀌면 같은 머지에서 7단계 인용도 고친다고 terms.md 줄에 적었다(plan-reviewer).
- 롤백: `docs(improve)` 커밋만 `git revert <sha>`.

# Blockers
