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
```

## 전제 (스크립트가 설치하지 않음)

이 repo 를 clone·실행하는 시점에 이미 있어야 한다:
- **claude** (공식 설치) — 없으면 안내만 하고 중단. 이 스크립트는 claude 를 설치하지 않는다(이미 쓰던 환경을 새 머신에 재현하는 용도).
- **Homebrew**(mac) 또는 **winget/choco**(win) — 도구 설치에 필요.
- **git**.

## 재현 대상

| 항목 | 방법 |
|---|---|
| node | `brew install node` / `winget install OpenJS.NodeJS` |
| jq | `brew install jq` / `winget install jqlang.jq` — rtk hook(`rtk-rewrite.sh`)이 stdin JSON 파싱에 의존 |
| uv | astral 설치 스크립트 (비-conda) |
| headroom | `uv tool install headroom-ai` |
| codegraph | `npm install -g @colbymchenry/codegraph` |
| **rtk** | 별도 설치 아님 — headroom 번들(`~/.headroom/bin/rtk`)을 심링크(mac)/PATH(win) 노출 + `rtk init -g --hook-only --no-patch`(hook 서명). **hook 파일 직접편집 금지**(sha256 무결성). |
| MCP 등록 | `codegraph install -y` + `claude mcp add headroom` (홈 `~/.claude.json`) |
| headroom proxy | `headroom install apply --mode token` (mac=launchd service, win=scheduled task) |
| codegraph 인덱스 | `codegraph init <repo>` |
| 셸 env | marker 블록(mac `~/.zshrc`) / User 레지스트리(win): `ANTHROPIC_MODEL`, `CLAUDE_CODE_EFFORT_LEVEL`, PATH. headroom env 8개는 `headroom install` 이 따로 심음. |
| settings.json | **재현 안 함** — repo 추적 파일이라 `git clone` 으로 따라옴. 부트스트랩은 rtk hook 등록만. |
| memory | `--memory-from`/`-MemoryFrom` 으로 기존 머신 경로 줄 때만 복원(아래 한계). |

## idempotent 동작

각 단계가 "이미 됐는지" 선검사 후 `[SKIP]`. 핵심 guard:
- **절대경로 체크** — `~/.local/bin/<tool>` 직접 확인(새 셸 PATH 미반영 오탐 회피).
- **rtk dangling 심링크** — `[ -L ] && [ -e ]` 둘 다여야 정상, 깨졌으면 재생성 후 `rtk verify`.
- **zshrc marker 블록** — `# >>> claude-bootstrap env >>>` … 사이를 멱등 교체(append 누적 방지).

## 한계 (반드시 인지)

- **Windows `setup.ps1` 은 실행 검증되지 않았다.** macOS 세션에서 로직·문서 기반으로 작성. 특히 검증 필요:
  - headroom 번들 rtk 의 Windows 경로(`~\.headroom\bin\rtk.exe` 가정)·PATH 노출 방식
  - `headroom install --preset persistent-task` 의 Windows 동작
- **Windows token mode timeout** — 과거 Windows 에서 token mode 압축이 30s timeout 으로 `api_error` 를 낸 이력이 있다. 첫 실행 후 관찰하고, 재현되면 `headroom install apply --mode cache` 로 재설치할 것. (macOS 에선 미재현이라 token 유지. 상세: `docs/headroom-proxy-session-lifecycle.md`)
- **memory 는 git 미추적** — `projects/*/memory/` 는 repo 에 안 들어간다(public repo 노출 방지). 따라서 새 머신 단독 실행 시 memory 는 비어있다. 기존 머신의 `~/.claude` 경로를 `--memory-from`/`-MemoryFrom` 으로 줘야 복원된다. 복원은 **overwrite**(소스에 없는 파일은 대상에 보존 — 순수 미러 아님).
- **원격 설치 스크립트 신뢰 전제** — uv 설치에 astral 공식 `curl … | sh`(mac) / `irm … | iex`(win) 를 쓴다. checksum/버전 pinning 없이 원격 스크립트를 실행하므로 astral 도메인을 신뢰하는 전제다.
- **conda 는 재현 안 함** — 의도적으로 비-conda 셋업이다. 기존 머신이 anaconda 기반이었어도 새 머신은 astral uv + 시스템 도구로 깔린다.
- **git config / gh auth** — 대화형이라 자동 설정하지 않고 미설정 시 안내만 한다.
