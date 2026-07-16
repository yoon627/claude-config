---
title: asset-cleanup — Workstream B: 미사용·중복 운영 자산 정리 (감사 결정 반영)
status: done
started: 2026-07-04
updated: 2026-07-04
---

# Goal
2026-07-02 전수 감사에서 사용자가 승인한 자산 정리: ① agents 의 codex 블록 중복 제거(docs/codex-review.md 참조화) ② commands/local-review 제거 ③ code-simplifier subagent 제거 → dlc 13단계 내장 체크리스트 ④ agents `model: opus` 상속화(제거) ⑤ CLAUDE.md §5·README 동기화. 상위: `<main>/plans/2026-07-02-workflow-loopify/` Workstream B.

# Progress
- 2026-07-04: worktree 생성, draft plan.

# Next
없음 — PR #71 머지 완료, CI 통과. 후속(defer 3건)은 plans/2026-07-04-doc-slim 에 인계됨.

# Progress (추가)
- 2026-07-04: plan-reviewer(+codex 병행) CONDITIONAL — 강한 우려 2(arch-reviewer 위임 7곳·model 상속 acceptance 공백) + 약한 우려 6 전부 Decisions 반영(model 은 inherit 명시로 전환). classify 순수 매칭·improve.sh :89 안전·상속 문서 근거 등 검증 확정 사항 확보.

# Decisions
- (감사·사용자 승인 2026-07-02) local-review 제거 근거: per-repo hook 의존·실사용 2회·dlc 리뷰 단계+빌트인 /code-review 로 충분. code-simplifier 체크리스트화 근거: 실사용 0회·CLAUDE.md 가 이미 "메인 직접 점검 가능" 허용 — 현실을 규약으로 승격. model 상속화 근거: 모델 세대 교체 시 수정 지점 0(Fable 상실 대비).
- codex 블록 참조화: architecture-reviewer.md 가 선례(공통 규약은 docs/codex-review.md 참조 + agent 고유 트리거·프롬프트만 보유) — code-reviewer.md·plan-reviewer.md 를 같은 구조로(고유 유지: 호출 조건·effort 등급·도메인 프롬프트·출력 형식의 Codex 병행 섹션).
- **arch-reviewer skip (Explore 후 판정)**: 이번 변경은 "문서만 변경" — arch-reviewer 정의의 호출 금지 조건 해당 → 4(planning)·11(정밀) 생략, 사유 기록. TDD 도 §7 예외(문서 — 수동 검증 절차 명시): 검증 축 = improve.sh 기계 점검 + 잔존 참조 grep + CI + 신규 simplify 체크 규약의 자기 적용(dogfood).
- **simplify 체크리스트 내장 형태**: dlc 13단계를 "[메인 직접 · blocker 없을 때만]"로 바꾸고 격리 경계 절의 code-simplifier bullet 을 체크 항목(중복 3회+·과한 추상화·불필요 옵션·죽은 코드·과한 방어·표준lib 대체·깊은 nesting / 동작 보존·범위 내·불확실 보류 / substantive 수정 시 14 targeted 재검증)으로 교체. 근거: 실사용 0회 + CLAUDE.md 가 이미 메인 직접 점검 허용 — 현실을 규약으로 승격, agent 정의 삭제.
- **model 상속화의 wiki 영향**: effort-global-xhigh 결정(모델 opus 명시)과 어긋나므로 그 페이지에 "model 명시 → 세션 상속 변경(2026-07-04, Fable 상실 대비 수정 지점 0)" 반영 + index 요약 갱신. superseded·이력 페이지(subagent-model-effort-tiering 등)의 code-simplifier 언급은 이력이라 보존, **현행 서술** 페이지(dlc-development-cycle·hub-and-spoke-isolation·dual-review-plan-and-code 중 현행 파이프라인 서술)만 동기화.
- CLAUDE.md 편집 범위: §5(code-simplifier bullet→simplify 체크, 표준 순서, 필수 문구), §9(선택 목록에서 code-simplifier 제거), §10 말미(`/local-review` → 빌트인 `/code-review` 수동 사용). 그 외 섹션 불변.

- **plan-review 반영 (2026-07-04, CONDITIONAL→GO 조건)**: ① agents/architecture-reviewer.md 의 code-simplifier 위임 참조 7곳(8·17·18·75·81·85·173행)을 "메인 simplify 체크(dlc 13단계)"로 재지정 — 편집 대상 추가. ② model 은 **제거가 아니라 `model: inherit` 명시**(4 agents) — 상속 의도를 자기서술해 조용한 약화 미감지 리스크 차단(근거: wiki claude-code-subagent-config:17-18 미지정=세션 상속·inherit 별칭 유효). ③ dlc SKILL :40(규모표)·:108(runner 의 'simplifier(Edit) 도 아닌 제3 범주' 정의 대조) 추가. ④ wiki claude-codex-collaboration:17 추가, hub-and-spoke-isolation 은 "mutating spoke 소멸 → 모든 spoke read-only" 구조 귀결을 명시 서술. ⑤ README :5(intro 대표 예시 재작성)·:259(5개→4개) 명시. ⑥ dlc-doc-drift.test.js:28 의 local-review fixture 를 생존 경로로 교체(classify 는 순수 문자열 매칭 — CI 비회귀 확정, staleness 만 해소). ⑦ wiki/log.md 필요 여부는 WIKI.md 규약 확인 후 판정.
- codex 참조화 시 **agent 고유 유지 목록 확정**: 호출 조건 + effort 등급 + 도메인 프롬프트 + 출력 추출 grep 패턴 + 통합 방침 1줄(plan-reviewer 의 "충돌 시 메인 판단 위임" 포함) + 출력 형식의 Codex 병행 섹션. 공유 규약(preflight·owner·sandbox·Windows·출력처리 일반·통합 일반)만 docs/codex-review.md 참조로 대체.

# Key Files
- agents/code-reviewer.md·plan-reviewer.md — codex 블록 → docs/codex-review.md 참조화
- agents/code-simplifier.md — 제거 / skills/dlc/SKILL.md — 13단계를 메인 직접 체크리스트로 교체
- agents/*.md (4 잔존) — `model: opus` → `model: inherit` / agents/architecture-reviewer.md — code-simplifier 위임 7곳 재지정
- commands/local-review.md — 제거
- CLAUDE.md §5(sub-agent 목록·표준 순서)·§9(리뷰 매트릭스의 code-simplifier 언급) — 동기화
- README.md — agents/·commands/·해당 절 동기화 / .github/workflows/lint.yml — 영향 없음 예상(확인)

# Blockers
(없음)

# Acceptance
1. 잔존 참조 0: `git grep -l "local-review"`·`"code-simplifier"`(subagent 로서의 참조 — dlc 체크리스트 서술 제외)·agents 내 codex 호출 명령 블록 중복 없음.
2. dlc 13단계가 agent 호출이 아닌 메인 체크리스트로 동작 가능하게 서술됨(단계 번호·fix loop 연계 불변).
3. agents 4파일 frontmatter `model: inherit` + description/tools 유지 (제거 아님 — 상속 의도 자기서술).
4. `bash skills/improve/improve.sh` error=0 (CLAUDE.md 참조 agent 실존 점검 통과 — code-simplifier 참조 제거 후).
5. CI lint.yml 로컬 재현 통과(변경이 js/sh 없으면 해당 없음 확인만).
6. README·CLAUDE.md 동기화 diff 존재 + 서술이 실제 자산과 일치.

# Review Disposition
- [code-review Major] docs/codex-review.md 상대경로 참조 + Read 지시 부재(격리 subagent 에서 미해석 → sandbox 없는 codex 임의 호출 위험) — **fix**: 절대경로 `~/.claude/docs/codex-review.md` + "호출 전 먼저 Read" 명령형 명시 (2 agents).
- [code-review Minor] docs §4 PowerShell fallback ↔ CLAUDE.md §9 Bash 강제 — **defer**(pre-existing, Bash 도구 부재 환경용 fallback 이라 실모순 아님·문구 정리는 Workstream C).
- [code-review Minor] dlc small 경로에 simplify 미명시 ↔ CLAUDE.md "모든 코드 변경 필수" — **defer**(pre-existing 설계 긴장, C 의 3중 기술 슬림화에서 단일 소스로 정리).
- [code-review Minor] architecture-reviewer 의 inline codex 명령 잔존(비대칭) — **defer**(참조+고유 예시 형태가 기존 선례, 통일은 C).
- [code-review Nit] superseded 링크 문구·fixture 유지 — **wontfix**(dead link 아님·classify 순수 로직 방어 커버리지 정당).

# Deferred
- (C 인계) docs/codex-review.md §4 PowerShell 문구 ↔ §9 정합 / dlc small 규모 simplify 명시 여부 / arch-reviewer codex 블록 축약 통일.

# Workflow Findings
- evidence-ledger VERIFY 정규식이 **스크립트로 감싼 검증**(`bash /tmp/xxx-verify.sh` — CLAUDE.md §2 가 권장하는 실행 방식)을 인식 못 해 false negative → early-stop 오경고. 재발 조건: 검증 명령 묶음을 스크립트 파일로 실행하는 모든 턴(§2 권장과 정면 충돌이라 상시 재발). 수정 후보: `scripts/dlc-evidence-ledger.js` VERIFY 에 검증성 스크립트 패턴(`verify`·`test` 파일명) 추가 또는 exit code 관찰. 횟수 1 (2026-07-04).
