---
title: worktree-per-task
category: concept
created: 2026-06-19
updated: 2026-09-04
sources:
  - skills/wt/SKILL.md
  - skills/e/SKILL.md
  - CLAUDE.md (§8 Git/보안)
---

# worktree-per-task

코드/파일을 바꾸는 모든 작업은 **규모 불문** 별도 git worktree에서 한다(CLAUDE.md §8 — 2026-09-04 trivial 포함으로 확대. 그전까지는 trivial 제외였다). 각 worktree = 1 branch = 1 [[plan-handoff|plan]] = 1 작업. main 직접 작업·진행 중 worktree에 새 작업 얹기를 금지한다.

## 왜 worktree마다인가
한 repo에서 여러 작업을 섞으면 ① 같은 파일 동시 편집 ② 브랜치 전환 시 변경 누수 ③ 테스트가 다른 작업 코드와 상호작용해 결과 해석 불확실. worktree 격리로 셋 다 차단한다.

## wt skill
`/wt <요청사항>` → slug 파생(확인 없음 — [[risk-based-approval]]) → `.claude/worktrees/<name>/`에 prefix 없는 브랜치 생성 → main에서 `.env` 복사 → submodule heal + bootstrap → codegraph 인덱스 백그라운드 init → [[dlc-development-cycle]] 시작. `/wt <N>`·기존 이름은 이동, `?` 접두는 질문 모드.

## 안전장치
- worktree 세션 guard hook: worktree 안에서 main repo 소스 Edit/Write 차단(실수 방지). **2026-08-12 실측으로 이 기능은 네이티브 worktree 격리(v2.1.222)가 더 넓게 덮는 것이 확인됐다 — `retire` 후보([[native-overlap-ledger]] 1b).** 비-worktree 세션의 main 직접편집 `ask` 는 교집합이 없어 유지.
- 삭제 조건(`/e`): done ∧ clean ∧ pushed ∧ base에 merged 모두 충족 시에만 제안(자동 삭제 안 함).
- **삭제 주의**: `git worktree remove`는 gitignored 파일(`.env` 등)을 무경고 동반 삭제(`plans/` 는 tracked 라 미커밋이면 remove 가 거부한다 — CLAUDE.md §8) → 삭제 전 `git status --porcelain --ignored` 점검, plan은 main으로 먼저 보존.

## 연계
codegraph 자동 init의 race·daemon 점유 이슈는 wt-codegraph-autoinit 작업에서 다룸. plan 보존은 [[plan-handoff]].

worktree 를 **작업마다** 가르는 규율이 지켜지지 않으면 같은 기능을 두 브랜치가 각자 구현하는 사고가 난다 — 실제 사례와 착수 전 점검 절차는 [[lesson-parallel-duplicate-implementation]].
