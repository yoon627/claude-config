---
title: subagent-model-effort-tiering
category: decision
created: 2026-06-19
updated: 2026-06-26
sources:
  - plans/2026-06-18-subagent-model-effort/subagent-model-effort-plan.md
  - PR #51
  - agents/*.md
---

# subagent-model-effort-tiering

> [!conflict] Superseded by [[effort-global-xhigh]] (PR #66·#67·#68, 2026-06-26)
> model/effort 차등을 폐기하고 메인·subagent 전부 `opus` + `xhigh` 단일 정책으로 전환했다. 아래 차등(simplifier sonnet·researcher haiku·reviewer effort max·메인 high)은 더 이상 유효하지 않다 — 역사적 근거로만 보존.

subagent별 `model`/`effort`를 차등해 토큰을 최적화하되 리뷰 품질은 보존한 결정(PR #51, 2026-06-19 머지). [[hub-and-spoke-isolation]]의 spoke마다 작업 성격에 맞는 모델 티어를 둔다.

## 차등 (agents/*.md frontmatter)
- **reviewer 3종**(plan-reviewer·code-reviewer·architecture-reviewer) = `model: opus` + `effort: max` — 버그·보안·누락을 잡는 깊은 추론 단계라 thinking 비용을 여기 집중.
- **code-simplifier** = `model: sonnet` — 기계적 작업(~40%↓).
- **researcher** = `model: haiku` — 단순 검색(~80%↓).
- **메인 세션 effort** = `max`→`high` — Anthropic 권장(Opus는 high 기본, max는 latency-insensitive 한정). 전 작업 max는 과사고·낭비.

## 근거
모델 능력에 비용을 비례시킨다 — 리뷰는 값을 치를 곳(opus+max), 검색·단순화는 저단가로 충분. 가격·effort 지원 근거는 [[anthropic-claude-models]], frontmatter 문법·상속은 [[claude-code-subagent-config]].

## 함정
메인 effort 레버는 settings.json만으론 부족했다 — OS env가 우선이라 별도 삭제가 필요했다: [[effort-os-env-single-source]].
