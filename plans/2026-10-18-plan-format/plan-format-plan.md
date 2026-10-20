---
title: plan-format — plan 파일을 Goal · Tasks 체크리스트 · Acceptance · 현재 Decisions · Blockers 로 단순화
status: in_progress
started: 2026-10-18
updated: 2026-10-20
---

# Goal
plan 파일을 짧고 최신 상태로 유지하기 쉽게 만든다: `# Goal` · `# Tasks`(첫 미완료 항목이 다음 할 일) · `# Acceptance` · `# Decisions`(현재 결정·이유·기각안) · `# Blockers`. 옛 형식 plan 도 계속 유효하다.
- Why: plan 이 같은 말을 반복했고(Goal 과 Intent, Progress 와 Next), Decisions 는 이력이 쌓여 길어졌으며, 사용자가 plan 이 제대로 갱신될지 의심했다(사용자, 2026-10-17).
- Constraints: 사용자 결정 — Goal 과 Intent 를 합친다, Progress/Next 대신 Tasks 체크리스트, Decisions 는 현재 상태만, Acceptance 는 유지, 섹션 이름은 영어. §10 형식 정의는 CLAUDE.md 에 둔다([[ops-doc-slimming]]). skills 와 CLAUDE.md 는 main checkout 에서 로드되지만 `plan-lint` 는 각 worktree 에서 돌아서, 옛 worktree 는 옛 lint 를 쓴다. 옛 형식 plan 이 다른 repo 와 `read-points` worktree 에서 진행 중이다.
- Out of scope: 옛 plan 변환 · 묶음 `intent.md` 형식 · 공용 wiki(main 세션, log `# Deferred`) · 규칙 파일의 영어 번역(다음 작업, log `# Deferred`).
- Split: none — 단위 1(lint 가 두 형식을 받음)은 혼자 머지할 수 있지만, 단위 2 가 들어오기 전에는 새 형식을 쓰는 곳이 없어 나누면 리뷰·머지 비용만 두 배가 된다.

# Tasks
- [x] plan 섹션을 쓰는 곳 전부 조사 (2026-10-18) — workflow `wf_8fe4367b-eaa`
- [x] 계획 리뷰 (2026-10-18) — architecture-reviewer REQUEST CHANGES(Major 4), plan-reviewer CONDITIONAL(strong 7), 지적은 Decisions 에 반영
- [x] 테스트 먼저, 그다음 `scripts/plan-lint.js` 두 형식 판별 · `scripts/plan-lint.test.js` (2026-10-18) — 단위 1 로 커밋
- [x] `CLAUDE.md` §10 과 다른 섹션 참조 고쳐 쓰기 (2026-10-18)
- [x] 사용처를 새 형식으로: `skills/dlc/SKILL.md`, `skills/c/SKILL.md`, `skills/e/SKILL.md`, `agents/plan-reviewer.md`, `agents/code-reviewer.md`, `agents/architecture-reviewer.md`, `agents/researcher.md`, `scripts/dlc-early-stop.js`, `scripts/dlc-signal.js`, `skills/improve/SKILL.md`, `skills/jira-task/SKILL.md`, `README.md` (2026-10-18) — workflow `wf_c55c55d9-484` 초안을 적용·확인
- [x] 이 plan 을 새 형식으로 변환 (2026-10-18)
- [x] `read-points` plan 의 scratch 사본을 새 형식으로 변환하고 lint (2026-10-19) — 통과(Acceptance 4)
- [x] 단위 2 code-reviewer (2026-10-18) — REQUEST CHANGES, Major 3
- [x] fix loop 1회차 (2026-10-19) — plan-lint 코드펜스 수정은 단위 1 fixup, `skills/c/SKILL.md`·`skills/e/SKILL.md` 의 `/c`·`/e` 수정, `CLAUDE.md`·`agents/plan-reviewer.md`·`README.md` 문구
- [x] 1회차 targeted 재리뷰 (2026-10-19) — workflow `wf_48cbf48c-ab2`: code-reviewer NEEDS DISCUSSION, skeptic 이 5건 확인, blocker 없음
- [x] fix loop 2회차 (2026-10-19) — 들여 쓴 펜스·info string 펜스는 두 번째 단위 1 fixup, `skills/c/SKILL.md`·`skills/e/SKILL.md` 문구
- [x] 2회차 targeted 점검 (2026-10-19) — workflow `wf_aab130ca-6ea`: blocker 없음, R2-1·R2-4·R2-6 을 `skills/c/SKILL.md` 와 이 plan 에서 수정
- [x] `origin/main` 위로 rebase (2026-10-19) — PR #237, `skills/e/SKILL.md` 5단계 충돌 1건(main 문구 유지, 근거만 `# Tasks`), `skills/jira-task/SKILL.md` 3단계도 `# Tasks` 를 읽게 함
- [x] simplify 점검 (2026-10-19) — `scripts/plan-lint.js` 의 쓰지 않는 `parse()` 반환값 제거(단위 1 fixup), Acceptance 2·3 검색은 호환 안내만 남음
- [x] 사용자 확인 (2026-10-20) — 한국어 plan 페이지와 diff 페이지를 보고 커밋 지시, plan/log 분리 추가 지시
- [x] 단위 2 커밋 (2026-10-20) — `bash scripts/verify.sh changed` ALL PASS(skip 1건: PowerShell 설치 테스트, 이 서버에 PowerShell 없음·이번 변경과 무관)
- [x] 이 plan 의 기록을 `plans/2026-10-18-plan-format/plan-format-log.md` 로 옮기기 (2026-10-20)
- [x] 테스트 먼저 — `scripts/plan-lint.test.js` N14·N15 (2026-10-20) — N14 구현 전 실패 확인
- [x] 단위 3 설계 리뷰 (2026-10-20) — workflow `wf_96459bb5-09b`: plan-reviewer CONDITIONAL(강한 우려 5), 사용처 sweep 27곳
- [x] 단위 3 구현 (2026-10-20) — `scripts/plan-lint.js`, `CLAUDE.md`, `skills/dlc/SKILL.md`, `skills/e/SKILL.md`, `skills/improve/SKILL.md`, `skills/wiki/SKILL.md`, `agents/plan-reviewer.md`, `README.md` (32곳)
- [x] 단위 3 code-reviewer (2026-10-20) — workflow `wf_2efcf7e5-2b8`: APPROVE, Major 없음
- [x] 단위 3 fix loop 1회차 (2026-10-20) — `scripts/dlc-evidence-ledger.js`(plan log 편집은 plan drift 경고를 끄지 않음, 테스트 ⑪ʺ), `skills/c/SKILL.md`·`skills/wt/SKILL.md`·`skills/improve/SKILL.md` 문구, 참조를 "plan log" 로 통일
- [x] simplify 점검, `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-20) — workflow `wf_840bbe4e-320`: Acceptance 1·2·3·5·7 충족, 4 의 "read-points 무변경"은 runner 가 격리로 못 봐서 파일 수정 시각으로 확인(2026-10-16 이후 변경 0개), 6 은 머지 후
- [x] 사용자에게 단위 3 문구 확인받고 커밋(이 plan·log 포함) (2026-10-20) — plan·diff 페이지 확인, Acceptance 7 기준 변경 승인
- [x] commit-check 로 단위 1 의 fixup 정리 (2026-10-20) — 6커밋 → 3커밋, 단위 1 메시지를 지금 코드에 맞춤, 최종 내용 동일
- [ ] 머지 (`/e merge`) — 이 worktree 의 `skills/e/SKILL.md` M1–M6 을 따른다(main 사본은 아직 옛 버전)
- [ ] [post-merge] main 세션에서 공용 wiki 갱신 — log `# Deferred` 첫 항목의 목록(머지 직후 하지 않으면 dlc 가 `wiki/docs/dlc-details.md` §D 를 읽고 plan 본문에 `# Workflow Findings` 를 써서 `/e merge` M4 lint 에 걸린다)
- [ ] [post-merge] 머지 뒤 첫 새 세션: `/c` 가 새 형식 plan 의 첫 미완료 Task 를 짚는다(Acceptance 6)

# Acceptance
1. plan-lint 가 두 형식을 검사하고, 섞인 plan 을 거부하고, 코드펜스 안의 heading·체크박스를 무시하고, Acceptance 참조 검사를 유지한다 — `node scripts/plan-lint.test.js` 통과, `git ls-files 'plans/*/*-plan.md' | xargs node scripts/plan-lint.js` 가 출력 없이 exit 0.
2. CLAUDE.md §10 이 새 형식(Tasks 규칙, Decisions 규칙, 옛 형식 대응 줄)을 정의하고 §1·§9·묶음 절이 그에 맞다 — `rg -n 'Progress|Key Files|\bNext\b|Intent|6 ?H1|6개 섹션|6섹션' CLAUDE.md` 결과가 대응 줄과 §1 옛 형식 안내뿐.
3. skills·agents·early-stop 메시지·improve·jira-task·README 가 새 형식을 따른다 — 같은 `rg` 를 그 파일들에 돌리면 호환 안내만 나온다.
4. 실사용: 새 형식인 이 plan 이 `plan-lint` 를 통과하고(뒤에 `/e merge` M4 게이트도), `read-points` plan 의 scratch 사본이 변환되어 `plan-lint` 를 통과하며, `read-points` worktree 는 건드리지 않는다.
5. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 이 있으면 무관함을 보인다).
6. [post-merge] 머지 뒤 첫 새 세션에서 `/c` 가 진행 중인 새 형식 plan(예: 번역 작업 plan)의 첫 미완료 Task 를 다음 할 일로 보고한다.
7. 작업 기록이 plan 밖 `<slug>-log.md` 에 있다 — plan-lint 가 새 형식 plan 본문의 `# Review Disposition`·`# Deferred`·`# Workflow Findings` 를 위반으로 잡고 옛 형식은 통과시킨다(`node scripts/plan-lint.test.js`). 그 섹션을 쓰는 규칙·skill·agent·README 가 log 를 가리킨다(`rg -n 'Review Disposition|Deferred|Workflow Findings' CLAUDE.md skills/*/SKILL.md agents/*.md README.md` 결과에 작업 기록의 위치를 새 형식 plan 본문으로 지시하는 줄이 없다). 이 plan 의 기록이 `plan-format-log.md` 에 있다. (2026-10-20 추가 — 사용자가 지시한 범위. 통과 기준 변경: 이전 "결과가 log 정의·log 참조·옛 형식 대응표뿐" → 지금 문구, 위치와 무관한 설명 줄도 결과에 나와서. 사용자 승인 2026-10-20)

# Decisions
- wiki 결정: [[ops-doc-slimming]](§10 은 CLAUDE.md 에 둔다) → 따른다. "필수 6섹션 고정"([[plan-handoff]], unknowns-pass wontfix) → 사용자 요청으로 뒤집는다. 그 이유(6섹션 구조와 충돌)는 더는 성립하지 않는다.
- 정본: 의미와 쓰는 규칙은 CLAUDE.md §10, 코드로 검사할 수 있는 것은 `plan-lint`(`planFormat` 이 형식을 정한다). 다른 파일은 섹션을 나열하지 않고 §10 을 가리킨다.
- 형식 판별: 기본은 새 형식. `# Tasks` 없이 옛 형식 전용 섹션(`Progress`, `Next`, `Key Files`, `Intent`)이 있을 때만 옛 형식. 둘이 같이 있으면 오류. 코드펜스 안의 heading·체크박스는 무시. 기각: frontmatter `format:` 키(의례만 하나 늘고 읽는 곳이 없다).
- 옛 plan: lint 는 두 형식을 계속 받는다. 옛 형식으로 진행 중인 plan 은 끝날 때까지 옛 형식(§10 대응 줄 하나). 기각: 다음에 쓸 때 진행 중 plan 을 변환(옛 worktree 의 lint 가 거부해 `/e merge` M4 가 막힌다).
- Tasks: 체크한 항목(하위 항목 포함)은 `(YYYY-MM-DD)`, 커밋 sha 는 적지 않는다. 파일을 바꾸는 Task 는 경로를 backtick 으로 적는다(Key Files 대체). 급한 일은 미완료 맨 위. 미완료 `NEEDS-HUMAN:` Task 가 하나라도 있으면 `/c` 가 멈춘다. done plan 에는 `[post-merge]` 항목만 미완료로 남는다. `/c` 는 그 Task 를 끝낸 커밋이 있을 때만 체크하고, `wip:`·`fixup!` 커밋은 근거가 아니다.
- 머지 대기: PR 이 `OPEN` 인 done plan 은 머지를 기다리는 중(`/e merge` QUEUED/UNKNOWN). `/c` 가 PR 상태를 읽는다. PR 이 없거나 상태를 모르면 보통 done plan. 기각: "PR 이 `MERGED` 가 아님"(PR 없이 로컬 머지한 done plan 도 걸린다). 기각: done plan 에 "`/e merge` 재실행" Task 쓰기(QUEUED 중에는 head 를 바꾸면 안 돼 커밋할 수 없고, done plan 에는 `[post-merge]` 만 남는다).
- 머지 Task: `/e merge` 를 실행하는 Task(`/e` 가 쓴 재실행 Task 포함). `/e merge` 를 언급만 하는 Task(예: "`/e merge` 문구 고치기")는 보통 Task. `/e merge` M1 이 push 전에 다른 미완료 Task 를 거부하고(새 형식 plan 만), M4 가 머지 Task 를 전부 체크하며, 복구 때 다시 미완료로 돌린다. 기각: M4 에서 미완료 Task 를 거부(push 뒤에 돌고 `/e` 자신의 재실행 Task 에 걸렸다). 기각: "`/e merge` 를 언급하는 모든 Task"(`/e` 관련 미완료 작업이 완료로 체크된다).
- Acceptance 는 번호 항목 유지(`1.`, `1. [ ]` 허용): plan-lint 가 번호 항목을 세고 `/e` M1 이 미체크 박스로 막는다.
- Decisions 는 현재 상태만: 바뀐 결정은 고쳐 쓰고 밀려난 안은 기각 목록으로. plan 은 작업 끝에만 커밋돼 세션 안의 이력을 git 이 남기지 못하기 때문이다. Acceptance 변경은 이전 → 새 값과 사용자 승인을 남긴다.
- `/c` 의 NEEDS-HUMAN 정지는 새 예외 6 이 아니라 예외 1(blocked)에 합친다. "예외 5종" 참조가 그대로 유효하다.
- Codex 생략 사유는 기록하지 않는다(사용자, 2026-10-19): Codex 는 선택이고 Claude subagent 리뷰는 어차피 필수다. reviewer 출력의 `Codex 미가용` 한 줄은 한도 캐시가 쓰므로 남긴다.
- 언어(사용자, 2026-10-20): 사용자에게 보이는 것(답변·plan)은 한국어, 내부(CLAUDE.md·skills·agents·hook 문구·subagent 지시와 보고·생각)는 영어. 이 브랜치의 규칙 파일은 한국어 그대로 두고 번역은 다음 작업에서. 기각: plan 을 영어로(2026-10-19 결정 — 사용자가 plan 을 직접 확인하므로 2026-10-20 에 한국어로 변경).
- 작업 기록 분리(사용자, 2026-10-20): `# Review Disposition`·`# Deferred`·`# Workflow Findings` 는 같은 폴더의 `<slug>-log.md` 에 둔다. plan 은 Task 체크 말고는 거의 바뀌지 않는 문서가 된다. 근거: BMAD·superpowers·compound-engineering 이 실행 기록을 계획 본문과 분리한다(조사 2026-10-20). 새 형식 plan 본문에 이 섹션이 있으면 plan-lint 위반이고 옛 형식은 예외. log 는 frontmatter 없이 필요할 때 만들고, plan-lint 대상이 아니며, plan 과 같이 커밋한다(`plans/*.md` 라 secret 검사 대상). 기각: plan 끝에 "작업 기록" 구역으로 남기기(여전히 계속 바뀌는 문서로 보인다). 기각: Deferred 를 GitHub issue 로 옮기기(다른 repo·오프라인에서 못 쓰고 도구가 하나 늘어난다). 감수: log 에는 Acceptance 참조 검사가 돌지 않는다(기록용이라). H2(`## Deferred`)로 쓰면 lint 를 피한다(드문 경우라). 기록을 log 로 옮기는 Write 가 activity 신호를 1건 남긴다(영향 작음).
- 롤백: 단위 3 만, 또는 3 → 2 순서로 되돌린다(3 이 2 가 만든 같은 줄을 다시 고친다). 단위 3 만 되돌리면 이미 만든 log 는 남지만 lint 에 영향이 없다. 새 형식 plan 이 하나라도 있으면 단위 1 은 남긴다.
- 커밋 단위: 1) `feat(plan-lint): accept the Tasks-based plan format` — 완료, fixup 3개 포함 2) `feat(plans): switch plan files to Goal, Tasks, Acceptance, Decisions, Blockers` — 완료, CLAUDE.md·skills·agents·스크립트 메시지·README 3) `feat(plans): keep review and deferred records in a separate log file` — plan-lint 규칙, `dlc-evidence-ledger` 의 plan 편집 판정, CLAUDE.md·skills·agent·README, 이 plan 과 log.

# Blockers
