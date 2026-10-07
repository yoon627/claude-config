#!/usr/bin/env node
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const STATUS = path.join(ROOT, 'statusline.js');
const SUB = path.join(ROOT, 'subagent-statusline.js');

let n = 0;
const ok = (name, fn) => { fn(); n++; };

// 가짜 HOME: 실행이 실제 홈 디렉토리의 파일을 읽거나 쓰지 않게.
const HOME = fs.mkdtempSync(path.join(os.tmpdir(), 'statusline-test-'));

function run(script, input, env = {}) {
  const r = spawnSync(process.execPath, [script], {
    input: typeof input === 'string' ? input : JSON.stringify(input),
    env: { ...process.env, HOME, USERPROFILE: HOME, ...env },
    encoding: 'utf8',
    timeout: 10000,
  });
  assert.strictEqual(r.status, 0, r.stderr);
  return r.stdout;
}
const rows = (input) => run(SUB, input).trim().split('\n').filter(Boolean).map((l) => JSON.parse(l));
// 테스트 쪽 폭 계산: 한글 음절과 ✅ 는 2칸(이 테스트가 쓰는 문자 범위만).
const width = (s) => Array.from(s).reduce((w, ch) => w + (/[가-힣✅]/.test(ch) ? 2 : 1), 0);

ok('null·빈·깨진 stdin 에서 두 스크립트 모두 exit 0', () => {
  for (const script of [STATUS, SUB]) {
    for (const input of ['null', '', '{nope', '[]', '{"rate_limits":5}', '{"rate_limits":{"five_hour":null,"seven_day":"x"}}',
      '{"model":{"display_name":{"toString":1}},"rate_limits":{"seven_day":{"used_percentage":{"toString":1}}}}']) run(script, input);
  }
});

ok('subagent: 문자열 id 를 가진 task 마다 {id, content} 한 줄 — 없는 조각은 뺀다', () => {
  const now = Date.now();
  const tasks = [
    { id: 't1', name: 'code-reviewer', description: 'Review\nchange', status: 'running',
      startTime: now - 192100, tokenCount: 48200, contextWindowSize: 200000 },
    { id: 't2', name: 'x', description: ' \n ', status: 'completed', startTime: now - 60000, tokenCount: 999 },
    { id: 't3', name: 'over', tokenCount: 300000, contextWindowSize: 200000, startTime: 0 },
    { id: 't4', description: 'no name', status: 'running', startTime: now + 60000 },
    { id: 7, name: 'numeric-id' },
    { name: 'no-id', status: 'running' },
  ];
  const got = rows({ columns: 200, tasks });
  assert.deepStrictEqual(got.map((r) => r.id), ['t1', 't2', 't3', 't4']);
  assert.match(got[0].content, /^code-reviewer · Review change · running · 48\.2k tok \(24%\) · 3m 1[23]s$/);
  assert.strictEqual(got[1].content, 'x · completed · 999 tok'); // 끝난 task 는 경과를 붙이지 않는다
  assert.strictEqual(got[2].content, 'over · 300.0k tok (100%)');
  assert.strictEqual(got[3].content, 'no name · running');
  assert.deepStrictEqual(rows({ columns: 0, tasks }), []); // 폭이 없으면 기본 표시에 맡긴다
});

ok('subagent: columns 를 넘으면 description 부터 줄인다 — 한글은 2칸으로 센다', () => {
  const now = Date.now();
  for (const description of ['Review the whole change set in detail please', '변경 전체를 아주 자세히 검토해 주세요', '✅'.repeat(20)]) {
    const [row] = rows({ columns: 60, tasks: [{ id: 't1', name: 'code-reviewer', description, status: 'running',
      startTime: now - 192100, tokenCount: 48200 }] });
    assert.ok(width(row.content) <= 60, `${width(row.content)}: ${row.content}`);
    assert.ok(row.content.startsWith('code-reviewer · ') && /… · running · 48\.2k tok · 3m 1[23]s$/.test(row.content), row.content);
  }
});

// 쿼터 조각: TZ 를 고정해 리셋 시각 표기를 결정적으로 본다.
const at2030 = Date.UTC(2026, 0, 1, 20, 30) / 1000;
const runStatus = (input, home = HOME) => run(STATUS, input, { HOME: home, USERPROFILE: home, TZ: 'UTC' });

ok('claude 쿼터: 남은 % 와 리셋 시각, 둘 중 하나만 있으면 그것만', () => {
  const model = { display_name: 'Opus' };
  assert.ok(runStatus({ model, rate_limits: { five_hour: { used_percentage: 47.4, resets_at: at2030 } } }).includes('Opus 53%(20:30)'));
  assert.ok(runStatus({ model, rate_limits: { five_hour: { used_percentage: 110 } } }).includes('Opus 0%'));
  assert.ok(runStatus({ rate_limits: { five_hour: { resets_at: at2030 } } }).includes('claude (20:30)'));
  assert.ok(!runStatus({ model, rate_limits: { five_hour: {} } }).includes('Opus'));
});

ok('claude 주간 쿼터: 5시간 조각 뒤에 wk 남은 % 만(리셋 시각 없이), 5시간 창이 없어도 레이블은 붙인다', () => {
  const model = { display_name: 'Opus' };
  const seven_day = { used_percentage: 28, resets_at: at2030 };
  assert.strictEqual(runStatus({ model, rate_limits: { five_hour: { used_percentage: 47.4, resets_at: at2030 }, seven_day } }),
    'Opus 53%(20:30) wk 72%');
  assert.strictEqual(runStatus({ model, rate_limits: { seven_day } }), 'Opus wk 72%');
  assert.strictEqual(runStatus({ model, rate_limits: { seven_day: { resets_at: at2030 } } }), '');
  // 숫자가 아닌 값은 없는 것으로 본다 — 그 창만 빠지고 다른 창은 남는다.
  assert.strictEqual(runStatus({ model, rate_limits: { five_hour: { used_percentage: 47.4, resets_at: at2030 },
    seven_day: { used_percentage: { toString: 1 }, resets_at: '2026-01-03' } } }), 'Opus 53%(20:30)');
});

ok('codex 쿼터 캐시가 남아 있어도 codex 조각을 그리지 않고 refresh 도 띄우지 않는다', () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'statusline-codex-'));
  try {
    const cache = path.join(home, '.claude', 'cache');
    fs.mkdirSync(cache, { recursive: true });
    fs.writeFileSync(path.join(cache, 'codex-quota.json'), JSON.stringify({ fetchedAt: 0,
      primary: { usedPercent: 20, resetsAt: at2030 }, secondary: { usedPercent: 79, resetsAt: at2030 } }));
    assert.strictEqual(runStatus({}, home), '');
    assert.deepStrictEqual(fs.readdirSync(cache), ['codex-quota.json']);
  } finally {
    fs.rmSync(home, { recursive: true, force: true });
  }
});

// 상태줄은 갱신마다 새로 뜨므로 git 을 띄우면 프로세스가 갱신 수만큼 곱해진다 — GIT_TRACE 파일이 생기면 git 이 실행된 것.
ok('git branch·worktree 표시를 git 프로세스 없이 만든다', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'statusline-git-'));
  // 상위 git 환경(hook·rebase -x 안의 실행)이 fixture 명령을 실제 repo 로 돌리지 않게 지운다.
  const env = { ...process.env, HOME, USERPROFILE: HOME };
  for (const k of ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR']) delete env[k];
  try {
    const git = (cwd, ...args) => {
      const r = spawnSync('git', ['-c', 'user.name=t', '-c', 'user.email=t@t', '-c', 'commit.gpgsign=false',
        '-c', 'init.defaultRefFormat=files', ...args], { cwd, env, encoding: 'utf8', timeout: 10000 });
      assert.strictEqual(r.status, 0, r.stderr);
    };
    const repo = path.join(tmp, 'repo');
    fs.mkdirSync(path.join(repo, 'sub'), { recursive: true });
    git(repo, 'init', '-q', '-b', 'feat/x');
    git(repo, 'commit', '-q', '--allow-empty', '-m', 'i');
    const wt = path.join(tmp, 'wt-name');
    git(repo, 'worktree', 'add', '-q', '-b', 'wt-branch', wt);
    const unborn = path.join(tmp, 'unborn');
    fs.mkdirSync(unborn);
    git(unborn, 'init', '-q', '-b', 'fresh');

    const trace = path.join(tmp, 'git-trace.log');
    // 양성 대조: git 이 trace 파일을 못 열면 tracing 만 끄고 계속 돌아 아래 단언이 공허해진다.
    spawnSync('git', ['version'], { env: { ...env, GIT_TRACE: trace }, timeout: 10000 });
    assert.ok(fs.existsSync(trace), 'GIT_TRACE 가 파일을 쓰지 않아 git 실행을 감지할 수 없다');
    fs.rmSync(trace);
    const show = (cwd) => {
      const r = spawnSync(process.execPath, [STATUS], {
        input: JSON.stringify({ workspace: { current_dir: cwd } }),
        env: { ...env, GIT_TRACE: trace }, encoding: 'utf8', timeout: 10000,
      });
      assert.strictEqual(r.status, 0, r.stderr);
      assert.ok(!fs.existsSync(trace), 'statusline 이 git 을 실행했다');
      return r.stdout;
    };
    assert.strictEqual(show(repo), 'feat/x');
    assert.strictEqual(show(path.join(repo, 'sub')), 'feat/x');
    assert.strictEqual(show(wt), 'wt-branch @wt:wt-name');
    assert.strictEqual(show(tmp), ''); // repo 밖
    assert.strictEqual(show(unborn), 'fresh'); // 커밋 전 branch 도 보인다
    fs.writeFileSync(path.join(repo, '.git', 'HEAD'), 'ref: refs/heads/a\x1b]0;x\x07b\n');
    assert.strictEqual(show(repo), ''); // 터미널 제어문자가 든 ref 는 출력하지 않는다
    fs.writeFileSync(path.join(repo, '.git', 'HEAD'), 'ref: refs/heads/feat/x\n');
    git(repo, 'checkout', '-q', '--detach');
    assert.strictEqual(show(repo), ''); // detached HEAD 는 뺀다
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

// input 이 null 이면 stdin 의 쓰기 끝을 열어 둔다 — 하니스가 셸만 끝내고 stdin 을 닫지 않은 상황.
// cwd 는 git repo 가 아닌 HOME — 정상 경로의 경과에 .git 탐색 I/O 가 섞이지 않게.
function runTimed(script, input) {
  return new Promise((resolve) => {
    const start = performance.now();
    const child = spawn(process.execPath, [script], { cwd: HOME, env: { ...process.env, HOME, USERPROFILE: HOME } });
    let out = '';
    let exit;
    child.stdout.on('data', (d) => { out += d; });
    if (input != null) child.stdin.end(input);
    const cap = setTimeout(() => child.kill(), 15000);
    child.on('exit', (code, signal) => {
      exit = { code, signal, ms: Math.round(performance.now() - start) };
      clearTimeout(cap);
      child.stdin.destroy();
    });
    child.on('close', () => resolve({ script: path.basename(script), ...exit, out }));
  });
}
const report = (r) => `${r.script}: code=${r.code} signal=${r.signal} ms=${r.ms} out=${JSON.stringify(r.out)}`;

Promise.all([STATUS, SUB].flatMap((s) => [runTimed(s, null), runTimed(s, '{}')])).then((results) => {
  for (const [open, closed] of [results.slice(0, 2), results.slice(2, 4)]) {
    assert.ok(open.code === 0 && open.out === '' && open.ms >= 3000 && open.ms < 15000,
      `닫히지 않는 stdin 이면 3초 시한에 출력 없이 exit 0 — ${report(open)}`);
    assert.ok(closed.code === 0 && closed.ms < 3000, `stdin 이 닫히면 시한을 기다리지 않고 끝난다 — ${report(closed)}`);
  }
  n++;
  fs.rmSync(HOME, { recursive: true, force: true });
  console.log(`statusline.test.js: ${n} tests passed`);
}).catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
