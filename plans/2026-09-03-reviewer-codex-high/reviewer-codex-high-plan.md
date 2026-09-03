---
title: reviewer-codex-high — code-reviewer 의 codex 병행을 high·브랜치 전체 diff 로 강화(pre-push 게이트 대체)
status: done
started: 2026-09-03
updated: 2026-09-03
---

# Goal

coin-trading-bot 의 pre-push codex 게이트를 제거하는 결정(2026-09-03)에 맞춰, 구현 후 code-reviewer 의 codex 병행이 그 역할(브랜치 전체 diff·high·P0/P1 우선)을 넘겨받도록 `docs/codex-review.md` effort 표와 `agents/code-reviewer.md` 프롬프트를 갱신한다.

# Progress

- 2026-09-03: effort 표 행 분리(plan/소규모 medium, 구현 후 병행 high), 범위 규칙 bullet 추가, code-reviewer 호출 조건·프롬프트 갱신. 문서 변경만 — 실행 검증은 크레딧 복구 후 첫 dlc 에서 codex 출력으로 확인(Deferred).

# Next

- PR 머지로 종료.

# Decisions

- `codex-review.md` 가 규약 단일 소스이므로 effort·범위는 거기에 두고 agent 는 참조만 한다.
- pre-push 가 하던 P2/P3 ACK 절차는 옮기지 않는다 — reviewer 의 finding 처분(`# Review Disposition`)이 같은 역할.

# Key Files

- `docs/codex-review.md` — effort 표·범위 bullet.
- `agents/code-reviewer.md` — 호출 조건·프롬프트.

# Blockers

# Deferred

- 크레딧 복구 후 첫 비trivial dlc 에서 codex 가 실제로 `git diff <base>...HEAD` 를 실행해 브랜치 전체를 봤는지 출력으로 확인(중).
