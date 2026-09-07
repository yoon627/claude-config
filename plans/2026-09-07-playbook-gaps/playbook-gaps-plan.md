---
title: playbook-gaps — AI-Native SDLC Playbook 격차 분석 결과를 A/B/C 그룹으로 반영
status: in_progress
started: 2026-09-07
updated: 2026-09-07
---

# Intent

## Problem

`# Intent` 도입(PR #162) 때 플레이북 Stage 1 만 반영하고 나머지 11개 플레이는 미조사로 남겼다. 그중 일부는 조직 장치라 해당 없지만, 메커니즘 층(자기검증 루프·계획 대비 대조·설정 변경의 회귀 검사)은 이 repo 와 겹친다. 분석 과정에서 플레이북과 무관한 **현재 설정의 실제 결함**도 드러났다.

## Constraints

- 플레이북은 스스로 *"written for large enterprises, and especially regulated ones"* 라고 밝힌다. 조직 장치(PO 승인·역할 분리·managed settings·DORA·릴리스 매니저)는 1인 환경에 구조적으로 해당 없다 — **메커니즘의 1인용 등가물**만 옮긴다.
- 운영 자산 자가 수정 금지(§1) — 사용자가 A+B+C 범위를 명시 승인했다.
- managed settings 는 관리자 권한이 없어 쓸 수 없다(2026-09-07 확인).
- §1 "무승인 자동 적립 금지" 와 충돌하는 자율 루프(bands.yaml 류)는 격차가 아니라 **의도적 선택**이다.

## Out of scope

skill 트리거 eval 코퍼스(structural) · managed settings 등가물 · `claude -p` CI 트리아지 · `bands.yaml` 응답 계층 · `REVIEW.md` 신설(code-reviewer 정의가 이미 그 역할).

## Open questions

- plan drift 축의 오탐률은 실사용 몇 세션 뒤 `/improve` 의 `early-stop-plan-drift` 신호 빈도로 판정해야 한다. 지금은 근거가 없다.

# Goal

격차 분석 결과를 세 그룹으로 반영한다 — A: 확인된 결함 정정, B: 계획·리뷰 규율, C: 검증 자동화.

# Progress

- 2026-09-07: 플레이북 12개 레슨 본문을 브라우저로 수집(SPA 라 WebFetch 불가). 수집 중 2개 페이지가 직전 페이지 내용으로 잘못 담긴 것을 발견해 개별 navigate 로 재취득.
- 2026-09-07: 격차 분석 workflow(22 agents). 11개 플레이가 **전부 `partial`** 로 균일해 status 축은 변별력 없다고 보고 폐기, 검증 통과 제안만 채택(28건 중 17건 검증 기각).
- 2026-09-07: A그룹 커밋 `9433787` — CI 누락 테스트 3개 등재 + `ask`/`allow` 사실 정정 + wiki 적립.
- 2026-09-07: B그룹 커밋 `3d04050` — ⚠️ self-flag · plan-reviewer 관점 3개 · code-reviewer plan 대비 축 · runner acceptance 대조.
- 2026-09-07: C그룹 커밋 — `verify.sh` · `improve.sh --ci` · plan drift 축 · `plan-match.js` 신규.

# Next

1. push → PR → CI → 머지
2. **main 복귀 후**: `lesson-parallel-duplicate-implementation` 의 `MEMORY.md` 인덱스 줄 적립(§13 짝 누락 — gitignored 라 worktree 에서 못 쓴다)

# Decisions

- **status 축 폐기** — 11/11 이 `partial` 이고 뒤집힌 판정 0건. "완전히 있다/없다"를 회피하는 분석 편향으로 보고, 제안 단위로만 판단했다.
- **A/B/C 를 별도 커밋으로** — 되돌림 경계를 나눈다. A 는 사실 정정이라 독립적으로 유효하다.
- **`verify.sh` 는 glob 발견** — 수기 목록이 A1 결함의 근본 원인이므로 목록 자체를 없앴다.
- **plan drift 는 좁게** — plan 파일이 실제 매칭될 때만 발동. §10 의 세션 내 active 추적은 hook 이 알 수 없어 false negative 를 감수한다(오탐이 이 축의 최대 위험).
- **`plan-match.js` 모듈 추출** — early-stop 에 매칭 로직을 복사하면 세 번째 사본이 된다. 기각안: 복사(drift 위험), session-brief 에서 export(hook 스크립트를 모듈로 쓰는 것은 부작용 위험).
- **`session_time.py` NUL 가드는 범위 밖이나 수정** — 새 검증 타깃을 깨는 직접 원인(§3-4 예외). main 에서도 실패하던 Windows 한정 baseline 임을 재현 확인했고, 기존 테스트가 이미 기대 동작을 정의하고 있었다.

# Key Files

- `scripts/verify.sh`(신규) · `scripts/plan-match.js`(신규, +test) — 단일 검증 타깃, 매칭 단일 소스
- `scripts/dlc-{early-stop,evidence-ledger,ledger,signal}.js` — plan drift 축
- `skills/improve/improve.sh` — `--ci` 모드
- `.github/workflows/lint.yml` — verify.sh 축별 호출 + 자산 정합 게이트
- `agents/{plan-reviewer,code-reviewer}.md` · `skills/dlc/SKILL.md` · `CLAUDE.md` · `README.md` · `wiki/`

# Blockers

(없음)

# Acceptance

1. `bash scripts/verify.sh` 가 `ALL PASS` — 검증: 실행 (22 tests, skip 없음)
2. `improve.sh --ci` 가 error=0 으로 exit 0 이고 안 돈 점검을 명시 — 검증: 실행
3. plan drift 축이 매칭 plan 있을 때만 발동 — 검증: `dlc-early-stop.test.js` 6 케이스(발동·미발동·plan없음·non-git·CAP·OFF)
4. `plan-match` 규칙이 잠김 — 검증: `plan-match.test.js` 11 케이스
5. CI 가 `verify.sh` 호출로 바뀌고 실제 CI 통과 — 검증: PR checks
6. 문서 drift 없음(README·CLAUDE.md·SKILL·wiki index) — 검증: `check_links.py` clean + 대상 파일 확인

# Deferred

- C 그룹 미채택분: `# Review Disposition` 집계를 `/improve` 축으로 · skill 트리거 recall 신호 · `workflow-failures` 회귀잠금 열 · nit 볼륨 상한 · `lint.yml` 최소권한 토큰.
- `agents/plan-reviewer.md` 에 `# Intent` 검토 항목 추가(PR #162 에서 이월).
- 플레이북 `closing-thoughts-and-resources` 미수집(리소스 목록).

# Workflow Findings

- 격차 분석 workflow 의 status 축이 11/11 `partial` 로 균일했다. 판정 카테고리를 주면 중간값으로 수렴하는 편향이 있으므로, 다음에는 status 대신 **"이 파일 이 줄이 그 메커니즘이다" 증거 제출 여부**로 갈라야 한다.
