---
title: translate-skill-dlc — skills/dlc 를 규칙 손실 없이 영어로 옮긴다
status: done
started: 2026-10-31
updated: 2026-10-31
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
`skills/dlc/SKILL.md`(frontmatter description 포함, 173줄)를 영어로 옮긴다. 진입 매트릭스·규모 gate·요구사항 명확화·분할 판정·self-flag·evidence gate·판정·no-progress·커밋 단위·파이프라인·격리 경계·codex owner·fix loop·자기 진단·Report 규칙은 빠지거나 약해지거나 강해지지 않는다(사용자 2026-10-31 "물어보지 말고 이번 세션 작업 모두 마무리해서 main 반영").
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-repo 의 마지막 문서 단위. terms.md 와 공통 대조 검사를 쓴다.
- Constraints(델타): plan 파일에 한국어로 남는 표지(`⚠️ (구현)`·`[리뷰 미경유]`·`[plan 대비]`·`커밋 단위:`·`없음 — <…>`·`none — purpose-commit bundle: …` 등)와 hook·스크립트가 찍는 글자는 원문. 다른 파일(CLAUDE.md·README·hooks·skills·공용 wiki)이 가리키는 절 이름·단계 번호는 유지하거나, 바꾸면 같은 머지에서 포인터를 고친다(공용 wiki 는 main 세션).
- Out of scope(델타): hook 이 주입하는 문구(translate-hooks) · 공용 wiki `docs/dlc-details.md`(translate-wiki-docs).
- Split: none — 번역과 그 포인터, 옛 이름 "plan 반영용 요약" 정리는 같은 머지에서만 맞는다.

# Tasks
- [x] 대조 기준 — `plans/2026-10-31-translate-skill-dlc/manifest.md`(번역 초안 전) (2026-10-31) — 358조항, 핵심 문구 157
- [x] 번역 — `skills/dlc/SKILL.md`, 줄 구조 유지 (2026-10-31) — 173줄, 단계 번호 0~16 유지
- [x] 옛 이름 "plan 반영용 요약" 정리 — 영어본에 "Summary for the plan" 만 (2026-10-31) — `plans/2026-10-31-translate-skill-dlc/check-dlc.js` 가 확인
- [x] 위치·설정·변형 시험 — `plans/2026-10-31-translate-skill-dlc/locations-en.txt`·`check.json` (2026-10-31) — 공통 검사 PASS, 변형 R 40/40·G 전부
- [x] 포인터 — `agents/code-reviewer.md`(Report "Where to read"), `README.md`(334·335 인용, 282·316 "Split judgment"), 나머지는 `plans/2026-10-31-translate-skill-dlc/pointers.md` 와 log Deferred (2026-10-31)
- [x] 리뷰 — 게이트 줄 전담·조항별 대조·code-reviewer(Codex 미가용), 처분은 `plans/2026-10-31-translate-skill-dlc/translate-skill-dlc-log.md` (2026-10-31) — 지적 9건 fix, code-reviewer APPROVE
- [x] plan-reviewer 14항 소급 면제를 dlc 45행과 맞춤 — `agents/plan-reviewer.md` (2026-10-31) — code-reviewer APPROVE(면제를 좁힌다)
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 (2026-10-31)
- [x] 기록 커밋, ff-merge(translate-agent-code-reviewer 다음) (2026-10-31)
- [ ] [post-merge] 새 세션에서 비자명한 변경 요청에 dlc 가 골라지는지 관찰 (Acceptance 6)

# Acceptance
1. 규칙 손실 0 — `node plans/2026-10-21-ops-docs-rework/check-translation.js <root> plans/2026-10-31-translate-skill-dlc/check.json` PASS, `node plans/2026-10-21-ops-docs-rework/mut-translation.js <root> <check.json> <scratch>` 가 원본 PASS 뒤 변형(R·G) 전부 FAIL, 종료 코드 0
2. 독립 대조(게이트 줄 전담 1개 + 조항별 1개)의 OK 아닌 판정을 모두 반영하거나 반박해 plan log 에 — 미처분 0
3. 포인터 — 바뀐 절 이름·라벨과 유지한 표지를 `rg` 로 repo 에서 찾아 걸린 곳마다 처분, hook 테스트(`node scripts/dlc-early-stop.test.js` 등 dlc 문구를 읽는 테스트) 통과
4. `node scripts/frontmatter-lint.js skills/dlc/SKILL.md` 통과
5. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
6. [post-merge] 새 세션에서 비자명한 변경 요청에 dlc 가 골라지는지 관찰

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다. terms.md 와 공통 대조 검사를 쓴다.
- read-points worktree(다른 세션, plan 만 있고 구현 없음, 2026-10-15 이후 정지)가 이 파일을 고칠 계획이지만 막지 않는다 — 이유는 translate-agent-code-reviewer plan 과 같다.
- 커밋 단위: 1) `docs(dlc): translate skills/dlc into English` — `skills/dlc/SKILL.md`·포인터(`agents/code-reviewer.md`·README) 2) `fix(plan-reviewer): exempt only pre-rule plans from the labeled-bullet check` — `agents/plan-reviewer.md`(리뷰에서 나온 같은 규칙의 어긋남, 목적이 달라 따로). plan·log·대조 파일은 기록 커밋.
- 테스트: 문서 번역이라 새 테스트 없음(§7 예외 — 수동 검증은 Acceptance 1~4).
- 문구 검증: CLAUDE.md §8 위임 예외 — dlc 의 evidence gate·fix loop 를 빼거나 약하게 하면 예외 밖이다. 번역은 규칙을 바꾸지 않는 것이 목표이고 Acceptance 1·2 로 확인하며, code-reviewer 에게 완화 여부를 명시적으로 묻는다.
- 옛 이름 정리: 원문 격리 경계 절은 agent 출력 절을 "plan 반영용 요약"(영어로 옮긴 agent 는 "Summary for the plan") 두 이름으로 적었다. agent 4개가 모두 영어가 된 뒤(translate-agent-code-reviewer 가 먼저 머지)라 영어본은 "Summary for the plan" 만 남긴다(terms.md 임시 문자열 줄의 조건). 기각: 두 이름 유지(영어 문서에 한글이 남는다).
- 사용자용 Report 라벨(`## 읽을 곳`·`확인 필요:`·`미충족`/`미검증`·"미식별")은 영어로(`## Where to read`·`Needs confirmation:`·unmet/unverified·"not identified") — 스크립트가 읽지 않고 CLAUDE.md §0 이 문서 라벨은 영어로 정한다. 같은 머지에서 `agents/code-reviewer.md`·README 인용을 맞췄다. plan 파일에 한국어로 남는 표지는 원문. 기각: `## 읽을 곳` 원문 유지(§0 과 어긋난다).
- 원문자 ①②③ → `1)`·`2)`·`3)`(CLAUDE.md §0). 가리키는 곳 없음.
- "검증 칸"·"검증 명령 미식별" 은 code-reviewer 단위가 terms.md 에 정한 "verification field"·"verification command not identified" 를 쓴다(조항별 리뷰).
- 롤백: 번역 커밋만 `git revert <sha>`.

# Blockers
