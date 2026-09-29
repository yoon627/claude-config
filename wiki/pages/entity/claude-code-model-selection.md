---
title: claude-code-model-selection
category: entity
created: 2026-08-05
updated: 2026-09-29
sources:
  - https://code.claude.com/docs/en/model-config (alias 해석·우선순위·effort·1M — 2026-09-27 조회, 2026-09-29 재조회)
  - https://code.claude.com/docs/en/advisor (advisor 조합 — 2026-09-27 조회, 2026-09-29 재조회)
  - https://claude.com/blog/the-advisor-strategy
  - https://code.claude.com/docs/en/sub-agents (subagent 모델·effort 해석, FORCE — 2026-09-27 조회)
  - researcher 조사 2026-08-05, 2026-08-06 + code-reviewer 재확인 2026-08-11(pin 시 확정사실 — 기준 v2.1.222), workflow 교차 검증 2026-09-27(wf_83e9d53b-c4e)
  - https://github.com/anthropics/claude-code/issues/45169
---

# claude-code-model-selection

Claude Code(v2.1.x)의 모델 선택 메커니즘 확정 사실 — 단계별 모델 배치([[model-stage-tiering]])의 구현 수단. 기준: 2026-09-27(버전명 목록은 2026-09-29 부터 [[anthropic-claude-models]] 에만 둔다).

## alias
`default`·`best`·`fable`·`fable[1m]`·`opus`·`opus[1m]`·`sonnet`·`sonnet[1m]`·`haiku`·`opusplan`(+`opusplan[1m]`). `best`=Fable 접근권 있으면 `fable`, 없으면 `opus` 와 같은 모델. **`fableplan`류는 없다.** Fable 은 어떤 계정에서도 default 가 아니며 `/model fable` 로만 선택.

별칭이 지금 어느 버전으로 해석되는지(provider·Claude Code 버전별)는 [[anthropic-claude-models]] 에만 적는다. `fable` 은 `ANTHROPIC_DEFAULT_FABLE_MODEL` 이 있으면 그 값으로 해석된다. 다른 provider 는 다르게 해석한다(model-config 표) — 이 repo 는 Anthropic API 만 쓴다. 별칭은 Claude Code 릴리스와 함께 전진하므로, 별칭으로 고정한 `agents/*.md` 는 세대 교체를 자동으로 따라간다(기본 effort 도 따라 바뀐다 — [[anthropic-claude-models]]).

## opusplan
plan mode 에서 `opus`, 실행 전환 시 `sonnet`. 공식 문구: "pairs Opus's reasoning for planning with Sonnet's efficiency for execution" — "강한 모델로 계획, 싼 모델로 구현"의 공식 근거.

## advisor tool (experimental)
싼 main 모델이 실행하고, 결정 시점에만 강한 모델을 서버측 자문 호출(`advisorModel` 설정·`/advisor`·`--advisor`, Anthropic API 전용). **공식 측정치**(2026-08 기준, advisor 전략 글): Sonnet main + Opus advisor = Sonnet 단독 대비 SWE-bench Multilingual +2.7pp, 태스크당 비용 −11.9%; Haiku+Opus advisor 는 BrowseComp 에서 Haiku 단독의 2배+ 성능을 Sonnet 단독보다 85% 싸게.
- **Fable 을 advisor 로 쓸 수 있다**(2026-09-27) — 조합 표에 "Sonnet main + Fable advisor — Fable guidance at decision points without running Fable throughout. Requires Fable access". Fable 이 usage credit 으로 과금되는 플랜에서는 advisor 도 credit 으로 과금되고, 한 번의 `/model fable` 동의가 필요하다.
- 공식: *"The advisor must be at least as capable as the main model"*. main 모델별 허용 조합은 advisor 문서(https://code.claude.com/docs/en/advisor)의 표가 정본이라 여기 옮겨 적지 않는다(2026-09-29 확인 — Sonnet 5.5 행 포함). subagent 는 설정된 advisor 를 물려받고 자기 모델로 같은 검사를 한다.

## /model 저장 동작 · env
- v2.1.153+: `/model` 선택이 user settings `model` 에 default 저장(Enter 저장 / `s` 세션 한정).
- 우선순위(model-config): `/model` > `--model` > `ANTHROPIC_MODEL` > settings `model` > `ANTHROPIC_DEFAULT_MODEL`(새 세션 기본값). project·managed settings 의 `model` 은 실행마다 다시 적용돼 user 의 저장값보다 앞선다. 조직 기본값은 user 선택이 없을 때의 출발점일 뿐이다(관리자가 override 를 켠 경우만 예외).
- `ANTHROPIC_DEFAULT_FABLE_MODEL`(fable alias 해석 제어)·`DISABLE_PROMPT_CACHING_FABLE`.

## subagent model · effort
해석 순서(sub-agents 문서, 2026-09-27): **1) 호출 파라미터 `model` 2) frontmatter `model`(`inherit` = 메인 모델) 3) `CLAUDE_CODE_SUBAGENT_MODEL` 4) 메인 모델.** *"Before v2.1.251, `CLAUDE_CODE_SUBAGENT_MODEL` came first in this order and overrode both the per-invocation parameter and the frontmatter"* — 그래서 이 env 만으로는 frontmatter 고정을 **더 이상 덮지 못한다**.

effort: frontmatter `effort` 는 *"Overrides the session effort level. Default: inherits from session."*(sub-agents frontmatter 표) — 단 `CLAUDE_CODE_EFFORT_LEVEL` env 는 이기지 못하고 `maxEffortLevel`·조직 상한에 묶인다(model-config). 이 repo 의 `agents/*.md` 는 `effort` 가 없어 세션 레벨을 따른다. 레벨을 따로 정하지 않았다면 user settings 에 effort 저장값이 없어(2026-09-29) 세션 모델의 기본값을 받는다 — M12 결정(2026-09-24, Opus 5.5 `medium`)은 그 기본값과 같아 저장 키를 지웠다([[effort-global-xhigh]]). 세션 모델과 다른 모델로 고정된 subagent 가 어떤 레벨을 받는지는 문서에 없다(❌).

**함정: 전부 inherit 이면 Fable 세션에서 리뷰·검색 subagent 까지 Fable 로 돎.** 빌트인 Explore 는 inherit 하되 Opus 상한(Fable 세션이어도 Explore 는 Opus 이하). → 이 repo 는 2026-08-06 단계별 고정으로 이 함정을 해소했다([[model-stage-tiering]]).

## subagent 고정 시 확정 사실
- **`[1m]` 접미사는 subagent frontmatter 에 쓰지 않는다** — 공식 허용값 목록(`sonnet|opus|haiku|fable|full ID|inherit`)에 미기재이고, resolution 이 접미사를 벗기는 버그가 미수정(anthropics/claude-code#45169, #36670, #34421 — 2026-08 확인). `/model`·`--model` 에서는 정식 표기라는 점과 구분할 것.
- **필요하지도 않다**: Anthropic API 에서 `opus`·`sonnet`·`fable` 이 지금 가리키는 모델은 모든 플랜(Pro 포함)에서 native 1M 이다(model-config — 2026-09-29 재확인, 모델 목록은 [[anthropic-claude-models]]). 200K 로 떨어지는 경우는 `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`, alias 가 구형 모델로 해석되는 provider, LLM gateway 경유.
- **subagent context 는 부모 상속이 아니라 자기 모델 기준**("sized by its own model, not the parent's") — 작은 창 모델에 위임하면 그 subagent 는 작은 창을 받는다.
- **명시 pin 은 자동 폴백이 없다**: 한도 소진 시 `Agent terminated early due to an API error` 로 실패하고, `fallbackModel` 체인은 rate-limit 류에 발동하지 않는다. 메인이 `/model sonnet` 으로 피신해도 pin 된 subagent 는 계속 Opus 를 호출한다(⚠️추정 — 문서가 이 조합을 직접 언급하진 않음).

> [!note] 비상 레버 (2026-09-27 정정 — v2.1.251 순위 변경)
> `CLAUDE_CODE_SUBAGENT_MODEL=<별칭>` **만으로는 frontmatter 고정을 덮지 못한다.** 모든 subagent 를 한 모델로 돌리려면 `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`(v2.1.257+)을 함께 설정한다 — FORCE 가 켜지면 *"Claude Code ignores the `model` field of every subagent definition, including the built-in Explore and Plan subagents, and Claude can't pass a model when it starts a subagent"* 이라 researcher·빌트인 Explore/Plan 까지 같은 모델로 돈다. FORCE 만 켜면 subagent 가 메인 모델로 돈다(단 빌트인 Explore 는 Claude API 에서 Opus 상한 유지). 범위를 좁히려면 `agents/*.md` 의 `model:` 을 직접 바꾼다.

- **`CLAUDE_CODE_SUBAGENT_MODEL=inherit` 은 무효**(v2.1.196+) — "미설정과 동일"이라 pin 을 되돌리려고 `inherit` 을 넣으면 **아무 일도 안 일어난다**. 되돌리려면 구체적 별칭(`sonnet` 등)이나 full ID 에 FORCE 를 더하거나 frontmatter 를 고친다. (v2.1.196 이전에는 반대로 `inherit` 이 메인 모델을 강제하고 파라미터·frontmatter 를 무시했다.)
- 조직 `availableModels` allowlist 에 걸린 값: **v2.1.222+** 는 family 별칭(`opus` 등)이면 allowlist 가 허용하는 **그 계열 최신 버전으로 실행**하고, 그 외이거나 허용 버전이 없으면 inherited model 로 폴백. **v2.1.222 이전**에는 family 별칭도 inherited model 로 갔다. 어느 쪽이든 실패가 아니라 조용한 대체라는 점이 함정.

## 관련
가격·한도·벤치 구도는 [[anthropic-claude-models]], 이 메커니즘을 쓰는 결정은 [[model-stage-tiering]]·[[effort-global-xhigh]].
