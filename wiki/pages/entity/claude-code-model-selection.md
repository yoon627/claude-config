---
title: claude-code-model-selection
category: entity
created: 2026-08-05
updated: 2026-08-05
sources:
  - https://code.claude.com/docs/en/model-config
  - https://code.claude.com/docs/en/advisor
  - https://claude.com/blog/the-advisor-strategy
  - https://code.claude.com/docs/en/sub-agents
  - researcher 조사 2026-08-05 (본 세션)
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
frontmatter `model:` = alias(`fable` 포함)|full ID|`inherit`(기본). 우선순위: `CLAUDE_CODE_SUBAGENT_MODEL` env > 호출 파라미터 > frontmatter > 세션 모델([[claude-code-subagent-config]]). **함정: 전부 inherit이면 Fable 세션에서 리뷰·검색 subagent까지 Fable로 돎.** 빌트인 Explore는 inherit하되 Opus 상한(Fable 세션이어도 Explore는 Opus 이하).

## 관련
가격·한도·벤치 구도는 [[anthropic-claude-models]], 이 메커니즘을 쓰는 결정은 [[model-stage-tiering]]·[[effort-global-xhigh]].
