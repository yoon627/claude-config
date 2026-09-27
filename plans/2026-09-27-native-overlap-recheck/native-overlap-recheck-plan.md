---
title: native-overlap-recheck — 네이티브 중복 대장 재판정(v2.1.223~283)과 /improve 발견 적립
status: in_progress
started: 2026-09-27
updated: 2026-09-27
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal
`/improve deep`(2026-09-27) 결과를 적립한다: 네이티브 중복 대장 재판정(창 v2.1.223~283), workflow-failures 가산, 새로 찾은 개선 후보를 미착수 단위로 올린다.

# Intent
- 묶음: `plans/2026-09-25-repo-audit-followups/intent.md` 의 native-overlap-recheck 단위.
- 델타: 판정 내용은 사용자가 초안으로 승인했다(2026-09-27 — "초안대로 ingest", 후보 1~4 전부 단위화). 이 단위는 wiki·intent 기록만 바꾸고 hook·스크립트는 고치지 않는다(수정은 새 미착수 단위의 몫).
- 분할: 없음 — 대장 재판정·workflow-failures·hook-notification·두 intent 가 서로를 가리켜(대장 12행 ↔ hook-notification ↔ workflow-failures 라우터 행 ↔ 새 묶음 단위 줄) 일부만 머지하면 참조가 끊긴다.

# Acceptance
1. 대장 `wiki/pages/decision/native-overlap-ledger.md` — frontmatter `checked: 2026-09-27`·`checked_version: 2.1.283`, 창 v2.1.223~283 원문 전수 조회 사실(2,326줄·헤더 50개)과 조회 방법 규칙, 변동 행(1b 미이행·콜아웃 재실측, 2~8 창 내 근거), 신규 행 9~15. 확인: 파일 read + 인용 버전·날짜쌍 전부 npm 게시일 대조(스크립트).
2. `wiki/pages/decision/workflow-failures.md` — 라우터 알림 턴 행(새 경로 2026-09-15~ 14개 세션 130건, 4→134, fixed 유지 + 새 경로 proposed), 중간 턴 오탐 행(+1 → 5, ledger-bash-edits 로 합침). 확인: 파일 read + 전체 transcript·telemetry 대조 스크립트.
3. 감사 묶음 intent `# Plans` — native-overlap-recheck 줄이 이 plan 경로로 바뀌고 ledger-bash-edits 줄 범위에 중간 턴 오탐·종료 조건·순서·`bashEditDiffEnabled` 후보가 들어간다. 새 묶음 `plans/2026-09-27-improve-followups/intent.md` 에 미착수 3줄. 확인: 파일 read.
4. 줄번호로 workflow-failures 행을 가리키는 곳이 없다(행 이름으로만). 확인: `grep -rn '2[89]행\|4[12]행'` 가 이번에 바뀐 wiki·intent 파일에서 0건(이 plan 은 Decisions 에 옛 표기를 인용하므로 제외).
5. README 영향 판정 — 변경 없음(README 에 대장 판정·workflow-failures 수치를 옮겨 적은 곳이 없다; `README.md:422` 라우터 서술 갱신은 router-agent-message 몫). 확인: README grep.
6. `wiki/index.md`·`wiki/log.md` 동기화, `check_links.py wiki` clean, `bash scripts/verify.sh` 마지막 줄 `ALL PASS`, plan-lint rc=0.
7. 추가된 줄과 새 파일에 공개 금지 식별자 없음(스캔 0건, 양성 샘플로 검사식 확인).

# Progress
- 2026-09-27: `/improve deep` 실행(error 0·warn 0), researcher 로 changelog 대조, 초안·후보 승인. worktree 생성(base `origin/main@b4a9f66`). 대장·workflow-failures·hook-notification·intent·index·log 편집, 링크 clean·plan-lint rc=0·공개 스캔 0건·`verify.sh` ALL PASS. 리뷰 2종 병렬(Codex 크레딧 소진으로 생략) — plan-reviewer CONDITIONAL(major 4), code-reviewer REQUEST CHANGES(major 4). 처분: CHANGELOG 원문을 받아 창 전수 재조회(subagent 가 2,326줄 전부 read), telemetry·transcript 로 라우터 오발동 확인(2회차 리뷰 뒤 전체 기준 130건/14세션으로 정정), 새 묶음 intent 생성, 버전·날짜쌍 npm 대조 0 불일치. 인용 문서(worktrees·hooks) 원문 확인. fix loop 2회로 종료. 격리 runner 최종 검증: verify ALL PASS(skip 없음)·check_links clean·plan-lint rc=0·날짜 40쌍 0 불일치·행번호 참조 0·변경 파일 집합 일치 — 메인 판정과 일치, evidence gate DONE.

# Next
커밋 → commit-check → `/e merge`(medium — push·PR·CI).

# Decisions
- 규모 small — 문서만, 판정 내용은 사전 승인. diff 가 커지면 재판정. → medium 으로 재판정(구현 뒤 wiki·intent +70/−14, plan 44줄): plan-reviewer 와 code-reviewer 를 병렬로 돌린다(계획 내용이 구현보다 먼저 사용자 승인을 받아 순서만 바뀜).
- 커밋 단위: 1개 — 한 목적(재판정 결과 적립)이고 파일끼리 서로 가리킨다.
- doc-drift-index 단발 오탐(2026-09-27)을 별도 줄 대신 라우터 알림 턴 행 새 경로의 결과로 적는다 (이유: 라우터는 걷어낸 뒤 텍스트가 남으면 키워드와 무관하게 `ledger.reset` 을 부른다(`scripts/dlc-task-router.js:41-42`). transcript 순서는 index 편집 → compaction(뒤이은 결론 경고로 장부 생존 확인) → 리뷰어 hand-back 턴 → 페이지 재편집 → 경고이고 사이에 사용자 턴이 없다. 그 hand-back 은 키워드가 없어 리셋을 직접 관측하지 못해 ⚠️).
- 범위에 `claude-code-hook-notification-turns` 를 더한다 (이유: 라우터 행이 가리키는 원인 페이지가 hand-back 턴을 모르면 router-agent-message 단위가 태그만 추가하는 불충분한 수정을 할 수 있다 — transcript 51건에서 태그 밖 평문 접두어와 개행을 확인했다).
- 대장 `checked` 를 올린다(사용자 선택 2026-09-27) → 근거를 "키워드 검색 한계를 적고 올림"에서 **원문 전수 조회**로 변경 (이유: 리뷰 두 곳이 대장 규칙("`checked` = 전수 조회일")과의 모순과, 전문을 읽었다던 265~283 구간의 누락(v2.1.271 hand-back·v2.1.280)을 잡았다. WebFetch 대신 GitHub `CHANGELOG.md` 원문을 받아 subagent 가 2,326줄 전부 읽었다). 기각안: 운영 규칙에 "부분 조회로 올릴 때는 미전수 구간을 할 일로 적는다" 예외 추가 — 원문을 받으면 전수가 싸게 되므로 예외를 둘 이유가 없어졌다.
- changelog 1차 출처를 SKILL §6 이 지정한 docs 페이지 대신 GitHub `CHANGELOG.md` 로 (이유: docs 페이지는 WebFetch 에서 v2.1.275 부근에서 잘린다. GitHub 원문은 같은 내용을 버전 헤더로 담고 한 번에 받을 수 있다). 날짜는 원문에 없어 npm 게시 시각(UTC)을 쓴다 — 기존 대장의 v2.1.222 · 2026-08-04 도 UTC 기준이다.
- ⚠️ 새 개선 3개(router-agent-message·claude-md-dedupe·guard-deny-removal)를 감사 묶음이 아니라 새 묶음 `plans/2026-09-27-improve-followups/intent.md` 에 둔다 — 사용자 선택지 문구("intent 에 미착수로 추가")와 감사 묶음 Out of scope("감사에서 나오지 않은 새 개선은 별도 요청") 상충 — Out of scope 를 따른다(이유: 감사 묶음의 Problem 과 무관하고, 넣으면 감사 묶음을 닫는 조건이 그만큼 늦어진다. 사용자 결정의 요지 "셋 다 단위화"는 그대로 지켜진다). 기각안: 감사 묶음 Problem·Out of scope 개정 — 진행 중인 autopull-verified-client 에 영향 통지가 필요하고 묶음 경계가 흐려진다. ledger-bash-edits 범위 확장은 기존 감사 단위라 감사 묶음에 둔다.
- workflow-failures 행은 줄번호가 아니라 행 이름으로 가리킨다 (이유: 이번 diff 가 frontmatter 에 줄을 넣어 "28행·41행" 참조가 한 줄씩 밀렸다 — 표에 `#` 열이 없어 줄번호는 편집마다 어긋난다. 대장은 `#` 열이 있어 "#8" 로 가리킨다).

# Review Disposition
- [plan] major 라우터 오발동 1회로 과소 기록 — fix(telemetry 45건 중 42건이 hand-back 턴 0.1초 이내, transcript hook 주입 41/41 → 4→45).
- [plan][code] major workflow-failures 줄번호 참조가 +1 밀림 — fix(행 이름으로 교체, Acceptance 4).
- [plan] major 새 3단위가 감사 묶음 Out of scope 와 충돌 — fix(새 묶음 intent, Decisions ⚠️).
- [plan][code] major·minor `checked` 가 대장 규칙과 모순 — fix(원문 전수 조회로 해소, 조회 방법 규칙 추가).
- [code] major 대장 12행 "UserPromptSubmit 관련 변경 없음"이 v2.1.271·280 과 어긋남 — fix(12행을 "파손"으로, 같은 계열 v2.1.234·251·277 추가).
- [code] major 접두어 구분자는 공백이 아니라 개행 — fix(hook-notification·workflow-failures·새 intent).
- [code] minor 버전 귀속 오류 3건(`!` 규칙 v2.1.269, `$VAR`·heredoc v2.1.257, OTel repo v2.1.269 만) — fix. 추가로 v2.1.274·v2.1.223 날짜 오류를 npm 대조로 찾아 fix.
- [code] minor 관측 런타임은 2.1.281(설치 2.1.283) — fix(14,931 레코드 전부 2.1.281·permissionMode auto 확인).
- [code] nit sources 날짜 출처 — fix(npm 게시 시각). nit "근거가 바뀐 행" 제목과 1a 누락 — fix. nit `claudeMdExcludes` "창 이전부터" 근거 없음 — fix(changelog 에는 v2.1.239 수정만). nit "223~264" 버전 범위 — 해소(전수 조회, 없는 헤더 목록 명시).
- [plan] minor doc-drift 재해석에 transcript 순서 근거 — fix(workflow-failures·Decisions). minor entity 페이지 접두어 추론 ⚠️·hook stdin 캡처 — fix. minor 대기 턴 부분 종료 조건 — fix(감사 intent). minor guard-deny-removal 착수 조건 재실측·memory 콜아웃 합치기 — fix(새 intent). minor 규모·`분할:` 줄 — fix. minor Acceptance README·행 참조 — fix(5·4). minor 상태 칸 fixed 유지 — fix. minor plan Next·changelog 출처 이유 — fix. minor `wiki/log.md` 끝 추가가 autopull-verified-client 와 충돌 가능 — wontfix(나중에 머지하는 쪽에서 해소, 두 항목 모두 보존하면 된다).
- [plan] 누락 시나리오: router 수정 뒤 대기 턴 오탐이 늘 수 있음 — fix(감사 intent ledger-bash-edits 줄에 기준선 측정).
- [code 2회차] major hand-back 오발동을 한 세션 기준(2026-09-24~·41건)으로만 적음 — fix(전체 transcript 210턴·telemetry 144건 중 130건/14세션, 첫 발생 2026-09-15, v2.1.271 게시 전 0건을 직접 재확인. 4→134, 41/41 은 표본으로만).
- [code 2회차] minor `.worktreeinclude` 는 Claude Code 가 만드는 worktree 에만 적용 — fix(worktrees 문서 원문 확인, 대장 4행에 전제·"request §3 4단계"). nit 12행 "이것뿐" 이 8행과 어긋남 — fix. nit `bashEditDiffEnabled` 는 "모든 모드에 켜는 설정"·PostToolUse `tool_response.bashEditDiff` — fix(hooks 문서 원문 확인, 대장 6행·감사 intent). nit Acceptance 4 grep 이 plan 자신에 걸림 — fix(범위에서 plan 제외). nit WebFetch 경위 서술 앞뒤 — fix. nit claude-md-dedupe 함정 1 은 일반 패턴일 때만 — fix.
- fix loop 2회 상한 도달 — 남은 finding 없음.

# Deferred
- (낮음) 대장 45일 주기의 근거("6주 36릴리스")가 이번 창(51일·헤더 50개)에서 깨졌다. 원문을 로컬로 읽으면 창이 길어도 싸게 전수할 수 있어 주기 자체를 늘릴지 검토 — `wiki/pages/decision/native-overlap-ledger.md` 운영 규칙, `README.md:350`.
- (중간) `skills/improve/SKILL.md` §6 2단계가 docs changelog 페이지(WebFetch 로 잘림)를 1차 출처로 적는다 — 대장 운영 규칙("GitHub `CHANGELOG.md` 원문을 받아 로컬에서 끝까지 읽는다")과 맞추는 개정 제안. 운영 자산이라 승인 후 별도 작업.
- (낮음) worktree 의 `.claude/settings.local.json` 에 allow 91개, main 에 54개(code-reviewer 2회차 관측). 네이티브는 권한 승인을 main checkout 쪽 파일에 저장한다고 문서화돼 있는데 repo root 가 설정 디렉토리인 이 구조에서는 아닌 듯하다 — `/wt` 의 settings.local 복사가 여전히 필요한지와 함께 claude-md-dedupe 또는 별도 점검에서 본다.
- (중간) 2026-09-24~26 early-stop 오탐 분류(Bash 편집 17회·대기 턴 4회)에 hand-back 턴 장부 리셋이 섞였을 수 있다 — ledger-bash-edits 착수 때 router 수정 뒤 기준선과 비교.

# Key Files
- `wiki/pages/decision/native-overlap-ledger.md` — 재판정 대장
- `wiki/pages/decision/workflow-failures.md` — 라우터 알림 턴 행·중간 턴 오탐 행
- `wiki/pages/entity/claude-code-hook-notification-turns.md` — subagent 보고 턴의 raw 형태 관측
- `plans/2026-09-25-repo-audit-followups/intent.md` — 감사 묶음 `# Plans`
- `plans/2026-09-27-improve-followups/intent.md` — 새 묶음(미착수 3단위)
- `wiki/index.md`, `wiki/log.md`

# Blockers
없음
