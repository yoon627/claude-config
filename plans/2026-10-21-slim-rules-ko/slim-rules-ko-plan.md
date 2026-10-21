---
title: slim-rules-ko — CLAUDE.md 를 규칙 손실 없이 줄이고, 근거 규칙 3개 추가와 모순 정리
status: in_progress
started: 2026-10-21
updated: 2026-10-21
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
CLAUDE.md 를 규칙 하나 빠짐없이 짧게 고쳐 쓰고(한국어), 추천·번복의 근거 규칙 2개와 dlc Tasks 규칙 1개를 더하고, 문서끼리 어긋난 곳을 바로잡는다.
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md)
- Constraints(델타): 이 plan 은 CLAUDE.md 만 줄인다. skills·README 는 규칙 3개·모순 수정에 필요한 줄만 고친다. Codex 도 CLAUDE.md 를 AGENTS.md 로 읽고 Codex 에 연결된 skill 은 c·dlc·e·improve·jira-worklog·wiki·wt 뿐이라(`scripts/bootstrap/setup.sh`), 그 밖의 skill 을 가리키는 포인터를 새로 더하지 않는다.
- Out of scope(델타): skills·agents 줄이기(묶음의 다음 plan) · 영어 번역과 언어 정책(묶음의 language-policy·translate-*) · MEMORY.md·memory.
- Split: bundle → plans/2026-10-21-ops-docs-rework/intent.md

# Tasks
- [x] 범위·기준 확인 (2026-10-21) — 사용자: CLAUDE.md 먼저, 규칙 보존 기준(줄 수 목표 없음), 이력·실측 메모는 wiki 로
- [x] 계획 리뷰 (2026-10-21) — plan-reviewer CONDITIONAL, 묶음 리뷰 CONDITIONAL, 처분은 plan log
- [x] 규칙 목록 (2026-10-21) — `plans/2026-10-21-slim-rules-ko/manifest.md`: 조항 단위, 등급, 표지, 핵심 문구 76개(지금 CLAUDE.md 에 전부 매치)
- [x] 단위 1 — 규칙 3개 추가와 모순 정리 (2026-10-21): `CLAUDE.md`(§1·§3-1·§3-5·§5·§10·§13), `skills/dlc/SKILL.md`(파이프라인 3단계 Tasks 줄, "마무리 1회 원칙"), `skills/e/SKILL.md`("§3-6 1회 원칙" 2곳), `README.md`(CLAUDE.md 절 요약 중 §1, agents 표의 code-reviewer 호출 조건), `agents/code-reviewer.md`(호출 조건 "모든 흐름" 2곳 — 모순 8 의 사본)
- [x] 단위 1 리뷰 — code-reviewer(단위 1 diff + manifest 의 등급 칸 검토), fix loop (2026-10-21) — REQUEST CHANGES(manifest Major 3, diff Minor), 처분은 plan log. 반영분은 재리뷰 없이 사용자 문구 확인으로 갈음
- [x] 단위 1 확인·커밋 — 사용자에게 바뀐 문구 확인받고 커밋 (2026-10-21) — 사용자 "커밋"
- [x] 단위 2 — §3-1·§8 을 뺀 절 줄이기 (2026-10-21) — 268줄·50,737B → 255줄·48,914B: `CLAUDE.md`. 이력 표시를 지우고 wiki 에 없는 것만 plan log Deferred 에. 줄인 뒤 manifest 새 위치(`§N «인용»`) 채우기
- [x] 단위 3 — §3-1·§8 줄이기(이관 없이 표현만) (2026-10-21) — → 259줄·47,881B(§8 의 긴 한 줄 불릿을 하위 불릿으로 나눠 줄 수는 늘었다): `CLAUDE.md`, manifest 새 위치 채우기
- [x] 대조 (2026-10-21) — 독립 대조 missing·weakened·misplaced 0, 모순 2 → 11·12 — manifest 새 위치 검사(`plans/2026-10-21-slim-rules-ko/locations.txt`, 317개 전부 찾음 2026-10-21), 핵심 문구 97개(전부 매치), 표지(절 제목 14개·§3 항목 1~6 순서·§8 (a)(b) 확인), 표지(절 제목·§3 항목 순서·§8 (a)(b)·인용), 새 subagent 에 새 CLAUDE.md 와 인라인 조항 목록만 주고 빠지거나 약해진 규칙 찾기
- [x] 단위 2·3 리뷰 (2026-10-21) — NEEDS DISCUSSION(Critical·Major 0, Minor 5·Nit 8 반영, 처분은 plan log) — code-reviewer(`git diff --word-diff <단위 1>..HEAD -- CLAUDE.md` 를 manifest 와 조항 단위로 대조), fix loop
- [x] 단위 2·3 확인·커밋 — 사용자에게 지운 조항과 등급·위치가 바뀐 조항만 보여 확인받고 단위별 커밋 (2026-10-21) — 사용자 "커밋", 모순 11·12 는 단위 1 의 fixup
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-21) — 격리 runner: 위치 317·문구 97·표지·plan-lint 통과, `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 미설치, 문서 변경과 무관). 판정 DONE
- [x] simplify 점검 (2026-10-21) — 생략: 문서만 바뀌어 코드 simplify 대상이 없다(§5 는 코드 변경에 필수)
- [x] 선행 plan 정리 (2026-10-21) — `plans/2026-10-18-plan-format/plan-format-plan.md` 에 `intent:` 1줄과 끝난 [post-merge] wiki Task 체크(0c6f7e2), `plans/2026-10-20-remove-conclusion-block/remove-conclusion-block-plan.md` 에 `intent:` 1줄과 [post-merge] Task 체크(wiki 5b0950a, Acceptance 5 관찰)
- [x] 기록 커밋(plan·log·manifest·intent·선행 plan), commit-check (2026-10-21)
- [ ] 머지 (`/e merge`)
- [ ] [post-merge] main 세션에서 공용 wiki 갱신 — plan log Deferred 의 이력 메모(있을 때)

# Acceptance
1. 규칙 손실 0 — manifest 의 인라인·세부·신규 조항마다 새 위치 `§N «인용»`(또는 `경로 «인용»`)이 있고 그 인용이 그 파일에서 글자 그대로 찾힌다, CLAUDE.md 를 다시 가리키는 파일은 새 위치로 쓰지 않는다 — scratch 검사 스크립트로 전 조항 확인 + code-reviewer 가 단위 2·3 diff 를 조항 단위로 대조 — 새 위치 없는 조항 0
2. 안전·트리거 문구가 남는다 — manifest 의 핵심 문구 97개(단위 2 전 고정)를 새 CLAUDE.md 에서 찾음 — 97개 전부
3. 다른 파일이 가리키는 표지가 남는다 — `## 0.`~`## 13.` 제목, §3 번호 항목 1~6 의 제목과 순서, §8 의 (a)·(b), manifest "표지" 절의 인용(글자 그대로 2개, 불릿 라벨 4개), `rg -n '1회 원칙' skills agents CLAUDE.md` 0건 — 누락 0
4. 독립 대조 — 새 subagent 에 새 CLAUDE.md 와 manifest 의 인라인 조항 목록만 주고 빠지거나 약해진 조항을 찾게 함 — 지적마다 반영하거나 근거로 반박해 plan log 에 기록
5. 규칙 3개 — CLAUDE.md §1 에 추천 근거 문장과 번복 근거 문장(사용자 결정을 따르는 것과 구분), `skills/dlc/SKILL.md` 파이프라인 3단계에 Tasks 문장(건너뛴 단계를 닫는 방법 포함) — diff 대조
6. 모순 — `# Decisions` 의 12개 각각이 고쳐졌거나 근거와 함께 그대로다 — 12개 모두
7. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)
8. 크기 — `wc -lc CLAUDE.md` 전(268줄·49,942B)과 후를 Report 에 적는다 — 보조 목표, 통과 조건 아님
9. [post-merge] 공용 wiki 갱신 — plan log Deferred 의 각 항목이 wiki 에 반영됨(항목이 없으면 해당 없음)

# Decisions
- wiki 결정 [[ops-doc-slimming]] → 따른다: 규칙 손실 0 이 hard gate, 줄 수·바이트는 보조(사용자 확인 2026-10-21), 안전·트리거 규칙은 CLAUDE.md 에 남긴다, 방향 역전 금지. 같은 페이지의 2026-09-28 "영어로 옮기기 기각 권고"는 사용자 결정(2026-10-20)으로 뒤집혔다 — 이 plan 범위 밖. [[lesson-verify-scaffold-purpose-before-removal]] → 따른다: 지우기 전에 그 조항이 다른 곳에 있는지 확인한다(manifest), 적용 시점 날짜는 남긴다.
- 범위: CLAUDE.md 만(사용자, 2026-10-21). 근거: 7월 압축도 파일별 PR(#89~92), 파일마다 manifest 대조가 필요하다. 기각: CLAUDE.md·skills·agents 한 번에(확인할 diff 가 너무 크다).
- 기준: 줄 수 목표 없음(사용자, 2026-10-21). 메인은 처음에 "약 200줄"을 말했는데 ops-doc-slimming 을 확인하지 않은 값이었다 ⚠️. 기각: 200줄 목표(규칙을 skill 로만 옮기게 돼 로드 등급이 떨어진다).
- 이력 = 괄호 안의 근거 표시(버전 번호·측정값·"재현"·"선례"·"실측")뿐이다. 지우고, wiki·README 에 없는 것만 머지 뒤 main 세션에서 wiki 에 적는다(사용자, 2026-10-21). 규칙 문장 속의 "재현"(§3-5·§7·§11·§13 의 재현 테스트·재현 조건)과 적용 시점 날짜("2026-10-18 이전 형식")는 규칙이라 남긴다. worktree 세션에서는 공용 wiki 를 쓸 수 없다(§3-1). 기각: 그대로 두기.
- 옮기지 않는 절: §8 과 §10 은 표현만 줄인다. `skills/dlc/SKILL.md` 16단계가 "조건과 금지는 CLAUDE.md §8 단일 소스" 라고 가리키고, 커밋 게이트(`git add -A` 금지·staged 확인·커밋하지 않는 경우·`--no-verify` 금지·미검증 커밋 금지·하네스 기본값 대체·`git rebase --abort`·plan 없는 small 의 `/e merge` 전 plan)와 §8(a)(b) 정리 조건은 CLAUDE.md 에만 있다(plan-reviewer S2·S3, 2026-10-21 grep 확인). (a) 는 `/e` 밖에서도(dlc Report·사용자가 "머지했다"고 할 때) 확인 없는 삭제를 허락하는 안전 게이트다. §5 의 Workflow effort 표도 Workflow 를 쓸 때 로드되는 skill 이 없어 그대로 둔다. 다른 파일로 옮기는 것은 이미 그 파일에 있는 메커니즘 설명뿐이다(manifest 의 "세부" 줄, 인용으로 확인). 기각: §8 절차를 `/e`·dlc 로 옮기고 한 줄만 남기기(방향 역전 — 그 skill 을 안 부른 세션이 규칙을 잃는다).
- 포인터 형식: 다른 문서를 가리킬 때는 절대경로나 skill 이름과 "언제 읽는지" 를 함께 적는다([[ops-doc-slimming]] 이관 형식). `[[…]]` 링크만 남기는 것은 근거 표시일 때만.
- 절 번호·§3 항목 번호와 순서·§8 (a)(b) 표기·§10 의 불릿 라벨(시작·진행 중 동기화·턴 종료·완료)·인용된 구절은 그대로 둔다(intent Constraints 의 표지 고정).
- 모순 처리(`slim-input.md` 의 7곳 + 계획 리뷰가 찾은 2곳, 2026-10-21 현재 파일로 확인):
  1. §5 "simplify 점검은 모든 코드 변경에 필수" + 같은 문장의 "생략 사유는 Report 에" vs `skills/dlc` trivial 행(simplify 없음) — 고친다: "trivial 이 아닌 코드 변경엔 필수, 못 했으면(미해결 blocker 등) 사유를 Report 에". 단위 1.
  2. §1 확인 대상의 "머지" vs §8 로컬 `--ff-only` 반영·(a) 무확인 정리 — 고친다: §1 목록의 "머지" 는 그대로 두고 "예외: trivial·small 의 로컬 `--ff-only` 반영과 그 뒤 §8(a) 정리는 §8 대로 묻지 않는다" 를 목록 밖에 더한다. 단위 1. `skills/c` 73·77행의 "머지" 멈춤은 이어받은 흐름의 더 엄격한 규칙이라 그대로. 기각(code-reviewer C): "PR 머지" 로 바꾸기 — 로컬 non-ff 머지·GitHub 밖 머지가 확인 목록에서 빠지고, (a) 정리를 "데이터를 지우지 않는" 괄호에 넣게 된다(`git worktree remove` 는 ignored 파일을 지운다). 이 방식이면 공용 wiki risk-based-approval 의 "머지" 도 맞아 고칠 필요가 없다.
  3. §13 "§11 wiki ingest '제안 아님'과 동일 게이트" — 인용이 뒤집혀 있다(ced08ec 부터, §11 은 "제안(자동 아님)"). 고친다. 단위 1.
  4. §3-1 "auto 모드에서는 ask 가 생략" vs `scripts/guard-push-delete.js` "권한 모드와 무관하게 ask" — 모순 아님: `scripts/guard-worktree-edit.js` 가 auto 모드에서 ask 를 걸지 않도록 만들어졌고(98~102행, 7c977c8), guard-push-delete 는 모드와 무관하게 ask 를 건다. §3-1 문장이 하네스 동작처럼 읽혀 주어를 그 hook 으로 고친다. 단위 1.
  5. §10 "빈 채로라도 헤더 유지" 가 Acceptance 를 포함 vs `scripts/plan-lint.js` 의 새 형식 필수 섹션은 Goal·Tasks·Decisions·Blockers — 규칙 완화다(문서가 lint 보다 엄격했다): 그 넷은 헤더 유지, Acceptance 는 비trivial 에 필수로 맞춘다. `/e` M1(3) 은 섹션이 없으면 이미 통과시킨다. 단위 1.
  6. §8 (a) `--merged <default>`(로컬 포함) vs `skills/wt/SKILL.md` 114행 `--merged origin/<default>` — 모순 아님: wt 는 원격 삭제 경고용이고 같은 줄이 "로컬 default 에만 머지됨" 을 따로 구분한다. 변경 없음.
  7. §9 "공유 채널" 줄(§10 서두와 중복), §10 "리뷰는 dlc 중간 단계…" 단락(§5·§9 와 중복) — 중복 정리라 압축이다: 단위 2 에서 중복 줄을 지우고, 다른 곳에 없는 "push 직전 별도 codex 리뷰 없음·로컬 다관점 점검은 `/code-review`" 는 §9 로 옮긴다.
  8. §5 "code-reviewer — 코드 변경 있는 모든 흐름" vs `skills/dlc` trivial 행(리뷰 없음) — 고친다: "trivial 이 아닌 코드 변경" 과 trivial 의 뜻(dlc 규모표의 오타·주석·포맷·import·로그 1줄 — §7 예외의 "1줄 수정" 보다 좁다)을 §5 에 적는다. 같은 문구가 `agents/code-reviewer.md` description·호출 조건과 README agents 표에도 있어 함께 고친다. 단위 1.
  9. §3-5 "비trivial 은 plan `# Acceptance` 를 대조한 뒤에만 완료" vs `skills/dlc` 의 plan 없이 가는 small — 고친다: 문장은 그대로 두고 "(plan 없이 가는 small 은 검증 결과로)" 만 더한다. 단위 1. 기각(code-reviewer B): "plan 이 있는 비trivial 작업은" — plan 을 빠뜨린 medium 이상이 규칙 밖으로 빠진다.
  10. §8 "repo 로컬 `core.hooksPath` 가 있으면 설치해도 무효" vs `scripts/install-hooks.sh` — 설치 스크립트는 `core.hooksPath` 가 다른 디렉토리를 가리키면 설치를 거부한다(exit 1, "Not installing"). 고친다. 단위 1(code-reviewer M6).
  11. §3-6 의 마무리 선택지가 모든 코드 작업에 `/e merge`(push·PR)를 내놓는다 vs §8 의 trivial·small 로컬 ff-merge — 고친다: "(trivial·small 은 §8 의 로컬 ff-merge)". 원래 문구부터 있던 것을 독립 대조가 찾았다. 동작 변경이라 단위 1 의 fixup 으로.
  12. §8 "미커밋 plan·log 변경은 삭제 전 커밋·push 로 보존" vs "push 는 요청 시만"·로컬 ff 흐름 — 고친다: "커밋으로 보존(push 는 요청 시만)"(미머지 브랜치는 `git branch -d` 가 지우지 않아 커밋이면 보존된다). 단위 1 의 fixup 으로.
  - 끊긴 참조: `skills/e` 46행 "§3-6 1회 원칙"(머지 모드의 done 확인 생략)과 `skills/dlc` 16단계 "마무리 1회 원칙" 은 "중복 질문 금지(§3-6)" 로, `skills/e` 82행(`/e` 호출 = worklog 등록 동의)은 인용을 지운다(문장이 이유를 스스로 말하고, 중복 질문과는 뜻이 다르다). §3-6 에 그런 문구는 처음부터 없었다(`git log -S`). 기각: §3-6 에 "1회 원칙" 이라는 새 용어를 더하기.
- 규칙 3개의 위치와 문구(사용자, 2026-10-20): §1 "추측 금지" 줄에 "추천은 근거와 함께, 확인 못 한 안은 ⚠️추정", "아부 금지" 줄에 "내 추천은 새 근거가 있을 때만 바꾸고 그 근거를 말한다 — 다시 묻는 것만으로 바꾸지 않는다. 사용자가 결정하면 따르되(§8 의 금지는 그대로), 새 근거 없이 내 추천이 바뀐 것처럼 말하지 않는다"(code-reviewer D — 결정을 따르는 것과 추천을 바꾸는 것을 구분하고 §8 금지를 넘지 않게), `skills/dlc` 파이프라인 3단계 줄에 "규모표의 단계를 Tasks 에 처음부터 전부 적고, 나중에 더하는 Task 에는 이유를 적는다. 조건부 단계가 해당 없거나 사용자가 생략을 정한 단계는 `- [x] <단계> (YYYY-MM-DD) — 생략: <사유>` 로 닫는다"(`/e merge` M1(5) 가 미완료 Task 를 거부하고 plan-lint 가 날짜를 요구한다. 생략을 누가 정하는지 적어 리뷰·검증을 스스로 건너뛰지 않게 — code-reviewer G, dlc 자기 진단의 "plan/리뷰/검증 건너뜀" 은 중대 신호). 기각: 새 절 만들기(같은 주제를 두 곳에 둔다).
- Acceptance 변경(사용자 승인 2026-10-21): 2 "핵심 문구 76개" → "97개" — 단위 2 전에 code-reviewer M1·M8 지적으로 21개를 더했다(원래 76개는 그대로 들어 있어 검사가 강해지기만 했다).
- Acceptance 변경(사용자 승인 2026-10-21, 단위 2·3 확인 때): 6 "10개 모두" → "12개 모두"(모순 11·12 추가).
- Acceptance 변경(사용자 승인 2026-10-21): 6 "9개 모두" → "10개 모두"(모순 10 추가) · 9 "risk-based-approval 17행과 plan log Deferred 의 각 항목" → "plan log Deferred 의 각 항목"(모순 2 를 "머지" 유지로 고쳐 wiki 갱신이 필요 없어짐). 단위 1 확인 때 함께 승인받았다.
- 커밋 단위: 1) `docs(claude-md): add evidence rules and fix contradictions` — `CLAUDE.md`·`skills/dlc/SKILL.md`·`skills/e/SKILL.md`·`README.md` 2) `docs(claude-md): compress CLAUDE.md outside §3-1 and §8` — `CLAUDE.md` 3) `docs(claude-md): compress §3-1 and §8 without moving rules` — `CLAUDE.md`. plan·log·manifest·intent·선행 plan 줄은 마지막 기록 커밋. 이유: 동작을 바꾸는 변경(1)과 바꾸지 않는 압축(2·3)을 따로 확인하고, 가장 위험한 §3-1·§8 압축을 따로 되돌릴 수 있게. 단위 1 은 리뷰·사용자 확인·커밋을 마친 뒤 단위 2 를 시작한다(같은 파일이라 커밋 전에 겹치면 commit-check 가 나누지 못한다). 기각: 두 plan 으로 나누기 — plan 마다 worktree·리뷰·머지 고정비가 붙고, 커밋 단위가 이미 따로 리뷰된다.
- 단위 2·3 분리: 둘 다 CLAUDE.md 를 고치고 대화형 stage 는 못 쓴다. 커밋할 때 작업 파일에서 §3-1·§8 만 단위 1 커밋(45a8204)의 것으로 되돌린 사본을 만들어 단위 2 로 커밋하고, 그 다음 작업 파일 전체를 단위 3 으로 커밋한다(scratch `fill-u3.js --u2`). 리뷰 반영이 §3-1·§8 밖이면 단위 2 에, 안이면 단위 3 에 들어간다.
- 크기 결과(보조 목표): 5555fc6 의 268줄·49,942B → 264줄·48,170B(−3.5%, 단위 1 이 더한 문장 포함 — 단위 1 뒤 50,737B 기준이면 −5.1%). 메인은 처음 "약 20% ⚠️추정" 이라고 했는데, 그중 절반이던 §8 절차 이관을 계획 리뷰(S2·S3)가 막았다 — 커밋 게이트와 (a)(b) 조건이 CLAUDE.md 에만 있다는 새 근거. 남은 압축은 7월 실측 상한(약 11%)보다 낮다.
- 테스트: 규칙 문서라 새 테스트는 없다(§7 예외 — 수동 검증은 manifest 대조·핵심 문구·표지·독립 대조·사용자 문구 확인). CLAUDE.md 를 언급하는 테스트 5개는 경로만 쓰고 내용을 읽지 않는다(2026-10-21 확인). worktree 세션과 그 subagent 는 main checkout 의 CLAUDE.md 를 읽어 새 문구의 동작은 머지 전에 관찰할 수 없다 — 사용자 문구 확인이 유일한 행동 검증이다.
- architecture-reviewer: 부르지 않는다 — 문서만 바뀌고 코드 구조·API 변경이 없다.
- 선행 plan 본문 편집: §10 트리거 3 은 소급 생성 때 선행 plan 에 `intent:` 1줄만 더하라고 하지만, remove-conclusion-block 의 [post-merge] 체크는 사용자 지시("같이: … 체크")라 intent 소급과 별개의 기록 갱신으로 한다. plan-format 의 끝난 [post-merge] wiki Task 도 같은 근거(0c6f7e2)로 체크한다.
- 롤백: 전체는 `git revert -m 1 <merge sha>`. 압축에서 규칙 손실이 나중에 드러나면 단위 3(또는 2) 커밋만 `git revert <sha>` 로 되돌린다 — 단위 1 의 리뷰 반영은 단위 1 커밋에 합쳐 두어야 가능하다. 되돌린 뒤 각 머신은 main 을 pull 하고 새 세션을 연다(세션이 main checkout 의 CLAUDE.md 를 읽는다).

# Blockers
