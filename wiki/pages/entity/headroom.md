---
title: headroom
category: entity
created: 2026-06-21
updated: 2026-06-21
sources:
  - headroom-ai 0.25.0 (headroom --help, 2026-06 확인)
  - docs/headroom-proxy-session-lifecycle.md
  - memory rtk-headroom-path-fix
---

# headroom

LLM 컨텍스트 최적화 레이어. 세 역할: ① HTTP proxy(`ANTHROPIC_BASE_URL` 경유 토큰 압축·캐시) ② MCP 서버(compress/retrieve/stats) ③ rtk 번들. [[codegraph]] 와 함께 이 repo 워크플로우의 핵심 MCP·proxy 도구다.

## proxy (macOS 셋업)
- `headroom install apply --preset persistent-service --mode token` → launchd service `com.headroom.default` 상시 기동 + `~/.zshrc` 에 `ANTHROPIC_BASE_URL`·`HEADROOM_MODE=token` 등 routing env 를 심는다.
- token mode 압축은 이 macOS 머신에서 timeout 없이 동작(상세 `docs/headroom-proxy-session-lifecycle.md`). Windows 는 과거 압축 30s timeout 이력이 있어 cache mode 로 회피했다.
- proxy 라우팅은 OS/셸 env 로 적용된다 → env 우선순위는 [[effort-os-env-single-source]] 와 같은 원칙(OS env 가 단일 소스).

## rtk 번들
rtk(Rust Token Killer)는 별도 설치가 아니라 headroom 이 `~/.headroom/bin/rtk` 에 번들한다. 심링크 `~/.local/bin/rtk` + `rtk init -g --hook-only --no-patch`(hook 서명)으로 PATH·hook 정합을 맞춘다. hook 파일 직접편집은 sha256 무결성 검증에 걸리므로 금지. 상세: memory `rtk-headroom-path-fix`.

## 설치
- 설치: `uv tool install headroom-ai` (PyPI 패키지명 `headroom-ai`, 0.25.0 — 명령은 `headroom`).
- 새 머신 재현은 [[codegraph]] 와 함께 `scripts/bootstrap/setup.sh`. rtk hook 의존 `jq` 도 같이 설치.
