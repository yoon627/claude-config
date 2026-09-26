---
title: ci-secret-scan-backstop
category: decision
created: 2026-09-26
updated: 2026-09-26
sources:
  - scripts/ci-secret-scan.sh, scripts/ci-secret-scan.test.sh, .github/workflows/lint.yml
  - plans/2026-09-26-repo-audit-g8-g9-docs-ci (Decisions·Review Disposition), PR #177
  - plans/2026-09-26-push-remote-scope (가드 제외 기준 변경 → 임시 repo 제거·shallow 거부)
---

# ci-secret-scan-backstop

로컬 pre-push 가드(`pre-commit-check.sh pre-push`)를 건너뛴 push(훅 미설치·`--no-verify`·다른 머신)를 **사후에** 잡기 위해, CI 에서 같은 가드를 push 범위에 다시 돌린다(2026-09-26, PR #177). 차단이 아니라 탐지다 — 잡혔을 때는 이미 공개됐으므로 token 회수가 먼저다([[github-sensitive-data-removal]]).

## 결정과 근거
- **base 를 가드에 push 대상의 remote sha 로 넘기고 checkout 에서 바로 부른다**(2026-09-26 push-remote-scope). 가드는 stdin 각 줄의 remote sha 가 가리키는 커밋만 "이미 공개됨" 으로 빼고 추적 ref 는 보지 않으므로, CI checkout(`fetch-depth: 0`)의 `refs/remotes/origin/<브랜치>` 가 검사할 커밋을 이미 담고 있어도 스캔이 비지 않는다.
  - 대체 기록: PR #177 에서는 가드가 `<push 커밋> --not --remotes` 를 스캔해 checkout 에서 부르면 아무것도 보지 않았다. 그래서 checkout 의 객체를 alternates 로 빌린 임시 bare repo 에 base 하나만 추적 ref 로 두고 돌렸다(임시 clone 은 detached merge 커밋에 닿지 않을 수 있어 기각). 가드가 추적 ref 를 보지 않게 되면서 이 장치를 없앴다.
- **shallow checkout 이면 실패한다.** 임시 repo 는 checkout 의 shallow 목록을 물려받지 않아 부모 누락이 `git log failed` 로 차단됐지만, 직접 호출은 shallow 경계를 root 로 보고 조용히 좁게 스캔한다(plan-reviewer). 지금은 `fetch-depth: 0` 이 지키고, 스크립트가 `rev-parse --is-shallow-repository` 로 한 번 더 막는다.
- **PR 은 `pull_request.head.sha` 를, checkout 된 merge 커밋의 `HEAD^1` 기준으로 스캔한다.** merge 커밋을 스캔하면 가드의 `-m` 이 main 쪽 추가분을 PR 탓으로 다시 잡는다. payload 의 `base.sha` 는 이벤트 시점 값이라 rebase 뒤 옛 값일 수 있다(code-reviewer) — merge ref 의 첫 부모가 그 merge 를 만든 base tip 이다.
- **base 가 없으면(force push 로 사라짐·새 브랜치의 0 sha) 전체 이력을 스캔한다.** 실패로 두면 README 의 재작성 절차를 따르는 순간 main CI 가 빨개지고 필수 check 에 걸린다. 전체 이력은 범위가 넓어지는 쪽이라 fail-closed 가 유지되고, 이 repo 에서 약 1초·clean 이다([[lesson-gate-safe-side-first]]).
- **CI 로그에서 매치 값을 가린다.** public repo 의 Actions 로그는 공개이고 가드는 매치 값을 30자까지 찍는다. 패턴 이름에 `)` 가 있어(`GitHub PAT (fine)`) 이름은 `[^:]*` 로, 값에 탭이 있을 수 있어 나머지는 `.*` 로 치환한 뒤 색 리셋(ESC`[0m`)을 다시 붙인다. 로컬 전용인 `--no-verify` 안내 줄은 지운다.
- **`if: ${{ !cancelled() }}`** — 조건이 없으면 앞 테스트 step 이 실패할 때 스캔이 skip 되고, 그 main push 는 다시 스캔되지 않는다.
- stdin 의 ref 이름은 `refs/heads/ci-scan` — 가드의 main/master 직접 push 차단을 피한다.

## 한계 (알고 둔 것)
- main push 범위의 merge 커밋은 가드의 `-m` 때문에 main 쪽에 이미 있던 토큰 줄을 다시 잡는다(main 에 토큰이 남아 있을 때만 — 해법은 재작성).
- CI 는 그 PR 자신의 가드로 검사한다 — 가드를 약화한 PR 은 스스로 통과한다(accepted-risk, 1인 소유).
- PR·main push 만 본다. PR 없이 push 한 feature 브랜치는 대상이 아니다(기각: 모든 브랜치용 workflow — 비용 대비 드묾).
- 가드와 CI 스크립트는 한 커밋으로 묶여 있다 — 가드만 되돌리면 checkout 의 추적 ref 때문에 스캔이 비고, 그것을 `ci-secret-scan.test.sh` 의 "추적 ref 에 이미 있는 PR 커밋 차단" 이 잡아 CI 가 빨개진다.

## 기각한 대안
- PR diff 의 추가 줄을 별도 grep 으로 스캔 — 가드와 패턴·예외가 갈라져 두 곳을 유지해야 한다.
- merge 커밋 스캔을 인정하고 문구만 고침 — 거짓 차단 가능성이 남는다.

## 연계
가드가 추가 줄을 놓치는 경로와 막는 옵션은 [[git-log-added-lines-hardening]], 게이트를 고칠 때 안전측부터 정하는 원칙은 [[lesson-gate-safe-side-first]].
