// translate-skill-dlc unit checks (check.json "extra"): step numbers other files cite, the self-flag trigger numbering,
// and the deliberate drop of the old Korean agent output-section name "plan 반영용 요약".
module.exports = ({ en, lines, bad }) => {
  const a = lines.findIndex((l) => l.startsWith('## structural full pipeline'));
  const b = lines.findIndex((l, i) => i > a && l.startsWith('## '));
  const steps = lines.slice(a, b).map((l) => (l.match(/^(\d+) +\S/) || [])[1]).filter(Boolean).map(Number);
  if (steps.join(',') !== Array.from({ length: 17 }, (_, i) => i).join(',')) bad(`pipeline steps: ${steps.join(',')}`);
  const s = lines.findIndex((l) => l.startsWith('## ⚠️ self-flag'));
  const trig = lines.slice(s, s + 10).map((l) => (l.match(/^ {2}(\d+)\. /) || [])[1]).filter(Boolean).map(Number);
  if (trig.join(',') !== '1,2,3,4') bad(`self-flag triggers: ${trig.join(',')}`);
  if (en.includes('plan 반영용 요약')) bad('old Korean name "plan 반영용 요약" must be gone (all four agents are English)');
  if ((en.match(/"Summary for the plan"/g) || []).length !== 1) bad('"Summary for the plan" must occur exactly once');
};
