---
title: lesson-verify-scaffold-purpose-before-removal
category: decision
created: 2026-09-24
updated: 2026-09-27
sources:
  - plans/2026-09-24-prompt-audit-apply/prompt-audit-apply-plan.md (Progress·Decisions·Review Disposition)
  - plans/2026-09-27-audit-docs-drift/audit-docs-drift-plan.md (Progress·Review Disposition·Deferred — 사례 2)
  - plans/2026-06-04-dlc-final-verify-subagent/dlc-final-verify-subagent-plan.md (runner 원래 목적)
  - plans/2026-09-07-playbook-gaps/playbook-gaps-plan.md (runner Acceptance 독립 대조 도입)
---

# lesson-verify-scaffold-purpose-before-removal

프롬프트·하네스 장치를 "낡은 scaffold" 로 보고 없애자고 하기 전에, **그 장치를 도입한 plan·결정을 먼저 읽고 원래 목적을 하나씩 반박할 수 있는지** 확인한다. 패턴 표에 맞는다는 것은 제거 근거가 아니다. **설정값(effort·모델·권한)을 "회귀"·"미결"로 적거나 바꾸자고 할 때도 같다** — 실제 설정 파일의 값과 그 값을 만든 결정 기록을 먼저 찾는다(사례 2).

## 사례 1 — prompt-audit 의 제거 제안 (2026-09-24)

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
- 설정값이 문서·기본값과 다르거나 기본값이 바뀌어 동작이 달라졌다고 적기 전에, **실제 설정 파일의 값을 읽고** 그 키 이름으로 `plans/` 를 grep 해 그 값을 정한 결정이 있는지 본다. 결정이 있으면 "회귀"가 아니라 "그 결정의 범위"로 적고, 남은 미확인만 따로 적는다.

## 사례 2 — 결정된 설정값을 "미결 회귀"로 적음 (2026-09-27)

audit-docs-drift 에서 Opus 5.5 의 API 기본 effort 가 `medium` 이라는 공식 문서를 보고, opus 로 고정한 리뷰어가 Opus 5 시절(기본 `high`)보다 한 단계 낮은 `medium` 으로 돌고 복원 여부는 사용자 결정을 기다린다고 적었다 — 공용 wiki callout·index, plan Deferred("결정 필요"), 커밋 메시지. README 에는 M12 없이 모델 기본값 때문에 `medium` 으로 돈다고만 적었다. 실제로는 3일 전 prompt-audit-apply 의 **M12 결정**이 user settings `modelSettings` 에 Opus 5.5 = `medium` 을 명시 저장해 둔 상태였다. 근거와 되돌리기 기준은 그 plan 에 있다 — fix 과제 2×2 A/B 에서 medium·high 모두 숨은 테스트 9/9, fix 과제 비용 약 29% 절감(표본이 작아 accepted-risk), 놓침·재작업이 보이면 그 키만 `high` 로 복원. code-reviewer 가 settings 파일과 그 plan 을 읽어 잡았고, 게시 전 fixup 으로 "M12 결정의 범위 + 남은 미확인(세션 모델과 다른 고정 subagent 의 레벨)"으로 고쳤다([[effort-global-xhigh]]).

- 원인: 외부 사실(문서의 기본값)에서 곧바로 이 repo 의 상태를 추론했고, 실제 설정값과 그 값을 만든 plan 을 읽지 않았다. 왜 못 봤나 — M12 는 plan 에만 있고 wiki 에는 없었으며, user settings 는 repo 가 추적하지 않아 diff·repo 검색에 나오지 않는다. 사례 1 과 같은 축 — 현재 문장·문서만 보고 도입 경위를 건너뛰었다.
- 막은 것: 3일 전 근거·되돌리기 기준을 붙여 정한 결정을 새 근거 없이 다시 여는 것, 이미 있는 설정을 "새로 추가할 항목"으로 제안하는 것.

## 전후 비교는 증거로 만든다

같은 작업에서 적용 여부를 갈랐던 방법 — 재사용 가능하다.
- **transcript 전수 스캔**(`~/.claude/projects/**/*.jsonl`, subagent 는 `subagents/*.meta.json` 의 `agentType` 으로 식별): tool-call 누출 0건/수천 텍스트 블록 → 우회 규칙 제거, small 변경 code-reviewer 10건 중 1건이 실제 Major → 생략안 보류.
- **headless A/B**(`claude -p --model … --effort … --output-format json --no-session-persistence --setting-sources project`): 숨은 테스트로 채점하는 과제로 비용·시간·정답을 비교. 천장 효과(양쪽 만점)면 품질 차이는 말할 수 없다는 한계를 같이 적는다.

관련: [[workflow-failures]], [[evidence-gate]].
