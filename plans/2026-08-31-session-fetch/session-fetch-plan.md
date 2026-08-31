---
title: session-fetch — 밀림을 판정할 근거(remote-tracking ref)를 실제로 갱신하고, 못 하면 그렇다고 말한다
status: in_progress
started: 2026-08-31
updated: 2026-08-31
---

# Goal

어제 넣은 신호 O 는 **캐시된 remote-tracking ref** 로만 밀림을 판정하는데, `~/.claude` 밖에는 그 ref 를
갱신할 주체가 없다. 그래서 "한 번도 fetch 하지 않은 채 밀린" 구간이 통째로 무음이다 — 이번 사건이
정확히 그랬다(실측: `refs/remotes/origin/dev` 가 2026-08-28 17:43 → 08-31 10:52 사이 얼어 있는 동안
원격은 37커밋 앞서 있었다. 그 2.7일 동안 O 는 밀림에 대해 아무 말도 못 했을 것이다).

두 축으로 막는다.
1. **(a) 갱신한다** — SessionStart 에서 세션이 열린 repo 를 async 로 `git fetch`(merge 안 함).
2. **(b) 못 갱신했으면 말한다** — fetch 가 오래됐으면 "N일째 fetch 안 함 — 밀렸는지 알 수 없다".
   (a) 가 있어도 오프라인·인증 실패·원격 불가 상황은 남는다. 침묵을 **명시적 모름**으로 바꾼다.

# Progress

- 2026-08-31: reflog 로 구멍을 실증하고 이 plan 을 열었다(위 Goal). 사용자가 (a)+(b)+README+교훈
  적립까지 승인했다.

- 2026-08-31: (a)+(b) 를 구현하고, **직전 리뷰가 이미 머지된 코드에서 찾은 CONFIRMED Major 5건도
  같이 고쳤다**(같은 파일이라 분리하면 결함 위에 기능을 얹게 된다). 그 5건: `-uall` 이 maxBuffer 를
  넘겨 미커밋 신호가 통째로 사라짐 / `-uall` 이 `venv/` 류로 상시 잡음 / 임의 repo 의 `core.fsmonitor`
  **명령 자동 실행**(실측 RAN) / `GIT_DIR` 상속이 `-C` 를 이겨 다른 repo 를 답함 / N 라벨 수정에
  재현 테스트 없음(mutant 생존).
- 2026-08-31: codex code 리뷰(high) — Critical 0 / Major 5 / Minor 5, 전부 반영. GIT_* 스크럽 누락,
  `GIT_ASKPASS=echo` 가 **프롬프트 문자열을 자격증명으로 되돌려주는** 문제, 최악 실행시간 41s > 훅
  timeout 30s(고아 프로세스), `FETCH_HEAD` 가 repo 전역이라 다른 remote fetch 로 거짓 신선, refspec
  미지정 시 `remote.<n>.fetch` 설정에 따라 **로컬 브랜치 ref 가 움직일 수 있음**.
- 2026-08-31: wiki `[[git-hook-network-safety]]` 를 읽고 빠진 처방 두 개를 마저 넣었다 —
  `ssh -oConnectTimeout=10`, `http.lowSpeedLimit/Time`. 그 페이지의 "네트워크는 async, 사용자에게
  보여야 할 판정은 동기로" 원칙에 맞게 출력 시점도 주석에 명시했다.
- 2026-08-31: 검증 — Windows: session-brief **74**, session-fetch **10**, session-start-pull 9(불변),
  나머지 단위테스트 전부 통과, `node --check` 전 파일, settings.json JSON·체인 index 0 불변, plan-lint 0.
  WSL(node v18.19.1/git 2.43): 74·10·9 동일 통과.
- 2026-08-31: 교훈 적립 — wiki `pages/decision/lesson-fix-scoped-to-one-repo.md` + `index.md`·`log.md`
  동기화, memory `fix-scope-beyond-one-repo.md` + `MEMORY.md` 인덱스 한 줄.
# Next

1. **`~/.claude` main 의 `settings.json` 로컬 변경 처리 방법을 사용자가 정해야 한다**(아래 Blockers).
   이 브랜치가 같은 파일을 건드리므로 그대로는 ff-merge 가 거부된다.
2. 그다음 ff-merge → push. push 후 다른 머신은 각자의 다음 SessionStart pull 로 받는다.
3. 대기 중인 code-reviewer(claude) 결과 반영.


# Decisions

- **fetch 만 하고 merge 하지 않는다.** 로컬 커밋·작업트리를 건드리지 않으므로 되돌릴 것이 없다.
  `~/.claude` 는 예외로 기존 pull 훅이 계속 담당한다(그쪽은 ff-only pull 이 규약).
- **async 로 돈다.** 세션 시작을 네트워크에 묶지 않는다. 대신 fetch 로 ref 가 움직였으면 그 훅이
  **직접 밀림 한 줄을 출력**한다 — 안 그러면 사용자는 한 세션 늦게 알게 된다.
- **판정 로직은 브리프에서 가져다 쓴다**(`currentRepoLine` export). 같은 문장을 두 곳에서 만들면
  갈라진다. 대신 `require.main === module` 가드를 넣어 require 가 브리프를 실행하지 않게 한다.
- **인증 프롬프트를 절대 띄우지 않는다** — `GIT_TERMINAL_PROMPT=0`, `GIT_ASKPASS=echo`,
  `GIT_SSH_COMMAND='ssh -oBatchMode=yes'`. 훅이 자격증명 입력을 기다리며 매달리는 것이 최악이다.
- **최근에 fetch 했으면 skip** — `.git/FETCH_HEAD` mtime 기준(기본 15분,
  `CLAUDE_SESSION_FETCH_MIN_MINUTES`). 세션을 자주 여는 사용이 원격을 두드리지 않게.
- **(b) 는 밀림 파트가 없을 때만 낸다.** 이미 "N커밋 뒤처짐"을 말하고 있으면 fetch 신선도는 잡음이다.
  침묵을 모름으로 바꾸는 것이 목적이지 줄을 늘리는 게 아니다.
- **kill switch 두 개** — `CLAUDE_SESSION_FETCH_OFF=1`(훅 자체), `CLAUDE_BRIEF_FETCH_DAYS`(임계).

# Key Files

- `scripts/session-brief.js` — (b) 파트 + `currentRepoLine` export + require.main 가드
- `scripts/session-fetch.js` — 신설. async fetch + 갱신 시 밀림 한 줄
- `scripts/hook-cwd.js` — 신설. hook stdin JSON 의 cwd 를 읽는 공유 모듈
- `settings.json` — `hooks.SessionStart[0].hooks` 에 async fetch 추가(**index 0 은 건드리지 않는다** —
  `session-start-pull.test.js:22` 가 `[0].hooks[0].command` 로 pull 체인을 집는다)
- `.github/workflows/lint.yml` — 새 스크립트를 `node --check` 와 단위테스트 목록에 등록
- `README.md` — 신호·훅 문서 + WSL worktree 한계 한 줄

# Blockers

- **`~/.claude` main 의 working tree 에 `settings.json` 미커밋 변경이 있다**(Orca 가 재주입한 Windows
  절대경로 — README:446 이 "push 전 `git diff` 로 확인하라"고 적어 둔 그 변경이다). 이 브랜치도
  `settings.json` 을 건드리므로 `git merge --ff-only` 가 "local changes would be overwritten" 으로
  거부한다. 사용자 파일이라 내가 임의로 버리거나 커밋하지 않는다. 선택지:
  (a) `git stash push settings.json` → 머지 → `git stash pop`(변경 영역이 달라 충돌 가능성은 낮다),
  (b) 그 변경을 버린다(Orca 가 다음 세션에 재주입하므로 실질 손실은 없을 가능성이 높다),
  (c) 커밋한다(**권하지 않음** — tracked 파일에 머신 절대경로가 들어가 멀티머신 ping-pong 재발).

# Acceptance

1. `node scripts/session-brief.test.js`·`session-fetch.test.js`·기존 단위테스트 전부 통과
2. fixture 로 실증: 로컬 bare repo 를 origin 으로 둔 clone 이 뒤처진 상태에서 훅을 돌리면
   remote-tracking ref 가 실제로 갱신되고, 밀림 한 줄이 출력된다(관찰)
3. fetch 가 오래된 repo 에서 브리프가 "N일째 fetch 안 함" 을 낸다. 밀림 파트가 있을 땐 안 낸다
4. 인증이 필요한 원격에서도 프롬프트 없이 즉시 실패하고 exit 0 (fail-open)
5. 최근 fetch 했으면 skip(원격 접근 0회)
6. `session-start-pull.test.js` 9건 불변(기존 pull 체인 회귀 없음)
7. README·lint.yml 갱신, `node --check` 통과
8. Windows + WSL 양쪽에서 테스트 통과

# Review Disposition

- `-uall` maxBuffer 로 신호 소실 (claude Major) — **fix**: `-unormal` + `maxBuffer 16MiB`.
- `-uall` 이 만든 상시 잡음 (claude Major) — **fix**: 디렉토리 항목 skip + 테스트 ⓞ16.
- `core.fsmonitor` 자동 실행 (codex→claude 실측 Major) — **fix**: 모든 git 호출에 `-c core.fsmonitor=`
  + 테스트 ⓞ17(평범한 `git status` 는 실행한다는 전제까지 단언해 vacuous test 방지).
- `GIT_DIR` 상속 (codex→claude 실측 Major) — **fix**: 두 스크립트 모두 스크럽 + 테스트 ⓞ18.
- N 라벨 mutant 생존 (claude Major) — **fix**: 테스트 ⓝ9 + ⓞ1 의 잘못된 주석 정정.
- `GIT_ASKPASS=echo` (codex Major) — **fix**: 제거하고 `credential.helper=`·`core.askPass=` 무력화.
  물어볼 경로 자체를 없앤다.
- 최악 실행시간 > 훅 timeout (codex Major) — **fix**: GIT_MS 5s→2s, FETCH_MS 20s→12s(합 ≈21s < 30s).
- `FETCH_HEAD` 가 repo 전역 (codex Major) — **fix**: remote 별 스탬프 `.git/claude-fetch-<remote>` 로
  교체 + 회귀 테스트 ①b(다른 remote 를 fetch 해도 origin 은 건너뛰지 않는다).
- refspec 미지정 시 로컬 ref 이동 가능 (codex Major) — **fix**: `+<remoteref>:<trackingRef>` 명시.
- kill switch 가 stdin 대기 비용을 뭄 (claude Minor) — **fix**: 검사를 `readHookCwd` 앞으로.
- stdout write 콜백 백스톱 부재 (claude/codex Minor) — **fix**: 2s 타이머.
- `ageFile` DST 플레이크 (claude Minor) — **fix**: 달력 연산으로 교체.
- `packed-refs` mtime 부정확 (codex Minor) — **accept**: 스탬프·ref 파일 다음의 최후 폴백일 뿐이고,
  없으면 아무 말도 안 한다(거짓 경고를 내지 않는 쪽으로 기울였다).
- 접힌 디렉토리 안의 오래된 파일 미탐 (codex Minor) — **accept(문서화)**: `-uall` 의 잡음·소실과
  맞바꾼 의도된 사각. README·코드 주석·테스트 ⓞ16 에 명시.
- 동시 세션 fetch 경합 (codex Minor) — **accept**: git 이 ref 를 잠그고, 실패는 무음 fail-open 이며,
  스탬프가 중복 실행을 줄인다. 락을 새로 만들 만한 피해가 없다.
- ref 가 움직여도 낼 말이 없을 수 있음 (codex Minor) — **fix(문구)**: 계약 주석을 "움직였고 그래서 할
  말이 생겼을 때"로 정정.
- README 훅 개수 "2개 + orca" (codex Minor) — **fix**: 3개로.
