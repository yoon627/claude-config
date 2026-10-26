---
title: ops-docs-rework — 운영 문서를 규칙 손실 없이 짧게, 내부 문서는 영어로
status: open
started: 2026-10-21
updated: 2026-10-24
---

# Problem
CLAUDE.md(268줄·49,942B)·skills·agents 가 길고 읽기 어렵다(사용자, 2026-10-19 "shorter and simpler"). 답변 끝의 정해진 결론 블록도 답을 길게 만들었다(사용자, 2026-10-20). 언어 정책도 바꾸기로 했다 — 사용자에게 하는 답과 plan 은 한국어, 그 밖의 내부 문서와 subagent 지시·보고는 영어(사용자, 2026-10-20). 작업 목록은 `plans/2026-10-18-plan-format/plan-format-log.md` 의 Deferred "다음 작업" 에서 나왔다.

# Proposed outcome
CLAUDE.md·skills·agents 가 같은 규칙을 더 짧게 담고, 그 다음 영어로 옮겨진다. 사용자에게 보이는 것(답·plan)은 한국어로 남는다.

# Constraints
- 규칙 손실 0 이 hard gate, 줄 수·바이트는 보조 목표(wiki [[ops-doc-slimming]], 사용자 확인 2026-10-21).
- 안전·트리거 규칙은 CLAUDE.md 에 명령형 1줄 + 세부 위치를 남긴다(로드 등급 보존). §10 은 옮기지 않는다.
- 줄이기는 한국어로 먼저, 영어 번역은 그 뒤 따로 한다(사용자, 2026-10-20). 이유: 규칙 손실 대조(manifest)는 같은 언어 안에서만 줄 단위로 할 수 있다. 줄이기는 CLAUDE.md 에서 멈춘다(사용자, 2026-10-24): CLAUDE.md 는 −3.5% 였고, 남은 skills·agents 는 push·머지·삭제 게이트가 많아 이득이 작은데 영어로 옮기면 같은 내용이 약 22% 짧다(§1 실측 1,650 → 1,292 토큰). 그래서 번역 단위가 파일마다 조항 manifest 를 만들어 언어를 넘는 손실을 대조한다(CLAUDE.md·skills/e 의 manifest 는 이어받는다).
- 파일별로 나눠 머지한다(7월 PR #89~92 선례). 규칙·스킬 문구 변경은 커밋 전에 사용자가 diff 를 확인한다.
- 이력·실측 메모(버전 번호·측정값·"재현"·"선례")는 문서에서 지우고, wiki 에 없는 것만 main 세션에서 wiki 에 적는다(사용자, 2026-10-21). 단 규칙이 적용되는 시점을 정하는 날짜("2026-09-16 이후 새로 만든 plan 부터", "2026-10-18 이전 형식")는 규칙이라 남긴다 — 지우면 옛 plan 에 소급된다.
- 다른 파일이 가리키는 표지는 그대로 둔다: CLAUDE.md 절 번호, skill 단계 번호와 M 코드, agent 항목 번호, 다른 파일이 따옴표로 인용하는 제목·라벨. 각 단위의 Acceptance 는 자기가 바꾼 표지를 가리키는 곳을 전부 검색한다. 인용된 라벨은 줄일 때 글자 그대로 두고, 번역할 때는 가리키는 쪽과 같은 머지에서 옮긴다.
- 어떤 단위가 지운 세부의 "새 위치"가 다른 파일이면, 그 파일을 줄이는 단위의 manifest 에 "유일한 사본 — 지우지 않음" 으로 넘긴다(가리키는 쪽끼리 서로 가리키며 규칙이 사라지는 것을 막는다).
- 묶음이 열려 있는 동안 CLAUDE.md·skills·agents 를 고치는 다른 plan(예: `read-points`)은 그 파일의 줄이기 단위보다 먼저 머지하거나 그 위로 rebase 한다. 번역이 끝난 파일에 더하는 문구는 영어로 쓴다.
- 언어 정책의 행동 규칙(subagent 지시·보고는 영어)은 아직 어떤 규칙 문서에도 없다 — agents 의 "응답 언어 — 한국어" 와 Codex 프롬프트의 "응답: 한국어" 가 그대로다. language-policy 단위가 머지되기 전까지 subagent 에 영어 보고를 요청하는 것은 사용자 지시(2026-10-20)에 따른 의도된 예외다.

# Out of scope
- README·코드 주석의 언어(사용자, 2026-10-20).

# Open questions
- 번역 범위 밖으로 남은 것: `wiki/pages`·repo wiki·plan log·`intent.md`(plan 파일은 한국어라는 사용자 결정에 들어가는지)는 정하지 않았다 (열림)
- 사용자에게 보이는 hook 문구(`permissionDecisionReason`·데스크톱 알림)는 한국어로 둘지 — 표시 방식을 확인한 뒤 translate-hooks 가 정한다 (열림)
- 다른 머신의 `MEMORY.md`·memory 번역을 누가 언제 하는지 (열림)
- language-policy 단위를 넣을 시점 — 번역 단계의 첫 단위로 둘지, 더 앞으로 당길지 (열림)

# Plans
- plans/2026-10-18-plan-format/plan-format-plan.md — 선행(plan 형식 변경). 이 묶음의 작업 목록이 나온 곳
- plans/2026-10-20-remove-conclusion-block/remove-conclusion-block-plan.md — 답변 끝 결론 블록 규칙·hook 제거
- plans/2026-10-21-slim-rules-ko/slim-rules-ko-plan.md — CLAUDE.md 줄이기 + 근거 규칙 3개 + 모순 정리
- plans/2026-10-22-slim-skill-e-ko/slim-skill-e-ko-plan.md — skills/e 의 끊긴 참조 수정(압축은 사용자 결정으로 접음)
- language-policy (미착수) — 행동 변경: §0 에 언어 정책, agents 의 응답 언어 줄, Codex 프롬프트. 별도 커밋으로 리뷰
- translate-repo (미착수) — CLAUDE.md·skills(references·frontmatter description 포함)·agents 를 영어로, 파일별. 줄이기 단위가 모두 done 또는 폐기된 뒤. 각 줄이기 단위의 manifest 가 그 번역의 대조표
- translate-hooks (미착수) — hook 주입 문구와 그것을 확인하는 테스트(코드라 medium 이상·TDD). 사용자에게 보이는 문구는 Open question 을 따른다
- translate-wiki-docs (미착수) — `wiki/docs/` 를 영어로. 공용 wiki 라 main 세션에서, 그 문서를 가리키는 skill 의 번역과 순서를 맞춘다
- translate-memory (미착수) — `MEMORY.md`·memory 를 영어로. gitignored 라 각 머신의 main 세션에서
