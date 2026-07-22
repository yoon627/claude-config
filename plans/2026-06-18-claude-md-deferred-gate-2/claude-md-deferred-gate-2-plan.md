---
title: claude-md-deferred-gate-2 — 운영자산 자가수정 금지 + # Deferred 규칙 (claude-md-deferred-gate 이어)
status: done
started: 2026-06-18
updated: 2026-06-18
---

# Goal
claude-md-deferred-gate(base 4f322b2, tmp e401d60) 미완 이어 — 최신 main(9679ac7)에 두 규칙 재적용: (1) §1 운영 자산 자가 수정 금지 (2) §3·§10 # Deferred(범위 밖 발견 기록). README §1·§10 설명 동기화.

# Progress
- 2026-06-18 worktree 신규(9679ac7, codegraph init). 요구 명확화 silent 통과(tmp가 명세). wiki/feedback no-op.
- 2026-06-18 Explore: tmp(e401d60) 내용 + 최신 §1(L22)/§3-4(L45)/§3-5(L46)/§10(L184)/README(L218,227) 재적용 위치 6곳 확정.
- 2026-06-18 plan-reviewer(Claude+codex): CONDITIONAL 🔴4 — tmp 단순 재적용의 함정 발굴. 매핑 위치는 정확하나 개념 충돌 해소 필요(아래 반영).
- 2026-06-18 구현 6곳(CLAUDE.md §1·§3-4·§3-5·§10 + README §1·§10), 충돌 4건 해소. 일관성 통과(§1↔§3-4↔self-diagnosis 정합, baseline 가드↔§1 에러무시, defer/Deferred 구분↔dlc SKILL, README 12개섹션 유지). 이 작업 자체가 자가수정금지 허용 케이스("이어해줘"+plan Key Files)=dogfooding. code-reviewer/simplifier 생략(markdown 규약·plan-reviewer+codex 선행·메인 직접 §5).
- 2026-06-18 커밋 `54788fe` → PR #50 머지. **status: done**. 구버전 claude-md-deferred-gate(tmp e401d60) 내용은 이로써 반영 완료 — 구버전 worktree/브랜치 정리 가능.

# Next
(완료) PR #50 머지. 남은 것: worktree 정리(claude-md-deferred-gate-2 merged, 구버전 claude-md-deferred-gate는 tmp 미머지지만 내용 #50 반영됨→-D) + main pull.

# Decisions
## 재적용 위치 (tmp → 최신 매핑)
1. CLAUDE.md §1: "사용자 변경사항 보호"(L22) 다음 "운영 자산 자가 수정 금지" 불릿.
2. CLAUDE.md §3-4 Implement(L45): 끝에 "범위 밖 발견 유실 금지 → # Deferred(§10) 기록".
3. CLAUDE.md §3-5 Verify(L46): "baseline failure(작업 전부터 깨진 것) → # Deferred 기록".
4. CLAUDE.md §10: 6섹션(L184) 다음 "선택 섹션 (# Review Disposition, # Deferred)".
5. README §1 설명(L218): "운영자산 자가수정금지" 추가.
6. README §10 설명(L227): "필수 6개 + 선택 섹션".

## 정합성 (최신 구조)
- 자가수정금지 vs dlc: dlc는 사용자 요청 하 자산수정 → "명시 요청 없이 금지"라 충돌 아님(요청 있으면 OK). 문구로 명확히.
- # Deferred vs # Review Disposition: 둘 다 §10 선택섹션. 구분 — Review Disposition=리뷰 finding(dlc fix loop), Deferred=범위밖 발견. tmp가 둘 다 명시.
- self-diagnosis(#49) "스코프 밖 파일 수정" 중대 신호 ↔ # Deferred(범위밖 발견 기록) 연결 — 일관.

## plan-reviewer 반영 (Claude+codex)
- 🔴 README: tmp "11개 섹션"은 stale(최신 12개, §11 LLM Wiki 존재) → tmp 재현 말고 **현재 구조에서 §1·§10 두 줄만** 갱신.
- 🔴 `defer`/`# Deferred` 글자충돌(dlc SKILL fix loop disposition 값 `defer` 기존) → §10에 구분 한 줄(`defer`=finding 처분 / `# Deferred`=범위 밖 발견 보존).
- 🔴 §3-5 baseline 우회 위험(§1 "에러 무시 금지" 자기모순) → "**입증된 baseline만**(pre-change 실행/base 재현), 미입증·완료 막는 실패는 # Deferred 금지 → 수정 or `status: blocked`/미검증" 가드.
- 🔴 발견 vs 수정 경계 → §3-4에 "**발견=기록 후 진행 / 수정=§1 자가수정·스코프 경계 → 별도 작업**" 분기(self-diagnosis "스코프 밖 수정" 중대와 정합).
- 🟡 "명시 요청" 정의 = active plan `# Goal`/`# Key Files` 포함 or 사용자 자산명+변경 지시. `# Review Disposition`도 dlc SKILL에서 §10 승격임을 명시. 운영자산은 "등"으로 여지.
- codex "21파일 rollback" = base..HEAD 전체 오해 → 기각(실제 5곳). rollback 단일 커밋으로.

# Key Files
- `CLAUDE.md` — §1·§3·§10.
- `README.md` — §1·§10 설명.

# Review Disposition
- 🔴 README 11→12 → **fix**(최신 구조 두 줄만). 🔴 defer/Deferred 충돌 → **fix**(§10 구분). 🔴 baseline 우회 → **fix**(입증 가드). 🔴 발견/수정 경계 → **fix**(§3-4 분기).
- 🟡 명시요청 정의·Review Disposition 승격·운영자산 범위 → **fix**. plan없음 휘발 → **defer**(현 "plan없으면 Report" 유지, wiki 승격은 별도).
- codex 21파일 → **false-positive**(base..HEAD 오해).

# Blockers
(없음)
