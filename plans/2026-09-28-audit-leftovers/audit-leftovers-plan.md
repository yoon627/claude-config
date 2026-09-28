---
title: audit-leftovers — 감사 저우선 잔여(pre-push stdin·heal 3건·statusline 쿼터 헬퍼)
status: done
started: 2026-09-28
updated: 2026-09-28
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal
`repo-audit-remaining` plan `# Deferred` 저우선 절의 미배정 항목을 처리한다 — 남은 것은 고치고, 이미 해소된 것은 근거와 함께 닫고, Windows 실측이 필요한 ps1 항목은 `windows-ps1-verify` 단위로 넘긴다.

# Intent
- 묶음: `plans/2026-09-25-repo-audit-followups/intent.md` 의 audit-leftovers 단위.
- 델타(사용자 결정 2026-09-28 — 처분안 승인):
  - 여기서 고침(5): (1) pre-push 스캔의 sh 가드가 push 커밋과 제외 목록을 `git log` 인자 대신 stdin(`--stdin`)으로 넘기고 중복을 뺀다 — 입력이 비면 차단 (2) heal `git submodule deinit` 에 `--literal-pathspecs`(+ `GIT_*_PATHSPECS` 제거) (3) heal 이 `.git` 파일을 git 과 같은 `gitdir: ` 형식일 때만 gitlink 로 본다 (4) heal 수동 복구 안내의 `rm -rf` 를 OS 중립 문구로 (5) statusline 의 Claude·Codex 쿼터 표시 중복을 헬퍼 하나로, lock 25초 > refresh timeout 20초 결합을 statusline 쪽 주석으로.
  - `windows-ps1-verify` 로 넘김(3): ps1 pre-push 스캔의 같은 stdin 수정, ps1 `~/.claude` 면제의 `Resolve-Path` symlink 미해소, notify.ps1 balloon — pwsh 가 worktree 세션에서 격리 가드에 막히고(이 머신 PATH 에도 없다), PS5.1·Windows 동작 확인이 필요하다. notify.ps1 은 2026-06 감사가 `ShowBalloonTip` 뒤 `Start-Sleep 5`+`Dispose()` **추가**를 제안했고(표시 전 소멸 가능) 아직 적용되지 않았다 — Windows 에서 표시 여부를 보고 적용을 정한다.
  - 닫음(2): statusline readdir 선형 비용(`32f0787` 에서 bg 표시와 함께 사라짐), heal `_force_rmtree` symlink chmod(audit-install-fixes 에서 해소 — `_retry_readonly` 가 Windows 에서만·링크 제외).
  - 기각(1): heal 의 "corrupt 시그니처 확인 후에만 reset" — 범위는 wt 생성 경로 기준이다(heal 은 `/wt` 가 새 worktree 를 만든 직후에만 자동으로 돌고 `modules` 는 worktree 별). 그 경로에서 작업 트리가 빈 submodule 은 이번 clone 이 만든 것이라 리셋으로 잃는 것은 불완전한 objects 뿐이고, 파일이 남은 submodule 이 하나라도 있으면 게이트가 어떤 리셋보다 먼저 멈춘다. git 오류 문자열 매칭은 버전·로케일에 따라 오판한다. 예외 ⚠️: 오래 쓴 worktree 에서 heal 을 손으로 다시 돌리면 deinit 해 둔(작업 트리가 빈) submodule 의 module dir 에 있던 push 안 한 커밋이 지워질 수 있다. 검토 후 보류한 셋째 안: 오류 문자열 대신 module dir 에 gitlink 커밋이 있는지 `git cat-file -e` 로 보는 구조 검사(로케일 무관) — 자동 경로에서는 이득이 없어 보류.
- Constraints: 가드·heal 은 모든 머신에서 도는 운영 코드라 기존 테스트 전부 통과 유지. pre-push 는 fail-closed 유지(git 실패 → 차단).
- Out of scope: ps1 파일 변경(위 이관), cache/lock 경로 상수의 공유 모듈화(`require` 로 공유할 수는 있지만 상수 셋에 새 파일을 만들 만큼의 이득이 없다 — 주석으로 결합만 드러낸다).
- 분할: 없음 — 세 모듈(sh 가드·heal·statusline)은 각자 머지 가능하지만, 사용자가 저우선 잔여를 한 단위로 정했고(2026-09-27) 항목마다 몇 줄이라 plan 별 worktree·리뷰·머지 고정비가 크다. 대신 목적별 커밋 단위로 나눈다.

# Acceptance
1. sh pre-push 스캔이 push 커밋과 제외(published) 커밋을 `git log --stdin` 으로 넘기고(명령줄에 sha 없음) 순서를 지키며 중복을 빼고, 입력이 비거나 만들지 못하면 차단한다(fail-closed — `--stdin` 은 빈 입력·첫 빈 줄에서 HEAD 로 대체한다). 확인: `bash scripts/pre-commit-check.test.sh` — 새 케이스 (a) git shim 이 기록한 `log` 인자에 `^?` 40자리 sha 가 없다(제외 sha 가 있는 push 포함, sh) (b) 한 커밋을 가리키는 ref 50줄에서도 토큰을 막는다 (c) HEAD 는 clean 이고 체크아웃 안 된 push ref 에만 토큰이 있어도 막는다 (d) dedupe 가 아무것도 내지 않고 exit 0 이면 막는다(sh) — (a) 는 첫 구현 전 Red, (d) 는 `sort -u` 판(`de0de8c`)에서 Red(통과 — fail-open), 지금 전부 PASS. 기존 pre-push 케이스 전부 PASS. ps1 엔진은 이 머신에 pwsh 가 없어 로컬에서 관찰하지 못했다(ps1 코드는 바꾸지 않았다).
2. heal 이 `git --literal-pathspecs submodule deinit -f -- <path>` 로 부르고, `main()` 이 `GIT_{LITERAL,GLOB,NOGLOB,ICASE}_PATHSPECS` 를 지운다(함께 쓰면 git 이 fatal). `.gitmodules` path 의 glob 문자가 다른 submodule 로 번지지 않는다(2026-09-28 실측: plain `sub*` 는 두 submodule 을 해제, literal 은 매칭 없음). 확인: `python3 skills/wt/test_heal_submodules.py` 의 deinit 인자·환경변수 단언.
3. heal 의 작업 트리 검사가 `.git` 파일을 git 이 gitlink 로 읽는 형식(`gitdir: `, BOM 불허)일 때만 제외한다 — 다른 내용·빈 파일·공백 없는 `gitdir:`·BOM 붙은 파일은 "파일 있음"(리셋 거부). 확인: 같은 테스트의 새 케이스, 기존 `test_only_dotgit`·`test_worktree_with_only_dotgit_is_safe` PASS. 모듈 docstring·`references/rm-recovery.md` 거부 조건이 이 기준을 적는다.
4. heal 수동 복구 안내(로그)가 POSIX 전용 `rm -rf` 대신 OS 중립 문구다(`references/rm-recovery.md` 에는 `rm -rf` 가 없다 — grep). 확인: `heal_submodules.py` read.
5. statusline 의 Claude·Codex 쿼터 표시가 한 헬퍼를 쓰고 출력은 그대로다. 확인: `node scripts/statusline.test.js` — 리팩터 전에 추가한 특성 테스트(퍼센트+시각·퍼센트만·시각만·Codex 캐시 `primary`)가 리팩터 전후 모두 PASS. lock 25초와 refresh timeout 20초의 결합이 statusline 쪽에 주석으로 있다.
6. 묶음 intent: 이 단위 줄은 plan 경로와 실제 처분(고침 5·이관 3·닫음 2·기각 1)으로, `windows-ps1-verify` 줄에 ps1 이관 3건(notify.ps1 은 감사 제안 미적용으로)이 적혀 있다. `repo-audit-remaining` plan `# Deferred` 저우선 절에 처분이 표시된다.
7. README `pre-commit-check` 절이 stdin 전달·빈 입력 차단·ps1 은 아직 인자임을 적고, 커버리지 수(pre-push 스캔 51)가 테스트와 맞다.
8. `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없이).

# Progress
- 2026-09-28: worktree 생성(base `origin/main@38d5007`). Explore — 11개 항목을 코드·이력으로 대조(처분은 Intent). heal deinit 실측: `git submodule deinit -f -- 'sub*'` 가 subA·subB 둘 다 해제, `git --literal-pathspecs …` 는 "did not match" 로 0개(git 2.54). pwsh 는 이 worktree 세션에서 격리 가드가 실행을 막는다. 사용자 결정: 처분안대로.
- 2026-09-28: plan-reviewer 병행 중 TDD — statusline: 특성 테스트 2개를 리팩터 전에 추가(현재 코드 5 passed) → `quotaPiece` 헬퍼·결합 주석 → 5 passed, 단위 커밋. heal: Red 2(literal pathspec 인자·`.git` 내용 검사) → 구현 → 34 OK(3.13·3.9), 단위 커밋. pre-push: Red 1(shim 이 본 `git log` 인자에 sha) → `rev_input | git log --stdin` → 67 passed(ps1 엔진은 pwsh 가 PATH 에 없어 skip), shellcheck 통과, 단위 커밋.
- 2026-09-28: plan-reviewer CONDITIONAL(Review Disposition `[plan]`, Codex 는 크레딧 소진으로 생략 — pre-push 는 보안 영향이 있어 원래 병행 대상). pre-push: 테스트 보강 → `de0de8c`(sort 판)에서 Red 1(dedupe 가 빈 출력·exit 0 → 통과) → `rev_input` 을 awk·변수·빈 입력 차단으로 → 69 passed, shellcheck 통과, README 커버리지 51·stdin 서술, fixup. heal: Red 2(환경변수·gitlink 기준) → `main()` 의 `GIT_*_PATHSPECS` 제거·`gitdir: ` 기준·docstring·rm-recovery 거부 조건 → 35 OK(3.13·3.9), fixup. 기록(intent 두 줄·audit plan 처분·이 plan) fixup.
- 2026-09-28: code-reviewer REQUEST CHANGES(`[code 1]`, Codex 생략 — 크레딧). shim 테스트 입력 조립 수정·stdin 기록 단언 → 69 passed, 제외를 argv 로 되돌린 변이본에서 FAIL. 가드 주석 분리, statusline 테스트 헬퍼 통합(5 passed). fixup 2개.
- 2026-09-28: simplify — 변경 없음. 격리 runner: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음), pre-commit 69 passed/0 failed(`ps1: skipped (no pwsh)` — A1 에 명시), heal 35 OK(3.13·3.9), statusline 5 passed, shellcheck 0건. heal·rm-recovery 의 `rm -rf` 0건(grep). evidence gate: Acceptance 1~8 충족 → DONE.
- 2026-09-28: commit-check 적용(사용자 승인) — 10개 → 목적 단위 3개, heal·pre-push 메시지를 현재 동작(`gitdir: ` 기준·환경변수 제거, awk dedupe·빈 입력 차단)으로 갱신. 최종 트리 동일. `/e merge` — PR #188(브랜치 push 때 새 sh 가드가 stdin 경로로 통과).

# Next

# Review Disposition
- [plan] CONDITIONAL. 강 pre-push fail-closed 구멍(`git log --stdin` 빈 입력 HEAD 대체 + 파이프라인이 dedupe 실패를 못 봄) — fix(awk·변수·빈 입력 차단, 케이스 (c)·(d)). 강 notify.ps1 "닫음" 근거를 거꾸로 읽음(원 감사는 `Start-Sleep 5`+`Dispose()` 추가 제안) — fix(닫음에서 빼고 이관 문구 정정). 강 README 커버리지·stdin 서술 누락 — fix. 약 heal `--literal-pathspecs` 와 `GIT_*_PATHSPECS` 충돌 — fix(`main()` 에서 제거, 테스트). 약 기각 전제 범위 — fix(wt 생성 경로 기준·수동 재실행 예외·`cat-file` 구조 검사 보류 기록). 약 shim 이 제외 쪽을 안 봄 — fix(제외 sha 포함, `^?` 정규식). 약 ps1·skip 관찰 불가 — fix(Acceptance 에 명시). 약 최고 위험 단계 미지목 — fix(Decisions). 약 intent audit-leftovers 줄이 원래 범위 — fix. 약 절차 순서·커밋 순서 — fix(Decisions 에 실제 순서·fixup 대상). 약 `--not` 기각 사유 보강 — fix. Nit docstring — fix. Nit `_is_gitlink` 기준 — fix(git 과 같게). Nit 복구 안내에 실제 경로 — wontfix(게이트가 멈춘 경로가 여러 개일 수 있어 일반 안내 유지). Nit rm-recovery 거부 조건 — fix. Nit Out of scope 사유 — fix.
- [code 1] REQUEST CHANGES — 운영 코드(sh 가드 stdin·fail-closed, heal, statusline)는 결함 없음(statusline 은 base 에 특성 테스트를 돌려 출력 동일 독립 확인). Major shim 테스트 입력 `"$many$(line …)"` 가 명령 치환의 끝 줄바꿈 제거로 두 ref 줄을 합쳐 제외 sha 가 malformed 줄에 묻힘 — fix(한 명령 치환에서 조립, shim 이 `git log` stdin 도 기록해 `^<b>` 가 stdin 으로 간 것을 단언. 제외를 argv `--not` 으로 되돌린 변이본에서 FAIL 확인). Minor plan 과 테스트 불일치 — fix(위로 해소). Nit 주석이 `rev_input` 위에 `added_lines` 헤더 — fix(주석 분리). Nit `rev_input` 을 pathspec 마다 두 번 — wontfix(awk 1회 차이, 빈 입력 판정을 `added_lines` 한 곳에 둔다). Nit env pop 을 `main()` 에서 — wontfix(`init_submodules` 를 `main()` 없이 부르는 곳은 테스트뿐이고 run 은 mock). Nit `_is_gitlink` 는 접두어만 본다 — wontfix(대상 검증을 더하면 heal 이 고치려는 corrupt module dir 에서 리셋을 거부한다, Decisions 문구 정확화). Nit statusline 테스트 spawn 헬퍼 중복 — fix(`run(script, input, env)`). fix loop 1회로 종료 — Major 는 테스트 전용이고 변이본으로 검증돼 재리뷰를 돌리지 않았다.

# Decisions
- 커밋 단위(커밋 순서): 1) `refactor(statusline): share quota formatting between Claude and Codex rows` — `statusline.js`·`scripts/statusline.test.js` 2) `fix(heal): literal pathspecs, gitlink content check, OS-neutral recovery hint` — `skills/wt/heal_submodules.py`·`skills/wt/test_heal_submodules.py`·`skills/wt/references/rm-recovery.md` 3) `fix(pre-push): hand scanned commits to git log on stdin` — `scripts/pre-commit-check.sh`·`scripts/pre-commit-check.test.sh`·`README.md`. plan·intent·audit plan 은 마지막 단위(pre-push)의 fixup 으로.
- **가장 위험한 단계는 pre-push 가드**다 — install-hooks 를 설치한 모든 repo 가 `~/.claude/scripts/` 에서 직접 부르고 autopull 로 곧바로 퍼지며, fail-open 은 되돌릴 수 없는 유출이다. 그래서 fail-closed 회귀 케이스((c)·(d))를 그 검증으로 둔다.
- pre-push 의 `--stdin`: `git log --stdin` 이 stdin 에서 리비전을 읽는다(pathspec 은 명령줄 `--` 뒤). 제외 커밋은 `^<sha>` 줄로 넘긴다. 기각: stdin 의 `--not` 줄 — 어느 git 버전부터 되는지 확인하지 못했고(⚠️ 2.54 에선 동작 — plan-reviewer 실측), `sort -u` 로 섞으면 `-`(0x2D)가 맨 앞으로 정렬돼 모든 리비전을 부정해 스캔 0건으로 통과한다(fail-open).
- dedupe 는 `sort -u` 에서 `awk 'NF && !seen[$0]++'` 로 변경 (이유: plan-reviewer — `git log --stdin` 은 빈 입력·첫 빈 줄에서 HEAD 로 대체하고 rc 0 이라(2.54 실측) 입력 생성이 조용히 실패하면 HEAD 이력을 훑는 fail-open 이 된다. `sort` 는 Windows Git Bash 에서 System32 `sort.exe` 와 이름이 겹칠 수 있다 ⚠️. awk 는 이 가드가 이미 쓰고 순서를 지켜 push 커밋이 먼저 나온다). 입력은 변수로 먼저 만들고 비면 `return 1`(fail-closed).
- heal `_is_gitlink` 는 git 의 gitfile 읽기와 같은 접두어 검사 `gitdir: `(공백 포함, BOM 불허 — 대상이 git 디렉토리인지는 보지 않는다: corrupt module dir 를 고치는 게 heal 의 목적이라)로 판정한다로 변경 (이유: plan-reviewer — git 이 gitlink 로 읽지 않는 파일을 gitlink 로 빼면 안 된다). 쓰다 중단돼 빈 `.git` 파일이 남은 경우도 이제 리셋을 거부한다 — 안전한 쪽의 트레이드오프로 수용.
- intent.md 의 `windows-ps1-verify` 줄 편집은 §10 소유권(자기 plan 줄만)의 예외다 — 아직 착수한 세션이 없는 `(미착수)` 줄이고 사용자가 이관을 승인했다(2026-09-28).
- ps1 의 같은 수정은 넘긴다 — PS5.1 의 native 프로세스 stdin 파이프(인코딩·줄끝)는 Windows 에서 확인해야 하고, sh 와 ps1 이 달라지는 기간은 Windows 에서 wrapper 가 sh 가드를 부르므로(`install-hooks.sh`) `install-hooks.sh` 로 설치한 곳은 sh 가 덮는다. `install-hooks.ps1` 로 설치하면 wrapper 가 `powershell … pre-commit-check.ps1` 을 부르므로(확인) 그 설치는 이관이 끝날 때까지 명령줄 한계가 남는다 — 차단 쪽(fail-closed)이라 유출은 없고 790+ ref 신규 push 가 막히는 불편이다.
- statusline 은 매 2초 도는 표시라 헬퍼 추출 외 동작 변경 없음. 특성 테스트를 먼저 넣어 리팩터 전 출력을 고정한다(현재 쿼터 표시 테스트가 없다).

# Key Files
- `scripts/pre-commit-check.sh`·`scripts/pre-commit-check.test.sh`·`README.md`(pre-commit-check 절) — pre-push 스캔.
- `skills/wt/heal_submodules.py`·`skills/wt/test_heal_submodules.py`·`skills/wt/references/rm-recovery.md` — heal.
- `statusline.js`·`scripts/statusline.test.js` — 쿼터 표시.
- `plans/2026-09-25-repo-audit-followups/intent.md`·`plans/2026-09-25-repo-audit-remaining/repo-audit-remaining-plan.md` — 처분 기록.

# Blockers
