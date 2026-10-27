// translate-skill-c Acceptance 1–4 checks.
// Usage: node check-c.js <worktree root> [<english SKILL.md path>]
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = process.argv[2];
const P = (p) => path.join(root, p);
const en = fs.readFileSync(process.argv[3] || P('skills/c/SKILL.md'), 'utf8');
const ko = execFileSync('git', ['-C', root, 'show', 'eaaf7d7:skills/c/SKILL.md'], { encoding: 'utf8' });
const dir = 'plans/2026-10-27-translate-skill-c';
let fail = 0;
const bad = (m) => { console.log('  ! ' + m); fail++; };
const manifest = fs.readFileSync(P(`${dir}/manifest.md`), 'utf8');

// 1. clause locations
const ids = [...manifest.matchAll(/^- ([A-Za-z0-9]+(?:\.[0-9a-z]+)+) /gm)].map((m) => m[1]);
const locs = new Map();
for (const line of fs.readFileSync(P(`${dir}/locations-en.txt`), 'utf8').split('\n')) {
  if (!line.trim() || line.startsWith('# ')) continue;
  const i = line.indexOf(' | ');
  locs.set(line.slice(0, i).trim(), line.slice(i + 3));
}
let n1 = 0;
for (const id of ids) {
  const q = locs.get(id);
  if (q === undefined) { bad(`no location: ${id}`); continue; }
  const miss = q.split(' ‖ ').filter((s) => !en.includes(s));
  if (miss.length) bad(`not found: ${id} — ${miss.join(' ‖ ')}`); else n1++;
}
const extra = [...locs.keys()].filter((k) => !ids.includes(k));
if (extra.length) bad('extra location ids: ' + extra.join(', '));
console.log(`1. clauses ${ids.length}, found ${n1}`);

// 2. core phrases (none contain Korean)
const lines = manifest.split('\n');
const setLine = lines[lines.findIndex((l) => l.startsWith('## 핵심 문구')) + 1];
const phrases = setLine.split(' · ').map((s) => s.trim().replace(/^`|`$/g, '')).filter(Boolean);
let n2 = 0;
for (const ph of phrases) { if (/[가-힣]/.test(ph)) bad(`Korean core phrase needs a counterpart: ${ph}`); else if (!en.includes(ph)) bad(`core phrase missing: ${ph}`); else n2++; }
console.log(`2. core phrases ${phrases.length}, found ${n2}`);

// 3. no Hangul
const hangul = [...en.matchAll(/[가-힣]+/g)].map((m) => m[0]);
if (hangul.length) bad(`Hangul left: ${hangul.length} runs — ${hangul.slice(0, 10).join(' ')}`);
console.log(`3. Hangul runs ${hangul.length}`);

// 4. markers and internal references
if (ko.split('\n').length !== en.split('\n').length) bad(`line count ${ko.split('\n').length} ≠ ${en.split('\n').length}`);
const steps = [...en.matchAll(/^### (\d)\. /gm)].map((m) => +m[1]);
if (steps.join() !== '1,2,3') bad('step numbers: ' + steps.join());
const exBlock = en.slice(en.indexOf('(closed list of 5)'));
for (let x = 1; x <= 5; x++) if (!new RegExp(`^  ${x}\\. `, 'm').test(exBlock)) bad(`exception ${x}`);
const rows = (s) => s.split('\n').filter((l) => /^  \| /.test(l)).length;
if (rows(ko) !== rows(en)) bad(`sync table rows ${rows(ko)} ≠ ${rows(en)}`);
if (/[①②③]/.test(en)) bad('circled numbers');
const cnt = (s, re) => (s.match(re) || []).length;
if (cnt(ko, /예외\s?[45](?!종)/g) !== cnt(en, /exception [45]/g)) bad(`exception refs ${cnt(ko, /예외\s?[45](?!종)/g)} ≠ ${cnt(en, /exception [45]/g)}`);
const fm = en.split('\n').slice(1, 3).join('\n');
if (/^description: .*: /m.test(fm)) bad('": " inside the description plain scalar');
console.log('4. markers checked');
console.log(fail ? `FAIL ${fail}` : 'PASS');
process.exitCode = fail ? 1 : 0;
