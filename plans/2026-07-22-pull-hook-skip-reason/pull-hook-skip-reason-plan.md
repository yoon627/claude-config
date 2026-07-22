---
title: pull-hook-skip-reason — SessionStart 자동 pull 이 조용히 skip 되는 문제
status: in_progress
started: 2026-07-22
updated: 2026-07-22
---

# Goal

`settings.json` 의 SessionStart 자동 pull 훅이 게이트에 걸려 아무 일도 안 했을 때 **이유를
말하게** 한다. 지금은 실패와 "이미 최신"이 구분되지 않아 레포가 밀려도 알 수 없다.

# Progress

- 2026-07-22 발견 — worklog 작업 중 `~/.claude` 가 **origin/main 보다 132 커밋 뒤처져** 있는 걸
  확인. 자동 pull 훅이 도는데도 밀려 있었다. 원인은 `settings.json` 미커밋 변경(`effortLevel`)
  으로 `git diff --quiet` 게이트가 실패했고, 체인 끝의 `|| true` 가 이유를 삼킨 것.
- 2026-07-22 이 plan 만 작성해 push (구현 없음 — 사용자 지시).

# Next

구현 착수 전 `# Decisions` 의 A안(스크립트 분리) 확정 여부 결정. 그 뒤 TDD 로 판정 로직 작성.

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

## 왜 working tree 가 만성적으로 dirty 한가 (근본 원인 후보)

`settings.json` 은 **tracked** 다(`plans/2026-05-13-track-settings-json/` 에서 의도적으로 전환,
`status: done`. 머신별·민감 설정은 gitignored `settings.local.json` 으로 분리).

그런데 Claude Code CLI 자신이 `/config` 등으로 `settings.json` 에 쓴다 — 이번 사고에서 dirty 를
만든 것도 CLI 가 넣은 `"effortLevel": "xhigh"` 였다. 즉 **도구가 자동으로 고치는 파일을 tracked
로 두고, 그 파일이 더러우면 자동 pull 을 끄는** 구조라 skip 이 상시화된다.

→ 이유 출력(A안)은 증상 가시화이고, dirty 상시화 자체를 없애려면 CLI 가 쓰는 키를
`settings.local.json` 쪽으로 옮기는 별도 판단이 필요하다. **이번 스코프는 A안까지**로 하고,
키 분리는 아래 `# Deferred` 에 둔다(사용자 결정 필요 — effort 값은 동작에 영향).

## 방향

- **A안 (유력): 훅 본문을 `scripts/` 의 스크립트로 분리**하고 settings.json 은 그 스크립트를
  호출만 한다. 근거: 이 레포의 다른 훅 진입점이 전부 그 형태(`notify-hook.js`,
  `session-brief.js`, `dlc-*.js`)이고, CI(`.github/workflows/lint.yml`)가 `node --check` +
  단위테스트를 돌려준다. JSON 문자열 안의 긴 셸 체인은 테스트도 리뷰도 불가능하다.
- **B안: 인라인 유지 + 분기마다 `|| echo`** — settings.json 한 줄이 더 길어지고 테스트 불가.
  A안이 가능하면 택하지 않는다.
- **fail-open 유지 필수** — 훅이 세션 시작을 막으면 안 된다(README 의 "모두 fail-open" 규약).
  이유를 출력하되 exit code 는 항상 0.
- **2번(dirty) 을 skip 사유로 계속 둘 것인가**는 열린 질문. `git pull --ff-only` 는 로컬 변경을
  덮어쓸 때만 거부하므로, 게이트를 없애고 pull 을 시도한 뒤 실패 사유를 출력하는 편이 실제로
  더 자주 최신화된다. 다만 이번 사례는 origin 이 `settings.json` 을 바꿔서 어차피 거부됐을 것.
  → 구현 시 결정하고 이유를 기록한다.

# Key Files

- `settings.json` — `hooks.SessionStart[0].hooks[0].command` (수정 대상).
- `scripts/notify-hook.js` · `scripts/session-brief.js` — 훅 진입점 스크립트 선례(형식·fail-open).
- `.github/workflows/lint.yml` — 새 스크립트는 `node --check` + `Unit tests` 목록에 추가해야 함.
- `README.md` `### scripts/` — 훅 진입점 목록에 등재 필요(문서 동기화).
- `plans/2026-05-13-track-settings-json/` — settings.json 을 tracked 로 만든 선행 결정(done).

# Blockers

# Acceptance

1. main 아님 / unstaged dirty / staged dirty / pull 실패 각각에서 **서로 다른 사유 한 줄**이
   출력된다.
2. 이미 최신이면 **무음**(현재 동작 유지 — 매 세션 잡음 금지).
3. 실제로 pull 되면 기존과 같은 형식으로 before→after 를 보고한다.
4. 어떤 경로에서도 exit code 0 (fail-open) — 세션 시작을 막지 않는다.
5. 새 스크립트가 CI(`node --check` + `Unit tests`)에 등록되고 단위테스트가 위 분기를 덮는다.
6. README `### scripts/` 훅 진입점 목록 동기화.

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
