---
title: git-hook-network-safety
category: decision
created: 2026-07-16
updated: 2026-07-16
sources: [PR #82, 커밋 888ec8e, plans/2026-07-05-main-autopull]
---

# git-hook-network-safety — git 훅에서 네트워크/git 작업 시 hang·재귀 안전

main-autopull(post-checkout 자동 ff, PR #82)에서 도출. git 클라이언트 훅 안에서 `git pull` 같은 네트워크·git 작업을 할 때의 두 비자명한 함정과 대응.

## 1. 훅은 동기·무timeout — checkout 을 hang 시킬 수 있다
git `post-checkout`(및 대부분의 클라이언트 훅)은 **동기 실행**이고 git 은 훅이 끝날 때까지 무한 대기하며 **자체 timeout 수단이 없다**. 훅 안의 `git pull` 이 죽은 네트워크(DNS/TCP/TLS connect blackhole)나 자격증명 프롬프트에 걸리면 `git checkout` 이 수 초~수십 초 hang 된다(브랜치 전환은 이미 끝났고 pull 만 매달림 — Ctrl-C 로 회복은 되나 "never blocks" 계약 파손).
- ~~**`settings.json` 의 SessionStart 훅에는 이 문제가 없다** — 하니스가 `async:true`+`timeout` 으로 감싸 강제 종료하기 때문~~ → **2026-09-04 정정: 과했다.** 하니스 timeout 은 **훅 프로세스**를 죽일 뿐 그 훅이 띄운 **자손을 거두지 않는다**. 훅이 `git fetch` 를 돌리면 하니스가 훅을 죽인 뒤에도 `git`·`ssh`·`git-remote-https` 가 계속 돈다(실측: 직접 자식만 kill 하면 손자가 살아남는다). 즉 SessionStart 훅도 **자기 상한과 프로세스 그룹 kill 을 스스로 가져야** 한다 — 하니스 안전망은 사용자를 안 막아줄 뿐 자원 누수는 막지 못한다. `scripts/session-start-pull.sh` 가 그 처방(`set -m` + `kill -- -$pid` + wall-clock 워치독 + PROMPT=0/BatchMode/ConnectTimeout/low-speed)을 갖는 이유다. **그룹 kill 의 이식성 한계(2026-09-04 실측)**: bash(Git Bash·macOS)에서는 `set -m` 이 백그라운드 job 을 자기 프로세스 그룹에 두어 `kill -- -$pid` 가 손자까지 거둔다. 반면 **dash**(Linux 의 `/bin/sh`)는 tty 없이 job control 을 켜지 않아 그룹 kill 이 거부된다 — 그래서 처방은 `그룹 kill → 직접 kill 폴백 → 유예 후 SIGKILL 승격` 3단이어야 하고, 그룹 kill 하나에만 기대면 안 된다. **git 클라이언트 훅에는 그 안전망조차 없다** — 사용자를 직접 막으므로 더 급할 뿐, 상한이 필요한 것은 양쪽 다 같다.
- **다만 `async:true` 는 공짜가 아니다 (2026-08-04 추가)** — async 훅의 stdout 은 **첫 턴 이후에야 도달**한다(`scripts/session-brief.js` 상단 계약). 즉 hang 안전을 얻는 대신 **그 훅은 세션 시작 시점에 사용자에게 말할 수 없다**. 그래서 "자동 pull 이 왜 밀렸나" 같은 *시작 시점에 알아야 하는* 정보는 async 훅에 두면 안 되고, 동기 훅(`session-brief`)이 로컬 상태로 판정해 말해야 한다. **일반화: 네트워크는 async 로, 사용자에게 보여야 할 판정은 동기로 나눈다.** 동기로 바꿔 해결하려 들면 위 hang 안전망을 스스로 재구현해야 한다(그게 이 페이지의 §1).
- **동기 전환으로 "그 세션의 CLAUDE.md 를 최신화"하려는 시도는 성립하지 않는다 (2026-09-04 실측 4케이스).** CLAUDE.md·skill 문서 로드는 SessionStart 훅과 **순서가 아니라 경합**이다. 즉시 끝나는 훅(`printf`)은 이겨서 새 내용이 읽히지만, 같은 동기 훅에 `sleep 2` 만 넣으면 옛 내용을 읽는다. 실제 훅 설정 + 실제 `git pull`(~0.6s)로도 옛 내용이었다(훅 실행·pull 성공 로그로 확인). 대안 후보였던 `InstructionsLoaded` 훅도 CLI 원문상 *observability-only, does not support blocking* 이고 로드가 끝난 파일 목록을 `await` 없이 순회하며 쏘는 **사후 통지**라 쓸 수 없다. → **repo 최신화의 이득은 다음 세션부터**라는 것이 구조적 사실이며, 동기 전환은 비용만 남긴다.
- **macOS 는 GNU `timeout(1)`/`gtimeout` 이 기본 부재** → `timeout 20 git pull` 식 래핑이 stock macOS 에서 dead. `http.lowSpeedLimit/Time` 은 *전송 중 stall* 만 끊고 connect 단계는 못 막으며 SSH 엔 무의미.

**대응(병행)**:
- **poll 워치독** — pull 을 백그라운드(`&`, stdio 는 `/dev/null` 로 분리해 caller 파이프 미점유)로 돌리고 `kill -0` 로 폴링, 상한(≈20s) 초과 시 kill. `timeout(1)` 비의존·orphan 없음. (서브셸 `( sleep 20; kill )&` 은 kill 시 자식 `sleep` 이 orphan 되어 caller 의 stdout 파이프를 20s 붙잡으니 피한다.)
- `GIT_TERMINAL_PROMPT=0` + `git -c core.askpass=` — 대화형 인증 프롬프트 hang 차단.
- `GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh} -o BatchMode=yes -o ConnectTimeout=10"` — SSH connect·auth 상한.
- `http.lowSpeedLimit/Time` — HTTP 전송 stall 상한.
- 훅은 **항상 `exit 0`**(checkout 을 막지 않음) + **kill-switch env**(파일 삭제 없이 무력화 — 클라이언트 훅은 비추적·머신별 분산 설치라 소스 revert 로 안 지워짐 → env kill-switch 가 사실상 유일한 rollback).

## 2. ff-merge 는 post-checkout 을 재발동시키지 않는다 (재귀 없음)
훅 안에서 `git pull --ff-only` 를 해도 그 pull 의 **fast-forward 는 `post-checkout` 을 재발동시키지 않는다** — fast-forward 는 `post-merge` 계열을 발동시키는데 그 훅이 없으면 무동작. 상식적 우려("훅에서 pull → 그 pull 이 훅을 또 부름 → 무한 loop")는 기우. **실측 확정**([[evidence-gate]]): main checkout 시 내부 ff pull 이 post-checkout 을 재호출하지 않음(fire count = 명시 checkout 수).
- 일반화: 훅 안 git 작업의 재귀는 "그 작업이 발동시키는 훅 종류"로 판정. checkout→post-checkout, merge/pull-ff→post-merge, commit→post-commit. **같은 훅을 재발동시키는 작업만** 피하면 된다.

## 미결 — SessionStart pull 이 dirty tree 에서 거부되는 건 (2026-08-06)

> [!open] SessionStart pull 훅에 `--autostash` 를 넣을 것인가 — **결정 보류**(2026-08-06 사용자 판단).
> CLI 가 tracked `settings.json` 에 자동으로 쓰기 때문에 working tree 가 수시로 dirty 해지고, 자동 pull 이 `Your local changes to settings.json would be overwritten by merge` 로 거부된다(실측).
> 결정할 것은 둘이다 — **(a)** `--autostash` 도입 여부, **(b)** 도입 시 stash 재적용 **충돌을 어떻게 알릴지**. 지금 훅은 출력을 전부 죽이고 있어 충돌이 나도 조용하다. 알림 없이 (a) 만 도입하면 *"변경이 사라진 것처럼 보이는"* 새 실패 모드가 생긴다 — 위 §1 의 "네트워크는 async, 사용자에게 보여야 할 판정은 동기로" 와 같은 축의 문제다(async 훅은 시작 시점에 말할 수 없다).
> 조사·근거는 `plans/2026-08-05-settings-local-keys/`(PR #129, `status: done` — 그 plan 의 범위는 조사까지였고 이 결정만 남았다). 착수 시 운영 자산 변경이라 승인 후 wt→dlc.

## 관련
- 위 hang 함정은 [[claude-codex-collaboration]] 의 code-review(codex+Claude 병행)가 사각지대(Major)로 파냄 — 사용자 환경(macOS+HTTPS)이 정확히 취약점이었고 단일 리뷰였으면 놓쳤을 것.
- 재귀 안전은 [[evidence-gate]] 대로 정적 단언이 아니라 격리 fixture 실측으로 확정.
