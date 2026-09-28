---
title: ai-native-sdlc-playbook-intent
category: source
created: 2026-09-07
updated: 2026-09-15
sources:
  - https://academy.claude.com/ko/courses/ai-native-sdlc-playbook/capture-intent (Claude Academy, "The AI-Native SDLC Playbook" Stage 1 "Capture as intent.md" — 원문)
  - plans/2026-09-07-plan-intent-section (반영 설계 — 일시 채널)
  - plans/2026-09-15-intent-md-bundle (묶음 intent.md 부분 채택)
---

# ai-native-sdlc-playbook-intent

Claude Academy *The AI-Native SDLC Playbook* 의 **Stage 1 "Capture as intent.md"** 요약. 핵심 논지: 아이디어를 백로그·유저스토리·리파인먼트 회의로 흘려보내지 말고, **발의자가 Claude 와 브레인스토밍해 그 자리에서 proto-spec 을 쓰고 버전관리에 커밋**하라. 전통적 SDLC 는 핸드오프마다 소유권이 옮겨가 엔지니어링에 도착할 즈음이면 발의자의 원래 의도에서 여러 단계 멀어진다.

> [!open] SPA 라 `WebFetch` 로는 제목만 온다(본문 미반환). 이 요약은 브라우저로 렌더된 본문을 읽어 정리했다. 나머지 5단계(Design·Build·Test·Deploy·Maintain)는 미조사.

## intent.md 의 구조

발의자 언어로 쓴 proto-spec. 헤더에 Author·Status, 본문은 다섯 항목:

| 항목 | 담는 것 |
|---|---|
| `## Problem` | 오늘 무엇이 안 되는가, 누가 영향받는가 |
| `## Proposed outcome` | 무엇이 나아지는가 |
| `## Affected users and systems` | 닿는 사람·시스템 |
| `## Constraints` | 지켜야 할 경계조건 |
| `## Open questions` | 아직 못 정한 것 |

형식 언어는 요구하지 않는다 — Claude 가 분석가가 물을 것(범위·사용자·제약·성공 기준)을 물어 구체화한 뒤 조직 템플릿으로 받아쓰고, 발의자가 오해된 부분을 고쳐 커밋한다. 템플릿은 **skill 로 인코딩**한다("Repeat processes are encoded via skills").

## 거버넌스·측정

- **증거 = 커밋된 파일 자체.** author·timestamp·개정 이력이 git history 에 남고, 승인/반려는 merge 또는 closing review 로 기록된다.
- **선행 지표**: 첫 대화에서 `intent.md` 커밋까지 걸린 시간. 수 주짜리 elicitation·refinement 주기가 수 시간으로 떨어지는 것이 기대치.
- **후행 지표**: *survival rate* — 커밋된 intent 중 product owner 가 Design 단계로 넘긴 비율. 더해서 `spec.md` 첫 커밋 이후 `intent.md` 가 몇 번 바뀌었는지.

## 이 repo 의 반영 (2026-09-07)

**산출물 형태만 채택**했다 — [[plan-handoff]] 의 `# Intent` 선택 섹션(Problem·Constraints·Out of scope·Open questions)으로 들어가고, [[dlc-development-cycle]] 의 요구사항 명확화 체크리스트가 4항에서 6항(문제·제약 추가)으로 늘어 그 결과를 이 섹션에 적는다.

**미채택 — 조직 장치**: 별도 `intent/` 홈(§10 "plan = 단일 진실 소스"와 충돌, 산출물 이원화는 drift 원인), product owner 승인 게이트, survival rate 지표, Git 없는 기여자용 VCS 커넥터. 1인 워크플로우엔 해당 없다. 원문의 `## Proposed outcome`·`## Affected users and systems` 도 빼는데, 전자는 `# Goal` 이 이미 담고 후자는 이 repo 규모에서 상시 자명하기 때문이다.

**2026-09-15 부분 정정 — 파일 형태도 채택**: 위 "산출물 형태만" 은 plan 과 요구가 1:1 이라는 전제였는데, knowledge_base 실측(2026-09-14, 한 요구 → plan 3~4개)에서 깨졌다. 그래서 여러 plan 으로 갈라지는 요구는 `plans/<date>-<intent-slug>/intent.md` 파일로 두고 plan 이 `intent:` 로 가리킨다([[plan-handoff]] 묶음 intent). 여전히 미채택: 별도 `intent/` 홈(`plans/` 아래에 둔다), 조직 장치 전부, `Affected users and systems` 항목. 단발 작업은 plan `# Intent` 그대로다. 2026-09-15 재확인(WebSearch): 공식 페이지에 "Claude Code 가 intent.md 를 자동으로 읽는다" 는 서술은 없다 — 조직 템플릿으로 Claude 에게 받아쓰게 하는 대화 지침이며, 서드파티 글의 "plan 전에 읽는 파일" 표현은 해석이다.

채택 계기는 이론이 아니라 실측이다 — 제약을 안 적어 같은 안이 3회 제시·기각된 2026-09-07 건([[lesson-tracked-config-machine-paths]]). 같은 이유로 2026-07-07 [[unknowns-discovery]] 세션이 기각했던 "plan 에서 바뀔 결정 앞세우기" wontfix 를 부분 supersede 한다.

관련: [[plan-handoff]], [[dlc-development-cycle]], [[unknowns-discovery]], [[fable-field-guide-unknowns]](같은 계열 — 구현 전 공백 발굴).
