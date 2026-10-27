# skills/commit-check 규칙 목록 (translate-skill-commit-check)

origin/main 1d9c2ae 의 `skills/commit-check/SKILL.md`(75줄) 기준. 한 줄 = 한 조항(한정어도 조항의 일부). 번역 대조는 `locations-en.txt`(`<id> | <영어 인용>`, 인용 여러 개는 ` ‖ `, 각 인용은 파일 안에서 한 번). 이 manifest 는 번역 초안 전에 만든다.

## frontmatter
- F.1 description: 아직 게시(push)되지 않은 커밋이 "리뷰 가능한 하나의 목적 단위"인지 점검, 합치기(fixup)·나누기(파일 단위)·순서·메시지 수정 제안 표, 사용자가 승인하면 코드 내용은 그대로 두고 커밋 경계만 재구성
- F.2 description: dlc 마무리(16단계 커밋 뒤)와 `/e merge`(push 전, 정리 안 된 커밋이 있을 때)에서 호출, `/commit-check` 명시 호출이나 "커밋 정리해줘 / 커밋 나눠줘 / 이 커밋 합쳐줘"류 요청에도
- F.3 description: push 는 하지 않는다

## 머리말
- P.1 커밋은 리뷰 가능한 하나의 목적 단위 — 브랜치의 미게시 커밋을 그 기준으로 보고, 고칠 것이 있으면 제안 → 승인 → 재구성
- P.2 판단은 모델, 수집·검증·재구성은 `commit_units.py`(스크립트가 안전 조건을 모두 강제 — git 명령을 직접 조합해 우회하지 않는다)

## 판정 기준
- J.1 합친다(fixup): 같은 작업의 후속 수정 — 리뷰 반영, 오타·단순 실수 정정, 같은 파일의 초안 뒤 다듬기, `wip:`·`fixup!` 커밋 — 목적이 같은 앞 커밋에
- J.2 `fixup!` 커밋은 `fixup_of`(git `rebase --autosquash` 대상 선택을 근사한 범위 안 대상 — ref 이름·`HEAD~n` 은 해석하지 않는다)에 합치는 것이 기본 제안(`show` 확인 불필요)
- J.3 이 기본값은 `plan-only` 기본값보다 우선 — plan 파일만 담은 `fixup!` 도 대상에 합친다
- J.4 `/e` WIP 커밋이 여러 단위에 걸치면 단위마다 `{"from": [단위, WIP], "paths": [그 단위 경로]}` 항목으로 WIP 를 경로별로 나눠 합친다
- J.5 `squash!`·`amend!` 도 `fixup_of` 가 대상을 가리키지만 합칠 때 메시지 의미(squash=본문 결합, amend=메시지 교체)가 있어 계획 항목에 `message` 를 명시
- J.6 `fixup_of` 가 null 이면 "대상 미확인/범위 밖"(제목 오타, 대상이 이미 게시·기본 브랜치·다른 브랜치·태그에 있음)으로 적고 합치지 않는다
- J.7 같은 파일을 여러 단위가 고친 상태에서 앞 단위로 합치면 충돌해 apply 가 거부될 수 있다 — 그러면 보류하고 사유를 제안 표에
- J.8 그 밖의 후속 수정은 `overlaps`(뒤 커밋이 앞 커밋 파일을 다시 고침)가 1차 신호, 실제로 같은 목적인지는 `show` 로 확인
- J.9 나눈다(split): 목적이 둘 이상 섞인 커밋 — 서로 다른 문제의 수정, 기능과 무관한 리팩터링·설정 변경, 파일 단위로 나뉘면 나눈다
- J.10 한 파일 안에서 목적이 섞였으면(hunk 단위) 자동으로 나누지 않고 제안 표에 "수동 분할 필요"로만
- J.11 메시지를 고친다: 제목이 repo 관례와 다를 때 — 관례 정본은 그 repo 의 AGENTS.md·CLAUDE.md 커밋 절, 없으면 `convention_samples`(기본 브랜치 최근 제목) — 제목은 무엇을 바꿨는지, 본문은 왜
- J.12 그대로 둔다: 이미 한 목적 한 커밋이면 손대지 않는다, plan 전용 커밋(`plan-only`)은 기록 목적이 달라 합치지 않는 것이 기본(단 `fixup_of` 가 있는 `fixup!` 이면 합치기 기본값이 우선)
- J.13 범위 밖: 게시된 커밋(원격에서 도달 가능)·태그가 걸린 커밋·다른 로컬 브랜치의 커밋은 수집 단계에서 빠진다(`excluded`), 서명 커밋·merge 커밋이 범위에 있으면 재구성하지 않는다

## 절차
- S.1 수집 — repo 루트에서 `uv run --no-project python "${CLAUDE_SKILL_DIR}/commit_units.py" collect`
- S.1b 실패(detached HEAD·범위에 merge 커밋·기준 브랜치 없음)면 사유를 보고하고 끝, `on_default_branch` 가 true 면 기본 브랜치라 재구성하지 않는다(보고만)
- S.2 빠른 경로 — 범위 커밋 0개면 질문 없이 "점검할 미게시 커밋 없음" 한 줄로 끝
- S.2b 1개여도 판정 — 파일 목록이 한 목적으로 보이고(서로 무관한 영역이 섞이지 않음) 플래그가 없고 제목이 관례에 맞을 때만 "이상 없음" 한 줄로 끝
- S.3 판정 — 커밋별 `files`·`flags`·`overlaps`, 필요한 커밋만 `commit_units.py show <sha>` 로 패치 확인(raw `git log/show` 금지)
- S.4 제안 표 — 바꿀 것이 없으면 "이상 없음"(질문 없음), 있으면 `현재 커밋 → 제안 → 이유` 표와 함께 해당될 때만 아래를 적는다
- S.4a 중간 커밋 미검증 — 재구성으로 생긴 중간 커밋은 hook·빌드를 거친 적 없는 조합(최종 tree 는 원래와 같다)
- S.4b 커밋과 그 되돌림을 합쳐 없애는 것(drop)은 지원하지 않는다
- S.4c 수동 분할 필요(hunk 단위)
- S.4d 이 브랜치에서 이미 push 돼 제외된 커밋 수(`excluded.published`)·태그로 제외된 커밋 수(`excluded.tags`)
- S.5 승인 — `AskUserQuestion` 으로 적용/보류, 미게시 로컬 이력이라 되돌릴 수 있지만 재구성 전 승인은 사용자가 정한 규칙(2026-09-24)
- S.5b 물을 수 없는 흐름(무인 실행)이면 적용하지 않고 제안 표만 보고에
- S.6 적용 — 계획 JSON 을 스크래치 파일에 `Write` 로 쓰고 `uv run --no-project python "${CLAUDE_SKILL_DIR}/commit_units.py" apply <계획 파일>`
- S.6b 성공하면 `new_head`·`commits`(커밋별 sha·제목·파일)·`backup_ref`·`rollback`
- S.6c 실패하면 브랜치·index·작업트리는 호출 전 그대로(repo 의 commit-msg hook 이 스스로 일으킨 부작용은 예외) — 오류 문구를 그대로 보고, 계획을 고쳐 다시 시도하거나 보류
- S.7 보고 — `commits` 의 커밋별 파일이 제안 표와 맞는지 확인(순서를 바꾸면 한 커밋의 변경이 뒤 커밋과 상쇄돼 파일이 빠질 수 있다 — 최종 tree 가 같아도 제안과 다르면 되돌리기를 안내)
- S.7b 새 커밋 sha 목록·백업 ref·되돌리기 명령(`rollback`)을 보고에, 호출한 쪽의 기록 파일(plan 등)에는 쓰지 않는다

## `/e merge` 에서 부를 때
- M.1 `/e merge` 는 push 전에 `commit_units.py pending origin/<default>` 로 PR 에 실릴 커밋 중 `wip`·`fixup`(`squash!`·`amend!` 포함) flag 커밋을 찾는다
- M.2 분류 — `rewritable`(이 스킬 범위 안) / `published`(원격 추적 ref 가 도달) / `held`(원격엔 없고 다른 로컬 브랜치·태그가 붙잡음) / `blocked`(범위를 재구성할 수 없음 — `range_error`: merge 커밋·서명 커밋·기본 브랜치 등, apply 가 거부할 조건을 `pending` 이 미리 본다)
- M.3 `rewritable` 이 있을 때만 이 스킬을 `wip`·`fixup` flag 커밋 정리로 범위를 좁혀 부른다(`review-followup`·`plan-only` flag 는 대상 아님)
- M.4 `wip`·`fixup` flag 커밋마다 합치기(`fixup_of` 또는 목적이 같은 앞 커밋) 또는 정식 제목으로 reword(`{"from": [sha], "message": ...}`) 중 하나를 제안
- M.5 대상이 범위 밖(`fixup_of` null — 이미 게시된 단위에 대한 `fixup!` 등)이면 reword, 범위 첫 커밋이 `wip` 라 합칠 앞 커밋이 없어도 reword
- M.6 합치기를 제안하는 flag 커밋에는 제안 표에 "충돌 시 reword: `<제목>`" 을 함께 적어 한 번의 승인으로 둘 다 덮는다
- M.7 apply 가 충돌(`merge-tree --write-tree 실패`)로 거부하면 보류하지 말고 그 커밋만 표에 적은 reword 로 바꿔 한 번 다시 적용 — 같은 파일을 여러 단위가 고친 뒤의 `fixup!` 이 이 경우라, 보류하면 `/e merge` 가 재실행해도 같은 자리에서 멈춘다
- M.8 표에 없던 계획으로 바꿔야 하면 다시 묻는다
- M.9 flag 와 무관한 split·순서·메시지 제안은 표에 참고로만, 계획에 넣지 않는다(보류하면 머지 전체가 멈춘다)
- M.10 보류·적용 실패의 후속 처리는 `/e` 가 한다(이 스킬은 결과만 돌려준다)

## 계획 JSON
- K.1 `collect` 가 준 `base`·`head` 를 그대로 돌려보낸다(그 사이 브랜치가 움직였으면 apply 가 거부), `commits` 는 새 이력의 순서
- K.2 예시: `"schema": 1`, `base`·`head`, 합치기(`from` 2개), 메시지 바꾸기, 같은 커밋을 `paths` 로 두 항목에 나누기(각각 `message`)
- K.3 `from`: 이 새 커밋에 담을 원래 커밋들(원래 순서대로), 여럿이면 합치기 — 첫 커밋이 대상이고 author·메시지를 물려받음, 나머지의 트레일러(`Co-Authored-By` 등)는 중복 없이 합쳐진다
- K.4 `paths`: 파일 단위로 나눌 때만 — 그 커밋들의 변경 중 이 경로만, 나눈 항목은 `message` 필수, 원래 커밋의 모든 파일이 항목들에 빠짐없이·겹침 없이 배정, rename 은 옛·새 경로를 같은 항목에
- K.5 `message`: 새 메시지, 생략하면 대상 커밋 메시지 — 계획이 메시지를 주거나 트레일러 병합으로 결과 메시지가 원본과 달라지면 repo 의 `commit-msg` hook 을 거친다(거부되면 적용 전체가 거부, hook 이 고친 메시지는 그대로 쓴다)
- K.6 세션마다 다른 트레일러(`Claude-Session` 등)가 있는 커밋끼리 합치면 거의 항상 hook 이 돈다
- K.7 계획 형식의 정본은 `commit_units.py` 의 `validate_plan`

## 하지 않는 것
- N.1 push·force-push — 게시 커밋은 범위에 들어오지 않으므로 필요한 경우가 없다
- N.2 기본 브랜치(main·master 등)의 재구성, 서명 커밋·merge 커밋이 있는 범위의 재구성, hunk 단위 분할, drop
- N.3 스크립트가 거부한 것을 git 명령으로 직접 우회하는 것

## 다른 파일이 가리키는 표지
- 절 `## \`/e merge\` 에서 부를 때` — `skills/e/SKILL.md` M3 3) "that SKILL's `/e merge` section". 번역 뒤에도 제목에 `/e merge` 를 담는다.
- 절차 번호 1~7 — 다른 파일이 번호로 가리키지는 않는다(번역 뒤에도 그대로).

## 핵심 문구 검색 세트
`commit_units.py` · `collect` · `commit_units.py show <sha>` · `commit_units.py pending origin/<default>` · uv run --no-project python "${CLAUDE_SKILL_DIR}/commit_units.py" · `fixup_of` · rebase --autosquash · HEAD~n · `plan-only` · `wip:` · `fixup!` · `squash!` · `amend!` · `overlaps` · `convention_samples` · `excluded` · excluded.published · excluded.tags · `on_default_branch` · `files` · `flags` · `new_head` · `commits` · `backup_ref` · `rollback` · AskUserQuestion · `rewritable` · `published` · `held` · `blocked` · `range_error` · `review-followup` · merge-tree --write-tree 실패 · {"from": [sha], "message": ...} · "schema": 1 · `validate_plan` · commit-msg · Co-Authored-By · Claude-Session · AGENTS.md · 2026-09-24 · git log/show · /e merge · /commit-check · ${CLAUDE_SKILL_DIR}
