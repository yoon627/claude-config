---
title: project-memory
category: concept
created: 2026-06-16
updated: 2026-09-26
sources:
  - plans/2026-06-15-llm-wiki/llm-wiki-plan.md
  - plans/2026-09-26-wiki-ingest-audit-lessons (여러 repo 사이 — 사용자 결정)
  - plans/2026-09-26-wiki-shared-layer (두 계층 구현)
---

# project-memory

이 wiki 의 목적: 이 repo·워크플로우 작업에서 나온 **재사용 가능한 개발 지식**(아키텍처 결정·교훈·검증된 외부 사실)을 작업을 가로질러 누적한다. [[llm-wiki-pattern]] 을 이 용도로 구현한 것.

## plans/ 와의 경계 (핵심)
- `plans/` = 한 작업의 **일시적** 핸드오프. `in_progress → done` 후 닫힌다. 브랜치와 함께 커밋되는 tracked 파일이다(CLAUDE.md §10).
- `wiki/` = 작업을 **가로지르는 영속·누적**. git-tracked.
- 관계: dlc 는 plan 으로 "지금 이 작업"을 추적하고, wiki 로 "작업이 끝나도 남길 지식"을 적립. plan `# Decisions` 중 **미래 작업이 재사용할 것만** wiki `decision/` 으로 **일방향 승격**(양방향 동기화 금지 — 중복 동기화 회피).

## 적재 경로
- 외부 사실(버전/API/CVE) → `entity/`. 이 repo·전역 자산의 결정·교훈 → `decision/`. 절차는 [[ingest-operation]].

## 여러 repo 사이
repo 고유 결정은 각 repo 의 `wiki/` 에, 여러 repo 에 쓸모 있는 공개 가능한 사실과 전역 자산의 교훈은 공용 `~/.claude/wiki`(이 wiki)에 둔다. 모든 repo 세션이 두 index 를 조회하고, 다른 repo 세션에서 나온 공용 지식은 제안으로만 넘어온다(CLAUDE.md §11, 2026-09-26 구현). 이 wiki 는 공개 repo 에 있어 회사·비공개 정보를 넣지 않는다(점검 표면은 CLAUDE.md §11 공개 점검). 계층 규칙과 submodule 기각 근거는 [[wiki-shared-layer]].
