---
title: translate-skill-commit-check — skills/commit-check 를 규칙 손실 없이 영어로 옮긴다
status: done
started: 2026-10-27
updated: 2026-10-27
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
`skills/commit-check/SKILL.md`(frontmatter description 포함, 75줄)를 영어로 옮긴다. 규칙은 빠지거나 약해지거나 강해지지 않고, 절차 번호 1~7·JSON 키·flag·status 이름은 그대로다.
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-repo 단위의 다섯 번째. 방법은 `plans/2026-10-27-translate-skill-wt/` 와 같다(번역 전 manifest, 조항 전체를 덮는 위치 인용(파일 안에서 한 번), 덮이지 않은 구간 검사, 손으로 고른 변형 + 문장 삭제 sweep).
- Constraints(델타): 스크립트 출력과 글자로 맞아야 하는 `merge-tree --write-tree 실패`(`skills/commit-check/commit_units.py` 의 `Git.run` 오류 문구 일부)는 원문 그대로. JSON 키·flag(`wip`·`fixup`·`review-followup`·`plan-only`·`empty`)·status(`rewritable`·`published`·`held`·`blocked`)는 원래 영어라 핵심 문구로 지킨다. e 가 "that SKILL's `/e merge` section" 으로 가리키므로 절 제목에 `/e merge` 를 남긴다. 사용자 지시(2026-10-26): 추천안대로 끝까지 진행.
- Out of scope(델타): 규칙 내용 변경(찾은 결함은 plan log Deferred) · `commit_units.py`·테스트 등 코드(오류 문구가 한국어인 것 포함) · README.
- Split: none — 대상이 파일 하나이고, 번역과 그것을 확인하는 대조가 한 머지에서만 맞는다. 저장소 안에서 이 skill 의 문구를 글자로 인용하는 곳이 없다(e 의 절 포인터는 제목에 `/e merge` 를 남겨 맞춘다).

# Tasks
- [x] 범위 확인 (2026-10-27) — 사용자 "다음 skill 번역 (추천)", read-points 가 다루는 `agents/code-reviewer.md`·`skills/dlc/SKILL.md` 는 피해 commit-check 를 골랐다
- [x] 대조 기준 (2026-10-27) — `plans/2026-10-27-translate-skill-commit-check/manifest.md`(조항 55개, 번역 초안 전에 작성), `plans/2026-10-27-translate-skill-commit-check/check-cc.js`, `plans/2026-10-27-translate-skill-commit-check/mut-cc.js`
- [x] 번역 (2026-10-27) — `skills/commit-check/SKILL.md` 75줄, 줄 구조 유지
- [x] 새 위치·기계 대조·변형 시험 (2026-10-27) — `plans/2026-10-27-translate-skill-commit-check/locations-en.txt`, check-cc PASS, 변형 A·문장 삭제 sweep 전부 FAIL(scratch `mut-cc.js`) — 조항 55·핵심 문구 46·덮이지 않은 구간 0, 변형 A 23/23·문장 삭제 83/83
- [x] 리뷰 4개 병렬 (2026-10-27) — 게이트 대조 OK 72, 조항 대조 OK 55, code-reviewer APPROVE, 계획 리뷰 CONDITIONAL — 처분은 `plans/2026-10-27-translate-skill-commit-check/translate-skill-commit-check-log.md`
- [x] 리뷰 반영 (2026-10-27) — `skills/commit-check/SKILL.md` 보류 → "leave unapplied"·문구 다듬기, check-cc 5절 인용 밖 글자 0·4절 H1·frontmatter·2절 backtick, 변형 A 24/24·B 8/8·문장 삭제 113/113
- [x] simplify 점검 (2026-10-27) — 생략: 코드 변경 없음(check-cc·mut-cc 는 대조용 기록 파일)
- [x] 사용자 diff 확인 (2026-10-27) — 사용자 "커밋": 보류 → "leave unapplied"·요청 예시 영어화·스크립트 오류 문구 유지·Acceptance 문구 강화 포함
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-27) — `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 미설치, 무관), check-cc PASS, 변형 24/24·8/8·113/113, Acceptance 1~4·6 관찰
- [x] 기록 커밋(plan·log·manifest·locations·check-cc·mut-cc·intent), commit-check (2026-10-27)
- [x] 머지 (`/e merge`) (2026-10-27) — PR #247
- [ ] [post-merge] 새 세션에서 관찰 — 한국어 요청("커밋 정리해줘")에 맞는 skill 로 commit-check 가 골라지는지
- [ ] [post-merge] main 세션에서 공용 wiki 확인 — commit-check 문구를 인용한 곳이 있으면 영어로(지금 조사로는 이름·경로 참조만), ops-doc-slimming·log 기록

# Acceptance
1. 규칙 손실 0 — manifest 조항마다 locations-en.txt 의 영어 인용(조항 전체를 덮는 하나 이상, 파일 안에서 한 번)이 글자 그대로, 인용 밖에 글자가 없고(제목·frontmatter 틀·`description: ` 키·코드 펜스 제외), 변형을 넣으면 잡힌다 — `check-cc.js` 1·4·5절 + `node plans/2026-10-27-translate-skill-commit-check/mut-cc.js <root> <scratch 파일>`(규칙 변형·경계 삽입·H1·모든 문장 삭제) — missing·not found·uncovered 0, 변형 전부 FAIL. 뜻이 원문과 같다는 근거는 이 검사가 아니라 5(독립 대조)와 사용자 diff 확인이다
2. 식별자·명령·글자로 맞추는 출력은 그대로 — manifest 핵심 문구가 backtick 째로 파일에 글자 그대로 — `check-cc.js` 2절 — 전부 찾음
3. 한국어 없음 — 원문 그대로 둔 문자열(`merge-tree --write-tree 실패`) 밖 한글 0 — `check-cc.js` 3절 — 0
4. 표지 — 줄 수가 원문과 같음, H1·절 제목과 절차 1~7, frontmatter 키, `/e merge` 절 제목, description 평문에 `: ` 없음 — `check-cc.js` 4절 + `node scripts/frontmatter-lint.js skills/commit-check/SKILL.md` — 누락 0
5. 독립 대조 — 게이트 줄 전담 1개 + 조항별(manifest 감사 포함) 1개 — OK 아닌 판정마다 반영하거나 반박해 plan log 에 — 미처분 0
6. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
7. [post-merge] 공용 wiki — commit-check 문구 인용 확인·기록
8. [post-merge] 관찰 — 새 세션에서 한국어 커밋 정리 요청에 맞는 skill 로 commit-check 가 골라진다 — 아니면 description 예시를 되돌리는 안을 제안

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다. 앞 번역 단위(translate-skill-wt)의 방법과 묶음 Constraints 를 그대로 쓴다. [[commit-restructure-plumbing-cas]] 는 재구성 방식 결정이라 번역으로 바뀌지 않는다.
- 원문 그대로 둔 문자열: `merge-tree --write-tree 실패` — `commit_units.py` 가 git 실패를 `git merge-tree --write-tree 실패(exit N): …` 로 내고, 이 skill 은 그 문구로 충돌 거부를 알아본다(옮기면 reword 재시도 분기를 놓친다). 기각: 영어로 옮기기(스크립트 출력은 한국어 그대로라 글자가 안 맞는다).
- 보류 → "leave unapplied"(파일 전체) — "hold" 는 같은 절의 상태값 `held`(다른 로컬 ref 가 붙잡은 커밋)와 같은 말이라 "/e 가 held 커밋을 처리한다" 로 읽힐 수 있다. e M3 의 "leaving its plan unapplied" 와 같은 말(translate-skill-e 의 같은 지적). 기각: "hold"(계획 리뷰 S1).
- description 의 사용자 요청 예시("커밋 정리해줘 / 커밋 나눠줘 / 이 커밋 합쳐줘")를 영어로 옮겼다 — c·e·wt 와 같고, 머지 뒤 한국어 요청으로 skill 이 골라지는지 Acceptance 8 로 확인한다. 기각: 한국어 예시 유지(한 파일에 언어가 섞이고, 앞 단위들에서 영어 예시로도 한국어 요청이 골라졌다).
- 가장 위험한 곳: description(skill 선택 — Acceptance 8)과 `/e merge` 절의 충돌 → reword 한 번 재적용 규칙(잘못 읽으면 `/e merge` 가 같은 자리에서 멈춘다 — 게이트 대조가 따로 봤다).
- Acceptance 1·2·4 문구를 바꿨다(계획 리뷰 S2·code-reviewer) — 1 "인용 밖에 규칙 문장이 없고 … 1절·5절 + 변형 시험(손으로 고른 변형과 모든 문장 삭제)" → "인용 밖에 글자가 없고 … 1·4·5절 + mut-cc.js(규칙 변형·경계 삽입·H1·모든 문장 삭제), 뜻이 같다는 근거는 5 와 사용자 diff 확인", 2 "글자 그대로" → "backtick 째로 글자 그대로", 4 "절 제목" → "H1·절 제목 … frontmatter 키" — 검사를 넓히는 쪽이라 통과 기준은 약해지지 않는다, 사용자 승인은 diff 확인에서.
- 모델이 보고에 쓰는 문구("점검할 미게시 커밋 없음"·"이상 없음"·"수동 분할 필요"·"대상 미확인/범위 밖"·"충돌 시 reword"·표 머리)는 영어로 — CLAUDE.md §0 에 따라 사용자 답에서는 한국어로 쓴다. 스크립트가 읽지 않는다.
- 계획 JSON 예시의 한국어 커밋 메시지("feat: 새 제목" 등)는 영어 예시로 — 이 repo 의 커밋 관례가 영어다.
- 절 제목 `## \`/e merge\` 에서 부를 때` → `/e merge` 를 그대로 담은 영어 제목 — e 3단계 "that SKILL's `/e merge` section" 이 이 제목을 가리킨다.
- README 는 바꾸지 않는다(동작 불변, README 는 §0 밖) — `dlc-doc-drift` 경고는 예상된 오탐.
- 커밋 단위: 1개 — `docs(commit-check): translate skills/commit-check into English`. plan·log·대조 파일은 기록 커밋.
- 테스트: 문서라 새 테스트 없음(§7 예외 — 수동 검증은 Acceptance 1~5). 사용자 diff 확인이 행동 검증.
- Codex 미가용. architecture-reviewer 는 부르지 않는다(문서만).
- 롤백: `git revert -m 1 <merge sha>`.

# Blockers
