---
title: bash-search-use-rg — Bash 재귀 검색을 grep -r 대신 rg 로
status: done
started: 2026-09-28
updated: 2026-09-28
---

# Goal
Bash 재귀 텍스트 검색이 `.gitignore` 를 따르는 `rg`(→ `rtk rg`)로 가게 한다. 새 머신 bootstrap 도 독립 `rg` 실행 파일을 설치한다.

# Intent
- Problem: rtk 훅이 Bash `grep` 을 `rtk grep` 으로 바꾸는데 `rtk grep` 은 시스템 grep 만 쓴다(rg 가 PATH 에 있어도 동일 — 2026-09-28 실측). `grep -r` 은 `.gitignore` 를 무시해 `projects/` transcript(1.1GB)까지 뒤진다: `worktree` 292,500 매치/2,823 파일/12.3초 vs `rtk rg` 1,465/188/0.04초. 또 Bash `rg` 는 `rtk rg` 로 재작성되는데 독립 `rg` 실행 파일이 없으면 실패한다(세션의 `rg` 는 Claude Code 내장 ripgrep 을 부르는 셸 함수라 rtk 자식 프로세스에서 안 보인다).
- Constraints: rtk 0.44.2 에 grep→rg 재작성 설정 없음(`rtk config` `[hooks]` 는 `exclude_commands`·`transparent_prefixes` 뿐) → 규칙(CLAUDE.md)으로 유도.
- Out of scope: setup.ps1(Windows) — 이 머신에서 실행·검증 불가(memory no-speculative-platform-switch). 자체 PreToolUse 재작성 훅 — grep/rg 플래그 의미가 달라 기계 변환은 오동작 위험. Ollama 의미 검색 — 별도 계획.

# Progress
- 2026-09-28: 이 머신에 `brew install ripgrep`(15.2.0) — `rtk rg` 정상 동작 확인. worktree 생성, plan 작성.

- 2026-09-28: CLAUDE.md §2 규칙·setup.sh 2c·README 2곳 구현, verify ALL PASS. code-reviewer(+Codex) Critical/Major 0 — Minor 반영(문구 범위 한정·`type -P`·wiki shims 갱신).

- 2026-09-28: 재검증 — dry-run 두 분기(SKIP / `brew install ripgrep`), `bash -n`, verify.sh ALL PASS. Acceptance 1~5 충족(DONE), 커밋.

# Next
없음 — 로컬 ff-merge 로 main 반영(push 는 요청 시). 후속은 `# Deferred`.

# Decisions
- 규칙 위치는 CLAUDE.md §2(컨텍스트 관리) — 토큰·잡음 문제라서. 기각: RTK.md(추적 안 되는 파일, `rtk init -g` 가 재생성).
- 기각: 자체 훅으로 `grep -r` → `rg` 자동 재작성 — `-r`/`-R`·`--include`·BRE 등 의미 차이로 조용한 오동작 위험.
- 커밋 단위: 1개 — 규칙·설치·문서가 한 목적.

# Acceptance
1. CLAUDE.md §2 에 규칙 1줄 — 관찰: 파일 diff.
2. setup.sh 가 rg 없으면 `brew install ripgrep`, 있으면 SKIP — 검증: `bash scripts/bootstrap/setup.sh --dry-run` 출력에 rg 줄, `bash -n` 통과. rg 실행 파일만 뺀 PATH 에서 dry-run 이 `brew install ripgrep` 을 낸다.
3. bootstrap README 도구 표·루트 README §2 요약 동기화 — 관찰: diff.
4. `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없는).
5. `rtk rg` 가 규칙에 적은 대로 동작(`.gitignore` 준수, `-uu` 로 ignored 포함) — 실행 관찰.

# Review Disposition
- CLAUDE.md "grep 은 .gitignore 무시" 과잉 일반화(파이프 안은 ugrep 이라 따름) — fix: "단순 명령" 한정 + wiki 링크.
- "bootstrap 이 설치" 가 macOS 한정임을 숨김 — fix: "macOS bootstrap, Windows 수동".
- bootstrap README 의 rg 셸 함수 설명 무조건 단정 — fix: "독립 rg 가 없을 때" 조건.
- setup.sh `have rg` 가 export 된 함수에 속을 수 있음(disputed Minor) — fix: `type -P rg`(비용 0, 목적이 실행 파일 확인).
- wiki shims 페이지 drift — fix: rg 경로 절 추가 + index·log.
- Acceptance 2 경계(함수만 있음) — fix: Acceptance 2 에 rg 뺀 PATH dry-run 추가.
- 설치 실패도 exit 0 — defer: node/jq 와 같은 기존 관례, 아래 Deferred.
- README:396 jq 누락(Nit) — defer: 이번 변경 이전부터의 누락.
- Open: Codex 세션에서 "rtk 훅" 문구 적합성 ❌ 미확인 · repo 밖에선 rg 가 .gitignore 를 안 따름(`--no-require-git`) — 규칙 대상이 repo 내부라 문구 유지.

# Deferred
- bootstrap setup.sh: 도구 설치 실패가 누적되지 않고 exit 0 "완료" — Minor — scripts/bootstrap/setup.sh
- setup.ps1 ripgrep 설치(Windows 검증 환경 필요) — Minor — scripts/bootstrap/setup.ps1
- README.md:396 bootstrap 도구 목록에 jq 누락 — Nit — README.md

# Key Files
- wiki/pages/entity/claude-code-bash-tool-shims.md — rg 경로 실측 절 (+ wiki/index.md·log.md)
- CLAUDE.md — §2 규칙
- scripts/bootstrap/setup.sh — 2c ripgrep 단계
- scripts/bootstrap/README.md — 도구 표
- README.md — CLAUDE.md 섹션 요약

# Blockers
