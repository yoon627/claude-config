#!/usr/bin/env node
// dlc-doc-drift 순수 모듈 단위테스트 (node 내장 assert, 의존 0).
// 실행: node scripts/dlc-doc-drift.test.js  (CI lint.yml 에서 호출)
'use strict';
const assert = require('assert');
const d = require('./dlc-doc-drift.js');

let n = 0;
const ok = (name, fn) => { fn(); n++; };

// --- resolveRoot: home(~/.claude) 기준. worktree / main / 타repo(null) ---
const HOME = 'C:/Users/u';
const WT = 'C:/Users/u/.claude/.claude/worktrees/doc-drift-guard';
const R = 'C:/Users/u/.claude';
const root = (cwd) => d.resolveRoot(cwd, HOME);
ok('worktree root from subdir', () => assert.strictEqual(root(WT + '/scripts'), WT));
ok('worktree root backslash', () => assert.strictEqual(root(WT.replace(/\//g, '\\')), WT));
ok('main .claude root', () => assert.strictEqual(root(R), R));
ok('main .claude subdir', () => assert.strictEqual(root(R + '/scripts'), R));
ok('non-home repo dir → null', () => assert.strictEqual(root('C:/work/other-repo'), null));
ok('other-repo .claude → null', () => assert.strictEqual(root('C:/work/other-repo/.claude/scripts'), null));
ok('empty → null', () => assert.strictEqual(root(''), null));

// --- classify: trigger / target / null (root 기준 정확 경로) ---
ok('scripts js trigger', () => assert.strictEqual(d.classify(R + '/scripts/x.js', R), 'readme-trigger'));
ok('top-level js trigger', () => assert.strictEqual(d.classify(R + '/statusline.js', R), 'readme-trigger'));
ok('agents md trigger', () => assert.strictEqual(d.classify(R + '/agents/a.md', R), 'readme-trigger'));
ok('commands md trigger', () => assert.strictEqual(d.classify(R + '/commands/x.md', R), 'readme-trigger'));
ok('skill trigger', () => assert.strictEqual(d.classify(R + '/skills/dlc/SKILL.md', R), 'readme-trigger'));
ok('settings trigger', () => assert.strictEqual(d.classify(R + '/settings.json', R), 'readme-trigger'));
ok('root CLAUDE trigger', () => assert.strictEqual(d.classify(R + '/CLAUDE.md', R), 'readme-trigger'));
ok('root README target', () => assert.strictEqual(d.classify(R + '/README.md', R), 'readme-target'));
ok('wiki page trigger', () => assert.strictEqual(d.classify(R + '/wiki/pages/concept/x.md', R), 'index-trigger'));
ok('wiki index target', () => assert.strictEqual(d.classify(R + '/wiki/index.md', R), 'index-target'));
// FP guards
ok('sub README not target', () => assert.strictEqual(d.classify(R + '/skills/dlc/README.md', R), null));
ok('docs md not trigger', () => assert.strictEqual(d.classify(R + '/docs/codex-review.md', R), null));
ok('nested scripts not trigger', () => assert.strictEqual(d.classify(R + '/scripts/sub/x.js', R), null));
ok('outside root null', () => assert.strictEqual(d.classify('C:/other/scripts/x.js', R), null));

// --- applyChange: dirty 전이 + same-turn 순서 (cwd=R, home=HOME) ---
ok('trigger sets readmeDirty', () => {
  const data = { readmeDirty: false, indexDirty: false };
  d.applyChange(data, R + '/scripts/x.js', R, HOME);
  assert.strictEqual(data.readmeDirty, true);
});
ok('target clears readmeDirty', () => {
  const data = { readmeDirty: true, indexDirty: false };
  d.applyChange(data, R + '/README.md', R, HOME);
  assert.strictEqual(data.readmeDirty, false);
});
ok('same-turn README-first stays dirty', () => {
  const data = { readmeDirty: false, indexDirty: false };
  d.applyChange(data, R + '/README.md', R, HOME);     // README 먼저
  assert.strictEqual(data.readmeDirty, false);
  d.applyChange(data, R + '/scripts/x.js', R, HOME);  // surface 나중
  assert.strictEqual(data.readmeDirty, true);         // false negative 없음
});
ok('wiki dirty transition', () => {
  const data = { readmeDirty: false, indexDirty: false };
  d.applyChange(data, R + '/wiki/pages/concept/x.md', R, HOME);
  assert.strictEqual(data.indexDirty, true);
  d.applyChange(data, R + '/wiki/index.md', R, HOME);
  assert.strictEqual(data.indexDirty, false);
});
ok('root=null no change', () => {
  const data = { readmeDirty: false, indexDirty: false };
  d.applyChange(data, 'C:/other/scripts/x.js', 'C:/other', HOME);
  assert.strictEqual(data.readmeDirty, false);
});

// --- applyChange: trigger 파일 detail 기록 (신호 detail 용, repo-relative) ---
ok('trigger records readmeTrigger rel', () => {
  const data = { readmeDirty: false, indexDirty: false };
  d.applyChange(data, R + '/skills/dlc/SKILL.md', R, HOME);
  assert.strictEqual(data.readmeTrigger, 'skills/dlc/SKILL.md');
});
ok('target clears readmeTrigger', () => {
  const data = { readmeDirty: true, readmeTrigger: 'CLAUDE.md', indexDirty: false };
  d.applyChange(data, R + '/README.md', R, HOME);
  assert.strictEqual(data.readmeTrigger, null);
});
ok('last trigger wins in readmeTrigger', () => {
  const data = { readmeDirty: false, indexDirty: false };
  d.applyChange(data, R + '/CLAUDE.md', R, HOME);
  d.applyChange(data, R + '/scripts/x.js', R, HOME);
  assert.strictEqual(data.readmeTrigger, 'scripts/x.js');
});
ok('index trigger records + clears', () => {
  const data = { readmeDirty: false, indexDirty: false };
  d.applyChange(data, R + '/wiki/pages/concept/x.md', R, HOME);
  assert.strictEqual(data.indexTrigger, 'wiki/pages/concept/x.md');
  d.applyChange(data, R + '/wiki/index.md', R, HOME);
  assert.strictEqual(data.indexTrigger, null);
});

// --- evaluate: dirty → 메시지 ---
ok('clean → no message', () => assert.deepStrictEqual(d.evaluate({ readmeDirty: false, indexDirty: false }), []));
ok('readme dirty → 1 msg', () => assert.strictEqual(d.evaluate({ readmeDirty: true, indexDirty: false }).length, 1));
ok('both dirty → 2 msg', () => assert.strictEqual(d.evaluate({ readmeDirty: true, indexDirty: true }).length, 2));

console.log(`dlc-doc-drift.test.js: ${n} assertions passed`);
