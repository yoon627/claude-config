---
title: self-diagnosis-and-improvement-status
category: decision
created: 2026-06-19
updated: 2026-06-19
sources:
  - skills/dlc/SKILL.md (자기 진단)
  - PR #49 (self-diagnosis), #46 (명확화 게이트), #47 (feedback 메모리)
  - plans/2026-06-14-dlc-improvements/dlc-improvements-plan.md (f698001 심의 종결)
  - self-improve-trigger@b9a9ede (폐기 — 원격 브랜치 삭제)
---

# self-diagnosis-and-improvement-status

이 워크플로우의 "스스로 점검·개선" 능력의 현황. **자기 진단은 채택**, 자기 개선은 능동 부분만 기존 메커니즘으로 채택 — 자발적 트리거·invariant-check 는 미채택, 단 **증거기반 finding 최소형은 2026-06-19 dlc 에 채택**(아래).

## 자기 진단 (self-diagnosis) — 채택 (PR #49)
[[dlc-development-cycle]]에 통합된 **작업 단위 가드**. plan write 시점에 "지금 행동이 `# Next`·규모표와 맞나"를 점검한다. 중대 신호(방향/요구 변경, 필요 단계 건너뜀, 스코프 밖 파일 수정, 격리 위반, 동일 실패 2회, 검증 허위 위험)면 **멈춤 + `AskUserQuestion` + 결정 대기**. *이번 작업*이 규약을 이탈하는지 본다.

## 자기 개선 (self-improvement) — 심의 종결 (2026-06-19)
실수·교훈을 누적해 **규약 자체를 고쳐나가는 메타 루프**를 별도로 둘지 검토했고, 결론은 "능동 부분은 기존 메커니즘으로 충분, 신규 일반 단계는 미채택"(dlc-improvements 브랜치 f698001 `done`, self-improve-trigger 폐기).

- **채택(이미 머지)**: 요구사항 명확화 게이트(#46), self-diagnosis(#49), feedback 메모리 인프라(#47 — [[feedback-memory]]). 계획했던 retrospect·gate·skip 명확화는 이들로 반영됨 → 별도 구현 불필요.
- **미채택 — self-improve-trigger(폐기)**: CLAUDE.md에 *자발적 실수기록 트리거*를 추가하려던 안. 원격 브랜치 삭제. [[feedback-memory]](§12, 사용자 지시 기반) + self-diagnosis(사후 감지)로 갈음.
- **미채택 — preflight invariant-check**: "변경 전 절대 깨면 안 되는 것 2~3개 선언" 안. 사유 — 개수·형식이 자의적·모호해 빈 체크리스트 의례로 전락 우려(over-engineering). 핵심 통찰(위험 변경 전 제약 인지)은 유효하나 일반 dlc 단계로 박을 형태가 아님. 실제 실패사례(RTK가 sha256 서명한 hook을 직접 편집 → RTK 실행 거부)는 feedback 메모리(`rtk-headroom-path-fix.md`) + #49 self-diagnosis로 부분 커버.
- **[채택 2026-06-19] 증거기반 finding 최소형**: 사용자 재요청으로 도입. 확인된 workflow 실패(중대 self-diagnosis·동일유형 2회)에만 plan `# Workflow Findings` 에 한 줄(깨진 규칙·재발 조건·수정 후보), 2회 누적 시 dlc/wiki 수정 *제안* 승격. **자동 수정은 여전히 안 함**(사용자 승인 후 별도). invariant-check 의 '빈 의례' 함정을 피한 형태 — [[evidence-gate]]·[[fablize-adopted-disciplines]].

## 함의
"자발적 자기개선 루프"는 **의도적으로 두지 않는** 것이 현재 결론이다 — 능동 트리거·일반 invariant 단계 대신, 사용자 지시 기반 [[feedback-memory]] + 사후 [[dlc-development-cycle|self-diagnosis]] 조합으로 간다. 향후 "특정 위험 변경 전 제약 인지"를 더 구체적 형태로 다룰 필요가 생기면 위 미채택 기록이 출발점이다. 범위 경계 규칙은 [[deferred-and-scope-boundary]].
