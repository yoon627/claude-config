---
title: push-colon-delete-hook — 콜론 refspec 원격 삭제 확인을 ask 규칙에서 PreToolUse hook 으로
status: done
started: 2026-09-28
updated: 2026-09-28
---

# Goal

`git push <remote> :<branch>`(rtk 접두 포함) 원격 삭제 확인을 PreToolUse hook `ask` 로 옮기고, settings.json 의 두 ask 규칙을 지워 세션 시작 경고를 없앤다.

# Intent

- Problem: `/doctor` 점검(2026-09-28) 결과, `permissions.ask` 의 `Bash(git push * :*)`/`Bash(rtk git push * :*)` 는 끝의 `:*` 때문에 prefix 규칙으로 해석돼(바이너리 `/^(.+):\*$/` 확인) 아무것도 매칭하지 못했다 — 콜론 형태 원격 삭제가 확인 없이 통과 가능. 같은 날 `:**` 로 바꿔 매칭은 복구했지만 규칙 문자열에 `:*` 가 있으면 위치 무관하게 시작 안내가 뜬다(실측 3종). 사용자는 경고가 안 뜨길 원함 → hook 으로 이관(사용자 지시).
- Constraints: 기존 ask 규칙과 동등 이상 — 모든 권한 모드(auto 포함)에서 확인이 떠야 한다(README `permissions.ask` 절: ask 는 auto 에서도 확인, CLAUDE.md §8(b) 원격 삭제는 항상 확인). fail-open(파싱 실패는 통과 — 다른 hook 관례). settings.json 은 gitignored 라 브랜치에는 스크립트·테스트·README 만 담기고, settings 편집은 main 복귀 후.
- Out of scope: `--delete`·`-d`·main/master·force push 규칙은 기존 ask 규칙 유지(경고 없음). `bash <script>` 안의 push 등 README 가 적은 기존 사각지대. 다른 머신의 settings.json(추적 대상 아님 — README 에 머신별 수동 단계 기록).
- 분할: 없음 — 스크립트와 settings 편집은 순서 의존(스크립트가 main 에 있어야 hook 등록이 유효)이지만 settings 는 추적 대상이 아니라 머지 단위가 하나뿐.

# Progress

- 2026-09-28: worktree 생성, Explore(guard-worktree-edit.js 형식·README 482/490 행·verify.sh node 축 glob), plan 작성.
- 2026-09-28: hook ask 실측(auto+allow 아래서도 차단, 대조군은 실행됨) → TDD Red(모듈 없음 26건) → 구현 → Green 26/26 → e2e(bare remote: hook 있으면 `:b1`·`rtk … :b2` 유지, 없으면 `:c1` 삭제) → README 갱신. plan-reviewer(CONDITIONAL)·code-reviewer(REQUEST CHANGES) → fix loop 1(전 위치 git·큰따옴표 스캔·줄 이음 등, 50/50) → 재리뷰(Major 1) → fix loop 2(따옴표 상태 스택, 59/59, 재리뷰 하네스 전부 기대대로) → e2e 한 줄 루프 차단 확인 → verify.sh ALL PASS → 커밋 07981bd → `/e merge` PR #187.

# Next

# Decisions

- 새 스크립트 `scripts/guard-push-delete.js`(matcher `Bash`) — guard-worktree-edit.js 에 합치지 않는다(matcher 가 `Edit|Write|NotebookEdit` 로 다르고 판정 대상도 다름).
- ⚠️ auto 모드에서도 `ask` — guard-worktree-edit 의 "auto 모드는 ask 생략"(2026-08-06 사용자 지시)과 상충 — 이 hook 은 원래 모드 무관하게 확인을 띄우던 ask 규칙의 대체라 동등성을 택함(그 지시는 main 편집 ask 에 한정).
- 판정: 명령을 `&&`·`||`·`;`·`|`·`&`·개행·`$(`·백틱·괄호로 나눈 각 조각에서 선행 `VAR=val`·`rtk` 를 건너뛰고 첫 단어의 basename 이 `git`, 전역 옵션 뒤 부속명령이 `push`, 그 뒤 인자 중 `^\+?:.` 인 토큰이 있으면 ask. `:` 단독은 matching push 라 제외. 부수 효과로 `git -C dir push origin :x` 도 잡는다(구 규칙은 못 잡음).
  - → "첫 단어" 대신 **조각 안 어느 위치든 git** 으로 변경 (이유: code-reviewer 실측 — 한 줄 루프 `do git push`·`xargs`·`env`/`sudo`·`if` 조건이 통과. 앞말 목록 관리보다 전 위치 검사가 단순하고, 대가는 따옴표 없는 `echo git push origin :x` 같은 안전 쪽 FP). 큰따옴표는 문자 단위 스캔(`\"` 이스케이프·안쪽 `$(`/백틱을 경계로), `\`+개행 줄 이음, `2>&1` 의 `&`, 단독 `{`/`}`, `:$(…)` 를 `:$` 로 보존, `-c`·`eval` 인자 재귀 검사 추가.
- `deny` 안 기각 — 사용자가 승인하고 실행하는 정상 삭제 경로까지 막아 ask 규칙과의 동등성을 깬다(plan-reviewer).
- fail-open 의 대가: hook 프로세스 실패(node 부재·경로 없음·timeout)면 판정 없이 통과 — node 에 의존하지 않던 규칙보다 이 경우만 약함. 수용(다른 hook 관례와 같고, 이 머신은 node 상주).
- rtk 상호작용: `rtk hook claude` 는 `updatedInput` 만 돌려주고 판정을 안 낸다(plan-reviewer 실측) → 가드 `ask` 와 충돌 없음, 가드는 원문·`rtk git …` 둘 다 처리.
- settings.json 편집 순서(main 복귀 후, 가장 위험한 단계 — untracked 라 git 복구 불가): 1) main 에 `scripts/guard-push-delete.js` 존재 확인 2) `cp settings.json settings.json.bak-push-hook` 3) hook 만 등록 4) 새 세션(headless)에서 hook 발동 실측 — 이 동안 `:**` 규칙이 남아 이중 보호 5) 규칙 2개 제거 6) 시작 출력 경고 0줄 확인. 롤백: 백업 복원(`cp settings.json.bak-push-hook settings.json`).
- 커밋 단위: 1개 — 스크립트·테스트·README 가 한 목적.

# Acceptance

- [x] 1. `node scripts/guard-push-delete.test.js` 통과 — ask: `git push origin :feat`, `rtk git push origin :feat`, `git push origin +:feat`, `cd x && git push origin :feat`, `git -C /r push origin :feat`, `/usr/bin/git push o :x` / allow: `git push origin feat`, `git push origin :`, `git push origin HEAD:feat`, `echo "git push origin :x"`(따옴표 안), `git log :x`, 빈/비JSON 입력(크래시 없음).
- [x] 2. 실측: headless `claude -p --permission-mode auto` 로 로컬 bare remote 에 `git push origin :<b>` 를 시키면 hook 이 ask → 실행되지 않고 원격 브랜치 유지(`Bash(git *)`·`Bash(rtk git *)` allow 가 있는 상태). 대조군(hook 없음)은 삭제됨. headless 라 확인 창이 아니라 거부로 관찰된다 — 대화형 확인 창은 관찰 범위 밖(⚠️).
- [x] 3. `bash scripts/verify.sh` 가 `ALL PASS`(skip 없는 줄).
- [x] 4. README: `permissions.ask` 절의 `:branch` 서술과 `hooks.PreToolUse` 목록·진입점 목록·트리에 hook 반영.
- [ ] [post-merge] 5. (main 복귀 후, Decisions 의 순서대로) hook 등록 후 main 스크립트 경로로 발동 실측 → 두 규칙 제거 → `claude -p` 시작 출력에 Permission 경고 0줄.

# Key Files

- `scripts/guard-push-delete.js` — 신규 PreToolUse hook
- `scripts/guard-push-delete.test.js` — 신규 테스트
- `README.md` — permissions.ask / hooks.PreToolUse / 진입점 / 트리
- `~/.claude/settings.json` — (gitignored) ask 규칙 2개 제거 + hook 등록

# Blockers

# Review Disposition

- ⚠️ self-flag(auto 에서도 ask) — resolved: plan-reviewer 가 선택 타당 판정(§8(b)·대체 대상이 ask 규칙).
- [plan] 강: settings 편집 순서·롤백 없음 — fix(Decisions 6단계·Acceptance 항목 5).
- [plan] 강 / [code] minor: `\`+개행 줄 이음 FN — fix(+테스트 2).
- [plan] 약: `$(…)`·`bash -c`·`env`/`sudo`·`2>&1` FN — fix(전 위치 검사·`-c`/`eval` 재귀·리다이렉트 `&`).
- [plan] 약: 다른 머신 수동 단계 — fix(README 한계 절).
- [plan] 약: README (3) 사각지대 문단 불일치 — fix(괄호 주석).
- [plan] 약: hook 실행 실패 시 보호 약화 — fix(Decisions·README 기록, 수용).
- [plan] 약: rtk 상호작용 근거 — fix(Decisions).
- [plan]/[code] plan Progress·Next 낡음 — fix.
- [code] Major: 첫 단어만 git — fix(조각 내 전 위치).
- [code] Major: 큰따옴표 `\"`·안쪽 `$(`/백틱 — fix(문자 단위 스캔).
- [code] Major: `:$(…)` 가 `:` 로 잘림 — fix(`:$` 보존).
- [code] minor: `git.exe`·`rtk proxy`·`--attr-source` — fix.
- [code] minor FP: heredoc·주석·`-o :값` 에서 ask — wontfix(안전 쪽 FP, README 에 명시).
- [code] nit: README "따옴표 안 통과"·fail-open 범위·"확인 강제" 표현 — fix.
- [code 2회차] Major: 큰따옴표 안 치환 뒤 따옴표 상태 반전(`-m "$(cat <<'EOF'…)" && git push origin :f` 우회) — fix(치환·서브셸 스택으로 복원, +테스트 4).
- [code 2회차] minor: 짝 없는 아포스트로피가 끝까지 삼킴·`bash -lc`·`$'…'` — fix(+테스트 4). fix loop 2회 상한 도달 — 재리뷰 하네스 전 케이스 기대대로(잔존 없음).
- [code] open: 작동하는 `:**` 규칙이 한 줄 루프 안쪽을 잡았는지 — 미확인, hook 이 이제 잡으므로 동등성 판단에 영향 없음.

# Deferred

- README `enabledPlugins` 서술(Pyright `true`·claude-md-management `true`)이 2026-09-28 `/doctor` 로컬 조치(pyright uninstall·claude-md-management `false`)와 어긋남 — 낮음 — `README.md` enabledPlugins 항목. 이 작업 범위 밖.

# Workflow Findings

- medium 규모인데 plan-reviewer 를 구현 전에 돌리지 않고 구현 뒤 사후 실행 — 단계 순서 누락(자기 발견). 결과는 동일하게 처분한다.
