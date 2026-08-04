---
title: auto-cleanup-after-merge — 내가 직접 수행한 merge 직후 안전조건 충족 시 정리 자동화
status: done
started: 2026-07-21
updated: 2026-07-26
---

# Goal
**내가(에이전트) 이 세션에서 직접 수행/확인한 merge 직후**, 대상이 안전조건(비-main/보호브랜치·clean·fetch 후 remote-ahead 없음·base 에 merged·산출물 안전) 충족이면 worktree+로컬+원격 브랜치를 **확인 없이 자동 정리**하고 결과(삭제 tip sha 포함) 1줄 보고. 우연히 머지된 브랜치·`/e`·`wt rm` 독립 정리, 또는 안전조건 미충족/불확실이면 **기존 AskUserQuestion 유지**(데이터 유실 방지). 리뷰어 CONDITIONAL GO 설계. 순수 문서/정책 변경.

# Progress
- 2026-07-21: wt→dlc 진입, Explore 완료(대상 CLAUDE.md:120·e·dlc·wt). plan-review(+codex) 가 원안(머지 후 항상 원격 자동삭제) NO-GO 판정 — remote-ahead 단방향 unpushed 미탐지·human-gate 소멸 등 데이터 유실 구멍 → 옵션1(self-merge 한정+fetch 양방향) 재설계, 사용자 확정.
- 2026-07-22: 옵션1 로 6파일 편집 완료 — CLAUDE.md §8(a)/(b) anchor, dlc:120·e:46·wt:122·docs/worktree-lifecycle.md:5 cross-ref, README:300 동기화(§3). 자체검증: 5개 구멍(remote-ahead·remoteContainingHead·PR-uncheck·human-gate·rollback) 각 구현 텍스트와 1:1 대조로 닫힘 + /e·wt rm over-reach 명시 배제. 확정 재리뷰는 API 세션 한도로 실패(리뷰 결과 아님) — 설계는 plan-review CONDITIONAL GO, 구현은 충실한 전사.
- 2026-07-25: /e 마무리 — 정식 커밋 `724b8b9`(7파일, wip 아님·완료 상태). working tree clean.
- 2026-07-26: `origin/main` merge(`eefb6b0`) — 예고된 충돌 1건 실현. **#98 이 `/e` 에 worklog 를 step5 로 삽입해 worktree 정리가 step6 으로 재번호** → 충돌(skills/e/SKILL.md)은 main 구조 채택 + 이 브랜치의 "§8(b) 독립 정리라 항상 ask" 문구를 step6 본문에 반영으로 해결. 이 브랜치가 추가한 step5 참조 2곳(CLAUDE.md:124·dlc:120) → step6 정정. 검증: plan-lint exit=0 · settings.json parse OK · `node --test scripts/*.test.js` 8파일 전건 pass · 충돌 마커 0(shellcheck 는 변경이 전부 `.md` 라 생략).

- 2026-07-26: **PR #102 머지 완료 → `status: done`.** §8(a) 자동 정리 첫 실적용 결과(실관찰):
  - `plan-status-sync` worktree — 조건 ②~⑥ 전부 충족 → **확인 없이 자동 정리** 성공(worktree→로컬 `branch -d`→원격 `push --delete`), 삭제한 원격 tip sha `eb874b9` 보고.
  - 이 worktree(`auto-cleanup-after-merge`) — ⑥ 에서 ignored `.codegraph/` 검출 → **fail-safe 로 (b) 경로 이탈 → AskUserQuestion** 후 정리. 설계 의도대로 동작(재생성 가능한 인덱스 캐시라도 자동 판정은 보수적으로 멈춘다).
  - 즉 (a)/(b) 분기가 양쪽 모두 의도대로 갈렸다.
- 2026-07-26: **이 plan 자체가 §10 위반 사례가 됐다** — 머지(#102) 직후 `status: done` 전환을 빠뜨려 반나절 `in_progress` 로 남았고, 같은 날 만든 탐지 신호(PR #105 `stalePlanLine`)의 첫 실검출 대상이 될 상태였다. 발견 경로: PR #105 구현 중 실환경 실행 관찰 + plan-reviewer 지적("살아 있는 5번째 누락"). 소급 정리(#103)와 동일 원인 — 머지 시점에 plan 을 닫을 주체가 없다.

# Next
(없음 — 완료)

# Chosen Design (옵션 1, 2026-07-21 사용자 확정)
**auto FULL cleanup(worktree+로컬+원격, 무확인) 트리거 = 아래 전부 AND:**
1. 이 세션에서 **내가 직접 수행/확인한 merge** 직후(정리 의도가 fresh·user-directed — `gh pr merge --delete-branch` 와 동류 authorization).
2. 대상 브랜치 ≠ 기본/보호 브랜치(main·master·`origin/HEAD`).
3. working tree clean(untracked 포함).
4. **`git fetch origin <branch>` 후 remote-ahead 없음**: `git rev-list <branch>..origin/<branch>` 비어야(원격전용 커밋 없음 — 단방향 collect-state 갭 보완).
5. **base 에 merged**: fetch 후 `git rev-list origin/<default>..<branch>` 빔(전 커밋 base 포함; squash→안 빔→auto 아님→ask, 안전).
6. 산출물 안전(미보존 `.env`/ignored/미커밋 plan 없음 — /e 조건6 재사용).
- 하나라도 불충족/불확실/명령 error → **auto 금지 → AskUserQuestion**(fail-safe). main 은 절대 auto 대상 아님.
- 삭제 실행 순서 worktree→로컬(`git branch -d`)→원격(`git push origin --delete`). 보고에 **삭제한 원격 tip sha** 명시(복구: base 에 merged 라 history 로 복구 가능 + `git push origin <sha>:refs/heads/<branch>`).
- **범위 밖 유지**: `/e` step5·`wt rm` 독립 정리(우연 머지)는 기존 AskUserQuestion — self-merge-this-turn 아니라 §8 auto 조건 미해당. 두 파일엔 cross-ref 1줄만.

# Review Outcome (plan-reviewer + Codex, 2026-07-21) — NO-GO(현설계)
자동 `git push origin --delete` 경로에 데이터 유실 구멍 다수:
- **remote-ahead 미탐지**(blocker): collect-state.sh:30 unpushed=`@{u}..HEAD` 단방향 → 다른 머신 push 를 못 봄 → 자동 원격삭제로 유실(§10 멀티머신 워크플로우에서 현실). fetch/lease 없음.
- **remoteContainingHead(조건5b) 자동 부적합**(blocker): `branch -r --contains HEAD` 는 조상포함일 뿐 — stacked PR·통합 브랜치도 충족. 문서(§B) 자신이 "확정 아님, 사용자 확인 전제".
- **PR 미조회**(major): 순수 git 휴리스틱. "base 에 merged" ≠ "불필요"(다음 PR base·다른 open PR). worktree-lifecycle §B 는 "PR 미조회의 보상통제 = 사용자 확인"이라 명시 — 확인만 제거하면 보상통제 소멸.
- **human gate 소멸**(blocker): settings `git push origin main/master` 만 deny, `git push *`=ask + skipDangerousModePermissionPrompt → skill AskUserQuestion 이 원격삭제 전 유일 human gate. Decision #23("deny 안 됨=자동 가능") 오류.
- **rollback**: 정책 revert 는 값싸나 auto-삭제된 원격 브랜치 효과는 사실상 복구 불가(durable ref 소멸 가능).

## 사실 정정 (내 plan 오류)
- **Deferred 폐기**: `docs/worktree-lifecycle.md` 는 **repo root 에 실재**(8.7K). `skills/e/SKILL.md` 상대참조는 repo root 기준. 이 문서가 merge 판정 §B authority + "최종 삭제 늘 AskUserQuestion" 규정 → **5번째 수정 대상**. (find 를 skills/ 하위로만 돌린 내 오류 — 세션 2번째 경로 미검증 실수 [[root-cause-read-code-before-concluding]].)
- **Decision #23 폐기**: settings push 는 ask/skip-dangerous, deny 아님.

## 재설계 방향 (리뷰 권고)
자동화를 **worktree + 로컬 `git branch -d`**(비가역 아님·-d 는 미머지 거부)까지로 한정, **원격 삭제는 확인 유지 또는 사용자-지시-머지(gh pr merge --delete-branch)에만**. 원격 자동 도입 시 fetch+remote-ahead 차단·보호브랜치 게이트·삭제전 복구 tag 선행 필수.

# Decisions
- **안전 게이트 재사용**: /e step5 의 6조건(①비-main ②done/merged ③clean ④no-unpushed ⑤merged-detected ⑥산출물안전)을 "자동 정리 안전 판정"으로 그대로 씀. 새 게이트 만들지 않음(단일 소스). 6조건 AND 충족→자동, else→기존 동작(ask 또는 skip).
- **자동 vs 확인 분기**: 6조건 충족→worktree+로컬+원격 자동 실행(확인 생략)+1줄 보고. 불충족/불확실(dirty·unpushed·미머지·squash 미감지·`.env`/미커밋 plan 위험)→자동 삭제 금지→AskUserQuestion(e 는 skip 이 기본 보수동작).
- **squash-merge 안전**: `git branch --merged origin/<default>` 가 squash 를 미감지→미머지 취급→자동 안 됨→ask. false-merged 는 --merged 특성상 사실상 불가(안전 방향).
- **main 제외**: main/master worktree 는 자동 정리 대상 아님(불변).
- **1줄 보고**(가정, 결과동치): 자동 정리 후 무엇을 지웠는지 1줄 보고(silent 아님 — 투명성). blocking 질문만 제거.
- **hook/settings 무변경**: feature 브랜치 원격 삭제는 이미 deny 안 됨(이번 세션 실측 push --delete 성공). main push deny 는 무관.

# Key Files
- CLAUDE.md:120 — §8 "머지/완료 후 정리" 규칙(정책 anchor, 주 변경)
- skills/dlc/SKILL.md:120 — 정리 판정 bullet(주 변경 — dlc Report 가 self-merge 직후 경로)
- skills/e/SKILL.md:46,56 — step5(cross-ref 1줄; self-merge-this-turn 아니면 기존 ask 유지)
- skills/wt/SKILL.md:112,122 — rm(cross-ref 1줄; 기존 AskUserQuestion 유지)
- docs/worktree-lifecycle.md — merge 판정 §B authority(참조 정합만 확인, 확인=늘 AskUserQuestion 철학과 auto-예외 충돌 없게 anchor 는 §8)

# Acceptance
- [x] CLAUDE.md:120: self-merge-this-session + 안전6조건(비-main·clean·fetch후 remote-ahead없음·base merged·산출물안전)→worktree+로컬+원격 자동(확인생략, 삭제 tip sha 보고); 미충족/우연머지→AskUserQuestion. `gh pr merge --delete-branch`·main 제외 보존 (관찰: diff)
- [x] dlc:120: self-merge 직후+안전→자동 full clean, else 능동 제안(AskUserQuestion) (관찰: diff)
- [x] e step5·wt rm: cross-ref 1줄 추가(§8 auto-예외 지시), 나머지 기존 ask 동작 보존 — /e·wt rm 독립정리는 여전히 확인 (관찰: diff)
- [x] 일관성: 4파일 + docs 가 동일 정책, "auto 인데 remote-ahead/protected 미체크" 잔존 없음 (관찰: grep + 읽기)
- [x] 안전 불변식: main auto 없음·squash/미머지/dirty/remote-ahead/불확실→ask·`--force` 자동 없음·삭제전 tip sha 기록 (관찰: 각 문구)

# Deferred
- **정정**: `docs/worktree-lifecycle.md` 는 repo root 에 실재(내 find 오류). Deferred 아님 — Key Files 로 이동, 참조 정합 확인 대상.
- **step 번호 baseline drift (범위 밖 · main 기원 · 2026-07-26 발견)**: #98 이 `/e` 에 worklog step5 를 삽입하며 후속 단계 번호를 밀었으나 참조 2곳이 갱신되지 않음 — `docs/worktree-lifecycle.md:3`("worktree 삭제 판정(5단계)…복귀 pull(6단계 ⓑ)" → 실제 6·7단계), `README.md:301`("마무리 2단계·5단계의 읽기전용 git 신호" → 2·6단계). 이 브랜치가 만든 drift 가 아니라 merge 로 가시화된 것이라 §3-4 대로 미수정. 심각도 낮음(문서 참조), 수정 비용 2줄.
- `skills/e/collect-state.sh:30` unpushed=`@{u}..HEAD` **단방향**(remote-ahead 미탐지). 이번 auto 경로는 §8 에서 별도 `git fetch`+양방향 rev-list 를 명시해 우회하므로 무영향. collect-state 소비자(/e·wt rm)는 여전히 ask 라 유실 없음. 근본 개선(collect-state 에 remote-ahead 필드 추가)은 스코프 밖·별도 작업 후보. 심각도 낮음.

# Blockers
(없음)
