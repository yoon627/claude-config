---
title: codex-jira-worklog-skill — jira-worklog를 Codex에서 직접 사용 가능하게 한다
status: done
started: 2026-08-12
updated: 2026-08-20
---

# Goal

기존 `jira-worklog` 구현을 단일 소스로 유지하면서 Codex가 스킬을 직접 발견·호출하게 한다.
Codex/Windows에서도 `/e`의 worklog 단계가 사용 가능한 Python 실행기로 동작하게 한다.

# Progress

- 2026-08-20: 막혔던 blocker 2건을 해소하고 잔여 검증을 **전부 통과**했다. launcher dry-run exit 0, `test_launcher.sh`, bootstrap installer test, shell 문법 4/4, Node 10/10, Python 2/2(`test_session_time.py` 1건은 Windows NUL 경로 baseline — CI ubuntu green, 변경 무관). shellcheck 는 로컬 미설치라 CI 검증에 맡긴다. status done.
- 2026-08-12: 현재 상태 실증 — Codex rollout 집계 dry-run 성공, direct skill 미노출, `/e`의 `python` 명령은 현재 Windows PATH에서 실패.
- 2026-08-12: `origin/main@a0edca6` 기준 `codex-jira-worklog-skill` worktree 생성, ignored `.claude/settings.local.json` 복사, submodule self-heal 완료, codegraph init 시작.
- 2026-08-12: plan-review `CONDITIONAL` 반영 후 helper 구현. Windows junction 상태 행렬 통과, 실제 `$HOME/.agents/skills/jira-worklog` junction 생성, `uv --cache-dir .tmp\uv-cache run --no-project python ... --all` dry-run 성공.
- 2026-08-12: code-review의 installer 실패 전파·Python-only 호환성·doc/CI drift를 수정하기 위해 setup 실패 전파, `run_worklog` 플랫폼 launcher(uv 우선·Python fallback), docstring/README/CI 동기화, dangling/dry-run 상태 검증을 추가했다.
- 2026-08-12: PowerShell helper 상태 행렬·POSIX launcher fallback/argv 테스트·shell syntax 통과. `test_worklog_scope.py` 29/29, `test_register_gate.py` 19/19 통과. `test_session_time.py`는 기존 Windows NUL 경로 baseline 1건 실패(59/60)이며 변경과 무관하다.

# Next

다음: uv managed Python 권한이 해결되면 Windows launcher dry-run을 재검증하고, 현재 Codex 세션은 재시작 후 skill catalog를 확인한다.

# Decisions

- 기존 `skills/jira-worklog/`를 복제하지 않는다. 공식 Codex user-scope 검색 위치인 `$HOME/.agents/skills/jira-worklog`가 이 디렉터리를 가리키게 해 구현과 지침의 단일 소스를 유지한다.
- 저장소 밖 user-scope 연결은 설치 상태로 두되, `scripts/bootstrap/setup.ps1`·`setup.sh`가 junction/symlink를 멱등 설치하도록 tracked 재현 경로를 둔다. source는 worktree 삭제 후에도 살아 있는 `$HOME/.claude/skills/jira-worklog`로 고정하고 `SKILL.md` 실재를 생성 전에 확인한다.
- Python 실행은 `run_worklog.sh`·`run_worklog.ps1` launcher가 담당한다. `uv`를 우선 사용하되 기존 Claude 환경의 Python-only 호환성을 위해 POSIX는 `python3`/`python`, Windows PowerShell은 `python`/`python3`/`py`로 fallback한다. 모든 CLI 인자는 Python 스크립트 뒤에 그대로 전달하고, uv cache는 기본 충돌을 피하는 `$HOME/.claude/.tmp/jira-worklog-uv-cache`를 사용한다(`UV_CACHE_DIR`로 override 가능). `uv` 실행 자체가 실패한 뒤에는 `--register` 부분 반영 중복을 막기 위해 다른 실행기로 재시도하지 않는다.
- `$wt` switch에 Jira 외부 write를 새로 결합하지 않는다. 기존 계약대로 `/e`와 direct `jira-worklog` 호출이 기록 진입점이다.
- 3 Whys: direct 호출 불가 → Codex 검색 위치에 skill이 없음 → 원본이 Claude 전용 위치에만 있음. `/e` 실패 → 지침이 `python`을 고정 호출 → 현재 Codex Windows PATH에는 `python`이 없고 fallback 계약도 없음.

# Key Files

- `skills/jira-worklog/SKILL.md` — Codex trigger와 portable 실행 절차의 단일 지침.
- `skills/jira-worklog/run_worklog.sh`, `run_worklog.ps1` — uv/Python 선택과 CLI argv 전달을 담당하는 공통 launcher.
- `skills/jira-worklog/test_launcher.sh` — POSIX Python fallback과 argv 전달 테스트.
- `skills/e/SKILL.md` — 마무리 단계에서 같은 실행 절차 사용.
- `scripts/bootstrap/setup.ps1`, `scripts/bootstrap/setup.sh` — Codex user-scope skill 연결을 새 머신에서도 멱등 재현.
- `scripts/bootstrap/README.md` — bootstrap 재현 대상과 Codex 전제 문서화.
- `scripts/bootstrap/install-codex-skill.ps1`, `.sh` — 안전한 junction/symlink 설치·충돌 보호.
- `scripts/bootstrap/install-codex-skill.test.ps1`, `.test.sh` — Windows/Unix link 상태 행렬 테스트.
- `.github/workflows/lint.yml` — Unix helper 테스트와 기존 검증 연결.
- `README.md` — Codex 설치·호출 방식과 `/e` 동작 문서화.
- `$HOME/.agents/skills/jira-worklog` — Codex user-scope discovery 연결(로컬 설치 상태, tracked 아님).

# Blockers

(해소 — 2026-08-20)
- ~~uv managed Python `Access is denied`~~ → 권한 정상 셸에서 launcher dry-run **exit 0** 재검증 완료.
- ~~새 Codex 세션 catalog 갱신 관찰~~ → junction 실재 확인(`~/.agents/skills/jira-worklog`), fresh forward-test 항목은 이미 충족. **잔여**: Codex 세션의 implicit invocation 은 Claude 세션에서 관찰 불가해 미확인으로 둔다 — 기능 결함이 아니라 관찰 경로의 한계이며, 실사용 시 catalog 에 안 뜨면 그때 재개한다.

# Acceptance

- [x] Codex user-scope 위치에서 `jira-worklog/SKILL.md`가 발견되고 안정적인 `$HOME/.claude/skills/jira-worklog`와 동일한 실체를 가리킨다 — 실제 junction + 파일 존재 확인.
- [x] 설치 후 새 Codex subagent에서 `jira-worklog`를 직접 호출해 dry-run이 성공하고 Codex rollout 항목이 나타난다 — fresh forward-test 관찰. 현재 세션 catalog는 재시작 전 갱신을 완료 근거로 쓰지 않는다.
- [x] Windows junction과 Unix symlink 설치가 `target 없음`, `정상 link 재실행`, `다른 target/실제 directory`, dangling link, `source SKILL.md` 없음, dry-run 무변경을 안전하게 처리한다. 정상은 멱등 skip, 충돌·source 없음은 기존 경로 무변경+명확한 실패 — Windows 상태 행렬 통과, Unix assertion은 CI에서 실행.
- [x] `uv` 우선 launcher 의 문서화된 경로로 dry-run 이 exit 0 이다 — **2026-08-20 재검증 완료**. 권한이 정상인 셸(`uv 0.11.7`)에서 `bash run_worklog.sh` 를 --register 없이 실행해 **exit 0**, worktree 별 시간 분리 출력까지 확인했다(경고는 tzdata 미설치뿐). `test_launcher.sh` 통과.
- [x] `$e`와 direct skill이 같은 플랫폼 launcher와 `--register` 전달 규칙을 사용한다 — 호출부 `rg`, launcher 문법·POSIX fallback/argv 테스트 및 docstring 동기화.
- [x] Jira 등록은 실행하지 않은 상태에서 Codex rollout 항목이 dry-run에 나타난다 — 실제 `--all` 관찰.
- [x] 기존 Python 단위테스트와 repo lint/plan integrity 가 통과한다 — **2026-08-20 로컬에서 CI 동등 실행**: Node 유닛 10/10, Python 2/2 통과 (`test_session_time.py` 1건은 Windows NUL 경로 baseline — CI ubuntu green, 변경 무관), `install-codex-skill.test.sh`·`test_launcher.sh` 통과, shell 문법 4/4, plan-lint 통과. shellcheck 는 로컬 미설치라 머지 후 CI 로 확인한다.
- [x] README와 bootstrap README가 Codex discovery·portable 실행 변경과 동기화된다 — diff/문서 점검.
- [x] rollback 안전성: installer는 target을 삭제하지 않으며, 실제 directory·다른 target은 보존한다 — 상태 행렬 테스트와 helper 문서 확인.

# Review Disposition

- plan-review `CONDITIONAL` 반영:
  - `fix`: filesystem 확인만으로 discovery를 완료 판정하지 않고 새 Codex 세션 forward-test 추가.
  - `fix`: link source를 `$HOME/.claude/skills/jira-worklog`로 고정하고 source 존재 검증 추가.
  - `fix`: launcher를 `uv` 우선·Python fallback 단일 진입점으로 만들고 `/e`·direct skill·CLI docstring을 동기화.
  - `fix`: `setup.sh`가 Codex installer non-zero를 성공으로 보고하지 않도록 실패 전파.
  - `fix`: bootstrap 충돌·dangling·source 없음 상태와 안전 rollback을 acceptance에 명시.
  - `fix`: helper 상태 행렬에 dangling link와 dry-run 무변경을 추가하고 CI shellcheck 대상에 bootstrap shell을 포함.
  - `fix`: test/CI 및 bootstrap README의 검증 범위를 Key Files/Acceptance에 반영.
  - `false-positive`: “사용자 승인 대기 stale” — 사용자는 작업 재개를 승인했지만, bootstrap까지 확장된 multi-file plan은 아직 제시되지 않아 CLAUDE.md §3-3 방향 승인이 필요.

# Deferred

- `--all` dry-run이 현재 코퍼스에서 10.3초로 과거 5초 acceptance보다 느림. 이번 Codex discovery/launcher 범위와 독립인 성능 이슈라 별도 작업 후보(낮음).
