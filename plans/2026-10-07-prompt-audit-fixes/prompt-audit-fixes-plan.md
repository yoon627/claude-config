---
title: prompt-audit-fixes — prompt-audit 반영 · 검증된 것만 커밋 (머지 정책은 별도 plan 으로 분리)
status: done
started: 2026-10-07
updated: 2026-10-07
---

# Goal
1) `/claude-api prompt-audit`(2026-10-07)이 찾은 틀린 사실·이력 서술·description 비대화를 고친다. 2) 검증·확인되지 않은 변경은 커밋하지 않게 §8 예외를 없앤다. (머지 정책은 `# Deferred` 로 분리.)

# Intent
- Problem: audit 보고서(세션 scratchpad, 요지는 `plans/2026-10-07-conclusion-format/conclusion-format-plan.md` `# Deferred`)가 실제 버그 2건(`skills/wt` `<default>` 이중 `origin/` → rm 미머지 탐지 실패, CLAUDE.md "Agent 도구에 effort 없음" 오기)과 규칙 충돌 4건, 이력·날짜 조건·description 비대화를 찾았다. 사용자는 "확인·검증된 것만 커밋"을 원칙으로 확인했고(2026-10-07), 기존 §8 은 "검증 명령 미식별이면 커밋하되 보고"로 그 반대였다.
- Constraints (사용자 확인 2026-10-07):
  - C-3 wt rm 은 "로컬 default 에만 머지됨(origin 미반영)"을 미머지와 구분해 경고.
  - C-4 wt description 에 dlc 가 worktree 를 만들 때의 호출도 명시.
  - audit F-3(`RTK.md`)은 제외 — untracked·`rtk init -g` 가 재생성.
  - C-1·C-2(완료 판정·머지 정책)는 이 plan 밖 — `# Deferred`.
- Out of scope: 머지 정책 전체(`# Deferred`). 검증 시간 개선 3건(conclusion-format plan `# Deferred`). `docs/codex-review.md:56` 공개 점검은 확인만. audit low(L-1~L-7) 변경 없음.
- 분할: 묶음 아님 — 처음엔 세 목적을 한 plan 으로 묶었으나(같은 §3-6/§8 문단·verify 50분 고정비) plan-reviewer 가 머지 정책이 종결 경로 전체를 바꾼다고 지적해 그 목적만 후속 plan 으로 분리(사용자 승인 2026-10-07). 남은 두 목적은 각각 독립 커밋.

# Progress
- 2026-10-07: worktree 생성(base 로컬 main@15837ce — origin 보다 1커밋 앞서 wt 의 origin base 대신 로컬 main), audit 보고서 확인, 충돌 4건 사용자 결정, plan 작성. 단위 1·2 구현·커밋(audit diff F-3 제외 적용 + (4) 축·C-3·C-4 수동, `verify.sh syntax` ALL PASS, Acceptance 1 rg 무매칭, `<default>` 유도 관찰: 옛 `origin/origin/main` = fatal, 새 유도 = `main`·exit 0). README 316·340 은 description 이 아니라 동작 설명이고 동작 불변이라 유지.
- 2026-10-07 (cont.): plan-reviewer+Codex CONDITIONAL — 단위 1·2 지적 반영(fixup: wt 생성 경로·rm-recovery 의 `<default>` 정의, §8 검증 규칙에 `/e` WIP·공용 wiki 예외와 무인 흐름 보류·§7 수동 검증 인정), 단위 3 은 사용자 승인으로 분리.
- 2026-10-07 (cont.): code-reviewer(+Codex high) REQUEST CHANGES → 처분 반영(아래). §8 단위 2 문구는 그 규칙대로 사용자 diff 확인 받음("확정"). simplify: 문서 문구 변경뿐이라 대상 없음. 전체 verify exit 0·FAIL 0, `ALL PASS (skip: install-hooks.test.js(case) record-verified.test.sh)` — 허용된 환경 skip 2건. Acceptance 1(F-9·F-10 철회로 두 날짜 패턴은 rg 에서 뺌)·2(`origin/<default>` 유도 3곳 + base sha `origin/<default>` 읽기, `rev-parse --short origin/main`=1086b28 관찰)·3·4·5 충족. 판정 DONE.

# Next
(없음 — 로컬 ff-only 로 종결. 후속은 `# Deferred` 순서대로: docs/ 추적 제외 → 부트스트랩 플러그인 설정 → 머지 정책 plan. 검증 시간 개선은 conclusion-format plan `# Deferred`.)

# Decisions
- 선행 decision: 공용 wiki `decision/e-merge-mode`·`dlc-wt-autoflow` — 이 plan 은 종결 경로를 바꾸지 않으므로 해당 없음(머지 정책 plan 에서 다룬다).
- 커밋 단위: 1) `docs: fix stale facts and dated phrasing found by prompt audit` 2) `docs(claude-md): commit only verified or confirmed changes`. 같은 파일을 두 단위가 고쳐 순서대로 구현·커밋했다.
- 머지 정책(단위 3)을 분리 — plan-reviewer 강한 우려 1~5·7(아래 `# Deferred`)이 "M1 게이트 조건 추가"가 아니라 종결 경로 재설계를 요구하고, 정책 결정이 6건 더 필요하다(사용자 승인 2026-10-07).
- 이 plan 의 종결은 로컬 ff-only — 현행 §8 은 medium 을 `/e merge` 로 보내지만 사용자가 merge 커밋 없는 로컬 ff 를 원했고(2026-10-07) 종결 방식 변경을 승인. plan-reviewer 권고대로 작업 브랜치에서 done 커밋 → ff → 실패 시 브랜치에서 `in_progress` 복구 순서로 한다.

# Key Files
- `CLAUDE.md` §8(136)·§5(95)·머리(3)·§3-6(51 (4) 축)·§8(a)(142)·§10(209·227).
- `skills/wt/SKILL.md` — description, 생성 `<default>`(71), rm `<default>`·미머지 구분(114), 134. `skills/wt/references/rm-recovery.md` §A.
- `skills/e/SKILL.md` — description, 83.
- `skills/dlc/SKILL.md` — 45·48 날짜 조건, 163 검증 미식별.
- `skills/{c,improve,jira-worklog}/SKILL.md`, `agents/code-reviewer.md` — description·이력.

# Acceptance
1. audit F-1·F-2·F-4~F-17 반영: `rg -n "effort 파라미터가 없어|짧고 강하게|예전처럼|이 변경 이전에 만든|예전엔 정확일치|2026-09-09 도입|2026-09-16 도입|AI-Native SDLC|wiki-shared-layer\)|구 /audit 승계\)과|통과 검토 금지, 비판|①대상|④ 축" CLAUDE.md skills agents` 무매칭.
2. wt 의 `<default>` 유도가 실제로 `main` 을 낸다(생성·rm 두 곳 + rm-recovery 정의 일치) — `git symbolic-ref --short refs/remotes/origin/HEAD` 에서 `origin/` 을 떼면 `main`, `git branch --merged origin/main` 이 오류 없이 돈다(관찰). rm 문서에 로컬 전용 머지 구분 경고가 있다.
3. §8 에 "검증 미식별이면 커밋" 문구가 없고(`rg -n "커밋하되 보고" CLAUDE.md skills` 무매칭) "커밋하지 않고 검증 방법을 묻는다" + `/e` WIP·공용 wiki 예외 + 무인 보류가 있으며 dlc 163 이 같은 뜻이다.
4. description 수정 후 trigger 문구 유지 — `/e`·"오늘 여기까지", `/wt` 호출 형태, `/c`·"이어가자" 가 각 description 에 남음(rg).
5. `bash scripts/verify.sh` 마지막 줄 `ALL PASS` — skip 은 이번 변경과 무관한 환경 skip(jq 미설치, 구 git case)만, 사유 원문 기록. 변경 확정 후 1회.

# Deferred
- **머지 정책 plan (다음 착수, 사용자 결정 2026-10-07)**: 모든 repo 종결 = 로컬 `git merge --ff-only`(merge 커밋 없음). 원격 머지(`/e merge` M6)는 repo 가 허용을 명시한 곳에서만. default 브랜치 머지 금지도 repo 단위 표기(사용자가 직접 적음, `~/.claude` 에는 이름 없는 일반 규칙만 — §11). `/c` 완료 판정은 로컬 default 머지도 완료로(C-1 변경, you-should-know 플러그인 지적). 착수 전 정할 것(plan-reviewer+Codex, 파일 확인 ✅):
  1. done 커밋 시점 — 작업 브랜치에서 done 커밋 → ff → 실패 시 `in_progress` 복구(M4 와 같은 구조), 실행 주체(dlc 16 / `/e`).
  2. 묶음 intent closed 판정을 그 done 커밋에 포함(`CLAUDE.md` §10 214, `skills/e` 44).
  3. ff 불가 분기표(게시 여부 × ff 가능 × rebase 충돌) — 원격 머지가 막히면 기존 출구(`/e merge`)가 사라진다. §3-6(51)·dlc 161 의 "마무리 = `/e merge`" 선택지 교체.
  4. default 머지 금지 repo 의 정상 종결(사용자 확인 done + worktree 보존?), 두 표기 공존 시 우선순위, 원격 PR 생성 허용 여부.
  5. `/wt` 생성 base — 로컬 default 가 origin 보다 앞서면 로컬 기준(안 바꾸면 종결마다 rebase+전체 verify). 여러 머신 로컬 ff 후 origin 과 갈라짐 복구 절차.
  6. 표기 판정 위치·revision — `git show <default>:CLAUDE.md`(브랜치 자기 허가 차단) + main worktree 의 `CLAUDE.local.md`(untracked 라 worktree 에 없음) + `<repo>/.claude/CLAUDE.md` 포함 여부, `rg -x` 정규식. `~/.claude` 허용은 `~/.claude/CLAUDE.local.md` 에(전역 CLAUDE.md 는 모든 repo 세션에 주입돼 허용이 샌다). Acceptance 에 정의 문장이 단독 줄로 매칭되지 않는지.
  7. 영향 범위: `CLAUDE.md` 139·182·214, `docs/worktree-lifecycle.md` §B·§E, `skills/e` description·43·98·134·136, `skills/c` 42·74(전환기 `/e merge` 재실행 대기 plan), README 347·349, PR 전용 CI(plan-lint) 상실 기록. 공용 wiki `dlc-wt-autoflow:40`·`e-merge-mode` 갱신은 main 세션에서.
- **docs/ 추적 제외 (사용자 결정 2026-10-07, 이 plan 머지 후 별도 작업)**: `docs/codex-review.md:56` 에 다른 repo 이름이 노출된 것을 계기로 `docs/` 전체를 gitignore + `git rm --cached`. 사용자 판단: 혼자 쓰는 repo 이고 다른 머신엔 worktree 가 없어 문제 없음. 해야 할 것: 참조 34곳(CLAUDE.md·README·agents 3·skills dlc/e/wt·rm-recovery·scripts/dlc-doc-drift.test.js·scripts/bootstrap/README)을 공용 wiki 처럼 절대경로 `~/.claude/docs/...` 로 바꾼다(새 worktree 에는 untracked 파일이 없어 상대경로가 깨진다). 다른 머신은 docs 를 수동 복사해야 함. 이미 push 된 이력의 이름은 남는다(history rewrite 는 별도 승인).
- **부트스트랩 플러그인 설정 (사용자 요청 2026-10-07, docs 작업 다음)**: `scripts/bootstrap/setup.sh`(macOS)·`setup.ps1`(Windows)에 멱등 단계 추가 — `claude plugin enable cc-plugin-you-should-know@builtin`(Claude Code 2.1.287 미만이면 경고만), `claude plugin install session-report@claude-plugins-official`, `claude plugin install receipts@claude-plugins-official`. `settings.json` 추적은 하지 않는다(memory: 도구가 쓰는 설정은 tracked 금지). macOS 실행은 이 Windows 세션에서 관찰 불가 — 사용자 맥 실행 확인이 검증.
- `/e merge` M6 의 `--merge` → `--rebase`(merge 커밋 제거)는 보류 — rebase 머지는 SHA 가 바뀌어 `git branch --merged`·§8(a) 자동 정리 판정이 깨진다. 원격 머지가 기본 차단되면 필요성이 낮다.

# Review Disposition
- plan-reviewer(+Codex medium, CONDITIONAL):
  - 강6 단위 2 가 `/e` WIP 와 모순 → fix(예외 2종·무인 보류·§7 수동 검증 인정).
  - 약 F-2 범위(생성 경로 71-73) → fix(wt 71·rm-recovery §A 정의).
  - 약 단위 2 "확인"의 정의 → fix(§7 수동 검증 절차 실행을 검증으로 인정).
  - 강1~5·7, 약 영향 범위·CI·`/c`·Acceptance 4 → defer(머지 정책 plan, `# Deferred` 1~7).
- code-reviewer(+Codex high, REQUEST CHANGES):
  - Major wt 72·80 base sha 를 로컬 `<default>` 에서 읽음(이번 변경의 회귀) → fix(`origin/<default>`).
  - Minor dlc 48 ↔ plan-reviewer 32 날짜 기준 불일치 → fix(audit F-9·F-10 철회 — 리뷰어는 이어받은 plan 인지 알 수 없어 날짜가 유일한 기계 기준. audit 도 plan-reviewer 쪽 날짜 유지를 권함).
  - Minor dlc 163 이 §8 보다 좁음 → fix(§8 검증 수단 3종).
  - Minor 기록 커밋(plan·commit-check 재구성) 예외 누락 → fix(대상은 작업 변경으로 한정).
  - Minor(논의) 규칙 문구의 "관찰" 정의 없음 → fix(사용자 diff 확인 또는 실제 세션 관찰) + 이 브랜치 단위 2 문구 사용자 확인 받음.
  - Nit improve "/audit" 어휘 → wontfix(`/audit` skill 없음, 명시 호출 전용).
  - Open Agent effort 실존 → 확인(이 세션 Agent 도구 스키마에 `effort` 있음). Open `docs/codex-review.md:56` repo 이름 → 사용자 결정으로 docs/ 추적 제외(`# Deferred`).

# Blockers
(없음)
