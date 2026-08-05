---
title: workflow-failures
category: decision
created: 2026-06-19
updated: 2026-08-05
sources:
  - skills/dlc/SKILL.md (Workflow Findings)
  - scripts/dlc-signal.js (자동 신호 수집 — 2026-07-03)
  - plans/2026-07-04-ledger-fix (evidence-ledger 오탐 3종 fixed — 2026-07-05·07-12)
  - plans/2026-08-05-doc-drift-testfile-fp (.test.js doc-drift 오탐 fixed — 2026-08-05)
---

# workflow-failures

dlc/규약 자체의 문제로 작업이 샌 **확인된 workflow 실패**를 작업을 가로질러 누적 추적한다 — [[dlc-development-cycle]] 의 Workflow Findings 가 plan(일시적)에 더해 여기에 영속 기록된다. 같은 실패가 2회 이상 누적되면 `wt` 로 해결을 제안한다.

## 추적 표
| 실패(깨진 규칙/단계) | 재발 조건 | 수정 후보 위치 | 횟수 | 상태 |
|---|---|---|---|---|
| early-stop 이 임시·gitignored 파일(`.commit-msg` 등) Write·마무리 단계를 미검증 변경으로 오탐 → false block | dlc 마무리(커밋 메시지 임시파일 Write)마다 | `scripts/dlc-evidence-ledger.js` — gitignored 제외(`git check-ignore`) | 2 | fixed (2026-06-19) |
| rtk 가 `tail -N f`·`cat a b c` 를 `rtk read -N f`·`rtk read a b c` 로 재작성 → `rtk read` 가 미지원 인자에서 서브커맨드명으로 폴백해 **`/usr/bin/read` 를 실행** → `read: -1: invalid option` / `not a valid identifier` | `tail -N`·다중 파일 `cat`/`head`/`tail` 이 든 Bash 호출마다(결정적) | **rtk 바이너리 업그레이드** — 설치본 0.28.2, 상류는 이 둘을 각각 **0.35.0**(`cmd: read/cat multiple file`)·**0.39.0**(`head/tail multi-file rewrite falls back to native command` #1362)에서 수정함. `hooks/rtk-rewrite.sh` 는 규칙 없는 얇은 위임자이고 `.gitignore` 로 untracked·rtk 관리라 **수정 위치가 아니다** | 6 | proposed (2026-08-03 — 근본원인 확정, 업그레이드는 headroom 번들 소유라 사용자 결정 대기) |
| evidence-ledger `changed` 오탐 — worktree 세션이 worktree 밖 gitignored 파일(main 의 `plans/…` 등) 편집 시 check-ignore 를 세션 cwd repo 기준으로 돌려 outside-repo(128)→not-ignored 오판 → false changed → early-stop false block | worktree 세션에서 worktree 밖 gitignored 파일 편집(상위 plan 편집 등)마다 | `scripts/dlc-evidence-ledger.js` — check-ignore 를 dirname(fp) 기준 + repo 소속 walk-up 판정 | 3 | fixed (2026-07-05) |
| evidence-ledger `verified` 미인식 — 검증을 스크립트로 래핑(`bash /tmp/x-verify.sh`)하면 VERIFY(개별 도구명 매칭)가 못 잡아 verified=false → 실제 검증했는데 early-stop false block | 검증을 `bash *-verify.sh` 로 실행한 세션마다 | `scripts/dlc-evidence-ledger.js` — VERIFY_SCRIPT 패턴(키워드가 `.sh` 직전 세그먼트) | 2 | fixed (2026-07-05) |
| evidence-ledger `verified` 미인식 — 이 repo 의 테스트 방식 `node scripts/X.test.js`·`node --test` 가 VERIFY 에 없어 verified=false → dlc 세션마다 early-stop "검증 누락" false nudge(위 ② 와 동일 class, ledger-fix 세션 자체에서 관측) | `node *.test.js`/`node --test` 로 검증한 세션마다 | `scripts/dlc-evidence-ledger.js` — VERIFY 에 `node\s+(--test\|\S*\.test\.[cm]?js)` 추가 | 1 | fixed (2026-07-12) |
| evidence-ledger `changed` 오탐(간헐) — main cwd + **같은 repo** gitignored 편집인데도 드물게 early-stop 경고. ① cross-worktree 결정적 케이스와 별개, 근인 미확정(check-ignore 간헐 실패 or reset 미실행 유력) | 비결정적·드묾 | `scripts/dlc-evidence-ledger.js` — walk-up 이 timeout→in-repo 를 보수적 changed 로 만들어 완화 방향이나, gitignored 파일의 간헐 check-ignore timeout 은 여전히 false warning 가능 → 근인 규명 필요 | 1 | tracking (2026-07-05; 2026-07-30 이후 재발 0 — 2026-08-05 telemetry 확인) |
| doc-drift-readme 오탐 — CLAUDE.md/SKILL.md **내부 dedup**(README 무영향)도 `readmeDirty=true` 로 flag → false doc-drift 경고. 표면 파일 변경이 README 갱신을 실제로 요구하는지 hook 이 판정 불가(heuristic 한계) | 문서화 표면 파일을 README 불필요하게 내부 편집한 세션마다(예 CLAUDE.md §5/§13 dedup — PR #92 에서 관측, 최근 2026-08-05) | `scripts/dlc-doc-drift.js` — 근본 판정은 불가, "불필요하면 통과" escape 가 의도된 완화. 신호에 `readmeTrigger` detail 을 실어 `/improve` 가 FP 패턴(내부 dedup) 식별 가능(signal-detail 작업) | 7 (telemetry unique-session 총계 — 7월 5 + 8월 2, 아래 `.test.js` sub-class 1건 포함) | tracking (2026-08-05 — sub-class 1종은 아래 행에서 fixed, 내부 dedup 은 escape 유지) |
| doc-drift-readme 오탐 **sub-class** — `scripts/*.test.js` **기존 파일 편집**만으로 README 미갱신 경고. `classify()` 의 `/^scripts\/[^/]+\.js$/` 가 `.test.js` 도 매치하는데, README 는 테스트를 `x.js (+ .test.js)` 접미 표기로만 문서화해 내용 변경이 README 에 영향이 없다 | 기존 테스트 파일을 편집한 세션마다(결정적). telemetry detail `scripts/session-brief.test.js`(2026-08-04) 로 확정 | `scripts/dlc-doc-drift.js` — `readme-trigger-new` 카테고리 신설(README 가 **존재만** 문서화하는 부류는 신규 추가일 때만 trigger) + 신규 판정은 `scripts/dlc-evidence-ledger.js` 의 `isNewInRepo`(`git ls-tree HEAD`)가 주입 | 1 (위 7 중) | fixed (2026-08-05) |

- **early-stop-verify 계열 fix 효과 확인 (2026-08-05, telemetry 실측)**: unique-session 기준 2026-07 **16** → 2026-08 **0**, 마지막 발화 **2026-07-30**. 더 강한 근거는 detail 축 — `.md` 편집을 verify 게이트에서 제외한 fix(`584ae95`, 2026-07-17) **이후 신호 20건 중 `.md` detail 은 0건**(전부 `.kt`·`.sh`·`settings.json`·`.env.example` 등 실제 코드 변경, 대부분 타 repo). 즉 doc-only 오탐 class 는 재발 0. ⚠️ 8월 0 자체는 표본이 5일뿐이라 "완전 소멸"의 증거는 아니고, detail 축이 fix 효과의 직접 근거다.
- **기록 규칙**: 같은 실패면 새 줄 말고 기존 항목 횟수만 +1. 상태 = `tracking`(누적 중) / `proposed`(wt 해결 제안함) / `fixed`(수정 머지) / `wontfix`.
- **반복 해결**: 횟수 ≥2 → dlc 가 `AskUserQuestion` 으로 "이 실패 N회 반복 — wt 로 고칠까?" 제안. 수정은 사용자 승인 후 **wt→dlc**(운영 자산 자가수정 금지 — [[self-diagnosis-and-improvement-status]]).
- 단발(횟수 1)은 여기 남기되 해결 강제 안 함 — 반복돼야 패턴으로 본다. 단 **사용자가 명시적으로 지적한 마찰**은 반복 신호로 보아 즉시 해결 대상(횟수 ≥2 취급)이 될 수 있다.
- **자동 신호와의 관계 (2026-07-03)**: hook 발동(early-stop·doc-drift·guard·plan-blocked 등)은 `scripts/dlc-signal.js` 가 `~/.claude/telemetry/dlc-signals.jsonl` 에 자동 누적하고 `/improve` 가 집계한다. 이 표는 신호가 못 담는 **맥락**(깨진 규칙·재발 조건·수정 후보)을 사람이 읽는 형태로 남기는 곳 — `/improve` 가 신호와 이 표를 대조해 횟수 갱신 누락·개선 후보를 찾는다.

## 연계
기록 트리거·형식은 [[dlc-development-cycle]], 자기개선 경계·채택 이력(수집·분석 기계화 포함)은 [[self-diagnosis-and-improvement-status]], 완료 게이트는 [[evidence-gate]].
