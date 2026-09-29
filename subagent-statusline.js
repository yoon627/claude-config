#!/usr/bin/env node
// ~/.claude/subagent-statusline.js — Claude Code subagentStatusLine command
// 입력: {columns, tasks: [{id, name, description, status, startTime, tokenCount, contextWindowSize, ...}]}
// 출력: 바꿀 행마다 {"id", "content"} JSON 한 줄(id·content 는 문자열 — 아니면 그 줄만 버려진다).
// 내보내지 않은 행은 기본 표시(name · description · tokens)로 남는다.
// https://code.claude.com/docs/en/statusline#subagent-status-lines

const SEP = ' · ';

// columns 는 터미널 칸 수다. 글자(grapheme) 단위로 세고 자른다 — 한글·CJK·전각·이모지 표현은 2칸,
// 결합 문자만으로 된 조각은 0칸. 이모지 ZWJ 시퀀스나 é 같은 결합을 중간에서 끊지 않기 위해서다.
const WIDE = /[\u1100-\u115f\u2e80-\ua4cf\uac00-\ud7a3\uf900-\ufaff\ufe30-\ufe4f\uff00-\uff60\uffe0-\uffe6\u{20000}-\u{3fffd}\ufe0f]|\p{Emoji_Presentation}/u;
const ZERO = /^[\p{Mn}\p{Me}\p{Cf}]+$/u;
const segmenter = typeof Intl.Segmenter === 'function' ? new Intl.Segmenter() : null;
const graphemes = (s) => (segmenter ? Array.from(segmenter.segment(s), (g) => g.segment) : Array.from(s));
const cells = (g) => (WIDE.test(g) ? 2 : ZERO.test(g) ? 0 : 1);
const width = (s) => graphemes(s).reduce((w, g) => w + cells(g), 0);

// cols 칸 안에 들도록 글자 단위로 자르고 '…' 를 붙인다.
function clip(s, cols) {
  if (width(s) <= cols) return s;
  let out = '';
  let w = 0;
  for (const g of graphemes(s)) {
    if (w + cells(g) > cols - 1) break;
    out += g;
    w += cells(g);
  }
  return out + '…';
}

const clean = (v) => String(v).replace(/[\u0000-\u001f\u007f]+/g, ' ').trim();

// tokenCount 는 출력 토큰을 겹쳐 세 모델 한도를 넘을 수 있어 비율은 100% 에서 자른다(근사치).
function tokens(task) {
  const n = task.tokenCount;
  if (typeof n !== 'number' || !Number.isFinite(n) || n < 0) return '';
  const count = n >= 1000 ? (n / 1000).toFixed(1) + 'k tok' : n + ' tok';
  const window = task.contextWindowSize;
  return typeof window === 'number' && window > 0 ? count + ' (' + Math.min(100, Math.round((n / window) * 100)) + '%)' : count;
}

// startTime 은 epoch ms. 0·음수·미래 값은 경과를 모르는 것으로 본다. 입력에 종료 시각이 없어
// 끝난 task 는 행이 남아 있는 동안(약 30초) 경과가 계속 늘어나므로, 진행 중일 때만 붙인다.
function elapsed(task, now) {
  const start = task.startTime;
  if (task.status && task.status !== 'running' && task.status !== 'pending') return '';
  if (typeof start !== 'number' || !Number.isFinite(start) || start <= 0 || start > now) return '';
  const sec = Math.floor((now - start) / 1000);
  return Math.floor(sec / 60) + 'm ' + (sec % 60) + 's';
}

// 폭을 넘으면 description 부터 줄이고, 그래도 넘으면 끝을 자른다.
function fit(parts, descIndex, columns) {
  const text = parts.join(SEP);
  if (width(text) <= columns || descIndex < 0) return clip(text, columns);
  const rest = parts.filter((_, i) => i !== descIndex);
  const room = columns - width(rest.join(SEP)) - SEP.length;
  const shrunk = room >= 2 ? parts.map((p, i) => (i === descIndex ? clip(p, room) : p)) : rest;
  return clip(shrunk.join(SEP), columns);
}

// name 은 이름을 등록한 subagent 에만 온다(기본 표시는 이름이 없으면 agent 종류를 쓰지만 입력에는 그 값이 없다).
function rowContent(task, columns, now) {
  const name = task.name ? clean(task.name) : '';
  const description = task.description ? clean(task.description) : '';
  const parts = name ? [name] : [];
  const descIndex = description ? parts.push(description) - 1 : -1;
  for (const p of [task.status && clean(task.status), tokens(task), elapsed(task, now)]) if (p) parts.push(p);
  return fit(parts, descIndex, columns);
}

const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  let input = null;
  try { input = JSON.parse(Buffer.concat(chunks).toString()); } catch (_) {}
  const tasks = input && Array.isArray(input.tasks) ? input.tasks : [];
  const columns = input && typeof input.columns === 'number' ? input.columns : Infinity;
  const now = Date.now();
  const rows = [];
  // 폭이 0 이면(좁은 터미널) 내보내지 않고 기본 표시에 맡긴다 — 빈 content 는 행을 숨긴다.
  for (const task of columns > 0 ? tasks : []) {
    if (!task || typeof task.id !== 'string' || !task.id) continue;
    try { rows.push(JSON.stringify({ id: task.id, content: rowContent(task, columns, now) })); } catch (_) {}
  }
  if (rows.length) process.stdout.write(rows.join('\n') + '\n');
});
