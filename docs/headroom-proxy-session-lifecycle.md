# 동시 Claude 세션: headroom proxy 프로세스 수명주기

여러 Claude Code 세션을 동시에 띄워 쓸 때, **어떤 보조 프로세스를 끄면 다른 세션까지 죽는가**를 정리한 운영 노트. 한 번 크게 당한 적이 있어 기록한다(headroom proxy 세션 동반 사망). headroom `0.25.0` 기준.

## TL;DR

| 대상 | 구조 | 잘못 끄면 | 다른 세션 |
|---|---|---|---|
| **headroom proxy** (8787) | 전역 공유 **단일** 인스턴스 | 모든 세션 `api_error` | **다 죽음** |

- proxy를 죽이는 건 **`headroom wrap claude` 세션을 닫는 것**이지, 그냥 `claude`를 켜는 것이 아니다.

## 이 머신의 셋업

- User 환경변수: `ANTHROPIC_BASE_URL=http://127.0.0.1:8787`, `HEADROOM_MODE=cache` (레지스트리 `HKCU\Environment`).
- → **모든** `claude` 가 (wrap 없이 그냥 `claude` 로 띄워도) 이 단일 proxy 를 경유한다. `claude.exe` 자체는 순수 exe 라 "wrap 안 했으니 proxy 무관"은 오판.
- scheduled task `headroom-proxy` 가 로그온 시 proxy 를 8787 에 상시 기동하도록 설계돼 있음.

## 1. headroom proxy — 왜 wrap 세션을 닫으면 다른 세션이 죽나

headroom 은 로컬 HTTP proxy 다. `ANTHROPIC_BASE_URL` 을 `127.0.0.1:8787` 로 돌려 Claude ↔ Anthropic API 요청을 가로채 최적화한다(cache mode: prefix 동결로 캐시 hit 최대화 / token mode: 압축 — 이 머신은 압축 30s timeout 이슈로 cache 고정).

**핵심: proxy 는 8787 단일 포트의 공유 인스턴스이고, 모든 세션이 그것 하나를 쓴다.**

문제 흐름:
1. `headroom wrap claude` 는 8787 이 비어 있으면 proxy 를 **자기 자식으로 spawn** → 그 세션이 proxy "주인"이 된다. (`_ensure_proxy` 가 직접 띄우면 `Popen` 핸들을, 재사용이면 `None` 을 반환.)
2. 다른 세션들(그냥 `claude`)도 같은 proxy 를 HTTP 로 쓰지만, **wrap 코드를 안 거치므로 client marker 를 등록하지 않는다** (`_register_proxy_client` 는 wrap 흐름에서만 호출).
3. 주인 wrap 세션을 닫으면 cleanup(`_make_cleanup`)이 돈다:
   - `_other_clients_exist()` 로 "다른 사용자 있나"를 확인하는데, 이게 **wrap marker 만** 센다(`_live_proxy_clients`).
   - 순수 `claude` 세션은 marker 가 없어 **카운트 0** 으로 오판 → `proc.terminate()` → **공유 proxy 사망**.
4. proxy 가 죽자 그것을 쓰던 다른 세션 전부 `api_error`.

proxy 는 실제 active session 수를 알지만(`_proxy_active_session_count`, health 의 websocket_sessions) cleanup 은 그걸 안 본다 = **reference count 의 분모가 틀렸다.** "wrap 1개 + 순수 claude N개" 조합이 정확히 이 버그를 때린다.

보조 요인(Windows): `_start_proxy` 의 `start_new_session=os.name=="posix"` 가 Windows 에선 `False` → proxy 가 wrap 콘솔 트리에 묶여, 창을 그냥 닫아도 동반 종료될 수 있다.

### 범인은 "닫기"지 "켜기"가 아니다 (헷갈리기 쉬움)

"세션 닫고 `claude` 로 새로 켰더니 다른 세션이 죽었다"의 진짜 원인은 **닫기**다. `claude` 는 순수 exe(`~/.local/bin/claude.exe`, alias/function 아님 — `Get-Command claude` 가 Application 으로 resolve)라 headroom 코드를 전혀 실행하지 않고, proxy 를 띄우지도 죽이지도 못한다. 닫는 순간 proxy 가 이미 죽었고, 새로 켠 claude 는 죽은 proxy 에 붙어 "켤 때 다 죽은 것처럼" 보일 뿐이다.

## 2. 권장 운영

**proxy 수명주기를 wrap 에 의존시키지 않는다:**

1. 동시에 여러 세션을 쓸 거면 `headroom wrap claude` 대신 **그냥 `claude`** 로 띄운다. 전역 `ANTHROPIC_BASE_URL` 덕에 wrap 없이도 proxy 를 경유하고, 어떤 세션도 "주인"이 안 되므로 닫아도 proxy 를 안 건드린다. proxy 는 scheduled task `headroom-proxy` 가 책임지게 둔다. → 가장 깔끔.
2. 굳이 wrap 을 쓰려면 동시 세션을 **전부 wrap 으로 통일**한다(각자 marker 등록 → reference counting 정상). **wrap + 순수 claude 를 섞는 게 문제의 전부다.**

주의: 지금 8787 주인이 wrap 세션이면 그 창을 닫는 순간 다른 세션이 끊긴다. 닫기 전에 독립 proxy 를 8787 에 먼저 확보(scheduled task 재실행 또는 `headroom proxy --port 8787 --mode cache` 를 별도 기동)해야 한다. 포트는 한 번에 하나만 bind 되니 교대 순서가 중요하다.

## 진단 치트시트 (PowerShell)

```powershell
# 라우팅 확인
Get-ChildItem env: | Where-Object Name -match 'ANTHROPIC|HEADROOM'

# 8787 주인이 누구인가 — 부모 체인이 'headroom wrap claude' 면 그 세션이 proxy 주인
$pid0 = (Get-NetTCPConnection -LocalPort 8787 -State Listen).OwningProcess
while ($pid0) {
  $p = Get-CimInstance Win32_Process -Filter "ProcessId=$pid0"
  if (-not $p) { break }
  "{0} | parent {1} | {2}" -f $p.ProcessId,$p.ParentProcessId,$p.Name
  if ($p.ParentProcessId -in 0,$pid0) { break }
  $pid0 = $p.ParentProcessId
}
```

연관: token-mode 압축 timeout 으로 세션이 `api_error` 로 멈추는 별개 이슈는 proxy 를 `--mode cache` 로 교체해 해결한다(이 머신은 `HEADROOM_MODE=cache` 로 영구화됨).
