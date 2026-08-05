---
title: settings-local-keys — CLI 자동 기입 키로 dirty 해지는 tracked settings.json 대응
status: in_progress
started: 2026-08-05
updated: 2026-08-05
---

# Goal

tracked `~/.claude/settings.json` 이 Claude Code CLI·외부 도구의 자동 기입으로 수시로 dirty 해져
SessionStart 자동 pull 이 거부되는 문제의 근본 대응안을 확정한다.
이번 턴은 **조사·계획까지**. 운영 자산(settings·CLAUDE.md) 수정은 승인 후 별도 작업.

# Progress
- 2026-08-05: **사용자 결정 3건** — ① B2 `effortLevel` 은 **그대로 둔다**(env 가 override 해 평소엔 무력하지만 env 미주입 환경의 fallback 은 남긴다) ② 무효 스코프의 권한 규칙을 적용되는 파일로 **병합** ③ worktree 권한 공백은 **`wt` 가 `.claude/settings.local.json` 도 복사**하는 방식으로 해소.
- 2026-08-05: **권한 병합 실행 완료** — `~/.claude/settings.local.json`(58개, cwd=$HOME 전용이라 이 repo 세션엔 무효)의 규칙을 `~/.claude/.claude/settings.local.json` 으로 병합(31 → 83, 추가 52). 중복 2개 제외, **일회성·머신 한정 4개 제외**(죽은 PID `kill -9 4132`, `last reboot *`, `.pkg` 를 내려받는 curl 2개 — 상시 허용에 남길 성질이 아니다). 백업 `.bak`. gitignored 라 커밋 대상 아님.
- 2026-08-05: **새 발견 — worktree 세션은 권한 규칙이 0개다**(이게 권한 프롬프트 빈발의 더 큰 원인일 가능성 ⚠️추정). `.claude/settings.local.json` 은 gitignored 라 worktree 생성 시 안 따라오고, `wt` 는 `.env` 만 복사한다. 그런데 CLAUDE.md §8 은 비trivial 작업을 worktree 에서 하도록 **강제**하므로 실제 작업 경로에서 허용목록이 통째로 빈다. 실측: main repo 83개 / worktree 3곳 **파일 없음** / tracked `settings.json` 8개(유일하게 전 세션 적용).

- 2026-08-05 조사 완료.
  - 최우선 검증 대상이던 후보안(자동 기입 키를 user 스코프 `~/.claude/settings.local.json` 으로 이동)이
    **기술적으로 무효**임을 확인 — 근거는 아래 Decisions D1.
  - CLI/외부도구 자동 기입 키 목록화(D2), `effortLevel` 이중화 실태 확인(D3),
    근본 원인 3 Whys(D4), 대안 비교·추천(D5) 완료.
  - 코드 변경 없음. 이 plan 파일만 추가.

# Next

사용자 결정 대기 (Blockers B1·B2). 결정되면 별도 worktree 에서 dlc 로 진행:
1. B1 승인 시 — SessionStart pull 훅에 `--autostash` 추가 + README 해당 항목 동기화.
2. B2 결정에 따라 tracked `effortLevel` 유지/삭제.
3. 어느 쪽이든 `README.md` 약 101줄의 Issue #19487 경고 문구를 D1 의 실제 기전으로 교정.

# Decisions

## D1. Issue #19487 검증 — 후보안 폐기 (✅확실)

**결론: 키를 `~/.claude/settings.local.json` 으로 옮기는 후보안은 무효다. 채택하면 안 된다.**

### 로컬 증거 — Claude Code 2.1.222 네이티브 바이너리 코드 직접 확인

`/Users/jongyoonlee/.local/share/claude/versions/2.1.222` 의 문자열에서 설정 소스 열거와
경로 해석 함수를 그대로 읽었다. 설정 소스는 **정확히 6개**이고 user 스코프 local 소스는 없다.

| 소스 | 실제 경로 |
|---|---|
| `policySettings` | managed settings (엔터프라이즈) |
| `flagSettings` | `--settings <path>` 로 준 파일 |
| `userSettings` | `<CLAUDE_CONFIG_DIR>/settings.json` = `~/.claude/settings.json` |
| `projectSettings` | `<cwd>/.claude/settings.json` |
| `localSettings` | `<canonical git root>/.claude/settings.local.json` (+ cwd≠gitroot 일 때 legacy `<cwd>/.claude/settings.local.json` 병행) |
| `cliArg` | CLI 플래그 |

경로 해석 함수(난독화된 이름 그대로): `Vlt(source, ctx)` 가 소스→경로,
`zVr` 이 소스→기준 디렉토리(`localSettings` 는 `Eze(cwd, canonicalGitRoot)`),
`Dte` 가 파일명(`.claude/settings.local.json`), `Qnr` 이 legacy cwd 기반 경로다.

**따라서 `~/.claude/settings.local.json` 은 "user 스코프 local 파일"이 아니라
"프로젝트 루트가 `$HOME` 인 세션의 project-local 파일"일 뿐이다.**
`$HOME` 은 git repo 가 아님을 확인했으므로(`git -C ~ rev-parse` 실패, `~/.git` 부재),
이 파일은 **cwd 가 정확히 `$HOME` 인 세션에서만** 읽힌다.
`~/.claude` repo 세션에서는 git root 가 `/Users/jongyoonlee/.claude` 이므로
localSettings = `~/.claude/.claude/settings.local.json` 이다(현재 31개 `permissions.allow` 보유).
worktree 세션은 git root 가 worktree 디렉토리라 **worktree 마다 별도 local 파일**이 된다.

부수 확인: `enabledPlugins`/`extraKnownMarketplaces` 를 `settings.json`+`settings.local.json`
쌍으로 훑는 별도 루프가 있으나 대상 디렉토리는 `--add-dir` 로 추가된 디렉토리 목록이라
`~/.claude` 를 특별 취급하지 않는다. 즉 우회 경로도 없다.

### 외부 증거 (researcher subagent, 2026-08-05 웹 조사)

- 공식 문서(`code.claude.com/docs/en/settings`)의 스코프 목록에 **user-level `settings.local.json` 은 없다**.
  User 스코프는 `~/.claude/settings.json` 하나뿐. ✅
- 그 파일을 만들어 달라는 **open feature request** 가 따로 있다 —
  anthropics/claude-code #81990 (2026-07-28, Open): `~/.claude` 에는 `settings.local.json` 에
  해당하는 것이 없다는 취지. 즉 미지원이 현행. ✅
- #19487 은 실재: 제목 `[Bug] Project settings.local.json overwrites global settings instead of deep merging`
  (2026-01-20, v2.1.12). **closed as not planned**, `stale` 라벨 동반, 연결 PR 없음. ✅
- CHANGELOG 에 이 병합 동작을 고쳤다는 항목 없음. 대신 2.1.211 에서
  local 파일 위치가 starting directory → **git repo root** 로 이동 — 위 바이너리 코드와 정확히 일치. ✅
- 참고: 문서상 일반 병합은 "파일 통째 replace"가 아니라 **키 단위 override**(permission rule 은 스코프 간 merge).

### README 서술 교정 필요 (⚠️ 현재 문서가 틀림)

`README.md` 약 101줄의 경고 "project-level `.claude/settings.local.json` 존재하면
user-level `~/.claude/settings.local.json` 전체가 무시됨" 은
**결론(무시된다)은 맞지만 기전이 틀렸다**. 실제로는 project local 이 user local 을 이기는 게 아니라
**user local 이라는 개념 자체가 없다**. 두 파일이 서로 override 하는 관계가 아니라,
`localSettings` 단일 슬롯이 세션의 git root 에 따라 둘 중 하나로 **해석될 뿐**이다.

### 후보안이 위험한 이유

키를 옮기면 거의 모든 세션에서 **조용히 무시**된다. 에러도 경고도 없다.
특히 `effortLevel` 이 조용히 기본값으로 떨어져 모델 동작이 바뀐다(B2 참조).

### 실증 절차 (미실행 — 필요 시)

바이너리 코드 근거로 충분하다고 판단해 실행하지 않았다. 확인이 더 필요하면 비파괴적으로:
1. 세션에서 `/status` 의 `Setting sources` 줄을 본다 —
   `~/.claude/settings.local.json` 이 목록에 뜨지 않으면 읽히지 않는 것.
   (문서상 "설정을 1개 이상 담고 로드됐을 때만" 표시되므로, 현재 58개 항목이 있는데도 안 뜨면 판정 성립.)
2. 더 엄밀히 하려면 임시 git repo 를 만들어 무해한 키(`spinnerTipsEnabled` 등)를
   두 스코프에 다른 값으로 넣고 `/status`·`/config` 에서 유효값을 관찰한다.
   운영 파일을 건드리지 않도록 `CLAUDE_CONFIG_DIR` 를 임시 디렉토리로 지정해 격리할 것.

## D2. 자동 기입 키 목록 (근거 커밋 + 바이너리)

**출처가 CLI 단독이 아니다** — 최소 2개 주체가 tracked `settings.json` 에 쓴다.

### (a) Claude Code CLI

바이너리 안에 `/config`·`/model`·`/effort` 가 **userSettings 에 영속 저장하는 키 배열**이 그대로 있다:
`model`, `outputStyle`, `language`, `effortLevel`, `fastMode`, `alwaysThinkingEnabled`,
`spinnerTipsEnabled`, `prefersReducedMotion`, `promptSuggestionEnabled`, `awaySummaryEnabled`,
`precomputeCompactionEnabled`, `switchModelsOnFlag`, `autoUpdatesChannel`, `viewMode`,
`syntaxHighlightingDisabled`, `useAutoModeDuringPlan`, `enableWorkflows`, `disableWorkflows`,
`disableArtifact`, `enableArtifact`, `workflowKeywordTriggerEnabled`, `respondToBashCommands`,
`autoCompactWindow`, `cleanupPeriodDays`, `forceLoginMethod`
— 여기에 `permissions.defaultMode`, `worktree.baseRef` 가 추가된다.
`preferredNotifChannel` 은 `/config` 의 알림 채널 변경이 userSettings 에 쓴다(바이너리 문자열 확인).

근거 커밋:

| 커밋 | 날짜 | 근거 |
|---|---|---|
| `7563bd7` | 2026-06-02 | 커밋 메시지가 직접 명시 — "Claude Code auto-writes these into settings.json". `skipWorkflowUsageWarning` 추가 + hook 키 순서가 CC 재직렬화로 바뀐 것을 그대로 반영 |
| `78a6715` | 2026-08-03 | `effortLevel` xhigh→high (사람이 고쳤지만 이 키 자체는 `/effort` 가 쓰는 키) |
| `d758165` | 2026-06-12 | `effortLevel`·`model`·`preferredNotifChannel` 동반 변경 |
| `5b896c8` | — | `skipDangerousModePermissionPrompt` 활성 반영 |
| `1df164a` | — | `/doctor` 점검 반영 — `permissions.defaultMode`, `enabledPlugins` |

현재 tracked `settings.json` 에 실재하는 자동 기입 계열 키:
`effortLevel`, `theme`, `preferredNotifChannel`, `tui`,
`skipDangerousModePermissionPrompt`, `skipWorkflowUsageWarning`,
`enabledPlugins`, `extraKnownMarketplaces`, `permissions.defaultMode`.

⚠️ `theme` 과 `tui` 는 위 배열에 없다 — 다른 경로로 저장된다. 정확한 write 경로는 **미확인(❌모름)**.
(둘 다 표시 전용이라 이번 판단에 영향 없음.)

### (b) 외부 도구 — Orca 터미널 통합

`f4011a5` (2026-08-03): Orca 가 `hooks` 에 +106줄을 자동 주입한 것을 그대로 커밋했다.
CLI 만 막아도 dirty 는 계속 생긴다는 뜻 — **키 이동/삭제로는 원인을 못 없앤다.**

### 참고 — 현재 상태

조사 시점 `~/.claude/settings.json` 은 HEAD 와 **완전히 동일(clean)**했다.
dirty 는 상시가 아니라 간헐적이다.

## D3. `effortLevel` 이중화 — env 가 이긴다 (✅확실)

`env.CLAUDE_CODE_EFFORT_LEVEL` 이 `effortLevel` 키를 override 한다는 README 약 409줄 서술은 사실이다.
바이너리 문자열이 직접 말한다:
"Not applied: `CLAUDE_CODE_EFFORT_LEVEL=…` overrides effort this session",
"Cleared effort from settings, but … `CLAUDE_CODE_EFFORT_LEVEL=…` still controls this session".

따라서 현재 tracked `effortLevel` 은 같은 파일의 `env.CLAUDE_CODE_EFFORT_LEVEL` 이 있는 한 **무력**이다.
다만 완전히 무의미하지는 않다 — env 가 주입되지 않는 경로(다른 머신, env 를 물려받지 않는 실행 컨텍스트)에서는
fallback 으로 작동한다. 삭제 결정은 B2 참조.

## D4. 근본 원인 (3 Whys)

1. **왜 자동 pull 이 거부되나?** → `git pull --ff-only` 가 로컬 변경을 덮어쓰게 되므로 거부.
2. **왜 로컬 변경이 생기나?** → CC 가 user 스코프 설정을 쓸 수 있는 파일이 `~/.claude/settings.json`
   **하나뿐**이고(D1), 외부 도구(Orca)도 같은 파일에 주입한다(D2b).
3. **왜 그게 pull 을 막나?** → 그 파일이 tracked 이고, **들어오는 커밋도 같은 파일을 건드릴 때만** 거부된다.
   즉 실패는 "자동 기입 발생" ∧ "origin/main 이 settings.json 을 변경" 이 겹칠 때만 난다.

→ **자동 기입은 원천 차단이 불가능하다**(리다이렉트할 대상 파일이 존재하지 않음).
그러므로 근본 대응은 "쓰기를 막기"가 아니라 **"pull 이 로컬 변경을 안전하게 비켜가게 하기"** 쪽이다.

## D5. 대안 비교

| # | 안 | 문제를 푸는가 | 위험 | 비용 |
|---|---|---|---|---|
| A | 자동 기입 키를 `~/.claude/settings.local.json` 으로 이동 | ❌ **무효** (D1) | 높음 — 조용한 무시, effort 변동 | — |
| B | tracked `effortLevel` 삭제 | 부분 — dirty 빈도만 소폭↓ | 중 — env 없는 환경의 fallback 상실 | 낮음 |
| C | pre-commit 훅으로 해당 키를 커밋에서 제외 | ❌ pull 실패와 무관(커밋 시점 문제가 아님) | 낮음 | 중 |
| D | **SessionStart pull 을 `--autostash` 로** | ✅ 근본 — 누가 쓰든 무관하게 해소 | 낮~중 — 재적용 시 충돌 가능(문서 명시) | 낮음 (1토큰) |
| E | `settings.json` untrack + 템플릿/동기화 스크립트 | ✅ 하지만 이 repo 의 존재 목적을 훼손 | 높음 | 높음 |
| F | 현상 유지 — 실패 시 사람이 처리 | ❌ | — | 0 |

### 추천: D (필요 시 B 병행)

`git pull --autostash` 는 이 머신의 git 2.50.1 에서 지원되며(`git pull --help` 확인),
문서가 명시적으로 "dirty worktree 에서 실행할 수 있다"고 말한다.
임시 stash 를 `MERGE_AUTOSTASH` 로 기록하고 작업 후 재적용한다.
현재 훅은 이미 rebase/merge/bisect 진행 중이면 건너뛰는 가드가 있어 조합상 안전하다.

문서화된 주의: 성공적 merge 뒤 stash 재적용에서 non-trivial 충돌이 날 수 있다.
이 훅은 `--ff-only` 라 원격이 settings.json 을 바꾸고 로컬도 같은 줄을 바꿨을 때가 그 경우다.
그때 변경이 **유실되지는 않고** stash 로 남지만, 조용히 실패하면(현재 훅은 `2>&1 >/dev/null`)
사용자가 모를 수 있으므로 **충돌 시 알림을 내는 것을 구현 범위에 포함**해야 한다.

B 는 D 의 대체가 아니라 보조다. 단독으로는 Orca 주입(D2b)을 못 막는다.

# Key Files

- `~/.claude/settings.json` — tracked. userSettings 소스. 자동 기입 대상. `hooks.SessionStart[0]` 에 자동 pull.
- `~/.claude/settings.local.json` — gitignored, `permissions.allow` 만 58개.
  **D1 에 따르면 cwd 가 `$HOME` 인 세션에서만 읽힌다** → 사실상 죽은 파일일 가능성(별도 확인 필요, `# Deferred`).
- `~/.claude/.claude/settings.local.json` — gitignored, `permissions.allow` 31개.
  `~/.claude` repo 세션의 실제 localSettings.
- `README.md` 약 101줄 — Issue #19487 경고. **기전 서술 오류, 교정 대상**(D1).
- `README.md` 약 409줄 — `env.CLAUDE_CODE_EFFORT_LEVEL` override 서술. **정확함**(D3).
- `.gitignore` — whitelist 방식. `settings.local.json` 은 belt-and-suspenders 로 ignore.
- `scripts/session-brief.js` — 세션 브리프. pull 실패 사유 노출 경로.

# Blockers

## B1. SessionStart pull 훅에 `--autostash` 를 넣을 것인가 — 사용자 결정 필요

운영 자산(`settings.json`) 변경이라 CLAUDE.md §1 상 명시 승인 없이는 못 건드린다.
결정할 것:
- (a) `--autostash` 도입 여부.
- (b) 도입 시 stash 재적용 충돌을 어떻게 알릴지 — 현재 훅은 출력을 전부 죽이고 있어
  충돌이 나도 조용하다. 알림 없이 도입하면 "변경이 사라진 것처럼 보이는" 새 실패 모드가 생긴다.

## B2. ~~tracked `effortLevel` 삭제 여부~~ → **2026-08-05 결정: 그대로 둔다** (해소)

- 사실관계: 같은 파일의 `env.CLAUDE_CODE_EFFORT_LEVEL` 이 이 키를 override 한다(D3, ✅확실).
  현재 두 값은 일치한다.
- **전례 경고**: 과거 설정 통합 중 effort 값이 조용히 바뀐 적이 있다.
  `78a6715` 은 `xhigh` 가 WebSearch/WebFetch 보조 모델에서 400 을 유발해 웹 검색이 통째로 막힌 사고를
  뒤늦게 잡은 커밋이다. effort 는 **모델 동작에 실제 영향**이 있고 증상이 즉시 드러나지 않는다.
- 그래서 이건 "무력한 값이니 지워도 된다"로 자동 처리하면 안 된다. 선택지:
  - (i) 유지 — env 미주입 환경의 fallback 보존. dirty 빈도 이득은 포기.
  - (ii) 삭제 — 단일 소스화(env 하나). 대신 env 를 안 물려받는 실행 경로에서 CC 기본 effort 로 떨어진다.
  - (iii) 반대로 `env` 쪽을 지우고 키만 남긴다 — ❌ 비권장. 그러면 `/effort` 한 번에 tracked 파일이
    dirty 해져 지금 문제가 악화된다.
- 어느 쪽이든 README 두 항목(101줄·409줄)과 같은 브랜치에서 동기화해야 한다.

## B3. (확인만) 후보안 폐기에 이견이 있는지

D1 이 맞다면 원래 요청의 접근 자체가 성립하지 않는다.
바이너리 코드 + 공식 문서 + open FR #81990 이 같은 방향을 가리키므로 확신도는 ✅이지만,
사용자가 다른 근거를 갖고 있다면 진행 전에 말해달라.

# Acceptance

(구현 단계 진입 시 적용 — 이번 턴은 조사·계획이라 미적용)

1. B1 승인안대로 `settings.json` 의 SessionStart pull 훅이 수정되고,
   dirty `settings.json` 상태에서 실제로 pull 이 성공함을 **실행·관찰**로 확인.
2. stash 재적용 충돌 시 사용자에게 보이는 메시지가 실제로 출력됨을 재현 시나리오로 확인.
3. B2 결정이 `settings.json` 과 `README.md` 두 항목에 모순 없이 반영됨.
4. `README.md` 약 101줄의 #19487 경고가 D1 의 실제 기전으로 교정됨.
5. `node scripts/plan-lint.js` 통과 + 이 plan 의 `status` 가 결과에 맞게 갱신됨.

# Deferred

- `~/.claude/settings.local.json` (58개 `permissions.allow`) 이 D1 에 따라 사실상 읽히지 않는다면
  그 권한들은 현재 무효다. 심각도 중 — 권한 프롬프트가 예상보다 자주 뜨는 원인일 수 있다.
  별도 작업으로 `/status` 의 `Setting sources` 확인 후 `~/.claude/.claude/settings.local.json` 으로
  이관할지 판단할 것. (이번 스코프 밖 — 운영 자산 수정)
- `theme`·`tui` 의 write 경로 미확인(❌모름). 표시 전용이라 이번 판단에는 영향 없음.

# Workflow Findings

- README 에 외부 issue 요지를 적어둘 때 **기전까지 단정하면 틀릴 수 있다**(D1).
  #19487 은 "user local 이 project local 에 진다"로 읽혔지만 실제로는 "user local 이라는 소스가 없다"였다.
  결론이 우연히 같아서 1년 가까이 드러나지 않았다.
  → 외부 issue 인용은 "관측된 증상"과 "추정 기전"을 분리해 적을 것.
