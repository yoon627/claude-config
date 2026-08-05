---
title: lesson-parallel-dup — 병렬 에이전트 중복 구현 교훈 §13 적립
status: done
started: 2026-08-05
updated: 2026-08-05
---

# Goal
Claude 와 다른 도구가 같은 기능을 각자 구현해 한쪽(PR #120, 553줄)이 통째로 폐기된 사건을 §13 형식으로 적립한다 — wiki lesson 페이지(상세) + `MEMORY.md` feedback 인덱스(자동 상기).

# Progress
- 2026-08-05: worktree 생성(base `origin/main@64dfaa2`). 증거 확정 — #118(2026-08-04 14:42 머지)과 #120(2026-08-05 00:12 생성, 분기점 `d38c70b`=#116)이 같은 기능. #120 커밋에 Claude 트레일러 없음(다른 도구 추정).

- 2026-08-05: lesson 페이지 작성, `wiki/index.md`·`wiki/log.md` 동기화 완료.

- 2026-08-05: 링크 검사(outbound 4·dead 0·index 34=34)·CI 스위트 `ALL PASS` 후 PR #130 머지.

- 2026-08-05: main 복귀 후 memory 2단계 저장 완료 — `check-inflight-work-before-starting.md` + `MEMORY.md` 인덱스 줄(명령형). Acceptance 5항목 전부 충족.

# Next
없음 — 완료.

# Decisions
- **`lesson-*.md` 신규 페이지로 적립** (이유: §13 이 정한 형식. [[workflow-failures]] 추적표는 *hook·규약이 낸 반복 신호*를 세는 곳이고, 이번 건은 신호가 없는 1회성 협업 설계 문제라 성격이 다르다).
- **"Codex 가 작성했다"고 단정하지 않는다** (이유: PR #120 커밋에 `Co-Authored-By: Claude` 트레일러가 없다는 정황뿐 — ⚠️추정으로만 표기. §1 추측 금지).
- **memory 는 2단계 저장** (이유: §12·§13 — wiki 는 능동 조회라 자동으로 안 떠오르고, 매 세션 주입되는 유일 경로가 `MEMORY.md` 인덱스 줄이다).
- **memory 저장은 worktree 밖(main 복귀 후)에서 수행하도록 변경** (이유: memory 는 gitignored 라 worktree 사본이 없고, worktree 격리 가드가 공유 체크아웃 경로 Write 를 차단한다. repo 커밋 대상이 아니므로 브랜치와 무관하게 마지막에 쓴다).

# Key Files
- `wiki/pages/decision/lesson-parallel-duplicate-implementation.md` — 신규 lesson
- `wiki/index.md` · `wiki/log.md` — 동기화
- `~/.claude/projects/-Users-jongyoonlee--claude/memory/` — feedback memory (gitignored, repo 커밋 대상 아님)

# Blockers
없음.

# Acceptance
1. lesson 페이지에 원인(3 Whys)·재현 조건·잘못된 방법·올바른 방법이 있고 outbound 링크 ≥2. 검증: 육안 + grep
2. 사실 주장에 근거(PR 번호·sha·날짜) 표기, 미확정은 ⚠️추정 표기. 검증: 육안
3. `wiki/index.md` 등재 + `wiki/log.md` append. 검증: grep
4. memory 파일 + `MEMORY.md` 인덱스 **둘 다**, 인덱스는 명령형 행동 규칙. 검증: 두 파일 확인
5. CI 스위트 통과. 검증: `.github/workflows/lint.yml` 로컬 실행

# Deferred
(없음)

# Workflow Findings
(없음 — 이 작업 자체의 실패는 없다. 적립 대상은 선행 작업의 실패다)
