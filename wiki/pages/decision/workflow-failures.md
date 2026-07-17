---
title: workflow-failures
category: decision
created: 2026-06-19
updated: 2026-07-12
sources:
  - skills/dlc/SKILL.md (Workflow Findings)
  - scripts/dlc-signal.js (자동 신호 수집 — 2026-07-03)
  - plans/2026-07-04-ledger-fix (evidence-ledger 오탐 3종 fixed — 2026-07-05·07-12)
---

# workflow-failures

dlc/규약 자체의 문제로 작업이 샌 **확인된 workflow 실패**를 작업을 가로질러 누적 추적한다 — [[dlc-development-cycle]] 의 Workflow Findings 가 plan(일시적)에 더해 여기에 영속 기록된다. 같은 실패가 2회 이상 누적되면 `wt` 로 해결을 제안한다.

## 추적 표
| 실패(깨진 규칙/단계) | 재발 조건 | 수정 후보 위치 | 횟수 | 상태 |
|---|---|---|---|---|
| early-stop 이 임시·gitignored 파일(`.commit-msg` 등) Write·마무리 단계를 미검증 변경으로 오탐 → false block | dlc 마무리(커밋 메시지 임시파일 Write)마다 | `scripts/dlc-evidence-ledger.js` — gitignored 제외(`git check-ignore`) | 2 | fixed (2026-06-19) |
| rtk-rewrite hook 이 복합 Bash 명령을 오재작성 → 명령 실패 (다중 인자 `cat a b c`→`/usr/bin/read` 오류 · `echo ===` 체인→zsh `== not found` · `tail -6 f`→read 오재작성 · rg 다중경로 체인 exit 2) | 체인(`;`)·특수문자·다중 인자 파일명령이 든 Bash 호출 | `hooks/rtk-rewrite.sh` 재작성 조건 좁히기 또는 rtk upgrade | 4 | tracking (2026-07-03 — 2회+ 라 해결 제안 대상) |
| evidence-ledger `changed` 오탐 — worktree 세션이 worktree 밖 gitignored 파일(main 의 `plans/…` 등) 편집 시 check-ignore 를 세션 cwd repo 기준으로 돌려 outside-repo(128)→not-ignored 오판 → false changed → early-stop false block | worktree 세션에서 worktree 밖 gitignored 파일 편집(상위 plan 편집 등)마다 | `scripts/dlc-evidence-ledger.js` — check-ignore 를 dirname(fp) 기준 + repo 소속 walk-up 판정 | 3 | fixed (2026-07-05) |
| evidence-ledger `verified` 미인식 — 검증을 스크립트로 래핑(`bash /tmp/x-verify.sh`)하면 VERIFY(개별 도구명 매칭)가 못 잡아 verified=false → 실제 검증했는데 early-stop false block | 검증을 `bash *-verify.sh` 로 실행한 세션마다 | `scripts/dlc-evidence-ledger.js` — VERIFY_SCRIPT 패턴(키워드가 `.sh` 직전 세그먼트) | 2 | fixed (2026-07-05) |
| evidence-ledger `verified` 미인식 — 이 repo 의 테스트 방식 `node scripts/X.test.js`·`node --test` 가 VERIFY 에 없어 verified=false → dlc 세션마다 early-stop "검증 누락" false nudge(위 ② 와 동일 class, ledger-fix 세션 자체에서 관측) | `node *.test.js`/`node --test` 로 검증한 세션마다 | `scripts/dlc-evidence-ledger.js` — VERIFY 에 `node\s+(--test\|\S*\.test\.[cm]?js)` 추가 | 1 | fixed (2026-07-12) |
| evidence-ledger `changed` 오탐(간헐) — main cwd + **같은 repo** gitignored 편집인데도 드물게 early-stop 경고. ① cross-worktree 결정적 케이스와 별개, 근인 미확정(check-ignore 간헐 실패 or reset 미실행 유력) | 비결정적·드묾 | `scripts/dlc-evidence-ledger.js` — walk-up 이 timeout→in-repo 를 보수적 changed 로 만들어 완화 방향이나, gitignored 파일의 간헐 check-ignore timeout 은 여전히 false warning 가능 → 근인 규명 필요 | 1 | tracking (2026-07-05) |
| doc-drift-readme 오탐 — CLAUDE.md/SKILL.md **내부 dedup**(README 무영향)도 `readmeDirty=true` 로 flag → false doc-drift 경고. 표면 파일 변경이 README 갱신을 실제로 요구하는지 hook 이 판정 불가(heuristic 한계) | 문서화 표면 파일을 README 불필요하게 내부 편집한 세션마다(예 CLAUDE.md §5/§13 dedup — PR #92 에서 관측) | `scripts/dlc-doc-drift.js` — 근본 판정은 불가, "불필요하면 통과" escape 가 의도된 완화. 신호에 `readmeTrigger` detail 을 실어 `/improve` 가 FP 패턴(내부 dedup) 식별 가능(signal-detail 작업) | 5 | tracking (2026-07-17 — detail 로 관측 개선, 근본 완화는 escape 유지) |

- **기록 규칙**: 같은 실패면 새 줄 말고 기존 항목 횟수만 +1. 상태 = `tracking`(누적 중) / `proposed`(wt 해결 제안함) / `fixed`(수정 머지) / `wontfix`.
- **반복 해결**: 횟수 ≥2 → dlc 가 `AskUserQuestion` 으로 "이 실패 N회 반복 — wt 로 고칠까?" 제안. 수정은 사용자 승인 후 **wt→dlc**(운영 자산 자가수정 금지 — [[self-diagnosis-and-improvement-status]]).
- 단발(횟수 1)은 여기 남기되 해결 강제 안 함 — 반복돼야 패턴으로 본다. 단 **사용자가 명시적으로 지적한 마찰**은 반복 신호로 보아 즉시 해결 대상(횟수 ≥2 취급)이 될 수 있다.
- **자동 신호와의 관계 (2026-07-03)**: hook 발동(early-stop·doc-drift·guard·plan-blocked 등)은 `scripts/dlc-signal.js` 가 `~/.claude/telemetry/dlc-signals.jsonl` 에 자동 누적하고 `/improve` 가 집계한다. 이 표는 신호가 못 담는 **맥락**(깨진 규칙·재발 조건·수정 후보)을 사람이 읽는 형태로 남기는 곳 — `/improve` 가 신호와 이 표를 대조해 횟수 갱신 누락·개선 후보를 찾는다.

## 연계
기록 트리거·형식은 [[dlc-development-cycle]], 자기개선 경계·채택 이력(수집·분석 기계화 포함)은 [[self-diagnosis-and-improvement-status]], 완료 게이트는 [[evidence-gate]].
