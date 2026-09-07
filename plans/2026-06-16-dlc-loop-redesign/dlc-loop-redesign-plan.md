---
title: dlc-loop-redesign — dlc를 자가검증 acceptance 루프로 진화
status: in_progress
started: 2026-06-16
updated: 2026-09-08
---

# Goal
dlc를 "구체적 목표 → 단일 루프(act→verify→self-correct)로 요구사항 충족까지 반복 → 완료/문제 시 알림" 형태의 자가검증 루프로 진화. 검증을 '테스트 통과'가 아닌 'acceptance(요구사항 충족)'에 결속. (사용자 8개 요구 + 궁극목표.)

# Progress
- 2026-06-16: ultracode 워크플로(현행분석 + loop engineering 리서치 + llm-wiki/okf 정체) + codex 인라인 리뷰로 진단·설계 종합. 핵심 plan-경로 결함 직접 재확인(Grep/Glob). 사용자 3대 결정 확정(Decisions). P0 착수.
- 2026-06-16: **P0 완료**. dlc:8 → `<main>/plans/<YYYY-MM-DD>-<slug>/<slug>-plan.md` 고정, `/wt rm` 안전검사에 gitignored-plan 가드(`git -C <대상> status --porcelain --ignored`) 이식. worktree `dlc-loop-redesign` 커밋 `6c703d2` (2 files, 미push). 자기리뷰서 `-C <대상>` 누락 버그 발견·수정(/wt rm 대상≠cwd), codex 병행 리뷰 통과(제기 2건=`*-plan.md` 외 커버·c/e dated-dir 매칭 모두 기존 처리 확인). 검증: 잔존 `.claude/plans` 0건 + dlc/c/e 경로 정합 grep 확인(테스트 surface 없는 md 변경).
- 2026-09-08: **P0 종결 — 브랜치 `6c703d2` 는 머지하지 않고 현재 main 기준으로 재적용**(브랜치 `dlc-p0-merge`). 3개월간 main 이 371커밋 나가며 P0 의 전제가 무효가 됐다: `plans/` 가 tracked 로 전환돼(`.gitignore` `!/plans/`) worktree-local plan 은 더 이상 gitignored 소실 대상이 아니고, `skills/c/SKILL.md:19-21` 이 이미 "양쪽(`<ROOT>`·main worktree) 을 본다 — plans/ 는 브랜치별 독립" 으로 진화했다. 따라서 "항상 main worktree 에 둔다" 강제는 폐기하고, **실제로 남아 있던 결함 2건만** 반영: (1) `skills/dlc/SKILL.md:8` 의 `.claude/plans/<slug>-plan.md` → §10 dated-dir 형식 + ROOT double-nest 주의, (2) `skills/wt/SKILL.md` rm 안전검사에 `--ignored` 점검 누락(브랜치 원문의 "plans/ 가 ignored" 서술은 현재 사실과 달라 `.env`·settings.local 기준으로 고쳐 적용). README:298 도 같은 브랜치에서 동기화.
- 2026-06-17: `/e` 체크포인트. 신규 변경 없음(트리 clean — P0 는 `6c703d2` 로 커밋, 미push). plan 이 main `<main>/plans/` 에 존재하고 worktree-local `plans/` 부재 확인(이번 fix dogfooding 성립). status=in_progress 유지(P0 미머지 + P2 acceptance 루프 남음) → worktree 유지·main 복귀.

# Next
- **P1 follow-up**: CLAUDE.md §10 문구 `.claude/plans/<YYYY-MM-DD>-<slug>/...` 가 이 repo(ROOT=`~/.claude`)에서 double-nest 된다. 스킬 3종(dlc/c/e)과 README 는 정합됐고 master 문서 §10 만 남음. CLAUDE.md 는 운영 자산이라 사용자 승인 후 별도 작업(§1).
- **다음 페이즈(P2, acceptance 루프)**: acceptance 확정 게이트 + 3계층 검증 + DONE/BLOCKED/NEEDS-HUMAN 판정 + 알림. dlc 의 worktree 생성 흡수(D2). plan 완료-삭제 동작(D1). → structural 규모, 별도 plan-review 필수.

# Decisions
- **D1 전제 무효 → "main worktree 고정" 폐기로 변경 (2026-09-08)** (이유: D1 은 "plan 이 gitignored 라 worktree 삭제 시 소실된다" 를 근거로 삼았는데, 그 뒤 `plans/` 가 tracked 로 전환됐다. 이제 worktree 에서 만든 plan 은 브랜치와 함께 커밋·머지되고, 미커밋이면 `git worktree remove` 가 거부한다 — 소실 경로 자체가 없다. `skills/c/SKILL.md` 도 "양쪽을 본다·브랜치별 독립" 으로 이미 정착. 아래 D1 원문은 이력으로 남긴다.)
- **D1 (plan 저장)**: 작업 중 `<main>/plans/`에 영속(worktree 삭제와 무관) → **확정 DONE(머지/승인) 시 명시적 삭제**. 안전조건: (1) 삭제는 worktree 정리와 **분리된 별도 동작**(현 소실버그의 근원이 이 결합), (2) 삭제 전 acceptance 증거·핵심 Decisions를 commit/PR에 남겨 'why' 보존. 사용자 선택='완료 후 자동 삭제'(아카이브 대신 삭제, 잡음 0 우선). codex "삭제=유지보수의 몫, 실행 루프와 분리"와 일치.
- **D2 (worktree 소유권)**: dlc가 worktree 생성을 흡수, wt는 얇은 네비/재개 도구로. 채택 근거(codex): 가장 중요한 불변식(worktree)을 정작 일하는 주체가 소유해야 함(현 split은 leaky).
- **D3 (진행 범위)**: P0(경로버그 + /wt rm 가드) 먼저 최소 수정. acceptance 루프 개편은 다음 페이즈.
- **설계 골격(5-step loop)**: [0]진입가드(비-trivial+cwd==main→/wt 유도) [1]acceptance 확정게이트(목표를 pass/fail로 환원, 모호하면 AskUserQuestion 끝까지, #Goal에 freeze) [2]규모별 본체(현행 explore→plan→리뷰→TDD→구현→리뷰→simplify 유지) [3]3계층 검증(①rules=lint/test/build ②acceptance 항목별 대조, 테스트 못잡는 동작은 verify 스킬 연결 ③LLM-judge 보조; '주장 말고 증거') [4]판정(전항목 satisfied→DONE / 미충족→[2] 재진입, 재시도≤3+no-progress 감지, 테스트약화·기준무단수정 금지=reward-hack 차단) [5]알림(DONE 또는 BLOCKED/NEEDS-HUMAN 전이만 PushNotification).
- **정합 경로 기준**: c/e의 `<main>/plans/`가 정답. dlc:8·CLAUDE.md §10 문구(`.claude/plans/`)는 이 repo가 ROOT=.claude라 double-nest되어 빈 경로를 가리킴 → main-worktree 기준으로 통일. (직접 확인: `<ROOT>/plans/`에 plan 2개 존재, `.claude/plans/`는 비어있음.)

# Key Files
- skills/dlc/SKILL.md:8 — plan 경로 표기 (✅P0 적용: `<main>/plans/` 고정)
- skills/wt/SKILL.md (rm 섹션 ~107-115) — /wt rm gitignored-plan 가드 (✅P0 적용)
- skills/e/SKILL.md:51-53 — ignored-plan 가드 원본 (이식 소스)
- skills/c/SKILL.md:19-21 — 정합 경로 기준 `<main>/plans/`
- CLAUDE.md §8(worktree 삭제 위험)·§10(plan 핸드오프 규약)

# Blockers
- (없음)
