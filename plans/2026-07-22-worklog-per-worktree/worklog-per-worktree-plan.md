---
title: worklog-per-worktree — 같은 티켓의 worktree 별로 worklog 항목을 분리해 시간이 덮이지 않게
status: in_progress
started: 2026-07-22
updated: 2026-07-22
---

# Goal

같은 Jira 티켓 prefix 를 가진 worktree 가 여럿일 때(`CSTP1-1234-abc`, `CSTP1-1234-def`),
각 worktree 의 AI 작업시간이 **서로 덮지 않고** 티켓 총 작업시간에 누적되게 한다.

# Progress

- 2026-07-22 원인 확정: 마커가 `(ticket, date)` 뿐이라 같은 티켓의 두 worktree 가 동일 마커로
  충돌 → `upsert_worklog` 가 기존 항목을 찾아 `update_worklog` 로 **치환**(합산 아님).
- 2026-07-22 등록 이력 조사: `~/.jira-kit/` 없음 · `JIRA_*` env 없음 · repo `.env` 없음 →
  `config.jira is None` 이라 실제 Jira 등록이 발생한 적 없음. 스킬 도입일도 오늘(`aae9d6d`).
  (단, 과거 셸 세션의 env var 는 사후 반증 불가 — 그래서 legacy 경로는 "중단"으로 설계.)
- 2026-07-22 설계 결정(사용자): worktree 별 별도 worklog 항목.
- 2026-07-22 plan-reviewer(+codex 0.144.4 병행) 검토 → blocker 4건 수용, 아래 Decisions 갱신.
- 2026-07-22 구현 + 테스트 21개 통과. code-reviewer(+codex 병행) 검토 → CONFIRMED Major 2건
  (`adf_lines` 가 hardBreak/codeBlock/heading·후행공백에서 마커 유실 → 조용한 이중계상 /
  legacy 중단 메시지의 복구 안내가 그대로 따르면 이중계상) + Minor 5건 수용해 fix loop 1회.
- 2026-07-22 mutation 검증: 줄 정확일치 → 부분문자열 되돌리면 7건 Red, hardBreak/codeBlock/
  heading 처리 제거하면 3건 Red — 테스트가 두 회귀를 실제로 잡는 것 확인.
- 2026-07-22 최종 검증 통과(신규 21 + 기존 Python 24 + node 8종 + plan-lint + JSON).
  커밋 `6683d63` → push → PR #101 (https://github.com/yoon627/claude-config/pull/101).

# Next

PR #101 리뷰·머지. 머지되면 `status: done` 으로 바꾸고 worktree(`worklog-ticket-union`) 정리.
그 다음 Deferred 의 `settings.json` pull 훅 문제를 별도 브랜치에서.

# Decisions

- **worktree 별 별도 worklog 항목** — 마커에 worktree 이름을 넣어 각 worktree 가 자기 항목만
  갱신한다. Jira 티켓의 `timespent` 는 worklog 항목 합계라 누적은 Jira 가 한다.
  (이유: 사용자 워크플로가 "worktree 를 옮길 때 그 worktree 시간을 기록"이라 호출 단위 = worktree.
  등록 시점에 티켓 전체를 재계산하지 않으므로 지운 worktree 항목이 보존되고, 재실행 멱등성도
  worktree 단위로 유지된다.)
- **티켓 단위 interval union 은 채택하지 않음** — 초기 제안이었으나 사용자 모델과 어긋나 폐기.
  (이유: 등록마다 그 티켓의 모든 worktree 를 재수집해야 하고, worktree 를 지우면 집계에서 빠져
  **기존 등록값이 축소 갱신**되는 회귀가 생긴다. 대가로 두 worktree 를 같은 시각에 병렬로 돌린
  경우 겹치는 시간이 이중 계상되는 것은 사용자가 수용 — "일한 만큼"으로 본다.)
- **마커 매칭을 부분문자열 → ADF 문단(줄) 정확일치로 전환** (plan-reviewer B1).
  `adf_to_text` 가 문단을 **구분자 없이** 이어붙이고(`markers.py:30`) 매칭이 `marker in text`
  (`markers.py:42-45`)라, 괄호 구분자를 넣어도 ① worktree 이름에 `)` 가 있으면 충돌 ② 사용자
  `--comment`·Jira UI 수동 편집 텍스트가 마커를 포함하면 오매치 ③ 두 문단에 걸쳐 마커가 우연히
  합성되는 경우를 못 막는다. `adf_lines()` 로 문단 단위 줄을 뽑아 **줄 정확일치**로 바꾼다.
  `adf_from_text` 가 줄→문단으로 만들므로(`jira_client.py:82-92`) 라운드트립이 정확히 복원된다.
  부수 효과: legacy 감지도 정확해진다(구 마커 줄과 정확히 같은 줄만 legacy).
  - 초안에 근거로 적었던 "`-abc` 가 `-abc-2` 항목에 걸린다"는 **사실이 아니다** — 닫는 `)`
    때문에 부분문자열이 아니다(code-reviewer 가 실행으로 반증). 유효한 근거는 위 ①②③.
- **정확일치는 놓치는 쪽(false-negative)이 더 위험하다** — code-reviewer CONFIRMED Major.
  마커를 못 찾으면 새 항목을 만들어 그날 시간이 **이중계상**되는데, 오매치와 달리 조용하다
  (옛 부분문자열 매칭 대비 회귀). 그래서 `adf_lines` 는 Jira UI 편집이 만드는 `hardBreak`
  (→ 줄바꿈)·`codeBlock`·`heading` 을 텍스트 블록으로 처리하고, 비교 전 줄 양끝 공백을 뗀다
  (Jira 가 ADF 를 정규화해 돌려주는지 실호출 검증이 불가능한 점도 이 `strip()` 이 흡수).
- **빈/개행 worktree 이름은 `worklog_marker` 에서 `ValueError`** — 빈 이름은 구 형식과 같은
  마커가 돼 legacy 검사에 자기가 걸려 영구 중단되고, 개행은 마커를 두 줄로 쪼개 영영 못 찾게
  만들어 실행마다 새 항목이 생긴다. 둘 다 조용한 이중계상이라 생성 지점에서 막는다.
  legacy 형식 생성은 `legacy_worklog_marker()` 로 분리해 "worktree 를 빠뜨리면 조용히 구 형식"
  경로 자체를 없앴다. 괄호·공백·비ASCII 이름은 파싱하지 않으므로 **방어하지 않는다**.
- **마커 형식 `[jira-kit] worklog <ticket> <date> (<worktree>)`** — 구 마커를 prefix 로 포함하는
  형식을 **유지**한다. (이유: 롤백 시 구버전 코드는 부분문자열 매칭이라 새 항목을 인식한다 —
  1건이면 정상 갱신, 2건+면 기존 `worklog 마커 중복` 에러로 **큰 소리로** 멈춘다. 반면 codex 가
  제안한 버전 접두사(`[jira-kit:v2]`)로 바꾸면 롤백한 구 코드가 아무것도 못 찾아 3번째 항목을
  **조용히** 생성해 이중계상된다 — 조용한 손실보다 시끄러운 실패가 낫다.)
- **구 마커(worktree 없는 형식) 항목 발견 시 경고가 아니라 `JiraError` 로 그 (ticket,date) 중단**
  (plan-reviewer B2). (이유: 구 항목이 어느 worktree 것인지 알 수 없다. 새로 만들면 구 항목과
  이중계상, 건너뛰면 그날 기록 누락 — 어느 쪽도 옳지 않다. 같은 모듈이 이미 "마커 중복 2건+ →
  중단"(`worklog_register.py:44-46`) 정책을 쓰므로 일관된다. `/e` 는 worklog 실패를 비차단으로
  처리하므로(`skills/e/SKILL.md`) 마무리 흐름은 안 막힌다.) legacy 탐지에도 **author scoping**
  을 적용한다 — 안 하면 타인 항목 때문에 영구 중단된다.
- **scope = 선택된 `Worktree` 의 `Path(wt.path).name`** (`Path.cwd()` 아님, plan-reviewer B4).
  (이유: `select_worktrees` 는 positional `name` 으로 현재 cwd 가 아닌 worktree 를 지정할 수 있어
  cwd 기반이면 조용히 틀린 scope 가 박힌다.) 티켓을 브랜치 fallback 으로 잡았어도 scope 는 항상
  디렉토리 이름 — 출처와 무관하게 일관.
  - **rename** → 새 scope 로 새 항목, 옛 항목은 고아로 잔존. 세션 로그도 경로 slug 기준이라
    옛 시간은 새 경로에서 안 잡히므로 총합은 대체로 보존. **허용**.
  - **삭제 후 같은 이름 재생성** → slug 가 같아 옛 세션 로그가 다시 잡히고 같은 항목을 갱신.
    항목 1개 유지. **허용**.
  - **다른 레포에 같은 이름 worktree + 같은 티켓** → 마커 충돌로 원래 버그가 축소 재현.
    현재 티켓 패턴이 단일 프로젝트(`CSTP1-\d+`)이고 1인 로컬 도구라 **수용**(방어 안 함).
- **삭제된 worktree 의 worklog 항목은 Jira 에 영구 잔존**한다(정정 수단 없음). 의도된 결과이며
  SKILL.md 에 명시한다.

# Key Files

- `skills/jira-worklog/jira_kit/markers.py` — 마커 생성 + `adf_lines` 줄 정확일치 전환.
- `skills/jira-worklog/jira_kit/worklog_register.py` — upsert 에 worktree scope · legacy 중단.
- `skills/jira-worklog/jira_worklog.py` — `_register`/`process` 에 scope 배선, dry-run 출력.
- `skills/jira-worklog/SKILL.md` — upsert 설명(49행) worktree 단위로 갱신 + 삭제 잔존 명시.
- `skills/e/SKILL.md` — worklog 단계 "그날 항목 upsert" 문구 → "그 worktree 의 그날 항목".
- `README.md` — `skills/jira-worklog/` 가 Components/Layout 에 **미등재**. docdrift 게이트 대상.
- 신규 `skills/jira-worklog/test_worklog_scope.py` — stdlib unittest, 수동 실행.
- `skills/jira-worklog/jira_kit/session_time.py` — 변경 없음(worktree 단위 수집이 이미 맞음).
- `skills/jira-worklog/jira_kit/jira_client.py` — 변경 없음(`adf_from_text` 라운드트립 근거).

# Blockers

# Acceptance

1. 같은 티켓·같은 날, worktree `abc` 항목이 있는 상태에서 `def` 로 upsert 하면 **새 항목이
   생성되고 `abc` 항목은 건드리지 않는다**.
   - 검증: `add_worklog`/`update_worklog` 를 `worklog_register` 네임스페이스에서 patch.
   - 통과 기준: `add_worklog` 1회 호출 + `update_worklog.assert_not_called()`.
     (Red 는 시그니처 변경 때문에 `TypeError` 로 났다 — "`update_worklog` 가 불려서 Red" 라는
     초안 서술은 부정확. 덮어쓰기 회귀는 아래 mutation 검증으로 별도 확인.)
2. 같은 worktree 재실행은 자기 항목만 갱신 — `created` → 같은 시간이면 `unchanged`,
   다른 시간이면 `updated`(그 항목 id 로만).
3. 마커 유사 텍스트가 **본문에 있는** 항목을 자기 것으로 오인하지 않는다.
   - 검증: `--comment` 에 마커 문자열을 넣은 항목·마커가 다른 문단과 붙는 케이스를
     `adf_from_text` 로 만든 **실제 ADF** 로 구성.
4. 구 마커(worktree 없는) **본인** 항목이 있으면 `JiraError` 로 중단한다. 타인의 구 마커 항목은
   중단 사유가 되지 않는다.
5. `my_account_id` falsy 면 기존대로 중단(회귀 방지).
6. dry-run 이 이번 실행이 쓸 **scope·마커 문자열**을 출력한다(Jira 조회 없이 — 토큰-free 계약
   유지, created/updated 예측은 하지 않는다).
7. 문서 동기화: `skills/jira-worklog/SKILL.md` upsert 설명, `skills/e/SKILL.md` 문구,
   `README.md` 에 jira-worklog 등재.

# Review Disposition

- B1 부분문자열 매칭 → **fix** (줄 정확일치).
- B2 legacy 경고만 → **fix** (JiraError 중단 + author scoping).
- B3 rollback 미기재 → **fix** (Decisions 에 기록, 마커 형식은 prefix 포함 유지 — codex 의
  버전 접두사 제안은 **false-positive/wontfix**: 롤백 시 조용한 이중계상 유발).
- B4 scope identity 미정의 → **fix** (`Path(wt.path).name`).
- codex "동시 실행 race" → **wontfix** (1인 로컬 CLI, 오히려 이번 변경으로 다른 worktree 동시
  등록은 마커가 달라 안전해짐. 원자성 없음은 알려진 한계로 남김).
- codex `--allow-legacy-overlap`/`--migrate-legacy-to` 플래그 → **wontfix** (1인 도구에 과한 표면적).
- Acceptance 1·3·6 지적 → **fix** (위 Acceptance 반영).

code-reviewer(2026-07-22, +codex 병행):
- Major ① `adf_lines` 가 hardBreak/codeBlock/heading·후행공백에서 마커 유실 → **fix**
  (hardBreak → 줄바꿈, `_TEXT_BLOCKS` 에 heading/codeBlock, 비교 전 `strip()`).
- Major ② legacy 중단 메시지가 이중계상 유도 → **fix** (교체할 정확한 마커 문자열과 두 선택지의
  결과를 메시지에 담고, 테스트로 그 문자열 포함을 강제).
- Minor 문서의 `-abc`/`-abc-2` 예시 오류(4곳) → **fix**.
- Minor 테스트가 scoped 정확일치를 1건만 지킴 · `adf_lines` 단위테스트 0개 → **fix**
  (`AdfLinesTest` 8건 추가, prefix 테스트를 `test_marker_embedded_in_a_longer_line...` 으로 교체,
  mutation 2종으로 회귀 포착 확인).
- Minor 빈/개행 scope 미검증 → **fix** (`ValueError` + `legacy_worklog_marker` 분리).
- Minor dry-run 마커가 `days[0]`(가장 오래된 날짜)만 표시 → **fix** (날짜별 줄에 실제 마커 출력).
- Minor `worktree` positional → **fix** (keyword-only).
- codex "worktree basename 이 불변 ID 가 아니다"(타 레포 동명) → **wontfix**
  (Decisions 에 수용 기록. 티켓 패턴이 단일 프로젝트이고 1인 로컬 도구).
- codex "worktree 이름의 Jira 노출(PII)" → **wontfix** (티켓 prefix 규약 이름, 1인 사용).
- reviewer open question "Jira 가 ADF 를 정규화해 돌려주는지 실호출 미검증" → **defer**
  (토큰 미설정이라 검증 불가. `strip()` 비교로 위험을 흡수했고, 실등록 후 재확인 대상).

# Deferred

- `settings.json` SessionStart pull 훅이 dirty working tree 에서 조용히 skip 되는 문제
  (`|| true` 가 원인 삼킴). 사용자가 "지금 같이 고쳐달라" 했으나 무관 변경이라 **별도 브랜치**로
  분리하기로 합의 — 이 작업 종료 후 진행.
- Jira UI 에서 코멘트를 수동 편집해 마커 문단이 사라지면 다음 실행이 새 항목을 만든다(기존 동작,
  이번 변경으로 악화되지 않음). SKILL.md 한 줄 문서화로만 대응.

# Workflow Findings
