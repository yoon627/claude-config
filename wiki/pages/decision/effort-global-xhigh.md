---
title: effort-global-xhigh
category: decision
created: 2026-06-26
updated: 2026-07-04
sources:
  - PR #66 (subagent model opus 통일)
  - PR #67 (settings effort xhigh + README)
  - PR #68 (agents frontmatter effort 제거)
  - https://platform.claude.com/docs/en/build-with-claude/effort
---

# effort-global-xhigh

메인 세션과 모든 subagent 를 `model: opus` + effort `xhigh` 단일 정책으로 통일한 결정(2026-06-26, PR #66·#67·#68 머지). [[subagent-model-effort-tiering]]의 model/effort 차등을 폐기하고 단일 레버로 되돌렸다.

## 결정
- **단일 레버**: `settings.json` `env.CLAUDE_CODE_EFFORT_LEVEL=xhigh` 하나로 메인·subagent effort 를 전역 고정. (`effortLevel` 키도 xhigh 로 일치시켜 두되 실효 레버는 env.)
- **subagent frontmatter**: `agents/*.md` 는 `model: opus` 만 두고 `effort` 필드 제거 — env 가 frontmatter effort 를 override 하므로 어차피 죽은 설정이었다([[claude-code-subagent-config]]).
- model 차등(simplifier sonnet / researcher haiku)도 폐기 → 전부 opus.
- **`model: opus` → `model: inherit` 로 변경 (이유: Fable 가용성 변동 대비 — 모델 세대 교체 시 agents 수정 지점 0, 세션 모델 상속. 2026-07-04, asset-cleanup)**. effort=xhigh 전역 단일은 유지 — 이 결정의 "단일 레버" 원칙은 불변이고 model 명시만 상속으로 완화. 상속 동작 근거는 [[claude-code-subagent-config]](미지정=세션 상속·inherit 별칭).

## 근거 (공식 docs)
- **Opus 4.8 코딩 권장 = xhigh**: "Start with `xhigh` for coding and agentic use cases." 기본값은 high 이므로 xhigh 는 명시 설정해야 적용.
- **effort 는 hard cap 이 아니라 adaptive signal**: 쉬운 작업엔 높은 설정이어도 모델이 덜 추론. "간단한 작업까지 과추론"은 약한 우려.
- **`max` 는 frontier 전용**: 공식이 "structured-output·less intelligence-sensitive 작업엔 overthinking 유발"이라 경고. 코드리뷰 같은 작업엔 max 보다 xhigh 가 맞다 → reviewer 의 옛 `effort: max` 는 부적절했고, env=xhigh override 로 실제로도 적용된 적 없음.
- 차등의 비용 절감 < 통일의 단순성·운용 편의. 비용/레이턴시가 민감하지 않은 운용 전제.

## precedence (적용 우선순위)
`env(CLAUDE_CODE_EFFORT_LEVEL)` > `effortLevel`(settings) > 모델 기본값. subagent/skill frontmatter effort 는 세션 레벨은 override 하지만 **env 는 못 이긴다**. → env 가 설정된 한 frontmatter effort 는 무효라 제거가 정합적. 상세는 [[effort-os-env-single-source]].

## 트레이드오프
유일한 비용은 토큰·레이턴시 증가. 비용 민감 구간이 생기면 전역 하향 대신 그 턴만 조절: `/effort` 슬라이더 또는 프롬프트에 `ultrathink`(설정 불변, 그 턴만 nudge). 작업유형별 effort 가이드를 문서로 박는 것은 adaptive 특성과 중복이라 채택하지 않음.
