---
title: claude-md-dedupe — CLAUDE.md 의 자기 중복과 skill 안 절차 세부의 재서술을 지운다 (#223, 규칙 손실 0)
status: done
started: 2026-11-07
updated: 2026-11-08
---

# Goal
#223 의 결정(2026-11-06 "범위·중복 제거 먼저")대로 CLAUDE.md 에서 (1) CLAUDE.md 안에서 같은 규칙을 두 번 적은 자리와 (2) 그 skill 을 부른 세션 안에서만 쓰이는 절차 세부를 skill 과 같은 말로 다시 적은 자리를 지운다. 규칙의 범위·강도·로드 등급(항상 주입 ↔ skill 호출 시 ↔ wiki 조회 시)은 하나도 낮추지 않는다 — 문장 단위 대응표와 변이 검사가 증거.

- Why: 매 세션 주입되는 CLAUDE.md 가 54,951B 다. #223 댓글(2026-11-07)의 중복 목록이 후보를 찍었지만, 그중 skill 이 CLAUDE.md 를 "단일 출처"로 가리키는 §8(a) 정리 조건·ff-merge 절차·§3-6 보고 선택지·§11 적립 형식은 **2026-10-21 plan 리뷰가 이미 이관을 막은 것**(공용 wiki `ops-doc-slimming` "2026-10-21 실행": skill 을 안 부른 세션이 규칙을 잃는다)이라 이번에도 옮기지 않는다. 남는 것은 자기 중복과 skill 안 절차 세부의 재서술이다.
- Constraints: (1) **항상-켜짐 판정(닫힌 검사)** — 문장이 (a) 확인 없이 행동을 허락하거나 (b) 금지·확인을 요구하거나 (c) 트리거·의무이거나 (d) 그 skill 밖(단순 질문·리뷰 세션·Codex 의 `~/.codex/AGENTS.md` 심링크·subagent — 이들은 CLAUDE.md 는 받지만 skill 은 호출할 때만 읽는다)에서도 적용되면 CLAUDE.md 에 남긴다. 지우는 것은 이 넷에 해당하지 않는 **절차 세부·이유 설명·자기 중복**이다. (2) 남는 자리의 로드 등급이 원문 이상이어야 한다 — 남는 자리가 wiki 페이지(조회 시만 읽음)면 명령문은 남기고 설명 괄호만 지운다. (3) `improve.sh` 점검 3 은 `**agent-name**` 굵은 이름을 읽는다 — §5 의 네 agent 굵은 이름·호출 조건·81행 표준 순서·78행 "비자명 변경마다 필수" 는 남긴다(지우는 것은 78행의 점검 항목 나열만). (4) 섹션 번호·제목, `@` import, 138행 위임 예외, §4·§6·§7, §8(a)(b) 의 조건 번호(e:97·worktree-lifecycle 이 "condition 4" 로 인용)와 `--delete-branch` 금지, L142 ignored 파일 경고, L50 보고 규칙과 Stop hook 거짓 양성 한 줄 규칙, §11 239-240 의 의무 문장은 바꾸지 않는다. (5) 고정 문구(`plans/2026-10-26-translate-claude-md/pointers.md` — dlc "wrap up", e "push only on request", `wip:` 이어가기 문구, plan-match 의 매칭 문구, `/wiki ingest` 공유 형식, hook 메시지 `scripts/dlc-early-stop.js:175`·`guard-push-delete.js`·`guard-worktree-edit.js` 의 § 인용)는 지우지 않는다. (6) 공용 wiki 는 이 PR 에서 바꾸지 않는다 — 지워지는 문장을 인용하는 wiki 줄은 `# Deferred`. (7) CLAUDE.md 변경이라 커밋 전 사용자 word-diff 확인(§8 위임 예외 밖) — 커밋마다 3줄 요약 + 대응표 + 절별 word-diff.
- Out of scope: 출처 방향 전환(skill 이 CLAUDE.md 를 출처로 가리키는 자리 — 2026-10-21 결정 유지), 수치 목표·재개 여부(측정 뒤), §5 agent 줄, 문구 다듬기·재배열, skill description 축소, 공용 wiki 수정.
- Size: medium
- Split: none — purpose-commit bundle: #223 · 1) CLAUDE.md 자기 중복 한 벌 남기기 2) skill 안 절차 세부·이유 설명 삭제(남는 자리가 이미 같은 세기로 있는 것만) · 둘 다 CLAUDE.md 만 고치고 서로 다른 줄이라 따로 되돌릴 수 있다; 리뷰에서 지운 것이 문제면 그 커밋만 revert.

# Tasks
- [x] plan 승인 (2026-11-07) — "남은거 진행해"(#223 다음 단계를 맡긴 위임 메시지; #223 2026-11-06 결정)
- [x] plan-reviewer (2026-11-07) — CONDITIONAL: 10-21 이관 차단 누락(S1)·방향 규칙 비검증성(S2)·byte 게이트(S3)·rg 검사의 거짓 통과(S4)·세기 정의(S5) → 이 판으로 재작성
- [x] plan-reviewer 재확인 (2026-11-07) — CONDITIONAL(가깝게): 후보 행 10개 keep/축소, 인용 줄 번호 오류 2건(codex-review 31; 91 없음), 변이 검사가 자명 통과(N1) → Task 2·검사 설계 수정
- [x] 1) 자기 중복 (2026-11-07) — 실제 5행(i1~i5): 133(worktree 예외 괄호 → §3-1 포인터)·230(`rg` 가 wiki 를 건너뜀 → §2)·265(주입 경로 문장 → §12 가 가짐)·203(acceptance 증거 → §3-5 포인터, "every item" 유지)·184(토큰 스캔 범위 → §8). 45·232·250 은 손대지 않음(`in a ~/.claude main session: add to FEEDBACK.local.md: <rule>` 형식 문자열은 250 한 곳, 232 의 `# Deferred` 라우팅은 고유). 삭제 뒤 `git diff -U0` 에서 지운 문장을 절로 나눠 대응표 작성
- [x] 2) 절차 세부·설명 (2026-11-07) — 최종 10행(d1~d4·d6~d9·d11·d12) + 50행(d3) = 커밋 2, 전체 1,337자(plan-reviewer 재확인 판정 반영 — 삭제는 괄호 설명과 skill 안 세부만) — `CLAUDE.md`: §1 22행 `verify.sh changed` 괄호(dlc:39; "skip 을 통과로 읽지 말라" 는 남김) · §2 38행 Windows 괄호를 `(Windows: survives TaskStop — [[windows-bash-tool-orphan-processes]])` 로 줄임 · §3 50행 적립 경로 괄호 중 main 세션·타 repo 라우팅만 "(§11)" 로(거짓 양성 규칙·"쌓이면 workflow-failures.md" 는 남김; 대응표에서는 §11 과의 자기 중복이라 kind intra, 커밋 2 에 둠) · §3 52행은 손대지 않음("capped warning" 두 단어 — 행을 만들 가치가 없음) · §8 135행 WIP 예외 이유 · §8 140행은 **되살림**(독립 감사·code-reviewer: `--no-verify` 금지와 commit-check 를 조정하는 유일한 문장 — 대상 없음) · §8 141행 "per-line `cwd` … after returning to main also works" 세부(e:79-81; "삭제 전 step 6" 의무는 남김) · §8 145행 `origin` 만 보면 영원히 미머지 설명(e:96; 조건 4개·tip sha 보고·복구 명령은 남김) · §8 147행 `--delete-branch` 이유 괄호(e:61; 금지와 "승인으로 간주" 는 남김) · §9 160행 PowerShell hang 이유(codex-review.md:31 「MUST — call codex with the Bash tool」; "Bash 로 호출" 은 남김) · §11 238행은 **되살림**(독립 감사: §11 이 skill 없이 돌리라는 명령의 사용 안내라 로드 등급 하강) · §13 263행 근거 괄호 · §13 264행 "index.md·log.md 동기화"(wiki skill ingest 9단계) · §13 265행 "주입 경로는 전역 피드백 파일과 MEMORY.md 인덱스" 재서술(§12 250·252 — "(after the shared-wiki entry is done)" 는 남김). **남기는 것(재확인에서 FAIL)**: 49행 실행 산출물 관찰, 50행 거짓 양성 한 줄 규칙, 78행 simplify 항목, 134행 괄호(targeted 검증 한정어·포인터), 162행 push 전 재리뷰 없음, 182행 `/e merge` done 전진, 217행 intent 닫기, 266행.
- [x] 검사 (2026-11-07) — `check-dedupe.js --mutate` PASS; code-reviewer 지적으로 덮임 검사를 "줄마다 지워진 단어열 = 그 줄 행들의 단어열(정확 일치)" 로 바꾸고 부정어·숫자 삭제 변이(72건) 추가, 생존 0 — 대응표 `claude-md-dedupe-log.md` `# Rule manifest`(열: CLAUDE.md 옛 줄 · 지운 절 원문 · 남는 자리 file:line «인용» · 남긴 포인터 · 분류 intra/detail/reason · 로드 등급) · 검사 스크립트 `plans/2026-11-07-claude-md-dedupe/check-dedupe.js`: `git diff -U0 main -- CLAUDE.md` 의 지워진 글자가 모두 대응표 행에 덮이는지(미덮임 → FAIL), 각 행의 «인용» 이 남는 자리 파일에 그대로 있는지 · keep 목록 `keep.json`(Constraints 4·5 의 고정 문구·항상-켜짐 문장을 원문 그대로)이 새 CLAUDE.md 에 있는지 · 변이 검사 `--mutate`: 대응표 행을 하나씩 빼면 덮임 검사가 FAIL 인지, keep 목록 항목을 새 CLAUDE.md 에서 하나씩 지우면 FAIL 인지(인용 삭제 변이는 같은 검사를 되풀이할 뿐이라 쓰지 않는다 — plan-reviewer N1) · 대응표의 남는 자리는 줄 번호가 아니라 «인용» 으로 적는다(N2) · 결과를 log 에
- [x] 독립 감사 (2026-11-07) — OK 15 · WEAKER 1(d5)·LOAD-DOWNGRADE 1(d10) → 둘 되살림 — 옛/새 CLAUDE.md 와 남는 자리 파일만 받은 subagent 가 절마다 OK/MISSING/WEAKER/LOAD-DOWNGRADE 판정(세기 = 같은 범위·같은 양상(must/never/ask)·같은 한정어·로드 등급 ≥) → WEAKER/DOWNGRADE 는 되살림
- [x] 문서 (2026-11-07) — README 278~291 에 지운 용어 없음; 지운 줄의 § 인용은 포인터로 남음 — `README.md` CLAUDE.md 절 요약(278~291행, 특히 §5 표준 순서·§8 ff-merge/정리 문구)과 바뀐 줄의 대조 · `rg -n 'CLAUDE.md §' skills agents scripts` + `/root/.claude/wiki/docs` 로 깨진 인용 확인(wiki 쪽은 `# Deferred`)
- [x] 검증 (2026-11-07) — code-reviewer REQUEST CHANGES(검사 스크립트의 부정어 누락 Major, 확인 전 커밋 Major) → 스크립트 수정·커밋 해제 — `node scripts/frontmatter-lint.js` · `bash skills/improve/improve.sh` 점검 3 의 `OK agent` 4줄(plan-reviewer·researcher·code-reviewer·architecture-reviewer, 변경 전과 같음) · `bash scripts/verify.sh changed` · code-reviewer(대응표의 keep/delete 판정과 감사 결과를 항목별로)
- [x] 사용자 word-diff 확인(커밋마다: 3줄 요약 + 대응표 + 절별 word-diff) → 커밋 2개 (2026-11-08) — 두 커밋 승인(AskUserQuestion), 패치에서 재커밋, 트리 일치
- [x] PR → CI → 머지(`/e merge`) (2026-11-08) — PR #261

# Acceptance
1. 대응표가 `git diff -U0` 의 지워진 글자를 전부 덮고(검사 스크립트 PASS), 각 «인용» 이 남는 자리에 그대로 있으며, 변이 검사에서 모든 행이 FAIL 로 잡힌다 — `node plans/…/check-dedupe.js [--mutate]` — PASS / 변이 전부 FAIL
2. 독립 감사의 판정이 전 행 OK(또는 되살린 뒤 OK) — subagent 보고 — WEAKER·LOAD-DOWNGRADE·MISSING 0
3. 항상-켜짐 규칙(Constraints 1·4·5)이 그대로 있다 — code-reviewer 가 keep 행과 고정 문구 목록을 대조 — 이의 0
4. `improve.sh` 점검 3 `OK agent` 4줄 · frontmatter-lint · `verify.sh changed` 통과 · CI `lint` success
5. 사용자가 커밋마다 word-diff 를 확인했다(AskUserQuestion 기록)
6. README 의 CLAUDE.md 절 요약이 새 본문과 맞다 — 리뷰 대조
7. (보고 지표, 게이트 아님) 줄어든 바이트·글자 수 — `wc -c`/`wc -m` 전후 — 재확인 뒤 남은 후보로는 수천 자 수준이 예상된다(plan-reviewer N3; ops-doc-slimming 의 11% 상한과 같은 방향)

# Decisions
- 관련 decision 조회: 공용 wiki `ops-doc-slimming` — **따른다**: "bytes 목표를 hard gate 로 걸지 말 것"(Acceptance 7 은 지표만), "2026-10-21 실행: §8 절차 이관을 계획 리뷰가 막았다"(이관 없음 — 아래 기각), 조건부 로드 skill 이 참조하는 정본 스펙(§10 형식)은 옮기지 않음, 번역 단위의 교훈(부분 인용의 거짓 PASS → 변이 검사·독립 감사). `lesson-skipped-axis-blocks-merge`(CI 경로).
- **항상-켜짐 판정은 닫힌 검사 (a)~(d)** (Constraints 1) — "절차 vs 규칙" 같은 요지 판정 대신 문장이 하는 일로 가른다(plan-reviewer S2). 세기의 정의: 같은 범위(누가·언제)·같은 양상(must/never/ask)·같은 한정어·로드 등급 ≥ 원문. 판정자는 저자가 아니라 독립 감사 subagent, 다툼 행은 code-reviewer.
- **기각: 출처 방향 전환(skill 을 출처로, CLAUDE.md 는 포인터)** — 2026-10-21 plan 리뷰가 §8(a)·ff-merge 에서 같은 안을 막았고(skill 을 안 부른 세션·Codex·subagent 가 확인 없는 삭제의 조건을 잃는다) 새 근거가 없다. §3-6 보고 선택지(리뷰·`/c`·Codex 세션도 보고한다)·§11 239-240(모든 세션의 Report 에 걸리는 의무)·§5 81행도 같은 이유로 남긴다.
- **기각: 전부 CLAUDE.md 에 두기(지금 상태)** — 크기 문제의 원인. **기각: byte 하드 게이트(≥8,000자)** — ops-doc-slimming 의 결정에 어긋나고(삭제 압력), 항상-켜짐 제외 뒤 남는 후보는 약 3,000~5,000자(⚠️ plan-reviewer 추정)라 달성 자체가 의심스럽다.
- **검사 방법**: 대응표는 후보 목록이 아니라 `git diff -U0` 의 지워진 글자에서 만든다(목록 밖 삭제·긴 불릿 속 한정어 탈락을 잡기 위해 — 10-21 교훈). 검사 스크립트는 번역 단위의 `check-translation.js`/`mut-translation.js` 를 참고하되 1:1 번역용이라 새로 쓴다(⚠️ 재사용 가능성은 구현 때 판단). 기각: `rg` 로 "CLAUDE.md 에 없고 남는 자리에 있음" 확인 — 삭제 뒤 부재는 자명하고 존재는 변경 전부터 참이라 아무것도 잡지 못한다.
- 커밋 단위: 1) `docs(claude-md): keep one copy of each rule CLAUDE.md states twice` 2) `docs(claude-md): drop skill-internal procedure details CLAUDE.md restates` — 2 가 더 위험하므로 뒤에.
- 사용자 확인 형식(FEEDBACK.md "확인은 3줄 + 예 하나"): 커밋마다 요약 3줄 + 대응표 + 절별 word-diff + 다툼 행 목록. 독립 감사는 사용자 확인 **전**에 끝낸다.

# Blockers
