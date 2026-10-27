// Reads the "## 기계 대조" block of the bundle term table for check-translation.js and mut-translation.js.
// Returns { pairs: [[korean, english], …], errors: [message, …] }: the block is a ```text fence that opens before the next
// "## " heading (its lines may themselves start with "## "); every non-blank line in it must be "<Korean> => <English>",
// and an empty or unclosed block is an error.
const fs = require('fs');

module.exports = function readTermBlock(file) {
  const errors = [];
  const text = fs.readFileSync(file, 'utf8').replace(/\r\n/g, '\n');
  const start = text.search(/^## 기계 대조/m);
  if (start < 0) return { pairs: [], errors: [`term table has no "## 기계 대조" section: ${file}`] };
  const rest = text.slice(start + 1);
  const open = rest.indexOf('```text\n');
  const next = rest.search(/^## /m);
  if (open < 0 || (next >= 0 && next < open)) return { pairs: [], errors: ['term table "## 기계 대조" section has no ```text block'] };
  const body = rest.slice(open + '```text\n'.length);
  const close = body.search(/^```/m);
  if (close < 0) return { pairs: [], errors: ['term table block is not closed'] };
  const pairs = [];
  for (const line of body.slice(0, close).split('\n')) {
    if (!line.trim()) continue;
    const m = line.match(/^(\S.*?) => (\S.*)$/);
    if (!m) { errors.push(`term table line does not parse: ${line}`); continue; }
    pairs.push([m[1], m[2]]);
  }
  if (!pairs.length) errors.push('term table block is empty');
  return { pairs, errors };
};

module.exports.count = (haystack, needle) => {
  if (!needle) return 0;
  let n = 0;
  for (let i = haystack.indexOf(needle); i >= 0; i = haystack.indexOf(needle, i + needle.length)) n++;
  return n;
};
