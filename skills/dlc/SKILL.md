---
name: dlc
description: 비자명한 코드 변경(버그 수정·기능 추가·리팩토링)을 시작할 때 적용하는 개발 사이클 오케스트레이션. 규모를 판정해 trivial(오타·로그 1줄)은 즉시 통과, structural(다계층·public API·DB·신규 service)은 explore→plan→리뷰→TDD→구현→리뷰→simplify→검증 전체 파이프라인을 돈다. `/dlc` 명시 호출 또는 비자명한 코드 변경 시 자동 적용. 단순 질문·탐색·읽기 전용 작업에는 쓰지 않는다.
---

# dlc — 자동 개발 사이클

메인이 hub, 리뷰/검토만 격리 subagent. `.claude/plans/<slug>-plan.md` 가 유일한 공유 채널(메인만 쓴다). CLAUDE.md §3 작업 흐름의 구체화 버전 — 충돌 시 CLAUDE.md 우선.

## 적용
- `/dlc` 명시 호출 또는 비자명한 코드 변경 시. trivial 은 규모 gate 에서 즉시 통과하므로 자동 적용돼도 오버헤드 없음.
- 단순 질문·탐색·읽기 전용·한 턴짜리 명령은 제외.

## 0. 규모 gate (예비 판정)

| 규모 | 트리거 | 도는 단계 |
|---|---|---|
| **trivial** | 오타·주석·포맷·import·로그 1줄 | 구현 → 검증 → Report (리뷰/plan/TDD 생략 — CLAUDE.md §7 예외) |
| **small** | 단일 함수/파일, <50줄, 단일 모듈 | Explore → (버그면 재현 TDD Red) → 구현 → Green → code-reviewer → 검증 → Report |
| **medium** | 다중 함수/1 모듈, 50~150줄 | small + draft plan → plan-reviewer → code-simplifier(+재검증) |
| **structural** | 다계층·public API·DB·migration·신규 service·150줄+ | 전체 파이프라인(아래) |

- 규모는 **예비값**. Explore 후 / 구현 diff 후 **재판정**. small 로 시작했다 public API·DB·2계층·150줄+ 가 되면 상위로 승급하고 skip 했던 plan-review/arch 를 되살린다.

## structural 전체 파이프라인 (상태 전이)

```
0  Setup            git status · 규모 판정 · plan 파일
1  Explore
2  researcher       [조건부 · 격리]
3  draft plan       테스트전략 · rollback · 영향범위 · 구조의도
4  arch planning    [격리 · structural 만 · codex off]
5  plan 수정
6  plan-reviewer    [격리 · codex owner]
7  지적 반영         구조 바뀌면 4~6 재실행
8  TDD Red          새 테스트가 의도한 이유로 실패하는지 확인
9  구현
10 Green            test/build/typecheck 최소
11 arch(정밀) + code-reviewer   [격리 · 병렬 · codex owner 1개]
12 fix loop         관련 reviewer 만 · ≤2회 · disposition
13 code-simplifier  [격리 mutating · blocker 없을 때만]
14 재리뷰           simplifier substantive edit 시 targeted
15 최종 검증         lint / typecheck / test / build
16 Report + plan 업데이트
```

## 격리 경계 (hub-and-spoke)
- **메인(hub)**: Setup, Explore(얇게 — 광범위 검색만 Explore agent 위임), draft plan, TDD Red, 구현, Green, 통합, 최종 검증, Report, 최종 판단.
- **격리 subagent (spoke, read-only)**: researcher, architecture-reviewer(planning/정밀), plan-reviewer, code-reviewer.
- **code-simplifier**: 격리 mutating 단계(`Edit` 권한 보유). 순수 리뷰 아님 — 메인이 diff 흡수 + targeted test + targeted 재리뷰 필수.
- subagent 끼리 context 공유 안 함. 입력은 메인이 번들로 전달, 결과는 각 agent 의 "plan 반영용 요약" 으로 수신.

## codex phase owner
- 규약: `docs/codex-review.md`. 한 phase 에 reviewer 가 여럿이면 codex owner 1개만 지정하고 나머지는 `CLAUDE_REVIEW_CODEX_MODE=external`.
- 계획 단계: `plan-reviewer` (arch planning 은 codex off). 구현 후: 버그/보안 위주면 `code-reviewer`, 구조 위주면 `architecture-reviewer`.

## fix loop / disposition
- 최대 2회. 각 finding 을 plan 파일 `# Review Disposition` 섹션에 `fix / defer / false-positive / wontfix` 로 기록(메인만 씀).
- 2회 후 같은 class 잔존 시 plan `status: blocked` 또는 명시적 risk accept.

## 필수 산출물 / 핵심 규칙
- plan 파일(CLAUDE.md §10): 매 턴 `Progress`/`Next` 갱신. **subagent 는 plan 쓰지 않음** — 메인이 single writer, 쓰기 직전 re-read 후 외부 변경 merge.
- 검증 명령 미식별 시: README / package / pyproject / Makefile / CI 확인해도 없으면 "미식별" 기록 + 추측 실행 금지. 이 상태에서 "검증 완료" 금지.
- researcher 재진입: 어느 단계든 외부 사실(버전/API/CVE) 의문 시 호출.
- TDD Red: 새 테스트가 의도한 이유로 실패하는지 확인(기존 baseline failure 와 분리).
