// translate-skill-wt Acceptance 1–4 checks.
// Usage: node check-wt.js <worktree root> [<dir holding SKILL.md, references/env-copy.md, references/rm-recovery.md>]
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = process.argv[2];
const base = process.argv[3] || path.join(root, 'skills/wt');
const P = (p) => path.join(root, p);
const files = { 'skills/wt/SKILL.md': 'SKILL.md', 'skills/wt/references/env-copy.md': 'references/env-copy.md', 'skills/wt/references/rm-recovery.md': 'references/rm-recovery.md' };
const en = {}; const ko = {};
for (const [rel, local] of Object.entries(files)) {
  en[rel] = fs.readFileSync(path.join(base, local), 'utf8');
  ko[rel] = execFileSync('git', ['-C', root, 'show', `142e11e:${rel}`], { encoding: 'utf8' });
}
const S = 'skills/wt/SKILL.md';
const dir = 'plans/2026-10-27-translate-skill-wt';
let fail = 0;
const bad = (m) => { console.log('  ! ' + m); fail++; };
const manifest = fs.readFileSync(P(`${dir}/manifest.md`), 'utf8');

// 1. clause locations (whole-clause quotes, several joined by " ‖ "; each quote occurs once in its file)
const ids = [...manifest.matchAll(/^- ([A-Za-z0-9]+(?:\.[0-9a-z]+)+) /gm)].map((m) => m[1]);
const locs = new Map();
for (const line of fs.readFileSync(P(`${dir}/locations-en.txt`), 'utf8').split('\n')) {
  if (!line.trim() || line.startsWith('# ')) continue;
  const i = line.indexOf(' | ');
  locs.set(line.slice(0, i).trim(), line.slice(i + 3));
}
const covered = Object.fromEntries(Object.keys(files).map((rel) => [rel, new Uint8Array(en[rel].length)]));
let n1 = 0;
for (const id of ids) {
  const loc = locs.get(id);
  if (loc === undefined) { bad(`no location: ${id}`); continue; }
  const k = loc.indexOf(':: ');
  const file = k >= 0 ? loc.slice(0, k) : S;
  const quotes = (k >= 0 ? loc.slice(k + 3) : loc).split(' ‖ ');
  const miss = quotes.filter((q) => !en[file].includes(q));
  if (miss.length) { bad(`not found: ${id} — ${miss.join(' ‖ ').slice(0, 100)}`); continue; }
  for (const q of quotes) {
    const at = en[file].indexOf(q);
    if (en[file].indexOf(q, at + 1) >= 0) bad(`quote occurs more than once: ${id} — ${q.slice(0, 60)}`);
    for (let c = at; c < at + q.length; c++) covered[file][c] = 1;
  }
  n1++;
}
const extra = [...locs.keys()].filter((k) => !ids.includes(k));
if (extra.length) bad('extra location ids: ' + extra.join(', '));
console.log(`1. clauses ${ids.length}, found ${n1}`);

// 2. core phrases (any of the three files)
const lines = manifest.split('\n');
const setLine = lines[lines.findIndex((l) => l.startsWith('## 핵심 문구')) + 1];
const phrases = setLine.split(' · ').map((s) => s.trim().replace(/^`|`$/g, '')).filter(Boolean);
const all = Object.values(en).join('\n');
let n2 = 0;
for (const ph of phrases) if (!all.includes(ph)) bad(`core phrase missing: ${ph}`); else n2++;
console.log(`2. core phrases ${phrases.length}, found ${n2}`);

// 3. Hangul only in kept literals
const keep = ['"로그인 리다이렉트 버그 수정"', '세션 활동 없음', 'ticket=(없음)', '`합계 <duration>`', '`등록 차단`'];
let runs = 0;
for (const [rel, t] of Object.entries(en)) {
  let s = t; for (const k of keep) s = s.split(k).join('');
  const h = [...s.matchAll(/[가-힣]+/g)].map((m) => m[0]);
  if (h.length) bad(`Hangul left in ${rel}: ${h.slice(0, 8).join(' ')}`);
  runs += h.length;
}
console.log(`3. Hangul runs outside kept literals ${runs}`);

// 4. markers and internal references
for (const rel of Object.keys(files)) if (ko[rel].split('\n').length !== en[rel].split('\n').length) bad(`line count ${rel}`);
for (const h of ['## Arguments', '## Common rules', '## list', '## switch', '## request (', '## Question mode', '## rm `<name>`', '## Cautions', '### 1. Derive the slug', '### 2. Collision check', '### 3. Create', '### 4. Report + dlc work']) if (!en[S].includes(h)) bad('heading ' + h);
for (let x = 0; x <= 6; x++) if (!new RegExp(`^${x}\\. `, 'm').test(en[S].slice(en[S].indexOf('### 3. Create')))) bad(`request §3.${x}`);
const rmBlock = en[S].slice(en[S].indexOf('## rm `<name>`'), en[S].indexOf('## Cautions'));
for (let x = 1; x <= 7; x++) if (!new RegExp(`^${x}\\. `, 'm').test(rmBlock)) bad(`rm step ${x}`);
for (const rel of ['skills/wt/references/env-copy.md', 'skills/wt/references/rm-recovery.md']) if (/## 주의/.test(en[rel])) bad(`old heading quote in ${rel}`);
if ((en['skills/wt/references/rm-recovery.md'].match(/`## Cautions`/g) || []).length !== 2) bad('rm-recovery must point to `## Cautions` twice');
if (/[①②③④⑤]/.test(all)) bad('circled numbers');
if (/condition 5 gate|조건5/.test(all)) bad('stale e condition 5');
if (!en[S].includes('e blocks it with its step 7 condition 4 (merged) gate')) bad('e condition 4 pointer');
if (/^description: .*: /m.test(en[S].split('\n').slice(1, 3).join('\n'))) bad('": " in description');
console.log('4. markers checked');

// 5. no rule text outside the quotes: headings and the frontmatter frame are exempt; any other uncovered run with more than 12 letters fails
let n5 = 0;
for (const [rel, t] of Object.entries(en)) {
  let pos = 0;
  for (const line of t.split('\n')) {
    const exempt = /^#/.test(line) || /^(---|name: wt|\|---\|---\||\| Input \| Action \|)$/.test(line);
    if (!exempt) {
      for (const m of line.matchAll(/[^\n]+/g)) {
        let run = '';
        const flush = () => { if ((run.match(/[A-Za-z가-힣]/g) || []).length > 12) { bad(`uncovered in ${rel}: ${run.trim().slice(0, 90)}`); n5++; } run = ''; };
        for (let c = 0; c < m[0].length; c++) { if (covered[rel][pos + m.index + c]) flush(); else run += m[0][c]; }
        flush();
      }
    }
    pos += line.length + 1;
  }
}
console.log(`5. uncovered runs ${n5}`);
console.log(fail ? `FAIL ${fail}` : 'PASS');
process.exitCode = fail ? 1 : 0;
