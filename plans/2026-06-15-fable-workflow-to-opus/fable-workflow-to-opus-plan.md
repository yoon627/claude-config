---
title: fable-workflow-to-opus — Fable 5 의 workflow 행동패턴 중 Opus(.claude 설정)에 이식할 점 분석·제안
status: done
started: 2026-06-15
updated: 2026-06-19
---

# Goal

사용자는 Opus 4.8 로 Claude Code 를 쓰고 Fable 5 는 못 쓴다. **Fable 의 좋은 workflow·사고방식을 Opus 가 쓰는 이 `.claude` 설정에 이식**하는 것이 목표.
- 산출물: 코드가 아니라 **분석 + 개선 제안 plan**. 실제 구현은 사용자 승인 후 별도.
- 범위: 이 repo 의 workflow 체계(CLAUDE.md 10개 섹션 · skills `dlc`/`c`/`e`/`wt` · agents · hooks · `plans/` 핸드오프 · auto-memory).

# Progress
- 2026-06-19 PR #38 머지 완료 (main). status: done — worktree 정리.

- 2026-06-15: worktree `fable-workflow-to-opus` 생성. Explore — settings.json(`model: opus[1m]`, effort `max`/`xhigh`, fable 분기 없음)·statusline.js·CLAUDE.md 전문·skills(dlc/c/e/wt)·.gitignore(plans/ 는 whitelist ignored 확정) 정독. WebSearch 로 Fable 5 특성 1차 확인. researcher 위임 → Fable 행동패턴의 이식 가능/불가 구분 + Anthropic 공식 권장 기법 확보(아래 근거 URL). draft plan 작성.
- 2026-06-15 (마무리): plan-reviewer 검토 직전 사용자 요청으로 세션 마무리 — 분석·draft plan 보존, 구현 미착수.
- 2026-06-16: `/c` 로 이어받음(sync 어긋남 없음). **plan-reviewer(Claude) + Codex(gpt-5.5 high) 병행 검토 완료 → CONDITIONAL GO.** P1 과대평가·P2 전역 hook 부작용·놓친 갭(skill 라우팅)을 반영해 plan 보정(D5~D7, P1 中격하, P2 설계검토 only, P5 신규, Blockers 승격). `README.md:407,410` 직접 확인으로 P2 근거 검증.
- 2026-06-16 (구현): 사용자가 **P5(skill 라우팅)만 선택** → `CLAUDE.md` §3-1 Setup 에 self-check 한 문장 보강(줄 순증 0). P1/P3/P4 미선택, P2 보류.
- 2026-06-16 (commit+리뷰): P5 초안 commit `9a3c8c4` → code-reviewer(Claude+Codex gpt-5.5 high) **2 Major** 발견(§3-1 self-check ↔ §8:125 `/wt` 진입 모순 / "다단계"가 dlc 코드변경 범위 초과) → **fix**(§8 `/wt`(→dlc) 경로 정합 + "다단계" 삭제·"비자명 코드 변경" 한정 + 문장 단축) → commit `e2647cd`. 줄 순증 0 유지, working tree clean. README 동기화 불요(220행 단계 요약만).
- 2026-06-16 (/e 마무리): clean, 새 커밋 2건(`9a3c8c4`·`e2647cd`) **미push·미머지**. status `in_progress` 유지(머지 신호 없음). worktree 정리 제안 생략(unpushed + plan 이 worktree 내부 gitignored → 소실 방지) → 보존. main 복귀.
- 2026-06-16 (P1+push): 사용자 요청으로 push — 3 커밋(`9a3c8c4`·`e2647cd`·`2cd299a`) origin 반영. P1(§1 "검증 통과 ≠ 목표 충족", 줄 순증 0) commit `2cd299a`. **P3/P4 는 사용자 결정으로 skip**(§10 중복, D8). 채택 = P5·P1.
- 2026-06-16 (PR): **PR #38** 생성 → https://github.com/yoon627/claude-config/pull/38 (→ main, 머지 대기). 머지 시 status→done + plan main `plans/` 이전 + worktree 정리.

# Next

> P5·P1 구현·push 완료. P3/P4 skip(D8), P2 구현불가. 남은 건 PR/머지뿐.

1. (선택) **PR 생성·머지** — origin 에 3 커밋(`9a3c8c4`·`e2647cd`·`2cd299a`) push 됨. PR 열어 main 머지하면 작업 종료 → status→done.
2. **머지 후 정리**: worktree 삭제 전 plan 을 main `plans/` 로 이전(worktree 내부 gitignored → 함께 삭제 방지), 그 후 `/wt rm fable-workflow-to-opus`.
3. P3/P4 는 skip 확정(D8) — 재고 시 그때.

# Decisions

- **D1. Fable 4개 강점은 전부 "행동 패턴"이라 이식 가능.** 이식 불가능한 건 행동의 *존재*가 아니라 *성공률·판단 질*뿐. 근거: Anthropic 이 task decomposition·progress check·verification 을 "Must be built into harness/prompts" 로 분류 — https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents (✅ 공식). **단서(D5 검토 반영)**: 자기검증(c)을 hook 으로 *강제*하려면 "프로젝트별 검증 명령 발견" 경로가 선행돼야 한다(이 repo 도 `dlc:67` 에서 미식별 케이스를 별도 처리할 만큼 비자명) — 그 경로 없이 자기검증만은 hook 일반화 불가.
- **D2. 이 repo 의 §10 plan 핸드오프 ≈ Anthropic "Multi-session software development pattern".** frontmatter `status`·`# Progress
- 2026-06-19 PR #38 머지 완료 (main). status: done — worktree 정리.`/`# Next`/`# Decisions`·"완료 시점 즉시 done" 이 progress log + feature checklist + "e2e 검증 후에만 완료" 패턴과 사실상 동일. → 신규 설계 아님, **빈 곳 메우기**. 근거: memory-tool 문서 multi-session 패턴 — https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/memory-tool (✅ 공식)
- **D3. 이식 원칙 (P0 — 모든 제안의 전제):**
  - ⓐ **지시 추가 최소화.** "smarter models require less prescriptive engineering"(Anthropic) + CLAUDE.md 자체 비대화 경고("too long → Claude ignores half of it"). Opus 처럼 강한 모델엔 과한 처방이 역효과.
  - ⓑ **프롬프트보다 결정론적 메커니즘(hook) 선호** — *단 전역 hook 의 rollback 비대칭(D6)을 고려*. advisory 지시는 긴 세션에서 무시될 수 있으나, 글로벌 hook 은 끄기가 어렵다.
  - ⓒ **기존 자산 강화 위주, 신규 최소.** plan/dlc/c/e/agents 를 손보되 새 개념을 늘리지 않는다.
- **D4. (사용자 기대 보정)** "Fable 사고방식을 지시로 넣으면 Opus 가 Fable 이 된다"는 **성립하지 않는다** — 모델 능력 상한(추론 질·끈기)은 프롬프트로 안 바뀐다. 바꿀 수 있는 건 *행동 습관*뿐. 목표를 "행동 유도"로 한정, 효과를 과장하지 않는다.
- **D5. (plan-reviewer+Codex, 2026-06-16) P1 "premature completion 방어 약함"은 과대평가.** `CLAUDE.md:20`(검증 못하면 완료 금지)·`skills/e:38,88`(done 자동전환 안 함, 사용자 확인)·`skills/dlc:51-52,67`(격리 runner 최종검증·통과까지 수정·미식별 시 완료 금지)가 이미 다층 방어. → 갭을 **"dlc/c/e skill 경로를 안 타는 일반 작업의 완료 재대조 느슨함"**(훨씬 좁음)으로 축소, P1 우선순위 高→中.
- **D6. (plan-reviewer+Codex, 2026-06-16) P2(Stop hook) 전역 적용 금지, 설계검토 only.** 근거: `README.md:407,410` — 글로벌 hook 은 `settings.local.json` 으로 per-repo opt-out 불가·스코프 간 누적 실행이라 rollback 비대칭(끄려면 전 머신 블록 제거 또는 `disableAllHooks`=notify·statusline 동반 사망). Stop 슬롯은 `notify-hook.js`(settings.json:80-90) 이미 점유, 검증명령 식별은 `dlc:67` 과 중복(hook 은 모델추론 없어 더 약함). → Codex 대안: 한다면 "검증 *실행*"이 아니라 "검증 *누락 경고*" 수준 + per-repo opt-in 선결.
- **D7. (plan-reviewer+Codex, 2026-06-16) P3 "일반 작업 plan read 확장"은 §10·`c:12` 경계와 충돌** ("단순 질문·탐색·한 턴짜리 제외") → **"기존 plan 존재 또는 branch/작업명 매칭 시에만"**으로 조건 제한.
- **D8. (2026-06-16, 사용자 확인) P3·P4 미채택.** 구현 직전 §10 을 직접 대조하니 둘 다 기존 규칙과 중복: P3 = §10:154(active plan 추적)·157(시작 read)과 겹치고 §10:188 적용범위와 충돌; P4 = §10:180 `# Next`·dlc 규모 gate 와 겹치고 低 우선순위·과설계. D3(비대화) 대비 실익이 낮아 사용자 확인 후 skip. → **최종 채택 = P5(skill 라우팅) + P1(완료≠목표충족)**, P2 구현불가, P3·P4 skip.

# Analysis — Fable 행동패턴 ↔ 이 repo 현황 갭

| Fable 행동패턴 | 이 repo 현황 (확인 파일) | 갭 | 이식 가능성 |
|---|---|---|---|
| **(a) 파일 working memory 능동 활용** | §10 `plans/` 핸드오프(매우 강함) + `MEMORY.md` auto-memory. c/e skill 이 plan↔실제 sync 진단·갱신 자동화. | "ASSUME INTERRUPTION → 작업 시작 시 메모리 먼저 read" 가 c skill 에만 있고 일반 작업엔 약함. memory tool(`memory_20250818`) 미사용(⚠️추정 — settings 엔 없음 확인, 기본제공 여부 ❌모름). | ✅ 인프라는 이식 가능 / 활용 *질*은 모델 |
| **(b) 진행점검→목표대비→자기수정 루프** | CLAUDE.md §2 "잘못된 방향 감지 시 중단", dlc 0→16 파이프라인 + 격리 runner 최종검증. | **갭(좁음, D5 정정)** — dlc/c/e skill 경로 안에선 진행점검·검증이 방어되나, **skill 미진입 일반 작업**엔 "목표 대비 재확인"이 느슨. (당초 "갭 큼"은 과대평가) | ✅ 루프 구조 이식 가능 / 재계획 *정확성*은 모델 |
| **(c) 자기검증 (스스로 테스트·대조)** | §1 "검증 후 완료"·§7 TDD·code-reviewer agent·**dlc 최종검증 runner=사실상 게이트(dlc:51-52)**. | skill 밖 일반 작업에선 advisory. hook 강제는 "검증명령 발견" 선행 필요(D1 단서). | ✅ 단 발견 경로 선결 / 통과 *끈기*는 모델 |
| **(d) 과제 분해** | dlc 규모 gate(trivial~structural), plan `# Next`. | 다단계 작업의 "one-feature-at-a-time + 완료조건 추적"이 느슨(단 상시 체크리스트는 과). | ✅ 추적 강화 가능 / 분해 *질*은 모델 |
| reasoning-checkpoint 라우팅 | agents 정의는 있으나 model 미지정, `model: opus[1m]` 단일. | Fable 못 쓰는 환경 → 라우팅 대상 모델 부재 → **현 시점 비적용**. | N/A (Fable 가용 시 재검토) |

> **진짜 갭 (plan-reviewer+Codex 독립 발견)**: 위 방어는 대부분 dlc/c/e skill *안*에 집약돼 있다. 따라서 실제 최대 위험은 "방어 강도"가 아니라 **비자명한 작업을 skill(dlc) 안 타고 맨손 진행(라우팅 실패)** — 모든 방어를 우회한다. → **P5**.

근거(이식 기법): note-taking/compaction/multi-agent — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents · 검증 게이트(Stop hook/verification subagent/"show evidence")·CLAUDE.md 간결성 — https://code.claude.com/docs/en/best-practices (둘 다 ✅ 공식)

# Proposals — 개선 항목 (검토 반영, 우선순위순)

> 전제: D3 이식 원칙(최소 줄·hook 선호하되 전역 rollback 고려·기존 자산 강화). 각 항목 **독립 적용 가능** — 사용자가 선택.

- **P1. skill 경로 밖 일반 작업의 완료 재대조 보강 (우선순위 中, 효과 中·비용 低)** *(당초 高→中 격하, D5)*
  - 왜: premature completion 자체는 dlc/c/e 가 이미 다층 방어(D5). 남은 좁은 갭은 skill 미진입 일반 작업에서 "목표(요청) 대비 충족 재확인"이 느슨할 수 있음.
  - 무엇: CLAUDE.md §1 기존 "검증 못하면 완료 금지" 한 줄에 "완료 선언 전 *요청 대비 충족* 재확인"을 합쳐 보강(신규 섹션 X, 줄 순증 0~1).
  - 형태: 프롬프트 최소 줄. 리스크: 과한 지시 → 역효과(D3ⓐ).

- **P2. 검증 게이트 — 설계검토 only, 전역 적용 금지 (보류, 리스크 高)** *(구현 후보에서 제외, D6)*
  - 제약: 글로벌 hook rollback 비대칭(`README.md:407,410`) + Stop 슬롯 `notify-hook.js` 점유(settings.json:80-90) + 검증명령 식별 `dlc:67` 중복 + subagent 종료 시 발화 여부 미검증.
  - 한다면(검토 한정): "검증 *실행*"이 아니라 "검증 *누락 경고*"(Codex 대안), per-repo opt-in 메커니즘 선결.
  - 결론: **구현하지 않음** (Blockers 참조). 향후 per-repo hook opt-out 이 생기면 재검토.

- **P3. working-memory "중단 가정" 보강 (우선순위 中, 효과 中·비용 低)** *(조건 제한, D7)*
  - 무엇: §10/`c` 의 "시작 시 plan read" 를 **"기존 plan 존재 또는 branch/작업명 매칭 시에만"** 일반 작업으로 가볍게 확장(§10 "단순 질문 제외" 경계 유지). memory tool 도입은 보류(중복·비대화).
  - 형태: 프롬프트 최소 줄. 리스크: §10 경계 침범 → 조건 명확히.

- **P4. 과제 분해 추적 (우선순위 低, 효과 中·비용 低)** *(다단계 한정 명확화)*
  - 무엇: **다단계 작업에 한해** plan `# Next` 에 항목별 완료조건 1~3개. 상시 체크리스트화 금지(D3ⓐ·작은 작업 운영부담). JSON feature checklist 미채택.
  - 형태: 프롬프트 가이드. 리스크: 과설계 → "다단계만" 단서 필수.

- **P5. skill 라우팅 — 비자명 작업의 dlc 진입 보강 (우선순위 中~高, 효과 中·비용 低)** *(신규, plan-reviewer+Codex 독립 발견)*
  - 왜: 이 repo 방어는 dlc/c/e skill *안*에 집약 → 최대 위험은 "비자명 작업을 dlc 안 타고 맨손 진행". Fable 의 "자율 분해/계획"이 닿는 지점.
  - 무엇: dlc 자동 적용 트리거를 더 분명히(이미 "비자명한 코드 변경 시 자동 적용"이나 실제 진입 누락 가능). CLAUDE.md §3 작업흐름에 "비자명 판단 시 dlc 경유" self-check 가벼운 보강.
  - 형태: 프롬프트 최소 줄. 리스크: 과적용(trivial 까지 dlc) → 트리거 문구 신중.

- **P0 (메타, 항상)**: 위 어느 것도 CLAUDE.md 를 키우는 방향이면 재고. **줄 수 중립**(기존 줄 보강) 또는 **hook 으로 이전** 우선 — 단 전역 hook 은 D6 rollback 비대칭 감안. 변경 후 CLAUDE.md 총량 늘면 다른 곳 축소 검토.

# Review Disposition

plan-reviewer(Claude) + Codex(gpt-5.5, high effort) 병행, 2026-06-16. **충돌 없음** (CONDITIONAL GO).
- **P1 과대평가** (Major) → **fix**: D5 — "방어 약함"→skill 경로 밖 좁은 갭, 우선순위 高→中.
- **P2 전역 hook 부작용·rollback 비대칭** (Major) → **fix**: D6 — 설계검토 only, 구현 제외, Blockers 승격.
- **놓친 갭: skill 라우팅 실패** (Major, 둘 다 독립 발견) → **fix**: P5 신규.
- **D1 자기검증 hook 일반화 과함** (Minor) → **fix**: D1 단서(검증명령 발견 경로 선행).
- **P3 §10 경계 충돌** (Minor) → **fix**: D7 — 조건 제한.
- **P4 상시 체크리스트 부담** (Minor) → **fix**: 다단계 작업 한정 명확화.
- **memory tool 미사용=⚠️추정** (Nit) → **ack**: settings 엔 없음 확인, 기본제공 여부 ❌모름. 보류 결론은 중복 근거로 유효.
- **Stop hook + subagent 발화 시나리오** (Minor) → **defer** (P2 와 함께, P2 설계검토 항목에 포함).
- Codex 단독 기여: P2 "누락 경고 수준" 대안(→D6). 메인 단독: Stop 슬롯 점유·`dlc:67` 중복·memory tool 추정성.

**(code-reviewer 2차, 2026-06-16 — P5 최종 *문구* 검토)** Claude + Codex(gpt-5.5 high), 4항목 합의:
- **Major1** §3-1 self-check ↔ §8:125 `/wt` 진입 모순(같은 트리거에 다른 첫 액션 + "진행 중 worktree 에 새 작업 안 얹기" 충돌) → **fix**: "§8 대로 `/wt`(→dlc) 경유 — 이미 작업 worktree 안이면 dlc 적용 self-check" 로 두 경로 정합.
- **Major2** "다단계"가 dlc 코드변경 한정 범위(읽기전용 제외) 초과 → **fix**: "다단계" 삭제, "비자명 **코드 변경**" 한정.
- **Minor** "비용은 없고" 과장 → **fix**: 삭제. **Nit** Setup bullet 과밀 → **fix**: 문장 단축.
- commit: `9a3c8c4`(초안) + `e2647cd`(fix). fix loop 1회로 종결(Critical 0).

# Key Files

- `CLAUDE.md` — §1(검증/완료)·§3(작업흐름)·§5(sub-agent)·§10(plan 핸드오프). P1/P3/P5 텍스트 보강 후보. **비대화 경고 대상 — 순증 최소화.**
- `skills/c/SKILL.md` — 작업 재개·sync 진단. P1 완료 재대조·P3 "시작 시 read"(조건부) 후보.
- `skills/dlc/SKILL.md` — 개발 사이클. `:51-52`(격리 runner 검증)·`:67`(검증명령 미식별 처리) = 이미 강한 방어(D5 근거). P5 진입 트리거 후보.
- `skills/e/SKILL.md` — `:38,88` done 자동전환 안 함(premature completion 이미 방어, D5 근거).
- `settings.json:80-90` · `README.md:407,410` — P2 근거(Stop 슬롯 점유 + hook 누적·rollback 비대칭). **P2 구현 금지 근거.**
- `scripts/guard-worktree-edit.js` — 기존 PreToolUse hook 패턴(참고용).
- `README.md` — 변경이 문서화 컴포넌트에 닿으면 동기화.

# Blockers

- **P2 (검증 Stop hook)**: 전역 hook rollback 비대칭(`README.md:407,410` — `settings.local.json` 으로 opt-out 불가, 스코프 간 누적 실행). per-repo opt-in 메커니즘 부재가 선결 blocker → **P2 구현 진입 금지, 설계검토만**.
- 그 외(P1·P3·P4·P5): 블로커 없음(프롬프트·skill 텍스트 변경, git revert 가능).
