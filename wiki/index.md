# Wiki Index

모든 페이지의 1줄 요약(카테고리별). ingest 시 갱신. 운영 규약은 `WIKI.md`.

## concept
- [[llm-wiki-pattern]] — 이 wiki 가 따르는 LLM Wiki 패턴(Karpathy): 영속·누적 markdown 지식베이스.
- [[project-memory]] — 이 wiki 의 목적·`plans/` 와의 경계(일시적 vs 영속).
- [[ingest-operation]] — raw/지식을 wiki 에 반영하는 연산 절차.
- [[dlc-development-cycle]] — 비자명 코드변경 개발사이클 오케스트레이션(규모 gate·16단계·격리·요구사항 명확화 6항→plan `# Intent`(medium 이상 항상)·분할 판정(→ 묶음 intent 또는 `분할: 없음`)·마무리 판정 3값).
- [[plan-handoff]] — 세션·도구 간 작업 컨텍스트 단일 plan 채널(§10·single-writer·active tracking·선택 섹션 `# Intent`/`# Acceptance` 외·묶음 intent `intent.md` 에 plan 여럿이 `intent:` 로 링크).
- [[hub-and-spoke-isolation]] — 메인 hub(구현·통합·판단), reviewer 는 격리 read-only spoke.
- [[worktree-per-task]] — 작업마다 격리 worktree(wt skill·자동 bootstrap·삭제 조건).
- [[claude-codex-collaboration]] — Claude(구현·통합)↔Codex(리뷰·검증) 병행(§9·리뷰 매트릭스).
- [[feedback-memory]] — 사용자 교정의 영속화(§12·MEMORY.md 인덱스=행동지시문).
- [[unknowns-discovery]] — 구현 전 unknowns(unknown unknowns) 능동 발굴 기법→dlc 매핑(blind-spot·질문우선순위·프로토타입-우선·퀴즈·deviations·Intent 기록).

## entity
- [[anthropic-claude-models]] — Claude 5 세대 가격·Fable 주간 50% 캡·벤치 구도(닫힌 코딩 Opus5≥Fable)·effort 지원 (2026-08).
- [[claude-code-hook-notification-turns]] — UserPromptSubmit 은 subagent 완료 `<task-notification>` 턴에도 발동(2.1.258 실측) — hook 의 prompt 를 사용자 발화로 가정하지 말 것; dlc-task-router 오발동·장부 리셋 원인(PR #149).
- [[claude-code-agents-md-loading]] — v2.1.277+ 는 cwd·상위에 CLAUDE.md 가 없으면 AGENTS.md 를 읽고 `~/.claude/CLAUDE.md` 는 그 판정에서 세지 않는다 → `~/.claude` 세션에 Codex 미러 AGENTS.md 가 함께 주입됐다; `claudeMdExcludes` 로 그 경로만 제외(2026-09-25 실측). Codex 쪽은 `~/.codex/AGENTS.md` → CLAUDE.md 심링크로 복원.
- [[worktree-isolation-bash-guard]] — worktree 격리 세션의 네이티브 Bash 거부는 경로가 아니라 명령 텍스트의 git 언급이 트리거(플래그명·heredoc 본문 포함)·비결정적; 우회는 payload 파일 분리 + git 토큰 제거. "Agent hook condition was not met" 는 이 가드가 아니라 repo agent hook.
- [[git-autosquash-target-selection]] — git 2.54 `rebase --autosquash` 대상 선택 실측: 첫 접두는 `fixup! ` 리터럴(탭이면 fixup 아님), 제목 정확 → 커밋 이름 → 제목 접두 순·각 단계 가장 앞 커밋, 제목이 sha 보다 우선, fixup 커밋도 후보 (2026-09-24).
- [[git-log-added-lines-hardening]] — `git log -p` 로 추가 줄을 검사할 때 사용자 설정·환경·attributes 가 줄을 0건으로 만드는 경로 13가지(`log.diffMerges=off`·`showRoot`·`follow`·binary/`-diff`·replace·pathspec env·로케일 등)와 막는 옵션, Windows PS5.1 Process·env·코드페이지 함정 (2026-09-25 실측). "이미 공개됨" 은 추적 ref 가 아니라 stdin remote sha 로 정한다(pushurl 마다 따로 옴·재작성 뒤 오래된 ref, 2026-09-26).
- [[claude-code-statusline-input]] — subagentStatusLine 입력 `{…, columns, tasks[]}`·출력 `{"id","content"}` 줄, `name` 은 등록한 agent 만, `CLAUDE_CODE_TMPDIR` 규칙·slug 의 `.`→`-`, tasks 디렉토리에 foreground Bash 출력이 섞임, worktree 진입 뒤 transcript 는 옮겨지고 tasks 는 시작 slug 에 남음 (2026-09-25 실측).
- [[claude-code-bash-tool-shims]] — Bash 도구의 `grep` 은 명령 모양에 따라 내장 ugrep(셸 함수, `-I --ignore-files`)이나 `rtk grep`(훅 재작성, 비UTF-8 인자에서 panic)으로 바뀐다; 스크립트 안에서만 시스템 grep. 바이트 판정은 python 으로 (2.1.282·rtk 0.44.2, 2026-09-26).
- [[github-sensitive-data-removal]] — 비밀 이력 제거의 공식 절차가 그렇게 생긴 이유: filter-repo 는 fresh clone 만·`--sensitive-data-removal` 은 origin 유지·`--mirror` 로 모든 ref·`refs/pull/*` 는 Support·merge 말고 rebase (git-filter-repo 2.47.0 실측, 절차 정본은 README).
- [[claude-code-subagent-config]] — subagent frontmatter model/effort·env 우선순위·Haiku effort.
- [[claude-code-model-selection]] — alias(opusplan, fableplan 없음)·advisor tool 공식 수치·/model 저장·subagent model 함정(inherit×Fable)·pin 시 확정사실(`[1m]` 금지·자동 1M·폴백 없음).
- [[claude-code-oss-frameworks]] — OSS 하네스 생태계 스냅샷(2026-08): 커버리지 부분적·프레임워크 후퇴·내부 확장이 정책 안전.
- [[codegraph]] — retired(2026-09-15) 코드 심볼 그래프 MCP 의 historical 기록 — 보존 로그상 성공 호출 0회로 전역 해제, wt 자동 init·bootstrap 에서 제거.
- [[headroom]] — retired 컨텍스트 최적화 proxy/MCP의 historical 기록(현재 bootstrap·runtime 미사용).

## decision
- [[effort-global-xhigh]] — effort 정책의 이력; 현재는 강제 env 없음으로 `/effort`·모델 기본값을 사용한다. `max`는 settings 파일이 아니라 env/일회성 옵션에서만 가능.
- [[model-stage-tiering]] — dlc 단계별 모델 배치(2026-08-05): Fable=plan/설계만(50% 캡), 구현 opus(촘촘한 plan은 sonnet), 리뷰 opus, 조사 sonnet. **agents/*.md 고정 완료(2026-08-06)**.
- [[harness-keep-and-borrow]] — 자작 하네스 유지+부품 차용 결정(2026-08-05): 대체 OSS 부재·프레임워크 후퇴·정책 안전성; 유지비 감시 + 네이티브 중복 역정리 조건(→ [[native-overlap-ledger]] 로 2026-08-06 구현).
- [[subagent-model-effort-tiering]] — (superseded by [[effort-global-xhigh]]; model 차등만 2026-08-06 부분 복원 → [[model-stage-tiering]]) reviewer opus+max / simplifier sonnet / researcher haiku 차등 (#51).
- [[effort-os-env-single-source]] — OS env > settings.json env라는 precedence와, 전역 env를 제거해 `/effort`를 복구한 결정.
- [[dual-review-plan-and-code]] — plan 리뷰(구현 전) + code 리뷰(구현 후) 관점 분리.
- [[deferred-and-scope-boundary]] — 범위 밖 발견 보존(# Deferred)·운영자산 자가수정 금지 (#50).
- [[self-diagnosis-and-improvement-status]] — 자기진단 채택(#49) / 자기개선 = 수집·분석 기계화 채택(2026-07-03, dlc-signal+/improve), 반영은 승인 게이트 유지.
- [[comment-and-commit-policy]] — 주석 최소·변경 경위는 커밋/PR 에 (#26·#34·#25).
- [[codex-bash-invocation]] — codex 는 Bash 도구로 호출(PowerShell stdin hang 회피, #23).
- [[evidence-gate]] — 검증 항목화 + 증거 충족 시만 완료(plan # Acceptance + Stop hook 보조, capped·fail-open). 미충족 처분은 DONE/BLOCKED/NEEDS-HUMAN 판정.
- [[lesson-gate-safe-side-first]] — 게이트 판정을 고칠 땐 정확도보다 안전측을 먼저 확정(빈 `.git` 오탐을 고치다 손상 repo 미탐을 넣은 사례, 2026-09-08).
- [[lesson-stale-branch-premise]] — 오래된 브랜치는 diff 가 아니라 *전제*가 유효한지부터 확인(371커밋 뒤 `plans/` tracked 전환이 P0 근거를 무효화, 2026-09-08).
- [[e-merge-mode]] — `/e merge` 머지 모드 설계(2026-09-02): 트리거 토큰 한정·done 을 PR 에 싣고 REJECTED 만 복구·mergedAt+fetch invariant·MERGED PR 재사용 안 함·checks 는 exit code+bucket·`--delete-branch` 금지.
- [[dlc-wt-autoflow]] — dlc 가 코드/파일을 바꾸면 규모 불문 wt worktree 자동 경유(순환 방지·생성은 무확인, 2026-08-03 확인 폐지 · 2026-09-04 trivial 포함으로 확대).
- [[risk-based-approval]] — 승인은 가역성으로 가른다: 비가역·외부공개·파괴적만 확인, 가역·로컬은 무확인 실행 후 되돌릴 정보 보고 (2026-08-03, graph engineering HITL 원칙). **`ask` 는 `allow` 로 풀리지 않는다**(deny→ask→allow, first match wins) — 2026-09-07 정정.
- [[rtk-rewrite-permission-rules]] — 명령을 재작성하는 PreToolUse 훅(rtk)이 있으면 권한 규칙은 재작성된 명령으로 평가된다: ask 는 원래 형태 + `rtk ` 형태를 함께 둔다. allow 는 auto 분류기보다 먼저 통과시키고 ask 는 auto 에서도 확인 창(2026-09-25 headless 실측·ask 10→72).
- [[fablize-adopted-disciplines]] — fablize 검증 규율 차용(grounding·investigation·early-stop), 플러그인 없이 직접 구현.
- [[workflow-failures]] — 반복 workflow 실패 누적 추적(자동 신호는 telemetry, 표는 맥락), 2회+ 반복 시 wt 해결 제안. 규약이 권장한 명령 자체가 실패하는 건도 적립(`gh pr merge --delete-branch` — worktree 가 base 를 점유해 정리만 누락, #123 에서 fixed). 2026-09-26: early-stop 이 Bash 경유 편집·검증을 못 봐 오탐 17회, 중간 턴 오탐 4회 tracking.
- [[ops-doc-slimming]] — 항상주입 운영문서 압축 상한 실측 ~11%(규칙손실0 유지 시), 30%+ 는 이관=범위확대; bytes 목표는 보조·규칙손실0 이 hard gate (#73). 후속 이관 실행(#89-92): 압축률∝1/규칙밀도(e −31%~CLAUDE −1.1%)·조건부로드 skill 이 참조하는 canonical 스펙 이관 금지(방향역전)·manifest+diff-U0+합집합grep 방법론.
- [[git-hook-network-safety]] — git 클라이언트 훅은 동기·무timeout → 네트워크 작업은 poll 워치독+PROMPT=0+SSH ConnectTimeout 으로 상한(하니스 안전망 없음); ff-merge 는 post-checkout 재발동 안 함(재귀 없음, 실측); async 훅은 hang 안전을 주는 대신 stdout 이 첫 턴 뒤에 도달 → 네트워크는 async, 사용자에게 보여야 할 판정은 동기로 분리 (#82). **2026-09-04**: 하니스 timeout 은 훅 프로세스만 죽이고 자손은 안 거둔다(SessionStart 훅도 자기 상한+프로세스 그룹 kill 필요) · CLAUDE.md 로드는 훅과 **경합**이라 동기 전환으로 같은 세션 최신화는 불가(실측 4케이스) · 훅이 띄운 손자를 거두려면 프로세스 그룹 분리가 필요한데 그 수단이 플랫폼별로 다르다(Linux setsid / Git Bash set -m, 겹쳐 쓰면 안 됨). **미결**: dirty tree 로 SessionStart pull 이 거부되는 건의 `--autostash` 도입 여부(2026-08-06 보류).
- [[lesson-fix-scoped-to-one-repo]] — 한 repo 에 하드코딩해 고치면 실패 모드는 안 덮인 repo 로 옮겨갈 뿐이다(2026-08-12 수정이 08-31 에 다른 repo 에서 재현). 대상 상수·라벨 상수 금지, 처방이 다르면 신호를 나눈다, 넓힐 땐 잡음을 먼저 실측한다.
- [[lesson-grep-absence-not-proof]] — grep 무매칭·**검색범위 누락·매칭 결과 오독**으로 "부재/영향 없음" 단정 금지, 동기화·영향 판정은 대상 파일 직접 확인. 사례 4(2026-09-25): 도구가 바꾼 grep(ugrep)이 0 을 내 "ps1 은 모두 ASCII" 오판 — 0 은 알려진 양성 샘플로 검사식을 먼저 확인
- [[lesson-parser-precedent-partial-mirror]] — 선례 파서 미러링은 전처리(CRLF)·토큰 관용까지, fixture 는 문서화된 정본 템플릿에서 (무음 결함 2건) (§13 첫 lesson).
- [[lesson-stale-tool-version]] — 도구발 오류는 우회 전에 `--version` 을 상류 CHANGELOG 와 대조; 실패 표의 "수정 위치"는 확인된 것만 적는다 (rtk 0.28.2 로 6회 반복, 상류는 0.35.0·0.39.0 에서 이미 수정).
- [[lesson-parallel-duplicate-implementation]] — 비trivial 착수 전 열린 PR·원격 브랜치·다른 plan 을 먼저 확인; plan 매칭 실패는 "없다"의 근거가 아니다 (#118 과 #120 이 같은 기능을 각자 구현, 553줄 폐기). 2회째: origin/commit-split(09-22) 을 보지 않고 #171·#172 착수, 설계 충돌로 close(2026-09-25).
- [[lesson-test-after-implementation]] — 경계 있는 도메인(날짜·TZ·버전·인코딩)은 분량 무관하게 Red 부터; 형식 통과 ≠ 값 유효(왕복 대조), 시각·오늘은 주입해 TZ 교차 실행 (PR #139 결함 2건).
- [[lesson-tracked-config-machine-paths]] — tracked 설정에 머신 절대경로 금지: Mac↔Windows ping-pong 으로 staged 가 6일 방치되고, 그 dirty 가 autopull 게이트를 막아 레포가 조용히 밀렸다. 동기화 훅에 dirty 게이트를 걸지 말 것(자기 차단). 2026-09-04 gitkraken marketplace 로 **재발 1회** — "이 키를 여기 두지 않는다"는 제외 결정을 커밋 본문에만 두면 다음 세션이 누락으로 오인해 되돌린다. 2026-09-07 `autoMode`(사내 IP·도메인)로 **재발 2회** → 키가 아니라 **`settings.json` 파일 자체를 추적 중단**. `autoMode` 는 `settings.local.json` 에서 안 읽히므로 표준 remedy 가 통하지 않는다. 3회 반복된 진짜 원인은 이 lesson 의 `MEMORY.md` 인덱스 줄이 없어 자동 상기가 성립한 적 없다는 것.
- [[lesson-test-copies-artifact]] — 검증 스크립트에 배포물을 복붙하면 갈라진 뒤 "통과"한다; 테스트는 배포물에서 직접 읽고 exit code 아닌 분기 마커를 assert (거짓 통과 1회 실측).
- [[lesson-agent-hook-if-best-effort]] — hook `if` 는 best-effort 라 게이트가 아니다: agent/prompt hook 프롬프트 0단계에서 `tool_input` 으로 범위를 자체 판정하고, 게이트 hook 은 플랫폼마다 막혀야 할 케이스를 실제로 넣어 fail-open 을 확인(`shell: powershell` 은 macOS 에서 실패 후 통과했다).
- [[native-overlap-ledger]] — 자작 부품 ↔ 네이티브 흡수 대조 대장(keep/watch/retire). 45일 주기·delta 창(`checked_version`)으로 changelog 를 전수 아닌 증분만 조회, `/improve` §6 이 읽고 갱신은 승인 후 ingest(판정 분포는 대장에만).
- [[lesson-zip-reproducibility-os]] — Python zip 재현성은 timestamp 고정만으론 안 된다: `ZipInfo.create_system`(win32=0/그 외 3)과 `sorted(Path)` 의 Windows case-fold 로 OS 마다 sha 가 갈린다. `create_system=3` 명시 + posix 문자열 정렬, 테스트는 엔트리 순서·create_system 을 직접 assert (2026-09-22 리뷰 실측).
- [[lesson-verify-scaffold-purpose-before-removal]] — 장치를 "낡은 scaffold" 로 없애기 전에 도입 plan·결정을 읽고 원래 목적을 하나씩 반박할 수 있는지 확인; 날짜는 경위와 적용 범위를 구분 (prompt-audit 제안 3건이 plan-review 에서 뒤집힘, 2026-09-24).
- [[commit-restructure-plumbing-cas]] — 커밋 경계 재구성은 in-place rebase 가 아니라 merge-tree+commit-tree 재조립 후 update-ref --stdin 트랜잭션 CAS(실패 시 사용자 상태 불변). rebase abort 실패·author/트레일러 유실·symref 트랜잭션 거부 실측 (2026-09-24).
- [[ci-secret-scan-backstop]] — CI 에서 pre-push 가드를 사후 재실행: base 를 remote sha 로 넘겨 checkout 에서 바로 부른다(가드가 추적 ref 를 보지 않게 된 뒤 임시 bare repo 제거, shallow 거부), PR 은 `head.sha` 를 `HEAD^1` 기준으로, 없는 base 는 전체 이력, 로그 값 마스킹, `!cancelled()` (PR #177).
- [[autopull-verified-ff]] — SessionStart 자동 pull 이 CI 를 통과한 커밋까지만 따라가게: main push 의 lint 통과 시 CI 가 `ci/verified` 에 기록 커밋(`main-sha`)을 쌓는다. GITHUB_TOKEN 은 `workflows` 권한이 없어 main 커밋을 가리키는 ref 는 workflow 변경 뒤 못 옮길 수 있음·기록 값은 늘 main 위·CI 먼저 client 나중·rollback 순서 (2026-09-26, client 단계 미착수).
- [[wiki-shared-layer]] — 여러 repo wiki 를 submodule 하나로 합치는 안 기각(공개 범위 혼합·worktree 에서 init·DETACHED·같은 브랜치 갱신 불가 실측); repo 결정은 각 repo, 공용 사실은 `~/.claude/wiki` (2026-09-26 사용자 결정, 구현 미착수).

## source
- [[ai-native-sdlc-playbook-intent]] — Claude Academy "AI-Native SDLC Playbook" Stage 1 "Capture as intent.md" 요약: 발의자가 Claude 와 proto-spec 을 그 자리에 쓰고 커밋(Problem·Proposed outcome·Affected·Constraints·Open questions), 증거는 커밋 이력, 후행지표는 survival rate. 이 repo 는 plan `# Intent`(단발) + 묶음 `plans/<date>-<slug>/intent.md`(여러 plan, 2026-09-15) 채택, 조직 장치·별도 `intent/` 홈 미채택.
- [[fable-field-guide-unknowns]] — Thariq "A Field Guide to Fable: Finding Your Unknowns"(2026-07-04) 요약: unknowns 사분면·발굴 기법(Interviews·References·Mockups·Blind spot scans·Explainer&Quiz·Implementation Notes).

## query
_(없음)_
