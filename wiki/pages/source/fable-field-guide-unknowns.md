---
title: fable-field-guide-unknowns
category: source
created: 2026-07-16
updated: 2026-07-16
sources:
  - https://x.com/trq212/article/2073100352921215386 (Thariq, "A Field Guide to Fable: Finding Your Unknowns", 2026-07-04)
  - plans/2026-07-07-unknowns-pass (Fable 계획 세션 분석)
---

# fable-field-guide-unknowns

Thariq(Anthropic Claude Code 팀) "A Field Guide to Fable: Finding Your Unknowns"(2026-07-04) 요약. 핵심 논지: **작업의 진짜 위험은 "모르는 줄도 모르는 것(unknown unknowns)"이며, 구현 전에 이 unknowns 를 능동 발굴하라.** 코드 짜기 전 요구·취향·제약의 공백을 좁히는 것이 재작업 비용을 줄인다.

> [!open] 원문은 x.com 인증 벽(HTTP 402)이라 재fetch 불가. 이 요약은 [[plan-handoff|Fable 계획 세션]]이 원문을 읽고 캡처한 분석(plans/2026-07-07-unknowns-pass)을 2차 출처로 정리 — 원문 미확인 세부는 단정하지 않는다.

## unknowns 사분면
안다/모른다 × 알고 있음을 아느냐로 4분면(고전 known/unknown 프레이밍):
- **known knowns** — 요구·사실 명확 → 바로 진행.
- **known unknowns** — 모른다는 걸 아는 공백 → 질문·조사(인터뷰).
- **unknown knowns** — 사용자가 아는데 안 밝힌 암묵 지식 → 프로토타입·예시로 끌어냄.
- **unknown unknowns** — 양쪽 다 모르는 사각 → 낯선 영역 브리핑·deviation 관찰로 노출.

## 발굴 기법
- **interviews / question prioritization** — 설계·완료기준을 바꿀 질문을 **우선순위로, 한 번에 하나씩** 인터뷰하듯 공백을 좁힌다.
- **blind-spot briefing** — 사용자가 낯선 영역이면 질문 반복 대신 **함정·"좋음"의 기준·과거 결정을 먼저 브리핑**한다.
- **prototype-first** — 취향·시각 산출물은 구현 전 **저비용 변형을 먼저 제시**해 반응(unknown knowns)을 끌어낸다.
- **quizzes** — 큰·낯선 변경은 "변경 이해 리포트+퀴즈"로 사용자의 이해 공백을 노출.
- **deviations** — 계획과 실제의 어긋남을 관찰해 숨은 제약을 발견.

이 기법들이 [[dlc-development-cycle]] 의 명확화 게이트·grounding 에 어떻게 반영됐는지는 [[unknowns-discovery]] 의 매핑 표 참조.
