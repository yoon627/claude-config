---
title: comment-and-commit-policy
category: decision
created: 2026-06-19
updated: 2026-06-19
sources:
  - CLAUDE.md (§6 코드 규칙, §3-5 Verify)
  - PR #25, #26, #34
---

# comment-and-commit-policy

주석과 커밋 메시지에 대한 이 repo의 규약(PR #26 주석 최소화, #34 변경경위 금지, #25 현행성 확인). 핵심: **주석은 "이 코드가 지금 왜 이래야 하나"(제약)에 답하지, "왜 바꿨나"(경위)에 답하지 않는다.**

## 규칙
- **주석은 없는 게 기본** — 주석 없이 읽히는 코드가 최선. 자명한·코드를 그대로 옮긴 주석 금지. 표현 가능한 의도는 네이밍·구조로. 코드에 안 드러나는 *왜*(우회·트레이드오프·비자명한 제약)만 최소 줄로.
- **변경 경위는 주석이 아니라 커밋/PR에** — "버그 X 수정", "리뷰 반영", "원래 ~였음", "안전을 위해 추가" 같은 *왜 바꿨는가*는 코드에 남기지 않는다.
- **죽은 코드는 삭제**(git이 기억), 임시 코드는 `# TODO: <이유> (<제거 조건>)`.
- **현행성**(§3-5 Verify): 주석·docstring·commit message가 변경된 코드의 *현재 동작*과 어긋나지 않는지 항상 확인 — 특히 리팩토링·rename·fixup 흡수 후.

## 왜
CLAUDE.md가 길면 절반이 무시될 수 있다 — 규칙은 신규 추가보다 기존 줄 보강으로 줄 수를 중립 유지한다(claude-md-improvement 교훈). 이 정책도 [[dlc-development-cycle]] Verify 단계에 바인딩된다.

## 연계
범위 밖 발견 처리는 [[deferred-and-scope-boundary]].
