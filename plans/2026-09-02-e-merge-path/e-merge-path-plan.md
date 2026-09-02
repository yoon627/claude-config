---
title: e-merge-path — /e 에 push·PR·머지 마무리 경로(머지 모드) 추가 + 호출측(CLAUDE.md §3-6·§8, dlc Report) 정합
status: in_progress
started: 2026-09-02
updated: 2026-09-02
---

# Goal
CLAUDE.md §3-6 과 dlc Report 가 "push·PR·머지는 `/e` 로" 위임하는데 `skills/e/SKILL.md` 에는 그 경로가 없다(경계 절 "push 안 함"만 있음). `/e merge` 머지 모드를 정의해 push → PR → plan done 커밋 → CI 대기 → merge → fetch·머지 확인 → 정리를 규약화하고(실패 시 plan 복구 규칙 포함), 호출측(CLAUDE.md §3-6·§8 `--delete-branch` 문장, dlc Report 의 원격 자동삭제 문구·step 번호)·README 를 동기화한다.

# Progress
- 2026-09-02: `/improve` 후보 1 승인 → worktree 생성, 규모 medium. 실측 흐름(PR #147 세션)을 기준으로 draft plan.
- 2026-09-02: plan-reviewer(+codex medium) NO-GO, blocker 4 — (1) `collect-state.sh` 에 fetch 가 없어 `gh pr merge`(서버 머지) 후 7단계 merged 판정이 로컬 ref 기준으로 결정적 실패(PR #147 세션에선 수동 fetch 로 우연히 통과) (2) 머지 전 `status: done` 은 §10 "머지 시점에 done" 과 충돌 + 머지 실패 시 복구 절차 부재, 근거로 든 session-brief 는 3일 임계라 서술 부정확 (3) §8 격리 한 줄의 인과가 리뷰어 실측 4회로 반증 — 거부 트리거는 경로가 아니라 명령 텍스트의 git 언급(`--skip-git-repo-check` 플래그명만으로 거부)이며 비결정적·하네스 버전 의존 (4) `skills/dlc/SKILL.md:120` 이 "직접 수행한 merge 직후 원격 tip 삭제 자동 정리" 를 허용해 §8(b) 원격 삭제 항상-확인과 충돌 — `/e merge` 가 생기면 상시 경로가 되어 활성화. 약한 우려: `push`/`PR` alias 가 승인 범위 초과, 재실행·기존 PR·checks 없음/timeout·mergeable·squash-only 미정의, Acceptance 가 grep 순환, 머지 모드에 acceptance 게이트 없음.

- 2026-09-02: 재검토 CONDITIONAL GO(B1~B4 해소, 조건 3+minor 4 → Decisions 반영) → 구현: `skills/e/SKILL.md` 모드 절·M1~M6·경계, `docs/worktree-lifecycle.md` §E+헤더 정정, CLAUDE.md §3-6/§8, dlc SKILL :119-120, README bullet (5 files, +58/-12). plan-lint 통과.
- 2026-09-02: code-reviewer(+codex medium) REQUEST CHANGES(Major 6·Minor 12·Nit 2) → fix loop 2회(M2/M3 재배치·M6 4분류·`<default>`·M5 exit code·description·조건4 override·`/c` 예외5 등) → **APPROVE**(잔여 Minor 1·Nit 1 도 반영). simplify: M6 `--delete-branch` 근거를 §8 포인터로 축약(동작 불변). 6 files +73/-21. acceptance 항목은 `[post-merge]` smoke 하나만 남기고 전부 충족.

# Next
- `/e merge` 로 마무리(새 규약의 첫 실행 = smoke). 결과를 관찰해 규약대로 M1~M6·fetch·7단계 자동 정리가 되는지 확인, 어긋나면 `# Workflow Findings` 기록.

# Decisions
- **트리거는 `/e merge`·`/e 머지` 만** (2026-09-02 사용자 확정 — 원안 `push`·`PR` alias 는 제거. 이유: `/e push` 를 머지 승인으로 해석하면 §1 비가역·외부공개 확인 위반). 그 외 `/e` 는 체크포인트 모드 그대로 — "push 안 함" 기본값 유지, 머지 모드는 `/e merge` 명시 인자 자체가 push·PR·머지 지시(§8 "push 는 요청 시만" 충족). `git push` 의 `permissions.ask` 가 뜨면 그것도 게이트, 거부되면 중단·plan 무변경.
- **머지 모드 진입 게이트(hard-stop, 닫힌 목록)**: 브랜치가 main/master/detached · plan 없음 · `# Acceptance` 에 미체크 항목 · `gh` 미인증 또는 remote 가 GitHub 아님 → 머지 모드 거부, 사유 보고(체크포인트로 조용히 폴백하지 않는다). uncommitted 있으면 WIP 가 아니라 AskUserQuestion(정식 메시지로 커밋 / 취소) — 이는 §1 위험 확인이 아니라 "작업이 끝났는가" 방향 합의(§1 단서).
- **plan done 은 머지 전에 커밋해 PR 에 포함 + 실패 시 복구 규칙** (사용자 확정 (b). 이유: 머지 후엔 worktree·브랜치가 사라져 done 커밋을 올릴 곳이 main 뿐이고 main 직접 push 는 §8 `ask` 대상. §10 "머지 시점에 done" 과의 간극은 복구 규칙으로 메운다): PR 확보 → plan `status: done`·`# Progress` "PR #N"·`# Next` 비움 → plan-lint → 커밋·push → checks → merge. **이후 어느 단계든 머지에 실패·중단(checks 실패·CONFLICTING·머지 거부·timeout·사용자 거부)하면 즉시 `status: in_progress` 복구 + `# Blockers`(또는 timeout 은 `# Next` "PR #N checks 대기, `/e merge` 재실행") 기록 → 커밋·push 후 중단.** done 인 미머지 plan 을 남기지 않는다.
- **머지 성공 확인 + fetch 는 hard invariant**: `gh pr merge` 후 `gh pr view --json state,mergedAt,mergeCommit` 로 실제 머지를 확인하고 `git fetch origin <default>` 를 실행한 뒤에만 7단계 재수집으로 넘어간다 (이유: `collect-state.sh` 는 fetch 하지 않아 로컬 ref 만으로는 서버 머지를 영원히 감지 못함 — 리뷰어가 스크립트로 확정. PR #147 세션은 수동 fetch 로 우연히 통과).
- **재실행 안전(idempotent)**: 기존 open PR 재사용(`gh pr view --json number,state,isDraft,mergeable`), closed 면 새로 생성, draft 면 중단·보고. 이미 merged(state MERGED)면 M2~M6 skip 하고 fetch → 5~8단계만. 머지 성공 후 5~8단계 실패 시 재실행에서 merge 재호출 금지.
- **checks 분기(닫힌 목록)**: `gh pr checks <N> --watch` 를 도구 timeout(10분)과 함께. pass → 머지 / fail·cancelled → 복구 규칙 / none("No checks reported") → `gh pr view --json statusCheckRollup` 로 재확인, 비어 있으면 required 없음으로 보고 진행 / timeout → 복구 규칙(`# Next` 재실행). skipped 는 pass 취급.
- **머지 방식**: 기본 `--merge`. repo 가 merge 커밋을 거부하면(`gh` 에러) `--squash` 로 1회 재시도, 둘 다 거부면 복구 규칙. `mergeable: CONFLICTING`·merge queue(`mergeStateStatus`)는 머지 전에 확인해 CONFLICTING 이면 복구 규칙. **`--delete-branch` 금지** (이유: wiki `workflow-failures` — worktree 가 main 을 점유해 gh 의 로컬 삭제가 항상 실패하고 정리만 조용히 누락). 원격 삭제는 7단계 뒤 AskUserQuestion 1회(§8(b)) — 4단계 done 확인 질문은 머지 모드에선 생략(`/e merge` 가 그 확인, §3-6 1회 원칙).
- **SKILL 에는 게이트·닫힌 목록만, gh 메커닉은 `docs/worktree-lifecycle.md` §E** (repo 패턴 — README:304 참조 관계). 단계 번호는 소수점 대신 **모드 분기**: 체크포인트 1~8 유지, 머지 모드는 M1~M6 을 4단계 뒤에 삽입하고 5~8 공유.
- **호출측 정합(사용자 확정 ④ 포함)**: CLAUDE.md §3-6 "(`/e merge`)" 삽입. CLAUDE.md §8 의 `--delete-branch` 문장은 삭제가 아니라 "worktree 환경에선 항상 실패하므로 명령으로 쓰지 않고, 지시로 나왔을 땐 원격 삭제 승인으로만 해석" 으로 재작성(승인 범위 해석 의미 보존). `skills/dlc/SKILL.md:120` 은 "원격 tip sha 보고" 자동 원격삭제 문구 제거(원격은 항상 확인) + `/e step6`→step7 정정 + 선택지에 `/e merge`. README `skills/e/` 절은 bullet 1~2줄 요약만(세 번째 진실 소스 금지).
- **재검토 반영(CONDITIONAL GO 조건 3 + minor)**: (a) Acceptance 게이트는 `# Acceptance` 섹션이 없으면 통과(보고 1줄), 있으면 미체크 항목 중 "`/e merge` 실행 자체로 충족되는 항목(머지·smoke 류)" 은 제외하고 판정(이유: 자기 자신의 smoke 를 게이트가 막는 데드락). (b) `gh pr view` 로 확인된 `mergedAt` 은 **7단계 조건4(merged) 를 직접 충족**한다 — `--squash` 폴백 시 `inBase`/`patchInBase` 가 false 여도 git 신호로 재유도하지 않는다. (c) checks none 분기는 1회 조회가 아니라 head SHA 대조(`gh pr view --json headRefOid` = `git rev-parse HEAD`) 후 15초 간격 3회 재조회, 그래도 비어 있을 때만 required 없음으로 진행(이유: plan done push 직후 check run 미등록 레이스로 CI 우회 가능). (d) 복구 push 가 거부되면 로컬 커밋만 남기고 보고. (e) `<default>` 는 `git symbolic-ref --short refs/remotes/origin/HEAD` → 실패 시 `origin/main`(wt 와 동일). (f) 시나리오 표의 거처는 `docs/worktree-lifecycle.md` §E. (g) lifecycle 헤더의 `(SKILL §5)`/`(SKILL §6 ⓑ)` stale 역참조는 §E 를 쓰면서 함께 정정(Deferred 에서 스코프로 승격).
- **code-reviewer fix loop 로 변경된 결정**(위 항목을 덮어쓴다, 세부는 `# Review Disposition`): "MERGED 면 M2~M6 skip" → **MERGED/CLOSED 는 재사용하지 않고 남은 커밋으로 새 PR, 커밋 0+done 이면 지름길(`git restore` 후 M6 확인·fetch)**, 새 PR 이 필요하면 M4 선행 (이유: skip 경로는 7단계 조건 2·3·5 를 못 넘는다) / checks 판정 "pass·fail·cancelled 문자열" → **exit code + `--json name,bucket` 별도 재조회** (이유: `--watch` 는 cancel 을 exit 에 반영하지 않는다) / `<default>` 폴백 "`origin/main`" → **`gh repo view defaultBranchRef.name`** (이유: remote-tracking ref 를 브랜치 이름 자리에 쓰면 `gh pr create --base` 가 실패) / 복구 규칙 "어느 단계든 실패·중단" → **REJECTED 확정 시만**, QUEUED/UNKNOWN/head 불일치는 done 유지 + `# Next` 재실행 / Acceptance 예외 "의미 판정" → **`[post-merge]` 마커** / squash "에러 문자열 재시도" → **M1 의 `gh repo view` 머지 설정으로 선택** / 사전 점검 CONFLICTING·DIRTY 는 done 전 중단, BEHIND·BLOCKED 는 M6 직전 재평가.
- **CLAUDE.md §8 격리 한 줄은 이번 스코프에서 제외** (사용자 확정 ②. 이유: 리뷰어 실측 4회 — 거부 트리거는 경로가 아니라 명령 텍스트의 git 언급이며 비결정적·하네스 버전 의존. 틀린 규칙을 전역 주입하지 않는다. wiki decision 관찰 기록 → Report 에서 `/wiki ingest` 제안).

# Key Files
- `skills/e/SKILL.md` — 모드 분기 헤더, 머지 모드 M1~M6(게이트·닫힌 목록·복구 규칙·fetch invariant), 경계 절 분기
- `docs/worktree-lifecycle.md` — §E 머지 모드 gh 메커닉(PR 재사용 JSON 필드·body 템플릿·checks 판정·merge 재시도·머지 확인)
- `CLAUDE.md` — §3-6 `/e merge`, §8 `--delete-branch` 문장 재작성
- `skills/dlc/SKILL.md` — Report·정리 판정 줄(:120) 원격 자동삭제 제거·step7 정정·`/e merge`
- `README.md` — `skills/e/` 절 bullet 1~2줄
- `skills/c/SKILL.md` — 예외 5(done) 에 "`/e merge` 재실행 대기" 단서 한 절(리뷰 반영)

# Blockers
(없음 — 2026-09-02 사용자 결정 4건 확정)

# Acceptance
- [x] `skills/e/SKILL.md` 머지 모드에 진입 게이트(닫힌 목록)·M1~M6 순서·복구 규칙·fetch+머지 확인 invariant·checks 닫힌 목록·재실행 규칙·`--delete-branch` 금지·원격 삭제 확인이 모두 있음 — 검증: 아래 시나리오 표의 각 행이 SKILL 문장으로 매핑됨(리뷰어 대조).
- [x] 시나리오 표 — 각 행에 "외부 쓰기 발생 · plan status · `# Next` · 재실행 결과" 가 규약으로 정해짐: 새 PR / 기존 open PR / closed PR / draft / checks none / pending→pass / fail / timeout / CONFLICTING / merge 커밋 거부(squash 재시도) / gh 미인증 / push 거부 / plan 없음 / plan 이미 done+merged / main 브랜치 / 머지 후 정리 실패 후 재실행.
- [x] 체크포인트 모드(`/e` 무인자) 동작·"push 안 함" 이 머지 모드와 모순 없음 — 검증: 경계 절 diff.
- [x] CLAUDE.md §3-6 `/e merge` 언급, §8 `--delete-branch` 문장 재작성 — 검증: grep.
- [x] dlc SKILL.md :120 에 원격 자동삭제 문구 없음·step7·`/e merge` — 검증: grep `step6` 0건.
- [x] `docs/worktree-lifecycle.md` §E 존재, SKILL 이 참조 — 검증: grep.
- [x] README `skills/e/` 절 머지 모드 bullet — 검증: diff(doc-drift 게이트).
- [x] `node scripts/plan-lint.js plans/2026-09-02-e-merge-path/e-merge-path-plan.md` 통과.
- [ ] [post-merge] 최종 smoke 1회: 이 작업을 `/e merge` 로 마무리하며 M1~M6·fetch·7단계 자동 정리가 규약대로 진행되는지 관찰(외부 쓰기는 이 1회뿐).

# Review Disposition
plan-reviewer(+codex medium) 2회(NO-GO → CONDITIONAL GO), code-reviewer(+codex medium) fix loop 1회.
- fix — M3 MERGED skip 경로가 7단계 조건 2·3·5 로 정리 불가 (Major): PR 조회를 push 앞(M2)으로 옮기고 MERGED/CLOSED 는 재사용하지 않음 — 남은 커밋(plan done)으로 새 PR.
- fix — 복구 규칙이 확인 실패·merge queue 를 실패로 취급 (Major): M6 결과를 MERGED/QUEUED/REJECTED/UNKNOWN 으로 분류, 복구는 REJECTED 만. 그 외 오류는 plan 무변경 중단 catch-all.
- fix — `<default>` 폴백 `origin/main` 이 remote-tracking ref (Major): `origin/` 제거 → `gh repo view defaultBranchRef.name` → 거부.
- fix — M5 판정 키가 gh 출력·exit 과 불일치 (Major): exit code 기준 + `--json name,bucket` 별도 재조회(cancel 은 exit 미반영), `no checks reported` 소문자 부분일치.
- fix — frontmatter description 미갱신 (Major) / 7단계 조건4 에 mergedAt override 미기재 (Major).
- fix — Minor 12: 시나리오 표 외부 쓰기 순서, README 299/302/305 한정어·§E, lifecycle:5 Read 트리거, `gh pr list --head --base` 로 PR 고정, `--match-head-commit`, mergeStateStatus UNKNOWN/BEHIND/BLOCKED 사전 점검(done 전 중단), `[post-merge]` 마커, 원격 삭제 "항상 1회" 통일, CLAUDE.md:129 승인/재확인 모순, `--delete-branch` 인과 완화, `gh repo view` 로 인증·설정 통합 조회, 원문자 → (1)~(4), dlc:120 열거 삭제, §10 예외 한 줄.
- fix(2회차) — MERGED 재실행 잔여 2갈래: 새 PR 필요 시 M4 선행 후 push·create / 지름길은 fetch 후 `rev-list --count`=0 판정 + 3단계 plan 편집 `git restore`. Minor: "done 인 미머지" 문장 완화(REJECTED 한정), 사전 점검은 CONFLICTING/DIRTY 만·BEHIND/BLOCKED 는 M6 재평가, 머지 설정은 M1 로 통일, CLAUDE.md:129 완화 문구, `/c` 예외5 에 머지 대기 단서.
- wontfix — Codex Major "Acceptance 예외의 의미 판정": `[post-merge]` 마커로 기계 판별화해 흡수(disposition 은 fix 와 동일 효과).
- false-positive(리뷰어 자체 refuted 4건 동의) — step6 stale(worklog 단계라 정확) / `--watch`+`--json` 병용(별도 호출) / 잔존 §5/§6 / `# Next` 비움 plan-lint.
- open(❌모름, 규약은 보수 방향 유지) — gh 2.89 의 `--delete-branch` 현행 동작(금지 유지) / `gh auth status` 다중 host exit(`gh repo view` 로 대체) / "사용자 거부" 정의 → 권한 프롬프트 거절 = REJECTED 로 명시.

# Deferred
- `docs/codex-review.md:24` 정본 codex 호출(`--skip-git-repo-check` 포함)이 worktree 세션 하네스 격리에 거부됨 → §9 codex 병행 필수가 worktree 에서 구조적으로 막힘. 우회: 프롬프트를 파일로 분리 + 해당 플래그 제거(리뷰어 실측). 심각도 major, 파일 `docs/codex-review.md`.

# Workflow Findings
- `dlc-task-router` 가 subagent 완료 `<task-notification>` 턴에 `router-investigation` 을 발동(이 세션 2회 — code-reviewer·plan-reviewer 결과 뒤). `/improve` 후보 2 로 이미 승인, 별도 wt 예정.
