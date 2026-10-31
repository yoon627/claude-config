# wiki docs/headroom-proxy-session-lifecycle 규칙 목록 (translate-wiki-docs)

공용 wiki 3eaa4f4 의 `docs/headroom-proxy-session-lifecycle.md`(69줄) 기준. 한 줄 = 한 조항(한정어도 조항의 일부). 번역 대조는 `locations-en.txt`(`<id> | <영어 인용>`, 인용 여러 개는 ` ‖ `, 각 인용은 파일 안에서 한 번, manifest 순서대로). 이 manifest 는 번역 초안 전에 만든다. 제목 줄(코드 블록 안 `#` 주석 줄 포함)은 check.json `headings` 가 고정한다. 과거 운영 기록(README "과거 운영 기록은 … 보존")이라 사실 기술이 대부분이다.

## 머리말
- P.1 여러 Claude Code 세션을 동시에 띄울 때 headroom proxy 의 기동·유지와 어떤 조작이 다른 세션에 영향을 주는지 정리한 운영 노트
- P.2 headroom `0.25.0`, macOS(Apple Silicon) 기준
- P.3 proxy 를 launchd service 가 소유하도록 셋업 → proxy 수명주기가 개별 claude 세션과 독립, 세션을 닫아도 proxy 는 안 죽는다

## TL;DR
- T.1 표: headroom proxy(8787) — launchd service `com.headroom.default` 소유, 전역 공유 단일 인스턴스 / 잘못 끄면 그 service 가 즉시 재기동(KeepAlive) / 다른 세션 영향 없음
- T.2 proxy 는 어떤 claude 세션의 자식도 아니다, `headroom install apply` 로 만든 launchd service 가 띄우고 살린다
- T.3 claude 는 `ANTHROPIC_BASE_URL` 로 proxy 를 경유만 — 띄우지도 죽이지도 않는다, 그래서 세션을 닫아도 proxy 는 그대로
- T.4 proxy 를 진짜 멈추려면 `headroom install stop`, 수동 `kill` 해도 launchd 가 곧 되살린다

## 이 머신의 셋업
- S.1 `headroom install apply --preset persistent-service --mode token` 한 번으로 구성
- S.2 건드린 것은 셸 env 와 launchd plist 둘뿐 — `~/.claude/settings.json`·`~/.claude.json` 운영 자산은 변경하지 않는다
- S.3 routing — `~/.zshrc` 의 `# >>> headroom persistent env >>>` 블록(HEADROOM_PORT·HOST·MODE·BACKEND, `ANTHROPIC_BASE_URL="http://127.0.0.1:8787"`)
- S.4 새 로그인 셸에서 띄우는 모든 `claude` 가 이 단일 proxy 를 경유
- S.5 이미 떠 있는 셸/세션은 프로세스 env 가 런타임에 안 바뀌므로 재시작 후 적용
- S.6 상시 기동 — `~/Library/LaunchAgents/com.headroom.default.plist`, 로그인 시 자동 기동 + 죽으면 재기동, `launchctl list | grep headroom` 에 `com.headroom.default` 로 보인다
- S.7 mode = token — 압축까지 해 토큰 절감폭이 크다, 이 머신 proxy.log 상 압축이 timeout 없이 정상(`content_router: ... compressed`, `cache_hit_pct=100`)
- S.8 cache mode 는 압축을 안 해 절감폭이 작다

## 운영 명령
- O.1 `headroom install status` — running/healthy, mode, port 확인
- O.2 `headroom install start|stop|restart` — service 수명주기 제어(이걸로 끄고 켠다)
- O.3 `headroom install remove` — service 해제 + zshrc/plist 등 관리 설정 원복
- O.4 `kill <proxy_pid>` 로 직접 죽이지 말 것 — launchd KeepAlive 가 즉시 새 인스턴스를 띄워 PID 만 바뀐다, 멈추려면 `headroom install stop`

## Windows 세션 동반 사망 버그
- W.1 다른(Windows) 머신에서는 `headroom wrap claude` 로 띄운 세션이 proxy 를 자기 자식으로 spawn 해 proxy "주인"이 됐다
- W.2 주인 세션을 닫으면 cleanup 이 도는데, reference counting 이 wrap marker 만 세어 "그냥 `claude`" 로 붙은 다른 세션을 0 으로 오판 → 공유 proxy `terminate` → 다른 세션 전부 `api_error`
- W.3 "wrap 1개 + 순수 claude N개" 조합이 이 버그를 때렸다
- W.4 macOS 의 이 셋업은 그 전제 자체가 없다 — proxy 소유권이 launchd service 에 있어 어떤 claude 를 닫아도 proxy cleanup 이 돌지 않는다
- W.5 wrap 을 쓸 일도 없다(전역 `ANTHROPIC_BASE_URL` 로 충분), 즉 reference counting 버그의 트리거 조건이 성립하지 않는다

## 진단 치트시트
- X.1 라우팅 확인(새 로그인 셸 기준): `env | grep -E 'ANTHROPIC|HEADROOM'`
- X.2 8787 을 누가 LISTEN 하나 + 부모 체인(launchd 가 소유하면 service 가 부모): `lsof … awk …` 로 pid, `ps -o pid=,ppid=,command= -p "$pid"`
- X.3 launchd service 등록/상태: `launchctl list | grep headroom`, `headroom install status`
- X.4 proxy 헬스 + 실제 압축 동작: `curl -s http://127.0.0.1:8787/health`, `grep 'content_router' ~/.headroom/logs/proxy.log | tail -3`
- X.5 연관: token mode 압축 timeout 으로 `api_error` 가 나는 별개 이슈는 다른(Windows) 머신에서 `--mode cache` 로 회피 — 이 macOS 머신에서는 재현되지 않아 token 유지
- X.6 재현되면 `headroom install apply --mode cache` 로 재설치

## 다른 파일이 가리키는 표지
- `scripts/bootstrap/README.md`·`README.md` 는 파일 경로로만 가리킨다(절 표지 없음). 파일 이름 그대로.
- 명령·포트·plist 경로·로그 문자열(`content_router: ... compressed`·`cache_hit_pct=100`·`api_error`) — 원래 영어. 그대로.

## 핵심 문구
`0.25.0` · 8787 · `com.headroom.default` · KeepAlive · `headroom install apply` · `ANTHROPIC_BASE_URL` · `headroom install stop` · `kill` · `headroom install apply --preset persistent-service --mode token` · `~/.claude/settings.json`·`~/.claude.json` · `~/.zshrc` · `# >>> headroom persistent env >>>` · export ANTHROPIC_BASE_URL="http://127.0.0.1:8787" · `~/Library/LaunchAgents/com.headroom.default.plist` · `launchctl list | grep headroom` · `content_router: ... compressed` · `cache_hit_pct=100` · headroom install start|stop|restart · headroom install remove · `kill <proxy_pid>` · `headroom wrap claude` · reference counting · `terminate` · `api_error` · env | grep -E 'ANTHROPIC|HEADROOM' · ps -o pid=,ppid=,command= -p "$pid" · curl -s http://127.0.0.1:8787/health · grep 'content_router' ~/.headroom/logs/proxy.log | tail -3 · `--mode cache` · `headroom install apply --mode cache`
