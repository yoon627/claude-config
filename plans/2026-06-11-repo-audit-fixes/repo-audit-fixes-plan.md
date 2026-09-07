---
title: repo-audit-fixes — .claude 설정 레포 전반 감사 후 일괄 버그/개선 수정
status: in_progress
started: 2026-06-11
updated: 2026-06-11
---

# Goal

`~/.claude` 설정 레포 전체를 5개 subagent 로 감사(완료)해 발굴한 **확실한 버그 · 문서 drift · CI 갭**을 일괄 수정한다. 라이브 설정이라 worktree `repo-audit-fixes`(branch `worktree-repo-audit-fixes`)에서 작업 후 PR. 사용자 요청: "이 레포에서 문제될만한거나 개선할만한거 모두 수정."

# Progress

- 2026-06-11: dlc structural 진입. 감사 5건 완료 — ①JS 4파일(statusline·subagent-statusline·codex-quota-refresh·notify-hook) ②scripts 9파일(gwl·install-*·pre-commit-check·notify*·prompt-gwl) ③wt python(heal_submodules+test) ④문서 정합성(README·CLAUDE.md·SKILL·agents·docs) ⑤settings.json 유효성. code-reviewer 3건은 codex 병행. worktree 생성·진입. **수정 0건** — 구현 직전 사용자가 `/e` 호출로 마무리. 감사 산출물을 본 plan 에 보존(아래 Next 가 구현 체크리스트). worktree clean → 임시 커밋 없음.

# Next

**구현 시작 — G1(보안)부터 우선순위순. 각 그룹 1커밋.** 다음 세션은 `/wt repo-audit-fixes` 진입 후 `/c`. 구현 후 code-reviewer(보안 그룹은 codex 병행) → 검증(아래 Decisions 의 검증 명령).

체크리스트(파일:라인 — 문제 — 수정방향):

## G1 — heal_submodules.py 보안/데이터손실 [HIGH·실증됨]
- [ ] **path traversal** (`:115,124`): submodule *name* 의 `../` 가 `git rev-parse --git-path modules/<name>` → `_force_rmtree` 로 흘러 **repo 밖 임의 디렉토리 삭제** 가능. `/wt` 가 자동 실행하므로 악성 `.gitmodules` repo 진입 시 트리거. → `Path(git_dir).resolve()` 후 `git rev-parse --git-common-dir`/modules 하위인지 `is_relative_to` 검증, name 에 `..`·경로구분자 있으면 reset 거부+중단.
- [ ] **공백 name 파싱** (`:75` `key,_,path = line.partition(" ")`): name 에 공백 있으면 깨져 안전게이트가 엉뚱 경로 검사 → 데이터손실 게이트 우회. git 기본 name==path 라 공백 경로 submodule 이 트리거. → `git config -z -f .gitmodules --get-regexp '^submodule\..*\.path$'` 로 바꿔 `\0` split, 각 record `partition("\n")` (value strip 금지).
- [ ] **fail-open 게이트** (`:146-156`): `_submodule_entries` 가 파싱 실패 시 `[]` → unsafe 빈 채 reset 진행. → `.gitmodules` 에 `[submodule` 있는데 entries 비면 heal 중단+수동 안내.
- [ ] **테스트 추가** (`test_heal_submodules.py`): 현재 `InitSubmodulesTest` 가 `_submodule_entries` 를 mock 해 파서↔게이트 단절. 실제 `.gitmodules`(공백 path·`../` name) + 실제 파서로 reset 거부 단언하는 회귀 테스트.
- 후속(선택): `.git` 파일 `gitdir:` prefix 검증(`:94`), update 실패 시 stderr corrupt 시그니처 확인 후에만 reset(`:142`), `rm -rf` 로그 OS중립화(`:153`).

## G2 — pre-commit-check pre-push 가드 [HIGH·실증됨] (ps1+sh 쌍)
- [ ] **pre-push 가 HEAD 검사** (`ps1:23`, `sh:27` `git show HEAD:settings.json`): push 되는 sha 가 아니라 checkout 된 HEAD 검사 → clean HEAD 에서 `git push origin tainted-branch` 하면 토큰 무검사 통과(우회). → stdin 각 라인 `<local sha>` 로 `git show "<lsha>:settings.json"` 검사. delete push(zero sha `0000…`) skip. 여러 ref 루프. violations 로직 함수화.
- [ ] **bypass 메시지 오류** (`ps1:67` `git $Mode --no-verify` → `git pre-commit/pre-push --no-verify` 출력): Mode→실제 cmd(commit/push) 매핑.
- [ ] **PS5.1 `2>$null`+EAP=Stop crash** (`ps1:21` `git ls-tree … 2>$null`): PS5.1 은 native stderr redirect 를 terminating error 화. unborn HEAD 등에서 fail-closed crash(sh 는 fail-open 으로 불일치). → redirect 제거 또는 try/catch.

## G3 — statusline.js / subagent-statusline.js
- [ ] **bg slug 불일치** (`statusline.js:161` `cwd.replace(/[:\\\/]/g,'-')`): 실제 `%TEMP%\claude` 디렉토리는 `.` 도 `-` 치환(`C--Users-USER--claude`) → dot 포함 경로는 bg indicator 영구 미표시(실측). → `cwd.replace(/[^A-Za-z0-9-]/g,'-')`, `%TEMP%\claude` 목록과 대조 확인.
- [ ] **ctime→birthtime** (`:172,177`): 실행 중 작업의 elapsed 가 "마지막 쓰기 후"(거의 항상 수초)로 표시(실측, Windows ChangeTime). → `stat.birthtimeMs || stat.ctimeMs`.
- [ ] **null stdin 방어** (`:28`): `printf 'null'` 입력 시 TypeError(재현). → `JSON.parse(...) || {}`. (subagent-statusline.js:8 동일.)
- [ ] **subagent-statusline 스키마 드리프트** [리스크 높음·미확정]: 현재 `input.status/context_window.current_usage/cost.total_duration_ms`(메인 스키마) 읽음 — docs 는 subagent stdin 이 `tasks[]` 배열(`id,name,type,status,startTime,tokenCount`)이라 함. 현재 출력이 빈 문자열일 가능성. → **방어적 처리**: 신규 `tasks[]` 있으면 그걸로, 없으면 기존 필드 fallback(양 스키마 안전). 가능하면 라이브 stdin 1회 캡처로 확정 후. 잘못 고치면 subagent 패널 깨짐 — 보수적으로.
- [ ] (선택·리스크중) **git 3회 spawn→1회** (`:129-141`): `git rev-parse --abbrev-ref HEAD --show-toplevel --path-format=absolute --git-common-dir` 1회(검증됨, 96ms→32ms). 3줄 split 파싱 주의 + docs mock JSON 으로 수동 확인.

## G4 — codex-quota-refresh.js
- [ ] **proc.stdin error handler 부재** (`:91`): child 조기종료 시 EPIPE uncaught → negative cache 못 써 respawn churn. notify-hook.js:95 는 이미 방어. → `proc.stdin.on("error",()=>{})`.
- [ ] **exit-0 조기리턴 미settle** (`:80` `if(code===0)return;`): RPC 응답 없이 code 0 종료 시 settle 없이 20초 타이머 대기 후에야 negative cache. → 즉시 settle.
- [ ] **tmp 고아** (`:104-106`): `renameSync` 실패 시 `.tmp.<pid>` 잔존(catch 에 unlink 없음). → catch 에서 tmp 정리.

## G5 — install 스크립트
- [ ] **install-hooks.ps1:3 null `.Trim()`**: 비-git 디렉토리서 raw exception, line4-6 가드 도달불가(재현). → 획득 후 null 체크 다음 Trim(install-gwl.ps1:11 패턴).
- [ ] **worktree 훅 설치 실패** (`install-hooks.ps1:9`, `sh:13` `$repoRoot/.git/hooks`): linked worktree 의 `.git` 은 파일이라 mkdir 에러 + `core.hooksPath` 미고려. worktree 중심 워크플로(§8)와 충돌. → `git rev-parse --git-path hooks`.
- [ ] **.bak 단일슬롯 clobber** (`ps1:29`, `sh:37`): 두번째 백업이 첫 백업 무경고 소실(이 repo `.git/hooks/pre-commit.bak` 이미 존재). → timestamp suffix 또는 기존 .bak 시 중단.

## G6 — gwl 중첩 worktree 이중 마커
- [ ] `gwl.ps1:16` / `prompt-gwl.py:29`: 중첩 worktree(`<repo>/.claude/worktrees/<slug>`)에서 main(prefix 매칭)+현재 worktree 둘 다 `→`. → 가장 긴(구체적) 매칭 경로 하나만 마킹.

## G7 — .editorconfig
- [ ] `[*.ps1] charset = utf-8-bom` 추가: 현재 `[*] charset=utf-8` 가 gwl.ps1/notify-hook.ps1 의 BOM(`→`·한글 깨짐 방지, 바이트 efbbbf 확인)과 충돌 — editorconfig 준수 저장 시 BOM 제거 회귀.

## G8 — 문서 drift
- [ ] **README:38**: "SessionStart hook 이 pwsh 있으면 매 세션 자동 등록" — 제거됨(L345/355, settings.json 엔 git pull 만). → "수동 1회 실행 필요".
- [ ] **README:444/449**: rollback 의 `git push --force-with-lease origin main` 이 자체 pre-push hook 에 차단됨 + 가드의 main/master push 차단 기능이 D섹션(107-109 등)에 미기재. → `--no-verify` 필요 명시 + 가드 기능에 "main/master 직접 push 차단" 추가.
- [ ] **README wt 섹션(306-313)+Layout(494-495)**: `.env` 자동복사·heal_submodules self-heal·bootstrap 미반영, `heal_submodules.py`/`test_*.py` 미등재. → 추가.
- [ ] **agents codex 참조 절대경로화**: `code-reviewer.md:51`, `plan-reviewer.md:39`, `architecture-reviewer.md:96,105` 의 `docs/codex-review.md`(상대) → `~/.claude/docs/codex-review.md`(codex-review.md:5 가 "절대경로 명시 참조" 규약, subagent 는 대상 repo cwd 라 상대 해석 불가).
- [ ] **external codex 모드 비대칭**: `code-reviewer.md`/`plan-reviewer.md` 에 `CLAUDE_REVIEW_CODEX_MODE=external` 인지 문단 없음(arch:126 엔 있음). → 대칭 문단 추가.
- [ ] **codex-review.md:3** "각 agent 의 흩어진 codex 호출 블록을 대체한다" — 실제 인라인 블록 잔존(code-reviewer.md:52-61 등)이라 거짓 + 사본 drift(Nit 등급 불일치). → "공통 규약 정의, agent 인라인 예시는 본 문서 우선"으로 정정하거나 인라인 블록 실제 제거.

## G9 — CI lint.yml [py/ps1 전면 미커버 — 17개 test 가 CI 미실행]
- [ ] python: `actions/setup-python` + `python -m unittest`(skills/wt, 로컬 17 OK) + `py_compile` 3파일(prompt-gwl·heal_submodules·test).
- [ ] secret-guard 서버측 백스톱: `bash scripts/pre-commit-check.sh pre-push` 상당(훅은 클론별 opt-in 이라 미설치 PR 토큰 무방비).
- [ ] (선택) statusline 스모크(docs mock JSON + `{}`·`null` 파이프 → exit0), ps1 파싱 체크.

## 저우선/선택
- notify.ps1:104 balloon fallback `Start-Sleep 5`+`Dispose()`(미대기로 표시 전 소멸 가능).
- statusline fmtQuota 중복(38-57 vs 99-113), cache/lock 상수 양파일 중복(statusline 63-67 vs refresh 14-17, `25s>20s` 암묵결합 무주석), readdir 선형 비용.
- pre-commit-check 매치 토큰 30자 출력 → 패턴명만(§8 정신).

# Decisions

- **작업 위치**: worktree `repo-audit-fixes` / branch `worktree-repo-audit-fixes` 에서 진행(라이브 설정 보호). plan 은 main worktree `plans/` 에 둠(worktree 삭제 시 동반소실 회피 + 어디서든 `/c` 발견). → 이어가려면 `/wt repo-audit-fixes` 진입.
- **/e 예외 적용**: "plan 없으면 안 만든다" 원칙이나, dlc structural 감사 산출물(~470k 토큰) 보존이 다음 세션 이어받기에 필수라 CLAUDE.md §10 우선해 plan 생성(사용자에 명시).
- **statusline 고위험 변경 보수적 취급**: subagent-statusline 스키마는 양 스키마 fallback(방어적)으로, git 3회→1회 통합은 선택(검증 철저). 라이브라 커밋 전 `node --check` + docs mock JSON 파이프 필수.
- **기각**: claude-code-guide 의 `model: claude-fable-5[1m]` ANSI 오판 — `[1m]` 은 1M 컨텍스트 변형 정식 모델 ID(환경 정보 확인). `skipWorkflowUsageWarning` "문서에 없음"도 신뢰도 낮아 보류.
- **손대지 않음(사용자 진행분)**: main worktree 의 `settings.json` uncommitted `model`/`effortLevel` 키. effortLevel:xhigh 가 env CLAUDE_CODE_EFFORT_LEVEL=max 와 충돌(env override)하나 사용자 판단 영역 — 보고만.
- **검증 명령**: `node --check {statusline,subagent-statusline,codex-quota-refresh,scripts/notify-hook}.js` / `node -e "JSON.parse(fs.readFileSync('settings.json'))"` / `python skills/wt/test_heal_submodules.py`(또는 `-m unittest`) / `python -m py_compile` 3파일 / shellcheck(로컬 미설치 가능 — CI 의존). lint.yml 이 CI 진실.
- **그룹 우선순위**: G1(보안)→G2(보안)→G3·G4(라이브 버그)→G5·G6·G7→G8·G9(문서·CI). 보안 2그룹은 code-reviewer + codex 병행.

# Key Files

- `skills/wt/heal_submodules.py` + `test_heal_submodules.py` — G1. 파서(`_submodule_entries:58`)·게이트(`_submodule_worktree_has_files:83`)·삭제(`_force_rmtree:99`,`_reset_submodule:111`).
- `scripts/pre-commit-check.ps1` / `.sh` — G2(pre-push sha)·G5(공통). 양 플랫폼 쌍 동기 필수.
- `scripts/install-hooks.ps1` / `.sh`, `scripts/install-gwl.ps1` — G5.
- `scripts/gwl.ps1`, `scripts/prompt-gwl.py` — G6.
- `statusline.js`, `subagent-statusline.js`, `codex-quota-refresh.js` — G3·G4(라이브 — 보수적).
- `.editorconfig` — G7. `.github/workflows/lint.yml` — G9.
- `README.md`, `agents/{code-reviewer,plan-reviewer,architecture-reviewer}.md`, `docs/codex-review.md` — G8.
- 감사 subagent IDs(SendMessage 로 재질의 가능): JS=af2e5c8179f8c6cfd, scripts=a5f925766ba962972, wt-py=a8423e501b67ddbf4, 문서=afe4c25fd3c524338.

# Blockers

- 없음. subagent-statusline 스키마만 미확정 → 구현 시 양 스키마 fallback 으로 우회(라이브 stdin 캡처 가능하면 확정).
