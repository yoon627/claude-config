---
title: dlc-wt-autoflow
category: decision
created: 2026-06-19
updated: 2026-06-19
sources:
  - skills/dlc/SKILL.md (진입 매트릭스·dlc→wt)
  - skills/wt/SKILL.md
  - CLAUDE.md (§3-1)
---

# dlc-wt-autoflow

dlc 가 **비trivial 변경인데 작업 worktree 밖이면 자동으로 wt 를 경유**해 worktree 안에서 진행한다. 기존에는 wt→dlc(한 방향)만 있어, `/dlc` 직접 진입 시 main 에서 작업할 여지가 있었다 — 이를 양방향으로 닫는다.

## 진입 매트릭스
요청 유형을 단일 기준 **"비trivial 변경인가"**로 분기([[worktree-per-task]] 의 강제 기준과 일치):
- 질문·탐색·읽기 전용 → dlc 미적용, 직접.
- trivial(오타·로그 1줄) → 현재 worktree 에서 dlc trivial, 새 worktree 불필요.
- 비trivial(small 이상) → **wt 경유 worktree → dlc 전체**.

## 순환 방지
wt→dlc(정상)와 dlc→wt(보강)는 **worktree 위치로 구분**한다. wt 가 요청사항으로 dlc 를 invoke 한 경우는 이미 worktree 안 → dlc 가 이 단계를 건너뛴다. `git worktree list --porcelain` 첫 worktree(=main)와 현재 cwd 비교로 판정.

## 자동이되 생성은 확인
"자동"은 *경로 선택*이 자동이라는 뜻 — wt 의 slug 확인(`AskUserQuestion`)은 유지한다. 무확인 worktree 생성은 하지 않는다(실수 생성 방지).

## 연계
완료 게이트는 [[evidence-gate]], dlc 파이프라인은 [[dlc-development-cycle]], plan 채널은 [[plan-handoff]].
