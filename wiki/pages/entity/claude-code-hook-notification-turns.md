---
title: claude-code-hook-notification-turns
category: entity
created: 2026-09-03
updated: 2026-09-03
sources:
  - ~/.claude/projects/-Users-jongyoonlee--claude/*.jsonl (type:"user" + <task-notification> 1841건·6건 파싱 대조 — 2026-09-02, Claude Code 2.1.258)
  - PR #149 (scripts/dlc-task-router.js 수정 + dlc-task-router.test.js)
  - plans/2026-09-02-router-notification-fp
---

# claude-code-hook-notification-turns

Claude Code(2.1.258 기준)의 **`UserPromptSubmit` hook 은 사용자가 친 프롬프트에만 도는 것이 아니다**. subagent(Agent 도구)나 백그라운드 작업이 끝나면 하네스가 그 결과를 `type:"user"` 메시지로 대화에 넣고, 그 턴에도 `UserPromptSubmit` 이 발동한다. hook 의 `prompt` 필드에는 사용자 텍스트가 아니라 알림 본문이 들어온다.

## 관측된 형태 (transcript 실측)
- 최상위 `<task-notification>` 태그, `<system-reminder>` 래퍼 없음. 내부는 `<task-id>`·`<tool-use-id>`·`<output-file>`·`<status>`·`<summary>`.
- `<summary>` 에는 subagent 의 결과 요약이 그대로 들어간다 — 리뷰어 보고라면 "재현·failing·회귀" 같은 단어가 흔하다.
- 모델 쪽 대화 뷰에는 `<system-reminder>[SYSTEM NOTIFICATION - NOT USER INPUT]…` 로 감싸여 보이지만, hook 이 받는 raw 형태는 래퍼 없는 최상위 태그였다(6건 전부). 다른 형태가 있을 가능성은 배제하지 않는다.

> [!open] 하네스 버전·이벤트 종류에 따라 `<system-reminder>` 래퍼가 붙는 경우가 있는지는 미확인. 이 repo 의 라우터는 두 형태를 모두 걷어낸다.

## 이 repo 에 준 영향
- `scripts/dlc-task-router.js` 가 prompt 전체를 키워드 매칭해 알림 턴마다 `[dlc:investigation]` 을 문서 작업에 주입했다(한 세션 4회). 같은 턴의 `ledger.reset` 이 [[evidence-gate]] 의 changed/verified·doc-drift 판정을 조용히 지웠다(리뷰어가 pre-existing 으로 확인).
- 수정(PR #149): `<system-reminder>`·`<task-notification>` 블록을 걷어낸 **사용자 텍스트만** 판정하고, 남는 텍스트가 없으면 리셋 없이 종료. "태그로 시작하면 skip" 을 택하지 않은 이유는 하네스가 정상 프롬프트 *앞에도* reminder 를 붙이기 때문.

## 일반 교훈
- UserPromptSubmit 기반 hook 을 쓸 때 `prompt` 를 사용자 발화로 가정하지 말 것. 세션 상태를 리셋하는 hook 이면 특히 위험 — 알림 턴이 사용자 턴 사이에 끼어 들어와 상태를 지운다.
- 관련: [[workflow-failures]](오탐 누적 표), [[claude-code-subagent-config]](subagent 실행 설정).
