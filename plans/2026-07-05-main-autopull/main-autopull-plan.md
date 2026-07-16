---
title: main-autopull — main 체크아웃/복귀 시 자동 최신화 (현행 SessionStart pull 검증 포함)
status: done
started: 2026-07-05
updated: 2026-07-05
---

# Goal
main/master 로 체크아웃되거나 세션이 main 으로 복귀할 때 로컬이 origin 최신을 자동 반영하게 한다 (사용자: "main 체크아웃 시 항상 git pull --rebase — 이미 돼 있을 수도 있는데 잘 작동하는지 모르겠다"). 현행 장치의 실동작 검증 + 빈 구간 보강.

# Progress
- 2026-07-05: Fable 계획 세션 — 현행 조사·설계 확정. 구현은 opus.
- 2026-07-16 (opus, 착수): worktree 진입·최신 main(40ebf96) ff·baseline 4 test green. Explore 완료(install-hooks.sh/.ps1·e SKILL 6단계 현행 read). **ff-only vs --rebase → 사용자 ff-only 확정**(§8 근거). ⓑ 착수조건(doc-slim 머지) 충족. dlc plan-review 착수.
- 2026-07-16 (opus, 구현 완료): dlc 전체 파이프라인 완료 — plan-review(codex+Claude CONDITIONAL→반영)→TDD Red→구현(install_hook 추출·post-checkout ⓐ·e SKILL ⓑ·test·lint.yml·README)→Green→code-review(codex+Claude, Major 3 전부 fix: hang→poll 워치독·브랜치대응·마이그레이션 검증)→simplify(stale timeout 참조 제거)→최종검증. **커밋 `a6c5aae`**(6 files +316/-20). 실측: install-hooks.test.js **16/16 PASS**·재귀 non-loop 실증·.sh≡.ps1 본문(41줄)·baseline 전건 PASS·bash -n/sh -n OK. **미검증(환경 한계)**: .ps1 실행(pwsh 부재→본문 parity+sh -n 로 대체)·실 hang timeout(재현 불가→poll 로직 검증). status: 구현 done, **머지 대기**.
- 2026-07-16 (opus, 머지 완료): 최신 origin/main(fa3f288, loop-ops #81·unknowns #80 반영) 위로 rebase — 충돌 2건(lint.yml·README) 양쪽 additive 유지로 해소, rebased 트리 전체 CI 등가 green(session-brief·usage-count 포함 전 unit test PASS). force-push(`--force-with-lease`) → **PR #82 머지**(merge commit `888ec8e`) → 원격 브랜치 삭제. **status: done.** worktree 정리 대상.

# 현행 상태 (Explore 완료 — 근거)
- **있는 것**: settings.json SessionStart hook — `~/.claude` 한정, main+clean 이면 `git pull --ff-only origin main`(async, 실패 무음, 변경 시 1줄 알림). ✅ 이 세션들에서 정상 작동 관찰됨(모르실 수 있는 이유: 최신이면 무음이라 티가 안 남).
- **없는 것(빈 구간)**: ① 세션 *도중* main 복귀(/e 6단계 ExitWorktree·checkout) 시 pull 없음 — 이번에 merge 후 수동 pull 했던 이유 ② ~/.claude 외 다른 repo ③ --rebase (현행은 ff-only).

# Next
구현·리뷰·검증 완료(커밋 `a6c5aae`). **다음: push + PR → 머지** (사용자 확인 대기 — §8 push 는 요청 시). 활성 loop-ops 와 README 만 겹침 → 별도 브랜치라 머지 시 rebase 로 해소. 머지 후 worktree 정리 대상.

# Decisions
- **ff-only 유지, --rebase 도입 안 함 (✅ 2026-07-16 사용자 확정)**: main 은 로컬 커밋을 만들지 않는 규약(§8 main 직접 금지 + main-edit 가드 예정)이라 rebase 할 로컬 커밋이 없어야 정상. ff-only 가 실패하면 그건 "main 에 로컬 커밋이 있다"는 **이상 신호**라 조용히 rebase 로 덮지 않고 드러내는 게 맞음. 사용자 요청 취지(항상 최신)는 ff-only 로 충족. rebase 가 필요한 상황이 실재하면 그때 재검토.
- **ⓐ post-checkout git hook 추가**: `scripts/install-hooks.sh`(+.ps1)가 설치하는 hook 에 post-checkout 추가 — main/master 로 체크아웃됐고 clean 이면 `git pull --ff-only origin <branch>` (백그라운드 아닌 동기, 실패 시 경고 출력만·차단 없음). ~/.claude 뿐 아니라 **설치한 모든 repo** 에 적용 가능(install-hooks 는 per-repo 1회 실행 규약 유지). worktree 생성 시(post-checkout 발동됨!)는 새 브랜치라 main 조건 미해당 → 무영향 확인 필수.
  - **확정 hook body(리뷰 반영, .sh·.ps1 공유 `#!/bin/sh`)** 게이트 순서: ① `CLAUDE_AUTOPULL_OFF=1`→exit(kill-switch, P3) ② `$3=1`(branch checkout) ③ rebase/merge/bisect 진행 중이면 exit(P 약점) ④ branch∈{main,master} ⑤ clean(diff+cached) ⑥ origin 존재 ⑦ `GIT_TERMINAL_PROMPT=0`+SSH `ConnectTimeout=10`+백그라운드 `git -c core.askpass= -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=10 pull --ff-only --quiet origin <branch>` 를 `kill -0` 0.2s 폴링(100회≈20s 초과 시 kill — timeout(1) 비의존·orphan 0) ⑧ 변경 시 1줄, 실패/timeout 시 중립 경고. 항상 `exit 0`.
  - install-hooks.sh: 멱등 writer 를 `(path,content)` 헬퍼로 추출, pre-commit/pre-push content 는 **바이트 동일**(P4).
- **ⓑ e SKILL 6단계(main 복귀) 뒤에 pull 1줄 — 가드 필수(P2)**: 복귀 직후 pull 은 **branch=main/master + main worktree + ExitWorktree 성공(no-op 아님) + clean** 전부 충족 시에만 `git pull --ff-only origin main`. ExitWorktree 가 no-op(세션이 feature 브랜치/worktree 에 잔류)이면 **skip**(feature 브랜치에 origin/main merge 하는 파괴적 동작 방지). 세션 내 복귀 구간 커버. (착수조건 doc-slim 머지 — 충족.)
- **경계**: 자동 stash·자동 rebase·force 없음(§8). dirty 면 skip+한 줄 보고. 다른 repo 강제 아님(install-hooks 실행한 repo 만).

# Key Files
- scripts/install-hooks.sh / install-hooks.ps1 — post-checkout hook 생성 추가
- scripts/pre-commit-check.sh(참고 — 기존 hook 파일 패턴)
- skills/e/SKILL.md 6단계 — 복귀 후 pull 1줄 (doc-slim 머지 후)
- README — install-hooks 절·SessionStart 설명 동기화

# Blockers
- ⓑ만 doc-slim 머지 대기. ⓐ는 독립 — 먼저 구현 가능.

# Acceptance
1. 실측(`scripts/install-hooks.test.js`, node·fixture bare origin+clone): ① feature→main 체크아웃 시 behind→자동 ff pull(HEAD 전진) ② dirty→skip ③ main 로컬 커밋(비정상)→ff 실패 경고·미rebase ④ worktree add(feature)→무영향 ⑤ `CLAUDE_AUTOPULL_OFF=1`→완전 skip(P3) ⑥ **재귀 non-loop**: N회 checkout 에 hook fire=N(내부 ff pull 이 재발동 안 함, 실측 확정분 회귀방어) ⑦ rebase 진행 중 main 해석 순간 skip.
2. **마이그레이션 idempotency(P4)**: 구 install-hooks.sh(post-checkout 없던 버전) 설치 → 신 재실행 시 pre-commit/pre-push **sha256 불변·.bak 미생성**, post-checkout 만 신규. (신-vs-신 재실행도 동일.)
3. shellcheck(CI)·bash -n 통과. README 동기화 diff.
4. ⓑ: e SKILL 6단계에 pull 서술 + 기존 "비파괴 자동" 원칙과 정합(ff-only 는 비파괴).
5. 현행 SessionStart hook 은 무변경(중복 아님 확인 — 시작 시점 vs 체크아웃 시점으로 역할 분리 서술).

# Review Disposition
**codex 0.134.0 (2026-07-16, medium):**
- **M1 [fix] network hang** — 매 main checkout 동기 `git pull` 이 auth 프롬프트·죽은 VPN·느린 DNS 에 checkout 을 묶음. → hook 에 `export GIT_TERMINAL_PROMPT=0`(대화형 인증 hang 차단) + **feature-detect timeout**(`command -v timeout`→`timeout 15`, elif `gtimeout 15`, 없으면 plain — macOS/Windows 이식성). ff 실패/timeout 은 동일 경고 경로.
- **M2 [fix] 바이트 동일 idempotency** — install-hooks 재실행 시 pre-commit/pre-push 가 .bak 안 생기는 것뿐 아니라 **byte hash 동일**해야. → 테스트에 기존 hook 선설치 후 재실행 → sha256(pre-commit/pre-push) 불변 assert(.sh·.ps1 양쪽).
- **[confirmed sound]** post-checkout 재귀 낮음(ff-merge 는 checkout hook 재발동 안 함, merge/post-merge 계열) · `$3=1`(branch)/`0`(file) 판정 맞음 · detached HEAD→`HEAD`→case skip. → 설계 유지, 테스트로 회귀 방어. **실측 확정**(recursion-check: main checkout 시 내부 ff pull 이 post-checkout 재발동 안 함, HEAD 정상 ff).

**Claude plan-reviewer (2026-07-16, CONDITIONAL) — 강한 우려 4:**
- **P1 [fix] = codex M1** 동기 hook hang: SessionStart 는 async+timeout:30(하니스 강제종료)인데 post-checkout 은 git 동기·무제한. → `GIT_TERMINAL_PROMPT=0`+`core.askpass=`+`http.lowSpeedLimit/Time`+feature-detect `timeout`. background pull 은 워킹트리 변형 race 라 채택 안 함.
- **P2 [fix] ⓑ feature 브랜치 오염(파괴적)**: ExitWorktree no-op 시 세션이 feature 브랜치에 남는데 `git pull --ff-only origin main` 하면 origin/main 을 feature 로 merge. → ⓑ 가드: **branch=main/master + main worktree + ExitWorktree 성공(no-op 아님) + clean** 전부일 때만 pull, 아니면 skip.
- **P3 [fix] rollback 부재**: `.git/hooks/` 비추적·분산 설치라 install-hooks revert 로 기존 설치 hook 안 지워짐. → **kill-switch `CLAUDE_AUTOPULL_OFF=1`** hook 초입 체크(파일 삭제 없이 무력화) + README uninstall(`rm .git/hooks/post-checkout`) 절.
- **P4 [fix] = codex M2 심화** 마이그레이션 idempotency: 테스트 ⑤ 는 신-vs-신만 검증. → **구 install-hooks 설치 → 신 재실행 → pre-commit/pre-push sha256 불변·미백업, post-checkout 만 추가** 케이스 추가.
- **약한 [fix/note]**: rebase/merge/bisect 진행 중 skip(index.lock 경합·transient checkout) → hook 초입에 `$git_dir/{rebase-merge,rebase-apply,MERGE_HEAD,BISECT_LOG}` 존재 시 exit. hook body 정적 lint 밖(shellcheck 는 *.sh 파일만) → **통합 테스트(실제 checkout 시나리오)로 간접 검증** + 재귀 non-loop assert. `git remote get-url`(git≥2.7) minor. SessionStart↔ⓑ 이중 pull 은 무해(ff idempotent).
- **scope note**: default 브랜치가 develop/trunk 면 혜택 없음 → README scope 명시.

**codex 0.134.0 code-review (2026-07-16, medium) — 구현 후:**
- **CM1 [fix] timeout 부재 시 무제한 pull**: macOS 기본에 GNU `timeout` 없어 `_tmo=""` → `git pull` 무바운드 → SSH/DNS/auth stall 에서 checkout hang. → hook 에 `export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh} -o BatchMode=yes -o ConnectTimeout=10"` 추가(SSH transport 바운드) — HTTP 는 lowSpeed, prompt 는 TERMINAL_PROMPT=0 로 이미 바운드 → `timeout` 없어도 전 transport 바운드. .sh·.ps1 둘 다.
- **CM2 [fix] ⓑ 브랜치 오대응**: 가드는 {main,master} 인데 pull 이 `origin main` 고정 → master repo 오ff. → ⓑ 를 `origin "$(git rev-parse --abbrev-ref HEAD)"` 로 수정(현재 브랜치).
- **Cm3 [fix] ④ 테스트 강화**: worktree-add 케이스가 hook 미발동해도 통과 → 새 worktree 가 분기점 유지(미pull) assert 추가. (발동 자체는 recursion-check 로 실증.)
**Claude code-reviewer (2026-07-16, REQUEST CHANGES→해소) — 구현 후:**
- **RM1 [fix] = codex CM1 심화**: 사용자 머신 실측 = macOS + `timeout`/`gtimeout` **둘 다 부재** + origin **HTTPS** → SSH ConnectTimeout 무의미·HTTP lowSpeed 는 connect 단계(DNS/TCP/TLS) hang 못 막음 → checkout 이 hang 가능(사용자 환경 직격). → **`timeout(1)` 비의존 poll 워치독**: 백그라운드 pull(stdio detached) 을 `kill -0` 0.2s 폴링, 100회(≈20s) 초과 시 kill. orphan 0(서브셸 watchdog 의 sleep orphan 문제도 poll 로 제거). SessionStart 는 no-timeout 시에도 async+하니스 timeout 이라 무관.
- **Rm2 [fix] 테스트 env 누출**: base env 가 ambient `CLAUDE_AUTOPULL_OFF`/`GIT_DIR`/`GIT_WORK_TREE` 를 hook 에 전파 → kill-switch 켠 dev 에서 ①⑥ 거짓 실패. → `BASE_ENV` 로 scrub.
- **Rm3 [fix] 커버리지 갭**: rebase/merge 중 skip·flag=0 skip 미검증 → 직접 훅 호출로 ⑦(MERGE_HEAD skip)·⑧(flag=0 skip)·⑨(직접호출 positive) 추가.
- **Rm4 [wontfix-cosmetic] .ps1/.sh trailing newline 1B 차이**: 각 설치기 self-idempotent, cross-install(한 repo 를 두 OS 설치기로) 비현실적. 본문 로직은 IDENTICAL 실측 확인(41줄 diff 0). 주석도 "logic" 한정.
- 최종 재검증: install-hooks.test.js **16/16 PASS**, orphan sleep 0, .sh 설치본≡.ps1 본문(41줄, `sh -n` OK), baseline 4 test 전건 PASS.

# Workflow Findings
(발생 시 기록)
