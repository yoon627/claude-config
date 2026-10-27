---
title: e-merge-checks-json — /e merge M5 가 gh 2.50 미만에서도 checks 를 판정한다
status: done
started: 2026-10-27
updated: 2026-10-27
---

# Goal
`/e merge` M5 의 checks 재조회(`gh pr checks <N> --json name,bucket`)가 gh 2.50 미만에서 `unknown flag: --json` 으로 실패해 REJECTED 로 잘못 가는 것을 고친다. 그런 gh 에서도 같은 판정(모든 check 가 통과·건너뜀일 때만 M6, fail·cancel·pending 은 REJECTED)을 낸다.
- Why: `/improve`(2026-10-27) 1순위 — 이 머신의 gh 2.45.0(Ubuntu 패키지)에서 매 `/e merge` 가 이 단계에서 손으로 우회했다(PR #243 등 translate 단위들).
- Constraints: `--json` 이 되는 gh(2.50+)의 동작은 그대로. rtk 가 있는 머신에서 `gh pr checks` 원문 출력은 요약으로 바뀌므로(공용 wiki claude-code-bash-tool-shims) 원문 표 파싱에 기대지 않는다. 사용자 지시(2026-10-26): 추천안대로 끝까지 진행.
- Out of scope: gh 업그레이드(repo 밖 설치) · `--watch` 의 exit code 판정(그대로 동작한다).
- Split: none — 한 줄 규칙 변경이라 나눌 단위가 없다.

# Tasks
- [x] 조사 (2026-10-27) — `--json` 은 gh v2.50.0(cli/cli#9079)에서 추가. 2.45 의 오류 문구 `unknown flag: --json`(exit 1). 2.45 에서도 `gh pr view --json statusCheckRollup` 은 된다. gh 의 bucket 판정(`pkg/cmd/pr/checks/aggregate.go`): SUCCESS→pass, SKIPPED·NEUTRAL→skipping, ERROR·FAILURE·TIMED_OUT·ACTION_REQUIRED→fail, CANCELLED→cancel, 나머지→pending, 중복은 check run 이 이름+workflow+event, status 가 context 로 묶어(따로) `startedAt` 이 가장 늦은 것만 남긴다(code-reviewer 가 v2.45.0·trunk 소스로 확인)
- [x] M5 고치기 (2026-10-27) — `skills/e/SKILL.md` M5 줄 — 처음엔 문장 규칙(이름별 최신, status 는 `createdAt`)이었으나 code-reviewer 가 두 결함을 잡아 `--jq` 식으로 바꿨다: `gh pr view` JSON 은 status 의 생성 시각도 `startedAt` 으로 내보낸다(`api/export_pr.go`), gh 의 중복 기준은 이름만이 아니다. 식은 PR #253 에서 gh 2.45 로 `PASS`, 가짜 rollup 9개(재실행 실패→성공, 다른 workflow 의 cancel, 같은 이름의 status·check run, 진행 중, queued 0시각, status pending, 빈 목록)가 gh 와 같은 판정
- [x] code-reviewer (2026-10-27) — REQUEST CHANGES → `--jq` 식으로 반영, 처분은 `plans/2026-10-27-e-merge-checks-json/e-merge-checks-json-log.md`
- [x] simplify 점검 (2026-10-27) — 문장 규칙을 식 하나로 줄인 것이 곧 단순화, 더 줄일 곳 없음
- [x] 사용자 diff 확인 (2026-10-27) — "커밋 (추천)", Acceptance 1·2·5 변경 포함
- [x] `bash scripts/verify.sh changed`, 수동 검증(대체 경로를 실제 PR 데이터로 돌려 본다) (2026-10-27) — 격리 runner: `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 미설치, 무관), 가짜 rollup 9개 모두 gh 판정과 같음(queued 0시각 행은 시험 파일의 기대값 표기가 틀렸고 gh 도 PASS), PR #253 은 gh 2.45 로 `PASS` — Acceptance 1·2·4 충족
- [x] 머지 (`/e merge`) — 이 PR 의 M5 가 새 대체 경로를 처음 쓴다 (2026-10-27) — PR #254
- [ ] [post-merge] main 세션에서 공용 wiki 갱신 — `docs/worktree-lifecycle.md` §E M5 줄, `pages/decision/e-merge-mode.md` checks 줄, `pages/entity/claude-code-bash-tool-shims.md` rtk 절 끝 줄, `index.md` 35줄(claude-code-bash-tool-shims 요약의 "`--json` 재조회") + log

# Acceptance
1. M5 가 gh 2.50 미만을 다룬다 — `skills/e/SKILL.md` M5 줄 — `unknown flag: --json` 일 때 `gh pr view <N> --json statusCheckRollup --jq <식>` 으로 판정하는 규칙(check 별 최신 하나 — check run 은 이름+workflow, status 는 context, 완료 여부, 통과 값 목록, `NOTPASS`·`NONE`·호출 실패는 REJECTED)이 있고, `--json` 이 되는 경우의 기존 규칙은 그대로
2. 대체 판정이 gh 의 bucket 과 같다 — 이 머신(gh 2.45)에서 PR #253 에 그 식을 gh 로 실행 + 가짜 rollup 경계 사례를 jq 로 실행(`scratchpad/m5-jq/test.sh`) — PR #253 은 `PASS`(같은 PR 의 `gh pr checks 253` 원문 bucket pass·skipping 과 일치), 경계 사례는 gh 의 판정과 같다
3. 실제 사용 — 이 작업의 `/e merge` M5 가 대체 경로로 판정해 M6 로 간다 — 관찰
4. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
5. [post-merge] 공용 wiki 4곳이 새 규칙과 맞는다 — main 세션에서 고친 뒤 `rg -n "name,bucket|--json\` 재조회" /root/.claude/wiki` 의 각 줄이 대체 경로를 함께 적는다

# Decisions
- wiki 결정 [[e-merge-mode]] "checks 는 exit code + `--json name,bucket` 별도 재조회" → 따르고 넓힌다(`--json` 이 안 되는 gh 의 대체 경로를 더한다). 근거: 그 결정 때는 gh 2.50+ 만 가정했다.
- 대체 경로 = `gh pr view <N> --json statusCheckRollup --jq <식>` — gh 와 같은 판정(check 별 최신 하나, 통과 값 SUCCESS·SKIPPED·NEUTRAL)을 식이 계산해 `PASS`/`NOTPASS`/`NONE` 하나만 낸다. 한계: `gh pr view` 가 event 를 내보내지 않아 한 workflow 의 push·pull_request run 은 하나로 묶인다(gh 는 따로 본다). 기각: 문장 규칙(모델이 매번 중복 기준·값 대응을 다시 짜야 하고, 처음 쓴 문장에 두 결함이 있었다 — code-reviewer). 기각: `--json` 없이 `gh pr checks <N>` 원문 표의 둘째 칸 읽기 — gh 가 같은 bucket·중복 제거를 해 주지만 rtk 훅이 있는 머신에서는 출력이 요약으로 바뀐다(공용 wiki claude-code-bash-tool-shims). 기각: 언제나 `statusCheckRollup` 만 쓰기 — 되는 gh 에서는 gh 가 계산한 bucket 이 더 정확하고 기존 동작을 바꿀 이유가 없다.
- 대체 경로가 실패하거나 남은 항목이 0개면 REJECTED — `--watch` 가 exit 0 이었는데 항목이 없으면 판정 근거가 없다(fail-safe, 재실행으로 풀린다).
- 테스트: 문서 규칙이라 새 테스트 없음(§7 예외) — 수동 검증은 Acceptance 2·3. 사용자 diff 확인이 행동 검증.
- Acceptance 1·2·5 문구 변경: 문장 규칙 → `--jq` 식, 검증에 가짜 rollup 경계 사례 추가, post-merge 검색에 `index.md` 35줄 추가(code-reviewer). 사용자 승인(2026-10-27, diff 확인 "커밋 (추천)").
- 커밋 단위: 1개 — `fix(e): judge M5 checks without gh pr checks --json`.
- 롤백: 그 커밋 `git revert`.

# Blockers
