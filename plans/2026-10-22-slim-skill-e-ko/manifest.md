# skills/e/SKILL.md 규칙 목록 (slim-skill-e-ko)

origin/main 3736fe5 의 skills/e/SKILL.md(138줄·35,536B) 기준. 한 줄 = 한 조항(긴 불릿은 조항마다 나눈다 — 한정어도 조항의 일부).
등급 — 인라인: SKILL 에 남는다 · 세부: 다른 파일에 이미 있다(그 파일이 SKILL 을 다시 가리키면 안 된다) · 이력: 괄호 안의 근거 표시(날짜 실측·버전) — 지우고 wiki 에 없으면 Deferred · 이유: 근거 문장 — 짧게 남기거나, 규칙만으로 적용할 수 있으면 지운다 · 중복: 같은 SKILL 안의 다른 절에 같은 조항이 있어 한 곳만 남긴다 · 수정: 단위 1 에서 고친다.
새 위치는 `locations.txt`(줄인 뒤 채움, `<id> | <인용>`).

## 머리말·frontmatter
- F.1 frontmatter `name`·`description` 은 그대로(트리거 문구 — 다른 skill·README 가 인용) — 인라인
- H.1 진행 중 §10 plan 을 실제 git/코드 상태로 동기화 기록, uncommitted 는 임시 커밋으로 보존, 다음 세션 `/c` 가 이어받게 — 인라인
- H.2 CLAUDE.md §10 "턴 종료 / 완료" + §8 의 자동화 버전, 충돌 시 CLAUDE.md 우선, c 의 대칭 — 인라인

## 적용
- A.1 `/e` 명시 호출 또는 "진행상황 기록하고 마무리 / 오늘 여기까지 / 일단 저장하고 끝" 류 — 인라인
- A.2 단순 질문·탐색·읽기 전용·한 턴 명령 제외 — 인라인
- A.3 plan 이 없으면 새로 만들지 않는다(dlc/작업 시작의 몫) — 인라인

## 모드
- M.1 체크포인트 모드(기본, 무인자 또는 머지 토큰 없음): 1~8단계, push 안 함 — 인라인
- M.2 머지 모드는 `/e merge`·`/e 머지` 두 토큰만, `push`·`PR` 은 트리거 아님 — 인라인
- M.3 머지 모드 순서: 1~4 → M1~M6 → 5~8 — 인라인
- M.4 `/e merge` 인자 자체가 push·PR·머지 지시(CLAUDE.md §8 «push 는 요청 시만» 충족) — 인라인
- M.5 `git push` 에 `permissions.ask` 가 뜨면 그것도 게이트 — 거부되면 중단, plan 무변경 — 인라인

## 동작 제목
- D.1 8단계 이름(찾기 → 상태 수집·임시 커밋 → plan 동기화 → 마무리 보고 → Jira → worklog → worktree 정리 → main 복귀), 비-메인 worktree 세션은 worklog 전에 복귀 — 인라인

## 1. plan 찾기
- 1.1 `ROOT = git rev-parse --show-toplevel`, `BR = git rev-parse --abbrev-ref HEAD` — 인라인
- 1.2 탐색 위치: `<ROOT>/plans/` + cwd 가 worktree 면 main worktree 의 `plans/`(porcelain 첫 worktree), 존재하는 것만·중복 제거 — 인라인
- 1.2b 이유: plans/ 는 브랜치마다 내용이 달라 양쪽을 봐야 누락이 없다 — 이유 → 짧게 유지
- 1.3 매칭(§10): `BR` 이 plan dir 이름에 포함되는 dir 의 `*-plan.md` 1개 — 1개 채택 / 2개+ 후보 제시 후 선택 / 0개 fallback — 인라인
- 1.4 active plan 우선: 세션에서 진행 중이던 plan 은 branch 매칭과 무관하게 대상 — 인라인
- 1.5 fallback: `status: in_progress|blocked` plan 을 `updated` 내림차순 제시 → 사용자 선택, 추측으로 자동 선택 금지 — 인라인
- 1.6 전부 done/없음이면 "마무리할 plan 없음" — 그래도 2단계(임시 커밋)는 하고 보고만 — 인라인

## 2. 상태 수집 + 임시 커밋
- 2.1 `bash skills/e/collect-state.sh` 1회로 읽기전용 상태 신호를 `key: value` 로 받는다 — 인라인
- 2.1b 이유: 개별 git 10+ 호출을 1회로 묶음 — 이유 → 삭제
- 2.2 상대경로는 cwd 가 `~/.claude`(또는 그 worktree) 루트일 때만 — 다른 repo 는 `~/.claude/skills/e/collect-state.sh` 절대경로 — 인라인
- 2.3 격리 worktree 세션에서는 `bash "$HOME/…"` 형태가 거부될 수 있어 `$HOME` 을 펼친 절대경로 — 인라인 (다른 단계가 «2단계 경로 표기» 로 가리킨다)
- 2.3m (2026-09-30 실측) — 이력 → 삭제(wiki worktree-isolation-bash-guard)
- 2.4 헬퍼 실패·필드 누락이면 보고에 명시하고 개별 git 명령으로 폴백 — 인라인
- 2.5 필드 카탈로그·파싱 규칙·폴백 명령은 `~/.claude/wiki/docs/worktree-lifecycle.md` §A(상태 수집 분기에서 Read) — 인라인(포인터)
- 2.6 uncommitted 있으면 작업 브랜치에 WIP 커밋(임시 커밋 규칙), 없으면 skip + "변경 없음" — 인라인
- 2.7 머지 모드는 WIP 를 만들지 않는다 — uncommitted 가 있으면 AskUserQuestion(정식 메시지로 커밋 / 취소) — 인라인
- 2.7b 이건 §1 위험 확인이 아니라 "작업이 끝났는가" 방향 합의(§1 단서) — 인라인

## 3. plan 동기화
- 3.1 plan 을 re-read(외부 변경 merge) 후 사실 기반으로만(§1) 갱신, 옛 형식은 §10 대응표 — 인라인
- 3.2 `# Tasks`: 끝낸 Task 체크(`(YYYY-MM-DD)`), 새 할 일 추가(급한 일은 미완료 맨 위), 실효된 것 정리 — 첫 미완료 Task 가 다음 세션 즉시 액션 — 인라인
- 3.2b 파일을 바꾼 Task 는 그 경로를 backtick 으로 — 인라인
- 3.2c WIP 커밋 있으면 미완료 Task 에 "브랜치 tip 의 `wip:` 커밋 이어서 — 정리는 commit-check(`/e merge` 가 push 전에 제안)" → c 가 인지 — 인라인
- 3.2d sha 는 적지 않는다(보고에만) — commit-check 가 다시 쓰면 없는 커밋을 가리킨다 — 인라인
- 3.3 `# Decisions`: 세션 중 결정·스코프 변경 보강(그 결정을 고쳐 쓰고 이유, 밀려난 안은 기각안) — 인라인
- 3.4 `# Blockers`: 막힌 것 + 풀 조건 — 인라인
- 3.5 frontmatter: `status` 판정(4단계) · `updated:` 오늘 — 인라인
- 3.6 갱신을 write 한 뒤 `node scripts/plan-lint.js <이 plan>`(있으면) — §10 형식·끊긴 Acceptance 참조 — 인라인
- 3.6b 위반은 그 자리에서 보정(additive 편집이 참조를 깬 경우 흔함) — 인라인
- 3.6c 명령 실패는 skip+명시, hard-stop 아님 — 인라인

## 4. status 판정 + 보고
- 4.1 확정 완료 신호(머지·배포)가 있을 때만 `done`, done 전환은 사용자 확인(마무리 ≠ 작업 끝) — 인라인
- 4.2 묶음 intent 판정: plan 에 `intent:` 가 있으면 done 을 쓰는 그 지점에서(체크포인트는 4단계 확인 done, 머지 모드는 M4 커밋) — 인라인
- 4.2b `# Plans` 의 plan frontmatter `status` 를 읽음 — 메모 `폐기` 는 done 취급, 읽을 수 없는 항목·`(미착수)` 는 done 아님(fail-safe) — 인라인
- 4.2c 전부 done + `# Open questions` 전부 처분(`(해소)`/`(이월 → …)`)이면 `status: closed` + `updated`, 확인 없이, plan done 과 같은 커밋 — 인라인
- 4.2d 하나라도 남으면 open 유지 + 보고에 남은 항목, `# Out of scope` 는 조건 아님 — 인라인
- 4.3 막힘 → `blocked` + `# Blockers`, 그 외 → `in_progress` 유지 — 인라인
- 4.4 보고 항목: plan 위치·title·status / 임시 커밋 sha 또는 "변경 없음" / 동기화한 항목 / 남은 작업(미완료 Tasks·Blockers) / "다음 세션은 `/c` 로 이어받기" — 인라인
- 4.4b 묶음이고 `(미착수)` 줄이 있으면 그 줄들을 열거하고 "착수는 `/wt <slug 후보> — <메모>`" 를 덧붙인다(맨 slug 만 넘기면 dlc 가 다시 묻는다) — 인라인
- 4.4c 이유: `/c` 는 plan 을 새로 만들지 않아 이 안내가 없으면 형제가 잊혀 intent 가 영영 open — 이유 → 짧게 유지
- 4.5 `/e` 호출 자체가 마무리 지시라 작업 선택지용 새 AskUserQuestion 은 만들지 않는다(§3-6 예외) — 인라인
- 4.5b 단 5단계의 Jira 반영 승인은 외부 쓰기라 별도로 반드시 받는다 — 인라인
- 4.5c 마무리 액션은 7단계 정리와 8단계 "다음 세션 `/c`" 안내가 담당 — 인라인
- 4.5d 머지 모드에선 done 확인 질문을 생략한다 — `/e merge` 가 그 확인(중복 질문 금지 — §3-6) — 인라인

## 머지 모드 M1~M6
- MM.1 gh 명령·JSON 필드·PR body 템플릿·시나리오 표는 `~/.claude/wiki/docs/worktree-lifecycle.md` §E(진입 시 Read), 여기엔 게이트·순서·닫힌 목록만 — 인라인(포인터)
- MM.2 M1 진입 게이트(hard-stop, 닫힌 목록) — 하나라도 걸리면 거부 + 사유, 체크포인트로 조용히 폴백하지 않는다 — 인라인
- MM.2a (1) 브랜치가 main/master 또는 detached — 인라인
- MM.2b (2) plan 없음 — 인라인
- MM.2c (3) `# Acceptance` 에 미체크 항목 — 섹션이 없으면 통과·보고 1줄, `[post-merge]` 접두어 항목만 제외(의미 판정으로 제외 금지) — 인라인
- MM.2d (4) `gh repo view` 실패(미인증·GitHub 아님·권한 없음) — 인라인
- MM.2e (5) `# Tasks` 에 `/e merge` 를 실행하는 Task(`/e` 가 쓴 재실행 Task 포함)·`[post-merge]` 밖의 미완료 항목(옛 형식은 해당 없음) — 인라인
- MM.2f `<default>` = `origin/HEAD` symbolic-ref 에서 `origin/` 을 뗀 이름 → 실패 시 `gh repo view` 의 `defaultBranchRef.name` → 없으면 거부, remote-tracking ref 를 브랜치 이름 자리에 쓰지 않는다 — 인라인
- MM.3 M2: 먼저 `git fetch origin <default>`, `gh pr list --head <branch> --base <default> --state all` — 후보 2개+ → 중단·보고 — 인라인
- MM.3b OPEN → 재사용(draft 면 중단·보고) — 인라인
- MM.3c MERGED·CLOSED → 재사용하지 않는다 — 인라인
- MM.3d 이유: skip 경로면 done 커밋을 실을 PR 이 없어 7단계 조건 2·3·5 를 못 넘는다 — 이유 → 이미 wiki e-merge-mode, 짧게 유지 또는 삭제
- MM.3e 지름길: `origin/<default>..HEAD` 커밋 0개 + plan 이미 done → 3단계 plan 편집을 `git restore` 로 되돌리고 M3~M5 없이 M6 의 확인·fetch 로 — 인라인
- MM.3f 이유: 머지된 plan 이 단일 진실, ahead 면 `git branch -d` 거부 — 이유 → 짧게 유지
- MM.4 M3 선행 검사(push·"M4 먼저" 분기보다 앞, M2 지름길이면 건너뜀): PR 에 `wip`·`fixup!` 커밋이 실리지 않게(push 되면 commit-check 범위 밖) — 인라인
- MM.4a 1. `git fetch origin "+refs/heads/<branch>:refs/remotes/origin/<branch>"`(refspec 명시) — 인라인
- MM.4a2 이유: fetch refspec 이 main 만 매핑하면 브랜치 이름만 준 fetch 는 추적 ref 를 갱신하지 않는다 — 이유 → 짧게 유지
- MM.4a3 `couldn't find remote ref` 면 남은 `refs/remotes/origin/<branch>` 를 `git update-ref -d` 로 지우고 sha 를 보고(복구 `git update-ref refs/remotes/origin/<branch> <sha>`) 후 진행 — 인라인
- MM.4a4 이유: 옛 추적 ref 가 미게시 커밋을 `published` 로 보이게 한다, 로컬 ref 라 원격 영향 없음 — 이유 → 짧게 유지
- MM.4a5 그 밖의 fetch 실패는 중단 — 인라인
- MM.4a6 fetch 했으면 `git merge-base --is-ancestor origin/<branch> HEAD` — exit 1(갈라짐)·그 밖의 비0 이면 중단 — 인라인
- MM.4b 2. `uv run --no-project python "$HOME/.claude/skills/commit-check/commit_units.py" pending origin/<default>`(경로 고정 — main checkout 에서 로드), 명령 실패는 0건이 아니라 중단, `unfolded` 가 비면 M3 로 — 인라인
- MM.4c 3. `status: rewritable` 이 있으면 `commit-check` 를 "`/e merge` — `wip`·`fixup` flag 커밋 정리만" 으로(합치기 또는 정식 제목 reword, 합치기 충돌이면 reword 재시도 — 그 SKILL 의 `/e merge` 절) — 인라인
- MM.4c2 적용 뒤 `pending` 을 다시 돌려 `rewritable` 0 일 때만 계속, 보류·적용 실패·잔존·무인 → 중단, apply 성공 뒤 중단하면 재구성은 유지하고 `backup_ref`·`rollback` 보고 — 인라인
- MM.4d 4. `published`·`held`·`blocked`(`range_error`) 는 고치지 않는다(§8 force-push 금지) — 제목·상태·`refs` 를 보여 AskUserQuestion(그대로 진행 / 중단), 무인이면 중단 — 인라인
- MM.4d2 `held` 는 그 ref 를 치운 뒤 재실행하면 다시 분류된다(merge·서명 커밋이 드러나 `blocked` 가 될 수도) — 인라인
- MM.4d3 repo 가 merge 커밋을 불허하면(M6 이 squash) 묻지 않고 보고만 — 인라인
- MM.4e 중단 규칙: done 을 새로 쓰지 않는다, 3단계의 미커밋 plan 편집은 그대로 두고 Tasks 미완료 맨 위에 사유를 적은 "정리 후 `/e merge` 재실행" Task(커밋·push 안 함) — 인라인
- MM.4e2 plan 이 이미 done 이면(UNKNOWN·QUEUED·head 불일치 뒤 재실행) Task 도 status 도 건드리지 않는다 — 인라인
- MM.5 M3 push + PR: 직전 PR 이 MERGED/CLOSED 라 새 PR 이 필요하면 M4 를 먼저 한 뒤 push·생성(커밋 0 이면 `gh pr create` 실패) — 인라인
- MM.5b `git push -u origin HEAD` — 거절·실패 → 중단, plan 무변경(M4 선행 경로면 복구 규칙으로 `in_progress` 되돌리고 보고) — 인라인
- MM.5c PR 이 없으면 `gh pr create --base <default>`(title = plan title 또는 첫 커밋 subject, body 는 스크래치 파일 — §E 템플릿) — 인라인
- MM.5d done 을 쓰기 전에 `mergeable`/`mergeStateStatus` 확인: CONFLICTING·DIRTY → 중단(plan 무변경), UNKNOWN → 짧게 재조회, BEHIND·BLOCKED 는 여기서 막지 않고 M6 직전에 재평가 — 인라인
- MM.6 M4: `status: done` · `/e merge` 를 실행하는 Task(없으면 추가)를 `(YYYY-MM-DD) — PR #N` 으로 체크(옛 형식은 `# Progress` "PR #N"·`# Next` 비움) → plan-lint(실패 → 중단, 커밋 안 함) → plan 과 log 를 커밋·push — 인라인
- MM.6b `intent:` 가 있으면 4단계 묶음 판정을 여기서 해 `intent.md` 변경을 같은 커밋에, 복구 시 `closed` 도 `open` 으로 — 인라인
- MM.6c §10 "머지 시점에 done" 을 PR 단위로 앞당긴 것, 복구 규칙이 간극을 메운다 — 인라인
- MM.6d 복구 규칙(hard-stop): M5·M6 에서 REJECTED 로 확정된 경우에만 즉시 `in_progress` + M4 가 체크한 Task 를 미완료로 + `# Blockers`(timeout 은 미완료 맨 위 Task "PR #N checks 대기, `/e merge` 재실행") → 커밋·push 후 중단 — 인라인
- MM.6e 복구 push 가 거부되면 로컬 커밋만 남기고 보고 — 인라인
- MM.6f REJECTED 면 done 을 남기지 않는다, UNKNOWN·QUEUED·head 불일치는 done 유지 + 재실행 안내 — 인라인
- MM.7 M5: `headRefOid` ≠ 로컬 HEAD 면 M3 의 push 만 재실행, 그래도 다르면 중단(plan 무변경) — 인라인
- MM.7b `gh pr checks <N> --watch`(도구 timeout 10분) — 인라인
- MM.7c exit 0 → 별도 호출 `gh pr checks <N> --json name,bucket`, 모든 bucket ∈ {pass, skipping} 일 때만 M6, `fail`/`cancel` 하나라도 → REJECTED(--watch 는 cancel 을 exit 에 반영 안 함) — 인라인
- MM.7d exit 8·도구 timeout → REJECTED(timeout) — 인라인
- MM.7e exit 1 + stderr `no checks reported`(소문자 부분일치) → 15초 간격 3회 재조회, 그래도 없을 때만 required 없음으로 M6(done push 직후 check run 미등록 레이스) — 인라인
- MM.7f 그 외 exit 1 → REJECTED — 인라인
- MM.8 M6: 머지 직전 `mergeable`/`mergeStateStatus` 재확인 — CONFLICTING → REJECTED, BEHIND·BLOCKED 가 남아 있으면 REJECTED — 인라인
- MM.8b `gh pr merge <N> --merge --match-head-commit <M5 시점 headRefOid>`(head 불일치 거부 → 중단·보고, 복구 아님) — 인라인
- MM.8c `--delete-branch` 금지(CLAUDE.md §8) — 인라인
- MM.8d merge 커밋 불허면(M1 의 `gh repo view` 설정) `--squash` — 인라인
- MM.8e 결과 넷: MERGED(`mergedAt` non-null) → `git fetch origin <default>` 후 5단계 / QUEUED(성공인데 `mergedAt` null) → plan 무변경, "큐 대기, 완료 후 재실행" 보고·중단(복구 push 금지) / REJECTED(명령 실패·권한 거절) → 복구 규칙 / UNKNOWN(확인·fetch 실패) → plan 무변경, 재조회 안내·중단 — 인라인
- MM.8f 그 외 오류는 전부 plan 무변경 중단 — 인라인
- MM.8g 확인된 `mergedAt` 은 7단계 조건4 를 직접 충족(squash 면 git 신호가 false 여도) — 인라인
- MM.8h 이유: `collect-state.sh` 는 fetch 하지 않아 fetch 없이는 서버 머지를 못 본다 — 이유 → 짧게 유지
- MM.8i 재실행은 M2 에서 MERGED 를 재사용하지 않아 merge 를 재호출하지 않는다 — 인라인
- MM.9 원격 브랜치 삭제는 여기서 하지 않는다 — 7단계 로컬 정리 뒤 머지 모드에선 항상 1회 AskUserQuestion(§8(b), `--delete-branch` 로 지시했으면 그 승인으로 갈음), 로컬 정리를 생략했으면 원격 질문도 미룬다 — 인라인

## 5. Jira task
- 5.1 `jira-task` skill 이 있으면 task 목표에 해당하는 변경만 결과 위주 한 줄 항목(1~4개) + 티켓 목표를 나눈 해야 할 일 목록으로 description 추가 preview(작성 규칙은 `skills/jira-task/SKILL.md` 2~3단계, 과정은 넣지 않는다) — 인라인
- 5.2 WIP commit 이 있으면 그 diff 와 그날 체크된 Tasks 를 근거로 — 인라인
- 5.3 티켓이 없거나 적을 항목이 없으면 skip — 인라인
- 5.4 preview: CLI 를 `--summary-file`(과 만들었을 때만 `--todo-file`)로 실행(절차 `skills/jira-task/SKILL.md` 5~6단계), Jira 는 읽기만 — 인라인
- 5.4b 그날 기존 항목이 있으면 합쳐 다시 쓰고 preview 를 다시 — 인라인
- 5.4c 지문이 `unknown` 이면 반영하지 않고 사유 보고 — 인라인
- 5.5 승인: 티켓·그날 기존 항목·교체 후 내용을 보고하고 AskUserQuestion "이 작업 내용을 Jira task 본문에 반영할까요?" — 승인 전 `--post` 금지, 반영 안 하면 preview 만 남기고 진행 — 인라인
- 5.6 반영: 승인 시 마지막 preview 인자에 `--date <preview 날짜> --post --expect-existing <preview 지문>` 1회 — 기존 description 보존, 그날 항목만 교체 — 인라인
- 5.6b 지문 불일치·Jira 오류면 재시도 없이 credential 을 노출하지 않는 한 줄로 "게시하지 않음" 보고 후 계속 — 인라인
- 5.7 `~/.agents/skills/jira-task/` 또는 `skills/jira-task/` 가 없으면 skip + "jira-task skill 없음" — 인라인

## 6 전. worktree 밖으로
- 6p.1 비-메인 worktree 세션이면 6단계 전에 값 캡처(`target_path`·`target_branch`·`main_path`) 후 `ExitWorktree(action: keep)` 시도 — 인라인
- 6p.2 이유: 격리 세션에서는 worktree 안의 `bash "$HOME/..."` 헬퍼(worklog·collect-state)가 네이티브 Bash 가드에 거부된다 — 이유 → 짧게 유지
- 6p.2m (2026-09-30 실측 — 펼친 절대경로와 `uv run python "$HOME/..."` 는 통과, 하네스 버전에 따라 달라질 수 있다) — 이력 → 이미 wiki worktree-isolation-bash-guard 확인 후 삭제
- 6p.3 5단계까지는 worktree 안에서 — 인라인
- 6p.4 복귀했으면 6·7단계를 원래 디렉토리에서 — worklog 는 미리보기·등록 모두 `<target_path>` 의 디렉터리 이름을 인자로(빠뜨리면 main 이 대상) — 인라인
- 6p.4b 7단계 재수집은 `(cd "<target_path>" && bash "$HOME/.claude/skills/e/collect-state.sh")` — 인라인
- 6p.4c 이후 `ExitWorktree` 를 다시 부르지 않는다 — 인라인
- 6p.5 no-op 이면(harness 가 worktree 에서 시작) worktree 안에서 6·7단계, 헬퍼는 펼친 절대경로(2단계 경로 표기) — 인라인
- 6p.5b 그래도 worklog·collect-state 가 거부·실패하면 7단계 정리를 생략(worklog 를 다시 돌릴 수 있게 남긴다) — 인라인
- 6p.6 6·7단계 도중 멈췄으면 같은 세션은 캡처한 값으로 잇고, 새 세션은 `/wt <이름>` 으로 들어가 다시 — 인라인

## 6. worklog
- 6.1 이 worktree 의 AI 작업시간을 Jira worklog 에 기록, 7단계 삭제보다 먼저 — 지우면 이름으로 고를 수 없어 등록 불가(표시만) — 인라인
- 6.2 `~/.claude/skills/jira-worklog/` 없으면 skip + "worklog 스킬 없음" 1줄 — 인라인
- 6.3 실행: POSIX `bash "$HOME/.claude/skills/jira-worklog/run_worklog.sh"`, Windows PowerShell `& "$HOME/.claude/skills/jira-worklog/run_worklog.ps1"`(dry-run)로 날짜별 시간·티켓 확인 — 인라인
- 6.3b launcher 는 `uv` 우선, `python3`/`python` fallback(Windows 는 `py` 포함) — 인라인
- 6.3c 귀속은 줄 단위 cwd 기준이라 main 복귀 뒤 이름을 인자로 줘도 정확, 다만 삭제 전이어야 — 인라인 (slim-rules-ko manifest 8.m5 의 유일한 사본 — 지우지 않음)
- 6.4 등록: 티켓이 잡히고(worktree 이름 prefix) `~/.jira-kit/.env` 에 토큰이 있으면 `--register`(6 전으로 main 에 나왔으면 `run_worklog.sh <이름> --register`) — 인라인
- 6.4b 그 worktree 의 그날 항목 upsert — 멱등, 같은 티켓의 다른 worktree 항목은 건드리지 않고 합산은 Jira — 인라인
- 6.4c 티켓 없음/토큰 없음/세션 활동 없음 → preview 만, 조용히 넘어감 — 인라인
- 6.4d `/e` 에 이 동작을 넣은 것 = 등록 표준 동의(별도 AskUserQuestion 안 만듦) — 인라인
- 6.5 비차단: 조회·네트워크 실패는 보고 1줄, 마무리 계속 — 다만 7단계 정리는 막는다 — 인라인
- 6.5b 정리 생략 조건: worklog 비0 종료(사유 불문 — 1·2·127 예) · 2단계 경로 표기로도 헬퍼 거부 · `--register` 에 "등록 불가" 경고(exit 0 이라 종료코드로 안 잡힘) — 인라인
- 6.5c 세션 활동 없음·티켓 없음·토큰 파일 없음은 exit 0 정상 skip 이라 정리 계속, 스킬이 없으면 이 조건 없음 — 인라인
- 6.6 보고 1줄(등록 결과·preview 만·세션 활동 없음), 이름 인자면 머리줄 `[<이름>]` 확인 — 인라인
- 6.6b 실패면 사유와 다음 명령 — 등록 차단이면 확인 뒤 `run_worklog.sh <이름> --register --allow-large-change`, 그다음 `/wt <이름>` → `/e`, 시간을 포기하면 `/wt rm <이름>` — 인라인

## 7. worktree 정리
- 7.1 역할을 다했고 안전하면 정리, 6단계 worklog 가 실패했으면 조건을 판정하지 않고 생략 — 인라인
- 7.1b 조건이 전부 충족되면 묻지 않고 worktree + 로컬 브랜치 삭제(CLAUDE.md §8(a), 누가 머지했는지 불문) — 인라인
- 7.1c 원격 브랜치 삭제는 포함되지 않는다 — 항상 AskUserQuestion(§8(b)) — 인라인
- 7.2 삭제 직전 `collect-state.sh` 를 한 번 더 실행해 그 신호로 판정(2단계 스냅샷 재사용 금지 — 재수집 invariant), 6 전으로 main 에 나왔으면 `(cd "<target_path>" && …)` — 인라인
- 7.2b 헬퍼 실패·필드 누락·파싱 불가면 정리 생략 — 인라인
- 7.3 조건 1 비-메인 worktree(`root` ≠ `mainWorktree`) — 인라인
- 7.4 조건 2 `detached`=false + plan `status == done` — 인라인
- 7.5 조건 3 working tree clean(untracked 포함, `dirty`=unknown 이면 생략) — 인라인
- 7.6 조건 4 default 에 merged — `mergedToLocalBase` 또는 `inBase`/`patchInBase`, 로컬 main 머지도 인정, 셋 다 false/unknown 이면 유지, squash 미감지는 유지 방향 — 인라인
- 7.6b 이유: push 하지 않는 워크플로우에서 `inBase` 만 보면 영영 false/unknown — 이유 → 짧게 유지
- 7.6c 예외: 머지 모드에서 M6 가 `mergedAt` 을 확인했으면 충족(git 신호가 false 여도) — 인라인
- 7.7 조건 5 미보존 산출물 안전 — 이 worktree `plans/` 에 미커밋 plan·log 가 있으면 생략, `.env`·secret 후보는 삭제 목록 명시, `ignoredStatus`=unknown 이면 생략 — 인라인
- 7.8 조건 6 점유 프로세스 없음 — 내가 띄운 서버·데몬은 삭제 전에 경로로 특정해 회수(사용자 서버·다른 worktree 프로세스는 건드리지 않음), 회수 못 하면 생략 + 사유 — 인라인
- 7.8b Windows 증상("Invalid argument"·"Access is denied") — 이유 → 짧게 유지
- 7.9 각 조건의 판정 git 명령·폴백·세부는 `~/.claude/wiki/docs/worktree-lifecycle.md` §B(삭제 판정 분기에서 Read) — 인라인(포인터)
- 7.10 하나라도 불충족·위험·헬퍼 불가이거나 worklog 실패면 정리 생략 + 사유 한 줄(예시 4개) — 인라인
- 7.11 실행: 묻지 않고 worktree → `git branch -d` 순, 삭제한 tip sha 한 줄(`git branch <name> <sha>` 로 복구) — 인라인
- 7.11b `git worktree remove` 의 부분 성공을 확인하고, 잔여 디렉터리는 조건6 처리 후 마저 지운다, 세부는 정리 규칙 + §C — 인라인
- 7.12 원격 브랜치: 체크포인트 모드는 지울 필요가 있을 때만, 머지 모드는 머지 성공 + 로컬 정리 뒤 항상 1회 AskUserQuestion, 자동 정리에 얹지 않음 — 인라인
- 7.12b 로컬 정리를 생략했으면 원격 질문도 미루고 "원격 브랜치 유지 — worktree 정리 때 확인" 1줄(원격은 로컬 삭제 뒤) — 인라인

## 8. main 복귀
- 8.1 1~7 뒤 세션을 main worktree 로 되돌린다, 비파괴적이라 자동 — 인라인
- 8.2 대상: 7단계 뒤에도 비-메인 worktree 에 있을 때(`--show-toplevel` ≠ main path, 정규화 후 비교), 처음부터 main 이면 skip — 인라인
- 8.3 7단계에서 삭제했거나 6 전에서 이미 나왔으면 skip(중복 `ExitWorktree` 금지), main 최신화는 그대로 — 인라인
- 8.4 그 외 → `ExitWorktree(action: keep)`, status 무관 — worktree·브랜치는 남고 다음에 `/wt <name>` → `/c` — 인라인
- 8.5 no-op 이면 in-session 복귀 불가 — 강제 이동 금지, "세션 종료하면 harness 가 worktree 를 놓는다" 고 보고만(다른 worktree 로 우회 금지) — 인라인
- 8.6 복귀 후 main 최신화(main-autopull ⓑ): 실제로 main 에 복귀했을 때만, main worktree·브랜치 ∈ {main, master}·clean 전부 충족 시 `git pull --ff-only origin "$(현재 브랜치)"` 1회(하드코딩 `main` 금지) — 인라인 (라벨 «main-autopull ⓑ» 는 worktree-lifecycle §D 가 인용)
- 8.6b no-op·dirty·ff 실패·origin 부재면 skip, 자동 rebase·stash·force 없음, 세부 §D — 인라인
- 8.7 한 줄 보고: main 복귀 여부 또는 불가 사유 — 인라인

## 임시 커밋 규칙
- T.1 uncommitted 를 잃지 않게 작업 브랜치에 보존, 자동 수행하되 안전장치 필수 — 인라인
- T.2 브랜치 보호: 현재 브랜치가 main/master(또는 origin/HEAD default)면 직접 커밋 금지 — AskUserQuestion ① 새 작업 브랜치에 커밋 / ② 커밋 생략하고 plan 기록만 / ③ 취소, 자동 브랜치 생성·강제 커밋 안 함 — 인라인 (원문자는 기존 선택지 표기 — 단위 2 에서 1)2)3) 로 바꿀지 리뷰)
- T.3 위험 파일 점검: `.env`·`*.key`·`*.pem`·`id_rsa`·인증서·대용량 의심 항목이면 커밋 보류 + 사용자 확인 — 인라인
- T.4 커밋: `git add -A` 후 `git commit`, 메시지 `wip: <작업 한 줄 요약> (e checkpoint)` + Co-Authored-By, 본문에 "다음 세션에 이어서 — commit-check 로 합칠 대상" — 인라인
- T.5 push 안 함(§8) — 중복(경계 B.1·M.1) → 한 곳
- T.6 uncommitted 없으면 skip — 중복(2.6) → 한 곳

## worktree 정리 규칙
- R.1 7단계에서 삭제할 때만, cwd 가 대상 안일 수 있어 순서 중요(6 전에서 나왔으면 이미 밖) — 인라인
- R.2 이동 전 값 캡처: `target_path`·`target_branch`·`main_path`(porcelain 첫 worktree)를 옮기기 전에 고정 — 인라인
- R.3 worktree 밖으로 `ExitWorktree(action: keep)` — 대상 안에선 자기 remove 불가, 6 전에서 나왔으면 다시 부르지 않음(그 no-op 을 폴백으로 처리하지 않는다) — 인라인
- R.3b no-op 이면 폴백은 §C(다른 linked worktree 경유 or remove 생략+보고), 강제 진행 금지, 이동 실패로 cwd 가 대상 안이면 중단+보고 — 인라인
- R.4 제거: cwd 가 대상 밖인지 확인 후 `git worktree remove <target_path>`, 실패 분기 세부는 §C — 인라인
- R.5 안전 게이트: `--force`·`git branch -D`(미머지)·원격 `git push origin --delete` 는 별도 AskUserQuestion 뒤에만 — 인라인
- R.5b 예외: 7단계 조건을 모두 충족한 worktree 를 remove 가 submodule 로 거부하고 §C 의 submodule 점검 두 가지를 통과하면 `--force` 는 묻지 않는다(더 지워지는 것이 원격 추적 ref 에 있는 것뿐) — 인라인
- R.6 로컬 브랜치 `git branch -d`(미머지로 거부되면 `-D` 는 확인 후) — 수정: "(옵션 ②·③)" 은 지금 `/e` 에 없는 선택지를 가리킨다
- R.7 원격은 사용자가 원격 삭제를 택했을 때만(7단계 원격 bullet) — worktree·로컬 삭제 성공 뒤 `git push origin --delete`(원격 ref 부재 no-op), 그 외 push 안 함 — 수정: "(옵션 ③만)·조건5 확정 아님" 을 뜻이 드러나게
- R.8 한 줄 보고: 제거한 worktree·브랜치 또는 유지 사유 — 인라인

## 경계 (안 하는 것)
- B.1 체크포인트 모드는 push 안 함, push·PR·머지는 머지 모드에서만, `push`·`PR` 단어는 트리거 아님 — 중복(M.1·M.2) → 경계에 짧게 남김(요약 절)
- B.2 main/master 직접 커밋 안 함 — 확인 후 분리 — 중복(T.2) → 경계에 짧게
- B.3 plan 없으면 새로 만들지 않음 — 임시 커밋 + "마무리할 plan 없음" 보고만(plan 가치 있어 보이면 dlc 제안 한 줄), 머지 모드는 M1 거부 — 인라인("dlc 제안 한 줄" 은 여기에만 있다)
- B.4 done 자동 전환 안 함 — 확정 신호 + 사용자 확인 시만, 머지 모드 M4 done 은 `/e merge` 가 확인이고 실패 시 복구 — 중복(4.1·4.5d·MM.6d) → 경계에 짧게
- B.5 plan 갱신은 사실 기반만 — 추측으로 Tasks 체크·Decisions 채우기 금지 — 인라인("추측으로 Tasks 를 체크하거나 Decisions 를 채우지 않는다" 는 여기에만 명시)
- B.6 subagent 위임 아님 — plan single writer 는 메인, 메인이 직접 커밋·기록 — 인라인(여기에만 있다)
- B.7 정리는 7단계 조건 충족 시 무확인, 불충족·worklog 실패면 생략(강행 금지), `--force`(submodule 예외 제외)·`-D`·원격 삭제는 명시 확인 없이 금지 — 중복(7.1~7.12·R.5) → 경계에 짧게
- B.8 main 복귀(6 전·8단계)는 자동 — 비파괴, 삭제는 7단계 사안, no-op 이면 강제 이동 없이 보고 — 중복(8.1·8.5) → 경계에 짧게

## 다른 파일이 가리키는 표지 (Acceptance 3)
- 절·단계: `### 1.`~`### 8.` 제목의 번호와 이름, `### 6 전.`, `### 머지 모드 M1~M6`, M1~M6 코드, M1 (1)~(5), 7단계 조건 1~6 의 번호, `## 임시 커밋 규칙`·`## worktree 정리 규칙`·`## 경계 (안 하는 것)` 제목.
- 인용하는 쪽: CLAUDE.md(§3-1 "`/e` 8단계", §8 "`/e` 6단계를 7단계 삭제보다 먼저"·"`/e` 7단계·worktree 정리 규칙", §10 "M4 커밋"), skills/dlc(16단계·정리 판정 "`/e` 7단계의 6조건"), skills/c·skills/wt(rm 의 worklog 미리보기 "`/e` 6단계"·"`skills/e/SKILL.md` 2단계"), skills/commit-check("`/e merge` 절"), `~/.claude/wiki/docs/worktree-lifecycle.md`(§A "SKILL §2"·"SKILL 2단계", §B "SKILL §7"·"6조건", §C "SKILL 정리 규칙", §D "SKILL §8 ⓑ", §E "SKILL M1~M6"·"SKILL "6 전" 절"), 공용 wiki e-merge-mode.
- 글자 그대로 남길 구절: «main-autopull ⓑ» · «2단계 경로 표기» · «임시 커밋 규칙» · «worktree 정리 규칙» · «재수집 invariant» · «복구 규칙» · «중단 규칙» · «지름길» · «hard invariant».

## 핵심 문구 검색 세트 (Acceptance 2 — 단위 2 전에 고정, 바꾸려면 사용자 승인)
/e merge · /e 머지 · push 는 요청 시만 · permissions.ask · collect-state.sh · $HOME · worktree-lifecycle.md · §A · §B · §C · §D · §E · plan-lint.js · intent: · (미착수) · 폐기 · (해소) · AskUserQuestion · M1 · M2 · M3 · M4 · M5 · M6 · [post-merge] · gh repo view · defaultBranchRef · gh pr list · --state all · git restore · couldn't find remote ref · git update-ref -d · merge-base --is-ancestor · commit_units.py · pending · rewritable · published · held · blocked · range_error · backup_ref · gh pr create · mergeStateStatus · CONFLICTING · BEHIND · --match-head-commit · --delete-branch · --squash · mergedAt · QUEUED · REJECTED · UNKNOWN · --watch · --json name,bucket · no checks reported · jira-task · --summary-file · --todo-file · --expect-existing · ExitWorktree(action: keep) · target_path · run_worklog.sh · run_worklog.ps1 · --register · --allow-large-change · ~/.jira-kit/.env · /wt rm · mergedToLocalBase · inBase · patchInBase · ignoredStatus · git branch -d · git branch -D · --force · git push origin --delete · git pull --ff-only · main-autopull ⓑ · wip: · (e checkpoint) · git add -A · single writer · 재수집 invariant · 복구 규칙 · 중단 규칙 · 지름길 · hard invariant · 임시 커밋 규칙 · worktree 정리 규칙 · 2단계 경로 표기
