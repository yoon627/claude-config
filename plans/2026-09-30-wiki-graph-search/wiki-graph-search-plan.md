---
title: wiki-graph-search — wiki 를 구조(섹션·링크·callout) 그래프로 읽어 검색 결과를 섹션 단위로 가리키고 관련 페이지·구조 질의를 낸다(#221 첫 단위)
status: in_progress
started: 2026-09-30
updated: 2026-09-30
intent: plans/2026-09-29-repo-context-kit/intent.md
---

# Goal
`skills/wiki/wiki_search.py` 가 wiki 페이지를 평문이 아니라 구조로 읽는다. 구조는 섹션 트리, `[[링크]]` 간선, `[!open]`·`[!conflict]` callout 이다. 이것으로 네 가지를 한다.
- 검색 결과의 맞은 줄마다 그 섹션과 줄 범위를 보인다.
- 결과마다 링크로 이어진 관련 페이지를 붙인다.
- `--links-to <stem>` 질의를 둔다.
- `--open` 질의를 둔다.

GitHub issue #221 의 첫 단위다.

# Intent
- 묶음: `plans/2026-09-29-repo-context-kit/intent.md`. 이 단위는 묶음의 "요청 시" 층(repo wiki 조회)을 강화한다.
- 델타 — Problem: wiki 를 통째로 읽기는 어렵다(컨텍스트 비용). 지금 검색은 페이지를 이름·요약·본문 세 칸의 평문으로만 보고, 섹션·링크·미해결 항목을 쓰지 못한다. 사용자 요청(2026-09-30)은 "단순히 위키를 읽기는 어려울 것이고, 실제 code 와도 연결되면 좋겠다"였다.
- 델타 — Constraints:
  - 묶음 제약을 따른다. 새 기능은 실제로 쓰였는지 잴 방법을 둔다(# Decisions).
  - 색인 파일·daemon 없이 실행할 때마다 만든다. 걷어낸 codegraph 가 실패한 조건(worktree 에서 인덱스가 낡음, 모델이 따로 불러야 하는 도구)을 피하기 위해서다(공용 wiki `codegraph`).
  - 기존 호출 계약(인자·exit code 0/1/2·첫 줄 헤더)과, #219 의 회귀·판별 질의 결과와 속도를 유지한다.
- 델타 — Out of scope:
  - `covers` 간선·`--covers` 조회·가리키는 파일이 없는 covers 점검 → wiki-covers-query.
  - 여러 repo 검색·공개 경계 → wiki-multi-search.
  - 파일 Read 시점 주입 → path-scoped-context / #220.
  - 코드 AST → 묶음 범위 밖(묶음 Out of scope 의 코드 그래프 재도입 조건).
- Open questions: 없음 — 출력 형식은 # Decisions 에서 정하고 plan 리뷰에서 검토한다.
- 분할: 묶음 → `plans/2026-09-29-repo-context-kit/intent.md`. #221 을 단위 셋으로 나눴다(이 plan · wiki-covers-query · wiki-multi-search). 각 단위는 순서대로 혼자 머지돼도 유효하다. covers 조회는 이 단위의 그래프 위에 얹는 순차 의존이다.

# Acceptance
각 항목: 무엇이 충족되나 — 어떻게 검증 — 통과 기준.

1. **단위 테스트**(`skills/wiki/test_wiki_search.py` fixture) — Python 3.13·3.9 — 전부 통과.
   - **섹션 파싱**
     - 코드 블록 안의 `#` 줄은 제목이 아니다. 코드 블록은 여는 fence 와 같은 문자·같거나 긴 길이로만 닫히고, 닫히지 않으면 파일 끝까지 코드다.
     - frontmatter 안의 `# …` 줄은 제목·callout 이 아니다.
     - H2→H3→H2 에서 H3 범위는 다음 H2 앞에서 끝난다.
   - **검색 결과**
     - 맞은 줄에 그 섹션 제목과 줄 범위가 붙는다.
     - 관련 페이지(`→` 나가는 링크·`←` 들어오는 링크)는 같은 wiki 에 실제로 있는 페이지만 보인다. 별칭 링크 `[[a|b]]` 도 간선이다.
     - 없는 페이지를 가리키는 링크와 self-link 는 빼고, index.md 의 링크는 들어오는 링크로 세지 않는다.
   - **`--links-to <stem>`**
     - 그 stem 을 가리키는 링크가 든 줄마다 한 레코드를 낸다(페이지·줄·섹션, 한 줄에 여럿이어도 한 번).
     - `--limit` 과 무관하게 전부 낸다(fixture 는 5건 초과).
     - category 는 가리키는 쪽 페이지에만 적용한다. 그래서 category 밖의 stem 을 가리키는 링크도 찾는다.
     - 결과가 0건이면 exit 1. 어느 wiki 에도 그 stem 이 없거나 category 에 해당하는 페이지가 0쪽이면 exit 2.
     - 같은 stem 이 공용·repo 두 wiki 에 있으면 wiki 별로 따로 찾아 공용 → repo 순으로 낸다.
   - **`--open`**
     - `[!open]`·`[!conflict]` callout 마다 한 줄을 낸다(페이지·줄·섹션·종류·첫 줄 문장).
     - `--limit` 과 무관하다. 0건이면 exit 1.
   - **사용 오류(exit 2)**: 질의 모드에 질의어를 함께 주거나, `--links-to` 와 `--open` 을 함께 준다.
2. **그래프 일치**: 실제 공용 wiki 에서 check_links 간선이 그래프 간선의 부분집합이고, 차이는 별칭 링크 간선과 정확히 같다.
   - 비교 대상: 페이지별 나가는 링크 집합(있는 페이지만, self 제외)과 페이지별 들어오는 링크 집합(index.md 제외).
   - check_links 간선은 `extract_links` 규칙으로 뽑는다.
   - 스크래치 대조 스크립트로 확인한다. 통과 기준은 차이 = 별칭 링크로만 생긴 간선이다. 착수 전 리뷰 실측은 별칭 7개였고, 구현 뒤 실측은 출현 8·간선 5 였다.
3. **실제 wiki 질의**: 실제 공용 wiki 에서 두 질의의 레코드 수가 기계 집계와 같다(실행).
   - `--open` 레코드 수 = pages 본문(코드 블록 밖)에서 `> [!open]`·`> [!conflict]` 로 시작하는 줄 수.
   - `--links-to wiki-shared-layer` 의 페이지 수와 레코드 수 = pages 에서 `[[wiki-shared-layer]]`(별칭 포함)를 담은 다른 페이지 수와 출현 줄 수.
4. **회귀**: #219 plan 의 회귀 질의 10개가 상위 3위 안에 9/10 이상, 판별 질의 4개가 3/4 이상이고, `python3` 새 프로세스 5회 중앙값이 0.5초 미만이다 — 실행.
5. **문서**: 다음이 모두 갱신됐다 — `rg -n "links-to|--open"` 와 exit 2 사유 대조 — 모든 곳.
   - `skills/wiki/SKILL.md` query 1단계가 섹션 위치·관련 페이지·`--links-to`·`--open` 을 설명한다.
   - README 의 skills/wiki 절·tree 가 맞다.
   - exit 2 사유를 나열한 모든 곳에 새 사유(없는 stem, 질의 모드 사용 오류)가 반영됐다: `wiki_search.py` docstring·Usage, SKILL.md, README, `docs/dlc-details.md`.
6. `bash scripts/verify.sh` 마지막 줄이 main 과 같은 skip 만 둔 `ALL PASS`, `bash skills/improve/improve.sh --ci` exit 0 — 격리 runner — 통과.

# Progress
- 2026-09-30: `/wt` 로 worktree 생성(base `main@62ddfcf`). 착수 전 점검에서 열린 묶음 `repo-context-kit` 을 발견했다. #221 이 그 "요청 시" 층의 후속이라 사용자 승인을 받아 연결했다. #220·#221 에 묶음 연결 댓글을 남겼다. 계획 전 조회로 `wiki-search-design`·`codegraph` 를 읽었다.
  - 공용 wiki 구조 실측: 72쪽, 제목 H1 72·H2 299·H3 6, callout open 13·conflict 5·note 9·warning 3·done 1, `[[링크]]` 373개, 코드 블록 5개(안에 `#` 줄 0).
- 2026-09-30: plan 리뷰(Codex 병행)와 묶음 리뷰를 병렬로 받아 반영했다. 둘 다 CONDITIONAL, Critical 0 이다(처분은 # Review Disposition).
  - 리뷰어 실측: 별칭 링크 7개, self-link 0, callout 줄 18(여러 줄 3), `[[wiki-shared-layer]]` 를 담은 다른 페이지 3, 중복 stem 0.
  - 묶음 intent 의 covers-query·multi-search·path-scoped-context 줄과 Open question 2개(공용 covers 기준, 사용 측정)를 고쳤다.
  - architecture 계획 리뷰는 생략했다. 파일 하나를 확장하는 medium 규모다.

- 2026-09-30: TDD Red → 구현 → Green(3.13·3.9 29개).
  - Red 는 `parse_structure` 가 없다는 이유와 모르는 인자 이유로 떨어졌다. 그때 이미 통과하던 두 테스트(사용 오류, exit 2 사례)는 구현 뒤 변이로 올바른 이유를 확인했다.
  - 변이 검사: 구조 14종과 #219 의 14종 모두 KILLED 다. frontmatter 제외 변이를 잡으려고 fixture 의 주석을 `## …` 로 바꿨다(H1 은 원래 섹션에서 빠져 판별력이 없었다).
  - Acceptance 2: check_links 간선 306 ⊆ 그래프 311. 차이 5 가 별칭으로만 생긴 간선과 같다(나가는·들어오는 모두, 별칭 출현 8).
  - Acceptance 3: `--open` 18 = 기계 집계 18, `--links-to wiki-shared-layer` 페이지 3/3·레코드 4/4.
  - Acceptance 4: 회귀 10/10·판별 4/4(대조군 0/4). `python3` 0.065·0.064·0.064·0.066·0.069초(중앙값 0.065), `uv run` 포함 0.097초.
  - Acceptance 5: SKILL.md query 1단계, README 두 곳, `docs/dlc-details.md`, 스크립트 docstring·Usage 에 새 플래그와 exit 2 사유를 반영했다.

- 2026-09-30: 코드 리뷰(Codex 병행)를 반영했다. REQUEST CHANGES 였고 Major 2·Minor 6 이다(처분은 # Review Disposition).
  - 테스트는 32개로, 3.13·3.9 모두 통과한다.
  - 변이 검사: 구조 20종(리뷰에서 살아남았던 계층 합친 그래프·닫는 fence 뒤 글자 포함)과 검색 14종이 모두 KILLED 다.
- 2026-09-30: simplify 로 `Page.body` 를 없앴다. `lines` 의 꼬리와 같은 상태가 두 벌이었고, 본문 위치 계산도 한 번으로 줄였다.
  - 이 뒤 `offset0` 변이가 살아남았다. 줄 번호는 맞은 채 frontmatter 줄만 섞이는 형태였다.
  - 그래서 "frontmatter 링크 줄은 `frontmatter` 로 표시"를 단언하는 테스트를 더했다. plan 에 적어 두고도 테스트가 없던 동작이다. 이제 KILLED 다.
  - 다시 잰 값: A2(차이 = 별칭 간선 5), A3(18=18, 3/3·4/4), A4(10/10, 4/4, `python3` 0.069·0.071·0.063·0.064·0.064초 중앙값 0.064).

- 2026-09-30: 격리 runner 결과 — verify.sh exit 0 `ALL PASS (skip: install-codex-skill.test.ps1)`(main 과 같은 skip), improve --ci exit 0(error 0·warn 0). evidence gate 1~6 을 모두 증거로 충족해 판정은 DONE 이다(status 는 머지 때 done).

# Next
- 다음 즉시 액션 — 사용자 선택: `/e merge`(push·PR·머지 — PR 본문에 #221 첫 단위 표시) 또는 확인. 머지 뒤 묶음의 다음 단위(wiki-covers-query·wiki-multi-search)는 각 Open question 을 정한 뒤 착수한다.

# Decisions
- 관련 결정을 따른다.
  - [[wiki-search-design]]: 점수식, 대상 결정, exit 계약.
  - [[codegraph]]: 모델이 따로 불러야 하는 도구와 낡는 색인을 피한다. 그래서 색인 없이 기존 `wiki_search.py` 호출 경로에 얹는다.
  - 묶음 `repo-context-kit` 의 Constraints: 사용 측정, stdlib, 공개 점검.
- **분할**: #221 을 세 단위(구조 그래프 → covers 조회 / 여러 repo 검색)로 나눴다.
  - 기각 (a) plan 하나: 완료 기준이 커지고 리뷰가 반복된다. 과거 한 단위가 Acceptance 19개·fix 3회로 세션 3개가 걸렸다.
  - 기각 (b) 두 단위(그래프+covers / 여러 repo): covers 조회는 git 파일 목록과 covers 해석이라는 다른 관심사(코드 연결)를 가져오고, 그 조회를 쓰는 곳도 path-scoped-context·#220 쪽이다.
- **기각: 여러 repo 의 wiki 를 공용 wiki clone 한 곳에 모으기**(2026-09-30 사용자 질문으로 다시 검토했다). [[wiki-shared-layer]] 의 기각 절 그대로다.
  - 공개 범위가 섞인다. 모든 repo 세션이 공용 wiki 를 읽고 공개 repo 로 옮겨 적는다.
  - 코드와 같은 브랜치 갱신과 `covers` 신선도 검사가 멈춘다(git 최상위가 다르다).
  - `[[링크]]` 이름 공간이 겹친다.
  - consumer repo 의 CI 와 다른 사람은 `~/.claude` 아래를 볼 수 없다.
  - 사용자 목적은 "한 곳에서 보고 검색하기"로 확인했다. 그래서 wiki 는 제자리에 두고 검색을 모은다(wiki-multi-search).
- **구조 파싱**: 파일 하나에 둔다(`wiki_search.py` — `wiki_check.py` 처럼 stdlib 도구). 입력은 `read_texts` 가 정규화한 전문(BOM·CRLF 처리)이고, 줄 번호는 파일 기준이다.
  - **제목**
    - frontmatter 뒤 본문에서, 줄 첫머리의 ATX `#`~`######` + 공백만 제목으로 본다.
    - 코드 블록은 줄 첫머리(앞 공백 3칸까지)의 ``` · ~~~ 3개 이상으로 열리고, 같은 문자·같거나 긴 길이로만 닫힌다. 닫히지 않으면 파일 끝까지 코드다(CommonMark 와 같다). 코드 블록 안은 제외한다.
    - H1 은 페이지 제목이라 섹션으로 쓰지 않는다. 섹션은 H2 이하이고, 범위는 다음의 같거나 높은 단계 제목 앞까지다. 한 줄의 섹션은 그 줄을 담은 가장 깊은 섹션이다.
  - **링크**
    - `[[stem]]` 과 별칭 `[[stem|표시]]` 를 전문 어디서나 센다. frontmatter·코드 블록 안도 센다(check_links 처럼). stem 이름 집합은 `wiki_check.STEM` 이다.
    - 별칭을 넣는 이유: 실제 공용 wiki 에 별칭 링크가 7개 있고, check_links 는 이것을 못 읽는다.
    - 기각 (a) check_links 와 똑같이 별칭을 빼기 — 관련 페이지·`--links-to` 에서 실제 간선이 빠진다.
    - check_links 자체는 고치지 않는다. 묶음 제약이 경로·인자·출력을 바꾸지 말라고 한다. 한계는 # Deferred 에 둔다.
    - 관련 페이지와 `--links-to` 는 같은 wiki 에 실제로 있는 페이지만 보이고, self-link 는 뺀다. 링크는 같은 wiki 안에서만 쓰는 것이 규약이다.
    - index.md 는 카탈로그라 들어오는 링크로 세지 않는다(check_links 의 orphan 판정과 같다).
    - 같은 wiki 안에서 stem 이 겹치면(schema 위반) pages 기준 경로 순으로 앞의 페이지를 쓴다.
  - **callout**: 본문(코드 블록 밖)에서 줄 첫머리 `>` 뒤의 `[!open]`·`[!conflict]` 만 모은다. 여러 줄 callout 은 첫 줄 문장만 보인다.
  - 보강 (코드 리뷰):
    - backtick fence 의 info 에 backtick 이 있으면 fence 가 아니다. 닫는 fence 뒤에 글자가 붙으면 닫지 않는다.
    - 빈 ATX 제목(`##`)도 섹션 경계다. 표시할 때는 섹션 이름을 생략한다. 닫는 `#` 는 앞에 공백이 있을 때만 뗀다.
    - 별칭은 `[` 를 받지 않는다. 닫히지 않은 별칭이 뒤의 링크를 삼키지 않게 하기 위해서다.
    - callout 은 WIKI.md 표기 밖의 변형(대소문자, 접기 표시 `-`/`+`, 중첩 인용)도 모은다. self-link 는 관련 페이지와 `--links-to` 모두 stem 으로 가른다.
    - 한계: 인용(`>`) 안의 코드 블록은 코드로 보지 않는다. 그래서 인용 안 코드에 든 callout 예시가 `--open` 에 잡힐 수 있다. 실제 wiki 에는 0건이고, 오류 방향이 누락이 아니라 잡음이라 받아들인다.
- **출력**
  - 맞은 본문 줄: `L<n> §<섹션 제목> (L<a>-<b>): <줄>`. 섹션이 없으면(첫 제목 앞) 지금처럼 `L<n>: <줄>` 이다. 섹션 제목과 줄은 줄여 보인다.
  - 관련 페이지: 결과마다 `관련: → a, b · ← c` 한 줄. 나가는 쪽 먼저, 합쳐 6개까지다.
  - 기각: 관련 페이지에 점수 가산점 — #219 의 검증된 순위(회귀·판별)를 바꾸므로, 이 단위에서는 보여 주기만 한다.
- **질의 모드**
  - 레코드 형식: 페이지마다 머리줄 `[<계층>] <category>/<stem>  <절대경로>` 을 한 번 내고, 그 아래 레코드를 한 줄씩 들여 쓴다. 절대경로는 검색과 같이 Read 에 바로 쓰게 한다.
    - `--links-to` 레코드: `   L<n> §<섹션>: <줄>`
    - `--open` 레코드: `   L<n> §<섹션>: [!open] <첫 줄 문장>`
    - frontmatter 줄은 섹션 자리에 `frontmatter` 를, 첫 제목 앞 본문은 `§` 없이 `L<n>:` 를 쓴다.
  - `--links-to` 는 링크가 든 줄마다, `--open` 은 callout 마다 한 레코드다.
  - `--limit` 은 검색 결과에만 쓴다. 질의 모드는 전부 낸다(목록형이고, 잘리면 "없음"으로 읽힌다).
  - `--links-to`·`--open` 은 서로, 그리고 질의어와 함께 쓸 수 없다(exit 2).
  - `--category` 는 출발 페이지(가리키는 쪽·callout 이 든 쪽)에만 적용한다. 그래프와 stem 존재는 거르기 전 전체 wiki 로 판정한다. category 에 해당하는 페이지가 0쪽이면 검색과 같이 exit 2 다.
  - 헤더 첫 줄과 공용 wiki 부재 정책은 검색과 같다.
  - exit: 0 레코드 있음, 1 없음, 2 사용 오류·없는 stem·없는 category.
- **사용 측정**(묶음 제약): 측정은 묶음 intent `# Open questions` 에 `(열림)` 으로 올린다. 그래서 측정을 처분하기 전에는 묶음을 닫을 수 없고, 이 plan 이 done 이 돼도 측정 담당이 남는다.
  - 기간: 머지 뒤 2주(2026-10-14 무렵부터).
  - 제외: 머지 이전 호출, 이 worktree·scratchpad 가 cwd 인 호출, 테스트·리뷰 subagent 세션.
  - 집계: transcript 레코드는 tool_use id 로 중복을 제거한다.
  - 새 기능 신호로 세는 것:
    - `--links-to`·`--open` 호출 수.
    - 검색 결과의 `관련:` 줄에만 나온 페이지를 같은 턴에 Read 한 수.
    - Read 의 `offset` 이 표시한 섹션 시작 줄과 같은 수.
  - `wiki_search.py` 호출 수 자체는 새 기능 신호가 아니다. dlc·§11 조회가 원래 부르기 때문이다.
  - 임계값: 2주 합계 3회 미만이면 문서 안내를 고치거나 되돌림을 검토한다.
- **단일 파일 예외**: 묶음 공통 제약은 "파일 하나만 복사해도 동작"이다. `wiki_search.py` 는 #219 부터 `wiki_check.py` 를 import 하므로, vendoring 할 때 두 파일을 함께 옮긴다. 이 예외는 묶음 Constraints 에 한 줄로 적는다.
- **커밋 단위**: 1개 — 구조 파싱, 출력, 질의 모드, 테스트, 문서가 한 기능이다.

# Key Files
- `skills/wiki/wiki_search.py` — 구조 파싱·출력·질의 모드
- `skills/wiki/test_wiki_search.py` — fixture 테스트
- `skills/wiki/SKILL.md` — query 1단계
- `README.md` — skills/wiki 절, tree
- `plans/2026-09-29-repo-context-kit/intent.md` — 묶음(# Plans 줄·Open question)

# Blockers
없음

# Review Disposition
plan 리뷰 — plan-reviewer(Codex 병행) CONDITIONAL, Critical 0·Major 4·Minor 3.
- M1 질의 모드 출력·`--limit`·두 모드 동시 사용 계약 — fix: # Decisions 질의 모드, Acceptance 1·3(레코드 수 비교, 5건 초과 fixture).
- M2 category 적용 순서 — fix: 출발 페이지에만 적용하고 그래프·stem 존재는 전체 wiki 로 판정한다. fixture 를 넣는다.
- M3 별칭 링크 `[[a|b]]` 누락 — fix(b 안): 간선에 넣는다. Acceptance 2 는 "check_links ⊆ 그래프, 차이 = 별칭". 기각 (a) 는 # Decisions 에 있다.
- M4 사용 측정 기준·담당 — fix: 제외·중복 제거·신호·임계값을 정했고, 묶음 Open question 으로 올린다.
- m5 self-link·fence 경계·frontmatter 제외 — fix: # Decisions 구조 파싱, Acceptance 1. 들어오는 링크는 페이지별 집합으로 대조한다(Acceptance 2).
- m6 같은 stem — fix: wiki 별로 따로, 공용 → repo 순. 한 wiki 안의 중복은 경로 순으로 앞의 것을 쓴다.
- m7 exit 2 문서 4곳 — fix: Acceptance 5.
- 제안(되살아난 안 기록) — fix: # Decisions 에 "여러 repo wiki 모으기" 기각을 남겼다.

묶음 리뷰 — plan-reviewer 묶음 모드 CONDITIONAL, Major 4·Minor 4.
- [묶음] M1 모으기 안 기각 미기록 — fix: 이 plan # Decisions 와 intent wiki-multi-search 줄.
- [묶음] M2 공용 wiki covers 해석 기준(`~/.claude`)이 `wiki_check` covers 정의(git 최상위)와 충돌하고, 대상도 0건이다 — fix: covers-query 줄에서 뺐다. 공용 wiki 가 `~/.claude` 코드를 가리키는 방법은 intent Open question 으로 올렸다.
- [묶음] M3 없는 파일 covers 점검은 `wiki_check` 판정과 겹친다 — fix: covers-query 는 그 판정을 재사용해 표시만 한다.
- [묶음] M4 path-scoped-context 줄과 B/C 질문 불일치, 결정 시점 — fix: 그 줄을 "전달 방식 미정(B/C), C 면 covers-query 선행"으로 고쳤다. 결정 시점은 covers-query 착수 전이다. 비교 항목에 등록 비용·Read 당 지연·측정을 더하고, 문서 기준 주장은 로컬 미재현이라고 표시했다.
- [묶음] m wiki-multi-search 선행·공개 경계 기본값 — fix: 선행 wiki-graph-search(같은 파일). 공개 경계는 fail-closed(표시 없는 wiki·판정 불가 세션은 제외).
- [묶음] m 단일 파일 제약과 wiki_check import — fix: 예외를 묶음 Constraints 에 한 줄로 적었다.
- [묶음] m 새 단위 규모 메모 — fix: 세 줄에 규모 예비값(medium)을 적었다.

구현 리뷰 — code-reviewer(Codex 병행) REQUEST CHANGES, Critical 0·Major 2·Minor 6. 모두 재현으로 확인된 지적이고, 실제 wiki 에는 해당 입력이 0건이다.
- M1(a) backtick info 줄을 fence 로 열어 뒤의 제목·callout 을 놓친다 — fix. "없음"을 거짓으로 내는 조용한 누락이다.
- M1(b) 인용 안 코드 블록 — wontfix. 한계로 적었다(# Decisions). 오류 방향이 잡음이다.
- M2 별칭이 `[` 를 받아 뒤의 링크를 삼킨다 — fix: `[^\[\]\n]`.
- m 테스트가 계층을 합친 그래프와 닫는 fence 뒤 글자 조건을 가르지 못한다 — fix: fixture·단언을 추가했다. 변이 20종 모두 KILLED.
- m 빈 ATX 제목 — fix. m 중복 stem 의 self-link 기준 불일치 — fix: stem 으로 통일했다.
- m 문서 "출현마다"와 코드 "줄마다" — fix: "링크가 든 줄마다"로 맞췄다. m SKILL.md exit 2 규칙 문장 위치 — fix: 목록 밖으로 뺐다.
- open(callout 변형) — fix: 대소문자·접기 표시·중첩 인용을 모은다.
- 재리뷰는 생략했다. 수정이 지적 그대로이고 변이 검사로 확인했다. 사용자가 리뷰 반복을 줄이라고 했다.

# Deferred
- `check_links.py` 는 별칭 링크 `[[a|b]]` 를 읽지 못한다(`WIKILINK` 가 `|` 를 받지 않는다). 그래서 dead link·outbound·orphan 판정에서 그 간선이 빠진다. 실제 공용 wiki 에 7개 출현한다. 묶음 제약(경로·인자·출력 유지) 안에서 고칠지는 별도로 정한다 — Minor, `skills/wiki/check_links.py:35`.
