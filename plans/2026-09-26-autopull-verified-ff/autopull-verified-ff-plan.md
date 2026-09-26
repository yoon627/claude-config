---
title: autopull-verified-ff — main push 의 lint 가 통과하면 CI 가 그 sha 를 ci/verified 브랜치에 기록(자동 pull 검증 게이트의 1단계)
status: done
started: 2026-09-26
updated: 2026-09-26
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

SessionStart 자동 pull 이 CI 를 통과한 커밋까지만 ff 하게 만드는 두 단계 중 첫 단계다. main push 의 lint 가 통과하면 CI 가 그 main sha 를 파일 하나(`main-sha`)에 담은 기록 커밋을 `refs/heads/ci/verified` 에 쌓는다. 이 단위는 기록만 한다. 자동 pull·세션 브리프가 기록을 읽는 것은 후속 단위 `autopull-verified-client` 에서 하고, 실제 GitHub 에서 기록이 생기는 것을 본 뒤에 착수한다.

# Intent

- 링크: `plans/2026-09-25-repo-audit-followups/intent.md` 의 `autopull-verified-ff` 단위.
- 사용자 결정(2026-09-26): 1) 방식 "CI 가 검증 표시"(대안 "hook 에서 GitHub API 조회" 기각) 2) 확인 실패 시 "ff 보류 + 브리프 알림 + 검증 끄는 환경변수" 3) GITHUB_TOKEN 제약이 드러난 뒤 "기록 커밋 방식"(대안 PAT·API 조회·보류 기각) — 2 PR 로 나눠 CI 쪽을 먼저 머지·관찰.
- 규모: small(workflow job 1개 + README·wiki, 목적 1). 절차는 medium 에 준해 plan-reviewer 를 거쳤다(권한을 가진 job 이라서).
- 분할: 묶음 → `plans/2026-09-25-repo-audit-followups/intent.md` 에 `autopull-verified-client (미착수)` 줄을 더했다. 이유(plan-reviewer): 클라이언트를 먼저 바꾸면 기록이 생길 때까지 모든 머신의 자동 pull 이 멈춘다. CI 를 먼저 머지하면 클라이언트가 도착할 때 기록이 이미 있고, 기록 job 이 실제 GitHub 에서 동작하는지를 사용자 머신에 영향 없이 확인한다. 기각: 한 PR — 기록 job 이 GitHub 에서만 검증되는데 실패하면 같은 머지로 fleet 가 멈춘다.
- 델타: 쓰기 권한 job 은 checkout·repo 코드 없이 REST API 만 쓴다. 기록 값은 항상 "lint 통과 + 기록 시점에 main 에서 도달 가능" 이어야 한다.
- Out of scope: `session-start-pull.sh`·`session-brief.js` 변경(→ `autopull-verified-client`), `post-checkout` 훅 pull(체크아웃 때 origin/main 을 검증 없이 pull 한다 — 무인 SessionStart 경로만 게이트한다는 것을 client 단위 README 에 명시), `/e` 8단계 pull.

사실 확인(2026-09-26):
- ruleset `main-guard` 는 `~DEFAULT_BRANCH` 에만 걸린다 → `ci/verified` 는 제약 없음. 기본 workflow 권한 `read` → 기록 job 에 `contents: write` 명시 필요. repo 는 public. main push 의 Lint 는 76~121초, 최근 30회 success(plan-reviewer `gh run list`).
- ✅ GITHUB_TOKEN 은 `workflows` 권한을 받을 수 없다(workflow `permissions:` 목록에 없음). REST `POST/PATCH git/refs` 도 공식 권한 표에서 Workflows 추가 권한 대상이라 우회가 아니다. workflow 파일 변경이 걸린 브랜치·태그 갱신이 "refusing to allow a GitHub App to create or update workflow" 로 거부된 사례가 반복된다(researcher). 판정 기준(범위 diff 인지 default tip 비교인지)은 공식 설명이 없다(❌). → main 커밋을 가리키는 ref 를 옮기는 원래 안은 workflow 변경 뒤 멈출 수 있다.
- workflow 파일이 없는 트리의 커밋은 GITHUB_TOKEN 으로 push 된다 — gh-pages 배포 action 들의 표준 경로(선례). 기록 커밋의 트리는 `main-sha` 파일 하나다.
- ✅ 명령줄 refspec 을 준 `git fetch --prune` 은 그 refspec 범위만 지운다(다른 clone 에서 지운 브랜치·살아 있는 대조군으로 재측정). 처음 적은 "설정 refspec 기준으로 다른 추적 ref 도 지운다" 는 같은 clone 의 `push --delete` 가 추적 ref 를 직접 지운 교란이었다(plan-reviewer 지적, git-fetch(1) PRUNING 과도 일치). client 단위의 전제.
- GitHub compare API `compare/{base}...{head}` 의 `status`: ahead/behind/identical/diverged, 없는 sha 는 404(plan-reviewer read-only 확인).

# Acceptance

1. `.github/workflows/lint.yml`: 최상위 `permissions: contents: read`(lint job 은 읽기만). 새 job `record-verified` — `needs: lint`, `if` 는 main push 조건만(암묵 `success()` 유지 — lint 실패·취소면 skip), `permissions: contents: write`, job 수준 `concurrency`(`cancel-in-progress: false`), `timeout-minutes`, checkout 없음, `GH_TOKEN`·`repos/$GITHUB_REPOSITORY` 명시. 단계: `github.sha` 가 지금 main 에서 도달 가능하지 않으면 기록하지 않음 → 현재 기록(`git/matching-refs` 로 정확히 일치하는 항목)이 같은 sha 면 그대로, 기록된 sha 가 main 위에 있고 `github.sha` 보다 새로우면 그대로(늦게 끝난 옛 run) → 아니면 트리 `main-sha` + 부모 = 현재 기록 커밋으로 새 커밋을 만들어 ref 를 생성·ff 갱신. 검증: YAML 파싱·actionlint, 그리고 `bash scripts/record-verified.test.sh`(workflow 의 run 블록을 그대로 꺼내 가짜 `gh` 로 실행) — 첫 기록(ref 없음 → 생성)·전진(→ PATCH)·같은 sha(→ 없음)·늦게 끝난 옛 run(→ 없음)·main 에 없는 sha(diverged·404 → 없음)·기록된 sha 가 main 에 없음(재작성·되감기 → 새 기록)·compare API 오류 3곳(→ job 실패, 기록 불변). API 오류 케이스는 수정 전 run 블록에서 실패(Red).
2. 기록 커밋에는 workflow 파일이 없다(트리 = `main-sha` 하나). 검증: stub 실행에서 트리 생성 호출의 인자 확인.
3. 문서: README CI 절(기록 job·`ci/verified`·client 는 후속·한계·이 단위 단독 되돌리기와 client 합류 뒤 rollback 순서 — 자동 pull 끄기 스위치는 client 단위 몫), wiki 새 decision 페이지(GITHUB_TOKEN 제약·기록 커밋 방식·불변식·기각안), `wiki/index.md`·`wiki/log.md`, intent 의 이 단위 줄 + `autopull-verified-client (미착수)` 줄.
4. 전체: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음), plan-lint 통과. PR CI 가 통과(이 PR 에서는 `record-verified` 가 skip 돼야 한다 — pull_request 이벤트).
- [ ] [post-merge] 이 PR 의 머지 push 에서 `record-verified` 가 성공하고 `origin/ci/verified:main-sha` 가 그 머지 커밋 sha 인지(`git fetch origin ci/verified && git show FETCH_HEAD:main-sha`). 실패하면 client 단위를 착수하지 않는다 — 관찰 주체는 client 단위 착수 시점(intent `(미착수)` 줄 메모).

# Progress

- 2026-09-26: 착수. ruleset·workflow 권한·refspec 실측, 사용자 설계 결정.
- 2026-09-26: plan-reviewer CONDITIONAL — 강 5(표시가 main 밖 커밋을 가리킬 수 있음·prune 실측 교란·GITHUB_TOKEN workflows 권한 ⚠️·CI 먼저 분할·rollback 없음)·약 다수. researcher 로 권한 제약 확인 → 사용자 결정 "기록 커밋 방식 + 2 PR". prune 재측정으로 교란 확인·사실 정정. plan 을 1단계(CI 기록) 범위로 재작성.
- 2026-09-26: `record-verified` job 작성(순서: job 을 먼저 쓰고 하니스를 뒤에 — plan 에 적은 "하니스 먼저" 와 다르다). scratch 하니스가 lint.yml 의 run 블록을 그대로 꺼내 가짜 `gh`(main 이력·기록 상태 흉내)로 8 분기 실행 → 8/8(처음 4건 실패는 하니스의 트리 검사 버그 — 수정). mutation 2개(main 밖 sha 가드 제거·"더 새 기록 유지" 제거)가 각각 해당 케이스를 실패시킴. YAML 파싱: 최상위 `contents: read`, job `needs`·`if`·`permissions`·`concurrency`·`timeout-minutes` 확인. README CI 절·wiki 새 decision 페이지·index·log, check_links clean.
- 2026-09-26: code-reviewer(Codex 미가용) REQUEST CHANGES — Major 2(API 오류를 삼켜 green 무기록·기록 후퇴 — 502 주입 재현, 하니스가 scratch 에만 있음), Minor 4, Nit 6, refuted 11. fix: 404 만 main 밖·나머지 job 실패·비교 결과 변수화, `scripts/record-verified.test.sh` 로 승격(11 케이스, 수정 전 run 블록에서 API 오류 3건 Red → 수정 후 11/11), 주석·README·wiki hedge·한계·단독 되돌리기. shellcheck ok.
- 2026-09-26: 최종 검증(격리 runner) — `record-verified.test.sh` 11/0, `verify.sh` 마지막 줄 `ALL PASS`(skip 없음, 새 테스트 `ok`), actionlint 0 finding, plan-lint 0, wiki link clean, 수정 전 run 블록은 API 오류 3건만 실패. runner 대조 어긋남 없음. evidence gate: Acceptance 1~4 충족, [post-merge] 1건 남음. 판정 DONE(통합 대기).
- 2026-09-26: 커밋 `b8bd8bc`, 사용자 선택 `/e merge` → PR #179. [post-merge] 관찰 결과는 머지 보고와 client 단위 착수 시점에 기록.

# Next

(없음 — PR #179 머지로 종료. [post-merge] 관찰은 client 단위의 착수 조건)

# Decisions

- 기록 방식: `refs/heads/ci/verified` 에 기록 커밋을 쌓는다(트리 = `main-sha` 파일, 부모 = 직전 기록). 이유: 기록 커밋은 workflow 파일을 담지 않아 GITHUB_TOKEN 으로 갱신할 수 있고(gh-pages 선례), 부모를 이어 ff 로만 움직이므로 force 가 필요 없다. main 이력과 연결되지 않아 `branch -r --contains`(`/e` 정리 신호)에도 섞이지 않는다.
- 불변식: 기록 값은 "lint 통과 + 기록 시점에 main 에서 도달 가능". 재작성·되감기로 main 에서 사라진 커밋의 run 이 늦게 끝나거나 re-run 돼도 기록하지 않는다(public repo 에서 지운 커밋을 다시 가리키지 않게). 기록된 sha 가 main 밖이면(재작성) 새 sha 를 기록한다. client 도 기록 sha 가 origin/main 의 조상인지 확인한다(client 단위). 기각: 옛 표시와만 compare 하는 규칙 — 재작성 뒤 diverged→force 로 main 밖 커밋을 표시하고, 되감기를 "늦게 끝난 옛 run" 으로 오판한다(plan-reviewer).
- 기록 job 은 REST API 만 쓴다(checkout·repo 스크립트 없음). 이유: 쓰기 토큰을 가진 job 에서 repo 코드를 실행하지 않는다. ~~대가: 로직을 repo 테스트로 잠글 수 없어~~ → 로직은 `scripts/record-verified.test.sh` 가 workflow 의 run 블록을 그대로 꺼내 가짜 `gh` 로 검사하고, 그 테스트는 읽기 권한 lint job(verify.sh bash 축)에서 돈다 (이유: code-reviewer — 쓰기 job 이 repo 코드를 안 돌리는 것과 테스트를 repo 에 두는 것은 충돌하지 않는다). 테스트는 jq 가 없으면 이유를 밝히고 실패한다(verify.sh 의 "조용히 건너뛰지 않는다").
- API 오류는 compare 의 404(main 밖·공통 조상 없음 — `gh: Not Found (HTTP 404)`, rc 1, 2026-09-26 실측)만 "main 밖" 으로 보고, 그 밖은 job 실패. 순서 비교 결과는 변수로 받아 `set -e` 가 잡게 한다. 이유: code-reviewer 502 주입 재현 — green 인 채 기록이 멈추거나 m3→m2 로 뒤로 갔다.
- 한계로 둔다: 연속 push 에서 대기 중인 기록 job 이 concurrency 교체 규칙으로 취소되면 tip 은 다음 push 까지 기록되지 않는다(불변식은 유지). 기각: `queue: max` — job 수준 지원·actionlint 인식이 확인되지 않았다(⚠️).
- `ci/verified` 삭제는 일시 정지(다음 green main push 가 새 root 기록을 만든다). 영구 정지 수단은 client 단위에서 정한다.
- concurrency 는 job 수준. 이유: workflow 수준이면 lint run 이 취소돼 main push 의 비밀 스캔이 빠진다(그 push 는 다시 스캔되지 않는다).
- Rollback: 이 단위만 머지된 동안은 기록을 읽는 쪽이 없어 job revert(+ `ci/verified` 브랜치 삭제)로 된다. client 단위 머지 뒤에는 **client revert 먼저 → 기록이 그 revert 커밋까지 전진한 것을 확인 → job 제거** 순서여야 한다(push 이벤트는 push 된 커밋의 workflow 로 돈다 — 한 push 에 담으면 그 커밋에는 기록 job 이 없어 revert 가 자동 pull 로 전달되지 않는다). 원격 정지 레버: `ci/verified` 삭제(client 가 prune 으로 보류).
- 기각: PAT(workflows 권한) — 만료·발급 관리, 만료 시 자동 pull 정지(사용자 선택). 기각: hook 에서 check-runs API 조회 — HTTP·JSON·프록시(git 설정을 따르지 않음)가 회사 PC 에서 막힐 수 있다(사용자 선택). 기각: 태그·커스텀 ref 로 main 커밋 가리키기 — 같은 권한 검사를 받는다(researcher: 태그 ✅, 커스텀 ref ⚠️ 증거 없음).
- 커밋 단위: 1개 — `ci: record the main commit that passed lint on ci/verified`.

# Key Files

- `.github/workflows/lint.yml` — 최상위 permissions, `record-verified` job.
- `scripts/record-verified.test.sh`(신규) — run 블록 검사.
- `README.md` — CI 절, 트리.
- `wiki/pages/decision/autopull-verified-ff.md`(신규), `wiki/pages/decision/git-hook-network-safety.md`(링크 1줄), `wiki/index.md`, `wiki/log.md`.
- `plans/2026-09-25-repo-audit-followups/intent.md` — 이 단위 줄, `autopull-verified-client (미착수)`.

# Review Disposition

- [plan] 강1 표시가 main 밖 커밋을 가리킬 수 있음(재작성 뒤 diverged→force, 되감기 오판, client 조상 미확인) — fix(불변식·main 위 확인, client 조상 확인은 client 단위).
- [plan] 강2 prune 실측 교란 — fix(다른 clone 삭제·대조군으로 재측정, 사실 정정, Workflow Findings).
- [plan] 강3 GITHUB_TOKEN workflows 권한 ⚠️ — researcher 로 확인 → 사용자 결정 "기록 커밋 방식".
- [plan] 강4 CI 먼저 분할 — fix(이 단위 = CI 기록, client 는 `(미착수)`).
- [plan] 강5 rollback 없음·한 push 함정 — fix(Decisions Rollback, README).
- [plan] 약: job 수준 concurrency·`GH_TOKEN`·`matching-refs`·`timeout-minutes`·`if` 조건 — fix. 테스트 하니스 env 제거·FETCH_HEAD 서술·브리프 처방·post-checkout 근거·`[skip ci]`·fork·새 decision 페이지 — client 단위 몫은 intent 메모로, 새 decision 페이지는 fix.
- [code] Major API 오류 삼킴 — fix(404 만 main 밖, 그 밖 job 실패, 비교 변수화, 테스트 3건). Major 하니스 scratch — fix(`scripts/record-verified.test.sh`).
- [code] Minor pending 교체로 tip 미기록 — wontfix(한계로 문서화, `queue: max` 는 미확인). Minor 정지 레버 일시성 — fix(Decisions·wiki 한계, 영구 정지는 client 단위). Minor gh-pages 선례 단정 — fix(REST 경로는 머지 후 확인으로 hedge). Minor Acceptance 3 끄기·단독 rollback — fix(README·Acceptance 문구).
- [code] Nit 주석 현재형 — fix. README 문장 위치 — fix(별도 문단). `ci` 브랜치 충돌·`git branch -r` 노출 — fix(README·wiki 한계). `[skip ci]` — fix(README 한계, client 메모). TOCTOU — wontfix("기록 시점에" 로 충분, 다음 run·client 조상 확인이 복구).
- [code] Codex 미가용(크레딧 소진) — Claude 리뷰만으로 처분(§9 생략 사유).

# Blockers

# Deferred

# Workflow Findings

- 설계 전제를 교란된 실측으로 확정했다 — prune 범위를 같은 clone 의 `push --delete` 로 만든 상태에서 재서 "다른 추적 ref 도 지운다" 로 적었다(plan-reviewer 가 공식 문서와의 충돌로 잡음). 오늘 적립한 "검사식은 알려진 양성 샘플·같은 실행 경로로 먼저 확인" 과 같은 계열 — 실측은 교란 변수(같은 clone 의 부수 효과)를 뺀 대조군과 함께 설계한다.
