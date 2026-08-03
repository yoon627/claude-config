---
title: rtk-rewrite-guard — rtk 오재작성 6회 반복의 근본 원인 규명·기록 정정
status: in_progress
started: 2026-08-03
updated: 2026-08-03
---

# Goal

`workflow-failures` 표에 6회 누적된 "rtk-rewrite hook 이 복합 Bash 명령을 오재작성" 항목의 근본 원인을 확정하고, 잘못 기록된 수정 위치를 정정한다. 실제 해결(바이너리 업그레이드)은 사용자 환경 변경이라 제안까지.

# Progress

- 2026-08-03 재현·근본 원인 확정. 표에 적힌 가설(hook 재작성 조건 문제)이 **틀렸음**을 확인.

- 2026-08-03 wiki 정정·lesson 신설 완료, 검증 통과. 사용자가 업그레이드 대신 **headroom·codegraph 실사용 감사**를 지시 → 측정 완료(아래 Decisions).

# Next

repo 변경분(표 정정 + lesson) 커밋·PR·머지. 감사 결과 3건(effort=xhigh 웹툴 차단 / debug_400 1GB / codegraph 저효용)은 사용자 결정 대기.

# Decisions

- **근본 원인 = 설치된 rtk 가 6개월 묵음 (✅확실).** 상류 v0.44.2(2026-08-01) 대비 설치본 **0.28.2**. 우리가 맞은 두 실패는 상류에서 이미 수정됨:
  - `cmd: read/cat multiple file and consistent behavior` → **0.35.0**
  - `head/tail multi-file rewrite falls back to native command (#1362)` → **0.39.0**
- **표에 적혀 있던 수정 위치가 틀렸다.** `hooks/rtk-rewrite.sh` "재작성 조건 좁히기"로 기록돼 있었으나 ① 그 파일은 **얇은 위임자**로 rewrite 규칙이 하나도 없다(전부 rtk 바이너리 `src/discover/registry.rs`) ② `.gitignore:3` 로 **untracked·rtk 관리 파일**이라 고쳐도 업그레이드 때 덮인다. 그래서 6회 동안 "고칠 위치"를 잘못 보고 방치됐다.
- **in-repo 가드는 채택하지 않는다.** 상류에서 고쳐진 버그를 로컬 래퍼로 우회하는 건 증상 억제(§1). 업그레이드가 근본 해결.
- **도구 감사 결과 (2026-08-03, 측정치)** — 사용자 지시로 rtk 업그레이드 전에 headroom·codegraph 실효용을 측정:
  - **headroom 프록시 = 값을 한다.** API 요청 2582건 중 1644건 압축, 토큰 20.7M 제거, $103.87(13.7%) 절감. 번들 rtk 는 4731 명령에서 2.1M 토큰(64.7%) 절감. **다만 headroom MCP 도구는 사실상 미사용** — 298개 transcript 전수 스캔에서 `headroom_retrieve` 38회(압축이 가린 원문을 되찾는 *비용* 쪽), `headroom_compress` **0회**. 가치는 자동 프록시에 있고 MCP 표면엔 없다.
  - **headroom 디스크 위생 결함**: `~/.headroom/logs/debug_400/` 이 **1.0 GB · 673 파일**(개당 최대 5.2MB, 7월 것까지 잔존)이고 **로테이션이 없다**(proxy.log 는 10MB×3 로테이션 있음). `session_stats.jsonl` 은 0바이트 死파일. 이름과 달리 429 도 적재.
  - **codegraph = 이 repo 에선 저효용.** 인덱스가 **40 파일 / 602 노드**뿐 — js 22·py 17·yaml 1 만 인덱싱하고 이 repo 지식의 대부분인 **Markdown(CLAUDE.md·skills·wiki)은 전혀 안 들어간다**. 실사용도 298 transcript 에서 30회(`explore` 16, 마지막 실사용 2026-07-30). 반면 비용은 상시: `/wt` 마다 백그라운드 init(worktree 당 ~1.4MB), worktree 인덱스 stale(수동 `codegraph sync` 필요 — memory `codegraph-projectpath-explicit`), `wt rm` 시 daemon 파일점유 실패(`rm-recovery.md` §C). 코드 39파일 규모라 Read/Grep 이 더 싸다.
  - **별건 발견 — `effort=xhigh` 가 웹 도구를 죽인다 (✅확실).** `settings.json:3` `CLAUDE_CODE_EFFORT_LEVEL=xhigh` + `:268` `effortLevel: xhigh`. 이번 세션 WebSearch·WebFetch 가 전부 `400 output_config.effort 'xhigh' is not supported when thinking is disabled on this model` 로 실패해 curl 스크래핑으로 우회했다. 웹 검색이 필요한 모든 작업(CLAUDE.md §4)이 무력화된다. headroom·codegraph 와 무관한 설정 문제.
- **rtk 는 headroom 번들 소유.** `~/.local/bin/rtk` → `~/.headroom/bin/rtk` 심링크(기존 memory `rtk-headroom-path-fix` 의 그 심링크). 업그레이드는 headroom 설치물을 건드리므로 **사용자 승인 대상**(§1 애매하면 확인). 가장 안전한 경로는 headroom 바이너리를 두고 **심링크만 새 rtk 로 재지정**(되돌리기 = 심링크 원복 1줄).

# Key Files

- `wiki/pages/decision/workflow-failures.md` — rtk 항목 근본원인·수정위치·상태 정정
- `wiki/pages/decision/lesson-stale-tool-version.md` — (신설) 외부 도구 오작동은 버전 대조부터
- `wiki/index.md`·`wiki/log.md` — 등재 동기화

# Blockers

(없음 — repo 변경분은 진행 가능. 업그레이드만 사용자 결정 대기)

# Acceptance

| 항목 | 검증 | 통과 기준 |
|---|---|---|
| 1. 재현·근본원인 증거 | `rtk rewrite` / `rtk read` 실행 로그 | `tail -160 f`→`rtk read -160 f`→`/usr/bin/read: invalid option` 관찰됨 ✅ |
| 2. 상류 수정 버전 확정 | CHANGELOG 파싱 | 0.35.0·0.39.0 매핑 확인됨 ✅ |
| 3. 표 정정 | `workflow-failures.md` read | 근본원인·수정위치·상태가 실제와 일치 |
| 4. lesson 적립 | 페이지 + index + log | dead link 0, index 개수 일치 |
| 5. 회귀 없음 | CI 등가(단위테스트 8종·JSON·shellcheck) + `improve.sh` | 전부 통과, error=0 |

# Review Disposition

(fix loop 시 기록)

# Deferred

(없음)

# Workflow Findings

- **workflow-failures 표의 "수정 후보 위치"가 검증 없이 기록돼 6회 동안 잘못된 방향을 가리켰다.** 표 항목을 적을 때 수정 위치를 *추정*으로 채우면 반복 해결이 영영 안 된다 — 위치는 확인된 것만 적거나 "미확정"으로 남겨야 한다.
