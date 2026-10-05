---
title: guard-214-followups — #214 2·4·6: verify 요약의 ps1 실행 여부, 가드 git 옵션 공유, 용어 목록 Read 거부 절차
status: done
started: 2026-10-03
updated: 2026-10-05
---

# Goal
이슈 #214 의 2·4·6 을 처리한다. verify 요약에 ps1 엔진이 돌았는지 건너뛰었는지 보이게 하고, `pre-commit-check` 두 엔진(sh·ps1)이 세 곳에 따로 적은 git 옵션 묶음을 엔진마다 한 곳으로 모으고, 비공개 용어 목록을 도구로 읽지 못하게 하는 머신별 설정 절차를 README 에 적는다.

# Intent
- Problem: (2) `verify.sh` 는 테스트 안의 `SKIP ` 줄만 요약에 올려, `pre-commit-check.test.sh`·`install-hooks.test.js` 가 찍는 `ps1: ran`/`skipped` 가 `ok` 한 줄에 묻힌다 — PR #213 CI 에서 ps1 이 돌았는지 로그로 확인하지 못했다. (4) 비밀 스캔과 비공개 용어 스캔이 같은 하드닝 옵션을 엔진마다 세 번씩 적는다 — 한쪽만 고치면 그 스캔만 눈이 먼다. (6) 목록 파일을 에이전트가 도구로 읽지 않게 하는 절차가 없다. 사용자 결정(2026-10-03): 세 항목 지금 처리.
- Constraints:
  - 동작 불변 — (4) 는 각 git 호출의 인자 집합을 바꾸지 않는 리팩터다. 순서는 같은 영역 안에서만 바뀔 수 있다 — 전역 옵션(`--no-replace-objects`·`-c`)은 서브커맨드 앞, log 옵션은 서브커맨드 뒤·`--` 앞, pathspec 은 `--` 뒤. 기존 테스트 수와 결과가 같아야 한다(새로 더하는 회귀 케이스 제외).
  - 이 Mac 에는 pwsh 가 없어 ps1 은 CI(pwsh 7)에서만 검증된다 → PR(`/e merge`)로 마무리하고 CI 로그에서 ps1 실행을 확인한다.
  - 비공개 용어와 목록 내용을 어디에도 적지 않는다.
- Out of scope: #214 5(ps1 쌍둥이 정리 검토)·7(잘못된 UTF-8 판정 차이)·10(다른 공개 repo opt-in)·1(다른 머신의 목록). Bash `cat` 까지 막는 규칙(아래 Decisions). Windows PowerShell 5.1 엔진 검증(CI 는 Linux pwsh 7 만).
- Open questions:
  - (열림) Grep·Glob 도구에 Read 거부가 걸리는지 — 문서는 best-effort 라 하고 실측은 안 했다.
  - (열림) Bash `cat`·`head` 가 막히지 않은 원인 — 문서는 막는다고 적는다(2.1.288·auto 모드 실측과 다름).
- 분할: 없음 — 세 단위가 각자 머지돼도 무모순이지만, 모두 같은 가드의 작은 후속이고 (4) 의 ps1 검증을 (2) 의 가시성이 받쳐 한 PR 의 CI 로그로 함께 확인하는 편이 싸다(plan·worktree·리뷰·머지 고정비 1회).

# Progress
- 2026-10-03: worktree 생성(base `origin/main@8eeb8fd`). Explore — 옵션 중복 3곳(sh `added_lines`·`pt_log`/`pt_scan_pushed`·`pt_scan_staged`, ps1 `Get-AddedLines`·`Invoke-PrivateLog`/`Invoke-PrivatePushed`·`Invoke-PrivateStaged`), `verify.sh` `run()` 은 `^SKIP ` 만 요약. 이 Mac 의 사용자 설정에 `Read(~/.claude/private-terms.txt)` deny 를 넣고 미끼로 실측했다 — Read 도구는 막히고 Bash `cat`·`/bin/cat`·`head` 는 막히지 않았다(2.1.288, auto 모드). Bash deny 미끼 추가는 auto 모드 분류기가 [Self-Modification] 으로 거부해 시험하지 못했다.
- 2026-10-03: plan-reviewer 반영 후 단위 1 커밋 — 이 Mac 의 verify 에서 두 테스트 `ok` 줄 아래 `SKIP [ps1] …`, 마지막 줄 `ALL PASS (skip: install-hooks.test.js(case) pre-commit-check.test.sh(case) install-codex-skill.test.ps1)`, test.sh 123 유지, `CI=1`·pwsh 없음 → exit 1, 가짜 repo 에서 `NOTE ` 줄이 skip 에 안 들어감을 관찰. 단위 2 — 적대 설정 회귀 케이스 4개를 먼저 넣어 리팩터 전 127 통과(특성화) → 묶음 리팩터 후 127 통과. sh 는 git shim 으로 변경 전후 argv 를 기록해 영역별 multiset 동일·출력 동일(staged 패치 `--no-ext-diff` 중복만 차이), ps1 은 배열을 정적으로 펼쳐 같은 결과. 변형 실행 진행 중.
- 2026-10-03: 단위 2·3 커밋. 변형 실행(sh) — 비공개 용어 호출부에서 묶음을 뺀 변형 4종 모두 검출, 옵션 단위로는 동작이 같은 변형만 생존(Decisions), quotePath 케이스를 더해 그 변형도 검출. 코드 리뷰 workflow(리뷰어 3 + 반박 검증 2, Codex 미가용 — 2026-09-30 크레딧 소진 세션 캐시): 코드 결함 0, 문서 minor 1·nit 3 반영(fixup). simplify: `verify.sh` NOTE 블록 단순화(fixup). 최종 검증(격리 runner): `verify.sh` 마지막 줄 `ALL PASS (skip: install-hooks.test.js(case) pre-commit-check.test.sh(case) install-codex-skill.test.ps1)`, test.sh 128 passed, `CI=true`·pwsh 없음 → exit 1 과 안내문, README 문구 12개 확인. Acceptance 2 와 3 의 CI 부분은 PR CI 대기.
- 2026-10-05: commit-check 로 커밋 7개 → 3개(fixup 흡수, 단위 2·3 메시지 갱신 — 사용자 승인, tree 동일 확인). 로컬 main 의 미게시 커밋을 사용자 승인으로 push(머지 뒤 main 자동 pull 이 ff 로 되도록). main 규칙은 `strict_required_status_checks_policy: false` 라 rebase 없이 `/e merge` 진행. PR #233.

# Next
- 없음 (머지 뒤 #214 의 2·4·6 체크는 이 세션에서 사용자 승인으로 처리, main 세션 후속은 `# Deferred`).

# Decisions
- 관련 wiki: `git-log-added-lines-hardening`(각 옵션이 막는 실명 경로 — 리팩터 뒤에도 그대로 유지해야 할 목록), `lesson-agent-hook-if-best-effort`(가드는 실제 훅 경로로 시험). 뒤집는 결정 없음.
- (2) 형식: 엔진별로 보고한다 — pwsh 가 있으면 `NOTE [ps1] ran N`, 없으면 `SKIP [ps1] no pwsh`(기존 `SKIP` 경로로 verify 마지막 줄 skip 목록에 오름), powershell.exe 가 있으면 `NOTE [ps51] ran M`(없는 macOS·Linux 에서는 줄 없음). `run()` 은 `NOTE ` 줄을 `ok` 줄 아래에 보이되 skip 목록에 넣지 않는다. `install-hooks.test.js` 도 이미 쓰는 `SKIP [ps1] …` 형식에 맞춰 `NOTE [ps1] ran (<pwsh 경로>)`/`SKIP [ps1] …`. CI(`CI` 환경변수)에서 pwsh 가 없으면 `pre-commit-check.test.sh` 를 실패시킨다(`record-verified.test.sh` 의 jq 선례) — 가시성만이 아니라 ps1 검증이 조용히 빠지는 것을 막는다. 기각: verify.sh 가 `ps1: ` 줄을 특정해 grep — 테스트마다 다른 문구를 verify 가 알아야 한다. (리뷰 반영: ps1·ps51 을 한 카운터로 세던 결함, 형식 통일, CI 강제 여부)
- (4) 모양 → **묶음별 사용처를 나눠 적는 것으로 변경** (이유: plan 리뷰 major — staged 스캔은 `git log` 가 아니라 `git diff --cached` 라 log 설정을 넣으면 인자가 늘어난다): 엔진마다 배열 셋 — 전역 묶음(`--no-replace-objects -c core.quotePath=false -c log.diffMerges=separate -c log.showRoot=true -c log.follow=false`, 서브커맨드 앞)은 log 두 곳(`added_lines`·`pt_log`), 걷기 묶음(`log --stdin --full-history`)도 그 두 곳, 패치 묶음(`-U0 --text --no-color --no-ext-diff --no-textconv --src-prefix=a/ --dst-prefix=b/`, 서브커맨드 뒤·`--` 앞)은 세 곳(`added_lines`·pushed 패치·staged 패치). staged 패치 호출은 공통 인자에 이미 `--no-ext-diff` 가 있어 한 번 더 들어간다 — 동작이 같아 허용한다. 호출마다 다른 것(`diff.renames`·`i18n.logOutputEncoding`·`-M`·`-m`·`-p`·pathspec)은 그 자리에 남긴다. 기각: 함수 하나로 git 호출 전체를 감싸기 — 세 호출의 인자 차이를 매개변수로 넘겨야 해 오히려 복잡하다.
- (4) 회귀 방지: 비공개 용어 경로(pre-commit staged·pre-push)에 적대 설정(`color.ui=always`·`diff.noprefix`·`log.diffMerges=off`·`log.showRoot=false`·`log.follow=true` 등)을 건 케이스를 엔진마다 더한다 — 지금은 이런 케이스가 비밀 스캔 쪽에만 있어, 묶음이 빈 값으로 펼쳐져도(두 엔진 모두 미정의 변수 검사 없음) 비공개 용어 스캔은 조용히 fail-open 된다. 리팩터 전에 넣어 통과를 확인하고(특성화), 옵션 하나를 일부러 뺀 변형이 이 케이스에 걸리는지 확인한다. 가장 위험한 단계는 단위 2 다(보안 가드의 무음 fail-open, ps1 은 CI 로만 검증).
- (6) 범위 → **규칙 위치를 프로젝트 로컬 `~/.claude/.claude/settings.local.json` 으로 변경** (이유: plan 리뷰 major — 사용자 설정 `settings.json` 에 두면 README:509 의 "`permissions.deny` 비어 있음" 서술과 모순되고 CLAUDE.md §8 의 "전역 deny 는 두지 않는다"와 부딪힌다. 사용자가 승인한 문구도 "이 Mac 의 settings.local.json"이었다(2026-10-03 AskUserQuestion). 목록을 쓰는 가드는 `~/.claude` 에서만 돌아 그 프로젝트 세션을 막으면 충분하고, `/wt` 가 새 worktree 에 이 파일을 복사한다). 이 Mac 에서 사용자 설정에 먼저 넣었던 항목은 main 세션에서 옮긴다. README Install D 에는 절차와 효과를 **실측과 문서로 나눠** 적는다: 실측(2.1.288·macOS·auto 모드) — Read 도구 차단, Bash `cat`·`/bin/cat`·`head` 통과. 문서(permissions 페이지) — Grep·Glob 은 best-effort, Bash 파일 명령에도 적용된다고 적음. Windows 미검증. Bash 규칙은 auto 모드 분류기가 미끼 추가를 막아 시험하지 못했으므로 권하지 않는다(미검증 스위치 금지 — memory). 기각: sandbox 로 OS 수준 읽기 제한 — Bash 도구에서 실행한 `git commit` 의 훅(같은 하위 프로세스)도 목록을 못 읽어 가드가 fail-closed 로 모든 커밋을 막는다(⚠️ 추정).
- (4) 변형 실행 결과(sh, 2026-10-03): 비공개 용어 경로의 호출부에서 묶음을 뺀 변형 4종(pt_log 전역·pushed 패치·staged 패치·pt_log 걷기)은 새 케이스가 모두 잡는다. 옵션 하나씩 뺀 변형 15종 중 잡히지 않은 것은 동작이 같은 변형으로 본다 — `--no-replace-objects`(두 엔진이 `GIT_NO_REPLACE_OBJECTS=1` 을 이미 export), `--full-history`(git 2.54 에서 `-m` 만으로 사이드 브랜치를 걷는다 — probe: `-m` 이나 `--full-history` 중 하나만 있어도 토큰 2줄, 둘 다 없을 때 0줄), `-U0`(문맥 줄은 `+` 로 시작하지 않는다), `--no-ext-diff`(git log 는 `--ext-diff` 없이 외부 diff 를 쓰지 않고 staged 호출은 기본 인자에 이미 있다), `--src-prefix=a/`(파서는 `+++` 줄만 본다). `-c core.quotePath=false` 는 동작이 다르다 — 빠지면 비ASCII 용어가 든 경로의 내용 적중 라벨이 숨김 대신 8진 escape 경로로 찍힌다(scratch 사본 실측) → **pushed 케이스 1개 추가로 변경** (이유: 케이스가 없어 변형이 살아남았다. 라벨은 `path (hidden)` 이라 출력이 ASCII 로 남아 Windows 콘솔에서도 비교가 같다). 리뷰가 끝난 뒤 단위 2 fixup 으로 넣는다.
- (6) worktree 서술 → **"worktree 세션도 main checkout 의 파일을 읽는다(Windows 제외)" 로 변경** (이유: 코드 리뷰 — settings 문서 "Where Claude Code keeps the local file in a git repository": 2.1.211 이후 worktree 는 main checkout 루트의 `.claude/settings.local.json` 을 쓰고, Windows·홈 디렉토리 루트·비 git·소유자 불일치면 시작 디렉토리 파일을 쓴다. 위 (6) 의 "`/wt` 가 새 worktree 에 이 파일을 복사한다" 는 Windows 에서만 필요한 근거다). macOS·Linux 에서 worktree 세션에 실제로 걸리는지는 미실측 — main 세션에서 항목을 옮긴 뒤 worktree 세션에서 Read 를 재 보면 확인된다.
- CLAUDE.md §8 해석: "전역 `deny` 는 두지 않는다"는 push 규칙을 전역 settings 에 두는 문제(이 repo 까지 막음)를 다룬다. 목록 Read 거부는 프로젝트 로컬에 두므로 이 문장과 부딪히지 않는다 — CLAUDE.md 는 고치지 않는다.
- 커밋 단위: 1) `test(verify): show whether the ps1 engine ran` — `scripts/verify.sh`·`scripts/pre-commit-check.test.sh`·`scripts/install-hooks.test.js`·README 의 해당 서술 2) `refactor(pre-commit-check): share the git log and patch options per engine` — `scripts/pre-commit-check.sh`·`.ps1` → **회귀 케이스(`scripts/pre-commit-check.test.sh`)와 README 의 공유 묶음 문장·용어 케이스 수(52→56)도 단위 2 에 넣는 것으로 변경** (이유: 케이스는 리팩터의 안전망이라 같은 커밋에 있어야 그 커밋만 봐도 검증되고, README 수치는 그 케이스가 바꾼다) 3) `docs(readme): add the Read deny rule for the private-terms list` — README Install D. README 는 1·3 이 다른 줄을 고쳐 단위별로 차례대로 편집·커밋한다.
- rollback: 단위별 커밋 revert(공개 식별자 정리와 무관해 revert 가 안전하다). settings 규칙은 항목 하나만 지운다 — `jq '.permissions.deny |= map(select(. != "Read(~/.claude/private-terms.txt)"))'` 를 그 파일에 적용(파일 통째 복원은 그 사이 다른 변경까지 되돌리므로 쓰지 않는다).

# Acceptance
1. pwsh 가 없는 이 Mac 에서 `bash scripts/verify.sh` 의 `pre-commit-check.test.sh`·`install-hooks.test.js` `ok` 줄 아래에 `SKIP [ps1] …` 가 보이고, 마지막 줄 skip 목록에 두 테스트의 `(case)` 가 더해진다. 기준선(변경 전 마지막 줄): `ALL PASS (skip: install-codex-skill.test.ps1)`. 관찰: verify 출력.
2. pwsh 가 있는 CI 에서 같은 두 줄 아래에 `NOTE [ps1] ran …` 이 보인다. 관찰: PR CI 로그. (CI 는 Linux pwsh 7 만 — 5.1 은 미검증으로 PR 본문에 적는다.)
3. (4) 뒤에 `pre-commit-check.test.sh` 결과가 바뀌지 않는다 — 이 Mac(sh) 통과 수가 기준선 123(+ 새 회귀 케이스 수)이고, CI(ps1 포함)도 통과. 관찰: 변경 전후 test.sh 요약 대조 + CI.
4. 세 호출의 git 인자 집합이 변경 전과 같다(staged 패치의 `--no-ext-diff` 중복만 예외) — 관찰: diff 로 옵션 대조. 새 회귀 케이스는 비공개 용어 경로에서 옵션 하나를 뺀 변형을 잡는다 — 관찰: 변형 실행.
5. README: Install D 에 Read 거부 절차와 실측·문서 구분, verify 절(463행 부근)에 `NOTE ` 줄 규칙, install-hooks·pre-commit-check 커버리지 서술(474·485행 부근)이 새 형식과 맞다. 관찰: rg.
6. `bash scripts/verify.sh` 마지막 줄 — 기준선의 skip 에 두 테스트의 `(case)` 만 더해진다.
7. 비공개 용어 적중 0(diff·커밋 메시지·PR 본문).

# Review Disposition
- [plan major] log 묶음을 세 호출(staged diff 포함)에 쓰면 인자가 늘어남 — fix: 묶음별 사용처를 나눔(Decisions (4)).
- [plan major] 비공개 용어 경로에 하드닝 회귀 테스트가 없어 무음 fail-open 가능 — fix: 적대 설정 케이스 + 변형 확인, 단위 2 를 가장 위험한 단계로 지목.
- [plan major] README:509·CLAUDE.md §8 과 사용자 설정 deny 의 모순, 승인 근거 — fix: 규칙을 승인 문구대로 프로젝트 로컬로 옮기고 §8 해석을 Decisions 에.
- [plan major] README 가 실측과 문서를 구분할 근거, sandbox 대안 — fix: 공식 permissions 문서를 메인이 직접 확인(WebFetch)해 실측과 나눠 적고, sandbox 는 기각 사유와 함께 Decisions 에.
- [plan minor] ps1·ps51 한 카운터 — fix: 엔진별 보고.
- [plan minor] verify 절 README 동기화 — fix: Acceptance 5 에 추가(474행은 출력 형식 서술만).
- [plan minor] CI 에서 pwsh 부재 시 조용히 빠짐 — fix: CI 에서 실패. 5.1 미검증은 PR 본문에.
- [plan minor] "git 옵션은 순서와 무관" 부정확 — fix: Constraints 문구.
- [plan minor] settings rollback 을 통째 백업에 기댐 — fix: 항목 하나만 지우는 절차.
- [code minor, 검증 confirmed] README Install D 의 "worktree 세션은 그 worktree 의 settings.local.json 을 읽는다 — 사본 필요" 가 settings 문서(2.1.211+: worktree 는 main checkout 루트의 파일을 읽음, Windows 등 예외)와 어긋남 — fix: 플랫폼별로 나눠 적음(macOS·Linux 는 main 파일, Windows 는 worktree 사본에 항목 추가·통째 덮어쓰기 금지).
- [code minor → 검증 refuted, nit] '실측' 이 규칙을 사용자 설정에 둔 상태에서 잰 것임을 밝히지 않음 — fix: 괄호에 배치 명시.
- [code nit] `permissions.deny` 줄의 새 괄호(프로젝트 로컬 deny)와 "deny 는 프로젝트 단위 범위 지정이 불가" 가 같은 줄에서 부딪힘 — fix: "사용자 설정의 deny 는" 으로 한정.
- [code nit] README 의 묶음 문장이 `-m`·환경변수까지 묶음에 있는 것처럼 읽히고 staged 가 쓰는 묶음을 흐림 — fix: 묶음별 사용처와 묶음 밖 항목을 적음, "눈이 머는" 비유도 직설로.
- [code note] 새 merge 케이스의 `git merge --no-commit` 안내문이 테스트 출력에 섞임 — wontfix: 판정·카운트 무관이고 기존 비밀 스캔 케이스(같은 형태)와 같다.
- [simplify] `verify.sh` 의 `NOTE` 블록 `if grep -q` 는 skip 집계가 없어 불필요 — fix: 파이프 한 줄로(가짜 repo 로 출력 동일 확인).
- [plan nit] `--full-history` 공통 — fix: 걷기 묶음에 포함. [nit] Open questions 없음 — fix. [nit] 형식 통일 — fix. [nit] Acceptance 6 기준선 — fix. [nit] 공용 wiki `git-log-added-lines-hardening` 의 "ps1 은 아직 argv" 가 낡음 — defer(# Deferred).

# Deferred
- `~/.claude` main 세션: 사용자 설정의 `Read(~/.claude/private-terms.txt)` deny 를 `~/.claude/.claude/settings.local.json` 으로 옮기고(Decisions rollback 의 jq 처럼 항목 하나만 — 파일 통째 복원 금지) main 세션과 worktree 세션에서 Read 차단을 다시 잰다. README Install D 의 "worktree 세션도 main checkout 의 파일을 읽는다" 실측이 이것으로 확인된다.
- 공용 wiki `git-log-added-lines-hardening` 의 "ps1 은 아직 argv 로 넘긴다" 서술이 낡았다(지금은 `-Stdin`) — `~/.claude` main 세션에서 고친다. 같은 페이지에 이번에 확인한 사실도 더할 후보: git 2.54 에서 `git log -m` 은 `--full-history` 없이도 net-zero 사이드 브랜치를 걷는다(가드에서 `--full-history` 는 `-m` 과 겹치는 이중 장치), 옵션 묶음이 엔진마다 한 곳으로 모였다.
- `/wt` 의 settings.local.json 복사 근거("worktree 는 자기 자신이 git root 라 localSettings 를 상속하지 않는다" — README `skills/wt/` 절, `skills/wt/SKILL.md`·`references/env-copy.md`)가 2.1.211 이전 모델이다. settings 문서상 macOS·Linux 는 main checkout 의 파일을 읽고 Windows 만 사본이 필요하다. 심각도 낮음(복사는 해롭지 않고 Windows 에는 필요) — 운영 자산(skill)이라 승인 후 별도 작업.

# Key Files
- `scripts/verify.sh` — `run()` 의 `NOTE ` 줄 표시.
- `scripts/pre-commit-check.test.sh`·`scripts/install-hooks.test.js` — ps1 실행 보고 형식.
- `scripts/pre-commit-check.sh`·`scripts/pre-commit-check.ps1` — 옵션 묶음 공유.
- `README.md` — install-hooks 커버리지 서술, Install D 절차.

# Blockers
- 없음.
