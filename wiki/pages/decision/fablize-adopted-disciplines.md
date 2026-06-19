---
title: fablize-adopted-disciplines
category: decision
created: 2026-06-19
updated: 2026-06-19
sources:
  - fablize README (fivetaku/fablize, MIT)
  - skills/dlc/SKILL.md
  - scripts/dlc-task-router.js
---

# fablize-adopted-disciplines

fablize(Opus 를 Fable 처럼 "끝까지·증거로" 일하게 하는 플러그인)에서 **검증된 규율만** dlc 에 차용한 결정. **플러그인은 설치하지 않고 개념을 직접 구현**(repo 스타일·한국어·dlc 통합, 외부 의존·hook 충돌 회피).

## 차용한 것 (procedure — 전이 가능)
- **verification grounding** — 실행 산출물은 실제 실행·관찰. → [[evidence-gate]].
- **multi-story evidence gate** — 분해 + 증거 없는 "done" 거부. → [[evidence-gate]].
- **investigation protocol** — 재현 → 가설 3개+ 경쟁 → 인과사슬. dlc 조사 프로토콜 + `dlc-task-router.js` 가 디버깅 키워드에 주입.
- **early-stop hook** — "할게요" 하고 안 하기 방지(capped·fail-open). `dlc-early-stop.js`.
- **per-task router** — 작업 유형별 규율 주입(UserPromptSubmit hook).

## 차용 안 한 것 (capability — 전이 불가, fablize 도 명시)
- out-of-spec 결함 발견 · 개방형 창의 · **self-driven 개선 깊이**. harness 로 못 옮기는 모델 능력. → 자기개선은 [[self-diagnosis-and-improvement-status]] 의 *증거기반 finding 최소형*까지만(발견·기록), 자동 수정은 안 함.

## 한계
fablize 효과 수치는 small single-family self-measurement — 방향은 타당하나 도입 효과는 사후 관찰 대상. early-stop 은 declarative offer 오탐 가능(질문형으로 회피).

## 연계
완료 게이트 [[evidence-gate]], worktree 자동화 [[dlc-wt-autoflow]], dlc 본체 [[dlc-development-cycle]].
