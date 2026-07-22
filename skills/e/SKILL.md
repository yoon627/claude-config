---
name: e
description: 진행 중이던 §10 plan 을 실제 git/코드 상태로 동기화 기록하고 작업을 마무리하는 plan-end 오케스트레이션. uncommitted 변경은 작업 브랜치에 임시(WIP) 커밋으로 보존하고(main/master 직접 커밋·push 는 안 함), Progress/Next/Decisions/status/updated 를 갱신해 다음 세션(/c)이 곧장 이어받게 한다. worktree 에서 작업이 done 으로 끝나고 clean·pushed·base 에 merged 면 worktree 삭제도 제안한다. 마무리 후에는 세션을 main worktree 로 복귀시킨다(worktree 보존). `/e` 명시 호출 또는 "진행상황 기록하고 마무리 / 오늘 여기까지 / 일단 저장하고 끝"류 요청 시 사용. plan 이 없으면 새로 만들지 않는다(그건 dlc 몫). 단순 질문·탐색·읽기 전용에는 쓰지 않는다.
---

# e — plan 마무리 (plan end)

진행 중이던 §10 plan 을 **실제 git/코드 상태로 동기화 기록**하고, uncommitted 변경을 **임시 커밋으로 보존**한 뒤 작업을 마무리한다. 다음 세션이 `/c` 로 곧장 이어받게 만드는 게 목표. CLAUDE.md §10 "턴 종료 / 완료" + §8 git 규칙의 자동화 버전 — **충돌 시 CLAUDE.md 우선**. c(이어가기)의 대칭.

## 적용
- `/e` 명시 호출, 또는 "진행상황 기록하고 마무리 / 오늘 여기까지 / 일단 저장하고 끝" 류 요청 시.
- 단순 질문·탐색·읽기 전용·한 턴짜리 명령은 제외. **plan 이 없으면 새로 만들지 않는다** (dlc/작업 시작의 몫).

## 동작 (7단계: 찾기 → 상태 수집·임시 커밋 → plan 동기화 → 마무리 보고 → worklog 기록 → worktree 정리 제안 → main 복귀)

### 1. plan 찾기 (c 1단계와 동일)
- `ROOT = git rev-parse --show-toplevel`, `BR = git rev-parse --abbrev-ref HEAD`.
- 탐색 위치(존재하는 것만, 중복 제거): `<ROOT>/plans/`, 그리고 cwd 가 worktree 면 main worktree 의 `plans/` (`git worktree list --porcelain` 첫 `worktree <path>`). plans/ 는 worktree(브랜치)별 독립이라 양쪽을 봐야 누락이 없다(tracked 지만 브랜치마다 내용이 다르다).
- **매칭**(§10): `BR` 이 plan **dir 이름**(`<YYYY-MM-DD>-<slug>`)에 포함되는 dir → 그 안 `*-plan.md` 1개. 1개 채택 / 2개+ 후보 제시 후 선택 / 0개 fallback.
- **active plan 우선**(§10): 세션에서 진행 중이던 plan 이 이미 있으면 branch 매칭과 무관하게 그것을 대상으로 한다 (branch≠slug 여도 빠뜨리지 않음).
- **fallback (매칭 0개)**: `status: in_progress|blocked` plan 을 `updated` 내림차순 목록 제시 → 사용자 선택. 추측으로 자동 선택하지 않는다. 전부 done/없음이면 "마무리할 plan 없음" — 그래도 2단계(임시 커밋)는 수행하고 보고만 한다.

### 2. 작업 상태 수집 + 임시 커밋
- **수집 (`collect-state.sh` 1회)**: `bash skills/e/collect-state.sh` 로 읽기전용 상태 신호를 평문 `key: value` 로 받는다(개별 git 10+ 호출 1회 묶음). **헬퍼 실패·필드 누락이면** 보고에 명시하고 개별 git 명령으로 폴백. **필드 카탈로그·파싱 규칙(첫 `: ` split·list 필드)·조건별 폴백 명령은 `docs/worktree-lifecycle.md` §A**(상태 수집 분기에서 Read).
- **임시 커밋**(아래 "임시 커밋 규칙"): uncommitted 있으면 작업 브랜치에 WIP 커밋으로 보존. 없으면 skip + "변경 없음" 명시.

### 3. plan 동기화 기록 (메인이 single writer; §10)
plan 을 re-read(외부 변경 merge) 후 **사실 기반으로만**(§1) 갱신:
- `# Progress`: 오늘 진행 한 줄 + 임시 커밋 sha7.
- `# Next`: 다음 세션 즉시 액션으로 교체(실효된 것 정리). WIP 커밋 있으면 "WIP `<sha7>` 이어서/squash" 명시 → c 가 인지.
- `# Decisions`: 세션 중 결정·스코프 변경 보강(기존은 지우지 말고 §10 방식 "~로 변경 (이유: …)" 덮어쓰기/추가).
- `# Key Files`: 추가/이동 동기화.
- `# Blockers`: 막힌 것 + 풀 조건.
- frontmatter: `status` 판정(4단계) · `updated:` 오늘.
- **plan 무결성(plan-lint)**: 위 갱신을 **write 한 뒤** `node scripts/plan-lint.js <이 plan>`(있으면) 실행 — frontmatter·6 H1 섹션·**끊긴 Acceptance 참조** 검증. 위반은 **그 자리에서 보정**(additive 편집이 참조를 깬 경우 흔함). 명령 실패(스크립트 부재 등)는 skip+명시. hard-stop 아님.

### 4. status 판정 + 마무리 보고
- **status 판정**:
  - 머지·배포 등 **확정 완료 신호** 있을 때만 `done` — 단 done 전환은 **사용자 확인**(마무리=세션 끝이지 작업 끝이 아닐 수 있음).
  - 막힘 → `blocked` + `# Blockers`.
  - 그 외 → `in_progress` 유지(체크포인트).
- **보고**: plan 위치·title·status / 임시 커밋 sha(또는 "변경 없음") / 동기화한 항목 / 남은 작업(`# Next`·`# Blockers`) / "다음 세션은 `/c` 로 이어받기".
- **recap 형식(CLAUDE.md §3-6)**: 위 보고는 **결론 요약(≤3줄, 무엇이 끝났고 status)을 먼저**. **`/e` 호출 자체가 "마무리" 지시**이므로 §3-6 예외(사용자가 이미 다음 지시를 준 흐름 → 선택지 생략)에 따라 **새 AskUserQuestion(4선택지)을 만들지 않는다**(마무리 시점 1회 원칙). 마무리 액션은 아래 6단계 worktree 정리 제안(조건 충족 시)과 7단계 "다음 세션 `/c`" 안내가 담당한다 — step6 는 조건부(done·plan-in-worktree)라 안 뜰 수 있고 그때도 별도 질문을 새로 만들지 않는다.

### 5. worklog 기록 (현재 worktree — 삭제·복귀 전)
마무리 시 이 worktree 에서 한 AI 작업시간을 Jira worklog 에 기록한다. **세션이 아직 worktree 에 있을 때(cwd = 현재 worktree)** 실행 — 6단계 삭제·7단계 main 복귀 전이라 순서가 중요. `~/.claude/skills/jira-worklog/` 없으면 이 단계 skip + "worklog 스킬 없음" 1줄.
- **실행**: `python ~/.claude/skills/jira-worklog/jira_worklog.py`(dry-run)로 날짜별 시간·대상 티켓 확인(cwd = 현재 worktree — main 에서 돌리면 그 worktree 시간 안 잡힘).
- **등록**: 티켓이 잡히고(worktree 이름 prefix) `~/.jira-kit/.env` 에 토큰 있으면 이어서 `--register` — 그날 항목 upsert(멱등, /e 반복해도 중복 없음). **티켓 없음/토큰 없음/세션 활동 없음 → preview 만 하고 조용히 넘어감**(마무리 흐름 방해 금지). 사용자가 /e 에 이 동작을 넣은 것 = 등록 표준 동의(별도 AskUserQuestion 안 만듦, §3-6 1회 원칙).
- **비차단**: 조회·네트워크 실패는 보고 1줄만 하고 마무리는 계속(worklog 실패가 /e 를 막지 않는다).
- 보고 1줄: 등록 결과("CSTP1-xxxx 에 `<시간>` 등록" · "티켓 없음/토큰 없음 → preview 만" · "세션 활동 없음").

### 6. worktree 정리 제안 (조건부)
마무리가 끝난 뒤, 현재 worktree 가 **역할을 다했고 안전하게 지울 수 있으면** 삭제를 제안한다 — **자동 삭제 안 함, 항상 AskUserQuestion**.
- **제안 조건 (6가지 모두 충족 = AND)**: 2단계 이후 WIP 커밋·plan write 로 상태가 바뀌므로 **삭제 직전 `bash skills/e/collect-state.sh` 를 한 번 더 실행**해 그 신호로 판정(2단계 스냅샷 재사용 금지 — 재수집 invariant). **헬퍼 실패·필드 누락·파싱 불가면 제안 생략(보수)**.
  1. **비-메인 worktree**(`root` ≠ `mainWorktree`; 메인이면 제안 안 함)
  2. **`detached`=false + plan `status == done`**(4단계 확정)
  3. **working tree clean**(untracked 포함; `dirty`=unknown 이면 생략)
  4. **unpushed 없음**(`unpushedStatus`=unknown 이면 미보존으로 제안 안 함 — false-positive 삭제 차단)
  5. **base 또는 다른 원격 브랜치에 merged**(git-only 추정, 확정 아님 — 최종 삭제는 늘 AskUserQuestion; squash merge 는 미감지=유지 방향이라 안전)
  6. **미보존 산출물 안전**(`git worktree remove`/`--force` 가 gitignored `.env`·미커밋 plan 을 유실시킴 — 이 worktree `plans/` 에 이번 갱신한 미커밋 plan 있으면 제안 생략; `.env`·secret 후보 있으면 삭제 목록 명시; `ignoredStatus`=unknown 이면 생략)
  - **각 조건의 판정 git 명령·폴백·`inBase`/`patchInBase`/`remoteContainingHead` 세부·squash/rebase 한계는 `docs/worktree-lifecycle.md` §B**(삭제 판정 분기에서 Read).
  - 하나라도 불충족/위험/헬퍼 불가 → 제안 생략 + 보고에 사유 한 줄("미머지 → 유지"·"unpushed 2건 → 유지"·"plan 이 worktree 내부 → 유지").
- **제안 (AskUserQuestion; wt rm 계열)**: ① worktree 만(브랜치 유지) / ② +로컬 브랜치(원격 유지) / ③ +로컬·원격(조건4 pushed·조건5 merged 신호 충족분만 — 조건5 불확실성 경고 본문 노출) / ④ 유지(기본). 실행은 "worktree 정리 규칙"(+ `docs/worktree-lifecycle.md` §C).

### 7. 세션을 main worktree 로 복귀
1~6단계 후 세션을 main worktree 로 되돌린다(작업 기록은 worktree 에 남기고 다음 작업은 main 에서). **비파괴적**(worktree·브랜치 보존)이라 자동 수행.
- **대상**: 6단계 후에도 세션이 **비-메인 worktree** 에 있을 때(`--show-toplevel` ≠ main path, 정규화 후 비교). 메인이면 skip.
- 6단계에서 worktree 를 **삭제한 경우** → 이미 main 복귀됨 → skip(중복 `ExitWorktree` 금지).
- 그 외(유지·제안 생략·조건 미충족) → `ExitWorktree(action: keep)` 로 원래 디렉토리(보통 main) 복귀. plan `status` 무관 — `in_progress` 체크포인트여도 세션만 빠지고 worktree·브랜치는 남는다(다음에 `/wt <name>` 로 들어가 `/c` 로 이어감).
- **`ExitWorktree` 가 no-op**(harness 가 worktree 에서 바로 시작해 `EnterWorktree` 미경유) → in-session 복귀 불가. 강제 이동 금지 — "세션 종료하면 harness 가 worktree 를 놓는다"고 보고만(다른 worktree 로 우회하지 않는다).
- **복귀 후 main 최신화 (main-autopull ⓑ)**: 세션이 **실제로 main 에 복귀했을 때만** — ① main worktree ② 현재 브랜치 ∈ {main, master} ③ clean **전부 충족 시** — `git pull --ff-only origin "$(현재 브랜치)"` 1회(하드코딩 `main` 금지 — master repo 오대응 방지). **no-op(feature 잔류)·dirty·ff 실패·origin 부재면 skip**(feature 에 origin/main merge 하는 파괴 방지). 자동 rebase·stash·force 없음(§8). 세부 `docs/worktree-lifecycle.md` §D.
- 한 줄 보고: main 복귀 여부(또는 불가 사유).

## 임시 커밋 규칙
마무리 시 uncommitted 변경을 잃지 않도록 작업 브랜치에 보존한다. **자동 수행하되 아래 안전장치 필수.**

- **브랜치 보호(§8)**: 현재 브랜치가 `main`/`master`(또는 `origin/HEAD` default)면 직접 커밋 금지. 멈추고 AskUserQuestion — ① 작업 브랜치 새로 만들어 거기 커밋 / ② 커밋 생략하고 plan 기록만 / ③ 취소. 자동 브랜치 생성·강제 커밋 안 함.
- **위험 파일 점검(§8)**: `git status` 에 `.env`·`*.key`·`*.pem`·`id_rsa`·인증서·대용량(빌드 산출물 등) 의심 항목 있으면 커밋 보류 + 사용자 확인(secret 유출 방지).
- **커밋**: 안전하면 `git add -A` 후 `git commit`. 메시지 `wip: <작업 한 줄 요약> (e checkpoint)` + 규약 트레일러(Co-Authored-By). 본문에 "다음 세션 squash/amend 대상" 한 줄.
- **push 안 함** — §8, 사용자 요청 시만.
- uncommitted 없으면 커밋 skip.

## worktree 정리 규칙
6단계에서 사용자가 삭제를 택했을 때만. **cwd 가 삭제 대상 안이라 순서 중요.**
- **이동 전 값 캡처**: `target_path`·`target_branch`·`main_path`(`git worktree list --porcelain` 첫 worktree)를 **세션 옮기기 전에** 고정(이동 후 재계산하면 엉뚱한 대상·main 가리킴).
- **worktree 밖으로**: `ExitWorktree(action: keep)` 로 원래 디렉토리(보통 main) 복귀 — 대상 안에선 자기 remove 불가. **`ExitWorktree` no-op**(harness 가 worktree 에서 시작)이면 폴백은 `docs/worktree-lifecycle.md` §C(다른 linked worktree 경유 or remove 생략+보고) — **강제 진행 금지**. 이동 실패로 cwd 가 대상 안이면 **중단+보고**(remove 금지).
- **제거**: cwd 가 대상 밖 확인 후 `git worktree remove <target_path>`. 실패 시 stderr 분기(untracked→`--force`·codegraph daemon 파일점유·부분성공 prune) 세부는 `docs/worktree-lifecycle.md` §C.
- **안전 게이트(§8) — 무확인 금지**: `--force`·`git branch -D`(미머지)·원격 `git push origin --delete` 는 **별도 AskUserQuestion 확인 후에만**.
- **로컬 브랜치(옵션 ②·③)**: `git branch -d <target_branch>`(미머지 `-d` 거부 시 `-D` 는 확인 후). **원격(옵션 ③만)**: worktree·로컬 삭제 성공 후 `git push origin --delete <target_branch>`(원격 ref 부재 no-op). 조건5 확정 아님 → 사용자가 경고 보고 택한 경우만(orphan 방지). 그 외 push 안 함.
- 한 줄 보고: 제거한 worktree·브랜치(또는 유지 사유).

## 경계 (안 하는 것)
- **push 안 함**(§8). **main/master 직접 커밋 안 함** — 확인 후 분리.
- plan 없으면 **새로 만들지 않음** — 임시 커밋 + "마무리할 plan 없음" 보고만(plan 가치 있어 보이면 dlc 제안 한 줄).
- done **자동 전환 안 함** — 확정 완료 신호 + 사용자 확인 시만. 기본 in_progress 체크포인트.
- plan 갱신은 **사실 기반만**(§1) — git/파일로 확인된 것만. 추측으로 Progress/Decisions 채우지 않는다.
- subagent 위임 아님 — plan single writer 는 메인. 메인이 직접 커밋/기록한다.
- **worktree 자동 삭제 안 함** — 6단계 제안 조건(비-메인·done·clean·pushed·merged·ignored 안전) 충족 시에도 항상 AskUserQuestion. `--force`·`git branch -D`·**원격 삭제(`git push origin --delete`)**는 명시 확인 없이 금지(§8).
- **main 복귀(7단계)는 자동** — `ExitWorktree(action: keep)` 라 worktree·브랜치를 보존하는 비파괴 동작이라 확인 없이 수행. 단 삭제(remove)는 7단계 아닌 6단계 사안이고, no-op(harness 가 worktree 에서 시작)이면 강제 이동 없이 보고만.
