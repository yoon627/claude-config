---
title: e-isolated-helper-order — /e 6·7단계 헬퍼를 격리 worktree 세션에서는 main 으로 나온 뒤 돌린다
status: in_progress
started: 2026-09-30
updated: 2026-09-30
---

# Goal
worktree 에 격리된 세션에서 `/e` 6단계(worklog)·7단계(상태 재수집) 헬퍼가 네이티브 Bash 가드에 거부돼 worklog 가 빠지거나 정리가 생략되는 일을 막는다. 비-메인 worktree 세션은 6단계 전에 `ExitWorktree(keep)` 로 나와 원래 디렉토리(보통 main)에서 헬퍼를 돌린다. 문서만 바꾸고 스크립트는 그대로 둔다.

# Acceptance
1. **등록 대상**: 복귀 흐름에서 worklog 미리보기·등록 모두 `<target_path>` 의 디렉터리 이름을 인자로 준다고 적혀 있고(SKILL "6 전" 절·6단계 등록 bullet), `jira_worklog.py` 가 `<이름> --register` 를 받는다 — 문서 대조 + argparse 실측.
2. **일관성**: SKILL "6 전"·6·7·8단계·정리 규칙·경계 절, `docs/worktree-lifecycle.md` §C, README 가 서로 모순되지 않는다 — 재리뷰 Critical/Major 0 + `rg -n "6 전|ExitWorktree" skills/e/SKILL.md docs/worktree-lifecycle.md` 대조.
3. **명령 실동작**: 문서에 적은 두 명령(main 에서 `run_worklog.sh <이름>`, `(cd "<target_path>" && bash …/collect-state.sh)`)이 실제로 돈다 — 이 세션의 실측(아래 Progress).
4. `bash scripts/verify.sh` 마지막 줄이 main 과 같은 skip 만 둔 `ALL PASS`, `bash skills/improve/improve.sh --ci` exit 0 — 격리 runner.

# Progress
- 2026-09-30: `/wt` 로 worktree 생성(base `origin/main@6f1d754`). 계획 전 조회로 공용 wiki `worktree-isolation-bash-guard`(가드 관찰)를 읽었다.
  - 근거 실측(같은 날 wiki-graph-search 의 `/e merge`): 격리 세션에서 `bash "$HOME/.claude/skills/jira-worklog/run_worklog.sh" wiki-graph-search` 가 거부됐다.
  - 우회는 값 캡처 → `ExitWorktree(keep)` → main 에서 `run_worklog.sh <이름>`·`(cd <wt> && bash …/collect-state.sh)` → 판정 → remove 였다. 같은 순서를 autopull-verified-client·check-links-alias 정리에서도 썼고 모두 성공했다(Acceptance 3).
- 2026-09-30: SKILL 6·7·8단계·정리 규칙, lifecycle §C, README 를 고쳤다. 격리 runner 결과: `verify.sh` `ALL PASS (skip: install-codex-skill.test.ps1)`, `improve --ci` exit 0.
- 2026-09-30: 코드 리뷰 REQUEST CHANGES — Major 1·Minor 4·Nit 7. Codex 미가용(workspace out of credits, 세션 마커 기록). 순서 규칙을 "6 전" 절로 떼고, 판별을 `ExitWorktree` 시도 결과로 바꿨다.
- 2026-09-30: 재리뷰 APPROVE — 이전 Major 해소(argparse 실측: `<이름> --register` 양쪽 순서 모두 name·register=True). Critical/Major 0, Minor 3·Nit 8 은 문구로 반영했다(처분은 # Review Disposition).
  - 재리뷰어의 가드 실측(이 격리 세션): `bash "$HOME/…"` 3/3 거부, `$HOME` 을 펼친 절대경로 bash 3/3 통과, `uv run --no-project python "$HOME/…"`(commit_units·jira_task `--help`) 2/2 통과.
- 2026-09-30: 문구 반영 뒤 격리 runner 재실행 — `verify.sh` `ALL PASS (skip: install-codex-skill.test.ps1)`, `improve --ci` exit 0. argparse 도 직접 확인했다(`<이름> --register`·`--register <이름>` 모두 name·register=True). evidence gate 1~4 를 모두 증거로 충족해 판정은 DONE 이다(status 는 머지 때 done).

# Next
- 커밋 → commit-check → 로컬 main(`1bd6939`) 위로 rebase·재검증 → ff-merge → 이 worktree 를 새 순서대로 정리(실측 재현) → main 세션에서 # Deferred 의 공용 wiki 적립.

# Decisions
- 관련 결정·관찰: 공용 wiki `worktree-isolation-bash-guard` 는 가드를 규칙이 아니라 관찰로 둔다(하네스 버전 의존). 그래서 문서에는 2026-09-30 실측과 버전 의존을 함께 적는다.
- 순서: 비-메인 worktree 세션은 "worktree 정리 규칙"의 값 캡처와 `ExitWorktree(keep)` 를 6단계 앞으로 당긴다. 5단계까지는 worktree 안에 둔다 — jira-task CLI 가 cwd 로 worktree·티켓을 추론하고, 그 호출 형태(`uv run python "$HOME/…"`)는 실측에서 통과했다.
- 판별은 세션 종류가 아니라 `ExitWorktree` 시도 결과로 한다(리뷰 Minor). 복귀하면 원래 디렉토리 흐름, no-op 이면 전처럼 worktree 안에서 돈다. no-op 분기에서는 거부되면 `$HOME` 을 펼친 절대경로로 한 번 다시 부르고, 그래도 worklog·collect-state 가 실패하면 정리를 생략한다.
- 명령: worklog 는 미리보기·등록 모두 `<target_path>` 의 디렉터리 이름 인자(`jira_worklog.py` 의 `name` 인자, 마커·등록 키도 디렉터리 이름). collect-state 는 `(cd "<target_path>" && bash "$HOME/.claude/skills/e/collect-state.sh")`. 둘 다 이 세션에서 실제로 돌린 형태다.
- 기각: 호출 형태만 바꾸기(`$HOME` 을 펼친 절대경로) — 오늘은 통과했지만 가드 규칙은 하네스 버전에 따라 바뀐다. worktree 밖에서 돌리는 순서는 가드 규칙이 바뀌어도 유지된다. 그래서 형태 바꾸기는 no-op 분기의 재시도로만 쓴다.
- 기각: `collect-state.sh` 에 경로 인자 추가 — 거부는 호출 형태에 걸리므로 경로 인자로는 풀리지 않고, 스크립트를 바꿔야 한다.
- 비-메인 worktree 세션은 이제 체크포인트 모드에서도 6단계 전에 나온다. 원래 8단계에서 언제나 나오던 비파괴 동작이라 최종 상태는 같다.
- 커밋 단위: 1개 — 문서 세 곳이 한 순서 규칙이다.

# Key Files
- `skills/e/SKILL.md` — 동작 헤더, "6 전" 절, 6단계 등록, 7단계 재수집, 8단계 대상·skip, worktree 정리 규칙, 경계 절
- `docs/worktree-lifecycle.md` — §C 서두·worktree 밖으로
- `README.md` — `/e` 정리 bullet

# Blockers
없음

# Review Disposition
코드 리뷰 1회차 — code-reviewer REQUEST CHANGES, Critical 0·Major 1·Minor 4·Nit 7. Codex 미가용(workspace out of credits).
- Major 복귀 흐름의 등록 명령에 worktree 이름이 없어 main 이 대상이 된다 — fix: 등록에도 미리보기와 같은 `<이름>` 을 준다.
- Minor 격리 범위를 `EnterWorktree` 경유로만 서술 — fix: 판별을 `ExitWorktree` 시도 결과로 바꿨다.
- Minor 정리 규칙이 `ExitWorktree` 재호출을 막지 않는다 — fix: 다시 부르지 않고, 재호출 no-op 을 no-op 폴백으로 처리하지 않는다.
- Minor 5단계 jira-task·M3-2 commit_units 의 가드 노출 — defer → 2회차 실측으로 해소(적힌 `uv run python "$HOME/…"` 형태 2/2 통과). 하네스가 바뀌면 다시 본다.
- Minor 6단계 실패와 무관하게 7단계가 삭제한다(기존 문제) — defer(# Deferred). no-op 분기는 2회차에 정리 생략을 명시했다.
- Nit 8단계 skip 조건, 정리 규칙 서두, 순서 규칙의 위치, 경로 따옴표, 중단 시 재실행 — fix.
- Nit "현재 worktree" 표현 — wontfix: 작업 worktree 를 가리켜 그대로 맞다.
- Nit collect-state 경로 두 형태 혼재, 운영 자산의 옛 서술(CLAUDE.md·dlc-early-stop.js) — defer(# Deferred).

코드 리뷰 2회차(targeted) — APPROVE, Critical 0·Major 0·Minor 3·Nit 8. 1회차 Major 해소 확인.
- Minor no-op 분기의 "헬퍼가 거부되면 정리 생략"이 worklog 를 포함하는지 모호 — fix: worklog·collect-state 가 거부·실패하면 정리 생략을 명시하고, 먼저 펼친 절대경로로 한 번 재시도한다.
- Minor "비결정적" 서술과 기각 사유가 실측과 다르다 — fix: 2026-09-30 실측과 버전 의존으로 고쳤고, 기각 사유를 새로 썼다.
- Minor plan `# Acceptance` 없음 — fix: 네 항목을 두고 대조한다.
- Nit lifecycle §C 서두, 동작 헤더·경계 절, '묶인 세션' 용어, §C no-op 폴백 시점, 8단계 "대상", "main" → "원래 디렉토리(보통 main)", 재개 안내 — fix.
- Nit 이름 선택 모호(동명 worktree)·복귀와 worklog 사이 수 초의 시간 귀속·PowerShell `( )` 는 서브셸이 아님 — risk accept: `/wt` 가 이름 중복을 막고, 시간 차는 초 단위이며, 제거 전 "cwd 가 대상 밖" 게이트가 있다.

# Deferred
- 7단계 삭제 조건에 6단계 결과가 없다. 등록 게이트·네트워크 실패로 worklog 가 빠져도 worktree 가 지워져 다시 등록할 수 없다 — Minor(기존 문제), `skills/e/SKILL.md` 6·7단계.
- 7단계 collect-state 호출이 상대경로(`bash skills/e/collect-state.sh` — `~/.claude` 에서만 해석)와 `$HOME` 절대경로로 섞여 있다 — Nit, `skills/e/SKILL.md` 7단계.
- `CLAUDE.md`(§3-1 "복귀는 `/e` 8단계", §8 worklog 줄)와 `scripts/dlc-early-stop.js` 주석이 "8단계에서 main 복귀"를 전제한다 — Nit, 운영 자산이라 명시 요청이 있을 때 고친다.
- `claude --worktree` 로 시작한 세션에서 `ExitWorktree` 가 no-op 인지 모른다(no-op 이면 no-op 분기의 재시도·정리 생략이 적용된다) — Open.
- 공용 wiki `worktree-isolation-bash-guard` 에 2026-09-30 실측을 더한다(`bash "$HOME/…"` 거부 3/3, 펼친 절대경로 통과 3/3, `uv run python "$HOME/…"` 통과 2/2 — 이 repo 세션 실측이라 공개 출처) — `~/.claude` main 세션에서 `/wiki ingest`.
