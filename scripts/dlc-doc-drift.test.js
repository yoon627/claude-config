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
// 테스트 파일은 README 가 존재만 문서화(`x.js (+ .test.js)`) → 신규 추가일 때만 trigger
ok('scripts test js → new-only trigger', () =>
  assert.strictEqual(d.classify(R + '/scripts/x.test.js', R), 'readme-trigger-new'));
ok('top-level test js → new-only trigger', () =>
  assert.strictEqual(d.classify(R + '/x.test.js', R), 'readme-trigger-new'));
ok('nested test js not trigger', () => assert.strictEqual(d.classify(R + '/scripts/sub/x.test.js', R), null));
ok('backslash test js → new-only trigger', () =>
  assert.strictEqual(d.classify('C:\\Users\\u\\.claude\\scripts\\x.test.js', R), 'readme-trigger-new'));
// 경계: `.test.js` 접미가 아닌 이름은 일반 표면(readme-trigger)·비표면(null) 판정을 그대로 유지
ok('mytest.js is plain surface', () => assert.strictEqual(d.classify(R + '/scripts/mytest.js', R), 'readme-trigger'));
ok('x.testxjs is plain surface', () => assert.strictEqual(d.classify(R + '/scripts/x.testxjs.js', R), 'readme-trigger'));
ok('x.test.jsx not surface', () => assert.strictEqual(d.classify(R + '/scripts/x.test.jsx', R), null));
// `.mjs` 는 테스트든 아니든 표면이 아니다(`scripts/x.mjs` 도 null) — 그 대칭을 깨지 않는다
ok('x.test.mjs not surface', () => assert.strictEqual(d.classify(R + '/scripts/x.test.mjs', R), null));
ok('spec js → new-only trigger', () =>
  assert.strictEqual(d.classify(R + '/scripts/x.spec.js', R), 'readme-trigger-new'));
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

// --- applyChange: 테스트 파일은 신규 추가일 때만 dirty (기존 편집 오탐 제거) ---
ok('existing test file edit → not dirty', () => {
  const data = { readmeDirty: false, indexDirty: false };
  d.applyChange(data, R + '/scripts/x.test.js', R, HOME, () => false);
  assert.strictEqual(data.readmeDirty, false);
});
ok('new test file → dirty + trigger rel', () => {
  const data = { readmeDirty: false, indexDirty: false };
  d.applyChange(data, R + '/scripts/x.test.js', R, HOME, () => true);
  assert.strictEqual(data.readmeDirty, true);
  assert.strictEqual(data.readmeTrigger, 'scripts/x.test.js');
});
ok('no predicate → test file never dirty', () => {
  const data = { readmeDirty: false, indexDirty: false };
  d.applyChange(data, R + '/scripts/x.test.js', R, HOME);
  assert.strictEqual(data.readmeDirty, false);
});
ok('predicate receives rel/root', () => {
  const seen = [];
  d.applyChange({ readmeDirty: false, indexDirty: false }, R + '/scripts/x.test.js', R, HOME, (...a) => {
    seen.push(a);
    return false;
  });
  assert.deepStrictEqual(seen, [['scripts/x.test.js', R]]);
});
ok('predicate not consulted for non-test surface', () => {
  let calls = 0;
  const data = { readmeDirty: false, indexDirty: false };
  d.applyChange(data, R + '/scripts/x.js', R, HOME, () => { calls++; return false; });
  assert.strictEqual(calls, 0);
  assert.strictEqual(data.readmeDirty, true);
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

// --- covered-set: 동기화 끝난 surface 의 재편집은 재-dirty 시키지 않는다 ---
// 오탐 재현 경로(2026-08-12, 세션 2회): trigger → target(동기화) → 같은 trigger 재편집.
// 문서는 실제로 동기화돼 있는데 순서 기반 플래그가 다시 dirty 로 뒤집던 것.
const ledger = require('./dlc-ledger.js');
const fresh = () => ({ ...ledger.DEFAULT });

ok('README: 동기화 후 같은 파일 재편집 → dirty 아님', () => {
  const data = fresh();
  d.applyChange(data, R + '/scripts/x.js', R, HOME);
  d.applyChange(data, R + '/README.md', R, HOME);
  assert.strictEqual(data.readmeDirty, false);
  d.applyChange(data, R + '/scripts/x.js', R, HOME); // 재편집
  assert.strictEqual(data.readmeDirty, false);
});
ok('index: 동기화 후 같은 페이지 재편집 → dirty 아님', () => {
  const data = fresh();
  d.applyChange(data, R + '/wiki/pages/decision/a.md', R, HOME);
  d.applyChange(data, R + '/wiki/index.md', R, HOME);
  assert.strictEqual(data.indexDirty, false);
  d.applyChange(data, R + '/wiki/pages/decision/a.md', R, HOME); // 재편집
  assert.strictEqual(data.indexDirty, false);
});
ok('동기화 후 *새* surface → dirty (미탐 미도입)', () => {
  const data = fresh();
  d.applyChange(data, R + '/scripts/x.js', R, HOME);
  d.applyChange(data, R + '/README.md', R, HOME);
  d.applyChange(data, R + '/scripts/brand-new.js', R, HOME);
  assert.strictEqual(data.readmeDirty, true);
  assert.strictEqual(data.readmeTrigger, 'scripts/brand-new.js');
});
ok('여러 trigger 를 한 target 이 모두 커버', () => {
  const data = fresh();
  d.applyChange(data, R + '/wiki/pages/decision/a.md', R, HOME);
  d.applyChange(data, R + '/wiki/pages/decision/b.md', R, HOME);
  d.applyChange(data, R + '/wiki/index.md', R, HOME);
  d.applyChange(data, R + '/wiki/pages/decision/a.md', R, HOME);
  d.applyChange(data, R + '/wiki/pages/decision/b.md', R, HOME);
  assert.strictEqual(data.indexDirty, false);
});
ok('covered 는 축끼리 섞이지 않는다', () => {
  const data = fresh();
  d.applyChange(data, R + '/scripts/x.js', R, HOME);
  d.applyChange(data, R + '/README.md', R, HOME);
  d.applyChange(data, R + '/wiki/pages/decision/a.md', R, HOME);
  assert.strictEqual(data.indexDirty, true);   // index 축은 별개로 dirty
  assert.strictEqual(data.readmeDirty, false); // readme 축은 여전히 clean
});
ok('target 선행이어도 그 뒤 trigger 는 dirty (기존 계약 유지)', () => {
  const data = fresh();
  d.applyChange(data, R + '/README.md', R, HOME);
  d.applyChange(data, R + '/scripts/x.js', R, HOME);
  assert.strictEqual(data.readmeDirty, true);
});
ok('DEFAULT 오염 없음 — 세션 간 배열 공유 금지', () => {
  const a = fresh();
  const b = fresh();
  d.applyChange(a, R + '/scripts/x.js', R, HOME);
  d.applyChange(a, R + '/README.md', R, HOME);
  // a 에서 covered 로 넘어간 항목이 b·DEFAULT 로 새면 안 된다
  assert.deepStrictEqual(ledger.DEFAULT.readmeCovered, []);
  assert.deepStrictEqual(b.readmeCovered, []);
  d.applyChange(b, R + '/scripts/x.js', R, HOME);
  assert.strictEqual(b.readmeDirty, true); // b 는 covered 가 비어 있으므로 dirty
});
ok('covered 상한 50 — 무한 증가 방지', () => {
  const data = fresh();
  for (let i = 0; i < 60; i++) d.applyChange(data, `${R}/scripts/f${i}.js`, R, HOME);
  d.applyChange(data, R + '/README.md', R, HOME);
  assert.ok(data.readmeCovered.length <= 50, `covered=${data.readmeCovered.length}`);
});
ok('구 ledger(필드 부재)에서도 크래시 없음', () => {
  const data = { readmeDirty: false, indexDirty: false }; // covered/pending 없음
  d.applyChange(data, R + '/scripts/x.js', R, HOME);
  assert.strictEqual(data.readmeDirty, true);
  d.applyChange(data, R + '/README.md', R, HOME);
  assert.strictEqual(data.readmeDirty, false);
  d.applyChange(data, R + '/scripts/x.js', R, HOME);
  assert.strictEqual(data.readmeDirty, false);
});

// --- evaluate: dirty → 메시지 ---
ok('clean → no message', () => assert.deepStrictEqual(d.evaluate({ readmeDirty: false, indexDirty: false }), []));
ok('readme dirty → 1 msg', () => assert.strictEqual(d.evaluate({ readmeDirty: true, indexDirty: false }).length, 1));
ok('both dirty → 2 msg', () => assert.strictEqual(d.evaluate({ readmeDirty: true, indexDirty: true }).length, 2));

// --- evaluate + mtimeOf: 동기화 판정을 도구 종류가 아니라 **파일 상태**로 ---
// 배경: dirty 는 PostToolUse 의 Edit|Write 분기에서만 세워진다. README 를 Bash(`node -e`·sed·
// heredoc)로 고치면 target 갱신이 장부에 안 잡혀 dirty 가 안 풀리고 오탐이 난다(실측).
// mtime 비교는 어떤 도구로 고쳤는지와 무관하므로 그 비대칭을 없앤다.
const rDirty = (pending) => ({ readmeDirty: true, indexDirty: false, readmePending: pending });

ok('mtimeOf 미제공 → 종전대로 경고(하위호환)', () => {
  assert.strictEqual(d.evaluate(rDirty(['scripts/x.js'])).length, 1);
});
ok('README 가 모든 pending trigger 보다 최신 → 경고 없음(Bash 로 고쳐도 인정)', () => {
  const m = (rel) => (rel === 'README.md' ? 200 : 100);
  assert.deepStrictEqual(d.evaluate(rDirty(['scripts/x.js']), m), []);
});
ok('trigger 하나라도 README 보다 나중 → 경고 유지', () => {
  const m = (rel) => ({ 'README.md': 200, 'scripts/a.js': 100, 'scripts/b.js': 300 }[rel]);
  assert.strictEqual(d.evaluate(rDirty(['scripts/a.js', 'scripts/b.js']), m).length, 1);
});
ok('동시각(같은 mtime)은 동기화로 본다', () => {
  const m = () => 200;
  assert.deepStrictEqual(d.evaluate(rDirty(['scripts/x.js']), m), []);
});
ok('README mtime 조회 실패 → 보수적으로 경고 유지', () => {
  const m = (rel) => (rel === 'README.md' ? null : 100);
  assert.strictEqual(d.evaluate(rDirty(['scripts/x.js']), m).length, 1);
});
ok('trigger mtime 조회 실패 → 보수적으로 경고 유지', () => {
  const m = (rel) => (rel === 'README.md' ? 200 : null);
  assert.strictEqual(d.evaluate(rDirty(['scripts/x.js']), m).length, 1);
});
ok('pending 이 비면 판정 근거가 없다 → 경고 유지', () => {
  assert.strictEqual(d.evaluate(rDirty([]), () => 999).length, 1);
});
ok('index 축도 같은 규칙', () => {
  const data = { readmeDirty: false, indexDirty: true, indexPending: ['wiki/pages/p.md'] };
  const m = (rel) => (rel === 'wiki/index.md' ? 200 : 100);
  assert.deepStrictEqual(d.evaluate(data, m), []);
});
ok('mtimeOf 가 throw 해도 경고 유지(fail-open, 크래시 없음)', () => {
  const m = () => { throw new Error('stat boom'); };
  assert.strictEqual(d.evaluate(rDirty(['scripts/x.js']), m).length, 1);
});

// --- evaluate 는 축을 함께 돌려준다 (신호를 dirty flag 로 emit 하면 억제된 축의 failure 가 남는다) ---
ok('한 축만 억제되면 남은 축만 보고한다', () => {
  const data = {
    readmeDirty: true, indexDirty: true,
    readmePending: ['scripts/x.js'], indexPending: ['wiki/pages/p.md'],
  };
  const m = (rel) => (rel === 'README.md' ? 200 : rel === 'wiki/index.md' ? 50 : 100);
  const out = d.evaluate(data, m);
  assert.strictEqual(out.length, 1);
  assert.strictEqual(out[0].axis, 'index'); // readme 는 mtime 으로 억제됨
});

// --- NaN 은 '판정 불가'다 — typeof 로만 거르면 미탐 쪽으로 떨어진다 ---
ok('target mtime 이 NaN → 경고 유지', () => {
  const m = (rel) => (rel === 'README.md' ? NaN : 100);
  assert.strictEqual(d.evaluate(rDirty(['scripts/x.js']), m).length, 1);
});
ok('trigger mtime 이 NaN → 경고 유지', () => {
  const m = (rel) => (rel === 'README.md' ? 200 : NaN);
  assert.strictEqual(d.evaluate(rDirty(['scripts/x.js']), m).length, 1);
});

// --- pending 이 상한에 잘리면 전수 비교가 성립 안 한다 ---
ok('pending 이 상한(50)에 도달 → 판정 불가 → 경고 유지', () => {
  const many = Array.from({ length: 50 }, (_, i) => `scripts/f${i}.js`);
  const m = (rel) => (rel === 'README.md' ? 999 : 1);
  assert.strictEqual(d.evaluate(rDirty(many), m).length, 1);
});

// --- settle: 확인된 동기화를 covered 로 옮겨 재편집 오탐을 막는다 ---
ok('settle 이 전부 커버하면 dirty 해제 + covered 이동', () => {
  const data = { readmeDirty: true, indexDirty: false, readmePending: ['scripts/x.js'], readmeCovered: [] };
  const m = (rel) => (rel === 'README.md' ? 200 : 100);
  assert.strictEqual(d.settle(data, m), true);
  assert.strictEqual(data.readmeDirty, false);
  assert.deepStrictEqual(data.readmeCovered, ['scripts/x.js']);
  assert.deepStrictEqual(data.readmePending, []);
});
ok('settle 후 같은 파일을 재편집해도 dirty 가 아니다 (covered-set 효과)', () => {
  const data = { readmeDirty: true, indexDirty: false, readmePending: ['scripts/x.js'], readmeCovered: [] };
  d.settle(data, (rel) => (rel === 'README.md' ? 200 : 100));
  d.applyChange(data, R + '/scripts/x.js', R, HOME);
  assert.strictEqual(data.readmeDirty, false);
});
ok('settle 은 일부만 커버되면 남은 것을 유지한다', () => {
  const data = { readmeDirty: true, indexDirty: false, readmePending: ['old.js', 'new.js'], readmeCovered: [] };
  const m = (rel) => ({ 'README.md': 200, 'old.js': 100, 'new.js': 300 }[rel]);
  assert.strictEqual(d.settle(data, m), true);
  assert.strictEqual(data.readmeDirty, true);
  assert.deepStrictEqual(data.readmePending, ['new.js']);
  assert.deepStrictEqual(data.readmeCovered, ['old.js']);
});
ok('settle 은 판정 불가면 아무것도 바꾸지 않는다', () => {
  const data = { readmeDirty: true, indexDirty: false, readmePending: ['scripts/x.js'], readmeCovered: [] };
  assert.strictEqual(d.settle(data, undefined), false);
  assert.strictEqual(data.readmeDirty, true);
  assert.deepStrictEqual(data.readmePending, ['scripts/x.js']);
});

// --- driftRoot: rel 이 어느 root 기준인지 핀 고정 ---
ok('applyChange 가 driftRoot 를 기록한다', () => {
  const data = fresh();
  d.applyChange(data, R + '/scripts/x.js', R, HOME);
  assert.strictEqual(data.driftRoot, R);
});
ok('두 root 를 오가면 driftRoot 는 mixed(빈 문자열)', () => {
  const data = fresh();
  d.applyChange(data, R + '/scripts/x.js', R, HOME);
  d.applyChange(data, WT + '/scripts/y.js', WT, HOME);
  assert.strictEqual(data.driftRoot, '');
});

// --- classify: rel 이 stat 에 쓰이므로 `..` 는 거른다 ---
ok('.. 세그먼트가 든 경로는 분류하지 않는다', () => {
  assert.strictEqual(d.classify(R + '/wiki/pages/../../etc/x.md', R), null);
  assert.strictEqual(d.classify(R + '/scripts/../secret.js', R), null);
});

console.log(`dlc-doc-drift.test.js: ${n} assertions passed`);
