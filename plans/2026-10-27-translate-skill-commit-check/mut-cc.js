// Mutation test for check-cc.js: each mutation alone, applied to a copy of skills/commit-check/SKILL.md, must make check-cc FAIL.
// Usage: node mut-cc.js <worktree root> <scratch file path for the mutated copy>
// A: hand-picked rule edits. B: short insertions at quote boundaries, an H1 edit and a blank line turned into a rule
// (the cases the plan and code reviews showed passing an earlier checker). C: delete every sentence of every non-heading line.
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const [root, tmp] = process.argv.slice(2);
const src = fs.readFileSync(path.join(root, 'skills/commit-check/SKILL.md'), 'utf8');
const check = path.join(root, 'plans/2026-10-27-translate-skill-commit-check/check-cc.js');
const run = (text) => {
  fs.writeFileSync(tmp, text);
  try { execFileSync('node', [check, root, tmp], { stdio: 'pipe' }); return false; } catch { return true; }
};
const A = [
  ['translate kept literal', '`merge-tree --write-tree 실패`', '`merge-tree --write-tree failed`'],
  ['drop approval rule', 'is a rule the user set (2026-09-24)', 'is optional'],
  ['apply when unattended', 'do not apply; leave only the proposal table in the report', 'apply it'],
  ['auto split by hunk', 'do not split automatically; only write "manual split needed"', 'split it automatically'],
  ['fold null target', 'and do not fold.', 'and fold into the previous commit.'],
  ['plan-only wins', 'This default takes precedence over the `plan-only` default below', 'The `plan-only` default below takes precedence over this default'],
  ['leave unapplied on conflict', 'do not leave it unapplied; switch only that commit', 'leave it unapplied; switch only that commit'],
  ['retry many times', 'and apply once more', 'and apply until it works'],
  ['narrowing dropped', '(`review-followup`·`plan-only` flags are not targets)', '(all flags are targets)'],
  ['split goes into plan', 'go in the table only for reference and not into the plan', 'go into the plan'],
  ['write to caller plan', "Do not write to the caller's record files (plan etc.).", 'Also update the plan.'],
  ['raw git allowed', '(do not run raw `git log/show`)', '(raw `git log/show` is fine)'],
  ['fast path asks', 'end without a question with one line', 'ask, then end with one line'],
  ['default branch restructure', 'so do not restructure (report only).', 'restructure anyway.'],
  ['force push allowed', '- push or force-push —', '- push —'],
  ['bypass allowed', 'by running git commands directly.', 'when needed.'],
  ['message optional on split', 'A split entry requires a `message`', 'A split entry may omit `message`'],
  ['rename split', 'put the old and new paths in the same entry', 'put the old and new paths in separate entries'],
  ['hook refusal skips entry', '(if the hook refuses, the whole apply is refused;', '(if the hook refuses, the entry is skipped;'],
  ['e section heading', '## When called from `/e merge`', '## When called from e'],
  ['squash message unstated', 'so state `message` in the plan entry', 'so the message is optional'],
  ['excluded tag count dropped', ' and excluded by tags (`excluded.tags`)', ''],
  ['description push', ' It does not push.', ''],
  ['code span loses backticks', '`held` (not on the remote', 'held (not on the remote'],
];
const B = [
  ['insert after M.8', 'ask again.', 'ask again. Or just apply.'],
  ['insert after S.5b', 'leave only the proposal table in the report.', 'leave only the proposal table in the report. Or apply.'],
  ['insert after N.3', 'running git commands directly.', 'running git commands directly. Allowed.'],
  ['insert in description', 'It does not push.', 'It does not push. Except main.'],
  ['insert between M.4 and M.5', '"message": ...}`) — if', '"message": ...}`) or hold — if'],
  ['insert after J.2', '(no `show` check needed).', '(no `show` check needed). Optional.'],
  ['edit H1', '# commit-check — check and restructure commit units', '# commit-check — check commit units'],
  ['blank line becomes a rule', '\n\n## Procedure', '\n- Skip step 5.\n## Procedure'],
];
let caught = 0;
for (const [group, list] of [['A', A], ['B', B]]) {
  let c = 0;
  for (const [name, a, b] of list) {
    if (!src.includes(a)) { console.log(`SETUP ${name}: anchor missing`); continue; }
    const failed = run(src.replace(a, b));
    if (!failed) console.log(`MISSED ${name}`);
    if (failed) c++;
  }
  console.log(`${group}: caught ${c}/${list.length}`);
  caught += c;
}
let total = 0; let missed = 0;
const lines = src.split('\n');
lines.forEach((line, i) => {
  if (!line.trim() || line.startsWith('#') || /^(---|name: commit-check|\s*```(json)?)$/.test(line)) return;
  for (const m of line.matchAll(/[^ ].*?(?:[.!?:](?= |$)|$)/g)) {
    if (!/[A-Za-z]/.test(m[0])) continue;
    const copy = [...lines];
    copy[i] = line.slice(0, m.index) + line.slice(m.index + m[0].length);
    total++;
    if (!run(copy.join('\n'))) { missed++; console.log(`MISSED delete ${i + 1}: ${m[0].slice(0, 80)}`); }
  }
});
console.log(`C: sentence deletions ${total}, missed ${missed}`);
