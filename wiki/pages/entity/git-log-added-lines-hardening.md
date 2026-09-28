---
title: git-log-added-lines-hardening
category: entity
created: 2026-09-25
updated: 2026-09-28
sources:
  - git 2.54.0 (Apple Git-157) `git log --stdin`·`git rev-list --stdin` 실측 — scratch 재현 후, 조건을 바꿔 반례를 찾는 재실행 (2026-09-28), git v2.54.0 revision.c `read_revisions_from_stdin`
  - git RelNotes 2.42.0·2.43.0 · 커밋 c40f0b78771e "revision: handle pseudo-opts in `--stdin` mode" (v2.42.0 에 처음) · PR #188 (scripts/pre-commit-check.sh stdin 전환)
  - plans/2026-09-25-repo-audit-remaining/repo-audit-remaining-plan.md (plan-reviewer·code-reviewer 실측, 2026-09-25)
  - plans/2026-09-26-push-remote-scope (remote sha 기준 제외·replace peel·pushurl 실측, 2026-09-26)
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
| `git replace` | log 는 대체 객체를 읽지만 push 는 원본을 보냄. 원격 태그의 `^{commit}` peel 도 대체 객체를 따라 원격에 없는 커밋을 제외 목록에 넣는다 | `--no-replace-objects`, 스크립트 전체 `GIT_NO_REPLACE_OBJECTS=1` |
| `GIT_{LITERAL,GLOB,NOGLOB,ICASE}_PATHSPECS` | `plans/*.md` 가 중첩 경로와 매칭되지 않음 | 환경에서 제거 |
| UTF-8 로케일 + 잘못된 바이트 | awk 가 `towc` 오류로 죽고 BSD grep 은 그 줄을 건너뜀(awk 만 고치면 grep 이 fail-open) | 스크립트 전체 `LC_ALL=C` |
| 본문이 `++` 로 시작하는 줄 | 패치에서 `+++ …` 로 보여 헤더로 오인 | `diff --git`~`@@` 상태 기계로 헤더 판정 |

그 밖의 원칙:
- git 이 실패하면 차단한다(`2>/dev/null || true` 금지). 예외는 push 대상의 remote sha 를 로컬 커밋으로 푸는 단계뿐이다 — 원격만 가진 커밋·blob·tree 는 "뺄 것이 없음" 이라는 정상 분기라, 차단하지 않고 제외만 생략한다(더 넓게 스캔). blob·tree peel 은 `--quiet` 에도 `error:` 를 찍어 그 호출에서만 stderr 를 버린다.
- "이미 공개됨" 으로 뺄 범위는 remote-tracking ref 가 아니라 stdin 각 줄의 remote sha(원격이 알려 준 현재 값)로 정한다. 추적 ref 는 다른 원격의 것이거나, 재작성 뒤 오래됐거나, pushurl 마다 다를 수 있다(훅은 pushurl 마다 따로 불리고 remote sha 도 URL 별로 온다 — 2026-09-26 실측). 대가로 새 브랜치 push 는 이력 전체를 다시 본다([[ci-secret-scan-backstop]]).
- ref 줄의 sha 는 repo 해시 길이(`rev-parse --show-object-format` — sha1 40자·sha256 64자)만 받는다. 그 밖의 16진수 문자열(짧은 것, sha1 repo 의 64자)은 rev-parse 가 같은 이름의 ref 로 풀 수 있다(code-reviewer 재현: 64자 이름의 ref 가 토큰 커밋을 가리키면 제외됐다).
- 경로 종류마다 따로 실행한다. pathspec 밖에서 들어온 rename 은 짝지어지지 않아 추가 줄로 보인다.

## 커밋 목록을 stdin 으로 넘길 때 — `git log --stdin` (✅ 2.54 실측)

push 커밋과 제외 커밋을 argv 로 넘기면, ref 가 많은 push 에서 Windows 명령줄 한계 32,767자(CreateProcessW `lpCommandLine`, Microsoft 문서)를 넘어 git 프로세스를 띄우지 못한다. 새 원격에 약 790개 이상이 기준인데, 이 수는 32,767자를 sha1 한 개(약 41자)로 나눈 계산값이다. 가드가 fail-closed 라 유출은 없지만 push 가 아예 안 된다(⚠️ 이 문단은 문서·계산 근거이고 Windows 에서 실측하지 않았다. 아래 bullet 은 2.54 실측). 그래서 `--stdin` 으로 넘기는데(이 repo 의 sh 가드는 PR #188 부터, ps1 은 아직 argv), 그러면 argv 에는 없던 함정이 생긴다.

- **빈 입력이면 HEAD 를 스캔한다.**
  - stdin 이 비었거나 첫 줄이 빈 줄이면 리비전이 0개가 되고, `git log` 는 문서화된 기본값 HEAD 로 돈다(rc 0). argv 에도 리비전이 없을 때만 그렇다.
  - HEAD 기본값은 `git log` 의 것이다. `git rev-list --stdin` 은 빈 입력이면 아무것도 출력하지 않는다(rc 0).
  - 입력을 만드는 단계(dedupe 파이프 등)가 조용히 실패하면 push 커밋 대신 HEAD 이력을 검사해 통과하는 fail-open 이 된다. 그래서 목록을 변수로 먼저 만들고 비면 차단한다.
- **빈 줄에서 읽기를 멈춘다.**
  - 목록 중간의 빈 줄(LF·CRLF 모두) 뒤에 오는 리비전은 경고 없이 버려진다(rc 0). 빈 줄은 걸러서 넘긴다(`awk 'NF'`).
  - 공백만 있는 줄은 빈 줄로 치지 않고 `fatal: bad revision ' '`(128)이다.
  - 근거는 실측과 `revision.c` `read_revisions_from_stdin` 의 `if (!sb.len) break;` 이다. git-log·git-rev-list 문서에는 이 동작이 없다.
  - `--` 줄 뒤는 pathspec 으로 읽히고, 거기서 빈 줄은 `fatal: empty string is not a valid pathspec`(128)이다.
- **제외 커밋은 `^<sha>` 줄로 넘긴다.** argv 와 똑같이 동작한다.
  - `--not`·`--all`·`--glob=<pat>` 같은 pseudo-option 줄은 2.42.0 부터 받는다(RelNotes 2.42.0 — 커밋 c40f0b78771e 가 v2.42.0 에 처음 들어갔다). 같은 커밋이 `--end-of-options` 줄도 받게 했지만 RelNotes 에는 없다.
  - 2.43.0 에서 `--not` 의 적용 범위가 바뀌었다. stdin 의 `--not` 은 stdin 리비전에만, 명령줄의 `--not` 은 명령줄 리비전에만 적용된다(RelNotes 2.43.0).
  - 그 밖의 옵션 줄(`-n1`·`--since=…`)은 `fatal: invalid option '-n1' in --stdin mode`(128)이다. 값을 다음 줄에 둔 `--glob` 도 실패한다(`--glob=<pat>` 처럼 붙여 써야 한다).
  - `^<sha>` 는 리비전 문법이라 버전 제약이 없다고 보고 이 형식을 쓴다. 2.42 이전 git 에서는 실측하지 않았다(⚠️).

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

"출력 0건 ≠ 없음"이라는 같은 함정은 [[lesson-grep-absence-not-proof]] 에 있다. `GIT_*_PATHSPECS` 전역 설정끼리의 충돌과 `--literal-pathspecs` 의 범위는 [[git-literal-pathspecs]] 에 있다. git 훅의 hang·재귀 안전은 [[git-hook-network-safety]] 에, git 동작을 실측해 규칙으로 옮긴 다른 사례는 [[git-autosquash-target-selection]] 에 있다.
