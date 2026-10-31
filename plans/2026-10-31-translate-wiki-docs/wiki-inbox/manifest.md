# wiki docs/wiki-inbox 규칙 목록 (translate-wiki-docs)

공용 wiki 3eaa4f4 의 `docs/wiki-inbox.md`(51줄) 기준. 한 줄 = 한 조항(한정어도 조항의 일부). 번역 대조는 `locations-en.txt`(`<id> | <영어 인용>`, 인용 여러 개는 ` ‖ `, 각 인용은 파일 안에서 한 번, manifest 순서대로). 이 manifest 는 번역 초안 전에 만든다. 제목 줄은 check.json `headings` 가 고정한다.

## 머리말
- P.1 다른 repo 세션이 MCP `wiki_submit` 으로 남긴 요청을 이 wiki 에 반영하는 절차
- P.2 요청은 `repoctx-server` 를 돌리는 머신의 로컬 inbox(`~/.local/share/repoctx-server/inbox`, 항목당 JSON)에 쌓인다, 처리는 두 경로
- P.3 매일(무인): launchd 가 `wiki-inbox` 스크립트를 정해진 시각에 돌린다
- P.4 스크립트는 `source: public` 항목만 `claude -p` 에 넘기고, git·검사·push·PR 은 스크립트가 한다, A 절이 그 세션의 절차
- P.5 수동: 사람이 대화형 세션에서 처리, `source: private` 항목은 이 경로로만, B 절
- P.6 이 파일은 자동 로드되지 않는다 — 무인 실행의 프롬프트가 읽으라고 지시하고, 수동 처리 때는 세션이 직접 Read
- P.7 페이지 형식·불변 규칙은 `WIKI.md` 가 단일 소스, 여기는 inbox 처리만

## 항목 형식
- F.1 JSON 형식: `format`·`id`(16 hex)·`created`(UTC ISO)·`kind`(update|request)·`title`(한 줄)·`body`·`source`(public|private)·`pages`(category/name 목록)
- F.2 `update`: 기록할 지식(검증된 도구·플랫폼·라이브러리 동작, 전역 자산의 교훈)과 근거, 초안 페이지가 들어 있을 수 있다
- F.3 `request`: 다른 세션이 wiki 에서 찾지 못한 것, 무엇을 왜 찾았는지가 body 에
- F.4 `pages`: 제출한 세션이 관련 있다고 본 페이지 키(없을 수 있고, 틀릴 수 있다)

## A. 무인 실행
- A.1 작업 디렉토리는 스크립트 전용 clone, 브랜치는 `origin/main` 에서 딴 `inbox/<날짜>`
- A.2 `--restricted` 모드 — 도구는 Read·Edit·Write·Glob·Grep·WebSearch·WebFetch 뿐(셸·MCP 없음), 파일 도구는 clone 과 항목 디렉토리 밖을 읽지 못한다
- A.3 git 은 스크립트가 한다
- A.4 1 `WIKI.md` 를 읽고, 항목 디렉토리(프롬프트가 알려 준다)의 JSON 을 모두 읽는다
- A.5 2 항목을 주제별로 묶고, 같은 사실을 말하는 항목은 하나로
- A.6 3 각 묶음 처리 — 관련 페이지를 Grep(`pages/`·`index.md`)으로 찾고, 기존 페이지 갱신을 먼저, 새 페이지는 맞는 페이지가 없을 때만
- A.7 `update`: 근거가 공개적으로 확인 가능한지(공식 문서·공개 이슈·release note·재현 명령과 출력), 없거나 확인 불가면 반영하지 않고 `deferred`, 필요하면 WebSearch·WebFetch 로 공식 출처 확인해 `sources` 에
- A.8 `request`: 기존 페이지로 답이 되면 그 페이지의 index 요약을 찾기 쉽게 고치거나 보강, 없으면 공식 출처 조사해 쓰거나 보강, 믿을 근거가 없으면 `deferred`(무엇을 찾았고 무엇이 없었는지 한 줄)
- A.9 기존 서술과 어긋나면 조용히 덮어쓰지 않는다 — 새 근거가 더 확실하면 고치고 날짜·출처를 남기고, 판단이 안 서면 `> [!conflict]` callout 으로 둘 다(`WIKI.md` 불변 규칙 3)
- A.10 4 페이지 규칙(`WIKI.md`): frontmatter 필수 키, `updated` 를 오늘로, 다른 페이지로 가는 링크 2개 이상(`[[a-z0-9-]]` 이름만 링크로 센다), 새 페이지는 다른 페이지 하나 이상에서 링크를 받고 `index.md` 의 그 category 절에 한 줄
- A.11 모델 버전·목록은 `anthropic-claude-models` 에만
- A.12 5 공개 점검: 회사·조직·고객명, 내부 도메인·호스트·IP, 비공개 repo 의 이름·경로·내부 도구명, 티켓 키, 사람 이름 → 일반 표현("company repo")으로, 그래도 의미가 남지 않으면 `rejected`
- A.13 항목이 `public` 이라고 신고했어도 다시 본다
- A.14 6 `log.md` 끝에 이번 실행 항목 하나: `## [YYYY-MM-DD] ingest | inbox (<적용 수>/<전체>)` 와 바뀐 페이지마다 한 줄
- A.15 7 수정은 `pages/`·`index.md`·`log.md` 만, 파일을 지우지 않는다(스크립트가 그 밖의 변경·삭제를 거부)
- A.16 8 마지막에 두 파일(위치는 프롬프트가 알려 준다)
- A.17 `result.json`: 읽은 모든 항목 id → `{"status": "applied" | "deferred" | "rejected", "note": "<한 줄>"}`, 빠진 항목은 대기로 남아 다음 실행에서 다시 본다
- A.18 `summary.md`: PR 본문, 항목마다 한 줄(제목 · 상태 · 바뀐 페이지), 비공개 정보·사람 이름을 쓰지 않는다
- A.19 스크립트가 그 뒤 검사: `result.json` 의 id(내보낸 항목만), 변경 경로, `check_links`·`wiki_check schema`, 이번에 더한 줄의 자격 증명·비공개 용어
- A.20 페이지를 하나도 바꾸지 않았으면 `applied` 는 `deferred` 로 보관
- A.21 하나라도 실패하면 push 하지 않고 항목은 대기로 남는다(로그: `~/Library/Logs/repoctx-wiki-inbox.log`)

## B. 수동 처리
- B.1 `~/.claude/wiki` main 세션에서 한다(공용 wiki 쓰기 규칙 그대로 — CLAUDE.md §11)
- B.2 1 대기 목록: `~/.local/share/repoctx-server/current/bin/repoctx-server inbox list`(`--source private`·`--json` 가능), 항목 파일은 inbox 디렉토리에
- B.3 2 `private` 항목: 공개 가능한 사실만 뽑아 일반 표현으로, 비공개 코드·대화에서만 확인되는 내용은 공용 대상이 아니다
- B.4 커밋 전 diff 를 사용자에게 보이고 확인받는다
- B.5 3 반영은 평소 공용 wiki 적립과 같다(페이지·`index.md`·`log.md`, main 직접 커밋, push 는 요청 시)
- B.6 4 닫기: `repoctx-server inbox archive --status applied|deferred|rejected --note "<한 줄>" <id>…`, 닫은 항목은 `inbox/done/<YYYY-MM>/` 에 상태와 함께 남는다
- B.7 5 public 항목을 지금 무인 경로로: `launchctl kickstart gui/$(id -u)/local.repoctx.wiki-inbox`
- B.8 6 무인 실행 로그에 `unreadable inbox item` 이 있으면 그 파일을 열어 고치거나 지운다(건너뛸 뿐 처리되지 않는다)
- B.9 `run … holds …` 가 매일 반복되면 그 pid 가 정말 살아 있는지 확인

## 다른 파일이 가리키는 표지
- 절 표지 "A"·"B" — `repoctx/scripts/wiki-inbox.sh` 프롬프트("follow its section A"), `repoctx/README.md`("`docs/wiki-inbox.md` B 절"). 제목의 `A.`·`B.` 그대로.
- 상태값 `applied`·`deferred`·`rejected`, 파일 `result.json`·`summary.md` — 스크립트·`repoctx-server inbox archive` 가 글자로 읽는다. 그대로.
- 출력 문자열 `unreadable inbox item`·`run … holds …` — `repoctx-server`·`wiki-inbox.sh` 가 찍는 글자(원래 영어). 그대로.
- `log.md` 항목 머리 `## [YYYY-MM-DD] ingest | inbox (…)` — WIKI.md log 형식. `ingest | inbox` 그대로, 자리표시자만 영어.
- `skills/wiki/SKILL.md`·CLAUDE.md 는 이 파일을 가리키지 않는다(공용 wiki `WIKI.md`·`repoctx/` 만).

## 핵심 문구
`wiki_submit` · `repoctx-server` · `~/.local/share/repoctx-server/inbox` · `wiki-inbox` · `source: public` · `claude -p` · `source: private` · `WIKI.md` · `update` · `request` · `pages` · `origin/main` · `--restricted` · Read·Edit·Write·Glob·Grep·WebSearch·WebFetch · `deferred` · `sources` · `> [!conflict]` · `[[a-z0-9-]]` · `anthropic-claude-models` · "company repo" · `rejected` · ## [YYYY-MM-DD] ingest | inbox ( · `result.json` · `{"status": "applied" | "deferred" | "rejected", "note": "<one line>"}` · `summary.md` · `check_links`·`wiki_check schema` · `~/Library/Logs/repoctx-wiki-inbox.log` · `~/.claude/wiki` · CLAUDE.md §11 · `~/.local/share/repoctx-server/current/bin/repoctx-server inbox list` · `--source private`·`--json` · `repoctx-server inbox archive --status applied|deferred|rejected --note "<one line>" <id>…` · `inbox/done/<YYYY-MM>/` · `launchctl kickstart gui/$(id -u)/local.repoctx.wiki-inbox` · `unreadable inbox item` · `run … holds …`
