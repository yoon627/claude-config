---
title: verify-cmd-coverage — early-stop-verify 의 검증기 인식 격차 해소
status: done
started: 2026-08-13
updated: 2026-08-18
---

# Goal

`dlc-evidence-ledger` 의 `VERIFY` 가 node/python/JVM 중심이라 컨테이너·셸·스타일·타 생태계 검증기를 못 알아보는 문제를 고친다. **오탐만 줄이고 미탐은 늘리지 않는다.**

# Progress

- 2026-08-13: telemetry 조사(main 에서 read-only) → 근본 원인 확정. worktree 생성(base main@debfe57).
- 2026-08-13: TDD — 양성 17 + 음성 11 케이스 먼저 작성 → Red 확인 → `VERIFY` 2분할 확장 → Green(64 tests).
- 2026-08-13: 전 검증 통과(단위 10스위트·node --check·shellcheck·wiki clean). simplify 1건(`ruff` 가 TOOLS 에 이미 있어 SUBCMD 쪽 중복 제거) + `hadolint` 테스트 보강.
- 2026-08-18: 커밋 `6b1a9e9` → PR #143 → CI pass → 머지(`775b66a`). worktree·로컬·원격 정리(`--force` 없이 — 복사해 넣은 `settings.local.json` 만 먼저 제거). 삭제한 원격 tip `6b1a9e9`. `status: done`.

# Next

없음 — 종결. 효과 검증은 다음 `/improve` 에서 `early-stop-verify` 의 2026-08-18 이후 추이로 본다(인식 격차가 원인이었다면 줄어야 한다).

# Decisions

1. **[조사] 이 축은 대부분 이미 해소된 legacy 였다.** `early-stop-verify` 21세션/72회 중 `.md` 제외 fix(2026-07-17) **이전이 43건**, 이후 29건. 월별 7월 67 → 8월 5. 세션 브리프의 누적 카운트는 "지금 문제"의 크기가 아니다 — 조사 없이 상위 신호를 개선 후보로 직행시키면 안 된다는 사례.
2. **[근본 원인] 검증기 인식 격차.** 남은 발동의 파일 종류와 `VERIFY` 미인식 명령이 정확히 겹친다. 실측:

   | 신호 detail | 표준 검증 명령 | 기존 판정 |
   |---|---|---|
   | `compose.yaml` ×2 (8월) | `docker compose config` | MISS |
   | `security_workflow.css` (8월) | `stylelint`·`prettier --check` | MISS |
   | `smoke.sh`·`deploy.sh`·`pre-push` (7월) | `shellcheck` | MISS |
   | `.kt` ×14 (7월) | `./gradlew test` | **MATCH** |

   `.kt` 클러스터는 MATCH 라 **이 class 가 아니다**(진짜 미검증이거나 IDE 실행). 8월 5건은 전부 타 repo(`knowledge_base`).
3. **[해법] `VERIFY` 2분할.** `VERIFY_TOOLS`(그 자체가 검증: pytest·eslint·`shellcheck`·`stylelint`·`yamllint`·`hadolint`·`rspec`·`phpunit` 등) + `VERIFY_SUBCMD`(서브커맨드·플래그 필요: `docker compose … config`·`make (test|lint|check|verify|typecheck)`·`dotnet test`·`swift test`·`terraform validate`·`(prettier|black) … --check`).
   - 나눈 이유: `docker compose up`·`terraform apply`·`prettier --write`·`black .`·`make install`·`dotnet build` 는 **실행·적용이지 검증이 아니다**. 도구 이름만 보고 verified 로 치면 gate 가 헐거워진다(모듈 주석 "verified 오탐은 gate 를 헐겁게 하므로 보수적"). 음성 11케이스를 테스트로 락.
4. **[안 한 것] `.yaml`/`.json`/`.css` 를 `.md` 처럼 changed 게이트에서 빼지 않는다** — 깨진 compose·settings 는 실제 결함이라 미탐을 만든다. 인식을 넓히는 방향만 택했다.
5. **[입증 한계 — 단정 금지]** telemetry 는 "changed + not verified" 만 기록하고 **실제 실행 명령은 남기지 않는다.** 그 세션들이 정말 검증을 돌렸는지는 확인 불가 → "인식 격차가 존재한다"까지가 입증된 것이고 "발동이 전부 오탐"은 아니다. 효과는 다음 `/improve` 의 8월 이후 추이로 검증한다.

# Key Files

- `scripts/dlc-evidence-ledger.js` — `VERIFY` → `VERIFY_TOOLS` + `VERIFY_SUBCMD` 2분할·확장.
- `scripts/dlc-evidence-ledger.test.js` — 양성 17 + 음성 11 케이스.
- `README.md` — 2단 구조와 분할 이유 문서화.
- `wiki/pages/decision/workflow-failures.md` · `wiki/log.md` — 조사 결과·처방 적립.

# Acceptance

1. **오탐 축소**: 실제 발동 파일의 표준 검증기(`docker compose config`·`stylelint`·`shellcheck`)가 `verified=true`. 검증: 신규 양성 테스트.
2. **게이트 무완화(중요)**: `docker compose up`·`terraform apply`·`prettier --write`·`black .`·`make`·`make install`·`dotnet build`·`cat Makefile`·`echo make test` 는 `verified` 불변. 검증: 신규 음성 테스트.
3. **비회귀**: 기존 VERIFY/VERIFY_SCRIPT 케이스 전부 통과(`npm test`·`pytest`·`node --test`·`bash verify.sh`·`bash checkout.sh` 오인식 차단). 검증: 기존 테스트.
4. **전 스위트 + shellcheck + wiki**. 검증: 실행.
5. **문서 동기화**: README(`scripts/` 변경이라 evidence gate 대상) + workflow-failures 적립 + `wiki/log.md`. 검증: diff.

# Blockers

없음.

# Review Disposition

# Deferred

- `.kt` 14건(2026-07, coin-trading-bot) — `gradlew` 는 MATCH 라 인식 격차가 아니다. 진짜 미검증인지 IDE 실행인지는 transcript 를 봐야 알 수 있고 타 repo 라 이번 범위 밖. 7/29 이후 발동 없음.
