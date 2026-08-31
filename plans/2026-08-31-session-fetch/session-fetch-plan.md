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

# Next

1. `scripts/hook-cwd.js` 추출(브리프·fetch 훅이 같은 stdin cwd 규약을 공유).
2. 브리프에 (b) 파트 추가 + `currentRepoLine` export(+`require.main` 가드).
3. `scripts/session-fetch.js` 신설 + `settings.json` 배선 + `lint.yml` 등록.
4. 테스트(두 파일) → 리뷰(code-reviewer + codex) → 검증(Windows·WSL) → 머지·push.
5. 교훈 적립(wiki lesson + MEMORY.md 인덱스 한 줄).

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
