#!/usr/bin/env node
// plan-match — branch → §10 plan 매칭 순수 모듈 테스트.
//
// 이 규칙은 session-brief(닫히지 않은 plan 신호)와 dlc-early-stop(plan drift 축) 두 소비자가
// 공유한다. 한쪽만 바뀌어 어긋나는 것을 막는 것이 모듈화의 목적이므로 규칙 자체를 여기서 잠근다.
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { anchorMatches, activePlanPath } = require('./plan-match.js');

let n = 0;
const ok = (name, fn) => { fn(); n++; };

// --- anchorMatches (§10 매칭 규칙) ---
ok('정확일치', () => assert.strictEqual(anchorMatches('my-task', 'my-task'), true));
ok('worktree- prefix', () => assert.strictEqual(anchorMatches('worktree-my-task', 'my-task'), true));
ok('접미 앵커(날짜 prefix 브랜치)', () =>
  assert.strictEqual(anchorMatches('feat-my-task', 'my-task'), true));
ok('부분일치는 매칭 아님 — 앵커가 `-` 경계여야', () =>
  assert.strictEqual(anchorMatches('my-task-2', 'my-task'), false));
ok('무관 브랜치', () => assert.strictEqual(anchorMatches('other', 'my-task'), false));
ok('빈 slug/branch 는 false (전체 매칭 폭주 방지)', () => {
  assert.strictEqual(anchorMatches('any', ''), false);
  assert.strictEqual(anchorMatches('', 'slug'), false);
});

// --- activePlanPath ---
function makeRoot(plans) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pm-'));
  for (const [dir, file] of plans) {
    fs.mkdirSync(path.join(root, 'plans', dir), { recursive: true });
    fs.writeFileSync(path.join(root, 'plans', dir, file), '---\nstatus: in_progress\n---\n');
  }
  return root;
}

ok('매칭되는 plan 경로를 찾는다', () => {
  const root = makeRoot([['2026-09-07-my-task', 'my-task-plan.md']]);
  const p = activePlanPath(root, 'my-task');
  assert.ok(p && p.endsWith(path.join('2026-09-07-my-task', 'my-task-plan.md')), String(p));
});

ok('매칭 없으면 null — plan 없는 흐름에서 축이 발동하지 않는다', () => {
  const root = makeRoot([['2026-09-07-other', 'other-plan.md']]);
  assert.strictEqual(activePlanPath(root, 'my-task'), null);
});

ok('plans/ 자체가 없으면 null (fail-open)', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pm-empty-'));
  assert.strictEqual(activePlanPath(root, 'my-task'), null);
});

ok('-plan.md 가 아닌 파일은 무시', () => {
  const root = makeRoot([['2026-09-07-my-task', 'notes.md']]);
  assert.strictEqual(activePlanPath(root, 'my-task'), null);
});

ok('root·branch 결측이면 null', () => {
  assert.strictEqual(activePlanPath(null, 'b'), null);
  assert.strictEqual(activePlanPath('/tmp', ''), null);
});

console.log(`plan-match.test.js: ${n} tests passed`);
