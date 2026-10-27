---
title: dlc-split-exception — 같은 출처의 작은 후속을 목적 단위 커밋으로 한 plan 에 묶는 예외
status: in_progress
started: 2026-10-27
updated: 2026-10-27
---

# Goal
dlc 분할 판정에 예외를 둔다: 같은 출처에서 온 결합 없는 작은 후속들은 목적 단위 커밋으로 단위마다 따로 revert 할 수 있으면 한 plan 에 둘 수 있다. 같은 `Split:` 형식을 정하는 CLAUDE.md §10 과 plan-reviewer 14항도 함께 맞춘다.
- Why: 공용 wiki workflow-failures #55(3회) — 같은 `# Deferred` 의 low 항목들을 함께 처리할 때마다 "단위마다 plan" 규칙에서 이탈했다. 사용자 승인 2026-10-27("적용", 이어서 리뷰 지적에 따라 "세 곳 함께 고치기").
- Constraints: 예외는 같은 출처(한 plan 의 `# Deferred`·Out of scope, 또는 같은 open intent)로 한정 — CLAUDE.md §8 "무관한 변경을 한 브랜치에 섞지 않는다" 와 맞추려고. 같은 파일 안에서 섞이는 단위·structural 트리거가 있는 단위면 예외 불가. `Split:` 표지는 세 곳에서 같은 영어 고정 문자열 `none — purpose-commit bundle: …`(CLAUDE.md 는 한국어 0). 사용자 지시(2026-10-26): 추천안대로 끝까지 진행.
- Out of scope: dlc 영어 번역(read-points 머지 뒤 번역 단위) · README(`Split: none — <근거>` 일반 서술이라 그대로 맞다).
- Split: none — 세 문서가 같은 `Split:` 형식을 정해 일부만 머지되면 규약끼리 모순이다.

# Tasks
- [x] dlc 분할 판정에 예외 (2026-10-27) — `skills/dlc/SKILL.md` — 처음 한 문장만 넣었다가 code-reviewer 가 세 곳 불일치·범위 무제한·전제 붕괴 시 처리 없음을 잡아, 같은 출처 한정·불가 조건·재판정 절·"안 나뉘면" 뒤로 이동으로 고쳤다
- [x] CLAUDE.md §10 `Split:` 형식·트리거 2 (2026-10-27) — `CLAUDE.md`
- [x] plan-reviewer 14항 (2026-10-27) — `agents/plan-reviewer.md` — 예외 표지면 "결합" 대신 출처·단위별 revert·structural 을 반박
- [x] 재리뷰(code-reviewer — plan 대조 포함) (2026-10-27) — Critical·Major 0, Acceptance 1~3 충족. Minor 반영: plan-reviewer 의 "한 파일에 섞임" 을 "한 커밋 단위로 합쳐질 만큼 섞임(같은 파일을 커밋을 나눠 고치는 것은 괜찮다)" 으로, 정의 없는 "작은/small" 삭제. "같은 open intent" 가 넓다는 점은 리뷰어가 반박하므로 그대로(처분은 `plans/2026-10-27-dlc-split-exception/dlc-split-exception-log.md`)
- [x] 사용자 diff 확인 (2026-10-27) — "커밋 (추천)"
- [x] `bash scripts/verify.sh changed` (2026-10-27) — 격리 runner: `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 미설치, 무관), 표지가 세 파일에 하나씩 — Acceptance 1~4 충족
- [ ] 머지 (`/e merge`)
- [ ] [post-merge] main 세션에서 공용 wiki workflow-failures #55 → fixed, log

# Acceptance
1. 세 곳이 같은 예외를 같은 표지로 말한다 — `rg -n "purpose-commit bundle" CLAUDE.md agents/plan-reviewer.md skills/dlc/SKILL.md` — 세 파일 모두에 나온다
2. 예외의 범위·불가 조건·재판정이 dlc 에 있다 — `skills/dlc/SKILL.md` 분할 판정 — 같은 출처 한정, 같은 파일 섞임·structural 이면 불가, 전제가 깨지면 재판정
3. 독립 대조 — code-reviewer 재리뷰에서 Critical·Major 0
4. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
5. [post-merge] 공용 wiki #55 상태 갱신

# Decisions
- wiki 결정 [[workflow-failures]] #55 의 제안(dlc 분할 판정 예외) → 따르고 넓힌다(CLAUDE.md §10·plan-reviewer 14항도 같은 형식을 정해 함께 고쳐야 모순이 없다 — code-reviewer, 사용자 승인).
- 표지는 영어 고정 문자열 `none — purpose-commit bundle: <공통 출처> · <단위들> · <이유>` — 기존 `none — <…>` 처럼 plan 이 한국어여도 표지는 고정 문자열. 기각: 한국어 표지(CLAUDE.md 는 한국어 0 이라 세 곳이 갈린다).
- 범위를 같은 출처로 한정 — "결합 없음" 만으로 열면 무관한 변경을 한 브랜치에 섞는 근거가 된다(CLAUDE.md §8). 기각: "등" 으로 열어 두기.
- 커밋 단위: 1개 — `docs(dlc): allow a purpose-commit bundle in the split judgment`(세 파일이 한 형식이라 한 커밋). plan 은 기록 커밋.
- 테스트: 규칙 문구라 새 테스트 없음(§7 예외) — 수동 검증은 Acceptance 1~3, 사용자 diff 확인이 행동 검증.
- Codex 미가용.
- 롤백: `docs(dlc)` 커밋 `git revert`.

# Blockers
