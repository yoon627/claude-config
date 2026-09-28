---
title: link-following-file-ops
category: entity
created: 2026-09-27
updated: 2026-09-27
sources:
  - https://pubs.opengroup.org/onlinepubs/9799919799/functions/unlink.html (EACCES — 경로 검색 권한 또는 "the directory containing the directory entry to be removed" 의 쓰기 권한, 부모 디렉토리의 S_ISVTX)
  - https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap04.html (4.5 Directory Protection — sticky 디렉토리의 삭제 조건, "Optionally, the file is writable by the process" 는 구현 정의)
  - https://pubs.opengroup.org/onlinepubs/9799919799/functions/link.html (link 는 기존 파일에 새 디렉토리 항목을 만든다)
  - https://docs.python.org/3/library/os.html#os.chmod (`follow_symlinks=True` 기본, Linux 는 `follow_symlinks=False` 불가, Windows 는 read-only 플래그만·"The default value of follow_symlinks is False on Windows", 3.13 에서 Windows 의 follow_symlinks 인자 지원)
  - https://docs.python.org/3/library/shutil.html#shutil.rmtree (최상위 path 는 디렉토리 심링크면 안 됨, `onexc` 3.12 추가·`onerror` 3.12 폐기 예정, read-only 제거 예제)
  - https://pubs.opengroup.org/onlinepubs/9799919799/utilities/cd.html (`-L` 은 `..` 를 먼저 처리, `-P` 는 심링크를 먼저 푼다)
  - https://git-scm.com/docs/git-clone (`--local` — 로컬 경로면 기본, `.git/objects/` 파일은 가능하면 hardlink)
  - PR #181 (audit-install-fixes — heal `_force_rmtree`, `install-codex-skill.sh` 의 링크 판정, Red 테스트와 재현)
---

# link-following-file-ops

**트리를 지우거나 링크를 비교하는 코드는 "무엇이 링크를 따라가는가"를 먼저 확인한다.** 링크를 따라가는 연산을 트리 전체에 돌리면 트리 밖 파일이 바뀐다. 링크 경로를 글자로 풀면 실제로는 다른 파일을 가리키는데도 같다고 판정한다.

## 사실
- **POSIX 에서 파일 자신의 모드는 삭제를 막는 조건이 아니다.** `unlink` 의 권한 검사는 경로의 검색 권한과, 지울 항목이 든 부모 디렉토리의 쓰기 권한이다. 부모에 sticky bit(`S_ISVTX`)가 있으면 소유자 조건이 더해지고, "파일이 쓰기 가능하면 허용"은 구현 정의다(XBD 4.5). 그래서 sticky 가 아닌 쓰기 가능 디렉토리 안의 `0o444` 파일은 chmod 없이 지워진다.
- **POSIX 에서 `os.chmod` 는 기본으로 심링크를 따라간다**(`follow_symlinks=True`). 링크 자체의 모드를 바꾸는 `follow_symlinks=False` 는 Linux 에서 쓸 수 없다(`lchmod` 없음). **Windows 는 다르다** — read-only 플래그만 다루고 `follow_symlinks` 기본값이 `False` 다(Windows 의 인자 지원은 3.13).
- **hardlink 는 같은 파일에 대한 또 하나의 디렉토리 항목이다**(`link`). 모드는 항목이 아니라 파일의 속성이라, 트리 안 hardlink 를 chmod 하면 트리 밖 같은 파일의 모드가 바뀐다(PR #181 의 hardlink Red 테스트가 `0o200` 을 관찰). 심링크 검사(`os.path.islink`)로는 걸러지지 않는다.
- **git 은 로컬 경로에서 clone 하면 `.git/objects/` 의 파일을 가능한 한 hardlink 로 만든다**(`--local` 이 기본). 그래서 submodule 의 module dir 이 원본 repo 와 object 파일을 공유할 수 있다.
- **`shutil.rmtree` 의 최상위 path 는 디렉토리 심링크면 안 되고**, 트리 안의 디렉토리 심링크는 따라 내려가지 않는다(PR #181 의 디렉토리 심링크 회귀 테스트 — 밖의 파일 모드 불변). 실패 처리 인자는 3.12 부터 `onexc`(예외 객체를 받음)이고 그 전의 `onerror`(`sys.exc_info()` 튜플)는 3.12 에서 폐기 예정이다. 공식 문서의 read-only 제거 예제는 핸들러에서 `os.chmod(path, stat.S_IWRITE)` 후 재시도한다.
- **셸 `cd` 는 기본(`-L`)으로 `..` 를 먼저 처리한다** — 앞 구성요소를 글자로 지운 뒤 심링크를 푼다. **`cd -P` 는 심링크를 먼저 풀고** 그 실제 디렉토리에서 `..` 를 적용한다. 커널이 경로를 푸는 방식은 `-P` 쪽이다.

## 함정과 올바른 방법
- **삭제 전에 트리 전체를 chmod 하지 않는다.** 이 repo 의 heal(`skills/wt/heal_submodules.py`)은 Windows read-only pack 파일 때문에 모든 플랫폼에서 트리의 모든 파일에 `os.chmod(…, S_IWRITE)` 를 먼저 돌렸다. 재현해 보니 POSIX 에서 트리 안 파일 심링크·hardlink 가 가리키는 밖의 파일이 `0o200`(읽기 불가)이 됐다. 고친 방법은 공식 예제처럼 **삭제가 실패했을 때만 핸들러에서** read-only 를 풀되, **Windows 에서만**, **심링크가 아닐 때만** 하는 것이다(PR #181).
- **남은 한계(Windows)**: 핸들러의 `islink` 검사는 hardlink 를 거르지 못해, 트리 안 hardlink 가 read-only 로 삭제에 실패하면 공유하는 read-only 속성이 풀린다(수정 전과 같은 동작). junction 을 `os.path.islink` 가 링크로 보는지는 확인하지 않았다 ⚠️(3.12 에 `os.path.isjunction` 이 따로 있다). Windows 에서 실행해 보지 않았으므로 추정으로 방어를 더하지 않는다([[lesson-no-speculative-platform-switch]]).
- **이미 있는 링크가 원하는 대상을 가리키는지 비교할 때는 물리 경로로 푼다.** `install-codex-skill.sh` 는 기존 링크의 대상을 `cd <dir> && pwd -P` 로 정규화했다. 그러면 부모가 심링크인 자리의 `../x` 상대 링크가 글자로 풀려 source 와 같다고 판정됐다. 실제로는 다른 파일(decoy)을 가리키는데도 "already" 로 넘어간 것이다. `cd -P` 로 바꿔 커널과 같은 결과를 얻었다(Red 재현 테스트 포함).

## 연계
실행해 볼 수 없는 플랫폼의 스위치는 [[lesson-no-speculative-platform-switch]], 판정 불능 시 기울일 방향은 [[lesson-gate-safe-side-first]].
