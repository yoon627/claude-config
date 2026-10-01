---
title: wiki-tests-windows-fix — Windows 에서 실패하는 wiki 테스트 5건의 원인을 고쳐 wiki_check·wiki_search 테스트가 Windows 에서 통과한다
status: in_progress
started: 2026-10-01
updated: 2026-10-01
intent: plans/2026-09-29-repo-context-kit/intent.md
---

# Goal
Windows(이 머신 — Windows 11, Python 3.13.15)에서 `skills/wiki/test_wiki_check.py`·`test_wiki_search.py` 가 실패 0 으로 통과한다. 테스트를 약화하지 않고 원인을 고치며, POSIX(WSL Ubuntu, Python 3.12.3)의 판정·exit code·stdout 은 바뀌지 않는다.

# Intent
- 묶음: `plans/2026-09-29-repo-context-kit/intent.md` — 묶음이 만든 도구(wiki_check·wiki_search)의 Windows 결함 수정이다. 아래는 이 plan 의 델타다(공통 제약 — stdlib 만·`uv run`·hook fail-open·실행해 보지 못한 플랫폼에 추정 스위치 금지 — 은 묶음 Constraints 가 정본).
- Problem: Windows 에서 python 축의 wiki 테스트 5건이 실패한다(2026-10-01 재현, base `origin/main@c9eb5d5`). CI 는 ubuntu 뿐이라 드러나지 않았다. 원인은 원인 조사 workflow(원인별 실험 + 반증 agent, 9개 — 아래 Progress)로 확정했다.
  1. `SchemaTest.test_closed_stdout_exits_2_without_traceback` — exit 120 과 traceback. 읽는 쪽이 닫은 pipe 에 쓰면 Windows CRT 가 `ERROR_NO_DATA` 를 errno 로 옮기지 못해 `BrokenPipeError` 가 아니라 `OSError(EINVAL)` 이 난다(✅ 실측, CPython gh-79935 open, `subprocess._stdin_write` 도 같은 뜻으로 본다). `main()` 은 `BrokenPipeError` 만 "판정 불가(exit 2) + stdout devnull" 로 보내므로, EINVAL 은 `except Exception` 으로 가 traceback 을 찍고 stdout 을 그대로 둬 종료 flush 가 다시 실패한다(exit 120). 출력이 버퍼보다 크면 `print` 안에서 실패해 exit 2 + traceback 이다. hook 경로는 이미 막혀 있다(exit 0).
  2. `StaleBranchTest.test_case_mismatched_wiki_argument_is_refused` — exit 0(기대 2). Windows 의 `Path.resolve()`(`_getfinalpathname`)는 디스크의 대소문자로 되돌려 `Wiki` 가 `wiki` 가 되고, git `--show-prefix` 와 같아 거부하지 않는다(✅ 3.13·3.9 실측, realpath 공식 문서). 판정은 올바른 표기와 같다 — `--branch`·`--report`(같은 지문)는 바이트 단위로 같았다(✅, clean·stale·작업 트리 변경, 소문자 드라이브·루트 대소문자 변형 포함). `--stop-hook` 은 조사 agent 가 같다고 했으나 반증 agent 는 앞 150자만 비교했다(⚠️). 테스트의 "대소문자 무시 FS 면 거부" 는 resolve 가 표기를 그대로 두는 플랫폼(macOS 로 본다 ⚠️)의 가정이다. 제품 결함이 아니다.
  3. `StopHookTest.test_oversized_stdin_gives_system_message` — `systemMessage` 없음.
  4. `StopHookTest.test_stdin_without_eof_ends_within_3_seconds` — 3초 안에 끝나지 않는다.
     - 3·4 공통: `read_stdin` 의 Windows 분기가 `sys.stdin.buffer.read()` 한 번이라 `STDIN_WAIT`·`STDIN_MAX` 를 둘 다 적용하지 않는다(✅). 선행 plan 이 Windows 에서 실행할 수 없어 "(미검증)" 으로 남긴 분기다.
  5. `ExitCodeTest.test_unreadable_index_exit_2`(wiki_search) — `str(OSError)` 는 경로를 `repr` 로 붙여 Windows 경로의 역슬래시가 겹친다(✅). POSIX 경로엔 역슬래시가 없어 통과했다.
- Constraints:
  - 테스트 약화 금지(CLAUDE.md §7). 기대값을 바꾸는 것은 그 기대가 플랫폼 사실과 어긋날 때만이고, 근거를 Decisions 에 남긴다(2번만 해당).
  - POSIX 의 판정·exit code·stdout 불변 — `select` 경로, `BrokenPipeError` 처리, 대소문자만 다른 인자 거부. stderr 안내 문구는 wiki_search 읽기 실패 한 곳만 바뀐다(Decisions ⚠️).
  - Python 3.9 호환(SKILL.md "Python" 절).
  - Stop hook 계약을 Windows 에서도 지킨다 — 언제나 exit 0, stdin 은 `STDIN_WAIT`(1초) 안에 EOF, `STDIN_MAX` 초과는 `systemMessage`.
  - 테스트는 실패할 때 멈추지 않고 실패해야 한다 — verify.sh·CI lint job 에는 시한이 없다(`lint.yml` 의 lint job 은 `timeout-minutes` 없음, 기본 360분).
- Out of scope:
  - 이 5건 밖의 Windows skip 테스트(symlink·pty·실행 비트 등) — 플랫폼 기능이 없어 skip 이 맞다.
  - verify.sh 다른 파일·축의 Windows 실패 — 요청은 wiki 테스트 5건이다. 기준선에서 같은 실패로 입증된 것만 Deferred 에 남긴다.
  - 조사·리뷰에서 찾은 같은 계열의 다른 결함(Linux 대소문자 무시 FS 의 거짓 stale, 다른 `str(OSError)` 문구, wiki_search 의 닫힌 stdout 등) — 실패하는 테스트가 없어 고치지 않고 Deferred 에 남긴다(CLAUDE.md §3-4).
- 분할: 없음 — 네 원인(stdout EINVAL·stdin 읽기·대소문자 테스트·wiki_search 문구)은 서로 독립이라 따로 머지해도 모순은 없다(결합 없음). 나누지 않는 이유는 고정비다 — 단위마다 140줄 안팎의 작은 수정이고 Windows 검증 환경 하나를 공유해, plan 4개의 worktree·리뷰·머지 대신 한 plan 에서 목적 단위 커밋으로 나눈다(아래 ⚠️).

# Acceptance
1. Windows 3.13: `python skills/wiki/test_wiki_check.py` — failures·errors 0, skip 은 기준선과 같은 14건(worktree 기준 — main checkout 은 공용 wiki `WIKI.md` 가 있어 L540 이 돌아 13건). 실행 수는 126 + 새 테스트 수.
2. Windows 3.13: `python skills/wiki/test_wiki_search.py` — Ran 32, OK(skipped=1).
3. Windows 3.9.25(uv 가 받은 인터프리터): 두 파일 failures·errors 0.
4. POSIX(WSL Ubuntu 3.12.3, ext4 사본): `test_wiki_check.py` OK(skipped=2 — 기준선과 같은 두 테스트, 대소문자 테스트는 이름이 바뀐다), `test_wiki_search.py` 32 OK, `test_check_links.py` 13 OK.
5. Windows Stop hook 실측(실제 CLI): EOF 없는 stdin 30회 → 모두 exit 0·`systemMessage`("1초")·stderr 빈 값·최대 경과 < 3초. 이 가운데 일부는 SKILL.md 가 적은 `uv run --no-project python …` 경로로 돈다. Node 부모(`child_process.spawn`, libuv pipe)가 JSON 을 쓰고 end → 정상 판정, end 하지 않음 → timeout `systemMessage`. 모두 "Fatal Python error" 없음.
6. Windows 닫힌 stdout(실제 CLI): `schema` 작은 출력(종료 flush 에서 실패)·큰 출력(`print` 안에서 실패) 둘 다 exit 2·stderr 에 traceback 없음. `stale --stop-hook` 은 exit 0.
7. 정상 출력이 base 와 바이트 단위로 같다 — 최종 구현으로 `schema`(위반 있음, 한글 경로 포함)·`stale --branch` 의 stdout·exit code 를 base 사본과 비교, Windows·POSIX 둘 다.
8. wiki_search 읽기 실패 문구가 OS 표기 경로를 그대로 담는다 — Windows 는 역슬래시 하나, POSIX 는 `<경로>: Is a directory`. 경로에 `\` 가 든 fixture 로 POSIX 에서도 base 가 Red 다.
9. 새 단위 테스트 `ThreadStdinTest` 가 base 에서 Red(헬퍼 없음), 구현 뒤 Windows·POSIX 에서 Green. 변이 — 시한 없는 대기·크기 검사 없음·예외 삼킴·`daemon=False` — 에서 각각 10초 안에 실패하고 멈추지 않는다. `StdoutTest` 는 변환 제거·조건 뒤집기 변이에서 Windows·POSIX 둘 다 실패한다.
10. 대소문자 테스트 변이(Windows): resolve 를 우회하고 prefix 대조를 끄면(거짓 stale) 실패, resolve 만 우회하면(거부) 통과.
11. Windows 콘솔: 숨긴 새 콘솔에서 `schema` 를 돌려 stdout 이 콘솔 장치(`_WindowsConsoleIO`)일 때도 rewrap 이 예외 없이 exit code 를 낸다(화면 표시는 보지 않는다 — 결과에 따라 SKILL.md 서술을 정한다).
12. 문서: SKILL.md "Python" 절의 "Windows 실행은 검증하지 않았다" 를 실제 확인 범위(OS·Python 판·연결 방식·미확인 부분)로 고친다. README 는 wiki_check 의 Windows 서술이 없어 바꾸지 않는다(확인함). 묶음 intent 의 "(Windows) 실행해 볼 수 없는 플랫폼" 전제를 고치고 `# Plans` 에 이 plan 을 더한다.
13. `bash scripts/verify.sh` 전체(Windows) — wiki 테스트 3파일 ok. 다른 실패는 base `c9eb5d5` 에서 같은 실패로 입증된 것만(python 축 기준선은 wiki 2파일 말고 전부 ok 였다).

# Progress
- 2026-10-01 착수. 5건 재현(Windows), 열린 PR·`in_progress` plan 없음 확인. worktree `wiki-tests-windows-fix`(base `origin/main@c9eb5d5`). Explore: 실패 테스트 5개와 `read_stdin`·`main`·`open_repo`·`hook_main`·`_discard`·`_QuietStderr`·wiki_search `main` 을 읽어 원인 후보를 잡았다. Windows python 축 기준선을 base 그대로 background 실행.
- 2026-10-01 기준선(Windows, base `c9eb5d5`, `bash scripts/verify.sh python`): 실패는 `test_wiki_check.py`(failures 2·errors 2·skipped 14, 126개)·`test_wiki_search.py`(failures 1·skipped 1, 32개) 둘뿐 — 같은 5건. 나머지 python 테스트 9파일은 ok(`test_commit_units.py` 포함). POSIX 기준선(WSL ext4): 세 파일 모두 OK(wiki_check skipped 2 — `test_wiki_md_block_copy_matches_original`·`test_case_mismatched…`). Windows 3.9.25 기준선: 같은 5건만 실패.
- 2026-10-01 원인 조사 workflow(`wiki-windows-rootcause`, 원인별 조사 4 + POSIX 기준선 1 + 반증 4): 네 원인 모두 반증 실패(확신 high). 수정안 반증 결과 — stdout·stdin·wiki_search 는 반증 실패, 대소문자 테스트안은 "기능 감지" 조건이 `WindowsPath` 비교(대소문자 무시)라 사실상 `os.name` 분기라는 결함으로 반증 → 단일 불변식 테스트로 바꿨다(Decisions). 반증 지적 반영: stdin 스레드는 `OSError` 만이 아니라 모든 예외를 넘긴다, wiki_search 는 최소 형태로. scratch 사본 초안이 Windows(관련 4클래스 52 OK)·POSIX(130 OK)에서 통과.
- 2026-10-01 plan-reviewer(codex 미가용 — out of credits, 세션 마커 기록): CONDITIONAL. 강한 2 — `ThreadStdinTest` 가 실패·회귀 시 멈춤(Windows 에서 다른 스레드가 `os.read` 중인 fd 의 `os.close` 가 3초 막힘 실측, CI lint job 시한 없음) / `test_wiki_check.py:193` 주석이 낡음. 약한 11. 초안 독립 실측: EOF 없는 stdin 10회·종료 중 데이터 도착 경합 15회 × 3.13·3.9 전부 exit 0·`systemMessage`·stderr 빈 값·최대 1.12초. 처분은 Review Disposition.
- 2026-10-01 구현(TDD, 단위마다 Red → Green → 커밋 — sha 는 Report): 단위 1 wiki_search(Windows·POSIX 모두 Red — fixture 의 `\` → Green), 단위 2 `_Stdout`(커밋 전 Windows 전체·POSIX 171 OK·출력 바이트 비교·닫힌 stdout 실측), 단위 3 `_read_in_thread`+`ThreadStdinTest`(양쪽 Red — 헬퍼 없음 → Green), 단위 4 대소문자 테스트. 검증 증거(Acceptance 번호): Windows 3.13 wiki_check 130 OK(skip 14)·wiki_search 32 OK(skip 1)=1·2, Windows 3.9.25 130 OK(skip 31 — tomllib 없음)·32 OK·13 OK=3, WSL ext4 175 OK(skip 2)=4, `hookreal.py` python 20회 최대 1.14초·`uv run` 10회 최대 1.76초·Node 부모 end 190ms/hang 1098ms=5, `closedout.py` 작은·큰 출력 rc 2 traceback 없음·hook rc 0(base 는 rc 120/traceback)=6, `bytecmp.py` schema·`--branch`·`--report`·`--stop-hook` 바이트 동일 × Windows·POSIX=7, `mutate.py stdin` 변이 모두 4~11초에 실패·멈춤 없음 × 양쪽=9, `mutate.py case` 거짓 stale 실패·거부 통과=10, `console_probe.py` 숨긴 콘솔(`_WindowsConsoleIO`)에서 exit 1·예외 없음=11.
- 2026-10-01 구현 리뷰 workflow(`wiki-windows-review` — code-reviewer·architecture-reviewer + 지적마다 반증 agent, codex 미가용): code COMMENT(Critical·Major 0, Minor 3·Nit 4), arch APPROVE(Minor 3 — 반증 뒤 1건은 Nit·범위 밖). 처분은 Review Disposition `[code]`·`[arch]`. 반영: 단위 2 fixup(가드를 `isinstance(…, io.TextIOWrapper)` 로 — StringIO 호스트에서 base 는 stderr 가드로 이미 `AttributeError`, 새 코드는 exit 1 정상 / `_Stdout` docstring / `StdoutTest` — 변환 제거·조건 뒤집기 변이가 양쪽에서 실패), 단위 3 fixup(daemon 단언 — `daemon=False` 변이가 양쪽에서 실패 / fd 0 제약을 `read_stdin` docstring 으로 — timeout 뒤 stdin 을 물려받는 git 생성이 3.64초 막힘 재현), SKILL.md skip 범주. simplify 체크: 걷어낼 것 없음(POSIX `select` 루프와 `pump` 의 크기 계산 중복은 POSIX 경로 불변 결정으로 둔다).
- 2026-10-01 구현 리뷰 2차(code-reviewer, fixup 2개·미커밋 docs 대상): APPROVE, Minor 2·Nit 4 — 처분 `[code-2]`. 반영: 단위 2 fixup 2번째(`StdoutTest` 에 nt + ENOSPC subtest — `errno-dropped` 변이가 양쪽에서 실패, `mock` import 순서), SKILL.md 의 index 상태 미검증, plan 문구.
- 2026-10-01 최종 검증(격리 runner, 명령 14개): `bash scripts/verify.sh` 전체(Windows) `FAILED: 1` — wiki 3파일·python 12파일·node·syntax·shellcheck 는 ok, 실패는 `skills/jira-worklog/test_launcher.sh` 하나(아래), skip 은 `record-verified.test.sh`(jq 없음)·`install-hooks.test.js` 의 `[ps1]` 케이스. `improve.sh --ci` exit 0(error 0·warn 0), plan-lint 0, 3.9.25 wiki_check 131 OK(skip 31)·wiki_search 32 OK·check_links 13 OK, WSL 176 OK(skip 2), `hookreal`(python 20회 최대 1.13초·`uv run` 10회 최대 2.29초·Node end/hang)·`closedout`·`bytecmp`(양쪽)·`mutate` stdin/stdout/case(양쪽)·콘솔 probe 모두 기대대로. runner 가 출력 한계로 못 본 항목(Acceptance 1·2·4·8 의 개수·skip 이름·`test_unreadable_index_exit_2` 실행)은 메인이 `counts.sh` 로 직접 확인 — Windows 3.13 wiki_check 131 OK(skip 14 — 기준선과 같은 14건)·wiki_search 32 OK(skip 1 = 권한 테스트, `test_unreadable_index_exit_2` ok), WSL 131 OK(skip 2 — 기준선과 같은 두 테스트)·32 OK·13 OK. runner 관찰과 어긋나는 판정은 없다.
- 2026-10-01 `test_launcher.sh` 실패 입증: base `c9eb5d5` 의 `skills/jira-worklog` 를 scratch 에 꺼내 Git Bash 로 돌려도 같은 단언(`test 1 -eq 127`)에서 실패한다. 이 브랜치는 jira-worklog 를 건드리지 않았다(`git diff c9eb5d5 HEAD -- skills/jira-worklog` 빈 값). WSL bash 에서는 통과한다 → Deferred.
- 2026-10-01 evidence gate: Acceptance 1~13 전 항목 증거로 충족 → **DONE**(13 은 base 에서 입증된 범위 밖 실패 하나를 Deferred 로). status 는 머지 때 done(§10).

# Next
- 단위 5 docs 커밋(SKILL.md·intent·plan) → commit-check(fixup 3개를 대상에 합치고 bf5082e·0d2dbdc 메시지 갱신 — 사용자 승인) → Report → 마무리 선택(`/e merge` 등).

# Decisions
- 계획 전 wiki 조회(`windows wiki_check`·`stdin stop-hook`·`wiki_check stale hook covers`): [[lesson-no-speculative-platform-switch]](실행해 보지 못한 플랫폼 분기 금지 — 이번엔 대상 플랫폼에서 직접 실행해 확인한다), [[python-subprocess-text-stdin-windows]](Windows 의 subprocess stdin 쓰기는 EINVAL 을 "읽는 쪽이 닫음"으로 본다 — CPython `_stdin_write` 선례), [[windows-bash-tool-orphan-processes]](Windows verify.sh 는 오래 걸린다 — background 실행). 셋 다 따른다. Stop hook 전용 결정 페이지는 없다.
- 선행 plan `2026-09-29-wiki-freshness-gate`(done)의 결정과의 관계:
  - "Windows 의 `select` 는 소켓만 받으므로 막히는 읽기로 둔다(미검증 — 묶음 제약)" 를 뒤집는다. 근거: 그때는 Windows 에서 실행할 수 없어 남긴 것이고, 이번엔 이 머신에서 실행해 확인한다. 테스트가 정한 계약(1초·`STDIN_MAX`)을 Windows 분기만 어겼고, 사용자 요청(실패 5건 수정)이 이 계약 이행을 요구한다.
  - 대소문자만 다른 wiki 인자의 거부(그 plan 의 리뷰 FP-6)가 지키려던 것은 "인자 표기가 판정·지문을 바꾸지 않는다" 다. Windows 는 resolve 가 정규화해 이것이 이미 지켜진다 — 거부를 Windows 로 넓히지 않는다(아래 3).
  - "main 의 `BrokenPipeError` 는 stdout 에서만 온다"(stderr 는 `_QuietStderr`) 전제를 유지한다.
- 묶음 `repo-context-kit`(open)에 연결한다 — 처음엔 "묶음 Problem 의 단위가 아니다" 로 연결하지 않으려 했으나 바꿨다(이유: 묶음 도구의 판정 정확도 수정인 check-links-alias 가 연결된 선례가 있고, 묶음 제약의 "(Windows) 실행해 볼 수 없는 플랫폼" 전제가 이 plan 의 실측으로 더는 참이 아니라 다음 단위(wiki-init)가 그 전제를 근거로 쓰지 않게 고쳐야 한다 — plan-reviewer W2). 공통 제약 변경을 알릴 진행 중 plan 은 없다(묶음의 연결 plan 3개 모두 done).
- 1) 닫힌 stdout — stdout 을 `_QuietStderr` 처럼 `io.TextIOWrapper` 서브클래스 `_Stdout` 으로 다시 감싼다. `write`·`flush` 의 `OSError` 가 `os.name == "nt"` 이고 errno EINVAL 이면 `BrokenPipeError` 로 바꿔 올린다(원 예외는 `__cause__`). 그러면 `main()` 의 기존 `except BrokenPipeError`(exit 2 + `_discard`) 한 곳이 두 플랫폼을 다 받는다. 감싸는 것은 모든 플랫폼에서 하고(`reconfigure` 대신 같은 encoding·errors·line_buffering·write_through 로 rewrap — stderr 와 헬퍼 공유), 바꾸는 것만 nt 로 가른다 — POSIX 의 쓰기 EINVAL 은 다른 뜻이고 닫힌 pipe 는 이미 EPIPE 다(✅ WSL). Windows 는 race 에 따라 EPIPE 도 낼 수 있어(gh-79935) `except BrokenPipeError` 는 그대로 둔다.
  - 기각: `main()` 에서 EINVAL 을 잡기 — Windows 에서는 `? * < > | "`·제어문자 경로의 `os.stat`·`open` 도 EINVAL 을 내(✅ 실측) 파이프와 무관한 결함을 traceback 없이 숨긴다. 오류가 난 스트림에서 바꿔야 뜻이 "stdout 이 닫혔다" 하나로 좁혀진다.
  - 기각: EINVAL 일 때 닫힘을 더 확인 — `_winapi.WriteFile(handle, b"")`(닫힌 pipe 는 winerror 232, ✅) 또는 `stat.S_ISFIFO(os.fstat(fd).st_mode)`(닫힌 pipe 도 FIFO, devnull 은 CHR — plan-reviewer W9 실측). 얻는 것은 Windows 에서 파이프가 아닌 stdout 의 쓰기 EINVAL 때 traceback 하나뿐이고 exit code(2)는 같다. 앞의 것은 private 모듈 의존, 뒤의 것은 오류 경로 안의 새 syscall 과 그 실패 처리가 는다.
  - 기각: 래퍼를 nt 에만 설치 — stdout 설정이 두 갈래가 된다. POSIX 출력이 base 와 같은지는 Acceptance 7 로 다시 본다.
- 2) Windows stdin — `read_stdin` 의 nt 분기가 `_read_in_thread(fd, wait)` 를 부른다. daemon 스레드가 raw fd 에 막히는 `os.read` 를 EOF 또는 `STDIN_MAX` 초과까지 돌려 결과 하나를 `queue.Queue` 로 넘기고, 메인은 `get(timeout=wait)` 로 기다린다. 스레드의 예외는 무엇이든 넘겨 메인에서 다시 올린다(POSIX 처럼 `hook_main` 이 보고 — 반증 지적). timeout 이면 스레드는 읽기에 막힌 채 남아 프로세스와 함께 끝난다 — 초안(결과 하나 전달)으로 plan-reviewer 가 잰 값: EOF 없는 stdin 10회·종료 중 데이터 도착 경합 15회 × 3.13·3.9 모두 exit 0·stderr 빈 값·최대 1.12초(조사 단계의 "종료 지연 ≤17ms" 는 채택하지 않은 청크 전달안에서 잰 값이다). 그동안 그 fd 의 `close` 는 읽기가 끝날 때까지 막혀(Windows 실측 3초) timeout 뒤에는 fd 를 건드리지 않는다 — 지금 timeout 경로는 곧바로 반환하고 git 이 stdin 을 물려받는 것은 eof 경로뿐이다(docstring 에 적는다). `sys.stdin.buffer` 가 아니라 fd 를 읽어야 종료 때 그 lock 을 쥔 스레드가 없다. timeout 의 바이트는 b"" 다 — 호출부는 eof 의 바이트만 쓴다(`read_stdin` docstring). POSIX `select` 루프는 그대로.
  - 기각: `PeekNamedPipe` 폴링(`_winapi` 또는 ctypes) — 파일 종류 분기가 늘고 Windows 에서만 테스트된다. 측정 동작은 스레드안과 같았다.
  - 기각: `concurrent.futures` — atexit 이 막힌 worker 를 join 해 종료가 멈춘다.
  - 기각: POSIX 도 스레드로 통일 — 작동·테스트된 `select` 경로를 바꿀 이득이 없다. 대신 헬퍼를 os.pipe 로 모든 플랫폼에서 단위 테스트해 ubuntu CI 가 Windows 로직을 덮는다.
  - 기각: 조사안의 청크 단위 전달(부분 바이트를 timeout 에 돌려주려고 크기 계산이 스레드·메인 두 곳) — 호출부가 timeout 의 바이트를 쓰지 않아 단순한 쪽을 택했다.
  - 관찰: Windows 에서 NUL stdin 은 `os.isatty` 가 True 라 nt 분기 전에 "tty"(빈 stdin 과 같은 결과)다 — 수정 전부터 그렇고 해가 없어 두었다.
- 3) 대소문자 테스트 — 제품은 고치지 않는다. 테스트를 불변식 하나로 바꾼다: 대소문자 무시 FS 에서 `stale --branch Wiki` 는 거부되거나 — exit 2 이고 stderr 에 `open_repo` 의 거부 문구("git 은 wiki")가 있다(crash 의 exit 2 를 거부로 세지 않는다 — plan-reviewer W1) — 올바른 표기와 같은 (exit code, stdout) 이어야 한다. clean 출력에 covers 페이지 수와 base sha 가 들어 있어 아무 페이지도 못 본 경우·다른 base 도 "같은 판정" 에서 걸러진다. fixture 는 그대로(페이지와 covers 코드를 한 commit 에 — 경로가 git 과 어긋나면 페이지 변경을 못 봐 거짓 stale 이 나는 구분력 있는 경우). 이름은 `test_case_mismatched_wiki_argument_is_refused_or_judged_the_same`. resolve 가 표기를 그대로 두는 플랫폼은 거부 쪽을, Windows 는 같은 판정 쪽을 탄다(✅). 거짓 stale(Linux DrvFs 의 rc 1)은 둘 다 아니라 실패한다.
  - 기각: Windows 에서도 거부하게 제품을 고치기 — 판정이 이미 맞고, 어떤 표기로 친 경로·소문자 드라이브 cwd 를 "Windows 가 같다고 보는 경로를 다시 치라" 는 오류로 막게 된다.
  - 기각: `resolve()` 결과로 갈라 두 테스트(거부 / 같은 판정) — 조사안의 조건 `(root / "Wiki").resolve() == self.wiki` 는 `WindowsPath` 비교가 대소문자를 무시해 감지가 아니라 숨은 `os.name` 분기였다(반증 agent 실측). `.name` 비교로 고칠 수 있지만, 지키려는 것이 "판정을 바꾸지 않는다" 하나라 단일 불변식이 더 단순하고 플랫폼 추론에 기대지 않는다.
- 4) wiki_search 읽기 실패 — `e.filename` 과 `e.strerror` 가 있으면 `<경로>: <이유>`, 없으면 지금처럼 `str(e)`. wiki_check `load_config` 의 `{path}: … {e.strerror or e}` 와 같은 모양이다. 테스트는 shared wiki 를 이름에 `\` 가 든 디렉터리에 만든다 — POSIX 에서는 글자라 repr 로 겹친 경로를 ubuntu CI 도 잡고, Windows 에서는 구분자라 중첩 디렉터리일 뿐이다(plan-reviewer W8 a).
  - 기각: `filename2`·bytes·fd 까지 다루는 헬퍼(조사안) — `load_pages` 의 OSError(`read_bytes`·`os.walk` onerror)는 늘 str 경로 하나와 OS 이유를 가져 닿지 않는 경로다.
- 5) 새 테스트는 `ThreadStdinTest`(EOF 까지 끊어 온 청크·timeout(남은 리더가 daemon 인지 포함)·`STDIN_MAX` 초과·읽기 오류가 호출자에서 올라옴, 4개)와 `StdoutTest`(닫힌 pipe 의 EINVAL 이 nt 에서만 `BrokenPipeError` — write·flush 두 경로, 1개)다. `ThreadStdinTest` 는 실패해도 멈추지 않게 쓴다 — 정리 순서는 쓰는 쪽 닫기 → 새로 생긴 스레드 기다리기 → 읽는 쪽 닫기, 쓰는 쪽은 5초 뒤 감시 타이머도 한 번만 닫는다(이유: Windows 는 다른 스레드가 읽는 중인 fd 의 `os.close` 를 그 읽기가 끝날 때까지 막아, 정리 순서가 틀리거나 헬퍼가 시한 없이 막히는 회귀가 verify.sh 멈춤이 된다 — plan-reviewer S1). `StdoutTest` 는 `os.name` 을 write·flush 둘레에서만 `mock.patch` 한다(pathlib 도 실행 중에 `os.name` 을 읽는다 — architecture-reviewer A1 채택, 처음 "1번은 Windows 실행에서만 회귀를 잡는다" 로 두었던 것을 바꿨다). 1·4번은 기존 실패 테스트가 회귀 테스트다(base Red ✅). ubuntu CI 가 못 잡는 것: `read_stdin` 의 nt 분기 연결(Windows `StopHookTest` 가 잡는다), `__main__` 의 `_Stdout` 설치(Windows `SchemaTest` 의 닫힌 stdout 테스트가 잡는다 — 설치를 빼는 변이가 POSIX 전체를 통과한다, 2차 리뷰 실측), 대소문자 테스트(대소문자를 가리는 FS 에서는 skip).
  - 기각: nt 판정을 모듈 상수로 빼 가짜 buffer 로 `_Stdout` 을 POSIX 에서 단위 테스트(plan-reviewer W8 b) — 파일 안의 다른 `os.name` 분기(`start_new_session`·`_kill_group`·`read_stdin`)와 갈라지고 테스트만을 위한 표면이 는다. `mock.patch` 는 제품 코드를 바꾸지 않아 이 두 사유에 걸리지 않는다. 큰 출력의 닫힌 stdout 은 같은 except 경로라 Acceptance 6 의 실측으로만 본다.
- 커밋 단위: 1) `fix(wiki): show the path as the OS spells it in wiki_search read errors` — `wiki_search.py` + `test_wiki_search.py` 2) `fix(wiki): treat EINVAL on a closed stdout pipe as a broken pipe on Windows` — `wiki_check.py` 의 `_Stdout`·`_rewrap`·`__main__` + `test_wiki_check.py:193` 주석 3) `fix(wiki): bound the Stop hook stdin read on Windows with a reader thread` — `wiki_check.py` 의 `_read_in_thread`·`read_stdin` + `test_wiki_check.py` 의 `ThreadStdinTest` 4) `test(wiki): accept a case-mismatched wiki argument that resolves to the disk case` — `test_wiki_check.py` 대소문자 테스트 5) `docs(wiki): record where wiki_check was checked on Windows` — `SKILL.md`, 묶음 intent, plan. 2·3 은 같은 파일이라 단위마다 구현·검증·커밋을 끝내고 다음으로 간다. plan 은 마지막 커밋에만.
- 가장 위험한 단계는 단위 2 다 — 모든 플랫폼의 모든 CLI·hook 호출에서 stdout 객체를 바꾸는데, hook 은 언제나 exit 0 이라 출력이 깨져도 게이트가 조용히 꺼진다. 단위 2 는 커밋 전에 Windows·POSIX 전체를 돌린다(특히 `>&-` 로 `sys.stdout is None` 경로를 덮는 `test_closed_stdout_or_stderr_still_exits_0` 은 POSIX 에서만 돈다 — plan-reviewer W5).
- ⚠️ 분할하지 않는다 — 분할 판정(독립 머지 가능하면 나눈다)과 고정비 사이에서 판단했다 — 결합은 없지만 고정비 때문에 한 plan·목적 단위 커밋을 택했다.
- ⚠️ POSIX stderr 문구가 바뀐다 — "POSIX 동작 불변" 과 상충 — wiki_search 읽기 실패가 `[Errno 21] Is a directory: '/p/index.md'` 에서 `/p/index.md: Is a directory` 로 바뀌는 것을 감수한다. `repr` 을 쓰지 않는 한 POSIX 의 따옴표도 빠지고, 피하려면 플랫폼 분기밖에 없다. 이 문구를 단언·파싱하는 곳은 worktree·공용 wiki 에 없다(plan-reviewer 도 직접 찾음 — 무매칭이라 정황 근거). exit code·stdout 은 같다. 커밋 메시지에 적는다.
- ⚠️ 대소문자 테스트의 거부 갈래(macOS 로 보는 플랫폼)는 실행하지 못하고 추론에 기댄다 — 단일 불변식은 거부(문구 단언 포함)·같은 판정 어느 쪽도 받아, 추론이 틀려도 테스트 판정은 맞다.

# Key Files
- `skills/wiki/wiki_check.py` — `read_stdin`·`_read_in_thread`(Windows stdin), `_Stdout`·`_raise_if_closed_pipe`·`_rewrap`·`__main__`(닫힌 stdout), `main`·`hook_main`(호출부, 변경 없음)
- `skills/wiki/wiki_search.py` — `main` 의 읽기 실패 문구
- `skills/wiki/test_wiki_check.py` — `ThreadStdinTest`·`StdoutTest`(신규), 대소문자 테스트(변경), `_run_code` 주석, 실패 4건
- `skills/wiki/test_wiki_search.py` — `test_unreadable_index_exit_2`(fixture 경로)
- `skills/wiki/SKILL.md` — "Python" 절 Windows 서술
- `plans/2026-09-29-repo-context-kit/intent.md` — 묶음 Constraints 의 Windows 전제, `# Plans` 줄

# Blockers

# Review Disposition
- [self-flag] 분할하지 않음 — accepted-risk(결합 없음·고정비, `분할:` 문구 정정)
- [self-flag] POSIX stderr 문구 변경 — accepted-risk(피하려면 플랫폼 분기뿐, 소비자 없음, 커밋 메시지에 적는다)
- [self-flag] 대소문자 테스트 macOS 추론 — resolved(W1 로 거부 갈래에 문구 단언)
- [plan] S1 `ThreadStdinTest` 가 실패·회귀 시 멈춤 — fix(정리 순서 + 감시 타이머, Acceptance 9 변이)
- [plan] S2 `test_wiki_check.py:193` 주석 낡음 — fix(단위 2)
- [plan] W1 거부 갈래가 exit 2 만 봄 — fix(거부 문구 단언), 테스트 주석의 macOS 단정 — fix(플랫폼 이름 빼고 Windows 만 실측으로)
- [plan] W2 묶음 연결 — fix(연결, intent 전제 갱신·`# Plans` 줄)
- [plan] W3 SKILL.md 확인 범위 — fix(Acceptance 11·12: 콘솔 시도 후 범위 고정)
- [plan] W4 Acceptance 보강 — fix(4 문구, 5 `uv run`, 7 바이트 비교, 9·10 변이)
- [plan] W5 가장 위험한 단계 — fix(단위 2 지목, 커밋 전 양 플랫폼 전체)
- [plan] W6 커밋 4 목적 섞임 — fix(SKILL.md 를 단위 5 `docs` 로)
- [plan] W7 근거 표기 — fix(Decisions 2 의 측정 출처, Intent 2 의 hook 비교 ⚠️)
- [plan] W8 CI 가 덮는 범위 — fix(a: wiki_search fixture 에 `\`) · wontfix(b: nt 상수화 — Decisions 5 기각, Windows 실행에서만 잡는다고 명시 → 구현 리뷰 A1 로 바뀜: `mock.patch` 의 `StdoutTest` 로 변환은 CI 가 덮는다)
- [plan] W9 FIFO 판정 대안·PeekNamedPipe 표기 — wontfix(Decisions 1 에 비용 기준 기각) · fix(표기)
- [plan] W10 fd 잠김 제약 — fix(`_read_in_thread` docstring → 구현 리뷰 A2 로 호출부 계약인 `read_stdin` docstring 으로 옮김)
- [plan] W11 Deferred 추가 — fix(아래 Deferred 3줄)
- [code] F1 SKILL.md 의 Windows skip 범주가 일부만 적혀 git 시한·자식 정리·hook 시간 예산이 확인된 것처럼 읽힘 — fix(skip 이 덮는 경로를 "확인하지 않았다" 로 열거)
- [code] F2 `ThreadStdinTest` 가 리더의 daemon 속성을 지키지 않음(`daemon=False` 변이 통과), 0d2dbdc 메시지의 "ubuntu CI covers the Windows logic" 과장 — fix(이름으로 찾은 리더가 있고 모두 daemon 인지 단언 — 빈 목록이면 실패, 단위 3 fixup / 메시지는 commit-check 에서 "read_stdin 의 nt 분기 연결은 Windows 실행만 잡는다" 로 좁힌다)
- [code] F3 plan Next·Progress 미갱신 — fix
- [code] F4(Nit) stdout 가드가 `detach` 유무로 넓어져 StringIO 류 호스트에서 `write_through` AttributeError — fix(stdout·stderr 둘 다 `isinstance(…, io.TextIOWrapper)` — stderr 쪽은 base 부터 같은 crash 였다, 실측)
- [code] F5(Nit) `_Stdout` docstring 의 "EINVAL 만" 단정 — fix("대개", EPIPE 일 때도 있다)
- [code] F6(Nit) wiki_search `__main__` 의 "(wiki_check.py 와 같다)" — deferred(목적인 UTF-8 은 여전히 같다. wiki_search 닫힌 stdout Deferred 를 고칠 때 함께)
- [code] F7(Nit) timeout 바이트가 플랫폼마다 다름(POSIX 부분 바이트, Windows b"") — wontfix(docstring 이 "입력으로 쓰는 것은 eof 일 때뿐" 이라 호출부 계약은 같다, POSIX 경로 불변)
- [code] open — 실제 Claude Code(Windows)가 Stop hook stdin 을 end 하는지 — accepted-risk(Node 부모 end/hang 실측, SKILL.md 에 "Claude Code 에 등록해 돌려 보지는 않았다" 공개. end 하지 않는다면 지금은 1초 뒤 timeout systemMessage 이고, 수정 전에는 hook timeout 까지 멈췄다)
- [arch] A1 nt 변환을 `mock.patch` 로 POSIX CI 에서 덮을 수 있음 — fix(`StdoutTest`, 단위 2 fixup, Decisions 5)
- [arch] A2 fd 0 제약이 private 헬퍼 docstring 에만 — fix(`read_stdin` docstring 으로 옮기고 stdin 을 물려받는 자식 생성도 적음 — 재현 3.64초, 단위 3 fixup)
- [arch] A3 표준 스트림 설정이 wiki_check `__main__` 인라인뿐 — deferred(반증 뒤 Nit·범위 밖. wiki_search 닫힌 stdout Deferred 줄에 구조 메모)
- [code-2] APPROVE — 1차 처분 10건 반영 확인(F2·A1 변이가 양쪽에서 실패, `StdoutTest` 는 3.9·`-X dev`·순서·GC 잡음 문제 없음, 가드는 콘솔·pipe·StringIO 정상). Minor 1 Decisions 5 의 "nt 분기 연결뿐" 이 틀림(`__main__` 의 `_Stdout` 설치도 Windows 만 잡는다) — fix(Decisions 5, Deferred 의 wiki_search 줄, bf5082e 메시지는 변환까지만 CI 라고 적는다) · Minor 2 SKILL.md 의 "symlink" 가 `--report` 지문의 index 상태 미검증을 가림 — fix(경로로 풀어 씀) · Nit `StdoutTest` 가 errno 조건을 지키지 않음 — fix(nt + ENOSPC → OSError subtest, `errno-dropped` 변이가 양쪽에서 실패) · Nit W8 b·W10 줄 낡음 — fix · Nit Deferred 의 base 기준 줄 번호 — fix(심볼 이름으로) · Nit `mock` import 순서 — fix · open `_Stdout` docstring 의 "CRT 가 ERROR_NO_DATA 를 errno 로 옮기지 못한다" 를 이슈 본문으로 직접 확인 못 함 — accepted-risk(동작은 실측·이슈 제목으로 확인, 조사 agent 가 gh-79935 의 eryksun 설명 "STATUS_PIPE_CLOSING … ERROR_NO_DATA and C errno EINVAL" 을 인용함)

# Deferred
- [medium] Windows Git Bash 에서 `skills/jira-worklog/test_launcher.sh` 가 실패한다(기존 — base `c9eb5d5` 재현). 실행기 없는 PATH 에서 `run_worklog.sh` 가 127 이 아니라 1 을 내 `test 1 -eq 127` 에서 `set -e` 로 메시지 없이 끝난다. 그래서 Windows 의 `bash scripts/verify.sh` 가 `FAILED: 1` 로 끝나고, `/e` 6단계가 이 종료코드로 정리 여부를 가르므로 Windows 에서 오판할 수 있다. WSL bash 에서는 통과한다.
- [medium] Linux 대소문자 무시 FS(WSL DrvFs `/mnt/c` ✅, SMB·vfat·ext4-casefold ⚠️)에서 대소문자만 다른 wiki 인자를 거부도 정규화도 하지 않는다 — realpath·getcwd·`--show-prefix` 가 모두 `Wiki/` 를 내고 index 는 `wiki/` 라 거짓 stale(rc 1). 기준선부터 그렇다(대소문자 테스트가 DrvFs 에서 실패). 고치려면 getcwd 와 무관한 표기원(`git ls-files --full-name` 대조 또는 `core.ignorecase` 일 때 디렉터리 목록으로 정규화)이 필요하다. `wiki_check.py` `resolve_context`·`open_repo`.
- [low] wiki_search 에 닫힌 stdout 처리가 없다 — base 에서 Windows exit 120 + "Exception ignored on flushing sys.stdout: OSError [Errno 22]" 실측(plan-reviewer). 1번 수정과 같은 계열. wiki_search `__main__`. 고칠 때 wiki_check `__main__` 의 스트림 설정을 함수로 빼 두 스크립트가 함께 쓰고(wiki_search 는 이미 wiki_check 을 import), `wiki_search.main` 에도 `BrokenPipeError` → `_discard` → exit 2 처리를 넣는다(설치만으로는 안 고쳐진다). wiki_search `__main__` 의 "(wiki_check.py 와 같다)" 주석도 그때 고친다(구현 리뷰 A3·F6). 옮긴 뒤에는 Windows 에서 `SchemaTest.test_closed_stdout_exits_2_without_traceback` 을 돌린다 — `_Stdout` 설치가 빠지는 회귀는 ubuntu CI 가 못 잡는다(2차 리뷰).
- [low] `StopHookTest.test_closed_stdout_or_stderr_still_exits_0` 가 sh 리다이렉트 때문에 nt 에서 통째로 skip — 뒤쪽 os.pipe 단계는 플랫폼 무관이라 skip 을 sh 부분으로 좁히면 Windows 에서도 돈다.
- [low] `str(OSError)` 를 그대로 싣는 다른 문구 — `hook_main` 의 `예상 밖 오류 — {e}`(Windows 경로가 이중 역슬래시로 `systemMessage` 에), `Git.run` 의 `GitError(f"git 을 실행하지 못했다 — {e}")`(Windows 는 `filename` 이 없어 무엇을 못 찾았는지 빠짐).
- [low] `check_links.py` 가 페이지·index 를 `read_text` 할 때 try 가 없어 OSError·UnicodeDecodeError 가 traceback 과 exit 1 — 위반 exit code 와 겹친다.
- [low] `open_repo` docstring 과 선행 plan FP-6 서술이 "대소문자 무시 FS 면 거부" 로 읽힌다 — Windows 는 정규화, Linux DrvFs 는 둘 다 아니다.
- [low] `test_stdin_without_eof_ends_within_3_seconds` 의 3초 한도는 Windows 부하 시 여유가 작다 — 동시 verify.sh 아래 최대 2.5~2.8초 관측, 초과 0회(기동 시간 포함, POSIX 도 같은 구조).
- [wiki] `~/.claude main 세션에서 /wiki ingest` — Windows 에서 다른 스레드가 `os.read(fd)` 로 막혀 있으면 같은 fd 의 `os.close` 와 그 handle 을 물려받는 자식 생성이 그 읽기가 끝날 때까지 막힌다(CPython 3.13.15, 3초·3.64초 실측 — UCRT fd lock 은 추정) · Windows 의 닫힌 pipe 쓰기는 대개 `BrokenPipeError` 가 아니라 `OSError(EINVAL)`(gh-79935, 경합에 따라 EPIPE) — 오류가 난 스트림에서 바꾼다(main 에서 EINVAL 을 잡으면 `? *` 경로의 EINVAL 까지 섞인다) · Windows 의 `Path.resolve()` 는 디스크의 대소문자로 되돌리고 macOS 는 친 표기를 두며 Linux 의 DrvFs 는 대소문자를 무시하면서도 정규화하지 않는다 · Windows `select` 는 소켓만 받아 시한 있는 stdin 읽기는 daemon 스레드 + `queue.get(timeout)` 로 한다(`concurrent.futures` 는 종료 때 막힌 worker 를 join 해 멈춘다) · Python `subprocess` 의 `"bash"` 는 Windows PATH 에서 `System32\bash.exe`(WSL)로 잡힐 수 있다 · 출처: 공개(이 repo 의 재현).
- [lesson] `~/.claude main 세션에서 승인 후 적립` — 플랫폼 확인 범위를 문서에 적을 때 skip 된 테스트가 덮는 **경로**를 미확인으로 열거한다(skip 사유 이름 — "symlink" 등 — 은 그 뒤의 경로를 가린다). 이번 작업에서 같은 실수를 두 번 했다(구현 리뷰 F1 → 2차 Minor 2). 공용 wiki `lesson-…` + `MEMORY.md` 인덱스 줄 후보(§13).
