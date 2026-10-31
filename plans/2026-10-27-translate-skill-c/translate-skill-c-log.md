# Review Disposition

## 리뷰 4개 병렬 (2026-10-27, Codex 미가용) — 번역을 먼저 적용하고 계획 리뷰·독립 대조 2개·code-reviewer 를 함께 돌렸다
- 게이트 줄 대조: OK 21, WEAKER·STRONGER·CHANGED·MISSING 0. 선택 문구 1개(L60 "exception 5 below stops") → fix.
- 조항 대조 + manifest 감사: OK 75, non-OK 0. 감사가 찾은 manifest 밖 세부 12개는 번역에 모두 있다 — fix: 그중 위치 검사에 안 걸리던 것(2.1b 두 축·1.4 tracked 이유·2.15 예·2.24 `author.login`·3.17 무확인 생성)을 manifest·locations 에 보탰다. 문구 메모 3개(stuck=blocked·exception 5·"step 3, 5 exceptions") → fix.
- 계획 리뷰 CONDITIONAL:
  - S1 위치 인용이 조항 일부만 덮어 변형을 놓친다(변형 6개에도 PASS) — fix: 한 조항에 인용 여러 개(` ‖ `)를 허용하고 1.2·1.4·1.6·2.14·3.17 을 조항 전체로 넓혔다. 변형 시험 — 지금 번역본에 변형 8개(리뷰어 6개 + 게이트 약화 3개 중 겹침 제외)를 하나씩 넣어 8/8 FAIL(scratch `mut-c.js`).
  - S2 공용 wiki 가 c 의 Task 문구를 인용 — fix: pointers.md 와 [post-merge] Task·Acceptance 7. Split 근거도 고쳤다.
  - W Tasks 가 실제보다 늦음 — fix(plan). manifest 는 번역 초안 전에 만들었다(이 세션 순서: manifest → 초안 → 위치) — 그래도 번역자가 만든 것이라 조항별 대조 subagent 가 원문에서 직접 감사했다.
  - W 머지 뒤 트리거 관찰 없음 — fix: Acceptance 8.
  - W `PR#n address review: <gist>` 의 gist 언어·기각안 — fix(Decisions): 접두는 영어 고정, `<gist>` 는 plan 언어(한국어).
  - W README 결정 없음 — fix(Decisions): README 는 바꾸지 않는다(동작 불변, README 는 §0 밖) — `dlc-doc-drift` 경고는 예상된 오탐.
  - W 예외 번호 검사가 탐색 위치 목록과 겹침 — fix: 예외 블록("closed list of 5" 뒤)으로 고정.
  - W "2+ 후보 선택" 이 닫힌 목록 5종에 없음(README 343행과 SKILL 불일치) — defer(규칙 변경, Deferred).
  - W e 의 "end-of-session done confirmation" 라벨이 e 에 없음 — fix: "the done confirmation of e's step 4".
- code-reviewer APPROVE(Critical·Major 0):
  - :69 "outside main" 이 dlc 게이트를 반대로 읽게 함 — fix: "whenever it is not in a work worktree (on main or outside)"(dlc 진입 조건과 같은 뜻 — 원문의 모호함을 바로잡은 것이라 아래 ⚠️).
  - "stale" 이 최신성 점검과 헷갈림 — fix: "no longer valid"(3곳).
  - nit :26 "under the root" — fix: "under each plans/ root". nit :60 2개 — fix.
  - pre-existing :51/:52(자기 코멘트 제외 vs 사용자가 남긴 코드 지적) · `gh api … /comments` 에 `--paginate` 없음(30개 넘으면 누락) — defer(Deferred).
- ⚠️ (구현) [리뷰 미경유] :69 문구를 원문("dlc 가 main 밖이면")보다 분명하게 고쳤다 — 원문 그대로 옮기는 안도 있었다 — 영어에서는 "outside main" 이 dlc 규칙과 반대로만 읽혀 dlc 진입 조건 문구로 맞췄다(규칙 변경 아님) — accepted-risk, 사용자 diff 확인으로 검증.

# Deferred
- `skills/c/SKILL.md` 1단계의 "2+ 후보 → 사용자 선택" 정지가 3단계 "닫힌 목록 5종" 예외에 없다(예외 2 는 fallback 만). README 343행은 예외 2 를 "plan 후보 다수" 로 적어 SKILL 과 어긋난다. 심각도 낮음 — 규칙 변경이라 별도 작업.
- `skills/c/SKILL.md` PR intake — 자기 코멘트를 빼는 규칙(현재 사용자 login 제외)과 "사용자가 남긴 코드 지적" 이 혼자 쓰는 흐름(같은 계정으로 PR 작성·리뷰)에서 충돌해 intake 가 늘 빈다. 심각도 중간 — 별도 작업.
- `skills/c/SKILL.md` 인라인 코멘트 수집 `gh api repos/{owner}/{repo}/pulls/<n>/comments` 에 `--paginate` 가 없어 30개를 넘으면 조용히 빠진다. 심각도 중간 — 별도 작업.
- (2026-10-30 처리) 위 인라인 코멘트 `--paginate` 누락과 자기 코멘트 제외 충돌 — `fix(c)` 커밋 2개(c-intake-fixes): `gh api --paginate`, 본인 계정 코멘트는 self 로 모아 보고에만(할 일은 사용자가 말할 때만 — 같은 계정의 Claude 코멘트와 구분되지 않는다)
- `skills/c/SKILL.md` PR intake 의 bot 판정 — `[bot]` 접미사는 `gh pr view` 의 reviews·comments(GraphQL)에 없고 Copilot 인라인에는 어느 API 에도 없다(`github-actions`·`copilot-pull-request-reviewer`·`Copilot`). 그래서 bot 코멘트가 사람 코멘트로 Task 가 되어 자동 실행된다 — Claude 코멘트 자동 실행과 같은 종류의 해. 세 출처를 REST(`--paginate`)로 바꾸고 `user.type == "Bot"` 으로 거르는 안. 심각도 중간(c-intake-fixes code-reviewer)
- (2026-10-31 처리) 위 bot 판정 — `fix(c)` 커밋(c-bot-detection): 세 출처를 REST `--paginate` 로, bot 은 `user.type == "Bot"`, 시각·커밋 필드 유지, 빈 리뷰는 state 만, bot 코멘트에 단 사람 답은 bot 을 맥락으로, 현재 login 을 못 얻으면 전부 self
- `skills/c/SKILL.md` intake — REST 에는 인라인 스레드의 resolved 상태가 없다(GraphQL `isResolved` 만) — 3단계 "코멘트 상태로 미해결 판단" 은 인라인에서 그 신호 없이 시각·뒤 커밋으로만 한다. 심각도 낮음(c-bot-detection code-reviewer)

