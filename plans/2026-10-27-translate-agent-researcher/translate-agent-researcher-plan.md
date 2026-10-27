---
title: translate-agent-researcher — agents/researcher 를 규칙 손실 없이 영어로 옮기고 묶음 공통 용어표를 만든다
status: in_progress
started: 2026-10-27
updated: 2026-10-27
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
`agents/researcher.md`(frontmatter description 포함, 63줄)를 영어로 옮긴다. 규칙·출처 우선순위 1~4·출력 형식의 절 구성은 빠지거나 약해지거나 강해지지 않는다. 같은 머지에서 묶음 공통 용어표 `plans/2026-10-21-ops-docs-rework/terms.md` 를 만들고 intent Constraints 에 "착수 때 읽고, 새로 정한 것은 더한다" 를 넣는다(사용자, 2026-10-27 "용어표 넣고 다음 번역").
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-repo 단위의 여섯 번째. 방법은 `plans/2026-10-27-translate-skill-commit-check/` 와 같다(번역 전 manifest, 인용은 조항 전체·파일 안에서 한 번, 인용 밖 글자 0, 규칙 변형·경계 삽입·H1·문장 삭제 변형 시험).
- Constraints(델타): 출력 절 "plan 반영용 요약" 은 `skills/dlc/SKILL.md` 격리 경계 절이 이름으로 가리키고 다른 agent 3개도 같은 제목을 쓴다 — 이 단위에서 "Summary for the plan" 으로 옮기고, dlc 의 그 줄은 같은 머지에서 두 이름을 함께 적는다(agent 4개가 다 옮겨지면 마지막 단위가 한국어 이름을 지운다 — terms.md). 확신도 라벨은 CLAUDE.md §1 의 ✅certain / ⚠️inferred / ❌unknown. frontmatter `name`·`tools`·`model` 은 그대로. 사용자 지시(2026-10-26): 추천안대로 끝까지 진행.
- Out of scope(델타): researcher 의 규칙 내용 변경(결함은 plan log Deferred) · dlc 의 다른 문장(dlc 번역 단위의 일, 다른 세션 read-points 가 dlc 를 다룬다) · README 의 agent 설명.
- Split: none — researcher 번역과 dlc 포인터는 한 머지에서만 서로 맞다. 용어표·intent 줄은 혼자 머지될 수 있지만 그 표의 한 줄(출력 절 이름)이 이 단위의 결정이라, 나누면 머지 고정비만 늘어난다(⚠️ 계획 리뷰가 "느슨하다" 고 본 부분 — 롤백은 docs 커밋만 되돌려 용어표를 남긴다, Decisions).

# Tasks
- [x] 범위 확인 (2026-10-27) — 사용자 "용어표 넣고 다음 번역 (추천)", 가장 작은 남은 대상 researcher(63줄)
- [x] 공통 용어표 (2026-10-27) — `plans/2026-10-21-ops-docs-rework/terms.md`, `plans/2026-10-21-ops-docs-rework/intent.md` Constraints·Plans 줄
- [x] 대조 기준 (2026-10-27) — `plans/2026-10-27-translate-agent-researcher/manifest.md`(번역 초안 전에 작성), `plans/2026-10-27-translate-agent-researcher/check-rs.js`, `plans/2026-10-27-translate-agent-researcher/mut-rs.js` — 조항 26개
- [x] 번역 (2026-10-27) — `agents/researcher.md` 63줄, 줄 구조 유지 · `skills/dlc/SKILL.md` 격리 경계 절의 "plan 반영용 요약" 포인터 한 줄
- [x] 새 위치·기계 대조·변형 시험 (2026-10-27) — `plans/2026-10-27-translate-agent-researcher/locations-en.txt` — check-rs PASS(조항 26·핵심 문구 23·한글 0·인용 밖 글자 0), 변형 A 18/18·B 8/8·문장 삭제 43/43
- [x] 리뷰 4개 병렬 (2026-10-27) — 게이트 대조 OK 30·WEAKER 1, 조항 대조 OK 전부, code-reviewer APPROVE, 계획 리뷰 CONDITIONAL — 처분은 `plans/2026-10-27-translate-agent-researcher/translate-agent-researcher-log.md`
- [x] 리뷰 반영 (2026-10-27) — `agents/researcher.md` "publication date"·문장 다듬기, check-rs 인용 순서·제목 목록 일치·frontmatter 면제는 1~6행만·인용 밖은 공백과 목록 표시만, `plans/2026-10-27-translate-agent-researcher/mut-rs.js` 줄 바꿔치기·새 제목·`tools:`/`model:` 줄·기호 삽입, `plans/2026-10-21-ops-docs-rework/terms.md` 보완, manifest 가리키는 곳에 공용 wiki 2곳
- [x] simplify 점검 (2026-10-27) — 생략: 코드 변경 없음(check-rs·mut-rs 는 대조용 기록 파일)
- [x] 사용자 diff 확인 (2026-10-27) — 사용자 "커밋": 출력 절 이름 영어화·dlc 두 이름 병기·terms.md 신설·Acceptance 문구 강화 포함
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-27) — `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 미설치, 무관), check-rs PASS, 변형 S 4/4·A 18/18·B 13/13·문장 삭제 43/43, sync 테스트 11 OK, Acceptance 1~4·6 관찰
- [x] 기록 커밋(plan·log·manifest·locations·check-rs·mut-rs·terms·intent), commit-check (2026-10-27)
- [ ] 머지 (`/e merge`)
- [ ] [post-merge] 새 세션에서 관찰 — 외부 사실 질문(예: "최신 버전 릴리스 노트 확인해줘")에 맞는 agent 로 researcher 가 골라지고, 보고가 영어 절 이름으로 오는지
- [ ] [post-merge] main 세션에서 공용 wiki — `pages/concept/plan-handoff.md`(45행)·`pages/concept/hub-and-spoke-isolation.md`(13행)의 "plan 반영용 요약" 에 "Summary for the plan" 을 함께 적기, 그 밖의 researcher 문구 인용 확인, ops-doc-slimming·log 기록
- [ ] [post-merge] Codex 가 있는 머신에서 `scripts/bootstrap/sync_codex_agents.py` 재실행 — agent 파일이 바뀐 커밋이 main 에 들어오면 다시 돌린다(`scripts/bootstrap/README.md`). 이 머신에는 `~/.codex/agents` 가 없다

# Acceptance
1. 규칙 손실 0 — manifest 조항마다 locations-en.txt 의 영어 인용(조항 전체를 덮는 하나 이상, 파일 안에서 한 번, manifest 순서대로)이 글자 그대로, 인용 밖에는 공백과 목록 표시만 있고(제목·frontmatter 1~6행(description 은 키만)·코드 펜스 제외), 변형을 넣으면 잡힌다 — `check-rs.js` 1·4·5절 + `node plans/2026-10-27-translate-agent-researcher/mut-rs.js <root> <scratch 파일>`(줄 바꿔치기·규칙 변형·경계 삽입·제목·frontmatter·문장 삭제) — missing·not found·순서·uncovered 0, 변형 전부 FAIL. 뜻이 원문과 같다는 근거는 이 검사가 아니라 5(독립 대조)와 사용자 diff 확인이다
2. 식별자·도구 이름은 그대로 — manifest 핵심 문구가 backtick 째로 파일에 글자 그대로 — `check-rs.js` 2절 — 전부 찾음
3. 한국어 없음 — `agents/researcher.md` 에 한글 0 — `check-rs.js` 3절 — 0
4. 표지 — 줄 수가 원문과 같음, frontmatter `name`·`tools`·`model` 불변, 제목 줄이 정해진 목록(본문 절 7개 + 출력 절 6개, "Summary for the plan" 포함)과 정확히 같음, 출처 우선순위 1~4, description 평문에 `: ` 없음, dlc 의 포인터 줄이 두 이름을 모두 담음 — `check-rs.js` 4절 + `node scripts/frontmatter-lint.js agents/researcher.md` — 누락 0
5. 독립 대조 — 게이트 줄 전담 1개 + 조항별(manifest 감사 포함) 1개 — OK 아닌 판정마다 반영하거나 반박해 plan log 에 — 미처분 0
6. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
7. [post-merge] 공용 wiki — researcher 문구 인용 확인·기록
8. [post-merge] 관찰 — 새 세션에서 외부 사실 질문에 researcher 가 골라지고 보고 절 이름이 영어다 — 아니면 description 을 되돌리는 안을 제안

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다. 앞 단위(translate-skill-commit-check)의 방법을 그대로 쓴다.
- 공통 용어표를 이 단위에서 만든다(사용자 2026-10-27) — 묶음 폴더에 `terms.md` 한 파일, intent Constraints 에 한 줄. 기각: 각 단위 log 에만 남기기(e 의 "hold" 결정이 commit-check 로 넘어오지 않았다). 기각: intent 본문에 표를 넣기(intent 는 6절 형식이 정해져 있고 표가 커진다).
- 출력 절 "plan 반영용 요약" → "Summary for the plan", dlc 의 포인터 줄에 두 이름을 함께 — agent 4개가 같은 제목을 쓰는데 한 번에 옮길 수 없고(code-reviewer 는 read-points 가 다룬다), dlc 가 이름으로 받으므로 섞인 동안은 둘 다 적는다. 기각: researcher 만 한국어 제목 유지(한 파일에 언어가 섞인다). 기각: agent 4개를 한 단위로(파일별 단위 결정과 다르고 read-points 와 겹친다).
- 가장 위험한 곳: description(자동 선택 — Acceptance 8, 머지 뒤 관찰)과 dlc 의 포인터 줄(메인이 agent 결과를 찾는 이름). 둘 다 이 단위의 docs 커밋 하나로 되돌릴 수 있다.
- description 을 영어로 옮겼다(c·e·wt·commit-check 와 같다) — 머지 뒤 Acceptance 8 로 선택을 확인한다. 기각: 한국어 description 유지(한 파일에 언어가 섞인다).
- 작성일 → "publication date", 기준일 → "As of" — "date" 하나로 옮기면 출처의 날짜와 검색한 날짜가 섞인다(게이트 대조 WEAKER·code-reviewer).
- 용어표는 append-only(줄을 더하기만, 동시 추가 충돌은 두 줄 모두 유지) — 여러 단위가 같은 파일을 고친다. §10 의 intent 소유권 규칙은 intent.md 만 다룬다.
- Acceptance 1·4 문구를 바꿨다(계획 리뷰 S1·code-reviewer) — 1 "인용 밖에 글자가 없고(… `name`·`tools`·`model` 줄 …)" → "manifest 순서대로 … 인용 밖에는 공백과 목록 표시만(… frontmatter 1~6행 …)" + 변형 종류 명시, 4 "출력 형식의 절 7개와" → "제목 줄이 정해진 목록(본문 절 7개 + 출력 절 6개)과 정확히 같음" — 검사를 넓히는 쪽이라 통과 기준은 약해지지 않는다, 사용자 승인은 diff 확인에서.
- 확신도 라벨은 CLAUDE.md §1 과 같은 ✅certain / ⚠️inferred / ❌unknown, "결정적 근거 없음" → "no conclusive evidence".
- README 는 바꾸지 않는다(동작 불변, README 는 §0 밖).
- 커밋 단위: 1개 — `docs(researcher): translate agents/researcher into English`(researcher·dlc 포인터 한 줄). plan·log·대조 파일·terms·intent 는 기록 커밋.
- 테스트: 문서라 새 테스트 없음(§7 예외 — 수동 검증은 Acceptance 1~5). 사용자 diff 확인이 행동 검증.
- Codex 미가용. architecture-reviewer 는 부르지 않는다(문서만).
- 롤백: merge 를 되돌리지 않고 `docs(researcher)` 커밋만 `git revert <sha>` 한다(용어표·intent 줄은 다음 단위가 기대므로 남긴다). 되돌린 뒤 Codex 가 있는 머신에서 `sync_codex_agents.py` 를 다시 돌린다. researcher 와 dlc 줄은 같은 커밋이라 함께 되돌아간다.

# Blockers
