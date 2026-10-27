---
title: translate-skill-wiki — skills/wiki 를 규칙 손실 없이 영어로 옮긴다
status: in_progress
started: 2026-10-27
updated: 2026-10-27
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
`skills/wiki/SKILL.md`(frontmatter description 포함, 153줄)를 영어로 옮긴다. 두 계층 배치·공개 점검·ingest 1~10·query 1~4·lint·신선도(covers·verified_at·모드·CI 한계·알림 해소·hook 등록·Python)·경계는 빠지거나 약해지거나 강해지지 않는다(사용자, 2026-10-27 "skills/wiki 번역").
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-repo 단위. `plans/2026-10-21-ops-docs-rework/terms.md` 와 공통 대조 검사(용어 대조 포함)를 쓴다.
- Constraints(델타): 스크립트가 찍는 글자는 그대로 — `wiki_search.py` 의 `[공용]`·`L20 §결정 (L18-35): …`·`관련: → 나가는 · ← 들어오는`·`찾을 wiki 가 없다`, `check_links.py` 의 `UTF-8 아님`·`check_links: 읽기 실패`, `wiki_check.py` 의 "covers 읽기 실패"·"검사 대상 아님"·"미확인"·"작업 트리 기준 — … 미커밋 변경 N개"·"인자 오류". 첫 번째로 나올 때 괄호에 영어 뜻을 붙인다. `훅` 은 한 음절 한글 예시라 그대로. 명령·플래그·경로·config 키·정규식은 그대로. 다른 파일이 가리키는 곳 — dlc·공용 wiki 의 "query 1단계"(`## query` 1번), 공용 wiki 의 "Python" 절(`**Python**`) — 은 번호·라벨을 유지해 그대로 맞는다. 사용자 지시(2026-10-26): 추천안대로 끝까지 진행.
- Out of scope(델타): `skills/wiki/templates/wiki-check.toml` 의 한국어 주석(29줄 — 테스트가 주석 속 예시를 읽는 코드·테스트 결합이라 이 문서 단위 밖, 분류는 intent Open question) · 스크립트의 한국어 출력·docstring(코드) · jira 관련 skill.
- Split: none — 번역과 `wiki_check.py`·README 의 "SKILL.md 신선도 절" 포인터는 같은 머지에서만 맞는다(따로 머지하면 포인터가 없는 절을 가리킨다).

# Tasks
- [x] 범위 확인 (2026-10-27) — 스크립트 출력 글자 11개, 이 skill 을 가리키는 곳(dlc·공용 wiki `docs/dlc-details.md` "query 1단계", 공용 wiki "Python" 절, `wiki_check.py`·README "SKILL.md 신선도 절") 조사
- [x] 대조 기준 (2026-10-27) — `plans/2026-10-27-translate-skill-wiki/manifest.md`(조항 179개, 번역 초안 전에 작성)
- [x] 번역 (2026-10-27) — `skills/wiki/SKILL.md` 153줄, 줄 구조 유지
- [x] 포인터 (2026-10-27) — `skills/wiki/wiki_check.py`(docstring 3곳·help 문구 1곳)·`README.md` 의 "SKILL.md 신선도 절" → "SKILL.md Freshness 절" — wiki 테스트 3종 통과(135·19·35, skip 은 플랫폼 조건)
- [x] 위치·설정·변형 시험 (2026-10-27) — `plans/2026-10-27-translate-skill-wiki/locations-en.txt`, `plans/2026-10-27-translate-skill-wiki/check.json`, `plans/2026-10-21-ops-docs-rework/terms.md` 줄·기계 대조 3쌍 추가 — 공통 검사 PASS(조항 179·핵심 문구 196), 변형 R 33/33·G 전부
- [x] 리뷰 4개 병렬 (2026-10-27) — plan-reviewer, 게이트 줄 전담 대조, 조항별·manifest 감사 대조, code-reviewer(Codex 미가용), 처분은 `plans/2026-10-27-translate-skill-wiki/translate-skill-wiki-log.md` — 145줄 범위·147줄 "closed modes" 등 반영, 재검사 PASS(핵심 문구 204, 변형 R 36)
- [x] simplify 점검 (2026-10-27) — 생략: 코드 로직 변경 없음(문서 번역과 문자열 4곳), 군더더기는 리뷰 4개가 문장 단위로 봤다
- [x] 사용자 diff 확인 (2026-10-27) — "커밋 (추천)", 147줄 명확화·Acceptance 6 변경 포함
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-27) — 격리 runner: `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 미설치, 느린 테스트 2개는 변경과 무관), 공통 검사 PASS(조항 179·핵심 문구 204), 변형 전부 잡힘, wiki 테스트 3종·frontmatter-lint·plan-lint 통과, "신선도 절" 0건 — Acceptance 1~7 충족
- [ ] 기록 커밋(plan·log·manifest·locations·check.json·terms·intent), commit-check
- [ ] 머지 (`/e merge`)
- [ ] [post-merge] 새 세션에서 관찰 — `/wiki query <질문>` 명시 호출이 wiki 를 불러 `wiki_search.py` 를 실행하는지, 단순 질문에는 골라지지 않는지
- [ ] [post-merge] main 세션에서 공용 wiki 확인 — `~/.claude/wiki/WIKI.md` 61줄 "(절차는 `skills/wiki/SKILL.md` 공개 점검)" → "Public check"(같은 줄의 "CLAUDE.md §11 공개 점검" 도 함께), ops-doc-slimming·log 기록

# Acceptance
1. 규칙 손실 0 — `node plans/2026-10-21-ops-docs-rework/check-translation.js <root> plans/2026-10-27-translate-skill-wiki/check.json` 이 PASS(인용 글자 그대로·한 번·manifest 순서, 인용 밖은 공백과 줄 머리 목록 표시만, 줄 모양·들여쓰기·단어 없는 줄·코드 펜스가 원문과 같다, 용어표 대조), 그리고 `node plans/2026-10-21-ops-docs-rework/mut-translation.js <root> <check.json> <scratch>` 가 원본 PASS 를 확인한 뒤 규칙 변형(R)·생성 변형(G, 용어 포함) 전부 FAIL, 종료 코드 0. 뜻이 원문과 같다는 근거는 이 검사가 아니라 5(독립 대조)와 사용자 diff 확인이다
2. 식별자·스크립트와 맞추는 글자는 그대로 — manifest 핵심 문구가 backtick 째로 — 공통 검사 2절 — 전부 찾음
3. 한국어는 원문 유지 문자열(위 출력 글자·`훅`) 안에만, 원문자 없음 — 공통 검사 3·4절 — 0
4. 표지 — 줄 수, frontmatter(`name` 불변), 제목 줄 목록 정확 일치, ingest 1~10·query 1~4·알림 해소 1~3 번호, description 평문에 `: ` 없음 — 공통 검사 4절 + `node scripts/frontmatter-lint.js skills/wiki/SKILL.md` — 누락 0
5. 독립 대조 — 게이트 줄 전담 1개 + 조항별(manifest 감사 포함) 1개 — OK 아닌 판정마다 반영하거나 반박해 plan log 에 — 미처분 0
6. 포인터 — 바뀐 절 이름·라벨(적용·인자 해석·공개 점검·신선도·경계·모드·CI 조건·알림 해소·hook 등록)과 유지한 표지(query 1단계·ingest 2·10단계·Python)를 `rg -e "SKILL\.md.{0,40}<표지>" --glob '!plans/**' . /root/.claude/wiki` 로 찾아 걸린 곳마다 처분(이 머지에서 고침 / 그대로 맞음 / post-merge 공용 wiki 에서 고침), `rg -n "신선도 절" skills scripts README.md CLAUDE.md agents` 가 0건, `wiki_check.py` 테스트 3종(`skills/wiki/test_wiki_check.py`·`test_check_links.py`·`test_wiki_search.py`) 통과
7. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
8. [post-merge] 공용 wiki — wiki skill 문구 인용 확인·기록
9. [post-merge] 관찰 — 새 세션에서 `/wiki query` 명시 호출이 이 skill 을 불러 `wiki_search.py` 를 실행하고, 단순 질문에는 골라지지 않는다 — 어긋나면 description 영어 문구를 고치거나 한국어로 되돌리는 안을 제안

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다. terms.md 와 공통 대조 검사를 쓴다(9단계까지의 교훈 — 원문 유지 출력 글자의 한 방향 결합, 명시 호출 전용 skill 의 관찰 기준 — 을 처음부터 적용).
- 원문 유지: 스크립트 출력 11개(Goal Constraints) — 모델이 그 출력을 보고 판단한다(`찾을 wiki 가 없다` 일 때만 조회를 건너뛴다 등). 첫 번째로 나올 때 괄호에 영어 뜻. 기각: 영어로 옮기기(출력과 글자가 안 맞는다), 뜻을 붙이지 않기(영어 독자가 출력의 뜻을 모른다).
- 원문 `비공개`(공개 점검의 제안 출처 값) → `private` — ingest 2단계가 출처 칸 값을 `public`/`private` 로 정하므로 같은 값의 옛 한국어 이름이다.
- 절 제목: 적용 → When to use, 인자 해석 → Arguments, 공개 점검 → Public check(CLAUDE.md §11 과 같음), 신선도 → Freshness, 경계 → Boundaries. `## ingest`·`## query`·`## lint` 와 번호는 그대로(dlc·공용 wiki 가 "query 1단계" 로 가리킨다).
- "SKILL.md 신선도 절" 포인터(`wiki_check.py` docstring 3곳·`--help` 문구 1곳, README 1곳)는 같은 머지에서 "SKILL.md Freshness 절" 로 — 코드의 한국어 문장은 두고 절 이름만. 기각: 제목에 한국어를 남기기(번역문 한국어 0 규칙과 충돌), 포인터를 따로 고치기(그 사이 없는 절을 가리킨다).
- 템플릿 `templates/wiki-check.toml` 주석은 이 단위 밖 — `skills/wiki/test_wiki_check.py` 의 `test_template_smoke_example_is_valid_once_uncommented` 가 주석 속 smoke 예시를 정규식으로 읽고 그 예시(템플릿 51줄)에 한국어 정규식이 있어, 옮기면 코드·테스트 결합 작업이다. translate-repo 인지 Out of scope(코드 주석)인지는 intent `# Open questions` 에 열었다(plan-reviewer).
- 용어표: 기계 대조에 `신선도 => Freshness`·`대표 질문 => representative question`·`대상 계층 => target layer` 추가(한 뜻으로만 쓰이는 절 제목·라벨). 원문 유지 표에 이 skill 의 출력 글자 줄 — 출력을 바꾸는 작업이 같은 머지에서 인용도 고친다.
- Codex 쪽 사용처: `~/.agents/skills/wiki` 는 이 폴더로의 symlink(`scripts/bootstrap/README.md`) — 머지만으로 반영된다.
- 커밋 단위: 1개 — `docs(wiki): translate skills/wiki into English`(SKILL.md·wiki_check.py·README 포인터 — 같은 머지에서만 맞는다). plan·log·대조 파일·terms·intent 는 기록 커밋.
- 테스트: 문서·문자열이라 새 테스트 없음(§7 예외 — 수동 검증은 Acceptance 1~6). 기존 wiki 테스트 3종으로 문자열 변경 회귀를 본다. 사용자 diff 확인이 행동 검증.
- Codex 미가용.
- 롤백: `docs(wiki)` 커밋만 `git revert <sha>`(번역·포인터가 함께 되돌아간다). post-merge 공용 wiki 수정(`WIKI.md` 61줄)은 다른 repo 커밋이라 따로 되돌린다. terms.md 줄은 남아도 무해하다.
- Acceptance 6 변경: "`신선도 절` 만 검색" → "바뀐 절 이름·라벨과 유지한 표지를 repo·공용 wiki 에서 검색하고 걸린 곳마다 처분" — intent Constraints("자기가 바꾼 표지를 가리키는 곳을 전부 검색")에 맞춘다(plan-reviewer). 사용자 승인(2026-10-27, diff 확인 "커밋 (추천)").
- 147줄 "닫힌 모드" → "the other modes (all but `--stop-hook`)" — 원문 용어가 정의 없이 쓰였고, 코드(`wiki_check.py` 의 git 실패 처리 docstring "닫힌 모드는 exit 2, hook 은 systemMessage")가 hook 이 아닌 모드를 뜻함을 보인다. 번역이 아니라 명확화 — 사용자 diff 확인에서 승인(2026-10-27).

# Blockers
