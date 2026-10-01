---
name: wiki
description: 영속 프로젝트 메모리(LLM Wiki)를 운영하는 ingest/query/lint 오케스트레이션. 두 계층 — 현재 repo 의 `wiki/`(그 repo 의 결정·교훈)와 공용 `~/.claude/wiki/`(여러 repo 에 쓸모 있는 공개 가능한 사실·전역 자산의 교훈). raw 소스·작업 지식을 상호링크 markdown 페이지로 누적하고(ingest), 누적 페이지로 답하고(query), 무결성을 점검한다(lint). `/wiki <ingest|query|lint>` 명시 호출 시 사용. 단순 질문·코드 변경에는 쓰지 않는다(dlc/직접의 몫).
---

# wiki — LLM Wiki 운영 (영속 프로젝트 메모리)

wiki 는 두 계층이다(CLAUDE.md §11 이 배치 규칙의 단일 소스):
- **repo wiki** `<ROOT>/wiki/` — 그 repo 의 결정·교훈. 운영 규약은 그 wiki 의 `WIKI.md`.
- **공용 wiki** `~/.claude/wiki/` — 여러 repo 에 쓸모 있는 공개 가능한 사실과 전역 자산의 결정·교훈. 규약은 `~/.claude/wiki/WIKI.md`. 비공개 GitHub repo 를 이 경로에 별도 clone 한 것이다(`~/.claude` 는 추적하지 않는다). 저장소는 비공개지만 모든 repo 세션이 읽고 옮겨 적으므로 아래 "공개 점검"을 통과한 내용만.

**현재 repo 판정**: `[ "$(git rev-parse --path-format=absolute --git-common-dir)" -ef "$HOME/.claude/.git" ]` 가 참이면 `~/.claude`(worktree 포함, `-ef` 라 `C:/`·`/c/`·심볼릭 링크 같은 표기 차이에 무관) — 두 계층이 같고, 읽고 쓰는 위치는 절대경로 `~/.claude/wiki` 다. worktree 에는 사본이 없어 쓰기는 main 세션에서만 한다. `~/.claude` 루트에서 돌린 `rg`·Grep 은 부모 `.gitignore` 때문에 이 폴더를 건너뛰므로 검색할 때는 경로를 명시한다. 아니면 "다른 repo"(비-git 디렉토리 포함). `git -C ~/.claude …` 로 판정하지 않는다(worktree 격리 가드가 거부한다).

시작 시 **대상 wiki 의 `WIKI.md` 를 반드시 read**. 이 skill 은 그 규약을 강제하는 실행 절차다. 어느 wiki 에 둘지는 §11, 페이지 형식은 대상 wiki 의 WIKI.md 가 정한다. 페이지 write 는 **메인만**(single-writer, `plans/` 와 동일 원칙). 충돌 시 CLAUDE.md 우선.

## 적용
- `/wiki ingest|query|lint` 명시 호출.
- dlc 연계(CLAUDE.md §11): 작업 시작 시 두 wiki 조회(있는 것만 — `wiki_search.py`, query 1단계), 작업 후 재사용 지식의 대상 계층 판정·ingest 제안(자동 아님).
- 코드 변경·단순 질문은 제외.

## 인자 해석
| 입력 | 동작 |
|---|---|
| `ingest <경로\|설명>` | raw/지식 → 대상 wiki 페이지 갱신 + index/log |
| `query <질문>` | 두 wiki 를 검색해 페이지 read 후 답, 가치 있으면 filed |
| `lint` | 현재 repo 의 wiki 무결성 점검·보고 |
| (빈 인자) | 두 `index.md` 요약 + 사용법 |

첫 토큰으로 분기. 모르는 서브커맨드는 사용법 안내 후 종료.

## 공개 점검 (공용 적립 작업이 공개하는 모든 것)
공용 wiki 는 비공개 repo 지만 모든 repo 세션이 읽고 공개 repo 로 옮겨 적는다 — 옮겨져 push 된 이력은 revert 로 지워지지 않는다. 금지 목록과 점검 표면(페이지·`sources`·index·log·`source/` 요약·plan·브랜치/worktree 이름·커밋 메시지·PR 제목/본문)은 **CLAUDE.md §11** 이 단일 정의다 — token/key/PII 는 늘 금지.
- 근거는 공개 검증 가능한 것(공식 문서 URL·공개 이슈·비공개 코드 없이 되는 재현)만 `sources` 에 싣는다. 비공개 코드 경로를 근거로 옮기지 않는다.
- 제안의 출처가 `비공개` 이거나 **출처가 적혀 있지 않으면**(불명 = 비공개로 본다) 커밋 전에 최종 diff 를 보이고 `AskUserQuestion`(없는 환경이면 채팅)으로 확인받는다(CLAUDE.md §1 외부공개).
- 걸리면 공용에서 빼고 출처 repo 의 wiki 로 돌린다.

## ingest
1. **대상 계층 판정**(§11): repo 고유 → repo wiki / 여러 repo 에 쓸모 있는 공개 가능한 사실·전역 자산 교훈 → 공용 / 비대상(사유). 애매하면 repo wiki. repo wiki 대상인데 repo wiki 가 없거나 비-git 이면 비대상 + 사유(공용 대상은 여전히 2단계 제안).
2. **다른 repo 에서 공용 대상**이면 쓰지 않는다: Report 와 출처 plan `# Deferred`(없으면 Report 만)에 `~/.claude main 세션에서 /wiki ingest <요약 · 공개 근거 · 출처(공개/비공개)>` 를 남기고 끝낸다(§11 과 같은 형식). 출처 칸에는 `공개`/`비공개` 만 쓴다(비공개 repo 이름은 적지 않는다). 요약·근거는 위 공개 점검을 이미 통과한 문장이어야 한다.
3. 공용 wiki 에 쓰는 경우 main 세션에서 `~/.claude/wiki` 에 직접 쓰고, 그 repo 의 main 에 커밋한다(CLAUDE.md §3-1·§8 예외 — worktree 에는 사본이 없다). worktree 세션이면 쓰지 않고 plan `# Deferred` 에 남긴 뒤 main 세션에서 한다. push 는 요청 시. 다른 repo 의 repo wiki 는 그 repo 의 규칙대로 쓴다.
4. 대상 wiki 의 `WIKI.md` read(규약 확인).
5. 원문이 주어지면 대상 wiki 의 `raw/`(없으면 mkdir) 에 보존(최초 1회, 이후 불변 — 편집·삭제 안 함) → `git check-ignore <wiki>/raw/<f>` 로 ignored 확인. raw 적재는 사용자 큐레이션 또는 ingest 입력에서만. worktree 에 둔 raw 는 gitignored 라 worktree 정리 때 경고 없이 지워진다 — 보존이 필요하면 정리 전에 옮긴다.
6. 원문 기반이면 `pages/source/<name>.md` 1:1 요약 생성(공용이면 공개 점검 — 비공개 원문의 요약은 공용에 두지 않는다).
7. 관련 `entity`(외부사실·버전)/`decision`(결정·교훈)/`concept` 페이지 갱신·생성. 한 ingest 가 여러 페이지 touch. 같은 사실이 이미 있으면 새 페이지 대신 갱신.
8. 각 페이지 규칙 충족: frontmatter, ≥2 outbound `[[링크]]`(같은 wiki 안의 페이지만 — 계층을 넘는 참조는 경로 텍스트 `~/.claude/wiki/pages/<cat>/<stem>.md`), sources, 모순은 `> [!conflict]`. **raw 적재·페이지 write 전 token/key/PII 점검 → 발견 시 마스킹/중단**(경고 후 진행 금지), 공용이면 공개 점검까지.
9. `index.md` 등재 + `log.md` append(`## [YYYY-MM-DD] ingest | <title>`).
10. `check_links.py`(링크·index)와 `wiki_check.py schema`(frontmatter 형식)로 점검 후 보고(명령은 lint 절). `covers` 가 있는 페이지를 고쳤으면 `wiki_check.py stale --report` 도 돌린다(값 옮기기는 신선도 절). config 에 `[smoke]` 를 둔 wiki 면 `wiki_check.py smoke` 도 돌린다. 공용 적립이면 커밋 전 공개 점검을 한 번 더(비공개 출처면 diff 확인).

## query
1. `uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_search.py" <질의어…>` 로 관련 페이지를 찾아 read 한다.
   - 공용 wiki(`CLAUDE_SHARED_WIKI`, 없으면 `~/.claude/wiki`)는 cwd 와 무관하게 찾고, repo wiki 는 현재 디렉터리에서 repo 루트까지 올라가며 찾아 함께 검색한다. 둘이 같은 경로면 한 번만 찾는다.
   - 결과마다 계층(`[공용]`/`[repo]`)·절대경로·index 요약·맞은 본문 줄이 나온다.
     - 맞은 줄에는 그 섹션과 줄 범위가 붙는다(`L20 §결정 (L18-35): …`). 섹션만 읽으려면 Read 의 offset·limit 에 그 범위를 쓴다.
     - 결과마다 같은 wiki 안에서 링크로 이어진 관련 페이지가 붙는다(`관련: → 나가는 · ← 들어오는`). 별칭 `[[a|b]]` 도 링크로 세고, index.md 의 링크는 들어오는 쪽으로 세지 않는다.
   - `--limit N`(기본 5)·`--category C` 는 질의어 앞뒤 어디든 둔다. `-` 로 시작하는 단어(플래그 이름)는 앞의 `-` 를 떼고 넣는다.
   - 구조 질의(질의어 대신 쓴다):
     - `--links-to <stem>`: 그 페이지를 가리키는 링크가 든 줄을 전부 낸다(한 줄에 여럿이어도 한 번). 결정을 바꾸기 전에 영향받는 페이지를 찾을 때 쓴다.
     - `--open`: 미해결 `[!open]`·`[!conflict]` 를 전부 낸다.
     - 둘 다 페이지마다 머리줄(계층·이름·절대경로) 아래 `L<줄> §<섹션>: …` 레코드를 낸다. `--limit` 을 따르지 않는다.
     - `--category` 는 가리키는 쪽(callout 이 든 쪽) 페이지에만 적용한다.
   - 첫 줄의 찾은 wiki·쪽수로 어디를 찾았는지 확인한다. 기본 경로에 공용 wiki 가 없으면 stderr 경고와 함께 repo wiki 만 찾는다.
   - exit 1(결과 없음)이거나 결과가 빗나가면 다른 단어(영문 식별자·동의어)로 다시 찾고, 두 `index.md`(공용은 `~/.claude/wiki/index.md`)를 직접 훑는다. 한 음절 한글(`훅`)은 찾지 못한다.
   - exit 2 의 경우:
     - 찾을 wiki·단어·category·stem 이 없다.
     - 질의 모드를 질의어나 서로와 함께 썼다.
     - `CLAUDE_SHARED_WIKI` 가 wiki 가 아니다.
     - 읽기 오류다.
     - stdout 을 읽는 쪽이 먼저 닫아 출력을 끝까지 내지 못했다(`| head` 가 다 받은 뒤 닫으면 오류 없이 원래 값이다).
     - 예상 밖 오류다(stderr 에 traceback).
   - exit 2 면 stderr 의 이유를 보고 질의·설정을 고쳐 다시 찾는다 — `찾을 wiki 가 없다` 일 때만 조회를 건너뛴다.
   - 점수는 stem·title 일치 3, index 요약 일치 2.5, 본문 BM25(상한 2.2)의 idf 가중합이다. 한글은 2-gram 으로 나눠 조사가 붙어도 맞는다.
2. 페이지 기반으로 답(raw chunk 아님). 근거 페이지를 **어느 wiki 의 것인지와 함께** 인용.
3. 재사용 가치 있으면 **현재 repo 의 wiki** 에 `pages/query/<slug>.md` 로 filed(frontmatter+링크) + 그 wiki 의 `log.md` append. 공용 페이지가 근거인 답을 다른 repo 에서 filed 할 가치가 있으면 ingest 2단계의 공용 제안으로 돌린다. 공용 페이지는 비공개 repo 의 페이지를 가리키지 않는다.
4. 관련 페이지가 없으면 "wiki 에 없음" 명시(추측 금지). 필요 시 ingest 제안.

## lint
현재 repo 의 wiki 만(`~/.claude` 에서는 공용 wiki — 검사 명령에 `~/.claude/wiki` 를 경로로 넘긴다). 점검만, 자동 수정 안 함(수정은 보고 후 사용자 승인). 점검 항목:
- dead `[[링크]]`(대상 부재) / orphan(`index.md` 외 어느 페이지도 안 가리킴, inbound=0) / outbound 링크 <2.
- `index.md` ↔ `pages/**` 불일치(누락·잉여).
- frontmatter 형식(필수 키·category·날짜 등)과 stem 형식·중복.
- covers 신선도 — `verified_at` 이 지금 covers 파일 지문과 다른 페이지(신선도 절).
- 대표 질문 — 그 wiki 가 답해야 하는 질문마다 답할 페이지·index 등재·본문 근거가 있는가, 작업 중 흔적(브랜치 이름·plan 상태·시점 집계)이 페이지에 남지 않았는가(config 에 `[smoke]` 를 둔 wiki 만).
- 모순(`[!conflict]` 미해소)·오래된 entity 버전(외부 사실의 버전 낡음 — `wiki_check.py stale` 과 다르다) 후보. 공용 wiki 면 공개 점검 위반 후보도.

기계 점검은 아래 스크립트가 하고(stdlib 만 쓴다), 의미 점검(모순·오래된 entity 버전·공개)은 LLM 이 한다.
- `check_links.py` — dead link·orphan·outbound<2·index 동기화: `uv run --no-project python "${CLAUDE_SKILL_DIR}/check_links.py" [wiki 경로]`(인자가 없으면 현재 repo 의 wiki). 별칭 `[[a|b]]` 도 `a` 로의 링크로 센다. 다만 index 등재는 별칭 없는 `[[a]]` 만 인정한다(smoke 와 같은 기준). exit 0 clean, 1 위반 — UTF-8 이 아닌 페이지·index 는 `UTF-8 아님` 위반을 내고 나머지를 판정한다(페이지는 schema 와 같은 값), 2 pages 디렉터리 없음이나 읽기 실패(권한·하위 디렉터리 — 위반 목록 없이 `check_links: 읽기 실패 — <경로>: <이유>`).
- `wiki_check.py schema` — frontmatter 형식: `uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_check.py" schema [wiki 경로] [--config 파일]`.
  - wiki 경로가 없으면 현재 디렉터리에서 repo 루트까지 올라가며 `wiki/` 를 찾는다. `docs/wiki` 처럼 그 밖에 있는 wiki 는 경로를 넘긴다.
  - exit 0 통과, 1 위반(`<경로>: <규칙> — <내용>` 한 줄씩, 경로는 repo 루트 기준이고 repo 밖이면 wiki 의 부모 기준), 2 사용·설정·환경 오류.
  - 값은 YAML 처럼 공백 뒤 `#` 부터 주석이다. `[PR #82, …]` 는 그 줄에서 닫았어도 `[PR` 만 남아 위반이다. `#` 가 항목의 일부면 그 항목을 따옴표로 감싸고(`["PR #82", …]`), 설명이면 `]` 뒤의 주석으로 옮긴다(`[a.kt]  # 설명`). `[ … ]` 뒤에 붙은 설명도 같다. 설명까지 따옴표로 감싸면 covers 는 어디에도 맞지 않는 패턴이 되어 stale 이 조용히 놓친다.
  - 규칙은 `<wiki>/wiki-check.toml` 로 그 wiki 의 WIKI.md 규약에 맞춘다. 템플릿은 `templates/wiki-check.toml` 이고 키 설명은 템플릿 주석에 있다. config 가 없으면 공용 WIKI.md 규약(필수 키 5개, category 5종, `created`·`updated` 날짜)으로 돈다. 형식의 정본은 WIKI.md 라 둘이 어긋나면 config 를 고친다.
  - config 를 읽으려면 Python 3.11+(`tomllib`)가 필요하다. 3.9·3.10 은 config 없는 검사만 된다.
- `wiki_check.py stale --report` — covers 신선도: `uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_check.py" stale --report [wiki 경로]`. 판정에 config 값을 쓰지 않지만 config 가 있으면 읽고 검증한다(아래 config 오류). `covers`·`verified_at` 이 있는 페이지와 읽지 못한 페이지(UTF-8 아님·frontmatter 닫힘 없음·covers 값이나 항목이 `[` 로 시작해 `]` 로 끝나지 않음)가 없으면 "검사 대상 아님" 을 내고 exit 0 이라 모든 wiki 에 돌려도 된다. 읽지 못한 페이지는 covers 가 없어도 "covers 읽기 실패" 위반(exit 1)이다. covers 페이지가 있으면 git repo 안에서 돌린다. 판정·exit code 는 신선도 절.
- `wiki_check.py smoke` — 대표 질문: `uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_check.py" smoke [wiki 경로] [--config 파일]`. config 에 `[smoke]` 가 없으면 "검사 대상 아님" 을 내고 exit 0 이라 모든 wiki 에 돌려도 된다. `[smoke]` 를 두고 검사를 하나도 채우지 않으면 exit 2 다. 예시는 템플릿 주석에 있다.
  - `[[smoke.questions]]` 마다 `page`(pages 기준 `.md` 경로)가 있고, `index.md` 에 `[[stem]]` 이 있고, 본문(frontmatter 뒤)의 어느 줄이 `expect` 에 맞으면 통과다. `expect` 는 Python `re` 이고 grep 처럼 줄마다 찾는다. POSIX 문자 클래스(`[[:space:]]`)와 GNU grep 방언(`\<`·`\>`, 문자 집합 안의 `[=…=]`·`[.….]`)은 Python `re` 가 다른 뜻으로 읽어서 exit 2 로 막는다 — `\s`·`[0-9]`·`\b` 로 쓴다. `[smoke.forbid] patterns` 도 같다.
  - `[smoke.forbid]` 는 pages 의 `.md` 전문(frontmatter 포함)을 줄마다 보고 걸린 줄을 FAIL 로 낸다. `branch_names`(로컬·원격 추적 브랜치 이름에서 원격 이름을 뗀 뒤 `/` 없이 하이픈이 든 소문자 이름 전체인 것 — `feat/x-y` 처럼 `/` 가 든 이름은 보지 않는다. 원격 이름은 한 단계로 읽어서 `team/fork` 처럼 `/` 가 든 원격의 브랜치는 보지 않는다. git repo 안이어야 하고, repo 밖이면 다른 검사도 돌지 않고 smoke 전체가 exit 2), `plan_status`(`status: in_progress`), `patterns`(정규식 목록)이고 모두 기본 꺼짐이다. 작업 중 상태를 옮겨 적은 문장은 그 작업이 끝나면 틀린 사실로 남는다.
  - exit 0 통과, 1 실패(`PASS | …`·`FAIL | …` 한 줄씩과 합계), 2 사용·설정·환경 오류.
- frontmatter 판정의 정본은 `wiki_check.py schema` 다. `check_links.py` 의 frontmatter 줄은 호환용이라 BOM 이 붙은 페이지와 닫는 `---` 가 없는 페이지를 다르게 본다. `check_links.py` 만 따로 돌리면 같은 stem 의 페이지 중복을 잡지 못한다(한쪽을 조용히 덮어쓴다).
- config(`<wiki>/wiki-check.toml`)가 있으면 schema·stale·smoke 가 모두 파일 전체를 읽고 검증한다. 모르는 키·잘못된 타입·`[smoke]` 정규식 오류(POSIX 문자 클래스 포함)는 어느 섹션에 있든 모든 명령이 exit 2 이고, hook 은 covers 페이지가 있을 때만 config 를 읽어 오류를 stale 판정 대신 `systemMessage` 로 매 턴 알린다. smoke 오타 하나가 ingest 10단계의 schema 점검도 막으므로 config 를 고친 뒤 `schema` 를 먼저 돌려 본다.

결과를 분류해 보고 + 수정안 제시 + `log.md` append(`## [YYYY-MM-DD] lint | <요약>`).

## 신선도 (`covers`·`verified_at`)
두 키의 의미·권고·판정은 이 절이 정본이다. 코드에 대해 주장하는 페이지가 그 코드 경로를 `covers` 에 걸면, 코드가 바뀌었는데 페이지가 그대로인 것을 `wiki_check.py stale` 이 찾는다. 두 키는 선택이고, 없는 페이지는 stale 이 보지 않는다.

**`covers`** — 경로 패턴 목록(인라인 `[a, b]` 또는 블록 `- a`). 인라인 목록은 한 줄 안에서 닫는다 — 값이나 블록 항목이 `[` 로 시작해 `]` 로 끝나지 않으면(여러 줄 목록, 주석에 잘림, `[ … ]` 뒤의 글자) schema 위반이고 stale 은 "covers 읽기 실패" 로 본다.
- 패턴은 git 최상위 기준 상대 경로의 fnmatch 다. 대소문자를 가리고 `*` 가 `/` 를 넘는다(`src/*` 는 `src/a/b.py` 에도 맞는다 — gitignore 식 `**` 가 아니다). 경로와 똑같은 패턴은 `[`·`?`·`*` 가 들어 있어도 언제나 맞는다. 패턴 전체를 한 번은 `[…]` 를 문자 집합으로, 한 번은 모든 `[` 를 문자 그대로 읽어 맞춘다(`app/[id]/*` 는 `app/[id]/page.tsx` 에 맞는다). 한 패턴에 리터럴 `[` 와 문자 집합을 섞으려면 리터럴 쪽을 `[[]` 로 쓴다(`app/[[]id]/[ab].py`). 빈 항목, `/`·`./`·`../` 로 시작, `/` 로 끝남, `\` 포함은 schema 가 위반으로 낸다.
- 거는 기준(권고 — 스크립트는 강제하지 않는다): 코드가 바뀌면 참·거짓이 달라지는 주장에 직접 걸린 경로만 건다. 근거는 한 repo 의 실측이다 — 넓은 covers 가 커밋의 약 3분의 1 에 걸려 확인이 형식이 됐다.
- 형태는 정확한 파일 경로, `디렉터리/*`, `디렉터리/*.확장자` 를 권한다. `.claude/rules` 의 `paths:`(glob — `*` 는 한 디렉터리 안에서만 맞고 `**` 가 디렉터리를 넘는다)로 옮길 수 있는 형태다. `?`·`[...]` 가 `/` 에 맞는 패턴이나 `*` 가 여럿인 패턴은 그대로 옮기지 못한다.

**`verified_at`** — 페이지를 코드와 대조한 때의 covers 파일 내용 지문. `fp1-` 와 소문자 16진수 16자다.
- 지문은 covers 에 걸린 파일(wiki 페이지는 뺀다)마다 "지금 `git add -A` 를 하면 index 에 기록될 (mode, blob)" 을 모아 해시한 값이다. 이력을 보지 않아 fixup·rebase·squash·revert·얕은 clone 과 무관하게 "지금 내용이 대조한 내용과 같은가" 하나로 정해진다. 실행 비트만 바뀌어도, covers 목록을 바꿔 파일 집합이 바뀌어도 달라진다.
- 값을 만드는 명령은 따로 없다. `stale --report` 가 페이지마다 현재 값을 보인다. 페이지 주장을 걸린 파일과 대조해 고친 뒤에만 그 값을 적고, 값을 바꾸는 커밋 메시지에 대조한 파일을 적는다. 값 한 줄을 옮기면 hook 과 보고가 함께 풀려서, 대조 없이 옮기는 것을 도구로는 막지 못한다 — 이 순서가 유일한 장치다.
- 판정: 값이 지금 지문과 같으면 OK, 다르면 STALE(위반)이다. 값이 없으면 "미확인"(위반 아님)이다. 16진수 7~64자는 옛 형식(commit 값)이라 위반이다 — 페이지를 다시 대조하고 보고가 보인 값으로 바꾼다. `fp2-` 처럼 스크립트가 모르는 판은 스크립트 갱신이 필요하다(exit 2). covers 없이 `verified_at` 만 있거나 covers 에 걸린 파일이 0개면 위반이다.

**모드** — `uv run --no-project python "${CLAUDE_SKILL_DIR}/wiki_check.py" stale <모드> [wiki 경로] [--config 파일]`

| 모드 | 판정 | 용도 |
|---|---|---|
| `--report` | 페이지마다 `verified_at` 과 작업 트리의 지문을 비교한다. 이력을 보지 않는다 | 감사·lint·CI |
| `--branch [--base REF]` | `merge-base(HEAD, base)..HEAD` 의 commit 에서 covers 파일이 바뀌었는데 페이지는 바뀌지 않았다 | CI·push 전 |
| `--stop-hook` | `--branch` 와 같은 판정을 작업 트리(untracked 포함)까지 넓혀서 본다 | Claude Code Stop hook |

- `--branch`·`--stop-hook` 은 순서를 보지 않는다 — 브랜치에서 페이지를 한 번 고쳤으면 그 뒤의 covers 변경도 알리지 않는다. 대조 뒤의 변경은 `--report` 가 잡지만 `verified_at` 이 있는 페이지만이다.
- base 는 `--base`, config `[stale] base`, 기본 브랜치 후보(`origin/HEAD`·`origin/main`·`origin/master`·`main`·`master` 가운데 현재 브랜치가 아닌 ref 들과 HEAD 의 분기점) 순으로 정한다. CI 는 `--base origin/$GITHUB_BASE_REF` 처럼 넘긴다. `--report` 는 `--base` 를 받지 않는다(exit 2).
- `--branch`·`--report` 는 페이지·config 를 작업 트리에서 읽는다. commit 되지 않은 변경이 있으면 출력 머리와 stderr 에 "작업 트리 기준 — … 미커밋 변경 N개" 를 쓴다. CI 는 commit 된 내용으로 판정한다.
- exit: 0 통과, 1 위반(`<경로>: …` 한 줄씩), 2 사용·설정·환경 오류(repo 밖, git 실패, base 를 정하지 못함, 스크립트가 모르는 지문 판). UTF-8 이 아니거나 frontmatter 가 닫히지 않았거나 covers 값이나 항목이 `[` 로 시작해 `]` 로 끝나지 않는 페이지는 covers 를 알 수 없어 "covers 읽기 실패" 위반이다. covers 페이지(`--report` 는 `verified_at` 페이지까지)와 읽지 못한 페이지가 없으면 "검사 대상 아님" 을 내고 exit 0 이다.

**`--report` 의 CI 조건·한계**
- 미커밋 상태에서 적은 값이 CI 값과 같으려면 대조한 작업 트리를 그대로 commit 한다 — 부분 staging 없이, pre-commit 포매터가 파일을 바꾸지 않게, covers 에 걸린 untracked 파일은 commit 하거나 ignore 한다.
- CI 에 covers 에 걸린 untracked 산출물이 있으면 CI 에서만 STALE 이 나고 재확인으로 풀리지 않는다 — 산출물을 ignore 하거나 깨끗한 checkout 에서 돌린다.
- 지문이 기계마다 갈리는 경우: `.gitattributes` 의 줄 끝 규칙을 바꾼 뒤 renormalize commit 전, 대소문자만 다른 두 추적 경로(대소문자를 무시하는 파일시스템 — macOS·Windows 기본 — 과 Linux), 기계마다 다른 ignore 규칙(`core.excludesFile`·`.git/info/exclude` — untracked 집합이 바뀐다).
- 지문은 git 의 add 경로로 구해서 LFS 같은 clean 필터가 바뀐 covers 파일마다 돈다 — 큰 파일에서 느리고, 필터가 스스로 쓰는 것은 막지 않는다. `core.fsmonitor` 도 평소 `git status` 처럼 돈다. hook 으로 두었으면 사본에 대한 git 호출(update-index·ls-files)에서도 불린다. `true`(내장 데몬)면 status 가 데몬을 띄워 `$GIT_DIR/fsmonitor--daemon*` 를 만든다. 그 밖에 도구가 쓰는 것은 임시 디렉터리의 index 사본뿐이다 — 사본은 split index 로 쓰지 않고 `core.hooksPath` 의 hook(`post-index-change` 등)을 부르지 않으며, 진짜 index·shared index·object 는 그대로다.
- submodule gitlink 변경: `diff.ignoreSubmodules` 는 `git add` 가 따르지 않아 지문도 따르지 않는다. `submodule.<name>.ignore = all` 인 submodule 의 HEAD 이동은 지문에 들지 않는다. 지문은 `.git/config` 가 `.gitmodules` 를 덮은 유효값을 따른다. git 2.54.0 의 `git add -A` 는 `.gitmodules` 의 값만 따른다. 그래서 이 값을 `.gitmodules` 에만 두면 둘이 같다. `.git/config` 가 `all` 여부를 바꾸면(`.git/config` 에만 `all` 을 두거나, `.gitmodules` 의 `all` 을 `none` 으로 덮으면) 어느 쪽이든 commit 뒤 지문이 달라진다. 2.54 전의 `git add` 는 이 설정을 따르지 않아(2.54.0 릴리스 노트) `.gitmodules` 쪽도 어긋난다.

**알림 해소** — hook 은 상태를 두지 않아 풀릴 때까지 매 턴 끝에 다시 알린다.
1. 페이지 주장을 걸린 파일과 대조해 고친다. `verified_at` 이 있으면 대조 뒤 값도 옮긴다.
2. 변경이 주장과 무관하면 covers 를 좁힌다. `verified_at` 이 있으면 파일 집합이 바뀌어 지문이 달라지므로 값도 다시 적는다.
3. 이 repo 에서 hook 을 끄려면 `<wiki>/wiki-check.toml` 에 `[stale] stop_hook = false` 를 둔다(자체 게이트가 있는 repo 에 전역 등록이 겹칠 때). `--branch`·`--report` 에는 영향이 없다.

**hook 등록** — 이 skill 은 hook·CI 를 등록하지 않는다. 등록할 때 지킬 것:
- 스크립트 경로가 그 settings 를 쓰는 모든 머신에 있어야 한다. 없으면 python 이 exit 2 로 끝나고, Stop hook 의 exit 2 는 매 종료를 막는다. 플래그를 줄여 적거나(`--st`·`--stop-h`) 값을 붙이면(`--stop-hook=…`) exit 2 로 종료를 막지는 않지만, 판정하지 않고 매 턴 "인자 오류" `systemMessage` 만 낸다. 등록 명령에는 `--stop-hook` 을 그대로 쓴다.
- 시작점은 hook 입력 JSON 의 `cwd`(worktree 에 들어가면 그 worktree)이고, 상대 wiki 경로·`--config` 는 그 repo 루트 기준이다. wiki 경로에 `${CLAUDE_PROJECT_DIR}` 를 쓰지 않는다 — 세션 시작 위치에 머물러 worktree 안의 판정이 main checkout 의 wiki 를 본다. `docs/wiki` 처럼 탐색되지 않는 위치는 경로를 넘긴다. 단 wiki 경로·`--config` 는 전역(`~/.claude/settings.json`)에 등록할 때는 넘기지 않고, 그 repo 의 project settings 에 등록할 때만 넘긴다. 전역에 넘기면 그 경로가 없는 repo 마다 매 턴 `systemMessage` 가 뜬다(`--config` 는 covers 페이지가 있는 repo 에서). 끄는 `stop_hook = false` 도 없는 그 wiki·config 에 두어야 해서 끌 수 없다.
- 출력은 무출력·`additionalContext`·`systemMessage` 이고 언제나 exit 0 이다. stale 과 도구·환경 실패(base 를 정하지 못함, covers 페이지가 있을 때의 읽지 못한 페이지)가 겹치면 한 JSON 에 `hookSpecificOutput` 과 `systemMessage` 를 함께 담는다. 할 일이 없으면 무출력이다(`stop_hook_active`, subagent·workflow background 작업 대기, repo 밖, 탐색으로 찾은 wiki 없음, covers 페이지 0개, `stop_hook = false` 등). 인자로 넘긴 wiki 경로가 없으면 `systemMessage` 로 알린다. stale 이면 `hookSpecificOutput.additionalContext` 에 갱신할 페이지·걸린 파일·해소 방법을 10,000자 안으로 담는다. 도구·환경 실패(인자·stdin·config 오류, git 실패, base 를 정하지 못함, 읽지 못한 페이지(covers 페이지가 있을 때 — 없으면 무출력), 15초 초과)는 `systemMessage`("wiki_check stale: …")로 알린다 — 무출력으로 끝내면 게이트가 꺼져도 드러나지 않는다. `additionalContext` 는 Claude Code 2.1.163 부터 문서화된 형식이다.
- 원격 없는 repo 의 기본 브랜치와 unborn HEAD 에서는 작업 트리만 본다(경고 없음).

**Python** — config 없는 schema·stale(세 모드)은 3.9 부터 돈다. config 가 있으면 3.11+(`tomllib`)가 필요하다 — 3.9·3.10 에서 닫힌 모드는 exit 2, hook 은 `systemMessage` 로 버전을 알린다. 그래서 config 가 필요한 기능(규칙 조정, `stop_hook = false`, smoke)은 3.11+ 다. Windows 는 Windows 11·CPython 3.13·3.9 에서 테스트와 pipe 로 이은 hook(python·`uv run`·Node 부모)으로 확인했다(2026-10-01). 다만 Windows 에서 건너뛰는 테스트가 덮는 경로 — git 호출 시한·git 이 띄운 프로세스 정리·hook 시간 예산(가짜 git 을 sh 스크립트로 둔다), `--report` 지문이 여러 index 상태(충돌·intent-to-add·UTF-8 아닌 경로·typechange·디렉터리↔파일 전환)에서 `git add -A` 와 같은지(symlink 와 Windows 에서 못 쓰는 파일 이름을 쓴다), 지문 계산이 git hook 을 부르지 않는 것, 프로세스 그룹 신호, 표준 스트림 fd 가 닫힌 채 뜬 hook, symlink wiki 탐색·실행 비트·pty·읽기 권한·`*` 파일 이름 — 은 Windows 에서 확인하지 않았다. 콘솔 출력은 새 콘솔에서 예외 없이 끝나는 것까지만 봤고, Claude Code 에 등록해 돌려 보지는 않았다.

## 경계
- 페이지 write 는 메인만. `raw/` 원문은 적재 후 편집·삭제하지 않음(불변).
- 다른 repo 세션은 공용 wiki 에 쓰지 않는다(제안만). 공용 wiki 의 모든 write 는 공개 점검을 통과해야 한다.
- 자동 수정 안 함(lint 는 보고까지). 근거 없는 단정·추측 페이지 금지(CLAUDE.md §1).
- 코드 변경 아님 — dlc 와 분리. 현재 repo 에 wiki 가 없어도 공용 wiki 조회는 한다(쓰기는 비대상 + 사유).
