# Review Disposition
단위 2 code-reviewer (2026-10-18), REQUEST CHANGES:
- Major 1, QUEUED/UNKNOWN 재실행 신호를 쓰는 곳이 없었다 — fix: `/c` 예외 5 가 PR 상태를 읽고, `/e` M2 는 done plan 을 건드리지 않으며, §10 에 한 줄.
- Major 2, `/c` sync 표에서 커밋 행이 빠졌다 — fix: 행을 되살려 체크된 Task 와 비교하고, `/c` 는 커밋 날짜를 적는다.
- Major 3, M4 가 push 뒤에 `/e` 자신의 재실행 Task 에 걸려 멈췄다 — fix: 검사를 M1 (5) 로 옮기고 M4 는 머지 Task 를 전부 체크.
- Minor, M4 에 옛 형식 줄이 없다 — fix(2회차, 처음엔 wontfix): "머지 Task 가 없으면 추가"가 옛 plan 을 섞인 형식으로 만들고 `read-points` 가 이 경로를 탄다. M4 에 옛 plan 은 `# Progress` "PR #N"·`# Next` 비움을 적었다.
- Minor, 머지 단계가 main 의 옛 `/e` 를 쓴다 — fix: 머지 Task 에 이 worktree 의 M1–M6 을 따르라고 적었다.
- Minor, plan-reviewer 14항이 `Open questions:` 를 필수로 요구 — fix: 필수 목록에서 뺐다.
- Minor, NEEDS-HUMAN 을 첫 Task 에서만 봤다 — fix: 미완료 Task 전부.
- Minor, M1 의 post-merge 패턴이 `- [ ]` 만 — fix: `[post-merge]` 접두로 판정.
- Minor, Codex 생략 사유를 둘 곳 — fix: 규칙 자체를 지웠다(사용자).
- Minor, §10 "빈 헤더 유지"와 lint 의 체크박스 최소 1개, 체크된 하위 항목의 날짜 — fix: §10 에 둘 다 적었다.
- Minor, Acceptance 6 이 관찰할 수 없었다 — fix: 고쳐 썼다.
- Minor, §10 은 PR 요약이 Goal 첫 문단만 쓴다고 했지만 M3 는 그렇지 않다 — fix: §10 에서 그 말을 지웠다.
- Nit, 체크박스 검사가 코드펜스를 무시하지 않았다 — fix: 단위 1 fixup, 테스트 N12.
- Nit, ```` 펜스가 안쪽 ``` 에서 닫혔다 — fix: 단위 1 fixup, 테스트 N13.
- Nit, 잘못된 날짜가 통과 — wontfix: 날짜는 기록용이라 형식 검사로 충분하다.
- Nit, 쓰지 않는 export — fix: `lintPlan`·`planFormat` 만 export.
- Nit, 테스트 N8 이 N1 과 중복 — fix: N1 에 합쳤다.
- Nit, README 에 "~로 변경"이 남음 — fix.
- Nit, README 의 `/c` 예외에 NEEDS-HUMAN 이 없음 — fix.
- Nit, plan Task 줄에 결과가 날짜보다 앞 — fix.
- Nit, `/e` 5단계와 jira-task 의 Tasks 범위 표현이 다름 — fix.
- Nit, `/c` 가 적는 날짜가 정의되지 않음 — fix: 커밋 날짜.
- Nit, "(138 plans)"가 금방 낡는다 — fix: 개수를 지웠다.
- Open, `read-points` 가 같은 파일을 고친다 — defer: Deferred 참고.

1회차 재리뷰 (2026-10-19, workflow `wf_48cbf48c-ab2`, Codex CLI 미설치), major/minor 는 skeptic 이 각각 확인:
- Major F1, `/c` 가 커밋이 있다는 것만으로 Task 를 체크해 `wip:` 커밋이 끝나지 않은 일을 완료로 표시 — fix: 그 Task 를 끝낸 커밋만 근거, `wip:`·`fixup!` 은 근거가 아니다.
- Minor F2, `/c` 예외 5 가 "PR 없음"을 머지 대기로 봤다 — fix: `OPEN` PR 만.
- Minor F3, "`/e merge` Task"가 정의되지 않았다 — fix: `/e merge` 를 실행하는 Task(재실행 Task 포함).
- Minor F4, 복구가 "그" Task 를 체크 해제하는데 M4 는 여러 개를 체크 — fix: M4 가 체크한 Task 를 미완료로.
- Minor F5, M1 (5) 에 옛 형식 plan 규칙이 없었다 — fix: 옛 형식에는 적용하지 않는다.
- Nit F6, plan-lint 가 들여 쓴 펜스를 놓치고 "```js" 가 열린 펜스를 닫았다 — fix: 두 번째 단위 1 fixup, 테스트 N12·N13 확장.
- Nit F7, done plan 규칙을 `/e merge` 만 강제 — wontfix: 규칙은 쓰는 쪽 모두에 적용되고 `/e merge` 가 머지 전 관문이다.
- Nit(sweep), M3 중단 규칙이 Task 두 개로 읽힐 수 있다 — fix: 사유를 담은 재실행 Task 하나.
- Nits W1–W12(sweep), 낡게 될 공용 wiki 문구 — defer: Deferred 에 추가.

2회차 점검 (2026-10-19, workflow `wf_aab130ca-6ea`), NEEDS DISCUSSION, blocker 없음. fix loop 상한(2회)에 닿아 더 리뷰를 돌리지 않고 사용자가 최종 diff 를 확인한다:
- Minor R2-1, `/c` 예외 5 가 PR 이 merge queue 에 있는 동안 재실행을 권했다(새 push 는 큐에서 뺀다) — fix: 큐가 끝날 때까지 기다린 뒤 재실행.
- Minor R2-2, 실제로는 머지된 UNKNOWN 뒤에 `/c` 가 보통 done plan 으로 보여 `/e` 5–7단계가 돌지 않는다 — defer: 이 브랜치가 만든 문제가 아니고, 거기서 `/e merge` 를 다시 돌리면 squash 머지 repo 에서 깨진다. Deferred 참고.
- Minor R2-3, M3 중단 규칙과 M4 timeout 복구에 옛 형식 문구가 없다 — false-positive(skeptic 이 반박): 둘 다 §10 대응 줄이 덮는 plan 에서 돈다.
- Minor R2-4, `/c` 커밋 점검이 `git log -15` 를 읽어 rebase 뒤 base 커밋까지 잡는다 — fix: 다음 행과 같은 범위인 `origin/main..HEAD`.
- Minor R2-5, `origin/main` 154b042(PR #237)가 `skills/e/SKILL.md` 5단계·`skills/jira-task/SKILL.md`·`README.md` 를 고치고 `# Next` 참조를 더했다 — fix: `origin/main` 위로 rebase 하고 jira-task 가 `# Tasks` 를 읽게 했다.
- Nit R2-6, Decisions 줄이 M4 의 Task 체크 자체를 기각한 것처럼 읽혔다 — fix: 고쳐 썼다.

단위 3 설계 리뷰 (2026-10-20, workflow `wf_96459bb5-09b`, plan-reviewer CONDITIONAL, Codex CLI 미설치):
- 강한 1, "in english 제거"가 번역 작업 취소일 수 있다 — false-positive: 그 요청은 답변 맨 위 "In English" 줄을 빼라는 것이고, 파일 번역은 그 전에 사용자가 직접 지시했다(2026-10-20).
- 강한 2, `/e merge` M4 가 log 를 커밋하지 않고 정리 조건이 log 를 모른다 — fix: M4 가 plan 과 log 를 커밋, `skills/e/SKILL.md` 7단계 조건 5 와 CLAUDE.md §8 의 "미커밋 plan" 을 plan·log 로.
- 강한 3, 공용 wiki 참조 문서가 계속 plan `# Workflow Findings` 를 지시한다 — fix: Deferred 목록 보강, 머지 직후 처리하도록 `[post-merge]` Task 로 올림.
- 강한 4, 롤백 줄이 단위 3 을 반영하지 않았다 — fix: 3 만 또는 3 → 2 순서.
- 강한 5, Acceptance 7 의 검색에 범위가 없다 — fix: 파일 목록 명시.
- 약한, log 에는 Acceptance 참조 검사가 안 돈다 — wontfix: 기록용이라 감수, Decisions 에 기록.
- 약한, log 만 고쳐도 plan drift 경고가 꺼진다 — defer: 회귀는 아님, Deferred 참고.
- 약한, 위반 메시지가 `<slug>-log.md` 자리표시자 — wontfix: slug 는 plan 파일 이름 그대로라 바로 알 수 있다.
- 약한, H2 로 쓰면 lint 를 피한다 — wontfix: 드문 경우라 감수, Decisions 에 기록.
- 약한, 기록 이동 Write 가 activity 신호 1건 — wontfix: 영향 작음.
- 약한, self-flag 줄(plan)과 처분(log)이 갈린다 — fix: dlc 11단계 리뷰어 입력을 plan·log 경로로.
- 약한, plan Task 가 실제보다 늦다 — fix: 체크.
- 약한, plan 폴더가 untracked — fix: 단위 3 커밋으로 해소.
- 누락, 옛 형식 plan 옆에 log 가 생기는 경우 — fix: CLAUDE.md 대응표에 "log 의 작업 기록 ↔ plan 본문의 같은 섹션", improve 는 둘 다 읽음.
- 누락, 묶음 모드 기록처 3곳 — fix: dlc 48·plan-reviewer 33·CLAUDE.md §10 을 "첫 plan 의 log" 로.
- 누락, 다른 repo 에서는 lint 가 안 돈다 — wontfix: 이전과 같고 규칙 문구가 지킨다.
- 누락 테스트(펜스 안 `# Deferred`, 섞인 형식 + 기록 섹션) — wontfix: 펜스는 N8·N9 와 같은 처리, 섞인 형식은 혼재 위반이 먼저 나온다.

단위 3 code-reviewer (2026-10-20, workflow `wf_2efcf7e5-2b8`), APPROVE, Major 없음. major/minor 는 skeptic 이 각각 확인:
- Minor F1, `dlc-evidence-ledger.js` 가 plan log 편집도 plan 편집으로 쳐서 plan drift 경고가 꺼진다 — fix: `*-plan.md` 만 센다, 테스트 ⑪ʺ(구현 전 실패 확인). 설계 리뷰 때 defer 했던 항목을 뒤집었다(새 근거: plan log 가 fix loop 마다 고치는 파일이 되어 실제로 경고가 사라진다).
- Minor F2, 공용 wiki 갱신 목록에 3곳 누락 — fix: `dlc-details` §C, `wiki-shared-layer` 27·37행, `worktree-lifecycle` §B 추가.
- Minor F3, `/c` 가 plan log 를 읽지 않아 이전 처분·Deferred 를 이어받지 못한다 — fix: `/c` 2단계와 §10 "시작" 에 plan log 읽기.
- Minor F4, dlc 16단계 경로 확정이 plan log 를 빠뜨릴 수 있다 — false-positive(skeptic 이 반박): CLAUDE.md §10 정의가 "plan 과 같이 커밋"을 정하고 `/e` 7단계 조건 5 가 미커밋 plan log 를 막는다.
- Nit F5, `skills/improve/SKILL.md` 줄 끝과 `skills/wt/SKILL.md` 의 "미커밋 plan" — fix.
- Nit F6, 리뷰어 입력에 "(있으면)" 없음 — fix.
- Nit F7, Acceptance 7 통과 기준을 글자 그대로 적용하면 위치와 무관한 설명 줄 때문에 통과하지 못한다 — fix: 기준 문구 변경, 사용자 승인(2026-10-20).
- Nit F8, "log" 가 wiki 의 `log.md` 와 헷갈린다 — fix: 참조를 모두 "plan log" 로(12곳).

# Deferred
- 공용 wiki(main 세션): `pages/concept/plan-handoff.md`(형식과 뒤집은 결정), `docs/dlc-details.md`(`# Intent` → Goal 라벨 불릿, §C 16 Report·§D 의 `# Deferred`·`# Workflow Findings` 기록처 → plan log), `pages/decision/workflow-failures.md`(기록처 → plan log), `pages/decision/wiki-shared-layer.md`(27·37행 plan `# Deferred` → plan log), `docs/worktree-lifecycle.md` §E(`# Next` 열, QUEUED/UNKNOWN 행은 plan 무변경)·§B(미커밋 plan → plan·log), `docs/codex-review.md`(생략 사유는 reviewer 출력에만), `pages/decision/e-merge-mode.md`(머지 대기 = PR `OPEN`), `pages/concept/claude-codex-collaboration.md`(생략 사유 규칙 삭제), `pages/decision/evidence-gate.md`(NEEDS-HUMAN Task), `deferred-and-scope-boundary`(Deferred 기록처 → log), `lesson-parallel-duplicate-implementation`, `self-diagnosis-and-improvement-status`, `dlc-development-cycle`, `unknowns-discovery`, `feedback-memory`, `index.md`, `log.md`.
- 다음 작업(사용자, 2026-10-20): 1) 결론 블록 완전 제거(CLAUDE.md §3-6 형식 규칙, `scripts/dlc-early-stop.js` 검사 4와 테스트, skill·agent 사본 — 사용자 결정 2026-10-20). "미확인" 표시는 §1 확신도 표시(✅⚠️❌)가 이어받는지 확인 2) CLAUDE.md·skills·agents 를 한국어로 먼저 줄이기(규칙 목록 대조, 모순 7곳 수정). 규칙 3개도 이때 넣는다(사용자, 2026-10-20): 추천은 근거와 함께만 내고 확인 못 한 안은 ⚠️추정으로 말한다 · 추천을 바꿀 때는 새 근거를 말하고 질문만으로 바꾸지 않는다(§1 "추측 금지"·"아부 금지" 줄 보강) · dlc draft plan 단계에서 정해진 단계를 Tasks 에 처음부터 전부 적고, 나중에 더하는 Task 에는 이유를 적는다(dlc 3단계 한 줄) 3) 영어로 옮기기: CLAUDE.md·skills·agents, hook 주입 문구, MEMORY.md·memory, 하네스 참조 문서(`wiki/docs/`). 사용자에게 보이는 것(답변·plan)은 한국어, subagent 지시·보고는 영어. README·코드 주석은 범위 밖.
- 실제로는 머지된 UNKNOWN 뒤의 `/e merge`: plan 은 done, PR 은 `MERGED` 인데 `/e` 5–7단계(Jira·worklog·정리)가 돌지 않았고 `/c` 도 그쪽을 가리키지 않는다. 또 M4 가 이미 done 인 plan 을 다시 커밋한다. 둘 다 이 브랜치 이전부터 있던 문제(리뷰 R2-2, 2026-10-19).
- `read-points` worktree 도 `agents/code-reviewer.md`·`skills/dlc/SKILL.md`·`README.md` 를 고친다. 이 브랜치가 들어간 뒤 그쪽에서 머지 충돌이 예상된다.
