---
title: language-policy — 사용자에게는 한국어, 내부는 영어라는 언어 정책을 규칙으로 적기
status: done
started: 2026-10-26
updated: 2026-10-26
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
사용자 결정(2026-10-20)인 언어 정책을 CLAUDE.md §0 에 적고, 그와 어긋나는 agents 의 "응답 언어 — 한국어" 와 Codex 프롬프트의 "응답: 한국어" 를 바꾼다. 문서 자체의 번역은 하지 않는다.
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md)
- Constraints(델타): 고치는 곳은 `CLAUDE.md` §0 첫 줄, `agents/{plan,code,architecture}-reviewer.md` 의 "응답 언어" 줄과 Codex 프롬프트 줄, `agents/researcher.md` 의 "응답 언어" 줄. 번역 전 문서는 한국어 그대로 두고 새로 더하는 문구도 그 파일 언어를 따른다(intent Constraints — 섞인 언어 방지).
- Out of scope(델타): 문서 번역(translate-* 단위) · 공용 wiki `docs/codex-review.md` 의 "응답: 한국어"(main 세션 — plan log Deferred) · README·코드 주석.
- Split: bundle → plans/2026-10-21-ops-docs-rework/intent.md

# Tasks
- [x] 범위 확인 (2026-10-26) — 사용자 "남은거 진행해", 묶음의 다음 단위
- [x] 수정 (2026-10-26): `README.md` CLAUDE.md 요약 §0, `CLAUDE.md` §0, `agents/plan-reviewer.md`, `agents/code-reviewer.md`, `agents/architecture-reviewer.md`, `agents/researcher.md`
- [x] 계획 리뷰 (2026-10-26) — 생략: small(5개 파일·약 10줄), 사용자 문구 확인이 검증
- [x] code-reviewer·simplify (2026-10-26) — 생략: 코드 변경 없음
- [x] 사용자에게 바뀐 문구 확인받고 커밋 (2026-10-26) — 사용자 "커밋하고 /e merge"(plan log·intent 를 한국어 쪽에 둔 추론도 함께 확인)
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 (2026-10-26) — 격리 runner: agents 의 한국어 보고 줄 0건, `ALL PASS`. 판정 DONE
- [x] (2026-10-26) intent 의 Open question "language-policy 단위를 넣을 시점" 을 (해소)로, `# Plans` 줄 치환
- [x] 기록 커밋, commit-check (2026-10-26)
- [x] 머지 (`/e merge`) (2026-10-26) — PR #242
- [ ] [post-merge] main 세션에서 공용 wiki `docs/codex-review.md` 의 "응답: 한국어" 를 정책에 맞게(plan log Deferred)

# Acceptance
1. §0 에 정책이 있다 — 사용자 답·plan 파일은 한국어, 그 밖의 내부는 영어, subagent·Codex 결과는 메인이 한국어로 전한다, 번역 전 문서는 그 언어 그대로 — diff 대조와 사용자 문구 확인
2. agents 에 "한국어" 로 보고하라는 줄이 없다 — `rg -n '응답: 한국어|^- 한국어\.' agents/` — 0건
3. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)

# Decisions
- 정책 문구(사용자, 2026-10-20 "나와 소통할때만 한국어 … 생각하는 과정이나 내부적으로 진행되는 것들은 모두 영어"): 한국어 = 사용자에게 하는 답, `plans/` 의 파일. 영어 = 생각, subagent 지시·보고, Codex 프롬프트·응답, 운영 문서(번역된 뒤부터). plan log·`intent.md` 를 "plan 파일" 에 넣은 것은 메인의 추론이었고, 문구 확인 때 사용자가 그대로 승인했다(2026-10-26). 이것으로 intent Open question 의 그 부분이 정해진다.
- 번역 전 문서: 운영 문서가 아직 한국어라 "운영 문서는 영어" 를 지금 적용하면 한 파일 안에 언어가 섞인다. 번역 단위가 그 파일을 옮긴 뒤부터 영어로 고친다.
- agents 의 보고 언어: 영어로 바꾼다. 메인이 사용자에게 한국어로 전한다. 기각: agents 를 한국어로 두기(사용자 결정과 다르고, 이미 영어 보고를 요청하고 있다 — intent Constraints 의 "의도된 예외" 를 이 단위가 해소한다).
- 커밋 단위: 1개 — `docs(claude-md): write down the language policy`. plan·intent 는 기록 커밋.
- 롤백: `git revert -m 1 <merge sha>`.

# Blockers
