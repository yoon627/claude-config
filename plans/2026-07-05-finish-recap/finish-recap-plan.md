---
title: finish-recap — 작업 마무리 recap+선택지 규약화 + hook 경고 대응 "결론 1줄" 규칙
status: done
started: 2026-07-05
updated: 2026-07-15
---

# Goal
① 작업(또는 세션)이 마무리될 때 마지막 메시지를 **"결론 요약(≤3줄) + 다음 선택지 제시(AskUserQuestion: 작업 확인 / 마무리+정리 / 다른 작업 이어가기 / 종료)"** 로 끝내는 것을 규약화. ② Stop hook 경고·오탐 대응은 **결론 1줄**("오탐 — 문서 변경뿐, 조치 불필요")로 제한 — 판단 과정 서술 금지, 근거는 plan/finding 에만 (2026-07-05 사용자 지시: "내가 다 읽어봐야 하잖아 — 결론 정리 부분이 필요해").

# Progress
- 2026-07-05: Fable 계획 세션 — 설계·수용기준 확정. 즉시 완화는 memory `report-conclusion-first`(주입 중). 구현은 opus.
- 2026-07-15: opus 구현 세션. `git rebase origin/main`(→102ec70, fast-forward). 편집 3건 완료 — CLAUDE.md:47(§3 step6 Report, 2문장: 결론≤3줄+선택지(+큰변경 리포트+퀴즈)+hook 1줄), skills/dlc/SKILL.md(16 Report recap 불릿), skills/e/SKILL.md(4단계 보고 recap 형식·중복 AskUserQuestion 회피). improve.sh error=0 warn=0. Codex(low) 정합 OK — Critical/Major/Minor 전무. README 미수정 판정(line 223 은 단계명 인덱스라 서술 불변).
- 2026-07-15 (opus, 이어서): 위 WIP(미커밋) 발견 → 커밋 `e05e569`. **README skills/e 절(line 294)에 recap 1줄 추가**(위 '미수정 판정' 정정 — prose 절은 별건, §3 doc-sync). 재검토(Claude code-reviewer + codex xhigh) → **Major/blocker 1**: e recap 이 "선택지는 step5 가 겸한다"는데 step5 는 조건부(done·plan-in-worktree)라 지배 경로서 안 뜸 → **fix**: §3-6 예외("/e=마무리 지시→선택지 생략")로 근거 교체. + dlc merged 시 "마무리·정리"=정리판정 명시(2차 질문 아님), CLAUDE §6 라벨 맥락화(dlc push/PR/머지·/e 정리)·skip 판정가능화(최신 메시지 명시 액션)·"plan 에만"→plan(+wiki)·이어가기=`/wt` 신규. improve.sh error=0.

# Next
편집·검증 완료(2026-07-15). 남은 것은 **머지 게이트에 묶인 2건** 뿐:
① **머지**(사용자 승인 필요 — §8 게이트): finish-recap → main. 승인 시 `gh pr` 또는 직접 머지.
② **memory 정리는 머지 후**(§12 "승격 *후* 정리"): 지금 삭제하면 CLAUDE.md 승격본이 아직 worktree 안(미머지)이라 live 전역 CLAUDE.md 는 main 것 → 규칙 공백 발생. 머지로 §3-6 이 live 된 뒤에만 `report-conclusion-first.md` + MEMORY.md 인덱스 줄(line 6) 삭제(중복 주입 방지).
③ 머지·정리 후 worktree 정리 제안(merged·clean 시).

# Decisions
- **recap 트리거**: dlc 16 Report 완료 시·/e 마무리 보고 시·명확한 작업 단위가 끝났을 때. 단순 질문/탐색 턴은 제외(마찰 방지).
- **선택지 형식**: AskUserQuestion 사용(옵션: 작업 확인(diff/검증 재확인) / push·PR·머지 진행 / 다른 작업 이어가기(대기 목록 제시) / 여기서 종료). 단 사용자가 이미 다음 지시를 준 흐름에선 생략(중복 질문 금지 — c 자동 진행(B)의 예외 정신과 동일).
- **hook 경고 대응 형식**: 결론 1줄 + 필요시 "근거는 <plan> 기록" 포인터. 오탐 분석·가설·경위는 사용자 메시지에 쓰지 않고 plan `# Workflow Findings` 에만. (이번 세션 실패 사례: 오탐 판정 서술을 매번 여러 문단으로 출력 → 사용자가 전부 독해해야 했음)
- **편집 대상 3건**: ⓐ CLAUDE.md §3-6 Report 에 "마무리 시 결론 요약+선택지, hook 대응은 결론 1줄" 2문장(§0 의례 금지와 정합 — 형식은 간결 유지) ⓑ dlc SKILL 16 Report 에 recap+선택지 1줄 ⓒ e SKILL 4단계 보고에 동일 1줄. doc-slim 슬림화 정신 위배 금지 — 각 1-2문장 이내.
- **경계**: recap 은 보고 형식이지 추가 단계가 아님(16단계 표 안 늘림). AskUserQuestion 남용 금지 — 마무리 시점 1회만.
- **[스코프 추가 2026-07-07] 선택지에 "변경 이해 리포트+퀴즈" 옵션**: recap 의 다음 선택지에 "변경 이해 확인(리포트+퀴즈)" 을 추가 — 선택 시 변경의 맥락·의도·동작을 설명하는 리포트와 확인 퀴즈를 제시(사용자가 통과해야 머지 진행 권장). 출처: Thariq "Finding Your Unknowns"(2026-07-04) Quizzes 기법 — 큰 diff 를 사용자가 빠르게 이해·검수하는 수단. 강제 아님(옵션) — 사용자가 이미 내용을 아는 소규모 변경에선 무의미하므로 큰/낯선 변경에서만 옵션 노출.
- **[2026-07-15] memory 정리는 머지 후로 순서 고정**: CLAUDE.md 승격이 실제로 live 되는 시점은 main 머지 시점(전역 주입되는 CLAUDE.md 는 main worktree 것). 미머지 상태에서 memory 를 먼저 지우면 규칙이 어디에도 주입 안 되는 공백이 생김 → §12 "승격 *후* 정리" 를 "머지 후 정리"로 구체화. (이 순서 판단 자체가 이번 세션 recap 규약이 요구하는 '근본 원인' 정합의 예.)
- **[2026-07-15] README 미수정 판정**: README line 223 은 §3 단계명 인덱스(Setup→…→Report)라 recap(=Report 단계 내부 상세)로는 서술이 어긋나지 않음. 문서 동기화 게이트(§3)는 정확성 요구지 상세 미러링이 아니므로 수정 불필요. (dlc-doc-drift hook 이 경고하면 오탐 — 결론 1줄로 대응.)

# Key Files
- CLAUDE.md §3-6(Report) — 결론-우선·선택지 규칙 2문장
- skills/dlc/SKILL.md 16 Report — recap+선택지 1줄 / skills/e/SKILL.md 4단계 — 동일 1줄
- projects/.../memory/report-conclusion-first.md — 규약 승격 후 정리(§12)
- README — 해당 절 서술 어긋나면 최소 동기화

# Blockers
- ~~doc-slim 머지 대기~~ **해소(2026-07-06)**: doc-slim #73 머지됨 — `git rebase origin/main` 후 즉시 착수 가능(대상 3파일이 슬림화됐으니 머지본 기준으로 절 위치 재확인).

# Acceptance
1. 3개 문서에 규칙 반영 diff 존재 + 문구가 "결론≤3줄·선택지·hook 1줄" 세 요소를 모두 명시.
2. 모순 없음 대조: §0(preamble 금지)·c 자동 진행 예외(중복 질문 금지)·dlc 16단계 표 불변.
3. memory 승격 처리(§12 유지 규칙 — 중복 주입 방지).
4. improve.sh error=0 · 기존 테스트 비회귀(문서만 — 확인).
5. 실측 grounding: 편집 후 세션에서 작업 1건 마무리 시 recap+선택지 형식이 실제로 출력되는지 관찰(구현 세션 자신의 마무리로 확인 가능).

# Review Disposition
(리뷰 후 기록)

# Workflow Findings
(발생 시 기록)
