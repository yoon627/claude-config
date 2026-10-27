// Shared mutation test for check-translation.js: every mutated copy must make the check FAIL (its stdout has a "FAIL n" line;
// a crash of the check stops this test instead of counting as caught). The unmutated file must PASS first.
// Exit code 1 when the baseline fails or any mutation is MISSED or its anchor is missing (SETUP).
// Usage: node mut-translation.js <worktree root> <unit config.json> <scratch file path for the mutated copy>
//
// R  rule edits listed in the config ("mutations": [[name, from, to], …]) — chosen by the unit
// G  generated, the same for every unit:
//    swap   each pair of adjacent non-blank lines outside the frontmatter
//    edge   a short sentence, and "**" emphasis, appended at the end of each quote
//    indent each plain text line indented by four spaces (markdown renders it as code)
//    fence  each code fence given a language tag
//    blank  each blank line turned into a heading, a "tools:" line, a rule sentence, a symbol
//    del    each sentence of each non-exempt line deleted
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const [root, cfgPath, tmp] = process.argv.slice(2);
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
const lf = (x) => x.replace(/\r\n/g, '\n');
const src = lf(fs.readFileSync(path.join(root, cfg.file), 'utf8'));
const check = path.join(__dirname, 'check-translation.js');
const run = (text) => {
  fs.writeFileSync(tmp, text);
  try { execFileSync('node', [check, root, cfgPath, tmp], { stdio: 'pipe' }); return false; } catch (e) {
    if (!/^FAIL \d+$/m.test(String(e.stdout))) throw new Error('check crashed: ' + String(e.stderr).slice(0, 300));
    return true;
  }
};
{
  fs.writeFileSync(tmp, src);
  try { execFileSync('node', [check, root, cfgPath, tmp], { stdio: 'pipe' }); } catch (e) {
    console.log('BASELINE FAIL — the unmutated file does not pass, so no mutation result means anything:\n' + String(e.stdout));
    process.exit(1);
  }
}
const tally = {};
let bad = 0;
const record = (group, name, failed) => {
  tally[group] = tally[group] || [0, 0];
  tally[group][1]++;
  if (failed) tally[group][0]++; else { bad++; console.log(`MISSED ${group} ${name}`); }
};

for (const [name, a, b] of cfg.mutations || []) {
  if (!src.includes(a) || a === b) { console.log(`SETUP R ${name}: anchor missing or no-op`); record('R', name, false); continue; }
  record('R', name, run(src.replace(a, b)));
}

const lines = src.split('\n');
const fmLen = (cfg.frontmatter || []).length;
const fence = /^\s*(`{3,}|~{3,})\w*\s*$/;
for (let i = fmLen; i < lines.length - 1; i++) {
  if (!lines[i].trim() || !lines[i + 1].trim() || lines[i] === lines[i + 1]) continue;
  const copy = [...lines];
  [copy[i], copy[i + 1]] = [copy[i + 1], copy[i]];
  record('G.swap', `${i + 1}<->${i + 2}`, run(copy.join('\n')));
}
for (const line of lf(fs.readFileSync(path.join(root, cfg.locations), 'utf8')).split('\n')) {
  if (!line.trim() || line.startsWith('# ')) continue;
  for (const q of line.slice(line.indexOf(' | ') + 3).split(' ‖ ').map((x) => x.split('⏎').join('\n'))) {
    const at = src.indexOf(q);
    if (at < 0) { console.log(`SETUP G.edge quote not found: ${q.slice(0, 40)}`); record('G.edge', q.slice(0, 40), false); continue; }
    const end = at + q.length;
    record('G.edge', q.slice(0, 40), run(src.slice(0, end) + ' Or skip it.' + src.slice(end)));
    record('G.edge', '** ' + q.slice(0, 37), run(src.slice(0, end) + '**' + src.slice(end)));
  }
}
const fills = ['## Skip this when busy', 'tools: Edit', '- Guessing is fine.', '¬'];
lines.forEach((l, i) => {
  if (l.trim() || i < fmLen) return;
  for (const f of fills) {
    const copy = [...lines];
    copy[i] = f;
    record('G.blank', `${i + 1} ${f}`, run(copy.join('\n')));
  }
});
lines.forEach((l, i) => {
  if (i < fmLen || !l.trim()) return;
  const copy = [...lines];
  if (fence.test(l)) { copy[i] = l.replace(/\s*$/, 'bash'); record('G.fence', `${i + 1}`, run(copy.join('\n'))); return; }
  if (/^(#|\s*([-*]|\d+\.|>) )/.test(l) || /^\s/.test(l)) return;
  copy[i] = '    ' + l;
  record('G.indent', `${i + 1}`, run(copy.join('\n')));
});
const descIdx = (cfg.frontmatter || []).indexOf(null);
lines.forEach((l, i) => {
  if (!l.trim() || l.startsWith('#') || fence.test(l) || (i < fmLen && i !== descIdx)) return;
  for (const m of l.matchAll(/[^ ].*?(?:[.!?:](?= |$)|$)/g)) {
    if (!/[A-Za-z]/.test(m[0])) continue;
    const copy = [...lines];
    copy[i] = l.slice(0, m.index) + l.slice(m.index + m[0].length);
    record('G.del', `${i + 1}: ${m[0].slice(0, 60)}`, run(copy.join('\n')));
  }
});
for (const [g, [c, t]] of Object.entries(tally)) console.log(`${g}: caught ${c}/${t}`);
if (bad) { console.log(`NOT ALL CAUGHT: ${bad}`); process.exitCode = 1; }
