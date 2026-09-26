---
title: claude-code-bash-tool-shims
category: entity
created: 2026-09-26
updated: 2026-09-26
sources:
  - ~/.claude/shell-snapshots/snapshot-zsh-*.sh (Claude Code 2.1.282, 2026-09-26 확인)
  - 세션 재현 2026-09-26 — ugrep 7.8.4(내장)·rtk 0.44.2·/usr/bin/grep(BSD 2.6.0) 비교
  - plans/2026-09-25-repo-audit-g5-g7-install (오판이 plan 에 들어간 사례)
---

# claude-code-bash-tool-shims

Claude Code 의 Bash 도구로 친 `grep` 은 **시스템 grep 이 아닐 수 있다**. 명령 모양에 따라 서로 다른 두 프로그램으로 바뀐다(2.1.282·rtk 0.44.2, macOS zsh, 2026-09-26 확인). `bash script.sh` 안의 `grep` 만 시스템 grep 이다.

## 두 가지 대체
1. **셸 함수 → 내장 ugrep.** 도구 셸은 사용자 프로필 스냅샷을 읽는데, 그 안에서 `grep` 이 함수로 정의돼 Claude Code 실행 파일을 `ARGV0=ugrep` 으로 부른다(ugrep 7.8.4). 인자 앞에 `-G --ignore-files --hidden -I --exclude-dir=.git …` 가 고정으로 붙는다.
   - `-I`: 바이너리로 판정한 파일은 매치 없음으로 친다.
   - `--ignore-files`: 재귀 검색에서 `.gitignore` 등을 따른다 — **gitignored 파일은 빠진다**(예: `wiki/raw/`).
   - `-z`·`--null`·`--config` 류 옵션이 있거나 실행 파일이 없으면 `command grep`(시스템 grep)으로 넘긴다.
   - `find` 도 같은 방식으로 `ARGV0=bfs` 가 되고, `pkill` 은 CLI 프로세스를 맞히는 패턴을 거부하도록 감싸여 있다.
2. **PreToolUse 훅 → `rtk grep`.** rtk 재작성 훅이 단순 명령의 `grep` 을 `rtk grep` 으로 바꾼다(`rtk rewrite "LC_ALL=C grep -c x f"` → `LC_ALL=C rtk grep -c x f`). `for` 루프·`$(…)` 안처럼 재작성되지 않은 자리에서는 1번 함수가 돈다.

## 실측한 차이 (2026-09-26)
UTF-8 em dash·한글이 든 3줄 파일(비ASCII 줄 2개)에 비ASCII 줄 수 세기:

| 실행 경로 | `LC_ALL=C grep -c $'[\x80-\xff]' f` |
|---|---|
| 도구에서 `for`·`$(…)` 안(→ 내장 ugrep) | `0` — 2026-09-25 plan 오판의 원인 |
| 도구에서 단순 명령(→ `rtk grep`) | Rust panic(`Result::unwrap()` on `"[\x80-\xFF]"`), 출력 없음 |
| `bash script.sh` 안(→ `/usr/bin/grep`) | `2`(정답) |

- 같은 ugrep 에서 `-P -c '[^\x00-\x7F]'` 는 `2`, `-U`(바이트 모드)는 이 범위식을 `invalid character class range` 로 거부한다. 기본 모드가 0 을 내는 내부 이유는 확인하지 않았다(❌).
- rtk 는 비UTF-8 인자를 받으면 panic 한다 — 바이트 패턴을 인자로 넘기는 모든 명령이 해당된다.

## 어떻게 쓰나
- 바이트·인코딩 판정(비ASCII, BOM, CR)은 python(`b"\r" in data`, `any(b > 0x7f for b in data)`)으로 한다.
- 시스템 grep 이 필요하면 스크립트 파일 안에서 부르거나 `command grep` 을 쓴다.
- gitignored 파일까지 뒤지는 재귀 검색은 도구 셸의 `grep -r` 로 하지 않는다.
- 부재를 결론으로 쓰려면, 검사식을 **알려진 양성 샘플에 같은 실행 경로로** 먼저 돌려 1 이상이 나오는지 확인한다.

## 연계
grep 무매칭을 부재로 확정한 사례들은 [[lesson-grep-absence-not-proof]], rtk 재작성이 권한 규칙에 주는 영향은 [[rtk-rewrite-permission-rules]], 같은 도구 셸의 명령 거부 규칙은 [[worktree-isolation-bash-guard]].
