---
title: anthropic-claude-models
category: entity
created: 2026-06-19
updated: 2026-09-29
sources:
  - https://platform.claude.com/docs/en/about-claude/models/overview (현재·legacy 목록, 권장 시작 모델, 기본 effort, 은퇴 하한 — 2026-09-27 조회, Sonnet 5.5·Haiku 5.5 상태 — 2026-09-29 조회)
  - https://platform.claude.com/docs/en/about-claude/models/sonnet-5-5/overview (Sonnet 5.5 사양·effort 권장 — 2026-09-29 조회)
  - https://platform.claude.com/docs/en/about-claude/pricing (가격·캐시 배율·Sonnet 5 가격 각주 — 2026-09-27 조회, Sonnet 5.5·캐시 읽기 배수 — 2026-09-29 조회)
  - https://platform.claude.com/docs/en/build-with-claude/effort (모델별 기본·권장 effort — 2026-09-27 조회, Sonnet 5.5 — 2026-09-29 조회)
  - https://platform.claude.com/docs/en/about-claude/model-deprecations (Sonnet 5.5·Sonnet 5 은퇴 하한 — 2026-09-29 조회)
  - https://code.claude.com/docs/en/model-config (Claude Code 최소 버전·effort 해석·안전 분류기 폴백 — 2026-09-27 조회, ultracode 토글·별칭 표·1M 목록·기본 effort·`/effort` 저장·Sonnet 5.5 폴백 — 2026-09-29 조회)
  - https://code.claude.com/docs/en/prompt-caching (effort 변경 시 캐시 유지 모델 — 2026-09-29 조회)
  - https://code.claude.com/docs/en/workflows (ultracode 키워드·설정과 effort 레벨 — 2026-09-29 조회)
  - https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md (2.1.284 — ultracode 가 `/effort` 별도 토글로, `xhigh` 강제 해제)
  - https://support.claude.com/en/articles/15424964-claude-fable-5-on-your-plan (플랜별 Fable 포함 범위·최소 버전)
  - https://www.anthropic.com/claude-opus-5-5 (Opus 5.5 발표 — 벤치 수치는 vendor 발표)
  - https://www.vals.ai/benchmarks/swebench (2026-08 당시 Opus 5 대 Fable 5)
  - researcher 조사 2026-08-05·2026-09-29(Sonnet 5.5), workflow 교차 검증 2026-09-27(wf_83e9d53b-c4e)·2026-09-29(wf_0b281262-6a0, ultracode — 설치 바이너리 2.1.281~2.1.284 비교 포함)
---

# anthropic-claude-models

이 워크플로우가 model/effort 차등에 쓰는 Claude 모델들의 가격·능력·한도 사실. **모델 버전·별칭 해석·모델 목록·모델별 기본 effort 는 이 페이지에만 적는다** — 다른 페이지는 버전명 없이 이 페이지를 링크한다(2026-09-29 결정, 새 모델이 나올 때 고칠 곳을 하나로). 단 날짜 붙은 기록·측정·결정 근거와 한 모델에 대한 고정 사실(그 모델의 단가 등)은 다른 페이지에서도 버전명을 그대로 둔다 — 별칭으로 바꾸면 무엇을 쟀는지, 어느 모델에 대한 결정인지 모호해진다. 공식 문서가 완전한 표를 유지하는 목록(advisor 허용 조합 등)은 여기에도 옮기지 않고 그 문서를 링크한다. 조회일은 절마다 적는다(가격·정책은 변할 수 있음 — 갱신은 공식 models overview·pricing·model-config 로 재검증).

새 모델이 나오면 이 페이지를 고친 뒤 버전에 묶인 결정을 다시 본다: [[effort-global-xhigh]](M12 — 특정 opus 모델의 effort 레벨), [[model-stage-tiering]](단계별 별칭 배치와 그 근거), 아래 `[!open]`(고정 subagent 의 레벨·폴백).

> [!open] 2026-09-29 Sonnet 5.5 출시 뒤 남은 미확인 — researcher(`model: sonnet`)는 v2.1.284+ 에서 Sonnet 5.5 로 돈다(아래 별칭 표). ❌ 그 researcher 가 받는 effort 레벨: 세션 모델과 다른 모델로 고정된 subagent 가 어떤 레벨을 받는지는 문서에 없다(Sonnet 5.5 는 Claude Code 기본 `medium`이고 레벨이 재보정됐다). ❌ `switchModelsOnFlag: false`(이 환경의 user settings)에서 subagent 요청이 cybersecurity 플래그를 받을 때 멈추는지·실패하는지 — researcher 가 CVE 조사를 맡는다.

## 현재 라인업 (per 1M tokens, input/output — 2026-09-27 조회, Sonnet 5.5·Haiku 5.5 는 2026-09-29)
- **Fable 5.1** (`claude-fable-5-1`, 2026-09-01) — $10 / $50, 캐시 읽기 $0.25(0.025x). 1M context, 최대 출력 128K. adaptive thinking 항상 켜짐. 기본 effort `high`.
- **Opus 5.5** (`claude-opus-5-5`, 2026-09-22) — $4 / $20, 캐시 읽기 $0.20(0.05x). 1M context, 최대 출력 128K. adaptive thinking 항상 켜짐(끌 수 없음 — 400). **기본 effort `medium`**(API 기준 — effort 를 지원하는 다른 현재 모델은 `high`, Claude Code 기본값은 아래 effort 절).
- **Sonnet 5.5** (`claude-sonnet-5-5`, 2026-09-28) — $2 / $10(Sonnet 5 와 같음), 캐시 읽기 $0.20(0.1x). 1M context, 최대 출력 128K. adaptive thinking. **기본 effort: API `high`, Claude Code·앱 `medium`**. Claude Code v2.1.284+. 은퇴 "Not sooner than September 28, 2027".
- **Haiku 4.5** (`claude-haiku-4-5-20251001`) — $1 / $5. 200K context. effort 미지원(extended thinking). **은퇴 "Not sooner than October 15, 2026"** — 이 repo 에 haiku 고정은 없다(2026-09-27 확인). Haiku 5.5 는 "in the coming weeks" 로 예고만 됐다(2026-09-29 미출시).

캐시 읽기 배수(pricing, 2026-09-29 조회): *"0.1x base input price (0.025x on Claude Fable 5.1 and Claude Mythos 5.1; 0.05x on Claude Opus 5.5)"*.

공식 권장: *"If you're unsure which model to use, start with Claude Opus 5.5 for most workloads. Use Claude Fable 5.1 for demanding reasoning and long-horizon agentic work, or when your evals on Claude Opus 5.5 at higher effort still fall short."*(models overview)

Legacy(still available): Sonnet 5 $2/$10(출시 때 인트로 가격이라 했으나 표준 가격이 됐고 9-01 의 $3/$15 인상은 "will not occur" — pricing 각주. 4.7 이후 tokenizer 라 같은 텍스트가 ~30% 더 많은 토큰. 은퇴 "Not sooner than June 30, 2027") · Fable 5 $10/$50(캐시 읽기 $1) · Opus 5 $5/$25 · Opus 4.8·4.7·4.6·4.5 $5/$25 · Sonnet 4.6·4.5 $3/$15.

## 별칭 해석·1M (Claude Code model-config, 2026-09-29 조회)
| provider | `opus` | `sonnet` |
|---|---|---|
| Anthropic API | Opus 5.5 | Sonnet 5.5 |
| Claude Platform on AWS | Opus 5.5 | Sonnet 4.6 |
| Amazon Bedrock, Google Cloud's Agent Platform | Opus 5.5 | Sonnet 4.5 |
| Microsoft Foundry | Opus 4.6 | Sonnet 4.5 |

- 이 표는 Claude Code 버전을 탄다 — Sonnet 5.5 는 v2.1.284+ 필요다(v2.1.284 CHANGELOG 가 Sonnet 5.5 를 기본 Sonnet 으로 추가). 직전 클라이언트(2026-09-27 조회 당시 v2.1.283 이하)의 Anthropic API `sonnet` 은 Sonnet 5 였고, 그 클라이언트에서는 effort 저장값이 없으면 Sonnet 5 기본값 `high` 로 돈다.
- `fable` → Fable 5.1(`ANTHROPIC_DEFAULT_FABLE_MODEL` 이 없을 때, 2026-09-27 조회). `best` 는 Fable 접근권이 있으면 `fable` 과 같은 모델, 없으면 `opus` 와 같은 모델. `default` 는 모델 override 를 지우고 계정의 런타임 기본값으로 돌아가는 특수값이다.
- native 1M: *"On the Anthropic API, Fable 5.1, Fable 5, Sonnet 5 and later, and Opus 4.7 and later run with the 1M window on every plan, including Pro."* — `[1m]` 변형을 고를 필요가 없다. 200K 로 떨어지는 조건은 [[claude-code-model-selection]].

## Fable 구독 한도
- Max·Team/Enterprise premium: Fable 5 와 5.1 모두 포함, **주간 한도의 최대 50% 까지**(공유 풀에서 차감). Pro·Team standard: 포함 접근 없음, usage credit 종량제(support 문서).
- Claude Code 최소 버전: Fable 5 는 v2.1.170+.

> [!conflict] Fable 5.1 의 Claude Code 최소 버전 — model-config·advisor 문서는 *"Fable 5.1 requires Claude Code v2.1.257 or later"*, support 문서는 v2.1.255+ 로 적는다(2026-09-27). 높은 쪽(v2.1.257)을 기준으로 삼는다. Opus 5.5 는 v2.1.280+(model-config).

## 성능 구도
- **현재(Opus 5.5 출시 이후)**: 공식 문서는 Opus 5.5 를 기본 출발점, Fable 5.1 을 "demanding reasoning and long-horizon agentic work" 용으로 둔다. Opus 5.5 발표(vendor)는 Opus 5.5 가 대부분의 작업에서 Fable 5.1 수준이고 발표에 실린 코딩 벤치(Terminal-Bench 4.0 66.4 대 55.8, CursorBench 4.0 57.8 대 51.8 등)에서 앞선다고 적는다 — 독립 측정(Vals 등)은 아직 확인하지 않았다.
- **2026-08 당시(Opus 5 대 Fable 5, 역사 기록)**: 닫힌 단발 코딩은 Opus 5 ≥ Fable 5(SWE-bench Verified 97.0% 대 95.0%, Vals), Fable 5 우위는 장기·자율·모호 작업("the longer and more complex the task, the larger its lead"). 이 구도가 [[model-stage-tiering]] 결정(2026-08-05)의 근거였다.
- Sonnet 5 "Opus급" 평가는 조건부 — 대부분 코딩에서 근접하나 백엔드·장기 자율 작업은 Opus 우위 보고 잔존(2026-08 조사).
- 안전 분류기 폴백(Claude Code, model-config — 2026-09-27 조회, Sonnet 5.5 는 2026-09-29): Fable 5.1·Fable 5·Opus 5.5 는 biology 플래그 → Opus 5, cybersecurity 플래그 → Opus 4.8 로 재실행. Opus 5 는 cybersecurity → Opus 4.8, biology 는 거절. Sonnet 5.5 는 cybersecurity → Sonnet 5, biology 는 거절(*"Sonnet 5.5 has no biology fallback model"*). `switchModelsOnFlag: false` 면 자동 전환 대신 세션이 멈추고 선택지를 준다(이 환경의 user settings 는 `false`). 장기 세션은 `/status` 로 실제 모델 확인.

## effort
- 지원: Fable·Opus·Sonnet(5.5·5·4.6) 은 `effort` 지원(`low`~`max`, `xhigh` 는 모델 한정 — Sonnet 5.5 는 다섯 단계 모두). **Haiku 4.5 는 미지원** — 상속 시 무시되어 안전([[claude-code-subagent-config]]).
- 모델별 기본값(API): Opus 5.5 `medium`, 나머지 지원 모델 `high`(Sonnet 5.5 포함 — Claude Code 기본값은 다르다, 아래). Opus 5.5 는 *"a request that omits `effort` runs one level lower than it did on Claude Opus 5"* 이고 이전 모델 설정을 옮기지 말고 effort sweep 을 하라고 권한다. Sonnet 5.5 도 *"Its levels are recalibrated, so a level doesn't produce the same amount of thinking as the same level on Claude Sonnet 5. Run a fresh effort sweep"* 이고, *"Start with `high` unless your workload is agentic or latency-sensitive. For agentic coding and multistep tool use, start with `medium` for well-specified tasks and move to `high` for harder or longer ones"* 라고 권한다(2026-09-29). Fable 5.1·Fable 5·Opus 5 는 "Start with `high`, the default", Opus 4.7·4.8 은 "Start with `xhigh` for coding and agentic use cases".
- Claude Code: 명시 선택(`CLAUDE_CODE_EFFORT_LEVEL`·`--effort`·`/effort`) > settings(모델별 `modelSettings` 또는 최상위 `effortLevel`) > 모델 기본값(Claude Code 에서는 `high`, Opus 5.5·Sonnet 5.5 `medium`, Opus 4.7 `xhigh`). **user settings 의** 최상위 `effortLevel` 은 `/effort` 의 옛 저장 형식이라(*"the older form `/effort` wrote before Claude Code saved levels per model"*) *"keeps applying where it applied before, on Opus 5, Fable 5.1, and earlier models, while Opus 5.5 and models released after it start at their own default until you choose a level for them with `/effort` or the `/model` picker."* 반면 *"A top-level `effortLevel` in project, local, or managed settings, or one passed with `--settings`, applies to every model."* 지금 `/effort` 는 레벨을 `modelSettings` 에 **모델별로** 저장한다 — 슬라이더·picker 에서 `Enter` 는 저장, `s` 는 이번 세션만(v2.1.257+) (2026-09-29 조회). subagent 는 세션 레벨을 물려받고, frontmatter `effort` 가 세션 레벨을 덮는다(env 는 못 이기고 상한 설정에 묶인다 — [[claude-code-model-selection]]).
- `/effort` 변경과 prompt cache: 대부분 모델은 레벨마다 캐시가 따로라 무효화된다. *"On Opus 5.5, Sonnet 5.5, and Fable 5.1 with an API key or a Claude subscription, changing effort keeps the cache"* — Amazon Bedrock·Google Cloud's Agent Platform·Claude apps gateway, `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` 설정, 조직의 HIPAA 구성에서는 해당하지 않는다. v2.1.260 전에는 Fable 5.1 에서도 무효화됐다(prompt-caching, 2026-09-29 조회).
- ultracode(v2.1.284+)는 effort 레벨이 아니라 `/effort` 안의 별도 토글이다: *"Turning ultracode on or off with `/effort` or the `ultracode` setting leaves the effort level unchanged."* 켜는 경로는 `/effort ultracode`(끄기 `… off`)·슬라이더 `Tab`·설정 `"ultracode": true`. 예외로 *"The `--effort ultracode` flag and the Agent SDK `effortLevel: "ultracode"` value turn it on and also set the level to `xhigh`."* 프롬프트 키워드는 레벨을 바꾸지 않는다 — *"To run a single task as a workflow without changing the session's effort level, include the keyword `ultracode` in your prompt."* `CLAUDE_CODE_EFFORT_LEVEL`·effort 상한이 레벨을 정하면 ultracode 는 그 레벨에서 켜진 채 남고, 모델이 `xhigh` 를 지원하지 않거나 workflows 가 꺼져 있으면 쓸 수 없다(model-config·workflows, 2026-09-29 조회).
  - 이전 동작(v2.1.283 이하): *"Before v2.1.284, turning on ultracode set the session to `xhigh` effort, picking another level turned it off, and an effort cap below `xhigh` made it unavailable."* 2026-09-27 이 줄의 "ultracode 설정이 꺼져 있을 때 — 켜면 `xhigh` 를 보낸다" 는 이 동작 기준이었다. 설치 바이너리 비교로도 확인했다 — 2.1.281·2.1.283 에는 설정 `ultracode: true` 일 때 effort 기본값을 `xhigh` 로 바꾸는 분기가 있고 2.1.284 에는 없다(workflow wf_0b281262-6a0).

## 정정 (재논의 방지)
- `opus[1m]`/`fable[1m]`(1M long-context)에 **long-context 프리미엄 가격은 없다** — 4.6 이후 모델은 1M 전체가 표준 가격(pricing).
- `max` effort 는 "Absolute maximum capability with no constraints on token spending" 이고, Opus 4.7 표는 "Reserve for frontier problems" 라고 적는다(2026-08 이 페이지의 "extremely hard, latency-insensitive" 인용은 현 문서에 없다).

## 연계
이 사실에 기반한 단계별 모델 배치는 [[model-stage-tiering]], Claude Code 쪽 선택 메커니즘은 [[claude-code-model-selection]], 과거 티어 결정은 [[subagent-model-effort-tiering]]→[[effort-global-xhigh]].
