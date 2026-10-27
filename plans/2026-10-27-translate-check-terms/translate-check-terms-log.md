# Review Disposition

## 리뷰 (2026-10-27, Codex 미가용) — 처음엔 jira-task 번역과 한 단위로 계획 리뷰·code-reviewer·독립 대조 2개를 돌렸다. jira-task 번역은 사용자 지시로 철회해 그 번역에 대한 처분은 남기지 않고, 용어 대조에 대한 것만 적는다.
- 계획 리뷰 CONDITIONAL:
  - S1 용어 대조가 있는지만 봐 섞어 쓴 번역을 통과시킨다(arch 사본에서 재현) — fix: 개수 비교(원문 유지 문자열 밖 한국어 횟수 ≤ 번역 영어 횟수), 머지된 네 단위 PASS, 섞은 plan-reviewer 사본 FAIL.
  - S2 빈 블록·형식이 틀린 줄이 0쌍으로 PASS, 게으른 정규식이 다른 블록을 읽을 수 있다 — fix: `terms-block.js` 가 다음 절 제목 전에 열린 블록만 읽고(블록 줄이 `## ` 로 시작해도 된다), 틀린 줄·빈 블록·닫히지 않은 블록은 FAIL.
  - W termsSkip 이 흔적 없이 쉽다 — fix: `{"<한국어>": "<이유>"}`, 표·원문에 없거나 이유가 없으면 FAIL, 목록 형식도 FAIL, 건너뛴 낱말 출력.
  - W 기계 블록에 결정된 용어가 빠졌다·선택 규칙이 없다 — fix: 15쌍 추가(확신도·심각도·도메인 특화 프롬프트·결론부 추출 패턴 등), 선택 규칙을 terms.md·Decisions 에.
  - W `동작 규칙 => Rules` 가 너무 넓다 — fix: `## 동작 규칙 => ## Rules`.
  - W 용어 대조에 변형 시험이 없다 — fix: G.term(한 곳·전부 바꾸기).
  - W 롤백·가장 위험한 곳에 공통 검사 — fix(Decisions).
- code-reviewer REQUEST CHANGES(Major 1 = 위 S1, 같은 지적) — fix. Minor 블록 누락·빈·틀린 블록·게으른 정규식·`Rules` — fix(위). Open 용어표 추가가 머지된 단위 재실행을 깨뜨릴 수 있다 — Decisions(추가하는 단위가 재검증).
- 처음 블록 읽기가 `## 동작 규칙 => ## Rules` 줄을 다음 절 제목으로 보고 블록을 잘랐다(네 단위 FAIL) — fix: 열린 펜스를 닫는 줄까지 읽는다.
- 반영 뒤: 머지된 네 단위 PASS(적용 4·11·23·24쌍), G.term 8·22·46·48 전부 FAIL. 음성 시험: 섞어 쓴 사본 → `×2 … found 1` FAIL, 틀린 줄 → FAIL, 빈 블록 → FAIL, 잘못된 termsSkip → FAIL, 목록 termsSkip → FAIL.

# Deferred
- 없음.

# Workflow Findings
- 2026-10-27 jira-task 를 번역 대상으로 고른 뒤 사용자가 "jira 관련 스킬 건들지마" 로 막았다 — 남은 대상 목록을 낼 때 사용자가 손대지 않을 영역이 있는지 묻지 않았다. intent `# Out of scope` 에 적어 다음 단위가 고르지 않게 했다.
