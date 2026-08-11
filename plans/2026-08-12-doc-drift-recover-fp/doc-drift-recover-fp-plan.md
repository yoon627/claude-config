---
title: doc-drift-recover-fp — 동기화 후 재편집이 doc-drift 를 재-dirty 시키는 오탐 수정
status: in_progress
started: 2026-08-12
updated: 2026-08-12
---

# Goal

`dlc-doc-drift` 가 **이미 문서화한 surface 파일을 다시 편집하면 다시 dirty** 로 판정하는 오탐을 없앤다. 새 surface 는 계속 잡는다(미탐 도입 금지).

# Progress

- 2026-08-12: worktree 생성(base main@d3fc05a). 근본 원인 확정 — 아래 Decisions 1.
- 2026-08-12: **TDD 순서 준수** — 경계 9케이스 먼저 작성 → Red 확인(`actual: true, expected: false`, 의도한 이유) → `applyChange` covered-set 전환 → Green(56 assertions).
- 2026-08-12: 전 검증 통과 — 단위 10스위트·`node --check`·shellcheck·plan-lint·wiki clean. simplify 1건(도달 불가 `rel` null 가드 제거) 후 재통과.
- 2026-08-12: **e2e 실측**(실제 hook 경로 `dlc-evidence-ledger` → `dlc-early-stop`): ①미갱신→경고1 ②README 갱신→0 ③**같은 파일 재편집→0**(오탐 소멸) ④새 파일→경고1(미탐 미도입).

# Next

커밋 → PR → 머지 → worktree 정리.

# Decisions

1. **[근본 원인] 편집 순서 기반 last-write-wins 플래그.** `dlc-doc-drift.js:55-63` 의 `applyChange` 는 trigger 를 만나면 `dirty=true`, target(README/wiki index)을 만나면 `dirty=false` 로만 쓴다. 그래서 **동기화를 끝낸 뒤 trigger 파일을 한 번이라도 더 건드리면 다시 dirty** 가 된다. 문서 동기화는 *순서* 문제가 아니라 *상태* 문제인데 순서로 모델링한 것이 원인.
   - 이 세션 2회 재현: ① `scripts/*.js` → README 갱신 → simplify 로 `native-overlap-lint.js` 재편집 → readme 오탐 ② `wiki/pages/*` 4개 → `wiki/index.md` 갱신 → 대장에 `[!conflict]` 추가 → index 오탐. 둘 다 문서는 실제로 동기화돼 있었다(`improve.sh` 점검 6 `pages=40 = index=40`, README diff +15).
2. **[해법] covered-set.** target 을 편집하면 *그때까지 dirty 를 유발한 trigger 들*을 `covered` 로 넘긴다. 이후 **covered 에 든 파일의 재편집은 dirty 를 만들지 않고**, covered 에 없는 새 파일은 종전대로 dirty. 순서가 아니라 "이 파일이 이번 세션에 문서화됐나"를 본다.
   - 기존 계약 보존: `dlc-doc-drift.test.js:68-74` "README 먼저 → *새* surface 나중 → dirty" 는 그대로 통과한다(새 파일은 covered 에 없다).
3. **[해법 세부] copy-on-write 필수.** `ledger.DEFAULT` 는 `{...DEFAULT}` 로 얕은 복사돼 쓰인다(`dlc-ledger.js:20,34`, `dlc-signal.test.js:233`). 배열을 넣고 `push` 하면 **모든 세션이 DEFAULT 의 같은 배열을 공유·오염**한다 → `applyChange` 는 `concat` 으로 새 배열을 할당한다. 회귀 테스트로 못박는다.
4. **[해법 세부] 상한.** ledger 는 세션당 JSON 파일이라 무한 증가를 막는다 — covered/pending 각 **50개** 상한, 초과분은 버린다(초과 시 그 파일은 종전 동작=재편집 시 dirty. 미탐이 아니라 오탐 방향이라 안전).
5. **`readmeTrigger`/`indexTrigger` 는 유지** — `/improve` 가 오탐 패턴 식별에 쓰는 신호 detail(`dlc-ledger.js:12`). 의미 변경 없음.
6. **§7 TDD 순서 준수** — 방금 적립한 [[lesson-test-after-implementation]] 의 첫 적용. 경계(covered 히트/미스·상한·DEFAULT 오염·target 선행)를 테스트로 먼저 열거하고 Red 확인 후 구현.

# Key Files

- `scripts/dlc-doc-drift.js` — `applyChange` covered-set 전환(순수 모듈).
- `scripts/dlc-ledger.js` — `DEFAULT` 에 covered/pending 4필드.
- `scripts/dlc-doc-drift.test.js` — 경계 케이스 추가.
- `README.md` — doc-drift 설명에 covered-set 반영.
- `wiki/pages/decision/workflow-failures.md` — 확인된 workflow 실패 2회 기록(§13·dlc).

# Acceptance

1. **오탐 소멸(회귀)**: trigger → target → **같은 trigger 재편집** 시 `dirty=false` 유지. readme·index 양쪽. 검증: 신규 테스트.
2. **미탐 미도입**: trigger → target → **새 trigger** 시 `dirty=true`. 기존 `dlc-doc-drift.test.js:68-74` 도 그대로 통과. 검증: 신규 + 기존 테스트.
3. **DEFAULT 무오염**: `{...ledger.DEFAULT}` 로 만든 data 2개를 각각 `applyChange` 해도 서로·DEFAULT 에 영향 없음. 검증: 신규 테스트.
4. **상한**: covered 가 50 을 넘지 않는다. 검증: 신규 테스트.
5. **전 스위트 통과** + `shellcheck` + `plan-lint`. 검증: 실행.
6. **문서 동기화**: README 의 doc-drift 설명 갱신(이 변경 자체가 `scripts/` 를 건드리므로 evidence gate 대상). 검증: diff.
7. **실사용 확인**: 이 작업 자체가 `scripts/*.js` 를 고치고 README 를 갱신한 뒤 또 `scripts/*.js` 를 만지는 흐름이라 **수정 전이면 오탐이 재현되는 시나리오**다. 종료 시 Stop hook 이 README 오탐을 내지 않는지 관찰. 검증: 세션 종료 시 관찰.

# Blockers

없음.

# Review Disposition

# Deferred
