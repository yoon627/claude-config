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
// Exit codes: 0 in sync or written · 1 drift (--check only) · 2 error (unreadable JSON or rules,
// bad arguments, write failure, anything unexpected).
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const RULES_DEFAULT = path.join(__dirname, 'permission-rules.json');
const SETTINGS_DEFAULT = path.join(os.homedir(), '.claude', 'settings.json');
const USAGE = 'usage: node scripts/sync-permissions.js [--settings <path>] [--rules <path>] [--check | --dry-run] [--keep-allow]';

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
  return rules;
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

// plan(settings, rules, { keepAllow }) -> { next, addAsk, retireAsk, removeAllow, localOnly, drift }
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
  const drift = addAsk.length + retireAsk.length + removeAllow.length > 0;
  return { next, addAsk, retireAsk, removeAllow, localOnly, drift };
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
  list('local-only ask rules (not in the canonical file, kept)', p.localOnly);
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
  const p = plan(settings, rules, { keepAllow: opts.keepAllow });
  if (!p.drift) { console.log(`sync-permissions: ${opts.settings} in sync`); return 0; }
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
