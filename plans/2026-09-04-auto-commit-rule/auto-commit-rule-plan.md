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
- 2026-09-04: 1차 커밋 `f643a61`(새 규약대로 — 사용자 지시 없이 커밋 = Acceptance 6 행동 증거).
- 2026-09-04: **스코프 확장(사용자 결정)** — Deferred 1번(trivial-on-main 커밋 도달 불가)을 미루지 않고 해소한다: **trivial 도 worktree 에서 작업**(D13). 영향 범위 전수 조사(`wiki/` 포함) 결과 18파일 49곳 중 **trivial 을 worktree 밖에 두는 문장 11곳**이 대상. `scripts/guard-worktree-edit.js` 는 규모 개념이 없어 **코드 변경 불필요**(직접 확인).

- 2026-09-04: 2차 구현 — 분기 기준 치환 11곳(`CLAUDE.md`·`skills/dlc`·`README`) + wiki 4파일 동기화(`dlc-wt-autoflow` 결정 절 신설·`worktree-per-task`·`index`·`log`). 규모 재판정 **small**(문장 치환·새 로직 0·설계 선택지 없음)이라 plan-reviewer 생략, code-reviewer 로 검증.
- 2026-09-04: code-reviewer 2차 **REQUEST CHANGES** Major 6 → fix loop 1회로 반영. 핵심: ① 새 기준이 **worktree 사본 없는 gitignored 글로벌 상태**(`projects/…/memory/`·`settings.local.json`)까지 삼켜 §12 memory 적립이 불가 → §3-1·§8 에 예외 명시 ② `skills/c/SKILL.md:68` 옛 기준 잔존(전수 조사 재누락) → 치환 ③ `wiki/pages/concept/dlc-development-cycle.md` 가 1차 커밋 편입 미반영(defer 전제 오류) → 동기화 ④ worktree base=`origin/default` 라 main dirty 파일이 안 담김 → `skills/wt/SKILL.md` §3 에 dirty 확인 0단계 추가 ⑤ main 편집 발생 시 복구 절차 부재 → §8 에 "`/wt` 로 옮겨 재적용" 추가 ⑥ 경량 종결 경로 부재(아래 `# Blockers`). Minor 6·Nit 4 도 반영(역함의 문구 3곳·`plans/` 오기재·미짝 `**`·용어 통일).

- 2026-09-04: 2차 커밋 `69d3e88`. 이어 §13 적립(사용자 결정) — `wiki/pages/decision/lesson-grep-absence-not-proof.md` 를 확장(중복 금지로 새 페이지 대신 기존 페이지에 사례 2·3 추가).
- 2026-09-04: **D15 가 불충분함이 실측으로 드러남** — `MEMORY.md` 인덱스를 갱신하려다 **하네스 네이티브 격리에 차단**("Edit the worktree copy" — gitignored 라 사본이 없다). `guard-worktree-edit.js` 는 allow 하지만 네이티브 격리가 그 위에 있다. code-reviewer 의 Open question(2026-08-12 실측이 현행 하네스에서도 유효한가)이 **재현으로 확인**됨. → CLAUDE.md §3-1·wiki 예외 절을 "main 경로 편집이 정상" → "**worktree 안에서 시도하지 말고 main 복귀 후 적립**"으로 정정.

# Next

3차 커밋 → `/e merge`(push·PR·머지·정리) → **main 복귀 후 `MEMORY.md` 인덱스 갱신**(worktree 안에서는 네이티브 격리로 불가)

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
- **D13. trivial 도 worktree 에서 작업한다** (사용자 결정 2026-09-04, 스코프 확장). 기존 분기 기준 "비trivial 인가"를 **"코드/파일 변경인가"**로 바꾼다 — 질문·탐색·읽기 전용·한 턴 명령만 worktree 불필요. 이유: 자동 커밋 규약(D1~D12)이 main/master 커밋을 금지하는데 trivial 은 main 에서 돌도록 돼 있어, **가장 흔한 소소한 수정에서 커밋이 도달 불가**했다(code-reviewer Minor 지적). trivial 의 *절차* 생략(리뷰/plan/TDD 면제)은 그대로 유지 — 바뀌는 것은 작업 장소뿐. 이 결정은 `wiki/pages/decision/dlc-wt-autoflow.md`(2026-08-03)의 "trivial 은 새 worktree 불필요"를 대체하므로 그 페이지와 `worktree-per-task`·`wiki/index.md`·`wiki/log.md` 동기화가 따라온다(§11).
- **D14. trivial·small 의 종결은 로컬 ff-merge** (사용자 결정 2026-09-04, code-reviewer Major 6 대응). push·PR 없이 `git merge --ff-only <slug>` 로 default 에 반영 후 §8(a) 자동 정리. 이유: D13 으로 trivial 도 worktree 브랜치에 커밋되는데 반영 경로가 `/e merge`(PR) 뿐이면 오타 1줄당 PR 1개라 실제로는 머지가 미뤄지고, 그러면 (a) 의 merged 조건이 안 걸려 worktree 가 누적된다 — "커밋 도달 불가"가 "머지 도달 불가"로 옮겨갈 뿐. ff 불가·medium 이상·CI 검증·외부 공유는 `/e merge`. push 는 어느 경로든 요청 시만이라 로컬 default 가 origin 보다 앞설 수 있다.
- **D15. worktree 강제의 예외 — gitignored 글로벌 상태** (code-reviewer Major 1). `projects/…/memory/`·`MEMORY.md`·`settings.local.json` 과 비-git 디렉토리는 worktree 사본이 없고 gitignored 라 worktree 를 만들어도 커밋될 것이 없다. 제외하지 않으면 §12/§13 memory 적립이 네이티브 격리에 막힌다(`wiki/pages/decision/native-overlap-ledger.md:66` 실측). `scripts/guard-worktree-edit.js:107-111` 이 이미 이들을 allow 로 코드화하고 있어 규약이 hook 과 어긋나던 것을 맞춘다.
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
9. **(D13) trivial 도 worktree 규약이 전 문서에서 일관** — ✅ "trivial 은 worktree 불필요/현재 worktree 에서" 류 문장 **0건**(과거 기록 인용 2곳은 의도적 보존), 분기 기준이 "코드/파일을 바꾸는가"로 통일. 역함의를 심던 "비trivial 이라 wt 필수" 3곳(`skills/c:68`·`skills/dlc:114`·`skills/improve:42`)도 치환. wiki 5파일(`dlc-wt-autoflow`·`worktree-per-task`·`dlc-development-cycle`·`index`·`log`) 동기화(§11).
10. **(D14) trivial·small 종결 경로 명시** — CLAUDE.md §8 · `skills/dlc/SKILL.md` 정리 판정 · wiki 결정 절에 로컬 ff-merge 경로 기술.
11. **(D15) worktree 강제 예외 명시** — CLAUDE.md §3-1·§8 에 gitignored 글로벌 상태 제외. `guard-worktree-edit.js:107-111` 의 allow 와 규약이 일치.

# Blockers

(없음 — Major 6 은 D14 로 해소)

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
- §11 wiki ingest(dlc 개념 페이지) → **defer 철회 → fix**. 2차 code-reviewer 가 defer 전제("D1 로 wiki 본문이 안 바뀜")가 **사실과 다름**을 지적 — D9(규모 gate 표 커밋 추가)로 `wiki/pages/concept/dlc-development-cycle.md` 미러링 대상이 실제로 바뀌었다. 해당 페이지 동기화 완료.

### 2차 리뷰(D13 trivial→worktree) 처분
- Major "gitignored 글로벌 상태까지 worktree 강제 → §12 memory 적립 불가" → **fix** (D15)
- Major "`skills/c/SKILL.md:68` 옛 기준 잔존 — `/c` 로 구멍 재개방" → **fix** (전수 조사 재누락. `# Workflow Findings` 기록)
- Major "`wiki/…/dlc-development-cycle.md` 1차 커밋 편입 미반영" → **fix**
- Major "worktree base=`origin/default` 라 main dirty 편집이 안 담김" → **fix** (`skills/wt/SKILL.md` §3 에 dirty 확인 0단계)
- Major "main 편집 발생 시 복구 절차 부재" → **fix** (§8 커밋 bullet 에 "`/wt` 로 옮겨 재적용")
- Major "trivial 종결 경로가 `/e merge`(PR) 뿐" → **fix** (D14 — 사용자 결정)
- Minor "`worktree-per-task.md:25` 의 `plans/` gitignored 오기재" → **fix** (updated 를 올리며 틀린 진술에 신선도를 찍을 뻔했다)
- Minor "매트릭스 1행 '한 턴 명령' 이 새 기준과 겹침" → **fix** ("파일 변경 없는" 한정)
- Minor "`skills/dlc:114`·`skills/improve:42` 의 역함의 근거절" → **fix** ("파일 변경이라"로)
- Minor "`workflow-failures.md:28` proposed 행 조건" → **fix** / `:38`(fixed 이력)·`docs/codex-review.md:23` → **wontfix**(이력·여전히 참)
- Minor "`skills/dlc/SKILL.md:3` description 에 worktree 단서 없음" → **fix**
- Nit "`CLAUDE.md:134` 미짝 `**`" · "README 용어 불일치" · "`dlc-wt-autoflow` sources" · "README:280 한정어" → **fix**
- `guard-worktree-edit.js` 코드 변경 불필요 판단 → 리뷰 **검증 통과**(규모 개념 없음 + 테스트 23케이스 PASS)

# Deferred

- **baseline failure**: `skills/jira-worklog/test_session_time.py::test_malformed_cwd_does_not_abort` — `classify_cwd("/repo/\0bad", …)` 가 `UNMATCHED` 대신 `MAIN` 반환. **base(`main@23c1606`) 에서 동일 재현으로 입증**(2026-09-04, 이번 `.md` 변경과 무관). 심각도 낮음(NUL 바이트 경로는 실사용 경로 아님).
- **active plan 이 main worktree 쪽 `plans/` 에만 있는 경우** 커밋 규정이 침묵한다(plan 갱신을 커밋하려면 main 커밋이 필요 → §8 금지와 충돌).
- **`skills/e/SKILL.md` 에 `add -A` 예외 1줄 추가** — §8 쪽에서 "자동 커밋 한정 + `/e` 예외"로 한정해 충돌은 해소했으나, `/e` 본문에도 적으면 더 명확. 운영 자산 자가수정 경계(§1)로 이번 스코프 밖.

# Workflow Findings

- 2026-09-04: dlc 파이프라인에 커밋 단계가 없어, 검증까지 끝낸 변경이 uncommitted 로 남고 사용자가 매번 "커밋해"라고 지시해야 했다 — 사용자 명시 지적(트리거 ③). 이 작업이 그 수정.
- 2026-09-04: Explore 에서 `wiki/` 를 grep 범위에서 제외해 참조 6줄을 놓쳤다(3곳이라 단정 → 실제 9줄). "무매칭을 없음으로 단정 금지"의 인접 실패 — **검색 범위 누락**. 영향 범위 조사 시 `wiki/`·`docs/` 를 기본 포함할 것.
- 2026-09-04: `dlc-early-stop` 이 README·`wiki/index.md` 를 이미 같은 브랜치에서 갱신했는데도 "동기화 안 됨" 경고를 냈다(오탐 **2회** — README 축 1회, wiki index 축 1회). `dlc-doc-drift.test.js` 는 56 assertions 통과라 분류 로직 자체는 정상 — ledger 의 갱신 감지 시점 문제로 추정(⚠️추정). 2회 재현됐으므로 wiki `workflow-failures` 승격 후보.
- 2026-09-04: 영향 범위 조사 실패 2회(범위 누락·매칭 오독) → `lesson-grep-absence-not-proof` 확장으로 적립 완료(사용자 승인).
- 2026-09-04: **worktree 세션에서 gitignored 글로벌 상태(`MEMORY.md`) 편집이 네이티브 격리에 차단**. 규약에 예외를 적어도 하네스가 막으므로, 적립은 main 복귀 후로 미뤄야 한다 — 규약을 실측에 맞게 정정(위 Progress).
