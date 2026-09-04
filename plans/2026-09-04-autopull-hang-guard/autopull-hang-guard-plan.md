---
title: autopull-hang-guard — SessionStart 자동 pull 에 hang 방어 (동기 전환은 불가 판정)
status: done
started: 2026-09-04
updated: 2026-09-04
---

# Goal

`~/.claude` 를 공유하는 다른 머신에서 SessionStart 자동 pull 이 **조용히 아무것도 안 하는** 경로를
닫는다. (B) 인증 프롬프트·네트워크 blackhole 에 매달려 timeout 을 태우는 것을 막는다.

~~(C) pull 을 동기로 올려 그 세션이 최신 CLAUDE.md 를 읽게 한다~~ → **실측으로 불가능 판정, 철회**
(아래 `## C 는 불가능하다`). B 만 남는다.

# Progress

- 2026-09-04 조사 — 자동 pull 메커니즘은 이미 구현·머지돼 있다(PR #117,
  `plans/2026-07-22-pull-hook-skip-reason/`). 안 도는 게 아니라 **조용히 skip** 되는 구멍이 남았다.
  사용자가 B·C 를 지정(A = `settings.json` 키 분리는 `settings-fmt-plan-ignore` 에서 별도 진행 중).
- 2026-09-04 **hang 방어 부재 확인** — `install-hooks.sh:66-88`(post-checkout)과
  `session-fetch.js:56-76` 은 `GIT_TERMINAL_PROMPT=0` + SSH `BatchMode`/`ConnectTimeout=10` +
  `http.lowSpeed*` + 워치독을 전부 갖췄는데, **`settings.json` 인라인 체인만 하나도 없다**
  (`grep` 무매칭 + 체인 원문 육안 확인).
- 2026-09-04 C 를 1차로 "가능"이라 판정했다(동기 훅 fixture 실험 2케이스). **뒤에 반증됨** — 아래.
- 2026-09-04 `InstructionsLoaded` 훅(대안 후보)을 CLI 바이너리에서 확인 —
  **observability-only, blocking 미지원, `await` 없이 fire-and-forget, 파일을 이미 읽은 뒤 호출**.
  대안으로 쓸 수 없음이 확정.
- 2026-09-04 **타이밍 실측 3종** — 정상 pull 521/554/712ms · Git Bash `sleep 0.2` = 실제 235ms
  (워치독 iteration 예산이 Windows 에서 ~18% 초과) · 워치독 원시 요소(`kill -0`/`kill`/`wait`)
  Git Bash 동작 확인, 고아 없음(`rc=143`).
- 2026-09-04 **전수 영향범위 조사 완료**(Explore agent). 갱신 지점을 `# Key Files` 에 Y/조건부로
  확정. **CI 정지 위험 1건 발견** — 테스트의 `spawnSync` 가 stdout 파이프 + timeout 없음이라
  백그라운드 pull 을 넣으면 테스트·CI 가 매달린다(`# Decisions` 참조).
- 2026-09-04 **plan-reviewer CONDITIONAL** — blocker 5 + 약한 우려 8. 처분은 `# Review Disposition`.
  Codex 병행은 크레딧 소진으로 생략(§9 사유 기록).
- 2026-09-04 **리뷰 지적 2건을 실측으로 확정** (추정으로 두지 않았다):
  - **훅 그룹은 병렬 실행** — 2초 훅과 즉시 훅이 같은 ms 에 시작. **내 plan 의 "pull→brief 순서"
    서술이 거짓이었고 정정했다.** 부수 소득: 세션 시작 지연은 훅들의 합이 아니라 최댓값.
  - **SessionStart `matcher` 가 동작하고 alternation 도 먹는다** — `startup` 발화 / `compact` 미발화 /
    `startup|resume|clear` 발화 / `resume|compact` 미발화.
- 2026-09-04 **C 철회 (실측 반증)** — 동기 훅에 `sleep 2` 만 넣어도 세션이 옛 CLAUDE.md 를 읽는다.
  실제 훅 설정 + 실제 pull(user-level)로도 같은 결과(훅 실행·pull 성공 로그까지 확인). CLAUDE.md
  로드는 훅과 **경합**할 뿐이라 동기 전환은 이득 없이 비용만 남긴다 → `async: true` 유지,
  `matcher` 도 함께 철회(근거가 동기 비용이었다). 상세는 `## C 는 불가능하다`.
- 2026-09-04 **B 구현·검증 완료** — `scripts/session-start-pull.sh` 신규, 테스트 9→17개 통과(3회 연속),
  shellcheck CI 글롭 전체 clean. 워치독 손자 고아는 `set -m` + 그룹 kill 로 해소(동일 프로베가
  "고아 발생"→"고아 없음"으로 뒤집힘).
- 2026-09-04 **문서 동기화** — README(훅 서술·post-checkout 대비·rollback 파일 스위치·트리),
  `wiki/pages/decision/git-hook-network-safety.md` + `wiki/index.md`(하니스 timeout 이 자손을
  안 거둔다는 정정 + 동기 전환 불가 실측), `skills/improve/improve.sh`(점검 1 이 `.sh` 도 보도록).
- 2026-09-04 **내가 만든 회귀 1건 자체 발견·수정** — Python 텍스트 모드 write 가 Windows 에서
  `\n`→`\r\n` 로 바꿔 LF 파일 5개를 CRLF 로 오염시켰고 shellcheck(SC1017)가 잡았다. LF 로 복원.
  교훈: 이 repo 편집에 Python `io.open(...,'w')` 를 쓰지 말 것(`newline='\n'` 없으면 줄끝을 바꾼다).
- 2026-09-04 **base 이동 대응** — 작업 중 `settings-fmt-plan-ignore` 가 `3a11a92` 로 origin/main 에
  먼저 들어가 `settings.json` 을 전면 재포맷했다(plan `## 머지 순서` 가 예상한 충돌이 반대 순서로
  실현). 내 편집을 백업 → `git checkout -- settings.json` → `merge --ff-only origin/main` →
  새 포맷 위에 2줄만 재적용. **결과 `settings.json` diff = 2줄**로 재포맷과 완전히 분리됐다.
- 2026-09-04 **CI 로컬 전체 재현** — `node --check` 21개, unit test 14종, Python 4종, JSON validation,
  shellcheck, plan-lint 전부 통과. 유일한 실패는 아래 `# Deferred` 의 **입증된 baseline**.
- 2026-09-04 **code-reviewer REQUEST CHANGES → 전건 fix** (처분표는 `# Review Disposition`).
  리뷰가 mutation testing 으로 "헤드라인 설계 2개가 테스트로 안 잠긴다"를 입증했고, 고친 뒤
  **같은 mutation 3종을 재실행해 전부 FAIL(=잡힘)** 을 확인했다. 첫 리뷰어는 6시간 매달려
  중단·재실행했다(codex·네트워크 git·실 remote 실행을 명시 금지하니 14분에 완료).
- 2026-09-04 **Linux(dash) 실측** — CI 는 `sh`=dash 인데 `set -m` 그룹 kill 이 거기서 거부된다는
  지적을 WSL Ubuntu 로 확인했다. 거부는 사실이나 직접 kill 폴백이 받아 **테스트 19/19 통과** →
  CI red 아님. 문서의 "손자까지 거둔다"는 bash 한정으로 좁혔다.
- 2026-09-04 최종: `session-start-pull` 9→**19**개, `session-brief` 74→**75**개, shellcheck clean,
  Windows·Linux 양쪽 통과. 커밋 `dd1956c`.
- 2026-09-04 **PR #159 CI 가 내 오판을 잡았다** — `⑪` 의 하한 단언 `elapsed >= 1500` 이 실제
  1427ms 로 실패. 원인은 워치독 마감이 `date +%s` **초 단위라 절삭**되는 것: `timeout=N` 이어도
  시작이 X.99 초면 마감 `X+N` 은 실제 (N-1).01 초 뒤다. 즉 **실제 대기는 (N-1, N] 초**.
  → 하한을 그 성질에 맞게 재설정(`timeout=3`, 하한 1800ms) + 스크립트 주석에 granularity 명시.
  **이 발견은 앞서 "WSL `/mnt/c` 9p 일관성 아티팩트"라고 적었던 간헐 실패(31회 중 3회)의 진짜
  원인이기도 하다** — 같은 단언이었고, 내 추정은 틀렸다. 그 Deferred 항목은 삭제했다.
  교훈: 재현이 안 되는 간헐 실패를 환경 탓으로 돌리기 전에 **실패 단언 자체를 포착**할 것.
- 2026-09-04 **PR #159** 머지 → `status: done`.

# Next

(없음 — PR #159 로 머지 완료.)

**단, 머지가 곧 배달은 아니다 (이 변경 고유의 문제 — 잊으면 효과가 0)**: `# Deferred` 의 settings.json dirty 문제로,
**로컬 `settings.json` 이 더러운 머신은 이 커밋을 영영 못 받는다.** 즉 hang 방어가 가장 필요한
(무음으로 밀린) 머신이 옛 인라인 체인에 남는다. 머지 후 각 머신에서 확인할 것:
1. `git -C ~/.claude status --porcelain settings.json` — 비어야 pull 이 통과한다.
2. 더러우면 커밋하거나 되돌린 뒤 새 세션 1회.
3. `git -C ~/.claude log -1 --oneline` 이 이 커밋을 포함하는지.

# Review Disposition

plan-reviewer 2026-09-04 (CONDITIONAL). Codex 병행은 **크레딧 소진**(`ERROR: Your workspace is out of
credits.`)으로 생략 — §9 대로 사유 기록.

| # | 지적 | 처분 | 근거 |
|---|---|---|---|
| B1 | 워치독 명목 10s 가 Windows 실제 ~12.2s | **fix** | 내 실측(235ms/iter)과 일치. wall-clock 마감으로 교체 |
| B2 | SessionStart 는 compact/fork 에도 발화 | **무효** | 사실은 맞으나(스키마·matcher 실측 확인) C 철회로 문제 자체가 사라졌다. matcher 는 범위 밖이라 미도입 |
| B3 | 워치독이 merge 중 kill → index.lock·부분 체크아웃 | **fix** | 자기 배포 채널을 스스로 깨는 경로. fetch/merge 분리 |
| B4 | 테스트 COMMAND 추출이 깨진다 | **fix** | 리뷰 안(fixture 에 스크립트 복사)이 내 안보다 낫다 — 경로 검증 보존 |
| B5 | `improve.sh` 가 `.js` 만 봐서 새 `.sh` 미점검 | **fix** | grep 을 `\.(js\|sh)` 로 + 주석 갱신 |
| W1 | 훅 그룹 순차 실행 가정 미검증 | **fix** | **실측 결과 병렬** — 내 plan 서술이 거짓이었다. 정정 + Deferred |
| W2 | C 실측이 project-level 뿐 | **fix — 지적이 옳았고 결론을 뒤집었다** | user-level + 실제 훅으로 재실측했더니 **C 자체가 성립 안 함**. 이 지적이 없었으면 잘못된 기능을 넣을 뻔했다 |
| W3 | Acceptance 1·2 검증이 비결정적 | **fix** | PATH 앞 `git` stub + `CLAUDE_AUTOPULL_TIMEOUT` 주입 |
| W4 | Windows 손자 프로세스 고아 | **fix** | 단정 낮추고 프로세스 목록 관찰로 |
| W5 | rollback 레버가 env 하나뿐 | **fix** | 파일 스위치 `~/.claude/.autopull-off` 추가 |
| W6 | 스탬프 backoff 도입 여부 | **wontfix** | async 유지로 세션 시작 비용이 0 이라 backoff 로 줄일 비용이 없다. 오히려 "최신화"라는 목적을 깎는다 |
| W7 | 폐기됐던 A안 재채택 이유 미기록 | **fix** | `## 스크립트 분리(A안)를 재채택하는 이유` 추가 |
| W8 | lint.yml 서술 부정확 | **fix** | shellcheck 글롭 자동 포함·테스트 이미 등록. 실제 제약은 "shellcheck 통과" |
| — | 배달 순환 | **fix** | `# Next` 에 배달 확인 절차 |
| — | `settings-fmt-plan-ignore` 충돌 | **fix** | 아래 `## 머지 순서` |

## code-reviewer 2026-09-04 (REQUEST CHANGES) — 전건 fix

Codex 병행은 크레딧 소진으로 이번에도 생략(§9). 리뷰가 **mutation testing** 으로 진짜 구멍을
찾았다 — 헤드라인 설계 2개가 어떤 테스트로도 잠기지 않아 되돌려도 전부 통과했다.

| # | 지적 | 처분 | 조치·검증 |
|---|---|---|---|
| M1 | wall-clock 상한이 테스트로 안 잠김(iteration 으로 되돌려도 통과) | **fix** | 설계 텍스트 단언(`_deadline=$(( $(date +%s)`, iteration 카운터 부재) + 타이밍 하한 추가. **mutation 재실행으로 이제 FAIL 확인** |
| M2 | `wait \|\| exit 0`(stale FETCH_HEAD 차단) 안 잠김 | **fix** | 케이스 `⑪-b` 신규 — dirty 로 merge 거부시켜 stale FETCH_HEAD 를 만든 뒤 fetch 를 kill. **mutation 재실행으로 FAIL 확인** |
| M3 | `session-brief.js` 가 새 `.autopull-off` 를 몰라 "원인 미확인" 오진 | **fix** | 분기 1줄 + 회귀 테스트 `ⓝ11-b`. **내가 만든 회귀였다** — 새 kill-switch 를 추가하며 그것을 열거하는 신호를 갱신하지 않았다 |
| M4 | dash 에서 `set -m` 그룹 kill 미성립 → CI red 위험 | **fix + 실측** | **WSL Ubuntu(`/bin/sh`→dash)에서 직접 확인**: 그룹 kill 은 실제로 거부되고 직접 kill 폴백이 받는다. 테스트는 Linux 에서 19/19 통과 → **CI red 아님**. SIGKILL 승격 추가, README·wiki 의 "손자까지 거둔다"를 bash 한정으로 좁힘 |
| m1 | 스크립트 주석이 "동기 훅"이라 서술(실제 async) | **fix** | C 철회 시절 잔재. 주석 2곳 정정(§3-5) |
| m2 | README·`session-brief.js` 가 없어진 `grep -qx main` 을 인용 | **fix** | 두 곳 모두 "브랜치가 `main` 과 정확히 일치할 때만" 으로 |
| m3 | `CLAUDE_AUTOPULL_TIMEOUT` 무상한 → 하니스가 먼저 죽여 고아 | **fix** | `[1,12]` clamp(하니스 15 안) |
| m4 | TERM 후 `wait` 무제한 — escalation 없음 | **fix** | 2초 유예 후 `kill -9` 승격 |
| m5 | 실행 중 자기 파일 교체 시 tail 이 잘려 읽힘 | **fix** | 본문을 `main()` 로 감싸고 마지막 줄 `main "$@"` |
| m6 | 테스트 `⑫` 실패 시 무한 손자 루프 영구 잔존 | **fix** | 손자 루프를 60회(≈18s)로 유한화 |
| n1 | `after=` 에만 `\|\| exit 0` 없음(관례 불일치) | **fix** | 추가 |
| n2 | 비숫자 env → 산술 0 → 매번 즉시 kill(무음) | **fix** | `case` 로 비숫자 거름 |
| n3 | 테스트명 "4종"인데 단언 7개 | **fix** | 이름 정정 |
| — | 리뷰가 발견한 orphan 프로세스 | **해소됨** | 재확인 시 이미 종료돼 있었다 |
| — | 스크립트가 untracked — settings.json 과 **같은 커밋**이어야 | **fix** | 같은 커밋에 포함(따로 나가면 `-r` 가드로 fail-open 되어 자동 pull 이 조용히 영구 정지) |

## 머지 순서 (`settings-fmt-plan-ignore` 와의 충돌)

그 worktree 는 **커밋이 0개**이고 `settings.json` 변경은 **시맨틱 델타 0**(순수 재포맷)임을 확인했다
(`git log main..HEAD` 무결과, JSON 평탄화 비교 무차이). 따라서 텍스트 충돌은 나더라도 **내용 손실이
없다** — 이쪽을 먼저 머지하고, 재포맷 쪽이 나중에 포맷을 다시 적용하면 된다. 반대 순서면 내 한 항목
변경이 재포맷 diff 에 묻혀 리뷰가 어려워진다.

# Decisions

## C 는 불가능하다 — 순서 보장이 아니라 경합이다 (✅확실, 실측 3회)

**처음엔 가능하다고 판정했다가 뒤집었다.** 근거와 반증을 모두 남긴다.

fixture: project `CLAUDE.md` 에 `BANANA-STALE` 마커를 심고, SessionStart 훅이 그 파일을
`CHERRY-FRESH` 로 덮어쓰게 한 뒤 `claude -p` 로 **세션이 무엇을 읽는지** 관찰.

| # | 훅 모드 | 훅이 쓰는 데 걸린 시간 | 세션이 읽은 내용 | 디스크 최종 |
|---|---|---|---|---|
| 1 | 동기 | 즉시(`printf`, ~10ms) | **CHERRY-FRESH** | CHERRY-FRESH |
| 2 | `async: true` | 즉시 | BANANA-STALE | CHERRY-FRESH |
| 3 | 동기 | **`sleep 2` 후** 쓰기 | **BANANA-STALE** | CHERRY-FRESH |
| 4 | 동기, 실제 훅 설정 + 실제 pull(user-level) | ~0.5s | **BANANA-STALE** | CHERRY-FRESH |

실험 1·2 만 보고 "동기 훅은 CLAUDE.md 로드보다 먼저 끝난다"고 결론냈는데, **실험 3 이 그걸
반증한다**: 동기인데도 딜레이만 넣으면 진다. 실험 4 는 실제 훅 설정·실제 git pull 로 같은 결과다
(훅 실행 로그로 훅이 정상 실행·pull 성공까지 확인했는데도 세션은 옛 내용을 읽었다).

**따라서 CLAUDE.md 로드는 SessionStart 훅과 병렬로 경합한다.** 동기 전환이 이기게 해주는 게 아니라,
**즉시 끝나는 훅만 우연히 이긴다.** 경합 창이 수십 ms 수준이라 네트워크 pull 은 구조적으로 진다.

→ **C 철회.** 동기로 바꾸면 세션 시작만 붙잡고 약속한 이득은 없다. `async: true` 를 유지한다.
`README.md:444` 의 "CLAUDE.md·skill 문서 등 컨텍스트 주입분은 다음 세션부터" 서술은 **그대로 참**이며,
왜 동기로도 못 고치는지를 덧붙인다.

**함께 철회되는 것**: `matcher: "startup|resume|clear"`. 그 근거는 "동기 pull 이 compact 마다 세션을
멈춘다"였는데 동기를 안 하므로 사라졌다. matcher 자체는 동작함을 실측했으나(아래 표), 요청 범위 밖
동작 변경이라 넣지 않는다(§3-4).

| matcher | startup 세션에서 |
|---|---|
| `"startup"` | 실행됨 |
| `"compact"` | 실행 안 됨 |
| `"startup\|resume\|clear"` | 실행됨 |
| `"resume\|compact"` | 실행 안 됨 |

## `InstructionsLoaded` 는 대안이 아니다 (✅확실 — CLI 바이너리 원문)

description 원문: *"This hook is observability-only and does not support blocking."* ·
*"Exit code 0 - command completes successfully · Other exit codes - show stderr to user only"*.
호출부(`executeInstructionsLoadedHooks`)는 **로드가 끝난 파일 목록을 순회하며 `await` 없이** 쏜다.
사후 통지라 pull→재주입 용도로 쓸 수 없다.

## 구현 방식 — 인라인 체인을 `scripts/session-start-pull.sh` 로 분리

hang 방어 4종 + 폴링 워치독을 넣으면 인라인 체인이 ~1100자 JSON 문자열이 된다. 다음 이유로 **셸
스크립트 파일**로 뺀다:

- **node 의존을 이 경로에 들이지 않는다.** 이 훅은 *자기 자신의 업데이트 배포 채널*이라(PR #117 이
  지목한 실패 모드) node 부재·throw 로 죽으면 모든 머신이 조용히 업데이트를 멈춘다. `sh` 는 현재
  체인도 이미 요구하므로 **새 의존이 아니다**(README: Windows 는 Git Bash 필수).
- **복사할 원본이 이미 있다.** `install-hooks.sh:66-88` 의 post-checkout 본문이 정확히 같은 문제를
  이미 푼 검증된 셸이다 — 발명이 아니라 미러링.
- **`settings.json` 편집이 한 줄로 줄어든다.** 같은 파일을 통째로 재포맷 중인
  `settings-fmt-plan-ignore` worktree 와의 텍스트 충돌면이 최소화된다.
- 기존 테스트 `scripts/session-start-pull.test.js` 는 파일명이 이미 이 스크립트를 가리키고,
  `spawnSync('sh', ['-c', COMMAND])` 로 체인을 fixture HOME 에 실행한다 — **COMMAND 추출부만** 바꾸면
  9개 케이스가 그대로 회귀 커버로 남는다.

**`.js` 가 아니라 `.sh` 인 이유**(이 repo 훅 진입점은 전부 `node ~/.claude/scripts/*.js`): 위 첫
bullet 하나 때문이다. 다른 훅은 죽어도 그 기능만 잃지만, 이 훅이 죽으면 **고칠 방법이 배달되지 않는다**.

## 타임아웃 예산 (실측 기반)

훅은 async 로 남지만 상한은 여전히 필요하다 — 하니스 timeout 까지 매달리면 그 세션 내내 고아
git/ssh 가 돈다. 실측해서 잡았다:

- **정상 경로 실측 = 521 / 554 / 712 ms** (이 repo, 실제 origin, 이미 최신 3회). 즉 평상시
  세션 시작 지연은 **~0.6초**다.
- **Git Bash 의 `sleep 0.2` 는 실제 ~235ms** (프로세스 spawn 오버헤드 — 실측). post-checkout 식
  `100회` 루프는 명목 20s 가 아니라 **실제 ~23.5s** 다. 워치독 상한을 iteration 수로만 잡으면
  Windows 에서 조용히 초과한다.
- → 워치독은 **wall-clock 8s**(`date +%s` 마감 — iteration 카운트 아님), `CLAUDE_AUTOPULL_TIMEOUT`
  으로 주입 가능. 하니스 `timeout` **15s**. 워치독이 하니스보다 먼저 작동해야 고아가 안 남는다.
- `ConnectTimeout=10` · `http.lowSpeedTime=10` 이 흔한 실패는 워치독 전에 스스로 끊는다.
- async 라 이 시간이 세션 시작을 막지는 않는다. 상한의 목적은 **고아 프로세스 수명 제한**이다.

**Git Bash 워치독 원시 요소 실측** (`sleep 0.2` · `kill -0` · `kill` · `wait`): 전부 동작,
60s 자식을 상한에서 죽이고 `rc=143`(SIGTERM), **직접 자식은 고아 없음** 확인. 다만 MSYS `kill` 이
`git-remote-https.exe`·`ssh.exe` **손자**까지 죽이는지는 ❌미확인 — Acceptance 에서 프로세스 목록으로
관찰하고, 확인 못 하면 "고아 없음"을 단정하지 않는다.

## 테스트가 매달릴 수 있다 (CI 정지 위험 — 반드시 같이 고친다)

`session-start-pull.test.js:58-64` 의 `runChain` 은 `spawnSync('sh', ['-c', COMMAND])` 를
**stdout 파이프 + timeout 미지정**으로 돈다. 백그라운드 pull(`&`)을 넣으면 그 자식이 파이프를
물고 있어 `spawnSync` 가 자식 종료까지 반환하지 않는다 — 테스트가 매달리고 `lint.yml:63` 이
**CI 를 통째로 멈춘다**. `install-hooks.sh:78` 이 `>/dev/null 2>&1 </dev/null &` 로 stdio 를
끊어둔 것이 정확히 이 이유다.
→ 스크립트도 같은 stdio 분리를 하고, **테스트에도 `timeout` 을 건다**(방어 이중화).

## 테스트의 COMMAND 추출 계약이 깨진다

`session-start-pull.test.js:21-22` 는 `settings.json` 의 `[0].hooks[0].command` 를 꺼내
`sh -c` 로 돌리고, `HOME` 만 fixture 로 갈아끼워 격리한다. command 가
`sh ~/.claude/scripts/session-start-pull.sh` 가 되면 `~` 가 **fixture HOME** 으로 확장돼
**존재하지 않는 스크립트**를 가리킨다.
→ **fixture HOME 에 `.claude/scripts/session-start-pull.sh` 를 repo 에서 복사해 두고,
`settings.json` 의 실제 command 를 그대로 spawn 한다**(리뷰 B4 안 채택 — 내가 먼저 적었던
"스크립트를 직접 실행" 안보다 낫다). 그래야 *경로가 맞는지*까지 계속 검증된다 — 이 테스트의 존재
이유(`session-start-pull.test.js:2-8`: settings 문자열이 깨지면 전 머신이 조용히 멈춘다)가 보존된다.
더해 "settings.json 이 참조하는 스크립트가 repo 에 실존" 단언 1개를 별도로 둔다.

## hook 실행 순서 — 병렬이다 (실측으로 앞선 가정을 폐기)

**앞서 "pull(hooks[0]) → brief(hooks[1]) 순서라 신호 N 정확도가 오른다"고 적었던 것은 거짓이다.**
같은 그룹에 2초짜리 훅과 즉시 훅을 넣고 타임스탬프를 찍어보니:

```
groupA-first  start 1788496434621
groupA-second start 1788496434621   ← 같은 ms 에 시작
groupA-second end   1788496434643   ← first(2s) 가 끝나기 전에 종료
```

**같은 그룹의 훅은 동시에 돈다.** 배열 순서·그룹 분리 어느 쪽으로도 "pull 을 brief 보다 먼저"를
보장할 수 없다(별도 그룹인 `MATCHER-startup` 이 index 0 그룹보다 12ms **먼저** 시작하기도 했다).

귀결 두 가지:
- **좋은 쪽** — 세션 시작 지연은 훅들의 *합*이 아니라 **최댓값**이다. pull 0.6s 는 다른 동기 훅과
  겹쳐 흡수된다.
- **나쁜 쪽** — 신호 N 은 pull 과 **race** 한다(pull 전/후 상태를 비결정적으로 읽음). 이건 async 인
  지금도 있는 race 이고 이번 변경이 없애지 못한다 — 개선이 아니라 **현상 유지**로 정정한다.
  근본 해결은 pull 을 `session-brief.js` 안으로 합치는 것뿐이라 `# Deferred` 로 넘긴다.

신호 N 은 존치한다 — pull 체인은 여전히 *왜 못 했는지*(diverged·detached·dirty-overlap)를 말하지 못한다.

## 워치독은 `fetch` 만 감싼다 (merge 중 kill 금지)

`install-hooks.sh:77-85` 는 `pull`(fetch+merge) 전체를 워치독으로 감싼다. 그 형태를 그대로
가져오면 **ff-merge 가 index/worktree 를 갱신하는 도중 TERM 이 떨어질 수 있고**, `.git/index.lock`
잔존 + 부분 체크아웃(스크립트 절반만 새 버전)이 가능하다. 잔존 lock 은 이후 모든 pull 을 무음
실패시킨다 — **이 plan 이 없애려는 "조용히 안 도는" 상태를 스스로 만드는 것**이다. 동기 전환으로
발화 빈도가 오르므로 확률도 같이 오른다.

→ 두 단계로 쪼갠다: `git fetch origin main`(**워치독 대상 — 네트워크**) → 성공 시
`git merge --ff-only FETCH_HEAD`(**로컬, 워치독 없음**). kill 대상이 항상 fetch 라 index/worktree 를
건드리지 않는다. `session-brief.js:288-289` 가 기록한 "pull 은 fetch 를 먼저 하고 merge 만 거부한다"
성질과도 정합적이라 신호 N 의 전제가 안 깨진다.

## 워치독 상한은 iteration 이 아니라 wall-clock

`sleep 0.2` 는 Windows Git Bash 에서 실제 **235ms**(실측). iteration 카운트로 상한을 잡으면
플랫폼마다 상한이 달라지고 Windows 에서 ~18~22% 초과한다. → `date +%s` 기준 **wall-clock 마감**으로
잡는다. 폴링 간격의 오차는 상한에 영향을 주지 않고 granularity 에만 영향을 준다.

상한 값은 env 로 주입 가능하게 둔다(`CLAUDE_AUTOPULL_TIMEOUT`) — 테스트가 1초로 끝나고, 사용자에게
튜닝 레버가 생긴다.

## 즉시 rollback 레버 — 파일 스위치를 추가한다

이 훅은 **자기 배포 채널**이라 revert 커밋은 "고장난 그 pull 이 돌아야" 도달한다. 즉 코드 revert 는
즉시 레버가 아니다. `CLAUDE_AUTOPULL_OFF=1`(env)은 셸 launch 에서만 확실하다.
→ `~/.claude/.autopull-off` **파일이 존재하면 첫 줄에서 exit 0**. GUI 실행 사용자도 파일 하나로 끌 수
있다. 호출부도 fail-open 형태로 못박는다:
`[ -r ~/.claude/scripts/session-start-pull.sh ] && sh ~/.claude/scripts/session-start-pull.sh; true`
— 파일이 없거나 못 읽어도 세션은 열린다(exec bit 비의존).

## 하니스 fail-open 이 최악을 규정한다

훅이 timeout 되면 하니스는 `"<Event> hook timed out — output discarded"` 경고 후 **세션을 계속
연다**. 즉 동기 전환의 최악은 "세션이 안 열림"이 아니라 "세션 시작이 상한만큼 느려지고 경고가 뜸"이다.
이 사실이 C 의 위험도를 크게 낮춘다.

## 스크립트 분리(A안)를 재채택하는 이유

선행 plan `pull-hook-skip-reason:162-165` 는 같은 "훅 본문을 `scripts/` 로 분리"를 **폐기**했다.
폐기 사유는 "체인은 판정을 안 하고 시도만 하므로 **분리할 로직 자체가 없다**"였다. 이번엔 B 로
hang 방어 4종 + 워치독 + fetch/merge 분리라는 **실체가 생긴다** — 폐기 전제가 사라졌으므로 재채택한다.
(§10: 뒤집는 이유를 남겨야 다음 세션이 되돌리지 않는다.)

## 기존 결정과의 충돌 처리

`wiki/pages/decision/git-hook-network-safety.md` 는 "`settings.json` 의 SessionStart 훅에는 hang 문제가
없다 — 하니스가 `async:true`+`timeout` 으로 감싸기 때문"을 확정 기록으로 두고 있다. C 로 **그 전제가
무효화**되므로 같은 브랜치에서 갱신한다(그 페이지가 스스로 "동기로 바꾸면 §1 의 hang 방어를 그대로
미러링해야 한다"고 요구했고, B 가 정확히 그 미러링이다).

# Key Files

전수 영향범위 조사(Explore agent, `README`·`CLAUDE.md`·`wiki`·`docs`·`skills`·`agents`·`scripts`·
`plans`·`.github` 전체)로 확정한 목록이다. **갱신 필요(Y)** 와 **조건부**를 구분한다.

## 코드 (수정)
- `settings.json` — `hooks.SessionStart[0].hooks[0]`: command → 스크립트 호출, `async` 제거,
  `timeout` 30→15. **이 항목 하나만** 건드린다(`settings-fmt-plan-ignore` 충돌 최소화).
  **배열 index `[0].hooks[0]` 위치는 유지**해야 한다 — 테스트가 하드코딩으로 집는다
  (`plans/2026-08-31-session-fetch/…:91-92` 가 명문화한 계약).
- `scripts/session-start-pull.sh` — **신규**. 체인 + hang 방어 4종 + 폴링 워치독 + stdio 분리.
- `scripts/session-start-pull.test.js` — COMMAND 추출 계약 교체(위 Decisions), `spawnSync` 에
  `timeout` 추가, hang 방어·워치독 회귀 케이스 추가. 기존 9케이스 유지.
- `scripts/session-brief.js` — 주석·문구가 **"pull 훅은 async 라"** 를 전제로 쓰여 있다
  (`:2-13`, `:285-289`, `:296-349`). 동기 전환 후 거짓이 되므로 갱신. 특히 `:348-349` 폴백
  `"원인 미확인(마지막 pull 이 실패했거나 아직 안 돌았다)"` — 동기가 되면 **"아직 안 돌았다"는
  불가능**해지고 hang/타임아웃이 새 원인으로 들어온다(과거 C1 오진과 동형의 재발 지점).
- `skills/improve/improve.sh:35` — 주석 `"SessionStart git pull 은 파일 아니라 제외"` + grep 이
  `scripts/*.js` 만 본다. `.sh` 로 빼내면 주석이 거짓이 되고 실존 점검에서 새 스크립트가 누락된다.

## 미러링 원본 (읽기)
- `scripts/install-hooks.sh:51-95` — post-checkout main-autopull. hang 방어 3종 + 워치독 +
  `>/dev/null 2>&1 </dev/null &` stdio 분리의 정본.
- `scripts/session-fetch.js:40-90` — env 스크럽 범위·`credential.helper=`·`core.askPass=`·
  `GIT_ASKPASS=echo` 를 **쓰면 안 되는 이유**.

## 문서 (같은 브랜치 갱신 — acceptance)
- `README.md:444` — **최우선**. `async` 서술·"컨텍스트 주입분은 다음 세션부터"·타임아웃·skip 조건.
- `README.md:396` — `session-brief.js` 존재 이유가 "pull 훅은 async 라"로 서술돼 있다.
- `README.md:415·417` — post-checkout 과의 대비("hang 방어는 이쪽에만") 서술.
- `README.md:506·508·510` — kill-switch·rollback 절.
- `README.md:629 인근` — 트리에 **신규 스크립트 한 줄**(`dlc-doc-drift` 의 신규 파일 규칙).
- `wiki/pages/decision/git-hook-network-safety.md:15-16` — **"SessionStart 훅에는 hang 문제가
  없다(하니스가 async+timeout 으로 감싸므로)"** 가 이번 변경으로 정면 무효화. `:20-24` 의 처방
  범위도 "클라이언트 훅 한정"에서 넓혀야 한다.
- `wiki/index.md:45` — 위 페이지 요약 동반 갱신(§11).
- `.github/workflows/lint.yml:88` — `shellcheck scripts/*.sh` 가 신규 `.sh` 를 **자동 커버**한다
  (인라인 체인이 어떤 정적 lint 도 안 받던 사각이 닫힌다 — 분리의 부수 이득). `:43`·`:63` 의
  테스트 등록은 파일명 유지라 변경 불필요.

## 이력 (판단만, 수정 안 함)
- `plans/2026-07-22-pull-hook-skip-reason/…:133-136` — **이번 변경의 직접 선행 결정**. "(b) 동기
  전환을 택하면 `install-hooks.sh` 의 hang 방지 3종 + 워치독을 그대로 미러링해야 한다"고 이미
  적어둔 그 경로를 지금 실행하는 것이다.
- `plans/2026-07-05-main-autopull/…:67` — "SessionStart 는 async+하니스 timeout 이라 무관"이
  이번에 뒤집힌다. `:55` 의 "background pull 은 워킹트리 변형 race 라 채택 안 함" 판단도 재검토 대상.

# Blockers

(없음)

# Acceptance

1. **hang 방어 4종이 실제로 적용된다** — 스크립트가 `GIT_TERMINAL_PROMPT=0`,
   `GIT_SSH_COMMAND … BatchMode=yes -o ConnectTimeout=10`, `-c credential.helper=` ·
   `-c core.askPass=`, `-c http.lowSpeedLimit/lowSpeedTime` 을 건다. 검증: 스크립트 텍스트 단언
   (환경 의존 없이 결정적).
2. **워치독이 매달린 fetch 를 상한 안에 죽인다** — PATH 앞의 `git` stub 으로 fetch 를 매달리게 하고
   `CLAUDE_AUTOPULL_TIMEOUT` 를 주입해 결정적으로 관찰. 상한 안 종료 + exit 0 + HEAD 불변.
3. **기존 9케이스 회귀 유지** — `session-start-pull.test.js` 의 clean·무관dirty·충돌dirty·최신·
   main아님·kill-switch·rebase중·비git·홈없음이 전부 통과.
4. **워치독이 손자까지 거둔다** — git 이 띄우는 ssh·git-remote-https 에 해당하는 손자가 kill 이후
   계속 도는지 마커 mtime 으로 관찰(고아 없음).
5. **원격 추적 ref 가 갱신된다** — `pull` 을 `fetch`+`merge` 로 쪼갠 뒤에도
   `refs/remotes/origin/main` 이 갱신돼야 `session-brief` 의 밀림 신호가 계속 동작한다.
6. **fail-open 유지** — 모든 경로 exit 0. 스크립트 파일이 아예 없어도 세션을 막지 않는다.
7. **kill-switch 유지** — `CLAUDE_AUTOPULL_OFF=1` 과 `~/.claude/.autopull-off` 파일 둘 다
   **가장 먼저** 평가된다.
8. **테스트·CI 가 매달리지 않는다** — `node scripts/session-start-pull.test.js` 가 유한 시간에
   끝난다(백그라운드 pull 의 stdio 분리 + `spawnSync` timeout). CI 정지 회귀 락.
9. **`settings.json` 이 스크립트를 올바로 가리킨다** — command 문자열 단언(경로 오타 회귀 락).
   `[0].hooks[0]` 배열 위치 유지.
10. **`shellcheck scripts/*.sh` 통과** — 신규 스크립트가 CI 정적 검사를 통과한다.
11. **문서 동기화(같은 브랜치)** — `README.md`(444 훅 서술·415/417 post-checkout 대비·506/508/510
    rollback·트리에 신규 스크립트), `wiki/pages/decision/git-hook-network-safety.md` +
    `wiki/index.md`(async 전제는 유지되지만 "SessionStart 엔 hang 방어가 불필요하다"는 함의가
    바뀐다), `skills/improve/improve.sh` 주석·grep.
    **`session-brief.js` 는 갱신 대상에서 제외** — C 철회로 "pull 훅은 async 라" 전제가 그대로
    참이라 고칠 것이 없다(리뷰 지적은 동기 전환을 전제한 것이었다).

# Review Disposition

(비어 있음)

# Deferred

- `settings.json` 의 CLI 자동기록 키 분리 — `settings-fmt-plan-ignore` 에서 진행 중이라 이
  브랜치 범위 밖. 그게 닫히기 전까지는 origin 이 `settings.json` 을 건드릴 때마다 pull 이 거부되는
  경로가 남는다(이번 변경은 그 경로를 없애지 못한다 — **심각도 상**: 이 커밋의 배달 자체를 막는다).
- **신호 N 과 pull 의 race** — 훅이 병렬이라 `session-brief` 가 pull 전/후 상태를 비결정적으로
  읽는다(실측). async 인 현재도 있는 race 라 이번 변경이 악화시키지는 않지만 해소도 못 한다.
  근본 해결은 pull 을 `session-brief.js` 안으로 합치는 것 — 그러면 node 의존이 배포 채널에 들어오는
  트레이드오프가 생겨 별도 판단이 필요하다. 심각도 중(잡음).
- **`install-hooks.sh` post-checkout 도 같은 두 결함을 갖는다** — 워치독이 `pull` 전체를 감싸고
  (merge 중 kill 위험, B3 와 동형), iteration 카운트 상한이라 Windows 에서 명목 20s 가 실제 ~24s.
  이번 스코프 밖(그쪽은 발화 빈도가 낮아 위험도가 낮다). 심각도 중.
- 체인이 `main` 만 보고 `master` 를 skip 하는 정책 불일치(post-checkout 은 `main|master`).
  README 에 이미 명시. 심각도 하.
- **baseline failure (입증됨, 이번 변경과 무관)** — `python skills/jira-worklog/test_session_time.py`
  의 `test_malformed_cwd_does_not_abort` 가 실패한다:
  `classify_cwd("/repo/\0bad", ROOT, [ROOT]).kind` 가 `UNMATCHED` 이어야 하는데 `MAIN` 을 반환.
  **입증 방법**: 이 브랜치는 `skills/jira-worklog/` 를 전혀 건드리지 않았고(`git diff --name-only
  origin/main` 에 없음), `origin/main` 을 detached 워크트리로 따로 체크아웃해 돌려도 **동일하게
  실패**했다. 심각도 중(NUL 바이트 경로 방어 회귀로 보이나 이 브랜치 범위 밖).
- 체인이 `grep -qx main` 이라 `master` 인 머신은 skip 되는 정책 불일치(post-checkout 은 `main|master`).
  README 에 이미 명시돼 있고 이번 스코프 밖 — 심각도 하.

# Workflow Findings

- subagent(claude-code-guide)가 **자기모순인 결론**을 확신조로 반환했다(“SessionStart 는 CLAUDE.md
  주입 전에 실행된다” + “CLAUDE.md 는 SessionStart 전에 이미 읽힌다”). tool 호출 1회로 67k 토큰을
  쓴 점도 신호였다. 그대로 채택했으면 **C 를 불가능으로 판정하고 접었을 것** — 실제로는 가능하다.
  교훈: 외부 동작 판정은 agent 보고가 아니라 **실행·관찰**로 확정한다(§3-5 verification grounding).
