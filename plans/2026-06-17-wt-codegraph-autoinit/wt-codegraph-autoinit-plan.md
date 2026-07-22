---
title: wt-codegraph-autoinit — worktree 생성 시 codegraph 자동 init (+ 삭제 시 점유 안내)
status: done
started: 2026-06-17
updated: 2026-06-19
---

# Goal

`/wt` 가 worktree 를 만들 때 codegraph 인덱스를 **조건부·백그라운드**로 자동 생성한다.
worktree 삭제 시 codegraph daemon 점유로 remove 가 막히면 **자동 kill 하지 않고 원인을 진단·안내**한다.
codegraph 를 안 쓰는 레포에서는 완전 no-op.

# Progress
- 2026-06-19 PR #42 머지 완료 (main). status: done — worktree 정리.

- 2026-06-17: codegraph 동작 검증 → worktree 는 상위 탐색으로 main `.codegraph/`(=main 브랜치 코드)를 잡아 변경 누락. 자동화 필요.
- 2026-06-17: worktree 실측 — init 은 worktree-local 인덱스(추적 코드 8 + lint.yml = 9 files) 정확 생성. `init`·`status` 는
  daemon 미기동. daemon idle 300s 자동종료. 루트 `.gitignore` whitelist 라 `.codegraph/` 자동 ignore(→ `.gitignore` 수정 불요).
- 2026-06-17: code-reviewer + codex(0.140.0) 리뷰. **삭제 시 daemon 자동 kill 은 오인 kill 위험**(살아있는 codegraph daemon 들의
  CommandLine 이 worktree 경로 없이 동일 → stale `daemon.pid` 의 pid 가 타 worktree live daemon pid 로 재사용되면 무관 daemon kill).
  → **자동 kill 폐기, init 자동화만 + 삭제는 진단·안내로 확정**(사용자 재확인). wt/e SKILL.md 3곳 최종 수정 완료.
- 2026-06-17: 커밋 `4d2a045`, origin push, **PR #42 생성** (https://github.com/yoon627/claude-config/pull/42). 머지 대기.
- 2026-06-17: `/e` 마무리 — uncommitted 없음, PR #42 미머지라 `in_progress` 유지. worktree 보존(미머지 + plan 이 worktree 내부). 세션 main 복귀.

# Next

1. PR #42 리뷰/머지 대기.
2. 머지 후 e2e: 실제 `/wt` 로 새 worktree 생성 시 codegraph 자동 init 동작 확인(현재는 main 로드라 미적용).

# Decisions

- **백그라운드 init** (유지): bootstrap 뒤 `run_in_background`. 조건 = `codegraph` PATH + main worktree(§4.4 `git worktree list
  --porcelain` 첫 worktree)에 `.codegraph/` 존재. 둘 다 만족 시에만 (미사용 레포 무영향).
- **init race 감수**: 백그라운드라 인덱싱 완료 전 dlc 초기 조회는 부분 인덱스/main fallback 을 볼 수 있음(곧 sync) — 진입 비차단 우선이라 감수, skill 에 ⚠️ 명시.
- **daemon 정리: 예방적 → 반응적 → (최종) 자동 kill 폐기·진단/안내** (이유: ① worktree daemon 은 `init`/`status` 로 안 뜨고 idle
  자동종료라 삭제 시점 생존이 드묾, ② 살아있어도 CommandLine 으로 대상 worktree daemon 을 식별 못 해 **오인 kill 방지가 불가능**.
  startedAt↔생성시각 대조 헬퍼로 막을 수 있으나 드문 케이스 대비 복잡도 과함 → 자동 kill 제거가 가장 안전·단순. 사용자 재확인).
  대신 remove 실패를 **stderr 로 분기**: "modified/untracked" → `--force` 확인 / "파일 점유(Access denied·in use·Dir not empty)"
  → codegraph daemon 점유 가능성 안내(세션 닫기·idle 대기·수동 종료; `--force` 는 OS 점유 못 풂) / 부분 성공(디렉토리 잔존) → prune+수동.
- **`.gitignore` 변경 불필요** (whitelist `/*` 로 `.codegraph/` 자동 ignore — 실측).
- **branch 삭제는 remove 성공 후에만** (wt rm 옵션2; codex 지적 반영).
- **헬퍼 스크립트 없음** — 자동 kill 폐기로 불필요, 전부 인라인 지시문.

# Key Files

- `skills/wt/SKILL.md` — §4 "생성" 6번(heal·bootstrap 뒤 백그라운드 init), rm §6(remove 실패 stderr 분기·안내).
- `skills/e/SKILL.md` — "worktree 정리 규칙" 제거 단계(remove 실패 stderr 분기·안내).

# Blockers

없음.
