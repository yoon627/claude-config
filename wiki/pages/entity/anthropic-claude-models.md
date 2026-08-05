---
title: anthropic-claude-models
category: entity
created: 2026-06-19
updated: 2026-08-05
sources:
  - claude-api skill (models.md, shared/model-migration.md)
  - https://support.claude.com/en/articles/15424964-claude-fable-5-on-your-plan
  - https://x.com/claudeai/status/2072402639644766602 (Fable 50% 정책)
  - https://www.vals.ai/benchmarks/swebench (Opus 5 vs Fable 5)
  - researcher 조사 2026-08-05 (본 세션)
---

# anthropic-claude-models

이 워크플로우가 model/effort 차등에 쓰는 Claude 모델들의 가격·능력·한도 사실. **기준: 2026-08-05** (가격·정책은 변할 수 있음 — 갱신은 `claude-api` skill로 재검증).

## 가격 (per 1M tokens, input/output) — Claude 5 세대
- **Fable 5** — $10 / $50. 1M context 기본. thinking 비활성화 불가.
- **Opus 5** (2026-07-24 출시) — $5 / $25 (Fable의 절반).
- **Sonnet 5** (2026-06-30 출시) — 인트로 $2 / $10 (2026-08-31까지), 이후 $3 / $15. **신규 tokenizer로 동일 텍스트가 ~1.3배 토큰** — 실효 격차는 표시가보다 작다.
- **Haiku 4.5** — $1 / $5.

구세대: Opus 4.8 $5/$25 · Sonnet 4.6 $3/$15 (참고용).

## Fable 5 구독 한도 (2026-07-20 확정)
- Max·Team Premium: **주간 한도의 최대 50%까지만 Fable 사용 가능** — 별도 버킷이 아니라 공유 풀에서 차감. Opus 대비 ~2배 가중 차감이라는 서술은 2차 출처만 확인(⚠️추정). 50% 소진 후 나머지는 Opus/Sonnet으로.
- Pro·Team Standard: 포함 접근 없음, usage credit($10/$50 per MTok) 종량제.
- Claude Code v2.1.170+ 필요. `/usage`에 "Fable covered by plan (50% weekly limit)" 표기.

## 벤치마크 구도 (Opus 5 출시 이후)
- **닫힌 단발 코딩: Opus 5 ≥ Fable 5** — SWE-bench Verified Opus 5 97.0% > Fable 5 95.0% (Vals). ARC-AGI-3 등 다수 벤치에서 Opus 5 우위.
- **Fable 5 순수 우위 = 장기·자율·모호 작업** — DeepSWE·Legal Agent 등. 공식 표현: "the longer and more complex the task, the larger its lead". 공식 구도: "Fable=스페셜리스트, Opus=엑스퍼트, Sonnet=제너럴리스트".
- Sonnet 5 "Opus급" 평가는 조건부 — 대부분 코딩에서 근접하나 백엔드·장기 자율 작업은 Opus 우위 보고 잔존.
- Fable 5 safety classifier: cyber flag→Opus 4.8, bio flag→Opus 5로 **자동 모델 전환**(v2.1.219+) — 장기 Fable 세션은 `/status`로 실제 모델 확인 가치.

## effort 지원
- Opus·Sonnet·Fable: `effort` 파라미터 지원(`low`~`xhigh`·`max`).
- **Haiku 4.5: effort 파라미터 미지원** — 상속 시 무시되어 안전([[claude-code-subagent-config]]).

## 정정 (재논의 방지)
- `opus[1m]`/`fable[1m]`(1M long-context)에 **long-context 프리미엄 가격은 없다**.
- Anthropic 권장 effort: 코딩·에이전트는 `xhigh`(기본값은 high), `max`는 "extremely hard, latency-insensitive" 한정.

## 연계
이 사실에 기반한 단계별 모델 배치는 [[model-stage-tiering]], Claude Code 쪽 선택 메커니즘은 [[claude-code-model-selection]], 과거 티어 결정은 [[subagent-model-effort-tiering]]→[[effort-global-xhigh]].
