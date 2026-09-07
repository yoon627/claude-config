---
title: dlc-final-verify-subagent — dlc 최종 검증을 격리 runner 실행으로 위임
status: done
started: 2026-06-04
updated: 2026-06-04
---

# Goal
dlc 15단계 최종 검증(전체 lint/typecheck/test/build)의 긴 출력을 메인 컨텍스트에서 덜어낸다. 격리 runner(general-purpose)가 메인이 지정한 명령·worktree cwd 로 **실행만** 하고 exit code+실패증거를 구조화 반환, 메인은 명령 식별·판단·실패 fix 책임 유지. Green(10)·14 targeted 재검증·trivial 검증은 메인 직접.

# Progress
- 2026-06-04: worktree 생성(base 8383e00). "최종 검증만 subagent" 결정. 변경 4곳 설계 확정.
- 2026-06-04: plan-reviewer(재시도, CONDITIONAL: critical1/major3/minor2)+codex 병행 검토 → 6 finding 전부 fix. 구현 — SKILL.md 4곳(격리경계·파이프라인·규모표각주·미식별규칙)+README:286 동기화. prompt 문서라 lint/test 무관, 마크다운·내부참조 일관성으로 검증.
- 2026-06-04: 커밋 `c20d43b` → push → PR #28 머지(no-ff `9a12c7c`, origin/main 갱신). worktree 정리(plan→main 이동 후 worktree+브랜치 삭제), main 복귀.

# Next
- 완료(머지 #28). main worktree(`C:\Users\USER\.claude`)에서 `git pull` 하면 dlc 신규약 적용(`8383e00`→`9a12c7c`).

# Decisions
- **검증 runner = 빌트인 general-purpose** (`.claude/agents/` 비어있음 — code-reviewer 등은 harness 빌트인). 검증은 Bash 실행이라 read-only spoke 와 구분.
- **격리 = 완료 전 최종 검증(전 규모)**. Green(10 구현 직후 최소)·14 targeted 재검증·trivial 검증은 메인. 경계는 *범위*(전체 스위트 vs 최소·targeted). 이유: 구현↔검증 즉시 루프를 subagent 경유로 만들면 spawn 왕복 손해(plan-reviewer C1/codex 반영).
- **제3 범주 표기**(plan-reviewer M2): 검증 runner 는 read-only 도 simplifier(Edit) 도 아님 — 소스 불변이나 build/test 산출물·캐시 생성. 49행 read-only 그룹에 안 넣음.
- **명령·cwd 전달**(plan-reviewer M3/codex 계약): 메인이 식별한 명령을 **문자열 그대로 + worktree 절대 cwd** 로 전달, runner 는 재탐색·수정·수리 안 함. cwd 누락 시 엉뚱한 디렉토리 검증 → silent false-pass. exit code+실패증거 구조화 반환, 불충분하면 불완전 검증으로 간주(메인 재실행).
- **검증 실패 처리 ≠ 12단계 fix loop**(plan-reviewer M1): 검증 실패는 객관적이라 disposition(false-positive/wontfix) 대상 아님, 통과까지 메인 수정·재검증.

# Key Files
- skills/dlc/SKILL.md — 격리 경계(최종 검증 runner 제3 범주·실패처리·메인직접 신설), 파이프라인 15(`[격리 runner]`), 규모표 각주, 미식별 규칙 보강
- README.md:286 — dlc 격리 구조에 최종 검증 격리 반영

# Review Disposition (plan-reviewer 재시도 + codex 병행)
- C1[critical] 14 재검증 vs 15 충돌 → **fix** (14 targeted·Green·trivial=메인, 15 전체=격리 명시).
- M1[major] 검증실패 fix vs 12 fix loop 혼선 → **fix** (별개 메커니즘, disposition 무관 명시).
- M2[major] mutating 표기 → **fix** (제3 범주, read-only 그룹서 분리).
- M3[major] 명령전달+cwd 누락 → **fix** (문자열·절대 cwd, silent false-pass 경고, 미식별 규칙 보강).
- m1[minor] Green vs 최종 범위차 → **fix** (각주에 범위 명시).
- m3[minor] small/medium 격리 여부 → **fix** (각주 "전 규모").
- §63 정합·trivial 모순 없음 → 확인(no-op).

# Blockers
(없음)
