---
title: worklog-cwd-attribution — jira-worklog 시간 귀속을 줄 단위 cwd 기반 worktree별 분리로 개선
status: in_progress
started: 2026-07-22
updated: 2026-07-22
---

# Goal
한 세션이 여러 worktree 를 오갈 때 AI 작업시간이 **마지막에 머문 worktree 한 곳으로 전부 몰리는** 오귀속을 없앤다. 세션 로그의 **줄 단위 `cwd`** 로 이벤트를 worktree 별로 쪼개 귀속시켜, 오가더라도 각 worktree 가 실제로 자기 시간만 받게 한다. (이번 세션 산출물 = plan 만. 구현은 다음 세션.)

# Progress
- 2026-07-22: 문제 실증·원인 규명 완료(아래 Decisions 의 실측 근거). worktree `worklog-cwd-attribution` 생성, 이 plan 작성. 구현 미착수.

# Next
구현 착수 시 첫 액션: `skills/jira-worklog/test_session_time.py`(신규, stdlib unittest — 기존 `skills/wt/test_heal_submodules.py` 스타일) 에 **회귀 테스트부터** 작성. 케이스: 한 jsonl 안에 worktree A 구간 → B 구간이 섞여 있을 때 A/B 가 각자의 시간만 받고 합이 이중계상되지 않을 것(Red 확인 후 구현).

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
- **cwd → worktree 매핑은 longest-prefix**. `git worktree list --porcelain`(`git_util.list_worktrees`) 의 path 목록과 비교해 가장 긴 접두 일치를 고른다. 이유: cwd 가 하위 디렉토리(`<wt>/skills/jira-worklog`)이거나 **worktree 안에 worktree 가 중첩**된 실사례(`.../CSTP1-2812/ingest-pipeline`)가 있어 단순 일치·짧은 접두로는 오귀속된다.
- **worktree 경계를 넘는 interval 은 버린다**(직전 이벤트와 현재 이벤트의 worktree 가 다르면 skip). 이유: 그 구간은 "이동" 자체라 어느 쪽 것도 아니고, 어느 한쪽에 넣으면 이중계상 방향으로 틀어진다. 기존 제외 규칙(`max_gap` 초과, assistant→user 대기)은 그대로 유지.
- **탐색 범위는 repo 접두로 제한한다.** worktree 는 `<main>/.claude/worktrees/<name>` 아래라 모든 관련 폴더의 slug 가 `project_slug(main경로)` 로 시작한다 → `~/.claude/projects/<mainslug>*/` 만 스캔하면 된다(전체 projects 스캔 회피). 이 접두에 안 걸리는 worktree 는 `git worktree list` 의 각 path slug 를 추가로 포함해 보완.
- **Codex 는 현행 유지**(파일 단위 귀속). `session_meta.payload.cwd` 가 파일 첫 줄에만 있어 세션 중 이동을 나눌 수 없다(`codex_session.py:43-58`). 한계를 SKILL.md 에 1줄 명시. Codex 가 세션 중 이동을 어떻게 기록하는지는 ❌ 미확인 — 구현 전 rollout 파일 1건 확인만 하고, 불가면 그대로 둔다.
- **호환**: 오가지 않은 세션(정상 케이스)은 결과가 달라지면 안 된다 — 기존 동작 회귀 테스트를 함께 둔다.

# Key Files
- `skills/jira-worklog/jira_kit/session_time.py` — 핵심. `discover_sessions`/`find_session_files`(폴더 단위 탐색)와 `parse_message_events`/`ai_worklog_by_date`(cwd 미사용) 를 cwd 인지 방식으로 교체
- `skills/jira-worklog/jira_kit/git_util.py` — `list_worktrees` 재사용(신규 git 접근 추가 금지)
- `skills/jira-worklog/jira_worklog.py` — `process()`/`_days_for()` 가 worktree 1개 = 폴더 1개 전제. `--all` 은 한 번 스캔해 worktree 별로 나누는 쪽이 효율적
- `skills/jira-worklog/jira_kit/codex_session.py` — 변경 없음(한계 문서화 대상)
- `skills/jira-worklog/SKILL.md` — 동작 설명 갱신(귀속 기준, Codex 한계)
- `skills/e/SKILL.md:45-46` — "main 복귀 전 실행" 근거가 약해지면 문구 재검토(삭제 아님 — Codex 는 여전히 파일 단위)
- (신규) `skills/jira-worklog/test_session_time.py` — stdlib unittest, `uv run --no-project python test_session_time.py`

# Acceptance
- [ ] 한 jsonl 안에 A→B→A 구간이 섞인 fixture 에서, A/B 가 각자 구간 시간만 받고 총합이 실제 시간을 넘지 않음 (테스트 통과)
- [ ] 중첩 worktree(`<wt>/<subwt>`) fixture 에서 하위 worktree 구간이 상위로 새지 않음 (longest-prefix 검증)
- [ ] 오가지 않은 단일 worktree 세션의 산출값이 변경 전과 동일 (회귀 테스트 통과)
- [ ] 실제 데이터 검증: `cf0d4e59` 가 있는 knowledge_base 에서 `--all` dry-run 시 CSTP1-2812 계열 worktree 에 시간이 잡히고 main 의 2h 가 그만큼 줄어듦 (실행·관찰)
- [ ] `--all` 실행 시간이 체감 가능하게 나빠지지 않음 (4.4MB 파일 포함 스캔, 실행·관찰)
- [ ] SKILL.md 가 새 귀속 기준·Codex 한계를 반영 (문서 동기화 규약)

# Blockers
(없음)

# Deferred
- CLAUDE.md §8 의 설명 부정확: "여러 worktree 를 오가면 **launch 프로젝트** 로그에 뭉친다" → 실측은 "**마지막 위치**로 뭉친다". 결론(한 세션 = 한 worktree)은 유효하나 근거 서술이 틀림. 운영 자산이라 승인 후 별건 처리(§1). 심각도 낮음(운영 규율은 그대로 안전 방향).
- 이 개선이 들어가면 §8 규율("한 세션 = 한 worktree")의 강제 필요성이 낮아진다 — 규칙 완화 여부는 구현·검증 후 별도 판단.
