---
title: global-feedback-file — 사용자 지적(개발·응답 방식)을 모든 repo 세션에 자동 적용하는 전역 피드백 파일
status: done
started: 2026-11-02
updated: 2026-11-02
---

# Goal

사용자가 Claude Code 에 한 지적 중 repo 와 무관한 것(개발 방식·응답 방식)을 `~/.claude` 의 전역 피드백 파일에 모아, `~/.claude/CLAUDE.md` 의 import 로 모든 repo 세션에 자동 주입되게 한다.

- Why: §12 feedback memory 는 `~/.claude/projects/<repo>/memory` 라 그 repo 세션에서만 읽힌다. `~/.claude` 메모리의 지적 4개가 다른 repo 세션에 적용되지 않는다. 모든 repo 세션에 자동 주입되는 곳은 `~/.claude/CLAUDE.md` 와 그 import 뿐이다.
- Constraints: 위치는 claude-config(`~/.claude`)이고 CLAUDE.md 의 `@` import 로 불러온다(사용자 결정, 2026-11-02). 공개 repo 라 추적 파일의 지적 문장은 회사·내부 정보 없이 일반 표현으로 쓴다(§11). 운영 자산 변경이라 plan 승인 후 구현한다(§1·§3). 운영 문서라 파일 본문은 영어로 쓴다(§0).
- Out of scope: repo 고유 메모리(어느 repo 의 커밋 작성자·운영 서버 주의, 다른 repo 의 fixup·재게시 무확인 예외, 일지 기록 방식)의 이전은 하지 않는다(사용자 선택 2026-11-02). 승격 시점을 알려 주는 훅·자동화는 만들지 않는다(필요해지면 별도 작업).
- Open questions: 없음 — 저장 방식과 이전 대상은 2026-11-02 사용자 선택으로 정해졌다.
- Size: medium
- Split: none — CLAUDE.md 규칙(§12·§13)·import·FEEDBACK 파일·dlc 참조가 같은 규칙의 앞뒤라 일부만 merge 하면 "지적은 전역 파일에" 와 "지적은 MEMORY.md 에" 가 동시에 남아 규약이 모순된다.

# Tasks

- [x] plan 승인 (2026-11-02) — "승인"
- [x] `FEEDBACK.md` 신설(추적) — 이전할 지적 4개를 "명령형 규칙 — 짧은 이유" 한 줄씩(+ 교훈 링크가 있으면) (2026-11-02)
- [x] `.gitignore` whitelist 에 `!/FEEDBACK.md` 추가(`FEEDBACK.local.md` 는 기본 `/*` 로 무시됨을 확인) (2026-11-02)
- [x] `CLAUDE.md` 끝에 `@FEEDBACK.md` · `@FEEDBACK.local.md` import 추가 (2026-11-02)
- [x] `CLAUDE.md` §12 개정 — 지적을 받으면 전역/repo 판정 후 저장 제안(승인 또는 "기억해" 류 명시 지시 후 저장). 전역은 `FEEDBACK.local.md`(임시칸)→`FEEDBACK.md`(승격: 일반 표현으로 다시 쓰기·기존 규칙과 중복 확인), repo 고유는 repo 메모리. 세션 3경우(`~/.claude` main / `~/.claude` worktree → main 복귀 후 / 다른 repo 세션 → 직접 쓰고, 거부되면 Report·`# Deferred` 에 남겨 main 에서) (2026-11-02)
- [x] `CLAUDE.md` §13 개정 — 전역 교훈의 자동 상기를 MEMORY.md 대신 전역 피드백 파일로 (2026-11-02)
- [x] `CLAUDE.md` §0 언어 목록·§3-1 전역 상태 예외 목록에 `FEEDBACK.local.md` 반영 (2026-11-02)
- [x] `skills/dlc/SKILL.md` 의 §12 저장 판정(16 Report)·Explore 참조 문장을 새 규칙에 맞춤 (2026-11-02)
- [x] `skills/c/SKILL.md` PR intake 의 §12 판정 문장을 새 규칙에 맞춤 (2026-11-02)
- [x] `skills/improve/SKILL.md`(점검 대상 목록)·`skills/improve/improve.sh`(`FEEDBACK.local.md` 줄 수 보고 — 승격 대기 표시) (2026-11-02)
- [x] `README.md` 12·13 항목, `@RTK.md` 설명 단락, `/c` 설명(feedback memory 판정)·plugin 설명의 §12 언급 반영 (2026-11-02)
- [x] code-reviewer (2026-11-02) — REQUEST_CHANGES → Major 1·Minor 4 수정, 승인·안전 규칙 완화 없음
- [x] simplify check (2026-11-02) — 줄일 곳 없음
- [x] 최종 검증 — `bash scripts/verify.sh changed` (2026-11-02) — ALL PASS(skip: PowerShell·zsh 미설치, wiki·wt 테스트 일부 케이스 — 변경 파일과 무관)
- [x] 문구 diff 사용자 확인 후 커밋 (2026-11-02) — "커밋"
- [x] `/e merge` (2026-11-02) — PR #256
- [ ] [post-merge] main 세션에서 `projects/-root--claude/memory/` 의 이전한 4개 파일을 `projects/-root--claude/memory-archive/2026-11-02/` 로 옮기고 `MEMORY.md` 4줄 삭제(merge~이 단계 사이에는 `~/.claude` 세션에 같은 규칙이 두 번 주입되지만 무해)
- [ ] [post-merge] 다른 repo 의 새 세션에서 `FEEDBACK.md` 규칙이 context 에 들어왔는지 관찰
- [ ] [post-merge] main 세션에서 `~/.claude/wiki/docs/dlc-details.md` 의 feedback memory 판정 문장 맞춤(worktree 에 사본 없음)

# Acceptance

1. 전역 피드백 파일이 모든 세션에 import 된다 — `CLAUDE.md` 의 `@FEEDBACK.md`·`@FEEDBACK.local.md` 줄이 코드 스팬 밖에 있고 상대경로가 `~/.claude` 기준으로 풀림(공식 문서) — 두 줄이 있고 백틱 밖.
2. `FEEDBACK.local.md` 가 없어도 세션이 정상 로드된다 — `RTK.md` 가 없는 이 머신에서 `@RTK.md` 가 든 CLAUDE.md 로 세션이 정상 시작된 관찰 — 이 세션에서 관찰됨.
3. 추적 범위가 의도대로다 — `git check-ignore -v FEEDBACK.md FEEDBACK.local.md` — `FEEDBACK.md` 는 무시되지 않고 `FEEDBACK.local.md` 는 무시됨.
4. `FEEDBACK.md` 에 이전 지적 4개가 공개 가능한 일반 표현으로 있다 — 내용 확인 + `pre-commit-check` 통과 — 규칙 4개, 회사·내부 식별자 없음, 파일 40줄 이하.
5. 규칙 문구가 서로 모순 없이 "전역 지적 → 전역 파일, repo 고유 → repo 메모리" 를 말한다 — `rg -n -i 'MEMORY\.md|feedback memory|§12' CLAUDE.md skills agents README.md` 로 남은 언급 전수 확인 + code-reviewer — 낡은 "전역 지적도 MEMORY.md" 서술 0.
6. README 동기화 — README 12·13 항목, import 단락, `/c`·plugin 설명이 새 규칙과 맞음 — diff 확인.
7. 회귀 없음 — `bash scripts/verify.sh changed` — `ALL PASS`(skip 줄은 통과로 읽지 않음).
8. `improve.sh` 가 `FEEDBACK.local.md` 의 승격 대기 줄 수를 보고한다 — 임시 파일로 실행 관찰 — 줄 수가 출력되고 파일이 없으면 조용히 통과.

# Decisions

- wiki 조회: `uv` 가 이 환경에 없어 `wiki_search.py` 를 못 돌렸다. 대신 공용 wiki 의 관련 교훈 페이지(`lesson-grep-absence-not-proof`, `lesson-delete-only-what-you-created`)를 이전 대상 지적의 링크로 쓴다 — 따르거나 뒤집는 결정 없음.
- 저장 방식: 임시칸+승격(사용자 선택 2026-11-02). `FEEDBACK.local.md`(gitignored, 머신별)는 어느 repo 세션에서든 즉시 쓰고, `~/.claude` main 세션에서 `/wt` 로 공개 점검을 거쳐 `FEEDBACK.md`(추적, 이력·머신 간 동기화)로 옮긴 뒤 임시칸에서 지운다. 이유: 추적 파일만 두면 다른 repo 세션의 지적이 worktree·커밋 전까지 적용되지 않고, gitignored 만 두면 머신 간 동기화·이력·공개 점검이 없다.
  - 기각: 추적 파일 하나 — 쓰기마다 `~/.claude` worktree·커밋이 필요해 즉시 적용이 안 됨.
  - 기각: gitignored 하나 — Windows·Mac·Linux 마다 내용이 갈라지고 이력이 없음.
  - 기각: 비공개 wiki repo(`~/.claude/wiki/FEEDBACK.md`) — "claude-config 에 둔다" 는 결정과 다르고 wiki 가 clone 되지 않은 머신에서 빠짐.
  - 기각: `autoMemoryDirectory` 를 user scope 로 한 곳에 모으기 — 공식 문서상 전역 계층이 아니라 모든 프로젝트 메모리를 한 디렉터리로 합칠 뿐이라 repo 고유 메모리까지 섞임.
- 이전 대상: `~/.claude` 메모리 지적 4개만(사용자 선택). 나머지는 repo 메모리에 둔다.
- 파일 형식: 한 지적 = "명령형 규칙 — 짧은 이유" 한 줄(+ 있으면 교훈 링크). 크기 예산: `FEEDBACK.md` 40줄 이하 — 넘으면 보편·중대 규칙은 CLAUDE.md 본문으로 승격하고 나머지는 합친다. 이유: import 는 모든 repo 의 매 세션에 전체가 주입되고, 파일당 200줄 경고가 있다.
- 메모리 본문(사례·Why·How): 교훈 페이지가 있는 2개(`lesson-grep-absence-not-proof`, `lesson-delete-only-what-you-created`)는 링크로 잇고, 없는 2개(짧은 확인 요청, main push 묶기)는 `FEEDBACK.md` 줄의 짧은 이유로 핵심만 남긴다. 원본 4개 파일은 삭제하지 않고 `memory-archive/` 로 옮겨 보존(되돌리기 경로).
- `@import` 사실(✅ 공식 문서 https://code.claude.com/docs/en/memory, 2026-11-02): 상대경로는 import 하는 파일 기준, user-scope import 는 승인 창 없음, 최대 4 hop, 코드 스팬·펜스 안은 무시. 상한은 둘로 다르다 — auto-memory `MEMORY.md` 는 앞 200줄/25KB 만 로드(자름), CLAUDE.md·import 는 다 로드하되 파일당 200줄 넘으면 경고.
- 쓰기 경로(세션 3경우): `~/.claude` main 세션은 바로 쓴다. `~/.claude` worktree 세션은 harness 격리가 main 경로 편집을 거부하므로(§3-1) Report·plan log `# Deferred` 에 남기고 main 복귀 후 쓴다. 다른 repo 세션은 직접 쓰고, 거부되면 같은 방식으로 미룬다 — 거부 여부는 이 세션에서 시험할 수 없어(다른 repo 세션이 아님) 거부돼도 안전한 규칙으로 정했다.
- 공개 점검: `FEEDBACK.local.md` 는 회사 repo 세션에서 쓰여 내부 용어를 담을 수 있다. 승격은 그대로 옮기는 것이 아니라 일반 표현으로 다시 쓰는 일이고, 승격 커밋은 §11 공개 점검 대상이다. 승격 전에 `FEEDBACK.md` 에 같은 규칙이 있는지 확인한다(머신 간 중복 방지).
- Codex 는 범위 밖: Codex 가 `@` import 를 풀지 않으면 전역 피드백은 Codex 에 닿지 않는다(⚠️ 추정, 미확인). 필요해지면 별도 작업.
- 대상 파일이 없을 때(✅ 관찰): 이 머신엔 `RTK.md` 가 없는데 이 세션이 정상 시작됐다 — 공식 문서에는 서술 없음.
- 커밋 단위: 1개 — 같은 규칙 변경의 앞뒤라 나누면 중간 커밋에서 규약이 모순된다.
- ⚠️ 승격 시점: 훅 없이 §12 규칙("`~/.claude` main 세션에서 임시칸에 줄이 있으면 승격 제안")과 `/improve` 의 줄 수 보고만 둔다 — 훅을 만들면 범위가 커진다. 쌓이기만 하고 승격되지 않을 위험은 남는다(`FEEDBACK.local.md` 도 import 되므로 그 머신에선 적용됨).

# Blockers

