---
title: autopull-verified-ff
category: decision
created: 2026-09-26
updated: 2026-09-26
sources:
  - plans/2026-09-26-autopull-verified-ff (plan-reviewer·researcher, 사용자 결정 3건)
  - .github/workflows/lint.yml (record-verified job)
  - https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens (Workflows 권한 대상 endpoint, 2026-09-26 확인)
  - https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax (permissions 목록에 workflows 없음, 2026-09-26 확인)
---

# autopull-verified-ff

SessionStart 자동 pull 은 origin/main 을 CI 결과와 무관하게 ff 하고, 그 훅 코드는 다음 세션에 바로 실행된다. ruleset `main-guard` 는 관리자 bypass 라 소유자의 lint 미통과 push 를 막지 못한다. 그래서 **CI 가 통과시킨 커밋만 자동 pull 이 따라가게** 한다(2026-09-26 사용자 결정). 두 단계다 — 1단계(이 결정): CI 가 기록한다. 2단계(`autopull-verified-client`, 미착수): 자동 pull·세션 브리프가 기록을 읽는다.

## 결정
- **기록 커밋 방식.** main push 의 lint 가 통과하면 `record-verified` job 이 `refs/heads/ci/verified` 에 기록 커밋(트리 = `main-sha` 파일 하나, 부모 = 직전 기록)을 쌓는다. 자동 pull 은 그 sha 가 origin/main 의 조상일 때만 그 커밋까지 ff 한다(2단계).
- **왜 main 커밋을 가리키는 ref 가 아닌가.** GITHUB_TOKEN 은 `workflows` 권한을 받을 수 없다(workflow `permissions:` 목록에 없음 ✅). REST `POST/PATCH git/refs` 도 공식 권한 표에서 Workflows 추가 권한 대상이라 git push 의 우회가 아니다 ✅. workflow 파일 변경이 걸린 브랜치·태그 갱신이 `refusing to allow a GitHub App to create or update workflow … without workflows permission` 으로 거부된 사례가 반복된다 ⚠️(판정 기준 — 범위 diff 인지 default tip 비교인지 — 은 공식 설명이 없다 ❌). workflow 파일이 없는 트리의 커밋은 gh-pages 배포 action 들이 GITHUB_TOKEN 으로 늘 push 하는 형태다(그 선례는 git push 경로 — 이 job 의 REST 경로는 머지 후 첫 기록으로 확인).
- **불변식: 기록 값은 "lint 통과 + 기록 시점에 main 에서 도달 가능".** `compare/<sha>...main` 이 ahead·identical 일 때만 기록한다. 재작성·되감기로 main 에서 빠진 커밋의 늦은 run·re-run 은 기록하지 않는다(public repo 에서 유출 대응으로 지운 커밋을 다시 가리키지 않게). 기록된 sha 가 main 밖이면(재작성) 새 sha 를 기록하고, main 위의 더 새 커밋이 기록돼 있으면 되돌리지 않는다.
- **최소 권한.** 워크플로 최상위는 `contents: read`, 기록 job 만 `contents: write`. 그 job 은 checkout·repo 코드 없이 REST API 만 쓴다. concurrency 는 job 단위(workflow 단위면 lint 가 취소돼 그 main push 의 비밀 스캔이 빠진다).
- **CI 먼저, client 나중.** client 를 먼저 바꾸면 기록이 생길 때까지 모든 머신의 자동 pull 이 멈춘다. 기록 job 은 GitHub 에서만 검증되므로 실제 기록이 생기는 것을 본 뒤 client 를 머지한다.
- **Rollback 순서.** client 머지 뒤에는 client revert → 기록이 그 커밋까지 전진한 것 확인 → job 제거. push 이벤트는 push 된 커밋의 workflow 로 돌아, 한 push 에 담으면 revert 가 전달되지 않는다.
- **API 오류는 삼키지 않는다.** compare 의 404(main 밖·공통 조상 없음)만 "main 밖" 으로 보고 그 밖의 오류는 job 을 실패시킨다. 처음 구현은 `2>/dev/null || return 1` 과 `[ ]` 안 치환이라 5xx 에서 green 인 채 기록이 멈추거나 뒤로 갔다(code-reviewer 가 502 주입으로 재현). run 블록은 `scripts/record-verified.test.sh` 가 workflow 에서 그대로 꺼내 가짜 `gh` 로 검사한다 — 쓰기 job 은 repo 코드를 돌리지 않지만 테스트는 읽기 권한 lint job 에서 돈다.

## 한계
- 연속 push 에서 대기 중인 기록 job 은 GitHub concurrency 의 교체 규칙(pending 은 하나만, 새로 들어온 것이 기존 pending 을 취소)으로 취소될 수 있다 — 늦게 끝난 옛 커밋의 job 이 더 새 tip 의 job 을 밀어내면 tip 은 다음 main push 까지 기록되지 않는다(불변식은 유지된다). `[skip ci]` push 도 기록되지 않는다.
- `ci/verified` 삭제는 **일시** 정지다 — 다음 green main push 가 새 root 기록을 만든다. 영구 정지 수단은 client 단위에서 정한다.
- 원격에 `ci` 브랜치는 만들 수 없다(경로 충돌). `git branch -r` 에 `origin/ci/verified` 가 늘 보인다(작업 브랜치 점검 때 걸러낸다).
- REST `POST git/refs` 로 workflow 파일이 없는 root 커밋 브랜치를 만들 수 있는지는 머지 후 첫 기록으로만 확정된다 ❌ — 실패하면 job 이 빨간불로 드러난다.

## 기각
- workflows 권한 PAT — 발급·만료(최대 1년) 관리, 만료 시 자동 pull 정지.
- 훅에서 check-runs API 조회 — HTTP·JSON·프록시 처리가 훅에 들어가고, git 의 프록시 설정을 따르지 않아 회사 PC 에서 막힐 수 있다. CI 가 도는 동안에는 ff 하지 못한다.
- 태그·커스텀 ref 로 main 커밋 가리키기 — 태그는 같은 거부 사례가 있다 ✅, 커스텀 ref 는 증거 없음 ⚠️.
- 옛 표시와만 compare 하는 갱신 규칙 — 재작성 뒤 diverged→force 로 main 밖 커밋을 표시하고, 되감기를 "늦게 끝난 옛 run" 으로 오판한다(plan-reviewer).

## 실측으로 정정한 것
- 명령줄 refspec 을 준 `git fetch --prune` 은 그 refspec 범위만 지운다(git-fetch(1) PRUNING). 처음에 "다른 추적 ref 도 지운다" 로 적었던 것은 같은 clone 에서 `push --delete` 를 해 추적 ref 가 직접 지워진 교란이었다 — 다른 clone 에서 지우고 살아 있는 대조군을 두어 재측정했다([[lesson-grep-absence-not-proof]] 사례 4 와 같은 계열: 검사를 교란 없는 조건에서 먼저 확인).

## 연계
자동 pull 의 hang·재귀 안전 설계는 [[git-hook-network-safety]], 비밀 스캔 백스톱은 [[ci-secret-scan-backstop]], 되돌릴 수 없는 단계의 확인 기준은 [[risk-based-approval]].
