---
title: harness-keep-and-borrow
category: decision
created: 2026-08-05
updated: 2026-08-05
sources:
  - researcher 조사 2026-08-05 (본 세션 — [[claude-code-oss-frameworks]])
  - https://github.com/buildermethods/agent-os/discussions/310
---

# harness-keep-and-borrow

"자작 하네스를 유지할까, 오픈소스로 갈아탈까"에 대한 결정 (2026-08-05, 사용자 승인): **유지 + 부품 선별 차용, 전면 이주 비채택.**

## 이유
1. **대체 대상 부재**: 이 하네스의 차별점은 오케스트레이션(네이티브가 흡수 중)이 아니라 **규율 강제·검증 장치**(worktree 게이트 hook·evidence ledger·plan-lint·doc-drift 감지·[[claude-codex-collaboration]] 교차리뷰·[[llm-wiki-pattern]] wiki) — 이를 하나로 묶은 동급 오픈소스가 없다([[claude-code-oss-frameworks]]).
2. **프레임워크 진영의 후퇴**: Agent OS v3가 자체 기능을 네이티브에 이양·폐기, 2025년 세대 도구 집단 정체 — 프레임워크에 올라탔다면 이주 비용을 재차 치르는 중.
3. **정책 안전성**: 외부 하네스는 구독 차단 리스크(2026-04), 내부 확장(skill/hook/agents)은 무관.

## 조건 (유지의 대가)
- **유지비 감시**: 이 repo에 최근 3개월 296커밋 — 하네스 유지보수 시간이 실제 개발을 잠식하면 축소가 답.
- **역방향 정리**: Claude Code 네이티브가 흡수한 기능(subagent 영속 메모리, worktree commit/push/draft PR 자동화, plan mode 강화 등)과 중복된 자작 부분을 주기 점검·제거 — `/improve`의 점검 축으로 추가 (2026-08-05 승인, 구현 대기).

## 차용 목록 (전면 이주 아닌 부품)
- OpenSpec의 **archive** 개념 → `plans/` `status: done` 이후 보존 규약 후보.
- superpowers 개별 skill(마켓플레이스 경유) → [[dlc-development-cycle]] 보강 후보 — 도입 전 실품질 로컬 검증.
- zen-mcp의 합의 리뷰 패턴은 참고만 — 현행 Bash codex 직접 호출([[codex-bash-invocation]])이 MCP 스키마 상주 토큰 없이 더 경량.

> [!open] 구현 대기: /improve에 "네이티브 중복 점검" 축 추가 — 별도 worktree 작업.
