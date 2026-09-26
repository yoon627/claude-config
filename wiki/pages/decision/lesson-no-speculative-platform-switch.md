---
title: lesson-no-speculative-platform-switch
category: decision
created: 2026-09-26
updated: 2026-09-26
sources:
  - https://www.msys2.org/docs/filesystem-paths/ (MSYS2 — `MSYS2_ARG_CONV_EXCL` 은 `*` 면 모든 인자를 변환에서 뺀다)
  - https://github.com/git-for-windows/msys2-runtime/pull/11 (Git for Windows — `MSYS_NO_PATHCONV` 도입, 값과 무관하게 설정만 돼 있으면 명령의 경로 변환을 끈다, 2015-06-17 머지)
  - https://raw.githubusercontent.com/msys2/msys2-runtime/msys2-3.6.1/winsup/cygwin/msys2_path_conv.cc (`find_path_start_and_type` — `MSYS_NO_PATHCONV` 가 있으면 모든 인자 NONE, `*` 가 든 인자는 skip, `<a>:<b>` 는 `:` 뒤가 `/`·`.`·`:` 가 아니고 `=` 가 없으면 SIMPLE_WINDOWS_PATH 로 그대로 복사)
  - https://github.com/datanika-io/datanika-core/issues/1075 (같은 증상 공개 보고 — `MSYS_NO_PATHCONV=1` 아래 `git -C /d/...` 가 `fatal: cannot change to '/d/...'`)
  - plans/2026-09-26-autopull-verified-client (code-reviewer Critical 과 처분, 2026-09-26 — 이 페이지 작성 시점에 미머지 브랜치 `autopull-verified-client` 에만 있고 Windows 확인 대기)
---

# lesson-no-speculative-platform-switch

**실행해 볼 수 없는 플랫폼을 위해 "거기서는 무시되거나 도움이 될 것" 이라는 추정만으로 환경변수·옵션 스위치를 넣지 않는다.** 검증 가능한 플랫폼에서는 그 스위치가 효과가 없으니 테스트가 모두 통과하고, 스위치가 실제로 작동하는 플랫폼에서만 동작이 바뀐다. 그래서 잘못 넣은 방어가 아무 신호 없이 그 플랫폼의 모든 머신을 멈출 수 있다.

## 사례 (이 lesson 의 발단)

[[autopull-verified-ff]] 의 client 단계에서 SessionStart 자동 pull 이 `git -C <repo> fetch … origin '+refs/heads/main:refs/remotes/origin/main' '+refs/heads/ci/*:refs/remotes/origin/ci/*'` 를 부르게 바꿨다. Windows Git Bash 가 refspec 을 경로로 오인해 바꿀까 봐 fetch 에 `MSYS_NO_PATHCONV=1` 과 `MSYS2_ARG_CONV_EXCL='*'` 를 붙였다. 이 Mac 에서는 두 변수가 아무 일도 하지 않아 테스트가 모두 통과했다.

code-reviewer 가 Critical 로 잡았다.
- 두 변수는 특정 인자가 아니라 **명령의 모든 인자**에서 변환을 끈다(MSYS2 문서·Git for Windows PR·변환 코드).
- 그러면 Git Bash 가 넘기는 `-C /c/Users/...` 도 변환 없이 native `git.exe` 로 간다. native git 은 이 경로로 이동하지 못하므로 fetch 가 매번 실패한다 — 같은 변수로 `git -C /d/...` 가 `fatal: cannot change to` 로 실패한 공개 보고가 있다 ⚠️(이 스크립트를 Windows 에서 실행해 보지는 않았다).
- 실패는 무음이다. fetch 가 실패하면 캐시가 전진하지 않고, 세션 브리프도 새 기록을 보지 못해 침묵한다. Windows 머신의 자동 pull 이 모두 조용히 멈춘다(macOS·Linux 에는 영향이 없다).
- 막으려던 위험은 변환 코드상 일어나지 않는다. ci refspec 은 `*` 가 들어 있어 통째로 건너뛰고, main refspec 은 `:` 뒤가 `r` 이고 `=` 가 없어 그대로 복사된다 ⚠️(코드 읽기로 판단, Windows 실행은 안 했다). "`/` 로 시작하지 않으면 안전" 이 아니다 — `--dir=/foo` 처럼 `/` 로 시작하지 않아도 변환되는 인자가 있다(MSYS2 문서의 예).

처분: 두 변수를 제거하고, 스크립트에 두 이름이 다시 들어오지 못하게 주석을 뺀 텍스트를 단언하는 테스트를 넣었다(Windows 는 CI 에 없다). 머지 전에 Windows 머신에서 한 줄 실행해 보는 확인을 사용자에게 맡겼다. 이 페이지를 쓴 2026-09-26 에는 그 브랜치가 아직 머지 전이다.

## 근본 원인 (3 Whys)

1. **왜 스위치를 넣었나?** Windows 경로 변환이 refspec 을 망칠 수 있다는 가능성을 미리 막으려 했다. 위험이 실제로 있는지는 변환 규칙을 보고 확인하지 않았다.
2. **왜 그 방어가 해로웠나?** 스위치의 영향 범위가 "그 인자 하나"가 아니라 "명령 전체"였다. 문서를 확인했다면 `-C` 경로도 함께 꺼진다는 것을 알 수 있었다.
3. **왜 놓쳤나?** 검증할 수 없는 플랫폼에서는 "여기서는 무시되니 저기서도 해가 없을 것" 이라는 추정이 검증을 대신했다. 이 Mac 의 통과는 그 스위치에 대해 아무것도 증명하지 않는데, 통과를 근거로 삼았다.

## 올바른 방법

- 플랫폼 전용 스위치를 넣기 전에 **영향 범위를 공식 문서로 확인한다**. 인자 하나에만 걸리는지, 명령 전체에 걸리는지, 자식 프로세스에 상속되는지 확인한다.
- **막으려는 위험이 실제로 있는지 먼저 확인한다.** 규칙을 어림하지 말고 문서·코드로 본다. 여기서는 두 refspec 모두 변환 코드상 그대로 넘어갔다. "`/` 로 시작하지 않으면 안전" 같은 요약은 틀린다.
- 영향 범위와 위험의 실재를 문서로 확인하지 못했고 대상 플랫폼에서 실행도 못 하면, **스위치를 넣지 말고 미검증으로 보고한다**. 위험이 문서로 실재해서 넣는다면 가장 좁은 형태로 넣는다(예: 전부 끄는 `*` 대신 해당 인자의 prefix 만 빼는 `MSYS2_ARG_CONV_EXCL` 목록).
- 대상 플랫폼 확인은 **머지 전**이 먼저다. 머지가 곧 모든 머신 배포인 변경(자동 pull 처럼)에서는 `[post-merge]` 로 미루면 이미 늦다. 그렇지 않을 때만 `[post-merge]` 항목으로 둔다.
- 방어가 막으려는 실패와 방어가 만드는 실패를 나란히 놓는다([[lesson-gate-safe-side-first]]). 여기서는 둘 다 "Windows 자동 pull 무음 정지"로 결과가 같았다. 차이는 증거였다 — 막으려던 쪽은 코드상 일어나지 않고, 방어가 만든 쪽은 문서상 확실히 일어난다. 방어가 실패를 더 확실하게 만들 뿐이면 넣지 않는다.
- 스위치를 제거하기로 했으면 **재도입을 막는 단언**을 테스트에 둔다. 해당 플랫폼이 CI 에 없으면 텍스트 단언밖에 남지 않는다.
- 같은 뿌리의 다른 사례로, 게이트 hook 이 어떤 플랫폼에서는 실패한 뒤 통과(fail-open)해 버린 일이 있다([[lesson-agent-hook-if-best-effort]]). 플랫폼마다 막혀야 할 케이스를 실제로 넣어 확인해야 한다.

## 연계

자동 pull 검증 게이트의 설계는 [[autopull-verified-ff]], 안전측 판단은 [[lesson-gate-safe-side-first]], 플랫폼별 fail-open 사례는 [[lesson-agent-hook-if-best-effort]].
