# 가리키는 곳 (translate-skill-e)

## 저장소 안 — 영향 없음(확인함)
단계 번호·M 코드·영어 라벨로만 가리키므로 번역으로 끊기지 않는다: `CLAUDE.md`(`/e` step 6·7·8, "the worktree cleanup rules", M4) · `skills/wt/SKILL.md:115`(`skills/e/SKILL.md` 2단계) · `skills/jira-worklog/SKILL.md:79,103` · `skills/jira-worklog/test_exit_contract.py:4-5` · `skills/c/SKILL.md:74` · `skills/commit-check/SKILL.md:40-46`·`commit_units.py:8` · `skills/dlc/SKILL.md:169`. CLAUDE.md 쪽 문구는 `check-e.js` 4절이 확인한다.

## 원문 그대로 둔 문자열 (입력·출력 문자열)
- `/e 머지` — 사용자가 입력하는 인자 토큰
- `"등록 불가"` — `skills/jira-worklog/jira_worklog.py` 가 출력하는 경고, `test_exit_contract.py` 가 고정한다. e 7단계 정리를 막는 신호라 번역하면 미등록 worktree 를 지울 수 있다
- `wip:` 제목 접두와 `(e checkpoint)` — `commit_units.py` 가 `^wip\b` 로 찾는다
- `main-autopull ⓑ` — 공용 wiki 가 가리키는 라벨

## 대응표 (e 안의 내부 라벨 — 번역 전후 개수가 같다, `check-e.js` 4b절)
6 전 → 6 pre · 복구 규칙 → recovery rule · 비차단 → non-blocking · worktree 정리 규칙 → Worktree cleanup rules · 임시 커밋 규칙 → Temporary commit rules · 2단계 경로 표기 → step 2 path notation · 지름길 → Shortcut · 중단 규칙 → Stop rule · 재수집 invariant → re-collection invariant · 경계 (안 하는 것) → Boundaries (what this skill does not do)

## [post-merge] 공용 wiki — main 세션
- `~/.claude/wiki/docs/worktree-lifecycle.md`
  - :3 `8단계 ⓑ`·`정리 규칙` → step 8 ⓑ·cleanup rules
  - :37 사유 줄 «미머지 → 유지»·«dirty → 유지»·«plan 이 worktree 내부 → 유지»·«worklog 실패 → 유지» → "unmerged → kept"·"dirty → kept"·"plan inside the worktree → kept"·"worklog failed → kept"
  - :41 `SKILL 정리 규칙` → SKILL Worktree cleanup rules
  - :42·:47 «"6 전" 절» → "6 pre" section
  - :61 `SKILL §8 ⓑ` — 그대로(번호와 ⓑ 유지)
  - :83·:84·:94 표의 Task 문구 «정리 후 `/e merge` 재실행» 등 → "clean up the commits, then rerun `/e merge`"·"PR #N waiting for checks, rerun `/e merge`"
- `~/.claude/wiki/pages/entity/worktree-isolation-bash-guard.md:80` — «6 전» → "6 pre"
- 그대로(역사 기록): `pages/decision/e-merge-mode.md`·`workflow-failures.md`·`dlc-wt-autoflow.md` 의 옛 한국어 인용
