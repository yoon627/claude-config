---
title: e-worklog-gate — /e 6단계 worklog 가 실패하면 7단계 자동 정리를 생략하고, collect-state 경로 표기를 적는다
status: done
started: 2026-09-30
updated: 2026-09-30
---

# Goal
`/e` 6단계 worklog 가 실패로 끝났을 때 7단계가 worktree 를 지워 그 시간을 영영 등록할 수 없게 되는 일을 막는다. 2·7단계의 collect-state 호출이 어느 위치에서 어떤 경로 형태로 가능한지 적는다. 문서만 바꾸고 스크립트는 그대로 둔다.

# Acceptance
1. **정리 게이트**: 6단계 비차단 bullet 이 실패 조건(비0 종료 사유 불문, 재시도 뒤 헬퍼 거부, `--register` 의 "등록 불가" 경고)과 정상 skip(세션·티켓·토큰 파일 없음, 스킬 없음)을 가르고, 7단계 서두·"하나라도 불충족" bullet·실행 전제·원격 bullet·경계 절·lifecycle 범위·§B 결과 처리·README 가 같은 게이트를 가리킨다 — `rg -n "worklog 실패|worklog 가 실패" skills/e/SKILL.md docs/worktree-lifecycle.md README.md` 대조.
2. **종료코드 주장**: 문서의 종료코드(세션·티켓·토큰 없음 0, 등록 차단·Jira 오류 1, 설정·git 오류 2, 실행기 없음 127, 부분 자격증명 0 + 경고)가 `skills/jira-worklog/jira_worklog.py`·`run_worklog.sh` 와 맞다 — 코드 리뷰 대조.
3. **경로 표기**: 2단계가 상대경로의 해석 조건과 다른 repo·격리 세션의 형태를 적고, 7단계·lifecycle §A·"6 전" no-op 분기가 그것을 가리킨다.
4. `bash scripts/verify.sh` 마지막 줄이 main 과 같은 skip 만 둔 `ALL PASS`, `bash skills/improve/improve.sh --ci` exit 0.

# Progress
- 2026-09-30: `/wt` 로 worktree 생성(base `main@b881777`). e-isolated-helper-order plan # Deferred 의 두 항목(6단계 실패와 무관한 7단계 삭제, collect-state 경로 두 형태)을 사용자 "남은거 이어서" 요청으로 착수했다.
  - `jira_worklog.py` 의 반환 경로를 읽어 종료코드를 확인했다(세션 없음·티켓 없음 0, 등록 차단·Jira 오류는 실패 수, main 은 1/2).
  - 격리 runner: `verify.sh` `ALL PASS (skip: install-codex-skill.test.ps1)`, `improve --ci` exit 0.
- 2026-09-30: 코드 리뷰 APPROVE — Critical/Major 0·Minor 5·Nit 7(Codex 미가용). 처분은 # Review Disposition. 게이트를 7단계 서두·경계 절·lifecycle §B 까지 올리고, 원격 질문 시점·남긴 worktree 의 다음 명령·부분 자격증명을 적었다.
  - 반영 뒤 `verify.sh` 재실행 `ALL PASS (skip: install-codex-skill.test.ps1)`, plan-lint 0. `rg` 로 게이트가 SKILL·lifecycle·README 모든 요약에 들어간 것을 확인했다. evidence gate 1~4 충족 → 판정 DONE(status 는 머지 때 done).
- 2026-09-30: 커밋 1개. small 이라 로컬 ff-merge(§8)로 반영하고 새 순서대로 정리한다. 남은 것은 # Deferred.

# Next

# Decisions
- 게이트는 6조건 번호 목록에 넣지 않고 7단계의 선행 조건으로 둔다. "6조건" 을 가리키는 다른 문서(CLAUDE.md §8(a)·dlc)의 수를 바꾸지 않으려는 선택이다. 대신 7단계 서두·실행·경계 절·lifecycle 이 모두 선행 조건을 적는다(리뷰 M1).
- 원격 브랜치 질문은 로컬 정리 뒤라는 순서를 지킨다. 로컬 정리를 생략했으면 질문도 미루고 보고에 1줄 남긴다(리뷰 M2).
- "6 전" no-op 분기는 처음부터 `$HOME` 을 펼친 절대경로로 부른다 — 이전 plan(e-isolated-helper-order)의 "형태 바꾸기는 재시도로만"을 이 분기에서는 대체한다. 이유: 2단계 경로 표기와 통일하고, 실측상 펼친 경로가 통과한다(리뷰 N4). 복귀 흐름(worktree 밖)은 그대로 `$HOME` 형태다.
- 커밋 단위: 1개 — 두 항목이 모두 `/e` 6·7단계 헬퍼 호출의 안전성이고 같은 문서 줄을 고친다.

# Key Files
- `skills/e/SKILL.md` — 2단계 경로 표기, M6 뒤 원격 bullet, "6 전" no-op, 6단계 서두·비차단·보고, 7단계 서두·재수집·원격 bullet, 경계 절
- `docs/worktree-lifecycle.md` — 범위, §A, §B 결과 처리
- `README.md` — `/e` 정리 bullet, jira-worklog 절(6단계)
- `plans/2026-09-30-e-isolated-helper-order/e-isolated-helper-order-plan.md` — # Deferred 해소 표시

# Blockers
없음

# Review Disposition
코드 리뷰 — code-reviewer APPROVE, Critical 0·Major 0·Minor 5·Nit 7. Codex 미가용(workspace out of credits).
- M1 게이트가 번호 목록 밖이라 다른 요약이 "6조건 충족 → 무확인 삭제" 로 남음 — fix: 7단계 서두·실행 전제·경계 절·lifecycle 범위·§B 결과 처리에 적었다.
- M2 로컬 정리를 생략했을 때 원격 질문 시점이 세 곳에서 다름 — fix: 로컬 정리 뒤로 통일하고, 생략했으면 미루고 1줄 보고.
- M3 남긴 worktree 를 끝낼 안내가 없음 — fix: 6단계 보고에 사유와 다음 명령(`--allow-large-change` 재등록 → `/wt <이름>` 에서 `/e`, 포기하면 `/wt rm`)을 적었다.
- M4 부분 자격증명은 exit 0 이라 게이트를 통과함 — fix: `--register` 의 "등록 불가" 경고를 실패로 본다고 적었다.
- M5 `jira_worklog.py` 종료코드 계약을 고정하는 테스트가 없음 — defer(# Deferred): 이 브랜치는 코드를 바꾸지 않고 기존 동작을 문서화한다.
- N1 종료코드 괄호가 전체 목록처럼 읽힘 — fix: "사유 불문 — 예:" 로 바꾸고 127 을 더했다. N2 "헬퍼 거부" 와 재시도 — fix: "2단계 경로 표기로 다시 불러도". N3 상대경로 해석 조건 — fix: "cwd 가 `~/.claude`(또는 그 worktree) 루트일 때". N4 경로 첫 시도 형태 — fix(# Decisions). N5 README 괄호 — fix. N6 해소 표기가 지워질 브랜치를 가리킴 — fix: 이 plan 경로로 바꿨다. N7 이름 누락 시 main 이 대상 — fix: 보고 전에 출력 머리줄 `[<이름>]` 확인.
- 범위 밖: README "`/e` 5단계" → 6단계 — fix(같은 문서 영역, 1단어). jira-worklog SKILL·CLAUDE.md 의 "`--all` 순회 대상에서 빠져" 기전 서술, `wt rm` 의 미등록 시간 경고 없음 — defer(# Deferred). SKILL 6단계 서두의 같은 서술은 이 브랜치에서 고쳤다.

# Deferred
- `jira_worklog.py` 의 종료코드 계약(세션·티켓·토큰 없음 0, 게이트·Jira 실패 비0, 부분 자격증명 0 + 경고)을 고정하는 테스트가 없다. `/e` 7단계 게이트가 이 계약에 기댄다 — Minor, `skills/jira-worklog/`.
- `skills/jira-worklog/SKILL.md` 와 `CLAUDE.md` §8 worklog 줄의 "지우면 `--all` 순회 대상에서 빠져 등록 불가" 는 결론은 맞지만 기전이 다르다(이름 선택이 살아 있는 worktree 만 본다) — Nit, CLAUDE.md 는 운영 자산이라 명시 요청 시.
- `/wt rm` 은 worklog 를 돌리지도, 미등록 시간을 경고하지도 않는다. 게이트로 남긴 worktree 를 이 경로로 지우면 시간이 조용히 버려진다 — Minor, `skills/wt/SKILL.md` rm.
- Windows 에서 `run_worklog.ps1` 의 비0 종료가 도구 결과에 비0 으로 보이는지 모른다 — Open(검증 못 하는 플랫폼).
