---
title: worktree-cleanup-flow — merge/done 후 worktree 정리 handoff gap 수정
status: done
started: 2026-07-05
updated: 2026-07-05
---

# Goal
작업 worktree 가 main 에 merge/done 됐을 때 **정리(worktree+로컬·원격 브랜치)가 자동으로 트리거되도록** 워크플로우를 잇는다. 현재는 dlc(작업)·수동 merge·e(정리)가 분리돼 handoff 가 없어, Report 에서 멈추면 worktree 가 방치된다(gwl-zsh-wt-main 에서 실제 발생, 사용자 2회 지적).

세 지점 수정 후보:
1. `skills/dlc/SKILL.md` — 완료(merge/done) 시 `/e`(정리 제안)로의 handoff 명시.
2. `skills/e/SKILL.md` step5 — **원격 브랜치** 삭제 옵션 추가(현재 worktree+로컬만).
3. PR 머지 기본값 — `gh pr merge --delete-branch` 로 원격 자동 정리(문서화/규약).

# Progress
- 2026-07-05: worktree 생성(base 18f2b07). plan-only 요청. 근본원인은 gwl-zsh-wt-main plan `# Workflow Findings` + feedback memory `worktree-cleanup-after-merge` 에 기록됨. 본 plan 은 그 구조적 수정 설계.
- 2026-07-05: 구현 착수(사용자 "거기서 해"). Open Questions 해결(아래) → 구현: CLAUDE.md §8 정리 규칙+`--delete-branch`(Q4), skills/e step5 원격 옵션③+실행(Q3), skills/dlc step16 정리 판정 참조(Q1=b·Q2=both), README e 옵션 동기화. + (정합 발견) skills/wt rm 도 원격 옵션 추가(e 의 "wt rm 과 동일 옵션" 유지 + 같은 gap 이 wt 경로에 안 남게). 5파일. 다음: code-review.
- 2026-07-05: code-review(Claude REQUEST CHANGES + codex, blocker2+major3 수렴) → fix loop 1회: §8 `--delete-branch` 스코프+트리거 정합, e 경계 원격삭제 금지 추가, wt step4 merged 탐지, e option③ "안전" 완화, dlc 정리판정을 wiki연계→핵심규칙(무조건) 이동. disposition 기록. 재검증 통과(정합 grep·dlc 배치·improve.sh error=0)·커밋 `4704fdc`(5파일). status in_progress(미머지).
- 2026-07-14: (9일 경과) main 이 CLAUDE.md/dlc/e/wt 를 재작성(#74·docs 슬림)해 `4704fdc` stale·머지 불가 → stale worktree/브랜치 폐기, **동일(2리뷰+fix loop 통과)텍스트를 현재 main 위 `cleanup-rule` 브랜치에 재적용**(anchor 4/5 무손상·#74 정합). improve.sh error=0. **머지 #76 (`ff40ec8`)** → worktree·로컬·원격 정리 완료. **done**.

# Next
(구현·2리뷰·fix loop·검증·커밋 `4704fdc` 완료. 남은 것은 사용자 액션)
1. push/PR → merge (`gh pr merge --delete-branch` — 이 변경이 정한 규약대로).
2. merge 후 이 worktree 정리(§8 신규 규약대로 능동). ①review-intake(`30fe13c`)도 함께 미머지 — 둘 다 정리 대상.
3. merge 후: feedback memory `worktree-cleanup-after-merge` 가 §8 로 승격됐으니 §12 대로 memory 슬림화 판정.

# Decisions
- 범위: **운영 자산(skills) 수정** → 비trivial, 이 worktree 에서 진행. gwl 작업과 무관하므로 별도 브랜치(정상).
- feedback memory 는 이미 적립됨(내 행동 교정). 본 작업은 **구조적 방지**(Codex·다음 세션 전체에 걸쳐) — memory 와 상보.
- dlc 는 merge 를 직접 안 한다(merge 는 수동/외부). 따라서 handoff 트리거는 "dlc 종료"가 아니라 **"merge/done 확정 시점"** 이어야 한다 → dlc step16 은 *제안*만, 실제 정리는 `/e` 또는 `wt rm` 이 담당(소유권 분리 유지).

# Open Questions (plan-review/사용자 결정 대상)
- **Q1 dlc handoff 형태**: step16 에서 (a) `/e` 를 자동 invoke 할지 vs (b) "merge/done 이면 `/e` 로 정리하라" 제안 문구만 넣을지. → (b) 권장(자동 invoke 는 dlc 종점 동작을 무겁게·사용자 통제 약화). 단 "제안 문구"가 silent 지침이면 또 놓칠 수 있음 → self-diagnosis/Report 체크리스트에 bind 하는 방안 검토.
- **Q2 트리거 시점**: dlc 는 merge 를 안 보므로, 실효 트리거는 ① 에이전트가 직접 merge 수행한 직후, ② plan `status: done` 전환 시점. 둘 다 커버할지, 어디를 단일 소스로 할지.
- **Q3 e step5 원격 옵션**: AskUserQuestion 옵션을 ①worktree만 ②+로컬 ③+로컬·원격 ④취소 로 확장. 원격 삭제 안전조건(이미 merged=조건5 재사용) + `git push origin --delete` (없는 원격이면 skip). §8 명시 확인 유지.
- **Q4 proposal 3 위치**: `gh pr merge --delete-branch` 기본화를 어디에 규약화? CLAUDE.md §8(git) vs 별도 PR 머지 가이드. 전역 강제 vs 권장.
- **Q5 중복 방지**: dlc·e·CLAUDE.md 에 정리 규칙이 흩어지면 또 drift. 단일 소스(예: e step5)를 정본으로 하고 dlc/CLAUDE 는 참조만 할지.

**해결 (2026-07-05, 사용자 승인 "CLAUDE.md §8 + skills 참조")**: Q1=b(자동 invoke 안 함 — 제안 문구 + dlc step16 참조). Q2=both(에이전트 merge 직후 ∧ status→done — 규칙이 §8 단일 소스라 트리거 시점 무관하게 적용). Q3=구현(e step5 옵션③ 원격 + 실행). Q4=CLAUDE.md §8. Q5=**CLAUDE.md §8 이 정본**(항상 주입·강제), dlc step16·e step5·README 는 참조/실행 담당.

# Acceptance (구현 시 — 지금은 미도출 확정 아님)
- A1 정리 handoff 가 **정본 CLAUDE.md §8 + dlc 핵심규칙(무조건·wiki 무관) + e step5 실행**에 존재·정합(리뷰·정독 확인). 런타임 트리거 실관찰은 inherent future(정적으론 문구·walkthrough — 다음 실작업에서 관찰).
- A2 e step5 AskUserQuestion 에 원격 브랜치 옵션 + 안전조건 존재. 가능하면 시나리오 walkthrough.
- A3 proposal3 규약 위치 확정·기록.
- A4 문서 동기화: 변경한 skill/CLAUDE.md 섹션이 README 문서화 표면과 어긋나면 README 동기화(§3 acceptance).
- 주의: skills 는 markdown 스펙이라 자동 test 불가 → 검증은 정독+시나리오 walkthrough+다음 실작업 관찰(수동 절차 명시).

# Key Files
- `skills/dlc/SKILL.md` — step16(Report) 종점, 정리 단계 없음(추가 대상). "structural 전체 파이프라인" 표.
- `skills/e/SKILL.md` — step5 "worktree 정리 제안"(원격 옵션 추가 대상), AskUserQuestion 옵션·안전조건 5·6.
- `skills/wt/SKILL.md` — `rm` 섹션(정리 옵션의 다른 진입점 — 일관성 참조).
- `CLAUDE.md` §8(git·worktree 삭제 주의 :128), §3(dlc 흐름) — proposal3·handoff 규약 후보 위치.
- `~/.claude/projects/.../memory/worktree-cleanup-after-merge.md` — 이미 적립된 feedback(행동 교정 축).

# Blockers
(없음 — 방향/범위 확정은 Open Questions 로 plan-review·사용자 결정 대기)

# Review Disposition
(2리뷰 REQUEST CHANGES 수렴 — fix loop 1회로 전부 fix)
- §8 자기모순(`--delete-branch` 기본 ↔ 원격삭제 확인금지) → **fix**: 머지지시 포함=`--delete-branch`, 독립경로는 Ask + 트리거를 "merged·완료"로 정합.
- e 경계(line99) 원격삭제 금지 열거 누락(실행 주체 outlier) → **fix**: 원격삭제 추가.
- wt rm merged 게이트 부재·"미머지" 경고 근거 없음 → **fix**: step4 에 merged 탐지 추가.
- e option③/실행 "원격 안전 삭제" 과장(조건5 확정 아님) → **fix**: "확정 아님·Ask 전제"로 완화.
- dlc "정리 판정"이 "wiki 연계"(wiki 없으면 no-op) 아래 → **fix**: 핵심규칙(무조건)으로 이동.
- e④유지 vs wt④취소 라벨 · `--delete-branch`↔e 탐지 상호작용 → **관찰**: 기능 동일·merge-commit repo 무해(Claude walkthrough 확인).
- handoff hard-enforcement(dlc-early-stop bind) 미적용 → **wontfix(설계)**: Q1=b propose-only 의식 채택, §8 always-inject 가 완화. 잔여리스크로 남김.
