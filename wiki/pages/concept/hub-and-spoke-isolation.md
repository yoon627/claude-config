---
title: hub-and-spoke-isolation
category: concept
created: 2026-06-19
updated: 2026-07-04
sources:
  - skills/dlc/SKILL.md (격리 경계)
  - CLAUDE.md (§5 Sub-agent)
---

# hub-and-spoke-isolation

[[dlc-development-cycle]]의 실행 구조: 메인 에이전트가 **hub**(구현·통합·판단), 리뷰/검토/조사는 **격리 spoke** subagent. spoke끼리는 context를 공유하지 않고, 입력은 메인이 번들로 전달, 결과는 각자 "plan 반영용 요약"으로만 수신한다.

## 역할 분담
- **메인(hub)**: Setup, Explore(얇게 — 광범위 검색만 Explore agent 위임), draft plan, TDD Red, 구현, Green(최소 스모크), 통합, 검증 명령 식별·결과 판단, Report, 최종 판단.
- **격리 spoke(read-only)**: researcher, plan-reviewer, code-reviewer, architecture-reviewer.
- **최종 검증 runner**: 제3 범주 — 소스 불변, build/test 산출물만 생성. 메인이 식별한 명령을 worktree cwd 그대로 받아 실행만(해석·수리 안 함).
- **simplify 체크(구 code-simplifier)**: 2026-07-04 부로 격리 subagent 가 아니라 **메인 직접** 단계(dlc 13단계 체크리스트) — 실사용 0 으로 agent 제거. 이로써 mutating spoke 가 소멸해 **모든 spoke 는 read-only**(모델이 더 단순해짐). substantive 수정 시 targeted 재검증은 유지.

## 왜 격리인가
reviewer가 메인과 context를 공유하면 ① 메인의 미완 작업 메모가 리뷰 입력이 돼 불완전 리뷰 ② reviewer 수정을 메인이 다시 읽어 context 폭증. 완전 격리로 둘 다 차단하고, 각 reviewer는 정해진 관점만 본다.

## 연계
리뷰 관점 분리는 [[dual-review-plan-and-code]], Codex 병행은 [[claude-codex-collaboration]]. spoke의 model/effort 차등은 [[subagent-model-effort-tiering]].
