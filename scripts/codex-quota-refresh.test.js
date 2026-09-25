#!/usr/bin/env node
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const REFRESH = path.join(__dirname, '..', 'codex-quota-refresh.js');

let n = 0;
const ok = (name, fn) => { fn(); n++; };

if (process.platform === 'win32') {
  // stub `codex` 를 PATH 의 실행 파일로 흉내 내는 방식이라 POSIX 에서만 돈다.
  console.log('codex-quota-refresh.test.js: skipped on win32');
  process.exit(0);
}

// STUB_MODE — answer: 두 요청에 답하고 곧바로 exit 0 · serve: 답한 뒤 stdin 이 닫힐 때까지 산다(실제 app-server)
// · silent: 답 없이 exit 0 · orphan: 파이프를 물려받은 손자 프로세스를 남기고 답 없이 exit 0
const STUB = `#!/usr/bin/env node
const fs = require('fs');
const mode = process.env.STUB_MODE;
fs.writeFileSync(process.env.STUB_PID_FILE, String(process.pid));
if (mode === 'silent') process.exit(0);
if (mode === 'orphan') {
  const c = require('child_process').spawn('sleep', ['30'], { stdio: ['ignore', 'inherit', 'inherit'], detached: true });
  fs.writeFileSync(process.env.STUB_PID_FILE + '.orphan', String(c.pid));
  c.unref();
  process.exit(0);
}
let buf = '';
process.stdin.on('end', () => process.exit(0));
process.stdin.on('data', (c) => {
  buf += c;
  let i;
  while ((i = buf.indexOf('\\n')) !== -1) {
    const msg = JSON.parse(buf.slice(0, i));
    buf = buf.slice(i + 1);
    const result = msg.method === 'initialize' ? {} : { rateLimits: { primary: { usedPercent: 40, resetsAt: 123 } } };
    process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id: msg.id, result }) + '\\n', () => {
      if (mode === 'answer' && msg.method !== 'initialize') process.exit(0);
    });
  }
});
`;

const alive = (pid) => { try { process.kill(pid, 0); return true; } catch (_) { return false; } };
function gone(pid) {
  for (let i = 0; i < 20 && alive(pid); i++) Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 100);
  return !alive(pid);
}

function refresh(mode, prepare) {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'codex-quota-test-'));
  const bin = path.join(home, 'bin');
  fs.mkdirSync(bin);
  if (mode !== 'missing') fs.writeFileSync(path.join(bin, 'codex'), STUB, { mode: 0o755 });
  const cache = path.join(home, '.claude', 'cache');
  fs.mkdirSync(cache, { recursive: true });
  fs.writeFileSync(path.join(cache, 'codex-quota.lock'), '1');
  if (prepare) prepare(cache);
  const pidFile = path.join(home, 'stub.pid');
  const started = Date.now();
  const r = spawnSync(process.execPath, [REFRESH], {
    env: { ...process.env, HOME: home, STUB_MODE: mode, STUB_PID_FILE: pidFile,
      // missing 은 stub 디렉토리만 — node 옆에 npm 전역 codex 가 있는 머신에서 진짜 codex 를 찾지 않게.
      PATH: (mode === 'missing' ? [bin] : [bin, path.dirname(process.execPath), '/usr/bin', '/bin']).join(path.delimiter) },
    encoding: 'utf8',
    timeout: 30000,
  });
  const orphanFile = pidFile + '.orphan';
  if (fs.existsSync(orphanFile)) try { process.kill(Number(fs.readFileSync(orphanFile, 'utf8')), 'SIGKILL'); } catch (_) {}
  const result = { status: r.status, ms: Date.now() - started, files: fs.readdirSync(cache),
    stubPid: fs.existsSync(pidFile) ? Number(fs.readFileSync(pidFile, 'utf8')) : null };
  if (mode !== 'missing') assert.ok(result.stubPid, 'stub codex did not start');
  try { result.cache = JSON.parse(fs.readFileSync(path.join(cache, 'codex-quota.json'), 'utf8')); } catch (_) {}
  fs.rmSync(home, { recursive: true, force: true });
  return result;
}

ok('계속 살아 있는 app-server 가 답하면 캐시를 쓰고 바로 끝내며 app-server 도 남기지 않는다', () => {
  const r = refresh('serve');
  assert.strictEqual(r.status, 0);
  assert.ok(r.ms < 5000, `took ${r.ms}ms`);
  assert.strictEqual(r.cache.primary.usedPercent, 40);
  assert.deepStrictEqual(r.files.sort(), ['codex-quota.json']);
  assert.ok(gone(r.stubPid), 'app-server stub still running');
});

ok('app-server 가 답하자마자 끝나도 그 응답을 캐시에 쓴다', () => {
  const r = refresh('answer');
  assert.strictEqual(r.status, 0);
  assert.strictEqual(r.cache.primary.usedPercent, 40);
});

ok('app-server 가 답 없이 exit 0 하면 timeout 을 기다리지 않고 negative cache', () => {
  const r = refresh('silent');
  assert.strictEqual(r.status, 1);
  assert.ok(r.ms < 5000, `took ${r.ms}ms`);
  assert.match(r.cache.error, /^process-exit/);
});

ok('codex 가 PATH 에 없으면 곧 spawn-error negative cache 를 쓰고 lock 을 푼다', () => {
  const r = refresh('missing');
  assert.strictEqual(r.status, 1);
  assert.ok(r.ms < 5000, `took ${r.ms}ms`);
  assert.match(r.cache.error, /^spawn-error/);
  assert.ok(!r.files.includes('codex-quota.lock'));
});

ok('손자 프로세스가 파이프를 쥔 채 app-server 만 끝나도 곧 끝낸다', () => {
  const r = refresh('orphan');
  assert.strictEqual(r.status, 1);
  assert.ok(r.ms < 5000, `took ${r.ms}ms`);
  assert.match(r.cache.error, /^process-exit/);
});

ok('캐시를 못 쓰면 비0 으로 곧 끝내고, 임시 파일은 지우고, lock 은 남겨 재spawn 을 늦춘다', () => {
  const r = refresh('serve', (cache) => fs.mkdirSync(path.join(cache, 'codex-quota.json')));
  assert.strictEqual(r.status, 1);
  assert.ok(r.ms < 5000, `took ${r.ms}ms`);
  assert.deepStrictEqual(r.files.filter((f) => f.includes('.tmp.')), []);
  assert.ok(r.files.includes('codex-quota.lock'));
  assert.ok(gone(r.stubPid), 'app-server stub still running');
});

console.log(`codex-quota-refresh.test.js: ${n} tests passed`);
