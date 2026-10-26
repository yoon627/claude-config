# Review Disposition

## 계획 리뷰 (plan-reviewer, 2026-10-26, CONDITIONAL, Codex 미가용) — 사용자 지시 "추천안대로 끝까지"
- S1 `"등록 불가"` 는 jira-worklog 출력 문자열(테스트 고정)이라 번역하면 7단계 정리 차단이 풀린다 — fix: 입력·출력 문자열을 원문 그대로 두는 부류로 예외를 넓혔다(`/e 머지`·`"등록 불가"`·`wip:`·`(e checkpoint)`·`main-autopull ⓑ`), Acceptance 3 갱신.
- S2 `### 6 전.` 이 Acceptance 3(한글 0)과 4(표지 유지)를 충돌시킴 — fix: "6 pre" 로 옮기고 7곳 모두 같은지 개수로 확인(Acceptance 4), wiki 의 «"6 전" 절» 은 [post-merge].
- S3 slim-skill-e-ko 가 넘긴 항목(log S2 한정어·S3 가리키는 곳·S4 내부 참조·W1 안전 문구·W5/W6 경계 절과 이유 줄·W7 게이트 줄 대조·plan W4 원문자) — fix: 내부 라벨 개수 검사(Acceptance 4·`check-e.js` 4b절), 게이트 줄 전담 독립 대조(Acceptance 5), 한정어는 나머지 독립 대조에 명시, 원문자 ①②③ → 1)2)3), 가리키는 곳은 pointers.md.
- S4 description 번역이 manifest F.1 을 결정 없이 뒤집음 — fix: Decisions 에 F.1 수정·근거·기각안·머지 뒤 관찰(Acceptance 8)을 적었다.
- W1 plan 파일에 쓰는 Task 문구의 언어 — fix: 영어 고정 문자열로(Decisions).
- W2 [post-merge] wiki 목록 불완전 — fix: pointers.md 에 줄 단위로, 역사 기록 페이지는 "그대로".
- W3 원문자 — fix: ①②③ → 1)2)3), ⓑ 유지.
- W4 Split 근거 문장이 부정확 — fix(plan): 저장소 안 가리키는 곳은 번호·영어 라벨로만 가리킨다고 고쳤다.
- W5 `wip:`·`(e checkpoint)`·`M1~M6` 물결·CLAUDE.md 소문자 표기 — fix: 그대로 두고 `check-e.js` 가 확인.
- W6 게이트 줄이 가장 위험 — fix: 독립 대조 하나를 게이트 줄 전담으로.
- W7 기각안 없음 — fix: Decisions 에 기각안을 적었다.
- W8 머지 뒤 관찰 없음 — fix: Acceptance 8.
- W9 대조 스크립트가 scratch 에만 — fix: `plans/2026-10-26-translate-skill-e/check-e.js` 로 같이 커밋.
- self-flag(`/e 머지` 유지) — resolved: 리뷰어가 타당하다고 봤고 부류(입력·출력 문자열)로 넓혔다.


## 독립 대조 (Acceptance 5, 2026-10-26)
- 게이트 줄(머지 모드·7단계·Temporary commit rules·Worktree cleanup rules·Boundaries·16·83~87행): OK 58, WEAKER·STRONGER·CHANGED·MISSING 0. 선택 문구 2개 — L137 "(do not push through)" 이 git push 로 읽힐 수 있음 → fix "(do not force it)". L102 는 원문과 같은 구조 → code-reviewer 지적과 함께 fix.
- 조항(194개): OK 194, non-OK 0. 넘겨받은 한정어(7.2·M2·M4·B.5·T.4·MM.4c·6.4)와 경계 절·이유 줄 전부 남음. 메모: 다른 파일이 인용하는 "6 전" 등은 pointers.md [post-merge] 에 있다.

## code-reviewer (2026-10-26, APPROVE, Critical·Major 0, Codex 미가용)
- :55 "Hold"(보류)가 상태값 `held` 와 같은 단어 — fix: "commit-check leaving its plan unapplied".
- :102 체크포인트 모드 원격 삭제 문장이 묻지 않아도 되는 것처럼 읽힐 수 있음(원문과 같은 구조, :91·:127·:128 이 막는다) — fix: "ask with AskUserQuestion" 을 명시(규칙 변경 없음).
- [plan 대비] Tasks 체크가 작업보다 늦음 — fix, 바뀐 쪽 plan.
- Task 문구 "clean up" 이 7단계 정리와 같은 단어 — fix: "clean up the commits, then rerun `/e merge`"(pointers.md [post-merge] 도 같이).
- :82 "put … first" 가 "미리보기를 먼저" 로 읽힐 수 있음 — fix: "before the flag".
- :98 1인칭 "I reclaim" — fix: "Reclaim what this session started".
- refuted 8(필드 이름·"등록 불가"·`^wip\b`·commit-check 인자·CLI 플래그·exit 코드 예시·YAML·다른 파일 참조·보고 문구 소비처) — 감사 기록만.
- ⚠️ Decisions 2개(입력·출력 문자열 유지, description 예시 번역) — 리뷰어 "타당" → accepted-risk(description 은 머지 뒤 관찰 Acceptance 8 로 확인).

# Deferred
- `skills/e/SKILL.md` M5 의 `gh pr checks <N> --json name,bucket` — 이 머신의 gh 에서는 `unknown flag: --json` 으로 실패한다(2026-10-26 PR #243 머지 때 실제로 겪음, 일반 출력과 종료 코드로 대신 확인했다). gh 버전에 따라 다른 것으로 보인다 ⚠️. 심각도 중간 — 이 단계가 REJECTED 로 잘못 갈 수 있다. 별도 작업(번역 범위 밖).
- `skills/wt/SKILL.md:114` "조건5"(지금 e 번호로 조건4) — wt 번역 단위.
