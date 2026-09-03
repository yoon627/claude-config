---
title: worktree-isolation-bash-guard
category: entity
created: 2026-09-03
updated: 2026-09-03
sources:
  - plan-reviewer 실측 4회 (plans/2026-09-02-e-merge-path # Progress — 2026-09-02, Claude Code 2.1.258)
  - 메인 세션 실측 (git -C <main>·perl -0pi 복합·bash "$HOME/.claude/…"·heredoc 본문 git 언급 거부 — 2026-09-02)
  - docs/codex-review.md (§3 정본 호출 명령)
---

# worktree-isolation-bash-guard

Claude Code(2.1.258 기준)가 `EnterWorktree` 로 격리된 세션에서 Bash 명령을 거부하는 네이티브 가드. 이 repo 의 `guard-worktree-edit.js`(Edit/Write 매처) 와는 별개이며, 메시지는 "This session is isolated in the worktree … Refusing to run it — a worktree-isolated session's git operations must target its own worktree." 형태다.

## 실측된 트리거 (2026-09-02)
거부 기준은 **"경로가 worktree 밖이냐"가 아니라 "명령 텍스트에 worktree 안에 머문다고 증명할 수 없는 git 언급이 있느냐"** 다.

| 명령 | 결과 |
|---|---|
| `git -C <main-path> show …` | 거부(명시적 밖 경로) |
| `bash "$HOME/.claude/skills/jira-worklog/run_worklog.sh"` | 거부 — 같은 스크립트를 상대경로 `bash skills/jira-worklog/run_worklog.sh` 로 부르면 통과 |
| `perl -0pi -e '…'` 복합 원라이너, 여러 명령을 `&&`·`;` 로 묶은 긴 한 줄 | 거부("too complex to verify") |
| `codex exec --sandbox read-only --skip-git-repo-check …` | 거부 — **플래그 이름의 `git`** 만으로 걸림 |
| heredoc 본문에 `git` 토큰이 여러 개 든 `cat >> file <<'EOF'` | 거부 — 본문에서 `git` 토큰을 빼면 통과 |
| 스크래치 파일에 쓴 스크립트 `bash <scratch>/x.sh`(내용에 `--skip-git-repo-check`) | 한 번은 통과, 거의 같은 형태가 다른 번엔 거부 |

즉 분류기는 **비결정적**이고 하네스 버전 의존이다. "worktree 상대경로만 쓰면 된다"는 규칙은 틀렸다(플래그명·heredoc 본문에도 걸린다) — 그래서 CLAUDE.md §8 에 규칙으로 올리지 않고 여기 관찰로 둔다.

## 혼동 주의 — repo 의 agent hook 오탐과 다른 기전
거부 메시지가 `PreToolUse:Bash hook error: Agent hook condition was not met: …` 이면 이 가드가 아니라 **repo `.claude/settings.json` 의 `type: agent` hook** 이다. coin-trading-bot 에서 code-reviewer 의 `codex exec` 가 막힌 2건(2026-08-22 06:54·2026-09-02 14:07)은 후자였다 — `if: Bash(git commit*)` 가 best-effort 라 `$`·backtick·heredoc 이 든 명령에 발화하고 프롬프트가 범위 자체 판정을 안 해 차단([[lesson-agent-hook-if-best-effort]], PR #165 수정). 이 가드의 메시지는 "This session is isolated in the worktree …" 로 시작한다.

> [!open] 위 표의 `codex exec --skip-git-repo-check` 행은 ~/.claude 세션 실측이다. coin-trading-bot 트랜스크립트에선 같은 명령의 거부가 전부 agent hook 쪽이었으므로, 이 가드가 플래그명만으로 거부하는지는 ~/.claude 세션에서 재확인 필요.

## 실용 우회
- 긴 payload(heredoc·PR body·프롬프트)는 `Write` 도구로 스크래치 파일에 쓰고, Bash 는 `cat a b > c`·`bash x.sh` 같은 짧은 평문으로.
- git 이 아닌 명령에 `git` 처럼 보이는 텍스트를 섞지 않는다(플래그·주석·문자열 포함).
- git 명령은 한 번에 하나씩, cwd 기준 상대경로로.
- 파일 수정은 Bash 대신 `Edit` 도구(가드 밖).

## 이 repo 에 준 영향
- `docs/codex-review.md` §3 정본 호출(`--skip-git-repo-check` 포함)이 worktree 세션에서 거부돼 CLAUDE.md §9 "codex 병행 필수"가 구조적으로 막힌다. 리뷰어들은 프롬프트를 파일로 빼고 그 플래그를 제거해 우회했다. 정본 갱신은 Deferred(major).
- 관련: [[codex-bash-invocation]](codex 호출 규약), [[worktree-per-task]](worktree 격리 원칙), [[workflow-failures]].
