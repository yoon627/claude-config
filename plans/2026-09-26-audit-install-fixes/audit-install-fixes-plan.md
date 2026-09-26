---
title: audit-install-fixes — heal 의 symlink chmod 차단, bootstrap(macOS)이 Codex skill 7종·AGENTS.md 를 연결
status: in_progress
started: 2026-09-26
updated: 2026-09-26
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

1. `skills/wt/heal_submodules.py` 의 `_force_rmtree` 가 트리 안 symlink 를 따라가 트리 밖 파일의 모드를 바꾸지 않게 한다.
2. macOS bootstrap(`scripts/bootstrap/setup.sh`)이 README 가 적은 Codex 연결 — `~/.agents/skills/{c,dlc,e,improve,jira-worklog,wiki,wt}` 와 `~/.codex/AGENTS.md` → `~/.claude/CLAUDE.md` — 을 모두 재현하게 한다.

# Intent

- 묶음: `plans/2026-09-25-repo-audit-followups/intent.md` — `audit-low-batch` 를 독립 머지 가능한 단위로 나눴고 이 plan 이 첫 단위다(사용자 선택 2026-09-26).
- Problem:
  - `_force_rmtree` 는 `path.rglob("*")` 로 돌며 `child.is_file()`(symlink 를 따라감)이면 `os.chmod(child, stat.S_IWRITE)`(symlink 를 따라감)를 한다. 트리 안에 밖을 가리키는 파일 symlink 나 **hardlink**(로컬 경로 clone 은 objects 를 hardlink 로 공유할 수 있다 ⚠️)가 있으면 밖의 파일 모드가 `0o200`(쓰기 전용)으로 바뀌어 읽을 수 없게 된다(plan-reviewer 실측 — 파일 symlink·hardlink 모두 `0o200`, 디렉토리 symlink 는 rglob 이 들어가지 않아 변화 없음). 삭제 자체(`shutil.rmtree`)는 symlink 를 따라가지 않는다. chmod 는 Windows 의 read-only pack 파일 때문에 있는 것이고, POSIX 에서는 unlink 가 파일 모드와 무관해 필요 없다(실측: chmod 없이 `0o444` 트리 삭제).
  - `setup.sh` 3b 단계는 `jira-worklog` 하나만 연결한다. 2026-09-25 Codex 쪽 재정렬로 실제 연결은 skill 7종 + `~/.codex/AGENTS.md` 심링크이고 README(`README.md:396`)도 그렇게 적는다. 새 머신에서 bootstrap 을 돌리면 나머지 6종과 AGENTS.md 가 없다. 설치 도구 `install-codex-skill.sh` 의 메시지도 "jira-worklog" 로 고정돼 있다.
- 델타(이 plan 에만 더해지는 제약):
  - Windows(`setup.ps1`·`install-codex-skill.ps1`)는 고치지 않는다 — 이 Mac 에 pwsh 가 없어 실행 검증이 불가능하다(사용자 결정 2026-09-26, 공용 wiki `lesson-no-speculative-platform-switch`). Windows 에서 검증할 단위로 넘기고 README 에 macOS 와의 차이를 적는다.
  - 연결 충돌(실디렉토리·실파일·다른 곳을 가리키는 링크)은 지금처럼 건드리지 않고 실패로 알린다(fail-closed). 달라지는 것은 실패 시점 — 아래 Decisions.
  - `setup.sh` 는 macOS 기본 `/bin/bash` 3.2 에서 `set -uo pipefail` 로 돈다 — 빈 배열 확장(`"${a[@]}"`)은 3.2 에서 unbound 오류라 쓰지 않는다(plan-reviewer 실측).
- Out of scope: `setup.ps1`/`install-codex-skill.ps1`(Windows 단위), `~/.codex/agents/*.toml`·Codex `hooks.json`(codex-agents-hooks 단위), heal 의 다른 후속(`gitdir:` prefix 검증 등 — 원 plan `# Deferred` 저우선에 남김), 연결 대상 skill 목록 자체를 바꾸는 것(2026-09-25 결정 그대로).
- 분할: 묶음 → `plans/2026-09-25-repo-audit-followups/intent.md`(이 plan 안의 두 목적은 커밋 단위로 나눈다 — 각각 따로 머지해도 유효하지만 둘 다 작고 같은 감사 묶음이라 plan 하나로 둔다).

# Acceptance

1. heal: 트리 안에 밖을 가리키는 파일 symlink·hardlink 가 있어도 `_force_rmtree` 뒤 트리는 지워지고 밖의 파일은 남으며 모드가 바뀌지 않는다 — `test_heal_submodules.py` 새 테스트가 변경 전 코드에서 Red(`0o200`), 변경 후 Green. 디렉토리 symlink 는 원래 Green 인 회귀 방지 테스트. read-only 해제 경로(Windows 에서만 켜지는 게이트)는 게이트를 테스트에서 켜서 POSIX 에서도 관찰한다: 일반 파일이면 chmod 후 재시도, symlink 면 chmod 없이 원래 오류, 게이트가 꺼져 있으면 chmod 없이 원래 오류. 기존 read-only 트리 삭제 테스트 통과.
2. 설치 도구: `install-codex-skill.sh --file` 이 파일 source(AGENTS.md)를 링크한다 — 생성, 같은 source 재실행은 "already"(절대·상대 링크 모두), `--dry-run` 은 변경 없음, 실파일·다른 링크·끊긴 링크 충돌은 거부하고 그대로 둠, 없는 source·디렉토리 source 거부. setup 검증이 기대는 출력 문구("already points"·"[dry-run] create symlink")를 테스트가 단언한다. 스크립트 메시지에 `jira-worklog` 가 남지 않는다. 검증: `install-codex-skill.test.sh` 확장 통과 + `grep -c jira-worklog scripts/bootstrap/install-codex-skill.sh` = 0.
3. setup.sh: scratchpad 스크립트가 비어 있지 않은 mktemp HOME(가짜 `~/.claude/skills/<7종>/SKILL.md`·`~/.claude/CLAUDE.md`, `$HOME/.local/bin/rtk` 는 `exit 0` stub)을 만들고 `/bin/bash`(3.2)로 실제 실행해 관찰한다: (a) `--dry-run`·링크 없음 → 8개 모두 `[dry-run] create symlink`, 링크 0개 생성 (b) **non-dry-run** → 8개 링크가 생기고 각 대상이 source 를 가리킴 (c) 재실행 → 8개 모두 "already" (d) 한 skill 자리에 실디렉토리, `AGENTS.md` 자리에 실파일 → 나머지 6개는 처리, 뒤 단계(zshrc)는 실행, 마지막에 충돌 요약과 exit 1, 충돌한 실디렉토리·실파일 내용은 그대로 (e) `CODEX_HOME` 을 주면 그 아래 `AGENTS.md` 가 생김. 실행 전후 실제 `~/.agents/skills` 목록·`readlink ~/.codex/AGENTS.md`·`~/.zshrc` mtime·`~/.local/bin` 목록이 같다. 목록의 7개 이름마다 repo `skills/<name>/SKILL.md` 가 있다.
4. 문서: `scripts/bootstrap/README.md`(`$jira-worklog` 만 말하는 연결 설명 절·재현 대상 표·되돌리기 절·idempotent 절의 "source 에 SKILL.md" 서술)에 8개 연결·`--file`·충돌 해소 절차(실파일·실디렉토리를 백업 → 제거 → 재실행)·Windows 차이를 적고, 루트 README 의 bootstrap 요약(`README.md:394`)과 Codex 연결 절(`:396` — "jira-worklog 하나만"·`(intent audit-low-batch)`)을 새 동작에 맞춘다. 실패 메시지가 bootstrap README 의 충돌 해소 절을 가리킨다.
5. intent: `audit-low-batch (미착수)` 줄을 이 plan 경로와 나머지 단위 `(미착수)` 줄로 바꾸고, main 에서 처리한 환경 항목(pyright-lsp 끄기, memory 끊긴 링크)을 적는다.
6. 검증: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음), `bash skills/improve/improve.sh --ci` error 0, `node scripts/plan-lint.js <이 plan>` 통과.

# Progress

- 2026-09-26: 착수. audit-low-batch 14항목 현재 상태 재확인 → 사용자와 분할·첫 단위 결정(이 plan), pyright-lsp 끄기·memory 끊긴 링크는 main 에서 처리. pwsh 없음 확인 → ps1 은 Windows 단위로(사용자 결정).
- 2026-09-26: plan-reviewer(Codex 크레딧 소진으로 생략) CONDITIONAL — 강 A1~A4·B1~B2 반영(heal 은 사전 chmod 제거·실패 핸들러 방식, setup 은 단일 호출·끝에서 exit 1·non-dry-run 검증, 분할 줄 보강). `CODEX_HOME` 은 공식 문서로 확인.
- 2026-09-26: TDD — heal 새 테스트 Red(밖의 `linked.pack` 이 `0o200`, 핸들러 부재) → rmtree 실패 핸들러 구현 → Green(3.13·3.9), 단위 커밋 1. installer `--file` 테스트 Red(메시지에 jira-worklog 고정) → 구현 → Green, setup.sh 3b 루프·끝 요약, throwaway HOME 하니스(/bin/bash 3.2) (a)~(e)·실제 HOME 불변 전부 통과, 단위 커밋 2. code-reviewer(Codex 생략) APPROVE — Minor 반영: 부모 symlink 를 거친 `..` 상대 링크 오판(기존 결함, Red 재현 → `cd -P` → Green), `--file` 충돌 행렬 보강, `CODEX_SKILLS` 존재 검사, rmtree 배선 테스트(onexc·onerror, mutation 둘 다 잡힘), README macOS 한정·백업 위치·source missing 안내·override 문구, 요약 메시지. fixup 2개.
- 2026-09-26: 최종 검증(격리 runner) — verify.sh `ALL PASS`(skip 없음)·improve error=0·plan-lint·heal 3.9 32 OK·setup 하니스 전부 PASS·배선 mutation 2종 모두 잡힘. evidence gate(시스템 grep, 양성 샘플 포함)로 Acceptance 1~6 충족 → DONE.

# Next

로컬 main(교훈 커밋) push → `/e merge`(사용자 결정 2026-09-27) → 머지 뒤 공용 wiki 적립(POSIX unlink·chmod·hardlink, `cd` vs `cd -P` — 별도 `/wt`).

# Decisions

- 분할(사용자 선택 2026-09-26): `audit-low-batch` → `audit-install-fixes`(이 plan) · `audit-docs-drift` · `ledger-bash-edits` · `codex-agents-hooks` · `native-overlap-recheck` · `windows-ps1-verify`. 기각: 한 plan 으로 전부(diff 가 크고 결정 필요 항목이 섞여 리뷰·머지가 늦어진다).
- heal 수정 방식: ~~`os.walk` 로 돌며 symlink 만 chmod 건너뛰기~~ → **사전 chmod 패스를 없애고 `shutil.rmtree` 의 실패 핸들러(3.12+ `onexc`, 그 전 `onerror`)에서만, Windows 에서만(모듈 상수 게이트), symlink 가 아닐 때만 read-only 를 풀고 재시도**로 변경 (이유: plan-reviewer 실측 — hardlink 는 symlink 검사로 걸러지지 않아 밖의 inode 가 `0o200` 이 된다. POSIX 는 unlink 가 파일 모드와 무관하니 chmod 할 이유가 없고, 실패 시에도 원인은 부모 디렉토리 권한이라 파일 chmod 는 공유 inode 만 망가뜨린다). Windows 의 read-only 속성 해제는 지금과 같은 동작이다(hardlink 가 공유하는 read-only 속성도 지금처럼 풀린다 — Windows 에서 검증 불가, windows-ps1-verify 로). 기각: Windows 게이트를 건 사전 chmod 패스(rmtree 가 실패하지 않을 파일까지 건드린다), `os.walk`+symlink 건너뛰기(hardlink 미해결), `os.chmod(..., follow_symlinks=False)`(Linux 는 `lchmod` 가 없어 `NotImplementedError`), `Path.rglob(recurse_symlinks=False)`(3.13 전용, 파일 symlink 는 그대로).
- 가장 위험한 단계: heal 변경 — `/wt` 가 자동으로 부르는 파괴적 경로이고 존재 이유인 Windows 동작을 여기서 실행할 수 없다. 그래서 게이트를 테스트에서 켜 핸들러 분기를 POSIX 에서 관찰한다. 되돌리기는 커밋 1 revert.
- setup.sh 실패 시점: **3b 에서 8개를 모두 시도하고, 실패를 모아 뒤 단계(rtk·zshrc·memory·git 안내)를 마저 한 뒤 마지막에 충돌 요약과 exit 1**. 기각: 첫 실패에서 즉시 exit(현행 — 링크가 8개로 늘면 Codex import 가 사본을 만든 머신에서 bootstrap 이 3b 에서 멈춰 Claude 쪽 설정까지 반쯤 남는다), 3b 끝에서 exit(같은 문제), 경고만 하고 exit 0(충돌을 놓친다). Codex 연결은 뒤 단계의 전제가 아니다.
- setup.sh 호출 경로는 하나로: `--dry-run` 은 `${dry_flag:+"$dry_flag"}` 로 붙인다(bash 3.2 의 `set -u` 빈 배열 오류 회피). 기존 if/else 두 벌은 non-dry-run 쪽이 검증되지 않았다.
- AGENTS.md 위치는 `${CODEX_HOME:-$HOME/.codex}/AGENTS.md` — Codex 는 `CODEX_HOME`(기본 `~/.codex`)의 `AGENTS.md` 를 읽는다(공식 문서 https://developers.openai.com/codex/guides/agents-md). 부모 디렉토리가 없으면 설치 도구가 만든다 — Codex 를 안 쓰는 머신에도 빈 `~/.codex` 와 링크가 생기지만 `~/.agents/skills` 도 이미 그렇게 만들고 있어 같은 동작으로 둔다. `AGENTS.override.md` 가 있으면 Codex 가 그것을 먼저 읽는다는 점은 README 에 적는다.
- AGENTS.md 연결: `install-codex-skill.sh` 에 `--file` 을 더해 같은 충돌 규칙(실파일·다른 링크는 그대로 두고 실패)을 재사용한다. 기각: setup.sh 에 링크 판정을 따로 쓰기(충돌 판정 로직이 두 벌이 된다), 새 스크립트(이름만 다르고 로직이 같다).
- skill 목록은 setup.sh 한 곳에 두고 README 가 같은 목록을 적는다(2026-09-25 결정 목록 그대로).
- 커밋 단위: 1) `fix(wt): keep heal from chmod-ing through symlinks` — `skills/wt/heal_submodules.py`·`skills/wt/test_heal_submodules.py` 2) `feat(bootstrap): link all Codex skills and AGENTS.md on macOS` — `scripts/bootstrap/{setup.sh,install-codex-skill.sh,install-codex-skill.test.sh,README.md}`·`README.md`. plan·intent 는 마지막 커밋에.

# Key Files

- `skills/wt/heal_submodules.py` — `_force_rmtree`
- `skills/wt/test_heal_submodules.py` — `ForceRmtreeTest`
- `scripts/bootstrap/setup.sh` — 3b 단계
- `scripts/bootstrap/install-codex-skill.sh`·`install-codex-skill.test.sh`
- `scripts/bootstrap/README.md`, `README.md`(bootstrap 요약·Codex 연결 절)
- `plans/2026-09-25-repo-audit-followups/intent.md` — `# Plans`

# Blockers

# Review Disposition

- [plan] 강 A1 heal 이 hardlink 로 밖의 inode 모드를 바꿈 — fix(사전 chmod 제거, rmtree 실패 핸들러에서 Windows·비-symlink 만 read-only 해제 후 재시도, Acceptance 1 에 hardlink Red).
- [plan] 강 A2 read-only 테스트가 POSIX 에서 아무것도 검증하지 않음 — fix(게이트를 테스트에서 켜 핸들러 분기 단언).
- [plan] 강 A3 dry-run 만 검증·bash 3.2 빈 배열 — fix(호출 경로 하나 `${dry_flag:+…}`, Intent 제약에 bash 3.2, Acceptance 3 에 stub rtk 로 non-dry-run).
- [plan] 강 A4 실패 뒤 종료 시점 미정 — fix(뒤 단계를 마치고 마지막에 요약·exit 1, 기각안 Decisions).
- [plan] 약: 디렉토리 symlink 는 원래 Green — fix(문구). junction 은 알려진 한계 — defer(windows-ps1-verify). AGENTS.md 실파일 충돌·충돌 해소 문서·실패 메시지 — fix. `~/.codex` 생성·`CODEX_HOME` — fix(공식 문서 확인, `${CODEX_HOME:-…}`). `--file` 행렬(디렉토리 source·상대 링크·문구 단언) — fix. 임시 HOME 밖 불변 관찰 — fix(Acceptance 3). bootstrap README `:29-32`·`:73`, README `:394`·`:396` — fix. dry-run 부작용(`mkdir -p $LOCAL_BIN`·`touch $ZSHRC`) — defer(기존 결함). skill 목록 3곳 — fix(검증 때 `skills/<name>/SKILL.md` 존재 확인). 가장 위험한 단계·기각안 — fix(Decisions). `os.walk` 조용한 건너뜀 — 해당 없음(os.walk 를 쓰지 않게 됨).
- [묶음] 강 B1 g8-g9 Deferred 의 `~/.codex/agents` `CLAUDE_REVIEW_CODEX_MODE` 정리 유실 — fix(codex-agents-hooks 줄).
- [묶음] 강 B2 windows-ps1-verify 선행 의존 누락 — fix(선행: audit-install-fixes).
- [code] 경1 부모 symlink 를 거친 `..` 상대 링크를 논리 경로로 풀어 다른 파일을 "already" 로 오판(기존 결함, `--file` 로 AGENTS.md 에도 도달) — fix(`cd -P`, Red 재현 테스트).
- [code] 경2 README 두 곳의 "계속하고 마지막에 exit 1" 이 macOS 한정이 아님(setup.ps1 은 즉시 throw) — fix.
- [code] 경3 heal 테스트 docstring 의 "사전 chmod" drift — fix.
- [code] 경4 Acceptance 2 의 `--file` 충돌 행렬 일부가 dir 모드에서만 검증 — fix(other·dangling·missing source 추가).
- [code] 경5 rmtree 배선(onexc·<3.12 onerror) 미검증 — fix(쓰기 금지 디렉토리로 실패를 만들어 두 분기 subTest, mutation 으로 둘 다 잡힘 확인).
- [code] 경6 실패 요약이 원인과 무관하게 충돌 절만 가리킴 — fix("원인은 위 installer 메시지", README 에 source missing 안내).
- [code] 경7 백업 예시가 skills 폴더 안 `.bak` 이면 Codex 가 사본을 읽을 수 있음 — fix(`~/.agents/skills` 밖으로).
- [code] 경8 plan Next·Progress 뒤처짐 — fix.
- [code] nit override 는 비어 있지 않을 때만 우선 — fix. skill 목록 여러 곳 — fix(`install-codex-skill.test.sh` 가 `CODEX_SKILLS` 각 이름의 `skills/<name>/SKILL.md` 확인). 핸들러가 `func` 종류와 무관하게 재시도 — wontfix(Python 문서의 관용구와 같고, 결과는 뒤이은 rmdir 실패로 surface).
- [묶음] 약: wiki `workflow-failures` 의 `audit-low-batch` 포인터 — fix(ledger-bash-edits 줄에 갱신 담당). codex-agents-hooks 기계 작업·조사 혼재 — fix(순서 명시: toml 먼저). native-overlap 주기성·README `:396` 공동 편집 순서·단위별 성격(structural·저장소 밖) — fix(줄 메모).

# Deferred

- (낮음) Windows: `setup.ps1`·`install-codex-skill.ps1` 가 skill 7종과 `%USERPROFILE%\.codex\AGENTS.md` 를 연결하게 — pwsh·Windows 실행 검증 필요(파일 symlink 는 개발자 모드·관리자 권한). `windows-ps1-verify` 단위.
- (낮음) Windows junction: heal 의 `shutil.rmtree` 가 트리 안 junction 을 어떻게 다루는지(밖의 파일 read-only 해제 가능성) Windows 에서 확인 — 이번 변경 전에도 같았다(회귀 아님). `windows-ps1-verify` 단위.
- (처분: intent `audit-leftovers (미착수)` 로 넘김 — 사용자 결정 2026-09-27) `repo-audit-remaining` plan `# Deferred` 의 저우선 항목 중 어느 단위에도 배정되지 않은 것(pre-push 790 ref 명령줄 한계, heal `deinit` 의 `--literal-pathspecs`, ps1 `~/.claude` 면제의 symlink 해석, notify.ps1 재확인, statusline 상수 중복, heal 후속 `gitdir:` 검증 등) — done plan 의 Deferred 라 주인이 없다(intent `# Problem` 이 막으려는 상황). 새 단위로 묶을지 사용자 판정.
- (낮음) 공개 repo 에 사용자 홈 절대경로가 이미 들어 있다 — `README.md:479`(`claudeMdExcludes` 값), wiki `claude-code-agents-md-loading.md:29`. 이번 변경 전부터 있던 것.
- (낮음) `setup.sh` 가 `--dry-run` 에서도 `mkdir -p "$LOCAL_BIN"`(:55)·`touch "$ZSHRC"`(:110)를 실행해 "(DRY-RUN: 실제 변경 없음)" 안내와 어긋난다 — 이번 변경 전부터 있던 결함.
