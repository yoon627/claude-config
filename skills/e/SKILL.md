---
name: e
description: 진행 중이던 §10 plan 을 실제 git/코드 상태로 동기화 기록하고 작업을 마무리하는 plan-end 오케스트레이션. uncommitted 변경은 작업 브랜치에 임시(WIP) 커밋으로 보존하고(main/master 직접 커밋·push 는 안 함), Progress/Next/Decisions/status/updated 를 갱신해 다음 세션(/c)이 곧장 이어받게 한다. worktree 에서 작업이 done 으로 끝나고 clean·pushed·base 에 merged 면 worktree 삭제도 제안한다. 마무리 후에는 세션을 main worktree 로 복귀시킨다(worktree 보존). `/e` 명시 호출 또는 "진행상황 기록하고 마무리 / 오늘 여기까지 / 일단 저장하고 끝"류 요청 시 사용. plan 이 없으면 새로 만들지 않는다(그건 dlc 몫). 단순 질문·탐색·읽기 전용에는 쓰지 않는다.
---

# e — plan 마무리 (plan end)

진행 중이던 §10 plan 을 **실제 git/코드 상태로 동기화 기록**하고, uncommitted 변경을 **임시 커밋으로 보존**한 뒤 작업을 마무리한다. 다음 세션이 `/c` 로 곧장 이어받게 만드는 게 목표. CLAUDE.md §10 "턴 종료 / 완료" + §8 git 규칙의 자동화 버전 — **충돌 시 CLAUDE.md 우선**. c(이어가기)의 대칭.

## 적용
- `/e` 명시 호출, 또는 "진행상황 기록하고 마무리 / 오늘 여기까지 / 일단 저장하고 끝" 류 요청 시.
- 단순 질문·탐색·읽기 전용·한 턴짜리 명령은 제외. **plan 이 없으면 새로 만들지 않는다** (dlc/작업 시작의 몫).

## 동작 (6단계: 찾기 → 상태 수집·임시 커밋 → plan 동기화 → 마무리 보고 → worktree 정리 제안 → main 복귀)

### 1. plan 찾기 (c 1단계와 동일)
- `ROOT = git rev-parse --show-toplevel`, `BR = git rev-parse --abbrev-ref HEAD`.
- 탐색 위치(존재하는 것만, 중복 제거): `<ROOT>/plans/`, 그리고 cwd 가 worktree 면 main worktree 의 `plans/` (`git worktree list --porcelain` 첫 `worktree <path>`). plans/ 는 gitignored & worktree별 독립이라 양쪽을 봐야 누락이 없다.
- **매칭**(§10): `BR` 이 plan **dir 이름**(`<YYYY-MM-DD>-<slug>`)에 포함되는 dir → 그 안 `*-plan.md` 1개. 1개 채택 / 2개+ 후보 제시 후 선택 / 0개 fallback.
- **active plan 우선**(§10): 세션에서 진행 중이던 plan 이 이미 있으면 branch 매칭과 무관하게 그것을 대상으로 한다 (branch≠slug 여도 빠뜨리지 않음).
- **fallback (매칭 0개)**: `status: in_progress|blocked` plan 을 `updated` 내림차순 목록 제시 → 사용자 선택. 추측으로 자동 선택하지 않는다. 전부 done/없음이면 "마무리할 plan 없음" — 그래도 2단계(임시 커밋)는 수행하고 보고만 한다.

### 2. 작업 상태 수집 + 임시 커밋
- 수집: `git status --short`, `git log --oneline`(plan 시작 이후 새 커밋), origin 대비 unpushed·merged 여부(판정 명령은 5단계 조건 4·5; `BASE` 정의는 조건5). 점검 명령이 실패(origin 없음 등)하면 그 점검만 skip + 보고에 명시.
- **임시 커밋**(아래 "임시 커밋 규칙"): uncommitted 있으면 작업 브랜치에 WIP 커밋으로 보존. 없으면 skip + "변경 없음" 명시.

### 3. plan 동기화 기록 (메인이 single writer; §10)
plan 을 re-read(외부 변경 merge) 후 **사실 기반으로만**(§1) 갱신:
- `# Progress`: 오늘 진행 한 줄 + 임시 커밋 sha7.
- `# Next`: 다음 세션 즉시 액션으로 교체(실효된 것 정리). WIP 커밋 있으면 "WIP `<sha7>` 이어서/squash" 명시 → c 가 인지.
- `# Decisions`: 세션 중 결정·스코프 변경 보강(기존은 지우지 말고 §10 방식 "~로 변경 (이유: …)" 덮어쓰기/추가).
- `# Key Files`: 추가/이동 동기화.
- `# Blockers`: 막힌 것 + 풀 조건.
- frontmatter: `status` 판정(4단계) · `updated:` 오늘.

### 4. status 판정 + 마무리 보고
- **status 판정**:
  - 머지·배포 등 **확정 완료 신호** 있을 때만 `done` — 단 done 전환은 **사용자 확인**(마무리=세션 끝이지 작업 끝이 아닐 수 있음).
  - 막힘 → `blocked` + `# Blockers`.
  - 그 외 → `in_progress` 유지(체크포인트).
- **보고**: plan 위치·title·status / 임시 커밋 sha(또는 "변경 없음") / 동기화한 항목 / 남은 작업(`# Next`·`# Blockers`) / "다음 세션은 `/c` 로 이어받기".

### 5. worktree 정리 제안 (조건부)
마무리가 끝난 뒤, 현재 worktree 가 **역할을 다했고 안전하게 지울 수 있으면** 삭제를 제안한다 — **자동 삭제 안 함, 항상 AskUserQuestion**.
- **제안 조건 (모두 충족 시에만; 2단계 결과를 신뢰하지 말고 삭제 직전 대상 worktree 기준으로 재수집)**:
  1. cwd 가 **비-메인 worktree** — `git rev-parse --show-toplevel`(canonical 절대경로) ≠ main worktree path(`git worktree list --porcelain` 첫 `worktree <path>`). 슬래시 방향·대소문자 normalize 후 비교. 메인이면 제안 안 함.
  2. **detached HEAD 아님** + plan `status == done`(이번 4단계 확정). detached 면 브랜치 기준 판정이 불가하니 제안 생략.
  3. **tracked 변경 없음** — 지금 시점 `git status --porcelain` 이 빈 출력.
  4. **unpushed 없음** — upstream 있으면(`git rev-parse --abbrev-ref --symbolic-full-name @{u}`) `git log @{u}..HEAD` 가, 없으면 폴백 `git log <branch> --not --remotes`(wt rm 과 동일) 가 비어야 한다(모든 커밋이 원격에 보존됨). 원격 자체가 없으면 미보존으로 보고 제안 안 함. (`git log origin/<branch>..HEAD` 는 origin ref 부재 시 fatal 이라 쓰지 않는다.)
  5. **base 또는 다른 원격 브랜치에 merged 됨 (둘 다 git-only 추정 — 확정 아님)** — pushed(조건4)는 커밋이 원격에 보존됐다는 뜻일 뿐, PR 리뷰 중·머지 전이면 그 브랜치에서 수정이 더 남아 지우면 안 된다. 아래 (a)·(b) 중 하나라도 머지 신호면 제안하되, 둘 다 **로컬 git 커밋 그래프 기반 추정**이라 확정이 아니며 최종 삭제는 늘 AskUserQuestion 이다:
     - **(a) 기본 base 포함**: `BASE` = `git symbolic-ref --short refs/remotes/origin/HEAD`(실패 시 `origin/main`); `git rev-parse --verify --quiet <BASE>` 로 **유효성 먼저 확인** — 무효면(원격/기본 브랜치 미설정) 이 신호 skip(조건4 처럼 fatal `git log` 회피). 유효하면 `git log <BASE>..HEAD` 가 비면(브랜치 커밋이 모두 BASE 에 포함) BASE 에 merged.
     - **(b) 다른 원격 브랜치 포함 (ticket-to-ticket 머지 감지)**: (a) 가 비어있지 않아도, `git branch -r --contains HEAD` 결과에서 self(`origin/<현재브랜치>`)를 뺀 원격 브랜치가 남으면 그 브랜치에 머지됐을 가능성(이 worktree 가 기본 브랜치 아닌 다른 ticket 위로 분기·PR 된 경우 — 예: CSTP1-2615 가 CSTP1-2613 에 머지). ⚠️ 단 **진행 중인 다른 브랜치가 내 커밋을 조상으로 쌓은 경우도 포함**되므로 머지 확정이 아니다 → 그 브랜치명을 근거로 들고, 5단계 제안의 AskUserQuestion 본문에 "`<HEAD7>` 가 `<remote-branch>` 에 포함됨 — 거기 머지됐을 수 있으나 진행 중 브랜치일 수도(확정 아님)" 로 **명시**해 사용자가 판단하게 한다.
     - (a)·(b) 모두 신호 없으면(self 만 남거나 BASE 에 미포함) → 미머지로 보고 생략·유지.
     - ⚠️ 한계: squash/rebase 머지는 원커밋 SHA 가 어느 브랜치에도 안 남아 (a)·(b) 둘 다 못 잡아 미머지로 보이고(no-ff 전제), fetch 안 한 stale 원격 ref 도 그러함 — 둘 다 유지 방향이라 안전. **PR 상태 직접 조회(Bitbucket API 등)는 인증·CLI 부재(ssh remote)와 headless/cron 동작 때문에 쓰지 않는다** — git-only 추정 + 사용자 확인으로 대신한다. 막으려는 1순위는 false-positive(미머지 삭제)이므로 (b)는 "확정"이 아니라 "근거 제시"로만 쓴다.
  6. **gitignored 산출물 점검 (필수)** — `git worktree remove`(--force 없이)는 **gitignored 파일을 경고 없이 함께 삭제**한다. 이 repo 는 whitelist `.gitignore` 라 `plans/`·`.env` 가 ignored → `git status` 엔 안 보인다. `git status --porcelain --ignored` 로 인벤토리를 수집:
     - 이 worktree `plans/` 에 **이번에 갱신한 plan 이 있으면 → 제안 생략**(방금 done 기록한 plan 이 worktree 와 함께 소실 방지; main worktree `plans/` 로 옮긴 뒤에야 안전).
     - `.env`·secret 후보·기타 산출물이 있으면 → 삭제될 목록을 AskUserQuestion 본문에 **명시**(기본 유지).
  - 하나라도 불충족/위험 → 제안 생략 + 보고에 사유 한 줄(예: "미머지(리뷰 중) → 유지", "unpushed 2건 → 유지", "plan 이 worktree 내부 → 유지").
- **제안 (AskUserQuestion; wt rm 과 동일 옵션)**: ① worktree 만 삭제(브랜치 유지) / ② worktree + 브랜치 삭제 / ③ 유지(기본). 실행은 "worktree 정리 규칙".

### 6. 세션을 main worktree 로 복귀
1~5단계(기록·정리)가 끝나면 세션을 main worktree 로 되돌린다 — worktree 에 작업 기록을 남긴 뒤 다음 작업은 main 에서 시작하도록. **비파괴적**(worktree·브랜치 보존)이라 자동 수행한다.
- **대상**: 5단계 후에도 세션이 **비-메인 worktree** 에 있을 때(`git rev-parse --show-toplevel` ≠ main worktree path, 정규화 후 비교). 메인이면 skip.
- 5단계에서 worktree 를 **삭제한 경우** → 이미 main 으로 복귀됨 → skip(중복 `ExitWorktree` 금지).
- 그 외(유지·제안 생략·조건 미충족) → `ExitWorktree(action: keep)` 로 세션을 원래 디렉토리(보통 main)로 되돌린다. plan `status` 와 무관 — `in_progress` 체크포인트여도 세션만 빠지고 worktree·브랜치는 그대로 남는다(다음에 그 worktree 로 들어가 — 예: `/wt <name>` — `/c` 로 이어가면 된다).
- **`ExitWorktree` 가 no-op 인 경우**(harness 가 worktree 에서 바로 시작해 `EnterWorktree` 를 거치지 않은 세션) → in-session 복귀 불가. 강제 이동 금지 — "세션을 종료하면 harness 가 worktree 를 놓는다"고 보고만 한다(복귀가 목적이므로 다른 worktree 로 우회하지 않는다).
- 한 줄 보고: main 복귀 여부(또는 복귀 불가 사유).

## 임시 커밋 규칙
마무리 시 uncommitted 변경을 잃지 않도록 작업 브랜치에 보존한다. **자동 수행하되 아래 안전장치 필수.**

- **브랜치 보호(§8)**: 현재 브랜치가 `main`/`master`(또는 `origin/HEAD` default)면 직접 커밋 금지. 멈추고 AskUserQuestion — ① 작업 브랜치 새로 만들어 거기 커밋 / ② 커밋 생략하고 plan 기록만 / ③ 취소. 자동 브랜치 생성·강제 커밋 안 함.
- **위험 파일 점검(§8)**: `git status` 에 `.env`·`*.key`·`*.pem`·`id_rsa`·인증서·대용량(빌드 산출물 등) 의심 항목 있으면 커밋 보류 + 사용자 확인(secret 유출 방지).
- **커밋**: 안전하면 `git add -A` 후 `git commit`. 메시지 `wip: <작업 한 줄 요약> (e checkpoint)` + 규약 트레일러(Co-Authored-By). 본문에 "다음 세션 squash/amend 대상" 한 줄.
- **push 안 함** — §8, 사용자 요청 시만.
- uncommitted 없으면 커밋 skip.

## worktree 정리 규칙
5단계에서 사용자가 삭제를 택했을 때만 수행. **cwd 가 삭제 대상 worktree 안이라 순서가 중요.**
- **이동 전 값 캡처**: `target_path`(대상 절대경로)·`target_branch`·`main_path`(`git worktree list --porcelain` 첫 worktree)를 **세션을 옮기기 전에** 고정한다. 이동 후 `--show-toplevel`/`HEAD` 를 재계산하면 엉뚱한 대상(또는 main 자신)을 가리킨다.
- **worktree 밖으로 이동**: `ExitWorktree(action: keep)` 로 세션을 원래 디렉토리(보통 main)로 되돌린다 — 대상 worktree 안에서는 자기 자신을 remove 할 수 없다(cwd 점유). ⚠️ **`EnterWorktree(path: <main_path>)` 는 쓰지 않는다** — 메인 워킹트리는 linked worktree 가 아니라 `EnterWorktree` 가 거부한다(검증됨).
  - **`ExitWorktree` 가 no-op 인 경우**(harness 가 worktree 에서 바로 시작해 `EnterWorktree` 를 거치지 않은 세션): 세션이 그 worktree 에 묶여 in-session 으로 못 빠져나온다. 폴백 — (a) 다른 **linked** worktree 가 있으면 `EnterWorktree(path: <other>)` 로 이동 후 대상 remove, (b) 없으면 remove 를 **생략하고 보고**("세션 종료 시 정리 — 종료하면 harness 가 worktree 를 놓는다" + 수동 `git worktree remove`/디렉토리 삭제 안내). 강제 진행 금지.
  - 이동(또는 폴백) 실패로 cwd 가 여전히 대상 안이면 **중단 + 보고**(remove 진행 금지).
- **제거**: cwd 가 대상 밖임을 확인한 뒤, 대상이 `git worktree list --porcelain` 에 있으면 `git worktree remove <target_path>`. "modified or untracked files" 류로 실패하면 `--force` 는 **별도 AskUserQuestion 확인 후에만**(§8 — 묻지 않고 강제 금지). 디렉토리 삭제가 OS 제약(Windows long-path·점유 등)으로 실패하면 git 등록만 빠지고 디렉토리가 잔존할 수 있으니, 잔존 시 `git worktree prune` + 대상 디렉토리 수동 삭제로 마무리. ignored 산출물 손실 경고는 5단계에서 이미 처리.
- **브랜치 (옵션 ② 일 때만)**: `git branch -d <target_branch>`. 미머지로 `-d` 가 거부하면 `-D` 는 **별도 AskUserQuestion 확인 후에만**(§8, wt 주의 승계).
- **push 안 함** — pushed 가 이미 제안 조건이라 추가 push 없음.
- 한 줄 보고: 제거한 worktree·브랜치(또는 유지 사유).

## 경계 (안 하는 것)
- **push 안 함**(§8). **main/master 직접 커밋 안 함** — 확인 후 분리.
- plan 없으면 **새로 만들지 않음** — 임시 커밋 + "마무리할 plan 없음" 보고만(plan 가치 있어 보이면 dlc 제안 한 줄).
- done **자동 전환 안 함** — 확정 완료 신호 + 사용자 확인 시만. 기본 in_progress 체크포인트.
- plan 갱신은 **사실 기반만**(§1) — git/파일로 확인된 것만. 추측으로 Progress/Decisions 채우지 않는다.
- subagent 위임 아님 — plan single writer 는 메인. 메인이 직접 커밋/기록한다.
- **worktree 자동 삭제 안 함** — 5단계 제안 조건(비-메인·done·clean·pushed·merged·ignored 안전) 충족 시에도 항상 AskUserQuestion. `--force`·`git branch -D` 는 명시 확인 없이 금지(§8).
- **main 복귀(6단계)는 자동** — `ExitWorktree(action: keep)` 라 worktree·브랜치를 보존하는 비파괴 동작이라 확인 없이 수행. 단 삭제(remove)는 6단계 아닌 5단계 사안이고, no-op(harness 가 worktree 에서 시작)이면 강제 이동 없이 보고만.
