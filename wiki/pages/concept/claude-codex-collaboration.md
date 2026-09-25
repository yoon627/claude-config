---
title: claude-codex-collaboration
category: concept
created: 2026-06-19
updated: 2026-09-25
sources:
  - 커밋 a3d7bdc (Codex AGENTS.md 심링크 단일 소스 결정)
  - CLAUDE.md (§9 Claude ↔ Codex 협업)
  - docs/codex-review.md
---

# claude-codex-collaboration

사용자는 Claude와 Codex 양쪽을 쓴다(CLAUDE.md §9). 둘 다 같은 `plans/` 핸드오프 채널을 공유하되, 역할은 나뉜다 — Claude는 plan 생성/갱신·메인 구현·통합, Codex는 리뷰·보조 구현·검증. **최종 통합 책임은 항상 현재 메인 에이전트.**

## 리뷰 매트릭스
- `plan-reviewer` / `code-reviewer` = **Claude subagent 필수 + Codex 가용 시 병행**. Codex 미가용이면 생략 사유를 Report/plan에 남긴다.
- `researcher` / 보조 구현 = 가용성·비용 대비 이득 있을 때 선택. (simplify 체크는 2026-07-04 부로 메인 직접 — 매트릭스 대상 아님)
- 한 phase에 reviewer가 여럿이면 codex owner 1개만 지정, 나머지는 `CLAUDE_REVIEW_CODEX_MODE=external`(중복 호출 방지).

## 왜 병행인가
Claude(컨텍스트 축적·통합)와 Codex(독립 뷰)가 같은 변경을 보면 단일 리뷰가 놓친 보안·구조 결함을 잡을 확률이 오른다. 실제로 "skill 라우팅 실패"를 plan-reviewer+Codex가 독립 발견한 전례가 있고, git 훅의 동기-pull hang 사각지대(사용자 macOS+HTTPS 환경 직격)를 code-review 병행이 Major 로 파낸 예도 있다 — [[git-hook-network-safety]].

## 호출 규약
Codex는 반드시 **Bash 도구**로 호출한다 — [[codex-bash-invocation]](PowerShell hang 회피). 무거운 작업 전 짧은 smoke test로 응답부터 확인.

## 연계
격리 구조는 [[hub-and-spoke-isolation]], 공유 채널은 [[plan-handoff]], 리뷰 관점 분리는 [[dual-review-plan-and-code]]. Codex 용 `AGENTS.md` 미러가 Claude 세션에 섞여 들어가는 경로와 차단은 [[claude-code-agents-md-loading]]. Codex 의 전역 지침 `~/.codex/AGENTS.md` 는 `CLAUDE.md` 심링크(단일 소스)이고 `~/.agents/skills/{c,dlc,e,improve,jira-worklog,wiki,wt}` 도 이 repo `skills/` 심링크다 — Codex 앱의 Claude import 가 사본으로 덮어쓰면 규칙이 갈라진다(2026-08-01 사례, 2026-09-25 복원).
