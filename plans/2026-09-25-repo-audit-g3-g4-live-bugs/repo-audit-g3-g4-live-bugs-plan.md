---
title: repo-audit-g3-g4-live-bugs — statusline null 입력·bg 표시 제거·subagent 행 재작성, codex quota refresh 종료 처리
status: in_progress
started: 2026-09-25
updated: 2026-09-25
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

라이브 statusline 세 스크립트의 결함을 고친다: `null` 입력 크래시, 구분할 수 없는 bg 표시(제거), 현행 스키마와 맞지 않아 아무것도 그리지 않는 subagent 행, codex quota refresh 가 응답 없이 끝난 app-server 를 20초 기다리는 것과 캐시 쓰기 실패 시 helper 가 끝나지 않고 남는 것.

# Intent

- 링크: `plans/2026-09-25-repo-audit-followups/intent.md` 의 `repo-audit-g3-g4-live-bugs` 단위. 항목 원본은 `plans/2026-09-25-repo-audit-remaining/repo-audit-remaining-plan.md` `# Deferred` G3·G4.
- 규모: medium(파일 3개 + 테스트, 목적 2개).
- 분할: 없음 — G3(statusline)와 G4(refresh)는 각자 머지할 수 있지만(G3 는 spawn·lock 코드를 건드리지 않는다), 같은 감사에서 나온 작은 라이브 수정 두 건이라 한 PR 로 함께 리뷰·라이브 확인하고 되돌림은 커밋 단위로 한다(G1/G2 와 같은 선택, plan-reviewer 지적으로 근거 정정).
- 사용자 결정(2026-09-25): subagent 행은 현행 스키마로 다시 작성(대안: 설정·스크립트 제거 / null 방어만). bg 표시는 제거(대안: 서브에이전트 symlink 만 세기 / 경로만 고침) — 경로를 고치자 tasks 디렉토리의 foreground Bash 출력까지 세서 `refreshInterval: 2` 마다 오표시가 나는 것이 드러났다.
- Constraints: 라이브 경로라 보수적으로 — 모든 부분은 지금처럼 실패 시 그 조각만 빠지고 exit 0. 공식 문서가 정본(statusline·env-vars).
- Out of scope: git spawn 3→1(선택 항목, 아래 기각), fmtQuota·cache/lock 상수 중복(저우선), CI statusline 스모크(G9 — 이 단위의 `scripts/statusline.test.js` 가 `verify.sh node` 로 CI 에서 돈다).

재현(2026-09-25, macOS):
- G3.1 bg(제거로 처분): 코드가 보는 `$TMPDIR/claude/-Users-jongyoonlee-.claude/<sid>/tasks` 는 없고 실제는 `/private/tmp/claude-501/-Users-jongyoonlee--claude/<sid>/tasks`. 기준 디렉토리(✅ env-vars 문서: `CLAUDE_CODE_TMPDIR`, 기본 macOS `/tmp`·Linux/Windows `os.tmpdir()`, Unix 는 `/claude-{uid}/`·Windows 는 `/claude/` 를 붙임)와 slug(`.` 도 `-`) 둘 다 틀림. tasks 는 worktree 에 들어가도 시작 디렉토리 slug 에 남는다. (처음 적은 "`transcript_path` 상위 디렉토리와 같다" 는 틀렸다 — plan-reviewer 실측: EnterWorktree 뒤 transcript 와 `project_dir` 는 worktree slug 로 옮겨진다.)
- G3.2 ctime: 파일 생성 2초 뒤 append 하면 ctime 이 따라 움직인다(birth→ctime 2004ms) — 경과 시간이 "마지막 쓰기부터" 가 된다.
- G3.3 null: `echo null |` 두 스크립트 모두 TypeError exit 1.
- G3.4 subagent: ✅ statusline 문서 — 입력은 `{base hook fields, columns, tasks[]}`(task: `id, name, type, status, description, label, startTime, model, effort, contextWindowSize, tokenCount, tokenSamples, cwd`), 출력은 행마다 `{"id","content"}` JSON 한 줄. 현 스크립트는 최상위 `status`·`context_window`·`cost` 를 읽고 평문을 써서 매번 빈 출력.
- G4.2: 응답 없이 exit 0 하는 app-server → 20초 timeout 까지 대기 후 `timeout` negative cache.
- G4.1 EPIPE: 재현 안 됨(codex 부재 40회 0건, stdin 을 닫는 stub 도 첫 write 가 파이프 버퍼에 먼저 들어감). stdin `error` 미처리는 Node 에서 uncaught 가 되는 것이 문서화된 동작이라 핸들러만 더하고 "고침" 이 아니라 예방으로 보고한다.

# Acceptance

1. `null`·빈·깨진 JSON stdin 에서 `statusline.js`·`subagent-statusline.js` 모두 exit 0, bg 조각은 없다. 검증: `scripts/statusline.test.js`.
2. subagent 행: 문자열 id 를 가진 task 마다 `{"id","content"}` 한 줄, content 는 `name · description · status · <N>k tok (P%) · Xm Ys`(없는·공백뿐인 조각 생략, 제어문자는 공백, 비율 100% 상한, 경과는 `running`·`pending` 이고 `startTime`(epoch ms)이 유효할 때만), `columns` 를 넘으면 description 부터 글자(grapheme) 단위로 줄이며 한글·이모지는 2칸, `columns` 가 0 이면 출력하지 않는다. 검증: 테스트.
3. refresh: 모든 종료 경로가 한 곳에서 캐시를 쓰고 app-server 를 끝낸 뒤 종료한다 — 응답 후에도 살아 있는 app-server(`serve`)에서 5초 안에 exit 0·캐시 기록·stub 종료 / 답하자마자 끝나는 app-server(`answer`)의 응답도 기록 / 답 없이 exit 0(`silent`)·손자 프로세스가 파이프를 쥔 채 종료(`orphan`)는 5초 안에 `process-exit` negative cache / codex 가 PATH 에 없으면(`missing`) 5초 안에 `spawn-error` negative cache·lock 해제 / 캐시 경로에 쓸 수 없으면 5초 안에 exit 1·임시 파일 없음·lock 유지(backoff)·stub 종료. POSIX 는 셸 없이 spawn. 라이브: 이 머신의 codex 0.154.0 으로 exit 0·캐시 갱신·잔류 프로세스 0. 검증: `scripts/codex-quota-refresh.test.js`(옛 코드에서 `silent`·`orphan` 은 20초, 캐시 쓰기 실패는 30초 넘게 끝나지 않음을 확인).
4. README statusline·subagent·refresh 절과 설치 확인 절 갱신, intent 의 `(미착수)` 줄 치환.
5. 전체: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음), plan-lint 통과.
- [ ] [post-merge] 머지 직후 라이브 확인: Agent 를 하나 띄워 subagent 패널 행이 새 형식(`description · running · Nk tok (P%) · Xm Ys`, 이름을 붙인 agent 는 앞에 이름)으로 보이는지(사용자 관찰), 다음 stale 때 `~/.claude/cache/codex-quota.json` 의 `fetchedAt` 이 갱신되고 `pgrep -fl "codex-quota-refresh|codex app-server"` 에 남은 프로세스가 없는지.

# Progress

- 2026-09-25: 착수(`/wt`). 재현(위 `# Intent`)·공식 문서 확인. 사용자에게 subagent 행 방향 확인 → 현행 스키마로 재작성.
- 2026-09-25: bg 경로를 고쳐 이 세션 tasks 로 돌리자 foreground Bash 출력까지 세는 것이 드러남 → 사용자 결정으로 bg 표시 제거. plan-reviewer(+codex) CONDITIONAL — 강한 우려 4(worktree 뒤 slug 불일치[bg 제거로 해소]·캐시 쓰기 실패 시 helper 잔류·close 지연·한글 폭) 반영. TDD: 새 refresh 케이스는 옛 코드에서 20초/30초+ 로 실패, 구현 뒤 refresh 5·statusline 3 통과. 이 머신에 남은 refresh·app-server 프로세스 없음(`pgrep`).
- 2026-09-25: 단위 커밋 2개 → code-reviewer(+codex high): Critical/Major 없음, 분쟁 2(kill 이 셸에만·폭 표 불완전)·논의 1(이름 없는 agent 행) → fix loop 1. POSIX 셸 없이 spawn, grapheme 폭, 끝난 task 경과 생략, `columns:0`, 빈 조각, 테스트 flaky·임시 디렉토리 정리, `missing` 테스트 추가. 테스트 statusline 3·refresh 6 통과, 라이브 refresh 확인.
- 2026-09-25: 재확인 APPROVE(원 finding 10 해소·1 문서화). 새 Minor(`missing` 테스트 PATH 에 node 디렉토리 — npm 전역 codex 머신에서 진짜 codex 를 찾음)·Nit(stubPid null 허용) → fix loop 2. refresh 6 통과.

# Next

commit-check(fixup 합치기, 승인) → `/e merge` → post-merge 라이브 확인.

# Decisions

- ~~slug 는 `transcript_path` 상위 디렉토리 이름을 우선한다~~ → **bg 표시 제거로 무효** (사용자 결정. 참고로 이 규칙도 틀렸다 — worktree 진입 뒤 transcript·project_dir 는 옮겨지고 tasks 는 시작 slug 에 남는다; 대안이던 session id 로 `<root>/*/<sid>/tasks` 를 찾는 방식은 foreground Bash 구분 문제를 못 풀어 채택하지 않음). 원래 근거: 이유: Claude Code 가 긴 경로를 자르거나 해시를 붙이는 규칙을 재구현하지 않아도 되고, worktree 에 들어간 뒤에도 시작 디렉토리 기준이라는 점이 그대로 맞는다. 없을 때만 `workspace.project_dir` 를 치환한다(`cwd` 가 아님 — worktree 세션에서 틀린다).
- ~~기준 디렉토리는 env-vars 문서 규칙을 그대로 따른다~~ → bg 제거로 무효.
- subagent 행은 기본 표시의 `name · description` 을 유지하고 원래 스크립트가 보이던 상태·경과를 붙인다. 이유: 행이 여러 개라 이름이 없으면 구분이 안 되고, 기본 표시보다 정보가 줄면 커스텀 행을 둘 이유가 없다. `label` 은 문서에 의미가 없어 쓰지 않는다. 폭은 표시 칸 기준(한글·CJK·이모지 2칸, 코드 포인트 단위로 자름), id 는 문자열만(host 가 스키마가 틀린 줄을 버린다 — plan-reviewer 바이너리 확인), `startTime` 은 epoch ms 만(처음 넣은 초·문자열 추정은 근거 없어 뺌).
- refresh 의 종료 판정을 `exit` → `close` + `exit` 뒤 1초 drain 으로 바꾼다(처음엔 `close` 만 — plan-reviewer: 손자 프로세스가 파이프를 쥐면 `close` 가 20초까지 늦어 기존의 즉시 처리(code≠0)가 회귀한다). 이유: `if (code === 0) return` 은 종료 직후 stdout 에 남은 응답을 놓치지 않으려는 장치로 보이는데(⚠️ 추정), 그 목적은 모든 stdio 가 닫힌 뒤 오는 `close` 로 달성되고 응답이 없을 때 20초를 기다리지 않는다.
- 모든 종료 경로를 `finish()` 하나로 모은다(이유: 성공 경로에서 캐시 쓰기가 실패하면 `settled` 뒤 catch 가 `return` 해 kill·exit 없이 helper 와 app-server 가 남았다 — 옛 코드에서 30초+ 재현). lock 은 캐시를 쓴 경우에만 지운다(이유: 못 쓰면 statusline 이 2초마다 재spawn — 남긴 lock 이 25초 inflight 창으로 backoff).
- 기각: git spawn 3→1(`rev-parse` 한 번에 여러 값) — 선택 항목이고 라이브 경로라 보수적으로, 측정된 지연 문제도 없다.
- 커밋 단위: 1) `fix(statusline): survive a null payload, drop the bg indicator, render subagent rows` — `statusline.js`·`subagent-statusline.js`·`scripts/statusline.test.js`·README statusline 부분 2) `fix(codex-quota): settle as soon as app-server exits and never linger` — `codex-quota-refresh.js`·`scripts/codex-quota-refresh.test.js`·README refresh 부분·intent·이 plan(제목은 bg 제거·리뷰 반영 뒤 실제 커밋에 맞춤). README 는 두 단위가 함께 고치므로 단위 1 에는 statusline 부분만 담고, 리뷰 뒤 README 수정은 단위 2 쪽 fixup 으로 보낸다(3-way 충돌 회피 — 귀속 예외).
- subagent 행의 이름: 입력 `name` 은 이름을 등록한 agent 에만 오고 기본 표시가 대신 쓰는 agent 종류는 입력에 없다(code-reviewer 바이너리 확인). 이름 없는 행은 `description · status · …` 로 두고 README·post-merge 기대값을 맞춘다(이유: 사용자가 승인한 미리보기가 이 형태였고, 행마다 description 이 있어 구분된다). 기각: 이름 없으면 기본 표시에 맡김 — 상태·경과를 잃는다.
- POSIX 는 셸 없이 spawn(이유: Ubuntu dash 는 `sh -c` 를 exec 하지 않아 kill 이 셸에만 간다 — code-reviewer). Windows 는 `.cmd` shim 때문에 셸 + 한 문자열(DEP0190 회피, 미검증).

# Key Files

- `statusline.js` — null 입력 방어, bg 표시 제거
- `subagent-statusline.js` — 현행 스키마 재작성
- `codex-quota-refresh.js` — `finish()` 통합·close+drain·lock backoff·임시 파일·POSIX 셸 없는 spawn
- `scripts/statusline.test.js`, `scripts/codex-quota-refresh.test.js` — 신규 테스트
- `README.md` — statusline·subagent·refresh 절, 설치 확인 절
- `plans/2026-09-25-repo-audit-followups/intent.md` — `# Plans` 자기 줄

# Review Disposition

- [plan] 강 1 worktree 뒤 bg slug 불일치 — resolved(사용자 결정 bg 제거; plan 의 틀린 실측 문구 정정). 강 2 캐시 쓰기 실패 시 helper 잔류·재spawn 주기 — fix(`finish()`, lock backoff, `serve` stub 테스트). 강 3(분쟁: Codex 강 / Claude 약) close 지연 — fix(exit 뒤 1초 drain, `orphan` 테스트). 강 4 한글 폭 — fix(표시 폭·코드 포인트 절단, 한글 테스트).
- [plan] 약: 문자열 id — fix. startTime 추정 — fix(ms 만, 무효 생략). P% 100% 초과 — fix(상한, README 근사치). 제어문자 — fix. birthtime 조용한 skip — 해당 없음(bg 제거). Windows 경로 — 해당 없음(bg 제거). 분할 근거 — fix. 기각 대안 기록 — fix. rollback·가장 위험한 단계 — fix(post-merge 라이브 확인, `pgrep` 점검, 아래 rollback). 수동 확인 가짜 통과 — 해당 없음(bg 제거). 테스트의 가짜 HOME spawn — fix(신선한 가짜 캐시).
- [plan] 누락: lock 소유권 없는 삭제·비원자적 생성 — defer(`# Deferred`). DEP0190 — fix(POSIX 셸 제거·Windows 한 문자열). 조용한 bg 명령 — 해당 없음(bg 제거).
- [code] 재확인 Minor `missing` 테스트 PATH — fix(stub 디렉토리만). Nit stubPid null 허용으로 단언 약화 — fix(`missing` 외 모드는 pid 필수).
- [code] 논의 이름 없는 agent 행 — wontfix + 문서화(Decisions). 분쟁(codex Major / Claude Minor) kill 이 셸에만 — fix(POSIX 셸 없이). 분쟁 폭 표 불완전 — fix(grapheme·Emoji_Presentation·결합 문자 0칸, ✅ 테스트). 경과 테스트 flaky — fix(허용 범위). 끝난 task 경과 증가 — fix(running·pending 만). plan 문구 drift — fix. `columns:0` — fix. 빈 조각 — fix. README 25초 근사 — fix(문구). 쓸모없는 재시도 분기 — fix(제거). 임시 디렉토리 미정리 — fix.

# Deferred

- (low) `codex-quota-refresh.js` — lock 을 소유권 확인 없이 지우고 `statusline.js` 는 lock 을 비원자적으로 만든다(`writeFileSync`). 두 statusline 이 동시에 stale 을 보면 refresh 가 둘 뜰 수 있다.

# Rollback

- 되돌림은 커밋 단위 `git revert` 후 main push — 다른 머신은 다음 SessionStart 자동 pull 로 따라온다. 캐시 형식은 그대로라 이전 버전과 호환된다.
- refresh 결함으로 이미 남은 프로세스는 revert 로 정리되지 않는다: `pgrep -fl "codex-quota-refresh|codex app-server"` 로 확인하고 PID 로 종료한다. 2026-09-25 착수 시점 이 머신에는 없었다.

# Blockers

없음.
