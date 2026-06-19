---
title: deferred-and-scope-boundary
category: decision
created: 2026-06-19
updated: 2026-06-19
sources:
  - CLAUDE.md (§1, §3-4, §3-5, §10)
  - plans/2026-06-18-claude-md-deferred-gate-2/claude-md-deferred-gate-2-plan.md
  - PR #50
---

# deferred-and-scope-boundary

범위 밖 발견을 *유실 없이 보존*하되 *고치지는 않는* 경계 규칙(PR #50, claude-md-deferred-gate → -2로 정제 머지). 작업이 요청 범위를 벗어나 번지는 것을 막는다.

## 세 규칙
- **운영 자산 자가 수정 금지**(§1): CLAUDE.md·agents/·skills/·settings는 명시 요청 없이 수정 안 함. "요청"이란 active plan `# Goal`/`# Key Files`에 그 자산이 들었거나 사용자가 자산명+변경을 지시한 경우. 그 외 개선점은 Report 제안으로만.
- **발견 = 기록 후 진행 / 수정 = 별도 작업**(§3-4): 범위 밖 발견은 [[plan-handoff|plan]]의 `# Deferred`(없으면 Report)에 한 줄(내용·심각도·파일)로 남기고 진행. 고치는 건 자가수정·스코프 경계상 별도 작업.
- **baseline failure 구분**(§3-5): 이번 변경이 깨뜨린 것만 수정 대상. 작업 전부터 깨진 실패는 *입증된 것만* `# Deferred`. 미입증·완료 막는 실패는 수정하거나 `status: blocked`(에러 무시 금지).

## # Deferred vs # Review Disposition
둘 다 plan 선택 섹션이나 다르다 — `# Review Disposition`은 리뷰 finding의 *처분 값*(fix/defer/false-positive/wontfix), `# Deferred`는 범위 밖 발견의 *보존 섹션*.

## 연계
self-diagnosis의 "스코프 밖 파일 수정" 중대 신호와 정합 — [[self-diagnosis-and-improvement-status]]. dlc 흐름은 [[dlc-development-cycle]].
