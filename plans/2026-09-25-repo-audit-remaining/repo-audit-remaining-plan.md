---
title: repo-audit-remaining — repo-audit-fixes(2026-06-11) 미해소 항목 + 2026-09-25 전체 감사 미처리 항목
status: in_progress
started: 2026-09-25
updated: 2026-09-25
---

# Goal

`plans/2026-06-11-repo-audit-fixes/repo-audit-fixes-plan.md` 에서 미해소로 남은 항목을 보안 그룹(G1·G2)부터 고친다. 2026-09-25 전체 감사에서 이번에 처리하지 않은 항목은 `# Deferred` 에 보존한다. 그룹마다 별도 작업(`/wt`)으로 진행해도 된다.

# Progress

- 2026-09-25: repo-audit-fixes 를 닫으면서 생성(사용자 선택 "닫고 미해소만 새 plan"). 아래 체크리스트의 줄번호는 2026-09-25 main(`e79b97f`) 기준으로 재확인했다. 같은 날 이 plan 밖에서 한 일: 권한 규칙 축소(`settings.json` ask 10→72, `settings.local.json` 두 파일의 파괴적 allow 제거. 백업 `~/.claude/backups/permissions-20260925/`), 원격 브랜치 3개 삭제(commit-split 은 로컬 태그 `archive/commit-split` 51d55d9 로 보존).

# Next

`/wt repo-audit-g1-heal` 로 G1 착수(dlc — 보안이라 code-reviewer + codex 병행). 체크리스트(파일:라인 — 문제 — 수정 방향, 원문 근거는 repo-audit-fixes plan 같은 항목):

## G1 — skills/wt/heal_submodules.py 보안·데이터 손실 [HIGH]
- [ ] **path traversal** (`:115` `git rev-parse --git-path modules/{name}` → `:124` `_force_rmtree`): name 의 `../` 로 repo 밖 디렉토리 삭제 가능. → resolve 후 modules 하위인지 `is_relative_to` 검증, `..`·경로 구분자 있는 name 은 reset 거부.
- [ ] **공백 name 파싱** (`:75` `line.partition(" ")`): `git config -z` 로 `\0` split.
- [ ] **fail-open 게이트** (`:71-72` `if not out: return []`): `.gitmodules` 에 `[submodule` 이 있는데 entries 가 비면 heal 중단.
- [ ] **회귀 테스트**: `test_heal_submodules.py` 에 `../` name·공백 path 를 실제 파서로 거부하는 케이스 없음.
- 후속(선택): `.git` 파일 `gitdir:` prefix 검증, update 실패 시 corrupt 시그니처 확인 후에만 reset, `rm -rf` 로그 OS 중립화.

## G2 — scripts/pre-commit-check.{sh,ps1} pre-push 가드 [HIGH]
- [ ] **pre-push 가 push 대상이 아닌 HEAD 를 검사** (`sh:95`, `ps1:85` `git show HEAD:settings.json`): `sh:20` 에 stdin read 루프는 있으나 settings 스캔은 HEAD 기준. → 각 `<local sha>` 로 검사, delete push(zero sha) skip.
- [ ] **bypass 메시지** (`ps1:100` `git $Mode --no-verify`): Mode → 실제 명령(commit/push) 매핑.
- [ ] **PS5.1 `2>$null` + EAP=Stop** (`ps1:83` `git ls-tree … 2>$null`): redirect 제거 또는 try/catch.
- [ ] (저우선) 매치 토큰 앞 30자 출력 (`sh:63`, `ps1:53`) → 패턴 이름만.

## G3 — statusline.js / subagent-statusline.js (라이브 — 보수적으로)
- [ ] bg slug (`statusline.js:161` `/[:\\\/]/g`): `.` 도 `-` 로 치환되는 실제 디렉토리명과 불일치 → `/[^A-Za-z0-9-]/g`. macOS 에서 bg 표시 경로 자체가 틀렸다는 감사 지적(critic-statusline-bg-dead-macos)도 함께 확인.
- [ ] ctime → birthtime (`:172-177`).
- [ ] null stdin (`:28`, `subagent-statusline.js:8`): `JSON.parse(...) || {}`.
- [ ] subagent 스키마 드리프트 (`subagent-statusline.js:16-19` `current_usage`) — 양 스키마 fallback, 가능하면 라이브 stdin 캡처로 확정.
- [ ] (선택) git spawn 3회 → 1회.

## G4 — codex-quota-refresh.js
- [ ] `proc.stdin.on("error")` 핸들러 없음 → EPIPE uncaught.
- [ ] `:80` `if (code === 0) return;` — 응답 없이 종료 시 즉시 settle 하지 않음.
- [ ] `:104-106` rename 실패 시 `.tmp.<pid>` 잔존.

## G5 — scripts/install-hooks.{sh,ps1}
- [ ] `ps1:3` `(& git rev-parse --show-toplevel).Trim()` — 비-git 디렉토리에서 null.Trim 예외.
- [ ] `sh:13` `hook_dir="$repo_root/.git/hooks"` — linked worktree·`core.hooksPath` 미고려 → `git rev-parse --git-path hooks`.
- [ ] `.bak` 단일 슬롯 덮어쓰기 (`ps1:29`, `sh:32`).

## G6 — gwl 중첩 worktree 이중 마커
- [ ] `scripts/gwl.ps1:16`, `scripts/prompt-gwl.py:29`: 가장 긴 매칭 경로 하나만 `→`.

## G7 — .editorconfig
- [ ] `[*.ps1]` 에 `charset = utf-8-bom` 없음(현재 `end_of_line = crlf` 만) — BOM 파일(gwl.ps1 등)이 저장 시 BOM 을 잃을 수 있다.

## G8 — 문서 drift (남은 것)
- [ ] README 유출 대응 절(`README.md:568-581`): `git push --force-with-lease origin main` 이 자체 pre-push 에 막힐 수 있고, "`permissions.deny` 는 …" 서술이 현행(전역 deny 없음, CLAUDE.md §8)과 다르다.
- [ ] code-reviewer·plan-reviewer 의 `CLAUDE_REVIEW_CODEX_MODE=external` 비대칭 — 2026-09-25 감사(refs-06)에서 이 변수를 읽는 코드가 없다고 확인됨. 대칭 문단 추가보다 개념 자체를 유지할지 먼저 판단.

## G9 — CI
- [ ] secret-guard 서버측 백스톱: `.github/workflows/lint.yml` 에 `pre-commit-check` 실행 없음.
- [ ] (선택) statusline 스모크(`{}`·`null` stdin → exit 0).

## 저우선
- notify.ps1 balloon fallback — 원래 지적한 `Start-Sleep`·`Dispose` 문자열이 현재 파일에 없다. 코드가 바뀌었는지 먼저 재확인.
- statusline fmtQuota 중복, cache/lock 상수 양 파일 중복, readdir 선형 비용.

# Decisions

- **이관 범위**: repo-audit-fixes 의 미체크 항목 전부 + 2026-09-25 감사에서 사용자가 이번에 고르지 않은 항목(`# Deferred`). 해소 확인한 항목(G8 README:38·wt 절·agents 절대경로·codex-review.md:3, G9 python)은 옛 plan 에 체크하고 옮기지 않았다.
- **intent.md 를 만들지 않음**: §10 생성 트리거는 사용자 지시·분할·선행 plan 의 Out of scope/Deferred/별도 작업에서 시작 세 가지인데, 이 plan 은 선행 plan 본 체크리스트의 잔여분이라 어느 것에도 해당하지 않는다. 선행 plan 은 done 으로 닫았고 Goal 에 경로로 연결한다.
- **그룹 순서**: G1 → G2(보안) → G3·G4(라이브 버그) → G5·G6·G7 → G8·G9. 옛 plan 의 순서를 유지한다.

# Key Files

- `skills/wt/heal_submodules.py`, `skills/wt/test_heal_submodules.py` — G1
- `scripts/pre-commit-check.sh`, `scripts/pre-commit-check.ps1` — G2
- `statusline.js`, `subagent-statusline.js`, `codex-quota-refresh.js` — G3·G4
- `scripts/install-hooks.{sh,ps1}`, `scripts/gwl.ps1`, `scripts/prompt-gwl.py`, `.editorconfig` — G5~G7
- `README.md`, `agents/{code-reviewer,plan-reviewer}.md`, `.github/workflows/lint.yml` — G8·G9
- `plans/2026-06-11-repo-audit-fixes/repo-audit-fixes-plan.md` — 원 감사 근거(done)

# Blockers

없음.

# Deferred

2026-09-25 전체 감사(workflow `wf_3746ca79-3e4`, 결과는 세션 스크래치라 여기 요약만 남긴다)에서 사용자가 이번에 고르지 않은 항목. 착수할 때 현재 상태를 다시 확인한다.
- (high) Codex 쪽이 2026-08-01 Codex 앱 import 스냅샷에 멈춤 — `~/.codex/AGENTS.md`(원격 브랜치 무확인 삭제·`.Codex/plans/`), `~/.agents/skills/*` 사본(41커밋 미반영, jira-worklog 는 Windows 경로라 Mac 에서 실행 불가·bootstrap 3b exit 1), `~/.codex/agents/*.toml`, `~/.claude/.codex/config.toml`(제거 결정한 serena MCP 를 고정 안 된 git+https 로 기동). Codex `hooks.json` 에 dlc-early-stop·worktree 게이트 없음.
- (해소 2026-09-25) `~/.claude/AGENTS.md` 가 main checkout 의 Claude 세션에 주입됨 — user `settings.json` 에 `claudeMdExcludes` 로 그 경로만 제외(headless 전후 확인). README·wiki `claude-code-agents-md-loading` 에 기록. AGENTS.md 파일 자체(Codex 용)는 위 Codex 쪽 항목에서 다룬다.
- (medium) `scripts/verify.sh:37` `find_repo` 가 ignored 디렉토리(shell-snapshots·plugins/marketplaces·backups)까지 스캔 → main checkout 에서 항상 `FAILED: 1`, python 축은 plugin pytest 파일을 0건 실행으로 ok. `git ls-files` 기반으로.
- (medium) `/improve` 권장의 `last-improve` 마커를 쓰는 코드 없음(`scripts/session-brief.js:124`) — "마커 이후 N세션"이 07-03 이후 전체 누적.
- (medium) `skills/synced/`(claude.ai 동기화 skill, 라이선스 파일 포함)가 `.gitignore` 에 없음 — PUBLIC repo, `/e` WIP `git add -A` 로 커밋될 수 있다.
- (medium) CLAUDE.md §8 "다른 repo main 푸시는 pre-push 훅이 하드 차단" 은 사실이 아님(global hooksPath 없음). §3-1 이 가리키는 `/e` 8단계에 memory 절차 없음(low).
- (medium) user 스코프 `autoMode.environment` 가 knowledge_base 전용 서술("assume private")인데 공개 repo 인 이 repo 세션에도 적용.
- (medium) GitHub main 에 branch protection·ruleset 없음 + SessionStart 자동 pull 이 CI 결과 없이 ff.
- (medium) `scripts/bootstrap/README.md:63` 이 settings.json 을 tracked 로 서술(done plan remove-codegraph-mcp 의 Deferred 에서 주인 없이 남음).
- (low) docs/codex-review.md Codex effort 서술(xhigh) vs config(low), README 트러블슈팅의 `--no-verify` 안내, RTK.md 가 gitignored 인데 CLAUDE.md 가 `@import`, wiki `anthropic-claude-models` 모델 목록 stale, memory `[[codegraph-projectpath-explicit]]` 끊긴 링크, pyright-lsp 바이너리 없음, native-overlap 대장 50일 경과, dlc-early-stop 이 Bash 로 한 plan 편집을 못 봐 오탐.
- (low) 권한 규칙 잔여: `bash <script>` 로 실행한 명령은 ask 규칙 패턴이 보지 못한다. main 브랜치에서 `git push -u origin HEAD` 처럼 브랜치 이름이 없는 push 는 패턴으로 잡을 수 없다.
