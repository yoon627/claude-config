---
title: wt-ask-mode — wt 스킬에 접두 ? 질문 모드 추가
status: done
started: 2026-06-09
updated: 2026-06-10
---

# Goal
wt 스킬에 접두 `?` 트리거 '질문 모드' 추가. 막연한 요청을 AskUserQuestion 대화로 구체화한 뒤, 기존 request 경로(slug 확인→생성→dlc)로 합류시켜 worktree 를 생성한다.

# Progress
- 2026-06-09: 설계 확정(접두 `?`, 1순위안). `/wt` 로 wt-ask-mode worktree 생성·진입. Explore(SKILL.md / README 동기화 지점 식별).
- 2026-06-09: 구현 완료 — SKILL.md(frontmatter·인자 표·해석 순서 ②.5·새 '질문 모드' 섹션) + README(308 인자목록 / 313 해석규칙). code-reviewer 검토: Critical 0 / Major 2 fix / Nit 2 wontfix, 기존 5경로 회귀 없음 확인. 보완 반영. 비코드 markdown 이라 자동 검증 파이프라인 미존재 → 수동 파싱 시뮬레이션으로 검증.
- 2026-06-09 (/e): 변경 커밋 `c28ef02` (skills/wt/SKILL.md + README.md). tracked clean → 임시 커밋 불필요. unpushed·미머지 체크포인트, main 복귀.
- 2026-06-10 (/c·/e): 이 plan 이 worktree 의 `.claude/plans/`(nested)에 있어 /c·/e 탐색(`<ROOT>/plans/`)에서 누락 → 초기 "plan 없음" 오판. 사용자 "merge하고 /e" 지시로 `wt-ask-mode` push → PR #29 생성·머지(merge commit `fbb9739`), 로컬 main ff 동기화, origin `wt-ask-mode` 삭제. plan 을 main `plans/2026-06-09-wt-ask-mode/` 로 이전(보존) 후 worktree 정리. → status done.

# Next
- (없음 — PR #29 머지로 done)
- (선택, 후속) 질문 모드 실사용 후 AskUserQuestion 프롬프트 미세조정

# Decisions
- 트리거 = 접두 `?` (접미 금지: 의문형 요청과 충돌). 근거: slug 패턴 `^[a-zA-Z0-9._/-]+$` 에 `?` 없어 slug·worktree 이름과 충돌이 본질적으로 없음.
- 파싱 위치 = ② rm 다음, ③ 정수 앞(②.5). ⑤ 요청사항보다 반드시 앞이어야 `?...` 가 요청사항으로 새지 않음. 해석 순서는 '위에서부터 첫 매치 확정'(short-circuit)을 명문화.
- 동작 = 질문 모드는 '요구사항 확정' 앞단만 추가하고, 이후 기존 request(§1 slug→§5 dlc)를 100% 재사용 → 중복 없음.
- 질문 모드는 최소 1회 AskUserQuestion 으로 구체화; 끝까지 모호하면 request 로 넘기지 않고 더 묻거나 종료.
- 2026-06-10 발견(plan 위치 갭): 이 plan 은 worktree 의 `<ROOT>/.claude/plans/` 에 생성됐으나 /c·/e skill 은 `<ROOT>/plans/` 만 탐색 → worktree 작업 plan 이 누락(이번 세션 초기 "plan 없음" 오판의 직접 원인). 이번엔 main `plans/` 로 이전해 보존·해소. 근본 수정(별도 작업 후보): worktree 세션이 plan 을 `<ROOT>/plans/` 로 통일하거나, /c·/e·wt 탐색에 `<ROOT>/.claude/plans/` 추가.

# Key Files
- skills/wt/SKILL.md — frontmatter · 인자 표 · 해석 순서 · 새 '질문 모드' 섹션 (PR #29 머지됨)
- README.md:306-313 — wt 문서화 동기화 (PR #29 머지됨)

# Blockers
(없음)
