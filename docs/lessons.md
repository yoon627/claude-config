# Lessons

재발 가능성 높고 비자명한 함정만 기록. 형식: `- [YYYY-MM-DD] 증상 → 원인 → 해결 (관련 파일/커밋)`

- [2026-06-02] Windows 작업완료/입력대기 toast 알림이 안 뜸 → `notify-hook.js` 가 powershell 을 `detached:true` + `child.unref()` 로 spawn 하면서 stdin 은 `'pipe'`(hook JSON 전달용)로 유지 → Node 문서상 detached 자식이 부모 종료 후 생존하려면 stdio 도 부모와 분리돼야 하는데 stdin pipe 가 그 조건을 깨, 부모(node) 종료와 함께 자식이 죽어 toast 미발생. #6 `a066562` 에서 settings.json 의 powershell 직접호출 → node 래퍼 전환 시 유입 → 해결: win32 분기에서 `detached`/`unref` 제거(node 가 powershell 종료까지 event loop 유지, hook 이 `async:true` 라 Claude Code 논블록) + hung powershell 대비 watchdog(`child.kill()` 10s) + `child.stdin` async EPIPE 핸들러. **함정**: `notify.ps1` 직접 실행만으로 "정상" 오판 금지 — 실제 트리거 경로는 node→powershell 이므로 `node notify-hook.js` 경유 + `CLAUDE_NOTIFY_DEBUG=1` 자식 로그(`%TEMP%\claude-notify-debug.json`)로 검증할 것. (scripts/notify-hook.js)
