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
// 스탬프 키는 추적 ref 단위다(브리프와 같은 함수). remote 단위면 다른 브랜치가 굶는다.
const STAMP = 'claude-fetch-refs_remotes_origin_main';
const stampPath = (dir, name) => path.join(dir, '.git', name || STAMP);

ok('① 원격이 앞서면 ref 를 갱신하고 밀림 한 줄을 낸다', () => {
  const { remote, work } = cloned();
  const before = upstreamSha(work);
  commit(remote, 'r1');
  commit(remote, 'r2');
  const out = run(work);
  assert.notStrictEqual(upstreamSha(work), before, 'remote-tracking ref 가 갱신돼야 한다');
  assert.match(out, /2커밋 뒤처짐/);
  assert.match(out, /origin\/main/);
  assert.ok(fs.existsSync(stampPath(work)), 'rate-limit 스탬프를 남긴다');
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
  fs.writeFileSync(stampPath(work), ''); // 이 훅이 방금 한 셈
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

ok('⑩ 사용자의 FETCH_HEAD 를 덮지 않는다', () => {
  // 덮으면, 사용자가 `git fetch origin <다른 브랜치>` 해 둔 상태에서 이어 친 `git merge FETCH_HEAD` 가
  // 엉뚱한 브랜치를 머지한다. 훅이 사용자 workspace 를 만지지 않는다는 계약의 핵심 조각.
  const { remote, work } = cloned();
  git(work, ['fetch', 'origin', 'main']);
  const userHead = fs.readFileSync(path.join(work, '.git', 'FETCH_HEAD'), 'utf8');
  commit(remote, 'r1');
  run(work);
  assert.strictEqual(fs.readFileSync(path.join(work, '.git', 'FETCH_HEAD'), 'utf8'), userHead);
});

ok('⑪ 한 브랜치의 fetch 가 다른 브랜치를 굶기지 않는다', () => {
  // remote 단위 스탬프였을 때: main 세션이 찍은 스탬프 때문에 15분 안의 feat 세션이 skip 되고
  // origin/feat 는 영영 갱신되지 않았다(그리고 브리프의 "fetch 안 함" 경고까지 억제됐다).
  const { remote, work } = cloned();
  git(remote, ['checkout', '-q', '-b', 'feat']);
  commit(remote, 'f1');
  git(remote, ['checkout', '-q', 'main']);
  git(work, ['fetch', '--quiet', 'origin', '+refs/heads/feat:refs/remotes/origin/feat']);
  git(work, ['checkout', '-q', '-b', 'feat', '--track', 'origin/feat']);
  // main 세션이 방금 fetch 한 상태를 만든다 — **main 쪽 스탬프만** 찍는다.
  fs.writeFileSync(stampPath(work), '');
  git(remote, ['checkout', '-q', 'feat']);
  commit(remote, 'f2');
  git(remote, ['checkout', '-q', 'main']);
  const before = git(work, ['rev-parse', 'origin/feat']).trim();
  // 게이트를 최대로 열어 둬도(9999분) feat 는 자기 스탬프가 없으므로 fetch 해야 한다.
  const out = run(work, { CLAUDE_SESSION_FETCH_MIN_MINUTES: '9999' });
  assert.notStrictEqual(git(work, ['rev-parse', 'origin/feat']).trim(), before, 'feat 는 자기 스탬프로 판정한다');
  assert.match(out, /뒤처짐/);
  assert.ok(
    fs.existsSync(stampPath(work, 'claude-fetch-refs_remotes_origin_feat')),
    'feat 스탬프가 따로 생긴다',
  );
});

ok('⑫ 그 repo 의 git 훅을 실행하지 않는다', () => {
  // fetch 는 ref 를 갱신하며 reference-transaction 훅을 부른다. 사용자가 아무 git 명령도 치지 않았는데
  // 남의 repo 훅이 도는 것은 core.fsmonitor 와 같은 문제다.
  const { remote, work } = cloned();
  const marker = path.join(work, 'hook-ran');
  const hook = path.join(work, '.git', 'hooks', 'reference-transaction');
  fs.writeFileSync(hook, `#!/bin/sh\ntouch "${marker.replace(/\\/g, '/')}"\nexit 0\n`);
  fs.chmodSync(hook, 0o755);
  commit(remote, 'r1');
  const before = upstreamSha(work);
  run(work);
  assert.notStrictEqual(upstreamSha(work), before, '전제: ref 는 실제로 갱신된다');
  assert.ok(!fs.existsSync(marker), 'repo 훅은 실행되지 않는다');
});

ok('⑬ 상속된 GIT_COMMON_DIR 이 다른 repo 를 fetch 하게 만들지 않는다', () => {
  const { remote, work } = cloned();
  const other = cloned();
  commit(remote, 'r1');
  const before = upstreamSha(work);
  run(work, { GIT_COMMON_DIR: path.join(other.work, '.git'), GIT_DIR: path.join(other.work, '.git') });
  assert.notStrictEqual(upstreamSha(work), before, '지목된 repo 를 fetch 해야 한다');
  assert.ok(!fs.existsSync(stampPath(other.work)), '무관한 repo 에 스탬프를 남기지 않는다');
});

ok('⑭ 브리프 kill switch 는 출력만 끈다(fetch 는 계속한다)', () => {
  const { remote, work } = cloned();
  commit(remote, 'r1');
  const before = upstreamSha(work);
  const out = run(work, { CLAUDE_BRIEF_CWD_OFF: '1' });
  assert.strictEqual(out, '', 'README 가 즉시 차단 레버로 안내하는 스위치가 이 훅에도 들어야 한다');
  assert.notStrictEqual(upstreamSha(work), before);
});

ok('⑮ 브리프가 감시하는 repo 자신은 건드리지 않는다(pull 훅과 ref 를 다투지 않게)', () => {
  const { remote, work } = cloned();
  commit(remote, 'r1');
  const before = upstreamSha(work);
  const out = run(work, { CLAUDE_BRIEF_REPO: work });
  assert.strictEqual(out, '');
  assert.strictEqual(upstreamSha(work), before, 'fetch 자체를 하지 않는다');
});

ok('⑯ 실패해도 스탬프를 찍어 매 세션 재시도하지 않는다', () => {
  const { remote, work } = cloned();
  fs.rmSync(remote, { recursive: true, force: true });
  assert.strictEqual(run(work), '');
  assert.ok(fs.existsSync(stampPath(work)), '실패에도 backoff 가 있어야 한다');
});

ok('⑰ submodule 을 가진 repo 에서 submodule ref 까지 건드리지 않는다', () => {
  // `fetch.recurseSubmodules` 기본값은 on-demand 라, superproject fetch 가 submodule 포인터를 들여오면
  // git 이 submodule 도 함께 fetch 한다 — "추적 ref 하나만 갱신한다"는 계약이 깨지고, 다른 repo 의 ref 가
  // 사용자 모르게 움직인다. 로컬 경로 submodule 은 protocol.file.allow=always 가 필요하다(git 2.38+).
  const FILE_OK = ['-c', 'protocol.file.allow=always'];
  const subRemote = initRepo('sf-subremote-');
  commit(subRemote, 'sub-base');
  const superRemote = initRepo('sf-superremote-');
  commit(superRemote, 'super-base');
  git(superRemote, [...FILE_OK, 'submodule', 'add', '-q', subRemote, 'sub']);
  git(superRemote, ['commit', '-qm', 'add sub']);

  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'sf-superwork-')) + '/w';
  execFileSync('git', [...FILE_OK, 'clone', '-q', '--recurse-submodules', superRemote, work], { stdio: 'ignore' });
  git(work, ['config', 'user.email', 't@t']);
  git(work, ['config', 'user.name', 't']);

  // 원격 submodule 이 앞서고, superproject 가 그 포인터를 갱신한다(= on-demand 재귀 조건).
  commit(subRemote, 'sub-r1');
  git(superRemote, [...FILE_OK, 'submodule', 'update', '--remote', '-q', 'sub']);
  git(superRemote, ['add', 'sub']);
  git(superRemote, ['commit', '-qm', 'bump sub']);

  const sub = path.join(work, 'sub');
  const subBefore = git(sub, ['rev-parse', 'origin/main']).trim();
  const superBefore = upstreamSha(work);
  run(work);
  assert.notStrictEqual(upstreamSha(work), superBefore, '전제: superproject 는 갱신된다');
  assert.strictEqual(git(sub, ['rev-parse', 'origin/main']).trim(), subBefore, 'submodule ref 는 그대로다');
});

console.log(`session-fetch.test.js: ${n} tests passed`);
