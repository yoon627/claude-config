---
title: commit-check-skill — 브랜치 커밋 단위 점검·승인 후 재구성 스킬 + dlc 마무리 연결
status: done
started: 2026-09-24
updated: 2026-09-24
---

# Goal
브랜치의 커밋들이 "리뷰 가능한 하나의 목적 단위"인지 점검하고, 승인하면 코드 내용은 그대로 둔 채 커밋 경계만 재구성하는 `commit-check` 스킬을 만든다. dlc 마무리(16단계)에서 호출하고, 원칙은 전역 CLAUDE.md §8 에 짧게 둔다.

# Intent
- Problem: 커밋 단위 판단(후속 수정을 어느 커밋에 합칠지, 목적이 섞인 커밋을 나눌지, 메시지 prefix)이 매번 추론으로 갈린다(cstp_compliance 2026-09-15~16 FE 커밋 분리·`fix`/`refactor` 논쟁). 규칙은 cstp `AGENTS.md:75` 에만 있고 전역에는 없다.
- Constraints (사용자 확인 2026-09-24): 재구성은 **제안 표 → 승인 후 실행**. 호출 시점은 **dlc 마무리 과정**. 원칙 명시는 **전역 CLAUDE.md 만**(Codex 파일 제외). 코드 내용은 바꾸지 않는다(사용자 요청 "커밋 단위 점검"의 전제 — 재구성 전후 최종 트리 동일).
- Out of scope: Codex 쪽(`~/.codex/AGENTS.md`·`~/.claude/AGENTS.md` 규칙 추가, `~/.agents/skills` 등록) — 사용자가 전역 CLAUDE.md 만 선택. `/e merge` 연결 — 사용자가 dlc 마무리를 선택. hunk 단위 분할 — 파일 단위만 자동, hunk 단위는 제안·수동 안내. repo 별 메시지 형식 규칙 자체(각 repo AGENTS/CLAUDE 가 정본, 스킬은 읽기만). 게시(push)된 커밋 재작성 — 아래 Decisions.
- 분할: 없음 — 스킬 단독 머지(1단계) → dlc·CLAUDE.md 연결(2단계)로 나누면 순서대로 머지해도 무모순이다. 나누지 않는 이유는 사용자가 dlc 연결까지를 한 요구로 지정했고, 연결 전 실사용 관찰(Acceptance 9)을 이 plan 안에서 하므로 분리의 이득(dogfooding 기간)이 plan 고정비(worktree·리뷰·머지 2회)보다 작아서다.
- Open questions: 없음.

# Acceptance
1. `skills/commit-check/SKILL.md`(frontmatter `name: commit-check`)와 `skills/commit-check/commit_units.py`·`test_commit_units.py` 가 있고 `bash skills/improve/improve.sh` 에 `[error]` 가 없다.
2. **범위(collect)** — fixture 테스트: 재작성 대상 = HEAD 에서 도달 가능하지만 다른 로컬 브랜치·원격 ref·태그 어디에서도 도달 불가한 커밋(따라서 로컬·origin default 모두 제외). 로컬 main 이 origin 보다 앞선 경우·뒤처진 경우, push 된 커밋이 섞인 경우 각각 올바른 범위를 낸다. 범위에 merge 커밋이 있거나 범위 부모가 하나가 아니면 거부(비0).
3. **수집 내용(collect)** — JSON 에 `schema`·`base`·`head`, 커밋별 sha·제목·본문·author·파일(경로·상태·rename 쌍, `-z` 로 한글 경로 원문)·변경량, 플래그(`wip:`·`fixup!`·`squash!`·"리뷰 반영"류 제목, plan 전용 커밋, 빈 커밋), 파일 overlap(뒤 커밋이 앞 커밋 파일을 다시 고침 — `plans/**` 제외), 제외된 게시 커밋 수, 기본 브랜치 최근 제목의 관례 샘플, 서명 사용 여부를 낸다.
4. **재구성(apply)** — fixture 테스트: 합치기·순서 변경·메시지 수정·파일 단위 분할(합치기+분할 조합 포함)이 계획대로 된다. 결과 검증: 새 HEAD tree OID = 원래 HEAD tree OID, 결과 커밋 수·제목·커밋별 파일 집합이 계획과 일치, author 이름·메일·날짜가 원본(합치기면 대상 커밋) 값, 원본 `Co-Authored-By` 등 트레일러 보존(합쳐진 커밋의 트레일러는 중복 없이 합침).
5. **실패 시 상태 불변(apply)** — 잘못된 계획(커밋 누락·중복·분할 경로 누락/중복·rename 쌍 분리), 계획의 `head`/`base` 가 현재와 다름, 진행 중 rebase·merge·cherry-pick, detached HEAD, 재구성 중 충돌(merge-tree exit 1), 빈 커밋이 생기는 계획, 서명 커밋이 범위에 있음, 새 메시지가 commit-msg hook 에 거부됨, git 2.40 미만 — 각각 비0 종료하고 심볼릭 HEAD·브랜치 ref·index·`status --porcelain` 이 호출 전과 같다.
6. **push 하지 않음** — git 호출 인자를 가로채는 테스트로 apply 전 과정에 `push` 가 없음을 확인.
7. **롤백** — apply 가 백업 ref(`refs/commit-check/<branch>/<UTC>`)를 남기고, 출력한 롤백 명령(`git update-ref refs/heads/<branch> <원래 HEAD sha> <new>`)으로 원래 HEAD 로 돌아간다(fixture). 백업 정리는 같은 트랜잭션 안에서 이 브랜치 직속 백업만 대상으로 한다.
8. 문서: CLAUDE.md §8 커밋 단위 원칙 bullet, `skills/dlc/SKILL.md` 16단계 호출 지점(결과 sha·백업 ref 는 Report 에만), README `skills/commit-check/` 섹션.
9. 실사용 관찰: (a) 이 repo 실제 브랜치에서 `collect` (b) 실제 history 복사본에서 합치기 시나리오 `apply` 후 트리 동일 (c) 다른 repo(cstp_compliance) worktree 세션 경로에서 스크립트 절대경로 호출이 worktree 가드를 통과하는지 — 관찰 불가면 그 사실과 사유를 Report 에.
10. `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음).

# Progress
- 2026-09-24: 착수. 사용자 결정 3건(승인 후 재구성·dlc 마무리·전역 CLAUDE.md 만). 근거 조사 — 규칙 원문 cstp `AGENTS.md:75`, 전역 규칙 부재 확인, git 2.54 비대화형 `rebase --autosquash`·todo 복사 `rebase -i` 동작 실측.
- 2026-09-24: architecture-reviewer(planning) REQUEST CHANGES·plan-reviewer(+codex) CONDITIONAL — in-place rebase 는 실패 시 abort 도 실패(exit 128, worktree 가 rebase 도중 상태로 남음)·분할 재커밋이 author/date/트레일러 유실·`set -e`+`&&` 로 파일 누락이 exit 0(리뷰어 실측). 설계를 plumbing 재조립 + CAS update-ref 로 전환, scratch 실측으로 순서 변경·합치기·파일 분할·author/트레일러 보존·CAS 1회성·작업트리 무변경 확인.

- 2026-09-24: plan-reviewer 재검토 CONDITIONAL(경미) 반영. TDD Red(모듈 없음) → 구현 → 41 테스트 Green. SKILL.md·CLAUDE.md §8·dlc 16·README 연결, improve.sh error=0. 실사용: 이 repo collect(게시 커밋 4 제외), ~/.claude 실제 history clone 에서 합치기 apply(tree 동일·트레일러 보존·clean), cstp main·worktree 5곳 read-only collect 정상. cstp worktree **세션**의 가드 통과 여부는 이 세션에서 관찰 불가.

- 2026-09-24: architecture-reviewer(정밀) APPROVE, code-reviewer(+codex high) REQUEST CHANGES → fix loop 1회: 재현 테스트 16개 추가(Red 15) 후 수정, 57 테스트 Green. simplify: apply 의 범위 이중 계산 제거.

- 2026-09-24: 격리 runner 최종 검증(fix loop 2 전 코드) verify ALL PASS·57 OK·improve error=0·plan-lint·wiki clean. code-reviewer 재검토 → 새 Major(원격 ref 전체 verify 가 symref `origin/HEAD` 와 충돌해 clone repo 에서 apply 항상 실패) → fix loop 2: 재현 테스트(Red: exit 128 multiple updates via symref) 후 verify 대상을 각 remote 의 `refs/remotes/<remote>/<branch>` 로 한정(없으면 zero oid), `_nested_conflict` 선형화, SKILL hook 조건 문구. 58 OK, verify ALL PASS 재실행, 실제 history clone(origin/HEAD 있음) apply 재관찰 tree 동일. 판정 DONE.

- 2026-09-24: 커밋 0244549(스킬·연결)·eabdd7d(wiki `commit-restructure-plumbing-cas`). 자기 적용 결과 이상 없음. `/e merge` → PR #171.

# Next
(없음 — PR #171 머지로 종료)

# Decisions
- 판단(모델)과 실행(스크립트)을 나눈다 — 수집·검증·재조립·ref 이동은 결정적이라 `commit_units.py` 서브커맨드(`collect`/`show`/`apply`)로, 어떤 커밋을 합치고 나눌지는 SKILL.md 기준으로 모델이 판정해 JSON 계획으로 넘긴다. 계획 스키마의 정본은 스크립트의 검증 함수 하나(SKILL.md 는 예시만). 기각: 모델이 git 명령을 직접 조합(안전 조건을 매번 재현해야 하고 테스트 불가).
- **재구성은 plumbing 으로, 사용자 작업 공간 밖에서** — 새 커밋마다 원본 커밋(분할이면 경로를 제한한 합성 커밋)을 `git merge-tree --write-tree --merge-base=<원본 부모>` 로 현재 tip 위에 3-way 적용하고 `git commit-tree` 로 커밋을 만든다. 임시 index 는 `GIT_INDEX_FILE` 로만. 모든 검증을 통과한 뒤 마지막에 백업 ref 를 쓰고 브랜치를 CAS 로 옮긴다(`update-ref refs/heads/<br> <new> <old>`). 트리가 같으므로 사용자 index·작업트리는 건드릴 필요가 없고, 실패하면 만든 객체를 버리기만 한다(abort 경로 없음). 기각: (1) 사용자 worktree 에서 `rebase -i` + todo(실패 시 abort 가 실패해 worktree 가 망가짐 — 리뷰어 실측), (2) 임시 worktree 에서 rebase 후 ref 이동(체크아웃 비용·hook 실행·정리 필요, plumbing 이 같은 격리를 더 싸게 준다), (3) `commit --fixup` + `rebase --autosquash`(합치기만 되고 분할·순서·메시지 수정은 안 되며 in-place 문제 동일), (4) 새 브랜치에 `checkout <backup> -- <files>` 재조립(파일이 여러 커밋에 걸쳐 변하면 중간 상태 재현 불가).
- **hook** — `commit-tree` 는 hook 을 실행하지 않는다. 최종 트리가 원본과 같고 working tree 를 거치지 않으므로(eol 정규화·formatter 개입 없음) 파일 내용 hook 을 다시 돌릴 대상이 없다고 본다. 단 순서를 바꾸면 merge-tree 가 원본에 없던 중간 blob 을 만들 수 있어, 중간 커밋은 "미검증"이다. 계획이 새로 쓴 **메시지**는 유일한 새 내용이라 `git hook run --ignore-missing commit-msg -- <msgfile>`(git 2.36+, 파일 무변경)을 돌리고, 실패하면 계획 거부·hook 이 고친 메시지는 그대로 쓴다. CLAUDE.md §8 의 `--no-verify` 금지는 "hook 에 막힌 커밋을 우회"하는 것이라 해당하지 않는다. 대신 분할로 생긴 중간 커밋은 hook·빌드를 거친 적 없는 조합이라 제안 표에 "중간 커밋 미검증"을 표시한다. 기각: hook 을 돌리고 실패·수정 시 롤백(cstp 의 파일 수정 hook 이 중간 상태를 고쳐 매번 롤백 — 스킬이 주 사용처에서 동작 안 함).
- **게시된 커밋은 불변** — 재작성 범위에서 어느 원격 ref 에서든 도달 가능한 커밋은 뺀다. 따라서 force-push 경로가 없고 `/e merge` M3 의 일반 push 와 충돌하지 않는다. 원격 정보가 없으면(원격 없음) 로컬 default·다른 브랜치만 기준. 기각: push 된 브랜치도 재작성 + `--force-with-lease` 확인(확인 주체·경로가 없고 M3 가 non-ff 로 중단).
- **범위 경계** — 제외 기준 ref 를 명시 열거한다: 현재 브랜치를 뺀 `refs/heads/*`·`refs/remotes/*`·`refs/tags/*`(`--all` 금지 — 자기 백업 ref `refs/commit-check/*` 가 범위를 잠근다). 태그가 걸린 커밋은 재작성하면 태그가 옛 커밋에 남으므로 제외한다. 게시 판정은 로컬 remote-tracking ref 기준이라 fetch 안 한 다른 머신의 push 는 못 본다(이 repo 의 push 경로 `/e merge` 는 tracking ref 를 갱신하므로 실용상 수용). 이 규칙으로 로컬 default 와 origin default 가 모두 제외된다(CLAUDE.md §8 은 로컬 ff-merge 후 push 안 한 상태를 정상으로 둔다 — 이 worktree 실측에서도 로컬 main≠origin/main). 다른 로컬 브랜치가 포함한 커밋도 뺀다(stacked branch). 범위가 선형이 아니면(merge 커밋) 거부.
- **merge-tree 판정** — exit code 로 한다(0 clean·1 충돌·그 외 오류). 충돌이어도 첫 줄에 tree OID 가 찍히므로 출력만 보면 충돌 tree 로 커밋을 만들 수 있다.
- **빈 커밋** — 새 tree 가 부모 tree 와 같으면 거부. 단 원본이 원래 빈 커밋(`--allow-empty`)이고 그 커밋만 단독으로 옮기는 항목은 허용. 커밋과 그 revert 를 합쳐 비우는(drop) 계획은 v1 미지원 — 제안 표에 적는다.
- **git 버전** — apply 는 시작할 때 `git version` 이 2.40 미만(`merge-tree --merge-base` 미지원)이면 거부.
- **ref 이동은 트랜잭션 하나** — `git update-ref --stdin` 의 `start`/`create <backup>`/`update refs/heads/<br> <new> <old>`/`commit` 으로 백업 생성과 CAS 를 원자적으로 묶는다.
- **dirty 작업트리 허용** — plumbing 은 index·작업트리를 건드리지 않고 최종 트리가 같아 staged·unstaged 변경이 새 HEAD 기준으로도 그대로 유효하다.
- **계획 = 수집 결과에 묶임** — collect 가 낸 `base`·`head` 를 계획이 그대로 돌려보내고, apply 는 현재 HEAD·범위가 다르면 아무것도 하지 않고 종료(승인 뒤 fix loop 재커밋·/e WIP 로 HEAD 가 움직인 경우).
- **author·트레일러 보존** — 새 커밋의 author 이름·메일·날짜는 원본(합치기면 대상 커밋) 값, committer 는 현재 사용자(rebase 와 같은 관례). 메시지는 계획이 주면 그것, 없으면 대상 커밋 메시지. 합쳐진 커밋들의 트레일러(`Co-Authored-By` 등)는 중복 없이 합친다.
- **서명** — 범위에 서명된 커밋이 있으면 v1 은 거부한다(서명을 조용히 잃으면 안 된다). 모든 `commit-tree` 호출에 `--no-gpg-sign` 을 붙여 `commit.gpgSign` 설정만 켜진 경우의 pinentry 대기를 막는다.
- **경로·메시지 전달** — git 출력은 `-z` 로 읽고, 경로·메시지는 셸 문자열로 만들지 않는다(subprocess 인자 리스트·stdin). rename 쌍은 같은 분할 그룹이어야 한다(아니면 계획 거부).
- **백업 ref** — `refs/commit-check/<branch>/<UTC timestamp>`(refs/heads 밖, 모든 worktree 공유). 같은 브랜치 백업은 최근 5개만 남긴다. 브랜치 삭제 시 함께 지우는 연결은 Deferred. 롤백은 `update-ref`(CLAUDE.md §8 의 `reset --hard` 금지와 무관 — 트리가 같아 ref 만 옮기면 된다).
- **fixture 격리** — 테스트의 모든 git 호출은 `GIT_CONFIG_GLOBAL=/dev/null`·`GIT_CONFIG_NOSYSTEM=1`·명시 identity·`init -b main`·상속된 `GIT_DIR`/`GIT_INDEX_FILE` 제거 env 로. 스크립트는 git 실행 함수에 env 를 받을 수 있게 둔다.
- **worktree 가드 대응** — 판정에 필요한 정보(커밋별 파일·diffstat, 필요 시 `show <sha>` 로 패치)를 스크립트가 제공해 모델이 raw git 을 치지 않게 한다.
- **dlc 연결** — 16단계 커밋 뒤·Report 전에 규모와 무관하게 `commit-check` 를 부른다. 생략 판단은 스킬이 한다(범위 커밋 1개 이하이고 플래그 없으면 질문 없이 한 줄). 결과 sha·백업 ref 는 plan 이 아니라 Report 에(plan 에 쓰면 tree 가 다시 dirty). 제안이 없으면 질문하지 않는다. 거절·적용 실패는 DONE 을 되돌리지 않고 Report 리스크로 남긴다. 두 번째 실행은 제안이 없어야 한다(멱등).
- **승인을 받는 이유** — 미게시 로컬 이력 재작성은 백업이 있어 §1 기준으로는 확인 대상이 아니지만, 사용자가 "제안 → 승인 후 실행"을 명시적으로 골랐다(2026-09-24). 다음 세션이 마찰로 보고 자동화하지 않도록 남긴다.
- 스킬 이름 `commit-check` — 동작(점검)이 이름에 드러나고 기존 짧은 이름(c·e·wt)과 겹치지 않는다.
- ~~⚠️ `-i` 미지원 안내와 상충~~ → plumbing 전환으로 `rebase -i` 를 쓰지 않아 해소.

# Review Disposition
- [arch 1] 계획이 수집 결과에 안 묶임 — fix(`base`·`head`·`schema` 계약, apply 재대조).
- [arch 2] 실패 복구 주체 미정 — fix(plumbing 으로 abort 경로 자체 제거, 스크립트가 끝까지 책임).
- [arch 3] 재커밋 hook 정책 — fix(commit-tree 는 hook 미실행, 새 내용 없음 근거, 중간 커밋 미검증 표시).
- [arch 4] exec 문자열 로직 — fix(exec 없음, Python 함수 + 인자 리스트).
- [arch Minor] push 된 브랜치 안전 조건 — fix(게시 커밋을 범위에서 제외).
- [arch Minor] 백업 ref 수명 — fix(이름 규칙·최근 5개), 브랜치 삭제 연동은 Deferred.
- [arch Minor] 생략 조건 위치 — fix(스킬이 판단).
- [arch Minor] fixture git 설정 격리 — fix.
- [plan 강1] in-place abort 실패 — fix(plumbing).
- [plan 강2] exec 셸 에러 처리 누락 — fix(셸 없음, 결과 커밋별 파일 집합 검증).
- [plan 강3] author·date·트레일러 유실 — fix(보존 규칙 + Acceptance 4).
- [plan 강4] base 경계 — fix(로컬·origin default·다른 브랜치·원격 모두 제외).
- [plan 강5] push 된 커밋 재작성 — fix(게시 커밋 불변). Intent "그 밖" 의 확정 서술 제거.
- [plan 강6] merge·CAS·빈 커밋 — fix(merge 거부, 계획 CAS, 빈 커밋 계획 거부).
- [plan 강7] 파일 수정 hook — fix(hook 미실행 결정 + 근거).
- [plan 강8] Acceptance 불충분 — fix(4·5·6·7 재작성, tree OID 비교, 인자 가로채기 테스트).
- [plan 약] self-flag — resolved(rebase -i 미사용).
- [plan 약] 기각 대안 기록 — fix.
- [plan 약] 가장 위험한 단계 — fix(실패 시 상태 불변 테스트를 Red 맨 앞, dlc 연결은 실사용 관찰 뒤).
- [plan 약] 분할 근거 — fix(근거를 고정비 대비 이득으로 변경).
- [plan 약] dlc 연결 세부 — fix(Decisions dlc 연결).
- [plan 약] plan 경로 overlap 오염 — fix(`plans/**` 제외).
- [plan 약] 경로 인코딩·주입 — fix(`-z`, 인자 리스트, rename 쌍).
- [plan 약] worktree 가드 — fix(`show` 서브커맨드) + Acceptance 9(c).
- [plan 약] CI fixture 격리 — fix. CI git 버전: `merge-tree --merge-base` 는 git 2.40+ 필요 — ubuntu-latest 기본 git 이 그 이상인지 구현 중 CI 로 확인.
- [plan 약] 롤백 명령 — fix(update-ref, reset --hard 불요).
- [plan 재검토 1] hook 근거 정정·commit-msg 공백 — fix(근거 문장 수정, 새 메시지에 `git hook run commit-msg`, §8 bullet 에 "commit-tree 재조립은 `--no-verify` 우회가 아님").
- [plan 재검토 2] 설정만 켜진 서명 — fix(`--no-gpg-sign`).
- [plan 재검토 3] 범위 — fix(명시 ref 열거·`--all` 금지·태그 제외·tracking ref 한계 기록). 제외 원인별 개수 출력 — fix.
- [plan 재검토 4] merge-tree exit code·원래 빈 커밋·drop 미지원 — fix. rename 분할 fixture — fix.
- [plan 재검토 5] git 2.40 가드 — fix(+테스트).
- [plan 재검토 약] update-ref 트랜잭션 — fix. dirty 작업트리 — 허용으로 명시.
- [arch 정밀 Minor] rebuild 책임 혼재·hook 이 tree 적용 루프 안 — fix(`_entry_tree`·`_entry_message` 분리). hook 을 전 항목 tree 확정 뒤로 미루는 것은 wontfix(commit-tree 가 메시지를 요구해 tree·커밋 2단계로 나눠야 하고, hook 부작용은 문서 보장 문구에서 예외로 한정).
- [arch 정밀 simplify 위임] SKILL 절차 7 이 dlc 규칙·근거를 되풀이 — fix("호출한 쪽 기록 파일에 쓰지 않는다"만 남김).
- [code Major] prune 이 `<branch>/x` 네임스페이스와 섞여 자기 백업 삭제 — fix(직속 `<stamp>` 만, 테스트).
- [code Major] CAS 뒤 prune 실패 시 실패 보고 — fix(오래된 백업 delete 를 같은 트랜잭션에, 테스트).
- [code Major PLAUSIBLE] 빠른 경로가 1커밋 분할 판정을 건너뜀 — fix(0개만 무판정, 1개도 파일 목록으로 판정). Decisions dlc 연결의 "1개 이하 생략"을 이것으로 대체.
- [code Minor] 하위 디렉토리 cwd 에서 삭제 분할 실패 — fix(삭제도 `--index-info` mode 0 루트 기준, 테스트).
- [code Minor] 태그·브랜치 동명 — fix(`symbolic-ref HEAD` 전체 ref, 테스트).
- [code Minor] `excluded.published` 의미 — fix(기본 브랜치 도달분 제외, 테스트). 앞 Progress 의 "게시 커밋 4 제외"는 upstream 커밋을 잘못 센 값이었다.
- [code Minor PLAUSIBLE] 재배열로 변경 상쇄가 subset 검사 통과 — fix(결과에 커밋별 파일을 내고 SKILL 7단계에서 제안과 대조). 엄격 비교는 정당한 되돌림 fixup 을 거부해 wontfix.
- [code Minor] 트레일러 `---`·Change-Id·메시지 바뀐 합치기의 hook 미실행 — fix(`--no-divider`, 단일값 키는 대상 우선, 계획 메시지 또는 결과가 원본과 다르면 hook). pseudo-trailer 승격(Nit) — wontfix(git 트레일러 규칙 그대로).
- [code Minor PLAUSIBLE] commit-msg hook 부작용 — fix(문서 보장 문구에 예외 명시, hook 에는 `GIT_LITERAL_PATHSPECS=0`).
- [code Minor PLAUSIBLE] collect~CAS 사이 push 경합 — fix(트랜잭션에 원격 ref `verify`).
- [code Minor] NUL 파싱 — fix. 파일↔디렉토리 분리 분할 — fix(검증 단계 거부, 테스트). 잘못된 형식 계획 traceback — fix(테스트). 단일 브랜치 repo 오류 문구 — fix(테스트). README 과장 — fix. CLAUDE.md bullet 게시 범위 — fix("아직 push 하지 않은 커밋").
- [code Minor PLAUSIBLE] argv 길이(Windows) — 제외 ref 는 fix(`rev-list --stdin`), 분할 경로 argv 는 defer(보통 수 개). Windows CRLF — fix(`newline="\n"`).
- [code 테스트 누락] gitlink·dirty 내용·삭제 분할·prune 네임스페이스·하위 디렉토리 — fix. mode/symlink 분할 — defer(리뷰어 probe E8 로 정상 확인).
- [code Nit] `show` 옵션 주입 — fix(테스트). 관례 샘플 merge 제목 — fix(`--no-merges`, 테스트). `sequencer` — fix. 강제 종료 시 임시 index 잔존 — wontfix(ref·사용자 index 무영향, `.lock` 은 정상 경로에서 정리). Acceptance 7 형태 — fix(문구).
- [code 재검토 Major] 원격 ref verify 가 symref 와 충돌 — fix(브랜치 upstream ref 만 verify, 처음 push 경합도 zero oid 로 잡음, 테스트). [code 재검토 Minor] 새 원격 ref 미감지·무관 fetch 로 실패 — 같은 수정으로 해소. SKILL hook 조건 문구 — fix. `_nested_conflict` O(n²) — fix.
- [code Open] 기본 브랜치에서 실행 — fix(apply 거부, collect 는 `on_default_branch` 표시, 테스트). 무인 dlc 흐름에서 승인 불가 — fix(SKILL: 적용하지 않고 제안만).
- [plan 약] 중간 커밋 빌드 가능성 — fix(제안 표 표시).
- [plan 약] §1 긴장 — fix(Decisions 승인 이유).
- [누락 시나리오] 진행 중 rebase 등·빈 범위·원격 없음 — Acceptance 5·2 에 포함. submodule 포인터(gitlink)는 merge-tree 가 그대로 다루므로 별도 처리 없음(fixture 1개로 확인). eol 정규화는 plumbing 이 working tree 를 거치지 않아 해당 없음. Bash timeout 중단 — apply 는 ref 이동 전까지 사용자 상태를 안 바꾸므로 중단돼도 불변.

# Deferred
- `~/.codex/AGENTS.md` §8(a) 가 merge 직후 원격 브랜치를 확인 없이 삭제하도록 적혀 있다(CLAUDE.md §8 "원격 삭제는 항상 확인"과 반대, `~/.claude/AGENTS.md` 는 PR #170 에서 수정됨). 심각도 Major(Codex 가 원격 삭제를 무확인 실행 가능). 사용자가 Codex 파일 제외를 골라 이 작업 범위 밖.
- 백업 ref 를 브랜치 삭제(/e 7단계) 때 함께 정리하는 연결 — Minor.
- 분할 경로를 argv 로 넘기는 부분(`ls-tree -- <paths>`)의 Windows 명령줄 길이 — Minor, 경로 수백 개일 때만.
- mode 변경·symlink 분할 fixture 테스트 — Minor(리뷰어 scratch probe 로 정상 확인).

# Key Files
- `skills/commit-check/SKILL.md` — 판정 기준·절차(신규)
- `skills/commit-check/commit_units.py` — collect/show/apply(신규)
- `skills/commit-check/test_commit_units.py` — fixture 테스트(신규)
- `CLAUDE.md` §8 — 커밋 단위 원칙 bullet
- `skills/dlc/SKILL.md` — 16단계 호출 지점
- `README.md` — 스킬 섹션

# Blockers
없음
