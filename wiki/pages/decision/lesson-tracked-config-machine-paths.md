---
title: lesson-tracked-config-machine-paths
category: decision
created: 2026-08-12
updated: 2026-09-04
sources:
  - 커밋 f1cbee0 (orca 훅 경로 머신 무관화)
  - 커밋 bde82de (README 동기화 + ~ 표기 통일)
  - 커밋 f4011a5 (2026-08-03, Orca agent-hooks 주입분 반영 — macOS 절대경로 커밋)
  - 커밋 c20c246 (2026-08-04, autopull 개선 — staged 스냅샷이 되돌리고 있던 것)
  - 실측 2026-08-12 (staged 6일 방치, autopull 정지, 훅 3분기 테스트)
  - 커밋 80dbb3c (2026-09-03, gitkraken marketplace 절대경로를 이 페이지 근거로 제외)
  - 커밋 3a11a92 (2026-09-04, 그 제외를 "누락 보강"으로 오인해 재도입 — 재발)
  - 커밋 0ec47a1 (2026-09-04, 재도입분 제거 + plugin enable 만으로 로드됨 실측)
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

## 탐지 신호

- `git status` 에 `M ` (staged-only) 가 **며칠 이상** 남아 있다
- 다른 머신에서 온 커밋과 같은 줄이 계속 충돌한다
- 자동 pull 이 도는 줄 알았는데 origin 이 앞서 있다 → 게이트를 의심

관련: [[effort-os-env-single-source]](같은 계열 — 같은 설정을 두 곳에 두면 어느 쪽이 레버인지 흐려진다), [[workflow-failures]].
