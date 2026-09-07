---
title: dev-cycle-skill — 자동 개발 사이클 파이프라인 skill (dlc 로 개명, 완료)
status: done
started: 2026-05-28
updated: 2026-05-29
---

# Goal

자동 개발 사이클(규모 gate → explore → plan → 리뷰 → TDD → 구현 → 리뷰 → simplify → 검증 → report)을 `skills/dev-cycle/SKILL.md` 로 명문화. 기존 5개 reviewer subagent + codex 병행을 hub-and-spoke 로 오케스트레이션하고, 메인이 plan 파일을 single source of truth 로 유지한다.

# Progress

- 2026-05-28: 전 세션에서 16단계 순서 + 8개 합의 항목 + 규모 gate(trivial/small/medium/structural) 확정.
- 2026-05-28: 세 질문(미결 의미 / codex skill화 / 단계별 subagent 격리) + 미결(arch planning-mode)을 codex(gpt-5.5, reasoning effort xhigh)로 foreground 교차검토. background 금지 — 직전 세션의 `thinking blocks cannot be modified` API 400 회피.
- 2026-05-28: codex 합의 — Claude 큰 방향 동의 + 보정 8건 수령(아래 Decisions).
- 2026-05-28: 사용자 결정 D1=A(phase owner)/D2=초안/D3=자동 트리거+gate. 3파일 작성·검증 완료:
  - `docs/codex-review.md`(신규) — 위치를 `agents/_codex-review.md` 에서 변경(agents/ 는 frontmatter `name` 기반 agent 오인식 위험).
  - `agents/architecture-reviewer.md`(수정) — `mode: planning|post-implementation` 추가 + Codex 병행 섹션에 docs 참조 포인터.
  - `skills/dev-cycle/SKILL.md`(신규).
  - `.gitignore` 에 `!/docs/` 추가 — codex-review.md cross-machine 추적(참조 무결성).
  - 검증: 참조 정합성 3곳 ✅, dev-cycle skill 등록 ✅, 사용자 dirty 파일 미접촉 ✅. (markdown 산출물이라 lint/test 없음.)
- 2026-05-29: skill 이름 `dev-cycle` → `dlc` 개명(`skills/dlc/`, `/dlc`). dlc 본체·`docs/codex-review.md`·architecture-reviewer mode·README dlc 가 PR(#1~#4)로 **main(3124dd6) 전부 머지 완료**. 작업 브랜치 로컬·원격 정리. **dlc skill 작업 완료.**

# Next

완료. 남은 후속(별도 작업, 선택):
1. 나머지 4개 reviewer agent(plan-reviewer/code-reviewer/code-simplifier/researcher)의 인라인 codex 블록을 `docs/codex-review.md` 참조로 일괄 교체(현재 architecture-reviewer 만 포인터).
2. CLAUDE.md §3 ↔ dlc 자동 트리거 연동 명문화.
3. 관찰: dlc 자동 트리거 description 광범위 — 실사용 오발동/미발동 모니터.

# Decisions

## 세 질문 답 (Claude 분석 + Codex 합의)

- **Q1 "미결"의 정체**: 16단계 중 4번 `arch-light(planning mode)`. `architecture-reviewer.md` 가 입력으로 `git diff`·변경 symbol 호출부·생성 경로를 요구(36-46행)하고 트리거가 코드 변경(diff) 전제(19-34행)라, 계획 단계엔 diff 가 없어 그대로 못 돈다. → 계획 단계 구조 검토를 어떻게 돌릴지가 미결.
- **Q1 해결 = (A) 채택**: `architecture-reviewer.md` 에 `mode` 추가. (B SKILL 내 wrapper 는 입력번들 로직을 복제해 Q2 중복을 재생산 → 기각). Codex 강제 조건:
  - 호출 프롬프트 첫 줄 `mode: planning | post-implementation` 명시. **기본값 post-implementation**(기존 동작 보존).
  - planning 입력 번들: plan 파일 / 관련 기존 코드 / 예상 변경 symbol·계층 / non-goals / 제약 / researcher 결과.
  - planning 출력은 "코드 문제"가 아니라 "plan 수정 요구". 존재하지 않는 코드에 `file:line` 금지.
  - planning mode 에선 arch 의 codex 중첩 호출 기본 off(plan-reviewer codex 와 중복 방지).
  - planning 섹션이 커지면 그때 별도 `architecture-planner` agent 고려. 지금은 A.
- **Q2 codex 구조화 = 공유 reference 문서**: 사용자 `/skill` 아님. `agents/_codex-review.md` 로 추출. (Codex 지적: subagent 는 격리 컨텍스트라 dev-cycle SKILL 내부 섹션을 자동으로 못 본다 → SKILL 섹션이 아니라 reference 문서가 정답). 필수 내용: `codex --version` preflight / `--sandbox read-only --skip-git-repo-check --ephemeral` / effort 기본값 / `CLAUDE_REVIEW_CODEX_MODE=external` 처리 / non-blocking 실패 fallback / 출력 요약 규칙 / **Windows·PowerShell fallback**(현 agent 문서의 bash heredoc·`grep`·`tail` 가정이 Windows 에서 깨질 수 있음).
- **Q3 subagent 격리 경계 = 리뷰만 격리**: 흐름제어·구현·통합·최종판단은 메인(hub). 리뷰/검토(plan-reviewer, arch, code-reviewer, researcher)는 격리 spoke. `.claude/plans/<slug>-plan.md` 가 공유 채널(subagent 끼리 직접 context 공유 안 함). Codex 보정:
  - **code-simplifier 는 순수 리뷰 아님 — `Edit` 권한 보유**(code-simplifier.md:4). "격리된 mutating refactor 단계"로 분류. 메인이 diff 흡수 + targeted test + targeted re-review 필수.
  - 구현은 기본 메인이나 절대 원칙 아님. 큰 작업 + 파일 소유권 분리 시 보조 구현 subagent 가능. 현 5개 agent 는 리뷰용이라 dev-cycle 기본값은 "메인 구현".
  - Explore 도 "전부 메인"보다 "메인이 얇게 소유 + 큰 검색은 보조 가능".

## Codex 추가 실패모드 (전부 반영)

1. **규모 gate 재판정**: Setup 규모는 예비값. Explore 후 / 구현 diff 후 재판정. small→public API·DB·2계층이 되면 skip 했던 arch·plan-review 단계 되살림.
2. **fix loop 종료조건**: "최대 2회"만으론 부족. 각 finding 에 `fix / defer / false positive / wontfix` disposition table. 2회 후 같은 class 잔존 시 `blocked` 또는 명시적 risk accept.
3. **plan 파일 동시성**: subagent 는 plan 쓰지 않음. 메인만 single writer. 쓰기 직전 re-read 후 외부 변경 merge.
4. **검증 명령 미식별**: README/package/pyproject/Makefile/CI 확인해도 없으면 "미식별" 기록 + 추측 실행 금지. 이 상태에서 "검증 완료" 금지.
5. **TDD Red 오판**: 새 테스트가 의도한 이유로 실패했는지 확인. 기존 baseline failure 와 섞이면 Red 무의미.
6. **researcher 재진입**: code-review 중 버전/API/CVE 의문 시 언제든 researcher loopback.
7. **Codex phase owner**: reviewer 들이 각자 codex 부르면 quota/속도/충돌. dev-cycle 이 "이번 phase codex owner" 1개 지정.
8. **skill 길이 리스크**: 16단계 전부 본문에 풀면 체크리스트로만 소비됨. "규모 gate 표 + 상태 전이 + 필수 산출물" 중심으로 짧게.

## 확정 16단계 (structural 기준)

0 Setup(git status·규모 예비판정·plan) → 1 Explore → 2 researcher(조건부) → 3 draft plan → 4 arch planning-mode(structural만) → 5 plan 수정 → 6 plan-reviewer → 7 지적 반영(구조 변하면 4~6 재실행) → 8 TDD Red → 9 구현 → 10 Green → 11 arch(정밀)+code-reviewer 병렬 → 12 fix loop(관련 reviewer만, ≤2회+disposition) → 13 code-simplifier(blocker 없을 때만) → 14 simplifier substantive edit 시 targeted 재리뷰 → 15 최종 검증 → 16 Report+plan 업데이트.

# Key Files

- `skills/dev-cycle/SKILL.md` — (신규) 파이프라인 오케스트레이션. 규모 gate 표 + 상태 전이 중심.
- `docs/codex-review.md` — (신규) codex 호출 공유 reference. agents/ 는 agent 오인식 위험으로 docs/ 채택. `.gitignore` `!/docs/` 로 추적.
- `agents/architecture-reviewer.md` — (수정) `mode: planning | post-implementation` 추가.
- `agents/{plan-reviewer,code-reviewer,code-simplifier,researcher}.md` — (참조/후속) codex 블록을 `_codex-review.md` 참조로 교체는 후속 가능.
- `skills/wt/SKILL.md` — (참고) 기존 skill 포맷 레퍼런스.

# Blockers

- 없음 (완료).
