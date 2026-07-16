---
title: feedback-memory
category: concept
created: 2026-06-19
updated: 2026-07-05
sources:
  - CLAUDE.md (§12 피드백 메모리)
  - MEMORY.md
  - skills/c/SKILL.md (/c PR 리뷰 intake)
---

# feedback-memory

사용자가 작업 방식 교정을 영속화하라고 지시하면("기억해 / 규칙으로 / 다음부턴 이렇게") 하니스 메모리 `type: feedback`으로 저장하는 메커니즘(CLAUDE.md §12). 목표는 저장이 아니라 **다음 작업에서의 실제 반영**. [[project-memory]]의 행동-교정 측면이며, [[llm-wiki-pattern|wiki]](지식 적립)와는 별개 저장소다.

## 인덱스를 행동 지시문으로
`MEMORY.md` 인덱스 줄만 매 세션 항상 주입된다(본문은 관련 있을 때만 recall). 그래서 인덱스를 *정보 요약*이 아니라 **명령형 행동 규칙**으로 쓴다: "notify-hook 알림 버그 메모" ✗ → "코드 변경 시 주석·문서도 같은 커밋에서 갱신" ✓. 본문엔 사례·Why·How.

## 2단계 저장
메모리 파일 생성 + `MEMORY.md` 인덱스 한 줄 추가 — **둘 다**. 인덱스를 빠뜨리면 본문이 묻혀 반영 안 됨(인덱스 갱신은 자동 아님).

## 승격·유지
보편·중대 규칙은 CLAUDE.md 해당 섹션으로 승격(전문이 100% 주입)하고 메모리는 정리. 모순되면 옛 것을 새 것으로 교체, 죽은 규칙은 삭제(계속 주입돼 방해).

## self-improvement와의 관계
feedback-memory는 *사용자가 지시할 때* 저장한다. Claude가 실수를 **자발적으로** 감지해 기록하는 트리거(self-improve-trigger)는 검토 후 **미채택·폐기**(2026-06-19) — [[self-diagnosis-and-improvement-status]]. 사용자 지시 기반 저장 + self-diagnosis(사후 감지) 조합으로 간다. **CLAUDE.md §13(실수·교훈 로그)** 은 이 조합의 산출 규약 — 사후 감지되거나 사용자가 지적한 실수를 wiki lesson + `MEMORY.md` 인덱스로 적립(첫 사례 [[lesson-grep-absence-not-proof]]). "자발적 무승인 자동저장" 금지는 유지되고, §13 은 *적립 형식*을 정할 뿐이다.

## /c PR 리뷰 intake (유입 경로)
plan 이어받기(`/c`)가 그 브랜치 PR 의 **사람** 리뷰 코멘트를 수집해, 작업방식 교정성 지적을 이 feedback-memory 저장 **판정**으로 넘긴다 — "사용자 코드리뷰 → 개선 → 기억" 루프의 자동 유입 경로. 코드 지적은 `# Next`(fix)로, 저장 자체는 여전히 §12 대로 사용자 확인 후.
