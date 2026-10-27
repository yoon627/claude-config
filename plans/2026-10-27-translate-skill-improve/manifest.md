# skills/improve 규칙 목록 (translate-skill-improve)

origin/main c6b0076 의 `skills/improve/SKILL.md`(81줄) 기준. 한 줄 = 한 조항(한정어도 조항의 일부). 번역 대조는 `locations-en.txt`(`<id> | <영어 인용>`, 인용 여러 개는 ` ‖ `, `⏎` 는 줄바꿈, 각 인용은 파일 안에서 한 번, manifest 순서대로). 이 manifest 는 번역 초안 전에 만든다.

## frontmatter
- F.1 description: dlc 자기개선 loop 의 분석 축 — 운영 자산 정합성 기계 점검과 hook 이 자동 누적한 workflow 실패 신호(telemetry)·wiki workflow-failures·feedback memory 를 함께 읽어 개선 후보를 근거·빈도 기반으로 랭킹 제시하는 오케스트레이션
- F.2 description: `deep` 에서는 Claude Code 네이티브가 흡수한 기능과 자작 하네스의 중복을 주기(45일) 재판정하는 축도 돈다
- F.3 description: 발견은 보고·제안까지, 수정은 사용자 승인 후 wt→dlc(운영 자산 자가수정 금지 §1 — 자동 수정 안 함)
- F.4 description: `/improve` 명시 호출 시 사용, 단순 질문·코드 변경에는 쓰지 않는다

## 머리말
- P.1 `/improve` 로 1) 운영 자산 정합성(구 `/audit` 승계)과 2) hook 이 자동 누적한 신호(telemetry)를 함께 분석해 개선 후보를 랭킹으로 제시
- P.2 loop 의 다른 축: 수집은 hook 이 자동(`scripts/dlc-signal.js` — early-stop·guard·doc-drift·router·plan 신호), 분석·제안이 이 skill, 반영은 사용자 승인 후 `wt→dlc` 별도 작업, 효과 확인은 다음 `/improve` 의 신호 추이
- P.3 c/e 처럼 메인이 직접 수행(subagent 위임 아님)

## 적용
- A.1 `/improve` 명시 호출 시 — 자산 추가/리네임 후, workflow 마찰이 반복된다고 느낄 때, 개선 효과를 확인하고 싶을 때
- A.2 단순 질문·탐색·코드 변경에는 쓰지 않는다

## 역할 경계
- B.1 README ↔ surface drift → `dlc-doc-drift` hook(세션 중 Stop 경고) 영역, improve 는 재판정하지 않고 hook 이 emit 한 `doc-drift-*` 신호를 사후 집계만
- B.2 wiki 내부 무결성(orphan·dead link·모순) → `/wiki lint` 영역, improve 는 공용 wiki(`~/.claude/wiki` clone, 경로 override `CLAUDE_IMPROVE_WIKI`)의 index↔pages 개수만 보고 lint 권장
- B.2b 같은 점검 6 이 이 repo 가 `wiki/` 를 추적하면 error(공용 wiki 는 비공개 repo — CI 게이트)
- B.3 대장 갱신(네이티브 중복 판정을 wiki 에 적립) → `/wiki ingest` 영역, improve 는 판정 초안까지, write 는 승인 후 ingest(§6 경계)
- B.4 improve 고유: 자산 간 크로스참조(settings↔scripts·MEMORY↔memory·문서↔agents·죽은 스크립트 후보) + 신호·실패 이력의 종합 분석과 개선 후보 랭킹 + 네이티브 흡수분과의 중복 재판정(§6) — 다른 어떤 메커니즘도 안 하는 부분

## 1. 기계 점검 + 신호 집계
- S.1 repo root 에서 `bash skills/improve/improve.sh` 를 1회 실행(read-only)
- S.1a 점검 1~6(구 audit 승계): `[error]` 실행경로 깨짐(settings→scripts 부재 — exec form `args` 의 절대경로는 그 경로 그대로 확인하고 `~`·`$HOME` 은 error, CLAUDE.md→agent 부재, skill·agent frontmatter 형식 위반 — YAML 오류·허용 형식 밖·name/description 누락, `scripts/frontmatter-lint.js`) / `[warn]` 미등록·한쪽 누락(MEMORY 인덱스, wiki 개수) / `[info]` 죽은 스크립트 후보(단정 아님) / `[ok]`
- S.1b 점검 8 = plan-lint(tracked plan 전수, 항상): `scripts/plan-lint.js` 로 §10 형식·무결성(frontmatter 필수키·필수 H1·Tasks 체크박스와 날짜·끊긴 Acceptance 참조), 위반은 `[warn]`, tracked plan 없으면 skip, 셸엔 active-plan 개념이 없어 전수(/c·/e 만 active plan 대상)
- S.1c 점검 7: `~/.claude/telemetry/dlc-signals.jsonl` 집계 — kind 별 `sessions`(unique)·`raw`·기간
- S.1d failure 축(early-stop-verify·early-stop-plan-drift·doc-drift-*·guard-worktree-deny·main-edit-ask·plan-blocked)과 activity 축(router-*·review-disposition·early-stop-wait-shell — 실패 아님, 활동량·대기 턴 수)을 분리 표시, kind 목록의 정본은 `scripts/dlc-signal.js` 의 `KINDS`
- S.1e 효과 판단은 sessions(unique) 우선 — raw 는 같은 세션 반복 발동에 지배될 수 있다
- S.1f 점검 9 = 네이티브 중복 대장 신선도(주기 게이트): 대장(`~/.claude/wiki/pages/decision/native-overlap-ledger.md`, override `CLAUDE_IMPROVE_LEDGER`)의 `checked` 가 임계(45일, `CLAUDE_IMPROVE_NATIVE_MAX_AGE_DAYS`)를 넘으면 §6 재판정 권고
- S.1g 점검 9 는 `[info]` 만 — 정합성 위반이 아니라 리마인더라 err/warn 카운터·랭킹 심각도 축을 오염시키지 않는다
- S.1h 대장 부재·frontmatter 불량·날짜 불량·미래 날짜는 사실만 적고 skip(`exit 0` 유지), 판정 로직은 `scripts/native-overlap-lint.js`(순수함수+CLI, 테스트 있음)

## 2. 누적 이력 대조
- H.1 `~/.claude/wiki/pages/decision/workflow-failures.md` 추적 표(실패·횟수·상태) read — 신호와 대조해 횟수 갱신이 누락된 실패를 찾는다
- H.2 `MEMORY.md` 인덱스(feedback 행동지시문) — 최근 작업에서 실제 반영됐는지, 죽은 규칙이 없는지
- H.3 현재/최근 plan log(`<slug>-log.md`, 옛 형식은 본문)의 `# Workflow Findings`·`# Deferred` — plan log(또는 옛 본문)에만 있고 wiki 로 승격 안 된 반복 항목

## 3. 의미 점검
- M.1 문서 간 모순(CLAUDE.md ↔ SKILL.md 규칙 충돌), 같은 trigger 의 skill 중복, 죽은 규칙(더는 유효하지 않은 항목)
- M.2 관련 파일을 read 해 근거로 판단(추측 금지 §1)

## 4. 개선 후보 랭킹 + 처분 제안
- R.1 각 후보 = `무엇이 문제 · 근거(신호 수치/파일:라인) · 제안 변경(어느 파일을 어떻게) · 예상 효과(어떤 신호가 줄어야 하나)`
- R.2 랭킹 기준: failure 신호 unique-session 빈도 × 심각도(실행경로 깨짐 > 반복 마찰 > 인벤토리) × 수정 비용(작을수록 위)
- R.3 효과 확인: 이전에 `fixed` 로 처리된 항목의 신호가 실제로 줄었는지 추이(안 줄었으면 재개선 후보로 복귀)
- R.4 처분: 사용자 승인 시 그 수정은 별도 작업(wt→dlc) — 운영 자산 변경은 파일 변경이라 worktree 필수, dlc 의 "같은 실패 2회+ 반복 시 해결 제안" 규칙과 같은 경로로 합류
- R.5 error 0 + 유의미 신호 없음이면 "개선 후보 없음" 보고

## 5. 광역 관측 (deep)
- D.1 기본 4단계로 부족하거나 주기 점검 시 `bash skills/improve/improve.sh deep` 로 3개 섹션을 더 본다(여전히 read-only·secret 미출력)
- D.2 점검 10 주입·로드 표면 크기(`wc -c`): CLAUDE.md·skills/*/SKILL.md·agents/*.md 바이트 + 합계 — 토큰 압박의 정량 근거(슬림화 후보)
- D.3 점검 11 사용량 카운트(`scripts/usage-count.js`): transcript 기반 skill·subagent·codex 호출 빈도(카운트·slug 만, 원문·파일명 미출력) — 실사용 낮은 자산 vs 고빈도 마찰 지점
- D.4 점검 12 MCP 서버 인벤토리(`~/.claude.json` 이름만) — 미사용·중복 후보
- D.5 deep 에서는 점검 9 도 한 줄 늘어난다 — delta 창(대장 `checked_version` → 설치 `claude --version`)을 출력해 §6 이 changelog 를 어디부터 읽을지 알려준다
- D.6 deep 은 광역 관측 보강일 뿐 — 판단·제안·처분 경로는 4단계와 동일(측정→판단→제안, 수정 금지, main 직접)
- D.7 외부 조회(생태계·버전)가 필요하면 main 이 별도 researcher 로 판단하되 로컬 transcript·MCP·telemetry 내용을 web 프롬프트에 넣지 않는다

## 6. 네이티브 중복 점검 (deep 전용·주기)
- N.1 자작 하네스가 Claude Code 네이티브에 흡수된 기능을 붙들고 있지 않은지 재판정, 1~5 가 "자산이 서로 어긋났나" 라면 이 축은 "자산이 아직 필요한가" — 유일하게 밖(네이티브)을 기준으로 삼는 축
- N.2 언제: 점검 9 가 임계 경과를 알릴 때, 또는 네이티브 대규모 릴리스 직후, 기본 4단계에서는 돌지 않는다(웹 조회 비용)
- N.3 절차 1 대장 read — 기존 판정과 `checked_version`
- N.4 절차 2 delta 조회 — 공식 changelog(`https://code.claude.com/docs/en/changelog`)를 `checked_version` 이후만, 전수 조회는 대장이 없거나 `checked_version` 이 없을 때만, 더 이전 이력은 `github.com/anthropics/claude-code/blob/main/CHANGELOG.md`, 외부 조회 규칙 아래 — 로컬 transcript·MCP·telemetry 내용을 web 프롬프트에 넣지 않는다
- N.5 절차 3 재판정 초안 — 파일은 수정하지 않는다, 뒤집힐 근거가 생긴 기존 행과 delta 에서 새로 겹친 컴포넌트를 표 형태 초안으로, 값은 `keep`/`watch`/`retire`(정의는 대장), 근거 없는 판정 금지(§1) — 각 행은 `vX.Y.Z + 날짜` 또는 로컬 파일 경로로
- N.6 절차 4 랭킹 합류 — 이 축의 후보는 telemetry 신호가 0 이라 unique-session 빈도 축에서 항상 바닥, 대체 점수: 중복도(`retire` > `watch`) × 유지비용(점검 10 표면 바이트·항상주입 여부) × 제거 비용
- N.7 절차 5 처분 — 4단계와 동일하게 제안까지
- N.8 경계: `/improve` 는 대장을 쓰지 않는다, 판정은 초안, 대장·`index.md`·`log.md` 갱신은 사용자 승인 후 `/wiki ingest`
- N.8b `retire` 판정이 나와도 자작 컴포넌트를 제거하지 않는다 — 랭킹 후보로만, 실제 제거는 승인 후 `wt→dlc` 별도 작업(§1·§11·§13)
- N.9 한계: 설치 버전이 최신보다 뒤처지면 delta 창이 최신 흡수분을 못 덮는다 — "버전 변화 없음 ≠ 중복 없음", 자동 업데이트를 끈 설치에서 특히

## 7. 마무리 — last-improve 마커
- K.1 (기본·deep 공통) 랭킹·처분 제안(또는 "개선 후보 없음")을 확정했으면 최종 보고 직전에 `node ~/.claude/scripts/dlc-signal.js mark` 를 1회 실행하고 결과를 보고에
- K.2 SessionStart 의 `/improve 권장 — failure 신호 N세션 누적 (마커 이후)` 는 마커 시각 이후의 세션만 센다 — 갱신하지 않으면 한 번 넘은 임계가 영영 내려오지 않아 권장이 신호로서 의미를 잃는다
- K.3 신호를 실제로 보지 못했으면 실행하지 않는다 — `improve.sh` 가 비0 으로 끝났거나, 점검 7 이 `신호 집계 실행 실패` 를 출력했거나, 보고 전에 중단한 경우, 보지 않은 신호까지 카운트에서 빠지므로
- K.3b 점검이 `[error]` 를 발견한 것은 실행 실패가 아니다
- K.4 경로를 `~/.claude/scripts/` 로 고정하는 이유: 이 SKILL 은 user-level(main checkout)에서 로드되는데, cwd 상대경로로 부르면 worktree 세션에서 이 기능이 없는 옛 스크립트가 돌 수 있다
- K.5 출력에 `last-improve 마커 갱신:` 줄이 없거나 비0 으로 끝나면 실패 — 보고에 한 줄(다음 세션도 권장이 계속 뜬다)

## 경계 (안 하는 것)
- X.1 수정 안 함 — 점검·집계·랭킹·제안까지, 운영 자산 자가수정 금지(§1), improve.sh 에 수정/파괴 명령 없음(read-only)
- X.1b 유일한 write 는 7단계 마커(`<signalDir>/last-improve` — 기본 `~/.claude/telemetry`, `CLAUDE_DLC_SIGNAL_DIR` 로 override, gitignored 로컬 상태, 운영 자산 아님)
- X.1c wiki 대장도 예외 아님 — §6 판정은 초안이고 write 는 승인 후 `/wiki ingest`
- X.2 신호 재판정 안 함 — telemetry 는 hook 판정의 사후 집계, README drift·wiki 내부는 각각 hook·`/wiki lint` 영역
- X.3 죽은 스크립트 단정·삭제 안 함 — info 후보로만, 실제 판단은 사람
- X.4 subagent 위임 아님 — 메인이 직접 실행·판단·보고

## 다른 파일이 가리키는 표지
- 절·점검 번호(§6·점검 1~12·### 1.~7.) — `improve.sh` 가 "SKILL §6"·"== 9." 로, 공용 wiki 대장이 improve 의 축으로 가리킨다. 그대로.
- 스크립트 출력 글자 `신호 집계 실행 실패`·`last-improve 마커 갱신:`·`/improve 권장 — failure 신호 N세션 누적 (마커 이후)` — 그대로.

## 핵심 문구 검색 세트
`/improve` · `deep` · `/audit` · `scripts/dlc-signal.js` · `wt→dlc` · `dlc-doc-drift` · `doc-drift-*` · `/wiki lint` · `~/.claude/wiki` · `CLAUDE_IMPROVE_WIKI` · `wiki/` · `/wiki ingest` · `bash skills/improve/improve.sh` · `[error]` · `args` · `~` · `$HOME` · `[warn]` · `[info]` · `[ok]` · `scripts/frontmatter-lint.js` · `scripts/plan-lint.js` · `~/.claude/telemetry/dlc-signals.jsonl` · `sessions` · `raw` · `KINDS` · `~/.claude/wiki/pages/decision/native-overlap-ledger.md` · `CLAUDE_IMPROVE_LEDGER` · `checked` · `CLAUDE_IMPROVE_NATIVE_MAX_AGE_DAYS` · `exit 0` · `scripts/native-overlap-lint.js` · `~/.claude/wiki/pages/decision/workflow-failures.md` · `MEMORY.md` · `<slug>-log.md` · `# Workflow Findings` · `# Deferred` · `fixed` · `bash skills/improve/improve.sh deep` · `wc -c` · `scripts/usage-count.js` · `~/.claude.json` · `checked_version` · `claude --version` · `https://code.claude.com/docs/en/changelog` · `github.com/anthropics/claude-code/blob/main/CHANGELOG.md` · `keep` · `watch` · `retire` · `vX.Y.Z + date` · `index.md` · `log.md` · `node ~/.claude/scripts/dlc-signal.js mark` · `신호 집계 실행 실패` · `~/.claude/scripts/` · `last-improve 마커 갱신:` · `<signalDir>/last-improve` · `CLAUDE_DLC_SIGNAL_DIR` · early-stop-verify · guard-worktree-deny · plan-blocked · review-disposition · early-stop-wait-shell · early-stop-plan-drift · main-edit-ask · router-* · SessionStart · skills/*/SKILL.md · agents/*.md
