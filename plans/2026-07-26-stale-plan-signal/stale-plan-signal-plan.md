---
title: stale-plan-signal — 머지됐는데 닫히지 않은 plan 을 세션 브리프로 알림
status: in_progress
started: 2026-07-26
updated: 2026-07-26
---

# Goal
`session-brief.js` 에 세 번째 신호 `stalePlanLine()` 을 추가한다 — `status: in_progress` 인데 (a) slug 에 매칭되는 로컬 브랜치가 없고 (b) `updated` 가 임계일 이상 경과한 plan 을 세션 시작 시 1줄로 알린다. 머지 시점에 plan 을 닫을 주체가 없어 `in_progress` 로 새는 문제(2026-07-26 에 4건 소급 정리)의 재발 감지.

# Progress
- 2026-07-26: 착수. Explore 완료 — `session-brief.js:31 mergePendingLine()` 이 반대 방향(미머지 브랜치)만 보고 "브랜치는 사라졌는데 plan 이 열린" 축은 아무도 안 봄을 확인. `plan-lint.js` 는 순수 구조 검사(git 무관)라 이 판정을 넣을 자리가 아님. 테스트는 임시 git repo + CLI 실행 통합 스타일(`initRepo`/`commit`/`run`).

- 2026-07-26: plan-review(+codex medium 병행) = **CONDITIONAL**. 실증 결함 6건 반영해 설계 v2 로 수정(아래 Decisions v2). 지적이 명확·반영 방향 확정적이라 plan-reviewer 재실행 생략, 구현 후 code-reviewer 가 최종 점검.

- 2026-07-26: TDD Red(ⓜ 의도된 실패) → 구현(`stalePlanLine` + `collect()` 격리 + 헤더 주석) → Green **32건** → README 3곳 동기화 → code-review(+codex high 병행) = **REQUEST CHANGES**(CONFIRMED Major 5) → fix loop 1회 전건 반영 → **38건 통과**.
  - Major 처분: ①§10 정본 템플릿의 `status: in_progress  # ...` 인라인 주석을 값으로 오인해 **영구 무음**(fix — 주석 제거 후 비교, 회귀 M-1) ②CRLF 미정규화로 Windows 체크아웃 시 M 전체 사망(fix — `readHead` 에서 BOM·CRLF 정규화, `plan-lint.js:93` 선례 누락분, 회귀 M-2) ③`MAX_PLANS` cap 이 `isDirectory()` 필터보다 앞이라 상한 도달 시 **최신 plan 만 잘림**(fix — 필터 후 slice, 회귀 M-3) ④ⓧ 격리 테스트 vacuous — 그 경로는 내부 try 가 흡수해 `collect` catch 미도달(fix — 테스트명·주석을 실제 검증 내용으로 정정, Acceptance 문구도 하향) ⑤squash-merge 브랜치는 ahead>0 이라 D3 블라인드 잔존(**wontfix** — patch-id 로는 N→1 squash 를 감지 못하고 PR 조회는 동기 hook 에 부적합. 미탐이지 오탐이 아니며 그 구간은 K 가 계속 알린다 → README 에 명시 + `# Deferred`).
  - Minor 처분: DST 전환 off-by-one(fix — UTC 자정 차분) · 존재하지 않는 날짜 롤오버 오보고 + 죽은 NaN 가드(fix — 롤오버 검증, 회귀 M-5) · `updated` 불량 시 영구 무음(fix — `started` 폴백, 회귀 M-4) · "파일 단위 격리"가 실제로 dir 단위(fix — try 를 파일 루프 안으로) · 브랜치 cap 누락(fix — `MAX_BRANCHES` 적용) · README "다머신 오탐 차단" 이 fetch 된 ref 한정(fix — 문구) · `hasOriginMain=false` 테스트 공백(fix — 회귀 M-6) · plan 문서 모순 3건(fix — 이 커밋).
  - Nit 처분: 테스트 헤더 K+L→K·L·M(fix) · `name==='HEAD'` 죽은 가드 → 실제 short 표기는 `origin`(fix) · 빈 slug 앵커 매칭(fix — 가드) · `SOFF`→`KLOFF` 네이밍 일관(fix) · §6 위반 주석(변경 경위) 제거(fix) · `daysAgo` 자정 경계 flake(**wontfix** — 확률 극소, 방어하려면 프로덕션 코드에 시각 주입 경로를 뚫어야 해서 비용이 크다).

# Next
push → PR(main) → 리뷰·머지. 머지 후 §8(a) 조건 판정해 worktree 정리.

# Decisions
- **위치 = `session-brief.js`** (별도 스크립트·CI·`/improve` 아님). 근거: ① 매 세션 자동 주입되는 유일 경로 ② 동일 성격 신호 2종이 이미 사는 곳 ③ `mergePendingLine` 과 정반대 축이라 나란히 두면 인지적으로 짝 ④ `plan-lint.js` 는 git 상태를 모르는 순수 함수(CI 에서 돌아 git 접근 부적절), `/improve` 는 주기적 호출이라 재발을 늦게 잡는다.
- **판정 3조건 AND (v2)**: ① frontmatter `status: in_progress` ② 매칭 브랜치가 **없음 OR 있어도 `origin/main` 대비 ahead 0(=이미 머지됨)** ③ `updated` 경과 ≥ 임계(기본 **3일**).
  - `status: blocked` 는 **제외** — 의도적으로 막아둔 것이라 "닫히지 않음"이 아니다.
  - **② 확장 이유 (plan-review D3)**: v1 의 "브랜치 없음"만으로는 **목표 시나리오의 절반을 놓친다**. 세션 종료 후 GitHub 에서 머지되면 로컬 브랜치·worktree 가 그대로 남는데, 그 상태에서 K 는 `origin/main..branch` count 0 이라 skip(`session-brief.js:54`) 하고 M 은 "브랜치 존재"로 제외 → **두 신호 모두 눈이 먼다**. ahead 0 판정(K 의 `rev-list --count` 재사용)을 더해 그 구간을 덮는다.
  - 매칭 브랜치가 있고 ahead > 0 이면 제외 — 아직 작업 중이다.
- **브랜치 매칭 = 앵커 매칭 + MAINLINE 제외** (v1 의 양방향 substring 철회, plan-review D2).
  - 규칙: `b === slug` · `b === 'worktree-' + slug` · `b.endsWith('-' + slug)`.
  - **철회 이유(실증)**: free substring 은 항상 존재하는 `main` 브랜치(4자라 최소길이 가드 통과)가 slug 에 `main` 이 든 plan 을 **영구 억제**한다 — `main-autopull`, `gwl-zsh-wt-main` 이 실제 사례. K 가 같은 이유로 `MAINLINE` 을 명시 제외하는 것과 동일 함정(`session-brief.js:21,47`). 무관 브랜치 우연 매칭도 실측됨(`doc-slim` ← `doc-slim-wiki`).
  - `worktree-` prefix 는 `EnterWorktree` 도구가 붙이는 형태라 앵커에 포함(`skills/wt/SKILL.md:3`). `/wt` 는 정확일치 규약이므로 앵커 매칭이 규약과 정합.
- **매칭 대상에 원격 브랜치 포함**(`refs/remotes/origin/*`, MAINLINE·HEAD 제외). 근거: §10 은 멀티머신 핸드오프를 명시 지원하고, 지금도 로컬엔 없고 원격에만 있는 미머지 브랜치가 4개다(`origin/worklog-ticket-union` 등) — 로컬만 보면 다른 머신에서 진행 중인 작업을 오탐한다.
- **임계 기본값 7일 → 3일** (plan-review D4). 근거: 오늘 소급 정리한 4건의 fix 이전 경과일은 10·9·7·**4**일 — 7일 기본값은 `code-reviewer-absorb`(4일)를 못 잡고 경계 케이스(7일)는 실행 시각에 흔들린다. 즉 사람의 수동 발견(4~10일)을 앞서지 못해 신호의 존재 의미가 사라진다. ② 를 "머지 확인"으로 강화해 오탐 위험이 줄었으므로 임계를 낮출 여유가 생겼다.
- **경과일은 달력 일수 차 + 음수 클램프 + 롤오버 거부**. `updated` 는 날짜만이라 시각 성분을 섞으면(`Date.parse('2026-07-26')`=UTC 자정 vs 로컬 현재시각) 오전에 음수가 된다. **양쪽을 `Date.UTC` 자정으로 옮겨 차분한다** — 로컬 자정 간 ms 차분은 DST 전환(23시간 하루)에서 하루 작아지기 때문(code-review 실증: TZ=America/New_York, 3/5→3/9 이 3일로 계산). 미래 날짜는 0, `2026-02-31` 같은 롤오버 값은 거부(`getUTCMonth`/`getUTCDate` 역검증 — 이게 없으면 `new Date(2026,1,31)`=3/3 으로 조용히 넘어가 145일로 오보고).
- **slug 추출은 파일명 기준** (`<slug>-plan.md` → `<slug>`), dir 명 아님. §10 이 "파일명에 slug 가 있어야 `@` 자동완성에서 식별 가능"이라 파일명을 정본으로 본다.
- **frontmatter 파싱은 자체 정규식** — `plan-lint.js` 를 require 하지 않는다. 근거: plan-lint 는 값 추출 API 가 없고(무결성 검사 전용), session-brief 는 fail-open 이 계약이라 외부 모듈 의존을 늘리면 로드 실패 시 신호가 통째로 죽는다(`dlc-signal` 을 optional require 로 감싼 기존 판단과 동일 방향).
- **환경변수**: `CLAUDE_BRIEF_STALE_OFF=1`(해제), `CLAUDE_BRIEF_STALE_DAYS`(임계, 기본 **3** — 위 D4). 기존 2종과 동일 규약.
- **cap 5 + `+N`** — `MERGE_CAP` 과 동일 형식. 오래된 것(경과일 큰 순) 먼저.
- **스캔 계약 명문화 + 3단 실패 격리** (plan-review D5). v1 의 "파싱 실패 → null" 은 granularity 가 틀렸다.
  - 스캔: `readdirSync(withFileTypes)` → `isDirectory()` 인 것만 → 그 안의 `<slug>-plan.md` 만. **근거(실측)**: `plans/giggly-petting-moonbeam.md` 처럼 루트에 디렉토리 아닌 파일이 실재해 디렉토리 가정 시 `ENOTDIR`.
  - 파일 단위 try/catch → 불량 plan 1건이 나머지 유효 stale plan 보고를 막지 않는다.
  - **`main()` 에서 신호별 try/catch 로 상호 격리** — stdout write 가 모든 신호 수집 후 1회(`session-brief.js:124`)라, 격리 없으면 M 의 예외가 이미 계산된 K·L 라인을 통째로 삭제한다(기존 신호 회귀).
- **`MAX_PLANS` 상한(200) + frontmatter 만 부분 read**. 성능 실측은 4.5ms/16파일·108KB 로 비이슈지만 `MAX_BRANCHES`(`session-brief.js:20`)와 대칭을 맞춘다(plans/ 는 done 도 계속 누적). 전역 deadline 은 두지 않는다 — 호스트 kill 은 JS try/catch 로 못 막고 실측 여유가 크다.
- **`CLAUDE_BRIEF_STALE_DAYS` 입력 계약 = 범위 검사**(선례 `Math.max(1, Number(x) || 5)` 는 **채택하지 않음**). 구현 중 발견: 그 관용구는 음수가 truthy 라 `-5` 를 임계 1 로 통과시킨다 → `Number.isFinite(raw) && raw >= 1 ? Math.floor(raw) : 3`. 0·음수·비숫자는 기본값 흡수. (동일 결함이 `improveNudgeLine` 의 `CLAUDE_BRIEF_IMPROVE_MIN` 에도 있으나 이번 변경이 만든 게 아니라 `# Deferred`.)
- **frontmatter 파싱 스코프는 `^---\n...\n---` 블록 내부 한정** — 본문의 `status:`/`updated:` 오탐 차단. `plan-lint.js:98-111` 선례를 미러링(코드 재사용은 아님 — 아래 fail-open 이유).
- **fail-open 유지** — plans/ 부재·파싱 실패·git 실패 전부 `null`(무음). 세션 시작을 막지 않는다.
- **snooze/ack 는 도입하지 않는다**(이번 스코프). L 은 `last-improve` 마커로 침묵 가능하지만 M 은 plan 을 닫기 전까지 매 세션 반복된다 — 조치 경로가 싸지 않다(main tracked 편집은 `guard-worktree-edit` ask, main push 는 deny → 브랜치+PR 필요). 알림 피로가 실제로 관측되면 그때 도입하고, 지금은 `# Deferred` 에 남긴다.
- **이 신호는 예방이 아니라 보조 탐지다.** 근본 원인(머지가 세션 밖에서 일어나 plan 을 닫을 주체가 없음 — `/e` 는 `done` 전환을 확정 완료 신호 + 사용자 확인으로 제한, `skills/e/SKILL.md:37-40`)은 손대지 않고 **탐지 지연 3일을 수용**한다. 머지 후 정리 정책 자체는 `2026-07-21-auto-cleanup-after-merge` plan(PR #102)이 소유 — 정책 변경은 그쪽, 탐지는 이쪽.
- **스코프는 `~/.claude` 한정** (`session-brief.js:5` 계약). 다른 repo 의 `.claude/plans/` 누락은 커버하지 않는다.
- **rollback**: (a) 즉시 완화 = `CLAUDE_BRIEF_STALE_OFF=1`(kill-switch, 코드 되돌림 아님) → (b) 코드 복귀 = 해당 커밋 revert + `node scripts/session-brief.js` 직접 실행으로 K·L 정상 복귀 확인. 읽기 전용·telemetry emit 없음이라 상태 잔여물 없음.

# Key Files
- `scripts/session-brief.js` — `stalePlanLine()` 신규 + `main()` 신호별 try/catch 격리 + 헤더 주석(2~4행) "두 종"→"세 종"(주 변경)
- `scripts/session-brief.test.js` — M 축 테스트 + `writePlan` 헬퍼 신규 + **기존 L 테스트 6곳(135·141·148·174·179·189) env 격리 수정**(D1)
- `README.md:359·400·564` — 신호 3종 반영: 스크립트 상세 열거 / "브리프 1~2줄"+kill-switch 목록 / 트리 주석 (§3 문서 동기화, acceptance 항목)

# Acceptance
- [x] in_progress + 매칭 브랜치 없음 + 경과 ≥ 임계 → `닫히지 않은 plan: <slug>(<N>d)` 1줄 (관찰: 테스트 통과)
- [x] **매칭 브랜치가 있고 ahead > 0 이면 제외** (관찰: 테스트 — `<slug>`·`worktree-<slug>`·`*-<slug>` 세 앵커 형태 각각)
- [x] **매칭 브랜치가 있어도 ahead 0(머지됨)이면 검출** — D3 이중 블라인드 구간 (관찰: 테스트)
- [x] **slug 에 `main` 이 포함된 plan 이 `main` 브랜치에 억제되지 않음** — D2 영구 누락 (관찰: 테스트, slug `main-autopull` 형태)
- [x] **원격 전용 브랜치(`origin/<slug>`)가 매칭돼 제외됨** — 다머신 오탐 (관찰: 테스트)
- [x] `status: done`/`blocked` 는 제외 (관찰: 테스트)
- [x] 경과 < 임계면 제외, `CLAUDE_BRIEF_STALE_DAYS` 로 조정 가능 + 0·음수·비숫자는 기본값 흡수 (관찰: 테스트)
- [x] `CLAUDE_BRIEF_STALE_OFF=1` 로 해제, `CLAUDE_SESSION_BRIEF_OFF=1` 이 우선 (관찰: 테스트)
- [x] plans/ 부재·frontmatter 불량·**루트의 디렉토리 아닌 파일(ENOTDIR)** → 무음, **exit 0**(관찰: 테스트 — `run()` 이 status 를 은닉하므로 `spawnSync` 로 별도 단언)
- [x] **불량 plan 1건이 있어도 유효 stale plan 은 계속 보고됨** (파일 단위 격리, 관찰: 테스트)
- [x] **M 이 스캔 불가여도 K 라인은 보존됨** (ⓧ. 원안 "예외를 던져도"는 **관측 불가라 하향** — `stalePlanLine` 은 모든 throw 경로가 내부 try 안이라 total 함수이고, `main()` 의 `collect` catch 는 미래 회귀 대비 방어물이라 CLI 로는 도달시킬 수 없다. 그 사실을 테스트 이름·주석에 명시)
- [x] cap 5 초과 시 `+N` 표기 (ⓨ)
- [x] 기존 18 test(K·L 축) 전건 통과 — 회귀 없음 (`node scripts/session-brief.test.js` = CI 와 동일 명령, `.github/workflows/lint.yml:51`)
- [x] **실증**: 소급 정리 4건과 동형 fixture(10·9·7·4일)가 기본 임계 3 으로 **전건 검출** (ⓩ)
- [x] README 3곳(359·400·564) + `session-brief.js` 헤더 주석이 신호 3종으로 갱신
- [x] **리뷰 반영 회귀**: §10 템플릿 인라인 주석(M-1) · CRLF(M-2) · cap 순서(M-3) · `updated`→`started` 폴백(M-4) · 날짜 롤오버 거부(M-5) · `origin/main` 부재 폴백(M-6)

# Review Disposition
- Major①②③④ → `fix` (전건 반영 + 회귀 테스트 M-1~M-6)
- Major⑤ squash-merge 블라인드 → `wontfix` (감지 수단 없음 — squash 는 N커밋→1커밋이라 patch-id 비교 불가, PR 조회는 네트워크라 동기 hook 부적합. 미탐이며 K 가 그 구간을 커버 → README 명시로 대체)
- Minor 8건 → 전부 `fix`
- Nit `daysAgo` 자정 flake → `wontfix` (확률 극소 vs 프로덕션 코드에 시각 주입 경로 추가 비용)
- Nit 짧은 slug(`lint`·`e`) 앵커 오억제 → `wontfix` (현 slug 관행 3단어 이상에서 미발생. 빈 slug 만 가드)

# Deferred
- **`CLAUDE_BRIEF_IMPROVE_MIN` 도 음수 truthy 결함**(범위 밖·기존 코드): `session-brief.js` 의 `Math.max(1, Number(x) || 5)` 는 `-5` 를 임계 1 로 통과시킨다. M 은 범위 검사로 짰지만 L 은 그대로 — 이번 변경이 만든 결함이 아니라 §3-4 대로 미수정. 심각도 낮음(음수를 넣을 이유가 없다), 수정 비용 1줄.
- **squash-merge + 브랜치 잔존 구간은 M 미탐** (Major⑤ wontfix 의 잔여 리스크): 그 구간은 K 가 "미머지 로컬"로 알리므로 무신호는 아니지만, K 입장에선 이미 머지된 브랜치를 미머지로 보고하는 오탐이다. K 쪽 patch-in-base 판정(선례: `skills/e/collect-state.sh` 의 `patchInBase`)을 붙이면 양쪽이 정확해진다 — 별도 작업.
- **snooze/ack 미도입** (범위 밖·의도): M 은 plan 을 닫기 전까지 매 세션 반복 노출된다. 알림 피로가 관측되면 `last-improve` 같은 마커 방식 도입 검토. 심각도 낮음(신호 자체는 정확).
- **`status: blocked` plan 은 영구 무신호** (범위 밖): `origin/plans-backfill` 의 `hook-recall-lesson-plan.md`(blocked, updated 2026-06-24)가 한 달째 썩어도 아무 신호가 없다. blocked 는 의도적 정지라 이번 판정에서 제외했지만, 장기 방치 축은 비어 있다.
- **wiki drift** (범위 밖·main 기원): `wiki/pages/concept/project-memory.md:15` 가 `plans/` 를 "worktree 별·gitignored" 로 설명 — §10 tracked 전환 이후 어긋남. 심각도 낮음(문서 1줄).

# Blockers
(없음)
