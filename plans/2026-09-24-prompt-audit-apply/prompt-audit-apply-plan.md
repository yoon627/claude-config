---
title: prompt-audit-apply — Opus 5.5 기준 prompt audit 결과를 운영 자산에 반영
status: done
started: 2026-09-24
updated: 2026-09-24
---

# Goal
`/claude-api prompt-audit` 가 찾은 파일 간 모순 4곳과 대상 모델(Opus 5.5) 기준 낡은 프롬프트 패턴을 운영 자산에 반영한다. 전후 비교가 필요한 항목(M2·M4·M5·M12)은 근거를 보고 적용 여부를 정한다.

# Intent
- Problem: 규칙 파일끼리 모순(AGENTS.md↔CLAUDE.md, dlc↔§8, jira-worklog↔/e, reviewer plan 경로)이 매 세션 주입되고, 이전 모델용 우회·날짜 기록이 누적돼 있다.
- Constraints: 사용자가 "다 반영해도 괜찮다, 전후 비교 항목은 비교해서 판단"이라고 지시(2026-09-24) — 운영 자산 수정 요청 충족(§1). audit 패치를 기본으로 적용하되 리뷰 반영분은 추가 편집·보류를 허용하고 그 내역을 `# Decisions`·`# Review Disposition` 에 남긴다. gitignored 전역 파일(AGENTS.md·settings.json)은 main 에서 적용(§3-1 예외).
- Out of scope: 보고서 flag F1~F7(굵게 강조 정리, dlc 묶음 intent 재작성, codex 문서 날짜 등) — 근거 부족 또는 비-Claude 대상. AGENTS.md 전체 재생성.
- 분할: 없음 — 패치들은 서로 독립이지만 모두 같은 audit 의 한 번 반영이고, 리뷰 반영(M5·M6·M7 수정, wiki 동기화)이 여러 패치에 걸쳐 한 머지에서만 서로 맞는다. 나눠도 머지 무모순은 성립하나 plan 고정비 대비 이득이 없다.

# Acceptance
worktree(커밋 전 판정):
1. 패치 02·03·04·05·06·09·10·11·12·13·14·15 가 번호순 단건 `git apply` 로 적용되고, `git diff --stat` 대상이 `CLAUDE.md`, `docs/dlc-details.md`, `agents/{architecture-reviewer,code-reviewer,plan-reviewer,researcher}.md`, `scripts/dlc-task-router.js`, `skills/{dlc,e,jira-worklog,jira-task,wt}/SKILL.md`, `README.md`, `wiki/pages/decision/fablize-adopted-disciplines.md`, `wiki/log.md`, 이 plan 디렉터리뿐이다(`skills/e`·`README.md` 는 code-review Major 반영).
2. 모순 해소 — `grep -rn '\.claude/plans/<dir>' agents/` 0건 · `grep -n '내가 이 세션에서 직접 수행한 merge' skills/dlc/SKILL.md` 0건 · `skills/jira-worklog/SKILL.md` 에 "6단계" 위임 문장 존재.
3. 패치 범위 밖 잔존 없음 — `plans/`·`.git` 제외 repo 전체에서 `가설 3개+`·`가설 경쟁` 0건. runner 는 보류라 기존 참조(skills/dlc·docs·README·wiki)가 그대로 남아야 한다(`grep -c runner skills/dlc/SKILL.md` 가 base 와 같음).
4. M6 기능 조항 유지 — `skills/dlc/SKILL.md`·`agents/plan-reviewer.md` 의 적용 범위 날짜(2026-09-09·2026-09-16) 조항이 남아 있다.
5. wiki 동기화 — `uv run --no-project python skills/wiki/check_links.py` clean, `wiki/log.md` 에 이번 갱신 1건.
6. `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음) — 현행 dlc 대로 격리 runner 로 실행.

main 복귀 후:
7. main `AGENTS.md` 가 `plans/2026-09-24-prompt-audit-apply/agents-md-h1.patch`(패치 01 + Codex worklog 단서)를 적용한 상태 — `.Codex/plans` 0건, 원격 브랜치 삭제 "항상 확인" 문장, "rollout 파일 단위" 단서 존재.
8. main `settings.json` 의 `claude-opus-5-5.effortLevel` 이 `medium`, JSON 파싱 성공, 다른 키 무변경(`git diff` 불가 — 적용 전후 JSON 비교).

# Progress
- 2026-09-24: audit 완료(보고서 scratchpad/audit/REPORT.md, 패치 16개, 사본 적용·verify ALL PASS). 전후 비교 — M2: transcript 전수에서 tool-call 마크업 누출 0건(Bash 17~31% 가 긴/여러 줄 명령인데도) → 적용. M4: small 리뷰 10건 중 1건이 실제 Major(CLAUDE.md sed→hook 우회)를 잡음 → 보류. M5: 실제 발동 1건은 중대 신호(설계 전제 변경)로 걸린 것 → 적용(리뷰 후 plan write 점검 1곳 유지로 수정). M12: A/B(fix 과제 2×2) medium·high 모두 숨은 테스트 9/9, fix 과제에서 medium 이 비용 약 29%·시간 약 35% 적음(review 과제 비용은 약 12% 적음, 품질 미채점) → 적용. main AGENTS.md 에 패치 01 적용(되돌리기: `git apply -R plans/2026-09-24-prompt-audit-apply/agents-md-h1.patch` 를 main 에서).
- 2026-09-24: plan-reviewer(+codex) CONDITIONAL — 강한 우려 4건 처분(아래 Review Disposition). 패치 12개 적용 + 리뷰 반영 편집 + wiki fablize 갱신.
- 2026-09-24: 격리 runner 검증 — verify ALL PASS·link clean·plan-lint 통과, Acceptance 3 어긋남(wiki 이력 문장이 "가설 3개+" 를 인용) → 이력 문장 표현 수정 후 0건. code-reviewer(+codex high) REQUEST CHANGES — Major 1·Minor 4·Nit 4 처분, 재검증 verify ALL PASS·router 12 passed·link clean.
- 2026-09-24: 커밋 35b3285(반영)·959527c(wiki lesson `lesson-verify-scaffold-purpose-before-removal`). main 에 AGENTS.md 최종본(Acceptance 7 ✅)·settings.json opus-5-5 effort medium(Acceptance 8 ✅, 다른 키 무변경) 적용. `/e merge` → PR #170.

# Next
(없음 — PR #170 머지로 종료)

# Decisions
- M4(small 변경의 code-reviewer 생략) 보류 — transcript 에서 small 리뷰 10건 중 1건이 저자가 놓친 교차 파일 결함(PreToolUse matcher 가 Bash 를 안 봐 sed 가 worktree 가드를 우회)을 잡았다. 표본은 작지만 제거 근거가 없어 현행 유지(fail-safe).
- M3(최종 검증 runner 제거) 보류 — runner 의 원래 목적(긴 검증 출력을 메인 컨텍스트에서 덜어냄, 2026-06-04 `dlc-final-verify-subagent`; Acceptance 를 독립 대조해 메인 판정과 갈리면 멈춤, 2026-09-07 `playbook-gaps`)을 audit 근거("결정적 실행이라 판단할 것이 없다")가 반박하지 못한다. audit 이 대체 수단이라 한 code-reviewer 11항은 정적 plan↔diff 대조라 실행 결과를 보지 않는다 — audit 보고서의 그 문장은 사실과 다르다. 기각한 대안: 07 적용 + 출력 파일 리다이렉트 규칙 + code-reviewer 재대조 추가(새 장치를 더 만드는 것이라 "scaffold 제거" 취지와 반대).
- M3·M4 결합 — 둘 다 보류라 small 변경의 독립 대조(code-reviewer)와 최종 검증 대조(runner)가 모두 유지된다. 나중에 둘 중 하나를 적용하면 다른 하나가 유일한 독립 대조가 되는지 먼저 본다.
- M6 범위 축소 — 경위 날짜(사용자 지시일·실측일·헤더 날짜)만 지우고, 적용 범위를 정하는 날짜 조항(dlc 요구사항 명확화 2026-09-09·2026-09-16, plan-reviewer 14항)은 유지. 기능 조항이라 1d/2 패턴이 아니고, "메인이 신규라고 전달한 plan" 으로 바꾸면 전달 누락 시 검사가 조용히 면제된다(dlc 6단계는 신규 여부 전달을 요구하지 않음).
- M7 완화 — "가설 3개+" 의 개수만 빼고 "원인이 불확실하면 다른 원인 후보를 반증한 근거" 원칙은 유지(첫 가설 안주 금지 보존). wiki `fablize-adopted-disciplines` 결정 기록도 같이 갱신. 기각: 원칙까지 삭제(대안 원인 배제가 보장되지 않음).
- M5 수정 — 5지점 점검 주기는 없애고 plan write 시점 1곳은 유지. wiki `self-diagnosis-and-improvement-status` 결정("plan write 시점에 점검")과 일치시키고 "재진단" 상한의 대상이 남는다.
- M12 적용 — 근거: claude-api 스킬 `shared/model-migration.md` → Migrating to Claude Opus 5.5 → "Choosing an effort level"(API 기본 medium, medium 이 Opus 5 high 이상, 같은 레벨에서 더 오래 생각) + 이 세션 A/B. 한계: 표본 2×2·천장 효과, review 과제 출력은 auto mode 분류기가 읽기를 거부해 품질 미채점. ❌모름: modelSettings effort 가 opus reviewer subagent 에도 적용되는지. 되돌리기 기준: reviewer·구현 결과에서 놓침·재작업이 눈에 띄면 그 키만 `"high"` 로 복원(파일 통째 덮어쓰기 금지).
- 최종 검증은 현행 dlc 대로 격리 runner — 처음 ⚠️ self-flag(메인 직접)는 M3 보류로 근거가 사라져 철회.
- M2 에서 "이미 반복 끊기면 `/compact`" 복구 지침도 뺐다 — 그 지침은 tool_use 누출을 전제로 한 복구책이라 전제와 함께 제거. 누출이 다시 관찰되면 그때 증상과 함께 되살린다.
- jira-task 요약은 명령 인자 대신 `--summary-file` — 요약에 backtick·`$` 가 흔해 두 셸 모두에서 해석된다(code-review Major, codex 가 printf 로 재현).

# Review Disposition
- [plan-reviewer 강1] 07 이 runner 원래 목적 미반박 — fix(07 보류, Decisions 기록).
- [plan-reviewer 강2] 10 이 신규 여부 전달 누락 시 검사 면제 — fix(기능 날짜 조항 유지, 안 a).
- [plan-reviewer 강3] Acceptance 가 패치 밖 잔존을 못 잡음 — fix(Acceptance 3·4·5 확장, wiki fablize 갱신. runner 관련 wiki 는 07 보류로 모순 없음, self-diagnosis 페이지는 M5 수정으로 일치).
- [plan-reviewer 강4] "패치 그대로" Constraint 충돌 — fix(Constraint 수정).
- [plan-reviewer 약] 07 trivial 검증 범위 확대 — 해당 없음(07 보류).
- [plan-reviewer 약] 11 이 첫 가설 안주 금지까지 삭제 — fix(원칙 유지 완화).
- [plan-reviewer 약] 09 감지 능력 근거 부족·재진단 대상 소실 — fix(plan write 점검 1곳 유지).
- [plan-reviewer 약] M12 근거 약함·subagent effort 영향 미확인 — accepted-risk(되돌리기 쉬움, 출처·한계·되돌리기 기준 Decisions 기록).
- [plan-reviewer 약] M3·M4 결합 미기록 — fix(Decisions).
- [plan-reviewer 약] Acceptance 6 과 Next 순서 — fix(worktree / main 복귀 후 판정 분리).
- [plan-reviewer 약] Acceptance 1 파일 목록 — fix.
- [plan-reviewer 약] 번호순 단건 적용 명시 — fix(Acceptance 1).
- [plan-reviewer Nit] §8 "실측 2026-08-05" 잔존 — fix.
- [plan-reviewer rollback] AGENTS.md 백업이 휘발성 경로 — fix(패치를 plan 디렉터리에 보존, 역적용 명령 Progress 기록).
- [self-flag] 최종 검증 메인 직접 — resolved(runner 사용으로 철회).
- [runner] Acceptance 3 — wiki 이력 문장이 제거 대상 문자열을 인용 — fix(이력 문장 표현 변경, Acceptance 문구는 유지).
- [code-reviewer Major] jira-task `--summary "…"` 셸 메타문자 해석 — fix(`--summary-file`, skills/e·README 예시도 정렬).
- [code-reviewer Minor] AGENTS 패치의 worklog 문장이 Codex(파일 단위 귀속)에 틀림 — fix(Codex 단서 추가, patch 재생성, main 적용은 복귀 후).
- [code-reviewer Minor] README jira-task 예시 PowerShell 전용·Acceptance 1 목록 누락 — fix.
- [code-reviewer Minor] §3-6 "§0 preamble 금지" 참조 유실·README §0 요약 — fix.
- [code-reviewer Minor] M1 업데이트 조건 축소 — fix("도구 호출이 길게 이어질 때" 추가, "도구 결과를 보지 못하므로" 과장 완화).
- [code-reviewer Nit] dlc-details "만 인라인"·router 어조·wt 자리표시자·fablize sources — fix.
- [code-reviewer Open] M2 `/compact` 복구 지침 제거 — Decisions 기록. jira-worklog 무확인 vs jira-task 확인 비대칭 — Deferred.
- fix 후 재리뷰 생략 — 수정이 리뷰어 제안 그대로이고 문구 수준이라 재검증(verify·router test·link check)으로 갈음.

# Key Files
- `CLAUDE.md` — M1·M2·M6·M8
- `skills/dlc/SKILL.md` — H3·M5·M6·M7
- `agents/*.md` — H2·M6·M9
- `skills/jira-worklog/SKILL.md`, `skills/jira-task/SKILL.md`, `skills/wt/SKILL.md` — H4·M10·M11
- `docs/dlc-details.md`, `scripts/dlc-task-router.js` — M7 동반 수정
- `skills/e/SKILL.md`, `README.md` — jira-task `--summary-file` 정렬, README §0 요약
- `wiki/pages/decision/fablize-adopted-disciplines.md`, `wiki/log.md` — M7 결정 기록 동기화
- `wiki/pages/decision/lesson-verify-scaffold-purpose-before-removal.md`, `wiki/index.md` — 이번 작업의 교훈(사용자 선택으로 ingest)
- `plans/2026-09-24-prompt-audit-apply/agents-md-h1.patch` — main AGENTS.md 에 적용한 패치 01(되돌리기용)
- (gitignored, main) `AGENTS.md` — H1, `settings.json` — M12

# Deferred
- /e 안에서 jira-worklog 등록은 무확인(skills/e/SKILL.md 6단계), jira-task description 쓰기는 매번 확인(5단계) — 둘 다 Jira 외부 쓰기라 §1 기준 비대칭. 의도된 정책 차이인지 사용자 확인 필요. 심각도 Minor. 이번 diff 가 만든 문제 아님.

# Blockers
없음
