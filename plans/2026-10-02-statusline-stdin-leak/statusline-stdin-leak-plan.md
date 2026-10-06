---
title: statusline-stdin-leak — 상태줄 스크립트가 닫히지 않는 stdin 을 기다리며 고아로 남지 않게
status: done
started: 2026-10-02
updated: 2026-10-06
---

# Goal
`statusline.js`(와 같은 구조의 `subagent-statusline.js`)가 stdin 이 끝나지 않아도 스스로 끝나게 해, 하니스가 셸만 끝낸 뒤 node 상태줄 프로세스가 영영 남아 그 순간의 cwd(worktree)를 잡는 누수를 막는다. 이미 떠 있는 고아는 사용자에게 보고하고 처리를 묻는다(사용자 지시 2026-10-02).

# Intent
- 출처: 공용 wiki `workflow-failures`(상태줄 고아 행 — "statusline.js 에 stdin 읽기 시한" 제안), `windows-bash-tool-orphan-processes`(2026-10-01 관찰). 묶음: 없음 — 열린 두 묶음(repo-context-kit·repo-audit-followups)의 요구가 아니다.
- Problem — 2026-10-02 실측(Windows 11·Node 22.19.0):
  - 이 머신에 `node …/statusline.js` 고아 13개가 떠 있다(9/30 생성 8, 10/02 생성 5). 모두 부모(중간 셸)가 죽었고, 현재 디렉터리는 이 세션이 아닌 다른 repo 세션의 repo·worktree 다. `subagent-statusline.js` 고아는 없다.
  - 코드상 두 스크립트는 `process.stdin.on('end', …)` 안에서만 일하고 끝난다(`statusline.js:31-33`, `subagent-statusline.js:73-75`). 'end' 전에는 이벤트 루프에 stdin 하나만 남는다(git 호출은 'end' 뒤의 동기 호출이고 각자 2초 timeout). 그래서 stdin 의 쓰기 끝이 열린 채 남으면 프로세스가 끝나지 않는다.
  - 3 Whys:
    1. 상태줄 프로세스가 끝나지 않는다 — stdin 'end' 가 오지 않는다(위 코드).
    2. 'end' 가 오지 않는다 — 하니스가 중간 셸만 끝내고 stdin 쓰기 끝을 닫지 않은 것으로 보인다(⚠️ 추정 — 하니스 내부는 볼 수 없다. 정황: 고아 전부 부모가 죽었고, 오늘 5개는 이 머신이 부하 재현으로 무거웠던 시각에 생겼다 — 상태줄 호출이 느려지자 하니스가 포기한 것으로 보인다).
    3. 그것이 영구 누수가 된다 — 두 스크립트에 stdin 대기 시한이 없다(같은 repo 의 `scripts/hook-cwd.js`·wiki Stop hook 은 시한을 둔다).
- Constraints:
  - 정상 경로 불변 — stdin 이 닫히면 지금과 같은 출력·exit 0 이고, 그 뒤에 시한 때문에 늦게 끝나지 않는다.
  - 시한 경로는 exit 0·출력 없음 — 하니스가 이미 포기한 호출이라 그릴 대상이 없다.
  - `refreshInterval: 2` 라 2초마다 새로 뜬다(공용 wiki `claude-code-statusline-input`) — 외부 프로세스·무거운 작업을 더하지 않는다.
  - 공개 repo — 고아가 잡은 다른 repo 의 이름·경로를 plan·커밋·PR 에 적지 않는다(CLAUDE.md §11).
- Out of scope:
  - 하니스 쪽 원인(셸만 끝내고 stdin 을 닫지 않음) — 이 repo 밖이다.
  - stdin 'error' 처리 — 관찰된 적이 없다(Windows 의 끊긴 pipe 는 'end' 로 온다).
  - 이미 떠 있는 고아의 종료 — 다른 세션의 프로세스라 소유 판정이 안 된다. 사용자 결정으로 처리한다(아래 # Next).
- 분할: 없음 — 두 스크립트의 같은 시한(각 5줄 안팎)과 그 테스트는 한 목적이다. 나누면 같은 테스트 파일을 두 번 고치고 리뷰·검증 고정비만 두 배가 된다.
- 규모: small(두 스크립트에 같은 시한 + 테스트 + README, 50줄 미만, 한 모듈). dlc 규모표대로 plan-review 는 두지 않고 code-review 로 덮는다. 다중 파일이라 계획은 사용자 승인을 받는다(CLAUDE.md §3-3).

# Progress
- 2026-10-02: 착수. 고아 13개 확인(부모 사망·다른 repo 세션의 cwd), 코드 경로 확인, plan 초안. 승인 질문은 사용자가 거절하고 `/e` 로 마무리(2026-10-06) — 코드 변경 없음, plan 만 WIP 커밋.
- 2026-10-06: 사용자 승인(다른 repo 세션의 SessionStart "머지 대기" 알림이 계기) — 계획 그대로, `subagent-statusline.js` 포함, 기존 고아는 목록 보고 후 종료(살아 있는 세션 것 제외). 브랜치를 main(bb81ed1) 위로 rebase. Red(두 스크립트 15초 상한 SIGTERM) → 구현 → Green(7 tests). 정상 경로 관찰: JSON·빈 stdin 은 base 와 같이 약 40ms(간헐 수백 ms 는 base 에도 있음), 열린 stdin 은 약 3040ms 에 exit 0·출력 없음. README 두 항목 갱신. 기존 고아: `node statusline.js` 13개(9/30 생성 8·10/2 생성 5, 전부 부모 사망, 생성 4~6일 경과 — plan 착수 때 목록과 같다)를 종료 직전 재확인(이름·명령줄·생성일·부모 사망) 뒤 종료, 남은 상태줄 프로세스 0. 이 세션의 정상 호출(생성 0분·부모 생존) 1개는 제외했다(종료 시점에 이미 끝남).
- 2026-10-06: code-reviewer(+codex) APPROVE → 처분(# Review Disposition) 반영, simplify 변경 없음. `bash scripts/verify.sh` 단독(격리 runner): exit 0, `ALL PASS (skip: install-hooks.test.js(case) record-verified.test.sh)` — skip 은 git `--path-format` 미지원 ps1 케이스·jq 미설치로 이 변경 경로가 아님, statusline 3파일 ok. evidence gate: Acceptance 1~7 충족 → DONE.

# Next
- 없음 — main 에 로컬 ff-merge 로 반영(push 는 요청 시). 하니스가 statusLine 의 빈 stdout(exit 0)을 어떻게 그리는지는 미확인(리뷰 open question — 시한 경로는 하니스가 이미 포기한 호출이라 영향 없다고 본다 ⚠️).

# Decisions
- wiki decision 조회(`statusline stdin 고아 누수`): `workflow-failures` 상태줄 고아 행의 제안(stdin 읽기 시한) — 따른다. `claude-code-statusline-input`(2초마다 새로 뜬다, null·깨진 입력에도 exit 0) — 따른다.
- 설계: 두 스크립트의 stdin 리스너 등록 바로 앞(함수 정의 뒤 — 정의는 즉시 끝나 차이 없음)에 `const STDIN_MS = 3000;` 과 `setTimeout(() => process.exit(0), STDIN_MS)` 타이머, 'end' 처리기 첫 줄에서 `clearTimeout`. 3초 — 정상 호출에서 stdin 은 시작 직후 닫히고(수 ms), 하니스가 포기한 호출이 cwd 를 잡는 시간을 짧게 둔다. wiki Stop hook stdin 의 3초와 같은 값.
- 기각:
  - 시한이 되면 받은 데까지로 그리기 — 하니스가 포기한 호출이라 읽는 쪽이 없고, 닫힌 stdout 에 쓰면 EPIPE 로 죽을 수 있다.
  - `unref()` 한 타이머로 clearTimeout 생략 — 'end' 뒤의 느린 git 호출과 비동기 stdout flush 사이에 타이머가 발화하면 출력을 자를 수 있다.
  - 두 스크립트가 쓰는 공용 모듈 — 5줄을 위해 루트의 두 진입점에 require 경로를 더한다.
  - 주기적으로 고아를 찾아 죽이는 감시 — 다른 세션 프로세스를 소유 판정 없이 죽이게 된다.
- ⚠️ 사용자가 지목한 것은 `statusline.js` 다 — 같은 대기 구조인 `subagent-statusline.js` 를 함께 고친다(고아는 아직 없지만 같은 하니스 경로에서 같은 누수가 난다) — 승인 질문에 범위로 묻는다.
- 커밋 단위: 1개 — 한 목적.

# Key Files
- `statusline.js` — stdin 대기 시한
- `subagent-statusline.js` — 같은 시한
- `scripts/statusline.test.js` — 닫히지 않는 stdin·닫힌 stdin 경과 테스트(비동기 꼬리)
- `README.md` — `### statusline.js`·`### subagent-statusline.js` 항목

# Blockers

# Review Disposition
- code-reviewer(+codex high): APPROVE, blocker 없음.
  - fix — 테스트가 출력을 'exit' 에서 확정 → 'close' 에서 확정(종료 직전 쓴 출력을 놓치지 않게).
  - fix — `clearTimeout` 회귀 무가드 → 닫힌 stdin(`{}`)이 3초 전에 끝나는지 단언 추가(cwd 를 git repo 가 아닌 임시 HOME 으로 두어 git 시간 배제). mutation 확인: `clearTimeout` 을 빼면 `ms=3051` 로 실패.
  - fix — 경과를 `Date.now` 로 잼 → `performance.now()`.
  - fix — README 가 추정 원인을 실측처럼 서술 → 관찰과 추정을 나눔. `< /dev/null` 예시(PowerShell 불가) → `echo {} | node statusline.js`.
  - fix — plan Key Files 행 번호·"맨 앞" 서술 낡음.
  - accepted-risk — EOF 와 3초 타이머가 같은 루프 반복에서 함께 준비될 때의 순서(PLAUSIBLE, 재현 못 함): 리스너 등록뿐인 구간이라 확률이 매우 낮고, 결과는 그 회차 상태줄이 비는 것뿐(2초 뒤 다음 회차).
  - wontfix — 비동기 단언 실패 시 임시 HOME 잔존: 기존 동기 테스트 실패 시와 같은 동작.
- simplify 체크: 변경 없음 — 스크립트당 4줄·테스트 헬퍼 1개로 줄일 중복·죽은 분기가 없다.

# Acceptance
1. Red — base 에서 새 테스트가 실패한다: stdin 을 열어 둔 채 띄운 두 스크립트가 상한(15초) 안에 끝나지 않는다. 검증: `node scripts/statusline.test.js`. 통과 기준: 그 테스트에서 실패.
2. Green — stdin 을 열어 둔 두 스크립트가 스스로 끝난다: exit 0·출력 없음·경과 3초 이상(시한)·상한 15초 미만. 검증: 같은 명령. 통과: 전부 통과.
3. 정상 경로 불변 — 기존 statusline 테스트 전부 통과(입력 → 같은 출력), 그리고 입력을 준 실행이 시한 때문에 늦어지지 않는다(조용한 상태에서 경과 관찰 — 수백 ms). 검증: 같은 명령 + 경과 관찰 1회.
4. 실제 실행 관찰 — `node statusline.js` 를 닫히지 않는 stdin 으로 띄우면 약 3초 뒤 끝나고, 빈 stdin 이나 JSON 입력이면 바로 끝난다. 검증: scratch 실행. 통과: 관찰값.
5. 전체 검증 — `bash scripts/verify.sh` 단독. 통과: `ALL PASS`(skip 이 붙으면 이 변경 경로가 아님을 확인).
6. 문서 동기화 — README 두 항목에 stdin 시한과 이유. 검증: diff 검토.
7. 기존 고아 — 목록(PID·생성 시각·부모 사망·다른 repo 세션의 cwd)을 사용자에게 보고하고 결정대로 처리. 통과: 보고·처리 결과 기록.

# Deferred
