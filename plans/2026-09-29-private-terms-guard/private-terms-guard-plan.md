---
title: private-terms-guard — 공개 repo(~/.claude)에 비공개 식별자가 다시 커밋·push 되지 않게 규칙·기계 차단
status: in_progress
started: 2026-09-29
updated: 2026-09-29
---

# Goal
`~/.claude`(공개 repo)에 회사·조직 이름, 비공개 repo 이름, 사내 티켓 키가 다시 들어가지 않게 한다. (1) CLAUDE.md §11 공개 점검의 대상을 wiki 적립 작업에서 이 repo 의 모든 커밋·push 로 넓히고 (2) 추적하지 않는 로컬 목록으로 `scripts/pre-commit-check.sh`·`.ps1` 가 해당 커밋·push 를 막는다. 목록 자체는 공개되지 않는다.

# Intent
- Problem: plan 은 7월 plans-sync 부터 공개로 추적되고 근거를 구체적으로 적는데, §11 공개 점검은 2026-09-26(`5a4bbe3`)에야 공용 wiki 적립 작업 한정으로 생겼고 `pre-commit-check` 는 `settings.json`·`plans/*.md` 의 토큰 패턴만 본다. 그래서 회사 식별자가 plan·README·wiki 에 쌓였다(2026-09-29 `0db7fde`·`02c499a` 로 wiki 밖 정리, 과거 이력은 그대로 두기로 결정). GitHub issue #206 의 3번.
- Constraints:
  - 가드는 `install-hooks` 를 실행한 **모든 repo** 가 `~/.claude/scripts/pre-commit-check.sh` 한 벌을 공유하고, merge 되면 `ci/verified` → SessionStart 자동 pull 로 모든 머신에 바로 퍼진다 — 검사는 `~/.claude` 에만 걸리고, 다른 repo 에서는 판정 실패를 포함해 어떤 경우에도 막지 않는다.
  - 훅은 동기·무timeout — 공개 여부를 네트워크로 조회하지 않는다([[git-hook-network-safety]]).
  - CI 가 pre-push 가드를 다시 돌린다 — CI 에는 목록이 없고 없어야 한다(목록을 secret 으로 넣지 않는다, [[ci-secret-scan-backstop]]).
  - 기존 이력·wiki 에 식별자가 남아 있다 — **추가된 내용만** 본다(파일 전체 스캔 금지).
  - 새 검사가 내는 출력에는 목록 원문·걸린 줄을 넣지 않는다. 기존 위반 메시지(경로·ref 원문 출력)는 이번에 바꾸지 않으며 한계로 적는다.
  - wiki/ 는 보관 방식 결정 대기라 수정하지 않는다(사용자 로컬 기록). jira-worklog 스킬은 사용자 지시로 그대로 둔다.
  - test.sh·README 예시에는 합성 용어만 쓴다(실제 목록을 읽거나 옮기지 않는다).
- Out of scope: PR 제목·본문·GitHub 웹 편집·`--no-verify`(git 훅 밖 — §11 규칙이 담당), annotated tag 본문(pre-push 가 tag 객체를 받으므로 읽을 수는 있지만 이 repo 는 tag 를 거의 쓰지 않아 비용 대비 이득이 작다 — tag 이름은 rref 검사로 잡는다), 새 훅 종류(commit-msg), install-hooks·CI 워크플로 변경, 다른 공개 repo 적용(opt-in 은 Deferred), 과거 이력 재작성.
- 분할: 없음 — 규칙 문구(§11·§8·README)가 가드 동작을 서술해 한 머지에서만 문서↔코드가 일치하고, sh·ps1 쌍둥이는 같은 test.sh 가 두 엔진으로 검사해 따로 머지하면 pwsh 가 있는 CI 에서 앞 단위가 red 가 된다.
- Open questions: (해소) 2026-09-29 사용자 확인 — 목록 부재는 note 1줄 후 통과, 커밋 author·committer 신원도 검사, PowerShell 로컬 설치·목록 초기값 채우기는 하지 않음(ps1 은 CI 경로로 검증, 목록은 사용자가 직접 관리).

# Progress
- 2026-09-29: 착수. 관련 decision 조회(git-hook-network-safety·ci-secret-scan-backstop). ultracode 설계 workflow(조사 3·설계안 3·심사 2, `wf_70d53aa2-b35`) — 두 심사가 robust 안 기반으로 수렴. plan 초안.
- 2026-09-29: architecture-reviewer(planning) REQUEST CHANGES(Major 1·Minor 7), plan-reviewer(+Codex) CONDITIONAL(강한 우려 4) — 아래 # Review Disposition 대로 plan 재작성.
- 2026-09-29: 사용자 승인. TDD — 새 케이스 Red(20건 실패, 기존 71 통과) → sh 구현 → Green, ps1 쌍둥이 작성(로컬 pwsh 없음 — 미실행). 변이 검사 3건(최상위 목록 staging·origin/main 제외·단어 경계)이 각각 해당 케이스로 잡힘. `verify.sh` ALL PASS(skip: install-codex-skill.test.ps1 — pwsh 미설치). 단위 1 커밋. 구현 리뷰 workflow(`wf_c2c52ba4-1d5`) 진행. 단위 2 문서(`improve.sh --ci` error 0) 커밋. E2E(임시 HOME·install-hooks·bare 원격·합성 목록) 10/10 — commit·push·메시지·ref·목록 파일·linked worktree 차단, origin/main 이력 위 새 브랜치 push·다른 repo 통과, 출력에 용어 없음.
- 2026-09-29: 구현 리뷰 21 agent 완료(Codex 크레딧 소진으로 미가용) — major 2·minor 4·nit 4 확정, 3건 반박. # Review Disposition 대로 수정: 테스트 먼저(sh Red 3 — gitfile·경로 숨김·목록 오류 안내; 실제 훅 케이스는 ps1 에서만 실패하는 결함이라 CI 에서 Red→Green), sh·ps1 수정 → sh 118/118, 이스케이프 제거 변이를 잡음, 1MB 병적 줄 9.4s→0.13s, `verify.sh` ALL PASS(skip: install-codex-skill.test.ps1). simplify 점검 — 변경 없음. README 기술 절 갱신. 수정분 targeted 재리뷰 APPROVE(Minor 5·Nit 3) — 전부 반영: 테스트 먼저(구버전 git shim 은 scratch 재현으로 fail-open 확인, 안내 2건 Red) → sh·ps1 수정 → 123/123, 이스케이프 변이 3종 잡힘, `verify.sh` ALL PASS(skip: install-codex-skill.test.ps1). fixup 2건 커밋. E2E 재실행(커밋된 상태) 13/13 — 다른 repo linked worktree commit·push 통과, `~/.claude` linked worktree `commit -a` 차단 추가. `improve.sh --ci` error 0.
- 2026-09-29 evidence gate: Acceptance 1~7·9·10 충족(sh 엔진·로컬 증거). 8(ps1)은 로컬 미검증 — 실제 훅 케이스를 포함한 CI(ubuntu pwsh 7) 실행이 남아 있다. 판정 NEEDS-HUMAN — 다음 단계가 push·PR(외부 공개)이라 사용자 승인이 필요하다.

# Next
사용자 승인 후 `/e merge` — commit-check 로 fixup 2건 정리 → push → PR → CI 에서 ps1(test.sh ps1 엔진 + 실제 훅 케이스) 통과 확인 → 머지. CI 에서 ps1 이 실패하면 머지하지 않고 고친다. 머지 뒤 issue #206 에 진행 댓글(외부 쓰기 — 승인 후).

# Decisions
- 관련 decision: [[git-hook-network-safety]]·[[ci-secret-scan-backstop]] 을 따른다(네트워크 없음, CI 무동작·목록 미주입). `plans/2026-09-26-push-remote-scope` 의 "추적 ref 기준 제외 기각"과의 관계는 아래 "private push 범위".
- **목록**: `$HOME/.claude/private-terms.txt` 고정(ps1 `Join-Path $HOME '.claude\private-terms.txt'`). env 로 경로를 바꾸지 않는다(에이전트의 무흔적 우회 통로 방지 — 끄려면 목록을 비운다). `.gitignore` 는 `/*` 규칙으로 이미 무시되지만 belt 블록에 `/private-terms.txt` 를 명시한다. 형식: UTF-8, 앞 BOM·줄 끝 CR·앞뒤 공백 제거, 빈 줄·`#` 줄 무시, 한 줄 한 항목, 식별은 물리 줄 번호. 3바이트 미만·제어문자 항목은 설정 오류로 차단. 배포는 clone 이 아니라 settings.json 처럼 머신마다 직접 복사.
- **매칭**: 기본은 **ASCII 영숫자 경계** 고정 문자열 매치(앞뒤 문자가 `[A-Za-z0-9]` 가 아니어야 함 — `_`·`-`·공백·비ASCII 는 경계), ASCII 대소문자 무시. 경계 없이 부분일치가 필요한 항목은 줄 앞 `*` 로 표시(`*<항목>`). 이유: 경계 없는 부분일치는 커밋 해시(16진수)·일반 단어 속 짧은 약어에 걸린다(Codex 가 합성 입력으로 확인). 경계 매치로도 `<항목>_<접미>`·`<항목>-1234` 같은 흔한 누출 모양은 잡힌다. sh 는 `LC_ALL=C` awk(목록은 `FILENAME==ARGV[1]` 로 구분 — `NR==FNR` 은 0바이트 목록에서 stdin 을 목록으로 읽는다), ps1 은 같은 규칙을 문자열 비교로 구현(비ASCII 대소문자까지 접어 ps1 이 더 엄격 — 문서화). 기각: 정규식 목록(sh ERE 와 .NET regex 차이·ReDoS), 경계 없는 기본값(해시 오탐), 최소 길이 상향만(짧은 약어 자체가 식별자일 수 있음).
- **범위 판정**(모드 분기 전 1회, 새 변수 `claude_repo` — 기존 main push 면제의 `--show-toplevel` 판정과 의미가 다름을 주석으로 구분): 결과는 셋이다.
  - 대상: `git rev-parse --git-common-dir` 결과가 `$HOME/.claude/.git` 과 같은 디렉토리(sh `-ef`, ps1 은 두 경로 모두 git 이 정규화한 절대경로로 비교). linked worktree 포함.
  - 비대상: 위가 다르거나 `$HOME/.claude/.git` 이 없음(CI·다른 repo) — 목록을 열지 않고 출력 없이 통과.
  - 판정 불능(rev-parse 실패·ps1 경로 예외): `pwd -P` 가 `$HOME/.claude` 아래면 차단(fail-closed, `[BLOCKED] private-terms scope check failed`), 아니면 통과. sh 는 `set -e` 아래에서 `if common=$(…); then` 형태로 써서 [BLOCKED] 없는 exit 128 을 막는다. **이 단계가 되돌리기 가장 비싸다**(버그면 목록을 비워도 복구 안 되고 모든 repo 커밋이 막힘) — TDD 첫 순서, SHIM 오류 주입 테스트.
- **검사 순서**: 범위 판정 → 목록과 무관한 검사(`private-terms.txt` 경로를 stage·push 하면 차단) → 목록 로드·상태 분기 → 목록 기반 검사. 목록 상태: 없음 → 통과 + stderr note(사용자 확인됨), 디렉토리·깨진 링크·읽기 불가 → 차단, 형식 오류 → 차단, 유효 항목 0 → 조용히 통과.
- **관문**: 기준 관문은 **pre-push** 다. pre-commit 은 조기 경고일 뿐 merge·cherry-pick·rebase·`commit-check` plumbing 재조립은 pre-commit 을 거치지 않는다. pre-commit 은 `git -c core.quotePath=false -c diff.renames=true diff --cached -M -U0 --text --no-color --no-ext-diff --no-textconv --src-prefix=a/ --dst-prefix=b/`(ps1 은 `Invoke-Git` 으로 — UTF-8·종료 코드 확인) 전체 경로에서 hunk 의 `+` 줄과 새 경로(new file·rename to·copy to)를 본다. 기존 settings.json·plans 전체 스캔은 그대로.
- **private push 범위**: 기존 `rev_input`(push_commits + `^published`)은 그대로 두고, 별도 `private_rev_input` 이 그 출력에 `^refs/remotes/origin/main`(있을 때만)을 더한다. 이유: 가드 도입 전 이력의 식별자가 새 브랜치 push(rsha=0)마다 걸려 모든 PR push 가 막히는 것을 막기 위해 제외가 필요하고, 제외 대상은 "이미 공개된 것"이어야 한다. `plans/2026-09-26-push-remote-scope` 는 secret 스캔에서 추적 ref 기준 제외를 기각했다 — 비공개 원격에서 받은 커밋이 공개 원격으로 갈 때 재검사를 빠뜨리기 때문(G2). 여기서는 제외 기준을 **origin(공개) 기본 브랜치 한 개**로 좁혀 그 경로를 닫는다: origin/main 에 도달 가능한 커밋은 이미 공개됐고, main 은 force-push 금지(§8)라 추적 ref 가 오래돼도 비공개 내용을 담지 않는다. 기각: `refs/remotes/*`(비공개 mirror 추가 시 fail-open), `refs/remotes/origin/*`(비공개 내용이 든 채 삭제·force-push 된 브랜치 ref), 고정 baseline sha(GitHub merge 커밋 메시지의 PR 제목에 용어가 한 번 섞이면 이후 새 브랜치 push 가 영구히 막힘). 상태별 계약: 추적 ref 가 뒤처지거나 없음 → 범위가 넓어져 fail-closed 오탐 가능(복구 `git fetch origin`, 차단 안내에 명시) / 로컬 `update-ref` 로 조작된 ref → fail-open(한계로 문서화).
- **pre-push 검사 대상**: (a) private 범위의 추가 줄·새 경로(전체 경로, `-M`, `-c diff.renames=true`, 기존 하드닝 옵션 상속) (b) 커밋 메시지 + author·committer 신원(사용자 확인됨) (c) 삭제가 아닌 모든 줄의 rref — **`push_commits` 가 비어도**(tag 만·기존 커밋을 새 이름으로 push) 실행. git 실패는 fail-closed. 기존 secret 스캔 범위·옵션은 바꾸지 않는다(test.sh 의 추적 ref 무시 케이스가 회귀 가드).
- **merge 커밋**: 기존 하드닝의 `-m`(separate)을 그대로 상속한다. 가드 도입 전 main 을 feature 로 merge 하면 main 쪽 추가 줄이 다시 보고될 수 있다 — 가드 도입 뒤 main 에 들어오는 줄은 이미 검사를 통과하고 이 repo 는 ff/rebase 위주라 과도기 한정 한계로 문서화. 기각: `--diff-merges=dense-combined`(결합 diff 파서가 sh·ps1 양쪽에 필요, 이득 작음).
- **출력**: `private term (list line N) in <surface>` 만 — surface 는 `staged <path>`·`pushed <path>`·`commit <sha7> message|identity`·`push ref (hidden)`, 경로 자체에 항목이 있으면 `path (hidden)`. 항목·걸린 줄은 출력하지 않는다. 차단 안내(청록): 목록 위치 / "목록을 도구로 읽지 말고 걸린 표현을 일반 표현(예: '회사 repo')으로 바꿀 것 — 커밋 메시지에 항목을 인용하지 말 것" / 메시지에 걸리면 reword 절차(`git commit --amend` 또는 미게시면 `commit-check`) / 추적 ref 가 뒤처졌으면 `git fetch origin`. `--no-verify` 는 secret 스캔까지 끄므로 복구책으로 안내하지 않는다.
- **ps1**: sh 와 1:1 대응 함수, 위반 문자열 글자 단위 동일(테스트는 전체 줄 단언), PowerShell 5.1 호환(`??`·삼항 금지).
- **rollback**: revert PR 이 같은 경로(merge → ci/verified → 자동 pull)로 퍼진다. 목록 형식 오류로 막히면 목록을 고치거나 비워 복구(코드 되돌림 불필요). 범위 판정 버그는 목록으로 복구되지 않아 revert 뿐 — 그래서 판정을 fail-safe 계약 + 테스트로 먼저 고정한다.
- 구현 중 변경(2026-09-29):
  - sh 목록 전달을 "`FILENAME==ARGV[1]` 로 목록·입력을 한 awk 에"에서 **목록 파싱 awk 1회 → 정규화된 행을 셸 변수 → 매처 awk 에 `ENVIRON` 으로**로 변경 (이유: 목록 상태·형식 오류를 매칭 전에 판정해야 하고, 0바이트 목록의 `NR==FNR` 문제가 구조적으로 사라진다).
  - 신원 format 을 `%an%x20<%ae>` 로 (이유: ps1 `Invoke-Git` 은 인자를 따옴표 없이 공백으로 잇는다 — 공백 든 인자 불가).
  - 새 위반 문자열은 ASCII 만 (이유: `—` 등 비ASCII 는 Windows 콘솔 코드페이지에 따라 깨질 수 있고, 테스트가 전체 줄을 비교한다). 안내 문구(청록)의 "회사 repo" 예시는 그대로.
  - 테스트 reason 에 `=` 접두 = ANSI 를 벗긴 출력에서 `  - <메시지>` 한 줄 전체 일치(ps1 문자열 동일성 단언).
  - ps1 은 PowerShell 의 대소문자 무시 기본값을 피하려고 레코드 종류를 대소문자로 구분하지 않는 이름(staged/pushed/stagedPath…)으로, 경로 캐시는 Ordinal `Dictionary` 로 둔다.
  - 범위 판정을 "`--git-common-dir` 을 `$HOME/.claude/.git` 경로와 비교(sh `-ef`)·ps1 은 `-Cwd` 로 한 번 더 물어 비교"에서 **두 엔진 모두 git 변수(`GIT_DIR`·`GIT_COMMON_DIR`·`GIT_WORK_TREE`·`GIT_INDEX_FILE`)를 지운 채 `~/.claude` 의 common dir 을 git 에 묻고 비교**로 변경 (이유: 구현 리뷰 — linked worktree 훅이 받는 `GIT_DIR` 때문에 ps1 이 다른 repo 를 대상으로 오판, sh 는 gitfile `.git` 을 놓침). ps1 은 `--git-dir=` 인자 대신 env 를 잠시 지운다(Invoke-Git 이 인자를 따옴표 없이 이어 붙여 공백 든 HOME 이 깨진다).
  - sh 경계 판정을 "occurrence 마다 substr 로 재탐색"에서 **index 사전 필터 + 이스케이프한 ERE 한 번(앞뒤 공백 패딩으로 앵커 대신)**으로 변경 (이유: 긴 한 줄에서 2차 시간 — 훅은 timeout 이 없다. 앵커 `^`·`$` 를 괄호 안에 쓰지 않아 BSD awk·mawk·gawk 차이를 피한다). 기각: 청크 분할 탐색(복잡도 대비 이득 없음). "매칭" 의 기각안 "정규식 목록" 과 다르다 — 목록 항목은 여전히 고정 문자열이고 ERE 는 이스케이프한 내부 검색 수단일 뿐이다. 기각 사유였던 awk 방언 의존은 이스케이프 집합 테스트(변이 3종이 잡힘)와 CI(mawk) 실행으로 막는다.
  - 목록 파일명 위반·목록/범위 오류·용어 일치를 따로 세어 안내를 각각 낸다 (이유: 재리뷰 M2·M3 — 한 안내로 묶으면 목록 파일명 위반에 "목록 줄을 고쳐라"가 붙고, 에이전트가 목록을 열거나 비우도록 유도한다).
  - FAILSHIM 케이스는 sh + Windows 가 아닌 ps1 에서 돈다 (이유: Windows 의 ps1 은 git 을 `.exe` 로만 골라 PATH shim 을 집지 않는다). Acceptance 1 의 `both` 는 이 범위로 읽는다.
  - 실제 훅 테스트의 ps1 엔진은 pwsh 만(ps51 제외 — Windows 전용 훅 shim·콘솔 인코딩 설정이 따로 필요).
- 커밋 단위: 1) `feat(pre-commit-check): block private terms from being committed to ~/.claude` — sh·ps1·test.sh(pwsh 가 있는 CI 에서 스스로 green 이려면 쌍둥이를 한 커밋에) 2) `docs: widen the public check to every commit and document the private-terms list` — CLAUDE.md·README·bootstrap README·.gitignore.

# Acceptance
1. 범위 판정(TDD 첫 순서): `~/.claude` main checkout(`--git-common-dir` 이 상대경로 `.git`)·linked worktree(절대경로) 둘 다 대상, 다른 repo 는 목록이 있어도 clean(출력 없음), SHIM 으로 rev-parse 실패를 주입하면 `$HOME/.claude` 아래는 `[BLOCKED] … scope check failed`·밖은 통과, `$HOME/.claude/.git` 없음은 통과 — test.sh `both`.
2. 목록 상태: 없음 → 통과(+note 는 확인 결과대로), 0바이트 → clean, 주석만 → clean, 디렉토리 → 차단, 2바이트 항목 → 차단, BOM·CRLF·주석·빈 줄이 섞여도 보고되는 줄 번호가 물리 줄과 같다, 목록이 없어도 `private-terms.txt` stage 는 차단 — test.sh.
3. 매칭: 대소문자 섞인 항목 추가 → 차단(`list line N`), 커밋 해시·긴 단어 속 짧은 항목은 경계 매치라 clean, `<항목>_x`·`<항목>-1234` 는 차단, `*` 항목은 부분일치로 차단, 잘못된 UTF-8 바이트 줄 + 한글 항목 → 차단 — test.sh.
4. pre-commit: 항목이 이미 있는 파일의 다른 줄만 수정 → clean, 항목이 든 새 경로 → 차단(경로 숨김), 항목 없는 경로로 rename → clean, 항목 든 경로로 rename → 차단, rename + 항목 줄 추가 → 차단 — test.sh.
5. pre-push: 항목을 추가한 커밋 → 차단, 메시지(+확인 시 신원) → 차단, rref → 차단(삭제는 clean), 커밋 범위가 빈 push(기존 커밋을 항목 든 이름으로) → 차단, **`refs/remotes/origin/main` 에 이미 있는 이력 위의 새 브랜치 push(rsha=0) → clean(핵심 회귀)**, 항목이 origin 이 아닌 remote 추적 ref 에만 있는 이력 위의 새 브랜치 push → 차단, published 범위 → clean — test.sh.
6. 원문 미출력: 모든 private 차단 케이스 출력에 항목 원문이 없다(부정 단언, `FORBID`) — test.sh.
7. 회귀: 기존 71 케이스 전부 통과(추적 ref 를 무시하는 secret 스캔 케이스 포함) + `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 이 있으면 원인과 함께 판정).
8. ps1: 같은 test.sh 가 ps1 엔진으로 통과 — pwsh 가 있으면 로컬 실행 관찰, 없으면 "로컬 미검증" 으로 보고하고 CI(ubuntu pwsh 7) 결과로 확인. Windows PowerShell 5.1(실제 훅 엔진)은 CI 에서 돌지 않아 Windows 수동 실행 전까지 미검증.
9. E2E(merge 전 관찰 가능한 형태): 임시 HOME 의 `.claude` 를 이 worktree 를 가리키는 clone/링크로 만들고 `scripts/install-hooks.sh` 로 훅 설치 → bare 원격 + 합성 목록으로 실제 `git commit`·`git push` 가 차단되고, 같은 HOME 의 다른 repo 에서는 차단되지 않음을 관찰(선례 `plans/2026-09-26-push-remote-scope`).
10. 문서: CLAUDE.md §11(대상 확장 + 기계 백스톱과 한계 1문장)·§8(가드 서술), README(가드 절·"추적 ref 는 보지 않는다" 서술과 private 범위의 구분·NOT-in-repo 표·수동 grep 절·설치 절차), `scripts/bootstrap/README.md` 행, `.gitignore` belt — diff 관찰, `improve.sh --ci` error 0.

# Review Disposition
- [arch Major] `refs/remotes/*` 제외는 fail-open — fix: origin 기본 브랜치 하나로 좁힘(plan-reviewer 강1 과 합쳐 처리).
- [plan 강1] 2026-09-26 기각 방식 재도입 — fix: 제외 기준을 `refs/remotes/origin/main` 으로, 기각 결정과의 차이·대안 기각 사유를 Decisions 에.
- [plan 강2] 범위 판정 실패 처리 부재 — fix: 대상/비대상/판정 불능 계약, `set -e` 안전 형태, SHIM 주입 테스트, TDD 첫 순서.
- [plan 강3] 짧은 항목 오탐 — fix: 기본 ASCII 영숫자 경계 매치 + `*` 부분일치 opt-in, 해시·단어 정상 통과 테스트.
- [plan 강4] Acceptance 9 관찰 불가 — fix: 임시 HOME + install-hooks + bare 원격 E2E.
- [arch Minor] `rev_input` 플래그 혼합 — fix: `private_rev_input` 분리, 기존 케이스를 회귀 가드로 명시.
- [arch Minor] 하드닝 옵션 4벌 — defer: 기존 함수 불변을 우선, 교차 주석으로 대체(Deferred).
- [arch Minor] 두 `~/.claude` 판정 공존 — fix: `claude_repo` 명명·주석, `--show-toplevel` 결함은 Deferred.
- [arch Minor] sh `-ef` vs ps1 문자열 비교 — fix: ps1 도 git 정규화 경로로 비교, main checkout·worktree 둘 다 테스트.
- [arch Minor] test 도우미 — fix: `newclaude`·`FORBID`·전체 줄 단언·0바이트 목록.
- [arch Minor] merge `-m` 재보고 — accepted-risk: 과도기 한정(Decisions "merge 커밋").
- [arch Minor] ps1 쌍둥이 유지비 — defer(Deferred).
- [arch Minor] 목록 무관 검사를 상태 분기 밖에 — fix: 검사 순서 명시·목록 없음 상태 테스트.
- [plan 약] tag 본문 제외 근거 오류 — fix: 사유 정정. 커밋 1·2 분리 — fix: 한 커밋. 기존 메시지 경로 출력 — fix: Constraint 를 "새 검사 출력"으로 한정하고 한계로 문서화. 안내가 목록 원문으로 이끎 — fix: 안내 문구. ff-merge 경로의 늦은 메시지 검사 — fix: reword 절차 안내(commit-msg 기각 유지). pre-commit 보조 — fix: 관문 명시. rename 모호 — fix: Acceptance 분리. fixture 공개 안전 — fix: Constraint. 목록 부재 fail-open — 사용자 확인 근거로 전달. 빈 push_commits 에서 rref 검사 누락 — fix: Acceptance 5. rollback 절 — fix.
- [plan/Codex 충돌] merge `-m` 심각도(Codex 강함 vs reviewer 약함) — 약함으로 판단: 가드 도입 뒤 main 에 들어오는 줄은 이미 검사를 통과한다.
- 구현 리뷰(`wf_c2c52ba4-1d5` — code-reviewer·architecture-reviewer·ps1 동등성 finder + finding 마다 반박 verifier, Codex 는 크레딧 소진으로 미가용):
  - [impl major, 3개 reviewer 독립 발견] ps1 범위 판정이 훅 환경의 `GIT_DIR` 을 물려받아 다른 repo 의 linked worktree 를 `~/.claude` 로 오판 — fix: 두 엔진 모두 git 변수를 지운 채 `~/.claude` 의 common dir 을 git 에 묻는다.
  - [impl major] 테스트가 실제 훅 환경을 재현하지 않음 — fix: `core.hooksPath` 로 실제 `git commit`·`git push` 가 훅을 부르는 케이스(sh·ps1: 다른 repo linked worktree commit·push clean, `~/.claude` linked worktree 차단).
  - [impl minor] ps1 판정 불능 경로 미검사 — fix: FAILSHIM 을 Windows 가 아닌 ps1 에도.
  - [impl minor] sh 가 gitfile `.git` 을 대상에서 빠뜨림 — fix: 위 git 질의로 해소 + 테스트.
  - [impl minor] 긴 한 줄에서 경계 재탐색이 2차 시간(1MB 9.4s) — fix: 이스케이프한 ERE 한 번(0.13s), 이스케이프 제거 변이를 잡는 테스트.
  - [impl nit] 경로 숨김이 경계 기준이라 긴 단어 속 항목이 경로로 출력 — fix: 부분일치로 숨김.
  - [impl nit] 목록·범위 오류에도 "표현을 바꾸라" 안내 — fix: 용어 일치와 오류를 따로 세고 오류에는 목록 줄 안내.
  - [impl nit] ps1 `ToLowerInvariant` 가 Kelvin 기호 등을 ASCII 로 바꿔 경계를 잃음 — fix: 경계는 소문자화 전 글자로.
  - [impl nit] 목록의 잘못된 UTF-8·NUL 에서 sh·ps1 판정이 갈림 — defer: 목록 형식은 UTF-8 로 문서화, README 한계에 명시(Deferred).
  - [impl minor] ps1 대체 판정이 논리 경로를 비교(sh 는 `pwd -P`) — defer: git 이 `~/.claude` 에서 답하지 못하고 경로에 링크가 낀 경우만이고 .NET Framework 에 실제 경로 API 가 없다. README 한계에 명시(Deferred).
  - 수정분 targeted 재리뷰(code-reviewer, APPROVE — blocking 없음; awk 교차 확인 BWK·mawk 2종·busybox, gawk 미확인):
    - [re M1 minor] sh 가 git<2.31 에서 `--path-format` 을 되찍으면 fail-open — fix: `[ -d ]` 로 판정 불능 처리 + 구버전 git shim 테스트(sh·비Windows ps1).
    - [re M2 minor] 목록 파일명 위반에 목록 오류 안내가 붙음 — fix: 따로 세고 `git rm --cached` 안내.
    - [re M3 minor] 오류 안내가 목록 편집·비우기를 유도 — fix: "손으로 고칠 것, 도구로 열거나 다시 쓰지 말 것" 으로(비우기 안내는 README 에만).
    - [re M4 minor] `quote()` 이스케이프 집합 테스트 공백(`{` 제거 변이 생존) — fix: `{ ( ) * ? \ ^ $` 가 든 항목 + 정규식으로만 맞는 decoy, 변이 3종이 잡힘.
    - [re M5 minor] ps1 env 복원 미검사 — fix: 실제 훅 `commit -a`(훅이 `GIT_INDEX_FILE=<index.lock>` 을 받음) 차단 케이스.
    - [re M6] plan 과 diff 불일치 — fix: Decisions·Review Disposition·Progress 갱신(아래 "매칭" 보강 포함), plan 은 마지막 커밋에 포함.
    - [re N1·N2·N3 nit] env 제거 루프를 try 안으로, 카운터 이름 `pt_term_hits`/`$ptTermHits`, 대체된 구현을 설명하던 주석 정리 — fix.
  - [impl] plan 미반영 지적 — false-positive(리뷰 시점 뒤 plan 이 이미 갱신됨; 남은 괄호 문구는 정리). `cd` 실패 시 패턴 `/*` — false-positive(`.git` 존재 검사와 같은 권한이 필요해 도달 불가). git<2.31 — false-positive(install-hooks 가 설치를 거부).

# Deferred
- 기존 main push 면제가 `--show-toplevel` 을 써서 `~/.claude` linked worktree 에서는 면제가 안 걸린다(현재 동작: worktree 에서 main 직접 push 는 가드가 막음) — low — scripts/pre-commit-check.sh·.ps1.
- git log/diff 하드닝 옵션을 sh·ps1 각 배열 하나로 공유 — low — 같은 파일.
- ps1 쌍둥이를 둔 원래 이유 확인 후 sh 단일화 검토(Windows 훅 shim 은 이미 Git for Windows sh 에서 돈다) — low.
- 다른 공개 repo 에도 적용하는 opt-in(git config 등) — 두 번째 공개 repo 가 생기면.
- 목록 파일 `Read` deny 권한 규칙(settings.json 추적 밖이라 머신별) — low.
- test.sh 의 `ps1: skipped` 를 verify 요약에 드러나는 형태로 — low.
- README `#### pre-commit-check.ps1` 절의 "ps1 은 아직 인자로 넘긴다(Windows 확인 뒤 같게 할 예정)" 는 옛 서술 — 지금 ps1 `Get-AddedLines` 도 `-Stdin` 으로 넘긴다 — low — README.md.
- 목록에 잘못된 UTF-8·NUL 이 든 항목의 sh·ps1 판정 차이(sh 는 바이트 수, ps1 은 U+FFFD 치환 뒤 수) — low — pre-commit-check.ps1 목록 디코드.
- ps1 범위 대체 판정(git 이 답하지 못할 때)이 심볼릭 링크·junction 을 풀지 않은 경로로 비교 — low(git 실패 + 링크 낀 경로에서만 fail-open) — pre-commit-check.ps1.
- Windows PowerShell 5.1(실제 Windows 훅 엔진)로 test.sh 를 도는 것 — Windows 머신에서 수동 1회 — scripts/pre-commit-check.test.sh(ps51 엔진).

# Key Files
- scripts/pre-commit-check.sh · scripts/pre-commit-check.ps1 — 가드
- scripts/pre-commit-check.test.sh — 테스트(sh·ps1 엔진 공용)
- CLAUDE.md §8·§11 — 규칙
- README.md · scripts/bootstrap/README.md · .gitignore — 문서·설치 절차
- ~/.claude/private-terms.txt — 로컬 목록(추적 안 함)

# Blockers
