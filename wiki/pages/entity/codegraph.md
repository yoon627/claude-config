---
title: codegraph
category: entity
created: 2026-06-21
updated: 2026-09-15
sources:
  - npm @colbymchenry/codegraph@0.9.9 (codegraph --help, 2026-06 확인)
  - 이 repo settings.json·skills/wt/SKILL.md (당시)
  - 2026-08-03 사용량 감사 (transcript 298개 전수 스캔 + codegraph_status)
  - 2026-09-15 retire 조사 (Claude transcript 310개·Codex 세션 627개의 실제 호출·결과 집계)
  - memory codegraph-projectpath-explicit (retire 로 삭제 대상 — 실측 수치는 아래 worktree-local 인덱스 절로 이관)
---

# codegraph

> [!note] Retired (2026-09-15)
> wt 자동 init·bootstrap 설치 단계를 제거하고, Claude·Codex 전역 MCP 등록은 머지 후 전역 단계에서 해제한다(완료 확인은 plan `remove-codegraph-mcp` Acceptance 6). 아래 설치·인덱스·감사 내용은 과거 운영 기록으로 보존한다.

코드 심볼 그래프 MCP 서버. SQLite 지식그래프로 심볼·엣지·파일을 인덱싱해 sub-ms 조회를 제공한다. 과거 dlc Explore·코드 조회용으로 [[headroom]]과 독립적으로 글로벌 MCP(`~/.claude.json`)에 등록했었다.

## 설치·등록 (historical)
- 설치: `npm install -g @colbymchenry/codegraph` (node 스크립트, 0.9.9).
- MCP 등록: `codegraph install -y` (claude global, `codegraph serve --mcp`).
- 인덱스: `codegraph init <repo>` → `.codegraph/`(SQLite, 루트 `.gitignore` whitelist).

## worktree-local 인덱스 (historical)
[[dlc-wt-autoflow]] 의 wt 가 새 worktree 생성 시 **조건부**(codegraph 바이너리 PATH + main worktree 에 `.codegraph/`)로 `codegraph init` 을 백그라운드 실행했다 — worktree 변경이 main 인덱스(=main 브랜치 코드)에 가려지지 않게 하려는 것. 운영 중 확인한 한계:
- **세션 기본 조회는 시작 시점 인덱스에 고정** — EnterWorktree 이후·merge 반영 후에도 stale 해 `projectPath` 를 명시해야 했다(2026-07-04 실측: 같은 커밋에서 기본 17파일/172노드 vs `projectPath` 명시 20파일/221노드).
- **worktree 인덱스엔 live watcher 가 없었다** — auto-sync watcher 는 MCP 서버가 기동 시 바인딩한 root(=main)에서만 돌고, worktree-local `.codegraph/` 는 init 시점 스냅샷이라 조회 전 `codegraph sync <worktree>` 가 필요했다(2026-07-19 실측: worktree init 28파일 후 새 심볼은 sync 전 검색 불가 → sync 후 29파일/+3노드).
- worktree 삭제 시 `.codegraph/` 를 codegraph daemon 이 점유해 OS 삭제가 실패할 수 있었다.

## 실사용 감사 (2026-08-03) — 이 repo 에선 끔

transcript 298개 전수 스캔 결과 codegraph MCP 호출은 **총 30회**이고 분포가 갈린다:

| 프로젝트 | 호출 | transcripts |
|---|---|---|
| coin-trading-bot (+worktree 3종) | **21** | 175 |
| `~/.claude` (이 repo) | 7 | 48 |
| conductor | 2 | 68 |

이 repo 에서 저효용인 이유는 **인덱스가 이 repo 지식을 거의 못 담기 때문**이다 — `codegraph_status` 기준 40 파일 / 602 노드뿐이고 언어는 js 22·py 17·yaml 1. 이 repo 의 실체인 **Markdown(CLAUDE.md·skills·wiki)은 인덱싱 대상이 아니다**. 코드가 39파일 규모라 Read/Grep 이 더 싸고 정확하다. 반면 비용은 상시였다: worktree 마다 백그라운드 init(~1.4MB), init 시점 스냅샷의 stale 화, `wt rm` 시 daemon 파일점유.

**조치**: `~/.claude/.codegraph/` 만 삭제했다. **MCP 서버(`~/.claude.json` root)는 유지**해 실사용의 70%인 coin-trading-bot 을 보호했다. 이 감사는 호출 횟수만 셌고 성공 여부는 세지 않았다.

## Retire (2026-09-15) — 전역 해제

2026-08-03 의 "전역 MCP 유지" 판단을 뒤집었다. 근거:

| 출처 | 기간 | 실제 호출 | 결과 |
|---|---|---|---|
| Claude transcript 310개 | 2026-08-06 ~ 09-15 | 7회(전부 `explore`, coin-trading-bot) | 7회 모두 `CodeGraph not initialized` / `No CodeGraph project is loaded` 에러 |
| Codex 세션 627개 | 2026-06 ~ 07 | 38회 | 결과 21건 전부 `user cancelled MCP tool call`, 17건 결과 미기록 |

- 보호하려던 실사용처 coin-trading-bot 을 포함해 홈 depth 5 이내 탐색에서 `.codegraph/` 가 하나도 없었다 — 호출하면 반드시 실패하는 상태로 매 세션 MCP 지침 토큰만 들고 있었다.
- "성공 0회"는 **보존된 로그 기간 한정**이다. 2026-08-03 감사 기간(30회)의 원본은 보존기간으로 사라져 성공 여부를 다시 셀 수 없다.
- 토큰 절감량은 직접 측정할 수 없다 — codegraph 에 사용 통계 명령·저장소가 없고, 대신 Read/Grep 을 썼을 때의 비용도 기록되지 않는다.
- 기각한 대안: coin-trading-bot 프로젝트 scope 로만 MCP 유지(인덱스가 없어 여전히 실패), 인덱스 재생성 후 유지(코드 repo 에서 값을 한다는 증거 0).
- 2026-08-03 의 `[!open]`(코드 repo 에서 값을 하는지 별도 측정 필요)은 **측정 없이 retire 로 종결**했다 — 측정할 인덱스가 남아 있지 않았다.
- 조치: 레포에서 wt 자동 init(참조 문서 포함)·bootstrap 설치/등록/init 단계 제거. 전역 단계(`claude mcp remove`·`codex mcp remove`·settings.json 허용목록·npm 전역 바이너리)는 머지 후 수행한다. 되돌리기: `npm install -g @colbymchenry/codegraph && codegraph install -y`.

## 부트스트랩 (historical)
새 머신 재현은 `scripts/bootstrap/setup.sh`가 설치 → MCP 등록 → init 을 처리했으나 2026-09-15 제거했다 — 현재 bootstrap 은 codegraph 를 다루지 않는다.
