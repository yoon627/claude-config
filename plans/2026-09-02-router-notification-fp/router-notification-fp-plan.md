---
title: router-notification-fp — dlc-task-router 가 subagent 알림 턴에 오발동하는 문제 수정
status: done
started: 2026-09-02
updated: 2026-09-03
---

# Goal
`scripts/dlc-task-router.js`(UserPromptSubmit) 가 subagent 완료 `<task-notification>`·`<system-reminder>` 턴에도 실행되어 알림 본문의 "재현·failing" 으로 `router-investigation` 을 오발동한다(한 세션 4회). 하네스 블록을 걷어낸 사용자 텍스트만 매칭하도록 고치고, 진입점 테스트(Red→Green)·CI 등록·README 동기화.

# Progress
- 2026-09-02: `/improve` 후보 2 승인 → worktree. 가설 3(H1 알림 턴 발동 ✅ / H2 사용자 메시지 매치 ❌ / H3 Stop hook 턴 ❌). 재현 테스트 `scripts/dlc-task-router.test.js`(spawn 진입점, `CLAUDE_DLC_SIGNAL_OFF=1`) Red 확인 → 블록 제거 정규식 구현 → Green 8/8 → lint.yml 등록·README 갱신.
- 2026-09-02: 격리 runner 25개 중 24 통과(실패 1 = baseline, Deferred). code-reviewer(+codex low) Major 1(알림 턴 `ledger.reset`)·Minor 5 → fix loop 1회 반영, 테스트 12 passed, 인접 ledger/drift 테스트 무회귀. targeted 재리뷰 APPROVE(조기 exit 이 reset 만 건너뛰고 방향이 보수적임을 확인). simplify 수정 없음. 브랜치 커밋 `eafa069`.
- 2026-09-03: `/e merge` — M1 통과 → M2 PR 없음·ahead 1 → M3 push·PR #149(MERGEABLE/UNSTABLE) → M4 done 커밋.

# Next
- 없음 (PR #149 머지 시 완료).

# Decisions
- **"시작이 태그면 skip" 이 아니라 "태그 블록을 걷어내고 남은 텍스트만 매칭"** (이유: 이 세션 첫 메시지처럼 하네스가 `<system-reminder>` 를 사용자 텍스트 *앞에* 붙이는 정상 프롬프트가 있어, 시작 문자 판정은 진짜 사용자 요청을 놓친다).
- 테스트는 순수 함수 추출 없이 진입점을 spawn 해 stdin→stdout 계약을 검증 (이유: 라우터는 40줄짜리 hook 이고 계약이 곧 I/O — 추출은 과한 추상화. ledger 부작용은 테스트 session id 파일을 끝에 삭제).
- 텔레메트리 emit 은 `CLAUDE_DLC_SIGNAL_OFF=1` 로 차단(기존 스위치 재사용).

# Key Files
- `scripts/dlc-task-router.js` — prompt 전처리 1곳(정규식)
- `scripts/dlc-task-router.test.js` — 신규, 8 케이스
- `.github/workflows/lint.yml` — Unit tests 에 등록
- `README.md` — 라우터 설명에 전처리·테스트 표기

# Blockers
(없음)

# Acceptance
- [x] 재현: 알림만 담긴 prompt 로 진입점을 실행하면 `[dlc:investigation]` 이 출력된다 — 검증: 테스트 Red 실행 관찰(4번째 케이스 실패).
- [x] 수정 후 같은 입력이 무출력, 사용자 텍스트에 키워드가 있으면(reminder 앞·뒤 모두) 라우팅 유지 — 검증: `node scripts/dlc-task-router.test.js` 8 passed.
- [x] `node --check scripts/dlc-task-router.js` 통과.
- [x] CI 등록·README 동기화 — 검증: lint.yml diff(syntax check + Unit tests 2곳), README 라우터 줄·CI 테스트 목록.
- [x] 알림-only 턴은 evidence 장부를 리셋하지 않고, 사용자 턴은 리셋 — 검증: 테스트 `notification turn keeps evidence ledger`·`user turn resets evidence ledger` 통과(12 passed).
- [x] 격리 runner 로 lint.yml 의 Node syntax check + Unit tests 전부 통과 — 25개 중 24개 exit 0. 유일한 실패 `skills/jira-worklog/test_launcher.sh`(exit 127, `mapfile: command not found`)는 base 대비 diff 0 인 파일이라 baseline(아래 Deferred).

# Review Disposition
code-reviewer(+codex low) REQUEST CHANGES → fix loop 1회.
- fix — 알림 턴에도 `ledger.reset` 실행 → early-stop 의 changed/verified·doc-drift 미탐 (Major, pre-existing·같은 근본 원인): 블록 제거 후 사용자 텍스트가 없으면 exit(리셋 skip). 회귀 테스트 2개 추가.
- fix — fixture 가 실제 하네스 형태(래퍼 없는 최상위 `<task-notification>` + `<summary>`)와 불일치 (Minor): 실측 형태를 기본 fixture 로, 래퍼 형태는 보조 케이스.
- fix — 테스트 session id 고정·cleanup 미보장 (Minor): pid 유니크 + try/finally(선례 `dlc-evidence-ledger.test.js`).
- fix — lint.yml syntax check 목록·README:402 CI 목록 누락 (Minor).
- fix — 태그 대소문자 (Minor): `toLowerCase` 를 replace 앞으로. 미종료·속성·동일이름 중첩은 현 하네스 출력(1841건 전부 소문자·무속성)에 없어 wontfix.
- wontfix — 정규식 이차 시간(미종료 opener 수천 개, Nit): 실제 최악 프롬프트 882KB 가 1ms, 현실 트리거 부재. 사용자가 태그 문자열을 인용하는 경우 키워드 소실(Nit): harm 은 nudge 1회 누락.
- false-positive(리뷰어 refuted 4건 동의) — `ok(name)` 관례 / grounding 회귀 / SIGNAL_OFF 실효 / slash-command 래퍼.
- open(❌모름) — subagent 알림이 `<system-reminder>` 래퍼로 오는 형태의 존재 여부: 정규식은 두 형태 모두 처리하므로 결과 무관.

# Deferred
- `skills/jira-worklog/test_launcher.sh:21` 이 `mapfile`(bash 4+)을 써서 macOS 기본 `/bin/bash` 3.2 로컬에선 exit 127. CI(ubuntu, bash 5)는 통과하므로 로컬 전용 baseline 실패 — 입증: 이 worktree 의 `skills/jira-worklog/` 는 origin/main 대비 diff 0. 수정 후보: `mapfile` → `while read` 루프 또는 shebang 을 `#!/usr/bin/env bash` + brew bash 안내. 심각도 minor. **→ 해소(2026-09-03, plan `launcher-test-bash3` — `while read` 루프로 교체).**
