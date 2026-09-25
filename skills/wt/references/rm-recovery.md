# rm-recovery — wt 생성 git 시퀀스 상세 · rm 실패 복구 분기 (참조)

`wt` 의 worktree **생성 git 시퀀스 상세**(§3.1~3.3·3.6 self-heal/bootstrap 이유)와 **`rm` 실패 stderr 분기 복구**(§6)를 담는다. SKILL 본문엔 절차 스텝·안전 게이트만 남기고 메커닉·폴백은 여기로.

> 이 파일은 자동 로드되지 않는다 — `wt` 가 **worktree 생성(§3 base ref·`--no-track`·self-heal 판단)** 또는 **`rm` 이 `git worktree remove` 실패로 분기할 때** 이 파일을 Read 한다. 안전 게이트(`--force`/`-D`/원격삭제 무확인 금지, remove 성공 후에만 branch 삭제)는 SKILL 본문(`## 주의`·rm §6)이 단일 소스이고, 여기는 "왜/어떻게"만.

## A. 생성 git 시퀀스 상세 (§3.1~3.3)
- **base ref**: `git symbolic-ref --short refs/remotes/origin/HEAD` → 실패 시 `origin/main` 폴백.
- `git fetch origin <default>` (실패해도 경고만).
- `git worktree add --no-track -b <slug> .claude/worktrees/<slug> origin/<default>`.
  - **`--no-track` 이유**: 새 브랜치 upstream 자동 설정 차단 → 첫 `git push` 시 global `push.autoSetupRemote=true` 가 `origin/<slug>` 으로 set(=자기 이름 원격 브랜치). track 두면 origin/<default> 로 잘못 향함.

## B. 환경 셋업 순서·self-heal (§3.6 heal/bootstrap)
새 cwd 에서 순서대로. 무엇이 실패해도 worktree 는 유지하고 에러를 그대로 보고(사용자가 수동 재실행 결정).
1. **submodule self-heal init**: `uv run --no-project python "${CLAUDE_SKILL_DIR}/heal_submodules.py"`. 중단됐던 submodule clone(objects 불완전 → "Unable to find current revision")을 자동 복구한 뒤 init. `.gitmodules` 없는 레포는 no-op(무해).
   - **bootstrap 보다 먼저 실행하는 이유**: bootstrap 의 submodule update 가 중단 corrupt 로 죽으면 이후 단계(uv sync 등)가 안 도는 것을 방지.
   - **자동 복구를 거부하고 exit 1 로 멈추는 경우**(어떤 deinit·삭제보다 먼저 판정): `.gitmodules` 의 path 를 읽을 수 없을 때(문법 오류·값 없는 path·항목 없음), submodule name 의 module dir 이 이 worktree 의 `modules` 디렉토리 밖을 가리킬 때(`..` 구성요소·절대경로 — linked worktree 에선 `<main>/.git/objects` 까지 닿는다), work tree 에 보존할 파일이 남았을 때. clone 한 repo 가 정하는 `.gitmodules` 를 삭제 경로로 믿지 않기 위해서다. 멈춘 뒤에는 원인을 확인하고 수동으로 복구한다.
2. `tools/bootstrap/bootstrap.py` 있으면 `uv run tools/bootstrap/bootstrap.py`(없으면 skip — 다른 프로젝트 무영향).

## C. rm 실패 stderr 분기 — 파일 점유 (§6)
`git worktree remove <path>` 실패 시 SKILL 본문 §6 이 stderr 로 분기한다. **안전 게이트·브랜치 삭제 순서(`--force`/`-D`/원격삭제 무확인 금지, remove 성공 후에만 branch 삭제)는 SKILL 본문(`## 주의`·rm §6)이 단일 소스** — 여기는 "파일 점유" 분기의 이유만:
- **파일 점유 류**("Access is denied"·"being used by another process"·"Directory not empty"·Windows "Invalid argument" 등 OS 삭제 실패): 살아있는 프로세스가 worktree 파일(`.venv` 등)을 잡고 있다. `wt rm` 은 **자동 종료하지 않고 안내**한다 — 사용자가 직접 부르는 경로라 점유 프로세스를 띄운 세션이 이 세션인지 알 수 없고, 경로 필터만으로는 사용자 서버와 구분되지 않는다(`/e` 7단계는 같은 세션이 띄운 프로세스를 회수할 수 있다 — `docs/worktree-lifecycle.md` §C). (`--force` 는 git 레벨이라 OS 파일점유는 못 푼다.)
- **부분 성공**(등록은 해제됐는데 디렉토리 잔존)은 점유와 별도 분기 — 확인·`prune` 절차는 `docs/worktree-lifecycle.md` §C.
