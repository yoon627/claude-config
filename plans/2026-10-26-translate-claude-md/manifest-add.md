# CLAUDE.md 조항 보충 (translate-claude-md)

`plans/2026-10-21-slim-rules-ko/manifest.md` 의 조항(317개, 그중 삭제 6개)에 그 뒤 CLAUDE.md 에 더해진 조항을 보탠다. 형식·등급은 그 manifest 와 같다. 번역 대조는 두 파일의 조항 id 를 합쳐 `locations-en.txt` 로 한다.

## §0 (language-policy, PR #242)
- 0.lp1 사용자에게 하는 답과 `plans/` 의 파일(plan·plan log·`intent.md`)은 한국어 — 인라인 → §0
- 0.lp2 그 밖의 내부(생각·subagent 지시와 보고·Codex 프롬프트와 응답·운영 문서 CLAUDE.md·skills·agents·hook 주입 문구·`MEMORY.md`·memory·`wiki/docs/`)는 영어 — 인라인 → §0
- 0.lp3 subagent·Codex 결과는 메인이 한국어로 전한다 — 인라인 → §0
- 0.lp4 운영 문서는 번역된 뒤부터 영어로 고치고 번역 전 파일은 그 파일의 언어로(한 파일에 언어를 섞지 않음) — 인라인 → §0
- 0.lp5 README·코드 주석은 이 정책 밖 — 인라인 → §0
- 0.lp6 이 문서가 인용한 라벨·템플릿·선택지 이름이 사용자 답에 나오면 한국어로 — 신규(번역으로 생긴 언어 쏠림 방지, translate-claude-md 독립 대조·code-reviewer) → §0
- 0.lp7 plan 파일의 표시(intent 상태 토큰·`[bundle]`·`NEEDS-HUMAN:`)는 고정 문자열로 그대로 — 신규(같은 리뷰) → §0
