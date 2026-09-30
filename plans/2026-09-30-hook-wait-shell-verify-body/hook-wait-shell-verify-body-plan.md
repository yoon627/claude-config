---
title: hook-wait-shell-verify-body — 이번 턴에 띄운 background shell 은 대기로 보고, 작은 검증 래퍼 스크립트는 본문으로 검증을 인식한다
status: in_progress
started: 2026-09-30
updated: 2026-09-30
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal
early-stop hook 의 오탐 두 가지를 없앤다.
1. 이번 턴에 `run_in_background` 로 띄운 Bash 를 기다리며 턴을 닫으면 결론·검증 경고가 난다 — subagent·workflow 대기처럼 미룬다.
2. `bash <file>.sh` 래퍼 안에서 테스트를 돌렸는데 이름이 규칙에 안 맞아 "검증 없음" 경고가 난다 — 작은 스크립트는 본문으로 판정한다.

# Intent
- 묶음: `plans/2026-09-25-repo-audit-followups/intent.md`. 선행 `plans/2026-09-27-ledger-bash-edits` 의 후속이다(그 plan 이 대기 턴 억제를 subagent·workflow 로 한정했고, 래퍼 본문 판정은 # Deferred 로 넘겼다).
- 델타 — Problem: 2026-09-27~30 transcript 분류(독립 반증 에이전트와 일치).
  - 대기 턴 수정이 live 로 들어간 뒤(main 반영 2026-09-27T08:38Z)의 결론 경고 7건이 모두 background shell 대기 턴이었다(머지 뒤 배포 감시·`gh run watch`·until-loop).
  - 검증 경고 2건은 실제로 gradle 테스트를 돌려 통과했지만 래퍼(`bash <scratch>/<이름>.sh`, 격리 runner 경로) 안이라 `VERIFY_SCRIPT` 이름 규칙(키워드가 `.sh` 바로 앞)에 안 맞았다.
  - 사용자 승인(2026-09-30): 대기 턴은 hook 으로(이번 턴 shell 만), 래퍼는 본문 판정으로.
- 델타 — Constraints: fail-open 유지(손상 장부·이상한 입력·파일 오류에도 exit 0, 같은 Bash 의 기존 기록 유지), 상시 프롬프트 비용 0, `VERIFY_SCRIPT` 이름 규칙은 넓히지 않는다(checkout.sh·test-data-loader.sh 오인식 락 유지).
- 델타 — Out of scope: 이전 사용자 턴에 띄운 서버·tail(계속 경고), Ctrl+B·timeout 으로 자동 background 된 명령(`run_in_background` 없음 — 경고 유지), 두 단계 이상 중첩 스크립트·`./x.sh` 직접 실행·`$VAR` 경로(변수는 풀지 않는다)·`\` 줄 이어쓰기로 나뉜 명령·`cat > x.sh <<…` 로 만들고 한 명령에서 실행(명령 첫 단어 veto)·실행 뒤 지운 스크립트, Windows PowerShell 도구 호출(PostToolUse matcher 가 Bash 만 본다 — 장부 전체의 기존 한계, 경고가 남는 쪽), `skills/wiki/wiki_check.py` 의 `WAIT_TYPES` 복제본(장부가 없어 이번 턴 shell 을 알 수 없다 — 그대로 둔다), Codex 쪽 hook.
- 분할: 없음 — 머지 무모순 기준으로는 두 수정이 나뉜다(각각 혼자 머지돼도 유효하다). 그러나 고정비(worktree·리뷰·머지)가 두 배인 데 비해 이득(독립 롤백)이 작고, 독립 롤백은 단위 커밋 revert 로 대신한다. 선행 plan 도 같은 처리를 했다.

# Acceptance
1. **대기 턴 — 장부**(`scripts/dlc-evidence-ledger.test.js`): `tool_input.run_in_background === true` 이고 `tool_response.backgroundTaskId` 가 비지 않은 문자열인 Bash 만 그 id 를 `bgTaskIds` 에 기록한다(중복 없이, 최근 50개). `run_in_background` 가 없는 Bash(timeout 자동 background 포함)는 기록하지 않는다. `dlc-ledger.js` 의 `DEFAULT.bgTaskIds: []` 라 사용자 턴 리셋에 비워진다. 손상 장부(`bgTaskIds` 가 null·문자열·객체)에서도 exit 0 이고 같은 Bash 의 `verified` 기록이 유지된다.
2. **대기 턴 — Stop**(`scripts/dlc-early-stop.test.js`):
   - `background_tasks` 에 `type: shell` 이고 `id` 가 `bgTaskIds` 에 있는 항목이 있으면 경고 없이 통과하고, 장부를 바꾸지 않고, activity 신호 `early-stop-wait-shell` 을 1건 남긴다.
   - `bgTaskIds` 에 없는 id(이전 턴 서버)·id 없는 항목만 있으면 기존대로 경고한다.
   - 손상 장부(null·문자열·객체)면 exit 0 이고 억제하지 않는다(문자열 부분 일치로 억제하지 않는다).
   - `stop_hook_active: true` 와 이번 턴 shell 이 함께면 장부를 바꾸지 않는다.
   - 기존 대기 턴 테스트는 그대로 통과한다.
3. **검증 래퍼**(`scripts/dlc-evidence-ledger.test.js`):
   - 명령 원문(대소문자 유지)에서 `(^|\n|&&|;) bash|sh [옵션] <file>.sh` 의 경로를 뽑는다. `~/` 는 홈으로, 상대경로는 `cwd` 기준으로 푼다. 변수는 풀지 않는다. 한 명령에서 최대 3개까지 본다.
   - 16KB 이하 일반 파일이면 본문(CRLF 허용 — BOM 은 JS `\s` 가 공백으로 읽어 따로 지우지 않는다)에서 주석·heredoc 본문·`NONVERIFY_START` 줄을 뺀 한 줄이 `VERIFY` 또는 `VERIFY_SCRIPT` 에 맞으면 `verified=true`. 한 단계만 본다.
   - 양성: 대소문자가 섞인 디렉토리의 래퍼(Linux CI 에서 소문자화 버그를 잡는다), cwd 기준 상대경로·`~/`·옵션·개행 앵커, CRLF 본문의 `<<-` heredoc 뒤 검증 줄, 본문의 `VERIFY_SCRIPT`, 두 번째 래퍼.
   - 음성: 본문이 주석·`echo` 뿐, heredoc 도움말 안의 `npm test`, BOM 뒤 주석, 16KB 초과, 파일 없음, 변수 경로, FIFO, 읽기 오류(EACCES), 네 번째 래퍼, 실제 파일 `deploy.sh`(검증 명령 없음) — 모두 불변. 기존 `VERIFY_SCRIPT` 오인식 락 테스트는 그대로 통과한다.
4. **실제 형태**: fixture 는 실제 도구 결과 형태(`backgroundTaskId`·`stdout`·`stderr`·`interrupted` 키 — 이 세션 transcript 에서 확인)와 일반 이름 래퍼(`x_final.sh` 안의 `./gradlew build -q > log 2>&1`)로 만든다. 다른 repo 의 이름·경로·클래스명은 넣지 않는다(§11).
5. **문서**: README hook 절(`dlc-evidence-ledger.js`·`dlc-early-stop.js` 설명, 한계 — 기록이 다음 사용자 프롬프트까지 이어짐·subagent 가 띄운 shell 도 기록·같은 턴 서버·자동 background 는 기록 안 함·`backgroundTaskId` 는 문서에 없는 필드(2.1.285 확인)), `settings.json` 등록 줄, 신호 kind 목록, 두 스크립트 머리·`WAIT_TYPES` 주석, `dlc-ledger.js` 필드 주석이 새 동작과 맞다 — `rg -n "bgTaskIds|backgroundTaskId|wait-shell|래퍼" README.md scripts/` 대조.
6. `bash scripts/verify.sh` 마지막 줄이 main 과 같은 skip 만 둔 `ALL PASS`, `bash skills/improve/improve.sh --ci` exit 0 — 격리 runner.
7. **기준선**: 머지 전 기준(2026-09-27T08:38Z~09-30 분류 — 결론 경고 11건 중 7건이 shell 대기, 검증 경고 4건 중 2건이 래퍼)을 # Progress 에 두고, 다음 `/improve` 에서 두 유형이 줄었는지와 `early-stop-wait-shell` 수를 본다. shell 대기 뒤 알림 턴의 결론 경고는 "옮겨 간 경고"로 따로 센다(# Decisions — 코드 리뷰 M4).
8. [post-merge] **실측(대조군 포함)**: main 반영 뒤 이 세션에서
   - (a) 편집 → `run_in_background` 로 짧은 대기 명령을 띄우고 결론 없이 턴을 닫는다 → 경고 없음, `early-stop-wait-shell` 신호 1건, 장부 `bgTaskIds` 에 그 id.
   - (b) 그 명령의 완료 알림 턴에서 편집 뒤 결론 없이 닫는다 → 결론 경고(대조군).
   - (c) 편집 뒤 `bash <scratch>/x_final.sh`(본문에 검증 명령) → 장부 `verified=true`.

# Progress
- 2026-09-30: `/wt` 로 worktree 생성(base `main@b881777`). 계획 전 조회로 공용 wiki `workflow-failures`(대기 턴·Bash 경유 검증 행), `codex-cli-agents-and-hooks`(Codex 에는 `background_tasks` 가 없다)를 읽었다. 선행 plan `ledger-bash-edits` 의 # Decisions·# Deferred 를 확인했다.
  - 문서 조사(공식 hooks 문서): Stop 입력 `background_tasks` 항목에 `id`·`type`(shell·subagent·monitor·workflow…)·shell 전용 `command`(1000자 상한)가 있다. 끝나는 shell 과 서버를 가르는 필드는 없다.
- 2026-09-30: plan 리뷰 CONDITIONAL(강 4·약 다수, Codex 미가용). 처분은 # Review Disposition.
  - 매칭 키를 id 로 바꿨다. 이 세션 transcript 실측: `run_in_background` Bash 의 도구 결과 `backgroundTaskId` 2건이 완료 알림 `<task-id>` 와 같았다(timeout 자동 background 1건은 `timedOutAfterMs` 가 있었다).
  - 리뷰어 관찰: subagent·runner 의 Bash PostToolUse 가 부모 장부에 쓴다. 30일 재생에서 래퍼 본문 규칙이 새로 인식하는 것은 57건이고 표본 오인식은 0, 16KB 초과는 0 이었다.
  - 기준선(Acceptance 7): 결론 경고 11건 중 shell 대기 7, 검증 경고 4건 중 래퍼 2(나머지는 대기 턴 수정 전 subagent 3·실측 대조 1, probe 2).
- 2026-09-30: 단위 1(이번 턴 shell 대기) — Red(기록 없음·경고 발생·kind 없음) → 구현 → Green → 단위 커밋.
  - 실제 결과 키(transcript): `backgroundTaskId`·`interrupted`·`isImage`·`noOutputExpected`·`stderr`·`stdout`, timeout 자동 background 는 `timedOutAfterMs` 가 더해지고 입력에 `run_in_background` 가 없다 — fixture 를 이 형태로 맞췄다.
  - 변이 10종(가드·type·신호·판정 순서·조건·상한·중복·기본값) 모두 KILLED.
- 2026-09-30: 단위 2(래퍼 본문) — Red(`false`) → 구현 → Green → 단위 커밋, BOM 테스트는 fixup.
  - 변이 18종 KILLED. 소문자 경로 변이는 macOS(대소문자 무시)에선 드러나지 않아, 대소문자 구분 APFS 이미지에서 원본 Green·변이 KILLED 를 확인했다(이미지는 분리·삭제). try/catch 변이는 ENOTDIR 로는 안 잡혀(`throwIfNoEntry:false` 가 ENOTDIR 도 삼킨다) EACCES 사례로 바꿨다.
- 2026-09-30: 코드 리뷰 APPROVE(Minor 5·Nit 7) → fix 1회. 처분은 # Review Disposition. 반영분은 단위별 fixup 이다. 두 단위가 함께 고친 `dlc-evidence-ledger.js`·README 의 반영분은 단위 2 fixup 으로 보냈다(귀속 예외: `BG_TASK_MAX` 이동, README 469·538 문구). 변이 7종 KILLED, 테스트 Green.
  - simplify 체크(메인): 래퍼 카운터 → `slice(0, WRAPPER_MAX)`, `ownShellWait` 의 `!ids.length` 중복 검사 제거, `BG_TASK_MAX` 를 래퍼 블록 밖으로 — 동작 불변, 위 테스트·변이로 재확인. 판정식 공통화는 줄지 않아 보류했다.
- 2026-09-30: 격리 runner 최종 검증 — `bash scripts/verify.sh` exit 0, 마지막 줄 `ALL PASS (skip: install-codex-skill.test.ps1)`(main 과 같은 skip — PowerShell 미설치), 세 테스트 파일 `ok`. `bash skills/improve/improve.sh --ci` exit 0(error 0·warn 0, settings.json 이 untracked 라 점검 1 은 이 환경에서 안 돈다).
  - evidence gate: Acceptance 1–3 테스트·변이, 4 transcript 키·공개 점검 0건, 5 `rg` 대조(README 472 의 "억제" 문구를 검증 중에 고쳤다 — README 를 읽는 테스트는 없다), 6 runner, 7 기준선 기록 — 충족. 8 은 머지 뒤.

# Next
- commit-check(fixup 합치기, 단위 1 메시지의 "over-suppression stays visible" 문구를 대기 턴 수로 고친다) → 로컬 main(`1851661`) 위로 rebase·재검증 → close 커밋 → worktree 밖으로 나와 ff-merge → 정리 → Acceptance 8 실측 → main 세션에서 공용 wiki `workflow-failures` 적립.

# Decisions
- 관련 결정 변경(사용자 승인 2026-09-30): `ledger-bash-edits` 의 "shell 은 대기로 보지 않는다"(그 리뷰의 wontfix — 전제 "결과를 기다리는 검증은 보통 foreground")를 "이번 사용자 턴에 `run_in_background` 로 띄운 shell 은 대기"로 좁혀 변경한다. 이유: 대기 턴 수정이 live 가 된 뒤의 결론 경고 7건 전부가 shell 대기 턴이었다(머지 뒤 배포 감시 등 — foreground 전제가 맞지 않았다).
- `ledger-bash-edits` # Deferred 의 "래퍼 본문 판정은 오인식 위험 — 별도 판단"을 채택한다(사용자 승인). 위험은 크기·일반 파일·줄 단위 veto·heredoc 건너뜀·한 단계로 줄인다. `npm run build` 같은 build 명령도 검증으로 본다 — 직접 명령의 기존 의미와 같다.
- 묶음 연결: 두 부분 모두 `ledger-bash-edits` 의 결정(대기 턴 제외 범위, # Deferred)을 다듬는 일이라 그 묶음에 둔다. `/improve` 발 개선 묶음 `improve-followups` 는 이미 닫혔다.
- 대기 턴 매칭 키: PostToolUse `tool_response.backgroundTaskId` ↔ Stop `background_tasks[].id`(리뷰 강1).
  - 근거: 2.1.285 바이너리 판독(리뷰 — 등록 id·Stop `id`·알림 task-id 가 같은 값)과 이 세션 transcript 실측(2/2).
  - 기록 조건은 `run_in_background === true`(명시 의도)만이다. Ctrl+B·timeout 자동 background 는 기록하지 않아 경고가 남는다.
  - `backgroundTaskId` 는 hooks 문서에 없는 도구 출력 필드다. 이름이 바뀌면 억제가 안 되는 쪽(경고 유지)으로만 틀린다.
  - 기각: 명령 문자열 키 — Stop `command` 는 1000자를 넘으면 `… [+N chars]` 가 붙어(30일 508건 중 24건) 안 맞고, 같은 문자열의 이전 턴 서버·Monitor task 와 섞인다.
- 범위: 장부 리셋은 사용자 프롬프트에만 있다(알림 턴은 리셋하지 않는다). 그래서 기록은 다음 사용자 프롬프트까지 이어진다. subagent·runner 의 Bash 도 부모 장부에 쓰므로 그들이 띄운 shell 도 기록된다. 둘 다 README 한계에 적는다.
- 대기 턴 telemetry: 이번 턴 shell 로 미룬 Stop 마다 activity 신호 `early-stop-wait-shell` 을 남긴다 — 과억제를 볼 수단이 없다는 plan 리뷰 지적 때문이다(선행 # Deferred 의 억제 telemetry 를 이 축에 한해 채택).
  - 장부에 걸린 경고가 없어도 남는 대기 턴 수다. 처음 적은 "억제량"은 과장이라 문구를 고쳤다(코드 리뷰 M3). 과억제(실제로는 기다리지 않은 턴)는 이 신호의 session·시각으로 transcript 를 찾아 가른다.
  - 기각: 걸려 있던 축을 `detail` 에 넣는 안. 검증·결론 판정식을 대기 경로에 복제해야 하고, 과억제인지는 어차피 transcript 로만 가를 수 있다.
- 검증 래퍼 판정: Acceptance 3 의 규칙. `stat` 으로 일반 파일인지 먼저 본다(FIFO 에서 읽기가 막히지 않게). 목록 상한(래퍼 3개, id 50개)을 둔다.
- 구현하며 좁힌 것(2026-09-30): 래퍼 앵커에서 `||` 를 뺐다(초안에 내가 더한 것 — 실제 사례가 없다). BOM 은 따로 지우지 않는다(JS `\s` 가 U+FEFF 를 공백으로 읽어 주석·veto 판정이 같다 — 테스트로 잠갔다). `\` 줄 이어쓰기는 합치지 않는다(Out of scope). 변수 경로는 풀지 않으니 문자 그대로 찾아 없으면 불변이라 별도 코드 없이 테스트로만 잠갔다. 한 명령 안에서 `cat > x.sh <<…` 로 만들고 바로 실행하는 형태는 명령 첫 단어 `cat` veto 로 인식되지 않는다 — 처음 적은 "PostToolUse 시점에 파일이 있어 인식된다"는 틀렸다(코드 리뷰 N1). Out of scope 에 되돌렸다.
- ⚠️ 본문 줄이 실제로 실행되는지는 보지 않는다 — `case` 분기·부르지 않는 함수·메시지·설치 줄도 세고, 명령 쪽 인용도 가리지 않는다 — gate 를 헐겁게 하지 않는다는 제약과 상충 — 문서화하고 감수한다(코드 리뷰 M2). 이유: 사용자가 본문 판정을 골랐고, 분기·함수를 가르려면 셸 파서가 필요하다. plan 리뷰의 30일 재생 표본과 이 repo 스크립트 재생(리뷰어)에서 오인식이 없었다.
- 대기 턴에 쓴 `## 결론` 은 소비하지 않는다(코드 리뷰 M4) — subagent 대기와 같은 의미다(결과가 온 뒤의 턴에서 판정). 결론을 대기 턴에 쓰고 알림 턴을 한 줄로 닫으면 결론 경고가 알림 턴으로 옮겨 간다. README 에 적었고, Acceptance 7 비교에서는 이 옮겨 간 경고를 따로 센다.
- 억제 신호 `early-stop-wait-shell` 은 `stop_hook_active` 재종료에서도 남긴다 — 다른 Stop hook 이 막은 턴에만 생겨 드물고, 조건을 더하는 비용이 더 크다.
- 기각(대안): shell 전부 대기(이전 턴 서버·tail 이 영구히 경고를 끈다), 명령 패턴 휴리스틱(until·watch — 형태가 다양하고 서버와 가를 근거가 없다), `/e` 에 "대기 턴도 결론 블록" 한 줄(사용자가 hook 안을 골랐고 `/e` 밖 대기 턴은 못 덮는다), 격리 runner 래퍼 이름 규약 `…-verify.sh`(모델 준수에 기대고 어긋난 사례가 이미 2건), `VERIFY_SCRIPT` 이름 규칙 확장(checkout.sh·test-data-loader.sh 락을 깬다).
- ⚠️ 같은 턴에 띄운 서버를 기다리지 않고 턴을 닫거나, 그 서버가 도는 동안의 알림 턴은 경고가 빠진다 — 대기 턴 오탐 제거와 상충 — 오탐 제거를 택한다(규칙 §3-6 은 그대로이고 hook 은 보조망이며, `early-stop-wait-shell` 신호로 그 턴을 찾아 과억제를 가른다).
- rollback: 단위 커밋을 main 에서 `git revert` 하면 hook 이 이벤트마다 main 사본을 읽어 즉시 원복된다. 새 장부 필드는 옛 코드가 무시하고 새 코드는 없으면 기본값을 써서 양방향 호환이다. README 같은 문단을 두 단위가 고쳐 단위별 revert 는 수동 충돌 해소가 필요할 수 있다.
- 커밋 단위: 1) `fix(hooks): treat a background shell started this turn as a wait at Stop` — `scripts/dlc-ledger.js`·`scripts/dlc-evidence-ledger.js`(bgTaskIds)·`scripts/dlc-early-stop.js`·`scripts/dlc-signal.js`(kind)·세 테스트·README 해당 문장 2) `fix(hooks): recognize verification inside small wrapper scripts` — `scripts/dlc-evidence-ledger.js`(본문 판정)·그 테스트·README 해당 문장.

# Key Files
- `scripts/dlc-evidence-ledger.js` — `bgTaskIds` 기록, 래퍼 본문 판정
- `scripts/dlc-ledger.js` — `DEFAULT.bgTaskIds`, 필드 주석
- `scripts/dlc-early-stop.js` — 이번 턴 shell 대기 판정, `WAIT_TYPES` 주석, 신호
- `scripts/dlc-signal.js` — `early-stop-wait-shell` kind
- `scripts/dlc-evidence-ledger.test.js`·`scripts/dlc-early-stop.test.js`·`scripts/dlc-signal.test.js`
- `README.md` — hook 절, `settings.json` 등록 줄, 신호 kind
- `plans/2026-09-25-repo-audit-followups/intent.md` — # Plans 줄

# Blockers
없음

# Review Disposition
plan 리뷰 — plan-reviewer CONDITIONAL(Codex 미가용).
- ⚠️ self-flag 1(command 문자열 동일성) — resolved: 키를 `backgroundTaskId`↔`id` 로 바꿨고 transcript 로 확인했다.
- ⚠️ self-flag 2(같은 턴 서버) — accepted-risk: 알림 턴까지 이어지는 범위를 README 한계에 적고, `early-stop-wait-shell` 신호로 과억제를 본다.
- ⚠️ self-flag 3(분할) — resolved: `분할:` 줄을 머지 무모순 기준 그대로(나뉘지만 합친다)로 고쳤다.
- 강1 매칭 키 — fix(위). 강2 손상 장부에서 exit 1·기록 유실 — fix: `Array.isArray` 가드·concat·상한, Acceptance 1·2 에 손상·`stop_hook_active` 케이스. 강3 Acceptance 7 실행 불가 — fix: 핵심 가정은 머지 전 transcript 로 확인했고, 실측을 대조군 있는 8(a)(b)(c)로 바꿨다. 강4 선행 결정 변경·빠진 대안 — fix(# Decisions).
- 약: 억제 범위(알림 턴·subagent) — fix(README 한계·신호). 억제 telemetry — fix(kind 추가). 소문자화된 명령에서 경로를 뽑는 함정 — fix(원문 사용, 대소문자 fixture). `~`·`$VAR`·상대경로·`\n` 앵커·여러 래퍼·FIFO·본문의 `VERIFY_SCRIPT` — fix(Acceptance 3). heredoc 도움말 오인식 — fix(heredoc 본문 건너뜀 + 음성 테스트). 공허한 락 테스트 — fix(실제 파일 `deploy.sh` 음성). build 명령 의미 — fix(# Decisions). `wiki_check.py` 복제본 — wontfix(Out of scope 에 사유). `dlc-ledger.js` 주석·README 469·537 — fix(Acceptance 5). runner 가 부모 장부에 쓰는 사실 — fix(# Progress). 묶음 연결 — fix(# Decisions). 공개 점검 fixture 이름 — fix(Acceptance 4). rollback·기준선 — fix(# Decisions·Acceptance 7).
- 누락 시나리오: 자동 background(경고 유지 — Out of scope), 턴 종료 전 완료(Stop 목록에 없어 경고 — 타이밍, 감수), 병렬 Bash 장부 경합(기록 유실 → 경고 유지, 감수), 한 명령 안에서 만들고 실행·실행 뒤 삭제(인식 안 함 — Out of scope), CRLF·BOM(fix — Acceptance 3), 긴 자율 세션(fix — 상한 50), id 없는 Stop 항목(fix — Acceptance 2).

코드 리뷰 — code-reviewer APPROVE(Critical·Major 0, Minor 5·Nit 7). Codex 는 한도 소진으로 생략했다.
- M1 heredoc 이 `<<\EOF`·하이픈 든 구분자를 못 알아봐 도움말의 `npm test` 를 검증으로 셈 — fix: 정규식에 `\\?`·`-` 를 더하고 음성 테스트 2개.
- M2 본문 줄의 실행 여부를 보지 않음(분기·함수·메시지·설치 줄), 명령 쪽 인용도 안 가림 — fix(README 한계) + accepted-risk(# Decisions ⚠️).
- M3 신호가 억제량이 아니라 대기 턴 수 — fix(주석·README·plan 문구). detail 안은 기각(# Decisions).
- M4 대기 턴에 쓴 결론을 소비하지 않아 결론 요구가 알림 턴으로 옮겨 감 — wontfix: subagent 대기와 같은 의미다. README 에 적고 Acceptance 7 에서 따로 센다.
- M5 README 537·538 등록 줄 미갱신 — fix.
- N1 plan 의 "한 명령 안에서 만들면 인식" 문구가 틀림 — fix(정정, Out of scope 로).
- N2 try 가 래퍼 루프 전체를 감싸 앞 래퍼 오류가 뒤 래퍼 판정을 끊음 — fix(래퍼마다 try, 테스트).
- N3 stat 과 read 사이에 FIFO 로 바뀌는 경우 — wontfix: 확률이 극히 낮고, hook timeout 10s 로 끝나 그 Bash 기록만 잃는다(경고가 남는 쪽).
- N4 대시 없는 `<<` 의 탭 든 끝 줄·한 줄에 heredoc 둘·CR 단독 개행 — wontfix(인위적 입력).
- N5 README 한계에 못 보는 쪽 목록이 빠짐 — fix.
- N6 `typeof t.id` 가드를 잡는 테스트가 없음 — fix(`[null]` 장부 + `id: null` 사례).
- N7 판정식 중복 — wontfix(함수로 빼도 호출부의 veto 가 남아 줄지 않는다). `BG_TASK_MAX` 위치 — fix(래퍼 블록 밖으로).
- Open: Windows PowerShell 도구 사용 여부 ❌모름(Out of scope·# Deferred). subagent PostToolUse 의 `cwd` 가 호출마다 리셋되는지 ❌모름 — 실제 2건은 절대경로라 영향이 없었다.
- 반영분 변이 7종 모두 KILLED.

# Deferred
- 공용 wiki `workflow-failures` 추적 표 적립(대기 턴 행 shell 하위 유형 +5, Bash 경유 검증 행 +2)과 이 수정의 상태 반영 — `~/.claude` main 세션에서(사용자 승인 2026-09-30).
- 다음 `/improve` 에서 Acceptance 7 기준선과 비교하고, `early-stop-wait-shell` 이 찍힌 턴의 transcript 로 과억제(실제로는 기다리지 않은 턴)를 가른다.
- Windows 에서 PowerShell 도구가 켜져 있으면 그 호출은 장부가 보지 않는다(matcher `Edit|Write|NotebookEdit|Bash`) — 검증·background 기록 모두. 켜져 있는지 ❌모름, 낮음.
- `skills/improve/SKILL.md` 점검 7 의 kind 나열이 `KINDS` 와 어긋난다 — failure 에 `early-stop-plan-drift`·`early-stop-conclusion` 이 없고 activity 에 이번 `early-stop-wait-shell` 이 없다(낮음, 운영 자산이라 별도 작업).
