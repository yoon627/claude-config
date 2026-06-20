# 동시 Claude 세션: headroom proxy 프로세스 수명주기 (macOS)

여러 Claude Code 세션을 동시에 띄워 쓸 때, headroom proxy 가 어떻게 기동·유지되고
**어떤 조작이 다른 세션에 영향을 주는가**를 정리한 운영 노트. headroom `0.25.0`,
macOS(Apple Silicon) 기준. proxy 를 launchd service 가 소유하도록 셋업했으므로
**proxy 수명주기가 개별 claude 세션과 독립**이다 — 세션을 닫아도 proxy 는 안 죽는다.

## TL;DR

| 대상 | 구조 | 잘못 끄면 | 다른 세션 |
|---|---|---|---|
| **headroom proxy** (8787) | launchd service `com.headroom.default` 소유, 전역 공유 단일 인스턴스 | 그 service 가 즉시 재기동(KeepAlive) | **영향 없음** |

- proxy 는 어떤 claude 세션의 자식도 아니다. `headroom install apply` 로 만든 launchd service 가 띄우고 살린다.
- claude 는 `ANTHROPIC_BASE_URL` 로 proxy 를 **경유만** 한다 — 띄우지도 죽이지도 않는다. 그래서 세션을 닫아도 proxy 는 그대로다.
- proxy 를 진짜 멈추려면 `headroom install stop`. 수동 `kill` 해도 launchd 가 곧 되살린다.

## 이 머신의 셋업 (실측)

`headroom install apply --preset persistent-service --mode token` 한 번으로 구성됨. 건드린 것은 셸 env 와 launchd plist 둘뿐 — `~/.claude/settings.json`·`~/.claude.json` 운영 자산은 변경하지 않는다.

- **routing** — `~/.zshrc` 의 `# >>> headroom persistent env >>>` 블록:
  ```sh
  export HEADROOM_PORT="8787"
  export HEADROOM_HOST="127.0.0.1"
  export HEADROOM_MODE="token"
  export HEADROOM_BACKEND="anthropic"
  export ANTHROPIC_BASE_URL="http://127.0.0.1:8787"
  ```
  → 새 로그인 셸에서 띄우는 **모든** `claude` 가 이 단일 proxy 를 경유한다. (이미 떠 있는 셸/세션은 프로세스 env 가 런타임에 안 바뀌므로 재시작 후 적용.)
- **상시 기동** — `~/Library/LaunchAgents/com.headroom.default.plist`. 로그인 시 자동 기동 + 죽으면 재기동. `launchctl list | grep headroom` 에 `com.headroom.default` 로 보인다.
- **mode = token** — 압축까지 해 토큰 절감폭이 크다. 이 머신 proxy.log 상 압축이 timeout 없이 정상 동작(`content_router: ... compressed`, `cache_hit_pct=100`). cache mode 는 압축을 안 해 절감폭이 작다.

## 운영 명령

```sh
headroom install status      # running/healthy, mode, port 확인
headroom install start|stop|restart   # service 수명주기 제어 (이걸로 끄고 켠다)
headroom install remove      # service 해제 + zshrc/plist 등 관리 설정 원복
```

`kill <proxy_pid>` 로 직접 죽이지 말 것 — launchd KeepAlive 가 즉시 새 인스턴스를 띄워 PID 만 바뀐다. 멈추려면 `headroom install stop`.

## Windows 의 "세션 동반 사망" 버그는 왜 여기선 안 나나 (참고)

다른(Windows) 머신에서는 `headroom wrap claude` 로 띄운 세션이 proxy 를 **자기 자식으로 spawn** 해 그 세션이 proxy "주인"이 됐다. 주인 세션을 닫으면 cleanup 이 도는데, reference counting 이 wrap marker 만 세어 "그냥 `claude`" 로 붙은 다른 세션을 0 으로 오판 → 공유 proxy 를 `terminate` → 다른 세션 전부 `api_error`. "wrap 1개 + 순수 claude N개" 조합이 이 버그를 때렸다.

**macOS 의 이 셋업은 그 전제 자체가 없다.** proxy 소유권이 wrap 세션이 아니라 launchd service 에 있어, 어떤 claude 를 닫아도 proxy cleanup 이 돌지 않는다. wrap 을 쓸 일도 없다(전역 `ANTHROPIC_BASE_URL` 로 충분). 즉 reference counting 버그의 트리거 조건이 성립하지 않는다.

## 진단 치트시트 (macOS / zsh)

```sh
# 라우팅 확인 (새 로그인 셸 기준)
env | grep -E 'ANTHROPIC|HEADROOM'

# 8787 을 누가 LISTEN 하나 + 부모 체인 (launchd 가 소유하면 service 가 부모)
pid=$(lsof -nP -iTCP:8787 -sTCP:LISTEN | awk 'NR==2{print $2}')
ps -o pid=,ppid=,command= -p "$pid"

# launchd service 등록/상태
launchctl list | grep headroom
headroom install status

# proxy 헬스 + 실제 압축 동작
curl -s http://127.0.0.1:8787/health
grep 'content_router' ~/.headroom/logs/proxy.log | tail -3
```

연관: token mode 압축 timeout 으로 `api_error` 가 나는 별개 이슈는 다른(Windows) 머신에서 `--mode cache` 로 회피했던 것 — 이 macOS 머신에서는 재현되지 않아 token 을 유지한다. 재현되면 `headroom install apply --mode cache` 로 재설치.
