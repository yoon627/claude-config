---
title: workflow-failures
category: decision
created: 2026-06-19
updated: 2026-06-19
sources:
  - skills/dlc/SKILL.md (Workflow Findings)
---

# workflow-failures

dlc/규약 자체의 문제로 작업이 샌 **확인된 workflow 실패**를 작업을 가로질러 누적 추적한다 — [[dlc-development-cycle]] 의 Workflow Findings 가 plan(일시적)에 더해 여기에 영속 기록된다. 같은 실패가 2회 이상 누적되면 `wt` 로 해결을 제안한다.

## 추적 표
| 실패(깨진 규칙/단계) | 재발 조건 | 수정 후보 위치 | 횟수 | 상태 |
|---|---|---|---|---|
| _(아직 없음)_ | | | | |

- **기록 규칙**: 같은 실패면 새 줄 말고 기존 항목 횟수만 +1. 상태 = `tracking`(누적 중) / `proposed`(wt 해결 제안함) / `fixed`(수정 머지) / `wontfix`.
- **반복 해결**: 횟수 ≥2 → dlc 가 `AskUserQuestion` 으로 "이 실패 N회 반복 — wt 로 고칠까?" 제안. 수정은 사용자 승인 후 **wt→dlc**(운영 자산 자가수정 금지 — [[self-diagnosis-and-improvement-status]]).
- 단발(횟수 1)은 여기 남기되 해결 강제 안 함 — 반복돼야 패턴으로 본다.

## 연계
기록 트리거·형식은 [[dlc-development-cycle]], 자기개선 경계·미채택 이력은 [[self-diagnosis-and-improvement-status]], 완료 게이트는 [[evidence-gate]].
