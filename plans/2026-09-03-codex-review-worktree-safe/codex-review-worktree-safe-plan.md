---
title: codex-review-worktree-safe — codex 정본 호출을 worktree 격리 가드에 안 걸리는 형태로 갱신
status: done
started: 2026-09-03
updated: 2026-09-03
---

# Goal
`docs/codex-review.md` §3 정본(`--skip-git-repo-check` + heredoc)이 worktree 격리 세션의 네이티브 Bash 가드에 거부돼 CLAUDE.md §9 "codex 병행 필수"가 구조적으로 막히던 문제(plan e-merge-path Deferred major, wiki `worktree-isolation-bash-guard`). 정본을 "프롬프트는 스크래치 파일, 플래그 제거" 로 바꾸고 agents/README 를 동기화한다.

# Progress
- 2026-09-03: §3 정본 재작성, `agents/architecture-reviewer.md` 호출 예시 동일 형태로, README 한 줄. 새 정본을 worktree 에서 실제 실행(effort low smoke) → exit 0·응답 OK, 가드 미발동.
- 2026-09-03: code-reviewer(+codex low, 새 정본으로 병행 — 가드 활성 상태에서 첫 시도 통과) REQUEST CHANGES Major 4 → fix loop 1회(`0e76a88`) → APPROVE, Nit 반영(`ace6238`). `/e merge` PR #151.

# Next
- 없음 (PR #151 머지 시 완료).

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
- [x] code-reviewer 가 새 정본 형태로 codex 병행에 성공 — 검증: 리뷰 결과 "가드 활성 상태에서 첫 시도 통과, exit 0". 단 문서대로는 못 따라(`$SCRATCH`·Write 부재) 우회했음 → fix loop 로 정본 절차 교정.
- [x] agents·README 동기화 — 검증: `grep -rn "git diff --stat" agents/` 가 Claude 자체 조사 절차(code-reviewer:16)만 남고 codex 프롬프트 본문엔 0건; `skip-git-repo-check` 는 docs §3 사유·각주 2곳 + README 1곳(포인터)만.

# Review Disposition
code-reviewer(+codex low, 새 정본으로 병행) REQUEST CHANGES → fix loop 1회.
- fix — `$SCRATCH` 미정의 (Major): `<scratch>` 플레이스홀더 + "하네스가 주는 스크래치패드 절대경로, 셸 변수 아님" 명시.
- fix — reviewer 3종에 Write 도구 없음 (Major): 1단계를 도구 중립(Write 가용 시 / 아니면 Bash heredoc, 본문에 git 토큰 금지 — 통과 실증).
- fix — `agents/code-reviewer.md:77` `<git diff --stat …>` 잔존 (Major): `<diff --stat …>`.
- fix — §4 PowerShell `<` 미지원 (Major): `Get-Content -Raw | codex exec -` 를 1차 폴백(미검증 표기), here-string 은 파일 생성용으로 격하.
- fix — Minor 7: §5 출력 위치 통일·grep 중복 블록 주의, cwd 전제 1줄, 비-git 각주를 "병행 생략+사유" 로 결론, arch 예시의 명령 중복 제거(§3 포인터)+절대경로 참조, "git 토큰 금지" 를 Bash 생성 시 한정, README 포인터로 축약, plan acceptance 교정.
- wontfix — 펜스 nit(절차를 번호목록으로 이미 분리, 펜스엔 실행 한 줄만).
- false-positive(리뷰어 refuted 3건 동의) — README 범위·agents 절대경로 스큐·CDXPROMPT 잔존(§4 로 흡수).
- open(❌모름) — PowerShell 파이프의 stdin 종료 여부 → 문서에 미검증 표기.
