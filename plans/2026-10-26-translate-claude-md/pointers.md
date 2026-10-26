# 가리키는 곳 (translate-claude-md)

CLAUDE.md 의 글자를 따옴표로 인용하거나 CLAUDE.md 와 같은 형식 문자열을 쓰는 곳. 형식: `` - `파일` | «새 영어 문구» | «옛 한국어 문구» `` — 새 문구는 CLAUDE.md 와 그 파일 양쪽에 글자 그대로 있고, 옛 문구는 그 파일에 더 없어야 한다(`check-en.js`, Acceptance 4·6).
범위: 따옴표·backtick 안 인용과 형식 문자열만. `§0 언어 정책`·`§10 대응표` 처럼 절 번호와 함께 쓴 따옴표 없는 서술 참조는 그 파일이 번역될 때 옮긴다(절 번호로 찾을 수 있다).

## 따옴표 인용
- `skills/c/SKILL.md` | «**Start**» | «"시작: 매칭 plan read 후 컨텍스트 복원 / 진행 중 동기화"»
- `skills/c/SKILL.md` | «**In-progress sync**» | «"시작: 매칭 plan read 후 컨텍스트 복원 / 진행 중 동기화"»
- `skills/dlc/SKILL.md` | «"if ambiguous, ask first"» | «"모호하면 질문"»
- `skills/dlc/SKILL.md` | «"unverified"» | «/"미검증"(CLAUDE.md §1)»
- `skills/dlc/SKILL.md` | «"wrap up"» | «"마무리·정리" 선택지»
- `skills/e/SKILL.md` | «**Turn end**» | «"턴 종료 / 완료"»
- `skills/e/SKILL.md` | «"push only on request"» | «"push 는 요청 시만"»
- `skills/e/SKILL.md` | «**Completion**» | «"머지 시점에 done"»
- `agents/architecture-reviewer.md` | «"optional"» | «"선택" 카테고리»
- `README.md` | «**Active plan tracking**» | «"세션 내 active 추적"»
- `skills/e/SKILL.md` | «continue from the `wip:` commit at the branch tip» | «브랜치 tip 의 `wip:` 커밋 이어서»
- `scripts/plan-match.js` | «the dir whose slug contains the current git branch» | «현재 git branch 가 slug 에 포함된 dir»

## 공유 형식
- `skills/dlc/SKILL.md` | «in a ~/.claude main session: /wiki ingest <summary · public evidence · source (public/private)>» | «/wiki ingest <요약 · 공개 근거 · 출처(공개/비공개)>»
- `skills/wiki/SKILL.md` | «in a ~/.claude main session: /wiki ingest <summary · public evidence · source (public/private)>» | «/wiki ingest <요약 · 공개 근거 · 출처(공개/비공개)>»
- `README.md` | «in a ~/.claude main session: /wiki ingest <summary · public evidence · source (public/private)>» | «/wiki ingest <요약 · 공개 근거 · 출처(공개/비공개)>»
- `skills/wiki/SKILL.md` | «`public`/`private`» | «`공개`/`비공개` 만»
- `skills/dlc/SKILL.md` | «(not started)» | «(미착수)»
- `skills/dlc/SKILL.md` | «[bundle]» | «[묶음]»
- `skills/dlc/SKILL.md` | «`- [ ] NEEDS-HUMAN: <question> — <options>`» | «NEEDS-HUMAN: <질문> — <선택지>»
- `skills/dlc/SKILL.md` | «`what is satisfied`» | «`무엇이 충족되나`»
- `skills/dlc/SKILL.md` | «`pass criterion`» | «`통과 기준`»
- `skills/e/SKILL.md` | «(not started)» | «(미착수)»
- `skills/e/SKILL.md` | «(resolved)» | «(해소)»
- `skills/e/SKILL.md` | «(carried over → » | «(이월 → »
- `skills/e/SKILL.md` | «`dropped`» | «`폐기`»
- `skills/e/SKILL.md` | «`<slug candidate> (not started) — note`» | «(미착수) — 메모»
- `agents/plan-reviewer.md` | «(not started)» | «(미착수)»
- `agents/plan-reviewer.md` | «[bundle]» | «[묶음]»
- `plans/2026-10-21-ops-docs-rework/intent.md` | «(not started)» | «(미착수)»
- `plans/2026-10-21-ops-docs-rework/intent.md` | «(open)» | «(열림)»
- `plans/2026-10-21-ops-docs-rework/intent.md` | «(resolved)» | «(해소)»
- `plans/2026-09-29-repo-context-kit/intent.md` | «(not started)» | «(미착수)»
- `plans/2026-09-29-repo-context-kit/intent.md` | «(open)» | «(열림)»
- `plans/2026-09-25-repo-audit-followups/intent.md` | «(not started)» | «(미착수)»
- `plans/2026-09-25-repo-audit-followups/intent.md` | «(resolved)» | «(해소)»

## 역방향 인용 — 그 파일의 번역 단위가 제목을 이 영어로 맞춘다 (intent Constraints)
- dlc 요구사항 명확화 → requirement clarification (`skills/dlc/SKILL.md` 제목)
- 분할 판정 → split judgment (`skills/dlc/SKILL.md`)
- 커밋 단위 → commit units (`skills/dlc/SKILL.md` 제목)
- dlc 증거기반 자기개선 → evidence-based self-improvement (`skills/dlc/SKILL.md` Workflow Findings 절)
- 규모표 → size table (`skills/dlc/SKILL.md` 0. 규모 gate)
- 16단계 커밋 규칙 → step 16 commit rules (`skills/dlc/SKILL.md`)
- worktree 정리 규칙 → worktree cleanup rules (`skills/e/SKILL.md` 제목)
- 묶음 모드 → bundle mode (`agents/plan-reviewer.md`)

## [post-merge] 공용 wiki — main 세션
- `~/.claude/wiki/docs/dlc-details.md` — `/wiki ingest <요약 · 공개 근거 · 출처(공개/비공개)>` 형식 → 영어 형식
- `~/.claude/wiki/docs/wiki-inbox.md` — «공개 점검» → «Public check», "회사 repo" → "company repo"
- `~/.claude/wiki/pages/concept/plan-handoff.md` — «### 묶음 intent»·«진행 중 동기화» 인용 → 영어 라벨
- 그대로(역사 기록 — 그때의 문구를 인용한 것): `pages/decision/workflow-failures.md`·`wiki-shared-layer.md`·`lesson-stale-tool-version.md`·`dlc-wt-autoflow.md`·`e-merge-mode.md`·`feedback-memory.md`·`comment-and-commit-policy.md`·`risk-based-approval.md`
