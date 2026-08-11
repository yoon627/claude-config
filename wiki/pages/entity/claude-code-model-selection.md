---
title: claude-code-model-selection
category: entity
created: 2026-08-05
updated: 2026-08-11
sources:
  - https://code.claude.com/docs/en/model-config
  - https://code.claude.com/docs/en/advisor
  - https://claude.com/blog/the-advisor-strategy
  - https://code.claude.com/docs/en/sub-agents
  - researcher 조사 2026-08-05 (본 세션)
  - researcher 조사 2026-08-06 + code-reviewer 재확인 2026-08-11 (pin 시 확정사실 — 기준 v2.1.222)
  - https://github.com/anthropics/claude-code/issues/45169
---

# claude-code-model-selection

Claude Code(v2.1.x)의 모델 선택 메커니즘 확정 사실 — 단계별 모델 배치([[model-stage-tiering]])의 구현 수단. 기준: 2026-08-05.

## alias
`default`·`best`·`fable`·`opus`·`sonnet`·`haiku`·`sonnet[1m]`·`opus[1m]`·`opusplan`(+`opusplan[1m]`)이 전부. `best`=Fable 접근권 있으면 Fable, 없으면 최신 Opus. **`fableplan`류는 없다.** Fable은 어떤 계정에서도 default가 아니며 `/model fable`로만 선택.

## opusplan
plan mode에서 `opus`(→Opus 5), 실행 전환 시 `sonnet`(→Sonnet 5). 공식 문구: "pairs Opus's reasoning for planning with Sonnet's efficiency for execution" — "강한 모델로 계획, 싼 모델로 구현"의 공식 근거.

## advisor tool (experimental)
싼 main 모델이 실행하고, 결정 시점에만 강한 모델을 서버측 자문 호출(`advisorModel` 설정·`/advisor`·`--advisor`). **공식 측정치**: Sonnet main + Opus advisor = Sonnet 단독 대비 SWE-bench Multilingual +2.7pp, 태스크당 비용 −11.9% (더 좋으면서 더 쌈); Haiku+Opus advisor는 BrowseComp에서 Haiku 단독의 2배+ 성능을 Sonnet 단독보다 85% 싸게. **Fable은 현재 advisor로 선택 불가**(dim 처리, 롤아웃 대기) — 풀리면 "Sonnet main + Fable advisor"가 계획-자문 통합형 상위 호환 후보.

## /model 저장 동작 · env
- v2.1.153+: `/model` 선택이 user settings `model`에 default 저장(Enter 저장 / `s` 세션 한정). 우선순위 `/model` > `--model` > `ANTHROPIC_MODEL` > settings.
- `ANTHROPIC_DEFAULT_FABLE_MODEL`(fable alias 해석 제어)·`DISABLE_PROMPT_CACHING_FABLE` 신설.

## subagent model
frontmatter `model:` = alias(`fable` 포함)|full ID|`inherit`(기본). 우선순위: `CLAUDE_CODE_SUBAGENT_MODEL` env > 호출 파라미터 > frontmatter > 세션 모델([[claude-code-subagent-config]]). **함정: 전부 inherit이면 Fable 세션에서 리뷰·검색 subagent까지 Fable로 돎.** 빌트인 Explore는 inherit하되 Opus 상한(Fable 세션이어도 Explore는 Opus 이하). → 이 repo 는 2026-08-06 단계별 고정으로 이 함정을 해소했다([[model-stage-tiering]]).

## subagent 고정 시 확정 사실 (조사 2026-08-06)
- **`[1m]` 접미사는 subagent frontmatter 에 쓰지 않는다** — 공식 허용값 목록(`sonnet|opus|haiku|fable|full ID|inherit`)에 미기재이고, resolution 이 접미사를 벗기는 버그가 미수정(anthropics/claude-code#45169, #36670, #34421). `/model`·`--model` 에서는 정식 표기라는 점과 구분할 것.
- **필요하지도 않다**: Opus 4.7+ 는 Anthropic API 에서 항상 1M, Max/Team/Enterprise 는 Opus 가 자동 1M 승격. 200K 로 떨어지는 조건은 Pro 플랜·LLM gateway 경유·`CLAUDE_CODE_DISABLE_1M_CONTEXT=1`·alias 가 구형 Opus 로 해석되는 배포(Bedrock/Vertex/Foundry).
- **subagent context 는 부모 상속이 아니라 자기 모델 기준**("sized by its own model, not the parent's") — 작은 창 모델에 위임하면 그 subagent 는 작은 창을 받는다.
- **명시 pin 은 자동 폴백이 없다**: 한도 소진 시 `Agent terminated early due to an API error` 로 실패하고, `fallbackModel` 체인은 rate-limit 류에 발동하지 않는다. 메인이 `/model sonnet` 으로 피신해도 pin 된 subagent 는 계속 Opus 를 호출한다(⚠️추정 — 문서가 이 조합을 직접 언급하진 않음). 비상 레버는 `CLAUDE_CODE_SUBAGENT_MODEL`.
- **함정: `CLAUDE_CODE_SUBAGENT_MODEL=inherit` 은 무효**(v2.1.196+) — "미설정과 동일"이라 resolution 이 그대로 호출 파라미터→frontmatter 로 내려간다. 즉 pin 을 되돌리려고 `inherit` 을 넣으면 **아무 일도 안 일어난다**. 되돌리려면 구체적 별칭(`sonnet` 등)이나 full ID 를 줄 것. (v2.1.196 이전에는 반대로 `inherit` 이 메인 모델을 강제하고 파라미터·frontmatter 를 무시했다.)
- 조직 `availableModels` allowlist 에 걸린 값: **v2.1.222+** 는 family 별칭(`opus` 등)이면 allowlist 가 허용하는 **그 계열 최신 버전으로 실행**하고, 그 외이거나 허용 버전이 없으면 inherited model 로 폴백. **v2.1.222 이전**에는 family 별칭도 inherited model 로 갔다. 어느 쪽이든 실패가 아니라 조용한 대체라는 점이 함정.

## 관련
가격·한도·벤치 구도는 [[anthropic-claude-models]], 이 메커니즘을 쓰는 결정은 [[model-stage-tiering]]·[[effort-global-xhigh]].
