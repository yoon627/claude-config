---
title: statusline-drop-codex — statusline 에서 codex 사용량·리셋 시각 표시 제거
status: done
started: 2026-09-30
updated: 2026-10-01
---

# Goal
메인 statusline 에서 codex 조각(`<codex 모델명> NN%(HH:MM) wk NN%`)을 없애고, 그 조각만을 위해 있던 백그라운드 refresh(`codex-quota-refresh.js`)와 관련 테스트·문서를 함께 정리한다.

# Intent
- Problem: 사용자가 statusline 에 codex 사용량/시간을 보여줄 필요가 없다고 판단했다(2026-09-30 요청). 지금은 2초 refresh 마다 캐시를 읽고, 캐시가 5분 넘으면 `codex app-server` 를 띄우는 helper 를 spawn 한다.
- Constraints: Claude 조각(`<모델> NN%(HH:MM) wk NN%`)·`ctx`·branch 조각의 동작은 그대로. statusline 은 어떤 입력에도 exit 0 을 유지.
- Out of scope: Codex CLI 자체의 리뷰 병행(§9·`docs/codex-review.md`) — statusline 과 무관, 손대지 않는다. 각 머신의 gitignored 런타임 파일 `~/.claude/cache/codex-quota.*`(json·lock·json.tmp.<pid> — 이 머신에 tmp 도 실제로 남아 있다)은 지우지 않는다(추적 대상이 아니고 남아도 읽는 코드가 없다 — Report 에 "`cache/codex-quota.*` 만 지우고 `cache/` 디렉토리는 지우지 말 것(Claude Code 자체 캐시 공존)" 안내만). 과거 plan(`plans/2026-06-11-*`, `2026-09-25-*`)의 codex-quota 언급은 기록이라 고치지 않는다.
- refresh 스크립트·테스트 삭제: 처음엔 ⚠️ 추론이었고 2026-09-30 plan 승인에서 사용자가 "표시 제거 + 스크립트 삭제"를 택해 확정(기각된 선택지: 표시만 제거). 추론 근거 — 호출자가 statusline 1b 블록 하나뿐이라 표시를 없애면 죽은 코드가 되고, §6 은 죽은 코드를 삭제하라고 한다. 호출자 부재 근거의 범위: 추적 파일 전체·이 머신 `settings.json`·`~/.claude/skills`·`commands`·`~/.codex`(plan-reviewer 확인). 다른 머신의 개인 예약작업 등은 ❌모름. 되돌리기는 `git revert` 또는 `git show 62ddfcf:codex-quota-refresh.js`.
- 분할: 없음 — 표시 제거와 refresh 삭제를 나누면 첫 머지 뒤에 호출자 없는 스크립트와 그것을 "statusline 이 spawn 한다"고 설명하는 README 가 남는다. 한 머지에서만 문서와 코드가 맞는다.

# Acceptance
1. codex 캐시가 있어도 codex 조각을 그리지 않고 refresh 를 spawn 하지 않는다 — `node scripts/statusline.test.js` 의 새 테스트(stale codex 캐시를 둔 별도 가짜 HOME 에서 `{}` 입력 → 출력 `''`, cache 디렉토리에 캐시 파일 하나만 있고 lock 이 없음). 통과 기준: base 코드에서 Red(출력에 `codex 80%(20:30) wk 21%`, lock 생성), 변경 후 Green. lock 부재가 "spawn 안 함"의 증거가 되는 전제: base statusline 은 spawn 직전에 lock 을 동기 기록하고, 가짜 HOME 에는 helper 가 없어 lock 을 지울 주체가 없다.
2. Claude·ctx·branch 조각 불변 — (a) codex 테스트를 뺀 기존 statusline 테스트 전부 통과. (b) 실제 실행: `printf '%s' '{"model":{"display_name":"Opus"},"rate_limits":{"five_hour":{"used_percentage":47.4,"resets_at":1767299400},"seven_day":{"used_percentage":28}},"context_window":{"used_percentage":12},"workspace":{"current_dir":"<worktree 절대경로>"}}' | TZ=UTC node statusline.js` → `Opus 53%(20:30) wk 72% | ctx 12% | statusline-drop-codex @wt:statusline-drop-codex`. **실제 HOME**(이 머신 `~/.claude/cache/codex-quota.json` 존재)으로 변경 코드를 돌리므로 codex 조각 부재와 `cache/codex-quota.lock` 미생성도 함께 관찰한다. base 코드는 실제 HOME 으로 돌리지 않는다(실제 `codex app-server` 가 뜬다).
3. 잔존 참조 0 — `git grep -n -E "codex-quota|readCodexModel|codexWindow|CDX_" -- ':!plans/' ':!scripts/statusline.test.js'` 0건, `scripts/statusline.test.js` 에는 새 테스트 fixture 의 `codex-quota` 만 남음(파일명을 문자열 연결로 쪼개 grep 을 피하지 않는다). `codex-quota-refresh.js`·`scripts/codex-quota-refresh.test.js` 삭제, `.gitignore` 의 `!/codex-quota-refresh.js` 제거.
4. README 동기화 — Key Files 의 README 13곳 목록을 한 줄씩 읽어 대조 + `git grep -n -i -E "codex quota|codex NN%|codex-quota|gpt-5\.4|config\.toml|Codex CLI, git" README.md` 0건. Verify 절 번호는 1~4 로 연속.
5. 전체 검증 — `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 이 붙으면 그 축은 미검증으로 따로 적는다).

# Progress
- 2026-09-30: `/wt` 로 worktree 생성(base main@62ddfcf) → dlc medium. Explore — codex 참조는 `statusline.js` 1b 블록·`readCodexModel`·`codexWindow`, `codex-quota-refresh.js`(+test), `scripts/statusline.test.js`, README 13곳, `.gitignore` 1줄. settings.json 에 codex-quota 참조 없음. plan-reviewer(+Codex) CONDITIONAL → 지적 반영(# Review Disposition). 사용자 plan 승인(스크립트 삭제 포함). TDD Red 확인(base: 출력 `codex 80%(20:30) wk 21%`, scratch 로 lock 생성도 확인) → 구현(statusline.js 1b 블록·helper·`fs`/`os` 제거, refresh+test `git rm`, `.gitignore`, README 13곳) → Green(`statusline.test.js: 6 tests passed`). A2 실제 HOME 실행: `Opus 53%(20:30) wk 72% | ctx 12% | statusline-drop-codex @wt:statusline-drop-codex`, codex 조각 없음·lock 없음 — 단 실제 캐시가 4.6분(fresh)이라 base 도 spawn 하지 않았을 시점이고, main 의 옛 statusline 이 같은 캐시를 계속 갱신해 실제 HOME 에서 spawn 여부는 떼어 관찰할 수 없다 → spawn 부재 증거는 A1 테스트(stale 캐시 → lock 미생성)와 코드상 spawn 호출 0.

- 2026-09-30: code-reviewer(+Codex) APPROVE → README 2곳·plan 표기 fix. simplify: `quotaPiece`·`windowPiece` 는 호출처 1개지만 이름 붙은 포맷 함수라 유지(동작 변경 없음). 격리 runner 의 `verify.sh` 는 syntax 34·node 17 전부 ok 뒤 bash 축 `scripts/pre-commit-check.test.sh` 에서 10분+ 제한에 걸려 중단(`ALL PASS` 없음). 조사: 단독 `timeout 150` 도 rc 124·출력 없음. 그러나 runner 종료 뒤에도 그 verify.sh 프로세스가 45분 넘게 살아 새 guard 자식을 계속 만들고 있었다 → 교착이 아니라 느린 진행으로 보인다(⚠️ 추정 — 완주 전). 이 세션이 남긴 프로세스만 정리(다른 세션 테스트는 손대지 않음). guard·테스트·verify.sh 는 base 62ddfcf 와 동일(`git diff --stat HEAD` 빈 출력). 전체 verify.sh 를 백그라운드 2시간 제한으로 재실행 중(로그 `<scratch>/verify-full.log`).

- 2026-09-30: 백그라운드 `bash scripts/verify.sh` 완주(약 50분) — `pre-commit-check.test.sh` ok(교착 아님, 느린 진행 확정), syntax·node·bash·ps1·shellcheck 전부 ok, `record-verified.test.sh` `[skip]`(jq 미설치), `FAILED: 2` = `skills/wiki/test_wiki_check.py`(fail 2·error 2)·`test_wiki_search.py`(fail 1). base 재현: main checkout(62ddfcf, clean, `skills/wiki` 동일)에서 두 테스트를 돌려 **같은 테스트 이름**이 실패(worktree 도 이름 단위 대조 일치, skip 수만 14/13) → 입증된 baseline failure 로 # Deferred. evidence gate: A1 Red→Green ✅, A2 (a)(b) ✅, A3·A4 grep 0·13곳 대조 ✅, A5 = baseline 2건 제외 통과·`record-verified` 축은 로컬 미검증(jq, 파일 무변경) — 판정 DONE.

- 2026-10-01: 정식 커밋 → commit-check 이상 없음 → `/e merge`: origin/main 이 23커밋 앞섰으나 trial merge 깨끗(README 만 겹침, 무관한 줄)·병합 tree 잔존 참조 0 → push → PR #227 → done.
- 2026-10-01: 정정 — # Workflow Findings·# Deferred 의 `timeout` 서술이 틀렸음을 재현으로 확인하고 고쳤다(남은 프로세스의 원인은 Bash 도구 중단).

# Next

# Decisions
- wiki decision 조회: `lesson-verify-scaffold-purpose-before-removal` 이 걸렸다 — 따른다. 이 제거는 사용자 지시이고, refresh 스크립트의 도입 목적은 statusline codex 조각에 캐시를 채우는 것 하나뿐(스크립트 헤더 "Designed to be invoked detached from statusline.js", `git grep` 상 다른 호출자 없음, `docs/codex-review.md` 의 리뷰 호출은 `codex exec` 경로로 무관)이라 표시를 없애면 목적이 함께 사라진다.
- refresh 스크립트·테스트는 삭제한다(2026-09-30 사용자 plan 승인으로 확정 — # Intent). 기각: (a) 스크립트만 남기기 — 호출자 없는 죽은 코드. (b) env 토글로 숨기기 — 요청하지 않은 옵션이 늘고, 다시 켜려면 `git revert` 로 충분하다.
- `statusline.js` 에서 `fs`·`os` import 도 함께 뺀다 — codex 코드만 쓰던 것.
- `scripts/statusline.test.js` 의 전역 가짜 HOME 은 실행을 실제 홈과 격리하는 용도로 남기되 전역 codex 캐시 쓰기는 지우고 헤더 주석을 그 용도로 고친다. codex 쿼터 테스트는 "codex 캐시를 무시한다" 테스트 1개로 바꾼다(별도 HOME 을 쓰므로 `runStatus` 의 `home` 인자는 계속 쓰인다).
- spawn 을 직접 가로채 기록하는 테스트(Codex 제안)는 기각 — 서브프로세스에 `--require` preload 가 필요해 §7 "덤을 늘리지 않는다"에 어긋나고, lock 부재로 결정적으로 판정된다(# Acceptance 1 전제).
- 커밋 단위: 1개 — 목적이 하나(codex 표시 제거와 그에 딸린 죽은 코드·문서 정리).

# Key Files
- `statusline.js` — 1b 블록·`readCodexModel`·`codexWindow`·`fs`/`os` import 제거
- `scripts/statusline.test.js` — codex 테스트 교체, 전역 codex 캐시 fixture 제거
- `codex-quota-refresh.js`, `scripts/codex-quota-refresh.test.js` — 삭제
- `.gitignore` — `!/codex-quota-refresh.js` 제거
- `README.md` — 13곳: 15(Node 전제의 helper 이름), 18(Codex CLI 선택 의존 → 리뷰 병행 용도), 237(codex 레이블 설명), 239(예시 출력의 codex 조각), 249-252(Verify 3 삭제 → 4·5 를 3·4 로), 294(Codex rate limit 항목), 298(외부 의존 → git 만), 306-316(refresh 컴포넌트 절), 584-585(Codex CLI 없는 머신 → 리뷰 병행 기준으로), 660(OS 목록), 679(Layout), 779-783(Troubleshooting "Codex quota 미표시")

# Review Disposition
- plan-reviewer(+Codex) 1회차 CONDITIONAL:
  - [높음] Acceptance 1·3 모순(새 fixture 가 grep 에 걸림) — fix: A3 pathspec 에서 plans/·statusline.test.js 제외, 테스트 파일 잔존은 별도 확인.
  - [높음] README 9곳 → 13곳, grep 이 237·239·298·584 헤더를 못 잡음 — fix: Key Files 목록화, A4 를 목록 대조 + grep 확장, Verify 재번호.
  - [중간] A2 재현성(TZ·display_name·입력 JSON) — fix: 명령 명시, 실제 HOME 관찰 추가(base 는 실제 HOME 금지).
  - [낮음] 정리 안내에 `codex-quota.json.tmp.*` 누락·`cache/` 삭제 금지 — fix: # Intent Out of scope.
  - [낮음] 테스트 헤더 주석·`home` 인자 — fix: 주석 교정, `home` 은 새 테스트가 써서 유지.
  - [낮음] 공용 wiki `native-overlap-ledger` 15행 stale — defer: # Deferred.
  - [낮음] 로컬 settings.local.json stale allow — defer: # Deferred.
  - [선택] spawn 가로채기 테스트(Codex) — wontfix: # Decisions 기각 사유.
  - ⚠️ self-flag(refresh 삭제 추론) — accepted-risk: 호출자 부재를 범위 한정으로 확인, 사용자 plan 승인 요약에 삭제를 명시해 합의.
- (simplify 참고) 제거 후 `quotaPiece`·`windowPiece` 호출처가 Claude 조각 하나 — 13단계에서 판단.
- code-reviewer(+Codex high) 1회차 APPROVE (Critical·Major 0):
  - [Minor] ctx 에 object 입력이면 `Math.round` 에서 throw → rc 1(base 부터 있던 결함, 재현 확인) — defer: # Deferred.
  - [Minor] README Codex CLI 용도가 plan/code-reviewer 만 적음(architecture-reviewer 도 병행) — fix: "reviewer subagent … (§9)".
  - [Minor] README 에 제거 기록·`cache/codex-quota.*` 정리 안내 한 줄(bg 제거 관례) — wontfix: 그 줄이 A3·A4 잔존 참조 grep 에 걸려 acceptance 를 다시 바꿔야 하고, 남은 파일은 무해하다. 정리 안내는 커밋 메시지 본문(다른 머신도 `git log` 로 본다)과 Report 에 담는다.
  - [Nit] README 288 레이블 `claude` → 모델명(폴백 `claude`) — fix.
  - [Nit] README 642 OS 목록 괄호의 os API — wontfix: 여러 파일을 묶은 설명이라 여전히 참.
  - [Nit] 새 테스트가 머지 뒤엔 "없는 기능 부재" 확인 — wontfix: 부분 revert 로 1b 블록이 되살아나는 것을 막는다(# Decisions).
  - [Nit] # Decisions 의 "⚠️ 추론" 표기 — fix.

# Workflow Findings
- 격리 runner 가 `bash scripts/verify.sh` 를 도구 시간 제한(foreground 600s → background)으로 "killed" 보고했지만, Git Bash(MSYS) 자식 프로세스(verify.sh·pre-commit-check.test.sh·guard)는 45분 넘게 살아 있었다. Bash 도구의 중단(시간 제한·TaskStop)이 Git Bash 자식을 끝내지 않기 때문이다(2026-10-01 재현 — TaskStop 뒤 `sleep.exe` 잔존). GNU `timeout` 은 자손까지 끝냈다(같은 날 재현). 처음 적었던 "`timeout 150` 도 손자 프로세스를 죽이지 못했다" 는 틀렸다 — 그때 남아 있던 같은 명령줄의 bash 는 runner 의 verify.sh 트리였다. 시간 제한으로 끝난 검증 뒤에는 `Win32_Process` 에서 남은 프로세스를 확인·정리해야 한다(다른 세션 프로세스와 구분 필수). 1회 — 반복되면 dlc runner 계약(`docs/dlc-details.md` §E)에 정리 단계를 넣는 제안.

# Blockers

# Deferred
- (low) 공용 wiki `entity/claude-code-statusline-input` "Codex rate limit 창" 절의 "그래서 창은 `windowDurationMins` 로 고르고…" 와 `decision/native-overlap-ledger` 15행(`statusline.js`(Claude·Codex 사용량 표시), keep 근거 "Codex 사용량은 네이티브에 없다")이 이 repo statusline 의 옛 동작을 설명한다 — 머지 뒤 `~/.claude` main 세션에서 "2026-09-30 statusline 의 codex 표시 제거" 로 갱신한다(외부 사실 부분은 유효하므로 유지).
- (medium) Windows 로컬 `bash scripts/verify.sh` 가 base(62ddfcf)부터 `FAILED: 2` — `skills/wiki/test_wiki_check.py` 의 `test_closed_stdout_exits_2_without_traceback`(flush 가 EPIPE 대신 `OSError: [Errno 22]`), `test_case_mismatched_wiki_argument_is_refused`(대소문자 무시 파일시스템에서 거부 안 됨), `StopHookTest.test_oversized_stdin_gives_system_message`·`test_stdin_without_eof_ends_within_3_seconds`(error), `skills/wiki/test_wiki_search.py` 의 `test_unreadable_index_exit_2`(stderr 에 경로가 repr 이스케이프로 찍힘). CI 는 ubuntu 뿐이라 드러나지 않는다. 이번 변경과 무관(파일 동일, base 재현).
- (low) Windows 에서 `scripts/pre-commit-check.test.sh` 가 수십 분 걸린다(이번 실행에서 전체 verify.sh 약 50분의 대부분) — 격리 runner 의 도구 시간 제한(600s)을 넘는다. `record-verified.test.sh` 는 jq 미설치로 로컬 skip.
- (low) `statusline.js` ctx 조각 — `context_window.used_percentage` 가 object 면 `Math.round` 에서 throw 해 rc 1·빈 출력, 문자열이면 `ctx NaN%`(base 부터 있던 결함, 이번 변경과 무관). 고칠 때는 `num()` 으로 거르고 `scripts/statusline.test.js` 의 깨진 입력 목록에 케이스 추가.
- (low) `/wiki ingest` 후보 → 2026-10-01 main 세션에서 적립(공용 wiki `entity/windows-bash-tool-orphan-processes`) · 요약: Windows 에서 Claude Code Bash 도구의 중단(시간 제한·TaskStop)은 Git Bash 자식 프로세스를 끝내지 않아 검증 스크립트가 계속 돈다(GNU `timeout` 은 자손까지 끝낸다) — 중단 뒤 `Win32_Process` 로 남은 프로세스를 확인한다 · 근거: 2026-10-01 재현(TaskStop 뒤 `sleep.exe` 잔존, `timeout` 뒤 잔존 없음) · 출처: 공개.
- (low) main checkout 과 이 worktree 의 `.claude/settings.local.json` 에 `Bash(node --check codex-quota-refresh.js)` 류 allow 가 남는다 — gitignored 로컬 상태라 이 브랜치 범위 밖, 동작에 해 없음. main 세션에서 정리 가능.
