---
title: claude-md-deferred-gate — CLAUDE.md 에 Deferred 기록·운영 자산 자가 수정 게이트·§10 선택 섹션 추가
status: done
started: 2026-06-12
updated: 2026-06-19
---

# Goal
self-improvement loop 검토(ChatGPT 답변 비판)에서 승인된 "바로 반영" 3건을 CLAUDE.md 에 반영하고 PR 생성 (merge 는 사용자 보류).

# Progress
- 2026-06-19 브랜치 미머지지만 내용은 후속 claude-md-deferred-gate-2(PR #50)로 정제·반영 완료. 폐기 — status: done, worktree/브랜치 정리.
- 2026-06-12: 검토 완료(대화), 사용자 승인. worktree 생성, CLAUDE.md ①②③ + README 동기화 편집.

# Next
- code-reviewer 검토 → commit → push → PR 생성 (merge 안 함).

# Decisions
- ① `# Deferred` 기록 규칙은 §3-4(범위 밖 수정 금지 옆)에, baseline failure 구분은 §3-5 Verify 에 분리 배치 (각 단계 규칙 옆이 맥락상 맞음).
- ② 자가 수정 게이트는 §1 핵심 규칙에 — "사용자 변경사항 보호"와 같은 성격.
- ③ §10 은 필수 6개 유지 + 선택 섹션(Review Disposition, Deferred) 등재 — dlc 가 이미 쓰던 Review Disposition 미등재 비일관성 해소.
- 루프 정의 자체는 CLAUDE.md 에 중복 기재하지 않음 (dlc 단일 소스 유지 — 검토 결론).

# Key Files
- CLAUDE.md — §1·§3·§10 수정 대상
- README.md — 216~227행 CLAUDE.md 요약 동기화 (§3 문서 동기화 규칙)

# Blockers
(없음)
