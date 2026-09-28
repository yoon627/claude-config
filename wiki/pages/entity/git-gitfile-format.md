---
title: git-gitfile-format
category: entity
created: 2026-09-28
updated: 2026-09-28
sources:
  - git 2.54.0 (Apple Git-157) 실측 — `.git` 파일 변형을 scratch 에서 재현한 뒤, 조건을 바꿔 반례를 찾는 재실행 (2026-09-28)
  - git v2.54.0 setup.c `read_gitfile_gently` (접두어 검사·`\r`/`\n` 제거) · setup.c 의 탐색 경로 메시지 (v2.55.0 L940 `not a git repository: %s`, master L947 `gitfile does not point to a valid repository: %s`, 2026-09-28 조회)
  - https://git-scm.com/docs/gitrepository-layout
  - git 커밋 1dd27bfbfd "setup: improve error diagnosis for invalid .git files" (v2.54.0·v2.55.0 포함) · 커밋 54a441bcea "read_gitfile(): simplify NOT_A_REPO error message" · RelNotes 2.56.0 (master, 2026-09-28 조회)
  - PR #188 (skills/wt/heal_submodules.py `_is_gitlink`)
---

# git-gitfile-format

submodule 이나 linked worktree 의 작업 트리에는 `.git` **파일**(gitlink)이 있다. 이 페이지는 git 이 그 파일을 언제 유효하다고 보는지 정리한다(git 2.54 실측). gitrepository-layout 문서는 "`gitdir: <path>` 를 담은 파일" 이라고만 적는다. 정확한 규칙은 `setup.c` 에만 있다.

## 형식 규칙 (✅ 2.54.0)

- **첫 8바이트가 정확히 `gitdir: `(소문자, 공백 한 칸)여야 한다.** 아니면 `fatal: invalid gitfile format: <.git 파일 경로>`(128)이다. 거부되는 예:
  - 공백 없는 `gitdir:<path>`
  - `gitdir:` 뒤에 탭
  - 대문자 `Gitdir: `
  - 앞에 공백
  - UTF-8 BOM(git 은 BOM 을 벗기지 않는다)
  - 빈 파일, `gitdir: ` 접두어가 없는 그 밖의 내용
- **끝에서 `\r`·`\n` 만 떼고, 나머지는 전부 경로로 본다.**
  - CRLF, 마지막 줄바꿈 없음, `\r\n` 이 여러 번 붙은 경우는 모두 받아들인다.
  - 콜론 뒤의 두 번째 공백, 줄 끝의 공백·탭, 두 번째 줄은 경로에 포함된다. 그러면 대상이 repo 가 아니게 된다.
  - 경로는 C 문자열로 다뤄져 중간의 NUL 바이트에서 잘린다. `gitdir: <abs>\0junk` 도 유효하다(실측).
  - 접두어 뒤가 비어 있으면 `fatal: no path in gitfile: <경로>` 이다.
- **상대 경로는 `.git` 파일이 있는 디렉토리를 기준으로 푼다.**
- **1 MiB(1048576 바이트)를 넘으면** `too large to be a .git file` 로 거부한다.
- **`.git` 이 gitlink 파일을 가리키는 symlink 여도 따라가서 읽는다.**
- **잘못된 `.git` 파일이 있으면 상위 repo 로 넘어가지 않는다.** 바깥 repo 안에 있어도 그 자리에서 fatal 이다.

그래서 "이 `.git` 파일이 gitlink 인가"를 판정하는 도구는 git 과 같은 접두어 검사(`gitdir: ` 8바이트, 예외 없음)를 써야 한다. 기준이 더 관대하면 git 이 읽지 못하는 파일까지 gitlink 로 판정해 버린다. `skills/wt/heal_submodules.py` 의 `_is_gitlink` 가 이 기준을 쓴다. 가리키는 대상이 유효한지는 일부러 보지 않는다. `heal_submodules.py` 는 대상 module dir 이 손상된 경우를 고치는 도구이기 때문이다([[lesson-gate-safe-side-first]]).

## 대상이 잘못됐을 때의 메시지는 버전마다 다르다

접두어는 맞는데 대상이 repo 가 아닌 경우다(없는 경로이거나 위의 공백 문제).

- **2.53 이하에서 repo 를 탐색하는 경로**는 `fatal: not a git repository: <대상 경로>` 로 대상 경로를 메시지에 담았다(수정 커밋 54a441bcea 메시지 근거, 미실행).
- **2.54.0 에서 repo 를 탐색하는 경로**(`git -C dir`, cwd)는 `fatal: not a git repository: (null)` 을 낸다(✅ 실측). `.git` 파일 경로도 대상 경로도 나오지 않는다.
  - 원인은 커밋 1dd27bfbfd(v2.54.0 에 처음, v2.55.0 에도 포함)가 NULL 을 `%s` 에 넘기게 된 회귀다.
  - 수정 커밋 54a441bcea 의 메시지에 따르면 플랫폼에 따라 "segfault or get garbage like `not a git repository: (null)`" 이다. macOS 는 `(null)` 을 찍었다.
- **`GIT_DIR`·`--git-dir` 로 같은 파일을 지정하면** 다른 코드 경로를 타서 대상 경로가 메시지에 나온다(✅ 실측).
- **수정 상태**: 54a441bcea 는 대상 경로를 빼고 `.git` 파일 경로를 적도록 바꿨다.
  - master 소스의 새 메시지는 `gitfile does not point to a valid repository: <.git 파일 경로>` 다(소스 근거, 미실행).
  - RelNotes 2.56.0(2026-09-28 master 기준, v2.56.0 태그 없음)에 "A regression in the error diagnosis code for invalid .git files has been fixed, avoiding a potential NULL-pointer crash" 로 올라 있고, maint 에도 반영 예정이라고 적혀 있다.
  - v2.55.0 에는 들어가지 않았다. v2.55.0 소스는 아직 옛 문구다.
- 이 메시지를 파싱하는 도구는 버전에 따라 `.git` 파일 경로·대상 경로·`(null)` 중 무엇이 나올지 모른다고 봐야 한다. 대상 판정은 메시지가 아니라 rc 와 형식 규칙으로 한다.

## 연계

submodule 경로를 pathspec 이 아니라 글자 그대로 넘기는 방법은 [[git-literal-pathspecs]] 에 있다. git 동작을 실측해 규칙으로 옮긴 다른 사례는 [[git-autosquash-target-selection]] 에 있다.
