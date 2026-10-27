# Review Disposition
- 게이트 대조·조항 감사·plan-reviewer N1 — 73줄 "Otherwise signals you never saw drop out of the count too." 가 "보지 못한 다른 경우"로 읽혀 뜻이 뒤집힐 수 있다 — fix: "Running it anyway would also drop signals you never saw from the count."
- 게이트 대조·조항 감사 — 16줄 "개수만 보고" 를 "only reports" 로 옮겨 보는 범위 제한이 약해짐 — fix: "only checks"
- 게이트 대조 — 52줄 "4단계와 동일" 을 "the 4 steps" 로 옮겨 64·65줄 "step 4" 와 어긋남 — false-positive: 괄호 안이 측정(1단계)→판단→제안이라 원문 뜻이 기본 4단계 전체다(45·58줄 "기본 4단계" 와 같은 쓰임)
- 조항 감사 — 52줄 "main directly" 가 main 브랜치로 읽힐 수 있음 — fix: "the main agent directly"
- 조항 감사 — 58줄 "It does not run in the 4 basic steps" 가 deep 실행 안의 1~4단계에서만 안 도는 것으로 읽힐 수 있음 — fix: "It does not run in a basic (non-deep) run" (제목 "deep only" 와 같은 뜻), 변형 앵커 갱신
- 조항 감사(문체) — 24줄 "`~`·`$HOME` are an error" → "`~` or `$HOME` is an error", 26줄 "the period" → "the time span", 27줄 "is past the threshold" → "the `checked` date … is older than the threshold", 16줄 "The same check 6" → "Check 6 also" — fix
- 조항 감사(문체) — F.2 "periodically (45 days)", D.7 "judges it with a separate researcher" — wontfix: 뜻이 같고 원문 구조를 따른다
- 조항 감사 — manifest 핵심 문구에 kind 이름 3개·`SessionStart`·`skills/*/SKILL.md`·`agents/*.md` 누락, K.1 에 "(기본·deep 공통)" 누락, N.4 축약 — fix: 핵심 문구 63 → 69, K.1·N.4 보강. 그 밖의 manifest 축약(N.3·N.6·N.7·R.4·D.2~D.4·S.1c·N.8b)은 wontfix — 번역문에는 다 있고 위치 인용이 조항 전체를 덮는다
- 조항 감사 — N.2 위치 인용에 "**Procedure**:" 줄이 함께 들어감 — wontfix: 그 줄을 덮을 조항이 따로 없고, 덮지 않으면 공통 검사 5절이 실패한다
- plan-reviewer S1 — 원문 유지 출력 글자가 스크립트 쪽 변경에 묶여 있지 않다(translate-hooks 가 `session-brief.js` 를 옮길 수 있다) — fix: terms.md 줄에 "같은 머지에서 7단계 인용도 고친다" 추가
- plan-reviewer S2·code-reviewer — Acceptance 8 이 명시 호출 전용 description 과 맞지 않고 실패 시 처리가 없다 — fix: 기준을 "명시 호출로 실행·단순 질문엔 안 골라짐 + 어긋나면 되돌림 제안" 으로(사용자 승인 대상, `# Decisions`)
- plan-reviewer N2·N3 — doc-drift 오탐 예상, Codex symlink 동기화 불필요를 `# Decisions` 에 — fix
- plan-reviewer N4 — Acceptance 4 의 `improve.test.sh` 는 번역 증거가 아니다 — wontfix: 스크립트 불변 확인용으로 적어 둔 것이고 번역 증거는 1~3·5 다
- code-reviewer — 13·40줄 "보고" 를 "reports" 로 — 16줄은 위에서 fix, 40줄(R.3)은 wontfix: 4단계가 보고로 끝나 두 뜻 모두 맞다

# Deferred
- §6 절차 2 가 아직 docs changelog 페이지를 1차 출처로 적는다 — 공용 wiki `native-overlap-ledger` 에 "WebFetch 가 잘리니 GitHub `CHANGELOG.md` 원문을 읽어야 한다"고 기록돼 있다. 규칙 변경이라 이 번역 단위 밖(심각도 낮음, `skills/improve/SKILL.md` §6) — code-reviewer
