# scripts/bootstrap — Claude Code 환경 부트스트랩

새 머신/환경에서 **한 번 실행**하면 이 `~/.claude` 환경(도구 + 설정 + 선택적 memory)을
재현하는 **idempotent** 스크립트. 재실행해도 안전(이미 된 단계는 `[SKIP]`).

| OS | 스크립트 |
|---|---|
| macOS | `setup.sh` (zsh/launchd, 비-conda) |
| Windows | `setup.ps1` (레지스트리/scheduled task) — ⚠️ 미검증, 아래 한계 참조 |

## 사용법

```sh
# macOS
bash scripts/bootstrap/setup.sh            # 실제 실행
bash scripts/bootstrap/setup.sh --dry-run  # 동작만 출력(변경 없음)
bash scripts/bootstrap/setup.sh --memory-from ~/old-machine/.claude   # memory 도 복원
```

```powershell
# Windows (PowerShell)
pwsh -File scripts\bootstrap\setup.ps1
pwsh -File scripts\bootstrap\setup.ps1 -DryRun
pwsh -File scripts\bootstrap\setup.ps1 -MemoryFrom 'D:\backup\.claude'
# Codex skill junction helper만 검증
pwsh -File scripts\bootstrap\install-codex-skill.test.ps1
```

Codex 가 이 환경의 규칙과 skill 을 그대로 쓰도록 macOS bootstrap(`setup.sh`)은 다음 8개 연결을 만든다:
- `$HOME/.agents/skills/<name>` → `$HOME/.claude/skills/<name>` — `c`·`dlc`·`e`·`improve`·`jira-worklog`·`wiki`·`wt`(목록은 `setup.sh` 의 `CODEX_SKILLS`)
- `${CODEX_HOME:-$HOME/.codex}/AGENTS.md` → `$HOME/.claude/CLAUDE.md` — Codex 는 `CODEX_HOME`(기본 `~/.codex`)의 `AGENTS.md` 를 읽는다. 같은 곳에 비어 있지 않은 `AGENTS.override.md` 가 있으면 Codex 가 그것을 먼저 읽으니 이 연결이 무시된다.

Windows(`setup.ps1`)는 아직 `jira-worklog` 하나만 연결하고 `AGENTS.md` 는 만들지 않는다 — pwsh·Windows 실행 검증이 필요해 따로 다룬다.

설치 후 Codex를 재시작해야 새 skill 목록을 읽는다. 연결만 되돌릴 때는 target이 이 source를 가리키는지
확인한 뒤 junction/symlink 자체만 제거한다. 실제 디렉터리나 다른 target은 삭제하지 않는다.

```powershell
# Windows: target 확인 후 junction 자체만 제거
Get-Item -Force "$HOME\.agents\skills\jira-worklog" | Format-List LinkType,Target,ResolvedTarget
Remove-Item -LiteralPath "$HOME\.agents\skills\jira-worklog"
```

```sh
# macOS/Linux: target 확인 후 symlink 자체만 제거(skill 마다, AGENTS.md 도 같다)
readlink "$HOME/.agents/skills/wiki"
rm "$HOME/.agents/skills/wiki"
readlink "${CODEX_HOME:-$HOME/.codex}/AGENTS.md"
rm "${CODEX_HOME:-$HOME/.codex}/AGENTS.md"
```

### Codex 연결 충돌

연결할 자리에 실제 디렉터리·실제 파일·다른 곳을 가리키는 링크가 있으면 bootstrap 은 그것을 건드리지 않고 실패로 남긴다. macOS(`setup.sh`)는 나머지 연결과 뒤 단계를 계속하고, 마지막에 `Codex 연결 실패: skill:<name> AGENTS.md` 처럼 요약한 뒤 exit 1 로 끝난다. Windows(`setup.ps1`)는 첫 실패에서 멈춘다. 흔한 원인은 Codex 앱의 Claude 설정 import 가 링크를 단어 치환한 실파일 사본으로 바꿔 놓은 경우다(루트 README "Codex 쪽 연결"). 정리 순서:

1. 원인을 본다 — 각 `[WARN] … 연결 실패` 줄 바로 위에 installer 메시지가 있다. `ls -la "$HOME/.agents/skills/<name>"`, `readlink` 또는 `head` 로 자리에 무엇이 있는지 확인.
2. 필요하면 백업한다 — **`~/.agents/skills` 밖으로** 옮긴다. 예: `mkdir -p "$HOME/.agents/skills-backup" && mv "$HOME/.agents/skills/dlc" "$HOME/.agents/skills-backup/"`, `mv "$HOME/.codex/AGENTS.md" "$HOME/.codex/AGENTS.md.bak"`. skills 폴더 안에 `dlc.bak` 처럼 남기면 Codex 가 그 사본도 skill 로 읽을 수 있다.
3. bootstrap 을 다시 실행한다 — 빈 자리에 링크를 만든다.

installer 메시지가 `source missing` 이면 충돌이 아니라 `~/.claude` 에 그 skill(또는 `CLAUDE.md`)이 없다는 뜻이다 — `~/.claude` 를 최신으로 받은 뒤 다시 실행한다.

## 전제 (스크립트가 설치하지 않음)

이 repo 를 clone·실행하는 시점에 이미 있어야 한다:
- **claude** (공식 설치) — 없으면 안내만 하고 중단. 이 스크립트는 claude 를 설치하지 않는다(이미 쓰던 환경을 새 머신에 재현하는 용도).
- **Homebrew**(mac) 또는 **winget/choco**(win) — 도구 설치에 필요.
- **git**.

## 재현 대상

| 항목 | 방법 |
|---|---|
| node | `brew install node` / `winget install OpenJS.NodeJS` |
| jq | `brew install jq` / `winget install jqlang.jq` — rtk hook이 stdin JSON 파싱에 의존 |
| uv | astral 설치 스크립트 (비-conda) |
| **rtk** | 이미 설치된 standalone `rtk`가 있을 때만 `rtk verify`/`rtk init -g --hook-only --no-patch` 실행. 없으면 건너뜀. **hook 파일 직접편집 금지**(sha256 무결성). |
| Codex skill·AGENTS.md | macOS: skill 7종을 `$HOME/.agents/skills/` 에, `${CODEX_HOME:-$HOME/.codex}/AGENTS.md` 를 `$HOME/.claude/CLAUDE.md` 에 symlink. Windows: `jira-worklog` 하나만 junction |
| 셸 env | marker 블록(mac `~/.zshrc`) / User 레지스트리(win): `ANTHROPIC_MODEL`, PATH. `CLAUDE_CODE_EFFORT_LEVEL`은 제거/해제해 `/effort`가 동작하게 함. |
| settings.json | **재현 안 함** — untracked(2026-09-07~)라 `git clone` 으로 오지 않는다. 기존 머신에서 직접 복사한다(루트 README Install A 의 settings.json 배치 단계 — Windows 5번, macOS 2번). 부트스트랩은 rtk hook 등록만. |
| memory | `--memory-from`/`-MemoryFrom` 으로 기존 머신 경로 줄 때만 복원(아래 한계). |

## idempotent 동작

각 단계가 "이미 됐는지" 선검사 후 `[SKIP]`. 핵심 guard:
- **절대경로 체크** — `~/.local/bin/<tool>` 직접 확인(새 셸 PATH 미반영 오탐 회피).
- **rtk 선택 처리** — standalone `rtk`가 PATH에 있을 때만 `rtk verify`/hook 초기화를 수행하며, 없으면 실패하지 않고 건너뜀.
- **zshrc marker 블록** — `# >>> claude-bootstrap env >>>` … 사이를 멱등 교체(append 누적 방지).
- **effort env 해제** — marker 블록에 `unset CLAUDE_CODE_EFFORT_LEVEL`을 넣어 부모 셸의 stale 환경변수 상속을 끊음. Windows는 User/Process 환경변수에서 제거.
- **Codex link** — skill 은 source 에 `SKILL.md` 가 있을 때, `AGENTS.md` 는 source(`CLAUDE.md`)가 파일일 때(`install-codex-skill.sh --file`), target 이 비어 있으면 생성. 같은 source 를 가리키는 link 는 "already points to source", 실제 파일·directory·다른 target·dangling/unknown link 는 기존 경로를 보존하고 실패한다(위 "Codex 연결 충돌").
- Unix helper 상태 행렬은 CI에서 `bash scripts/bootstrap/install-codex-skill.test.sh`로 실행하고, Windows junction helper는 Windows에서 `pwsh -File scripts\bootstrap\install-codex-skill.test.ps1`로 실행한다.

## 한계 (반드시 인지)

- **Windows `setup.ps1` 은 실행 검증되지 않았다.** macOS 세션에서 로직·문서 기반으로 작성. 특히 검증 필요:
  - standalone `rtk` 설치 경로·PATH 노출 방식
  - Codex skill junction 단계는 Windows에서 별도 helper 상태 행렬로 검증한다. 전체 bootstrap이 검증됐다는 뜻은 아니다.
  - macOS 와 달리 Codex skill 은 `jira-worklog` 하나만, `AGENTS.md` 는 연결하지 않는다(macOS 는 8개). Windows 실행 검증과 함께 맞출 예정이다.
- **headroom은 더 이상 bootstrap 대상이 아니다.** 기존 설치·proxy·MCP 상태는 자동으로 관리하거나 복구하지 않는다. 과거 운영 기록은 `docs/headroom-proxy-session-lifecycle.md`에 보존한다.
- **memory 는 git 미추적** — `projects/*/memory/` 는 repo 에 안 들어간다(public repo 노출 방지). 따라서 새 머신 단독 실행 시 memory 는 비어있다. 기존 머신의 `~/.claude` 경로를 `--memory-from`/`-MemoryFrom` 으로 줘야 복원된다. 복원은 **overwrite**(소스에 없는 파일은 대상에 보존 — 순수 미러 아님).
- **원격 설치 스크립트 신뢰 전제** — uv 설치에 astral 공식 `curl … | sh`(mac) / `irm … | iex`(win) 를 쓴다. checksum/버전 pinning 없이 원격 스크립트를 실행하므로 astral 도메인을 신뢰하는 전제다.
- **conda 는 재현 안 함** — 의도적으로 비-conda 셋업이다. 기존 머신이 anaconda 기반이었어도 새 머신은 astral uv + 시스템 도구로 깔린다.
- **git config / gh auth** — 대화형이라 자동 설정하지 않고 미설정 시 안내만 한다.
