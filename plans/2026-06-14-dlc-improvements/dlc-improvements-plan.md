---
title: dlc-improvements — dlc 개선 심의 기록 (대부분 머지, invariant-check 미채택)
status: done
started: 2026-06-14
updated: 2026-06-19
---

# Goal
`skills/dlc/SKILL.md` 개선 검토. 이번 세션 실패유형(기존 무결성 깬 변경) 예방 + retrospect 통합 + skip 명확화. **이 브랜치는 구현이 아니라 심의 기록** — 대부분 다른 PR 로 머지됐고, invariant-check 만 미채택으로 사유와 함께 보존한다.

# Progress
- 2026-06-14: 분석 + codex 논의(effort high). plan 작성(plan-only).
- 2026-06-19: 토픽 대부분 **이미 머지 확인** — #46(요구사항 명확화 게이트), #49(self-diagnosis). retrospect/게이트/skip 명확화는 사실상 반영됨. **invariant-check 는 고려했으나 미채택**(아래 Decisions). 심의 기록으로 remote 보존, status→done.

# Next
(없음 — 심의 종결.) dlc 개선 본류는 머지 완료. invariant-check 는 미채택 기록만 남김 — 향후 "특정 위험 변경 전 제약 인지"를 더 구체적 형태로 다룰 필요가 생기면 이 기록을 출발점으로 재고.

# Decisions
- **[머지됨] 요구사항 명확화 게이트(#46), self-diagnosis(#49).** 내가 계획한 retrospect·gate 명확화·자기점검은 이 두 PR 로 dlc SKILL.md 에 반영됨 → 별도 구현 불필요.
- **[미채택 · 기록용] preflight invariant-check.**
  - *고려했던 이유*: 이번 세션에 RTK hook 을 "개선"하려 직접 편집했는데, RTK 가 자기 hook 을 sha256 으로 **서명**해둬서 편집 즉시 무결성 검사 실패 → **RTK 실행 거부**(개선하려다 죽임). "변경 전 절대 깨면 안 되는 것을 선언"하면 이 부류를 사전 예방한다는 발상이었다.
  - *미채택 사유(사용자 비판, 타당)*: **"변경 전 invariant 2~3개를 적어라"는 형식 자체가 자의적·모호하다.** 개수(2~3)도 임의이고, 매 작업 강제하면 빈 체크리스트 의례로 전락한다(우리가 경계한 over-engineering, codex 도 "빈 회고" 우려 지적). 핵심 *통찰*(위험 변경 전 제약 인지)은 유효하나, **일반 dlc 단계로 박을 형태가 아니다.**
  - *대체 커버*: 그 실패 사례 자체는 §11 feedback 메모리(`rtk-headroom-path-fix.md` — "rtk hook 직접 편집 금지" 행동지시) + #49 self-diagnosis(이탈 사후 감지)로 부분 커버됨. 일반 예방 규칙은 두지 않는다.
- **[합의 — 당시] retrospect 는 별도 단계 ✗(Report 흡수), 의무화 ✗, dlc-only ✗.** → #49 self-diagnosis 가 유사 취지로 머지되며 해소.

# Key Files
- `skills/dlc/SKILL.md` — #46/#49 로 이미 개선됨 (이 브랜치는 미반영)
- `~/.claude/projects/.../memory/rtk-headroom-path-fix.md` — invariant-check 가 막으려던 실패 사례 + 현 대체 커버
- (참고) `CLAUDE.md` §11/§12 — feedback 메모리 메커니즘(#47)

# Blockers
(없음 — 종결)
