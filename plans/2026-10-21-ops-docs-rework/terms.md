# 번역 공통 용어표 (ops-docs-rework)

translate-repo 단위는 착수 때 이 표를 읽고 따른다. 새로 정한 용어·원문 유지 문자열은 그 단위의 머지에서 이 표에 더한다(같은 지적이 단위마다 다시 나오지 않게 — translate-skill-commit-check log Workflow Findings). **줄을 더하기만 한다(append-only)** — 두 단위가 동시에 더해 충돌하면 두 줄을 모두 남긴다. 고칠 때는 그 단위의 plan `# Decisions` 에 이유를 적는다. 단위별 전체 대응표는 아래 "출처" 의 파일에 있다.

## 원문 그대로 두는 문자열 (스크립트·사용자·다른 파일과 글자로 맞춘다)
| 문자열 | 왜 | 정한 단위 |
|---|---|---|
| `/e 머지` | 사용자가 입력하는 인자 토큰 | translate-skill-e |
| `"등록 불가"` | jira-worklog 경고 — e 가 이것을 보고 worktree 정리를 막는다 | translate-skill-e |
| `wip:` · `(e checkpoint)` | e 의 WIP 커밋 제목 — commit-check 가 이 글자로 찾는다 | translate-skill-e |
| `main-autopull ⓑ` | 공용 wiki 가 가리키는 라벨 — 원문자지만 §0 의 원문자 금지 대상이 아니다(인용) | translate-skill-e |
| `M1~M6` (물결) | 공용 wiki 가 "SKILL M1~M6" 로 가리킨다 | translate-skill-e |
| `## Codex 병행` | `scripts/bootstrap/sync_codex_agents.py` 의 `CODEX_SECTION`·`LEFTOVER` 가 이 제목으로 Codex 절을 뗀다 — agent 를 옮길 때 그대로 두거나, 스크립트를 같은 머지에서 고친다 | translate-claude-md(log W4) |
| `세션 활동 없음` · `ticket=(없음)` · `합계` · `등록 차단` | jira-worklog 출력 머리줄·차단 문구 | translate-skill-wt |
| `"로그인 리다이렉트 버그 수정"` | 비ASCII 요청을 slug 로 바꾸는 예시(입력 자체가 예시) | translate-skill-wt |
| `merge-tree --write-tree 실패` | `commit_units.py` 의 git 실패 문구 — 충돌 거부를 알아본다 | translate-skill-commit-check |
| git/OS stderr("modified or untracked files"·"Access is denied" 등) | 원래 영어 — 핵심 문구로 지킨다 | translate-skill-wt |
| `"plan 반영용 요약"`(임시) | agent 출력 절의 옛 이름 — 아직 한국어인 agent 가 쓰는 동안 `skills/dlc/SKILL.md` 격리 경계 절과 공용 wiki(`pages/concept/plan-handoff.md`·`pages/concept/hub-and-spoke-isolation.md`)가 두 이름("Summary for the plan")을 함께 적는다. **agent 4개(researcher·plan-reviewer·code-reviewer·architecture-reviewer)를 다 옮긴 단위가 한국어 이름을 지운다** — dlc 를 먼저 옮기면 영어 dlc 도 이 따옴표를 남긴다 | translate-agent-researcher |
| plan 파일 표지 `없음 — <…>` | plan 은 한국어 — `없음` 을 그대로 두고 자리표시자만 영어(`없음 — <reason>`). `none — <…>`(Split) 도 같다 | translate-agent-plan-reviewer |
| `## Codex 병행` 이 붙은 본문 제목 | `## Codex 병행 검토 (optional)` → `## Codex 병행 review (optional)` — 접두만 원문, 나머지는 영어. 남은 reviewer agent 도 같게 | translate-agent-plan-reviewer |
| `mode: planning` · `mode: post-implementation` | architecture-reviewer 가 스스로 정한 입력 토큰(호출 측이 프롬프트 첫 줄에 이 글자로 쓴다 — dlc 본문에는 아직 이 글자가 없다, 그 plan log Deferred) | translate-agent-arch-reviewer |
| `신호 집계 실행 실패` · `last-improve 마커 갱신:` · `/improve 권장 — failure 신호 N세션 누적 (마커 이후)` | `skills/improve/improve.sh`·`scripts/dlc-signal.js mark`·`scripts/session-brief.js` 가 찍는 글자 — improve 7단계가 이 글자로 마커 갱신 여부·성공을 판단한다. 이 출력을 바꾸는 작업(예: translate-hooks 의 `session-brief.js`)은 같은 머지에서 `skills/improve/SKILL.md` 7단계 인용도 고친다 | translate-skill-improve |
| `[공용]` · `L20 §결정 (L18-35): …` · `관련: → 나가는 · ← 들어오는` · `찾을 wiki 가 없다` · `UTF-8 아님` · `check_links: 읽기 실패` · "covers 읽기 실패" · "검사 대상 아님" · "미확인" · "작업 트리 기준 — … 미커밋 변경 N개" · "인자 오류" | `skills/wiki` 의 `wiki_search.py`·`check_links.py`·`wiki_check.py` 가 찍는 글자 — 첫 번째로 나올 때 괄호에 영어 뜻을 붙인다. 이 출력을 바꾸는 작업은 같은 머지에서 `skills/wiki/SKILL.md` 인용도 고친다. `훅` 은 "한 음절 한글은 못 찾는다" 의 예시라 그대로 | translate-skill-wiki |
| `[plan 대비]` | code-reviewer 11번 관점 finding 태그 — dlc 처분 줄·16 Report "읽을 곳" 출처 (3)·README·공용 wiki 가 이 글자로 가리킨다 | translate-agent-code-reviewer |
| `⚠️ (구현)` | plan `# Decisions` 의 dlc self-flag 표지 — code-reviewer 12번 관점·Codex 독립 입력·출력 절이 가리킨다 | translate-agent-code-reviewer |
| `"읽을 곳"` | dlc 16 Report 블록 이름 — code-reviewer 는 인용하고 "(read points)" 를 붙인다. dlc 단위가 이름을 바꾸면 같은 머지에서 맞춘다 | translate-agent-code-reviewer |
| `/improve recommended — failure signals accumulated in N sessions (since the marker)` | **위 `/improve 권장 — failure 신호 N세션 누적 (마커 이후)` 를 대체** — `scripts/session-brief.js` L 줄을 영어로 옮겼다(N=1 이면 `1 session`). `skills/improve/SKILL.md` 7단계가 이 글자를 그대로 인용한다. 이 줄을 바꾸는 작업은 같은 머지에서 그 인용도 고친다 | translate-hooks |
| `guard-worktree-edit.js`·`guard-push-delete.js` 의 `ask` reason · `notify-hook.js`/`.ps1` 알림 문구(`입력 대기`·`응답 완료`) | 대화형 세션의 사용자 확인 창·데스크톱 알림에 보이는 글(headless `-p` 에서는 `ask` 가 거부되어 모델도 읽는다) — §0 에 따라 한국어로 둔다. hook 이 모델에게 보내는 글(SessionStart stdout·additionalContext·Stop block reason·`deny` reason)만 영어 | translate-hooks |
| `[dlc:investigation]` · `[dlc:grounding]` | `dlc-task-router.js` 가 붙이는 태그 — `dlc-task-router.test.js` 가 이 글자로 라우팅을 확인한다 | translate-hooks |

## 용어 (한국어 → 영어)
| 한국어 | 영어 | 메모 |
|---|---|---|
| 보류(계획·적용을 미룸) | leave unapplied | "hold" 는 commit-check 상태값 `held` 와 겹친다(e·commit-check 리뷰가 두 번 지적) |
| 미게시 | unpublished | |
| 정리 안 된 커밋 | uncleaned commits | e M3·commit-check |
| 합치기 / 나누기 | fold / split | commit-check |
| 무인 실행 | unattended | |
| push 는 요청 시만 | push only on request | |
| 대응표 | mapping table | |
| stale(최신성이 아닌 "더는 유효하지 않음") | no longer valid | translate-skill-c |
| 확신도 ✅확실 / ⚠️추정 / ❌모름 | ✅certain / ⚠️inferred / ❌unknown | CLAUDE.md §1 |
| 미검증 | unverified | CLAUDE.md §1 |
| 공개 점검 | Public check | CLAUDE.md §11 |
| 회사 repo | company repo | CLAUDE.md §11 |
| intent 상태 토큰 (미착수)·(열림)·(해소)·(이월 → …)·폐기 | (not started)·(open)·(resolved)·(carried over → …)·dropped | translate-claude-md |
| `PR#n 리뷰 반영: <요지>` | `PR#n address review: <gist>` | translate-skill-c — `<gist>` 는 plan 언어 |
| e 표의 Task 문구 "정리 후 `/e merge` 재실행"·"checks 대기" | "clean up the commits, then rerun `/e merge`"·"PR #N waiting for checks, rerun `/e merge`" | translate-skill-e |
| agent 출력 절 "plan 반영용 요약" | "Summary for the plan" | translate-agent-researcher — 위 임시 문자열 줄 |
| agent 공통 절 제목 응답 언어 / 출처 우선순위 / 동작 규칙 / 확신도 / 출력 형식 | Response language / Source priority / Rules / Confidence / Output format | translate-agent-researcher — 남은 agent 3개도 같은 제목을 쓴다 |
| agent 공통 응답 언어 문장 "영어(CLAUDE.md §0 언어 정책 — 메인이 사용자에게 한국어로 전한다)…" | "English (CLAUDE.md §0 language policy — the main agent relays it to the user in Korean). Keep code identifiers, library names, error messages and option names in their original form." | translate-agent-researcher |
| 작성일(출처가 쓰인 날) / 기준일(검색한 날) | publication date / As of | translate-agent-researcher — 둘을 "date" 하나로 옮기면 섞인다 |
| 묶음 모드 / "묶음 분할 리뷰" | Bundle mode / "bundle split review" | translate-agent-plan-reviewer — CLAUDE.md §5 "in bundle mode" |
| 리뷰 출력 절 종합 판단 / 강한 우려 / 약한 우려 / 누락된 시나리오 / rollback 평가 / 확인한 파일 | Overall verdict / Strong concerns / Weak concerns / Missing scenarios / Rollback evaluation / Files checked | translate-agent-plan-reviewer — 남은 reviewer agent 도 같은 제목을 쓴다(`## Codex 병행` 은 원문 유지) |
| Codex 프롬프트의 응답 제목 강한 우려 / 약한 우려 / 제안 | strong concerns / weak concerns / suggestions — 추출 grep 은 같은 머지에서 `grep -iE` 영어 제목으로 | translate-agent-plan-reviewer |
| 검토 관점 | Review checklist (절 제목과 Codex 프롬프트 모두) | translate-agent-plan-reviewer — code-reviewer·architecture-reviewer 도 같은 낱말을 쓴다 |
| Codex 출력 템플릿 필드 실행 여부 / 합의 항목 / Codex 만 잡은 것 / 메인만 잡은 것 | Run: yes \| skipped (reason: ...) / Agreed items / Found only by Codex / Found only by this review | translate-agent-plan-reviewer, 고침 translate-agent-arch-reviewer — "메인만" 은 Codex 와 견준 리뷰어 자신의 검토(`~/.claude/wiki/docs/codex-review.md` "자체 검토")라 "the main agent" 가 아니다. `## Codex 병행` 제목은 원문 |
| 도메인 특화 프롬프트 / 결론부 추출 패턴 | Domain-specific prompt / Conclusion extraction pattern | translate-agent-plan-reviewer — `scripts/bootstrap/test_sync_codex_agents.py` 의 `REMOVED` 가 한국어 "도메인 특화 프롬프트" 를 찾으므로 마지막 reviewer 를 옮기는 단위가 그 테스트를 함께 고친다 |
| architecture-reviewer 절 제목 책임 경계 / 호출 트리거 / 입력 최소 번들 / 검토 시작 절차 / 비-목표 / 금지 사항 / 심각도 | Responsibility boundaries / Call triggers / Minimum input bundle / Review start procedure / Non-goals / Prohibitions / Severity | translate-agent-arch-reviewer — code-reviewer 에 같은 절이 있으면 같은 말 |
| 리뷰 출력 절 호출 적정성 / 수집 한계 / 다른 agent 위임 · 출력 값 "없음" | Call appropriateness / Collection limits / Delegated to other agents · "none" | translate-agent-arch-reviewer — agent 출력 값 "없음" 은 plan 표지 `없음` 과 달라 영어로 |
| wiki 절 제목 신선도 / 대표 질문 / 대상 계층 / 알림 해소 / hook 등록 | Freshness / representative questions / target layer / Clearing the notice / Registering the hook | translate-skill-wiki — `wiki_check.py`·README 의 "SKILL.md 신선도 절" 은 같은 머지에서 "SKILL.md Freshness 절" 로 |
| 외부공개(CLAUDE.md §1 승인 대상) | publicly visible | CLAUDE.md §1·`skills/c` 와 같음 — translate-skill-wiki 에서 "publishing externally" 로 옮겼다가 리뷰가 잡음 |
| refuted 후보(감사 로그) · 구현 ⚠️ 응답 · 검증 실행 결과 · 제안 · 타당 \| 반박 · 검토 항목 통과 · 검증 명령 미식별 · 검증 칸 | refuted candidates (audit log) · Implementation ⚠️ responses · Verification run results · Suggestion · valid \| rebutted · review items passed · verification command not identified · verification field | translate-agent-code-reviewer — dlc 도 "검증 명령 미식별"·"검증 칸" 을 같은 말로 |
| 요구사항 명확화 · 분할 판정 · 진입 매트릭스 · 자기 진단 · 조사 프로토콜 · wiki 연계 · 격리 경계 · 정식 완료 커밋 · 단위 커밋 · 우선 검토 · 위임 예외 | Requirement clarification · Split judgment · Entry matrix · Self-diagnosis · Investigation protocol · wiki integration · Isolation boundary · formal completion commit · unit commit · review first · handover exception | translate-skill-dlc — dlc 절 제목, 공용 wiki docs·hooks 도 같은 이름 |
| `## 읽을 곳` · `확인 필요:` | `## Where to read` · `Needs confirmation:` | translate-skill-dlc — Report 라벨(스크립트가 읽지 않는다). code-reviewer·README 인용도 같은 머지에서 맞췄다 — 위 원문 유지 표의 `"읽을 곳"` 줄을 대체 |
| 공통 호출 규약 · 호출 측 · 세션 캐시 · 자체 검토 · 차등 표 · 외부 codex 모드 | common invocation convention · the caller · session cache · the reviewer's own review · tiering table · external codex mode | translate-wiki-docs(codex-review) |
| 파일 점유 류 · 부분 성공 · 결과 처리 · 미보존 산출물 · 선행 검사 · 재수집 · "SKILL N단계" | File held type · Partial success · Result handling · unsaved artifacts · prerequisite check · re-collection · "SKILL step N" | translate-wiki-docs(worktree-lifecycle) |

## 기계 대조 (공통 대조 검사가 읽는다)
원문(한국어, 원문 유지 문자열 밖)에 왼쪽 낱말이 나온 횟수만큼 번역에 오른쪽 낱말이 있어야 한다(대소문자 무시). 다른 뜻으로 쓰인 원문이면 단위 설정의 `termsSkip` 에 `{ "<왼쪽 낱말>": "<이유>" }` 로 적는다. **한 뜻으로만 쓰이는 절 제목·필드·라벨만 넣는다** — 여러 뜻의 일상어(보류·합치기·나누기·제안)는 넣지 않는다(사람용 표에만). 형식이 틀린 줄이나 빈 블록은 검사가 FAIL 한다. 줄을 더하기만 한다(위 규칙과 같다).

```text
검토 관점 => Review checklist
메인만 잡은 것 => Found only by this review
Codex 만 잡은 것 => Found only by Codex
합의 항목 => Agreed items
plan 반영용 요약 => Summary for the plan
종합 판단 => Overall verdict
확인한 파일 => Files checked
누락된 시나리오 => Missing scenarios
응답 언어 => Response language
출력 형식 => Output format
## 동작 규칙 => ## Rules
수집 한계 => Collection limits
호출 적정성 => Call appropriateness
책임 경계 => Responsibility boundaries
금지 사항 => Prohibitions
묶음 모드 => bundle mode
✅확실 => ✅certain
⚠️추정 => ⚠️inferred
❌모름 => ❌unknown
미검증 => unverified
작성일 => publication date
공개 점검 => Public check
회사 repo => company repo
무인 실행 => unattended
미게시 => unpublished
정리 안 된 커밋 => uncleaned commits
push 는 요청 시만 => push only on request
대응표 => mapping table
확신도 => Confidence
심각도 => Severity
도메인 특화 프롬프트 => Domain-specific prompt
결론부 추출 패턴 => Conclusion extraction pattern
강한 우려 => strong concerns
약한 우려 => weak concerns
rollback 평가 => Rollback evaluation
출처 우선순위 => Source priority
호출 트리거 => Call triggers
입력 최소 번들 => Minimum input bundle
검토 시작 절차 => Review start procedure
비-목표 => Non-goals
다른 agent 위임 => Delegated to other agents
묶음 분할 리뷰 => bundle split review
기준일 => as of
신선도 => Freshness
대표 질문 => representative question
대상 계층 => target layer
refuted 후보 => refuted candidates
구현 ⚠️ 응답 => Implementation ⚠️ responses
검증 실행 결과 => Verification run results
검토 항목 통과 => review items passed
```

## 출처 (단위별 전체 대응표·결정)
- `plans/2026-10-26-translate-claude-md/phrases-en.txt` — CLAUDE.md 핵심 문구(사용자 승인 2026-10-26)
- `plans/2026-10-26-translate-claude-md/pointers.md` "역방향 인용" — CLAUDE.md 가 가리키는 한국어 skill 제목의 영어
- `plans/2026-10-26-translate-skill-e/phrases-en.txt` · `pointers.md` 대응표 — e 의 내부 라벨(Worktree cleanup rules·"6 pre" 등)
- `plans/2026-10-27-translate-skill-c/pointers.md` — c 의 Task 문구와 공용 wiki 인용
- `plans/2026-10-27-translate-skill-wt/pointers.md` — wt 의 원문 유지 문자열과 출력 출처(`jira_worklog.py`)
- `plans/2026-10-27-translate-skill-commit-check/translate-skill-commit-check-log.md` — 보류 → "leave unapplied" 결정
- `plans/2026-10-27-translate-agent-researcher/translate-agent-researcher-plan.md` `# Decisions` — 출력 절 이름과 agent 공통 제목
- `plans/2026-10-27-translate-agent-plan-reviewer/translate-agent-plan-reviewer-plan.md` `# Decisions` — 공통 대조 검사, Codex 프롬프트·추출 패턴

## 공통 대조 검사
- `plans/2026-10-21-ops-docs-rework/check-translation.js`·`mut-translation.js` — 단위는 설정 JSON(manifest·locations·원문 유지·frontmatter·제목 목록·번호 블록·허용 기호·규칙 변형)만 쓴다. 쓰는 법은 스크립트 머리 주석.
