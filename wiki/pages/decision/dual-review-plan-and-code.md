---
title: dual-review-plan-and-code
category: decision
created: 2026-06-19
updated: 2026-06-19
sources:
  - CLAUDE.md (§5 Sub-agent)
  - skills/dlc/SKILL.md (파이프라인 단계 4·11)
  - agents/plan-reviewer.md, agents/code-reviewer.md
---

# dual-review-plan-and-code

리뷰를 **plan 단계**(구현 전)와 **code 단계**(구현 후)로 분리한 결정. 표준 순서: `plan-reviewer → 구현 → code-reviewer → code-simplifier → 최종 검증`([[dlc-development-cycle]]).

## 관점 차이
- **plan-reviewer**(구현 전): 누락 케이스·잘못된 가정·영향 범위·rollback·테스트 전략. 설계 허점은 코드 작성 전에 잡아야 rollback 비용이 낮다.
- **code-reviewer**(구현 후): 버그·보안·예외 처리·근본 원인·backward compatibility. 실제 코드의 오류.
- **code-simplifier**(통과 후 항상): 중복·과한 추상화·죽은 코드 제거. 동작 보존, mutating이라 메인이 재검증.
- **architecture-reviewer**(트리거 기반): public API·DB·DI·2계층+ 변경 시.

## 왜 분리인가
코드 리뷰만으로는 설계 오류·공격 벡터를 구현 후에야 발견 → 비용 큼. 단계를 나눠 각 시점에 맞는 결함을 잡는다. 비용은 규모 gate로 완화(trivial/small은 plan-reviewer 생략).

## 연계
격리 실행은 [[hub-and-spoke-isolation]], Codex 병행은 [[claude-codex-collaboration]], reviewer 모델 티어는 [[subagent-model-effort-tiering]].
