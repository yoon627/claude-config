---
title: unknowns-discovery
category: concept
created: 2026-07-16
updated: 2026-07-16
sources:
  - [[fable-field-guide-unknowns]]
  - plans/2026-07-07-unknowns-pass (dlc 반영 설계)
---

# unknowns-discovery

구현 전 **unknowns(특히 unknown unknowns)를 능동 발굴**하는 방법론 — [[fable-field-guide-unknowns]] 의 기법을 이 repo 의 [[dlc-development-cycle]] 에 매핑한 것. 원리: 요구·취향·제약의 공백은 질문만으로 안 좁혀질 때가 있고(사용자도 답 못 함), 그럴 땐 브리핑·프로토타입·관찰로 노출시킨다.

## 기법 → dlc 현행 대응
| 기법(원문 명명) | dlc 반영 위치 | 상태 |
|---|---|---|
| Interviews | 요구사항 명확화 게이트(체크리스트 4항·≤2라운드) + "질문 우선순위"(설계·acceptance 바꾸는 것 먼저·1개씩) | 기존(+이번 우선순위) |
| References | Explore(기존 파일·같은 레이어 스타일 참조) + 사용자 제공 예시 | 기존 |
| Blind spot scans | 명확화 절 "blind-spot pass"(낯선 영역 브리핑 후 질문 재구성) | 신규(이번) |
| Mockups (프로토타입-우선) | 명확화 절 프로토타입-우선 + router `[dlc:grounding]` 주입(취향·시각은 구현 전 변형 2~4종) | 신규(이번) |
| Explainer & Quiz | Report recap "변경 이해 리포트+퀴즈" 옵션(§3-6) | 기존(#79 finish-recap) |
| Implementation Notes (deviations 기록) | §10 [[plan-handoff|plan]] 진행 중 동기화(계획↔실제 어긋남 즉시 반영) | 기존 |

## 원칙
- **강제 아님·판단은 모델** — 프로토타입-우선은 "고려 제안"(모든 render 가 취향성은 아님). blind-spot·질문우선순위는 명확화 ≤2라운드 안에서(새 단계 아님).
- **질문 vs 브리핑·추천 경계** — 무엇(요구·목표·산출물)이 빠졌으면 질문, 방법만 갈리면 분석 후 추천, 사용자도 모를 영역이면 브리핑. 상세는 [[dlc-development-cycle]] 명확화 게이트.

> [!open] 원문(x.com) 재fetch 불가 — 매핑은 Fable 세션 분석 기준. 추가 기법 반영은 근거 확인 후.
