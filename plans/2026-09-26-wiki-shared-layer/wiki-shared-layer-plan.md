---
title: wiki-shared-layer — ~/.claude/wiki 를 여러 repo 가 함께 쓰는 공용 계층으로(조회는 두 곳, 공용 적립은 ~/.claude 세션, 공개 repo 기밀 게이트)
status: in_progress
started: 2026-09-26
updated: 2026-09-26
---

# Goal

`wiki` skill·CLAUDE.md §11·dlc 가 두 계층을 다루게 한다. repo 고유 결정·교훈은 그 repo 의 `wiki/`, 여러 repo 에 쓸모 있는 **공개 가능한** 사실(도구·플랫폼·라이브러리 동작, 전역 워크플로우의 결정·교훈)은 `~/.claude/wiki`. 어느 repo 세션에서든 두 index 를 함께 조회하고, 다른 repo 세션에서 발견한 공용 지식은 제안만 한다(적립은 `~/.claude` 세션에서 `/wt` 경유).

# Intent

- Problem: 지금 규약(§11·wiki skill·dlc)은 "현재 repo 의 `wiki/` 하나"를 전제한다. 그래서 다른 repo 세션은 `~/.claude/wiki` 에 쌓인 도구·워크플로우 사실을 조회하지 않고(같은 조사를 반복), 전역 자산(dlc·hook)의 교훈을 어디에 둘지 규칙이 없다. 2026-09-26 사용자가 submodule 통합을 기각하고 이 두 계층 구조를 골랐다(`wiki/pages/decision/wiki-shared-layer.md`).
- 사용자 결정(2026-09-26): 1) 다른 repo 세션의 공용 지식은 "제안만, 적립은 `~/.claude` 세션"(대안 "그 세션에서 바로 적립"·"조회만 공유" 기각) 2) 공용 wiki 기밀 기준은 "비공개 repo 이름까지 금지"(대안 "이름은 허용, 내부 식별자만 금지" 기각) — 이미 공개된 예전 언급은 그대로 두되, 오늘 쓴 `wiki-shared-layer` 의 회사 repo 표 줄은 고친다 3) 공개 repo 에 있던 사내 IP·도메인 값은 현재 파일에서 지웠다(별도 커밋 `1f09a54`, push 완료, 이력 재작성은 안 함).
- 규모: medium(운영 자산 문서 — CLAUDE.md §11·§13, `skills/wiki/SKILL.md`, `skills/dlc/SKILL.md` wiki 연계·Workflow Findings, `docs/dlc-details.md` §C·§D, `wiki/WIKI.md`, README, wiki 페이지 2개·index·log. 코드 변경 없음).
- 분할: 없음 — 조회·적립·교훈·Workflow Findings 규칙이 모두 같은 두 계층 정의에 기대므로, 일부만 머지되면 §11·wiki skill·dlc 가 서로 다른 계층 모델을 말한다(plan-reviewer 가 처음 범위의 이 누락을 지적).
- Constraints: 운영 자산 변경은 사용자 결정 범위만. `~/.claude` 는 **공개 repo**. 다른 repo 의 `wiki/WIKI.md` 는 그 repo 에서 고치지 않는다 — 우선순위는 "어느 wiki 에 둘지는 §11, 형식은 대상 wiki 의 WIKI.md". 규칙 문구는 Codex 도 그대로 받는다(`~/.codex/AGENTS.md` → CLAUDE.md, `~/.agents/skills/wiki` → `skills/wiki`) — Claude 전용 기능에 기대지 않는다.
- Out of scope: 다른 repo wiki 의 공용성 페이지 이관, 다른 repo 의 WIKI.md·CLAUDE.md 수정, `check_links.py` 변경(인자로 wiki 경로를 받고 인자 없으면 cwd 의 wiki), `wiki/**` 기계 스캔(Deferred), 회사용 공용 계층.

# Acceptance

1. CLAUDE.md §11: 두 계층(repo `wiki/` = 그 repo 의 결정·교훈, `~/.claude/wiki` = 여러 repo 에 쓸모 있는 공개 가능한 사실·전역 자산의 결정·교훈), 현재 repo 판정 명령 한 줄(`git rev-parse --path-format=absolute --git-common-dir` 이 `$HOME/.claude/.git` — worktree 포함, `~/.claude` worktree 에서는 공용 wiki = 그 worktree 의 `wiki/`), 작업 시작 조회는 두 index, ingest 판정은 대상 계층까지(repo / 공용 / 비대상 + 사유, wiki 없는 repo·비-git 은 비대상 + 사유), 다른 repo 세션의 공용 대상은 적립하지 않고 Report 와 출처 plan `# Deferred` 에 `~/.claude 에서 /wt → /wiki ingest …` 제안, 공용 wiki 금지 목록, 전역 자산의 `[[…]]` 는 공용 wiki 페이지, 우선순위. CLAUDE.md §13: 교훈 상세는 대상 계층의 wiki(전역 워크플로우 교훈은 공용), 공용 교훈의 memory 줄은 `~/.claude` 프로젝트 memory 에만 주입된다는 한계.
2. `skills/wiki/SKILL.md`: frontmatter `description`, 두 계층·판정 명령·규약 파일, query(두 index, 어느 wiki 인지 인용, filed 는 현재 repo wiki 에만 — 공용 페이지 근거면 제안으로, 계층을 넘는 참조는 `[[ ]]` 가 아니라 경로 텍스트), ingest(대상 계층 먼저, 다른 repo 에서 공용 대상이면 쓰지 않고 제안 — 공개 검증 가능한 근거만, 공용 wiki 의 **모든** write(sources·index·log·커밋 메시지 포함) 전 금지 목록 점검, 출처가 비공개 repo 인 제안을 적립할 때는 커밋 전에 diff 를 보이고 AskUserQuestion, `~/.claude` 에서의 write 는 `/wt` 경유), lint(현재 repo 의 wiki), 경계("wiki 없으면 no-op" 정정).
3. `skills/dlc/SKILL.md` wiki 연계(두 index 조회, Report 판정은 대상 계층까지, 공용 대상 제안 형식)·Workflow Findings(기록처는 공용 wiki 의 `decision/workflow-failures.md` — 다른 repo 세션이면 제안), `docs/dlc-details.md` §C·§D 같은 내용. `wiki/WIKI.md`: 공용 계층을 겸함·`decision/` 정의 확장·공개 제약. README: wiki skill 절, CLAUDE.md 절 목록 §11·§13 문구.
4. wiki: `wiki-shared-layer` 를 구현됨으로(규칙·기각 흐름) + 회사 repo 표 줄을 금지 목록에 맞춰 일반화, `project-memory` 의 "여러 repo 사이" 갱신 + 같은 절의 `plans/` gitignored 낡은 서술 정정, `wiki/index.md`·`wiki/log.md`.
5. 판정 명령을 네 맥락(`~/.claude` main, 이 worktree, 다른 repo, 비-git 디렉토리)에서 실행해 출력 대조(scratch 스크립트).
6. 검증: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음), `bash skills/improve/improve.sh --ci`(운영 자산 정합 — verify.sh 에 없다) error 0, `uv run --no-project python skills/wiki/check_links.py wiki` clean, `node scripts/plan-lint.js plans/2026-09-26-wiki-shared-layer/wiki-shared-layer-plan.md`.
- [ ] [post-merge] 다른 repo(예: coin-trading-bot) 세션에서 작업 시작 조회가 두 index 를 보는지, 공용 대상 지식이 제안으로만 나오는지 관찰.

# Progress

- 2026-09-26: 착수. 사용자 결정(제안만, 적립은 `~/.claude` 세션).
- 2026-09-26: plan-reviewer CONDITIONAL — 강 5(verify.sh 에 improve 없음·dlc/§13/workflow-failures 범위 누락·기밀 점검이 실행 쪽에만·query filed·계층 링크 미정·제안 유실과 `/wt` 누락)·약 다수. 공개 repo 점검 중 사내 IP·도메인 값이 3개 파일에 있던 것을 발견 → 사용자 결정으로 현재 파일에서 제거·push(`1f09a54`, 별도 단위). 기밀 기준 "비공개 repo 이름까지 금지"(사용자). plan 재작성.
- 2026-09-26: 판정 명령 5맥락 실측(`~/.claude` main·이 worktree → `~/.claude`, 다른 repo·`~/.claude` 안 중첩 repo·비-git → other). 편집: CLAUDE.md §11·§13, `skills/wiki/SKILL.md`(전면), `skills/dlc/SKILL.md`·`docs/dlc-details.md` §C·§D, `wiki/WIKI.md`, README(§11·§13 요약·wiki 절), `wiki-shared-layer`(구현됨·회사 repo 표 줄 일반화)·`project-memory`·index·log. check_links clean, plan-lint ok, `improve.sh --ci` error=0. 이번 diff 의 추가 줄에 비공개 repo 이름·회사 식별자 없음(스캔).
- 2026-09-26: code-reviewer REQUEST CHANGES(주 2·경 다수) 반영 — 공개 점검 표면을 적립 작업이 공개하는 모든 것으로 넓혀 §11 에 단일 정의, 제안 형식 `<요약 · 공개 근거 · 출처(공개/비공개)>` 로 통일(출처 불명 = 비공개), 판정을 `-ef` 로 바꿔 bash·sh·dash·심볼릭 링크 실측, 계층 명시(§3-6·§8 의 `workflow-failures`, dlc 반복 제안·self-diagnosis 링크), `ingest-operation` 에 계층 판정 단계.
- 2026-09-26: code-reviewer 2차 APPROVE, 경 2·open 1 반영(memory 줄은 main 복귀 후, 출처 칸은 `공개`/`비공개` 만, lesson 경로는 대상 wiki 형식). `-ef` 판정 5맥락 × bash·/bin/sh·dash + 심볼릭 링크 실측 일치.

# Next

머지 — main 이 base 보다 앞서 있어 로컬 ff 불가, `/e merge`(push·PR 은 사용자 확인 후). 머지 뒤 [post-merge] 관찰.

# Decisions

- 공용 계층 위치는 `~/.claude/wiki` 그대로(새 repo·submodule 없음 — `wiki-shared-layer` 결정). `~/.claude` 세션에서는 repo wiki 와 공용 wiki 가 같다.
- 현재 repo 판정: `git rev-parse --path-format=absolute --git-common-dir` 결과가 `$HOME/.claude/.git` 과 같은지(main·worktree 모두). 비교는 문자열이 아니라 `[ … -ef … ]` 로 변경 (이유: code-review — Windows Git Bash 의 `C:/`·`/c/` 표기 차이와 심볼릭 링크 경로에서 문자열 비교가 `~/.claude` 를 다른 repo 로 오판한다. bash·/bin/sh·dash 와 심볼릭 링크 경로로 실측. Windows 실측은 없음 ⚠️). 기각: `--show-toplevel` 비교 + worktree 별도 처리(두 단계라 worktree 여부를 먼저 알아야 한다), 경로 prefix(중첩 repo 오판 — `dlc-doc-drift.js` 선례), `git -C ~/.claude …`(worktree 격리 가드가 거부). 오판해도 "다른 repo → 제안만" 쪽으로 떨어진다(안전한 쪽).
- 적립 대상: repo 고유 → repo wiki. 여러 repo 에 쓸모 있는 공개 가능한 사실·전역 자산(dlc·hook·skill)의 결정·교훈 → 공용. 애매하면 repo wiki(비공개 repo 에서는 특히 — 공개 repo 로 새는 쪽이 비싸다). repo wiki 가 없거나 비-git 이면 비대상 + 사유(필요하면 repo wiki 신설 제안).
- 다른 repo 세션의 공용 대상: 쓰지 않는다. Report 와 출처 plan `# Deferred`(없으면 Report 만)에 `~/.claude 에서 /wt → /wiki ingest <요약 · 공개 근거 · 출처(공개/비공개)>`(형식 통일 — code-review: 문서마다 형식이 달라 적립 쪽이 출처를 알 수 없었다) — 근거는 공개 검증 가능한 것(공식 문서 URL·공개 이슈·비공개 코드 없이 되는 재현)만, 없으면 공용 대상이 아니다. 기각: 그 세션에서 바로 적립(사용자), 조회만 공유(사용자), gitignored inbox 파일(새 장치 — 기존 `# Deferred` 로 유실이 막힌다), 채팅에만 남기기(§3-4 유실 금지 위반).
- 기밀 게이트(가장 위험한 단계 = 공용 적립 커밋의 push. 공개 이력은 revert 로 지워지지 않고 `github-sensitive-data-removal` 절차만 남는다): 금지 목록 — 회사·조직명, 내부 도메인·호스트·IP, 고객·제품 코드명, 비공개 repo 의 이름·경로·내부 도구명(비공개 repo 는 "회사 repo" 로만). 제안을 만드는 쪽에서 먼저 정제하고, 적립하는 쪽이 다시 점검한다. 점검 표면은 적립 작업이 공개하는 모든 것 — 페이지·`sources`·index·log·plan·브랜치/worktree 이름·커밋 메시지·PR 제목/본문, 티켓 키 포함으로 확장 (이유: code-review — 처음 목록은 wiki 파일만 봐서 `/wt` slug·plan·PR 로 새는 경로가 남았다). 금지 목록·표면은 §11 에만 두고 skill·WIKI.md·README 는 §11 을 가리킨다. 출처가 비공개이거나 **적혀 있지 않은** 제안을 적립할 때는 커밋 전 diff 를 보이고 AskUserQuestion(없는 환경이면 채팅, §1 외부공개). 기각(지금은): `wiki/**` 를 pre-commit 가드로 스캔 — 금지어 목록 자체가 공개 repo 에 둘 수 없는 값이라 로컬 전용 목록 설계가 필요하다(`# Deferred`).
- query 결과 filed 는 현재 repo 의 wiki 에만. 공용 페이지를 근거로 한 답을 다른 repo 에서 filed 할 가치가 있으면 공용 제안으로 돌린다. 계층을 넘는 참조는 `[[ ]]` 가 아니라 경로 텍스트(`~/.claude/wiki/pages/<cat>/<stem>.md`) — `check_links.py` 는 현재 wiki 의 페이지만 본다. 공용 페이지는 비공개 repo 의 페이지를 가리키지 않는다.
- 교훈(§13): 상세는 대상 계층의 wiki. 전역 워크플로우 교훈은 공용. `MEMORY.md` 는 git repo 별(같은 repo 의 worktree 는 공유 — 이 worktree 세션의 memory 경로가 main checkout 의 `projects/<slug>/memory/` 다)이라 공용 교훈의 memory 줄은 `~/.claude` 세션에만 주입된다. 다른 repo 에서 찾은 전역 교훈의 memory 줄은 공용 적립을 마치고 `~/.claude` main 으로 복귀한 세션에서 적는다(§3-1 — worktree 안에서는 못 쓴다) — 다른 repo 에서의 상기는 작업 시작의 공용 index 조회가 맡는다(한계로 명시). 기각: memory 줄을 여러 프로젝트에 복제 — 동기화 대상이 늘어난다.
- dlc Workflow Findings 의 기록처(`workflow-failures`)는 공용 wiki(dlc 는 전역 자산). 다른 repo 세션이면 plan `# Workflow Findings` 에 적고 공용 기록은 제안.
- 조회 비용: 공용 `index.md` 는 약 16KB 라 매 작업 전체 read 는 비싸다 — 작업 키워드로 먼저 거른 뒤 관련 줄만 본다.
- ⚠️ 동급 규약 상충 — 다른 repo 의 WIKI.md 는 "외부 사실" 을 자기 wiki 소관으로 두고 스스로 단일 소스라고 선언한다(coin `WIKI.md:13`, 회사 repo `WIKI.md:35`) — 전역 §11 과 겹친다 — "어느 wiki 에 둘지는 §11, 형식은 대상 wiki 의 WIKI.md" 로 정했다. 이유: 계층 배치는 repo 를 가로지르는 규칙이라 전역이 정하고, 페이지 형식은 각 wiki 가 이미 다르게 운영한다.
- 커밋 단위: 1개 — `docs(wiki): make ~/.claude/wiki the shared layer every repo reads`.

# Key Files

- `CLAUDE.md` §11·§13
- `skills/wiki/SKILL.md`
- `skills/dlc/SKILL.md` — wiki 연계, Workflow Findings
- `docs/dlc-details.md` §C·§D
- `wiki/WIKI.md`, `README.md`
- `wiki/pages/decision/wiki-shared-layer.md`, `wiki/pages/concept/project-memory.md`, `wiki/pages/concept/ingest-operation.md`, `wiki/index.md`, `wiki/log.md`

# Review Disposition

- [plan] 강1 verify.sh 에 improve `--ci` 없음 — fix(Acceptance 6 에 별도 명령).
- [plan] 강2 dlc SKILL·dlc-details §D·§13·workflow-failures·README §13 누락 — fix(Key Files·Acceptance 1·3).
- [plan] 강3 기밀 점검이 실행 쪽에만·제안의 비공개 경로·기계 방어 없음·공개 표면·기존 표 줄 — fix(양쪽 점검·모든 표면·비공개 출처 diff 확인·금지 목록·표 줄 일반화), 기계 스캔은 defer(금지어 목록 설계 필요).
- [plan] 강4 query filed·계층 간 링크 — fix(Decisions).
- [plan] 강5 제안 유실·`/wt` 누락 — fix(`# Deferred` 병기, `/wt → /wiki ingest`).
- [plan] 약: 판정 명령 한 줄·worktree 의 공용 wiki 경로·비-git 처분·조회 비용·Codex 호환·전역 `[[…]]`·WIKI.md 우선순위(self-flag)·이관 Deferred·Problem·description·`decision/` 정의·기각안·가장 위험한 단계 — fix.
- [self-flag] WIKI.md 우선순위 상충 — accepted-risk(다른 repo 의 WIKI.md 는 고치지 않는다는 제약. §11 이 배치를 정한다고 양쪽 문서에 적었다).
- [code] 주1 점검 표면이 wiki 파일뿐(plan·브랜치/worktree 이름·PR·티켓 키 누락) — fix(§11 단일 정의, skill·WIKI.md·README 는 참조).
- [code] 주2 제안 형식이 문서마다 다르고 출처가 없어 비공개 판정 불가 — fix(`출처(공개/비공개)` 통일, 불명 = 비공개 → diff 확인).
- [code] 경: 문자열 판정의 Windows 표기 차이 — fix(`-ef`). AskUserQuestion 없는 환경 — fix(채팅 폴백). 비-git·wiki 없는 repo 에서 공용 제안까지 막힘 — fix(공용 대상은 여전히 제안). "진행 중인 worktree" 모호 — fix(무관한 작업). worktree 의 raw 가 정리 때 유실 — fix(주의 문구). 계층 미표기(§3-6·§8 `workflow-failures`, dlc 반복 제안·self-diagnosis 상대경로) — fix. `decision/` 정의·`ingest-operation` 절차 — fix. §13 memory 서술 — fix.
- [code] 다른 repo 세션의 공용 wiki 쓰기를 막는 가드 없음(`guard-worktree-edit.js` 는 repo 밖 경로 allow) — defer.
- [code] `~/.claude` plan 전체의 기밀 기준 — defer(사용자 결정 필요).
- [code 2차] APPROVE — 주1·주2 해소 확인(§11 단일 정의, 제안 형식 7곳·`-ef` 4곳 바이트 일치, 식별자 스캔 clean).
- [code 2차] 경1 §13 "공용 적립 때 memory 줄을 함께" 가 §3-1(worktree 안 memory 쓰기 불가)과 부딪침 — fix(적립을 마치고 main 복귀 세션에서, §13·결정 페이지·Decisions).
- [code 2차] 경2 제안 출처 칸의 값이 정해지지 않아 비공개 repo 이름이 적힐 수 있음 — fix(`공개`/`비공개` 만, §11·wiki skill).
- [code 2차] nit WIKI.md·SKILL 이 §11 목록을 요약해 다시 적음 — wontfix(ingest 시작에 WIKI.md 를 먼저 읽으므로 요지가 있어야 하고, 두 곳 모두 §11 을 단일 정의로 명시해 어긋나면 §11 이 이긴다).
- [code 2차] open §13 lesson 경로가 다른 repo WIKI.md 형식과 충돌할 수 있음 — fix(공용은 `decision/lesson-*`, 다른 repo 는 그 WIKI.md 형식 — §13·README).

# Blockers

# Deferred

- (중간) 공용 wiki 기계 방어: `wiki/**` 를 pre-commit·CI 가드로 스캔. 금지어(회사명·내부 도메인 등)는 공개 repo 에 둘 수 없으므로 로컬 전용 목록(gitignored 또는 `~/.config` 류) 설계가 먼저다. `scripts/pre-commit-check.{sh,ps1}`.
- (낮음) 다른 repo wiki 의 공용성 페이지 이관(coin 의 도구·워크플로우 교훈 등). 회사 repo 에서 옮길 때는 기밀 게이트 필수.
- (낮음) `skills/wiki/SKILL.md` 의 `${CLAUDE_SKILL_DIR}` 는 Codex 에서 설정되지 않는다(기존 문제).
- (중간) 다른 repo 세션이 `~/.claude/wiki` 를 편집해도 막는 장치가 없다 — `scripts/guard-worktree-edit.js` 는 세션 repo 밖 경로를 allow 한다. 지금은 §11 규약만 막는다.
- (중간) `~/.claude` 의 plan 전체(공용 적립이 아닌 작업)에도 공개 점검을 적용할지 — 사용자 결정 필요. 지금은 공용 적립 작업의 plan 만 대상.
- (낮음) 다른 repo 의 `# Deferred` 에 남은 공용 제안을 `~/.claude` 로 모으는 경로가 없다 — 사용자가 가져와야 한다.
