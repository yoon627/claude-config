---
title: repo-audit-followups — 두 감사(2026-06-11·2026-09-25)에서 남은 결함을 주인 있게 추적
status: open
started: 2026-09-25
updated: 2026-09-25
---

# Problem

남은 결함이 plan 하나의 체크리스트에만 있으면, 그 plan 이 머지돼 done 이 될 때 주인을 잃는다. `/e merge` M4 는 `# Next` 를 비우고, done plan 의 `# Deferred` 는 아무도 다시 보지 않는다. 2026-09-25 감사에서 실제로 이렇게 방치된 항목이 2건 나왔다(bootstrap README settings.json 서술, Codex AGENTS.md 원격 삭제 규칙).

# Proposed outcome

각 그룹이 자기 plan 으로 착수·머지된다. 아직 손대지 않은 그룹은 아래 `# Plans` 에 `(미착수)` 로 남아 `/e` 가 알린다. 항목별 상세(파일:줄·수정 방향)는 첫 plan 의 `# Deferred` 에 있다.

# Constraints

- 보안 그룹을 먼저 한다.
- 운영 자산(`CLAUDE.md`·`skills/`·`agents/`·`settings`) 변경은 사용자가 고른 뒤 `/wt` → dlc 로 한다.
- 착수할 때 줄번호와 현재 상태를 다시 확인한다 — 감사 시점 이후 코드가 바뀌었을 수 있다.

# Out of scope

- 두 감사에서 나오지 않은 새 개선 — 별도 요청으로 받는다.

# Open questions

- (열림) Codex 용 `AGENTS.md` 를 CLAUDE.md 에서 생성할지, 심링크로 둘지, 따로 유지할지 — Codex 재정렬 단위를 착수할 때 정한다.

# Plans

- `plans/2026-09-25-repo-audit-remaining/repo-audit-remaining-plan.md` — G1 heal 경로 탈출·G2 pre-push 범위 비밀 스캔. 아래 단위들의 상세 체크리스트 원본은 이 plan 의 `# Deferred`.
- repo-audit-g3-g4-live-bugs (미착수) — G3 statusline(bg slug·ctime·null stdin·subagent 스키마)·G4 codex-quota-refresh(stdin error·code 0·tmp 고아)
- repo-audit-g5-g7-install (미착수) — G5 install-hooks(Trim·`--git-path hooks`·`.bak`, 래퍼가 원격 이름을 넘기도록)·G6 gwl 이중 마커·G7 `.editorconfig` ps1 BOM
- repo-audit-g8-g9-docs-ci (미착수) — G8 README 유출 대응 절·`CLAUDE_REVIEW_CODEX_MODE` 존폐, G9 CI 비밀 스캔 백스톱·statusline 스모크
- codex-side-resync (미착수) — Codex 쪽 2026-08-01 import 스냅샷 재정렬(`~/.codex/AGENTS.md`·`~/.agents/skills`·`~/.codex/agents`·`.codex/config.toml` serena·Codex 훅 부재)
- verify-tracked-only (미착수) — `scripts/verify.sh` `find_repo` 를 `git ls-files` 기반으로(main checkout 상시 FAILED 해소)
- improve-marker (미착수) — `/improve` 권장의 `last-improve` 마커를 쓰는 경로 또는 기간 창
- gitignore-skills-synced (미착수) — `.gitignore` 에 `/skills/synced/`
- claude-md-guard-wording (미착수) — CLAUDE.md §8 "pre-push 훅이 하드 차단" 서술·§3-1 `/e` 8단계 참조(운영 자산 — 사용자 지시 필요)
- automode-env-scope (미착수) — user `autoMode.environment` 의 knowledge_base 전용 서술
- main-branch-protection (미착수) — GitHub ruleset(required check)·SessionStart 자동 pull 의 무검증 ff
- bootstrap-readme-settings (미착수) — `scripts/bootstrap/README.md:63` settings.json tracked 서술
- audit-low-batch (미착수) — low 묶음(codex-review effort, README `--no-verify` 안내, RTK.md `@import`, wiki 모델 목록, memory 끊긴 링크, pyright-lsp, native-overlap 대장, dlc-early-stop Bash 오탐, 권한 규칙 잔여 한계, heal `_force_rmtree` symlink, ps1 CP949 디코딩)
