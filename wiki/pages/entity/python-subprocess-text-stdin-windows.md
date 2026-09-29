---
title: python-subprocess-text-stdin-windows
category: entity
created: 2026-09-28
updated: 2026-09-28
sources:
  - CPython 3.13.15 Lib/subprocess.py — Windows `_stdin_write`(1153~1176행)·`_writerthread`(1619행), POSIX `_save_input`(2206~2215행)
  - 재현 2026-09-28 Windows 11, Python 3.13.15, Git Bash — 최소 스크립트 + skills/commit-check/test_commit_units.py 가 verify.sh 를 1시간 넘게 멈춤
  - https://github.com/python/cpython/issues/158006 (읽기 쪽 관련 이슈 — 제목만 확인)
  - https://github.com/liatrio-labs/claude-code-gauntlet/issues/349 (같은 증상의 제3자 보고)
---

# python-subprocess-text-stdin-windows

**Windows 에서 `subprocess.run(..., input=<str>, text=True)` 를 `encoding` 없이 부르면, 로캘 코드페이지로 표현할 수 없는 문자(한글 등)가 든 입력에서 예외 대신 무한 대기한다.** 자식 프로세스가 stdin 을 끝까지 읽는 명령(`git commit -F -`, `git hash-object --stdin` 등)이면 `timeout` 이 없는 한 영원히 끝나지 않는다.

## 사실 (✅ 2026-09-28 Windows 11·Python 3.13.15 재현)

- `text=True` 이고 `encoding` 이 없으면 파이프 인코딩은 `locale.getpreferredencoding(False)` 이다. 이 머신은 `cp1252` 였다.
- Windows 의 `communicate()` 는 stdin 을 별도 스레드(`_writerthread` → `_stdin_write`)에서 쓴다. `_stdin_write` 는 `write()` 에서 `BrokenPipeError` 와 `EINVAL` 만 잡는다. `UnicodeEncodeError` 는 잡지 않아 스레드가 죽고, 바로 뒤의 `self.stdin.close()` 에 닿지 못한다.
- stdin 이 닫히지 않으니 자식은 EOF 를 못 받아 기다리고, 부모는 자식 종료를 기다린다. 예외는 `Exception in thread … (_writerthread)` 로 stderr 에만 찍혀서, `capture_output=True` 인 테스트 러너 안에서는 멈춘 것으로만 보인다.
- 최소 재현: 자식 `python -c "import sys; sys.stdin.buffer.read()"` 에 `input="한글 메시지\n"` 을 넘기면, `text=True` 만으로는 `timeout=5` 에서 `TimeoutExpired` 가 나고 `encoding="utf-8"` 을 주면 즉시 끝났다.
- `PYTHONUTF8=1`(UTF-8 모드)이면 기본 인코딩이 `utf-8` 이 되어 같은 코드가 즉시 끝났다. 코드를 고치지 않고 실행 환경만 바꾸는 우회책이다.
- ⚠️ POSIX 는 `_save_input` 이 메인 스레드에서 인코딩하므로, 같은 입력이면 멈추지 않고 `UnicodeEncodeError` 가 호출자에게 올라올 것으로 본다. 코드 읽기 결과이고 실행은 하지 않았다. 게다가 CI 의 Linux 로캘은 보통 UTF-8 이라 인코딩 오류 자체가 안 난다. 그래서 **ubuntu CI 는 이 결함을 잡지 못한다**.

## 올바른 사용

- 텍스트를 파이프로 주고받는 호출은 `encoding="utf-8"`(필요하면 `errors=`)을 명시한다. `text=True` 만 쓰지 않는다.
- 자식에게 stdin 을 주는 호출에는 `timeout` 을 건다. 이 결함이 아니어도 stdin 이 안 닫히는 경로가 무한 대기가 되는 것을 막는다.
- Windows 에서 멈춘 Python 테스트는 자식 트리를 먼저 본다. 이번 사례에서 `git commit -F -` 는 자식 없이 CPU 0 으로 멈춰 있었다. 그러면 "stdin 대기"를 의심하고, 코드에서 쓰는 쪽이 예외로 끝났는지 확인한다.

## 이 repo 사례 (2026-09-28)

`skills/commit-check/test_commit_units.py` 의 헬퍼가 `subprocess.run([...git commit -q -F -], input=message, text=True)` 로 한글 커밋 메시지를 넘겨, Windows 에서 `bash scripts/verify.sh` 가 1시간 넘게 멈췄다. CI 는 ubuntu 뿐이라 드러나지 않았다. `PYTHONUTF8=1` 로 돌리면 이 hang 은 사라지고, 같은 파일의 서명 위조 테스트 2건이 `git hash-object` rc 128 로 따로 실패한다. 수정(`encoding="utf-8"` 명시)은 별도 작업이다.

## 관련

- [[lesson-no-speculative-platform-switch]] — Windows 는 CI 에 없어, 그 플랫폼에서만 드러나는 결함은 실제 실행으로만 확인된다.
- [[lesson-zip-reproducibility-os]] — 같은 Python 코드가 OS 기본값(여기서는 인코딩, 거기서는 zip 메타데이터·정렬) 때문에 다르게 동작한 다른 사례.
