# Wiki Index

모든 페이지의 1줄 요약(카테고리별). ingest 시 갱신. 운영 규약은 `WIKI.md`.

## concept
- [[llm-wiki-pattern]] — 이 wiki 가 따르는 LLM Wiki 패턴(Karpathy): 영속·누적 markdown 지식베이스.
- [[project-memory]] — 이 wiki 의 목적·`plans/` 와의 경계(일시적 vs 영속).
- [[ingest-operation]] — raw/지식을 wiki 에 반영하는 연산 절차.
- [[dlc-development-cycle]] — 비자명 코드변경 개발사이클 오케스트레이션(규모 gate·16단계·격리).
- [[plan-handoff]] — 세션·도구 간 작업 컨텍스트 단일 plan 채널(§10·single-writer·active tracking).
- [[hub-and-spoke-isolation]] — 메인 hub(구현·통합·판단), reviewer 는 격리 read-only spoke.
- [[worktree-per-task]] — 작업마다 격리 worktree(wt skill·자동 bootstrap·삭제 조건).
- [[claude-codex-collaboration]] — Claude(구현·통합)↔Codex(리뷰·검증) 병행(§9·리뷰 매트릭스).
- [[feedback-memory]] — 사용자 교정의 영속화(§12·MEMORY.md 인덱스=행동지시문).

## entity
- [[anthropic-claude-models]] — Opus4.8/Sonnet4.6/Haiku4.5 가격·effort 지원(2026-06).
- [[claude-code-subagent-config]] — subagent frontmatter model/effort·env 우선순위·Haiku effort.

## decision
- [[subagent-model-effort-tiering]] — reviewer opus+max / simplifier sonnet / researcher haiku / 메인 high (#51).
- [[effort-os-env-single-source]] — OS env > settings.json, effort 레버 단일소스화 교훈.
- [[dual-review-plan-and-code]] — plan 리뷰(구현 전) + code 리뷰(구현 후) 관점 분리.
- [[deferred-and-scope-boundary]] — 범위 밖 발견 보존(# Deferred)·운영자산 자가수정 금지 (#50).
- [[self-diagnosis-and-improvement-status]] — 자기진단 있음(#49) / 자기개선 미머지 현황·재개 경로.
- [[comment-and-commit-policy]] — 주석 최소·변경 경위는 커밋/PR 에 (#26·#34·#25).
- [[codex-bash-invocation]] — codex 는 Bash 도구로 호출(PowerShell stdin hang 회피, #23).

## source
_(없음)_

## query
_(없음)_
