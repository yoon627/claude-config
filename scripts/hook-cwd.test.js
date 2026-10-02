#!/usr/bin/env node
// hook-cwd.js 테스트 — 시간 배수(scaleMs) 해석. readHookCwd 의 JSON·빈 입력 경로는 두 SessionStart 훅의 테스트가
// 실제 훅을 띄워 덮지만, 닫히지 않는 stdin 을 타이머가 끊는 경로는 자동 테스트가 없다.
'use strict';
const assert = require('assert');
const { scaleMs, TIME_SCALE_ENV } = require('./hook-cwd.js');

let n = 0;
const ok = (name, fn) => {
  fn();
  n++;
};

const scaled = (value) => scaleMs(2000, value === undefined ? {} : { [TIME_SCALE_ENV]: value });

ok('없거나 숫자가 아니면 운영 상한 그대로', () => {
  for (const v of [undefined, 'abc']) assert.strictEqual(scaled(v), 2000, `값 ${v}`);
});

ok('1 미만은 1 로 자른다 — 0 은 execFileSync 에서 상한 없음이다', () => {
  for (const v of ['', ' ', '0', '-5', '0.5', '-Infinity']) assert.strictEqual(scaled(v), 2000, `값 ${JSON.stringify(v)}`);
});

ok('배수를 곱하고 20 으로 자르며, execFileSync 가 받도록 정수로 낸다', () => {
  assert.strictEqual(scaled('10'), 20000);
  for (const v of ['1000', 'Infinity']) assert.strictEqual(scaled(v), 40000, `값 ${v}`);
  const odd = scaled('1.3333');
  assert.ok(Number.isInteger(odd), `정수가 아니다: ${odd}`);
});

ok('env 를 넘기지 않으면 process.env 를 읽는다 — 훅의 호출부가 쓰는 경로', () => {
  const saved = process.env[TIME_SCALE_ENV];
  try {
    process.env[TIME_SCALE_ENV] = '10';
    assert.strictEqual(scaleMs(2000), 20000);
  } finally {
    if (saved === undefined) delete process.env[TIME_SCALE_ENV];
    else process.env[TIME_SCALE_ENV] = saved;
  }
});

console.log(`hook-cwd.test.js: ${n} tests passed`);
