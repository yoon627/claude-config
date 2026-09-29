---
title: wiki-shared-layer
category: decision
created: 2026-09-26
updated: 2026-09-26
sources:
  - 사용자 결정 2026-09-26 (AskUserQuestion 3건 — 구조, 공용 적립 흐름, 기밀 기준)
  - 실측 2026-09-26 — git 2.54 superproject + wiki submodule + linked worktree, `--git-common-dir` 판정 5맥락
  - git help worktree, BUGS 절 (git 2.54.0)
  - plans/2026-09-26-wiki-shared-layer (구현 — CLAUDE.md §11·§13, skills/wiki, skills/dlc, docs/dlc-details)
---

# wiki-shared-layer

여러 repo 의 wiki 를 **하나의 wiki repo 로 합쳐 각 repo 에 submodule 로 붙이는 안을 기각**하고, 두 계층으로 나눴다(2026-09-26 사용자 결정, 같은 날 구현).

## 결정
- **repo wiki** `<ROOT>/wiki/` — 그 repo 의 결정·교훈(코드 경로를 감시하는 페이지 포함). 코드와 같은 브랜치에서 갱신해야 하기 때문이다.
- **공용 wiki** `~/.claude/wiki/` — 여러 repo 에 쓸모 있는 **공개 가능한** 사실(도구·플랫폼·라이브러리 동작)과 전역 자산(dlc·hook·skill)의 결정·교훈. 이 경로는 어느 repo 세션에서나 같아 submodule 이 필요 없다. `~/.claude` 에서는 두 계층이 같다.
- **조회**: 모든 repo 세션이 작업 시작에 두 `index.md` 를 본다(작업 키워드로 먼저 거른다).
- **적립**: 대상 계층을 먼저 정한다(애매하면 repo wiki). 다른 repo 세션에서 공용 대상이면 쓰지 않고, Report 와 출처 plan `# Deferred` 에 `~/.claude 에서 /wt → /wiki ingest …` 제안을 `<요약 · 공개 근거 · 출처(공개/비공개)>` 형식으로 남긴다 — 적립은 `~/.claude` 세션에서 사용자가 한 번 보고 한다(사용자 결정). 기각: 그 세션에서 `~/.claude` worktree 를 만들어 바로 적립(한 세션이 두 repo 를 건드리는 절차·worktree 격리 가드와 충돌), 조회만 공유(공용 지식이 쌓일 경로가 없다), gitignored inbox(새 장치 — `# Deferred` 로 유실이 막힌다).
- **현재 repo 판정**: `[ "$(git rev-parse --path-format=absolute --git-common-dir)" -ef "$HOME/.claude/.git" ]`(main·worktree 모두 — 중첩 repo·다른 repo·비-git 은 아님, 5맥락 실측. bash·sh·dash 동일, 심볼릭 링크 경로도 같은 파일로 본다). 기각: 문자열 비교(Windows 의 `C:/`·`/c/` 표기 차이에 깨진다), 경로 prefix(중첩 repo 오판), `git -C ~/.claude …`(격리 가드 거부).
- **기밀 게이트**(사용자 결정 "비공개 repo 이름까지 금지"): 공용 wiki 는 공개 repo 라 회사·조직명, 내부 도메인·호스트·IP, 고객·제품 코드명, 비공개 repo 의 이름·경로·내부 도구명을 쓰지 않는다(비공개 repo 는 "회사 repo"). 표면은 적립 작업이 공개하는 모든 것 — 본문·`sources`·index·log·plan·브랜치/worktree 이름·커밋 메시지·PR 제목/본문, 티켓 키 포함(단일 정의는 CLAUDE.md §11). 제안을 만드는 쪽이 공개 근거만 싣고, 적립하는 쪽이 다시 점검하고, 출처가 비공개이거나 적혀 있지 않은 제안은 커밋 전 diff 를 확인받는다. 가장 위험한 단계는 공용 적립의 push — 공개 이력은 revert 로 지워지지 않는다. 이 결정 과정에서 공개 repo 에 사내 IP·도메인 값이 옛 교훈 기록에 남아 있던 것을 발견해 현재 파일에서 지웠다(이력은 유지, 사용자 결정).
- **계층 간 참조**: `[[ ]]` 는 같은 wiki 안에서만 — 넘을 때는 경로 텍스트. 공용 페이지는 비공개 repo 의 페이지를 가리키지 않는다. query 결과 filed 는 현재 repo 의 wiki 에만.
- **교훈·Workflow Findings**: 전역 워크플로우 교훈과 `workflow-failures` 는 공용. `MEMORY.md` 는 git repo 별(같은 repo 의 worktree 는 공유)이라 공용 교훈의 memory 줄은 `~/.claude` 세션에만 주입되고, 다른 repo 에서의 상기는 공용 index 조회가 맡는다. 다른 repo 에서 찾은 전역 교훈의 memory 줄은 공용 적립을 마치고 `~/.claude` main 으로 복귀한 세션에서 적는다(worktree 세션에서는 memory 경로 쓰기가 막힌다).
- **우선순위**: 어느 wiki 에 둘지는 CLAUDE.md §11, 페이지 형식은 대상 wiki 의 `WIKI.md` — 다른 repo 의 WIKI.md 가 "외부 사실" 을 자기 소관으로 적어 둔 것과 겹치는 부분은 §11 이 정한다.

## 당시 wiki (2026-09-26)
| repo | 공개 | 페이지 | 규약 차이 |
|---|---|---|---|
| `~/.claude` | 공개(GitHub) | 57 | 기준 |
| `coin-trading-bot` | 공개(GitHub) | 51 | `schema: 1` |
| 회사 repo | 비공개 | 35 | 페이지가 감시하는 코드 경로와 검증 날짜를 frontmatter 에 두고, Stop hook 이 같은 브랜치 갱신을 강제 |

## 기각: 단일 wiki repo + submodule
1. **공개 범위가 섞인다.** 회사 지식과 공개 repo 의 지식이 한 저장소에 들어간다. wiki repo 를 private 으로 두면 공개 repo 의 CI 가 submodule 을 받지 못한다.
2. **worktree 방식과 맞지 않는다**(실측, git 2.54): 새 worktree 에서는 `wiki/` 가 비어 있어 매번 `git submodule update --init` 이 필요하고, init 하면 submodule 이 DETACHED HEAD 라 그대로 고치면 브랜치 없는 커밋이 된다. submodule git dir 은 `.git/worktrees/<name>/modules/` 에 worktree 마다 따로 생긴다. `git help worktree` BUGS 절도 "submodule 지원이 불완전하니 superproject 를 여러 곳에 checkout 하지 말라" 고 한다. 이 workflow 는 모든 변경을 worktree 에서 한다([[worktree-per-task]]).
3. **코드와 같은 브랜치에서 갱신할 수 없다**(실측): 상위 repo 는 wiki 변경을 gitlink 한 줄(`M wiki`)로만 본다. 회사 repo 의 같은 브랜치 갱신 게이트와 전역 문서 동기화 규약(`wiki/pages` ↔ `index.md`)이 상위 repo diff 로는 페이지 내용을 볼 수 없다. 갱신마다 wiki repo 커밋·push + 상위 repo 포인터 커밋 두 단계가 들고, 다른 repo 는 `submodule update --remote` 전까지 옛 버전을 본다.
4. 세 wiki 의 규약이 다르고 `[[링크]]` 이름 공간이 겹칠 수 있다.

## 기각: 단일 wiki repo 를 고정 경로(예 `~/wiki`)에 clone
submodule·worktree 문제는 없지만 코드와 같은 브랜치 갱신을 포기하고, 공개 범위 문제는 그대로 남는다. repo 를 가로지르는 사실만 모으는 목적이면 이미 전역 경로인 `~/.claude/wiki` 가 같은 역할을 한다.

## 남은 것
- `wiki/**` 를 가드로 기계 스캔하는 방어는 없다 — 금지어 목록 자체가 공개 repo 에 둘 수 없는 값이라 로컬 전용 목록 설계가 먼저다.
- 다른 repo wiki 에 이미 있는 공용성 페이지의 이관은 하지 않았다(회사 repo 에서 옮길 때는 기밀 게이트 필수).
- 다른 repo 세션이 `~/.claude/wiki` 에 쓰는 것을 막는 가드는 없다 — 편집 가드는 세션 repo 기준이라 밖의 경로는 보지 않는다. 지금은 규약(§11)만 막는다.
- 다른 repo 의 `# Deferred` 에 남은 공용 제안을 모으는 경로는 없다 — 사용자가 `~/.claude` 에서 가져와야 한다.
- 이 결정 전에 공개 repo 에 적힌 비공개 repo 이름은 그대로 뒀다(사용자 결정 — 이력은 공개돼 있어 지워도 되돌릴 수 없다). 해당 파일을 고칠 때 "회사 repo" 로 일반화한다.
- `~/.claude` 의 plan 전체(공용 적립이 아닌 작업)에 같은 기밀 기준을 적용할지는 정하지 않았다.

## 연계
wiki 의 목적·`plans/` 와의 경계는 [[project-memory]], 따르는 패턴은 [[llm-wiki-pattern]].
