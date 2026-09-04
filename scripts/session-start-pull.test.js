#!/usr/bin/env node
// settings.json 의 SessionStart 자동 pull 훅 회귀 테스트.
//
// 왜 필요한가: 이 훅은 **자기 자신의 업데이트 배포 경로**다. 경로 오타 하나로도
// `JSON.parse` 는 통과하고(CI 의 JSON validation 이 보는 전부다) 전 머신이 조용히 업데이트를
// 멈춘다 — 이 훅이 애초에 고치려던 "132커밋 밀렸는데 아무도 몰랐다" 사고의 상위 재현이다.
// 그래서 문자열을 눈으로 읽는 대신 fixture HOME 에 실제로 spawn 해 동작을 고정한다.
// (셸 훅을 fixture repo 로 spawn 하는 방식은 install-hooks.test.js 선례.)
//
// settings.json 의 command 를 **그대로** 돌린다. 스크립트를 직접 실행하면 "settings 가 엉뚱한
// 경로를 가리킨다"는 이 테스트의 존재 이유가 검증에서 빠지므로, fixture HOME 안에 스크립트를
// 복사해 두고 command 가 스스로 그것을 찾아가게 한다.
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync, spawnSync } = require('child_process');

for (const k of ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE']) delete process.env[k];

let n = 0;
const ok = (name, fn) => { fn(); n++; };

const REPO = path.join(__dirname, '..');
const SETTINGS = JSON.parse(fs.readFileSync(path.join(REPO, 'settings.json'), 'utf8'));
const GROUP = SETTINGS.hooks.SessionStart[0];
const ENTRY = GROUP.hooks[0];
const COMMAND = ENTRY.command;
const SCRIPT_REL = 'scripts/session-start-pull.sh';
const SCRIPT_ABS = path.join(REPO, SCRIPT_REL);

function git(dir, args) {
  execFileSync('git', ['-C', dir, ...args], { stdio: 'ignore' });
}

// fixture HOME 에 <home>/.claude 를 만들고, origin 이 1커밋 앞선 상태로 둔다.
// command 가 `~/.claude` 를 쓰므로 HOME 만 갈아끼우면 실 repo 를 건드리지 않고 검증된다.
// 스크립트도 같은 상대경로에 복사해 둬야 command 가 실제로 찾아간다.
function makeHome({ withScript = true } = {}) {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'ssp-home-'));
  const bare = path.join(home, 'origin.git');
  const repo = path.join(home, '.claude');
  execFileSync('git', ['init', '-q', '--bare', '-b', 'main', bare], { stdio: 'ignore' });
  execFileSync('git', ['clone', '-q', bare, repo], { stdio: 'ignore' });
  git(repo, ['config', 'user.email', 't@t']);
  git(repo, ['config', 'user.name', 't']);
  git(repo, ['config', 'commit.gpgsign', 'false']);
  fs.writeFileSync(path.join(repo, 'shared.txt'), 'a');
  fs.writeFileSync(path.join(repo, 'other.txt'), 'b');
  git(repo, ['add', '-A']);
  git(repo, ['commit', '-m', 'init']);
  git(repo, ['push', '-q', 'origin', 'HEAD:main']);
  git(repo, ['branch', '-M', 'main']);
  if (withScript) {
    fs.mkdirSync(path.join(repo, 'scripts'), { recursive: true });
    fs.copyFileSync(SCRIPT_ABS, path.join(repo, SCRIPT_REL));
  }
  // 원격을 1커밋 앞세운다(shared.txt 변경).
  const other = path.join(home, 'other');
  execFileSync('git', ['clone', '-q', bare, other], { stdio: 'ignore' });
  git(other, ['config', 'user.email', 't@t']);
  git(other, ['config', 'user.name', 't']);
  git(other, ['config', 'commit.gpgsign', 'false']);
  fs.writeFileSync(path.join(other, 'shared.txt'), 'remote');
  git(other, ['add', '-A']);
  git(other, ['commit', '-m', 'remote']);
  git(other, ['push', '-q', 'origin', 'HEAD:main']);
  return { home, repo };
}

// timeout 은 필수다. 스크립트가 fetch 를 백그라운드로 돌리므로, stdio 를 제대로 끊지 못한 회귀가
// 들어오면 spawnSync 가 영원히 반환하지 않고 CI 가 통째로 멈춘다.
function runChain(home, extraEnv, opts = {}) {
  const r = spawnSync('sh', ['-c', COMMAND], {
    env: { ...process.env, HOME: home, ...extraEnv },
    encoding: 'utf8',
    timeout: opts.timeout || 30000,
  });
  assert.ok(!r.error, `spawn 실패: ${r.error && r.error.message}`);
  return { out: (r.stdout || '').trim(), code: r.status };
}
const head = (repo) => execFileSync('git', ['-C', repo, 'rev-parse', 'HEAD']).toString().trim();

// PATH 앞에 두는 `git` stub. fetch 만 매달리게 해 워치독을 결정적으로 검증한다
// (blackhole IP 는 환경 의존이고 10초를 잡아먹는다).
function makeGitStub({ grandchildMarker } = {}) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ssp-stub-'));
  const real = execFileSync('sh', ['-c', 'command -v git']).toString().trim();
  // 실제 git 은 fetch 중 ssh·git-remote-https 를 손자로 띄운다. 그 손자가 워치독 kill 뒤에도
  // 살아남는지 보려면 stub 도 손자를 띄워야 한다(마커를 계속 갱신해 생존을 드러낸다).
  // 손자 루프는 **유한**해야 한다. 무한이면 이 케이스가 실패할 때마다(= 회귀를 고치는 동안
  // 반복 실행할 때마다) 개발 머신에 루프가 하나씩 영구히 쌓인다.
  const spawnGrandchild = grandchildMarker
    ? `( _i=0; while [ $_i -lt 60 ]; do date +%s > "${grandchildMarker}"; sleep 0.3; _i=$((_i+1)); done ) &\n  `
    : '';
  fs.writeFileSync(
    path.join(dir, 'git'),
    `#!/bin/sh\nfor a in "$@"; do\n  if [ "$a" = fetch ]; then\n  ${spawnGrandchild}sleep 60\n  exit 0\n  fi\ndone\nexec "${real}" "$@"\n`,
    { mode: 0o755 },
  );
  return dir;
}
const sleepSync = (sec) => execFileSync('sh', ['-c', `sleep ${sec}`]);

ok('settings.json 이 스크립트를 가리키고 그 파일이 repo 에 실존한다', () => {
  assert.ok(COMMAND.includes(SCRIPT_REL), `command 가 ${SCRIPT_REL} 를 참조하지 않는다: ${COMMAND}`);
  assert.ok(fs.existsSync(SCRIPT_ABS), `${SCRIPT_REL} 가 없다`);
});

ok('훅은 async 로 남는다 — 동기로 바꿔도 CLAUDE.md 최신화는 못 얻고 세션 시작만 늦어진다', () => {
  // CLAUDE.md 로드는 SessionStart 훅과 **경합**한다(순서 보장 아님, 실측). 즉시 쓰는 훅은 이기고
  // 0.5초짜리 pull 은 진다 — 동기 전환은 비용만 남기므로 채택하지 않았다.
  assert.strictEqual(ENTRY.async, true);
  // 워치독(기본 8s)보다 하니스 timeout 이 커야 워치독이 먼저 작동해 고아가 안 남는다.
  assert.ok(ENTRY.timeout >= 15, `timeout 이 워치독 상한보다 작다: ${ENTRY.timeout}`);
});

ok('hang 방어(프롬프트·SSH·HTTP)가 스크립트에 있다', () => {
  const s = fs.readFileSync(SCRIPT_ABS, 'utf8');
  assert.match(s, /GIT_TERMINAL_PROMPT=0/);
  assert.match(s, /BatchMode=yes/);
  assert.match(s, /ConnectTimeout=10/);
  assert.match(s, /credential\.helper=/);
  assert.match(s, /core\.askpass=/i);
  assert.match(s, /http\.lowSpeedLimit=1000/);
  assert.match(s, /http\.lowSpeedTime=10/);
});

ok('워치독 상한이 wall-clock 이고 하니스 예산 안으로 clamp 된다', () => {
  // 이 둘은 동작만으로는 잠기지 않는다: iteration 카운트로 되돌려도 타이밍 단언 범위 안에
  // 들어와 초록이 된다(mutation 으로 확인). 그래서 설계 형태를 직접 고정한다.
  const s = fs.readFileSync(SCRIPT_ABS, 'utf8');
  assert.match(s, /_deadline=\$\(\(\s*\$\(date \+%s\)/, '상한을 wall-clock 으로 잡아야 한다');
  assert.doesNotMatch(s, /_n\s*\+\s*1|_n=\$\(\(/, 'iteration 카운터로 상한을 재면 안 된다');
  // 비숫자·과대값이 그대로 쓰이면 각각 "매번 즉시 kill"과 "하니스가 먼저 죽여 고아 잔존"이 된다.
  assert.match(s, /\*\[!0-9\]\*\)/, '비숫자 timeout 을 걸러야 한다');
  assert.match(s, /-gt 12/, '하니스 timeout(15) 안으로 clamp 해야 한다');
});

ok('① clean + behind → pull 하고 한 줄 알린다', () => {
  const { home, repo } = makeHome();
  const before = head(repo);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.match(out, /updated from origin\/main/);
  assert.notStrictEqual(head(repo), before);
});

ok('①-b 원격 추적 ref 도 갱신된다 (신호 N 이 이 ref 로 밀림을 잰다)', () => {
  const { home, repo } = makeHome();
  runChain(home);
  const tracking = execFileSync('git', ['-C', repo, 'rev-parse', 'refs/remotes/origin/main'])
    .toString().trim();
  assert.strictEqual(tracking, head(repo));
});

ok('② 무관 파일이 더러워도 pull 한다 (dirty 게이트 제거의 핵심)', () => {
  const { home, repo } = makeHome();
  const before = head(repo);
  fs.writeFileSync(path.join(repo, 'other.txt'), 'local-dirty');
  const { code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.notStrictEqual(head(repo), before);
  assert.strictEqual(fs.readFileSync(path.join(repo, 'other.txt'), 'utf8'), 'local-dirty');
});

ok('③ 충돌 파일이 더러우면 git 이 거부 — 무음·변경 보존', () => {
  const { home, repo } = makeHome();
  const before = head(repo);
  fs.writeFileSync(path.join(repo, 'shared.txt'), 'local-dirty');
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
  assert.strictEqual(fs.readFileSync(path.join(repo, 'shared.txt'), 'utf8'), 'local-dirty');
});

ok('④ 이미 최신이면 무음', () => {
  const { home } = makeHome();
  runChain(home);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
});

ok('⑤ main 이 아니면 skip', () => {
  const { home, repo } = makeHome();
  git(repo, ['checkout', '-q', '-b', 'feature']);
  const before = head(repo);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
});

ok('⑥ CLAUDE_AUTOPULL_OFF=1 이면 아무것도 안 한다', () => {
  const { home, repo } = makeHome();
  const before = head(repo);
  const { out, code } = runChain(home, { CLAUDE_AUTOPULL_OFF: '1' });
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
});

ok('⑥-b .autopull-off 파일이 있으면 아무것도 안 한다 (GUI 실행용 즉시 레버)', () => {
  const { home, repo } = makeHome();
  const before = head(repo);
  fs.writeFileSync(path.join(repo, '.autopull-off'), '');
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
});

ok('⑦ rebase/merge 진행 중이면 skip', () => {
  const { home, repo } = makeHome();
  fs.mkdirSync(path.join(repo, '.git', 'rebase-merge'), { recursive: true });
  const before = head(repo);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
});

ok('⑧ ~/.claude 가 git repo 가 아니어도 exit 0 (fail-open)', () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'ssp-nongit-'));
  fs.mkdirSync(path.join(home, '.claude', 'scripts'), { recursive: true });
  fs.copyFileSync(SCRIPT_ABS, path.join(home, '.claude', SCRIPT_REL));
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
});

ok('⑨ ~/.claude 가 아예 없어도 exit 0 (fail-open)', () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'ssp-nohome-'));
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
});

ok('⑩ 스크립트 파일이 없어도 세션을 막지 않는다 (배포 순환 fail-open)', () => {
  const { home } = makeHome({ withScript: false });
  const { code } = runChain(home);
  assert.strictEqual(code, 0);
});

ok('⑪ 워치독이 매달린 fetch 를 상한 안에 죽인다', () => {
  const { home, repo } = makeHome();
  const before = head(repo);
  const stub = makeGitStub();
  const t0 = Date.now();
  const { code } = runChain(
    home,
    { PATH: `${stub}${path.delimiter}${process.env.PATH}`, CLAUDE_AUTOPULL_TIMEOUT: '3' },
    { timeout: 30000 },
  );
  const elapsed = Date.now() - t0;
  assert.strictEqual(code, 0, '워치독 발동 후에도 fail-open 이어야 한다');
  // 하한은 "너무 일찍 죽지 않음"을 건다 — timeout 파싱이 깨져 deadline=now 가 되면 무음으로
  // 매번 즉시 kill 된다(그 경우 0.3s 안에 끝난다).
  // **N-1 초까지 내려갈 수 있다**: 마감이 `date +%s` 초 단위라 절삭된다. 시작이 X.99 초면
  // 마감 X+3 은 실제 2.01 초 뒤다. 이걸 몰라 1500ms 로 잡았다가 CI 가 1427ms 로 잡아냈다.
  assert.ok(elapsed >= 1800, `상한 전에 죽으면 안 된다 (실제 ${elapsed}ms)`);
  // 상한 쪽은 느린 파일시스템(네트워크 마운트·WSL /mnt)에서 사전 git 호출이 길어질 수 있어
  // 여유를 둔다. **설계(wall-clock)를 잠그는 것은 위 텍스트 단언**이고 여기서는 "워치독이 아예
  // 없다/카운트가 터무니없다"급 회귀만 잡는다(post-checkout 식 100회 루프면 ~23s 라 걸린다).
  assert.ok(elapsed < 12000, `상한 안에 끝나야 한다 (실제 ${elapsed}ms)`);
  // fetch 가 죽었으므로 merge 도 없다 — HEAD 불변.
  assert.strictEqual(head(repo), before);
});

ok('⑪-b 워치독이 죽인 뒤 stale FETCH_HEAD 로 머지하지 않는다', () => {
  // 앞선 세션이 fetch 는 성공했는데 merge 가 거부되면 FETCH_HEAD 가 남는다. 그 상태에서
  // 네트워크가 죽어 fetch 가 kill 되면, 가드가 없는 구현은 **origin 과 한 번도 통신하지 않고**
  // 옛 FETCH_HEAD 로 ff 한 뒤 "updated" 알림까지 낸다 — 사용자는 최신화됐다고 믿는다.
  const { home, repo } = makeHome();
  const shared = path.join(repo, 'shared.txt');

  // 1) 충돌 dirty 로 merge 를 거부시켜 stale FETCH_HEAD 를 남긴다.
  fs.writeFileSync(shared, 'local-dirty');
  const stale = runChain(home);
  assert.strictEqual(stale.out, '', 'merge 가 거부돼 무음이어야 한다');
  const before = head(repo);
  assert.ok(fs.existsSync(path.join(repo, '.git', 'FETCH_HEAD')), 'fetch 는 성공했어야 한다');

  // 2) dirty 를 걷어내 이제는 ff 가 가능한 상태로 만든다.
  git(repo, ['checkout', '--', 'shared.txt']);

  // 3) fetch 를 매달리게 해 워치독이 죽이게 한다.
  const stub = makeGitStub();
  const { out, code } = runChain(home, {
    PATH: `${stub}${path.delimiter}${process.env.PATH}`,
    CLAUDE_AUTOPULL_TIMEOUT: '2',
  });

  assert.strictEqual(code, 0);
  assert.strictEqual(head(repo), before, 'stale FETCH_HEAD 로 ff 하면 안 된다');
  assert.strictEqual(out, '', '통신하지 않았는데 "updated" 를 알리면 안 된다');
});

ok('⑫ 워치독이 손자(ssh·git-remote-https)까지 거둔다 — 그룹 kill 회귀 락', () => {
  const { home } = makeHome();
  const marker = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'ssp-mark-')), 'alive');
  const stub = makeGitStub({ grandchildMarker: marker });
  runChain(
    home,
    { PATH: `${stub}${path.delimiter}${process.env.PATH}`, CLAUDE_AUTOPULL_TIMEOUT: '2' },
    { timeout: 30000 },
  );
  // 내용이 아니라 mtime 을 본다. `date > marker` 는 truncate 후 write 라, 그 틈에 내용을 읽으면
  // 손자가 죽었는데도 빈 문자열이 잡혀 결과가 흔들린다(실제로 한 번 겪었다).
  // 종료 직후 1초는 진행 중이던 write 가 끝나도록 두고 잰다.
  sleepSync(1);
  const settled = fs.statSync(marker).mtimeMs;
  sleepSync(2);
  assert.strictEqual(
    fs.statSync(marker).mtimeMs,
    settled,
    '손자가 살아남아 계속 쓰고 있다 — 워치독이 프로세스 그룹째 죽이지 않는다',
  );
});

console.log(`session-start-pull.test.js: ${n} tests passed`);
