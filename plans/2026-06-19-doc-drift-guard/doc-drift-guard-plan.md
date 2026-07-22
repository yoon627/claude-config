---
title: doc-drift-guard — 문서/index drift 조기경고 hook + evidence gate 명문화
status: done
started: 2026-06-19
updated: 2026-06-19
---

# Goal
dlc evidence gate 가 "코드 변경 ↔ 검증"만 추적하고 "문서화 표면 변경 ↔ README/index 동기화"는 추적하지 않아 README 가 반복적으로 뒤처진 근본 문제를, early-stop 패턴을 확장한 Stop hook(`dlc-doc-drift.js`)으로 메운다. 보조로 CLAUDE.md §3·dlc SKILL 에 문서 동기화를 evidence gate 항목으로 명문화.

# Progress
- 2026-06-19: 근본원인 분석(ledger/early-stop 코드 근거) 완료 → wt `doc-drift-guard` 생성 → dlc medium 착수. CI=node --check+JSON+shellcheck, 유닛테스트 인프라 없음 확인. draft plan 작성.
- 2026-06-19: plan-reviewer(Claude+Codex 병행) CONDITIONAL — 강한 우려 3건 반영해 설계 변경: 별도hook→early-stop 통합(소모-노출 분리 버그 차단), paths배열→dirty flag(same-turn 순서), basename→root 한정 정확매칭(FP 차단). Acceptance A1~A9 재작성.
- 2026-06-19: 구현 완료 — dlc-doc-drift.js(순수모듈)+test(26 assert) / ledger DEFAULT 스키마 / evidence-ledger·early-stop 통합. dogfooding: README·CLAUDE.md §3·dlc SKILL 동기화. Green: node --check 전체 + 단위26 + 통합스모크 7시나리오 + settings JSON valid 통과. → code-reviewer 단계.

# Next
(완료 — PR #58 squash 머지, main 반영. CI lint pass.) 남은 사용자 요청: ④ e 스킬 속도 개선(별도 작업 — 별 worktree).

# Decisions
- **early-stop 통합**(별도 hook 아님 — plan-reviewer 반영): 별도 Stop hook 이면 두 hook 이 같은 Stop 에서 둘 다 block 시 doc-drift 의 capped 카운터가 *출력 없이* 소모돼(Claude Code 가 첫 reason 만 노출) README 경고를 한 번도 못 보는 false negative(근본원인 재발). → `dlc-early-stop.js` 가 검증누락+문서drift 를 함께 판정하고 **한 block 메시지로 합쳐** 출력, 카운터(blocks·docBlocks) 각각 capped. 판정 로직은 `dlc-doc-drift.js` **순수 모듈**(hook 아님)로 분리해 early-stop·evidence-ledger 가 require + 단위테스트.
- **root 한정 + 정확 경로 매칭**(basename FP 차단 — plan-reviewer 반영): 이 drift 규칙은 `~/.claude` repo 자산 문서화 전용. `resolveRoot(cwd)`: cwd 가 `.../.claude/worktrees/<name>` 이면 그것, `.../.claude`(또는 하위)면 그 `.claude`, 둘 다 아니면 `null`→**no-op**(타 repo 무영향). 판정은 root 기준 **정확 상대경로**: trigger=`scripts/<f>.js`·`agents/<f>.md`·`skills/<x>/SKILL.md`·`settings.json`·`CLAUDE.md`, target=`README.md`. index: trigger=`wiki/pages/**`, target=`wiki/index.md`. 루트가 아닌 README/CLAUDE(per-repo·wiki 하위)는 매칭 안 됨.
- **dirty flag**(paths 배열 아님 — same-turn 순서 false negative 차단, plan-reviewer 반영): ledger 에 `readmeDirty`·`indexDirty`·`docBlocks` 추가. evidence-ledger 가 변경 분류 — trigger→`*Dirty=true`, target→`*Dirty=false`. 단순 `includes` 와 달리 "surface 변경 *이후* README 동반?"의 순서를 반영(prompt 중간 README-first 도 surface 가 뒤따르면 다시 dirty).
- **ledger 회귀 방지**(plan-reviewer 반영): `read` 기본값·`reset` **두 곳 모두** 새 필드 포함(한 곳 누락 시 undefined → evidence-ledger 가 fail-open 으로 조용히 기록 누락). 기존 `{changed,verified,blocks}` 보존 → early-stop 검증 경로 무회귀.
- **안전장치**: fail-open(의존/파싱/root=null exit 0)·capped(docBlocks<1)·holdout(`CLAUDE_DLC_DOCDRIFT_OFF=1`)·stop_hook_active 통과. **카운터 증가는 reason 을 실제 출력하는 분기에서만**(소모-노출 분리 금지).
- **문구 하향**(과신 방지 — plan-reviewer 반영): "동기화 증명"이 아니라 "문서 동기화 **검토 누락 1회 경고**". 차단 아닌 remind — 무관 변경(내부 버그픽스)은 재종료로 통과.
- **한계 명시**: `mv`/`git mv` rename 은 Edit/Write file_path 가 아니라 paths 미포착(수용·문구 명시). main↔worktree 같은 session_id 혼입은 약한 우려로 남김(보통 세션 분리).
- **자기 dogfooding + 테스트**: 새 스크립트 추가이므로 README·CLAUDE.md §3·SKILL 동기화(안 하면 자기 경고). `scripts/dlc-doc-drift.test.js`(node 내장 assert, 의존 0) 신설 + lint.yml 에 `node --check` 와 테스트 실행 추가.

# Key Files
- `scripts/dlc-doc-drift.js` (신규) — Stop hook 판정
- `scripts/dlc-ledger.js` — 스키마에 paths·docBlocks
- `scripts/dlc-evidence-ledger.js` — Edit/Write fp 를 paths 기록
- `scripts/dlc-task-router.js` — reset 경유(ledger.reset 확장으로 자동)
- `settings.json` — Stop 배열 등록
- `.github/workflows/lint.yml` — node --check 추가
- `CLAUDE.md` §3 / `skills/dlc/SKILL.md` — evidence gate 명문화
- `README.md` — scripts/settings hooks/Layout 동기화(dogfooding)

# Acceptance
(검증: `node scripts/dlc-doc-drift.test.js` 단위테스트 + early-stop 에 모의 stdin 스모크)
- A1 ledger 스키마: reset 후 read 하면 `readmeDirty:false`·`indexDirty:false`·`docBlocks:0` + 기존 `changed/verified/blocks` 보존. read·reset 두 곳 동기화.
- A2 classify/root: `resolveRoot` 가 worktree·`.claude`·타repo(null) 정확 판정. `classify(fp,root)` 가 trigger/target/null 정확(루트 README 만 target, `skills/x/README.md`·per-repo CLAUDE.md 는 null).
- A3 dirty 전이: trigger 변경 → readmeDirty=true; 그 뒤 루트 README 변경 → false. **same-turn README-first**(README→surface 순서) → 최종 readmeDirty=true(false negative 없음). wiki/pages↔index 동일.
- A4 통합 판정·출력: early-stop 에서 검증누락+문서drift 둘 다면 **한 block reason 에 합쳐** 출력, blocks·docBlocks 각각 1. 문서drift 만이면 문서 메시지만.
- A5 capped·소모-노출: docBlocks=1 → 재Stop 무경고. **카운터는 출력 분기에서만 증가**(미출력 소모 없음) — docBlocks=0 이고 readmeDirty=true 면 반드시 1회 출력.
- A6 holdout/safety: `CLAUDE_DLC_DOCDRIFT_OFF=1` → 문서drift 미발동(검증 경로는 유지). root=null·파싱실패 → exit0.
- A7 등록/문법: settings.json Stop 배열 유지(early-stop 통합이라 항목 추가 없음) + JSON valid. lint.yml 에 신규 `node --check` + 테스트 실행 라인.
- A8 dogfooding: README·CLAUDE.md §3·dlc SKILL 동기화 → 이 브랜치 변경에 drift hook 이 경고 안 함(실제 early-stop 실행 관찰).
- A9 전체 검증: `node --check` 전 dlc 스크립트+신규, `node dlc-doc-drift.test.js` 통과, settings.json JSON valid, shellcheck.

# Blockers
(없음)

# Review Disposition
plan-reviewer(Claude+Codex) 강한우려 3건 → 설계 단계 반영(통합·dirty flag·root 한정). code-reviewer(Claude+Codex) REQUEST CHANGES:
- Major① ignored 파일(tmp_*) drift 유발 → **fix**: applyChange 를 isIgnored 블록 안으로. 스모크 시나리오 8 회귀 검증 추가.
- Major② evidence-ledger require 결합 fail-open 비대칭 → **fix**: drift require 별도 try + `if(drift)` 가드.
- Major③ resolveRoot 임의 `.claude` 오인 → **fix**: os.homedir() 기준 `~/.claude` 만 인정(home 주입 가능). 타repo `.claude` null 테스트 추가.
- Minor classify 표면 누락 → **fix**(부분): top-level `*.js`·`commands/*.md` trigger 추가. `docs/`·`wiki/WIKI.md` 는 **defer**(보수적 트리거 — false positive 위험 대비 커버리지 공백 수용, 필요 시 후속).
- Minor reset 1턴 수명(후속 턴 README 갱신 미크레딧) → **wontfix**(검증 게이트와 동일 fail-open/저마찰 의도). 한계로 문서화.
- Minor Windows casing(startsWith 대소문자) → **defer**(실사용 cwd/file_path casing 일관, 스모크 통과; 위험 낮음).
2회 한도 내 1회로 모든 Major 해소 → fix loop 종료.

# Progress (재검증)
- 2026-06-19: code-reviewer REQUEST CHANGES 3 Major fix → 재검증 29 assertions + 8 스모크 통과.
