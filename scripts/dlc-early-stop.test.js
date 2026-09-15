#!/usr/bin/env node
// dlc-early-stop(Stop hook) 통합 테스트 — 훅을 실제로 spawn 해 stdout(block 여부)과
// 신호(telemetry) 방출을 함께 관찰한다.
//
// 왜 필요한가: 문서 drift 판정의 절반은 훅 쪽에 있다(root 해석 → path.join → statSync → 주입 →
// 축별 emit). 순수 모듈 테스트만으로는 그 절반이 통째로 미검증이라, root 불일치로 게이트가
// 꺼지는 결함과 억제된 축의 failure 신호가 남는 결함이 **모듈 테스트를 전부 통과한 채** 존재했다.
//
// 격리: `os.homedir()`(→ HOME/USERPROFILE)로 fixture root 를, `os.tmpdir()`(→ TMPDIR/TEMP/TMP)로
// ledger 를, `CLAUDE_DLC_SIGNAL_DIR` 로 신호 파일을 각각 실 환경 밖으로 돌린다.
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const HOOK = path.join(__dirname, 'dlc-early-stop.js');
let n = 0;
const ok = (name, fn) => { fn(); n++; };

const SEC = 1000;
const setMtime = (fp, ms) => fs.utimesSync(fp, new Date(ms), new Date(ms)); // sleep 없이 결정적으로

// <home>/.claude 를 root 로 갖는 fixture. mtime 은 호출부가 명시적으로 박는다.
function makeHome() {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'es-home-'));
  const root = path.join(home, '.claude');
  fs.mkdirSync(path.join(root, 'scripts'), { recursive: true });
  fs.mkdirSync(path.join(root, 'wiki', 'pages'), { recursive: true });
  fs.writeFileSync(path.join(root, 'README.md'), '#');
  fs.writeFileSync(path.join(root, 'wiki', 'index.md'), '#');
  fs.writeFileSync(path.join(root, 'scripts', 'x.js'), '//');
  fs.writeFileSync(path.join(root, 'wiki', 'pages', 'p.md'), '#');
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'es-tmp-'));
  return { home, root, tmp };
}

const LEDGER_BASE = {
  changed: false, verified: false, blocks: 0, docBlocks: 0,
  readmeDirty: false, indexDirty: false, readmeTrigger: null, indexTrigger: null, changedTrigger: null,
  readmeCovered: [], readmePending: [], indexCovered: [], indexPending: [], driftRoot: null,
};
const SID = 'es-test';
const ledgerFile = (tmp) => path.join(tmp, `dlc-evidence-${SID}.json`);
const writeLedger = (tmp, patch) =>
  fs.writeFileSync(ledgerFile(tmp), JSON.stringify({ ...LEDGER_BASE, ...patch }));
const readLedger = (tmp) => JSON.parse(fs.readFileSync(ledgerFile(tmp), 'utf8'));

function run({ home, tmp }, cwd, { input: extra = {}, env: extraEnv = {} } = {}) {
  const sigDir = fs.mkdtempSync(path.join(tmp, 'sig-'));
  const r = spawnSync('node', [HOOK], {
    input: JSON.stringify({ session_id: SID, cwd, stop_hook_active: false, ...extra }),
    env: {
      ...process.env,
      HOME: home, USERPROFILE: home,      // os.homedir()
      TMPDIR: tmp, TEMP: tmp, TMP: tmp,   // os.tmpdir() → ledger
      CLAUDE_DLC_SIGNAL_DIR: sigDir,
      ...extraEnv,
    },
    encoding: 'utf8',
    timeout: 20000,
  });
  assert.ok(!r.error, `spawn 실패: ${r.error && r.error.message}`);
  assert.strictEqual(r.status, 0, 'Stop hook 은 어떤 경로에서도 exit 0 이어야 한다');
  let signals = [];
  try {
    signals = fs.readdirSync(sigDir)
      .flatMap((f) => fs.readFileSync(path.join(sigDir, f), 'utf8').split('\n'))
      .filter(Boolean)
      .map((l) => { try { return JSON.parse(l); } catch { return null; } })
      .filter(Boolean);
  } catch { /* 신호 파일 없음 = 방출 없음 */ }
  return { out: r.stdout || '', signals: signals.map((s) => s.kind), rows: signals };
}
const blocked = (out) => out.includes('"decision":"block"');

ok('root 일치 + README 가 trigger 보다 최신 → 경고 없음 (Bash 로 고친 README 인정)', () => {
  const F = makeHome();
  setMtime(path.join(F.root, 'scripts', 'x.js'), 1000 * SEC);
  setMtime(path.join(F.root, 'README.md'), 2000 * SEC);
  writeLedger(F.tmp, { readmeDirty: true, readmePending: ['scripts/x.js'], readmeTrigger: 'scripts/x.js', driftRoot: F.root.replace(/\\/g, '/') });
  const { out, signals } = run(F, F.root);
  assert.ok(!blocked(out), `경고가 뜨면 안 된다: ${out.slice(0, 160)}`);
  assert.deepStrictEqual(signals, [], '출력하지 않은 경고의 신호를 남기면 안 된다');
});

ok('trigger 가 README 보다 최신 → 경고 (미탐 아님)', () => {
  const F = makeHome();
  setMtime(path.join(F.root, 'README.md'), 1000 * SEC);
  setMtime(path.join(F.root, 'scripts', 'x.js'), 2000 * SEC);
  writeLedger(F.tmp, { readmeDirty: true, readmePending: ['scripts/x.js'], readmeTrigger: 'scripts/x.js', driftRoot: F.root.replace(/\\/g, '/') });
  const { out, signals } = run(F, F.root);
  assert.ok(blocked(out));
  assert.ok(out.includes('README.md 가 문서화 표면'));
  assert.deepStrictEqual(signals, ['doc-drift-readme']);
});

ok('driftRoot 가 현재 root 와 다르면 mtime 을 믿지 않는다 → 경고 유지', () => {
  // 세션이 편집 후 다른 worktree·main 으로 옮기면 같은 rel 이 다른 파일을 가리킨다.
  // main 은 README 가 매 머지마다 재작성돼 거의 항상 최신이라, 대조가 없으면 게이트가 통째로 꺼진다.
  const F = makeHome();
  setMtime(path.join(F.root, 'scripts', 'x.js'), 1000 * SEC);
  setMtime(path.join(F.root, 'README.md'), 2000 * SEC); // 여기선 '동기화된 것처럼' 보인다
  writeLedger(F.tmp, { readmeDirty: true, readmePending: ['scripts/x.js'], readmeTrigger: 'scripts/x.js', driftRoot: '/some/other/worktree' });
  const { out } = run(F, F.root);
  assert.ok(blocked(out), 'root 가 다르면 종전 동작(경고)로 떨어져야 한다');
});

ok('driftRoot 가 mixed("") 여도 경고 유지', () => {
  const F = makeHome();
  setMtime(path.join(F.root, 'scripts', 'x.js'), 1000 * SEC);
  setMtime(path.join(F.root, 'README.md'), 2000 * SEC);
  writeLedger(F.tmp, { readmeDirty: true, readmePending: ['scripts/x.js'], readmeTrigger: 'scripts/x.js', driftRoot: '' });
  assert.ok(blocked(run(F, F.root).out));
});

ok('한 축만 억제되면 남은 축만 경고하고 신호도 그 축만 남긴다', () => {
  const F = makeHome();
  setMtime(path.join(F.root, 'scripts', 'x.js'), 1000 * SEC);
  setMtime(path.join(F.root, 'README.md'), 2000 * SEC);        // readme 축은 동기화됨
  setMtime(path.join(F.root, 'wiki', 'index.md'), 1000 * SEC);
  setMtime(path.join(F.root, 'wiki', 'pages', 'p.md'), 2000 * SEC); // index 축은 미동기화
  writeLedger(F.tmp, {
    readmeDirty: true, readmePending: ['scripts/x.js'], readmeTrigger: 'scripts/x.js',
    indexDirty: true, indexPending: ['wiki/pages/p.md'], indexTrigger: 'wiki/pages/p.md',
    driftRoot: F.root.replace(/\\/g, '/'),
  });
  const { out, signals } = run(F, F.root);
  assert.ok(out.includes('wiki/index.md 가'));
  assert.ok(!out.includes('README.md 가 문서화 표면'), 'README 축은 억제됐어야 한다');
  assert.deepStrictEqual(signals, ['doc-drift-index'], '억제된 축의 failure 신호가 남으면 안 된다');
});

ok('경고가 없어도 settle 결과(covered)가 ledger 에 저장된다', () => {
  const F = makeHome();
  setMtime(path.join(F.root, 'scripts', 'x.js'), 1000 * SEC);
  setMtime(path.join(F.root, 'README.md'), 2000 * SEC);
  writeLedger(F.tmp, { readmeDirty: true, readmePending: ['scripts/x.js'], readmeTrigger: 'scripts/x.js', driftRoot: F.root.replace(/\\/g, '/') });
  run(F, F.root);
  const after = readLedger(F.tmp);
  assert.strictEqual(after.readmeDirty, false);
  assert.deepStrictEqual(after.readmeCovered, ['scripts/x.js']);
});

ok('타 repo cwd → root 미해석 → 종전 동작(경고 유지)', () => {
  const F = makeHome();
  const other = fs.mkdtempSync(path.join(os.tmpdir(), 'es-other-'));
  writeLedger(F.tmp, { readmeDirty: true, readmePending: ['scripts/x.js'], readmeTrigger: 'scripts/x.js', driftRoot: F.root.replace(/\\/g, '/') });
  assert.ok(blocked(run(F, other).out));
});

ok('CLAUDE_DLC_DOCDRIFT_OFF=1 이면 문서 경고 없음', () => {
  const F = makeHome();
  setMtime(path.join(F.root, 'README.md'), 1000 * SEC);
  setMtime(path.join(F.root, 'scripts', 'x.js'), 2000 * SEC);
  writeLedger(F.tmp, { readmeDirty: true, readmePending: ['scripts/x.js'], driftRoot: F.root.replace(/\\/g, '/') });
  const sigDir = fs.mkdtempSync(path.join(F.tmp, 'sig-'));
  const r = spawnSync('node', [HOOK], {
    input: JSON.stringify({ session_id: SID, cwd: F.root, stop_hook_active: false }),
    env: { ...process.env, HOME: F.home, USERPROFILE: F.home, TMPDIR: F.tmp, TEMP: F.tmp, TMP: F.tmp, CLAUDE_DLC_SIGNAL_DIR: sigDir, CLAUDE_DLC_DOCDRIFT_OFF: '1' },
    encoding: 'utf8',
    timeout: 20000,
  });
  assert.strictEqual(r.status, 0);
  assert.ok(!blocked(r.stdout || ''));
});

ok('stop_hook_active=true 면 즉시 통과(무한 루프 방지)', () => {
  const F = makeHome();
  setMtime(path.join(F.root, 'README.md'), 1000 * SEC);
  setMtime(path.join(F.root, 'scripts', 'x.js'), 2000 * SEC);
  writeLedger(F.tmp, { readmeDirty: true, readmePending: ['scripts/x.js'], driftRoot: F.root.replace(/\\/g, '/') });
  const r = spawnSync('node', [HOOK], {
    input: JSON.stringify({ session_id: SID, cwd: F.root, stop_hook_active: true }),
    env: { ...process.env, HOME: F.home, USERPROFILE: F.home, TMPDIR: F.tmp, TEMP: F.tmp, TMP: F.tmp },
    encoding: 'utf8',
    timeout: 20000,
  });
  assert.strictEqual(r.status, 0);
  assert.strictEqual(r.stdout, '');
});

// --- (3) plan drift 축 ---
// 이 축의 최대 위험은 오탐이다. "plan 이 매칭될 때만 발동"을 양방향으로 잠근다.

function initRepo(root, branch) {
  const g = (args) => spawnSync('git', ['-C', root, ...args], { stdio: 'ignore' });
  g(['init', '-q', '-b', branch]);
  g(['config', 'user.email', 't@t']);
  g(['config', 'user.name', 't']);
  g(['config', 'commit.gpgsign', 'false']);
  g(['add', '-A']);
  g(['commit', '-m', 'init']);
}

ok('plan drift: 소스 변경 + 매칭 plan 있는데 미편집 → 경고 + 신호', () => {
  const F = makeHome();
  initRepo(F.root, 'my-task');
  fs.mkdirSync(path.join(F.root, 'plans', '2026-09-07-my-task'), { recursive: true });
  fs.writeFileSync(path.join(F.root, 'plans', '2026-09-07-my-task', 'my-task-plan.md'), '#');
  writeLedger(F.tmp, { changed: true, verified: true, planTouched: false, changedTrigger: 'scripts/x.js' });
  const { out, signals } = run(F, F.root);
  assert.ok(blocked(out), 'plan 미갱신이면 경고해야 한다');
  assert.ok(out.includes('my-task-plan.md'), '어느 plan 인지 알려줘야 한다');
  assert.ok(signals.includes('early-stop-plan-drift'), `신호 누락: ${signals}`);
});

ok('plan drift: plan 을 편집했으면 경고 없음', () => {
  const F = makeHome();
  initRepo(F.root, 'my-task');
  fs.mkdirSync(path.join(F.root, 'plans', '2026-09-07-my-task'), { recursive: true });
  fs.writeFileSync(path.join(F.root, 'plans', '2026-09-07-my-task', 'my-task-plan.md'), '#');
  writeLedger(F.tmp, { changed: true, verified: true, planTouched: true });
  assert.ok(!blocked(run(F, F.root).out));
});

ok('plan drift: 매칭 plan 이 없으면 발동하지 않는다 (오탐 방지의 핵심)', () => {
  const F = makeHome();
  initRepo(F.root, 'my-task');
  fs.mkdirSync(path.join(F.root, 'plans', '2026-09-07-other'), { recursive: true });
  fs.writeFileSync(path.join(F.root, 'plans', '2026-09-07-other', 'other-plan.md'), '#');
  writeLedger(F.tmp, { changed: true, verified: true, planTouched: false });
  assert.ok(!blocked(run(F, F.root).out), 'plan 없는 흐름에 경고가 뜨면 안 된다');
});

ok('plan drift: git repo 가 아니면 판정 포기 (fail-open)', () => {
  const F = makeHome(); // initRepo 안 함
  fs.mkdirSync(path.join(F.root, 'plans', '2026-09-07-my-task'), { recursive: true });
  fs.writeFileSync(path.join(F.root, 'plans', '2026-09-07-my-task', 'my-task-plan.md'), '#');
  writeLedger(F.tmp, { changed: true, verified: true, planTouched: false });
  assert.ok(!blocked(run(F, F.root).out));
});

ok('plan drift: CAP=1 — 재종료 시 통과', () => {
  const F = makeHome();
  initRepo(F.root, 'my-task');
  fs.mkdirSync(path.join(F.root, 'plans', '2026-09-07-my-task'), { recursive: true });
  fs.writeFileSync(path.join(F.root, 'plans', '2026-09-07-my-task', 'my-task-plan.md'), '#');
  writeLedger(F.tmp, { changed: true, verified: true, planTouched: false });
  assert.ok(blocked(run(F, F.root).out));
  assert.strictEqual(readLedger(F.tmp).planBlocks, 1);
  assert.ok(!blocked(run(F, F.root).out), '두 번째 종료는 통과해야 한다');
});

ok('plan drift: OFF 스위치', () => {
  const F = makeHome();
  initRepo(F.root, 'my-task');
  fs.mkdirSync(path.join(F.root, 'plans', '2026-09-07-my-task'), { recursive: true });
  fs.writeFileSync(path.join(F.root, 'plans', '2026-09-07-my-task', 'my-task-plan.md'), '#');
  writeLedger(F.tmp, { changed: true, verified: true, planTouched: false });
  const r = spawnSync('node', [HOOK], {
    input: JSON.stringify({ session_id: SID, cwd: F.root, stop_hook_active: false }),
    env: { ...process.env, HOME: F.home, USERPROFILE: F.home, TMPDIR: F.tmp, TEMP: F.tmp, TMP: F.tmp,
      CLAUDE_DLC_PLANDRIFT_OFF: '1' },
    encoding: 'utf8', timeout: 20000,
  });
  assert.strictEqual(r.status, 0);
  assert.ok(!blocked(r.stdout || ''));
});

// ---- 결론 블록 축 (④) — 편집한 턴의 마지막 답변이 `## 결론` 으로 끝나야 한다 ----
const WITH_CONCLUSION = '상세 설명…\n\n## 원인\n- x\n\n## 결론\n- 문제: a\n- 원인: b\n- 조치: c\n- 검증: d\n- 남은 것: 없음\n';
const NO_CONCLUSION = '고쳤습니다. 테스트도 통과합니다.';

ok('결론 축: 편집 + 결론 블록으로 끝남 → 통과, edited 소비', () => {
  const F = makeHome();
  writeLedger(F.tmp, { edited: true, conclusionBlocks: 0 });
  const r = run(F, F.root, { input: { last_assistant_message: WITH_CONCLUSION } });
  assert.ok(!blocked(r.out));
  assert.strictEqual(readLedger(F.tmp).edited, false, '통과한 결론은 edited 를 소비해야 한다(후속 짧은 답변 오탐 방지)');
});

ok('결론 축: 편집 + 결론 없음 → 1회 block + 카운터 + 신호(detail 없음)', () => {
  const F = makeHome();
  writeLedger(F.tmp, { edited: true, conclusionBlocks: 0 });
  const r = run(F, F.root, { input: { last_assistant_message: NO_CONCLUSION } });
  assert.ok(blocked(r.out));
  assert.ok(r.out.includes('## 결론'), 'reason 에 요구 형식이 있어야 한다');
  const led = readLedger(F.tmp);
  assert.strictEqual(led.conclusionBlocks, 1);
  assert.strictEqual(led.edited, true, 'block 은 edited 를 소비하지 않는다');
  assert.deepStrictEqual(r.signals, ['early-stop-conclusion']);
  assert.strictEqual(r.rows[0].detail, null, '답변 본문·경로를 telemetry 에 넣지 않는다');
  assert.ok(!blocked(run(F, F.root, { input: { last_assistant_message: NO_CONCLUSION } }).out), 'CAP=1 — 재종료 통과');
});

ok('결론 축: `## 결론` 이 마지막 heading 이 아니면 block (위치 검사)', () => {
  const F = makeHome();
  writeLedger(F.tmp, { edited: true, conclusionBlocks: 0 });
  const mid = '## 결론\n- 문제: a\n\n## 상세\n- 긴 설명';
  assert.ok(blocked(run(F, F.root, { input: { last_assistant_message: mid } }).out));
});

ok('결론 축: 코드펜스 안의 `## ` 는 heading 이 아니다 (양방향)', () => {
  const F = makeHome();
  writeLedger(F.tmp, { edited: true, conclusionBlocks: 0 });
  const fenceAfter = WITH_CONCLUSION + '- 조치 예시:\n```md\n## 예시\n```\n';
  assert.ok(!blocked(run(F, F.root, { input: { last_assistant_message: fenceAfter } }).out), '결론 뒤 펜스 안 heading 은 무시');
  writeLedger(F.tmp, { edited: true, conclusionBlocks: 0 });
  const fenceOnly = '설명\n```\n## 결론\n- 문제: x\n```\n';
  assert.ok(blocked(run(F, F.root, { input: { last_assistant_message: fenceOnly } }).out), '펜스 안 결론만 있으면 없는 것');
});

ok('결론 축: stop_hook_active 재종료도 결론이면 edited 를 소비한다(경고는 없음)', () => {
  const F = makeHome();
  writeLedger(F.tmp, { edited: true, conclusionBlocks: 0, changed: true, verified: false, blocks: 0 });
  const r = run(F, F.root, { input: { stop_hook_active: true, last_assistant_message: WITH_CONCLUSION } });
  assert.ok(!blocked(r.out));
  const led = readLedger(F.tmp);
  assert.strictEqual(led.edited, false);
  assert.strictEqual(led.blocks, 0, '재종료 경로는 다른 축을 판정하지 않는다');
});

ok('결론 축: edited=false 면 침묵', () => {
  const F = makeHome();
  writeLedger(F.tmp, { edited: false, conclusionBlocks: 0 });
  const r = run(F, F.root, { input: { last_assistant_message: NO_CONCLUSION } });
  assert.ok(!blocked(r.out));
  assert.deepStrictEqual(r.signals, []);
});

ok('결론 축: last_assistant_message 부재 → 판정 포기(fail-open), edited 유지', () => {
  const F = makeHome();
  writeLedger(F.tmp, { edited: true, conclusionBlocks: 0 });
  const r = run(F, F.root);
  assert.ok(!blocked(r.out));
  assert.strictEqual(readLedger(F.tmp).edited, true);
  assert.strictEqual(readLedger(F.tmp).conclusionBlocks, 0);
});

ok('결론 축: OFF 스위치', () => {
  const F = makeHome();
  writeLedger(F.tmp, { edited: true, conclusionBlocks: 0 });
  const r = run(F, F.root, { input: { last_assistant_message: NO_CONCLUSION }, env: { CLAUDE_DLC_CONCLUSION_OFF: '1' } });
  assert.ok(!blocked(r.out));
  assert.deepStrictEqual(r.signals, []);
});

ok('결론 축: 검증 축과 동시 block — reason 합산·카운터 각각', () => {
  const F = makeHome();
  writeLedger(F.tmp, { changed: true, verified: false, blocks: 0, edited: true, conclusionBlocks: 0 });
  const r = run(F, F.root, { input: { last_assistant_message: NO_CONCLUSION } });
  assert.ok(blocked(r.out));
  assert.ok(r.out.includes('검증(test/lint') && r.out.includes('## 결론'), '두 축의 reason 이 함께 나와야 한다');
  const led = readLedger(F.tmp);
  assert.strictEqual(led.blocks, 1);
  assert.strictEqual(led.conclusionBlocks, 1);
  assert.deepStrictEqual(r.signals.sort(), ['early-stop-conclusion', 'early-stop-verify']);
});

ok('결론 축: 구 장부(신규 필드 없음) → DEFAULT 병합으로 침묵', () => {
  const F = makeHome();
  writeLedger(F.tmp, {}); // edited/conclusionBlocks 키 자체가 없음
  const r = run(F, F.root, { input: { last_assistant_message: NO_CONCLUSION } });
  assert.ok(!blocked(r.out));
});

console.log(`dlc-early-stop.test.js: ${n} tests passed`);
