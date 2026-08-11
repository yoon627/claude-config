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

## [2026-08-05] ingest | workflow-failures 갱신 (.test.js doc-drift 오탐 fixed)
- `doc-drift-readme` 를 두 sub-class 로 분리: 내부 dedup(판정 불가 — escape 유지, tracking) / `.test.js` 기존 편집(정규식 과매치 — fixed 2026-08-05). telemetry unique-session 총계 5→7 로 갱신(7월 5 + 8월 2).
- `early-stop-verify` 계열 fix 효과를 실측으로 확정: 2026-07 16 → 2026-08 0(마지막 2026-07-30). 더 직접적인 근거는 detail 축 — `.md` 제외 fix(2026-07-17) 이후 신호 20건 중 `.md` detail 0건.
- 8월 0 은 표본 5일이라 단독으로는 근거가 약하다 — 빈도 대신 detail 축으로 class 소멸을 입증하는 편이 강하다는 사례.

## [2026-08-05] ingest | workflow-failures (gh merge 실패 신규 적립 + doc-drift 오탐 가산)
- CLAUDE.md §8 이 권장하던 `gh pr merge --delete-branch` 가 worktree 워크플로우에서 **결정적으로** 실패하는 건을 표에 신규 적립(횟수 1·`fixed`). gh 가 로컬 브랜치를 지우려 base 로 checkout 하는데 main worktree 가 그 base 를 점유해 거부되고, **머지는 성공하므로 정리 누락이 조용히 지나간다** — 규약을 성실히 따를수록 브랜치가 남는 구조였다. 근거는 커밋 `31be25b`(PR #123) 의 실측(#121 실패·#122 `--merge` 정상).
- `doc-drift-readme` 오탐 행 5→6 (CLAUDE.md §8 절 단위 수정에서 재현, signal detail=`CLAUDE.md`).
- 대조 중 확인한 함정을 표에 명시: **표 횟수·신호 발동 수·unique session 수가 서로 다른 척도**다(실측 6/16/7). hook 이 세션당 capped 라 한 세션의 여러 어긋남이 신호 1건으로 접힌다 — 세 수치를 같게 맞추려 하면 이중계상된다.
- 미적립으로 남긴 것: 2026-08-04 `detail=scripts/session-brief.test.js` 신호(테스트 파일이 README 트리거로 잡히는 별개 FP class — 다른 세션 `/improve` 의 1순위 후보라 소유권 분리).

## [2026-08-05] ingest | lesson-parallel-duplicate-implementation (신규)
- PR #118 과 #120 이 **같은 기능**(worktree 별 작업시간 귀속)을 각자 구현해 #120 의 553줄이 통째로 폐기된 건을 §13 lesson 으로 신설. #120 의 분기점이 `d38c70b`(#116)라 트리를 취하면 이후 머지분까지 `−2009` 줄 삭제되는 상태였다.
- 근본 원인은 도구의 실수가 아니라 **채널 설계의 공백**: `plans/` 매칭(§10)은 *자기 branch → plan dir* 방향이라 남이 다른 브랜치에서 연 plan 은 안 보이고, 새 브랜치로 시작한 도구는 기존 plan 을 못 찾아 새로 만든다. 채널의 목표가 "이어받기"였지 "동시 착수 감지"가 아니었다.
- 행동 규칙(memory 인덱스로 승격): 비trivial 착수 전 `gh pr list --state open`·원격 브랜치·`status: in_progress` plan 확인. **plan 매칭 실패를 "없다"의 근거로 쓰지 않는다.**
- "#120 을 Codex 가 만들었다"는 ⚠️추정으로만 표기(커밋에 Claude 트레일러 부재라는 정황뿐) — 단정하지 않았다.

## [2026-08-05] ingest | 모델 단계별 배치 + OSS 하네스 판단
- 신규: entity/claude-code-model-selection, entity/claude-code-oss-frameworks, decision/model-stage-tiering, decision/harness-keep-and-borrow. 갱신: entity/anthropic-claude-models (Claude 5 세대·Fable 50% 캡·벤치 구도). 출처: 본 세션 researcher 조사 2건.

## [2026-08-06] ingest | git-hook-network-safety (보류된 결정 1건 미해결 표시)
- SessionStart pull 의 `--autostash` 도입 여부를 `[!open]` 콜아웃으로 올렸다. 근거 plan(`settings-local-keys`)이 PR #129 로 머지되며 `status: done` 이 됐는데, 그 plan 의 범위는 *조사까지*였고 **결정만 미결로 남았다** — done 인 plan 안에 있으면 `in_progress` 스캔에도 세션 시작 신호에도 안 잡혀 조용히 묻힌다. wiki 는 작업을 가로질러 누적되는 층이라 보류된 결정의 제자리다.
- 결정 구조를 그대로 보존: (a) 도입 여부와 (b) stash 재적용 **충돌 알림** 방식은 별개 — 지금 훅은 출력을 죽이므로 (a) 만 도입하면 "변경이 사라진 것처럼 보이는" 새 실패 모드가 생긴다. 같은 페이지 §1 의 async↔동기 분리와 같은 축이라 그 페이지에 붙였다.

## [2026-08-06] ingest | subagent model 단계별 고정 (구현 반영)
- [[model-stage-tiering]] 의 `[!open] 구현 대기` 해소 — `agents/*.md` 를 reviewer 3종 `model: opus`·researcher `model: sonnet` 으로 고정(worktree subagent-model-pinning). 갱신: decision/effort-global-xhigh(2026-07-04 inherit 결정의 재개정 기록), decision/model-stage-tiering([!open]→[!done]), decision/subagent-model-effort-tiering([!conflict] 배너에 "model 차등만 부분 복원" — effort 차등은 여전히 폐기), entity/claude-code-model-selection(pin 시 확정사실 절 신설), index 4줄.
- 조사로 확정한 외부 사실(researcher, 공식 docs + GH issue): subagent frontmatter 의 `[1m]` 접미사는 **미문서화 + stripping 버그 미수정**(#45169) → 쓰지 않는다. 필요도 없음 — Opus 4.7+ 는 API 에서 항상 1M, Max/Team/Enterprise 는 자동 승격. subagent context 는 **자기 모델 기준**(부모 상속 아님). 명시 pin 은 **자동 폴백 없음**(한도 소진 시 `Agent terminated early due to an API error`; `fallbackModel` 은 rate-limit 에 미발동) → 비상 레버 `CLAUDE_CODE_SUBAGENT_MODEL`.
- **부수 발견(문서 drift 교정)**: [[effort-global-xhigh]] 가 주장하던 `CLAUDE_CODE_EFFORT_LEVEL=xhigh` 는 사실이 아니었다 — `78a6715 fix(settings): effort xhigh→high (웹툴 400 해소)` 에서 의도적으로 하향됐는데 wiki 만 stale 이었다. 페이지 안에 `[!warning]` 로 교정. **페이지명 rename 은 링크 전수 수정 동반이라 미뤘다**(plan `# Deferred`).

## [2026-08-06] ingest | native-overlap-ledger (신규)
- `/improve` 에 네이티브 중복 점검 축(§6)을 추가하면서, 판정을 누적할 대장을 신설. 자작 부품 8종 × Claude Code 네이티브 대응 × keep/watch/retire.
- 조회 창은 공식 changelog v2.1.186(2026-06-22)~v2.1.222(2026-08-04), 로컬 설치 2.1.222. 결과: watch 5 / keep 3 / **retire 0** — 이번 창에서 완전히 대체된 자작 부품은 없다.
- 가장 근접한 후보는 `guard-worktree-edit.js` 의 **worktree 밖 편집 deny** — v2.1.222 가 worktree isolation 을 모든 세션 타입의 edit+Bash 로 확대해 방향이 같다(다음 점검 1순위). 같은 파일의 *main 편집 ask* 는 방향이 반대(네이티브=밖으로 새는 것 차단 / 자작=main 에서 편집 시작 차단)라 유지.
- 주기 45일의 근거는 취향이 아니라 실측: 6주에 36릴리스라 90일 창이면 delta 가 70~80 릴리스로 커져 "delta 만 읽어 싸게"라는 설계 전제가 깨진다.
- **갱신 권한 분리**: `/improve` 는 판정 초안까지만, 대장 write 는 승인 후 `/wiki ingest`. read-only 경계(SKILL.md)·§11 ingest 제안 원칙·§13 무승인 적립 금지가 모두 자동 write 를 금한다 — plan-reviewer 가 이 충돌을 blocker 로 잡아 설계를 정정했다.

## [2026-08-11] lint | code-review 지적 반영 — effort drift 재조사·정정
- **08-06 의 교정 자체가 부분적으로 틀렸다**(code-reviewer 반례): "런타임 모두 `high`" 는 tool 셸의 `printenv` 만 본 판단이었고, **실행 중 claude 프로세스 env 는 `max`**(`ps eww <pid>` 실측). shell/OS env 가 settings.json 을 이기므로 유효값은 `max`. → [[effort-global-xhigh]] warning 재작성 + **판정 시 `printenv` 금지, `ps eww` 사용** 명시.
- **근본원인 적립**: `scripts/bootstrap/setup.sh:118`·`setup.ps1:156` 이 이 repo 안에서 shell/User env 에 `max` 를 심는다 → [[effort-os-env-single-source]] 가 적립한 실패의 **재발**이며 bootstrap 재실행 시 재주입. 그 페이지의 `[!note] 현재 상태` 도 같은 stale(`xhigh`·"OS env 없음")이라 함께 교정. 스크립트 수정은 운영자산 변경이라 별건(plan `# Deferred`).
- 갱신: decision/effort-global-xhigh, decision/effort-os-env-single-source, decision/subagent-model-effort-tiering(haiku 배제 사유 페이지 간 충돌 `[!conflict]` flag), entity/claude-code-model-selection(`SUBAGENT_MODEL=inherit` no-op 함정, availableModels 버전 조건). 편집한 5개 페이지 `updated`/`sources` 갱신(WIKI.md 필수 필드 누락 교정).

## [2026-08-12] ingest | native-overlap 1b `retire` 확정 + lesson-test-after-implementation (신규)
- **이 축의 첫 `retire`**: `guard-worktree-edit.js` 기능 ②(worktree 밖 편집 deny)가 네이티브 worktree 격리(v2.1.222)에 완전히 흡수됐음을 실측으로 확정. 정본 changelog 는 "isolation now applies file edits" 라고만 적고 범위를 안 밝혀 **문서로는 판정 불가**였다 — worktree 세션에서 main checkout 경로에 실제 Write 를 시도해 갈랐다.
- 관측: 자작이 **허용**하는 `<main>/plans/…` 를 네이티브가 **거부** → 진상위집합. 기능 ①(비-worktree 세션의 main 직접편집 `ask`)은 교집합이 없어 `keep` — 1행을 1a/1b 로 분리했다.
- **부수 발견(`[!conflict]` 로 flag)**: 네이티브에는 자작이 뒀던 예외(`plans/`·`projects/`·`settings.local.json` — worktree 복사본이 없는 전역 상태)가 없어 **worktree 세션에서 §12 memory 적립이 불가능**하다. hook 을 되살려도 안 풀린다(네이티브가 선행 차단). `retire` 판정과는 별개인 workflow 마찰로 추적.
- `checked` 는 밀지 않았다 — 이번 건 changelog delta 전수 조회가 아니라 1행 표적 실측이라, `checked` 를 갱신하면 45일 타이머가 근거 없이 리셋된다. `checked`↔`updated` 구분을 대장 운영 규칙에 명문화.
- lesson 신규 [[lesson-test-after-implementation]] — PR #139 의 §7 순서 위반 자진 기록. 근본원인은 "분량으로 TDD 필요 여부를 판단"한 것이고, 실제 위험은 분량이 아니라 경계 밀도(날짜·TZ·버전·인코딩)였다. [[lesson-parser-precedent-partial-mirror]] 와 상호링크(같은 "형식은 맞는데 무음으로 틀린 값" 계열).
- orphan 2건([[lesson-parallel-duplicate-implementation]]·[[lesson-parser-precedent-partial-mirror]]) 을 inbound 링크로 해소 — `check_links.py` clean.

## [2026-08-12] update | workflow-failures — doc-drift 재편집 오탐 fixed
- 신규 sub-class 적립 + fixed: 동기화 후 이미 문서화된 trigger 파일을 재편집하면 `dlc-doc-drift` 가 다시 dirty 로 판정하던 오탐. 한 세션에서 2회 재현(README·wiki index)이라 §13 기록 트리거 ②(동일 유형 2회) 충족.
- 근본 원인은 heuristic 한계가 아니라 **모델링 오류**였다 — 문서 동기화는 편집 *순서*가 아니라 *상태*인데 `applyChange` 가 순서(trigger→dirty / target→clean)로만 다뤄, target 뒤에 오는 어떤 trigger 든 미동기화로 뒤집었다. 기존 두 오탐 항목(내부 dedup·`.test.js`)이 "무엇이 trigger 인가"를 좁히는 방향이었다면 이번 건은 "언제 clean 인가"를 고친 것.
- covered-set 전환으로 새 surface 탐지는 유지(미탐 미도입). 부수 위험 하나를 테스트로 못박음: `ledger.DEFAULT` 가 `{...DEFAULT}` 얕은 복사로 쓰여 배열에 `push` 하면 전 세션이 같은 배열을 공유·오염 → `concat` 강제.
- §7 TDD 순서를 지킨 첫 사례([[lesson-test-after-implementation]] 적립 직후 첫 적용) — 경계를 먼저 열거하고 Red 확인 후 구현했고, DEFAULT 오염 케이스는 그 열거 과정에서 나왔다.
