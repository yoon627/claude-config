# env-copy — wt 신규 생성 시 자동 복사 메커닉 (참조)

`wt` request 경로의 worktree 생성 §3.4 자동 복사(옵트아웃 없음)의 **후보 선정·제외 규칙**을 담는다. 대상은 두 종류다 — `.env`(민감정보)와 `.claude/settings.local.json`(권한 허용목록). SKILL 본문엔 "main 에서 복사, 이미 있으면 skip, 실패 경고만"만 남기고 세부는 여기로.

> 파일명은 `.env` 시절 그대로다(README·wiki 인벤토리가 인용) — 내용은 두 대상을 모두 다룬다.

> 이 파일은 자동 로드되지 않는다 — `wt` 가 **worktree 를 새로 생성(request §3.4 `.env` 복사)할 때** 이 파일을 Read 한다. "복사한다·덮어쓰지 않는다·실패해도 worktree 유지"라는 동작 골격은 SKILL 본문이 단일 소스이고, 여기는 "어떤 파일을 후보로/제외로 고르나"만.

## 후보 선정
- **source = main worktree path** = `git worktree list --porcelain` 의 첫 `worktree <path>` 라인. 현재 cwd 가 worktree 안이어도 **항상 main 기준**.
- **후보 목록 = `git -C <main> ls-files --others --ignored --exclude-standard`** (ignored 파일만 나열). 이 목록에서 아래 두 predicate 로 고른다.
  - **A. `.env`** — basename 이 정확히 `.env` 인 행. (디렉토리째 ignored 된 캐시 안 `.env` 는 git 이 listing 에 넣지 않으므로 자동 제외됨.)
  - **B. 권한 허용목록** — repo-relative 경로가 **정확히 `.claude/settings.local.json`** 인 행(앵커드 일치, basename 매칭 금지).

### B 를 앵커드 정확일치로 두는 이유
Claude Code 의 `localSettings` 스코프는 `<canonical git root>/.claude/settings.local.json` **이 경로 하나**다. worktree 는 자기 자신이 git root 라 main 의 파일을 상속하지 않아, 복사하지 않으면 worktree 세션의 권한 허용목록이 **0개**로 시작한다(CLAUDE.md §8 이 worktree 작업을 강제하므로 실사용 경로가 전부 여기 해당).

basename 이나 접두 매칭으로 넓히면 실제로 엉뚱한 파일이 딸려온다 — 이 repo 실측에서 같은 listing 에 `.claude/settings.local.json.bak`(백업)과 `settings.local.json`(repo 루트 — cwd 가 `$HOME` 인 세션 전용이라 worktree 와 무관)이 함께 나온다. 중첩 worktree 사본(`.claude/worktrees/<other>/.claude/settings.local.json`)도 같은 이유로 배제된다.

### B 대상을 하나로 좁힌 이유
`.claude/` 아래 다른 ignored 파일은 성격이 다르다 — `.credentials.json`(인증정보, 복사하면 유출면 확대) · `history.jsonl`(세션 이력) · `*.lock`(락) · `*.bak`(백업) · `worktrees/`(재귀). 넓히면 얻는 것 없이 위험만 는다.

### 후보 목록이 ignored 파일이라는 점 자체가 안전장치다
어떤 repo 가 `.claude/settings.local.json` 을 tracked 로 두면 애초에 후보에 안 잡히고(그 경우 worktree checkout 이 이미 갖고 있다), untracked-but-not-ignored 여도 안 잡혀 **커밋 위험 파일을 worktree 로 밀어넣지 않는다**.

## 추가 제외 (정규식, 어느 세그먼트에서든 매치)
`(^|/)(\.venv|node_modules|__pycache__|\.uv-cache|\.cache|dist|build)/` — 디렉토리 단위가 아닌 패턴 ignore 케이스 대비 안전망.

## 복사
- 각 후보를 **동일 상대경로**로 `.claude/worktrees/<slug>/` 안에 복사. 부모 디렉토리 없으면 mkdir.
- **이미 같은 경로에 파일 존재하면 skip (덮어쓰지 않음).**
- 복사 실패(권한 등)는 경고만 출력하고 worktree 는 유지.
- 보고: `.env: N copied, M skipped` · `settings.local: N copied, M skipped` (각각 둘 다 0 이면 생략).
