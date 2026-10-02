---
title: session-fetch-flake — SessionStart 훅 테스트가 부하에서 시간 상한에 흔들리지 않게(테스트 전용 시간 배수)
status: in_progress
started: 2026-10-02
updated: 2026-10-02
---

# Goal
`scripts/session-fetch.test.js` 가 프로세스 생성 부하(Windows 에서 검증을 겹쳐 돌릴 때)에서 간헐 실패하지 않게 한다. 같은 시간 상한을 거치는 `session-brief.test.js` 도 부하에서 실패해(base 8/8) 함께 고친다. 운영의 시간 상한 기본값은 그대로 둔다 — 사용자 지시(2026-10-02): "운영 기본값은 바꾸지 않고 테스트가 부하에 흔들리지 않게, 동시 부하 재현으로 수정 전 실패·수정 후 통과를 입증".

# Intent
- 출처: `plans/2026-10-01-wiki-windows-followups/wiki-windows-followups-plan.md` # Intent Out of scope 32행("묶음 밖"), 공용 wiki `lesson-serialize-windows-verification`(2026-10-01 런처 단위의 최종 검증에서 드러남).
- Problem — 2026-10-02 base `dbad22e` 실측(Windows 11·16 CPU·Node 22.19.0·git 2.55.0.windows.5). 동시 부하는 같은 테스트 8벌을 한꺼번에 띄운 것(scratch `sf_load.sh`)이다. 계측은 scratch preload(`NODE_OPTIONS=--require sf_trace.js`)가 훅 프로세스의 git 호출마다 시작·소요·결과·`timeout` 값을 남긴 것이다.
  - `session-fetch.test.js`: 조용할 때 18건 통과(29초). 계측을 켠 8벌 동시 실행에서 5/8 실패(195초). 계측 없는 base 도 2026-10-01 8벌 3/8 실패(같은 `scripts/`).
    - ①b 4건 — fetch 는 4~5초 걸려 성공했다. 그 뒤 `currentRepoLine` 이 git 4~5회에 2.0~2.6초를 써서, O 신호 전체 예산 `CWD_BUDGET_MS`(2초)가 마지막 `spent()` 확인에서 이미 만든 줄을 버렸다 → 빈 출력.
    - ⑰ 1건 — 훅의 첫 `rev-parse` 가 2.3초로 git 호출별 timeout(2초)에 걸렸다(ETIMEDOUT). fetch 없이 끝나 "superproject 는 갱신된다" 전제가 실패했다.
    - 출력을 단언하지 않는 테스트에서도 예산 사용 3.2초가 2건, timeout 이 2건(`rev-parse @{upstream}`·`rev-list`, 그중 하나는 예산 사용 4.3초) 났다.
    - git 호출(fetch 포함)은 p50 112ms·p90 878ms·p99 5.3초·최대 5.81초(fetch — 상한 8초의 73%)였다.
    - stdin 대기(1초)로 인한 폴백은 0회였다. stdout 백스톱은 write 콜백 시각을 남기지 않아 이 계측으로 판정할 수 없다.
  - `session-brief.test.js`: 조용할 때 95건 통과(149초). 계측을 켠 8벌 동시 실행에서 8/8 실패(290초) — K 머지 대기(147·161행), O 밀림 파일(567행), N 갈라짐(892행) 단언.
    - git 호출별 2초 timeout 이 18회 났다(K `for-each-ref`·`rev-list --count`, N `rev-parse --absolute-git-dir`·`log -1`·`diff`·`ls-files`, O `status`·`rev-parse`). 성공한 호출은 최대 1.95초였다.
    - 한 사본(c6)은 timeout 없이 O 단언이 실패했다 — 예산 만료로 보인다(⚠️ 추정).
  - 3 Whys:
    1. 부하에서 git 생성이 느려져 시간 상한이 만료되고, 훅은 설계대로 조용히 넘어간다(fail-open).
    2. 테스트가 실제 훅을 운영 상한 그대로 띄워 기능(ref 갱신 → 한 줄, 신호 → 한 줄)을 단언한다. 그래서 "로직이 맞다"와 "기계가 빨랐다"를 가르지 못한다.
    3. 임계·경로·스위치는 env 로 주입하는데(`CLAUDE_BRIEF_*`·`CLAUDE_SESSION_FETCH_MIN_MINUTES`) 시간 상한에만 주입점이 없다.
- Constraints:
  - 운영 기본값 불변 — 조절값이 없으면 모든 상한이 지금과 같은 ms 다(사용자 지시).
  - 조절값은 테스트 전용이다. 운영에서 키우면 최악 합이 settings 의 훅 timeout(brief 10초·fetch 30초)을 넘는다. 그러면 하니스가 훅을 죽이고, 하니스는 자손을 거두지 않아 git 이 고아로 남는다(공용 wiki `git-hook-network-safety`). 이름·주석·README 에 적고 상한을 둔다.
  - 훅은 모듈 로드부터 언제나 exit 0 이다 — 새 코드가 CLI try 밖(모듈 최상위)에서 던질 수 있으면 안 된다.
  - 이 repo 는 자기 배포 채널이다 — 머지 → CI 통과 기록 → 각 머신의 다음 세션 auto-pull 로 모든 머신에 간다. CI 는 배수 10 으로 도는 테스트만 보므로, 기본(미설정) 경로의 결함은 따로 확인한다(Acceptance 6).
  - 증상 억제 금지 — 재시도·skip·단언 완화로 덮지 않는다(CLAUDE.md §1).
- Out of scope:
  - 운영 상한 값 조정 — 사용자 지시. git 호출 수 줄이기 — 상한 값은 아니지만 운영 동작을 바꾸는 별개 작업이라 뺐다(사용자 확인 2026-10-02).
  - 부하에서의 운영 브리프 결함 — 줄이 조용히 빠지거나 틀린 문장이 나온다(N 의 `gitOk` 가 ETIMEDOUT 을 "없음"으로 읽는 등). # Deferred.
  - 시간 상한 만료 자체(예산을 넘기면 무음)를 시험하는 테스트 — 지금도 없고 이 요구가 아니다.
  - `session-start-pull.test.js` ⑪ 의 `elapsed < 12000` 같은 다른 시간 단언 — 이 plan 밖이다. 그래서 Windows 검증 직렬화 권고(lesson)는 계속 필요하다.
- 묶음: 없음 — 아래 ⚠️(§10 트리거 3).
- 분할: 없음 — 조절값(훅 3파일)과 그것을 쓰는 테스트는 한 요구의 양면이다. 조절값만 먼저 머지하면 쓰는 곳 없는 테스트 전용 조절값이 README 에 남고, 테스트 쪽은 조절값 없이 머지할 수 없다. fetch 테스트 / brief 테스트로 나누는 안도 봤다 — `session-brief.js` 배선은 fetch 테스트에도 필요해(`currentRepoLine`) 첫 단위에 이미 들어가고, 둘째 단위는 `run()` 한 줄이라 고정비(Windows 검증 약 50분·리뷰)가 이득보다 크다.

# Progress
- 2026-10-02: 착수. base 8벌 동시 부하 재현 + 계측으로 발동한 상한을 특정(위 Problem). Node 22.19.0 실측 — `execFileSync` 의 비정수 `timeout` 은 `ERR_OUT_OF_RANGE`, `setTimeout(2**31)` 은 TimeoutOverflowWarning 후 1ms 로 즉시 발화. plan 초안. `session-brief.test.js` base 부하 8/8 실패 → 범위에 넣음.
- 2026-10-02: plan-review CONDITIONAL(강 2·약 14) → 처분 반영(# Review Disposition). 리뷰어 probe — `execFileSync` 의 `timeout: 0` 은 유효한 값(= 상한 없음). 사용자 plan 승인 — `session-brief.test.js` 포함, git 호출 수 줄이기·운영 브리프 부하 결함은 범위 밖 유지.
- 2026-10-02: TDD Red(`hook-cwd.test.js` — `scaleMs is not a function`) → 구현(hook-cwd·session-brief·session-fetch·두 테스트 `run()`·README) → Green: `node --check` 6파일, `hook-cwd.test.js` 3건, 조용한 상태 `session-fetch.test.js` 18건(38초)·`session-brief.test.js` 95건(141초) 통과. 수정 후 부하 재현(단독) 실행.
- 2026-10-02: 수정 후 부하 재현 — session-fetch 무계측 8×3 `pass=24 fail=0`(라운드 232~273초). 계측 8×1 `pass=8`: (b) `currentRepoLine` 시작 64건 중 빈 출력 0, (c) run() 경유 호출 timeout 전부 20000·fetch 80000, (d) 최장 fetch 9.8초/80초·그 밖 4.2초/20초·예산 사용 9.4초/20초. 단 (a) ETIMEDOUT 2·(c) timeout 2000 호출 8건이 남았다 — 사본마다 1건씩 stdin 폴백 뒤 `rev-parse` 하나뿐인 프로세스, 즉 run() 을 거치지 않는 ⑨ 의 직접 spawn(배수 없음, exit 0 만 단언)이다(scratch `sf_unscaled_calls.js` 로 확인). session-brief 8×2 `pass=15 fail=1` — ⓣ(364행)에서 훅이 exit 1·stderr 없음으로 끝났다(라운드 889·755초). 코드상 브리프가 exit 1 로 끝나는 길은 잡히지 않은 예외(stderr 에 스택)뿐이라 원인 미상 — 스트레스 하네스(scratch `sb_exit_stress.js`, 브리프 안 probe 가 start·uncaught·exit 이벤트 기록)로 branch(배수 10)·base(미설정)를 비교 중.
- 2026-10-02: 스트레스 — ⓣ 조건 브리프를 동시 32개로 branch(배수 10) 3000회·base(미설정) 3000회: 둘 다 exit 0 3000/3000, 출력 0(브리프 1회 p50 9.5/11.1초·최대 38/34초). exit 1 은 재현되지 않았다 — 원인 미상으로 둔다(재현 실패는 환경 탓의 근거가 아니다). 실패 시각 11:58:21 에 이 세션은 도구를 쓰지 않았고, 오늘 생긴 상태줄 고아 둘(12:13·12:28)도 유휴 중이었다(하니스는 유휴 중에도 프로세스를 띄운다 — 외부 종료 가설의 정황일 뿐 ⚠️). 직접 spawn 3곳에 배수를 넣고(`TIME_SCALE` 상수) 조용한 상태 재확인(단위 3·session-fetch 18·session-brief 95 통과) → session-fetch 계측 8×1, probe 를 켠 session-brief 8×2 재측정 중.
- 2026-10-02: 재측정 — session-fetch 계측 8×1 `pass=8`, (a) ETIMEDOUT 0, (b) `currentRepoLine` 시작 64건 중 빈 출력 0, (c) timeout 전부 20000·fetch 80000, (d) 최장 fetch 6.8초/80초·그 밖 3.3초/20초·예산 사용 5.2초/20초 → Acceptance 4 문구 그대로 충족. session-brief(probe) 8×2 `pass=15 fail=1` — 254행 테스트에서 다시 `brief exited 1`(stderr 없음). probe: 그 브리프(pid 35564, 13:16:09.557 시작, 13:16:10 실패 기록)만 `start` 뒤 `exit`·`uncaught` 기록이 없다(1830개 중 1개). exit 처리기가 돌지 않았고 exit code 1·stderr 없음 → 밖에서 TerminateProcess(…, 1)(libuv kill·taskkill /F 의 종료 방식)로 끝난 것이다 — 시간 상한과 다른 부류이고 브리프 코드는 이 종료에 관여하지 못한다. 가해자는 미상(⚠️ 주기적 프로세스 관리의 오래된 PID 종료 — PID 재사용 — 로 의심: 오늘 상태줄 프로세스 생성 12:13·12:28·12:43·13:00·13:31 의 약 15분 주기 위에 두 종료(11:58·13:16)가 놓인다. 상태줄은 `refreshInterval: 2`). repo 코드에 PID 로 종료하는 곳은 없다(`notify-hook.js` 의 `child.kill()` 은 핸들 기반·종료 후 타이머 해제).
- 2026-10-02: code-review APPROVE(Minor 2·Nit 7) → 처분 반영(# Review Disposition — Nit 7 만 wontfix). 단위 4건 통과, `sf_mixed_version.js` 로 Minor 1 수정 확인. simplify 체크 — 변경 없음(각 훅의 항등 폴백 두 개는 require 실패·export 부재를 각각 맡고, 테스트의 `TIME_SCALE` 은 파일당 상수 하나, 주석은 코드에 안 드러나는 이유만). 수정 뒤 확인(조용한 session-brief, session-fetch 계측 8×1, Acceptance 6·8) 실행.
- 2026-10-02: 수정 뒤 확인 — 조용한 session-brief 95 통과. session-fetch 계측 8×1 `pass=8`, (a) 0·(b) 0/64·(c) 20000·80000 전부·(d) fetch 5.8초/80초·그 밖 3.8초/20초·예산 5.4초/20초. Acceptance 6(b) 미설정 경로 base·branch 출력·exit code 동일(fetch 한 줄, 브리프 K+O 두 줄), 6(a) `=1` 로 session-fetch 18·session-brief 95 통과. Acceptance 8 stdin 대기 — 미설정 1.69·1.58초, `=3` 3.36·3.60초.
- 2026-10-02: 최종 검증(격리 runner, 단독 46분) `VERIFY_RC=0`, `ALL PASS (skip: install-hooks.test.js(case) record-verified.test.sh)`, FAIL 0. skip 두 건은 기존 환경 사유(git 2.30 이하 ps1 케이스의 sh shim·jq 없음)이고 두 훅·hook-cwd 를 참조하지 않는다. evidence gate — Acceptance 1·2·3·4·6·7·8·9 충족, 5 는 문구상 미충족(15/16 두 번, 실패 2건 모두 외부 종료·시간 상한 기인 실패 0) → NEEDS-HUMAN(기준 한정 승인 대기, 정식 완료 커밋 보류).
- 2026-10-02: 사용자 승인 — Acceptance 5 기준 한정(# Decisions), 마무리는 로컬 main 위로 rebase 후 `/e merge`, 새 사실의 공용 wiki 적립은 머지 뒤 main 세션에서. evidence gate 전 항목 충족 → DONE(status 는 머지 때 done).

# Next
- 정식 완료 커밋 → commit-check → 로컬 main 위로 rebase(로컬 main 의 미push 커밋 2개, drvfs-case-stale — 파일이 겹치지 않는다) → `/e merge`.
- 머지 뒤 main 세션: 공용 wiki 적립(# Deferred 의 [wiki] 두 줄 + lesson-serialize-windows-verification·workflow-failures 갱신). Acceptance 5 는 외부 종료 2건으로 문구상 미충족 — 기준을 "시간 상한 기인 실패 0(probe 로 외부 종료가 확인된 실패 제외)"으로 한정할지 사용자 승인을 받는다.

# Decisions
- wiki decision 조회(`session-fetch session-brief 시간 예산 flake`):
  - `lesson-serialize-windows-verification` — 따른다. 수정 후 부하 재현과 최종 검증을 다른 실행과 겹치지 않게 단독으로 돌리고, 리뷰어 프롬프트에 verify·부하 재현 금지를 적는다.
  - `git-hook-network-safety` — 따른다. 하니스는 자손을 거두지 않으므로 조절값을 테스트 전용으로 두고 상한을 둔다.
  - `session-start-pull.sh` 의 `CLAUDE_AUTOPULL_TIMEOUT` 선례 — 운영 조절값은 하니스 timeout 안으로 자른다. 이 조절값은 그 원칙과 상충한다(아래 ⚠️).
- 설계 — 테스트 전용 env `CLAUDE_BRIEF_FETCH_TEST_TIME_SCALE`(배수):
  - 이름: 테스트 전용(`TEST`)과 범위(session-brief·session-fetch 둘)를 담는다. 세 번째 SessionStart 훅 `session-start-pull.sh` 는 따르지 않는다.
  - `hook-cwd.js` 에 `scaleMs(ms, env = process.env)` 를 둔다. `Number(값)` 이 유한수면 [1, 20] 으로 자르고 `Math.round(ms × 배수)`, 아니면(없음·비숫자) ms 그대로다. 빈 값·공백은 0 으로 읽혀 하한 1 로 잘린다(결과는 그대로).
  - 호출부는 전부 `scaleMs(ms)` 로 `process.env` 하나만 본다. `env` 인자는 단위 테스트용이다.
    - `currentRepoLine` 의 `env` 인자는 임계용이고 시간 상한은 따르지 않는다. git()·stdin·백스톱은 `process.env` 만 볼 수 있어서, 섞으면 예산과 호출 timeout 의 배수가 갈린다. 그 함수에 한 줄 주석을 단다.
  - 이것을 거치는 상한: `readHookCwd` 의 stdin 대기, `session-brief.js` 의 git timeout·`CWD_BUDGET_MS`·stdout 백스톱, `session-fetch.js` 의 `GIT_MS`·`FETCH_MS`·stdout 백스톱.
  - 두 훅은 `scaleMs` 기본값 `(ms) => ms` 를 require 앞에 둔다. `hook-cwd.js` 를 못 읽어도 지금처럼 폴백하고, 모듈 최상위에서는 부르지 않는다.
  - 테스트: `session-fetch.test.js`·`session-brief.test.js` 의 `run()` 이 `process.env` 에 값이 있으면 그것을, 없으면 `10` 을 넣는다. 테스트별 env 가 덮을 수 있다. 바깥에서 `=1` 로 돌리면 운영 상한 그대로 종단 실행이 된다.
  - run() 을 거치지 않고 훅을 직접 띄우는 곳(session-fetch ⑨, session-brief ⓥ 의 둘)에도 같은 배수를 넣는다(파일 상단 상수 `TIME_SCALE` 하나를 함께 쓴다)로 변경 (이유: 첫 수정 후 계측에서 ⑨ 의 직접 spawn 이 배수 없이 돌아 Acceptance 4(a)(c) 가 문구상 미충족이었다. 그 단언(exit 0·무음)은 시간과 무관하지만, 같은 파일의 훅 실행이 한 규칙을 따르게 하고 배선 판정을 값 그대로 하기 위해서다 — 기준 문구는 바꾸지 않았다).
  - 상한 전부를 거치게 하는 이유:
    - 계측에서 예산(①b)과 호출별 timeout(⑰, brief 18회)이 둘 다 실패를 만들었고, fetch 상한(최대 73%)도 가깝다.
    - stdin·백스톱은 발동이 관측되지 않았지만 같은 부류(만료되면 기능 출력이 바뀐다)다.
    - 부하로 프로세스가 스케줄되지 못하면 이벤트 루프가 타이머 단계를 poll 보다 먼저 돌아, stdin 타이머가 데이터보다 먼저 발화할 수 있다(⚠️ 추정, 관측 0회). 그러면 process.cwd() 로 폴백해 엉뚱한 repo 를 본다.
  - 하한 1: 1 미만을 허용하면 운영 상한이 준다. 0 이면 `execFileSync` 의 `timeout: 0`(유효한 값 = 상한 없음, 리뷰어 probe)이 되어 훅의 timeout 이 사라진다.
  - 상한 20: 운영에서 잘못 켰을 때의 피해 상한이다(고아 git 수명 = 상한 × 배수 — brief git 40초·fetch 160초). 테스트 값 10 의 두 배라 여유는 남는다. 초안의 "setTimeout 2^31-1 오버플로 방지" 근거는 이 크기에서 성립하지 않아 버렸다(8000ms × 100 도 2^31-1 의 0.04%).
  - `Math.round`: 비정수 `timeout` 은 `execFileSync` 가 던지고(실측), 훅은 그것을 git 실패로 삼켜 조용해진다.
  - 테스트 값 10: 계측의 최장 git 호출 5.81초(fetch → 상한 80초), 예산 사용 최대 4.3초(→ 상한 20초).
  - 트레이드오프: 통합 테스트가 10배로 돌면, 평상시에도 O 신호가 2초를 넘게 되는 회귀(예: `currentRepoLine` 에 git 호출 추가)가 테스트에서 안 보인다. 바깥 `=1` 실행으로 확인할 수 있게 했고, 이번 변경의 확인은 Acceptance 6 이 한다.
  - `session-brief.js` 의 쓰이지 않는 `STDIN_MS`(52행)와 659행 주석 "(최대 STDIN_MS)" 를 같은 커밋에서 정리한다. stdin 대기가 배수를 따르게 되면 더 틀린 서술이 되고, 이 상수에 배수를 걸면 된다는 착각을 부른다(§3-5 주석 정합 — 초안의 # Deferred 에서 옮김).
  - 기각:
    - stdin JSON 시험 필드(테스트가 hook 입력에 키를 싣고, 훅은 그 키가 있을 때만 배수를 쓴다) — 하니스가 stdin 을 만들므로 운영에서 켤 수 없다는 장점이 있다. 그러나 stdin 대기는 키를 읽기 전이라 늘릴 수 없다. JSON 없는 경로를 단언하는 `session-brief.test.js` ⓞ10(`/2커밋 뒤처짐/`)은 키를 실을 수 없어 같은 결함이 남는다. 파싱한 값을 두 모듈의 상태로 넘기는 배선(fetch 가 brief 의 git 을 `currentRepoLine` 으로 부른다)도 는다.
    - 함수 인자 주입(DI) — brief 의 git() 이 K·M·N·O 전반에서 불려 배선이 넓고, CLI 진입부(stdin·백스톱)는 in-process 테스트에서 빠진다.
    - 검증 직렬화만 하기(lesson 의 처방) — 사용자 지시는 테스트 자체의 견고성이다. 다른 이유로 겹치는 실행(다른 세션·CI 머신)은 여전히 흔든다.
    - 테스트 재시도, 불확정 시 skip — 증상 억제이고, 부하가 높을 때 실제 회귀를 가린다.
    - 운영 상한 상향 — 사용자 지시 위반이고, 동기 브리프가 세션 시작을 더 붙잡는다.
    - 테스트 preload 로 `execFileSync`·`Date.now` 를 바꾸기 — 운영 코드는 그대로지만 시간 왜곡이 스탬프 나이·날짜 계산까지 흔든다.
    - 상한별 env 여러 개 — 조절면만 넓어진다.
    - argv 플래그 — 이 훅들에는 argv 해석이 없고, env 가 이 repo 의 조절 채널이다.
- 되돌리기: 코드만 바뀐다(상태·마이그레이션 없음). 미설정이면 상한 값이 지금과 같아 revert 가 안전하다. 즉시 차단 레버는 settings `env` 의 `CLAUDE_SESSION_FETCH_OFF=1`·`CLAUDE_BRIEF_CWD_OFF=1`·`CLAUDE_SESSION_BRIEF_OFF=1` 이다.
- 가장 위험한 단계: 머지 뒤 기본(미설정) 경로의 결함 — 자기 배포로 모든 머신에 가고, fail-open 이라 조용하며, CI 는 10배로 도는 테스트만 본다. 그래서 code-review 뒤·최종 검증 앞에 기본 경로 종단 확인(Acceptance 6)을 둔다.
- 순서: TDD Red → 구현 → Green → 부하 재현(Acceptance 4·5, 단독) → code-review(프롬프트에 verify·부하 재현 금지) → fixup → 훅 코드가 바뀌었으면 부하 재현 다시 → simplify 체크 → 기본 경로 종단 확인(6)·stdin 관찰(8) → 최종 검증 단독(7).
- ⚠️ 조절값을 운영에 두면 하니스 timeout 을 넘을 수 있다 — `CLAUDE_AUTOPULL_TIMEOUT` 처럼 하니스 timeout 안으로 자르는 원칙과 상충한다 — 자르면 테스트 목적(10배)을 못 이루므로 이름에 `TEST`, 상한 20(피해 상한), 주석·README 경고를 두는 쪽을 택했다(운영에서 이 값을 둘 이유가 없다).
- ⚠️ §10 묶음 트리거 3(선행 plan 의 Out of scope 에서 새 plan 을 시작)이 문구상 걸린다 — 선행 `wiki-windows-followups` 는 이미 repo-context-kit 묶음에 속하고, plan 은 묶음 하나만 가리킨다(§10) — 그 항목이 스스로 "묶음 밖"이고 같은 요구의 후속이 아니라(검증 환경에서 드러난 별개 결함) 묶음을 만들지 않았다.
- 커밋 단위: 1개 — 조절값과 그것을 쓰는 테스트가 한 목적이다(위 `분할:` 근거).
- Acceptance 5 를 "`pass=16 fail=0`" 에서 "시간 상한 기인 실패 0(probe 로 외부 종료가 확인된 실패는 제외)"로 한정했다(사용자 승인 2026-10-02). 이유: 수정 후 두 번의 부하 재현(각 15/16)의 실패 2건은 모두 밖에서 종료된 프로세스였다 — probe 에 exit 처리기 실행 기록이 없고 exit 1·stderr 없음이라 브리프 코드가 관여할 수 없고, base 에도 같은 현상이 걸린다. 같은 조건 스트레스 6000회(branch·base)는 모두 exit 0 이었다. 기각: 가해자 조사가 끝날 때까지 미완으로 두기 — 하니스 동작 관찰이 필요한 별개 문제라 이 단위의 범위가 아니다.

# Key Files
- `scripts/hook-cwd.js` — `scaleMs`, `readHookCwd` 의 stdin 대기, 머리 주석
- `scripts/session-brief.js` — git timeout·`CWD_BUDGET_MS`·stdout 백스톱, `STDIN_MS` 정리
- `scripts/session-fetch.js` — `GIT_MS`·`FETCH_MS`·stdout 백스톱, 최악 합 주석
- `scripts/hook-cwd.test.js` — 새 파일, 배수 해석
- `scripts/session-fetch.test.js` — `run()` 배수
- `scripts/session-brief.test.js` — `run()` 배수
- `README.md` — `hook-cwd.js` 항목(457행)·트리(724행)

# Blockers

# Acceptance
1. 운영 기본값 불변 — 조절값이 없으면 모든 상한이 지금 ms 와 같다. 검증: `hook-cwd.test.js` 의 미설정 케이스, diff 에서 상한 상수 값 불변. 통과: 테스트 통과, 상수 값 변경 없음.
2. 배수 해석 — 미설정·비숫자 → 그대로, 빈 값 → 그대로(하한), `10` → 10배, `1.3333` → 정수 ms, `0`·`-5`·`0.5` → 1배, `1000` → 20배. 검증: `node scripts/hook-cwd.test.js`. 통과: 전부 통과.
3. 수정 전 실패 재현 — base 8벌 동시 부하에서 `session-fetch.test.js` 실패 ≥ 1. 관측: 계측 5/8(`dbad22e`), 무계측 3/8(2026-10-01). 통과: 기록됨.
4. 수정 후 `session-fetch.test.js` 가 같은 부하에서 통과한다(단독 실행).
   - 무계측 `bash <scratch>/sf_load.sh <worktree> scripts/session-fetch.test.js 8 3 <scratch>/sf-load-after` → `pass=24 fail=0`.
   - 계측 1라운드 `bash <scratch>/sf_load.sh <worktree> scripts/session-fetch.test.js 8 1 <scratch>/sf-trace-after trace` → `pass=8`. 분석기에서:
     - (a) ETIMEDOUT 0.
     - (b) `currentRepoLine` 을 시작한(두 번째 `rev-parse --show-toplevel` 이 있는) fetch 프로세스 중 빈 출력 0.
     - (c) 기록된 git `timeout` 이 전부 20000(fetch 는 80000) — session-fetch·session-brief 의 git() 배선을 값으로 확인한다.
     - (d) 최대 git 호출·최대 예산 사용을 배율 상한 대비로 보고한다.
   - 확인 범위: 예산 배선은 (b)와 24회 무실패가 확인한다. stdin 대기 배선은 Acceptance 8 의 관찰로 확인한다. stdout 백스톱 배선은 실행으로 확인하지 못하고 코드 리뷰로만 확인된다.
5. `session-brief.test.js` — base 8벌 동시 부하 실패 ≥ 1(관측 8/8, 계측). 수정 후 같은 부하 `bash <scratch>/sf_load.sh <worktree> scripts/session-brief.test.js 8 2 <scratch>/sb-load-after` 단독 → 시간 상한 기인 실패 0(probe 로 외부 종료가 확인된 실패는 제외 — 처음 기준 `pass=16 fail=0` 에서 사용자 승인으로 한정, 2026-10-02, # Decisions).
6. 기본(미설정) 경로 종단 확인 — (a) 조용한 상태에서 `CLAUDE_BRIEF_FETCH_TEST_TIME_SCALE=1` 로 두 테스트 파일이 통과한다(운영 상한 그대로). (b) 배수를 설정하지 않은 env 로 base(`~/.claude/scripts`, 같은 내용)와 branch 의 두 훅을 같은 fixture 에 실행해 stdout·exit code 가 같다. 통과: 둘 다.
7. 전체 검증 — `bash scripts/verify.sh` 단독 실행. 통과: 마지막 줄 `ALL PASS`(skip 이 붙으면 이 변경 경로가 아님을 확인).
8. stdin 대기 배선 관찰 — 닫히지 않는 stdin 으로 훅을 띄우면(cwd 는 git 밖) 미설정일 때 약 1초, `=3` 일 때 약 3초 뒤에 끝난다. 통과: 두 값의 차가 배수와 맞다.
9. 문서 동기화 — README `hook-cwd.js` 항목에 조절값(테스트 전용·범위·[1, 20]·운영에 두면 생기는 일)과 테스트 파일, 트리 724행에 `(+ .test.js)`, `hook-cwd.js` 머리 주석, `session-fetch.js` 최악 합 주석. 검증: diff 검토. 통과: 코드와 서술이 맞는다.

# Review Disposition
- [plan-review 1차, 2026-10-02 CONDITIONAL]
  - ⚠️1(운영에서 하니스 timeout 초과) — accepted-risk: 이름에 `TEST`·범위, 상한 20(피해 상한), 하한 근거 기록, 주석·README 경고. 운영에서 둘 이유가 없는 값이다.
  - ⚠️2(§10 트리거 3) — resolved: 리뷰어 동의(선행 plan 의 `intent:` 가 이미 있어 처리 방식을 쓸 수 없고, 요구가 다르다). 출처를 Intent 에 경로로 남겼다.
  - 강1(완화책이 설계에 없음) — fix: 이름 변경, 상한 100 → 20(근거 정정), 하한 근거(`timeout: 0` = 상한 없음)와 Acceptance 2 의 `0`·`-5`, 기각 대안 (a) stdin 시험 필드·(b) DI 기록.
  - 강2(Acceptance 4 판정 불가) — fix: out dir 인자, 예산 만료 판정식(CRL 시작 + 빈 출력), timeout 값으로 배선 확인, 확인 범위 명시. 분석기 보강은 scratch 에서 한다.
  - 약1(배수 출처) — fix: 호출부 전부 `process.env`, `currentRepoLine` 주석.
  - 약2(rollback·위험 단계·기본 경로) — fix: Decisions 의 되돌리기·가장 위험한 단계·순서, Acceptance 6.
  - 약3(수치 어긋남) — fix: fetch 최대 5.81초(73%), 예산 사용 최대 4.3초, 백스톱은 판정 불가로.
  - 약4(브리프 줄이 조용히 빠진다는 서술) — fix: "무음 또는 틀린 문장"으로 고치고 운영 결함은 # Deferred(코드 확인 — `gitOk` 300-307행, `verifiedTarget` 317-339행, K `log -1` 102-107행).
  - 약5(Intent) — fix: git 호출 수 제외를 ⚠️ 추론으로 표기하고 승인 때 확인, `session-brief.test.js` 포함을 승인 질문에 명시, Constraints 에 exit 0(모듈 로드 포함)·자기 배포 채널.
  - 약6(기각 대안) — fix: (a)(b)·검증 직렬화만.
  - 약7(분할 줄) — fix: fetch/brief 테스트 분할 후보와 기각 이유.
  - 약8(`STDIN_MS`) — fix: 같은 커밋에서 정리(# Deferred 에서 옮김).
  - 약9(문서 지점) — fix: `hook-cwd.js` 머리 주석을 Acceptance 9 에. README 517 포인터는 넣지 않는다 — 사용자 조절값 목록에 테스트 전용 값을 올리면 쓰라는 신호가 된다(경고는 457행 조절값 서술에 둔다). 공용 wiki 두 쪽 갱신은 # Deferred(main 세션).
  - 약10(폴백) — fix: `scaleMs` 기본값을 require 앞에.
  - 약11(운영 상한 미시험) — fix: 트레이드오프 기록, `run()` 이 바깥 값을 우선(`=1` 종단 실행), Acceptance 6(a).
  - 약12(다른 시간 단언) — fix: Out of scope 에 `session-start-pull.test.js` ⑪.
  - 약13(유한수 서술) — fix.
  - 약14(⚠️2 + §10 공백 제안) — ⚠️2 resolved. §10 공백 제안은 # Workflow Findings 가 아니라 # Deferred 에 둔다 — 확인된 workflow 실패가 아니라 규약 공백이라 dlc 의 기록 트리거(①~③)에 해당하지 않는다.
  - 누락 시나리오: stdin 타이머가 데이터보다 먼저 발화 — fix(stdin 배수 근거에 ⚠️ 추정으로). base 조건(계측 5/8·무계측 3/8, brief 8/8·c6 예산 추정) — fix(Problem·Acceptance 3).
- [code-review 1차, 2026-10-02 APPROVE — Critical·Major 0]
  - Minor 1(export 없는 옛 `hook-cwd.js` 와 섞이면 브리프 백스톱에서 TypeError → exit 1) — fix: 두 훅의 구조 분해에 `scaleMs = (ms) => ms` 기본값. 확인: scratch `sf_mixed_version.js` — 현재판·HEAD 판·부재 세 경우 모두 브리프 exit 0 + M 줄, fetch exit 0(HEAD 판은 줄까지).
  - Minor 2(배선 회귀 테스트 부재) — fix: `hook-cwd.test.js` 에 env 를 넘기지 않는 `process.env` 경로 단언, `TIME_SCALE_ENV` 를 export 해 두 테스트가 import(이름 drift 방지). 호출부 배선을 영구 테스트로 감시하는 안(preload 로 `execFileSync` 감시)은 비용 대비 기각 — 계측 라운드(Acceptance 4(c))와 리뷰가 확인했다.
  - Nit 1(테스트 머리 주석이 stdin 범위를 과장) — fix: 타이머 경로는 자동 테스트가 없다고 적음.
  - Nit 2(a 네트워크 상한 제외·b "넘어" 단정·c 하한 근거) — fix: `hook-cwd.js` 주석과 README.
  - Nit 3(최악 합 주석 "배수 1 일 때" 부정확) — fix: "이 합은 배수 1 기준".
  - Nit 4(`isFinite` 불연속) — fix: `Number.isNaN` 으로 거르고 ±Infinity 는 자르기에 맡김(README "숫자가 아니면 무시"와 일치), 테스트에 `Infinity`·`-Infinity`.
  - Nit 5(run() 설명 주석과 함수 사이에 `TIME_SCALE`) — fix: 상수를 설명 주석 위로.
  - Nit 6(바깥 빈 값을 테스트는 10배, 훅은 1배로 읽음) — fix: `??`.
  - Nit 7(시간 배수가 hook-cwd.js 에 있는 응집도) — wontfix: 별도 모듈로 빼면 훅마다 폴백이 하나씩 는다. 머리 주석·README 가 두 책임을 적는다.
  - Open(probe 기록 실패 가능성) — 답: A5 probe 는 사본마다 별도 파일이고 사본 안에서 브리프는 순차로 떠 같은 파일에 동시 append 가 없다. 나머지 1829개는 start·exit 가 모두 짝지어 있다(기록 실패 0). 그리고 probe 와 무관하게 exit code 1·stderr 없음은 내부 경로로 설명되지 않는다.
  - Open(`session-brief.js:197` 의 무가드 `require('./plan-match.js')`) — # Deferred(사전 존재).

# Deferred
- [medium] 부하에서의 운영 브리프 결함 — N 의 `gitOk`(`scripts/session-brief.js:300-307`)가 ETIMEDOUT 도 false 로 돌려, `verifiedTarget` 이 "CI 검증 기록이 없어 보류"(317-323행)·"origin/main 밖"(337-339행) 같은 틀린 처방을 낸다. K 는 `log -1` 실패 시 ct=0 으로 정렬 맨 앞에 온다(102-107행). 1배(운영 상한)에서도 brief 1회가 10.2초 걸렸다(하니스 10초 초과, 계측 sb c2) — K·M·N 에는 전체 예산이 없다.
- [low] 공용 wiki `lesson-serialize-windows-verification`(18행)·`workflow-failures`(50행)가 이 flake 를 열린 결함으로 적고 있다 — 머지 뒤 main 세션에서 "테스트 쪽은 고쳤다(배수), 직렬화 권고는 다른 시간 단언 때문에 유지" 로 갱신.
- [wiki] ~/.claude main 세션에서 /wiki ingest — Windows 에서 밖에서 종료된 프로세스(TerminateProcess(…, 1) — libuv kill·taskkill /F 의 방식)는 exit code 1·`exit` 처리기 미실행·stderr 없음이다. 부모의 spawnSync 가 스스로 죽였으면 signal 이 남고 status 가 null 이라 구별된다. 진단법: `NODE_OPTIONS=--require` preload 로 start·`uncaughtExceptionMonitor`·exit 를 남긴다. 이 세션의 무거운 프로세스 생성 중 무관한 node 프로세스가 두 번 밖에서 종료됐다(가해자 미상 ⚠️). 출처: 공개(이 repo 의 재현).
- [wiki] ~/.claude main 세션에서 /wiki ingest — Node 22.19: `execFileSync` 의 `timeout` 은 정수만(비정수 `ERR_OUT_OF_RANGE`), `0` 은 상한 없음, `setTimeout` 은 2^31-1ms 를 넘으면 1ms 로 즉시 발화. 출처: 공개(실측). 그리고 이 단위의 설계(SessionStart 훅 테스트 전용 시간 배수와 기각 대안)를 decision 페이지 후보로.
- [low] `scripts/session-brief.js:197` 의 `require('./plan-match.js')` 는 모듈 최상위에서 가드 없이 실행된다(이 변경 전부터) — plan-match.js 가 없거나 깨지면 스택을 남기는 exit 1 이다. "모듈 로드부터 exit 0" 계약의 남은 구멍(code-review Open).
- [proposal] §10 묶음 트리거 3 은 선행 plan 이 이미 다른 묶음에 속한 경우를 정하지 않는다(스칼라 `intent:` 와 충돌) — "선행이 묶여 있고 같은 요구의 후속이 아니면 묶음을 만들지 않는다" 한 줄을 제안한다. 운영 자산(CLAUDE.md)이라 승인 후 별도 작업.
