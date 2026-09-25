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

- (열림) `push-remote-scope` 가 가드의 인자 없는 호출 의미를 바꾸면 `scripts/ci-secret-scan.sh`(인자 없이 부르고 임시 repo 의 추적 ref 를 base 하나로 둔다)도 맞춰야 한다 — `ci-secret-scan.test.sh` 의 "base 이전 토큰은 다시 보지 않는다" 가 그 의존을 잠근다. 그 단위 착수 때 확인(g8-g9 plan 이 연 질문).

- (해소) Codex 용 `AGENTS.md` 는 CLAUDE.md 심링크 — 2026-06-10 사용자 결정(`a3d7bdc`)을 2026-09-25 복원(config-docs-sync).

# Plans

- `plans/2026-09-25-repo-audit-remaining/repo-audit-remaining-plan.md` — G1 heal 경로 탈출·G2 pre-push 범위 비밀 스캔. 아래 단위들의 상세 체크리스트 원본은 이 plan 의 `# Deferred`.
- `plans/2026-09-25-repo-audit-g3-g4-live-bugs/repo-audit-g3-g4-live-bugs-plan.md` — G3 statusline(null 입력·bg 표시 제거·subagent 행 현행 스키마로 재작성)·G4 codex-quota-refresh(종료 경로 통합·응답 없는 종료 즉시 처리·캐시 쓰기 실패 시 잔류·임시 파일)
- `plans/2026-09-25-repo-audit-g5-g7-install/repo-audit-g5-g7-install-plan.md` — G5 install-hooks(git 밖 오류·공용 hooks 디렉토리·`core.hooksPath` 거부·백업 보존)·G6 gwl 이중 마커·G7 `.editorconfig` ps1 BOM
- push-remote-scope (미착수) — pre-push 가드가 push 대상 원격이 가진 커밋만 건너뛰게(G2 accepted-risk, 원래 G5 넷째 항목). 출발점은 g5-g7 plan 의 `# Decisions`·`# Review Disposition`: 래퍼 인자가 설치 시점에 확장되는 함정(sh heredoc `"$@"`·ps1 `@"` 의 `$1`), 추적 ref 를 믿는 조건(pushurl 없음·url 1개·`<name>/` 로 시작하는 다른 원격 없음·기본 refspec), 인자 없음과 빈 값 구분·옛 래퍼 호환 결정·재설치 단계, rsha OID 검증, 실제 `git push` E2E·dogfood·혼합 상태(새 래퍼+옛 가드) 확인, `PWSH` 지정 ps1 증거
- `plans/2026-09-26-repo-audit-g8-g9-docs-ci/repo-audit-g8-g9-docs-ci-plan.md` — G8 README 유출 대응 절·`CLAUDE_REVIEW_CODEX_MODE` 폐기(사용자 결정), G9 CI 비밀 스캔 백스톱(`scripts/ci-secret-scan.sh`; statusline 스모크는 g3-g4 의 `statusline.test.js` 가 CI 에서 이미 돈다)
- `plans/2026-09-25-config-docs-sync/config-docs-sync-plan.md` — CLAUDE.md §8 pre-push·§3-1 문구, 저장소 밖 적용분(autoMode.environment repo 별 분리·GitHub ruleset `main-guard`·Codex 쪽 재정렬)의 README·wiki 문서화
- autopull-verified-ff (미착수) — SessionStart 자동 pull(`scripts/session-start-pull.sh`)이 CI 결과 없이 origin/main 을 ff 해 훅 코드로 바로 실행한다. ruleset `main-guard` 는 관리자 bypass 라 소유자의 lint 미통과 push 는 막지 못한다 — ff 전에 대상 sha 의 check 상태를 보는 방안
- `plans/2026-09-25-repo-small-cleanups/repo-small-cleanups-plan.md` — `.gitignore` `/skills/synced/` · bootstrap README settings.json 서술 · verify.sh 를 git ls-files 기반으로(main checkout 상시 FAILED 해소)
- `plans/2026-09-25-improve-marker/improve-marker-plan.md` — `/improve` 완료 시 `last-improve` 마커 갱신(`dlc-signal.js mark`)
- audit-low-batch (미착수) — low 묶음(codex-review effort, README `--no-verify` 안내, RTK.md `@import`, wiki 모델 목록, memory 끊긴 링크, pyright-lsp, native-overlap 대장, dlc-early-stop Bash 오탐, 권한 규칙 잔여 한계, heal `_force_rmtree` symlink, ps1 CP949 디코딩, `~/.codex/agents/*.toml` 08-01 스냅샷(재생성 시 codex 자기 호출 절 제외 필요), bootstrap `setup.sh` 가 jira-worklog 외 skill 심링크와 `~/.codex/AGENTS.md` 심링크를 안 만듦(`install-codex-skill.sh` 의 메시지도 jira-worklog 고정), Codex `hooks.json` 에 dlc 훅 없음)
