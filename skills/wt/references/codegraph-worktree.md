# codegraph-worktree — wt 신규 생성 시 codegraph 인덱스 (참조)

`wt` request 경로의 환경 셋업 §4.6 마지막 단계 **codegraph worktree-local 인덱스**의 조건·staleness·조회 지침을 담는다. SKILL 본문엔 "조건부·백그라운드 codegraph init" 1줄만 남기고 세부는 여기로.

> 이 파일은 자동 로드되지 않는다 — `wt` 가 **worktree 생성 후 codegraph init 을 판단할 때**, 또는 그 worktree 에서 **codegraph 조회가 stale 해 보일 때** 이 파일을 Read 한다.

## init 조건 (둘 다 만족일 때만)
heal·bootstrap 뒤, 조건부·백그라운드:
1. `codegraph` 바이너리가 PATH 에 있음.
2. **main worktree**(`git worktree list --porcelain` 의 첫 `worktree <path>` 라인, `.env` 복사와 동일 기준)에 `.codegraph/` 가 있음.
- 둘 다 만족이면 이 worktree 에서 `codegraph init` 을 `run_in_background` 로 실행해 worktree-local 인덱스 생성. init 안 하면 worktree 는 상위 탐색으로 main 의 `.codegraph/`(=main 브랜치 코드)를 잡아 **이 worktree 변경이 누락**된다.
- 조건 불만족이면 skip(codegraph 미사용 레포 무영향). 실패해도 인덱스만 없을 뿐 worktree·dlc 는 진행.
- (`.codegraph/` 는 루트 `.gitignore` whitelist 로 자동 ignore.)

## ⚠️ 백그라운드 주의
백그라운드라 인덱싱 완료 전 dlc 초기 codegraph 조회는 생성 중 부분 인덱스나 main fallback 을 볼 수 있다(곧 sync — 감수).

## ⚠️ staleness / projectPath (실측)
codegraph MCP 세션의 **기본 조회는 세션 시작 시점 인덱스에 고정**되어 EnterWorktree 이후·merge 반영 후에도 stale 할 수 있다(실측: 같은 커밋에서 기본 17파일/172노드 vs `projectPath` 명시 20파일/221노드).
- 조회 시 `projectPath` 를 **현재 worktree 절대경로로 명시**.
- 오래돼 보이면 그 repo 에서 `codegraph init` 재실행(비파괴).
- 근거: memory `codegraph-projectpath-explicit`.
