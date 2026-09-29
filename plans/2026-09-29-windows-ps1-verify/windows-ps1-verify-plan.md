---
title: windows-ps1-verify — Windows 에서 verify.sh 가 빨갛던 ps1·도구 부재 3건을 원인대로 고친다 (#190 의 첫 단위)
status: done
started: 2026-09-29
updated: 2026-09-29
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

Windows(Git Bash·pwsh 7)에서 `bash scripts/verify.sh` 가 기존 결함 3건으로 `FAILED: 3` 이던 것을 원인대로 고친다. 이슈 #190 의 나머지 항목은 이 plan `# Deferred` 로 넘긴다.

# Intent

- 링크: 묶음 `plans/2026-09-25-repo-audit-followups/intent.md` 의 windows-ps1-verify 단위(이슈 #190).
- 델타: 이 단위는 "Windows verify 를 빨갛게 만드는 3건"만 다룬다. 원인은 모두 Windows 에서 재현해 확인했다(2026-09-29).
  1. `install-hooks.test.js` ps1 6건 — 테스트가 `sh -c 'command -v pwsh'` 의 Git Bash 경로(`/c/Program Files/...`)로 node spawn 을 해 `ENOENT`. ps1 을 한 번도 실행하지 못했는데 "ps1: ran" 을 찍었다.
  2. `pre-commit-check.test.sh` ps1 2건 — PowerShell `$HOME` 은 `HOME` 환경변수가 아니라 `USERPROFILE` 을 따른다(7·5.1 실측). 테스트는 가짜 `HOME` 만 넘겨 ps1 은 실제 사용자 홈을 봤다. `install-hooks.test.js` 의 ps1 도 같은 이유로 실제 `~/.claude` 가드에 기대 통과하고 있었다(code-reviewer).
  3. `record-verified.test.sh` — `jq` 가 없으면 exit 1. verify 의 "미설치 도구는 `[skip]` 으로 요약에 남긴다" 규약과 어긋난다.
- 분할: 없음 — 세 건 모두 "Windows verify 초록" 한 목적의 테스트·가드 교정이고 각 1~10줄이다.
- Out of scope: 이슈 #190 의 나머지(아래 `# Deferred`), macOS 의 `Resolve-Path` symlink 문제(#190 항목 5 원문 — 이번 수정은 `HOME` 불일치만 고친다).

# Acceptance

1. `node scripts/install-hooks.test.js`(Windows): ps1 케이스가 실제로 실행돼 통과하고, 생성된 훅이 가짜 HOME 의 가드를 부른다(새 단언 — USERPROFILE 격리를 빼면 FAIL 하는 것을 사본으로 확인). 옛 git 흉내 1건은 Windows 에서 이유를 찍는 SKIP(.NET `Process.Start` 는 PE 실행 파일만 띄워 sh shim 을 못 씀 — 실측 오류 "not a valid application for this OS platform"). 결과 `ALL PASS`.
2. `bash scripts/pre-commit-check.test.sh`(Windows): `0 failed`. `pre-commit-check.ps1` 은 바꾸지 않는다.
3. `bash scripts/verify.sh`(Windows, jq 없음): `record-verified.test.sh` 가 `[skip] … jq is required` 로 찍히고, 케이스 skip 도 `<파일>(case)` 로 요약에 남아 마지막 줄이 `ALL PASS (skip: …)`. `CI=1` 에서 jq 가 없으면 rc 1. README 445 에 규약.
4. PR CI(ubuntu, jq 있음) 통과 — skip 규약 변경이 CI 결과를 바꾸지 않는다.

# Progress

- 2026-09-29: 원인 3건 재현·확인 → 수정. install-hooks ps1 5 PASS + 1 SKIP(`ALL PASS`), pre-commit-check 135/135, verify bash 축 `ALL PASS (skip: record-verified.test.sh)`.

- 2026-09-29: code-reviewer(+Codex) REQUEST CHANGES — 아래 Review Disposition. 가드 수정을 되돌리고 테스트 격리(USERPROFILE)로 방향 변경, 훅 가드 경로 단언 추가(Red 확인), 케이스 skip 요약·CI 에서 jq 부재 실패. install-hooks `ALL PASS`, pre-commit-check 135/135, verify node 축 `ALL PASS (skip: install-hooks.test.js(case))`.
- 2026-09-29: 전체 verify(Windows) rc 0, `ALL PASS (skip: install-hooks.test.js(case) record-verified.test.sh)`. `/e merge` — PR #200. 나머지 #190 항목은 묶음 intent 의 `windows-ps1-verify-rest (미착수)` 줄로.

# Next


# Review Disposition

- [code Major] Windows ps1 설치 테스트가 실제 `~/.claude` 가드에 의존, 가드·설치 스크립트 HOME 규칙 불일치 — fix(가드 되돌림, 두 테스트가 USERPROFILE 격리, 훅 가드 경로 단언).
- [code Minor] 케이스 skip 이 verify 요약에 안 보임 — fix(`SKIP ` 줄 수집, `(case)` 표기).
- [code Minor] 77 우발 종료가 skip 으로 둔갑 — wontfix(감수, Decisions).
- [code Minor] CI 에서 jq 부재 시 조용히 green — fix(`CI` 이면 exit 1).
- [code Minor] plan 의 "CI 에 pwsh 없음" 오류 — fix(Decisions 정정).
- [code Nit] ps1 주석 언어 — 해당 줄 되돌림으로 소멸. verify.sh 헤더 77 — fix. `basename` 요약 — wontfix(출력 줄에 전체 경로).

# Decisions

- ps1 옛 git 케이스는 Windows 에서 SKIP 으로 둔다. 기각: `git.cmd` 래퍼 — `.NET Process.Start` 가 PATH 에서 확장자 없는 shim 을 먼저 집어 여전히 실패했다(실측). 그 검사(`install-hooks.ps1:44`)는 플랫폼 무관 문자열 검사라, ubuntu CI 러너의 pwsh(러너 이미지에 PowerShell 7 포함)가 PATH 에서 발견되면 거기서 돈다(⚠️ 이 repo CI 로그의 `ps1: ran` 은 PR 에서 확인).
- skip 은 테스트가 종료 코드 77 로 알린다(automake 관례). 기각: verify.sh 에 파일 이름으로 도구 조건을 하드코딩 — 테스트가 자기 전제를 가장 잘 안다. 감수: `set -e` 테스트 안의 명령이 우연히 77 을 내면 skip 으로 보인다(발생 경로 미발견, code-reviewer PLAUSIBLE).
- ~~ps1 면제 판정은 `$env:HOME` 우선~~ → **가드는 그대로(`$HOME`), 테스트가 `USERPROFILE` 도 가짜 홈으로 넘긴다** (이유: PowerShell `$HOME` 은 USERPROFILE 을 따르고, Claude Code 가 쓰는 `~/.claude`(node `os.homedir()`)도 Windows 에서 USERPROFILE 이다 — 가드만 `$env:HOME` 으로 바꾸면 설치 스크립트(`install-hooks.ps1:58`, `$HOME`)와 어긋나고 HOME≠USERPROFILE 인 머신에서 실제 `~/.claude` 면제가 풀린다. code-reviewer Major).

# Key Files

- `scripts/install-hooks.test.js` — pwsh 경로 `cygpath -w`, USERPROFILE 격리·훅 가드 경로 단언, 옛 git 케이스 Windows SKIP, 실패 시 실측 출력
- `scripts/pre-commit-check.test.sh` — ps1 호출에 USERPROFILE 격리
- `scripts/verify.sh`, `scripts/record-verified.test.sh`, `README.md` — 종료 코드 77 skip

# Blockers

# Deferred

이슈 #190 에서 이 단위가 다루지 않은 항목(Windows 에서만 검증 가능):
- pre-commit 경로 ps1 의 native 출력 CP949 디코딩(PS5.1).
- `setup.ps1`·`install-codex-skill.ps1` 이 Codex skill 7종·`%USERPROFILE%\.codex\AGENTS.md` 연결, `.ps1`·`.test.ps1` 에 `.sh` 의 `--file` 대응 옵션, README 의 macOS/Windows 차이 서술.
- heal 의 Windows 경로(read-only 해제 재시도, 트리 안 junction — `os.path.islink` 는 junction 을 못 본다).
- `pre-commit-check.ps1` pre-push 스캔을 `git log --stdin` 으로(명령줄 32,767자 한계 — PS5.1 native stdin 파이프 확인).
- ps1 `~/.claude` 면제의 symlink(macOS `Resolve-Path`).
- `notify.ps1` balloon 의 `Start-Sleep`+`Dispose()`.
