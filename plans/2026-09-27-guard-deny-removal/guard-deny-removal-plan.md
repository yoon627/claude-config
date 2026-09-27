---
title: guard-deny-removal — guard-worktree-edit 기능 ②(worktree 밖 편집 deny) 재판정·처분
status: in_progress
started: 2026-09-27
updated: 2026-09-28
intent: plans/2026-09-27-improve-followups/intent.md
---

# Goal
`scripts/guard-worktree-edit.js` 기능 ②(worktree 세션의 worktree 밖 main checkout 편집 `deny`)를 현재 버전(2.1.283)에서 다시 재고, 그 결과에 맞게 처분한다(묶음 단위 원안은 제거). 기능 ①(비-worktree 세션의 main/master 추적 파일 편집 `ask`)은 남긴다.

# Intent
- 묶음: `plans/2026-09-27-improve-followups/intent.md` 의 guard-deny-removal 단위.
- 델타: 착수 조건(대장 1b 2026-08-12 관측표 재실측 + 1b 콜아웃의 worktree 세션 memory 쓰기 확인)이 원안(제거)의 전제를 뒤집었다(아래 Progress·Decisions). 사용자 결정(2026-09-27): **제거 대신 ② 를 좁힌다** — main checkout 의 추적 파일 편집과 새 파일(아직 없고 gitignored 아님) 생성만 deny(두 번째 결정, 규칙 (C)) + 대장 1b 정정. 기능 ① 불변.
- Constraints: hook 은 fail-open 관례(git 판정 실패 → allow). `guard-worktree-deny` 신호·<2.1.222 보호는 유지된다(제거가 아니므로). 묶음 공통 "fixture 는 실제 hook stdin" — 처분은 Decisions.
- Out of scope: 기능 ① 변경, 격리 해제 뒤 cwd 가 worktree 로 돌아간 세션을 판별하는 장치(hook 입력에 격리 여부가 없다 — 아래 Decisions), worktree 세션의 memory 쓰기 막힘(네이티브 쪽이라 guard 로 못 푼다), CLAUDE.md §3-1 문구(운영 자산 — `# Deferred`).
- 분할: 없음 — 대장 정정과 guard 좁히기는 같은 실측의 두 결과라 한쪽만 머지되면 대장 판정과 코드가 어긋난다(대장이 keep 인데 코드가 옛 범위, 또는 그 반대).

# Acceptance
1. ② 가 worktree 세션(cwd 가 `.claude/worktrees/<name>/` 하위)의 worktree 밖 `<repo>/` 경로 편집에서 **main checkout 추적 파일 → deny, 아직 없고 gitignored 아닌 새 경로 → deny**, gitignored(기존·새)·main 에만 있는 기존 untracked 파일 → allow, git 판정 실패(cwd 없음 spawn 실패·repo 아님 128) → allow(fail-open), 상속된 `GIT_DIR` 은 무시한다. 기존 예외(현재 worktree 안, `<repo>/.claude/` 메타, `~/.claude` 레이아웃의 `plans/`(기존·새), repo 밖)와 `<repo>/.git/`(기존·새)은 allow, `~/.claude` 레이아웃 fixture 는 실물 whitelist `.gitignore` 로 판정하고, guard 크래시는 allow 로 세지 않는다, `plans/../scripts/<추적>` 우회는 정규화 뒤 deny, glob 문자가 든 기존 untracked 이름(`[ab]c.js`)이 추적 파일(`ac.js`)에 매칭돼 deny 되지 않는다. 확인: `node scripts/guard-worktree-edit.test.js` 의 실 git fixture 케이스(`~/.claude` 레이아웃·일반 repo 레이아웃) — 새 케이스가 구현 전 Red(옛 guard 로 스크래치에서 실행), 구현 뒤 전부 PASS, `..` 정규화를 지운 변이본에서 traversal 케이스 FAIL.
2. 관측 오탐 두 경로가 회귀 케이스로 allow — `~/.claude/jobs/<id>/tmp/*.txt`(gitignored)·일반 repo 의 gitignored `plans/*.md`. 확인: 1 의 테스트 안 이름 붙은 케이스.
3. 기능 ①(비-worktree 세션의 main/master 추적 파일 `ask`, auto 모드 제외, OFF env)은 동작 불변 + glob 이름 untracked(`[st]racked.js`)는 `ask` 하지 않는다. 확인: 기존 ① 케이스(ⓐ~ⓝ·ⓘ)와 ⓞ 전부 PASS.
4. deny 시 `guard-worktree-deny` 신호 emit 유지. 확인: `node scripts/dlc-signal.test.js` 통합(guard) 테스트를 실 git fixture 로 바꿔 PASS.
5. README `guard-worktree-edit.js` 절과 `hooks.PreToolUse` 줄·파일 트리 주석, guard 파일 머리 주석이 추적 파일 편집·새 not-ignored 파일 생성 deny, gitignored·기존 untracked allow, fail-open 을 서술한다(옛 "main repo 소스 전부 deny"·`projects/`·`settings` 개별 예외 서술 잔존 없음). 확인: 해당 줄 read + `rg` 로 옛 문구 부재.
6. 대장 `native-overlap-ledger` 1b: 행을 지우지 않고 정정 행 + 근거 + `> [!conflict]`(대장 운영 규칙) — 2026-09-27 관측(EnterWorktree 세션 vs worktree 디렉토리에서 시작한 linked worktree 세션, 발동 이력 7건 분류 + 측정 행 1), verdict `retire` → `keep`, 1b 콜아웃의 memory 쓰기 2.1.283 재실측 결과, 옛 `retire` 서술(판정 표 1b·요약 줄 2곳·"결론"·"제거 시 함께 사라지는 것")에 정정 포인터. `checked` 는 밀지 않는다(표적 실측). 같은 서술을 가진 `worktree-per-task`(retire 후보)·`dlc-wt-autoflow`(네이티브 거부 — EnterWorktree 한정) 정정. `wiki/index.md`·`wiki/log.md` 동기화, `check_links.py` clean. 공개 점검: 다른 repo 이름·경로 없음.
7. `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없이).
8. 머지 전 실세션: user hook 을 뺀(`--setting-sources project,local`) headless 세션에 이 worktree 의 guard 만 `--settings` 로 걸어, 임시 repo 의 linked worktree 디렉토리에서 시작해 main checkout 에 — 추적 파일 Write → guard deny(추적 파일 문구)·main 내용 불변, 새 not-ignored 파일 Write → deny(새 파일 문구)·미생성, gitignored 새 파일 Write → 생성됨(옛 guard 였다면 deny — user hook 이 빠졌다는 증거). 확인: `stream-json` 도구 결과.

# Progress
- 2026-09-27: worktree 생성(base `origin/main@3a86766`). 재실측(2.1.283, auto 모드):
  - **EnterWorktree 세션**(이 세션): main checkout 의 `plans/` 새 파일·`scripts/` 새 파일·`projects/…/memory/` 새 파일 Write, 기존 `README.md` Edit, `scripts/*.ipynb` NotebookEdit — 전부 네이티브 `tool_use_error` "This session is isolated in the worktree … Edit the worktree copy of this file instead of the shared-checkout path." 로 거부(파일 생성·변경 없음 확인). `scripts/` 도 guard 문구가 아니라 네이티브 문구 → 네이티브 검증이 PreToolUse hook 보다 먼저 돈다. memory 쓰기는 2.1.283 에서도 막힌다(1b 콜아웃 유지).
  - **worktree 디렉토리에서 바로 시작한 세션**(EnterWorktree 미경유, headless `claude -p --permission-mode acceptEdits`): 임시 git repo 의 linked worktree(`.claude/worktrees/wt1`)에서 main checkout 새 파일 Write — hook 끔 = **생성됨**(2회 재현, 네이티브 격리 없음), hook 켬 = guard ② 가 `deny`. `~/.claude` 에서는 같은 시도가 격리가 아니라 "sensitive file" 권한 요청으로 멈춘다(`~/.claude` 경로 자체의 민감 판정).
  - **guard ② 실제 발동 이력**(`telemetry/dlc-signals.jsonl` `guard-worktree-deny`, 이날 이전 7행): 2026-07-16 1건 = `~/.claude/jobs/<session>/tmp/` 임시파일(gitignored) 오탐 · 2026-08-11 3건 = 08-12 실측의 hook 직접 호출(`session_id: probe`) · 2026-09-14 3건 = 다른 repo 세션이 `ExitWorktree` 로 격리를 벗어난 뒤 Bash `cd` 로 cwd 가 worktree 로 돌아간 상태에서 main 의 gitignored plan 편집을 막은 오탐(편집이 worktree 사본으로 옮겨가 worktree 삭제 때 사라질 위치였다). 옳게 막은 기록 0건. 2026-09-27T10:23 1행은 위 hook 켬 실측이 남긴 측정 행.
  - **worktree 디렉토리에서 시작한 세션 빈도**(transcript 시작 cwd): interactive 2개(둘 다 2026-09-14, 1개는 뒤에 EnterWorktree), headless 22개(대부분 실측용 `claude -p`).
- 2026-09-27: 사용자 결정 — 제거 대신 추적 파일 한정으로 좁힘. plan-reviewer 병행 중 구현: git 확인(`--literal-pathspecs` 없으면 `a*.js` 가 추적 `abc.js` 에 매칭돼 rc 0, 절대경로·symlink tmp·repo 밖 128 정상). TDD Red 6건 → `isTracked` 공유 헬퍼로 Green. README 3곳·대장 1b 정정 절·index·log 갱신, check_links clean.
- 2026-09-27: plan-reviewer CONDITIONAL(아래 Review Disposition). ⚠️ self-flag 전제 오류(관측 오탐은 전부 gitignored 라 새 파일 차단과 양립) → 사용자 결정으로 규칙 (C) 채택. 테스트 갱신 → Red 3건(새 not-ignored 파일 2·상속 `GIT_DIR`) → `git()` 헬퍼(`spawnSync`·`GIT_LOCAL_ENV` 제거·`core.fsmonitor=`)·`isNewUnignored`(check-ignore)로 Green(guard ALL PASS, dlc-signal 22 passed). 스크래치에서 옛 guard(HEAD)로 새 테스트 Red 8건(+ⓘ 는 스크래치에 `dlc-signal.js` 가 없어서 난 실패), `..` 정규화 제거 변이본에서 traversal FAIL. Acceptance 8 을 머지 전 실세션으로 확인(3건 기대대로). README·대장(정정 절 보강·retire 포인터 4곳)·`worktree-per-task`·`dlc-wt-autoflow`·log 갱신. 단위 커밋 2개(`fix(guard)`·`docs(wiki)`).
- 2026-09-28: code-reviewer(1회 600초 무진행으로 멈춰 이어서 완료) APPROVE — 처분은 Review Disposition. Red 1건(일반 repo `.git/hooks` 새 파일) → `.git/` allow 로 Green, 테스트 크래시 판정·실물 whitelist fixture·서술 범위·대장 84·85행 포인터 반영 → fixup 2개. simplify: 로직 중복·죽은 분기 없음, 옛 `projects/` 예외를 예로 든 `..` 정규화 주석만 `plans/` 로 고침(fixup). 격리 runner 에 `bash scripts/verify.sh` 위임.
- 2026-09-28: 격리 runner — `bash scripts/verify.sh` exit 0·마지막 줄 `ALL PASS`(skip 없음, node tests 16 에 두 테스트 포함), guard 테스트 41 PASS·ALL PASS, dlc-signal 22 passed. runner 가 not observed 로 둔 두 곳을 메인이 확인: ⓕ·ⓖ 는 base 에도 없는 번호(원래 없는 케이스), dlc-signal `ok(` 22개에 213행 guard 통합 테스트 포함. A5 옛 문구 부재(`main repo 소스`·`main repo 편집 차단` grep 0), 공개 점검(diff·plan 에 비공개 repo 이름·홈 경로 0). evidence gate: Acceptance 1~8 충족 → DONE.

# Next
commit-check 로 fixup 합치기(승인) → `/e merge`(push·PR·머지 — 사용자 지시 시).

# Decisions
- 대장 1b 의 "네이티브 ⊇ 자작 ②"는 **EnterWorktree 세션에 한해서만** 참이다(2026-09-27 실측). 네이티브 격리는 세션이 worktree 에 들어간 경로(EnterWorktree)에 걸리고, worktree 디렉토리에서 시작한 세션에는 걸리지 않는다 — 그런 세션에서 ② 가 유일한 보호다. 08-12 실측은 EnterWorktree 세션만 쟀다.
- EnterWorktree 세션에서는 네이티브가 hook 보다 먼저 거부하므로 ② 는 그 세션에서 도달하지 않는다 — ② 가 실제로 발동하는 것은 "격리되지 않았는데 cwd 가 worktree 안"인 세션뿐이고, 그 안에 옳은 차단(worktree 디렉토리에서 시작)과 오탐(격리 해제 뒤 cwd 복귀, gitignored 경로)이 섞여 있다.
- 처분: ② 를 제거하지 않고 좁힌다(사용자 결정 2026-09-27). 기각: 원안대로 제거 — worktree 디렉토리에서 시작한 세션은 네이티브도 막지 않아 보호가 0 이 된다(다른 repo 는 권한 요청도 없다). 기각: 대장만 정정 — 관측 오탐 4건(전부 gitignored 경로)이 그대로 남는다.
- deny 범위를 "추적 파일만"에서 **"추적 파일 OR (아직 없고 gitignored 아닌 경로)"(규칙 (C))로 변경** (이유: plan-reviewer 가 ⚠️ self-flag 의 전제 오류를 지적 — 관측 오탐 4건은 untracked 가 아니라 전부 gitignored 라 새 파일 차단과 양립한다. 새 파일이 main 에 남으면 브랜치 커밋에서 빠지고, 같은 경로를 들여오는 main `git merge --ff-only`·SessionStart autopull 이 untracked 충돌로 멈춘다 — 이 repo 문서가 `~/.claude/...` 절대경로를 많이 써 가장 일어나기 쉬운 실수다. 사용자 결정 2026-09-27). 기각: (B) "ignored 가 아니면 deny" — main 에만 있는 기존 untracked 파일(`settings.json`·사용자 초안)은 worktree 사본이 없는데 deny 메시지가 없는 경로로 안내한다. 그래서 "아직 없음" 조건을 붙인다.
- ~~⚠️ 새 파일은 막지 않는다 — 오탐 제거와 새 파일 차단이 같은 조건(untracked)이라 동시에 만족할 수 없다~~ → 위 규칙 (C) 로 변경(이유: 전제가 틀렸다 — plan-reviewer). self-flag 처분은 Review Disposition.
- 추적 판정은 `git --literal-pathspecs ls-files --error-unmatch`, 새 경로 판정은 `fs.existsSync` + `git check-ignore -q`(exit 1 = not ignored) — 둘 다 main checkout(`repoRoot`)에서, ① 과 공유하는 `git()` 헬퍼로. `--literal-pathspecs`: `[ab]c.js` 같은 untracked 이름이 추적 `ac.js` 에 glob 매칭돼 deny·ask 되지 않게(① 도 함께 바뀌어 오탐 `ask` 가 준다). check-ignore 에는 붙이지 않는다 — `pathspec magic not supported` 128 로 조용히 fail-open 된다(plan-reviewer 실측).
- `git()` 헬퍼는 `spawnSync`(exit status 구분 — check-ignore 의 0/1/128), 상속된 repo-routing `GIT_*`(`session-brief.js` 의 `GIT_LOCAL_ENV` 와 같은 목록) 제거, `-c core.fsmonitor=`(repo 설정의 명령 실행 방지 — `session-brief.js` 선례). 목록은 복제했다 — 공유 모듈로 빼면 hook 두 개가 새 require 를 갖게 돼 이번 범위를 넘는다.
- fail-open(allow) 경로: spawn 실패(cwd 없음)·timeout 2s·repo 아님·safe.directory 거부·submodule 안 경로(128) — 옛 ② 는 git 을 안 써 이 경우 deny 였다. hook 관례대로 fail-open 을 택했다. **양성 대조 케이스(① ⓐ ask·② 추적 파일 deny)는 지우지 않는다** — `git` 옵션 위치가 틀리면(예: `ls-files --literal-pathspecs` → 129) fail-open 으로 ①·② 가 조용히 꺼지는 것을 잡는 유일한 장치다.
- 예외 정리: `~/.claude` 레이아웃의 `projects/`·`settings.local.json`·`settings.json` 개별 allow 는 지운다 — 앞 둘은 gitignored, `settings.json` 은 main 에만 있는 기존 untracked 라 새 규칙으로 allow 된다(중복). `plans/` 는 추적 중이라 예외를 남긴다(§10 핸드오프 — worktree 세션이 main 의 상위 plan 을 고치는 것이 정상, 새 plan 도). `<repo>/.claude/` 메타 allow 도 남긴다(일반 repo 의 추적 `.claude/settings.json`·agents 등).
- deny 메시지는 대응하는 worktree 경로(`wtRoot + fp.slice(repoRoot.length)`)를 적는다 — 추적 파일은 "그 경로를 Edit/Write", 새 파일은 "그 경로에 만드세요".
- 격리 해제 뒤 cwd 가 worktree 로 돌아간 세션(2026-09-14 사례)이 main 의 **추적** 파일을 고치거나 새 not-ignored 파일을 만들면 여전히 deny 된다 — hook 입력에 격리 여부가 없어 "worktree 디렉토리에서 시작" 과 구별할 수 없다. 그 편집은 main 직접 편집이라 ① 규약상으로도 확인 대상이고, `~/.claude` 의 `plans/` 는 예외로 허용된다.
- 묶음 공통 "fixture 는 실제 hook stdin" 처분: 테스트 stdin 은 합성(`{cwd, tool_name, tool_input}`)이지만 필드 형태는 실제 hook stdin 과 같다 — 근거: Acceptance 8 에서 실제 hook stdin 이 새 guard 를 end-to-end 로 거쳐 기대 판정을 냈고(cwd·file_path 모두 `/private/tmp/…` 형태로 일치), 09-14 telemetry 행(실제 stdin)의 cwd·detail 도 같은 형태다. 캡처 fixture 는 추가하지 않는다.
- 커밋 단위: 1) `fix(guard): narrow worktree-outside deny to tracked and new unignored main files` — `scripts/guard-worktree-edit.js`·`scripts/guard-worktree-edit.test.js`·`scripts/dlc-signal.test.js`·`README.md` 2) `docs(wiki): correct native-overlap 1b — native isolation skips sessions started in a worktree` — `wiki/pages/decision/native-overlap-ledger.md`·`wiki/pages/concept/worktree-per-task.md`·`wiki/pages/decision/dlc-wt-autoflow.md`·`wiki/index.md`·`wiki/log.md`. plan·intent 는 마지막 커밋(단위 2 의 fixup)에.

# Review Disposition
- [plan] CONDITIONAL. ⚠️ self-flag(새 파일 미차단) — resolved: 전제 오류 확인, 규칙 (C) 채택(사용자 결정). 강 traversal 테스트가 `projects/` 예외 제거로 무의미 — fix(`plans/../scripts/foo.js` 로, 변이본 FAIL 확인). 강 대장·wiki 에 옛 `retire` 서술 잔존 — fix(대장 4곳 포인터, `worktree-per-task`·`dlc-wt-autoflow` 정정, CLAUDE.md §3-1 은 Deferred). 강 intent 의 stdin fixture 제약 — fix(Decisions 에 처분 + Acceptance 8 실세션). 약 위험 단계(공유 헬퍼 → ① 도 바뀜, 옵션 위치 오류 시 조용한 fail-open) — fix(Decisions 에 양성 대조 유지). 약 새 fail-open 경로·상속 `GIT_*` — fix(`GIT_LOCAL_ENV` 제거 + 테스트, 경로 목록 Decisions). 약 대소문자 무시 FS(macOS 에서 `Tracked.js` 를 `tracked.js` 로 편집하면 ls-files 1 → 새 경로도 아님(존재) → allow) — accepted-risk(대소문자만 다른 경로로 편집하는 경우는 드물고 옛 ② 대비 좁아진 구멍이다). 약 실측 변수(모드·headless) — fix(대장에 linked worktree 명시·모드 차이 서술 ⚠️). 약 측정 행 telemetry 오염 — fix(대장·Progress 에 측정 행 명시, 이후 실측은 `CLAUDE_DLC_SIGNAL_OFF=1`). 약 Acceptance 3 에 ① 변화 누락·"repo 없음" 이름 — fix(ⓞ 추가, spawn 실패·128 두 케이스로). 약 구현 전 Red 증거 — fix(스크래치에서 옛 guard 로 Red 8건). 약 Windows 미검증 — accepted-risk(아래 Deferred 가 아니라 리스크로 Report). 약 (C) 채택 시 메시지·README — fix. 누락 시나리오 resume 시 격리 복원 — deferred.
- [code] APPROVE, blocker 없음. Minor `.env` 처럼 worktree 에 사본이 있는 gitignored 파일이 allow 로 바뀜 — wontfix(규칙 유지: 사본 유무로 deny 하면 worktree 에도 plan 사본이 있던 2026-09-14 오탐이 다시 막힌다. 해는 모델이 main 절대경로로 `.env` 를 쓸 때만 난다) + fix(머리 주석·README 의 "worktree 사본이 없다"를 "대개 없다 + `.env` 예외" 로). Minor 테스트가 guard 크래시를 allow 로 셈 — fix(`decide`·`decideMain` 이 비0 종료를 `'crash'` 로). Minor 대장 84·85행 정정 포인터 없음 — fix. Minor "worktree 디렉토리에서 시작한 세션만" 서술이 좁음(격리 해제 뒤 `cd` 복귀 누락, 대장의 "EnterWorktree 세션에 한해서" 가 미측정 세션 종류까지 배제) — fix(머리 주석·README·대장·`worktree-per-task`·index·intent). Minor `~/.claude` fixture `.gitignore` 가 실물과 다름 — fix(실물 whitelist `.gitignore` 복사, `telemetry/` 새 파일·기존 untracked `scripts/draft.js` 케이스, `settings.json` 은 실물대로 ignored). Nit `.git/` 새 파일 deny 문구가 없는 worktree 경로로 안내 — fix(`.git/` 을 common dir 로 allow, 일반 repo fixture 로 Red→Green — `~/.claude` fixture 에서는 whitelist `/*` 가 `.git` 도 ignore 로 판정해 이미 allow). Nit `GIT_LOCAL_ENV` 복제 — wontfix(편집마다 도는 hook 에 SessionStart hook 모듈을 싣지 않는다 — 주석에 이유). Nit plan 오타 — fix. Minor 대소문자 무시 FS — 이미 accepted-risk. Open fixture `git` 이 상속 `GIT_*` 를 안 지움 — 조치 없음(git hook 이 테스트를 돌리지 않는다 — `pre-commit-check.sh`·`install-hooks.sh` 확인). Open `.claude/` 메타 allow 가 다른 worktree 편집도 통과 — Deferred(기존 동작).

# Deferred
- CLAUDE.md §3-1 의 "이미 worktree 세션 안이면 하네스 네이티브 격리가 이들의 main 경로 편집도 거부" 는 EnterWorktree 세션에만 맞다(worktree 디렉토리에서 시작한 세션은 격리되지 않는다 — 대장 "1b 정정"). 운영 자산이라 승인 후 별도 작업. 심각도 낮음(memory 적립을 main 복귀 후에 하라는 결론은 그대로 맞다).
- EnterWorktree 세션을 resume 했을 때 네이티브 격리가 복원되는지 모른다 — 복원되지 않으면 ② 의 적용 면적이 늘어난다. `claude --worktree`·subagent `isolation: worktree` 세션도 재지 않았다. 실측 필요. 심각도 낮음.
- `scripts/guard-worktree-edit.js` 의 `<repo>/.claude/` 메타 allow 가 `<repo>/.claude/worktrees/<다른 wt>/` 편집도 통과시킨다(worktree 사이 오염) — 기존 동작, code-reviewer 발견. 심각도 낮음.
- Windows 미검증 — Git for Windows 가 `C:/…` forward-slash pathspec 을 `ls-files`·`check-ignore` 에서 받는지, 드라이브 문자 대소문자가 다를 때(기존 prefix 비교 — fail-open)의 동작. Windows 머신에서 `node scripts/guard-worktree-edit.test.js` 로 확인.

# Key Files
- `scripts/guard-worktree-edit.js` — 기능 ①(ask)·②(deny) 판정, `git()`·`isTracked`·`isNewUnignored`.
- `scripts/guard-worktree-edit.test.js` — ② 실 git fixture 케이스·① 케이스.
- `scripts/dlc-signal.test.js` — 통합(guard) deny 신호 테스트(실 git fixture).
- `README.md` — `guard-worktree-edit.js` 절·`hooks.PreToolUse` 줄·파일 트리.
- `wiki/pages/decision/native-overlap-ledger.md` — 1b 판정·2026-08-12 관측표·"1b 정정" 절.
- `wiki/pages/concept/worktree-per-task.md`·`wiki/pages/decision/dlc-wt-autoflow.md` — 같은 서술의 정정.
- `plans/2026-09-27-improve-followups/intent.md` — 묶음.

# Blockers
