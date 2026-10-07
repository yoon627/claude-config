---
title: verify-speed — 로컬 검증을 바뀐 축만(verify.sh changed)으로, 테스트별 소요 시간 출력, 전체는 CI·사용자 주기 실행
status: done
started: 2026-10-07
updated: 2026-10-07
---

# Goal
Windows 에서 약 50분 걸리는 전체 `verify.sh` 를 작업마다 돌리지 않는다. 로컬 최종 검증은 바뀐 파일로 축을 고르는 `verify.sh changed`, 전체는 push 시 CI(GitHub, Linux 4~5분)와 사용자의 주기 실행이 맡는다. 테스트별 소요 시간을 출력해 느린 테스트를 찾을 수 있게 한다.

# Intent
- Problem: 2026-10-07 결론 형식 작업에서 형식 확정 전에 전체 verify 를 시작해 50분×2 를 썼고, 사용자가 "너무 오래 걸린다"고 지적했다. docs-untrack 에서 사용자 승인으로 바뀐 축만 돌려 몇 분에 끝낸 첫 사례가 있다.
- Constraints (사용자 확인 2026-10-07): 로컬은 항상 바뀐 것만 검증, 전체 로컬 verify 는 사용자가 주기적으로 직접 실행. CI(`.github/workflows/lint.yml`, push·PR 시 전 축)는 전체 유지 — push 속도와 무관하고 로컬이 안 보는 축의 안전망. 검증은 변경 확정 후 1회(작업 중엔 관련 테스트만).
- Out of scope: 느린 테스트 자체의 최적화(측정 결과를 보고 별도), CI 워크플로 변경, 병렬 실행(Windows 시간 한도 테스트가 간헐 실패 — wiki `lesson-serialize-windows-verification`).
- 분할: 없음 — `changed` 축·소요 시간 출력·dlc/CLAUDE.md 규칙이 같은 `verify.sh` 와 "최종 검증" 정의를 함께 바꿔, 규칙만 먼저 머지되면 없는 명령을 가리킨다.

# Progress
- 2026-10-07: worktree 생성(base origin/main@33d9566), Explore — verify.sh 축 구조, lint.yml 은 main push·main 대상 PR 에 전 축. (정정: 처음엔 "테스트는 실제 문서가 아니라 임시 fixture 를 읽는다"고 판단했으나 좁은 Grep 무매칭에 기댄 결론이었고 code-reviewer 가 반증 — 다른 언어 테스트가 실제 repo 파일을 읽는 교차 의존 7곳.) 사용자 결정 2건(로컬 changed·전체는 사용자, CI 전체 유지).
- 2026-10-07 (cont.): TDD — `verify-changed.test.sh` Red(모르는 축 `changed` 를 받은 기존 verify.sh 가 아무것도 안 돌고 `ALL PASS` — 기존 결함 발견) → 구현(`changed` 축·축 선택·모르는 축 FAIL·`(Ns)`·총 시간) → Green(12 케이스). 실제 `verify.sh changed` 는 verify.sh 자체가 바뀌어 규칙대로 전 축 — 백그라운드 실행 중, 첫 소요 시간 측정 겸용(지금까지 session-brief 179s·install-hooks 98s·session-fetch 88s·native-overlap-lint 67s). dlc 최종 검증 정의·CLAUDE.md §1·README 갱신.

- 2026-10-07 (final): 사용자가 "여전히 너무 오래 걸린다" → 원인 분석(subagent 단독 실측: 프로세스 생성 비용 × 대량 git·bash 호출, 의도적 대기 아님) → 느린 테스트 로컬 기본 제외(임시책) 추가, 근본 개선 3건은 `# Deferred`. 최종 `verify.sh changed`(전 축 선택 + 느린 테스트 9개 제외) 171초 `ALL PASS (skip: record-verified.test.sh)`(jq 환경 skip). 규칙 문구 3곳 사용자 diff 확인. 판정 DONE.

# Next
(없음 — 로컬 ff·push 후 CI 성공이 Acceptance 2 의 node·python 축 확인. 후속은 `# Deferred` 의 느린 테스트 근본 개선.)

# Decisions
- 선행 decision: 공용 wiki `lesson-serialize-windows-verification`(전체 verify 는 리뷰 뒤 단독) — **따른다**(전체 실행 시에 그대로 적용). 병렬화는 이 교훈 때문에 범위 밖.
- 축 선택 규칙(바뀐 파일 = `git merge-base HEAD origin/<default>` 이후 커밋 + 작업트리 + untracked, `--no-renames`·quotePath 끔): `.js` → syntax·node / `.sh`·`.ps1` → bash·shell·node / `.py`·`.toml` → python / `agents/*.md` → syntax·python / `skills/*/SKILL.md` → syntax·bash / `scripts/verify.sh`·`.github/**`·`.gitattributes`·`.gitignore`·`.editorconfig`·기준 못 찾음 → 전 축 / 그 밖 → syntax(빈 선택으로 통과처럼 보이지 않게). 처음엔 확장자만으로 골랐으나(".sh → bash·shell" 등) code-reviewer 가 다른 언어 테스트가 실제 repo 파일을 읽는 교차 의존 7곳을 찾아 넓혔다(ps1-encoding·install-hooks·session-start-pull·native-overlap-lint → node, test_sync_codex_agents·test_wiki_check → python, install-codex-skill → bash). 기각: 바뀐 파일을 참조하는 테스트를 내용 검색으로 고르는 동적 방식 — 문자열 참조만 잡고 간접 의존은 놓쳐 확장자 표와 같은 빈틈이 생기고, 판정이 불투명하다.
- 소요 시간은 테스트 줄 끝 `(Ns)` + 마지막 요약 앞 총 시간. `date +%s` 초 단위(POSIX sh).
- 축 선택을 테스트하려고 `VERIFY_PRINT_AXES=1` 이면 고른 축만 출력하고 끝낸다, `VERIFY_CHANGED_FILES` 로 바뀐 파일 목록을 주입한다(git 상태와 무관한 결정적 테스트).
- 이 브랜치의 최종 검증: verify.sh 자체가 바뀌어 규칙상 전 축이지만, 사용자 승인(2026-10-07)으로 로컬은 syntax·shell·bash 축(verify-changed.test.sh 포함), node·python 축의 테스트 발견은 push 후 CI(Linux, 전 축)가 확인. 측정용 전 축 실행은 리뷰 수정으로 스크립트가 바뀌어 중단(결과 무효, 소요 시간만 참고).
- 느린 테스트 로컬 기본 제외(사용자 선택 2026-10-07 "임시책 먼저 + 근본 후속"): `changed` 에서 단독 실측 30초+ 테스트 9개(아래 7개 + python 축의 test_commit_units.py 243초·test_wiki_check.py 97초 — 첫 changed 실행에서 발견)를 건너뛰되, 그 테스트나 검사 대상 스크립트가 바뀌면 돌린다(대상 표는 verify.sh `SLOW_TESTS`). `VERIFY_SLOW=1` 이면 포함, CI·전 축은 항상 전부. 근거 실측(단독, 초): pre-commit-check 30~50분+(600초에 117 중 87), session-brief 306, session-start-pull 275, ci-secret-scan 97, install-hooks 84, session-fetch 66, native-overlap-lint 36. 원인은 의도적 대기가 아니라 프로세스 생성 비용(git 651ms·bash 857ms·node 638ms·`cmd /c exit` 191ms, Defender 실시간 보호 켜짐 ⚠️ 관련 추정) × 테스트당 git 약 1,000회·가드 1회당 프로세스 약 100개. 기각: Defender 예외(git·bash 프로세스 예외는 그 프로세스의 모든 파일 검사를 끄고, %TEMP% 예외도 위험 — 효과 미측정), PS5.1 엔진 테스트를 영구 제외(Linux CI 가 대신 못 봄 — 사용자 주기 전 축이 맡는다).
- 모르는 축 이름은 FAIL 로(범위 확장 — 같은 case 문에서 `changed` 를 받으며 드러난 결함이고, 고치지 않으면 오타 축이 검증 없이 통과로 보인다).
- 커밋 단위: 1개 — 명령과 그것을 가리키는 규칙이 한 머지에서만 유효.

# Key Files
- `scripts/verify.sh` — `changed` 축, 소요 시간.
- `scripts/verify-changed.test.sh` — 축 선택 테스트(bash 축이 자동 발견).
- `skills/dlc/SKILL.md` — 최종 검증 정의(확정 후 1회·`verify.sh changed`), 16단계 커밋 규칙에 규칙 문구 diff 확인(Workflow Findings 조치).
- `CLAUDE.md` §1 — `~/.claude` 검증 명령 안내.
- `README.md` — verify.sh 설명.

# Acceptance
1. `VERIFY_PRINT_AXES=1 VERIFY_CHANGED_FILES=<목록> bash scripts/verify.sh changed` 가 규칙대로 축을 고른다 — 새 테스트 `scripts/verify-changed.test.sh` 통과(js·md·SKILL·sh·ps1·py·verify.sh·빈 목록).
2. 실제 실행: `bash scripts/verify.sh changed` 가 `ALL PASS`(허용된 환경 skip 만), 각 테스트 줄에 `(Ns)`·`[slow]` 줄과 총 시간이 찍힌다(관찰 — 171초). 제외된 느린 테스트는 push 후 CI 성공으로 확인(사용자 승인 2026-10-07 — `# Decisions`).
5. 느린 테스트 제외: 무관한 변경이면 9개 제외, 그 테스트·대상이 바뀌면 유지, `VERIFY_SLOW=1` 이면 제외 없음 — `verify-changed.test.sh` 케이스.
3. dlc·CLAUDE.md·README 가 "로컬 최종 = `verify.sh changed` 1회(확정 후), 전체 = 사용자 주기 실행·CI" 로 일치 — 옛 "전체 스위트" 서술 rg 무매칭.
4. 축 지정 기존 동작(`verify.sh syntax` 등) 불변 — `bash scripts/verify.sh syntax`·`shell` ALL PASS.

# Blockers
(없음)

# Deferred
- 느린 테스트 근본 개선(사용자 선택 2026-10-07, 이 순서로 별도 worktree):
  1. 시크릿 가드 `scripts/pre-commit-check.sh`(+`.ps1`) 빠른 경로 — `scan_tokens` 를 `grep -Eq -e p1 … -e p14` 1회로 먼저 보고 걸릴 때만 패턴별 루프, ref 줄별 `rev-parse` 를 `git cat-file --batch-check` 1회로. 실제 push 의 가드도 빨라진다. 보안 가드라 판정 불변 증명 필요. 대상 테스트 pre-commit-check·ci-secret-scan.
  2. fixture 재사용 — session-start-pull·session-brief·session-fetch 의 케이스별 `git init`/clone 을 템플릿 1회 생성 + `fs.cpSync` 복사로, `git config` 호출을 `GIT_AUTHOR_*`·`GIT_CONFIG_COUNT` env 로. 예상 150~250초 절감(⚠️ 추정).
  3. native-overlap-lint.test.js — 점검 번호 확인을 위해 `improve.sh deep` 전체 실행(35초) 대신 헤더만 확인.
  4. (낮음) 워치독·post-checkout 폴링 루프의 1회당 프로세스 수.

# Review Disposition
- code-reviewer(+Codex high, REQUEST CHANGES, 테스트 실행 없이):
  - Major 확장자 기반 축 선택이 교차 의존 테스트 7곳을 놓침 → fix(선택표 확장 + `verify-changed.test.sh` 케이스로 잠금, Progress 전제 정정).
  - Minor 기준 못 찾으면 무경고 HEAD 기준 → fix(BASE_UNKNOWN → 전 축 + 안내 줄, 파일 수 출력).
  - Minor quotePath 로 비ASCII 경로 오분류 → fix(`-c core.quotePath=off`).
  - Minor rename 은 새 경로만 → fix(`--no-renames`).
  - Minor `VERIFY_PRINT_AXES` 가 다른 축에 샘 → fix(changed 축에서만 읽음).
  - Minor README "CI push·PR 마다" 부정확 → fix("main 대상 PR·main push").
  - Minor 테스트가 문자열 매핑만 → fix(실제 git 임시 repo: 커밋·rename·untracked·기준 없음, 모르는 축 exit 1).
  - Minor 루트 설정 파일 → fix(전 축).
  - Nit "index" 서술 → fix(README 에서 뺌).
  - Open `improve.sh --ci` 가 verify 축에 없음 → defer(이번 변경 전부터의 범위 — README 에 "CI 에서만" 명시).
- code-reviewer 2회차(codex 외부, APPROVE — 테스트 38개 교차 의존 전수 대조, 새 누락 0):
  - Minor untracked 케이스가 아무것도 잠그지 않음 → fix(untracked 를 비ASCII `한.sh` 로 — untracked 수집·quotePath 둘 다 잠금, 기대값 전 축).
  - Minor dlc 16 새 문장이 "순서를 바꾸면" 의 지시 대상을 끊음 → fix(문장 뒤로 이동).
  - Minor dlc 와 §8 확인 조건 불일치 → fix(실제 세션 관찰도 갈음한다고 명시).
  - Nit verify.sh 주석 "index" → fix. Nit BASE_UNKNOWN 이 "1개" 로 찍힘 → fix(별도 문구). Nit README ".editorconfig 는 git 설정 아님" → fix("루트 설정 파일").

# Workflow Findings
- 2026-10-07: 축 선택 설계를 "테스트는 fixture 만 읽는다"는 좁은 Grep 무매칭 결론에 기댔다 — memory `lesson-grep-absence-not-proof`(무매칭은 부재 근거가 아님)와 같은 실수의 재발. code-reviewer 가 잡음.
- 2026-10-07: §8 "규칙·스킬 문구 변경은 사용자 diff 확인 후 커밋"(dcec070)을 만든 직후 `c2ad1fd`(audit 반영)·`52db0af`(docs 이전)를 diff 확인 없이 커밋·push — you-should-know 플러그인이 짚음. 사후 확인(사용자 2026-10-07, 두 커밋 모두 확인). 원인: dlc 16단계 커밋 절차에 그 확인 단계가 없어 §8 문장만으로는 커밋 직전에 떠오르지 않았다. 조치: dlc 16 커밋 규칙에 "규칙·스킬·agent 문구 변경은 커밋 전 사용자 diff 확인(단위 커밋·fixup 포함, 방향 승인 ≠ 문구 확인)" 추가(사용자 승인 2026-10-07, 이 브랜치). 공용 wiki workflow-failures 기록은 main 세션에서.
