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
| Codex 출력 템플릿 필드 실행 여부 / 합의 항목 / Codex 만 잡은 것 / 메인만 잡은 것 | Run: yes \| skipped (reason: ...) / Agreed items / Found only by Codex / Found only by the main agent | translate-agent-plan-reviewer — `## Codex 병행` 제목은 원문 |
| 도메인 특화 프롬프트 / 결론부 추출 패턴 | Domain-specific prompt / Conclusion extraction pattern | translate-agent-plan-reviewer — `scripts/bootstrap/test_sync_codex_agents.py` 의 `REMOVED` 가 한국어 "도메인 특화 프롬프트" 를 찾으므로 마지막 reviewer 를 옮기는 단위가 그 테스트를 함께 고친다 |

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
