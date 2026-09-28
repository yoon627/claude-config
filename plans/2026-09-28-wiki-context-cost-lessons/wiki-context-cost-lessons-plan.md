---
title: wiki-context-cost-lessons — 컨텍스트 비용 실측·교훈 2건 공용 wiki 적립
status: done
started: 2026-09-28
updated: 2026-09-29
---

# Goal
2026-09-28 토큰 절감 분석에서 확정한 사실(1M auto-compact 기본값·설정, 캐시 재작성 원인, transcript 집계 방법)과 교훈 2건을 공용 wiki 에 적립한다.

# Intent
- Problem: 분석 결과가 대화와 보류 plan(branch claude-md-slim)에만 있어 다른 세션·repo 가 같은 조사를 반복하거나 같은 실수(중복 합산·기존 결정 미조회)를 한다.
- Constraints: 공개 repo — 비공개 repo 이름·회사 식별자·개인 금액 금지, 수치는 비율·토큰 수만(CLAUDE.md §11). 같은 주제는 기존 페이지 갱신(§12·§13), 규칙 원칙(ops-doc-slimming)은 바꾸지 않는다.
- Out of scope: 기존 log.md 의 과거 줄에 있는 비공개 식별자 정리(아래 Deferred). CLAUDE.md·skill 규칙 변경. memory(MEMORY.md) 갱신은 main 복귀 후 별도(§3-1).
- 분할: 없음 — 신규 페이지와 교훈 사례가 서로를 링크해 한 머지에서만 링크가 유효하다.

# Progress
- 2026-09-28: 신규 entity claude-code-context-cost, ops-doc-slimming 재검토 절, lesson-grep-absence-not-proof 사례 7, lesson-verify-scaffold-purpose-before-removal 사례 4, index·log 동기화. check_links clean, 변경분 공개 점검 통과.
- 2026-09-29: code-reviewer(+Codex) REQUEST CHANGES — Major 3·Minor 10·Nit 5 전부 처분(아래). 공식 문서 인용 3건은 원문(env-vars·prompt-caching)을 직접 읽어 확인 후 수정. 측정 스크립트 6개를 `analysis/` 로 보존(보류 브랜치 claude-md-slim 은 미게시라 근거 경로로 부적합).

# Next
없음 — Acceptance 1~4 충족(check_links clean · 추가 줄 공개 점검 0건 · 공식 문서 원문 대조 후 수정 · verify.sh ALL PASS), 로컬 ff-merge 로 main 반영. 후속은 `# Deferred`.

# Decisions
- 규모 medium(문서 약 70줄)이지만 plan-reviewer 생략 — 코드 변경 없는 wiki 적립이고 사실은 이 세션에서 공식 문서·실측으로 확인했다. 대신 사후 code-reviewer 를 사실 정확성·공개 점검 관점으로 돌린다.
- 교훈은 새 페이지를 만들지 않고 같은 축의 기존 lesson 에 사례로 추가(중복 방지 — §12 유지 규칙).
- 커밋 단위: 1개 — 서로 링크하는 문서 묶음.

# Acceptance
1. `uv run --no-project python ~/.claude/skills/wiki/check_links.py wiki` → `clean`.
2. 변경 파일에 비공개 식별자·개인 금액 없음 — rg 점검 결과 0(과거 줄 제외).
3. 신규 페이지의 공식 문서 사실(967K·100000~1000000·우선순위·할증 없음·0.05×·2×)이 출처 원문과 일치 — code-reviewer 대조.
4. `bash scripts/verify.sh` → `ALL PASS`(skip 없음).

# Review Disposition
- [Major] `autoCompactWindow` scope("user settings" 오기)·env 정수 함정·managed 우선 누락 — fix(원문 env-vars:214·model-config 대조).
- [Major] index 의 "`/effort` 는 아님" 일반화 — fix: 공식(prompt-caching: 대부분 모델 무효화, Opus 5.5·Fable 5.1 만 유지, 2.1.260 전 Fable 도 무효화) 인용, cwd 는 "세션 중 이동은 무관·세션 간 디렉토리별 캐시".
- [Major/PLAUSIBLE] 절대 토큰 합계 × 공개 단가로 개인 사용 규모 역산 — fix: 절대 합계 삭제, 배수·비율만.
- [Minor] TTL 조건(구독 포함 사용량 안의 본 대화만) — fix.
- [Minor] 3.6~6.6% 분모 표기·"약 4%" 혼재 — fix: 산식 명시, 본 세션 평균 대비 4.4% 병기.
- [Minor] 기대효과 1~2% 가정 부재·시뮬레이션 기준 — fix: 압축률 11~30% 가정 명시(0.4~2%), "본 세션 비용 기준".
- [Minor] 표본을 일반 사실로 — fix: "이 표본" 한정.
- [Minor] 근거 브랜치 미게시·원인표 스크립트 미보존 — fix: analysis/ 에 6개 보존, sources 에 미게시 표기.
- [Minor] 재작성 정의(60K)·n — fix: 정의 보강, 신호별 n.
- [Minor] 3 Whys 가 재발 조건까지 안 감 — fix: 사례 4 Why 3 을 트리거 공백으로, 사례 7 에 3 Whys 추가. 구조 변경은 Deferred 제안.
- [Minor/PLAUSIBLE] "기각" 확정 표현 — fix: "기각 권고".
- [Minor/PLAUSIBLE] 무신호 재작성 원인 단정 — fix: index ⚠️, 본문에 공식 무효화 후보 나열.
- [Minor/PLAUSIBLE] 3.6~6.6% 가 계산값·이중 주입 기간 — fix: 계산값 명시, 2026-09-27 전 worktree 이중 주입 주석.
- [Nit] 5건(공식 절의 실측 문장·import 바이트·"재현"→"실측"·lesson 도입부·범위 표현 통일·68%→47.5% 오귀속) — fix. 68% 는 중복이 아니라 단가 가정 차이였음을 사례 7a 에 반영.
- [Open] Sonnet 5 단가 — false-positive: bundled SKILL.md 모델 표에 $2/$10 이 있다(cache read 0.1× → $0.20). tokenizer 차이 — 본문에 "sonnet 으로 측정, 다를 수 있음 ⚠️" 명시.

# Key Files
- plans/2026-09-28-wiki-context-cost-lessons/analysis/ — 측정 스크립트(call_stats2·cost_stats·simulate·rewrite_markers·rate_by_version·mdtok)
- wiki/pages/entity/claude-code-context-cost.md — 신규
- wiki/pages/decision/ops-doc-slimming.md — 2026-09-28 재검토 절
- wiki/pages/decision/lesson-grep-absence-not-proof.md — 사례 7
- wiki/pages/decision/lesson-verify-scaffold-purpose-before-removal.md — 사례 4·적용 범위 확장
- wiki/index.md · wiki/log.md — 동기화

# Deferred
- wiki/log.md 과거 줄(81·171·173·238·245)에 개인 repo 이름과 회사 티켓 키로 보이는 문자열이 있다 — 공개 점검(§11) 위반 후보 — Major — 이미 push 된 이력이라 파일 수정만으로는 이력에서 사라지지 않는다. 정리 범위(파일만/이력 재작성) 사용자 결정 필요 — 별도 작업. (2026-09-29 처분: 이력은 그대로 두기로 결정. wiki 밖 파일의 회사 식별자는 `0db7fde` 로 정리, wiki 속 식별자는 wiki 보관 방식 결정과 함께 — 사용자 로컬 memory 에 기록)
- wiki 조회 트리거 공백: §11 의 조회 시점은 "작업 시작 시" 뿐이고 dlc Explore 의 wiki 조회는 조건부(절차는 자동 로드 안 되는 docs/dlc-details.md §C) — 같은 세션에서 분석 → 운영 자산 변경 계획으로 넘어갈 때 조회가 걸리지 않는다(lesson-verify-scaffold-purpose-before-removal 사례 4) — Minor~Major — 운영 자산(CLAUDE.md §11·skills/dlc) 변경이라 제안만(§1): "draft plan 전 wiki index 를 대상 자산명·작업 종류로 조회" 를 dlc 3단계 체크에 넣는 안. (반영 2026-09-29: 사용자 승인, skills/dlc/SKILL.md 3단계·wiki 연계 + docs/dlc-details.md §C + README)

# Blockers
