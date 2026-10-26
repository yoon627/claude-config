# Review Disposition

## 계획 리뷰 (plan-reviewer, 2026-10-26, CONDITIONAL, Codex 미가용)
- S1 역방향 인용(CLAUDE.md 가 한국어 skill 제목을 인용: dlc 요구사항 명확화·분할 판정·커밋 단위·worktree 정리 규칙·증거기반 자기개선·규모표·16단계 커밋 규칙·묶음 모드) — fix: 영어로 옮기고 대응표를 intent Constraints 로 넘겨 그 skill 의 번역 단위가 제목을 같은 영어로 맞춘다(사용자 결정 2026-10-26 "영어로 + 대응표로 넘김").
- S2 다른 열린 intent 2개(repo-context-kit·repo-audit-followups)의 옛 토큰 — fix: 토큰만 영어로 바꾼다(§10 소유권 예외, 사용자 승인 2026-10-26). 닫힌 intent 는 읽는 곳이 없어 그대로.
- S3 Acceptance 1·2 가 자기 채점에 가깝다 — fix: 핵심 문구 대응표를 번역 전에 사용자 승인(2026-10-26 "이대로 쓴다"), Acceptance 5 를 조항 id 별 판정·locations-en 확인까지 독립 subagent 가 하도록 강화.
- S4 가리키는 쪽 확인 없음 — fix: pointers.md 의 항목마다 새 영어 문구가 그 파일에 있고 옛 한국어 문구가 없는지 양방향 검사(Acceptance 4).
- W1 빠진 가리키는 곳(architecture-reviewer·researcher 의 "§0 언어 정책", commit-check 의 "리뷰 가능한 하나의 목적 단위") — false-positive: 따옴표 없는 서술 참조이거나 그 skill 자신의 기준 문장이라 CLAUDE.md 의 글자를 찾는 포인터가 아니다(Decisions "가리키는 곳 범위"). 대신 quote 스캔으로 찾은 c·e·dlc·architecture-reviewer·README 의 따옴표 인용을 pointers.md 에 넣었다.
- W2 공유 형식 추가(`[묶음]`·Acceptance 항목 형식·`NEEDS-HUMAN`) — fix: pointers.md 에 넣었다. `델타 없음` — false-positive: dlc·plan-reviewer 가 쓰는 것은 `없음 — <근거>`(Goal 라벨 불릿 자체 형식)이고 CLAUDE.md 의 `델타 없음 — <근거>` 문자열을 공유하지 않는다.
- W3 wiki docs(dlc-details.md·wiki-inbox.md) 와 역사 기록 페이지 — fix: [post-merge] 목록에 docs 2개, 역사 기록 페이지는 pointers.md 에 "그대로" 로 표시.
- W4 Codex agent TOML 동기화 — fix: [post-merge] Task 로 `scripts/bootstrap/sync_codex_agents.py` 재실행. `## Codex 병행` 제목은 건드리지 않는다.
- W5 improve.sh 3번 점검은 매치 0 이면 통과 — fix: Acceptance 7 에서 빼고 Acceptance 4 의 굵은 agent 이름 검사가 맡는다. `**reviewers**` 같은 새 굵은 소문자 단어를 만들지 않는다.
- W6 언어 쏠림 위험 — fix: Acceptance 5 에 §0·§12 트리거 문구 확인을 넣고, [post-merge] 새 main 세션에서 답·새 plan 이 한국어인지 관찰. 되돌림 조건: 답이나 새 plan 이 영어로 나오면 revert 를 제안한다.
- W7 manifest 0.1 의 앞 절반(한국어로 답)이 낡음 — fix: manifest-add 에 0.lp1~5 로 나눴다(0.1 은 식별자 원문 유지 절반만 남는다).
- W8 read-points 와 같은 파일(agents/code-reviewer.md·skills/dlc/SKILL.md) — fix: Decisions 에 순서 기록(intent Constraints 대로 먼저 머지하거나 이 단위 위로 rebase).
- W9 롤백 범위(공용 wiki·Codex TOML·머지 뒤 영어 토큰으로 쓴 intent) — fix: Decisions 롤백 줄에 추가.
- W10 Acceptance 8 의 측정 스크립트가 없을 수 있음 — wontfix: 보조 항목이고 이 세션 scratch 에 있다(`tok/measure.sh`).
- self-flag(한국어 파일 안 영어 인용) — accepted-risk: 사용자 결정 "전부 영어로"와 기존 `Commit or push only when the user asks.` 선례. 묶음 공통 해석으로 intent Constraints 에 적었다.

## 독립 대조 (Acceptance 5, subagent 3개, 2026-10-26)
- §0–§3: OK 82 · CHANGED 2. 1.11 "marked `[slow]`" — fix: "shown as `[slow]`"(verify.sh 가 건너뛸 때 찍는 표시). 3.6.4 오탐 한 줄 템플릿이 영어라 사용자 답이 영어로 쏠릴 수 있음(확신도 라벨·"unverified"·"done" 도 같은 종류) — fix: §0 에 0.lp6 문장(인용된 라벨·템플릿·선택지 이름이 사용자 답에 나오면 한국어로).
- §4–§8: OK 123, 0 non-OK. nit 8.10b(검사 범위가 `~/.claude` 라는 뜻이 흐림) — fix. 7.2 "필수" 누락 — fix. 8.7 소문자 시작 — wontfix: `skills/e` 가 인용하는 "push only on request" 와 글자를 맞춘다. 5.3 — 문제 없음.
- §9–§13: OK 109, 0 non-OK. WIP 표시 문구가 `skills/e/SKILL.md:33` 과 다름 — fix: e 를 영어 인용으로. §10 에 "plan 본문은 한국어, 표시는 고정" 한 줄 제안 — fix: 0.lp7 로 §0 에. §12 트리거에 "e.g." 제안 — wontfix: 원문도 괄호 예시 구조이고 앞 문장이 뜻으로 조건을 말한다.

## code-reviewer (2026-10-26, APPROVE, Critical·Major 0, Codex 미가용)
- 사용자에게 보이는 영어 템플릿·선택지 이름 — fix: 0.lp6(위와 같음). 머지 뒤 관찰(Acceptance 10)도 유지.
- intent 토큰이 고정 문자열이라는 말이 CLAUDE.md 에 없음 — fix: 0.lp7.
- `scripts/plan-match.js:10` 주석의 옛 §10 인용 — fix: 영어 인용으로, pointers.md 에 추가. `scripts/dlc-early-stop.js:147` 의 따옴표 없는 서술 참조 — wontfix: 가리키는 곳 범위 밖(Decisions).
- [plan 대비] plan Task 의 파일 목록이 diff 와 다름 — fix(plan): 리뷰 시점 뒤 Task 를 실제 파일로 고쳤다. 바뀐 쪽 plan.
- [plan 대비] ops-docs-rework intent 의 토큰 외 편집(Constraints 2줄·`# Plans` 줄·translate-repo 줄에서 CLAUDE.md 제거) — false-positive: 이 plan 의 묶음 기록(소유권 범위 — 자기 줄과 공통 제약 변경, 진행 중인 다른 묶음 plan 없음). 사용자 diff 확인에 포함. 바뀐 쪽 없음.
- `(open)`·`(resolved)` 가 다른 곳의 같은 단어와 겹침 — wontfix: 괄호째 맞춰 구분된다.
- 문구 nit(§12 "permanent" 어순·§13 "avoidance repeats"·§3-1 "put the `ask`") — fix. "working worktree" — wontfix: 원문 "작업 worktree" 의 뜻 그대로.
- ⚠️ (구현) [리뷰 미경유] §0 의 0.lp6·0.lp7 문장 — accepted-risk: 번역으로 생긴 쏠림을 막는 새 문장이라 사용자 diff 확인으로 검증한다.

# Deferred
- `skills/wt/SKILL.md:114` "조건5" 는 지금 `skills/e` 번호로 조건4(merged 게이트) — wt 번역 단위에서 고친다. 심각도 낮음(괄호 안 설명).
- `scripts/pre-commit-check.sh:454`·`.ps1:558` 의 출력 예시 `"회사 repo"` — CLAUDE.md §11 은 "company repo" 가 된다. hook 사용자 출력이라 translate-hooks 단위.
