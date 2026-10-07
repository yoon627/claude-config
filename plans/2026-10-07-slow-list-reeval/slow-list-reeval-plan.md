---
title: slow-list-reeval — 빨라진 테스트를 느린 테스트 목록에서 빼기
status: done
started: 2026-10-07
updated: 2026-10-08
---

# Goal
native-overlap-lint-fast `# Deferred`: 앞선 속도 개선으로 단독 30초 아래가 된 테스트를 `verify.sh changed` 의 느린 테스트 목록에서 빼, 로컬 검증에서 건너뛰지 않게 한다.

# Progress
- 2026-10-07: 단독 1회 실측(Windows 11, 다른 실행 없음): ci-secret-scan 24.1초, session-fetch 14.4초, install-hooks 29.0초, session-start-pull 58.8초, session-brief 58.9초, test_wiki_check 58.7초, test_commit_units 127.9초, pre-commit-check 486초(guard-hardening verify 중 측정). 두 테스트를 목록에서 빼고 verify-changed.test.sh 기대 개수·README 를 맞춤. verify-changed.test.sh 통과.

# Next
- 없음 — 사용자 선택으로 main 에 로컬 ff + push.

# Decisions
- 규모: small(세 파일이지만 목록 한 줄씩과 그에 맞춘 숫자).
- 뺀다: ci-secret-scan(24초), session-fetch(14초) — 기준 30초 아래이고 여유가 있다.
- 유지: install-hooks(29.0초) — 기준에 1초 차이라 측정 흔들림으로 다시 넘을 수 있고, 부하에서는 98초로 관측됐다. 기준을 "약 30초"로 적어 경계 판단의 여지를 README 에 남긴다.
- 커밋 단위: 1개.
- verify-speed `# Deferred` 4번(워치독·post-checkout 폴링 루프의 1회당 프로세스 수)은 코드 변경 없이 닫는다(2026-10-08): 루프(`install-hooks` 의 post-checkout, `session-start-pull.sh`)의 상한은 반복 수가 아니라 wall-clock 이라 `sleep 0.2` 프로세스를 줄여도 걸리는 시간은 같고 CPU 만 조금 준다. `sleep` 을 없애려면 bash 전용 `read -t` 가 필요한데 두 스크립트는 POSIX `sh` 로 돈다(macOS 포함) — 이식성을 잃는 대가가 이득보다 크다.

# Review Disposition
- [Major CONFIRMED] verify-changed.test.sh 의 "대상이 바뀐 느린 테스트가 그 경로로 돈다" 회귀가 목록에서 빠진 ci-secret-scan 을 fixture 로 써서 공허해짐 — fix (fixture 를 pre-commit-check 로, fixture 가 느린 목록에 있는지도 단언; slow_skip 을 `{ }` 로 되돌린 변형에서 실패 확인).
- [Nit] verify.sh 주석 "30초 이상" ↔ README "약 30초" — fix.

# Acceptance
1. 두 테스트가 SLOW_TESTS 에서 빠지고 README 목록이 6개가 된다.
2. verify-changed.test.sh 통과(각 줄의 기대 개수 재계산).
3. `bash scripts/verify.sh changed` ALL PASS.

# Key Files
- scripts/verify.sh — SLOW_TESTS
- scripts/verify-changed.test.sh — slow 기대 개수
- README.md — 느린 테스트 목록

# Blockers
