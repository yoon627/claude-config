---
title: model-stage-tiering
category: decision
created: 2026-08-05
updated: 2026-08-11
sources:
  - researcher 조사 2026-08-05 ×2 (공식 권장·커뮤니티 관행 — 본 세션)
  - memory model-strategy-fable-plan-opus-impl (2026-07-04 원결정)
  - https://support.claude.com/en/articles/15424964-claude-fable-5-on-your-plan
  - researcher 조사 2026-08-06 (subagent frontmatter model 정본·precedence·폴백)
  - https://code.claude.com/docs/en/sub-agents
  - https://github.com/anthropics/claude-code/issues/45169 ([1m] stripping)
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

> [!done] 구현 완료 (2026-08-06, subagent-model-pinning)
> `agents/*.md` 를 reviewer 3종 `model: opus`·researcher `model: sonnet` 으로 고정하고 [[effort-global-xhigh]] 를 개정했다. 조사로 확정한 부수 사실: subagent frontmatter 에 `[1m]` 접미사는 쓰지 않는다(공식 미기재 + stripping 버그 anthropics/claude-code#45169) — Opus 5 가 API·Max/Team/Enterprise 에서 자동 1M 이라 불필요하다. 명시 pin 은 **자동 폴백이 없어** Opus 한도 소진 시 리뷰 게이트가 멈추므로, 비상 레버는 `CLAUDE_CODE_SUBAGENT_MODEL`([[claude-code-model-selection]]).
