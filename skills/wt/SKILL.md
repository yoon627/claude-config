---
name: wt
description: Git worktree 빠른 관리 — 목록/이동/생성/제거. 신규 생성 시 ignored `.env` 파일을 main worktree 에서 동일 상대경로로 자동 복사. `.claude/worktrees/<name>/` 에 prefix 없는 브랜치(`<name>`)로 생성하여 EnterWorktree 도구의 `worktree-` prefix 문제를 회피. 사용자가 `/wt`, `/wt <name>`, `/wt <N>`, `/wt rm <name>` 형태로 호출할 때만 사용.
---

# wt — Git Worktree 관리

## 인자

`args` 토큰을 다음 규칙으로 해석:

| 입력 | 동작 |
|---|---|
| (빈 인자) | list |
| `<정수 N>` | list N번째 worktree 로 switch |
| `rm <name>` | remove |
| `<name>` | branch 정확일치 worktree 있으면 switch, 없으면 new 로 자동 생성 |

- 첫 토큰이 `rm` 이면 무조건 remove 로 해석 (worktree 이름으로 `rm` 사용 금지).
- 인덱스가 범위 밖이면 안내 + list.
- `rm` 뒤 인자 누락 등 형식 이상 → 위 표 출력 후 종료.

> **참고**: 단순 list 만 보고 싶을 때는 사용자가 PowerShell `gwl` 함수를 쓰는 것이 훨씬 빠름 (모델 왕복 없음). `/wt` 는 가공된 출력이나 후속 동작이 필요할 때만.

## 공통 규칙

- worktree path 는 항상 `.claude/worktrees/<name>` 으로 통일.
- 브랜치 이름 = worktree 이름 (1:1).
- **EnterWorktree 호출 시 항상 `path` 인자만 사용**. `name` 인자는 절대 쓰지 않는다 (prefix 자동 부착됨).
- 실행 전 git repo 안인지 확인 (`git rev-parse --show-toplevel`).
- 이름 검증: `^[a-zA-Z0-9._/-]+$`.

## list

`git worktree list` 결과를 `<path>  <sha>  [<branch>]` 형태로 인덱스(1-based) 와 함께 출력. 현재 cwd 와 일치하는 행 앞에 `→` 마커.

## switch

호출 경로 2가지:
1. `/wt <N>` (정수) — list N번째 worktree path 로 `EnterWorktree(path: <abs>)`. 범위 밖이면 안내 + list.
2. `/wt <name>` — `git worktree list` 의 branch 이름과 **정확일치**하는 worktree 1개 → `EnterWorktree(path: <abs>)`. 정확일치 0개면 new 로 폴백.

부분일치/모호 매칭 없음. 정확일치만.

## new (정확일치 없을 때 자동)

`/wt <name>` 매칭 worktree 0개일 때 자동 진행. 실행 직전 한 줄 보고에 **"신규 생성"** 임을 명시 (오타로 의도치 않은 생성 방지).

1. 이름 검증: `^[a-zA-Z0-9._/-]+$` 위반 시 중단.
2. 충돌 검사:
   - 기존 브랜치(`git rev-parse --verify --quiet refs/heads/<name>`) 존재 시 중단 — worktree 는 없지만 branch 가 살아있는 케이스. 사용자에게 안내 후 종료 (자동 checkout 하지 않음).
   - 디렉토리(`.claude/worktrees/<name>`) 존재 시 중단.
3. base ref: `git symbolic-ref --short refs/remotes/origin/HEAD` → 실패 시 `origin/main` 폴백.
4. `git fetch origin <default>` (실패해도 경고만).
5. `git worktree add --no-track -b <name> .claude/worktrees/<name> origin/<default>` (`--no-track` 으로 새 브랜치 upstream 자동 설정 차단 → 첫 `git push` 시 global `push.autoSetupRemote=true` 가 `origin/<name>` 으로 set).
6. **`.env` 자동 복사** (옵트아웃 없음):
   - source = main worktree path = `git worktree list --porcelain` 의 첫 `worktree <path>` 라인. 현재 cwd 가 worktree 안이어도 항상 main 기준.
   - 후보 = `git -C <main> ls-files --others --ignored --exclude-standard` 결과 중 basename 이 정확히 `.env` 인 행. (디렉토리째 ignored 된 캐시 안 `.env` 는 git 이 listing 에 넣지 않으므로 자동 제외됨.)
   - 추가 제외 (정규식, 어느 세그먼트에서든 매치): `(^|/)(\.venv|node_modules|__pycache__|\.uv-cache|\.cache|dist|build)/` — 디렉토리 단위가 아닌 패턴 ignore 케이스 대비 안전망.
   - 각 후보를 동일 상대경로로 `.claude/worktrees/<name>/` 안에 복사. 부모 디렉토리 없으면 mkdir. **이미 같은 경로에 파일 존재하면 skip (덮어쓰지 않음)**.
   - 복사 실패 (권한 등) 는 경고만 출력하고 worktree 는 유지.
7. `EnterWorktree(path: <repo-root>/.claude/worktrees/<name>)`.
8. 새 cwd 에서 `tools/bootstrap/bootstrap.py` 가 있으면 `uv run tools/bootstrap/bootstrap.py` 실행 (없으면 skip — 다른 프로젝트 무영향). 실패해도 worktree 는 유지하고 에러를 사용자에게 그대로 보고 (사용자가 원인 보고 수동 재실행 결정).
9. 한 줄 보고. "신규 생성" 명시 + `.env: N copied, M skipped` (둘 다 0 이면 생략) + bootstrap skip/실패 사실.

## rm `<name>`

1. `<name>` 미지정 → 사용법 안내 + list.
2. 매칭: 정수면 list N번째, 아니면 branch 이름 **정확일치** 1개.
3. 0개 → 안내 + list. (정확일치만 하므로 2개+ 모호 케이스 없음.)
4. 안전 검사:
   - 메인 worktree 거부.
   - cwd 가 대상 하위면 거부 + 다른 worktree 로 switch 안내.
   - 대상에서 `git status --porcelain` 비어있지 않으면 경고.
   - unpushed 커밋 있으면 경고 (`git log origin/<branch>..<branch>` 또는 upstream 없으면 `git log <branch> --not --remotes`).
5. AskUserQuestion (옵션 1: worktree 만 / 옵션 2: worktree + 브랜치 / 옵션 3: 취소). 경고는 question 본문에 명시.
6. 실행: `git worktree remove <path>`. "modified or untracked files" 류 실패 시 `--force` 적용 여부 별도 AskUserQuestion (절대 묻지 않고 강제 실행 금지). 옵션 2 선택 시 `git branch -D <branch>`.
7. 한 줄 보고.

## 주의

- `git worktree remove --force`, `git branch -D` 는 사용자 명시 확인 없이 실행 금지.
- `/wt <name>` 정확일치 없을 때 자동 new — 이름 오타로 의도치 않은 worktree 생성 가능. 실행 직전 한 줄 보고에 "신규 생성" 임을 명시해 사용자가 즉시 알아챌 수 있게 함.
- EnterWorktree 후 후속 명령은 새 cwd 기준.
