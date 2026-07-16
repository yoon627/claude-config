---
title: unknowns-pass — dlc 에 unknowns 발굴 기법 3종 반영 (blind-spot·질문 우선순위·프로토타입-우선) + dead memory ref 정리 + 아티클 wiki ingest
status: done
started: 2026-07-07
updated: 2026-07-16
---

# Goal
Thariq(Anthropic Claude Code 팀) "A Field Guide to Fable: Finding Your Unknowns"(2026-07-04, x.com/trq212/article/2073100352921215386)에서 검증된 기법 중 현행 dlc 에 없는 3종을 소규모로 반영: ① blind-spot pass(낯선 영역에서 사용자의 unknown unknowns 브리핑) ② 명확화 질문 우선순위("답이 설계를 바꿀 질문 먼저") ③ 프로토타입-우선(취향/시각 산출물은 구현 전 저비용 변형 제시). + 같은 절의 dead memory 참조 정리 + 아티클 wiki ingest.

# Progress
- 2026-07-07: Fable 계획 세션 — 현행 대조(겹침/신규 판별)·설계 확정. 구현은 opus.
- 2026-07-16 (opus, 이어서): Blocker(cleanup-flow·finish-recap) 해소(#76·#79). rebase→main. 구현 — dlc 명확화 절 ①blind-spot·②질문우선순위·④dead ref 제거·③프로토타입-우선, router 주입, wiki 2페이지+index+log. 검증: 테스트4종·router 주입 관찰·wiki check_links clean·improve.sh error=0.
- 2026-07-16: code-review(Claude APPROVE + codex blocker) fix loop 1회 — (blocker) log.md dead-key 문자 제거(#3 0refs 달성) / (both) wiki 기법명을 원문 명명(Interviews·References·Mockups·Blind spot scans·Explainer&Quiz·Implementation Notes)으로 정정+References 추가+derived-repo 교차출처 / (both) 프로토타입-우선 grounding→명확화 절 이동 / (both) concept `[[feedback-memory]]` 오귀속→`[[dlc-development-cycle]]`. 재검증 all green.
- **⑥ grounding walkthrough (blind-spot)**: 모의 요청 "셰이더로 물결 효과 만들어줘"(낯선 render·사용자가 취향/제약 못 밝힘) → 새 규칙상 "어떤 물결?" 반복 대신 함정(성능·모바일·lib)·좋음 기준 후보(사실적 vs 스타일라이즈)·과거결정無 를 **브리핑 후 질문 재구성** — 규칙 텍스트가 이 흐름 지시함 확인(skill-text 라 런타임 아닌 walkthrough). Acceptance #5 improve.sh error=0(메인 실행)·#6 관찰 충족.

# Next
**착수 조건: worktree-cleanup-flow(4704fdc)·finish-recap 머지 후** (둘 다 skills/dlc/SKILL.md 편집 — rebase 후 시작). ① rebase → ② 아래 편집 4건 → ③ wiki ingest(2페이지+index+log) → ④ code-reviewer(문서 정합) → ⑤ improve.sh error=0 확인.

# Decisions
- **① blind-spot pass (dlc 명확화 절 +1~2줄)**: 조건부 — 요청 영역이 사용자에게 낯설다는 신호(사용자가 밝혔거나, 질문으로도 공백이 안 좁혀질 때)가 있으면, 질문을 반복하는 대신 **"이 영역에서 사용자가 모를 함정·좋음의 기준·과거 결정(wiki/코드)을 먼저 브리핑"** 하고 그 위에서 질문을 재구성한다. 현행 게이트의 공회전 지점(사용자도 답 못 하는 질문 반복) 보완. 기존 "≤2라운드" 안에서 수행(라운드 소모로 카운트) — 새 단계 아님.
- **② 질문 우선순위 (같은 절 +1줄)**: 질문이 여럿이면 **답이 설계/acceptance 를 바꾸는 것부터**, 필요 시 한 번에 하나씩(인터뷰식 — 사용자가 배치 질문에 부담을 보이면). 체크리스트 4항은 불변.
- **③ 프로토타입-우선 (router 주입 확장 + dlc 1줄)**: `dlc-task-router.js` 의 RENDER 매칭 주입문(`[dlc:grounding]`)에 사전 축을 추가 — "취향·시각 판단이 큰 산출물이면 **구현 전 저비용 변형 2~4종을 먼저 제시해 반응을 받는 것을 고려**(취향 발견이 구현 후로 밀리면 비쌈)". dlc verification grounding 절에도 같은 취지 1줄. **강제 아님(고려 제안)** — 모든 render 작업이 취향성은 아니므로 판단은 모델. router 문구 변경은 JS 문자열 1곳이라 기존 테스트 무영향(주입 문자열 assert 하는 테스트 없음 — 확인 필요).
- **④ dead memory ref 정리**: `skills/dlc/SKILL.md:45` 의 "(memory `feedback-analyze-before-asking` 와 짝)" — 해당 memory 파일 부재(2026-07-07 확인). 규칙 본문("무엇 빠지면 질문, 방법 갈리면 추천")은 SKILL 에 이미 자체 서술돼 있으므로 **참조 괄호만 제거**(memory 재생성 불요 — §12 승격·정리 과정의 잔재로 추정, 이력은 git).
- **⑤ wiki ingest**: `pages/source/fable-field-guide-unknowns.md`(아티클 1:1 요약, sources=URL) + `pages/concept/unknowns-discovery.md`(4분면 taxonomy + 기법→dlc 매핑: interviews=명확화 게이트, deviations=§10 동기화, blind-spot/프로토타입/퀴즈=이번 반영) + index/log 갱신. WIKI.md 규약 준수(≥2 outbound 링크·frontmatter). 이미 커버된 기법(References·implementation-notes)은 concept 페이지에 "현행 대응" 표로만.
- **반영 안 함 (판정 사유)**: Pitches/explainers(개인 repo — buy-in 대상 없음), "plan 에서 바뀔 결정 앞세우기"(§10 6섹션 구조와 충돌 — # Decisions·AskUserQuestion 승인 흐름이 이미 결정 지점을 노출, 이득 대비 구조 변경 큼 → wontfix, concept 페이지에 기법으로만 기록), 퀴즈(→ finish-recap plan 스코프로 분리 — 같은 아티클 출처 명기).

# Key Files
- skills/dlc/SKILL.md — 명확화 절(①②④)·verification grounding 절(③ 1줄)
- scripts/dlc-task-router.js — RENDER 주입문 확장(③)
- wiki/pages/source/fable-field-guide-unknowns.md(신규)·wiki/pages/concept/unknowns-discovery.md(신규)·wiki/index.md·wiki/log.md
- README — dlc·router 서술 어긋나면 최소 동기화

# Blockers
- worktree-cleanup-flow(dlc SKILL step16 편집, 커밋 4704fdc 미머지)·finish-recap(dlc Report 편집 예정) — 머지 후 rebase 하고 착수. 순서: cleanup-flow → finish-recap → 이 작업.

# Acceptance
1. dlc 명확화 절에 ①②가 각 1~2줄로 반영되고 기존 체크리스트·2라운드·silent 원칙 불변(diff 대조).
2. router RENDER 주입문에 사전 프로토타입 제안 축 존재 + `node --check` 통과 + 기존 테스트 3종 비회귀 + stdin 주입으로 새 문구 출력 관찰.
3. `feedback-analyze-before-asking` 참조 0건(`git grep`).
4. wiki 2페이지 신규 + index/log 갱신 + `/wiki lint`(check_links.py) 통과 — outbound ≥2·orphan 없음.
5. improve.sh error=0 · README 정합.
6. 실측 grounding: 편집 후 낯선 도메인 요청 시나리오 1건에서 blind-spot 브리핑이 실제 발동하는지 관찰(구현 세션이 모의 요청으로 확인).

# Review Disposition
(리뷰 후 기록)

# Workflow Findings
(발생 시 기록)
