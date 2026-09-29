---
title: git-literal-pathspecs
category: entity
created: 2026-09-28
updated: 2026-09-28
sources:
  - git 2.54.0 (Apple Git-157) 실측 — scratch repo 재현 후, 조건을 바꿔 반례를 찾는 재실행 (2026-09-28)
  - git v2.54.0 pathspec.c `get_global_magic`·`unsupported_magic`, builtin/check-ignore.c, builtin/submodule--helper.c `module_list_compute`·`die_on_index_match`·`deinit_submodule`
  - https://git-scm.com/docs/git (`--literal-pathspecs`, `GIT_*_PATHSPECS`) · https://git-scm.com/docs/git-submodule · https://git-scm.com/docs/gitglossary (pathspec) · https://git-scm.com/docs/git-check-ignore
  - PR #188 (skills/wt/heal_submodules.py: deinit 에 `--literal-pathspecs` 추가, `GIT_*_PATHSPECS` 4개 제거)
---

# git-literal-pathspecs

스크립트가 경로를 git 에 글자 그대로 넘기려 할 때의 함정이다(git 2.54 실측).
- git 의 경로 인자는 대부분 pathspec 이라 `*` 가 glob 으로 풀린다.
- glob 을 끄는 전역 설정(`--literal-pathspecs`·`GIT_LITERAL_PATHSPECS`)을 `GIT_GLOB_PATHSPECS`·`GIT_ICASE_PATHSPECS` 와 함께 켜면 fatal 이다. `GIT_NOGLOB_PATHSPECS` 와는 함께 쓸 수 있다.
- `git check-ignore` 는 이 설정을 포함한 pathspec magic 을 거부한다(`top` 제외).

## `git submodule` 의 경로 인자는 pathspec 이다 (✅)

- `git submodule deinit -f -- 'sub*'` 는 `subA` 와 `subB` 를 **둘 다** 해제한다(rc 0). `--` 를 빼도 같다.
- `git submodule update --init -- 'sub*'` 도 둘 다 초기화한다.
- `subA` 가 이미 있는 repo 에서 `git submodule add <url> 'sub*'` 는 `fatal: 'sub*' already exists in the index`(128)로 실패한다. 새 경로 인자가 기존 `subA` 에 매칭되기 때문이다.
- git-submodule 문서는 `<path>` 를 "Paths to submodule(s)" 라고만 적고 pathspec 이라고 하지 않는다.
  - 소스를 보면 deinit·update·status 등은 `module_list_compute()`(`parse_pathspec` + `match_pathspec`)로 대상을 고른다.
  - add 는 그 함수를 거치지 않고 `die_on_index_match()` 에서 따로 경로를 pathspec 으로 파싱해 index 와 대조한다.
  - 실제로 실행해 본 하위 명령은 deinit·update --init·add·status 넷이다.
- `.gitmodules` 의 path 값은 repo 가 정한다. 그 값을 그대로 넘기는 도구는 다른 submodule 까지 건드릴 수 있다. 그래서 이 repo 의 `skills/wt/heal_submodules.py` 는 `git --literal-pathspecs submodule deinit -f -- <path>` 로 부른다.
- 이름을 정규식으로 해석하면 자기 자신과 매칭되지 않는 submodule(실측한 것은 이름 `sub*` 뿐)은 deinit 이 문제를 일으킨다.
  - `Cleared directory` 를 출력하고도 `.git/config` 의 `submodule.sub*.url` 을 지우지 않는다.
  - 원인: 소스의 `deinit_submodule` 이 이름을 그대로 `git config --get-regexp "submodule.<name>\."` 에 넣는다.
  - ⚠️ `*` 만 실측했고, deinit 인자를 네 가지로 바꿔도 결과가 같았다.

## `--literal-pathspecs` 가 하는 것과 안 하는 것 (✅)

- **glob 과 magic 접두어 해석을 끈다.** git(1) 문서의 표현은 "no globbing, no pathspec magic" 이다.
  - `git --literal-pathspecs submodule deinit -f -- 'sub*'` 는 `error: pathspec 'sub*' did not match any file(s) known to git`(rc 1)로 끝나고 아무것도 바꾸지 않는다.
- **submodule 하위 명령은 인자 하나라도 매칭이 없으면 아무것도 하지 않고 끝난다(deinit 실측).** `-- subA 'sub*'` 를 주면 `subA` 도 그대로 남는다.
- **앞 디렉토리 매칭은 남는다.** `-- dir` 은 `dir/` 아래 submodule 을 모두 고른다. submodule 경로를 정확히 줄 때만 그 하나만 고른다.
- 환경변수 `GIT_LITERAL_PATHSPECS=1` 은 플래그와 같다.
- 인자 하나만 글자 그대로 쓰려면 `:(literal)sub*` 이나 `sub\*` 로 쓴다.
- 전역 literal 을 켜면 magic 접두어도 해석하지 않는다. `':(glob)a*b'` 가 그 이름을 가진 파일에 매칭된다.

## 전역 설정끼리의 충돌 (✅)

| 조합 (플래그든 env 든) | 결과 |
|---|---|
| literal + `GIT_GLOB_PATHSPECS` | `fatal: global 'literal' pathspec setting is incompatible with all other global pathspec settings` (128) |
| literal + `GIT_ICASE_PATHSPECS` | 같음 |
| literal + `GIT_NOGLOB_PATHSPECS` | 허용된다. noglob 은 충돌 판정이 끝난 뒤에 literal 을 더하기 때문이다 |
| glob + noglob | `fatal: global 'glob' and 'noglob' pathspec settings are incompatible` (128) |

- **충돌은 pathspec 인자가 있을 때만 드러난다.**
  - `status`·`log`·`add -A`·`commit` 을 인자 없이 부르면 충돌하는 env 가 있어도 rc 0 이다.
  - 명시한 `.` 은 인자로 친다.
  - 그래서 테스트가 인자 없는 호출만 돌리면 충돌을 보지 못한다.
- env 값은 boolean 으로 읽는다. `=0` 은 꺼짐이고 `true`·`yes` 는 켜짐이다.
- 전역 설정 충돌은 git(1) 문서에 없다. gitglossary 에는 요소 단위 magic 의 "Glob magic is incompatible with literal magic" 한 문장만 있다(`':(literal,glob)x'` → fatal).
- 따라서 literal 을 켜는 래퍼는 사용자 환경의 `GIT_GLOB_PATHSPECS`·`GIT_ICASE_PATHSPECS` 를 먼저 지워야 한다.
  - `heal_submodules.py` 는 `GIT_LITERAL/GLOB/NOGLOB/ICASE_PATHSPECS` 네 변수를 모두 지운다.
  - 이 repo 의 pre-push 가드도 같은 네 변수를 unset 한다. 가드는 `plans/*.md` 의 glob 매칭이 바뀌지 않게 하려는 목적이다([[git-log-added-lines-hardening]]).

## `git check-ignore` 는 pathspec magic 을 거부한다 (✅)

- `top` 을 뺀 모든 magic 을 거부한다. 전역(플래그·env 의 literal·noglob·glob·icase)이든 요소 단위든 결과는 `fatal: <path>: pathspec magic not supported by this command: '<magic>'`(128)다.
  - `<magic>` 자리에는 거부된 magic 이름(`literal`·`glob`·`icase`)이 들어간다. noglob 은 내부적으로 literal 이라 `'literal'` 로 나온다.
  - 요소 단위일 때 `<path>` 에는 `:(literal)a*b` 처럼 접두어까지 찍힌다.
- check-ignore 는 인자를 glob 으로 풀지 않는다. `*` 가 든 경로도 그대로 넘기면 된다.
- literal 을 전역으로 켜는 래퍼는 check-ignore 를 부를 때 env 를 지우거나 `GIT_LITERAL_PATHSPECS=0` 으로 덮어써야 한다. 플래그만 빼면 env 가 남는다.
- 이와 별개로, `check-ignore --stdin` 에 빈 줄이 오면 환경과 상관없이 `fatal: empty string is not a valid pathspec`(128)이다.

## 연계

`.git` 파일(gitlink)이 유효한지 판정하는 규칙은 [[git-gitfile-format]] 에 있다. `skills/wt/heal_submodules.py` 처럼 복구 동작을 할지 판정하는 조건을 고칠 때 먼저 정하는 안전측 원칙은 [[lesson-gate-safe-side-first]] 에 있다.
