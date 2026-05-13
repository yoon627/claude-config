---
name: wt
description: Git worktree 빠른 관리 — 목록/이동/생성/제거. `.claude/worktrees/<name>/` 에 prefix 없는 브랜치(`<name>`)로 생성하여 EnterWorktree 도구의 `worktree-` prefix 문제를 회피. 사용자가 `/wt`, `/wt list`, `/wt switch X`, `/wt new X`, `/wt remove X` 형태로 호출할 때만 사용.
---

# wt — Git Worktree 관리

## 인자

`args` 첫 토큰을 서브커맨드로 해석. 토큰 없으면 `list`.

| 서브커맨드 | 별칭 |
|---|---|
| `list` | `ls`, (빈 인자) |
| `switch <target>` | `sw`, `cd`, `s` |
| `new <name>` | `create`, `add`, `n`, `c` |
| `remove <name>` | `rm`, `delete`, `del` |

알 수 없는 서브커맨드 → 위 표 출력 후 종료.

> **참고**: 단순 list 만 보고 싶을 때는 사용자가 PowerShell `gwl` 함수를 쓰는 것이 훨씬 빠름 (모델 왕복 없음). `/wt list` 는 가공된 출력이 필요할 때만.

## 공통 규칙

- worktree path 는 항상 `.claude/worktrees/<name>` 으로 통일.
- 브랜치 이름 = worktree 이름 (1:1).
- **EnterWorktree 호출 시 항상 `path` 인자만 사용**. `name` 인자는 절대 쓰지 않는다 (prefix 자동 부착됨).
- 실행 전 git repo 안인지 확인 (`git rev-parse --show-toplevel`).

## list

`git worktree list` 결과를 `<path>  <sha>  [<branch>]` 형태로 인덱스(1-based) 와 함께 출력. 현재 cwd 와 일치하는 행 앞에 `→` 마커.

## switch <target>

1. `<target>` 미지정 → list 후 종료.
2. 매칭: 정수면 N번째, 아니면 path/branch 부분일치.
3. 0개 → 안내 + list. 2개+ → AskUserQuestion 으로 명확화. 1개 → `EnterWorktree(path: <abs>)`.

## new <name>

1. `<name>` 미지정 → 사용법 안내 후 종료.
2. 검증: `^[a-zA-Z0-9._/-]+$`.
3. 충돌 검사: 기존 브랜치(`git rev-parse --verify --quiet refs/heads/<name>`) / 디렉토리(`.claude/worktrees/<name>`) 존재 시 중단.
4. base ref: `git symbolic-ref --short refs/remotes/origin/HEAD` → 실패 시 `origin/main` 폴백.
5. `git fetch origin <default>` (실패해도 경고만).
6. `git worktree add -b <name> .claude/worktrees/<name> origin/<default>`.
7. `EnterWorktree(path: <repo-root>/.claude/worktrees/<name>)`.
8. 한 줄 보고.

## remove <name>

1. `<name>` 미지정 → list 후 종료.
2. switch 와 동일한 매칭.
3. 안전 검사:
   - 메인 worktree 거부.
   - cwd 가 대상 하위면 거부 + 다른 worktree 로 switch 안내.
   - 대상에서 `git status --porcelain` 비어있지 않으면 경고.
   - unpushed 커밋 있으면 경고 (`git log origin/<branch>..<branch>` 또는 upstream 없으면 `git log <branch> --not --remotes`).
4. AskUserQuestion (옵션 1: worktree 만 / 옵션 2: worktree + 브랜치 / 옵션 3: 취소). 경고는 question 본문에 명시.
5. 실행: `git worktree remove <path>`. "modified or untracked files" 류 실패 시 `--force` 적용 여부 별도 AskUserQuestion (절대 묻지 않고 강제 실행 금지). 옵션 2 선택 시 `git branch -D <branch>`.
6. 한 줄 보고.

## 주의

- `git worktree remove --force`, `git branch -D` 는 사용자 명시 확인 없이 실행 금지.
- 매칭 모호 시 임의 선택 금지 — AskUserQuestion 으로 명확화.
- EnterWorktree 후 후속 명령은 새 cwd 기준.
