# Review Disposition

## 리뷰 4개 병렬 (2026-10-27, Codex 미가용) — 번역을 먼저 적용하고 계획 리뷰·독립 대조 2개·code-reviewer 를 함께 돌렸다
- 게이트 줄 대조: OK 30, WEAKER 1 — :30 "작성일" → "date" 가 검색한 날짜로도 읽힌다(:52 템플릿도) — fix: "publication date"(둘 다). 선택 문구 :29 문장 조각 → fix("Give version, …"), :3 명령형 → wontfix(호출 측 책임이 그대로 드러난다).
- 조항 대조 + manifest 감사: OK 전부, manifest 빠짐 0. T.6 인용이 제목 줄(1–2줄·대상 경로)을 덮지 않음 → fix: T.1~T.6 에 출력 절 제목을 첫 인용으로. P.2 의 `## Core mission` 은 제목이라 5절 면제 — wontfix(4절 제목 목록이 지킨다). 문구 메모 2개는 위와 같은 곳.
- code-reviewer APPROVE(Critical·Major 0):
  - Minor check-rs 가 새 제목·본문 `tools:`/`model:` 줄을 통과시킨다 — fix: frontmatter 면제를 1~6행만, 제목 줄 목록 정확 일치, 변형 시험에 세 사례.
  - Minor "date" — fix(위).
  - Minor 공용 wiki `pages/concept/plan-handoff.md:45` 도 "plan 반영용 요약" 을 적는다 — fix: manifest 가리키는 곳·terms.md·[post-merge] Task.
  - Minor terms.md 출처 목록이 모자란다 — fix(c·wt pointers·commit-check log·이 plan).
  - Nit terms.md 에 e 의 원문 유지 문자열(`wip:`·`(e checkpoint)`·`main-autopull ⓑ`·`M1~M6`)과 Task 문구가 없다 — fix.
  - Nit :29 — fix(위). Nit mut-rs 가 검사 스크립트가 죽은 것도 "잡았다" 로 센다 — fix: 출력의 `FAIL n` 이 있을 때만, 없으면 멈춘다.
  - Nit check-rs 가 base `b1e7042` 와 dlc 한 줄 변경에 묶여 rebase 뒤 재실행이 거짓 FAIL 할 수 있다 — wontfix(재실행 한정, 기록 파일).
- 계획 리뷰 CONDITIONAL:
  - S1 check-rs 가 Acceptance 1 이 말하는 것보다 적게 잡는다(출처 우선순위 줄 바꿔치기·단일/복수 출처 줄 바꿔치기·출력 절 본문 바꿔치기·새 제목·`tools:`/`model:` 줄이 PASS) — commit-check S2 와 같은 종류 — fix: 인용이 manifest 순서대로 나오는지, 제목 줄 목록 정확 일치, frontmatter 면제 1~6행, 인용 밖은 공백과 `-`·`*` 만. 변형 시험에 줄 바꿔치기 4개(S)와 새 사례 5개(B). Acceptance 1·4 문구를 바꿨다(Decisions).
  - S2 terms.md 에 앞 단위가 정한 원문 유지 문자열이 빠졌다(`## Codex 병행`(sync 스크립트가 글자로 찾는다)·e 의 네 개)·출처 목록 모자람 — fix.
  - S3 머지 뒤 `sync_codex_agents.py` 재실행 Task 가 없다(translate-claude-md W4 와 같은 지적) — fix: [post-merge] Task, 롤백 줄에도.
  - W "date" — fix(위). W 가장 위험한 곳·description 결정 줄이 없다 — fix(Decisions).
  - W 임시 한국어 이름을 언제 누가 지우는지 terms.md 에 없다 — fix: 원문 유지 표에 "agent 4개를 다 옮긴 단위가 지운다, dlc 를 먼저 옮기면 영어 dlc 도 따옴표를 남긴다".
  - W 공용 wiki 두 곳(plan-handoff·hub-and-spoke-isolation) — fix: [post-merge] Task 에 이름으로.
  - W agent 공통 절 제목·응답 언어 문장이 terms.md 에 없다 — fix. "동작 규칙" → "Rules" 는 유지(짧고 앞 단위 제목 관례와 맞다).
  - W Acceptance 4 의 "절 7개" 가 틀렸다 — fix: "본문 절 7개 + 출력 절 6개".
  - W Split 근거·롤백이 느슨하다 — fix: 롤백은 docs 커밋만 되돌린다(용어표 유지), Split 줄에 이유.
  - W terms.md 를 여러 세션이 고친다 — fix: append-only·충돌 시 두 줄 유지를 표 머리에.
  - W commit-check log 의 Deferred "묶음 공통 용어표" 를 이 단위가 풀었다 — fix: 아래 처리 기록.
  - W `sync_codex_agents.py` 의 Codex 머리말이 한국어라 생성 TOML 이 섞인다 — defer(Deferred).
  - W 5절이 글자만 본다(숫자·기호 삽입 통과) — fix: 인용 밖은 공백과 목록 표시만.
- 앞 단위 Deferred 처리: translate-skill-commit-check log 의 "묶음 공통 용어표" 는 이 단위에서 만들었다(`plans/2026-10-21-ops-docs-rework/terms.md`, intent Constraints 한 줄 — 사용자 2026-10-27). 그 log 는 done plan 이라 손대지 않는다.
- 반영 뒤: check-rs PASS(조항 26, 핵심 문구 23, 한글 0, 순서·제목 목록·인용 밖 0), 변형 S 4/4·A 18/18·B 13/13·문장 삭제 43/43.

# Deferred
- `scripts/bootstrap/sync_codex_agents.py` 의 Codex agent 머리말(41~45행)이 한국어라, 영어로 옮긴 agent 에서 만든 TOML 이 한국어 머리말 + 영어 본문이 된다. 심각도 낮음 — 코드라 translate-hooks 또는 별도 작업.

# Workflow Findings
- 2026-10-27 대조 검사가 Acceptance 가 말하는 것보다 적게 잡는다는 지적이 세 단위째(wt S1·commit-check S2·이 단위 S1) — 단위마다 검사 스크립트를 앞 단위에서 복사해 고치면서 새 단위의 구조(frontmatter 줄·출력 템플릿·순서 규칙)에 맞는 빈틈을 새로 만든다. 대책 후보: 공통 검사 스크립트 하나(manifest·locations·면제 목록을 인자로)를 묶음 폴더에 두기 — 이 단위 범위 밖, 다음 단위 착수 전 제안.
