---
title: autopull-verified-client — SessionStart 자동 pull 이 ci/verified 에 기록된 커밋까지만 ff, 보류 사유는 세션 브리프가 알림
status: done
started: 2026-09-26
updated: 2026-09-28
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

자동 pull 검증 게이트의 2단계. `scripts/session-start-pull.sh` 가 `origin/ci/verified` 의 기록 커밋이 담은 `main-sha` 가 origin/main 의 조상일 때만 그 커밋까지 ff 한다. 보류하면 `scripts/session-brief.js` 의 밀림 신호(N)가 이유와 처방을 알린다. `CLAUDE_AUTOPULL_VERIFY=0` 이면 지금처럼 origin/main 까지 ff 한다.

# Intent

- 링크: `plans/2026-09-25-repo-audit-followups/intent.md` 의 `autopull-verified-client` 단위. 출발점은 1단계 plan(`plans/2026-09-26-autopull-verified-ff/`)의 Decisions·Review Disposition.
- 착수 조건 충족(2026-09-26): 1단계 머지 push(run 36228831948)에서 `record-verified` success, 기록 커밋 `38aae27` 의 `main-sha` = 머지 커밋 `1016a5f`, 트리는 `main-sha` 하나(40 hex, 개행 없음). REST 경로로 workflow 파일 없는 root 기록을 만들 수 있다는 것이 실측으로 확인됐다.
- 사용자 결정(1단계에서 확정): 확인 실패 시 "ff 보류 + 브리프 알림 + 검증 끄는 환경변수".
- 규모: medium(sh 훅·브리프 js·테스트 2개·README·wiki·lint.yml 주석, 목적 1).
- 분할: 없음 — 자동 pull 의 새 보류 경로와 브리프의 사유는 한 머지여야 한다. 자동 pull 만 들어가면 보류 중인 머신이 "원인 미확인" 만 보고, 브리프만 들어가면 존재하지 않는 보류를 설명한다. fetch 만 먼저 내보내는 분할도 위험을 줄이지 않는다 — 깨진 fetch 는 어느 쪽이든 그 머신을 얼린다(plan-reviewer).
- 델타: 자동 pull 계약(모든 경로 exit 0, 네트워크는 워치독 안, 프롬프트 없음)을 유지한다. 이 스크립트는 macOS 와 **Windows Git Bash** 에서 돈다 — CI 는 ubuntu 뿐이라 Windows 는 여기서 검증되지 않는다. 검증 게이트는 무인 SessionStart 경로에만 건다 — `post-checkout` 훅(main 체크아웃 때 origin/main pull)과 `/e` 8단계 pull 은 검증 없이 origin/main 을 따른다(README 에 명시).
- Out of scope: `record-verified` job 동작 변경(주석만 현재형으로), `post-checkout`·`/e` pull 게이트, 다른 repo 의 `session-fetch.js`.

사실 확인(2026-09-26, git 2.54, scratch 실측):
- ✅ 기록이 새 root 로 다시 만들어지면(삭제 뒤 재기록) `+` 없는 refspec 은 fetch 를 거부한다(rc 1). `+` 가 있으면 받는다.
- ✅ 로컬에 `refs/remotes/origin/ci` 가 있으면 D/F 충돌로 fetch 가 rc 1 이지만 `origin/main` 은 갱신된다(원자적이지 않음). 이 Mac 에는 그 ref 가 없다(plan-reviewer).
- ✅ `fetch.pruneTags=true` 여도 명령줄 refspec 을 준 `--prune` 은 로컬 전용 태그를 지우지 않았다. `--no-prune-tags` 는 존재한다.
- ✅ `merge --ff-only <HEAD 의 조상>` 은 rc 0, HEAD 불변(no-op).
- ✅ `--no-write-fetch-head` 는 FETCH_HEAD 를 건드리지 않는다(`session-fetch.js` 선례).

# Acceptance

1. 자동 pull: 검증 켜짐(`CLAUDE_AUTOPULL_VERIFY` 가 정확히 `0` 이 아니면)이면 `git fetch --quiet --prune --no-write-fetch-head origin '+refs/heads/main:refs/remotes/origin/main' '+refs/heads/ci/*:refs/remotes/origin/ci/*'`(main 먼저, 워치독 안) 뒤 `refs/remotes/origin/ci/verified:main-sha` 가 HEAD sha 와 같은 길이의 소문자 16진수(문자 목록 판정)이고 `refs/remotes/origin/main` 의 조상일 때만 그 sha 로 `merge --ff-only`. 아니면 ff 하지 않고 무음. 검증 꺼짐이면 예전 명령 `fetch origin main` 뒤 `refs/remotes/origin/main` 으로 ff(새 fetch 가 깨진 머신의 탈출구). MSYS 경로 변환은 끄지 않는다. 검증: `node scripts/session-start-pull.test.js` —
   - (a) 기록 = main tip → ff, 알림(옛 스크립트도 통과 — 회귀 잠금)
   - (b) 기록 없음 → ff 안 함·무음, `origin/main` 추적 ref 는 갱신
   - (c) 기록이 tip 보다 뒤(CI 진행 중) → 기록까지만 ff
   - (d) 원격이 기록을 지웠고(다른 clone 에서) 로컬 추적 ref 는 옛 값(HEAD 보다 앞) → prune 으로 사라져 ff 안 함
   - (e) 기록 sha 가 origin/main 밖이고 로컬 객체이며 HEAD 의 후손(재작성 직후) → ff 안 함
   - (f) 기록 내용이 git 이 해석하는 이름(`refs/remotes/origin/main`) → 형식 불량으로 ff 안 함
   - (g) 기록이 새 root 로 다시 만들어져 더 새 tip 을 가리킴 → 받아서 ff(`+`)
   - (h) HEAD 가 이미 기록보다 앞섬 → HEAD 불변·무음
   - (f2) 기록이 짧은 16진수(축약 sha) → ff 안 함(길이 확인)
   - (i) `CLAUDE_AUTOPULL_VERIFY=0` → origin/main 으로 ff(`false`·`off` 는 켜짐)
   - (i2) 로컬 `refs/remotes/origin/ci`(D/F)로 새 fetch 가 실패하는 머신 — 검증 켜짐은 보류, `CLAUDE_AUTOPULL_VERIFY=0` 은 예전 fetch 로 ff
   - 스크립트에 `MSYS_NO_PATHCONV`·`MSYS2_ARG_CONV_EXCL` 이 없다(주석 제외 텍스트 단언 — Windows 는 CI 에 없다)
   - 기존 케이스(dirty 무관·충돌 거부·main 아님·끄기·워치독·손자 kill·중단된 fetch 뒤 이전 결과로 머지 안 함)는 기록을 tip 에 둔 fixture 로 통과, 사용자 FETCH_HEAD 를 덮지 않음
   - mutation 6종이 각각 해당 케이스를 실패시킨다: `--prune` 제거(d), 조상 확인 제거(e), 형식 확인 제거(f), 길이 확인 제거(f2), `ci` refspec 의 `+` 제거(g), 검증 꺼짐도 새 fetch 사용(i2)
   Red: (b)~(i) 중 옛 스크립트의 동작과 다른 것은 옛 스크립트에서 실패. (a) 와 (i) 는 회귀 잠금.
2. 브리프 N(`autopullStalledLine`): 기존 사유(끔·detached·main 아님·진행 중·갈라짐) 뒤, 검증 켜짐이면 — 로컬 `refs/remotes/origin/ci` 충돌 / 기록 없음 / 기록 형식 아님(내용은 출력하지 않는다) / 기록이 origin/main 밖 / 기록이 HEAD 에 이미 포함(마지막 fetch 기준) 을 각각 알린다. 문구는 캐시 기준임을 밝히고 사유별 처방을 붙인다(확인: `gh run list -w Lint -b main -L 3`, 급하면 1회 `git -C ~/.claude pull --ff-only` — `CLAUDE_AUTOPULL_VERIFY=0` 은 영구 해제로만 안내). 충돌 파일 판정은 검증 켜짐이면 `HEAD..기록 sha`, 꺼짐이면 `HEAD..origin/main`. 비0 을 내는 git 호출(`merge-base --is-ancestor`·`show`·`rev-parse --verify`)은 사유마다 따로 처리해 N 줄 전체가 사라지지 않게 한다. 검증: `node scripts/session-brief.test.js` 새 케이스(사유 5종·검증 꺼짐 경로) + 기존 N 케이스(기록 = origin/main tip fixture, 비-behindRepo 케이스 포함) 통과.
3. 두 테스트 하니스는 `CLAUDE_AUTOPULL_` 접두 env 를 모두 지우고, 자동 pull 하니스는 `GIT_CONFIG_NOSYSTEM=1`·fixture `XDG_CONFIG_HOME` 으로 사용자 git 설정(`fetch.prune` 등)을 막는다.
4. 문서: `session-start-pull.sh` 머리·FETCH_HEAD 주석, `session-brief.js` 의 `git pull` 근거 주석, 테스트 ⑪-b 이름, `lint.yml` 기록 job 주석(현재형, REST 확인, `main-sha` 는 client 와의 계약 — HEAD 와 같은 길이 16진수·개행 없음), README(자동 pull 절 426·485, CI 절 435, 끄기 절 547, 트리 680 — "검증 게이트는 SessionStart 만"·한계·rollback·수동 복구·전환기 1세션·fork/CI 없는 clone 은 `CLAUDE_AUTOPULL_VERIFY=0`), wiki `autopull-verified-ff`(client 결정·REST ❌→✅·영구 정지 레버 답), `wiki/index.md`·`wiki/log.md`, intent 줄.
5. 전체: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음), plan-lint 통과.
- [ ] [post-merge] 두 머신(macOS·Windows)의 다음 세션 뒤 `git -C ~/.claude ls-remote origin main` 과 `git -C ~/.claude rev-parse origin/main` 이 같은지(fetch 가 도는지 — 깨지면 브리프도 침묵한다), 그리고 `~/.claude` 가 기록된 커밋까지 ff 됐거나 브리프가 보류 사유를 말하는지 관찰. Windows 에서 fetch 가 실패하면 `CLAUDE_AUTOPULL_VERIFY=0` 또는 수동 `git -C ~/.claude pull --ff-only` 로 복구하고 원인을 후속으로 연다.

# Progress

- 2026-09-26: 착수. 1단계 머지로 기록 존재 확인.
- 2026-09-26: plan-reviewer CONDITIONAL — 강 2(Windows 미검증인데 깨지면 무음·push 로 못 고침, rollback·가장 비싼 단계 없음 / 조상·형식·`+` 가 테스트로 안 잠김, "기록=tip" Red 주장 오류)·약 다수. probe 5개 실측(새 root 재기록·D/F·pruneTags·ff-only no-op·no-write-fetch-head). plan 보강.
- 2026-09-26: 자동 pull — 테스트 먼저(Red: 옛 스크립트에서 (b)(c)(d)(e)(f)(g)(i)·FETCH_HEAD 8건 실패, (a)(h) 는 잠금으로 통과) → 구현 → 28/28. mutation 4종: `--prune`·조상·`+` 는 첫 시도에 잡힘, 형식 확인 제거는 **살아남음**(기록 내용이 24자라 길이 확인이 대신 막았다) → (f) fixture 를 40자 이름(`refs/remotes/origin/main~0…`)으로 바꿔 잡힘. 브리프 — **순서 이탈: 구현을 테스트보다 먼저 썼다.** 테스트를 쓴 뒤 HEAD 의 옛 브리프로 돌려 Red 확인(ⓝ15~ⓝ19·ⓝ21 실패, ⓝ20 잠금 통과) → 83/83. 문서: lint.yml 주석, README(N·CI·SessionStart·끄기·트리), wiki·index·log. check_links clean, shellcheck ok.
- 2026-09-26: code-reviewer(Codex 미가용) REQUEST CHANGES — Critical 1(MSYS 변수가 `-C` 경로 변환까지 꺼 Windows 자동 pull 이 매번 무음 실패), Minor 5, 권고 1, Nit 6, refuted 7. fix: MSYS 변수 제거 + 재도입 방지 단언, VERIFY=0 은 예전 fetch(탈출구 — (i2)), 16진 판정 문자 목록, 브리프 끝 개행만 제거(ⓝ18b), 모든 기록 사유에 "마지막 fetch 기준", 길이 확인 테스트((f2)), 문서 정정. fetch 지속 실패 신호는 Deferred. 최종 검증(격리 runner): 자동 pull 31/31, 브리프 84/84, mutation 6/6 잡힘, 옛 브리프 RED 7(ⓝ15~19·18b·21), `verify.sh` `ALL PASS`(skip 없음), plan-lint·link clean. evidence gate: Acceptance 1~5 충족, [post-merge] 1건. 판정 DONE(통합 대기). targeted 재리뷰는 생략 — Critical 수정이 제거이고 mutation·테스트가 새 경로를 잠근다(Report 에 명시).
- 2026-09-28: Windows 확인(Git Bash MINGW64, git 2.55.0.windows.5) — 이슈 #189 의 fetch 명령 rc=0(rtk 래퍼 없이 `/mingw64/bin/git.exe` 로 다시 돌려도 rc=0), `origin/ci/verified` 수신. 원격 브랜치로 worktree 를 만들어 `session-start-pull.test.js` 31/31·`session-brief.test.js` 84/84 Windows 통과. 전체 `verify.sh` 는 Windows 에서 기존 결함 5종으로 실패(Deferred — origin/main 재현으로 이 브랜치 무관 입증). Acceptance 5 의 `ALL PASS` 는 2026-09-26 macOS 실행 증거로 유지하고, 머지 전 CI(ubuntu)에서 다시 확인한다.
- 2026-09-28: `/e merge` — origin/main(46커밋) 병합 `92c719d`, 충돌 3곳(README·wiki index·log)은 줄마다 한쪽만 바뀐 것이라 그쪽 버전으로(결과가 base→branch 변경과 같음을 대조), 병합 트리에서 자동 pull 31/31·브리프 84/84·plan-lint·링크 통과. PR #193. 묶음 intent 는 windows-ps1-verify 미착수라 open 유지.

# Next


# Decisions

- ff 대상은 기록 커밋의 `main-sha` 가 가리키는 sha. 조건: HEAD sha 와 같은 길이의 16진수(repo 해시 길이 — `--show-object-format` 대신 `${#before}`, 호출 1개와 버전 의존이 없다) + `origin/main` 의 조상(`merge-base --is-ancestor` 는 객체가 없으면 실패하므로 "로컬 커밋" 확인을 겸한다). 이유: 1단계 불변식(기록은 main 위)을 client 도 확인한다 — 재작성 직후 기록 job 이 아직 안 돈 창에서 main 밖 커밋으로 ff 하지 않는다.
- 두 refspec 을 fetch 한 번으로 받는다 — 같은 ref 광고 스냅샷이어야 기록과 main 의 관계를 판단할 수 있다. main 을 먼저 둔다(로컬 갱신은 원자적이지 않아, 중간 상태를 브리프가 읽으면 "main 밖" 거짓 경보가 아니라 "미전진" 쪽이 되게 — ⚠️갱신 순서 추정).
- `ci/*` refspec 은 `+` — 기록은 정지 레버(삭제) 뒤 새 root 로 다시 생긴다. `+` 가 없으면 fetch 가 거부돼 영원히 무음 정지한다(실측).
- `--prune` 은 명령줄 refspec 범위만 지운다 — 원격이 기록을 지우면 로컬 옛 기록으로 ff 하지 않는다.
- `--no-write-fetch-head` — ff 는 fetch 성공 뒤의 추적 ref 로 하므로 FETCH_HEAD 가 필요 없고, 두 refspec 이면 for-merge 항목이 여럿이 된다. 사용자 FETCH_HEAD 를 덮지 않는다. fetch 가 kill·실패하면 지금처럼 `wait || exit 0` 으로 끝나 이전 fetch 의 추적 ref 로 머지하지 않는다.
- ~~`MSYS_NO_PATHCONV=1`(과 `MSYS2_ARG_CONV_EXCL='*'`)을 fetch 에만~~ → **MSYS 경로 변환은 끄지 않는다** (이유: code-reviewer Critical — 두 변수는 명령의 인자 전부에 걸려 Git Bash 의 `-C /c/Users/...` 까지 native git 에 그대로 넘기고, fetch 가 매번 실패해 캐시가 전진하지 않으니 브리프도 침묵한다. Git for Windows release notes·MSYS2 문서·같은 증상 이슈가 근거, Windows 미실행 ⚠️). refspec 은 `/` 로 시작하지 않아 변환 대상이 아니다. 재도입은 텍스트 단언 테스트로 막는다. 방어로 넣은 장치가 가장 비싼 실패(전 머신 무음 정지)를 만들 뻔했다 — 검증 수단이 없는 플랫폼에 "무시될 것" 이라는 추정으로 스위치를 넣지 않는다.
- 검증 꺼짐(`CLAUDE_AUTOPULL_VERIFY=0`)은 예전 명령(`fetch origin main` — FETCH_HEAD 를 쓰고 origin/main 도 갱신)으로 돌아간다 (이유: code-reviewer — 새 fetch 가 어떤 머신에서 깨졌을 때 VERIFY=0 이 같은 fetch 를 쓰면 탈출구가 되지 못한다. 예전 명령은 두 머신에서 돌던 형태다).
- 16진수 판정은 `case` 의 범위(`0-9a-f`)가 아니라 문자 목록(`0123456789abcdef`) — macOS sh(bash 3.2)는 UTF-8 로케일에서 범위에 A-F·é 를 넣는다(code-reviewer probe). 브리프는 끝 개행만 떼어(`trim()` 아님) 스크립트와 같은 판정을 한다.
- 검증 끄기는 `CLAUDE_AUTOPULL_VERIFY=0`(정확히 `0`), sh·js 같은 술어. ~~기각: 파일 스위치 — `.autopull-off` 가 이미 머신 단위 정지 레버다~~ → 기각 사유 정정: `.autopull-off` 는 pull 을 멈추고 VERIFY=0 은 검증 없이 pull 하는 것이라 역할이 다르다. 파일 스위치가 필요한 GUI 실행 환경은 settings `env` 로 환경변수를 줄 수 있어 따로 두지 않는다(plan-reviewer).
- 원격 전체 정지는 `ci/verified` 삭제(일시 — 다음 green main push 가 새 root 로 다시 기록). 그 사이 고침을 push 하면 고친 커밋까지 한 번에 따라간다. 기각: workflow 에 repo variable 게이트 — 드문 경우를 위해 CI 에 스위치를 하나 더 둔다.
- 브리프 사유 순서: 끔 → detached → main 아님 → 진행 중 → 갈라짐 → (검증 켜짐) `origin/ci` 충돌 → 기록 없음 → 기록 형식 아님 → 기록이 main 밖 → 기록 미전진 → 충돌 파일(HEAD..기록) → 원인 미확인. 갈라짐이 먼저인 이유: 갈라지면 기록이 있어도 ff 가 영원히 불가능하다.
- ⚠️ 게이트하지 않는 경로: `/e` 8단계는 자기 머지 직후 pull 하므로 늘 기록 전이라 게이트하면 항상 보류된다. `post-checkout` 은 사용자가 main 을 체크아웃하는 순간이라 무인 경로가 아니다. — 사용자 결정이 아니라 이 plan 의 판단이다.
- Rollback: 레버는 머신 단위 `CLAUDE_AUTOPULL_VERIFY=0`(검증 없이 예전 fetch 로 pull — 새 fetch 가 깨진 머신의 탈출구이기도 하다) → `CLAUDE_AUTOPULL_OFF`/`.autopull-off`(정지) → 원격 `ci/verified` 삭제(전 머신 일시 보류). 즉시 확인은 머신별 `git -C ~/.claude pull --ff-only`. 기능 전체 제거는 1단계 순서(client revert → 기록이 그 revert 까지 전진한 것 확인 → job 제거)를 따른다. revert 도 새 client 가 ff 할 수 있을 때만 자동 전달된다.
- 가장 비싼 단계는 머지다 — 바꾸는 것이 그 머지를 전 머신에 배포하는 경로다. Windows 는 머지 전에 실측할지 사용자에게 묻는다(머지 확인 시점).
- 한계(README): CI 는 ubuntu lint 뿐이라 Windows 에서만 드러나는 파손도 "검증됨" 으로 기록된다. fork·Actions 가 없는 clone 은 기록이 영영 없어 `CLAUDE_AUTOPULL_VERIFY=0` 이 필요하다. 전환기 1세션: 새 브리프가 옛 스크립트의 캐시(ci 추적 ref 없음)를 읽어 "기록 없음" 을 말할 수 있다. 옛 스크립트를 가진 머신의 첫 세션은 이 머지를 검증 없이 한 번 pull 한다.
- 커밋 단위: 1개 — `feat(autopull): fast-forward only to the commit CI recorded on ci/verified`.

# Key Files

- `scripts/session-start-pull.sh`, `scripts/session-start-pull.test.js`
- `scripts/session-brief.js`, `scripts/session-brief.test.js`
- `.github/workflows/lint.yml` — 기록 job 주석만.
- `README.md`, `wiki/pages/decision/autopull-verified-ff.md`, `wiki/index.md`, `wiki/log.md`
- `plans/2026-09-25-repo-audit-followups/intent.md`

# Review Disposition

- [plan] 강1 Windows 미검증·rollback·가장 비싼 단계 — fix(MSYS 변환 차단, Decisions Rollback·수동 복구, 머지 시점에 Windows 실측 여부 질문, [post-merge] 두 머신). 머지 전 Windows 실행을 Acceptance 에 넣는 것은 사용자 결정으로 넘긴다(이 Mac 에서 불가).
- [plan] 강2 안전 핵심 테스트 공허 — fix(케이스 e·f·g fixture 조건, mutation 4종, (a) Red 주장 정정).
- [plan] 약: 브리프 git() throw·캐시 기준 문구·처방 분리·VERIFY=0 먼저 권하지 않음·기록 내용 비출력·하니스 env 접두 제거와 git 설정 격리·ⓝ14 fixture·pruneTags(실측 무영향)·D/F 사유·Decisions 보강(파일 스위치 사유·게이트 안 하는 경로·단일 fetch)·VERIFY=0 충돌 판정·문서 목록 확장·`--no-write-fetch-head`·게이트 한계·`${#before}` — fix.
- [code] Critical MSYS 변수가 `-C` 경로 변환까지 꺼 Windows fetch 가 매번 실패 — fix(두 변수 제거, 텍스트 단언 테스트, 문서·Decisions 정정).
- [code] Minor 16진 범위의 로케일 의존 — fix(문자 목록). Minor 브리프 `trim()` 과 스크립트 판정 불일치 — fix(끝 개행만, ⓝ18b). Minor VERIFY=0 에서 D/F 무진단 — fix(VERIFY=0 은 예전 fetch 라 D/F 에 걸리지 않음, (i2)). Minor 캐시 기준 문구 — fix(모든 기록 사유에 "마지막 fetch 기준"). Minor 길이 확인 mutation 생존 — fix((f2)·ⓝ18b).
- [code] 권고 fetch 지속 실패를 N 이 감지 못함 — defer(`# Deferred`), [post-merge] 에 `ls-remote` 대조 추가.
- [code] Nit README (2) 요약·435 낡은 문장·(i) `false`·브리프 괄호 중첩·`CLAUDE_BRIEF_REPO` 경로·하니스 `GIT_CONFIG_GLOBAL` 등 — fix. (c) 알림 문구 — wontfix("updated from origin/main (CI-verified, …)" 는 기록 커밋도 origin/main 위라 참이다).
- [code] Codex 미가용(크레딧 소진) — Claude 리뷰만으로 처분.

# Blockers

# Deferred

- (높음, 이 브랜치 무관 — origin/main 재현) Windows 에서 `bash scripts/verify.sh` 가 `skills/commit-check/test_commit_units.py` 에서 무한 대기한다. 테스트의 `subprocess.run(..., input=…, text=True)` 가 encoding 을 지정하지 않아 cp1252 로 한글 메시지를 쓰다 writer 스레드가 `UnicodeEncodeError` 로 죽고, stdin 이 닫히지 않아 `git commit -F -` 가 끝나지 않는다. CI 는 ubuntu(UTF-8)라 안 드러남. `PYTHONUTF8=1` 이면 우회된다. 수정은 별도 작업(`encoding="utf-8"` 명시). `skills/commit-check/test_commit_units.py:48,72,132,775`.
- (중간, 이 브랜치 무관 — origin/main `0f8d6f4` 에서 같은 결과로 재현) Windows 에서 `PYTHONUTF8=1 bash scripts/verify.sh` 는 `FAILED: 4`: `install-hooks.test.js` 의 `[ps1]` 6건, `pre-commit-check.test.sh` 의 `[ps1] HOME/.claude repo main/master push`(이슈 #190 항목 5 와 같은 증상), `record-verified.test.sh`(`jq` 미설치), `commit-check` 의 서명 위조 테스트 2건(`hash-object` rc 128). 이 브랜치 diff 는 이 파일들을 건드리지 않는다. 처리는 #190(windows-ps1-verify) 쪽.

- (중간) 자동 pull 의 fetch 가 어떤 머신에서 계속 실패해도 브리프 N 은 침묵한다(캐시가 전진하지 않아 behind 가 0). 스크립트가 fetch 시도·성공 시각을 `.git` 에 남기고 N 이 "시도는 있는데 성공이 N일째 없음" 을 알리는 신호 — 성공 stamp 만으로는 새 스크립트가 처음부터 깨진 경우를 못 잡는다(stamp 가 영영 생기지 않는다). `scripts/session-start-pull.sh`, `scripts/session-brief.js`.
