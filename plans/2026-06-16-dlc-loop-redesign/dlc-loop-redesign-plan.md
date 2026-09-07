---
title: dlc-loop-redesign — dlc를 자가검증 acceptance 루프로 진화
status: done
started: 2026-06-16
updated: 2026-09-08
---

# Goal
dlc를 "구체적 목표 → 단일 루프(act→verify→self-correct)로 요구사항 충족까지 반복 → 완료/문제 시 알림" 형태의 자가검증 루프로 진화. 검증을 '테스트 통과'가 아닌 'acceptance(요구사항 충족)'에 결속. (사용자 8개 요구 + 궁극목표.)

# Progress
- 2026-06-16: ultracode 워크플로(현행분석 + loop engineering 리서치 + llm-wiki/okf 정체) + codex 인라인 리뷰로 진단·설계 종합. 핵심 plan-경로 결함 직접 재확인(Grep/Glob). 사용자 3대 결정 확정(Decisions). P0 착수.
- 2026-06-16: **P0 완료**. dlc:8 → `<main>/plans/<YYYY-MM-DD>-<slug>/<slug>-plan.md` 고정, `/wt rm` 안전검사에 gitignored-plan 가드(`git -C <대상> status --porcelain --ignored`) 이식. worktree `dlc-loop-redesign` 커밋 `6c703d2` (2 files, 미push). 자기리뷰서 `-C <대상>` 누락 버그 발견·수정(/wt rm 대상≠cwd), codex 병행 리뷰 통과(제기 2건=`*-plan.md` 외 커버·c/e dated-dir 매칭 모두 기존 처리 확인). 검증: 잔존 `.claude/plans` 0건 + dlc/c/e 경로 정합 grep 확인(테스트 surface 없는 md 변경).
- 2026-06-17: `/e` 체크포인트. 신규 변경 없음(트리 clean — P0 는 `6c703d2` 로 커밋, 미push). plan 이 main `<main>/plans/` 에 존재하고 worktree-local `plans/` 부재 확인(이번 fix dogfooding 성립). status=in_progress 유지(P0 미머지 + P2 acceptance 루프 남음) → worktree 유지·main 복귀.
- 2026-09-08: **P0 종결 — 브랜치 `6c703d2` 는 머지하지 않고 현재 main 기준으로 재적용**(브랜치 `dlc-p0-merge`). 3개월간 main 이 371커밋 나가며 P0 의 전제가 무효가 됐다: `plans/` 가 tracked 로 전환돼(`.gitignore` `!/plans/`) worktree-local plan 은 더 이상 gitignored 소실 대상이 아니고, `skills/c/SKILL.md:19-21` 이 이미 "양쪽(`<ROOT>`·main worktree) 을 본다 — plans/ 는 브랜치별 독립" 으로 진화했다. 따라서 "항상 main worktree 에 둔다" 강제는 폐기하고, **실제로 남아 있던 결함 2건만** 반영: (1) `skills/dlc/SKILL.md:8` 의 `.claude/plans/<slug>-plan.md` → §10 dated-dir 형식 + ROOT double-nest 주의, (2) `skills/wt/SKILL.md` rm 안전검사에 `--ignored` 점검 누락(브랜치 원문의 "plans/ 가 ignored" 서술은 현재 사실과 달라 `.env`·settings.local 기준으로 고쳐 적용). README:298 도 같은 브랜치에서 동기화.
- 2026-09-08: **P2 종결(범위 축소)**. 실사 결과 [1]acceptance 확정게이트·[2]규모별 본체·[3]①rules②acceptance 대조는 이미 구현돼 있었다(`# Intent`·`# Acceptance`·evidence gate·15단계 격리 runner 의 항목별 매핑). 남은 공백 [4]판정·[5]알림만 `skills/dlc/SKILL.md` 규약으로 구현. [3]③LLM-judge 는 사용자가 범위에서 제외. codex 리뷰가 1차안을 **병합 불가**로 반려(아래 Review Disposition) — DONE 을 `status: done` 에 묶어 `/c` 가 통합 대기 작업을 건너뛰게 만든 것, 모든 판정 뒤 커밋해 검증 실패 상태를 정식 커밋하게 만든 것이 Critical. 재설계해 반영하고 README·wiki 2쪽·index 동기화.
- 2026-09-08: **P1 완료** — CLAUDE.md §10 을 `<ROOT>/plans/<YYYY-MM-DD>-<slug>/` 로 정정(`<ROOT>` = `git rev-parse --show-toplevel`, 스킬 c·e·dlc 기준과 통일). §9·§10 제목의 `.claude/plans/` 표기와 README 목차도 동기화. §10 이 경로의 단일 소스가 됐으므로 dlc SKILL·README 에 중복 서술하던 double-nest 경고는 §10 참조로 축약(simplify).

# Next
- 없음(완료). 범위에서 뺀 것은 `# Deferred`.

# Decisions
- **D1 전제 무효 → "main worktree 고정" 폐기로 변경 (2026-09-08)** (이유: D1 은 "plan 이 gitignored 라 worktree 삭제 시 소실된다" 를 근거로 삼았는데, 그 뒤 `plans/` 가 tracked 로 전환됐다. 이제 worktree 에서 만든 plan 은 브랜치와 함께 커밋·머지되고, 미커밋이면 `git worktree remove` 가 거부한다 — 소실 경로 자체가 없다. `skills/c/SKILL.md` 도 "양쪽을 본다·브랜치별 독립" 으로 이미 정착. 아래 D1 원문은 이력으로 남긴다.)
- **D1 (plan 저장)**: 작업 중 `<main>/plans/`에 영속(worktree 삭제와 무관) → **확정 DONE(머지/승인) 시 명시적 삭제**. 안전조건: (1) 삭제는 worktree 정리와 **분리된 별도 동작**(현 소실버그의 근원이 이 결합), (2) 삭제 전 acceptance 증거·핵심 Decisions를 commit/PR에 남겨 'why' 보존. 사용자 선택='완료 후 자동 삭제'(아카이브 대신 삭제, 잡음 0 우선). codex "삭제=유지보수의 몫, 실행 루프와 분리"와 일치.
- **D2 (worktree 소유권)**: dlc가 worktree 생성을 흡수, wt는 얇은 네비/재개 도구로. 채택 근거(codex): 가장 중요한 불변식(worktree)을 정작 일하는 주체가 소유해야 함(현 split은 leaky).
- **D3 (진행 범위)**: P0(경로버그 + /wt rm 가드) 먼저 최소 수정. acceptance 루프 개편은 다음 페이즈.
- **설계 골격(5-step loop)**: [0]진입가드(비-trivial+cwd==main→/wt 유도) [1]acceptance 확정게이트(목표를 pass/fail로 환원, 모호하면 AskUserQuestion 끝까지, #Goal에 freeze) [2]규모별 본체(현행 explore→plan→리뷰→TDD→구현→리뷰→simplify 유지) [3]3계층 검증(①rules=lint/test/build ②acceptance 항목별 대조, 테스트 못잡는 동작은 verify 스킬 연결 ③LLM-judge 보조; '주장 말고 증거') [4]판정(전항목 satisfied→DONE / 미충족→[2] 재진입, 재시도≤3+no-progress 감지, 테스트약화·기준무단수정 금지=reward-hack 차단) [5]알림(DONE 또는 BLOCKED/NEEDS-HUMAN 전이만 PushNotification).
- **정합 경로 기준** (2026-09-08 `<ROOT>/plans/` 로 정정 — CLAUDE.md §10 이 단일 소스. 당시 서술은 이력): c/e의 `<main>/plans/`가 정답. dlc:8·CLAUDE.md §10 문구(`.claude/plans/`)는 이 repo가 ROOT=.claude라 double-nest되어 빈 경로를 가리킴 → main-worktree 기준으로 통일. (직접 확인: `<ROOT>/plans/`에 plan 2개 존재, `.claude/plans/`는 비어있음.)

# Key Files
- skills/dlc/SKILL.md:8 — plan 경로 표기 (✅ `<ROOT>/plans/`, CLAUDE.md §10 참조로 축약 — 2026-09-08 재적용)
- skills/wt/SKILL.md (rm 안전검사) — `--ignored` 산출물 점검 (✅ 2026-09-08 재적용, `.env`·settings.local 기준)
- skills/e/SKILL.md:51-53 — ignored-plan 가드 원본 (이식 소스)
- skills/c/SKILL.md:19-21 — `<ROOT>/plans/` + worktree 양쪽 탐색(plans/ 는 브랜치별 독립)
- CLAUDE.md §8(worktree 삭제 위험)·§10(plan 핸드오프 규약 — ✅ 2026-09-08 경로 정정)

# Blockers
- (없음)

# Review Disposition

codex 1차 리뷰(P2 규약안) — 병합 불가 판정, 전부 반영:
- Critical 1 (DONE 을 `status: done` 에 결합 → `/c` 가 통합 대기 plan 을 건너뜀) — `fix`. DONE 은 acceptance 판정일 뿐 plan 생명주기와 분리, status 는 §10 대로 머지·승인 시점.
- Critical 2 (모든 판정 뒤 커밋 → 검증 실패 상태를 정식 커밋) — `fix`. DONE 만 커밋, BLOCKED/NEEDS-HUMAN 은 금지 + `/e` WIP 안내.
- Major 1 (세 값이 배타적·망라적이지 않음) — `fix`. 판정은 **끝낼 때만**(고치는 중이면 대상 아님), 겹치면 *다음 한 걸음*(받아야 함/골라야 함)으로 가름.
- Major 2 (NEEDS-HUMAN 을 blocked 에 접으면 `plan-blocked` failure telemetry 오염 + 전이 키 부재) — `fix`. NEEDS-HUMAN 은 `status: in_progress` + `# Next` 로 두어 status 자체가 구분 키가 되게. frontmatter 필드 추가는 불채택(§10·plan-lint·소비자 동시 변경 비용 대비 status 분리로 충분).
- Major 3 (no-progress 가 reward hacking 을 못 막고 원 설계의 방지책 누락) — `fix`. 테스트 약화·acceptance/통과기준/검증명령 변경으로 카운터 리셋 금지 + 변경엔 사용자 승인·`# Decisions` 선행, acceptance 항목 번호를 안정 ID 로.
- Major 4 (`2회` 근거를 fix loop 에서 빌린 것은 다른 축) — `fix`. fix loop 문구를 원복하고 두 축이 별개임을 명시, 상한은 "1회차 뒤 전략 변경 → 그러고도 개선 없으면 2회차 정지" 로 재정의. transient 실패는 카운트 제외.
- Major 5 (`tool_response` 를 훅이 못 읽는다는 단정이 사실과 다름) — `fix`. 확인한 것은 "현재 ledger 가 소비하지 않는다" 뿐이므로 그대로만 기술하고 불가능 단정 철회.
- Major 6 (알림 "전이 시 항상 1회" 가 도구 계약과 충돌) — `fix`. 전이는 필요조건이지 충분조건 아님, 전이당 **최대** 1회, DONE 은 장시간 작업일 때만.
- Minor 1 (wiki·plan 미동기화) — `fix`. `dlc-development-cycle`·`evidence-gate`·`index.md` 와 이 plan 을 같은 브랜치에서 갱신.

# Deferred

- **[3]③ LLM-judge 보조 검증** — 사용자가 P2 범위에서 제외(2026-09-08). judge 오판이 게이트를 헐겁게 만들 위험이 있어 도입 시 보조 역할로 종속시켜야 한다.
- **D2 (worktree 생성을 dlc 가 흡수)** — 보류. 근거("불변식은 일하는 주체가 소유")는 유효하나, 그 사이 `guard-worktree-edit` 훅·CLAUDE.md §3-1/§8 worktree 강제·`/wt` 의 ignored 파일 자동 복사가 자리잡아 현재 분업이 실동작한다. 두 스킬 + CLAUDE.md 동시 개편 비용 대비 이득이 2026-06 대비 작아졌다.
- **no-progress 의 기계화** — ledger 가 tool response 를 소비하고 안정적인 실패 signature·acceptance 매핑을 갖추면 가능. 지금은 모델 책임.
