---
title: session-test-fixtures — session-* 테스트의 fixture git 프로세스 줄이기
status: in_progress
started: 2026-10-07
updated: 2026-10-07
---

# Goal
scripts/session-start-pull.test.js · session-brief.test.js · session-fetch.test.js 가 fixture 를 만들며 띄우는 git 프로세스를 줄여 테스트 시간을 줄인다. 판정·커버리지 불변.

# Intent
- Problem: verify-speed `# Deferred` 2번. 단독 실측(preload 로 child_process 계측, 2026-10-07): 전체 / 테스트 쪽 git — fetch 17초 / 252회 11.3초, start-pull 91초 / 871회 50.5초(push 110회 23.6초, config 222회), brief 57초 / 1149회 31.2초(config 331회). 훅 실행(테스트 대상) 68초는 줄일 수 없다. 부하가 겹치면 프로세스 비용이 수 배로 커져(이전 측정 brief 179초) 절감도 그만큼 커진다.
- Constraints: 판정·커버리지 불변(케이스 수·단언 그대로). 훅이 보는 repo 상태(설정·ref·작업트리)는 지금과 같아야 한다. 시간 배수 decision(wiki session-hook-test-time-scale)은 건드리지 않는다. 새 공유 모듈은 만들지 않는다 — verify.sh SLOW_TESTS 트리거와 각 파일 helper 관례를 늘리지 않게 파일마다 몇 줄 helper.
- Out of scope: 훅 스크립트 자체, session-brief 의 케이스별 시나리오 repo(behindRepo 등 — 케이스마다 모양이 달라 템플릿 이득이 작다), verify-speed `# Deferred` 의 다른 항목.
- Open questions: 없음 — 측정·설계 공백은 plan-reviewer 처분으로 닫았다.
- 분할: 없음 — 세 파일이 같은 기법(설정 직접 쓰기·템플릿 복사)을 쓰고 합쳐 ~80줄이라 나누면 리뷰·머지 고정비만 는다. 각 파일 변경은 독립이지만 하나의 목적이다.

# Progress
- 2026-10-07: 탐색·계측(위 Problem 수치). session-start-pull.sh 는 clean 판정을 porcelain `merge --ff-only` 로 해 복사본의 stat 어긋남이 판정을 바꾸지 않는다(시작 때 index refresh).

- 2026-10-07: plan-reviewer CONDITIONAL → 처분 반영. baseline wall-clock(단독 2회): fetch 17.2/16.3초, start-pull 87.7/89.7초, brief 57.6/57.2초. 구현 후 1회: fetch 11.9초(18 통과), start-pull 49.0초(38), brief 52.7초(95). config 동등성 probe: init·clone 모두 바이트 동일, 복사+origin 교체 config 가 새 clone 과 바이트 동일, 템플릿 경로 흔적 없음, status clean.

- 2026-10-07: code-reviewer(+codex) NEEDS DISCUSSION — 확정 Critical/Major 0, 조건부 2건·Nit 반영(복사 filter·verbatimSymlinks·주석). 정식 측정(단독 2회): fetch 12.1/12.9초(전 17.2/16.3), start-pull 49.1/51.7초(전 87.7/89.7), brief 52.2/51.2초(전 57.6/57.2) — 합계 약 163→115초, 케이스 수 동일. `bash scripts/verify.sh changed` ALL PASS(skip 없음, 158초). Acceptance 1~4 충족 → DONE.

# Next
- 머지(사용자 선택). 남은 verify-speed `# Deferred`: native-overlap-lint 헤더만 검사, watchdog·polling 프로세스 수(낮음).

# Decisions
- wiki 조회: decision/session-hook-test-time-scale 걸림 — 따른다(시간 배수 그대로).
- (A) 세 파일의 `git config user.email/user.name/commit.gpgsign` 호출(660회)을 `.git/config` 에 같은 키를 직접 덧붙이는 helper 로 바꾼다. 디스크 결과가 같다(검증: 바꾼 뒤 `git config --list --local` 비교를 구현 중 1회 확인).
- (B) session-fetch `cloned()`: 같은 모양(remote 에 base 커밋 1개 + clone)을 처음 한 번 만들고 케이스마다 `fs.cpSync` 로 복사, work 의 origin url 을 새 remote 경로로 바꾼다.
- (C) session-start-pull `makeHome(opts)`: 옵션 조합(withScript·remoteCommits·record)별로 템플릿 home 을 한 번 만들어 캐시하고 케이스마다 복사, repo·other 의 origin url 을 새 home 경로로 바꾼다. 반환하는 commits sha 는 템플릿과 같다(케이스 간 sha 가 같아지지만 home 끼리 독립이라 단언에 영향 없음 — 구현 중 sha 를 케이스 간 비교하는 단언이 없는지 확인).
- ⚠️ url 교체 방식 — 프로세스 0개(텍스트 치환)와 형식 안전(git 이 쓰는 escape 규칙: Windows 경로의 `\` 가 `\\` 로 저장)이 상충 — `git config remote.origin.url <새 경로>` 1회를 택한다(repo 당 1프로세스, escape 를 git 에 맡김).
- url 교체는 `git config remote.origin.url` 로 확정. 교체 직후 복사본 `.git/config` 텍스트에 템플릿 디렉터리 basename(mkdtemp 접미사)이 없는지 helper 안에서 상시 assert(0프로세스) — 교체 누락이 템플릿 origin 오염(start-pull 의 pushRecord·(d)·(e) 가 템플릿 bare 에 push)으로 조용히 번지는 대신 즉시 실패하게. start-pull 은 repo·other 둘 다.
- 템플릿 자체를 케이스에 넘기지 않는다(첫 케이스 포함) — 모든 케이스가 fixture 를 변형한다(rmSync·dirty 파일·push). brief 의 공유 `blankRepo` 처럼 공유하지 않는 이유가 이것.
- 반환 commits 는 `[...commits]` 사본. 캐시 키는 기본값을 채운 `{withScript, remoteCommits, record}` 를 JSON 으로(record 0 과 'tip' 구분).
- `cpSync` 는 기본 옵션(preserveTimestamps false) — mtime 이 복사 시각이 돼 지금의 clone 직후와 같다.
- (A) 적용 범위: 일반 repo 의 `.git/config` 만(`.git` 이 디렉터리인 곳). 현재 호출부 brief initRepo, fetch initRepo·cloned·⑰ superwork, start-pull makeHome 은 모두 일반 repo. fetch ⑰ 의 work 는 지금 gpgsign 을 설정하지 않으므로 그 자리는 user 2키만 쓴다(설정 불변).
- 기각: env(`GIT_AUTHOR_*`·`GIT_CONFIG_COUNT`)로 user/gpgsign 주기 — 훅이 보는 repo 설정이 바뀌고 start-pull runChain 이 GIT_CONFIG_COUNT 를 일부러 지운다. 상대 origin url(`../origin.git`) — 0프로세스지만 훅이 보는 설정이 달라진다. url 텍스트 치환 — clone 이 저장한 경로 표기와 어긋나면 0건 매칭으로 조용히 통과. `hooks/*.sample` 빼기·`init --template=` — 훅이 보는 repo 모양이 달라져 보류.
- 커밋 단위: 1개 — 같은 목적(테스트 fixture 프로세스 감소).

# Acceptance
1. 세 테스트가 통과하고 케이스 수가 같다 — `node scripts/<t>.test.js` 의 "N tests passed" 가 전후 같다(fetch 18, start-pull 38, brief 95).
2. 파일별 테스트 wall-clock 이 준다 — 단독 실행, 전후 각 2회(cpSync 비용 포함). 보조로 preload 계측의 git 호출 수.
3. 템플릿 복사본이 원본과 같은 설정을 갖고(경로만 다름) 템플릿 경로를 가리키지 않는다 — helper 상시 assert + 구현 중 `git config --list --local` 비교 1회.
4. `bash scripts/verify.sh changed` ALL PASS(대상 테스트가 바뀌어 [slow] 로 건너뛰지 않고 돈다).

# Review Disposition
- ⚠️ url 교체 방식 self-flag — resolved (git config + 템플릿 경로 부재 상시 assert).
- [강] url 교체 누락 = 템플릿 오염 — fix (상시 assert, repo·other 둘 다, 템플릿 미배포).
- [강] 계측이 cpSync 를 안 잡아 이득 과대 — fix (Acceptance 2 를 wall-clock 전후 2회로).
- [강] (A) 적용 범위·⑰ gpgsign — fix (범위 명시, ⑰ 은 user 2키만).
- [약] commits 사본·캐시 키 정규화·preserveTimestamps 기본·기각안 기록·Open questions — fix.
- [code-review Major PLAUSIBLE] 전역 core.fsmonitor=true(Mac)면 템플릿 .git 의 데몬 소켓에서 cpSync 실패 — fix (복사 filter 로 `fsmonitor--daemon*` 제외; 이전에도 fixture 마다 데몬이 떴으므로 훅이 보는 상태 동일. probe: 디렉터리·ipc 제외 확인).
- [code-review Minor PLAUSIBLE] 상대 symlink 가 템플릿 절대 링크로 바뀜 — fix (`verbatimSymlinks: true`, probe 로 상대 유지 확인).
- [code-review Nit] "git config 세 번" 주석이 변경 경위·⑰ 에 부정확 — fix (제약만 한 줄).
- [code-review Nit] start-pull 의 url 교체가 fetch 의 pointOrigin 과 모양이 다름 — wontfix (파일마다 호출 1곳, 동작 동일).
- [약] Linux/macOS cpSync 미측정 — defer (CI 가 Linux 에서 세 테스트를 돈다; 기능 차이는 CI 통과로 확인).

# Key Files
- scripts/session-fetch.test.js — initRepo·cloned
- scripts/session-start-pull.test.js — makeHome
- scripts/session-brief.test.js — initRepo(config 직접 쓰기만)

# Blockers
