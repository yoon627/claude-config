---
title: review-guide — 구현 중 임의 결정 신고 + Report "읽을 곳" 으로 사람의 diff 리뷰 범위를 좁힌다
status: done
started: 2026-10-07
updated: 2026-10-08
---

# Goal
사용자가 diff 전체를 읽지 않고도 설계 의도가 박힌 지점만 골라 읽을 수 있게 한다. 구현 중 plan 이 정하지 않은 동작을 정했으면 신고하고, Report 가 이미 있는 기록(Acceptance·⚠️·plan 이탈)에서 "읽을 곳" 을 모아 보여준다. GitHub issue #234.

# Intent
- Problem: dlc 는 계획 단계(Intent·Acceptance·plan-reviewer·⚠️ self-flag)와 검증(TDD·evidence gate·code-reviewer)은 촘촘하지만, 사람이 최종적으로 "diff 의 어디를 읽어야 하나" 를 알려주는 산출물이 없다. Report 는 변경 요약·파일·검증·영향·리스크라 위치 단위 안내가 아니다. 또 ⚠️ self-flag 는 3단계(plan 작성) 전용이고 §10 동기화는 plan 과 *다른* 결정만 다뤄서, 구현 중 plan 이 *정하지 않은* 세부(실패 시 동작·기본값·경계 입력 처리)를 모델이 채운 것은 어디에도 남지 않는다 — 사람이 코드를 읽어야 하는 바로 그 지점이다.
- Constraints: 새 단계·새 plan 섹션·새 subagent 를 만들지 않는다(16단계 표의 단계 수 불변 — 기존 행의 서술만 보탠다). opt-in 선택지로 만들지 않는다 — 2026-09-28 "변경 이해 리포트+퀴즈" 옵션이 14회 제시·0회 선택으로 제거됐고 AskUserQuestion 선택지 4개 상한도 그대로다(remove-quiz-option). self-flag 원칙(닫힌 트리거·해당 없으면 침묵·개수 상한 없음)을 유지한다. `## 결론` 이 마지막 `## ` heading 이어야 한다(`dlc-early-stop` 결론 축). CLAUDE.md 는 고치지 않는다(사용자 결정 2026-10-07, #223).
- Out of scope: 퀴즈·이해 확인 옵션 재도입. Stop hook 으로 "읽을 곳" 블록 강제 — 반복 누락이 확인되면 별도 작업. trivial 규모. plan 파일이 없는 small(트리거 4 의 "plan 이 정하지 않은" 범위가 전부라 무의미하고 기록처도 없다 — 그 diff 는 code-reviewer 가 그대로 본다). 위험 도메인(인증·인가·금전·영구 삭제·동시성)의 규모 승급 — 사용자 결정(아래 Open questions 1). `/e merge` PR 본문으로 "읽을 곳" 전달(`# Deferred`).
- Open questions:
  - (해소) 위험 도메인 승급 — 승급하지 않는다. 사용자 판단(2026-10-07): "규모가 커진 부분을 AI 가 확인하면 된다". dlc 규모표상 small 도 이미 code-reviewer 를 거치므로(✅ `skills/dlc/SKILL.md` 규모표) 그 판단이 현행 동작이다 — 규모 gate 를 바꾸지 않는다.
  - (해소) "읽을 곳" 정의 위치 — dlc SKILL 16 Report 에만 둔다(사용자 결정 2026-10-07). CLAUDE.md §3-6 에는 올리지 않는다(#223, ops-doc-slimming 과도 정합).
  - (해소) "읽을 곳" 배치 — 본문 `## 읽을 곳` 블록(결론 앞) + 사람 판단이 필요한 출처 (2)·(3) 항목은 `## 결론` 의 `**다음**` 에도 `file:line — 확인할 것` 으로 올린다(사용자 결정 2026-10-07, plan-reviewer 강한 우려 1 — §3-6 "마지막 블록만 본다").
- 분할: 없음 — A(트리거 4)·B(읽을 곳)·C(테스트 식별자)는 A→C→B 순서면 각자 혼자 머지돼도 모순이 없지만(순차 의존은 분할 사유가 아니다), 세 단위가 같은 세 파일(SKILL·code-reviewer·README)의 인접 문단을 각각 수 줄씩 고쳐 plan·worktree·리뷰·머지 고정비 3배 대비 이득이 없다.

# Progress
- 2026-10-07: 초안(issue #234 본문 — claude.ai 채팅에서 공개 repo `1086b28` 기준 작성). `skills/dlc`·`agents/code-reviewer.md` 는 그 뒤 변경 없음(`git diff --stat a11dc37 HEAD`, README 만 2줄 변경 — 대상 행 아님).
- 2026-10-07: 착수. worktree `review-guide`(base `origin/main@d78c62d`). Explore — self-flag 표기는 `skills/dlc/SKILL.md` 54·58·106·110행, `README.md:327` 뿐(`agents/plan-reviewer.md:31`·`CLAUDE.md:204` 는 처분값·우선 검토 서술이라 불변). wiki decision 조회. Open questions 2건 사용자 확인.
- 2026-10-07: plan-reviewer CONDITIONAL(강한 우려 6). 배치는 사용자 결정, 나머지는 `# Review Disposition` 대로 반영해 Decisions·Acceptance 를 고쳤다(구현 전 — 카운터 리셋 대상 아님).
- 2026-10-07: 구현(SKILL·code-reviewer·README). Acceptance 7 시험 적용 — wiki-search plan: 출처 (1)은 Acceptance 1·2 에 테스트 파일까지만 있고 테스트 이름이 없다(C 가 채울 칸), 6·7 은 위치 없는 항목(증거만), 구현 위치는 기록에 없어 Report 시점에 코드에서 산출해야 한다. 출처 (3)은 plan 대비 이탈 2건(Disposition 27·28행)이 `fix` 로만 남아 자유 서술을 읽어야 가를 수 있다 — `[plan 대비]` 태그·바뀐 쪽 기록이 필요하다는 근거.
- 2026-10-08: `/e merge` — 커밋 ac3a72b push, PR #235 생성(MERGEABLE). plan done 은 이 PR 에 실어 머지한다.
- 2026-10-08: 최종 검증(격리 runner) — 명령 7개 exit 0, 어긋남 3건 처분(`# Review Disposition` 최종 검증 줄). 사용자가 바뀐 규칙을 쉬운 요약으로 확인하고 커밋 승인.
- 2026-10-07: code-reviewer REQUEST CHANGES(Major CONFIRMED 3·PLAUSIBLE 1) → fix loop 1회차 → 재리뷰 APPROVE(Minor 4·Nit 3) → 2회차에서 Minor 3·Nit 3 반영. verify changed ALL PASS(skip: ps1 — PowerShell 없음), plan-lint 0, test_sync_codex_agents OK, test_wiki_check 135 OK.

# Next

# Decisions
- wiki decision 조회(2026-10-07, 공용 wiki clone `/root/repos/claude-wiki` 를 `rg` 로 — 이 서버엔 `uv` 가 없어 `wiki_search.py` 미실행): [[ops-doc-slimming]](상시 주입 문서를 늘리지 않음 — CLAUDE.md 미변경으로 따름) · [[unknowns-discovery]] 표의 Explainer & Quiz "제거함 — 변경 설명이 필요하면 사용자가 요청한다"(따름 — "읽을 곳" 은 설명이 아니라 기존 기록에서 모은 위치 포인터라 그 결정을 뒤집지 않는다) · [[evidence-gate]](Acceptance 증거 대조 — 출처 (1)이 이 기록을 재사용, 따름) · [[self-diagnosis-and-improvement-status]](빈 체크리스트 의례 기각 — 트리거 4 도 닫힌 조건·침묵·개수 상한 없음으로 따름). 뒤집는 결정 없음.
- A. ⚠️ self-flag 트리거 4(dlc self-flag 절). 적용: 구현 중 **8~15단계**(테스트 assert 로 정한 동작 포함 — code-reviewer Major 1), plan 파일이 있는 **small 이상**(묶음 trivial 제외). 문안 요지: plan·`# Intent`·`# Acceptance` 가 정하지 않은 **관찰 가능한 동작**(실패·예외 시 동작, 기본값·임계값·타임아웃, 경계 입력 처리, 외부 부작용의 순서·조건)을 정했고, **그럴듯한 선택지가 둘 이상이었으며 고른 쪽이 관찰 가능한 결과를 바꿀 때만** 적는다. 기존 코드·호출부 계약·같은 레이어 관례가 이미 정한 것, 선택지가 하나뿐이던 것, 동작 불변 내부 세부는 침묵(plan-reviewer 강한 우려 3 — 트리거 4 는 본래 흔해 신호가 희석된다). 8~15단계의 트리거 1~3 줄과 §10 동기화 "~로 변경" 줄도 접두 `⚠️ (구현)` 으로 같은 처분·Report 경로를 탄다(출처 (2)로 흡수 — 강한 우려 4(c), code-reviewer Major 3). 자기 진단 판정은 그대로이고 Acceptance 기준·사용자 가시 산출물을 바꾸는 선택은 반드시 묻는다. 기록: 접두 공통, 트리거 4 본문은 `⚠️ (구현) <정한 동작> — <다른 선택지> — <택한 쪽과 이유> — <파일·심볼>`(줄번호 대신 심볼 — 줄은 이후 수정으로 밀린다). 절 제목·도입부의 "계획을 쓰는 쪽" 주체 표기와 "3단계"·"3종" 은 그에 맞게 고친다.
- A 의 처분 경로: 트리거 1~3 은 지금처럼 6→7단계. 트리거 4 는 11단계 code-reviewer 입력에 `(구현)` ⚠️ 를 "우선 검토" 로 넘기고 12단계에서 같은 처분값(`resolved`/`accepted-risk`/`deferred`)으로 남긴다. 그 뒤에 생긴 줄은 12 fix loop·14 재리뷰에 넘기고, 재리뷰를 거치지 않은 줄(15단계 검증 수리·재리뷰 생략)만 `⚠️ (구현) [리뷰 미경유]` 로 메인이 처분해 읽을 곳에 반드시 넣는다(강한 우려 4, code-reviewer Minor). 처분 대응: 리뷰어 타당 → `accepted-risk`, 리뷰로 바꿈 → `resolved`. 리뷰어가 반박해 finding 이 되면 두 처분을 한 줄에 함께 적는다(강한 우려 6). code-reviewer 에는 12번 관점(구현 중 임의 결정 — plan 경로를 받으면 미신고 결정도 트리거 4 와 같은 조건으로 찾고, 전달받은 줄은 먼저 본다)과 출력 슬롯 `## 구현 ⚠️ 응답` 을 둔다 — 동의해도 줄마다 답이 남아야 12단계 처분 근거가 생긴다(강한 우려 6(a)). Codex 에는 주지 않는다(독립 입력 원칙 `code-reviewer.md` Codex 절).
- B. dlc 16 Report 에 `## 읽을 곳`(H2 — 결론 판정이 마지막 H2 만 보므로 `###`·굵은 라벨을 결론 뒤에 두면 hook 이 못 잡는다, `scripts/dlc-early-stop.js`). 조건: medium 이상, 또는 `⚠️ (구현)` 줄이 있는 작업. 판정이 BLOCKED·NEEDS-HUMAN 이어도 낸다. 출처는 닫힌 3종 — (1) `# Acceptance` 각 항목 → 구현 위치 `file:line (심볼)` → 증거(테스트 식별자·명령) 한 줄, 구현 위치가 없는 항목(전체 검증·문서 동기화)은 증거만, 증거가 없는 항목은 `미충족`/`미검증` (2) `⚠️ (구현)` 각 줄 → `file:line` (3) code-reviewer `[plan 대비]` finding 중 처분이 `false-positive` 가 아니고 바뀐 쪽(`코드`/`plan`/`둘 다`/`없음`)이 `코드` 만은 아닌 것(plan 을 코드에 맞췄거나 defer/wontfix — wiki-search plan:135-136 실측처럼 `fix` 에 plan 을 고친 이탈이 섞이므로 처분값만으로는 못 가른다, 강한 우려 5). `file:line` 은 Report 시점 작업트리 기준(커밋했으면 HEAD 와 같다 — BLOCKED·커밋 보류에서도 맞게, code-reviewer Major 2). 0건이면 생략. 출처 (2) 중 `resolved` 가 아닌 것과 (3) 은 `## 결론` `**다음**` 에도 `file:line — <무엇을 확인할지>` 로(사용자 결정). 결론에 새 라벨은 만들지 않는다.
- B 를 위한 기록 규칙: code-reviewer 11관점 finding 에 `[plan 대비]` 태그, 메인은 그 finding 의 처분 줄에 태그와 바뀐 쪽(`코드`/`plan`/`없음`)을 적는다(dlc fix loop 절) — compaction 뒤에도 기록만으로 출처 (3)을 가를 수 있게.
- C. 테스트 식별자: 테스트를 **작성할 때(늦어도 evidence gate 전)** 그 테스트가 증거인 Acceptance 항목의 검증 칸에 `path::test_name`(관찰이면 명령)을 채운다 — 규모표상 버그 아닌 medium 에는 8단계 TDD Red 가 없을 수 있어 단계 번호로 묶지 않는다. 빈 칸을 채우거나 식별자를 덧붙이는 것은 구체화라 승인 대상이 아니고, 검증 실패 수리 중 이미 적힌 식별자·명령을 바꾸거나 빼는 것은 no-progress 승인 대상이다(code-reviewer PLAUSIBLE Major·재리뷰 Minor). 규칙 문안은 단계 번호로 묶지 않고, 표 8행에는 TDD 가 있는 흐름의 표기로만 둔다. assert 적합성 문장은 code-reviewer **4번(테스트) 관점**에 둔다 — 11관점에 두면 "기본 Minor" 를 물려받는데, assert 하지 않는 테스트는 evidence gate 를 거짓으로 통과시키는 결함이다(강한 우려 6(b)).
- 위험 도메인 승급 안 함 — 사용자 결정(2026-10-07, Intent Open questions 1). 기각안: 규모 gate 에 "인증·인가·금전·삭제·동시성이면 small→medium" 추가(20줄 권한 수정에도 plan 마찰, 사용자가 AI 확인으로 충분하다고 판단).
- 기각: opt-in 이해 리포트·퀴즈 재도입 — 사용 0회 실측과 선택지 4개 상한(remove-quiz-option). 새 plan 섹션 `# Review Guide` — `file:line` 이 후속 수정(fix loop·검증 수리)과 ff 불가 시 rebase 로 밀리고, 커밋 뒤 plan 에 쓰면 tree 가 다시 dirty 가 된다(commit-check 는 최종 tree 를 보존하므로 사유가 아니다 — plan-reviewer 정정). 전용 subagent — 출처가 메인 기록이라 격리 spoke 가 더할 정보가 없다. 항목 개수 상한 — self-flag 원칙과 같은 이유로 두지 않는다. CLAUDE.md §3-6 에 정의 한 구절 — 사용자 결정(dlc 만). 결론에만 두는 안 — Acceptance→위치 전체 지도가 빠진다(사용자 결정).
- ⚠️ "읽을 곳" 을 Report 에 상시 넣으면 사용자가 실제로 그 위치를 읽는다 — 퀴즈 제거 근거는 *opt-in* 미사용이고, 상시 블록의 사용 여부는 실측이 없다 — 마찰 최소(기존 기록 재사용·0건 생략)와 결론 `**다음**` 병기를 택하고, 관찰 지표·재검토 시점은 `# Deferred` 에 둔다.
- codex 병행 리뷰 생략 — 이 서버에 `codex` 미설치(`codex --version` → command not found, CLAUDE.md §9 미가용 사유).
- Acceptance 3 문구를 리뷰 반영 문안(작업트리 기준·`⚠️ (구현)`·`<무엇을 확인할지>`·결론 병기 필터)에 맞춰 고쳤다 — 이유: code-reviewer Major 2 등으로 규칙 자체가 바뀌어 옛 문구는 폐기된 규칙을 요구한다. evidence gate 전이고 검증 실패 수리가 아니라 no-progress 카운터 대상이 아니다.
- Acceptance 1 허용 목록에 제목의 목적어(`우려를`)를 더했다 — 사용자 승인(2026-10-08). 이유: 최종 검증 runner 가 `[-우려를-]` 을 허용 목록 밖으로 보고했다. 제목 변경은 트리거 4 가 우려가 아니라 임의 결정이라 생긴 것(plan-reviewer 약한 우려 "수정 범위")이고, 처음 목록을 쓸 때 목적어를 빠뜨렸다. 트리거 1~3·침묵·형식·처분값 문장의 보존이라는 항목의 의도는 그대로다.
- SKILL 크기 36,490B → 41,782B(+14.5%) — 늘어난 문장은 리뷰 지적별 경계 조건이라 simplify 에서 줄이지 않았다([[ops-doc-slimming]] 은 bytes 를 hard gate 로 두지 않는다). Report 리스크.
- 커밋 단위: 1개 — 세 목적이 같은 세 파일의 인접 문단을 고친다. 순차 단위 커밋(A→C→B)도 가능하지만 각 단위가 수 줄이라 리뷰 단위로 나눌 이득이 없다.

# Acceptance
1. dlc self-flag 절에 트리거 4 가 있고 기존 트리거 1~3 문장·침묵 규약·기록 형식 문장·처분값 문장의 기존 내용이 유지된다. 검증: `git diff --word-diff=plain origin/main -- skills/dlc/SKILL.md`. 통과: 삭제 토큰 `[-…-]` 이 허용 목록에만 있다 — self-flag 절 제목의 주체·목적어(`우려를` → `우려와 임의 결정을`)·단계 표기, 도입부 마지막 문장의 주체, `3종`, 처분 bullet 첫머리(트리거 1~3 으로 범위 한정). 그 밖의 `[-…-]` 0.
2. `⚠️ (구현)` 처분 경로가 self-flag 절·파이프라인 표 9·11·12·14 행·fix loop 절에서 같은 단계(11 입력·12/14 재리뷰 전달, 재리뷰 없는 줄만 `[리뷰 미경유]`·메인 처분)와 같은 처분값을 말한다. 검증: diff 대조.
3. dlc 16 Report 불릿에 "읽을 곳" 의 조건(medium 이상 또는 `⚠️ (구현)` 줄이 있는 작업, BLOCKED·NEEDS-HUMAN 포함)·`## 읽을 곳` H2·결론 앞 배치·닫힌 출처 3종(위치 없는 항목은 증거만, 증거 없으면 `미충족`/`미검증`, Report 시점 작업트리 기준)·0건 생략·출처 (2)(`resolved` 제외)·(3) 의 결론 `**다음**` 병기(`file:line — <무엇을 확인할지>`)·결론 새 라벨 금지가 명시된다. 검증: diff 대조.
4. dlc Acceptance 절에 테스트 식별자 기입 규칙(작성 시점·빈 칸 채우기는 승인 불요·수리 중 변경은 승인), `agents/code-reviewer.md` 에 4번 관점 assert 적합성 문장·11번 `[plan 대비]` 태그(템플릿 위치 포함)·12번 구현 중 임의 결정·출력 슬롯 `## 구현 ⚠️ 응답`·Codex 미전달. 검증: `git grep -n -e 'assert' -e '(구현)' -e 'plan 대비\]' agents/code-reviewer.md`.
5. README 동기화: dlc 절 self-flag 서술이 트리거 4 를, code-reviewer 표 행이 assert 적합성·`(구현)` ⚠️ 우선 검토·`[plan 대비]` 태그를 반영하고, dlc 절에 "읽을 곳" 서술이 있다. 검증: `git grep -n -e 'self-flag' -e '읽을 곳' -e 'assert' README.md`.
6. `bash scripts/verify.sh changed` 마지막 줄 `ALL PASS`(skip 이 붙으면 skip 축이 이 변경과 무관함을 보인다) + `node scripts/plan-lint.js plans/2026-10-07-review-guide/review-guide-plan.md` exit 0.
7. 시험 적용: 과거 plan `plans/2026-09-30-wiki-search/wiki-search-plan.md` 의 기록만으로 새 규칙의 출처 (1)·(3) 을 산출해 본다. 통과: 산출 가능한 것과 불가능한 것(옛 기록엔 `[plan 대비]` 태그가 없다)을 `# Progress` 에 기록 — 규칙이 기록만으로 동작하는지의 관찰.
8. 실측: 이 작업 자신의 16 Report 에 `## 읽을 곳` 이 규칙대로(출처 3종에서만, `## 결론` 앞, 출처 (2)(3) 이 있으면 결론 `**다음**` 병기) 출력된다. 검증: Report 관찰.

# Key Files
- skills/dlc/SKILL.md — self-flag 절(A), Acceptance 절(C), 파이프라인 표 8·9·11·12 행, fix loop 절(`[plan 대비]` 처분 기록), 16 Report 불릿(B)
- agents/code-reviewer.md — 4번 assert 적합성(C), 11번 `[plan 대비]` 태그(B), 12번 `(구현)` ⚠️ 우선 검토 + 출력 슬롯(A), Codex 미전달
- README.md — code-reviewer 표 행(318), dlc 절 self-flag(327)·"읽을 곳" 서술

# Review Disposition
- [plan-reviewer ⚠️ self-flag 우선 검토] "읽을 곳" 상시 노출의 효용(추정) — accepted-risk: 배치는 사용자 결정(본문+결론 `**다음**` 병기)으로 §3-6 충돌을 줄였고, 효용은 관찰 지표로 사후 판정(`# Deferred`).
- 강한 1 (배치·관찰 지표) — fix: 사용자 결정 반영 + `# Deferred` 에 지표·재검토 시점.
- 강한 2 (Acceptance 1 통과 불가) — fix: `--word-diff` 와 허용 삭제 목록으로 재작성(구현 전).
- 강한 3 (트리거 4 경계) — fix: 침묵 조건(관례·계약·단일 선택지)·"선택지 둘 이상 + 결과 변화" 조건·plan 있는 작업 한정, Intent·B 조건의 trivial/"규모 무관" 모순 해소.
- 강한 4 (시간 창) — fix: 9~15단계, 11 이후는 `(구현·리뷰 미경유)`·메인 처분·읽을 곳 필수.
- 강한 5 (출처 (3) 판정 불가) — fix: `[plan 대비]` 태그 + 처분 줄에 바뀐 쪽 기록, 필터 재정의, §10 "~로 변경" 줄 `(구현)` 흡수.
- 강한 6 (처분 경로 결함) — fix: code-reviewer 12번 관점 + 출력 슬롯, assert 를 4번 관점으로, 반박 시 한 줄 병기.
- 약한: `# Review Guide` 기각 사유 정정 — fix. `file:line (심볼)`·Report 시점 HEAD — fix. 위치 없는 항목 — fix(증거만). C 시점 — fix("작성할 때, 늦어도 evidence gate 전" + 구체화 문구). 분할·커밋 단위 근거 — fix. wiki 관계(unknowns-discovery :22) — fix(Decisions 첫 줄). wiki 동기화 3곳 — defer(main 세션, `# Deferred`). 수정 범위(절 제목·도입부·표 9행·README 318) — fix. Codex 에 ⚠️ 전달 여부 — fix(전달 안 함 명시). Acceptance 6 plan-lint 명령 — fix. Acceptance 7 자기 참조 — fix(과거 plan 시험 적용 항목 추가, 커밋 전 diff 확인을 Next 에). Codex toml 재동기화 — defer(Report 리스크·`# Deferred`). Q3 heading — fix(`## 읽을 곳` H2 고정, 결론 새 라벨 금지). doc-drift mtime — fix(README 마지막, Next).
- [code-reviewer 1회차] Major 1 8단계 Red 누락 — fix(8~15단계·assert 포함). Major 2 HEAD 기준 — fix(작업트리 기준). Major 3 "~로 변경" 흡수 미정 — fix(접두 `⚠️ (구현)`·같은 경로). PLAUSIBLE Major 식별자 교체 우회 — fix. Minor 미경유 문자열·12/14 재리뷰·12번 0줄 gate·미신고 결정 경로·트리거 1~3 구현 중·escalation 경계·자리표시·처분값 대응/결론 필터·`둘 다` — fix. Minor plan 대비 3건(Decisions C·trivial·Acceptance 7) — fix(plan 쪽 수정 `[plan 대비] 바뀐 쪽: plan`). Minor SKILL +11% — wontfix(경계 조건이라 유지, Report 리스크). Nit 표 11행 arch·템플릿 태그·9~15 경계·12번 심각도·근거 링크·BLOCKED 표기 — fix. Nit Codex 가 plan 을 읽을 수 있음 — wontfix(독립성은 프롬프트 관례).
- [최종 검증 runner] Acceptance 2 — fix loop 절에 `⚠️ (구현)` 언급 없음 — fix(한 줄 추가). Acceptance 1 — `[-우려를-]` — fix(허용 목록 보완, 사용자 승인). Acceptance 6 — skip 붙음 — 해당 없음(항목이 무관한 skip 을 허용, ps1 은 PowerShell 부재).
- [code-reviewer 재리뷰 APPROVE] Minor 식별자 변경 승인 범위 — fix(수리 중으로 한정). Minor 12번 기준 비대칭 — fix(트리거 4 와 같은 조건). Minor escalation 축소 해석 — fix(자기 진단 판정 유지 명시). Minor 크기 +13.7% — wontfix(Report 리스크). Nit 기록 형식 접두·plan 한정·wiki 문구 — fix.
- 누락 시나리오: BLOCKED/NEEDS-HUMAN Report — fix(낸다). `/e merge` PR 본문 전달 — defer. rollback 기준 — defer(`# Deferred` 지표와 함께). 가장 위험한 단계 A 의 발동량 선확인 — wontfix(과거 plan 의 구현 결정은 기록이 없어 재현 불가 — 침묵 조건 강화와 도입 후 관찰로 대체, Acceptance 7 은 기록 기반 출처만 시험).

# Deferred
- 공용 wiki 동기화(main 세션 `/wiki ingest`): `pages/concept/unknowns-discovery.md:23` Implementation Notes 행에 트리거 4, `pages/decision/evidence-gate.md:18` Acceptance 형식에 테스트 식별자, `pages/concept/dlc-development-cycle.md:27` self-flag·Report 서술. 출처: 공개(이 repo).
- 관찰·되돌림 기준: 도입 후 한 달(2026-11-07 재검토) 동안 (a) `## 읽을 곳` 이 나간 Report 다음 사용자 메시지가 그 위치·항목을 언급한 비율 (b) 작업당 `(구현)` ⚠️ 줄 수. (b) 가 작업당 10줄을 넘는 일이 반복되거나 (a) 가 0 이면 트리거 4 문안·읽을 곳 조건을 재검토. 측정은 세션 로그 집계(remove-quiz-option 과 같은 방식). 심각도 low.
- `/e merge` 가 만드는 PR 본문으로 "읽을 곳" 전달 — 실제 diff 리뷰가 일어나는 곳. 심각도 low, `skills/e/SKILL.md`.
- `agents/*.md` 변경은 Codex agent toml 사본에 자동 전파되지 않는다 — 머지 뒤 각 머신에서 `sync_codex_agents.py` 재실행(README 의 bootstrap 절). 심각도 low.
- `scripts/dlc-signal.js` DISPOSITION_LINE 이 self-flag 처분값(`resolved`/`accepted-risk`/`deferred`)을 세지 않아 트리거 4 남발·침묵에 telemetry 가 없다. 심각도 low.

# Blockers
