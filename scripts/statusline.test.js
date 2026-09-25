#!/usr/bin/env node
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const STATUS = path.join(ROOT, 'statusline.js');
const SUB = path.join(ROOT, 'subagent-statusline.js');

let n = 0;
const ok = (name, fn) => { fn(); n++; };

// 가짜 HOME + 신선한 codex 캐시: statusline 이 실제 캐시를 읽거나 refresh 를 spawn 하지 않게.
const HOME = fs.mkdtempSync(path.join(os.tmpdir(), 'statusline-test-'));
fs.mkdirSync(path.join(HOME, '.claude', 'cache'), { recursive: true });
fs.writeFileSync(path.join(HOME, '.claude', 'cache', 'codex-quota.json'), JSON.stringify({ fetchedAt: Date.now() }));

function run(script, input) {
  const r = spawnSync(process.execPath, [script], {
    input: typeof input === 'string' ? input : JSON.stringify(input),
    env: { ...process.env, HOME, USERPROFILE: HOME },
    encoding: 'utf8',
    timeout: 10000,
  });
  assert.strictEqual(r.status, 0, r.stderr);
  return r.stdout;
}
const rows = (input) => run(SUB, input).trim().split('\n').filter(Boolean).map((l) => JSON.parse(l));
// 테스트 쪽 폭 계산: 한글 음절과 ✅ 는 2칸(이 테스트가 쓰는 문자 범위만).
const width = (s) => Array.from(s).reduce((w, ch) => w + (/[가-힣✅]/.test(ch) ? 2 : 1), 0);

ok('null·빈·깨진 stdin 에서 두 스크립트 모두 exit 0', () => {
  for (const script of [STATUS, SUB]) {
    for (const input of ['null', '', '{nope', '[]']) run(script, input);
  }
});

ok('subagent: 문자열 id 를 가진 task 마다 {id, content} 한 줄 — 없는 조각은 뺀다', () => {
  const now = Date.now();
  const tasks = [
    { id: 't1', name: 'code-reviewer', description: 'Review\nchange', status: 'running',
      startTime: now - 192100, tokenCount: 48200, contextWindowSize: 200000 },
    { id: 't2', name: 'x', description: ' \n ', status: 'completed', startTime: now - 60000, tokenCount: 999 },
    { id: 't3', name: 'over', tokenCount: 300000, contextWindowSize: 200000, startTime: 0 },
    { id: 't4', description: 'no name', status: 'running', startTime: now + 60000 },
    { id: 7, name: 'numeric-id' },
    { name: 'no-id', status: 'running' },
  ];
  const got = rows({ columns: 200, tasks });
  assert.deepStrictEqual(got.map((r) => r.id), ['t1', 't2', 't3', 't4']);
  assert.match(got[0].content, /^code-reviewer · Review change · running · 48\.2k tok \(24%\) · 3m 1[23]s$/);
  assert.strictEqual(got[1].content, 'x · completed · 999 tok'); // 끝난 task 는 경과를 붙이지 않는다
  assert.strictEqual(got[2].content, 'over · 300.0k tok (100%)');
  assert.strictEqual(got[3].content, 'no name · running');
  assert.deepStrictEqual(rows({ columns: 0, tasks }), []); // 폭이 없으면 기본 표시에 맡긴다
});

ok('subagent: columns 를 넘으면 description 부터 줄인다 — 한글은 2칸으로 센다', () => {
  const now = Date.now();
  for (const description of ['Review the whole change set in detail please', '변경 전체를 아주 자세히 검토해 주세요', '✅'.repeat(20)]) {
    const [row] = rows({ columns: 60, tasks: [{ id: 't1', name: 'code-reviewer', description, status: 'running',
      startTime: now - 192100, tokenCount: 48200 }] });
    assert.ok(width(row.content) <= 60, `${width(row.content)}: ${row.content}`);
    assert.ok(row.content.startsWith('code-reviewer · ') && /… · running · 48\.2k tok · 3m 1[23]s$/.test(row.content), row.content);
  }
});

fs.rmSync(HOME, { recursive: true, force: true });
console.log(`statusline.test.js: ${n} tests passed`);
