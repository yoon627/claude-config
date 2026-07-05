---
name: dlc
description: 비자명한 코드 변경(버그 수정·기능 추가·리팩토링)을 시작할 때 적용하는 개발 사이클 오케스트레이션. 규모를 판정해 trivial(오타·로그 1줄)은 즉시 통과, structural(다계층·public API·DB·신규 service)은 explore→plan→리뷰→TDD→구현→리뷰→simplify→검증 전체 파이프라인을 돈다. `/dlc` 명시 호출 또는 비자명한 코드 변경 시 자동 적용. 단순 질문·탐색·읽기 전용 작업에는 쓰지 않는다.
---

# dlc — 자동 개발 사이클

메인이 hub, 리뷰/검토만 격리 subagent. `.claude/plans/<slug>-plan.md` 가 유일한 공유 채널(메인만 쓴다). CLAUDE.md §3 작업 흐름의 구체화 — 충돌 시 CLAUDE.md 우선.

## 적용
- `/dlc` 명시 호출 또는 비자명한 코드 변경 시. trivial 은 규모 gate 에서 즉시 통과하므로 오버헤드 없음.
- 단순 질문·탐색·읽기 전용·한 턴 명령은 제외.

## 진입 매트릭스 (dlc vs wt vs 직접)
요청 유형을 판정해 경로를 정한다. 기준은 **"비trivial 변경인가"** 단일.

| 입력 유형 | 경로 |
|---|---|
| 질문·탐색·읽기 전용·한 턴 명령 | dlc 미적용 — 현재 위치에서 직접 |
| trivial 변경(오타·로그 1줄) | 현재 worktree 에서 dlc trivial(즉시) |
| 비trivial 변경(small 이상) | **wt 경유 worktree 에서 dlc 전체**(아래) |

## dlc → wt (비trivial 필수)
비trivial 인데 **현재 작업 worktree 가 아니면**(main 이거나 밖) dlc 는 **다른 어떤 행동(Explore·구현 포함)보다 먼저, 예외 없이** `wt` 로 worktree 를 만들어 그 안에서 진행. main 직접·우회 금지 — **필수 게이트**.
- **판정**: Setup(0단계)에서 worktree 위치를 *가장 먼저* 확인(코드 읽기·수정 전). `git worktree list --porcelain` 첫 worktree(=main) 와 cwd 비교, main 이면 wt.
- **생성은 확인**: wt slug 확인(`AskUserQuestion`) 유지 — 무확인 생성 금지("자동"은 경로 선택 자동이지 생성 무확인 아님).
- **순환 방지**: wt 가 dlc 를 invoke 한 경우는 이미 worktree 안이라 skip(wt→dlc 정상, dlc→wt 보강은 위치로 구분).
- 이미 worktree 안이면 self-check 만 하고 진행(CLAUDE.md §3-1).

## 0. 규모 gate
| 규모 | 트리거 | 도는 단계 |
|---|---|---|
| **trivial** | 오타·주석·포맷·import·로그 1줄 | 구현 → 검증 → Report (리뷰/plan/TDD 생략 — CLAUDE.md §7 예외) |
| **small** | 단일 함수/파일, <50줄, 단일 모듈 | Explore → (버그면 재현 TDD Red) → 구현 → Green → code-reviewer → simplify 체크 → 검증 → Report |
| **medium** | 다중 함수/1 모듈, 50~150줄 | small + draft plan → plan-reviewer → simplify 체크(+재검증) |
| **structural** | 다계층·public API·DB·migration·신규 service·150줄+ | 전체 파이프라인(아래) |

- 규모는 **예비값** — Explore 후/구현 diff 후 **재판정**. small 로 시작했다 public API·DB·2계층·150줄+ 되면 승급하고 skip 한 plan-review/arch 를 되살린다.
- **최종 검증 위임**: 표 마지막 '검증'(전 규모·structural 15단계·승급 합류)은 **격리 runner** 실행·메인 판단(아래 격리 경계). **trivial 검증·10단계 Green·14단계 targeted 재검증은 메인 직접**. 격리=완료 전 전체 스위트(lint 포함), 메인=구현 중 최소·targeted.

## 요구사항 명확화 (규모 gate 직후, 비-trivial)
규모 판정 후 Explore 전, 요구의 **공백**을 점검한다 — §3 "모호하면 질문"의 판정 절차. 임의 추론으로 메우지 않는다.
- **체크리스트** — ① 완료 기준 ② 대상 파일/기능 범위 ③ 사용자-visible 산출물·문구 형태 ④ 명시적 금지/제외 범위. 빈 칸이 **완료 판정(acceptance)에 영향 줄 가능성이 조금이라도 있으면 질문**(`AskUserQuestion`), 불확실하면 질문(fail-safe). **명백히 결과무관일 때만** 가정 + 1줄 명시 후 진행.
- **silent** — 공백 없으면 침묵 진행(명확한 요구엔 마찰 0).
- **질문 vs 추천 경계** (memory `feedback-analyze-before-asking`) — **무엇(요구·목표·산출물)이 빠졌으면 질문**, **요구는 있고 구현 방법만 갈리면 분석 후 추천**. 둘 다면 acceptance 를 바꾸는 축(what) 먼저.
- **trivial 도 예외 아님** — 절차 생략이지 요구 불명확 허용 아님. 산출물·문구 모호하면 먼저 질문.
- 명확화 ≤2 라운드(fix loop 동형). Explore 후 규모 재판정으로 범위 커지면 게이트 재평가.

## Acceptance — 항목화 + evidence gate (비-trivial)
요구를 **test 가능한 acceptance 항목**으로 분해, 각 항목이 **증거(실행·관찰·통과)로 충족될 때만** "완료". 증거 없는 "완료" 금지.
- **항목화**(draft plan 시): plan `# Acceptance` 에 `무엇이 충족되나` + `어떻게 검증(명령/관찰)` + `통과 기준`. 관찰 가능하게(추상적 "잘 동작" 금지).
- **증거 게이트**(Report 전): 전 항목 증거 대조. 미충족·미검증이면 완료 금지 → 수정 또는 `status: blocked`/"미검증"(CLAUDE.md §1).
- **verification grounding**: 실행되는 산출물(HTML·SVG·게임·차트·CLI·서버)은 정적 점검이 아니라 **실제 실행·출력 관찰** 증거를 넣는다("well-formed ≠ correct").
- trivial 은 항목화 면제(검증 자체가 acceptance) — 단 검증은 한다.
- **문서 동기화도 acceptance**(CLAUDE.md §3): README 문서화 컴포넌트·`wiki/pages/` 를 건드리면 README/`wiki/index.md` 동기화를 acceptance 항목으로 같은 브랜치 갱신(잊으면 완료 아님).
- **이중 보조**: Stop hook(`dlc-early-stop`)이 capped 경고(fail-open) — ① 비trivial 변경에 검증 기록 없음 ② 문서화 표면 바꿨는데 README/index 동기화 없음(`dlc-doc-drift`). hook 은 보조 — 이 규약이 단일 소스.

## 조사 프로토콜 (디버깅·장애)
버그·장애는 추측 수정 전에 절차를 따른다(CLAUDE.md §1 근본 원인·3 Whys 구체화):
1. **재현**: 실패를 먼저 재현. 재현 없이 "고쳤다" 금지.
2. **가설 경쟁(3+)**: 원인 가설 최소 3개 경쟁, 첫 가설에 안주 금지.
3. **인과 사슬**: 증상 → 직접 원인 → 근본 원인까지 증거로 확정. 증상만 누르는 수정(에러 무시·무의미 retry) 금지.
- 가능하면 재현 테스트 먼저(TDD Red) — 수정 후 그 테스트가 green 이 되는 것이 acceptance 증거.

## structural 전체 파이프라인 (상태 전이)
```
0  Setup            git status · 규모 판정 · plan 파일
1  Explore
2  researcher       [조건부 · 격리]
3  draft plan       테스트전략 · rollback · 영향범위 · 구조의도 · # Acceptance 항목화
4  arch planning    [격리 · structural 만 · codex off]
5  plan 수정
6  plan-reviewer    [격리 · codex owner]
7  지적 반영         구조 바뀌면 4~6 재실행
8  TDD Red          새 테스트가 의도한 이유로 실패하는지 확인
9  구현
10 Green            test/build/typecheck 최소
11 arch(정밀) + code-reviewer   [격리 · 병렬 · codex owner 1개]
12 fix loop         관련 reviewer 만 · ≤2회 · disposition
13 simplify 체크    [메인 직접 · blocker 없을 때만]
14 재리뷰           simplify 체크의 substantive edit 시 targeted
15 최종 검증         lint / typecheck / test / build   [격리 runner · 실행만]
16 Report + plan 업데이트   ← evidence gate: # Acceptance 전 항목 증거 대조 통과 후에만 완료
```

## wiki 연계 (CLAUDE.md §11)
조건부·opt-in 2지점, 16단계 표는 안 늘린다, wiki 없으면 no-op.
- **1 Explore**: `wiki/index.md` 있으면 관련 `decision`/`entity` 페이지 read(과거 결정·검증된 외부 사실 재사용 → researcher 재검색 절감). 없으면 skip.
- **16 Report**: 재사용 지식(비자명 결정·교훈·확정한 외부 사실) 나오면 `/wiki ingest` 제안(자동 아님). trivial·일회성·이 작업 국한은 제외.
- **16 Report — feedback memory 판정(§12)**: 작업 중 **사용자 교정·리뷰 지적**이 있었으면 §12 feedback 저장 판정 — 대상이면 memory 파일 + `MEMORY.md` 인덱스(둘 다), 비대상이면 사유 1줄. **판정 누락 금지**(wiki ingest 판정과 대칭).
- plan→wiki **일방향 승격**(plans=일시적 핸드오프, wiki=영속 누적). 양방향 동기화 금지.

## 격리 경계 (hub-and-spoke)
- **메인(hub)**: Setup, Explore(얇게 — 광범위 검색만 Explore agent 위임), draft plan, TDD Red, 구현, Green(구현 직후 최소 스모크), 통합, 검증 명령 식별·결과 판단·실패 fix, Report, 최종 판단.
- **격리 subagent (spoke, read-only)**: researcher, architecture-reviewer(planning/정밀), plan-reviewer, code-reviewer.
- **최종 검증 runner (격리·Edit 없음·검증 산출물은 생성)**: 빌트인 general-purpose — 소스 불변, build/test 산출물·캐시는 만듦. 메인이 식별한 검증 명령을 **문자열 그대로 + worktree 절대 cwd** 로 받아 지정 명령만 실행, 해석·수정·재탐색·수리 안 함(명령 식별 책임은 메인 — 아래 '검증 명령 미식별'). 반환: exit code + 통과/실패 + 실패 항목·로그 핵심(구조화). 실패 요약이 fix 에 불충분하면 메인 재실행. cwd 누락 시 silent false-pass 위험.
- **검증 실패는 12단계 fix loop 와 별개** — 객관적이라 disposition(false-positive/wontfix) 대상 아님, 통과까지 메인이 수정·재검증.
- **메인 직접 검증(격리 아님)**: 10단계 Green·14단계 targeted 재검증·trivial 검증 — 짧고 즉시 루프라 격리 오버헤드가 손해.
- **simplify 체크(13단계)**: 격리 아니라 **메인 직접**(모든 spoke read-only). diff 범위 점검: 중복(3회+ 반복만 추상화 검토) · 과한 추상화 · 불필요 옵션/죽은 분기 · 죽은 코드(rg 사용처 확인 후 삭제) · 과한 방어 코드 · 표준 라이브러리/기존 유틸 대체 · 깊은 nesting. 동작 보존 · 범위 내 · 불확실하면 보류(제안만 Report). substantive 수정 시 targeted test + 14 targeted 재리뷰 필수.
- subagent 끼리 context 미공유. 입력은 메인이 번들 전달, 결과는 각 agent 의 "plan 반영용 요약"으로 수신.

## codex phase owner
- 규약 `docs/codex-review.md`. 한 phase 에 reviewer 여럿이면 codex owner 1개만 지정, 나머지 `CLAUDE_REVIEW_CODEX_MODE=external`.
- 계획 단계: `plan-reviewer`(arch planning 은 codex off). 구현 후: 버그/보안 위주면 `code-reviewer`, 구조 위주면 `architecture-reviewer`.

## fix loop / disposition
- 최대 2회. 각 finding 을 plan `# Review Disposition` 에 `fix / defer / false-positive / wontfix` 기록(메인만 씀).
- 2회 후 같은 class 잔존 시 `status: blocked` 또는 명시적 risk accept.

## 자기 진단
새 단계가 아니라 **plan write 시점**(single writer re-read 강제)에 기생하는 메타 점검 — "지금 행동이 `# Next`·규모표와 맞나". silent self-check 에 기대지 않는다(이탈 중엔 자기점검도 안 돈다). **trivial 면제**.
- **점검**(plan write + 구현 전·리뷰 전·실패 재시도 전·Report 전): ① 현재 행동이 `# Next` 와 어긋나나 ② 규모표상 건너뛴 필수 단계 있나 ③ 아래 중대 신호 해당하나.
- **중대(닫힌 목록)**: 방향/요구/설계 변경 · plan/리뷰/검증 건너뜀 · 스코프 밖 파일 수정 · single writer·격리 경계 위반 · 동일 실패에 동일 전략 2회 재현 · "검증 완료" 허위 위험. **모호하면 중대**(fail-safe).
- **대응**: 사소(순서·산출물·검증결과 불변, 회복 가능한 누락 — 예: Progress 갱신 빠뜨림) → 바로 보강 + 한 줄 보고. 중대 → **멈춤 + `AskUserQuestion` + 결정 대기**(승인 전 수정 금지 — CLAUDE.md §1).
- **기존과 연결**: 방향 오류는 CLAUDE.md §2, 반복 실패는 fix loop(≤2회→blocked), 단계 누락은 규모표·승급 — 새 로직 만들지 말고 참조.
- **상한**: 발동→대응 후 재진단 ≤1회. 잔존 시 `status: blocked` + 알림.

## Workflow Findings (증거기반 자기개선)
작업 중 **확인된 workflow 실패**(dlc/규약 자체 문제로 작업이 샌 경우)만 기록 — 매 작업 회고 아님(빈 의례 방지). 자동 수정 안 함.
- **기록 트리거**(확인된 것만): ① 중대 self-diagnosis 발동(스코프 이탈·단계 누락·격리 위반 등) ② 동일 유형 실패 2회 재현 ③ **사용자가 명시 지적한 workflow 마찰·오탐**(예: hook false positive). ③ 은 §12 feedback(작업방식 즉시 교정)과 달리 *운영 자산(dlc/hook/규약)*을 고칠 반복 마찰.
- **기록(2곳)**: ① plan `# Workflow Findings` 한 줄 ② **wiki `decision/workflow-failures.md` 누적**(영속·반복 추적). 형식 `깨진 규칙/단계 · 재발 조건 · 수정 후보 위치 · 발생 횟수`. 같은 실패면 기존 항목 횟수만 올린다.
- **반복 시 제안**: wiki 같은 finding 이 **2회+ 누적**되면 `AskUserQuestion` 으로 "N회 반복됐다 — `wt` 로 고칠까?" 제안. 승인 시 **wt → dlc**(운영 자산 변경은 비trivial 이라 wt 필수), 거부 시 보존만.
- **자동 신호와 관계**: hook(`scripts/dlc-signal.js`)이 early-stop·doc-drift·guard 차단·plan-blocked 신호를 `~/.claude/telemetry/dlc-signals.jsonl` 자동 누적, `/improve` 가 집계·랭킹 제안. 이 수동 기록은 신호가 못 담는 **맥락**(원인·재발 조건·수정 후보 위치) — 상보(대체 아님).
- **자가수정 경계(§1)**: 승인 없이 운영 자산(dlc/CLAUDE.md 등)을 스스로 고치지 않는다. harness 는 발견·기록·제안까지, 수정은 사용자 승인 후. 완전 무인 자동화는 두지 않는다(`wiki/pages/decision/self-diagnosis-and-improvement-status.md`).

## 필수 산출물 / 핵심 규칙
- plan(CLAUDE.md §10): 매 턴 `Progress`/`Next` 갱신. **subagent 는 plan 안 씀** — 메인이 single writer, 쓰기 직전 re-read 후 외부 변경 merge.
- 검증 명령 미식별: README/package/pyproject/Makefile/CI 확인해도 없으면 "미식별" 기록 + 추측 실행 금지. 이 상태에서 "검증 완료" 금지. 식별한 명령은 runner 에 **문자열·worktree cwd 그대로** 전달(runner 는 재탐색·수리 안 함).
- researcher 재진입: 어느 단계든 외부 사실(버전/API/CVE) 의문 시 호출.
- TDD Red: 새 테스트가 의도한 이유로 실패하는지 확인(기존 baseline failure 와 분리).
- feedback memory 참고(§12): Explore 시 `MEMORY.md` 인덱스의 관련 feedback(행동지시문)을 확인해 적용.
