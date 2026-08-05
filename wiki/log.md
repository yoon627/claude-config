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

## [2026-06-24] ingest | lesson-grep-absence-not-proof (§13 첫 lesson)
- CLAUDE.md §13 실수·교훈 로그 규약 신설(PR #65) 후 첫 dogfooding. README 동기화 오판(grep 무매칭→부재 단정, doc-drift hook 이 포착)을 decision 으로 적립.
- decision 신규: [[lesson-grep-absence-not-proof]]. 교훈: 부재 주장은 grep 무매칭이 아니라 직접 증거(Read·`git check-ignore`)로.

## [2026-06-26] ingest | effort-global-xhigh (effort 정책 전환)
- effort 전역 정책 전환: model/effort 차등 폐기 → 메인·subagent 전부 opus + xhigh 단일(PR #66 model 통일·#67 settings effort xhigh·#68 agents frontmatter effort 제거).
- decision 신규: [[effort-global-xhigh]]. 근거: 공식 docs Opus 4.8 코딩 권장=xhigh / effort=adaptive signal / max=frontier 전용.
- [[subagent-model-effort-tiering]] 에 `[!conflict]` superseded 표시(역사 보존). [[effort-os-env-single-source]] 에 현재 상태 note(env=xhigh 단일소스·env 가 frontmatter override) 추가.

## [2026-07-14] ingest | ops-doc-slimming (항상주입 문서 압축 상한 교훈)
- doc-slim(PR #73) 교훈 적립: 규칙손실0 유지 시 규칙밀도 높은 항상주입 문서의 압축 상한 실측 ~11%(70,596→62,706B). 30%+ 는 규칙 통합/이관=범위확대 없이는 불가, 이관은 로드등급 하락이라 안전/실행/트리거 규칙엔 그 자체가 손실.
- decision 신규: [[ops-doc-slimming]] — bytes 감소는 보조목표, 규칙손실0 이 hard gate([[evidence-gate]] 정합). 손실방어 3겹 + [[claude-codex-collaboration]] 병행이 규칙손실 3건 포착.
- 상위 plans/2026-07-02-workflow-loopify Workstream C 완료 마커 정정 동반.

## [2026-07-16] ingest | unknowns-pass (Fable unknowns 발굴 기법 → dlc)
- Thariq "A Field Guide to Fable: Finding Your Unknowns"(2026-07-04, x.com) 의 unknowns 발굴 기법 3종을 dlc 에 반영: blind-spot pass·질문 우선순위(명확화 절), 프로토타입-우선(router `[dlc:grounding]` 주입 + verification grounding). 부재 memory 참조(명확화 절 괄호) 정리.
- source 신규: [[fable-field-guide-unknowns]](원문 auth-gated 402 → Fable 세션 분석 2차출처·`[!open]` flag). concept 신규: [[unknowns-discovery]](기법→dlc 매핑 표).
- 상위 plans/2026-07-02-workflow-loopify Workstream J.

## [2026-07-16] ingest | git-hook-network-safety (main-autopull 훅 교훈)
- main-autopull(PR #82) 교훈 2건 적립. ① git 클라이언트 훅은 동기·무timeout → 훅 안 `git pull` 이 죽은 네트워크/프롬프트에 걸리면 checkout hang(SessionStart 훅과 달리 하니스 안전망 없음). macOS 는 `timeout(1)` 부재라 poll 워치독(`kill -0` 폴링·orphan 0)+`GIT_TERMINAL_PROMPT=0`+SSH `ConnectTimeout` 로 자체 상한. ② ff-merge 는 post-checkout 재발동 안 함(재귀 없음, 격리 fixture 실측).
- decision 신규: [[git-hook-network-safety]] — hang 함정은 [[claude-codex-collaboration]] 병행 리뷰가 사각지대로 포착, 재귀 안전은 [[evidence-gate]] 실측으로 확정.
- 상위 plans/2026-07-02-workflow-loopify Workstream G(main-autopull).

## [2026-07-17] ingest | ops-doc-slimming 정련 — thin skills slim 후속 이관(#89-92): 압축률∝1/규칙밀도·방향역전 금지·manifest 방법론

## [2026-07-19] update | codegraph (worktree 인덱스 watcher-부재/staleness)
- [[codegraph]] "worktree-local 인덱스" 절에 init 스냅샷·live watcher 부재·조회 전 `codegraph sync <worktree>` 재-sync 필요를 반영(2026-07-19 실측: worktree init 후 새 심볼이 수동 sync 전 검색 불가, MCP projectPath 조회도 일회성, worktree 에 daemon.log 미생성).
- 동반: skills/wt/references/codegraph-worktree.md("곧 sync"→최초 init 1회 한정 명확화 + staleness 절 watcher-부재 메커니즘), wiki/index.md 요약 동기화.

## [2026-07-26] ingest | lesson-parser-precedent-partial-mirror (신규)
- PR #105(session-brief M 신호) code-review 에서 CONFIRMED Major 2건이 같은 원인으로 확인됨 — 새 frontmatter 파서가 선례(`plan-lint.js`)의 정규식 모양만 가져오고 ① CRLF 정규화 전처리 ② `(\S+)` 첫-토큰 관용을 빠뜨려, `.gitattributes: * text=auto` 하의 Windows 체크아웃과 CLAUDE.md §10 정본 템플릿(`status: in_progress  # ...`)에서 각각 **무음 exit 0** 이 되던 문제.
- 교훈 페이지 신설 + `wiki/index.md` 등재. 인접 lesson([[lesson-grep-absence-not-proof]])과 연계.

## [2026-08-03] ingest | risk-based-approval (신규)
- 사용자가 `/wt` 의 slug 승인을 마찰로 지목 → graph engineering(2026)의 risk-based human-in-the-loop 원칙을 대조해 승인 기준을 가역성으로 일원화하는 결정을 적립.
- 신규 [[risk-based-approval]] + [[dlc-wt-autoflow]] "생성은 확인" 결정 뒤집기(이유 병기) + [[worktree-per-task]] 흐름 문구 동기화, `wiki/index.md` 등재.
- 근거: analyticsvidhya "Graph Engineering for AI Agents"(2026-07-29) — 노드/엣지·guard·checkpoint·interrupt 중 이 repo 에 없던 축이 interrupt 정책이었음.

## [2026-08-03] ingest | lesson-stale-tool-version (신규)
- [[workflow-failures]] 의 rtk 오재작성 항목(6회 tracking)을 재현·근본원인 확정: 설치 rtk 0.28.2 의 `rtk read` 폴백 버그이며 상류가 0.35.0·0.39.0 에서 이미 수정(상류 최신 0.44.2). 표에 적혀 있던 수정 위치(`hooks/rtk-rewrite.sh`)는 규칙 없는 얇은 위임자 + untracked 라 **틀린 위치**였고, 이 오기록이 6회 방치의 직접 원인.
- 교훈 페이지 신설 + 표 항목 정정(근본원인·수정위치·횟수 6·상태 proposed) + `wiki/index.md` 등재.

## [2026-08-03] ingest | 도구 사용량 감사 (codegraph · headroom 갱신)
- transcript 298개 전수 스캔으로 MCP 실사용을 측정해 [[codegraph]]·[[headroom]] 에 반영. codegraph 30회(70%가 coin-trading-bot), headroom MCP 41회(`compress` 0회) — headroom 의 가치는 프록시($103.87·13.7% 절감)와 번들 rtk(2.1M 토큰·64.7%)에 있고 MCP 표면엔 없음.
- 조치: 이 repo `.codegraph/` 만 삭제(전역 MCP 는 유지 — 실사용처 보호), headroom `debug_400` 1.0GB→1.0MB 회수, rtk 심링크 0.44.2 재지정.
- 처음엔 "codegraph 전역 제거"로 갈 뻔했으나 프로젝트별로 갈라 보니 실사용이 다른 repo 에 몰려 있어 판단을 뒤집었다 — 집계 단위를 섞으면 결론이 뒤집힌다는 사례.

## [2026-08-05] ingest | workflow-failures (gh merge 실패 신규 적립 + doc-drift 오탐 가산)
- CLAUDE.md §8 이 권장하던 `gh pr merge --delete-branch` 가 worktree 워크플로우에서 **결정적으로** 실패하는 건을 표에 신규 적립(횟수 1·`fixed`). gh 가 로컬 브랜치를 지우려 base 로 checkout 하는데 main worktree 가 그 base 를 점유해 거부되고, **머지는 성공하므로 정리 누락이 조용히 지나간다** — 규약을 성실히 따를수록 브랜치가 남는 구조였다. 근거는 커밋 `31be25b`(PR #123) 의 실측(#121 실패·#122 `--merge` 정상).
- `doc-drift-readme` 오탐 행 5→6 (CLAUDE.md §8 절 단위 수정에서 재현, signal detail=`CLAUDE.md`).
- 대조 중 확인한 함정을 표에 명시: **표 횟수·신호 발동 수·unique session 수가 서로 다른 척도**다(실측 6/16/7). hook 이 세션당 capped 라 한 세션의 여러 어긋남이 신호 1건으로 접힌다 — 세 수치를 같게 맞추려 하면 이중계상된다.
- 미적립으로 남긴 것: 2026-08-04 `detail=scripts/session-brief.test.js` 신호(테스트 파일이 README 트리거로 잡히는 별개 FP class — 다른 세션 `/improve` 의 1순위 후보라 소유권 분리).
