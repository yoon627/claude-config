# Claude Code Global Config (Windows)

Windows 에서 사용하는 `%USERPROFILE%\.claude\` 의 사용자 글로벌 설정·에이전트·명령·스킬·후크·스크립트·스테이터스라인을 한 레포에 모은 것. 다른 Windows 머신에서 동일한 작업 환경을 빠르게 재현하기 위함.

대상: Claude Code 를 깊이 사용하는 본인. 일반 공개 가이드 아님. 본인 워크플로우와 기존 자동화에 종속된 컴포넌트가 일부 있음 (특히 `commands/push-review`).

---

## Prerequisites

- **Node.js** (LTS 권장) — `statusline.js`, `subagent-statusline.js`, `codex-quota-refresh.js` 가 Node 로 실행. `node --version` 으로 확인.
- **Claude Code** 설치 — `~/.claude/` 위치를 자동으로 읽음. 설치 후 한 번이라도 실행하여 디렉토리 생성.
- **Git** + **Git Bash** — Claude Code 가 일부 명령을 Git Bash 로 실행. statusline 의 `~` expansion 도 Git Bash 가 처리.
- **(선택) Codex CLI** — statusline 의 Codex quota 표시용. 없으면 해당 부분만 빠지고 나머지는 정상 동작 (silent fail).
- **(선택) PowerShell ExecutionPolicy** — 후크가 `.ps1` 스크립트를 호출하므로 `Restricted` 면 실행 안 됨. 아래 Install 참고.

---

## Install

### A. 새 Windows 머신 — `~/.claude/` 가 없거나 비어있을 때

```powershell
# 1. clone (USERPROFILE 위치로)
cd $env:USERPROFILE
git clone <this-repo-url> .claude

# 2. 실제 settings.json 생성 (example 복사)
Copy-Item .claude\settings.example.json .claude\settings.json

# 3. (필요 시) PowerShell ExecutionPolicy — 후크가 .ps1 호출하므로
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 4. Claude Code 재시작
```

### B. 이미 `~/.claude/` 가 있는 머신 — 기존 데이터 보존

`git clone` 은 디렉토리가 비어있어야 동작. 기존 디렉토리에 덮어쓰려면:

```powershell
cd $env:USERPROFILE\.claude

# 1) 백업 디렉토리 명시 생성 (-Force 는 이미 있어도 통과)
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
#    그래야 사용자가 자체 수정한 statusline.js, CLAUDE.md, agents/*.md 같은 파일이
#    무음 덮어쓰기 당하지 않는다. git 출력에 표시된 충돌 파일을 backup 으로 옮긴 뒤 재시도.
git checkout origin/main -b main

# 5) settings.json 차단되어 있으므로 example 에서 복사 (없을 때만)
if (-not (Test-Path settings.json)) {
  Copy-Item settings.example.json settings.json
}
```

`.gitignore` 가 화이트리스트 방식이라 `.credentials.json`, `settings.local.json`, `history.jsonl`, `projects/`, `sessions/`, `cache/` 등 기존 개인 데이터는 git 이 건드리지 않음.

### C. settings.json 커스터마이즈

기본 `settings.example.json` 그대로 복사하면 거의 모든 기능 동작. 머신별로 다음을 추가:

- **MCP 서버**: `mcpServers` 키
- **추가 allow list**: `permissions.allow` — `settings.local.json` 에 두는 게 안전 (git 차단됨)
- **개인 hook**: 예를 들어 특정 repo 의 pre-push hook 같은 머신별 후크는 `settings.local.json` 에 두거나, 해당 repo 의 `.claude/settings.json` 에 두는 것을 권장 (글로벌 설정 오염 방지)

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
간단한 작업을 끝낸 뒤 응답 완료 시 Asterisk 시스템 사운드 + 토스트 알림이 나와야 함. 입력 대기 시엔 Exclamation 사운드.

사운드/알림이 없으면 → "hook 미실행".

### 3. Codex quota 표시 (선택)
`codex --version` 으로 Codex CLI 설치 확인 후, statusline 에 `codex NN%(HH:MM)` 가 나타나야 함. 첫 표시는 캐시 채워질 때까지 최대 20초.

표시 안 되면 → "codex quota 미표시".

### 4. Subagent statusline
`Agent` 도구로 subagent 호출 시 subagent 의 statusline 에 `running | 1.2k tok | 0m 5s` 같은 한 줄이 나와야 함.

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
11. 실수 기록 — `docs/lessons.md` 형식

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

#### `push-review` (`/push-review [base-ref]`)

`local-review` + **Codex 백그라운드 리뷰** 를 동시 실행 → 통합 리포트 (`combined.md`) 작성. 자동 push 안 함, recommendation (`PROCEED` / `FIX_REQUIRED` / `REVIEW_NEEDED`) 만 출력. 사용자가 직접 `git push`.

**Per-repo hook 의존**: `active-plan.sh`, `resolve-range.sh`, `run-codex-review.sh`, `review-codex.sh`, `clear-review.sh` (5개) 필요. 없으면 안내 후 종료. 프로젝트별로 `.claude/hooks/` 에 설치해야 함.

### skills/wt/ — Git worktree 빠른 관리

`/wt`, `/wt list`, `/wt switch <X>`, `/wt new <X>`, `/wt remove <X>` 로 worktree 관리. 컨벤션:
- worktree path: `.claude/worktrees/<name>` (현재 repo 기준)
- 브랜치 이름 = worktree 이름 (1:1)
- `EnterWorktree(path: <abs>)` 로 진입 — `name` 인자 사용 금지 (Claude Code 의 `worktree-` prefix 자동 부착 회피)

### scripts/

#### `notify.ps1`
Toast 알림 + 시스템 사운드 + 윈도우 flash. 우선순위: WinRT ToastNotification → System.Windows.Forms NotifyIcon. PowerShell 7 / Windows PowerShell 5 둘 다 지원.

#### `notify-hook.ps1`
`Stop` / `Notification` 후크가 호출. stdin 으로 들어온 Claude Code JSON 에서 `cwd`, `session_id` 추출, 부모 프로세스 트리에서 WindowsTerminal 의 tab 제목 추출 → `notify.ps1` 에 title/message 전달.

debug log: `$env:CLAUDE_NOTIFY_DEBUG = '1'` 설정 시에만 `%TEMP%\claude-notify-debug.json` 에 매 호출마다 덮어씀. cwd, sessionId 포함되므로 디버깅 후 환경변수 해제 권장. 기본값은 off (privacy footprint 최소화).

### settings.example.json — 설정 템플릿

clone 후 `settings.json` 으로 복사해서 사용. 본 파일 자체는 git tracked, 실제 `settings.json` 은 belt-and-suspenders 차단 (`gitignore`).

핵심 키:
- `theme`, `effortLevel`, `preferredNotifChannel` — Claude Code UI 설정
- `permissions.deny` — `git push origin main/master` 직접 푸시 차단
- `permissions.ask` — 일반 `git push` 는 확인 후 실행
- `statusLine`, `subagentStatusLine` — 위 statusline 스크립트 등록
- `hooks.Stop` / `hooks.Notification` — 응답 완료 / 입력 대기 시 PowerShell 후크 호출
- `enabledPlugins`, `extraKnownMarketplaces` — Pyright LSP plugin + OpenAI Codex marketplace

Path 표기:
- statusLine command: `node "~/.claude/statusline.js"` — Claude Code 가 Git Bash 로 spawn, `~` expansion 처리
- Hook command: `& "$env:USERPROFILE\.claude\scripts\notify-hook.ps1"` — `shell: powershell` 이라 PowerShell 의 `$env:USERPROFILE` automatic variable 사용

머신별 추가 (allow list 보강, MCP 서버, 개인 hook 등) 는 `settings.local.json` 에 두는 것을 권장 (git 차단).

---

## What's NOT in this repo

`.gitignore` 의 화이트리스트 방식 (`/*` + `!/...`) + belt-and-suspenders 차단으로 다음은 의도적 제외:

| 항목 | 사유 |
|---|---|
| `.credentials.json` | Claude / Anthropic OAuth 토큰. 절대 commit 금지. |
| `settings.json` | 살아있는 실제 설정. 향후 MCP server config / API key 추가 시 자동 commit 위험 차단. `settings.example.json` 에서 복사해 사용. |
| `settings.local.json` | 머신별 allow list (이전 세션에서 채워진 경로 다수). 다른 머신에 의미 없음. |
| `history.jsonl` | 명령 입력 히스토리. 개인 데이터. |
| `projects/`, `sessions/`, `tasks/`, `cache/`, `paste-cache/`, `shell-snapshots/`, `file-history/`, `backups/`, `plugins/` | runtime cache, 세션 로그, 붙여넣기 캐시 등 머신·세션별 데이터 |
| `mcp-needs-auth-cache.json` | MCP 인증 캐시 |
| `*.bak`, `*.bak.*`, `tmp_*` | 임시 백업 |
| `CLAUDE.md.bak.*` | CLAUDE.md 이전 버전 백업 |

---

## Customization

### 사용자명이 다른 머신
`settings.example.json` 의 path 가 모두 `~` 또는 `$env:USERPROFILE` 로 추상화돼 있어 사용자명 무관 동작. Git Bash 와 PowerShell 양쪽에서 자동 expansion.

### Codex CLI 없는 머신
설치 안 해도 statusline 의 `codex NN%(HH:MM)` 부분만 빠지고 나머지는 정상. 설치하려면 `npm install -g @openai/codex` 후 `codex login`.

### PowerShell ExecutionPolicy 가 `Restricted` 인 머신
후크의 `.ps1` 스크립트 실행 불가. 일회성 처리:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
또는 settings 의 hook command 를 다음으로 교체:
```
"command": "powershell -NoProfile -ExecutionPolicy Bypass -File \"$env:USERPROFILE\\.claude\\scripts\\notify-hook.ps1\" -Event Stop -Sound Asterisk"
```

### Notify 알림 끄기
`settings.json` 의 `hooks.Stop` / `hooks.Notification` 블록 제거. `preferredNotifChannel` 도 `"none"` 으로 변경.

### Permission prompt 자주 뜨는 경우
Claude Code 내장 skill `/fewer-permission-prompts` 호출 시 최근 transcript 의 read-only Bash·MCP 호출을 분석해 `.claude/settings.json` 의 `permissions.allow` 에 자동 추가. 머신별 차이는 `settings.local.json` 에 두는 게 안전.

### Commit 전 식별자 leak 점검
다른 머신용 username·내부 repo 이름·이메일 등이 staged 파일에 새어 들어갔는지 commit 전 직접 검사. CI 가 자동 처리하지 않는 이유는 패턴 자체가 leak 표면이 될 수 있어서.
```powershell
git diff --staged | Select-String -Pattern '본인_username|내부_repo_이름|이메일도메인'
```
또는 Git Bash:
```bash
git diff --staged | grep -iE '본인_username|내부_repo_이름|이메일도메인'
```
패턴은 본인 환경의 식별자로 채우고, 외부에 두지 말 것 (memo / 1Password 등 머신 외부 저장소 권장).

---

## Troubleshooting

### Statusline 미표시
1. Claude Code 재시작 후에도 안 보이면 직접 실행해 stdout 확인:
   - Git Bash: `node "~/.claude/statusline.js" < /dev/null`
   - cmd / PowerShell: `node "$env:USERPROFILE\.claude\statusline.js" < NUL` (cmd 는 `~` expansion 안 함)
2. `~` expansion 이 안 되는 환경이면 settings.json 의 path 를 `$env:USERPROFILE` 또는 절대경로로 교체
3. Node 가 PATH 에 없으면 `node --version` 으로 확인

### Hook 미실행 (notify 안 됨)
1. `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` 한 번 실행
2. `powershell -File "$env:USERPROFILE\.claude\scripts\notify-hook.ps1" -Event Stop -DryRun` 로 직접 호출 — JSON 출력 나오는지
3. 디버그 로그 사용: `$env:CLAUDE_NOTIFY_DEBUG = '1'` 설정 후 재현 → `%TEMP%\claude-notify-debug.json` 확인 (후크 invoke 흔적). 확인 후 `Remove-Item Env:\CLAUDE_NOTIFY_DEBUG` 로 해제.

### Codex quota 미표시
1. `codex --version` 으로 CLI 존재 확인
2. `codex login` 인증 상태 확인
3. `cache/codex-quota.json` 의 `error` 필드 확인 — 마지막 실패 사유 기록
4. 수동 refresh: `node "$env:USERPROFILE\.claude\codex-quota-refresh.js"` 직접 실행 후 cache 갱신 확인

### Hook 이 다른 repo 의 스크립트를 찾음 (예: `pre-push-review.sh`)
`settings.example.json` 에는 그런 hook 이 없음. 본인 `settings.json` 에 추가됐다면 머신별 차이 — 필요시 제거하거나 `settings.local.json` 으로 이동.

### `commands/push-review` 가 `Error: hooks 가 설치되지 않았습니다`
프로젝트 `.claude/hooks/` 에 `active-plan.sh`, `resolve-range.sh`, `run-codex-review.sh`, `review-codex.sh`, `clear-review.sh` 가 없어서 발생. 기존 프로젝트의 `.claude/hooks/*.sh` 를 복사해 `chmod +x` 후 재시도. 글로벌 `.claude/` 가 아닌 **각 프로젝트** 의 `.claude/hooks/` 에 둬야 함.

---

## Roadmap

### 다른 OS 지원 (macOS / Linux)
현재는 Windows-only 가정으로 출발. portable 한 부분과 분기 필요한 부분 정리:
- `statusline.js`, `subagent-statusline.js`, `codex-quota-refresh.js` — `os.homedir()` 기반, **이미 portable**.
- `CLAUDE.md`, `agents/*.md`, `commands/*.md`, `skills/wt/SKILL.md` — 텍스트 가이드, **OS 무관**.
- `scripts/notify-hook.ps1`, `scripts/notify.ps1` — **PowerShell 전용**. macOS 는 `osascript -e 'display notification ...'` 또는 `terminal-notifier`, Linux 는 `notify-send` 로 분기 필요.
- `settings.example.json` — hook command 가 PowerShell 의존. OS 별 분기 또는 멀티 OS 호환 wrapper script 로 통합.

### 단일 실행 파일 install (`install.ps1`)
`settings.example.json` → `settings.json` 복사, ExecutionPolicy 설정, 자동 verify 까지 한 번에. 흐름:
1. 기존 `~/.claude/` backup (있으면)
2. `git clone` 또는 `git init + fetch + checkout` (기존 dir 처리)
3. `Copy-Item settings.example.json settings.json` (덮어쓰지 않음)
4. `Set-ExecutionPolicy CurrentUser RemoteSigned` (사용자 동의 후)
5. Statusline / notify hook / Codex quota 각각 1회 직접 호출 → stdout 검증
6. 실패 시 Troubleshooting 섹션의 어느 단락으로 가야 하는지 안내
- macOS / Linux 지원 시 `install.sh` 같은 인터페이스로 제공.

---

## Layout

```
~/.claude/
├── CLAUDE.md                       # 전역 작업 규칙 (자동 로드)
├── README.md                       # 본 파일
├── .gitignore                      # whitelist 방식 + belt-and-suspenders
├── settings.example.json           # 설정 템플릿
├── settings.json                   # 실제 설정 (git 차단, example 에서 복사)
├── settings.local.json             # 머신별 allow list 등 (git 차단)
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
│   ├── local-review.md             # /local-review (per-repo hook 필요)
│   └── push-review.md              # /push-review (per-repo hook 필요)
├── skills/
│   └── wt/
│       └── SKILL.md                # /wt — git worktree 관리
└── scripts/
    ├── notify.ps1                  # Toast + 사운드 + flash
    └── notify-hook.ps1             # Stop / Notification 후크 entry
```
