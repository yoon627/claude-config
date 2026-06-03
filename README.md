# Claude Code Global Config (Windows / macOS)

Windows 에서 사용하는 `%USERPROFILE%\.claude\` 또는 macOS 에서 사용하는 `~/.claude/` 의 사용자 글로벌 설정·에이전트·명령·스킬·후크·스크립트·스테이터스라인을 한 레포에 모은 것. 다른 머신에서 동일한 작업 환경을 빠르게 재현하기 위함.

대상: Claude Code 를 깊이 사용하는 본인. 일반 공개 가이드 아님. 본인 워크플로우와 기존 자동화에 종속된 컴포넌트가 일부 있음 (특히 per-repo hook 에 의존하는 `commands/local-review`).

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

# 4. (선택) PowerShell `gwl` 명령 설치 — worktree list 단축키
#    SessionStart hook 이 pwsh 있으면 매 세션 자동 등록하므로, 다음 세션을 안 기다리고 즉시 쓰려는 경우에만.
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

`scripts/pre-commit-check.ps1` 가 staged/HEAD `settings.json` 을 검사해서 다음을 차단:
- 금지 키: `mcpServers`, `apiKeyHelper`, `awsCredentialExport`, `awsAuthRefresh`
- 토큰 패턴: Anthropic / OpenAI / GitHub / GitLab / AWS / GCP / Slack / JWT / PEM

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

# 3. Claude Code 재시작
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

`scripts/pre-commit-check.sh` 가 Windows `.ps1` 버전과 동일한 규칙으로 staged/HEAD `settings.json` 을 검사. 동일하게 금지 키 + 토큰 패턴 차단.

설치:
```bash
./scripts/install-hooks.sh
```

`.git/hooks/` 머신별이라 clone 한 프로젝트마다 매번 실행 필요.

---

## Verify

설치 후 다음으로 동작 확인:

### 1. Statusline 표시
Claude Code 실행 후 화면 하단에 한 줄이 나와야 함. 예시:
```
claude 53%(20:30) | codex 60%(18:45) | ctx 12% | main
```

표시 안 되면 → Troubleshooting 의 "statusline 미표시".

### 2. Notify hook 동작
간단한 작업을 끝낸 뒤 응답 완료(Stop) 시 사운드 + 알림이 나와야 함 — macOS: `Glass` + 배너, Windows: `Asterisk` + toast. 입력 대기(Notification) 시엔 다른 사운드 — macOS: `Ping`, Windows: `Exclamation`.

사운드/알림이 없으면 → "hook 미실행".

### 3. Codex quota 표시 (선택)
`codex --version` 으로 Codex CLI 설치 확인 후, statusline 에 `codex NN%(HH:MM)` 가 나타나야 함. 첫 표시는 캐시 채워질 때까지 최대 20초.

표시 안 되면 → "codex quota 미표시".

### 4. Subagent statusline
`Agent` 도구로 subagent 호출 시 subagent 의 statusline 에 `running | 1.2k tok | 0m 5s` 같은 한 줄이 나와야 함.

### 5. Pre-commit guard
`.\scripts\install-hooks.ps1` 실행 후 일반 `git commit` 은 무동작 (정상). 의도적으로 settings.json 에 `"mcpServers": {}` 박고 commit 시도 → `[BLOCKED]` 출력 + exit 1 이어야 함.

---

## Components

### CLAUDE.md — 전역 작업 규칙

모든 프로젝트에 자동 로드되는 사용자 지시문. Claude Code 가 `~/.claude/CLAUDE.md` 를 모든 세션에서 읽음.

11개 섹션:
0. 응답 언어 — 한국어, 의례적 preamble 금지
1. 핵심 규칙 — 추측 금지, 코드 read 기반 답변, 근본 원인, 검증 후 "완료", 사용자 변경사항 보호
2. 컨텍스트 관리 — `/clear`, `/rewind`, subagent 위임 기준
3. 작업 흐름 — Setup → Explore → Plan → Implement → Verify → Report
4. 웹 검색 능동 사용 — 지식 컷오프 이후 정보, 라이브러리 버전별 동작 등
5. Sub-agent — 표준 순서 (plan-reviewer → 구현 → code-reviewer → code-simplifier)
6. 코드 규칙 — 동일 디렉토리 스타일, 타입 힌트, 임시 코드 표기
7. 테스트 (TDD) — 테스트 작성 순서, 예외 조건
8. Git / 보안 — destructive 명령 금지, 시크릿 출력 금지
9. Claude ↔ Codex 협업 — `.claude/plans/` 핸드오프 채널
10. `.claude/plans/` 핸드오프 규약 — slug, frontmatter, 6개 섹션

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

### agents/ — 5개 subagent

`Agent` 도구로 호출. CLAUDE.md §5 의 표준 순서 (plan-reviewer → 구현 → code-reviewer → code-simplifier) 가 기본.

| 파일 | 호출 시점 | 핵심 책임 |
|---|---|---|
| `plan-reviewer.md` | Plan 단계 직후 (비사소한 모든 구현 계획) | 누락 케이스·잘못된 가정·영향 범위·rollback·근본 원인 비판적 발굴. public API / DB schema / migration / 보안 / 아키텍처 / 권한 변경 시 필수. |
| `architecture-reviewer.md` | 트리거 기반 (자동 호출 대상 아님) | 설계 결정 — 의존 방향·레이어 경계·객체 생명주기·DI/IoC·인터페이스 위치·테스트 가능 구조. public API / proto / DB schema / auth 변경, 신규 service·repository·client, DI 변경, 2개 이상 레이어 변경, 150줄 이상 diff, 또는 설계 의문 명시 시. |
| `code-reviewer.md` | 구현 직후 (코드 변경이 있었던 모든 흐름) | 버그·보안·테스트 누락·예외 처리·성능·backward compatibility·근본 원인. 통과 검토 금지, 비판적 발굴 목적. |
| `code-simplifier.md` | code-reviewer 통과 후 항상 실행 | 중복·과한 추상화·불필요한 복잡도·죽은 코드·과한 옵션 제거. ROI 없으면 보고만. public API / 행동 변경 / 다중 파일 리팩토링은 제안만 (직접 수정 금지). |
| `researcher.md` | 외부 사실 조사 필요 시 (어느 단계에서든) | 라이브러리 버전별 동작·마이그레이션·최신 API, 정확한 에러 메시지 매칭, 릴리스 노트·CVE·RFC, 지식 컷오프 이후 정보, 함수/플래그 실존 여부 불확실 시. |

각 agent 의 frontmatter `tools` 필드가 권한 범위를 제한 (예: researcher 는 Edit 권한 없음, code-reviewer 는 Bash 가능). agent 별 출력 형식과 호출 조건은 각 파일 본문 참고.

### commands/ — slash command

사용자 `/<command>` 입력 시 실행.

#### `local-review` (`/local-review [base-ref]`)

`base-ref..HEAD` 범위 변경분을 **5개 관점** (security, correctness, tests, impact, maintainability) 으로 **병렬 subagent** 로 검토. 각 perspective subagent 가 결과를 파일로 저장 → 6번째 synthesis subagent 가 통합 → `local.md` 작성. 메인 컨텍스트는 요약만 받음 (raw 결과 끌어오기 금지).

저장 위치: `<active plan dir>/reviews/<TS>-<sha7>/local.md`.

**Per-repo hook 의존**: `local-review` 는 프로젝트 `.claude/hooks/active-plan.sh`, `resolve-range.sh` 가 있어야 동작. 글로벌 설정만으론 미작동 — 프로젝트 setup 시 hook 별도 설치 필요.

### skills/dlc/ — 자동 개발 사이클

`/dlc` 명시 호출 또는 비자명한 코드 변경 시 적용하는 개발 사이클 오케스트레이션. 규모 (trivial / small / medium / structural) 를 판정해 단계를 gate — 오타 1줄은 즉시 통과, structural 변경은 explore → plan → 리뷰 → TDD → 구현 → 리뷰 → simplify → 검증 전체를 돈다.
- 메인이 hub, 리뷰/검토만 격리 subagent (plan-reviewer, architecture-reviewer, code-reviewer). 구현·통합·최종 판단은 메인.
- code-simplifier 는 `Edit` 권한이 있어 격리 mutating 단계 — 메인이 diff 흡수 + targeted 재검증.
- `.claude/plans/<slug>-plan.md` 가 subagent 간 단일 공유 채널 (메인만 write).
- codex 병행 검토 호출 규약은 `docs/codex-review.md` (phase 당 codex owner 1개 지정으로 중복 호출 방지, Windows/PowerShell fallback 포함).

### skills/c/ — plan 이어가기

`/c` 로 현재 worktree/repo 의 진행 중인 plan(§10)을 찾아 **남은 작업 + plan↔실제(git/코드) sync 상태**를 진단하고, 어긋나면 plan 을 보정한 뒤 다음 액션을 제시.
- branch→plan dir 매칭(§10), 실패 시 `in_progress`/`blocked` plan 목록 제시 후 사용자 선택 (추측 자동선택 안 함).
- `plans/` 가 gitignored & worktree별 독립이라 현재 repo + main worktree 양쪽 `plans/` 를 탐색.
- 확인·sync 진단·plan 보정까지 수행하되 **다음 액션은 제시만** (자동 실행 안 함). plan 이 없으면 새로 만들지 않음 — 신규 plan 생성은 dlc 몫.

### skills/e/ — plan 마무리

`/e` 로 진행 중이던 plan(§10)을 **실제 git/코드 상태로 동기화 기록**하고 작업을 마무리. c(이어가기)의 대칭.
- uncommitted 변경은 작업 브랜치에 **임시(WIP) 커밋**으로 보존 — `main`/`master` 직접 커밋·push 는 안 함(§8), `.env`·key 등 위험 파일은 커밋 보류 후 확인.
- `# Progress`/`# Next`/`# Decisions`/`status`/`updated` 를 사실 기반으로 갱신 → 다음 세션이 `/c` 로 곧장 이어받음.
- done 자동 전환 안 함 (확정 완료 신호 + 사용자 확인 시만, 기본 `in_progress` 체크포인트). plan 없으면 새로 만들지 않음 — 임시 커밋 + 보고만.
- worktree 에서 작업이 `done`·clean·pushed 이고 내부에 잃을 ignored 산출물(plan·`.env`)이 없으면 **worktree 삭제도 제안** (AskUserQuestion; worktree만/+브랜치/유지). 삭제 시 main 으로 빠져나간 뒤 `git worktree remove`, `--force`·`branch -D` 는 추가 확인.

### skills/wt/ — Git worktree 빠른 관리

`/wt` (목록) · `/wt <N>` (N번째 worktree 로 이동) · `/wt <기존이름>` (정확일치 worktree 로 이동) · `/wt <요청사항>` (slug 확인 후 worktree 신규 생성 → 그 안에서 `dlc` 로 작업) · `/wt rm <name>` (제거) 로 worktree 관리. 컨벤션:
- worktree path: `.claude/worktrees/<name>` (현재 repo 기준)
- 브랜치 이름 = worktree 이름 (1:1)
- `EnterWorktree(path: <abs>)` 로 진입 — `name` 인자 사용 금지 (Claude Code 의 `worktree-` prefix 자동 부착 회피)
- 정수·`rm`·기존 worktree 정확일치가 아닌 텍스트는 **요청사항**으로 간주 → 영문 kebab-case slug 파생 → AskUserQuestion 으로 확인 후 생성 → 요청사항 원문을 `dlc` task 로 전달 (dlc 없는 빈 worktree 단순 생성은 폐지)

### scripts/

후크가 호출하는 진입점은 `notify-hook.js` 하나 (settings.json 의 `Stop` / `Notification` command). macOS 는 이 안에서 직접 알림을 띄우고, Windows 는 기존 `.ps1` 로 위임한다.

#### `notify-hook.js`
Cross-platform notify 진입점 (Node). stdin 의 Claude Code JSON 에서 `message` · `cwd` 추출 (title = cwd basename). **macOS**: `afplay` 시스템 사운드 + `osascript` 배너 (인라인). **Windows**: 원본 stdin 을 그대로 넘기며 `powershell.exe -File notify-hook.ps1` spawn. **Linux**: best-effort `notify-send`. 모든 동작 best-effort — 실패해도 throw 안 하고 stdin 1초 타임아웃으로 세션 안 멈춤. 사운드 기본값은 이벤트별 (Stop→Glass/Asterisk, Notification→Ping/Exclamation); command 3번째 인자로 override.

#### `notify.ps1`
Toast 알림 + 시스템 사운드 + 윈도우 flash. 우선순위: WinRT ToastNotification → System.Windows.Forms NotifyIcon. WinRT toast 는 Windows PowerShell 5.1 전용 (PS7 은 WinRT 어셈블리 미포함) — hook 이 `powershell.exe` 로 5.1 고정 실행. toast 표시 전 `HKCU\Software\Classes\AppUserModelId\Claude.Code` 에 AppID 자가 등록 (미등록 AppID 는 Windows 가 toast 를 조용히 버림).

#### `notify-hook.ps1`
Windows 에서 `notify-hook.js` 가 spawn (`Stop` / `Notification` 이벤트). stdin 으로 넘어온 Claude Code JSON 에서 `cwd`, `session_id` 추출, 부모 프로세스 트리에서 WindowsTerminal 의 tab 제목 추출 → `notify.ps1` 에 title/message 전달. (macOS·Linux 에선 호출되지 않음.)

debug log: `$env:CLAUDE_NOTIFY_DEBUG = '1'` 설정 시에만 `%TEMP%\claude-notify-debug.json` 에 매 호출마다 덮어씀. cwd, sessionId 포함되므로 디버깅 후 환경변수 해제 권장. 기본값은 off (privacy footprint 최소화).

#### `pre-commit-check.ps1`
staged (`pre-commit` 모드) 또는 HEAD (`pre-push` 모드) 의 `settings.json` 을 검사. 금지 키 (`mcpServers`, `apiKeyHelper`, `awsCredentialExport`, `awsAuthRefresh`) 또는 토큰 패턴 (Anthropic/OpenAI/GitHub/GitLab/AWS/GCP/Slack/JWT/PEM) 검출 시 exit 1.

`.git/hooks/` 에 직접 두지 않고 별도 파일 → repo 에 tracked. `install-hooks.ps1` 가 `.git/hooks/{pre-commit,pre-push}` sh wrapper 를 생성해서 이 스크립트로 위임.

#### `install-hooks.ps1`
`.git/hooks/pre-commit`, `.git/hooks/pre-push` sh wrapper 생성. UTF-8 (no BOM) + LF endings — Git Bash 가 인식. idempotent — 재실행 시 덮어쓰기. 새 머신 setup 시 1회 실행.

#### `prompt-gwl.py`
프롬프트에 정확히 `gwl` 만 입력하면 가로채서 `git worktree list` 를 현재 위치 `→` 마커와 함께 출력하는 UserPromptSubmit 훅 (모델 왕복 없음). `--porcelain` 기반이라 공백 포함 경로·bare·detached worktree 도 정확히 파싱. 글로벌 `settings.json` 엔 미등록 — 프로젝트별 `.claude/settings.json` 에 hook 으로 등록해 사용.

#### `gwl.ps1` (Windows / PowerShell)
`prompt-gwl.py` 와 같은 목적의 PowerShell 단축 함수 — `git worktree list` 를 출력하되 현재 디렉토리를 포함하는 worktree 앞에 `→` 마커. `$PROFILE` 에서 dot-source 해 명령처럼 사용 (모델 왕복 없음). 임의 프로젝트용으로 `--porcelain` 을 쓰는 `prompt-gwl.py` 와 달리, 개인 worktree(`.claude/worktrees/<name>` 규약상 경로 무공백) 전용이라 단순 `git worktree list` split. `→` 가 Windows PowerShell 5.1(BOM 없는 UTF-8 을 ANSI 로 해석)에서 깨지지 않도록 **UTF-8 BOM** 으로 저장 (PS 7 은 양쪽 모두 읽음).

#### `install-gwl.ps1` (Windows / PowerShell)
`$PROFILE` (CurrentUserCurrentHost) 에 `. "$HOME/.claude/scripts/gwl.ps1"` 한 줄을 marker 블록(begin/end)으로 멱등 추가 — 두 marker 다 있으면 skip, 한쪽만 있으면(손상) 에러, 없으면 추가. 기존 inline `function gwl` 발견 시 경고. dot-source 대상은 항상 `~/.claude/scripts/gwl.ps1`(문서상 clone 위치)이라 레포가 다른 곳이면 경고만 하고 그대로 진행. 이후 `git pull` 로 `gwl.ps1` 갱신 시 profile 수정 없이 반영. **수동 1회 실행** 필요 — `~/.claude` 에서 `& ./scripts/install-gwl.ps1` (또는 `pwsh -File scripts/install-gwl.ps1`). 과거 `hooks.SessionStart` 가 자동 실행했으나, 무서명 원격 스크립트를 매 세션 자동 실행하는 위험 때문에 제거했다.

### settings.json — 살아있는 설정 (tracked)

머신 간 sync 의 source of truth. 핵심 키:
- `theme`, `preferredNotifChannel` — Claude Code UI 설정
- `permissions.deny` — `git push origin main/master` 직접 푸시 차단
- `permissions.ask` — 일반 `git push` 는 확인 후 실행
- `statusLine`, `subagentStatusLine` — statusline 스크립트 등록 (`node ~/.claude/statusline.js`)
- `env.CLAUDE_CODE_EFFORT_LEVEL` — Opus effort level (`max`). docs 명시 값: `low|medium|high|xhigh|max`. `/effort` 나 `effortLevel` 키로는 세션 한정이지만 **env 변수로 설정할 때만 영구 적용**되므로 이 키로 둔다. env 가 `effortLevel` 키를 override.
- `hooks.SessionStart` — `~/.claude` 가 `main` 브랜치 + 클린 트리이면 `git pull --ff-only origin main` 으로 origin/main 자동 동기화 (ff-only·가드 실패 무음; `~` 확장 위해 sh/Git Bash 필요). pull 로 HEAD 가 바뀌면 한 줄 알림(`~/.claude updated …`) 출력. pull 내용은 **다음 세션부터** 적용. dirty/분기/다른 브랜치면 가드에 걸려 skip. (과거엔 `install-gwl.ps1` 을 자동 실행하는 2번 command 가 있었으나 무서명 원격 스크립트 자동 실행 위험 때문에 제거 — gwl 등록은 위 `install-gwl.ps1` 수동 1회 실행으로.)
- `hooks.Stop` / `hooks.Notification` — 응답 완료 / 입력 대기 시 `node ~/.claude/scripts/notify-hook.js` 호출 (cross-platform)
- `enabledPlugins`, `extraKnownMarketplaces` — Pyright LSP plugin + OpenAI Codex marketplace

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
- `statusline.js`, `subagent-statusline.js`, `codex-quota-refresh.js`, `notify-hook.js` — `os.homedir()` / `process.platform` 기반, **cross-platform**.
- `CLAUDE.md`, `agents/*.md`, `commands/*.md`, `skills/*/SKILL.md` — 텍스트 가이드, **OS 무관**.
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
│   ├── code-simplifier.md
│   ├── plan-reviewer.md
│   └── researcher.md
├── commands/
│   └── local-review.md             # /local-review (per-repo hook 필요)
├── docs/
│   └── codex-review.md             # codex 병행 검토 공유 규약
├── skills/
│   ├── dlc/
│   │   └── SKILL.md                # /dlc — 자동 개발 사이클
│   ├── c/
│   │   └── SKILL.md                # /c — plan 이어가기
│   ├── e/
│   │   └── SKILL.md                # /e — plan 마무리 (임시 커밋 + 동기화)
│   └── wt/
│       └── SKILL.md                # /wt — git worktree 관리
├── scripts/
│   ├── notify-hook.js              # notify 진입점 (cross-platform; mac 인라인, win→.ps1 위임)
│   ├── notify.ps1                  # (Windows) Toast + 사운드 + flash
│   ├── notify-hook.ps1             # (Windows) notify-hook.js 가 spawn
│   ├── pre-commit-check.sh / .ps1  # settings.json secret guard (pre-commit + pre-push)
│   ├── install-hooks.sh / .ps1     # .git/hooks/{pre-commit,pre-push} wrapper 생성
│   ├── prompt-gwl.py               # UserPromptSubmit 훅 (프로젝트별 사용)
│   ├── gwl.ps1                     # (Windows) PowerShell `gwl` — worktree list + 현재 위치 →
│   └── install-gwl.ps1             # gwl.ps1 을 $PROFILE 에 dot-source 등록 (멱등)
└── plans/                          # 핸드오프 plan 파일 (gitignored)
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
