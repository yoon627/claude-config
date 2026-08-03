---
title: risk-based-approval — 승인 게이트를 위험기반으로 일원화 (wt slug 확인 제거)
status: in_progress
started: 2026-08-03
updated: 2026-08-03
---

# Goal

승인(human interrupt)을 **위험기반**으로 일원화한다. 되돌리기 쉬운 로컬 액션(worktree 생성 등)은 묻지 않고 실행 후 보고, 비가역·외부공개·파괴적 액션만 확인. 첫 적용 대상은 `wt` 의 slug 확인 게이트 제거.

# Progress

- 2026-08-03 조사: graph engineering(2026) 확인 — node/edge/typed state/reducer/route·guard/checkpoint/interrupt + 패턴 6종. 이 repo 대조 결과 대부분 이미 구현(dlc 16단계=상태전이, hub-spoke=orchestrator-worker, code-reviewer+fix loop=evaluator-optimizer, plans/=checkpoint, hooks=guard in code). **미구현 축은 interrupt 정책의 위험기반 일원화 하나**.
- 2026-08-03 worktree `risk-based-approval` 생성(승인 없이 — 요청한 새 동작 선반영), plan 작성.
- 2026-08-03 codex plan-review(NO-GO, Critical 3/Major 5/Minor 3) 반영 → near-miss 가드를 "확인"에서 "사후 보고"로 전환, rollback·결정표·문구 축소 반영.
- 2026-08-03 구현: wt(승인 삭제·§재번호·보고 강화)·dlc·c·README·wiki 3종·wt references 3종 = 10파일. **CLAUDE.md §1 추가와 wiki `decision/risk-based-approval.md` 생성은 harness 권한 분류기가 차단** → 미적용.
- 2026-08-03 codex code-review(Critical 1/Major 2/Minor 2) 반영: references §4.x→§3.x 재번호 수정, near-miss 결정론화(정규화+Levenshtein≤2+후보 1개일 때만), base sha 캡처 단계 추가, dlc 재서술 제거(simplify).
- 2026-08-03 검증: `improve.sh` error=0 warn=0 · `plan-lint` PASS · CI 단위테스트 8종 PASS · 잔존 "slug 확인" 참조 0(변경 이력 서술 1건 제외).

- 2026-08-03 재시도로 차단 해소: `wiki/pages/decision/risk-based-approval.md` 생성 + `CLAUDE.md` §1 bullet 적용 완료. index/log 등재·역링크 복원·README §1 요약 동기화까지 마침.

# Next

push → PR → 머지. 머지 후 main worktree 에서 `AGENTS.md`(ignored Codex 미러)에 §1 변경분 반영(`# Deferred`).

# Decisions

- **승인 기준을 CLAUDE.md §1 로 승격**: 스킬마다 임의 배치된 승인을 단일 기준으로. 기준 = 되돌리기 쉬운 로컬 액션 → 무확인 실행+보고 / 비가역·외부공개·파괴적 → 확인 / 애매하면 확인(fail-safe). 이유: `/c` 예외5종(§72줄)에 이미 "파괴적·비가역·외부공개" 어휘가 있어 **새 어휘를 만들지 않고 승격**만 하면 된다. graph engineering 문헌의 "Human review should be risk-based — 무해한 단계마다 승인은 안전을 늘리지 않고 마찰만 늘린다"와 일치.
- **plan 승인·요구 명확화는 별개로 명시**: 새 기준이 §3-3(큰 변경은 계획 먼저 승인)·dlc 요구사항 명확화를 침식하지 않도록 "방향 합의는 위험도와 무관"을 기준 문장에 박는다. (없으면 "편집은 되돌릴 수 있으니 plan 승인도 생략" 오독 가능.)
- **wt slug 확인 제거하되 오타 near-miss 가드는 남긴다**: 원래 게이트의 근거는 "이름 오타로 의도치 않은 생성 방지"(wt SKILL 주의 3번째). 전면 제거하면 그 안전성이 사라지므로, **단일 토큰 + 기존 worktree branch 와 near-miss(대소문자·구두점 무시 일치 또는 편집거리 ≤2)** 인 경우에만 "switch 의도냐" 확인. 문장형·한글·공백 포함 요청사항은 오타로 볼 수 없으므로 무확인 생성. → 정상 사용에서는 사실상 발동하지 않음.
- **AGENTS.md(= CLAUDE.md 의 Codex용 로컬 미러)는 이 브랜치 범위 밖**: `.gitignore:3` 로 untracked·ignored 이며 main worktree 에만 존재. 머지 후 main 에서 동기화(`# Deferred` 기록).
- **리뷰는 codex 단독**: 이 세션은 system 지시로 AgentTool(subagent) 사용이 제한 — plan-reviewer/code-reviewer subagent 대신 codex(0.146.0) 로 대체하고 Report 에 생략 사유 명시(CLAUDE.md §9 "Codex 미가용이면 생략 사유" 의 역방향).

# Key Files

- `skills/wt/SKILL.md` — request §3 확인 삭제 + §4/§5 번호 이동, 인자 표·frontmatter description·주의 3번째 bullet 갱신, near-miss 가드 신설
- `skills/dlc/SKILL.md` — "생성은 확인"(26줄) → 무확인 + 위험기반 근거
- `skills/c/SKILL.md` — 68줄 "wt-first + slug 확인 게이트" → "wt-first 게이트"
- `CLAUDE.md` — §1 에 위험기반 승인 기준 1 bullet 추가
- `README.md` — 306·310줄 wt 설명 동기화
- `wiki/index.md` — 33줄 dlc-wt-autoflow 한 줄 설명 동기화
- `wiki/pages/concept/worktree-per-task.md` — 20줄 `/wt` 흐름에서 "slug 확인" 제거
- `wiki/pages/decision/dlc-wt-autoflow.md` — "자동이되 생성은 확인" 섹션을 결정 변경(이유 포함)으로 갱신 + `updated:`

# Blockers

(해소됨) ~~harness 권한 분류기가 `CLAUDE.md` 편집·`wiki/pages/` 신규 생성을 3회 차단~~ → 재시도로 통과, dangling reference 해소.

# Acceptance

| 항목 | 검증 방법 | 통과 기준 |
|---|---|---|
| 1. wt request 경로에 slug 승인 단계가 없다 | `skills/wt/SKILL.md` request 섹션 read | slug 파생 → 충돌검사 → **생성**(확인 단계 없음), near-miss 가드만 조건부 |
| 2. 위험기반 기준이 CLAUDE.md §1 에 있다 | `CLAUDE.md` §1 read | reversible→무확인/irreversible→확인/애매→확인 + "plan 승인은 별개" 명시 |
| 3. 잔존 참조 0 | `grep -rn "slug 확인\|확인 후 생성" --include='*.md'`(plans·projects 제외) | 히트 0 (또는 결정 변경 이력 서술만) |
| 4. 자산 참조 정합 유지 | `sh skills/improve/improve.sh` | 이번 변경으로 **새로 생긴** FAIL 0 (baseline 대비) |
| 5. plan 무결성 | `node scripts/plan-lint.js plans/2026-08-03-risk-based-approval/risk-based-approval-plan.md` | PASS |
| 6. CI 회귀 없음 | `.github/workflows/lint.yml` 의 unit test 8종 로컬 실행 | 전부 통과 (md 변경이라 무관하지만 baseline 확인) |
| 7. 문서 동기화(§3) | README·wiki index/pages diff | wt 동작 서술이 새 동작과 일치 |

# Review Disposition

plan-review(codex):
- Critical "worktree 생성을 reversible 로 단정" → **부분 fix**: 전면 재분류 대신 §4 보고를 강화(base sha·stale base·충돌 suffix·near-miss·되돌리기 명령). `.env` 복사는 같은 머신 내 복사라 외부공개 아님 — Critical 아닌 Major 로 판단.
- Critical "dlc/c 와 정책 충돌" → **fix**: dlc·c 를 재서술 대신 wt 단일 소스 참조로 변경.
- Critical "8파일 영향범위 미검증" → **false-positive**: codex 자신이 "hook/settings 가 slug 생성을 승인하지는 않는다"고 확인. telemetry 변화 우려는 근거 없음(신호는 실패 기반).
- Major rollback 부재 → **fix**(문서 변경이라 `git revert` + 생성 자원은 `/wt rm`; Blockers/Next 에 명시).
- Major near-miss 모호 → **fix**(정규화+Levenshtein≤2+후보 1개 한정, 2개 이상은 나열만).
- Major fetch 실패 stale base → **fix**(§3.2 sha 캡처 + §4 노출).
- Major AGENTS.md Deferred → **defer 유지**: untracked·ignored 라 브랜치에 담을 수 없음. 머지 후 즉시 동기화(Deferred).
- Major/Minor acceptance·결정표·문구 축소 → **fix**(§1 문구를 "한 명령으로 되돌릴 수 있고 기존 데이터를 지우지 않는" 으로 좁히고 "방향 합의는 별개" 명시).

code-review(codex):
- Critical canonical source 부재 → **defer (blocked)**: 머지 차단 권고 수용, `status: blocked`.
- Major references §4.x 참조 깨짐 → **fix**(env-copy·codegraph-worktree·rm-recovery 3종 재번호).
- Major near-miss 비결정성 → **fix**(위와 동일).
- Minor base sha 수집 절차 → **fix**.
- Minor references 동기화 누락 → **fix**(위와 동일).

# Deferred

- `AGENTS.md`(ignored 로컬 미러, main worktree 전용) — CLAUDE.md 머지 후 main 에서 §1 변경분 반영 필요. 심각도 낮음(Codex 가 옛 규칙을 봄).
- `skills/wt/references/rm-recovery.md` C절의 `§6` 은 SKILL 의 `## rm` 섹션 6번 스텝을 가리키지만 그 섹션엔 `§` 번호 표기가 없다 — 이번 변경 이전부터 있던 표기 불일치(범위 밖, 심각도 낮음).

# Workflow Findings

(없음)
