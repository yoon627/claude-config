---
title: translate-agent-arch-reviewer — agents/architecture-reviewer 를 규칙 손실 없이 영어로 옮긴다
status: done
started: 2026-10-27
updated: 2026-10-27
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
`agents/architecture-reviewer.md`(frontmatter description 포함, 172줄)를 영어로 옮긴다. 책임 경계·두 모드·호출 트리거(자동·수동·금지)·입력 최소 번들 1~6·검토 시작 절차 0~4·검토 관점 1~8·비-목표·금지 사항·심각도·출력 형식은 빠지거나 약해지거나 강해지지 않는다(사용자, 2026-10-27 "architecture-reviewer 번역").
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-repo 단위의 여덟 번째. `plans/2026-10-21-ops-docs-rework/terms.md` 와 공통 대조 검사(`check-translation.js`·`mut-translation.js`)를 쓴다.
- Constraints(델타): 메인이 프롬프트 첫 줄에 넣는 입력 토큰 `mode: planning`·`mode: post-implementation` 은 그대로(사용자·메인 입력). `## Codex 병행` 접두 제목 두 개는 그대로(sync 스크립트, terms.md). 판정값 `APPROVE | REQUEST CHANGES | NEEDS DISCUSSION`·심각도 `Critical`·`Major`·`Minor`·번호(입력 번들 1~6·검토 시작 0~4·검토 관점 1~8)는 그대로. Codex 프롬프트는 §0 대로 영어로, 분류 지시(Critical / Major / Minor)와 항목 필드는 출력 템플릿의 영어 필드명과 같게. 공통 절 제목·출력 절 이름은 terms.md 대로. 사용자 지시(2026-10-26): 추천안대로 끝까지 진행.
- Out of scope(델타): 규칙 내용 변경(결함은 plan log Deferred) · `scripts/bootstrap/test_sync_codex_agents.py` 의 `REMOVED`("도메인 특화 프롬프트" 는 이 파일에 없고 code-reviewer 에 남는다 — code-reviewer 단위가 고친다) · dlc 의 "arch planning"·"arch(정밀)" 같은 개념 참조(dlc 번역 단위).
- Split: none — 대상 파일 하나이고 번역과 그 대조가 한 머지에서만 맞는다. 이 파일의 문구를 글자로 인용하는 다른 파일이 없다.

# Tasks
- [x] 범위 확인 (2026-10-27) — 사용자 "architecture-reviewer 번역 (추천)", 가리키는 곳 조사(dlc·CLAUDE.md·README·공용 wiki 는 이름·개념 참조만)
- [x] 대조 기준 (2026-10-27) — `plans/2026-10-27-translate-agent-arch-reviewer/manifest.md`(조항 76개, 번역 초안 전에 작성)
- [x] 번역 (2026-10-27) — `agents/architecture-reviewer.md` 172줄, 줄 구조 유지
- [x] 위치·설정·변형 시험 (2026-10-27) — `plans/2026-10-27-translate-agent-arch-reviewer/locations-en.txt`, `plans/2026-10-27-translate-agent-arch-reviewer/check.json`, `plans/2026-10-21-ops-docs-rework/terms.md` 줄 추가, 공통 검사 `plans/2026-10-21-ops-docs-rework/check-translation.js`·`mut-translation.js` 에 인용 줄바꿈 표지 `⏎`(Major·Minor 아래 같은 줄 두 개를 제목과 함께 인용) — 공통 검사 PASS(조항 76·핵심 문구 27), 변형 R 21/21·G 전부(swap 92·edge 210·blank 152·indent 18·fence 4·del 177), sync 잔존 0, 머지된 세 단위 재검증 PASS
- [x] 리뷰 4개 병렬 (2026-10-27) — 게이트 대조 OK 73·WEAKER 2·CHANGED 1, 조항 대조 OK 73·WEAKER 3, code-reviewer APPROVE, 계획 리뷰 CONDITIONAL — 처분은 `plans/2026-10-27-translate-agent-arch-reviewer/translate-agent-arch-reviewer-log.md`
- [x] 리뷰 반영 (2026-10-27) — `agents/architecture-reviewer.md` "Review checklist"(terms.md 대로)·호출 금지 한 줄만 출력·호출 측 범위 우선·검토 관점 8 "branches"·R.3·호출 측 주어·"Found only by this review", 머지된 `agents/plan-reviewer.md` 의 같은 필드와 그 `plans/2026-10-27-translate-agent-plan-reviewer/locations-en.txt`, `plans/2026-10-21-ops-docs-rework/mut-translation.js` CRLF·못 찾은 인용을 실패로, terms.md 두 줄 고침
- [x] simplify 점검 (2026-10-27) — 생략: 제품 코드 변경 없음
- [x] 사용자 diff 확인 (2026-10-27) — 사용자 "커밋": mode 토큰·Codex 제목 원문 유지, "Review checklist", plan-reviewer "Found only by this review" 함께, 공통 검사 ⏎·CRLF, Acceptance 4 문구 포함
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-27) — `ALL PASS`, 공통 검사 PASS(arch·plan-reviewer), 변형 R 25/25·G 전부, sync 테스트 11 OK, Acceptance 1~4·6 관찰
- [x] 기록 커밋(plan·log·manifest·locations·check.json·terms·intent·공통 검사), commit-check (2026-10-27)
- [x] 머지 (`/e merge`) (2026-10-27) — PR #250
- [ ] [post-merge] 새 세션에서 관찰 — 설계 질문("이거 메서드로 빼야 하나", "주입해야 하나")에 architecture-reviewer 가 골라지는지
- [ ] [post-merge] main 세션에서 공용 wiki 확인 — architecture-reviewer 문구 인용 확인, ops-doc-slimming·log 기록
- [ ] [post-merge] Codex 가 있는 머신에서 `scripts/bootstrap/sync_codex_agents.py` 재실행

# Acceptance
1. 규칙 손실 0 — `node plans/2026-10-21-ops-docs-rework/check-translation.js <root> plans/2026-10-27-translate-agent-arch-reviewer/check.json` 이 PASS(인용 글자 그대로·한 번·manifest 순서, 인용 밖은 공백과 줄 머리 목록 표시만, 줄 모양·들여쓰기·단어 없는 줄·코드 펜스가 원문과 같다), 그리고 `node plans/2026-10-21-ops-docs-rework/mut-translation.js <root> <check.json> <scratch>` 가 원본 PASS 를 확인한 뒤 규칙 변형(R)·생성 변형(G) 전부 FAIL, 종료 코드 0. 뜻이 원문과 같다는 근거는 이 검사가 아니라 5(독립 대조)와 사용자 diff 확인이다
2. 식별자·입력 토큰·판정값은 그대로 — manifest 핵심 문구가 backtick 째로 — 공통 검사 2절 — 전부 찾음
3. 한국어는 원문 유지 문자열(`## Codex 병행`) 안에만 — 공통 검사 3절 — 0
4. 표지 — 줄 수, frontmatter(`name`·`tools`·`model` 불변), 제목 줄 목록 정확 일치, 번호 블록(호출 트리거 1~3·입력 번들 1~6·검토 시작 0~4·검토 관점 1~8), description 평문에 `: ` 없음, sync 스크립트가 Codex 절을 뗀다 — 공통 검사 4절 + `node scripts/frontmatter-lint.js agents/architecture-reviewer.md` + `python3 -m unittest scripts/bootstrap/test_sync_codex_agents.py` + sync 실행에서 Codex 절 잔존 0 — 누락 0
5. 독립 대조 — 게이트 줄 전담 1개 + 조항별(manifest 감사 포함) 1개 — OK 아닌 판정마다 반영하거나 반박해 plan log 에 — 미처분 0
6. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
7. [post-merge] 공용 wiki — architecture-reviewer 문구 인용 확인·기록
8. [post-merge] 관찰 — 새 세션에서 설계 질문에 architecture-reviewer 가 골라진다

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다. terms.md 와 공통 대조 검사를 쓴다.
- 입력 토큰 `mode: planning`·`mode: post-implementation` 은 그대로 — 이 agent 가 스스로 정한 입력 계약이고 호출 측이 이 글자로 쓴다(terms.md). dlc 본문에는 이 글자가 없다(계획 리뷰가 바로잡음 — 처음 근거 "dlc 4·11단계가 쓴다" 는 틀렸다, Deferred). 기각: 번역(호출 측과 agent 가 다른 글자를 쓰게 된다).
- "검토 관점" → "Review checklist"(terms.md 대로, 절 제목·M.4·S.4·Codex 프롬프트) — 처음에 "Review angles" 로 옮겨 용어표를 어겼다(계획 리뷰·code-reviewer). code-reviewer 의 개별 관점을 가리키는 "성능 관점"·"테스트 관점" 은 "performance item"·"test item".
- ⚠️ Codex 템플릿 필드 "메인만 잡은 것" → "Found only by this review", 머지된 plan-reviewer 도 같은 머지에서 고친다 — "메인" 은 Codex 와 견준 리뷰어 자신의 검토인데("자체 검토", codex-review.md) "the main agent" 는 이 파일에서 상위 세션을 뜻해 발견 주체를 잘못 가리킨다(두 독립 대조) — 별도 작업으로 미루는 안도 있었다 — 같은 용어표 줄을 고치는 일이고 한 줄이라 함께 고쳤다(terms.md 줄 고침 이유는 여기). plan-reviewer 의 기록(`locations-en.txt`)도 같은 문구로 맞췄다.
- Codex 프롬프트를 영어로 — 분류 지시 "Critical / Major / Minor" 와 공통 추출(`~/.claude/wiki/docs/codex-review.md` §5 의 `Critical|Major|Minor` grep)은 그대로 맞는다. 항목 형식 필드는 출력 템플릿의 영어 필드명과 같게 옮긴다.
- 공통 검사에 인용 줄바꿈 표지 `⏎` 를 더했다 — Major·Minor 아래의 같은 줄 "(same format as Critical)" 이 원문에서도 두 번이라 한 줄만으로는 한 번 나오는 인용이 될 수 없다. 기각: 두 줄을 다르게 옮기기(원문에 없는 차이를 만든다), `\n` 표지(commit-check 예시 JSON 에 글자 `\n` 이 있다). 머지된 세 단위를 바뀐 검사로 다시 돌려 PASS.
- 출력 값 "없음"(템플릿의 "없으면 \"없음\"") 은 agent 가 영어로 쓰는 출력이라 "none" — plan 파일 표지 `없음` 과 다르다.
- 가장 위험한 곳: 호출 금지(즉시 종료) 조건과 모드 기본값 — 잘못 옮기면 agent 가 불필요한 검토를 하거나 해야 할 검토를 건너뛴다. 게이트 대조가 따로 본다. Codex 절은 sync 가 떼므로 런타임 위험이 작다.
- description 을 영어로 옮겼다(앞 단위들과 같다) — 머지 뒤 Acceptance 8 로 선택을 확인한다. 기각: 한국어 description 유지(한 파일에 언어가 섞인다).
- README 는 바꾸지 않는다(동작 불변, README 는 §0 밖).
- 커밋 단위: 1개 — `docs(architecture-reviewer): translate agents/architecture-reviewer into English`. plan·log·대조 파일·terms·intent 는 기록 커밋.
- 테스트: 문서라 새 테스트 없음(§7 예외 — 수동 검증은 Acceptance 1~5). 사용자 diff 확인이 행동 검증.
- Codex 미가용. architecture-reviewer 를 그 자신의 번역 검토에 부르지 않는다(문서만).
- Acceptance 4 문구를 고쳤다(계획 리뷰) — "번호 블록(입력 번들 1~6·검토 관점 1~8·호출 트리거 1~3)" → "(호출 트리거 1~3·입력 번들 1~6·검토 시작 0~4·검토 관점 1~8)" — 설정이 이미 검사하던 블록을 적은 것이라 기준은 그대로, 사용자 승인은 diff 확인에서.
- 커밋 단위: 1개 유지 — plan-reviewer 의 한 줄 수정은 같은 용어 결정의 일부라 이 번역 커밋에 함께 넣는다(커밋 메시지에 적는다).
- 롤백: `docs(architecture-reviewer)` 커밋만 `git revert <sha>`, 되돌린 뒤 Codex 머신에서 sync 재실행.

# Blockers
