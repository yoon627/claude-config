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
- **최종 검증 위임**: 표의 마지막 **'검증'**(전 규모, structural 15단계, 승급 합류 포함)은 **격리 runner** 가 실행하고 메인이 판단한다(아래 격리 경계). **trivial 검증·10단계 Green·14단계 targeted 재검증은 메인 직접**. 경계는 *범위* — 격리 = 완료 전 전체 스위트(lint 포함), 메인 = 구현 중 최소·targeted.

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
15 최종 검증         lint / typecheck / test / build   [격리 runner · 실행만]
16 Report + plan 업데이트
```

## wiki 연계 (영속 프로젝트 메모리 — CLAUDE.md §11)
조건부·opt-in 2지점. 16단계 표는 안 늘린다. wiki 없으면 전부 no-op.
- **1 Explore**: `wiki/index.md` 있으면 훑어 관련 `decision`/`entity` 페이지 read(과거 결정·검증된 외부 사실 재사용 → researcher 재검색 절감). 없으면 skip(무비용).
- **16 Report**: 재사용 가능한 지식(비자명한 결정·교훈·확정한 외부 사실)이 나왔으면 `/wiki ingest` 제안(자동 아님). trivial·일회성·이 작업 국한은 제외.
- plan→wiki **일방향 승격**: plans=일시적 작업 핸드오프(종료 시 닫힘), wiki=영속 누적. 양방향 동기화 금지.

## 격리 경계 (hub-and-spoke)
- **메인(hub)**: Setup, Explore(얇게 — 광범위 검색만 Explore agent 위임), draft plan, TDD Red, 구현, Green(구현 직후 최소 스모크), 통합, 검증 명령 식별·결과 판단·실패 fix, Report, 최종 판단.
- **격리 subagent (spoke, read-only)**: researcher, architecture-reviewer(planning/정밀), plan-reviewer, code-reviewer.
- **최종 검증 runner (격리 · Edit 없음 · Bash 검증 산출물은 생성)**: 빌트인 general-purpose — read-only spoke 도 simplifier(Edit) 도 아닌 제3 범주(소스 불변, build/test 산출물·캐시는 만듦). 메인이 식별한 검증 명령을 **문자열 그대로 + worktree 절대 cwd** 로 받아 그 cwd 에서 지정 명령만 실행하고, 해석·수정·재탐색·수리하지 않는다(명령 식별 책임은 메인 — 아래 '검증 명령 미식별' 규칙). 반환: exit code + 통과/실패 + 실패 시 실패 항목·로그 핵심(구조화). 실패 요약이 fix 에 불충분하면 불완전 검증으로 간주 → 메인 재실행. 적용: 전체 스위트가 길거나 출력·산출물이 많은 **완료 전 최종 검증**(전 규모). cwd 누락 시 엉뚱한 디렉토리 검증 → silent false-pass 위험.
- **검증 실패 처리는 12단계 fix loop 와 별개** — 검증 실패는 객관적이라 disposition(false-positive/wontfix) 대상 아님, 통과까지 메인이 수정·재검증.
- **메인 직접 검증(격리 아님)**: 10단계 Green(구현 직후 최소)·14단계 targeted 재검증·trivial 검증 — 짧고 즉시 루프라 격리 오버헤드가 손해.
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
- 검증 명령 미식별 시: README / package / pyproject / Makefile / CI 확인해도 없으면 "미식별" 기록 + 추측 실행 금지. 이 상태에서 "검증 완료" 금지. 식별한 명령은 최종 검증 runner 에 **문자열·worktree cwd 그대로** 전달(runner 는 재탐색·수리 안 함).
- researcher 재진입: 어느 단계든 외부 사실(버전/API/CVE) 의문 시 호출.
- TDD Red: 새 테스트가 의도한 이유로 실패하는지 확인(기존 baseline failure 와 분리).
