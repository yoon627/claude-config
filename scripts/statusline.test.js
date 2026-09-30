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

// 가짜 HOME: 실행이 실제 홈 디렉토리의 파일을 읽거나 쓰지 않게.
const HOME = fs.mkdtempSync(path.join(os.tmpdir(), 'statusline-test-'));

function run(script, input, env = {}) {
  const r = spawnSync(process.execPath, [script], {
    input: typeof input === 'string' ? input : JSON.stringify(input),
    env: { ...process.env, HOME, USERPROFILE: HOME, ...env },
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
    for (const input of ['null', '', '{nope', '[]', '{"rate_limits":5}', '{"rate_limits":{"five_hour":null,"seven_day":"x"}}',
      '{"model":{"display_name":{"toString":1}},"rate_limits":{"seven_day":{"used_percentage":{"toString":1}}}}']) run(script, input);
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

// 쿼터 조각: TZ 를 고정해 리셋 시각 표기를 결정적으로 본다.
const at2030 = Date.UTC(2026, 0, 1, 20, 30) / 1000;
const runStatus = (input, home = HOME) => run(STATUS, input, { HOME: home, USERPROFILE: home, TZ: 'UTC' });

ok('claude 쿼터: 남은 % 와 리셋 시각, 둘 중 하나만 있으면 그것만', () => {
  const model = { display_name: 'Opus' };
  assert.ok(runStatus({ model, rate_limits: { five_hour: { used_percentage: 47.4, resets_at: at2030 } } }).includes('Opus 53%(20:30)'));
  assert.ok(runStatus({ model, rate_limits: { five_hour: { used_percentage: 110 } } }).includes('Opus 0%'));
  assert.ok(runStatus({ rate_limits: { five_hour: { resets_at: at2030 } } }).includes('claude (20:30)'));
  assert.ok(!runStatus({ model, rate_limits: { five_hour: {} } }).includes('Opus'));
});

ok('claude 주간 쿼터: 5시간 조각 뒤에 wk 남은 % 만(리셋 시각 없이), 5시간 창이 없어도 레이블은 붙인다', () => {
  const model = { display_name: 'Opus' };
  const seven_day = { used_percentage: 28, resets_at: at2030 };
  assert.strictEqual(runStatus({ model, rate_limits: { five_hour: { used_percentage: 47.4, resets_at: at2030 }, seven_day } }),
    'Opus 53%(20:30) wk 72%');
  assert.strictEqual(runStatus({ model, rate_limits: { seven_day } }), 'Opus wk 72%');
  assert.strictEqual(runStatus({ model, rate_limits: { seven_day: { resets_at: at2030 } } }), '');
  // 숫자가 아닌 값은 없는 것으로 본다 — 그 창만 빠지고 다른 창은 남는다.
  assert.strictEqual(runStatus({ model, rate_limits: { five_hour: { used_percentage: 47.4, resets_at: at2030 },
    seven_day: { used_percentage: { toString: 1 }, resets_at: '2026-01-03' } } }), 'Opus 53%(20:30)');
});

ok('codex 쿼터 캐시가 남아 있어도 codex 조각을 그리지 않고 refresh 도 띄우지 않는다', () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'statusline-codex-'));
  try {
    const cache = path.join(home, '.claude', 'cache');
    fs.mkdirSync(cache, { recursive: true });
    fs.writeFileSync(path.join(cache, 'codex-quota.json'), JSON.stringify({ fetchedAt: 0,
      primary: { usedPercent: 20, resetsAt: at2030 }, secondary: { usedPercent: 79, resetsAt: at2030 } }));
    assert.strictEqual(runStatus({}, home), '');
    assert.deepStrictEqual(fs.readdirSync(cache), ['codex-quota.json']);
  } finally {
    fs.rmSync(home, { recursive: true, force: true });
  }
});

fs.rmSync(HOME, { recursive: true, force: true });
console.log(`statusline.test.js: ${n} tests passed`);
