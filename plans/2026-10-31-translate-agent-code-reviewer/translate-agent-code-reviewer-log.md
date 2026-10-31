# Review Disposition
- 게이트 줄 전담(59줄 — OK 57)
  - AMBIGUOUS 3행 description 의 "not trivial (a typo, …)" 가 괄호를 해당 변경의 예로 읽힐 수 있다 — fix: "other than a trivial one (trivial = …)". 변형 R "description scope narrowed" 의 기준 글자도 함께 고쳤다.
  - WEAKER 90행 "Agreement … does not raise" 가 금지가 아니라 사실 진술 — fix: "Do not raise a candidate to CONFIRMED on the two models' agreement alone".
- 조항별·manifest 감사(84조항 — OK 83)
  - TERM V.6 `⚠️circumstantial` 이 없는 확신도 라벨처럼 읽힌다 — fix: `⚠️inferred`(CLAUDE.md §1 라벨, 같은 파일 95행과 같음).
  - manifest 가 V.6·O.2·O.4 의 설명·자리표시자를 줄였다 — false-positive: 번역문은 모두 유지했고(리뷰어 확인) 대조 검사의 핵심 문구가 덮는다.
- code-reviewer — APPROVE(검토 기준·verdict 대응·severity·안전 규칙 완화 없음, check PASS·변형 30/30·sync 테스트 11 OK·frontmatter-lint·verify ALL PASS)
  - Minor [plan 대비] Tasks 에 `plans/2026-10-21-ops-docs-rework/terms.md`·`scripts/bootstrap/test_sync_codex_agents.py` 경로가 없다 — fix(plan): 포인터 Task 에 두 경로를 적었다. 바뀐 쪽: plan.
  - PLAUSIBLE(원문부터) Codex 프롬프트가 `##` 제목 형식을 정하지 않아 결론 추출 grep 이 빈 결과일 수 있다 — defer(Deferred): 번역 단위는 규칙을 강하게 하지 않는다. 고치려던 별도 커밋은 auto 모드 분류기가 자기 수정으로 막아 사용자 결정으로 넘긴다.
  - CONFIRMED(원문부터) verdict 대응에 "CONFIRMED Minor/Nit 만" 인 경우가 없다 — defer(Deferred): 위와 같다.
  - 참고: `plans/2026-10-27-translate-agent-plan-reviewer/check.json` 대조가 main 에서도 FAIL 9 — 그 단위 머지 뒤 a4f39e7·dc71c19 가 plan-reviewer 를 고쳤기 때문. 끝난 단위의 대조 기록이라 고치지 않는다.

# Deferred
- `agents/code-reviewer.md` Codex 프롬프트(85행)에 `## Critical`·`## Major`·`## Minor`·`## Nit` 제목을 쓰라고 정하기(plan-reviewer a4f39e7 과 같은 방식) — 원문부터의 빈틈, 심각도 낮음. 2026-10-31 시도는 auto 모드 분류기가 Self-Modification 으로 거부 → 사용자 결정 필요
- `agents/code-reviewer.md` verdict 대응(111행)을 "앞에서부터 첫 일치: CONFIRMED Critical/Major → REQUEST CHANGES · 그 밖에 PLAUSIBLE 이 있으면 NEEDS DISCUSSION · 그 밖(CONFIRMED Minor/Nit 만, 또는 없음) → APPROVE" 로 — 원문부터의 빈틈, 심각도 낮음. 위와 같은 이유로 사용자 결정 필요
- 공용 wiki `pages/concept/plan-handoff.md`·`pages/concept/hub-and-spoke-isolation.md` 의 옛 이름 "plan 반영용 요약" 지우기 — translate-skill-dlc 머지 뒤 main 세션에서
