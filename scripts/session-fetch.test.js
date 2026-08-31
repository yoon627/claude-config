#!/usr/bin/env node
// session-fetch.js 테스트 — 로컬 repo 를 origin 으로 둔 clone fixture 로 실제 fetch 를 관찰한다.
// 네트워크는 쓰지 않는다(origin 이 로컬 경로). 검증 축: ①ref 가 실제로 갱신되고 밀림 한 줄이 나온다
// ②merge 는 하지 않는다(HEAD·작업트리 불변) ③skip 조건(최근 fetch·upstream 없음·kill switch·비 git)
// ④어떤 경우에도 exit 0.
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const FETCH = path.join(__dirname, 'session-fetch.js');

for (const k of ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE']) delete process.env[k];

let n = 0;
const ok = (name, fn) => {
  fn();
  n++;
};

function git(dir, args, extraEnv) {
  return execFileSync('git', ['-C', dir, ...args], {
    stdio: ['ignore', 'pipe', 'ignore'],
    env: { ...process.env, ...extraEnv },
  }).toString();
}
function initRepo(prefix) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), prefix || 'sf-'));
  execFileSync('git', ['init', '-q', '-b', 'main', dir], { stdio: 'ignore' });
  git(dir, ['config', 'user.email', 't@t']);
  git(dir, ['config', 'user.name', 't']);
  git(dir, ['config', 'commit.gpgsign', 'false']);
  return dir;
}
function commit(dir, msg) {
  fs.writeFileSync(path.join(dir, msg.replace(/\W/g, '_') + '.txt'), msg);
  git(dir, ['add', '-A']);
  git(dir, ['commit', '-m', msg], {
    GIT_AUTHOR_DATE: '2026-01-01T00:00:00',
    GIT_COMMITTER_DATE: '2026-01-01T00:00:00',
  });
}
// origin(로컬 경로)에서 clone 한 작업 repo. clone 이라 upstream·remote 가 실제로 설정된다.
function cloned() {
  const remote = initRepo('sf-remote-');
  commit(remote, 'base');
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'sf-work-')) + '/w';
  execFileSync('git', ['clone', '-q', remote, work], { stdio: 'ignore' });
  git(work, ['config', 'user.email', 't@t']);
  git(work, ['config', 'user.name', 't']);
  git(work, ['config', 'commit.gpgsign', 'false']);
  return { remote, work };
}
function run(cwd, env) {
  const res = require('child_process').spawnSync('node', [FETCH], {
    env: { ...process.env, CLAUDE_SESSION_FETCH_MIN_MINUTES: '0', ...env },
    input: JSON.stringify({ hook_event_name: 'SessionStart', cwd }),
  });
  assert.strictEqual(res.status, 0, `fetch hook 은 항상 exit 0 이어야 한다 (got ${res.status})`);
  return res.stdout.toString();
}
const upstreamSha = (dir) => git(dir, ['rev-parse', 'origin/main']).trim();

ok('① 원격이 앞서면 ref 를 갱신하고 밀림 한 줄을 낸다', () => {
  const { remote, work } = cloned();
  const before = upstreamSha(work);
  commit(remote, 'r1');
  commit(remote, 'r2');
  const out = run(work);
  assert.notStrictEqual(upstreamSha(work), before, 'remote-tracking ref 가 갱신돼야 한다');
  assert.match(out, /2커밋 뒤처짐/);
  assert.match(out, /origin\/main/);
  assert.ok(fs.existsSync(path.join(work, '.git', 'claude-fetch-origin')), 'rate-limit 스탬프를 남긴다');
});

ok('①b 다른 remote 를 fetch 해도 origin 은 건너뛰지 않는다', () => {
  // FETCH_HEAD 는 repo 전역이라 `git fetch other` 만으로도 갱신된다. 그걸 기준으로 삼으면 정작 볼
  // origin 을 "방금 했다"로 건너뛴다 — remote 별 스탬프를 쓰는 이유다.
  const { remote, work } = cloned();
  const other = initRepo('sf-other-');
  commit(other, 'obase');
  git(work, ['remote', 'add', 'other', other]);
  git(work, ['fetch', '--quiet', 'other']); // FETCH_HEAD 가 방금 갱신된다
  const before = upstreamSha(work);
  commit(remote, 'r1');
  const out = run(work, { CLAUDE_SESSION_FETCH_MIN_MINUTES: '9999' });
  assert.notStrictEqual(upstreamSha(work), before, 'origin 스탬프는 없으므로 fetch 해야 한다');
  assert.match(out, /1커밋 뒤처짐/);
});

ok('② merge 는 하지 않는다 — HEAD 와 작업트리가 그대로다', () => {
  const { remote, work } = cloned();
  const head = git(work, ['rev-parse', 'HEAD']).trim();
  fs.writeFileSync(path.join(work, 'wip.txt'), 'mine');
  commit(remote, 'r1');
  run(work);
  assert.strictEqual(git(work, ['rev-parse', 'HEAD']).trim(), head);
  assert.strictEqual(fs.readFileSync(path.join(work, 'wip.txt'), 'utf8'), 'mine');
});

ok('③ 최근에 fetch 했으면 원격을 두드리지 않는다', () => {
  const { remote, work } = cloned();
  fs.writeFileSync(path.join(work, '.git', 'claude-fetch-origin'), ''); // 이 훅이 방금 한 셈
  const before = upstreamSha(work);
  commit(remote, 'r1');
  const out = run(work, { CLAUDE_SESSION_FETCH_MIN_MINUTES: '9999' });
  assert.strictEqual(upstreamSha(work), before, 'skip 이면 ref 가 그대로여야 한다');
  assert.strictEqual(out, '');
});

ok('④ upstream 이 없으면 아무것도 하지 않는다', () => {
  const { remote, work } = cloned();
  git(work, ['checkout', '-q', '-b', 'solo']); // upstream 없는 브랜치
  const before = upstreamSha(work);
  commit(remote, 'r1');
  const out = run(work);
  assert.strictEqual(upstreamSha(work), before);
  assert.strictEqual(out, '');
});

ok('⑤ kill switch 로 끌 수 있다', () => {
  const { remote, work } = cloned();
  const before = upstreamSha(work);
  commit(remote, 'r1');
  const out = run(work, { CLAUDE_SESSION_FETCH_OFF: '1' });
  assert.strictEqual(upstreamSha(work), before);
  assert.strictEqual(out, '');
});

ok('⑥ 원격이 사라져도 조용히 실패한다(exit 0)', () => {
  const { remote, work } = cloned();
  fs.rmSync(remote, { recursive: true, force: true });
  assert.strictEqual(run(work), '');
});

ok('⑦ 갱신은 됐지만 밀림이 없으면 무음', () => {
  const { work } = cloned(); // 원격이 앞서지 않음
  assert.strictEqual(run(work), '');
});

ok('⑧ git repo 가 아니면 무음', () => {
  assert.strictEqual(run(fs.mkdtempSync(path.join(os.tmpdir(), 'sf-nogit-'))), '');
});

ok('⑨ cwd 가 비어 있어도 죽지 않는다', () => {
  const res = require('child_process').spawnSync('node', [FETCH], {
    env: { ...process.env, CLAUDE_SESSION_FETCH_MIN_MINUTES: '0' },
    input: '{}',
  });
  assert.strictEqual(res.status, 0);
});

console.log(`session-fetch.test.js: ${n} tests passed`);
