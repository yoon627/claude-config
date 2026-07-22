---
title: dlc-fablize-evidence — dlc에 evidence gate·fablize 규율·wt 자동화 통합
status: done
started: 2026-06-19
updated: 2026-06-19
---

# Context

사용자가 dlc를 다음으로 강화 요청: ① 요구 모호하면 되묻기 ② 검증 항목이 실제로 작동할 때만 "완료" ③ 비trivial이면 dlc가 알아서 wt worktree 생성 ④ fablize의 검증된 규율 차용. 이전 턴의 codex 검토(전부 "부분적용", "비trivial 기준으로 좁히고 ③은 증거기반 최소형") + fablize README + hook 인프라 조사를 반영.

**확정 결정**: (Q1) fablize는 플러그인 설치 없이 **개념 직접 구현**. (Q2) evidence gate = **plan 검증항목 + Stop hook 보조(capped·fail-open)**. (Q3) ③ = **증거기반 finding 최소형**.

# Goal
1. dlc가 비trivial 작업을 **자동으로 wt worktree**에서 진행 (dlc→wt).
2. plan에 **test 가능한 acceptance 항목** → 증거(실행·통과)로 충족될 때만 완료 (evidence gate).
3. fablize 검증 규율 차용: verification grounding(실행·관찰)·investigation protocol(재현→가설경쟁→causal chain)·early-stop(capped).
4. ② 명확화 강화 / ④ wiki "판정 필수" / ⑤ wt "비trivial 강제" (codex 제안대로 완화).
5. ③ 증거기반 workflow finding 최소형.

# Next
1. **이 작업 자체를 wt worktree로** 이전 후 dlc 진행 (비trivial structural — dogfooding).
2. dlc SKILL.md 개정.
3. hook 3종 + settings.json 등록.
4. CLAUDE.md·wiki 동기화.
5. acceptance 항목 검증 + lint + hook smoke.

# Decisions
- **Q1 직접 구현**: 외부 플러그인 미설치 — repo 스타일·한국어·dlc 통합. hook 인프라는 빈 슬롯(UserPromptSubmit) + Stop 배열 추가로 충돌 없음.
- **Q2 plan + Stop hook 보조(capped·fail-open)**: hard-block 아님. plan acceptance가 1차(모델), Stop hook이 "변경했는데 검증 기록 없음"을 capped 경고로 2차 보조. fablize 철학(harness는 suggest).
- **Q3 finding 최소형**: 확인된 workflow 실패(중대 self-diagnosis·동일유형 2회)에만 plan에 한 줄. 자동 수정 금지, 2회 누적 시 제안 승격. (직전 미채택 함정 회피)
- **dlc→wt 순환 방지**: dlc Setup에서 "이미 작업 worktree 안인가?" 체크 — 아니고 비trivial이면 wt 경로. wt가 dlc를 호출한 경우는 이미 worktree 안이라 재호출 안 함. **wt의 slug 확인(AskUserQuestion)은 유지** — "자동 진입"이되 생성 자체는 확인.
- **용어 통일**(codex): "모든 작업/문제"가 아니라 **"비trivial 변경"** 기준.
- **이중 메커니즘 일관성**: evidence gate가 plan(모델이 읽음)과 hook(ledger·결정론적) 양쪽에 — 같은 규칙을 두 층이 강제, 어긋나지 않게.

# Key Files
## 신규 (구현)
- `skills/dlc/SKILL.md` — 핵심 개정: ① 진입 매트릭스(질문/읽기전용/trivial/비trivial/structural → dlc vs wt vs 직접) ② Setup에 dlc→wt 자동 ③ `# Acceptance` evidence gate(요구를 test 항목으로 분해, 증거 충족 시만 완료) ④ verification grounding(render/실행 artifact 실제 실행·관찰) ⑤ investigation protocol(디버깅) ⑥ `# Workflow Findings` 최소형 ⑦ 명확화 게이트 강화.
- `scripts/task-router.js` (UserPromptSubmit hook) — debugging/render 키워드 감지 → discipline 텍스트 주입. ledger 턴 초기화.
- `scripts/evidence-ledger.js` (PostToolUse hook) — Bash/Edit/Write 후 파일변경·검증명령·실패 기록(per-turn JSON ledger, 임시 위치).
- `scripts/early-stop-guard.js` (Stop hook, 배열 추가) — 비trivial 변경 있는데 검증결과 없음 → capped 경고(fail-open, holdout env 지원). notify-hook과 공존.
- `settings.json` — UserPromptSubmit·PostToolUse 추가, Stop 배열에 early-stop 추가.

## 동기화
- `CLAUDE.md` — §3(진입 매트릭스 참조)·§10(`# Acceptance` 섹션)·§11(wiki "판정 필수")·§8(비trivial wt) 줄 단위 갱신.
- `wiki/pages/` — 새 decision: `evidence-gate`, `dlc-wt-autoflow`, `fablize-adopted-disciplines`. 기존 `self-diagnosis-and-improvement-status`에 ③ finding 최소형 반영. index/log 갱신.

## 참고(읽기)
- hook 관례: `scripts/guard-worktree-edit.js`(stdin JSON·deny·fail-open), `scripts/notify-hook.js`.
- `docs/codex-review.md`(리뷰 병행), `skills/wt/SKILL.md`(생성 경로 재사용).

# Acceptance (이 작업의 완료 기준 — evidence gate dogfooding)
각 항목은 증거로 충족돼야 "완료". 미충족이면 완료 금지.
1. dlc SKILL에 진입 매트릭스 + dlc→wt 자동 규약 존재 — `grep`로 확인.
2. dlc SKILL에 `# Acceptance` evidence gate + verification grounding + investigation + finding 규약 존재.
3. hook 3종 파일 존재 + settings.json 등록 — JSON valid(`ConvertFrom-Json`).
4. **early-stop hook 동작 테스트**: "변경+검증없음" 입력 → 경고 / "검증있음" 입력 → 통과 / 잘못된 stdin → exit 0(fail-open).
5. **router hook 동작 테스트**: debugging 키워드 → investigation discipline 주입 / render 키워드 → grounding 주입 / 무관 → 무주입.
6. CLAUDE.md ②④⑤ 줄이 비trivial 기준으로 갱신됨.
7. wiki 신규 decision 3종 + lint clean(`check_links.py`).
8. 기존 hook(guard-worktree-edit·notify) 회귀 없음 — smoke.

# Progress
- 2026-06-19: worktree 생성→dlc SKILL 개정(진입매트릭스·dlc→wt·Acceptance·grounding·investigation·Workflow Findings·명확화 강화)→hook 4종(ledger+router+evidence+early-stop)+settings 등록→smoke 통과→CLAUDE.md/wiki 3종 동기화→lint clean.
- 2026-06-19: code-reviewer + codex(medium) 병행 리뷰. Critical 2 + Major 5 발굴 → fix loop 1회. 재검증 통과(C1 재검증강제·C2 VERIFY 정확도·node --check·router 오탐완화). Acceptance 8항목 전 충족 → PR 준비.

# Review Disposition
- C1 verified 미무효화(codex Critical) → **fix**: Edit/Write/NotebookEdit 시 verified·blocks 리셋(최종 변경 후 재검증 강제).
- C2 검증성공 미확인(codex Critical) → **fix**: VERIFY 정규식 좁힘 + NONVERIFY_START(echo/cat/grep/ls 제외). 검증 *성공* 판정은 acceptance(메인) 단일소스로 문서화(hook은 "검증 시도" 감지 근사).
- M1 NotebookEdit guard 우회 → **fix**: guard matcher에 NotebookEdit 추가.
- M2 CAP 추가변경 통과 → **fix**: C1 blocks 리셋으로 해소.
- M3 require fail-open 미적용 → **fix**: require try/catch.
- M5 CI syntax 미검사 → **fix**: lint.yml에 dlc-*.js `node --check`.
- Minor router 오탐 → **fix**: DBG/RENDER 정규식 증상표현 위주로 완화. watchdog 부재 → **fix**: 1초 stdin 안전망. Minor README → **fix**: skills/dlc 섹션 hook 문서.
- M4 ledger 원자성 → **defer**: 플래그 단조증가(false→true)라 실해 낮음, lock ROI 낮음. ledger tmp 잔존 → **defer**: OS tmp 정리·플래그뿐이라 보안 무관.

# Acceptance — 결과: 8항목 전 충족 ✅ (grep·hook smoke·lint clean·code-reviewer+codex 리뷰로 증거 확인)

# Workflow Findings
(이번 작업 중 확인된 workflow 실패 없음)

# Blockers / 염려 (사용자 질문 4)
1. **early-stop hook 오작동** — fablize도 인정한 declarative offer("~할게요") 오탐. capped(N회 후 경고로 강등)·fail-open·`HOLDOUT` env로 완화하나 **완전 제거 불가**. 한국어 패턴 튜닝 + 초기엔 경고-only로 보수 운영.
2. **③ 자기개선의 본질적 한계** — fablize 명시: self-driven 개선은 capability라 harness로 불가. finding *기록*까지만 자동, 실제 dlc 수정은 사용자 승인(자동수정 금지). "스스로 dlc 개선"의 완전 자동화는 의도적으로 안 함.
3. **dlc↔wt 자동 진입의 마찰** — dlc가 wt를 자동 invoke 시 slug 확인은 유지(무확인 생성 금지). 다만 "이미 worktree인지" 오판 시 중첩 생성 위험 → Setup 체크 견고화 필요.
4. **이중 메커니즘 동기화** — plan 규약(모델)과 hook(ledger)이 같은 evidence gate를 표현 → 한쪽만 바뀌면 불일치. 규칙 단일 소스를 SKILL에 두고 hook은 그 보조로 명시.
5. **운영자산 대량 변경 rollback 비대칭** — 전역 hook은 per-repo opt-out 불가. 단계적 적용 + 각 단계 검증 + holdout env.
6. **효과 미보장** — fablize 효과 수치도 small single-family self-measurement. 방향은 타당하나 도입 효과는 사후 관찰 필요.
