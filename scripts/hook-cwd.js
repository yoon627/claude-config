'use strict';
// SessionStart 계열 훅 둘(session-brief·session-fetch)이 require 하는 공유 모듈(hook 아님).
// (1) hook stdin JSON 의 `cwd` 읽기. `cwd` 는 전 이벤트 공통 입력 필드이고 **Claude 를 따라간다** —
// worktree 에 들어가면 worktree 루트, `cd` 하면 그 디렉토리(공식 문서). 그래서 `process.cwd()` 보다
// 이쪽이 정확하다. 형제 훅(`dlc-task-router.js`·`guard-worktree-edit.js`·`notify-hook.js`)도 같은 입력원을 쓴다.
//
// 계약: 항상 콜백을 정확히 한 번 부른다 · 어떤 경우에도 세션 시작을 막지 않는다.
//   - stdin 이 TTY(터미널에서 직접 실행) → 즉시 `process.cwd()`
//   - JSON 이 아니거나 cwd 가 비었으면 → `process.cwd()`
//   - stdin 이 닫히지 않으면 → 타이머가 끊는다(그래서 unref 하지 않는다. 이 타이머가 유일한 진행 보장)
//
// (2) 시간 배수(`scaleMs`). 두 훅이 직접 거는 시간 상한(git 호출 timeout·브리프 O 예산·이 stdin 대기·stdout
// 백스톱)이 모두 이것을 거친다(ssh·http 의 네트워크 상한은 거치지 않는다). **테스트 전용**이다 — 프로세스
// 생성 부하에서 상한이 만료돼 기능 단언이 흔들리지 않게 테스트가 키운다. 운영에 두면 최악 합이 그만큼 커져
// settings 의 훅 timeout 을 넘기 쉽고, 넘으면 하니스가 훅을 죽이며 하니스는 자손을 거두지 않아 git 이 고아로 남는다.
const DEFAULT_STDIN_MS = 1000;
const TIME_SCALE_ENV = 'CLAUDE_BRIEF_FETCH_TEST_TIME_SCALE';

function scaleMs(ms, env = process.env) {
  const v = Number(env[TIME_SCALE_ENV]);
  if (Number.isNaN(v)) return ms;
  // 하한 1: 운영 상한보다 줄이지 않는다(0 은 execFileSync 에서 "상한 없음"이다). 상한 20: 운영에서 잘못 켰을 때
  // 고아 git 이 사는 시간의 상한. 반올림: execFileSync 는 정수가 아닌 timeout 을 던진다.
  return Math.round(ms * Math.min(Math.max(v, 1), 20));
}

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
  const timer = setTimeout(finish, scaleMs(ms || DEFAULT_STDIN_MS));
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

module.exports = { readHookCwd, scaleMs, TIME_SCALE_ENV, DEFAULT_STDIN_MS };
