#!/usr/bin/env node
// settings.json 의 SessionStart 자동 pull 체인 회귀 테스트.
//
// 왜 필요한가: 이 체인은 **자기 자신의 업데이트 배포 경로**다. 따옴표 하나만 어긋나도
// `JSON.parse` 는 통과하고(CI 의 JSON validation 이 보는 전부다) 전 머신이 조용히 업데이트를
// 멈춘다 — 이 훅이 애초에 고치려던 "132커밋 밀렸는데 아무도 몰랐다" 사고의 상위 재현이다.
// 그래서 문자열을 눈으로 읽는 대신 fixture HOME 에 실제로 spawn 해 동작을 고정한다.
// (셸 훅을 fixture repo 로 spawn 하는 방식은 install-hooks.test.js 선례.)
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync, spawnSync } = require('child_process');

for (const k of ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE']) delete process.env[k];

let n = 0;
const ok = (name, fn) => { fn(); n++; };

const COMMAND = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'settings.json'), 'utf8'))
  .hooks.SessionStart[0].hooks[0].command;

function git(dir, args) {
  execFileSync('git', ['-C', dir, ...args], { stdio: 'ignore' });
}

// fixture HOME 에 <home>/.claude 를 만들고, origin 이 1커밋 앞선 상태로 둔다.
// 체인이 `~/.claude` 를 쓰므로 HOME 만 갈아끼우면 실 repo 를 건드리지 않고 검증된다.
function makeHome() {
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

function runChain(home, extraEnv) {
  const r = spawnSync('sh', ['-c', COMMAND], {
    env: { ...process.env, HOME: home, ...extraEnv },
    encoding: 'utf8',
  });
  return { out: (r.stdout || '').trim(), code: r.status };
}
const head = (repo) => execFileSync('git', ['-C', repo, 'rev-parse', 'HEAD']).toString().trim();

ok('① clean + behind → pull 하고 한 줄 알린다', () => {
  const { home, repo } = makeHome();
  const before = head(repo);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.match(out, /updated from origin\/main/);
  assert.notStrictEqual(head(repo), before);
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
  const { home, repo } = makeHome();
  runChain(home);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  void repo;
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
  fs.mkdirSync(path.join(home, '.claude'), { recursive: true });
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

console.log(`session-start-pull.test.js: ${n} tests passed`);
