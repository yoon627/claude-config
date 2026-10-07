---
title: guard-fast-path — 시크릿 가드의 프로세스 생성 수 줄이기
status: in_progress
started: 2026-10-07
updated: 2026-10-07
---

# Goal
`scripts/pre-commit-check.sh`(+`.ps1`)가 가드 1회에 띄우는 프로세스 수를 줄여 가드 호출과 그 테스트(pre-commit-check.test.sh, ci-secret-scan.test.sh)를 빠르게 한다. 판정(block/allow·위반 문구·순서)은 바꾸지 않는다.

# Intent
- Problem: Windows 에서 프로세스 1개가 0.2~0.9초라 가드 1회가 6~17초, 800줄 push 케이스는 173초. 원인은 `scan_tokens` 의 패턴별 `$(printf|grep|head)`(14패턴 × 3) 와 ref 줄마다 `git rev-parse` 2회.
- Constraints: 보안 가드 — 판정 불변(기존 테스트 전부 통과 + 동치 근거). `.ps1` 은 같은 방식 또는 근거 있는 제외. fail-closed 경로 유지.
- Out of scope: pt_* (private-terms) 스캔 구조, 테스트 fixture 재사용(verify-speed `# Deferred` 다른 항목), 패턴 목록 변경.
- 분할: 없음 — 두 개선이 같은 두 파일·같은 테스트를 공유하고 합쳐도 ~40줄이라 plan 을 나누면 고정비만 는다.

# Progress
- 2026-10-07: 탐색. `cat-file --batch-check` 가 `rev-parse --verify --quiet X^{commit}` 과 같은 해석을 내는 것을 probe 로 확인(commit·tag→commit, blob·tree·없음→missing, blob sha 이름의 브랜치가 있어도 hex 우선, git 2.55.0.windows.5).

- 2026-10-07: 구현(.sh scan_tokens 사전 grep + ref 일괄 해석, .ps1 ref 일괄 해석) + 혼합 ref 줄 테스트. 전후 실측(sh, 같은 fixture, 출력 md5 동일): 일반 push 4.9→1.4초, 토큰 push 3.4→2.5초, 800줄 58.0→2.1초. ps1 parse 0 오류, shellcheck 통과. 전체 테스트·code-reviewer 진행 중.

- 2026-10-07: code-reviewer(+codex) REQUEST CHANGES — ps1 Invoke-Git 가 stdin 을 다 쓴 뒤 stdout 을 읽어 cat-file 질의 ~150개 이상에서 교착(PS 5.1·7 재현, 첫 전체 테스트도 800줄 ps1 케이스에서 멈춤 → 중단). 읽기를 쓰기 전에 비동기로 시작하도록 수정, fail-closed shim 테스트 추가. 전체 테스트 재실행 중.

- 2026-10-07: 전체 가드 테스트 370 통과·0 실패(ps1 122, ps51 118). `verify.sh changed` 가 이름 없는 FAIL 2건 — verify.sh `slow_skip` 이 호출부 루프 변수 `f` 를 덮어써 대상이 바뀐 느린 테스트가 빈 경로로 실행됨(ec51eb1 결함, 건너뛰는 경우만 시험돼 미발견). `local` 로 수정 + verify-changed.test.sh 회귀 테스트(HEAD 판 Red·수정판 Green 확인). verify.sh changed 재실행 중.

- 2026-10-07: 재리뷰(r2, +codex) REQUEST CHANGES 처분 — `local`→subshell 함수, shim 테스트 판별력 보강. shellcheck 통과. verify.sh changed 재실행 중.

- 2026-10-07: `bash scripts/verify.sh changed` 전 축 ALL PASS (skip: record-verified.test.sh — jq 미설치, 이전과 같음), 총 553초. pre-commit-check.test.sh 450초(전: 30~50분+), ci-secret-scan.test.sh 22초(전: 97초). Acceptance 1~5 충족 → DONE, 커밋.

# Next
- 머지(`/e merge` 또는 로컬 ff) — 사용자 선택. 그 뒤 verify-speed `# Deferred` 다음 항목(session-* fixture 재사용).

# Decisions
- wiki 조회: ci-secret-scan-backstop·git-log-added-lines-hardening 이 걸림 — 따른다(replace 무시는 두 스크립트의 `GIT_NO_REPLACE_OBJECTS=1` export 가 cat-file 에도 적용, 기존 replace 테스트가 지킨다).
- 부수 차이: .sh 의 lsha 해석 실패 때 git 이 stderr 로 내던 `error: … expected commit type` 줄이 더 이상 출력되지 않는다(cat-file stderr 를 버림). 판정·위반 문구는 같다.
- TDD Red 해당 없음 — 동작 불변 리팩토링이라 새 테스트는 두 단계 해석의 짝 맞춤을 잠그는 회귀 테스트다(옛 코드에서 돌려보지는 않았다).
- (a) `scan_tokens`: 내용 전체를 `grep -Eq -e p1 … -e p14` 1회로 먼저 본다. exit 1(어느 줄도 어느 패턴에도 안 맞음)일 때만 바로 return, 그 밖(0 매치·2 오류)은 기존 패턴별 루프로. 동치 근거: 기존 루프의 위반 조건은 패턴별 `grep -Eo` 출력이 비지 않음 = 그 패턴에 맞는 줄이 있음(모든 패턴이 리터럴 접두를 가져 빈 매치가 없다). 여러 `-e` 의 grep 은 어느 패턴이든 맞는 줄이 있으면 0. 따라서 exit 1 ⇒ 모든 패턴 출력이 비어 위반 0 — 기존과 같다. 오류(2)는 기존 루프로 넘겨 기존 동작 그대로.
- (b) ref 줄: 1차 루프에서 형식 검증·질의 목록 생성, `git cat-file --batch-check='%(objectname) %(objecttype)'` 1회, 2차 루프에서 줄 순서대로 결과 소비 → violations·published·pt_refs·push_commits 순서 불변. cat-file 실패(비0)·출력 줄 수 불일치는 전부 미해석으로 처리(lsha 쪽은 위반 = fail-closed, rsha 쪽은 제외 없음 = 스캔 확대).
- `.ps1` Scan-Tokens 는 제외 — .NET `-match` 라 프로세스를 띄우지 않는다. `.ps1` ref 루프는 (b) 와 같은 방식으로 바꾼다(Invoke-Git -Stdin 이 이미 있다).
- 커밋 단위: 1개 — 같은 가드의 같은 목적(프로세스 수 감소).
- 커밋 단위 2개로 변경 (이유: verify.sh `slow_skip` 변수 덮어쓰기 결함이 이 작업의 검증을 막아 §3-4 "빌드·테스트를 깨는 직접 원인"으로 함께 고쳤으나 목적이 다르다): 1) `fix(verify): run a changed slow test by its own path` — scripts/verify.sh, scripts/verify-changed.test.sh 2) `perf(pre-commit-check): fewer processes per guard run` — 가드 두 파일·pre-commit-check.test.sh·plan.

# Acceptance
1. pre-commit-check.test.sh 전 엔진(sh·ps1·ps51) 통과 — `bash scripts/pre-commit-check.test.sh` 마지막 줄 실패 0.
2. ci-secret-scan.test.sh 통과.
3. 가드 1회 시간 감소를 전후 실측으로 보인다(같은 fixture, sh 엔진).
4. 새 테스트: 여러 ref 줄에 미해석 lsha·tag·blob rsha 가 섞여도 위반 문구 순서가 줄 순서와 같다(이미 커버되면 그 케이스를 근거로 적는다).
5. `bash scripts/verify.sh changed` ALL PASS.

# Review Disposition
- [Critical] ps1 cat-file 파이프 교착 — fix (Invoke-Git 이 stdout/stderr 읽기를 stdin 쓰기 전에 시작).
- [Minor] fail-closed 분기 테스트 없음 — fix (sh shim: cat-file 실패·줄 부족 → 미해석 block).
- [Nit] lsha blob/tree 때 git stderr 진단 소실 — wontfix (판정·위반 문구 불변, Decisions 에 기록).
- [Nit] grep -q 조기 종료 시 SIGPIPE 노이즈 — wontfix (기존 `grep | head` 와 같은 종류, 판정 무영향, PLAUSIBLE).
- [Nit] 새 케이스가 ran_ps1 집계 안 됨 — fix (verdict 경유).
- [Nit] sh/ps1 cat-file 형식 차이 주석 없음 — fix (ps1 주석).
- [Minor] plan wiki 자리표시 — fix.
- [r2 Major] verify.sh `local` 이 `#!/bin/sh` 에서 shellcheck SC3043 → CI shell 축 실패 — fix (`slow_skip() ( … )` subshell 본문).
- [r2 Minor] cat-file shim 테스트가 게이트를 지워도 통과(판별력 없음) — fix (fail=전부 응답 후 exit 1, short=remote 0 인 ref 두 줄; 게이트 제거 변형에서 위반 수가 2→0 / 2→1 로 바뀌는 것 실측).
- [r2 Minor] ps1 Invoke-Git 의 stdin Write/Close 가 git 조기 종료 때 raw 예외로 끝남 — defer (HEAD 에도 있던 경로, push 는 막히는 fail-closed, # Deferred).
- [r2 Nit] mixed-ref else 분기 ran_* 미집계 — wontfix (실패 시 집계 수만 1 적음, 판정 무관).
- [r2 Open] ps1 엔진의 cat-file 실패·줄 부족 게이트 테스트 수단 없음(bash shim 이 .exe 해석에 안 걸림) — defer (# Deferred).
- 제안: run_guard 에 timeout — defer (macOS 기본에 `timeout` 없음, 범위 밖 → # Deferred).

# Deferred
- pre-commit-check.test.sh `run_guard` 에 엔진 공통 timeout 이 없어 가드가 멈추면 테스트도 영원히 멈춘다(이번에 실제로 발생). 낮음~중간. macOS 에 `timeout` 이 기본 없으므로 이식 가능한 방식이 필요.
- pre-commit-check.ps1 `Invoke-Git`: git 이 stdin 을 다 읽기 전에 끝나면 Write/Close 가 IOException 으로 훅을 끝낸다(push 는 막히나 `[BLOCKED]` 판정 문구 없이 raw 예외). 낮음. try/catch 후 Code 를 비0 으로 강제하는 방향.
- ps1 엔진의 cat-file 실패·줄 부족 게이트(.ps1 의 `$r.Code -eq 0`·줄 수 비교)를 시험할 수단이 없다 — `$gitExe` 를 Application 으로 고르므로 bash shim 이 안 걸린다. 낮음.

# Key Files
- scripts/pre-commit-check.sh — scan_tokens, pre-push ref 루프
- scripts/pre-commit-check.ps1 — pre-push ref 루프
- scripts/pre-commit-check.test.sh — 회귀 테스트
- scripts/verify.sh, scripts/verify-changed.test.sh — slow_skip 변수 덮어쓰기 수정·회귀 테스트

# Blockers
