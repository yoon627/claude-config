---
title: headroom
category: entity
created: 2026-06-21
updated: 2026-08-03
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

## 실사용 감사 (2026-08-03) — 프록시는 값을 하고, MCP 표면은 죽어 있다

| 축 | 측정치 | 판정 |
|---|---|---|
| 프록시 자동 압축 | API 2582건 중 1644건 압축 · 토큰 20.7M 제거 · **$103.87(13.7%) 절감** | 유지 |
| 번들 rtk | 4731 명령 · 2.1M 토큰(64.7%) 절감 | 유지 |
| MCP 도구 | transcript 298개 전수: `headroom_retrieve` 38회, `headroom_compress` **0회** | 사실상 미사용 |

`retrieve` 38회는 이득이 아니라 **압축이 가린 원문을 되찾은 비용**이다. 가치는 전부 자동 프록시에 있고 MCP 표면엔 없다 — 도구 목록에서 빼도 실질 손실은 거의 없다(미조치, 관찰만).

**디스크 위생 결함**: `logs/debug_400/` 이 로테이션 없이 **1.0 GB / 673 파일**까지 자랐다(개당 최대 5.2MB, 이름과 달리 429 도 적재). `proxy.log` 는 10MB×3 로테이션이 있는데 이 디렉토리만 없다. 2026-08-03 에 7일 초과분 662개(1052MB)를 삭제해 1.0MB 로 회수 — **재발한다**(상류 로테이션 없음). `session_stats.jsonl` 은 0바이트 死파일.

번들 rtk 가 6개월 묵어 발생한 반복 실패는 [[lesson-stale-tool-version]] 참고 — 심링크만 0.44.2 로 재지정해 해소했고 headroom 번들 바이너리는 그대로 뒀다.

## 설치
- 설치: `uv tool install headroom-ai` (PyPI 패키지명 `headroom-ai`, 0.25.0 — 명령은 `headroom`).
- 새 머신 재현은 [[codegraph]] 와 함께 `scripts/bootstrap/setup.sh`. rtk hook 의존 `jq` 도 같이 설치.
