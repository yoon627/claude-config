---
title: self-diagnosis-and-improvement-status
category: decision
created: 2026-06-19
updated: 2026-06-19
sources:
  - skills/dlc/SKILL.md (자기 진단)
  - PR #49
  - plans/2026-06-14-self-improve-trigger/self-improve-trigger-plan.md
  - plans/2026-06-14-dlc-improvements/dlc-improvements-plan.md
---

# self-diagnosis-and-improvement-status

이 워크플로우의 "스스로 점검·개선" 능력의 현황. **자기 진단은 있고, 자기 개선은 아직 없다** — 둘은 다른 것이다.

## 자기 진단 (self-diagnosis) — 있음 (PR #49 머지)
[[dlc-development-cycle]]에 통합된 **작업 단위 가드**. plan write 시점에 "지금 행동이 `# Next`·규모표와 맞나"를 점검한다. 중대 신호(방향/요구 변경, 필요 단계 건너뜀, 스코프 밖 파일 수정, 격리 위반, 동일 실패 2회, 검증 허위 위험)면 **멈춤 + `AskUserQuestion` + 결정 대기**. *이번 작업*이 규약을 이탈하는지 본다.

## 자기 개선 (self-improvement) — 미구현
실수·교훈을 누적해 **규약 자체(CLAUDE.md/dlc)를 고쳐나가는 메타 루프**. dlc 16단계에 retrospect도 preflight invariant check도 없다.

> [!open] 두 plan-only 브랜치에 설계만 있고 **구현 미착수**(2026-06-14, macOS 머신 생성, 원격 보존):
> - **self-improve-trigger**: CLAUDE.md에 *자발적 실수기록 트리거* 1줄 추가(옛 lessons.md 실패=auto-load 없음 반복 회피, 자동로드되는 [[feedback-memory]] 활용). 부록: 쌓인 메모리 주기 소화(consolidation)를 `/schedule`로.
> - **dlc-improvements**: dlc에 ① preflight invariant check ② Report에 retrospect 흡수 ③ skip 조건 명확화 ④ plan 과잉갱신 경계. PR1(트리거)에 #2 의존.
> 재개 시: 두 작업은 CLAUDE.md §1/§12·skills/dlc/SKILL.md를 건드린다 → 그 영역 새 작업과 **충돌 가능**. plan은 `plans/2026-06-14-*/`에 복원됨.

## 보정
[[feedback-memory]] §12는 *사용자가 지시할 때* 저장 — self-improve-trigger가 노린 *자발적* 트리거와 다르다. 인프라는 있고 트리거가 빠짐. 범위 경계는 [[deferred-and-scope-boundary]].
