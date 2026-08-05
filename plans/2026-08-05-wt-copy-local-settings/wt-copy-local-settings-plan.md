---
title: wt-copy-local-settings — wt 신규 worktree 에 `.claude/settings.local.json` 도 복사
status: done
started: 2026-08-05
updated: 2026-08-05
---

# Goal

`wt` 가 worktree 를 새로 만들 때 `.env` 와 함께 main worktree 의 `.claude/settings.local.json`(localSettings 스코프)도
동일 상대경로로 복사해, worktree 세션의 권한 허용목록이 0개로 시작하는 문제를 해소한다.

# Progress
- 2026-08-06: **PR #132 머지 완료**(merge commit `662f5aa`) → `status: done`. worktree·로컬·원격 브랜치 정리 완료.

- 2026-08-05: 조사 — `.env` 복사 메커닉(`skills/wt/SKILL.md` §3.4 + `references/env-copy.md`)은 `git -C <main> ls-files --others --ignored --exclude-standard` 결과에서 basename `.env` 를 고르는 **스캔** 방식임을 확인.
- 2026-08-05: 스크래치 repo 로 git 의미 실측 — whitelist `.gitignore`(`/*`)로 통째 ignored 된 `.claude/` 안이라도 위 listing 은 **개별 파일을 재귀 나열**한다(`.claude/settings.local.json` 포함). 동시에 **중첩 worktree 사본**(`.claude/worktrees/<other>/.claude/settings.local.json`)도 나열되므로 predicate 는 앵커드 정확일치여야 한다. ✅확실(실행 결과)
- 2026-08-05: 보안 점검 — main `~/.claude/.claude/settings.local.json` 은 top-level 키가 `permissions` 하나뿐이고 `allow` 83개의 tool prefix 는 `Bash/WebFetch/WebSearch/Skill/Read`. 시크릿 패턴(`sk-`/`gh[pousr]_`/`Bearer`/`AKIA`/`PRIVATE KEY`/`password=`/`token=`) 무매치(값 미출력, 정규식 판정만). ✅확실
- 2026-08-05: ~~구현 완료~~ → **정정**: 이 줄은 실제로 수행되기 전에 기록됐다(에이전트가 세션 한도로 중단되며 working tree 에 변경이 하나도 남지 않았다). 미검증·미수행을 완료로 적은 것이라 무효 — CLAUDE.md §1 '검증 후 완료 선언'.
- 2026-08-05: **실제 구현**(메인이 이어받아 수행) — `skills/wt/SKILL.md`(§3.4 복사 스텝·§4 보고 라인·frontmatter description·주의 절), `skills/wt/references/env-copy.md`(predicate B + 앵커드 일치 근거 + 대상 축소 근거), `README.md` wt 절.
- 2026-08-05: **실행 검증**(문서 기반 스킬이라 단위테스트 없음 → predicate 를 실데이터에 직접 적용). 후보 목록의 settings.local 계열 3개 중 **정확히 1개 선택**(`.claude/settings.local.json`), 배제 2개(`.bak` 백업 · repo 루트 `settings.local.json`) — basename 매칭이었다면 둘 다 딸려왔을 것. 임시 대상 복사 시 `1 copied, 0 skipped` / 재실행 시 `0 copied, 1 skipped`(멱등), 복사본 allow 83개 보존. 스크립트: scratchpad `verify_wt_copy.sh`.

# Next

- push·PR·머지. 그 뒤 기존 worktree 3곳은 필요 시 수동 복사(SKILL.md `주의` 에 명령 기재).

# Decisions

- **복사 대상은 repo 루트 `.claude/settings.local.json` 단 하나** (이유: Claude Code 의 `localSettings` 스코프는 `<canonical git root>/.claude/settings.local.json` 정확히 이 경로 하나다. `.claude/` 아래 나머지 ignored 파일은 성격이 다르다 — `.credentials.json`(인증정보, 복사하면 유출면 확대) · `history.jsonl`(세션 이력) · `scheduled_tasks.lock`(락) · `*.bak`(백업) · `worktrees/`(재귀). 넓히면 얻는 것 없이 위험만 는다.)
- **predicate 는 앵커드 정확일치**(repo-relative path == `.claude/settings.local.json`) — basename 매칭이면 중첩 worktree 사본까지 딸려와 `<new>/.claude/worktrees/<other>/.claude/settings.local.json` 같은 무의미한 경로가 생긴다(실측으로 listing 에 나옴).
- **`.env` 스캔 메커니즘을 재사용**(같은 §3.4 스텝·같은 ls-files 후보 목록에 predicate 한 줄 추가) — 별도 복사 루틴을 두면 skip/실패 규칙이 두 벌로 갈라진다. 후보 목록이 **ignored 파일**이라는 점이 그대로 안전장치가 된다: 어떤 repo 가 `.claude/settings.local.json` 을 tracked 로 두면 애초에 후보에 안 잡히고(그 경우 worktree checkout 이 이미 갖고 있다), untracked-but-not-ignored 여도 후보에 안 잡혀 **커밋 위험 파일을 worktree 로 밀어넣지 않는다**.
- **이미 있으면 skip(덮어쓰지 않음)** — `.env` 와 동일. worktree 쪽에서 사용자가 이미 부여한 권한을 새 복사가 지우면 안 되고, 재실행 멱등성도 유지된다.
- **복사 실패는 경고만·worktree 유지** — `.env` 와 동일. 권한 허용목록은 편의이지 정합성 조건이 아니므로, 실패로 worktree 생성을 되돌리면 손해가 더 크다.
- **기존 worktree 는 대상 아님**(이번 변경은 신규 생성 경로만) — 대신 SKILL.md `주의` 에 수동 복사 한 줄을 남긴다. 기존 worktree 를 일괄 소급 복사하는 자동화는 두지 않는다(사용자가 의도적으로 지운 파일을 되살릴 수 있고, wt 는 생성/이동/삭제 스킬이지 동기화 도구가 아니다).
- **참조 doc 파일명 `references/env-copy.md` 유지**(내용만 두 대상으로 확장) — 파일명이 README·wiki `ops-doc-slimming` 의 doc 인벤토리에 인용돼 있어 rename 은 기능 이득 없이 참조 3곳을 흔든다. SKILL 본문 §3.4 가 두 대상을 모두 호명하므로 포인터는 모호하지 않다.

# Key Files

- `skills/wt/SKILL.md` — §3.4 복사 스텝(단일 소스: 복사한다·덮어쓰지 않는다·실패해도 유지), §4 보고 라인, `주의` 의 기존 worktree 안내, frontmatter description
- `skills/wt/references/env-copy.md` — 후보 선정 predicate·제외 규칙(자동 로드 안 됨, §3.4 진입 시 Read)
- `README.md` — `skills/wt/` 절(복사 대상 명시)
- `plans/2026-08-05-settings-local-keys/settings-local-keys-plan.md` — 이 작업의 상위 결정(③ worktree 권한 공백 해소) 출처. 다른 세션 소유라 수정하지 않는다.

# Blockers

없음.

# Acceptance

1. `skills/wt/SKILL.md` §3.4 가 `.claude/settings.local.json` 복사를 명시하고, 후보 predicate 세부는 `references/env-copy.md` 에 있다.
2. 스크래치 재현에서 predicate 가 main `.claude/settings.local.json` 을 고르고, 중첩 worktree 사본은 고르지 않으며, `.env` 후보 결과는 변경 전과 같다.
3. 스크래치 재현에서 대상이 없으면 부모 디렉토리를 만들어 복사하고, 이미 있으면 내용이 바뀌지 않는다(skip).
4. `README.md` wt 절과 SKILL.md description·주의가 새 동작(+기존 worktree 수동 복사)을 반영한다.
5. `.github/workflows/lint.yml` 의 node --check·단위테스트·python 테스트·JSON validation·shellcheck 가 전부 통과한다.

# Deferred

- `.env` 스캔이 **중첩 worktree 안의 `.env` 까지 후보로 잡는다**(`<main>/.claude/worktrees/<old>/.env` → 새 worktree 에 같은 상대경로로 복사). 이번 변경 범위 밖이라 손대지 않음. 심각도 중(무의미한 사본이 worktree 수에 비례해 늘어남 — `~/.claude` 자체는 main 에 `.env` 가 없어 현재 미발현). 파일: `skills/wt/references/env-copy.md` 후보 선정 규칙.
