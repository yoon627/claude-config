---
title: workflow-failures
category: decision
created: 2026-06-19
updated: 2026-07-03
sources:
  - skills/dlc/SKILL.md (Workflow Findings)
  - scripts/dlc-signal.js (자동 신호 수집 — 2026-07-03)
---

# workflow-failures

dlc/규약 자체의 문제로 작업이 샌 **확인된 workflow 실패**를 작업을 가로질러 누적 추적한다 — [[dlc-development-cycle]] 의 Workflow Findings 가 plan(일시적)에 더해 여기에 영속 기록된다. 같은 실패가 2회 이상 누적되면 `wt` 로 해결을 제안한다.

## 추적 표
| 실패(깨진 규칙/단계) | 재발 조건 | 수정 후보 위치 | 횟수 | 상태 |
|---|---|---|---|---|
| early-stop 이 임시·gitignored 파일(`.commit-msg` 등) Write·마무리 단계를 미검증 변경으로 오탐 → false block | dlc 마무리(커밋 메시지 임시파일 Write)마다 | `scripts/dlc-evidence-ledger.js` — gitignored 제외(`git check-ignore`) | 2 | fixed (2026-06-19) |
| rtk-rewrite hook 이 복합 Bash 명령을 오재작성 → 명령 실패 (다중 인자 `cat a b c`→`/usr/bin/read` 오류 · `echo ===` 체인→zsh `== not found` · `tail -6 f`→read 오재작성 · rg 다중경로 체인 exit 2) | 체인(`;`)·특수문자·다중 인자 파일명령이 든 Bash 호출 | `hooks/rtk-rewrite.sh` 재작성 조건 좁히기 또는 rtk upgrade | 4 | tracking (2026-07-03 — 2회+ 라 해결 제안 대상) |

- **기록 규칙**: 같은 실패면 새 줄 말고 기존 항목 횟수만 +1. 상태 = `tracking`(누적 중) / `proposed`(wt 해결 제안함) / `fixed`(수정 머지) / `wontfix`.
- **반복 해결**: 횟수 ≥2 → dlc 가 `AskUserQuestion` 으로 "이 실패 N회 반복 — wt 로 고칠까?" 제안. 수정은 사용자 승인 후 **wt→dlc**(운영 자산 자가수정 금지 — [[self-diagnosis-and-improvement-status]]).
- 단발(횟수 1)은 여기 남기되 해결 강제 안 함 — 반복돼야 패턴으로 본다. 단 **사용자가 명시적으로 지적한 마찰**은 반복 신호로 보아 즉시 해결 대상(횟수 ≥2 취급)이 될 수 있다.
- **자동 신호와의 관계 (2026-07-03)**: hook 발동(early-stop·doc-drift·guard·plan-blocked 등)은 `scripts/dlc-signal.js` 가 `~/.claude/telemetry/dlc-signals.jsonl` 에 자동 누적하고 `/improve` 가 집계한다. 이 표는 신호가 못 담는 **맥락**(깨진 규칙·재발 조건·수정 후보)을 사람이 읽는 형태로 남기는 곳 — `/improve` 가 신호와 이 표를 대조해 횟수 갱신 누락·개선 후보를 찾는다.

## 연계
기록 트리거·형식은 [[dlc-development-cycle]], 자기개선 경계·채택 이력(수집·분석 기계화 포함)은 [[self-diagnosis-and-improvement-status]], 완료 게이트는 [[evidence-gate]].
