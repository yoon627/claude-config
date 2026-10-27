# Review Disposition

## 리뷰 4개 병렬 (2026-10-27, Codex 미가용) — 번역을 먼저 적용하고 계획 리뷰·독립 대조 2개·code-reviewer 를 함께 돌렸다
- 게이트 줄 대조: OK 72, WEAKER·STRONGER·CHANGED·MISSING 0. 선택 문구 4개:
  - :45 "holding them stops the whole merge" 가 규칙과 반대로 읽힌다 — fix(아래 계획 리뷰 S1 과 같은 곳).
  - :67 "needs a `message`" 가 "필수" 보다 약하다 — fix: "requires".
  - :38 "point to the undo" — fix: "tell the user how to undo it (`rollback`)".
  - :43 "wip 라" 의 인과 — wontfix(두 조건이 늘 함께 참이라 뜻이 같다).
- 조항 대조 + manifest 감사: OK 55, non-OK 0, 인용 72개가 각각 파일에서 한 번. manifest 밖 세부 4개(F.1 "현재 브랜치의"·제목 줄·K.2 예시 세부·굵은 강조)는 번역에 모두 있다 — fix 없음(위치 검사가 이제 인용 밖 글자 0 을 요구해 제목 줄 외에는 모두 인용에 덮인다, 제목 줄은 4절 표지). 문구 메모: J.12 "recording purpose" → fix("serves a different purpose (keeping a record)"), K.6 → fix("trailers that differ per session"), F.2 "uncleaned commits" → wontfix(e M3 의 같은 말과 맞춘다).
- 계획 리뷰 CONDITIONAL:
  - S1 `/e merge` 절에서 보류 → "hold" 가 상태값 `held` 와 같은 말이다(e 단위의 같은 지적 — `plans/2026-10-26-translate-skill-e/translate-skill-e-log.md`) — fix: 파일 전체의 보류를 "leave unapplied" 로(:12·:32·:37·:44·:45·:46), :46 은 "when the plan is left unapplied or apply fails"(e M3 의 "leaving its plan unapplied, apply failure" 와 같은 말).
  - S2 Acceptance 1 이 증명하는 것을 넘어 말한다 — 12글자 이하 경계 삽입·H1 수정·빈 줄을 규칙으로 바꾼 것이 PASS 했다 — fix: check-cc 5절을 인용 밖 글자 0 으로(`description: ` 키·제목·frontmatter 틀·코드 펜스만 제외), 4절에 H1·frontmatter 키 검사, 변형 시험에 그 사례 8개(B), Acceptance 1 에 "뜻이 같다는 근거는 5 와 사용자 diff 확인" 을 적었다(Decisions).
  - W 2절이 backtick 을 떼고 찾아 흔한 영어 낱말에 맞는다 — fix: backtick 째로 찾는다(`show <sha>`·`pending origin/<default>` 는 실제 code span 인 `commit_units.py show <sha>`·`commit_units.py pending origin/<default>` 로).
  - W :44 가 `commit_units.py` 의 한국어 오류 문구에 묶여 있다 — defer(Deferred).
  - W :66 "passes on its author and message" — fix: "the new commit takes its author and message".
  - W 가장 위험한 단계를 plan 이 이름 붙이지 않았다 — fix(Decisions).
- code-reviewer APPROVE(Critical·Major 0):
  - Minor 5절 경계 삽입 — fix(위 S2). Minor 2절 backtick — fix(위 W).
  - Minor [plan 대비] description 예시 번역에 Decisions 줄이 없다 — fix, 바뀐 쪽 plan.
  - Nit 변형 시험이 scratch 에만 있다 — fix: `plans/2026-10-27-translate-skill-commit-check/mut-cc.js` 로 옮겼다.
  - Nit 문구 :21 "type" → fix("run"), :12 "divides by file" → fix("the purposes separate by file"). :35·:38 은 위와 같은 곳.
  - Nit 한글 정규식이 자모를 놓치고 원문자 검사가 ①~⑤ 뿐 — fix(자모 범위·①~⑳).
- 반영 뒤: check-cc PASS(조항 55, 핵심 문구 45, 인용 밖 글자 0), 변형 A 24/24·B 8/8·문장 삭제 113/113(처음 1건 — `description:` 키 삭제 — 을 놓쳐 4절에 frontmatter 키 검사를 더했다).

# Deferred
- `skills/commit-check/SKILL.md` `/e merge` 절이 `commit_units.py` 의 오류 문구 `git merge-tree --write-tree 실패(exit N): …`(`Git.run`)에 글자로 묶여 있고 이 연결을 확인하는 테스트가 없다 — 나중에 `commit_units.py` 메시지를 영어로 옮기면 SKILL.md 의 그 문구를 같은 머지에서 바꿔야 한다. 심각도 중간 — 별도 작업(코드).
- 묶음 공통 용어표 — 앞 단위의 용어 결정(보류 → "leave unapplied", `held` 와의 충돌)이 다음 단위로 넘어가지 않아 같은 지적이 다시 나왔다. intent `# Constraints` 에 번역 용어표를 두는 안 — 공통 Constraints 변경이라 사용자 확인 뒤. 심각도 낮음.

# Workflow Findings
- 2026-10-27 앞 단위(translate-skill-e)의 용어 결정이 이 단위로 넘어오지 않아 같은 리뷰 지적("hold" vs `held`)이 다시 나왔다 — 방법(manifest·대조·변형)은 넘기면서 용어 결정은 각 단위 log 에만 남겼다. 대책 후보는 Deferred 의 묶음 용어표.
