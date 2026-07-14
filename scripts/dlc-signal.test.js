#!/usr/bin/env node
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const s = require('./dlc-signal.js');

let n = 0;
const ok = (name, fn) => { fn(); n++; };

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-signal-test-'));
const readLines = (dir) => {
  const f = path.join(dir, 'dlc-signals.jsonl');
  if (!fs.existsSync(f)) return [];
  return fs.readFileSync(f, 'utf8').trim().split('\n').filter(Boolean).map((l) => JSON.parse(l));
};

// ---- KINDS taxonomy ----
ok('KINDS: failure/activity 축이 계획대로 고정된다', () => {
  assert.strictEqual(s.KINDS['early-stop-verify'], 'failure');
  assert.strictEqual(s.KINDS['doc-drift-readme'], 'failure');
  assert.strictEqual(s.KINDS['doc-drift-index'], 'failure');
  assert.strictEqual(s.KINDS['guard-worktree-deny'], 'failure');
  assert.strictEqual(s.KINDS['main-edit-ask'], 'failure');
  assert.strictEqual(s.KINDS['plan-blocked'], 'failure');
  assert.strictEqual(s.KINDS['router-investigation'], 'activity');
  assert.strictEqual(s.KINDS['router-grounding'], 'activity');
  assert.strictEqual(s.KINDS['review-disposition'], 'activity');
  assert.strictEqual(Object.keys(s.KINDS).length, 9);
});

// ---- 경로 해석 (env 채널) ----
ok('signalDir: CLAUDE_DLC_SIGNAL_DIR 이 기본(~/.claude/telemetry)을 이긴다', () => {
  assert.strictEqual(s.signalDir({ CLAUDE_DLC_SIGNAL_DIR: '/x/y' }), '/x/y');
  const def = s.signalDir({});
  assert.ok(def.split(path.sep).join('/').endsWith('.claude/telemetry'));
});

// ---- tildeify (payload 정규화) ----
ok('tildeify: 홈 prefix 를 ~ 로 축약하고 역슬래시를 정규화한다', () => {
  assert.strictEqual(s.tildeify('/Users/u/repo/a.md', '/Users/u'), '~/repo/a.md');
  assert.strictEqual(s.tildeify('C:\\Users\\u\\w', 'C:/Users/u'), '~/w');
  assert.strictEqual(s.tildeify('/other/p', '/Users/u'), '/other/p');
  assert.strictEqual(s.tildeify('', '/Users/u'), '');
});

// ---- emit ----
ok('emit: OFF=1 이면 쓰지 않고 false', () => {
  const d = tmp();
  assert.strictEqual(s.emit('guard-worktree-deny', {}, { CLAUDE_DLC_SIGNAL_DIR: d, CLAUDE_DLC_SIGNAL_OFF: '1' }), false);
  assert.strictEqual(readLines(d).length, 0);
});

ok('emit: 미정의 kind 는 drop(false)', () => {
  const d = tmp();
  assert.strictEqual(s.emit('nope', {}, { CLAUDE_DLC_SIGNAL_DIR: d }), false);
  assert.strictEqual(readLines(d).length, 0);
});

ok('emit: JSONL 1줄 append — ts/kind/axis/session_id/cwd(~축약)/detail', () => {
  const d = tmp();
  const env = { CLAUDE_DLC_SIGNAL_DIR: d };
  const home = os.homedir();
  assert.strictEqual(
    s.emit('early-stop-verify', { session_id: 'abc', cwd: path.join(home, 'proj'), detail: path.join(home, 'proj/f.js') }, env),
    true
  );
  const rows = readLines(d);
  assert.strictEqual(rows.length, 1);
  const r = rows[0];
  assert.strictEqual(r.kind, 'early-stop-verify');
  assert.strictEqual(r.axis, 'failure');
  assert.strictEqual(r.session_id, 'abc');
  assert.strictEqual(r.cwd, '~/proj');
  assert.strictEqual(r.detail, '~/proj/f.js');
  assert.ok(!Number.isNaN(Date.parse(r.ts)));
});

ok('emit: session_id 부재는 default 로 뭉개지 않고 null', () => {
  const d = tmp();
  s.emit('plan-blocked', { cwd: '/w' }, { CLAUDE_DLC_SIGNAL_DIR: d });
  assert.strictEqual(readLines(d)[0].session_id, null);
});

ok('emit: fail-open — 쓰기 불가 경로에서도 throw 없이 false', () => {
  const d = tmp();
  const asFile = path.join(d, 'not-a-dir');
  fs.writeFileSync(asFile, 'x'); // 디렉토리 자리에 파일 → mkdir/append 실패 유도
  assert.strictEqual(s.emit('plan-blocked', {}, { CLAUDE_DLC_SIGNAL_DIR: path.join(asFile, 'sub') }), false);
});

ok('emit: MAX_BYTES 초과 시 .1 로 단일 회전(best-effort)', () => {
  const d = tmp();
  const env = { CLAUDE_DLC_SIGNAL_DIR: d, CLAUDE_DLC_SIGNAL_MAX_BYTES: '10' };
  s.emit('plan-blocked', { session_id: 'a' }, env); // 10B 초과 파일 생성
  s.emit('plan-blocked', { session_id: 'b' }, env); // 회전 후 새 파일에 기록
  assert.ok(fs.existsSync(path.join(d, 'dlc-signals.jsonl.1')));
  const rows = readLines(d);
  assert.strictEqual(rows.length, 1);
  assert.strictEqual(rows[0].session_id, 'b');
});

// ---- detectPlanSignal (순수 판정 — substring 아닌 상태 전이) ----
const PLAN = '/Users/u/repo/plans/2026-07-02-x/x-plan.md';

ok('detect: plans/ 밖·비 md 는 null', () => {
  assert.strictEqual(s.detectPlanSignal('Write', { file_path: '/u/r/src/a.md', content: 'status: blocked' }), null);
  assert.strictEqual(s.detectPlanSignal('Write', { file_path: '/u/r/plans/a.txt', content: 'status: blocked' }), null);
});

ok('detect(Edit): status: blocked 로의 전이만 plan-blocked', () => {
  assert.strictEqual(
    s.detectPlanSignal('Edit', { file_path: PLAN, old_string: 'status: in_progress', new_string: 'status: blocked' }),
    'plan-blocked'
  );
  // 이미 blocked → 전이 아님
  assert.strictEqual(
    s.detectPlanSignal('Edit', { file_path: PLAN, old_string: 'status: blocked\nx', new_string: 'status: blocked\ny' }),
    null
  );
  // 본문에 col-0 라인 추가(old 에 status 라인 자체가 없음) → 상태 전이 아님
  assert.strictEqual(
    s.detectPlanSignal('Edit', { file_path: PLAN, old_string: '# Blockers\n(없음)', new_string: '# Blockers\nstatus: blocked 라고 적힌 로그 인용' }),
    null
  );
  // 상대경로 plan 도 대상
  assert.strictEqual(
    s.detectPlanSignal('Edit', { file_path: 'plans/2026-07-03-y/y-plan.md', old_string: 'status: in_progress', new_string: 'status: blocked' }),
    'plan-blocked'
  );
});

ok('detect(Write): frontmatter 의 blocked 만 인정(본문 문자열은 무시)', () => {
  const fmBlocked = '---\ntitle: t\nstatus: blocked\n---\n\n# Goal\n';
  const bodyOnly = '---\ntitle: t\nstatus: in_progress\n---\n\n본문에 status: blocked 라는 예시 문자열.\n';
  assert.strictEqual(s.detectPlanSignal('Write', { file_path: PLAN, content: fmBlocked }), 'plan-blocked');
  assert.strictEqual(s.detectPlanSignal('Write', { file_path: PLAN, content: bodyOnly }), null);
});

ok('detect: disposition 값 라인 추가 → review-disposition (헤더/placeholder 는 무시)', () => {
  assert.strictEqual(
    s.detectPlanSignal('Edit', { file_path: PLAN, old_string: '(리뷰 후 기록)', new_string: '- finding#1 — false-positive (사유)' }),
    'review-disposition'
  );
  // old 에 이미 같은 축 토큰 → 추가 아님
  assert.strictEqual(
    s.detectPlanSignal('Edit', { file_path: PLAN, old_string: '- a — wontfix', new_string: '- a — wontfix\n메모', }),
    null
  );
  // 템플릿 placeholder 만 있는 Write → null
  assert.strictEqual(
    s.detectPlanSignal('Write', { file_path: PLAN, content: '---\nstatus: in_progress\n---\n# Review Disposition\n(리뷰 후 기록)\n' }),
    null
  );
});

ok('detect: disposition 은 섹션/placeholder 컨텍스트 없인 안 찍힘 (산문 bullet 오탐 차단)', () => {
  // Progress 산문 bullet 의 fix/defer — 컨텍스트 없음 → null
  assert.strictEqual(
    s.detectPlanSignal('Edit', { file_path: PLAN, old_string: '# Progress\n- 이전 진행', new_string: '# Progress\n- 이전 진행\n- rtk 버그 fix 반영 논의' }),
    null
  );
  // Review Disposition 헤더가 fragment 에 있으면 컨텍스트 인정
  assert.strictEqual(
    s.detectPlanSignal('Edit', { file_path: PLAN, old_string: '# Review Disposition\n', new_string: '# Review Disposition\n- f1 — defer (다음 작업)' }),
    'review-disposition'
  );
  // Write: 토큰 라인이 # Deferred 섹션에만 있음 → null, Review Disposition 섹션 안이면 인정
  const wDeferredOnly = '---\nstatus: in_progress\n---\n# Deferred\n- x — defer 후보\n# Review Disposition\n(리뷰 후 기록)\n';
  const wDispSection = '---\nstatus: in_progress\n---\n# Deferred\n(없음)\n# Review Disposition\n- f1 — wontfix (사유)\n';
  assert.strictEqual(s.detectPlanSignal('Write', { file_path: PLAN, content: wDeferredOnly }), null);
  assert.strictEqual(s.detectPlanSignal('Write', { file_path: PLAN, content: wDispSection }), 'review-disposition');
});

ok('detect: blocked 전이가 disposition 보다 우선', () => {
  assert.strictEqual(
    s.detectPlanSignal('Edit', {
      file_path: PLAN,
      old_string: 'status: in_progress',
      new_string: 'status: blocked\n- x — defer',
    }),
    'plan-blocked'
  );
});

// ---- summarize (집계 — /improve 소비) ----
ok('summarize: kind 별 raw/unique-session/기간 집계, 불량 라인·미정의 kind 는 무시', () => {
  const text = [
    JSON.stringify({ ts: '2026-07-01T01:00:00Z', kind: 'early-stop-verify', axis: 'failure', session_id: 's1' }),
    JSON.stringify({ ts: '2026-07-02T01:00:00Z', kind: 'early-stop-verify', axis: 'failure', session_id: 's1' }),
    JSON.stringify({ ts: '2026-07-03T01:00:00Z', kind: 'early-stop-verify', axis: 'failure', session_id: 's2' }),
    JSON.stringify({ ts: '2026-07-03T02:00:00Z', kind: 'router-grounding', axis: 'activity', session_id: null }),
    'not-json',
    JSON.stringify({ ts: '2026-07-03T03:00:00Z', kind: 'unknown-kind', session_id: 's9' }),
  ].join('\n');
  const sum = s.summarize(text);
  const esv = sum['early-stop-verify'];
  assert.strictEqual(esv.raw, 3);
  assert.strictEqual(esv.sessions, 2);
  assert.strictEqual(esv.axis, 'failure');
  assert.strictEqual(esv.first, '2026-07-01T01:00:00Z');
  assert.strictEqual(esv.last, '2026-07-03T01:00:00Z');
  assert.strictEqual(sum['router-grounding'].sessions, 0); // session_id null 은 unique 에 안 섞임
  assert.strictEqual(sum['unknown-kind'], undefined);
  assert.strictEqual(s.summarize('').constructor, Object);
});

// ---- hook 통합 (spawn — 실제 emit 경로 관찰, OFF 자기격리와 동일 채널) ----
ok('통합(guard): deny 시 guard-worktree-deny 신호가 지정 DIR 에 기록된다', () => {
  const d = tmp();
  const inp = JSON.stringify({
    cwd: '/Users/u/repo/.claude/worktrees/wt1/sub',
    tool_input: { file_path: '/Users/u/repo/scripts/x.js' },
    session_id: 'g1',
  });
  const out = execFileSync('node', [path.join(__dirname, 'guard-worktree-edit.js')], {
    input: inp,
    env: { ...process.env, CLAUDE_DLC_SIGNAL_DIR: d },
  }).toString();
  assert.ok(out.includes('"permissionDecision":"deny"')); // 본연 출력 비회귀
  const rows = readLines(d);
  assert.strictEqual(rows.length, 1);
  assert.strictEqual(rows[0].kind, 'guard-worktree-deny');
  assert.strictEqual(rows[0].session_id, 'g1');
});

ok('통합(early-stop): 검증 누락 block 시 early-stop-verify 신호 기록 + block 출력 비회귀', () => {
  const d = tmp();
  const ledger = require('./dlc-ledger.js');
  const sid = `sigtest-${process.pid}`;
  ledger.write(sid, { ...ledger.DEFAULT, changed: true, verified: false });
  const out = execFileSync('node', [path.join(__dirname, 'dlc-early-stop.js')], {
    input: JSON.stringify({ session_id: sid }),
    env: { ...process.env, CLAUDE_DLC_SIGNAL_DIR: d, CLAUDE_DLC_DOCDRIFT_OFF: '1' },
  }).toString();
  assert.ok(out.includes('"decision":"block"'));
  const rows = readLines(d);
  assert.strictEqual(rows.length, 1);
  assert.strictEqual(rows[0].kind, 'early-stop-verify');
  ledger.reset(sid);
});

ok('통합(early-stop): OFF=1 이면 신호 없이 본연 동작만', () => {
  const d = tmp();
  const ledger = require('./dlc-ledger.js');
  const sid = `sigtest-off-${process.pid}`;
  ledger.write(sid, { ...ledger.DEFAULT, changed: true, verified: false });
  const out = execFileSync('node', [path.join(__dirname, 'dlc-early-stop.js')], {
    input: JSON.stringify({ session_id: sid }),
    env: { ...process.env, CLAUDE_DLC_SIGNAL_DIR: d, CLAUDE_DLC_SIGNAL_OFF: '1', CLAUDE_DLC_DOCDRIFT_OFF: '1' },
  }).toString();
  assert.ok(out.includes('"decision":"block"')); // fail-open: 신호 꺼져도 hook 본연 동작 유지
  assert.strictEqual(readLines(d).length, 0);
  ledger.reset(sid);
});

ok('CLI summary: 회전분(.1)도 함께 집계한다', () => {
  const d = tmp();
  const mk = (kind, sid, ts) => JSON.stringify({ ts, kind, axis: s.KINDS[kind], session_id: sid }) + '\n';
  fs.writeFileSync(path.join(d, 'dlc-signals.jsonl.1'), mk('guard-worktree-deny', 'old1', '2026-06-01T00:00:00Z'));
  fs.writeFileSync(path.join(d, 'dlc-signals.jsonl'), mk('guard-worktree-deny', 'new1', '2026-07-01T00:00:00Z'));
  const out = execFileSync('node', [path.join(__dirname, 'dlc-signal.js'), 'summary'], {
    env: { ...process.env, CLAUDE_DLC_SIGNAL_DIR: d },
  }).toString();
  assert.ok(out.includes('guard-worktree-deny: sessions=2 raw=2'));
  assert.ok(out.includes('first=2026-06-01'));
});

console.log(`dlc-signal.test.js: ${n} tests passed`);
