#!/usr/bin/env node
// sync-permissions.js regression test — the canonical rules (permission-rules.json) merge into a
// per-machine settings.json: ask rules plus their rtk twins are added, retired rules and forbidden
// allows are removed, everything else is kept. Fixtures live in a temp dir removed at exit.
'use strict';
const assert = require('assert');
const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const SYNC = path.join(__dirname, 'sync-permissions.js');
const RULES = path.join(__dirname, 'permission-rules.json');
const { rtkTwin } = require(SYNC);
const canonical = JSON.parse(fs.readFileSync(RULES, 'utf8'));

// Hook options are gated on the installed Claude Code version; the children read this instead of `claude --version`.
process.env.SYNC_PERMISSIONS_CLAUDE_VERSION = '2.1.318';
const T = fs.mkdtempSync(path.join(os.tmpdir(), 'sync-perm-'));
process.on('exit', () => fs.rmSync(T, { recursive: true, force: true }));

let pass = 0;
let fail = 0;
function check(name, fn) {
  try { fn(); pass++; } catch (e) { fail++; console.log(`FAIL ${name}: ${e.message}`); }
}
function run(args) {
  const r = spawnSync('node', [SYNC, ...args], { encoding: 'utf8' });
  return { code: r.status, out: r.stdout, err: r.stderr };
}
let n = 0;
function fixture(settings, rules) { // -> { dir, settings, rules } with files written (settings may be undefined = missing)
  const dir = fs.mkdtempSync(path.join(T, `c${n++}-`));
  const s = path.join(dir, 'settings.json');
  if (settings !== undefined) fs.writeFileSync(s, typeof settings === 'string' ? settings : `${JSON.stringify(settings, null, 2)}\n`);
  const r = path.join(dir, 'rules.json');
  fs.writeFileSync(r, `${JSON.stringify(rules || SMALL, null, 2)}\n`);
  return { dir, settings: s, rules: r };
}
const read = (f) => JSON.parse(fs.readFileSync(f, 'utf8'));
const backups = (f) => fs.readdirSync(path.dirname(f)).filter((x) => x.startsWith(`${path.basename(f)}.bak-`));
const sync = (fx, ...extra) => run(['--settings', fx.settings, '--rules', fx.rules, ...extra]);

// A small rules file keeps the behaviour cases independent of the canonical content.
const GUARDS = [
  { event: 'PreToolUse', script: 'guard-push-delete.js', onFailure: 'block', timeout: 10 },
  { event: 'PreToolUse', script: 'guard-worktree-edit.js', onFailure: 'block', timeout: 10 },
];
const SMALL = {
  ask: ['Bash(git push --force*)', 'Bash(gh repo delete*)'],
  retireAsk: ['Bash(git push * :*)'],
  forbidAllow: ['Bash', 'Edit'],
  hookOptions: GUARDS,
};
const SMALL_ASK = ['Bash(git push --force*)', 'Bash(rtk git push --force*)', 'Bash(gh repo delete*)', 'Bash(rtk gh repo delete*)'];

// --- the canonical file ---
check('canonical: ask / retireAsk / forbidAllow are string arrays', () => {
  for (const k of ['ask', 'retireAsk', 'forbidAllow']) {
    assert.ok(Array.isArray(canonical[k]), k);
    assert.ok(canonical[k].every((r) => typeof r === 'string' && r.length > 0), k);
  }
});
check('canonical: every ask rule is a Bash(...) rule in its base form (no rtk prefix), no duplicates', () => {
  assert.ok(canonical.ask.every((r) => /^Bash\(.+\)$/.test(r)));
  assert.ok(canonical.ask.every((r) => !r.startsWith('Bash(rtk ')));
  assert.strictEqual(new Set(canonical.ask).size, canonical.ask.length);
});
check('canonical: rtk twin count equals the base count and no twin reads rtk rtk', () => {
  const twins = canonical.ask.map(rtkTwin).filter(Boolean);
  assert.strictEqual(twins.length, canonical.ask.length);
  assert.ok(twins.every((t) => t.startsWith('Bash(rtk ') && !t.includes('rtk rtk')));
});
check('canonical: no ask rule contains :* (prefix-rule syntax that matches nothing or warns at start)', () => {
  assert.ok(canonical.ask.every((r) => !r.includes(':*')));
  assert.ok(canonical.ask.map(rtkTwin).every((r) => !r.includes(':*')));
});
check('canonical: the audit forms are present, the old colon rule is retired, bare tool allows are forbidden', () => {
  for (const r of ['Bash(git push)', 'Bash(git push --mirror*)', 'Bash(git push * --prune*)', 'Bash(git restore *)',
    'Bash(git switch --discard-changes*)', 'Bash(git branch -M*)', 'Bash(gh pr close * -d*)', 'Bash(gh api --method=DELETE*)',
    'Bash(gh release delete*)', 'Bash(gh issue delete*)', 'Bash(gh repo edit*)', 'Bash(gh auth token*)']) {
    assert.ok(canonical.ask.includes(r), r);
  }
  assert.ok(canonical.retireAsk.includes('Bash(git push * :*)'));
  for (const r of ['Bash', 'Bash(*)', 'Edit', 'Write', 'NotebookEdit']) assert.ok(canonical.forbidAllow.includes(r), r);
  for (const r of ['WebFetch', 'WebSearch']) assert.ok(!canonical.forbidAllow.includes(r), r);
});
check('canonical: hookOptions holds exactly the two PreToolUse guards with onFailure block and timeout 10', () => {
  assert.deepStrictEqual(canonical.hookOptions, GUARDS);
});
check('rtkTwin: Bash(inner) -> Bash(rtk inner); rtk-prefixed and non-Bash rules have no twin', () => {
  assert.strictEqual(rtkTwin('Bash(git push -f*)'), 'Bash(rtk git push -f*)');
  assert.strictEqual(rtkTwin('Bash(rtk git push -f*)'), null);
  assert.strictEqual(rtkTwin('Read(~/.claude/private-terms.txt)'), null);
  assert.strictEqual(rtkTwin('Bash'), null);
});

// --- merging ---
check('missing file: creates {permissions:{ask:[rules + twins]}} with 2-space indent and a trailing newline, no backup', () => {
  const fx = fixture(undefined);
  const r = sync(fx);
  assert.strictEqual(r.code, 0, r.err);
  const text = fs.readFileSync(fx.settings, 'utf8');
  const obj = JSON.parse(text);
  assert.deepStrictEqual(obj, { permissions: { ask: SMALL_ASK } });
  assert.strictEqual(text, `${JSON.stringify(obj, null, 2)}\n`);
  assert.deepStrictEqual(backups(fx.settings), []);
});
check('missing rules are appended after the local ones; other keys, local ask rules and allow rules are kept', () => {
  const fx = fixture({
    model: 'opus',
    permissions: { defaultMode: 'auto', allow: ['Bash(npm test)', 'WebFetch'], ask: ['Bash(rm -rf *)', 'Bash(gh repo delete*)'] },
    hooks: { Stop: [{ hooks: [{ type: 'command', command: 'node x.js' }] }] },
  });
  const r = sync(fx);
  assert.strictEqual(r.code, 0, r.err);
  const obj = read(fx.settings);
  assert.strictEqual(obj.model, 'opus');
  assert.deepStrictEqual(obj.hooks, { Stop: [{ hooks: [{ type: 'command', command: 'node x.js' }] }] });
  assert.deepStrictEqual(Object.keys(obj.permissions), ['defaultMode', 'allow', 'ask']);
  assert.strictEqual(obj.permissions.defaultMode, 'auto');
  assert.deepStrictEqual(obj.permissions.allow, ['Bash(npm test)', 'WebFetch']);
  assert.deepStrictEqual(obj.permissions.ask, ['Bash(rm -rf *)', 'Bash(gh repo delete*)',
    'Bash(git push --force*)', 'Bash(rtk git push --force*)', 'Bash(rtk gh repo delete*)']);
  assert.ok(r.out.includes('Bash(rtk gh repo delete*)'), r.out);
});
check('idempotent: the second run changes nothing and writes no backup', () => {
  const fx = fixture({ permissions: { ask: ['Bash(x)'] } });
  assert.strictEqual(sync(fx).code, 0);
  const once = fs.readFileSync(fx.settings, 'utf8');
  const b1 = backups(fx.settings);
  const r = sync(fx);
  assert.strictEqual(r.code, 0, r.err);
  assert.strictEqual(fs.readFileSync(fx.settings, 'utf8'), once);
  assert.deepStrictEqual(backups(fx.settings), b1);
  assert.strictEqual(sync(fx, '--check').code, 0);
});
check('forbidAllow: those rules leave allow, the rest stay in order', () => {
  const fx = fixture({ permissions: { allow: ['Bash', 'WebFetch', 'Edit', 'Bash(npm *)'], ask: SMALL_ASK } });
  const r = sync(fx);
  assert.strictEqual(r.code, 0, r.err);
  assert.deepStrictEqual(read(fx.settings).permissions.allow, ['WebFetch', 'Bash(npm *)']);
  assert.ok(r.out.includes('Bash') && r.out.includes('Edit'), r.out);
});
check('retireAsk: the rule and its rtk twin leave ask', () => {
  const fx = fixture({ permissions: { ask: ['Bash(git push * :*)', ...SMALL_ASK, 'Bash(rtk git push * :*)'] } });
  const r = sync(fx);
  assert.strictEqual(r.code, 0, r.err);
  assert.deepStrictEqual(read(fx.settings).permissions.ask, SMALL_ASK);
});
check('no allow key: none is created', () => {
  const fx = fixture({ permissions: { ask: [] } });
  assert.strictEqual(sync(fx).code, 0);
  assert.deepStrictEqual(Object.keys(read(fx.settings).permissions), ['ask']);
});
check('permissions without ask: ask is added after the existing keys', () => {
  const fx = fixture({ permissions: { defaultMode: 'auto' } });
  assert.strictEqual(sync(fx).code, 0);
  assert.deepStrictEqual(read(fx.settings).permissions, { defaultMode: 'auto', ask: SMALL_ASK });
});
check('a local ask rule already in rtk form is not duplicated', () => {
  const fx = fixture({ permissions: { ask: ['Bash(rtk gh repo delete*)'] } });
  assert.strictEqual(sync(fx).code, 0);
  const ask = read(fx.settings).permissions.ask;
  assert.strictEqual(ask.filter((r) => r === 'Bash(rtk gh repo delete*)').length, 1);
  assert.strictEqual(ask.length, SMALL_ASK.length);
});

// --- backup, dry-run, check ---
check('backup: the previous content is kept as <path>.bak-<YYYYMMDDTHHMMSS> only when the file changes', () => {
  const before = { permissions: { ask: ['Bash(x)'] } };
  const fx = fixture(before);
  const original = fs.readFileSync(fx.settings, 'utf8');
  const r = sync(fx);
  assert.strictEqual(r.code, 0, r.err);
  const b = backups(fx.settings);
  assert.strictEqual(b.length, 1, JSON.stringify(b));
  assert.match(b[0], /^settings\.json\.bak-\d{8}T\d{6}(\.\d+)?$/);
  assert.strictEqual(fs.readFileSync(path.join(fx.dir, b[0]), 'utf8'), original);
  assert.ok(r.out.includes(b[0]), r.out);
});
check('--dry-run: reports the changes, writes nothing, exit 0', () => {
  const fx = fixture({ permissions: { allow: ['Bash'], ask: ['Bash(git push * :*)'] } });
  const original = fs.readFileSync(fx.settings, 'utf8');
  const r = sync(fx, '--dry-run');
  assert.strictEqual(r.code, 0, r.err);
  assert.strictEqual(fs.readFileSync(fx.settings, 'utf8'), original);
  assert.deepStrictEqual(backups(fx.settings), []);
  assert.ok(r.out.includes('Bash(git push --force*)') && r.out.includes('Bash(git push * :*)') && r.out.includes('Bash'), r.out);
});
check('--check: drift exits 1 and lists rules to add, rules to retire, allows to remove and local-only rules; no write', () => {
  const fx = fixture({ permissions: { allow: ['Edit', 'WebFetch'], ask: ['Bash(rm -rf *)', 'Bash(git push * :*)', 'Bash(gh repo delete*)'] } });
  const original = fs.readFileSync(fx.settings, 'utf8');
  const r = sync(fx, '--check');
  assert.strictEqual(r.code, 1, r.out + r.err);
  assert.strictEqual(fs.readFileSync(fx.settings, 'utf8'), original);
  assert.deepStrictEqual(backups(fx.settings), []);
  const want = ['Bash(git push --force*)', 'Bash(rtk git push --force*)', 'Bash(rtk gh repo delete*)', 'Bash(git push * :*)', 'Edit', 'Bash(rm -rf *)'];
  for (const w of want) assert.ok(r.out.includes(w), `${w} in\n${r.out}`);
  assert.ok(!r.out.includes('WebFetch'), r.out);
});
check('--check: in sync exits 0', () => {
  const fx = fixture({ permissions: { allow: ['WebFetch'], ask: SMALL_ASK } });
  const r = sync(fx, '--check');
  assert.strictEqual(r.code, 0, r.out + r.err);
});
check('--check on a missing file is drift (exit 1) and creates nothing', () => {
  const fx = fixture(undefined);
  assert.strictEqual(sync(fx, '--check').code, 1);
  assert.ok(!fs.existsSync(fx.settings));
});

// --- --keep-allow: removing the bare tool allows is a per-machine decision (bootstrap passes it) ---
check('--keep-allow: forbidden allows stay and ask rules are still added', () => {
  const fx = fixture({ permissions: { allow: ['Bash', 'WebFetch'], ask: [] } });
  const r = sync(fx, '--keep-allow');
  assert.strictEqual(r.code, 0, r.err);
  assert.deepStrictEqual(read(fx.settings).permissions, { allow: ['Bash', 'WebFetch'], ask: SMALL_ASK });
  assert.ok(!r.out.includes('allow rules to remove'), r.out);
});
check('--keep-allow: allow-only drift is in sync (no write, no backup); plain --check still reports it', () => {
  const fx = fixture({ permissions: { allow: ['Bash', 'WebFetch'], ask: SMALL_ASK } });
  const original = fs.readFileSync(fx.settings, 'utf8');
  assert.strictEqual(sync(fx, '--check').code, 1);
  assert.strictEqual(sync(fx, '--check', '--keep-allow').code, 0);
  assert.strictEqual(sync(fx, '--keep-allow').code, 0);
  assert.strictEqual(fs.readFileSync(fx.settings, 'utf8'), original);
  assert.deepStrictEqual(backups(fx.settings), []);
  assert.strictEqual(sync(fx).code, 0);
  assert.deepStrictEqual(read(fx.settings).permissions.allow, ['WebFetch']);
});

// --- hook options: the two guards' onFailure/timeout from the canonical file ---
const H = (command, extra = {}) => ({ type: 'command', command, ...extra });
const PD = 'node ~/.claude/scripts/guard-push-delete.js';
const WE = 'node ~/.claude/scripts/guard-worktree-edit.js';
const SET = { onFailure: 'block', timeout: 10 };
const hooksFx = (hooks, perms = { ask: SMALL_ASK }) => fixture({ permissions: perms, hooks });
check('hook options: unset fields are set on the matched handlers only; other handlers, other events and order are kept', () => {
  const fx = hooksFx({
    PreToolUse: [{ matcher: 'Bash', hooks: [H(PD), H('node ~/.claude/scripts/other.js')] }, { matcher: 'Edit|Write|NotebookEdit', hooks: [H(WE)] }],
    Stop: [{ hooks: [H(PD)] }],
  });
  const r = sync(fx);
  assert.strictEqual(r.code, 0, r.err);
  const h = read(fx.settings).hooks;
  assert.deepStrictEqual(h.PreToolUse[0].hooks, [H(PD, SET), H('node ~/.claude/scripts/other.js')]);
  assert.deepStrictEqual(h.PreToolUse[1].hooks, [H(WE, SET)]);
  assert.deepStrictEqual(h.Stop, [{ hooks: [H(PD)] }]);
  assert.ok(r.out.includes('~ hook options to set (4):'), r.out);
  assert.ok(r.out.includes('PreToolUse guard-push-delete.js onFailure: (unset) -> "block"'), r.out);
  assert.ok(r.out.includes('PreToolUse guard-worktree-edit.js timeout: (unset) -> 10'), r.out);
  assert.ok(!r.out.includes('~/.claude/scripts') && !r.out.includes('hook not registered'), r.out);
  assert.strictEqual(sync(fx, '--check').code, 0);
});
check('hook options: a partial handler gets only the missing field; a string "10" timeout is replaced; same values are in sync', () => {
  const fx = hooksFx({ PreToolUse: [{ matcher: 'Bash', hooks: [H(PD, { onFailure: 'block', timeout: '10' })] }, { matcher: 'Edit', hooks: [H(WE, SET)] }] });
  const r = sync(fx, '--check');
  assert.strictEqual(r.code, 1, r.out);
  assert.ok(r.out.includes('~ hook options to set (1):') && r.out.includes('timeout: "10" -> 10'), r.out);
  assert.strictEqual(sync(fx).code, 0);
  assert.deepStrictEqual(read(fx.settings).hooks.PreToolUse[0].hooks, [H(PD, SET)]);
  const once = fs.readFileSync(fx.settings, 'utf8');
  assert.strictEqual(sync(fx).code, 0);
  assert.strictEqual(fs.readFileSync(fx.settings, 'utf8'), once);
  assert.strictEqual(backups(fx.settings).length, 1);
});
check('hook options: a redirect is not a chain; an empty SYNC_PERMISSIONS_CLAUDE_VERSION falls back to `claude --version`', () => {
  const fx = hooksFx({ PreToolUse: [{ matcher: 'Bash', hooks: [H('node ~/.claude/scripts/guard-push-delete.js 2>&1')] }, { matcher: 'Edit', hooks: [H(WE, SET)] }] });
  const r = spawnSync('node', [SYNC, '--settings', fx.settings, '--rules', fx.rules, '--check'], { encoding: 'utf8', env: { ...process.env, SYNC_PERMISSIONS_CLAUDE_VERSION: '' } });
  assert.ok(!r.stdout.includes('wrapped command'), r.stdout);
  // with `claude` on PATH (2.1.318 here) the handler drifts; without it the options are skipped — both prove the fallback ran
  assert.ok(r.stdout.includes('~ hook options to set (2):') || r.stdout.includes('hook options skipped: Claude Code version unknown'), r.stdout);
});
check('hook options: --keep-allow does not change them', () => {
  const fx = hooksFx({ PreToolUse: [{ matcher: 'Bash', hooks: [H(PD)] }, { matcher: 'Edit', hooks: [H(WE)] }] }, { allow: ['Bash'], ask: SMALL_ASK });
  assert.strictEqual(sync(fx, '--check', '--keep-allow').code, 1);
  assert.strictEqual(sync(fx, '--keep-allow').code, 0);
  const s = read(fx.settings);
  assert.deepStrictEqual(s.permissions.allow, ['Bash']);
  assert.deepStrictEqual(s.hooks.PreToolUse.map((g) => g.hooks[0].onFailure), ['block', 'block']);
});
check('hook options: matching is by exact basename token — exec form args (any element), quoted and backslash paths, twice registered', () => {
  const fx = hooksFx({ PreToolUse: [{ matcher: 'Bash', hooks: [
    { type: 'command', command: 'node', args: ['C:/Users/u/.claude/scripts/guard-push-delete.js', '--x'] },
    H('node "C:/Users/u/.claude/scripts/guard-push-delete.js"'),
    H('node C:\\Users\\u\\.claude\\scripts\\guard-worktree-edit.js 2>/dev/null'),
    H('node ~/.claude/scripts/guard-worktree-edit.js'),
  ] }] });
  const r = sync(fx);
  assert.strictEqual(r.code, 0, r.err);
  const hs = read(fx.settings).hooks.PreToolUse[0].hooks;
  assert.ok(hs.every((h) => h.onFailure === 'block' && h.timeout === 10), JSON.stringify(hs));
  assert.ok(r.out.includes('~ hook options to set (8):'), r.out);
});
check('hook options: a prefix-colliding name, an http handler, another event and a wrapped command are not changed', () => {
  const wrapped = '[ -r x ] && node ~/.claude/scripts/guard-push-delete.js; true';
  const hooks = { PreToolUse: [{ matcher: 'Bash', hooks: [
    H('node ~/.claude/scripts/old-guard-push-delete.js'),
    { type: 'http', url: 'http://localhost/guard-push-delete.js' },
    H(wrapped),
    H('node ~/.claude/scripts/guard-push-delete.js &'),
    H('node ~/.claude/scripts/guard-push-delete.js\ntrue'),
    H('echo $(node ~/.claude/scripts/guard-push-delete.js)'),
  ] }, { matcher: 'Edit', hooks: [H(WE, SET)] }], Stop: [{ hooks: [H(PD)] }] };
  const fx = hooksFx(hooks);
  const r = sync(fx, '--check');
  assert.strictEqual(r.code, 0, r.out);
  assert.deepStrictEqual(read(fx.settings).hooks, hooks);
  assert.ok(r.out.includes('wrapped command') && r.out.includes('guard-push-delete.js'), r.out);
  assert.ok(!r.out.includes('hook options to set'), r.out);
});
check('hook options: a guard that is not registered is reported even when in sync, is not drift, and no hooks key is created', () => {
  const fx = fixture({ permissions: { ask: SMALL_ASK } });
  const r = sync(fx, '--check');
  assert.strictEqual(r.code, 0, r.out);
  assert.ok(r.out.includes('hook not registered: guard-push-delete.js, guard-worktree-edit.js'), r.out);
  assert.ok(r.out.includes('settings.local.json'), r.out);
  const fx2 = fixture(undefined);
  assert.strictEqual(sync(fx2).code, 0);
  assert.deepStrictEqual(Object.keys(read(fx2.settings)), ['permissions']);
  const fx3 = hooksFx({ PreToolUse: [{ matcher: 'Bash', hooks: [H(PD)] }] });
  const r3 = sync(fx3, '--check');
  assert.strictEqual(r3.code, 1);
  assert.ok(r3.out.includes('hook not registered: guard-worktree-edit.js') && !r3.out.includes('registered: guard-push-delete.js'), r3.out);
});
check('hook options: a malformed hooks.PreToolUse is refused (exit 2, no write); other events are not inspected', () => {
  for (const hooks of [[], { PreToolUse: {} }, { PreToolUse: ['x'] }, { PreToolUse: [{ hooks: {} }] }, { PreToolUse: [{ hooks: [1] }] }]) {
    const fx = hooksFx(hooks);
    const original = fs.readFileSync(fx.settings, 'utf8');
    const r = sync(fx);
    assert.strictEqual(r.code, 2, JSON.stringify(hooks) + r.out + r.err);
    assert.ok(r.err.includes('hooks'), r.err);
    assert.strictEqual(fs.readFileSync(fx.settings, 'utf8'), original);
    // the shape is checked before the version gate, so an older Claude Code refuses the same file
    const old = spawnSync('node', [SYNC, '--settings', fx.settings, '--rules', fx.rules], { encoding: 'utf8', env: { ...process.env, SYNC_PERMISSIONS_CLAUDE_VERSION: '2.1.200' } });
    assert.strictEqual(old.status, 2, old.stdout + old.stderr);
    assert.strictEqual(fs.readFileSync(fx.settings, 'utf8'), original);
  }
  const ok = hooksFx({ Stop: 'not an array', PreToolUse: [{ matcher: 'Bash', hooks: [H(PD, SET)] }, { matcher: 'Edit', hooks: [H(WE, SET)] }] });
  assert.strictEqual(sync(ok, '--check').code, 0);
});
check('hook options: a rules file without hookOptions still works; invalid or duplicate entries are refused (exit 2)', () => {
  const { hookOptions, ...noHooks } = SMALL;
  assert.strictEqual(sync(fixture({ permissions: { ask: SMALL_ASK } }, noHooks), '--check').code, 0);
  const bad = [
    [GUARDS[0], GUARDS[0]],
    [{ ...GUARDS[0], onFailure: 'maybe' }],
    [{ ...GUARDS[0], timeout: 0 }], [{ ...GUARDS[0], timeout: -1 }], [{ ...GUARDS[0], timeout: 1.5 }], [{ ...GUARDS[0], timeout: '10' }],
    [{ ...GUARDS[0], script: '' }], [{ ...GUARDS[0], script: 'scripts/guard-push-delete.js' }],
    [{ ...GUARDS[0], event: 7 }], 'x',
  ];
  for (const hookOptions of bad) {
    const fx = fixture({ permissions: { ask: [] } }, { ...SMALL, hookOptions });
    const r = sync(fx);
    assert.strictEqual(r.code, 2, JSON.stringify(hookOptions) + r.err);
    assert.ok(r.err.includes('hookOptions'), r.err);
    assert.deepStrictEqual(read(fx.settings), { permissions: { ask: [] } });
  }
});

check('hook options: an older or unknown Claude Code version skips them with a note and no change', () => {
  for (const [ver, note] of [['2.1.294 (Claude Code)', 'older than 2.1.295'], ['garbage', 'version unknown']]) {
    const fx = hooksFx({ PreToolUse: [{ matcher: 'Bash', hooks: [H(PD)] }, { matcher: 'Edit', hooks: [H(WE)] }] });
    const original = fs.readFileSync(fx.settings, 'utf8');
    const r = spawnSync('node', [SYNC, '--settings', fx.settings, '--rules', fx.rules, '--check'], { encoding: 'utf8', env: { ...process.env, SYNC_PERMISSIONS_CLAUDE_VERSION: ver } });
    assert.strictEqual(r.status, 0, r.stdout + r.stderr);
    assert.ok(r.stdout.includes('hook options skipped') && r.stdout.includes(note), r.stdout);
    assert.ok(!r.stdout.includes('hook not registered'), r.stdout);
    assert.strictEqual(fs.readFileSync(fx.settings, 'utf8'), original);
  }
});

// --- errors: never write ---
check('rules file whose retireAsk overlaps ask (directly or through a twin) is refused (exit 2)', () => {
  for (const bad of [{ ...SMALL, retireAsk: ['Bash(gh repo delete*)'] }, { ...SMALL, retireAsk: ['Bash(rtk gh repo delete*)'] }]) {
    const fx = fixture({ permissions: { ask: [] } }, bad);
    const r = sync(fx);
    assert.strictEqual(r.code, 2, JSON.stringify(bad));
    assert.ok(r.err.includes('retireAsk'), r.err);
    assert.deepStrictEqual(read(fx.settings), { permissions: { ask: [] } });
  }
});
for (const [label, content] of [['invalid JSON', '{ "permissions": { "ask": [ '], ['empty file', ''], ['a JSON array', '[]']]) {
  check(`${label}: exit 2, no write, no backup`, () => {
    const fx = fixture(content);
    const r = sync(fx);
    assert.strictEqual(r.code, 2, r.out + r.err);
    assert.strictEqual(fs.readFileSync(fx.settings, 'utf8'), content);
    assert.deepStrictEqual(backups(fx.settings), []);
    assert.ok(r.err.includes(fx.settings), r.err);
  });
}
check('permissions.ask that is not an array: exit 2, no write', () => {
  const fx = fixture({ permissions: { ask: 'Bash(x)' } });
  const original = fs.readFileSync(fx.settings, 'utf8');
  assert.strictEqual(sync(fx).code, 2);
  assert.strictEqual(fs.readFileSync(fx.settings, 'utf8'), original);
});
check('unreadable rules file: exit 2, settings untouched', () => {
  const fx = fixture({ permissions: { ask: [] } });
  fs.writeFileSync(fx.rules, '{');
  const original = fs.readFileSync(fx.settings, 'utf8');
  assert.strictEqual(sync(fx).code, 2);
  assert.strictEqual(fs.readFileSync(fx.settings, 'utf8'), original);
});
check('rules file whose ask holds an rtk form or a :* rule is refused (exit 2)', () => {
  for (const bad of [{ ...SMALL, ask: ['Bash(rtk git push -f*)'] }, { ...SMALL, ask: ['Bash(git push * :*)'] }]) {
    const fx = fixture({ permissions: { ask: [] } }, bad);
    assert.strictEqual(sync(fx).code, 2, JSON.stringify(bad));
    assert.deepStrictEqual(read(fx.settings), { permissions: { ask: [] } });
  }
});
check('unknown argument: exit 2 with usage', () => {
  const r = run(['--bogus']);
  assert.strictEqual(r.code, 2);
  assert.ok(r.err.includes('--settings'), r.err);
});

// --- symlink: written in place ---
check('a symlinked settings.json is written through the link; the link stays a link', () => {
  const fx = fixture({ permissions: { ask: [] } });
  const real = path.join(fx.dir, 'real', 'settings.json');
  fs.mkdirSync(path.dirname(real));
  fs.renameSync(fx.settings, real);
  fs.symlinkSync(real, fx.settings);
  const r = sync(fx);
  assert.strictEqual(r.code, 0, r.err);
  assert.ok(fs.lstatSync(fx.settings).isSymbolicLink());
  assert.deepStrictEqual(read(real).permissions.ask, SMALL_ASK);
});

// --- the canonical file through the real merge ---
check('canonical merge from an empty file yields twice the base count, every rule with its twin, idempotent', () => {
  const dir = fs.mkdtempSync(path.join(T, 'canon-'));
  const s = path.join(dir, 'settings.json');
  const r = run(['--settings', s]);
  assert.strictEqual(r.code, 0, r.err);
  const ask = read(s).permissions.ask;
  assert.strictEqual(ask.length, canonical.ask.length * 2);
  for (const b of canonical.ask) assert.ok(ask.includes(b) && ask.includes(rtkTwin(b)), b);
  assert.strictEqual(new Set(ask).size, ask.length);
  assert.strictEqual(run(['--settings', s, '--check']).code, 0);
});

const total = pass + fail;
console.log(fail ? `${fail}/${total} failed` : `${total}/${total} passed`);
process.exit(fail ? 1 : 0);
