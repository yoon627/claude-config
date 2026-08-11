---
title: effort-global-xhigh
category: decision
created: 2026-06-26
updated: 2026-08-11
sources:
  - PR #66 (subagent model opus 통일)
  - PR #67 (settings effort xhigh + README)
  - PR #68 (agents frontmatter effort 제거)
  - https://platform.claude.com/docs/en/build-with-claude/effort
  - 커밋 78a6715 (effort xhigh→high, 웹툴 400 해소)
  - 실측 2026-08-11 (ps eww 로 claude 프로세스 env=max, settings.json=high)
  - worktree subagent-model-pinning (2026-08-06 model 단계별 고정)
---

# effort-global-xhigh

메인 세션과 모든 subagent 를 `model: opus` + effort `xhigh` 단일 정책으로 통일한 결정(2026-06-26, PR #66·#67·#68 머지). [[subagent-model-effort-tiering]]의 model/effort 차등을 폐기하고 단일 레버로 되돌렸다.

> [!note] 현재 상태 (2026-08-11)
> 이 페이지에서 지금도 유효한 것은 **effort 를 전역 단일 레버로 둔다**는 원칙뿐이다. 값은 `xhigh` 가 아니고 단일화도 깨져 있다(아래 warning). **model** 은 `inherit` 결정이 재개정되어 단계별 고정으로 갔다 — 타임라인 마지막 항목과 [[model-stage-tiering]] 이 현재값.

## 결정
- **단일 레버**: `settings.json` `env.CLAUDE_CODE_EFFORT_LEVEL` 하나로 메인·subagent effort 를 전역 고정. (`effortLevel` 키도 같은 값으로 일치시켜 두되 실효 레버는 env.)
  > [!warning] 실제 값은 `xhigh` 가 아니다 — 그리고 "단일 소스"도 깨져 있다 (2026-08-11 실측)
  > - `settings.json:3`·`:244` = `high`. 커밋 `78a6715 fix(settings): effort xhigh→high (웹툴 400 해소)` 에서 **의도적으로 하향**됐는데 이 페이지만 갱신되지 않았다.
  > - 그러나 **shell/OS env 가 settings.json 을 이긴다**([[effort-os-env-single-source]]) — 실행 중 claude 프로세스 실측값은 `max`(`ps eww <pid>`). Claude Code 가 tool 셸에 주입하는 env(`printenv` = `high`)와 **프로세스 자신의 env 가 다르므로, `printenv` 로 effort 를 판정하면 안 된다.**
  > - 근본원인: `scripts/bootstrap/setup.sh:118`(`export CLAUDE_CODE_EFFORT_LEVEL=max`)·`setup.ps1:156` 이 **이 repo 안에서** shell/User env 에 `max` 를 심는다. 즉 [[effort-os-env-single-source]] 가 적립한 실패(설정만 낮추고 OS env 가 이겨 계속 max)가 **재발한 상태**이고, bootstrap 재실행 시 다시 심어진다. (수정은 별건 — plan `# Deferred`.)
  > - **페이지명 `effort-global-xhigh` 는 이제 값이 아니라 "effort 를 전역 단일 레버로 둔다"는 결정을 가리키는 이름으로 읽을 것** — rename 은 링크 전수 수정을 동반해 별도 작업으로 미뤘다. 아래 "근거" 절의 xhigh 권장 서술은 *채택 당시* 근거이지 현재값이 아니다.
- **subagent frontmatter**: `agents/*.md` 는 `model: opus` 만 두고 `effort` 필드 제거 — env 가 frontmatter effort 를 override 하므로 어차피 죽은 설정이었다([[claude-code-subagent-config]]).
- model 차등(simplifier sonnet / researcher haiku)도 폐기 → 전부 opus.
- **`model: opus` → `model: inherit` 로 변경 (이유: Fable 가용성 변동 대비 — 모델 세대 교체 시 agents 수정 지점 0, 세션 모델 상속. 2026-07-04, asset-cleanup)**. effort 전역 단일은 유지 — 이 결정의 "단일 레버" 원칙은 불변이고 model 명시만 상속으로 완화. 상속 동작 근거는 [[claude-code-subagent-config]](미지정=세션 상속·inherit 별칭).
- **`inherit` → 단계별 고정으로 재변경 (2026-08-06, subagent-model-pinning)**: reviewer 3종 `model: opus`, researcher `model: sonnet`. 이유는 [[model-stage-tiering]] — 2026-07-04 inherit 결정의 전제("Fable 가용성 변동 대비")가 **Fable 이 기본 세션 모델이 되고 주간 50% 캡이 붙은 뒤로 역효과**가 됐다. 세션이 Fable 이면 리뷰·조사까지 Fable 캡을 소모하는데, 리뷰 품질 병목엔 opus 면 충분하고 검색·요약엔 sonnet 이면 충분하다. **inherit 결정이 지키려던 "세대 교체 시 수정 지점 0" 은 별칭(`opus`/`sonnet`)이라 그대로 보존**되고, 끊는 것은 *세션 모델 추종* 하나뿐이다(그게 이번 의도).
  - `[1m]` 접미사는 쓰지 않는다 — subagent frontmatter 의 공식 허용값에 미기재이고 stripping 버그 이력(anthropics/claude-code#45169, 미수정). 필요도 없다: Opus 5 는 Anthropic API·Max/Team/Enterprise 에서 **자동 1M** 이라 `model: opus` 만으로 1M 이 유지된다. subagent context 는 부모 상속이 아니라 **자기 모델 기준**(공식).
  - 트레이드오프: 명시 pin 은 **자동 폴백이 없다**. Opus 한도 소진 시 subagent 는 `Agent terminated early due to an API error` 로 실패하고, plan-reviewer/code-reviewer 는 필수 게이트라 dlc 가 멈춘다. 비상 레버는 `CLAUDE_CODE_SUBAGENT_MODEL=<별칭>`(frontmatter 보다 우선 — [[claude-code-model-selection]]). **`inherit` 값은 무효**(v2.1.196+ 미설정과 동일)이니 되돌릴 땐 구체적 별칭을 줄 것.

## 근거 (공식 docs)
- **Opus 4.8 코딩 권장 = xhigh**: "Start with `xhigh` for coding and agentic use cases." 기본값은 high 이므로 xhigh 는 명시 설정해야 적용.
- **effort 는 hard cap 이 아니라 adaptive signal**: 쉬운 작업엔 높은 설정이어도 모델이 덜 추론. "간단한 작업까지 과추론"은 약한 우려.
- **`max` 는 frontier 전용**: 공식이 "structured-output·less intelligence-sensitive 작업엔 overthinking 유발"이라 경고. 코드리뷰 같은 작업엔 max 보다 xhigh 가 맞다 → reviewer 의 옛 `effort: max` 는 부적절했고, env=xhigh override 로 실제로도 적용된 적 없음.
- 차등의 비용 절감 < 통일의 단순성·운용 편의. 비용/레이턴시가 민감하지 않은 운용 전제.

## precedence (적용 우선순위)
`env(CLAUDE_CODE_EFFORT_LEVEL)` > `effortLevel`(settings) > 모델 기본값. subagent/skill frontmatter effort 는 세션 레벨은 override 하지만 **env 는 못 이긴다**. → env 가 설정된 한 frontmatter effort 는 무효라 제거가 정합적. 상세는 [[effort-os-env-single-source]].

## 트레이드오프
유일한 비용은 토큰·레이턴시 증가. 비용 민감 구간이 생기면 전역 하향 대신 그 턴만 조절: `/effort` 슬라이더 또는 프롬프트에 `ultrathink`(설정 불변, 그 턴만 nudge). 작업유형별 effort 가이드를 문서로 박는 것은 adaptive 특성과 중복이라 채택하지 않음.
