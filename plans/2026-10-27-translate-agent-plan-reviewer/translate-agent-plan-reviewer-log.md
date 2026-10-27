# Review Disposition

## 리뷰 4개 병렬 (2026-10-27, Codex 미가용) — 공통 검사·번역을 먼저 적용하고 계획 리뷰·독립 대조 2개·code-reviewer 를 함께 돌렸다
- 게이트 줄 대조: OK 91, WEAKER 1 — :39 "규약을 따른다" → "is in" 이 따르라는 지시를 흐린다 — fix: "Follow the common invocation convention (…) in …". 날짜 경계("2026-09-09 이전" → before, "2026-09-16 이후" → on or after) — wontfix(앞 날짜는 규칙 도입 전에 만든 plan 을 뜻한다, dlc 도 "도입 이전"). 선택 문구: I.4 기록처 → fix, I.5 묶음 모드 출력 문장 → fix, :29 문장 → wontfix(뜻 같음), :30 "measured" → fix("observed").
- 조항 대조 + manifest 감사: OK 51, WEAKER 1(같은 X.1) — fix(위). manifest 밖 세부 9개는 번역에 모두 있다. T.3~T.5 는 본문이 단어 없는 줄이라 제목만 인용 — 공통 검사가 단어 없는 줄을 원문과 같게 묶어 덮는다.
- code-reviewer REQUEST CHANGES(Major 2, 공통 검사):
  - Major 변형 시험이 원본을 먼저 돌리지 않아 원본이 FAIL 이면 모든 변형을 "잡았다" 로 센다 — fix: 원본 PASS 를 먼저 확인하고 아니면 exit 1(음성 시험 확인).
  - Major 핵심 문구 줄이 제목 바로 다음 줄이 아니면 0개로 PASS — fix: 첫 비공백 줄, 제목이 없거나 0개면 FAIL(음성 시험 확인).
  - Minor 종료 코드가 늘 0·SETUP 이 분모에서 빠진다 — fix: MISSED·SETUP(앵커 없음·no-op)이면 exit 1, SETUP 도 실패로 센다.
  - Minor CRLF — fix: 줄바꿈을 정규화(CRLF 사본 PASS 확인).
  - Minor terms.md 새 줄이 빈 줄 뒤라 표 밖 — fix.
  - Minor Codex 절 용어(본문 제목·템플릿 필드)가 terms.md 에 없다 — fix(3줄).
  - Minor `test_sync_codex_agents.py` 의 `REMOVED` 가 한국어 "도메인 특화 프롬프트" 를 찾아 마지막 reviewer 번역 때 깨진다 — defer(Deferred, terms.md 에도 적었다).
  - Minor 프롬프트가 제목 형식을 정하지 않고 공통 뼈대(Critical/Major/Minor)와 충돌 — defer(Deferred, 원문부터).
  - Minor 형식이 틀린 조항 id 가 조용히 빠진다 — fix: 조항 절의 `- ` 줄이 id 로 읽히지 않으면 FAIL(음성 시험 확인).
  - Nit `headings` 없으면 TypeError — fix: 필수로 검사. Nit 머리 주석 "ends with" — fix. Nit 문구(:30·:17·:38) — :30·:17 fix, :38 은 sync 가 요구하는 반쪽 한국어 제목이라 wontfix.
  - Nit [plan 대비] `없음` 유지 근거가 CLAUDE.md §0 이 아니라 dlc — fix, 바뀐 쪽 plan.
  - ⚠️ `-i` self-flag — accepted-risk: 리뷰어가 타당하다고 봤다(소문자 패턴이라 오히려 원래 동작을 지킨다). 더 그럴듯한 놓침(H3·굵은 글씨·단수)은 프롬프트 쪽 Deferred.
- 계획 리뷰 CONDITIONAL:
  - S1 변형 시험이 깨진 원본에서도 통과·SETUP·종료 코드 — fix(위 code-reviewer Major 와 같다).
  - S2 유일한 동작 변경(grep)을 확인하는 단계가 없다 — fix: [post-merge] Task·Acceptance 9.
  - S3 가장 위험한 단계가 없다(researcher 단위와 같은 지적) — fix(Decisions: 공통 검사, 다음은 grep).
  - W 생성기가 못 만드는 구조 변형(본문 들여쓰기·인용 사이 `**`·펜스 태그)이 PASS — fix: 들여쓰기를 줄 모양에, 펜스를 원문 고정에, 인용 밖은 줄 머리 목록 표시만, 생성 변형에 세 종류를 더했다.
  - W "검토 관점" 이 제목 "Review checklist" 와 프롬프트 "Review angles" 로 갈렸다 — fix: 둘 다 "Review checklist", terms.md.
  - W description 결정 줄 — fix(Decisions).
  - W 형식이 틀린 id — fix(위). W terms.md 표 — fix(위). W X.1·observed — fix(위).
- 반영 뒤: 공통 검사 PASS(조항 50, 핵심 문구 34), 변형 R 22/22·G swap 45/45·edge 120/120·blank 80/80·indent 11/11·fence 4/4·del 93/93. 머지된 commit-check·researcher 단위도 같은 공통 검사로 PASS·생성 변형 전부 FAIL(scratch 설정). 음성 시험: 깨진 원본 → exit 1, 빈 핵심 문구 → FAIL, 틀린 id → FAIL, no-op 변형 → SETUP·exit 1, CRLF 사본 → PASS.

# Deferred
- `scripts/bootstrap/test_sync_codex_agents.py` 의 `REMOVED` 가 한국어 "도메인 특화 프롬프트" 를 agent 소스 중 하나에서 찾는다 — 마지막 reviewer(code-reviewer·architecture-reviewer)를 옮기면 테스트가 깨진다. 그 단위가 같은 머지에서 고친다(terms.md). 심각도 중간 — 코드.
- plan-reviewer 의 Codex 프롬프트가 응답 제목 형식(`## Strong concerns` 등)을 정하지 않고, 공통 뼈대(`~/.claude/wiki/docs/codex-review.md` "Critical / Major / Minor 분류")와 다른 분류를 요구한다 — 추출 grep 이 비면 `tail -300` 으로 떨어진다. 원문부터. 심각도 낮음 — 규칙 변경, 별도 작업.
- 14항은 `없음 — <reason>` 만 다루고 CLAUDE.md §10 의 `no delta — <reason>`(묶음 plan)은 다루지 않는다 — 원문부터. 심각도 낮음 — 별도 작업.
- `~/.claude/wiki/docs/codex-review.md` 가 reviewer 보고 줄 `Codex 미가용: … out of credits` 를 정하고 dlc 가 그 글자로 한도 마커를 만든다 — 영어로 보고하는 reviewer 가 다른 말을 쓸 수 있다. 그 문서의 번역(translate-wiki-docs)이 정한다. 심각도 낮음.

# Workflow Findings
- 2026-10-27 공통 검사를 만든 첫 단위에서도 리뷰어가 검사 자체의 빈틈(원본 미확인·0개 PASS·종료 코드)을 찾았다 — 검사의 "스스로 실패를 알리는" 성질을 처음부터 요구 사항으로 두지 않았다. 대책: 공통 검사 머리 주석에 계약(원본 PASS 먼저·SETUP 실패·exit 1)을 적었고 음성 시험을 돌렸다.
