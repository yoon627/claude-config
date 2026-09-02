#!/usr/bin/env node
// dlc-task-router hook 동작 테스트 — 실제 진입점(stdin JSON → stdout)을 spawn 으로 실행.
// 실행: node scripts/dlc-task-router.test.js  (CI lint.yml 에서 호출)
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const ledger = require('./dlc-ledger.js');

const SCRIPT = path.join(__dirname, 'dlc-task-router.js');
const SESSION = `dlc-router-test-${process.pid}`;

function run(prompt) {
  const r = spawnSync(process.execPath, [SCRIPT], {
    input: JSON.stringify({ session_id: SESSION, cwd: __dirname, prompt }),
    env: { ...process.env, CLAUDE_DLC_SIGNAL_OFF: '1' },
    encoding: 'utf8',
  });
  assert.strictEqual(r.status, 0, `exit ${r.status}: ${r.stderr}`);
  if (!r.stdout) return '';
  return JSON.parse(r.stdout).hookSpecificOutput.additionalContext;
}

let n = 0;
const ok = (name, fn) => { fn(); n++; };

// 하네스가 subagent 완료 시 user 턴으로 넣는 실제 형태(transcript 실측): 래퍼 없는 최상위 태그.
const TASK_NOTIFICATION =
  '<task-notification>\n<task-id>abc123</task-id>\n<status>completed</status>\n' +
  '<summary>Agent "Review fix" finished — 재현 테스트가 failing, 회귀 버그 의심. 렌더링 검증 필요</summary>\n' +
  '</task-notification>';
// system-reminder 래퍼가 붙는 형태(다른 하네스 이벤트)도 같은 규칙으로 걷어낸다.
const REMINDER = '<system-reminder>\n[NOT USER INPUT]\n' + TASK_NOTIFICATION + '\n</system-reminder>';

try {
  ok('user debugging prompt → investigation', () =>
    assert.ok(run('로그인이 안 돼요, 재현해보니 500 에러가 나요').includes('[dlc:investigation]')));
  ok('user render prompt → grounding', () =>
    assert.ok(run('차트를 그려서 시각화 해줘').includes('[dlc:grounding]')));
  ok('plain prompt → silent', () => assert.strictEqual(run('README 오타 고쳐줘'), ''));
  ok('task-notification only → silent', () => assert.strictEqual(run(TASK_NOTIFICATION), ''));
  ok('reminder-wrapped notification only → silent', () => assert.strictEqual(run(REMINDER), ''));
  ok('reminder-prefixed user prompt without keywords → silent', () =>
    assert.strictEqual(run(REMINDER + '\n\n다음 단계 진행해줘'), ''));
  ok('reminder-prefixed user prompt with keywords → investigation', () =>
    assert.ok(run(REMINDER + '\n\n실제로 버그가 재현돼요').includes('[dlc:investigation]')));
  ok('user prompt with trailing notification → investigation', () =>
    assert.ok(run('앱이 튕겨요\n\n' + TASK_NOTIFICATION).includes('[dlc:investigation]')));
  ok('upper-case tag is stripped too', () =>
    assert.strictEqual(run(TASK_NOTIFICATION.toUpperCase()), ''));
  ok('empty prompt → silent', () => assert.strictEqual(run(''), ''));

  ok('notification turn keeps evidence ledger (no reset)', () => {
    ledger.write(SESSION, { ...ledger.DEFAULT, changed: true, readmeDirty: true });
    run(TASK_NOTIFICATION);
    const d = ledger.read(SESSION);
    assert.strictEqual(d.changed, true);
    assert.strictEqual(d.readmeDirty, true);
  });
  ok('user turn resets evidence ledger', () => {
    ledger.write(SESSION, { ...ledger.DEFAULT, changed: true });
    run(REMINDER + '\n\n다음 단계 진행해줘');
    assert.strictEqual(ledger.read(SESSION).changed, false);
  });
} finally {
  try { fs.unlinkSync(ledger.ledgerPath(SESSION)); } catch { /* 없으면 무시 */ }
}
console.log(`dlc-task-router.test: ${n} passed`);
