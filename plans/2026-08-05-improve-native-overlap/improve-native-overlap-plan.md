---
title: improve-native-overlap — /improve 에 "네이티브 중복 점검" 축 추가
status: in_progress
started: 2026-08-05
updated: 2026-08-11
---

# Goal

`/improve` 에 **네이티브 중복 점검** 축을 추가한다 — Claude Code 네이티브가 흡수한 기능과 겹치는 자작 하네스 부분을 주기적으로 재판정(keep/watch/retire)하고, 판정을 wiki 대장에 누적해 다음 점검이 delta 만 보게 한다. 근거: main 의 미커밋 wiki 페이지 `harness-keep-and-borrow` 의 "역방향 정리" 조건.

# Progress

- 2026-08-05: worktree `improve-native-overlap` 생성(base main@d7cfba1). Explore 완료 — `skills/improve/SKILL.md`(4단계+deep), `improve.sh`(점검 1~8 + deep 9~11), `wiki/WIKI.md` 규약, README 318~324·568~570 확인.
- 2026-08-05: 요구사항 명확화 3문 확정 — ①deep+주기 게이트 ②wiki 대장 페이지 ③메커니즘+초기 대장.
- 2026-08-05: 네이티브 사실 조사(공식 changelog v2.1.186~2.1.222, 2026-06-22~08-04) 완료. 설치 버전 `2.1.222`. 결과는 아래 `# Native Overlap 조사 결과`.
- 2026-08-06: plan-reviewer(+codex 0.146.0 medium) 검토 **CONDITIONAL** — blocker 3 / major 8. 전건 수용해 Decisions 1~17 로 재작성(D8~D17 이 신규·정정분).
- 2026-08-06: 구현 완료(10파일). D17 을 뒤집어 별도 모듈로 분리(D17 각주). 테스트가 결함 2건 포착(D18).
- 2026-08-06: code-reviewer(+codex 0.146.0 high) **REQUEST CHANGES** — Major 4 / Minor 8 / Nit 8, refuted 10(정규식 오매치·롤오버·번호계약·`I()` 카운터·`claude --version` hang 등은 실행으로 반증됨). 전건 처분 완료(아래 Review Disposition), D19~D22 추가.
- 2026-08-06: 재검증 — 단위 10스위트 PASS(신규 58케이스), TZ 7종 ALL PASS, shellcheck 무경고, plan-lint exit 0, wiki dead link 0. simplify 1건(`deltaWindowLines` 1원소 배열 → 문자열) 후 재검증 통과.
- 2026-08-11: `/e` 마무리 — **`3b3f554`** 로 커밋(11파일 +618/−18). WIP 체크포인트가 아니라 **완결 커밋**(작업·리뷰·검증 완료, squash 불필요). push/PR 은 아래 Blockers B-1 해소 후.

# Next

구현·리뷰·검증·커밋(`3b3f554`) 완료. 남은 것은 **머지 순서**(사용자 결정: main 먼저) — 순서대로:
1. **main 세션에서** main 의 미커밋 wiki 변경 커밋·push (`cd ~/.claude && git add wiki/ && git commit && git push origin main`). 신규 4페이지(`harness-keep-and-borrow`·`model-stage-tiering`·`claude-code-model-selection`·`claude-code-oss-frameworks`) + `M wiki/index.md`·`log.md`·`anthropic-claude-models.md`. **이 worktree 세션에서는 불가** — worktree 격리가 main 대상 git 조작을 차단한다.
2. 이 worktree 에서 `git fetch origin && git rebase origin/main` → `wiki/index.md` 충돌 수동 해소(양쪽이 각자 항목을 추가한 것뿐, 둘 다 살리면 됨).
3. 대장(`native-overlap-ledger.md`)의 `[!open]` 콜아웃 제거 + `[[harness-keep-and-borrow]]` 상호링크 추가, `harness-keep-and-borrow` 쪽에도 역링크(그러면 orphan·`sources` 우회가 정리된다).
4. `python3 skills/wiki/check_links.py` 재확인 → push → PR.

# Decisions

1. **실행 시점 = deep + 주기 게이트** (사용자 선택). 실제 조사·재판정은 `deep` 에서만(웹 조회 비용). 기본 4단계는 대장의 `checked` 날짜만 읽어 임계 경과 시 리마인더 — 매 `/improve` 비용 ~0 을 지키면서 "주기"를 잊지 않게 한다.
   - 이유: 이 축의 사실 원천은 Claude Code 최신 changelog(외부·컷오프 이후)라 WebFetch 가 필수 → improve 의 "싸고 로컬" 성격과 충돌. 게이트로 분리.
2. **판정 보존 = wiki 대장 페이지** `wiki/pages/decision/native-overlap-ledger.md` (사용자 선택). §11 영속 지식 성격에 맞고 `wiki/index.md` 동기화 동반(WIKI.md 불변규칙 1·5).
3. **delta 창(비용 절감 핵심)**: 대장 frontmatter 에 `checked:`(점검일) + `checked_version:`(그때의 CC 버전). 다음 점검은 changelog 전체가 아니라 `checked_version` 이후 항목만 읽는다. `improve.sh` 는 설치 버전(`claude --version`)과 대조해 delta 창을 출력.
4. ~~기본 점검 9 + deep 분기(재번호 회피)~~ → **번호 충돌로 폐기** (plan-reviewer B1). `improve.sh:124,134,141` 이 이미 `== 9./10./11.` 이라 기본 9 를 만들면 deep 실행 시 `== 9.` 가 두 번 나온다. **변경: 기본 점검 = 9(신설), deep = 10/11/12 로 재번호.** SKILL.md:44-46·README 의 원문자도 같은 값으로 동시 갱신(한 계약, 4곳).
5. **임계 = 45일**, env `CLAUDE_IMPROVE_NATIVE_MAX_AGE_DAYS`. ~~90일~~에서 하향 (plan-reviewer M4).
   - 이유: 실측 v2.1.186(06-22)~v2.1.222(08-04) = **6주 36릴리스**. 90일이면 delta ≈70~80 릴리스로 "delta 만 읽어 싸게"가 무너진다. 45일 ≈ 6주 ≈ 이번에 WebFetch 1회로 실제 처리한 분량 → 경험적으로 1회 조회에 들어가는 창.
   - env 값 검증: `Math.max(1, Number(...) || 45)` (선례 `session-brief.js:83`) — 0·음수·비숫자는 기본값 흡수.
6. **판정 3값**: `keep`(네이티브가 대체 못 함) / `watch`(부분 중복 — 더 흡수되면 재판정) / `retire`(대체됨 — 제거 후보). `retire` 여도 **자동 제거 안 함**(§1) — 랭킹 후보로만. 3값으로 못 담는 뉘앙스는 `rationale` 열에 산문으로(별도 예외 필드 안 만듦 — 스키마 비대화 회피).
7. **README 원문자 정정 동반**: README 322 는 deep 을 ⑧⑨⑩ 으로 적었으나 실제는 ⑨⑩⑪ (기존 drift). D4 재번호로 최종값은 **⑩⑪⑫**. 같은 문장을 고치는 김의 정정이라 범위 밖 확산 아님. README 트리 568~570 의 improve.sh 한 줄도 갱신 대상.
8. **[B3 수용] `/improve` 는 대장을 쓰지 않는다 — 판정 초안까지.** 대장 갱신은 **사용자 승인 후 `/wiki ingest`** 경로(index.md·log.md 동반). improve.sh 는 읽기만.
   - 이유: `SKILL.md:51` "수정 안 함(read-only)", `skills/wiki/SKILL.md:8` "페이지 write 는 메인만", §11 "ingest 제안(자동 아님)", §13 "무승인 자동 적립 금지", `self-diagnosis-and-improvement-status` "완전 무인 자동화 미채택". 자동 write 는 이 5개와 정면 충돌.
   - 결과: 이 축은 **읽기(대장)→조사(changelog delta)→판정 초안→제안**까지. 기존 4단계 "수정 안 함, 제안까지"와 동일한 처분 경로.
9. **[B2 수용] SKILL.md 절 번호**: `### 5. 광역 관측(deep)` 유지, 새 축은 **`### 6. 네이티브 중복 점검`**. 상단 `## 동작 (4단계 + deep)` → `## 동작 (기본 4단계 + deep 축 2종)`.
10. **[M1 수용] 대장 경로 env override** `CLAUDE_IMPROVE_LEDGER` (선례 `CLAUDE_DLC_SIGNAL_DIR` — `improve.sh:99`). self-cd(`improve.sh:14-21`) 때문에 override 없이는 staleness/부재 경로를 **원본 오염 없이 재현할 수 없다**. Acceptance 1·2 를 이 env 기준으로 재작성.
11. **[M3 수용] 심각도 = `[info]`**, `[warn]` 아님. `improve.sh:3` 정의상 warn 은 *정합성 위반*인데 "45일 지났다"는 리마인더다. warn 으로 내면 요약 카운터(`:161`)와 랭킹 심각도 축(`SKILL.md:38`)에 상시 +1 로 섞인다.
12. **[M5 수용] fail-safe**: 대장 부재·frontmatter 파싱 실패·`checked` 형식 불량/미래 날짜·`claude` 미설치/출력 형식 변경·버전 역전(설치 < checked_version) → 전부 `[info]` 로 사실만 적고 skip, `exit 0` 유지(`improve.sh:6` 정책). **"delta 없음 ≠ 중복 없음"**(자동 업데이트 꺼진 설치는 최신 네이티브를 못 봄) 한계를 SKILL 에 1줄.
13. **[M8 수용] 신호 0 축의 랭킹 진입 규칙**: 이 축 후보는 telemetry 신호가 없어 `SKILL.md:38` 의 "unique-session 빈도" 축에서 항상 바닥이다. 대체 점수 명시 — **중복도(retire > watch) × 유지비용(deep ⑩ 표면 바이트·주입 여부) × 제거 비용**.
14. **범위 밖 명시(비변경)**:
    - `scripts/session-brief.js:81-117` 의 `improveNudgeLine`(`last-improve` 마커 기반 `/improve` 주기 nudge)은 **이번에 건드리지 않는다** — 그건 "improve 를 언제 돌릴까", 이건 "네이티브 점검을 언제 돌릴까"로 층이 다르다. 두 리마인더가 따로 노는 것은 의도된 분리.
    - **kill-switch 안 만듦**: 새 점검은 `[info]` 만 내고 아무것도 쓰지 않아 차단력이 0 → `CLAUDE_PLAN_LINT_OFF`(CI 차단)·`CLAUDE_DLC_SIGNAL_OFF`(파일 write) 같은 선례와 성격이 다르다. 무력화가 필요하면 `CLAUDE_IMPROVE_NATIVE_MAX_AGE_DAYS` 를 크게 주면 된다.
    - **안정 ID(`[check:native-overlap]`) 병기 안 함** (codex 제안): 다른 8개 점검이 전부 번호만 쓰는데 하나만 ID 를 달면 규약이 갈린다. 재번호는 D4 로 한 번에 정리.
15. **[M7 수용] wiki 카테고리·링크**: `decision/` 채택 — 내용이 외부 버전 사실을 인용하지만 **결정물은 "이 repo 의 컴포넌트를 유지/감시/폐기"** 라는 ADR-lite 판정이다(`WIKI.md:18`). outbound 링크는 **이 worktree 에 실존하는 페이지만** 건다(`[[self-diagnosis-and-improvement-status]]`, `[[dlc-development-cycle]]`, `[[worktree-per-task]]`, `[[claude-codex-collaboration]]`) — dead link 금지. `harness-keep-and-borrow` 는 아직 이 브랜치에 없으므로 **wikilink 대신 `sources:` 경로 + `[!open]` 콜아웃**으로 참조하고, 그 페이지가 main 에서 커밋된 뒤 별도 ingest 로 상호링크한다.
16. **[rollback]** 코드측은 단일 커밋 revert(번호 계약 ⑩⑪⑫→⑨⑩⑪ 이 README·SKILL 과 짝으로 되돌아감). 데이터측(대장 판정)은 성격이 달라 **오판정을 행 삭제로 지우지 않는다** — 정정 행 + 근거 + `> [!conflict]` 콜아웃(WIKI.md 규칙 3).
17. ~~[M2 부분수용] staleness 판정을 `improve.sh` 안 inline node 로 두고 별도 모듈을 신설하지 않는다~~ → **별도 모듈 `scripts/native-overlap-lint.js` + `.test.js` + `lint.yml` 등재로 변경** (이유: 구현하며 로직이 "frontmatter 1줄 파싱"이 아니라 날짜 왕복 대조·로컬달력 변환·semver 비교·env clamp 4종으로 커졌다. inline 은 `node --check` 도 단위테스트도 못 받는데, 이 repo 는 `scripts/*.js` 전부를 `lint.yml` 두 목록에 등재하는 관행이고 `plan-lint.js` 가 동일한 "순수판정+CLI" 선례다. 실제로 분리 후 테스트가 결함 2건을 잡았다 — 아래 D18).
18. **[구현 중 발견] 테스트가 잡은 결함 2건** (§7 순서 위반의 대가 — 아래 Workflow Findings):
    - `2026-02-30` 이 `Date.parse` 에서 03-02 로 **롤오버**해 오타 날짜가 조용히 통과. → `parseIsoDate` 왕복 대조.
    - `checked: <오늘>` 이 **"미래"로 판정**. `checked` 는 사람이 로컬 달력으로 적는데 UTC 자정 instant 와 비교해, UTC+9 에서 로컬 오늘 오전은 아직 UTC 어제. → `today`(로컬 달력 문자열) 주입 비교. 부수 효과로 테스트가 타임존 독립이 됨(7종 검증).
19. **[code-review 반영] 임계값 규칙 정정**: ~~`Math.max(1, Number(...) || 45)`~~ → **유효 = 1 이상 유한 정수, 그 외(0·음수·비숫자·빈값·`Infinity`)는 전부 기본 45** (이유: 오타 임계를 1일로 clamp 하면 매 실행 리마인더가 떠 오히려 무시하게 된다. `Infinity` 로 무력화하는 D14 의 escape hatch 는 큰 정수로 대체 가능).
20. **[code-review 반영] Acceptance 3 축소**: deep 의 **판정 분포(keep/watch/retire 개수) 출력을 뺀다** (이유: 분포를 세려면 대장 마크다운 표를 파싱해야 하는데, 그러면 "신선도만 판정"이라는 이 스크립트의 고도가 깨지고 표 형식과 결합된다. deep 에서는 LLM 이 대장 전문을 읽으므로 중복이다). Acceptance 3 은 delta 창 + 번호 계약으로 좁힌다.
21. **[code-review 반영] 번호 계약 자동 가드**: B1(기본 9 ↔ deep ⑨ 충돌)이 실제로 한 번 터진 결함이라 수동 관찰로 두지 않는다. `native-overlap-lint.test.js` 가 `improve.sh deep` 을 spawn 해 `== N.` 수열이 1..N 유일임을 검사(선례: `session-start-pull.test.js` 도 bash 를 spawn).
22. **[code-review 반영] env 이름**: `CLAUDE_INSTALLED_VERSION` → **`CLAUDE_IMPROVE_CC_VERSION`** (이유: 너무 범용이라 타 도구와 충돌 여지, `CLAUDE_IMPROVE_*` 네임스페이스 관례 이탈). README 에 3종 env 전부 문서화.

# Native Overlap 조사 결과 (초기 대장의 근거 — §10 단일 진실 소스)

출처: 공식 changelog `https://code.claude.com/docs/en/changelog`, 조회 범위 **v2.1.186(2026-06-22) ~ v2.1.222(2026-08-04)**. 로컬 설치 `claude --version` = **2.1.222**. (그 이전 2026년 분은 `github.com/anthropics/claude-code/blob/main/CHANGELOG.md`.)

| # | 자작 컴포넌트 | 네이티브 대응 (버전·날짜) | 판정 | 근거 요지 |
|---|---|---|---|---|
| 1 | `scripts/guard-worktree-edit.js` — main 추적파일 편집에 `ask` | worktree isolation 이 **모든 세션 타입**의 file edit + Bash 에 적용, main 파괴적 git checkout 차단 (v2.1.222, 08-04); `EnterWorktree` 가 `.claude/worktrees/` 밖 진입 시 확인 (v2.1.206, 07-09) | **watch** | 방향이 반대 — 네이티브는 *worktree 안에서 밖으로 새는 것*을 막고, 자작 guard 는 *main 에서 편집을 시작하는 것*을 막는다. 아직 대체 아님 |
| 2 | `/e` step6 + `wt` 의 push·PR·정리 흐름 | background agent 가 worktree 에서 **commit·push·draft PR** 까지 자동 (v2.1.198, 07-01); `/commit-push-pr` 이 `remote.pushDefault` 자동 허용 (v2.1.206, 07-09) | **watch** | 네이티브가 "코드 마무리"를 흡수. 자작은 plan 동기화·worklog·worktree 정리까지 묶은 범위라 아직 더 넓다 |
| 3 | `agents/code-reviewer.md` + codex 병행 (§9) | 빌트인 `/code-review <level>` 멀티에이전트 (v2.1.202, 07-06), 품질 개선 (v2.1.206), 비대화 세션 cloud review (v2.1.218, 07-22) | **watch** | CLAUDE.md §10 이 이미 "로컬 다관점 점검이 필요하면 빌트인 `/code-review` 수동 사용"으로 공존을 인정 — 경계가 이미 문서화됨 |
| 4 | `skills/wt` — 요청사항→slug→worktree→dlc | `/fork` 가 자체 worktree 생성 (v2.1.221, 08-04); in-session subagent 는 `/subtask` 로 분리 (v2.1.212, 07-17) | **keep** | 네이티브는 *대화 복제·격리*, 자작은 *요청→개발사이클 진입* 오케스트레이션. 대체 관계 아님 |
| 5 | §12 feedback memory 규약 (`MEMORY.md` 인덱스 = 행동지시문) | 네이티브 memory 서브시스템: `/memory`, `MEMORY.md` 인덱스, frontmatter `modified` (v2.1.214, 07-18), 인덱스 초과 시 침묵 절단 대신 명시 에러 (v2.1.210, 07-14) | **keep** | 자작은 네이티브 *저장소를 그대로 쓰되* "인덱스를 명령형 행동지시문으로" 라는 운용 규약을 얹은 것 — 중복 아님. 단 v2.1.210 인덱스 크기 제한과 충돌 가능 → 인덱스 비대화 감시 |
| 6 | dlc evidence gate + 최종 검증 runner (15단계) | `/verify`·`/checkup` 셋업 점검·진단·수정 (v2.1.215, 07-19) | **watch** | 네이티브는 *환경·셋업* 진단 중심, 자작은 *plan `# Acceptance` 대조*. 겹치는 건 "검증 명령 실행" 부분뿐 |
| 7 | `scripts/dlc-signal.js` 로컬 telemetry(jsonl) | OTel `workflow.run_id`/`workflow.name` 속성 (v2.1.202, 07-06), `/usage` 귀속 수정 (v2.1.222) | **keep** | 네이티브 OTel 은 *외부 수집기* 전제, 자작은 *로컬 hook 판정 신호* 누적 — 소비자와 대상이 다름 |
| 8 | dlc 규모 gate·병렬 규약 (§3, §5) | `workflowSizeGuideline` 설정 (v2.1.219, 07-24), subagent 상한 env 3종 (v2.1.212/217/219), nested subagent depth 기본 3 (v2.1.219) | **watch** | 네이티브는 *상한(cap)*, 자작은 *언제 무엇을 돌릴지(정책)*. 층은 다르나 "규모 판정" 축이 겹치기 시작 |

맥락(판정 아님): **`ultraplan` 기능 제거** (v2.1.222, 08-04) — 네이티브도 과한 오케스트레이션을 걷어내는 방향. 자작 하네스의 오케스트레이션 축이 네이티브에 흡수되는 흐름과 같은 신호.

# Key Files

- `scripts/native-overlap-lint.js` — **신규** 신선도·delta 창 순수판정 + CLI(항상 `[info]`·exit 0).
- `scripts/native-overlap-lint.test.js` — **신규** 52 케이스(날짜 경계·TZ 독립·env clamp·semver·CLI·번호 계약 가드).
- `.github/workflows/lint.yml` — `node --check` 2줄 + unit test 1줄 등재.
- `wiki/pages/decision/self-diagnosis-and-improvement-status.md` — "바깥 기준 축" 절 추가(대장 inbound 링크 — orphan 회피).
- `skills/improve/improve.sh` — 점검 9 신설(staleness 게이트, `[info]`, lint 호출) + deep 9/10/11 → 10/11/12 재번호.
- `skills/improve/SKILL.md` — `### 6. 네이티브 중복 점검` 신설, 상단 동작 문구·역할 경계·deep 원문자 갱신.
- `wiki/pages/decision/native-overlap-ledger.md` — **신규** 대장(위 8행 + frontmatter `checked`/`checked_version`).
- `wiki/index.md` — decision 카테고리에 대장 등재.
- `wiki/log.md` — ingest 로그 append(WIKI.md 불변규칙 5).
- `README.md` 318~324(improve 섹션 + 원문자 ⑩⑪⑫ 정정), 568~570(트리 한 줄).

# Acceptance

1. **staleness 게이트 정상 경로** — `CLAUDE_IMPROVE_LEDGER=<임계 내 checked 를 가진 fixture> bash skills/improve/improve.sh` 실행 시 점검 9 가 `[info]` 로 "최근 점검 N일 전(임계 45일 내)"를 출력. 검증: 실행·출력 관찰. **원본 대장 미변경**(D10 env override).
2. **경과·부재·불량 fail-safe** — ① `checked` 를 임계 밖으로 둔 fixture → deep 권고 `[info]` ② 존재하지 않는 경로 → "대장 없음" `[info]` ③ `checked` 형식 불량/미래 날짜 fixture → skip `[info]`. 세 경우 모두 스크립트 `exit 0`, `err=0 warn=0` 유지. 검증: 실행·출력·`echo $?` 관찰.
3. **deep 분기 출력 + 번호 계약** — `bash skills/improve/improve.sh deep` 이 delta 창(`checked_version` → 설치 버전)을 출력하고, 헤더 수열이 `1..12` 로 **중복 없이 연속**이다(B1 회귀 방지). 판정 분포 출력은 D20 으로 범위에서 제외. 검증: 실행·출력 관찰 + `native-overlap-lint.test.js` 의 번호 계약 케이스 3종(CI 가 지킴).
4. **초기 대장이 근거 있는 실물** — 위 `# Native Overlap 조사 결과` 8행이 대장에 반영. **각 행이 `자작 컴포넌트 / 네이티브 대응 / verdict / 근거(vX.Y.Z + YYYY-MM-DD) / rationale` 5요소를 전부 채운다** — 수량이 아니라 행 단위 형식으로 검증. 추측 근거 0건(전 행이 changelog 항목 또는 로컬 파일 경로). 검증: 페이지 read 로 전 행 대조.
5. **SKILL.md 축이 절차로 실행 가능** — 무엇을 읽고(대장 `checked_version` → changelog delta), 무엇을 판정하고(3값), 어디에 쓰는지(**쓰지 않음 — 승인 후 `/wiki ingest`**, D8)가 명시. D13 의 대체 랭킹 규칙과 D12 의 "delta 없음 ≠ 중복 없음" 한계도 명시.
6. **문서 동기화** — README improve 섹션에 점검 9 반영 + 원문자 ⑩⑪⑫ 정정 + 트리 한 줄, `wiki/index.md` 등재, `wiki/log.md` append. (dlc evidence gate — 검증과 동급)
7. **read-only 불변 — 스크립트 + 절차 양쪽** — ① `improve.sh` diff 에 write/파괴 명령 없음 ② SKILL.md 새 절이 대장 자동 write 를 지시하지 않음(D8). 검증: diff 확인 + SKILL 문구 확인.
8. **CI lint 통과** — `shellcheck skills/improve/improve.sh` 무경고, `node scripts/plan-lint.js <이 plan>` 통과. 검증: 실행.
9. **wiki 무결성** — 대장의 outbound `[[링크]]` ≥2 가 **전부 이 브랜치에 실존**하는 페이지(dead link 0), frontmatter 필수키 충족. 검증: `python3 skills/wiki/check_links.py` 또는 파일 실존 확인.

# Blockers

**B-1 (미해소·머지 순서 의존)**: 근거 페이지 `wiki/pages/decision/harness-keep-and-borrow.md` 가 **main 에서 untracked** 라 이 브랜치에 없다. 대장은 D15 대로 wikilink 없이 `sources:`+`[!open]` 으로 참조해 **이 브랜치 단독으로는 무결**하지만(dead link 0 확인), 두 지식이 상호링크되려면 main 의 미커밋 wiki 변경(신규 4페이지 + `M wiki/index.md`)이 커밋돼야 한다. 또한 양쪽이 `wiki/index.md` 를 편집하므로 **머지 시 index.md 충돌 가능**(사소·수동 해소).

- **사용자 결정 (2026-08-11)**: **main 미커밋을 먼저** 올린다 → 이 브랜치 rebase → 상호링크까지 닫고 PR. 절차는 `# Next` 1~4.
- **풀려면 필요한 것**: main worktree 세션에서의 커밋·push. 이 worktree 세션은 격리 때문에 `git -C <main>` 이 차단된다(하네스가 §8 을 강제) — **다른 세션이 해야 한다.**

# Review Disposition

- plan-reviewer B1(점검 번호 충돌) → **fix** (D4)
- plan-reviewer B2(SKILL 5절 점유) → **fix** (D9)
- plan-reviewer B3(대장 write 가 read-only 경계 침범) → **fix** (D8) — 설계의 핵심 정정
- M1(Acceptance 재현 불가) → **fix** (D10, Acceptance 1·2 재작성)
- M2(테스트·CI) → **부분 fix** (D17 — shellcheck 는 받고, 모듈 신설은 wontfix + §7 예외 명시)
- M3(warn 이 카운터 오염) → **fix** (D11)
- M4(90일 과대) → **fix** (D5, 45일)
- M5(`claude --version` fail-safe) → **fix** (D12)
- M6(조사 결과 plan 미기록) → **fix** (`# Native Overlap 조사 결과` 신설)
- M7(harness-keep-and-borrow 의존) → **fix** (D15 + Blockers B-1 승격)
- M8(랭킹 진입 불가) → **fix** (D13)
- codex: 안정 ID 병기 → **wontfix** (D14 — 규약 분기 회피)
- codex: verdict 예외 필드 → **wontfix** (D6 — rationale 산문으로 흡수)
- codex: 1단계 축소안(게이트 후속으로) → **wontfix** — 사용자가 "deep+주기 게이트"를 명시 선택(축소안 = 탈락한 "deep 전용" 옵션). 대신 게이트를 최소화(`[info]`·inline·kill-switch 없음)해 우려를 흡수.
- codex: Next "4파일" ↔ Key Files 6파일 불일치 → **fix** (Next 재작성)

## code-reviewer (2026-08-06, +codex high)

- Major 테스트 TZ flake(fixture 를 UTC 날짜로 생성) → **fix** — fixture 도 `localToday` 기준. TZ 7종 재검증.
- Major plan §10 미동기화(D17 ↔ 구현 모순, Next·Key Files stale) → **fix** — D17 각주 + D18~D22 + Next·Key Files·Progress 갱신.
- Major Acceptance 3 판정분포 미출력 → **fix (Acceptance 정정)** — D20. 표 파싱은 스크립트 고도를 깨고 deep 에선 LLM 이 대장 전문을 읽어 중복.
- Major SKILL §6 절차 3 이 write 로 오독 가능 → **fix** — "재판정 초안 — 파일은 수정하지 않는다"로 개정.
- Minor README `nowMs` 시그니처 오류 → **fix** (`today`).
- Minor `compareVersions` suffix 오단정 → **fix** — 끝까지 앵커 + `v?` 허용. `2.1.222-beta` 는 `null`(수동 판단).
- Minor 테스트 `:54` 동어반복 → **fix** — `checked_version` 이 날짜인 fixture 추가(오매치 시 즉시 FAIL).
- Minor 대장 H1 부재 / `sources` 들여쓰기 / `self-diagnosis` `updated` 미갱신 → **fix** 3건.
- Minor `CLAUDE_INSTALLED_VERSION` 미문서화·네임스페이스 이탈 → **fix** (D22).
- Minor(⚠️) 다머신 TZ 로 리마인더 1일 무음 → **fix** — `-1일`을 오늘로 흡수(회귀 테스트 2건).
- Minor(⚠️) 번호 계약 자동 가드 부재 → **fix** (D21) — 이미 한 번 터진 결함이라 CI 가드로.
- Nit `DEFAULT_MAX_AGE_DAYS` 미사용 export / `CC_VERSION=""` 죽은 초기화 / env 값 메시지 / `usage-count.sh` 오기 / 대장 8행 날짜 / 3행 flip 조건 / index 분포 복제 → **fix** 7건.
- Nit 대장 8행 `v2.1.217` 날짜 → **fix** (2026-07-21).
- codex: `maxAgeDays=Infinity` 무력화 → **fix** (D19 로 기본값 흡수).
- 외부 사실(대장 8행의 changelog 내용) → **미검증 상태 유지** — 리뷰어 범위 밖으로 지정했고, 근거는 조회 시점 URL·버전·날짜로 대장에 명시. 다음 `/improve deep` 이 delta 로 재확인한다.

# Workflow Findings

- **§7 TDD 순서 위반** (2026-08-06, 이 작업): `native-overlap-lint.js` 를 먼저 쓰고 테스트를 나중에 썼다. Red 를 안 보고 간 대가로 결함 2건(`2026-02-30` 롤오버 · 로컬 오늘이 "미래")이 *구현 후에야* 드러났다 — 테스트 우선이었다면 날짜 경계 케이스를 쓰는 시점에 둘 다 잡혔다. 자진 기록(사용자 지적 아님, §13). 2회 반복되면 게이트 승격 검토.

# Deferred

- `wiki` orphan 2건 — `lesson-parallel-duplicate-implementation`, `lesson-parser-precedent-partial-mirror` (inbound 링크 없음). **baseline 입증**: 둘 다 base `d7cfba1` 에 존재하며 이번 변경과 무관(`check_links.py` 는 이번 브랜치에서도 동일 2건만 보고). 심각도 낮음(WIKI.md 불변규칙 1 은 outbound 기준이고 orphan 은 lint 경고).
