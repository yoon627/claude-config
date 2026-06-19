---
name: dlc
description: 비자명한 코드 변경(버그 수정·기능 추가·리팩토링)을 시작할 때 적용하는 개발 사이클 오케스트레이션. 규모를 판정해 trivial(오타·로그 1줄)은 즉시 통과, structural(다계층·public API·DB·신규 service)은 explore→plan→리뷰→TDD→구현→리뷰→simplify→검증 전체 파이프라인을 돈다. `/dlc` 명시 호출 또는 비자명한 코드 변경 시 자동 적용. 단순 질문·탐색·읽기 전용 작업에는 쓰지 않는다.
---

# dlc — 자동 개발 사이클

메인이 hub, 리뷰/검토만 격리 subagent. `.claude/plans/<slug>-plan.md` 가 유일한 공유 채널(메인만 쓴다). CLAUDE.md §3 작업 흐름의 구체화 버전 — 충돌 시 CLAUDE.md 우선.

## 적용
- `/dlc` 명시 호출 또는 비자명한 코드 변경 시. trivial 은 규모 gate 에서 즉시 통과하므로 자동 적용돼도 오버헤드 없음.
- 단순 질문·탐색·읽기 전용·한 턴짜리 명령은 제외.

## 진입 매트릭스 (dlc vs wt vs 직접)

요청을 받으면 먼저 유형을 판정해 경로를 정한다. 기준은 단일하게 **"비trivial 변경인가"** — "모든 작업/문제"가 아니다.

| 입력 유형 | 경로 |
|---|---|
| 질문·탐색·읽기 전용·한 턴 명령 | dlc 미적용 — 현재 위치에서 직접 |
| trivial 변경(오타·로그 1줄) | 현재 worktree 에서 dlc trivial(즉시) — 새 worktree 불필요 |
| 비trivial 변경(small 이상) | **wt 경유 worktree 에서 dlc 전체** (아래 dlc→wt) |

## dlc → wt (비trivial 필수)

비trivial 변경인데 **현재 작업 worktree 가 아니면**(main worktree 이거나 worktree 밖) dlc 는 **다른 어떤 행동(Explore·구현 포함)보다 먼저, 예외 없이** `wt` 로 worktree 를 만들어 그 안에서 진행한다. main 에서 직접 진행하거나 이 단계를 우회하는 것은 금지 — "자동 경유 권장"이 아니라 **필수 게이트**다.

- **최우선 판정**: Setup(0단계)에서 worktree 위치를 *가장 먼저* 확인 — 코드를 읽거나 고치기 전에. 비trivial인데 main worktree면 즉시 wt 로 빠진다.
- **판정 방법**: `git worktree list --porcelain` 첫 worktree(=main) 와 현재 cwd 비교. 현재가 main worktree 면 → wt 경로.
- **자동 진입이되 생성은 확인**: wt 의 slug 확인(`AskUserQuestion`)은 유지 — 무확인 worktree 생성 금지. "자동"은 *경로 선택*이 자동이라는 뜻이지 생성을 묻지 않는다는 뜻이 아니다.
- **순환 방지**: wt 가 요청사항으로 dlc 를 invoke 한 경우는 **이미 작업 worktree 안**이므로 이 단계를 건너뛴다. wt→dlc(정상)와 dlc→wt(보강)는 worktree 위치로 구분된다.
- 이미 작업 worktree 안이면 self-check 만 하고 진행(skill 미진입으로 plan·검증 건너뛰기 방지 — CLAUDE.md §3-1).

## 0. 규모 gate (예비 판정)

| 규모 | 트리거 | 도는 단계 |
|---|---|---|
| **trivial** | 오타·주석·포맷·import·로그 1줄 | 구현 → 검증 → Report (리뷰/plan/TDD 생략 — CLAUDE.md §7 예외) |
| **small** | 단일 함수/파일, <50줄, 단일 모듈 | Explore → (버그면 재현 TDD Red) → 구현 → Green → code-reviewer → 검증 → Report |
| **medium** | 다중 함수/1 모듈, 50~150줄 | small + draft plan → plan-reviewer → code-simplifier(+재검증) |
| **structural** | 다계층·public API·DB·migration·신규 service·150줄+ | 전체 파이프라인(아래) |

- 규모는 **예비값**. Explore 후 / 구현 diff 후 **재판정**. small 로 시작했다 public API·DB·2계층·150줄+ 가 되면 상위로 승급하고 skip 했던 plan-review/arch 를 되살린다.
- **최종 검증 위임**: 표의 마지막 **'검증'**(전 규모, structural 15단계, 승급 합류 포함)은 **격리 runner** 가 실행하고 메인이 판단한다(아래 격리 경계). **trivial 검증·10단계 Green·14단계 targeted 재검증은 메인 직접**. 경계는 *범위* — 격리 = 완료 전 전체 스위트(lint 포함), 메인 = 구현 중 최소·targeted.

## 요구사항 명확화 (규모 gate 직후, 비-trivial)

규모 판정 후 Explore 전, 사용자가 넘긴 요구의 **공백**을 점검한다 — §3 "모호하면 질문"의 *판정 절차*(무엇을 질문하고 무엇을 가정할지 정함). 임의 추론으로 공백을 메우지 않는다.

- **체크리스트** — ① 완료 기준 ② 대상 파일/기능 범위 ③ 사용자-visible 산출물·문구 형태 ④ 명시적 금지/제외 범위. 빈 칸이 **완료 판정(acceptance)에 영향 줄 가능성이 조금이라도 있으면 질문**(`AskUserQuestion`) — 영향 여부가 불확실하면 질문 쪽(fail-safe). **명백히 결과무관일 때만** 합리적 가정 + 그 가정 1줄 명시 후 진행.
- **silent** — 공백이 없으면 침묵하고 진행(명확한 요구엔 마찰 0). 질문이 필요할 때만 노출.
- **질문 vs 추천 경계** (memory `feedback-analyze-before-asking` 와 짝) — **무엇(요구·목표·산출물)이 빠졌으면 질문**, **요구는 있고 구현 방법만 갈리면 분석 후 추천**. 한 요청에 둘 다면 acceptance 를 바꾸는 축을 what 으로 보고 질문 먼저, how 는 그 뒤 추천.
- **trivial 도 예외 아님** — trivial 은 절차(plan/리뷰/TDD) 생략이지 요구 불명확 허용이 아니다. 산출물·문구가 모호하면("이 로그 고쳐 — 뭘로?") trivial 이라도 먼저 질문.
- 명확화 ≤2 라운드(fix loop 동형). Explore 후 규모 재판정으로 산출물 범위가 커지면 게이트 재평가.

## Acceptance — 검증 항목화 + evidence gate (비-trivial)

요구사항을 **test 가능한 acceptance 항목**으로 분해하고, 각 항목이 **증거(실행·관찰·통과)로 충족될 때만** "완료"를 선언한다. 증거 없는 "완료"는 금지.

- **항목화**(draft plan 시): 요구를 검증 가능한 단위로 쪼개 plan `# Acceptance` 섹션에 적는다. 각 항목 = `무엇이 충족돼야 하나` + `어떻게 검증하나(명령/관찰)` + `통과 기준`. 추상적("잘 동작")이 아니라 관찰 가능하게.
- **증거 게이트**(Report 전): 모든 acceptance 항목을 증거로 대조. 미충족·미검증 항목이 있으면 완료 금지 → 수정하거나 `status: blocked`/"미검증" 명시(CLAUDE.md §1).
- **verification grounding**(render/실행 artifact): HTML·SVG·게임·차트·CLI·서버 등 *실행되는 산출물*은 정적 점검(파싱 OK)으로 끝내지 않고 **실제 실행해 출력을 관찰**한 증거를 acceptance 에 넣는다. "well-formed ≠ correct".
- trivial 은 항목화 면제(단일 변경이라 검증 자체가 acceptance) — 단 trivial 도 검증은 한다.
- **문서 동기화도 acceptance**(CLAUDE.md §3): 변경이 README 문서화 컴포넌트(스크립트·설정·skill·agent·CLAUDE.md 섹션)에 닿거나 `wiki/pages/` 를 건드리면, README/`wiki/index.md` 동기화를 **acceptance 항목으로** 넣고 같은 브랜치에서 갱신한다(검증과 동급, 잊으면 완료 아님).
- **이중 보조**: Stop hook(`dlc-early-stop`)이 capped 로 경고한다(fail-open) — ① "비trivial 변경 있는데 검증 기록 없음", ② "문서화 표면 바꿨는데 README/index 동기화 없음"(`dlc-doc-drift` 판정). hook 은 보조일 뿐 — 이 규약이 단일 소스다.

## 조사 프로토콜 (investigation — 디버깅·장애)

버그·장애는 추측 수정 전에 절차를 따른다(CLAUDE.md §1 근본 원인·3 Whys 의 구체화):

1. **재현**(reproduce): 실패를 먼저 재현. 재현 안 되면 그것부터 — 재현 없이 "고쳤다" 금지.
2. **가설 경쟁**(3+): 원인 가설 최소 3개를 세워 경쟁시킨다. 첫 가설에 안주하지 않는다.
3. **인과 사슬**(causal chain): 증상 → 직접 원인 → 근본 원인까지 추적해 증거로 확정. 증상만 누르는 수정(에러 무시·무의미 retry) 금지.
- 가능하면 재현 테스트 먼저(TDD Red) — 수정 후 그 테스트가 green 이 되는 것이 acceptance 증거가 된다.

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
13 code-simplifier  [격리 mutating · blocker 없을 때만]
14 재리뷰           simplifier substantive edit 시 targeted
15 최종 검증         lint / typecheck / test / build   [격리 runner · 실행만]
16 Report + plan 업데이트   ← evidence gate: # Acceptance 전 항목 증거 대조 통과 후에만 완료
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

## 자기 진단 (self-diagnosis)

새 단계가 아니라 **plan write 시점**(이미 single writer re-read 가 강제됨)에 기생하는 메타 점검 — "지금 행동이 `# Next`·규모표와 맞나". silent self-check 지침에 기대지 않는다(이탈 중엔 그 주의가 흐트러져 자기점검도 안 돈다). **trivial 면제**.

- **점검**(plan write + 구현 전·리뷰 전·실패 재시도 전·Report 전): ① 현재 행동이 `# Next` 와 어긋나나 ② 규모표상 건너뛴 필수 이전 단계 있나 ③ 아래 중대 신호에 해당하나.
- **중대 (닫힌 목록 — 하나라도 해당)**: 방향/요구/설계 변경 · 규모표상 필요한데 plan/리뷰/검증 건너뜀 · 스코프 밖 파일 수정 · single writer·격리 경계 위반 · 동일 실패에 동일 전략 2회인데 재현 · "검증 완료" 허위 위험. **모호하면 중대**(fail-safe).
- **대응**: 사소(순서·산출물·검증결과 불변, 회복 가능한 누락 — 예: Progress 갱신 빠뜨림) → 바로 보강 + 한 줄 보고. 중대 → **멈춤 + `AskUserQuestion` 알림 + 결정 대기**(승인 전 수정 금지 — CLAUDE.md §1 사용자 변경 보호).
- **기존과 연결 (재구현 금지)**: 방향 오류는 CLAUDE.md §2, 반복 실패는 fix loop(≤2회→blocked)·검증 실패 처리의 공통 escape hatch, 단계 누락은 규모표·승급(small→structural 되살리기)에 바인딩 — 새 로직 만들지 말고 참조.
- **상한**: 발동→대응 후 재진단 ≤1회. 잔존 시 `status: blocked` + 사용자 알림.

## Workflow Findings (증거기반 자기개선 — 기록 + 반복 시 해결 제안)

작업 중 **확인된 workflow 실패**(dlc/규약 자체의 문제로 작업이 샌 경우)만 기록한다 — 매 작업 회고가 아니다(빈 의례 방지). 자동 수정은 하지 않는다.

- **기록 트리거**(확인된 것만): ① 중대 self-diagnosis 발동(스코프 이탈·단계 누락·격리 위반 등) ② 동일 유형 실패 2회 재현 ③ **사용자가 명시적으로 지적한 workflow 마찰·오탐**(예: hook false positive). ③ 은 사용자 피드백을 누적해 반복 시 운영 자산을 고치기 위함 — 작업방식 행동 교정(§12 feedback, 즉시 반영)과 달리 *운영 자산(dlc/hook/규약)을 고칠* 반복 마찰을 다룬다.
- **기록 (2곳)**: ① 현재 작업 plan `# Workflow Findings` 에 한 줄 ② **wiki `decision/workflow-failures.md` 에 누적**(영속 — 작업을 가로질러 반복을 추적). 형식: `깨진 규칙/단계 · 재발 조건 · 수정 후보 위치 · 발생 횟수`. 같은 실패면 새 줄 말고 기존 항목의 횟수를 올린다.
- **반복 시 해결 제안**: wiki 의 같은 finding 이 **2회 이상 누적**되면 → `AskUserQuestion` 으로 "이 실패가 N회 반복됐다 — `wt` 로 worktree 만들어 고칠까?" **제안**한다. 승인 시 그 수정을 **wt → dlc** 로 착수(운영 자산 변경이면 그 자체가 비trivial 이라 wt 필수). 거부하면 wiki 에 보존만 하고 진행.
- **자가수정 경계(§1)**: 제안·승인 없이 운영 자산(dlc/CLAUDE.md 등)을 스스로 고치지 않는다. harness 는 *발견·기록·제안*까지, 실제 수정은 사용자 승인 후. "스스로 규약을 고치는" 완전 무인 자동화는 두지 않는다(`wiki/pages/decision/self-diagnosis-and-improvement-status.md` 결정).

## 필수 산출물 / 핵심 규칙
- plan 파일(CLAUDE.md §10): 매 턴 `Progress`/`Next` 갱신. **subagent 는 plan 쓰지 않음** — 메인이 single writer, 쓰기 직전 re-read 후 외부 변경 merge.
- 검증 명령 미식별 시: README / package / pyproject / Makefile / CI 확인해도 없으면 "미식별" 기록 + 추측 실행 금지. 이 상태에서 "검증 완료" 금지. 식별한 명령은 최종 검증 runner 에 **문자열·worktree cwd 그대로** 전달(runner 는 재탐색·수리 안 함).
- researcher 재진입: 어느 단계든 외부 사실(버전/API/CVE) 의문 시 호출.
- TDD Red: 새 테스트가 의도한 이유로 실패하는지 확인(기존 baseline failure 와 분리).
- feedback memory 참고(CLAUDE.md §12): Explore 시 `MEMORY.md` 인덱스의 관련 feedback(행동지시문)을 확인해 작업에 적용한다. 상세·근거 필요시 본문 read. 인덱스는 항상 주입되지만 명시적 확인으로 누락을 막는다.
