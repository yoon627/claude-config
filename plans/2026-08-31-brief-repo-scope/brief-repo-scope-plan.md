---
title: brief-repo-scope — 세션 브리프가 현재 작업 repo 의 밀림·묵은 미커밋도 말하게 한다
status: in_progress
started: 2026-08-31
updated: 2026-08-31
---

# Goal

세션 시작 브리프의 감시 대상을 `~/.claude` 하나에서 **세션이 실제로 작업 중인 repo** 까지 넓힌다.
넓히면서 라벨과 원인 문구를 repo 별로 가른다 — 지금 그대로 대상만 바꾸면 "~/.claude 가 뒤처졌다"고
**거짓 라벨**을, "훅은 main 에서만"이라는 **없는 훅의 원인**을 말한다(아래 Decisions 실측).

계기: knowledge_base 가 origin 보다 37커밋 뒤처지고 plan 편집이 3일간 미커밋으로 방치됐는데
아무 신호도 없었다. 2026-08-12 에 같은 실패 모드를 고쳤지만 그 수정이 `~/.claude` 한정이었다.

# Progress

- 2026-08-31: 원인을 실측으로 확정하고 이 plan 을 열었다. `CLAUDE_BRIEF_REPO` 로 브리프를
  knowledge_base worktree 에 겨누면 `~/.claude 1010커밋 뒤처짐 — 브랜치가 adapter-sandbox 라 자동
  pull 이 돌지 않는다(훅은 main 에서만)` 가 나온다 — 계산은 맞고 라벨·원인이 둘 다 틀린다.

- 2026-08-31: codex plan 리뷰(medium) — Critical 0 / Major 4 / Minor 5. 전부 반영했다(아래 Decisions).
  가장 큰 것은 **cwd 입력원**이었다: 계획은 `process.cwd()` 를 전제했는데 근거가 없었다. 이 repo 의
  형제 훅 4개가 전부 hook stdin JSON 의 `cwd` 를 쓴다 — `dlc-task-router.js:37`,
  `guard-worktree-edit.js:67`, `dlc-early-stop.js:57`, `notify-hook.js:49`. 그것이 정답이다.
- 2026-08-31: 비용을 실측했다(knowledge_base, tracked 815). `git status --porcelain -z` 32ms,
  `rev-list --left-right --count` 22ms. 예산 설계의 근거로 쓴다.
- 2026-08-31: 테스트 10건을 먼저 쓰고(Red 확인) 구현했다. `node scripts/session-brief.test.js`
  **65 passed**(기존 55 + 신규 10). 실 repo 관찰도 통과 — 뒤처진 worktree 를 cwd 로 주면
  `adapter-sandbox 1022커밋 뒤처짐·로컬 2커밋 앞섬 — 갈라져서 ff-only pull 이 불가능하다(rebase 나
  push 필요)`, 동기화·clean 인 main worktree 는 무음, stdin 없이 직접 실행해도 208ms 에 끝난다.
  N 라벨도 고쳤다 — 다른 repo 를 겨누면 이제 `adapter-sandbox 1022커밋 뒤처짐 …` 로 나온다.
- 2026-08-31: code-reviewer(claude, **CONDITIONAL**) + codex code 리뷰(high, Critical 0/Major 5/Minor 4)를
  받아 반영했다. 결정적 지적은 **기준 ref 폴백**이었다 — `origin/HEAD` 로 떨어뜨리면 knowledge_base
  worktree 68개 중 **60개**(upstream 없음)가 "294~1019커밋 뒤처짐"으로 걸린다(리뷰어 실측). 폴백을
  제거했고, 계기 사건은 폴백 없이도 잡힌다. 반영 후 **67 tests passed**, 실 repo 관찰도 다시 했다:
  upstream 없는 `adapter-sandbox` 는 이제 무음(전에는 1022커밋 뒤처짐이라고 했다),
  `CSTP1-2898-dev-merge` 는 `origin/dev 대비 336커밋 뒤처짐 — 이 repo 에는 자동 pull 이 없다`,
  `cstp-ai-agent-defaults` 는 `미커밋 13일: wiki/index.md, …`.
# Next

1. simplify 점검 후 `~/.claude` main 에 ff-only 머지.
2. 머지 후 새 세션에서 실제로 뜨는지 관찰(현재 이 머신은 대상 repo 가 조용해 무음이 정상).
3. push 는 사용자 승인 후.


# Decisions

- **새 신호는 cwd repo 한정으로 drift + 묵은 미커밋 두 파트를 한 줄에 담는다. K(머지 대기)·M(닫히지
  않은 plan)은 cwd repo 로 확장하지 않는다.** 이유: 브리프를 knowledge_base 에 겨눴을 때 K 가
  미머지 로컬 브랜치 35개를 뱉었다(실측 `+30` 표시). 매 세션 그 줄이 뜨면 신호가 잡음이 되어 죽는다.
- **기준 ref 는 `@{upstream}` 우선**(없으면 `origin/HEAD` → `origin/main`). 이유: 이번 사건에서 실제
  밀린 축은 `origin/dev` 였다. `origin/main` 고정이면 dev 계열 브랜치에서 일하는 세션은 영영 못 본다.
- **`~/.claude` 자신은 새 신호에서 제외**한다(기존 N 이 담당). 판정은 git common dir 비교 —
  `~/.claude` 의 worktree 에서 일해도 같은 repo 로 잡힌다.
- **원인 문구를 repo 별로 가른다.** `~/.claude` 는 자동 pull 훅이 있으니 "왜 훅이 못 따라잡았나"가
  맞고, 다른 repo 는 **훅이 아예 없으니** "자동 pull 이 없다(수동 pull 필요)"가 맞다. 같은 문구를
  재사용하면 브랜치를 main 으로 바꾸면 풀린다는 잘못된 처방을 준다.
- **묵은 미커밋 임계는 3일**(`CLAUDE_BRIEF_DIRTY_DAYS`, 기본 3). 편집 중인 파일로 매 세션 울리면
  잡음이다. 이번 사건의 실제 트리거(3일 방치된 plan 편집)를 잡는 최소 임계.
- **fail-open·무음 원칙 유지** — 판정 불가(비 git·upstream 없음·git 실패)는 전부 무음, 동기화+clean
  이면 무음. 신호별 예외 격리(`collect`)에 그대로 얹는다.

- **cwd 입력원은 hook stdin JSON 의 `cwd`** 다(codex Major 1). `process.cwd()` 가 프로젝트 루트라는
  근거가 없다 — 반면 형제 훅 4개(`dlc-task-router.js:37`·`guard-worktree-edit.js:67`·
  `dlc-early-stop.js:57`·`notify-hook.js:49`)가 모두 stdin JSON 을 쓴다. 같은 입력원을 따른다.
  **공식 문서로도 확정**했다(code.claude.com/docs/en/hooks, 2026-08-31 조회) — `cwd` 는 **모든 hook
  이벤트 공통 입력 필드**이고 "cwd follows Claude — worktree 에 들어가면 worktree 루트, `cd` 하면 그
  디렉토리"라고 명시한다. `process.cwd()` 보다 정확한 입력이다.
  터미널 직접 실행은 `process.stdin.isTTY` 가드로 즉시 `process.cwd()` 폴백(`notify-hook.js:22` 패턴),
  stdin 이 안 닫히는 환경 대비 짧은 타임아웃 백스톱 — **세션 시작을 막지 않는다**.
- **시간 예산을 둔다**(codex Major 4). fail-open 은 예외 정책이지 시간 상한이 아니다. 새 신호는
  마감시각을 들고 각 git 호출 전에 확인하고, 넘으면 가진 것만 내거나 무음. spawn 도 줄인다 —
  behind·ahead 를 `rev-list --left-right --count <upstream>...HEAD` **한 번**으로 얻는다.
  mtime 조회는 상한을 둔다. 실측 근거: status 32ms·rev-list 22ms(tracked 815).
- **upstream fallback 을 명시한다**(codex Major 3): `@{upstream}` → `origin/HEAD` → `origin/main`.
  각 단계는 `rev-parse --verify` 로 **존재를 확인한 것만** 채택하고, 채택 후 `rev-list` 가 실패하면
  다음 단계로 내려가지 않고 **무음**(원인을 지어내지 않는다). 셋 다 없으면 무음.
- **`~/.claude` 제외는 git common dir 로 판정한다**(codex Minor 2). cwd repo 의
  `rev-parse --path-format=absolute --git-common-dir` 를 `<repoDir>/.git` 과 정규화 비교(win32 는
  대소문자 무시). 경로 prefix 비교는 쓰지 않는다 — `~/.claude` 의 worktree 가 repo 밖에 있는 실제
  사례가 있다(`orca/workspaces/.claude/searobin`).
- **테스트는 cwd 를 명시 주입한다**(codex Major 2). `run()` 이 기본으로 `{cwd: blankRepo()}` JSON 을
  stdin 으로 넣는다 — 기존 테스트가 실 worktree 상태(지금도 untracked plan 이 있다)에 물들지 않게.
  이 파일 머리 주석의 "실 repo 가 우연히 조용해서 통과했다" 교훈과 같은 이유다.
- **묵은 미커밋 판정 기준을 못박는다**(codex Minor 3): tracked 변경 + untracked(ignored 제외)의
  **파일 mtime 최댓값이 아니라 최솟값(가장 오래된 것)** 기준, 달력 일수(`daysSinceLocal` 과 같은 축),
  미래 mtime 은 0 으로 클램프, 삭제된 파일은 stat 불가라 제외.

- **미커밋 나이는 upstream 유무와 독립**이다(구현 중 테스트가 두 관심사를 섞어서 드러났다). 원격이
  없어도 "5일째 커밋 안 된 파일"은 참인 사실이라 알린다. 반대로 셀 기준(upstream)이 없으면 밀림
  숫자는 **만들지 않는다** — 기준 없는 숫자를 같은 문장에 담지 않는다.
- **출력 모양은 N 과 같게** `<대상> <사실> — <처방>`. 이름 뒤에 대시를 또 넣으면 한 줄에 대시가 둘이
  되어 어디까지가 사실이고 어디부터가 처방인지 흐려진다(첫 구현에서 실제로 그랬다).
- **N 의 하드코딩 라벨도 이번에 고친다**(계획 3번). 원래는 "결과 불변" 조건이었지만, `CLAUDE_BRIEF_REPO`
  로 다른 repo 를 겨누는 경로가 실재하고 그때 거짓 라벨이 나오므로 감시 대상에서 유도하도록 바꿨다.
  기본 경로(`~/.claude`)의 출력은 그대로다.

- **기준 ref 폴백을 제거한다 (변경 — 이유: 실측 60/68 오탐).** 원래 `@{upstream}`→`origin/HEAD`→
  `origin/main` 순이었다. 이 워크플로우는 feature 브랜치를 push 하지 않는 것이 규약이라 upstream
  없음이 정상이고, 폴백은 조치 불가능한 "main 에서 갈라짐"을 매 세션 낸다 — K 를 확장하지 않기로 한
  이유와 같은 잡음이다. 계기 사건은 `@{upstream}` 만으로 잡힌다(실측 확인).
- **출력에 기준 ref 이름을 넣는다.** `336커밋 뒤처짐` 만으로는 무엇 대비인지 알 수 없어 사용자가
  확인할 수 없다 — 이번 사건의 "거짓 원인"과 같은 종류의 정보 결손이다.
- **`git status` 는 `--no-optional-locks`·`-uall` 로 부른다.** 전자는 배경 도구가 사용자 repo 의
  `index.lock` 을 잡은 채 2s timeout 으로 강제 종료되는 것을 막고(데이터 무결성), 후자는 untracked
  디렉토리 접힘(`?? dir/`)이 나이를 거짓으로 만드는 것을 막는다(디렉토리 mtime 은 안쪽 파일 편집으로
  안 바뀐다).
- **stdout 은 write 콜백에서 종료한다.** 파이프 write 는 비동기라 곧바로 `process.exit` 하면 브리프가
  잘려 도착할 수 있다(부모 커밋부터 있던 문제).
- **제외 판정은 낼 것이 있을 때만 한다.** 대부분의 세션은 무음이므로, worktree·submodule 대응용
  추가 spawn 을 무음 경로에서 물지 않게 마지막으로 옮겼다.

# Review Disposition

- `origin/HEAD` 폴백 대량 오탐 (claude C1 = codex Major 1) — **fix**: 폴백 제거 + 회귀 테스트 ⓞ11.
- 캐시 ref 만 보는데 자동 fetch 주체가 없다 (claude C2) — **fix(문서)**: 코드 주석과 README 에 N 의
  "부트스트랩 구멍"과 동급 한계로 명시. 미커밋 파트는 네트워크와 무관해 그 구멍이 없다는 점도.
- stdout flush 전 exit (codex Major 1) — **fix**: write 콜백에서 종료.
- macOS realpath / 8.3 단축명 (claude M1) — **fix**: `samePath` 가 `fs.realpathSync.native` 통과.
- 하네스가 non-zero exit 를 삼킨다 (codex Major 5) — **fix**: `run()` 이 throw.
- stdin 없는 `spawnSync` 2곳이 실 worktree 를 본다 (claude M2 = codex Major 4) — **fix**: 두 곳에
  `CLAUDE_BRIEF_CWD_OFF=1`.
- worktree/submodule 제외 미검증 (claude M3 = codex Major 4) — **fix**: repoDir 쪽 common dir 을
  실제로 물어보는 경로 추가 + 양방향 테스트 ⓞ12.
- untracked 디렉토리 접힘 · cap 을 정렬 전에 자름 (claude M4 = codex Minor 1) — **fix**: `-uall`,
  cap 20→200 + 예산 검사를 루프 안으로.
- `index.lock` (claude M6) — **fix**: `--no-optional-locks`.
- rollback 절차 부재 (claude M8 = codex Major 5) — **fix**: README 에 kill switch·revert 전파 명시.
- 라벨이 worktree 이름이라 repo 를 모른다 (claude) — **fix**: 다르면 `<repo>/<worktree>`.
- 빈 basename(`C:\`·`/`) (codex Minor 2) — **fix**: `|| top` 폴백.
- 느린 stdin(>백스톱) 이면 폴백 (codex Major 2) — **부분 fix**: 300ms→1000ms 로 형제 훅
  (`dlc-early-stop.js`) 선례에 맞춤. 무한 대기를 막는 것과 느린 입력을 기다리는 것은 상충하므로
  선례 값을 따르고 동작을 문서화한다.
- 3일 mtime 임계가 계기 사건을 못 잡을 수 있다 (claude M5) — **wontfix(근거 있음)**: 문제의 파일은
  2026-08-28 17:57 이후 손대지 않아 mtime 이 3일이었다. 다만 "편집하면 나이가 리셋된다"는 성질은 그대로다.
- 전역 시간 예산 부재 (claude M7 = codex Major 3) — **defer** → `# Deferred`.
- TTY 분기 미검증 (codex Minor 3) — **wontfix**: 실 TTY 를 테스트에서 만들 수 없다. 대신 터미널에서
  직접 실행해 208ms 종료를 관찰했다(수동 검증).
- SessionStart 가 compact·fork 에서도 재발화 (claude) — **accept**: 한 줄이고, 그 시점에도 사실이다.

# Deferred

- **전역 시간 예산이 없다** — `CWD_BUDGET_MS` 는 O 내부 마감이라, 앞선 K 가 최악(브랜치 100개 × git 2회
  × 2s)으로 밀리면 hook timeout 10s 를 O 차례 전에 소진할 수 있다. 실측은 여유가 있다(브리프 소요
  n=56, p50 529ms / p90 875ms / max 1035ms). 고치려면 `collect()` 가 공용 deadline 을 들고 각 신호가
  그것을 보게 해야 하는데, 기존 4신호의 발화 조건을 건드리므로 이번 범위 밖이다. 심각도 낮음(측정 여유).
- **`GIT_DIR`/`GIT_WORK_TREE` 상속을 프로덕션 경로에서 스크럽하지 않는다** — 테스트는 스크럽한다
  (`session-brief.test.js:14`). 기존부터 있던 비대칭인데 대상이 사용자 repo 로 넓어져 영향이 커졌다.

# Key Files

- `scripts/session-brief.js` — 라벨 하드코딩 `~/.claude ${behind}커밋 뒤처짐`(L268), 감시 대상 고정
  `repoDir = CLAUDE_BRIEF_REPO || ~/.claude`(L315), 신호 배선 `collect(...)`(L327-330)
- `scripts/session-brief.test.js` — fixture repo spawn 하네스. `run(env)`(L55-66)에 cwd 주입 필요
- `README.md` — 브리프 문서 3곳: L394(스크립트 상세)·L440(hooks.SessionStart)·L622(트리)
- `.github/workflows/lint.yml` — `node --check` + unit test 목록에 이미 등록됨(추가 배선 불필요)

# Blockers

# Acceptance

1. `node scripts/session-brief.test.js` 전체 통과(기존 + 신규 케이스: 뒤처짐만·갈라짐·동기화 무음·
   묵은 미커밋·최신 미커밋 무음·`~/.claude` 자신 제외·비 git 무음)
2. 뒤처진 repo 를 cwd 로 주면 **대상 이름(`<repo>` 또는 `<repo>/<worktree>`)과 기준 ref 가 들어간**
   밀림 줄이 출력된다(관찰)
3. `~/.claude` 대상 기존 N 신호의 문구·동작 불변(기존 테스트 통과 + 출력 육안 대조)
4. 동기화·clean 상태에서 무음(잡음 0)
5. README 3곳 갱신
6. `node --check scripts/session-brief.js` 통과
7. 동기 hook 예산: 새 신호가 추가하는 git spawn 은 **최대 4회**(toplevel+common-dir, upstream 확인,
   left-right count, status), 마감시각 초과 시 조기 반환. 실측으로 확인한다.
8. 파일 머리 주석·README 의 "신호 4종/1~4줄"·kill-switch 목록을 새 신호 포함으로 갱신(codex Minor 1)
9. 터미널에서 stdin 없이 직접 실행해도 즉시 끝난다(TTY 폴백 — hang 금지)
