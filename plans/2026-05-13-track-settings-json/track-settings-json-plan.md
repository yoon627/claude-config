---
title: track-settings-json — settings.json git tracked 전환 + 민감정보 local 분리
status: done
started: 2026-05-13
updated: 2026-06-03
---

# Goal

`~/.claude/settings.json` 을 git tracked 로 전환. 머신별/민감 정보는 `settings.local.json` 으로 분리. `settings.example.json` 폐기로 sync 부담 제거. portable path (`$env:USERPROFILE` expansion) 로 다른 머신 호환.

# Progress

- 2026-05-13: 옵션 검토 (단순 추적 vs base+local + install merge). 사용자 선택 — 단순 추적 + env 만 (effortLevel 키 제거).
- 2026-05-13: plan-reviewer NO-GO (blocker 다수). researcher 로 핵심 가정 재검증:
  - **mcpServers 자동 commit 우려 → myth**: MCP 는 `~/.claude.json` 별도 저장 (`claude mcp add --scope user` 가 settings.json 안 박음). settings.json tracking 의 secret leak surface 크게 줄어듦.
  - `~/.claude/settings.local.json` user-level 에서 **deep merge + .local 우선** 확인. 단 Issue #19487 (project local 이 user local 전체 overwrite) 미해결.
  - `env.CLAUDE_CODE_EFFORT_LEVEL = "max"` 는 잘못된 값 가능 — docs 명시: `low|medium|high|xhigh`. → `xhigh` 로 정정.
  - `/config`, `/statusline`, `/effort` 가 user-level settings.json 박음 → mutable dirty 부담은 잔존.
- 2026-05-13: 구현 1차 라운드 — .gitignore / settings.json / pre-commit-check.ps1 / install-hooks.ps1 작성, settings.example.json git rm. README 갱신 진행 중.
- 2026-06-03: 완료 확인 — settings.json git tracked + .gitignore 화이트리스트 + pre-commit/pre-push hooks + README install 섹션이 전부 origin/main 에 반영됨(후속 config-audit #16 이 이 설정을 감사·강화). effortLevel 값은 이후 `xhigh`→`max` 로 정정(커밋 a588164). status→done.

# Next

완료. 후속 감사·강화는 config-audit (`project_claude-config-audit` memory) 로 이어짐.

# Decisions

- 구조: 단순 추적. Claude Code 자동 deep merge 가 settings.json + settings.local.json 합쳐 줌 (researcher 확인).
- `effortLevel`: env 만 (`xhigh`). settings 키 제거.
- portable command: `powershell -NoProfile -Command 'node "$env:USERPROFILE\.claude\statusline.js"'`. outer single quote — Git Bash + PowerShell 양쪽 expansion 안전.
- pre-commit guard: regex 기반 (blacklist 키 + 토큰 패턴). pre-push 도 같은 스크립트 재사용. `.git/hooks/` 는 머신별 → `install-hooks.ps1` 가 sh wrapper 생성 (LF-encoded UTF-8 no BOM).
- README rollback: secret 실수 push 시 token revoke + `git filter-repo` + GitHub secret scanning alert 안내.

# Key Files

- `C:\Users\USER\.claude\.gitignore` — whitelist: `!/settings.json` 추가, `!/settings.example.json` 제거. belt-and-suspenders 의 `settings.json` 제거.
- `C:\Users\USER\.claude\settings.json` — portable path + `env.CLAUDE_CODE_EFFORT_LEVEL=xhigh` + `effortLevel` 키 제거.
- `C:\Users\USER\.claude\settings.example.json` — 삭제 (git rm 완료).
- `C:\Users\USER\.claude\scripts\pre-commit-check.ps1` — staged/HEAD settings.json 검사.
- `C:\Users\USER\.claude\scripts\install-hooks.ps1` — `.git/hooks/{pre-commit,pre-push}` sh wrapper 생성.
- `C:\Users\USER\.claude\README.md` — 갱신 중.

# Blockers

- 없음.
