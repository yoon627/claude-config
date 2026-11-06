---
title: ps1-utf8-terms — 비공개 용어 목록의 잘못된 UTF-8·NUL 을 두 엔진에서 같이 막기 (#214 7)
status: done
started: 2026-11-05
updated: 2026-11-06
---

# Goal
비공개 용어 목록 항목에 잘못된 UTF-8 이나 NUL 이 있을 때 sh 와 ps1 엔진의 판정을 같게 한다 — 둘 다 그 줄을 잘못된 항목으로 막는다.

- Why: #214 7. sh 는 바이트 그대로, ps1 은 U+FFFD 로 바꾼 문자열로 판정해 같은 목록이 엔진마다 다르게 읽혔다(README 한계로만 적혀 있었다). awk 구현에 따라 NUL 에서 줄이 잘려 sh 가 항목 일부만 쓸 수도 있었다.
- Constraints: ps1 은 이 세션에서 실행할 수 없다(PowerShell 설치 거부) → PR 의 CI 로 검증(공용 wiki `lesson-skipped-axis-blocks-merge`). 목록 원문은 읽거나 찍지 않는다.
- Out of scope: #214 5(ps1 쌍둥이 단일화 — 조사만), 그 밖의 #214 항목.
- Size: small
- Split: none — 두 엔진·테스트·README 가 같은 규칙을 한 번에 바꿔야 모순이 없다.

# Tasks
- [x] plan 승인 (2026-11-05) — "#214-7 수정 + #214-5 조사 (추천)"(사용자 선택)
- [x] 테스트 — `scripts/pre-commit-check.test.sh`: 잘못된 UTF-8·NUL·encoded surrogate 항목은 차단, 잘못된 바이트가 든 주석 줄은 건너뜀, 위반 문구 3곳 갱신 (2026-11-05) — Red 6건
- [x] sh — `scripts/pre-commit-check.sh` `pt_load`: `tr '\000' '\001'` 뒤 awk 의 `bad8()` 바이트 검사 (2026-11-05) — 162 통과, gawk·mawk·busybox awk 의 바이트 표 확인
- [x] ps1 — `scripts/pre-commit-check.ps1` `Get-PrivateTerms`: 줄마다 엄격한 UTF8Encoding 으로 다시 디코드 (2026-11-05) — 미실행(CI)
- [x] README — 항목 규칙과 한계 문구 (2026-11-05)
- [x] code-reviewer → `bash scripts/verify.sh changed` (2026-11-05) — APPROVE(Minor·Nit 각 1 → fix, 경계 테스트 4건 추가) · `ALL PASS (skip: pre-commit-check.test.sh(case) install-codex-skill.test.ps1 zsh)` — ps1 케이스는 CI
- [x] PR → CI(ps1) 녹색 → 머지 (2026-11-06) — PR #259

# Acceptance
1. 잘못된 UTF-8·NUL·surrogate 항목은 두 엔진 모두 `invalid entry (…invalid UTF-8)` 로 막는다 — `pre-commit-check.test.sh` 새 케이스 — sh 통과, CI 에서 ps1 통과(`NOTE [ps1] ran`)
2. 올바른 비ASCII 항목(기존 `얼룩말사` 케이스)과 주석 줄은 그대로 — 기존·새 케이스 통과
3. README 의 항목 규칙·한계가 새 동작과 같다 — 리뷰 대조
4. CI 녹색 — PR 의 `lint` success

# Decisions
- 관련 decision 조회: `lesson-skipped-axis-blocks-merge`(따른다 — ps1 변경이라 CI 경로).
- ⚠️ (구현) 판정 범위는 "엄격한 .NET 디코더가 받는 것" 과 같게 — overlong·surrogate·U+10FFFF 초과도 잘못된 것으로 — 다른 선택지: 바이트 수·연속 바이트만 보기 — 두 엔진이 같은 줄에서 갈리지 않게 하려면 ps1 의 표준 디코더 규칙에 sh 를 맞추는 쪽이 정의가 분명하다 — `bad8`·`Get-PrivateTerms`
- ⚠️ (구현) NUL 은 awk 전에 `\001` 로 바꿔 제어 문자로 잡는다 — 다른 선택지: 파일 전체를 거부 — 줄 번호를 알려 주는 기존 형식을 유지 — `pt_load`
- macOS 의 awk(One True Awk 2판)는 문자열 함수가 UTF-8 코드 포인트를 세지만, 그 분기는 모두 `awk_mb_cur_max == 1` 이면 바이트로 간다(`run.c:606·633·680`, `%c` 는 `run.c:1288`, `main.c:139-141` 이 `MB_CUR_MAX` 를 읽음 — onetrueawk/awk master 소스). sh 엔진은 `export LC_ALL=C` 라 macOS 에서도 바이트 방식 — gawk·mawk·busybox 는 이 컨테이너에서 실측(바이트 표 255개). macOS 실행 자체는 미관측.

# Blockers
