---
title: claude-code-hook-notification-turns
category: entity
created: 2026-09-03
updated: 2026-09-27
sources:
  - ~/.claude/projects/-Users-jongyoonlee--claude/*.jsonl (type:"user" + <task-notification> 1841건·6건 파싱 대조 — 2026-09-02, Claude Code 2.1.258)
  - transcript 의 type:"user" hand-back 턴 210건(2026-09-15~27, 런타임 2.1.271~2.1.281·auto mode, raw 형태는 한 세션 51건 표본)과 telemetry `router-investigation` 대조 (2026-09-27)
  - https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md (v2.1.271 auto mode hand-back 호출, v2.1.280 hand-back preamble 표시 수정 — 조회 2026-09-27)
  - PR #149 (scripts/dlc-task-router.js 수정 + dlc-task-router.test.js)
  - plans/2026-09-02-router-notification-fp
---

# claude-code-hook-notification-turns

Claude Code(2.1.258 기준)의 **`UserPromptSubmit` hook 은 사용자가 친 프롬프트에만 도는 것이 아니다**. subagent(Agent 도구)나 백그라운드 작업이 끝나면 하네스가 그 결과를 `type:"user"` 메시지로 대화에 넣고, 그 턴에도 `UserPromptSubmit` 이 발동한다. hook 의 `prompt` 필드에는 사용자 텍스트가 아니라 알림 본문이 들어온다.

## 관측된 형태 (transcript 실측)
- 최상위 `<task-notification>` 태그, `<system-reminder>` 래퍼 없음. 내부는 `<task-id>`·`<tool-use-id>`·`<output-file>`·`<status>`·`<summary>`.
- `<summary>` 에는 subagent 의 결과 요약이 그대로 들어간다 — 리뷰어 보고라면 "재현·failing·회귀" 같은 단어가 흔하다.
- 모델 쪽 대화 뷰에는 `<system-reminder>[SYSTEM NOTIFICATION - NOT USER INPUT]…` 로 감싸여 보이지만, hook 이 받는 raw 형태는 래퍼 없는 최상위 태그였다(6건 전부). 다른 형태가 있을 가능성은 배제하지 않는다.

> [!open] 하네스 버전·이벤트 종류에 따라 `<system-reminder>` 래퍼가 붙는 경우가 있는지는 미확인. 이 repo 의 라우터는 두 형태를 모두 걷어낸다. v2.1.234 부터 턴 사이에 오는 background 작업 알림은 모델에게 `<system-reminder>` 로 감싸 보낸다(changelog) — hook 이 받는 `prompt` 도 그런지는 changelog 에 없다.

### subagent 보고(hand-back) 턴 — 2026-09-15~27 관측 (런타임 2.1.271~2.1.281, auto mode)
- v2.1.271 이 auto mode 에서 subagent 가 "전용 hand-back 호출"로 보고하게 바꿨다(changelog: "Changed auto mode so a subagent reports back to its caller through a dedicated hand-back call …"). 그 보고는 `<task-notification>` 과 **별개의 `type:"user"` 턴**으로 들어온다. transcript 의 raw 텍스트는 평문 `Another Claude session sent a message:` 뒤 **개행**, 이어서 `<agent-message from="…">` 태그와 그 안의 `[Subagent hand-back]`·보고 본문이다. `<system-reminder>` 래퍼는 없다(한 세션 51건을 표본으로 확인). 이 형태의 턴은 transcript 전체에서 2026-09-15 첫 발생부터 210건이고 전부 auto mode 다 — auto mode 가 아닌 세션의 형태는 보지 못했다.
- 이 턴에도 `UserPromptSubmit` 이 돈다 — 표본 세션에서 보고 본문 단어가 라우터 정규식에 맞은 턴 전부(41/41)에 `[dlc:investigation]` 이 주입됐고(transcript 의 hook 주입 기록), telemetry 로는 14개 세션에서 130건이다. 정규식에 안 맞은 턴에서 hook 이 돌았는지는 관측할 수 없다.
- 걷어낼 태그에 `agent-message` 만 더하면 부족할 수 있다 ⚠️ — transcript 기준으로 태그 밖 평문 접두어가 남아 "사용자 텍스트가 남았다"로 판정되기 때문이다. 다만 hook stdin 의 `prompt` 가 transcript 텍스트와 같은지는 캡처해 보지 않았다 — 이 세션에는 debug 로그가 없고 hook 설정은 세션 시작 때 고정돼, 수정의 fixture 는 transcript 형태로 떴고 실제 stdin 경로는 머지 뒤 실제 hand-back 턴으로 확인한다. transcript 에서 이 턴은 전부 `isMeta: true` 다.

## 이 repo 에 준 영향
- `scripts/dlc-task-router.js` 가 prompt 전체를 키워드 매칭해 알림 턴마다 `[dlc:investigation]` 을 문서 작업에 주입했다(한 세션 4회). 같은 턴의 `ledger.reset` 이 [[evidence-gate]] 의 changed/verified·doc-drift 판정을 조용히 지웠다(리뷰어가 pre-existing 으로 확인).
- 수정(PR #149): `<system-reminder>`·`<task-notification>` 블록을 걷어낸 **사용자 텍스트만** 판정하고, 남는 텍스트가 없으면 리셋 없이 종료. "태그로 시작하면 skip" 을 택하지 않은 이유는 하네스가 정상 프롬프트 *앞에도* reminder 를 붙이기 때문.
- 2026-09-27: 위 hand-back 턴은 이 수정이 걷어내지 못해 라우터 오발동과 리셋이 다시 생겼다([[workflow-failures]] 의 라우터 알림 턴 행). 수정(`router-agent-message`): 걷어내기가 아니라 턴 앞머리로 판별 — reminder·notification 을 걷어낸 뒤 (선택적) `another claude session sent a message:` + `<agent-message` 로 시작하면 턴 전체를 건너뛴다. 태그만 걷어내면 뒤 안내 문단이 남고, 안내 문단 문구까지 맞추면 하네스 문구 변경에 조용히 깨지기 때문이다(3주 사이 턴 형식이 두 번 바뀌었다). 판별식은 transcript hand-back 턴 213/213 을 잡고 다른 user 텍스트 턴 1,888건은 0건이다.

## 일반 교훈
- UserPromptSubmit 기반 hook 을 쓸 때 `prompt` 를 사용자 발화로 가정하지 말 것. 세션 상태를 리셋하는 hook 이면 특히 위험 — 알림 턴이 사용자 턴 사이에 끼어 들어와 상태를 지운다.
- 관련: [[workflow-failures]](오탐 누적 표), [[claude-code-subagent-config]](subagent 실행 설정).
