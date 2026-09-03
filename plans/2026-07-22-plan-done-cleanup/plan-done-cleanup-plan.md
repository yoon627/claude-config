---
title: plan-done-cleanup — 완료 plan 을 merge 전 삭제하는 규약 (A 동기화 유지)
status: done
started: 2026-07-22
updated: 2026-09-03
---

# Goal
plans-sync 방안 A(plan tracked, 코드 브랜치와 함께 다머신 동기화)를 유지하되, 작업 완료 시 그 plan 을 **merge 전에** 삭제해 main 작업트리에 완료 plan 이 누적되지 않게 한다(방안 A 단점 ③ 해소).
- 진행 중: plan 이 작업 브랜치에 tracked → 다머신 `/c` 이어받기 유지.
- 완료 시: 재사용 지식은 wiki(§11)로 → plan 삭제 커밋 → git 이력엔 남아 복구 가능.

# Progress

- 2026-09-03: **wontfix 로 종료**(사용자 결정, PR #153). 구현 없음. 사유는 `# Decisions` 마지막 항목.
- 2026-08-20: worktree 정리. 구현이 전혀 없는 draft 라 **plan 만 main 에 squash 반영**하고 worktree·브랜치는 삭제했다 — 핵심 미결(삭제 타이밍)이 설계 결정이라 임의 착수하지 않았다. 재개 방법은 `# Next` 참조.
- 2026-07-22: Explore 완료. 상호작용 3종 검토 — ① `dlc-evidence-ledger.js` `isPlan`(L73-75)은 plans/ 경로를 evidence gate 에서 제외 + Edit/Write 만 잡아 **삭제(git rm)와 완전 무관** ② `guard-worktree-edit.js`(L107)는 main plans/ 편집·삭제 allow ③ `c` skill fallback(L26)은 in_progress|blocked 만 이어받기 대상 → **done 삭제와 무관**(삭제된 plan 은 매칭 실패=정상). 핵심 미결=삭제 타이밍(아래 Decisions).
- 2026-07-22 (/e): draft plan WIP 커밋 보존. 세션이 길어 체크포인트 — 새 세션 `/c` 로 plan-reviewer 부터 이어받기. 이 브랜치는 원격 미push(같은 머신 새 세션 전제; 다른 머신 이어받으려면 push 필요).

# Next

- 없음 (wontfix 종료). 완료 plan 누적이 실제 비용으로 드러나면 `# Decisions` 마지막 항목의 전제부터 재검토.

# Decisions
- **[2026-09-03 종료] wontfix — 삭제 규약 미채택**: `/e` 머지 모드(PR #148, wiki `e-merge-mode`)가 정착하면서 done 은 **머지 PR 에 실려 main 에 남는 것**이 규약이 됐다. 그 위에서 `/c`(done 정지 예외)·`session-brief`(닫히지 않은 plan 감지)·`improve.sh` plan-lint·wiki 승격 추적이 모두 main 의 plan 파일 존재를 전제로 동작한다. 삭제 지점을 M4 에 두면 7단계 정리 조건 2(plan done)·M2 지름길(plan done 판정)이 깨져 머지 모드를 다시 설계해야 하고, 얻는 것은 `plans/` 디렉토리 크기뿐이다. 완료 plan 이 실제로 마찰(탐색 비용·컨텍스트 주입)을 만들면 "삭제"가 아니라 "아카이브 디렉토리 이동"을 후보로 재검토.
- **[확정] A 채널 불변**: plans-sync 가 방안 B(별도 채널/main 제외)를 '동기화 망각 재발'로 비권장 → 동기화 메커니즘(작업 브랜치 tracked)은 안 건드린다. 완료 plan **수명만** 단축.
- **[핵심 미결] 삭제 타이밍 — "merge 되는 브랜치의 최종 상태에 plan 이 없어야" 함**:
  - **난제(이번 세션 실증)**: merge 가 done 확정(e)보다 **먼저** 일어나면(사용자가 gh 로 직접 merge 후 e) plan 이 이미 main 에 들어간 뒤라 삭제해도 소용없다. code-reviewer-absorb 가 정확히 이 case 였다(merge→후속 plan 커밋이 main 진입).
  - **후보 A (유력)**: 삭제를 **merge 전이 보장되는 지점**에 건다 = `dlc` 16 Report 또는 PR 생성 직전. dlc 는 merge 를 안 하므로 Report 시점은 항상 merge 전. done 확정 → wiki ingest 판정 → plan 삭제 커밋 → push → 그 브랜치를 PR/merge(최종 트리에 plan 없음).
  - **후보 B**: merge 후 main 에서 삭제 → §8 main 직접 금지 → 별도 정리 브랜치·2 PR 오버헤드. 비유력.
  - **미결 세부**(plan-reviewer/arch 대상): ① dlc Report vs e done 중 어디가 단일 삭제 지점인가(둘 다 done 확정 경로) ② merge commit 방식에서 "plan 추가 커밋들 + 삭제 커밋"이 이력에 남는 게 의도대로인가(복구 가능=OK) ③ PR 리뷰어가 최종 diff 에서 plan 못 보는 것 수용 가능한가(진행 중 plan 은 dlc 가 전달) ④ done 인데 미머지로 오래 남는 브랜치의 처리.
- **[확정] wiki ingest 선행**: 삭제 전 재사용 지식 wiki 판정(§11)은 필수 게이트 — 삭제로 지식이 유실되지 않게. (§11 은 이미 opt-in 판정 규약 — 삭제 규약이 이 판정을 강제 트리거로.)

# Key Files
- `CLAUDE.md §10` — plan 라이프사이클에 "완료 시 삭제(merge 전)" 규약 추가. "done 시점 즉시" 서술과 연계.
- `skills/e/SKILL.md` — done 확정(4단계)·worktree 정리(6단계) 근처에 삭제 단계. 순서: wiki 판정 → 삭제 커밋 → push.
- `skills/dlc/SKILL.md` — 16 Report 정리 판정에 완료 plan 삭제 연계(merge 전 지점).
- (상호작용, 변경 불요 확인됨) `scripts/dlc-evidence-ledger.js` isPlan · `scripts/guard-worktree-edit.js` · `skills/c/SKILL.md`.

# Blockers
(없음 — 삭제 타이밍은 미결이나 blocker 아님, plan-reviewer 로 확정)

# Acceptance
(2026-09-03 wontfix 종료 — 아래 항목은 **미달성 상태로 닫힘**. 재개 시 그대로 유효.)
1. **규약 문서화**: CLAUDE.md §10 + e + dlc 에 "완료 plan 을 merge 전 삭제" 규약이 일관되게 서술(삭제 지점·순서·wiki 선행). 검증: 세 파일 grep + 상호 모순 없음.
2. **merge 전 보장**: 규약의 삭제 지점이 실제로 merge 전임을 논증(dlc Report=merge 전 / e done=merge 전 조건). 검증: 흐름 서술이 이번 실증 난제(merge 선행)를 다룸.
3. **동기화 불변**: 진행 중 plan 은 여전히 브랜치 tracked·push(A). 검증: 규약이 A 채널을 안 바꿈 명시.
4. **wiki 선행 게이트**: 삭제 전 wiki ingest 판정이 규약에 명시. 검증: 문서에 존재.
5. **상호작용 무해**: isPlan/guard/c 가 삭제로 깨지지 않음(이미 검토). 검증: 회귀 없음 서술 + 필요시 evidence-ledger/guard 테스트 실행.
6. **문서 동기화**: README 의 관련 서술(plan 라이프사이클 언급 있으면) 갱신.
7. **리뷰 통과**: plan-reviewer + code-reviewer(+codex) 통과.

# Deferred
(없음 현재)
