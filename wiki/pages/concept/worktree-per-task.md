---
title: worktree-per-task
category: concept
created: 2026-06-19
updated: 2026-06-19
sources:
  - skills/wt/SKILL.md
  - skills/e/SKILL.md
  - CLAUDE.md (§8 Git/보안)
---

# worktree-per-task

trivial(오타·로그 1줄)이 아닌 모든 작업은 별도 git worktree에서 한다(CLAUDE.md §8). 각 worktree = 1 branch = 1 [[plan-handoff|plan]] = 1 작업. main 직접 작업·진행 중 worktree에 새 작업 얹기를 금지한다.

## 왜 worktree마다인가
한 repo에서 여러 작업을 섞으면 ① 같은 파일 동시 편집 ② 브랜치 전환 시 변경 누수 ③ 테스트가 다른 작업 코드와 상호작용해 결과 해석 불확실. worktree 격리로 셋 다 차단한다.

## wt skill
`/wt <요청사항>` → slug 확인 → `.claude/worktrees/<name>/`에 prefix 없는 브랜치 생성 → main에서 `.env` 복사 → submodule heal + bootstrap → codegraph 인덱스 백그라운드 init → [[dlc-development-cycle]] 시작. `/wt <N>`·기존 이름은 이동, `?` 접두는 질문 모드.

## 안전장치
- worktree 세션 guard hook: worktree 안에서 main repo 소스 Edit/Write 차단(실수 방지).
- 삭제 조건(`/e`): done ∧ clean ∧ pushed ∧ base에 merged 모두 충족 시에만 제안(자동 삭제 안 함).
- **삭제 주의**: `git worktree remove`는 gitignored 파일(`plans/`·`.env`)을 무경고 동반 삭제 → 삭제 전 `git status --porcelain --ignored` 점검, plan은 main으로 먼저 보존.

## 연계
codegraph 자동 init의 race·daemon 점유 이슈는 wt-codegraph-autoinit 작업에서 다룸. plan 보존은 [[plan-handoff]].
