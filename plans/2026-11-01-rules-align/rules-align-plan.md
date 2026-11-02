---
title: rules-align — CLAUDE.md 와 skill·agent 사이 규칙 불일치 12건 정리
status: done
started: 2026-11-01
updated: 2026-11-02
---

# Goal
2026-11-01 점검(보고 페이지 §3, 아래 결정표 R1~R12)에서 나온 CLAUDE.md ↔ skill/agent 규칙 불일치를 CLAUDE.md 를 정본으로 맞춘다. CLAUDE.md 쪽을 고치는 것은 넷 — R3 squash 예외, R8 wiki `plans/` 구절 삭제, §9 괄호 하나(R6), §10 `Size:` 라벨 한 항목(code-reviewer 1차) — 이다(사용자 2026-11-01 "규칙 불일치 12건" 선택 — 항목별 diff 확인 후 커밋).
- Why: 번역 뒤 포인터 감사에서 운영 문서끼리의 포인터는 모두 맞지만 같은 규칙을 두 문서가 다르게 적는 곳이 12곳 나왔다. 모두 번역 전부터 있던 것이다. 다음 세션이 어느 쪽을 따를지 매번 갈린다.
- Constraints: 규칙의 뜻을 바꾸는 변경이라 CLAUDE.md §8 위임 예외 밖 — 커밋 전 사용자 diff 확인 1회(아래 "느슨해지는 것 L1·L3·L4·L5·L6·L8·L9(강화 T1·T2 포함)" 을 그 질문에 함께 보인다). 확인은 `git diff --word-diff`(CLAUDE.md 줄이 1~2천 자라 일반 diff 는 한 단어 변경을 숨긴다). 공용 wiki(`docs/worktree-lifecycle.md` 5·18행, `docs/codex-review.md`, `docs/wiki-inbox.md`, `pages/concept/claude-codex-collaboration.md`:20)는 main 세션에서 [post-merge]. `terms.md` 는 audit-mechanical 머지 뒤 rebase 해서 고친다. `~/.agents/skills/*`·`~/.codex/AGENTS.md` 가 이 파일들의 symlink 라 Codex 세션도 같은 변경을 받는다. 사용자 지시: 묻지 말고 끝까지, push 는 끝에 한 번. 이 단위는 medium 이지만 사용자 지시로 로컬 ff-merge 한다(CLAUDE.md:143 의 `/e merge` 경로 대신 — 사용자 지시 예외).
- Out of scope: 규칙 자체의 재설계(fail-open 정책 등) · CLAUDE.md 줄이기 · dlc/e 의 머지 흐름 변경.
- Open questions: 로컬 default 기준으로 만든 worktree 에 `EnterWorktree` 한 뒤 격리 가드가 `git stash apply` 를 허용하는지 — 미검증(e:116 선택지 1).
- Split: none — purpose-commit bundle: 2026-11-01 점검 보고 §3 · 군 1)~7) · 각 군은 양쪽을 함께 고치므로 혼자 머지돼도 모순이 없고, 군마다 따로 되돌릴 수 있게 커밋을 나눈다(한 plan 으로 두는 이유는 고정비).

# Tasks
- [x] 군 1) done·merged 의미 — `skills/e/SKILL.md`:41·42·134: "done 은 머지되는 커밋에 쓴다(ff 전 기록 커밋, 또는 M4 — [[e-merge-mode]])" 를 원칙으로 적고, 사후 done 은 가드 3개가 모두 맞을 때만 확인 없이: (a) `[post-merge]` 외 미완료 Task 없음·`# Acceptance` 전부 체크 (b) 브랜치가 자기 커밋을 만들었음(`git reflog show --format=%gs refs/heads/<BR>` 에 `commit`·`cherry-pick`·`revert` 항목 — 또는 그 head 의 PR 이 MERGED 이고 headRefOid 가 HEAD 의 조상이며 이 브랜치 reflog 에 있음; code-reviewer 가 "plan 파일이 default 에 존재" 가드를 약하다고 봐 교체, 2차에서 이름 재사용 시 옛 PR 통과를 reflog 확인으로 막음) — 가드는 `BR ≠ <default>` 에서만, default 브랜치면 묻는다 (c) 머지 신호(로컬 default `--merged`, 또는 `gh pr view --json mergedAt`). 셋 다 맞으면 done 을 쓰고 plan(+log) 기록 커밋 `docs(plan): record <slug>` 을 만들어 "merged 인데 머지된 커밋에 done 없음 — 기록 커밋 생성, ff-merge 필요" 보고(uncommitted done 은 7단계 정리를 막는다 — M1), (a)·(b) 중 하나라도 빠지면 지금처럼 확인. `skills/c/SKILL.md`:40·42 `origin/main` → `<default>`(로컬 default, 없으면 `origin/<default>`) + :61 merged=done 에 같은 가드(b) — 커밋 0개인 새 worktree 는 "시작 전" 이지 merged 가 아니다. `CLAUDE.md`:145~146 squash 예외: "(`/e merge` 가 `mergedAt` 을 확인한 squash 는 (a); `git branch -d` 가 거부하면 `-D` 는 확인 뒤)". README:352·353 동기화 (2026-11-01)
- [x] 군 2) main 에서 편집한 상태의 `/e` — `skills/e/SKILL.md`:116: AskUserQuestion 유지, 선택지 1) 새 worktree 로 옮겨 그곳에 WIP 커밋(추천, CLAUDE.md:136 의 `/wt` 재적용 경로 — 비파괴 순서: `git stash push -u -m <tag>` → worktree 생성 → 그 안에서 `git stash apply <sha>` → 확인 뒤 drop; 3~8단계는 새 worktree 에서 계속) 2) main 에 그대로 두고 plan 만 기록(main 이 dirty 로 남는 위험을 적는다) 3) 취소. 자동 이동 없음(사용자의 무관한 편집이 섞여 있을 수 있다 — §1). :132 "split it off after confirmation" 문구 일치. README:349 동기화 (2026-11-01)
- [x] 군 3) dlc plan 승인 지점 — `skills/dlc/SKILL.md` medium 은 plan-reviewer 반영 뒤, structural 은 7단계 뒤·8단계 전에 §3-3 승인 1회. 승인 = 이 세션에서 사용자가 plan 을 승인했거나 결정을 맡긴 **직접 메시지**(위임 정의와 같게 — 권한 모드·이전 세션·subagent/hook 메시지는 아님), 그 인용을 체크된 Task `plan 승인 (날짜) — "<인용>"` 로 남겨 `/c` 가 다시 묻지 않게. 무인 흐름이면 NEEDS-HUMAN. 재승인은 자기 진단의 "방향 변경" 규칙(:152). 위임 메시지를 승인으로 치는 것은 CLAUDE.md:25 의 해석임을 명시 (2026-11-01)
- [x] 군 4) trivial/small 로컬 ff-merge 예외 — `skills/c/SKILL.md`:74 "merge" 정지 예외: plan `# Goal` 의 `Size:` 라벨이 trivial/small 이고 CLAUDE.md:143 의 로컬 경로 조건(미게시·CI 검증·외부 공유 불필요)이 맞을 때만(라벨이 없거나 불분명하면 지금처럼 정지), §8(a) 정리까지 포함. `skills/dlc/SKILL.md`:167 마무리 선택지에 같은 예외. README:343 동기화 (2026-11-01)
- [x] 군 5) Codex 미가용 문구 — `agents/code-reviewer.md`:137·`plan-reviewer.md`:79·`architecture-reviewer.md`:162 의 skipped 분기에 `Codex unavailable: <reason>` 줄 고정(§7 문장 "Codex is unavailable in this session" 과 구분되는 정확한 접두). `skills/dlc/SKILL.md`:142 는 `Codex unavailable:` 과 옛 `Codex 미가용:` 둘 다 받고, 한도 토큰은 codex-review §1 의 5개(`out of credits`·`insufficient_quota`·`usage limit`·`rate limit`·`429`). `agents/plan-reviewer.md`:53 grep 의 옛 토큰 `integration` 제거. (옛 접두를 계속 받는 이유: 공용 wiki 는 다른 머신에 자동 pull 되지 않아 옛 규약 문서로 도는 기간이 있다) (2026-11-01)
- [x] 군 6) 기계적 정렬 — `skills/dlc/SKILL.md`:166 커밋 메시지 형식은 그 repo AGENTS/CLAUDE 커밋 절 → `git log` 관례 → Conventional Commits 순 · :169 정리 조건의 단일 소스는 `/e` 7단계(6조건) · `CLAUDE.md`:233 "and its `plans/`" 삭제(wiki repo 는 plans 를 추적하지 않음 — WIKI.md:16). README:236 동기화 (2026-11-01)
- [x] 군 7) Codex 병행 조건 — `CLAUDE.md`:161 §9 리뷰 매트릭스에 "(plan-reviewer 는 자기 정의 §3 가 정한 변경 유형에만)" 괄호, `agents/plan-reviewer.md`:41 "when available" 을 :43 과 같게 (2026-11-01)
- [x] e:97 — `.env`·미보존 산출물이 있으면 "정리를 건너뛰고 목록을 적는다"(군 1 커밋에 포함 — 정리 조건) (2026-11-01)
- [x] 군별 패치 저장(`git diff > <scratch>/rules-k.patch` → `git add`) → code-reviewer(완화 여부 항목별 명시 요청) → simplify 점검 → `bash scripts/verify.sh changed` → plan-lint (2026-11-01)
- [x] 사용자 diff 확인(word-diff, L1·L3·L4·L5·L6·L8·L9·T1·T2 명시) → `git reset`(mixed) 뒤 패치를 군 순서대로 `git apply --cached` + 커밋 6개(군 4·6 은 하나) (2026-11-02)
- [x] audit-safety-net 머지 뒤 rebase → `plans/2026-10-21-ops-docs-rework/terms.md` 의 `Codex 미가용`·`결론` 행 갱신(기록 커밋에) → 기록 커밋 → ff-merge(push 는 끝에 한 번) (2026-11-02)
- [x] [post-merge] main 세션 공용 wiki: `docs/worktree-lifecycle.md` 5·18행을 §8(a) 에 맞춤 · `docs/codex-review.md` §1·§7 의 `Codex 미가용` → `Codex unavailable`(옛 접두 병기 기간 명시), §5 grep 의 `결론` 제거 · `docs/wiki-inbox.md`:5·23 에 "push 는 launchd 스크립트가 하고 agent 는 하지 않는다 — §11 의 요청 시 push 와 어긋나지 않는다" 1줄 · `pages/concept/claude-codex-collaboration.md`:20 매트릭스·문구 (2026-11-02)

# Acceptance
1. 결정표 R1~R12 각 항목에 대해 두 문서가 같은 말을 한다 — 양쪽 줄 인용이 `# Decisions` 표에 있고, code-reviewer 가 항목별로 완화/강화/중립을 판정해 L1·L3·L4·L5·L6·L8·L9·T1·T2 와 일치
2. `rg -n "origin/main" skills/c/SKILL.md` 0; `rg -c "Codex unavailable:" agents/code-reviewer.md agents/plan-reviewer.md agents/architecture-reviewer.md` 각 1; `rg -c "Codex unavailable:|Codex 미가용:" skills/dlc/SKILL.md` 1줄(둘 다 그 줄); `rg -n "integration" agents/plan-reviewer.md` 의 grep 패턴에 없음
3. `node scripts/frontmatter-lint.js` 전 agent·skill 통과, `node scripts/plan-lint.js` 이 plan 통과, README 5곳(236·343·349·352·353) 갱신 — `dlc-doc-drift` 경고 없음
4. `bash scripts/verify.sh changed` 가 `ALL PASS`
5. 사용자가 word-diff 를 확인했다(AskUserQuestion 기록) — L1·L3·L4·L5·L6·L8·L9·T1·T2 가 질문 본문에 있었다
6. 커밋 7개(군 커밋 6개 — 군 4·6 은 dlc:169·170 이 한 hunk 로 섞여 하나 — + plan·log·terms 기록 커밋 1개)가 단위와 1:1 — `git log --format=%s <base>..HEAD`

# Decisions
- 정본: CLAUDE.md(§1 "CLAUDE.md 우선"). 예외 — R3(squash: `mergedAt` 확정은 e 가 맞다), R8(wiki repo `plans/` 는 2026-10-09 사용자 결정으로 미추적), R6(plan-reviewer 의 Codex 조건은 비용 결정 — CLAUDE.md §9 가 그것을 가리킨다; 기각: plan-reviewer 를 "가능하면 항상" 으로).
- R9(wiki-inbox push)는 CLAUDE.md 를 고치지 않는다 — push 는 launchd 스크립트가 하고 `claude -p --restricted` 세션은 셸이 없다(docs/wiki-inbox.md:5·23). agent 규칙인 §11 과 어긋나는 것이 아니라 문서 쪽 설명 부족이므로 wiki 문서에 1줄. 기각: §11 에 예외 문장(항상 주입되는 글이 늘고, 세션이 push 허가로 읽을 수 있다 — plan-reviewer).
- done 전환(R1·R10): 원칙은 "머지되는 커밋이 done 을 담는다"([[e-merge-mode]], 기록 커밋 a81eb53·70e60d8 선례). 사후 done 은 가드 3개(미완료 Task 없음·브랜치가 자기 커밋을 만들었음(reflog `commit` 항목 또는 PR MERGED + headRefOid 조상 — "plan 파일이 default 에 존재" 는 plan 이 이미 default 에 있으면 커밋 0개 브랜치도 통과해 기각)·머지 신호) + 가드 done 은 plan 기록 커밋을 만들고 ff-merge 필요를 보고한다(uncommitted done 은 머지된 브랜치를 dirty·ahead 로 남겨 7단계 정리가 막힌다 — code-reviewer M1). 가드 done 은 bundle intent 도 확인 없이 닫는다(e:42 — L4 에 포함). 기각: e:41 의 확인을 그냥 없애기(plan-reviewer — 새 worktree 의 커밋 0개 브랜치가 merged 로 보이고, 미완료 Task 가 있어도 done 이 되며, done 이 머지된 브랜치에 uncommitted 로 남아 정리가 건너뛰어진다).
- e:116(R2): 확인 유지 + 추천 선택지를 `/wt` 이동으로. 기각: 자동 이동(main 의 무관한 편집까지 WIP `add -A` 로 옮긴다 — §1 사용자 변경 보호), "plan 만 기록" 삭제(사용자가 이동을 거부하면 plan 을 동기화할 길이 없다).
- dlc 승인 지점(R5): 승인 정의를 위임 정의와 같게 두고 인용을 Task 로 남긴다 — 사용자의 "묻지 말고" 지시와 충돌하지 않게. 유인 세션은 AskUserQuestion 으로 묻고, 물을 수 없는 무인 흐름만 NEEDS-HUMAN(code-reviewer). 위임 메시지를 §3-3 승인으로 치는 것은 완화 **L9**. 기각: 정의 없이 "승인" 만 적기(묻거나 건너뛰는 두 방향으로 갈린다).
- `Size:` 라벨(code-reviewer — c:74 의 "plan 이 규모를 적은 경우" 를 읽을 자리가 없었다): CLAUDE.md §10 `# Goal` 라벨 불릿에 `Size:`(한 단어 `trivial|small|medium|structural`, 재판정 시 갱신) 를 더한다 — dlc 요구사항 명확화가 쓰고(plan 있는 small 도) 규모 재판정 규칙이 갱신하며 c:74 는 이 라벨만 읽는다(없으면 지금처럼 정지). CLAUDE.md 변경이 R3·R8·R6 밖으로 한 항목 늘었다(§10 불릿 목록의 한 항목). 같은 군에 dlc:172 "ff-merge 전 기록 커밋에 `status: done` 을 싣는다"(e 4단계 원칙) 추가.
- 군 4·6 합침: dlc:169(R7 메시지 규약)와 :170(R12 선택지)이 인접해 `git diff -U0` hunk 하나로 묶인다 — code-reviewer 재분할 지시("한 hunk 가 두 군을 섞으면 그 두 군을 한 패치·커밋으로")에 따라 군 4 와 6 을 한 커밋으로 둔다. 기각: 줄 단위 hunk 를 수작업으로 쪼개기(지시 밖이고 재현이 어렵다).
- Codex 문구(R11): `Codex 미가용` → `Codex unavailable:`. translate-wiki-docs(codex-review manifest:92·check.json:51)와 translate-agent-plan-reviewer log:33 이 유지로 정했던 것을 뒤집는다 — 이유: 규약 문서·dlc·agent 가 모두 영어가 됐고 영어 리뷰어가 한국어 접두를 쓸 보장이 없다. dlc 는 전환 기간 옛 접두도 받는다. `plans/2026-10-31-translate-skill-dlc/check.json`:17 은 옛 글자를 고정한 역사 기록이라 FAIL 로 남는다(verify 밖, 수용).
- 결정표(R# · CLAUDE.md ↔ skill · 택한 쪽 · 완화/강화/중립):
  - R1 CLAUDE.md:182 "머지 시점에 done" ↔ e:41·42·134 "done 은 사용자 확인" · 원칙 + 가드 · **L4 완화**(가드 안에서만 확인 생략 — 가드 done 은 기록 커밋을 만들고, bundle intent 도 확인 없이 닫는다)
  - R2 CLAUDE.md:136 `/wt` 재적용 ↔ e:116 "plan 만 기록" 선택지 · 확인 유지, 추천 선택지 변경 · 중립
  - R3 CLAUDE.md:145~146 squash → (b) ↔ e:61·96 `mergedAt` → (a) · e · **L1 완화**(`mergedAt` 확정 squash 만)
  - R4 CLAUDE.md:145 `<default>`·로컬 main 인정 ↔ c:40·42 `origin/main` · CLAUDE.md + 커밋 0개 가드 · **L5 완화**(merged 신호가 넓어짐)·가드로 상쇄
  - R5 CLAUDE.md:47 §3-3 승인 ↔ dlc 파이프라인에 지점 없음 · CLAUDE.md · **T1 강화** + **L9 완화**(위임 메시지를 §3-3 승인으로 친다)
  - R6 CLAUDE.md:161 "Codex 가능하면 병행" ↔ plan-reviewer:43 조건부 · plan-reviewer, §9 괄호 · **L3 완화**(문서화)
  - R7 CLAUDE.md:140 커밋 형식 정본 ↔ dlc:166 `git log` 관례 · CLAUDE.md · 중립
  - R8 CLAUDE.md:233 "and its `plans/`" ↔ WIKI.md:16 미추적 · 구절 삭제 · **L8 중립**(실효 없는 규칙 제거)
  - R9 CLAUDE.md:232 push 요청 시 ↔ wiki-inbox 무인 push · 변경 없음(wiki 문서 1줄) · 중립
  - R10 CLAUDE.md:182 ↔ e:41 확인 / c:61 무확인 · R1 과 같은 가드 · (L4)
  - R11 dlc:142 `Codex 미가용` ↔ agent 템플릿에 없음 · 영어 접두 고정, 둘 다 수용 · 중립
  - R12 CLAUDE.md:25·143 trivial/small ff-merge ↔ c:74 정지 / dlc:167 `/e merge` 만 · 예외 추가(`Size:` 라벨 있을 때만) · **L6 완화**(CLAUDE.md:143 과 같은 조건 — 미게시·CI 검증·외부 공유 불필요)
  - 그 밖: e:97 정리 건너뛰기(**T2 강화**), dlc:169 단일 소스(중립), plan-reviewer:53(중립), plan-reviewer:41(중립)
- 커밋 단위: 1) `docs(e,c): write done in the merged commit and guard after-the-fact done` 2) `docs(e): offer the /wt move when wrapping up on main` 3) `docs(dlc): add the plan approval point and define approval` 4) `docs(c,dlc,claude-md): let trivial and small work finish with the local ff-merge; align commit convention, cleanup source and the wiki plans clause`(군 4+6 — dlc:169·170 이 한 hunk) 5) `docs(agents,dlc): pin the Codex unavailable line` 6) `docs(claude-md,plan-reviewer): state plan-reviewer's Codex condition in the review matrix` — 한 파일 안에서 군이 섞이므로 군별 패치를 저장해 순서대로 적용한다. plan·log·terms 는 기록 커밋.
- 롤백: 군별 `git revert`. rules-4 는 rules-1 에 의존한다(dlc:172 가 e 4단계 원칙을 인용) — 4 를 1 보다 먼저, 또는 함께 되돌린다. 공용 wiki 쪽 변경은 그 repo 에서 따로 되돌린다. push 뒤에는 다른 머신이 자동 pull 하므로 revert 도 push 해야 닿는다.

# Blockers
