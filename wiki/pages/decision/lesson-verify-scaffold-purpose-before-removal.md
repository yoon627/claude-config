---
title: lesson-verify-scaffold-purpose-before-removal
category: decision
created: 2026-09-24
updated: 2026-09-24
sources:
  - plans/2026-09-24-prompt-audit-apply/prompt-audit-apply-plan.md (Decisions·Review Disposition)
  - plans/2026-06-04-dlc-final-verify-subagent/dlc-final-verify-subagent-plan.md (runner 원래 목적)
  - plans/2026-09-07-playbook-gaps/playbook-gaps-plan.md (runner Acceptance 독립 대조 도입)
---

# lesson-verify-scaffold-purpose-before-removal

프롬프트·하네스 장치를 "낡은 scaffold" 로 보고 없애자고 하기 전에, **그 장치를 도입한 plan·결정을 먼저 읽고 원래 목적을 하나씩 반박할 수 있는지** 확인한다. 패턴 표에 맞는다는 것은 제거 근거가 아니다.

## 무슨 일이 있었나 (2026-09-24)

`/claude-api prompt-audit`(대상 모델 Opus 5.5)이 운영 자산에서 dated pattern 을 찾아 패치 16개를 제안했다. 그중 세 개가 도입 목적을 확인하지 않은 채 장치를 없애거나 약화했고, 셋 다 [[dual-review-plan-and-code]] 의 plan-reviewer(+codex)가 잡았다.

| 제안 | audit 근거 | 놓친 원래 목적 | 결과 |
|---|---|---|---|
| dlc 최종 검증 runner 제거 | "결정적 실행이라 LLM 이 판단할 것이 없다"(Group 4) | 긴 검증 출력을 메인 컨텍스트에서 덜어냄(2026-06-04) · Acceptance 를 독립 대조해 메인 판정과 갈리면 멈춤(2026-09-07) — [[hub-and-spoke-isolation]] | 보류. audit 이 대체 수단이라 한 code-reviewer 11항은 정적 plan↔diff 대조라 실행 결과를 보지 않아 **사실과 달랐다** |
| 날짜 기준 적용 범위를 "신규 plan" 으로 교체 | 날짜·경위 기록은 fossil(1d/2) | 날짜는 경위가 아니라 **소급 범위를 정하는 기능 조항**. "신규라고 전달된 plan" 으로 바꾸면 전달 누락 시 검사가 조용히 빠진다 | 기능 조항 유지, 경위 날짜만 제거 |
| 조사 프로토콜의 가설 규율 삭제 | 판단 작업의 strategy coaching(1c) | "첫 가설 안주 금지" — 대안 원인 배제는 성공 기준이다 ([[fablize-adopted-disciplines]]) | 개수만 빼고 원칙 유지 |

## 원인 (3 Whys)

1. 왜 잘못 제안했나 — 장치의 현재 문장만 보고 패턴 표와 대조했다.
2. 왜 문장만 봤나 — 도입 경위가 문장 밖(plan `# Decisions`, 커밋)에 있고, audit 절차의 provenance 단계를 idiom-dating 으로 대신했다.
3. 왜 대신했나 — 대량 스캔에서 "이 줄이 어떤 실패를 막으려 들어왔나"를 줄마다 추적하는 비용을 건너뛰었다. 그 질문은 audit 가이드 Step 2 가 명시한 것이다.

## 올바른 방법

- 제거·약화 후보마다 `git log -S '<문구>'` 또는 관련 plan 을 찾아 **도입 목적을 목록으로 적고, 각 목적이 대상 모델·현 구조에서 사라졌는지** 증거로 답한다. 하나라도 답 못 하면 제안하지 않거나 low-confidence flag 로만 둔다.
- "대체 수단이 있다"고 쓸 때는 그 수단의 실제 범위(정적/실행, 조건부/항상, 심각도 기본값)를 읽고 쓴다 — [[lesson-grep-absence-not-proof]] 와 같은 축.
- 날짜가 들어간 문장은 **경위(지워도 됨)**와 **적용 범위(기능)**를 구분한다.

## 전후 비교는 증거로 만든다

같은 작업에서 적용 여부를 갈랐던 방법 — 재사용 가능하다.
- **transcript 전수 스캔**(`~/.claude/projects/**/*.jsonl`, subagent 는 `subagents/*.meta.json` 의 `agentType` 으로 식별): tool-call 누출 0건/수천 텍스트 블록 → 우회 규칙 제거, small 변경 code-reviewer 10건 중 1건이 실제 Major → 생략안 보류.
- **headless A/B**(`claude -p --model … --effort … --output-format json --no-session-persistence --setting-sources project`): 숨은 테스트로 채점하는 과제로 비용·시간·정답을 비교. 천장 효과(양쪽 만점)면 품질 차이는 말할 수 없다는 한계를 같이 적는다.

관련: [[workflow-failures]], [[evidence-gate]].
