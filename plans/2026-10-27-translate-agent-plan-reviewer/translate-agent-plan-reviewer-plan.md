---
title: translate-agent-plan-reviewer — 공통 대조 검사를 만들고 agents/plan-reviewer 를 규칙 손실 없이 영어로 옮긴다
status: done
started: 2026-10-27
updated: 2026-10-27
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
묶음 공통 대조 검사(`plans/2026-10-21-ops-docs-rework/check-translation.js`·`mut-translation.js`, 단위는 설정 JSON 만)를 만들고, 그것으로 `agents/plan-reviewer.md`(frontmatter description 포함, 89줄)를 영어로 옮긴다. 검토 관점 1~15 번호·묶음 모드·출력 형식의 절 구성은 빠지거나 약해지거나 강해지지 않는다(사용자, 2026-10-27 "공통 검사 만들고 다음 번역").
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-repo 단위의 일곱 번째. `plans/2026-10-21-ops-docs-rework/terms.md` 를 따른다.
- Constraints(델타): `## Codex 병행` 으로 시작하는 두 제목(본문 절·출력 템플릿 소절)은 그대로 — `scripts/bootstrap/sync_codex_agents.py` 의 `CODEX_SECTION` 이 이 접두로 Codex 절을 뗀다(terms.md). Codex 프롬프트는 §0 대로 영어로 옮기고, 결론부 추출 grep 패턴은 같은 머지에서 프롬프트가 요구하는 영어 제목에 맞춘다. 검토 관점 번호 1~15(dlc 가 "15항", 이 파일이 "12항과 15항" 으로 가리킨다)·`[bundle]`·`NEEDS DISCUSSION`·`GO | NO-GO | CONDITIONAL` 은 그대로. plan 파일 표지 `없음 — <…>`·`none — <…>` 는 plan 이 한국어라 `없음` 을 그대로 둔다. 출력 절 "plan 반영용 요약" → "Summary for the plan"(terms.md). 사용자 지시(2026-10-26): 추천안대로 끝까지 진행.
- Out of scope(델타): plan-reviewer 의 규칙 내용 변경(결함은 plan log Deferred) · 앞 단위의 검사 스크립트(check-cc·check-rs 등)를 공통 검사로 바꾸기(이미 머지된 기록이라 그대로) · `sync_codex_agents.py` 코드.
- Split: none — 공통 검사는 이 단위가 첫 사용처라 같은 머지에서 실제 대상으로 검증되고, 번역은 그 검사를 증거로 쓴다. 나누면 공통 검사를 실제 대상 없이 머지하게 된다(앞 두 단위 재검증은 scratch 증거).

# Tasks
- [x] 범위 확인 (2026-10-27) — 사용자 "공통 검사 만들고 다음 번역 (추천)", 다음 agent plan-reviewer(89줄)
- [x] 공통 대조 검사 (2026-10-27) — `plans/2026-10-21-ops-docs-rework/check-translation.js`, `plans/2026-10-21-ops-docs-rework/mut-translation.js` — 머지된 commit-check·researcher 단위에 설정만 만들어 돌려 PASS, 생성 변형 전부 FAIL(줄 모양·단어 없는 줄 검사를 그때 더했다)
- [x] 대조 기준 (2026-10-27) — `plans/2026-10-27-translate-agent-plan-reviewer/manifest.md`(조항 50개, 번역 초안 전에 작성)
- [x] 번역 (2026-10-27) — `agents/plan-reviewer.md` 89줄, 줄 구조 유지
- [x] 새 위치·설정·변형 시험 (2026-10-27) — `plans/2026-10-27-translate-agent-plan-reviewer/locations-en.txt`, `plans/2026-10-27-translate-agent-plan-reviewer/check.json`, `plans/2026-10-21-ops-docs-rework/terms.md` 줄 추가 — 공통 검사 PASS(조항 50·핵심 문구 34), 변형 R 21/21·G swap 45/45·edge 60/60·blank 80/80·del 93/93, sync 실행에서 Codex 절 잔존 0(단어 없는 줄은 5절에서 면제 — 4절이 원문과 같게 묶는다)
- [x] 리뷰 4개 병렬 (2026-10-27) — 게이트 대조 OK 91·WEAKER 1, 조항 대조 OK 51·WEAKER 1(같은 X.1), code-reviewer REQUEST CHANGES(공통 검사 Major 2), 계획 리뷰 CONDITIONAL — 처분은 `plans/2026-10-27-translate-agent-plan-reviewer/translate-agent-plan-reviewer-log.md`
- [x] 리뷰 반영 (2026-10-27) — 공통 검사(`plans/2026-10-21-ops-docs-rework/check-translation.js`·`mut-translation.js`): 원본 먼저 PASS·SETUP 실패 처리·종료 코드, 핵심 문구 첫 비공백 줄·0개 FAIL, 조항 id 형식, CRLF, 본문 들여쓰기·펜스 고정, 인용 밖은 줄 머리 목록 표시만, 생성 변형에 들여쓰기·강조·펜스 태그. `agents/plan-reviewer.md` X.1 "Follow"·observed·묶음 모드 출력 문장·"Review checklist". `plans/2026-10-21-ops-docs-rework/terms.md` 표 이어 붙이기·Codex 절 용어 3줄
- [x] simplify 점검 (2026-10-27) — 생략: 제품 코드 변경 없음(공통 검사는 plans 의 기록 파일, 리뷰 지적만 반영)
- [x] 사용자 diff 확인 (2026-10-27) — 사용자 "커밋": Codex 제목 접두 유지·Codex 프롬프트와 grep 영어화·공통 검사·Acceptance 강화와 9 추가 포함
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-27) — `ALL PASS`, 공통 검사 PASS, 변형 R 22/22·G 전부(swap 45·edge 120·blank 80·indent 11·fence 4·del 93), sync 테스트 11 OK·dry-run exit 0, Acceptance 1~4·6 관찰
- [x] 기록 커밋(plan·log·manifest·locations·check.json·공통 검사·terms·intent), commit-check (2026-10-27)
- [x] 머지 (`/e merge`) (2026-10-27) — PR #249
- [ ] [post-merge] 새 세션에서 관찰 — 계획 검토 요청에 plan-reviewer 가 골라지는지
- [ ] [post-merge] main 세션에서 공용 wiki 확인 — plan-reviewer 문구 인용 확인, ops-doc-slimming·log 기록
- [ ] [post-merge] Codex 가 있는 머신에서 `scripts/bootstrap/sync_codex_agents.py` 재실행
- [ ] [post-merge] Codex 가 있는 머신에서 plan-reviewer 의 Codex 병행 검토를 한 번 돌려 결론부 추출 grep(`grep -iE '^##? (strong concerns|weak concerns|suggestions|integration)'`)이 우려 블록을 뽑는지 관찰

# Acceptance
1. 규칙 손실 0 — `node plans/2026-10-21-ops-docs-rework/check-translation.js <root> plans/2026-10-27-translate-agent-plan-reviewer/check.json` 이 PASS: manifest 조항마다 인용이 글자 그대로·한 번·manifest 순서대로, 인용 밖은 공백과 줄 머리 목록 표시만(제목·frontmatter 형식 줄·코드 펜스·단어 없는 줄 제외), 줄 모양·들여쓰기가 원문과 같고 단어 없는 줄·코드 펜스는 원문과 같다 — 그리고 `node plans/2026-10-21-ops-docs-rework/mut-translation.js <root> <check.json> <scratch>` 가 원본 PASS 를 먼저 확인한 뒤 규칙 변형(R)·생성 변형(G: 줄 바꿔치기·인용 끝 삽입·강조·빈 줄 채우기·들여쓰기·펜스 태그·문장 삭제)이 전부 FAIL, 종료 코드 0. 뜻이 원문과 같다는 근거는 이 검사가 아니라 5(독립 대조)와 사용자 diff 확인이다
2. 식별자·글자로 맞추는 문자열은 그대로 — manifest 핵심 문구가 backtick 째로 — 공통 검사 2절 — 전부 찾음
3. 한국어는 원문 유지 문자열(`## Codex 병행`·`없음`) 안에만 — 공통 검사 3절 — 0
4. 표지 — 줄 수, frontmatter(`name`·`tools`·`model` 불변), 제목 줄 목록 정확 일치, 검토 관점 1~15, description 평문에 `: ` 없음, sync 스크립트가 Codex 절을 뗀다 — 공통 검사 4절 + `node scripts/frontmatter-lint.js agents/plan-reviewer.md` + `python3 scripts/bootstrap/sync_codex_agents.py --source agents --out <scratch> --dry-run` — 누락 0, sync exit 0
5. 독립 대조 — 게이트 줄 전담 1개 + 조항별(manifest 감사 포함) 1개 — OK 아닌 판정마다 반영하거나 반박해 plan log 에 — 미처분 0
6. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
7. [post-merge] 공용 wiki — plan-reviewer 문구 인용 확인·기록
8. [post-merge] 관찰 — 새 세션에서 계획 검토 요청에 plan-reviewer 가 골라진다
9. [post-merge] Codex 결론부 추출 — Codex 가 있는 머신에서 plan-reviewer 의 Codex 병행 검토를 한 번 돌려 영어 grep 이 우려 블록을 뽑는다 — 아니면 프롬프트에 제목 형식을 못박는 안을 제안(Deferred)

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다. 묶음 용어표 terms.md 를 따른다.
- 공통 대조 검사(사용자 2026-10-27): 단위마다 검사 스크립트를 복사해 고치면 새 단위 구조(frontmatter 줄·출력 템플릿·순서 규칙)에서 빈틈이 새로 생겼다(wt S1·commit-check S2·researcher S1). 그래서 검사·변형을 한 곳에 두고 단위는 설정 JSON(manifest·locations·원문 유지·frontmatter·제목 목록·번호 블록·허용 기호·규칙 변형)만 준다. 구조 변형(줄 바꿔치기·인용 끝 삽입·빈 줄 채우기·문장 삭제)은 단위가 고르지 않고 생성한다. 줄 구조 1:1 유지를 이용해 줄 모양(빈 줄·제목 수준·코드 펜스·목록·번호)과 단어 없는 줄을 원문과 줄 번호로 맞춘다 — 검증 중 제목↔본문·펜스↔본문·JSON 괄호 바꿔치기가 순서 검사만으로는 PASS 해서 더했다. 기각: 단위별 스크립트 유지(같은 지적이 세 번). 기각: 앞 단위 스크립트를 공통 검사로 바꾸기(머지된 기록이라 그대로 두고, 공통 검사가 그 단위들도 통과하는지는 scratch 설정으로 확인했다).
- Codex 프롬프트를 영어로, 결론부 추출 패턴을 그 영어 제목으로(`grep -iE '^##? (strong concerns|weak concerns|suggestions|integration)'`) — 프롬프트가 요구하는 제목과 grep 이 같은 머지에서 맞아야 한다. ⚠️ 대소문자 무시(`-i`)를 더했다 — 원문은 한국어 낱말이라 대소문자가 없었고, 영어 제목은 "Strong Concerns" 처럼 올 수 있다 — 원문 그대로(`-E` 만)도 가능했다 — Codex 응답을 이 세션에서 관찰할 수 없어(미가용) 넓게 잡는 쪽을 택했다.
- plan 파일 표지 `없음 — <reason>` 은 `없음` 을 그대로(plan 은 한국어이고, `skills/dlc/SKILL.md` 요구사항 명확화가 `없음 — <근거 한 구절>` 을 정한다), 자리표시자만 영어. terms.md 에 더한다.
- 가장 위험한 곳: 공통 대조 검사 — 다음 단위들이 모두 그 빈틈을 물려받고, 빈틈은 여러 단위 뒤에야 드러난다(그래서 머지된 두 단위에 되돌려 돌리고 음성 시험을 했다). 다음은 Codex 추출 grep 변경 — 이 세션에서 관찰할 수 없어 [post-merge] Acceptance 9.
- description 을 영어로 옮겼다(앞 단위들과 같다) — 머지 뒤 Acceptance 8 로 선택을 확인한다. 기각: 한국어 description 유지(한 파일에 언어가 섞인다).
- Acceptance 1 문구를 바꾸고 9 를 더했다(계획 리뷰·code-reviewer) — 1 "인용 밖은 공백과 허용 기호만(… 코드 펜스 제외) … 단어 없는 줄은 원문과 같다 … 문장 삭제)이 전부 FAIL" → "인용 밖은 공백과 줄 머리 목록 표시만(… 단어 없는 줄 제외), 줄 모양·들여쓰기 … 코드 펜스는 원문과 같다 … 원본 PASS 를 먼저 확인한 뒤 … 강조·들여쓰기·펜스 태그 … 종료 코드 0", 9 는 Codex 추출 관찰 — 검사를 넓히는 쪽이라 통과 기준은 약해지지 않는다, 사용자 승인은 diff 확인에서.
- README 는 바꾸지 않는다(동작 불변, README 는 §0 밖).
- 커밋 단위: 1개 — `docs(plan-reviewer): translate agents/plan-reviewer into English`. 공통 검사·plan·log·대조 파일·terms·intent 는 기록 커밋.
- 테스트: 문서라 새 테스트 없음(§7 예외 — 수동 검증은 Acceptance 1~5). 공통 검사는 plans 의 기록 파일이라 repo 테스트에 넣지 않는다(앞 단위들과 같다). 사용자 diff 확인이 행동 검증.
- Codex 미가용. architecture-reviewer 는 부르지 않는다(문서만).
- 롤백: `docs(plan-reviewer)` 커밋만 `git revert <sha>`(공통 검사·terms 는 다음 단위가 쓴다), 되돌린 뒤 Codex 머신에서 sync 재실행.

# Blockers
