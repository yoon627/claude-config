---
title: auto-commit-rule — 검증 통과 후 자동 커밋 규약 도입 (CLAUDE.md §8 + dlc 파이프라인)
status: in_progress
started: 2026-09-04
updated: 2026-09-04
---

# Goal

검증 통과 후 작업 브랜치 커밋을 **사용자 요청 없이** 수행하도록 규약화한다. Claude Code 하네스 기본값(`Commit or push only when the user asks.`)을 CLAUDE.md 명령조로 오버라이드하고, dlc 파이프라인 16단계에 커밋을 편입한다.

# Progress

- 2026-09-04: 원인 진단 — ① 하네스 기본값이 "요청 시에만" ② `CLAUDE.md:134` 는 허가문("자유롭게")이라 명령조 기본값을 못 이김 ③ `skills/dlc/SKILL.md` 16단계에 커밋 단계 자체가 없고 `/e` 로 위임 ④ `/e` 커밋조차 `wip:` 체크포인트. 사용자 결정: A+B 동시, 커밋 시점은 검증 통과 후 1회.
- 2026-09-04: worktree `auto-commit-rule` 생성(base `main@23c1606`), draft plan 작성.
- 2026-09-04: plan-reviewer 검토(**Codex 미가용 — `codex exec` 가 `workspace out of credits` 로 exit 1, §9 대로 단독**). blocker 4건. **내 Explore 가 틀렸음**: 단계 번호 참조는 3곳이 아니라 9줄/5파일(`wiki/` 를 grep 범위에서 제외한 탓). → D1 표 불변 대안 채택(사용자 확정).
- 2026-09-04: 구현 — `CLAUDE.md` §8 독립 bullet, `skills/dlc/SKILL.md` 표 3곳 + 커밋 규칙 bullet, `README.md` 2곳.
- 2026-09-04: code-reviewer(단독, Codex 미가용) **REQUEST CHANGES** Major 8 → fix loop 1회로 전건 반영. 핵심: ① 신설했던 "worktree git 은 PowerShell 도구로" bullet 이 `wiki/pages/entity/worktree-isolation-bash-guard.md:28` 의 "§8 에 규칙으로 올리지 않는다" 결정과 충돌 + macOS 실행 불가 → **bullet 삭제**, 절차는 SKILL 에 플랫폼 중립 표현으로 ② baseline failure 예외(D5) 미반영 → 추가 ③ "예상 밖 dirty" 범위 불명 → `git diff --cached --name-only` index 확인으로 대체 ④ `--no-verify` 우회 금지 신설 ⑤ 3중 기술 → 역할 분리(§8=규칙 / SKILL=절차 / README=포인터).
- 2026-09-04: simplify 체크(메인 직접) — 추가 축소 없음. always-injected 실측 `CLAUDE.md` +1,277B(+4.2%, 리뷰 시점 +1,595B 에서 감축), 절차는 조건부 로드인 SKILL(+1,351B)로 이관.
- 2026-09-04: 최종 검증(격리 runner) — node syntax 29/29 PASS · unit 13/13 PASS · JSON PASS · plan-lint PASS · shellcheck SKIP(미설치) · python 3/4(1 FAIL). FAIL 은 base 재현으로 **baseline 입증**(아래 `# Deferred`).

# Next

(없음 — 커밋 후 Report 로 종료. 후속은 사용자 선택)

# Decisions

- **A+B 동시 적용** (사용자 결정 2026-09-04). A만 하면 dlc 흐름 내 커밋 시점이 애매하고, B만 하면 dlc 를 안 타는 직접 작업에 적용되지 않는다.
- **커밋 시점 = 최종 검증 통과 후 작업 단위 1회** (사용자 결정). 중간 커밋을 막지는 않되 마지막 1회는 반드시.
- **D1. 단계 번호를 밀지 않는다 — `16 Report` 를 `16 마무리`(evidence gate → plan 업데이트 → 커밋 → Report)로 확장** (사용자 확정). 이유: ① 외부 cross-ref 9줄(5파일)이 전부 유효하게 남아 drift 0 ② "16단계 표 안 늘림" 규칙(`skills/dlc/SKILL.md:83`·`:120`, `docs/dlc-details.md:22`)과 "step 번호 불변" 선례(`plans/2026-07-04-doc-slim/doc-slim-plan.md:82`) 준수 ③ 커밋이 plan 업데이트 뒤로 자연히 밀려 D2 가 함께 해결. 기각: 번호 밀기(참조 9줄 갱신 + 두 규칙 폐기 비용이 더 큼).
- **D2. 커밋은 plan 업데이트·evidence gate 통과 뒤.** 앞서면 plan 갱신이 uncommitted 로 남아 `/e` 자동 정리 조건 3·5(`skills/e/SKILL.md:80`·`:82`)를 못 넘기고 WIP 이중 커밋이 재발.
- **D3. 스테이징은 이번 작업이 건드린 경로만.** 자동 커밋에서 `git add -A` 금지 — 전역 규약이라 무관한 사용자 변경·산출물이 섞이고 `scripts/pre-commit-check.sh` 시크릿 스캔은 `settings.json`·`plans/*.md` 만 본다. **`/e` WIP 체크포인트는 전량 보존이 목적이라 이 금지의 명시적 예외**(리뷰 지적 — 한정 없이 쓰면 `/e` 가 §8 우선 규정에 져서 오작동).
- **D3-b. 커밋 직전 `git diff --cached --name-only` 로 index 확인** (리뷰 Major). 이미 staged 된 무관 변경이 딸려 들어가는 경로를 막는다. 초안의 "예상 밖 dirty 파일이면 보류"는 범위가 불명해 규칙을 자기 무력화할 수 있어 폐기.
- **D4. 커밋 메시지**: 그 repo 의 `git log` 관례(없으면 Conventional Commits) + `Co-Authored-By` 트레일러, 본문에 *왜*(`wiki/pages/decision/comment-and-commit-policy.md:17`). **커밋 sha 는 plan 이 아니라 Report 에 적는다** — plan 에 적으면 tree 가 다시 dirty 가 돼 D2 의 효과가 무효화된다(리뷰 지적).
- **D5. "검증 통과"의 3분기**: ① 통과 → 커밋 ② 실패 → 커밋 안 함(미검증 커밋 금지 §1) — **단 §3-5 로 입증된 baseline failure 는 막지 않는다** ③ 검증 명령 미식별 → 커밋하되 보고에 "검증 미식별" 명시(미식별 repo 에서 목표가 영영 미달성되는 것을 막고, 로컬 커밋은 `git reset --soft HEAD~1` 로 가역).
- **D5-b. 커밋이 훅에 차단되면 `--no-verify` 우회 금지** (리뷰 Major). `scripts/pre-commit-check.sh:109` 가 stderr 로 우회 명령을 직접 안내하는데, 이번 변경으로 그 안내를 읽는 주체가 사람에서 모델로 바뀐다. 원인 해소 또는 보고 후 중단.
- **D6. main/master·detached HEAD 면 커밋하지 않는다** — 생략 + 사유·다음 액션 보고. detached 는 리뷰 지적으로 추가(어느 브랜치에도 없는 커밋 방지).
- **D7. `/e` 와의 경계**: dlc 16 커밋 = 검증 통과한 정식 커밋, `/e` WIP = 미완·미검증 보존. `skills/e/SKILL.md` 자체는 스코프 밖(§1).
- **D8. 멱등성**: stage 할 변경 없으면 skip. fix loop 재진입 시 중복 커밋 금지. Report 후 후속 요청으로 dlc 재진입하면 그 작업 단위의 커밋을 따로 만든다.
- **D9. 규모 gate 표에도 반영** — trivial·small 행에 `→ 커밋` 추가(medium 은 small 상속, structural 은 파이프라인 상속).
- **D10. push 는 여전히 요청 시만.**
- **D11. 실효 시 대비책**: 하네스 기본값은 Bash 도구 설명으로 매 턴 재주입돼 행동 지점에 더 가깝다. 미커밋이 2회+ 재발하면 문구를 다시 손보는 대신 `scripts/dlc-early-stop.js` 에 3번째 축(changed && verified && uncommitted → capped 1회 경고)을 추가한다.
- **D12. worktree git 실행 수단은 CLAUDE.md 규칙으로 올리지 않는다** (리뷰 Major 반영, 초안에서 변경). `wiki/pages/entity/worktree-isolation-bash-guard.md:28` 이 "분류기가 비결정적·하네스 버전 의존이라 §8 규칙으로 올리지 않고 관찰로 둔다"를 이미 결정했고, PowerShell 지정은 macOS 세션에서 실행 불가다. SKILL 절차에 "가드에 거부되면 체이닝·`git -C` 없이 단일 명령으로 다른 도구 경로 재시도(상세는 wiki)"라는 플랫폼 중립 표현만 둔다.

# Key Files

- `CLAUDE.md:135` — §8 커밋 규약 독립 bullet(규칙 단일 소스)
- `skills/dlc/SKILL.md` — 파이프라인 표 L79(16 마무리), 규모 gate 표 L33-34, L39, 커밋 절차 bullet L119
- `README.md:228` — §8 요약 / `README.md:286` — dlc 커밋 편입 포인터
- `plans/2026-09-04-auto-commit-rule/auto-commit-rule-plan.md` — 이 파일

# Acceptance

1. **CLAUDE.md §8 독립 bullet 로 명령조 커밋 규약** — ✅ `CLAUDE.md:135`. "요청 없이 커밋한다" + 하네스 기본값 원문 인용 + stage 범위 + index 확인 + 커밋 안 하는 경우(main/master·detached·검증 실패·변경 없음) + `--no-verify` 금지 + push 예외.
2. **dlc 16단계에 커밋 편입** — ✅ 파이프라인 표 L79 `16 마무리   evidence gate(…) → plan 업데이트 → 커밋 → Report`, 규모 gate 표 trivial·small 행, 커밋 절차 bullet L119.
3. **단계 번호 참조 drift 0** — ✅ `grep -rn "1[67]단계\|1[67] Report" CLAUDE.md README.md skills/ docs/ wiki/` → `17` 잔존 **0건**, 기존 `16` 참조 13곳 전부 유효.
4. **README 동기화** — ✅ `:228`(§8 요약에 자동 커밋 추가) + `:286`(dlc 커밋 편입, 규칙은 §8 이 단일 소스임을 명시).
5. **worktree 세션 git 실행 실증** — ✅ Bash 도구 git 은 격리 가드에 **거부**(이 세션 4회+ 재현), PowerShell 도구는 **성공**. 단 D12 로 **수단을 규칙에 명시하지 않고** SKILL 에 플랫폼 중립 폴백만 둔다(초안의 "그 형태를 규칙 본문에 명시"에서 변경).
6. **행동 증거 — 이 작업의 마무리 커밋을 새 규약대로 수행** (커밋 시 sha 를 Report 에 기록).
7. **CI 스위트** — node syntax 29/29 · unit 13/13 · JSON · plan-lint PASS, shellcheck SKIP(미설치), python 1건 FAIL은 baseline 입증(`# Deferred`). **회귀 없음 증거이지 목표 증거가 아님**(이번 변경은 `.md` 만 건드리고 `lint.yml` 은 md 를 검사하지 않는다).
8. **plan-lint 통과** — ✅ exit 0.

# Blockers

(없음)

# Review Disposition

- plan-reviewer blocker "참조 3곳이 아니라 9줄/5파일" → **fix** (D1 채택으로 갱신 대상 소멸, grep 에 `wiki/` 포함)
- plan-reviewer blocker "표 안 늘림 규칙 + step 번호 불변 선례 위반" → **fix** (D1)
- plan-reviewer blocker "커밋이 plan 업데이트보다 앞서는 순서 오류" → **fix** (D2)
- plan-reviewer blocker "커밋 동작 명세 3종 부재" → **fix** (D3·D4·D5)
- code-reviewer Major "PowerShell bullet 이 wiki 결정과 충돌 + macOS 미적용" → **fix** (D12 — bullet 삭제)
- code-reviewer Major "baseline failure 예외 미반영" → **fix** (D5)
- code-reviewer Major "'예상 밖 dirty' 범위 불명" → **fix** (D3-b 로 대체)
- code-reviewer Major "이미 staged 된 무관 변경 혼입" → **fix** (D3-b)
- code-reviewer Major "`--no-verify` 우회 금지 부재" → **fix** (D5-b)
- code-reviewer Major "plan `# Next`/`# Blockers` stale" → **fix** (이번 갱신)
- code-reviewer Major "`README.md:228` §8 요약 미갱신" → **fix**
- code-reviewer Major "3중 기술 + always-injected +5.3%" → **fix** (역할 분리, +4.2% 로 감축)
- code-reviewer Minor "detached HEAD" → **fix** (D6)
- code-reviewer Minor "`/e` `add -A` 충돌" → **fix** (D3 에 예외 명시 — `/e` 파일은 스코프 밖이라 미수정)
- code-reviewer Minor "커밋 sha 를 plan 에 적으면 dirty" → **fix** (D4)
- code-reviewer Minor "경로 열거 폴백 부재" → **fix** (SKILL 절차에 `git status --porcelain` + `# Key Files` 대조)
- code-reviewer Minor "중간 커밋 금지로 읽힘" → **fix** ("마지막에 1회, 중간 커밋을 막지는 않는다")
- code-reviewer Minor "trivial-on-main 은 커밋 도달 불가" → **defer** (`# Deferred` — D6 의 의도된 부작용, 사용자 판단 사안)
- code-reviewer Minor "main worktree 쪽 plan 인 경우 규정 침묵" → **defer** (`# Deferred`)
- code-reviewer Nit "하네스 원문 인용 부정확" → **fix** (원문 그대로)
- code-reviewer Nit "'규약 트레일러' dangling" → **fix** (SKILL 에 `Co-Authored-By` 명시)
- code-reviewer Nit "관례 판정 순환(`git log` 필요한데 git 막힘)" → **fix** (D12 로 자연 해소)
- code-reviewer Nit "표 16행 '통과 후에만 완료' 소실" → **fix** (표에 복원)
- code-reviewer Nit "16행 이름 `마무리` vs 참조 '16 Report'" → **wontfix** (Report 가 16 의 마지막 하위단계라 참조 유효, 표 형태는 사용자 확정)
- code-reviewer Nit "README:286 날짜·경위 표기" → **fix** (1줄 축소하며 제거)
- `wiki/pages/decision/ops-doc-slimming.md:29` 역사 인용 → **wontfix** (과거 기록)
- §11 wiki ingest(dlc 개념 페이지) → **defer** — D1 로 wiki 본문이 안 바뀌므로 스코프 밖. Report 에서 제안만.

# Deferred

- **baseline failure**: `skills/jira-worklog/test_session_time.py::test_malformed_cwd_does_not_abort` — `classify_cwd("/repo/\0bad", …)` 가 `UNMATCHED` 대신 `MAIN` 반환. **base(`main@23c1606`) 에서 동일 재현으로 입증**(2026-09-04, 이번 `.md` 변경과 무관). 심각도 낮음(NUL 바이트 경로는 실사용 경로 아님).
- **trivial-on-main 은 자동 커밋 대상 밖** — dlc 진입 매트릭스는 trivial 을 현재 worktree(흔히 main)에서 돌리는데 §8 은 main 커밋을 금지하므로, trivial 경로에서는 커밋이 도달 불가하고 "브랜치로 옮기라"는 보고만 남는다. 사용자 원 불만의 일부(main 에서의 소소한 수정)는 그대로 남음 — 바꾸려면 별도 결정 필요.
- **active plan 이 main worktree 쪽 `plans/` 에만 있는 경우** 커밋 규정이 침묵한다(plan 갱신을 커밋하려면 main 커밋이 필요 → §8 금지와 충돌).
- **`skills/e/SKILL.md` 에 `add -A` 예외 1줄 추가** — §8 쪽에서 "자동 커밋 한정 + `/e` 예외"로 한정해 충돌은 해소했으나, `/e` 본문에도 적으면 더 명확. 운영 자산 자가수정 경계(§1)로 이번 스코프 밖.

# Workflow Findings

- 2026-09-04: dlc 파이프라인에 커밋 단계가 없어, 검증까지 끝낸 변경이 uncommitted 로 남고 사용자가 매번 "커밋해"라고 지시해야 했다 — 사용자 명시 지적(트리거 ③). 이 작업이 그 수정.
- 2026-09-04: Explore 에서 `wiki/` 를 grep 범위에서 제외해 참조 6줄을 놓쳤다(3곳이라 단정 → 실제 9줄). "무매칭을 없음으로 단정 금지"의 인접 실패 — **검색 범위 누락**. 영향 범위 조사 시 `wiki/`·`docs/` 를 기본 포함할 것.
- 2026-09-04: `dlc-early-stop` 이 README 를 이미 같은 브랜치에서 갱신(`README.md:286`)했는데도 "README 동기화 안 됨" 경고를 냈다(오탐 1회). `dlc-doc-drift.test.js` 는 56 assertions 통과라 분류 로직 자체는 정상 — ledger 의 갱신 감지 시점 문제로 추정(⚠️추정). 2회+ 재현되면 wiki `workflow-failures` 로 승격.
