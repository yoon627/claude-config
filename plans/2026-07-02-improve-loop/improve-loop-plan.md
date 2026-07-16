---
title: improve-loop — 자기개선 loop Workstream A: 신호 수집 + /improve skill (audit 흡수)
status: done
started: 2026-07-02
updated: 2026-07-04
---

# Goal
dlc 자기개선 loop 의 수집·분석 축 기계화: ① workflow 실패 신호를 hook 이 세션·프로젝트를 가로질러 자동 누적(append-only JSONL) ② `/improve` skill 이 기계 점검(기존 audit.sh 흡수)+누적 신호 분석으로 개선 후보를 랭킹 제시. 수정은 승인 후 wt→dlc(자동 수정 금지 §1 유지). 상위: `<main>/plans/2026-07-02-workflow-loopify/`.

# Progress
- 2026-07-02: worktree 생성(improve-loop), Explore 완료(감사 세션 지식 재사용 + lint.yml·테스트 러너·audit 참조 표면 확인), researcher skip(외부 사실 의존 없음), draft plan 작성.
- 2026-07-02: arch planning 검토 — 구조 골격(ledger/signal 분리·emit 분산·의존 단방향) 승인. 필수: env 기반 signal override 채널(spawn 테스트 격리). 후속: ctx 스키마 단일화·판정/IO 구분·회전 trade-off·improve 두-축 경계 → Decisions 반영 완료.
- 2026-07-03: 사용자 Loop Engineering 5단계 요구 반영 — 1·2·3단계는 기존 dlc 충족 확인, 갭인 5단계(리뷰 피드백 기억)를 dlc Report feedback memory 판정 의무로 스코프 추가. codegraph(worktree 자동 init 작동·172노드)·headroom(세션 실측 8% 절감)·wiki(dlc 연계 기존재·재사용 사례 입증) 진단 완료.
- 2026-07-03: plan-reviewer(+codex 병행, 합의 6건) CONDITIONAL → 필수 4건 반영: 신호 substring→상태전이 재정의·evidence-ledger emit 을 isIgnored 밖 배치·테스트 자기격리(env 명시)·taxonomy(failure/activity)+raw/session-unique 집계. 약한 우려(payload `~` 축약·session_id null·rotate best-effort 명문화)도 Decisions 반영. 구조 불변이라 arch 재실행 불요.
- 2026-07-03: TDD Red(모듈 부재 확인)→구현(dlc-signal.js+테스트 20건, hook 4종 emit, guard 테스트 자기격리, skills/improve 신설·audit 제거, dlc SKILL 연계 2건, lint.yml·README·wiki 3페이지+index 동기화)→Green(단위·통합·grounding·오염0 전부 관찰). arch 정밀 APPROVE(계약 6항 준수)·code-review NEEDS DISCUSSION→fix loop 1회차에서 Major 1(disposition 섹션 스코프)+Minor 5+Nit 2 반영, wontfix 1(위 disposition). 로컬 검증: node --check 전체·테스트 3종 pass·settings parse·bash -n OK, shellcheck 는 로컬 미설치로 CI 위임.

# Next
없음 — PR #70 머지 완료(33ec7e7), main ff-pull 완료, CI(shellcheck 포함) 통과. 후속은 상위 plan workflow-loopify 의 Workstream B.

# Acceptance 대조 결과 (2026-07-03 — evidence gate)
1 ✅ dlc-signal.test.js 20 pass(Red 선확인: MODULE_NOT_FOUND 관찰) / 2 ✅ 기존 테스트 비회귀+guard 자기격리+telemetry 오염 0 실측 / 3 ✅ node --check 14종·settings parse·bash -n (⚠️shellcheck 만 로컬 미설치 — CI lint.yml 게이트 위임, 경로 갱신 확인) / 4 ✅ 4개 emit 지점 grounding(spawn 통합 3 + 주입 관찰 2)+본연 출력 비회귀 / 5 ✅ fail-open(쓰기불가·OFF·require 부재) / 6 ✅ improve.sh 실행 관찰(error=0·skip 라인) / 7 ✅ audit 잔존 참조 0 / 8 ✅ README·lint.yml·dlc SKILL·wiki 4페이지+index 동기화.

# Decisions
- **저장 위치**: `~/.claude/telemetry/dlc-signals.jsonl` — home 앵커(글로벌 hook 이라 모든 프로젝트에서 한 곳에 누적, worktree/repo 무관). gitignored(whitelist .gitignore 라 자동 제외). 이유: per-session tmp ledger(휘발)와 달리 loop 분석엔 영속 필요, wiki/raw 는 큐레이션 대상이라 부적합.
- **settings.json 무변경**: 새 hook 등록 없이 기존 hook 스크립트 4종(early-stop·guard-worktree-edit·task-router·evidence-ledger)에 신호 emit 을 심는다. 이유: hook 등록 실수 리스크 0, 이미 검증된 실행 경로 재사용.
- **신호 세트(hook 감지 가능한 것만)**: early-stop-verify / doc-drift-readme / doc-drift-index / guard-worktree-deny / router-investigation / router-grounding / plan-blocked / review-disposition. "사용자 교정 발언 감지"는 오탐 커서 제외(상위 plan Next 에도 없음).
- **신호 taxonomy (plan-review 반영)**: failure 축 = early-stop-verify·doc-drift-*·guard-worktree-deny·plan-blocked(개선 효과 측정 대상) / activity 축 = router-*·review-disposition(작업 유형·리뷰 활동량 — 실패 아님). 모듈 KINDS 상수에 axis 명시, improve 집계는 축 분리 + **raw count 와 session-unique count 병기**(중복 발동 노이즈 흡수).
- **plan 신호 재정의 — substring 금지 (plan-review 필수)**: 이 plan 파일 자신도 `status: blocked` 문자열·`# Review Disposition` 헤더를 문서로 포함 — 문자열 존재 감지는 템플릿을 센다. `detectPlanSignal(toolName, toolInput)`: ① 대상 필터 = 경로에 `/plans/` 포함 + `.md`. ② plan-blocked: Edit 는 `new_string` 의 frontmatter 형 `status: blocked` 라인이 **있고 `old_string` 엔 없을 때만**(상태 전이); Write 는 `content` frontmatter(첫 `---` 블록 내)의 `status: blocked` 일 때(전이 판단 불가 — session-unique 집계로 반복 흡수). ③ review-disposition: `# Review Disposition` 헤더 자체가 아니라 **disposition 값 토큰**(`fix|defer|false-positive|wontfix` 목록 라인)이 new_string/content 에 추가됐을 때(Edit 는 old 에 없던 경우만).
- **emit 배치 (plan-review 필수)**: evidence-ledger 의 plan-signal emit 은 기존 `isIgnored` 게이트 **밖**에 둔다 — plans/ 는 gitignored 라 기존 블록은 plan 파일을 항상 skip(실측 확인됨). early-stop emit 은 reasons 출력 지점 **안**(실제 block 발생시만). router emit 은 주입 출력 지점 안.
- **테스트 자기격리 (plan-review 필수)**: 모든 hook 테스트는 child spawn 에 `env: {...process.env, CLAUDE_DLC_SIGNAL_OFF: '1'}` 을 **테스트 파일 자체가 명시**(절차 의존 금지 — lint.yml 은 env 없이 실행). 기존 guard-worktree-edit.test.js 도 이 방식으로 수정(스코프 내). 신규 signal 통합 검증만 `CLAUDE_DLC_SIGNAL_DIR`=tmpdir 로 관찰.
- **payload 정규화 (plan-review)**: cwd·파일 경로는 홈을 `~` 로 축약(글로벌 telemetry 에 환경 식별자 축적 최소화, §8). session_id 부재 시 `'default'` 로 뭉개지 않고 `null`(unique-session 집계 왜곡 방지).
- **rotate 명문화 (plan-review)**: best-effort(비원자) — 동시 세션에서 `.1` 덮어쓰기·회전 직후 유실 가능, 실패해도 append 는 계속. /improve 는 현재 파일만 읽음(회전 직후 관측창 축소 수용).
- **fail-open 불변**: 신호 emit 실패가 hook 본연 동작(경고·차단)을 절대 막지 않는다 — 모든 emit try/catch, 모듈 require 실패 시 no-op.
- **env override 채널 (arch 필수 지적)**: `CLAUDE_DLC_SIGNAL_DIR`(경로 redirect)·`CLAUDE_DLC_SIGNAL_OFF=1`(무력화)를 signal 모듈이 읽는다. 이유: hook 테스트는 execFileSync spawn 방식이라 함수 파라미터 주입 불가 — env 없이는 기존 guard 테스트의 deny 케이스가 프로덕션 telemetry 를 오염(신호 데이터 = loop 산출물이라 오염이 곧 목표 훼손). 기존·신규 hook 테스트는 이 env 로 tmpdir 격리.
- **ctx 스키마 단일화 (arch)**: append 의 ctx 를 모듈 한 곳에서 정규화(`{ts, session_id, cwd, kind, detail?}` — dlc-ledger DEFAULT 단일 스키마 패턴 차용). 4개 hook 이 제각각 필드를 넣지 않는다.
- **판정/IO 구분 (arch)**: detectPlanSignal 은 순수 함수(파일 무접촉)로 export — doc-drift 선례. 별도 파일화는 과분리(1함수)라 signal.js 내 "순수 판정" 섹션으로 구분만.
- **회전 trade-off (arch)**: 5MB 단일 회전 = 추이 관측 창 상한(초과분 유실 허용) — 소비자 1개·저빈도라 충분, 늘면 날짜 파티션 검토.
- **개인정보/시크릿**: 신호에 프롬프트 원문·파일 내용 저장 금지 — kind·ts·session_id·cwd·파일 경로(경로만)로 한정(§8).
- **회전**: 5MB 초과 시 `.1` 로 단일 회전(무한 성장 방지, 구현 단순).
- **/improve = audit 승계+확장**: audit.sh → skills/improve/improve.sh 이동, 기계 점검 유지 + 신호 집계 섹션 추가. 역할 경계(README drift=hook, wiki 내부=wiki lint) 승계. skills/audit/ 제거. dlc SKILL.md 의 Workflow Findings 절에 /improve·telemetry 연계 1-2줄(승인 스코프 내 — 상위 plan Key Files 명시).
- **improve 두 축 경계 (arch)**: SKILL.md 에 ① 정적 크로스참조 점검(audit 승계 — 경계 그대로) ② 신호 집계(hook 이 emit 한 판정의 **사후 집계**, 재판정 아님) 를 명시 — drift 를 improve 가 "직접 본다"로 오독돼 hook 과 책임 중복으로 비치는 것 방지.
- **feedback memory 판정 의무 (사용자 Loop Engineering 5단계, 2026-07-03 추가)**: dlc SKILL.md 16 Report 에 "작업 중 사용자 교정·리뷰 지적이 있었으면 §12 feedback memory 저장 판정(대상이면 저장+MEMORY.md 인덱스, 비대상이면 사유 1줄)" 추가 — wiki ingest 판정과 대칭. 이유: §12 트리거가 사용자 명시 지시뿐이라 MEMORY.md 1개(사실상 미작동) — 사용자 리뷰 피드백이 다음 구현에 반영되는 5단계 loop 의 갭. 신호 kind 로 감지하지 않고(오탐) 절차 판정으로 해결.
- **효과 측정**: /improve 가 kind별 일자 추이를 보고(개선 fixed 후 같은 신호 감소 확인) — 별도 인프라 없이 JSONL 집계로.

# Key Files
- scripts/dlc-signal.js (신규) — append/rotate/planSignal 순수 모듈 + scripts/dlc-signal.test.js (신규)
- scripts/dlc-early-stop.js·guard-worktree-edit.js·dlc-task-router.js·dlc-evidence-ledger.js — emit 심기
- skills/improve/SKILL.md (신규)·skills/improve/improve.sh (audit.sh 이동+확장) / skills/audit/ (제거)
- .github/workflows/lint.yml — node --check·테스트·shellcheck 경로 갱신
- README.md — audit 절→improve, scripts 절, repo layout / skills/dlc/SKILL.md — Workflow Findings 연계
- wiki/pages/decision/self-diagnosis-and-improvement-status.md·workflow-failures.md·wiki/index.md — 채택 상태 갱신

# Blockers
(없음)

# Acceptance
1. `node scripts/dlc-signal.test.js` 전 케이스 pass (TDD: Red 선확인 후 Green).
2. 기존 테스트 비회귀: `node scripts/dlc-doc-drift.test.js`·`node scripts/guard-worktree-edit.test.js` pass — **guard 테스트는 `CLAUDE_DLC_SIGNAL_DIR`(tmpdir) 격리 하에 실행되고, 실행 후 실제 `~/.claude/telemetry/` 에 신규 라인이 없음**을 관찰(오염 0).
3. lint.yml 로컬 재현 통과: 변경·신규 전 스크립트 `node --check`, `node -e "JSON.parse(...settings.json)"`, `shellcheck scripts/*.sh skills/e/*.sh skills/improve/*.sh`.
4. **실행·관찰(grounding)**: stdin 주입(`echo '<json>' | node scripts/<hook>.js`)으로 4개 emit 지점 각각 telemetry JSONL 라인 생성을 관찰 + hook 본연 출력(block JSON/deny JSON/additionalContext) 비회귀 관찰.
5. **fail-open 관찰**: telemetry 경로 쓰기 불가 상황(권한/존재불가 디렉토리 주입)에서도 hook 정상 출력.
6. `bash skills/improve/improve.sh` 실행 → 기존 audit 기계 점검 출력 + 신호 집계 섹션 관찰(신호 0건·파일 부재 시 skip 라인 포함).
7. audit 잔존 참조 0: `grep -rn "skills/audit" .` (git tracked 표면) 결과 없음.
8. 문서 동기화: README(improve·dlc-signal·telemetry·layout)·lint.yml·wiki/index.md·wiki 페이지 2종 갱신 완료(diff 존재).

# Review Disposition
- [arch post-impl] 구조 계약 6항 준수 APPROVE, finding 0 — require 중복·early-stop dirty 분기 중복은 simplifier 위임.
- [code-review Major] DISPOSITION_LINE 이 산문 bullet 의 fix/defer 도 매칭(섹션 스코프 부재) — **fix**: Edit 는 Review Disposition 헤더/placeholder 컨텍스트 게이트, Write 는 섹션 스코프 파싱. 음성 테스트 추가.
- [code-review Minor] plan-blocked Edit 가 본문 col-0 status 라인에 오발화 가능 — **fix**: old 에 기존 `^status:` 라인 존재(교체) 요구 + 음성 테스트.
- [code-review Minor] CLI summary 가 회전분 `.1` 미집계 — **fix**: `.1` 병합 읽기 + 테스트 (plan 의 '관측창 축소 수용' 결정을 저비용 개선으로 상향).
- [code-review Minor] telemetry 경로 메타데이터(로컬 잔존) README 미서술 — **fix**: 한 줄 보강.
- [code-review Minor] wiki dlc-development-cycle·fablize-adopted-disciplines 과소서술 — **fix**: 2페이지 채택 상태 갱신(+updated).
- [code-review Minor] `/plans/` 필터가 상대경로 miss — **fix**: `(^|/)plans/` + 테스트.
- [code-review Nit] README requirer 이중계수·guard 통합테스트 약한 OR — **fix**.
- [code-review Nit] summarize 가 ts 를 Date 검증 없이 문자열 비교 — **wontfix**: emit 이 만드는 고정폭 UTC ISO 만 유입(사전순=시간순), 손상 라인 위험 낮음.
- [targeted 재리뷰 APPROVE — 잔여 Nit 3] 코드블록 내 `#` 의 섹션 조기종료·DISPOSITION_CONTEXT 무앵커 산문 언급 오탐·대문자 `Status:` 미탐 — **wontfix**: 전부 현실성 낮음 + activity 축 session-unique 흡수 + 코드 주석에 명시된 정밀도-우선 tradeoff.
- [simplifier 제안] `signalPath` export 미소비 정리 — **defer**: public export 계약 변경, ROI 극소. evaluate 구조화 반환(-2줄) — **wontfix**: 다중 파일 계약 변경 대비 이득 없음.

# Workflow Findings
- rtk-rewrite hook 이 복합 Bash 명령을 손상: ① 다중 인자 `cat a b c` → `/usr/bin/read` 오류(✅재현) ② `echo ===` 체인 → zsh `== not found`(✅재현) ③ rg 다중 경로 체인 exit 2(⚠️원인 미확정) ④ `tail -6 f` → read 오재작성(✅재현). 재발 조건: 체인/특수문자 포함 명령. 수정 후보: hooks/rtk-rewrite.sh. 횟수 4 → wiki workflow-failures 에 tracking 기록 완료(2026-07-03).
- evidence-ledger `isIgnored` 가 **세션 worktree 밖 절대경로**(main worktree 의 gitignored `plans/`·`/tmp` 파일)에서 `git check-ignore` 실패 → not-ignored 로 평탄화 → changed=true 오탐 → early-stop false block. 재발 조건: worktree 세션에서 main 의 plan 파일 편집(상위 plan 동기화 — 흔한 경로). 수정 후보: `scripts/dlc-evidence-ledger.js` isIgnored 에 repo-루트 스위칭 또는 `/plans/`·repo 밖 경로 예외. 횟수 1(2026-07-03 — 기존 fixed 항목의 변형).
