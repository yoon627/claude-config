---
title: ledger-bash-edits — Bash 로 고친 plan·문서가 early-stop 경고를 끄고, subagent 대기 턴에는 경고를 미룬다
status: in_progress
started: 2026-09-27
updated: 2026-09-27
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal
`dlc-evidence-ledger` 가 Bash 로 고친 plan·README·`wiki/index.md` 를 보고 plan drift·문서 drift 경고를 끄게 해(workflow-failures "Bash 경유 편집" 행 17회의 본체), `dlc-early-stop` 이 background subagent 를 기다리는 중간 턴에는 경고를 미룬다(workflow-failures "중간 턴" 행 5회+).

# Intent
- 묶음: `plans/2026-09-25-repo-audit-followups/intent.md` 의 ledger-bash-edits 단위.
- 델타: 두 축 모두 네이티브 hook 입력으로 푼다 — Bash 편집은 PostToolUse `tool_response.bashEditDiff`(v2.1.269), 대기 턴은 Stop 입력 `background_tasks`(v2.1.145). Bash 편집은 **경고를 끄는 쪽으로만** 반영한다(사용자 결정 2026-09-27 — 아래 Decisions). 검증 명령을 이름이 안 맞는 스크립트로 감싸 생기는 "검증 없음" 오탐은 범위 밖(Deferred).
- 분할: 없음 — Bash 편집 축과 대기 턴 축은 따로 머지해도 모순은 없지만, 사용자가 한 단위로 합쳤고(2026-09-27) 두 축 모두 작아져 한 plan 이 리뷰·검증 비용이 적다. 커밋은 축별로 나눈다.

# Acceptance
1. 단위 1 — Bash 편집 반영(Red→Green): PostToolUse Bash 입력의 `tool_response.bashEditDiff` 경로(`changedFiles` ∪ `files[].filePath`) 중 (a) **이 브랜치에 매칭되는 plan**(`plan-match.activePlanPath`)이고 HEAD 와 다르면(`git --no-optional-locks status --porcelain` 비어 있지 않음) `planTouched=true` — 다른 작업의 plan(충돌로 멈춘 merge 가 남긴 것)은 무변경 (b) 세션 root 의 `README.md`·`wiki/index.md` 이고 HEAD 와 다르면 해당 drift 를 target 갱신으로 처리. 그 밖의 경로·HEAD 와 같은 경로(git pull·merge 결과)·`unavailable`/`skipped`/빈 목록·필드 없음·형태 불량은 장부를 바꾸지 않고, 같은 명령의 검증 인식(`verified`)은 그대로 된다. `changed`·`edited`·trigger dirty 는 Bash 로 켜지지 않는다. 확인: `node scripts/dlc-evidence-ledger.test.js`(실 git repo fixture) 수정 전 실패·후 통과.
2. 단위 2 — 대기 턴(Red→Green): Stop 입력 `background_tasks` 에 `type` 이 `subagent`·`workflow` 인 항목이 하나라도 있으면 early-stop 이 경고를 내지 않고 장부를 쓰지 않는다(`stop_hook_active` 분기보다 먼저). 빈 배열·필드 없음·`shell`/`teammate`/`monitor`/`cloud session`/모르는 type 만 있으면 기존 판정. 억제된 턴 뒤 background 가 빈 Stop 에서는 cap 이 보존된 채 경고가 난다. 확인: `node scripts/dlc-early-stop.test.js` 수정 전 실패·후 통과.
3. 기존 동작 유지 — 두 테스트 파일의 기존 케이스 전부 통과, `bash scripts/verify.sh` 마지막 줄 `ALL PASS`.
4. 실물 대조: transcript 의 `bashEditDiff` 레코드 전체에서 plan·README·index 경로가 든 레코드 수와, 그중 git 동기화 명령(pull·merge·checkout·rebase·reset·stash·cherry-pick)인 것의 수를 센다 — 후자는 런타임 HEAD 비교로 걸러져야 하므로 테스트 1 의 git merge 케이스가 그 경로를 덮는지 대조. 확인: scratch 재생 스크립트 출력.
5. 문서: README 의 `dlc-evidence-ledger.js`·`dlc-early-stop.js` 설명이 새 동작과 한계(auto·bypass 밖에서는 Bash 편집 기록 없음, 대기 중 새 사용자 프롬프트가 오면 미룬 경고가 리셋으로 사라짐)를 서술, 스크립트 주석의 "Edit/Write 로 고친 것만 본다" 서술 갱신, workflow-failures 두 행 상태 갱신과 `audit-low-batch` 포인터를 이 단위로 교체, `wiki/index.md`·`wiki/log.md` 동기화, `check_links.py wiki` clean.
6. 기준선: router-agent-message 머지(2026-09-27T06:5xZ) 뒤 이 단위 머지 전까지의 `early-stop-plan-drift`·`early-stop-conclusion`·`early-stop-verify` telemetry 수를 적어 둔다(효과 비교용).
7. - [ ] [post-merge] 실제 hook 경로: main 반영 뒤 (a) 소스를 Edit 로 고치고 plan 을 Bash 로만 고친 턴에서 plan drift 경고가 없는지 (b) background subagent 를 띄우고 턴을 닫을 때 early-stop 경고가 없는지 관찰.

# Progress
- 2026-09-27: worktree 생성(base `origin/main@43069b0`). 실측 — transcript Bash 결과 14,351건 중 800건에 `bashEditDiff`(v2.1.272~, 설정 없이 auto mode), 이 세션의 스크립트·`sed -i` 편집 160건이 잡힘. 필드: `files[{filePath(절대), hunks, deleted}]`·`moreFiles`·`changedFiles`(문자열, 상한 200)·`unavailable`·`shared`(바이너리 스키마엔 `created`·`skipped` 도). hooks 문서: PostToolUse 가 `tool_response.bashEditDiff` 로 받음, 기본은 auto·bypass 에서 Claude Code 가 Bash 편집을 시킨 경우만. Stop 입력 `background_tasks`(v2.1.145)는 스크립트가 아직 안 씀. doc-drift 는 이미 Stop 시점 mtime 비교(`partitionPending`)로 Bash 로 고친 README·index 를 보정하고, 남은 빈틈은 plan 축(`planTouched` 가 Edit/Write 에서만 켜짐 — 이 세션 `early-stop-plan-drift` raw 12). plan-reviewer CONDITIONAL → 단위 1 설계를 "경고 끄기만"으로 좁힘(사용자 결정). 기준선(Acceptance 6, 2026-09-27T06:52Z~07:32Z, 이 세션만): `early-stop-verify` 1·`doc-drift-index` 1·`early-stop-conclusion` 1·`early-stop-plan-drift` 0.
- 2026-09-27: 단위 1 — Red(새 테스트가 `planTouched` false 로 실패) → 구현 → Green 80건, 주석 3곳·README 갱신, 단위 커밋. 재생(Acceptance 4): `bashEditDiff` 800건 중 plan·README·index 경로가 든 146건 = 편집 명령 123·git 동기화 명령 23(런타임 HEAD 비교로 걸러질 대상 — 테스트의 merge·pull 케이스가 덮음). 단위 2 — Red(대기 중에도 검증 block) → 구현 → Green 31건, README 갱신, 단위 커밋. `verify.sh` ALL PASS. workflow-failures 두 행 fixed·`audit-low-batch` 포인터 교체·index·log 갱신. code-reviewer 진행(Codex 소진으로 생략).

- 2026-09-27: code-reviewer APPROVE — minor 7·nit 4 처분(Review Disposition). ledger 83건·early-stop 31건 통과, `verify.sh` ALL PASS.

- 2026-09-27: 재리뷰(fix loop 2) APPROVE — minor 2·nit 5 처분. 격리 runner 최종 검증이 메인 판정과 일치(ledger 83·early-stop 31·doc-drift 76·plan-match 11, `verify.sh` ALL PASS, check_links clean, plan-lint 0, tree clean) — runner 가 짚은 `monitor` 케이스 누락은 테스트 목록에 추가. evidence gate DONE(Acceptance 1~6 충족, 7 은 post-merge).

# Next
commit-check(fixup 합치기, 승인 후) → `/e merge`(hook 코드라 CI 경유) → 머지 뒤 Acceptance 7 실측.

# Decisions
- Bash 편집 감지는 네이티브 `bashEditDiff` 로 한다. 기각안: Stop 시점 `git status`/`git diff --name-only` 로 편집 집합 보강 — 사용자·다른 세션의 동시 편집까지 이 세션 것으로 잡고, 매 Stop 마다 git 을 돌리며, 커밋된 편집은 못 본다.
- **Bash 편집은 경고를 끄는 쪽으로만 반영한다**(사용자 결정 2026-09-27): plan 편집 → `planTouched`, README·`wiki/index.md` 편집 → drift target 처리. `changed`·`edited`·trigger dirty 는 켜지 않는다. 기각안: Edit/Write 와 완전 대칭 처리 — plan-reviewer 실측으로 새 오탐 3부류(git 동기화 diff 39건, 한 diff 안 사전순 처리로 target 이 trigger 보다 먼저 와 drift 잔존 76건, `sed … && verify.sh` 체인의 검증이 첫 토큰 veto 32건)가 생기고, 막으려면 HEAD 필터·배치 순서·조각별 veto·800건 턴 재생 게이트까지 필요해 structural 이 된다. 감수: Bash 로만 고친 스크립트는 지금처럼 검증·README 경고를 띄우지 못한다(미탐, 회귀 아님).
- 대상 경로는 **HEAD 와 다를 때만** 인정한다(경로가 든 repo 에서 `git status --porcelain -z -- <path>` 1회, 후보가 plan·README·index 뿐이라 호출이 적다). git pull·merge·checkout 결과는 HEAD 와 같아져 걸러진다. git 실패·timeout 은 "다르지 않음"으로 본다 — 경고를 끄지 않는 쪽이라 fail-safe.
- 경로 목록은 `changedFiles` ∪ `files[].filePath` — 둘 다 상한이 있다(`files` 는 `moreFiles` 로 나머지 개수만, `changedFiles` 는 200). `unavailable: true` 여도 나열된 경로는 처리한다(바이너리가 목록과 함께 줄 수 있다). 파싱 전체를 try/catch 로 감싸 형태가 어긋나도 `ledger.write`·검증 인식이 살아 있게 한다.
- `shared: true`(같은 repo 에서 Bash 가 동시에 돔)·Edit 로 먼저 고친 파일의 재나열 — 경고를 끄는 쪽으로만 쓰므로 다른 작업의 plan·README 편집을 이 세션 것으로 봐 경고가 한 번 덜 날 수 있다. 감수.
- plan 신호(`plan-blocked`·`review-disposition`)는 Bash 편집에서 만들지 않는다 — `detectPlanSignal` 은 Edit/Write 의 입력 본문을 보는데 Bash 에는 없다. hunks 로 만드는 안은 Deferred.
- Bash 로 고친 plan 은 **이 브랜치에 매칭되는 plan** 만 인정한다로 변경 (이유: code-reviewer — 충돌로 멈춘 `git fetch && git merge` 체인은 main 에서 온 다른 plan 들을 HEAD 와 다르게 남겨 `plans/` 전체를 인정하면 plan drift 가 세션 끝까지 꺼진다. plan drift 가 보는 파일도 브랜치 plan 뿐이라 기준이 같아지고, git 호출이 경로 수와 무관하게 rev-parse 1 + status 1 로 묶인다).
- `git status` 는 `--no-optional-locks`(index.lock 을 잡아 병렬 git 을 실패시키지 않게 — `session-brief.js` 선례)·`-uall`(untracked 디렉토리 안의 새 plan)·`:(literal)` pathspec 으로 부른다.
- 대기 턴 판정 type 은 `subagent`·`workflow` 만(allowlist) — 결과를 들고 이 세션으로 돌아오는 작업이다. `teammate` 는 뺀다로 변경 (이유: code-reviewer 가 2.1.283 바이너리로 확인 — 직렬화 필터가 running/pending·backgrounded 만 보고 idle 여부는 보지 않아, 일을 마친 idle teammate 가 running 으로 남아 team 세션 내내 경고가 꺼진다. 직렬화 항목에 idle 필드가 없어 hook 쪽에서 가를 수 없다). `shell`·`monitor`·`MCP task` 는 끝나지 않는 서버·tail 일 수 있어 넣으면 실제 종료에서도 경고가 영영 미뤄지고, `cloud session` 은 결과가 이 세션으로 돌아오는지 모른다 ❌, 모르는 type(`dream`·`auto-mode scan` 등)은 억제하지 않는다. 억제 판정은 `stop_hook_active` 분기보다 먼저 해 장부를 전혀 건드리지 않는다.
- ⚠️ 대기 턴 억제는 `background_tasks` 가 in-flight 작업만 담는다는 문서 서술과, subagent 가 끝나면 목록에서 빠진다는 추정에 기댄다 — observer subagent 가 오래 남으면 그동안 게이트가 꺼진다(teammate 는 이 이유로 뺐다). 머지 뒤 실측(Acceptance 7b)으로 확인하고, 어긋나면 `status` 로 좁힌다.
- 방향 합의(사용자 2026-09-27): 두 축 모두, `bashEditDiffEnabled` 는 넣지 않는다 — 이 머신 세션은 전부 auto mode 라 이미 기록되고, 켜면 모든 Bash 결과에 diff 가 붙어 컨텍스트 비용이 늘 수 있다 ⚠️.
- 커밋 단위: 1) `feat(hooks): let Bash-edited plans and docs settle early-stop warnings` — `scripts/dlc-evidence-ledger.js`·`.test.js`, README 의 ledger 설명, `scripts/dlc-early-stop.js` 의 doc-drift 주석 2) `feat(hooks): defer early-stop warnings while background subagents run` — `scripts/dlc-early-stop.js`·`.test.js`, README 의 early-stop 설명. plan·wiki 는 마지막 단위 fixup. README·early-stop.js 는 두 단위가 함께 고치므로 단위 1 을 커밋한 뒤 단위 2 를 시작한다.

# Review Disposition
- [plan] major 단위 1 대칭 처리의 새 오탐 3부류·recall 만 보는 Acceptance 4 — fix(설계를 "경고 끄기만"으로 좁혀 새 경고 경로 자체를 없앰, 사용자 결정. Acceptance 4 는 git 동기화 레코드가 런타임 필터 대상인지 대조로 바꿈).
- [plan] minor `changedFiles` 상한·`unavailable` 동반 경로·`created`/`skipped` — fix(합집합, 나열 경로 처리, 빈 목록 무변경). minor try/catch·`check-ignore` 지연 — fix(try/catch, 후보를 plan·README·index 로 먼저 좁혀 git 호출 최소화 — `check-ignore` 는 쓰지 않음). minor `detectPlanSignal` 미적용 — defer(Deferred). minor 편집·검증 순서 — 해당 없음(Bash 편집이 `changed` 를 켜지 않아 순서 영향이 없다). minor `shared`·재나열 — accepted(Decisions). minor `stop_hook_active` 순서·type allowlist·모르는 type — fix(Decisions·Acceptance 2). minor 억제 경고가 새 프롬프트 리셋으로 사라짐 — fix(README 한계). minor 낡는 주석 — fix(Acceptance 5). minor 기준선 — fix(Acceptance 6). minor shell 중 검증 명령도 억제 — wontfix(allowlist 를 단순하게 둔다, 결과를 기다리는 검증은 보통 foreground). minor 억제 telemetry — defer.
- [plan] 누락 시나리오: 실패한 Bash 는 diff 없음·`deleted` 파일·세션 repo 밖 경로·subagent diff 의 부모 장부 혼입 ❌ — README 한계에 앞의 둘을 적고, repo 밖 경로는 테스트로 무변경 확인, subagent 혼입은 경고를 끄는 쪽이라 감수.

- [code] APPROVE(Critical·Major 없음). minor `--no-optional-locks` 누락 — fix. minor 경로당 git 호출 상한 없음(plan 76개 merge 체인에서 865ms) — fix(브랜치 plan 한정으로 plan 은 경로 수와 무관하게 1회, README·index 는 root 당 최대 2). minor 충돌로 멈춘 merge 가 다른 plan 으로 `planTouched` — fix(브랜치 plan 한정, 테스트). minor idle teammate 가 running 으로 남아 억제 지속 — fix(allowlist 에서 제외, 테스트). minor `files` 만 있는 레코드(실측 39%)를 테스트가 안 덮음 — fix(테스트). minor root 밖 경로 테스트 누락 — fix(테스트). minor README doc-drift 절 낡음 — fix. nit README 한계 누락(`run_in_background`·단독 git 동기화 명령엔 diff 없음, 삭제된 README·index) — fix. nit 테스트의 단독 `git merge` 는 실물에서 diff 가 안 오는 형태 — fix(체인으로). observer subagent·HOME symlink 경로 ❌ — open(post-merge 관찰).
- [code 2회차] APPROVE(Critical·Major 0). minor `plan-match` 소비자 목록에 ledger 누락(README·모듈 주석) — fix. minor README ledger·doc-drift 문단이 단위 2 fixup 에 들어감 — accepted(dlc 귀속 예외: README 는 단위 2 도 고친 파일이라 단위 1 fixup 으로 보내면 합칠 때 3-way 충돌하고, 대화형 hunk 분리를 쓸 수 없다. 단위 1 커밋만 따로 보면 README 서술이 한 단계 뒤처진다). nit 테스트의 단독 `git pull` — fix(체인). nit plan ⚠️ 문구가 teammate 제외와 모순 — fix. nit 경로 중복 제거가 절대경로화 전 — fix. nit untracked 디렉토리의 새 브랜치 plan·worktree root 조합 테스트 없음 — wontfix(리뷰어가 scratch fixture 로 동작 확인, `-uall` 은 git 문서대로). nit `activePlanPath` 첫 매치만 — accepted(early-stop 과 같은 기준, 현재 충돌 0건). fix loop 2회 상한 — 남은 finding 없음.

# Deferred
- (중간) 검증 명령을 이름이 VERIFY_SCRIPT 에 안 맞는 스크립트로 감싸면 "검증 없음" 오탐(workflow-failures "Bash 경유 편집" 행의 verify 부분) — 스크립트 본문을 보는 안은 오인식 위험이 있어 별도 판단.
- (낮음) Bash 로 고친 plan 에서도 `plan-blocked`·`review-disposition` 신호를 hunks 로 만드는 안.
- (낮음) 대기 턴 억제 횟수를 telemetry 로 세는 안(`dlc-signal.js` KINDS 추가).

# Key Files
- `scripts/dlc-evidence-ledger.js` · `scripts/dlc-evidence-ledger.test.js` — Bash 편집을 경고 끄기로 반영
- `scripts/dlc-early-stop.js` · `scripts/dlc-early-stop.test.js` — 대기 턴 억제, doc-drift 주석
- `README.md` — 두 스크립트 설명
- `wiki/pages/decision/workflow-failures.md` — 두 행 상태, `audit-low-batch` 포인터

# Blockers
없음
