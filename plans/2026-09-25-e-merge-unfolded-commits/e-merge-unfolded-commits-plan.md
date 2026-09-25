---
title: e-merge-unfolded-commits — /e merge 가 push 전에 fixup!·wip: 등 정리 안 된 커밋을 검사
status: in_progress
started: 2026-09-25
updated: 2026-09-25
intent: plans/2026-09-25-unit-commit-followups/intent.md
---

# Goal

`/e merge` 가 push(M3) 전에 `origin/<default>..HEAD` 에서 `fixup!`·`squash!`·`amend!`·`wip:` 커밋을 찾아, commit-check 로 정리(승인 후)하거나 중단·보고한다. `skills/e/SKILL.md` 의 WIP 정리 안내를 commit-check 로 바꾸고, `docs/worktree-lifecycle.md` §E 시나리오 표에 해당 행을 더한다.

# Intent

→ `plans/2026-09-25-unit-commit-followups/intent.md` (Problem·Proposed outcome·공통 Constraints·Out of scope·Open questions 는 거기).

델타: intent 의 Open question 은 사용자가 2026-09-25 "commit-check 제안 → 승인" 으로 정했다(자동 재구성·중단만 둘 다 아님) — 이 plan 이 intent 에 `(해소)` 로 적는다.

규모: small 로 시작 → plan-reviewer 뒤 **medium 으로 재판정**(`commit_units.py` 읽기 전용 서브커맨드 + 테스트 + 문서 4곳, 50줄 초과).

분할: 없음 — `commit_units.py pending` 과 `/e` M3 규칙으로 나누려 했으나, `pending` 의 계약(상태 4종·flag 를 `wip`·`fixup` 으로 한정)은 M3 규칙이 유일한 소비자라 따로 머지하면 README·commit-check SKILL 이 호출처 없는 기능을 서술하고, 계약도 소비자 규칙 없이 리뷰하게 된다.

# Acceptance

1. `commit_units.py pending <upstream>` 이 `<upstream>..HEAD` 의 커밋 중 flag 가 `wip`·`fixup`(정본 `_FLAG_PATTERNS`, `squash!`·`amend!` 포함) 인 것만 전체 sha 와 함께 내고, 각각을 `rewritable`(commit-check 범위 안) / `published`(`refs/remotes/*` 에서 도달 — 붙잡은 ref 이름 포함) / `held`(원격엔 없고 다른 로컬 브랜치·태그가 붙잡음 — ref 이름 포함) / `blocked`(어느 ref 에도 없지만 범위를 재구성할 수 없음 — `range_error` 에 사유) 로 분류한다. 읽기 전용(ref·index·작업트리 불변). 검증: `test_commit_units.py` 의 pending 테스트(published·로컬 main 앞섬·태그·rewritable·merge 커밋 범위·flag 한정 — `plan-only`·`review-followup` 은 안 나옴)가 통과한다.
2. `skills/e/SKILL.md` M3 가 맨 앞(M4 선행 분기보다 먼저)에서: 원격 작업 브랜치가 있으면 `git fetch origin <branch>` 후 그것이 HEAD 의 조상인지 확인(아니면 중단) → `pending origin/<default>` → `rewritable` 이 있으면 commit-check 스킬을 flag 정리로 범위를 좁혀 호출(합치기 또는 정식 제목 reword) → 적용 뒤 `pending` 재실행에서 `rewritable` 0 일 때만 진행 / `published`·`held`·`blocked` 는 사유·ref 와 함께 보여 주고 진행/중단을 묻는다(`mergeCommitAllowed=false` 면 M6 이 어차피 squash 하므로 보고만) / 보류·apply 실패·재검사 잔존·`pending` 실패·질문 불가(무인) 는 중단. 검증: `git grep -n "pending origin/<default>" skills/e/SKILL.md` 1건 이상, 위 분기 각각의 문구 확인.
3. 중단 규칙이 모순 없다: done 을 새로 쓰지 않고, 3단계의 미커밋 plan 편집은 보존하며 `# Next` 에 사유·재실행 안내만 더한다(커밋·push 없음). 이미 done 인 PR 재실행은 status 를 건드리지 않는다. apply 성공 뒤 중단이면 재구성은 유지하고 `backup_ref`·`rollback` 을 보고한다. 검증: SKILL 문구와 §E 표 행.
4. WIP 정리 안내가 commit-check 를 가리킨다. 검증: `git grep -n "squash/amend\|이어서/squash" skills/e` 0건.
5. 문서 동기화: `docs/worktree-lifecycle.md` §E 에 `pending` 명령·출력과 시나리오 행(rewritable 정리·보류, published/held/blocked 질문, 원격 브랜치 분기)이 있고, README:317(`/e merge`)·README:350 과 `skills/commit-check/SKILL.md` description(호출처에 `/e merge` 추가)·`pending` 절이 갱신됐다. 검증: grep.
6. intent `plans/2026-09-25-unit-commit-followups/intent.md` 의 Open question 이 `(해소)` 다.
7. 전체: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음, `test_commit_units.py` 포함), 이 plan 의 plan-lint 통과.

# Progress

- 2026-09-25: 전체 감사 후 origin/commit-split 을 닫으면서 살릴 부분으로 생성(사용자 선택 "close + 살릴 것만 새 plan"). 착수 전.
- 2026-09-25: 착수(`/wt`). Explore — commit-check `collect` 가 `wip`·`fixup`(squash!/amend! 포함) flag 와 게시 제외를 이미 준다. `apply` 는 브랜치 ref 만 CAS 로 옮기고 최종 tree 가 같아 3단계의 미커밋 plan 편집과 충돌하지 않는다(`commit_units.py:496-523`).
- 2026-09-25: plan-reviewer(+codex) CONDITIONAL — 강한 우려 6·약한 우려 9. 문서만으로는 게시/로컬 보유 구분과 flag 판정을 결정적으로 할 수 없어 `commit_units.py pending` 추가로 설계 변경, medium 재판정. 사용자 승인 대기.
- 2026-09-25: 사용자 승인("pending 서브커맨드 추가"). TDD Red(pending 4건, `cu.pending` 부재) → 구현 → Green(66 통과) → 단위 커밋 1. `/e` M3 선행 검사·§E·README:317·intent 편집. bare remote 리허설(scratchpad `em_rehearsal.sh`): R1 OPEN PR 재실행 — 게시 wip 1 은 published 로 남고 미게시 fixup·wip 은 합쳐져 재검사 0, plan 편집 보존, ff push / R2 게시된 단위에 대한 fixup! — `fixup_of` null → reword → 재검사 0 / R3 원격 브랜치 갈라짐 → 조상 아님으로 중단.
- 2026-09-25: code-reviewer(+codex) REQUEST CHANGES — Major 3(서명 범위 rewritable↔apply 거부 · 충돌 fold 의 reword 폴백 부재 · fetch 가 추적 ref 를 안 갱신할 수 있음), Minor 5, Nit 7. fix loop 1: `_rewrite_blocker` 로 apply 와 거부 조건 공유(서명·git 버전·기본 브랜치 → blocked), range_error 면 held 대신 blocked, symref 제외, 제목 일괄 조회, CLI 가드 테스트 수정 · SKILL/§E/README 문구. 테스트 67 통과. 리허설 2(`em_rehearsal2.sh`): R4 fetch refspec 이 main 만일 때 명시 refspec 으로 추적 ref 갱신 → 갈라짐 중단 / R5 원격 삭제 뒤 옛 추적 ref 정리 → published→rewritable / R6 충돌 fold 거부 → reword 적용 → 재검사 0. R1~R3 재통과.
- 2026-09-25: code-reviewer 재확인(수정분) APPROVE — 남은 Minor 3·Nit 4 → fix loop 2(README·docstring 과장, 충돌 reword 승인 범위, Decisions 동기화, 추적 ref 삭제 sha 보고, held 안내), `cat-file` N회는 Deferred.

# Next

commit-check(단위 1 fixup 합치기) 승인 → 종결 방식 확인(`/e merge` 권장 — medium, PR·CI).

# Decisions

- **초안 출처**: 로컬 태그 `archive/commit-split`(51d55d9, 원격 브랜치는 2026-09-25 삭제)의 `skills/e/SKILL.md` M3·M4 문구와 `docs/worktree-lifecycle.md` §E 2행을 참고 초안으로 쓴다. 단 `/cs` 호출 자리는 commit-check 로 바꾸고, 무승인 자동 재구성은 가져오지 않는다(intent Constraints).
- **검사 대상**: 제목 접두 `fixup! `·`squash! `·`amend! `·`wip:`. `fixup!` 계열 대상 매칭은 commit-check `collect` 의 `fixup_of` 를 재사용한다(git autosquash 규칙과 대조 완료, wiki `git-autosquash-target-selection`).
- 원 결함 기록: `plans/2026-09-24-dlc-unit-commits/dlc-unit-commits-plan.md` # Deferred 첫 줄.
- **검사 위치**: M3 의 맨 앞 — "새 PR 이 필요하면 M4 먼저" 분기보다 앞. M4 의 done 커밋이 생기기 전이라 보류·실패 시 plan 을 되돌릴 일이 없고, 재구성 대상에 done 커밋이 섞이지 않는다.
- ~~**검출**: 트리거는 `git log` 제목, 분류는 `collect` 의 `commits` 포함 여부~~ → **`commit_units.py pending <upstream>` 으로 변경** (이유: plan-reviewer S1·S2 — collect 는 다른 로컬 브랜치·태그·원격을 한꺼번에 빼서 "게시분"과 "로컬 ref 가 붙잡은 미게시분"을 구분하지 못하고, 제외분에는 flag 가 없어 제목 판정을 모델 눈에 맡기게 된다. 상태 4종은 Acceptance 1). 코드 변경 없음 결정은 이것으로 뒤집혔다.
- **commit-check 호출**: Skill 도구로 `commit-check` 를 부르고 인자로 "flag(`wip`·`fixup`) 커밋 정리만 — 다른 제안은 참고로만"을 준다(W5 — 무관한 split·reword 가 싫어 보류하면 머지 전체가 멈춘다). flag 커밋은 합치거나, 대상이 범위 밖(이미 게시된 단위에 대한 `fixup!` 등 — `fixup_of` null)이면 정식 제목으로 reword 한다(apply 가 message 만 있는 항목을 지원). `/e` 가 직접 부르는 `pending` 은 `$HOME/.claude/skills/commit-check/commit_units.py`(SKILL 이 main checkout 에서 로드되므로 같은 버전).
- **중단 규칙**(S4): done 을 새로 쓰지 않는다 · 3단계 미커밋 plan 편집은 보존하고 `# Next` 에 사유·재실행 안내를 더한다(커밋·push 없음) · 이미 done 인 PR 재실행은 status 불변 · apply 성공 뒤 중단이면 재구성 유지 + `backup_ref`·`rollback` 보고(W2) · `pending`·collect·apply 실패는 0건이 아니라 중단(S3).
- **원격 작업 브랜치 fetch**(S6): M2 는 default 만 fetch 한다. `pending` 전에 `git fetch origin <branch>`(원격에 없으면 건너뜀) 후 `origin/<branch>` 가 HEAD 의 조상이 아니면 중단 — 오래된 추적 ref 로 게시분을 재작성 대상으로 오인하지 않게. → **명시 refspec `+refs/heads/<branch>:refs/remotes/origin/<branch>` 로 변경** (이유: code-reviewer — fetch refspec 이 main 만 매핑하는 clone 에서 브랜치 이름만 준 fetch 는 FETCH_HEAD 만 갱신한다, 리허설 R4). 원격에 브랜치가 없으면 남은 추적 ref 를 `update-ref -d` 로 지우고 sha 를 보고(이유: 옛 추적 ref 가 미게시 커밋을 published 로 보이게 한다, R5). `is-ancestor` 는 exit 1(갈라짐)과 그 밖(오류)을 구분해 둘 다 중단.
- **합치기 충돌 시 reword**: commit-check 제안 표에 합치기마다 "충돌 시 reword: `<제목>`" 을 함께 적어 한 번 승인받고, apply 가 충돌로 거부하면 그 커밋만 reword 로 한 번 재시도한다(이유: code-reviewer — 원 결함인 "충돌로 남는 `fixup!`" 이 이 기능의 주 입력인데 보류하면 재실행해도 같은 자리에서 멈춘다, R6. 표에 없던 계획은 다시 묻는다 — 재구성 전 승인 규칙).
- **범위 전체 거부 조건 공유**: `_rewrite_blocker`(기본 브랜치·git 2.40 미만·서명 커밋)를 `pending` 과 `apply` 가 함께 쓴다(이유: `pending` 이 rewritable 이라 해 놓고 apply 가 범위째 거부하는 막다른 경로). apply 의 오류 우선순위는 git 버전 검사가 `_in_progress`·`resolve_range` 뒤로 갔을 뿐 동작은 같다.
- **보류 = 중단**: commit-check 의 적용/보류 질문에서 보류하면 `/e merge` 를 멈춘다(plan 무변경, `# Next` 에 "정리 후 `/e merge` 재실행"). 이유: 그대로 push 하면 이 plan 이 막으려는 게시가 일어난다.
- ⚠️ 이미 게시된 정리 안 된 커밋 — "정리 안 된 커밋을 게시하지 않는다"(intent Problem) 와 "게시된 커밋은 고치지 않는다"(§8 force-push 금지) 가 상충 — 고치지 않고 목록을 보여 준 뒤 `AskUserQuestion`(그대로 진행 / 중단)으로 사용자에게 넘긴다. 조용히 계속하면 main 이력에 남는 것을 사용자가 모르고, 무조건 중단하면 §8 안에서는 풀 방법이 없다. `held`(로컬 ref 가 붙잡음)·`blocked`(범위 재구성 불가)도 같은 질문에 사유·ref 를 붙여 태운다 — `held` 는 그 ref 를 치우면 재실행으로 정리할 수 있다고 안내. `mergeCommitAllowed=false` 면 M6 이 squash 하므로 묻지 않고 보고만. 재실행마다 같은 게시분을 다시 묻는 마찰은 감수(게이트 밖 push 로만 생겨 드물다).
- 기각: 게시분에 "이 PR 만 squash 머지" 선택지(W1) — M6 경로가 갈리고 단위 커밋을 잃으며, 7단계 `git branch -d` 가 거부돼 확인 경로로 간다. 원하면 "중단" 후 수동으로.
- 기각: pre-push hook 으로 강제(W7) — 모든 push 경로를 덮지만 repo 별 opt-in 훅이라 이 repo 밖엔 없고(CLAUDE.md §8), 의도적인 WIP push(백업·공유)까지 막는다.
- 기각: 문서만으로 검사(초안) — 위 검출 변경 사유(S1·S2).
- 과거 `# Progress` 에 적힌 WIP sha7 은 재구성 뒤 옛 값이 되지만 고치지 않는다 — 기록이고, commit-check 는 호출한 쪽 기록 파일에 쓰지 않는다. 머지 모드는 `# Next` 를 비우므로(M4) "WIP `<sha7>` 이어서" 안내도 남지 않는다.
- 기각: archive 초안의 `/cs` 무승인 자동 재구성·"게시된 `wip:` 는 정리 생략 보고 후 계속" — 전자는 intent Constraints(승인 후 재구성)와 충돌, 후자는 위 ⚠️ 처분으로 대체.
- ~~커밋 단위: 1개~~ → 커밋 단위: 1) `feat(commit-check): classify unfolded commits before publishing` — `skills/commit-check/commit_units.py`·`test_commit_units.py`·`SKILL.md`·README:350 2) `feat(e): check unfolded commits before /e merge pushes` — `skills/e/SKILL.md`·`docs/worktree-lifecycle.md`·README:317·intent.md·이 plan (이유: medium 재판정으로 코드와 규약 두 목적이 됐다).

# Key Files

- `skills/commit-check/commit_units.py` — `pending` 서브커맨드(읽기 전용 분류)
- `skills/commit-check/test_commit_units.py` — pending 테스트
- `skills/commit-check/SKILL.md` — description 호출처·`pending` 절
- `skills/e/SKILL.md` — M3 맨 앞(검사 위치), `:34` `# Next` 의 "WIP 이어서/squash", `:104` WIP 커밋 본문의 "squash/amend 대상"
- `docs/worktree-lifecycle.md` §E — `pending` 명령·시나리오 표
- `README.md` — :317 `/e merge`, :350 commit-check
- `plans/2026-09-25-unit-commit-followups/intent.md` — Open question 처분·`# Plans` 자기 줄

# Review Disposition

- [code] Major 서명 범위가 `rewritable` 인데 apply 거부 — fix(`_rewrite_blocker` 공유, 테스트 `test_signed_range_is_blocked`). Major(PLAUSIBLE) 충돌 fold 에서 reword 폴백 없음 — fix(commit-check `/e merge` 절, 리허설 R6). Major(분쟁: Codex Major / Claude Minor) fetch 가 추적 ref 를 갱신 안 할 수 있음 — fix(명시 refspec, is-ancestor exit 구분, 리허설 R4).
- [code] Minor held+range_error 안내 오류 — fix(range_error 면 blocked, refs 유지). Minor 원격 삭제 뒤 옛 추적 ref → published 오판 — fix(`update-ref -d`, 리허설 R5). Minor M3-4 무인 처리 — fix. Minor 커밋마다 `_meta` — fix(`git log --format=%H%x00%s` 1회). Minor CLI 가드 테스트 미도달 — fix(`--` 뒤 인자).
- [code] Nit symref 중복 — fix(`%(symref)` 필터, 테스트). Nit §E 표 `# Next`·squash 행·재실행 칸 — fix. Nit README:317 blocked·squash — fix. Nit flag 범위 모호 — fix(`wip`·`fixup` 명시). Nit 넓은 except(resolve_range 의 git 인프라 실패도 blocked) — wontfix(오류 문구가 그대로 보이고 진행/중단을 묻는다, 드묾). Nit uv 필수 의존 — wontfix(commit-check 가 이미 uv 전용이고 bootstrap 이 uv 를 설치). Nit plan Progress 순서 — fix.
- [code] 재확인 Minor N1 README·docstring "apply 에서 막히는 일이 없다" 과장 — fix. Minor(PLAUSIBLE) N2 충돌 reword 재시도의 승인 공백 — fix(제안 표에 reword 제목 동봉). Minor N3 서명 검사 `cat-file` N회(apply 는 2N) — defer(`# Deferred`). Nit N4 Decisions 동기화 — fix. Nit N5 `update-ref -d` sha 보고 — fix. Nit N6 held 안내 과신 — fix. Nit N7 apply 거부 순서 — 기록만(Decisions).
- [code] Open: `<default>` 가 main/master 가 아닌 repo 에서 그 브랜치 위의 `/e merge` — defer(`# Deferred`, M1 게이트의 기존 공백).
- [plan] S1 제외분=게시분 오분류 — fix(`pending` 의 `published`/`held` 구분). S2 게시분 flag 판정 수단 없음·패턴 불일치·축약 sha — fix(`pending` 이 정본 패턴·전체 sha). S3 flag 가 남는 막다른 경로 — fix(reword 허용, 실패 ≠ 0건 → 중단, `blocked` 상태). S4 보류 시 plan 규칙 모순 — fix(중단 규칙). S5 intent Open question 미처분 — fix(Acceptance 6). S6 원격 작업 브랜치 추적 ref 최신성 — fix(fetch + 조상 확인).
- [plan] W1 squash 선택지 — wontfix(Decisions 기각 사유), `mergeCommitAllowed=false` 보고만 — fix. W2 apply 성공 뒤 중단 — fix. W3 flag 한정 — fix. W4 경로 해석 — fix(Skill 도구 + `$HOME/.claude/...`). W5 무관한 제안 보류 시 전체 중단 — fix(범위 한정 인자). W6 Acceptance 관찰 불가·중복 — fix(`pending` 단위 테스트로 신규 분기 검증, 엔진 재검증 제거, grep 패턴 명시). W7 기각 대안 기록 — fix. W8 동기화 범위 — fix. W9 규모 재판정 — fix(medium).
- ⚠️ self-flag(게시분 진행/중단 질문) — resolved: 리뷰가 방향 유지 판정, `held`·`blocked` 로 확장.

# Deferred

- (low) `skills/commit-check/commit_units.py` `_rewrite_blocker` 의 서명 검사가 미게시 커밋마다 `cat-file` 1회(apply 는 `collect` 의 `signed` 와 합쳐 2N) — `git cat-file --batch` 1회로 헤더를 모으고 apply 에선 결과를 공유하는 방안. 일반 PR 크기에선 영향 작음.
- (low) `skills/e/SKILL.md` M1 게이트 (1)이 main/master 만 거부한다 — `<default>` 가 다른 이름(develop 등)인 repo 에서 그 브랜치 위의 `/e merge` 가 통과한다(이 변경 이전부터). `pending` 은 그 경우 `blocked`(기본 브랜치)로 내 진행/중단을 묻는다.

# Blockers

없음.
