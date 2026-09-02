---
title: claude-md-fable51-guide — CLAUDE.md 에 Fable 5.1 프롬프팅 가이드 4건 반영
status: done
started: 2026-09-02
updated: 2026-09-02
---

# Goal
Anthropic "Prompting Claude Fable 5.1" 문서를 CLAUDE.md 와 대조해 사용자가 승인한 4건(§0 preamble 경계+수사 금지 · §4 이름 인지≠현재 상태 · §6 부분 편집 우선 · §7 테스트 규모 상한)을 CLAUDE.md 에 반영하고 README 의 섹션 요약을 동기화한다.

# Progress
- 2026-09-02: 문서 16개 섹션 대조 → 하네스 시스템 프롬프트가 이미 주입하는 블록(진행 업데이트·Finish the whole task·Delivering work·tool 배치)은 제외, 4건 제안 → 사용자 4건 모두 승인 → worktree 생성, 규모 small(단일 파일 doc, <50줄).
- 2026-09-02: CLAUDE.md 4곳 + README 요약 편집 → code-reviewer+Codex(low) 리뷰 Major 2·Minor 5·Nit 5 → fix loop 1회 반영(`sed` 제거·§7 경계 단서·§4 재배치 등) → simplify 수정 없음 → plan-lint 통과. 검증: lint.yml 표면(JS·sh·JSON) 미변경·마크다운 린터 없음 → diff 육안 대조로 acceptance 충족. 브랜치에 커밋 `117937c`.
- 2026-09-02: `/e` — 사용자 지시로 push·PR #147 생성·main 머지. status done.

# Next
- 없음 (머지 완료). Deferred 3건은 별도 작업으로.

# Decisions
- 하네스가 이미 주입하는 문장은 CLAUDE.md 에 중복 기재하지 않는다 (이유: 전문 100% 주입되는 파일이라 토큰 낭비이고, 하네스 버전이 바뀌면 이중 관리가 된다).
- §7 은 TDD 순서를 유지하고 *상한*(인접 테스트 규모·scratch 승격 금지)만 추가한다 (이유: 문서의 "commit tests only where the task asks" 를 그대로 넣으면 §7 기본 규칙과 충돌).
- §6 부분 편집 규칙은 "신규 파일·짧은 파일·대부분 변경" 예외를 명시한다 (이유: §2 "긴 명령은 `Write` 로 스크립트에" 와 Claude Code 하네스가 auto 모드에서 주입하는 "sed/heredoc 으로 파일 변경" 안내 — repo 문서가 아니라 세션 시스템 프롬프트에 있음 — 와 표면 충돌하지 않도록). 리뷰 반영으로 `sed` 는 규칙에서 뺐다 (이유: PreToolUse 훅 matcher 가 `Edit|Write|NotebookEdit` 뿐이라 Bash `sed` 는 `guard-worktree-edit.js` 의 worktree-밖 deny 를 우회한다 — `settings.json`·`scripts/guard-worktree-edit.js` 확인).
- §4 이름 검색 넛지는 원문이 `low` effort 한정으로 제시하지만 무조건으로 승격한다 (이유: 사용자 지시문은 effort 를 모르고, 검색 임계값을 낮추는 §4 기조와 일치). 원문의 "모르는 이름" 축도 포함하고, "원문 표기 검색어 포함" 은 신호 목록이 아니라 실행 규칙(우선순위 줄)에 둔다.
- 하네스 주입 문장 중복 여부: 이 세션의 시스템 프롬프트에서 "Before you start, say in a line…", "You are operating autonomously…", "# Delivering work", "Writing for the user", tool 결과 뒤 batch nudge 를 직접 확인(✅). CLAUDE.md 추가문은 허용문("억제하지 않는다")이지 그 지시문의 복제가 아니다.
- 규모 small: plan-reviewer 생략(medium 미만), code-reviewer 는 수행.

# Key Files
- `CLAUDE.md` — §0 L10 뒤, §4 L62 검색 신호, §6 L94 뒤, §7 L111 부근
- `README.md` — L219~L227 CLAUDE.md 섹션 요약(§0·§6·§7 한 줄)

# Blockers
(없음)

# Acceptance
- [x] CLAUDE.md §0: preamble 금지가 착수 한 줄·진행 업데이트·결론 요약을 억제하지 않음을 명시 + 수사 금지 1줄 — 검증: `grep -n "preamble" CLAUDE.md` 로 관찰.
- [x] CLAUDE.md §4 검색 신호에 "아는 이름 ≠ 현재 상태·원문 이름 검색어 포함" 추가 — 검증: grep 관찰.
- [x] CLAUDE.md §6 에 부분 편집 우선 규칙(예외 포함) 추가 — 검증: grep 관찰.
- [x] CLAUDE.md §7 에 테스트 규모 상한(인접 규모·scratch 승격 금지) 추가 — 검증: grep 관찰.
- [x] README CLAUDE.md 섹션 요약이 §0/§6/§7 변경을 반영 — 검증: `node scripts/dlc-doc-drift.js` 류 drift 없음 + diff 관찰.
- [x] `node scripts/plan-lint.js plans/2026-09-02-claude-md-fable51-guide/claude-md-fable51-guide-plan.md` 통과.
- [x] 하네스 주입 문장과 문구 중복 없음 — 검증: diff 관찰(리뷰어 대조).

# Review Disposition
code-reviewer + Codex(low) 병행, fix loop 1회.
- fix — §6 `sed` 명시가 worktree 훅 우회 (Major, 합의): `sed`·도구명 결박 제거, 동작 서술로.
- fix — §7 "동작당 1개" 경계 케이스 억제 오독 (Major, 합의): "경계·오류 조건은 그 동작의 일부" 단서 추가.
- fix — §4 신호 목록에 실행 규칙 혼입 (Minor): "원문 표기 포함" 을 우선순위 줄로 이동.
- fix — §4 "모르는 이름" 축 누락 (Minor): "모르거나, 알아도 현재 상태가 불확실한" 으로.
- fix — plan Decision 의 근거 미존재 지적 (Minor): 근거는 하네스 시스템 프롬프트임을 명시.
- fix — README §0 "예외" 프레이밍 역전 (Minor) / §4 요약 미갱신 (Nit) / §7 "scratch 승격 금지" 과장 (Nit) / "갈수록" 모호 (Nit) / §0 bold 스타일 (Nit).
- wontfix — §0:10 ↔ §3-6 중복 서술 (Nit): 양방향 cross-ref 로 유지(§3-6 은 기존 문장).
- false-positive — "하네스 주입 여부 미확인" open question: 메인 세션 시스템 프롬프트에서 확인(Decisions 참조). subagent 프롬프트에는 없어 리뷰어가 볼 수 없었던 것.

# Deferred
- 모델 전략 memory(`model-strategy-fable-plan-opus-impl.md`): 문서상 Fable 5.1 `medium` ≈ Fable 5 품질·저비용, `low` 도 Opus 대비 경쟁력 — "Fable 은 계획 전용" 전략 재검토 후보. 심각도 낮음.
- `wiki/WIKI.md`: 문서 요약 시 원문을 인용 표시 없이 재현하는 경향 증가 — ingest 규약에 인용 표시 규칙 후보. 심각도 낮음.
- hook/스크립트 tool 출력에 base64 포함 여부 점검(safeguard 오탐 유발). 심각도 낮음.
