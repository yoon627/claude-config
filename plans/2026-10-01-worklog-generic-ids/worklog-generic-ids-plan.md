---
title: worklog-generic-ids — jira-worklog 의 회사 식별자를 일반 표기로 바꾸고 미사용 기본 티켓 패턴을 없앰
status: in_progress
started: 2026-10-01
updated: 2026-10-02
---

# Goal
`skills/jira-worklog` 에 남은 비공개 목록 용어(8개 파일 51줄)를 일반 표기로 바꾼다. 기본 티켓 패턴은 범용 Jira 키 하나(`config.py`)만 남기고, 조직 고유 패턴은 머신별 설정(`JIRA_TICKET_PATTERN`·`jira-kit.toml`)에 둔다고 문서화한다. 이슈 #206 의 마지막 항목이다.

# Intent
- Problem: 공개 repo 인데 `skills/jira-worklog` 의 기본 티켓 패턴(`worklog_core.py`)·주석·SKILL.md 예시·테스트 fixture 에 회사 티켓 키 접두어가, SKILL.md 예시 1곳에 회사 repo 이름이 남아 있다. 2026-10-01 대조 결과 repo 전체의 적중은 이 8개 파일 51줄이 전부다. `pre-commit-check` 비공개 용어 가드는 추가 줄만 봐서 기존 줄은 잡지 못한다(#206 댓글 2026-09-30). 사용자 결정(2026-10-01 "지금 정리"): 예시·fixture 를 일반화하고, 기본 패턴은 일반 패턴으로, 회사 패턴은 머신별 설정으로 옮긴다. 동작이 바뀌는 지점은 plan 에서 다시 확인한다.
- Constraints:
  - 비공개 용어와 사용자 경로를 repo 파일·plan·커밋 메시지·PR·이슈에 쓰지 않는다(CLAUDE.md §11). 이 plan 에도 쓰지 않는다.
  - 런타임 동작은 바꾸지 않는다. 확인 결과 바뀌는 런타임 경로가 없다(# Decisions).
  - 과거 이력은 재작성하지 않는다(#206 배경 — filter-repo·force push 안 함).
  - 일반 표기는 기존 표기에 맞춘다: README 의 `ABC-1234-…`·"실측 한 티켓"·"실측(회사 repo)", `test_exit_contract.py` 의 `ABC-123-demo`.
- Out of scope:
  - `skills/jira-task` — 기본 패턴이 이미 범용이고(`jira_task.py:30`) 적중 0.
  - 다른 머신의 `~/.jira-kit` 설정 — 각 머신에서 사용자가 정한다.
  - 이미 Jira 에 등록된 worklog 마커 — 마커 형식과 런타임 추출이 그대로라 영향 없다.
  - 브랜치 fallback 의 범용 패턴 오탐(`fix-UTF-8-…`→`UTF-8`, `feature/ISO-8601`→`ISO-8601` — 리뷰어 재현) — #98 부터의 기존 동작이고 이 변경과 무관하다. 머신별 패턴으로 좁히면 줄어든다.
- Open questions:
  - (열림) 이 머신에 회사 패턴을 설정할지. 지금은 범용 기본값으로 돈다 — 확인 범위는 전역 설정까지다(`~/.jira-kit` 에 toml 없음, 전역 `.env` 에 키 없음, 환경변수 없음). `load_config` 는 실행 cwd 위로 프로젝트 `.env`·`jira-kit.toml` 도 찾는데(`jira_worklog.py` 가 `load_config(Path.cwd())` — `/e` 가 main 에서 이름 인자로 돌리면 main checkout 위) 회사 repo 쪽은 확인하지 않았다. 회사 패턴은 #98 이후 런타임에 적용된 적이 없어, 설정하면 이 머신의 모든 repo 와 jira-task 에서 자동 추출이 좁아지는 새 동작이다. repo 변경과 분리해 Report 에서 묻는다.
- 분할: 없음 — 단위 후보가 1개뿐이다. fixture·주석·예시 일반화와 미사용 기본값 제거는 모두 jira-worklog 의 회사 식별자 제거라는 한 목적이고, 어느 일부만으로는 적중 0 이 되지 않는다.

# Progress
- 2026-10-01: worktree 생성(base `origin/main@41de939`). Explore — 적중 8개 파일 51줄 확정(목록 대조 스크립트, 용어 미출력). 런타임 경로·설정 소스·도입 이력(`aae9d6d` #98) 확인. 관련 wiki decision 없음. draft plan.
- 2026-10-01: plan 리뷰 CONDITIONAL(강 4·약 9) → 반영(# Review Disposition). Codex 는 이 세션에서 크레딧 소진(세션 마커)이라 병행 생략. 기존 테스트 수 기준값 실측: scope 29, gate 19, session_time 71.
- 2026-10-02: 구현 — `test_ticket_pattern.py`(변경 전 코드에서도 통과 확인), `extract_ticket` 기본값 제거, fixture·주석·예시 일반화, SKILL.md·README 문서. Green: 비공개 용어 0(추적 파일·diff·untracked), 직접 실행 Ran 29·19·71·12·2 모두 OK(`-W error`). 코드 리뷰는 Workflow 로 세 관점(코드·문서 주장·낡은 참조) + nit 아닌 지적마다 반박 검증(agent 8개, Codex 미가용) → minor 3건 real, 나머지 nit — 반영(# Review Disposition).
- 2026-10-02: simplify — 손댈 것 없음(코드 변경은 미사용 기본값 제거뿐). 최종 검증은 Workflow 로 격리 runner(명령 9개 모두 exit 0, `verify.sh` `ALL PASS (skip: install-codex-skill.test.ps1)`, python 축에 새 파일 ok, Ran 29·19·71·12·2)와 문서 재대조(nit 2 → 반영) 병렬. 마지막 편집 뒤 `verify.sh` 재실행 같은 결과, 비공개 용어 0(추적·diff·untracked·커밋 메시지 초안). evidence gate 1–5 충족, runner 보고와 판정 일치 → DONE.

# Next
- 커밋 → commit-check → Report(머신 설정 Open question 질문 포함) → `/e merge`. PR 제목·본문은 게시 전 목록 대조 0(Acceptance 1).
- 머지 뒤: #206 완료 댓글·close — 외부 쓰기라 AskUserQuestion, 게시 전 본문 대조 0.

# Decisions
- 관련 wiki decision 없음 — `wiki_search.py jira-worklog ticket pattern 티켓 패턴`(공용 76쪽, repo wiki 없음). 두 기본값은 스킬 도입 커밋 `aae9d6d`(#98)에서 온 그대로이고 이후 바꾼 결정이 없다(`git log -L`). `worklog-per-worktree` plan 의 "티켓 패턴이 단일 프로젝트라 수용" 리스크 판단은 런타임 패턴과 무관한 같은 이름 worktree 충돌 건이라 이 변경으로 바뀌지 않는다.
- 동작 변화: 런타임 없음. `jira_worklog.py:92-95` 는 항상 `args.ticket_pattern or config.ticket_pattern` 을 넘기고, config 기본값은 #98 부터 범용 `[A-Z][A-Z0-9]+-\d+`(`config.py:24`)다. 바뀌는 것은 pattern 없이 부를 때의 `extract_ticket` 기본값뿐이고 그렇게 부르는 곳은 없다(`rg extract_ticket`, 리뷰어 재확인).
- 기본 패턴의 단일 소스는 `worklog_core.DEFAULT_TICKET_PATTERN`(범용)으로 두고 `config.py` 가 import 한다 → **`extract_ticket` 의 `pattern` 을 필수 인자로 바꾸고 `worklog_core` 의 기본값을 지우는 안으로 변경** (이유: plan 리뷰 약한 우려 1 — 식별자가 남은 원인 자체가 프로덕션에서 쓰지 않는 두 번째 기본값이 갈라진 것이다. 호출부는 `jira_worklog.py:93,95` 두 곳뿐이고 둘 다 pattern 을 넘긴다. 처음 기각 사유였던 "공개 함수 시그니처 변경"은 내부 모듈이라 근거가 약했다). 기본값은 `config._DEFAULT_TICKET_PATTERN`(범용) 하나만 남는다. 기각: `worklog_core` 단일 소스 + config import(A안) — 프로덕션에서 쓰지 않는 기본값과 그 기본값만을 위한 테스트가 남는다.
- 일반 표기: 티켓 `ABC-1234`, worktree 이름 `ABC-1234-abc`/`-def`/`-alpha`/`-beta`, 대소문자 보존 테스트 `ABC-2812-Foo`. fixture 의 키는 마커 안의 불투명한 문자열이라 값이 바뀌어도 테스트 의미가 같다(리뷰어 확인: `markers.py` 는 끼워 넣기만, `test_register_gate.py` 의 `beta` 검사·`test_session_time.py` 의 대소문자 검사도 동일). 프로젝트 키에 숫자가 든 형태(회사 키의 모양)는 새 테스트가 `AB1-12-fix` 로 덮는다.
- 머신별 설정 문서: SKILL.md·README 에 `~/.jira-kit/jira-kit.toml` 의 `[worklog]` `ticket_pattern = '…'`(작은따옴표 리터럴 문자열 — 큰따옴표면 `\d` 가 `TOMLDecodeError`, 2026-10-01 실측) 또는 `JIRA_TICKET_PATTERN` 을 적고, 조직 고유 값은 공개 repo 에 넣지 않는다고 쓴다. 리뷰 반영으로 더 적는 것: `[worklog]` 테이블 헤더 필수(`flatten_toml` 은 그 테이블만 읽음), cwd 위로 찾은 프로젝트 `jira-kit.toml` 이 있으면 전역 파일을 통째로 대체(병합 아님), 우선순위 `--ticket-pattern` > 환경변수 > `.env`(프로젝트 > 전역) > toml > 기본값, jira-task 도 같은 키를 읽어 함께 좁아진다, TOML 파싱 오류는 exit 2 라 `/e` 6단계가 실패하고 7단계 정리가 생략된다. SKILL.md:71 의 `max_gap` 은 TOML 키 `max_gap_minutes` 로 같은 줄에서 고친다(이번에 TOML 키 이름을 문서화하는 줄이라).
- 테스트: 새 `test_ticket_pattern.py` 에 두 동작만 — 설정이 없으면 범용 키를 anchored 로 뽑는다, 문서의 TOML 리터럴 문자열 설정이 기본값을 대체한다. 기존 테스트 파일은 관심사(종료 코드·게이트·시간·scope)가 달라 넣지 않는다. → **둘 다 변경 전에도 통과하는 특성화 테스트로 변경** (이유: B안에서는 런타임 기본값이 원래 범용이라 Red 가 날 동작이 없다. `extract_ticket` 기본값 제거는 기존 테스트(`test_exit_contract.py` 가 `_ticket_for` 경로로 pattern 을 넘겨 추출)가 회귀를 덮는 단순 리팩토링 — CLAUDE.md §7 예외). TOML 문자열은 raw string(Python 3.12+ SyntaxWarning 방지).
- 주석: `jira_worklog.py:91` 의 "기존 … 브랜치 worktree 는 회귀 없다" 절은 변경 경위 서술(§6)이라 일반화하지 않고 지운다. `test_session_time.py:368` 의 "대문자 패턴" 주석은 범용 기본값에서도 맞아 그대로 둔다.
- rollback: forward fix 로만 한다. revert 커밋은 회사 키 줄 50개와 회사 repo 줄 1개를 다시 추가해 §11 위반이고, 목록이 있는 머신에서는 pre-push 가드에도 걸린다. 런타임·Jira·git 이력은 바뀌지 않아 되돌릴 동작이 없다 — 실패 가능성은 import·테스트 깨짐뿐이고 같은 PR 안에서 고친다. 머신 설정을 바꾸게 되면 그 줄을 지우면 원복된다.
- 가장 위험한 단계: 훅이 보지 않는 공개 채널 — PR 제목·본문과 #206 댓글(README Install D 의 한계). 게시 전마다 같은 대조(0)를 거친다.
- ⚠️ 묶음 intent 를 만들지 않는다 — §10 트리거 3("기존 plan 의 `# Deferred` 에서 새 plan 시작")과 상충할 수 있음 — 출처는 두 곳(`worklog-followups` # Deferred 110행, `wiki-private-repo` Out of scope 18행)이고 둘 다 #206 으로 넘긴 역참조다. `worklog-followups` 는 이미 닫힌 무관 묶음 `worklog-deletion-safety` 에 `intent:` 로 속해 있고 §10 의 `intent:` 는 스칼라라 트리거 3 절차(선행 plan 에 `intent:` 1줄 추가)를 적용할 수 없다. #206 의 앞선 plan(`private-terms-guard`·`wiki-private-repo`)도 묶음 없이 끝났다. 그래서 #206 이 묶음 역할을 하고, 머지 뒤 #206 완료 댓글·close 를 # Next 에 둔다.
- 커밋 단위: 1개 — 모든 변경이 jira-worklog 의 회사 식별자 제거라는 한 목적이다.

# Acceptance
1. 비공개 용어 적중 0 — 로컬 목록 대조 스크립트(scratchpad, 용어 미출력)로 worktree 의 추적 파일 전체를 센다. 통과: "합계: 0 파일 0 줄". 커밋 직전 diff·untracked 대조도 0. 커밋 메시지·PR 제목·본문·#206 댓글 초안도 게시 직전에 같은 대조로 0(훅 밖 공개 채널).
2. 기본 패턴이 범용이고 두 번째 기본값이 없다 — `test_ticket_pattern.py`: 설정 없는 `resolve_config` 의 패턴이 `ABC-123-demo`→`ABC-123`, `AB1-12-fix`→`AB1-12` 를 anchored 로 뽑는다(특성화 — 변경 전후 모두 통과). `worklog_core.py` 에 기본 패턴이 없고 `extract_ticket` 호출부가 전부 pattern 을 넘긴다(`rg extract_ticket`).
3. 머신별 설정이 기본값을 대체한다 — 같은 파일: 문서와 같은 TOML 리터럴 문자열(`[worklog]` `ticket_pattern = 'XY-\d+'`)을 `tomllib`→`flatten_toml`→`resolve_config` 로 읽으면 `XY-7-demo`→`XY-7`, `ABC-123-demo`→`None`. 통과: OK.
4. 회귀 없음 — `python3 skills/jira-worklog/<file>` 직접 실행 시 Ran 수가 기준값과 같고(scope 29, gate 19, session_time 71) 새 파일은 Ran 2. `bash scripts/verify.sh` 의 `== python tests ==` 축에 새 파일이 `ok` 로 나오고, 마지막 줄이 `ALL PASS` 또는 `ALL PASS (skip: install-codex-skill.test.ps1)`(이 skip 은 pwsh 부재로 인한 기존 skip, 이 변경과 무관).
5. 문서 동기화 — SKILL.md 와 README jira-worklog 절에 기본 패턴(범용)과 머신별 설정 방법(`[worklog]` 헤더·작은따옴표 TOML·`JIRA_TICKET_PATTERN`·프로젝트 toml 이 전역을 대체·jira-task 와 키 공유)이 있고, README 파일 트리에 `test_ticket_pattern.py` 줄이 있다. 관찰: `rg` 로 해당 줄 확인.

# Review Disposition
- [⚠️ self-flag] 묶음 intent 미생성 — resolved: 결론 유지, 근거를 리뷰어가 확인한 사실(닫힌 무관 묶음 소속·스칼라 `intent:`·출처 2곳의 #206 역참조)로 보강. 트리거 3 문구의 모호성은 운영 자산이라 Report 제안(# Deferred).
- [강1] README 파일 트리에 새 테스트 줄 누락 — fix: Acceptance 5·Key Files.
- [강2] 훅 밖 공개 채널(PR·#206 댓글) 대조 없음 — fix: Acceptance 1, Decisions "가장 위험한 단계".
- [강3] rollback 부재, revert 는 식별자 재공개 — fix: Decisions "rollback".
- [강4] #206 을 닫는 담당 없음·⚠️ 근거 불완전 — fix: # Next 에 머지 뒤 댓글·close(AskUserQuestion), ⚠️ 줄 근거 보강.
- [약1] 필수 인자 안 기각 사유가 약함 — fix: B안으로 변경(Decisions).
- [약2] Acceptance 4 축 이름·실행 여부 — fix: `== python tests ==`, 직접 실행 Ran 수·기준값.
- [약3] Red 가 ImportError 로 날 위험 — fix: B안 전환으로 새 이름 import 가 없어지고 Red 대상도 없다(특성화).
- [약4] 문서 정확성(헤더·대체·우선순위·jira-task·exit 2·`max_gap`) — fix: Decisions "머신별 설정 문서".
- [약5] Open question 전제가 전역 설정까지만 확인됨 — fix: 확인 범위와 새 동작임을 Intent 에 명시.
- [약6] 잘못된 정규식이 traceback 으로 끝남 — defer: # Deferred(기존 동작·범위 밖).
- [약7] `jira_worklog.py:91` 경위 서술 — fix: 그 절 삭제.
- [약8] 테스트의 TOML 문자열 — fix: raw string.
- [약9] Codex 생략 사유 미기록 — fix: # Progress.
- [CR minor] README jira-worklog 절에 프로젝트 `jira-kit.toml` 이 전역을 대체한다는 설명이 없음(Acceptance 5, 세 관점 중복) — fix: README 문장에 한 구절.
- [CR minor] 큰따옴표의 `\b` 같은 TOML 이스케이프는 오류 없이 다른 문자가 되고, 맞지 않는 패턴은 exit 0 skip 이라 `/e` 가 정리를 계속한다(시간 등록 불가) — fix: SKILL.md 에 그 경로와 미리보기 `ticket=` 확인 안내. 검증자: 경로 자체는 기존이고 이번 문서가 처음 권하는 것.
- [CR minor] plan Progress·Next·updated 가 구현 상태와 어긋남 — fix.
- [CR nit] 우선순위 문장이 jira-task 에도 `--ticket-pattern` 이 있는 것처럼 읽힘·jira-task 는 매치 없으면 skip 이 아니라 오류·파싱 오류도 함께 받음 — fix: 문장 순서·한정, 직접 확인(`jira_task.py:141-143,156,540,597`).
- [CR nit] `worklog_core` docstring 이 기본값 위치를 `Config.ticket_pattern` 으로 지칭 — fix: `config._DEFAULT_TICKET_PATTERN` 으로.
- [CR nit] 새 테스트 docstring 이 단언하지 않는 사실을 설명 — fix: 단언 내용으로 고침(파싱 오류 단언 추가안은 stdlib 동작을 시험하는 덤이라 기각).
- [CR nit] plan Open question 의 "대상 worktree 의 cwd" 는 실제로 실행 cwd — fix.
- [CR nit] README 의 "범용 Jira 키" 가 밑줄·한 글자 키를 포함하는 것처럼 과장 — fix: README 에 정규식을 그대로 적음.
- [CR nit] SKILL.md(toml 만)와 README(toml 또는 환경변수)의 권장 위치가 다름 — fix: SKILL.md 에 `JIRA_TICKET_PATTERN` 병기.
- [최종 nit] SKILL.md 의 미리보기 `ticket=` 확인 안내는 세션 기록이 없는 worktree 에선 머리줄이 안 나와 따를 수 없음(`jira_worklog.py:228-230`) — fix: 전제 한 구절.
- [최종 nit] 새 테스트 모듈 docstring 의 "두 경로" 가 테스트하지 않는 환경변수 경로까지 덮는 것처럼 읽힘 — fix: "기본값과 toml 설정 두 가지".
- [CR nit 범위 밖] jira-task SKILL.md 가 `jira-kit.toml` 을 설정 소스로 적지 않음 · `config.load_config` docstring 의 우선순위가 toml 층과 대체 의미를 빼먹음 · 공개 스킬의 기본 타임존이 특정 지역 — defer: # Deferred.

# Deferred
- 잘못된 `ticket_pattern` 정규식이 `re.error` traceback·exit 1 로 끝난다(`jira_worklog.py:92-95` 가 잡지 않음, jira-task 는 ConfigError 로 감쌈). 문서가 사용자 패턴 설정을 권하게 되므로 ConfigError(exit 2)로 감싸는 후속을 검토한다 — 심각도 낮음.
- §10 묶음 intent 트리거 3 의 문구가 "이슈로 넘긴 Deferred"·"선행 plan 이 이미 다른 묶음 소속"인 경우를 다루지 않는다 — CLAUDE.md 운영 자산이라 Report 제안만 — 심각도 낮음.
- jira-task SKILL.md 의 설정 우선순위(41·49행)가 `jira-kit.toml`(프로젝트, 없으면 `~/.jira-kit`) 을 빼먹었다 — 코드는 4순위로 읽는다(`jira_task.py:141-158`) — 심각도 낮음.
- `jira_kit/config.py` `load_config` docstring(163행)의 우선순위가 `.env` 와 toml 층, 프로젝트 toml 의 전역 대체를 구분하지 않는다 — SKILL.md 가 더 정확하다 — 심각도 낮음.
- 공개 스킬 jira-worklog 의 기본 타임존이 `Asia/Seoul` 고정이다(`config.py:25`). jira-task 는 설정이 없으면 시스템 로컬 tz 를 쓴다 — 동작 변경이라 별도 검토 — 심각도 낮음.
- 공용 wiki 적립 후보(`~/.claude` main 세션에서 /wiki ingest): Claude Code 도구 인자(Write 내용·Bash 명령)의 백슬래시-u 이스케이프 텍스트는 제어문자·단독 surrogate 를 빼고 실제 문자로 바뀐다(개행 직전 U+FEFF 는 사라짐) · 근거: 2.1.285·2.1.286 로컬 재현(비공개 코드 없음) · 출처 공개.

# Key Files
- `skills/jira-worklog/jira_kit/worklog_core.py` — 회사 기본 패턴 삭제, `extract_ticket` 의 `pattern` 필수, docstring 예시 일반화.
- `skills/jira-worklog/jira_kit/config.py` — `_DEFAULT_TICKET_PATTERN`(범용)이 유일한 기본값, 주석의 회사 키 예시를 일반 예시로.
- `skills/jira-worklog/jira_kit/markers.py` — docstring 예시 일반화.
- `skills/jira-worklog/jira_worklog.py` — `_ticket_for` 주석 일반화(경위 절 삭제).
- `skills/jira-worklog/SKILL.md` — 실측 예시 2줄 일반화 + 머신별 패턴 설정 안내 + `max_gap_minutes`.
- `skills/jira-worklog/test_worklog_scope.py`·`test_register_gate.py`·`test_session_time.py` — fixture 일반화.
- `skills/jira-worklog/test_ticket_pattern.py` — 신규(Acceptance 2·3).
- `README.md` — jira-worklog 절 1문장 + 파일 트리 `test_ticket_pattern.py` 줄.

# Blockers
- 없음.
