# docs/worktree-lifecycle.md 규칙 목록 (translate-wiki-docs)

공용 wiki 3eaa4f4 의 `docs/worktree-lifecycle.md`(105줄) 기준. 한 줄 = 한 조항(한정어도 조항의 일부). 번역 대조는 `locations-en.txt`(`<id> | <영어 인용>`, 인용 여러 개는 ` ‖ `, `⏎` 는 줄바꿈, 각 인용은 파일 안에서 한 번, manifest 순서대로). 이 manifest 는 번역 초안 전에 만든다. 제목 줄은 설정의 `headings` 가 지킨다.

## 머리말
- P.1 `/e` SKILL 의 상태 수집(2단계)·머지 모드(M1~M6)·worktree 삭제 판정(7단계)·정리 실행(Worktree cleanup rules)·복귀 pull(step 8 ⓑ)의 git/gh 메커닉·폴백·엣지 처리를 담는다
- P.2 SKILL 본문엔 게이트·닫힌목록·안전 규칙만 남기고 세부는 여기로
- P.3 자동 로드되지 않는다 — `/e` 가 상태 수집·머지 모드(M1 진입)·worktree 삭제 판정/실행·복귀 pull 분기에 실제로 들어갔을 때 Read
- P.4 판정 골격(6조건 AND·자동삭제 금지·안전 게이트)은 SKILL 본문이 단일 소스, 여기는 "어떻게"만
- P.5 단 SKILL 의 submodule `--force` 예외가 묻지 않는 통과 기준(§C submodule 분기의 두 점검)은 여기가 정본
- P.6 범위: CLAUDE.md §8(a) 자동 정리(조건 충족 시 worktree + 로컬 브랜치를 묻지 않고)와 §8(b) 확인 경로(원격 브랜치 삭제·안전조건 미충족·`wt rm <이름>` 직접 호출)의 판정 메커닉을 함께 다룬다
- P.7 조건 판정은 같고 결과 처리만 갈린다 — 전부 충족이면 무확인 실행, 하나라도 불충족이면 정리 생략(강행 금지)
- P.8 원격 삭제는 언제나 AskUserQuestion(원격에 브랜치가 없으면 — 푸시한 적 없음·GitHub 자동 삭제 — 묻지 않는다, `/e` 7단계)
- P.9 `/e` 6단계 worklog 가 실패로 끝났으면 조건을 판정하지 않고 정리 생략(SKILL 6단계 비차단 bullet)

## A. collect-state
- A.1 `bash skills/e/collect-state.sh`(다른 repo·격리 세션의 호출 형태는 SKILL 2단계)가 개별 git 10+ 호출을 1회로 묶어 평문 `key: value` 로 반환하는 신호 목록(19개 필드)
- A.2 각 라인은 첫 `: ` 1회로만 split(경로 `C:/`·커밋 subject 의 `:` 보존)
- A.3 list 필드(`status`·`unpushed`·`remoteContainingHead`·`ignored`)는 들여쓰기 라인
- A.4 `git log --oneline`(plan 시작 이후 새 커밋)은 헬퍼 밖 별도
- A.5 점검 실패(origin 없음·status 오류)는 해당 필드 `none`/`unknown` — `false` 로 평탄화하지 않는다
- A.6 헬퍼 실패·필드 누락이면 보고에 명시하고 조건별 폴백 git 명령으로

## B. 삭제 판정 6조건
- B.0 SKILL 은 "6조건 AND + 하나라도 불충족/헬퍼불가면 제안 생략(보수)"만 명시, 여기는 각 조건 판정과 폴백
- B.1 비-메인 worktree: `root` ≠ `mainWorktree`
- B.1b 폴백 `git rev-parse --show-toplevel` vs `git worktree list --porcelain` 첫 `worktree <path>`
- B.1c 슬래시 방향·대소문자 normalize 후 비교(메인 책임 — 헬퍼는 raw path)
- B.1d 메인이면 제안 안 함
- B.2 detached=false + plan status==done: plan 의존이라 헬퍼 밖(4단계 확정값)
- B.2b detached 면 생략
- B.3 working tree clean(untracked 포함): `dirty`=false(`status` 빈), 폴백 `git status --porcelain`
- B.3b `dirty`=unknown(status 실패)이면 점검 불가 → 생략(보수)
- B.4 merged 판정(신호는 4a — 자동 정리의 핵심 게이트)
- B.4b unpushed 는 로컬 정리의 조건이 아니다: merged 면 커밋이 default 브랜치에 있어 로컬 브랜치를 지워도 잃을 게 없고, push 하지 않는 워크플로우라 게이트로 두면 자동 정리가 영영 안 돈다
- B.4c `unpushedStatus`·`unpushed` 는 원격 브랜치 삭제(§8(b), 항상 확인)를 판단할 때만 본다
- B.5 4a base 또는 다른 원격 브랜치에 merged(git-only 추정): (a)·(a′) 중 하나면 자동 정리 가능, (b) 만 있으면 확정이 아니라 확인 경로
- B.5a (a) 기본 base 포함: `baseValid`=true 이고 (`inBase`=true 또는 `patchInBase`=true)
- B.5a2 `inBase`=커밋 SHA 포함(ff/no-ff 머지), `patchInBase`=patch-equivalent 포함(`git cherry` — rebase merge 로 SHA 재작성돼도 전 커밋이 patch 로 있으면 감지)
- B.5a3 `baseValid`=false 면 skip
- B.5a4 폴백: `BASE`=`git symbolic-ref --short refs/remotes/origin/HEAD`||`origin/main`, `git rev-parse --verify --quiet <BASE>` 후 `git log <BASE>..HEAD` 빈지[inBase], 비어있지 않으면 `git cherry <BASE> HEAD` 의 `+` 가 0개인지[patchInBase]
- B.5b (a′) 로컬 default 포함: `mergedToLocalBase`=true, 헬퍼가 `git branch --merged <localDefault>` 로 판정, `localDefault` 는 `origin/HEAD` 뒷부분 → 없으면 실재하는 `main`/`master`
- B.5b2 origin 이 없거나 push 를 안 하는 repo 에서는 (a) 가 unknown 이라 이 신호만 남는다 — 로컬 main 머지도 정식 merged 로 인정
- B.5b3 폴백 `git branch --merged <localDefault> --format='%(refname:short)' | grep -qx <branch>`
- B.5c (b) 다른 원격 브랜치 포함(ticket-to-ticket 머지): `remoteContainingHead` 에서 self·`origin/HEAD -> ...` 제외하고 남는 원격 브랜치가 있으면 거기 머지됐을 가능성
- B.5c2 진행 중인 다른 브랜치가 내 커밋을 조상으로 쌓은 경우도 포함되니 확정 아님 → 그 브랜치명 근거로 AskUserQuestion 본문에 "`<HEAD7>` 가 `<remote-branch>` 에 포함 — 머지됐을 수 있으나 진행 중일 수도(확정 아님)" 명시
- B.5c3 폴백 `git branch -r --contains HEAD`
- B.5d (a)·(a′)·(b) 모두 신호 없으면(self 만·BASE 미포함) 미머지로 보고 생략·유지
- B.5e 한계: squash merge(N커밋→1)는 patch-id 가 합쳐져 cherry 도 못 잡아 미머지로 보임(stale 원격 ref·rebase 충돌해소도) — 전부 유지 방향이라 안전
- B.5e2 PR 상태 직접 조회는 인증·headless 때문에 안 씀 — git-only 추정 + 사용자 확인
- B.5e3 1순위 = false-positive(미머지 삭제) 차단이라 (b)·`patchInBase` 는 "근거 제시"로만
- B.6 미보존 산출물 점검: `git worktree remove`(--force 없이)는 gitignored 파일 무경고 동반 삭제, `--force` 는 미커밋 산출물도 삭제
- B.6b whitelist `.gitignore` 라 `.env` 등 gitignored 는 `git status` 안 보임(plans/ 는 tracked 라 미커밋 plan 은 보이고 remove 거부되나 `--force` 로는 유실)
- B.6c `ignoredStatus`=unknown 이면 생략(보수)
- B.6d `ignored` 목록(폴백 `git status --porcelain --ignored`) + `git status --short` 점검
- B.6e 이 worktree `plans/` 에 이번에 갱신한 미커밋 plan·plan log 가 있으면 제안 생략(방금 done 기록한 plan 소실 방지; 브랜치 commit·push 또는 main worktree `plans/` 이동 뒤에야 안전)
- B.6f `.env`·secret 후보·기타 산출물 있으면 정리 생략하고 그 목록을 보고에 명시(유실 방지), 지워도 되는지는 사용자 판단
- B.7 worktree 를 잡은 프로세스 없음: 이 세션이 띄운 서버·데몬이 잡고 있으면 `git worktree remove` 가 OS 단계에서 실패 — 경로로 특정해 회수하고, 못 하면 정리 생략(SKILL 7단계 조건6, 실패 분기는 §C 파일 점유)
- B.r1 조건 전부 충족 → 무확인 실행: worktree → 로컬 `git branch -d`, 삭제한 브랜치 tip sha 한 줄 보고(`git branch <name> <sha>` 로 복구), 묻지 않는다(§8(a))
- B.r2 하나라도 불충족 → 정리 생략 + 사유 한 줄("unmerged → kept"·"dirty → kept"·"plan inside the worktree → kept"), 6단계 worklog 실패도 같다("worklog failed → kept" + 다음 명령), 강행하지 않는다
- B.r3 원격 브랜치 삭제(`git push origin --delete`)는 자동 실행에 포함하지 않는다 — 필요하다고 판단되면 그때만 AskUserQuestion(§8(b)), `--force`(§C submodule 점검 통과는 제외)·`git branch -D`(미머지)도 동일
- B.r4 `wt rm <이름>` 직접 호출은 사용자가 대상을 지목한 경로라 조건과 무관하게 항상 확인(오타로 엉뚱한 worktree 를 지울 수 있다)

## C. 정리 실행
- C.0 §B 조건 전부 충족해 자동 정리(§8(a))하거나 확인 경로에서 사용자가 삭제를 택했을 때, cwd 가 삭제 대상 안일 수 있어 순서 중요(SKILL "6 pre" 절로 나왔으면 이미 밖)
- C.1 이동 전 값 캡처: `target_path`·`target_branch`·`main_path`(`git worktree list --porcelain` 첫 worktree)를 세션 옮기기 전에 고정, 이동 후 재계산하면 엉뚱한 대상(또는 main)
- C.2 worktree 밖으로: `ExitWorktree(action: keep)` 로 원래 디렉토리(보통 main) 복귀 — 대상 안에서는 자기 remove 불가
- C.2b `EnterWorktree(path: <main_path>)` 안 씀(메인 워킹트리는 linked 아니라 거부됨, 검증)
- C.3 `ExitWorktree` no-op(harness 가 worktree 에서 시작, `EnterWorktree` 미경유): 세션이 묶여 못 빠져나옴
- C.3b 폴백 (a) 다른 linked worktree 있으면 `EnterWorktree(path: <other>)` 후 remove, (b) 없으면 remove 생략+보고("세션 종료 시 harness 가 놓음" + 수동 `git worktree remove`/디렉토리 삭제 안내), 강제 금지
- C.4 이동 실패로 cwd 가 여전히 대상 안이면 중단+보고(remove 금지)
- C.5 비-메인 worktree 세션은 이 이동을 6단계 앞으로 당긴다(SKILL "6 pre" 절) — 격리된 세션에서는 worktree 안의 `bash "$HOME/..."` 헬퍼(worklog·collect-state) 호출이 네이티브 Bash 가드에 거부(2026-09-30 실측, 하네스 버전 의존)
- C.5b 복귀했으면 원래 디렉토리에서 worklog 는 미리보기·등록 모두 `<target_path>` 의 디렉터리 이름 인자로, 재수집은 `(cd "<target_path>" && bash "$HOME/.claude/skills/e/collect-state.sh")` 로
- C.5c 복귀했으면 `ExitWorktree` 를 다시 부르지 않는다(재호출 no-op 을 no-op 폴백으로 처리하지 않는다)
- C.5d 처음 시도가 no-op 이면 6·7단계는 worktree 안에서 계속하고 삭제할 때 위 폴백
- C.6 제거: cwd 가 대상 밖 확인 후, 대상이 `git worktree list --porcelain` 에 있으면 `git worktree remove <target_path>`, 실패 시 stderr 분기
- C.6a "modified or untracked files" 류: `--force` 는 별도 AskUserQuestion 후에만(§8 무확인 강제 금지)
- C.6b "working trees containing submodules cannot be moved or removed": submodule 이 있는 worktree(관리 디렉터리에 `modules/` 가 있거나 — deinit 해도 남는다 — 내용이 채워진 submodule)는 clean 이어도 `--force` 필요(git-worktree 문서)
- C.6b2 git 은 이 검사를 clean 검사보다 먼저 해 이 메시지만으로는 superproject clean 여부를 모른다 — 직전 재수집한 §B 조건(clean·미보존 ignored 없음)이 맡는다
- C.6b3 exit code(128)는 다른 거부와 같아 판별에 쓰지 않는다
- C.6b4 `--force` 가 더 지우는 것은 submodule 작업 트리(ignored 포함)와 module git dir(커밋·stash·reflog 포함)
- C.6b5 §B 조건을 모두 충족해 무확인 정리 중인 `/e` 7단계는 아래 두 점검을 모두 통과하면 묻지 않고 `--force` 로 지운다(§8(a))
- C.6b6 점검 명령(경로 확인·열거 포함)이 실패하거나, 하나라도 통과 못 하거나, 확인 경로(`wt rm` 등)이면 걸린 항목을 본문에 적고 AskUserQuestion 후에만
- C.6b7 `--force` remove 자체가 실패하면 아래 분기
- C.6b8 Windows 면 long-path 때문에 `git -c core.longpaths=true worktree remove --force` 로(공용 wiki `git-worktree-remove-submodule-longpaths`)
- C.6c 점검 1 모양: 모든 module git dir 이 작업 트리가 있는 submodule 의 것 — foreach `rev-parse --absolute-git-dir` 의 모든 줄이 `--git-path modules` 출력으로 시작하고 줄 수가 module git dir 수와 같다
- C.6c2 module git dir 은 깊이 제한 없이 `HEAD` 파일과 `objects` 디렉터리를 함께 가진 디렉터리(`find <modules> -type f -name HEAD` 중 같은 디렉터리에 `objects` 가 있는 것 — 이름에 `/` 가 있으면 여러 단계 아래)
- C.6c3 작업 트리 안에 `.git` 디렉터리를 둔 submodule, deinit 했거나 `.gitmodules` 에서 빠진 submodule 의 git dir 이 있으면 어긋난다
- C.6d 점검 2 내용: foreach `git status --porcelain --ignored && git log --oneline --all --reflog --not --remotes` 의 출력이 비고 exit 0(변경·untracked·ignored, 원격 추적 ref 에 없는 커밋 — 로컬 브랜치·stash·떠난 detached 커밋 포함)
- C.6e 한계: 원격 추적 ref 는 마지막 fetch 기준이라 그 뒤 원격에서 지워진 커밋은 못 잡는다
- C.6e2 원격 태그에만 있는 커밋도 2 에 출력돼 질문으로 간다(안전 쪽 오탐)
- C.6e3 초기화하지 않은 submodule 디렉터리에 둔 파일은 어느 점검도 안 본다 — plain remove 도 경고 없이 지운다
- C.7 파일 점유 류("Access is denied"·"being used"·"Directory not empty"·Windows "Invalid argument"·git `failed to delete` 의 "Permission denied"·남은 디렉토리 `rmdir` 의 "Device or resource busy"): 살아있는 프로세스가 `.venv` 등을 잡고 있다
- C.7b 단 "Permission denied" 는 Linux·macOS 에서 실제 권한 문제(docker·sudo 의 root 소유 파일)일 수도 — 잡은 프로세스가 없으면 파일 소유자 확인
- C.7c 먼저 내가 띄운 것부터 회수(`/e` 7단계 한정 — `wt rm` 은 자동 종료하지 않고 안내만, `skills/wt/SKILL.md` rm §6)
- C.7d 검증용 백그라운드 서버·데몬은 셸 `kill` 로 자식까지 안 죽는 경우가 많다(실측: `uv run` 서버가 `.venv` 를 잡아 remove 실패)
- C.7e 경로로 대상을 특정해 종료하고(예: `Get-Process … | Stop-Process -Force`) 재시도
- C.7f 사용자 서버·다른 worktree 프로세스는 건드리지 않는다 — 경로 필터 없이 이름만으로 일괄 종료 금지
- C.7g 내 것이 아닌 점유(사용자 서버·다른 세션 프로세스)는 자동 종료 안 함 — 점유 프로세스를 알려 소유자 종료 뒤 재시도 안내(`--force` 는 OS 점유엔 무효)
- C.8 현재 디렉토리만 worktree 인 점유자는 경로 필터(와 명령줄 검색)에 안 잡힌다 — 실행 파일은 밖이고 명령줄에도 경로가 없다
- C.8b 예: 하네스가 세션을 위해 worktree 안에서 띄운 언어 서버(Windows pyright — `claude.exe` → `pyright-langserver.exe` → `python.exe`, cwd = worktree)
- C.8c 2026-10-01 실측(Claude Code 2.1.286, 하네스 버전 의존)에서 등록만 해제되고 빈 디렉토리가 `Permission denied`·`Device or resource busy` 로 남았다
- C.8d 찾을 때는 프로세스마다 PEB 의 현재 디렉토리를 읽는다(공용 wiki `windows-bash-tool-orphan-processes`)
- C.8e 부모 체인이 이 세션의 `claude.exe`(내 셸 프로세스의 조상 — PID 대조)일 때만 내 것, 그 하네스의 직계 자식(`pyright-langserver.exe`)과 자손만 종료 — `claude.exe` 는 종료 안 함, 생성 시각은 보조 확인
- C.8f 언어 서버의 작업 디렉토리는 곧 지울 worktree 라 남길 이유가 없다
- C.8g 종료는 `/e` 7단계에서만(`wt rm` 은 같은 방법으로 찾은 점유자를 안내만), 이 세션 것으로 특정 못 하면 SKILL 조건6 대로 정리 생략·사유 보고
- C.8h Claude 밖에서 연 터미널·편집기나 다른 Claude 세션 프로세스는 건드리지 않는다
- C.9 부분 성공(등록 해제됐는데 디렉토리 잔존; Windows long-path·점유): remove 실패해도 등록이 빠졌을 수 있어 `git worktree list` 로 결과 확인
- C.9b 잔존 시 `git worktree prune` + 대상 디렉토리 수동 삭제(점유 회수 후)
- C.9c 이 상태에서 `git worktree remove` 재실행은 "is not a working tree" 로 실패
- C.10 long-path 원인(`error: failed to delete '<dir>': Filename too long`, exit 255 — 깊은 `node_modules` 등)은 remove 에 `-c core.longpaths=true` 를 붙이면 생기지 않는다(2026-10-13 재현)
- C.10b 이미 멈췄으면 남은 디렉토리는 PowerShell 7 의 `Remove-Item -LiteralPath <dir> -Recurse -Force` 로
- C.10c 전역·repo 설정으로는 켜지 않는다 — checkout 이 260자 넘는 파일을 경고 없이 만들 수 있다(공용 wiki `git-worktree-remove-submodule-longpaths`)
- C.11 로컬 브랜치: worktree 제거 성공 후 `git branch -d <target_branch>`(자동 정리에 포함)
- C.11b 미머지로 `-d` 거부면 `-D` 는 별도 AskUserQuestion 후에만(§8) — `-d` 거부 자체가 merged 판정이 틀렸다는 신호
- C.12 원격 브랜치: 자동 정리에 포함하지 않는다, 필요 시 worktree·로컬 삭제 성공 후 `git push origin --delete <target_branch>` 를 AskUserQuestion 으로 확인받고만(원격 ref 부재면 no-op·경고만)
- C.12b 묻기 전에 `git ls-remote --exit-code origin refs/heads/<target_branch>` 가 exit 2(원격에 없음)면 묻지 않고 남은 추적 ref 만 지운다(`/e` 7단계)
- C.12c merged 판정은 확정이 아니고(4a(b) 진행중 child·squash 미감지) 원격 삭제는 다른 머신의 유일본을 지울 수 있다

## D. 복귀 pull
- D.1 세션이 실제로 main 에 복귀했을 때만 `git pull --ff-only origin "$(git rev-parse --abbrev-ref HEAD)"` 1회 — 세션 중 머지·원격 진행분 반영(post-checkout hook 은 `git checkout` 에만 뜨고 ExitWorktree 복귀엔 안 뜬다)
- D.2 원격은 반드시 현재 브랜치(하드코딩 `main` 금지 — master repo 오대응 방지)
- D.3 선행 가드 전부 충족 시에만: main worktree, `git rev-parse --abbrev-ref HEAD` ∈ {main,master}, working tree clean
- D.4 no-op(feature 브랜치 잔류)·dirty·ff 실패·origin 부재면 skip(feature 브랜치에 origin/main merge 하는 파괴 방지)
- D.5 자동 rebase·stash·force 없음(§8)

## E. 머지 모드 gh
- E.0 SKILL 의 게이트·순서·닫힌 목록이 단일 소스, 여기는 명령·필드·템플릿·시나리오 표
- E.0b JSON 필드는 gh 2.89 `--help` 로 실존 확인(2026-09-02)
- E.1 M1 조회: 브랜치 `git rev-parse --abbrev-ref HEAD`(`HEAD` 면 detached)
- E.1b `gh repo view --json defaultBranchRef,mergeCommitAllowed,squashMergeAllowed` 한 번으로 인증·GitHub 여부·`<default>` 폴백·머지 방식(실패 = M1 거부)
- E.1c `<default>` 는 `git symbolic-ref --short refs/remotes/origin/HEAD` 에서 `origin/` 을 뗀 이름 → 실패 시 `defaultBranchRef.name`
- E.2 M2 PR 조회: `git fetch origin <default>` → `gh pr list … --json number,state,isDraft,url`, `state` ∈ {OPEN, MERGED, CLOSED}
- E.2b 후보 2개+ → 중단
- E.2c 지름길 판정은 `git rev-list --count origin/<default>..HEAD` = 0 + plan `status: done`, 진입 시 `git restore plans/<dir>/<slug>-plan.md`
- E.2d OPEN 이면 `gh pr view <N> --json mergeable,mergeStateStatus,headRefOid` 로 사전 점검
- E.3 M3 선행 검사: 명시 refspec fetch(원격에 브랜치 없으면 `couldn't find remote ref` — 그 경우만 `git update-ref -d …` 후 건너뜀) → `git merge-base --is-ancestor origin/<branch> HEAD`(0 조상 / 1 갈라짐 / 그 밖 오류)
- E.3b 분류는 `commit_units.py pending origin/<default>` JSON — `unfolded[]` 의 `sha`(전체)·`subject`·`flags`(`wip`·`fixup` 만)·`status`(rewritable/published/held/blocked)·`refs`(published 는 원격 추적 ref, held 는 로컬 브랜치·태그)
- E.3c 최상위 `range_error`(merge 커밋이 있는 범위·서명 커밋·기본 브랜치·git 2.40 미만 — 있으면 원격에 없는 것은 모두 `blocked`, 붙잡은 로컬 ref 는 `refs` 에 남는다)
- E.4 PR 생성(M3): `gh pr create --base <default> --head <branch> --title "<title>" --body-file <scratchpad>/pr-body.md`
- E.4b body 는 `## Summary`(plan `# Goal`·주요 변경 bullet) · `## Review`(리뷰어·처분 요약) · `## Verification`(실행한 검증 명령·결과) · 트레일러(`🤖 Generated with …` + 세션 URL, 하네스 지시 그대로)
- E.4c 파일로 쓰는 이유는 CLAUDE.md §2(긴 payload 를 tool 파라미터에 넣지 않는다)
- E.5 사전 점검 값: `mergeable` ∈ {MERGEABLE, CONFLICTING, UNKNOWN}, `mergeStateStatus` ∈ {CLEAN, UNSTABLE, HAS_HOOKS, UNKNOWN, DIRTY, BEHIND, BLOCKED, DRAFT}
- E.5b CONFLICTING/DIRTY/DRAFT → 중단·사유 보고(plan 무변경)
- E.5c UNKNOWN 은 10초 후 최대 3회 재조회
- E.5d BEHIND/BLOCKED 는 required check 전엔 정상이라 M3 에선 통과, M6 직전 재평가에서 남아 있으면 REJECTED
- E.6 M5 checks: `gh pr view <N> --json headRefOid` = `git rev-parse HEAD` 대조 → `gh pr checks <N> --watch`(Bash timeout 600000)
- E.6b exit 0 → `gh pr checks <N> --json name,bucket`(`--watch` 와 `--json` 병용 불가라 별도 호출)로 bucket ∈ {pass, fail, pending, skipping, cancel} 확인
- E.6c fail·cancel 이 먼저 REJECTED, 그다음 `pending`(`--watch` 가 돌아온 뒤 등록된 check)이 있으면 `--watch`·재조회를 한 번 더 돌리고 그래도 남을 때만 REJECTED(timeout)
- E.6d 그 호출이 `unknown flag: --json` 이면(gh 2.50 미만 — `pr checks --json` 은 v2.50.0, cli/cli#9079) statusCheckRollup `--jq` 식으로 대신 판정
- E.6e `PASS` 만 M6, `PENDING` 은 `--watch`·이 조회를 한 번 더 돌려 다시 판정하고 그래도 `PENDING` 이면 REJECTED(timeout), `NOTPASS`·`NONE`·호출 실패는 REJECTED
- E.6f `STALE`·`STARTUP_FAILURE` 결론은 gh 가 `pending` bucket 으로 넣지만 기다려도 풀리지 않아 여기서는 일부러 `NOTPASS`
- E.6g 식은 `gh pr checks` 처럼 check 별 최신 하나만 남긴다(check run 은 이름+workflow, status 는 context, 따로)
- E.6h `gh pr view` 는 status 생성 시각도 `startedAt` 키로 내보내고 event 는 내보내지 않아, 한 workflow 의 push·pull_request run 은 하나로 묶인다
- E.6i 원문 표(`gh pr checks <N>`)는 rtk 훅이 요약으로 바꾸므로 읽지 않는다
- E.6j exit 8 = pending 잔존
- E.6k exit 1 + stderr `no checks reported on the '<branch>' branch`(소문자 부분일치 `no checks reported`) = checks 없음 → `sleep 15` 후 `gh pr view <N> --json statusCheckRollup` 3회, 배열이 계속 비어 있을 때만 required 없음
- E.7 M6 머지·분류: `gh pr merge <N> --merge --match-head-commit <headRefOid>`(`mergeCommitAllowed: false` 면 `--squash`)
- E.7b 성공 exit 후 `gh pr view <N> --json state,mergedAt,mergeCommit` — `mergedAt` non-null = MERGED, null = QUEUED(merge queue)
- E.7c 명령 실패 = REJECTED, 확인 명령 실패 = UNKNOWN
- E.7d MERGED 면 `git fetch origin <default>`
- E.7e 7단계 재수집(`collect-state.sh`)에서 조건4 는 이 `mergedAt` 로 충족(squash 는 `inBase`·`patchInBase` 가 false 일 수 있다 — §B squash 미감지 한계)
- E.8 커밋 메시지: done `docs(plan): close <slug> (PR #N)`, 복구 `docs(plan): reopen <slug> (PR #N <사유>)`

## E 시나리오 표 (한 행 = 한 조항: 시나리오 / 외부 쓰기 / plan status / 다음 Task / 재실행 결과)
- T.0 열 머리: 시나리오 · 외부 쓰기 · plan status · 다음 Task(첫 미완료 `# Tasks`, 옛 형식 `# Next`) · 재실행(`/e merge`) 결과
- T.1 새 PR, checks pass, MERGED / push·PR·merge / done / 없음(`[post-merge]` 만) / M2: base 에 없는 커밋 0·done → M6 확인·fetch → 5~8
- T.2 기존 open PR / push(변경 있을 때) / done / 없음(`[post-merge]` 만) / 동일 PR 재사용
- T.3 기존 merged/closed PR + 새 커밋(plan done 등) / push·새 PR·merge / done / 없음(`[post-merge]` 만) / 새 PR 재사용
- T.4 미게시 정리 안 된 커밋(`rewritable`) — commit-check 적용 / 로컬 재구성 → push·PR·merge / done / 없음(`[post-merge]` 만) / 정리된 커밋은 이미 게시돼 다시 걸리지 않는다
- T.5 미게시 정리 안 된 커밋 — 보류·적용 실패·잔존·무인 / 없음(M3 전 중단) / 불변(done 전, 3단계 편집은 미커밋 보존) / 사유 + "clean up the commits, then rerun `/e merge`" / M3 선행 검사부터
- T.6 정리 안 된 커밋이 `published`·`held`·`blocked` / 진행 선택 시 push·PR·merge / done(진행) / 불변(중단·무인) / 중단이면 사유 + "clean up the commits, then rerun `/e merge`" / `held` 는 그 ref 를 치운 뒤 재실행하면 다시 분류(대개 `rewritable`), 같은 게시분은 재실행마다 다시 묻는다
- T.7 위와 같은데 repo 가 merge 커밋 불허(M6 squash) / push·PR·merge(squash) / done / 없음(`[post-merge]` 만) / 묻지 않고 보고만
- T.8 원격 작업 브랜치가 HEAD 의 조상 아님 / 없음(M3 전 중단) / 불변 / "원격 브랜치 반영 후 재실행" / M3 선행 검사부터
- T.9 draft PR / 없음(M2 에서 중단) / 불변 / 불변 / draft 해제 후 재실행
- T.10 사전 점검 CONFLICTING/DIRTY / push·PR(생성된 경우) / 불변(done 전 중단) / 불변 / 해소 후 재실행 → M2 재사용
- T.11 M6 직전 BEHIND/BLOCKED 잔존 (REJECTED) / push·PR / in_progress(복구) / protection 충족 후 재실행 / M2 재사용 → M5
- T.12 MERGED/CLOSED PR + plan 미done 재실행 / push·새 PR·merge / done(M4 선행) / 없음 / 새 PR 재사용
- T.13 checks none(3회 재조회 후에도) / push·PR·merge / done / 없음(`[post-merge]` 만) / required 없음으로 진행
- T.14 checks pending→pass / 위와 동일 / done / 없음(`[post-merge]` 만) / —
- T.15 checks fail·cancel (REJECTED) / push·PR / in_progress(복구) / 수정 후 재실행 / 수정·push 후 M2 재사용 → M5
- T.16 checks timeout / exit 8 / 한 번 더 기다려도 pending (REJECTED) / push·PR / in_progress(복구) / "PR #N waiting for checks, rerun `/e merge`" / M2 재사용 → M5
- T.17 머지 직전 CONFLICTING (REJECTED) / push·PR / in_progress(복구) / 충돌 해소 후 재실행 / rebase/merge 후 push → M5
- T.18 `--match-head-commit` 불일치 / push·PR / done 유지(중단·보고) / 불변 / head 확인 후 재실행
- T.19 merge 커밋 불허 → squash MERGED / push·PR·merge(squash) / done / 없음(`[post-merge]` 만) / mergedAt 로 조건4 충족
- T.20 권한 프롬프트 거절·branch protection (REJECTED) / push·PR / in_progress(복구) / 사유 해소 후 재실행 / M2 재사용
- T.21 QUEUED(merge queue) / push·PR·merge(큐) / done 유지 / 불변(보고: 큐 완료 후 `/e merge` 재실행) / M2: MERGED 재사용 안 함·커밋 0 → M6 확인·fetch
- T.22 UNKNOWN(확인·fetch 실패) / push·PR·merge(?) / done 유지 / 불변(보고: `gh pr view` 재조회 후 재실행) / M2 분기
- T.23 `gh repo view` 실패(미인증·GitHub 아님) / 없음 / 불변 / 불변 / M1 거부
- T.24 push 거부(`permissions.ask` 거절) / 없음 / 불변(M4 선행 시 로컬 done → 복구) / 불변 / M3 중단
- T.25 plan 없음 / 브랜치 main·detached / Acceptance 미체크 / `/e merge`·`[post-merge]` 밖 미완료 Task / 없음 / — / — / M1 거부
- T.26 머지 후 5~8단계 실패 / 없음 추가 / done / 실패 단계 기록 / merge 재호출 없이 5~8 재시도
- T.27 복구 push 거부 / 없음 / in_progress(로컬만) / 로컬 커밋 push 필요 보고 / push 후 M2

## 핵심 문구
`/e` · `~/.claude/skills/e/SKILL.md` · M1~M6 · `--force` · `wt rm <name>` · `bash skills/e/collect-state.sh` · `key: value` · `root·branch·detached·mainWorktree·dirty·status·upstreamStatus·upstream·unpushedStatus·unpushed·base·baseValid·inBase·patchInBase·localDefault·mergedToLocalBase·remoteContainingHead·ignoredStatus·ignored` · `: ` · `C:/` · `:` · `status` · `unpushed` · `remoteContainingHead` · `ignored` · `git log --oneline` · `none` · `unknown` · `false` · `root` · `mainWorktree` · `git rev-parse --show-toplevel` · `git worktree list --porcelain` · `worktree <path>` · `dirty` · `git status --porcelain` · `unpushedStatus` · `baseValid` · `inBase` · `patchInBase` · `git cherry` · `BASE` · `git symbolic-ref --short refs/remotes/origin/HEAD` · `origin/main` · `git rev-parse --verify --quiet <BASE>` · `git log <BASE>..HEAD` · `git cherry <BASE> HEAD` · `+` · `mergedToLocalBase` · `git branch --merged <localDefault>` · `localDefault` · `origin/HEAD` · `main` · `master` · `git branch --merged <localDefault> --format='%(refname:short)' | grep -qx <branch>` · `origin/<current-branch>` · `origin/HEAD -> ...` · `<HEAD7>` · `<remote-branch>` · `git branch -r --contains HEAD` · `git worktree remove` · `.gitignore` · `.env` · `git status` · `ignoredStatus` · `git status --porcelain --ignored` · `git status --short` · `plans/` · `git branch -d` · `git branch <name> <sha>` · `git push origin --delete` · `git branch -D` · `target_path` · `target_branch` · `main_path` · `ExitWorktree(action: keep)` · `EnterWorktree(path: <main_path>)` · `ExitWorktree` · `EnterWorktree` · `EnterWorktree(path: <other>)` · `bash "$HOME/..."` · `<target_path>` · `(cd "<target_path>" && bash "$HOME/.claude/skills/e/collect-state.sh")` · `git worktree remove <target_path>` · `modules/` · `wt rm` · `git -c core.longpaths=true worktree remove --force` · `git-worktree-remove-submodule-longpaths` · `git -C <target_path> submodule foreach --recursive --quiet "git rev-parse --absolute-git-dir"` · `git -C <target_path> rev-parse --path-format=absolute --git-path modules` · `HEAD` · `objects` · `find <modules> -type f -name HEAD` · `/` · `.git` · `.gitmodules` · `git -C <target_path> submodule foreach --recursive --quiet "git status --porcelain --ignored && git log --oneline --all --reflog --not --remotes"` · `failed to delete` · `rmdir` · `.venv` · `skills/wt/SKILL.md` · `kill` · `uv run` · `Get-Process python,<app> | Where-Object { $_.Path -like "*worktrees\<name>\*" } | Stop-Process -Force` · `claude.exe` · `pyright-langserver.exe` · `python.exe` · `Permission denied` · `Device or resource busy` · `windows-bash-tool-orphan-processes` · `git worktree list` · `git worktree prune` · `error: failed to delete '<dir>': Filename too long` · `node_modules` · `-c core.longpaths=true` · `git -c core.longpaths=true worktree remove …` · `Remove-Item -LiteralPath <dir> -Recurse -Force` · `git branch -d <target_branch>` · `-d` · `-D` · `git push origin --delete <target_branch>` · `git ls-remote --exit-code origin refs/heads/<target_branch>` · `git pull --ff-only origin "$(git rev-parse --abbrev-ref HEAD)"` · `git checkout` · `git rev-parse --abbrev-ref HEAD` · `--help` · `gh repo view --json defaultBranchRef,mergeCommitAllowed,squashMergeAllowed` · `<default>` · `origin/` · `defaultBranchRef.name` · `git fetch origin <default>` · `gh pr list --head <branch> --base <default> --state all --json number,state,isDraft,url` · `state` · `git rev-list --count origin/<default>..HEAD` · `status: done` · `git restore plans/<dir>/<slug>-plan.md` · `gh pr view <N> --json mergeable,mergeStateStatus,headRefOid` · `git fetch origin "+refs/heads/<branch>:refs/remotes/origin/<branch>"` · `couldn't find remote ref` · `git update-ref -d refs/remotes/origin/<branch>` · `git merge-base --is-ancestor origin/<branch> HEAD` · `commit_units.py pending origin/<default>` · `unfolded[]` · `sha` · `subject` · `flags` · `wip` · `fixup` · `rewritable` · `published` · `held` · `blocked` · `refs` · `range_error` · `gh pr create --base <default> --head <branch> --title "<title>" --body-file <scratchpad>/pr-body.md` · `## Summary` · `# Goal` · `## Review` · `## Verification` · `🤖 Generated with [Claude Code](https://claude.com/claude-code)` · `mergeable` · `mergeStateStatus` · `gh pr view <N> --json headRefOid` · `git rev-parse HEAD` · `gh pr checks <N> --watch` · `gh pr checks <N> --json name,bucket` · `--watch` · `--json` · `pending` · `unknown flag: --json` · `pr checks --json` · `gh pr view <N> --json statusCheckRollup --jq 'def ok: .v == "SUCCESS" or .v == "SKIPPED" or .v == "NEUTRAL"; def wait: .v == "QUEUED" or .v == "IN_PROGRESS" or .v == "WAITING" or .v == "PENDING" or .v == "REQUESTED" or .v == "EXPECTED"; [.statusCheckRollup[] | {k: [.__typename, (.name // .context), (.workflowName // "")], t: .startedAt, v: (if .__typename == "CheckRun" then (if .status == "COMPLETED" then .conclusion else .status end) else .state end)}] | group_by(.k) | map(max_by(.t)) | if length == 0 then "NONE" elif all(ok) then "PASS" elif all(ok or wait) then "PENDING" else "NOTPASS" end'` · `PASS` · `PENDING` · `NOTPASS` · `NONE` · `STALE` · `STARTUP_FAILURE` · `gh pr checks` · `gh pr view` · `startedAt` · `gh pr checks <N>` · `no checks reported on the '<branch>' branch` · `no checks reported` · `sleep 15` · `gh pr view <N> --json statusCheckRollup` · `gh pr merge <N> --merge --match-head-commit <headRefOid>` · `mergeCommitAllowed: false` · `--squash` · `gh pr view <N> --json state,mergedAt,mergeCommit` · `mergedAt` · `collect-state.sh` · `docs(plan): close <slug> (PR #N)` · `docs(plan): reopen <slug> (PR #N <reason>)` · `# Tasks` · `# Next` · `/e merge` · `[post-merge]` · `--match-head-commit` · `gh repo view` · `permissions.ask` · "modified or untracked files" · "working trees containing submodules cannot be moved or removed" · "Access is denied" · "being used" · "Directory not empty" · "Invalid argument" · "is not a working tree" · "unmerged → kept" · "dirty → kept" · "plan inside the worktree → kept" · "worklog failed → kept" · "clean up the commits, then rerun `/e merge`" · "PR #N waiting for checks, rerun `/e merge`" · "6 pre" · Worktree cleanup rules · step 8 ⓑ · §8(a) · §8(b) · §C · §B · AskUserQuestion · 2026-09-30 · 2026-10-01 · 2026-10-13 · 2026-09-02 · 2.1.286 · gh 2.89 · gh 2.50 · v2.50.0 · cli/cli#9079 · git 2.40 · 600000 · exit 255 · exit 0 · exit 8 · exit 1 · exit 2 · (128) · 260 · PowerShell 7 · PEB · PID · {OPEN, MERGED, CLOSED} · {MERGEABLE, CONFLICTING, UNKNOWN} · {CLEAN, UNSTABLE, HAS_HOOKS, UNKNOWN, DIRTY, BEHIND, BLOCKED, DRAFT} · {pass, fail, pending, skipping, cancel} · ∈ {main,master} · 4a. · (a′) · CLAUDE.md §2 · rm §6

## 다른 파일이 가리키는 표지
- 절 표지 `§A`~`§E`(`## A.`~`## E.`) — `skills/e/SKILL.md`(§A·§B·§C·§D·§E), `skills/wt/SKILL.md`·`skills/wt/references/rm-recovery.md`(§C), README(§E) 가 가리킨다. 제목 낱말은 영어로, 글자 표지는 그대로.
- §C 안의 분기 이름 — e SKILL 이 "§C checks"(submodule 분기의 두 점검)·"file held"·"partial success prune" 으로, wt 가 "File held type"·"Partial success" 로 가리킨다. 영어 이름을 같은 낱말로 둔다(File held type·Partial success).
- 결과 처리 사유 문구("unmerged → kept" 등)·Task 문구 — e SKILL 7단계·M3·M4 와 글자로 같다(이미 영어).
- `main-autopull ⓑ`·`M1~M6` — e SKILL 이 같은 라벨을 쓴다.
