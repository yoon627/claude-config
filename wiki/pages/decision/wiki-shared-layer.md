---
title: wiki-shared-layer
category: decision
created: 2026-09-26
updated: 2026-09-26
sources:
  - 사용자 결정 2026-09-26 (이 세션 AskUserQuestion)
  - 실측 2026-09-26 — git 2.54 superproject + wiki submodule + linked worktree
  - git help worktree, BUGS 절 (git 2.54.0)
  - plans/2026-09-26-wiki-ingest-audit-lessons (Deferred — 구현은 별도 plan)
---

# wiki-shared-layer

여러 repo 의 wiki 를 **하나의 wiki repo 로 합쳐 각 repo 에 submodule 로 붙이는 안을 기각**하고, 층을 나눈다(2026-09-26 사용자 결정). **구현은 미착수**다 — wiki skill 과 CLAUDE.md §11 을 바꾸는 별도 plan 이 필요하다.

## 결정
- **repo 고유 결정·교훈**(`decision/`, 코드 경로를 감시하는 페이지)은 지금처럼 **각 repo 의 `wiki/`** 에 둔다. 코드와 같은 브랜치에서 갱신해야 하기 때문이다.
- **여러 repo 에 쓸모 있는 사실**(Claude Code·git·GitHub 동작 같은 `entity/`·`concept/`)은 **`~/.claude/wiki` 한 곳**에 모은다. 이 경로는 어느 repo 세션에서나 같아 submodule 이 필요 없다.
- 구현 방향: wiki skill 이 `<repo>/wiki` 와 `~/.claude/wiki` 를 함께 조회한다(별도 plan).
- `~/.claude` 는 **공개 repo**(`yoon627/claude-config`)라 회사 지식은 넣지 않는다. 회사 쪽 공용 계층이 필요하면 회사 저장소에 따로 둔다.

## 당시 wiki (2026-09-26)
| repo | 원격 | 공개 | 페이지 | 규약 차이 |
|---|---|---|---|---|
| `~/.claude` | GitHub | PUBLIC | 57 | 기준 |
| `coin-trading-bot` | GitHub | PUBLIC | 51 | `schema: 1` |
| `knowledge_base` | 회사 Bitbucket | 회사 | 35 | `covers`·`verified_at` + `check_staleness.py` Stop hook(같은 브랜치 갱신 강제) |

## 기각: 단일 wiki repo + submodule
1. **공개 범위가 섞인다.** 회사 지식과 공개 repo 의 지식이 한 저장소에 들어간다. wiki repo 를 private 으로 두면 공개 repo 의 CI 가 submodule 을 받지 못한다.
2. **worktree 방식과 맞지 않는다**(실측, git 2.54): 새 worktree 에서는 `wiki/` 가 비어 있어 매번 `git submodule update --init` 이 필요하고, init 하면 submodule 이 DETACHED HEAD 라 그대로 고치면 브랜치 없는 커밋이 된다. submodule git dir 은 `.git/worktrees/<name>/modules/` 에 worktree 마다 따로 생긴다. `git help worktree` BUGS 절도 "submodule 지원이 불완전하니 superproject 를 여러 곳에 checkout 하지 말라" 고 한다. 이 workflow 는 모든 변경을 worktree 에서 한다([[worktree-per-task]]).
3. **코드와 같은 브랜치에서 갱신할 수 없다**(실측): 상위 repo 는 wiki 변경을 gitlink 한 줄(`M wiki`)로만 본다. `knowledge_base` 의 staleness 게이트와 전역 문서 동기화 규약(`wiki/pages` ↔ `index.md`)이 상위 repo diff 로는 페이지 내용을 볼 수 없다. 갱신마다 wiki repo 커밋·push + 상위 repo 포인터 커밋 두 단계가 들고, 다른 repo 는 `submodule update --remote` 전까지 옛 버전을 본다.
4. 세 wiki 의 규약이 다르고 `[[링크]]` 이름 공간이 겹칠 수 있다.

## 기각: 단일 wiki repo 를 고정 경로(예 `~/wiki`)에 clone
submodule·worktree 문제는 없지만 코드와 같은 브랜치 갱신을 포기하고, 공개 범위 문제는 그대로 남는다. repo 를 가로지르는 사실만 모으는 목적이면 이미 전역 경로인 `~/.claude/wiki` 가 같은 역할을 한다.

## 연계
wiki 의 목적·`plans/` 와의 경계는 [[project-memory]], 따르는 패턴은 [[llm-wiki-pattern]].
