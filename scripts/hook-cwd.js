'use strict';
// hook stdin JSON 의 `cwd` 를 읽는 공유 모듈(hook 아님 — SessionStart 계열 훅 둘이 require).
// `cwd` 는 전 이벤트 공통 입력 필드이고 **Claude 를 따라간다** — worktree 에 들어가면 worktree 루트,
// `cd` 하면 그 디렉토리(공식 문서). 그래서 `process.cwd()` 보다 이쪽이 정확하다. 형제 훅
// (`dlc-task-router.js`·`guard-worktree-edit.js`·`notify-hook.js`)도 같은 입력원을 쓴다.
//
// 계약: 항상 콜백을 정확히 한 번 부른다 · 어떤 경우에도 세션 시작을 막지 않는다.
//   - stdin 이 TTY(터미널에서 직접 실행) → 즉시 `process.cwd()`
//   - JSON 이 아니거나 cwd 가 비었으면 → `process.cwd()`
//   - stdin 이 닫히지 않으면 → 타이머가 끊는다(그래서 unref 하지 않는다. 이 타이머가 유일한 진행 보장)
const DEFAULT_STDIN_MS = 1000;

function readHookCwd(cb, ms) {
  if (process.stdin.isTTY) {
    cb(process.cwd());
    return;
  }
  let raw = '';
  let done = false;
  const finish = () => {
    if (done) return;
    done = true;
    clearTimeout(timer);
    let c = '';
    try {
      c = String(JSON.parse(raw).cwd || '');
    } catch {
      /* JSON 아님·잘림 → 프로세스 cwd 로 폴백 */
    }
    cb(c || process.cwd());
  };
  const timer = setTimeout(finish, ms || DEFAULT_STDIN_MS);
  try {
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (c) => {
      raw += c;
    });
    process.stdin.on('end', finish);
    process.stdin.on('error', finish);
  } catch {
    finish();
  }
}

module.exports = { readHookCwd, DEFAULT_STDIN_MS };
