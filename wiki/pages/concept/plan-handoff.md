---
title: plan-handoff
category: concept
created: 2026-06-19
updated: 2026-06-19
sources:
  - CLAUDE.md (§10 plans 핸드오프 규약)
  - skills/c/SKILL.md
  - skills/e/SKILL.md
---

# plan-handoff

세션·도구 간 작업 컨텍스트를 단일 plan 파일로 공유하는 규약(CLAUDE.md §10). 경로 `plans/<YYYY-MM-DD>-<slug>/<slug>-plan.md`. [[project-memory]]의 *일시적* 절반 — 작업이 끝나면 닫히고, 재사용 지식만 wiki로 일방향 승격된다.

## frontmatter + 6섹션
`title·status(in_progress|blocked|done)·started·updated` + `# Goal / Progress / Next / Decisions / Key Files / Blockers`. 선택 섹션: `# Review Disposition`(리뷰 finding 처분), `# Deferred`(범위 밖 발견 — [[deferred-and-scope-boundary]]).

## 핵심 원칙
- **single-writer**: 메인 에이전트만 plan을 쓴다. subagent는 읽기만, 결과는 "plan 반영용 요약"으로 반환. 쓰기 직전 re-read로 외부 변경 merge. (이유: Claude↔Codex 동시 쓰기 충돌 방지 — [[claude-codex-collaboration]])
- **active plan tracking**: branch가 slug와 안 맞아도 세션에서 진행 중이던 plan을 계속 추적(branch 매칭은 *처음 찾는* 수단일 뿐).
- **진행 중 동기화**: 방향/스코프/결정 변경은 턴 종료까지 미루지 말고 **즉시** plan에 반영.

## 도구
- `/c`(plan-continue): plan 찾기 + plan↔실제(git/코드) sync 진단 + 다음 액션 제시(자동 실행 안 함).
- `/e`(plan-end): Progress/Next/status 기록 + uncommitted를 WIP 커밋 보존 + worktree 정리 제안 + main 복귀.

## 경계
plans/는 gitignored이고 [[worktree-per-task]]별로 독립 — 충돌·진행중 작업 판단의 실시간 소스. [[dlc-development-cycle]]이 이 채널로 작업을 추적한다.
