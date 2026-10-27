# skills/wt 규칙 목록 (translate-skill-wt)

origin/main 142e11e 의 `skills/wt/SKILL.md`(134줄)·`references/env-copy.md`(33줄)·`references/rm-recovery.md`(23줄) 기준. 한 줄 = 한 조항(한정어도 조항의 일부). 번역 대조는 `locations-en.txt`(`<id> | <영어 인용>`, 다른 파일이면 `<경로>:: <인용>`, 인용 여러 개는 ` ‖ `). 이 manifest 는 번역 초안 전에 만든다 — plan-reviewer 가 찾은 빠진 조항(R.3.4d·R.3.6c·R.4.1b·X.4f4)과 문구 보강(F.1·R.4.2·R.4.4·Q.0·Q.2d·X.4f·X.4g3·EC.5·EC.8·RR.3·RR.10·RR.11)은 같은 원문에서 리뷰 뒤 더했다(plan log).

## frontmatter
- F.1 description: 요약(list/switch/생성+dlc/remove), `/wt <N>`·기존 이름=switch, 그 외 텍스트(요청사항)=무확인 slug 로 새 worktree 생성 후 그 안에서 dlc, `?` 접두=질문 모드(AskUserQuestion 으로 구체화 후 같은 생성 경로)
- F.2 description: 언제 쓰나(worktree 생성·이동·삭제·목록, 코드 변경 요청의 worktree 진입)

## 인자 (SKILL)
- I.1 빈 인자 → list
- I.2 `<정수 N>` → N번째 worktree 로 switch
- I.3 `rm <name>` → remove
- I.4 기존 worktree branch 와 정확일치 → 그 worktree 로 switch
- I.5 접두 `?` → 질문 모드(AskUserQuestion 으로 구체화 후 요청사항 경로로 합류)
- I.6 그 외 모든 텍스트 → slug 파생 → worktree 생성(무확인) → 그 안에서 dlc
- I.7 해석 순서: 위에서부터 평가, 첫 매치에서 확정, 이후 규칙은 보지 않는다 — 표 행 순서가 아니라 이 순서가 우선순위의 단일 소스
- I.8 1) 빈 인자 → list 2) 첫 토큰 `rm` → remove(worktree 이름으로 `rm` 사용 금지)
- I.9 2.5) 첫 비공백 문자가 `?` → 질문 모드(`?` 제거한 나머지가 seed), `?rm foo`·`?123` 등도 토큰/정수/정확일치와 무관하게 질문 모드
- I.10 3) 인자 전체가 정수 → switch(범위 밖이면 안내 + list) 4) 인자 전체가 기존 branch 와 정확일치 → switch 5) 그 외 전부 → 요청사항
- I.11 `rm` 뒤 인자 누락 등 형식 이상 → 표 출력 후 종료
- I.12 dlc 없는 단순 생성(빈 worktree 만 만들기)은 없다 — 정확일치하지 않는 텍스트는 항상 요청사항
- I.13 참고: 단순 list 만 볼 때는 셸 `gwl` 함수(`scripts/gwl.ps1`·`scripts/gwl.zsh`)가 빠르다(모델 왕복 없음), `/wt` 는 가공된 출력이나 후속 동작이 필요할 때만

## 공통 규칙
- C.1 worktree path 는 항상 `.claude/worktrees/<name>`
- C.2 브랜치 이름 = worktree 이름(1:1)
- C.3 EnterWorktree 는 항상 `path` 인자만, `name` 인자는 절대 쓰지 않는다(prefix 자동 부착)
- C.4 실행 전 git repo 안인지 확인(`git rev-parse --show-toplevel`)
- C.5 이름(slug·rm 대상) 검증 `^[a-zA-Z0-9._/-]+$`, 요청사항 원문은 검증 대상이 아니고 파생된 slug 가 만족해야 한다

## list
- L.1 `git worktree list` 를 `<path>  <sha>  [<branch>]` 로 인덱스(1-based)와 함께, 현재 cwd 행 앞에 `→`

## switch
- S.1 대상 해석: `/wt <N>` → list N번째(범위 밖이면 안내 + list) / `/wt <기존이름>` → branch 정확일치 1개, 0개면 request 로 폴백
- S.2 부분일치·모호 매칭 없음, 정확일치만
- S.3 worktree 세션 안에서 EnterWorktree 는 `.claude/worktrees/` 하위만 받는다(main 은 못 들어간다) — 그래서 대상이 main 인지로 도구를 가른다
- S.4 main 판정 = path 기준(브랜치명 아님): 대상 path == porcelain 첫 `worktree <path>`, `/wt 1`·`/wt <main브랜치명>` 둘 다 이 판정
- S.5 대상이 main 이고 이미 cwd 가 main 이면 ExitWorktree 없이 "이미 main" 보고
- S.6 아니면 `ExitWorktree(action: keep)` — 복귀 성공이면 완료, "활성 worktree 세션 없음" no-op 이고 cwd 가 여전히 worktree 면 자동 복귀 불가를 안내(새 세션·수동 이동)
- S.7 세션 이력을 추측하지 말고 툴 반환으로 판정
- S.8 대상이 하위 worktree 면 `EnterWorktree(path: <abs>)`

## request
- R.0 정수도 `rm` 도 정확일치도 아닌 모든 텍스트는 요청사항, 원문은 worktree 생성 뒤 dlc task 로 그대로
- R.1 slug: 짧은 kebab-case(ASCII 소문자/숫자/`-`, ≤ ~30자, 패턴 만족)
- R.1b 한글·비ASCII 요청은 핵심 의미를 영문으로 요약해 slug 화(예: "로그인 리다이렉트 버그 수정" → `login-redirect-fix`)
- R.1c 동사+대상 중심, 불용어 제거
- R.2 충돌: 기존 브랜치(`git rev-parse --verify --quiet refs/heads/<slug>`)·디렉토리 존재 시 `<slug>-2`… 비어 있는 첫 후보를 자동 채택하고 §4 보고에 표시
- R.3 생성은 확인 없이 — 로컬·비파괴이고 `/wt rm <slug>` 로 되돌아가므로 slug 승인을 묻지 않고, 되돌릴 정보를 §4 보고에
- R.3.0 main dirty 확인(`git status --porcelain`) — 요청 대상 파일이 dirty 면 새 worktree 에 그 편집이 담기지 않으므로 생성 전에 보고(§1 — 옛 버전을 고치면 머지 때 충돌하거나 사용자 편집을 되돌린다)
- R.3.1 `<default>` = symbolic-ref 에서 `origin/` 을 뗀 이름(실패 시 `main`), base ref 는 `origin/<default>`
- R.3.2 `git fetch origin <default>`(실패해도 경고만 — 단 fetch 실패는 §4 보고에 stale base 로), fetch 후 `git rev-parse --short origin/<default>` 로 base sha 캡처(§4 보고값)
- R.3.3 `git worktree add --no-track -b <slug> .claude/worktrees/<slug> origin/<default>`(이유는 references §A)
- R.3.4 ignored 설정 자동 복사(옵트아웃 없음): main worktree 의 1) basename 이 정확히 `.env` 2) 경로가 정확히 `.claude/settings.local.json` 을 동일 상대경로로 복사
- R.3.4b 이미 있으면 skip(덮어쓰지 않음), 복사 실패는 경고만·worktree 유지
- R.3.4c 2) 를 복사하는 이유: Windows 등 repo 루트 파일을 쓰지 않는 경우 세션 작업 디렉토리의 파일을 읽어, 안 하면 권한 허용목록이 0개로 시작(§8 이 worktree 작업을 강제), 그 밖은 2.1.211 부터 main checkout 파일을 읽어 복사본은 보조
- R.3.4d 후보 선정 predicate·제외 규칙·앵커드 일치가 필요한 이유는 `references/env-copy.md`
- R.3.5 `EnterWorktree(path: <repo-root>/.claude/worktrees/<slug>)`
- R.3.6 새 cwd 에서 submodule self-heal(`heal_submodules.py`) → bootstrap(`tools/bootstrap/bootstrap.py` 있으면) 순서, heal 을 먼저(corrupt submodule 이 이후 단계를 죽이는 것 방지)
- R.3.6b 무엇이 실패해도 worktree 유지·에러 그대로 보고(사용자가 수동 재실행 결정)
- R.3.6c self-heal/bootstrap 상세는 `references/rm-recovery.md` §B
- R.4.1 생성·진입 뒤 새 worktree 에서 dlc Skill 을 요청사항 원문을 인자로 invoke
- R.4.1b 이후는 dlc 가 규모 gate 부터 파이프라인까지 진행
- R.4.2 dlc 시작 직전 보고(무확인 생성의 안전망 — 승인 대신 되돌릴 정보를 준다): "신규 생성: `<slug>` (base `origin/<default>@<short-sha>`) — 되돌리기 `/wt rm <slug>`"
- R.4.3 덧붙임: `.env: N copied, M skipped`·`settings.local: N copied, M skipped`(둘 다 0 이면 생략) / fetch 실패 stale base / heal·bootstrap skip·실패 / 충돌 suffix
- R.4.4 near-miss(오타 오생성 대비 — 묻지 말고 생성하되 되돌릴 길을 알린다): 요청사항 원문에 공백이 없을 때만, 정규화(소문자화 + `-`/`_`/`.` 제거) 후 기존 branch 와 일치하거나 Levenshtein ≤2 인 후보
- R.4.5 후보가 정확히 1개일 때만 "기존 `<name>` 오타였다면 `/wt rm <slug>` 후 `/wt <name>`", 0개면 침묵, 2개 이상이면 후보명만(되돌리기 명령 없음 — 잘못된 후보를 지목하지 않게)
- R.4.6 마지막 줄 "→ dlc 시작: <요청사항>"

## 질문 모드
- Q.0 요청이 막연해 바로 slug 로 굳히기 이를 때 접두 `?` 로 요구를 대화로 좁힌 뒤 request 에 합류, 접미 `?` 는 쓰지 않는다(일반 의문형과 충돌)
- Q.1 seed = 맨 앞 `?` 와 뒤 공백을 뗀 나머지, `/wt ?` 처럼 비어도 된다
- Q.2 무엇을/어디를/어떤 결과로 좁히는 질문, seed 가 비면 "무엇을 하려는지"부터
- Q.2b 한 번에 안 좁혀지면 추가로 물어 범위·대상·완료 기준 확정, `?` 자체가 신호라 최소 1회는 묻는다
- Q.2c 사용자가 취소/거부하면 아무것도 만들지 않고 종료
- Q.2d 추가로 물어도 확정되지 않으면 request 로 넘기지 않는다 — 더 묻거나 종료(모호한 채 §3 으로 넘기면 slug·dlc task 가 부실해진다)
- Q.3 확정된 요구를 요청사항 원문으로 request §1→§4 그대로(slug·충돌검사·생성·복사·dlc 재사용)

## rm
- X.1 `<name>` 미지정 → 사용법 안내 + list
- X.2 매칭: 정수면 list N번째, 아니면 branch 정확일치 1개
- X.3 0개 → 안내 + list(정확일치만이라 2개+ 없음)
- X.4a 메인 worktree 거부
- X.4b cwd 가 대상 하위면 거부 + 다른 worktree 로 switch 안내
- X.4c 대상 `git status --porcelain` 이 비어 있지 않으면 경고
- X.4d unpushed 커밋 경고(`git log origin/<branch>..<branch>`, upstream 없으면 `git log <branch> --not --remotes`)
- X.4e gitignored 산출물 점검(필수): `git worktree remove` 는 gitignored 파일을 경고 없이 함께 삭제, whitelist `.gitignore` 라 `.env`·settings.local 은 status 에 안 잡힌다
- X.4e2 `git -C <대상> status --porcelain --ignored` 로 인벤토리(`-C` 필수 — 대상이 cwd 가 아닐 수 있다), `.env`·secret 후보·미보존 산출물이 있으면 5단계 질문 본문에 명시(기본 유지)
- X.4e3 `plans/` 는 tracked 라 미커밋 plan·log 는 status 에 잡히고 remove 가 거부 — 커밋한 뒤 삭제
- X.4f 미머지 탐지(옵션 3 원격 삭제 판단 근거): `git branch --merged origin/<default>` 에 없거나 `git log origin/<default>..<branch>` 가 비어 있지 않으면 미머지
- X.4f2 단 `git branch --merged <default>`(로컬)에는 있으면 "로컬 default 에만 머지됨(origin 미반영)" 으로 구분(원격을 지우면 그 커밋의 원격 사본은 default 를 push 할 때까지 없다)
- X.4f3 원격 삭제(옵션 3)는 유실 위험이라 이 사실을 옵션 3 경고에 명시(e 는 조건4 게이트로 막지만 wt 는 수동이라 사용자 판단, 미탐지 시 삭제 안 함 전제)
- X.4f4 `<default>` = symbolic-ref 에서 `origin/` 을 뗀 이름(실패 시 `main`)
- X.4g worklog 미리보기: 지운 worktree 의 시간은 이름으로 고를 수 없어 등록 불가 — 거부 검사를 모두 통과했고 jira-worklog 가 있으면 대상의 디렉터리 이름으로 미리보기(POSIX `run_worklog.sh <이름>`, Windows `run_worklog.ps1 <이름>`, 격리 세션이면 `$HOME` 펼친 절대경로)
- X.4g2 출력에서 머리줄이 `[<이름>]` 인 블록만 읽는다(다른 branch 에도 맞을 수 있고 뒤에 삭제된 worktree 목록이 붙는다)
- X.4g3 머리줄에 티켓(`ticket=<키>`)과 합계(출력 글자 `합계`)가 있으면 5단계 본문에 "등록하지 않았다면 이 시간은 지운 뒤 등록할 수 없다 — 먼저 `--register`(upsert, 등록 차단(출력 글자 `등록 차단`)이면 사유 확인 후 `--allow-large-change`)"
- X.4g4 `ticket=(없음)` 이거나 `[<이름>] 세션 활동 없음` 이면 적지 않는다
- X.4g5 대상 머리줄도 "세션 활동 없음" 줄도 없으면(비0 포함 — Windows 는 비0 이 보이는지 모른다, #190) 미리보기 실패로 본문에
- X.4g6 등록은 대신 하지 않는다 — 삭제 확인과 별개의 동의
- X.5 AskUserQuestion(옵션 1 worktree 만 / 2 + 로컬 브랜치 / 3 + 로컬·원격 / 4 취소), 경고(unpushed·미머지·미등록 worklog)는 본문에, 원격 삭제는 그 경고를 본 사용자가 택할 때만
- X.6 실행 `git worktree remove <path>`
- X.6a "modified or untracked files"/"use --force" 류 → `--force` 는 별도 AskUserQuestion 후에만(묻지 않고 강제 금지)
- X.6b 파일 점유 류("Access is denied"·"being used"·"Directory not empty"·Windows "Invalid argument") → 자동 종료하지 않고 점유 프로세스를 알려 소유자 종료 후 재시도 안내(`--force` 는 OS 점유엔 무효), 부분 성공·`prune` 은 worktree-lifecycle §C
- X.6c 옵션 2·3: remove 성공 후에만 `git branch -D <branch>`(실패·거부 시 브랜치 보존)
- X.6d 옵션 3: 로컬 삭제 후 `git push origin --delete <branch>`(원격 ref 부재면 no-op·경고만)
- X.7 한 줄 보고

## 주의
- N.1 `--force`·`git branch -D`·원격 삭제는 사용자 명시 확인 없이 실행 금지(`wt rm` 은 사용자가 대상을 지목하는 §8(b) 경로 — 오타로 엉뚱한 것을 지울 수 있어 항상 확인, merged 면 묻지 않는 자동 정리는 §8(a) — `/e`·머지 직후 흐름)
- N.2 정확일치하지 않는 텍스트는 요청사항으로 새로 만들고 생성 전 확인은 묻지 않는다 — 오생성은 near-miss 보고 + `/wt rm <slug>` 로 되돌린다, 삭제 계열은 확인 유지(생성은 무확인·삭제는 확인)
- N.3 요청사항 path 는 생성 후 dlc 자동 실행, 단순 질문·탐색·읽기 전용이면 `/wt` 대신 현재 worktree 에서 직접
- N.4 EnterWorktree 후 후속 명령은 새 cwd 기준
- N.5 자동 복사는 신규 생성 경로만 — 그 경로로 만들지 않은 worktree 엔 settings.local 이 없을 수 있어 필요하면 main 에서 한 번 복사(`cp <main>/.claude/settings.local.json <worktree>/...`), 2.1.211+ 는 그 밖의 경우 불필요
- N.5b 일괄 소급 복사는 두지 않는다(사용자가 지운 파일을 되살릴 수 있고 wt 는 동기화 도구가 아니다)

## references/env-copy.md
- EC.1 request §3.4 자동 복사의 후보 선정·제외 규칙, 대상 두 종류(`.env`·`.claude/settings.local.json`), SKILL 본문엔 동작 골격만
- EC.2 파일명은 `.env` 시절 그대로(README·wiki 인벤토리가 인용)
- EC.3 자동 로드 안 됨 — worktree 를 새로 생성할 때 Read, 동작 골격은 SKILL 본문이 단일 소스, 여기는 후보/제외만
- EC.4 source = main worktree path(porcelain 첫 줄), cwd 가 worktree 여도 항상 main 기준
- EC.5 후보 목록 = `git -C <main> ls-files --others --ignored --exclude-standard`(ignored 만), 여기서 아래 두 predicate 로 고른다
- EC.6 A. basename 이 정확히 `.env`(디렉토리째 ignored 된 캐시 안 `.env` 는 listing 에 안 들어와 자동 제외)
- EC.7 B. repo-relative 경로가 정확히 `.claude/settings.local.json`(앵커드 일치, basename 매칭 금지)
- EC.8 앵커드 이유: 로컬 설정 상대경로는 하나(settings 문서), 2.1.211 부터 repo 루트 파일, worktree 세션은 main checkout 루트 파일(2.1.288 macOS 실측) — 예외(Windows·repo 루트가 홈·git 밖·소유자 다름)에서는 작업 디렉토리 파일을 읽어 복사 안 하면 허용목록 0개(§8 이 worktree 작업을 강제해 실사용 경로가 전부 해당) — 이 예외가 복사가 필요한 이유, 그 밖은 보조
- EC.9 옛 버전이 시작 디렉토리에 남긴 파일도 함께 읽고 규칙이 둘 다 적용 — worktree 에서 바로 시작한 세션이면 복사본 규칙도 더해지고, 그 뒤 main 에서 지운 allow 도 남는다, EnterWorktree 세션이 복사본을 읽는지는 문서에 없고 재지 않았다
- EC.10 basename·접두 매칭으로 넓히면 엉뚱한 파일(`.bak`·repo 루트 `settings.local.json`·중첩 worktree 사본)이 딸려온다
- EC.11 B 를 하나로 좁힌 이유: `.claude/` 아래 다른 ignored(`.credentials.json`·`history.jsonl`·`*.lock`·`*.bak`·`worktrees/`)는 성격이 달라 넓히면 위험만
- EC.12 후보가 ignored 파일이라는 점이 안전장치 — tracked·untracked-but-not-ignored 는 안 잡혀 커밋 위험 파일을 밀어넣지 않는다
- EC.13 추가 제외 정규식 `(^|/)(\.venv|node_modules|__pycache__|\.uv-cache|\.cache|dist|build)/`
- EC.14 동일 상대경로로 복사, 부모 디렉토리 없으면 mkdir
- EC.15 이미 있으면 skip(덮어쓰지 않음), 실패는 경고만·worktree 유지
- EC.16 보고 `.env: N copied, M skipped`·`settings.local: N copied, M skipped`(둘 다 0 이면 생략)

## references/rm-recovery.md
- RR.1 생성 git 시퀀스 상세(§3.1~3.3·3.6)와 rm 실패 stderr 분기(§6), SKILL 엔 절차·안전 게이트만
- RR.2 자동 로드 안 됨 — 생성 때 또는 rm 이 remove 실패로 분기할 때 Read, 안전 게이트는 SKILL 본문(`## 주의`·rm §6)이 단일 소스
- RR.3 A. `<default>`·fetch(실패해도 경고만)·`git worktree add --no-track …`
- RR.4 `--no-track` 이유: upstream 자동 설정 차단 → 첫 push 때 `push.autoSetupRemote=true` 가 `origin/<slug>` 로, track 두면 origin/<default> 로 잘못 향함
- RR.5 B. 순서대로, 무엇이 실패해도 worktree 유지·에러 보고
- RR.6 1) self-heal: `uv run --no-project python "${CLAUDE_SKILL_DIR}/heal_submodules.py"`, 중단된 submodule clone 복구 후 init, `.gitmodules` 없으면 no-op
- RR.7 bootstrap 보다 먼저인 이유: bootstrap 의 submodule update 가 corrupt 로 죽으면 이후 단계가 안 돈다
- RR.8 자동 복구를 거부하고 exit 1 로 멈추는 경우(어떤 deinit·삭제보다 먼저 판정): path 를 읽을 수 없을 때, module dir 이 `modules` 밖(`..`·절대경로), work tree 에 보존할 파일이 남았을 때(`.git` 은 `gitdir: ` gitlink 파일일 때만 뺀다) — clone 한 repo 의 `.gitmodules` 를 삭제 경로로 믿지 않기 위해, 멈춘 뒤엔 수동 복구
- RR.9 2) `tools/bootstrap/bootstrap.py` 있으면 실행, 없으면 skip
- RR.10 C. remove 실패 시 SKILL §6 이 stderr 로 분기, 안전 게이트·브랜치 삭제 순서는 SKILL 본문이 단일 소스, 여기는 파일 점유 분기의 이유만
- RR.11 파일 점유 류("Access is denied"·"being used by another process"·"Directory not empty"·Windows "Invalid argument") — 살아있는 프로세스가 파일(`.venv` 등)을 잡고 있다, 자동 종료하지 않고 안내 — 점유 프로세스가 이 세션 것인지 알 수 없고 경로 필터로는 사용자 서버와 구분 안 됨(`/e` 7단계는 같은 세션 것을 회수할 수 있다), `--force` 는 OS 점유를 못 푼다
- RR.12 부분 성공(등록 해제·디렉토리 잔존)은 별도 분기 — worktree-lifecycle §C

## 다른 파일이 가리키는 표지
- SKILL 절 이름 `## request`·`## rm`·`## 주의` 와 request §1~§4·§3.0~§3.6·rm 1~7 번호 — dlc("`skills/wt/SKILL.md` request §3~§4"), references("§3.4", "rm §6", "`## 주의`") 가 가리킨다. 번역 뒤에도 `request`·`rm` 은 그대로, `## 주의` → `## Cautions`(references 도 같은 머지에서).
- references 파일명 `env-copy.md`·`rm-recovery.md` 는 그대로.

## 핵심 문구 검색 세트
`/wt` · `rm <name>` · `?` · git worktree list · --porcelain · `.claude/worktrees/<name>` · EnterWorktree · `path` · ExitWorktree(action: keep) · git rev-parse --show-toplevel · ^[a-zA-Z0-9._/-]+$ · gwl · git symbolic-ref --short refs/remotes/origin/HEAD · git fetch origin <default> · git rev-parse --short origin/<default> · git worktree add --no-track -b <slug> .claude/worktrees/<slug> origin/<default> · .env · .claude/settings.local.json · heal_submodules.py · tools/bootstrap/bootstrap.py · `dlc` · Levenshtein · <slug>-2 · git status --porcelain · git log origin/<branch>..<branch> · --not --remotes · status --porcelain --ignored · git branch --merged origin/<default> · run_worklog.sh · run_worklog.ps1 · --register · --allow-large-change · #190 · git worktree remove · --force · git branch -D · git push origin --delete · prune · worktree-lifecycle.md · §C · 세션 활동 없음 · ticket=(없음) · 2.1.211 · ls-files --others --ignored --exclude-standard · push.autoSetupRemote=true · CLAUDE_SKILL_DIR · gitdir: · modified or untracked files · use --force · Access is denied · being used by another process · Directory not empty · Invalid argument · Unable to find current revision · 합계 · 등록 차단
