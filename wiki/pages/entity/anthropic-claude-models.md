---
title: anthropic-claude-models
category: entity
created: 2026-06-19
updated: 2026-06-19
sources:
  - claude-api skill (models.md, shared/model-migration.md)
  - plans/2026-06-18-subagent-model-effort/subagent-model-effort-plan.md
---

# anthropic-claude-models

이 워크플로우가 model/effort 차등에 쓰는 Claude 모델들의 가격·능력 사실. **기준: 2026-06** (가격·정책은 변할 수 있음 — 갱신은 `claude-api` skill로 재검증).

## 가격 (per 1M tokens, input/output)
- **Opus 4.8** — $5 / $25. cache read 0.1×.
- **Sonnet 4.6** — $3 / $15 (Opus 대비 ~40% 저렴 — 1/5 아님).
- **Haiku 4.5** — $1 / $5 (Opus 대비 ~80% 저렴).

## effort 지원
- Opus·Sonnet·Fable: `effort` 파라미터 지원(max까지).
- **Haiku 4.5: effort 파라미터 미지원** — extended thinking 자체는 budget_tokens 방식으로 지원하나 effort는 제외. (상속 시 무시되어 안전 — [[claude-code-subagent-config]])

## 정정 (재논의 방지)
- `opus[1m]`(1M long-context)에 **long-context 프리미엄 가격은 없다**(별도 표기 안 함).
- Anthropic 권장 effort: Opus는 `high` 기본, `max`는 "extremely hard, latency-insensitive" 한정.

## 연계
이 사실에 기반한 모델 티어 결정은 [[subagent-model-effort-tiering]], effort 레버 함정은 [[effort-os-env-single-source]].
