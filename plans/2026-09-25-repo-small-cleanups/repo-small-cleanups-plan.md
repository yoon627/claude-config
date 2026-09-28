---
title: repo-small-cleanups — skills/synced gitignore · bootstrap README settings.json 서술 · verify.sh 를 git ls-files 기반으로
status: done
started: 2026-09-25
updated: 2026-09-25
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

intent `repo-audit-followups` 의 작은 단위 세 개를 한 번에 닫는다: `.gitignore` 에 `/skills/synced/`, `scripts/bootstrap/README.md` 의 settings.json 행 정정, `scripts/verify.sh` 가 추적되지 않는 ignored 파일을 검증하지 않게 한다.

# Intent

→ `plans/2026-09-25-repo-audit-followups/intent.md`.

델타:
- Problem: (1) claude.ai 동기화 skill(`skills/synced/`, 라이선스 파일 포함)이 whitelist `!/skills/` 때문에 untracked 로 노출돼 PUBLIC repo 로 커밋될 수 있다. (2) bootstrap README 가 settings.json 을 "repo 추적 파일이라 clone 으로 따라옴"이라 적어 새 머신에서 설정 없이 시작하게 만든다. (3) verify.sh 의 `find` 가 main checkout 의 ignored 산출물(shell-snapshots·plugins/marketplaces·backups)까지 shellcheck·테스트해 main 에서는 항상 `FAILED` 다.
- Constraints: verify.sh 는 CI 와 결과가 같아야 한다(CI checkout 엔 ignored 디렉토리가 없다). 아직 `git add` 하지 않은 새 테스트도 로컬에서 잡혀야 한다(목록을 수기로 두지 않는다는 2026-09-07 결정 유지). POSIX sh 유지.
- Out of scope: verify.sh 의 python 축을 `unittest` 러너로 바꾸는 것(tracked 테스트는 모두 `unittest.main` 진입점이 있다 — 감사 low).
- 분할: 없음 — 세 단위 모두 small 이고 파일이 겹치지 않아 각자 머지해도 무모순이지만, 각 1~10줄이라 worktree·리뷰 고정비가 변경보다 크다. small 이라 커밋은 1개이고, 본문에 목적별 항목을 적는다.

# Acceptance

1. `.gitignore` 에 `/skills/synced/` — `git check-ignore -v skills/synced/x` 가 그 줄을 가리킨다.
2. `scripts/bootstrap/README.md` settings.json 행이 untracked·수동 복사(루트 README Install A 의 settings.json 단계 — Windows 5번·macOS 2번)로 서술된다 — `grep -n "repo 추적 파일" scripts/bootstrap/README.md` 0건.
3. verify.sh 가 ignored 파일을 보지 않는다: worktree 에 ignored `shell-snapshots/probe.sh`(shellcheck 오류)를 두면 수정 전 `bash scripts/verify.sh shell` → FAIL, 수정 후 → ok.
4. verify.sh 가 untracked-not-ignored 새 테스트는 잡는다: `scripts/zz-probe.test.sh`(exit 1)를 두면 수정 후 `bash scripts/verify.sh bash` 가 그 파일을 FAIL 로 보고한다.
5. 비ASCII 이름의 새 테스트도 잡힌다(`scripts/한글-probe.test.sh` exit 1 → FAIL 보고). git 이 저장소를 모르면(`GIT_DIR` 무효) 0개 통과 대신 FAIL·rc 1.
6. 전체: `bash scripts/verify.sh` → `ALL PASS`(skip 없음). README:427 의 발견 방식 서술이 새 동작과 맞는다.

# Progress

- 2026-09-25: 착수(사용자 선택 "작은 정리 3건").
- 2026-09-25: Red(ignored probe 로 수정 전 FAILED) → 구현 → code-reviewer(+codex) REQUEST CHANGES(Major 2: 비ASCII 경로 quoting 으로 테스트 누락, git 실패 시 0개 통과) → 두 건 재현 후 수정(`-z`, 작업트리 검사). Acceptance 1~6 충족, 전체 verify ALL PASS, 수정 전후 발견 집합 동일(57).

# Next

(없음 — 로컬 ff-merge 로 종료)

# Decisions

- 커밋 단위: 1개 — small 이라 dlc 16단계 1회 커밋. 세 목적은 파일이 겹치지 않아 한 커밋 본문에 항목별로 적는다.
- verify.sh 대상 목록: `git ls-files --cached --others --exclude-standard` + 존재 검사. `--cached` 만 쓰면 아직 add 하지 않은 새 테스트를 로컬에서 놓치고, `find` 는 ignored 산출물을 끌어온다. 기각: find 에 `-not -path` 제외 목록 추가 — ignored 디렉토리가 생길 때마다 목록을 고쳐야 한다(`.gitignore` 가 이미 단일 소스).

# Review Disposition

- [code] Major 비ASCII 경로 quoting 누락 — fix(`git ls-files -z` + `tr`). Major git 실패 시 fail-open — fix(시작 시 `git rev-parse --is-inside-work-tree`). Minor bootstrap README 단계 번호 — fix(Windows 5번·macOS 2번). Minor README 단정 — fix. Minor plan 커밋 방침 불일치 — fix(Intent 문구를 1커밋으로). Nit 따옴표 없는 `$(…)` 펼침 — defer(기존 동작, 공백 경로는 FAIL 로 드러난다). 재리뷰: 생략 — 두 수정이 리뷰 제안과 같고 재현 케이스로 Green 확인.

# Key Files

- `.gitignore`, `scripts/bootstrap/README.md`, `scripts/verify.sh`, `README.md`(verify 절)

# Blockers

없음.
