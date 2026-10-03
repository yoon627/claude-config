---
title: jira-232-docs-regex — 이슈 #232 1–3: jira-task 설정 소스 문서·load_config docstring·잘못된 티켓 패턴의 exit 2
status: in_progress
started: 2026-10-03
updated: 2026-10-03
---

# Goal
이슈 #232 의 1–3 을 처리한다. jira-task SKILL.md 에 `jira-kit.toml` 설정 소스를 적고, jira-worklog `load_config` docstring 의 우선순위를 실제 동작에 맞추고, 잘못된 티켓 패턴 정규식이 traceback·exit 1 대신 exit 2 와 한 줄 오류로 끝나게 한다.

# Intent
- Problem: #231 이 머신별 티켓 패턴 설정을 안내하게 되면서, 설정 소스 문서의 빈 곳(jira-task)과 잘못된 정규식의 traceback(jira-worklog)이 사용자에게 드러날 가능성이 커졌다. 사용자 결정(2026-10-03): 1–3 지금 처리, 4(기본 타임존)·5(CLAUDE.md §10)는 하지 않는다.
- Constraints: 런타임 동작은 잘못된 패턴의 종료 방식 말고는 바꾸지 않는다. 비공개 용어를 어디에도 적지 않는다. 종료코드 계약(`test_exit_contract.py` 머리 docstring)과 맞춘다 — 설정 오류는 2.
- Out of scope: #232 4·5. jira-task 의 패턴 처리(이미 `ConfigError`). 다른 설정 값(`max_gap` 의 조용한 기본값 대체 등)의 검증.

# Progress
- 2026-10-03: worktree 생성(base `origin/main@4ad0b02`). Explore — 설정 오류는 `설정 로드 실패:` + exit 2(`jira_worklog.py:343-347`), CLI 값 검증 선례는 `--max-gap` 의 argparse type(`_non_negative_int`), jira-task 는 패턴 오류를 `ConfigError("JIRA_TICKET_PATTERN 파싱 실패: …")` 로 감싼다(`jira_task.py:493-497`).
- 2026-10-03: TDD Red(설정 쪽 `ConfigError not raised`, CLI 쪽 `re.PatternError` traceback) → 구현 → Green. 코드 리뷰(Workflow: 리뷰 1 + 반박 검증 1, Codex 미가용) APPROVE 수준, minor 1 real — 설정 패턴을 무조건 검사해 유효한 `--ticket-pattern` 으로도 우회하지 못함 → 검증을 `main` 으로 옮김(Red 재확인 후 Green). 실제 프로세스: 설정 오류 exit 2(한 줄), CLI 오류 exit 2(usage + 한 줄), 깨진 설정 + 유효한 CLI 값 exit 0.
- 2026-10-03: 최종 검증(Workflow) — 격리 runner 는 `verify.sh` ALL PASS(skip: install-codex-skill.test.ps1)·Ran 14·2·29·19·71·19 를 관찰했다. 9번 명령은 메인이 `[` 를 따옴표 없이 넘겨 zsh 글롭 오류로 실행되지 않았고, 그 경로는 메인이 따옴표를 넣어 직접 관찰했다(exit 2). 반영분 재검토는 nit 3 → 반영. 우회 테스트의 설정을 실제 `resolve_config` 로 만들고, 검사를 `resolve_config` 로 되돌린 변형이 잡히는 것을 확인했다. evidence gate 1–7 충족 → DONE.

# Next
- 커밋 → commit-check → 로컬 ff-merge·정리 → main push 는 사용자 확인.

# Decisions
- 관련 wiki decision 없음 — #231 의 조회와 같은 범위(jira-worklog 티켓 패턴), 이번 변경은 그 후속이다.
- 검증 위치: 설정에서 온 패턴은 `config.resolve_config` 에서 `re.compile` 해 `ConfigError` 로(데이터 경계 — 기존 `설정 로드 실패` 경로로 exit 2), `--ticket-pattern` 은 argparse type 함수로(`--max-gap` 선례 — argparse 오류는 exit 2). 메시지는 jira-task 와 같은 "JIRA_TICKET_PATTERN … 파싱 실패". 기각: `main` 에서 실제 쓰는 패턴 하나만 검증 — `_ticket_for` 가 패턴을 다시 계산해 두 번 다루거나 `process`·`_ticket_for` 시그니처를 바꿔야 한다.
- 검증 위치 → **설정 패턴은 `main` 에서 `--ticket-pattern` 이 없을 때만 `config.check_ticket_pattern` 으로 검사하도록 변경** (이유: 코드 리뷰 minor — `resolve_config` 에서 무조건 검사하면 유효한 `--ticket-pattern` 으로도 깨진 설정을 우회하지 못해, "종료 방식 말고는 바꾸지 않는다" 제약과 SKILL.md 의 `--ticket-pattern` 우선 설명에 어긋난다. jira-task 도 실제로 쓰는 패턴만 검사한다). `--ticket-pattern` 은 그대로 argparse type 으로 검사한다. 기각: `resolve_config` 에서 검사(위 이유).
- 테스트: 처음에는 `test_ticket_pattern.py` 에 `resolve_config` 수준 테스트를 두었으나 위 변경으로 지우고, `test_exit_contract.py` 에 2개 — 설정 패턴 오류 → exit 2 와 유효한 `--ticket-pattern` 이면 진행(exit 0), `--ticket-pattern` 오류 → exit 2. `test_ticket_pattern.py` 는 변경 없음.
- rollback: 이 브랜치 커밋 revert(식별자 정리와 무관해 revert 가 안전하다).
- 커밋 단위: 1개 — 세 항목 모두 #231 의 머신별 패턴 안내를 받치는 작은 후속이다.

# Acceptance
1. jira-task SKILL.md 의 설정 우선순위가 `jira-kit.toml`(cwd 위의 프로젝트 파일, 없으면 `~/.jira-kit/jira-kit.toml`)을 4순위로 적고, toml 에서 읽는 키(`[jira]` base_url·email·cloud_id, `[worklog]` timezone·ticket_pattern)와 토큰은 읽지 않는다는 점을 적는다. 관찰: 해당 줄을 읽어 `jira_task.py:102-112,141-160` 과 대조.
2. jira-worklog `load_config` docstring 이 `.env` 층(프로젝트 > 전역)과 toml 층(프로젝트 파일이 있으면 전역을 읽지 않음)을 구분한다. 관찰: docstring 을 `load_config` 본문과 대조.
3. 설정의 패턴이 잘못되고 `--ticket-pattern` 이 없으면 `설정 로드 실패: JIRA_TICKET_PATTERN… 파싱 실패: …` 한 줄과 exit 2, 유효한 `--ticket-pattern` 을 주면 그대로 진행(exit 0) — `test_exit_contract.py` 새 테스트 Red→Green, 실제 프로세스로 두 경우를 관찰.
4. `--ticket-pattern` 이 잘못되면 argparse 의 usage 와 오류 한 줄(`argument --ticket-pattern: 정규식 파싱 실패: …`)·exit 2 로 끝나고 traceback 이 없다 — `test_exit_contract.py` 새 테스트 Red→Green, 실제 프로세스로 관찰.
5. 회귀 없음 — 직접 실행 Ran 수(exit_contract 14, ticket_pattern 2, 나머지 29·19·71 그대로, jira-task 19), `bash scripts/verify.sh` 마지막 줄 `ALL PASS` 또는 `ALL PASS (skip: install-codex-skill.test.ps1)`.
6. `test_exit_contract.py` 머리 docstring 의 종료코드 목록에 잘못된 티켓 패턴(설정·`--ticket-pattern`)이 2 로 들어간다.
7. 비공개 용어 적중 0(추적 파일·diff·커밋 메시지). 이제 이 머신의 가드도 켜져 있다.

# Review Disposition
- [CR minor] 설정 패턴을 무조건 검사해 유효한 `--ticket-pattern` 으로도 우회하지 못함 — fix: 검사를 `main` 으로 옮겨 CLI 값이 없을 때만(Decisions).
- [CR nit] 패턴 오류 메시지에 값의 출처(env·.env·toml 경로)가 없음 — wontfix: `pick` 이 출처를 버리는 구조라 넓은 변경이 필요하고, 메시지가 키 이름과 toml 키를 함께 적어 찾을 곳은 좁혀진다.
- [CR nit] README·jira-worklog SKILL.md 가 잘못된 정규식의 exit 2 를 적지 않음 — fix: SKILL.md 79행에 한 구절. README 의 `test_ticket_pattern.py` 줄은 그 파일이 변경 없이 남아 그대로 맞다.
- [CR nit] 새 테스트 docstring 이 exit 2 를 말하지만 `ConfigError` 만 확인, Acceptance 4 의 "한 줄 오류" 가 argparse 출력과 다름 — fix: 테스트를 종료코드 수준으로 옮겼고 Acceptance 3·4 문구를 실제 출력에 맞췄다.

- [재검토 nit] 빈 `--ticket-pattern ''` 은 설정 패턴을 쓰고 검사하는데(코드는 일관), SKILL.md·주석이 "주면 검사하지 않는다"고 적음 — fix: "비어 있지 않은" 으로 좁힘.
- [재검토 nit] 우회 단언이 mock 된 설정 위에서만 돌아, 검사가 설정을 읽는 단계로 다시 들어가도 못 잡음 — fix: 설정을 실제 `resolve_config` 로 만들고 그 변형이 잡히는 것을 확인.
- [재검토 nit] `check_ticket_pattern` docstring 의 "쓰기 전에" 가 Jira 쓰기로 읽힘 — fix: "worktree 를 처리하기 전에".

# Key Files
- `skills/jira-task/SKILL.md` — Configuration 절 우선순위 문장.
- `skills/jira-worklog/jira_kit/config.py` — `check_ticket_pattern`(설정 패턴 → `ConfigError`), `ConfigError`·`load_config` docstring.
- `skills/jira-worklog/jira_worklog.py` — `--ticket-pattern` argparse type `_regex`, `main` 의 설정 패턴 검사.
- `skills/jira-worklog/SKILL.md` — 잘못된 정규식도 exit 2(CLI 값이 있으면 검사 안 함).
- `skills/jira-worklog/test_exit_contract.py` — 새 테스트 2개, 종료코드 docstring.

# Blockers
- 없음.
