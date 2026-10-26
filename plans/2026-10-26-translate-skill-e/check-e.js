// translate-skill-e Acceptance 1–4 checks.
// Usage: node check-e.js <worktree root> [<english SKILL.md path>]
const fs = require('fs');
const path = require('path');
const root = process.argv[2];
const P = (p) => path.join(root, p);
const en = fs.readFileSync(process.argv[3] || P('skills/e/SKILL.md'), 'utf8');
const dir = 'plans/2026-10-26-translate-skill-e';
let fail = 0;
const bad = (m) => { console.log('  ! ' + m); fail++; };
const manifest = fs.readFileSync(P('plans/2026-10-22-slim-skill-e-ko/manifest.md'), 'utf8');

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
  const loc = locs.get(id);
  if (loc === undefined) { bad(`no location: ${id}`); continue; }
  const k = loc.indexOf(':: ');
  const text = k >= 0 ? fs.readFileSync(path.isAbsolute(loc.slice(0, k)) ? loc.slice(0, k) : P(loc.slice(0, k)), 'utf8') : en;
  const quote = k >= 0 ? loc.slice(k + 3) : loc;
  if (!text.includes(quote)) bad(`not found: ${id} — ${quote}`); else n1++;
}
const extra = [...locs.keys()].filter((k) => !ids.includes(k));
if (extra.length) bad('extra location ids: ' + extra.join(', '));
console.log(`1. clauses ${ids.length}, found ${n1}`);

// 2. core phrases
const lines = manifest.split('\n');
const setLine = lines[lines.findIndex((l) => l.startsWith('## 핵심 문구')) + 1];
const phrases = setLine.split(' · ').map((s) => s.trim()).filter(Boolean);
const map = new Map();
for (const l of fs.readFileSync(P(`${dir}/phrases-en.txt`), 'utf8').split('\n')) {
  if (!l.trim() || l.startsWith('# ')) continue;
  const [ko, e] = l.split(' => ');
  map.set(ko.trim(), e.trim());
}
let n2 = 0;
for (const ph of phrases) {
  const target = /[가-힣]/.test(ph) ? map.get(ph) : ph;
  if (!target) { bad(`no English counterpart for core phrase: ${ph}`); continue; }
  if (!en.includes(target)) bad(`core phrase missing: ${target}`); else n2++;
}
console.log(`2. core phrases ${phrases.length}, found ${n2}`);

// 3. Hangul only in the `/e 머지` input token
const stripped = en.split('/e 머지').join('').split('"등록 불가"').join('');
const hangul = [...stripped.matchAll(/[가-힣]+/g)].map((m) => m[0]);
if (hangul.length) bad(`Hangul outside /e 머지: ${hangul.length} runs — ${hangul.slice(0, 10).join(' ')}`);
console.log(`3. Hangul runs outside the input token ${hangul.length}`);

// 4b. internal reference labels: same count as the Korean original (case-insensitive)
const ko = require('child_process').execFileSync('git', ['-C', root, 'show', 'b3fcf63:skills/e/SKILL.md'], { encoding: 'utf8' });
const cnt = (s, k) => (s.match(new RegExp(k.replace(/[.*+?^${}()|[\]\\]/g, '\\// 4. markers'), 'gi')) || []).length;
for (const [k, e] of [['6 전', '6 pre'], ['M1~M6', 'M1~M6'], ['복구 규칙', 'recovery rule'], ['비차단', 'non-blocking'], ['worktree 정리 규칙', 'worktree cleanup rules'], ['임시 커밋 규칙', 'temporary commit rules'], ['2단계 경로 표기', 'step 2 path notation'], ['지름길', 'shortcut'], ['중단 규칙', 'stop rule'], ['재수집 invariant', 're-collection invariant'], ['main-autopull ⓑ', 'main-autopull ⓑ'], ['등록 불가', '등록 불가']]) if (cnt(ko, k) !== cnt(en, e)) bad(`label count ${k} ${cnt(ko, k)} ≠ ${e} ${cnt(en, e)}`);
if (/[①②③]/.test(en)) bad('circled numbers left');
// 4. markers
const steps = [...en.matchAll(/^### (\d)\. /gm)].map((m) => +m[1]);
if (steps.join() !== '1,2,3,4,5,6,7,8') bad('step numbers: ' + steps.join());
for (const m of ['### 6 pre.', '### Merge mode M1~M6', '## Temporary commit rules', '## Worktree cleanup rules', '## Boundaries', '**M1 entry gate', '**M2 PR lookup', '**M3 prerequisite', '**M3 push', '**M4 plan done commit', '**M5 checks', '**M6 merge', '(1) the branch', '(2) no plan', '(3) an unchecked', '(4) `gh repo view`', '(5) an unchecked']) if (!en.includes(m)) bad('marker ' + m);
for (let c = 1; c <= 6; c++) if (!new RegExp(`^  ${c}\\. \\*\\*`, 'm').test(en)) bad(`step 7 condition ${c}`);
const claude = fs.readFileSync(P('CLAUDE.md'), 'utf8');
for (const q of ['`/e` step 8', '`/e` step 6', 'step 7 deletion', '`/e` step 7 and the worktree cleanup rules', 'M4 commit']) if (!claude.includes(q)) bad(`CLAUDE.md pointer text missing: ${q}`);
console.log('4. markers checked');
console.log(fail ? `FAIL ${fail}` : 'PASS');
process.exitCode = fail ? 1 : 0;
