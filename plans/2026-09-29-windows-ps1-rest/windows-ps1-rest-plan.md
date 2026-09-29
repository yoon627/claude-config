---
title: windows-ps1-rest — 이슈 #190 의 나머지 Windows 항목(PS5.1 BOM, Codex 연결, heal junction, ps1 pre-push stdin, notify balloon)
status: done
started: 2026-09-29
updated: 2026-09-29
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

이슈 #190 의 Windows 에서만 검증할 수 있는 나머지 항목을 이 PC(Windows 11, Git Bash, pwsh 7, PowerShell 5.1)에서 실측하고 고친다. macOS `Resolve-Path` symlink 면제 항목은 macOS 에서만 검증 가능해 제외한다(사용자 지시 2026-09-29 "window 관련만").

# Intent

- 링크: 묶음 intent 의 `windows-ps1-verify-rest (미착수)` 줄(이 plan 으로 치환). 선행 단위 `plans/2026-09-29-windows-ps1-verify/`(PR #200).
- 델타: 목적 4개 + 관찰 1개로 나눠 목적마다 커밋한다.
  - U1 PS5.1 이 BOM 없는 ps1 을 CP949 로 읽어 파싱 실패 — 가드(`pre-commit-check.ps1`)가 설치 훅(`exec powershell`)에서 전부 exit 1. `.editorconfig` 는 `utf-8-bom` 을 요구하지만 도구 편집엔 적용되지 않았다.
  - U2 `setup.ps1` Codex 연결을 macOS 와 맞춘다(skill 7종 + `AGENTS.md` 파일 symlink, 실패 모아 exit 1), `install-codex-skill.ps1` 에 `-File`, `*.test.ps1` 을 verify 에 연결(pwsh 없으면 77).
  - U3 heal `_force_rmtree` 의 Windows 경로(read-only·트리 안 junction)를 Windows 테스트로 실측 — 문제가 보일 때만 코드 수정(`lesson-no-speculative-platform-switch`).
  - U4 `pre-commit-check.ps1` pre-push 스캔을 `git log --stdin` 으로(명령줄 32,767자), PS5.1 native stdin 파이프 확인.
  - U5 `notify.ps1` balloon — 표시 여부는 사람이 봐야 한다. 실행하고 사용자 관찰로 적용 여부를 정한다.
- Out of scope: macOS `Resolve-Path` symlink 면제, Windows CI job 추가(별도 판단).

# Acceptance

1. U1: `node scripts/ps1-encoding.test.js` — 추적 ps1 전부 BOM(수정 전 8개 누락 Red 확인). `PWSH=<powershell.exe 5.1> bash scripts/pre-commit-check.test.sh` → `135 passed, 0 failed`(수정 전 ps1 66건 전부 exit 1).
2. U2: `install-codex-skill.test.ps1` 에 파일 모드 행렬이 있고 pwsh 7·5.1 에서 통과. verify.sh 가 `*.test.ps1` 을 돌리고 pwsh 가 없으면 `[skip]`. `setup.ps1 -DryRun`(또는 해당 단계)에서 skill 7종·`AGENTS.md` 연결 계획이 나오고, skill 목록이 `setup.sh` 의 `CODEX_SKILLS` 와 같다(테스트 단언). README(`scripts/bootstrap/README.md`·루트) 서술 동기화.
3. U3: Windows 전용 테스트 — 트리 안 junction 이 가리키는 트리 밖 read-only 파일이 `_force_rmtree` 뒤에도 존재하고 read-only 유지. 결과에 따라 코드 수정 또는 "수정 불필요" 를 wiki `link-following-file-ops` 에 실측으로 기록.
4. U4: ps1 pre-push 가 커밋 목록을 stdin 으로 넘긴다. 빈 입력·첫 빈 줄이면 차단(sh 가드와 같은 규칙). pwsh 7·5.1 에서 pre-commit-check 테스트 통과, ref 790+ 규모 케이스 1개.
5. U5: 사용자에게 balloon 이 보였는지 확인한 결과를 기록하고 그에 맞춰 적용/미적용.
6. 전체: Windows `bash scripts/verify.sh` rc 0, PR CI 통과.

# Progress

- 2026-09-29: 착수. U1 — BOM 테스트 Red(8개) → 8개 파일에 BOM → Green(10개), PS5.1 가드 테스트 135/135. 조사(subagent): setup.ps1 은 jira-worklog 1개만, `*.test.ps1` 은 verify·CI 미연결, heal junction 테스트 없음.
- 2026-09-29: U5 관찰 — `notify.ps1` 의 balloon 예비 경로를 그대로(A, 0.2초 만에 종료)와 `Start-Sleep 5`+`Dispose()`(B, 5.2초) 로 `powershell.exe`(5.1, notify-hook.js 가 쓰는 엔진)에서 띄움. 사용자 관찰: **A·B 둘 다 보임**(Windows 11 10.0.26200). → 수정 안 함.
- 2026-09-29: U1 커밋. U4 — 새 원격에 서로 다른 커밋 800개 push 케이스 추가(fast-import, 두 엔진) → ps1 Red(`Process.Start` 가 명령줄 길이로 예외, 깨끗한 push 차단) → `Invoke-Git -Stdin`, `Get-RevInput`(순서 유지 중복 제거, `^` 제외), `git log --stdin`, 빈 입력 차단 → pwsh 7·PS5.1 모두 137/137.
- 2026-09-29: U4 커밋. U3 — Windows 전용 테스트(트리 안 junction → 밖의 read-only 파일, junction 자체 read-only 로 핸들러 경로 강제·spy 로 호출 확인) 통과: 밖의 파일 존재·read-only 유지. heal 코드 수정 없음, wiki `link-following-file-ops` ⚠️→✅.
- 2026-09-29: U2 — `install-codex-skill.ps1 -File`, setup.ps1 3b 를 setup.sh 와 맞춤(skill 7종·AGENTS.md·agent 정의, 실패 모아 exit 1), `.test.ps1` 파일 모드 행렬·목록 일치, verify 가 `*.test.ps1` 실행. 실측: PS5.1 `New-Item -ItemType SymbolicLink` 은 개발자 모드에서도 관리자 요구, `setup.ps1 -DryRun`(5.1) 계획 정상.
- 2026-09-29: code-reviewer(+Codex) REQUEST CHANGES — 아래 Review Disposition. Major(U4 회귀): PS5.1 + UTF-8 콘솔 입력(이 PC 기본값이 65001)에서 .NET Framework 가 git stdin 앞에 BOM → `bad revision` exit 128 → 모든 push 차단. 재현(5.1 exit 128 / 7 exit 0) → 테스트에 `ps51` 엔진(UTF-8 콘솔) 추가 Red(pre-push 41건) → `Process.Start` 동안 `[Console]::InputEncoding` 을 BOM 없는 UTF-8 로 → 207/207(sh·7·5.1).
- 2026-09-29: 나머지 리뷰 지적 반영, verify.sh 배열 shellcheck 수정, 전체 verify 초록. commit-check 로 fixup 2개를 U1·U4 에 합침(4커밋, tree 동일). `/e merge` — PR #205.

# Next


# Review Disposition

- [code Major] PS5.1 stdin BOM(U4 회귀) — fix(`[Console]::InputEncoding` 임시 전환, `ps51` 엔진 테스트). 회귀 확인 절차: `bash scripts/pre-commit-check.test.sh`(Windows 에 powershell.exe 가 있으면 `ps51` 엔진이 UTF-8 콘솔로 돈다).
- [code Minor, severity disputed(Codex Major)] mklink 경로의 cmd 메타문자 — fix(`CreateSymbolicLinkW` 직접 호출, 생성 후 대상 확인, `&` 경로 테스트).
- [code Minor] 파일 모드 SKIP 과대 — fix(개발자 모드·관리자로 사전 판정, real-file 충돌은 skip 밖).
- [code Minor] `[string]$Stdin=$null` sentinel 죽음 — fix(`$PSBoundParameters`).
- [code Minor] verify 가 pwsh 만 — fix(`*.test.ps1` 을 pwsh·powershell.exe 둘 다).
- [code Minor PLAUSIBLE] python 탐지(py 런처) — fix(`py -3`). sync em dash — fix(`PYTHONUTF8=1`).
- [code Minor] 800커밋 block 케이스 — fix(801번째 ref 에만 토큰).
- [code Nit] 중복 `LASTEXITCODE`(코드 교체로 소멸)·목록 순서(테스트가 순서까지 비교)·BOM 테스트 `--others` — fix.
- [code Minor] plan/intent 어긋남 — fix(intent 줄 정정, macOS 항목 별도 `(미착수)` 줄).

# Decisions

- U5 는 적용하지 않는다(2026-06 감사 제안 기각). 이유: 사용자 관찰로 현재 코드의 balloon 이 표시됐고, 대기를 넣으면 알림 훅이 5초 더 산다. 다른 Windows 빌드에서 안 보이는 사례가 나오면 다시 연다.
- U1 은 ASCII 화가 아니라 BOM 추가. 이유: `.editorconfig` 가 이미 `utf-8-bom` 을 정했고(G7) `gwl.ps1`·`notify-hook.ps1` 이 그 형태다. 재발 방지는 `ps1-encoding.test.js`(CI 에서도 돈다) — 도구 편집은 `.editorconfig` 를 따르지 않기 때문.

# Key Files

- `scripts/ps1-encoding.test.js` — ps1 BOM 잠금
- `scripts/*.ps1`, `scripts/bootstrap/*.ps1`, `skills/jira-worklog/run_worklog.ps1` — BOM
- `scripts/bootstrap/setup.ps1`, `scripts/bootstrap/install-codex-skill.ps1`, `.test.ps1` — U2
- `skills/wt/heal_submodules.py`, `test_heal_submodules.py` — U3
- `scripts/pre-commit-check.ps1` — U4
- `scripts/notify.ps1` — U5

# Blockers
