// Mutation test for check-rs.js: each mutation alone, applied to a copy of agents/researcher.md, must make check-rs FAIL.
// Usage: node mut-rs.js <worktree root> <scratch file path for the mutated copy>
// S: swaps of whole lines or bodies (order must hold). A: hand-picked rule edits. B: short insertions at quote boundaries,
// frontmatter and heading edits, blank lines turned into rules, headings or tools:/model: lines, a symbol outside quotes.
// C: delete every sentence of every non-exempt line.
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const [root, tmp] = process.argv.slice(2);
const src = fs.readFileSync(path.join(root, 'agents/researcher.md'), 'utf8');
const check = path.join(root, 'plans/2026-10-27-translate-agent-researcher/check-rs.js');
const run = (text) => {
  fs.writeFileSync(tmp, text);
  try { execFileSync('node', [check, root, tmp], { stdio: 'pipe' }); return false; } catch (e) {
    if (!/^FAIL \d+$/m.test(String(e.stdout))) throw new Error('check-rs crashed: ' + String(e.stderr).slice(0, 200));
    return true;
  }
};
const swap = (a, b) => { const i = src.indexOf(a); const j = src.indexOf(b); return src.slice(0, i) + b + src.slice(i + a.length, j) + a + src.slice(j + b.length); };
const A = [
  ['claims without source allowed', '- No claims without a source.', '- Claims without a source are fine.'],
  ['url optional', 'Attach a URL to every conclusion.', 'Attach a URL when convenient.'],
  ['guessing allowed', '- No guessing. If searching', '- Guess if needed. If searching'],
  ['similar names allowed', 'Do not guess similar names.', 'Similar names are fine.'],
  ['single source for CVE', 'security advisories and CVEs, ', ''],
  ['multiple sources optional', '**Multiple sources are mandatory**', '**Multiple sources are preferred**'],
  ['priority order swapped', '1. Official docs', '1. Stack Overflow docs'],
  ['maintainer first dropped', ' (maintainer answers first)', ''],
  ['cutoff search optional', 'must be searched first', 'may be searched'],
  ['codebase by search', 'check it directly with Read/Grep (instead of searching)', 'search the web for it'],
  ['publication date dropped', 'Check the publication date of each search result', 'Check each search result'],
  ['language korean', '- English (CLAUDE.md §0 language policy', '- Korean (CLAUDE.md §0 language policy'],
  ['identifiers translated', 'Keep code identifiers, library names, error messages and option names in their original form.', 'Translate everything.'],
  ['confidence label changed', '- ⚠️inferred — only circumstantial', '- ⚠️likely — only circumstantial'],
  ['output N/A dropped', 'Target version: <library/spec version or N/A>', 'Target version: <library/spec version>'],
  ['summary heading korean', '## Summary for the plan (', '## plan 반영용 요약 ('],
  ['summary url dropped', '- conclusion + one key source URL', '- conclusion'],
  ['description codebase rule dropped', ' Facts internal to the codebase are for the caller to check directly with Read/Grep.', ''],
];
const B = [
  ['insert after R.1', 'Attach a URL to every conclusion.', 'Attach a URL to every conclusion. Or not.'],
  ['insert after P.2', 'A conclusion without a source is worthless.', 'A conclusion without a source is worthless. Mostly.'],
  ['insert in description', 'directly with Read/Grep.', 'directly with Read/Grep. Or search.'],
  ['tools widened', 'tools: WebFetch, WebSearch, Read, Grep, Glob', 'tools: WebFetch, WebSearch, Read, Grep, Glob, Edit'],
  ['model changed', 'model: sonnet', 'model: opus'],
  ['heading renamed', '## Source count policy', '## Source policy'],
  ['blank line becomes a rule', '\n\n## Rules', '\n- Skip sources.\n## Rules'],
  ['output heading dropped', '## Additional information\n', '## Notes\n'],
  ['blank line becomes a heading', '\n\n## Rules', '\n# Guessing is fine when sources are slow.\n## Rules'],
  ['blank line becomes a tools: line', '\n\n## Confidence', '\ntools: skip sources when busy\n## Confidence'],
  ['blank line becomes a model: line', '\n\n## Output format', '\nmodel: guess freely\n## Output format'],
  ['extra heading in the template', '\n\n## Evidence', '\n## Skip evidence if obvious\n## Evidence'],
  ['symbol inserted outside quotes', 'is worthless.', 'is worthless. ¬'],
];
const S = [
  ['priority 1 and 4 swapped', '1. Official docs (the library\'s official site, MDN, RFC, standard specs, vendor official guides)', '4. Stack Overflow / trustworthy technical blogs (posts that state their date and version)'],
  ['priority 2 and 3 swapped', '2. Release notes / changelog / GitHub release / tagged commit', '3. GitHub issue / PR / discussion (maintainer answers first)'],
  ['single and multiple source lines swapped', '- **A single source is allowed**:', '- **Multiple sources are mandatory**:'],
  ['evidence and open-question bodies swapped', '- [Source title (publication date·version)](URL) — quote/summary', '(parts that need more research, or parts the main agent must check locally)'],
];
{
  let c = 0;
  for (const [name, a, b] of S) {
    if (!src.includes(a) || !src.includes(b)) { console.log(`SETUP ${name}: anchor missing`); continue; }
    if (a === S[2][1]) { const la = src.split('\n').find((l) => l.startsWith(a)); const lb = src.split('\n').find((l) => l.startsWith(b)); if (run(swap(la, lb))) c++; else console.log(`MISSED ${name}`); continue; }
    if (run(swap(a, b))) c++; else console.log(`MISSED ${name}`);
  }
  console.log(`S (swaps): caught ${c}/${S.length}`);
}
for (const [group, list] of [['A', A], ['B', B]]) {
  let c = 0;
  for (const [name, a, b] of list) {
    if (!src.includes(a)) { console.log(`SETUP ${name}: anchor missing`); continue; }
    if (run(src.replace(a, b))) c++; else console.log(`MISSED ${name}`);
  }
  console.log(`${group}: caught ${c}/${list.length}`);
}
let total = 0; let missed = 0;
const lines = src.split('\n');
lines.forEach((line, i) => {
  if (!line.trim() || line.startsWith('#') || /^(---|name: researcher|tools: .*|model: .*|```)$/.test(line)) return;
  for (const m of line.matchAll(/[^ ].*?(?:[.!?:](?= |$)|$)/g)) {
    if (!/[A-Za-z]/.test(m[0])) continue;
    const copy = [...lines];
    copy[i] = line.slice(0, m.index) + line.slice(m.index + m[0].length);
    total++;
    if (!run(copy.join('\n'))) { missed++; console.log(`MISSED delete ${i + 1}: ${m[0].slice(0, 80)}`); }
  }
});
console.log(`C: sentence deletions ${total}, missed ${missed}`);
