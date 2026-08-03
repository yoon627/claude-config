---
title: codegraph
category: entity
created: 2026-06-21
updated: 2026-08-03
sources:
  - npm @colbymchenry/codegraph@0.9.9 (codegraph --help, 2026-06 확인)
  - 이 repo settings.json·skills/wt/SKILL.md
  - 2026-08-03 사용량 감사 (transcript 298개 전수 스캔 + codegraph_status)
---

# codegraph

코드 심볼 그래프 MCP 서버. SQLite 지식그래프로 심볼·엣지·파일을 인덱싱해 sub-ms 조회를 제공한다. 이 repo 워크플로우(dlc Explore·코드 조회)가 의존하는 핵심 MCP 도구로, [[headroom]] 과 함께 글로벌 MCP(`~/.claude.json`)에 등록된다.

## 설치·등록
- 설치: `npm install -g @colbymchenry/codegraph` (node 스크립트, 0.9.9).
- MCP 등록: `codegraph install -y` (claude global, `codegraph serve --mcp`).
- 인덱스: `codegraph init <repo>` → `.codegraph/`(SQLite, 루트 `.gitignore` whitelist).

## worktree-local 인덱스
[[dlc-wt-autoflow]] 의 wt 가 새 worktree 생성 시 **조건부**(codegraph 바이너리 PATH + main worktree 에 `.codegraph/`)로 `codegraph init` 을 백그라운드 실행한다 — worktree 변경이 main 인덱스(=main 브랜치 코드)에 가려지지 않게 worktree-local 인덱스를 만든다(skills/wt/SKILL.md). 단 이 인덱스는 **init 시점 스냅샷**이다 — worktree 엔 live watcher 가 없어(auto-sync watcher 는 MCP 서버 root=main 에서만) 이후 편집은 자동 반영되지 않고, 조회 전 `codegraph sync <worktree>` 재실행이 필요하다(2026-07-19 실측; 상세·근거 memory `codegraph-projectpath-explicit`). worktree 삭제 시 `.codegraph/` 를 codegraph daemon 이 점유할 수 있어 OS 삭제 실패에 주의.

## 실사용 감사 (2026-08-03) — 이 repo 에선 끔

transcript 298개 전수 스캔 결과 codegraph MCP 호출은 **총 30회**이고 분포가 갈린다:

| 프로젝트 | 호출 | transcripts |
|---|---|---|
| coin-trading-bot (+worktree 3종) | **21** | 175 |
| `~/.claude` (이 repo) | 7 | 48 |
| conductor | 2 | 68 |

이 repo 에서 저효용인 이유는 **인덱스가 이 repo 지식을 거의 못 담기 때문**이다 — `codegraph_status` 기준 40 파일 / 602 노드뿐이고 언어는 js 22·py 17·yaml 1. 이 repo 의 실체인 **Markdown(CLAUDE.md·skills·wiki)은 인덱싱 대상이 아니다**. 코드가 39파일 규모라 Read/Grep 이 더 싸고 정확하다. 반면 비용은 상시였다: worktree 마다 백그라운드 init(~1.4MB), init 시점 스냅샷의 stale 화, `wt rm` 시 daemon 파일점유.

**조치**: `~/.claude/.codegraph/` 만 삭제했다. 위 "worktree-local 인덱스" 게이트가 *main worktree 에 `.codegraph/` 있을 때만* init 하므로, 인덱스를 지우는 것만으로 이 repo 계열의 자동 init 이 멈춘다 — 코드·문서 변경 0. **MCP 서버(`~/.claude.json` root)는 유지**해 실사용의 70%인 coin-trading-bot 은 영향받지 않는다. 되돌리기: `codegraph init ~/.claude`.

> [!open] 전역 사용량 자체가 298 transcript 에 30회로 낮다. 코드 repo 에서도 값을 하는지는 별도 측정이 필요하다 — 이번 감사는 "이 repo 에서 끄는" 판단까지만 근거를 갖는다.

## 부트스트랩
새 머신 재현은 [[headroom]] 과 함께 `scripts/bootstrap/setup.sh` 가 처리(설치 → MCP 등록 → init).
