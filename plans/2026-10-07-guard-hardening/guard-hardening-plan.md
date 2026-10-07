---
title: guard-hardening — 가드 테스트 상한과 ps1 조기 종료 처리
status: done
started: 2026-10-07
updated: 2026-10-08
---

# Goal
guard-fast-path `# Deferred` 두 건: (1) pre-commit-check.test.sh 의 가드 호출에 상한을 둬 가드가 멈춰도 테스트 전체가 멈추지 않게 한다. (2) pre-commit-check.ps1 `Invoke-Git` 이 git 의 조기 종료를 raw 예외 대신 실패 코드로 돌려주게 한다.

# Progress
- 2026-10-07: (1) `capped` — `timeout` 이 있으면 그것(GNU timeout 은 프로세스 그룹에 신호), 없으면(macOS) perl 이 새 프로세스 그룹으로 띄우고 시한에 그룹을 끝낸다. run_guard 3곳·hook_git 에 적용, 기본 300초(`GUARD_TIMEOUT`). 새 케이스: git 대신 멈추는 shim → 이전 run_guard 는 60초 안에 끝나지 않음(Red), 이후 timeout 경로 4초·perl 경로 5초에 실패로 끝남(Green, Git Bash).
- 2026-10-07: (2) probe(Invoke-Git 원문, 2MB stdin): 수정 전 pwsh 7 은 `git log --stdin --no-such-option` 에서 "The pipe is being closed." 예외, 5.1 은 code 128. 수정 후 두 판 모두 code 128. stdin 을 안 읽고 성공하는 git(인위적 경우)은 pwsh 1, 5.1 은 0(5.1 은 그 쓰기에서 예외를 내지 않음 — 주석에 명시).

# Next
- 없음 — 사용자 선택으로 main 에 로컬 ff + push.

# Decisions
- 규모: 두 변경이 각각 한 파일·50줄 미만이라 small 둘로 본다(plan-reviewer 생략, code-reviewer 1회).
- 커밋 단위: 1) `test(pre-commit-check): end a hanging guard case at a time limit` — scripts/pre-commit-check.test.sh 2) `fix(pre-commit-check): report a git that closes its stdin early as a failure` — scripts/pre-commit-check.ps1. plan 은 마지막 커밋에.
- 기본 상한 300초: 정상 가드 1회는 수 초(800줄 ps51 포함)라 부하에서도 여유가 크고, 멈춘 경우 5분 안에 실패로 끝난다.
- 기각: perl `alarm`+`exec` 만 쓰는 형태 — 손자 git 이 출력 파이프를 붙잡아 `$(...)` 가 끝나지 않는다.

# Review Disposition
- [Major CONFIRMED] 상한 종료(124)가 `[BLOCKED]` 출력 뒤라면 block 기대에서 PASS — fix (verdict 가 124·137·143 을 기대와 무관하게 실패, 회귀 케이스 추가 — 상한 분기를 끈 변형에서 실패 확인).
- [Minor] hang 케이스가 즉시 실패해도 통과 — fix (rc=124 이고 3~20초).
- [Minor] GNU 경로는 TERM 만 보냄 — fix (`timeout -k 5`).
- [Minor] 직계 자식이 먼저 끝나면 그룹의 남은 프로세스를 정리하지 않음 — wontfix (가드는 `&` 를 쓰지 않고 ps1 은 git 을 기다린다; 남은 자식이 정상 종료하면 결과는 가드 자신의 것).
- [Minor] 체계적 hang 이면 케이스 × 300초 — wontfix (선택 사항; 테스트 전체가 무한히 멈추던 것에서 유한으로 바뀐 것이 목표).
- [Nit] ps1 주석이 너무 일반적 — fix (버퍼보다 작은 입력은 예외가 없다고 명시).
- [Nit] Write 예외 시 Close 미호출·perl alarm 정수 — wontfix (현실 trigger 없음, 영향 미미).

# Acceptance
1. 멈추는 가드 케이스가 상한에서 실패로 끝난다(timeout·perl 두 경로).
2. pwsh 7 에서 git 조기 실패가 예외 대신 git 의 종료 코드로 돌아온다(probe 전후).
3. `bash scripts/verify.sh changed` ALL PASS(가드가 바뀌어 pre-commit-check·ci-secret-scan 테스트가 돈다).

# Key Files
- scripts/pre-commit-check.test.sh — capped, run_guard, hook_git, 새 케이스
- scripts/pre-commit-check.ps1 — Invoke-Git

# Blockers
