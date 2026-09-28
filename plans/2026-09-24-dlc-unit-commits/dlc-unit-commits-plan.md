---
title: dlc-unit-commits — dlc 에 목적 단위 중간 커밋 + fixup + commit-check 합치기 도입
status: done
started: 2026-09-24
updated: 2026-09-24
intent: plans/2026-09-25-unit-commit-followups/intent.md
---

# Goal
medium 이상에서 목적이 2개 이상인 dlc 작업은 목적 단위로 중간 커밋하고, 커밋된 단위의 후속 수정은 `git commit --fixup=<대상>` 으로 만들어 마지막에 commit-check 가 합치게 한다. small·trivial 은 지금처럼 마지막 1회.

# Intent
- Problem: dlc 는 마지막에 1회 커밋해 목적이 섞인 커밋이 생기면 commit-check 가 파일 단위로만 나눌 수 있다(같은 파일 안 hunk 단위는 불가). 반대로 후속 수정 커밋이 합쳐지지 않고 남는다(knowledge_base 최근 60일 머지 PR 의 29%, 4 repo 읽기 전용 집계).
- Constraints (사용자 선택 2026-09-24 "C 구현"): 적용은 medium 이상 + 목적 2개 이상일 때만, small·trivial 은 현행 1회. 단위 커밋·fixup 은 그 단위의 targeted 검증(Green) 통과 뒤에만(CLAUDE.md §8 검증 실패 커밋 금지). 합치기는 commit-check 의 기존 승인 절차를 그대로 탄다(재구성 전 승인은 사용자 규칙).
- Out of scope: TDD Red·fix loop 등 단계마다 고정 커밋(선택지 B — 실패 테스트 커밋·bisect 파손·합칠 커밋만 늘어 기각). `/e merge` 의 plan 종료 커밋 방식. commit-check 의 hunk 단위 분할. `agents/code-reviewer.md` 수정(호출 측이 범위를 넘기면 충분 — 에이전트 정의는 이미 "호출 측이 명시한 범위"를 받는다).
- 분할: 없음 — U1(commit-check `fixup_of`)만 먼저 머지해도 유효하지만, 두 번째 plan 의 worktree·리뷰·머지 고정비가 U2 한 벌 문서 변경보다 크다. 대신 이 plan 안에서 목적 단위 커밋 2개(U1→U2)로 새 규칙을 스스로 적용한다.
- Open questions: 없음.

# Acceptance
1. commit-check `collect` 가 `fixup!`·`squash!`·`amend!` 커밋마다 `fixup_of`(범위 안 대상 sha, 없으면 null)를 내고, 그 선택이 git `rebase -i --autosquash` 와 같다 — 제목 정확일치 우선·같은 제목이면 가장 앞 커밋·접두 후보 여럿이면 가장 앞·`fixup!` 뒤 공백 여러 칸·제목과 sha 경합 시 제목·중첩 접두·범위 밖 null fixture 테스트 통과(기대값은 git 2.54 todo 실측).
2. commit-check SKILL.md: `fixup!` 은 `fixup_of` 대상에 합치는 것이 기본 제안, `squash!`·`amend!` 는 계획에 `message` 를 명시, `fixup_of` null 은 "대상 미확인/범위 밖".
3. `skills/dlc/SKILL.md`: 커밋 단위 절(선언·단위 커밋·fixup·plan 파일·공유 파일·리뷰 범위·16단계 마지막 커밋) + 파이프라인 표 3·10·11·12·16 반영. 옛 문구 잔존 없음 — `grep -n "정식 커밋은 이 판정에서만" skills/dlc/SKILL.md` 0건, `grep -n "중간 커밋을 막지는 않는다" CLAUDE.md` 0건, `grep -n "둘 다 정식 커밋 금지" README.md` 0건.
4. `CLAUDE.md` §8 커밋 bullet 2개가 새 규칙(목적 단위 중간 커밋·fixup)과 맞다.
5. README dlc·commit-check 섹션, wiki `dlc-development-cycle` 동기화, `check_links.py` clean.
6. 이 브랜치가 U1·U2 단위 커밋 + fixup 으로 만들어지고, 마지막 commit-check `collect` 가 각 fixup 의 `fixup_of` 를 올바른 단위로 가리키며 합치기를 제안한다. 적용은 사용자 승인 시(보류·충돌이면 그 사실을 Report 에 — dlc 규칙대로 DONE 을 되돌리지 않음).
7. `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음).

# Progress
- 2026-09-24: 착수. 근거 — 사용자 선택 C, 4 repo PR 집계(`pr_commit_stats.sh`: ~/.claude 후속 수정 PR 5/58, coin-trading-bot 7/74, knowledge_base 47/163·WIP 18).
- 2026-09-24: U1 구현(TDD) — `fixup_of` 테스트 Red→Green. plan-reviewer(+codex) CONDITIONAL → git autosquash todo 실측(scratch `autosquash_semantics.sh`)으로 매칭 규칙 4곳 불일치 확인·정정(Red→Green, 61 OK). 공유 plan 리허설(`shared_plan_rehearsal.sh`): plan 수정을 U1 fixup 에 넣으면 merge-tree 충돌로 apply 거부, 마지막 단위로 보내면 적용·tree 동일.

- 2026-09-24: U1 단위 커밋(targeted: commit-check 61 OK), U2 문서 → 옛 문구 grep 0건·wiki clean·improve error=0 → U2 단위 커밋. code-reviewer 범위는 `2365cf9...HEAD` + 작업트리.

- 2026-09-24: code-reviewer(+codex high) REQUEST CHANGES → git todo 2차 실측(`autosquash_semantics2.sh`: 접두·sha 단계는 fixup 커밋도 후보, 첫 접두 뒤 탭이면 fixup 아님)으로 `_fixup_of` 정정(Red→Green, 62 OK) → U1 fixup `8351b5c`. 규칙 문서 Major 2·Minor 정정 → U2 fixup `666cdc7`. simplify: 변경 없음.

- 2026-09-24: 격리 runner 최종 검증 — verify ALL PASS·62 OK·improve error=0·plan-lint·wiki clean·옛 문구 0건, collect 의 fixup_of 가 두 fixup 을 각 단위로 가리킴. 판정 DONE. plan 은 U2 fixup 으로 커밋.

- 2026-09-24: commit-check 합치기 승인·적용 — 5커밋 → U1 `3bd75bb`·U2 `60e7794`, tree 동일(백업 `refs/commit-check/dlc-unit-commits/20260924T143705273780Z`). 사용자 선택으로 wiki `git-autosquash-target-selection` 을 U3 로 추가.

- 2026-09-24: 커밋 3bd75bb(U1)·60e7794(U2)·2d283c6(U3 wiki). commit-check 재확인 이상 없음(wiki/log.md 는 append-only 로그라 후속 수정 아님). `/e merge` → PR #172.

# Next
(없음 — PR #172 머지로 종료)

# Decisions
- 커밋 단위: 1) `feat(commit-check): fixup! 커밋의 합칠 대상(fixup_of)을 git autosquash 규칙으로 표시` — `skills/commit-check/*` 2) `docs(dlc): medium 이상 목적 단위 중간 커밋·fixup 규칙` — `skills/dlc/SKILL.md`·`CLAUDE.md`·`README.md`·`wiki/**`. plan 파일은 어느 단위에도 넣지 않고 16단계 마지막 커밋(마지막 단위의 fixup)에만 싣는다. 3) `docs(wiki): git-autosquash-target-selection ingest` — `wiki/**`(사용자 선택으로 머지 전 추가, 마지막 단위라 plan 갱신을 함께 싣는다).
- **plan 파일은 단위 커밋에 넣지 않는다** — 매 단계 갱신되는 파일이라 앞 단위 fixup 에 들어가면 뒤 단위와 3-way 충돌한다(리허설 실측). 마지막 단위의 fixup 으로 보내면 충돌 없이 합쳐진다. 기각: 단위마다 그 시점 plan 을 싣기(리뷰어·리허설로 충돌 확인).
- **두 단위가 함께 고치는 파일은 뒤 단위에 속한다** — 후속 수정도 뒤 단위의 fixup 으로. 앞 단위 fixup 에 넣으면 같은 충돌이 난다.
- 단위 선언 위치는 plan `# Decisions` 의 "커밋 단위:" 한 줄(각 단위의 **고유 커밋 제목** 포함) — compaction 뒤에도 `git log --format='%h %s' <base>..HEAD` 로 단위 sha 를 다시 찾을 수 있고, `--fixup=<sha>` 가 만드는 `fixup! <제목>` 매칭이 모호하지 않다. 목적이 1개면 `커밋 단위: 1개 — <근거>`. 기각: 새 `# Commits` 섹션(§10·plan-lint 수정 필요, plan-reviewer 확인상 기존 파서는 Decisions 본문을 읽지 않아 한 줄이면 충분).
- `fixup_of` 매칭은 git `rebase --autosquash` 와 같게: 접두(`fixup!`/`squash!`/`amend!` + 공백들) 반복 제거 → 제목 정확일치 → (4자+ 16진이면) sha 접두 → 제목 접두, 각 단계 가장 앞 커밋, 대상 후보에서 `fixup!` 류 제외. 근거는 git 2.54 todo 실측(man 페이지·codex 의 sequencer.c 대조와 일치). commit name 해석은 sha 접두만 지원(ref 이름 등은 미지원 — 범위 안 커밋만 대상이라 실용상 충분).
- 개념 분리: **단위 커밋** = 그 단위의 targeted 검증(Green)을 통과한 중간 커밋, **정식 완료 커밋** = 16단계 evidence gate·판정 뒤의 마지막 커밋. BLOCKED·NEEDS-HUMAN 은 정식 완료 커밋만 하지 않으며 이미 만든 단위 커밋은 되돌리지 않는다. fixup 커밋도 targeted 검증 통과 뒤에만.
- 리뷰·simplify 범위: 단위 커밋이 있으면 `git diff <작업 base>...HEAD` + 작업트리 변경을 호출 측이 명시해 넘긴다(단위 커밋 뒤 기본 `git diff` 가 비는 문제). `agents/code-reviewer.md` 는 "호출 측이 명시한 범위"를 이미 받으므로 수정하지 않는다.
- `squash!`·`amend!` 는 합칠 때 메시지 의미(본문 결합·교체)가 있어, commit-check 기본 제안은 `fixup!` 만 자동 합치기로 하고 둘은 계획에 `message` 를 명시하게 한다. `fixup_of` null 은 "대상 미확인/범위 밖"(오타·게시·다른 브랜치·태그 모두 포함 — "게시됨" 단정 금지).
- `/e` WIP 가 두 단위에 걸치면 commit-check 계획에서 `{"from": [단위, WIP], "paths": [...]}` 로 WIP 를 경로별로 나눠 각 단위에 합친다(합치기+분할 조합은 이미 지원·테스트됨).
- 목적이 구현 중에 1개→2개로 늘면: 섞인 변경이 경로로 떼어지면 앞 목적을 단위로 먼저 커밋하고, 같은 파일 안에서 섞였으면 한 단위로 두고 `# Decisions` 에 사유를 적는다.
- 기각한 대안: A(현행 마지막 1회 유지 — 목적이 같은 파일 안에서 섞이면 commit-check 가 사후에 나눌 수 없어 문제를 해결 못 함), B(단계 고정 커밋 — Intent Out of scope), D(중간 커밋 없이 16단계에서 단위별 stage·`git apply --cached` hunk 분리 — 리뷰 범위·DONE 규칙 충돌은 없지만 같은 파일에 두 목적이 시차를 두고 섞이면 사후 hunk 분리를 모델이 수작업으로 해야 해 오류 위험이 가장 크다. C 는 목적이 섞이기 전에 커밋해 hunk 분리 자체를 피한다).
- 가장 위험한 단계: CLAUDE.md §8 전역 규칙 변경(모든 repo·세션에 즉시 전파) — 되돌리기는 dlc SKILL·CLAUDE §8·README·wiki 를 한 커밋(U2)으로 revert 하면 되고 U1(`fixup_of`)은 독립 유지 가능. 두 번째는 이 브랜치 commit-check apply — 백업 ref 로 복구 가능, 공유 plan 충돌은 리허설로 먼저 확인했다.

# Review Disposition
- [plan 강1] fixup_of 매칭이 git 과 다름 — fix(git todo 실측으로 규칙 정정 + 경합 fixture).
- [plan 강2] plan·공유 파일 fixup 충돌 — fix(plan 은 마지막 커밋에만·공유 파일은 뒤 단위, 리허설로 확인).
- [plan 강3] 단위 커밋 뒤 리뷰 범위 공백 — fix(호출 측이 `<base>...HEAD`+작업트리 명시, 에이전트 정의 무수정).
- [plan 강4] DONE 전용 커밋 문구 충돌 — fix(단위 커밋/정식 완료 커밋 개념 분리, 옛 문구 잔존 grep 을 Acceptance 3 에).
- [plan 약] squash!/amend! 메시지 의미 — fix. fixup_of null 표기 — fix. compaction 뒤 sha 재발견·제목 유일성 — fix(고유 제목 선언). /e WIP 가 두 단위에 걸침 — fix(합치기+분할). 분할 근거 — fix(비용 근거). 기각 대안 A·D — fix. 최고위험 단계·리허설 — fix(리허설 실행). Acceptance 6 과 DONE 규칙 — fix(보류·충돌 시 기준 명시). Next 순서(구현 선행) — accepted-risk(U1 은 TDD 로 이미 구현, 리뷰 반영 전 커밋하지 않음 — 지켰다). rollback 절 — fix(가장 위험한 단계 줄에).
- [plan 누락] 목적이 1→2 로 느는 경우 — fix(Decisions).
- [code Major] 공유 파일을 통째로 뒤 단위에 → 앞 단위 커밋이 불완전 — fix(앞 단위가 동작하는 데 필요한 변경은 앞 단위에, 한 파일 안에서 섞였으면 한 단위로. 뒤 단위 귀속은 앞 단위 fixup 이 뒤 단위 파일을 건드려 충돌할 때만, Report 에 귀속 예외로).
- [code Major] 16단계 "남은 변경" 전부를 마지막 단위로 → 목적 귀속 오류 — fix(코드는 귀속 단위 fixup, 기록 파일만 마지막 단위, 후속 수정 규칙을 11~15단계로 확장).
- [code Major, disputed] commit-check `fixup!`+`plan-only` 우선순위 — fix(`fixup_of` 있는 fixup 이 plan-only 기본값보다 우선).
- [code Minor, disputed] `!\s+` 접두·fixup 후보 제외·커밋 이름 해석 — fix(첫 접두 리터럴 공백·이후 공백 건너뜀·fixup 커밋도 후보·sha 는 범위 안 유일할 때만, git todo 2차 실측 테스트). ref 이름·`HEAD~n` 미해석은 문서 문구를 "근사"로 좁혀 wontfix.
- [code Minor] 보류된 `fixup!` 이 `/e merge` 로 게시 — fix(dlc 16단계 Report 리스크 문구) + Deferred(/e merge push 전 재확인).
- [code Minor] base 복원 절차 — fix(`git merge-base HEAD <default>`). 경계 테스트 — fix(2차 실측 테스트). 표 16행 용어 — fix("정식 완료 커밋", README·wiki 포함). CLAUDE §8 문구 해석 여지 — fix. WIP 분할이 plan 에만 — fix(commit-check SKILL).
- fix 후 재리뷰 생략 — 매처 수정은 git 실측 테스트로, 문서 수정은 리뷰어 제안 문구대로 반영하고 targeted 검증(옛 문구 grep·wiki·improve)을 통과했다.

# Deferred
- `/e merge` 가 push 전 브랜치에 남은 `fixup!`·`wip:` 커밋을 재확인하지 않는다 — commit-check 보류·충돌 시 그대로 게시될 수 있다(Minor, `skills/e/SKILL.md` M1~M3). 이번 plan Out of scope.

# Key Files
- `skills/commit-check/commit_units.py`, `test_commit_units.py`, `SKILL.md` — U1
- `skills/dlc/SKILL.md`, `CLAUDE.md` §8, `README.md`, `wiki/pages/concept/dlc-development-cycle.md`, `wiki/log.md` — U2

# Blockers
없음
