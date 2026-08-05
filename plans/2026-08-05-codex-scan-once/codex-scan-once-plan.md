---
title: codex-scan-once — Codex rollout 스캔 1회화 + 귀속 규칙을 Claude 경로와 통일
status: in_progress
started: 2026-08-05
updated: 2026-08-05
---

# Goal
Codex rollout 을 worktree 마다 재-glob 하지 않고 **한 번만 스캔**하고, 귀속을 Claude 경로와 같은 `WorktreeIndex.classify` 로 통일한다. 그 결과 `jira_worklog.py` docstring 의 "코퍼스는 한 번만 스캔해 worktree 별로 나눈다" 서술이 두 소스 모두에 대해 참이 된다.

# Progress
- 2026-08-05: worktree 생성(base `origin/main@47702f1`). Explore 로 실코퍼스 실측 — rollout 374개·1회 스캔 0.10s·live worktree 4개(=4회 재스캔). 성능 이득은 ~0.3s 로 작지만, **cwd 가 worktree 하위인 rollout 26건이 정확일치 필터에 걸려 아무 버킷에도 안 잡히는 비대칭**을 발견. 26건은 전부 삭제된 worktree(`ledger-fix`·`doc-slim` 등) 세션이라 등록 시간 영향은 0, 표시(DEAD)에서만 누락.
- 2026-08-05: 사용자 판정 — "classify 로 통일" 채택.

- 2026-08-05: TDD Red→구현→Green(44 tests, +9). 동시점 구/신 실행 대조 — live worktree 줄 **완전 동일**(등록 시간 불변 확정), 차이는 DEAD 목록 `33개→35개` 한 줄뿐.

- 2026-08-05: 자체 리뷰(code-reviewer subagent 는 세션 지시로 미호출 — 메인 직접) — `merge_intervals` 가 내부 정렬하므로 append 순서 의존 없음 확인(`session_time.py:294`). simplify 2건 반영: 죽은 `tzinfo` import 제거, main 루프 변수 `bucket`/`intervals` 섀도잉 해소. CI 스위트 `ALL PASS`(ruff 포함), 재대조에서도 차이는 DEAD 목록 한 줄뿐.

# Next
커밋 → PR → 머지 → worktree 정리.

# Decisions
- **귀속을 `WorktreeIndex.classify` 로 통일** (이유: Claude 경로가 이미 이 분류기를 유일 소스로 쓰고(`jira_worklog.py:311` 주석 "bucket 키는 인덱스가 단일 소스"), Codex 만 정확일치를 쓰면 같은 cwd 가 소스별로 다른 버킷이 된다. 실측 26건이 그 비대칭에 걸려 조용히 사라지고 있었다).
- **등록 시간 불변이 전제** (이유: 실측상 하위-cwd 26건은 전부 DEAD 버킷행. LIVE 버킷 하위-cwd 는 0건이라 `--register` 결과는 안 바뀐다. 바뀌면 회귀로 본다). → 구/신 동시 실행으로 **확정**.
- **효과 크기를 실측으로 낮춰 기록** (이유: "26건 누락"은 파일 수이지 시간이 아니다. 실제 시간 순증은 **180초**뿐 — 대부분의 rollout 구간이 같은 worktree 의 Claude 구간과 겹쳐 union 에 흡수된다(이중계상 없음이 정상). 구조적 이득은 **Codex 로만 작업한 worktree 2개**(`env-bootstrap`·`audit-fixes`)가 그동안 통째로 안 보이다가 표시되기 시작한 것).
- **union 지점은 날짜 분할 전 유지** (이유: 기존 `process()` 주석의 이중계상 방지 조건. 병합을 `main()` 의 `per_bucket` 으로 올리되 `worklog_from_intervals` 호출 전이라 조건 유지).
- **Codex 구간을 `per_bucket` 에 합치는 이유**: `_report_unregistrable` 이 그 dict 만 보므로, 합쳐야 DEAD worktree 의 Codex 시간이 표시된다(이번 결함의 실질 수정).
- `find_codex_session_files`(단일 worktree 정확일치)는 **삭제** (이유: 유일 호출부가 이 변경으로 사라진다. 죽은 코드는 git 이 기억 — CLAUDE.md §6).

# Key Files
- `skills/jira-worklog/jira_kit/codex_session.py` — rollout 스캔. 1회 스캔 API 추가, 정확일치 필터 제거
- `skills/jira-worklog/jira_kit/session_time.py` — `bucket_codex_intervals` 신설(classify 기반 버킷팅)
- `skills/jira-worklog/jira_worklog.py` — `main()` 에서 1회 스캔·버킷 병합, `process()` 는 병합된 구간만 받음
- `skills/jira-worklog/test_session_time.py` — 신규 테스트

# Blockers
없음.

# Acceptance
1. rollout 스캔이 worktree 수와 무관하게 **1회**. 검증: 스캔 함수 호출 횟수를 세는 테스트(또는 fake home 으로 glob 1회 확인)
2. cwd 가 worktree **하위 디렉토리**인 rollout 이 최장 prefix 버킷에 귀속. 검증: 신규 단위 테스트(LIVE 하위·DEAD 하위·무관 cwd)
3. cwd 가 worktree 와 **정확히 일치**하는 기존 케이스 회귀 없음. 검증: 신규 단위 테스트
4. **등록 시간 불변**. 검증: 변경 전/후 `jira_worklog.py --all --timezone UTC` 출력의 live worktree 합계 비교(동일해야 함)
5. DEAD 버킷 Codex 시간이 "삭제된 worktree 의 시간"에 표시. 검증: 같은 실행 출력에서 변경 전/후 비교(증가해야 함)
6. docstring 3곳(`jira_worklog.py` 코퍼스 서술 · `session_time.py` Codex 서술 · `codex_session.py` 필터 서술)이 새 동작과 일치. 검증: 육안 대조
7. CI 스위트 통과. 검증: `.github/workflows/lint.yml` 항목 로컬 실행

# Deferred
(없음)

# Workflow Findings
(없음)
