---
name: improve
description: dlc 자기개선 loop 의 분석 축 — 운영 자산 정합성 기계 점검(구 /audit 승계)과 hook 이 자동 누적한 workflow 실패 신호(telemetry)·wiki workflow-failures·feedback memory 를 함께 읽어 개선 후보를 근거·빈도 기반으로 랭킹 제시하는 오케스트레이션. `deep` 에서는 Claude Code 네이티브가 흡수한 기능과 자작 하네스의 중복을 주기(45일) 재판정하는 축도 돈다. 발견은 보고·제안까지, 수정은 사용자 승인 후 wt→dlc(운영 자산 자가수정 금지 §1 — 자동 수정 안 함). `/improve` 명시 호출 시 사용. 단순 질문·코드 변경에는 쓰지 않는다.
---

# improve — 자기개선 loop 의 분석 축 (읽기전용·랭킹·제안)

`/improve` 로 ① 운영 자산 정합성(구 `/audit` 승계)과 ② hook 이 자동 누적한 신호(telemetry)를 함께 분석해 **개선 후보를 랭킹**으로 제시한다. loop 의 다른 축과의 관계: **수집**은 hook 이 자동(`scripts/dlc-signal.js` — early-stop·guard·doc-drift·router·plan 신호), **분석·제안**이 이 skill, **반영**은 사용자 승인 후 `wt→dlc` 별도 작업, **효과 확인**은 다음 `/improve` 의 신호 추이. c/e 처럼 메인이 직접 수행(subagent 위임 아님).

## 적용
- `/improve` 명시 호출 시. 자산 추가/리네임 후, workflow 마찰이 반복된다고 느낄 때, 개선 효과를 확인하고 싶을 때.
- 단순 질문·탐색·코드 변경에는 쓰지 않는다.

## 역할 경계 (중복 회피 — 중요)
- **README ↔ surface drift** → `dlc-doc-drift` hook(세션 중 Stop 경고) 영역. improve 는 **재판정하지 않고** hook 이 emit 한 `doc-drift-*` 신호를 **사후 집계**만 한다.
- **wiki 내부 무결성**(orphan·dead link·모순) → `/wiki lint` 영역. improve 는 index↔pages 개수만 보고 lint 를 권장.
- **대장 갱신**(네이티브 중복 판정을 wiki 에 적립) → `/wiki ingest` 영역. improve 는 **판정 초안까지**, write 는 승인 후 ingest 가 한다(§6 경계).
- improve 고유: 자산 간 크로스참조(settings↔scripts·MEMORY↔memory·문서↔agents·죽은 스크립트 후보) + **신호·실패 이력의 종합 분석과 개선 후보 랭킹** + **네이티브 흡수분과의 중복 재판정**(§6) — 다른 어떤 메커니즘도 안 하는 부분.

## 동작 (기본 4단계 + `deep` 축 2종)

### 1. 기계 점검 + 신호 집계 — `improve.sh`
repo root 에서 `bash skills/improve/improve.sh` 를 **1회** 실행(read-only). 출력:
- 점검 1~6(구 audit 승계): `[error]` 실행경로 깨짐(settings→scripts 부재, CLAUDE.md→agent 부재, SKILL name 누락) / `[warn]` 미등록·한쪽 누락(MEMORY 인덱스, wiki 개수) / `[info]` 죽은 스크립트 *후보*(단정 아님) / `[ok]`.
- 점검 8 = **plan-lint**(tracked plan 전수, 항상): `scripts/plan-lint.js` 로 §10 plan 무결성(frontmatter 필수키·6 H1 섹션·**끊긴 Acceptance 참조**) 검사, 위반은 `[warn]`. tracked plan 없으면 skip. (셸엔 active-plan 개념 없어 전수 — /c·/e 만 active plan 대상.)
- 점검 7(신규): `~/.claude/telemetry/dlc-signals.jsonl` 집계 — kind 별 `sessions`(unique)·`raw`·기간. **failure 축**(early-stop-verify·doc-drift-*·guard-worktree-deny·main-edit-ask·plan-blocked)과 **activity 축**(router-*·review-disposition — 실패 아님, 활동량)을 분리 표시. 효과 판단은 sessions(unique) 우선 — raw 는 같은 세션 반복 발동에 지배될 수 있다.
- 점검 9 = **네이티브 중복 대장 신선도**(주기 게이트): `wiki/pages/decision/native-overlap-ledger.md`(경로 override `CLAUDE_IMPROVE_LEDGER`)의 `checked` 가 임계(45일, `CLAUDE_IMPROVE_NATIVE_MAX_AGE_DAYS`)를 넘었으면 §6 재판정을 권고. **`[info]` 만 낸다** — 정합성 위반이 아니라 리마인더라 err/warn 카운터·랭킹 심각도 축을 오염시키지 않는다. 대장 부재·frontmatter 불량·날짜 불량·미래 날짜는 사실만 적고 skip(`exit 0` 유지). 판정 로직은 `scripts/native-overlap-lint.js`(순수함수+CLI, 테스트 있음).

### 2. 누적 이력 대조
- `wiki/pages/decision/workflow-failures.md` 추적 표(실패·횟수·상태) read — 신호와 대조해 **횟수 갱신이 누락된 실패**를 찾는다.
- `MEMORY.md` 인덱스(feedback 행동지시문) — 최근 작업에서 실제 반영됐는지, 죽은 규칙이 없는지.
- 현재/최근 plan 의 `# Workflow Findings`·`# Deferred` — plan 에만 있고 wiki 로 승격 안 된 반복 항목.

### 3. 의미 점검 — LLM 판단 (기계가 못 잡는 것)
- 문서 간 모순(CLAUDE.md ↔ SKILL.md 규칙 충돌), 같은 trigger 의 skill 중복, 죽은 규칙(더는 유효하지 않은 항목).
- 관련 파일을 read 해 근거로 판단(추측 금지 §1).

### 4. 개선 후보 랭킹 + 처분 제안 (수정 안 함)
- 각 후보 = `무엇이 문제 · 근거(신호 수치/파일:라인) · 제안 변경(어느 파일을 어떻게) · 예상 효과(어떤 신호가 줄어야 하나)`.
- 랭킹 기준: failure 신호 unique-session 빈도 × 심각도(실행경로 깨짐 > 반복 마찰 > 인벤토리) × 수정 비용(작을수록 위).
- **효과 확인**: 이전에 `fixed` 로 처리된 항목의 신호가 실제로 줄었는지 추이를 보고(안 줄었으면 재개선 후보로 복귀).
- **처분**: 사용자 승인 시 그 수정은 **별도 작업(wt→dlc)** — 운영 자산 변경은 비trivial 이라 worktree 필수. dlc 의 "같은 실패 2회+ 반복 시 해결 제안" 규칙(wiki workflow-failures)과 동일 경로로 합류. error 0 + 유의미 신호 없음이면 "개선 후보 없음" 보고.

### 5. 광역 관측 — `improve.sh deep` (opt-in)
기본 4단계로 부족하거나 주기 점검 시 `bash skills/improve/improve.sh deep` 로 3개 섹션을 더 본다(여전히 read-only·secret 미출력):
- ⑩ **주입·로드 표면 크기**(`wc -c`): CLAUDE.md·skills/*/SKILL.md·agents/*.md 바이트 + 합계 — 매 세션/작업 토큰 압박의 정량 근거(슬림화 후보).
- ⑪ **사용량 카운트**(`scripts/usage-count.js`): transcript 기반 skill·subagent·codex 호출 빈도(카운트·slug 만, 원문·파일명 미출력) — 실사용 낮은 자산(죽은 후보) vs 고빈도 마찰 지점 식별.
- ⑫ **MCP 서버 인벤토리**(`~/.claude.json` 이름만): 등록 MCP 서버 목록 — 미사용·중복 후보.

deep 에서는 점검 ⑨ 도 한 줄 늘어난다 — **delta 창**(대장 `checked_version` → 설치 `claude --version`)을 출력해 §6 이 changelog 를 어디부터 읽으면 되는지 알려준다.

deep 은 **광역 관측 보강일 뿐** — 판단·제안·처분 경로는 4단계와 동일(측정→판단→제안, 수정 금지, main 직접). 외부 조회(생태계·버전)가 필요하면 main 이 별도 researcher 로 판단하되 **로컬 transcript·MCP·telemetry 내용을 web 프롬프트에 넣지 않는다**.

### 6. 네이티브 중복 점검 — deep 전용 · 주기 (역방향 정리)

자작 하네스가 **Claude Code 네이티브에 흡수된 기능을 붙들고 있지 않은지** 재판정한다. 1~5 가 "자산이 서로 어긋났나"를 보는 반면 이 축은 "자산이 **아직 필요한가**"를 본다 — 유일하게 밖(네이티브)을 기준으로 삼는 축이다.

**언제**: 점검 9 가 임계 경과를 알릴 때, 또는 네이티브 대규모 릴리스 직후. 기본 4단계에서는 돌지 않는다(웹 조회 비용).

**절차**:
1. **대장 read** — `wiki/pages/decision/native-overlap-ledger.md` 의 기존 판정과 `checked_version`.
2. **delta 조회** — 공식 changelog(`https://code.claude.com/docs/en/changelog`)를 **`checked_version` 이후만**. 전수 조회는 대장이 없거나 `checked_version` 이 없을 때만. 그보다 이전 이력은 `github.com/anthropics/claude-code/blob/main/CHANGELOG.md`. 이 조회는 위 "외부 조회" 규칙 아래 — **로컬 transcript·MCP·telemetry 내용을 web 프롬프트에 넣지 않는다**.
3. **재판정 초안** — **파일은 수정하지 않는다.** 뒤집힐 근거가 생긴 기존 행과 delta 에서 새로 겹친 컴포넌트를 **표 형태 초안으로 제시**한다. 값은 `keep`/`watch`/`retire`(정의는 대장). **근거 없는 판정 금지**(§1) — 각 행은 `vX.Y.Z + 날짜` 또는 로컬 파일 경로로 뒷받침한다.
4. **랭킹 합류** — 이 축의 후보는 telemetry 신호가 0 이라 4단계의 "unique-session 빈도" 축에서 항상 바닥이다. **대체 점수: 중복도(`retire` > `watch`) × 유지비용(⑩ 표면 바이트·항상주입 여부) × 제거 비용.**
5. **처분** — 4단계와 동일하게 **제안까지**. 아래 경계 참조.

**경계 (중요)**: `/improve` 는 **대장을 쓰지 않는다.** 판정은 초안으로 제시하고, 대장·`index.md`·`log.md` 갱신은 **사용자 승인 후 `/wiki ingest`** 가 한다. `retire` 판정이 나와도 자작 컴포넌트를 제거하지 않는다 — 랭킹 후보로 올릴 뿐이고, 실제 제거는 승인 후 `wt→dlc` 별도 작업이다(§1 운영 자산 자가수정 금지, §11 ingest 는 제안, §13 무승인 적립 금지).

**한계**: 설치 버전이 최신 릴리스보다 뒤처져 있으면 delta 창이 최신 흡수분을 못 덮는다 — **"버전 변화 없음 ≠ 중복 없음"**. 자동 업데이트를 끈 설치에서 특히 그렇다.

## 경계 (안 하는 것)
- **수정 안 함** — 점검·집계·랭킹·제안까지. 운영 자산 자가수정 금지(§1). improve.sh 에 수정/파괴 명령 없음(read-only). **wiki 대장도 예외 아님** — §6 판정은 초안이고 write 는 승인 후 `/wiki ingest`.
- **신호 재판정 안 함** — telemetry 는 hook 판정의 사후 집계. README drift·wiki 내부는 각각 hook·`/wiki lint` 영역.
- **죽은 스크립트 단정·삭제 안 함** — info 후보로만, 실제 판단은 사람.
- subagent 위임 아님 — 메인이 직접 실행·판단·보고.
