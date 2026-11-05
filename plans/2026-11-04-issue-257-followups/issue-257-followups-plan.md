---
title: issue-257-followups — #257 의 스크립트 항목 4개(drift 점검·fixture 토큰·경로 숨김·skip 노출 테스트)
status: done
started: 2026-11-04
updated: 2026-11-05
---

# Goal
#257 가운데 이 원격 세션에서 끝낼 수 있는 스크립트 항목 1·3·4·5 를 고친다.

- Why: 2026-11-01 점검의 미룬 항목이라 plan log 에만 있으면 잊힌다. 1 은 머신 settings 가 정본과 갈려도 아무도 알리지 않는 상태, 3·4 는 넓힌 토큰 스캔의 남은 빈틈, 5 는 검증 출력 변환이 테스트로 고정돼 있지 않은 상태다.
- Constraints: `.ps1` 은 이 컨테이너에서 실행할 수 없다(PowerShell 설치가 자동 모드에서 거부됨) → 로컬 ff-merge 하지 않고 PR 의 CI 로 검증한다(공용 wiki `lesson-skipped-axis-blocks-merge`). `skills/jira-task/` 는 건드리지 않는다(사용자 지시) — `test_jira_task.py:20` 이 같은 패턴에 걸려도 보고만.
- Out of scope: #257 2(머신 적용 — 사용자 작업)·6(fail-open 정책 결정)·7(관찰)·8(2.1.314 이상 실측). #214 5·7.
- Size: medium
- Split: none — purpose-commit bundle: #257 · 항목 1·3·4·5 · 넷 다 작은 스크립트 수정이고 서로 다른 파일이라 목적 커밋으로 따로 되돌릴 수 있다(3 과 4 는 같은 `pre-commit-check.test.sh` 를 고치지만 다른 줄).

# Tasks
- [x] plan 승인 (2026-11-04) — "남은 이슈 진행해"(#257 의 남은 항목을 맡긴 위임 메시지)
- [x] 3) fixture 토큰 — `scripts/pre-commit-check.test.sh`:19·145·147·149·153, `scripts/ci-secret-scan.test.sh`:9·10 을 따옴표를 끊어 실행 시 조립(기존 `'sk-ant-''…'` 관례) (2026-11-04) — 리터럴 0줄, sh 테스트 158·14 통과
- [x] 4) 토큰 위반 경로 숨김 — `scripts/pre-commit-check.sh`·`.ps1`: 비공개 용어 목록을 토큰 스캔 전에 읽고, 경로에 용어가 들어 있으면 `path (hidden):<줄>` 로 · `scripts/pre-commit-check.test.sh` 케이스 · `README.md` 해당 서술 (2026-11-04) — Red 2건 → Green, ps1 은 미실행(CI)
- [x] 5) skip 노출 테스트 — `scripts/verify-changed.test.sh` 에 skip 하는 python fixture 케이스 (2026-11-04) — 변환 줄 삭제 시 Red, 복원 시 Green
- [x] 1) drift 점검 — `skills/improve/improve.sh` 새 점검 13(`sync-permissions.js --check --keep-allow` → ask drift 는 warn, bare allow 제거 대기는 info, 개수만) · `skills/improve/improve.test.sh` · `skills/improve/SKILL.md` · `README.md` (2026-11-04) — Red 4건 → Green
- [x] code-reviewer → simplify 점검 → `bash scripts/verify.sh changed` (2026-11-05) — 1차 REQUEST CHANGES(점검 번호 계약 등 4건) → fix → 재리뷰 APPROVE · `ALL PASS (skip: pre-commit-check.test.sh(case) install-codex-skill.test.ps1 zsh)` — ps1 케이스는 CI
- [x] PR → CI(ps1 축 포함) 녹색 → 머지(`/e merge`) (2026-11-05) — PR #258

# Acceptance
1. fixture 에 토큰 모양 리터럴이 없다 — 스캐너 패턴 14개로 tracked 파일 전수 훑기(`skills/jira-task/` 제외) — 0줄, 그리고 `pre-commit-check.test.sh`·`ci-secret-scan.test.sh` 가 통과
2. 경로에 비공개 용어가 있는 파일의 토큰 위반은 경로를 숨긴다 — `pre-commit-check.test.sh` 새 케이스(staged·pushed) — sh 통과, ps1 은 CI 의 `NOTE [ps1] ran` 과 함께 통과
3. `verify.sh` 의 unittest skip 변환이 테스트로 고정된다 — `verify-changed.test.sh` 새 케이스 — 변환을 깨면 Red, 복원하면 Green
4. improve 점검 13 이 drift·동기화·파일 없음을 구분한다 — `improve.test.sh` 새 케이스 — warn/ok/info 줄이 기대대로, 규칙 목록 원문은 출력하지 않는다
5. 문서 동기화 — README 의 improve 점검 목록·pre-commit-check 서술이 새 동작과 같다 — 리뷰 대조
6. CI 녹색 — PR 의 `lint`·`record-verified` success

# Decisions
- 관련 decision 조회: 공용 wiki `lesson-skipped-axis-blocks-merge`(따른다 — ps1 변경이라 CI 경로), `claude-code-permission-prompt-sources` 처방 4(따른다 — bare allow 제거는 머신별 결정이라 점검 13 은 그것을 warn 으로 세지 않는다).
- 커밋 단위: 1) `test(pre-commit): assemble the fixture tokens at run time` — 3 2) `fix(pre-commit): hide private paths in token violations` — 4 3) `test(verify-changed): pin the unittest skip line` — 5 4) `feat(improve): report permission-rule drift against the canonical list` — 1
- ⚠️ (구현) 숨긴 자리 표기 `path (hidden):<줄>` — 다른 선택지: 줄 번호도 빼기 — 줄 번호는 비공개 정보가 아니고 위치를 찾는 데 필요해 남김 — `tok_hide_paths`·`Get-TokenPath`
- ⚠️ (구현) 목록이 깨져 있으면(`pt_load` 실패) 토큰 위반은 경로를 숨기지 않는다 — 다른 선택지: 모든 경로 숨기기 — 깨진 목록은 이미 커밋·push 를 막는 위반이라 그 출력은 목록을 고치기 전까지만 보이고, sh 의 `pt_load` 가 실패 시 `pt_terms` 를 비우는 기존 동작을 따름 — `pt_scan_staged`·`Invoke-PrivateStaged`
- 점검 번호 13: 10~12 는 deep 전용이라 번호를 다시 매기면 SKILL.md·README 의 deep 서술이 같이 바뀐다. 기본 점검이지만 13 으로 둔다.

# Blockers
