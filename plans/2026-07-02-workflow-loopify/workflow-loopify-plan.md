---
title: workflow-loopify — dlc 자기개선 loop 구축 + 운영 자산 정리 (2026-07-02 전수 감사 기반)
status: done
started: 2026-07-02
updated: 2026-07-17
---

# Goal
dlc/운영 자산을 "스스로 개선해나가는 loop"로 만든다: **수집·분석은 기계화, 수정은 승인 게이트 유지**(2026-06-19 결정의 병목이던 수동 수집만 해소). 동시에 감사에서 확인된 중복·미사용 자산을 정리하고, Opus-only 대비로 prose 의존 규칙을 hook 강제로 이관한다.

# Progress
- 2026-07-02: 전수 감사 완료(메인 solo — 최초 병렬 workflow 11 agent 는 세션 한도로 전멸, ~1M 토큰 소모 후 결과 0). 웹 리서치(fablize 실험·Fable 재배포·Sonnet 5 출시·ACE·MCP 2026) 완료. 사용자 결정 4건 확정(# Decisions). 이 plan 생성.
- 2026-07-03: **Workstream A 구현 완료** — worktree `improve-loop`, 커밋 `5ab50ac` (dlc-signal.js telemetry + hook 4곳 emit + /improve 신설·/audit 제거 + dlc SKILL 연계 + 문서·wiki 동기화). dlc 전체 파이프라인 경유(arch planning→plan-review CONDITIONAL 반영→TDD→arch 정밀 APPROVE·code-review fix loop 1회+targeted 재리뷰 APPROVE→simplifier 0건→격리 runner 22개 명령 전부 통과). 사용자 Loop Engineering 5단계 반영: 갭이던 5단계(리뷰 피드백 기억)를 dlc Report feedback memory 판정 의무로 추가. 진단: codegraph worktree 자동 init 작동·headroom 세션 8% 절감 실측·wiki 는 dlc 연계 기존재(재사용 사례 입증). push/PR 은 사용자 결정 대기.
- 2026-07-12 (Fable, /improve 첫 정기 실행): 기계 점검 error=0·warn=0. 신호 8일치 — failure: early-stop-verify 6세션/28회(대부분 ledger-fix 가 수정하는 오탐, 머지 지연으로 지속)·doc-drift 4세션(07-05 이후 0 — doc-slim 효과 ⚠️추정)·plan-blocked 2세션 / guard-deny 0(경계 위반 없음). 효과 확인: 06-19 fixed 항목 재발 0 ✓. 랭킹: ①머지 파이프라인 정체(최우선) ②rtk-rewrite tracking 4회(rtk upgrade 우선 시도 — 미실행) ③K·L 신규 등록(아래). #74(e rebase-merge 감지) 머지 확인.
- 2026-07-06 (/e, Opus): **머지 확인** — C(doc-slim #73)·gwl-zsh-wt-main(#72) 머지 완료, main ff-pull. **미머지 실작업 브랜치**: ledger-fix(f5215b0)·review-intake(30fe13c)·worktree-cleanup-flow(4704fdc, 다른 세션이 H 를 이미 구현·2리뷰·fix loop 완료). **구조 오류 2건 수정**: ① 신규 worktree 4개(F·G·H·I)가 상대경로+cwd 누출로 doc-slim 내부 중첩 생성됐던 것 → 제거 후 절대경로 재생성(plan 보존). ② **H(wt-cleanup-auto)는 worktree-cleanup-flow 와 완전 중복** — 후자가 이미 구현·미머지라 H 는 잉여(정리 대상). settings.json ` M`(사용자 model 변경) 은 미커밋 유지(§8 main 직접 금지).
- 2026-07-15 (opus, /c 진단): **머지 파이프라인 전량 배수 확인** — ready 3건 모두 머지·정리 완료: `ledger-fix`→#77, `worktree-cleanup-flow` 계열(worktree 정리 자동화+CLAUDE §8)→**#76 cleanup-rule**, `review-intake`→#75. doc-slim 후속 wiki ingest→#78(별건). 검증: 5개 잔존 브랜치(finish-recap·main-autopull·plans-sync·unknowns-pass·loop-ops) 전부 `git rev-list origin/main..<br>`=0(ahead=0) → **자기 커밋 없는 빈 스캐폴드(미구현)**. 머지 대상 0. **Next ① 종결, ②(계획 workstream 구현)로 이관.**
- 2026-07-15 (opus, 이어서): **F. finish-recap 구현·머지 완료 (#79, `40ebf96`)** — 이전 세션 미커밋 WIP 발견→커밋(`e05e569`), code-review(Claude REQUEST CHANGES + codex blocker) Major(e recap 이 조건부 step5 에 근거) fix loop 1회(`7d36689`), README 동기화, worktree·로컬·원격 브랜치 정리, memory `report-conclusion-first` §12 승격 정리(→CLAUDE §3-6). **다음 ready**: unknowns-pass(finish-recap 머지로 unblock — dlc/e SKILL 체인)·loop-ops(독립·즉시).
- 2026-07-16 (opus, 이어서): **J. unknowns-pass 구현·머지 완료 (#80, `2f1270e`)** — Thariq Fable unknowns 기법 3종(blind-spot·질문우선순위·프로토타입-우선) dlc 명확화 절 반영 + dead ref 정리 + wiki ingest(source/concept 2페이지). code-review(Claude APPROVE + codex blocker) fix loop 1회(기법명 원문 정정·dead-key 0refs·프로토타입 절 이동). worktree·브랜치 정리. **남은 ready**: loop-ops(K+L+M, 독립)·main-autopull(G)·plans-sync(I, 최후)·E plan-lint(상세 plan 필요).
- 2026-07-16 (opus, 이어서): **G. main-autopull(#82)·K+L+M. loop-ops(#81) 머지 완료** 확인 + **I. plans-sync 구현·머지 완료 (#83, `202c4f5`)** — plans/ tracked 전환(방안 A): .gitignore whitelist·pre-commit-check plans 스캔·evidence-ledger isPlan 게이트·문서. install-hooks end-to-end 검증. **마이그레이션**: 전 plan 전수 secret 스캔 clean → main 미tracked plan 10 + plans-sync plan 을 `plans-migrate` 로 tracked 커밋. **남은 workstream = E(plan-lint) 하나** — 나머지 A~M 전부 완료. umbrella 는 E 완료 시 done.
- 2026-07-17 (opus, 캡스톤·종결): **E. plan-lint 구현·머지 완료 (#86)** — §10 plan 무결성 CI+스킬 게이트. 머지 직후 legacy plan 3건 실드리프트 검출(그 중 review-intake·plans-sync 2건은 plan-lint 접미사-헤더(`# Decisions (설계)`) false-positive 로 판명 → plan-lint prefix 매칭 수정, plan-hygiene 브랜치). **`/improve` 캡스톤 실행(효과 측정)**: error=0·자산정합 전부 ok·wiki 30=30. 신호 추이 — `doc-drift-index` 07-05 이후 **0**(개선 확인), `early-stop-verify`(10세션)·`doc-drift-readme`(5세션)는 잔존(상당수 doc-only/정리 턴 오탐 = 다음 개선 후보, §1 자동수정 안 함). **전 workstream(A~M·E) 완료 → umbrella done.**

# Next
(없음 — 프로그램 종결. 잔여 개선 후보: hook 이 doc-only/정리 턴에 과발동하는 오탐 완화 — 필요 시 별도 `/wt`→dlc.)
- (2026-07-04 스코프 추가 3건 — 각 plan 에 상세: review-intake ← /c 자동 진행(B, 예외 5종) / doc-slim ← wt SKILL codegraph staleness 정확화 / ledger-fix ← main-edit 가드 ③(ask+신호). 사용자 승인 완료.)
- (B 완료: PR #71 머지 3386ec7·CI 통과·main ff-pull. plan 은 main plans/2026-07-04-asset-cleanup 로 이동, status done. defer 3건은 doc-slim plan 에 인계.)
- (C 계획 완료 2026-07-04: plans/2026-07-04-doc-slim/doc-slim-plan.md — 4대 타깃 70.6KB→목표 −30%+, 규칙 손실 0 게이트, 편집 전략·순서 상세. 구현 미착수 — opus 세션 몫.)
- (A 완료: PR #70 머지 33ec7e7·CI 통과·main ff-pull — 신호 수집 hook 라이브. plan 은 main plans/2026-07-02-improve-loop 로 이동, status done.)
- (B 구현 완료 2026-07-04: worktree asset-cleanup, 커밋 0b6d37e, +53/−394. code-simplifier→simplify 체크(메인 직접, 모든 spoke read-only)·local-review 제거·codex 블록 절대경로 참조화·model inherit. plan-review CONDITIONAL 반영 + code-review Major 1건 fix. push/PR 대기.)

# Merge Order (2026-07-14 확정 — 파일 겹침 기반)
**규칙**: 같은 파일을 편집하는 브랜치는 순차 머지 — 앞 브랜치 머지 후 다음을 **최신 main 위로 rebase**(각 브랜치가 stale=doc-slim 슬림화 이전이면 그 rebase 에서 CLAUDE·dlc SKILL 슬림 충돌을 "슬림 유지 + 기능 유지"로 해소). README 는 거의 모두 겹치나 기계적 rebase 라 순서를 강제하지 않는다 — 실질 순서는 skill/script 겹침이 정한다. 겹침은 `merge-base..branch`(순수 변경) 기준(stale 브랜치의 `main..branch` 는 슬림 되돌림이 섞여 부정확).

**review-intake: 이미 머지됨 (PR #75, 2026-07-14 확인) — 목록에서 제외.**

**~~현재 ready~~ — ✅ 둘 다 머지 완료 (2026-07-15):**
1. ~~**ledger-fix**~~ → **#77 머지·정리 완료**.
2. ~~**worktree-cleanup-flow**~~ → 계열 작업 **#76 (cleanup-rule) 머지·정리 완료** (worktree 정리 자동화 + CLAUDE §8 능동정리 규약). 브랜치/worktree 소멸 확인.

**이후 계획 브랜치 (전부 ahead=0 빈 스캐폴드 — 구현 후 머지, dlc/e SKILL 체인이라 순차):**
3. **finish-recap** (CLAUDE·dlc Report·e SKILL) — cleanup-flow 뒤(dlc·e SKILL 겹침).
4. **unknowns-pass** (dlc 명확화·router·wiki) — finish-recap 뒤(dlc SKILL 겹침).
5. **main-autopull** (install-hooks·pre-commit·e SKILL) — 체인 뒤(e SKILL 겹침).
6. **loop-ops** (dlc-signal·lint.yml·settings·session-brief·usage-count) — ledger-fix 뒤(dlc-signal·lint.yml 겹침).
7. **plans-sync** (CLAUDE·evidence-ledger·pre-commit·e/wt SKILL) — **최후**(거의 모든 브랜치와 겹침, 기존 결정 유지). tracked-plan 마이그레이션이 전체 plan 을 만지므로 맨 뒤.

**~~즉시 실행~~ ✅ 완료**: ledger-fix(#77) → worktree-cleanup-flow 계열(#76) 머지·정리 완료 (다른 세션이 §8 자동정리 규약대로 처리). 다음은 3-7번 스캐폴드 브랜치의 **구현**(머지 파이프라인 아님).

# Decisions
- **loop 자율성**: 수집·분석 자동 + 수정은 사용자 승인 후 wt→dlc (사용자 선택, 2026-07-02). 근거: ACE 계열 연구에서 "정적 규칙 + 자기진화 정제" 하이브리드가 순수 자동진화보다 우수, 기존 2026-06-19 미채택 결정과도 정합 — 뒤집는 게 아니라 수집 병목만 해소.
- **Windows 자산 유지** (사용자 선택): .ps1 7종·gwl·prompt-gwl.py·README Windows 절은 건드리지 않는다.
- **미사용 자산 처분** (사용자 선택, 실사용 카운트 근거): ① /audit → /improve 로 흡수(단독 skill 제거) ② code-simplifier subagent 제거 → dlc 13단계 내장 체크리스트로 축소 ③ commands/local-review 제거(per-repo hook 의존·글로벌 미사용, 빌트인 /code-review 로 충분).
- **모델 전략**: opus 단일 유지 + agents frontmatter `model: opus` 제거(세션 상속화 — 모델 세대 교체 시 수정 지점 0). settings.json 의 `claude-fable-5[1m]` 은 사용자 /model 영역 — Fable 상실 시점에 수동 교체(에이전트가 건드리지 않음).
- **Opus 대비 방향**: fablize 통제 실험상 닫힌 작업(코드·로직·빌드)에서 Opus 4.8 ≈ Fable 5, 전이 가능 규율 5종은 이 repo 가 이미 구현 완료. 남은 것은 prose→기계 강제 이관 + 독립 관점 수 보완이지 새 규율 추가가 아님.

# Key Files
- skills/dlc/SKILL.md — loop 연계 지점(Workflow Findings·self-diagnosis)·13단계 체크리스트화 대상
- skills/audit/SKILL.md, skills/audit/audit.sh — /improve 로 흡수될 원본
- scripts/dlc-ledger.js·dlc-early-stop.js·dlc-evidence-ledger.js·dlc-task-router.js — 신호 수집 hook 이 얹힐 기존 체인(per-session tmp 장부 → cross-session 누적 추가)
- agents/code-reviewer.md·plan-reviewer.md — codex 블록 중복 제거(docs/codex-review.md 참조화) 대상
- agents/code-simplifier.md, commands/local-review.md — 제거 대상
- agents/*.md — `model: opus` 상속화 대상
- wiki/pages/decision/self-diagnosis-and-improvement-status.md·workflow-failures.md — loop 채택 갱신 대상
- CLAUDE.md §5·§10·§11, README.md — 위 변경들의 문서 동기화 표면 (acceptance)

# Blockers
(없음)

# Workflow Findings
- [2026-07-04, 사용자 지적 트리거] 다중 세션 additive plan 편집 → 참조 무결성 파손(`Acceptance ⑤⑥` 참조만 있고 항목 부재 등 4건) — 기계 검증 부재가 원인. 재발 조건: 스코프 추가·상태 변화를 여러 세션이 시간차 편집할 때마다. 수정 후보: Workstream E(plan-lint). 횟수 4(단일 세션 내 동일 패턴). wiki workflow-failures 누적은 E 작업 브랜치에서.
- [2026-07-06, /e 중 발견·수정] **worktree 4개가 doc-slim 내부에 중첩 생성**. 3 Whys: ① `git worktree add` 를 **상대경로**로 호출 ② 그 시점 셸 cwd 가 이전 codegraph 백그라운드 `cd .../doc-slim` 로 **누출**돼 있었음 ③ 백그라운드 `cd` 가 포그라운드 셸 cwd 에 영향을 줄 수 있는데 이를 가정 안 함. **근본원인**: worktree 생성이 cwd 에 의존(상대경로). **수정**: wt 생성은 **항상 절대경로**로. 후보 반영처: skills/wt/SKILL.md(§4 생성 절 — 절대경로 명시), 이번엔 즉시 제거·재생성으로 복구. 횟수 1.
- [2026-07-06, /e 중 발견] **H(wt-cleanup-auto) 를 worktree-cleanup-flow 존재 모른 채 중복 생성**. 3 Whys: ① 새 worktree 만들기 전 기존 plan/worktree 미확인 ② plan 이 **worktree-local·gitignored** 라 다른 세션의 진행 중 plan 이 이 세션에 안 보였음 ③ 그래서 같은 주제가 두 번 착수됨. **근본원인 = plans-sync(I) 가 풀려는 바로 그 문제** — 이 사건이 I 의 필요성을 실증. 수정: H 폐기 + I 우선순위 근거 강화.

# Deferred
- **[2회 반복 — 수정 승인됨(2026-07-04), opus 세션 백로그: doc-slim 다음 순위] evidence-ledger 오탐 2종**: ① cross-worktree 절대경로(main plans/·memory)에서 check-ignore 실패 → changed 오탐(2026-07-03·07-04 각 1회) ② 스크립트 래핑 검증(`bash /tmp/*-verify.sh`) 을 VERIFY 정규식이 미인식 → false negative(07-04). 수정 후보: scripts/dlc-evidence-ledger.js (check-ignore 를 파일 경로 기준 repo 에서 실행 + VERIFY 에 검증성 스크립트 패턴). medium. 신호는 telemetry 에 자동 누적 중.
- CLAUDE.md↔SKILL.md↔README 3중 기술 슬림화(단일 소스 지정) — 별도 workstream C (위험도 높아 loop 구축 뒤로).
- rtk hook 이 다중 인자 `cat`(✅재현: `/usr/bin/read` 오류)·`rg`(⚠️exit 2, 원인 미확정) 를 깨뜨린 현상 — 재현 확정 후 workflow-failures.md 기록 검토. medium. hooks/rtk-rewrite.sh.
- worktree `audit-to-selfcheck` 잔존(머지 완료·clean·behind 4) — `/wt rm audit-to-selfcheck` 로 정리. low.
- dlc-task-router 정규식 라우팅 → 신형 prompt/agent hook 타입으로 대체 검토 — 공식 문서 재확인 필요(⚠️미검증). low.
- researcher 보강용 Context7 MCP(라이브러리 문서 RAG) 도입 검토 — vendor 유지 서버 한정 원칙. low.
- 확정 외부 사실(Sonnet 5 출시·가격 프로모, Fable suspend→redeploy·한도, ACE 패턴, MCP 2026 권고) `/wiki ingest` 후보.

# Workstreams (순서 제안)
- **F~I (2026-07-05 등록, worktree+plan 준비 완료 — opus 구현 대기)**: **F. finish-recap**(마무리 recap+선택지 규약화, hook 대응 결론 1줄 — 착수: doc-slim 머지 후) / **G. main-autopull**(main 체크아웃·복귀 시 자동 최신화 — post-checkout hook ⓐ는 즉시 가능, e SKILL ⓑ는 doc-slim 후. 현행 SessionStart pull 은 정상 작동 확인됨) / **H. wt-cleanup-auto**(정리 누락 3 Whys: 트리거가 머지 시점과 어긋남+상시 승인 미영속 — 검사 통과 시 자동 삭제로 전환, 착수: doc-slim 후) / **I. plans-sync**(plan tracked 화 권장안 A — 착수: **다른 브랜치 전부 머지 후 마지막**, 방안 사용자 확인 1회). 즉시 완화 반영: memory `report-conclusion-first` 주입 시작.
- **K+L+M → worktree `loop-ops` 로 통합 (2026-07-12, plan 내장 — 즉시 착수 가능·파일 겹침 0)**: **K** 머지 대기 리마인더(session-brief.js, 실측 3건×5일 방치) / **L** improve 주기 nudge(failure 신호 임계 시 세션 브리프 1줄) / **M** improve 광역 모드(`--deep`: 주입 크기·실사용 카운트·MCP 인벤토리·researcher 신기술 — 7/2 전수 감사의 절차화. 사용자 질문 "improve 가 전부 커버하나?" → 커버 밖 6영역 확인에서 도출). 상세는 plans/2026-07-12-loop-ops/.
- **J. unknowns-pass (2026-07-07 등록)**: Thariq unknowns 아티클 기법 반영 — blind-spot pass·질문 우선순위(설계를 바꿀 답 먼저)·프로토타입-우선(router 확장) + dlc dead memory ref 정리 + 아티클 wiki ingest. worktree `unknowns-pass`(blocked — cleanup-flow·finish-recap 머지 후, dlc SKILL 겹침). 퀴즈 기법은 finish-recap 스코프로 흡수. 이미 커버 확인: interviews=명확화 게이트·deviations=§10 동기화·references=프롬프트 기법.
- **E. plan-lint — 문서 참조 무결성 기계화 (2026-07-04 등록, 근본원인 분석 기반)**: 증상 = "꼼꼼히 봐달라" 할 때마다 결함 발견(이번 세션 4건: plan `Acceptance ⑤⑥` 참조 끊김·title 스코프 불일치·codex 블록 중복·wiki 과소서술 — 전부 동일 패턴). 3 Whys: ① additive 편집(특히 다중 세션 시간차 편집)이 참조 무결성을 깨뜨림 ② plan/문서 편집은 검증 게이트 밖(gitignored — hook 오탐만, 리뷰어·improve.sh 미커버) ③ plan 이 핸드오프 메모→다중 모델 공유 스펙으로 승격됐는데 검증이 미추격. **근본원인: 문서 참조 무결성이 모델 주의력에만 의존.** 개선안: `scripts/plan-lint.js`(순수 판정+테스트 — frontmatter 필수키·status 값·6섹션 헤더·**내부 참조 대응**(본문의 "Acceptance N/#섹션" 참조 ↔ 실제 항목 수)·title↔Goal 키워드 정합은 LLM 몫으로 분리) + 호출 3지점: /c 2단계(sync 진단에 plan 무결성 행), /e 3단계(기록 직후), /improve 1단계(improve.sh 에서 active plan 대상). **착수 조건: 3개 worktree 머지 후**(c SKILL=review-intake·e SKILL=doc-slim·improve 는 free — 지금 얹으면 3브랜치 충돌). Fable 계획 세션에서 상세 plan 작성 후 opus 구현.
- **D. PR 리뷰 intake (Loop Engineering 4단계 갭, 2026-07-04 등록)**: `/c` 가 plan 이어받기 시 해당 브랜치 PR 의 사용자 리뷰 코멘트를 `gh pr view/reviews` 로 읽어 ① 미해결 지적을 `# Next`/fix loop 입력으로 ② 작업방식 교정성 코멘트를 feedback memory 판정으로 넘긴다. 대상: skills/c/SKILL.md (+README 동기화). Loop 1·2·3·5 는 기존/A 로 충족 확인(2026-07-04 점검).
- **A. self-improve loop 구축** (最우선): 신호 수집 hook + /improve skill(+audit 흡수) + /e 회고 연계 + 효과 측정(신호 발동 추이). 완료 시 self-diagnosis-and-improvement-status.md 갱신.
- **B. 자산 정리 묶음**: codex 블록 참조화 / local-review 제거 / code-simplifier 체크리스트화 / agents model 상속화 / README·CLAUDE.md §5 동기화. (A 와 독립 — 병행 가능하나 파일 겹침 주의: dlc SKILL.md 는 A·B 둘 다 건드림 → 순차 권장)
- **C. 문서 슬림화** ✅ 완료(#73 머지 2026-07-05, 커밋 6b81a1a): 3중 기술 해소 — A·B 머지 후. 규칙 손실 0·감소 11.2%. plan=plans/2026-07-04-doc-slim(done). 후속 wiki ingest(압축 상한 교훈)는 2026-07-14 처리.
