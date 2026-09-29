---
title: github-sensitive-data-removal
category: entity
created: 2026-09-26
updated: 2026-09-26
sources:
  - https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository (2026-09-26 확인)
  - git-filter-repo 2.47.0 실측 — bare remote(브랜치 2·태그 1), 2026-09-26
  - plans/2026-09-26-repo-audit-g8-g9-docs-ci, PR #177
  - README.md "Secret 실수로 commit/push 한 경우" (절차 정본)
---

# github-sensitive-data-removal

GitHub 에 push 된 비밀을 이력에서 지우는 공식 절차에서, 옛 README 절차를 틀리게 만든 사실들(2026-09-26 확인, git-filter-repo 2.47.0 실측). **명령 순서의 정본은 README 의 유출 대응 절**이고, 여기에는 그 절차가 왜 그렇게 생겼는지만 적는다. 첫 단계는 언제나 token 회수·교체다 — 이력 재작성은 노출을 되돌리지 못한다.

## filter-repo 동작
- **fresh clone 에서만 돈다.** 작업 중인 checkout(worktree·reflog·설치된 훅)에서는 `Please operate on a fresh clone instead` 로 거부한다. `--force` 로 밀면 그 checkout 의 worktree·reflog 에 옛 이력이 남는다.
- 일반 모드는 재작성 뒤 `origin` remote 를 지운다. `--sensitive-data-removal` 은 `origin` 을 남기고 모든 브랜치·태그를 재작성한다.
- `--replace-text` 파일에서 `==>` 가 없는 줄은 그 문자열을 `***REMOVED***` 로 바꾼다.
- 재작성 뒤 `.git/filter-repo/first-changed-commits`·`changed-refs` 가 생긴다. 출력의 First Changed Commit(s) 와 `changed-refs` 의 `refs/pull/*/head` 수가 GitHub Support 요청에 필요하다.

## push 와 그 뒤
- `git push --force --mirror origin` 으로 모든 ref 를 재작성본으로 덮는다. **`main` 만 push 하면 다른 브랜치·태그에 비밀이 남는다**(실측: 브랜치 2·태그 1 에서 mirror push 뒤 모든 ref 0건).
- `--mirror` 는 원격을 그 clone 상태로 덮으므로, 재작성 중에 다른 머신이 push 한 브랜치·커밋이 사라진다 — 시작 전에 다른 push 를 멈춘다.
- `refs/pull/*` 는 GitHub 가 읽기 전용이라 push 가 실패한다(정상). PR ref 와 캐시된 화면은 사용자가 지울 수 없고 Support 포털로 요청한다.
- 옛 이력에서 딴 브랜치는 merge 하지 말고 rebase 한다 — merge 커밋 하나가 옛 이력을 통째로 되살린다(공식 권고).
- fresh clone 에는 로컬 훅이 없어 push 전 가드 스캔이 없다. `git log -p --all -S'<문자열>'` 가 비어 있는지가 push 전 유일한 확인이다. push 는 되돌릴 수 없다.
- 이 repo 는 ruleset `main-guard` 가 main force push 를 막아, 관리자(bypass)로 push 해야 한다.

## 연계
push 뒤 CI 가 사라진 base 를 어떻게 다루는지는 [[ci-secret-scan-backstop]], 되돌릴 수 없는 단계에 확인을 거는 기준은 [[risk-based-approval]], 가드가 추가 줄을 놓치는 경로는 [[git-log-added-lines-hardening]].
