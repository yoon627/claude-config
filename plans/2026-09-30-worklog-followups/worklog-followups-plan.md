---
title: worklog-followups — jira_worklog 종료코드 계약 테스트, 삭제 worktree 등록 불가 기전 문구 정정, /wt rm 의 worklog 경고
status: in_progress
started: 2026-09-30
updated: 2026-10-01
intent: plans/2026-09-30-worklog-deletion-safety/intent.md
---

# Goal
`e-worklog-gate` 의 # Deferred 3건을 처리한다(사용자 승인 2026-09-30).
1. `/e` 7단계 정리 게이트가 기대는 `jira_worklog` 종료코드 계약을 테스트로 고정한다.
2. "삭제되면 `--all` 순회 대상에서 빠진다"는 문구를 실제 기전으로 바로잡는다.
3. `/wt rm` 이 지우기 전에 등록하지 않은 worklog 시간을 알린다.

# Intent
- 묶음: `plans/2026-09-30-worklog-deletion-safety/intent.md`(§10 트리거 3 — 선행 plan `e-worklog-gate` 의 # Deferred 에서 착수해 소급 생성).
- 델타 — Problem: `/e` 6단계 게이트는 "비0 이면 정리 생략, 0 이어도 `--register` 뒤 '등록 불가' 경고면 생략"에 기대는데, 그 종료코드를 고정하는 테스트가 없다. jira-worklog SKILL·CLAUDE.md §8 은 등록 불가의 이유를 `--all` 순회로 적었지만 `--all` 은 원래 등록하지 않는다. `/wt rm` 은 worklog 를 보지 않아 등록하지 않은 시간을 조용히 버린다.
- 델타 — Constraints: CLAUDE.md §8 수정은 사용자 승인(2026-09-30). 상시 주입 문서라 줄을 늘리지 않는다(#223 — 수정 전 138행 281자). 테스트는 실제 홈(`~/.claude/logs`·`~/.claude/projects`·`~/.jira-kit`)·Jira·git 에 닿지 않는다.
- 델타 — Out of scope: 델타 없음 — 묶음 intent 의 Out of scope 와 같다.
- 분할: 없음 — 단위 후보 3개(계약 테스트·기전 문구·`/wt rm` 경고)는 서로 결합이 없어 머지 무모순 기준으로는 나뉜다. 사용자가 세 건을 한 요청으로 승인했고, 파일 경계가 겹치지 않는 단위 커밋 3개라 단위별 revert 가 남으며, plan 3개의 고정비(worktree·리뷰·머지)가 이득보다 커서 한 plan 으로 둔다.

# Acceptance
1. **종료코드 계약**(`skills/jira-worklog/test_exit_contract.py`):
   - in-process `main()` — 0: 세션 활동 없음(미리보기·`--register`), 미리보기(활동·티켓 있음 — 이름으로·이름 없이 cwd 로), 티켓 없음 + `--register`, 자격증명 불완전 + `--register`(stderr "등록 불가"), 등록 성공. 1: 등록 게이트 차단, Jira 조회·등록 계획 실패, 쓰기가 이틀 중 하루만 실패, worktree 처리 중 git 오류. 2: 설정 오류, worktree 목록 git 오류. 고를 수 없는 worktree(없는 이름, 이름 없이 최상위가 아닌 cwd)는 `SystemExit` 문자열(종료코드 1). 예상 밖 예외는 0 으로 삼켜지지 않고 올라온다. fixture 는 디렉터리 이름과 branch 를 다르게 둬 디렉터리 이름으로 고르는지까지 고정한다.
   - 사례마다 실제로 지난 경로를 단언한다 — 활동이 있으면 stdout 머리줄 `[<이름>] branch=…`, 등록 성공은 `upsert_worklog` 호출 수 = 항목 수, 등록 불가는 stderr "등록 불가" + `get_myself` 미호출, 게이트 차단은 stderr "등록 차단" + `upsert_worklog` 미호출, 성공·정상 skip 경로에는 "등록 불가" 가 없다.
   - 경계 격리 — `load_config`·git 목록·세션 스캔·Jira·복구 로그를 모두 patch 한다. 빠뜨린 경계가 실제 자원에 닿지 않게 `HOME`·`USERPROFILE` 을 빈 임시 디렉터리로 바꾸고 `urllib.request.urlopen` 을 AssertionError 로 바꾼다. bucket 키는 넘겨받은 `index.classify(<worktree 경로>)` 로 만든다.
   - subprocess 1건 — 임시 cwd 의 깨진 `jira-kit.toml`(상위 `.env` 탐색은 빈 `.env` 로 멈춤), `HOME`·`USERPROFILE` 임시화, `JIRA_*` 제거로 `[sys.executable, jira_worklog.py]` 가 **프로세스 종료코드** 2 와 `jira-kit.toml` 원인을 낸다(`sys.exit(main())` 고리 고정).
   - 목록이 `skills/e/SKILL.md` 6단계 비차단 bullet 의 실패·정상 skip 구분과 같다(대조). 헬퍼 거부·토큰 파일 유무 판단은 `/e` 쪽이라 이 테스트가 닿지 않는다.
   - 변이(scratch 복사본에서, 추적 파일은 불변): 위험한 방향(실패 → 0) — 게이트 차단·Jira 조회 실패·등록 계획 실패 반환 0, 일부 쓰기 실패를 성공으로, 고를 수 없는 worktree 의 `sys.exit` → `return []`(없는 이름·최상위 아님), `sys.exit(main())` → `main()`, 실패 미집계, 예상 밖 예외 삼킴, "등록 불가" 경고 삭제 — 와 값 고정 — 미리보기·티켓 없음·세션 활동 없음 → 1, `ConfigError`·바깥 git 오류 → 1, 이름을 branch 로만 선택 — 이 모두 관련 사례에서만 실패한다. 커밋 전 `git diff --quiet -- skills/jira-worklog/jira_worklog.py`.
2. **launcher**(`skills/jira-worklog/test_launcher.sh`): bash 는 절대경로로 부르고 PATH 는 전용 디렉터리 하나(`dirname` 만 링크)로 둔다. 실행기가 없으면 `run_worklog.sh` 가 127 로 끝나고 stderr 에 "실행기 없음" 이 있으며 "command not found" 는 없다. 가짜 python3 가 3 으로 끝나면 launcher 도 3 으로 끝난다(`exec` 전달).
3. **문구**: `skills/jira-worklog/SKILL.md`·`CLAUDE.md` §8 에서 "`--all` 순회 대상" 문구가 사라지고, 새 문구가 코드와 맞다 — 이름·cwd 선택은 살아 있는 worktree 에서만 된다(`select_worktrees`), `--all` 은 등록하지 않는다(`register = args.register and not args.all`), 지운 worktree 의 시간은 삭제 worktree 로 표시만 된다. "영구히·다시는" 같은 단정은 쓰지 않는다. `rg "순회 대상" CLAUDE.md skills/` 0건. CLAUDE.md 138행은 281자를 넘지 않는다(수정 후 길이를 # Progress 에).
4. **`/wt rm` 경고**: `skills/wt/SKILL.md` rm 4단계 끝에 worklog 미리보기 bullet — 거부 검사를 모두 통과한 뒤, 스킬 디렉터리가 있으면(`/e` 6단계 미리보기와 같다), 2단계에서 확정한 대상의 디렉터리 이름으로 부르고, 머리줄이 `[<대상 이름>]` 인 블록만 읽는다. 경고는 미리보기 명령에 `--register` 를 붙이라고 안내하고(POSIX·Windows 공통), 등록 차단이면 `--allow-large-change` 를 알려 준다. 티켓·합계가 있으면 5단계 본문에 경고를 적고, 티켓 없음·세션 활동 없음이면 적지 않는다. 대상 머리줄도 "세션 활동 없음" 줄도 없으면(비0 포함) 미리보기 실패로 본문에 적는다. 등록은 대신 하지 않는다. 5단계 본문 경고 목록에 들어 있다. README `/wt` 절에 한 구절, README 파일 트리에 새 테스트 줄(단위 1). 살아 있는 worktree 에 미리보기를 실제로 돌려 머리줄에서 티켓·합계를 읽을 수 있음을 확인한다.
5. 격리 runner(cwd 는 이 worktree 의 절대경로 `~/.claude/.claude/worktrees/worklog-followups`): `bash scripts/verify.sh` 마지막 줄이 main 과 같은 skip 만 둔 `ALL PASS`(`ALL PASS (skip: install-codex-skill.test.ps1)`), `bash skills/improve/improve.sh --ci` exit 0.

# Progress
- 2026-09-30: `/wt` 로 worktree 생성(base `origin/main@0ffa979`). Explore — `jira_worklog.main()` 은 `ConfigError`·바깥 `GitError` 에 2, `process()` 실패 합이 있으면 1, 나머지 0. 없는 이름·cwd 가 worktree 최상위가 아니면 `sys.exit(str)`(1). 자격증명 3개 중 하나라도 없으면 `config.jira` 가 None 이고 `--register` 면 "등록 불가" 경고 뒤 0. `jira-kit.toml` 문법 오류는 `ConfigError`. launcher 는 실행기가 없으면 127. 묶음 intent 를 소급 생성했다.
- 2026-10-01: plan 리뷰 CONDITIONAL(강 4·약 9, Codex 미가용) → 반영(# Review Disposition). 리뷰어 실측: uv 0.9.27 이 종료코드를 그대로 넘긴다(int 2 → 2, str → 1). 범위 밖 발견: jira-worklog 스킬 8개 파일 51줄에 비공개 목록 용어(# Deferred).
- 2026-10-01: 단위 1 — `test_exit_contract.py` 12개가 현재 코드에서 통과, launcher 127·종료코드 전달(3) 통과, shellcheck clean. scratch 복사본 변이 15종(`jira_worklog.py` 13·launcher 2) 모두 KILLED — 각각 해당 사례에서만 실패. 추적 소스 diff 0. README 트리에 테스트 2줄(`test_launcher.sh` 는 원래 빠져 있었다).
  - 단위 2 — 문구 정정. CLAUDE.md 138행 281 → 275자, "순회 대상" 0건.
  - 단위 3 — `/wt rm` 4단계 bullet·5단계 본문·README. 실제 미리보기 머리줄 확인: `[worklog-followups] branch=worklog-followups ticket=(없음) 세션 1개 항목 2개 합계 17m`(격리 세션에서 `$HOME` 을 펼친 절대경로로 exit 0). 티켓이 있을 때의 형식은 단위 1 테스트가 고정한다.
  - 코드 리뷰는 ultracode workflow(관점 3개 + finding 별 반증 검증).
- 2026-10-01: 코드 리뷰 — finding 13건(확인 4·반증 1·미검증 8, 에이전트 8). fix 1회: 이름 없는 경로·등록 계획 실패·일부 쓰기 실패·디렉터리 이름 선택을 고정하고, subprocess 원인을 고정했다. `/wt rm` 미리보기 조건·등록 안내·README 문구를 고쳤다. 변이 17종(`jira_worklog.py`) 모두 KILLED — 각각 해당 사례에서만. 처분은 # Review Disposition.
  - simplify: 자격증명 사례의 `Config` 재생성을 `dataclasses.replace` 로.

# Next
- 격리 runner(Acceptance 5) → plan·intent 기록을 마지막 단위 fixup 으로 → commit-check(단위 3 메시지의 미리보기 조건 문구 수정) → 마무리(medium — `/e merge` 가 규칙 기본, push 는 사용자 선택).

# Decisions
- 관련 결정: 공용 wiki `worktree-isolation-bash-guard` — 격리 세션은 `bash "$HOME/…"` 를 거부한다. `/wt rm` 의 미리보기 명령 표기에 반영한다(`/e` 2단계와 같은 규칙). 뒤집는 결정은 없다.
- 테스트는 새 파일에 둔다 — 기존 테스트는 모듈 단위(등록 게이트·세션 시간·scope)라 CLI 종료 계약을 한곳에 모은다.
- 경계: in-process `main()` 에 `load_config`·git 목록·세션 스캔·Jira·복구 로그를 `mock.patch.object(jira_worklog, …)` 로 바꾸고, `HOME`·`USERPROFILE` 임시화와 `urlopen` 차단으로 한 번 더 막는다(리뷰 강1 — `load_config` 는 실제 `~/.jira-kit/.env` 를 읽고 자격증명이 있으면 `fetch_cloud_id` 로 네트워크를 쓴다).
- `sys.exit(main())` 고리는 subprocess 1건으로 고정한다(리뷰 강2 — in-process 는 그 줄을 지나지 않아, 그 줄이 `main()` 이 되면 모든 실패가 exit 0 이 된다). 설정 오류는 git·세션 스캔·네트워크보다 먼저 나서 가짜 Jira 없이 만들 수 있다. 기각: 모든 사례를 subprocess 로 — 게이트 차단·Jira 실패에는 가짜 Jira 서버가 필요하다. argparse 오류로 고정 — `SystemExit` 이 그 줄과 무관하게 전파된다.
- 계약 고정이라 테스트는 지금 코드에서 통과해야 한다. TDD Red 는 scratch 복사본 변이로 확인하고, 위험한 방향(실패 → 0)을 포함한다(리뷰 약5). 추적 파일 `jira_worklog.py` 는 건드리지 않는다.
- `/wt rm` 의 미리보기 조건을 "스킬 디렉터리와 `~/.jira-kit/.env`"에서 "스킬 디렉터리"로 바꿨다(코드 리뷰 — plan 리뷰 약2(d)를 뒤집음). 이유: `load_config` 는 자격증명을 환경변수·프로젝트 `.env`·`~/.jira-kit/.env` 에서 받는데 `.env` 파일 조건은 앞의 둘을 쓰는 사용자의 경고를 없앤다. 미리보기는 자격증명 없이 돌고, `/e` 6단계도 미리보기는 스킬 존재만 본다. 스캔 비용(수 초)은 수동 `rm` 한 번이라 감수한다.
- `/wt rm` 은 등록을 대신 하지 않고 경고만 한다(묶음 Constraints). 미리보기는 Jira 를 보지 않아 이미 등록했는지 모르므로 "등록하지 않았다면" 조건을 달고, 등록이 upsert 라 다시 돌려도 중복이 없다고 적는다. 종료코드만 믿지 않는다 — Windows 에서 비0 이 보이는지 모른다(#190).
- CLAUDE.md §8 은 기전만 바로잡는다 — `/e` SKILL 6단계의 "이름으로 고를 수 없어" 문구에 맞추고 줄을 늘리지 않는다.
- 기각(대안): plan 3개로 분할(위 `분할:`), `/wt rm` 에서 삭제를 막거나 대신 등록(묶음 Constraints — 등록은 사용자가 동의한 경로에서만), 복구 로그(`~/.claude/logs/jira-worklog-*.jsonl`)로 등록 여부 추정(등록 직전에 쓰는 best-effort 기록이라 HTTP 실패와 구분하지 못한다).
- rollback: 테스트·문서만 바뀐다 — 단위 커밋 revert. 되돌리기 비싼 경로는 변이가 `jira_worklog.py` 에 남은 채 커밋되는 것뿐이라 변이는 scratch 복사본에서만 한다.
- 커밋 단위: 1) `test(jira-worklog): pin the exit-code contract that /e relies on` — `skills/jira-worklog/test_exit_contract.py`·`skills/jira-worklog/test_launcher.sh`·README 파일 트리 줄 2) `docs: explain why a deleted worktree's time cannot be registered` — `skills/jira-worklog/SKILL.md`·`CLAUDE.md` 3) `docs(wt): warn about unregistered worklog time before rm` — `skills/wt/SKILL.md`·README `/wt` 절. README 는 단위 1·3 이 다른 줄을 고친다. plan·intent·선행 plan 의 `intent:` 줄은 기록 파일이라 마지막 단위의 fixup 으로 싣는다.

# Key Files
- `skills/jira-worklog/test_exit_contract.py` — 새 종료코드 계약 테스트
- `skills/jira-worklog/test_launcher.sh` — 127·`exec` 전달 사례
- `skills/jira-worklog/jira_worklog.py` — 계약의 원천(바꾸지 않음)
- `skills/jira-worklog/SKILL.md`·`CLAUDE.md` §8 — 기전 문구
- `skills/wt/SKILL.md` rm·`README.md` `/wt` 절·파일 트리 — worklog 경고, 새 테스트 줄
- `skills/e/SKILL.md` 6단계 — 계약을 쓰는 쪽(대조 기준)
- `plans/2026-09-30-worklog-deletion-safety/intent.md`·`plans/2026-09-30-e-worklog-gate/e-worklog-gate-plan.md`(`intent:` 1줄)

# Blockers
없음

# Review Disposition
plan 리뷰 — plan-reviewer CONDITIONAL(Codex 미가용 — 한도 소진).
- 강1 `load_config` 미격리(실제 `~/.jira-kit/.env`·`fetch_cloud_id` 네트워크) — fix: 모든 사례에서 patch, `HOME`·`USERPROFILE` 임시화, `urlopen` 차단.
- 강2 `sys.exit(main())` 고리 미고정 — fix: 깨진 `jira-kit.toml` subprocess 1건(프로세스 종료코드 2).
- 강3 exit 0 사례끼리 구분 안 됨(헛통과) — fix: 사례별 경로 단언, bucket 키는 넘겨받은 `index.classify`.
- 강4 미리보기(활동·티켓 있음) → 0 누락 — fix: 사례 추가, `/e` 가 닿지 않는 조건(헬퍼 거부·토큰 파일)을 명시.
- 약1 launcher PATH 함정 — fix: bash 절대경로, 전용 PATH 디렉터리, `|| rc=$?`, "command not found" 부재 단언, `exec` 전달(3) 사례.
- 약2 `/wt rm` 미리보기 세부(대상 dir 이름·대상 블록만·머리줄 없으면 실패·스킬·토큰 파일 없으면 생략·거부 검사 뒤) — fix(Acceptance 4). `docs/worktree-lifecycle.md` 37행 보강은 선택이라 하지 않는다 — wontfix(그 줄은 확인 경로 요약이고 절차는 SKILL 이 단일 소스).
- 약3 README 파일 트리 동기화 — fix(단위 1).
- 약4 plan·intent 파일의 커밋 위치 — fix(# Decisions 커밋 단위).
- 약5 변이 절차 — fix(Acceptance 1·# Decisions: scratch 복사본, 위험한 방향 포함, 사례별 실패, 커밋 전 diff 확인).
- 약6 GitError 위치별 종료코드·"등록 불가" 부재 단언 — fix(Acceptance 1).
- 약7 불가역 단정·CLAUDE.md 길이 측정 — fix(Acceptance 3, 수정 전 281자).
- 약8 # Intent 델타 중복·`분할:` 근거·기각 대안 — fix.
- 약9 runner 명령 미정의 — fix(Acceptance 5).
- 누락 시나리오: 예상 밖 예외가 0 으로 삼켜지지 않는지 — fix(Acceptance 1). `/wt rm <정수>`·한 이름 두 매칭·토큰·스킬 없음·Jira 안 쓰는 repo — fix(Acceptance 4). 공개 점검 후보 — defer(# Deferred).

코드 리뷰 — ultracode workflow(관점 3개: 테스트 정확성·계약 빈틈 적대 탐색·문서 정확성, finding 별 반증 검증 최대 2건/관점, Codex 미가용).
- [확인] 이름 없는 기본 경로(`current_worktree` → `sys.exit`) 미고정 — 두 관점이 따로 찾음 — fix(이름 없는 미리보기 0·최상위 아님 1).
- [확인] 등록 계획 실패 경로(`return len(rows)` → 0 생존) — fix(subtest).
- [확인] `/wt rm` 미리보기의 `.env` 조건이 자격증명 출처보다 좁다 — fix(스킬 존재만, # Decisions).
- [반증] 자격증명 불완전이면 권한 `--register` 가 조용히 0 — 반증됨(stderr "등록 불가" 가 직접 보이고 성공 줄이 없다).
- [미검증] subprocess 가 상위 `.env` 를 읽을 수 있다(Windows 임시 경로가 홈 아래) — fix(빈 `.env`·원인 단언).
- [미검증] 항목 1개 fixture 는 일부 실패를 못 가른다 — fix(이틀 fixture·일부 쓰기 실패).
- [미검증] fixture 의 디렉터리 이름 = branch — fix(`worktree-` 접두 branch).
- [미검증] 경고의 등록 명령이 POSIX 전용이고 게이트 차단 뒤 안내가 없다 — fix(미리보기 명령 + `--register`, `--allow-large-change`).
- [미검증] README 의 "등록하지 않은 시간" — fix("등록할 시간(티켓·합계)").
- [미검증] Codex bucket 병합 배선 미고정 — defer(종료코드 계약 밖, # Deferred).
- [미검증] jira_kit 의 HTTP → `JiraError` 변환 미고정 — defer(# Deferred).
- [미검증] `run_worklog.ps1` 은 실행기가 없으면 127 이 아니라 throw, `exec uv` 전달 미검증 — defer(#190 과 함께, # Deferred).

# Deferred
- `main()` 이 Codex bucket 을 Claude bucket 에 합치는 배선을 고정하는 테스트가 없다(병합 함수 단위 테스트는 있다). 배선이 빠지면 Codex 만 쓴 worktree 가 "세션 활동 없음"(0)이 돼 `/e` 가 지운다 — 낮음, `skills/jira-worklog/`.
- `jira_kit` 이 HTTP 실패를 `JiraError` 로 바꾸는지 고정하는 테스트가 없다(이번 테스트는 그 위에서 patch) — 낮음, `skills/jira-worklog/jira_kit/jira_client.py`.
- `run_worklog.ps1` 은 실행기가 없으면 127 이 아니라 throw 한다(`/e` 6단계 목록은 127). `exec uv` 경로의 종료코드 전달도 테스트하지 않았다 — Windows 에서 #190 비0 가시성 항목과 함께 확인.
- jira-worklog 스킬 8개 파일 51줄(`SKILL.md`·`jira_worklog.py`·`jira_kit/*`·기존 테스트 3개)에 비공개 목록 용어(티켓 키 prefix·repo 이름 예시 등)가 있다. 공개 repo 라 §11 공개 점검 위반이다. README 408·410 은 같은 사실을 이미 일반화했다. 기본 티켓 패턴·fixture 에 걸려 있어 작은 문구 수정이 아니다 — 식별자 정리 이슈 #206 과 함께 처리(중요도 높음, 사용자 판단).
