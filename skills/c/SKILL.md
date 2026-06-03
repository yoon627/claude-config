---
name: c
description: 현재 worktree/repo 의 진행 중인 plan(CLAUDE.md §10)을 찾아 남은 작업과 plan↔실제(git/코드) sync 상태를 진단하고, 어긋나면 plan 을 보정한 뒤 다음 액션을 제시하는 plan 이어가기(plan-continue) 오케스트레이션. `/c` 명시 호출 또는 "진행하던 작업 이어가자"류 요청 시 사용. branch→plan dir 매칭, 실패 시 in_progress 목록 제시. 확인·sync 진단은 항상 수행하되 다음 액션은 제시만 하고 자동 실행하지 않는다. 단순 질문·탐색·신규 작업 시작에는 쓰지 않는다(새 plan 생성은 dlc 몫).
---

# c — plan 이어가기 (plan continue)

진행 중이던 §10 plan 을 찾아 **남은 작업 + sync 상태**를 진단하고, 어긋난 plan 을 실제 상태로 보정한 뒤 다음 액션을 제시한다. CLAUDE.md §10 "시작: 매칭 plan read 후 컨텍스트 복원 / 진행 중 동기화"의 자동화 버전 — **충돌 시 CLAUDE.md 우선**.

## 적용
- `/c` 명시 호출, 또는 진행하던 plan 을 이어가려 할 때.
- 단순 질문·탐색·읽기 전용·신규 작업 시작은 제외. **plan 이 없으면 새로 만들지 않는다** (그건 dlc/작업 시작의 몫).

## 동작 (3단계: 찾기 → 진단 → 보정·제시)

### 1. plan 찾기
- `ROOT = git rev-parse --show-toplevel`, `BR = git rev-parse --abbrev-ref HEAD`.
- 탐색 위치 (존재하는 것만, 중복 제거):
  1. `<ROOT>/plans/`
  2. cwd 가 worktree 일 때 main worktree 의 plans — `git worktree list --porcelain` 의 첫 `worktree <path>` 라인 → `<main>/plans/`. (1)과 동일하면 생략.
  > plans/ 는 gitignored & worktree 별 독립이라 양쪽을 봐야 누락이 없다.
- **매칭** (§10 규칙): `BR` 문자열이 plan **dir 이름**(`<YYYY-MM-DD>-<slug>`)에 포함되는 dir → 그 안의 `*-plan.md` 1개.
  - 1개 → 채택.
  - 2개+ → 후보 목록 제시 후 사용자 선택.
  - 0개 → fallback.
- **fallback (매칭 0개)**: 탐색 위치의 모든 plan(`*/*-plan.md` + 루트 직속 `*.md`) frontmatter 를 읽어 `status: in_progress|blocked` 인 것을 `updated` 내림차순으로 **목록 제시 → 사용자 선택**. 추측으로 자동 선택하지 않는다. 전부 done 이거나 없으면 "이어갈 plan 없음" 보고 후 종료.

### 2. 진단 (plan read 후)
plan 을 read 하고 두 축을 본다.
- **남은 작업**: `status` + `# Next` + `# Blockers`.
  - `done` → "이미 done" 안내 후 그래도 이어갈지 확인.
  - `blocked` → `# Blockers` 노출, 해소 가능 여부 판단.
  - `# Next` 가 비었거나 실효 → 3단계에서 실제 상태로 재구성.
- **sync 점검** (plan ↔ 실제):

  | 점검 | 방법 | 어긋남 신호 |
  |---|---|---|
  | 최신성 | frontmatter `updated` vs 최근 커밋 날짜 | `updated` 가 한참 과거 |
  | Key Files 실재 | `# Key Files` 경로 존재 확인 | 없는/이동된 파일 |
  | 커밋 반영 | `git log --oneline -15` (plan 시작 이후) | `# Progress` 에 없는 커밋 |
  | 미반영 변경 | `git status --short` | Progress/Next 에 없는 uncommitted |
  | 완료 여부 | `git log --oneline origin/main..HEAD` 비었나 / `git branch --merged origin/main` | 머지됐는데 `status≠done` |

  - 점검 명령이 실패(origin 없음 등)하면 그 점검만 skip 하고 보고에 명시.

### 3. 보정 + 다음 액션 제시 (그리고 멈춤)
- sync 어긋남이 있으면 **plan 파일을 먼저 보정** (메인이 single writer; §10 진행중 동기화):
  - 새 커밋 → `# Progress` 한 줄씩 추가.
  - uncommitted 변경 → 현황 반영.
  - 없어진/이동된 파일 → `# Key Files` 갱신.
  - 실제와 다른 `status` → 정정(머지=done, 막힘=blocked + `# Blockers`).
  - 실효된 `# Next` → 실제 다음 액션으로 교체.
  - frontmatter `updated:` 오늘로.
  - 기존 `# Decisions` 는 지우지 말고 §10 방식(덮어쓰기/추가 + 이유).
- 그 다음 **요약 보고 후 멈춘다** (다음 액션을 자동 실행하지 않는다):
  - plan 위치 · title · status
  - 남은 작업 (`# Next` / `# Blockers`)
  - sync 진단 결과 + 보정한 항목
  - **제안하는 다음 액션** — 사용자가 진행 의사를 밝히면 그때 실행(규모 크면 dlc 경유).

## 경계 (안 하는 것)
- 다음 액션 **자동 실행 안 함** — 보정·제시까지만. 사용자가 명시하면 그때 진행.
- plan 이 없으면 **새로 만들지 않음** — "이어갈 plan 없음"만 보고.
- 매칭 실패 시 추측 자동 선택 안 함 — 항상 목록 제시.
- subagent 위임 아님 — plan single writer 는 메인. 메인이 직접 read/보정한다.
- plan 보정은 **사실 기반만** — git/파일로 확인된 것만 기록. 추측으로 Progress/Decisions 채우지 않는다(CLAUDE.md §1).
