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
- **`settings.json` 의 SessionStart 훅에는 이 문제가 없다** — 하니스가 `async:true`+`timeout` 으로 감싸 강제 종료하기 때문. **git 클라이언트 훅에는 그 안전망이 없다** — 스스로 상한을 걸어야 한다.
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

## 관련
- 위 hang 함정은 [[claude-codex-collaboration]] 의 code-review(codex+Claude 병행)가 사각지대(Major)로 파냄 — 사용자 환경(macOS+HTTPS)이 정확히 취약점이었고 단일 리뷰였으면 놓쳤을 것.
- 재귀 안전은 [[evidence-gate]] 대로 정적 단언이 아니라 격리 fixture 실측으로 확정.
