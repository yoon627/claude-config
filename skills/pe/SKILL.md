---
name: pe
description: 진행 중이던 §10 plan 을 실제 git/코드 상태로 동기화 기록하고 작업을 마무리하는 plan-end 오케스트레이션. uncommitted 변경은 작업 브랜치에 임시(WIP) 커밋으로 보존하고(main/master 직접 커밋·push 는 안 함), Progress/Next/Decisions/status/updated 를 갱신해 다음 세션(/pc)이 곧장 이어받게 한다. `/pe` 명시 호출 또는 "진행상황 기록하고 마무리 / 오늘 여기까지 / 일단 저장하고 끝"류 요청 시 사용. plan 이 없으면 새로 만들지 않는다(그건 dlc 몫). 단순 질문·탐색·읽기 전용에는 쓰지 않는다.
---

# pe — plan 마무리 (plan end)

진행 중이던 §10 plan 을 **실제 git/코드 상태로 동기화 기록**하고, uncommitted 변경을 **임시 커밋으로 보존**한 뒤 작업을 마무리한다. 다음 세션이 `/pc` 로 곧장 이어받게 만드는 게 목표. CLAUDE.md §10 "턴 종료 / 완료" + §8 git 규칙의 자동화 버전 — **충돌 시 CLAUDE.md 우선**. pc(이어가기)의 대칭.

## 적용
- `/pe` 명시 호출, 또는 "진행상황 기록하고 마무리 / 오늘 여기까지 / 일단 저장하고 끝" 류 요청 시.
- 단순 질문·탐색·읽기 전용·한 턴짜리 명령은 제외. **plan 이 없으면 새로 만들지 않는다** (dlc/작업 시작의 몫).

## 동작 (4단계: 찾기 → 상태 수집·임시 커밋 → plan 동기화 → 마무리 보고)

### 1. plan 찾기 (pc 1단계와 동일)
- `ROOT = git rev-parse --show-toplevel`, `BR = git rev-parse --abbrev-ref HEAD`.
- 탐색 위치(존재하는 것만, 중복 제거): `<ROOT>/plans/`, 그리고 cwd 가 worktree 면 main worktree 의 `plans/` (`git worktree list --porcelain` 첫 `worktree <path>`). plans/ 는 gitignored & worktree별 독립이라 양쪽을 봐야 누락이 없다.
- **매칭**(§10): `BR` 이 plan **dir 이름**(`<YYYY-MM-DD>-<slug>`)에 포함되는 dir → 그 안 `*-plan.md` 1개. 1개 채택 / 2개+ 후보 제시 후 선택 / 0개 fallback.
- **active plan 우선**(§10): 세션에서 진행 중이던 plan 이 이미 있으면 branch 매칭과 무관하게 그것을 대상으로 한다 (branch≠slug 여도 빠뜨리지 않음).
- **fallback (매칭 0개)**: `status: in_progress|blocked` plan 을 `updated` 내림차순 목록 제시 → 사용자 선택. 추측으로 자동 선택하지 않는다. 전부 done/없음이면 "마무리할 plan 없음" — 그래도 2단계(임시 커밋)는 수행하고 보고만 한다.

### 2. 작업 상태 수집 + 임시 커밋
- 수집: `git status --short`, `git log --oneline`(plan 시작 이후 새 커밋), origin 대비 — `git log --oneline origin/<base>..HEAD`(unpushed), `git branch --merged origin/<base>`(머지 여부). 점검 명령이 실패(origin 없음 등)하면 그 점검만 skip + 보고에 명시.
- **임시 커밋**(아래 "임시 커밋 규칙"): uncommitted 있으면 작업 브랜치에 WIP 커밋으로 보존. 없으면 skip + "변경 없음" 명시.

### 3. plan 동기화 기록 (메인이 single writer; §10)
plan 을 re-read(외부 변경 merge) 후 **사실 기반으로만**(§1) 갱신:
- `# Progress`: 오늘 진행 한 줄 + 임시 커밋 sha7.
- `# Next`: 다음 세션 즉시 액션으로 교체(실효된 것 정리). WIP 커밋 있으면 "WIP `<sha7>` 이어서/squash" 명시 → pc 가 인지.
- `# Decisions`: 세션 중 결정·스코프 변경 보강(기존은 지우지 말고 §10 방식 "~로 변경 (이유: …)" 덮어쓰기/추가).
- `# Key Files`: 추가/이동 동기화.
- `# Blockers`: 막힌 것 + 풀 조건.
- frontmatter: `status` 판정(4단계) · `updated:` 오늘.

### 4. status 판정 + 마무리 보고
- **status 판정**:
  - 머지·배포 등 **확정 완료 신호** 있을 때만 `done` — 단 done 전환은 **사용자 확인**(마무리=세션 끝이지 작업 끝이 아닐 수 있음).
  - 막힘 → `blocked` + `# Blockers`.
  - 그 외 → `in_progress` 유지(체크포인트).
- **보고**: plan 위치·title·status / 임시 커밋 sha(또는 "변경 없음") / 동기화한 항목 / 남은 작업(`# Next`·`# Blockers`) / "다음 세션은 `/pc` 로 이어받기".

## 임시 커밋 규칙
마무리 시 uncommitted 변경을 잃지 않도록 작업 브랜치에 보존한다. **자동 수행하되 아래 안전장치 필수.**

- **브랜치 보호(§8)**: 현재 브랜치가 `main`/`master`(또는 `origin/HEAD` default)면 직접 커밋 금지. 멈추고 AskUserQuestion — ① 작업 브랜치 새로 만들어 거기 커밋 / ② 커밋 생략하고 plan 기록만 / ③ 취소. 자동 브랜치 생성·강제 커밋 안 함.
- **위험 파일 점검(§8)**: `git status` 에 `.env`·`*.key`·`*.pem`·`id_rsa`·인증서·대용량(빌드 산출물 등) 의심 항목 있으면 커밋 보류 + 사용자 확인(secret 유출 방지).
- **커밋**: 안전하면 `git add -A` 후 `git commit`. 메시지 `wip: <작업 한 줄 요약> (pe checkpoint)` + 규약 트레일러(Co-Authored-By). 본문에 "다음 세션 squash/amend 대상" 한 줄.
- **push 안 함** — §8, 사용자 요청 시만.
- uncommitted 없으면 커밋 skip.

## 경계 (안 하는 것)
- **push 안 함**(§8). **main/master 직접 커밋 안 함** — 확인 후 분리.
- plan 없으면 **새로 만들지 않음** — 임시 커밋 + "마무리할 plan 없음" 보고만(plan 가치 있어 보이면 dlc 제안 한 줄).
- done **자동 전환 안 함** — 확정 완료 신호 + 사용자 확인 시만. 기본 in_progress 체크포인트.
- plan 갱신은 **사실 기반만**(§1) — git/파일로 확인된 것만. 추측으로 Progress/Decisions 채우지 않는다.
- subagent 위임 아님 — plan single writer 는 메인. 메인이 직접 커밋/기록한다.
