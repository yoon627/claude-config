---
title: intent-split-check — dlc 요구사항 명확화에 "분할 판정" 추가(묶음 intent 트리거 2 를 능동 판정으로)
status: in_progress
started: 2026-09-16
updated: 2026-09-16
intent: plans/2026-09-15-intent-bundles/intent.md
---

# Intent

→ `plans/2026-09-15-intent-bundles/intent.md` (Problem·Proposed outcome·공통 Constraints·Out of scope·Open questions 는 거기).

이 plan 에만 더해지는 것:
- Problem 델타: 묶음 intent 생성 트리거 2 는 "plan 이 2개 이상 **예상됨**"이라 수동이다 — 나눌 수 있는지 능동으로 판정하는 단계가 없다. 사용자 2026-09-16: "intent 하위 여러 plan 이 생겨야 plan 단위가 작아져서 일을 더 잘하지 않을까" → 검토 후 "분할 판정 1항 추가" 선택(intent.md 상시화·보류는 기각). ⚠️ "사전 판정이 없어서 사후 분할이 났다"는 intent.md Problem 의 체인이 직접 입증하지 않는다(구현 중 새 요구 발견일 수 있다) — 검증할 가설로 두고 재판단 조건을 `# Decisions` 에 남긴다.
- Constraints 델타: 체크리스트 **6항 불변**(`docs/dlc-details.md:8,10`·`wiki/pages/concept/unknowns-discovery.md:18`·`wiki/index.md:9` 가 "6항"을 참조) — 분할 판정은 7항이 아니라 별도 bullet. intent.md 는 여전히 **나뉠 때만** 만든다(상시화 아님). 규약 정의는 CLAUDE.md §10, 절차는 dlc(2026-09-07 배치 결정 유지). 분할이 규모 gate·필수 리뷰를 면제하지 않는다.
- Out of scope: 분할 판정의 hook/lint 강제 · 규모 gate 표·16단계 표 변경 · 기존 plan 소급(시행 이전 plan 에 `분할:` 근거를 요구하지 않고, 기존 묶음 연결이 과거 형제 재리뷰를 부르지 않는다) · `# Plans` 미착수 항목을 자동 worktree 화하는 도구 · 묶음 단위 architecture-reviewer(아래 ⚠️ deferred).
- 분할: 없음 — 10파일이 한 규약(정의 §10 + 절차 dlc + 검사 plan-reviewer + 요약 README/wiki)을 서술해, 일부만 머지되면 §10↔dlc↔plan-reviewer 가 서로 모순인 상태가 된다.
- 사용자 확인 vs 추론: "독립 머지 가능 단위·묶음 단위 plan-reviewer 1회"는 검토 답변에 적어 사용자가 선택지로 승인. 답변에 있던 "각 plan 목표 ≤ medium"은 plan-reviewer 지적으로 **"작게 나누되 규모는 gate 로 독립 판정"**으로 바꿨다(Report 에 통지).

# Goal

dlc 요구사항 명확화(medium 이상)에 분할 판정 1항을 넣어, 독립 검증·머지 가능한 단위로 나뉘면 `intent.md` + plan N 으로 착수하고 안 나뉘면 사유 1줄을 남기게 한다. §10 트리거 2 가 이 판정을 가리키도록 연결하고 plan-reviewer·`/e`·README·wiki 를 동기화한다.

# Acceptance

1. `skills/dlc/SKILL.md` 요구사항 명확화에 분할 판정 bullet 이 있다 — 판정 기준(각 단위가 순서대로 혼자 default 에 머지돼도 빌드·규약이 모순 없이 유효), 예비 판정→Explore 후 확정, 나뉠 때(intent.md + `# Plans`, 첫 plan 만 착수, 묶음 plan-reviewer 1회, 규모는 gate 로 독립 판정), 안 나뉠 때(`# Intent` 에 `분할: 없음 — <무엇을 나누려 했고 어떤 결합 때문에 못 나눴나>`), medium 이상만 — `grep -n '분할 판정' skills/dlc/SKILL.md` 관찰. codex owner 절에 묶음 리뷰 owner 1줄.
2. `CLAUDE.md` §10 트리거 2 가 의미("독립 검증·머지 가능한 복수 plan 으로 나뉠 때") + "medium 이상은 dlc 분할 판정" 연결로 바뀌고, `# Intent` 정의에 분할 판정 결과 1구절이 있다 — `grep -n '분할' CLAUDE.md` 관찰, 트리거는 닫힌 목록 3개 유지.
3. `agents/plan-reviewer.md` 입력 가정에 묶음 모드(intent.md `# Plans` 초안)가 있고 15항 "묶음 분할 경계"가 있다 — grep 관찰.
4. `skills/e/SKILL.md` 마무리 안내(4단계 보고)에 묶음 `# Plans` `(미착수)` 후보 안내 분기가 있다 — grep 관찰.
5. `docs/dlc-details.md:8`, `README.md:244`, `wiki/pages/concept/dlc-development-cycle.md`(29줄 + sources), `wiki/pages/concept/plan-handoff.md`(묶음 절 + sources), `wiki/index.md:9`, `wiki/log.md` 동기화 — grep + `python3 skills/wiki/check_links.py` → `clean`.
6. `plans/2026-09-15-intent-bundles/intent.md` `# Plans` 에 이 plan 줄, Open questions 에 재판단 조건 + 묶음 arch 이월 2건, `updated` 갱신, status 복제 없음 — 관찰.
7. 시나리오 판독 7종을 새 문구로 따라가 예상 경로와 일치 — (a) 순차 분할 A→B (b) 분할 불가 structural (c) 20줄 public API 변경 (d) 문서만 변경 (e) 기존 묶음 후속 (f) 첫 plan 종료 후 형제 착수 (g) Explore 후 판정 뒤집힘. 결과는 Report 에 표로.
8. `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음) + `bash skills/improve/improve.sh --ci` → `error=0 warn=0` + `node scripts/plan-lint.js <이 plan>` exit 0.

# Progress

- 2026-09-16: 사용자 질문 검토(09-07 섹션 → 09-15 묶음 파일 이미 존재) → 3안 제시 → "분할 판정 1항 추가" 선택. wt `intent-split-check` 생성. Explore 로 편집 대상 확정. draft plan → plan-reviewer(+codex medium 병행) CONDITIONAL 5건 + 약한 우려 6건 → 전부 처분(아래) 후 Key Files 10파일로 확정. 규모 medium(다중 파일 규약 변경 — 줄수는 small 범위, 시나리오 d 의 공백이 이 판정에 실제로 걸렸다 → Deferred). 구현 → code-reviewer(codex 미가용 — out of credits, 세션 마커 기록) Major 3·Minor 8·시나리오 막힘 3 → fix loop 1회차 반영(아래 Disposition) + simplify 축약(고정비·소급·면제 중복 3구절 제거).

- 2026-09-16: targeted 재리뷰 2회차 12건 반영(Major 1·Minor 5·Nit 6). 격리 runner: verify `ALL PASS`(skip 없음)·improve `error=0 warn=0`·check_links clean·plan-lint 0, Acceptance 1~6·8 관찰 충족. 2회차 수정 후 메인 targeted 재검증.

# Next

- 커밋 후 `/e merge`(medium — PR 경로) 또는 로컬 ff-merge 는 사용자 선택.

# Deferred

- 문서만 바꾸는 변경의 규모 판정 기준이 없다(규모 gate 표는 줄수·모듈 기준) — 분할 판정이 medium 이상에만 걸리므로 이 공백이 load-bearing 해졌다. 중간, `skills/dlc/SKILL.md:31-36`. 이번 Out of scope(규모 gate 표 변경).

# Decisions

- **분할 판정은 체크리스트 7항이 아니라 별도 bullet** — "6항" 참조가 3곳이라 7항으로 만들면 전부 갱신해야 하고, 6항은 *요구의 공백*이고 분할은 *실행 단위*라 성질이 다르다. 기각안: 7항 추가.
- **분할 기준은 크기가 아니라 "각 단위가 순서대로 혼자 default 에 머지돼도 빌드·규약이 모순 없이 유효"** — plan = worktree = 브랜치 = 머지 1:1 이라 plan 마다 고정비(worktree·dlc 파이프라인·`/e`·머지)가 붙는다. 이 repo 의 주된 변경이 문서 규약이라 "빌드 안 깨짐"만으로는 거의 항상 참 — 진짜 기준은 일부만 머지된 상태에서 규약끼리 모순되지 않는가(리뷰 지적 6). 순차 의존은 분할을 막지 않는다. **판정은 명확화에서 예비, Explore 후 확정**(규모 gate 예비값·재판정과 동형) — 뒤집히면 intent.md `# Plans` 를 갱신(합치면 `폐기`, 더 나뉘면 추가).
- **"각 plan ≤ medium" 기각 → "작게 나누되 규모는 gate 로 독립 판정, 분할이 승급·필수 리뷰를 면제하지 않는다"**(리뷰 지적 1, codex 합의) — 20줄 public API 도 structural(`SKILL.md:36`)이라 ≤ medium 을 목표로 두면 규모를 서술값에서 규범값으로 바꾸고 우회 유인이 생긴다. 나뉜 각 plan 이 structural 트리거를 가지면 그 plan 이 structural 로 돈다.
- ⚠️ 묶음 단위 architecture-reviewer planning 1회 — **`deferred`**(리뷰 처분): `agents/architecture-reviewer.md:29,43`("structural 만·문서만 변경은 호출 금지")과 충돌하고 사용자 확인이 없다. 위 "분할이 규모 판정을 면제하지 않는다" 1줄이 우회 유인을 닫는다(세 번째 선택지). "plan 사이에 걸친 구조 의사결정이 있을 때만 묶음 arch" 조건부 형태는 사용자 확인 후 별도 작업 → intent.md Open question 으로 이월.
- **묶음 plan-reviewer 1회 = 입력 가정에 묶음 모드 + 별도 15항**(리뷰 지적 3) — 14항은 "계획 텍스트만이면 검사 생략"이라 얹을 수 없고, 1~13항은 구현 계획 전제라 경계를 반박하는 항목이 0개. 15항 검사 축: 각 단위가 혼자 머지돼도 규약/빌드 무모순 · 요구 전체가 빠짐없이 배정 · 선행 의존 명시 · 후속 취소해도 앞 단위 유효 · 고정비 N배 대비 이득 · `분할: 없음` 근거 성립. "1회"는 최초 검토 한정 — 경계·의존·공통 제약이 바뀌면 재검토. 결과·처분 보존처는 **첫 plan 의 `# Review Disposition`** 에 `[묶음]` 접두(intent.md 는 H1 6개 고정이라 섹션을 늘리지 않는다). 호출 시점은 명확화 안(3단계 draft plan 전) — **16단계 표는 안 바꾼다**(2026-09-07 "Intent 는 명확화 산출물이라 표에 넣으면 시점이 어긋난다"와 같은 이유), codex owner 절에 1줄만. 묶음 리뷰는 트리거 1·2 로 **새로** 만드는 묶음에만, 소급(3)은 제외.
- **`분할: 없음 — <근거>` 기록처는 `# Intent`, §10 `# Intent` 정의에 1구절 추가**(리뷰 지적 5) — "§10 은 트리거만" 결정을 철회한다: 필드를 dlc 에만 두면 plan-reviewer 14항·`/c` 가 §10 항목 기준으로 읽어 그 줄을 모른다. 기각안: `# Decisions` 로(codex) — 착수 전 판정이고 `# Intent` 의 다른 항목처럼 "확정한 요구"의 일부라 시점 기준을 유지한다. 근거는 **무엇을 나누려 했고 어떤 결합 때문에 못 나눴나**가 드러나야 한다(정형문 양산 방지 — 리뷰 지적 8).
- **미착수 형제 재개 경로**(리뷰 지적 2) — `/c` 는 plan 을 새로 만들지 않고(`skills/c/SKILL.md:78`) `/e` 는 open 유지만 하므로 첫 plan 만 머지된 채 잊힐 수 있다. `/e` 4단계 보고의 "다음 세션은 `/c`" 안내에 **묶음 `# Plans` 의 `(미착수)` 후보를 경로와 함께 열거하고 `/wt <후보>` 로 착수** 분기를 넣는다. 착수하는 dlc 가 `(미착수)` 줄을 실제 plan 경로로 치환한다(0단계 스캔에 1구절).
- **§10 트리거 2 는 의미를 남기고 절차만 dlc 로 연결**(리뷰 지적 7) — CLAUDE.md 는 항상 주입, dlc 는 skill 진입 시만 로드라 정의를 dlc 로 옮기면 미진입 세션이 생성 조건을 잃는다. small 은 "예상될 때"(현행 유지), medium 이상은 dlc 능동 판정.
- **intent.md 상시화 기각**(사용자 선택 2026-09-16) — 사용례 1건에서 상시화하면 단발 작업마다 파일이 늘고 plan 이 실제로 작아지는지 관찰된 바 없다. **보류 기각** — 트리거 2 가 수동인 채로는 능동 분할이 일어날 경로가 없다. **재판단 조건**(리뷰 지적 9): 5회 사용 뒤 분할이 실제 일어났는지·`분할: 없음` 이 정형문이 됐는지 관찰 → 분할 0회·정형문이면 이 bullet 을 회수한다. intent.md Open question 으로.
- **Acceptance 에 시나리오 판독 7종**(리뷰 지적 10) — grep 은 상충 규칙 공존을 못 잡고 `plan-lint` 는 Intent 내용을 안 본다(`scripts/plan-lint.js:13`).
- **첫 plan 이 blocked 면** intent 는 open 유지, 형제 착수는 막지 않는다(순차 의존이 아니면) — 새 규칙 없음, §10 수명 그대로. 순차 분할이 늘면 §10 한계(`git show` 반입)가 상시 경로가 된다 — trivial/small 은 로컬 ff-merge(§8)로 빨리 닫아 완화, 규약 변경 없음.

# Key Files

- `skills/dlc/SKILL.md` 요구사항 명확화 — 분할 판정 bullet(묶음 intent bullet 뒤) + 묶음 스캔에 `(미착수)` 치환 1구절 + codex owner 절 1줄
- `CLAUDE.md` §10 — 트리거 2 문구 + `# Intent` 정의 1구절
- `agents/plan-reviewer.md` — 입력 가정 묶음 모드 + 15항
- `skills/e/SKILL.md` 4단계 보고 — `(미착수)` 후보 안내 분기
- `docs/dlc-details.md:8` — SKILL 인라인 항목 열거
- `README.md:244` — §10 요약줄
- `wiki/pages/concept/dlc-development-cycle.md` — 29줄 + sources
- `wiki/pages/concept/plan-handoff.md` — 묶음 절 + sources
- `wiki/index.md:9`, `wiki/log.md`
- `plans/2026-09-15-intent-bundles/intent.md` — `# Plans` 줄 + Open question 2건

# Blockers

없음.

# Review Disposition

plan-reviewer 2026-09-16(+codex medium):
- ⚠️ self-flag 묶음 arch 1회 — `deferred`(Decisions, intent.md Open question 이월)
- 1 ≤ medium 충돌 — `fix` · 2 형제 재개 경로 — `fix`(e 4단계) · 3 묶음 리뷰 입력 계약 — `fix`(15항+입력 가정) · 4 호출 지점 — `fix`(codex owner 절; 16단계 표는 `wontfix`, 이유 Decisions) · 5 `분할:` 필드 §10 미정의 — `fix`(§10 Intent 정의)
- 6 판정 문구 — `fix` · 7 트리거 치환 — `fix` · 8 정형문 — `fix`(근거 형식) · 9 근본 원인 과잉 — `fix`(가설로 낮춤+재판단 조건) · 10 시나리오 acceptance — `fix` · 11 dogfooding — `fix`(이 plan Intent 에 `분할: 없음`)
- 누락 시나리오 4건 — first blocked/순차 상시화: `wontfix`(기존 규약으로 충분, Decisions) · Explore 후 뒤집힘: `fix`(예비→확정) · 트리거 1 묶음 리뷰: `fix`(1·2 에 적용) · small 2개 갈림: `fix`(§10 small 은 예상 시 유지)

code-reviewer 2026-09-16 1회차(codex 미가용):
- Major — 14항 소급 면제 누락: `fix`(2026-09-16 이후 한정) · 묶음 모드가 intent.md 형식 검사 배제: `fix`(15항에 §10 형식 축 + 12항 유지) · 나뉜 단위 small 이면 plan 미보장: `fix`(규모 무관 plan 생성)
- Minor — 47↔48 시점 순환: `fix` · 계획 phase codex owner 2개: `fix`(묶음 리뷰 codex off) · `[묶음]` §10 미정의: `fix`(Review Disposition 정의) · `(미착수)` 줄 형식: `fix`(§10 `# Plans` 형식 + e) · §10 `# Intent` 규모 단서·트리거 구분: `fix`(`분할: 묶음 — <단위 수>` 도입) · §5·README:285·agent description 미동기화: `fix` · 5곳 중복 서술: 부분 `fix`(dlc-development-cycle 축약) + `wontfix`(plan-handoff 는 결정 이력이지 절차 복제가 아님) · `"작아서" 금지` 정형문 유인: `fix`(허용 예로 교체)
- 시나리오 — (d) 문서만 변경 규모: `defer`(`# Deferred`) · (e) 열린 묶음 후속 재분할: `fix`(기존 `# Plans` 에 줄 추가, 새 경계만 리뷰) · (g) 뒤집힘: `fix`(양방향 1구절)
- Acceptance 6 문구 낡음: `fix`(2건으로)

targeted 재리뷰 2026-09-16 2회차(codex 미가용) — 1회차 9건 닫힘·4건 부분:
- Major `폐기`×`(미착수)` 이중 마킹: `fix`(합쳐지면 `(미착수)` 줄 삭제 — 착수 전이라 폐기할 plan 이 없다)
- Minor — 12항 `# Decisions` 앵커: `fix`(내용 검사 + 기록처 첫 plan) · small 형제 plan 보장 위치: `fix`(규모 무관 bullet 47 로 이동, **trivial 포함** — 묶음 단위는 추적 대상 요구의 일부라 §10 적용 범위에 든다) · `분할: 묶음 — <단위 수>` 복제: `fix`(`묶음 → <intent.md 경로>` 포인터로, 3곳) · 소급 면제 producer 소실: `fix`(48 끝 1구절) · 묶음 모드 출력 형식: `fix`(입력 가정 1구절)
- Nit — 47 트리거 2 무조건문: `fix` · trivial: 위 fix 에 포함 · `/wt <slug 후보> — <메모>`: `fix` · 15항 형식 축 frontmatter·미착수 줄: `fix` · codex off 문장 위치: `wontfix`(문장이 "6단계 하나"로 정확) · 고정비 근거 복원: `fix`(괄호 1구절)
- open 2 — trivial 단위 plan: 위 결정으로 해소 · 12항 목적: 분할선 대안 검토 강제(입력 가정에 명시)
