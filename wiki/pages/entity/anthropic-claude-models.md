---
title: anthropic-claude-models
category: entity
created: 2026-06-19
updated: 2026-09-29
sources:
  - https://platform.claude.com/docs/en/about-claude/models/overview (현재·legacy 목록, 권장 시작 모델, 기본 effort, 은퇴 하한 — 2026-09-27 조회)
  - https://platform.claude.com/docs/en/about-claude/pricing (가격·캐시 배율·Sonnet 5 가격 각주 — 2026-09-27 조회)
  - https://platform.claude.com/docs/en/build-with-claude/effort (모델별 기본·권장 effort — 2026-09-27 조회)
  - https://code.claude.com/docs/en/model-config (Claude Code 최소 버전·effort 해석·안전 분류기 폴백 — 2026-09-27 조회, ultracode 토글 — 2026-09-29 조회)
  - https://code.claude.com/docs/en/workflows (ultracode 키워드·설정과 effort 레벨 — 2026-09-29 조회)
  - https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md (2.1.284 — ultracode 가 `/effort` 별도 토글로, `xhigh` 강제 해제)
  - https://support.claude.com/en/articles/15424964-claude-fable-5-on-your-plan (플랜별 Fable 포함 범위·최소 버전)
  - https://www.anthropic.com/claude-opus-5-5 (Opus 5.5 발표 — 벤치 수치는 vendor 발표)
  - https://www.vals.ai/benchmarks/swebench (2026-08 당시 Opus 5 대 Fable 5)
  - researcher 조사 2026-08-05, workflow 교차 검증 2026-09-27(wf_83e9d53b-c4e)·2026-09-29(wf_0b281262-6a0, ultracode — 설치 바이너리 2.1.281~2.1.284 비교 포함)
---

# anthropic-claude-models

이 워크플로우가 model/effort 차등에 쓰는 Claude 모델들의 가격·능력·한도 사실. **기준: 2026-09-27** (가격·정책은 변할 수 있음 — 갱신은 공식 models overview·pricing 으로 재검증). Sonnet 5.5·Haiku 5.5 는 Opus 5.5 발표에서 "coming weeks" 로 예고만 됐고 2026-09-27 에는 목록에 없다 — 출시되면 이 페이지는 다시 낡는다.

> [!open] 2026-09-29: Sonnet 5.5 가 나왔다 — CHANGELOG 2.1.284 *"Added Claude Sonnet 5.5 (`claude-sonnet-5-5`), now the default Sonnet model on the Anthropic API"*, model-config *"Opus 5.5 and Sonnet 5.5 default to `medium`"*. 아래 라인업·가격·`sonnet` 별칭 해석·researcher(`model: sonnet`) 영향은 아직 반영하지 않았다(재검증 필요).

## 현재 라인업 (per 1M tokens, input/output)
- **Fable 5.1** (`claude-fable-5-1`, 2026-09-01) — $10 / $50, 캐시 읽기 $0.25(0.025x). 1M context, 최대 출력 128K. adaptive thinking 항상 켜짐. 기본 effort `high`.
- **Opus 5.5** (`claude-opus-5-5`, 2026-09-22) — $4 / $20, 캐시 읽기 $0.20(0.05x). 1M context, 최대 출력 128K. adaptive thinking 항상 켜짐(끌 수 없음 — 400). **기본 effort `medium`**(effort 를 지원하는 다른 현재 모델은 `high`).
- **Sonnet 5** (`claude-sonnet-5`, 2026-06-30) — $2 / $10. 출시 때 2026-08-31 까지의 인트로 가격이라 했으나 **표준 가격이 됐고 9-01 의 $3/$15 인상은 "will not occur"**(pricing 각주). 1M context. 기본 effort `high`. 4.7 이후 tokenizer 라 같은 텍스트가 ~30% 더 많은 토큰.
- **Haiku 4.5** (`claude-haiku-4-5-20251001`) — $1 / $5. 200K context. effort 미지원(extended thinking). **은퇴 "Not sooner than October 15, 2026"** — 이 repo 에 haiku 고정은 없다(2026-09-27 확인).

공식 권장: *"If you're unsure which model to use, start with Claude Opus 5.5 for most workloads. Use Claude Fable 5.1 for demanding reasoning and long-horizon agentic work, or when your evals on Claude Opus 5.5 at higher effort still fall short."*(models overview)

Legacy(still available): Fable 5 $10/$50(캐시 읽기 $1) · Opus 5 $5/$25 · Opus 4.8·4.7·4.6·4.5 $5/$25 · Sonnet 4.6·4.5 $3/$15.

## Fable 구독 한도
- Max·Team/Enterprise premium: Fable 5 와 5.1 모두 포함, **주간 한도의 최대 50% 까지**(공유 풀에서 차감). Pro·Team standard: 포함 접근 없음, usage credit 종량제(support 문서).
- Claude Code 최소 버전: Fable 5 는 v2.1.170+.

> [!conflict] Fable 5.1 의 Claude Code 최소 버전 — model-config·advisor 문서는 *"Fable 5.1 requires Claude Code v2.1.257 or later"*, support 문서는 v2.1.255+ 로 적는다(2026-09-27). 높은 쪽(v2.1.257)을 기준으로 삼는다. Opus 5.5 는 v2.1.280+(model-config).

## 성능 구도
- **현재(Opus 5.5 출시 이후)**: 공식 문서는 Opus 5.5 를 기본 출발점, Fable 5.1 을 "demanding reasoning and long-horizon agentic work" 용으로 둔다. Opus 5.5 발표(vendor)는 Opus 5.5 가 대부분의 작업에서 Fable 5.1 수준이고 발표에 실린 코딩 벤치(Terminal-Bench 4.0 66.4 대 55.8, CursorBench 4.0 57.8 대 51.8 등)에서 앞선다고 적는다 — 독립 측정(Vals 등)은 아직 확인하지 않았다.
- **2026-08 당시(Opus 5 대 Fable 5, 역사 기록)**: 닫힌 단발 코딩은 Opus 5 ≥ Fable 5(SWE-bench Verified 97.0% 대 95.0%, Vals), Fable 5 우위는 장기·자율·모호 작업("the longer and more complex the task, the larger its lead"). 이 구도가 [[model-stage-tiering]] 결정(2026-08-05)의 근거였다.
- Sonnet 5 "Opus급" 평가는 조건부 — 대부분 코딩에서 근접하나 백엔드·장기 자율 작업은 Opus 우위 보고 잔존(2026-08 조사).
- 안전 분류기 폴백(Claude Code, model-config): Fable 5.1·Fable 5·Opus 5.5 는 biology 플래그 → Opus 5, cybersecurity 플래그 → Opus 4.8 로 재실행. Opus 5 는 cybersecurity → Opus 4.8, biology 는 거절. `switchModelsOnFlag: false` 면 자동 전환 대신 세션이 멈추고 선택지를 준다(이 환경의 user settings 는 `false`). 장기 세션은 `/status` 로 실제 모델 확인.

## effort
- 지원: Fable·Opus·Sonnet 5/4.6 은 `effort` 지원(`low`~`max`, `xhigh` 는 모델 한정). **Haiku 4.5 는 미지원** — 상속 시 무시되어 안전([[claude-code-subagent-config]]).
- 모델별 기본값(API): Opus 5.5 `medium`, 나머지 지원 모델 `high`. Opus 5.5 는 *"a request that omits `effort` runs one level lower than it did on Claude Opus 5"* 이고 이전 모델 설정을 옮기지 말고 effort sweep 을 하라고 권한다. Fable 5.1·Fable 5·Opus 5 는 "Start with `high`, the default", Opus 4.7·4.8 은 "Start with `xhigh` for coding and agentic use cases".
- Claude Code: 명시 선택(`CLAUDE_CODE_EFFORT_LEVEL`·`--effort`·`/effort`) > settings(모델별 `modelSettings` 또는 최상위 `effortLevel`) > 모델 기본값(Claude Code 에서는 `high`, Opus 5.5·Sonnet 5.5 `medium`, Opus 4.7 `xhigh`). 단 *"Opus 5.5 starts at `medium` unless one of the sources above sets a level for it, and a top-level `effortLevel` in your user settings file doesn't count for Opus 5.5."* subagent 는 세션 레벨을 물려받고, frontmatter `effort` 가 세션 레벨을 덮는다(env 는 못 이기고 상한 설정에 묶인다 — [[claude-code-model-selection]]).
- ultracode(v2.1.284+)는 effort 레벨이 아니라 `/effort` 안의 별도 토글이다: *"Turning ultracode on or off with `/effort` or the `ultracode` setting leaves the effort level unchanged."* 켜는 경로는 `/effort ultracode`(끄기 `… off`)·슬라이더 `Tab`·설정 `"ultracode": true`. 예외로 *"The `--effort ultracode` flag and the Agent SDK `effortLevel: "ultracode"` value turn it on and also set the level to `xhigh`."* 프롬프트 키워드는 레벨을 바꾸지 않는다 — *"To run a single task as a workflow without changing the session's effort level, include the keyword `ultracode` in your prompt."* `CLAUDE_CODE_EFFORT_LEVEL`·effort 상한이 레벨을 정하면 ultracode 는 그 레벨에서 켜진 채 남고, 모델이 `xhigh` 를 지원하지 않거나 workflows 가 꺼져 있으면 쓸 수 없다(model-config·workflows, 2026-09-29 조회).
  - 이전 동작(v2.1.283 이하): *"Before v2.1.284, turning on ultracode set the session to `xhigh` effort, picking another level turned it off, and an effort cap below `xhigh` made it unavailable."* 2026-09-27 이 줄의 "ultracode 설정이 꺼져 있을 때 — 켜면 `xhigh` 를 보낸다" 는 이 동작 기준이었다. 설치 바이너리 비교로도 확인했다 — 2.1.281·2.1.283 에는 설정 `ultracode: true` 일 때 effort 기본값을 `xhigh` 로 바꾸는 분기가 있고 2.1.284 에는 없다(workflow wf_0b281262-6a0).

## 정정 (재논의 방지)
- `opus[1m]`/`fable[1m]`(1M long-context)에 **long-context 프리미엄 가격은 없다** — 4.6 이후 모델은 1M 전체가 표준 가격(pricing).
- `max` effort 는 "Absolute maximum capability with no constraints on token spending" 이고, Opus 4.7 표는 "Reserve for frontier problems" 라고 적는다(2026-08 이 페이지의 "extremely hard, latency-insensitive" 인용은 현 문서에 없다).

## 연계
이 사실에 기반한 단계별 모델 배치는 [[model-stage-tiering]], Claude Code 쪽 선택 메커니즘은 [[claude-code-model-selection]], 과거 티어 결정은 [[subagent-model-effort-tiering]]→[[effort-global-xhigh]].
