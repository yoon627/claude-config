---
title: slim-skill-e-ko — skills/e 의 원격 브랜치 삭제 줄이 없어진 선택지를 가리키는 것을 바로잡기
status: done
started: 2026-10-22
updated: 2026-10-26
intent: plans/2026-10-21-ops-docs-rework/intent.md
---

# Goal
`skills/e/SKILL.md` "worktree 정리 규칙" 의 로컬·원격 브랜치 줄이 지금 `/e` 에 없는 선택지("옵션 ②·③")와 옛 조건 번호("조건5")를 가리키는 것을 고친다. 원격 삭제 전에 merged 판정의 근거를 보여 주는 규칙은 그대로 남긴다. 압축은 하지 않는다(사용자, 2026-10-24).
- 묶음: [ops-docs-rework](../2026-10-21-ops-docs-rework/intent.md)
- Constraints(델타): 고치는 곳은 `skills/e/SKILL.md` 의 그 한 줄. 다른 줄은 바꾸지 않는다.
- Out of scope(델타): skills/e 압축(폐기 — 사용자, 2026-10-24) · 원문자 정리(번역 단계가 다시 쓴다) · `wiki/docs/worktree-lifecycle.md` §B 의 조건 번호 정리(plan log Deferred).
- Split: bundle → plans/2026-10-21-ops-docs-rework/intent.md

# Tasks
- [x] 범위 확인 (2026-10-22) — 사용자: slim-skills-ko 시작. 첫 파일은 dlc 대신 e(read-points 와 겹치지 않게)
- [x] 규칙 목록 (2026-10-22) — `plans/2026-10-22-slim-skill-e-ko/manifest.md`. 압축을 접어 번역 단계의 대조표로 남긴다(리뷰 보강분은 번역 단위가 반영)
- [x] 계획 리뷰 (2026-10-24) — plan-reviewer CONDITIONAL, 처분은 plan log
- [x] 방향 재확인 (2026-10-24) — 사용자: 이 PR 은 끊긴 참조 수정만, 압축은 폐기하고 번역으로
- [x] 수정 (2026-10-26): `skills/e/SKILL.md` "worktree 정리 규칙" 의 로컬·원격 브랜치 줄
- [x] 사용자에게 바뀐 문구 확인받고 커밋 (2026-10-26) — 사용자 "커밋하고 /e merge"
- [x] 단위 2 줄이기·대조·리뷰·확인 (2026-10-24) — 생략: 사용자 결정으로 압축 폐기
- [x] simplify 점검 (2026-10-22) — 생략: 문서만 바뀌어 코드 simplify 대상이 없다
- [x] `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-26) — 격리 runner: Acceptance 1~5 충족, `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 미설치, 무관). 판정 DONE
- [x] (2026-10-26) `plans/2026-10-21-slim-rules-ko/slim-rules-ko-plan.md` 의 [post-merge] wiki Task 체크(공용 wiki 커밋 653e690), intent 갱신
- [x] 기록 커밋, commit-check (2026-10-26)
- [x] 머지 (`/e merge`) (2026-10-26) — PR #241
- [ ] [post-merge] main 세션에서 plan log Deferred 처리(`worktree-lifecycle.md` §B 조건 번호)

# Acceptance
1. 끊긴 참조가 없다 — `rg -n '옵션 [②③]|조건5 확정' skills/` — 0건
2. 원격 삭제 규칙의 뜻이 남는다 — 새 줄에 "worktree·로컬 삭제 뒤", "사용자가 택했을 때만", "merged 판정 근거를 묻는 본문에", "`mergedAt` 은 확정", "그 외 push 안 함" 이 있다 — diff 대조와 사용자 문구 확인
3. 다른 줄은 바뀌지 않는다 — `git diff --stat origin/main -- skills/` 가 `skills/e/SKILL.md` 1개, 그 diff 가 한 줄 — 둘 다
4. 핵심 문구가 남는다 — manifest 의 89개를 새 파일에서 찾음 — 89개 전부
5. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 무관함을 보인다)

# Decisions
- wiki 결정 [[ops-doc-slimming]]·[[e-merge-mode]] → 따른다(게이트는 SKILL 에, 규칙 손실 0).
- 방향(사용자, 2026-10-24): 이 PR 은 수정만. 근거: CLAUDE.md 압축은 리뷰 4번에 −3.5%, e 는 대부분 push·머지·삭제 게이트라 기대 이득 5~10% ⚠️추정인데 계획 리뷰가 보강 항목을 20개 넘게 찾았다. 한국어 → 영어는 같은 내용이 약 22% 짧다(§1 실측 1,650 → 1,292 토큰). 기각: 리뷰를 다 반영해 압축까지(게이트 구간의 위험이 크고 이득이 작다).
- 새 문장(plan-reviewer S1): 지금 줄의 "조건5 확정 아님" 은 7월 slimming(e230de0) 이전 목록의 "조건5 = merged 신호" 를 가리킨다. 그 규칙을 지금 번호에 맞춰 이렇게 쓴다 — **로컬 브랜치**: `git branch -d <target_branch>`(미머지로 `-d` 가 거부되면 `-D` 는 확인 후). **원격**: worktree·로컬 삭제가 성공한 뒤, 사용자가 원격 삭제를 택했을 때만 `git push origin --delete <target_branch>`(원격 ref 가 없으면 no-op). git 신호로 본 merged(7단계 조건4)는 확정이 아니므로 묻는 본문에 그 근거(로컬 default 에만 머지됨인지, `inBase`/`patchInBase` 인지)를 적고, 그것을 본 사용자가 택한 경우에만 지운다(미머지 원격 사본 유실 방지). M6 가 확인한 `mergedAt` 은 확정이다. 그 외 push 안 함. 기각: "원격은 사용자가 택했을 때만" 으로 줄이기(근거를 보여 주는 규칙이 이 줄에만 있어 사라진다 — S1).
- 원문자(①②③): 고치지 않는다 — 번역 단위가 다시 쓴다.
- README: `README.md` 345~355행의 `/e` 설명은 원격 삭제 줄의 세부를 다루지 않아 바꿀 것이 없다(2026-10-24 확인). `dlc-doc-drift` 가 SKILL 편집에 README 경고를 내면 오탐 한 줄로 답한다.
- 커밋 단위: 1개 — `docs(e): fix the branch-deletion lines that pointed at removed options`. plan·log·manifest·intent·선행 plan 줄은 기록 커밋.
- code-reviewer: 부르지 않는다 — 한 줄짜리 규칙 문구이고, 문장은 plan-reviewer 가 짚은 뜻을 그대로 옮긴 것이며 사용자 문구 확인이 검증이다.
- 선행 plan 본문 편집: slim-rules-ko 의 [post-merge] Task 체크는 사용자 지시(2026-10-22 "같이: … 체크")에 따른 기록 갱신이다.
- 롤백: `git revert -m 1 <merge sha>`.

# Blockers
