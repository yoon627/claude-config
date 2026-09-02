# worktree-lifecycle — /e 상태 수집·worktree 정리 메커닉 (참조)

`/e` SKILL(`skills/e/SKILL.md`)의 상태 수집(2단계)·머지 모드(M1~M6)·worktree 삭제 판정(7단계)·정리 실행(정리 규칙)·복귀 pull(8단계 ⓑ)의 **git/gh 메커닉·폴백·엣지 처리**를 담는다. SKILL 본문엔 게이트·닫힌목록·안전 규칙만 남기고 세부는 여기로.

> 이 파일은 자동 로드되지 않는다 — `/e` 가 **상태 수집·머지 모드(M1 진입)·worktree 삭제 판정/실행·복귀 pull 분기에 실제로 들어갔을 때** 이 파일을 Read 한다. 판정 골격(6조건 AND·자동삭제 금지·안전 게이트)은 SKILL 본문이 단일 소스이고, 여기는 "어떻게"만.

> **범위**: 이 파일은 **CLAUDE.md §8(a) 자동 정리**(조건 충족 시 worktree + 로컬 브랜치를 **묻지 않고** 정리)와 **§8(b) 확인 경로**(원격 브랜치 삭제·안전조건 미충족·`wt rm <이름>` 직접 호출)의 판정 메커닉을 함께 다룬다. 조건 판정은 같고 **결과 처리만 갈린다** — 전부 충족이면 무확인 실행, 하나라도 불충족이면 정리 생략(강행 금지), 원격 삭제는 언제나 AskUserQuestion.

## A. collect-state 필드 카탈로그·파싱 (SKILL §2)
`bash skills/e/collect-state.sh` 가 개별 git 10+ 호출을 1회로 묶어 평문 `key: value` 로 반환하는 신호:
`root·branch·detached·mainWorktree·dirty·status·upstreamStatus·upstream·unpushedStatus·unpushed·base·baseValid·inBase·patchInBase·localDefault·mergedToLocalBase·remoteContainingHead·ignoredStatus·ignored`.
- 각 라인은 **첫 `: ` 1회로만 split**(경로 `C:/`·커밋 subject 의 `:` 보존). list 필드(`status`·`unpushed`·`remoteContainingHead`·`ignored`)는 들여쓰기 라인.
- `git log --oneline`(plan 시작 이후 새 커밋)은 헬퍼 밖 별도.
- 점검 실패(origin 없음·status 오류)는 해당 필드 `none`/`unknown` — `false` 로 평탄화하지 않는다.
- 헬퍼 실패·필드 누락이면 보고에 명시하고 아래 조건별 폴백 git 명령으로.

## B. worktree 삭제 판정 6조건 메커닉 (SKILL §7)
SKILL 은 "6조건 AND + 하나라도 불충족/헬퍼불가면 제안 생략(보수)"만 명시. 각 조건 판정과 폴백:
1. **비-메인 worktree**: `root` ≠ `mainWorktree`. 폴백 `git rev-parse --show-toplevel` vs `git worktree list --porcelain` 첫 `worktree <path>`. 슬래시 방향·대소문자 normalize 후 비교(메인 책임 — 헬퍼는 raw path). 메인이면 제안 안 함.
2. **detached=false + plan status==done**: plan 의존이라 헬퍼 밖(4단계 확정값). detached 면 생략.
3. **working tree clean**(untracked 포함): `dirty`=false(`status` 빈). 폴백 `git status --porcelain`. `dirty`=unknown(status 실패)이면 점검 불가 → 생략(보수).
4. **merged 판정**(아래 5와 통합 — 이 항목이 자동 정리의 핵심 게이트). ⚠️ **unpushed 는 로컬 정리의 조건이 아니다**: merged 면 커밋이 default 브랜치에 있어 로컬 브랜치를 지워도 잃을 게 없고, 이 사용자는 **push 하지 않는 워크플로우**라 unpushed 를 게이트로 두면 자동 정리가 영영 안 돈다. `unpushedStatus`·`unpushed` 는 **원격 브랜치 삭제(§8(b), 항상 확인)** 를 판단할 때만 본다.
5. **base 또는 다른 원격 브랜치에 merged(git-only 추정)**. (a)·(a′) 중 하나면 자동 정리 가능, (b) 만 있으면 확정이 아니라 확인 경로:
   - **(a) 기본 base 포함**: `baseValid`=true 이고 (`inBase`=true **또는** `patchInBase`=true). `inBase`=커밋 SHA 포함(ff/no-ff 머지), `patchInBase`=patch-equivalent 포함(`git cherry` — **rebase merge 로 SHA 재작성돼도** 브랜치 전 커밋이 base 에 patch 로 있으면 감지). `baseValid`=false 면 skip. 폴백: `BASE`=`git symbolic-ref --short refs/remotes/origin/HEAD`||`origin/main`, `git rev-parse --verify --quiet <BASE>` 후 `git log <BASE>..HEAD` 빈지[inBase]; 비어있지 않으면 `git cherry <BASE> HEAD` 의 `+`(미머지 patch)가 0개인지[patchInBase].
   - **(a′) 로컬 default 포함**: `mergedToLocalBase`=true. 헬퍼가 `git branch --merged <localDefault>` 로 판정하며 `localDefault` 는 `origin/HEAD` 의 뒷부분 → 없으면 실재하는 `main`/`master`. **origin 이 없거나 push 를 안 하는 repo 에서는 (a) 가 unknown 이라 이 신호만 남는다** — 로컬 main 머지도 정식 merged 로 인정한다. 폴백 `git branch --merged <localDefault> --format='%(refname:short)' | grep -qx <branch>`.
   - **(b) 다른 원격 브랜치 포함(ticket-to-ticket 머지)**: `remoteContainingHead` 에서 self(`origin/<현재브랜치>`)·`origin/HEAD -> ...` 제외하고 남는 원격 브랜치가 있으면 거기 머지됐을 가능성. ⚠️ **진행 중인 다른 브랜치가 내 커밋을 조상으로 쌓은 경우도 포함**되니 확정 아님 → 그 브랜치명 근거로 AskUserQuestion 본문에 "`<HEAD7>` 가 `<remote-branch>` 에 포함 — 머지됐을 수 있으나 진행 중일 수도(확정 아님)" 명시. 폴백 `git branch -r --contains HEAD`.
   - (a)·(a′)·(b) 모두 신호 없으면(self 만·BASE 미포함) → 미머지로 보고 생략·유지.
   - ⚠️ 한계: **squash merge**(N커밋→1)는 patch-id 합쳐져 cherry 도 못 잡아 미머지로 보임(stale 원격 ref·rebase 충돌해소도). 전부 유지 방향이라 안전. PR 상태 직접 조회는 인증·headless 때문에 안 씀 — git-only 추정 + 사용자 확인. 1순위 = false-positive(미머지 삭제) 차단이라 (b)·`patchInBase` 는 "근거 제시"로만.
6. **미보존 산출물 점검**: `git worktree remove`(--force 없이)는 gitignored 파일 무경고 동반 삭제, `--force` 는 미커밋 산출물도 삭제. whitelist `.gitignore` 라 `.env` 등 gitignored 는 `git status` 안 보임(plans/ 는 tracked §10 라 미커밋 plan 은 보이고 remove 거부되나 `--force` 로는 유실). **`ignoredStatus`=unknown 이면 생략(보수)**. `ignored` 목록(폴백 `git status --porcelain --ignored`) + `git status --short` 점검:
   - 이 worktree `plans/` 에 **이번에 갱신한 미커밋 plan 이 있으면 → 제안 생략**(방금 done 기록한 plan 이 worktree 와 함께 소실 방지; 브랜치 commit·push 또는 main worktree `plans/` 이동 뒤에야 안전).
   - `.env`·secret 후보·기타 산출물 있으면 **정리 생략**하고 그 목록을 보고에 명시(유실 방지). 지워도 되는지는 사용자 판단.

**결과 처리**:
- **조건 전부 충족 → 무확인 실행**: worktree → 로컬 `git branch -d`. 삭제한 브랜치 tip sha 를 한 줄 보고(`git branch <name> <sha>` 로 복구 가능). 묻지 않는다(§8(a)).
- **하나라도 불충족 → 정리 생략** + 사유 한 줄("미머지 → 유지"·"dirty → 유지"·"plan 이 worktree 내부 → 유지"). 강행하지 않는다.
- **원격 브랜치 삭제**(`git push origin --delete`)는 위 자동 실행에 **포함하지 않는다** — 필요하다고 판단되면 그때만 AskUserQuestion(§8(b)). `--force`·`git branch -D`(미머지)도 동일.
- **`wt rm <이름>` 직접 호출**은 사용자가 대상을 지목한 경로라 조건 충족 여부와 무관하게 **항상 확인**(오타로 엉뚱한 worktree 를 지울 수 있다).

## C. worktree 정리 실행 메커닉 (SKILL 정리 규칙)
§B 조건이 전부 충족돼 자동 정리하거나(§8(a)), 확인 경로에서 사용자가 삭제를 택했을 때. **cwd 가 삭제 대상 안이라 순서 중요.**
- **이동 전 값 캡처**: `target_path`·`target_branch`·`main_path`(`git worktree list --porcelain` 첫 worktree)를 **세션 옮기기 전에** 고정. 이동 후 재계산하면 엉뚱한 대상(또는 main) 가리킴.
- **worktree 밖으로**: `ExitWorktree(action: keep)` 로 원래 디렉토리(보통 main) 복귀 — 대상 안에서는 자기 remove 불가. ⚠️ `EnterWorktree(path: <main_path>)` 안 씀(메인 워킹트리는 linked 아니라 거부됨, 검증).
  - **`ExitWorktree` no-op**(harness 가 worktree 에서 시작, `EnterWorktree` 미경유): 세션이 묶여 못 빠져나옴. 폴백 — (a) 다른 **linked** worktree 있으면 `EnterWorktree(path: <other>)` 후 remove, (b) 없으면 remove **생략+보고**("세션 종료 시 harness 가 놓음" + 수동 `git worktree remove`/디렉토리 삭제 안내). 강제 금지.
  - 이동 실패로 cwd 가 여전히 대상 안이면 **중단+보고**(remove 금지).
- **제거**: cwd 가 대상 밖 확인 후, 대상이 `git worktree list --porcelain` 에 있으면 `git worktree remove <target_path>`. 실패 시 stderr 분기:
  - **"modified or untracked files" 류**: `--force` 는 **별도 AskUserQuestion 후에만**(§8 무확인 강제 금지).
  - **파일 점유 류**("Access is denied"·"being used"·"Directory not empty"·Windows **"Invalid argument"**): 그 worktree 안의 `.venv`/`.codegraph` 를 살아있는 프로세스가 잡고 있다. **먼저 내가 띄운 것부터 회수한다** — 검증용으로 백그라운드 실행한 서버·데몬은 셸 `kill` 로 자식까지 안 죽는 경우가 많다(실측: `uv run` 으로 띄운 서버가 worktree `.venv` 를 잡아 remove 실패). **경로로 대상을 특정해** 종료하고(예: `Get-Process python,<앱> | Where-Object { $_.Path -like "*worktrees\<name>\*" } | Stop-Process -Force`) 재시도한다. ⚠️ **사용자 서버·다른 worktree 프로세스는 건드리지 않는다** — 경로 필터 없이 이름만으로 일괄 종료 금지. 내 것이 아닌 점유(codegraph daemon 등)는 **자동 종료 안 함** — idle 자동종료(~5분) 후 재시도/수동 종료 안내(`--force` 는 OS 점유엔 무효).
  - **부분 성공**(git 등록은 해제됐는데 디렉토리 잔존; Windows long-path·점유): remove 가 실패해도 등록이 빠졌을 수 있으니 **`git worktree list` 로 결과를 확인**한다. 잔존 시 `git worktree prune` + 대상 디렉토리 수동 삭제(점유 회수 후). 이 상태에서는 `git worktree remove` 재실행이 "is not a working tree" 로 실패한다.
- **로컬 브랜치**: worktree 제거 성공 후 `git branch -d <target_branch>`(자동 정리에 포함). 미머지로 `-d` 거부면 `-D` 는 **별도 AskUserQuestion 후에만**(§8) — `-d` 거부 자체가 merged 판정이 틀렸다는 신호다.
- **원격 브랜치**: 자동 정리에 **포함하지 않는다**. 필요 시 worktree·로컬 삭제 성공 후 `git push origin --delete <target_branch>` 를 **AskUserQuestion 으로 확인받고**만 실행(원격 ref 부재면 no-op·경고만). merged 판정은 확정이 아니고(특히 5(b) 진행중 child·squash 미감지) 원격 삭제는 다른 머신의 유일본을 지울 수 있다.

## D. 복귀 후 main-autopull pull (SKILL §8 ⓑ)
세션이 **실제로 main 에 복귀했을 때만** `git pull --ff-only origin "$(git rev-parse --abbrev-ref HEAD)"` 1회 — 세션 중 머지·원격 진행분 반영(post-checkout hook 은 `git checkout` 에만 뜨고 ExitWorktree 복귀엔 안 뜨므로 이 구간 커버). **원격은 반드시 현재 브랜치**(하드코딩 `main` 금지 — master repo 오대응 방지). 선행 가드 전부 충족 시에만: ① main worktree ② `git rev-parse --abbrev-ref HEAD` ∈ {main,master} ③ working tree clean. **no-op(feature 브랜치 잔류)·dirty·ff 실패·origin 부재면 skip**(feature 브랜치에 origin/main merge 하는 파괴 방지). 자동 rebase·stash·force 없음(§8).

## E. 머지 모드 gh 메커닉 (SKILL M1~M6)
SKILL 의 게이트·순서·닫힌 목록이 단일 소스. 여기는 명령·필드·템플릿·시나리오 표. 아래 JSON 필드는 gh 2.89 `--help` 로 실존 확인(2026-09-02).

- **M1 조회**: 브랜치 `git rev-parse --abbrev-ref HEAD`(`HEAD` 면 detached). `gh repo view --json defaultBranchRef,mergeCommitAllowed,squashMergeAllowed` 한 번으로 인증·GitHub 여부·`<default>` 폴백·머지 방식을 같이 얻는다(실패 = M1 거부). `<default>` 는 `git symbolic-ref --short refs/remotes/origin/HEAD` 에서 `origin/` 을 뗀 이름 → 실패 시 위 `defaultBranchRef.name`.
- **M2 PR 조회**: `git fetch origin <default>` → `gh pr list --head <branch> --base <default> --state all --json number,state,isDraft,url`. `state` ∈ {OPEN, MERGED, CLOSED}. 후보 2개+ → 중단. 지름길 판정은 `git rev-list --count origin/<default>..HEAD` = 0 + plan `status: done`; 진입 시 `git restore plans/<dir>/<slug>-plan.md`. OPEN 이면 `gh pr view <N> --json mergeable,mergeStateStatus,headRefOid` 로 사전 점검.
- **PR 생성(M3)**: `gh pr create --base <default> --head <branch> --title "<title>" --body-file <scratchpad>/pr-body.md`. body 는 `## Summary`(plan `# Goal`·주요 변경 bullet) · `## Review`(리뷰어·처분 요약) · `## Verification`(실행한 검증 명령·결과) · 트레일러(`🤖 Generated with [Claude Code](https://claude.com/claude-code)` + 세션 URL, 하네스 지시 그대로). 파일로 쓰는 이유는 CLAUDE.md §2(긴 payload 를 tool 파라미터에 넣지 않는다).
- **사전 점검 값**: `mergeable` ∈ {MERGEABLE, CONFLICTING, UNKNOWN}, `mergeStateStatus` ∈ {CLEAN, UNSTABLE, HAS_HOOKS, UNKNOWN, DIRTY, BEHIND, BLOCKED, DRAFT}. CONFLICTING/DIRTY/DRAFT → 중단·사유 보고(plan 무변경). UNKNOWN 은 10초 후 최대 3회 재조회. BEHIND/BLOCKED 는 required check 전엔 정상이라 M3 에선 통과, M6 직전 재평가에서 남아 있으면 REJECTED.
- **M5 checks**: `gh pr view <N> --json headRefOid` = `git rev-parse HEAD` 대조 → `gh pr checks <N> --watch`(Bash timeout 600000). exit 0 → `gh pr checks <N> --json name,bucket`(`--watch` 와 `--json` 은 병용 불가라 별도 호출) 로 bucket ∈ {pass, fail, pending, skipping, cancel} 확인. exit 8 = pending 잔존. exit 1 + stderr `no checks reported on the '<branch>' branch`(소문자 부분일치 `no checks reported`) = checks 없음 → `sleep 15` 후 `gh pr view <N> --json statusCheckRollup` 3회, 배열이 계속 비어 있을 때만 required 없음.
- **M6 머지·분류**: `gh pr merge <N> --merge --match-head-commit <headRefOid>`(`mergeCommitAllowed: false` 면 `--squash`). 성공 exit 후 `gh pr view <N> --json state,mergedAt,mergeCommit` — `mergedAt` non-null = MERGED, null = QUEUED(merge queue). 명령 실패 = REJECTED, 확인 명령 실패 = UNKNOWN. MERGED 면 `git fetch origin <default>`. 7단계 재수집(`collect-state.sh`)에서 조건4 는 이 `mergedAt` 로 충족(squash 는 `inBase`·`patchInBase` 가 false 일 수 있다 — §B 의 squash 미감지 한계).
- **커밋 메시지**: done `docs(plan): close <slug> (PR #N)`, 복구 `docs(plan): reopen <slug> (PR #N <사유>)`.

### 시나리오 표 (외부 쓰기 · plan status · `# Next` · 재실행)
| 시나리오 | 외부 쓰기 | plan status | `# Next` | 재실행(`/e merge`) 결과 |
|---|---|---|---|---|
| 새 PR, checks pass, MERGED | push·PR·merge | done | 없음 | M2: base 에 없는 커밋 0·done → M6 확인·fetch → 5~8 |
| 기존 open PR | push(변경 있을 때) | done | 없음 | 동일 PR 재사용 |
| 기존 merged/closed PR + 새 커밋(plan done 등) | push·새 PR·merge | done | 없음 | 새 PR 재사용 |
| draft PR | 없음(M2 에서 중단) | 불변 | 불변 | draft 해제 후 재실행 |
| 사전 점검 CONFLICTING/DIRTY | push·PR(생성된 경우) | 불변(done 전 중단) | 불변 | 해소 후 재실행 → M2 재사용 |
| M6 직전 BEHIND/BLOCKED 잔존 (REJECTED) | push·PR | in_progress(복구) | protection 충족 후 재실행 | M2 재사용 → M5 |
| MERGED/CLOSED PR + plan 미done 재실행 | push·새 PR·merge | done(M4 선행) | 없음 | 새 PR 재사용 |
| checks none(3회 재조회 후에도) | push·PR·merge | done | 없음 | required 없음으로 진행 |
| checks pending→pass | 위와 동일 | done | 없음 | — |
| checks fail·cancel (REJECTED) | push·PR | in_progress(복구) | 수정 후 재실행 | 수정·push 후 M2 재사용 → M5 |
| checks timeout / exit 8 (REJECTED) | push·PR | in_progress(복구) | "PR #N checks 대기, `/e merge` 재실행" | M2 재사용 → M5 |
| 머지 직전 CONFLICTING (REJECTED) | push·PR | in_progress(복구) | 충돌 해소 후 재실행 | rebase/merge 후 push → M5 |
| `--match-head-commit` 불일치 | push·PR | done 유지(중단·보고) | 불변 | head 확인 후 재실행 |
| merge 커밋 불허 → squash MERGED | push·PR·merge(squash) | done | 없음 | mergedAt 로 조건4 충족 |
| 권한 프롬프트 거절·branch protection (REJECTED) | push·PR | in_progress(복구) | 사유 해소 후 재실행 | M2 재사용 |
| QUEUED(merge queue) | push·PR·merge(큐) | done 유지 | "큐 완료 후 `/e merge` 재실행" | M2: MERGED 재사용 안 함·커밋 0 → M6 확인·fetch |
| UNKNOWN(확인·fetch 실패) | push·PR·merge(?) | done 유지 | "`gh pr view` 재조회 후 재실행" | M2 분기 |
| `gh repo view` 실패(미인증·GitHub 아님) | 없음 | 불변 | 불변 | M1 거부 |
| push 거부(`permissions.ask` 거절) | 없음 | 불변(M4 선행 시 로컬 done → 복구) | 불변 | M3 중단 |
| plan 없음 / 브랜치 main·detached / Acceptance 미체크 | 없음 | — | — | M1 거부 |
| 머지 후 5~8단계 실패 | 없음 추가 | done | 실패 단계 기록 | merge 재호출 없이 5~8 재시도 |
| 복구 push 거부 | 없음 | in_progress(로컬만) | 로컬 커밋 push 필요 보고 | push 후 M2 |
