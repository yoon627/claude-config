# Review Disposition
- 조항별·게이트 대조(codex-review·wiki-inbox·headroom — 139조항)
  - AMBIGUOUS codex-review 61행 "leaks tokens" 가 인증 토큰 유출로 읽힌다 — fix: "wastes tokens".
  - AMBIGUOUS wiki-inbox 40행 "stored as `deferred`" — fix: "archived as `deferred`"(`inbox archive` 로 닫는 흐름).
  - 선택 문구 2건(codex-review 31행 "usage overrun", headroom 46행 "misjudged … as 0") — wontfix 아님, 리뷰어가 지적이 아니라고 밝힌 선택 사항이라 그대로.
- 조항별·게이트 대조(worktree-lifecycle·dlc-details — 224조항)
  - AMBIGUOUS worktree-lifecycle 28행 "merges the patch-ids" — fix: "combines the patches into one with a different patch-id".
  - AMBIGUOUS 57행 "If it already stopped" — fix: "If the remove already stopped partway".
  - AMBIGUOUS 103행 "outside `/e merge`·`[post-merge]`" — fix: "other than the `/e merge` Task(s) and `[post-merge]` items"(skills/e M1 (5) 와 같게).
- code-reviewer(5개 문서) — APPROVE(승인·확인·안전·검증·리뷰 규칙 완화 없음, 5개 check PASS·변형 전부·check_links·schema clean)
  - 원문부터 §E M5 가 skills/e 보다 낡음(jq `t: .startedAt`, 다른 실패 → REJECTED 없음) — fix: 번역 뒤 별도 공용 wiki 커밋 `docs(worktree-lifecycle): sync §E M5 with skills/e`.
  - 공개 점검 — codex-review 56행의 repo 이름 — fix: 별도 커밋 `docs(codex-review): describe the removed gate without naming the repo`. 같은 이름이 공용 wiki 페이지 5곳·log 에 더 있다 → Deferred(사용자 결정).
  - Minor dlc-details 헤딩이 dlc 의 영어 절 이름을 쓴다 — 그대로 맞음: translate-skill-dlc 가 같은 이름(Requirement clarification·Investigation protocol·wiki integration·Isolation boundary)으로 옮겼다.
  - Nit dlc-details 30행 기록 형식이 영어, `workflow-failures.md` 표 머리는 한국어 — Deferred(페이지 쪽은 wiki/pages 언어 결정과 함께).
  - Nit worktree-lifecycle 5·18행 "no automatic deletion"·"skip the proposal" 이 §8(a) 자동 정리보다 엄격한 옛 서술 — Deferred(문서를 규칙에 맞추면 확인 서술이 느슨해지므로 위임 예외 밖 — 사용자 결정).

# Deferred
- 공용 wiki 페이지 5곳(`pages/decision/wiki-shared-layer.md`·`workflow-failures.md`·`lesson-agent-hook-if-best-effort.md`, `pages/entity/codegraph.md`·`worktree-isolation-bash-guard.md`)과 `log.md` 에 개인 repo 이름이 있다 — 그 repo 가 비공개면 §11 공개 점검 위반. 이 세션은 그 repo 에 접근할 수 없어 공개 여부를 모른다 — 사용자 결정
- `docs/worktree-lifecycle.md` 5·18행의 옛 서술("no automatic deletion"·"skip the proposal")을 CLAUDE.md §8(a) 자동 정리에 맞추기 — 확인 서술을 느슨하게 하는 변경이라 사용자 확인 필요
- `docs/dlc-details.md` 30행 Workflow Findings 기록 형식과 `pages/decision/workflow-failures.md` 표 머리 맞추기 — wiki/pages 언어 결정(intent Open question)과 함께
