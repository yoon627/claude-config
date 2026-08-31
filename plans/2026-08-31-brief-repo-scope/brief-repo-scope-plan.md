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
# Next

1. code-reviewer(subagent) + codex code 리뷰 반영.
2. simplify 점검.
3. `~/.claude` main 에 머지(ff-only) — 머지 후에는 새 세션에서 실제로 뜨는지 관찰.
4. 재현 검증(선택): WSL 에 knowledge_base 재clone 해 2머신 밀림을 실제로 만들고 브리프가 잡는지 확인.


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
2. 뒤처진 fixture repo 를 cwd 로 주고 브리프를 돌리면 **repo 이름이 들어간** 밀림 줄이 출력된다(관찰)
3. `~/.claude` 대상 기존 N 신호의 문구·동작 불변(기존 테스트 통과 + 출력 육안 대조)
4. 동기화·clean 상태에서 무음(잡음 0)
5. README 3곳 갱신
6. `node --check scripts/session-brief.js` 통과
7. 동기 hook 예산: 새 신호가 추가하는 git spawn 은 **최대 4회**(toplevel+common-dir, upstream 확인,
   left-right count, status), 마감시각 초과 시 조기 반환. 실측으로 확인한다.
8. 파일 머리 주석·README 의 "신호 4종/1~4줄"·kill-switch 목록을 새 신호 포함으로 갱신(codex Minor 1)
9. 터미널에서 stdin 없이 직접 실행해도 즉시 끝난다(TTY 폴백 — hang 금지)
