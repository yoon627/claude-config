---
title: fetch-hardening — 새 fetch 훅이 사용자 workspace 를 만지지 않게, 그리고 가드가 테스트로 지켜지게
status: done
started: 2026-08-31
updated: 2026-08-31
---

# Goal

`session-fetch` 훅을 push 한 뒤 도착한 code-reviewer 결과(**REQUEST CHANGES**, CONFIRMED Major 7건)를
닫는다. 핵심은 하나다 — **"fetch 만 하므로 사용자 것은 안 건드린다"가 실제로는 거짓이었다.**

# Progress

- 2026-08-31: 리뷰 7건을 재현·확정하고 전부 고쳤다. 고치기 전에 플래그가 실제로 듣는지 fixture 로 먼저
  확인했다(추측 금지) — `--no-write-fetch-head`·`--no-recurse-submodules`·`--no-auto-maintenance` +
  `-c core.hooksPath=<없는 경로>` 로 **ref 는 갱신되고, FETCH_HEAD 는 보존되며, repo 훅은 실행되지 않는다**.
- 2026-08-31: 리뷰가 지적한 "가드가 테스트로 안 지켜진다"(fetch 쪽 mutant 5/6 생존)를 mutation 으로
  재확인하고 회귀 테스트 8건을 추가했다. 재측정 결과 **8/8 KILLED**(FETCH_HEAD 보존·hooksPath·GIT_* 스크럽·
  kill switch·감시 repo 제외·실패 스탬프·스탬프 키 단위·submodule 재귀).
- 2026-08-31: 검증 — Windows: session-brief 74 / session-fetch **18** / session-start-pull 9 / 나머지 전부.
  WSL(node 18·git 2.43) 동일 통과. `node --check` 전 파일, settings.json JSON OK.

# Next

없음 — 머지·push 로 배포 완료.

# Decisions

- **`--no-write-fetch-head` 는 선택이 아니라 계약이다.** 사용자가 `git fetch origin feature` 해 둔 상태에서
  훅이 FETCH_HEAD 를 덮으면, 이어 친 `git merge FETCH_HEAD` 가 **다른 브랜치를 머지**한다(리뷰 실측).
- **스탬프 키는 remote 가 아니라 추적 ref 단위**(변경 — 이유: remote 단위면 `main` 세션이 찍은 스탬프가
  15분 안의 `feat` 세션을 skip 시켜 `origin/feat` 가 영영 갱신되지 않고, 브리프의 "fetch 안 함" 경고까지
  억제된다. 조용히 밀리는 상태를 없애려던 기능이 정확히 그 상태를 만든다). 키 생성은 브리프의
  `fetchStampName` 단일 소스를 공유한다 — 갈라지면 한쪽은 못 찾고 다른 쪽은 굶는다.
- **실패에도 스탬프를 찍는다**(변경 — 이유: 안 찍으면 닿지 않는 원격에 매 세션 재시도한다. 직전 구현은
  `FETCH_HEAD` 기준이라 우연히 backoff 가 있었는데 스탬프로 바꾸며 그 성질이 사라졌다).
- **브리프의 kill switch 를 이 훅도 존중한다.** README 가 `CLAUDE_BRIEF_CWD_OFF` 를 "즉시 차단 레버"로
  안내하는데 이 훅이 `currentRepoLine` 을 직접 불러 우회하고 있었다 — 문서화된 롤백 수단이 안 듣는 것은
  결함이다. 출력만 끄고 fetch 는 계속한다(둘은 다른 관심사).
- **`GIT_*` 스크럽은 `git rev-parse --local-env-vars` 전량**(변경 — 3개만 지우면 `GIT_COMMON_DIR` 로
  새어나가 무관한 repo 를 fetch 하고 거기 스탬프까지 남긴다. 리뷰 실측).
- **`packed-refs` 폴백 유지**(재처분 — 이유 정정): 원래 "없으면 아무 말도 안 한다"를 근거로 accept 했는데,
  실측은 `git gc` 가 30일 무-fetch repo 의 경고를 **침묵으로** 바꾼다는 것이었다. 즉 틀리는 방향이
  거짓 경고가 아니라 미탐이다 — 그래서 유지하되 근거 문장을 고쳤다. fetch 훅이 도는 repo 는 매 실행마다
  스탬프를 남기므로 이 폴백까지 오지 않는다.

# Key Files

- `scripts/session-fetch.js` — 하드닝 전량
- `scripts/session-brief.js` — `fetchStampName`·`samePath`·`GIT_LOCAL_ENV` export, 추적 ref full name 사용
- `scripts/session-fetch.test.js` — 회귀 8건(⑩~⑰) 추가
- `README.md` — 문서 drift 3건 정정(`-uall` 자기모순, 사라진 `GIT_ASKPASS` 안내, 하드닝 서술)

# Blockers

# Acceptance

1. 하드닝 플래그가 실제로 듣는다 — ref 갱신 ✅ / FETCH_HEAD 보존 ✅ / repo 훅 미실행 ✅ (fixture 실측)
2. mutation 8/8 KILLED (가드마다 회귀 테스트가 존재)
3. Windows + WSL 전 스위트 통과
4. `session-start-pull.test.js` 9건 불변
5. 문서와 코드가 어긋나지 않는다(리뷰가 짚은 3건 정정)

# Review Disposition

- FETCH_HEAD 덮어쓰기 (Major) — **fix**: `--no-write-fetch-head` + 테스트 ⑩.
- 스탬프 granularity 로 브랜치 굶주림 (Major) — **fix**: 추적 ref 단위 키 + 공유 함수 + 테스트 ⑪.
- kill switch 우회 (Major) — **fix**: `CLAUDE_SESSION_BRIEF_OFF`·`CLAUDE_BRIEF_CWD_OFF` 존중 + 테스트 ⑭.
- `git fetch` 가 repo 훅 실행 (Major) — **fix**: `-c core.hooksPath=<없는 경로>` + 테스트 ⑫.
- `GIT_*` 스크럽 부분적 (Major) — **fix**: local-env-vars 전량 + 테스트 ⑬.
- submodule 재귀·auto-maintenance (Major) — **fix**: `--no-recurse-submodules --no-auto-maintenance` + 테스트 ⑰.
- fetch 가드 mutant 5/6 생존 (Major) — **fix**: 8건 추가, 재측정 8/8 KILLED.
- negative caching 회귀 (Minor) — **fix**: 실패에도 스탬프 + 테스트 ⑯.
- `GIT_SSH_COMMAND` 통째 덮어쓰기 (Minor) — **fix**: 사용자 값 보존 후 옵션만 덧댐.
- `samePath` 미사용 (Minor) — **fix**: 브리프에서 export 해 공유.
- 예산 주석 산술 (Minor) — **fix**: 사전 호출 4회·fetch 8s 로 재계산(≈23s < 30s).
- `!before` 침묵 (Minor) — **fix**: 추적 ref 가 새로 생긴 경우도 보고.
- stdout 백스톱 부재 (Nit) — **fix**: 2s 타이머.
- 고아 ssh (Minor) — **accept**: `ConnectTimeout=10` 이 상한이고, 손자 프로세스를 죽이는 워치독은 이
  훅이 async 라 얻는 이득 대비 복잡도가 크다. wiki [[git-hook-network-safety]] 의 "orphan 없음"은
  동기 git 훅 요건이었다 — 여기는 하니스가 프로세스를 감싼다.
- 인증 경로 실측 미완 (Open) — **defer**: 샌드박스가 소켓을 막아 HTTPS 인증 경로를 측정하지 못했다.
  `-c credential.helper=` 로 helper 를 비우는 것이 GCM 을 확실히 막는지는 미확인. 실 원격에서 1회
  관찰이 필요하다(위험은 낮다 — 최악이 무음 실패다).
