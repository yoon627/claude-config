---
title: codex-bash-invocation
category: decision
created: 2026-06-19
updated: 2026-06-19
sources:
  - CLAUDE.md (§9)
  - PR #23
---

# codex-bash-invocation

Codex는 반드시 **Bash 도구**로 호출한다(PowerShell 도구 금지). PR #23에서 확정한 교훈.

## 함정
`codex exec`는 PROMPT 인자가 있어도 stdin을 추가로 읽는다. PowerShell 도구로 호출하면 stdin이 안 닫혀 `Reading additional input from stdin...`에서 **무한 hang**(재현됨). → Bash 도구로 `codex exec --sandbox read-only "<프롬프트>"`(검증됨).

## 운영 규칙
- 설치 확인: `codex --version`.
- 무거운 작업 전 짧은 smoke test(≤60s)로 응답부터 확인. hang/사용량 초과 시 즉시 중단 후 Claude 단독 진행 + 사유 명시.
- 원인은 재현으로 확정한 뒤 단정한다 — 과거 PowerShell hang을 'codex 불가'로 과일반화한 전례가 있어, 외부 CLI는 동작 검증 후 사용.

## 연계
Codex의 역할·리뷰 매트릭스는 [[claude-codex-collaboration]], 리뷰 관점은 [[dual-review-plan-and-code]].
