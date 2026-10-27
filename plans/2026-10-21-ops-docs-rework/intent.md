---
title: ops-docs-rework — 운영 문서를 규칙 손실 없이 짧게, 내부 문서는 영어로
status: open
started: 2026-10-21
updated: 2026-10-27
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
- 언어 정책의 행동 규칙은 CLAUDE.md §0 에 있다(language-policy 단위, 2026-10-26). agents 는 영어로 보고하고 메인이 한국어로 전한다.
- 따옴표·코드 안의 문구(출력 형식·예시·라벨·intent 상태 토큰)도 영어로 옮긴다(사용자, 2026-10-26 "전부 영어로"). 번역 전 한국어 파일 안에 들어간 영어 인용·형식 문자열은 "한 파일에 언어를 섞지 않는다"의 대상이 아니다(인용이다 — `Commit or push only when the user asks.` 선례). intent 상태 토큰은 `(not started)`·`(open)`·`(resolved)`·`(carried over → …)`·`dropped` 이다(translate-claude-md 가 열린 intent 의 토큰을 바꿨다, 사용자 승인 2026-10-26).
- 번역된 파일이 아직 한국어인 파일의 제목을 가리키면 영어로 옮기고, 그 파일을 번역하는 단위가 제목을 같은 영어로 맞춘다. 대응표는 `plans/2026-10-26-translate-claude-md/pointers.md` 의 "역방향 인용" 절(사용자, 2026-10-26).
- 번역 단위는 착수 때 `plans/2026-10-21-ops-docs-rework/terms.md`(공통 용어표 — 원문 그대로 두는 문자열·용어)를 읽고 따르며, 새로 정한 것은 그 단위의 머지에서 표에 더한다(사용자, 2026-10-27 — 앞 단위의 용어 결정이 넘어오지 않아 같은 리뷰 지적이 다시 나왔다).

# Out of scope
- README·코드 주석의 언어(사용자, 2026-10-20).

# Open questions
- 번역 범위 밖으로 남은 것: `wiki/pages`·repo wiki·plan log·`intent.md`(plan 파일은 한국어라는 사용자 결정에 들어가는지)는 정하지 않았다 — plan log·`intent.md` 는 한국어로 정함(language-policy, 사용자 확인 2026-10-26). `wiki/pages`·repo wiki 는 (open)
- 사용자에게 보이는 hook 문구(`permissionDecisionReason`·데스크톱 알림)는 한국어로 둘지 — 표시 방식을 확인한 뒤 translate-hooks 가 정한다 (open)
- 다른 머신의 `MEMORY.md`·memory 번역을 누가 언제 하는지 (open)
- language-policy 단위를 넣을 시점 — 번역 단계의 첫 단위로 둘지, 더 앞으로 당길지 (resolved) — 번역 단계의 첫 단위로 넣었다(2026-10-26)

# Plans
- plans/2026-10-18-plan-format/plan-format-plan.md — 선행(plan 형식 변경). 이 묶음의 작업 목록이 나온 곳
- plans/2026-10-20-remove-conclusion-block/remove-conclusion-block-plan.md — 답변 끝 결론 블록 규칙·hook 제거
- plans/2026-10-21-slim-rules-ko/slim-rules-ko-plan.md — CLAUDE.md 줄이기 + 근거 규칙 3개 + 모순 정리
- plans/2026-10-22-slim-skill-e-ko/slim-skill-e-ko-plan.md — skills/e 의 끊긴 참조 수정(압축은 사용자 결정으로 접음)
- plans/2026-10-26-language-policy/language-policy-plan.md — 언어 정책을 CLAUDE.md §0 에, agents 의 보고 언어를 영어로
- plans/2026-10-26-translate-claude-md/translate-claude-md-plan.md — translate-repo 의 첫 파일: CLAUDE.md 를 영어로, 같은 문구를 인용·공유하는 곳도 함께
- plans/2026-10-26-translate-skill-e/translate-skill-e-plan.md — translate-repo 의 두 번째 파일: skills/e
- plans/2026-10-27-translate-skill-c/translate-skill-c-plan.md — translate-repo 의 세 번째 파일: skills/c
- plans/2026-10-27-translate-skill-wt/translate-skill-wt-plan.md — translate-repo 의 네 번째: skills/wt(본문·references) — 여기서부터 대조에 덮이지 않은 구간 검사·문장 삭제 sweep 을 쓴다(그 plan log Workflow Findings)
- plans/2026-10-27-translate-skill-commit-check/translate-skill-commit-check-plan.md — translate-repo 의 다섯 번째: skills/commit-check — 대조는 인용 밖 글자 0 기준으로 강화(그 plan log)
- plans/2026-10-27-translate-agent-researcher/translate-agent-researcher-plan.md — translate-repo 의 여섯 번째: agents/researcher — 공통 용어표(terms.md)를 만든 단위, dlc 의 "plan 반영용 요약" 포인터를 두 이름으로
- translate-repo (not started) — skills(references·frontmatter description 포함)·agents 를 영어로, 파일별. 줄이기 단위가 모두 done 또는 폐기된 뒤. 각 줄이기 단위의 manifest 가 그 번역의 대조표
- translate-hooks (not started) — hook 주입 문구와 그것을 확인하는 테스트(코드라 medium 이상·TDD). 사용자에게 보이는 문구는 Open question 을 따른다
- translate-wiki-docs (not started) — `wiki/docs/` 를 영어로. 공용 wiki 라 main 세션에서, 그 문서를 가리키는 skill 의 번역과 순서를 맞춘다
- translate-memory (not started) — `MEMORY.md`·memory 를 영어로. gitignored 라 각 머신의 main 세션에서
