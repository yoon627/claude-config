---
title: lesson-verify-scaffold-purpose-before-removal
category: decision
created: 2026-09-24
updated: 2026-09-29
sources:
  - plans/2026-09-24-prompt-audit-apply/prompt-audit-apply-plan.md (Progress·Decisions·Review Disposition)
  - plans/2026-09-27-audit-docs-drift/audit-docs-drift-plan.md (Progress·Review Disposition·Deferred — 사례 2)
  - plans/2026-09-27-guard-deny-removal/guard-deny-removal-plan.md (Progress·Decisions·Review Disposition — 사례 3)
  - plans/2026-06-04-dlc-final-verify-subagent/dlc-final-verify-subagent-plan.md (runner 원래 목적)
  - plans/2026-09-07-playbook-gaps/playbook-gaps-plan.md (runner Acceptance 독립 대조 도입)
  - plans/2026-09-28-claude-md-slim (사례 4 — Review Disposition, 미게시 로컬 branch claude-md-slim 보류 중)
  - plans/2026-09-28-wiki-context-cost-lessons (사례 4 원인 분석·Deferred 제안)
---

# lesson-verify-scaffold-purpose-before-removal

프롬프트·하네스 장치를 "낡은 scaffold" 로 보고 없애자고 하기 전에, **그 장치를 도입한 plan·결정을 먼저 읽고 원래 목적을 하나씩 반박할 수 있는지** 확인한다. 패턴 표에 맞는다는 것은 제거 근거가 아니다. **설정값(effort·모델·권한)을 "회귀"·"미결"로 적거나 바꾸자고 할 때도 같다** — 실제 설정 파일의 값과 그 값을 만든 결정 기록을 먼저 찾는다(사례 2). **운영 자산(문서·설정·hook)을 바꾸는 계획도 같다**(슬림화·재구성 포함) — 계획을 쓰기 전에 wiki index 에서 그 자산에 걸린 decision 을 찾는다(사례 4).

## 사례 1 — prompt-audit 의 제거 제안 (2026-09-24)

`/claude-api prompt-audit`(대상 모델 Opus 5.5)이 운영 자산에서 dated pattern 을 찾아 패치 16개를 제안했다. 그중 세 개가 도입 목적을 확인하지 않은 채 장치를 없애거나 약화했고, 셋 다 [[dual-review-plan-and-code]] 의 plan-reviewer(+codex)가 잡았다.

| 제안 | audit 근거 | 놓친 원래 목적 | 결과 |
|---|---|---|---|
| dlc 최종 검증 runner 제거 | "결정적 실행이라 LLM 이 판단할 것이 없다"(Group 4) | 긴 검증 출력을 메인 컨텍스트에서 덜어냄(2026-06-04) · Acceptance 를 독립 대조해 메인 판정과 갈리면 멈춤(2026-09-07) — [[hub-and-spoke-isolation]] | 보류. audit 이 대체 수단이라 한 code-reviewer 11항은 정적 plan↔diff 대조라 실행 결과를 보지 않아 **사실과 달랐다** |
| 날짜 기준 적용 범위를 "신규 plan" 으로 교체 | 날짜·경위 기록은 fossil(1d/2) | 날짜는 경위가 아니라 **소급 범위를 정하는 기능 조항**. "신규라고 전달된 plan" 으로 바꾸면 전달 누락 시 검사가 조용히 빠진다 | 기능 조항 유지, 경위 날짜만 제거 |
| 조사 프로토콜의 가설 규율 삭제 | 판단 작업의 strategy coaching(1c) | "첫 가설 안주 금지" — 대안 원인 배제는 성공 기준이다 ([[fablize-adopted-disciplines]]) | 개수만 빼고 원칙 유지 |

## 원인 (3 Whys)

1. 왜 잘못 제안했나 — 장치의 현재 문장만 보고 패턴 표와 대조했다.
2. 왜 문장만 봤나 — 도입 경위가 문장 밖(plan `# Decisions`, 커밋)에 있고, audit 절차의 provenance 단계를 idiom-dating 으로 대신했다.
3. 왜 대신했나 — 대량 스캔에서 "이 줄이 어떤 실패를 막으려 들어왔나"를 줄마다 추적하는 비용을 건너뛰었다. 그 질문은 audit 가이드 Step 2 가 명시한 것이다.

## 올바른 방법

- 제거·약화 후보마다 `git log -S '<문구>'` 또는 관련 plan 을 찾아 **도입 목적을 목록으로 적고, 각 목적이 대상 모델·현 구조에서 사라졌는지** 증거로 답한다. 하나라도 답 못 하면 제안하지 않거나 low-confidence flag 로만 둔다.
- "대체 수단이 있다"고 쓸 때는 그 수단의 실제 범위(정적/실행, 조건부/항상, 심각도 기본값)를 읽고 쓴다 — [[lesson-grep-absence-not-proof]] 와 같은 축.
- 날짜가 들어간 문장은 **경위(지워도 됨)**와 **적용 범위(기능)**를 구분한다.
- 설정값이 문서·기본값과 다르거나 기본값이 바뀌어 동작이 달라졌다고 적기 전에, **실제 설정 파일의 값을 읽고** 그 키 이름으로 `plans/` 를 grep 해 그 값을 정한 결정이 있는지 본다. 결정이 있으면 "회귀"가 아니라 "그 결정의 범위"로 적고, 남은 미확인만 따로 적는다.
- 대체 수단이 장치를 덮는다는 판정은 **장치가 발동하는 조건마다** 확인한다. 장치의 발동 기록(telemetry·차단 로그)을 먼저 분류해 어떤 조건에서 발동하는지 보고, 대체 수단은 그 조건별로 잰다. 한 조건에서 잰 "⊇" 는 그 조건으로 한정해 적는다(사례 3).
- "둘 다는 안 된다"는 트레이드오프를 적기 전에 관측 표본의 공통 속성을 가장 좁은 범주로 적는다 — 넓은 범주로 뭉치면 없는 상충이 생긴다(사례 3).
- 운영 자산(CLAUDE.md·skill·agent·hook·설정)을 바꾸는 계획을 쓰기 전에 wiki index 를 **자산 이름과 작업 종류**(slim·압축·이관·재구성 등)로 조회해 그 자산에 걸린 decision 을 찾는다. 있으면 따를지 뒤집을지를 plan `# Decisions` 첫 줄에 적고, 뒤집으면 근거와 사용자 승인을 붙인다(사례 4).

## 사례 2 — 결정된 설정값을 "미결 회귀"로 적음 (2026-09-27)

audit-docs-drift 에서 Opus 5.5 의 API 기본 effort 가 `medium` 이라는 공식 문서를 보고, opus 로 고정한 리뷰어가 Opus 5 시절(기본 `high`)보다 한 단계 낮은 `medium` 으로 돌고 복원 여부는 사용자 결정을 기다린다고 적었다 — 공용 wiki callout·index, plan Deferred("결정 필요"), 커밋 메시지. README 에는 M12 없이 모델 기본값 때문에 `medium` 으로 돈다고만 적었다. 실제로는 3일 전 prompt-audit-apply 의 **M12 결정**이 user settings `modelSettings` 에 Opus 5.5 = `medium` 을 명시 저장해 둔 상태였다. 근거와 되돌리기 기준은 그 plan 에 있다 — fix 과제 2×2 A/B 에서 medium·high 모두 숨은 테스트 9/9, fix 과제 비용 약 29% 절감(표본이 작아 accepted-risk), 놓침·재작업이 보이면 그 키만 `high` 로 복원. code-reviewer 가 settings 파일과 그 plan 을 읽어 잡았고, 게시 전 fixup 으로 "M12 결정의 범위 + 남은 미확인(세션 모델과 다른 고정 subagent 의 레벨)"으로 고쳤다([[effort-global-xhigh]]).

- 원인: 외부 사실(문서의 기본값)에서 곧바로 이 repo 의 상태를 추론했고, 실제 설정값과 그 값을 만든 plan 을 읽지 않았다. 왜 못 봤나 — M12 는 plan 에만 있고 wiki 에는 없었으며, user settings 는 repo 가 추적하지 않아 diff·repo 검색에 나오지 않는다. 사례 1 과 같은 축 — 현재 문장·문서만 보고 도입 경위를 건너뛰었다.
- 막은 것: 3일 전 근거·되돌리기 기준을 붙여 정한 결정을 새 근거 없이 다시 여는 것, 이미 있는 설정을 "새로 추가할 항목"으로 제안하는 것.

## 사례 3 — 한 세션 종류에서 잰 "네이티브 ⊇ 자작"으로 guard 를 `retire` (2026-08-12 판정 → 2026-09-27 정정)

[[native-overlap-ledger]] 는 2026-08-12 `scripts/guard-worktree-edit.js` 기능 ②(worktree 세션의 worktree 밖 편집 `deny`)를 `retire` 로 판정했다. 근거는 EnterWorktree 로 들어간 세션에서 main checkout Write 가 네이티브 격리에 막힌다는 실측 하나였는데, 결론은 "네이티브 ⊇ 자작 ②, 진상위집합"으로 모든 세션에 일반화됐다. 제거 착수 조건으로 건 2.1.283 재실측에서, worktree 디렉토리에서 바로 시작한 세션은 격리되지 않아 hook 을 끄면 main 에 파일이 그대로 만들어졌다 — 그런 세션에서는 ② 가 유일한 보호다. 제거안은 뒤집혀 ② 를 좁혀 남겼다(`keep`).

같은 작업 안에서 같은 축의 오류가 한 번 더 났다. guard 의 관측 오탐 4건을 "untracked" 로 뭉쳐 "오탐 제거와 새 파일 차단은 같은 조건이라 양립할 수 없다"는 ⚠️ self-flag 를 적었는데, 4건은 전부 gitignored 였다. plan-reviewer 가 잡았고 "추적 OR (아직 없음 AND not-ignored)" 규칙으로 둘 다 만족시켰다.

- 원인 (3 Whys):
  1. 왜 `retire` 로 적었나 — 대체 수단의 범위를 한 조건에서만 재고 전체로 적었다.
  2. 왜 한 조건만 쟀나 — 실측하던 세션 자체가 EnterWorktree 세션이라 그 조건이 기본값처럼 보였고, 장치가 실제로 언제 발동하는지(hook 은 cwd 문자열만 본다)를 먼저 보지 않았다.
  3. 왜 발동 조건을 안 봤나 — "대체됐나"를 "네이티브가 무엇을 막나"로만 물었지 "장치가 어떤 조건에서 발동하나"로 묻지 않았다. self-flag 도 같은 축이다 — 관측 표본의 속성(gitignored)을 한 단계 넓은 범주(untracked)로 적어 없는 상충을 만들었다.
- 막은 것: 원안대로 제거했다면 worktree 디렉토리에서 시작한 세션이 main checkout 의 추적 파일을 조용히 고칠 수 있었다(`~/.claude` 밖 repo 는 권한 요청도 없다). self-flag 를 그대로 두었다면 main 에 남은 새 파일이 브랜치 커밋에서 빠지고 뒤의 ff-merge·autopull 을 막는 경우를 놓쳤다.
- 찾은 방법: 제거 단위가 착수 조건으로 "현재 버전 재실측"을 걸어 두었고, 재실측에서 guard 의 telemetry 차단 기록 7행을 분류한 뒤(오탐 4건은 모두 네이티브 격리 밖이었다 — 2.1.222 이전 1건, `ExitWorktree` 로 격리를 벗어난 뒤 cwd 가 worktree 로 돌아온 세션 3건. 나머지 3행은 08-12 실측의 hook 직접 호출) hook 을 끈 headless 세션을 임시 repo 의 linked worktree 디렉토리에서 시작해 대조했다.

## 사례 4 — 슬림화 계획이 기존 결정을 조회하지 않음 (2026-09-28)

토큰 절감 논의 끝에 CLAUDE.md 슬림화 plan 을 쓰면서 `wc -c ≤ 22,000` 을 hard gate 로, 근거·절차를 참조 문서로 옮기는 것(§10 포함)을 수단으로 잡았다. 이 repo 에는 7월 결정 [[ops-doc-slimming]] 이 있었다 — 규칙 손실 0 이 hard gate, 항상 주입 규칙을 조건부 로드로 옮기면 그 자체가 손실, bytes 는 보조목표, §10 스펙 이관 금지. CLAUDE.md §11 은 작업 시작 시 index 조회를 요구하는데 건너뛰었고, plan-reviewer(+Codex)가 잡았다. 편집 전이라 되돌릴 것은 없었다.

- 원인 (3 Whys):
  1. 왜 기존 결정과 정면충돌하는 계획을 썼나 — 그 결정을 몰랐다.
  2. 왜 몰랐나 — index 조회(§11)를 건너뛰었다. 조회했다면 `ops-doc-slimming` 한 줄 요약에 "bytes 목표는 보조·규칙손실0 이 hard gate" 가 그대로 있었다.
  3. 왜 건너뛰었나 — 조회를 거는 시점이 없었다. §11 의 조회 트리거는 "작업 시작 시" 하나인데, 이 계획은 같은 세션의 측정·분석 흐름에서 이어져 나와 "시작"으로 인식되지 않았다. dlc 의 Explore wiki 조회도 "조건부·opt-in" 으로 적혀 있고 절차는 자동 로드되지 않는 `docs/dlc-details.md` §C 에 있다. 이 lesson 도 "제거·설정값"만 다뤄 계획 쪽 신호가 되지 못했다 — lesson 의 적용 범위는 넓혔고(위 첫 문단·올바른 방법), 트리거 공백(분석 → 계획 전환 시 조회)은 사용자 승인을 받아 dlc 3단계(draft plan) 앞의 필수 decision 조회로 넣었다(2026-09-29, `skills/dlc/SKILL.md` wiki 연계).
- 막은 것: 규칙을 조건부 로드 문서로 밀어내는 슬림화가 main 에 들어가는 것. 이어서 실사용 비중을 재 보니 슬림화 자체의 기대효과가 약 0.4~2%(압축률 가정에 따라) 라 우선순위도 바뀌었다([[claude-code-context-cost]]).

## 전후 비교는 증거로 만든다

같은 작업에서 적용 여부를 갈랐던 방법 — 재사용 가능하다.
- **transcript 전수 스캔**(`~/.claude/projects/**/*.jsonl`, subagent 는 `subagents/*.meta.json` 의 `agentType` 으로 식별): tool-call 누출 0건/수천 텍스트 블록 → 우회 규칙 제거, small 변경 code-reviewer 10건 중 1건이 실제 Major → 생략안 보류.
- **headless A/B**(`claude -p --model … --effort … --output-format json --no-session-persistence --setting-sources project`): 숨은 테스트로 채점하는 과제로 비용·시간·정답을 비교. 천장 효과(양쪽 만점)면 품질 차이는 말할 수 없다는 한계를 같이 적는다.

관련: [[workflow-failures]], [[evidence-gate]].
