---
title: worklog-cwd-attribution — jira-worklog 시간 귀속을 줄 단위 cwd 기반 worktree별 분리로 개선
status: in_progress
started: 2026-07-22
updated: 2026-08-04
---

# Goal
한 세션이 여러 worktree 를 오갈 때 AI 작업시간이 **마지막에 머문 worktree 한 곳으로 전부 몰리는** 오귀속을 없앤다. 세션 로그의 **줄 단위 `cwd`** 로 이벤트를 worktree 별로 쪼개 귀속시켜, 오가더라도 각 worktree 가 실제로 자기 시간만 받게 한다. (이번 세션 산출물 = plan 만. 구현은 다음 세션.)

# Progress
- 2026-07-22: 문제 실증·원인 규명 완료(아래 Decisions 의 실측 근거). worktree `worklog-cwd-attribution` 생성, 이 plan 작성. 구현 미착수.
- 2026-07-22: plan commit `b9e0a28` → `origin/worklog-cwd-attribution` push(PR 미오픈). 작업 트리 clean, WIP 커밋 없음.
- 2026-08-04: 13일 방치 후 재개. worktree 재생성(`origin/worklog-cwd-attribution` 체크아웃), `origin/main@d38c70b` merge(`1b4d218`) — base 39커밋 뒤처짐 해소. PR 여전히 없음, plan-lint 통과.
- 2026-08-04: **plan-review NO-GO**(claude plan-reviewer + codex medium 병행). 핵심 blocker 를 메인이 독립 시뮬레이션으로 재현 — plan 의 longest-prefix 규칙을 실데이터에 적용하면 main 귀속이 **42.53h** 인데 main 의 실제 자기 cwd 몫은 **11.63h** 다(3.7배·+30.9h 과다). 원인: main 경로가 모든 worktree 경로의 조상이고 main 자신도 `git worktree list` 에 있어, **삭제된 worktree 의 cwd 가 매핑 실패가 아니라 main 으로 흡수**된다(`plans-sync` 4.66h·`main-autopull` 2.83h·`doc-slim` 2.74h·`ledger-fix` 2.62h …). 고치려던 오귀속이 되레 커지는 설계라 구현 중단. 시뮬레이션 스크립트는 scratchpad(`sim_attribution.py`).
- 2026-08-04: **영향 규모 실측** (`~/.claude/projects` 301파일 / timestamped user·assistant 34,281줄). ① `cwd` 결측 줄 **0개(0.00%)** → 결측 방어는 필요하되 실데이터엔 없음. ② 파일당 distinct cwd 분포 `{0:8, 1:265, 2:6, 3:12, 4:5, 5:2, 9:2, 14:1}` → **28개 파일(9.3%)이 2개 이상**, 최대 14개. 정상 단일 cwd 265개는 회귀 보호 대상.
- 2026-08-04: Codex rollout 362개 전수 스캔 → plan 의 Codex 근거 정정(아래 Decisions). 결론(현행 유지)은 유지.
- 2026-08-04: **전제 재실증**(13일 경과 검증). 이 세션 파일 `03f014b5….jsonl` 이 worktree 폴더에 있는데 121줄 중 45줄의 `cwd` 가 main — 폴더 단위 귀속이면 main 시간이 worktree 로 계상된다(결과 ① 재현). `drop-codegraph`·`risk-based-approval`·`rtk-rewrite-guard` slug 폴더는 jsonl 0개(세션이 떠남). `session_time.py` 모듈 docstring 은 여전히 "worktree 에서 실행하면 그 worktree 세션들만 잡힌다"는 틀린 전제를 명시 → 미해결 확인.

# Next
설계 결정 3건 확정 완료(2026-08-04). **수정된 `# Decisions` 로 plan-reviewer 재실행**(dlc 7단계 "구조 바뀌면 4~6 재실행") → 통과하면 TDD: `skills/jira-worklog/test_session_time.py`(신규, stdlib unittest — 기존 `test_worklog_scope.py` 스타일) 에 회귀 테스트부터 Red 확인.
이어받기: `/wt worklog-cwd-attribution` → `/c`.

# Decisions

## 문제 (실측으로 확정 — 재조사 불필요)
- 현재 귀속 단위는 **폴더**다: cwd → `project_slug()` → `~/.claude/projects/<slug>/` 폴더의 `*.jsonl` **전부**를 합산(`session_time.py:37-46,172-177`). 파일 **내용의 `cwd` 는 읽지 않는다** — 파서가 꺼내는 필드는 `timestamp` 와 `type` 뿐(`session_time.py:85-97`, `_sessionio.py:19-42`).
- 그런데 세션 파일은 **cwd 를 따라 폴더를 옮겨 다닌다**(세션 시작 위치 고정이 아님). 실측:
  - 세션 `7826dfb7`: 12:51 main 에서 시작 → 13:00 worktree 진입 → 종료. 파일은 **worktree 폴더**에 있고 main 구간 85줄까지 그 안에 들어있음.
  - 세션 `cf0d4e59`(knowledge_base): 10:49 main 시작 → 10:54~12:5x 를 CSTP1-2812 worktree 3곳에서 작업(1,191줄) → 13:01 main 복귀. 파일은 **main 폴더**(4.4MB, AI 시간 2h). CSTP1-2812 worktree 들의 slug 폴더는 **0개**(파일이 세션과 함께 떠났음).
  - 같은 세션 id 파일이 두 폴더에 동시 존재하지 않음 → 복사가 아니라 **이동**.
- 결과 ①: 오간 세션의 시간이 **마지막 위치 한 곳**에 전부 몰린다. 위 예시는 main(`ticket=(없음)`)으로 몰려 CSTP1-2812 worklog 는 0 — 2시간이 통째로 미등록.
- 결과 ②: A 에서 등록 후 B 로 이동해 다시 등록하면 **A 시간이 B 에 또 계산**된다(이중계상).
- `skills/e/SKILL.md:45-46` 의 "worklog 는 6단계 삭제·7단계 main 복귀 **전**에 실행 — 순서가 중요"는 이 이동 특성에 대한 기존 우회책이다(규약으로 막고 있을 뿐 구조는 취약).

## 접근
- **Claude 세션은 줄 단위 `cwd` 로 분리한다.** 각 줄에 `cwd` 필드가 존재함을 실측 확인 → 데이터는 이미 있다. 이벤트마다 cwd 를 읽어 소속 worktree 를 정하고, **worktree 별로 따로** interval 을 뽑아 union 한다.
- ~~**cwd → worktree 매핑은 longest-prefix**~~ → **2026-08-04 폐기 (plan-review blocker, 메인 시뮬레이션으로 재현)**. live `git worktree list` 만으로 longest-prefix 를 하면 **삭제된 worktree 의 cwd 가 조상인 main 으로 흡수**된다(main 42.53h vs 실제 몫 11.63h). main 은 모든 worktree 의 조상이자 자신도 목록에 있으므로 "매칭 실패 → 조상으로 폴백"이 곧 오귀속이다. billable 티켓 worktree 하위에 중첩 worktree 가 있던 실사례(`.../CSTP1-2812/ingest-pipeline`)에서는 **과다 등록**으로 이어진다.
  - **대체 규칙 (확정)**: ① 비교는 `Path.resolve()` 후 **경로 요소 단위**(`is_relative_to`) — 문자열 접두는 `/wt/foo` 가 `/wt/foobar` 에 걸린다. ② 매핑 후보는 live worktree 뿐 아니라 **`<root>/.claude/worktrees/<name>` 규약으로 식별한 historical bucket** 을 포함한다(`skills/wt/SKILL.md:29`). ③ **조상 폴백 금지** — 어떤 worktree 디렉토리 아래에도 안 들어가는 cwd 만 그 repo 루트(main)에 귀속한다. 즉 `<main>/.claude/worktrees/<X>` 는 X 가 살아있든 삭제됐든 **절대 main 으로 가지 않는다**.
  - **죽은 worktree 는 별도 bucket 으로 집계·표시한다 (2026-08-04 사용자 결정)**. `<root>/.claude/worktrees/<name>` 규약으로 이름을 복원해 dry-run 출력에 `(삭제됨)` 표시와 함께 시간을 보여주되, **Jira 등록은 하지 않는다**. 이유: drop 하면 billable repo 에서 중첩 worktree 를 지웠을 때 시간이 조용히 사라지는데, 표시해 두면 유실이 눈에 보이고 사후 수동 등록도 가능하다. `--worktree-path` 로 직접 등록하는 경로는 이번 스코프에서 제외(CLI 표면 증가).
- **worktree 경계를 넘는 interval 은 버린다**(직전 이벤트와 현재 이벤트의 worktree 가 다르면 skip). 이유: 그 구간은 "이동" 자체라 어느 쪽 것도 아니고, 어느 한쪽에 넣으면 이중계상 방향으로 틀어진다. 기존 제외 규칙(`max_gap` 초과, assistant→user 대기)은 그대로 유지.
  - **interval 발행 규칙 명시 (2026-08-04 추가 — plan-review #4)**: **파일별 타임라인을 유지한 채**(파일 = 독립 세션 불변식, `session_time.py:155-163`) **인접 이벤트 쌍의 귀속키가 같을 때만** interval 을 발행한다. 금지되는 두 오구현: (a) worktree 별로 이벤트를 먼저 걸러 스트림을 만들면 A→B→A 왕복이 60분 이내일 때 A 의 두 이벤트가 B 구간을 가로질러 이어져 **이중계상**된다. (b) 여러 파일 이벤트를 한 스트림으로 합치면 서로 다른 세션 사이 공백이 **허위 작업시간**이 된다.
  - **경계 폐기 손실 정량**(실측): 전체 100.26h 중 5구간 0.01h(**0.01%**). 무시 가능하나 dry-run 에 폐기량을 표시해 과소계상을 감시한다.
- ~~**탐색 범위는 repo 접두로 제한한다**~~ → **2026-08-04 근거 약화(plan-review), 재설계**. `project_slug` 는 `/`·`-`·`.` 를 모두 `-` 로 뭉개는 **비단사** 변환이라 slug 접두가 repo 경계를 보장하지 않고(`foo` 가 `foo-bar` 의 접두), 이 머신엔 repo 밖 worktree 도 실재한다. 대신 **폴더 이름(slug)으로 거르지 말고 파일 내용의 cwd 로 판정**한다 — 스캔한 파일의 cwd 가 대상 worktree 에 속하지 않으면 그 이벤트를 무시하면 되므로, slug 접두는 성능 최적화일 뿐 정확성 근거가 아니다. 성능이 문제되면 접두를 후보 필터로만 쓰고(누락 시 정확성 손실이 아니라 탐색 실패로 드러나게) 별도 측정한다.
- **`find_session_files` 의 비재귀 glob 은 유지한다**(2026-08-04 추가 — plan-review). `<slug>/<session-id>/subagents/*.jsonl` 에 subagent 트랜스크립트가 따로 쌓이는데, 탐색부를 손대며 재귀 glob 으로 바꾸면 부모의 tool_use→tool_result 구간과 **이중계상**된다. 시뮬레이션에서 `subagents` 폴더가 9.83h 로 잡힌 것이 그 증거(재귀 스캔한 탓 — 실제 코드는 비재귀라 무영향).
- **Codex 는 현행 유지**(파일 단위 귀속) — **결론 유지, 근거는 2026-08-04 정정**.
  - ❌ 폐기된 근거: "`session_meta.payload.cwd` 가 파일 첫 줄에만 있어 세션 중 이동을 나눌 수 없다". **틀렸다** — rollout 에는 `turn_context` 줄이 있고 여기에도 cwd 가 실린다(전수 362개 중 212개 파일이 보유).
  - ✅ 정정된 근거(실측): rollout **362개 전수 스캔에서 cwd 가 2개 이상인 파일이 0개**다. Codex 는 Claude 의 `EnterWorktree` 같은 세션 중 cwd 이동 경로가 없어, 파일 단위 귀속이 현재 데이터에서 무손실이다. 즉 "나눌 수 없어서"가 아니라 **"나눌 것이 없어서"** 현행 유지다.
  - 따라서 Codex 경로(`codex_session.py`)는 이번 변경에서 건드리지 않는다. 다만 SKILL.md 한계 명시는 **"Codex 는 세션 중 cwd 이동을 하지 않으므로 파일 단위로 충분"** 이라는 정확한 서술로 적는다(옛 서술을 그대로 옮기면 틀린 근거가 문서에 박힌다).
  - 향후 Codex 가 세션 중 이동을 지원하게 되면 `turn_context` 로 같은 분리를 적용할 수 있다(경로는 열려 있음).
- **호환**: 오가지 않은 세션(정상 케이스)은 결과가 달라지면 안 된다 — 기존 동작 회귀 테스트를 함께 둔다.

## 등록 안전장치 (2026-08-04 사용자 결정 — 이번 스코프 포함)
`upsert_worklog` 는 기존 `timeSpentSeconds` 를 새 계산값으로 **덮어쓴다**(`worklog_register.py:81-85`). 이번 변경은 귀속 값을 크게 바꾸므로, 코드 revert 로 되돌릴 수 없는 Jira 쪽 사고를 막을 최소 게이트를 **같은 브랜치에** 넣는다.
- `--register` 전 `(ticket, date, worktree, old, new)` diff 를 stdout 에 출력한다.
- **감소폭 임계 초과 시 등록 차단** — 기존값 대비 크게 줄면(임계는 구현 시 확정, 기본 보수적으로) 자동 등록을 멈추고 명시 플래그를 요구한다. 근거: 이번 변경의 정상 방향은 "과다분 감소"라 감소 자체는 정상이지만, 매핑 버그로 인한 대량 소실과 구분이 안 되므로 사람이 한 번 본다.
- 등록 시 **이전 값과 worklog id 를 로그에 남겨** 수동 복구 경로를 확보한다.
- 이 게이트는 측정 로직과 독립적으로 테스트 가능해야 한다(순수 판정 함수로 분리).

## 스코프 제외 (후속)
- **과거 오귀속 worklog 의 reconciliation** — 2026-08-04 사용자 결정으로 **후속 분리**. 이번은 앞으로의 측정을 바로잡는 데 집중한다. 이미 등록된 main 항목의 과다분은 자동으로 사라지지 않으므로, 필요해지면 별도 작업으로 감지·보고를 만든다(`# Deferred` 참조).

## 인접 작업과의 경계 (2026-08-04 확인 — 중복 아님)
- main 에 `worklog-per-worktree`(plan `status: done`, PR #101)가 머지돼 있다. 그 작업이 고친 것은 **등록 단계**의 문제 — 마커가 `(ticket, date)` 뿐이라 같은 티켓의 두 worktree 가 서로를 덮어쓰던 것을 worktree별 마커로 분리(`markers.py`·`worklog_register.py`, 테스트 `test_worklog_scope.py`).
- 이 plan 이 고치는 것은 **측정 단계**의 문제 — 세션 파일이 cwd 를 따라 이동해 시간 자체가 엉뚱한 worktree 로 집계되는 것(`session_time.py`). 마커를 아무리 잘 나눠도 입력 시간이 틀리면 소용없으므로 두 작업은 직교하고, 순서상 이쪽이 뒤에 오는 게 맞다.
- **회귀 주의**: `test_worklog_scope.py`(upsert scope·마커 검증)는 이번 변경 대상이 아니지만 통과 유지가 필요하다. 신규 `test_session_time.py` 는 측정 축만 담당.

# Key Files
- `skills/jira-worklog/jira_kit/session_time.py` — 핵심. `discover_sessions`/`find_session_files`(폴더 단위 탐색)와 `parse_message_events`/`ai_worklog_by_date`(cwd 미사용) 를 cwd 인지 방식으로 교체
- `skills/jira-worklog/jira_kit/git_util.py` — `list_worktrees` 재사용(신규 git 접근 추가 금지)
- `skills/jira-worklog/jira_worklog.py` — `process()`/`_days_for()` 가 worktree 1개 = 폴더 1개 전제. `--all` 은 한 번 스캔해 worktree 별로 나누는 쪽이 효율적
- `skills/jira-worklog/jira_kit/codex_session.py` — 변경 없음(한계 문서화 대상)
- `skills/jira-worklog/SKILL.md` — 동작 설명 갱신(귀속 기준, Codex 한계)
- `skills/e/SKILL.md:45-47` — "삭제·복귀 전 실행" 규약은 **유지**(삭제 후에는 대상이 사라져 영구 소실). 복귀 관련 서술만 정확히 갱신
- `skills/jira-worklog/jira_kit/worklog_register.py:63-85` — `upsert_worklog` 가 기존 시간을 덮어씀. 등록 게이트(old/new diff·감소폭 차단·이전값 로깅) 추가 지점
- `README.md:326` — 폴더 단위 귀속을 단언하는 서술. 문서 동기화 대상
- `.github/workflows/lint.yml` — 현재 node 테스트만 실행. python 테스트 추가 필요(안 하면 신규 테스트의 회귀 방지 효과 0)
- (신규) `skills/jira-worklog/test_session_time.py` — stdlib unittest, `uv run --no-project python test_session_time.py`
- (참고) scratchpad `sim_attribution.py` — longest-prefix 결함을 실증한 시뮬레이션. 구현 후 같은 스크립트로 개선 전후 비교 가능

# Acceptance
- [ ] 한 jsonl 안에 A→B→A 구간이 섞인 fixture 에서, A/B 가 각자 구간 시간만 받고 총합이 실제 시간을 넘지 않음 (테스트 통과)
- [ ] 중첩 worktree(`<wt>/<subwt>`) fixture 에서 하위 worktree 구간이 상위로 새지 않음 (longest-prefix 검증)
- [ ] ~~오가지 않은 단일 worktree 세션의 산출값이 변경 전과 동일~~ → **2026-08-04 정정(plan-review 가 반증)**. worktree 수준에서는 거짓이다 — 새 방식은 *다른* slug 폴더에 있는 파일에서도 자기 cwd 줄을 끌어오므로 값이 바뀌는 게 정상이다(실측: doc-slim 1.96h→2.63h). 기준을 **"단일 cwd 만 담긴 파일 fixture 에서 산출값이 변경 전과 동일"** 로 한정한다(테스트 통과).
- [ ] ~~knowledge_base 에서 CSTP1-2812 계열에 시간이 잡히고 main 의 2h 가 줄어듦~~ → **2026-08-04 정정(검증 불가)**. CSTP1-2812 worktree 는 이미 삭제됐고 `--all` 은 live 만 순회한다. 대체 기준: **live worktree 쌍**(main + 현재 worktree)으로 dry-run 시 ⓐ main 귀속이 42.53h→11.63h 수준으로 감소하고 ⓑ 죽은 worktree 시간이 main 에 흡수되지 않음을 수치로 확인(실행·관찰).
- [ ] `--all` dry-run 이 5초 이내 (실행·관찰 — "체감 저하 없음"은 측정 불가라 수치로 대체)
- [ ] dry-run 출력에 **경계 폐기량**(구간 수·시간)과 **미매칭 cwd 건수**가 표시됨 — 과소계상·매핑 누락을 조용히 넘기지 않기 위함 (실행·관찰)
- [ ] **삭제된 worktree 가 별도 bucket 으로 표시**되고 main 에 흡수되지 않음. 실데이터에서 `plans-sync`·`doc-slim` 등이 자기 이름으로 뜨고 main 은 자기 몫만 받음 (실행·관찰)
- [ ] 삭제된 worktree bucket 은 **등록 대상에서 제외**됨 (테스트 통과 — dry-run 표시와 등록 목록이 분리)
- [ ] `--register` 전 `(ticket, date, worktree, old, new)` diff 출력, **감소폭 임계 초과 시 등록 차단**, 이전값·worklog id 로깅 (테스트 통과 — 판정 함수 단위)
- [ ] 신규 `test_session_time.py` 가 **CI 에서 실행됨** — `.github/workflows/lint.yml` 에 python 테스트 추가(현재 node 만 돌아 회귀 방지 효과 0) (CI 통과)
- [ ] 폴더 단위 시맨틱을 단언하는 문서 전부 갱신: `session_time.py` 모듈 docstring·`jira_worklog.py` docstring·`skills/jira-worklog/SKILL.md`·`README.md:326`·`skills/e/SKILL.md:45-47` (문서 동기화 규약)
- [ ] SKILL.md 가 새 귀속 기준·Codex 한계를 반영 (문서 동기화 규약)

# Review Disposition
2026-08-04 plan-review (claude plan-reviewer + codex medium 병행). blocker 4건은 메인이 시뮬레이션으로 직접 재현 후 처분.

| # | finding | 처분 |
|---|---|---|
| 1 | longest-prefix 가 죽은 worktree 를 main 으로 흡수 (blocker) | **fix** — 규칙 폐기·대체 규칙 확정(`# Decisions`). 재현 완료(42.53h vs 11.63h) |
| 2 | Acceptance #4 검증 불가 (blocker) | **fix** — live worktree 쌍 기준으로 교체 |
| 3 | Acceptance #3 worktree 수준에서 거짓 (blocker) | **fix** — 단일 cwd fixture 수준으로 한정 |
| 4 | interval 발행 경계 미정의 (blocker) | **fix** — "파일별 타임라인 + 인접 쌍 동일 시에만 발행" 명시 |
| 5 | 문자열 접두가 경로 경계 무시·정규화 주체 미정 (major) | **fix** — `resolve()` + `is_relative_to` 확정. 정규화 헬퍼 승격 위치는 구현 시 결정 |
| 6 | Jira upsert 비가역 — rollback 부재 (major) | **결정 대기** — `# Blockers` 2 |
| 7 | `/e` 규약 상호작용이 반대로 서술됨 (major) | **fix** — `# Blockers` 하단에 정정 기록 |
| 8 | slug 접두 제한 근거 부실 (major) | **fix** — 정확성 근거에서 제외, 성능 최적화로 격하 |
| 9 | 경계 폐기량 미측정 (minor) | **fix** — 0.01% 실측·dry-run 표시를 Acceptance 에 추가 |
| 10 | `--all` 성능 기준 측정 불가 (minor) | **fix** — "5초 이내"로 수치화 |
| 11 | cwd 결측 시맨틱 미정 (minor) | **fix** — 결측은 상속 말고 경계로 간주 + 건수 보고. 실측상 timestamped user/assistant 줄엔 결측 0건 |
| 12 | subagent jsonl 재귀 glob 함정 (minor) | **fix** — 비재귀 유지를 `# Decisions` 에 명시 |
| 13 | 문서 동기화 범위 누락 (minor) | **fix** — `session_time.py` 모듈 docstring·`jira_worklog.py`·SKILL.md·README·e/SKILL.md 전부 대상 |
| 14 | 신규 테스트가 CI 에 안 걸림 (minor) | **fix** — `.github/workflows/lint.yml` 에 python 테스트 추가를 스코프에 포함 |
| 15 | 과거 오귀속 worklog reconciliation (codex) | **결정 대기** — `# Blockers` 3 |
| 16 | Codex 실측 주장 재현됨 | **no-change** — 이미 정정 반영 |

# Blockers
(없음 — 2026-08-04 결정 3건 확정으로 해소. 내용은 `# Decisions` 에 반영)

부수 정정(결정 불필요, 반영 완료): `skills/e/SKILL.md:45-47` 의 "삭제·복귀 전 실행" 규약은 **여전히 필수**다 — 새 방식은 *복귀* 후에는 정확해지지만 *삭제* 후에는 대상이 사라져 영구 소실이다. plan `# Deferred` 에 있던 "§8 규율 강제 필요성이 낮아진다"는 삭제 순서에 대해 틀렸다.

# Deferred
- CLAUDE.md §8 의 설명 부정확: "여러 worktree 를 오가면 **launch 프로젝트** 로그에 뭉친다" → 실측은 "**마지막 위치**로 뭉친다". 결론(한 세션 = 한 worktree)은 유효하나 근거 서술이 틀림. 운영 자산이라 승인 후 별건 처리(§1). 심각도 낮음(운영 규율은 그대로 안전 방향).
- ~~이 개선이 들어가면 §8 규율("한 세션 = 한 worktree")의 강제 필요성이 낮아진다~~ → **2026-08-04 정정(plan-review #7)**. **삭제 순서에 대해서는 틀렸다** — 새 방식은 *main 복귀* 후에는 정확해지지만, worktree 를 *삭제*하면 매핑 대상이 사라져(`--all` 은 live 만 순회) 시간이 영구 소실된다. 죽은 worktree bucket 표시로 유실이 보이게는 되지만 등록은 여전히 불가. 따라서 `/e` 의 "삭제 전 worklog 실행"은 계속 필수이고, 완화 가능한 것은 "복귀 전" 쪽뿐이다.
- **과거 오귀속 worklog reconciliation** (2026-08-04 사용자 결정 — 후속 분리). 이미 등록된 main 항목의 과다분은 이번 변경으로 자동 정정되지 않고, 새 worktree 항목이 더해져 티켓 총합이 부풀 수 있다. 실제 Jira 등록 이력이 있는지부터 확인한 뒤 필요하면 별도 작업. 심각도: 등록 이력이 없으면 0.
