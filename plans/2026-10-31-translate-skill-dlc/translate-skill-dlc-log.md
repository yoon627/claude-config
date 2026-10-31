# Review Disposition
- 게이트 줄 전담(약 230 — OK 227)
  - AMBIGUOUS 45행 "or for plans being taken over" 가 2026-09-09 이후 plan 도 이어받으면 면제로 읽힌다 — fix: "made before this rule (2026-09-09), whether you are starting or taking them over".
  - CHANGED 100행 "because the plan was left unapplied" 의 plan 이 §10 plan 파일로 읽힌다 — fix: "the commit-check proposal was left unapplied"(조항별 U.20·code-reviewer Nit 과 같은 지적).
  - AMBIGUOUS 100행 "and only **record files** …" 동사 없음 — fix: "and commit the **record files** such as the plan — and only those — as a fixup of the last unit".
- 조항별·manifest 감사(358조항 — OK 352, manifest 누락 0)
  - TERM V.5·L.8 "check field" — fix: "verification field"(terms.md·code-reviewer 41행).
  - TERM H.5·B.45 "Verification command unidentified"/"unidentified" — fix: "not identified"(terms.md·code-reviewer 64행). `pointers.md` 의 "미식별 → unidentified" 메모는 이 결정으로 대체.
  - SHIFT U.20 — 위 100행과 같음, fix.
  - ADDITION J.29 "because the session is attached" — fix: "because it reports being attached".
  - 참고 V.15·V.19 "backstop" vs CLAUDE.md "safety net" — false-positive: 리뷰어도 고칠 필요 없다고 봤고 절 라벨로 남긴다.
- code-reviewer — APPROVE(evidence gate·fix loop·판정·worktree 게이트·self-flag·격리 경계·커밋 규칙 완화 없음, check PASS·변형 40/40·frontmatter-lint·plan-lint·verify ALL PASS)
  - Minor [plan 대비] README 282·316 "dlc 분할 판정" 포인터 미처분 — fix: "dlc Split judgment". 바뀐 쪽: 코드.
  - Minor [plan 대비] 의도한 변경 3건이 log 초안에만 있다 — fix: plan `# Decisions` 로 옮기고 Tasks 체크. 바뀐 쪽: plan.
  - Nit 100행 — 위와 같음, fix.
- code-reviewer 재검토(5b6355b) — APPROVE(7곳 문구 수정은 완화 없음 — 45행은 면제를 좁힌다)
  - Nit [plan 대비] "기록 커밋, ff-merge" 가 머지 전에 체크됨 — false-positive: 기록 커밋 바로 뒤 같은 명령에서 ff-merge 를 실행한다(체크가 기록 커밋에 들어가야 한다).
  - 범위 밖 지적 `agents/plan-reviewer.md` 14항이 "이어받는 plan" 을 모두 면제 — fix: 같은 머지의 별도 커밋으로 dlc 45행과 같게("made before this rule (2026-09-09) … whether started or taken over"). 면제를 좁히는 변경.

# Deferred
- 공용 wiki 페이지 13곳이 dlc 의 한국어 절 이름(요구사항 명확화·분할 판정·격리 경계·진입 매트릭스·자기 진단·조사 프로토콜·wiki 연계·"읽을 곳")과 옛 이름 "plan 반영용 요약" 을 가리킨다 — main 세션에서 라벨만 영어로(목록 `pointers.md` "[post-merge] 공용 wiki"). 심각도 낮음(뜻은 같아 찾을 수 있다)
- `scripts/dlc-task-router.js` 51·57줄 hook 문구가 `조사 프로토콜`·`요구사항 명확화 '프로토타입-우선'` 을 가리킨다 — translate-hooks 단위에서 `Investigation protocol`·`Requirement clarification 'prototype-first'` 로. 심각도 낮음
- `~/.claude/wiki/docs/dlc-details.md` 의 SKILL 절 포인터 5곳 — translate-wiki-docs 단위에서(`pointers.md`)
