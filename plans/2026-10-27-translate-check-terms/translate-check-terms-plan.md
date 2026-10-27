---
title: translate-check-terms — 공통 대조 검사에 용어표 기계 대조를 더한다
status: done
started: 2026-10-27
updated: 2026-10-27
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
공통 대조 검사가 묶음 용어표(`plans/2026-10-21-ops-docs-rework/terms.md`)의 기계 대조 블록을 읽어, 원문(원문 유지 문자열 밖)에 한국어 용어가 나온 횟수만큼 번역에 정해진 영어가 있는지 센다. 블록이 비거나 틀리면 FAIL 하고, 변형 시험에 용어 변형을 더한다(사용자, 2026-10-27 "용어 검사 넣고"). 번역 대상 파일은 바꾸지 않는다.
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-repo 의 공통 도구 보강.
- Why: architecture-reviewer 첫 번역이 용어표가 정한 "Review checklist" 대신 다른 말을 썼다 — 표를 "읽는다" 는 규칙만으로는 막지 못했다.
- Constraints(델타): jira-task·jira-worklog skill 은 건드리지 않는다(사용자, 2026-10-27 "jira 관련 스킬 건들지마") — 처음엔 jira-task 번역과 함께 한 단위였으나 그 번역을 되돌리고 이 검사만 남겼다. 사용자 지시(2026-10-26): 추천안대로 끝까지 진행.
- Out of scope(델타): 번역 대상 파일 · 이미 머지된 단위의 검사 스크립트(check-cc·check-rs 등).
- Split: none — 검사·읽기 모듈·변형 시험·용어표 블록이 서로 기대어 한 머지에서만 맞는다.

# Tasks
- [x] 범위 확인 (2026-10-27) — 사용자 "용어 검사 넣고 skill 번역 (추천)", 뒤에 "jira 관련 스킬 건들지마" 로 jira-task 번역은 되돌리고 검사만 남김("검사 개선만 남겨 머지 (추천)")
- [x] 용어 대조 (2026-10-27) — `plans/2026-10-21-ops-docs-rework/terms.md` 기계 대조 블록(43쌍·선택 규칙), `plans/2026-10-21-ops-docs-rework/terms-block.js`(블록 읽기 — 검사와 변형 시험이 함께 쓴다), `plans/2026-10-21-ops-docs-rework/check-translation.js` 4절(개수 비교·termsSkip 검증), `plans/2026-10-21-ops-docs-rework/mut-translation.js` G.term
- [x] 리뷰 (2026-10-27) — jira-task 단위로 함께 돌린 계획 리뷰·code-reviewer 가 용어 대조를 검토, 처분은 `plans/2026-10-27-translate-check-terms/translate-check-terms-log.md`
- [x] simplify 점검 (2026-10-27) — 블록 읽기를 `terms-block.js` 하나로 모았다
- [x] 사용자 diff 확인 (2026-10-27) — 2026-10-27 "커밋" 승인(jira-task 번역과 함께 받은 승인 중 검사 강화 부분), jira-task 번역 철회 뒤 "검사 개선만 남겨 머지"
- [x] 최종 격리 검증 (2026-10-27) — `ALL PASS`, 머지된 네 단위 PASS(4·11·23·24쌍), G.term 46/46·48/48, 음성 시험 다섯 개 FAIL, `skills/` 변경 0
- [x] 커밋, commit-check (2026-10-27)
- [x] 머지 (`/e merge`) (2026-10-27) — PR #251
- [x] [post-merge] main 세션에서 공용 wiki ops-doc-slimming·log 기록 (2026-10-27) — 공용 wiki 커밋 13efe22

# Acceptance
1. 머지된 단위가 그대로 통과 — `node plans/2026-10-21-ops-docs-rework/check-translation.js <root> <설정>` 을 plans/2026-10-27-translate-agent-plan-reviewer/check.json·plans/2026-10-27-translate-agent-arch-reviewer/check.json 과 scratch 의 commit-check·researcher 설정으로 — 모두 PASS, 용어 쌍이 적용된다
2. 변형 시험이 용어 변형을 잡는다 — `node plans/2026-10-21-ops-docs-rework/mut-translation.js <root> <설정> <scratch>` — 네 단위 모두 G.term 포함 전부 FAIL, 종료 코드 0
3. 빈틈이 막혔다 — 음성 시험: 용어를 한 곳만 바꾼 사본·형식이 틀린 블록 줄·빈 블록·잘못된 termsSkip(표·원문에 없음·이유 없음·목록 형식) — 모두 FAIL
4. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
5. [post-merge] 공용 wiki 기록

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다.
- 용어 대조: terms.md 에 기계 대조 블록(`<한국어> => <영어>`)을 두고, 공통 검사가 원문(원문 유지 문자열 밖)에 그 한국어가 나온 횟수만큼 번역에 그 영어가 있는지 센다(대소문자 무시). 블록의 형식이 틀린 줄·빈 블록·닫히지 않은 블록은 FAIL. 다른 뜻으로 쓰인 원문은 단위 설정 `termsSkip: {"<한국어>": "<이유>"}` — 표와 원문에 있어야 하고 이유가 있어야 하며 건너뛴 낱말을 출력한다. 블록 읽기는 `terms-block.js` 하나. 블록에는 한 뜻으로만 쓰이는 절 제목·필드·라벨만 넣는다(여러 뜻의 일상어 보류·합치기·나누기·제안은 사람용 표에만). 기각: 있는지만 보기(제목 하나가 맞으면 본문의 다른 말을 덮는다 — plan-reviewer 사본에서 재현, 두 리뷰). 기각: 별도 terms.json(사람용 표와 둘로 갈라진다). 기각: 단위 설정에 용어를 직접 적기(표를 놓친 것이 문제였으니 같은 누락이 반복된다).
- 용어표에 더한 줄은 이미 머지된 단위의 재실행을 깨뜨릴 수 있다(검사는 지금의 terms.md 를 옛 base 원문에 댄다) — 표에 줄을 더하는 단위가 머지된 단위 설정을 다시 돌려 확인한다. 기각: 단위마다 terms 판을 고정(표 고침이 앞 단위에 닿지 않는다).
- jira-task 번역은 철회(사용자 2026-10-27 "jira 관련 스킬 건들지마") — 번역·대조 파일(manifest·locations·설정)을 지우고, terms.md 의 jira-task 원문 유지 줄도 넣지 않는다. intent `# Out of scope` 에 jira-task·jira-worklog 제외를 적는다. 이 단위에서 낸 jira-task 관련 결정(Jira 본문 언어 등)은 적용하지 않는다.
- 커밋 단위: 1개 — `docs(plan): add a term check to the shared translation check`(모두 plans 의 기록 파일).
- 테스트: plans 의 기록 파일이라 repo 테스트에 넣지 않는다(앞 단위들과 같다) — 머지된 네 단위 재검증과 음성 시험이 증거.
- 롤백: 이 커밋을 `git revert <sha>` — 뒤 단위 설정이 용어 대조에 기대면 그 단위들을 다시 돌린다.

# Blockers
