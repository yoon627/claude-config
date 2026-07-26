#!/usr/bin/env node
// session-brief.js 테스트 — K(머지대기 브랜치) + L(improve nudge).
// git fixture(origin/main + ahead 브랜치) spawn / SIGNAL_DIR 주입 jsonl 로 판정 관찰.
// 신호 격리: CLAUDE_DLC_SIGNAL_DIR 로 telemetry 를 fixture 로 돌린다.
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync, spawnSync } = require('child_process');
const BRIEF = path.join(__dirname, 'session-brief.js');

// CI 결정성: 상속된 GIT_* 가 fixture repo 판정을 오염시키지 않게 스크럽.
for (const k of ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE']) delete process.env[k];

let n = 0;
const ok = (name, fn) => { fn(); n++; };

function git(dir, args, extraEnv) {
  execFileSync('git', ['-C', dir, ...args], { stdio: 'ignore', env: { ...process.env, ...extraEnv } });
}
function initRepo() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sb-repo-'));
  execFileSync('git', ['init', '-b', 'main', dir], { stdio: 'ignore' });
  git(dir, ['config', 'user.email', 't@t']);
  git(dir, ['config', 'user.name', 't']);
  git(dir, ['config', 'commit.gpgsign', 'false']);
  return dir;
}
function commit(dir, msg, date) {
  const f = path.join(dir, msg.replace(/\W/g, '_') + '.txt');
  fs.writeFileSync(f, msg);
  git(dir, ['add', '-A']);
  const d = date || '2026-01-01T00:00:00';
  git(dir, ['commit', '-m', msg], { GIT_AUTHOR_DATE: d, GIT_COMMITTER_DATE: d });
}
// run brief; returns stdout string.
function run(env) {
  try {
    return execFileSync('node', [BRIEF], { env: { ...process.env, ...env } }).toString();
  } catch (e) {
    return e.stdout ? e.stdout.toString() : '';
  }
}
function sigDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'sb-sig-'));
}
function writeRows(dir, rows, file) {
  fs.writeFileSync(path.join(dir, file || 'dlc-signals.jsonl'), rows.map((r) => JSON.stringify(r)).join('\n') + '\n');
}
// plans/<dir>/<slug>-plan.md 를 frontmatter 와 함께 만든다. dir 은 §10 형식(<date>-<slug>).
function writePlan(repoDir, slug, status, updated, dirName) {
  const dir = path.join(repoDir, 'plans', dirName || `2026-07-01-${slug}`);
  fs.mkdirSync(dir, { recursive: true });
  const fm = `---\ntitle: ${slug} — t\nstatus: ${status}\nstarted: 2026-07-01\nupdated: ${updated}\n---\n\n# Goal\nt\n`;
  fs.writeFileSync(path.join(dir, `${slug}-plan.md`), fm);
}
// updated 값으로 쓸 "오늘 - n일" 로컬 날짜 문자열(YYYY-MM-DD).
function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

const OFF = { CLAUDE_BRIEF_IMPROVE_OFF: '1', CLAUDE_BRIEF_STALE_OFF: '1' }; // K 테스트 시 L·M 끄기
// L 테스트 시 K·M 끄기. STALE_OFF 필수 — L 테스트는 CLAUDE_BRIEF_REPO 를 안 넘겨 실제 ~/.claude 를
// 읽으므로, M 이 켜져 있으면 그쪽 plan 상태에 따라 무음 단언이 깨진다.
const MOFF = { CLAUDE_BRIEF_MERGE_OFF: '1', CLAUDE_BRIEF_STALE_OFF: '1' };
const SOFF = { CLAUDE_BRIEF_MERGE_OFF: '1', CLAUDE_BRIEF_IMPROVE_OFF: '1' }; // M 테스트 시 K·L 끄기

// ---------- K: 머지 대기 ----------
ok('ⓐ ahead>0 브랜치 → 머지 대기 목록 1줄', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  git(r, ['checkout', '-b', 'feat1']); commit(r, 'f1a');
  git(r, ['checkout', 'main']); git(r, ['checkout', '-b', 'feat2']); commit(r, 'f2a'); commit(r, 'f2b');
  const out = run({ CLAUDE_BRIEF_REPO: r, ...OFF });
  assert.match(out, /머지 대기/);
  assert.match(out, /feat1\(\+1\)/);
  assert.match(out, /feat2\(\+2\)/);
});
ok('ⓑ ahead 브랜치 없음 → 무음', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...OFF }), '');
});
ok('ⓒ origin/main 없음 → 무음 exit 0', () => {
  const r = initRepo();
  commit(r, 'base'); // origin/main 미설정
  git(r, ['checkout', '-b', 'feat1']); commit(r, 'f1a');
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...OFF }), '');
});
ok('ⓒ 비-git repoDir → 무음 exit 0', () => {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'sb-nogit-'));
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: d, ...OFF }), '');
});
ok('ⓙ worktree checkout 브랜치도 + 마커 없이 1회만', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  git(r, ['checkout', '-b', 'wtbranch']); commit(r, 'w1');
  git(r, ['checkout', 'main']); // wtbranch 를 main repo 에서 놓아줌
  const wt = fs.mkdtempSync(path.join(os.tmpdir(), 'sb-wt-')) + '/wt';
  git(r, ['worktree', 'add', wt, 'wtbranch']); // wtbranch 가 worktree 에 checkout → git branch 면 '+' 붙음
  const out = run({ CLAUDE_BRIEF_REPO: r, ...OFF });
  assert.match(out, /wtbranch\(\+1\)/);
  assert.doesNotMatch(out, /\+ wtbranch|wtbranch.*wtbranch/); // 중복·마커 없음
});
ok('oldest-commit 먼저 정렬 + cap 5(+N)', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  const dates = ['2026-01-02', '2026-01-05', '2026-01-03', '2026-01-06', '2026-01-04', '2026-01-07', '2026-01-08'];
  dates.forEach((d, i) => {
    git(r, ['checkout', 'main']); git(r, ['checkout', '-b', 'b' + i]);
    commit(r, 'c' + i, d + 'T00:00:00');
  });
  const out = run({ CLAUDE_BRIEF_REPO: r, ...OFF });
  // 가장 오래된 커밋(2026-01-02 = b0)이 맨 앞, 최대 5개 + "+2"
  assert.match(out, /머지 대기[^\n]*b0\(\+1\)/);
  assert.match(out, /\+2/); // 7개 중 5 표시 + 2 more
  assert.doesNotMatch(out, /b5\(|b6\(/); // 가장 최신 2개는 미표시(정렬상 뒤)
});

// ---------- L: improve nudge ----------
const failRow = (sid, kind, ts) => ({ ts, kind, axis: 'failure', session_id: sid, cwd: null, detail: null });
ok('ⓓ failure 임계 이상 → nudge', () => {
  const d = sigDir();
  writeRows(d, [
    failRow('s1', 'guard-worktree-deny', '2026-07-10T00:00:00Z'),
    failRow('s2', 'early-stop-verify', '2026-07-10T00:01:00Z'),
    failRow('s3', 'plan-blocked', '2026-07-10T00:02:00Z'),
    failRow('s4', 'doc-drift-readme', '2026-07-10T00:03:00Z'),
    failRow('s5', 'main-edit-ask', '2026-07-10T00:04:00Z'),
  ]);
  const out = run({ CLAUDE_DLC_SIGNAL_DIR: d, ...MOFF });
  assert.match(out, /\/improve 권장/);
  assert.match(out, /5세션/);
});
ok('ⓕ 한 세션이 failure 2 kind → unique 1 집계(cross-kind dedup)', () => {
  const d = sigDir();
  // s1 이 2 kind, + s2,s3,s4 = unique 4 (< 5). naive kind별 sessions 합은 5 → 오발.
  writeRows(d, [
    failRow('s1', 'guard-worktree-deny', '2026-07-10T00:00:00Z'),
    failRow('s1', 'plan-blocked', '2026-07-10T00:01:00Z'),
    failRow('s2', 'early-stop-verify', '2026-07-10T00:02:00Z'),
    failRow('s3', 'doc-drift-index', '2026-07-10T00:03:00Z'),
    failRow('s4', 'main-edit-ask', '2026-07-10T00:04:00Z'),
  ]);
  assert.strictEqual(run({ CLAUDE_DLC_SIGNAL_DIR: d, ...MOFF }), ''); // 4 unique < 5 → 무음
});
ok('activity 축은 안 셈', () => {
  const d = sigDir();
  writeRows(d, Array.from({ length: 6 }, (_, i) =>
    ({ ts: '2026-07-10T00:0' + i + ':00Z', kind: 'router-grounding', axis: 'activity', session_id: 's' + i })));
  assert.strictEqual(run({ CLAUDE_DLC_SIGNAL_DIR: d, ...MOFF }), '');
});
ok('ⓔ 마커 이후 신호 0 → 무음', () => {
  const d = sigDir();
  writeRows(d, Array.from({ length: 6 }, (_, i) =>
    failRow('s' + i, 'plan-blocked', '2026-07-10T00:0' + i + ':00Z')));
  fs.writeFileSync(path.join(d, 'last-improve'), ''); // 마커 mtime = now > 모든 행 ts(과거)
  assert.strictEqual(run({ CLAUDE_DLC_SIGNAL_DIR: d, ...MOFF }), '');
});
ok('ⓖ 회전분(.1) across 마커 → 합산', () => {
  const d = sigDir();
  // 마커를 2026-07-09 로 설정, 이후 신호는 .1 3 + 현재 3 = 6 unique
  writeRows(d, Array.from({ length: 3 }, (_, i) => failRow('a' + i, 'plan-blocked', '2026-07-10T00:0' + i + ':00Z')), 'dlc-signals.jsonl.1');
  writeRows(d, Array.from({ length: 3 }, (_, i) => failRow('b' + i, 'plan-blocked', '2026-07-11T00:0' + i + ':00Z')));
  const marker = path.join(d, 'last-improve');
  fs.writeFileSync(marker, '');
  const t = new Date('2026-07-09T00:00:00Z');
  fs.utimesSync(marker, t, t);
  const out = run({ CLAUDE_DLC_SIGNAL_DIR: d, ...MOFF });
  assert.match(out, /6세션/);
});
ok('ⓗ ts 없음·null·객체 session_id → 전부 미집계(크래시 없음)', () => {
  const d = sigDir();
  writeRows(d, [
    { kind: 'plan-blocked', axis: 'failure', session_id: 'n1' }, // ts 없음 → 제외
    { kind: 'plan-blocked', axis: 'failure', session_id: 'n2' },
    { kind: 'plan-blocked', axis: 'failure', session_id: 'n3' },
    { kind: 'plan-blocked', axis: 'failure', session_id: 'n4' },
    { kind: 'plan-blocked', axis: 'failure', session_id: 'n5' },
    failRow(null, 'plan-blocked', '2026-07-10T00:00:00Z'), // null sid → 제외
    { ts: '2026-07-10T00:01:00Z', kind: 'plan-blocked', axis: 'failure', session_id: {} }, // 객체 sid → 제외
  ]);
  // 유효(문자열 sid + 유효 ts) failure 0 → 임계 1 로도 무음(불량 행이 집계 안 됨 증명)
  assert.strictEqual(run({ CLAUDE_DLC_SIGNAL_DIR: d, CLAUDE_BRIEF_IMPROVE_MIN: '1', ...MOFF }), '');
});
ok('min 음수 → 0세션 nudge 안 함(클램프 ≥1)', () => {
  const d = sigDir();
  fs.writeFileSync(path.join(d, 'dlc-signals.jsonl'), ''); // 신호 0
  assert.strictEqual(run({ CLAUDE_DLC_SIGNAL_DIR: d, CLAUDE_BRIEF_IMPROVE_MIN: '-1', ...MOFF }), '');
});
ok('ts == 마커 mtime → 제외(경계)', () => {
  const d = sigDir();
  const t = '2026-07-10T00:00:00.000Z';
  writeRows(d, Array.from({ length: 6 }, (_, i) => failRow('s' + i, 'plan-blocked', t)));
  const marker = path.join(d, 'last-improve');
  fs.writeFileSync(marker, '');
  const mt = new Date(t);
  fs.utimesSync(marker, mt, mt);
  assert.strictEqual(run({ CLAUDE_DLC_SIGNAL_DIR: d, ...MOFF }), ''); // t <= since → 제외
});
ok('main/master 는 머지 대기에서 제외(K)', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  git(r, ['checkout', '-b', 'feat1']); commit(r, 'f1'); // feat1 +1
  git(r, ['checkout', 'main']); commit(r, 'unpushedmain'); // 로컬 main +1(unpushed)
  const out = run({ CLAUDE_BRIEF_REPO: r, ...OFF });
  assert.match(out, /feat1\(\+1\)/);
  assert.doesNotMatch(out, /main\(\+/); // main 미표시
});
ok('ⓘ CLAUDE_BRIEF_IMPROVE_MIN=3 → 3에서 발화', () => {
  const d = sigDir();
  writeRows(d, Array.from({ length: 3 }, (_, i) => failRow('s' + i, 'plan-blocked', '2026-07-10T00:0' + i + ':00Z')));
  const out = run({ CLAUDE_DLC_SIGNAL_DIR: d, CLAUDE_BRIEF_IMPROVE_MIN: '3', ...MOFF });
  assert.match(out, /3세션/);
});
ok('ⓛ brief 실행 후 telemetry 파일 unchanged(no-emit)', () => {
  const d = sigDir();
  const rows = Array.from({ length: 6 }, (_, i) => failRow('s' + i, 'plan-blocked', '2026-07-10T00:0' + i + ':00Z'));
  writeRows(d, rows);
  const before = fs.readFileSync(path.join(d, 'dlc-signals.jsonl'), 'utf8');
  run({ CLAUDE_DLC_SIGNAL_DIR: d, ...MOFF });
  assert.strictEqual(fs.readFileSync(path.join(d, 'dlc-signals.jsonl'), 'utf8'), before);
});
ok('ⓚ CLAUDE_SESSION_BRIEF_OFF=1 → 완전 무음', () => {
  const d = sigDir();
  writeRows(d, Array.from({ length: 9 }, (_, i) => failRow('s' + i, 'plan-blocked', '2026-07-10T00:0' + i + ':00Z')));
  assert.strictEqual(run({ CLAUDE_DLC_SIGNAL_DIR: d, CLAUDE_SESSION_BRIEF_OFF: '1' }), '');
});

// ---------- M: 닫히지 않은 plan ----------
ok('ⓜ in_progress + 매칭 브랜치 없음 + 경과 ≥ 임계 → 1줄', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  writePlan(r, 'orphan-plan', 'in_progress', daysAgo(5));
  const out = run({ CLAUDE_BRIEF_REPO: r, ...SOFF });
  assert.match(out, /닫히지 않은 plan/);
  assert.match(out, /orphan-plan\(5d\)/);
});
ok('ⓝ 매칭 브랜치 존재 + ahead>0 → 제외(세 앵커 형태)', () => {
  for (const branch of ['anchor-a', 'worktree-anchor-a', 'feat-anchor-a']) {
    const r = initRepo();
    commit(r, 'base');
    git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
    writePlan(r, 'anchor-a', 'in_progress', daysAgo(5));
    git(r, ['checkout', '-b', branch]);
    commit(r, 'wip'); // ahead>0 = 진행 중
    assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...SOFF }), '', `branch=${branch}`);
  }
});
ok('ⓞ 매칭 브랜치 있어도 ahead 0(머지됨) → 검출(이중 블라인드 구간)', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['checkout', '-b', 'merged-work']);
  commit(r, 'work');
  git(r, ['checkout', 'main']);
  git(r, ['merge', '--ff-only', 'merged-work']);
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']); // 브랜치는 남았고 이미 머지됨
  writePlan(r, 'merged-work', 'in_progress', daysAgo(5));
  const out = run({ CLAUDE_BRIEF_REPO: r, ...SOFF });
  assert.match(out, /merged-work\(5d\)/);
});
ok('ⓟ slug 에 main 포함 → main 브랜치에 억제되지 않음', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  writePlan(r, 'main-autopull', 'in_progress', daysAgo(5));
  const out = run({ CLAUDE_BRIEF_REPO: r, ...SOFF });
  assert.match(out, /main-autopull\(5d\)/);
});
ok('ⓠ 원격 전용 브랜치가 매칭 → 제외(다머신 오탐 차단)', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  git(r, ['checkout', '-b', 'tmp']); commit(r, 'remote work');
  git(r, ['update-ref', 'refs/remotes/origin/other-machine', 'HEAD']); // 원격에만 존재
  git(r, ['checkout', 'main']); git(r, ['branch', '-D', 'tmp']);
  writePlan(r, 'other-machine', 'in_progress', daysAgo(5));
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...SOFF }), '');
});
ok('ⓡ done·blocked 는 제외', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  writePlan(r, 'closed-one', 'done', daysAgo(9));
  writePlan(r, 'stuck-one', 'blocked', daysAgo(9));
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...SOFF }), '');
});
ok('ⓢ 경과 < 임계 → 제외, STALE_DAYS 로 조정', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  writePlan(r, 'fresh-plan', 'in_progress', daysAgo(1)); // 기본 임계 3 미달
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...SOFF }), '');
  const out = run({ CLAUDE_BRIEF_REPO: r, CLAUDE_BRIEF_STALE_DAYS: '1', ...SOFF });
  assert.match(out, /fresh-plan\(1d\)/);
});
ok('ⓣ STALE_DAYS 0·음수·비숫자 → 기본값(3) 흡수', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  writePlan(r, 'two-days', 'in_progress', daysAgo(2)); // 기본 3 미달
  for (const v of ['0', '-5', 'abc', '']) {
    assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, CLAUDE_BRIEF_STALE_DAYS: v, ...SOFF }), '', `v=${v}`);
  }
});
ok('ⓤ STALE_OFF=1 로 해제 · SESSION_BRIEF_OFF=1 우선', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  writePlan(r, 'muted-plan', 'in_progress', daysAgo(5));
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...SOFF, CLAUDE_BRIEF_STALE_OFF: '1' }), '');
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, CLAUDE_SESSION_BRIEF_OFF: '1' }), '');
});
ok('ⓥ plans 부재·루트 stray 파일(ENOTDIR)·frontmatter 불량 → 무음 + exit 0', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  const res1 = spawnSync('node', [BRIEF], { env: { ...process.env, CLAUDE_BRIEF_REPO: r, ...SOFF } });
  assert.strictEqual(res1.status, 0);
  assert.strictEqual(res1.stdout.toString(), ''); // plans/ 없음
  fs.mkdirSync(path.join(r, 'plans'), { recursive: true });
  fs.writeFileSync(path.join(r, 'plans', 'stray.md'), '# not a plan dir\n'); // 디렉토리 아닌 파일
  fs.mkdirSync(path.join(r, 'plans', '2026-07-01-nofm'), { recursive: true });
  fs.writeFileSync(path.join(r, 'plans', '2026-07-01-nofm', 'nofm-plan.md'), 'no frontmatter here\n');
  const res2 = spawnSync('node', [BRIEF], { env: { ...process.env, CLAUDE_BRIEF_REPO: r, ...SOFF } });
  assert.strictEqual(res2.status, 0);
  assert.strictEqual(res2.stdout.toString(), '');
});
ok('ⓦ 불량 plan 이 있어도 유효 stale plan 은 계속 보고(파일 단위 격리)', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  fs.mkdirSync(path.join(r, 'plans'), { recursive: true });
  fs.writeFileSync(path.join(r, 'plans', 'stray.md'), 'x\n');
  writePlan(r, 'broken', 'in_progress', 'not-a-date');
  writePlan(r, 'valid-one', 'in_progress', daysAgo(6));
  const out = run({ CLAUDE_BRIEF_REPO: r, ...SOFF });
  assert.match(out, /valid-one\(6d\)/);
});
ok('ⓧ M 이 예외를 던져도 K·L 라인 보존(신호별 격리)', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  git(r, ['checkout', '-b', 'feat-live']); commit(r, 'f1');
  // plans 를 읽을 수 없게 만든다(디렉토리 자리에 파일) → M 경로에서 예외 유발
  fs.writeFileSync(path.join(r, 'plans'), 'not a directory\n');
  const out = run({ CLAUDE_BRIEF_REPO: r, CLAUDE_BRIEF_IMPROVE_OFF: '1' });
  assert.match(out, /머지 대기/); // K 는 살아 있어야 한다
  assert.match(out, /feat-live\(\+1\)/);
});
ok('ⓨ cap 5 초과 시 +N 표기 · 오래된 것 먼저', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  for (let i = 1; i <= 7; i++) writePlan(r, `p${i}`, 'in_progress', daysAgo(3 + i));
  const out = run({ CLAUDE_BRIEF_REPO: r, ...SOFF });
  assert.match(out, /p7\(10d\)/); // 가장 오래된 것이 먼저
  assert.match(out, /\+2/); // 7건 중 5건 표시 + 2
  assert.doesNotMatch(out, /p1\(4d\)/); // 가장 최근 건은 cap 밖
});
ok('ⓩ 실증: 소급 정리 4건과 동형(10·9·7·4d) → 기본 임계 3 으로 전건 검출', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  const cases = [['plan-lint', 10], ['signal-detail', 9], ['codegraph-wt-doc-fix', 7], ['code-reviewer-absorb', 4]];
  for (const [slug, d] of cases) writePlan(r, slug, 'in_progress', daysAgo(d));
  const out = run({ CLAUDE_BRIEF_REPO: r, ...SOFF });
  for (const [slug, d] of cases) assert.match(out, new RegExp(`${slug}\\(${d}d\\)`), `${slug} 미검출`);
});

console.log(`session-brief.test.js: ${n} tests passed`);
