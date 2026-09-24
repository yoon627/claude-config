---
title: commit-restructure-plumbing-cas
category: decision
created: 2026-09-24
updated: 2026-09-24
sources:
  - plans/2026-09-24-commit-check-skill/commit-check-skill-plan.md (Decisions·Review Disposition)
  - skills/commit-check/commit_units.py
  - plan-reviewer·code-reviewer scratch 실측 2026-09-24 (git 2.54.0)
---

# commit-restructure-plumbing-cas

커밋 경계를 재구성(합치기·파일 단위 분할·순서·메시지 수정)할 때는 **사용자 worktree 에서 rebase 하지 않는다.** plumbing 으로 새 커밋을 만들고, 모든 검증을 통과한 뒤에만 ref 를 트랜잭션 하나로 옮긴다. `commit-check` 스킬(`skills/commit-check/commit_units.py`)이 이 방식을 쓴다.

## 방식

1. 새 커밋마다 원본 커밋을 현재 tip 위에 3-way 로 적용한다: `git merge-tree --write-tree --merge-base=<원본 부모> <tip> <원본>`. 파일 단위 분할은 부모 tree 에 해당 경로만 원본 상태로 바꾼 **합성 커밋**을 임시 `GIT_INDEX_FILE` 로 만들어 같은 방식으로 적용한다(삭제는 `--index-info` 의 mode 0 레코드 — cwd 와 무관하게 루트 기준).
2. `git commit-tree --no-gpg-sign` 으로 커밋을 만들고 author 이름·메일·날짜는 원본 값, 트레일러는 중복 없이 합친다.
3. 최종 tree OID 가 원래 HEAD 와 같고 커밋별 파일이 계획 범위 안인지 확인한다.
4. `git update-ref --stdin` 트랜잭션 하나로 백업 ref 생성·오래된 백업 삭제·브랜치 CAS(`update refs/heads/<br> <new> <old>`)·그 브랜치 upstream ref `verify` 를 함께 처리한다.

사용자 index·작업트리는 한 번도 건드리지 않는다. 트리가 같으므로 옮긴 뒤에도 그대로 유효하고(dirty 상태 포함), 실패하면 만든 객체를 버리기만 하면 된다.

## 왜 rebase 가 아닌가 (실측)

[[dual-review-plan-and-code]] 의 plan-reviewer 가 scratch repo 에서 재현했다.
- `rebase -i` 의 `exec` 로 분할하다 재커밋이 실패하면, 원 커밋이 추가했던 파일이 untracked 로 남아 `git rebase --abort` 가 exit 128 로 실패한다. worktree 는 detached + `rebase-merge` 잔존 상태로 남는다. 브랜치 ref 는 그대로지만 사용자 작업 공간이 망가진다.
- 분할 재커밋은 author·날짜·`Co-Authored-By` 트레일러를 잃는다 — 최종 tree 비교로는 안 잡힌다.
- 셸 스크립트로 분할하면 `set -e` 가 `a && b` 의 왼쪽 실패에서 멈추지 않아, 강제 추가된 ignored 파일이 빠진 채 rebase 가 exit 0 으로 끝난다.
- 파일을 고치는 pre-commit hook(prettier·eslint --fix·ruff format)이 있는 repo 는 재커밋마다 중간 상태를 고쳐 트리 불변식을 깬다. `commit-tree` 는 hook 을 돌리지 않고, 새로 생기는 내용은 메시지뿐이라 메시지에만 `git hook run commit-msg` 를 돌린다.

기각한 다른 안: 임시 worktree 에서 rebase 후 ref 이동(체크아웃·hook·정리 비용), `commit --fixup` + `rebase --autosquash`(합치기만 되고 in-place 문제 동일), 새 브랜치에 `checkout <backup> -- <files>` 재조립(파일이 여러 커밋에 걸쳐 변하면 중간 상태 재현 불가).

## 함정 (구현 중 실측)

- **symref 를 트랜잭션에 넣지 않는다.** 원격 ref 전체를 `verify` 하면 clone 이 만드는 `refs/remotes/origin/HEAD`(→ `origin/main`) 때문에 `multiple updates … via symref` 로 트랜잭션이 항상 거부됐다(code-reviewer 재검토 실측). 필요한 것은 "이 브랜치가 그 사이 push 됐나"뿐이라 각 remote 의 `refs/remotes/<remote>/<branch>` 만 verify 한다(없으면 zero OID — 처음 push 경합도 잡는다).
- **`merge-tree` 충돌은 exit code 로 판정한다.** 충돌이어도 첫 줄에 (충돌 마커가 든) tree OID 가 찍힌다.
- **범위는 `--all` 이 아니라 명시 ref 로.** 자기 백업 ref(`refs/commit-check/*`)가 범위를 잠근다. 다른 로컬 브랜치·원격·태그를 명시 열거해 제외하고, 게시된 커밋은 불변으로 둔다(force-push 경로 제거).
- **백업 정리는 직속 이름만.** `refs/commit-check/<branch>/` 로 for-each-ref 하면 `<branch>/x/...` 다른 브랜치 백업이 섞여 방금 만든 자기 백업을 지웠다.

## 관련

- 장치를 없애거나 바꾸기 전에 도입 목적부터 확인한다는 교훈: [[lesson-verify-scaffold-purpose-before-removal]].
- `fixup!` 커밋의 합칠 대상(`fixup_of`)은 git autosquash 의 실측 규칙을 근사한다: [[git-autosquash-target-selection]].
- 이 세션처럼 worktree 격리 가드가 있으면 raw git 을 모델이 치기 어렵다 — 판정에 필요한 정보(`collect`·`show`)를 스크립트가 주는 이유: [[worktree-isolation-bash-guard]].
- 미게시 로컬 이력 재작성은 되돌릴 수 있어 [[risk-based-approval]] 기준으로는 확인 대상이 아니지만, 재구성 전 승인은 사용자가 명시적으로 정했다(2026-09-24).
