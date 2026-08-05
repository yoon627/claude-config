---
title: claude-code-oss-frameworks
category: entity
created: 2026-08-05
updated: 2026-08-05
sources:
  - researcher 조사 2026-08-05 (GitHub API 직접 조회 — 본 세션)
  - https://news.ycombinator.com/item?id=45155302 (Framework Wars)
  - https://github.com/buildermethods/agent-os/discussions/310 (Agent OS v3)
---

# claude-code-oss-frameworks

Claude Code 위 오픈소스 워크플로우 프레임워크 생태계 스냅샷 (★·push는 2026-08-05 GitHub API 조회). [[harness-keep-and-borrow]] 판단의 근거 데이터.

## 활발 (2026-08 push)
- **superpowers** (obra) 266.9k★ — skills 프레임워크+방법론(brainstorm→plan→TDD→subagent 구현·리뷰). 생태계 1위. ★ 급성장이 이례적이라 skill 실품질은 로컬 검증 권장.
- **spec-kit** (github) 125.4k★ — spec 주도 4단계(Specify→Plan→Tasks→Implement). Martin Fowler 평 "verbose and tedious to review".
- **claude-flow** 67.1k★ — 멀티에이전트 스웜 meta-harness. open issue 786개·범위 팽창 → 도입 리스크.
- **OpenSpec** 63.9k★ — 경량 spec 주도(proposal→apply→verify→**archive**). 이 repo `plans/` 규약과 가장 유사.
- **claude-mem** 89.7k★ — 자동 캡처·압축·주입형 메모리(Apache-2.0).
- **BMAD-METHOD** 51.5k★ — 역할 에이전트+PRD 중심 방법론. "무겁다" 비판 상수 → Quick Flow 트랙 추가.

## 정체/축소 (2026년 들어 push 중단·전환)
- claude-task-master 27.9k★ (04월~) · ccpm 8.3k★ (03월~) · **zen-mcp-server** 11.7k★ (2025-12~, 교차모델 리뷰 대표) · Crystal(상용 Nimbalyst 전환) · Agent OS 5.2k★ — **v3에서 spec·태스크·오케스트레이션을 전부 Claude Code 네이티브에 이양하고 자체 기능 폐기** (프레임워크가 네이티브 업데이트로 무용화된 공식 사례).

## 구조적 사실
1. **커버리지는 부분적** — spec 문서·skills·병렬 실행 관리는 있으나, 규율 강제(worktree 게이트 hook)·Codex 교차리뷰·evidence ledger·doc-drift 감지·자기개선 루프에 해당하는 오픈소스 대응물은 조사에서 미발견.
2. **커뮤니티 수렴**: Framework Wars 스레드 회의론 다수("과한 ritual은 모델 학습 분포와 어긋난다"), 메모리 도구 스레드 최다 추천 = "plain markdown을 이긴 메모리 도구가 없다" — [[llm-wiki-pattern]] 계열의 손을 들어줌.
3. **정책 리스크 비대칭**: 2026-04 Anthropic이 구독 자격증명의 외부 하네스(OpenClaw류) 사용 차단 — 외부 하네스는 리스크, **Claude Code 내부 확장(skill/hook/agents)은 안전한 형태**.
4. 2025년 세대 도구들의 2026년 집단 정체 = 네이티브 흡수 추세의 방증 (plan mode·subagent memory·worktree 자동화·Dynamic Workflows 등).
