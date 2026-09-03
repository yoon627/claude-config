---
title: codex-review-worktree-safe — codex 정본 호출을 worktree 격리 가드에 안 걸리는 형태로 갱신
status: in_progress
started: 2026-09-03
updated: 2026-09-03
---

# Goal
`docs/codex-review.md` §3 정본(`--skip-git-repo-check` + heredoc)이 worktree 격리 세션의 네이티브 Bash 가드에 거부돼 CLAUDE.md §9 "codex 병행 필수"가 구조적으로 막히던 문제(plan e-merge-path Deferred major, wiki `worktree-isolation-bash-guard`). 정본을 "프롬프트는 스크래치 파일, 플래그 제거" 로 바꾸고 agents/README 를 동기화한다.

# Progress
- 2026-09-03: §3 정본 재작성, `agents/architecture-reviewer.md` 호출 예시 동일 형태로, README 한 줄. 새 정본을 worktree 에서 실제 실행(effort low smoke) → exit 0·응답 OK, 가드 미발동.

# Next
- code-reviewer(low, 새 정본으로 codex 병행 = 2차 smoke) → `/e merge`.

# Decisions
- `--skip-git-repo-check` 는 정본에서 제거 (이유: 리뷰는 항상 git repo(worktree) 안에서 돌아 불필요하고, 플래그명 자체가 가드에 걸린다). repo 밖 예외만 각주.
- 프롬프트는 heredoc 대신 Write 로 파일화 (이유: heredoc 본문의 `git diff` 언급이 가드에 걸리며 CLAUDE.md §2 긴 payload 규칙과도 일치).

# Key Files
- `docs/codex-review.md` — §3 정본
- `agents/architecture-reviewer.md` — 호출 예시
- `README.md` — codex 규약 줄

# Blockers
(없음)

# Acceptance
- [x] 새 정본을 worktree 세션에서 실행해 통과 — 검증: `codex exec … - < prompt.txt` exit 0, 응답 OK.
- [ ] code-reviewer 가 새 정본대로 codex 병행에 성공 — 검증: 리뷰 결과의 "Codex 병행: 실행함".
- [x] agents·README 동기화 — 검증: grep `skip-git-repo-check` 가 정본 각주 1곳만.
