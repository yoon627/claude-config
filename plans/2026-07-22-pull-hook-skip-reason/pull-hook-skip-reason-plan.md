---
title: pull-hook-skip-reason — SessionStart 자동 pull 이 조용히 skip 되는 문제
status: in_progress
started: 2026-07-22
updated: 2026-08-04
---

# Goal

`settings.json` 의 SessionStart 자동 pull 훅이 게이트에 걸려 아무 일도 안 했을 때 **이유를
말하게** 한다. 지금은 실패와 "이미 최신"이 구분되지 않아 레포가 밀려도 알 수 없다.

# Progress

- 2026-07-22 발견 — worklog 작업 중 `~/.claude` 가 **origin/main 보다 132 커밋 뒤처져** 있는 걸
  확인. 자동 pull 훅이 도는데도 밀려 있었다. 원인은 `settings.json` 미커밋 변경(`effortLevel`)
  으로 `git diff --quiet` 게이트가 실패했고, 체인 끝의 `|| true` 가 이유를 삼킨 것.
- 2026-07-22 이 plan 만 작성해 push (구현 없음 — 사용자 지시).
- 2026-08-04 13일 방치 후 재개. worktree 재생성(`origin/pull-hook-skip-reason` 체크아웃), `origin/main` merge(`97a7452`)로 base 39커밋 지연 해소. **훅 명령이 plan 스냅샷과 문자 그대로 일치함을 확인**(`settings.json` `hooks.SessionStart[0][0]`, 526자) — plan 은 stale 하지 않다. PR 없음, plan-lint 통과.
- 2026-08-04 **A안 확정** — `scripts/*.js` + `node --check` + Unit tests 가 이 repo 의 정착된 훅 진입점 패턴이고(`lint.yml` 에 스크립트 14개 등록), Acceptance #5 도 그 형태를 요구한다. B안(인라인 유지) 폐기.
- 2026-08-04 **plan-review CONDITIONAL**(claude plan-reviewer + codex medium 병행), blocker 4건. 메인이 직접 확인한 것: ① 훅에 **`"async": true`, `"timeout": 30`** 이 있는데 plan 스냅샷이 통째로 누락했다 — 앞선 "훅이 plan 과 문자 그대로 일치" 확인은 `command` **문자열**만 본 것이라 불완전했다. 같은 그룹 `session-brief.js` 는 async 없이 동기이고 그 파일 8번 줄이 `동기 hook(async 면 stdout 이 첫 턴 후 도달)` 을 계약으로 명시 → **이유를 출력해도 세션 시작 시점엔 안 보일 수 있다**(Goal 미달성 위험). ② `CLAUDE_AUTOPULL_OFF` 는 `install-hooks.sh/.ps1`(post-checkout)에만 존재 → **SessionStart pull 은 이 스위치로 안 꺼진다**(기존 불일치). ③ `# Key Files` 가 인용한 `plans/2026-05-13-track-settings-json/` 은 **실존하지 않는다**(`ls`·`git log --all --diff-filter=A` 모두 무결과).
- 2026-08-04 **dirty 게이트 실험** (임시 repo 3케이스, `scratchpad/probe_ffonly.sh`) — 아래 Decisions 에 결과. 열린 질문이던 게이트 존치를 근거 기반으로 종결.

# Next

plan-review 반영 완료, 출력 가시성 (c) 확정 → **구현 착수**. 순서:

1. **신호 N TDD** — `session-brief.test.js` 에 Red 부터. 사유 열거형별 fixture:
   `not-main`/`detached`/`no-origin`/`behind`/`dirty-overlap`, 그리고 **최신이면 무음**.
2. `session-brief.js` 에 신호 N 구현(네트워크 없음, 캐시 `origin/main`, 기존 `git()` timeout 2000·
   예외 격리·`CLAUDE_BRIEF_REPO` override 를 그대로 재사용).
3. `settings.json` 체인에서 dirty 게이트 2개 제거 + `CLAUDE_AUTOPULL_OFF` 존중.
4. 문서 동기화(`README.md` 5곳 — 특히 410 "다음 세션부터 적용"·"dirty 면 skip" 서술).

**테스트는 선례를 그대로 미러링한다**(`session-brief.test.js` 기존 패턴): `fs.mkdtempSync` +
`git init` 으로 실제 git fixture, `spawnSync` 로 관찰, `CLAUDE_BRIEF_REPO` 로 repo 주입,
`GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE` 스크럽 + `commit.gpgsign=false`. **신규 테스트 파일 없음.**

이어받기: `/wt pull-hook-skip-reason` → `/c`.

# Decisions

## 현상 (확정)

`settings.json` `hooks.SessionStart[0].hooks[0].command` 는 한 줄 `&&` 체인이다:

```
git -C ~/.claude rev-parse --abbrev-ref HEAD 2>/dev/null | grep -qx main
  && git -C ~/.claude diff --quiet 2>/dev/null
  && git -C ~/.claude diff --cached --quiet 2>/dev/null
  && before=$(git -C ~/.claude rev-parse HEAD 2>/dev/null)
  && git -C ~/.claude pull --ff-only --quiet origin main >/dev/null 2>&1
  && after=$(git -C ~/.claude rev-parse HEAD 2>/dev/null)
  && [ "$before" != "$after" ]
  && echo "~/.claude updated from origin/main (...)"
  || true
```

**2026-08-04 정정 — 위 스냅샷은 `command` 문자열만이다.** 실물 훅 항목에는 `"timeout": 30`,
`"statusMessage": "Checking ~/.claude for updates"`, **`"async": true`** 가 함께 있다. 이 누락이
Goal 달성 여부를 좌우한다(아래 `## 출력 가시성` 참조).

체인이 끊기는 지점이 5가지인데 **출력이 전부 동일(무음)** 이다:

| # | 끊기는 지점 | 무음이 옳은가 |
|---|---|---|
| 1 | main 브랜치 아님 | 의도된 skip — 다만 왜 안 도는지 모름 |
| 2 | **unstaged 변경 있음** (`diff --quiet`) | **아니다 — 이번 사고의 원인** |
| 3 | staged 변경 있음 (`diff --cached --quiet`) | 아니다 |
| 4 | `pull --ff-only` 실패 (diverge·네트워크·origin 부재) | 아니다 — `>/dev/null 2>&1` 로 에러까지 삼킴 |
| 5 | `before == after` (이미 최신) | **그렇다** — 정상 무음 |

5번만 무음이어야 하는데 2·3·4 가 5번과 구분되지 않는다. 사용자는 "훅이 돌고 있으니 최신"
이라고 믿게 된다(실제로 132커밋 밀림).

## 출력 가시성 (2026-08-04 plan-review B1 — 미결, `# Blockers` 결정 1)

훅이 `"async": true` 라 **stdout 이 첫 턴 이후에 도달**한다(`scripts/session-brief.js:8` 이 계약으로
명시: `동기 hook(async 면 stdout 이 첫 턴 후 도달)`). 즉 사유 한 줄을 아무리 잘 만들어도 async 인 채로는
사용자가 세션 시작 시점에 못 본다 → "이유를 말하게 한다"는 Goal 이 절반만 달성된다.

**→ (c) 채택 (2026-08-04 사용자 결정).** 결과적으로 **A안(신규 스크립트 분리)은 대체·폐기**된다:
진단·출력은 이미 동기이고 이미 테스트되는 `session-brief.js` 가 맡고, 네트워크 pull 은 async
인라인 체인으로 남는다. 그래서 신규 스크립트·CI 등록·README 훅 진입점 추가가 **모두 불필요**해진다.

작업 분해:
1. **`session-brief.js` 에 신호 N 추가**(동기·네트워크 없음, 캐시된 `origin/main` 으로 판정) —
   `~/.claude` 가 뒤처졌는데 자동 pull 이 안 먹고 있으면 그 **이유**를 한 줄로. 사유 열거형:
   `not-main`/`detached`/`no-origin`/`behind`/`dirty-overlap`. 최신이면 **무음**.
2. **`settings.json` async 체인에서 dirty 게이트 2개 제거** + `CLAUDE_AUTOPULL_OFF` 존중.
   체인은 "시도만" 하고, *왜 안 됐는지*는 다음 세션 시작에 신호 N 이 동기로 말한다.
3. 테스트는 `session-brief.test.js` 에 추가(기존 git fixture 패턴 재사용 — 신규 테스트 파일 없음).

이 구성의 핵심 이점: **네트워크를 타는 쪽은 계속 async 라 hang 위험이 0**이고
(`wiki/pages/decision/git-hook-network-safety.md` 결정 유지), 사용자가 보는 쪽은 동기라 세션 시작에
즉시 보인다. B3(사유 판정)도 자연히 해결된다 — 신호 N 은 애초에 stderr 파싱이 아니라 상태 판정이다.

세 갈래가 있고 어느 쪽이든 대가가 있다:
- **(a) async 유지** — 안전(하니스가 timeout 으로 감싼다)하지만 사유가 첫 턴 뒤에 뜬다. Acceptance 를
  "첫 턴 이후라도 1회 표시"로 낮춰야 한다.
- **(b) 동기 전환** — 세션 시작에 보이지만 `wiki/pages/decision/git-hook-network-safety.md` 의
  "async+timeout 이 감싸므로 hang 없음" 결정이 **무효화**된다. 그러면 `scripts/install-hooks.sh:70-86`
  의 hang 방지 3종(`GIT_TERMINAL_PROMPT=0` · SSH `ConnectTimeout` · HTTP low-speed)과 20초 자체
  워치독을 **그대로 미러링해야** 한다(macOS 는 `timeout(1)` 부재).
- **(c) 분리** — 네트워크 없는 로컬 판정(브랜치 아님·dirty↔원격 충돌·behind N)은 이미 **동기**인
  `session-brief.js` 에 신호로 얹고, 네트워크 pull 은 async 로 둔다. 동기 출력 경로를 얻으면서 hang
  위험 0, CI·README 신규 등록 0건. 대신 pull *실패* 사유 일부는 여전히 다음 턴에 뜬다.

## 왜 working tree 가 만성적으로 dirty 한가 (근본 원인 후보)

`settings.json` 은 **tracked** 다(커밋 `543455b`, 2026-05-14 `Track settings.json directly; add
secret guard hooks` 에서 의도적으로 전환. 머신별·민감 설정은 gitignored `settings.local.json` 으로 분리).

그런데 Claude Code CLI 자신이 `/config` 등으로 `settings.json` 에 쓴다 — 이번 사고에서 dirty 를
만든 것도 CLI 가 넣은 `"effortLevel": "xhigh"` 였다. 즉 **도구가 자동으로 고치는 파일을 tracked
로 두고, 그 파일이 더러우면 자동 pull 을 끄는** 구조라 skip 이 잦아진다.

**2026-08-04 정정 (리뷰)**: "만성적/상시"는 과장이다 — 지금 `~/.claude` 는 clean 하고 `effortLevel`
은 `high` 로 커밋돼 있다(`78a6715`). 다만 메커니즘은 실재하고 **출처가 CLI 단독도 아니다**
(`f4011a5 chore(settings): Orca agent-hooks 주입분 반영` 처럼 외부 도구도 쓴다) → **"간헐적·다중
출처"** 가 정확하다.

→ **deferral 근거도 갱신한다.** 원래는 "A안은 증상 가시화니 근본 원인은 나중에"였는데, dirty 게이트를
없애기로 한 지금은 **dirty 가 staleness 의 원인 경로에서 빠진다**(더 이상 pull 을 막지 못한다). 남는 건
커밋 노이즈뿐이므로 deferral 이 오히려 더 정당해졌다. 3 Whys 상 근본 원인은 "게이트가 dirty 를 pull
차단 조건으로 삼은 설계"이고 **그건 이번에 고친다**. 키 분리는 `# Deferred` 유지.

## 방향

- ~~**A안: 훅 본문을 `scripts/` 의 신규 스크립트로 분리**~~ → **2026-08-04 (c) 채택으로 대체·폐기**.
  A안의 목적은 "테스트·리뷰 가능한 곳에 판정 로직을 두는 것"이었는데, (c)는 그 로직을 **이미 동기이고
  이미 테스트되는** `session-brief.js` 에 얹어 같은 목적을 신규 파일 0개로 달성한다. async 체인은
  판정을 갖지 않고 "시도만" 하므로 분리할 로직 자체가 없어진다.
- ~~**B안: 인라인 유지 + 분기마다 `|| echo`**~~ → 폐기(같은 이유). 다만 (c)에서도 체인은 인라인으로
  남되, **게이트를 덜어내 더 짧아진다**(판정을 안 하므로).
- **fail-open 유지 필수** — 훅이 세션 시작을 막으면 안 된다(README 의 "모두 fail-open" 규약).
  이유를 출력하되 exit code 는 항상 0.
- **dirty 게이트는 제거한다 — 항상 pull 을 시도한다** (2026-08-04 실험 + 사용자 결정으로 종결).
  근거(임시 repo 3케이스 실측, `scratchpad/probe_ffonly.sh`):

  | 상황 | `git pull --ff-only` 결과 |
  |---|---|
  | dirty 파일 ≠ 원격 변경 파일 | exit 0, ff 완료, **로컬 변경 보존** |
  | dirty 파일 = 원격 변경 파일 | exit 1 `local changes would be overwritten by merge: Aborting`, **변경 보존·HEAD 불변** |
  | staged(무관 파일) | exit 0, ff 완료, **staged 보존** |

  즉 **git 자체가 보호하므로 게이트는 중복 방어**이고, 로컬 변경이 유실되는 경로가 없다. 반면
  게이트를 두면 사고 당시처럼 origin 이 `settings.json` 을 건드리지 않은 경우에도 무조건 skip 되어
  레포가 계속 밀린다. 게이트 제거는 *가시화*를 넘어 **staleness 자체를 고친다**.
  - 이 결정으로 skip 사유 분류가 바뀐다: dirty 는 더 이상 *사전* skip 사유가 아니라 **pull 실패
    사유**로 보고된다(`# Acceptance` 1번 수정 반영).
  - 원래 사고 사례(origin 이 `settings.json` 변경 + 로컬 dirty)는 여전히 거부되지만, 이제
    **이유가 출력**되므로 사용자가 알아채고 커밋·stash 할 수 있다(단 가시성은 위 `## 출력 가시성`
    결정에 달렸다).
  - **표현 하향 (2026-08-04 리뷰)**: "로컬 변경이 유실되는 경로가 없다"는 과일반화다 →
    **"검증한 4케이스에서 유실 없음"**. 리뷰가 4번째 케이스를 추가 실측했다(원격이 새로 추가하는
    파일과 같은 이름의 untracked 로컬 파일 → `Please move or remove them` · rc=1 · 파일 보존).
    submodule·sparse-checkout·pull 중 CLI 동시 write 는 미검증.
  - **신규 부작용 (리뷰 지적, 반드시 문서화)**: 게이트를 없애면 세션 중 base repo 의
    `scripts/*.js`·`skills/`·`CLAUDE.md` 가 실제로 교체되는 빈도가 급증한다. 훅 스크립트는 매
    이벤트마다 파일에서 읽히므로 **같은 세션 안에서 동작이 바뀐다** → `README.md:410` 의 "pull 내용은
    다음 세션부터 적용" 서술이 거짓이 되므로 같이 고쳐야 한다.
  - **동시 세션 race (리뷰 지적)**: 이 사용자는 worktree 세션을 상시 병행한다. 게이트 제거로 매 세션이
    반드시 네트워크 pull 을 시도하므로 `index.lock` 경합 확률이 오른다. lock 계열 실패는 `busy` 로
    분류해 **무음/저노이즈** 처리한다 — 정상 상황에서 사유가 뜨면 알람 피로로 다시 무시하게 되어
    원래 문제가 재발한다. rebase/merge/bisect 중 skip 가드도 `install-hooks.sh:60-62` 대로 넣는다.

## 사유 판정은 stderr 파싱이 아니라 사전 상태 판정 (2026-08-04 리뷰 B3)
4분류는 전부 `git pull` **exit 1** 로 수렴하므로 stderr 문자열 매칭이 필요해지는데, 이는 git 버전·
`LANG` 에 따라 깨진다. 대신 pull *전에* 상태로 판정한다: `git remote get-url origin`(origin 부재) /
`rev-parse --abbrev-ref HEAD`(브랜치 아님 · **detached 는 `HEAD` 를 반환하므로 별도 사유**) /
fetch 후 `rev-list origin/main..HEAD`(diverge) / `diff --name-only` ∩ `diff --name-only HEAD..origin/main`
(덮어쓰기 충돌). 부득이 stderr 를 쓰면 `LC_ALL=C` 고정 + 미분류는 `unknown` 폴백.
결과 모델을 **열거형으로 먼저 정의**한다(codex 제안): `not-main`/`detached`/`no-origin`/`busy`/
`up-to-date`/`updated`/`dirty-overlap`/`diverged`/`network-or-auth`/`unknown-failure`.

## kill-switch 와 자기 배포 채널 위험 (2026-08-04 리뷰 B4)
- **`CLAUDE_AUTOPULL_OFF=1` 을 SessionStart 에도 적용한다.** 현재 이 스위치는 post-checkout 만 끄는데
  (`install-hooks.sh:57`), 사용자는 "auto-pull 껐다"고 믿는다 — **기존 불일치**를 같이 닫는다.
  선행 plan `plans/2026-07-05-main-autopull/main-autopull-plan.md:57` 이 이미 P3 로 지적한 항목이다.
- **이 훅은 자기 자신의 업데이트 배포 경로다.** 새 스크립트가 pull 전에 throw 하거나 node 가 없으면
  `|| true` 로 무음 exit 0 → **모든 머신이 조용히 업데이트를 멈춘다**. 이번 사고(132커밋)와 같은
  실패 모드를 한 층 위에서 재생산하는 것이다. 따라서 ① **pull 시도를 판정보다 먼저** 배치 ② node 내부
  catch 에서도 **한 줄은 출력**(fail-open ≠ fail-silent) ③ `|| true` 는 node 부재 대비로만 남기고 그
  경우도 stderr 한 줄 ④ CI `node --check` 등록(Acceptance #5).
- **rollback 3단** (plan 에 없던 항목): ① `CLAUDE_AUTOPULL_OFF=1`(즉시·머신별·파일 수정 없음)
  ② `settings.json` 훅 command 를 이전 인라인 체인으로 revert(1커밋) ③ 이미 pull 된 내용은
  `git reflog` 와 출력된 `before` SHA 로 복원. **`reset --hard` 를 rollback 절차로 쓰지 않는다**(§8).
  Acceptance #3 의 `before→after` 출력이 이 복원의 기준점임을 명시한다.

# Key Files

- `settings.json` — `hooks.SessionStart[0].hooks[0].command` (수정 대상).
- `scripts/notify-hook.js` · `scripts/session-brief.js` — 훅 진입점 스크립트 선례(형식·fail-open).
- `.github/workflows/lint.yml` — 새 스크립트는 `node --check` + `Unit tests` 목록에 추가해야 함.
- `README.md` `### scripts/` — 훅 진입점 목록에 등재 필요(문서 동기화).
- ~~`plans/2026-05-13-track-settings-json/`~~ → **2026-08-04 정정: 실존하지 않는 인용**(`ls`·
  `git log --all --diff-filter=A` 무결과). 실제 근거는 커밋 `543455b`(2026-05-14)
  `Track settings.json directly; add secret guard hooks`.
- `scripts/install-hooks.sh:51-95` — **미러링 대상 선례**. post-checkout main-autopull 의 hang 방지
  3종 + 20초 워치독 + rebase/merge/bisect 가드 + `CLAUDE_AUTOPULL_OFF` kill-switch.
- `plans/2026-07-05-main-autopull/main-autopull-plan.md` — 동일 문제의 선행 plan(게이트 순서·fixture
  테스트·detached HEAD·P3 rollback 지적).
- `wiki/pages/decision/git-hook-network-safety.md` — "SessionStart 는 async+timeout 이라 hang 없음"
  확정 기록. **동기 전환 시 이 결정이 무효화되므로 같이 갱신**.
- `scripts/session-brief.js` — 동기 훅 선례이자 (c)안 채택 시 신호를 얹을 대상.

# Blockers

(없음 — 2026-08-04 출력 가시성 결정 (c) 채택으로 해소. 내용은 `# Decisions` 의 `## 출력 가시성`.)

<!-- 해소된 blocker 기록

1. **출력 가시성 전략** (`## 출력 가시성` 의 (a)/(b)/(c) 중 택1) — 훅이 `"async": true` 라 사유가
   첫 턴 이후에 도달한다. (a) async 유지+Acceptance 하향 / (b) 동기 전환+hang 방지 미러링 /
   (c) 로컬 판정은 동기 `session-brief.js` 에, 네트워크 pull 은 async 유지. 이 선택이 구조·스코프·
   Acceptance 를 모두 바꾸므로 먼저 확정해야 한다.

나머지 blocker(사유 판정 방식·kill-switch·자기 배포 채널 방어·rollback)는 `# Decisions` 에 반영 완료. -->

# Acceptance

1. ~~main 아님 / unstaged dirty / staged dirty / pull 실패~~ → **2026-08-04 수정**(dirty 게이트
   제거로 분류가 바뀜). **main 아님 / origin 부재·네트워크 실패 / pull 거부(로컬 변경 덮어씀) /
   ff 불가(diverge)** 각각에서 **서로 다른 사유 한 줄**이 출력된다. dirty 는 사전 skip 사유가
   아니라 pull 거부 사유로만 나타난다.
2. 이미 최신이면 **무음**(현재 동작 유지 — 매 세션 잡음 금지).
3. 실제로 pull 되면 기존과 같은 형식으로 before→after 를 보고한다.
4. 어떤 경로에서도 exit code 0 (fail-open) — 세션 시작을 막지 않는다.
5. 새 스크립트가 CI(`node --check` + `Unit tests`)에 등록되고 단위테스트가 위 분기를 덮는다.
6. ~~README `### scripts/` 1곳~~ → **2026-08-04 확대(리뷰)**. 실제 갱신 지점: `README.md` **5곳**
   (337 훅 진입점 열거 · 368 부근 스크립트 불릿 · **410 "가드 실패 무음"·"dirty 면 skip" 서술이
   거짓이 됨** · 470 rollback 절 · 579 트리) + `wiki/pages/decision/git-hook-network-safety.md`
   (동기 전환 시) + `wiki/index.md`(§11 동반) + `.github/workflows/lint.yml` **2곳**
   (`node --check` 에 `.js`·`.test.js`, `Unit tests` 에 테스트).
7. **kill-switch**: `CLAUDE_AUTOPULL_OFF=1` 이면 SessionStart pull 도 skip (테스트 통과).
8. **자기 배포 채널 방어**: 스크립트가 예외로 죽어도 한 줄은 출력되고 exit 0 (테스트 통과).
9. **실제 관찰**(정적 점검 불가, CLAUDE.md §3-5): 마커 문구를 넣고 **새 세션 1회**를 열어 사유 줄이
   실제로 어디에(세션 시작 / 첫 턴 이후) 뜨는지 눈으로 확인. async 유지 결정의 전제를 실증한다.

# Deferred

- **CLI 가 쓰는 키를 `settings.local.json` 으로 분리**할지 — `effortLevel`·`theme`·
  `preferredNotifChannel` 처럼 CLI 가 자동으로 고치는 키가 tracked 파일에 있으면 working tree 가
  상시 dirty 해진다. effort 값은 동작에 영향이 있어 사용자 결정이 필요하다(과거에 설정 통합 중
  effort 값이 조용히 바뀐 전례가 있어 더 조심해야 함).
- 훅이 `--rebase` 가 아니라 `--ff-only` 인 점 — 사용자는 `pull --rebase` 로 기억하고 있었다.
  ff-only 가 안전하므로 바꿀 이유는 없지만, 문서·기억과 실제가 어긋나 있으니 README 에 명시할지.

# Workflow Findings

- 자동화가 **조용히 실패**하면 사용자는 "돌고 있으니 괜찮다"고 믿는다. 이번엔 132 커밋이 밀려
  `jira-worklog` 스킬이 로컬에 없는 것처럼 보였고, "스킬이 존재하지 않는다"는 잘못된 진단까지
  갔다(remote 확인 후 정정). fail-open 훅은 **실패해도 조용하면 안 되고, 이유를 남겨야** 한다.
