---
title: git-log-added-lines-hardening
category: entity
created: 2026-09-25
updated: 2026-09-25
sources:
  - plans/2026-09-25-repo-audit-remaining/repo-audit-remaining-plan.md (plan-reviewer·code-reviewer 실측, 2026-09-25)
  - 커밋 4f44adb (scripts/pre-commit-check.{sh,ps1}, pre-commit-check.test.sh 회귀 케이스)
  - git 2.54 실측 · https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw · https://github.com/dotnet/runtime/issues/19142
---

# git-log-added-lines-hardening

**`git log -p` 로 "커밋들이 추가한 줄"을 모아 검사할 때, 사용자 설정·환경·attributes 가 추가 줄을 조용히 0건으로 만들 수 있다.** git 은 rc 0 으로 끝나므로 종료코드로는 알 수 없다. 보안 스캔(비밀 검출 등)은 빈 출력이 "깨끗함"으로 읽혀 fail-open 이 된다. 아래는 이 repo 의 pre-push 가드(`scripts/pre-commit-check.*`)를 만들며 git 2.54 에서 실측한 경로와 막는 방법이다. 모두 하네스 회귀 케이스로 고정돼 있다.

## 추가 줄을 숨기는 경로와 대응 (✅ 실측)

| 경로 | 무엇이 빠지나 | 대응 |
|---|---|---|
| path 제한 log 의 history simplification | 사이드 브랜치에서 넣었다 지운 줄(merge 가 한쪽 부모와 TREESAME) | `--full-history` |
| 기본 `-p` 의 merge diff 생략 | merge 해결에서만 들어온 줄(evil merge) | `-m` |
| `log.diffMerges=off` | `-m` 이 이 설정의 기본 형식을 따라 merge diff 가 다시 사라짐 | `-c log.diffMerges=separate`(옛 git 은 모르는 키라 무시 — 버전 제약 없음) |
| `log.showRoot=false` | root 커밋의 줄(첫 push) | `-c log.showRoot=true` |
| `log.follow=true` | pathspec 1개일 때 rename 을 짝지어 `+` 줄이 없음 | `-c log.follow=false` |
| NUL 바이트·`-diff` attribute·`diff.<drv>.binary`·`core.bigFileThreshold` | binary 로 판정돼 `Binary files … differ` 만 나옴 | `--text` |
| textconv·external diff | 변환된 출력 | `--no-textconv --no-ext-diff` |
| `color.ui=always` | 색 코드가 줄 앞에 붙어 `^+` 매칭 실패 | `--no-color` |
| `diff.noprefix`·`diff.mnemonicPrefix` | 헤더 형태가 바뀜 | `--src-prefix=a/ --dst-prefix=b/` |
| `git replace` | log 는 대체 객체를 읽지만 push 는 원본을 보냄 | `--no-replace-objects` |
| `GIT_{LITERAL,GLOB,NOGLOB,ICASE}_PATHSPECS` | `plans/*.md` 가 중첩 경로와 매칭되지 않음 | 환경에서 제거 |
| UTF-8 로케일 + 잘못된 바이트 | awk 가 `towc` 오류로 죽고 BSD grep 은 그 줄을 건너뜀(awk 만 고치면 grep 이 fail-open) | 스크립트 전체 `LC_ALL=C` |
| 본문이 `++` 로 시작하는 줄 | 패치에서 `+++ …` 로 보여 헤더로 오인 | `diff --git`~`@@` 상태 기계로 헤더 판정 |

그 밖의 원칙:
- git 이 실패하면 차단한다(`2>/dev/null || true` 금지).
- 경로 종류마다 따로 실행한다. pathspec 밖에서 들어온 rename 은 짝지어지지 않아 추가 줄로 보인다.

## 영향 없음으로 확인된 것 (위 명령 기준)

- `GIT_CONFIG_COUNT`·`GIT_CONFIG_PARAMETERS` 로 설정을 주입해도 명령줄 `-c` 가 이긴다.
- `diff.relative`(훅은 repo 루트에서 돈다), `diff.suppressBlankEmpty`, `log.showSignature`, `diff.interHunkContext`, `diff.renames=copies`, `diff.context`, `GIT_DIFF_OPTS`, `GIT_EXTERNAL_DIFF`, `core.attributesFile`, `info/attributes` 의 textconv 는 모두 차단 결과가 같다.
- `.git/info/grafts` 는 스캔에서는 줄을 숨기지만, 실제 push 도 graft 를 따라가서 원격이 "missing necessary objects" 로 거부한다. 유출은 없다(로컬 bare 원격 실측).

## Windows PowerShell 쪽 함정 (같은 가드의 ps1)

- `Process.Start` 에 bare `git` 을 주면 CreateProcess 가 PATH 보다 **현재 디렉토리**(훅은 repo 루트)를 먼저 찾는다 → repo 에 들어 있는 `git.exe` 가 실행된다. `Get-Command git -CommandType Application` 으로 얻은 절대경로(`.exe` 우선)를 쓴다. 근거는 Microsoft 문서다. .NET 이 `lpApplicationName=NULL` 로 호출한다는 부분은 공개 이슈 근거라 ⚠️.
- `ProcessStartInfo.EnvironmentVariables` 는 .NET Framework(PS5.1)에서 대소문자만 다른 env(MSYS2 의 `tmp`/`TMP`)가 있으면 `Item has already been added` 로 던진다. 프로세스 env 를 `Remove-Item Env:` 로 지우고 자식이 상속하게 한다.
- PS5.1 의 native 호출은 stdout 을 콘솔 코드페이지로 디코딩하고(한국어 Windows 는 CP949), `2>$null` + `EAP=Stop` 에서 stderr 를 종료 오류로 바꾼다. `Process` + UTF-8 `StandardOutputEncoding` 으로 피한다. stdin 도 `[Console]::In` 대신 UTF-8 `StreamReader` 로 읽는다.
- 위 PS5.1 동작은 이 Mac(pwsh 7)에서 재현하지 못했다(⚠️ 문서·이슈 근거).

## 연계

"출력 0건 ≠ 없음"이라는 같은 함정은 [[lesson-grep-absence-not-proof]] 에 있다. git 훅의 hang·재귀 안전은 [[git-hook-network-safety]] 에, git 동작을 실측해 규칙으로 옮긴 다른 사례는 [[git-autosquash-target-selection]] 에 있다.
