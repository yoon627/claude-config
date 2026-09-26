---
title: repo-audit-followups — 두 감사(2026-06-11·2026-09-25)에서 남은 결함을 주인 있게 추적
status: open
started: 2026-09-25
updated: 2026-09-26
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

- (해소) `push-remote-scope` 가 가드의 인자 없는 호출 의미를 바꾸면 `scripts/ci-secret-scan.sh` 도 맞춰야 하는가 — 가드가 원격 이름 대신 stdin remote sha 로 판단하게 되어 인자 없는 호출은 그대로이고, CI 는 이미 base 를 remote sha 로 넘기고 있었다. 추적 ref 를 피하려던 임시 repo 는 필요 없어져 같은 커밋에서 없앴다(push-remote-scope plan).

- (해소) Codex 용 `AGENTS.md` 는 CLAUDE.md 심링크 — 2026-06-10 사용자 결정(`a3d7bdc`)을 2026-09-25 복원(config-docs-sync).

# Plans

- `plans/2026-09-25-repo-audit-remaining/repo-audit-remaining-plan.md` — G1 heal 경로 탈출·G2 pre-push 범위 비밀 스캔. 아래 단위들의 상세 체크리스트 원본은 이 plan 의 `# Deferred`.
- `plans/2026-09-25-repo-audit-g3-g4-live-bugs/repo-audit-g3-g4-live-bugs-plan.md` — G3 statusline(null 입력·bg 표시 제거·subagent 행 현행 스키마로 재작성)·G4 codex-quota-refresh(종료 경로 통합·응답 없는 종료 즉시 처리·캐시 쓰기 실패 시 잔류·임시 파일)
- `plans/2026-09-25-repo-audit-g5-g7-install/repo-audit-g5-g7-install-plan.md` — G5 install-hooks(git 밖 오류·공용 hooks 디렉토리·`core.hooksPath` 거부·백업 보존)·G6 gwl 이중 마커·G7 `.editorconfig` ps1 BOM
- `plans/2026-09-26-push-remote-scope/push-remote-scope-plan.md` — pre-push 가드가 추적 ref 대신 push 대상 ref 의 실제 값(stdin remote sha)으로 "이미 공개됨"을 판단(G2 accepted-risk, 사용자 결정 2026-09-26 — 원격 이름 기준 초안 기각), CI 스캔의 임시 repo 제거
- `plans/2026-09-26-repo-audit-g8-g9-docs-ci/repo-audit-g8-g9-docs-ci-plan.md` — G8 README 유출 대응 절·`CLAUDE_REVIEW_CODEX_MODE` 폐기(사용자 결정), G9 CI 비밀 스캔 백스톱(`scripts/ci-secret-scan.sh`; statusline 스모크는 g3-g4 의 `statusline.test.js` 가 CI 에서 이미 돈다)
- `plans/2026-09-25-config-docs-sync/config-docs-sync-plan.md` — CLAUDE.md §8 pre-push·§3-1 문구, 저장소 밖 적용분(autoMode.environment repo 별 분리·GitHub ruleset `main-guard`·Codex 쪽 재정렬)의 README·wiki 문서화
- `plans/2026-09-26-autopull-verified-ff/autopull-verified-ff-plan.md` — 1단계: main push 의 lint 가 통과하면 CI 가 그 sha 를 `ci/verified` 브랜치의 기록 커밋(`main-sha` 파일)으로 남긴다(GITHUB_TOKEN 은 main 커밋을 가리키는 ref 를 workflow 변경 뒤 옮기지 못할 수 있어 기록 커밋 방식 — 사용자 결정 2026-09-26)
- autopull-verified-client (미착수) — 2단계: `session-start-pull.sh` 가 `ci/verified` 의 `main-sha` 가 origin/main 의 조상일 때만 그 sha 까지 ff(`--prune`, `CLAUDE_AUTOPULL_VERIFY=0` 로 끄기), `session-brief.js` N 이 보류 사유(기록 없음·미전진·main 밖)를 처방과 함께 알림, 테스트 하니스에서 `CLAUDE_AUTOPULL_*` env 제거, FETCH_HEAD 서술 정정, README 에 "검증 게이트는 SessionStart 경로만(post-checkout·`/e` pull 은 아님)". **착수 조건**: 1단계 머지 push 에서 `origin/ci/verified:main-sha` 가 생긴 것을 확인. 출발점은 1단계 plan 의 Decisions·Review Disposition(plan-reviewer 약한 우려 다수가 이 단위 몫). 더 정할 것: 영구 정지 수단(`ci/verified` 삭제는 다음 green push 까지만), 기록이 tip 보다 뒤처지는 경우(`[skip ci]`·concurrency 교체)의 브리프 문구, Actions 가 꺼진 fork 를 origin 으로 쓰는 경우의 안내(`CLAUDE_AUTOPULL_VERIFY=0`)
- `plans/2026-09-25-repo-small-cleanups/repo-small-cleanups-plan.md` — `.gitignore` `/skills/synced/` · bootstrap README settings.json 서술 · verify.sh 를 git ls-files 기반으로(main checkout 상시 FAILED 해소)
- `plans/2026-09-25-improve-marker/improve-marker-plan.md` — `/improve` 완료 시 `last-improve` 마커 갱신(`dlc-signal.js mark`)
- `plans/2026-09-26-audit-install-fixes/audit-install-fixes-plan.md` — low 묶음(`audit-low-batch`, 2026-09-26 사용자 선택으로 아래 단위로 분할)의 첫 단위: heal `_force_rmtree` 가 symlink 를 따라 chmod 하지 않게, macOS bootstrap 이 Codex skill 7종·`~/.codex/AGENTS.md` 를 연결(`install-codex-skill.sh --file`, 메시지 일반화). 저장소 밖 항목 둘은 main 에서 처리했다 — pyright-lsp 플러그인 끔(바이너리 없음, 사용자 결정), memory 의 끊긴 `codegraph-projectpath-explicit` 링크 정리.
- audit-docs-drift (미착수) — `docs/codex-review.md:61` 의 Codex 기본 effort 서술(`xhigh` → 실제 `low`), README `--no-verify` 안내(`README.md:127,724`)를 §8 과 맞춤(사람이 하는 복구로 명시), RTK.md `@import` 는 그대로 두고 README 에 "worktree 사본·rtk 미설치 머신에서는 비어 있음" 한 줄(사용자 결정), wiki `anthropic-claude-models` 모델 목록 갱신(researcher), 권한 규칙 잔여 한계(`bash <script>`·브랜치 이름 없는 push) 문서화.
- ledger-bash-edits (미착수) — `dlc-early-stop` 이 Bash 로 한 편집(sed -i·리다이렉션 등)을 못 봐 오탐(공용 wiki `workflow-failures` 17회). 감지 방식 설계부터 — 운영 자산(hook)이라 방향을 먼저 정한다(structural 예상). 끝나면 `wiki/pages/decision/workflow-failures.md` 의 `audit-low-batch` 포인터를 이 단위로 갱신.
- codex-agents-hooks (미착수) — 순서: 먼저 `~/.codex/agents/*.toml` 08-01 스냅샷 재생성(codex 자기 호출 절 제외, 재생성 뒤 `CLAUDE_REVIEW_CODEX_MODE` 잔존 0 확인 — g8-g9 plan `# Deferred` 에서 넘어옴), 그다음 Codex `hooks.json` 의 dlc 훅은 Codex hook 호환 조사 결과로 할지 정한다. 저장소 밖 작업이라 worktree 는 README 서술을 고칠 때만. `README.md:396` 을 함께 고치므로 audit-install-fixes 머지 뒤에.
- native-overlap-recheck (미착수) — `native-overlap-ledger` 재판정(2026-08-06·v2.1.222 이후 51일, `improve.sh deep` + SKILL §6). `/improve` 의 주기 작업이라 이 묶음을 닫으려면 한 번 돌려야 한다.
- windows-ps1-verify (미착수) — Windows 에서만 검증 가능한 것: pre-commit 경로 ps1 의 native 출력 CP949 디코딩(PS5.1), `setup.ps1`·`install-codex-skill.ps1` 의 Codex skill 7종·`%USERPROFILE%\.codex\AGENTS.md` 연결(macOS 는 audit-install-fixes). pwsh·Windows 실행 없이는 넣지 않는다(공용 wiki `lesson-no-speculative-platform-switch`). **선행: audit-install-fixes** — 그 단위가 README 에 적는 macOS/Windows 차이 서술을 지우고, `install-codex-skill.ps1`·`.test.ps1` 에 `.sh` 의 `--file` 에 해당하는 옵션을 맞춘다. heal 의 Windows 경로(read-only 해제 재시도, 트리 안 junction — 핸들러의 `os.path.islink` 는 junction 을 못 본다)도 여기서 확인.
- audit-leftovers (미착수) — `repo-audit-remaining` plan `# Deferred` 저우선 절에서 어느 단위에도 배정되지 않은 항목(사용자 결정 2026-09-27): pre-push 스캔이 push 커밋 전부를 한 명령줄로 넘겨 790+ ref 새 원격 push 에서 Windows 명령줄 한계, heal `git submodule deinit -f -- <path>` 의 pathspec(`--literal-pathspecs` 검토), ps1 `~/.claude` 면제 판정이 symlink 를 풀지 못함, notify.ps1 balloon fallback 재확인, statusline `fmtQuota`·cache/lock 상수 중복·readdir 선형 비용, heal 후속(`.git` 파일 `gitdir:` prefix 검증·corrupt 시그니처 확인 후 reset·`rm -rf` 로그 OS 중립화). ps1 항목은 windows-ps1-verify 와 겹치면 그쪽으로.
