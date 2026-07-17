# rm-recovery — wt 생성 git 시퀀스 상세 · rm 실패 복구 분기 (참조)

`wt` 의 worktree **생성 git 시퀀스 상세**(§4.1~4.3·4.6 self-heal/bootstrap 이유)와 **`rm` 실패 stderr 분기 복구**(§6)를 담는다. SKILL 본문엔 절차 스텝·안전 게이트만 남기고 메커닉·폴백은 여기로.

> 이 파일은 자동 로드되지 않는다 — `wt` 가 **worktree 생성(§4 base ref·`--no-track`·self-heal 판단)** 또는 **`rm` 이 `git worktree remove` 실패로 분기할 때** 이 파일을 Read 한다. 안전 게이트(`--force`/`-D`/원격삭제 무확인 금지, remove 성공 후에만 branch 삭제)는 SKILL 본문(`## 주의`·rm §6)이 단일 소스이고, 여기는 "왜/어떻게"만.

## A. 생성 git 시퀀스 상세 (§4.1~4.3)
- **base ref**: `git symbolic-ref --short refs/remotes/origin/HEAD` → 실패 시 `origin/main` 폴백.
- `git fetch origin <default>` (실패해도 경고만).
- `git worktree add --no-track -b <slug> .claude/worktrees/<slug> origin/<default>`.
  - **`--no-track` 이유**: 새 브랜치 upstream 자동 설정 차단 → 첫 `git push` 시 global `push.autoSetupRemote=true` 가 `origin/<slug>` 으로 set(=자기 이름 원격 브랜치). track 두면 origin/<default> 로 잘못 향함.

## B. 환경 셋업 순서·self-heal (§4.6 heal/bootstrap)
새 cwd 에서 순서대로. 무엇이 실패해도 worktree 는 유지하고 에러를 그대로 보고(사용자가 수동 재실행 결정).
1. **submodule self-heal init**: `uv run --no-project python "${CLAUDE_SKILL_DIR}/heal_submodules.py"`. 중단됐던 submodule clone(objects 불완전 → "Unable to find current revision")을 자동 복구한 뒤 init. `.gitmodules` 없는 레포는 no-op(무해).
   - **bootstrap 보다 먼저 실행하는 이유**: bootstrap 의 submodule update 가 중단 corrupt 로 죽으면 이후 단계(uv sync 등)가 안 도는 것을 방지.
2. `tools/bootstrap/bootstrap.py` 있으면 `uv run tools/bootstrap/bootstrap.py`(없으면 skip — 다른 프로젝트 무영향).
3. codegraph init(조건부·백그라운드) — `references/codegraph-worktree.md`.

## C. rm 실패 stderr 분기 — 파일 점유 상세 (§6)
`git worktree remove <path>` 실패 시 SKILL 본문 §6 이 stderr 로 분기한다. **안전 게이트·브랜치 삭제 순서(`--force`/`-D`/원격삭제 무확인 금지, remove 성공 후에만 branch 삭제)는 SKILL 본문(`## 주의`·rm §6)이 단일 소스** — 여기는 "파일 점유" 분기의 원인·대응 세부만:
- **파일 점유 류**("Access is denied"·"being used by another process"·"Directory not empty" 등 OS 삭제 실패): 그 worktree 의 `.codegraph/` 를 codegraph daemon 이 잡고 있을 수 있다(그 worktree 에서 codegraph MCP 세션을 띄웠던 경우만 — `init`·`status` 로는 안 뜸). **자동 종료하지 않고 안내**: 그 세션을 닫거나 daemon idle 자동종료(~5분) 후 재시도, 급하면 수동으로 해당 node 프로세스 종료. (`--force` 는 git 레벨이라 OS 파일점유는 못 푼다.)
