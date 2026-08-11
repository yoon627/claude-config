---
title: effort-os-env-single-source
category: decision
created: 2026-06-19
updated: 2026-08-11
sources:
  - plans/2026-06-18-subagent-model-effort/subagent-model-effort-plan.md
  - Anthropic docs (settings.md, env-vars.md)
  - PR #67
  - 실측 2026-08-11 (ps eww claude pid → max; scripts/bootstrap/setup.sh:118 재주입)
---

# effort-os-env-single-source

> [!note] 현재 상태 (2026-08-11 갱신)
> effort 전역 정책은 [[effort-global-xhigh]] 로 통일 — `settings.json` `env.CLAUDE_CODE_EFFORT_LEVEL` 를 단일 소스로 두기로 했다.
>
> **단 2026-08-11 실측상 이 단일화는 깨져 있다**: `settings.json` 은 `high`(`78a6715` 에서 xhigh→high)인데 실행 중 claude 프로세스 env 는 `max` — 아래 교훈 그대로 shell/OS env 가 이겼다. 원인은 `scripts/bootstrap/setup.sh:118`·`setup.ps1:156` 이 **이 repo 안에서** `max` 를 shell/User env 에 심는 것(bootstrap 재실행 시 재주입). 즉 아래 사례의 재발이다. 판정 시 `printenv` 를 믿지 말 것 — tool 셸 env(`high`)와 프로세스 env(`max`)가 다르다. `ps eww <claude-pid>` 로 볼 것. 아래 "OS env 우선·단일 소스화" 교훈은 그대로 유효하며, 추가 확정 사실: **env 는 subagent/skill frontmatter 의 effort 도 override** 한다(precedence: env > effortLevel > frontmatter). 그래서 `agents/*.md` 의 effort 필드를 제거했다(PR #68).

메인 세션 effort를 낮추려 할 때 발견한 교훈: **OS/shell 환경변수가 settings.json `env`보다 우선**이라, settings.json만 바꿔도 OS에 설정된 값이 이긴다. effort 레버를 단일 소스화하려면 OS env를 제거해야 한다.

## 무슨 일이었나
Windows User 환경변수에 `CLAUDE_CODE_EFFORT_LEVEL=max`가 settings.json `env`와 **중복** 존재했다. 공식 우선순위(shell/OS env > settings.json `env`)상 settings.json을 `high`로 바꿔도 OS의 `max`가 이겨 메인은 계속 max였다. → **OS env 삭제 + settings.json `high` 단일화**로 해결([[subagent-model-effort-tiering]]).

## 일반 규칙
- 같은 설정을 OS env와 settings.json 양쪽에 두지 않는다 — 어느 쪽이 진짜 레버인지 흐려진다.
- 공식 변수명은 `CLAUDE_CODE_EFFORT_LEVEL`. `CLAUDE_EFFORT`는 파생/내부 별칭(빈값) — 변수명은 공식 문서로 검증.

## 검증 함정
> [!open] 변경이 worktree에 있을 때 *현재 세션*엔 미반영된다(설정은 세션 시작 시 로드, Process env는 시작 시 고정). 머지 후 **새 세션**에서 `/status`로 확인해야 한다. 자세한 effort 지원 범위는 [[claude-code-subagent-config]].
