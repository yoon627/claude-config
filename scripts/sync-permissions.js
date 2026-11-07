#!/usr/bin/env node
// sync-permissions.js — merge the canonical permission rules (scripts/permission-rules.json) into the
// untracked per-machine ~/.claude/settings.json (README "settings.json" > permissions.ask).
//
//   node scripts/sync-permissions.js [--settings <path>] [--rules <path>] [--check | --dry-run] [--keep-allow]
//
// permissions.ask ends up holding every canonical `ask` rule and its `Bash(rtk …)` twin — the rtk
// PreToolUse hook rewrites git/gh commands and permission rules are matched against the rewritten
// command (wiki rtk-rewrite-permission-rules) — minus the `retireAsk` rules and their twins;
// permissions.allow loses the `forbidAllow` rules unless --keep-allow (bootstrap passes it: removing
// the bare tool allows is a per-machine decision, README permissions.ask). Other keys, rules this
// file does not know and their order are kept, so a second run changes nothing. A missing file
// becomes {"permissions":{"ask":[…]}}; JSON that cannot be parsed is never written (exit 2). The
// new content goes to a temp file beside the real file and is renamed over it, so a symlink keeps
// pointing where it did; the previous content is kept as <path>.bak-<YYYYMMDDTHHMMSS> whenever
// something changes. Formatting-only differences are not drift: the file is rewritten only when a
// rule changes.
//
// `hookOptions` entries ({event, script, onFailure, timeout}) set those two fields on every
// hooks.<event> handler of type "command" whose command string or exec-form args names that script
// (exact basename token). onFailure needs Claude Code 2.1.295+, and an older CLI may drop the unknown
// key or reject the file, so the hook options are applied only when `claude --version` (or
// SYNC_PERMISSIONS_CLAUDE_VERSION) is at least that; otherwise they are skipped with a note. A guard
// script that is not registered at all is reported but is not drift (registering is the README install
// step), and a handler whose command chains with ; && || | is left alone (a `; true` tail swallows the
// failure the option is meant to catch).
//
// Exit codes: 0 in sync or written · 1 drift (--check only) · 2 error (unreadable JSON or rules,
// bad arguments, write failure, anything unexpected).
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const RULES_DEFAULT = path.join(__dirname, 'permission-rules.json');
const SETTINGS_DEFAULT = path.join(os.homedir(), '.claude', 'settings.json');
const USAGE = 'usage: node scripts/sync-permissions.js [--settings <path>] [--rules <path>] [--check | --dry-run] [--keep-allow]';
const HOOK_MIN_VERSION = [2, 1, 295];
const HOOK_FIELDS = ['onFailure', 'timeout'];

class Failure extends Error {}

const isObject = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

// rtkTwin('Bash(git push -f*)') -> 'Bash(rtk git push -f*)'; null for rtk-prefixed or non-Bash rules.
function rtkTwin(rule) {
  const m = /^Bash\((.*)\)$/s.exec(rule);
  if (!m || m[1].startsWith('rtk ')) return null;
  return `Bash(rtk ${m[1]})`;
}

function withTwins(rules) {
  const out = [];
  for (const r of rules) {
    out.push(r);
    const t = rtkTwin(r);
    if (t) out.push(t);
  }
  return [...new Set(out)];
}

function loadRules(file) {
  let rules;
  try {
    rules = JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (e) {
    throw new Failure(`rules file unreadable: ${file} (${e.message})`);
  }
  if (!isObject(rules)) throw new Failure(`rules file is not a JSON object: ${file}`);
  for (const k of ['ask', 'retireAsk', 'forbidAllow']) {
    if (!Array.isArray(rules[k]) || !rules[k].every((r) => typeof r === 'string' && r.length > 0)) {
      throw new Failure(`rules file: "${k}" must be an array of strings: ${file}`);
    }
  }
  // Twins are generated, and :* is prefix-rule syntax (README guard-push-delete.js) — refuse both.
  for (const r of rules.ask) {
    if (!rtkTwin(r)) throw new Failure(`rules file: ask rule must be Bash(...) in its base form, not "${r}"`);
    if (r.includes(':*')) throw new Failure(`rules file: ask rule must not contain ":*": "${r}"`);
  }
  // A rule that is both added and retired would be removed and re-added on every run.
  const asked = new Set(withTwins(rules.ask));
  for (const r of withTwins(rules.retireAsk)) {
    if (asked.has(r)) throw new Failure(`rules file: "${r}" is in both ask and retireAsk (twins included)`);
  }
  if (rules.hookOptions === undefined) rules.hookOptions = [];
  if (!Array.isArray(rules.hookOptions)) throw new Failure(`rules file: "hookOptions" must be an array: ${file}`);
  const seen = new Set();
  for (const h of rules.hookOptions) {
    const bad = (why) => new Failure(`rules file: hookOptions entry ${JSON.stringify(h)} ${why}`);
    if (!isObject(h)) throw bad('is not an object');
    if (typeof h.event !== 'string' || !h.event) throw bad('needs a string "event"');
    if (typeof h.script !== 'string' || !/^[^\\/\s]+$/.test(h.script)) throw bad('needs a bare script file name in "script"');
    if (h.onFailure !== 'continue' && h.onFailure !== 'block') throw bad('needs "onFailure" of "continue" or "block"');
    if (!Number.isInteger(h.timeout) || h.timeout <= 0) throw bad('needs a positive integer "timeout" (seconds)');
    // Two entries for one handler would make every run rewrite the file.
    const key = `${h.event}\t${h.script}`;
    if (seen.has(key)) throw bad('names the same event and script twice');
    seen.add(key);
  }
  return rules;
}

// claudeVersion -> [major, minor, patch] from SYNC_PERMISSIONS_CLAUDE_VERSION (an override — it wins
// when set and non-empty) or `claude --version`, or null when neither gives a version. On Windows an
// npm install is only a claude.cmd shim, which spawnSync finds only through the shell.
function claudeVersion() {
  let text = process.env.SYNC_PERMISSIONS_CLAUDE_VERSION;
  if (!text) {
    // One constant command string under the shell: args plus shell:true is deprecated (DEP0190).
    const r = process.platform === 'win32'
      ? require('child_process').spawnSync('claude --version', { encoding: 'utf8', timeout: 5000, windowsHide: true, shell: true })
      : require('child_process').spawnSync('claude', ['--version'], { encoding: 'utf8', timeout: 5000, windowsHide: true });
    text = r.status === 0 ? r.stdout : '';
  }
  const m = /(\d+)\.(\d+)\.(\d+)/.exec(text || '');
  return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
}
const versionAtLeast = (v, min) => v !== null && (v[0] - min[0] || v[1] - min[1] || v[2] - min[2]) >= 0;

// handlerNames(handler, script): true when a command-type handler runs that script — the last
// path segment of a token of `command` (split on whitespace and the shell operators ; & |, quotes
// stripped), or of any `args` element, equals the script name. Only type "command" is looked at.
function handlerNames(h, script) {
  if (h.type !== 'command') return false;
  const tokens = [];
  if (typeof h.command === 'string') tokens.push(...h.command.split(/[\s;&|]+/));
  if (Array.isArray(h.args)) tokens.push(...h.args.filter((a) => typeof a === 'string'));
  return tokens.some((tok) => tok.replace(/^["']|["']$/g, '').split(/[\\/]/).pop() === script);
}
// A redirect such as 2>&1 is not a chain, so its & is removed before the test.
const isChained = (h) => typeof h.command === 'string' && /[;&|\n`]|\$\(/.test(h.command.replace(/\d*>&\d/g, ''));

// hookPlan(settings, rules, version) -> { hooks (next value or undefined), set, wrapped, missing, skipped }
function hookPlan(settings, rules, version) {
  const out = { hooks: undefined, set: [], wrapped: [], missing: [], skipped: null };
  if (rules.hookOptions.length === 0) return out;
  // The version gate only marks the result skipped; the walk below still validates the shape, so a
  // malformed file is refused the same way on every machine.
  if (!versionAtLeast(version, HOOK_MIN_VERSION)) {
    out.skipped = version ? `Claude Code ${version.join('.')} is older than ${HOOK_MIN_VERSION.join('.')}` : 'Claude Code version unknown (claude --version failed; set SYNC_PERMISSIONS_CLAUDE_VERSION)';
  }
  const hooks = settings.hooks;
  if (hooks !== undefined && !isObject(hooks)) throw new Failure('"hooks" is not a JSON object — nothing written');
  const next = hooks === undefined ? undefined : JSON.parse(JSON.stringify(hooks));
  for (const want of rules.hookOptions) {
    const groups = next === undefined ? undefined : next[want.event];
    if (groups !== undefined && !Array.isArray(groups)) throw new Failure(`"hooks.${want.event}" is not an array — nothing written`);
    let found = 0;
    for (const g of groups || []) {
      if (!isObject(g) || (g.hooks !== undefined && !Array.isArray(g.hooks))) throw new Failure(`"hooks.${want.event}" has a malformed group — nothing written`);
      for (const h of g.hooks || []) {
        if (!isObject(h)) throw new Failure(`"hooks.${want.event}" has a malformed handler — nothing written`);
        if (!handlerNames(h, want.script)) continue;
        found++;
        if (isChained(h)) { out.wrapped.push(`${want.event} ${want.script}`); continue; }
        for (const f of HOOK_FIELDS) {
          if (h[f] === want[f]) continue;
          out.set.push(`${want.event} ${want.script} ${f}: ${h[f] === undefined ? '(unset)' : JSON.stringify(h[f])} -> ${JSON.stringify(want[f])}`);
          h[f] = want[f];
        }
      }
    }
    if (found === 0) out.missing.push(want.script);
  }
  if (out.skipped) return { ...out, hooks: undefined, set: [], wrapped: [], missing: [] };
  out.hooks = next;
  return out;
}

// readSettings -> { exists, settings }; a missing file is an empty object, anything else must be a
// JSON object.
function readSettings(file) {
  let text;
  try {
    text = fs.readFileSync(file, 'utf8');
  } catch (e) {
    if (e.code === 'ENOENT') return { exists: false, settings: {} };
    throw new Failure(`cannot read ${file}: ${e.message}`);
  }
  let settings;
  try {
    settings = JSON.parse(text);
  } catch (e) {
    throw new Failure(`${file}: not valid JSON (${e.message}) — nothing written`);
  }
  if (!isObject(settings)) throw new Failure(`${file}: top level is not a JSON object — nothing written`);
  return { exists: true, settings };
}

// plan(settings, rules, { keepAllow, claudeVersion }) -> { next, addAsk, retireAsk, removeAllow, localOnly, hook, drift }
function plan(settings, rules, opts = {}) {
  const perms = settings.permissions === undefined ? {} : settings.permissions;
  if (!isObject(perms)) throw new Failure('"permissions" is not a JSON object — nothing written');
  for (const k of ['ask', 'allow']) {
    if (perms[k] !== undefined && !Array.isArray(perms[k])) throw new Failure(`"permissions.${k}" is not an array — nothing written`);
  }
  const wantAsk = withTwins(rules.ask);
  const wantSet = new Set(wantAsk);
  const retire = new Set(withTwins(rules.retireAsk));
  const forbid = new Set(rules.forbidAllow);

  const localAsk = perms.ask || [];
  const keptAsk = localAsk.filter((r) => !retire.has(r));
  const retireAsk = localAsk.filter((r) => retire.has(r));
  const have = new Set(keptAsk);
  const addAsk = wantAsk.filter((r) => !have.has(r));
  const localOnly = keptAsk.filter((r) => typeof r === 'string' && !wantSet.has(r));

  const next = JSON.parse(JSON.stringify(settings));
  next.permissions = { ...perms, ask: [...keptAsk, ...addAsk] };
  let removeAllow = [];
  if (!opts.keepAllow && Array.isArray(perms.allow)) {
    removeAllow = perms.allow.filter((r) => forbid.has(r));
    next.permissions.allow = perms.allow.filter((r) => !forbid.has(r));
  }
  const hook = hookPlan(settings, rules, opts.claudeVersion === undefined ? null : opts.claudeVersion);
  if (hook.hooks !== undefined) next.hooks = hook.hooks;
  const drift = addAsk.length + retireAsk.length + removeAllow.length + hook.set.length > 0;
  return { next, addAsk, retireAsk, removeAllow, localOnly, hook, drift };
}

// hookNotes(p) -> lines about hook options that are not drift (printed in sync or not)
function hookNotes(p) {
  const lines = [];
  if (p.hook.skipped) lines.push(`hook options skipped: ${p.hook.skipped}`);
  for (const w of p.hook.wrapped) lines.push(`wrapped command — set by hand: ${w}`);
  if (p.hook.missing.length) lines.push(`hook not registered: ${p.hook.missing.join(', ')} — register them in settings.json hooks (README guard-push-delete.js); settings.local.json and project settings are not read`);
  return lines;
}

function report(file, p, exists) {
  const list = (title, items) => {
    if (items.length === 0) return;
    console.log(`  ${title} (${items.length}):`);
    for (const r of items) console.log(`    ${r}`);
  };
  console.log(`sync-permissions: ${file}${exists ? '' : ' (missing — will be created)'}`);
  list('+ ask rules to add', p.addAsk);
  list('- ask rules to retire', p.retireAsk);
  list('- allow rules to remove', p.removeAllow);
  list('~ hook options to set', p.hook.set);
  list('local-only ask rules (not in the canonical file, kept)', p.localOnly);
  for (const l of hookNotes(p)) console.log(`  ${l}`);
}

function stamp() {
  return new Date().toISOString().replace(/[-:]/g, '').slice(0, 15); // YYYYMMDDTHHMMSS (UTC)
}

function backupPath(file) {
  const base = `${file}.bak-${stamp()}`;
  let candidate = base;
  for (let i = 1; fs.existsSync(candidate); i++) candidate = `${base}.${i}`;
  return candidate;
}

// writeInPlace — the new content is written beside the real file and renamed over it: the rename
// is atomic on one filesystem, and a symlink at `file` keeps pointing at that real file. The
// file's mode is kept; a new file gets the default mode.
function writeInPlace(file, exists, out) {
  let target;
  if (exists) {
    target = fs.realpathSync(file);
  } else {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    target = path.join(fs.realpathSync(path.dirname(file)), path.basename(file));
  }
  const tmp = path.join(path.dirname(target), `.${path.basename(target)}.sync-${process.pid}`);
  try {
    fs.writeFileSync(tmp, out, { mode: 0o600 }); // settings can hold env secrets — never readable while in flight
    if (exists) fs.chmodSync(tmp, fs.statSync(target).mode & 0o7777);
    fs.renameSync(tmp, target);
  } finally {
    fs.rmSync(tmp, { force: true });
  }
}

function parseArgs(argv) {
  const opts = { settings: SETTINGS_DEFAULT, rules: RULES_DEFAULT, check: false, dryRun: false, keepAllow: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const [flag, inline] = a.includes('=') ? [a.slice(0, a.indexOf('=')), a.slice(a.indexOf('=') + 1)] : [a, undefined];
    const value = () => {
      if (inline !== undefined) return inline;
      if (i + 1 >= argv.length) throw new Failure(`${flag} needs a path\n${USAGE}`);
      return argv[++i];
    };
    if (flag === '--settings') opts.settings = value();
    else if (flag === '--rules') opts.rules = value();
    else if (a === '--check') opts.check = true;
    else if (a === '--dry-run') opts.dryRun = true;
    else if (a === '--keep-allow') opts.keepAllow = true;
    else if (a === '-h' || a === '--help') { console.log(USAGE); process.exit(0); }
    else throw new Failure(`unknown argument: ${a}\n${USAGE}`);
  }
  return opts;
}

function main(argv) {
  const opts = parseArgs(argv);
  const rules = loadRules(opts.rules);
  const { exists, settings } = readSettings(opts.settings);
  const p = plan(settings, rules, { keepAllow: opts.keepAllow, claudeVersion: rules.hookOptions.length ? claudeVersion() : null });
  if (!p.drift) {
    console.log(`sync-permissions: ${opts.settings} in sync`);
    for (const l of hookNotes(p)) console.log(`  ${l}`);
    return 0;
  }
  report(opts.settings, p, exists);
  if (opts.check) { console.log(`drift: run node scripts/sync-permissions.js${opts.keepAllow ? ' --keep-allow' : ''} to apply`); return 1; }
  if (opts.dryRun) { console.log('dry-run: nothing written'); return 0; }
  const out = `${JSON.stringify(p.next, null, 2)}\n`;
  try {
    let backup = null;
    if (exists) {
      backup = backupPath(opts.settings);
      fs.copyFileSync(opts.settings, backup);
    }
    writeInPlace(opts.settings, exists, out);
    console.log(`wrote ${opts.settings}${backup ? ` (previous content: ${path.basename(backup)})` : ''}`);
  } catch (e) {
    throw new Failure(`write failed: ${e.message}`);
  }
  return 0;
}

if (require.main === module) {
  try {
    process.exit(main(process.argv.slice(2)));
  } catch (e) {
    console.error(`sync-permissions: ${e instanceof Failure ? e.message : (e && e.stack) || e}`);
    process.exit(2);
  }
} else {
  module.exports = { rtkTwin, withTwins, plan, loadRules };
}
