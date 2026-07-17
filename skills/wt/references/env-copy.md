# env-copy — wt 신규 생성 시 `.env` 자동 복사 메커닉 (참조)

`wt` request 경로의 worktree 생성 §4.4 `.env` 자동 복사(옵트아웃 없음)의 **후보 선정·제외 규칙**을 담는다. SKILL 본문엔 "main 에서 basename `.env` 복사, 이미 있으면 skip, 실패 경고만"만 남기고 세부는 여기로.

> 이 파일은 자동 로드되지 않는다 — `wt` 가 **worktree 를 새로 생성(request §4.4 `.env` 복사)할 때** 이 파일을 Read 한다. "복사한다·덮어쓰지 않는다·실패해도 worktree 유지"라는 동작 골격은 SKILL 본문이 단일 소스이고, 여기는 "어떤 파일을 후보로/제외로 고르나"만.

## 후보 선정
- **source = main worktree path** = `git worktree list --porcelain` 의 첫 `worktree <path>` 라인. 현재 cwd 가 worktree 안이어도 **항상 main 기준**.
- **후보 = `git -C <main> ls-files --others --ignored --exclude-standard`** 결과 중 basename 이 정확히 `.env` 인 행. (디렉토리째 ignored 된 캐시 안 `.env` 는 git 이 listing 에 넣지 않으므로 자동 제외됨.)

## 추가 제외 (정규식, 어느 세그먼트에서든 매치)
`(^|/)(\.venv|node_modules|__pycache__|\.uv-cache|\.cache|dist|build)/` — 디렉토리 단위가 아닌 패턴 ignore 케이스 대비 안전망.

## 복사
- 각 후보를 **동일 상대경로**로 `.claude/worktrees/<slug>/` 안에 복사. 부모 디렉토리 없으면 mkdir.
- **이미 같은 경로에 파일 존재하면 skip (덮어쓰지 않음).**
- 복사 실패(권한 등)는 경고만 출력하고 worktree 는 유지.
- 보고: `.env: N copied, M skipped` (둘 다 0 이면 생략).
