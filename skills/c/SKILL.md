---
name: c
description: 현재 worktree/repo 의 진행 중인 plan(CLAUDE.md §10)을 찾아 남은 작업과 plan↔실제(git/코드) sync 상태를 진단하고, 어긋나면 plan 을 보정한 뒤 다음 액션이 명확하면 이어서 실행하는 plan 이어가기(plan-continue) 오케스트레이션. `/c` 명시 호출 또는 "진행하던 작업 이어가자"류 요청 시 사용. branch→plan dir 매칭, 실패 시 in_progress 목록 제시. 확인·sync 진단·보정 후 `# Next` 가 명확하면 이어서 실행한다(멈추는 예외 5종: blocked·plan 후보 다수·Next 재구성·파괴적/외부공개 액션·done). 그 브랜치 PR 의 사람 리뷰 코멘트도 intake 한다. 단순 질문·탐색·신규 작업 시작에는 쓰지 않는다(새 plan 생성은 dlc 몫).
---

# c — plan 이어가기 (plan continue)

진행 중이던 §10 plan 을 찾아 **남은 작업 + sync 상태**를 진단하고, 어긋난 plan 을 실제 상태로 보정한 뒤 `# Next` 가 명확하면 이어서 실행한다(예외 시 정지·제시). CLAUDE.md §10 "시작: 매칭 plan read 후 컨텍스트 복원 / 진행 중 동기화"의 자동화 버전 — **충돌 시 CLAUDE.md 우선**.

## 적용
- `/c` 명시 호출, 또는 진행하던 plan 을 이어가려 할 때.
- 단순 질문·탐색·읽기 전용·신규 작업 시작은 제외. **plan 이 없으면 새로 만들지 않는다** (그건 dlc/작업 시작의 몫).

## 동작 (3단계: 찾기 → 진단 → 보정·이어실행)

### 1. plan 찾기
- `ROOT = git rev-parse --show-toplevel`, `BR = git rev-parse --abbrev-ref HEAD`.
- 탐색 위치 (존재하는 것만, 중복 제거):
  1. `<ROOT>/plans/`
  2. cwd 가 worktree 일 때 main worktree 의 plans — `git worktree list --porcelain` 의 첫 `worktree <path>` 라인 → `<main>/plans/`. (1)과 동일하면 생략.
  > plans/ 는 worktree(브랜치)별 독립이라 양쪽을 봐야 누락이 없다(tracked 지만 브랜치마다 내용이 다르다).
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
- **PR 리뷰 intake** (plan 이 매칭된 경우만, read-only): 그 브랜치 PR 의 **사람** 리뷰 지적(요약·conversation·**인라인 line**)을 수집해 3단계 처분으로 넘긴다.
  - PR 식별: `gh pr list --head <BR> --state all --limit 3 --json number,state,title`.
  - 수집 (3소스 — **인라인이 코드지적의 주 형태라 필수**):
    - 리뷰 요약·state: `gh pr view <n> --json reviews` (`reviews[].body`·`state`·`author`).
    - conversation 코멘트: `gh pr view <n> --json comments`.
    - **인라인(line-level) 코멘트**: `gh api repos/{owner}/{repo}/pulls/<n>/comments --jq '.[] | {user:.user.login, path, line, body}'`. ⚠️ `gh pr view --json reviews,comments` 는 인라인을 **주지 않는다**(cli/cli #11477) — 빠뜨리면 사용자가 남긴 코드 지적을 '없음'으로 오보(silent false-negative).
  - **사람만**: `user.login`(또는 `author.login`)이 현재 사용자(`gh api user --jq .login`)와 같으면 제외(자기), `[bot]` 로 끝나면 제외(봇).
  - **fail-open**: `gh` 미설치·미인증·원격/PR 없음 → 이 점검만 skip 하고 "PR 리뷰: 확인 불가(<사유>)" 1줄. (네트워크 왕복 2-3회, plan 매칭 시에만.)

### 3. 보정 + 다음 액션 (이어서 실행)
- sync 어긋남이 있으면 **plan 파일을 먼저 보정** (메인이 single writer; §10 진행중 동기화):
  - 새 커밋 → `# Progress` 한 줄씩 추가.
  - uncommitted 변경 → 현황 반영.
  - 없어진/이동된 파일 → `# Key Files` 갱신.
  - 실제와 다른 `status` → 정정(머지=done, 막힘=blocked + `# Blockers`). (머지=done 은 **객관적 사실 기록** — done 이 되면 아래 예외5 로 정지하므로 e 의 '세션종료 done 확인'과 구분되어 안전.)
  - 실효된 `# Next` → 실제 다음 액션으로 교체.
  - frontmatter `updated:` 오늘로.
  - 기존 `# Decisions` 는 지우지 말고 §10 방식(덮어쓰기/추가 + 이유).
- **PR 리뷰 처분** (intake 수집분이 있으면):
  - (a) **코드 지적**(버그·수정 요청) → `# Next` 후보로 "PR#n 리뷰 반영: <요지>" 채택(미해결은 코멘트 상태·후속 커밋으로 추정, 불확실하면 그대로 노출).
  - (b) **작업방식 교정**(스타일·절차) → §12 feedback memory 저장 **판정**을 보고에 포함(대상이면 저장 제안, 저장 자체는 사용자 확인 후 — 판정 의무는 dlc Report 와 동일, 단 intake 는 사용자 미지시라 저장 전 확인).
- **요약 보고**: plan 위치·title·status / 남은 작업(`# Next`·`# Blockers`) / sync 진단·보정 항목 / PR 리뷰 intake 결과 / 다음 액션.
- **그 다음 이어서 실행** — `# Next` 가 명확하면 "진행해도 되나?" 재확인 없이 곧장 진행한다. 비trivial 구현이면 dlc 파이프라인으로 넘기며, **dlc 가 main 밖이면 wt-first + slug 확인 게이트를 적용하므로 worktree/slug 확인은 그대로 유지**된다(우회 아님). **단 아래 예외면 멈추고 사용자 결정을 기다린다 (닫힌 목록 5종)**:
  1. `status: blocked` — 해소가 사용자 몫.
  2. plan 매칭 실패로 **fallback 선택**이 필요한 경우(1단계) — 후보가 1개여도 사용자 선택을 받는다.
  3. `# Next` 가 비었거나 실효돼 **재구성**한 경우 — 방향 확인 1회.
  4. 다음 액션이 **파괴적·비가역·외부공개**(push·머지·삭제·배포·DB migration/write 등 — §8 게이트 및 그에 준하는 것; 분류 애매하면 멈춤) — 명시 확인.
  5. `done` plan — 이어갈지 확인.

## 경계 (안 하는 것)
- **파괴적·외부공개 액션은 이어서 실행하지 않음** (push·머지·삭제·배포 — §8 게이트) — 그 외 명확한 `# Next` 는 이어서 진행(3단계 예외 5종).
- **PR 리뷰 intake 는 read-only** — 코멘트를 수집·분류만 하고 **자동 회신·comment·resolve 는 하지 않는다**.
- plan 이 없으면 **새로 만들지 않음** — "이어갈 plan 없음"만 보고.
- 매칭 실패 시 추측 자동 선택 안 함 — 항상 목록 제시.
- subagent 위임 아님 — plan single writer 는 메인. 메인이 직접 read/보정한다.
- plan 보정은 **사실 기반만** — git/파일로 확인된 것만 기록. 추측으로 Progress/Decisions 채우지 않는다(CLAUDE.md §1).
