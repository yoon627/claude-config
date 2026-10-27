// translate-skill-commit-check Acceptance 1–4 checks.
// Usage: node check-cc.js <worktree root> [<path to the SKILL.md to check>]
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = process.argv[2];
const rel = 'skills/commit-check/SKILL.md';
const en = fs.readFileSync(process.argv[3] || path.join(root, rel), 'utf8');
const ko = execFileSync('git', ['-C', root, 'show', `1d9c2ae:${rel}`], { encoding: 'utf8' });
const dir = 'plans/2026-10-27-translate-skill-commit-check';
const P = (p) => path.join(root, p);
let fail = 0;
const bad = (m) => { console.log('  ! ' + m); fail++; };
const manifest = fs.readFileSync(P(`${dir}/manifest.md`), 'utf8');

// 1. clause locations (whole-clause quotes, several joined by " ‖ "; each quote occurs once)
const ids = [...manifest.matchAll(/^- ([A-Za-z0-9]+(?:\.[0-9a-z]+)+) /gm)].map((m) => m[1]);
const locs = new Map();
for (const line of fs.readFileSync(P(`${dir}/locations-en.txt`), 'utf8').split('\n')) {
  if (!line.trim() || line.startsWith('# ')) continue;
  const i = line.indexOf(' | ');
  locs.set(line.slice(0, i).trim(), line.slice(i + 3));
}
const covered = new Uint8Array(en.length);
let n1 = 0;
for (const id of ids) {
  const loc = locs.get(id);
  if (loc === undefined) { bad(`no location: ${id}`); continue; }
  const quotes = loc.split(' ‖ ');
  const miss = quotes.filter((q) => !en.includes(q));
  if (miss.length) { bad(`not found: ${id} — ${miss.join(' ‖ ').slice(0, 100)}`); continue; }
  for (const q of quotes) {
    const at = en.indexOf(q);
    if (en.indexOf(q, at + 1) >= 0) bad(`quote occurs more than once: ${id} — ${q.slice(0, 60)}`);
    for (let c = at; c < at + q.length; c++) covered[c] = 1;
  }
  n1++;
}
const extra = [...locs.keys()].filter((k) => !ids.includes(k));
if (extra.length) bad('extra location ids: ' + extra.join(', '));
console.log(`1. clauses ${ids.length}, found ${n1}`);

// 2. core phrases
const lines = manifest.split('\n');
const setLine = lines[lines.findIndex((l) => l.startsWith('## 핵심 문구')) + 1];
const phrases = setLine.split(' · ').map((s) => s.trim()).filter(Boolean);
let n2 = 0;
for (const ph of phrases) if (!en.includes(ph)) bad(`core phrase missing: ${ph}`); else n2++;
console.log(`2. core phrases ${phrases.length}, found ${n2}`);

// 3. Hangul only in kept literals
const keep = ['`merge-tree --write-tree 실패`'];
let s = en; for (const k of keep) s = s.split(k).join('');
const h = [...s.matchAll(/[\u1100-\u11ff\u3130-\u318f\uac00-\ud7a3]+/g)].map((m) => m[0]);
if (h.length) bad(`Hangul left: ${h.slice(0, 8).join(' ')}`);
console.log(`3. Hangul runs outside kept literals ${h.length}`);

// 4. markers
if (ko.split('\n').length !== en.split('\n').length) bad('line count');
for (const hd of ['# commit-check — check and restructure commit units', '## Judgment criteria', '## Procedure', '## When called from `/e merge`', '## Plan JSON', '## What it does not do']) if (!en.includes('\n' + hd + '\n')) bad('heading ' + hd);
const proc = en.slice(en.indexOf('## Procedure'), en.indexOf('## When called from'));
for (let x = 1; x <= 7; x++) if (!new RegExp(`^${x}\\. \\*\\*`, 'm').test(proc)) bad(`procedure step ${x}`);
if (/[\u2460-\u2473]/.test(en)) bad('circled numbers');
if (!/^---\nname: commit-check\ndescription: \S/.test(en)) bad('frontmatter keys');
if (/^description: .*: /m.test(en.split('\n').slice(1, 3).join('\n'))) bad('": " in description');
console.log('4. markers checked');

// 5. no rule text outside the quotes: headings, the frontmatter frame, the `description: ` key and code fences are exempt; any uncovered letter elsewhere fails
let n5 = 0; let pos = 0;
for (const line of en.split('\n')) {
  const exempt = /^#/.test(line) || /^(---|name: commit-check|\s*```(json)?)$/.test(line);
  if (!exempt) {
    const from = line.startsWith('description: ') ? 'description: '.length : 0;
    let run = '';
    const flush = () => { if (/[A-Za-z\u3130-\u318f\uac00-\ud7a3]/.test(run)) { bad(`uncovered: ${run.trim().slice(0, 90)}`); n5++; } run = ''; };
    for (let c = from; c < line.length; c++) { if (covered[pos + c]) flush(); else run += line[c]; }
    flush();
  }
  pos += line.length + 1;
}
console.log(`5. uncovered runs ${n5}`);
console.log(fail ? `FAIL ${fail}` : 'PASS');
process.exitCode = fail ? 1 : 0;
