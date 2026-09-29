---
title: autopull-fetch-stall — SessionStart 자동 pull 의 fetch 가 계속 실패하면 브리프 N 이 알린다(이슈 #204)
status: in_progress
started: 2026-09-29
updated: 2026-09-29
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

`scripts/session-start-pull.sh` 의 fetch 가 어떤 머신에서 계속 실패해도 세션 브리프 N 이 침묵하는 구멍(이슈 #204)을 막는다. 스크립트가 fetch 시도·성공 시각을 `.git` 에 남기고, `scripts/session-brief.js` 의 N 이 "시도는 있는데 성공이 임계일째 없음"을 behind 0 에서도 알린다.

# Intent

- 링크: 묶음 intent `plans/2026-09-25-repo-audit-followups/intent.md`. 출처는 선행 plan `plans/2026-09-26-autopull-verified-client/` 의 `# Deferred`(code-reviewer 권고, 심각도 중간) → 이슈 #204.
- 델타(이 plan 에만 더해지는 제약):
  - 스탬프는 빈 파일 두 개의 mtime 만 쓴다(`claude-autopull-attempt`, `claude-autopull-ok`, 위치 `git rev-parse --absolute-git-dir`). 지우지 않는다.
  - 스크립트 계약(어떤 경로에서도 exit 0, 네트워크 단계만 워치독)과 브리프 계약(무네트워크·fail-open·동기)을 그대로 둔다.
  - 비교식은 dash 에서도 맞아야 한다 — CI 는 `sh`=dash 로 pull 테스트를 돌린다.
  - 스크립트와 브리프가 같은 파일명을 쓰도록 `AUTOPULL_STAMPS` export 로 키를 잠근다(`fetchStampName` 선례).
- 분할: 없음 — 스크립트 두 곳의 touch 와 브리프 판정은 같은 스탬프 계약의 쓰는 쪽·읽는 쪽이라 따로 머지하면 한쪽만 배포된 창에서 무음이거나 거짓 경보가 난다.
- Out of scope 해석: 묶음 intent 의 Out of scope 는 "두 감사에서 나오지 않은 새 개선"이다. #204 는 감사 항목이 아니라 묶음 산출물(autopull-verified-client)을 code-review 하다 나온 **결함**이라 이 묶음에 연결한다(아래 # Decisions).
- Out of scope(이 plan): macOS 실측(사용자 지시 — bash 3.2 의 `-nt` 는 미검증으로 남긴다), 수동 pull·`/e`·post-checkout 에 ok 스탬프 찍기, fetch 실패 횟수 세기.

# Acceptance

1. `node scripts/session-start-pull.test.js` · `node scripts/session-brief.test.js` 가 Windows Git Bash 에서 전부 통과한다. 신규 케이스 ⑬–⑲(pull, 설계 번호 P1·P3–P7 + 리뷰 추가 ⑯)·ⓝf1–ⓝf11(brief, B1–B11) 은 구현 전 실행 결과(Red/잠금 통과)를 `# Progress` 에 기록한다.
2. 기존 ⑪(워치독 타이밍)·⑪-b(옛 fetch 결과로 머지 안 함)·ⓝ1(최신 무음)이 그대로 통과한다.
3. dash 경로: WSL Ubuntu(`sh`=dash)에서 `node scripts/session-start-pull.test.js` 가 통과한다 — 특히 ⑮(설계 P4, ok 없음 + 옛 attempt 가 다시 실패해도 유지). 원안 `-nt` 단독 식이면 ⑮ 가 dash 에서 실패함을 확인한다.
4. `shellcheck scripts/session-start-pull.sh` 경고 0 — 로컬 0.11.0 과 CI 러너(ubuntu-24.04)와 같은 0.9.0 둘 다. PR CI(ubuntu) `ALL PASS`(skip 줄은 통과로 치지 않는다) — 머지 전 확인.
5. 문서: README N 절·(1) SessionStart·"침묵할 수 있다" 줄, wiki `autopull-verified-ff`(:27, :34)·`index.md`·`log.md` 갱신, `PYTHONUTF8=1 python skills/wiki/check_links.py` 깨끗.
6. 머지 후 실측: 새 세션에서 `ls -l --time-style=full-iso ~/.claude/.git/claude-autopull-*` 의 ok 가 attempt 보다 새것이다(머지 후 항목 — 이 브랜치에서는 미검증).

# Progress

- 2026-09-29: 착수. 설계(정정본) 확인 — 원안의 `[ A -nt O ] || touch A` 는 Ubuntu dash 0.5.12 에서 `-nt 없는파일` 이 거짓이라 ok 가 없을 때 attempt 를 매번 새로 찍는다. 부재를 `-e` 로 명시하는 식으로 간다.
- 2026-09-29: TDD Red(구현 전, 케이스별 격리 러너 — 러너는 `AUTOPULL_STAMPS` 만 주입해 export 누락이 아니라 동작 차이로 판정. 주입 없이 돌리면 신규 케이스 전부 `Cannot read properties of undefined (reading 'attempt')`).
  - brief(ⓝf1–ⓝf11 = B1–B11): Red 7 — ⓝf2·ⓝf3·ⓝf6·ⓝf7·ⓝf11 은 `fetch 가 5일째 …`·`credential.helper=` 문구가 없음(현재 N 은 behind 0 이면 즉시 무음, behind>0 이면 "원인 미확인"·갈라짐·CI 기록 사유), ⓝf5 는 `fetch 가 2일째` 없음, ⓝf10 은 `claude-autopull-attempt 이 스크립트에 없다`. 잠금 통과 4 — ⓝf1·ⓝf4·ⓝf8·ⓝf9. 나머지 기존 84건 통과.
  - pull(P1–P7): Red 6 — ⑪(P2 단언) `fetch 전에 시도 스탬프를 남겨야 한다`, P1 `시도 스탬프가 없다`, P3 `false == true`(attempt 없음), P4·P5·P6 `ENOENT … utime`(스탬프 파일 자체가 없음). 잠금 통과 1 — P7. 나머지 기존 30건 통과.
- 2026-09-29: 구현 — 스크립트 touch 두 곳 + 머리말, 브리프 `AUTOPULL_STAMPS`·`autopullFetchFailure`·`autopullStalledLine(repoDir, env, now)`·main 에서 `new Date()`. Green: Windows Git Bash `node scripts/session-start-pull.test.js` 37 passed · `node scripts/session-brief.test.js` 95 passed. WSL Ubuntu(`/bin/sh` → dash 0.5.12-6ubuntu5, node 18.19.1) 에서도 37·95 passed.
- 2026-09-29: dash 대조 — 원안 `-nt` 단독 식으로 바꾼 사본(scratchpad)은 Windows 37/37 통과, WSL dash 에서 P4 `시도 스탬프를 다시 찍으면 경과 일수가 0 으로 돌아간다` 로 실패. 5경우 직접 실행(none / attempt 만 / attempt 새것 / attempt 옛것 / 같은 시각): dash 는 수정식 touch·keep·keep·touch·touch(기대와 일치), 원안 식은 "attempt 만" 에서 touch(틀림). Git Bash sh 는 두 식 모두 기대와 일치. `shellcheck scripts/session-start-pull.sh`(0.11.0) rc 0. fixture(attempt 5일 전) 에 대해 브리프가 `… 자동 pull 의 fetch 가 5일째 성공하지 못했다(성공 기록 없음) …` 출력.
- 2026-09-29: simplify — 게이트 분기의 `behind ? … : null` 5회를 `gate()` 헬퍼로, gitDir·failure 두 단계 계산을 한 번으로. 재실행 brief 95 passed(Windows·WSL). 문서: README N 절·(1)·(2)·끄기 절, wiki `autopull-verified-ff`(:27·:34, sources)·`index.md`·`log.md`, `PYTHONUTF8=1 python skills/wiki/check_links.py` → clean. `bash scripts/verify.sh`(Windows) → `ALL PASS (skip: install-hooks.test.js(case) record-verified.test.sh)` — skip 2건은 이 변경과 무관(install-hooks 의 한 케이스는 `SKIP [ps1] --path-format 을 모르는 git(2.30 이하) — Windows 에서는 sh shim 을 실행할 수 없음`, record-verified 는 jq 부재)이고 통과로 치지 않는다 — 해당 축은 PR CI(ubuntu)에서 확인.
- 2026-09-29: 코드 리뷰 반영(아래 # Review Disposition). SC3013 disable 주석 → 공식 shellcheck 0.9.0 으로 tracked `*.sh` 전체 rc 0(적용 전 이 줄만 rc 1), 0.11.0 rc 0. 테스트 이름 P1·P3–P7 → ⑬·⑭·⑮·⑰·⑱·⑲ 로 바꾸고 ⑯(ok 있음 + attempt 가 ok 보다 새것인 채 재실패 → attempt·ok 유지) 추가. 리뷰가 든 변형 식 `[ ! -e att ] || [ -e ok ]` 을 넣은 scratchpad 사본에서 ⑯ 이 `시도 스탬프를 다시 찍으면 경과 일수가 0 으로 돌아간다` 로 Red(기존 37건은 이 변형을 통과). Green: Windows pull 38·brief 95 passed, WSL dash pull 38·brief 95 passed.

# Review Disposition

- (Major) CI shellcheck 0.9.0 의 SC3013 이 `session-start-pull.sh` 의 `-nt` 비교에서 verify.sh shell 축을 깨뜨린다 → **fix**: 비교식 바로 위에 이유 한 줄 + `# shellcheck disable=SC3013`. 0.9.0·0.11.0 모두 rc 0. README 에는 CI shellcheck 서술이 없어 문서 변경 없음.
- (Major) "성공한 적 있음 + 계속 실패 → attempt 유지" 분기를 잠그는 테스트가 없다 → **fix**: ⑯ 추가, 변형 식에서 Red 확인.
- (Nit) 테스트 이름이 설계 문서의 P 번호를 써서 P2 가 비어 보인다 → **fix**: 파일의 ①–⑫ 체계를 이어 ⑬–⑲ 로 변경.

# Next

- PR(본문에 `Closes #204`) → PR CI(ubuntu, dash) `ALL PASS` 확인. 머지 후 Acceptance 6 실측.

# Decisions

- **스탬프 = 비교형 두 파일.** `claude-autopull-attempt` = 마지막 성공 뒤 **첫** 시도 시각, `claude-autopull-ok` = 마지막 fetch 성공 시각(rc=0, VERIFY=0 경로 포함). 규칙: attempt 가 없거나, ok 가 있고 attempt 가 ok 보다 엄밀히 새것이 아니면 attempt 를 touch. 이렇게 하면 처음부터 깨진 머신(ok 없음)에서도 attempt 가 첫 실패 시각에 머물러 경과 일수를 잰다.
- **비교식은 부재를 명시한다**: `if [ ! -e "$_att" ] || { [ -e "$_ok" ] && ! [ "$_att" -nt "$_ok" ]; }; then touch "$_att" 2>/dev/null; fi`. 원안 `[ "$_att" -nt "$_ok" ] || touch "$_att"` 은 **기각** — Ubuntu dash 0.5.12-6ubuntu5 에서 `[ a -nt 없는파일 ]` 이 거짓이라(MSYS dash·bash 는 참) ok 가 없을 때 attempt 를 매 세션 새로 찍어, 처음부터 깨진 Linux 머신이 영구 무음이 된다(WSL 실측, CI 는 sh=dash).
- attempt touch 위치는 모든 skip 게이트(OFF·`.autopull-off`·비 git·rebase/merge/bisect·비 main) 뒤, fetch 를 띄우기 직전 — fetch 전에 써야 워치독 kill·하니스 15s kill 뒤에도 남는다. ok touch 는 `wait` 성공 직후(merge 판정 전) — merge 거부는 기존 N 사유(충돌·갈라짐·기록 보류)가 맡는다.
- `: >` 대신 `touch` — 이미 빈 파일에 O_TRUNC 가 mtime 을 갱신하는지는 플랫폼마다 불확실하다 ⚠️.
- **브리프 순서**: behind==0 이면 스탬프 판정을 먼저 하고, 발화 조건이어도 훅 게이트(OFF env·`.autopull-off`·detached·비 main·busy)에 하나라도 걸리면 무음(훅이 fetch 를 시도하지 않는 상태에서 "fetch 가 실패 중"은 거짓). behind>0 이면 기존 게이트 → **fetch 실패** → ahead(갈라짐) → CI 기록 보류 → 충돌 → 원인 미확인. "분기 순서 = 훅이 포기하는 순서" 원칙과 같다(스크립트는 fetch 실패 시 merge 전에 exit).
- `autopullFetchFailure` 는 설계의 `(repoDir, env, now)` 대신 `(gitDir, env, now)` 를 받는다 — 호출부가 busy 판정에 쓰는 `--absolute-git-dir` 를 이미 구하므로 spawn 을 한 번 줄인다. 그래서 git dir 계산을 behind 판정 직후로 올렸다(behind>0 에서 앞쪽 게이트로 끝나는 드문 경로에 spawn 1회가 더해진다).
- 임계 env `CLAUDE_BRIEF_AUTOPULL_DAYS`, 기본 3, 해석은 STALE/DIRTY/FETCH_DAYS 와 같다(`Number.isFinite && >= 1 → floor`, 그 밖 3). 이름은 kill switch `CLAUDE_BRIEF_AUTOPULL_OFF` 와 짝.
- 재현 명령에 `-c credential.helper=` 를 넣는다 — 훅은 helper·프롬프트를 끄므로, 사람이 치는 평범한 fetch 는 되는데 훅만 실패하는 경우를 가려야 한다.
- 1회 실패 + 공백 오경보(실패 한 번 뒤 3일 넘게 세션을 안 열면 다음 브리프가 한 번 알림)는 README 한계로 문서화만 한다 — 횟수를 세면 내용형의 파싱·부분 쓰기 문제가 돌아온다.
- **묶음 연결**: repo-audit-followups 의 Out of scope("두 감사에서 나오지 않은 새 개선")와 충돌해 보이지만, #204 는 묶음 산출물(autopull-verified-client)의 code-review 결함이고 선행 plan 이 이미 이 intent 에 속한다. §10 규칙 3(Deferred 에서 시작)은 묶음 연결을 요구하고 선행 plan 에 두 번째 intent 를 달 수 없다(스칼라 1개). native-overlap-recheck 가 "감사 밖 새 개선"을 새 묶음으로 보낸 선례와 성격이 다르다.
- ~~CI shellcheck 가 sh 의 `-nt` 에 SC3013 을 내면 PR CI 결과를 보고 disable 주석을 단다(CI 버전 모름 ❌)~~ → **PR 전에 `# shellcheck disable=SC3013` 를 단다로 변경** (이유: 코드 리뷰가 CI 러너 ubuntu-24.04 의 shellcheck 가 0.9.0 이고 0.9.0 이 이 줄에 SC3013 warning·rc 1 을 낸다는 것을 확인했다 ✅ — 공식 0.9.0 바이너리로 재현. SC3013 은 0.11.0 에서 제거돼 로컬에서는 안 보였다). `find` 우회는 부재 처리가 복잡해지고 Windows PATH 의 find.exe 충돌 위험 ⚠️.
- 기각한 대안:
  - (a) 성공 스탬프만 — 처음부터 깨진 경우(ok 영영 없음)를 못 잡는다(이슈 본문).
  - (b) origin/main reflog·ref mtime — ref 가 안 움직인 성공 fetch 와 실패를 구분 못 한다.
  - (c) FETCH_HEAD — 검증 경로는 `--no-write-fetch-head` 라 안 쓰이고, 사용자 fetch 와 섞인다.
  - (d) session-fetch 의 `claude-fetch-<ref>` 재사용 — 성공·실패 무관 백오프 의미이고 O 신호가 읽는다(게다가 `~/.claude` 는 session-fetch 대상이 아니다).
  - (e) 브리프에서 `ls-remote` — 동기 브리프의 무네트워크 계약 위반.
  - (f) 삭제형(성공 시 attempt 삭제)·내용형(파일에 시각·횟수 기록) — 삭제형은 rm 실패 시 옛 시각이 남아 실패를 가리고, 내용형은 파싱·부분 쓰기 문제를 새로 만든다.
  - 원안 `-nt` 단독 식 — 위 dash 실측으로 기각.

# Key Files

- `scripts/session-start-pull.sh` — 운영 자산(SessionStart 훅). attempt/ok touch 두 곳 + 머리말.
- `scripts/session-brief.js` — 운영 자산(SessionStart 훅). `AUTOPULL_STAMPS`, `autopullFetchFailure`, `autopullStalledLine(repoDir, env, now)` 재구성.
- `scripts/session-start-pull.test.js` — ⑬–⑲(설계 P1·P3–P7 + ⑯, P2 는 ⑪ 안의 단언).
- `scripts/session-brief.test.js` — B1–B11.
- `README.md` — N 절, `hooks.SessionStart` (1)·(2), 되돌리기 절 "침묵할 수 있다" 줄.
- `wiki/pages/decision/autopull-verified-ff.md`, `wiki/index.md`, `wiki/log.md`.

# Blockers

(없음)

# Deferred

- README `hooks.SessionStart` (2) 의 임계 목록에 기존 `CLAUDE_BRIEF_FETCH_DAYS` 가 빠져 있다(낮음, `README.md` `hooks.SessionStart` (2) 줄 — O 신호의 fetch 신선도 임계). 같은 줄에 `CLAUDE_BRIEF_AUTOPULL_DAYS` 를 넣지만 범위 밖이라 고치지 않는다.
- `scripts/session-brief.test.js:2` 머리 주석이 "K+L+M" 이라 N·O 가 빠졌다(낮음).
