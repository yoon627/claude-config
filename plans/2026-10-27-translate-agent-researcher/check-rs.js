// translate-agent-researcher Acceptance 1–4 checks.
// Usage: node check-rs.js <worktree root> [<path to the researcher.md to check>]
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = process.argv[2];
const rel = 'agents/researcher.md';
const en = fs.readFileSync(process.argv[3] || path.join(root, rel), 'utf8');
const show = (p) => execFileSync('git', ['-C', root, 'show', `b1e7042:${p}`], { encoding: 'utf8' });
const ko = show(rel);
const dir = 'plans/2026-10-27-translate-agent-researcher';
const P = (p) => path.join(root, p);
let fail = 0;
const bad = (m) => { console.log('  ! ' + m); fail++; };
const manifest = fs.readFileSync(P(`${dir}/manifest.md`), 'utf8');

// 1. clause locations (whole-clause quotes, several joined by " ‖ "; each quote occurs once, in manifest order)
const ids = [...manifest.matchAll(/^- ([A-Za-z0-9]+(?:\.[0-9a-z]+)+) /gm)].map((m) => m[1]);
const locs = new Map();
for (const line of fs.readFileSync(P(`${dir}/locations-en.txt`), 'utf8').split('\n')) {
  if (!line.trim() || line.startsWith('# ')) continue;
  const i = line.indexOf(' | ');
  locs.set(line.slice(0, i).trim(), line.slice(i + 3));
}
const covered = new Uint8Array(en.length);
let n1 = 0; let last = -1;
for (const id of ids) {
  const loc = locs.get(id);
  if (loc === undefined) { bad(`no location: ${id}`); continue; }
  const quotes = loc.split(' ‖ ');
  const miss = quotes.filter((q) => !en.includes(q));
  if (miss.length) { bad(`not found: ${id} — ${miss.join(' ‖ ').slice(0, 100)}`); continue; }
  for (const q of quotes) {
    const at = en.indexOf(q);
    if (en.indexOf(q, at + 1) >= 0) bad(`quote occurs more than once: ${id} — ${q.slice(0, 60)}`);
    if (at <= last) bad(`quote out of manifest order: ${id} — ${q.slice(0, 60)}`);
    last = at;
    for (let c = at; c < at + q.length; c++) covered[c] = 1;
  }
  n1++;
}
const extra = [...locs.keys()].filter((k) => !ids.includes(k));
if (extra.length) bad('extra location ids: ' + extra.join(', '));
console.log(`1. clauses ${ids.length}, found ${n1}`);

// 2. core phrases (searched as written in the manifest, backticks included)
const lines = manifest.split('\n');
const setLine = lines[lines.findIndex((l) => l.startsWith('## 핵심 문구')) + 1];
const phrases = setLine.split(' · ').map((s) => s.trim()).filter(Boolean);
let n2 = 0;
for (const ph of phrases) if (!en.includes(ph)) bad(`core phrase missing: ${ph}`); else n2++;
console.log(`2. core phrases ${phrases.length}, found ${n2}`);

// 3. no Hangul at all
const h = [...en.matchAll(/[ᄀ-ᇿ㄰-㆏가-힣]+/g)].map((m) => m[0]);
if (h.length) bad(`Hangul left: ${h.slice(0, 8).join(' ')}`);
console.log(`3. Hangul runs ${h.length}`);

// 4. markers
if (ko.split('\n').length !== en.split('\n').length) bad('line count');
const fm = en.split('\n').slice(0, 6);
if (fm[0] !== '---' || fm[1] !== 'name: researcher' || !/^description: \S/.test(fm[2]) || fm[3] !== 'tools: WebFetch, WebSearch, Read, Grep, Glob' || fm[4] !== 'model: sonnet' || fm[5] !== '---') bad('frontmatter');
if (/: /.test(fm[2].slice('description: '.length))) bad('": " in description');
const headings = ['## Core mission', '## Response language', '## Source priority', '## Source count policy', '## Rules', '## Confidence', '## Output format',
  '## Question restated', '## Conclusion', '## Evidence', '## Additional information', '## Open questions', '## Summary for the plan (1–2 lines the main agent applies to `<ROOT>/plans/<dir>/<slug>-plan.md`)'];
const actual = en.match(/^#.*$/gm) || [];
if (actual.join('\n') !== headings.join('\n')) bad(`headings differ from the expected 7 body + 6 output sections: ${actual.filter((x) => !headings.includes(x)).join(' | ') || 'order or missing'}`);
const pri = en.slice(en.indexOf('## Source priority'), en.indexOf('## Source count policy'));
for (let x = 1; x <= 4; x++) if (!new RegExp(`^${x}\\. `, 'm').test(pri)) bad(`source priority ${x}`);
if (/[①-⑳]/.test(en)) bad('circled numbers');
const dlcRel = 'skills/dlc/SKILL.md';
const dlcNew = fs.readFileSync(P(dlcRel), 'utf8').split('\n');
const dlcOld = show(dlcRel).split('\n');
const changed = dlcOld.map((l, i) => (l !== dlcNew[i] ? i : -1)).filter((i) => i >= 0);
if (dlcOld.length !== dlcNew.length || changed.length !== 1) bad(`dlc must change exactly one line (changed ${changed.length})`);
else if (!dlcNew[changed[0]].includes('"plan 반영용 요약"(영어로 옮긴 agent 는 "Summary for the plan")')) bad('dlc pointer line');
console.log('4. markers checked');

// 5. nothing outside the quotes but whitespace and list markers (- *): headings, the six frontmatter lines (description only its key) and code fences are exempt
let n5 = 0; let pos = 0; let idx = -1;
for (const line of en.split('\n')) {
  idx++;
  const exempt = /^#/.test(line) || line === '```' || (idx <= 5 && idx !== 2);
  if (!exempt) {
    const from = idx === 2 ? 'description: '.length : 0;
    let run = '';
    const flush = () => { if (/[^\s*-]/.test(run)) { bad(`uncovered: ${run.trim().slice(0, 90)}`); n5++; } run = ''; };
    for (let c = from; c < line.length; c++) { if (covered[pos + c]) flush(); else run += line[c]; }
    flush();
  }
  pos += line.length + 1;
}
console.log(`5. uncovered runs ${n5}`);
console.log(fail ? `FAIL ${fail}` : 'PASS');
process.exitCode = fail ? 1 : 0;
