#!/usr/bin/env node
// check-dedupe.js — the rule-loss-0 gate of the CLAUDE.md dedupe (plan 2026-11-07-claude-md-dedupe).
//
//   node check-dedupe.js [--base <ref>] [--mutate] [--table]
//
// Reads manifest.json beside this file: rows {id, section, oldLine, deleted, kind, dest:{file, quote}|null,
// pointer}. Every text segment that `<base>:CLAUDE.md` has and the working-tree CLAUDE.md does not (a
// token-level diff of each changed line) must be inside some row's `deleted` (whitespace-normalised),
// so nothing can be removed outside the manifest. Each row's dest.quote must be in dest.file as is and
// each pointer must be in the new CLAUDE.md, and every phrase of keep.json (always-on rules and pinned
// phrases) must still be in the new CLAUDE.md verbatim. --mutate drops each manifest row in turn
// (coverage must fail) and re-deletes each keep.json phrase from the new text in turn (the keep check
// must fail), so a check that proves nothing is caught. --table prints the manifest as the markdown
// table for the plan log. Exit 0 PASS · 1 FAIL · 2 error.
'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const HERE = __dirname;
const ROOT = path.resolve(HERE, '..', '..');
const args = process.argv.slice(2);
const opt = (name, dflt) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : dflt; };
const BASE = opt('--base', '');
const MUTATE = args.includes('--mutate');
const TABLE = args.includes('--table');

const norm = (s) => s.replace(/\s+/g, ' ').trim();
const tokens = (s) => s.match(/[\p{L}\p{N}_`]+|[^\s\p{L}\p{N}_`]/gu) || [];
// coverage compares word tokens only: punctuation deleted around a clause is not a rule. A segment is
// covered when its whole-token sequence occurs in the deleted text of a row for the same old line,
// so a stray "not"/"only"/section number elsewhere in the manifest cannot cover it.
const words = (s) => tokens(s).filter((t) => /[\p{L}\p{N}_`]/u.test(t));
const tnorm = (s) => ` ${words(s).join(' ')} `;

function lcsKeep(a, b) { // -> boolean[] over a: token kept (part of the LCS with b)
  const n = a.length; const m = b.length;
  const dp = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) {
    dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  }
  const keep = new Array(n).fill(false);
  let i = 0; let j = 0;
  while (i < n && j < m) {
    if (a[i] === b[j]) { keep[i] = true; i++; j++; } else if (dp[i + 1][j] >= dp[i][j + 1]) i++; else j++;
  }
  return keep;
}

// deletedSegments(oldText, newText) -> [{line, text}]: runs of old tokens that are not in the new text,
// with the 1-based old line they came from
function deletedSegments(oldText, newText) {
  const oldLines = oldText.split('\n'); const newLines = newText.split('\n');
  const keepLine = lcsKeep(oldLines, newLines);
  const newSet = new Set(newLines);
  const segs = [];
  // a removed old line that still exists verbatim elsewhere in the new file is a move, not a deletion
  const removed = oldLines.map((l, k) => ({ line: k + 1, text: l })).filter((r) => !keepLine[r.line - 1] && !newSet.has(r.text));
  const added = newLines.filter((l) => !oldLines.includes(l));
  // pair each removed line with the most similar added line (by shared tokens); unpaired = whole line deleted
  for (const { line, text } of removed) {
    const ot = tokens(text);
    let best = null; let bestScore = 0;
    for (const cand of added) {
      const ct = new Set(tokens(cand));
      const score = ot.filter((t) => ct.has(t)).length / Math.max(ot.length, 1);
      if (score > bestScore) { bestScore = score; best = cand; }
    }
    if (!best || bestScore < 0.3) { segs.push({ line, text }); continue; }
    const keep = lcsKeep(ot, tokens(best));
    let run = [];
    for (let k = 0; k <= ot.length; k++) {
      if (k < ot.length && !keep[k]) run.push(ot[k]);
      else if (run.length) { segs.push({ line, text: run.join(' ') }); run = []; }
    }
    // the words of the paired new line that the old line lacks = what was added on this line
    const bt = tokens(best); const keepB = lcsKeep(bt, ot);
    const addedWords = bt.filter((tok, k) => !keepB[k]);
    if (addedWords.length) segs.push({ line, text: addedWords.join(' '), added: true });
  }
  return segs;
}

// only punctuation and symbols are trivial — "no", "or" and a section number are words that change a rule
const trivial = (seg) => words(seg).length === 0;

function load() {
  const manifest = JSON.parse(fs.readFileSync(path.join(HERE, 'manifest.json'), 'utf8'));
  const keep = JSON.parse(fs.readFileSync(path.join(HERE, 'keep.json'), 'utf8'));
  const base = BASE || execFileSync('git', ['-C', ROOT, 'merge-base', 'main', 'HEAD'], { encoding: 'utf8' }).trim();
  const oldText = execFileSync('git', ['-C', ROOT, 'show', `${base}:CLAUDE.md`], { encoding: 'utf8' });
  const newText = fs.readFileSync(path.join(ROOT, 'CLAUDE.md'), 'utf8');
  return { manifest, keep, oldText, newText };
}

function check(manifest, oldText, newText, files, keep = []) {
  const fails = [];
  for (const k of keep) if (!norm(newText).includes(norm(k))) fails.push(`keep phrase missing from the new CLAUDE.md: «${k.slice(0, 120)}»`);
  // Per old line, the words that disappeared must equal, in order, the words of the manifest rows for
  // that line: a row must be the exact deleted text (not the clause it came from), and no word outside
  // the rows may vanish — a second "not" or "without" is caught even when the row text holds the word.
  // Added words are checked the same way against the rows' pointers (new words not in any pointer would
  // widen or soften a rule), as a set because a pointer may also repeat words the line already had.
  const gone = {}; const allowed = {}; const addedOn = {};
  for (const seg of deletedSegments(oldText, newText)) {
    if (trivial(seg.text)) continue;
    if (seg.added) { addedOn[seg.line] = (addedOn[seg.line] || []).concat(words(seg.text)); continue; }
    gone[seg.line] = (gone[seg.line] || []).concat(words(seg.text));
  }
  for (const r of manifest) allowed[r.oldLine] = (allowed[r.oldLine] || []).concat(words(r.deleted));
  for (const line of new Set([...Object.keys(gone), ...Object.keys(allowed)])) {
    const g = (gone[line] || []).join(' '); const a = (allowed[line] || []).join(' ');
    if (g !== a) fails.push(`old line ${line}: deleted words «${g.slice(0, 160)}» ≠ manifest rows «${a.slice(0, 160)}»`);
  }
  for (const [line, ws] of Object.entries(addedOn)) {
    const pointerWords = new Set(manifest.filter((r) => String(r.oldLine) === line).flatMap((r) => words(r.pointer || '')));
    const stray = ws.filter((w) => !pointerWords.has(w));
    if (stray.length) fails.push(`old line ${line}: added words not in that line's pointers: «${stray.join(' ').slice(0, 160)}»`);
  }
  for (const r of manifest) {
    if (!r.id || !r.deleted || !r.kind) { fails.push(`row ${JSON.stringify(r).slice(0, 80)} lacks id/deleted/kind`); continue; }
    if (r.dest) {
      const content = files[r.dest.file];
      if (content === undefined) { fails.push(`${r.id}: dest file unreadable ${r.dest.file}`); continue; }
      if (!norm(content).includes(norm(r.dest.quote))) fails.push(`${r.id}: dest quote not found in ${r.dest.file}: «${norm(r.dest.quote).slice(0, 120)}»`);
    } else if (r.kind !== 'reason') {
      fails.push(`${r.id}: only kind "reason" may have no dest`);
    }
    if (r.pointer && !norm(newText).includes(norm(r.pointer))) fails.push(`${r.id}: pointer not in the new CLAUDE.md: «${r.pointer}»`);
  }
  return fails;
}

function readFiles(manifest, newText) {
  const files = {};
  for (const r of manifest) {
    if (!r.dest || files[r.dest.file] !== undefined) continue;
    const p = r.dest.file.startsWith('/') ? r.dest.file : path.join(ROOT, r.dest.file);
    try { files[r.dest.file] = r.dest.file === 'CLAUDE.md' ? newText : fs.readFileSync(p, 'utf8'); } catch { files[r.dest.file] = undefined; }
  }
  return files;
}

function main() {
  const { manifest, keep, oldText, newText } = load();
  if (TABLE) {
    console.log('| id | § | 옛 줄 | 지운 절 | 종류 | 남는 자리 «인용» | 남긴 포인터 |');
    console.log('|---|---|---|---|---|---|---|');
    for (const r of manifest) {
      const dest = r.dest ? `${r.dest.file}: «${norm(r.dest.quote).slice(0, 90)}»` : '(이유 설명 — 명령문은 그대로)';
      console.log(`| ${r.id} | ${r.section} | ${r.oldLine} | ${norm(r.deleted).slice(0, 110).replace(/\|/g, '\\|')} | ${r.kind} | ${dest.replace(/\|/g, '\\|')} | ${(r.pointer || '').replace(/\|/g, '\\|')} |`);
    }
    return 0;
  }
  const files = readFiles(manifest, newText);
  const fails = check(manifest, oldText, newText, files, keep);
  for (const f of fails) console.log(`FAIL ${f}`);
  const oldLen = oldText.length; const newLen = newText.length;
  console.log(`CLAUDE.md ${oldLen} -> ${newLen} chars (${oldLen - newLen} removed), manifest rows ${manifest.length}, keep phrases ${keep.length}`);
  if (fails.length) { console.log('check-dedupe: FAIL'); return 1; }
  console.log('check-dedupe: PASS');
  if (!MUTATE) return 0;
  let mutFails = 0; let cases = 0;
  for (const r of manifest) {
    cases++;
    const without = manifest.filter((x) => x !== r);
    if (check(without, oldText, newText, files).length === 0) {
      mutFails++; console.log(`MUTANT SURVIVED dropping row ${r.id}: its deleted text is not needed for coverage`);
    }
  }
  for (const k of keep) {
    cases++;
    const cut = newText.replace(k, '');
    if (cut === newText) { mutFails++; console.log(`MUTANT SURVIVED: keep phrase is not verbatim in the new text, so it cannot be re-deleted: «${k.slice(0, 80)}»`); continue; }
    if (check(manifest, oldText, cut, files, keep).length === 0) { mutFails++; console.log(`MUTANT SURVIVED re-deleting keep phrase «${k.slice(0, 80)}»`); }
  }
  // a deleted negation, modal or number anywhere in the file must fail coverage on its own (keep list off)
  const NEG = /\b(no|not|never|only|must|always|without|every|before|after|unless|except|[0-9]+)\b/u;
  const lines = newText.split('\n');
  const changedLines = new Set(manifest.map((r) => r.oldLine));
  const sample = lines.map((l, i) => i + 1).filter((n, i) => changedLines.has(n) || i % 7 === 0);
  for (const n of sample) {
    const m = NEG.exec(lines[n - 1]);
    if (!m) continue;
    cases++;
    const cut = [...lines]; cut[n - 1] = lines[n - 1].slice(0, m.index) + lines[n - 1].slice(m.index + m[0].length);
    if (check(manifest, oldText, cut.join('\n'), files, []).length === 0) { mutFails++; console.log(`MUTANT SURVIVED deleting "${m[0]}" from new line ${n}`); }
  }
  console.log(`mutation: ${cases} cases, ${mutFails} survived`);
  return mutFails ? 1 : 0;
}

try { process.exit(main()); } catch (e) { console.error(`check-dedupe: ${e.message}`); process.exit(2); }
