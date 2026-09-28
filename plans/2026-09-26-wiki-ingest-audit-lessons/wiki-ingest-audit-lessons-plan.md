---
title: wiki-ingest-audit-lessons — 감사 후속 작업의 외부 사실 3건·교훈 2건 wiki 적립 + wiki 공용 계층 결정 기록
status: done
started: 2026-09-26
updated: 2026-09-26
---

# Goal

repo-audit 후속 작업(PR #174~#177)에서 확인한 외부 사실(statusline 입력, CI 비밀 스캔 설계, GitHub 민감정보 제거 절차)과 교훈 2건(도구 셸 `grep` 대체로 인한 비ASCII 오판, Stop hook 이 Bash 편집을 못 보는 오탐)을 wiki 에 적립한다. 사용자가 고른 wiki 구조 결정(repo 결정은 각 repo, 공용 사실은 `~/.claude/wiki`, submodule 기각)을 decision 으로 남긴다. memory feedback 줄은 main 복귀 후 별도로 적는다(worktree 에선 불가).

# Intent

- 사용자 선택(2026-09-26): "wiki ingest + 교훈 적립", wiki 구조는 "`~/.claude/wiki` 공용", ingest 는 "지금 계속".
- 규모: small(문서만 — 새 페이지 5, 갱신 2, index·log).
- Constraints: 페이지는 확인한 사실만(출처 plan·스크립트·실측). 절차 원문은 README 가 정본이라 복제하지 않고 가리킨다. 공용 계층 구현(skill 2단 조회)은 운영 자산 변경이라 이 작업에서 하지 않는다.
- Out of scope: wiki skill·CLAUDE.md §11 변경(별도 plan), Stop hook 수정(intent `repo-audit-followups` 의 `audit-low-batch`).

# Acceptance

1. 새 페이지 5개(`claude-code-statusline-input`·`claude-code-bash-tool-shims`·`github-sensitive-data-removal`·`ci-secret-scan-backstop`·`wiki-shared-layer`)가 frontmatter·outbound 링크 2개 이상·sources 를 갖춘다. 검증: `uv run --no-project python skills/wiki/check_links.py wiki` 가 `clean`.
2. `lesson-grep-absence-not-proof` 에 도구 셸 `grep` 사례, `workflow-failures` 에 Bash 편집 오탐·중간 턴 오탐 두 줄이 들어간다. 검증: 파일 확인.
3. `wiki/index.md` 에 새 페이지 5개 등재, `wiki/log.md` 에 ingest 줄. 검증: check_links(index 동기화 포함).
4. 전체: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음), plan-lint 통과.

# Progress

- 2026-09-26: 착수. 비ASCII 오판 원인을 재현으로 정정 — grep 바이트 범위식이 아니라 Claude Code Bash 도구 셸의 `grep` 셸 함수(내장 ugrep). Stop hook 오탐은 이 세션 24회 중 17회가 Bash·python 편집·검증 미추적, 4회가 중간 턴.
- 2026-09-26: 페이지 작성 중 원인 재정정 — 오늘 본 Rust panic 은 ugrep(C++)이 아니라 rtk 훅이 바꾼 `rtk grep`. 경로별 재현: 도구 `for`·`$(…)` 안 → 내장 ugrep 7.8.4 → 0(09-25 오판), 단순 명령 → `rtk grep` panic, 스크립트 안 → `/usr/bin/grep` 2. `rtk rewrite` 는 루프·치환을 재작성하지 않음(exit 1) 확인. 새 페이지 5·갱신 4(grep lesson·workflow-failures·subagent-config·project-memory)·index·log. Acceptance 1~4 충족: check_links `clean`(orphan 2건은 subagent-config·project-memory 에서 inbound 링크로 해소), plan-lint ok, `bash scripts/verify.sh` ALL PASS(skip 없음). 문서만이라 code-reviewer 생략 — 주장은 출처 plan·스크립트·재현과 직접 대조.

# Next

(없음 — 로컬 ff-merge 로 종료. memory feedback 2건(grep 경로, Stop hook 오탐 대응)은 worktree 밖 글로벌 상태라 main 세션에서 이어서 적는다.)

# Decisions

- 비ASCII 교훈은 새 lesson 페이지가 아니라 `lesson-grep-absence-not-proof` 에 사례로 더한다(이유: 같은 실패 — grep 0 을 부재로 확정. §12 같은 주제는 기존 파일 갱신). 도구 셸 대체 자체는 외부 사실이라 entity 로 따로 둔다.
- Stop hook 오탐은 lesson 이 아니라 `workflow-failures` 의 행으로 둔다(이유: hook 오탐 누적 추적이 그 표의 역할이고, 수정 위치는 `audit-low-batch`).
- wiki 구조 결정은 구현 전이라도 decision 페이지로 남긴다(이유: 기각한 submodule 안과 근거가 plan 에만 있으면 다음 세션이 같은 제안을 다시 꺼낸다).
- 커밋 단위: 1개 — 문서 적립 한 목적.

# Key Files

- `wiki/pages/entity/claude-code-statusline-input.md` — 신규.
- `wiki/pages/entity/claude-code-bash-tool-shims.md` — 신규.
- `wiki/pages/entity/github-sensitive-data-removal.md` — 신규.
- `wiki/pages/decision/ci-secret-scan-backstop.md` — 신규.
- `wiki/pages/decision/wiki-shared-layer.md` — 신규.
- `wiki/pages/decision/lesson-grep-absence-not-proof.md`, `wiki/pages/decision/workflow-failures.md` — 사례·행 추가.
- `wiki/index.md`, `wiki/log.md` — 동기화.
- `wiki/pages/entity/claude-code-subagent-config.md`, `wiki/pages/concept/project-memory.md` — 새 페이지로 inbound 링크.

# Blockers

# Deferred

- (낮음) `wiki/pages/concept/project-memory.md` "plans/ 와의 경계" 가 `plans/` 를 "worktree 별·gitignored" 로 적음 — 지금은 tracked(CLAUDE.md §10). 이 작업은 링크 절만 더했다.

- wiki 공용 계층 구현(wiki skill 이 `<repo>/wiki` 와 `~/.claude/wiki` 를 함께 조회, CLAUDE.md §11 문구) — 사용자 결정 2026-09-26, 별도 plan. 근거는 `wiki/pages/decision/wiki-shared-layer.md`.
