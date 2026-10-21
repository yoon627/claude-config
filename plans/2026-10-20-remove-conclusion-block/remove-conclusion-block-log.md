# Review Disposition
plan-reviewer (2026-10-20, workflow `wf_502a2dc9-1a2`, CONDITIONAL, Codex CLI 미설치):
- 강한 1, Acceptance 2 의 검색이 테스트 파일까지 훑어 옛 장부 호환 테스트·무관한 `session-brief.test.js` 에 걸린다 — fix: 테스트가 아닌 파일만 보고, 테스트 쪽은 허용 목록을 명시.
- 강한 2, 선행 plan 2개(2026-09-15 도입, 2026-10-07 형식 변경)가 막으려던 문제의 재발을 다루지 않았다 — fix: 사용자에게 다시 물었고(메인은 제거 취소를 추천), 사용자가 재발 위험을 알고 완전 제거를 택했다(2026-10-21). Decisions 에 감수로 기록.
- 강한 3, 기각한 완화안이 기록되지 않았다 — fix: Decisions 에 기각 목록.
- 강한 4, "규칙 손실 0" 대조가 없고 dlc 16 의 "확인 필요 항목을 끝에 따로 올리기" 기능이 사라진다 — fix: 지우는 조항마다 버림·이관을 적었고, 그 기능은 "읽을 곳" 블록 안의 `확인 필요:` 표시로 남긴다.
- 약한, `dlc-signal.test.js` 의 개수 단언 — fix: 12 → 11.
- 약한, stop_hook_active·대기 턴의 순서 근거가 사라진다 — fix: 순서 유지, 주석을 남는 이유로, stop_hook_active 테스트에 장부 불변 단언.
- 약한, `edited` 의 다른 용도 — 확인: 결론 축 외 사용 없음. Bash plan 테스트는 `edited` 단언만 뺀다.
- 약한, README 수정 지점 불명확, 460행의 대기 턴 근거 — fix: Tasks 에 행 번호, 460행은 근거를 살려 다시 쓴다.
- 약한, §1 확신도 표시가 "미확인" 을 일부만 덮는다 — fix: Decisions 에 §1·§3-5·§3-6 "남은 리스크" 가 나눠 맡는다고 적음.
- 약한, 새 동작은 머지 후에만 실제 세션에서 볼 수 있다 — fix: `[post-merge]` Task 와 Acceptance 5.
- 약한, 없어지는 축의 과거 발동 수를 남겨야 한다 — fix: 이 서버 기준 0건(52행·5세션)을 Decisions 에 기록, 다른 머신은 모름.
- 약한, 가장 위험한 단계(§3-6 한 문단 재작성)를 지목하지 않았다 — fix: 커밋 전 사용자 문구 확인이 그 단계를 덮는다. 남길 절은 Acceptance 3 이 대조한다.
- 누락, 머지 시점에 떠 있는 세션 — fix: Decisions 에 무해함을 기록.
- 누락, `/e` 의 "§3-6 1회 원칙" 참조가 가리키는 문구가 없다 — defer: 원래부터 끊긴 참조, Deferred.
- rollback, PR 머지 커밋 revert — fix: `git revert -m 1 <merge sha>` 로 고쳐 씀.

code-reviewer (2026-10-21, APPROVE):
- F1, stop_hook_active 재종료 테스트가 대기 신호를 단언하지 않아 "순서 유지" 결정의 이유가 테스트로 묶이지 않는다 — fix: `early-stop-wait-shell` 신호 단언 추가.
- F2, README 460행 "결론 경고 7건" 이 없어진 축을 현재형처럼 읽힌다 — fix: "옛 결론 축(2026-10-21 제거) 경고 7건".
- F3, `dlc-early-stop.js` 머리 주석 "두 판정" 이 세 축과 어긋난다(원래부터) — fix: "여러 판정".
- F4, `skills/e/SKILL.md:46` 라벨 "보고 형식" 이 남은 내용(선택지 생략·승인)과 맞지 않는다 — fix: "마무리 선택지".
- F5, 테스트의 `last_assistant_message` 가 결론 축이 없어도 남아 있다 — wontfix: 실제 Stop 입력 모양이라 둔다.
- F6, plan Decisions 의 지우는 조항 목록에 dlc 16 "recap 은 새 단계를 더하지 않는다" 가 빠졌다 — fix: 버림으로 추가.
- F7, Deferred 의 wiki 목록이 실제 검색 결과와 다르다 — fix: 검색해 3건으로 고침.

# Deferred
- 공용 wiki(머지 후 main 세션): 결론 블록 언급 갱신. 2026-10-21 `rg -n '결론 블록|## 결론|early-stop-conclusion|CONCLUSION_OFF|결론 축' ~/.claude/wiki/pages ~/.claude/wiki/docs` 결과 3건 — `pages/concept/dlc-development-cycle.md:32`(읽을 곳 → 결론 `**다음**`, 현재 동작 서술이라 고친다) · `pages/decision/workflow-failures.md:51`(early-stop 대기 턴 행, 과거 기록이라 결론 축 제거 주석만) · `pages/entity/claude-code-agents-md-loading.md:29`(2026-09-25 제거된 AGENTS.md 의 과거 기록 — 그대로).
- `skills/e/SKILL.md` 46·82행의 "§3-6 1회 원칙"(과 dlc 의 "마무리 1회 원칙") 이 가리키는 문구가 CLAUDE.md 에 없다. 이 브랜치 이전부터 그랬다 — CLAUDE.md 줄이기 작업에서 정리(plan-reviewer, 2026-10-20).
