---
title: native-overlap-ledger
category: decision
created: 2026-08-06
updated: 2026-08-12
checked: 2026-08-06
checked_version: 2.1.222
sources:
  - https://code.claude.com/docs/en/changelog (조회 2026-08-06, v2.1.186 2026-06-22 ~ v2.1.222 2026-08-04)
  - 로컬 `claude --version` = 2.1.222 (2026-08-06)
  - wiki/pages/decision/harness-keep-and-borrow.md ("역방향 정리" 조건 — 이 대장을 요구한 결정)
  - 1b 실측 2026-08-12 (worktree 세션에서 main checkout Write 시도 — 관측표는 본문)
---

# native-overlap-ledger

자작 하네스의 각 부품이 **Claude Code 네이티브에 흡수됐는지**를 주기적으로 재판정해 누적하는 대장. [[harness-keep-and-borrow]] 가 "유지 부품 선별 차용"을 결정하며 조건으로 건 **역방향 정리**의 실행 장치다. `/improve` 의 네이티브 중복 점검 축(`skills/improve/SKILL.md` §6)이 읽고, 갱신은 **사용자 승인 후 `/wiki ingest`** 로만 한다 — `/improve` 자신은 쓰지 않는다([[self-diagnosis-and-improvement-status]] 의 "반영은 승인 게이트", CLAUDE.md §1·§11).

## 판정 3값

| verdict | 뜻 | 처분 |
|---|---|---|
| `keep` | 네이티브가 대체하지 못하는 고유 가치 | 유지. 재판정만 |
| `watch` | 부분 중복 — 네이티브가 더 흡수하면 뒤집힐 수 있음 | 유지 + 다음 점검에서 우선 확인 |
| `retire` | 네이티브로 대체됨 | **제거 후보로 랭킹에 올림.** 자동 제거 없음(§1) |

3값으로 안 담기는 뉘앙스는 별도 필드를 만들지 않고 근거 열의 산문으로 적는다.

## 운영 규칙

- **`checked` ≠ `updated`**: `checked` 는 *changelog delta 를 전수 훑은* 마지막 날이고, `updated` 는 이 문서가 마지막으로 바뀐 날이다. 한 행을 표적 실측해 판정만 뒤집는 경우처럼 delta 조회 없이 갱신할 때는 **`checked` 를 밀지 않는다** — 밀면 45일 타이머가 근거 없이 리셋된다.
- **delta 창**: frontmatter `checked_version` 이 다음 점검의 시작점. changelog 를 전수로 읽지 않고 그 버전 이후만 본다. `improve.sh` 점검 9 가 설치 버전과 대조해 창을 출력.
- **주기**: 마지막 `checked` 로부터 45일(`CLAUDE_IMPROVE_NATIVE_MAX_AGE_DAYS`). 근거 — 실측 v2.1.186~v2.1.222 가 6주 36릴리스라, 그보다 긴 창은 "delta 만 읽어 싸게"가 성립하지 않는다.
- **오판정 정정**: 행을 지우지 않는다. 정정 행 + 근거 + `> [!conflict]` 콜아웃(WIKI.md 규칙 3) — 판정 이력 자체가 "네이티브가 언제 무엇을 흡수했나"의 기록이다.
- **한계**: 설치 버전이 최신 릴리스보다 뒤처져 있으면 delta 창이 최신 흡수분을 못 덮는다. **"버전 변화 없음 ≠ 중복 없음"**.

## 판정 (checked 2026-08-06 · 조회 창 v2.1.186 ~ v2.1.222)

| # | 자작 컴포넌트 | 네이티브 대응 (버전 · 날짜) | verdict | 근거 |
|---|---|---|---|---|
| 1a | `scripts/guard-worktree-edit.js` **기능 ①** — 비-worktree 세션에서 main/master tracked 파일 편집에 `ask` (**auto 모드는 제외** — `7c977c8` · 2026-08-06) | 해당 없음 | `keep` | 네이티브 worktree 격리는 *worktree 세션*에만 적용되는데 ①의 대상은 worktree 가 아예 없는 세션이라 **교집합이 없다**([[worktree-per-task]] 규약을 worktree 밖에서 지키게 하는 장치). 단 auto 모드에서 스스로 꺼져 적용 면적은 줄어든 상태 |
| 1b | `scripts/guard-worktree-edit.js` **기능 ②** — worktree 세션의 worktree 밖(main checkout) 편집 `deny` | worktree isolation 이 **모든 세션 타입**의 file edit + Bash 에 적용 (v2.1.222 · 2026-08-04); `EnterWorktree` 가 `.claude/worktrees/` 밖 진입 시 확인 (v2.1.206 · 2026-07-09) | **`retire`** | **2026-08-12 실측으로 확정** — 네이티브가 ②의 전 범위를 덮고 **더 넓다**(아래 관측). 제거 후보이나 자동 제거는 안 한다(§1) |
| 2 | `/e` step6 + `wt` 의 push·PR·정리 흐름 | background agent 가 worktree 에서 **commit·push·draft PR** 까지 자동 (v2.1.198 · 2026-07-01); `/commit-push-pr` 이 `remote.pushDefault` 자동 허용 (v2.1.206 · 2026-07-09) | `watch` | 네이티브가 "코드 마무리"를 흡수했다. 자작은 plan 동기화(§10)·worklog·worktree 정리까지 묶은 범위라 아직 더 넓다 — 좁아진 차집합이 무엇인지 다음 점검에서 재확인 |
| 3 | `agents/code-reviewer.md` + Codex 병행 (§9) | 빌트인 `/code-review <level>` 멀티에이전트 (v2.1.202 · 2026-07-06), 품질 개선 (v2.1.206 · 2026-07-09), 비대화 세션 cloud review (v2.1.218 · 2026-07-22) | `watch` | CLAUDE.md §10 이 이미 "로컬 다관점 점검이 필요하면 빌트인 `/code-review` 수동 사용"으로 공존을 문서화했다. 자작의 잔존 가치는 리뷰 자체가 아니라 [[claude-codex-collaboration]] 의 *교차 검증*(서로 다른 모델). 빌트인이 **외부 모델 교차검증**을 흡수하면 `retire` 후보 |
| 4 | `skills/wt` — 요청사항 → slug → worktree → dlc | `/fork` 가 자체 worktree 를 만들고 (v2.1.221 · 2026-08-04), in-session subagent 는 `/subtask` 로 분리 (v2.1.212 · 2026-07-17) | `keep` | 네이티브는 *대화 복제·격리*, 자작은 *요청 → 개발사이클 진입* 오케스트레이션([[dlc-development-cycle]]). 겹치는 건 worktree 생성이라는 수단뿐 |
| 5 | §12 feedback memory 규약 (`MEMORY.md` 인덱스 = 행동지시문) | 네이티브 memory 서브시스템: `/memory`, `MEMORY.md` 인덱스, frontmatter `modified` (v2.1.214 · 2026-07-18), 인덱스 초과 시 침묵 절단 대신 명시 에러 (v2.1.210 · 2026-07-14) | `keep` | 자작은 네이티브 *저장소를 그대로 쓰되* "인덱스를 명령형 행동지시문으로" 라는 운용 규약을 얹은 것이라 중복이 아니다([[feedback-memory]]). 단 v2.1.210 의 인덱스 크기 제한과 충돌할 수 있어 인덱스 비대화를 감시 |
| 6 | dlc evidence gate + 최종 검증 runner (15단계) | `/verify`·`/checkup` — 셋업 점검·진단·수정 (v2.1.215 · 2026-07-19) | `watch` | 네이티브는 *환경·셋업* 진단 중심, 자작은 *plan `# Acceptance` 대조*([[evidence-gate]]). 겹치는 건 "검증 명령 실행" 부분뿐이나, `/verify` 가 프로젝트 검증까지 흡수하면 runner 단계가 `retire` 후보 |
| 7 | `scripts/dlc-signal.js` 로컬 telemetry(jsonl 누적) | OTel `workflow.run_id`/`workflow.name` 속성 (v2.1.202 · 2026-07-06), `/usage` 귀속 수정 (v2.1.222 · 2026-08-04) | `keep` | 네이티브 OTel 은 *외부 수집기* 전제이고 자작은 *로컬 hook 판정 신호* 누적 — 소비자와 대상이 다르다. 외부 수집기를 붙일 계획이 없는 한 대체 불가 |
| 8 | dlc 규모 gate·병렬 규약 (§3·§5) | `workflowSizeGuideline` 설정 (v2.1.219 · 2026-07-24), subagent 상한 env 3종 (v2.1.212 · 2026-07-17 / v2.1.217 · 2026-07-21 / v2.1.219 · 2026-07-24), nested subagent 기본 depth 3 (v2.1.219 · 2026-07-24) | `watch` | 네이티브는 *상한(cap)*, 자작은 *언제 무엇을 돌릴지(정책)* 라 층이 다르다. 다만 "규모 판정"이라는 축 자체가 네이티브에 생긴 것은 처음이라 감시 대상 |

`retire` 판정: **1건** (1b, 2026-08-12 실측 확정). 나머지 창(v2.1.186~v2.1.222) 기준 변동 없음.

### 1b 실측 (2026-08-12) — 이 축의 첫 `retire`

정본 changelog 는 v2.1.222 를 "isolation now applies file edits" 라고만 적고 **차단인지 리다이렉트인지·범위가 어디까지인지 밝히지 않는다**. 그래서 문서가 아니라 관측으로 갈랐다. worktree 세션에서 main checkout 경로에 Write 를 시도한 결과:

| 편집 대상 | 자작 guard 판정 (hook 직접 호출) | 네이티브 판정 (실제 Write) |
|---|---|---|
| `<main>/plans/native-isolation-probe.md` | **ALLOW** (repo-root `~/.claude` 의 `plans/` 는 §10 핸드오프라 의도적 허용) | **DENY** |
| `<main>/scripts/native-isolation-probe.txt` | DENY | **DENY** |

네이티브 거부 문구: *"This session is isolated in the worktree … Edit the worktree copy of this file instead of the shared-checkout path."* — 이 문자열은 `scripts/`·`settings.json` 어디에도 없다(자작 hook 이 아니다).

**결론**: 네이티브 ⊇ 자작 ②이고 진상위집합이다 — 자작이 *허용*하는 `plans/` 까지 네이티브가 막는다. ②는 더 이상 아무것도 추가로 막지 못하므로 `retire`.

> [!conflict] 다만 "더 넓다"가 곧 "더 낫다"는 아니다. 자작 ②는 `plans/`·`projects/`·`settings.local.json` 을 **의도적으로 예외**로 뒀다 — worktree 복사본이 없는 전역·핸드오프 상태라 main 경로 편집이 정상이기 때문이다. 네이티브에는 그 예외가 없어 **worktree 세션에서 §12 memory 적립(`projects/…/memory/`)이 불가능**하다(2026-08-12 실측: "Edit the worktree copy of this file instead" — 그런데 그 파일엔 worktree 복사본이 존재하지 않는다). 이는 자작 guard 를 되살려서는 풀리지 않는다(네이티브가 먼저 막는다) — **별개의 workflow 마찰**로 추적한다. `retire` 판정 자체는 영향 없음.

**제거 시 함께 사라지는 것**(별도 작업의 검토 항목): `guard-worktree-deny` telemetry 신호 · 구버전 Claude Code(<2.1.222)에서의 보호 · `guard-worktree-edit.test.js` 의 ② 케이스. 기능 ①(1a)은 남으므로 파일 전체 삭제가 아니라 분기 제거다.

## 맥락 (판정 아님)

- **`ultraplan` 기능 제거** (v2.1.222 · 2026-08-04) — 네이티브도 과한 오케스트레이션 계층을 걷어내는 방향. 자작 하네스의 오케스트레이션 축이 흡수되는 흐름과 같은 신호로 읽는다.
- **`/agents` 위저드 제거** (v2.1.198 · 2026-07-01) — 관리 UI 대신 파일 직접 편집으로 회귀. 자작이 `agents/*.md` 를 파일로 관리하는 방식과 같은 방향.

