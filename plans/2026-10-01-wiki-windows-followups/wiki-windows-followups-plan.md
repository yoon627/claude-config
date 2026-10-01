---
title: wiki-windows-followups — wiki 도구 후속 4건(wiki_search 닫힌 stdout·OSError 문구·check_links 읽기 오류·hook 닫힌 stdout 테스트의 Windows 실행)
status: in_progress
started: 2026-10-01
updated: 2026-10-01
intent: plans/2026-09-29-repo-context-kit/intent.md
---

# Goal
`wiki-tests-windows-fix` # Deferred 의 low 4건을 고친다(`skills/wiki/` — 사용자 지시 "남은거 진행해", 2026-10-01).
1. `wiki_search.py` 가 stdout 을 읽는 쪽이 먼저 닫아도 traceback 없이 exit 2 로 끝나고 stderr 에 이유를 남긴다. 예상 밖 예외도 "결과 없음"(1)이 아니라 2 로 끝난다.
2. OSError 를 싣는 문구(`wiki_check.py` 의 `hook_main`·`Git.run`, `wiki_search.py` 읽기 오류)가 경로를 repr 로 겹치지 않고, git 을 못 띄웠을 때 어느 디렉터리에서였는지 담는다.
3. `check_links.py` 가 읽지 못한 페이지·index·하위 디렉터리에서 traceback 없이 끝난다 — UTF-8 아님은 위반(exit 1), 실제 I/O 실패는 점검 불가(exit 2).
4. Stop hook 의 닫힌 stdout pipe 테스트가 Windows 에서도 돈다.

# Intent
- 묶음: `plans/2026-09-29-repo-context-kit/intent.md` — 같은 묶음의 `wiki-tests-windows-fix` # Deferred 후속. 델타는 아래(묶음 공통 제약은 복제하지 않는다).
- 선행 # Deferred 처분: 런처 Git Bash 실패 → 같은 세션의 별도 단위 `worklog-launcher-no-dirname`(로컬 main 에 머지) · wiki_search 닫힌 stdout·`str(OSError)` 문구·check_links 읽기·StopHookTest skip → 이 plan · DrvFs 대소문자·`open_repo` docstring → `drvfs-case-stale (미착수)`(묶음 `# Plans`) · stdin 3초 한도 → 조치 없음(아래 Out of scope) · 공용 wiki 적립 2건 → main 세션에서 처리됨.
- Problem(2026-10-01 기준선 실측 — Windows 11·CPython 3.13.15, WSL Ubuntu·CPython 3.12.3):
  - `wiki_search.py` 를 읽는 쪽을 닫은 stdout pipe 로 띄우면 결과 있음·결과 없음 경로는 rc 120(Windows `Exception ignored on flushing sys.stdout: OSError [Errno 22]`, POSIX `BrokenPipeError`), 큰 출력(`--open` 58,802 바이트)은 print 안에서 실패해 traceback + rc 1(plan-reviewer 실측) — 1 은 "결과 없음"과 같은 값이다. 예상 밖 예외도 일반 처리기가 없어 rc 1 이다.
  - `Git.run` 이 Popen 실패를 `git 을 실행하지 못했다 — {e}` 로 싣는다. Windows 는 `NotADirectoryError [WinError 267]`·filename=None 이라 어느 디렉터리인지 빠지고(WinError 267·2 로 디렉터리·실행 파일은 갈린다), POSIX 는 `PosixPath('…')` repr 이라 역슬래시가 겹친다. `hook_main` 의 `예상 밖 오류 — {e}` 도 같은 `str(OSError)` 다(코드 확인).
  - `check_links.py` 가 UTF-8 이 아닌 페이지에서 traceback + exit 1 — 위반 exit 1 과 구분되지 않는다(두 플랫폼). 같은 입력을 `wiki_check schema` 는 위반 "UTF-8 아님"(exit 1)으로, 읽기 OSError 는 일반 처리기 exit 2 로 낸다(wiki_check.py:300-307·609-611·1859-1862).
  - `StopHookTest.test_closed_stdout_or_stderr_still_exits_0` 은 sh 리다이렉트 때문에 nt 에서 통째로 skip 이다. 뒤쪽 os.pipe 단계는 플랫폼과 무관하다.
- Constraints:
  - exit code 의 의미는 그대로다 — wiki_search 0 결과·1 결과 없음·2 오류, check_links 0 clean·1 위반·2 점검 불가, hook 은 언제나 0. 바뀌는 것은 crash(traceback)로 끝나던 경로가 그 의미에 맞는 값으로 가는 것뿐이다. 단 check_links 의 2 는 문서상 "pages 디렉터리 없음" 하나였는데 "읽기 실패"가 더해진다(stderr 문구로 구분 — 아래 ⚠️ accepted-risk).
  - 정상 경로의 출력은 바이트 단위로 그대로다.
  - Windows 전용 분기를 새로 넣지 않는다. 닫힌 pipe 의 EINVAL 변환은 이미 있는 `_Stdout` 을 공유한다(공용 wiki `python-windows-closed-pipe-einval` — 변환은 스트림에서, main 은 `BrokenPipeError` 만).
- Out of scope:
  - DrvFs 대소문자·`open_repo` docstring — 같은 함수의 대소문자 처리를 바꾸는 별도 단위(`drvfs-case-stale (미착수)`).
  - Stop hook stdin 3초 한도의 여유 — 이 plan 의 결정으로 조치 없음: 선행 plan 관측 최대 2.5~2.8초·초과 0회, 오늘 부하 중 실패한 timing 테스트는 `scripts/session-fetch.test.js`(이 테스트가 아니다).
  - check_links 의 닫힌 stdout·`find_wiki_root` 의 git 부재(traceback)·locale 디코딩 — 선행 Deferred 에 없던 같은 부류다. # Deferred 에 남긴다.
  - `scripts/session-fetch.test.js` 의 부하 시 간헐 실패 — 묶음 밖(런처 단위 보고에 남김).
- 분할: 없음 — 네 건 사이에 결합은 없다. 분할이 사 주는 단위별 revert·리뷰는 merge commit 으로 보존되는 목적 단위 커밋으로 이미 얻고, consumer 가 보는 변경(check_links)을 마지막 커밋에 두어 거부돼도 interactive rebase 없이 떼어낸다. 분할하면 Windows 최종 검증(약 50분)·plan·code 리뷰가 각 3회 늘어난다.

# Progress
- 2026-10-01: 착수. 네 항목의 기준선을 Windows·WSL 에서 재현(위 Problem). plan 초안 → plan-reviewer CONDITIONAL(강 4·약 11) → 처분 반영(# Review Disposition).
- 2026-10-01: 단위 1 커밋 — Red(Windows·WSL: rc 120·120·1, 예외 전파) → Green(Windows 3.13 `test_wiki_search` 34·`test_wiki_check` 131, Windows 3.9.25 165, WSL 3.12.3 ext4 165 모두 OK), 정상 출력 7경우 base 와 바이트 동일(Windows).

- 2026-10-01: 단위 2·3·4 커밋. 단위 2 — Red(Windows 두 테스트, POSIX 는 기준선 탐침의 `PosixPath(…)`·cwd 없음) → Green(Windows·WSL 66). 단위 3 — 새 메서드가 Windows 에서 skip 없이 통과, `_discard` 를 뺀 변이에서 실패, WSL 두 메서드 통과. 단위 4 — Red(Windows 3·WSL 4) → Green(17), `ReadError` 대신 OSError 를 `main` 이 받게 단순화.

- 2026-10-01: code-review 1차 APPROVE(Minor 7·Nit 7) → fixup c014645(단위 1)·25604cf(단위 4) → 2차 APPROVE(Minor 2·Nit 5) → fixup f4f6742(단위 4)·fe8273f(단위 1). simplify 체크 — 변경 없음(분기·helper 마다 제약 하나). Windows 3.9·3.13·3.14 에서 test_check_links + test_wiki_search 통과, WSL 54 통과, 각 새 테스트가 이전 판이나 변이에서 실패함을 확인.

- 2026-10-01: 로컬 main(`a76a9c9` — 런처 수정) 위로 rebase. 정상 출력 9경우(wiki_search 결과·없음·`--open`·`--links-to`·사용 오류, check_links clean·위반(CRLF·BOM·한글 파일 이름·별칭 안 lone CR), schema clean·위반)가 base 와 바이트 동일 — Windows·WSL. skills/wiki 전체 Windows 3.9.25 188 OK(skip 33)·WSL 3.12.3 ext4 188 OK(skip 2). 최종 검증(격리 runner, 단독 실행) `bash scripts/verify.sh` exit 0 `ALL PASS (skip: install-hooks.test.js(case) record-verified.test.sh)` — skip 은 기존 환경 사유(git 2.30 이하 케이스의 sh shim, jq 없음)로 이 변경 경로가 아니다. evidence gate: Acceptance 1~10 충족 → DONE(status 는 머지 때 done).

# Next
- 사용자 결정 대기: commit-check 재구성(fixup 5개 합치기 + 단위 1·3·4 메시지 갱신) 승인, `/e merge`(push·PR·머지 — 로컬 main 의 미push 2커밋 `2951118`·`a76a9c9` 도 함께 실린다) 여부.

# Decisions
- wiki decision 조회: `wiki-search-design`(exit 0/1/2 계약 — 따른다, exit 2 에 "출력을 끝까지 못 냄"을 더한다), `python-windows-closed-pipe-einval`(변환은 스트림에서·main 은 `BrokenPipeError` 만 — 따른다).
- ⚠️ 네 건은 각각 혼자 머지해도 유효해 dlc 분할 기준을 충족한다 — 분할 규칙(skills/dlc/SKILL.md 분할 판정)과 plan 고정비가 상충 — 한 plan + 목적 단위 커밋을 택했다(근거는 `분할:` 줄). plan-reviewer 동의(조건: check_links 를 마지막 커밋으로).
- 스트림 설정을 `wiki_check.py` 의 공개 함수로 빼 두 스크립트의 `__main__` 이 함께 쓴다(wiki_search 는 이미 wiki_check 을 import 한다). 기각: wiki_search 에 복제 — 같은 함정을 두 곳에서 따로 고치게 된다.
- `wiki_search.main` 은 기존 본문을 `_main` 으로 이름만 바꾸고 얇은 `main(argv, *, env, cwd, home)` 이 본문 전체와 마지막 flush 를 한 try 로 감싼다(wiki_check `main` 과 같은 모양, `sys.stdout is None` 가드). `BrokenPipeError` → `wiki_check._discard(sys.stdout)` + stderr 한 줄 + 2, 그 밖의 `Exception` → traceback + 2. `BrokenPipeError` 가 stdout 의 것이라는 전제는 stderr 가 `_QuietStderr` 라 쓰기 실패를 삼키기 때문에 성립한다. 기각: 마지막 flush 만 감싸기 — 결과 없음(flush 전 return)과 큰 출력(print 안에서 실패)을 놓친다(plan-reviewer 실측).
- 공용 설정 함수의 devnull 대체로, fd 2 가 닫힌 채 뜬 wiki_search 가 `print(file=None)` 으로 오류 문구를 stdout 에 섞던 것도 함께 고쳐진다(plan-reviewer 실측). 별도 테스트는 두지 않는다 — 같은 함수를 wiki_check 의 `2>&-` subTest 가 덮는다.
- OSError 문구는 공용 함수 하나(`filename: strerror`, 둘 중 하나라도 없으면 `str(e)`, filename2 는 다루지 않는다)로 만든다. `Git.run` 은 cwd 를 함께 싣는다(POSIX 의 cwd 부재는 같은 경로가 두 번 나온다 — 단순함을 택한다). 기각: Popen 실패 때 cwd 존재를 판정해 원인을 단정 — 판정 로직이 늘고 WinError 267·2 가 이미 갈라 준다.
- check_links: 읽기를 `read_bytes` 로 하고, UTF-8 이 아니면 replace 로 읽어 링크 판정을 계속하며 위반 `UTF-8 아님: <stem>` 을 더한다(exit 1 — 링크 문법이 ASCII 라 판정은 같다, plan-reviewer 실측). 실제 I/O 실패(OSError — 권한·읽지 못한 하위 디렉터리)는 첫 실패에서 `check_links: 읽기 실패 — <경로>: <이유>` + exit 2(일부만 읽은 판정은 판정이 아니다 — wiki_check·wiki_search 의 OSError → 2 와 같다). 파일이 아닌 `*.md`(디렉터리·깨진 symlink)는 wiki_check `load_pages` 처럼 건너뛴다. 하위 디렉터리는 wiki_search 처럼 `os.walk(onerror=…)` 로 먼저 걸어 rglob 이 삼키지 않게 한다. 출력은 `errors="backslashreplace"` 로 — 새 문구가 surrogate 가 든 경로를 찍다 죽지 않게. check_links 는 wiki_check 을 import 하지 않으므로 문구를 자체로 만든다. 기각: UTF-8 아님까지 exit 2 — wiki_check 의 위반 규약과 반대이고, 2 를 "wiki 없음 → 건너뜀"으로 다루는 consumer 에서 지금 실패하는 입력이 통과로 바뀐다(fail-open).
- ⚠️ check_links 의 OSError 경로가 crash(exit 1)에서 exit 2 로 바뀐다 — consumer 가 2 를 "pages 디렉터리 없음 → 건너뜀"으로 다루면 그 경로만 fail-open 이 될 수 있다(consumer 처리 ❌ 확인 불가) — 권한·하위 디렉터리 읽기 실패라는 드문 경로이고 wiki_check·wiki_search 와 같은 값이라 accepted-risk, 보고에 명시한다.
- check_links 의 페이지 필터를 `is_dir()` + `FileNotFoundError` 에서 `_stat_is(path, stat.S_ISREG)` 로 변경(이유: code-review 2차 M1 — 1차 반영이 "일반 파일만" 을 "디렉터리·ENOENT 제외" 로 좁혀 symlink 루프는 rc 2, FIFO 는 open 에서 멈춤(WSL 실측 timeout), 장치 파일은 끝없이 읽게 됐다). `_stat_is` 는 3.13 까지의 `is_file()`/`is_dir()` 처럼 ENOENT·ENOTDIR·EBADF·ELOOP·winerror 21/123/1921(pathlib 의 목록 — Windows 의 깨진 symlink 는 ENOENT, 도는 symlink 는 winerror 1921 실측)만 False 로 보고 권한 같은 그 밖의 OSError 는 올린다. index 와 `pages` 판정에도 같은 함수를 쓴다(2차 Nit3). 기각: `is_file()` 로 되돌리고 3.14 문제는 wiki_check 와 함께 미루기 — 이번 단위가 약속하는 "읽기 실패 → 2" 가 3.14 에서 조용히 깨진다.
- code-review 1차 반영(2026-10-01): wiki_search 의 예상 밖 예외 분기는 traceback 뒤 stdout flush 를 다시 시도하고 실패하면 `_discard` 한다 — EPIPE 가 아닌 쓰기 실패(ENOSPC·EBADF)가 종료 때 flush 를 다시 실패해 120 이 되던 것. check_links 는 `is_file()` 대신 `is_dir()` 로 거르고 `FileNotFoundError`(깨진 symlink)만 건너뛴다 — Python 3.14 의 `is_file()`/`is_dir()` 은 `os.path.isfile`/`isdir` 라 권한 오류를 False 로 삼킨다(3.14.7 `inspect.getsource` 확인), 읽기에서 드러나게 한다. read() 단계의 OSError 는 경로를 싣지 않아 `read_text` 가 붙이고, 줄바꿈은 텍스트 모드처럼 맞춘다(base 의 `read_text` 와 같은 판정 — 별칭 안의 lone CR). `pages` 의 `is_dir()` 도 같은 `except OSError` 안에 둔다. 기각: 테스트의 crash 판별을 각 exit 2 테스트에 사유 단언으로 흩기 — `run_main` 한 곳에서 traceback 을 거부하는 쪽이 새 테스트까지 덮는다.
- 같은 파일을 고치는 단위(1·2 — wiki_check.py·wiki_search.py, 2·4 — test_wiki_check.py)는 구현·검증·커밋을 끝내고 다음으로 간다. 단위 1 은 커밋 전에 Windows 에서 `SchemaTest.test_closed_stdout_exits_2_without_traceback`·`StopHookTest` 전체·새 wiki_search 테스트를 돌린다 — hook 은 언제나 exit 0 이라 스트림 설정 이동이 깨져도 조용하고, `_Stdout` 설치가 빠지는 회귀는 ubuntu CI 가 못 잡는다.
- 커밋 단위(순서대로): 1) `fix(wiki): end wiki_search with exit 2 when its stdout is closed` — wiki_check.py(스트림 설정 함수), wiki_search.py(`__main__`·얇은 `main`·docstring), test_wiki_search.py, SKILL.md(query exit 2 목록), README.md:361 2) `fix(wiki): name the path and the git cwd in OSError messages` — wiki_check.py(공용 함수·`hook_main`·`Git.run`), wiki_search.py(읽기 오류), test_wiki_check.py 3) `test(wiki): run the closed-stdout-pipe Stop hook case on Windows too` — test_wiki_check.py 4) `fix(wiki): report unreadable pages in check_links without a traceback` — check_links.py(+docstring), test_check_links.py, SKILL.md(lint 의 check_links 줄).

# Acceptance
1. wiki_search 닫힌 stdout: `test_wiki_search.py` 의 새 subprocess 테스트(한 메서드, subTest 3개 — 결과 있음·결과 없음·큰 출력 `--open`) — 모두 exit 2, stderr 에 `Traceback`·`Exception ignored` 없음·이유 한 줄 있음. 구현 전 Red(Windows·WSL — 실측 rc 120·120·1).
2. wiki_search 예상 밖 예외: 새 프로세스 안 테스트가 본문이 `RuntimeError` 를 던질 때 `main` 이 2 를 돌려주고 stderr 에 traceback 이 있는지 본다. 구현 전 Red(예외가 그대로 나온다).
3. hook 의 예상 밖 OSError: 새 테스트가 `run_stop_hook` 이 `FileNotFoundError(2, …, <역슬래시 든 경로>)` 를 던질 때 stdout JSON 의 `systemMessage` 가 `예상 밖 오류 — FileNotFoundError: <경로>: <strerror>`(역슬래시 하나)인지 본다. 구현 전 Red.
4. `Git.run`: 새 테스트(GitAdapterTest)가 없는 cwd(POSIX 는 이름에 `\`)로 git 을 띄울 때 `GitError` 문구에 `(cwd <cwd>)` 가 있고 겹친 역슬래시가 없는지 본다. 구현 전 Red(두 플랫폼).
5. wiki_search 읽기 오류 문구는 공용 함수를 쓰고 기존 `test_unreadable_index_exit_2` 가 그대로 통과한다.
6. Windows: 닫힌 stdout pipe 의 Stop hook 단계가 skip 없이 돌고 통과한다(sh 쪽은 `skipIf(nt)` 유지). 변이 — `hook_main` 의 `_discard` 를 빼면 Windows 에서 그 테스트가 실패한다.
7. check_links(프로세스 안 `main` + stderr 캡처, 인접 파일처럼 동작마다 메서드 하나): UTF-8 아닌 페이지·index → exit 1·위반 `UTF-8 아님`·다른 판정은 그대로 · 읽기 OSError(패치 — filename 있음·없음 subTest) → exit 2·`check_links: 읽기 실패 — <경로>:`·traceback 없음 · 일반 파일이 아닌 `*.md`(디렉터리·깨진/도는 symlink·FIFO) → 건너뜀 · 페이지 stat 의 권한 오류(`Path.stat` 패치) → exit 2 · 별칭 안 lone CR → 링크 아님(텍스트 모드와 같음) · 읽지 못한 하위 디렉터리 → exit 2(POSIX 전용, nt·root skip — wiki_search 의 같은 테스트 방식). 구현 전 Red(권한 오류 테스트는 3.14 에서만 이전 판이 실패한다).
8. 정상 출력 불변: 대표 명령(wiki_search 결과 있음·없음·`--open`·`--links-to`, check_links clean·위반, wiki_check schema)의 stdout·stderr·exit code 가 base 사본과 바이트 단위로 같다(Windows·WSL).
9. 회귀: `skills/wiki` 테스트 전체가 Windows(3.13·3.9)·WSL(3.12)에서 통과. 최종 검증은 로컬 main(런처 수정 `a76a9c9` 포함) 위로 rebase 한 뒤 `bash scripts/verify.sh` 가 Windows 에서 `ALL PASS`(skip 은 목록 그대로 보고) — 리뷰어 실행과 겹치지 않게 돌리고, 간헐 실패가 나면 재실행으로 덮지 않고 단언 원문·실측값을 남긴다.
10. 문서: SKILL.md 의 wiki_search exit 2 목록("stdout 을 읽는 쪽이 먼저 닫아 출력을 끝까지 내지 못했다")·check_links 설명, README.md:361 의 wiki_search exit code, wiki_search.py·check_links.py docstring 을 같은 브랜치에서 갱신. README 트리(685-690)는 exit code 서술이 없어 그대로(확인함). `docs/dlc-details.md:22` 는 "그 밖의 이유"가 포괄해 그대로. 공용 wiki `wiki-search-design` 의 exit code 목록은 main 세션 적립으로 # Deferred.

# Key Files
- `skills/wiki/wiki_check.py` — 스트림 설정 공개 함수, `hook_main`, `Git.run`, OSError 문구 함수
- `skills/wiki/wiki_search.py` — `__main__`, 얇은 `main`/`_main`, 읽기 오류 문구, docstring exit code
- `skills/wiki/check_links.py` — 읽기·디코딩·하위 디렉터리 오류, 출력 errors, docstring exit code
- `skills/wiki/test_wiki_search.py`·`test_wiki_check.py`·`test_check_links.py`
- `skills/wiki/SKILL.md` — query exit 2 목록, lint 의 check_links 줄
- `README.md:361` — wiki_search exit code
- `plans/2026-09-29-repo-context-kit/intent.md` — `# Plans` 에 이 plan 줄과 `drvfs-case-stale (미착수)`

# Review Disposition
- [plan] ⚠️ 분할 — resolved(plan-reviewer 동의, check_links 를 마지막 커밋으로, `분할:` 줄을 사실로)
- [plan] 강1 check_links UTF-8 → exit 2 가 wiki_check 규약과 반대 — fix(UTF-8 아님 = 위반 exit 1, OSError 만 exit 2, 파일 아님 건너뜀 — Decisions)
- [plan] 강2 wiki_search try 범위 미정·Acceptance 1 이 틀린 구현을 통과 — fix(얇은 `main` 이 본문 전체 + flush, subTest 3개)
- [plan] 강3 Windows ALL PASS 가 base 의 런처 실패로 관찰 불가 — fix(로컬 main 위로 rebase 후 최종 검증, 간헐 실패는 원문 기록)
- [plan] 강4 README:361·docstring 2곳 동기화 누락 — fix(Acceptance 10, 단위 1·4)
- [plan] 약1 분할 규칙 이탈 3회째 — fix(# Workflow Findings 기록, 규칙 보완은 제안만)
- [plan] 약2 가장 위험한 단계·정상 출력 불변의 증거 — fix(단위 1 커밋 전 Windows hook 테스트, Acceptance 8)
- [plan] 약3 wiki_search 예상 밖 예외가 exit 1 — fix(얇은 `main` 의 `Exception` → 2, Acceptance 2)
- [plan] 약4 `_QuietStderr` 전제·fd 2 닫힘 — fix(Decisions 에 전제 기록, 별도 테스트는 두지 않음 — wiki_check 의 `2>&-` subTest 가 같은 함수를 덮는다)
- [plan] 약5 기각한 대안 기록 없음 — fix(Decisions 에 4건)
- [plan] 약6 rglob 의 하위 디렉터리 — fix(범위에 넣음, `os.walk(onerror=…)`)
- [plan] 약7 범위 근거(3초 한도 출처·DrvFs 처분·Constraints 복제) — fix(Intent 처분 목록·`(미착수)` 줄·복제 제거)
- [plan] 약8 커밋 경계 — fix(얇은 wrapper, 같은 파일 단위는 끝내고 다음, 순서 1·2·4·3)
- [plan] 약9 check_links 같은 부류 — fix(Goal 3 의 index·하위 디렉터리·여러 파일 정책·파일 아님·출력 errors) / defer(닫힌 stdout·git 부재·locale — # Deferred)
- [plan] 약10 테스트 위치·크기 — fix(제안 위치대로)
- [plan] 약11 닫힌 stdout 의 exit 2 가 stderr 비어 있음 — fix(stderr 한 줄)
- [plan] nit WinError 과장·OSError 함수 getattr·filename2·check_links 자체 문구·private `_discard`·문서 문구 정확도 — fix(문구), wontfix(`_discard` 외부 사용 — 같은 도구 묶음이고 wiki_search 는 이미 wiki_check 내부 구조에 기댄다)
- [code] APPROVE(Critical·Major 0). M1 새 `except Exception → 2` 가 기존 exit 2 단언의 crash 판별을 없앤다 — fix(`run_main` 이 traceback 을 거부, `crash=True` 만 예외) · M2 EPIPE 아닌 stdout 쓰기 실패가 rc 120 — fix(flush 재시도 → 실패 시 `_discard`, 읽기 전용 stdout 테스트 — Red Windows·WSL rc 120) · M3 check_links filename 없는 OSError 의 `None:` — fix(`read_text` 가 경로를 붙임, EIO subTest — Red WSL) · M4 Python 3.14 `is_file()` 이 권한 오류를 삼킴 — fix(`is_dir()` + `FileNotFoundError` 만 건너뜀, 0o644 subTest) · M5 `pages` `is_dir()` 의 PermissionError traceback — fix(같은 try) · M6 check_links exit 2 의미 확장이 묶음 기록에 "그대로" — fix(Constraints·intent 줄에 명시) · M7 Acceptance 7 문구·Acceptance 8 증거 — fix(문구), Acceptance 8 은 rebase 뒤 두 플랫폼에서 실행
- [code] Nit1 lone CR 판정 변화 — fix(줄바꿈 정규화) · Nit2 닫힌 stdout 의 `--help` 120 — wontfix(질의가 아니고 base 와 같다, 문서는 질의 경로를 말한다) · Nit3 6311484 메시지의 "EINVAL 변환을 지키는 테스트" — fix(commit-check reword — 지키는 것은 `_discard`, 변환은 wiki_search·SchemaTest 테스트가 덮는다) · Nit4 예상 밖 예외 테스트의 traceback 단언 — fix · Nit5 "(schema 와 같은 값)" — fix(SKILL.md "페이지는", 587f281 메시지는 reword) · Nit6 dlc-details 괄호 — wontfix(Acceptance 10 결정 유지) · Nit7 check_links 의 index.md 디렉터리 → "index 누락" — defer
- [code-2] fixup c014645·25604cf 재리뷰 APPROVE(Critical·Major 0). M1 1차 반영이 일반 파일이 아닌 `*.md`(symlink 루프·FIFO·장치)를 읽게 됨 — fix(`_stat_is`, Decisions; 25604cf 판은 Windows 루프 rc 2·WSL FIFO 에서 멈춤) · M2 정규화·깨진 symlink 건너뛰기를 고정하는 테스트 없음 — fix(lone CR 테스트 — 정규화를 뺀 변이·587f281 에서 실패, 일반 파일 아닌 항목 테스트 — 디렉터리·깨진/도는 symlink·FIFO) · Nit3 3.14 의 index `is_file()`·pages `is_dir()` — fix(같은 `_stat_is`) · Nit4 `detail` 규칙이 `describe_oserror` 와 다름 — fix(같은 규칙) · Nit5 lone CR 은 base 와 같고 wiki_search 와 다름 — wontfix(Constraints 의 출력 불변을 따른다, read_text docstring 에 적음) · Nit6 읽기 전용 stdout 테스트가 분기를 고정하지 않음 — fix(`Traceback` 단언) · Nit7 0o644 subTest 의 Red 미관찰 — fix(그 subTest 를 빼고 `Path.stat` 패치 테스트로 바꿈: Windows 3.14 에서 587f281·25604cf 판 모두 실패, 3.13·3.9 는 전후 통과 — `os.stat` 패치는 3.9 pathlib 이 import 때 잡은 함수를 써 보이지 않는다). fix loop 2회 상한 도달.

# Workflow Findings
- dlc 분할 판정에 plan 고정비 예외가 없어, 결합 없는 소규모 후속을 한 plan + 목적 단위 커밋으로 묶을 때마다 규칙에서 이탈한다 — 3회째(worklog-followups, wiki-tests-windows-fix, 이 plan; plan-reviewer 15항은 "고정비 N배 대비 이득"을 이미 본다). 규칙 보완(예: "결합 없음이어도 이득이 커밋 단위로 얻어지면 한 plan 허용 + 근거 한 줄")을 별도 작업으로 제안한다 — 적용은 승인 후(§1).

# Deferred
- [low] check_links 닫힌 stdout 처리 없음 — `print` 가 닫힌 pipe 에서 traceback·rc 120 류(wiki_search 와 같은 부류, 이번 plan 은 읽기 쪽만).
- [low] check_links `find_wiki_root` 의 `git rev-parse` — git 이 없으면 traceback + exit 1, `text=True` 라 locale(Windows 한국어면 cp949)로 디코딩.
- [low] wiki_check `main` 의 예상 밖 예외 분기도 EPIPE 아닌 stdout 쓰기 실패에서 종료 flush 가 다시 실패해 rc 120 이다(wiki_search 는 이번에 고침, code-review M2).
- [low] wiki_check `load_pages`·`read_texts`(wiki_search 가 씀)의 `is_file()` 필터 — Python 3.14 에서 권한 오류를 삼켜 페이지가 조용히 빠진다(check_links 는 이번에 고침, code-review M4).
- [low] check_links 는 index.md 가 디렉터리면 없는 것으로 보고 "index 누락"(exit 1)을 낸다 — wiki_search 는 같은 입력에 exit 2(기존 동작, code-review Nit7).
- [wiki] `~/.claude main 세션에서 /wiki ingest` — 공용 `wiki-search-design` 의 exit code 2 목록에 "stdout 을 읽는 쪽이 먼저 닫아 출력을 끝까지 내지 못함(stderr 한 줄)"과 예상 밖 예외를 더한다 · check_links 의 UTF-8 아님 = 위반, I/O 실패 = 2 · 출처: 공개(이 repo).

# Blockers
