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
- 2026-08-04: **plan-review NO-GO**(claude plan-reviewer + codex medium 병행). 핵심 blocker 를 메인이 독립 시뮬레이션으로 재현 — plan 의 longest-prefix 규칙을 실데이터에 적용하면 main 귀속이 실제 자기 몫의 **3.5배**가 된다. 원인: main 경로가 모든 worktree 경로의 조상이고 main 자신도 `git worktree list` 에 있어, **삭제된 worktree 의 cwd 가 매핑 실패가 아니라 main 으로 흡수**된다(`plans-sync` 4.57h·`doc-slim` 2.63h·`main-autopull` 2.61h·`improve-loop` 2.26h …). 고치려던 오귀속이 되레 커지는 설계라 구현 중단. 시뮬레이션 스크립트는 scratchpad(`sim_attribution.py`).
- 2026-08-04: **push + PR #118 생성** (`origin/worklog-cwd-attribution`, 14커밋). 측정 로직(4/7)만 담긴 중간 상태이고 CLI 미연결이라 기존 동작 불변 — PR 본문에 그 사실과 남은 5~7단계, `--register` 사용 금지 경고를 명시했다.
- 2026-08-04: **code-review 지적 수정 완료** (`af40cf0`). CONFIRMED Major 5건을 메인이 전부 재현한 뒤 수정 — 중첩 dead 흡수(이름→경로 비교), root 밖 live 유실(매칭 순서), Windows 소문자화(비교용/표시용 분리), 분류 성능(`WorktreeIndex` hoist+캐시, 20wt 5.61s→0.001s·실코퍼스 1.48s→0.55s), `ai_worklog_by_bucket` 테스트 0→5. 테스트 32개 통과, 기존 21개 회귀 없음, ruff 통과, 실코퍼스 bucket 결과·불변식 동일. 처분표는 `# Review Disposition`.
- 2026-08-04: **구현 2~4/7 완료** (`96de12f`) — `parse_message_events` 가 cwd 를 싣고, `bucket_intervals`(인접 쌍 동일 bucket 시에만 발행) + `worklog_from_intervals` + `ai_worklog_by_bucket`(단일 패스) 추가. gap/대기 판정은 `_is_work_gap` 술어로 뽑아 Codex 공용 `ai_intervals` 와 공유(규칙 중복 제거). 테스트 23개 통과(신규 9), 기존 21개 회귀 없음, ruff 통과, **CLI dry-run 출력 불변 확인**(아직 미연결). **실데이터 관찰**: 38파일 단일 패스 **1.48s**(기준 5초), main 9.72h·dead 24.88h(이름별 분리)·unmatched 28.20h·live 0.95h(등록가능 1개), 경계 폐기 99구간 0.41h(0.47%), 불변식 "bucket 합 63.75h ≤ 파일 union 87.41h" 성립. main 이 앞선 시뮬레이션 10.95h 보다 낮은 것은 새 경로가 `merge_intervals` 로 동시 세션 겹침을 union 제거하기 때문(기존 의미론과 동일, 시뮬레이션은 raw 합).
- 2026-08-04: **구현 1/7 완료** (`a10a433`) — `classify_cwd` + `BucketKind`/`Bucket` 순수 함수. TDD Red(ImportError) → Green. 신규 테스트 14개 통과, 기존 `test_worklog_scope.py` 21개 회귀 없음, ruff 통과. **실데이터 검증(실행·관찰)**: 이전 설계라면 main 이 10,728줄을 먹을 것을 3,514줄(자기 몫)로 분리, dead bucket 7,214줄이 이름별로 복원(`plans-sync` 869·`doc-slim` 824·`ledger-fix` 494 …), 타 repo 14,986줄은 unmatched 로 main 에 안 샘. 호출부 미연결이라 기존 동작 불변.
- 2026-08-04: **위 수치 정정 (2차 리뷰 B3 — 내 코퍼스가 오염돼 있었다)**. 1차 측정은 `rglob` 재귀 스캔이라 `<slug>/<sid>/subagents/*.jsonl` 이 섞였다. 프로덕션 `find_session_files` 는 **비재귀**(`session_time.py:172-177`)라 실제 가시 코퍼스는 **38파일**이다. 비재귀로 재측정: longest-prefix 적용 시 main **38.56h** vs 실제 자기 몫 **10.95h**. (폐기 수치: 42.53h/11.63h — 재귀 오염값이라 인용 금지.) **교훈: 측정 코퍼스를 프로덕션 탐색 규칙과 일치시킬 것.**
- 2026-08-04: **영향 규모 실측·정정** (프로덕션 비재귀 코퍼스 38파일 / timestamped user·assistant 25,914줄). ① `cwd` 결측 줄 **0개(0.00%)** → 결측 방어는 필요하되 실데이터엔 없음. ② 파일당 distinct cwd 분포 `{0:1, 1:8, 2:7, 3:12, 4:5, 5:2, 9:2, 14:1}` → **단일 cwd 는 8개뿐이고 29개(76%)가 다중 cwd**, 최대 14개. **앞서 적은 "단일 265개가 회귀 보호 대상, 다중은 9.3%"는 재귀 코퍼스 기준이라 틀렸다 — 실제로는 오귀속이 예외가 아니라 다수 케이스다.**
- 2026-08-04: Codex rollout 362개 전수 스캔 → plan 의 Codex 근거 정정(아래 Decisions). 결론(현행 유지)은 유지.
- 2026-08-04: **전제 재실증**(13일 경과 검증). 이 세션 파일 `03f014b5….jsonl` 이 worktree 폴더에 있는데 121줄 중 45줄의 `cwd` 가 main — 폴더 단위 귀속이면 main 시간이 worktree 로 계상된다(결과 ① 재현). `drop-codegraph`·`risk-based-approval`·`rtk-rewrite-guard` slug 폴더는 jsonl 0개(세션이 떠남). `session_time.py` 모듈 docstring 은 여전히 "worktree 에서 실행하면 그 worktree 세션들만 잡힌다"는 틀린 전제를 명시 → 미해결 확인.

# Next
**구현 1~4/7 + code-review 수정 완료** (`a10a433`, `96de12f`, `af40cf0`) — 측정 로직 완성, CLI 미연결이라 기존 동작 불변.

다음 액션: **순서 5단계** — 단일 패스 스캔으로 `process()` 재구성, dead/unmatched 표시(폐기량·미매칭 시간·main 기여 서브루트 목록 포함), `--all` 5초 실측. 그 뒤 6단계(등록 게이트), 7단계(CI·문서). 5단계에서 함께 처리할 이월 2건: UNMATCHED 를 "cwd 결측"과 "repo 밖"으로 분리 표시할지(C11), 파일 읽기 실패 건수를 `AttributionStats` 에 넣을지(C12).

---
2차 plan-review CONDITIONAL → blocker 4건(B1 repo 소속 선검증 / B2 최심 후보 선택 / B3 코퍼스 정정 / B4 등록 원자성) 을 `# Decisions`·`# Acceptance` 에 반영 완료. **구현 착수 가능.**

**구현 순서 (각 단계 독립 검증 가능 — 2차 리뷰 제안 채택)**:
1. 순수 매핑 함수 `classify_cwd(cwd, root, live_worktrees) -> Bucket` + 테이블 테스트(중첩·삭제·홈·타repo·컨테이너 경로·대소문자). **여기부터 TDD Red.** 기존 코드 변경 0줄.
2. `parse_message_events` 가 `(t, role, cwd)` 반환 — 단일 cwd fixture 회귀 고정.
3. 인접쌍 동일 bucket 일 때만 interval 발행 + bucket 별 union — A→B→A fixture, 경계 폐기량 카운터.
4. 집계 API `ai_worklog_by_bucket(...) -> dict[Bucket, list[DayWorklog]]`. 여기까지 CLI 무변경.
5. CLI 표시 — 단일 패스 스캔으로 `process()` 재구성, dead/unmatched 표시, `--all` 5초 실측.
6. 등록 사전계산 + 게이트(순수 판정 함수, 양방향 임계, all-or-nothing, rename 방어, 60초 하한 통일).
7. CI python 스텝(신규+기존 테스트) + 문서 동기화.
이어받기: `/wt worklog-cwd-attribution` → `/c`. **WIP 커밋 없음**(작업 트리 clean). 2026-08-04 **push 완료 + PR #118 (CI 통과)** — 다른 머신에서 그대로 이어받을 수 있다.

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
- ~~**cwd → worktree 매핑은 longest-prefix**~~ → **2026-08-04 폐기 (plan-review blocker, 메인 시뮬레이션으로 재현)**. live `git worktree list` 만으로 longest-prefix 를 하면 **삭제된 worktree 의 cwd 가 조상인 main 으로 흡수**된다(프로덕션 코퍼스 기준 main 38.56h vs 실제 몫 10.95h — 3.5배). main 은 모든 worktree 의 조상이자 자신도 목록에 있으므로 "매칭 실패 → 조상으로 폴백"이 곧 오귀속이다. billable 티켓 worktree 하위에 중첩 worktree 가 있던 실사례(`.../CSTP1-2812/ingest-pipeline`)에서는 **과다 등록**으로 이어진다.
  - **대체 규칙 (2026-08-04 2차 리뷰 B1·B2 반영해 확정 — 이 순서 그대로 구현)**. 순수 함수 `classify_cwd(cwd, root, live_worktrees) -> Bucket(kind, name)`, `kind ∈ {live, dead, main, unmatched}`:
    1. **정규화** — `Path.resolve()` + `os.path.normcase`(Windows·APFS 대소문자. 이 CLI 는 Windows 를 명시 지원한다 — `jira_worklog.py:30-34`).
    2. **repo 소속 선검증 (B1)** — `cwd` 가 `root` 아래가 **아니면 즉시 `unmatched`**. main 폴백 금지. 이 조건이 없으면 타 repo(`coin-trading-bot` 계열 ~29h)와 홈 디렉토리 cwd 가 전부 main 으로 흡수된다 — 1차 blocker 보다 큰 오귀속이 문구상 열려 있었다.
    3. **후보 수집** — live worktree 목록 + `<root>/.claude/worktrees/<name>` 규약으로 식별한 historical(삭제된) bucket. historical 은 **경로 문자열의 마지막 `.claude/worktrees/<name>` 출현** 기준으로 이름을 뽑고, 앵커는 `git worktree list` 의 main 경로로 고정한다(타 repo bucket 이 이름만으로 섞이지 않게).
    4. **최심(最深) 1개 선택 (B2)** — 후보 여러 개가 동시에 매치되면(`<root>` 와 `<root>/.claude/worktrees/A` 는 **항상** 함께 매치되고, `<A>/.claude/worktrees/B` 는 A 와도 매치된다) **경로 요소 수가 가장 깊은 하나**를 고른다. 이 규칙이 없으면 삭제된 중첩 worktree B 가 상위 live worktree A 로 흡수돼, 폐기 근거로 든 `.../CSTP1-2812/ingest-pipeline` 과다등록이 **대체 규칙에서도 그대로 재현**된다.
    5. **비교는 경로 요소 단위**(`is_relative_to`) — 문자열 접두는 `/wt/foo` 가 `/wt/foobar` 에 걸린다.
    6. 어떤 worktree 후보에도 안 걸리고 `root` 아래인 cwd만 `main`.
  - **규약 밖 경로의 잔여 위험 (닫지 못함, 완화만)**: `<root>/tmp-wt` 처럼 `.claude/worktrees/` 규약을 안 따르고 root 안에 있던 삭제 worktree 는 historical 복원이 불가해 main 으로 간다. 완화책으로 **main bucket 에 기여한 distinct cwd 서브루트 목록을 dry-run 에 출력**해 사람이 이상을 알아채게 한다.
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
  - **containment 비대칭 (2026-08-04 2차 리뷰 — 한계로 문서화)**: Claude 측은 `is_relative_to`(하위 디렉토리 포함)로 가는데 Codex 측은 정규화 **완전일치**다(`codex_session.py:66-75`). 실데이터에 worktree 하위 cwd 가 실재하므로(`<wt>/bot/build/test-results/test`, `<wt>/.claude/plans/…`) **같은 worktree인데 Claude 는 세고 Codex 는 빠지는** 비대칭이 생긴다. 죽은 bucket 표시에도 Codex 시간은 안 들어가 표시 총계가 과소된다. 이번 변경 대상은 아니되 SKILL.md 한계에 명시한다.
- **호환**: 오가지 않은 세션(정상 케이스)은 결과가 달라지면 안 된다 — 기존 동작 회귀 테스트를 함께 둔다.

## 등록 안전장치 (2026-08-04 사용자 결정 — 이번 스코프 포함)
`upsert_worklog` 는 기존 `timeSpentSeconds` 를 새 계산값으로 **덮어쓴다**(`worklog_register.py:81-85`). 이번 변경은 귀속 값을 크게 바꾸므로, 코드 revert 로 되돌릴 수 없는 Jira 쪽 사고를 막을 최소 게이트를 **같은 브랜치에** 넣는다.
- **all-or-nothing (B4 — 2차 리뷰)**. 현재 `_register()` 는 날짜별로 즉시 `upsert_worklog` 를 호출한다(`jira_worklog.py:93-103`). 게이트를 루프 안에 두면 3일치 중 3일째만 임계를 넘겨도 1·2일째는 이미 Jira 에 반영된 채 중단된다(revert 불가). 반드시 **① 전 날짜의 old/new/worklog id/marker 를 먼저 수집 → ② diff 출력 → ③ 게이트 판정 → ④ 통과한 경우에만 mutation 시작** 순서로 재구성한다.
- old 값 산출은 `upsert_worklog` 의 **author-scoping·legacy 마커 판정과 같은 순서**를 타야 diff 와 실제 갱신 대상이 일치한다(`worklog_register.py:52-63`, codex 지적).
- **양방향 임계 (2차 리뷰)** — 감소만 막으면 안 된다. 새 방식은 다른 slug 폴더의 줄까지 끌어와 값을 **올릴 수도** 있고(doc-slim 1.96h→2.63h), B1·B2 같은 매핑 버그의 대표 증상은 **과다 흡수**다. billable 에서는 과다 등록이 과소보다 위험하므로 증가·감소 양쪽에 임계를 건다.
- **rename 사각지대 방어 (2차 리뷰)** — 마커는 worktree 디렉토리명을 담는다(`markers.py:36-46`). 이름이 바뀌면 `_mine` 이 0건이라 `created` 경로로 가고 old 가 없어 감소 게이트가 침묵, 결과는 **이중계상**이다. 같은 `(ticket, date)` 에 **내 소유의 다른 worktree 마커**가 있는데 이번 마커가 0건이면 create 를 막고 경고한다.
- 등록 시 **이전 값과 worklog id 를 파일로 남긴다** — stdout 만이면 `/e` 자동 실행 시 유실된다. 위치는 `~/.claude/logs/jira-worklog-<date>.jsonl`(secret 없음, §8 준수).
- **비교값은 60초 하한 적용 후로 통일** — `seconds = max(day.seconds, 60)`(`worklog_register.py:64`)이라 하루가 여러 bucket 으로 쪼개지면 자투리마다 1분이 붙는다. old/new 를 하한 전후로 섞어 비교하면 유령 diff 가 난다.
- 이 게이트는 측정 로직과 독립적으로 테스트 가능해야 한다(**순수 판정 함수**로 분리).

## 죽은 bucket 의 등록 제외는 필터가 아니라 타입으로 강제 (2026-08-04 2차 리뷰)
등록 분기는 현재 `ticket` 유무만 본다(`jira_worklog.py:131-135`). 죽은 bucket 이름이 `CSTP1-1234-foo` 형태면 `extract_ticket` 이 티켓을 뽑아내 정상 worktree 와 구분되지 않는다. **`Bucket.kind`(또는 `registrable: bool`)를 `_register` 진입까지 전달하고 upsert 직전에 assert** 한다. `--all` 은 `register = args.register and not args.all`(`jira_worklog.py:179`)로 이미 안전하므로, 새는 경로는 **단일 worktree 실행** 쪽이다.

## `--all` 단일 패스는 성능이 아니라 요구사항 (2026-08-04 2차 리뷰)
현재 `process()` 는 worktree 마다 `discover_sessions(wt.path)` 를 호출한다(`jira_worklog.py:111`). cwd 판정을 위해 전체 코퍼스를 읽는 구조에서 이걸 유지하면 **worktree 수 N배 스캔**이 된다. 1패스 실측 약 1.2초라 5초 기준은 N≤4 에서만 성립 → **코퍼스를 한 번만 읽고 bucket 별로 나누는 단일 패스가 Acceptance 충족의 전제**다.

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
- [ ] 중첩 worktree(`<wt>/<subwt>`) fixture 에서 하위 worktree 구간이 상위로 새지 않음 — **최심 후보 선택 규칙 검증**(하위가 *삭제된* 경우도 포함. "longest-prefix 검증"이라는 옛 표현은 폐기된 규칙명이라 쓰지 않는다)
- [ ] `classify_cwd` 테이블 테스트: 타 repo cwd·홈 디렉토리·root 의 조상·worktrees 컨테이너 자체(`<root>/.claude/worktrees`)·대소문자 차이 → 각각 기대 bucket 으로 분류 (테스트 통과)
- [ ] ~~오가지 않은 단일 worktree 세션의 산출값이 변경 전과 동일~~ → **2026-08-04 정정(plan-review 가 반증)**. worktree 수준에서는 거짓이다 — 새 방식은 *다른* slug 폴더에 있는 파일에서도 자기 cwd 줄을 끌어오므로 값이 바뀌는 게 정상이다(실측: doc-slim 1.96h→2.63h). 기준을 **"단일 cwd 만 담긴 파일 fixture 에서 산출값이 변경 전과 동일"** 로 한정한다(테스트 통과).
- [ ] ~~knowledge_base 에서 CSTP1-2812 계열에 시간이 잡히고 main 의 2h 가 줄어듦~~ / ~~main 42.53h→11.63h~~ → **2026-08-04 두 번 정정**. ① CSTP1-2812 worktree 는 삭제돼 `--all`(live 만 순회)로 검증 불가. ② 대체안으로 쓴 고정 수치도 재귀 코퍼스 오염값인 데다, **실데이터는 매일 늘어 고정 수치는 내일 틀린다**(2차 리뷰 B3). 대체 기준 — **스냅샷 fixture + 불변식**:
  - `find_session_files(cwd, home)` 의 `home` 파라미터로 고정 corpus 를 주입해 재현 가능하게 한다.
  - 불변식 ① **main bucket 에 `<root>/.claude/worktrees/*` cwd 의 기여가 0**.
  - 불변식 ② **모든 bucket 시간의 합 ≤ 파일 union 총합**(이중계상 없음).
  - 불변식 ③ 타 repo·홈 cwd 의 main 기여가 0.
  - 실데이터 관찰은 회귀 기준이 아니라 **1회 sanity check** 로만: dry-run 에서 main 이 자기 몫 수준으로 줄고 죽은 worktree 가 자기 이름으로 뜨는 것을 눈으로 확인(수치를 Acceptance 에 박지 않는다).
- [ ] `--all` dry-run 이 5초 이내 (실행·관찰 — "체감 저하 없음"은 측정 불가라 수치로 대체)
- [ ] dry-run 출력에 **경계 폐기량**(구간 수·시간), **미매칭 cwd 건수와 시간**(건수만으로는 유실 규모가 안 보인다), **main bucket 에 기여한 distinct cwd 서브루트 목록**이 표시됨 (실행·관찰)
- [ ] **한 파일을 여러 bucket 처리에서 재파싱해도 각 이벤트는 정확히 한 bucket 에만 기여** (테스트 통과 — 불변식)
- [ ] 등록 게이트가 **all-or-nothing**: 마지막 날짜가 임계를 넘기면 앞 날짜도 등록되지 않음 (테스트 통과)
- [ ] 등록 게이트가 **증가 방향도** 차단하고, worktree rename 으로 마커가 안 잡힐 때 create 를 막음 (테스트 통과)
- [ ] 죽은 bucket 이 `CSTP1-1234-foo` 처럼 티켓 추출 가능한 이름이어도 **단일 worktree 실행에서 등록되지 않음** (테스트 통과 — 타입 강제)
- [ ] **삭제된 worktree 가 별도 bucket 으로 표시**되고 main 에 흡수되지 않음. 실데이터에서 `plans-sync`·`doc-slim` 등이 자기 이름으로 뜨고 main 은 자기 몫만 받음 (실행·관찰)
- [ ] 삭제된 worktree bucket 은 **등록 대상에서 제외**됨 (테스트 통과 — dry-run 표시와 등록 목록이 분리)
- [ ] `--register` 전 `(ticket, date, worktree, old, new)` diff 출력, **감소폭 임계 초과 시 등록 차단**, 이전값·worklog id 로깅 (테스트 통과 — 판정 함수 단위)
- [ ] 신규 `test_session_time.py` **와 기존 `test_worklog_scope.py` 둘 다** CI 에서 실행됨 — `.github/workflows/lint.yml` 에 python 스텝 추가(현재 node 전용이라 기존 테스트조차 안 돈다 → "통과 유지 필요"가 자동 보장되지 않음) (CI 통과)
- [ ] 폴더 단위 시맨틱을 단언하는 문서 전부 갱신: `session_time.py` 모듈 docstring·`jira_worklog.py` docstring·`skills/jira-worklog/SKILL.md`·`README.md:326`·`skills/e/SKILL.md:45-47` (문서 동기화 규약)
- [ ] SKILL.md 가 새 귀속 기준·Codex 한계를 반영 (문서 동기화 규약)

# Review Disposition
2026-08-04 plan-review (claude plan-reviewer + codex medium 병행). blocker 4건은 메인이 시뮬레이션으로 직접 재현 후 처분.

| # | finding | 처분 |
|---|---|---|
| 1 | longest-prefix 가 죽은 worktree 를 main 으로 흡수 (blocker) | **fix** — 규칙 폐기·대체 규칙 확정(`# Decisions`). 재현 완료(38.56h vs 10.95h — 2차 리뷰 B3 로 코퍼스 정정 후 값) |
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

2026-08-04 plan-review **2차 (CONDITIONAL)**. 개정본에 남은 결함.

| # | finding | 처분 |
|---|---|---|
| B1 | 매핑 규칙에 "cwd ∈ repo root" 선검증 누락 → 타repo·홈 cwd 가 main 으로 (blocker) | **fix** — `classify_cwd` 2단계로 명시 |
| B2 | 다중 후보 매치 시 선택 규칙 부재 → 삭제된 중첩 worktree 가 상위로 흡수 (blocker) | **fix** — 최심 1개 선택 명시 |
| B3 | 내 실측 코퍼스가 재귀라 오염(302파일) — 프로덕션은 비재귀 38파일 (blocker) | **fix** — 비재귀 재측정(38.56h/10.95h), 분포 통계 정정, Acceptance 고정수치 → fixture+불변식 |
| B4 | 등록 게이트가 날짜 루프 안이면 부분 등록 잔존 (blocker) | **fix** — all-or-nothing 명시 |
| B5 | 게이트가 감소만 막고 증가 무방비 (major) | **fix** — 양방향 임계 |
| B6 | worktree rename → 마커 미스 → create 로 이중계상 (major) | **fix** — 다른 worktree 마커 존재 시 create 차단 |
| B7 | 죽은 bucket 등록 제외가 필터라 티켓형 이름에서 샘 (major) | **fix** — `Bucket.kind` 타입 강제 + upsert 직전 assert |
| B8 | Codex 정확일치 vs Claude `is_relative_to` 비대칭 (major) | **문서화** — SKILL.md 한계에 명시(코드 변경 없음) |
| B9 | `--all` N배 스캔이면 5초 기준 미달 (major) | **fix** — 단일 패스를 요구사항으로 승격 |
| B10 | 60초 하한이 bucket 분할로 총량 미세 증가 (minor) | **fix** — old/new 비교를 하한 적용 후로 통일 |
| B11 | 중간 경로 cwd(`<root>/.claude/worktrees`) 소속 미정의 (minor) | **fix** — `classify_cwd` 테이블 테스트에 fixture 고정 |
| B12 | Windows·APFS 대소문자 정규화 미명시 (minor) | **fix** — `normcase` 명시 |
| B13 | 기존 `test_worklog_scope.py` 도 CI 미포함 (minor) | **fix** — 둘 다 추가 |
| B14 | old 산출이 author-scoping·legacy 마커와 같은 순서여야 (codex) | **fix** — 등록 게이트 절에 명시 |
| B15 | 규약 밖 삭제 worktree(`<root>/tmp-wt`)는 복원 불가 (누락 시나리오) | **완화만** — main 기여 cwd 서브루트 목록 출력 |
| B16 | `_split_by_date` DST 무한루프 소지 (기존 결함) | **defer** — `# Deferred`, 이번 변경이 만든 것 아님 |

2026-08-04 **code-review** (claude code-reviewer + codex high 병행), 대상 `a10a433`+`96de12f`. Critical 0, CONFIRMED Major 5 — **전부 메인이 직접 재현 후 fix**(`af40cf0`).

| # | finding | 처분 |
|---|---|---|
| C1 | 중첩 dead 가 동명 상위 live 로 흡수 → `registrable=True` 과다등록 (major) | **fix** — 이름 비교 → 경로 깊이 비교. 재현·수정 확인 |
| C2 | root 밖 live worktree 가 UNMATCHED 로 유실(기존 대비 회귀) (major) | **fix** — live 매칭을 root 검증보다 먼저. 재현·수정 확인 |
| C3 | Windows `normcase` 소문자화 → `extract_ticket` 실패로 조용한 미등록 (major) | **fix** — 비교용/표시용 분리, 이름은 원본 대소문자 보존 |
| C4 | 분류가 O(이벤트×worktree) → `--all` 5초 위협(20wt 5.61s 실측) (major) | **fix** — `WorktreeIndex` 로 hoist+캐시. 5.61s→0.001s, 실코퍼스 1.48s→0.55s |
| C5 | `ai_worklog_by_bucket` 테스트 0개, "파일 경계 미연결" 불변식 미고정 (major) | **fix** — 테스트 5개 추가(파일간 미연결·union·stats 누적·읽기실패 skip·dead 등록제외) |
| C6 | POSIX `normcase` 는 항등인데 docstring 이 APFS 도 덮는다고 서술 (minor) | **fix** — docstring 정정, macOS 대소문자 미지원을 명시 |
| C7 | `_dead_worktree_name` off-by-one + 도달 불가 분기 (minor) | **fix** — 재작성하며 해소(이름 뒤따르는 마지막 출현으로 명시) |
| C8 | 새 API 타입 힌트 누락, `live_worktrees` 계약 불명 (minor) | **fix** — `Iterable[str \| Path]` 등 명시. `list_worktrees()` 가 `Worktree` 객체를 주는 footgun 대비 |
| C9 | malformed cwd(NUL) → `ValueError` 전파로 전체 집계 중단 (plausible) | **fix** — `(OSError, ValueError)` → UNMATCHED 격리 + 테스트 |
| C10 | `parse_message_events` 시그니처 breaking 정책 미기록 (minor) | **fix** — 외부 소비자 0(rg 전수 확인)이라 시그니처 변경 채택, 여기 기록으로 갈음 |
| C11 | UNMATCHED 가 "cwd 결측"과 "타 repo"를 한 bucket 으로 합침 (minor) | **defer to step 5** — dry-run 표시 설계 시 분리 여부 결정. 현 코퍼스 결측 0건이라 무해 |
| C12 | 파일 읽기 실패를 로그 없이 삼킴 (nit) | **defer to step 5** — `AttributionStats` 에 읽기 실패 건수 추가를 표시 설계와 함께 |
| C13 | 인접쌍 순회 골격이 두 함수에 중복 (nit) | **wontfix** — 반환 형태(단일 리스트 vs bucket 딕셔너리)가 달라 통합하면 되레 복잡. simplify 체크에서 재판단 |

refuted 6건(`ai_worklog_by_date` 동작 변경·Codex 2-튜플 파손·bucket 이중계상 등)은 리뷰가 반증 근거와 함께 기록 — 별도 조치 없음.

# Blockers
(없음 — 2026-08-04 결정 3건 확정으로 해소. 내용은 `# Decisions` 에 반영)

부수 정정(결정 불필요, 반영 완료): `skills/e/SKILL.md:45-47` 의 "삭제·복귀 전 실행" 규약은 **여전히 필수**다 — 새 방식은 *복귀* 후에는 정확해지지만 *삭제* 후에는 대상이 사라져 영구 소실이다. plan `# Deferred` 에 있던 "§8 규율 강제 필요성이 낮아진다"는 삭제 순서에 대해 틀렸다.

# Deferred
- CLAUDE.md §8 의 설명 부정확: "여러 worktree 를 오가면 **launch 프로젝트** 로그에 뭉친다" → 실측은 "**마지막 위치**로 뭉친다". 결론(한 세션 = 한 worktree)은 유효하나 근거 서술이 틀림. 운영 자산이라 승인 후 별건 처리(§1). 심각도 낮음(운영 규율은 그대로 안전 방향).
- ~~이 개선이 들어가면 §8 규율("한 세션 = 한 worktree")의 강제 필요성이 낮아진다~~ → **2026-08-04 정정(plan-review #7)**. **삭제 순서에 대해서는 틀렸다** — 새 방식은 *main 복귀* 후에는 정확해지지만, worktree 를 *삭제*하면 매핑 대상이 사라져(`--all` 은 live 만 순회) 시간이 영구 소실된다. 죽은 worktree bucket 표시로 유실이 보이게는 되지만 등록은 여전히 불가. 따라서 `/e` 의 "삭제 전 worklog 실행"은 계속 필수이고, 완화 가능한 것은 "복귀 전" 쪽뿐이다.
- **기존 결함(이번 스코프 밖)**: `_split_by_date` 의 `next_midnight` 계산(`session_time.py:139-146`)은 DST 로 자정이 존재하지 않는 타임존에서 무한루프 소지가 있다. 이번 변경이 만든 것이 아니고 Asia/Seoul 은 DST 가 없어 현 사용에선 안 터진다 — 별건.
- **과거 오귀속 worklog reconciliation** (2026-08-04 사용자 결정 — 후속 분리). 이미 등록된 main 항목의 과다분은 이번 변경으로 자동 정정되지 않고, 새 worktree 항목이 더해져 티켓 총합이 부풀 수 있다. 실제 Jira 등록 이력이 있는지부터 확인한 뒤 필요하면 별도 작업. 심각도: 등록 이력이 없으면 0.
