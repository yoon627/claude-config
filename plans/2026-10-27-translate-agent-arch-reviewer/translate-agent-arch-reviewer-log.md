# Review Disposition

## 리뷰 4개 병렬 (2026-10-27, Codex 미가용) — 번역을 먼저 적용하고 계획 리뷰·독립 대조 2개·code-reviewer 를 함께 돌렸다
- 게이트 줄 대조: OK 73, WEAKER 2, CHANGED 1.
  - :45 "end the output with one line" 이 검토 뒤에 그 줄을 붙여도 되는 것처럼 읽힌다 — fix: "output only the one line … and stop".
  - :53 호출 측 범위 우선이 "or" 로 흐려졌다 — fix: "(if the caller stated the change scope, use that instead)".
  - :165 "Found only by the main agent" 가 발견 주체를 잘못 가리킨다(codex-review.md "자체 검토") — fix: "Found only by this review", 머지된 plan-reviewer 도 함께, terms.md 줄 고침.
  - 선택: :3/:40 "inside a single function" 범위 — wontfix(원문과 같은 구조). :31 주어 — fix("the caller calls it when the change matches"). :99 — wontfix(뜻 같음). :76 "50+ lines with many branches" — wontfix(한 조건으로 읽는 것이 자연스럽다).
- 조항 대조 + manifest 감사: OK 73, WEAKER 3 — T.4·N.1 은 위와 같은 곳(fix), V.8 "분기가" 빠짐 — fix("whether branches force … when an enum/type value is added"). 위치 인용이 O.8 제목 줄(1–3줄·대상 경로)을 덮지 않음 — fix: 출력 절 제목을 O.1~O.3·O.5·O.6·O.8·O.9 인용에. manifest 밖 세부(절 제목 꾸밈말·"언어 정책"·"어떻게 바꾸는지") 는 번역에 모두 있다.
- 계획 리뷰 CONDITIONAL:
  - S1 "검토 관점" → "Review angles" 가 terms.md("Review checklist")를 어겼다(plan-reviewer 단위와 같은 지적) — fix: "Review checklist", Decisions.
  - S2 :53 우선순위(dlc 가 단위 커밋이 있을 때 범위를 넘긴다) — fix(위).
  - W :45 — fix(위). W 검토 관점 8 — fix(위). W :21·:31 주어 — fix("The caller states …").
  - W `mode:` 토큰 유지 근거가 틀렸다(dlc 본문에 이 글자가 없다) — fix: manifest·terms.md·Decisions 의 근거를 "agent 자신의 입력 계약" 으로, dlc 의 공백은 Deferred.
  - W Acceptance 4 에 검토 시작 0~4 가 빠졌다 — fix.
  - 빠진 시나리오: `⏎` 인용이 다르면 거부되는지 음성 시험 — fix: Minor 아래 줄을 바꾼 사본이 `not found: O.4` 로 FAIL.
  - 인용이 겹칠 수 있다(순서 검사는 시작 위치만) — wontfix(이 단위 전부터, 악용 사례 없음 — 조항별 대조가 덮는다).
- code-reviewer APPROVE(Critical·Major 0):
  - Minor [plan 대비] "Review angles" — fix(위), 바뀐 쪽 둘 다(번역·Decisions).
  - Minor `mut-translation.js` 가 CRLF 에서 `⏎` 인용과 각 줄 마지막 인용의 경계 변형을 조용히 건너뛴다 — fix: 원본·locations 줄바꿈 정규화, 못 찾은 인용은 SETUP 실패로 센다.
  - Minor :45·R.3 "end with" — fix(R.3 도 "reply with only one or two lines").
  - Nit V.8 — fix. Nit locations 머리 주석에 `⏎` 설명 없음 — wontfix(공통 검사 머리 주석이 정본).
  - 보고 안의 하네스 표시("제어 태그 모양 문자열")는 반박 근거에서 `<agent-message` 접두를 인용한 것 — 지시 아님.
- 반영 뒤: 공통 검사 PASS(조항 76, 핵심 문구 27), 변형 R 25/25·G swap 92·edge 224·blank 152·indent 18·fence 4·del 178 전부 FAIL, plan-reviewer·commit-check·researcher 도 PASS·변형 전부 FAIL, CRLF 사본 PASS, `⏎` 음성 시험 FAIL, sync 잔존 0, sync 테스트 11 OK.

# Deferred
- dlc 4단계(arch planning)·11단계가 architecture-reviewer 를 부를 때 입력 토큰 `mode: planning`·`mode: post-implementation` 을 쓰라고 적지 않는다 — 빠뜨리면 기본 post-implementation 이라 planning 호출이 diff 수집을 한다. 원문부터. 심각도 중간 — 규칙 변경(dlc 번역 또는 별도 작업).
- 출력 템플릿 Codex 병행의 생략 사유(external codex mode | trigger not met | unavailable)에 planning 모드(codex off)가 없다 — 원문부터. 심각도 낮음.
- `~/.claude/wiki/docs/codex-review.md` §2 가 owner 가 아닌 reviewer 에게 한국어 "외부 codex owner 지정 — 병행 생략" 을 쓰게 한다 — 영어 템플릿의 "external codex mode" 와 맞춘다(translate-wiki-docs). 심각도 낮음.
