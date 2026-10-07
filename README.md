# Claude Code Global Config (Windows / macOS)

Windows 에서 사용하는 `%USERPROFILE%\.claude\` 또는 macOS 에서 사용하는 `~/.claude/` 의 사용자 글로벌 설정·에이전트·명령·스킬·후크·스크립트·스테이터스라인을 한 레포에 모은 것. 다른 머신에서 동일한 작업 환경을 빠르게 재현하기 위함.

대상: Claude Code 를 깊이 사용하는 본인. 일반 공개 가이드 아님. 본인 워크플로우와 기존 자동화에 종속된 컴포넌트가 일부 있음.

`settings.json` 은 **untracked** (2026-09-07~). Claude Code 가 이 파일에 머신별 값을 스스로 써넣어서 — Orca 훅 절대경로, gitkraken marketplace 의 `source: directory`, `/auto-mode-setup` 의 `autoMode`(머신 절대경로 + 사내 IP·도메인) — tracked 인 동안 `git pull` 이 주기적으로 막히고 public 레포로 사내 식별자가 새어나갔다. 키를 하나씩 빼는 대응은 3회 재발했다. 근거·이력은 `wiki/pages/decision/lesson-tracked-config-machine-paths.md`, 재도입 금지 사유는 `.gitignore` 주석.

내용 자체는 **단일 cross-platform** — statusline·notify 는 `node ~/.claude/...` 형태로 통일했고 (`~` 는 Git Bash·sh 양쪽에서 홈으로 확장), OS 분기는 호출되는 스크립트 내부에서 처리 (`scripts/notify-hook.js` 의 `process.platform`). Windows 의 toast·flash 만 `scripts/notify.ps1` / `notify-hook.ps1` 로 위임. 따라서 머신 간에는 **파일을 그대로 복사**하면 되고 OS별 편집은 필요 없다.

---

## Prerequisites

- **Node.js** (LTS 권장) — `statusline.js`, `subagent-statusline.js` 가 Node 로 실행. `node --version` 으로 확인.
- **Claude Code** 설치 — `~/.claude/` 위치를 자동으로 읽음. 설치 후 한 번이라도 실행하여 디렉토리 생성.
- **Git** + **Git Bash** (Windows) — Claude Code 가 statusLine·hook command 를 Windows 에서 Git Bash 로 실행. `~` 확장에 필요 (Git Bash·sh 는 `~` 를 홈으로 확장; `$HOME` 은 PowerShell fallback 시 깨질 수 있어 `~` 사용). Git Bash 가 없으면 PowerShell fallback 인데 이때 `~` 확장이 보장되지 않으므로 Windows 는 Git Bash 설치 필수.
- **(선택) Codex CLI** — reviewer subagent 의 Codex 병행 검토용(CLAUDE.md §9, `docs/codex-review.md`). 없으면 병행을 건너뛰고 Claude subagent 검토만 돈다.
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

# 3. Pre-commit / pre-push 가드 설치 (plans·settings.json 의 secret leak 차단)
cd $env:USERPROFILE\.claude
.\scripts\install-hooks.ps1

# 4. (선택) PowerShell `gwl` 명령 설치 — worktree list 단축키 (수동 1회 실행)
#    과거 SessionStart 자동등록은 무서명 원격 스크립트 자동 실행 위험으로 제거됨 (아래 install-gwl.ps1 절 참조).
.\scripts\install-gwl.ps1

# 5. settings.json 배치 — clone 에 포함되지 않는다 (untracked)
#    기존 머신의 ~/.claude/settings.json 을 그대로 복사해 온다. cross-platform 이라 편집 불필요.
#    없으면 hook·statusline 이 전혀 등록되지 않는다.

# 6. (선택) 비공개 용어 목록 — 기존 머신의 ~/.claude/private-terms.txt 를 복사 (untracked).
#    없으면 가드가 note 한 줄만 찍고 비공개 용어 검사를 건너뛴다 (아래 D 절).

# 7. 공용 wiki — 이 repo 에는 없다(비공개 repo 의 별도 clone, 아래 E 절).
git clone <비공개 wiki repo URL> $env:USERPROFILE\.claude\wiki

# 8. Claude Code 재시작
```

`settings.json` 은 **untracked** — clone 만으로는 오지 않으므로 위 5번을 건너뛰면 안 된다. 이유는 문서 맨 위 참조.

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
#    settings.json 은 untracked 라 checkout 대상이 아님 — 기존 파일이 그대로 살아남는다.
git checkout origin/main -b main

# 5) hooks 설치
.\scripts\install-hooks.ps1

# 6) 공용 wiki — 이 repo 에는 없다. 아래 E 절대로 clone 한다(wiki 가 있던 머신이면 E 절 1단계부터).
```

`.gitignore` 가 화이트리스트 방식이라 `.credentials.json`, `settings.local.json`, `history.jsonl`, `projects/`, `sessions/`, `cache/` 등 기존 개인 데이터는 git 이 건드리지 않음.

### C. 머신별 / 민감 정보 — `settings.local.json` 으로

`settings.json` 도 `settings.local.json` 도 이제 둘 다 gitignored 라, 이 구분은 "무엇이 커밋되나"가 아니라 **스코프**다. `settings.json` 은 이 머신의 base 설정, `settings.local.json` 은 그 위에 얹는 override — Claude Code 가 자동으로 deep merge 하고 `.local` 이 우선.

> ⚠️ `autoMode`(auto mode classifier 규칙)는 `settings.local.json` 에서 **읽히지 않는다**. 공식 문서: "The classifier doesn't read `autoMode` from project settings in `.claude/settings.json` or `.claude/settings.local.json`." 유효 스코프는 `~/.claude/settings.json` / managed settings / `--settings` 뿐이므로, 이 키만은 `.local` 로 옮길 수 없다 — 옮기면 에러 없이 조용히 무시된다.

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

`scripts/pre-commit-check.ps1` 가 커밋할 때는 staged `settings.json`·`plans/*.md`(tracked §10) 를, push 할 때는 push 되는 커밋(push 대상 ref 가 아직 갖지 않은 것 — 원격이 알려 준 현재 값 기준, 추적 ref 는 보지 않는다)이 `settings.json`·`plans/*.md` 에 **추가한 줄**을 검사해서 다음을 차단:
- 금지 키(settings.json): `mcpServers`, `apiKeyHelper`, `awsCredentialExport`, `awsAuthRefresh`
- 토큰/시크릿 패턴(settings.json·plans): Anthropic / OpenAI / GitHub / GitLab / AWS / GCP / Slack / JWT / PEM / DB URL creds / Bearer / 따옴표 시크릿 대입

`settings.json` 이 untracked 가 된 뒤로 이 가드가 실제로 보는 것은 `plans/*.md` 뿐이다. settings.json 검사는 staged 목록이나 push 범위에 그 파일 변경이 있을 때만 돌므로 지금은 조용히 건너뛴다 — 실수로 다시 추적되면 되살아나는 안전망으로 남겨 뒀다. push 검사는 `--no-verify`·commit-check(plumbing 이라 훅 없음)·다른 도구로 pre-commit 을 건너뛴 커밋까지 잡는다.

**비공개 용어 (`~/.claude` 에서만)**: 이 repo 는 공개라, 추적하지 않는 머신별 목록 `~/.claude/private-terms.txt`(한 줄 한 항목 — 회사·비공개 repo 이름·티켓 키 등, `#` 줄은 주석)에 적은 이름이 들어가는 커밋·push 도 막는다. 커밋 때는 staged 변경의 추가 줄·새 경로를, push 때는 ref 이름과 push 커밋의 추가 줄·새 경로·메시지·작성자/커미터를 본다(이 repo 의 모든 경로). 항목은 앞뒤가 ASCII 영숫자가 아닐 때만 걸리고(대소문자 무시 — 긴 단어·커밋 해시 속에는 안 걸린다), 줄 앞에 `*` 를 붙이면 부분일치로 걸린다. 출력은 목록 줄 번호와 위치(`private term (list line 3) in staged notes/a.md`)뿐 — 항목과 걸린 줄은 찍지 않는다. 걸리면 목록을 열어 보지 말고 그 표현을 일반 표현(예: "회사 repo")으로 바꾼다. 목록은 clone 으로 오지 않으니 머신마다 직접 복사한다 — 없으면 note 한 줄 후 통과, 디렉토리·읽을 수 없는 파일·3바이트 미만이나 제어문자가 든 항목은 차단(끄려면 목록을 비운다). `private-terms.txt` 라는 파일을 stage·push 하면 목록이 없어도 차단한다. 다른 repo 에서는 목록을 열지 않는다. 한계: 목록에 없는 이름, PR 제목·본문과 GitHub 웹 편집, `--no-verify` 는 못 잡는다(CLAUDE.md §11 공개 점검이 담당).

**목록을 도구로 열지 않게 (선택, 머신별)**: 에이전트가 목록을 열면 그 이름들이 대화 기록에 남는다. `~/.claude` 프로젝트의 로컬 설정 `~/.claude/.claude/settings.local.json`(gitignored)의 `permissions.deny` 에 `"Read(~/.claude/private-terms.txt)"` 를 더한다. 사용자 설정 `~/.claude/settings.json` 에 두지 않는 이유: 목록을 쓰는 가드가 `~/.claude` 에서만 돌아 이 프로젝트의 세션만 막으면 되고, 전역 deny 는 두지 않는다(아래 settings.json 절의 `permissions.deny`, CLAUDE.md §8). 다른 repo 의 세션은 막지 않는다. worktree 세션도 main checkout 의 이 파일을 읽는다([settings](https://code.claude.com/docs/en/settings) 문서 — 2.1.211 이후. 2.1.288·macOS 에서 사본 없는 worktree 에 `EnterWorktree` 로 들어간 세션으로 확인했고, worktree 에서 바로 시작한 세션은 재지 않았다). 예외는 Windows 등 repo 루트의 파일을 쓰지 않는 경우(목록은 `skills/wt/references/env-copy.md`)로, 로컬 설정을 세션의 작업 디렉토리(`EnterWorktree` 로 들어간 worktree 포함)에서 읽으므로 각 worktree 의 `.claude/settings.local.json` 에도 같은 항목이 있어야 한다 — `/wt` 는 새 worktree 를 만들 때 main 의 파일을 복사하고, 그전에 만든 worktree 는 그 파일의 `permissions.deny` 에 항목을 더한다(통째로 덮어쓰면 그 worktree 에만 있던 항목이 사라진다). 효과는 실측과 문서가 다르다:
- 실측(2.1.288·macOS·auto 모드): Read 도구는 규칙을 사용자 설정에 둔 상태와 이 프로젝트 로컬 설정에 둔 상태 모두에서 막혔다. Bash 는 막히지 않았다 — 사용자 설정 상태에서 `cat`·`/bin/cat`·`head`, 프로젝트 로컬 상태에서 `cat`·`sed`·`cat < 파일` 을 쟀다. rtk 훅이 `cat`·`head` 를 `rtk read` 로 재작성하지만, 재작성되지 않고 문서가 적용 대상으로 꼽는 `sed`·리디렉션도 통과해 rtk 재작성만으로는 설명되지 않는다(원인 미확인). default 모드·Grep·Glob 은 시험하지 않았고 Windows 는 미검증이다.
- 문서([permissions](https://code.claude.com/docs/en/permissions) "Read and Edit"): Read 규칙은 Grep·Glob 같은 내장 도구에는 best-effort 로 적용되고, Bash 에서 인식하는 파일 명령(`cat`·`head`·`tail`·`sed`·`tee`)과 `< file` 리디렉션에도 적용된다. 파일 이름을 적지 않는 명령(`grep -r pattern .`)이나 스스로 파일을 여는 스크립트에는 적용되지 않는다.

그래서 이 규칙은 실수로 여는 것을 줄일 뿐 막는 장치가 아니다 — 남는 경로는 위 규약(목록을 열어 보지 않는다)이 맡는다. Bash 거부 규칙은 시험하지 못해(auto 모드 분류기가 미끼 규칙 추가를 막았다) 권하지 않는다. sandbox 의 OS 수준 읽기 제한도 쓰지 않는다 — Bash 도구에서 실행한 `git commit` 의 훅도 그 제한 아래에서 돌아, 목록을 못 읽은 가드가 모든 커밋을 막을 것으로 본다(미시험).

설치 한 번:
```powershell
.\scripts\install-hooks.ps1
```

훅 디렉토리(`git rev-parse --git-path hooks`)는 머신별 → clone 후 매번 실행 필요.

`--no-verify` 로 로컬 훅은 우회된다 — 이 repo 는 main 을 향한 PR·main push 를 CI 비밀 스캔이 사후에 다시 보지만(이미 공개된 뒤 탐지), 다른 repo 와 PR 없이 push 한 feature 브랜치는 본인 규율에 의존한다. push 검사는 해석할 수 없는 입력·git 오류를 차단 쪽으로 처리한다(fail-closed). 그 때문에 가드 자체의 결함으로 모든 push 가 막히면, **사용자가 원인을 확인하고 판단한 뒤 터미널에서 직접** `git push --no-verify` 로 한 번 빠져나오거나 `$(git rev-parse --git-path hooks)/pre-push` 를 지우고, 원인을 고친 뒤 되돌린다(가드 수정을 revert 해도 그 revert 의 push 가 같은 가드를 탄다). 이것은 사람이 하는 복구 절차다 — Claude 는 훅 차단을 `--no-verify`·훅 삭제로 우회하지 않고 원인을 고치거나 보고 후 멈춘다(CLAUDE.md §8).

---

## Install (macOS)

macOS 는 PowerShell 대신 `bash` + `osascript` (알림) + `afplay` (사운드) 사용. 추가 의존성 없음 (system built-in).

### A. 새 macOS 머신 — `~/.claude/` 가 없거나 비어있을 때

```bash
# 1. clone
cd ~
git clone <this-repo-url> .claude

# 2. settings.json 배치 — clone 에 포함되지 않는다 (untracked)
#    기존 머신의 ~/.claude/settings.json 을 그대로 복사. cross-platform 이라 OS별 편집 불필요.
#    없으면 hook·statusline 이 전혀 등록되지 않는다.
#    (선택) 비공개 용어 목록 ~/.claude/private-terms.txt 도 같은 방식으로 복사 (untracked, 아래 D 절).

# 3. (optional) pre-commit / pre-push 가드 설치
cd ~/.claude
./scripts/install-hooks.sh

# 4. (optional) `gwl` 셸 단축키 설치 — worktree list (수동 1회). 상세: 아래 gwl.zsh 절.
./scripts/install-gwl.zsh

# 5. 공용 wiki — 이 repo 에는 없다(비공개 repo 의 별도 clone, 아래 E 절).
git clone <비공개 wiki repo URL> ~/.claude/wiki

# 6. Claude Code 재시작
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
#    settings.json 은 untracked 라 checkout 대상이 아님 — 기존 파일이 그대로 살아남는다.
git checkout origin/main -b main

# 4) hooks 설치
./scripts/install-hooks.sh

# 5) 공용 wiki — 이 repo 에는 없다. 아래 E 절대로 clone 한다(wiki 가 있던 머신이면 E 절 1단계부터).
```

### C. macOS 알림 권한

`osascript` 첫 호출 시 시스템 설정 → 알림 → 터미널 (혹은 Claude Code 실행 중인 앱) 권한 허용 요청 뜸. 허용해야 토스트 알림 표시.

사운드는 `/System/Library/Sounds/*.aiff` 에서 선택 (`Glass`, `Ping`, `Hero`, `Funk` 등). 기본값은 `notify-hook.js` 가 이벤트별로 지정 (Stop→`Glass`, Notification→`Ping`); 바꾸려면 `settings.json` hook command 에 3번째 인자로 사운드명 추가 (예: `node ~/.claude/scripts/notify-hook.js Stop Hero`). `Hero`·`Glass` 등은 macOS `.aiff` 명이고 Windows 는 `Asterisk|Beep|Exclamation|Hand|Question` 만 유효 — OS 에 안 맞는 값은 이벤트 기본값으로 자동 fallback (한 인자로 양 OS 를 못 맞추므로 OS별로 다른 사운드를 쓰려면 머신별 `settings.local.json` 이 아니라 직접 분기 필요).

### D. Pre-commit / Pre-push 가드 (macOS)

`scripts/pre-commit-check.sh` 가 Windows `.ps1` 버전과 동일한 규칙으로 커밋할 때는 staged `settings.json`·`plans/*.md`(tracked §10) 를, push 할 때는 push 되는 커밋(push 대상 ref 가 아직 갖지 않은 것)이 `settings.json`·`plans/*.md` 에 **추가한 줄**을 검사. 동일하게 금지 키 + 토큰/시크릿 패턴 차단. settings.json 이 untracked 라 실효 대상이 `plans/*.md` 뿐인 것도 Windows 판과 같다. `~/.claude` 의 비공개 용어 검사(`~/.claude/private-terms.txt`)도 위 Windows D 절과 같다.

설치:
```bash
./scripts/install-hooks.sh
```

훅 디렉토리(`git rev-parse --git-path hooks`)는 머신별이라 clone 한 프로젝트마다 매번 실행 필요. 가드가 모든 push 를 막을 때의 복구(`--no-verify` 로 한 번 빠져나오기·훅 삭제)는 위 Windows D 절과 같다 — 사용자가 판단해 직접 하는 절차이고, Claude 는 우회하지 않고 원인을 고치거나 보고 후 멈춘다(CLAUDE.md §8).

### E. 공용 wiki 전환 — 이미 쓰던 머신 (Windows·macOS 공통)

2026-09-30 부터 공용 wiki(`~/.claude/wiki`)는 이 repo 가 아니라 **비공개 wiki repo** 에 있다. 이 repo 는 `wiki/` 를 추적하지 않는다. 그래서 전환 커밋을 받으면(SessionStart 자동 pull 포함) 그 머신의 wiki 파일이 지워진다. 다시 받으려면 비공개 wiki repo 를 같은 자리에 clone 한다. 머신마다 한 번 한다.

Windows PowerShell 에서는 아래 명령의 `~` 를 `$env:USERPROFILE` 로 바꾼다(5.1 은 git 인자의 `~` 를 확장하지 않아 엉뚱한 폴더에 clone 된다). Git Bash 에서는 그대로 쓴다.

0. **(선택) 자동 pull 잠시 끄기** — 정리할 시간이 필요하면 전환 커밋이 들어오기 전에 `touch ~/.claude/.autopull-off` 로 그 머신의 SessionStart pull 을 멈춘다. 끝나면 그 파일을 지운다.
1. **전환 커밋을 받기 전** — 그 머신에 커밋·push 하지 않은 wiki 편집이 있는지 본다: `git -C ~/.claude status --porcelain -- wiki`, `git -C ~/.claude log origin/main..main -- wiki`.
   - 커밋하지 않은 편집만 있으면, 그 파일을 다른 곳에 복사해 두고 `git -C ~/.claude restore --staged --worktree -- wiki` 로 되돌린다.
   - push 하지 않은 로컬 커밋이 wiki 를 건드렸으면, 멈추고 그 wiki 파일을 복사해 둔다. **공개 repo 로 push 해서 풀지 않는다** — wiki 내용이 공개된다. 그 커밋을 어떻게 정리할지는 다른 파일과 섞였는지 보고 그 머신에서 정한다.
   - 그대로 두면 자동 pull 이 fast-forward 에 실패해 **조용히 멈춘다**.
2. **pull** — `git -C ~/.claude pull --ff-only`. 추적에서 빠진 wiki 파일이 지워진다.
3. **clone** — `git clone <비공개 wiki repo URL> ~/.claude/wiki`.
   - `~/.claude/wiki` 가 비어 있지 않아 실패하면(ignored `raw/` 등이 남은 경우), 다른 경로에 clone 한 뒤 남은 파일을 그 clone 으로 옮기고 폴더를 바꿔 넣는다.
   - 1 에서 복사해 둔 편집이 있으면 clone 에 다시 적용해 커밋한다.
4. **확인** — `git -C ~/.claude status --porcelain` 이 비어 있고(`wiki/` 는 무시된다), `git -C ~/.claude/wiki status` 가 clean 이다.

공용 wiki 에는 main 세션에서 쓰고 그 repo 의 main 에 직접 커밋한다. push 는 필요할 때 한다(CLAUDE.md §11·§8). 다른 머신의 wiki 는 자동으로 갱신되지 않는다 — `git -C ~/.claude/wiki pull`.

---

## Verify

설치 후 다음으로 동작 확인:

### 1. Statusline 표시
Claude Code 실행 후 화면 하단에 한 줄이 나와야 함. 사용량 조각의 앞 레이블은 세션 모델명(`model.display_name`)으로 표시됨. 예시:
```
Opus 53%(20:30) wk 72% | ctx 12% | main
```

표시 안 되면 → Troubleshooting 의 "statusline 미표시".

### 2. Notify hook 동작
간단한 작업을 끝낸 뒤 응답 완료(Stop) 시 사운드 + 알림이 나와야 함 — macOS: `Glass` + 배너, Windows: `Asterisk` + toast. 입력 대기(Notification) 시엔 다른 사운드 — macOS: `Ping`, Windows: `Exclamation`.

사운드/알림이 없으면 → "hook 미실행".

### 3. Subagent statusline
`Agent` 도구로 subagent 를 띄우면 프롬프트 아래 subagent 패널의 행이 `Review change · running · 48.2k tok (24%) · 3m 12s` 형태로 나와야 함(이름을 붙여 띄운 agent 는 앞에 `code-reviewer · ` 처럼 이름이 붙는다. 기본 표시는 `이름 또는 agent 종류 · description · tokens`).

### 4. Pre-commit guard
`.\scripts\install-hooks.ps1` 실행 후 일반 `git commit` 은 무동작 (정상). 확인하려면 `plans/` 아래 임시 plan 파일에 토큰 형태 문자열(예: `sk-` 로 시작하는 더미)을 넣고 stage 후 commit 시도 → `[BLOCKED]` 출력 + exit 1 이어야 함. (settings.json 은 untracked 라 더 이상 이 경로로 검증되지 않는다.)

---

## Components

### CLAUDE.md — 전역 작업 규칙

모든 프로젝트에 자동 로드되는 사용자 지시문. Claude Code 가 `~/.claude/CLAUDE.md` 를 모든 세션에서 읽음.

14개 섹션 (0~13):
0. 응답 언어 — 한국어, 인사말 없이 내용부터(착수 한 문장·진행 업데이트·결론 요약은 쓴다), 수사 대신 직설
1. 핵심 규칙 — 추측 금지, 코드 read 기반 답변, 근본 원인, 검증 후 "완료", 사용자 변경사항 보호, 승인은 위험기반(가역·로컬은 무확인 실행+보고 / 비가역·외부공개는 확인), 운영 자산 자가 수정 금지
2. 컨텍스트 관리 — `/clear`, `/rewind`, subagent 위임 기준, Bash 재귀 검색은 `grep -r` 대신 `rg`(`.gitignore` 준수)
3. 작업 흐름 — Setup → Explore → Plan → Implement → Verify → Report
4. 웹 검색 능동 사용 — 지식 컷오프 이후 정보, 라이브러리 버전별 동작, 이름 인지 ≠ 현재 상태 등
5. Sub-agent — 표준 순서 (plan-reviewer → 구현 → code-reviewer → simplify 체크(메인 직접)), Workflow(ultracode) subagent 는 단계별 effort 명시
6. 코드 규칙 — 동일 디렉토리 스타일, 타입 힌트, 임시 코드 표기, 부분 편집 우선(전체 재작성 지양)
7. 테스트 (TDD) — 테스트 작성 순서, 예외 조건, 인접 테스트 규모에 맞춤·임시 체크의 영구 테스트화 금지
8. Git / 보안 — destructive 명령 금지, 시크릿 출력 금지, 코드/파일 변경은 규모 불문 worktree(`/wt`)에서(gitignored 글로벌 상태 제외), **검증 통과분은 요청 없이 작업 브랜치 커밋**(push 는 요청 시만), 커밋은 하나의 목적 단위(`commit-check` 로 점검), trivial·small 종결은 로컬 ff-merge
9. Claude ↔ Codex 협업 — `plans/` 핸드오프 채널, 리뷰 매트릭스
10. `plans/` 핸드오프 규약 — slug, frontmatter, 필수 6개 + 선택 섹션(Intent·Acceptance·Review Disposition·Deferred·Workflow Findings — Intent 는 medium 이상 항상), 묶음 intent(`plans/<date>-<intent-slug>/intent.md` 하나에 plan 여럿이 `intent:` 로 링크 — 단발 작업은 plan `# Intent` 만. medium 이상은 dlc 분할 판정이 "독립 머지 가능한 복수 plan 으로 나뉘는가"를 능동으로 보고 안 나뉘면 `분할: 없음 — <근거>`)
11. 영속 프로젝트 메모리 (LLM Wiki) — 두 계층: repo `wiki/`(그 repo 의 결정·교훈) + 공용 `~/.claude/wiki/`(여러 repo 에 쓸모 있는 공개 가능한 사실·전역 자산 교훈 — 비공개 repo 의 별도 clone, 모든 repo 가 조회, 쓰기는 `~/.claude` main 세션, 다른 repo 세션은 적립 제안만), `plans/` 와 경계 (일시적 vs 영속). 공개 점검 — `~/.claude` 는 공개 repo 라 이 repo 의 **모든** 커밋·push 에 회사·비공개 정보 금지(`private-terms.txt` 목록으로 기계 백스톱)
12. 피드백 메모리 — 작업 방식 교정을 `memory/`(type: feedback) + `MEMORY.md` 인덱스로 영속화해 다음 작업에 반영. 보편·중대 규칙은 이 `CLAUDE.md` 로 승격.
13. 실수·교훈 로그 — 반복 실수를 대상 계층 wiki 의 교훈 페이지(상세 — 공용은 `decision/lesson-*`, 다른 repo 는 그 WIKI.md 형식. 전역 워크플로우 교훈은 공용) + `MEMORY.md` 인덱스(자동 상기 — 프로젝트별이라 다른 repo 에는 공용 index 조회로)로 적립해 다음 구현에서 회피. 인덱스 주입은 권고이지 강제 아님.

세션 시작 시점 자동 적용. 프로젝트별 추가 규칙은 per-repo `CLAUDE.md` 에 둘 수 있고, 글로벌 + 프로젝트 둘 다 로드됨.

끝줄 `@RTK.md` 는 rtk 명령 안내를 import 한다. `RTK.md` 는 whitelist `.gitignore` 로 추적되지 않고, `rtk init -g` 를 실행한 머신의 main checkout(`~/.claude/RTK.md`)에만 생긴다(bootstrap 이 쓰는 `rtk init -g --hook-only` 는 훅만 등록하고 RTK.md 는 만들지 않는다). worktree 세션은 worktree 의 CLAUDE.md 사본을 싣지 않고(`claudeMdExcludes`, 아래 settings.json 절) 사용자 전역 `~/.claude/CLAUDE.md` 가 이 파일을 불러오므로 세션이 받는 내용은 같다. 빠지는 경우는 그 머신에 `RTK.md` 가 아예 없을 때뿐이고(rtk 재작성 훅은 RTK.md 없이도 동작한다), 그때도 추적하거나 worktree 로 복사할 필요는 없다 — 안내가 필요하면 그 머신에서 `rtk init -g` 를 실행한다.

### statusline.js — 메인 statusline

Claude Code 의 [Custom Status Line](https://code.claude.com/docs/en/statusline) 으로 등록되어 약 2초 주기로 stdin 의 세션 JSON 을 받아 한 줄을 출력.

표시 항목:
- **Claude 5-hour + weekly rate limit**: `<모델명> NN%(HH:MM) wk NN%`(`model.display_name`, 없으면 `claude`) — 각 창(`rate_limits.five_hour`·`seven_day`)의 남은 percentage, 5시간 창은 reset 시각도. 두 창은 독립적으로 빠질 수 있다 — Claude Code 는 최신 API 응답에 그 창의 `anthropic-ratelimit-unified-5h-*`/`7d-*` 헤더가 없거나 reset 시각이 지나면 그 창을 입력에서 뺀다(2.1.285 바이너리 확인)
- **Context window**: `ctx NN%` — 현재 세션의 컨텍스트 사용률
- **Git branch + worktree**: `main` 또는 `feature-x @wt:gallant-hodgkin` — 현재 cwd 기준

외부 의존은 git 뿐이고 try/catch 로 감싸져 있어 실패하면 branch 부분만 빠지고 나머지는 정상 동작. stdin 이 `null`·빈 값·깨진 JSON 이어도 exit 0. stdin 이 3초 안에 닫히지 않으면 출력 없이 exit 0 으로 끝난다. 시한이 없을 때 Windows 에서 부모 셸이 죽은 `node statusline.js` 가 며칠씩 남아 그 순간의 cwd(worktree)를 계속 잡는 것을 관찰했다(공용 wiki `windows-bash-tool-orphan-processes`). 하니스가 셸만 끝내고 stdin 을 닫지 않아 'end' 가 오지 않은 것으로 추정한다(하니스 내부는 확인하지 못했다). 그래서 터미널에서 직접 실행할 때는 입력을 넘긴다 — 예: `echo {} | node statusline.js`(넘기지 않으면 3초 뒤 빈 출력으로 끝난다).

background task 표시(`✻ N bg`)는 2026-09-25 제거했다 — tasks 디렉토리에는 foreground Bash 출력도 쌓여 background 와 구분할 수 없고(`refreshInterval: 2` 라 Bash 를 돌릴 때마다 뜬다), macOS 에서는 경로도 틀려 한 번도 뜬 적이 없었다. background subagent 는 프롬프트 아래 subagent 패널과 `/tasks` 가 보여 준다.

### subagent-statusline.js — subagent statusline

`subagentStatusLine` 으로 등록되어 subagent 패널의 행을 그린다. 입력은 `{columns, tasks[]}`(task 마다 `id`·`name`·`description`·`status`·`startTime`(epoch ms)·`tokenCount`·`contextWindowSize` 등), 출력은 행마다 `{"id","content"}` JSON 한 줄이다([문서](https://code.claude.com/docs/en/statusline#subagent-status-lines)). content 는 `name · description · status · <N>k tok (P%) · Xm Ys` — 없는 조각은 빼고(`name` 은 이름을 등록한 agent 에만 오며, 기본 표시가 대신 쓰는 agent 종류는 입력에 없다), 경과는 `running`·`pending` 일 때만 붙인다(입력에 종료 시각이 없어 끝난 행의 경과가 계속 늘기 때문). `columns` 를 넘으면 description 부터 줄인다(글자 단위, 한글·CJK·이모지는 2칸). 비율은 `tokenCount / contextWindowSize` 로, 출력 토큰이 겹쳐 세여 100% 에서 자르는 근사치다. 문자열 id 가 없는 task 와 `columns` 가 0 일 때는 기본 표시로 남긴다. stdin 3초 시한은 `statusline.js` 와 같다(같은 대기 구조라 같은 고아 누수가 날 수 있다).

### agents/ — 4개 subagent

`Agent` 도구로 호출. CLAUDE.md §5 의 표준 순서 (plan-reviewer → 구현 → code-reviewer → simplify 체크(메인 직접, dlc 13단계)) 가 기본. frontmatter 는 `model` 을 단계별로 고정한다 — reviewer 3종 `opus`, researcher `sonnet`. 별칭이라 모델 세대 교체 시 수정 지점은 0이고, 세션이 Fable 이어도 리뷰·조사가 Fable 캡을 태우지 않는다. `effort` 는 두지 않아 subagent 가 세션 effort 를 물려받는다(sub-agents 문서 "Default: inherits from session"). 세션 effort 는 명시 선택(`/effort`·`--effort`·env) > settings 의 모델별 `modelSettings` > 모델 기본값 순으로 정해진다. user settings 에는 effort 저장값을 두지 않아(2026-09-29) project·local·managed settings 나 `--settings` 가 정하지 않는 한 모델 기본값으로 돈다 — 모델별 기본값은 `wiki/pages/entity/anthropic-claude-models.md`, 2026-09-24 M12 결정(Opus 5.5 `medium`, `plans/2026-09-24-prompt-audit-apply`)이 그 기본값과 같아 키를 지운 경위와 되돌리는 방법은 `wiki/pages/decision/effort-global-xhigh.md`. 세션 모델과 다른 모델로 고정된 subagent 가 어떤 레벨을 받는지는 문서에 없다(❌ — M12 plan 의 미확인 항목). 근거·precedence·함정은 `wiki/pages/decision/model-stage-tiering.md` 와 `wiki/pages/entity/claude-code-model-selection.md`.

> ⚠️ 고정에는 **자동 폴백이 없다**. Opus 한도 소진 시 plan-reviewer/code-reviewer 는 `Agent terminated early due to an API error` 로 실패하고, 둘 다 CLAUDE.md §5 의 **필수 게이트**라 dlc 가 멈춘다. 비상 레버는 `CLAUDE_CODE_SUBAGENT_MODEL=<별칭>`(예: `sonnet`)**과 `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`(v2.1.257+)을 함께** 설정하는 것이다 — v2.1.251 부터 env 는 frontmatter 보다 뒤라 혼자서는 고정을 덮지 못한다. FORCE 는 researcher·빌트인 Explore/Plan 까지 같은 모델로 돌리므로, 범위를 좁히려면 `agents/*.md` 의 `model:` 을 직접 바꾼다. 메인 모델을 따르게 하려면 FORCE 만 켠다(빌트인 Explore 는 Claude API 에서 Opus 상한 유지). `CLAUDE_CODE_SUBAGENT_MODEL=inherit` 은 미설정과 같아(v2.1.196+) 아무 효과가 없다.

| 파일 | 호출 시점 | 핵심 책임 |
|---|---|---|
| `plan-reviewer.md` | Plan 단계 직후 (비사소한 모든 구현 계획) | 누락 케이스·잘못된 가정·영향 범위·rollback·근본 원인 비판적 발굴 + **가장 위험한 단계 지목**·**기각한 대안이 `# Decisions` 에 남았나**·**dlc ⚠️ self-flag 우선 검토**·**medium 이상 plan 의 `# Intent`(`분할:` 줄 포함) 반박**·**묶음 모드(dlc 분할 판정의 `# Plans` 경계 — 15항)**. public API / DB schema / migration / 보안 / 아키텍처 / 권한 변경 시 필수. |
| `architecture-reviewer.md` | 트리거 기반 (자동 호출 대상 아님) | 설계 결정 — 의존 방향·레이어 경계·객체 생명주기·DI/IoC·인터페이스 위치·테스트 가능 구조. public API / proto / DB schema / auth 변경, 신규 service·repository·client, DI 변경, 2개 이상 레이어 변경, 150줄 이상 diff, 또는 설계 의문 명시 시. |
| `code-reviewer.md` | 구현 직후 (코드 변경이 있었던 모든 흐름) | 버그·보안·테스트 누락·예외 처리·성능·backward compatibility·근본 원인·설계고도(altitude)·관례(conventions)·**plan 대비 컴플라이언스**(plan 경로를 받았을 때만, 기본 Minor — 어느 쪽이 낡았는지 판정은 메인). Find→Verify 2-pass (report-everything 후 self-refute, verdict CONFIRMED/PLAUSIBLE/REFUTED). 통과 검토 금지, 비판적 발굴 목적. |
| `researcher.md` | 외부 사실 조사 필요 시 (어느 단계에서든) | 라이브러리 버전별 동작·마이그레이션·최신 API, 정확한 에러 메시지 매칭, 릴리스 노트·CVE·RFC, 지식 컷오프 이후 정보, 함수/플래그 실존 여부 불확실 시. |

각 agent 의 frontmatter `tools` 필드가 권한 범위를 제한 (예: researcher 는 Edit 권한 없음, code-reviewer 는 Bash 가능). agent 별 출력 형식과 호출 조건은 각 파일 본문 참고.

### skills/dlc/ — 자동 개발 사이클

`/dlc` 명시 호출 또는 비자명한 코드 변경 시 적용하는 개발 사이클 오케스트레이션. 규모 (trivial / small / medium / structural) 를 판정해 단계를 gate — 오타 1줄은 *절차*를 즉시 통과(worktree 는 규모 불문 경유), structural 변경은 explore → plan → 리뷰 → TDD → 구현 → 리뷰 → simplify → 검증 전체를 돈다.
- 메인이 hub, 리뷰/검토(plan-reviewer, architecture-reviewer, code-reviewer)와 **최종 검증**(격리 runner·general-purpose, 실행만 — 메인이 명령·worktree cwd 지정)은 격리 subagent. 구현·통합·검증 판단·실패 fix·최종 판단은 메인.
- **⚠️ self-flag**(3단계, 조건부): 계획을 쓰는 메인이 우려를 직접 신고한다 — 닫힌 트리거 3종(제약 동시 미충족·동급 규약 상충·⚠️추정 의존 설계)일 때만 `# Decisions` 에 한 줄, 아니면 침묵("우려 없음"은 쓰지 않는다). 이 repo 의 우려 장치가 전부 격리 리뷰어 쪽에 있어 메인의 낮은 확신 지점이 드러나지 않던 구멍을 메운다. 7단계에서 리뷰 지적과 함께 먼저 처분(`resolved`/`accepted-risk`/`deferred`).
- **계획 전 decision 조회**(3단계 앞, 필수): 두 wiki index 를 대상 자산 이름·작업 종류로 조회해 걸린 결정을 plan `# Decisions` 첫 줄에서 따르거나 뒤집는다(뒤집으면 근거·사용자 승인). 같은 세션의 분석에서 이어진 계획이 Explore 조회를 건너뛰어 기존 결정과 충돌한 사례(2026-09-28) 대응.
- simplify 체크(13단계)는 메인이 직접 수행 — 모든 격리 spoke 는 read-only. substantive 수정 시 targeted 재검증.
- `<ROOT>/plans/<YYYY-MM-DD>-<slug>/<slug>-plan.md` 가 subagent 간 단일 공유 채널 (메인만 write). 경로 규약은 CLAUDE.md §10.
- codex 병행 검토 호출 규약은 `docs/codex-review.md` (phase 당 codex owner 1개 지정으로 중복 호출 방지, Windows/PowerShell fallback 포함), 한도 오류는 세션 스크래치 마커 `codex-unavailable` 로 캐시해 같은 세션의 다음 reviewer 가 재시도하지 않음). 정본 명령은 프롬프트를 스크래치 파일로 넘기고 `--skip-git-repo-check` 를 쓰지 않는다(사유는 §3 — worktree 격리 가드).
- SKILL 본문엔 진입 게이트·규모 gate·16단계 표·닫힌목록·안전 규칙만 두고, 특정 분기에서만 찾는 절차 상세(요구사항 명확화 심화·조사 프로토콜 elaboration·wiki 연계 메커닉·Workflow Findings 기록형식·격리 runner 계약/simplify 체크리스트)는 `docs/dlc-details.md` 로 분리(자동 로드 안 됨 — 해당 분기 진입 시 Read).
- **목적 단위 커밋**(medium 이상·목적 2개+): draft plan 에 `커밋 단위:`(고유 제목)를 선언하고, 단위마다 targeted 검증 통과 후 그 경로만 커밋한다. 커밋된 단위의 후속 수정은 `git commit --fixup`, plan 등 기록 파일은 16단계 마지막 커밋에만(앞 단위에 넣으면 3-way 충돌). 공유 파일은 앞 단위가 동작하는 데 필요한 변경까지 앞 단위에. 단위 커밋이 있으면 리뷰·simplify 범위는 `<base>...HEAD`+작업트리.
- **16단계 마무리에 커밋 편입**: `evidence gate → 판정(DONE/BLOCKED/NEEDS-HUMAN) → plan 업데이트 → 정식 완료 커밋(DONE 만) → commit-check → 알림(필요할 때 최대 1회) → Report`. **판정은 작업을 끝낼 때만** — 고치는 중이면 판정 대상이 아니다. DONE 은 acceptance 충족이지 plan 종결이 아니라 `status: done` 을 박지 않는다(§10 대로 머지·승인 시점. 미리 박으면 `/c` 가 통합 대기 작업을 건너뛴다). BLOCKED(자원·사실을 **받아야** 함)는 `status: blocked`, NEEDS-HUMAN(대안을 **골라야** 함)은 `status: in_progress` + `# Next` — 후자를 blocked 로 접으면 정상적인 결정 대기가 `plan-blocked` failure telemetry 로 집계된다. 둘 다 정식 완료 커밋 금지(§8 — 이미 만든 단위 커밋은 유지), 보존이 필요하면 `/e` WIP. no-progress 정지는 "1회차 뒤 전략 변경, 그러고도 개선 없으면 2회차에서 정지" + 테스트·acceptance 를 바꿔 카운터를 되돌리는 것 금지. 커밋 **규칙**(요청 없이 커밋·stage 범위·커밋 안 하는 경우·`--no-verify` 금지)은 CLAUDE.md §8 이 단일 소스이고 **전역**(dlc 를 안 타는 흐름·타 repo 에도 적용), SKILL 커밋 bullet 은 절차(경로 확정·메시지·실행 폴백)만 담는다. `/e` 의 `wip:` 체크포인트와 구분 — 여기는 검증 통과한 정식 커밋.
- **evidence·라우팅 hook** (`scripts/dlc-*.js`, `settings.json` 등록, fail-open): `dlc-task-router`(UserPromptSubmit — 디버깅/render 키워드에 discipline 주입), `dlc-evidence-ledger`(PostToolUse — 변경·검증 기록 + 문서 drift dirty flag), `dlc-early-stop`(Stop — 변경 후 검증 누락 · **문서화 표면↔README/index drift**(판정은 `dlc-doc-drift.js`) · plan drift · 결론 블록 누락 시 capped 1회 경고). plan `# Acceptance` evidence gate 의 보조 누락방지망 — 검증 *성공* 판정은 acceptance(메인)가 단일 소스. `CLAUDE_DLC_EARLYSTOP_OFF=1`(검증)·`CLAUDE_DLC_DOCDRIFT_OFF=1`(문서)·`CLAUDE_DLC_PLANDRIFT_OFF=1`(plan)·`CLAUDE_DLC_CONCLUSION_OFF=1`(결론 블록) 로 각각 비활성(holdout — `settings.json` `env` 또는 셸 프로필에 세팅). syntax 검사 + 단위테스트는 CI `lint.yml`.

### skills/c/ — plan 이어가기

`/c` 로 현재 worktree/repo 의 진행 중인 plan(§10)을 찾아 **남은 작업 + plan↔실제(git/코드) sync 상태**를 진단하고, 어긋나면 plan 을 보정한 뒤 `# Next` 가 명확하면 이어서 실행(멈춤 예외 5종).
- branch→plan dir 매칭(§10), 실패 시 `in_progress`/`blocked` plan 목록 제시 후 사용자 선택 (추측 자동선택 안 함).
- `plans/` 가 worktree(브랜치)별 독립이라 현재 repo + main worktree 양쪽 `plans/` 를 탐색(tracked 지만 브랜치마다 내용이 다르다).
- 확인·sync 진단·plan 보정 후 **`# Next` 가 명확하면 이어서 실행**(멈추는 예외 5종: `blocked`·plan 후보 다수·`# Next` 재구성·파괴적/외부공개 액션·`done`). 그 브랜치 PR 의 **사람** 리뷰 코멘트를 intake 해 코드 지적은 `# Next`, 작업방식 지적은 feedback memory 판정으로 넘긴다. plan 이 없으면 새로 만들지 않음 — 신규 plan 생성은 dlc 몫.

### skills/e/ — plan 마무리

`/e` 로 진행 중이던 plan(§10)을 **실제 git/코드 상태로 동기화 기록**하고 작업을 마무리. c(이어가기)의 대칭.
- **마무리 recap(CLAUDE.md §3-6)**: 최종 메시지는 **맨 끝을 `## 결론` 블록(§3-6 5항목)으로**, 마무리 선택지(정리/이어가기/종료)는 아래 worktree 정리 제안 + 다음 세션 `/c` 안내가 겸한다. Jira task 본문 반영만은 외부 쓰기라 preview 후 별도 사용자 승인을 받는다.
- 체크포인트 모드에서는 uncommitted 변경을 작업 브랜치에 **임시(WIP) 커밋**으로 보존 — `main`/`master` 직접 커밋·push 는 안 함(§8), `.env`·key 등 위험 파일은 커밋 보류 후 확인.
- **머지 모드 `/e merge`**(`/e 머지` — 이 두 토큰만): PR 조회·사전 점검 → 정리 안 된 커밋 검사(`commit_units.py pending` — 미게시 `wip`·`fixup!` 류는 commit-check 제안·승인 후 정리하고 보류하면 중단, 게시분·로컬 ref 가 붙잡은 것·재구성할 수 없는 범위의 것은 진행 여부를 묻고, merge 커밋을 불허해 squash 하는 repo 면 보고만 한다) → push → PR(open 재사용, merged/closed 는 새로) → plan `done` 커밋 → `gh pr checks --watch`(exit code + bucket 재조회) → `gh pr merge --merge --match-head-commit`(`--delete-branch` 금지) → 결과를 MERGED/QUEUED/REJECTED/UNKNOWN 으로 분류, MERGED 면 `git fetch` 후 5~8단계. REJECTED 만 plan 을 `in_progress` 로 복구해 done 인 미머지 plan 을 남기지 않는다. 진입 게이트·닫힌 목록은 SKILL, gh 명령·시나리오 표는 `docs/worktree-lifecycle.md` §E.
- `# Progress`/`# Next`/`# Decisions`/`status`/`updated` 를 사실 기반으로 갱신 → 다음 세션이 `/c` 로 곧장 이어받음.
- 체크포인트 모드에서는 done 자동 전환 안 함 (확정 완료 신호 + 사용자 확인 시만, 기본 `in_progress` 체크포인트; 머지 모드의 done 은 `/e merge` 가 그 확인). plan 없으면 새로 만들지 않음 — 임시 커밋 + 보고만.
- worktree 에서 작업이 `done`·clean·merged 이고 내부에 잃을 ignored 산출물(plan·`.env`)이 없으면 **묻지 않고 worktree + 로컬 브랜치를 정리**한다(CLAUDE.md §8(a) — 누가 머지했는지 불문). merged 판정은 `origin/<default>` 뿐 아니라 **로컬 `main` 머지도 인정**한다(push 하지 않는 워크플로우에서 자동 정리가 실효되지 않도록). 격리된 worktree 세션에서는 worklog·상태 재수집 헬퍼가 worktree 안에서 가드에 거부될 수 있어, 6단계 전에 main 으로 먼저 나온 뒤 돌린다(나올 수 없는 세션은 전처럼 worktree 안에서). 6단계 worklog 가 실패로 끝났으면(비0 종료·헬퍼 거부·자격증명 불완전 — 세션·티켓·토큰 없음 같은 정상 skip 은 제외) 다시 등록할 수 있게 worktree 를 남긴다. 삭제한 브랜치 tip sha 를 보고(`git branch <name> <sha>` 로 복구 가능). **확인이 필요한 것(§8(b))**: **원격 브랜치 삭제**(`git push origin --delete`)는 항상, 그리고 안전조건 미충족/불확실(dirty·squash-merge·미보존 산출물)·`wt rm <이름>` 직접 호출·`--force`·`branch -D`. 삭제 시 main 으로 빠져나간 뒤 `git worktree remove`(내가 띄운 점유 프로세스는 먼저 회수). merge/done 후 정리를 방치하지 않는 규약은 CLAUDE.md §8.
- **`collect-state.sh`** (헬퍼): 마무리 2단계·7단계의 읽기전용 git 신호(worktree 위치·dirty·upstream/unpushed·base merged·**로컬 default merged**(`localDefault`·`mergedToLocalBase`)·ignored)를 평문 `key:value` 로 1회에 수집 — 분산된 개별 git 호출의 왕복을 줄인다. read-only(판정·삭제·파괴 명령은 SKILL 메인), 각 점검 fail-safe(실패 필드 none/unknown), `unpushedStatus` 는 false 와 unknown 을 구분해 false-positive 삭제를 막는다.
- **`docs/worktree-lifecycle.md`** (참조, 자동 로드 안 됨): `/e` 의 상태 수집 필드 카탈로그·머지 모드 gh 메커닉·시나리오 표(§E)·worktree 삭제 판정 6조건 메커닉·정리 실행 폴백·복귀 pull 의 git 세부를 담는다. SKILL 본문엔 게이트·닫힌목록·안전 규칙만 남기고 세부는 여기로 이관(해당 분기 진입 시 Read — `docs/codex-review.md` 와 같은 참조 패턴).

### skills/wt/ — Git worktree 빠른 관리

`/wt` (목록) · `/wt <N>` (N번째 worktree 로 이동) · `/wt <기존이름>` (정확일치 worktree 로 이동) · `/wt <요청사항>` (확인 없이 worktree 신규 생성 → 그 안에서 `dlc` 로 작업) · `/wt ? <막연한 설명>` (질문 모드 — 구체화 후 생성) · `/wt rm <name>` (제거) 로 worktree 관리. 컨벤션:
- worktree path: `.claude/worktrees/<name>` (현재 repo 기준)
- 브랜치 이름 = worktree 이름 (1:1)
- `EnterWorktree(path: <abs>)` 로 진입 — `name` 인자 사용 금지 (Claude Code 의 `worktree-` prefix 자동 부착 회피)
- 정수·`rm`·기존 worktree 정확일치가 아닌 텍스트는 **요청사항**으로 간주 → 영문 kebab-case slug 파생 → **확인 없이 생성**(위험기반 승인 — CLAUDE.md §1: 로컬·가역이라 묻지 않고, base·`.env`·stale·near-miss·`/wt rm <slug>` 되돌리기를 보고) → 요청사항 원문을 `dlc` task 로 전달 (dlc 없는 빈 worktree 단순 생성은 폐지). 삭제 계열(`rm`·`--force`·`branch -D`·원격 삭제)은 비가역이라 확인 유지. `rm` 은 확인 질문 전에 그 worktree 의 worklog 미리보기로 등록할 AI 작업시간(티켓·합계)을 알린다(지운 worktree 의 시간은 등록할 수 없다)
- 접두 `?` (`/wt ? <막연한 설명>`)는 **질문 모드** — AskUserQuestion 으로 요구사항을 구체화한 뒤 같은 요청사항 생성 경로로 합류 (접미 `?` 는 의문형 요청과 충돌해 미사용)
- **신규 생성 시 ignored 설정 자동 복사**: main worktree 에서 ① basename 이 정확히 `.env` 인 파일 ② repo-relative 경로가 정확히 `.claude/settings.local.json` 인 파일을 동일 상대경로로 복사(이미 있으면 skip, 실패는 경고만·worktree 유지). ②가 필요한 곳은 Windows 등 repo 루트의 파일을 쓰지 않는 경우다(목록은 `skills/wt/references/env-copy.md`) — 로컬 설정을 세션의 작업 디렉토리(`EnterWorktree` 로 들어간 worktree)에서 읽어, 복사하지 않으면 **권한 허용목록이 0개**로 시작하는데, CLAUDE.md §8 이 코드 변경을 규모 불문 worktree 에서 하도록 강제하므로 실사용 경로가 전부 여기 해당한다. 그 밖의 경우(보통의 macOS·Linux)는 2.1.211 부터 worktree 세션도 main checkout 의 `.claude/settings.local.json` 을 읽으므로([settings](https://code.claude.com/docs/en/settings) 문서, 2.1.288 macOS 실측) 복사본은 보조다. predicate 는 **앵커드 정확일치**(basename 매칭이면 `.bak` 백업이나 repo 루트의 동명 파일까지 딸려온다). 신규 생성 경로만 덮으므로 그 예외 환경의 기존 worktree 는 수동 복사.
- `references/` (자동 로드 안 됨): SKILL 본문엔 절차 스텝·안전 게이트만 두고, 상세 메커닉은 해당 분기 진입 시 Read 하는 참조 doc 으로 분리 — `env-copy.md`(자동 복사 후보/제외 — `.env` + `settings.local.json`)·`rm-recovery.md`(생성 git 시퀀스·self-heal·rm 실패 복구). `docs/codex-review.md`·`docs/worktree-lifecycle.md` 와 같은 참조 패턴.

### skills/wiki/ — LLM Wiki (영속 프로젝트 메모리)

`/wiki <ingest|query|lint>` 로 영속 프로젝트 메모리를 운영. 두 계층 — 현재 repo 의 `wiki/`(그 repo 의 결정·교훈)와 공용 `~/.claude/wiki/`(여러 repo 에 쓸모 있는 공개 가능한 사실·전역 자산 교훈). query 는 `wiki_search.py` 로 공용 wiki(cwd 무관)와 현재 repo 의 wiki 를 검색하고(stdlib, 한글 2-gram 이라 조사가 붙어도 맞고 결과마다 계층·절대경로·index 요약·맞은 본문 줄(섹션과 줄 범위)·링크로 이어진 관련 페이지를 낸다. 구조 질의 `--links-to <stem>`(그 페이지를 가리키는 링크)·`--open`(미해결 callout)도 둔다. exit 0 결과·1 없음·2 찾을 wiki·단어·category·stem 없음이나 질의 모드 사용 오류·설정·읽기 오류·출력을 끝까지 못 냄(stdout 을 먼저 닫음)·예상 밖 오류 — 첫 줄에 찾은 wiki·쪽수를 적어 "없음"을 판단할 수 있다. dlc 계획 전 조회와 CLAUDE.md §11 작업 시작 조회도 이것을 부른다), ingest 는 대상 계층을 먼저 정한다 — 다른 repo 세션이나 `~/.claude` worktree 세션에서 공용 대상이면 쓰지 않고 `~/.claude main 세션에서 /wiki ingest <요약 · 공개 근거 · 출처(공개/비공개)>` 제안을 Report·plan `# Deferred` 에 남긴다. 공용 wiki 는 비공개 repo 를 `~/.claude/wiki` 에 별도 clone 한 것이고(이 repo 는 추적하지 않는다 — 설치는 Install E 절), main 세션에서 쓰고 그 repo 의 main 에 직접 커밋한다. 저장소는 비공개지만 모든 repo 세션이 읽고 옮겨 적으므로 페이지·sources·index·log·커밋 메시지에 회사·조직명·내부 호스트/IP·코드명·티켓 키·비공개 repo 이름/경로를 두지 않고(단일 정의는 CLAUDE.md §11 공개 점검), 출처가 비공개이거나 불명인 제안은 커밋 전 diff 를 확인받는다. 현재 repo 판정은 `[ "$(git rev-parse --path-format=absolute --git-common-dir)" -ef "$HOME/.claude/.git" ]`. ingest(raw·작업지식 → 상호링크 페이지 + index/log) · query(누적 페이지로 답 → 가치 있으면 현재 repo wiki 에 filed) · lint(현재 repo wiki 의 orphan·dead link·frontmatter 형식·covers 신선도·대표 질문·모순 점검·보고). 기계 점검은 `check_links.py`(링크·orphan·index 동기화)와 `wiki_check.py`(stdlib 단일 파일, config 는 Python 3.11+)가 한다. `wiki_check.py schema` 는 frontmatter 형식을 보고(규칙은 `<wiki>/wiki-check.toml` 로 그 wiki 의 WIKI.md 에 맞추고 없으면 공용 WIKI.md 규약, 템플릿 `templates/wiki-check.toml`), frontmatter 판정의 정본이다. `wiki_check.py stale` 은 covers 신선도를 본다 — 페이지 frontmatter `covers` 에 걸린 코드가 바뀌었는데 페이지가 그대로인지를 `--branch`(CI·push 전)·`--stop-hook`(Stop hook 어댑터, 언제나 exit 0)으로, `verified_at`(대조한 때의 covers 파일 내용 지문)이 지금 지문과 같은지를 `--report`(이력 무관)로 본다. 규약 정본은 SKILL.md 신선도 절이고, hook·CI 등록은 하지 않는다. `wiki_check.py smoke` 는 config `[smoke]` 에 적은 대표 질문마다 답할 페이지·index 등재·본문 근거가 있는지와 작업 중 흔적(브랜치 이름·`status: in_progress`·사용자 패턴)이 페이지에 없는지를 본다 — `[smoke]` 가 없으면 검사 대상 아님(exit 0). 배치 규칙은 CLAUDE.md §11, 형식은 각 wiki 의 `WIKI.md`. `plans/`(일시적 작업 핸드오프)와 달리 작업을 **가로질러 누적**. raw 원문은 gitignored·읽기 전용, 페이지만 tracked(공용 wiki 는 그 비공개 repo 에서). dlc 연계는 CLAUDE.md §11.

### skills/improve/ — 자기개선 loop 분석 축 (구 /audit 흡수)

`/improve` 로 ① 운영 자산(skills·agents·CLAUDE.md·settings.json·MEMORY.md·wiki)의 **자산 간 참조 정합**(구 `/audit` 승계)과 ② hook 이 자동 누적한 **dlc 신호(telemetry)** 를 함께 분석해 **개선 후보를 랭킹**으로 제시. **수정은 제안만**(§1 자가수정 금지) — 승인 시 wt→dlc 별도 작업. loop 구조: 수집(hook 자동, `dlc-signal.js`) → 분석·제안(`/improve`) → 반영(승인 후 wt→dlc) → 효과 확인(다음 `/improve` 의 신호 추이). 최종 보고 직전에 `node ~/.claude/scripts/dlc-signal.js mark` 로 `last-improve` 마커를 갱신해 SessionStart 의 "/improve 권장" 카운트를 0 부터 다시 센다(스킬 7단계 — `/improve` 의 유일한 write).
- 기계 점검+집계 `skills/improve/improve.sh`(read-only): settings hooks↔scripts 실존 · MEMORY 인덱스↔파일 양방향 · CLAUDE.md 가 참조한 agent 실존 · skill·agent frontmatter 형식(`frontmatter-lint.js` — git 이 아는 파일만) · 죽은 스크립트 후보(require 그래프·수동유틸 화이트리스트로 오탐 차단, info 만) · **wiki 비추적 게이트**(이 repo 가 `wiki/` 를 추적하면 error — 공용 wiki 는 비공개 repo) · 공용 wiki(`~/.claude/wiki`, override `CLAUDE_IMPROVE_WIKI`) index↔pages 개수 · **plan-lint**(tracked plan 전수 §10 무결성) · **신호 집계**(`node scripts/dlc-signal.js summary` — failure/activity 축, session-unique 우선) · **네이티브 중복 대장 신선도**(⑨ — `node scripts/native-overlap-lint.js`, 아래 참조).
- **`improve.sh deep`**(opt-in 광역 관측, 여전히 read-only·secret 미출력): ⑩ 주입·로드 표면 크기(`wc -c` — CLAUDE.md·SKILL·agent, 토큰 압박) · ⑪ 사용량 카운트(`node scripts/usage-count.js` — transcript JSONL 파싱해 skill·subagent·codex 호출 빈도, **카운트·slug 만**, 원문·파일명·경로·args 미출력) · ⑫ MCP 서버 인벤토리(`~/.claude.json` **이름만**, 값·env·secret 미출력) + ⑨ 가 delta 창을 한 줄 더 출력. 판단·제안 경로는 기본 4단계와 동일(측정→제안, 수정 금지).
- **네이티브 중복 점검**(SKILL §6, deep 전용·주기): Claude Code 네이티브가 흡수한 기능과 겹치는 자작 부품을 `keep`/`watch`/`retire` 로 재판정해 wiki 대장 `~/.claude/wiki/pages/decision/native-overlap-ledger.md` 에 누적. 1~5 가 "자산이 서로 어긋났나"라면 이 축은 "자산이 **아직 필요한가**" — 유일하게 밖(네이티브)을 기준으로 삼는다. 대장 `checked_version` 이후 changelog 만 읽는 **delta 창** 방식이라 전수 조회를 피한다. 주기 임계 45일(`CLAUDE_IMPROVE_NATIVE_MAX_AGE_DAYS`, 근거: 실측 6주 36릴리스), 대장 경로 override `CLAUDE_IMPROVE_LEDGER`. **`/improve` 는 대장을 쓰지 않는다** — 판정은 초안, write 는 승인 후 `/wiki ingest`(§1·§11·§13 승인 게이트).
- 의미 점검(LLM): 문서 간 모순 · 중복 trigger · 죽은 규칙 + wiki `workflow-failures` 표·MEMORY 인덱스·plan `# Workflow Findings` 대조.
- **역할 경계**: README↔surface drift 는 `dlc-doc-drift` hook, wiki 내부 무결성·**대장 write** 는 `/wiki lint`·`/wiki ingest` 영역 — improve 는 재판정하지 않고 신호의 **사후 집계**만(중복 회피).

### skills/commit-check/ — 커밋 단위 점검·재구성

브랜치의 **미게시** 커밋이 "리뷰 가능한 하나의 목적 단위"인지 점검한다. 합치기(fixup)·파일 단위 나누기·순서·메시지 수정 제안 표를 만들고, 사용자가 승인하면 코드 내용은 그대로 둔 채 커밋 경계만 재구성한다. dlc 16단계(커밋 뒤)와 `/e merge`(push 전, 정리 안 된 커밋이 있을 때)에서 호출하고 `/commit-check` 로도 부른다.
- `commit_units.py` 가 수집(`collect`)·패치 조회(`show`)·재구성(`apply`)·push 전 분류(`pending <upstream>`)를 맡고, 판단은 모델이 SKILL.md 기준으로 해 JSON 계획으로 넘긴다. `collect` 는 `fixup!`·`squash!`·`amend!` 커밋의 합칠 대상(`fixup_of`)을 git `rebase --autosquash` 의 대상 선택을 근사해 표시한다(sha 접두·제목만, ref 이름 미해석). `pending` 은 읽기 전용으로 `<upstream>..HEAD` 의 `wip`·`fixup!` 류 커밋을 `rewritable`/`published`(원격 추적 ref)/`held`(다른 로컬 브랜치·태그)/`blocked`(merge 커밋·서명·기본 브랜치·git 버전 등 범위 전체 거부 조건 — apply 와 같은 헬퍼로 미리 본다. 충돌·hook 같은 계획별 거부는 apply 때 드러난다) 로 나눈다. 따로 두는 이유는 `collect` 의 제외가 원격·로컬 ref·태그를 한데 묶어서, "force-push 없이는 못 고침"과 "로컬 ref 를 치우면 고칠 수 있음"을 가르지 못하기 때문이다.
- 재구성은 plumbing(`merge-tree --write-tree` + `commit-tree`)으로 사용자 index·작업트리 밖에서 만든다. author·트레일러는 원본에서 옮겨 적고, 최종 tree 동일과 커밋별 파일이 계획 범위 안인지를 검증한 뒤에만 백업 ref(`refs/commit-check/<branch>/<UTC>`, 최근 5개) 생성·오래된 백업 삭제·브랜치 이동을 `update-ref --stdin` 트랜잭션 하나로 수행한다. 실패하면 ref·index·작업트리는 호출 전 그대로다(repo commit-msg hook 의 자체 부작용은 예외).
- 범위: 다른 로컬 브랜치·원격·태그에서 도달 불가한 커밋만(게시 커밋 불변 → force-push 없음). 기본 브랜치·서명 커밋·merge 커밋이면 거부. git 2.40+ 필요.
- 테스트: `test_commit_units.py`(임시 repo fixture, 전역 git 설정 격리).

### skills/jira-worklog/ — worktree 작업시간 → Jira worklog

AI 세션 로그(Claude `~/.claude/projects/<slug>` + Codex `~/.codex/sessions`)에서 AI 가 실제 작업한 시간(사용자 응답 대기·긴 공백 제외)을 날짜별로 추정해 Jira worklog 에 기록. stdlib only(설치 불필요), launcher는 `uv` 우선·`python3`/`python` fallback(Windows PowerShell은 `py` 포함)이며 기본은 미리보기(dry-run), 실제 등록은 `--register`다. Codex는 bootstrap이 `$HOME/.agents/skills/jira-worklog`를 안정적인 `$HOME/.claude/skills/jira-worklog`에 연결한 뒤 새 세션에서 이 스킬을 직접 발견한다. `/e` 6단계가 마무리 시 호출한다.
- **대기 제외는 role 단계에서** — 진짜 사용자 입력 직전 gap과 Claude의 `AskUserQuestion`·`ExitPlanMode` 응답 대기를 제외한다. Codex 는 turn lifecycle(`task_started` 직전·`task_complete`/`turn_aborted` 직후 gap)과 `request_user_input` call_id 구간으로 판정한다 — Codex 의 `user_message` 이벤트는 2026-08 을 지나며 사라져(8월 97/450 → 9월 0/47) 그 이벤트만 보면 turn 사이 대기가 통째로 작업이 된다(실측 rollout 1004개: 1029.5h → 469.9h). 이전에 등록한 Codex 항목은 재등록 시 등록 게이트에 걸리는 것이 정상이다. `--max-gap` 기본값은 24시간(1,440분)이며, 필터 이후 남은 인접 이벤트 간격이 이를 초과하면 구간 전체를 제외한다. 24시간 이하의 미식별 유휴 구간은 포함될 수 있다. CLI·환경변수·설정 파일에 명시한 값은 기본값보다 우선한다.
- **권한 승인 대기는 걸러내지 못한다**: tool_result 에 승인 여부를 가릴 필드가 없어 정상 결과와 구분되지 않는다(거부만 본문으로 식별 가능). 실측 규모는 작다 — Bash 는 8177건 중 5분 초과가 16건, 최대 17분이고 그마저 실제 실행시간이 섞여 있다.
- **귀속은 줄 단위 `cwd` 기준**(폴더 아님). Claude 세션 파일은 cwd 를 따라 slug 폴더를 **이동**하므로 파일 위치로 귀속하면 오간 세션의 시간이 마지막 위치 한 곳으로 몰린다(실측상 다중 cwd 파일이 다수 — 예외가 아니라 기본 케이스). 이벤트마다 cwd 를 읽어 bucket(live/dead/main/unmatched)으로 나누고, **인접 이벤트 쌍의 bucket 이 같을 때만** 구간을 발행한다(bucket 별로 먼저 거르면 A→B→A 왕복이 A 를 가로질러 이어붙어 이중계상). 코퍼스는 **한 번만** 스캔한다(worktree 마다 재스캔하면 N배).
- **삭제된 worktree**: `<root>/.claude/worktrees/<name>` 규약으로 이름을 복원해 **표시만** 하고 등록하지 않는다. 등록 가능 여부는 이름이 아니라 `Bucket.kind` 로 판정한다 — 죽은 worktree 이름이 티켓형(`ABC-1234-…`)이면 이름 기준 필터로는 샌다. main 은 모든 worktree 의 조상이라 **조상 폴백을 하지 않는다**(하면 삭제된 worktree 시간이 통째로 main 에 흡수된다).
- **Codex 는 파일 단위 귀속** — rollout 전수에서 세션 중 cwd 이동이 0건이라 나눌 것이 없다. 단 **소속 판정은 Claude 와 같은 분류기**(`WorktreeIndex.classify`)를 태운다 — worktree 하위 디렉토리에서 시작한 세션도 그 worktree 로 잡힌다(예전엔 정확일치라 26건이 어디에도 못 가고 사라졌다). "파일 단위"는 *한 rollout 을 쪼개지 않는다*는 뜻이지 매칭이 엄격하다는 뜻이 아니다.
- **등록 게이트**(게이트까지 all-or-nothing — 통과 후 HTTP 실패는 부분 반영 가능, Jira 에 트랜잭션 없음): 전 날짜 `old → new` diff 출력 후, 30분 이상 & 50% 초과 변동(**증가·감소 양쪽**)이나 rename 의심(같은 날 내 다른 worktree 항목 존재 + 이 마커 없음)이면 **한 건도 쓰지 않고** 중단. `--allow-large-change` 로 진행하며, 직전 값·worklog id 는 `~/.claude/logs/jira-worklog-<날짜>.jsonl` 에 남는다(Jira 쓰기는 code revert 로 복구 불가).
- 대상 티켓은 **worktree 디렉토리 이름 prefix**(anchored)에서 우선 추출, 없으면 브랜치명 fallback. 어느 쪽에도 없으면 등록 skip(안전). 기본 패턴은 `[A-Z][A-Z0-9]+-\d+` 이고, 조직 고유 키로 좁히는 패턴은 머신별 `~/.jira-kit/jira-kit.toml`(`[worklog]` `ticket_pattern`, 작은따옴표 리터럴 문자열 — cwd 위에 프로젝트 `jira-kit.toml` 이 있으면 전역 대신 그것만 읽는다) 또는 `JIRA_TICKET_PATTERN` 에 둔다. 공개 repo 에는 넣지 않는다. jira-task 도 같은 키를 읽는다(우선순위·주의는 SKILL.md).
- **worklog 항목은 세션 단위**: 마커 `[jira-kit] worklog <티켓> <날짜> (<worktree>) [<세션>]` 로 그 세션의 그날 항목만 upsert 한다(멱등). 세션 id 자체가 분할 키라 "어디까지 등록했나" 워터마크 없이 재실행이 안전하다. 세션이 끝날 때마다 실행하면 그 몫이 독립 항목으로 남고 **티켓 총 작업시간은 Jira 가 합산** — 대신 한 티켓에 항목이 여러 줄 쌓인다(실측 한 티켓: 3항목 → 22항목). 한 세션이 여러 worktree 를 오가면 worktree 마다 항목을 갖는다(세션은 등록 단위이지 귀속 단위가 아니다).
- **세션 id 는 uuid 의 뒤 8자**(`claude:e7173e9a`). 앞이 아니라 뒤인 이유는 Codex rollout id 가 UUIDv7 이라 앞 48비트가 timestamp 여서다 — 앞 8자로 줄이면 수 초 안에 시작된 세션끼리 그대로 겹친다(실측 수십 건이 한 항목으로 합쳐졌다). 그래도 겹치면 등록 전에 감지해 경고한다.
- **겹침 union 은 세션 안에서만** 일어난다. 두 세션을 같은 시각에 병렬로 돌리면 겹치는 시간이 양쪽에 잡혀 합계가 실제 경과시간보다 커진다 — 실측(회사 repo) 등록 대상 worktree 기준 과다분 합계 약 2.3h, worktree 94개 중 89개는 겹침 0.
- 마커 매칭은 ADF **줄 정확일치** — 부분문자열이면 사용자 `--comment` 본문이나 Jira UI 편집 텍스트에 마커가 섞인 항목을 자기 것으로 오인한다. 반대로 마커를 **놓치면** 새 항목이 생겨 조용히 이중계상되므로, 줄 추출은 UI 편집이 만드는 `hardBreak`·`codeBlock`·`heading`·앞뒤 공백까지 흡수한다.
- author scoping(내 accountId 항목만) · 마커 중복 2건+ 중단 · **worktree 없는** 구 형식 항목 발견 시 중단(귀속 불명 → 수동 정리 요구). **세션 없는** 구 형식은 귀속이 명확하므로 중단하지 않고 경고만 한다(새 항목과 겹쳐 계상되니 수동 정리 대상).
- 인증(`JIRA_BASE_URL`/`JIRA_EMAIL`/`JIRA_API_TOKEN`)은 환경변수 또는 `~/.jira-kit/.env`, 비민감 설정은 `~/.jira-kit/jira-kit.toml`. 토큰 없으면 미리보기만 되고 마무리 흐름은 안 막힌다.

### skills/jira-task/ — Claude·Codex 작업내용 → Jira task description

현재 worktree의 작업 중 task 목표에 해당하는 변경만 날짜 줄 + 한 줄 항목 목록으로 기존 Jira task description의 `작업 내용` 섹션에 반영한다(리베이스·테스트 정비 같은 과정은 적지 않고, 적을 항목이 없으면 갱신하지 않는다). 기본은 미리보기이며, `/e`에서 사용자 확인 후 `--post`를 붙여 기존 본문에 추가하거나 같은 marker 항목을 갱신한다. 별도 Jira comment는 생성하지 않는다. 인증 경로는 `jira-worklog`와 같은 `~/.jira-kit/.env`를 사용한다.

```text
uv run --no-project python "skills/jira-task/jira_task.py" --ticket ABC-1234 --summary-file "<요약 파일>"
```

요약(줄 하나 = 항목 하나)은 파일로 넘긴다 — 명령 인자로 넣으면 backtick·`$` 가 셸에서 해석된다.

preview 결과를 확인하고 `/e`에서 사용자 승인 후 동일 명령에 `--post`를 추가한다. 시간은 `jira-worklog`, 작업내용은 `jira-task`가 각각 Jira에 남긴다.

### scripts/

settings.json 에 등록돼 후크가 호출하는 진입점은 notify(`notify-hook.js`), 세션 브리프(`session-brief.js`), worktree 가드(`guard-worktree-edit.js`), 콜론 refspec 원격 삭제 가드(`guard-push-delete.js`), dlc evidence 3종(`dlc-task-router.js` / `dlc-evidence-ledger.js` / `dlc-early-stop.js`). 모두 fail-open (실패해도 throw 안 함). 나머지(`bootstrap/`, `*.ps1`, `install-*`, `prompt-gwl.py`)는 위 진입점이 위임하거나 수동/프로젝트별로 쓰는 보조 스크립트.

#### `bootstrap/` (setup.sh · setup.ps1 · sync_codex_agents.py · README.md)
새 머신에서 한 번 실행해 이 환경(도구 + 설정 + 선택적 memory)을 재현하는 **idempotent** 부트스트랩. macOS `setup.sh`(zsh/비-conda), Windows `setup.ps1`(레지스트리 — ⚠️ 전체 실행 미검증). 도구(node/uv/ripgrep(macOS)/선택적 standalone rtk)·셸 env 를 각 단계 guard 로 `[SKIP]`. Codex 연결은 macOS 가 skill 7종(`$HOME/.agents/skills/`)과 `${CODEX_HOME:-$HOME/.codex}/AGENTS.md` → `CLAUDE.md` 를 symlink 로 만들고 agent 정의(`…/agents/*.toml`)를 생성하며, Windows 는 skill 을 junction 으로, AGENTS.md 를 symlink 로 만든다(개발자 모드 또는 관리자 셸 필요) — 자리에 다른 것이 있으면 건드리지 않는다(macOS 는 나머지 연결·뒤 단계를 마치고 요약과 함께 exit 1, Windows 도 같다). effort 환경변수는 해제해 `/effort`가 동작하게 한다. `--dry-run`/`--memory-from` 지원. 상세·전제·한계는 `scripts/bootstrap/README.md`.

**Codex 쪽 연결**: `~/.codex/AGENTS.md` 는 `~/.claude/CLAUDE.md` 로의 심링크다(단일 소스 — 2026-06-10 사용자 결정 `a3d7bdc`). `~/.agents/skills/{c,dlc,e,improve,jira-worklog,wiki,wt}` 도 `~/.claude/skills/*` 심링크다(`scripts/bootstrap/install-codex-skill.sh --source … --target …` 로 설치). Codex 앱의 Claude 설정 import(2026-08-01)가 이 연결을 단어 치환한 실파일 사본으로 덮어써 규칙이 8월 초 상태에 멈췄던 것을 2026-09-25 에 되돌렸다(백업 `backups/codex-resync-20260925/`, 이 repo 의 `AGENTS.md` 미러도 치움). macOS bootstrap(`setup.sh`)은 이 8개 연결을 모두 재현하고(`install-codex-skill.sh --file` 이 AGENTS.md 담당), Windows(`setup.ps1`)도 같은 연결을 재현한다(`install-codex-skill.ps1 -File` 이 AGENTS.md 담당). Codex agent 정의 `~/.codex/agents/*.toml` 은 링크가 아니라 `agents/*.md` 에서 만든 사본이다 — `scripts/bootstrap/sync_codex_agents.py` 가 `## Codex 병행…` 절(Codex 안의 리뷰어가 자기 자신을 부르게 되는 병행 검토)을 빼고 첫 줄에 생성 표식을 단다. setup.sh 가 부르고, `agents/*.md` 를 고친 커밋이 main 에 들어오면 손으로 다시 돌린다(자동 감지 없음, 상세·충돌 처리는 `scripts/bootstrap/README.md`). **import 를 다시 실행하면 같은 일이 생기므로** 실행 뒤 `readlink ~/.codex/AGENTS.md`, `ls -la ~/.agents/skills`(7개가 링크인지), `ls ~/.claude/AGENTS.md`(미러가 다시 생겼는지), `head -1 ~/.codex/agents/*.toml`(생성 표식)로 확인한다.

Codex `~/.codex/hooks.json` 에는 dlc 훅을 두지 않는다. 이 repo 의 훅이 읽는 입력 — `guard-worktree-edit.js` 의 `tool_input.file_path`, `dlc-evidence-ledger.js` 의 `tool_response.bashEditDiff`, `dlc-early-stop.js` 의 `background_tasks` — 을 Codex 가 같은 형태로 준다는 근거가 없다(Codex 의 파일 편집은 `apply_patch` 라 경로가 `tool_input.command` 의 patch 본문 안에 있고, Claude Code 전용인 `bashEditDiff` 와 background 작업 목록이 없다. PostToolUse 에 명령 출력이 빠진다는 issue 보고도 있다 — 2026-09-28, codex-cli 0.154.0 기준 조사). 그래서 Codex 세션이 main checkout 을 worktree 없이 고쳐도 막는 게이트는 없고, `AGENTS.md`(=CLAUDE.md) 규약·git 훅·원격 ruleset 이 그 자리를 대신한다.

#### `notify-hook.js`
Cross-platform notify 진입점 (Node). stdin 의 Claude Code JSON 에서 `message` · `cwd` 추출 (title = cwd basename). **macOS**: `afplay` 시스템 사운드 + `osascript` 배너 (인라인). **Windows**: 원본 stdin 을 그대로 넘기며 `powershell.exe -File notify-hook.ps1` spawn. **Linux**: best-effort `notify-send`. 모든 동작 best-effort — 실패해도 throw 안 하고 stdin 1초 타임아웃으로 세션 안 멈춤. 사운드 기본값은 이벤트별 (Stop→Glass/Asterisk, Notification→Ping/Exclamation); command 3번째 인자로 override.

#### `notify.ps1`
Toast 알림 + 시스템 사운드 + 윈도우 flash. 우선순위: WinRT ToastNotification → System.Windows.Forms NotifyIcon. WinRT toast 는 Windows PowerShell 5.1 전용 (PS7 은 WinRT 어셈블리 미포함) — hook 이 `powershell.exe` 로 5.1 고정 실행. toast 표시 전 `HKCU\Software\Classes\AppUserModelId\Claude.Code` 에 AppID 자가 등록 (미등록 AppID 는 Windows 가 toast 를 조용히 버림).

#### `notify-hook.ps1`
Windows 에서 `notify-hook.js` 가 spawn (`Stop` / `Notification` 이벤트). stdin 으로 넘어온 Claude Code JSON 에서 `cwd`, `session_id` 추출, 부모 프로세스 트리에서 WindowsTerminal 의 tab 제목 추출 → `notify.ps1` 에 title/message 전달. (macOS·Linux 에선 호출되지 않음.)

debug log: `$env:CLAUDE_NOTIFY_DEBUG = '1'` 설정 시에만 `%TEMP%\claude-notify-debug.json` 에 매 호출마다 덮어씀. cwd, sessionId 포함되므로 디버깅 후 환경변수 해제 권장. 기본값은 off (privacy footprint 최소화).

#### `guard-worktree-edit.js`
> auto 모드에서는 main 직접-편집 `ask` 가 발동하지 않는다(2026-08-06). worktree 게이트는 그 모드에서 CLAUDE.md §3-1 규약으로만 남고 하드 게이트가 아니다.

PreToolUse(`Edit|Write|NotebookEdit`) 가드. 두 경로:
- **worktree 세션**(cwd 가 `.../.claude/worktrees/<name>/` 하위): 그 worktree 밖 **main checkout 의 추적 파일 편집**과 **새 파일 생성**(아직 없고 gitignored 가 아닌 경로)을 `deny` 로 차단 — worktree 사본을 고쳐야 할 편집이 main 으로 새거나, 브랜치에 담겨야 할 새 파일이 main 에 남아 뒤의 ff-merge·pull 을 untracked 충돌로 막는 실수 방지. deny 메시지는 대응하는 worktree 경로를 알려 준다. 판정은 main checkout 에서 `git --literal-pathspecs ls-files --error-unmatch`(추적)·`git check-ignore -q`(새 경로가 ignored 인지)이고, git 판정 실패(repo 아님·spawn 실패·timeout·submodule·safe.directory 거부)는 fail-open(allow). 현재 worktree 안, repo 의 `.claude/` 메타와 `.git/`(모든 worktree 가 공유하는 common dir), `~/.claude` 레이아웃의 `plans/`(추적되지만 §10 핸드오프), gitignored 경로(`projects/` memory·`settings.json`·`settings.local.json`·`jobs/` 등 — 기존·새 파일 모두), main 에만 있는 기존 untracked 파일(사용자 초안 등), repo 밖(홈 등) 경로는 allow — 대개 worktree 사본이 없는 경로다. `/wt` 가 복사한 `.env` 처럼 사본이 있는 gitignored 파일도 allow 한다(사본 유무로 막으면 worktree 에도 있는 gitignored plan 을 main 에서 고치는 정상 편집이 다시 막힌다). EnterWorktree 로 들어간 세션은 네이티브 worktree 격리가 이 hook 보다 먼저 worktree 밖 편집을 거부하므로(2.1.283 실측), 이 판정이 실제로 걸리는 것은 격리되지 않은 채 cwd 가 worktree 안인 세션이다 — worktree 디렉토리에서 바로 시작한 세션, `ExitWorktree` 뒤 Bash `cd` 로 cwd 가 돌아온 세션 등.
- **비-worktree 세션**: cwd repo 가 `main`/`master` 브랜치이고 편집 대상이 **그 repo 의 추적 파일**이면 `ask`(승인 요구) + `main-edit-ask` 신호 emit — main 직접 편집 대신 worktree/브랜치를 쓰는 규약(CLAUDE.md §8)을 기계화. branch·tracked 판정 모두 cwd repo 기준(fp 가 cwd repo 밖이면 allow). 전 repo 전역 적용, `CLAUDE_MAIN_EDIT_GUARD_OFF=1` 로 전역 해제. git 판정 실패(미설치·detached·repo 밖·timeout)는 모두 fail-open(allow).

jq 미설치 환경이라 node 로 stdin JSON 파싱. 파싱 실패 시 exit 0 (fail-open).

#### `guard-push-delete.js`
PreToolUse(`Bash`) 가드. 명령을 셸 단어로 나누고(작은·큰·`$'…'` 따옴표, `\` 이스케이프, `\`+개행 줄 이음, `2>&1` 같은 리다이렉트 처리. 큰따옴표 안 치환이 끝나면 따옴표 상태를 되돌리고, 짝 없는 작은따옴표는 글자로 둔다) `;`·`&`·`|`·개행·괄호·단독 `{`/`}`·`$(`·백틱(큰따옴표 안 포함 — 셸은 거기서도 치환을 실행한다)으로 조각을 끊은 뒤, 조각 안 **어느 위치든** `git`(경로·`.exe` 포함)이 나오면 전역 옵션(`-C`·`-c` 등 값 포함)을 건너뛰고 `push` 뒤 인자에 `:<ref>`·`+:<ref>` 가 있는지 본다. 있으면 **권한 모드와 무관하게 `ask`**(auto 포함 — `permissions.ask` 규칙과 같은 동작, CLAUDE.md §8(b)). 어느 위치든 보는 것은 `do`·`then`·`xargs`·`env`·`sudo`·`rtk proxy` 같은 앞말을 목록으로 관리하지 않기 위해서다. `-c`(`-lc` 같은 결합 포함)·`eval` 뒤의 문자열(`bash -c "…"`)은 그 자체를 명령으로 다시 검사하고, `:$(git branch --show-current)` 처럼 치환으로 이어지는 refspec 도 삭제로 본다. 통과: `:` 단독(matching push)·`HEAD:feat`·실행되지 않는 리터럴(`echo 'git push origin :x'`). 셸 문법을 완전히 해석하지 않으므로 애매하면 `ask` 쪽으로 틀린다 — 주석·heredoc 본문·`-o :값` 도 명령처럼 읽혀 확인이 뜰 수 있다. stdin JSON 파싱 실패만 fail-open.

규칙이 아니라 hook 인 이유: `Bash(git push * :*)` 는 끝의 `:*` 때문에 prefix 규칙으로 해석돼 앞의 `*` 가 풀리지 않아 **아무것도 매칭하지 못했고**(2.1.283 바이너리의 `/^(.+):\*$/` 판정, 시작 경고 *"mixes * with the trailing :* prefix syntax"*), `:*` 를 중간에 둔 `Bash(git push * :**)` 는 매칭은 되지만 규칙 문자열에 `:*` 가 있으면 위치와 무관하게 매 세션 시작마다 안내가 뜬다(2026-09-28 실측). hook 의 `ask` 는 매칭되는 `allow` 규칙(`Bash(rtk git *)`)이 있어도, auto 모드에서도 실행을 막는다 — headless `claude -p --permission-mode auto` 로 로컬 bare remote 에 시킨 `git push origin :b1`·`rtk git push origin :b2` 는 실행되지 않았고 hook 없이 같은 조건이면 삭제됐다(headless 라 확인 창 대신 거부로 끝난다. 대화형 세션에서는 확인 창이 뜨는 것이 hook `ask` 의 정의). rtk hook 은 `updatedInput` 만 돌려주고 판정을 내지 않아 이 가드의 `ask` 와 겹치지 않으며, 가드는 원문과 `rtk git …` 형태를 모두 본다.

한계: hook 프로세스 자체가 실패하면(node 부재·스크립트 경로 없음·timeout) 판정 없이 통과한다 — node 에 의존하지 않던 규칙보다 이 경우만 약하다. `bash <script>` 안의 push 는 못 본다(`permissions.ask` 절 (1)과 같다). settings.json 이 추적 대상이 아니라 **다른 머신은 pull 로 스크립트만 받는다** — 머신마다 `~/.claude/settings.json` 의 `hooks.PreToolUse` 에 `{"matcher": "Bash", "hooks": [{"type": "command", "command": "node ~/.claude/scripts/guard-push-delete.js"}]}` 를 넣고, 남아 있으면 `Bash(git push * :*)`·`Bash(rtk git push * :*)`(또는 `:**` 형태) ask 규칙을 지운다.

#### `dlc-task-router.js` · `dlc-evidence-ledger.js` · `dlc-early-stop.js` (+ `dlc-ledger.js` · `dlc-doc-drift.js` · `dlc-signal.js`)
dlc(`skills/dlc/`)의 evidence gate 를 보조하는 누락방지망. 모두 fail-open — plan `# Acceptance` evidence gate(메인 판정)가 단일 소스고, 이 hook 들은 capped 보조일 뿐.
- **`dlc-task-router.js`** (UserPromptSubmit, + `.test.js`) — 디버깅/render 키워드 감지 시 조사·검증 discipline(취향·시각 산출물엔 **프로토타입-우선** 제안 포함)을 주입하고 세션 evidence 장부를 리셋. 매칭 전에 하네스가 붙인 `<system-reminder>`·`<task-notification>` 블록을 걷어내고, 남은 사용자 텍스트가 없으면 **장부 리셋도 건너뛴다** — subagent 결과 알림 턴에도 UserPromptSubmit 이 발동해 알림 본문의 "재현·failing" 이 오발동시켰고(한 세션 4회 실측), 그 턴의 리셋이 `dlc-early-stop` 의 changed/verified·doc-drift 판정을 조용히 지웠다. reminder 가 앞뒤에 붙은 정상 프롬프트는 그대로 라우팅·리셋된다. 걷어낸 뒤 `<agent-message>` 로 시작하는 턴(앞에 `Another Claude session sent a message:` 가 붙든 말든 — auto mode 의 subagent 보고(v2.1.271~) 등 다른 agent 가 보낸 메시지)은 태그 뒤에 하네스 안내 문단이 붙어 걷어내기로는 텍스트가 남으므로, 앞머리로 판별해 **턴 전체를 건너뛴다**(라우팅·리셋 모두) — 2026-09-15 부터 14개 세션에서 130회 오발동했다.
- **`dlc-evidence-ledger.js`** (PostToolUse `Edit|Write|NotebookEdit|Bash`) — 코드 변경·검증 명령 실행을 세션 장부에 기록 + 문서화 표면↔README/index dirty flag 갱신(`dlc-doc-drift` 판정). `readme-trigger-new` 부류의 신규 여부는 여기서 판정해 주입(`isNewInRepo` — `git ls-tree HEAD` 에 그 경로가 없으면 신규; git 실행 실패는 기존 취급 = 무경고). **Bash 로 고친 plan·`README.md`·`wiki/index.md` 는 경고를 끄는 쪽으로만 반영** — Claude Code 가 PostToolUse 에 주는 `tool_response.bashEditDiff`(v2.1.269, 기본은 auto·bypass 모드에서만)의 경로(`changedFiles` ∪ `files[].filePath`) 중 **이 브랜치에 매칭되는 plan**(`plan-match.js`)이면 `planTouched`, README·index 면 drift target 처리 — 둘 다 HEAD 와 다를 때만(`git --no-optional-locks status --porcelain`). 끝까지 간 git pull·merge 가 나열한 경로는 HEAD 와 같아 걸러지고, 충돌로 멈춘 merge 가 남긴 다른 plan 은 브랜치 plan 이 아니라 인정하지 않는다. Bash 로 고친 스크립트는 `changed`·trigger 를 켜지 않는다 — Edit/Write 와 똑같이 다루면 git 동기화 diff·한 diff 안의 경로 순서·`sed … && verify` 체인의 veto 로 새 오탐이 생긴다(2026-09-27 실측, plan `ledger-bash-edits`). 한계: 다른 권한 모드·실패한 Bash·`run_in_background` Bash·단독 git 동기화 명령에는 diff 가 없어 예전처럼 못 보고, README·index 를 지워도 target 갱신으로 처리된다(드묾). **`run_in_background` 로 띄운 Bash 는 `tool_response.backgroundTaskId` 를 장부 `bgTaskIds` 에 남긴다**(최근 50개, 사용자 프롬프트마다 비움) — `dlc-early-stop.js` 가 이번 턴 shell 대기를 가르는 키다. 이 필드는 hooks 문서에 없는 도구 출력이다(2.1.285 transcript 에서 완료 알림의 task-id 와 같은 값으로 확인). 이름이 바뀌면 기록이 안 되고 경고가 남는 쪽으로만 틀린다. timeout·Ctrl+B 로 background 에 넘어간 명령은 입력에 `run_in_background` 가 없어 남기지 않는다. **검증 명령 인식은 2단 구조** — `VERIFY_TOOLS`(그 자체가 검증인 도구: pytest·jest·eslint·mypy·`shellcheck`·`stylelint`·`yamllint`·`hadolint`·`rspec`·`phpunit` 등) + `VERIFY_SUBCMD`(서브커맨드·플래그가 붙어야 검증: `docker compose … config`·`make (test|lint|check|verify|typecheck)`·`dotnet test`·`swift test`·`terraform validate`·`(prettier|black) … --check`·cargo/go/gradle/mvn/npm 계열). 나눈 이유는 `docker compose up`·`terraform apply`·`prettier --write`·`black .` 처럼 **실행·적용이지 검증이 아닌** 호출을 verified 로 치면 gate 가 헐거워지기 때문 — 음성 케이스도 테스트로 락. 이 확장은 2026-08-13 telemetry 조사에서 나왔다(`.md` 제외 fix 이후 남은 `early-stop-verify` 발동이 `compose.yaml`·`*.css`·`*.sh` 에 몰렸는데 그 표준 검증기가 전부 미인식이었다). **검증 래퍼는 본문으로 판정한다** — 명령이 `bash|sh [옵션] <file>.sh`(줄 시작·개행·`&&`·`;` 뒤, 명령 하나에 3개까지)이고 그 파일이 16KB 이하 일반 파일이면 본문을 한 단계만 본다. 줄마다 주석·heredoc 본문(도움말·만들 파일 내용)·비검증 시작 줄(`cat`·`echo` 등)을 빼고, 명령과 같은 규칙(`VERIFY_SCRIPT` 이름 규칙 포함)에 맞는 줄이 있으면 검증으로 친다. 경로는 명령 원문에서 뽑는다 — 소문자화한 명령에서 뽑으면 대소문자를 가리는 파일시스템(Linux)에서 못 찾는다. `~/` 는 홈, 상대경로는 hook 입력 `cwd` 기준이고 변수는 풀지 않는다. 격리 runner·scratch 의 `bash <scratch>/x_final.sh` 안에서 gradle 테스트를 돌려 통과했는데, 이름이 `VERIFY_SCRIPT`(키워드가 `.sh` 바로 앞)에 맞지 않아 검증 경고가 난 2건(2026-09-27~30, plan `hook-wait-shell-verify-body`)에서 나왔다. 이름 규칙은 넓히지 않는다(`checkout.sh`·`test-data-loader.sh` 오인식 락). 한계: 본문 줄이 실제로 실행되는지는 보지 않는다 — 다른 `case` 분기·부르지 않는 함수·변수에 담은 명령·`log "…npm test…"` 같은 메시지·`pip install pytest` 같은 설치 줄도 센다. 명령 쪽도 인용을 가리지 않아 `-m 'ran; bash x.sh ok'` 처럼 인용 안에 적힌 래퍼도 읽는다. plan 리뷰의 30일 기록 재생 표본과 이 repo 스크립트 재생에서는 오인식이 없었다. 못 보는 쪽은 두 단계 이상 중첩·`./x.sh` 직접 실행·명령 앞 접두(`timeout`·`sudo`·`X=1`)·`|`·`||` 뒤·인용하거나 공백이 든 경로·`-o pipefail` 처럼 값을 받는 옵션·`\` 줄 이어쓰기·실행 뒤 지운 스크립트·`cat`·`echo` 로 시작하는 명령 전체(기존 veto)·Windows 의 `/c/…`·`/tmp/…` 경로(Node 가 `C:\c\…` 로 푼다)다.
- **`dlc-early-stop.js`** (Stop) — 종료 시 네 누락을 capped 1회 경고로 합쳐 출력: ① **코드**를 변경했는데 검증 기록 없음(문서 `.md` 편집은 이 게이트 밖 — test/lint 대상 아님이라 doc-only/정리 세션 오탐 방지, 문서↔README 는 아래 ②가 커버; `CLAUDE_DLC_EARLYSTOP_OFF=1`), ② 문서화 표면(`scripts/`·`agents/`·`skills/**/SKILL.md`·`CLAUDE.md`, `wiki/pages/`)을 바꿨는데 `README.md`/`wiki/index.md` 동기화 없음(`CLAUDE_DLC_DOCDRIFT_OFF=1`; 판정 직전 `resolveRoot`+`fs.statSync` 로 target mtime 을 `dlc-doc-drift.evaluate` 에 주입해 **Bash 로 고친 README 도 인정**한다), ③ **plan drift** — 소스를 바꿨는데 이 브랜치에 매칭되는 §10 plan 을 한 번도 안 건드리고 종료(`CLAUDE_DLC_PLANDRIFT_OFF=1`). 발동 조건이 좁다: `plan-match.js` 가 `git rev-parse` 로 얻은 브랜치와 `plans/*/*-plan.md` 를 매칭해 **실제로 파일이 있을 때만** 판정하고, git 이 없거나 detached 면 판정을 포기한다(fail-open). §10 이 말하는 "세션 내 active 추적"(브랜치를 바꿔도 따라오는 plan)은 hook 이 알 수 없어 **놓치는 쪽을 감수**한다 — 이 축의 최대 위험은 오탐이다. 단 **테스트 파일(`*.test.js`)은 신규 추가일 때만** — README 는 테스트를 `x.js (+ .test.js)` 처럼 존재만 표기하므로 기존 테스트 편집은 README 무영향(오탐이었음). ④ **결론 블록** — plan 외 파일을 편집한 턴(`.md` 포함, ledger `edited`)의 마지막 답변(`last_assistant_message`, Stop stdin 이 주는 텍스트 — transcript 는 늦을 수 있어 안 읽음)이 `## 결론` 을 **마지막 `## ` heading** 으로 갖지 않으면 경고(`CLAUDE_DLC_CONCLUSION_OFF=1`; 마지막 `## ` heading 이 `## 결론` 인지만 검사하고 코드펜스 안 `## ` 는 무시, §3-6 5항목 유무는 검사하지 않는다). 하네스가 주는 텍스트는 **턴의 마지막 텍스트 블록만**이라(2.1.272 실측) AskUserQuestion 선택 뒤 짧은 마감으로 끝내면 걸린다 — §3-6 이 마감 텍스트 자체를 결론 블록으로 쓰라고 정한 이유. `stop_hook_active` 재종료 경로에서도 결론이면 `edited` 를 소비한다(경고는 없음). 통과하면 `edited` 를 **소비**한다 — ledger 리셋은 UserPromptSubmit 1곳뿐이라 subagent 알림·AskUserQuestion 응답 뒤의 짧은 답변까지 막지 않게. 자체 try/catch 로 다른 축의 reason·카운터를 삼키지 않으며 신호 `early-stop-conclusion` 은 detail 없음(답변 본문 미기록). 한 hook 에서 합산 출력 — 별도 hook 이면 동시 block 시 한쪽 카운터가 미노출 소모돼 다시 안 잡히는 false negative. **대기 턴은 건너뛴다** — Stop 입력 `background_tasks`(v2.1.145)에 `subagent`·`workflow` 가 있거나 **이번 사용자 턴에 `run_in_background` 로 띄운 `shell`**(id 가 장부 `bgTaskIds` 에 있는 것)이 있으면 턴이 끝난 게 아니라 결과를 기다리는 중이라, 경고도 장부 갱신도 하지 않고(`stop_hook_active` 분기보다 먼저) 결과가 온 뒤의 Stop 에서 판정한다. shell 은 id 로만 맞춘다 — Stop 의 `command` 는 1000자에서 잘리고, 이전 턴에 같은 명령으로 띄운 서버와 구분되지 않는다. shell 로 미룰 때는 activity 신호 `early-stop-wait-shell` 을 남긴다 — 장부에 걸린 경고가 없어도 남는 대기 턴 수라서, 과억제(실제로는 기다리지 않은 턴)는 그 신호의 session·시각으로 transcript 를 찾아 가른다. 대기 턴에 쓴 `## 결론` 은 소비하지 않는다 — subagent 대기와 같이, 결과가 온 뒤의 마지막 답변이 결론으로 끝나야 한다. 이전 턴의 `shell`·`monitor` 는 끝나지 않는 서버·tail 일 수 있고, `teammate` 는 일을 마치고 idle 이어도 목록에 running 으로 남으며(직렬화에 idle 여부가 없다), `cloud session`·모르는 type 은 이 세션으로 돌아오는지 몰라 억제하지 않는다. shell 대기는 2026-09-30 에 더했다 — subagent·workflow 대기 수정이 들어간 뒤의 결론 경고 7건이 모두 background shell 을 기다린 턴이었다(머지 뒤 배포 감시 등, plan `hook-wait-shell-verify-body`). 한계: 기다리는 사이 사용자가 새 프롬프트를 보내면 라우터가 장부를 리셋해 미룬 경고가 사라진다. `bgTaskIds` 는 다음 사용자 프롬프트까지 남는다(알림 턴은 리셋하지 않는다). 그래서 같은 턴이나 그 뒤 알림 턴에 띄운 서버가 도는 동안에는 기다리지 않고 닫아도 경고가 빠지고, subagent 가 띄운 shell 도 부모 장부에 기록된다. Stop 전에 끝난 shell 은 목록에 없어 그대로 경고한다.
- **`dlc-doc-drift.js`** — 문서 drift 판정 **순수 모듈**(hook 아님). `resolveRoot`(`.claude`/worktree 한정, 타 repo no-op)·`classify`(root 기준 정확 경로 → `readme-trigger`/`readme-trigger-new`/`index-trigger`/`*-target`)·`applyChange`(dirty 전이; 5번째 인자 `isNewFile(rel, root)` 는 `readme-trigger-new` 에만 조회되는 주입 콜백 — 미제공 시 트리거 안 함)·`partitionPending`·`settle`(mutating)·`evaluate(data, mtimeOf) → [{axis, message}]`. `readme-trigger-new` 는 README 가 **존재만** 문서화하는 부류(`*.test.js`·`*.spec.js`)라 신규 추가일 때만 경고한다. **covered-set**: target(README/wiki index)을 갱신하면 그때까지 dirty 를 유발한 trigger 들을 `*Covered` 로 넘기고, **covered 에 든 파일의 재편집은 다시 dirty 로 만들지 않는다** — 문서 동기화는 편집 *순서*가 아니라 *상태*인데 순서로만 모델링하면 "동기화 후 같은 파일을 한 번 더 만졌다"가 미동기화로 뒤집혀 오탐이 난다(2026-08-12 실제 2회). **mtime 재확인**: dirty 는 PostToolUse 의 `Edit|Write|NotebookEdit` 분기에서만 세워지므로, README 를 **Bash**(`node -e`·`sed`·heredoc)로 고친 target 갱신은 `bashEditDiff` 가 올 때(auto·bypass 모드, 2026-09-27~ `dlc-evidence-ledger.js`)만 장부에 잡히고, 그 밖엔 dirty 가 영영 안 풀린다("고쳤는데도 경고" — 2026-09-04 한 세션에 2회 발생). 그래서 `partitionPending` 이 `mtimeOf(rel)→ms|null`(early-stop 이 `resolveRoot` + `fs.statSync` 로 주입)로 **pending trigger 를 target mtime 기준으로 가르고**, `settle` 이 target 보다 낡은 것들을 covered 로 옮긴다(옮기지 않으면 그 파일 재편집 시 위 오탐이 Bash 경로에서만 되살아난다). `evaluate` 는 남은 게 있을 때만 경고하고 **축(`readme`/`index`)을 함께 돌려준다** — 신호를 dirty flag 로 emit 하면 억제된 축의 failure telemetry 가 남는다. **판정 불가는 전부 경고 유지**(`mtimeOf` 미제공·stat 실패·비유한 mtime·pending 없음·pending 이 상한 50 에 잘림) — 보조망이라 미탐이 오탐보다 나쁘다. **root 를 ledger 에 핀 고정**(`driftRoot`; 두 root 를 오가면 `''`)하고 Stop 시점 root 와 다르면 mtime 판정을 포기한다 — pending 의 rel 은 편집 시점 root 기준이라, 세션이 main 으로 옮기면 동명의 다른 파일을 재게 되고 main 은 README 가 매 머지마다 재작성돼 게이트가 통째로 꺼진다(실측: main 기준 `scripts/*.js` 26개 중 23개가 README 보다 낡음). **미탐**: mtime 은 *내용* 변경이 아니다 — `touch README.md`·`git checkout/stash/restore`·일괄 포매터가 target 을 재작성하면 통과한다(특히 `git restore README.md` 는 동기화를 되돌리면서 mtime 을 올린다). capped 1회·fail-open 보조망이라 감수하며, 단일 소스는 CLAUDE.md §3 문서 동기화 규약이다. covered 에 없는 **새** surface 는 종전대로 잡는다(미탐 미도입). 배열은 `push` 가 아니라 `concat` 으로 새로 할당 — `ledger.DEFAULT` 가 `{...DEFAULT}` 얕은 복사로 쓰여 push 하면 전 세션이 같은 배열을 공유·오염한다. covered/pending 각 50개 상한(초과분은 종전 동작). early-stop·evidence-ledger 가 require. 단위테스트 `dlc-doc-drift.test.js`.
- **`dlc-ledger.js`** — 위 hook 들이 공유하는 per-session 임시 장부(`%TEMP%/dlc-evidence-<sid>.json`) read/write/reset 모듈. `DEFAULT` 스키마 단일 소스(`changed/verified/blocks` + `readmeDirty/indexDirty/docBlocks` + `readmeTrigger/indexTrigger/changedTrigger` — 해당 dirty/changed 를 유발한 마지막 파일, 신호 `detail` 용 + `readmeCovered/readmePending/indexCovered/indexPending` — 재편집 오탐 차단용 covered-set, **소비자는 push 금지·concat 으로 새 배열 할당** + `bgTaskIds` — 마지막 사용자 프롬프트 이후 `run_in_background` 로 띄운 Bash 의 id, early-stop 대기 판정용). hook 으로 직접 등록되진 않음.
- **`dlc-signal.js`** — 자기개선 loop 의 **신호 수집 모듈**(hook 아님, 위 dlc hook 3종 + `guard-worktree-edit.js` 가 require). hook 판정 발동(early-stop 경고·early-stop 이 미룬 이번 턴 shell 대기(`early-stop-wait-shell`, activity — 대기 턴 수)·doc-drift·guard deny·guard main-edit ask·router 주입·plan `status: blocked` 전이·disposition 기록)을 `~/.claude/telemetry/dlc-signals.jsonl` 에 append-only 누적 — `/improve` 가 집계 소비. kind→axis(failure/activity) 단일 소스 `KINDS`, plan 신호는 substring 이 아니라 **상태 전이**로 판정(`detectPlanSignal` 순수 함수 — disposition 은 Review Disposition 섹션/placeholder 컨텍스트에서만). payload 는 kind·ts·session_id·cwd·`detail`(신호 유발 trigger 파일 — doc-drift 는 `readmeTrigger`/`indexTrigger`(repo-relative), early-stop 은 `changedTrigger`(basename); `/improve` 가 오탐 패턴(예 내부 dedup) 식별)만(`~` 축약, 프롬프트 원문·시크릿 없음 — 단 경로 메타데이터는 로컬 gitignored 파일에 남음, 전송·커밋 안 됨). fail-open + env 채널: `CLAUDE_DLC_SIGNAL_DIR`(redirect — 테스트 격리), `CLAUDE_DLC_SIGNAL_OFF=1`(무력화), `CLAUDE_DLC_SIGNAL_MAX_BYTES`(회전 임계, 기본 5MB `.1` 단일 회전 best-effort; summary 는 `.1` 도 함께 읽음). CLI `node scripts/dlc-signal.js summary`(집계) · `mark`(`/improve` 가 끝에 `<signalDir>/last-improve` 를 갱신 — 경로는 `improveMarkerPath` export 가 단일 소스이고 `session-brief.js` L 이 같은 export 로 읽는다. hook 이 아니라 호출자가 종료코드를 보는 명령이라 emit 과 달리 fail-open 이 아니다 — 쓰기 실패는 exit 1, 모르는 subcommand 는 exit 2). 단위+통합테스트 `dlc-signal.test.js`.
- **`session-brief.js`** (SessionStart hook — 위 hooks.SessionStart 참조) — 세션 시작 리마인더. K 머지 대기: `~/.claude` 의 origin/main 대비 ahead 로컬 브랜치(`for-each-ref`+`rev-list`, main/master 제외·oldest 순 cap5, fetch 안 함·git stderr 억제). L /improve 권장: `dlc-signal` 의 jsonl 을 직접 파싱해 마커(`last-improve` — `/improve` 가 끝에 `dlc-signal.js mark` 로 갱신, 없으면 전체 누적) 이후 failure 축 **unique 세션**(cross-kind dedup·회전분 합산) 이 임계(`CLAUDE_BRIEF_IMPROVE_MIN`, 기본5) 이상이면 nudge. **M 닫히지 않은 plan**: `plans/*/<slug>-plan.md` 중 `status: in_progress` 인데 작업이 끝난 것으로 보이는 것(= slug 앵커 매칭 브랜치가 **없음 OR 있어도 origin/main 대비 ahead 0**)이 `updated` 기준 임계(`CLAUDE_BRIEF_STALE_DAYS`, 기본3)일 이상 방치됐으면 알림 — **K 의 정반대 축**(K=코드는 됐는데 미머지, M=머지는 됐는데 §10 `status: done` 누락). 매칭은 `<slug>`·`worktree-<slug>`·`*-<slug>` 앵커만(free substring 금지 — 항상 존재하는 `main` 이 slug 에 main 이 든 plan 을 영구 억제한다), 로컬 + **fetch 된** 원격 ref 대상(다머신 진행분 오탐 차단 — fetch 전이면 "브랜치 없음"으로 볼 수 있다), `isDirectory()` 필터 **후** cap 적용(순서가 반대면 오래된 done 이 예산을 먹고 최신 plan 이 밀린다)·`*-plan.md` 한정·파일 단위 skip·frontmatter head 만 read(CRLF·BOM·YAML 인라인 주석 정규화)·`updated` 불량 시 `started` 폴백·oldest 순 cap5. **미탐 구간**: squash-merge 후 브랜치가 남아 있으면 ahead>0 이라 M 은 안 뜬다 — 그 구간은 K 가 "미머지 로컬"로 계속 알린다. **N 자동 pull 밀림**: `HEAD..origin/main` 이 0 이 아니면(=뒤처짐) 그 이유를 한 줄로 — `CLAUDE_AUTOPULL_OFF` 로 꺼둠 / detached / `main` 아님 / rebase·merge·bisect 진행 중 / **ahead>0 라 갈라져 ff 불가** / (검증 켜짐일 때) **CI 검증 기록 쪽 보류** — 로컬 `refs/remotes/origin/ci` 가 기록 경로를 막음 · 기록(`origin/ci/verified`) 없음 · 기록 내용이 커밋 이름 형식 아님(내용은 옮기지 않는다) · 기록이 origin/main 밖(재작성 직후) · 기록이 HEAD 까지(CI 진행 중·실패·`[skip ci]`), 각각 처방과 함께 / 자동 pull 이 가져올 범위(검증 켜짐이면 `HEAD..기록`, 꺼짐이면 `HEAD..origin/main`)의 파일을 로컬에서도 건드려 pull 거부(파일명 cap5, `-z` 로 받아 비ASCII·공백 경로 안전). 이 중 어디에도 안 걸리면 **원인을 단정하지 않는다**("원인 미확인") — 결정적 원인을 "재시도하면 되겠지"로 뭉뚱그리면 무기한 stale 이 된다. 네트워크를 쓰지 않고 **캐시된 추적 ref**(`origin/main`·`origin/ci/verified`)와 아래 fetch 스탬프로만 판정한다 — 이번 세션 pull 보다 먼저 돌므로 마지막 fetch 기준이다(성립 근거: 자동 pull 은 fetch 와 merge 를 나눠 하므로, merge 가 충돌로 거부돼도 추적 ref 는 갱신된다). **한계**: 훅이 pull 을 아예 시도하지 않는 상태(비-main·진행 중·kill-switch)가 계속되면 `origin/main` 이 갱신되지 않아 그 사유를 말해야 할 때 무음일 수 있다(부트스트랩 구멍). `origin/main` 없으면 판정 불가라 무음. **fetch 지속 실패**: 추적 ref 는 fetch 가 성공해야 전진하므로, 자동 pull 의 fetch 가 계속 실패하면 behind 가 0 으로 보여 위 사유가 전부 침묵한다. 그래서 `session-start-pull.sh` 가 git dir 에 빈 파일 두 개의 mtime 을 남긴다 — `claude-autopull-attempt`(마지막 성공 뒤 **첫** fetch 시도. 모든 skip 게이트 뒤·fetch 직전에 찍어 워치독 kill 뒤에도 남는다)와 `claude-autopull-ok`(마지막 fetch 성공 — rc 0, `CLAUDE_AUTOPULL_VERIFY=0` 경로 포함). 둘 다 지우지 않는다. attempt 가 ok 보다 새것(ok 없음 포함)이고 임계일(`CLAUDE_BRIEF_AUTOPULL_DAYS`, 기본3) 이상 지났으면 `자동 pull 의 fetch 가 N일째 성공하지 못했다(마지막 성공 <날짜>|성공 기록 없음)` 에 재현 명령(`GIT_TERMINAL_PROMPT=0 git -C ~/.claude -c credential.helper= fetch origin main` — 훅처럼 helper 를 꺼야 사람의 fetch 는 되는데 훅만 실패하는 경우가 가려진다)과 탈출구(`CLAUDE_AUTOPULL_VERIFY=0`)를 붙여 알린다. **behind 0 에서도** 내되 훅 게이트(OFF·`.autopull-off`·detached·`main` 아님·진행 중)에 걸리면 무음이다 — 훅이 fetch 를 시도하지 않는데 "실패 중"이라 하면 거짓이다. behind>0 이면 게이트 뒤·갈라짐 앞이다(훅은 fetch 가 실패하면 merge 전에 끝낸다). 스크립트의 비교는 부재를 `-e` 로 명시한다 — Ubuntu dash 는 `[ a -nt 없는파일 ]` 이 거짓이라(Git Bash sh 는 참) `-nt` 에 맡기면 성공 기록이 없는 Linux 머신에서 attempt 가 매 세션 새로 찍혀 영구 무음이 된다(WSL 실측, 테스트 P4 가 CI 의 dash 에서 잡는다). 파일명은 브리프의 `AUTOPULL_STAMPS` 가 정본이고 테스트가 스크립트 본문과의 일치를 잠근다. 한계: 이 스크립트를 받기 전의 머신은 스탬프가 없어 무음이다 · 브리프는 이번 세션 pull 과 동시에 돌므로 한 세션 늦다(이미 실패 중이던 머신은 이번 fetch 가 성공해도 그 세션에 한 번 더 뜬다) · fetch 가 한 번만 실패한 뒤 임계일 넘게 세션을 열지 않으면 다음 브리프가 한 번 알린다(attempt 는 "마지막 성공 뒤 첫 시도"라 공백 기간만큼 일수가 쌓인다 — 그 세션 fetch 가 성공하면 다음부터 무음) · 자동 pull 이 이미 깨진 머신은 이 변경도 자동으로 받지 못하므로 한 번 수동으로 당긴다(`git -C ~/.claude pull --ff-only`). 수동 pull·`/e`·`post-checkout` 은 ok 를 찍지 않는다 — 자동 pull 이 깨져 있으면 계속 알리는 것이 맞다. **존재 이유**: SessionStart pull 훅은 `async` 라 그 stdout 이 첫 턴 뒤에 도달하는데(이 파일 상단 `hooks.SessionStart` 참조), 레포가 밀린 사실은 세션 시작에 알아야 하므로 동기인 브리프가 대신 말한다. **O 세션 repo 밀림**: hook stdin JSON 의 `cwd`(전 이벤트 공통 필드이고 worktree 진입·`cd` 를 따라간다 — 형제 훅 `dlc-task-router.js`·`guard-worktree-edit.js` 와 같은 입력원, TTY 직접 실행은 `process.cwd()` 폴백 + stdin 타임아웃 백스톱)가 가리키는 repo 가 upstream 보다 뒤처졌거나 미커밋이 임계일(`CLAUDE_BRIEF_DIRTY_DAYS`, 기본3) 이상 방치됐으면 한 줄. **N 과 나누는 이유는 처방이 다르기 때문** — `~/.claude` 는 자동 pull 훅이 있어 "왜 훅이 못 따라잡았나"가 답이고, 다른 repo 는 훅이 없어 "직접 pull" 이 답이다. 기준 ref 는 **`@{upstream}` 뿐이고 폴백하지 않는다** — `origin/HEAD`·`origin/main` 으로 떨어뜨리면 push 하지 않는 feature 브랜치가 전부 "main 에서 갈라진 지 오래됨"으로 걸린다(실측: 한 repo 의 worktree 68개 중 60개). 조치할 것도 없고 사라지지도 않는 줄은 신호를 죽인다 — K 를 확장하지 않은 이유와 같다. 출력에 **기준 ref 이름을 넣는다**(`origin/dev 대비 336커밋 뒤처짐`) — 무엇 대비인지 없으면 확인할 수 없다. 미커밋 나이는 원격과 무관한 사실이라 upstream 이 없어도 알린다(`--no-optional-locks` 로 사용자 repo 의 `index.lock` 을 만지지 않고, `-unormal` 을 명시해 `status.showUntrackedFiles` 설정에 흔들리지 않게 한다 — 디렉토리 mtime 은 안쪽 파일 편집으로 안 바뀌어 나이가 거짓이 된다). **한계**: N 과 같이 캐시된 ref 로만 판정하는데 이쪽에는 그 ref 를 갱신할 자동 fetch 주체가 없다(N 은 pull 훅이 갱신해 준다) — 한 번도 fetch 하지 않은 채 밀린 구간은 무음이다. 미커밋 파트에는 그 구멍이 없다. **삭제된 파일**은 stat 이 안 돼 나이를 모르고, 접힌 untracked 디렉토리(`?? dir/`)도 건너뛴다 — 디렉토리 mtime 은 안쪽 파일 편집으로 안 바뀌어 나이가 거짓이 되기 때문이다(둘 다 알려진 사각). `-uall` 로 펼치는 방법은 쓰지 않는다: gitignore 안 된 `venv/`·`node_modules/` 하나가 매 세션 조치 불가능한 줄을 만들고, 목록이 크면 출력이 버퍼를 넘겨 신호 자체가 사라진다(실측 24k 파일 ENOBUFS). **fetch 신선도**: upstream 은 있는데 밀림이 0 이고 마지막 갱신이 임계일(`CLAUDE_BRIEF_FETCH_DAYS`, 기본3) 이상 지났으면 `N일째 fetch 하지 않았다 — … 밀렸는지 알 수 없다` 로 **침묵 대신 모름**을 말한다(밀림을 이미 말하고 있으면 덧붙이지 않는다). 갱신 시각은 위 스탬프→ref 파일→`packed-refs` mtime 순으로 보고, 셋 다 없으면 아무 말도 하지 않는다 — 갓 clone 한 repo 에 거짓 경고를 내지 않기 위해서다. 안전장치: repo 설정의 `core.fsmonitor` 는 `-c core.fsmonitor=` 로 무력화하고(훅은 사용자 액션 없이 임의 repo 에서 도는데, git 은 그 값에 적힌 **명령을 실행**한다), 상속된 `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE` 은 스크럽한다(`-C` 를 이겨 다른 repo 를 답하게 만든다). **WSL 한계**: Windows 에서 만든 linked worktree 의 `.git` 에는 Windows 절대경로가 박혀 있어 WSL 의 git 이 못 푼다 → 그 조합에서는 무음이다(git 자체가 실패하는 것이라 모든 git 도구에 동일하게 적용된다). `~/.claude` 자신은 git common dir 비교로 제외(worktree 도 걸린다 — N 과 중복 금지). 동기 hook 이라 **시간 예산**(2s)을 들고 각 git 호출 전에 확인하고, mtime 조회는 상한을 둔다 — fail-open 은 예외 정책이지 시간 정책이 아니다. **N 의 라벨도 감시 대상에서 유도하도록 고쳤다** — 하드코딩된 `~/.claude` 는 `CLAUDE_BRIEF_REPO` 로 다른 repo 를 겨눴을 때 "~/.claude 가 뒤처졌다"고 거짓 보고했다(실측 확인). **되돌리기**: 이 repo 는 자기 배포 채널이라(SessionStart pull) 결함이 나가면 머신마다 다음 세션에 도착한다 — 즉시 차단은 `CLAUDE_BRIEF_CWD_OFF=1`(settings `env` 에 넣으면 pull 이 닿는 머신부터 적용), 되돌림은 이 커밋 revert 후 push. 전부 fail-open + **신호별 예외 격리**(한 신호가 죽어도 나머지 라인 보존 — stdout write 가 마지막 1회라서). 테스트 `session-brief.test.js`.
- **`session-fetch.js`** (SessionStart hook — **async**) — 세션이 열린 repo 의 remote-tracking ref 를 **fetch 만** 해서 갱신한다(merge 안 함 → 로컬 커밋·작업트리 불변). 존재 이유: 브리프의 밀림 판정은 캐시된 ref 로만 하는데 `~/.claude` 밖에는 그 ref 를 갱신할 주체가 없어서, "한 번도 fetch 하지 않은 채 밀린" 구간이 통째로 무음이었다(2026-08-31 실측: `origin/dev` 가 2.7일 얼어 있는 동안 원격은 37커밋 앞서 있었다). skip 조건: `~/.claude` 자신(기존 pull 훅 담당)·최근 fetch(`CLAUDE_SESSION_FETCH_MIN_MINUTES`, 기본15분, `.git/claude-fetch-<remote>` 스탬프 기준 — `FETCH_HEAD` 는 repo 전역이라 다른 remote 를 fetch 해도 갱신돼 이쪽을 건너뛰게 만든다)·upstream 없음(무엇 대비인지 정할 수 없으면 네트워크를 쓸 이유가 없다)·`CLAUDE_SESSION_FETCH_OFF=1`. **인증 프롬프트 금지** — 물어볼 경로 자체를 없앤다 — `GIT_TERMINAL_PROMPT=0` + `-c credential.helper=` + `-c core.askPass=` + `GIT_SSH_COMMAND="<사용자 값 보존> -oBatchMode=yes -oConnectTimeout=10"`. **`GIT_ASKPASS=echo` 는 쓰지 않는다** — 실패하는 helper 가 아니라 프롬프트 문자열(`Username for …`)을 자격증명으로 되돌려준다. **사용자 workspace 를 만지지 않는다**: `--no-write-fetch-head`(사용자의 `FETCH_HEAD` 를 덮으면 이어 친 `git merge FETCH_HEAD` 가 다른 브랜치를 머지한다) · `--no-recurse-submodules`·`--no-auto-maintenance`(추적 ref 하나만 갱신) · `-c core.hooksPath=<없는 경로>`(fetch 는 그 repo 의 `reference-transaction`·`pre-auto-gc` 훅을 실행한다 — `core.fsmonitor` 와 같은 문제) · `git rev-parse --local-env-vars` 전량 스크럽(`GIT_COMMON_DIR` 하나만 남아도 무관한 repo 를 fetch 하고 거기 스탬프를 남긴다). 스탬프는 **추적 ref 단위**이고(remote 단위면 `main` 세션이 `feat` 세션을 굶긴다) 성공·실패 모두 찍는다(닿지 않는 원격에 매 세션 재시도 방지). 브리프의 `CLAUDE_SESSION_BRIEF_OFF`·`CLAUDE_BRIEF_CWD_OFF` 도 존중한다(출력만 끄고 fetch 는 계속). ref 가 움직였고 할 말이 생겼을 때만 브리프의 `currentRepoLine` 을 **가져다 써서**(두 곳에서 문장을 만들면 갈라진다) 한 줄 낸다 — 안 그러면 사용자는 갱신 사실을 한 세션 늦게 안다. 테스트 `session-fetch.test.js`(로컬 clone fixture, 네트워크 미사용).
- **`hook-cwd.js`** — 위 두 SessionStart 훅(`session-brief.js`·`session-fetch.js`)이 함께 쓰는 공유 모듈(hook 미등록). (1) hook stdin JSON 의 `cwd` 읽기 — 두 훅이 같은 규약을 쓴다: TTY 면 `process.cwd()` 폴백, JSON 불량·잘림도 폴백, 안 닫히는 stdin 은 타이머가 끊는다(그래서 unref 하지 않는다 — 그 타이머가 유일한 진행 보장이다). (2) **테스트 전용 시간 배수** `scaleMs` — 두 훅이 직접 거는 시간 상한(git 호출 timeout·브리프 O 예산·fetch 상한·이 stdin 대기·stdout 백스톱)이 모두 env `CLAUDE_BRIEF_FETCH_TEST_TIME_SCALE` 를 곱한다(ssh·http 의 네트워크 상한은 따르지 않는다). 1~20 으로 자르고 숫자가 아니면 무시한다 — 미설정이면 지금 값 그대로이고, 하한 1 은 운영 상한보다 줄이지 않기 위해서다(0 은 `execFileSync` 에서 "상한 없음"이다). 두 훅의 테스트가 10 을 넣는다 — 프로세스 생성 부하(Windows 에서 검증을 겹쳐 돌릴 때)에서 상한이 만료돼 기능 단언이 흔들렸기 때문이다(2026-10-02 실측: 8벌 동시 실행에서 `session-fetch.test.js` 5/8·`session-brief.test.js` 8/8 실패, git 호출별 2초 timeout 과 O 신호 2초 예산 만료). 바깥에서 `=1` 로 돌리면 운영 상한 그대로 종단 실행된다. **운영에 두지 않는다** — 최악 합이 settings 의 훅 timeout(brief 10s·fetch 30s)을 넘으면 하니스가 훅을 죽이고, 하니스는 자손을 거두지 않아 git 이 고아로 남는다(상한 20 은 그 피해의 상한이다). `session-start-pull.sh` 는 이 값을 따르지 않는다. 테스트 `hook-cwd.test.js`.
- **`usage-count.js`** (`improve.sh deep` ⑪ 가 호출, hook 아님) — transcript JSONL 을 파싱해 skill/subagent/codex tool_use 레코드만 집계. 프라이버시: 카운트+고정 slug 만 출력, 파일명·경로·원문·args 미출력(raw grep 대신 스키마 파싱). `CLAUDE_TRANSCRIPT_DIR` redirect(테스트). 테스트 `usage-count.test.js`.
- **`plan-lint.js`** — §10 plan 참조 무결성 **순수 판정 + CLI**(hook 아님). `lintPlan(text)`→위반 배열: frontmatter 필수키 non-empty · `status` 값 · 6 H1 섹션 · **끊긴 Acceptance 참조**(본문의 "Acceptance N/①-⑳" ↔ `# Acceptance` 항목 수; frontmatter·헤더·# Acceptance 섹션·백틱/따옴표 인용은 스캔 제외해 자기참조 오탐 차단). 의미 판정(title↔Goal 정합)은 LLM 몫. 강제 3지점: CI `lint.yml`(그 PR 변경 plan 만·`continue-on-error` 비차단) · `/c` 2단계(채택 plan) · `/e` 3단계(active plan, write 후) · `improve.sh` 8(전 tracked plan). `CLAUDE_PLAN_LINT_OFF=1` 로 CLI no-op. 테스트 `plan-lint.test.js`.
- **`frontmatter-lint.js`** — skill·agent frontmatter 형식 **순수 판정 + CLI**(hook 아님). `lintFrontmatter(text)`→`{ fields, violations: [{line, message}] }`. 소비자 셋 — Claude Code(엄격 YAML 파싱이 실패하면 값을 따옴표로 감싸 다시 파싱하고, 그래도 실패하면 필드를 경고 없이 버린다. CRLF 파일에서는 재시도도 실패한다 — 2.1.285 `claude plugin validate` 실측), YAML 파서, `scripts/bootstrap/sync_codex_agents.py`(한 줄 `key: 값` 만 받고 따옴표를 unescape 하지 않는다) — 가 **같게 읽는 한 줄 형식만** 통과시킨다. 유효한 YAML 이어도 빈 줄·주석·목록·여러 줄 값·escape 는 거부한다. 허용 형식 요약(정본은 스크립트 머리 주석): 모든 줄이 `key: 값`(key 는 영문자로 시작, camelCase 가능, 값 비지 않음) · 평문은 YAML 지시자로 시작하지 않고 `: `·` #` 가 없고 `:` 로 끝나지 않으며 앞뒤에 공백 문자가 없음 · 따옴표 값은 한 쌍이고 안에 그 따옴표와 `\` 없음 · 어느 줄에도 `---`(Claude Code 추출이 거기서 끝난다)·탭·제어문자 등 파서마다 갈리는 문자 없음 · 닫는 `---` 뒤 줄바꿈 · 중복 키·YAML 1.1 불리언 키·null(`~`)·특수 태그(`=`·`<<`)·날짜 값 없음 · `name`·`description` 필수, `name` 은 숫자·불리언 형태 금지(Claude Code 가 거부). BOM 하나·CRLF 는 통과, 잘못된 UTF-8 은 위반. 그 밖의 타입 해석 차이(`yes`·`1:20`·`0b101` — Claude Code 는 문자열, PyYAML 은 다른 타입)는 보지 않는다. CLI 출력 `<파일>:<줄>: <메시지>`, 위반·읽기 실패면 exit 1·인자 없으면 2, kill-switch 없음. 강제 2지점: `verify.sh` syntax 축(git 이 아는 `skills/*/SKILL.md`·`agents/*.md` — 0개면 FAIL) · `improve.sh` 4(같은 발견, CI `--ci` 게이트). 테스트 `frontmatter-lint.test.js`.
- **`native-overlap-lint.js`** (`improve.sh` ⑨ 가 호출, hook 아님) — 네이티브 중복 대장의 **신선도만** 판정하는 순수 함수 + CLI. `nativeOverlapStatus({text, today, installedVersion, maxAgeDays, deep})`→메시지 배열: `checked` 경과 여부 + deep 이면 **delta 창**(`checked_version` → 설치 버전; 동일·역전·비교불가·미확인 분기). 중복 여부 자체는 판정하지 않는다(그건 changelog 를 읽는 LLM 몫 — SKILL §6). **전 경로 `[info]`·항상 exit 0** — 리마인더라 err/warn 카운터를 오염시키지 않고, 대장 부재·frontmatter 불량·날짜 불량·미래 날짜는 사실만 적고 skip. 날짜 처리: `today` 는 **로컬 달력**(UTC instant 와 비교하면 UTC+n 에서 오늘이 "미래"가 된다), 왕복 대조로 검증(`2026-02-30` 이 `Date.parse` 에서 03-02 로 롤오버하는 것 차단), `-1일`은 다머신 TZ 차로 보고 오늘로 흡수. 버전 비교는 끝까지 앵커(`v` 접두 허용) — `2.1.222-beta` 를 "같음"으로 단정해 조회를 건너뛰지 않도록 `null`(수동 판단)로. env: `CLAUDE_IMPROVE_LEDGER`(대장 경로), `CLAUDE_IMPROVE_NATIVE_MAX_AGE_DAYS`(임계, **유효=1 이상 유한 정수**, 그 외 0·음수·비숫자·`Infinity` 는 전부 기본 45), `CLAUDE_IMPROVE_CC_VERSION`(설치 버전 주입 — improve.sh 가 `claude --version` 결과를 넘긴다). 테스트 `native-overlap-lint.test.js`(improve.sh 점검 번호 1..N 유일 가드 포함).

syntax 검사와 단위테스트는 **`bash scripts/verify.sh`** 가 단일 소스이고 CI `lint.yml` 이 축별로 그것을 호출한다. syntax 축은 JS 문법(`node --check`)과 skill·agent frontmatter 형식(`frontmatter-lint.js` — 대상이 0개면 FAIL)을 본다. 테스트 목록은 **수기가 아니라 glob 발견** — `scripts/**/*.test.js`·`*.test.sh`·`test_*.sh`·`test_*.py` 를 자동으로 집는다(수기 목록이 실존 테스트 3개를 CI 밖에 남겨둔 2026-09-07 사고의 재발 방지). 발견 대상은 `git ls-files --cached --others --exclude-standard`, 즉 추적 파일과 아직 add 하지 않은 새 파일뿐이라 main checkout 의 ignored 산출물(shell-snapshots·plugins·backups)은 검사하지 않는다 — ignored 산출물 때문에 main 에서만 나던 실패는 없어진다(아직 add 하지 않은 새 파일은 로컬에서만 잡히므로 그만큼은 CI 와 다를 수 있다). git 작업트리 밖에서 실행하면 대상을 찾을 수 없어 곧바로 FAIL 한다. CI 는 여기에 더해 **비밀 스캔 백스톱** `scripts/ci-secret-scan.sh <base> [<head>]` 를 돈다 — PR 은 PR head 를 checkout 된 merge 커밋의 첫 부모(merge 를 만든 시점의 base 브랜치 tip — payload 의 `base.sha` 는 옛 값일 수 있다) 기준으로(merge 커밋을 보면 main 쪽 추가분까지 PR 탓이 된다), main push 는 push 전 tip 을 기준으로 그 뒤 커밋이 `settings.json`·`plans/*.md` 에 추가한 줄을 로컬 pre-push 가드와 같은 스크립트로 검사한다(훅이 없거나 `--no-verify` 로 건너뛴 push 의 사후 탐지 — 막는 것이 아니고, PR 없이 push 한 feature 브랜치는 보지 않는다). base 는 가드에 push 대상의 remote sha 로 넘어가 그것만 이미 공개된 것으로 빠지고, checkout 의 추적 ref(검사 대상 커밋을 이미 담고 있다)는 가드가 보지 않는다. shallow checkout 이면 잘린 이력을 root 처럼 스캔하게 되므로 스캔하지 않고 실패한다(`fetch-depth: 0` 필요). all-zero·빈 base, 그리고 checkout 에 없는 base(force push 로 옛 tip 이 사라진 경우)는 건너뛰지 않고 전체 이력을 본다(이 repo 는 약 1초). 가드가 출력하는 매치 값과 로컬 전용 `--no-verify` 안내는 가린다 — public repo 의 Actions 로그는 공개다. Rollback 절의 이력 재작성 뒤 main push 는 옛 tip 이 없어 전체 이력을 보지만, 가드 패턴으로 두 경로만 보므로 **유출 제거 확인이 아니다**(그 절의 `git log -S` 가 그 역할). 한계: main push 범위에 merge 커밋이 있고 main 쪽 이력에 이미 토큰이 있으면, 가드의 `-m` 이 그 줄을 merge 의 추가분으로 다시 잡아 빨개진다(토큰을 재작성으로 지우는 것이 해법). 검사 스크립트는 그 PR 자신의 것이라 가드를 약화한 PR 은 스스로를 통과시킨다(1인 소유 repo 라 감수). 테스트 `ci-secret-scan.test.sh`. 로컬 미설치 도구는 `[skip]` 으로 표시되고 마지막 줄이 `ALL PASS (skip: …)` 가 된다 — **skip 붙은 통과를 무조건 통과로 읽지 말 것**. 개별 테스트도 필요한 도구가 없으면 종료 코드 77 로 끝내 같은 `[skip]` 이 된다(예: `record-verified.test.sh` 의 `jq` — CI(`CI` 환경변수)에서는 1 로 실패). 통과한 테스트가 `SKIP ` 으로 시작하는 줄을 찍으면 케이스 단위 skip 으로 요약에 `<파일>(case)` 가 붙는다. `NOTE ` 로 시작하는 줄은 무엇을 돌렸는지 알리는 표시(예: ps1 엔진 실행 수)라 그 테스트의 `ok` 줄 아래에 보이기만 하고 skip 으로 세지 않는다.

CI 의 **검증 기록** `record-verified` job — main push 의 lint 가 통과하면 그 커밋 sha 를 `ci/verified` 브랜치의 기록 커밋(파일 `main-sha` 하나, 부모 = 직전 기록)으로 남긴다. SessionStart 자동 pull 은 이 기록까지만 ff 한다(아래 `hooks.SessionStart` (1)) — `main-sha` 가 둘 사이의 계약이다(repo 해시 길이의 소문자 16진수, 개행 없음). main 커밋을 가리키는 ref 를 옮기지 않는 이유: GITHUB_TOKEN 은 `workflows` 권한을 받을 수 없어 workflow 파일이 바뀐 커밋으로 ref 를 옮기는 것이 거부될 수 있다. workflow 파일이 없는 트리의 기록 커밋은 이 job 의 REST 경로로도 만들어진다(2026-09-26 첫 기록 `38aae27` 으로 확인). 쓰기 권한은 이 job 만 받고(workflow 최상위는 `contents: read`) checkout·repo 코드 없이 REST API 만 쓴다 — 그 run 블록은 lint job 의 `record-verified.test.sh` 가 그대로 꺼내 가짜 `gh` 로 검사한다(jq 필요). 기록 값은 기록 시점에 main 에서 도달 가능한 커밋뿐이고 뒤로 가지 않는다(재작성으로 main 에서 빠진 커밋의 늦은 run·re-run 은 기록하지 않고, 먼저 push 된 커밋의 run 이 늦게 끝나도 기록을 되돌리지 않는다). API 오류는 404(main 밖)를 빼고 job 실패로 드러낸다. 한계: 연속 push 에서 대기 중인 기록 job 이 GitHub concurrency 의 교체 규칙으로 취소되면 그 tip 은 다음 main push 까지 기록되지 않는다(`[skip ci]` push 도 기록되지 않는다). 원격에 `ci` 라는 브랜치는 만들 수 없다(`ci/verified` 와 경로가 겹친다). 되돌리기(기능 전체 제거)는 **client 쪽(`session-start-pull.sh`·`session-brief.js`) revert 를 먼저 머지 → 기록이 그 커밋까지 전진한 것을 확인 → job 제거** 순서다 — push 이벤트는 push 된 커밋의 workflow 로 돌아서, 한 push 에 담으면 그 커밋에는 기록 job 이 없어 revert 가 자동 pull 로 전달되지 않는다.

> `plan-match.js` — branch→§10 plan 매칭 **순수 모듈**(`anchorMatches`·`activePlanPath`). `session-brief`(닫히지 않은 plan 신호)·`dlc-early-stop`(plan drift 축)·`dlc-evidence-ledger`(Bash 로 고친 plan 인정)가 공유해 한쪽만 바뀌어 어긋나는 것을 막는다 — ledger 는 early-stop 이 보는 것과 같은 plan 을 봐야 한다.

#### `pre-commit-check.ps1`
`pre-commit` 모드는 staged `settings.json`·`plans/*.md`, `pre-push` 모드는 stdin 의 ref 줄로 받은 push 커밋에서 push 대상 ref 가 이미 가진 것(각 줄의 remote sha — 원격이 알려 준 현재 값, 삭제 줄 포함)을 뺀 범위가 두 경로에 **추가한 줄**을 검사한다. settings.json 은 금지 키 (`mcpServers`, `apiKeyHelper`, `awsCredentialExport`, `awsAuthRefresh`) + 토큰 패턴 (Anthropic/OpenAI/GitHub/GitLab/AWS/GCP/Slack/JWT/PEM 등), plans 는 토큰 패턴만. 검출 시 exit 1. push 검사는 `git log -p` 가 추가 줄을 빠뜨리는 경로를 옵션으로 막는다. 넣었다 지운 사이드 브랜치는 `--full-history`, merge 해결에서만 들어온 줄은 `-m` + `log.diffMerges=separate`, root 커밋은 `log.showRoot=true`, rename 짝짓기는 `log.follow=false`, NUL 바이트·`-diff` attributes·`core.bigFileThreshold` 는 `--text`, `git replace` 는 모든 git 호출의 `GIT_NO_REPLACE_OBJECTS=1`(원격 태그를 커밋으로 peel 할 때 포함)로 막는다. 색·prefix·textconv 설정은 명시 플래그로 덮고, pathspec 환경변수(`GIT_*_PATHSPECS`)는 지우고, 로케일은 `LC_ALL=C`(잘못된 UTF-8 바이트가 섞인 줄도 검사)로 둔다. 이 중 git 옵션은 엔진마다 한 곳의 묶음(sh `git_global`·`git_walk`·`git_patch`, ps1 `$gitGlobal`·`$gitWalk`·`$gitPatch`)에 둔다 — 전역 옵션·걷기 묶음은 두 log 스캔(비밀 스캔과 아래 비공개 용어 push 스캔)이, 패치 묶음은 거기에 비공개 용어 staged 패치까지 세 곳이 쓴다. 호출마다 다른 `-m`·`-M`·`-p`·pathspec 과 환경변수는 묶음 밖이다. 한 스캔만 옵션을 잃어 추가 줄을 놓치는 일을 막으려는 것이다. sh 는 push 커밋과 제외 커밋(`^<sha>`)을 중복 없이 `git log --stdin` 으로 넘긴다 — 인자로 넘기면 새 원격에 ref 수백 개를 push 할 때 Windows 명령줄 한계(32,767자)를 넘는다. `--stdin` 은 입력이 비면 HEAD 로 대체하므로 입력을 먼저 만들고 비면 차단한다. ps1 도 `Get-AddedLines` 에서 같은 입력을 `git log --stdin` 으로 넘긴다. 해석할 수 없는 ref 줄(sha 는 repo 해시 길이 — sha1 40자·sha256 64자 — 여야 한다)·커밋이 아닌 push 객체·git 오류는 차단한다(fail-closed). 단 remote sha 가 로컬 커밋으로 풀리지 않으면(아직 fetch 하지 않은 커밋·blob·tree) 차단하지 않고 제외만 생략한다 — 더 넓게 스캔하는 쪽이다. ps1 은 git 을 PATH 로 찾은 절대경로의 `System.Diagnostics.Process` 로 부른다 — PS5.1 의 native stderr 종료 오류·콘솔 코드페이지 디코딩을 피하고, bare `git` 이면 Windows 가 repo 루트의 `git.exe` 를 먼저 실행하는 것을 막는다. stdin 도 UTF-8 로 읽는다. remote-tracking ref 를 "이미 공개됨" 으로 보지 않는 이유: 다른(private) 원격의 것일 수 있고, 이력 재작성 뒤에는 오래된 값이 남고, pushurl 이 여러 개면 URL 마다 가진 것이 다르다(훅이 URL 마다 따로 불리고 remote sha 도 URL 별로 온다 — 2026-09-26 실측). 알려진 한계: 새 브랜치 push(remote sha 가 all-zero)는 base 이력 전체를 다시 본다(`~/.claude` 505 커밋에서 sh 0.75s·ps1 0.47s). 그래서 원격 이력에 이미 토큰이 있으면 재작성할 때까지 새 브랜치 push 가 막히고, 가드 패턴을 추가·완화할 때는 과거 이력 전체에 매치가 없는지 먼저 확인해야 한다(아니면 모든 새 브랜치 push 가 막힌다).

> `settings.json` 이 untracked 가 된 뒤로 settings 검사는 **실제로는 돌지 않는다** — staged 목록이나 push 범위에 그 파일 변경이 있을 때만 진입한다. 실수로 다시 추적되면 되살아나도록 코드는 남겨 뒀고, 지금 실효 대상은 `plans/*.md` 다.

`pre-push` 모드는 추가로 **`main`/`master` 직접 푸시를 차단**한다(`.sh`·`.ps1` 동일). 단 **repo 루트가 `~/.claude` 면 면제** — 이 repo 는 main push 허용(2026-08-05 사용자 승인, CLAUDE.md §8)이지만 이 가드는 install-hooks 를 돌린 **모든 repo 가 공유**하므로 제거 대신 repo 루트로 범위를 좁혔다. `$HOME` 과 `--show-toplevel` 중 한쪽이 심볼릭 링크일 수 있어 양쪽을 실제 경로로 해석해 비교한다. linked worktree 의 `--show-toplevel` 은 그 worktree 디렉토리라 면제되지 않는다 — worktree 에서는 작업 브랜치만 push 하고 `~/.claude` 의 main push 는 main checkout 에서 하는 흐름에 맞춘 의도된 동작이다. 커버리지: `pre-commit-check.test.sh` — 실제 커밋 fixture 로 pre-commit 13(staged blob 의 `git replace` 포함), pre-push 스캔 51(선형·merge 토폴로지·사용자 log/diff 설정·attributes·pathspec 환경변수·`git replace`·NUL·잘못된 UTF-8·태그·손상 객체·입력 불량·커밋을 stdin 으로 넘김(ref 50줄·`git log` argv 에 sha 없음 — sh)·HEAD 가 아닌 push ref·입력 생성 실패, 그리고 제외 기준 — 대상 ref 가 가진 커밋만 제외·다른 브랜치 추적 ref 무시·재작성 뒤 오래된 추적 ref·로컬에 없는/blob/tree/annotated tag 인 remote sha·짧거나 16진수가 아니거나 repo 해시 길이와 다른 sha·sha256 repo·삭제 줄과 여러 줄의 합집합·replace 된 원격 태그), main 차단 5(면제 2 + 차단 2 + 무관 브랜치 1), 비공개 용어 57(아래 — 합성 용어만. 범위 판정 일부는 `core.hooksPath` 로 실제 `git commit`·`git push` 가 훅을 부르게 해서 git 이 훅에 넘기는 환경까지 재현한다. 사용자 설정(`color.ui=always`·`diff.noprefix`·`diff.mnemonicPrefix`·`log.showRoot=false`·`log.diffMerges=off`·아무것도 출력하지 않는 textconv)과 비ASCII 용어가 든 경로(`core.quotePath` 기본값)에서 용어를 놓치거나 경로를 잘못 적거나 숨길 경로를 드러내지 않는지도 본다 — 용어 스캔이 의존하는 공유 옵션을 잃으면 걸린다). 차단은 `[BLOCKED]` 와 기대 사유가 출력에 있어야 통과로 센다(사유가 `=` 로 시작하면 색 코드를 벗긴 출력에 `  - <사유>` 줄이 그대로 있어야 한다 — sh·ps1 문자열 동일성). pwsh 가 있으면(`$PWSH` 또는 PATH) 같은 케이스를 ps1 로도 돌린다. 끝에 엔진별 실행 수를 `NOTE [ps1] ran N`(Windows PowerShell 5.1 이 따로 있으면 `NOTE [ps51] ran M` 도)으로, pwsh 가 없으면 `SKIP [ps1] no pwsh` 를 찍는다 — 후자는 verify 요약에 `pre-commit-check.test.sh(case)` 로 남는다. CI(`CI` 환경변수)에서는 pwsh 가 없으면 실패한다(ps1 검증이 조용히 빠지지 않게).

**비공개 용어**(`~/.claude` 에서만 — 사용자 관점 요약은 위 Install D 절): 대상 판정은 현재 repo 의 `git rev-parse --git-common-dir` 이, git 변수(`GIT_DIR`·`GIT_COMMON_DIR`·`GIT_WORK_TREE`·`GIT_INDEX_FILE`)를 지운 채 `~/.claude` 에서 물은 common dir 과 같은 디렉토리인가다(sh `-ef`, ps1 은 git 이 낸 절대경로끼리 비교) — linked worktree 의 훅은 git 이 export 한 `GIT_DIR` 을 물려받아, 지우지 않으면 `~/.claude` 에 물어도 현재 repo 가 답한다. main checkout·linked worktree·gitfile `.git`(`--separate-git-dir`)이 대상이고, 위 main push 면제의 `--show-toplevel` 판정과 다르다. `$HOME/.claude/.git` 이 없으면(CI·다른 머신) 비대상이고, git 이 답하지 못하면 현재 디렉토리가 `~/.claude` 아래일 때만 차단한다 — 다른 repo 는 어떤 경우에도 막지 않고 목록도 열지 않는다. 목록은 UTF-8, 앞 BOM·줄 끝 CR·앞뒤 공백을 떼고 빈 줄·`#` 줄은 건너뛰며, 보고하는 줄 번호는 물리 줄 번호다. sh 는 목록을 awk 로 한 번 정규화해 매처 awk 에 환경변수로 넘기고(`LC_ALL=C` 바이트 비교, ASCII 만 소문자화, 경계 판정은 항목을 정규식 이스케이프해 줄마다 한 번 검색 — 긴 줄에서도 선형), ps1 은 `ToLowerInvariant` 라 비ASCII 대소문자까지 접는다(ps1 이 더 엄격 — 경계는 소문자화 전 글자로 판정해 sh 와 같다). pre-commit 은 `git diff --cached -M -U0 --text` 의 추가 줄과 `--diff-filter=ACR` 새 경로(pre-commit 은 merge·cherry-pick·rebase·commit-check 에서 안 돌므로 조기 경고일 뿐), pre-push 는 위 비밀 스캔과 같은 하드닝 옵션으로 **모든 경로**의 추가 줄·새 경로, `git log` 의 메시지·작성자·커미터, 삭제가 아닌 모든 줄의 remote ref 이름을 본다. push 범위는 비밀 스캔 범위에서 `refs/remotes/origin/main` 이 가진 이력을 더 뺀다 — 가드 도입 전 이력의 이름이 새 브랜치 push 마다 걸리지 않게 하려는 것이고, 제외 기준을 origin(공개) 기본 브랜치 하나로 좁혀 위의 "추적 ref 를 공개로 보지 않는다"는 이유(다른 원격·재작성 뒤 옛 값)가 닿지 않게 했다(main 은 force-push 금지). 계약: 로컬 `origin/main` 이 뒤처지거나 없으면 범위가 넓어져 이미 공개된 이력에도 걸릴 수 있고(`git fetch origin` 으로 해소), `update-ref` 로 조작된 `origin/main` 은 그만큼 놓친다. merge 는 `-m` 이라 가드 도입 전 main 을 feature 로 merge 하면 main 쪽 줄이 다시 보고될 수 있다. annotated tag 본문은 보지 않는다(tag 이름은 ref 검사가 본다). 위반은 `private term (list line N) in <staged 경로|pushed 경로|commit <sha> message|commit <sha> identity|push ref (hidden)>` — 경로에 항목이 들어 있으면(긴 단어의 일부여도) `path (hidden)` — 이고, 목록 파일 자체가 걸리면 `git rm --cached` 안내를, 목록·범위·git 오류에는 목록 줄을 손으로 고치라는 안내(도구로 열거나 다시 쓰지 말 것)를 따로 낸다. git 2.31 미만(`--path-format` 을 모르고 되찍는다)은 범위 판정 불능으로 본다 — install-hooks 가 설치를 거부하는 버전이라 설치 뒤 PATH 의 git 이 바뀐 경우에만 생긴다. 비공개 용어 위반이 있으면 `--no-verify` 안내를 찍지 않는다(비밀 스캔까지 꺼진다). 한계: ps1 은 git 이 범위를 답하지 못할 때의 대체 판정에서 경로의 심볼릭 링크·junction 을 풀지 못해(.NET Framework 에 실제 경로 API 가 없다) 그 경우 `~/.claude` 안에서도 통과할 수 있다. 목록은 올바른 UTF-8 이어야 한다 — 잘못된 바이트가 든 항목은 sh 와 ps1 의 판정이 갈릴 수 있다.

`.git/hooks/` 에 직접 두지 않고 별도 파일 → repo 에 tracked. `install-hooks.ps1` 가 hooks 디렉토리의 `{pre-commit,pre-push}` sh wrapper 를 생성해서 이 스크립트로 위임.

#### `install-hooks.ps1` / `install-hooks.sh`
repo 의 hooks 디렉토리(`git rev-parse --git-path hooks` — linked worktree 에서 실행해도 공용 `.git/hooks`)에 세 hook 의 sh wrapper 생성 (`.ps1`=Windows, `.sh`=Unix, 동일 로직). `core.hooksPath` 가 다른 디렉토리를 가리키면(husky·lefthook 등, 설정 위치 불문) 그 도구의 훅을 덮거나 git 이 읽지 않는 `.git/hooks` 에 쓰는 대신 **설치하지 않고 exit 1** — 그 도구에서 `pre-commit-check` 를 부르게 한다. git 밖에서는 `Not inside a git repo.` 로 exit 1. `core.hooksPath` 가 없으면 `.git/hooks` 가 symlink 여도 그 경로에 설치한다. **git 2.31+ 필요**(`rev-parse --path-format`; 더 오래된 git 은 설치하지 않고 알린다). ps1 은 git 을 `pre-commit-check.ps1` 과 같은 Process 헬퍼로 부른다(PS 5.1 의 native stderr 종료 오류·콘솔 코드페이지 회피):
- `pre-commit`·`pre-push` — 비밀·금지 키·비공개 용어 가드(`pre-commit-check`)로 위임.
- **`post-checkout`** (main-autopull) — main/master 로 **branch 체크아웃 시** `git pull --ff-only origin <branch>` 로 origin 최신화. `git checkout` 을 절대 막지 않음(항상 exit 0). ff 실패는 "main 에 로컬 커밋 있음" 신호라 자동 rebase 하지 않고 경고만. **skip/무해 조건**: dirty·origin 없음·rebase/merge/bisect 중·default 브랜치가 main/master 아님. **hang 방지**: `GIT_TERMINAL_PROMPT=0`(프롬프트)+SSH `ConnectTimeout=10`+HTTP low-speed+백그라운드 pull 을 ~20s 폴링 워치독으로 kill (macOS 는 `timeout(1)` 부재라 자체 워치독). **비활성**: `export CLAUDE_AUTOPULL_OFF=1`. **제거**(rollback): `rm "$(git rev-parse --git-path hooks)/post-checkout"`(hook 은 비추적·머신별이라 스크립트 revert 로 안 지워짐; linked worktree 에서는 `.git` 이 파일이라 `.git/hooks` 경로가 틀린다).

UTF-8 (no BOM) + LF endings — Git Bash 가 인식. idempotent — 재실행 시 기존 pre-commit/pre-push 는 **바이트 동일 유지**하고 post-checkout 만 추가. 내용이 다른 기존 훅은 `<hook>.bak.<UTC yyyyMMddTHHmmssZ>`(이미 있으면 `.1`·`.2`…)로 옮겨 재설치마다 앞 백업이 남는다(정리는 수동). 커버리지: `install-hooks.test.js` — git 밖·linked worktree·`core.hooksPath` 거부·백업 보존을 sh 와(pwsh 가 있으면, `PWSH=<path>` 로 지정 가능) ps1 로 확인하고 `NOTE [ps1] ran (<pwsh 경로>)` 또는 `SKIP [ps1] pwsh not found` 를 출력한다(후자는 verify 요약에 `install-hooks.test.js(case)` 로 남는다). 새 머신 setup 시(=clone 한 repo 마다) 1회 실행. SessionStart 훅(세션 **시작** 시점 pull)과 역할 분리 — post-checkout 은 **체크아웃** 시점을 커버. hang 방지 처방은 이제 양쪽에 다 있다(2026-09-04 SessionStart 쪽에도 이식). 다만 post-checkout 은 아직 `pull` 전체를 감싸고 상한도 iteration 카운트라 Windows 에서 명목 20s 가 실제 ~24s 다 — SessionStart 쪽에서 고친 두 결함이 여기엔 남아 있다(발화 빈도가 낮아 후순위).

#### `prompt-gwl.py`
프롬프트에 정확히 `gwl` 만 입력하면 가로채서 `git worktree list` 를 현재 위치 `→` 마커와 함께 출력하는 UserPromptSubmit 훅 (모델 왕복 없음). 현재 위치는 `git rev-parse --show-toplevel`(git 밖이면 cwd)과 일치하는 경로 중 가장 긴 한 행 — worktree 가 main 아래 nest 돼도 main 행에 붙지 않고, symlink 경로(`/tmp`→`/private/tmp`)도 맞는다(`test_prompt_gwl.py`). `--porcelain` 기반이라 공백 포함 경로·bare·detached worktree 도 정확히 파싱. 글로벌 `settings.json` 엔 미등록 — 프로젝트별 `.claude/settings.json` 에 hook 으로 등록해 사용.

#### `gwl.ps1` (Windows / PowerShell)
`prompt-gwl.py` 와 같은 목적의 PowerShell 단축 함수 — `git worktree list` 를 출력하되 현재 worktree(`git rev-parse --show-toplevel`, git 밖이면 현재 디렉토리)와 일치하는 경로 중 가장 긴 한 행 앞에 `→` 마커(`prompt-gwl.py` 와 같은 규칙). `$PROFILE` 에서 dot-source 해 명령처럼 사용 (모델 왕복 없음). 임의 프로젝트용으로 `--porcelain` 을 쓰는 `prompt-gwl.py` 와 달리, 개인 worktree(`.claude/worktrees/<name>` 규약상 경로 무공백) 전용이라 단순 `git worktree list` split. `→` 가 Windows PowerShell 5.1(BOM 없는 UTF-8 을 ANSI 로 해석)에서 깨지지 않도록 **UTF-8 BOM** 으로 저장 (PS 7 은 양쪽 모두 읽음).

#### `install-gwl.ps1` (Windows / PowerShell)
`$PROFILE` (CurrentUserCurrentHost) 에 `. "$HOME/.claude/scripts/gwl.ps1"` 한 줄을 marker 블록(begin/end)으로 멱등 추가 — 두 marker 다 있으면 skip, 한쪽만 있으면(손상) 에러, 없으면 추가. 기존 inline `function gwl` 발견 시 경고. dot-source 대상은 항상 `~/.claude/scripts/gwl.ps1`(문서상 clone 위치)이라 레포가 다른 곳이면 경고만 하고 그대로 진행. 이후 `git pull` 로 `gwl.ps1` 갱신 시 profile 수정 없이 반영. **수동 1회 실행** 필요 — `~/.claude` 에서 `& ./scripts/install-gwl.ps1` (또는 `pwsh -File scripts/install-gwl.ps1`). 과거 `hooks.SessionStart` 가 자동 실행했으나, 무서명 원격 스크립트를 매 세션 자동 실행하는 위험 때문에 제거했다.

#### `gwl.zsh` (macOS / zsh)
`gwl.ps1` 의 zsh 대응물 — `git worktree list` 를 출력하되 현재 디렉토리를 포함하는 worktree 앞에 `→` 마커. `~/.zshrc` 에서 source 해 명령처럼 쓴다 (모델 왕복 없음). 개인 worktree(`.claude/worktrees/<name>`, 경로 무공백) 전용이라 단순 split. 현재 worktree 판정은 `git rev-parse --show-toplevel` **정확일치** — 이 레포는 worktree 가 main 하위에 nest 되어(main path 가 worktree path 의 prefix) prefix 방식이면 main 행에도 `→` 가 붙기 때문(`gwl.ps1`·`prompt-gwl.py` 도 2026-09-25 부터 같은 기준). macOS/zsh 는 UTF-8 기본이라 BOM 불필요. 인자는 받지 않는다 (`--porcelain` 등으로 split 이 깨지는 것 방지).

#### `install-gwl.zsh` (macOS / zsh)
`~/.zshrc` 에 `source "$HOME/.claude/scripts/gwl.zsh"` 한 줄을 marker 블록으로 멱등 추가 — `install-gwl.ps1` 과 같은 규약(두 marker 다 있으면 skip, 한쪽만이면 에러, 없으면 추가; 기존 inline `gwl` 발견 시 경고; 파일 끝 개행 보장; `~/.zshrc` 없으면 생성). source 대상은 항상 `~/.claude/scripts/gwl.zsh`(문서상 clone 위치)라 `git pull` 갱신이 profile 수정 없이 반영된다. **수동 1회** 실행: `~/.claude` 에서 `./scripts/install-gwl.zsh`. `~/.zshrc` 는 인터랙티브 셸이 source 하므로 Claude Code `!`/Bash 스냅샷에도 흘러가나 **다음 세션/새 터미널부터** 유효.

### settings.json — 살아있는 설정 (untracked)

**git 이 추적하지 않는다** (2026-09-07~, 사유는 문서 맨 위·`.gitignore` 주석). 머신 간에는 파일을 직접 복사해 옮긴다. 아래 키 설명은 그 복사본이 무엇을 담고 있어야 하는지에 대한 참조 문서다 — 이 README 가 실질적인 sync 기준이므로, 키를 바꿨으면 여기도 같이 고친다.

핵심 키:
- `theme`, `preferredNotifChannel` — Claude Code UI 설정
- `permissions.defaultMode` — `auto`(기본 권한 모드). 매 액션 프롬프트 대신 안전 분류기가 판정한다. **user scope 전용** — 프로젝트/로컬 settings 의 `"auto"` 는 repo-controllable 이라 무시되고, 반대로 프로젝트가 *다른* 모드를 지정하면 그쪽이 이긴다(cascade user < project < local). 모델이 auto 미지원이면 CLI 가 안내와 함께 `default` 로 폴백.
- `permissions.deny` — **비어 있음**(비공개 용어 목록의 Read 거부도 여기가 아니라 `~/.claude` 프로젝트 로컬 설정에 둔다 — 위 Install D 절). `git push origin main/master` 직접 푸시 차단이 있었으나 이 repo(`~/.claude`) main push 허용(2026-08-05 사용자 승인)으로 제거 — 사용자 설정의 deny 는 프로젝트 단위로 범위를 정할 수 없고 allow 보다 우선하므로, 전역 deny 를 남기면 이 repo 도 막힌다. 다른 repo 의 main 푸시는 **그 repo 에서 `install-hooks` 를 실행했을 때만** git `pre-push` 훅이 하드 차단한다(설치는 repo 별 opt-in, 전역 `core.hooksPath` 없음 — 2026-09-25 감사에서 `~/Repos` 6개 중 설치 0곳 확인. `pre-commit-check` — repo 루트가 `~/.claude` 일 때만 면제). 즉 훅을 설치한 repo 만 이 레이어가 보호하고(`core.hooksPath` 가 다른 디렉토리를 가리키는 repo 는 install-hooks 가 설치를 거부하므로 보호되지 않는다), 나머지 repo 는 CLAUDE.md §8 규약과 아래 `ask` 에만 의존한다.
- `permissions.ask` — 비가역·외부공개·작업 유실 명령은 분류기 판정에 맡기지 않고 매번 확인을 띄운다(CLAUDE.md §8). 2026-08-06 에 "auto 모드 무마찰"을 이유로 한 번 지웠다가(7c977c8) 되돌렸고, 2026-09-25 에 72건으로 넓혔다. 범위: main/master·force push(`HEAD:main`·`refs/heads/main` 형태 포함), 원격 브랜치 삭제(`git push --delete`·`-d`. `:branch` 형태는 규칙이 아니라 `guard-push-delete.js` hook 이 맡는다 — 아래 `hooks.PreToolUse`), `git branch -D`, 작업트리를 버리는 `git checkout --`·`.`·`-f`, `git reset --hard`, `git clean -f`, `git worktree remove -f`, `git stash drop/clear`, `gh pr merge --delete-branch`, `gh repo delete`, `gh api` DELETE, 토큰을 출력하는 `gh auth token`·`status -t`. **각 규칙을 `rtk ` 접두 형태로도 한 번 더 둔다** — `hooks.PreToolUse` 의 rtk 훅이 git/gh 명령을 `rtk git …`·`rtk gh …` 로 재작성하고, 권한 규칙은 재작성된 명령에 대해 평가되기 때문이다([hooks 문서](https://code.claude.com/docs/en/hooks)). 원래 형태만 있던 2026-09-24 까지는 `git push origin main` 이 ask 를 한 번도 타지 않고 `.claude/settings.local.json` 의 `Bash(rtk git *)` allow 로 바로 통과했다(headless 실측, 상세 wiki `rtk-rewrite-permission-rules`). ask 는 auto 모드에서도 확인 창을 띄운다(권한 모드 문서 *"If an explicit ask rule matches the command, Claude Code asks you even in auto mode"*, 2026-09-25 대화형 확인). **`allow` 로는 못 푼다** — 규칙 평가 순서가 deny → ask → allow 이고 [문서](https://code.claude.com/docs/en/permissions)가 *"The first match in that order determines the outcome, and rule specificity doesn't change the order"* 라고 못박아, `ask` 가 먼저 매칭되면 어느 스코프의 `allow` 도 조회되지 않는다(2026-09-07 정정 — 그전까지 이 문서와 CLAUDE.md §8 이 "repo 별 `settings.local.json` allow 로 푼다"고 잘못 적고 있었다). 정말 풀려면 그 `ask` 규칙 자체를 지워야 하고, 그건 전역이라 모든 repo 에 적용된다. 패턴이 보지 못하는 경로가 남는다(2026-09-27, 규칙 문자열 대조 + `rtk rewrite` 실측 — rtk 0.44.2): (1) `bash <script>` — rtk 가 재작성하지 않고, 규칙은 `bash …` 문자열만 보므로 스크립트 안의 `git push` 는 확인이 안 뜬다. (2) 대상 브랜치 이름이 명령에 없는 push — 인자 없는 `git push` 는 정확 일치 규칙 `Bash(git push)`(와 `rtk ` 형태)로 확인이 뜨지만, main 체크아웃에서 하는 `git push origin`·`git push -u origin HEAD` 는 `* main*`·`*:main*`·`*refs/heads/main*` 어느 것에도 맞지 않는다. (3) `git <전역 옵션> push …`(`-C <dir>`·`-c k=v`·`--git-dir=…`·`--no-pager` 등) — `rtk git <옵션> push …` 로 재작성되는데 push 규칙은 모두 `git push` 로 시작해 맞지 않는다. (콜론 refspec 삭제만은 `guard-push-delete.js` hook 이 이 형태도 잡는다.) (4) `--mirror`·`--all`·`--prune` — 원격 ref 를 덮거나 지울 수 있지만 해당 ask 규칙이 없다. 맞는 ask 가 없으면 auto 분류기가 판정하고, 로컬 settings 에 `Bash(rtk git *)` allow 가 있는 repo(이 repo 포함)에서는 재작성된 형태가 분류기 없이 통과한다. 이 경로들의 백스톱은 명령 모양이 아니라 push 대상 ref 를 보는 pre-push 가드(위 D 절 — 대상이 `refs/heads/main|master` 면 차단)인데, `install-hooks` 를 실행한 repo 에만 있고 `~/.claude` main checkout 은 면제이며 `--no-verify` 로 건너뛸 수 있다. GitHub `main-guard`(아래)는 관리자 bypass 라 소유자 본인의 main push 는 통과한다(위반 표시만 남는다).
- `claudeMdExcludes` — `["/Users/jongyoonlee/.claude/AGENTS.md", "**/.claude/.claude/worktrees/*/CLAUDE.md", "**/.claude/.claude/worktrees/*/AGENTS.md"]`. **첫 번째 패턴**: Claude Code v2.1.277+ 는 작업 디렉토리나 그 위에 `CLAUDE.md` 가 없으면 `AGENTS.md` 를 프로젝트 지침으로 읽는데, `~/.claude/CLAUDE.md` 는 user 지침이라 그 판정에서 세지 않는다([memory 문서](https://code.claude.com/docs/en/memory)). 그래서 main checkout(`~/.claude`) 세션에는 Codex 용 로컬 미러 `AGENTS.md`(gitignored, CLAUDE.md 를 단어 치환한 옛 사본)가 함께 주입돼 서로 다른 규칙이 동시에 들어갔다. 이 경로 하나만 제외한다 — `/config` 의 Project instructions 를 `claude-md` 로 바꾸면 다른 repo 의 AGENTS.md 까지 끊기므로 쓰지 않았다(상세 wiki `claude-code-agents-md-loading`). 미러 자체는 2026-09-25 치웠다(Codex 는 `~/.codex/AGENTS.md` 심링크로 같은 CLAUDE.md 를 읽는다) — 이 줄은 Codex 앱 import 가 미러를 다시 만들 때를 대비해 남긴다. **worktree 패턴 둘**(2026-09-27, plan `claude-md-dedupe`): 이 repo 의 worktree 세션은 `~/.claude/CLAUDE.md` 를 user 지침으로, worktree 의 `CLAUDE.md` 를 프로젝트 지침으로 **둘 다** 실어 컨텍스트가 약 18.5k 토큰 중복됐다(headless haiku 실측 62,827 → 44,300 — 캐시 때문에 과금 차이는 이보다 작다). 전역 사본은 main 세션에서 프로젝트 파일과 같은 경로라 뺄 수 없어 worktree 사본을 뺀다. worktree `CLAUDE.md` 가 빠지면 그 worktree 의 `AGENTS.md` 폴백이 켜지므로(실측) 같은 위치의 `AGENTS.md` 도 뺀다. `.claude` 가 두 번 이어지는 경로만 맞아 다른 repo 의 worktree 는 안 걸린다. 결과: worktree 세션과 그 subagent 는 **main checkout 의 `CLAUDE.md`** 로 돌고, branch 에서 고친 규칙은 main 작업트리에 반영(머지·pull)된 뒤 새 세션부터 적용된다. macOS 에서만 실측했고 Windows 경로 매칭은 미검증이다(안 맞으면 중복이 남을 뿐이다).
- `autoMode.environment` — auto 분류기에 주는 환경 서술. **user scope 전용이라 모든 repo 세션에 똑같이 들어가므로 repo 조건을 문장 안에 둔다**(2026-09-25): 회사 repo(bitbucket, private 가정)·`~/.claude`(github.com/yoon627/claude-config, **PUBLIC** — 사내 자료·내부 호스트·토큰 커밋 금지)·coin-trading-bot(PUBLIC)을 따로 적는다. 전에는 회사 repo 전용 서술("assume private")이 이 공개 repo 세션에도 그대로 들어갔다. 적용 확인은 `claude auto-mode config`.
- (설정 파일 밖, GitHub 쪽) ruleset `main-guard`(2026-09-25) — default 브랜치에 `lint` status check 필수·force push 차단·삭제 차단, **관리자는 bypass**(`bypass_mode: always`). trivial·small 의 로컬 ff-merge 후 main push 가 막히지 않게 관리자 bypass 를 두었으므로 소유자 본인의 push 는 막지 않는다 — push 할 때 `Bypassed rule violations … lint` 가 찍히는 것이 정상. 쓰기 권한만 있는 다른 토큰·협업자의 직접 push·force push·삭제를 막는 것이 실효다. 조회: `gh api repos/yoon627/claude-config/rulesets`.
- `statusLine`, `subagentStatusLine` — statusline 스크립트 등록 (`node ~/.claude/statusline.js`)
- `CLAUDE_CODE_EFFORT_LEVEL` — 전역 settings/bootstrap에서 설정하지 않는다. shell/OS 환경변수가 존재하면 `effortLevel`과 `/effort`보다 우선하므로, 새 셸에서도 이 변수를 해제한 상태를 유지한다. 필요하면 `low|medium|high|xhigh|max|auto`를 한 세션의 `--effort` 또는 `CLAUDE_CODE_EFFORT_LEVEL`로 명시할 수 있다.
- 2026-08-03의 `xhigh` WebSearch/WebFetch 400 관측은 당시 모델·도구 조합에 대한 historical 기록이다. 현재 effort 오류가 나면 오류 원문과 active model을 함께 확인하고, 전역 env 강제로 덮어쓰지 않는다.
- `hooks.SessionStart` — 3개 + orca(아래 별도 항목). (1) `~/.claude` 가 `main` 브랜치이면 **CI 를 통과한 origin/main 커밋까지** 자동 동기화 — `scripts/session-start-pull.sh`(ff-only·실패 무음, async·timeout 15; `~` 확장 위해 sh/Git Bash 필요). `fetch --prune --no-write-fetch-head origin +refs/heads/main:refs/remotes/origin/main +refs/heads/ci/*:refs/remotes/origin/ci/*` 한 번(같은 ref 광고 스냅샷)으로 main 과 CI 검증 기록을 받고, 기록(`origin/ci/verified` 의 `main-sha`)이 HEAD 와 같은 길이의 16진수이며 origin/main 의 조상일 때만 그 커밋으로 `merge --ff-only` 한다 — CI 를 거치지 않은 훅 코드가 다음 세션에 바로 실행되지 않게. 기록이 없거나 형식이 아니거나 main 밖이면 ff 하지 않고, 이유는 세션 브리프(2)의 N 이 말한다. `ci/*` 의 `+` 는 기록이 삭제 뒤 새 root 로 다시 생겨도 받기 위해, `--prune` 은 원격이 지운 기록의 옛 값으로 ff 하지 않기 위해(명령줄 refspec 범위만 지운다) 있다. Git Bash 의 MSYS 경로 변환은 끄지 않는다 — `MSYS_NO_PATHCONV`·`MSYS2_ARG_CONV_EXCL='*'` 는 인자 전부에 걸려 `-C /c/Users/...` 까지 native git 에 그대로 넘겨 fetch 가 매번 실패한다(refspec 은 `/` 로 시작하지 않아 변환 대상이 아니다. 테스트가 이 변수의 재도입을 막는다). `CLAUDE_AUTOPULL_VERIFY=0`(정확히 `0`)이면 검증 없이 **예전 명령(`fetch origin main`)** 으로 origin/main 까지 ff 한다 — fork·Actions 가 없는 clone 은 기록이 영영 없으므로 이 값이 필요하고, 새 fetch 가 어떤 머신에서 깨졌을 때의 머신 단위 탈출구이기도 하다. **게이트는 이 SessionStart 경로에만** 있다: `post-checkout`(main 체크아웃 때)과 `/e` 8단계(자기 머지 직후 — 늘 기록 전이다)의 pull 은 검증 없이 origin/main 을 따른다. 한계: CI 는 ubuntu lint 뿐이라 Windows 에서만 드러나는 파손도 "검증됨" 으로 기록되고, 이 변경을 받기 전의 스크립트를 가진 머신은 첫 세션에 한 번 검증 없이 pull 한다(그 세션의 브리프는 기록 추적 ref 가 아직 없어 "기록 없음" 을 말할 수 있다). **`pull` 이 아니라 `fetch` + 추적 ref 로의 `merge --ff-only` 로 쪼개져 있다** — 워치독의 kill 이 항상 네트워크 단계에만 떨어지게 하기 위해서다(merge 도중 kill 되면 `index.lock` 잔존 + 부분 체크아웃이 남고, 그 lock 이 이후 모든 pull 을 무음 실패시킨다). fetch 가 kill·실패하면 이전 fetch 의 추적 ref 로 머지하지 않고 끝낸다. fetch 직전(마지막 성공 뒤 첫 시도일 때만)과 fetch 성공 직후에 git dir 의 `claude-autopull-attempt`·`claude-autopull-ok` mtime 을 남긴다 — fetch 가 계속 실패하면 추적 ref 가 멈춰 뒤처짐이 안 보이므로, (2) 의 N 이 이 둘로 "fetch 가 N일째 성공 못 함"을 알린다(아래 `session-brief` N 절). **hang 방지**(`session-fetch.js` 와 같은 처방): `GIT_TERMINAL_PROMPT=0` + `-c credential.helper=` + `-c core.askpass=` + `GIT_SSH_COMMAND="<사용자 값 보존> -o BatchMode=yes -o ConnectTimeout=10"` + HTTP low-speed + **wall-clock 워치독**(기본 8s, `CLAUDE_AUTOPULL_TIMEOUT` 로 조정). 워치독은 `set -m` + 프로세스 그룹 kill 이라 git 이 띄운 ssh·git-remote-https **손자까지** 거둔다(직접 자식만 죽이면 손자가 살아남는다 — 실측). 그룹을 가르는 수단은 플랫폼마다 다르다 — **Linux 는 `setsid`**, **Git Bash 는 `set -m`**(setsid 부재). 둘을 겹쳐 쓰지 않는다: `set -m` 하에선 배경 job 이 이미 그룹 리더라 `setsid` 가 fork 해버려 `$!` 가 래퍼를 가리키고 `wait` 가 조기 반환한다. dash 는 tty 없이 job control 을 켜지 않아 `set -m` 만으로는 그룹이 안 갈리고 **손자가 살아남는다**(CI 에서 실측 — 그래서 setsid 를 쓴다). TERM 을 안 듣는 자식은 짧은 유예 후 KILL 로 승격한다. 상한을 iteration 수가 아니라 wall-clock 으로 잡는 이유: Git Bash 의 `sleep 0.2` 는 실제 ~235ms 라 카운트로 재면 Windows 에서 상한이 20% 넘게 초과된다(실측). pull 로 HEAD 가 바뀌면 한 줄 알림(`~/.claude updated …`) 출력. **dirty 여도 시도한다** — `git pull --ff-only` 는 로컬 변경을 덮어쓸 때만 거부하고(무관 파일이면 ff 성공·변경 보존), 게이트로 미리 막으면 origin 이 그 파일을 안 건드린 경우까지 skip 되어 레포가 조용히 밀린다. **skip 조건**: 브랜치가 `main` 이 아님(**`master` 도 skip** — 스크립트가 브랜치를 `main` 과 정확히 일치할 때만 돌려서 `post-checkout` 의 `main|master` 와 정책이 다르다)·rebase/merge/bisect 중·`CLAUDE_AUTOPULL_OFF=1`·**`~/.claude/.autopull-off` 파일 존재**(둘 다 아래 `session-brief` 의 밀림 신호가 사유로 구분해 알린다). pull 이 거부되거나 실패해 뒤처진 상태가 남으면 **다음 세션 시작에 `session-brief` 의 자동 pull 신호가 그 이유를 알린다**(async 라 이 훅 자신의 출력은 첫 턴 뒤에 도달). 훅 스크립트는 매 이벤트마다 파일에서 읽히므로 pull 내용 중 **hook/스크립트는 같은 세션 안에서도 바뀔 수 있다**(CLAUDE.md·skill 문서 등 컨텍스트 주입분은 다음 세션부터). **이건 async 라서가 아니라 동기로 바꿔도 마찬가지다** — CLAUDE.md 로드는 SessionStart 훅과 **병렬로 경합**하고 경합 창이 수십 ms 라, 즉시 끝나는 훅만 우연히 이기고 네트워크 pull(~0.6s)은 구조적으로 진다(2026-09-04 실측: 동기 훅에 `sleep 2` 만 넣어도 세션은 옛 내용을 읽는다. 실제 훅 설정 + 실제 pull 로도 동일). 그래서 동기 전환은 채택하지 않았다 — 세션 시작만 붙잡고 이득이 없다. **이 pull 훅은 세션 시작 시점만 커버 — 체크아웃 시점은 install-hooks 의 `post-checkout` git hook, 세션 중 main 복귀 시점은 `/e` 8단계가 각각 보완(main-autopull).** (2) `session-brief.js`(동기·timeout10) — 세션 시작 브리프 1~5줄: **머지 대기**(origin/main 대비 ahead 인 미머지 로컬 브랜치, oldest 순 cap5) + **`/improve` 권장**(마커 이후 failure 신호 임계 세션 이상) + **닫히지 않은 plan**(`in_progress` 인데 매칭 브랜치가 없거나 이미 머지된 plan 이 `updated` 기준 임계일 이상 방치 — §10 `status: done` 누락 감지) + **자동 pull 밀림**(`~/.claude` 가 origin/main 보다 뒤처졌을 때 그 이유 — detached·main 아님·CI 검증 기록 쪽 보류(기록 없음·형식 아님·main 밖·미전진)·로컬 변경 충돌 파일명·pull 대기, 그리고 뒤처짐이 0 으로 보여도 (1) 의 fetch 가 임계일째 성공하지 못했으면 그 사실. 위 (1) 이 async 라 세션 시작에 안 보이는 것을 동기로 보완) + **세션 repo 밀림**(hook stdin 의 `cwd` 가 가리키는 **지금 작업 중인 repo** 가 upstream 보다 뒤처졌거나 미커밋이 임계일 이상 방치됐을 때. `~/.claude` 와 처방이 다르다 — 그 repo 에는 자동 pull 훅이 아예 없으므로 "직접 pull" 이 답이다). 전부 fail-open 무음 + 신호별 예외 격리, `CLAUDE_SESSION_BRIEF_OFF=1`(+ `CLAUDE_BRIEF_MERGE_OFF`·`CLAUDE_BRIEF_IMPROVE_OFF`·`CLAUDE_BRIEF_STALE_OFF`·`CLAUDE_BRIEF_AUTOPULL_OFF`·`CLAUDE_BRIEF_CWD_OFF`)로 해제, 임계는 `CLAUDE_BRIEF_IMPROVE_MIN`(기본5)·`CLAUDE_BRIEF_STALE_DAYS`(기본3)·`CLAUDE_BRIEF_DIRTY_DAYS`(기본3)·`CLAUDE_BRIEF_AUTOPULL_DAYS`(기본3)·`CLAUDE_BRIEF_FETCH_DAYS`(기본3 — 세션 repo 의 마지막 fetch 신선도). (3) `session-fetch.js`(**async**·timeout30) — 세션이 열린 repo 를 `git fetch` 로 갱신(merge 안 함). (2)의 밀림 판정이 캐시된 ref 에 의존하는데 그 ref 를 갱신할 주체가 없던 구멍을 메운다. `~/.claude` 는 (1)이 담당하므로 제외. `CLAUDE_SESSION_FETCH_OFF=1` 로 해제. (과거엔 `install-gwl.ps1` 을 자동 실행하는 command 가 있었으나 무서명 원격 스크립트 자동 실행 위험 때문에 제거 — gwl 등록은 위 `install-gwl.ps1` 수동 1회 실행으로.)
- `hooks.PreToolUse` — `Edit|Write|NotebookEdit` 에 `guard-worktree-edit.js`(worktree 세션의 worktree 밖 main checkout 추적 파일 편집·새 파일 생성 차단 + 비-worktree 세션의 main/master 추적파일 직접 편집 `ask`, `CLAUDE_MAIN_EDIT_GUARD_OFF=1` 로 해제. **`permission_mode`가 `auto` 면 `ask` 를 건너뛴다** — 분류기 판정 위에 확인을 겹치지 않는다. `deny`(worktree 밖 편집)는 데이터 보호라 모드 무관하게 유지), `Bash` 에 `rtk hook claude`(RTK 명령 재작성; rtk 0.44.0+ 의 빌트인 훅 — 구 `hooks/rtk-rewrite.sh` 파일 훅은 `rtk init -g` 가 제거했다. `command -v rtk` 가드로 rtk 없는 환경에선 no-op), `Bash` 에 `guard-push-delete.js`(콜론 refspec 원격 삭제 `ask` — 아래 절)
- `hooks.UserPromptSubmit` — `dlc-task-router.js` (디버깅/render discipline 주입 + evidence 장부 리셋)
- `hooks.PostToolUse` — `Edit|Write|NotebookEdit|Bash` 에 `dlc-evidence-ledger.js` (변경·검증 명령 기록 — 작은 `bash <file>.sh` 래퍼는 본문까지, Bash 로 고친 plan·README·index 반영, `run_in_background` Bash 의 id 기록)
- `hooks.Stop` — `dlc-early-stop.js`(검증 누락 + 문서 drift + plan drift + 결론 블록 capped 경고, subagent·workflow·이번 턴 shell 을 기다리는 턴은 미룸) + `notify-hook.js Stop`(알림) 2개
- `hooks.Notification` — 입력 대기 시 `notify-hook.js Notification` (cross-platform 알림)
- **orca agent-hooks** — 외부 도구 Orca 가 `~/.orca/agent-hooks/` 에 깔고 settings 에 주입하는 관측 훅. 11개 이벤트(`PreToolUse`·`PostToolUse`·`PostToolUseFailure`·`UserPromptSubmit`·`SessionStart`·`Stop`·`StopFailure`·`SubagentStart`·`SubagentStop`·`TeammateIdle`·`PermissionRequest`)에 동일 명령이 붙는다. **경로는 머신 무관** — `~/.orca/agent-hooks/claude-hook.cmd`(Windows) 를 먼저 보고 없으면 `.sh`(macOS) 를 `/bin/sh` 로, 둘 다 없으면 stdin 을 삼키고 조용히 통과한다. 예전엔 주입된 머신의 절대경로(`/Users/…` 또는 `C:/Users/…`)가 그대로 커밋돼 Mac↔Windows 가 서로를 덮어썼고, 그 충돌로 로컬 변경이 staged 에 묶여 위 자동 pull 까지 멈췄다(2026-08-12 해소). 같은 실패가 gitkraken marketplace(2026-09-04)·`autoMode`(2026-09-07)로 두 번 더 재발했고, 그래서 `settings.json` 자체를 추적 대상에서 뺐다 — 이제 Orca 가 절대경로로 재주입해도 커밋될 것이 없다. 다만 **다른 머신으로 복사할 때는 여전히 절대경로가 섞이지 않았는지 눈으로 확인**할 것.
- `enabledPlugins`, `extraKnownMarketplaces` — Pyright LSP plugin(**`true`** — 2026-07-26 `/doctor` 점검에서 lifetime 사용 0 으로 `false` 했다가 `80dbb3c`(2026-09-03)이 Windows 로컬 토글을 반영해 되돌렸다) + `claude-md-management`(**`true` — 2026-08-05 도입**. `claude-md-improver` 스킬로 CLAUDE.md↔코드베이스 정합성을 주기 점검. 동봉된 `/revise-claude-md` 는 §12 feedback memory·§13 lesson wiki·`/e` 와 역할이 겹쳐 쓰지 않는다) + OpenAI Codex marketplace. **`gitkraken` marketplace 는 여기 두지 않는다** — `source: directory` 라 값이 머신별 절대경로가 되고, 2026-09-04 실제로 Windows 경로가 커밋돼 Mac 에서 로컬 변경을 만들어 자동 pull 을 막았다(위 orca 훅과 같은 실패 — `lesson-tracked-config-machine-paths`). **애초에 필요 없는 항목이다** — `enabledPlugins` 의 `gitkraken-hooks@gitkraken`(이름 기반이라 머신 무관) 만으로 플러그인이 로드된다(`80dbb3c` 가 같은 이유로 제외했고 `0ec47a1` 이 실측 재확인: 항목을 뺀 뒤에도 `claude plugin list` 에서 enabled). 머신별로 굳이 marketplace 를 등록해야 하면 gitignored `settings.local.json` 에 넣는다(`extraKnownMarketplaces` 는 "any file" 스코프)
- `theme`, `skipDangerousModePermissionPrompt`, `skipWorkflowUsageWarning`, `preferredNotifChannel` — Claude Code UI / 세션 기본값
- `model` — **키 없음(핀 해제, 2026-09-04 `3a11a92`)**. 2.1.260 자동 업데이트가 `claude-fable-5-1[1m]` 핀을 지운 것을 되돌리지 않고 수용했다 — 핀이 없으면 그 키가 아예 생기지 않아 머신 간 델타 원천 하나가 사라진다. 세션 모델은 `/model` 로 그때그때 고른다. 머신별로 기본값을 고정하고 싶으면 gitignored `settings.local.json` 에 넣어 tracked 파일을 건드리지 않는다. (`[1m]` 접미사는 1M 컨텍스트 변형, 무버전 별칭은 `opus[1m]`.)

Path 표기 (cross-platform):
- 모든 command 가 `node ~/.claude/...` 형태. `~` 는 Claude Code 가 command 를 실행하는 셸(macOS·Linux = `sh -c`, Windows = Git Bash)에서 홈으로 확장된다. `$HOME` 은 Windows PowerShell fallback 에서 깨질 수 있어 쓰지 않음 → **Windows 는 Git Bash 필수**.
- OS 분기는 settings 가 아니라 호출되는 스크립트 내부에서 처리 (`notify-hook.js` 의 `process.platform`). Claude Code 는 settings 레벨 OS 조건부를 지원하지 않는다. **예외는 orca 훅 하나** — 스크립트가 외부 도구 소유라 우리 쪽에 분기를 넣을 자리가 없어, 명령 안에서 `~/.orca/…claude-hook.cmd` → `.sh` 순으로 **파일 존재만 보고** 고른다(OS 를 판별하지 않는다). 셸 변수는 `~` 로만 쓴다 — `c=~/.orca/…` 처럼 따옴표 없는 대입에서만 확장되고, `c="~/…"` 는 리터럴이 되어 조용히 fallback 으로 샌다.
- `node` + 스크립트 경로 패턴은 모든 OS 에서 동작 (node 가 PATH 에 있어야).

**Claude Code 가 자동 수정하는 키 (push 전 `git diff` 검토 권장)**:
- `/config` (theme, verbose 등) → user-level settings.json (v2.1.119+)
- `/statusline` → settings.json
- `/effort` → settings.json 의 `modelSettings` 에 모델별로 저장(슬라이더·picker 의 `Enter`. `s` 는 이번 세션에만 적용하고 저장하지 않는다). user settings 의 최상위 `effortLevel` 은 옛 저장 형식이다(적용 모델과, 모든 모델에 적용되는 project·local·managed settings 쪽 동작은 `wiki/pages/entity/anthropic-claude-models.md`). `CLAUDE_CODE_EFFORT_LEVEL`이 shell/OS 또는 settings `env`에 남아 있으면 "Not applied"가 표시될 수 있으므로 두 경로를 먼저 확인한다.
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
| `private-terms.txt` | 비공개 용어 목록(회사·비공개 repo 이름·티켓 키) — 공개 repo 에 올리면 그 자체가 누출이다. `pre-commit-check` 가 읽는다(위 Install D 절). 머신마다 직접 복사. |
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
설치 안 해도 된다 — reviewer subagent 가 Codex 병행 검토(CLAUDE.md §9)를 건너뛰고 Claude subagent 검토만 한다. 설치하려면 `npm install -g @openai/codex` 후 `codex login`.

### PowerShell ExecutionPolicy 가 `Restricted` 인 머신
후크의 `.ps1` 스크립트 실행 불가. 일회성 처리:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Notify 알림 끄기
`settings.json` 의 `hooks.Stop` / `hooks.Notification` 블록을 직접 제거 (untracked 라 커밋 대상 아님 — 머신마다 각자 적용). (hooks 는 스코프 간 **누적 실행** 이라 `settings.local.json` 으론 끄지 못하고 추가만 됨 — override 불가.) `preferredNotifChannel` 도 `"notifications_disabled"` 로 변경 가능.

### 자동 동기화(auto-pull) 끄기
**머신별(권장)**: `export CLAUDE_AUTOPULL_OFF=1` — 파일 수정 없이 그 머신의 SessionStart pull 과 `post-checkout` main-autopull 을 함께 끈다(둘이 같은 스위치를 공유).

**머신별(셸 env 를 못 거는 환경)**: `touch ~/.claude/.autopull-off` — SessionStart pull 만 끈다. GUI 로 실행해 셸 env 가 안 잡히는 경우의 즉시 레버다. 이 훅은 **자기 자신의 배포 채널**이라 코드 revert 는 "고장난 그 pull 이 돌아야" 도착한다 — 즉시 레버가 파일/env 두 개인 이유다.

**전 머신**: `settings.json` 의 `hooks.SessionStart` pull 블록을 제거 (untracked 라 머신마다 각자 적용). hooks 는 스코프 간 누적 실행이라 `settings.local.json` 으로 특정 머신만 끄지는 못한다(그래서 위 env 스위치를 쓴다). `disableAllHooks` 는 notify·statusline 까지 같이 꺼지므로 최후 수단.

**CI 검증 게이트만 끄기**(검증 없이 pull): `CLAUDE_AUTOPULL_VERIFY=0` — 셸 env 또는 settings `env`. 영구 해제라 CI 가 잠깐 늦는 정도에는 쓰지 말고 1회 `git -C ~/.claude pull --ff-only` 로 당긴다. **전 머신 일시 보류**: 원격 `ci/verified` 브랜치 삭제 — 머신들은 다음 fetch 에서 기록을 잃고(`--prune`) 보류한다. 다음 green main push 가 새 root 로 다시 기록하므로 영구 정지가 아니다 — 그 사이 고침을 push 하면 고친 커밋까지 한 번에 따라간다. **새 fetch 자체가 어떤 머신에서 깨졌을 때**(fetch 가 실패하면 캐시가 전진하지 않아 뒤처짐은 안 보이지만, 브리프 N 이 `CLAUDE_BRIEF_AUTOPULL_DAYS`(기본 3)일 뒤 "fetch 가 N일째 성공하지 못했다"로 알린다 — 이 기능을 받기 전의 스크립트를 가진 머신은 무음이고, 자동 pull 이 이미 깨진 머신은 이 기능 자체를 수동 pull 로 받아야 한다)는 그 머신에 `CLAUDE_AUTOPULL_VERIFY=0` 을 주면 예전 fetch 로 돌아가 고침을 받을 수 있고, 즉시 확인하려면 `git -C ~/.claude pull --ff-only` 로 직접 당긴다. fetch 가 도는지는 `git -C ~/.claude ls-remote origin main` 과 `git -C ~/.claude rev-parse origin/main` 을 비교해 본다. 기능 전체 제거는 client 쪽 revert 를 먼저 머지하고 기록이 그 커밋까지 전진한 것을 본 뒤 `record-verified` job 을 지운다(한 push 에 담으면 그 커밋의 workflow 에는 기록 job 이 없어 revert 가 자동 pull 로 전달되지 않는다).

**이미 pull 된 내용 되돌리기**: 알림에 찍힌 `before` SHA 또는 `git reflog` 로 복원한다. `git reset --hard` 는 미커밋 변경을 날리므로 rollback 절차로 쓰지 않는다.

### Permission prompt 자주 뜨는 경우
Claude Code 내장 skill `/fewer-permission-prompts` 호출 시 최근 transcript 의 read-only Bash·MCP 호출을 분석해 `permissions.allow` 에 자동 추가. 머신별 차이는 `settings.local.json` 에 두는 게 안전.

### Commit 전 식별자 leak 점검
pre-commit guard 가 staged `plans/*.md` 의 토큰 패턴과 `~/.claude/private-terms.txt` 에 적은 이름(Install D 절)은 잡지만, 목록에 없는 머신 식별자 (username·내부 repo 이름·사내 IP/도메인·이메일 등) 는 본인이 확인. CI 가 자동 처리하지 않는 이유는 패턴 자체가 leak 표면이 될 수 있어서. **이 레포는 public** 이므로 사내 식별자가 섞이지 않았는지 특히 볼 것 — `settings.json` 을 추적에서 뺀 것도 그 값들이 자동으로 밀려 들어왔기 때문이다.
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
가벼운 변경 — `git revert <commit>`. 다른 머신은 다음 pull 시 반영. `settings.json` 은 untracked 라 revert 대상에 들어가지 않는다 — 그 파일의 되돌림은 머신마다 직접 편집한다(예전엔 Claude Code 가 박는 자동 수정이 머지 충돌을 일으켰는데, 추적을 끊어 그 경로 자체가 없어졌다).

### Secret 실수로 commit/push 한 경우

**즉시 수행 (시간 순)**:
1. **token 회수** — 노출된 키/토큰 즉시 revoke + rotate (Anthropic console, GitHub settings, AWS IAM 등). 이게 가장 시급.
2. **GitHub secret scanning alert 확인** — repo Settings > Security > Secret scanning. 자동 detect 됐을 가능성.
3. **history rewrite** — GitHub 공식 절차([Removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)). filter-repo 는 **fresh clone 에서만** 돈다 — 작업 중인 checkout(worktree·reflog·설치된 훅이 있는 `~/.claude`)에서는 `Please operate on a fresh clone instead` 로 거부하고, `--force` 로 밀면 그 checkout 의 worktree·reflog 에 옛 이력이 남는다. **시작 전에 다른 머신·세션의 push 를 멈춘다**(`/e merge` 포함) — `--mirror` 는 원격을 이 clone 의 상태로 덮어, 그 사이 push 된 브랜치·커밋을 지운다.
   ```bash
   git clone https://github.com/<owner>/<repo>.git /tmp/scrub && cd /tmp/scrub   # fresh clone
   # replace.txt: 한 줄에 하나 `<literal>==><replacement>` (==> 를 빼면 ***REMOVED*** 로 바뀐다)
   printf '%s\n' 'leaked-secret-string==>***REMOVED***' > ../replace.txt
   uvx --from git-filter-repo git-filter-repo --sensitive-data-removal --replace-text ../replace.txt   # 또는 brew install git-filter-repo
   git log -p --all -S'leaked-secret-string' | head   # 비어 있어야 한다 — 다음 push 부터는 되돌릴 수 없다
   grep -c '^refs/pull/.*/head$' .git/filter-repo/changed-refs   # 영향받은 PR 수(filter-repo 출력의 First Changed Commit(s) 와 함께 Support 요청에 쓴다)
   git push --force --mirror origin   # 모든 브랜치·태그를 재작성본으로. refs/pull/* 는 GitHub 가 읽기 전용이라 실패한다(정상)
   # Support 요청을 보낸 뒤(.git/filter-repo/first-changed-commits·changed-refs 가 필요하다) 정리한다
   cd / && rm -rf /tmp/scrub /tmp/replace.txt   # 유출 문자열이 든 파일(셸 history 에도 남는다)
   ```
   - `--sensitive-data-removal` 은 `origin` 을 남기고(일반 모드는 지운다) 모든 브랜치·태그를 재작성한다 — `main` 만 push 하면 다른 브랜치·태그에 비밀이 남는다. 2026-09-26 bare remote 로 실측(브랜치 2·태그 1, push 뒤 모든 ref 에서 0건).
   - GitHub ruleset `main-guard` 가 main force push 를 막는다 — 저장소 관리자(bypass `always`)로 push 해야 통과한다.
   - fresh clone 에는 로컬 훅이 없어 push 전 가드 스캔이 없다 — 위의 `git log -S` 가 제거를 확인하는 유일한 단계다.
   - PR ref(`refs/pull/*`)와 GitHub 의 캐시된 화면은 사용자가 지울 수 없다 — GitHub Support 포털로 요청한다(공식 절차의 다음 단계).
4. **다른 머신·브랜치 정리** — 옛 이력에서 딴 브랜치는 **merge 하지 말고 rebase** 한다(GitHub 공식 권고 — merge 커밋 하나가 옛 이력을 통째로 되살린다). 로컬 작업이 없는 머신은 `git fetch && git reset --hard origin/main`. SessionStart 자동 pull 은 갈라진 main 을 ff 하지 못하고 세션 브리프가 "갈라져 ff 불가(rebase 나 push 필요)" 로 알린다 — 여기서 옛 main 을 push 하면 비밀이 되돌아간다. 가드를 설치한 머신이면 pre-push 가드가 이 push 를 막는다(원격이 알려 준 현재 값만 이미 공개된 것으로 보므로, fetch 전의 오래된 추적 ref 가 옛 커밋을 가리켜도 다시 스캔한다) — 단 비밀이 가드가 보는 `plans/*.md`·`settings.json` 에 있었고 패턴에 걸릴 때만이다. 재작성 전에 열려 있던 PR 은 새 main 위에서 다시 만든다. 노출된 secret 이 다른 머신 local 에도 있을 수 있음 — `git log` / `git stash list` / `git reflog` 도 점검.
5. **remote cache 점검** — PR diff, GitHub Actions log, CI artifact, 검색엔진 cache 도 표면. PR 은 사용자가 지울 수 없다 — 3단계의 GitHub Support 요청에 함께 적는다.

참고: Claude Code 의 `permissions.ask` 는 assistant 가 force push 를 실행할 때 확인을 띄울 뿐, 사용자가 터미널에서 직접 실행하는 명령에는 영향이 없다 — incident response 는 본인이 직접 터미널에서 진행.

---

## Roadmap

### OS 지원 현황 (Windows / macOS / Linux)
`settings.json` 은 단일 cross-platform — 모든 command 가 `node ~/.claude/...` 이고 OS 분기는 `notify-hook.js` 의 `process.platform` 에서. 컴포넌트별:
- `statusline.js`, `subagent-statusline.js`, `notify-hook.js`, `guard-worktree-edit.js`, `guard-push-delete.js`, `dlc-*.js` — node 기반(`os.homedir()` / `process.platform` / `os.tmpdir()`), **cross-platform**.
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
├── settings.json                   # 살아있는 설정 (untracked — 아래 참조)
├── settings.local.json             # 머신별 / 민감 정보 (gitignored)
├── statusline.js                   # 메인 statusline
├── subagent-statusline.js          # subagent statusline
├── agents/
│   ├── architecture-reviewer.md
│   ├── code-reviewer.md
│   ├── plan-reviewer.md
│   └── researcher.md
├── docs/
│   ├── codex-review.md             # codex 병행 검토 공유 규약
│   ├── dlc-details.md              # /dlc 절차 상세·엣지 참조(자동 로드 안 됨)
│   ├── headroom-proxy-session-lifecycle.md  # retired headroom proxy의 historical 운영 메모
│   └── worktree-lifecycle.md       # /e 상태수집·worktree 정리 메커닉 참조(자동 로드 안 됨)
├── skills/
│   ├── dlc/
│   │   └── SKILL.md                # /dlc — 자동 개발 사이클
│   ├── c/
│   │   └── SKILL.md                # /c — plan 이어가기
│   ├── e/
│   │   ├── SKILL.md                # /e — plan 마무리 (임시 커밋 + 동기화)
│   │   └── collect-state.sh        # 마무리 읽기전용 git 신호 1회 수집(read-only)
│   ├── wt/
│   │   ├── SKILL.md                # /wt — git worktree 관리
│   │   └── references/             # 생성 시퀀스·.env 복사·rm 복구 메커닉 (자동 로드 안 됨)
│   ├── wiki/
│   │   ├── SKILL.md                # /wiki — LLM Wiki 운영 (ingest/query/lint)
│   │   ├── check_links.py          # dead link·orphan·outbound·index 동기화·frontmatter 필수 키(호환용) 점검 (stdlib)
│   │   ├── test_check_links.py     # check_links 테스트 (CI)
│   │   ├── wiki_check.py           # wiki 정합성 검사 — schema(frontmatter 형식)·stale(covers 신선도)·smoke(대표 질문) (stdlib 단일 파일)
│   │   ├── test_wiki_check.py      # wiki_check 테스트 (CI)
│   │   ├── wiki_search.py          # 공용·repo wiki 검색 — 공용은 cwd 무관, 한글 2-gram·필드 가중 점수, 결과마다 절대경로·맞은 줄(섹션)·관련 페이지, 구조 질의 --links-to·--open (stdlib, wiki_check import)
│   │   ├── test_wiki_search.py     # wiki_search 테스트 (CI)
│   │   └── templates/
│   │       └── wiki-check.toml     # wiki_check config 템플릿 (값 = 코드 기본값)
│   ├── improve/
│   │   ├── SKILL.md                # /improve — 자기개선 loop 분석 축 (구 /audit 흡수; 자산 read-only·랭킹·제안, 끝에 last-improve 마커만 갱신)
│   │   └── improve.sh              # 자산 간 참조 정합 기계 점검 + dlc 신호 집계 + 네이티브 중복 대장 신선도 (read-only)
│   ├── jira-worklog/
│       ├── SKILL.md                # worktree AI 작업시간 → Jira worklog (dry-run 기본)
│       ├── run_worklog.sh/.ps1     # uv 우선·Python fallback 공통 launcher
│       ├── jira_worklog.py         # CLI 진입점 (stdlib only)
│       ├── jira_kit/               # 세션시간 추정·마커·Jira REST·설정 모듈
│       ├── test_worklog_scope.py   # worktree 단위 upsert 격리 테스트 (CI)
│       ├── test_session_time.py    # cwd → bucket 귀속·구간 발행 테스트 (CI)
│       ├── test_register_gate.py   # 등록 diff·게이트 판정 테스트 (CI)
│       ├── test_exit_contract.py   # /e 정리 게이트가 기대는 CLI 종료코드 계약 테스트 (CI)
│       ├── test_ticket_pattern.py  # 범용 기본 티켓 패턴·머신별 패턴 설정(toml) 테스트 (CI)
│       └── test_launcher.sh        # launcher 의 Python fallback·인자 전달·종료코드(127·전달) 테스트 (CI)
│   └── jira-task/
│       ├── SKILL.md                # Claude·Codex 작업내용 → Jira task description (dry-run 기본)
│       ├── jira_task.py            # description preview/post/upsert CLI (stdlib only)
│       └── test_jira_task.py       # Jira description·marker·preview 단위 테스트
├── scripts/
│   ├── notify-hook.js              # notify 진입점 (cross-platform; mac 인라인, win→.ps1 위임)
│   ├── notify.ps1                  # (Windows) Toast + 사운드 + flash
│   ├── notify-hook.ps1             # (Windows) notify-hook.js 가 spawn
│   ├── guard-worktree-edit.js      # PreToolUse — worktree 밖 main checkout 추적·새 파일 편집 차단
│   ├── guard-push-delete.js        # PreToolUse — 콜론 refspec 원격 삭제 ask (+ .test.js)
│   ├── dlc-task-router.js          # UserPromptSubmit — dlc discipline 주입 + 장부 리셋
│   ├── dlc-evidence-ledger.js      # PostToolUse — 변경·검증 기록 + 문서 drift dirty flag
│   ├── dlc-early-stop.js           # Stop — 검증 누락 + 문서 drift capped 경고 (+ .test.js)
│   ├── dlc-doc-drift.js            # 문서 drift 판정 순수 모듈 (+ .test.js)
│   ├── dlc-ledger.js               # 위 dlc hook 공유 장부 모듈 (hook 미등록)
│   ├── dlc-signal.js               # 자기개선 loop 신호 수집 모듈 — telemetry append (+ .test.js)
│   ├── session-brief.js            # SessionStart — 머지 대기 + /improve 권장 + 닫히지 않은 plan + 자동 pull 밀림 + 세션 repo 밀림 (+ .test.js)
│   ├── session-fetch.js            # SessionStart(async) — 작업 repo remote-tracking ref 갱신 (+ .test.js)
│   ├── hook-cwd.js                 # hook stdin 의 cwd 읽기 + 테스트 전용 시간 배수 공유 모듈 (hook 미등록) (+ .test.js)
│   ├── session-start-pull.sh       # SessionStart(async) — ~/.claude 를 CI 검증 기록(ci/verified)까지 ff + hang 방어 + 워치독
│   ├── session-start-pull.test.js  # 위 스크립트 + SessionStart command 회귀 테스트(fixture HOME, settings 없으면 CANONICAL)
│   ├── usage-count.js              # improve.sh deep — transcript 사용량 카운트 (+ .test.js)
│   ├── native-overlap-lint.js      # improve.sh ⑨ — 네이티브 중복 대장 신선도·delta 창 (+ .test.js)
│   ├── pre-commit-check.sh / .ps1  # plans·settings.json secret guard (staged + pushed range)
│   ├── ci-secret-scan.sh           # CI 백스톱 — 가드를 PR·push 범위에 실행 (+ .test.sh)
│   ├── record-verified.test.sh     # lint.yml record-verified job 의 run 블록을 가짜 gh 로 검사
│   ├── install-hooks.sh / .ps1     # hooks 디렉토리에 {pre-commit,pre-push,post-checkout} wrapper 생성 (+ install-hooks.test.js)
│   ├── bootstrap/                  # 새 머신 재현 — setup.sh·setup.ps1·install-codex-skill.*·sync_codex_agents.py(+ test_…) (상세 bootstrap/README.md)
│   ├── prompt-gwl.py               # UserPromptSubmit 훅 (프로젝트별 사용, + test_prompt_gwl.py)
│   ├── gwl.ps1 / gwl.zsh           # `gwl` — worktree list + 현재 위치 → (Windows / macOS·zsh)
│   └── install-gwl.ps1 / .zsh      # gwl 을 profile($PROFILE·~/.zshrc)에 등록 (멱등)
├── wiki/                           # 공용 LLM Wiki — 비공개 repo 의 별도 clone (이 repo 는 추적하지 않는다, Install E 절)
│   ├── WIKI.md                     # 운영 규약 (schema)
│   ├── index.md                    # 페이지 카탈로그
│   ├── log.md                      # 연산 로그
│   ├── raw/                        # 원문 (그 repo 에서 gitignored)
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

### Pre-commit guard 가 정상 변경을 차단
`scripts/pre-commit-check.sh`(`.ps1`)의 토큰 패턴이 `plans/*.md`(다시 추적되면 `settings.json`)의 정상 값과 충돌하는 경우. 패턴 수정이 정답이다. 패턴을 고치기 전에 한 번 통과시켜야 한다면, 그것은 **사용자가 차단된 매치를 직접 확인하고 오탐으로 판단한 뒤 터미널에서 실행하는** 복구 절차다 — `git commit --no-verify`(push 단계면 `git push --no-verify`). 매치를 확인하지 않고 통과시키지 말 것. Claude 는 이 우회를 실행하지 않는다 — 차단되면 원인(패턴·내용)을 고치거나 보고 후 멈춘다(CLAUDE.md §8).
