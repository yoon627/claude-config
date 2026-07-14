# Wiki Log

연산 기록(append-only). 형식: `## [YYYY-MM-DD] operation | title`.

## [2026-06-16] ingest | llm-wiki-pattern (seed)
- `docs/llm-wiki.md` 개념 정리를 `concept/llm-wiki-pattern.md` 로 이식 — 이 wiki 의 self-reference 패턴 문서.
- 동반 concept stub: [[project-memory]](plans↔wiki 경계), [[ingest-operation]](연산 절차).
- wiki 인스턴스 초기 골격 구축(WIKI.md·index.md·log.md·pages/).

## [2026-06-19] ingest | wiki-bootstrap (decision/entity/concept 보강)
- 보존된 plan 9개·repo 워크플로우 구조·미머지 self-improvement 2건을 구조화. decision/entity 카테고리가 비어있던 것을 채움.
- concept 6 신규: [[dlc-development-cycle]] [[plan-handoff]] [[hub-and-spoke-isolation]] [[worktree-per-task]] [[claude-codex-collaboration]] [[feedback-memory]].
- decision 7 신규: [[subagent-model-effort-tiering]] [[effort-os-env-single-source]] [[dual-review-plan-and-code]] [[deferred-and-scope-boundary]] [[self-diagnosis-and-improvement-status]] [[comment-and-commit-policy]] [[codex-bash-invocation]].
- entity 2 신규: [[anthropic-claude-models]] [[claude-code-subagent-config]].
- 미머지 self-improvement 현황은 [[self-diagnosis-and-improvement-status]] 에 `[!open]` 로 보존 + plans/2026-06-14-* 복원(충돌 판단용).
- 범위 밖 제외: plans/ 루트 랜덤이름 3개(다른 프로젝트 plan).

## [2026-06-19] ingest | self-improvement 심의 종결 반영
- remote 재확인: self-improve-trigger 폐기(원격 삭제, 머지 아님), dlc-improvements f698001 `done`(invariant-check 미채택 결론).
- [[self-diagnosis-and-improvement-status]] 갱신: "미구현·재개 필요"(stale) → "심의 종결, 신규 일반 단계 미채택". [[feedback-memory]] self-improvement 관계 문단 동기화.
- 로컬 plans 정합: dlc-improvements 최신화(f698001), self-improve-trigger 삭제(폐기).

## [2026-06-19] ingest | dlc-fablize-evidence (evidence gate·fablize 규율·wt 자동화)
- dlc 강화 구현: 진입 매트릭스·dlc→wt 자동·# Acceptance evidence gate·verification grounding·investigation 프로토콜·# Workflow Findings 최소형.
- hook 3종: dlc-task-router(UserPromptSubmit 라우터)·dlc-evidence-ledger(PostToolUse 증거 기록)·dlc-early-stop(Stop, capped·fail-open).
- decision 3 신규: [[evidence-gate]] [[dlc-wt-autoflow]] [[fablize-adopted-disciplines]]. [[self-diagnosis-and-improvement-status]] 에 finding 최소형 채택 반영.

## [2026-06-19] ingest | dlc-failure-loop (wt 강제 + 실패 wiki 추적)
- dlc→wt 를 "예외 없는 필수 게이트"로 강화(비trivial 은 항상 wt, main 직접 금지). trivial 즉시통과 유지.
- Workflow Findings 를 wiki [[workflow-failures]] 에 영속 누적 + 같은 실패 2회+ 반복 시 wt 해결 제안(승인 시 wt→dlc).
- decision 신규: [[workflow-failures]]. CLAUDE.md §3-1 wt 문구 강화.

## [2026-06-19] ingest | dlc-evidence-falsepos (early-stop 오탐 수정 + 사용자 지적 트리거)
- early-stop false positive 수정: `dlc-evidence-ledger` 가 gitignored/임시 파일(`git check-ignore`)은 changed 로 안 침 — 마무리 단계(커밋 메시지 임시파일 Write) 오탐 해결. [[workflow-failures]] 에 fixed 기록(첫 실제 항목).
- dlc Workflow Findings 트리거에 ③ "사용자가 명시 지적한 마찰·오탐" 추가 — 사용자 피드백 누적, 반복 시 wt 개선([[self-diagnosis-and-improvement-status]]·§12 feedback 과 역할 구분).

## [2026-06-26] ingest | effort-global-xhigh (effort 정책 전환)
- effort 전역 정책 전환: model/effort 차등 폐기 → 메인·subagent 전부 opus + xhigh 단일(PR #66 model 통일·#67 settings effort xhigh·#68 agents frontmatter effort 제거).
- decision 신규: [[effort-global-xhigh]]. 근거: 공식 docs Opus 4.8 코딩 권장=xhigh / effort=adaptive signal / max=frontier 전용.
- [[subagent-model-effort-tiering]] 에 `[!conflict]` superseded 표시(역사 보존). [[effort-os-env-single-source]] 에 현재 상태 note(env=xhigh 단일소스·env 가 frontmatter override) 추가.

## [2026-07-14] ingest | ops-doc-slimming (항상주입 문서 압축 상한 교훈)
- doc-slim(PR #73) 교훈 적립: 규칙손실0 유지 시 규칙밀도 높은 항상주입 문서의 압축 상한 실측 ~11%(70,596→62,706B). 30%+ 는 규칙 통합/이관=범위확대 없이는 불가, 이관은 로드등급 하락이라 안전/실행/트리거 규칙엔 그 자체가 손실.
- decision 신규: [[ops-doc-slimming]] — bytes 감소는 보조목표, 규칙손실0 이 hard gate([[evidence-gate]] 정합). 손실방어 3겹 + [[claude-codex-collaboration]] 병행이 규칙손실 3건 포착.
- 상위 plans/2026-07-02-workflow-loopify Workstream C 완료 마커 정정 동반.
