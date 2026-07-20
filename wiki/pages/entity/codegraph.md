---
title: codegraph
category: entity
created: 2026-06-21
updated: 2026-07-19
sources:
  - npm @colbymchenry/codegraph@0.9.9 (codegraph --help, 2026-06 확인)
  - 이 repo settings.json·skills/wt/SKILL.md
---

# codegraph

코드 심볼 그래프 MCP 서버. SQLite 지식그래프로 심볼·엣지·파일을 인덱싱해 sub-ms 조회를 제공한다. 이 repo 워크플로우(dlc Explore·코드 조회)가 의존하는 핵심 MCP 도구로, [[headroom]] 과 함께 글로벌 MCP(`~/.claude.json`)에 등록된다.

## 설치·등록
- 설치: `npm install -g @colbymchenry/codegraph` (node 스크립트, 0.9.9).
- MCP 등록: `codegraph install -y` (claude global, `codegraph serve --mcp`).
- 인덱스: `codegraph init <repo>` → `.codegraph/`(SQLite, 루트 `.gitignore` whitelist).

## worktree-local 인덱스
[[dlc-wt-autoflow]] 의 wt 가 새 worktree 생성 시 **조건부**(codegraph 바이너리 PATH + main worktree 에 `.codegraph/`)로 `codegraph init` 을 백그라운드 실행한다 — worktree 변경이 main 인덱스(=main 브랜치 코드)에 가려지지 않게 worktree-local 인덱스를 만든다(skills/wt/SKILL.md). 단 이 인덱스는 **init 시점 스냅샷**이다 — worktree 엔 live watcher 가 없어(auto-sync watcher 는 MCP 서버 root=main 에서만) 이후 편집은 자동 반영되지 않고, 조회 전 `codegraph sync <worktree>` 재실행이 필요하다(2026-07-19 실측; 상세·근거 memory `codegraph-projectpath-explicit`). worktree 삭제 시 `.codegraph/` 를 codegraph daemon 이 점유할 수 있어 OS 삭제 실패에 주의.

## 부트스트랩
새 머신 재현은 [[headroom]] 과 함께 `scripts/bootstrap/setup.sh` 가 처리(설치 → MCP 등록 → init).
