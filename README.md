# Claude Code Global Config (Windows / macOS)

Windows 에서 사용하는 `%USERPROFILE%\.claude\` 또는 macOS 에서 사용하는 `~/.claude/` 의 사용자 글로벌 설정·에이전트·명령·스킬·후크·스크립트·스테이터스라인을 한 레포에 모은 것. 다른 머신에서 동일한 작업 환경을 빠르게 재현하기 위함.

대상: Claude Code 를 깊이 사용하는 본인. 일반 공개 가이드 아님. 본인 워크플로우와 기존 자동화에 종속된 컴포넌트가 일부 있음.

`settings.json` 은 **단일 cross-platform** — Windows·macOS 모두 clone 한 그대로 동작 (OS별 복사 단계 없음). statusline·notify 는 `node ~/.claude/...` 형태로 통일했고 (`~` 는 Git Bash·sh 양쪽에서 홈으로 확장), OS 분기는 호출되는 스크립트 내부에서 처리 (`scripts/notify-hook.js` 의 `process.platform`). Windows 의 toast·flash 만 `scripts/notify.ps1` / `notify-hook.ps1` 로 위임.

---

## Prerequisites

- **Node.js** (LTS 권장) — `statusline.js`, `subagent-statusline.js`, `codex-quota-refresh.js` 가 Node 로 실행. `node --version` 으로 확인.
- **Claude Code** 설치 — `~/.claude/` 위치를 자동으로 읽음. 설치 후 한 번이라도 실행하여 디렉토리 생성.
- **Git** + **Git Bash** (Windows) — Claude Code 가 statusLine·hook command 를 Windows 에서 Git Bash 로 실행. `~` 확장에 필요 (Git Bash·sh 는 `~` 를 홈으로 확장; `$HOME` 은 PowerShell fallback 시 깨질 수 있어 `~` 사용). Git Bash 가 없으면 PowerShell fallback 인데 이때 `~` 확장이 보장되지 않으므로 Windows 는 Git Bash 설치 필수.
- **(선택) Codex CLI** — statusline 의 Codex quota 표시용. 없으면 해당 부분만 빠지고 나머지는 정상 동작 (silent fail).
- **(선택, Windows) PowerShell ExecutionPolicy** — Windows notify 는 `notify-hook.js` 가 `powershell.exe` 로 `notify-hook.ps1`(toast/flash) 를 spawn 하므로 `Restricted` 면 실행 안 됨. 아래 Install 참고. (macOS 는 PowerShell 불필요.)

---

## Install

### A. 새 Windows 머신 — `~/.claude/` 가 없거나 비어있을 때

```powershell
# 1. clone (USERPROFILE 위치로)
cd $env:USERPROFILE
git clone <this-repo-url> .claude

# 2. (필요 시) PowerShell ExecutionPolicy
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 3. Pre-commit / pre-push 가드 설치 (settings.json 의 secret leak 차단)
cd $env:USERPROFILE\.claude
.\scripts\install-hooks.ps1

# 4. (선택) PowerShell `gwl` 명령 설치 — worktree list 단축키 (수동 1회 실행)
#    과거 SessionStart 자동등록은 무서명 원격 스크립트 자동 실행 위험으로 제거됨 (아래 install-gwl.ps1 절 참조).
.\scripts\install-gwl.ps1

# 5. Claude Code 재시작
```

`settings.json` 은 tracked — clone 한 그대로 동작 (별도 복사 단계 없음).

### B. 이미 `~/.claude/` 가 있는 머신 — 기존 데이터 보존

`git clone` 은 디렉토리가 비어있어야 동작. 기존 디렉토리에 덮어쓰려면:

```powershell
cd $env:USERPROFILE\.claude

# 1) 백업 디렉토리 명시 생성
New-Item -ItemType Directory -Path ..\claude-backup -Force | Out-Null

# 2) 개인 데이터 백업 (없는 파일은 SilentlyContinue 로 무시)
Copy-Item -Recurse -Force `
  settings.json, settings.local.json, .credentials.json `
  -Destination ..\claude-backup\ -ErrorAction SilentlyContinue

# 3) git 초기화 + fetch
git init
git remote add origin <this-repo-url>
git fetch origin

# 4) `-f` 없이 checkout — repo 와 동명의 untracked 파일이 있으면 git 이 멈춤.
#    settings.json 도 이제 tracked 라 충돌하면 멈춤 — 백업한 값에서 머신별 부분은
#    settings.local.json 으로 옮길지, settings.json 을 덮어쓸지 본인이 판단.
git checkout origin/main -b main

# 5) hooks 설치
.\scripts\install-hooks.ps1
```

`.gitignore` 가 화이트리스트 방식이라 `.credentials.json`, `settings.local.json`, `history.jsonl`, `projects/`, `sessions/`, `cache/` 등 기존 개인 데이터는 git 이 건드리지 않음.

### C. 머신별 / 민감 정보 — `settings.local.json` 으로

`settings.json` 은 tracked → repo 의 base 설정. 머신별 차이나 민감 정보는 `~/.claude/settings.local.json` (gitignored) 에 둠. Claude Code 가 자동으로 deep merge 하고 `.local` 이 우선.

예시:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm test:*)",
      "Bash(git log:*)"
    ]
  },
  "env": {
    "ANTHROPIC_LOG": "warn"
  }
}
```

**들어가야 하는 항목**:
- 머신별 `permissions.allow` (cwd 절대경로 박힌 것 등)
- 머신별 hook
- 개발 시 임시 env var
- (참고) MCP 서버는 `settings.local.json` 이 아니라 `~/.claude.json` 에 자동 저장됨. `claude mcp add --scope user` 사용.

**경고 — Issue [#19487](https://github.com/anthropics/claude-code/issues/19487)**: project-level `.claude/settings.local.json` 이 존재하면 user-level `~/.claude/settings.local.json` 전체가 무시됨 (closed as not planned). project 별 local 사용 시 user-level 도 사용하면 충돌.

### D. Pre-commit / Pre-push 가드

`scripts/pre-commit-check.ps1` 가 staged/HEAD `settings.json` + staged `plans/*.md`(tracked §10) 를 검사해서 다음을 차단:
- 금지 키(settings.json): `mcpServers`, `apiKeyHelper`, `awsCredentialExport`, `awsAuthRefresh`
- 토큰/시크릿 패턴(settings.json·plans): Anthropic / OpenAI / GitHub / GitLab / AWS / GCP / Slack / JWT / PEM / DB URL creds / Bearer / 따옴표 시크릿 대입

설치 한 번:
```powershell
.\scripts\install-hooks.ps1
```

`.git/hooks/` 는 머신별 → clone 후 매번 실행 필요.

`--no-verify` 우회 가능 — 본인 규율 의존.

---

## Install (macOS)

macOS 는 PowerShell 대신 `bash` + `osascript` (알림) + `afplay` (사운드) 사용. 추가 의존성 없음 (system built-in).

### A. 새 macOS 머신 — `~/.claude/` 가 없거나 비어있을 때

```bash
# 1. clone — settings.json 이 cross-platform 이라 그대로 동작 (OS별 복사 불필요)
cd ~
git clone <this-repo-url> .claude

# 2. (optional) pre-commit / pre-push 가드 설치
cd ~/.claude
./scripts/install-hooks.sh

# 3. (optional) `gwl` 셸 단축키 설치 — worktree list (수동 1회). 상세: 아래 gwl.zsh 절.
./scripts/install-gwl.zsh

# 4. Claude Code 재시작
```

### B. 이미 `~/.claude/` 가 있는 macOS 머신 — 기존 데이터 보존

```bash
cd ~/.claude

# 1) 개인 데이터 백업
mkdir -p ../claude-backup
cp -R settings.json settings.local.json .credentials.json ../claude-backup/ 2>/dev/null

# 2) git 초기화 + fetch
git init
git remote add origin <this-repo-url>
git fetch origin

# 3) checkout — repo 와 동명의 untracked 파일이 있으면 git 이 멈춤.
git checkout origin/main -b main

# 4) hooks 설치 (settings.json 은 cross-platform 이라 OS별 적용 불필요)
./scripts/install-hooks.sh
```

### C. macOS 알림 권한

`osascript` 첫 호출 시 시스템 설정 → 알림 → 터미널 (혹은 Claude Code 실행 중인 앱) 권한 허용 요청 뜸. 허용해야 토스트 알림 표시.

사운드는 `/System/Library/Sounds/*.aiff` 에서 선택 (`Glass`, `Ping`, `Hero`, `Funk` 등). 기본값은 `notify-hook.js` 가 이벤트별로 지정 (Stop→`Glass`, Notification→`Ping`); 바꾸려면 `settings.json` hook command 에 3번째 인자로 사운드명 추가 (예: `node ~/.claude/scripts/notify-hook.js Stop Hero`). `Hero`·`Glass` 등은 macOS `.aiff` 명이고 Windows 는 `Asterisk|Beep|Exclamation|Hand|Question` 만 유효 — OS 에 안 맞는 값은 이벤트 기본값으로 자동 fallback (한 인자로 양 OS 를 못 맞추므로 OS별로 다른 사운드를 쓰려면 머신별 `settings.local.json` 이 아니라 직접 분기 필요).

### D. Pre-commit / Pre-push 가드 (macOS)

`scripts/pre-commit-check.sh` 가 Windows `.ps1` 버전과 동일한 규칙으로 staged/HEAD `settings.json` + staged `plans/*.md`(tracked §10) 를 검사. 동일하게 금지 키 + 토큰/시크릿 패턴 차단.

설치:
```bash
./scripts/install-hooks.sh
```

`.git/hooks/` 머신별이라 clone 한 프로젝트마다 매번 실행 필요.

---

## Verify

설치 후 다음으로 동작 확인:

### 1. Statusline 표시
Claude Code 실행 후 화면 하단에 한 줄이 나와야 함. claude/codex 조각의 앞 레이블은 각각 현재 모델명으로 표시됨 (claude = 세션 모델 `model.display_name`, codex = `~/.codex/config.toml` 의 기본 `model`). 예시:
```
Opus 53%(20:30) | gpt-5.4 60%(18:45) | ctx 12% | main
```

표시 안 되면 → Troubleshooting 의 "statusline 미표시".

### 2. Notify hook 동작
간단한 작업을 끝낸 뒤 응답 완료(Stop) 시 사운드 + 알림이 나와야 함 — macOS: `Glass` + 배너, Windows: `Asterisk` + toast. 입력 대기(Notification) 시엔 다른 사운드 — macOS: `Ping`, Windows: `Exclamation`.

사운드/알림이 없으면 → "hook 미실행".

### 3. Codex quota 표시 (선택)
`codex --version` 으로 Codex CLI 설치 확인 후, statusline 에 `<codex 모델명> NN%(HH:MM)` (예: `gpt-5.4 60%(18:45)`) 가 나타나야 함. 모델명은 `~/.codex/config.toml` 의 `model`, 못 읽으면 `codex` 로 폴백. 첫 표시는 캐시 채워질 때까지 최대 20초.

표시 안 되면 → "codex quota 미표시".

### 4. Subagent statusline
`Agent` 도구로 subagent 호출 시 subagent 의 statusline 에 `running | 1.2k tok | 0m 5s` 같은 한 줄이 나와야 함.

### 5. Pre-commit guard
`.\scripts\install-hooks.ps1` 실행 후 일반 `git commit` 은 무동작 (정상). 의도적으로 settings.json 에 `"mcpServers": {}` 박고 commit 시도 → `[BLOCKED]` 출력 + exit 1 이어야 함.

---

## Components

### CLAUDE.md — 전역 작업 규칙

모든 프로젝트에 자동 로드되는 사용자 지시문. Claude Code 가 `~/.claude/CLAUDE.md` 를 모든 세션에서 읽음.

13개 섹션 (0~12):
0. 응답 언어 — 한국어, 의례적 preamble 금지
1. 핵심 규칙 — 추측 금지, 코드 read 기반 답변, 근본 원인, 검증 후 "완료", 사용자 변경사항 보호, 운영 자산 자가 수정 금지
2. 컨텍스트 관리 — `/clear`, `/rewind`, subagent 위임 기준
3. 작업 흐름 — Setup → Explore → Plan → Implement → Verify → Report
4. 웹 검색 능동 사용 — 지식 컷오프 이후 정보, 라이브러리 버전별 동작 등
5. Sub-agent — 표준 순서 (plan-reviewer → 구현 → code-reviewer → simplify 체크(메인 직접))
6. 코드 규칙 — 동일 디렉토리 스타일, 타입 힌트, 임시 코드 표기
7. 테스트 (TDD) — 테스트 작성 순서, 예외 조건
8. Git / 보안 — destructive 명령 금지, 시크릿 출력 금지, 비trivial 은 worktree(`/wt`)에서
9. Claude ↔ Codex 협업 — `.claude/plans/` 핸드오프 채널, 리뷰 매트릭스
10. `.claude/plans/` 핸드오프 규약 — slug, frontmatter, 필수 6개 + 선택 섹션(Acceptance·Review Disposition·Deferred·Workflow Findings)
11. 영속 프로젝트 메모리 (LLM Wiki) — `wiki/` 누적 지식, `plans/` 와 경계 (일시적 vs 영속)
12. 피드백 메모리 — 작업 방식 교정을 `memory/`(type: feedback) + `MEMORY.md` 인덱스로 영속화해 다음 작업에 반영. 보편·중대 규칙은 이 `CLAUDE.md` 로 승격.

세션 시작 시점 자동 적용. 프로젝트별 추가 규칙은 per-repo `CLAUDE.md` 에 둘 수 있고, 글로벌 + 프로젝트 둘 다 로드됨.

### statusline.js — 메인 statusline

Claude Code 의 [Custom Status Line](https://code.claude.com/docs/en/statusline) 으로 등록되어 약 2초 주기로 stdin 의 세션 JSON 을 받아 한 줄을 출력.

표시 항목:
- **Claude 5-hour rate limit**: `claude NN%(HH:MM)` — 남은 percentage 와 reset 시각
- **Codex 5-hour rate limit**: `codex NN%(HH:MM)` — `cache/codex-quota.json` 에서 읽음, 5분 TTL, stale 시 `codex-quota-refresh.js` 백그라운드 spawn
- **Context window**: `ctx NN%` — 현재 세션의 컨텍스트 사용률
- **Git branch + worktree**: `main` 또는 `feature-x @wt:gallant-hodgkin` — 현재 cwd 기준
- **Background tasks**: `✻ 2 bg 1m30s` — Claude Code 의 background task 디렉토리 (`%TEMP%\claude\<slug>\<session>\tasks\`) 의 `.output` 파일 중 mtime 이 30초 이내인 항목 카운트

모든 부분이 try/catch 로 감싸져 있어 외부 의존(Codex CLI, git, fs) 실패 시 해당 부분만 빠지고 나머지는 정상 동작.

### subagent-statusline.js — subagent statusline

`Agent` 도구가 subagent 를 실행할 때 표시되는 한 줄. 현재 status, 누적 토큰 수, 경과 시간.

### codex-quota-refresh.js — Codex quota fetcher

`statusline.js` 가 cache stale 감지 시 detached spawn 으로 호출. `codex app-server` 의 JSON-RPC (`initialize` → `account/rateLimits/read`) 로 quota 조회 후 `cache/codex-quota.json` 에 atomic write.

- TTL: 5분
- Negative cache: 실패 시에도 `fetchedAt` 만 기록해서 매 2초마다 재spawn 방지
- Codex CLI 미설치 / 인증 안 된 머신: spawn 실패 시 negative cache, statusline 의 codex 부분만 빠짐
- Codex CLI 버전 변경으로 `account/rateLimits/read` 메소드가 사라지면 마찬가지로 빠짐 (확인된 동작 버전: codex-cli 0.128.x 시점)

### agents/ — 4개 subagent

`Agent` 도구로 호출. CLAUDE.md §5 의 표준 순서 (plan-reviewer → 구현 → code-reviewer → simplify 체크(메인 직접, dlc 13단계)) 가 기본. frontmatter `model: inherit` — 세션 모델을 상속(모델 세대 교체 시 수정 지점 0).

| 파일 | 호출 시점 | 핵심 책임 |
|---|---|---|
| `plan-reviewer.md` | Plan 단계 직후 (비사소한 모든 구현 계획) | 누락 케이스·잘못된 가정·영향 범위·rollback·근본 원인 비판적 발굴. public API / DB schema / migration / 보안 / 아키텍처 / 권한 변경 시 필수. |
| `architecture-reviewer.md` | 트리거 기반 (자동 호출 대상 아님) | 설계 결정 — 의존 방향·레이어 경계·객체 생명주기·DI/IoC·인터페이스 위치·테스트 가능 구조. public API / proto / DB schema / auth 변경, 신규 service·repository·client, DI 변경, 2개 이상 레이어 변경, 150줄 이상 diff, 또는 설계 의문 명시 시. |
| `code-reviewer.md` | 구현 직후 (코드 변경이 있었던 모든 흐름) | 버그·보안·테스트 누락·예외 처리·성능·backward compatibility·근본 원인. 통과 검토 금지, 비판적 발굴 목적. |
| `researcher.md` | 외부 사실 조사 필요 시 (어느 단계에서든) | 라이브러리 버전별 동작·마이그레이션·최신 API, 정확한 에러 메시지 매칭, 릴리스 노트·CVE·RFC, 지식 컷오프 이후 정보, 함수/플래그 실존 여부 불확실 시. |

각 agent 의 frontmatter `tools` 필드가 권한 범위를 제한 (예: researcher 는 Edit 권한 없음, code-reviewer 는 Bash 가능). agent 별 출력 형식과 호출 조건은 각 파일 본문 참고.

### skills/dlc/ — 자동 개발 사이클

`/dlc` 명시 호출 또는 비자명한 코드 변경 시 적용하는 개발 사이클 오케스트레이션. 규모 (trivial / small / medium / structural) 를 판정해 단계를 gate — 오타 1줄은 즉시 통과, structural 변경은 explore → plan → 리뷰 → TDD → 구현 → 리뷰 → simplify → 검증 전체를 돈다.
- 메인이 hub, 리뷰/검토(plan-reviewer, architecture-reviewer, code-reviewer)와 **최종 검증**(격리 runner·general-purpose, 실행만 — 메인이 명령·worktree cwd 지정)은 격리 subagent. 구현·통합·검증 판단·실패 fix·최종 판단은 메인.
- simplify 체크(13단계)는 메인이 직접 수행 — 모든 격리 spoke 는 read-only. substantive 수정 시 targeted 재검증.
- `.claude/plans/<slug>-plan.md` 가 subagent 간 단일 공유 채널 (메인만 write).
- codex 병행 검토 호출 규약은 `docs/codex-review.md` (phase 당 codex owner 1개 지정으로 중복 호출 방지, Windows/PowerShell fallback 포함).
- **evidence·라우팅 hook** (`scripts/dlc-*.js`, `settings.json` 등록, fail-open): `dlc-task-router`(UserPromptSubmit — 디버깅/render 키워드에 discipline 주입), `dlc-evidence-ledger`(PostToolUse — 변경·검증 기록 + 문서 drift dirty flag), `dlc-early-stop`(Stop — 변경 후 검증 누락 **및 문서화 표면↔README/index drift** 시 capped 1회 경고; 판정은 `dlc-doc-drift.js` 모듈). plan `# Acceptance` evidence gate 의 보조 누락방지망 — 검증 *성공* 판정은 acceptance(메인)가 단일 소스. `CLAUDE_DLC_EARLYSTOP_OFF=1`(검증)·`CLAUDE_DLC_DOCDRIFT_OFF=1`(문서) 로 각각 비활성(holdout). syntax 검사 + 단위테스트는 CI `lint.yml`.

### skills/c/ — plan 이어가기

`/c` 로 현재 worktree/repo 의 진행 중인 plan(§10)을 찾아 **남은 작업 + plan↔실제(git/코드) sync 상태**를 진단하고, 어긋나면 plan 을 보정한 뒤 `# Next` 가 명확하면 이어서 실행(멈춤 예외 5종).
- branch→plan dir 매칭(§10), 실패 시 `in_progress`/`blocked` plan 목록 제시 후 사용자 선택 (추측 자동선택 안 함).
- `plans/` 가 worktree(브랜치)별 독립이라 현재 repo + main worktree 양쪽 `plans/` 를 탐색(tracked 지만 브랜치마다 내용이 다르다).
- 확인·sync 진단·plan 보정 후 **`# Next` 가 명확하면 이어서 실행**(멈추는 예외 5종: `blocked`·plan 후보 다수·`# Next` 재구성·파괴적/외부공개 액션·`done`). 그 브랜치 PR 의 **사람** 리뷰 코멘트를 intake 해 코드 지적은 `# Next`, 작업방식 지적은 feedback memory 판정으로 넘긴다. plan 이 없으면 새로 만들지 않음 — 신규 plan 생성은 dlc 몫.

### skills/e/ — plan 마무리

`/e` 로 진행 중이던 plan(§10)을 **실제 git/코드 상태로 동기화 기록**하고 작업을 마무리. c(이어가기)의 대칭.
- **마무리 recap(CLAUDE.md §3-6)**: 최종 메시지는 **결론 요약(≤3줄) 먼저**, 마무리 선택지(정리/이어가기/종료)는 아래 worktree 정리 제안 + 다음 세션 `/c` 안내가 겸한다(별도 AskUserQuestion 을 새로 만들지 않음).
- uncommitted 변경은 작업 브랜치에 **임시(WIP) 커밋**으로 보존 — `main`/`master` 직접 커밋·push 는 안 함(§8), `.env`·key 등 위험 파일은 커밋 보류 후 확인.
- `# Progress`/`# Next`/`# Decisions`/`status`/`updated` 를 사실 기반으로 갱신 → 다음 세션이 `/c` 로 곧장 이어받음.
- done 자동 전환 안 함 (확정 완료 신호 + 사용자 확인 시만, 기본 `in_progress` 체크포인트). plan 없으면 새로 만들지 않음 — 임시 커밋 + 보고만.
- worktree 에서 작업이 `done`·clean·pushed·merged(base 통합)이고 내부에 잃을 ignored 산출물(plan·`.env`)이 없으면 **worktree 삭제도 제안** (AskUserQuestion; worktree만/+로컬브랜치/+로컬·원격브랜치/유지). 삭제 시 main 으로 빠져나간 뒤 `git worktree remove`, 원격은 `git push origin --delete`, `--force`·`branch -D`·원격 삭제는 추가 확인. merge/done 후 정리를 방치하지 않고 능동 제안하는 규약은 CLAUDE.md §8.
- **`collect-state.sh`** (헬퍼): 마무리 2단계·5단계의 읽기전용 git 신호(worktree 위치·dirty·upstream/unpushed·base merged·ignored)를 평문 `key:value` 로 1회에 수집 — 분산된 개별 git 호출의 왕복을 줄인다. read-only(판정·삭제·파괴 명령은 SKILL 메인), 각 점검 fail-safe(실패 필드 none/unknown), `unpushedStatus` 는 false 와 unknown 을 구분해 false-positive 삭제를 막는다.

### skills/wt/ — Git worktree 빠른 관리

`/wt` (목록) · `/wt <N>` (N번째 worktree 로 이동) · `/wt <기존이름>` (정확일치 worktree 로 이동) · `/wt <요청사항>` (slug 확인 후 worktree 신규 생성 → 그 안에서 `dlc` 로 작업) · `/wt ? <막연한 설명>` (질문 모드 — 구체화 후 생성) · `/wt rm <name>` (제거) 로 worktree 관리. 컨벤션:
- worktree path: `.claude/worktrees/<name>` (현재 repo 기준)
- 브랜치 이름 = worktree 이름 (1:1)
- `EnterWorktree(path: <abs>)` 로 진입 — `name` 인자 사용 금지 (Claude Code 의 `worktree-` prefix 자동 부착 회피)
- 정수·`rm`·기존 worktree 정확일치가 아닌 텍스트는 **요청사항**으로 간주 → 영문 kebab-case slug 파생 → AskUserQuestion 으로 확인 후 생성 → 요청사항 원문을 `dlc` task 로 전달 (dlc 없는 빈 worktree 단순 생성은 폐지)
- 접두 `?` (`/wt ? <막연한 설명>`)는 **질문 모드** — AskUserQuestion 으로 요구사항을 구체화한 뒤 같은 요청사항 생성 경로로 합류 (접미 `?` 는 의문형 요청과 충돌해 미사용)

### skills/wiki/ — LLM Wiki (영속 프로젝트 메모리)

`/wiki <ingest|query|lint>` 로 `wiki/`(영속 프로젝트 메모리)를 운영. ingest(raw·작업지식 → 상호링크 페이지 + index/log) · query(누적 페이지로 답 → 가치 있으면 filed) · lint(orphan·dead link·모순 점검·보고). 운영 규약 단일 소스는 `wiki/WIKI.md`. `plans/`(일시적 작업 핸드오프)와 달리 작업을 **가로질러 누적**. raw 원문은 gitignored·읽기 전용, 페이지만 tracked. dlc 연계는 CLAUDE.md §11.

### skills/improve/ — 자기개선 loop 분석 축 (구 /audit 흡수)

`/improve` 로 ① 운영 자산(skills·agents·CLAUDE.md·settings.json·MEMORY.md·wiki)의 **자산 간 참조 정합**(구 `/audit` 승계)과 ② hook 이 자동 누적한 **dlc 신호(telemetry)** 를 함께 분석해 **개선 후보를 랭킹**으로 제시. **수정은 제안만**(§1 자가수정 금지) — 승인 시 wt→dlc 별도 작업. loop 구조: 수집(hook 자동, `dlc-signal.js`) → 분석·제안(`/improve`) → 반영(승인 후 wt→dlc) → 효과 확인(다음 `/improve` 의 신호 추이).
- 기계 점검+집계 `skills/improve/improve.sh`(read-only): settings hooks↔scripts 실존 · MEMORY 인덱스↔파일 양방향 · CLAUDE.md 가 참조한 agent 실존 · SKILL frontmatter name · 죽은 스크립트 후보(require 그래프·수동유틸 화이트리스트로 오탐 차단, info 만) · wiki index↔pages 개수 · **plan-lint**(tracked plan 전수 §10 무결성) · **신호 집계**(`node scripts/dlc-signal.js summary` — failure/activity 축, session-unique 우선).
- **`improve.sh deep`**(opt-in 광역 관측, 여전히 read-only·secret 미출력): ⑧ 주입·로드 표면 크기(`wc -c` — CLAUDE.md·SKILL·agent, 토큰 압박) · ⑨ 사용량 카운트(`node scripts/usage-count.js` — transcript JSONL 파싱해 skill·subagent·codex 호출 빈도, **카운트·slug 만**, 원문·파일명·경로·args 미출력) · ⑩ MCP 서버 인벤토리(`~/.claude.json` **이름만**, 값·env·secret 미출력). 판단·제안 경로는 기본 4단계와 동일(측정→제안, 수정 금지).
- 의미 점검(LLM): 문서 간 모순 · 중복 trigger · 죽은 규칙 + wiki `workflow-failures` 표·MEMORY 인덱스·plan `# Workflow Findings` 대조.
- **역할 경계**: README↔surface drift 는 `dlc-doc-drift` hook, wiki 내부 무결성은 `/wiki lint` 영역 — improve 는 재판정하지 않고 신호의 **사후 집계**만(중복 회피).

### scripts/

settings.json 에 등록돼 후크가 호출하는 진입점은 notify(`notify-hook.js`), worktree 가드(`guard-worktree-edit.js`), dlc evidence 3종(`dlc-task-router.js` / `dlc-evidence-ledger.js` / `dlc-early-stop.js`). 모두 fail-open (실패해도 throw 안 함). 나머지(`bootstrap/`, `*.ps1`, `install-*`, `prompt-gwl.py`)는 위 진입점이 위임하거나 수동/프로젝트별로 쓰는 보조 스크립트.

#### `bootstrap/` (setup.sh · setup.ps1 · README.md)
새 머신에서 한 번 실행해 이 환경(도구 + 설정 + 선택적 memory)을 재현하는 **idempotent** 부트스트랩. macOS `setup.sh`(zsh/launchd, 비-conda), Windows `setup.ps1`(레지스트리/scheduled task — ⚠️ 실행 미검증). 도구(node/uv/headroom/codegraph/rtk)·MCP 등록·headroom proxy(`--mode token`)·codegraph init·셸 env 를 각 단계 guard 로 `[SKIP]`. rtk 는 headroom 번들 심링크+`rtk init` 서명(hook 직접편집 금지). `--dry-run`/`--memory-from` 지원. 상세·전제·한계는 `scripts/bootstrap/README.md`.

#### `notify-hook.js`
Cross-platform notify 진입점 (Node). stdin 의 Claude Code JSON 에서 `message` · `cwd` 추출 (title = cwd basename). **macOS**: `afplay` 시스템 사운드 + `osascript` 배너 (인라인). **Windows**: 원본 stdin 을 그대로 넘기며 `powershell.exe -File notify-hook.ps1` spawn. **Linux**: best-effort `notify-send`. 모든 동작 best-effort — 실패해도 throw 안 하고 stdin 1초 타임아웃으로 세션 안 멈춤. 사운드 기본값은 이벤트별 (Stop→Glass/Asterisk, Notification→Ping/Exclamation); command 3번째 인자로 override.

#### `notify.ps1`
Toast 알림 + 시스템 사운드 + 윈도우 flash. 우선순위: WinRT ToastNotification → System.Windows.Forms NotifyIcon. WinRT toast 는 Windows PowerShell 5.1 전용 (PS7 은 WinRT 어셈블리 미포함) — hook 이 `powershell.exe` 로 5.1 고정 실행. toast 표시 전 `HKCU\Software\Classes\AppUserModelId\Claude.Code` 에 AppID 자가 등록 (미등록 AppID 는 Windows 가 toast 를 조용히 버림).

#### `notify-hook.ps1`
Windows 에서 `notify-hook.js` 가 spawn (`Stop` / `Notification` 이벤트). stdin 으로 넘어온 Claude Code JSON 에서 `cwd`, `session_id` 추출, 부모 프로세스 트리에서 WindowsTerminal 의 tab 제목 추출 → `notify.ps1` 에 title/message 전달. (macOS·Linux 에선 호출되지 않음.)

debug log: `$env:CLAUDE_NOTIFY_DEBUG = '1'` 설정 시에만 `%TEMP%\claude-notify-debug.json` 에 매 호출마다 덮어씀. cwd, sessionId 포함되므로 디버깅 후 환경변수 해제 권장. 기본값은 off (privacy footprint 최소화).

#### `guard-worktree-edit.js`
PreToolUse(`Edit|Write|NotebookEdit`) 가드. 두 경로:
- **worktree 세션**(cwd 가 `.../.claude/worktrees/<name>/` 하위): **그 worktree 밖 main repo 소스**를 편집하려는 호출을 `deny` 로 차단 — 작업 격리가 새는 실수 케이스 방지. 현재 worktree 안, repo 의 `.claude/` 메타(plans·memory·settings 등), repo 밖(홈 등) 경로는 allow.
- **비-worktree 세션**: cwd repo 가 `main`/`master` 브랜치이고 편집 대상이 **그 repo 의 추적 파일**이면 `ask`(승인 요구) + `main-edit-ask` 신호 emit — main 직접 편집 대신 worktree/브랜치를 쓰는 규약(CLAUDE.md §8)을 기계화. branch·tracked 판정 모두 cwd repo 기준(fp 가 cwd repo 밖이면 allow). 전 repo 전역 적용, `CLAUDE_MAIN_EDIT_GUARD_OFF=1` 로 전역 해제. git 판정 실패(미설치·detached·repo 밖·timeout)는 모두 fail-open(allow).

jq 미설치 환경이라 node 로 stdin JSON 파싱. 파싱 실패 시 exit 0 (fail-open).

#### `dlc-task-router.js` · `dlc-evidence-ledger.js` · `dlc-early-stop.js` (+ `dlc-ledger.js` · `dlc-doc-drift.js` · `dlc-signal.js`)
dlc(`skills/dlc/`)의 evidence gate 를 보조하는 누락방지망. 모두 fail-open — plan `# Acceptance` evidence gate(메인 판정)가 단일 소스고, 이 hook 들은 capped 보조일 뿐.
- **`dlc-task-router.js`** (UserPromptSubmit) — 디버깅/render 키워드 감지 시 조사·검증 discipline(취향·시각 산출물엔 **프로토타입-우선** 제안 포함)을 주입하고 세션 evidence 장부를 리셋.
- **`dlc-evidence-ledger.js`** (PostToolUse `Edit|Write|NotebookEdit|Bash`) — 코드 변경·검증 명령 실행을 세션 장부에 기록 + 문서화 표면↔README/index dirty flag 갱신(`dlc-doc-drift` 판정).
- **`dlc-early-stop.js`** (Stop) — 종료 시 두 누락을 capped 1회 경고로 합쳐 출력: ① 변경했는데 검증 기록 없음(`CLAUDE_DLC_EARLYSTOP_OFF=1`), ② 문서화 표면(`scripts/`·`agents/`·`skills/**/SKILL.md`·`settings.json`·`CLAUDE.md`, `wiki/pages/`)을 바꿨는데 `README.md`/`wiki/index.md` 동기화 없음(`CLAUDE_DLC_DOCDRIFT_OFF=1`). 한 hook 에서 합산 출력 — 별도 hook 이면 동시 block 시 한쪽 카운터가 미노출 소모돼 다시 안 잡히는 false negative.
- **`dlc-doc-drift.js`** — 문서 drift 판정 **순수 모듈**(hook 아님). `resolveRoot`(`.claude`/worktree 한정, 타 repo no-op)·`classify`(root 기준 정확 경로)·`applyChange`(dirty 전이)·`evaluate`. early-stop·evidence-ledger 가 require. 단위테스트 `dlc-doc-drift.test.js`.
- **`dlc-ledger.js`** — 위 hook 들이 공유하는 per-session 임시 장부(`%TEMP%/dlc-evidence-<sid>.json`) read/write/reset 모듈. `DEFAULT` 스키마 단일 소스(`changed/verified/blocks` + `readmeDirty/indexDirty/docBlocks`). hook 으로 직접 등록되진 않음.
- **`dlc-signal.js`** — 자기개선 loop 의 **신호 수집 모듈**(hook 아님, 위 dlc hook 3종 + `guard-worktree-edit.js` 가 require). hook 판정 발동(early-stop 경고·doc-drift·guard deny·guard main-edit ask·router 주입·plan `status: blocked` 전이·disposition 기록)을 `~/.claude/telemetry/dlc-signals.jsonl` 에 append-only 누적 — `/improve` 가 집계 소비. kind→axis(failure/activity) 단일 소스 `KINDS`, plan 신호는 substring 이 아니라 **상태 전이**로 판정(`detectPlanSignal` 순수 함수 — disposition 은 Review Disposition 섹션/placeholder 컨텍스트에서만). payload 는 kind·ts·session_id·cwd·경로만(`~` 축약, 프롬프트 원문·시크릿 없음 — 단 경로 메타데이터는 로컬 gitignored 파일에 남음, 전송·커밋 안 됨). fail-open + env 채널: `CLAUDE_DLC_SIGNAL_DIR`(redirect — 테스트 격리), `CLAUDE_DLC_SIGNAL_OFF=1`(무력화), `CLAUDE_DLC_SIGNAL_MAX_BYTES`(회전 임계, 기본 5MB `.1` 단일 회전 best-effort; summary 는 `.1` 도 함께 읽음). CLI `node scripts/dlc-signal.js summary`. 단위+통합테스트 `dlc-signal.test.js`.
- **`session-brief.js`** (SessionStart hook — 위 hooks.SessionStart 참조) — 세션 시작 리마인더. K 머지 대기: `~/.claude` 의 origin/main 대비 ahead 로컬 브랜치(`for-each-ref`+`rev-list`, main/master 제외·oldest 순 cap5, fetch 안 함·git stderr 억제). L /improve 권장: `dlc-signal` 의 jsonl 을 직접 파싱해 마커(`last-improve` touch) 이후 failure 축 **unique 세션**(cross-kind dedup·회전분 합산) 이 임계(`CLAUDE_BRIEF_IMPROVE_MIN`, 기본5) 이상이면 nudge. 전부 fail-open. 테스트 `session-brief.test.js`.
- **`usage-count.js`** (`improve.sh deep` ⑩ 가 호출, hook 아님) — transcript JSONL 을 파싱해 skill/subagent/codex tool_use 레코드만 집계. 프라이버시: 카운트+고정 slug 만 출력, 파일명·경로·원문·args 미출력(raw grep 대신 스키마 파싱). `CLAUDE_TRANSCRIPT_DIR` redirect(테스트). 테스트 `usage-count.test.js`.
- **`plan-lint.js`** — §10 plan 참조 무결성 **순수 판정 + CLI**(hook 아님). `lintPlan(text)`→위반 배열: frontmatter 필수키 non-empty · `status` 값 · 6 H1 섹션 · **끊긴 Acceptance 참조**(본문의 "Acceptance N/①-⑳" ↔ `# Acceptance` 항목 수; frontmatter·헤더·# Acceptance 섹션·백틱/따옴표 인용은 스캔 제외해 자기참조 오탐 차단). 의미 판정(title↔Goal 정합)은 LLM 몫. 강제 3지점: CI `lint.yml`(그 PR 변경 plan 만·`continue-on-error` 비차단) · `/c` 2단계(채택 plan) · `/e` 3단계(active plan, write 후) · `improve.sh` 8(전 tracked plan). `CLAUDE_PLAN_LINT_OFF=1` 로 CLI no-op. 테스트 `plan-lint.test.js`.

syntax 검사 + `dlc-doc-drift.test.js`·`dlc-signal.test.js`·`dlc-evidence-ledger.test.js`·`guard-worktree-edit.test.js`·`plan-lint.test.js` 단위테스트는 CI `lint.yml`.

#### `pre-commit-check.ps1`
staged (`pre-commit` 모드) 또는 HEAD (`pre-push` 모드) 의 `settings.json` 을 검사. 금지 키 (`mcpServers`, `apiKeyHelper`, `awsCredentialExport`, `awsAuthRefresh`) 또는 토큰 패턴 (Anthropic/OpenAI/GitHub/GitLab/AWS/GCP/Slack/JWT/PEM) 검출 시 exit 1.

`.git/hooks/` 에 직접 두지 않고 별도 파일 → repo 에 tracked. `install-hooks.ps1` 가 `.git/hooks/{pre-commit,pre-push}` sh wrapper 를 생성해서 이 스크립트로 위임.

#### `install-hooks.ps1` / `install-hooks.sh`
`.git/hooks/` 에 세 hook 의 sh wrapper 생성 (`.ps1`=Windows, `.sh`=Unix, 동일 로직):
- `pre-commit`·`pre-push` — settings.json 가드(`pre-commit-check`)로 위임.
- **`post-checkout`** (main-autopull) — main/master 로 **branch 체크아웃 시** `git pull --ff-only origin <branch>` 로 origin 최신화. `git checkout` 을 절대 막지 않음(항상 exit 0). ff 실패는 "main 에 로컬 커밋 있음" 신호라 자동 rebase 하지 않고 경고만. **skip/무해 조건**: dirty·origin 없음·rebase/merge/bisect 중·default 브랜치가 main/master 아님. **hang 방지**: `GIT_TERMINAL_PROMPT=0`(프롬프트)+SSH `ConnectTimeout=10`+HTTP low-speed+백그라운드 pull 을 ~20s 폴링 워치독으로 kill (macOS 는 `timeout(1)` 부재라 자체 워치독). **비활성**: `export CLAUDE_AUTOPULL_OFF=1`. **제거**(rollback): `rm .git/hooks/post-checkout`(hook 은 비추적·머신별이라 스크립트 revert 로 안 지워짐).

UTF-8 (no BOM) + LF endings — Git Bash 가 인식. idempotent — 재실행 시 기존 pre-commit/pre-push 는 **바이트 동일 유지**하고 post-checkout 만 추가. 새 머신 setup 시(=clone 한 repo 마다) 1회 실행. SessionStart 훅(세션 **시작** 시점 pull)과 역할 분리 — post-checkout 은 **체크아웃** 시점을 커버.

#### `prompt-gwl.py`
프롬프트에 정확히 `gwl` 만 입력하면 가로채서 `git worktree list` 를 현재 위치 `→` 마커와 함께 출력하는 UserPromptSubmit 훅 (모델 왕복 없음). `--porcelain` 기반이라 공백 포함 경로·bare·detached worktree 도 정확히 파싱. 글로벌 `settings.json` 엔 미등록 — 프로젝트별 `.claude/settings.json` 에 hook 으로 등록해 사용.

#### `gwl.ps1` (Windows / PowerShell)
`prompt-gwl.py` 와 같은 목적의 PowerShell 단축 함수 — `git worktree list` 를 출력하되 현재 디렉토리를 포함하는 worktree 앞에 `→` 마커. `$PROFILE` 에서 dot-source 해 명령처럼 사용 (모델 왕복 없음). 임의 프로젝트용으로 `--porcelain` 을 쓰는 `prompt-gwl.py` 와 달리, 개인 worktree(`.claude/worktrees/<name>` 규약상 경로 무공백) 전용이라 단순 `git worktree list` split. `→` 가 Windows PowerShell 5.1(BOM 없는 UTF-8 을 ANSI 로 해석)에서 깨지지 않도록 **UTF-8 BOM** 으로 저장 (PS 7 은 양쪽 모두 읽음).

#### `install-gwl.ps1` (Windows / PowerShell)
`$PROFILE` (CurrentUserCurrentHost) 에 `. "$HOME/.claude/scripts/gwl.ps1"` 한 줄을 marker 블록(begin/end)으로 멱등 추가 — 두 marker 다 있으면 skip, 한쪽만 있으면(손상) 에러, 없으면 추가. 기존 inline `function gwl` 발견 시 경고. dot-source 대상은 항상 `~/.claude/scripts/gwl.ps1`(문서상 clone 위치)이라 레포가 다른 곳이면 경고만 하고 그대로 진행. 이후 `git pull` 로 `gwl.ps1` 갱신 시 profile 수정 없이 반영. **수동 1회 실행** 필요 — `~/.claude` 에서 `& ./scripts/install-gwl.ps1` (또는 `pwsh -File scripts/install-gwl.ps1`). 과거 `hooks.SessionStart` 가 자동 실행했으나, 무서명 원격 스크립트를 매 세션 자동 실행하는 위험 때문에 제거했다.

#### `gwl.zsh` (macOS / zsh)
`gwl.ps1` 의 zsh 대응물 — `git worktree list` 를 출력하되 현재 디렉토리를 포함하는 worktree 앞에 `→` 마커. `~/.zshrc` 에서 source 해 명령처럼 쓴다 (모델 왕복 없음). 개인 worktree(`.claude/worktrees/<name>`, 경로 무공백) 전용이라 단순 split. 현재 worktree 판정은 `git rev-parse --show-toplevel` **정확일치** — 이 레포는 worktree 가 main 하위에 nest 되어(main path 가 worktree path 의 prefix) prefix 방식이면 main 행에도 `→` 가 붙기 때문(`gwl.ps1`·`prompt-gwl.py` 의 잠재 이슈를 zsh 판에서 정본화). macOS/zsh 는 UTF-8 기본이라 BOM 불필요. 인자는 받지 않는다 (`--porcelain` 등으로 split 이 깨지는 것 방지).

#### `install-gwl.zsh` (macOS / zsh)
`~/.zshrc` 에 `source "$HOME/.claude/scripts/gwl.zsh"` 한 줄을 marker 블록으로 멱등 추가 — `install-gwl.ps1` 과 같은 규약(두 marker 다 있으면 skip, 한쪽만이면 에러, 없으면 추가; 기존 inline `gwl` 발견 시 경고; 파일 끝 개행 보장; `~/.zshrc` 없으면 생성). source 대상은 항상 `~/.claude/scripts/gwl.zsh`(문서상 clone 위치)라 `git pull` 갱신이 profile 수정 없이 반영된다. **수동 1회** 실행: `~/.claude` 에서 `./scripts/install-gwl.zsh`. `~/.zshrc` 는 인터랙티브 셸이 source 하므로 Claude Code `!`/Bash 스냅샷에도 흘러가나 **다음 세션/새 터미널부터** 유효.

### settings.json — 살아있는 설정 (tracked)

머신 간 sync 의 source of truth. 핵심 키:
- `theme`, `preferredNotifChannel` — Claude Code UI 설정
- `permissions.deny` — `git push origin main/master` 직접 푸시 차단
- `permissions.ask` — 일반 `git push` 는 확인 후 실행
- `model` — 세션 기본 모델 (`opus[1m]` — Opus, 1M context)
- `statusLine`, `subagentStatusLine` — statusline 스크립트 등록 (`node ~/.claude/statusline.js`)
- `env.CLAUDE_CODE_EFFORT_LEVEL` — Opus effort level (`xhigh`). docs 명시 값: `low|medium|high|xhigh|max`. `/effort` 나 `effortLevel` 키로는 세션 한정이지만 **env 변수로 설정할 때만 영구 적용**되므로 이 키로 둔다. env 가 `effortLevel` 키를 override.
- `hooks.SessionStart` — 2개. (1) `~/.claude` 가 `main` 브랜치 + 클린 트리이면 `git pull --ff-only origin main` 으로 origin/main 자동 동기화 (ff-only·가드 실패 무음, async; `~` 확장 위해 sh/Git Bash 필요). pull 로 HEAD 가 바뀌면 한 줄 알림(`~/.claude updated …`) 출력. pull 내용은 **다음 세션부터** 적용. dirty/분기/다른 브랜치면 가드에 걸려 skip. **이 pull 훅은 세션 시작 시점만 커버 — 체크아웃 시점은 install-hooks 의 `post-checkout` git hook, 세션 중 main 복귀 시점은 `/e` 6단계가 각각 보완(main-autopull).** (2) `session-brief.js`(동기·timeout10) — 세션 시작 브리프 1~2줄: **머지 대기**(origin/main 대비 ahead 인 미머지 로컬 브랜치, oldest 순 cap5) + **`/improve` 권장**(마커 이후 failure 신호 임계 세션 이상). 전부 fail-open 무음, `CLAUDE_SESSION_BRIEF_OFF=1`(+ `CLAUDE_BRIEF_MERGE_OFF`·`CLAUDE_BRIEF_IMPROVE_OFF`)로 해제. (과거엔 `install-gwl.ps1` 을 자동 실행하는 command 가 있었으나 무서명 원격 스크립트 자동 실행 위험 때문에 제거 — gwl 등록은 위 `install-gwl.ps1` 수동 1회 실행으로.)
- `hooks.PreToolUse` — `Edit|Write|NotebookEdit` 에 `guard-worktree-edit.js`(worktree 밖 main repo 편집 차단 + 비-worktree 세션의 main/master 추적파일 직접 편집 `ask`, `CLAUDE_MAIN_EDIT_GUARD_OFF=1` 로 해제), `Bash` 에 macOS 한정 `rtk-rewrite.sh`(RTK 명령 재작성, darwin 아니면 no-op)
- `hooks.UserPromptSubmit` — `dlc-task-router.js` (디버깅/render discipline 주입 + evidence 장부 리셋)
- `hooks.PostToolUse` — `Edit|Write|NotebookEdit|Bash` 에 `dlc-evidence-ledger.js` (변경·검증 명령 기록)
- `hooks.Stop` — `dlc-early-stop.js`(검증 누락 + 문서 drift capped 경고) + `notify-hook.js Stop`(알림) 2개
- `hooks.Notification` — 입력 대기 시 `notify-hook.js Notification` (cross-platform 알림)
- `enabledPlugins`, `extraKnownMarketplaces` — Pyright LSP plugin + OpenAI Codex marketplace
- `model`, `theme`, `skipWorkflowUsageWarning`, `preferredNotifChannel` — Claude Code UI / 세션 기본값

Path 표기 (cross-platform):
- 모든 command 가 `node ~/.claude/...` 형태. `~` 는 Claude Code 가 command 를 실행하는 셸(macOS·Linux = `sh -c`, Windows = Git Bash)에서 홈으로 확장된다. `$HOME` 은 Windows PowerShell fallback 에서 깨질 수 있어 쓰지 않음 → **Windows 는 Git Bash 필수**.
- OS 분기는 settings 가 아니라 호출되는 스크립트 내부에서 처리 (`notify-hook.js` 의 `process.platform`). Claude Code 는 settings 레벨 OS 조건부를 지원하지 않는다.
- `node` + 스크립트 경로 패턴은 모든 OS 에서 동작 (node 가 PATH 에 있어야).

**Claude Code 가 자동 수정하는 키 (push 전 `git diff` 검토 권장)**:
- `/config` (theme, verbose 등) → user-level settings.json (v2.1.119+)
- `/statusline` → settings.json
- `/effort` → settings.json (effortLevel 키 추가)
- `/plugin` enable/disable → enabledPlugins
- "Always allow" Bash prompt → project `.claude/settings.local.json` (이 repo 와 무관)

머신별 / 민감 정보는 [`settings.local.json`](#c-머신별--민감-정보--settingslocaljson-으로) 으로.

---

## What's NOT in this repo

`.gitignore` 의 화이트리스트 방식 (`/*` + `!/...`) + belt-and-suspenders 차단으로 다음은 의도적 제외:

| 항목 | 사유 |
|---|---|
| `.credentials.json` | Claude / Anthropic OAuth 토큰. 절대 commit 금지. |
| `~/.claude.json` | MCP server config + OAuth session. `claude mcp add --scope user` 가 여기 박음. 절대 commit 금지. `~/.claude/` 외부 (홈 디렉토리 직속) 라 본 repo 와 별도 파일. |
| `settings.local.json` | 머신별 allow list, 머신별 hook, 임시 env. Claude Code 가 자동 deep merge 하며 `.local` 우선. |
| `history.jsonl` | 명령 입력 히스토리. 개인 데이터. |
| `projects/`, `sessions/`, `tasks/`, `cache/`, `paste-cache/`, `shell-snapshots/`, `file-history/`, `backups/`, `plugins/`, `plans/` | runtime cache, 세션 로그, 붙여넣기 캐시, plan 핸드오프 등 머신·세션별 데이터 |
| `mcp-needs-auth-cache.json` | MCP 인증 캐시 |
| `*.bak`, `*.bak.*`, `tmp_*` | 임시 백업 |
| `CLAUDE.md.bak.*` | CLAUDE.md 이전 버전 백업 |

---

## Customization

### 사용자명이 다른 머신
settings.json 의 statusLine / hook command 모두 `~` 로 추상화돼 있어 사용자명 무관 동작. `~` 는 실행 셸(macOS·Linux = `sh`, Windows = Git Bash)이 홈 디렉토리로 확장.

### Codex CLI 없는 머신
설치 안 해도 statusline 의 `codex NN%(HH:MM)` 부분만 빠지고 나머지는 정상. 설치하려면 `npm install -g @openai/codex` 후 `codex login`.

### PowerShell ExecutionPolicy 가 `Restricted` 인 머신
후크의 `.ps1` 스크립트 실행 불가. 일회성 처리:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Notify 알림 끄기
`settings.json` 의 `hooks.Stop` / `hooks.Notification` 블록을 직접 제거 후 commit. (hooks 는 스코프 간 **누적 실행** 이라 `settings.local.json` 으론 끄지 못하고 추가만 됨 — override 불가.) `preferredNotifChannel` 도 `"notifications_disabled"` 로 변경 가능.

### 자동 동기화(auto-pull) 끄기
`settings.json` 의 `hooks.SessionStart` 블록(`git pull --ff-only`)을 제거 후 commit 하면 전 머신에서 꺼짐. hooks 는 스코프 간 누적 실행이라 `settings.local.json` 으로 특정 머신만 끄지는 못함 — 한 머신만 끄려면 그 머신에서 블록을 임시로 비우거나(트리 drift 발생) `disableAllHooks` 사용(단 notify·statusline 도 같이 꺼짐).

### Permission prompt 자주 뜨는 경우
Claude Code 내장 skill `/fewer-permission-prompts` 호출 시 최근 transcript 의 read-only Bash·MCP 호출을 분석해 `permissions.allow` 에 자동 추가. 머신별 차이는 `settings.local.json` 에 두는 게 안전.

### Commit 전 식별자 leak 점검
pre-commit guard 가 settings.json 의 토큰 패턴은 잡지만, 다른 파일의 머신 식별자 (username·내부 repo 이름·이메일 등) 는 본인이 확인. CI 가 자동 처리하지 않는 이유는 패턴 자체가 leak 표면이 될 수 있어서.
```powershell
git diff --staged | Select-String -Pattern '본인_username|내부_repo_이름|이메일도메인'
```
또는 Git Bash:
```bash
git diff --staged | grep -iE '본인_username|내부_repo_이름|이메일도메인'
```
패턴은 본인 환경의 식별자로 채우고, 외부에 두지 말 것 (memo / 1Password 등 머신 외부 저장소 권장).

---

## Rollback / Incident Response

### Settings 변경 되돌리기
가벼운 변경 — `git revert <commit>`. 다른 머신은 다음 pull 시 반영. 머신마다 settings.json 자동 수정 (Claude Code 가 박는 변경) 이 있으면 머지 충돌 가능 — 본인이 어느 쪽 살릴지 결정.

### Secret 실수로 commit/push 한 경우

**즉시 수행 (시간 순)**:
1. **token 회수** — 노출된 키/토큰 즉시 revoke + rotate (Anthropic console, GitHub settings, AWS IAM 등). 이게 가장 시급.
2. **GitHub secret scanning alert 확인** — repo Settings > Security > Secret scanning. 자동 detect 됐을 가능성.
3. **history rewrite** — `git filter-repo` 로 secret 들어간 commit 제거 후 force push.
   ```bash
   pip install git-filter-repo
   # replace.txt 형식: <literal>==><replacement>   (==> 없으면 git-filter-repo 거부)
   echo "leaked-secret-string==>***REMOVED***" > replace.txt
   git filter-repo --replace-text replace.txt
   git push --force-with-lease origin main
   ```
4. **다른 머신 pull 상태 정리** — 이미 pull 한 머신은 `git fetch && git reset --hard origin/main`. 노출된 secret 이 다른 머신 local 에도 있을 수 있음 — `git log` / `git stash list` / `git reflog` 도 점검.
5. **remote cache 점검** — PR diff, GitHub Actions log, CI artifact, 검색엔진 cache 도 표면. 가능하면 PR delete + admin contact.

참고: `permissions.deny` 는 Claude Code (assistant) 가 명령 실행할 때만 차단. 사용자가 직접 터미널에서 `git push --force-with-lease` 실행하는 것은 영향 없음 — incident response 는 본인이 직접 터미널에서 진행.

---

## Roadmap

### OS 지원 현황 (Windows / macOS / Linux)
`settings.json` 은 단일 cross-platform — 모든 command 가 `node ~/.claude/...` 이고 OS 분기는 `notify-hook.js` 의 `process.platform` 에서. 컴포넌트별:
- `statusline.js`, `subagent-statusline.js`, `codex-quota-refresh.js`, `notify-hook.js`, `guard-worktree-edit.js`, `dlc-*.js` — node 기반(`os.homedir()` / `process.platform` / `os.tmpdir()`), **cross-platform**.
- `CLAUDE.md`, `agents/*.md`, `skills/*/SKILL.md` — 텍스트 가이드, **OS 무관**.
- `scripts/notify.ps1`, `notify-hook.ps1` — Windows 전용 (WinRT toast / flash). macOS·Linux 는 `notify-hook.js` 가 직접 처리하므로 미사용.
- `scripts/pre-commit-check.{sh,ps1}`, `install-hooks.{sh,ps1}` — OS별 가드/설치 스크립트 (양쪽 제공).
- **남은 검증**: Windows notify 분기와 statusLine `~` 확장은 Windows 실기 확인 필요. Linux notify 는 `notify-send` best-effort 만.

---

## Layout

```
~/.claude/
├── CLAUDE.md                       # 전역 작업 규칙 (자동 로드)
├── README.md                       # 본 파일
├── .gitignore                      # whitelist 방식 + belt-and-suspenders
├── settings.json                   # 살아있는 설정 (tracked)
├── settings.local.json             # 머신별 / 민감 정보 (gitignored)
├── statusline.js                   # 메인 statusline
├── subagent-statusline.js          # subagent statusline
├── codex-quota-refresh.js          # Codex quota fetcher
├── agents/
│   ├── architecture-reviewer.md
│   ├── code-reviewer.md
│   ├── plan-reviewer.md
│   └── researcher.md
├── docs/
│   ├── codex-review.md             # codex 병행 검토 공유 규약
│   └── headroom-proxy-session-lifecycle.md  # headroom proxy 세션 수명·셋업 메모 (macOS)
├── skills/
│   ├── dlc/
│   │   └── SKILL.md                # /dlc — 자동 개발 사이클
│   ├── c/
│   │   └── SKILL.md                # /c — plan 이어가기
│   ├── e/
│   │   ├── SKILL.md                # /e — plan 마무리 (임시 커밋 + 동기화)
│   │   └── collect-state.sh        # 마무리 읽기전용 git 신호 1회 수집(read-only)
│   ├── wt/
│   │   └── SKILL.md                # /wt — git worktree 관리
│   ├── wiki/
│   │   └── SKILL.md                # /wiki — LLM Wiki 운영 (ingest/query/lint)
│   └── improve/
│       ├── SKILL.md                # /improve — 자기개선 loop 분석 축 (구 /audit 흡수; read-only·랭킹·제안)
│       └── improve.sh              # 자산 간 참조 정합 기계 점검 + dlc 신호 집계 (read-only)
├── scripts/
│   ├── notify-hook.js              # notify 진입점 (cross-platform; mac 인라인, win→.ps1 위임)
│   ├── notify.ps1                  # (Windows) Toast + 사운드 + flash
│   ├── notify-hook.ps1             # (Windows) notify-hook.js 가 spawn
│   ├── guard-worktree-edit.js      # PreToolUse — worktree 밖 main repo 편집 차단
│   ├── dlc-task-router.js          # UserPromptSubmit — dlc discipline 주입 + 장부 리셋
│   ├── dlc-evidence-ledger.js      # PostToolUse — 변경·검증 기록 + 문서 drift dirty flag
│   ├── dlc-early-stop.js           # Stop — 검증 누락 + 문서 drift capped 경고
│   ├── dlc-doc-drift.js            # 문서 drift 판정 순수 모듈 (+ .test.js)
│   ├── dlc-ledger.js               # 위 dlc hook 공유 장부 모듈 (hook 미등록)
│   ├── dlc-signal.js               # 자기개선 loop 신호 수집 모듈 — telemetry append (+ .test.js)
│   ├── session-brief.js            # SessionStart — 머지 대기 + /improve 권장 브리프 (+ .test.js)
│   ├── usage-count.js              # improve.sh deep — transcript 사용량 카운트 (+ .test.js)
│   ├── pre-commit-check.sh / .ps1  # settings.json secret guard (pre-commit + pre-push)
│   ├── install-hooks.sh / .ps1     # .git/hooks/{pre-commit,pre-push,post-checkout} wrapper 생성
│   ├── prompt-gwl.py               # UserPromptSubmit 훅 (프로젝트별 사용)
│   ├── gwl.ps1 / gwl.zsh           # `gwl` — worktree list + 현재 위치 → (Windows / macOS·zsh)
│   └── install-gwl.ps1 / .zsh      # gwl 을 profile($PROFILE·~/.zshrc)에 등록 (멱등)
├── wiki/                           # LLM Wiki — 영속 프로젝트 메모리
│   ├── WIKI.md                     # 운영 규약 (schema)
│   ├── index.md                    # 페이지 카탈로그
│   ├── log.md                      # 연산 로그
│   ├── raw/                        # 원문 (gitignored, 런타임 생성·미추적)
│   └── pages/                      # concept·entity·decision·source·query
└── plans/                          # 핸드오프 plan 파일 (tracked — §10, 브랜치와 함께 commit)
```

---

## Troubleshooting

### Statusline 미표시
1. Claude Code 재시작 후에도 안 보이면 직접 실행해 stdout 확인:
   - macOS/Linux: `node ~/.claude/statusline.js < /dev/null`
   - Windows (Git Bash): `node ~/.claude/statusline.js < /dev/null`
2. `~` 가 확장 안 되는 환경(Windows 에 Git Bash 없어 PowerShell fallback)이면 statusline 미표시 → Git Bash 설치. 임시로 absolute path 박아 원인 분리 가능.
3. Node 가 PATH 에 없으면 `node --version` 으로 확인.
4. Workspace trust dialog 거부 시 statusline 미실행. `statusline skipped · restart to fix` 표시면 trust accept 후 재시작.

### Hook 미실행 (notify 안 됨)
1. 공통: 직접 호출로 확인 — `echo '{}' | node ~/.claude/scripts/notify-hook.js Stop` (사운드/알림 떠야 함). `node --version` 으로 PATH 확인.
2. macOS: 첫 `osascript` 호출 시 알림 권한 허용 필요 (위 "macOS 알림 권한").
3. Windows: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` 한 번 실행 (notify-hook.js 가 spawn 하는 `.ps1` 용). `.ps1` 직접 점검: `powershell -File "$env:USERPROFILE\.claude\scripts\notify-hook.ps1" -Event Stop -DryRun` → JSON 출력 확인. 디버그 로그: `$env:CLAUDE_NOTIFY_DEBUG = '1'` 설정 후 재현 → `%TEMP%\claude-notify-debug.json` 확인, 후 `Remove-Item Env:\CLAUDE_NOTIFY_DEBUG`.

### Codex quota 미표시
1. `codex --version` 으로 CLI 존재 확인
2. `codex login` 인증 상태 확인
3. `cache/codex-quota.json` 의 `error` 필드 확인 — 마지막 실패 사유 기록
4. 수동 refresh: `node "$env:USERPROFILE\.claude\codex-quota-refresh.js"` 직접 실행 후 cache 갱신 확인

### Pre-commit guard 가 정상 변경을 차단
`scripts/pre-commit-check.ps1` 의 토큰 패턴이 settings.json 의 정상 값과 충돌하는 경우. 패턴 수정이 정답. 정말 통과 필요하면 `git commit --no-verify` — 단 한 번도 안 보고 통과시키지 말 것.
