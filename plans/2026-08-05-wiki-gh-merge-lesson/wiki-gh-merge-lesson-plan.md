---
title: wiki-gh-merge-lesson — gh pr merge --delete-branch worktree 실패 §13 적립
status: in_progress
started: 2026-08-05
updated: 2026-08-05
---

# Goal
CLAUDE.md §8 이 권장하던 `gh pr merge --delete-branch` 가 worktree 워크플로우에서 항상 실패한 건(PR #123 에서 수정)을 `wiki/pages/decision/workflow-failures.md` 추적표에 영속 적립한다. 부수로 관측된 `doc-drift-readme` 오탐(CLAUDE.md 절 단위 수정) 1건을 기존 행에 가산한다.

# Progress
- 2026-08-05: 다른 세션 확인(e7c4c921 중단·03f014b5 는 settings.json 조사 중 — 파일 충돌 없음). PR #120 중복 판정 후 close(브랜치 유지). 증거 수집: `31be25b` 커밋 메시지(실측), telemetry `dlc-signals.jsonl` 집계.

- 2026-08-05: wiki 3파일 편집 완료(표 신규 행 + doc-drift 5→6 + 횟수 semantics 주의, index/log 동기화). 표 컬럼 정합 확인, CI 스위트 전 항목 통과(Node syntax·unit 9종·Python 3종·plan-lint·JSON·shellcheck). simplify 체크로 index 한 줄 축약. code-reviewer subagent 는 세션 지시("Agent 는 요청 시에만")로 미호출 — 메인 직접 점검 대체.

# Next
commit → push → PR → 머지 후 worktree 정리.

# Decisions
- 새 lesson 페이지(`lesson-*.md`)를 만들지 않고 기존 [[workflow-failures]] 추적표 행으로 적립 (이유: 실패 주체가 *규약 자체*라 이 표의 정의와 정확히 일치하고, e7c4c921 이 제안한 위치도 이 파일).
- doc-drift-readme 횟수는 **5→6 만** 올린다 (이유: telemetry 실측상 CLAUDE.md detail 신호는 세션 e7c4c921 의 1건. hook 이 세션당 capped 라 "PR #121·#123 2건"은 신호 1건으로 집계됨 — 2 가산은 이중계상).
- 2026-08-04 `.test.js` detail 신호는 **건드리지 않는다** (이유: 별개 FP class 이고 다른 세션의 `/improve` 1순위 후보라 소유권 분리).

# Key Files
- `wiki/pages/decision/workflow-failures.md` — 추적표(적립 대상)
- `wiki/index.md` — 페이지 1줄 요약 카탈로그
- `wiki/log.md` — append-only 연산 로그

# Blockers
없음.

# Acceptance
1. workflow-failures 표에 gh merge 실패 행 존재 — 근본원인(base checkout 점유)·재발조건·수정위치·상태 `fixed (2026-08-05)` + 근거 커밋 `31be25b` 포함. 검증: `grep -c 'delete-branch' wiki/pages/decision/workflow-failures.md` ≥1
2. doc-drift-readme 행 횟수 `5`→`6`, 재발 조건에 CLAUDE.md 절 단위 수정 사례 반영. 검증: 해당 행 육안 + grep
3. frontmatter `updated: 2026-08-05` + `sources` 에 근거 추가. 검증: head 확인
4. `wiki/index.md` 요약이 표 내용과 어긋나지 않고, `wiki/log.md` 에 이번 연산 append. 검증: grep
5. CI 검증 스위트 통과(문서 변경이라 회귀 없음 확인). 검증: `.github/workflows/lint.yml` 의 Node/Python 테스트 + `node scripts/plan-lint.js` 이 plan

# Deferred
- `find_codex_session_files_for_worktrees` (PR #120 의 유일한 순증분 — Codex rollout 을 worktree 마다 재-glob 하지 않고 1회 스캔). 심각도 낮음(성능 nit), 소스는 `origin/jira-worklog-cwd-attribution@7826953` 에 보존. `skills/jira-worklog/jira_worklog.py:186`.
- `jira_worklog.py` docstring 이 "코퍼스는 한 번만 스캔"이라 주장하나 Codex 경로는 worktree 마다 재-glob — 서술·동작 불일치. 위 항목과 함께 처리 대상.

# Workflow Findings
- (이번 작업 자체에서 발생한 workflow 실패 없음)
