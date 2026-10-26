---
title: translate-claude-md — CLAUDE.md 를 규칙 손실 없이 영어로 옮긴다
status: done
started: 2026-10-26
updated: 2026-10-26
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
CLAUDE.md 전체를 영어로 옮긴다. 규칙은 하나도 빠지거나 약해지거나 강해지지 않고, 다른 파일이 인용하는 라벨·형식은 같은 머지에서 그 파일들도 맞춘다.
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md) — translate-repo 단위의 첫 파일
- Constraints(델타): 따옴표·코드 안의 한국어 문구(출력 형식·예시·라벨)도 영어로 옮긴다(사용자, 2026-10-26 "전부 영어로"). 그래서 같은 문구·형식을 쓰는 파일(skills·agents·README·열린 intent.md)도 이 머지에서 그 문구만 맞춘다. 그 파일들의 나머지는 번역하지 않는다(파일별 번역은 다음 단위).
- intent.md 의 상태 토큰(`(미착수)`·`(열림)`·`(해소)`·`(이월 → …)`·`폐기`)과 `/wiki ingest` 제안 형식도 위 결정에 들어간다(메인 추론, 사용자 계획 승인 2026-10-26).
- Out of scope(델타): CLAUDE.md 밖 파일의 번역 · 규칙 내용 변경(번역 중 찾은 문제는 plan log Deferred) · hook·script 의 사용자 출력 문구(translate-hooks — 예: `pre-commit-check` 의 `"회사 repo"` 예시) · 공용 wiki 의 인용(main 세션, [post-merge]) · `skills/wt/SKILL.md:114` "조건5"(wt 번역 단위).
- Split: bundle → plans/2026-10-21-ops-docs-rework/intent.md (이 단위는 더 나누지 않는다 — 번역과 인용 맞추기를 따로 머지하면 그 사이 인용이 끊긴다)

# Tasks
- [x] 계획 승인 (2026-10-26) — 사용자 "이대로 진행", intent 상태 토큰도 영어로
- [x] 계획 리뷰 (2026-10-26) — plan-reviewer CONDITIONAL(Codex 미가용), 처분은 plan log. 사용자 결정 3건: 역방향 인용은 영어 + 대응표로 넘김, 다른 열린 intent 2개도 토큰만 바꿈, 핵심 문구 대응표 승인
- [x] 대조 기준 고정 (2026-10-26) — `plans/2026-10-26-translate-claude-md/manifest-add.md`(0.lp1~5), `plans/2026-10-26-translate-claude-md/pointers.md`(33곳 + 역방향 대응표 + [post-merge] wiki), `plans/2026-10-26-translate-claude-md/phrases-en.txt`(26개, 사용자 승인)
- [x] 번역 (2026-10-26) — `CLAUDE.md` 265줄 → 265줄(줄 구조 유지)
- [x] 새 위치 채우기 (2026-10-26) — `plans/2026-10-26-translate-claude-md/locations-en.txt`
- [x] 가리키는 곳 맞추기 (2026-10-26) — `skills/c/SKILL.md`·`skills/dlc/SKILL.md`·`skills/e/SKILL.md`·`skills/wiki/SKILL.md`·`agents/plan-reviewer.md`·`agents/architecture-reviewer.md`·`README.md`, 열린 intent 토큰 `plans/2026-10-21-ops-docs-rework/intent.md`·`plans/2026-09-29-repo-context-kit/intent.md`·`plans/2026-09-25-repo-audit-followups/intent.md`(목록은 pointers.md 가 정본. improve·jira-task·code-reviewer 는 따옴표 인용이 없어 그대로)
- [x] 기계 대조 (2026-10-26) — Acceptance 1~4·6 PASS(조항 316·삭제 6, 핵심 문구 97, 한글 0, 가리키는 곳 33 양방향)
- [x] 독립 대조 (2026-10-26) — subagent 3개, OK 314 · CHANGED 2(1.11·3.6.4, 반영), 처분은 plan log
- [x] code-reviewer, fix loop 1회 (2026-10-26) — APPROVE(Critical·Major 0). 반영: §0 문장 2개(0.lp6·0.lp7), 문구 6곳, 놓친 인용 2곳(`skills/e/SKILL.md`·`scripts/plan-match.js`). 처분은 plan log
- [x] simplify 점검 (2026-10-26) — 생략: 코드 변경은 `scripts/plan-match.js` 주석 1줄뿐(§5 는 trivial 이 아닌 코드 변경에 필수)
- [x] 사용자 diff 확인 (2026-10-26) — 사용자 "커밋": §0 새 문장(0.lp6·0.lp7)·Acceptance 5·7·10 변경 포함
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-26) — 격리 runner: `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 미설치, .ps1 변경 없음), check-en PASS(조항 318 = 311 + 보충 7, 핵심 문구 97, 한글 0, 가리키는 곳 35·공유 형식), plan-lint 통과. 크기 48,746B → 50,762B(영어는 바이트가 늘고 토큰은 미측정 — 측정은 headless 호출 비용이 들어 하지 않았다). 판정 DONE
- [x] 기록 커밋(plan·log·manifest-add·pointers·locations·intent), commit-check (2026-10-26) — 커밋 2개(번역·기록), commit-check 이상 없음
- [x] 머지 (`/e merge`) (2026-10-26) — PR #243
- [ ] [post-merge] 새 main 세션에서 언어 관찰 — 답이 한국어인지, 새로 만든 plan 이 한국어인지. 영어로 나오면 revert 를 제안한다
- [ ] [post-merge] `scripts/bootstrap/sync_codex_agents.py` 재실행 — agents/*.md 가 바뀌어 Codex agent TOML 갱신
- [ ] [post-merge] main 세션에서 공용 wiki 갱신 — pointers.md 의 [post-merge] 절(dlc-details·wiki-inbox·plan-handoff, 역사 기록 페이지는 그대로)·ops-doc-slimming 기록·log. 언어 관찰 뒤에 한다(revert 가 wiki 를 되돌리지 못한다)

# Acceptance
1. 규칙 손실 0 — slim-rules-ko manifest 의 삭제 아닌 조항 311개 + manifest-add 조항마다 locations-en.txt 에 새 CLAUDE.md(또는 다른 파일)의 영어 인용이 있고 글자 그대로 찾힌다 — scratch `check-en.js` — missing·not found 0
2. 식별자·명령은 그대로 — slim-rules-ko 핵심 문구 97개 중 한국어가 없는 것은 새 CLAUDE.md 에 글자 그대로, 한국어가 든 것은 고정한 영어 대응 문구가 새 CLAUDE.md 에 있다 — `check-en.js` — 전부 찾음
3. 한국어 없음 — `node -e` 로 새 CLAUDE.md 의 한글 글자 수 — 0
4. 표지 — `## 0.`~`## 13.` 번호와 순서, §3 번호 항목 1~6(Setup·Explore·Plan·Implement·Verify·Report), §8 (a)·(b), 굵은 agent 이름(`skills/improve/improve.sh` 3번 점검), `@RTK.md` 끝줄 + pointers.md 의 가리키는 곳마다 그 인용이 새 CLAUDE.md 에 글자 그대로 있음 — `check-en.js` — 누락 0
5. 독립 대조 — 절 범위로 나눈 새 subagent 3개가 manifest 조항 id 마다 OK/MISSING/WEAKER/STRONGER/CHANGED/LOCATION-WRONG 를 판정하고 새로 더해진 규칙·예시를 찾는다(§0 언어 정책과 §12 트리거 예시 포함) — OK 아닌 판정마다 반영하거나 근거로 반박해 plan log 에 기록 — 미처분 0
6. 공유 형식 일치 — `/wiki ingest` 제안 형식이 CLAUDE.md·`skills/dlc`·`skills/wiki`·README 에서 같은 문자열, intent 상태 토큰이 CLAUDE.md·`skills/e`·`skills/dlc`·agents·열린 intent.md 에서 같은 문자열 — `check-en.js` — 불일치 0
7. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
8. 크기 — 바이트(`wc -c`)와 입력 토큰(scratch `tok/measure.sh` 방식) 전후를 Report 에 — 보조, 통과 조건 아님
9. [post-merge] 공용 wiki 의 인용·기록 갱신 — pointers.md 의 [post-merge] 절 항목마다 반영
10. [post-merge] 언어 — 머지 뒤 새 main 세션의 답과 새로 만든 plan 이 한국어 — 관찰 — 영어면 revert 제안

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다: 규칙 손실 0 이 hard gate, 크기는 보조. 같은 페이지의 2026-09-28 "영어 번역 기각 권고"는 사용자 결정(2026-10-20)으로 뒤집혔다(intent).
- 대조 방법: 같은 언어 안의 줄 대조가 안 되므로 (1) slim-rules-ko manifest 의 조항 id 를 그대로 쓰고 새 위치만 영어 인용으로 다시 채운다(locations-en.txt), (2) 조항 단위 독립 대조는 두 언어를 다 보는 새 subagent 가 한다, (3) 사용자가 diff 를 확인한다. 기각: 번역본을 다시 한국어로 옮겨 줄 대조(왕복 번역은 표현 차이만 잔뜩 만들고 손실 판정은 결국 사람이 한다).
- 문체: 명령형 영어, 한국어 원문의 구조(절·불릿·굵게 표시한 핵심 구)를 그대로 두고 한 줄씩 옮긴다. 줄이기는 하지 않는다(줄이기는 CLAUDE.md 에서 끝남 — intent). 번역하며 새 규칙·예외를 더하지 않는다. 기각: 의역으로 재구성(조항 대조가 불가능해진다).
- 따옴표 안 한국어(사용자, 2026-10-26): 전부 영어로. 예시 문구는 같은 뜻의 영어 예시로("다이얼 → 파라미터" 처럼 표현 규칙을 보이는 예시는 영어에서 같은 대비가 되는 예시로), 사용자 입력 예시("기억해 / 규칙으로 / 다음부턴 이렇게")는 영어로 옮기되 뜻으로 알아본다는 것은 그대로 둔다. 기각(추천했던 안): 따옴표 안 문구는 한국어로 두기 — 사용자가 택하지 않았다.
- 표지: 절 번호·§3 항목 번호와 순서·§8 (a)(b)·§10 의 번호 1)2)3)·굵은 agent 이름은 그대로. 절 제목과 불릿 라벨은 옮기고, 가리키는 파일의 인용을 같은 머지에서 그 영어로 바꾼다(intent Constraints). 가리키는 쪽이 번역 전 한국어 파일이면 한국어 문장 안에 영어 인용이 들어간다 — 인용이라 "한 파일에 언어를 섞지 않는다"의 대상이 아니다(이미 `Commit or push only when the user asks.` 같은 영어 인용이 있다) ⚠️ 판단.
- 커밋 단위: 1개 — `docs(claude-md): translate CLAUDE.md into English` (CLAUDE.md + 가리키는 곳). 번역과 인용 맞추기를 나누면 그 사이 인용이 끊긴다. plan·log·대조 파일은 마지막 기록 커밋.
- 테스트: 규칙 문서라 새 테스트 없음(§7 예외 — 수동 검증은 Acceptance 1~6). worktree 세션과 subagent 는 main checkout 의 CLAUDE.md 를 읽어 새 문구의 동작은 머지 전 관찰할 수 없다 — 사용자 diff 확인이 행동 검증이다.
- 가리키는 곳 범위: 따옴표·backtick 안 인용과 공유 형식 문자열만 이 머지에서 바꾼다. `§0 언어 정책`·`§10 대응표` 처럼 절 번호와 함께 쓴 따옴표 없는 서술 참조는 그 파일의 번역 단위가 옮긴다(절 번호로 찾을 수 있다). 기각: 서술 참조까지 영어로(번역 전 한국어 문장 수십 곳에 영어 단어가 섞이고 범위가 skill 번역으로 커진다).
- 다른 열린 intent 의 토큰 교체(사용자 승인 2026-10-26): §10 소유권(자기 plan 줄·자기 Open question 만) 의 예외 — 토큰만 바꾸고 내용은 그대로. 닫힌 intent 는 토큰을 읽는 곳이 없어 그대로 둔다(scripts 는 intent 를 읽지 않는다).
- 역방향 인용(사용자, 2026-10-26): CLAUDE.md 가 가리키는 한국어 skill 제목은 영어로 옮기고, 대응표를 intent Constraints 와 pointers.md 로 넘겨 그 skill 의 번역 단위가 제목을 맞춘다. 기각: 한국어 따옴표로 남기기(한 파일 언어 섞기·한글 0 검사 예외), skill 제목도 이번에(범위 확대).
- 순서: `read-points`(진행 중, `agents/code-reviewer.md`·`skills/dlc/SKILL.md` 를 고친다)는 intent Constraints 대로 이 단위보다 먼저 머지하거나 이 단위 위로 rebase 한다. 이 단위가 먼저 머지되면 read-points 가 rebase 할 때 토큰·인용 줄이 충돌할 수 있다.
- Acceptance 변경(계획 리뷰 반영, 사용자 승인 2026-10-26): 5 "새 subagent 가 찾은 빠짐·약화·강화·뜻 변화마다…" → "절 범위로 나눈 subagent 3개가 조항 id 마다 판정…" · 7 에서 "improve.sh 3번 점검 통과" 삭제(매치 0 이어도 통과해 증거가 아니다 — 굵은 agent 이름은 4 가 지킨다) · 10 추가(머지 뒤 언어 관찰).
- ⚠️ (구현) [리뷰 미경유] 사용자 답에 나오는 인용 라벨·템플릿은 한국어, plan 파일 표시는 고정 문자열 — 새 문장(0.lp6·0.lp7) 대신 머지 뒤 관찰만 하는 안도 있었다 — 번역이 만든 쏠림을 문장 하나로 막는 쪽을 택했다(독립 대조 3.6.4·code-reviewer) — `CLAUDE.md` §0 언어 정책 불릿
- Codex 미가용(`codex: command not found`) — reviewer 는 Claude 단독.
- architecture-reviewer: 부르지 않는다 — 문서만 바뀐다.
- 롤백: `git revert -m 1 <merge sha>` 후 각 머신이 main 을 pull 하고 새 세션을 연다(Codex 는 심링크라 바로 따라온다). revert 가 되돌리지 못하는 것: 공용 wiki 편집(별도 repo — 언어 관찰 뒤에 한다), Codex agent TOML(sync 재실행), 머지 뒤 영어 토큰으로 새로 쓴 intent 줄(손으로 되돌린다).

# Blockers
