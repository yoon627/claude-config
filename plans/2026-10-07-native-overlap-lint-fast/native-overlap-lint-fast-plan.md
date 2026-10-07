---
title: native-overlap-lint-fast — improve.sh 헤더 번호 계약을 실행 없이 검사
status: in_progress
started: 2026-10-07
updated: 2026-10-07
---

# Goal
scripts/native-overlap-lint.test.js 의 "improve.sh 점검 번호 1..N 유일" 검사가 `improve.sh deep` 을 실행하지 않고 소스에서 헤더를 읽게 해 테스트를 빠르게 하고, 그러면 느린 테스트가 아니므로 verify.sh SLOW_TESTS 에서 뺀다.

# Intent
- Problem: verify-speed `# Deferred` 3번. 이 테스트는 헤더 수열만 보려고 deep 전체(transcript JSONL 파싱·`claude --version`)를 돌린다. 단독 13.3초(2026-10-07), 부하 시 67초 관측.
- Constraints: 판정·커버리지 불변 — 잃는 것을 근거로 밝힌다. 헤더 수열 계약(같은 번호 두 번·건너뜀 금지)은 그대로 지킨다.
- Out of scope: improve.sh 자체, 테스트의 나머지(nativeOverlapStatus 단위·CLI) — 이미 빠르다.
- Open questions: 없음 — 구조를 읽어 확정(아래 Decisions).
- 분할: 없음 — 테스트 변경과 SLOW_TESTS 제거는 같은 머지에서만 맞는다(테스트가 여전히 느린데 목록에서 빼거나, 빨라졌는데 목록에 남기면 어긋난다).

# Progress
- 2026-10-07: 탐색. improve.sh 의 헤더 12개는 모두 리터럴 `echo "== N. …"` — 1~9 최상위, 10~12 `if [ "$DEEP" = 1 ]` 블록. 반복문·동적 번호 없음. CI 는 `improve.sh --ci` 로 점검 1~9 실행 경로를 이미 돈다(lint.yml:77).

- 2026-10-07: plan-reviewer CONDITIONAL·code-reviewer(+codex) REQUEST CHANGES 처분 반영. 테스트 13.3초 → 0.7초, 실제 improve.sh 헤더 1..12 수집, 합성 음성 케이스 14개 통과. verify-changed.test.sh 통과. `bash scripts/verify.sh changed` ALL PASS (skip: record-verified.test.sh — jq 미설치, 이전과 같음), 77초, native-overlap-lint 는 [slow] 없이 node 축에서 1초. Acceptance 1~4 충족 → DONE.

# Next
- 머지(사용자 선택).

# Decisions
- wiki 조회: native-overlap 관련 decision(공용 native-overlap-ledger 등)은 대장 판정 내용에 관한 것이라 이 테스트 방식과 무관 — 그대로.
- 정적 검사로 바꾼다: improve.sh 소스에서 `echo "== <숫자>.` 줄을 순서대로 모아 1..N 유일·연속을 본다. deep 실행 출력과 같은 수열인 근거: 헤더가 전부 리터럴이고, 반복문 밖이며, deep 에서는 `if DEEP` 블록까지 모두 실행돼 소스 순서 = 출력 순서.
- 정적 검사가 못 보는 것과 대책:
  1) 번호를 변수로 찍는 헤더(`echo "== $n."`) — `echo "== ` 로 시작하는 줄을 전수 모아 숫자 헤더·`요약`·`ci:` 외의 것이 있으면 실패시킨다.
  2) 반복문 안 헤더(한 줄이 여러 번 출력) — 정적으로 못 잡는다. 현재 없음. 감수(accepted) — 이런 구조 변경은 리뷰에서 보인다.
  3) deep 실행 자체가 끝까지 도는가 — 기존 테스트도 보지 않았다(중간 종료해도 1..k 면 통과). 잃는 것 없음.
  4) deep 전용 점검 10~12 의 실행 경로 — 기존 테스트는 헤더 출력만 봤고 실패도 [info] 로 삼켜 통과했다. 잃는 것은 "deep 분기가 bash 오류 없이 헤더까지 도달한다" 뿐 — `bash -n`·shellcheck(shell 축)가 문법을 본다.
- 수집 규칙(리뷰 반영): 주석 줄(`^\s*#`) 제외. 엄격한 수집기는 `^\s*echo "== <숫자>. `(들여쓴 deep 헤더 10~12 포함). 넓은 그물은 따옴표 바로 뒤 `== `(`["']== `)가 있는 모든 줄 — 엄격한 수집기·`요약`·`ci:` 어디에도 안 맞으면 실패(printf·작은따옴표·`echo -e`·`&& echo` 헤더·변수 번호). 헤더 0개도 실패(경로 오류 대비).
- 정적 검사는 모든 모드의 헤더를 한 수열로 본다 — 모드별로 같은 번호를 쓰는 설계도 실패로 본다(모드 간 번호 충돌 B1 계열을 더 엄격히 막는 차이).
- 잃는 것 추가: 루트 가드 실패·bash 부재로 헤더가 0개 나오는 경우(실행 검사만 보던 것 — 실질 손실 작음).
- accepted-risk: 이 변경 뒤 CI 어디에서도 deep 분기가 실행되지 않는다(CI 는 `--ci`=DEEP 0). deep 은 사용자가 /improve deep 으로 직접 돌리는 관측용이고 실패는 [info] 로 삼켜 판정에 영향이 없다 — 실행 경로 회귀는 그 실행에서 바로 보인다.
- verify.sh SLOW_TESTS 에서 native-overlap-lint.test.js 를 뺀다(빨라지면 건너뛸 이유가 없다). `.sh → node` 축 매핑(verify.sh:47 주석의 native-overlap-lint)은 유지 — 테스트가 여전히 improve.sh 소스를 읽는다. verify-changed.test.sh 의 slow 기대 개수를 하나씩 줄이고 해당 줄을 지운다.
- 커밋 단위: 1개 — 같은 목적(이 테스트를 빠르게 하고 그에 맞게 목록 갱신).

# Acceptance
1. native-overlap-lint.test.js 가 통과하고 단독 시간이 준다(전 13.3초) — 실행·시간 측정.
2. 정적 검사가 실제 회귀를 잡는다 — 검사 함수에 헤더 번호 중복(9 두 번)·건너뜀·변수 번호를 넣은 합성 소스를 주면 각각 문제를 보고한다(테스트 안의 상시 단언).
3. verify-changed.test.sh 통과(slow 개수 갱신). README.md 의 "느린 테스트 9개" 목록이 8개로 갱신되고 native-overlap-lint 가 빠진다.
4. `bash scripts/verify.sh changed` ALL PASS.

# Review Disposition
- [강] README 느린 테스트 목록 누락 — fix (Key Files·Acceptance 3).
- [강] 줄 시작 고정 정규식이 들여쓴 헤더를 조용히 빠뜨림 — fix (`^\s*` + 넓은 그물 대조).
- [강] printf·작은따옴표·`echo -e`·`&& echo` 헤더 — fix (넓은 그물 + 합성 음성 케이스).
- [약] 잃는 것 목록 보강(헤더 0개·모드 간 번호) — fix (Decisions).
- [약] CI 에서 deep 분기 실행 경로가 사라짐 — accepted-risk (Decisions).
- [약] 주석 안 `== 9.` 를 세지 않는 케이스 — fix (합성 케이스).
- [code-review Major, severity disputed] 따옴표 없는 echo·한 줄 두 echo·요약/ci 줄 꼬리·리다이렉션 헤더를 놓쳐 README 보장과 어긋남 — fix (엄격 수집기·요약/ci 면제를 줄 전체 고정, 넓은 그물에 `== \d` 추가, 합성 음성 케이스 5개 추가, README 를 실제 범위로 고침 — 반복문·printf 인자 분리는 못 본다고 명시).
- [code-review Nit] `echo -e` 상시 단언 없음 — fix.
- [code-review Nit] 기존 주석의 `(plan B1)` 참조 — defer (diff 밖 기존 줄, # Deferred).

# Deferred
- native-overlap-lint.test.js 헤더 계약 주석의 `(plan B1)` — 코드에 plan 참조(main 에 없는 plan 을 가리킬 수 있음). 낮음.
- verify.sh SLOW_TESTS 재평가: 앞선 작업으로 session-fetch(단독 약 12초)·ci-secret-scan(22초)이 30초 기준 아래가 됐다. 목록에서 뺄지 다시 잰 뒤 판단(낮음, verify.sh·verify-changed.test.sh·README).

# Key Files
- scripts/native-overlap-lint.test.js — 헤더 계약 블록
- scripts/verify.sh — SLOW_TESTS
- scripts/verify-changed.test.sh — slow 기대 개수
- README.md — 느린 테스트 목록(471행 부근)

# Blockers
