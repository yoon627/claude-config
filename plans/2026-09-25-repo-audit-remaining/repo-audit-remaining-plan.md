---
title: repo-audit-remaining — G1 heal 경로 탈출 차단·G2 pre-push 가 push 범위의 추가 줄을 스캔 (보안)
status: in_progress
started: 2026-09-25
updated: 2026-09-25
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

G1: `heal_submodules.py` 가 `.gitmodules` 의 name 으로 repo·`.git` 밖을 지우는 경로를 막고, 파서를 바로잡는다. G2: pre-push 가 push 되는 커밋 범위에서 `plans/*.md`·`settings.json` 에 추가된 줄을 스캔한다. 두 감사에서 남은 다른 항목은 intent 의 `(미착수)` 단위로 추적한다(상세는 아래 `# Deferred`).

# Intent

→ `plans/2026-09-25-repo-audit-followups/intent.md` (묶음 공통 Problem·Constraints·Open questions 는 거기).

이 plan 에만 더해지는 것:
- Problem:
  - G1: `/wt` 는 worktree 를 만들 때마다 `heal_submodules.py` 를 자동 실행한다. submodule update 가 실패하면 `.gitmodules` 의 name 으로 `git rev-parse --git-path modules/<name>` 을 구해, 경로 검증 없이 `rmtree` 한다.
    - name 에 `../` 가 있으면 repo 밖 디렉토리가 지워진다.
    - `/wt` 가 쓰는 linked worktree 에서는 `modules/../../../objects` 가 `<main>/.git/objects`, 즉 main repo 의 object DB 전체를 가리킨다(plan-reviewer 실측).
    - 파서는 `--get-regexp` 출력을 첫 공백에서 잘라 공백이 든 name 을 잘못 읽는다. 그러면 데이터 보호 게이트가 엉뚱한 경로를 검사한다.
  - G2: pre-push 비밀 스캔은 `HEAD:settings.json` 만 본다. `settings.json` 은 2026-09-07 부터 untracked 라 지금은 아무것도 검사하지 않는다. 그래서 pre-commit 을 건너뛴 커밋이 PUBLIC 원격에 검사 없이 올라갈 수 있다 — `--no-verify`, commit-check(plumbing 이라 훅 없음), 다른 도구로 만든 커밋.
- Constraints:
  - sh·ps1 쌍의 동작을 맞춘다(Windows 는 ps1 훅).
  - 기존 pre-commit 동작과 main/master 직접 push 차단(`~/.claude` 면제)은 바꾸지 않는다.
  - 훅은 매 push 마다 사용자 기계에서 돌므로 push 되는 범위만 본다.
  - 보안 게이트는 입력을 해석할 수 없거나 git 이 실패하면 막는다(fail-closed).
  - heal 은 stdlib 만 쓴다.
  - ps1 은 PS5.1 에서도 동작해야 한다. PS7 전용 구문(`??`·`?.`·삼항·`&&`)은 쓰지 않는다.
  - 훅은 main checkout 의 `$HOME/.claude/scripts/pre-commit-check.*` 를 exec 한다. 머지 즉시 두 머신의 모든 repo push 에 적용된다(SessionStart 자동 pull). 설치된 래퍼(`.git/hooks/pre-push`)는 머신별 파일이라 갱신되지 않고 원격 이름을 넘기지 않는다.
- Out of scope: G3 이후(intent `(미착수)`), CI 서버측 백스톱(G9), 래퍼가 원격 이름을 넘기게 하는 것(G5), 비밀 패턴 목록 변경, 매치 샘플 30자 출력, 기존 pre-commit 경로의 PS5.1 CP949 디코딩.
- Open questions:
  - (열림) PS5.1 실제 동작 — 이 Mac 은 pwsh 7 뿐이다. Windows 머신에서 첫 push 로 확인한다(`# Next` 의 머지 후 단계).
- 사용자 결정(2026-09-25):
  - G2 는 "push 범위의 추가 줄 스캔"으로 한다.
    - 기각: CI 백스톱으로 대체 — push 된 뒤에야 잡혀 PUBLIC repo 에선 이미 공개된 뒤다.
    - 기각: 최소 수정 — settings.json 이 untracked 라 실효가 없다.
  - ps1 은 pwsh 설치 후 검증한다(`~/.local/powershell/pwsh` 7.x, sudo 없이 공식 tarball).
- 분할: 묶음 → `plans/2026-09-25-repo-audit-followups/intent.md` (G3 이후는 `(미착수)` 단위). G1·G2 는 한 plan 에 두 커밋 단위로 둔다. 각자 머지할 수 있지만 같은 감사에서 나온 보안 수정 두 건이라 한 PR 로 함께 리뷰·dogfood 한다. 되돌림은 커밋 단위로 한다(`--merge` 머지라 커밋 보존). plan-reviewer 2026-09-25 의 세 번째 선택지다.

# Acceptance

G1 — `python3 skills/wt/test_heal_submodules.py`. 새 테스트는 수정 전 Red, 수정 후 Green:
1. 경로 탈출(main worktree 배치): `<tmp>/repo`(실제 `git init`) + `<tmp>/victim`(파일 1개).
  - `.gitmodules` name 은 `../../../victim` 이고, 실행 전에 "`--git-path modules/<name>` 을 resolve 한 경로 == victim" 을 단언한다.
  - repo 를 cwd 로, `GIT_DIR`·`GIT_WORK_TREE` 를 제거한 환경에서 실행한다.
  - 통과 기준: update 가 실패하면 deinit·삭제 전에 비정상 종료하고, victim 과 그 파일이 남는다.
2. 경로 탈출(linked worktree 배치 — `/wt` 실사용): linked worktree 에서 name 이 `<main>/.git/` 아래 sentinel 로 풀리는지 먼저 단언한다. 통과 기준: 거부하고 sentinel 이 남는다.
3. 공백 파싱: name·path 에 공백이 있으면 실제 `git config` 로 정확히 읽는다(`[("my sub", "my sub dir")]`).
4. fail-closed: 다음 경우 update 실패 뒤 reset 없이 비정상 종료한다.
  - `.gitmodules` 에 path 항목이 없음.
  - 값 없는 `path`.
  - `git config` 문법 오류(rc 128).
5. 회귀 없음: 정상 중첩 name(`manager/app/resources/templates`)은 검증을 통과해 heal 이 진행된다. 기존 테스트도 전부 통과한다.

G2 — `bash scripts/pre-commit-check.test.sh`. 모두 실제 커밋 fixture 다. block 케이스는 exit≠0 에 더해, stderr 에 `[BLOCKED]` 와 기대 사유 문자열이 있어야 통과로 센다(크래시와 차단 구분):
6. 선형 이력:
  - plans/*.md 토큰 추가 → 차단. 깨끗한 추가 → 허용.
  - 범위 안에서 넣었다 지운 토큰 → 차단.
  - settings.json 금지 키 추가 → 차단.
7. merge 토폴로지:
  - 사이드 브랜치에서 넣었다 지운 뒤 `--no-ff` merge → 차단.
  - merge 해결에서만 들어온 토큰(evil merge) → 차단.
8. 사용자 설정: repo config `color.ui=always`·`diff.noprefix=true`·`diff.mnemonicPrefix=true` 에서도 토큰 추가 → 차단.
9. 경계·입력:
  - remote-tracking ref 에 이미 있는 커밋의 토큰 → 허용(다시 보지 않음). 삭제 push(zero local sha) → 허용.
  - annotated tag push(깨끗) → 허용. 커밋이 아닌 객체를 가리키는 tag → 차단.
  - 필드 수가 4가 아닌 stdin 줄 → 차단. 해석 불가 local sha → 차단.
  - plan blob 이 사라진 손상 repo(git log 실패) → 차단.
  - ref 여러 개 중 하나만 불량 → 차단.
10. patch 파싱: 본문이 `++` 로 시작하는 추가 줄(패치에서 `+++ sk-ant…`)의 토큰 → 차단. plans → settings.json rename + 금지 키 → 차단.
11. 기존 main 차단 케이스(면제 2 + 차단 2 + 무관 브랜치 1)는 실제 sha 로 바꿔 유지한다.
12. 우회 안내: 차단 메시지가 pre-push 는 `git push --no-verify`, pre-commit 은 `git commit --no-verify` 다(sh·ps1).
13. ps1 일치: `PWSH=~/.local/powershell/pwsh bash scripts/pre-commit-check.test.sh` 에서 같은 케이스가 ps1 로 전부 통과한다. 하네스는 `ps1: ran N` 또는 `ps1: skipped (no pwsh)` 를 출력하며, 이 줄은 하네스를 직접 실행해 확인한다(verify.sh 는 성공 출력을 버린다).

공통:
14. worktree 에서 `bash scripts/verify.sh` → `ALL PASS`(skip 없음).
15. dogfood(머지 전 가장 비싼 단계): worktree 의 새 가드를 실제 repo 3곳(`~/.claude`·`~/Repos/knowledge_base`·`~/Repos/coin-trading-bot`)에서 실행한다. `<현재 브랜치 ref> <tip> <ref> <zero>` 줄을 stdin 으로 먹인다. 통과 기준: 모두 허용이고 소요 시간을 기록한다.
16. 문서: 아래가 바뀐 동작과 맞는다.
  - README 가드 절(35·114·118·186·432·434·436·442 부근)에 push 범위 스캔·탈출구(`git push --no-verify`, `.git/hooks/pre-push` 제거)를 적는다.
  - `scripts/install-hooks.{sh,ps1}` 안내 문구, `pre-commit-check.sh` 헤더 주석.
  - `skills/wt/references/rm-recovery.md` §B 에 heal 의 새 중단 동작.
  - `grep -n "HEAD" README.md | grep -i "settings.json"` 에서 옛 "HEAD settings.json 스캔" 서술 0건.

# Progress

- 2026-09-25: commit-check 합치기 적용(승인) → `f5b95a9`(G1)·`4f44adb`(G2+plan), tree 동일. 사용자 선택 "wiki ingest 후 /e merge" → wiki `git-log-added-lines-hardening` 을 세 번째 단위로 추가.
- 2026-09-25: evidence gate — Acceptance 1~16 충족, 판정 DONE. 격리 runner(`final_verify.sh`) 대조 일치: verify.sh `ALL PASS`(skip 없음), 하네스 sh 45/45·sh+ps1 90/90(`ps1: ran 45`), heal 29 OK, plan-lint ok, README 옛 서술 0건, rm-recovery §B 반영. Acceptance 15 dogfood 는 위 줄. PS5.1 은 미검증(Open question).
- 2026-09-25: 표적 재리뷰 APPROVE(Major 2 해소, 추가 벡터 — `GIT_CONFIG_*` 주입·`diff.relative`·`GIT_DIFF_OPTS`·`core.attributesFile`·textconv attribute 등 — 전부 차단 실측) + Minor 2·Nit 3 → fix loop 2: fixup `820cd69`(G1 `\r` 보존)·`d229bbe`(ps1 env 정리를 `Remove-Item Env:` 로, `.exe` 우선, README 커버리지 수, sh pre-push 분기 병합). heal 29 OK, 하네스 90/90.
- 2026-09-25: code-reviewer(+codex) REQUEST CHANGES(Major 2·Minor 7·Nit 4) → fix loop 1: fixup `c313142`(G1)·`16e7964`(G2). 하네스 sh 45 + ps1 45 = 90/90, 옛 sh 는 새 케이스 11 실패·옛 ps1 은 9 실패(Red 증거), heal 28 OK. dogfood(15): 실제 repo 3곳 sh·ps1 모두 허용(sh 0.06s·ps1 0.35s), 원격 없는 첫 push(~/.claude 전체 이력) sh 1.21s·ps1 0.46s 허용. 표적 재리뷰 요청.
- 2026-09-25: 구현 — 단위 1(G1) `ec991cf`, 단위 2(G2) `8c9491e` 커밋 전 targeted 검증 통과. heal 테스트 24 OK, 하네스 sh+ps1 68/68(pwsh 7), 옛 ps1 로 돌리면 13 실패(Red 증거). mutation 점검: `-m`·`--no-color`·헤더 상태 기계를 빼면 해당 케이스가 실패.
- 2026-09-25: G1·G2 착수 — Explore 완료, pwsh 7 설치(검증용). plan-reviewer(+codex) CONDITIONAL → S1~S9 반영. tracker 를 intent `repo-audit-followups` 로 분리.
- 2026-09-25: repo-audit-fixes 를 닫으면서 생성(사용자 선택 "닫고 미해소만 새 plan"). 같은 날 이 plan 밖에서 한 일:
  - 권한 규칙 축소(`settings.json` ask 10→72, `settings.local.json` 두 파일의 파괴적 allow 제거, 백업 `~/.claude/backups/permissions-20260925/`).
  - `claudeMdExcludes` 로 `~/.claude/AGENTS.md` 제외.
  - 원격 브랜치 3개 삭제(commit-split 은 로컬 태그 `archive/commit-split` 51d55d9 로 보존).

# Next

commit-check 로 fixup 4개 + plan fixup 을 두 단위에 합치기(승인) → `/e merge`(push·PR·CI·머지, 요청 시) → fix loop → simplify → verify → dogfood(15) → 문서(16) → Report. 머지 후: Windows 머신에서 첫 push 로 PS5.1 동작 확인(Open question).

# Decisions

- 커밋 단위:
  1. `fix(wt): heal_submodules refuses unsafe submodule names and parses .gitmodules with -z` — `skills/wt/heal_submodules.py`, `skills/wt/test_heal_submodules.py`, `skills/wt/references/rm-recovery.md`
  2. `fix(pre-commit-check): pre-push scans lines added in the pushed range` — `scripts/pre-commit-check.{sh,ps1}`, `scripts/pre-commit-check.test.sh`, `scripts/install-hooks.{sh,ps1}`(안내 문구만), `README.md`
  - plan·intent 파일은 마지막 단위 fixup 에만 싣는다.
- **G1 설계**:
  - 파서는 `git config -z -f .gitmodules --get-regexp '^submodule\..*\.path$'` 를 쓴다.
    - 출력 형식(실측): 레코드는 `key\nvalue\0`, 값 없는 path 는 `key\0`, 값에 개행이 들어갈 수 있다.
    - 첫 `\n` 에서만 나눈다. 값 없는 레코드는 불량으로 본다.
    - 종료코드: 0 = 항목 있음, 1 = 항목 없음/파일 없음, 그 외(문법 오류 128) = 오류.
    - `encoding="utf-8"` 을 명시하고 `strip` 하지 않는다(기존 `try_capture` 를 재사용하지 않는다).
  - update 가 실패한 뒤, 어떤 deinit·삭제보다 먼저 모든 항목을 검증한다. 하나라도 불량이면 종료한다(fail-closed).
    - name: 절대경로이거나, `/`·`\` 로 나눈 구성요소에 `..` 가 있으면 거부한다. git 의 submodule name 검사와 같은 기준이다. 중첩 name(`a/b/c`)은 허용한다.
    - 삭제 대상: `--git-path modules/<name>` 을 resolve 한 경로가 `--git-path modules` 를 resolve 한 경로 아래(자기 자신 제외)여야 한다.
    - 항목이 0개이거나 파서 오류면 종료한다.
  - `_reset_submodule` 도 삭제 직전에 같은 containment 를 다시 확인한다(방어 심화).
  - 기각: `..`·경로 구분자를 모두 거부 — 정상 중첩 name 이 회귀한다(옛 Next 문구, plan-reviewer S8).
  - 기각: "repo 안"·"`.git` 안"을 경계로 삼기 — linked worktree 에서 `.git/objects` 삭제를 못 막는다(S7).
  - 테스트는 heal 이 git 을 프로세스 cwd 에서 부르므로 chdir 후 복원하고 `GIT_DIR`·`GIT_WORK_TREE` 를 지운다. heal 함수에 `cwd` 인자를 새로 두지 않는다 — `main()` 이 이미 `chdir` 하므로 실사용 경로는 같다.
- **G2 설계**:
  - pre-push 모드는 stdin 을 한 번만 읽어 배열에 둔다.
    - main 차단은 기존 의미 그대로다(`~/.claude` 면제).
    - 스캔은 모든 repo 에서 한다.
  - 줄마다 필드 4개(`<lref> <lsha> <rref> <rsha>`)를 요구하고, 빈 줄은 건너뛴다. 필드 수가 다르면 차단한다.
  - local sha 가 `^0+$` 면 삭제라 건너뛴다(SHA-256 길이도 처리).
  - 그 외는 `<lsha>^{commit}` 으로 풀어 모은다.
    - annotated tag 는 가리키는 커밋으로 풀린다.
    - 풀리지 않거나 커밋이 아닌 객체면 차단한다.
  - 스캔 명령은 모은 커밋 전부를 한 번에 순회하며, 경로 종류별로 두 번 실행한다(`settings.json` → 금지 키 + 토큰, `plans/*.md` → 토큰):
    `git --no-replace-objects -c core.quotePath=false -c log.diffMerges=separate -c log.showRoot=true -c log.follow=false log -p --text --no-color --no-ext-diff --no-textconv --full-history -m -U0 --src-prefix=a/ --dst-prefix=b/ --format= <commits…> --not --remotes -- <path>`
    - 코드 리뷰(2026-09-25) 반영: 사용자 config·env·attributes 가 추가 줄을 0건으로 만드는 7경로(`log.diffMerges=off`·`log.showRoot=false`·`log.follow=true`·NUL 바이트·`-diff`/`bigFileThreshold`·pathspec env·`git replace`)를 막는다. `-c log.diffMerges` 는 옛 git 에선 모르는 키라 무시돼 버전 제약이 없다. 스크립트 전체 `LC_ALL=C`(잘못된 UTF-8 바이트가 있는 줄에서 awk 가 죽고 grep 이 건너뛰는 문제 — awk 에만 걸면 grep 이 fail-open), `GIT_*_PATHSPECS` 4개 unset(ps1 은 Process 환경에서 제거).
    - `--full-history`: path 제한 log 의 history simplification 이 사이드 브랜치를 건너뛰어 넣었다 지운 토큰을 놓친다(실측 0건→2건).
    - `-m`: 기본 `-p` 는 merge diff 를 생략해 merge 해결에서만 들어온 줄을 놓친다(실측). 구현 중 `--diff-merges=first-parent`(git 2.31+)에서 `-m`(각 부모와 비교, 버전 제약 없음)으로 바꿨다 — first-parent 가 보는 범위를 모두 포함한다. git 2.54 에선 `-m` 이 이력 단순화도 끄지만(`--full-history` 를 빼도 사이드 브랜치 케이스 통과, mutation 생존) 문서화된 동작이 아니라 `--full-history` 는 명시적 보장으로 둔다.
    - `--no-color`·`--no-ext-diff`·`--no-textconv`·명시적 prefix: 사용자 설정(`color.ui=always` 등)에 따라 매칭이 0건이 되는 fail-open 을 막는다(실측).
    - rename: 경로 종류별로 따로 실행하므로 pathspec 밖에서 들어온 rename 은 짝지어지지 않고 추가 줄로 보인다. `--no-renames` 는 빼도 rename 케이스가 통과해(mutation 생존) 효과가 없어 제거했다.
  - 추가 줄 추출은 상태 기계로 한다. `diff --git` 줄부터 `@@` 줄까지는 헤더로 보고 건너뛴다. 그 뒤 `+` 로 시작하는 줄에서 `+` 를 떼어 낸다. 본문이 `++` 로 시작해도 헤더 필터(`+++ `)에 걸리지 않는다.
  - git 이 0 이 아닌 코드로 끝나면 차단한다. 기존 `2>/dev/null || true` 스타일을 이 경로에는 쓰지 않는다.
  - ps1 은 git 호출을 `System.Diagnostics.Process` 헬퍼로 한다. FileName 은 `Get-Command git -CommandType Application` 의 절대경로다(bare `git` 이면 Windows CreateProcess 가 cwd=repo 루트의 `git.exe` 를 PATH 보다 먼저 찾는다 — 코드 리뷰 Major, ⚠️ .NET 동작은 문서·이슈 근거). stdin 은 `StreamReader`(UTF-8)로 읽는다.
    - stdout 은 UTF-8 로 읽고 종료코드를 받는다. stderr 는 리다이렉트하지 않는다.
    - 이렇게 하면 PS5.1 의 `2>$null` + `EAP=Stop` 종료 오류와 콘솔 코드페이지(CP949) 디코딩을 둘 다 피한다.
    - `ArgumentList` 는 PS7(.NET Core) 전용이라, 공백 없는 인자만 넘기고 `Arguments` 문자열로 조립한다.
  - 기각안:
    - `--remerge-diff`: merge 가 새로 넣은 줄만 보여 더 정밀하지만 git 2.36+ 가 필요해 sh·ps1 양쪽에 버전 분기가 생긴다. first-parent 는 사이드 브랜치 내용을 한 번 더 보지만 path 가 두 종류로 제한돼 비용이 작다.
    - 푸시 tip 의 plans 전체 스캔: 느리고, 범위 중간에 넣었다 지운 비밀을 놓친다.
    - `<rsha>..<lsha>` 범위: 새 브랜치는 rsha 가 zero 이고, rsha 가 로컬에 없을 수 있다.
    - 가드가 `pre-push <remote>` 인자로 대상 원격만 공개로 보기: 래퍼가 인자를 넘기지 않아 지금은 쓸모가 없다(G5 에서 래퍼와 함께).
- accepted-risk:
  - "이미 공개됨"의 경계를 모든 remote-tracking ref(`--not --remotes`)로 둔다. private 원격에서 받은 커밋을 public 원격으로 push 하면 다시 보지 않는다.
  - sh(grep: 대소문자 구분·줄 단위)와 ps1(`-match`: 대소문자 무시·줄 결합)은 매칭 의미가 다르다. ps1 이 더 엄격해서 생기는 차이는 오탐뿐이다. pre-commit 동작 불변 제약 때문에 `Scan-Tokens` 를 바꾸지 않는다. plan-reviewer 가 이 repo 전체 이력의 추가 줄 19,895행을 재현해 오탐 0건을 확인했다.
  - PEM 본문만 추가되고 헤더 줄이 이미 공개된 경우는 줄 단위라 놓친다.
  - 첫 push(원격 ref 가 없는 repo)는 이력 전체를 본다. 이 repo(2.5MB) 는 통과한다(reviewer 실측).
- rollback: G1·G2 는 각자 커밋을 revert 하면 된다.
  - G2 의 fail-closed 버그는 모든 repo 의 push 를 막는다. revert push 조차 그 가드를 타므로, 탈출구는 `git push --no-verify` 또는 `.git/hooks/pre-push` 제거다. README 에 적는다.
- CI: ubuntu-latest 에는 pwsh 가 기본 설치돼 있어 하네스의 ps1 케이스가 CI 에서도 돈다(범위 확장, 수용).
- ⚠️ 분할 규칙과 단일 tracker plan 이 상충했다 → tracker 를 intent.md 로 옮겨 해소했다. G1·G2 는 한 plan 에 두 커밋 단위로 둔다(Review Disposition self-flag 1).
- ⚠️ PS5.1 전용 동작(native stderr 처리·코드페이지)은 이 Mac 의 pwsh 7 로 재현할 수 없다. Process 헬퍼와 PS7 전용 구문 금지로 피해 가지만 실제 PS5.1 은 미검증이다(Open question).
- ⚠️ 해석 불가·비커밋 local 객체를 fail-closed 로 바꾸면서, 가짜 sha 를 쓰던 기존 pre-push 테스트를 실제 커밋으로 바꾼다. 실제 pre-push 는 로컬 객체를 넘기므로(githooks(5)) 영향은 커밋이 아닌 객체를 가리키는 tag push 뿐이며, 그것은 의도적으로 차단한다.

# Review Disposition

- [plan] S1 history simplification — fix(`--full-history` + 사이드 브랜치 fixture, Acceptance 7).
- [plan] S2 merge 해결 줄 누락 — fix(`--diff-merges=first-parent`, evil merge fixture). 기각 `--remerge-diff` 는 Decisions.
- [plan] S3 사용자 설정 fail-open — fix(`--no-color`·`--no-ext-diff`·`--no-textconv`·명시적 prefix, Acceptance 8·10. `--no-renames` 는 구현 중 효과 없음으로 제거 — Decisions).
- [plan] S4 fail-closed 범위 — fix(git rc·필드 수·비커밋 객체, Acceptance 9).
- [plan] S5 하네스가 크래시와 차단을 구분 못함 — fix(`[BLOCKED]` + 사유 단언).
- [plan] S6 G1 테스트 격리 — fix(`<tmp>/repo`·`<tmp>/victim`, resolve 사전 단언, chdir 복원, env 제거).
- [plan] S7 linked worktree `.git` 내부 — fix(Acceptance 2, 경계를 `--git-path modules` 로).
- [plan] S8 Next·Decisions 모순 — fix(옛 G1·G2 체크리스트를 Decisions 기준으로 대체).
- [plan] S9 머지 시 tracker 소실 — fix(intent `repo-audit-followups` 로 분리, 착수 전 반영).
- [plan] 약: 원격 경계 → accepted-risk. sh/ps1 매칭 의미 → accepted-risk. `Resolve-Path` symlink → defer(실측으로 확인됨, `# Deferred` 저우선에 기록 — 기존 동작이고 G2 범위 밖). verify skip 관찰 → fix(Acceptance 13). patch 파싱 → fix(상태 기계·경로별 2회·`-U0`·한 번 순회·`^0+$`). G1 파서 세부 → fix. `_force_rmtree` symlink → defer(intent audit-low-batch). 가장 비싼 단계 → fix(Acceptance 15). 문서 범위 → fix(Acceptance 16). Intent 형식 → fix(Open questions·Constraints).
- [code] Major pushed-range 스캔 config/env/attributes fail-open(7경로) — fix(경화 옵션·`LC_ALL=C`·env unset, 회귀 케이스 11).
- [code] Major ps1 cwd `git.exe` hijack — fix(PATH 절대경로). Windows 실행 재현은 못 함.
- [code] Minor locale awk/grep — fix(`LC_ALL=C` 전체). Minor ps1 stdin CP949 — fix(UTF-8 StreamReader, PS5.1 미검증). Minor 명령줄 32K 한계 — defer(fail-closed 이고 790+ ref 동시 push 에서만 — `# Deferred`). Minor G1 strip·형제 겹침 — fix(`_git_path`·overlap 검사). Minor containment 테스트 누락 — fix(symlink·reset 재확인 테스트). Minor 임시 디렉토리 누수 — fix(trap). Minor pwsh 없으면 skip — accepted(Open question). Minor plan S3 의 `--no-renames` 불일치 — fix(아래 S3 줄 정정).
- [code] Nit 죽은 `if git_dir:`·None 사유 로그·ordinal `StartsWith`·merge 출력 소음 — fix.
- [code] Open private 원격 경계(Codex Critical) — accepted-risk 유지. 변경 전엔 push 범위를 전혀 보지 않았고, 래퍼가 원격 이름을 넘기게 하는 G5 에서 `--not --remotes=<remote>` 로 푼다. Open `deinit -f -- <path>` 가 .gitmodules path 를 pathspec 으로 받음 — defer(변경 전부터 있던 문제, `# Deferred`).
- [code2] Minor PS5.1 `EnvironmentVariables` 대소문자 중복 env 크래시 — fix(프로세스 env 를 `Remove-Item Env:` 로 정리, 자식이 상속). Minor heal text 모드 `\r`→`\n` 변환 — fix(bytes 로 받아 디코드, `\r` name 테스트). Nit README 커버리지 수 — fix. Nit `Get-Command` 가 .cmd shim 을 고를 수 있음 — fix(`.exe`·확장자 없음만). Nit overlap 검사 대소문자 구분(case-insensitive FS) — wontfix(modules 안이고 두 항목 모두 데이터 게이트를 거쳐 영향 무시 수준).
- simplify 체크(메인): sh 앞쪽의 연속된 `pre-push` 분기 두 개를 하나로 합침. 그 외 중복·죽은 코드 없음(`if git_dir:` 는 fix loop 1 에서 제거).
- self-flag 1(분할 vs tracker) — resolved(intent 분리).
- self-flag 2(PS5.1) — accepted-risk. 이유: 이 기기에서 검증 수단이 없다. Process 헬퍼·PS7 구문 금지로 위험을 줄이고, 머지 후 Windows 첫 push 로 확인한다.
- self-flag 3(fail-closed 로 fixture 변경) — resolved(tag 처리 명시·테스트 고정).

# Key Files

- `skills/wt/heal_submodules.py`, `skills/wt/test_heal_submodules.py`, `skills/wt/references/rm-recovery.md` — G1
- `scripts/pre-commit-check.sh`, `scripts/pre-commit-check.ps1`, `scripts/pre-commit-check.test.sh`, `scripts/install-hooks.{sh,ps1}`(안내 문구), `README.md`(가드 절) — G2
- `plans/2026-09-25-repo-audit-followups/intent.md` — 남은 항목 추적(묶음)
- `plans/2026-06-11-repo-audit-fixes/repo-audit-fixes-plan.md` — 원 감사 근거(done)

# Blockers

없음.

# Deferred

intent `repo-audit-followups` 의 `(미착수)` 단위가 참조하는 상세 체크리스트다(2026-09-25 main 기준 줄번호, 착수 시 재확인).

## G3 — statusline.js / subagent-statusline.js (라이브 — 보수적으로)
- bg slug (`statusline.js:161` `/[:\\\/]/g`): `.` 도 `-` 로 치환되는 실제 디렉토리명과 다르다 → `/[^A-Za-z0-9-]/g`. macOS 에서 bg 표시 경로 자체가 틀렸다는 감사 지적(critic-statusline-bg-dead-macos)도 함께 확인한다.
- ctime → birthtime (`:172-177`).
- null stdin (`:28`, `subagent-statusline.js:8`): `JSON.parse(...) || {}`.
- subagent 스키마 드리프트 (`subagent-statusline.js:16-19` `current_usage`) — 양 스키마 fallback. 가능하면 라이브 stdin 캡처로 확정한다.
- (선택) git spawn 3회 → 1회.

## G4 — codex-quota-refresh.js
- `proc.stdin.on("error")` 핸들러가 없어 EPIPE 가 uncaught 로 끝난다.
- `:80` `if (code === 0) return;` — 응답 없이 종료하면 즉시 settle 하지 않는다.
- `:104-106` rename 이 실패하면 `.tmp.<pid>` 가 남는다.

## G5 — scripts/install-hooks.{sh,ps1}
- `ps1:3` `(& git rev-parse --show-toplevel).Trim()` — 비-git 디렉토리에서 null.Trim 예외.
- `sh:13` `hook_dir="$repo_root/.git/hooks"` — linked worktree·`core.hooksPath` 를 고려하지 않는다 → `git rev-parse --git-path hooks`.
- `.bak` 단일 슬롯 덮어쓰기 (`ps1:29`, `sh:32`).
- 래퍼가 pre-push 인자(`<remote> <url>`)를 가드에 넘기게 하고, 가드가 `--not --remotes=<remote>` 를 쓰게 한다(이 plan 의 accepted-risk 해소).

## G6 — gwl 중첩 worktree 이중 마커
- `scripts/gwl.ps1:16`, `scripts/prompt-gwl.py:29`: 가장 긴 매칭 경로 하나만 `→`.

## G7 — .editorconfig
- `[*.ps1]` 에 `charset = utf-8-bom` 이 없다(현재 `end_of_line = crlf` 만) — BOM 파일(gwl.ps1 등)이 저장될 때 BOM 을 잃을 수 있다.

## G8 — 문서 drift (남은 것)
- README 유출 대응 절(`README.md:568-581`): `git push --force-with-lease origin main` 이 자체 pre-push 에 막힐 수 있다. "`permissions.deny` 는 …" 서술도 현행(전역 deny 없음, CLAUDE.md §8)과 다르다.
- code-reviewer·plan-reviewer 의 `CLAUDE_REVIEW_CODEX_MODE=external` 비대칭 — 2026-09-25 감사(refs-06)에서 이 변수를 읽는 코드가 없다고 확인했다. 대칭 문단을 더하기보다 개념을 유지할지 먼저 판단한다.

## G9 — CI
- 비밀 스캔 서버측 백스톱: `.github/workflows/lint.yml` 에 `pre-commit-check` 실행이 없다.
- (선택) statusline 스모크(`{}`·`null` stdin → exit 0).

## 저우선
- pre-push 스캔이 push 커밋 전부를 한 명령줄로 넘긴다 — 790개 넘는 ref 를 새 원격으로 한 번에 push 하면 Windows 명령줄 32,767자 한계로 예외(차단 쪽). 커밋 중복 제거 + `git log --stdin`.
- heal 의 `git submodule deinit -f -- <path>` 는 `.gitmodules` path 를 pathspec 으로 받는다(`path = *` 면 전 submodule deinit). 데이터 게이트는 문자 그대로의 경로를 본다 — `--literal-pathspecs` 검토. 변경 전부터 있던 문제.
- ps1 `~/.claude` 면제 판정이 symlink 를 풀지 못한다(`pre-commit-check.ps1` `$resolve` 의 `Resolve-Path`): HOME 경로가 symlink(`/var`→`/private/var`)를 거치면 sh 는 면제(rc 0), ps1 은 main push 차단(rc 1) — 2026-09-25 pwsh 7 실측, 이번 변경 이전부터 있던 동작. 주석 "resolved because either side can be a link" 도 ps1 에선 사실이 아니다. 하네스는 FAKE_HOME 을 `pwd -P` 로 정규화해 이 문제와 분리했다.
- notify.ps1 balloon fallback — 원래 지적한 `Start-Sleep`·`Dispose` 문자열이 현재 파일에 없다. 코드가 바뀌었는지 먼저 재확인한다.
- statusline fmtQuota 중복, cache/lock 상수 양 파일 중복, readdir 선형 비용.
- heal 후속(선택): `.git` 파일 `gitdir:` prefix 검증, update 실패 시 corrupt 시그니처 확인 후에만 reset, `rm -rf` 로그 OS 중립화, `_force_rmtree` 가 symlink 를 따라 chmod 하는 문제(`heal_submodules.py:105-107`).
- 기존 pre-commit 경로의 ps1 이 native 출력을 콘솔 코드페이지(CP949)로 디코딩하는 문제(PS5.1).

## 2026-09-25 전체 감사 미처리 항목
workflow `wf_3746ca79-3e4` 결과는 세션 스크래치라 여기 요약만 남긴다.
- (high) Codex 쪽이 2026-08-01 Codex 앱 import 스냅샷에 멈춰 있다.
  - `~/.codex/AGENTS.md`: 원격 브랜치 무확인 삭제, `.Codex/plans/` 경로.
  - `~/.agents/skills/*` 사본: 41커밋 미반영. jira-worklog 는 Windows 경로라 Mac 에서 실행되지 않고 bootstrap 3b 가 exit 1 로 멈춘다.
  - `~/.codex/agents/*.toml`.
  - `~/.claude/.codex/config.toml`: 제거하기로 한 serena MCP 를 고정 안 된 git+https 소스로 기동한다.
  - Codex `hooks.json` 에 dlc-early-stop·worktree 게이트가 없다.
- (해소 2026-09-25) `~/.claude/AGENTS.md` 가 main checkout 의 Claude 세션에 주입되던 문제 — `claudeMdExcludes` 로 제외.
- (medium) `scripts/verify.sh:37` `find_repo` 가 ignored 디렉토리까지 스캔한다 → main checkout 에서 항상 `FAILED: 1`.
- (medium) `/improve` 권장의 `last-improve` 마커를 쓰는 코드가 없다(`scripts/session-brief.js:124`).
- (medium) `skills/synced/` 가 `.gitignore` 에 없다(PUBLIC repo).
- (medium) CLAUDE.md §8 "다른 repo main 푸시는 pre-push 훅이 하드 차단" 은 사실이 아니다. §3-1 이 가리키는 `/e` 8단계에 memory 절차가 없다(low).
- (medium) user `autoMode.environment` 가 knowledge_base 전용 서술인데 모든 세션에 적용된다.
- (medium) GitHub main 에 branch protection·ruleset 이 없다 + SessionStart 자동 pull 이 CI 결과 없이 ff 한다.
- (medium) `scripts/bootstrap/README.md:63` 이 settings.json 을 tracked 로 서술한다.
- (low) 다음 항목들:
  - codex-review effort 서술과 README `--no-verify` 안내.
  - RTK.md 가 gitignored 인데 CLAUDE.md 가 `@import` 한다.
  - wiki 모델 목록 stale, memory 끊긴 링크, pyright-lsp 바이너리 없음.
  - native-overlap 대장 50일 경과.
  - dlc-early-stop 이 Bash 로 한 편집을 못 본다.
  - 권한 규칙 잔여 한계: `bash <script>`, 브랜치 이름 없는 push.
