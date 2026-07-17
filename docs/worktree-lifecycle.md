# worktree-lifecycle — /e 상태 수집·worktree 정리 메커닉 (참조)

`/e` SKILL(`skills/e/SKILL.md`)의 상태 수집(2단계)·worktree 삭제 판정(5단계)·정리 실행(정리 규칙)·복귀 pull(6단계 ⓑ)의 **git 메커닉·폴백·엣지 처리**를 담는다. SKILL 본문엔 게이트·닫힌목록·안전 규칙만 남기고 세부는 여기로.

> 이 파일은 자동 로드되지 않는다 — `/e` 가 **상태 수집·worktree 삭제 판정/실행·복귀 pull 분기에 실제로 들어갔을 때** 이 파일을 Read 한다. 판정 골격(6조건 AND·자동삭제 금지·안전 게이트)은 SKILL 본문이 단일 소스이고, 여기는 "어떻게"만.

## A. collect-state 필드 카탈로그·파싱 (SKILL §2)
`bash skills/e/collect-state.sh` 가 개별 git 10+ 호출을 1회로 묶어 평문 `key: value` 로 반환하는 신호:
`root·branch·detached·mainWorktree·dirty·status·upstreamStatus·upstream·unpushedStatus·unpushed·base·baseValid·inBase·patchInBase·remoteContainingHead·ignoredStatus·ignored`.
- 각 라인은 **첫 `: ` 1회로만 split**(경로 `C:/`·커밋 subject 의 `:` 보존). list 필드(`status`·`unpushed`·`remoteContainingHead`·`ignored`)는 들여쓰기 라인.
- `git log --oneline`(plan 시작 이후 새 커밋)은 헬퍼 밖 별도.
- 점검 실패(origin 없음·status 오류)는 해당 필드 `none`/`unknown` — `false` 로 평탄화하지 않는다.
- 헬퍼 실패·필드 누락이면 보고에 명시하고 아래 조건별 폴백 git 명령으로.

## B. worktree 삭제 판정 6조건 메커닉 (SKILL §5)
SKILL 은 "6조건 AND + 하나라도 불충족/헬퍼불가면 제안 생략(보수)"만 명시. 각 조건 판정과 폴백:
1. **비-메인 worktree**: `root` ≠ `mainWorktree`. 폴백 `git rev-parse --show-toplevel` vs `git worktree list --porcelain` 첫 `worktree <path>`. 슬래시 방향·대소문자 normalize 후 비교(메인 책임 — 헬퍼는 raw path). 메인이면 제안 안 함.
2. **detached=false + plan status==done**: plan 의존이라 헬퍼 밖(4단계 확정값). detached 면 생략.
3. **working tree clean**(untracked 포함): `dirty`=false(`status` 빈). 폴백 `git status --porcelain`. `dirty`=unknown(status 실패)이면 점검 불가 → 생략(보수).
4. **unpushed 없음**: `unpushedStatus` ∈ {upstream, allRemotes} 이고 `unpushed`=(none). 폴백: upstream 있으면 `git log @{u}..HEAD`, 없으면 `git log <branch> --not --remotes`(`git log origin/<branch>..HEAD` 는 ref 부재 시 fatal 이라 안 씀). **`unpushedStatus`=unknown 이면 미보존으로 보고 제안 안 함**(false-positive 삭제 차단).
5. **base 또는 다른 원격 브랜치에 merged(둘 다 git-only 추정 — 확정 아님)**. pushed(조건4)는 원격 보존일 뿐, 리뷰 중·머지 전이면 지우면 안 됨. (a)·(b) 중 하나라도 신호면 제안하되 최종 삭제는 늘 AskUserQuestion:
   - **(a) 기본 base 포함**: `baseValid`=true 이고 (`inBase`=true **또는** `patchInBase`=true). `inBase`=커밋 SHA 포함(ff/no-ff 머지), `patchInBase`=patch-equivalent 포함(`git cherry` — **rebase merge 로 SHA 재작성돼도** 브랜치 전 커밋이 base 에 patch 로 있으면 감지). `baseValid`=false 면 skip. 폴백: `BASE`=`git symbolic-ref --short refs/remotes/origin/HEAD`||`origin/main`, `git rev-parse --verify --quiet <BASE>` 후 `git log <BASE>..HEAD` 빈지[inBase]; 비어있지 않으면 `git cherry <BASE> HEAD` 의 `+`(미머지 patch)가 0개인지[patchInBase].
   - **(b) 다른 원격 브랜치 포함(ticket-to-ticket 머지)**: `remoteContainingHead` 에서 self(`origin/<현재브랜치>`)·`origin/HEAD -> ...` 제외하고 남는 원격 브랜치가 있으면 거기 머지됐을 가능성. ⚠️ **진행 중인 다른 브랜치가 내 커밋을 조상으로 쌓은 경우도 포함**되니 확정 아님 → 그 브랜치명 근거로 AskUserQuestion 본문에 "`<HEAD7>` 가 `<remote-branch>` 에 포함 — 머지됐을 수 있으나 진행 중일 수도(확정 아님)" 명시. 폴백 `git branch -r --contains HEAD`.
   - (a)·(b) 모두 신호 없으면(self 만·BASE 미포함) → 미머지로 보고 생략·유지.
   - ⚠️ 한계: **squash merge**(N커밋→1)는 patch-id 합쳐져 cherry 도 못 잡아 미머지로 보임(stale 원격 ref·rebase 충돌해소도). 전부 유지 방향이라 안전. PR 상태 직접 조회는 인증·headless 때문에 안 씀 — git-only 추정 + 사용자 확인. 1순위 = false-positive(미머지 삭제) 차단이라 (b)·`patchInBase` 는 "근거 제시"로만.
6. **미보존 산출물 점검**: `git worktree remove`(--force 없이)는 gitignored 파일 무경고 동반 삭제, `--force` 는 미커밋 산출물도 삭제. whitelist `.gitignore` 라 `.env` 등 gitignored 는 `git status` 안 보임(plans/ 는 tracked §10 라 미커밋 plan 은 보이고 remove 거부되나 `--force` 로는 유실). **`ignoredStatus`=unknown 이면 생략(보수)**. `ignored` 목록(폴백 `git status --porcelain --ignored`) + `git status --short` 점검:
   - 이 worktree `plans/` 에 **이번에 갱신한 미커밋 plan 이 있으면 → 제안 생략**(방금 done 기록한 plan 이 worktree 와 함께 소실 방지; 브랜치 commit·push 또는 main worktree `plans/` 이동 뒤에야 안전).
   - `.env`·secret 후보·기타 산출물 있으면 삭제될 목록을 AskUserQuestion 본문에 **명시**(기본 유지).

**제안 옵션**(AskUserQuestion; wt rm 계열): ① worktree 만 삭제(브랜치 유지) / ② worktree+로컬 브랜치(원격 유지) / ③ worktree+로컬·원격(조건4 pushed·조건5 merged 신호 충족분만 — 조건5 불확실성 경고 본문 노출) / ④ 유지(기본).

## C. worktree 정리 실행 메커닉 (SKILL 정리 규칙)
사용자가 삭제를 택했을 때만. **cwd 가 삭제 대상 안이라 순서 중요.**
- **이동 전 값 캡처**: `target_path`·`target_branch`·`main_path`(`git worktree list --porcelain` 첫 worktree)를 **세션 옮기기 전에** 고정. 이동 후 재계산하면 엉뚱한 대상(또는 main) 가리킴.
- **worktree 밖으로**: `ExitWorktree(action: keep)` 로 원래 디렉토리(보통 main) 복귀 — 대상 안에서는 자기 remove 불가. ⚠️ `EnterWorktree(path: <main_path>)` 안 씀(메인 워킹트리는 linked 아니라 거부됨, 검증).
  - **`ExitWorktree` no-op**(harness 가 worktree 에서 시작, `EnterWorktree` 미경유): 세션이 묶여 못 빠져나옴. 폴백 — (a) 다른 **linked** worktree 있으면 `EnterWorktree(path: <other>)` 후 remove, (b) 없으면 remove **생략+보고**("세션 종료 시 harness 가 놓음" + 수동 `git worktree remove`/디렉토리 삭제 안내). 강제 금지.
  - 이동 실패로 cwd 가 여전히 대상 안이면 **중단+보고**(remove 금지).
- **제거**: cwd 가 대상 밖 확인 후, 대상이 `git worktree list --porcelain` 에 있으면 `git worktree remove <target_path>`. 실패 시 stderr 분기:
  - **"modified or untracked files" 류**: `--force` 는 **별도 AskUserQuestion 후에만**(§8 무확인 강제 금지).
  - **파일 점유 류**("Access is denied"·"being used"·"Directory not empty"): 그 worktree `.codegraph/` 를 codegraph daemon 이 잡을 수 있음(그 worktree 서 codegraph MCP 세션 띄운 경우만 — `init`/`status` 로는 안 뜸). **자동 종료 안 함** — 세션 닫기/daemon idle 자동종료(~5분) 후 재시도/수동 node 종료 안내(`--force` 는 OS 점유엔 무효).
  - **부분 성공**(git 등록 빠졌으나 디렉토리 잔존; Windows long-path): `git worktree prune` + 대상 디렉토리 수동 삭제.
- **로컬 브랜치(옵션 ②·③)**: `git branch -d <target_branch>`. 미머지로 `-d` 거부면 `-D` 는 **별도 AskUserQuestion 후에만**(§8).
- **원격 브랜치(옵션 ③만)**: worktree·로컬 삭제 성공 후 `git push origin --delete <target_branch>`. 원격 ref 부재면 no-op(경고만). 조건5 는 확정 아님(특히 5(b) 진행중 child 가능) → 사용자가 AskUserQuestion 경고 보고 택한 경우만(미머지 orphan 방지).

## D. 복귀 후 main-autopull pull (SKILL §6 ⓑ)
세션이 **실제로 main 에 복귀했을 때만** `git pull --ff-only origin "$(git rev-parse --abbrev-ref HEAD)"` 1회 — 세션 중 머지·원격 진행분 반영(post-checkout hook 은 `git checkout` 에만 뜨고 ExitWorktree 복귀엔 안 뜨므로 이 구간 커버). **원격은 반드시 현재 브랜치**(하드코딩 `main` 금지 — master repo 오대응 방지). 선행 가드 전부 충족 시에만: ① main worktree ② `git rev-parse --abbrev-ref HEAD` ∈ {main,master} ③ working tree clean. **no-op(feature 브랜치 잔류)·dirty·ff 실패·origin 부재면 skip**(feature 브랜치에 origin/main merge 하는 파괴 방지). 자동 rebase·stash·force 없음(§8).
