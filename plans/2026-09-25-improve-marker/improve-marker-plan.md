---
title: improve-marker — /improve 완료 시 last-improve 마커 갱신
status: done
started: 2026-09-25
updated: 2026-09-25
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

SessionStart 의 "/improve 권장 — failure 신호 N세션 누적 (마커 이후)" 이 `/improve` 를 돌린 뒤 0 부터 다시 센다. 지금은 마커를 쓰는 코드가 없어 누적이 줄지 않는다(2026-09-25 기준 58세션).

# Intent

- 링크: `plans/2026-09-25-repo-audit-followups/intent.md` 의 `improve-marker` 단위.
- Problem: `scripts/session-brief.js` 는 `<signalDir>/last-improve` 의 mtime 이후 failure 세션만 세는데, 그 파일을 쓰는 코드가 repo 어디에도 없다(README 만 "touch" 라고 적었다). 마커가 없으면 전체 누적이라 nudge 가 영구히 뜨고, 신호로서 의미를 잃는다.
- 사용자 선택(2026-09-25): 기간 창이 아니라 "`/improve` 완료 시 마커 갱신".
- Constraints: `improve.sh` 의 read-only 불변식과 `--ci` 모드는 그대로 둔다. 마커 경로는 한 곳에서 정한다(`CLAUDE_DLC_SIGNAL_DIR` override 를 따라야 테스트 격리가 된다).
- Out of scope: 현재 쌓인 58세션을 지금 지우는 것(사용자가 다음 `/improve` 를 돌리면 그때 갱신된다 — 내가 먼저 touch 하면 정당한 nudge 를 무승인으로 끈다). `dlc-signal.js summary` 에 "마커 이후" 집계를 더하는 것.
- 분할: 해당 없음 — small 단위.

# Acceptance

1. `node scripts/dlc-signal.js mark` 가 `<signalDir>/last-improve` 를 만들고(디렉토리가 없으면 생성) 이미 있으면 mtime 을 지금으로 올린다. 쓰기 실패는 한 줄 오류 + exit 1, 모르는 subcommand 는 비0 종료. 검증: `dlc-signal.test.js` 의 mark 테스트 2개 통과(과거로 되돌린 mtime 이 실행 뒤 앞으로 이동 / 파일 아래 경로·오타 subcommand 가 비0).
2. mark CLI 로 쓴 마커를 `session-brief.js` 가 그대로 읽는다 — 마커 이전 failure 신호만 있으면 nudge 가 사라진다. 검증: `session-brief.test.js` 의 통합 테스트 통과(같은 신호로 mark 전에는 nudge, 후에는 무음).
3. 마커 경로 단일 소스: `session-brief.js` 가 파일명을 직접 조립하지 않고 `dlc-signal.js` 의 export 를 쓴다. 검증: `git grep -n "'last-improve'" scripts/` 가 `dlc-signal.js` 한 곳만 나온다(테스트 제외).
4. `/improve` 절차가 완료 시 mark 를 실행한다: `skills/improve/SKILL.md` 7단계(기본·deep 공통 마무리)에 명령(`~/.claude/scripts/` 고정 경로)과 조건(최종 보고 직전, 신호를 보지 못했으면 안 함, 성공 줄 확인)이 있고, 경계 절이 유일한 write 예외(telemetry 상태, 운영 자산 아님)를 말한다. README `/improve`·`dlc-signal.js`·`session-brief.js` 서술이 이 경로를 가리킨다. 검증: 해당 줄 grep.
5. 전체: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음), 이 plan 의 plan-lint 통과.

# Progress

- 2026-09-25: 착수. Explore — 마커 read 는 `scripts/session-brief.js:124`, write 경로 없음, `improve.sh` 는 read-only(헤더 :6)·`--ci` 모드.
- 2026-09-25: TDD Red→Green(mark CLI·브리프 통합). code-reviewer(+codex 병행, 한도 오류 없음): 차단급 없음, SKILL 7단계 문구 3건·실패 계약 테스트 누락·Nit 6건 → fix loop 1. verify ALL PASS.
- 2026-09-25: 재리뷰 APPROVE, Nit 반영. simplify 체크 — 코드 diff 가 export 1개·CLI 분기 2개라 줄일 것 없음. 커밋 후 로컬 ff-merge.

# Next

(없음 — 로컬 ff-merge 로 종료)

# Decisions

- 마커 쓰기는 `node scripts/dlc-signal.js mark` CLI 로 둔다. 이유: `dlc-signal.js` 가 이미 `signalDir`(env override 포함)의 단일 소스이고, `session-brief.js` 도 그 모듈을 require 한다.
- 기각: `improve.sh --mark` — `improve.sh` 는 헤더·README·SKILL 이 모두 read-only 로 적고 CI 에서도 돈다. write 플래그를 더하면 그 불변식이 "플래그를 안 주면" 으로 약해진다. (처음 적은 "bash 에서 경로를 다시 조립해 signalDir 이 둘이 된다" 는 근거는 틀렸다 — 점검 7 이 이미 `SIGDIR` 을 bash 로 조립한다. 다만 거기에 write 까지 얹으면 읽기 경로와 쓰기 경로가 bash·node 로 갈린다.)
- 기각: SKILL.md 에 `touch ~/.claude/telemetry/last-improve` 를 직접 적기 — `CLAUDE_DLC_SIGNAL_DIR` override 를 무시해 브리프가 읽는 경로와 어긋날 수 있다.
- 마커 시각은 mark 실행 시각(최종 보고 직전). `/improve` 실행 중 들어온 신호가 빠질 수 있으나 몇 분 창이라 감수한다.
- 커밋 단위: 1개 — 목적이 하나(마커를 쓰는 경로)다.
- SKILL 7단계 명령은 `node ~/.claude/scripts/dlc-signal.js mark` 고정 경로로 쓴다(리뷰 반영). 이유: SKILL 은 user-level 에서 로드되고, 상대경로면 이 머지 이전에 딴 worktree 세션에서 옛 스크립트가 무음 exit 0 으로 끝난다(재현됨). 같은 이유로 SKILL 은 성공 줄(`last-improve 마커 갱신:`)을 확인하게 했다.
- mark 는 7단계(기본·deep 공통 마무리)로 둔다 — "4단계 끝" 이면 deep 모드에서 5·6단계보다 먼저 돈다. Acceptance 4 문구를 여기에 맞췄다(완화 아님 — 조건이 늘었다).
- CLI 는 모르는 subcommand 에 exit 2 로 바꿨다. 인자 없이 실행하는 호출부가 없다(hook 은 require, verify.sh 는 `node --check`).

# Key Files

- `scripts/dlc-signal.js` — `improveMarkerPath` export, `mark` CLI
- `scripts/session-brief.js` — 마커 경로를 export 로 읽음
- `scripts/dlc-signal.test.js` · `scripts/session-brief.test.js` — mark 단위(성공·실패 계약)·통합 테스트
- `plans/2026-09-25-repo-audit-followups/intent.md` — `# Plans` 의 자기 줄
- `skills/improve/SKILL.md` — 7단계 mark, 경계 절 예외
- `README.md` — `/improve`·`dlc-signal.js`·`session-brief.js` 서술

# Review Disposition

- [code] Minor(분쟁: Codex Major / Claude Minor) SKILL 7단계 skip 조건이 신호 집계 실패를 못 거름 — fix(비0 종료·점검 7 실패·중단이면 안 함, `[error]` 발견은 실패 아님).
- [code] Minor 옛 스크립트·오타 subcommand 가 무음 exit 0 — fix(CLI 는 모르는 subcommand exit 2, SKILL 은 고정 경로 + 성공 줄 확인).
- [code] Minor 보고와 mark 순서 모순 — fix(최종 보고 직전 실행, 결과를 보고에 포함).
- [code] Minor 비0 종료 계약 테스트 없음 — fix(테스트 추가).
- [code] Minor plan Acceptance 4·Key Files 의 "4단계"·낡은 Progress/Next — fix.
- [code] Nit README 트리 주석 read-only 잔존 — fix. Nit 경계 절 경로 하드코딩 — fix(`<signalDir>`). Nit "사람이 부르는 명령" 근거 — fix. Nit raw stack 출력 — fix(한 줄 오류 + exit 1). Nit plan 기각 근거 전제 오류 — fix(Decisions 정정).
- [code] Nit mark 시각 이전·신호 읽은 뒤 들어온 신호 누락 창 — wontfix(Decisions 에서 감수한 트레이드오프).
- [code] 재리뷰(fix loop 1): APPROVE. 새 Nit — plan Decisions 의 "보고 직후" 잔존 fix, `# Next` 의 push 표현 fix, SKILL 의 `~` 가 PowerShell 에서 확장 안 될 수 있음 wontfix(1단계가 이미 bash 를 요구하고, 실패해도 비0 으로 드러난다).
- [code] Open: worktree 격리가 Bash 의 main 경로 write 를 막는가 — 해소. 같은 세션의 config-docs-sync worktree 에서 python 이 `~/.claude/settings.json`·`backups/` 를 썼다(막히지 않음). 막히더라도 mark 는 비0 으로 드러난다.

# Deferred

- (low) `scripts/dlc-signal.js` summary 가 ENOENT 외 읽기 오류(EACCES 등)도 삼켜 "신호 없음" 을 출력한다 — 이번 변경 이전부터의 동작. ENOENT 만 무음으로 두고 나머지는 점검 7 이 실패로 보이게 하는 방안.

# Blockers

없음.
