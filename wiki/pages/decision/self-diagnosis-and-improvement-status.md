---
title: self-diagnosis-and-improvement-status
category: decision
created: 2026-06-19
updated: 2026-07-03
sources:
  - skills/dlc/SKILL.md (자기 진단)
  - PR #49 (self-diagnosis), #46 (명확화 게이트), #47 (feedback 메모리)
  - plans/2026-06-14-dlc-improvements/dlc-improvements-plan.md (f698001 심의 종결)
  - self-improve-trigger@b9a9ede (폐기 — 원격 브랜치 삭제)
  - improve-loop 브랜치 (2026-07-03 수집·분석 기계화 — scripts/dlc-signal.js·skills/improve/)
---

# self-diagnosis-and-improvement-status

이 워크플로우의 "스스로 점검·개선" 능력의 현황. **자기 진단은 채택**, 자기 개선은 **수집·분석 축 기계화까지 채택(2026-07-03)** — 반영(수정)은 여전히 사용자 승인 게이트, 완전 무인 자동화는 미채택. 증거기반 finding 최소형은 2026-06-19 채택(아래).

## 자기 진단 (self-diagnosis) — 채택 (PR #49)
[[dlc-development-cycle]]에 통합된 **작업 단위 가드**. plan write 시점에 "지금 행동이 `# Next`·규모표와 맞나"를 점검한다. 중대 신호(방향/요구 변경, 필요 단계 건너뜀, 스코프 밖 파일 수정, 격리 위반, 동일 실패 2회, 검증 허위 위험)면 **멈춤 + `AskUserQuestion` + 결정 대기**. *이번 작업*이 규약을 이탈하는지 본다.

## 자기 개선 (self-improvement) — 심의 종결 (2026-06-19)
실수·교훈을 누적해 **규약 자체를 고쳐나가는 메타 루프**를 별도로 둘지 검토했고, 결론은 "능동 부분은 기존 메커니즘으로 충분, 신규 일반 단계는 미채택"(dlc-improvements 브랜치 f698001 `done`, self-improve-trigger 폐기).

- **채택(이미 머지)**: 요구사항 명확화 게이트(#46), self-diagnosis(#49), feedback 메모리 인프라(#47 — [[feedback-memory]]). 계획했던 retrospect·gate·skip 명확화는 이들로 반영됨 → 별도 구현 불필요.
- **미채택 — self-improve-trigger(폐기)**: CLAUDE.md에 *자발적 실수기록 트리거*를 추가하려던 안. 원격 브랜치 삭제. [[feedback-memory]](§12, 사용자 지시 기반) + self-diagnosis(사후 감지)로 갈음.
- **미채택 — preflight invariant-check**: "변경 전 절대 깨면 안 되는 것 2~3개 선언" 안. 사유 — 개수·형식이 자의적·모호해 빈 체크리스트 의례로 전락 우려(over-engineering). 핵심 통찰(위험 변경 전 제약 인지)은 유효하나 일반 dlc 단계로 박을 형태가 아님. 실제 실패사례(RTK가 sha256 서명한 hook을 직접 편집 → RTK 실행 거부)는 feedback 메모리(`rtk-headroom-path-fix.md`) + #49 self-diagnosis로 부분 커버.
- **[채택 2026-06-19] 증거기반 finding 최소형**: 사용자 재요청으로 도입. 확인된 workflow 실패(중대 self-diagnosis·동일유형 2회)에만 plan `# Workflow Findings` 에 한 줄(깨진 규칙·재발 조건·수정 후보), 2회 누적 시 dlc/wiki 수정 *제안* 승격. **자동 수정은 여전히 안 함**(사용자 승인 후 별도). 실패는 [[workflow-failures]] 에 영속 누적되고 같은 실패 2회+ 반복 시 dlc 가 wt 해결을 제안한다. invariant-check 의 '빈 의례' 함정을 피한 형태 — [[evidence-gate]]·[[fablize-adopted-disciplines]].

## [채택 2026-07-03] 수집·분석 기계화 (loop 의 앞 두 축)
2026-06-19 미채택의 실제 병목이 "반영 자동화"가 아니라 **수집·분석의 수동성**(finding 기록이 모델 자발성에 의존 → [[workflow-failures]] 표에 항목 1개, MEMORY 1개)이었다는 2026-07-02 전수 감사 결론에 따라, 사용자 결정으로 앞 두 축만 기계화:
- **수집(자동)**: `scripts/dlc-signal.js` — 기존 hook 4종이 판정 발동(early-stop 경고·doc-drift·guard 차단·router 주입·plan `status: blocked` 전이·disposition 기록)을 `~/.claude/telemetry/dlc-signals.jsonl` 에 append-only 누적. failure/activity 축 구분, substring 아닌 상태 전이 판정, fail-open, env 채널(`CLAUDE_DLC_SIGNAL_{DIR,OFF}`).
- **분석·제안(반자동)**: `/improve` skill(구 `/audit` 흡수) — 정합성 기계 점검 + 신호 집계(session-unique 우선) + [[workflow-failures]]·MEMORY 대조 → 개선 후보 랭킹 제시.
- **반영·효과**: 수정은 사용자 승인 후 wt→dlc(불변), 효과는 다음 `/improve` 의 신호 추이로 확인.
- 근거: ACE 계열 연구의 "정적 규칙 + 자기진화 정제 하이브리드 > 순수 자동진화", dlc Report 의 feedback memory 판정 의무(§12 — 사용자 리뷰가 다음 구현에 반영되는 5단계) 동시 도입.

## 함의
"**반영까지 무인**인 자기개선 루프"는 여전히 **의도적으로 두지 않는다** — 단 2026-07-03 부로 수집·분석은 기계가 돌고(위), 사람은 승인 게이트만 담당한다. 사용자 지시 기반 [[feedback-memory]] + 사후 [[dlc-development-cycle|self-diagnosis]] 조합은 유지. 향후 "특정 위험 변경 전 제약 인지"를 더 구체적 형태로 다룰 필요가 생기면 위 미채택 기록이 출발점이다. 범위 경계 규칙은 [[deferred-and-scope-boundary]].
