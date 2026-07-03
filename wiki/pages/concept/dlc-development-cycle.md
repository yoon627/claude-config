---
title: dlc-development-cycle
category: concept
created: 2026-06-19
updated: 2026-07-03
sources:
  - skills/dlc/SKILL.md
  - CLAUDE.md (§3 작업 흐름, §5 Sub-agent)
---

# dlc-development-cycle

비자명한 코드 변경(버그 수정·기능 추가·리팩토링)을 시작할 때 적용하는 개발 사이클 오케스트레이션 skill. CLAUDE.md §3 작업 흐름의 구체화 버전(충돌 시 CLAUDE.md 우선). 메인이 hub, 리뷰/검토만 격리 subagent([[hub-and-spoke-isolation]]). `/dlc` 명시 호출 또는 비자명한 코드 변경 시 자동 적용.

## 규모 gate
변경 규모를 판정해 도는 단계를 차등한다 — 작은 변경에 과한 절차를 피하기 위함.
- **trivial**(오타·로그 1줄): 구현→검증→Report (리뷰/plan/TDD 생략).
- **small**(<50줄, 단일 모듈): Explore→(버그면 TDD Red)→구현→code-reviewer→검증.
- **medium**(50~150줄): small + draft plan→plan-reviewer→code-simplifier.
- **structural**(다계층·public API·DB·신규 service·150줄+): 전체 16단계 파이프라인.
- 규모는 **예비값** — Explore 후·구현 diff 후 재판정해 승급하면 skip한 단계를 되살린다.

## structural 파이프라인 (요지)
Setup → Explore → draft plan → plan-reviewer → TDD Red → 구현 → Green → code-reviewer+architecture-reviewer(병렬) → fix loop(≤2) → code-simplifier → targeted 재리뷰 → 최종 검증 → Report. 최종 검증은 격리 runner가 실행하고 메인이 판단.

## 요구사항 명확화 게이트
규모 판정 직후, 요구의 공백(완료기준·범위·산출물·제외)이 acceptance를 바꾸면 `AskUserQuestion`. 공백 없으면 침묵 진행. "무엇이 빠지면 질문, 방법만 갈리면 분석 후 추천".

## 자기 진단 vs 자기 개선
dlc에는 작업 단위 가드인 **자기 진단(self-diagnosis)**이 있다(이번 작업이 `# Next`·규모표를 이탈하나). 규약 자체를 고치는 **자기 개선**은 수집(hook 신호 자동 누적)·분석(`/improve` 랭킹 제안)까지 기계화됐고, 반영은 사용자 승인 게이트다(2026-07-03) — [[self-diagnosis-and-improvement-status]].

## 연계
plan은 [[plan-handoff]]이 단일 채널. Explore 시 [[ingest-operation]]으로 wiki 조회, Report 시 ingest 제안. 이중 리뷰는 [[dual-review-plan-and-code]]. Verify 단계의 주석·커밋 현행성 점검은 [[comment-and-commit-policy]].
