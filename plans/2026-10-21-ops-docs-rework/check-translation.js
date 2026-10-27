// Shared translation check for ops-docs-rework translate units (one file per unit).
// Usage: node check-translation.js <worktree root> <unit config.json> [<path of the translated file to check>]
//
// Config (paths relative to the worktree root):
//   file          translated file, e.g. "agents/plan-reviewer.md"
//   base          commit holding the Korean original (line count must match)
//   manifest      clause manifest (Korean); clause lines are "- <id> …" (every "- " line before "## 다른 파일이 가리키는 표지" or
//                 "## 핵심 문구" must parse as one), core phrases are the first non-blank line after "## 핵심 문구"
//   locations     "<id> | <quote>[ ‖ <quote>…]" — each quote verbatim, once, in manifest order
//   keep          strings allowed to contain Hangul (kept verbatim)
//   frontmatter   expected lines from the first "---" to the closing "---"; null marks the description line
//   headings      exact list of every line starting with "#", in order (required)
//   numbered      [{ "from": "<line start>", "to": "<line start>", "first": 1, "last": N }] — "N. " items between two lines
//   extra         optional module (relative to the config) exporting (ctx) => void for unit-specific checks
//   outside       extra characters allowed outside the quotes besides whitespace and a leading list marker (e.g. "{}[]" for a JSON example)
//
// Sections: 1 quotes (found, once, in order) · 2 core phrases (as written in the manifest) · 3 Hangul only in keep
// · 4 markers (line count, frontmatter, headings, numbering, line shapes and indentation, wordless lines and code fences
// equal to the original, circled numbers, ": " in description, extra)
// · 5 outside the quotes only whitespace and a leading list marker ("- ", "* ", "N. "), except headings, frontmatter
// lines (description: only its key), code fences and lines without words (section 4 pins those to the original).
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const [root, cfgPath, override] = process.argv.slice(2);
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
const P = (p) => path.join(root, p);
const lf = (s) => s.replace(/\r\n/g, '\n');
const read = (p) => lf(fs.readFileSync(p, 'utf8'));
const en = read(override || P(cfg.file));
const show = (p) => lf(execFileSync('git', ['-C', root, 'show', `${cfg.base}:${p}`], { encoding: 'utf8' }));
const ko = show(cfg.file);
let fail = 0;
const bad = (m) => { console.log('  ! ' + m); fail++; };
const manifest = read(P(cfg.manifest));
if (!Array.isArray(cfg.headings)) bad('config: headings is required');

const ids = [...manifest.matchAll(/^- ([A-Za-z0-9]+(?:\.[0-9a-z]+)+) /gm)].map((m) => m[1]);
const clauseEnd = manifest.search(/^## (다른 파일이 가리키는 표지|핵심 문구)/m);
for (const l of manifest.slice(0, clauseEnd < 0 ? undefined : clauseEnd).split('\n')) {
  if (l.startsWith('- ') && !/^- [A-Za-z0-9]+(?:\.[0-9a-z]+)+ /.test(l)) bad(`manifest line is not a clause id: ${l.slice(0, 60)}`);
}
const locs = new Map();
for (const line of read(P(cfg.locations)).split('\n')) {
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
const extraIds = [...locs.keys()].filter((k) => !ids.includes(k));
if (extraIds.length) bad('extra location ids: ' + extraIds.join(', '));
console.log(`1. clauses ${ids.length}, found ${n1}`);

const mlines = manifest.split('\n');
const head = mlines.findIndex((l) => l.startsWith('## 핵심 문구'));
const setLine = head < 0 ? '' : (mlines.slice(head + 1).find((l) => l.trim()) || '');
const phrases = setLine.split(' · ').map((s) => s.trim()).filter(Boolean);
if (head < 0) bad('manifest has no "## 핵심 문구" section');
else if (!phrases.length) bad('manifest core phrase set is empty');
let n2 = 0;
for (const ph of phrases) if (!en.includes(ph)) bad(`core phrase missing: ${ph}`); else n2++;
console.log(`2. core phrases ${phrases.length}, found ${n2}`);

let stripped = en;
for (const k of cfg.keep || []) stripped = stripped.split(k).join('');
const hangul = [...stripped.matchAll(/[ᄀ-ᇿ㄰-㆏가-힣]+/g)].map((m) => m[0]);
if (hangul.length) bad(`Hangul outside kept strings: ${hangul.slice(0, 8).join(' ')}`);
console.log(`3. Hangul runs outside kept strings ${hangul.length}`);

const lines = en.split('\n');
if (ko.split('\n').length !== lines.length) bad(`line count ${lines.length} ≠ original ${ko.split('\n').length}`);
const fm = cfg.frontmatter || [];
const descIdx = fm.indexOf(null);
fm.forEach((want, i) => {
  if (want === null) { if (!/^description: \S/.test(lines[i] || '')) bad('frontmatter description line'); }
  else if (lines[i] !== want) bad(`frontmatter line ${i + 1}: ${JSON.stringify(lines[i])}`);
});
if (descIdx >= 0 && /: /.test((lines[descIdx] || '').slice('description: '.length))) bad('": " in description');
const actual = lines.filter((l) => l.startsWith('#'));
if (Array.isArray(cfg.headings) && actual.join('\n') !== cfg.headings.join('\n')) {
  const extraH = actual.filter((x) => !cfg.headings.includes(x));
  const missH = cfg.headings.filter((x) => !actual.includes(x));
  bad(`headings differ — extra: ${extraH.join(' | ') || '-'} · missing: ${missH.join(' | ') || '-'}${!extraH.length && !missH.length ? ' · order' : ''}`);
}
for (const n of cfg.numbered || []) {
  const a = lines.findIndex((l) => l.startsWith(n.from));
  const b = lines.findIndex((l, i) => i > a && l.startsWith(n.to));
  if (a < 0 || b < 0) { bad(`numbered block bounds: ${n.from} … ${n.to}`); continue; }
  const got = lines.slice(a, b).map((l) => (l.match(/^(\d+)\. /) || [])[1]).filter(Boolean).map(Number);
  const want = Array.from({ length: n.last - n.first + 1 }, (_, i) => n.first + i);
  if (got.join(',') !== want.join(',')) bad(`numbering under ${n.from}: ${got.join(',')}`);
}
const shape = (l) => {
  if (!l.trim()) return 'blank';
  if (/^\s*(`{3,}|~{3,})/.test(l)) return 'fence';
  const h = l.match(/^(#+) /); if (h) return 'h' + h[1].length;
  const b = l.match(/^(\s*)[-*] /); if (b) return 'bullet' + b[1].length;
  const n = l.match(/^(\s*)\d+\. /); if (n) return 'num' + n[1].length;
  const q = l.match(/^(\s*)> /); if (q) return 'quote' + q[1].length;
  return 'text' + l.match(/^\s*/)[0].length;
};
const koLines = ko.split('\n');
const shapeDiff = lines.map((l, i) => (koLines[i] !== undefined && shape(l) !== shape(koLines[i]) ? i + 1 : 0)).filter(Boolean);
if (shapeDiff.length) bad(`line shape differs from the original at lines ${shapeDiff.slice(0, 10).join(',')}`);
const wordless = (l) => l.trim() && !/[A-Za-z㄰-㆏가-힣]/.test(l);
const pinned = (l) => wordless(l) || shape(l) === 'fence';
const wordDiff = lines.map((l, i) => ((pinned(l) || pinned(koLines[i] || '')) && l !== koLines[i] ? i + 1 : 0)).filter(Boolean);
if (wordDiff.length) bad(`lines without words and code fences must equal the original: ${wordDiff.slice(0, 10).join(',')}`);
if (/[①-⑳]/.test(stripped)) bad('circled numbers');
if (cfg.extra) require(path.resolve(path.dirname(cfgPath), cfg.extra))({ root, cfg, en, ko, lines, bad, show });
console.log('4. markers checked');

const allowed = cfg.outside || '';
let n5 = 0; let pos = 0;
lines.forEach((line, idx) => {
  const inFm = idx < fm.length;
  const exempt = line.startsWith('#') || /^\s*(`{3,}|~{3,})\w*\s*$/.test(line) || (inFm && idx !== descIdx) || wordless(line);
  if (!exempt) {
    const marker = (line.match(/^\s*(?:[-*]|\d+\.) /) || [''])[0].length;
    const from = idx === descIdx ? 'description: '.length : marker;
    let run = '';
    const flush = () => { if ([...run].some((ch) => !/\s/.test(ch) && !allowed.includes(ch))) { bad(`uncovered line ${idx + 1}: ${run.trim().slice(0, 90)}`); n5++; } run = ''; };
    for (let c = from; c < line.length; c++) { if (covered[pos + c]) flush(); else run += line[c]; }
    flush();
  }
  pos += line.length + 1;
});
console.log(`5. uncovered runs ${n5}`);
console.log(fail ? `FAIL ${fail}` : 'PASS');
process.exitCode = fail ? 1 : 0;
