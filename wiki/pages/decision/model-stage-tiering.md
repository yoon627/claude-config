---
title: model-stage-tiering
category: decision
created: 2026-08-05
updated: 2026-08-05
sources:
  - researcher 조사 2026-08-05 ×2 (공식 권장·커뮤니티 관행 — 본 세션)
  - memory model-strategy-fable-plan-opus-impl (2026-07-04 원결정)
  - https://support.claude.com/en/articles/15424964-claude-fable-5-on-your-plan
---

# model-stage-tiering

dlc 단계별 모델 배치 결정 (2026-08-05, 사용자 승인). 2026-07-04 memory 결정("Fable=계획, 구현=opus")을 Opus 5 출시·Fable 50% 캡 확정 이후 재검증·확장한 것.

## 결정

| dlc 단계 | 모델 | 근거 |
|---|---|---|
| Explore·조사 (researcher) | **sonnet** | 검색·요약엔 충분, 풀 소모 최소 (Haiku는 effort 미지원이라 제외) |
| Plan·설계·아키텍처·모호한 root-cause | **fable** | Fable이 유일하게 확실히 이기는 구간 — 주간 50% 캡을 여기에만 |
| plan-review / code-review / architecture-review | **opus** | 리뷰 품질이 병목, Fable 불필요 (+Codex 병행은 [[claude-codex-collaboration]] 그대로) |
| 구현 | 기본 **opus**, §10 plan이 촘촘한 닫힌 구현은 **sonnet** | 닫힌 코딩은 Opus 5 ≥ Fable ([[anthropic-claude-models]]); Sonnet "Opus급"은 조건부라 기본은 opus |
| simplify·verify | 세션 모델 그대로 | 전환 비용 > 이득 |

세션 흐름: **Fable 세션에서 plan(+plan-review)까지 → plan commit → `/model opus` 세션에서 `/c`로 구현** — [[plan-handoff]]가 전환 비용을 ~0으로 만드는 것이 전제.

## 이유
1. Fable 50% 주간 캡(공유 풀 차감)에서 실행급 작업에 캡을 태우면 계획급 기회를 놓친다 — 커뮤니티 공통 실패 패턴.
2. 공식 벤치·fablize 실험 모두 "닫힌 구현은 Opus로 충분" 수렴.
3. 커뮤니티 표준(Fable=plan/audit, Sonnet=구현, Haiku=탐색) 및 공식 opusplan/advisor 구도와 정합([[claude-code-model-selection]]).

## 실험 옵션 (채택 아님, 후보)
- 구현 세션 "Sonnet main + Opus advisor"(`/advisor`) — 공식 측정 Sonnet 단독 대비 +2.7pp·비용 −11.9%.
- Fable-as-advisor 롤아웃 시 "Sonnet main + Fable advisor" 재평가.
- "luna max"는 Claude가 아니라 OpenAI GPT-5.6 `gpt-5.6-luna` + max reasoning effort — Codex 경유 보조 구현에만 해당, 주 구현 비채택(dlc 파이프라인 이탈).

> [!open] 구현 대기: agents/*.md `model: inherit`(→[[effort-global-xhigh]]의 2026-07-04 결정)을 reviewer류 `model: opus`·researcher `model: sonnet`으로 고정하는 작업 — inherit 결정의 전제(Fable 가용성 변동 대비)가 Fable 기본모델+50% 캡 시대엔 역효과(리뷰가 Fable로 돎). 별도 worktree 작업으로 적용 시 effort-global-xhigh 페이지도 개정할 것.
