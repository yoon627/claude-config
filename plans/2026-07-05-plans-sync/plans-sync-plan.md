---
title: plans-sync — plan 을 환경 간 동기화 (local 전용 → 다른 머신에서 이어가기)
status: done
started: 2026-07-05
updated: 2026-07-16
---

# Goal
`plans/` 가 gitignored·머신 로컬이라 다른 환경(다른 머신·원격 세션)에서 작업을 이어갈 때 plan 핸드오프가 끊기는 문제 해결(2026-07-05 사용자 지시). §10 "plan = 단일 진실 소스" 가 머신 경계를 넘도록.

# Progress
- 2026-07-05: Fable 계획 세션 — 방안 비교·권장안 확정. 구현은 opus. **방안 선택은 plan-reviewer 후 사용자 확인 1회 필요(아래 Decisions — 트레이드오프가 실질적).**
- 2026-07-06 (/e): **실증 사례 확보** — 이 세션이 `wt-cleanup-auto` 를 다른 세션의 `worktree-cleanup-flow` 존재를 모른 채 중복 생성. 근본 원인이 "plan 이 worktree-local·gitignored 라 타 세션 진행 plan 이 안 보임" = 정확히 이 plan 이 푸는 문제. 우선순위 근거 강화(비용 실측: 중복 작업 1건 발생). umbrella Workflow Findings 에 기록됨.
- 2026-07-16 (구현 착수): **사용자 방안 A 확정** — 코어 구현 시작(dlc). 마이그레이션·전수 secret 스캔은 loop-ops·unknowns-pass 머지 후. 방안 선택 게이트 해소.
- 2026-07-16 (마이그레이션·done): 전체 worktree+main 의 plan 11개 전수 secret 스캔 → **0 히트(clean)**. main 의 미tracked plan 10개 + 이 plan 1개를 `plans-migrate` 브랜치로 모아 tracked 커밋(PR). 상위 workflow-loopify 는 E(plan-lint) 남아 done 아님 — plans-sync(I) 만 종결. **status: done.**
- 2026-07-16 (install-hooks): `./scripts/install-hooks.sh`(main 에서) 실행 → 공용 `.git/hooks` 에 pre-commit·pre-push(+머지된 main-autopull 의 post-checkout) 설치. **end-to-end 스모크 검증**: 설치된 pre-commit 훅이 plans/*.md 의 가짜 anthropic 토큰을 실제 차단(exit1, BLOCKED), clean plan 은 통과(오탐 없음), 흔적 정리. 보안 완화 활성화됨.
- 2026-07-16 (rebase·merge): origin/main 이 8커밋 전진(→888ec8e, loop-ops·unknowns-pass·main-autopull 머지)해 origin/main 에 rebase(무충돌, README·skills/e 자동병합) → 재검증 4스위트 통과 → force-push → **PR #83 rebase-merge 완료**(main=202c4f5). isPlan 이 main 에 반영돼 dlc-early-stop plan-편집 오탐도 소멸.
- 2026-07-16 (커밋·PR): 커밋 00c0035(11파일, plans/ 미포함) → push → PR #83 OPEN. tmp 메시지 파일 정리.
- 2026-07-16 (코어 구현 완료): 10파일 변경. ① `.gitignore` `!/plans/` (check-ignore not-ignored 검증, belt-and-suspenders `.bak`·settings.local 유지). ② pre-commit-check.sh 리팩터(scan_tokens/scan_keys 함수화 → settings.json + staged `plans/*.md` 양쪽 스캔, 패턴 +DB URL creds·Bearer·quoted-secret) + 신규 `pre-commit-check.test.sh`(fixture 10/10). ③ pre-commit-check.ps1 동일 미러(pwsh 미설치 → 수동검증 대상). ④ dlc-evidence-ledger.js `isPlan()` 추가 — gitignore 무관 plans 제외(TDD, 29/29). ⑤ 문서: guard-worktree-edit.js 주석·CLAUDE.md §8·§10·skills c/e·README. 전체 테스트 통과(evidence-ledger 29·pre-commit 10·guard ALL·dlc-signal 20). wt/SKILL.md 는 plans 언급 없어 변경 불요. **install-hooks 미설치 확인 — 보안 완화 활성화하려면 실행 필요(Report 권고).**
- 2026-07-16 (/c 진단): 브랜치 8 커밋 behind·0 ahead(구현 미착수) → origin/main(40ebf96)으로 fast-forward(무손실). **선행 의존 해소 확인**: doc-slim(#78 머지)·ledger-fix(`5641f7e` evidence-ledger 오탐 2종+main-edit 가드, 머지) 완료 → Key Files 의 e/wt SKILL·evidence-ledger 상호작용 검토 가능 상태. **시퀀싱**: 아직 열린 브랜치 loop-ops(ahead 1)·unknowns-pass(ahead 1) 2개 — 마이그레이션(각 worktree plan 이동)은 이 둘 머지 후 권장이나, 코어 구현(.gitignore whitelist·pre-commit-check·문서)은 파일 겹침 없어 선행 가능. A/B 최종 선택 여전히 미결(사용자 게이트).

# Next
**이 plan 완료(done)** — 코어 머지(#83) + install-hooks 검증 + 마이그레이션(전수 secret 스캔 clean → 11 plan tracked 커밋). 
- 상위 plan(workflow-loopify)은 **done 아님** — E(plan-lint) workstream 이 유일 잔존(그 plan Progress 에 I 완료 기록). plans-sync 는 그 하위 I 로서 종결.
- 후속 정리: 이 migration 브랜치 머지 후 plans-sync·plans-migrate worktree/브랜치 정리.

# Decisions — 방안 비교 (권장: A)
- **A (권장) — plans/ 를 tracked 로 전환 + 위치 유지**: `.gitignore` whitelist 에 `!/plans/` 추가, plan 을 브랜치와 함께 커밋·push. 장점: §10 워크플로우 무변경(경로 동일)·이력 자동·환경 간 push/pull 로 동기화·worktree 삭제 시 plan 소실 문제도 소멸(tracked 라 경고됨)·e/c 의 "양쪽 plans 탐색" 로직 그대로. 단점: ① plan 이 PR diff 에 섞임 → PR 노이즈(수용 가능 — plan 도 리뷰 가치 있음, 또는 머지 전 squash 지시) ② 민감정보 유입 위험 → 완화: pre-commit-check 의 토큰 패턴 검사를 plans/*.md 로 확장 + §8 원문 출력 금지 기존 규칙 ③ 과거 done plan 누적 → `plans/archive/` 규약(또는 done 은 삭제 — git 이 기억).
- **B — 별도 private repo/브랜치 (`plans` orphan 브랜치 또는 전용 repo)**: 장점: PR 노이즈 0. 단점: push/pull 을 별도로 해야 해 §10 "즉시 동기화" 규약과 마찰(동기화 자체를 잊는 새 실패 모드 — 이번 문제의 재생산), c/e/wt 탐색 로직 수정 필요. **비권장.**
- **C — 외부 저장(gist/클라우드)**: 인증·도구 의존 추가, git 워크플로우 밖 — **비권장.**
- **A 채택 시 부수 정리**: ① guard-worktree-edit 의 plans 예외(main plans 편집 allow)는 유지하되 tracked 화 이후엔 "main 직접 커밋 금지"와의 관계 정리 — plan 은 작업 브랜치에서 커밋되는 게 기본, main plans/ 의 상위 plan(workflow-loopify 류)은 **별도 정리 브랜치에서 커밋** 또는 main-edit 가드(ledger-fix ③)의 ask 허용 경로로. ② evidence-ledger: tracked plan 편집이 changed=true 가 되는 건 **정당**(문서도 검증 대상 표면) — 단 ledger-fix 의 "gitignored plans 오탐" 수정과 상호작용 확인 필수(tracked 전환 후엔 check-ignore 가 not-ignored 를 반환하는 게 맞음 — 오탐 아님이 됨. doc-drift 처럼 plan 편집을 verified 면제할지 판단). ③ wt 의 .env 복사·e 의 ignored 잔존물 검사에서 plans 항목 제거.
- **마이그레이션**: 기존 각 worktree 의 로컬 plan 을 해당 브랜치에 커밋, main 의 상위 plan·done plan 은 정리 브랜치 1개로 일괄 커밋. raw/개인 메모가 섞였는지 커밋 전 토큰·PII 스캔(§8).

# Key Files
- .gitignore — `!/plans/` 추가(whitelist) / scripts/pre-commit-check.sh(.ps1) — plans 토큰 검사 확장
- skills/e/SKILL.md(잔존물 검사)·skills/wt/SKILL.md(.env 복사 주석) — plans 관련 서술 갱신 (doc-slim 머지 후)
- scripts/dlc-evidence-ledger.js — ledger-fix 머지본과 상호작용 확인(코드 변경은 필요시만)
- CLAUDE.md §10 — "gitignored" 전제 서술 갱신 / README — 동기화

# Blockers
- (해소 2026-07-16) 방안 최종 선택 → A 확정. doc-slim·ledger-fix 의존도 해소.
- 시퀀싱: 마이그레이션 단계는 loop-ops·unknowns-pass(현재 열림) 머지 후. 코어 구현은 선행 진행 중(파일 겹침 없음).

# Acceptance
1. ✅(메커니즘) `.gitignore` `!/plans/` 후 `git check-ignore plans/…-plan.md` = not-ignored(exit1), belt-and-suspenders(`.bak`·settings.local) 유지 실측. "타 환경 clone 에서 보임"은 실제 commit+push=마이그레이션(⏸ defer)이나 tracked 메커니즘은 검증됨.
2. ✅ pre-commit-check 가 staged `plans/*.md` 토큰 차단 — `pre-commit-check.test.sh` 10/10(anthropic·DB URL·bearer·quoted-secret block, clean·prose(값없음) allow, settings.json 미스테이징에도 plans 스캔).
3. ✅ c/e 문서 tracked 반영 + evidence-ledger 29/29(ledger-fix 충돌 없음 — isPlan 은 isIgnored 와 독립 게이트). guard-worktree-edit ALL·dlc-signal 20 비회귀. wt 는 plans 언급 없어 불요.
4. ⏸ defer — 기존 plan 마이그레이션(각 브랜치 커밋 + 전수 secret 스캔)은 loop-ops·unknowns-pass 머지 후. §10·§8·README 서술 갱신은 이번에 **완료**.
5. ⏸ defer — 코어만 완료. 마이그레이션 후 상위 plan(workflow-loopify) done 표시.

# Deferred
- **마이그레이션 + 전수 secret 스캔** (loop-ops·unknowns-pass 머지 후): 각 worktree 로컬 plan 을 브랜치에 커밋, main 상위/done plan 일괄 정리 커밋, 커밋 전 기존 plan 전체 secret 수동 스캔(git 히스토리 진입 시 제거 난이도 高).
- **install-hooks 미설치** (심각도 中): pre-commit/pre-push 가 이 clone `.git/hooks` 에 미설치(samples 뿐) → 보안 완화가 opt-in. `./scripts/install-hooks.sh` 실행 필요(머신-로컬, repo diff 아님). Report 권고.
- **`plans/**` .md-한정 whitelist** (하드닝 옵션, 심각도 低): 현재 `!/plans/` 는 plans/ 전체 tracked. plans/ 내 비-.md 산출물에 secret 파일이 들어갈 극단 케이스 대비 `.md` 만 화이트리스트하는 방식 고려 가능(현재는 belt-and-suspenders + pre-commit-check + §8 로 커버).

# Review Disposition
- 2026-07-16 plan-reviewer(메인 직접 수행 — plan-reviewer subagent 가 주간 API 한도 도달로 중단, 동일 관점 직접 점검). **결론: 방안 A 타당·권장 유지.** 근거 실측:
  - `.gitignore` whitelist(`/*`+`!/dir/`)라 `!/plans/` 로 tracked 작동 확인(fix 불요, 구현 시 반영).
  - **[fix]** pre-commit-check 은 settings.json 전용 → plans/*.md 확장 = 비트리비얼 개조 필요. 패턴이 구조화 토큰만 커버(일반 password·DB URL creds·bearer·PII 누락) → 패턴 보강.
  - **[fix]** install-hooks.sh 로 설치하는 pre-commit/pre-push 가 이 clone 에 미설치(`.git/hooks` = samples). 보안 완화가 opt-in hook 의존이라 소프트 → 마이그레이션 전 기존 plan **전수 secret 수동 스캔**을 acceptance 로 승격.
  - **[fix]** dlc-evidence-ledger.js:45,95 가 "plans gitignored" 전제로 plan 편집을 changed 제외 → tracked 전환 시 게이트 반전. 코드 처리 필요(문서만 아님).
  - **[fix]** guard-worktree-edit.js:105 plans 예외는 유지하되 근거 주석 갱신.
  - rollback: secret 히스토리 진입 시 filter-repo/force-push — 사전 스캔이 실질 방어선.
  - B 비권장 근거(동기화 망각 재발) 재확인 — 타당.
- 2026-07-16 처분: 위 [fix] 4건 모두 **fix 적용** — pre-commit-check plans 확장+패턴보강(구현·테스트), isPlan 게이트(구현·테스트), guard 주석 갱신, 전수 secret 스캔은 마이그레이션과 함께 `# Deferred` 로 이관(코어 범위 밖). install-hooks 미설치는 `# Deferred`(머신-로컬 opt-in). 구현 결정: **secret 패턴은 구조화 시크릿만**(일반 PII/prose 정규식은 오탐 과다로 제외 — §8 규약 + 마이그레이션 전 수동 스캔으로 보완), **`isPlan` 은 절대경로 `plans/` 세그먼트 매칭**(repo 가 `/plans/` 하위에 중첩되지 않는다는 전제 — ~/.claude 는 해당 없음).

# Workflow Findings
- 2026-07-16: dlc-early-stop 오탐 1회 — 이 브랜치가 `!/plans/` 로 plans/ 를 un-ignore 하자, main 의 (isPlan 미적용) evidence-ledger 가 plan 파일 편집을 changed=true·verified=false 로 집계해 Stop 경고 발생. **정확히 이 plan(isPlan 게이트, PR #83)이 고치는 상호작용의 실증**. · 재발조건: PR #83 머지 전까지 이 브랜치에서 plan 편집 시. · 수정 위치: scripts/dlc-evidence-ledger.js isPlan (이 PR 에 포함) — 머지되면 소멸(transient). · 발생 1회.
