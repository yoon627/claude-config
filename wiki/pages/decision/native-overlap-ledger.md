---
title: native-overlap-ledger
category: decision
created: 2026-08-06
updated: 2026-09-27
checked: 2026-09-27
checked_version: 2.1.283
sources:
  - https://code.claude.com/docs/en/changelog (조회 2026-08-06, v2.1.186 2026-06-22 ~ v2.1.222 2026-08-04)
  - https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md (조회 2026-09-27, 원문 v2.1.223 ~ v2.1.283 전수 2,326줄) · 날짜는 https://registry.npmjs.org/@anthropic-ai/claude-code 게시 시각(UTC)
  - https://code.claude.com/docs/en/memory (조회 2026-09-27 — `claudeMdExcludes`)
  - https://code.claude.com/docs/en/worktrees · https://code.claude.com/docs/en/hooks (조회 2026-09-27 — `.worktreeinclude` 적용 범위, `tool_response.bashEditDiff`)
  - 로컬 `claude --version` = 2.1.222 (2026-08-06), 2.1.283 (2026-09-27)
  - plans/2026-09-27-native-overlap-recheck/native-overlap-recheck-plan.md (2026-09-27 재판정)
  - wiki/pages/decision/harness-keep-and-borrow.md ("역방향 정리" 조건 — 이 대장을 요구한 결정)
  - 1b 실측 2026-08-12 (worktree 세션에서 main checkout Write 시도 — 관측표는 본문)
  - 1b 재실측 2026-09-27 (2.1.283 — EnterWorktree 세션과 worktree 디렉토리에서 시작한 세션 비교, `guard-worktree-deny` 신호 이력 — 관측표는 본문 "1b 정정")
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
- **조회 방법**: GitHub `CHANGELOG.md` 원문을 받아 창 구간을 로컬에서 끝까지 읽는다. WebFetch 는 큰 문서를 요약 모델로 줄여 뒤쪽이 잘리고 버전 귀속이 흔들린다(2026-09-27 실측 — 그 결과로는 "대응 없음"을 보증할 수 없다). `skills/improve/SKILL.md` §6 2단계는 아직 docs changelog 페이지를 1차 출처로 적고 있다 — 개정은 운영 자산 변경이라 승인 후 별도 작업.
- **주기**: 마지막 `checked` 로부터 45일(`CLAUDE_IMPROVE_NATIVE_MAX_AGE_DAYS`). 근거 — 실측 v2.1.186~v2.1.222 가 6주 36릴리스라, 그보다 긴 창은 "delta 만 읽어 싸게"가 성립하지 않는다.
- **오판정 정정**: 행을 지우지 않는다. 정정 행 + 근거 + `> [!conflict]` 콜아웃(WIKI.md 규칙 3) — 판정 이력 자체가 "네이티브가 언제 무엇을 흡수했나"의 기록이다.
- **한계**: 설치 버전이 최신 릴리스보다 뒤처져 있으면 delta 창이 최신 흡수분을 못 덮는다. **"버전 변화 없음 ≠ 중복 없음"**.

## 판정 (checked 2026-08-06 · 조회 창 v2.1.186 ~ v2.1.222)

| # | 자작 컴포넌트 | 네이티브 대응 (버전 · 날짜) | verdict | 근거 |
|---|---|---|---|---|
| 1a | `scripts/guard-worktree-edit.js` **기능 ①** — 비-worktree 세션에서 main/master tracked 파일 편집에 `ask` (**auto 모드는 제외** — `7c977c8` · 2026-08-06) | 해당 없음 | `keep` | 네이티브 worktree 격리는 *worktree 세션*에만 적용되는데 ①의 대상은 worktree 가 아예 없는 세션이라 **교집합이 없다**([[worktree-per-task]] 규약을 worktree 밖에서 지키게 하는 장치). 단 auto 모드에서 스스로 꺼져 적용 면적은 줄어든 상태 |
| 1b | `scripts/guard-worktree-edit.js` **기능 ②** — worktree 세션의 worktree 밖(main checkout) 편집 `deny` | worktree isolation 이 **모든 세션 타입**의 file edit + Bash 에 적용 (v2.1.222 · 2026-08-04); `EnterWorktree` 가 `.claude/worktrees/` 밖 진입 시 확인 (v2.1.206 · 2026-07-09) | **`retire`** | **2026-08-12 실측으로 확정** — 네이티브가 ②의 전 범위를 덮고 **더 넓다**(아래 관측). 제거 후보이나 자동 제거는 안 한다(§1). → 2026-09-27 `keep` 정정(아래 "1b 정정") |
| 2 | `/e` step6 + `wt` 의 push·PR·정리 흐름 | background agent 가 worktree 에서 **commit·push·draft PR** 까지 자동 (v2.1.198 · 2026-07-01); `/commit-push-pr` 이 `remote.pushDefault` 자동 허용 (v2.1.206 · 2026-07-09) | `watch` | 네이티브가 "코드 마무리"를 흡수했다. 자작은 plan 동기화(§10)·worklog·worktree 정리까지 묶은 범위라 아직 더 넓다 — 좁아진 차집합이 무엇인지 다음 점검에서 재확인 |
| 3 | `agents/code-reviewer.md` + Codex 병행 (§9) | 빌트인 `/code-review <level>` 멀티에이전트 (v2.1.202 · 2026-07-06), 품질 개선 (v2.1.206 · 2026-07-09), 비대화 세션 cloud review (v2.1.218 · 2026-07-22) | `watch` | CLAUDE.md §10 이 이미 "로컬 다관점 점검이 필요하면 빌트인 `/code-review` 수동 사용"으로 공존을 문서화했다. 자작의 잔존 가치는 리뷰 자체가 아니라 [[claude-codex-collaboration]] 의 *교차 검증*(서로 다른 모델). 빌트인이 **외부 모델 교차검증**을 흡수하면 `retire` 후보 |
| 4 | `skills/wt` — 요청사항 → slug → worktree → dlc | `/fork` 가 자체 worktree 를 만들고 (v2.1.221 · 2026-08-04), in-session subagent 는 `/subtask` 로 분리 (v2.1.212 · 2026-07-17) | `keep` | 네이티브는 *대화 복제·격리*, 자작은 *요청 → 개발사이클 진입* 오케스트레이션([[dlc-development-cycle]]). 겹치는 건 worktree 생성이라는 수단뿐 |
| 5 | §12 feedback memory 규약 (`MEMORY.md` 인덱스 = 행동지시문) | 네이티브 memory 서브시스템: `/memory`, `MEMORY.md` 인덱스, frontmatter `modified` (v2.1.214 · 2026-07-18), 인덱스 초과 시 침묵 절단 대신 명시 에러 (v2.1.210 · 2026-07-14) | `keep` | 자작은 네이티브 *저장소를 그대로 쓰되* "인덱스를 명령형 행동지시문으로" 라는 운용 규약을 얹은 것이라 중복이 아니다([[feedback-memory]]). 단 v2.1.210 의 인덱스 크기 제한과 충돌할 수 있어 인덱스 비대화를 감시 |
| 6 | dlc evidence gate + 최종 검증 runner (15단계) | `/verify`·`/checkup` — 셋업 점검·진단·수정 (v2.1.215 · 2026-07-19) | `watch` | 네이티브는 *환경·셋업* 진단 중심, 자작은 *plan `# Acceptance` 대조*([[evidence-gate]]). 겹치는 건 "검증 명령 실행" 부분뿐이나, `/verify` 가 프로젝트 검증까지 흡수하면 runner 단계가 `retire` 후보 |
| 7 | `scripts/dlc-signal.js` 로컬 telemetry(jsonl 누적) | OTel `workflow.run_id`/`workflow.name` 속성 (v2.1.202 · 2026-07-06), `/usage` 귀속 수정 (v2.1.222 · 2026-08-04) | `keep` | 네이티브 OTel 은 *외부 수집기* 전제이고 자작은 *로컬 hook 판정 신호* 누적 — 소비자와 대상이 다르다. 외부 수집기를 붙일 계획이 없는 한 대체 불가 |
| 8 | dlc 규모 gate·병렬 규약 (§3·§5) | `workflowSizeGuideline` 설정 (v2.1.219 · 2026-07-24), subagent 상한 env 3종 (v2.1.212 · 2026-07-17 / v2.1.217 · 2026-07-21 / v2.1.219 · 2026-07-24), nested subagent 기본 depth 3 (v2.1.219 · 2026-07-24) | `watch` | 네이티브는 *상한(cap)*, 자작은 *언제 무엇을 돌릴지(정책)* 라 층이 다르다. 다만 "규모 판정"이라는 축 자체가 네이티브에 생긴 것은 처음이라 감시 대상 |

`retire` 판정: **1건** (1b, 2026-08-12 실측 확정 — 2026-09-27 `keep` 으로 정정, 아래 "1b 정정"). 나머지 창(v2.1.186~v2.1.222) 기준 변동 없음.

### 1b 실측 (2026-08-12) — 이 축의 첫 `retire`

정본 changelog 는 v2.1.222 를 "isolation now applies file edits" 라고만 적고 **차단인지 리다이렉트인지·범위가 어디까지인지 밝히지 않는다**. 그래서 문서가 아니라 관측으로 갈랐다. worktree 세션에서 main checkout 경로에 Write 를 시도한 결과:

| 편집 대상 | 자작 guard 판정 (hook 직접 호출) | 네이티브 판정 (실제 Write) |
|---|---|---|
| `<main>/plans/native-isolation-probe.md` | **ALLOW** (repo-root `~/.claude` 의 `plans/` 는 §10 핸드오프라 의도적 허용) | **DENY** |
| `<main>/scripts/native-isolation-probe.txt` | DENY | **DENY** |

네이티브 거부 문구: *"This session is isolated in the worktree … Edit the worktree copy of this file instead of the shared-checkout path."* — 이 문자열은 `scripts/`·`settings.json` 어디에도 없다(자작 hook 이 아니다).

**결론**: 네이티브 ⊇ 자작 ②이고 진상위집합이다 — 자작이 *허용*하는 `plans/` 까지 네이티브가 막는다. ②는 더 이상 아무것도 추가로 막지 못하므로 `retire`. (→ 2026-09-27 정정: EnterWorktree 세션에서만 참이었다 — 아래 "1b 정정")

> [!conflict] 다만 "더 넓다"가 곧 "더 낫다"는 아니다. 자작 ②는 `plans/`·`projects/`·`settings.local.json` 을 **의도적으로 예외**로 뒀다 — worktree 복사본이 없는 전역·핸드오프 상태라 main 경로 편집이 정상이기 때문이다. 네이티브에는 그 예외가 없어 **worktree 세션에서 §12 memory 적립(`projects/…/memory/`)이 불가능**하다(2026-08-12 실측: "Edit the worktree copy of this file instead" — 그런데 그 파일엔 worktree 복사본이 존재하지 않는다). 이는 자작 guard 를 되살려서는 풀리지 않는다(네이티브가 먼저 막는다) — **별개의 workflow 마찰**로 추적한다. `retire` 판정 자체는 영향 없음.

**제거 시 함께 사라지는 것**(별도 작업의 검토 항목): `guard-worktree-deny` telemetry 신호 · 구버전 Claude Code(<2.1.222)에서의 보호 · `guard-worktree-edit.test.js` 의 ② 케이스. 기능 ①(1a)은 남으므로 파일 전체 삭제가 아니라 분기 제거다. (→ 2026-09-27: 제거하지 않고 좁혔다 — 아래 "1b 정정")

## 재판정 (checked 2026-09-27 · 조회 창 v2.1.223 ~ v2.1.283)

조회 범위: GitHub `CHANGELOG.md` 원문을 로컬로 받아 v2.1.223~283 구간(버전 헤더 50개, 2,326줄 — 230·242·244·249·253~256·262·264·279 는 헤더가 없다)을 한 줄도 빼지 않고 읽었다. 처음에는 WebFetch 로 조회했다 — docs changelog 페이지는 v2.1.275 부근에서 잘렸고, GitHub 버전 비교 diff 도 요약 모델을 거쳐 버전 귀속이 흔들렸다. 그 조회가 "전문"이라 했던 v2.1.265~283 에서도 리뷰가 누락(v2.1.271·280)을 잡아, 원문을 받아 전수로 다시 했다. 날짜는 npm 게시 시각(UTC). 판정은 `/improve` 초안을 사용자가 승인했다(2026-09-27). **네이티브가 부품을 대체한 경우는 없고** 기존 행의 판정은 모두 그대로다. 아래는 창 안에서 근거가 바뀐 행과 2026-08-06 뒤에 생긴 부품이다.

### 기존 행 — 창 안의 변화 (1a 는 해당 항목 없음)

| # | 창 안의 네이티브 변화 (버전 · 날짜) | verdict | 근거 |
|---|---|---|---|
| 1b | background 세션이 `git worktree add` 로 만든 worktree 안 편집 허용 (v2.1.251 · 2026-08-28), worktree 격리 세션이 git 을 건드리지 않는 Bash 루프·`$VAR`·`"$(…)"`·heredoc 을 거부하던 것 수정 (v2.1.257 · 2026-09-01), 흔한 Bash 루프·xargs 파이프라인·launcher 로 감싼 명령 거부 수정 (v2.1.259 · 2026-09-02), 특정 중첩 셸 확장을 받아들이던 것을 거부로 바꿈 (v2.1.274 · 2026-09-16) | `retire` 유지 | 네이티브가 격리 경계를 계속 다듬고 있고 자작 ②가 추가로 막는 것은 여전히 없다. **2026-09-27 기준 미이행** — `scripts/guard-worktree-edit.js` 의 worktree 밖 `deny` 분기가 남아 있다(제거는 intent 단위 `guard-deny-removal`). → 같은 날 `keep` 정정(아래 "1b 정정") |
| 1b 콜아웃 | git repo 의 하위 디렉토리에서 시작한 세션의 auto-memory 편집이 sensitive-file 쓰기로 막히던 것 수정 (v2.1.283 · 2026-09-25) | — | 위 `[!conflict]` 의 worktree 세션 memory 쓰기 막힘과 시작 조건·차단 경로가 다르다 ⚠️ — 해소 근거가 아니다. 2.1.283 에서 재실측하기 전까지 memory 적립은 main 복귀 후(CLAUDE.md §3-1). → 2.1.283 재실측에서도 막힘(아래 "1b 정정") |
| 2 | `/commit-push-pr` 이 `--force`·`--amend`·`--no-verify` 등 위험 플래그를 자동 승인하지 않음 (v2.1.229 · 2026-08-12), `claude agents`·`claude rm` 이 로컬 default 브랜치에 머지된 worktree 세션을 지우게 됨 (v2.1.248 · 2026-08-27), background 세션이 도는 동안 worktree lock 을 잡아 정리·`git worktree remove` 가 건너뜀 (v2.1.248 · 2026-08-27) | `watch` 유지 | 네이티브의 background 세션 정리가 CLAUDE.md §8(a) 의 "로컬 main 머지도 merged" 판정과 같은 논리를 갖게 됐다. plan 동기화·worklog·머지는 여전히 자작에만 있다. lock 은 `/e` 7단계 정리가 background 세션이 잡은 worktree 에서 실패할 수 있다는 뜻 |
| 3 | `/review` 가 `/code-review` 의 별칭이 됨 (v2.1.223 · 2026-08-05), `/code-review`·`/ultrareview`·`[Code Review]` 개선 다수 | `watch` 유지 | 외부 모델 교차검증은 창 전체에 없다 — `retire` 조건이 서지 않았다 |
| 4 | `.worktreeinclude` 의 `**/` 패턴 수정 (v2.1.239 · 2026-08-21), `/cd` 가 이동한 디렉토리의 settings·hooks·skills 를 바로 적용 (v2.1.246 · 2026-08-25), background retention sweep 이 사용자가 만든 `.claude/worktrees/` worktree 를 지우던 것 수정 (v2.1.246 · 2026-08-25) | `keep` 유지 | 요청 → 개발사이클 진입을 대체하는 변경은 없다. `.worktreeinclude` 는 `/wt` 의 `.env`·`settings.local.json` 복사(`skills/wt/SKILL.md` request §3 4단계)와 목적이 같지만 Claude Code 가 만드는 worktree(`--worktree`·subagent·desktop 병렬 세션 — worktrees 문서)에만 적용된다. `/wt` 는 `git worktree add` 로 직접 만들어 지금 경로로는 대체할 수 없고, 대체하려면 생성을 네이티브로 옮겨야 한다 |
| 5 | MEMORY.md 절단 경고가 잘린 줄 수와 시작 위치를 알림 (v2.1.268 · 2026-09-10), session cleanup 이 memory 폴더 내용을 지우던 것 수정 (v2.1.228 · 2026-08-11) | `keep` 유지 | 저장소 쪽 변경이라 인덱스 운용 규약과 겹치지 않는다 |
| 6 | Stop **prompt** hook 이 반복 차단 때 프롬프트 전문 대신 500자 라벨을 보냄 (v2.1.274 · 2026-09-16), Bash 가 바꾼 파일의 diff 를 Bash 도구 결과에 붙임 — 기본은 auto·bypass 모드에서 Claude Code 가 Bash 편집을 시킨 경우만, 설정 `bashEditDiffEnabled` 로 모든 권한 모드 (v2.1.269 · 2026-09-11; hooks 문서: PostToolUse 가 `tool_response.bashEditDiff` 로 받음, gitignored·submodule 파일 제외), hook 으로 이어 가는 `/goal` 수정 다수 | `watch` 유지 | 이 repo 의 Stop hook 은 `type: command` 라 500자 라벨과 무관하다. `/verify` 가 프로젝트 검증으로 넓어진 항목은 창에 없다. `bashEditDiffEnabled` 는 early-stop 이 Bash 편집을 못 보는 문제([[workflow-failures]])의 감지 수단 후보 — 감사 묶음 단위 `ledger-bash-edits` 가 쓸 수 있는지 본다 |
| 7 | OTel 에 repo 속성 `OTEL_METRICS_INCLUDE_REPOSITORY` (v2.1.269 · 2026-09-11), `tool.output` 확장 (v2.1.283 · 2026-09-25), `/insights` 의 auto mode 권고 (v2.1.281 · 2026-09-23) | `keep` 유지 | 네이티브 telemetry 는 여전히 외부 수집기가 전제이고 hook 판정 신호를 담지 않는다 |
| 8 | Workflow 동시 agent 상한 `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` (v2.1.269 · 2026-09-11), `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` (v2.1.257 · 2026-09-01), subagent fork 기본 켜짐·비-teammate spawn 백그라운드 기본화 (v2.1.232 · 2026-08-13) | `watch` 유지 | 네이티브는 상한과 실행 방식, 자작은 언제 무엇을 돌릴지의 정책이다. 백그라운드 기본화로 subagent 결과를 기다리는 턴이 늘어 early-stop 중간 턴 오탐([[workflow-failures]])이 구조적으로 잦아진다 |

### 1b 정정 (2026-09-27 표적 재실측) — `retire` → `keep`

intent 단위 `guard-deny-removal` 의 착수 조건으로 2026-08-12 관측표를 2.1.283(auto 모드)에서 다시 쟀다. changelog delta 조회가 아니라 표적 실측이라 `checked` 는 그대로다(운영 규칙).

| 세션 | main checkout 편집 시도 | 네이티브 판정 | 자작 ② |
|---|---|---|---|
| EnterWorktree 로 들어간 세션 | `plans/`·`scripts/`·`projects/…/memory/` 새 파일 Write, `README.md` Edit, `scripts/*.ipynb` NotebookEdit | 전부 **DENY** — 도구 검증 단계 오류(`tool_use_error`)라 PreToolUse hook 까지 가지 않는다(`scripts/` 도 자작 문구가 아니라 네이티브 문구) | 도달하지 않음 |
| worktree 디렉토리에서 바로 시작한 세션(EnterWorktree 미경유 — 임시 repo 의 linked worktree `.claude/worktrees/wt1` 에서 headless `claude -p --permission-mode acceptEdits`) | 새 파일 Write | hook 을 끄면 **생성됨**(2회 재현) — 격리 없음 | hook 을 켜면 **DENY** |

두 줄은 권한 모드(auto 대 acceptEdits)와 대화 방식(interactive 대 headless)이 다르다. 첫 줄의 거부는 권한 판정이 아니라 도구 검증 단계에서 나서 모드와 무관할 것으로 본다 ⚠️. 대장 1b 가 인용한 v2.1.222 의 "모든 세션 타입"은 interactive·background·SDK 같은 세션 **종류**를 가리키는 것으로 읽히고, 격리는 여전히 worktree 에 들어간 경로(EnterWorktree 등)가 켠다 — 이 실측과 모순되지 않는다 ⚠️. `~/.claude` 에서는 두 번째 줄의 시도가 격리가 아니라 "sensitive file" 권한 요청으로 멈춘다 — `~/.claude` 경로 자체의 민감 판정이라 다른 repo 에는 없는 보호다. 잰 것은 이 두 종류뿐이다 — `claude --worktree` 로 시작한 세션, subagent `isolation: worktree`, 격리된 세션을 resume 한 경우는 재지 않았다 ⚠️.

자작 ② 의 실제 발동 이력(`telemetry/dlc-signals.jsonl` 의 `guard-worktree-deny`, 2026-09-27 이전 7행)은 오탐 4건과 2026-08-12 실측의 hook 직접 호출 3건(`session_id: probe`)이다. 오탐은 `~/.claude/jobs/<id>/tmp/` 임시파일 1건(2026-07-16)과, 다른 repo 세션이 `ExitWorktree` 로 격리를 벗어난 뒤 Bash `cd` 로 cwd 가 worktree 로 돌아간 상태에서 main 의 gitignored plan 을 고치려던 3건(2026-09-14 — 편집이 worktree 사본으로 옮겨가 worktree 를 지울 때 사라질 위치였다). 옳게 막은 기록은 없고, 오탐 4건은 전부 gitignored 경로다. 2026-09-27T10:23 행은 위 표 두 번째 줄의 hook 켠 실측이 남긴 **측정 행**이다 — 실제 발동으로 세지 않는다.

| # | 자작 컴포넌트 | 네이티브 대응 | verdict | 근거 |
|---|---|---|---|---|
| 1b 정정 | `scripts/guard-worktree-edit.js` 기능 ② — worktree 밖 `deny` 를 **main checkout 의 추적 파일 편집과 새 파일(아직 없고 gitignored 아님) 생성**으로 좁힘(2026-09-27, `guard-deny-removal`) | EnterWorktree 세션은 worktree 격리가 모든 편집 도구를 hook 보다 먼저 거부한다. worktree 디렉토리에서 시작한 세션은 격리되지 않는다(다른 세션 종류는 미측정 ⚠️) | `keep` | 격리되지 않은 채 cwd 가 worktree 안인 세션(worktree 디렉토리에서 시작, `ExitWorktree` 뒤 `cd` 복귀 등)은 ② 가 유일한 보호라 제거하지 않고, 오탐이 난 gitignored 경로와 main 에만 있는 기존 untracked 파일, git common dir `.git/` 을 풀었다 |

> [!conflict] 2026-08-12 의 "네이티브 ⊇ 자작 ②, 진상위집합"은 **EnterWorktree 세션에서는** 참이지만 worktree 디렉토리에서 시작한 세션에서는 거짓이다 — 그날 실측은 EnterWorktree 세션만 쟀고, 격리가 세션이 worktree 에 들어간 경로에 걸린다는 점을 보지 못했다. 위 판정 표 1b 의 `retire` 와 이 창 1b 의 "`retire` 유지"는 지우지 않고 이 정정 행이 대체한다. 1b 콜아웃의 worktree 세션 memory 쓰기 막힘은 2.1.283 에서도 그대로다(위 관측 첫 줄) — v2.1.283 의 auto-memory 수정은 해소 근거가 아니었다.

### 2026-08-06 뒤에 생긴 부품

| # | 자작 컴포넌트 | 네이티브 대응 (버전 · 날짜) | verdict | 근거 |
|---|---|---|---|---|
| 9 | `skills/commit-check` — 미게시 커밋의 fixup·WIP 합치기와 목적 분리(plumbing 재조립, 승인 후) | 없음 | `keep` | 커밋 이력 재구성 기능이 창에 없다 |
| 10 | SessionStart `scripts/session-start-pull.sh`(main 자동 ff) · `scripts/session-brief.js`(진행 중 plan·미머지 브랜치 브리프) | SessionStart resume hook 입력에 세션 신선도·재캐시 비용 추가 (v2.1.251 · 2026-08-28) | `keep` | 네이티브 추가분은 hook 입력이지 저장소 동기화·작업 브리프가 아니다 |
| 11 | `plans/<date>-<slug>/` 핸드오프(CLAUDE.md §10) — 세션·Claude↔Codex 간 공유 | plan mode UI 수정뿐 | `keep` | 세션을 넘어 공유되는 plan 저장소가 네이티브에 없다 |
| 12 | `scripts/dlc-task-router.js` — UserPromptSubmit 작업 유형 힌트 | 대체하는 기능은 없음. 대신 **의존하던 동작이 바뀌었다**: auto mode 의 subagent 보고가 전용 hand-back 호출로 바뀜 (v2.1.271 · 2026-09-14) — 그 보고가 별도 user 턴으로 들어와 라우터가 오발동하고 장부를 리셋한다([[claude-code-hook-notification-turns]]). 같은 계열: 턴 사이에 오는 background 작업 알림을 모델에 `<system-reminder>` 로 감싸 보냄 (v2.1.234 · 2026-08-17), 자기 subagent 메시지를 "이 세션 안의 worker" 로 알림 (v2.1.251 · 2026-08-28), subagent 결과를 표시 헤더 아래 들여써서 전달 (v2.1.277 · 2026-09-18), hand-back 메시지의 내부 출처 preamble 표시 수정 (v2.1.280 · 2026-09-22). UserPromptSubmit 입력에 턴 출처를 알리는 필드를 추가한 항목은 없다 | `keep` | 대체가 아니라 파손이라 판정은 그대로다. 수정은 묶음 `improve-followups` 의 `router-agent-message` |
| 13 | git pre-commit·pre-push hook — 비밀 스캔, worktree 에서 main push 차단 | 없음 | `keep` | 네이티브 비밀 스캔·push 차단이 창에 없다 |
| 14 | `skills/improve` — 자산 크로스참조·신호 랭킹·이 대장의 재판정 | `/doctor prompt-audit`(`/checkup prompt-audit`) — CLAUDE.md·skills·agents·commands 의 옛 모델용 프롬프트 패턴 점검, stale 경로·명령과 모순 지침을 보고 앞에 둠 (둘 다 v2.1.283 · 2026-09-25); `/skill-doctor` — 안 쓰는 skill 과 그 컨텍스트 비용 (v2.1.261 · 2026-09-04) | `watch` | 점검 대상 자산이 겹친다(`/skill-doctor` 는 `improve.sh deep` ⑪ 사용량 카운트와도). 신호 원천(프롬프트 패턴 vs hook 신호 빈도)이 달라 대체는 아니다 — 한 번 돌려 `/improve` 점검 1~6·⑪·의미 점검과 겹치는 범위를 실측한다 |
| 15 | notify hook · `statusline.js`(Claude·Codex 사용량 표시) | statusline 입력 `rate_limits` 필드 수정 (v2.1.243 · 2026-08-24)·`rate_limits.spend_limit` 추가 (v2.1.251 · 2026-08-28), Notification hook 이 Desktop·VS Code 권한 프롬프트에서 안 뜨던 것 수정 (v2.1.233 · 2026-08-14) | `keep` | `statusline.js` 는 이미 네이티브 `rate_limits` 입력을 읽는 소비자라 중복이 아니고, Codex 사용량은 네이티브에 없다. notify 는 네이티브 Notification 이벤트를 쓰는 hook 이다 |

`retire` 판정: 1건(1b, 미이행 — 같은 날 표적 재실측으로 `keep` 정정, 위 "1b 정정"). 이번 창의 신규 `watch` 1건(14).

### 창 안의 설정·hook 영향 (판정 아님)

- `!` 로 시작하는 deny·ask 규칙이 자기 settings 소스 안에서만 적용된다 (v2.1.269 · 2026-09-11) — 이 repo settings 에 `!` 규칙이 없어(2026-09-27 확인) 영향 없음.
- auto mode 의 subagent 보고가 전용 hand-back 호출로 바뀜 (v2.1.271 · 2026-09-14) — 위 12행. 창 안의 변경 중 이 repo 의 hook 동작을 직접 깨뜨린 것은 이것이다. 8행의 백그라운드 기본화는 hook 을 깨뜨리지는 않았지만 early-stop 대기 턴 오탐을 늘렸고, 4·5행의 worktree·memory 삭제 버그는 창 안에서 이미 고쳐졌다.
- Bash 권한 규칙의 중간 `:*` 가 settings 에서 무시되던 것 수정 (v2.1.282 · 2026-09-24) — 이 repo `permissions.ask` 72개에 중간 `:*` 가 없어(2026-09-27 확인) 영향 없음.
- custom subagent 가 CLAUDE.md 없이 돌게 하는 frontmatter `omitClaudeMd` (v2.1.271 · 2026-09-14), 큰 CLAUDE.md 시작 경고가 지침 파일을 합산 (v2.1.281 · 2026-09-23) — 아래 `claude-md-dedupe` 와 reviewer 컨텍스트 비용에 관련.
- `PreModelSwitch`·`PostModelSwitch` hook 이벤트 추가 (v2.1.251 · 2026-08-28).
- `claudeMdExcludes`(절대경로 glob, 모든 settings 계층, 배열 병합 — memory 문서) — changelog 에는 추가 시점 기록이 없고 창 안의 symlink 매칭 수정(v2.1.239 · 2026-08-21)만 있다. 이 repo 는 2026-09-25 부터 `AGENTS.md` 제외에 쓰고 있다([[claude-code-agents-md-loading]]). worktree 세션에서 `CLAUDE.md` 가 전역 사본과 worktree 사본으로 두 번 주입되는 비용(42KB)을 줄일 수단 후보 — intent 단위 `claude-md-dedupe`.

## 맥락 (판정 아님)

- **`ultraplan` 기능 제거** (v2.1.222 · 2026-08-04) — 네이티브도 과한 오케스트레이션 계층을 걷어내는 방향. 자작 하네스의 오케스트레이션 축이 흡수되는 흐름과 같은 신호로 읽는다.
- **`/agents` 위저드 제거** (v2.1.198 · 2026-07-01) — 관리 UI 대신 파일 직접 편집으로 회귀. 자작이 `agents/*.md` 를 파일로 관리하는 방식과 같은 방향.

