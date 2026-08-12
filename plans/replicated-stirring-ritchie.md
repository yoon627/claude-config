# 인터뷰 고정 항목 제거 — agent 가 정하고 사람이 확인하는 구조로

> **이 파일은 세션 재시작용 핸드오프다.** effort 를 max 로 올리려면 세션을 다시 시작해야 하는데,
> 그러면 아래 조사 결과가 사라진다. 재시작 후 이 파일부터 읽고 Phase 2(설계)로 이어가면 된다.
>
> 작업 시작 시 repo 규약(`~/.claude/CLAUDE.md` §10)에 맞춰
> `~/Repos/knowledge_base/.claude/plans/<YYYY-MM-DD>-dynamic-interview-contract/dynamic-interview-contract-plan.md`
> 로 옮길 것. 그 repo 의 `plans/` 는 tracked 라 작업 브랜치와 함께 커밋된다.

---

# Context

운영자가 "이 컴퓨터의 보안을 점검하고 싶다"고 입력했다. 인터뷰는 `target_description='이 컴퓨터'`
까지 정상 인식했지만 `interface_hints` 가 비었고, 확정 순간
`CompleteInterview.interface_hints` 검증이 터져 **502 "오류가 발생했습니다"** 만 나왔다.
운영자는 무엇이 빠졌는지 알 수 없어 4번 재시도했다(재시도로는 절대 안 풀리는 상태였다).

즉시 조치는 이미 끝났다 — 확정 실패를 **422 + 빠진 항목 이름**으로 바꿨다
(`61b9d27`, `origin/main` 반영, 실물 확인: `422 | 아직 확인되지 않은 항목이 있습니다: 연결 방식·프로토콜`).

이 plan 은 그 다음, 운영자가 제기한 **구조 문제**를 다룬다.

## 사용자가 정한 두 방향 (2026-08-07)

1. **"claude 처럼 정해야 할 게 있을 때 알아서 유저에게 확인받고 진행했으면 좋겠어.
   interview 뿐만 아니라 모든 agent 들이 동일하게."**
2. **"15칸을 없애고 전적 동적으로"** — 인터뷰의 하드코딩된 15개 항목을 제거하고,
   agent 가 요청마다 항목을 정한다.

## 이미 존재하는 것 (설계의 출발점)

요청받은 "agent 제안 → 사람 확인 → 진행" 모델은 **stage 2~5 에 이미 구현돼 있다.**
인터뷰 단계만 하드코딩 어휘 + 별도 확정 화면을 쓰는 예외다. 새 메커니즘을 세 번째로
만들지 말고 이것을 인터뷰까지 확장하는 것이 방향이다.

- `workflow/input_contracts.py` — `StageInputDraft`, `model_proposal` provenance,
  `record_model_proposals()`, `attest_model_proposals()`(승인 시 `operator_confirmed` 로 전환),
  `freeze_stage_input()`
- `workflow/stage_input_plan.py` — agent 가 **자유 key** 로 쓰는 단계별 계약
- `workflow/agents/stage_input_planner.py` — 그 key 를 만들어 내는 agent
- `workflow/security_kit.py` — `_OBSERVED_STAGE_INPUTS` / `SCAN_OBSERVED_KEYS` /
  `observed_stage_inputs()`: 서버가 관측한 값은 `system` provenance 로 주입해 운영자가
  타이핑 대신 확인만 한다
- **`InterviewService.__init__` 은 이미 `required_fields`·`optional_fields`·
  `ask_optional_fields`·`allow_custom_fields` 를 받는다.** `bootstrap.py:589-600` 이
  아무것도 안 넘겨서 실제 workflow 만 고정 15칸으로 돈다. playground 는 넘기고, 그 경로는
  테스트돼 있다. **기계장치는 있고 배선이 없다.**

---

# 조사 결과 — 고정 15칸 결합 지도

## 어휘 정의
`workflow/agents/interview_prompts.py` — `QUESTION_BY_FIELD`(:9, 15개),
`FIELD_LABELS`(:29), `INTERVIEW_FIELDS = tuple(QUESTION_BY_FIELD)`(:48),
`DEFAULT_REQUIRED_FIELDS = ()`(:49), `DEFAULT_OPTIONAL_FIELDS = INTERVIEW_FIELDS`(:50).
`question_for_field()`(:78)는 이미 미지 key 에 fallback 이 있다(soft).

## 병목 3곳 (이것만 열면 동적화가 가능해진다)

1. **`CompleteInterview.target_description` + `interface_hints` 가 구조적 필수**
   (`agents/interview.py:242-243`). `required_fields` 와 무관하게 강제된다.
   scan 은 `interface_hints` 에서 승인 protocol 을 뽑으므로(`service.py:242`, `:2508`)
   프로토콜 없이는 시작조차 못 한다. **가장 깊은 의존.**
2. **UI 가 15칸 밖 항목의 답변을 409 로 거부** — `app_routes.py:249`, `:392`.
   agent 가 정한 항목을 지금은 화면에서 답할 수조차 없다.
3. **`complete_interview()` 가 `custom_fields` 를 조용히 버린다** —
   `agents/interview.py:690` 이 `if name in CompleteInterview.model_fields` 로 필터.
   그래서 agent 가 만든 항목은 `TestRequest`·planner·reporter 에 영영 못 간다.

## 하드 결합 (특정 이름을 직접 읽음)

- `agents/interview.py`: `_LIST_FIELDS`(:55) · `_FILLED_LIST_FIELDS`(:65) ·
  `_UNSUGGESTABLE_FIELDS`(:107, **보안 규칙** — 모델이 소유권·승인근거·책임연락처를 제안 못 함) ·
  `InterviewField` Literal(:117, `InterviewEscape.field` 가 씀) · `InterviewProposal`(:201) ·
  `CompleteInterview`(:238) · `InterviewConfirmation`(:258) · `finalize()` 4항목 비교(:449) ·
  `_question_allow()`(:668) · `build_test_request()` 14개 명시 read(:699) ·
  `built_in = set(INTERVIEW_FIELDS)`(:762) · `_escape_note()` bare `FIELD_LABELS[...]`(:952) ·
  normalizer 들이 `allowed_fields=INTERVIEW_FIELDS`(:997,1014,1032)
- `workflow/service.py`: `_has_core_facts()`(:221, 리터럴 3개 — 초안 agent 실행 여부를 :467 에서 좌우) ·
  `_interview_stage_input_values()`(:234 — 인터뷰 항목을 **다른 이름의** stage input key 로 매핑:
  `interface_hints→"protocol"`, target/in_scope/out_of_scope→`"target_scope"` JSON,
  `authorization_basis→"authorization"`, constraints+prohibited+stop→`"safety_constraints"` JSON) ·
  `_scan_approval_context()`(:2410) · `_approved_protocols()`(:2493) · `build_test_request`(:1422)
- `workflow/app_routes.py`: :249 · :392 · bare `FIELD_LABELS[...]`(:259,:440,:442) ·
  `InterviewConfirmation` 조립(:534)
- `workflow/interview_view.py`: `_LIST_FIELDS` **중복**(:24) · `_SUMMARY_FIELDS`(:36) ·
  `_FALLBACK_EXAMPLES` 15개(:42) · `_legacy_allow()` **중복**(:267) ·
  **bare `FIELD_LABELS[field]`(:309) — 동적화 시 가장 먼저 터질 자리** · `proposal.approval_contact`(:138)
- `workflow/ui_contracts.py`: `ApprovalContext.target_description`·`.interface_hints`(:76)
- `workflow/models.py`: `TestRequest` 명시 필드(:61-83, legacy read 위해 전부 default 있음)
- 템플릿: `chat_workflow.html:547,550` · `agent_config.html:170,205,433`
- `stage_input_plan.py:32`: `INTERVIEW_OWNED_KEYS = frozenset(InterviewProposal.model_fields)` —
  파생이라 구조는 soft 지만 **의미**("인터뷰가 어차피 걷는 key")가 동적화 순간 깨진다

## 다운스트림 — 이름으로 의존하며 반드시 살아야 함

- **`agents/plan_validation.py:49-51`** — `prohibited_actions`·`out_of_scope`·`in_scope`.
  **보안 임계**: 계획이 금지된 일을 못 하게 막는 지점.
- `agents/planner.py:211,231` — `objective`·`in_scope`·`prohibited_actions`·`out_of_scope`
- `agents/reporter.py:262` — `objective`
- `chat_timeline.py:376` — handoff 표시

## 소프트 결합 (이미 일반적 — 재사용 대상)

- `agents/interview.py` `_advance`(:479-567)는 전부 `contract_fields = required + optional` 로 돈다.
  `_initial_states`·`_record_updates`·`_fields_to_ask`·`_missing_fields`·`_readiness`·
  `_unresolved_fields` 모두 필드 시퀀스를 받는다.
- `:836-838`, `:870-873` 은 이미
  `getattr(x, field) if field in INTERVIEW_FIELDS else x.custom_fields.get(field)` 이중 read.
- `InterviewResult.field_states/missing_fields/required_fields/optional_fields` 는 평범한 `list[str]`.
- `templates/chat_workflow.html:167-275` 은 필드 이름이 **템플릿에 없다**(row.field 로만 돔).
- `review_ui/static/*.js` 에 인터뷰 필드 참조 **0건**.
- `playground/input_config.py:26-107` `normalize_input_fields()` 가 **단일 검증 관문**이고
  `allowed_fields` 를 파라미터로 받는다.

## 영향받는 테스트 (~60). 가장 무거운 것들

- `tests/workflow/agents/test_interview.py` — :188(프롬프트 리터럴 "Still missing: target_description,
  interface_hints") · :214 · :247(custom_fields) · **:509(`_UNSUGGESTABLE_FIELDS` 보안)** ·
  :581/:604(`_FILLED_LIST_FIELDS`) · :633/:714/:743(`build_test_request`) ·
  **:764(legacy `TestRequest` 호환)** · :828(`DEFAULT_REQUIRED_FIELDS == ()`)
- `tests/test_workflow_ui.py` — :725(app_routes:249 잠금) · :838(`_SUMMARY_FIELDS`) ·
  :2716(`interface_hints` 필수 잠금 — 이번 세션에 추가한 것)
- `tests/workflow/test_service.py` — :1335(`_has_core_facts`) · :709/:774(protocol context)
- `tests/workflow/test_handoff_edits.py` · `test_stage_input_plan.py:41` · `test_input_config.py` ·
  `test_playground_service.py` · `tests/test_playground_ui.py`

---

# 설계 방향 (초안 — 재시작 후 Plan agent 로 정밀화할 것)

## 핵심 긴장

"전적 동적"을 **질문 목록**에는 적용할 수 있다. 그러나 다운스트림이 **이름으로** 요구하는 값이 있다:

| 값 | 누가 이름으로 요구하나 | 성격 |
|---|---|---|
| protocol | scan 승인 범위(`service.py:2508`) | **보안 — 사람 승인 필요** |
| in_scope / out_of_scope / prohibited_actions | `plan_validation.py:49` | **보안 — 계획 차단 근거** |
| objective | planner 프롬프트 · reporter | 표시·맥락 |
| target_description | 화면 표시 | 표시 |

**결론**: 이것들은 "운영자가 반드시 타이핑해야 하는 질문"이 아니라
**"agent 가 정해서 제안하고 운영자가 게이트에서 확인하는 값"** 으로 바꾼다.
그러면 사용자의 두 요구가 동시에 만족된다 — 질문 목록은 자유롭게 동적이고,
보안 임계값은 사람 승인을 유지한다. 이미 있는
`model_proposal → operator_confirmed`(승인 시 전환)와 `system` provenance 를 그대로 쓴다.

## 단계 제안 (각 단계가 독립 배포·검증 가능해야 함)

- **1단계 — 물어볼 필요 없는 것을 안 묻는다.** 대상이 worker host 자신이면 protocol 을
  연결된 worker 가 보고한 지원 protocol 에서 **제안**하고, scan 승인 화면(이미
  "scan에 사용할 protocol" 을 보여줌)에서 사람이 확인. 이번 사건의 직접 원인이 사라진다.
  범위 작고 효과 즉시.
- **2단계 — 병목 ②③ 개방.** `allow_custom_fields` 를 실제 경로에 배선하고,
  `app_routes.py:249,392` 가 계약에 있는 key 를 받아들이게 하고,
  `complete_interview()` 가 custom 값을 버리지 않게 한다(→ `TestRequest` 에 일반 map 으로 보존).
  여기까지 하면 **agent 가 항목을 추가**할 수 있다.
- **3단계 — 15칸 제거.** `InterviewProposal`/`CompleteInterview` 를 동적 map 으로 바꾸고,
  다운스트림이 요구하는 소수 값은 위 표대로 파생·확인 경로로 옮긴다.
  `interview_view.py` 중복 상수 정리와 bare `FIELD_LABELS[...]` 제거가 선행돼야 한다.

## 지켜야 할 불변식 (타협 불가)

- `plan_validation` 의 `prohibited_actions`/`out_of_scope`/`in_scope` 강제는 유지.
- scan 의 승인 protocol 범위는 **사람이 한 번은 확인**해야 한다(자동 확정 금지).
- `_UNSUGGESTABLE_FIELDS` 의 취지(모델이 승인 근거를 지어내지 못함)를 동적 어휘에서도 유지.
- 과거 artifact 가 계속 로드돼야 한다(`test_interview.py:764`).

## 하지 말 것

- 세 번째 "제안·확인" 메커니즘을 새로 만드는 것. `StageInputDraft` 계열을 재사용한다.
- 인터뷰의 완료 판정에 필수 항목을 몰래 끼워 넣는 것. 이번 세션에 시도했다가 되돌렸다 —
  `interview_prompts.py:47` 에 명시적 결정이 있다:
  `# 필수 필드는 운영자가 지정한 것만 쓴다 — 지정이 없으면 무엇도 강제하지 않는다`.
  테스트 6개가 이를 잠그고 있다.

---

# Verification

```
cd review-ui && uv run ruff check . && uv run python -m mypy review_ui && uv run pytest
```

정적 검증만으로는 부족하다. 실물 확인 경로(이번 세션에서 확립됨):

1. `docker compose up -d --build review-ui` (repo 루트, `.env` 에 `REVIEW_UI_SESSION_SECRET` 필요)
2. `cd byo-model-worker && uv run byo-model-worker connect --server http://localhost:8137
   --code <pairing-code> --provider claude --model haiku --security-local-tools`
   (pairing code 는 로그인한 계정 화면에서 나온다 — 계정 생성·로그인은 사용자가 직접)
3. 새 workflow 를 interview→report 까지 완주시켜 관찰. 완주 사례: workflow `bca56479`(2026-08-07).
4. 상태 확인: `docker compose exec -T review-ui python` 으로
   `/var/lib/knowledge-base/review/security-workflow.sqlite3` 의 `workflow_snapshot`·
   `workflow_context`·`workflow_artifact` 직접 조회.

# 남은 미결

- 3단계의 구체 설계(동적 map 의 저장 형태, `TestRequest` 호환 유지 방법)는 아직 안 정했다.
  재시작 후 Plan agent 로 정밀화할 것 — 이 파일의 결합 지도를 그대로 넘기면 된다.
- "모든 agent 동일하게"에서 scan/plan/execute/report 쪽은 이미 stage input 으로 그 모델을 쓴다.
  추가로 바꿀 것이 있는지는 미조사.
