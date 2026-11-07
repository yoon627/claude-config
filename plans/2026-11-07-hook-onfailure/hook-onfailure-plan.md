---
title: hook-onfailure — 두 PreToolUse 가드의 onFailure·timeout 을 정본에 두고 sync 가 병합 (#257 6)
status: done
started: 2026-11-07
updated: 2026-11-07
---

# Goal
`guard-push-delete.js`(Bash)·`guard-worktree-edit.js`(Edit|Write|NotebookEdit) 두 PreToolUse hook 에 `"onFailure": "block"` + `"timeout": 10` 을 거는 결정(#257 6, 2026-11-06)을 정본 `scripts/permission-rules.json` 에 적고, `sync-permissions.js` 가 머신의 `settings.json` hook 항목에 병합하며, `/improve` 점검 13 이 그 drift 도 보고하게 한다.

- Why: `settings.json` 은 추적하지 않아 결정이 문서에만 있으면 머신마다 손으로 넣어야 하고 빠진다. 가드 hook 은 프로세스가 실패하면(node 없음·경로 틀림·시간 초과) 조용히 통과한다 — 두 가드가 force/delete push 와 main 편집의 유일한 가드다.
- Constraints: `onFailure` 는 Claude Code v2.1.295 이상(공식 hooks 문서). 옛 버전이 모르는 필드를 어떻게 다루는지는 문서에 없다(❌) — 그래도 적는다(결정). 정보성 hook(SessionStart·UserPromptSubmit·PostToolUse·Stop·Notification)은 건드리지 않는다. 정본의 다른 키·로컬 항목·순서는 그대로(기존 멱등 규칙). 이 머신의 `settings.json` 에는 적용하지 않는다(머신 적용은 사용자 작업 — #257 2 와 같은 경로).
- Out of scope: 가드 내부의 의도된 fail-open(잘못된 stdin·git 오류 → exit 0)은 그대로. 등록되지 않은 hook 을 새로 추가하는 것(README 설치 절차의 일). 그 밖의 hook 옵션(`async` 등).
- Size: medium
- Split: none — purpose-commit bundle: #257 6 · 1) 정본+sync+테스트+README 2) improve 점검 13 집계 · 둘은 다른 파일이고 따로 되돌릴 수 있지만 하나의 결정이라 한 plan.

# Tasks
- [x] plan 승인 (2026-11-07) — "#257-6: 가드 2개 block (추천)" 선택(2026-11-06) + "스스로 진행할수 있는거 더할거 없어?" 에 "지금 이어갈 수 있다" 고 답한 항목
- [x] plan-reviewer (2026-11-07) — CONDITIONAL: 강한 우려 5(아래 Decisions 에 반영), 약한 우려 중 버전 질문은 researcher
- [x] researcher — 옛 Claude Code(2.1.295 미만)가 모르는 `onFailure` 키를 어떻게 다루는지 (2026-11-07) — 문서 없음(⚠️): 2.1.122 이후 handler 단위로 걸러질 가능성이 크지만 파일 거부도 배제 못함; 공개 이슈 #88113(CLI 가 settings.json 을 쓸 때 모르는 hook 키를 지움) → sync 에 버전 게이트
- [x] 1) 정본·sync (2026-11-07) — Red 9건 → 41/41 — `scripts/permission-rules.json` 새 키 `hookOptions`: `[{"event":"PreToolUse","script":"guard-push-delete.js","onFailure":"block","timeout":10}, {… "guard-worktree-edit.js" …}]` · `scripts/sync-permissions.js`: `loadRules` 검증(선택 키, event·script 문자열, onFailure ∈ continue|block, timeout 양의 정수), `plan()` 이 `settings.hooks[event][*].hooks[*]` 중 `command` 문자열이나 exec form `args` 가 그 스크립트 basename 으로 끝나는 handler 를 찾아 다른 값인 필드만 바꾸고 `hookOptions` 변경 목록을 내며 drift 에 포함, handler 가 없으면 `hookMissing` — in sync 일 때도 `sync-permissions: … in sync (hook not registered: guard-push-delete.js — README install step; settings.local.json·project settings 는 보지 않는다)` 로 찍는다 · `report` 에 `~ hook options to set (N):`(N = handler×필드) 줄 `PreToolUse guard-push-delete.js onFailure: (unset) -> block` · `--keep-allow` 와 무관 · `scripts/sync-permissions.test.js`: 설정·일부만 설정됨(onFailure 만 있음)·문자열 `"10"`·같은 값(변경 0·멱등)·handler 없음(in sync + not registered 줄, exit 0)·exec form args(뒤 인자 있음)·따옴표 경로·접두 충돌(`old-guard-push-delete.js` 불일치)·두 번 등록(둘 다, N 은 handler 마다)·다른 event 에 등록(불일치)·`type` 이 command 아님(불일치)·셸 제어 연산자가 든 wrapper(변경 없이 정보 줄)·`hooks` 없음→키 안 만듦(파일 없음도)·`hooks.PreToolUse` 가 배열 아님→exit 2·정본 중복 entry→exit 2·잘못된 onFailure/timeout→exit 2·`--check` exit 1·정본에 두 가드가 있음 (TDD Red 먼저)
- [x] 2) improve (2026-11-07) — `skills/improve/improve.sh` 점검 13: warn 조건을 `$sp_add$sp_retire$sp_hook` 로, 문구 `ask 추가 N개 · 은퇴 N개 · hook 옵션 N개`; `hook not registered:` 줄은 README 설치 절차를 가리키는 warn · `skills/improve/improve.test.sh`: hook 옵션만 drift, hook+bare allow 만 drift(ok 로 숨지 않음), not registered warn; 기존 fixture `{"hooks":{}}` 는 not registered 상태라 기대 문구 갱신 · `skills/improve/SKILL.md` 한 줄
- [x] 문서 (2026-11-07) — `README.md`: `permissions.ask` 정본 단락(`hookOptions`), `guard-push-delete.js` 설치 단락과 '한계' 단락(hook 프로세스 실패가 2.1.295+ 에서는 block — 복구는 Claude 밖에서 손으로 settings.json 을 고치거나 `.bak-*` 복원; 되돌리는 손잡이는 entry 삭제가 아니라 정본 값을 `continue` 로), improve 점검 13 요약, 트리 설명 2줄 · `scripts/bootstrap/README.md` settings.json 행과 멱등 bullet · `sync-permissions.js` 머리 주석 · `permission-rules.json` `$comment`
- [x] code-reviewer → simplify 점검 → `bash scripts/verify.sh changed` (2026-11-07) — NEEDS DISCUSSION(Minor 5·Nit 5) → fix(fixup 2개) → 표적 재확인 요청 · simplify: 쓰지 않는 `handlerNames` export 제거 · `ALL PASS (skip: install-codex-skill.test.ps1 zsh)`
- [x] PR → CI 녹색 → 머지(`/e merge`) (2026-11-07) — PR #260

# Acceptance
1. 정본에 두 가드의 hookOptions 가 있고 `loadRules` 가 잘못된 항목(모르는 onFailure 값·음수 timeout·빈 script)을 exit 2 로 거부한다 — `sync-permissions.test.js` — 통과
2. 설정이 없는 handler 에 두 필드를 넣고, 같은 값이면 변경 0(두 번째 실행 변경 0), 다른 값이면 바꾸며, handler 가 없으면 drift 가 아니고 정보 줄만 — 테스트 — 통과, 규칙 목록·명령 원문은 출력하지 않는다
3. `--check` 가 hook 옵션 drift 만 있어도 exit 1 과 `~ hook options to set (N)` 을 내고, 점검 13 이 그것을 warn 으로 센다 — `improve.test.sh` 새 케이스 — 통과
4. README·bootstrap README 가 새 동작과 같다 — 리뷰 대조
5. 이 머신 `settings.json` 의 사본에 `--dry-run --settings <사본>` 을 돌리면 handler 2개·필드 4개를 잡는다(실데이터 매칭 — 사본만, 원본은 건드리지 않음) — 관찰
6. `bash scripts/verify.sh changed` 통과 + CI `lint` success

# Decisions
- 관련 decision 조회: 공용 wiki `claude-code-permission-prompt-sources`(처방 4 — 정본·sync 경로를 따른다), `lesson-skipped-axis-blocks-merge`(ps1 변경 없음 — 그래도 CI 경로로 머지: `settings.json` 구조를 바꾸는 스크립트라 외부 검증을 거친다 ⚠️ 판단).
- handler 매칭(plan-reviewer 1차 반영): `type` 이 `command` 인 handler 만 · `command` 문자열은 공백으로 토큰을 나누고 따옴표를 벗긴 뒤 `/`·`\` 로 나눈 마지막 조각이 스크립트 이름과 **정확히 같은** 토큰이 하나라도 있으면 일치(`old-guard-push-delete.js` 는 불일치) · exec form 은 `args` 의 **어느 원소든** 같은 기준(뒤 인자가 있어도 됨) · 같은 event 안에서만 찾고, 두 번 등록이면 둘 다 바꾸며 N 은 handler 마다 센다 — 다른 선택지: matcher 문자열 매칭(같은 matcher 에 다른 hook 이 붙을 수 있음)·`endsWith`(접두 충돌·따옴표·뒤 인자에 약함) 기각.
- 셸 제어 연산자(`;`·`&&`·`||`·`|`)가 든 `command` 는 바꾸지 않고 정보 줄(`wrapped command — set by hand`) — `… ; true` 같은 wrapper 는 실패를 삼켜 `onFailure` 가 뜻을 잃는다.
- 잘못된 모양(`hooks` 가 객체 아님, `hooks.PreToolUse` 가 배열 아님, group 이 객체 아님·`.hooks` 가 배열 아님, handler 가 객체 아님)은 permissions 와 같게 **fail-closed exit 2**("nothing written" — 버전 게이트보다 먼저 검사해 어느 머신에서나 같다) — sync 가 실제로 걷는 경로(`hooks.PreToolUse`)만 검증하고 다른 event 는 보지 않는다. `hooks` 가 없으면(파일 없음 포함) `hooks` 키를 만들지 않는다.
- `loadRules` 는 같은 event+script 가 두 번이면 exit 2(ask∩retireAsk 검사와 같은 자리) — 멱등이 깨지는 유일한 정본 상태.
- `hookMissing` 은 drift 가 아니다(sync 가 고칠 수 없고 적용 명령이 뜻이 없다) 하지만 **in sync 출력에도 찍고 점검 13 이 warn 으로 올린다** — 두 가드는 force/delete push 와 main 편집의 유일한 가드라, 등록 누락이 `onFailure` 누락보다 나쁜 상태인데 가장 덜 보고되면 안 된다(plan-reviewer 강한 우려 1).
- ⚠️ (구현) 버전 게이트 — env `SYNC_PERMISSIONS_CLAUDE_VERSION`(있으면 우선, 빈 값은 없음으로) 아니면 `claude --version`(Windows 는 셸을 거쳐 npm 의 `claude.cmd` 도 찾음)이 2.1.295 미만이거나 알 수 없으면 hook 옵션을 건너뛰고 `hook options skipped:` 한 줄 — 다른 선택지: 경고만 내고 적용 — researcher 가 파일 전체 거부 가능성을 배제하지 못해(그러면 `permissions.ask` 까지 사라진다) 안전한 쪽으로; 알 수 없음도 건너뛰는 이유는 CI·bootstrap 에서 `claude` 가 없을 수 있어서(테스트는 env 로 2.1.318 고정) — `claudeVersion`·`hookPlan`
- ⚠️ (구현) wrapper 판정은 `command` 에 `;`·`&`·`|`·개행·백틱·`$(` 가 있는지만 본다 — 다른 선택지: 셸 파싱 — 두 가드의 등록 형태는 `node <경로>` 하나라 그 이상은 과하다 — `isChained`
- ⚠️ (구현) 매칭 토큰은 공백 분리 뒤 양끝 따옴표만 벗긴다(디렉터리 이름에 공백이 있어도 마지막 토큰이 파일 이름으로 끝나 일치하고, 파일 이름 자체에 공백이 있을 때만 불일치 — code-reviewer 재현) — 다른 선택지: 셸 단어 분리 — README 가 Windows 는 exec form(`args`)으로 등록하라 하므로 공백 경로는 그 형식으로 들어온다 — `handlerNames`
- 정본 값이 로컬의 더 큰 `timeout` 도 덮어쓴다 — 다른 선택지 "최소 N" 기각: 두 값의 뜻이 달라지고 drift 판정이 모호해진다. 10초 근거: `guard-worktree-edit.js` 는 git 호출 최대 3회×2초 + node 시작(Windows 0.4~0.9초) ≈ 7초.
- handler 가 없을 때 drift 로 세지 않는다 — hook 등록은 README 설치 절차(머신마다 `hooks.PreToolUse` 에 넣기)의 일이고, sync 가 hook 을 새로 만들면 설치 절차와 역할이 겹친다. 정보 줄로만 알린다.
- 정보성 hook 에는 걸지 않는다(#257 6 결정 그대로) — UserPromptSubmit 을 block 하면 모든 프롬프트가 막히고, Stop·async 에는 효과가 없다.
- 커밋 단위: 1) `feat(permissions): sync the guard hooks' onFailure and timeout from the canonical list` — 정본·sync·테스트·README 2) `feat(improve): count hook-option drift in the permission check` — improve.sh·test·SKILL.md
- 기각: `settings.json` 의 hook 전체를 정본으로 옮기기 — 머신별 경로(`~`/절대경로·exec form)가 들어 있어 정본화하면 머신마다 변환이 필요하다; 이번 범위는 두 필드다.

# Blockers
