# Review Disposition
- 게이트 대조·조항 감사 — 145줄 "In a repo without a remote, on its default branch and on an unborn HEAD" 가 unborn HEAD 까지 "원격 없는 repo" 로 묶는다(코드 `resolve_base` 는 unborn HEAD 를 어느 repo 에서나 조용히 넘긴다) — fix: "On the default branch of a repo without a remote, and on an unborn HEAD"
- 게이트 대조·조항 감사·code-reviewer — 147줄 "the closed modes" 가 영어 독자에게 뜻이 없다(원문 "닫힌 모드" 도 정의 없음) — fix: "the other modes (all but `--stop-hook`)", 근거 `wiki_check.py` git 실패 처리 docstring. 원문 명확화라 사용자 diff 확인 대상
- 게이트 대조·조항 감사 — 142줄 "does not block stopping with exit 2" 가 두 갈래로 읽힌다 — fix: "does not exit 2 (so stopping is not blocked)"
- 게이트 대조·조항 감사 — 68줄 "the original value is kept" 의 값이 무엇인지 불명 — fix: "the exit code is the usual one"
- 게이트 대조 — 31줄 제목 "shared-wiki ingest work" 가 "공용 적립 작업" 보다 좁다(47줄 "shared-wiki entry"·CLAUDE.md §11 과도 다름) — fix: "everything that a shared-wiki entry publishes"
- 게이트 대조(선택) — 12줄 "Otherwise" 가 바로 앞 rg 문장에 붙어 읽힐 수 있음 → "If it is false", 40줄 "Push on request." → "Push only on request."(CLAUDE.md §8), 152줄 "No assertions without evidence or speculative pages" → "No unsupported assertions and no speculative pages" — fix
- 조항 감사 — 85줄 "publishing" → "public check"(83줄과 같은 뜻), 90줄 YAML 주석 문장이 값 자체를 주석이라 함 → "In a value, as in YAML, everything from a `#` after whitespace is a comment."(code-reviewer 도 지적), 106줄 "closes" → "must close"(요구), 107줄 "an ending `/` and a `\`" → "ends with `/` or contains `\`", 113줄 "Moving one line" → "Carrying one line of value over"(47·137줄과 같은 동사, plan-reviewer N1 도), 141줄 "What to keep" → "Rules to follow", 144줄 "The output is nothing·…" → "one of: none, …", 38줄 "it is not git" → "the directory is not a git repo"(CLAUDE.md §11), 88줄 "outside that" → "elsewhere", 86줄 "same value as schema" → "same verdict", 61줄 첫 줄 문장 순서, 27줄 "(empty)" → "(no argument)", 109줄 "can move to" → "can be carried over to" — fix
- 조항 감사 — manifest L.6 에 "그 wiki 가 답해야 하는 질문마다" 누락 — fix. 핵심 문구 누락(`[ … ]`·"wiki_check stale: …"·숫자) — fix(196 → 204). 나머지 식별자(fnmatch·BOM 등)는 wontfix — 위치 인용이 문장 전체를 덮어 글자가 고정된다
- 조항 감사 — 31줄 제목의 범위("공용 적립 작업이 공개하는 모든 것")를 담은 조항이 없다 — wontfix: 제목 줄은 check.json `headings` 가 글자 그대로 고정한다
- code-reviewer — `[공용]`·`check_links: 읽기 실패` 에 첫 등장 영어 뜻이 없다(plan Constraints 위반) — fix: `[공용]` (shared), "…<reason>`, a read failure)"
- code-reviewer — R 변형에 stale 판정 규칙(옛 형식 위반·모르는 판 exit 2·공용 write 의 공개 점검)이 없다 — fix: R 3개 추가(33 → 36)
- plan-reviewer S1·code-reviewer — 공용 wiki `WIKI.md` 61줄 "(절차는 `skills/wiki/SKILL.md` 공개 점검)" 이 바뀐 제목을 가리킨다 — fix: post-merge Task 에 이름을 적고 main 세션에서 "Public check" 로(같은 줄의 CLAUDE.md §11 이름도)
- plan-reviewer S2 — Acceptance 6 이 "신선도 절" 만 검색해 intent Constraints(바꾼 표지 전부 검색)에 못 미친다 — fix: 바뀐 절 이름·라벨과 유지한 표지를 repo·공용 wiki 에서 검색하고 처분(검색 결과: `WIKI.md` 61줄만 고칠 곳, "query 1단계"·"Python" 은 그대로 맞음, 나머지 걸린 곳은 다른 skill 의 같은 낱말). Acceptance 문구 변경이라 사용자 승인 대상
- plan-reviewer S3 — 템플릿 제외 사유가 약하고 추적이 plan log 뿐 — fix: 사유를 코드·테스트 결합(`test_template_smoke_example_is_valid_once_uncommented`, 템플릿 51줄 한국어 정규식 예시)으로, 분류를 intent `# Open questions` 에 열었다
- plan-reviewer S4 — 34줄 "(CLAUDE.md §1 publishing externally)" 가 CLAUDE.md §1 영어("publicly visible")와 다름 — fix + terms.md 줄 추가
- plan-reviewer N2 — 롤백이 post-merge 공용 wiki 수정을 덮지 않음 — fix: `# Decisions` 롤백 줄에 추가
- code-reviewer — 그 밖의 확인(출력 글자 11개가 스크립트와 글자 그대로 맞음, 수치·플래그 주장이 코드와 맞음, `wiki_check.py` 변경은 문자열 4곳뿐) — 처분 불필요

# Deferred
- 공용 wiki `WIKI.md` 61줄의 "CLAUDE.md §11 공개 점검" — CLAUDE.md 번역 단위가 남긴 한국어 이름. 이 단위의 post-merge 수정 때 같은 줄이라 함께 고친다(심각도 낮음)
