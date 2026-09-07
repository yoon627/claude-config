---
title: lesson-tracked-config-machine-paths
category: decision
created: 2026-08-12
updated: 2026-09-07
sources:
  - 커밋 f1cbee0 (orca 훅 경로 머신 무관화)
  - 커밋 bde82de (README 동기화 + ~ 표기 통일)
  - 커밋 f4011a5 (2026-08-03, Orca agent-hooks 주입분 반영 — macOS 절대경로 커밋)
  - 커밋 c20c246 (2026-08-04, autopull 개선 — staged 스냅샷이 되돌리고 있던 것)
  - 실측 2026-08-12 (staged 6일 방치, autopull 정지, 훅 3분기 테스트)
  - 커밋 80dbb3c (2026-09-03, gitkraken marketplace 절대경로를 이 페이지 근거로 제외)
  - 커밋 3a11a92 (2026-09-04, 그 제외를 "누락 보강"으로 오인해 재도입 — 재발)
  - 커밋 0ec47a1 (2026-09-04, 재도입분 제거 + plugin enable 만으로 로드됨 실측)
  - 2026-09-07 `/auto-mode-setup` 의 autoMode 블록(사내 IP·도메인·머신 절대경로) — settings.json 추적 자체를 중단
  - https://code.claude.com/docs/en/auto-mode-config (autoMode 는 settings.local.json 에서 안 읽힘)
---

# lesson-tracked-config-machine-paths

tracked 설정 파일에 **머신 절대경로**를 담으면 멀티머신에서 영구 ping-pong 이 되고, 그 dirty 상태가 **자동 pull 게이트를 막아 레포가 조용히 밀린다.** 2026-08-12 에 `~/.claude/settings.json` 이 6일간 이 상태로 묶여 있던 것을 발견해 적립한다.

## 무슨 일이었나

Orca 가 주입하는 관측 훅 11개가 `settings.json` 에 **주입된 머신의 절대경로**로 박혔다.

- Mac 이 커밋한 값: `/Users/jongyoonlee/.orca/agent-hooks/claude-hook.sh` (`f4011a5`, 08-03)
- Windows 가 로컬에서 고친 값: `C:/Users/yoon627/.orca/agent-hooks/claude-hook.cmd`

`settings.json` 은 tracked 라 두 머신이 같은 줄을 서로 덮어쓴다. 어느 쪽을 커밋해도 반대쪽이 죽으므로(훅 자체는 fallback 이 있어 **무음 no-op** 으로 degrade — 그래서 아무도 눈치채지 못한다) Windows 쪽 적응분이 커밋되지 못하고 **6일간 index 에 staged 로 방치**됐다.

## 왜 자동으로 안 드러났나 (3 Whys)

1. **왜 6일이나 몰랐나** — 훅이 `else { cat; } >/dev/null` 로 fallback 해 실패가 무음이다. 깨져도 로그가 안 남는다.
2. **왜 staged 가 쌓이는데도 경고가 없었나** — 당시 활성 `SessionStart` autopull 훅이 `git diff --quiet && git diff --cached --quiet` 게이트를 걸고 있었다. dirty 면 pull 을 **skip** 한다. 즉 *충돌 때문에 생긴 dirty* 가 *충돌을 알려줄 동기화*를 스스로 껐다.
3. **왜 그 게이트가 남아 있었나** — `c20c246`(08-04)이 이미 그 게이트를 걷어내고 `CLAUDE_AUTOPULL_OFF` 탈출구 + rebase/merge 가드로 개선했는데, **staged 스냅샷이 그보다 오래돼 개선을 되돌린 상태로 고정**돼 있었다. staged 는 시간이 지나도 갱신되지 않는다 — 오래된 index 는 조용한 revert 다.

> [!warning] staged 방치는 "아직 안 정한 것"이 아니라 **활성 설정의 시간 고정**이다
> 작업트리 = index 였으므로 이 머신은 6일 내내 `c20c246` 이전 훅으로 돌고 있었다. `git status` 의 `M ` 한 글자가 그 사실을 전부 담고 있었지만 아무도 diff 를 열지 않았다.

## 올바른 방법

- **tracked 설정에는 머신 절대경로를 넣지 않는다.** 넣어야 하면 그 값은 gitignored 로컬 파일(`settings.local.json`)로 뺀다.
- 뺄 수 없으면(외부 도구가 tracked 파일에 주입) **파일 존재로 고른다** — OS 를 판별하지 말고 후보 경로를 순서대로 보고 없으면 조용히 통과:
  ```sh
  c=~/.orca/agent-hooks/claude-hook.cmd; s=~/.orca/agent-hooks/claude-hook.sh
  if [ -f "$c" ]; then "$c"; elif [ -f "$s" ] && [ -r "$s" ]; then /bin/sh "$s"
  else { command -p cat 2>/dev/null || cat; } >/dev/null 2>&1 || :; fi
  ```
  `~` 는 **따옴표 없는 대입에서만** 확장된다. `c="~/…"` 는 리터럴이 되어 무음 fallback 으로 샌다 — 이 함정으로 검증이 한 번 거짓 통과했다([[lesson-test-copies-artifact]]).
- **동기화 훅에 dirty 게이트를 걸지 않는다.** `git pull --ff-only` 는 실제로 덮어쓸 때만 거부하므로 무관 파일이면 성공한다. 미리 skip 하면 위 2번처럼 자기 차단이 된다. 이 원칙은 [[git-hook-network-safety]] 의 async/동기 분리와 짝이다.
- **재주입 도구가 있으면 그 사실을 문서에 박는다.** Orca 는 재주입 시 다시 절대경로로 되돌릴 수 있다 → push 전 `git diff` 확인.

## 재발 1회 — gitkraken marketplace (2026-09-04)

같은 실패가 `settings.json` 의 다른 키에서 반복됐다. `extraKnownMarketplaces.gitkraken` 은 `source: directory` 라 값이 **머신 절대경로**다.

- `80dbb3c`(09-03)은 이 항목을 **의도적으로 제외**했다 — "plugin enable 만으로 동작해 불필요"라며 이 페이지를 근거로 명시.
- 하루 뒤 `3a11a92`(09-04)이 "등록 누락분 보강"이라며 **Windows 절대경로로 다시 넣었다.** 제외 이유가 커밋 본문에만 있고 README·이 페이지에는 없어서, 다음 작업자(다른 세션)가 그것을 누락으로 오인했다.
- Mac 에서 Claude Code 가 그 값을 로컬 경로로 재작성 → `settings.json` dirty → `git pull --rebase` 거부. 2026-08-12 과 **완전히 같은 증상**이다.
- `0ec47a1` 이 항목을 제거해 복원하고, 뺀 뒤에도 `claude plugin list` 에서 `gitkraken-hooks@gitkraken` 이 enabled 임을 실측 확인했다.

> [!warning] 제외 결정은 커밋 본문에만 두면 재도입된다
> `80dbb3c` 는 이유까지 정확히 적었지만 **커밋 메시지는 아무도 다시 읽지 않는다.** "이 키를 여기 두지 않는다"는 결정은 그 설정을 문서화한 자리(README)와 이 페이지에 남겨야 다음 사람이 누락으로 오인하지 않는다. 부재는 흔적을 남기지 않으므로 **부재의 이유를 적는 것**이 규칙이다.

## 재발 2회 — autoMode, 그리고 추적 자체를 끊다 (2026-09-07)

세 번째 사례. `/auto-mode-setup` 이 `settings.json` 에 `autoMode` 블록을 썼다. 안에 머신 절대경로(`C:\Users\yoon627\Repos\knowledge_base`)뿐 아니라 **사내 IP(`192.168.62.48`)·도메인(`aigw.autocrypt.co.kr`)·조직명·Bitbucket 레포 URL**이 들어 있었다. 이 레포는 **public** 이라 유출 표면이 이전 두 사례보다 넓다. 증상은 동일 — `git pull --rebase` 가 `You have unstaged changes` 로 거부.

**이번엔 표준 remedy 가 통하지 않았다.** 위 "올바른 방법"의 1번(`settings.local.json` 으로 빼기)이 `autoMode` 에는 적용 불가다:

> The classifier doesn't read `autoMode` from project settings in `.claude/settings.json` or `.claude/settings.local.json`.
> — [Configure auto mode](https://code.claude.com/docs/en/auto-mode-config), *Where the classifier reads configuration*

유효 스코프는 `~/.claude/settings.json` · managed settings · `--settings` 뿐이다. 옮기면 **에러 없이 조용히 무시**되므로 "옮겼는데 auto mode 가 내부 호스트를 계속 막는다"로 나타난다. managed settings(`C:\Program Files\ClaudeCode\managed-settings.json`)는 관리자 권한이 필요해 이 머신에선 쓸 수 없었다(사용자가 Administrators 그룹 아님).

**그래서 키가 아니라 파일을 뺐다** — `settings.json` 을 `.gitignore` 화이트리스트에서 제거하고 `git rm --cached`. 키 단위 대응이 3회 반복된 것이 근거다: 뺄 키를 하나 고를 때마다 Claude Code 는 다음 기능으로 또 쓴다. 추적을 끊으면 그 주입이 dirty 를 만들지 못하고, public 레포로 밀려나갈 경로도 사라진다.

동반 변경(추적 전제에 의존하던 것들): CI `lint.yml` 의 JSON validation 제거, `session-start-pull.test.js` 를 "settings 있으면 실제 배선 검증 / 없으면 CANONICAL" 로 이원화, `guard-worktree-edit.js` 의 main 편집 허용목록에 `settings.json` 추가(gitignored 글로벌 상태가 됐으므로 — 안 하면 worktree 세션이 존재하지도 않는 사본을 편집하라는 막다른 길에 빠진다), `dlc-doc-drift.js` 의 `readme-trigger` 에서 제외(Claude Code 자동 수정에 README 를 요구하면 오탐).

> [!warning] 왜 3회나 반복됐나 — wiki 만으로는 상기되지 않는다
> 이 페이지는 2026-08-12 부터 있었는데도 두 번 더 재발했다. 원인은 **`MEMORY.md` 인덱스에 이 lesson 을 가리키는 줄이 없었던 것**이다(메모리 파일 자체도 없었다). CLAUDE.md §13 은 wiki(상세) + 인덱스(자동 상기)를 **짝**으로 요구하는데 짝이 성립한 적이 없다. wiki 는 자동 주입되지 않으므로, 능동으로 grep 한 세션에서만 발견된다 — 나머지 세션은 매번 처음부터 다시 판단했고 사용자가 같은 지적을 반복해야 했다. **lesson 을 적립할 때 인덱스 줄을 같이 만들지 않으면 그 lesson 은 없는 것과 같다.**

## 탐지 신호

- `git status` 에 `M ` (staged-only) 가 **며칠 이상** 남아 있다
- 다른 머신에서 온 커밋과 같은 줄이 계속 충돌한다
- 자동 pull 이 도는 줄 알았는데 origin 이 앞서 있다 → 게이트를 의심

관련: [[effort-os-env-single-source]](같은 계열 — 같은 설정을 두 곳에 두면 어느 쪽이 레버인지 흐려진다), [[workflow-failures]].
