---
title: evidence-gate
category: decision
created: 2026-06-19
updated: 2026-06-19
sources:
  - skills/dlc/SKILL.md (Acceptance)
  - scripts/dlc-early-stop.js
  - scripts/dlc-evidence-ledger.js
  - fablize README (multi-story verification gate)
---

# evidence-gate

비trivial 작업의 완료를 **증거로 게이트**한다 — 요구를 test 가능한 항목으로 분해하고, 각 항목이 실행·관찰·통과로 충족될 때만 "완료". [[fablize-adopted-disciplines|fablize]]의 evidence gate 개념을 [[dlc-development-cycle|dlc]]에 차용한 것.

## 2층 구조
- **1차 (모델·단일 소스)**: plan `# Acceptance` 섹션. 각 항목 = `무엇이 충족되나` + `어떻게 검증(명령/관찰)` + `통과 기준`. dlc 16단계 Report 전 전 항목을 증거로 대조, 미충족이면 완료 금지(`status: blocked`/"미검증").
- **2차 (결정론적 보조)**: Stop hook `dlc-early-stop.js`. "파일 변경했는데 검증 기록 없음"을 감지해 **capped(1회)·fail-open**으로 경고. ledger(`dlc-evidence-ledger.js`가 PostToolUse로 기록)를 읽는다. hook 은 보조일 뿐 규약(SKILL)이 단일 소스.

## verification grounding
실행되는 산출물(HTML·SVG·게임·차트·CLI·서버)은 정적 점검(파싱 OK)이 아니라 **실제 실행해 출력을 관찰**한 증거를 acceptance 에 넣는다 — "well-formed ≠ correct".

## 왜 capped·fail-open
hard-block 은 trivial·예외에서 마찰·오작동(fablize 도 declarative offer 오탐 인정). 그래서 차단이 아니라 *유도* — 1회 경고 후 통과, `CLAUDE_DLC_EARLYSTOP_OFF=1` holdout. 강제 강도는 plan 규약이 지고 hook 은 누락 방지망.

## 연계
worktree 자동 진입은 [[dlc-wt-autoflow]], 차용 규율 전체는 [[fablize-adopted-disciplines]].
