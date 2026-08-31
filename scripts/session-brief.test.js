#!/usr/bin/env node
// session-brief.js 테스트 — K(머지대기 브랜치) + L(improve nudge) + M(닫히지 않은 plan).
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
// repo 를 안 준 테스트가 실제 ~/.claude 를 보지 않도록 쓰는 빈 fixture.
// 예전엔 실 repo 가 우연히 조용해서 통과했지만, 그 repo 가 뒤처지거나 미머지 브랜치가 생기면
// 관계없는 테스트가 깨진다(실제로 겪었다 — 자동 pull 신호 추가 후 L 축 테스트가 무너졌다).
let _blankRepo;
function blankRepo() {
  if (!_blankRepo) {
    _blankRepo = fs.mkdtempSync(path.join(os.tmpdir(), 'sb-blank-'));
    execFileSync('git', ['init', '-q', '-b', 'main', _blankRepo], { stdio: 'ignore' });
  }
  return _blankRepo;
}
let _blankSignalDir;
function blankSignalDir() {
  if (!_blankSignalDir) _blankSignalDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sb-blanksig-'));
  return _blankSignalDir;
}

// run brief; returns stdout string.
// hookCwd: O 신호가 보는 repo(= hook stdin JSON 의 cwd). 명시 안 하면 빈 fixture — 안 그러면
// 모든 기존 테스트가 이 파일이 놓인 실 worktree 상태에 물든다(K/M/N 을 fixture 로 돌린 것과 같은 이유).
// hookCwd 를 null 로 주면 stdin 을 비워 "JSON 없음" 경로(process.cwd() 폴백)를 탄다.
// spawnCwd: 그 폴백이 무엇을 보는지 결정하는 프로세스 cwd.
function run(env, hookCwd, spawnCwd) {
  const merged = { ...process.env, ...env };
  // 테스트가 명시하지 않은 입력은 실 환경이 아니라 빈 fixture 를 보게 한다
  // (process.env 에 값이 있어도 테스트 기본값이 이기도록 병합 후 덮어쓴다).
  if (!env || !env.CLAUDE_BRIEF_REPO) merged.CLAUDE_BRIEF_REPO = blankRepo();
  if (!env || !env.CLAUDE_DLC_SIGNAL_DIR) merged.CLAUDE_DLC_SIGNAL_DIR = blankSignalDir();
  const input =
    hookCwd === null
      ? ''
      : JSON.stringify({ hook_event_name: 'SessionStart', cwd: hookCwd || blankRepo() });
  const opts = { env: merged, input };
  if (spawnCwd) opts.cwd = spawnCwd;
  try {
    return execFileSync('node', [BRIEF], opts).toString();
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
const KLOFF = { CLAUDE_BRIEF_MERGE_OFF: '1', CLAUDE_BRIEF_IMPROVE_OFF: '1' }; // M 테스트 시 K·L 끄기
// O 테스트 시 K·L·M·N 끄기 / 그 반대로 O 만 끄기. O 는 hook stdin 의 cwd 를 보므로 기본 fixture 가
// 조용하지만, 명시적으로 꺼 두는 편이 단언 실패 시 원인을 좁힌다.
const OOFF = { CLAUDE_BRIEF_MERGE_OFF: '1', CLAUDE_BRIEF_IMPROVE_OFF: '1', CLAUDE_BRIEF_STALE_OFF: '1', CLAUDE_BRIEF_AUTOPULL_OFF: '1' };

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
  const out = run({ CLAUDE_BRIEF_REPO: r, ...KLOFF });
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
    assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...KLOFF }), '', `branch=${branch}`);
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
  const out = run({ CLAUDE_BRIEF_REPO: r, ...KLOFF });
  assert.match(out, /merged-work\(5d\)/);
});
ok('ⓟ slug 에 main 포함 → main 브랜치에 억제되지 않음', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  writePlan(r, 'main-autopull', 'in_progress', daysAgo(5));
  const out = run({ CLAUDE_BRIEF_REPO: r, ...KLOFF });
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
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...KLOFF }), '');
});
ok('ⓡ done·blocked 는 제외', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  writePlan(r, 'closed-one', 'done', daysAgo(9));
  writePlan(r, 'stuck-one', 'blocked', daysAgo(9));
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...KLOFF }), '');
});
ok('ⓢ 경과 < 임계 → 제외, STALE_DAYS 로 조정', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  writePlan(r, 'fresh-plan', 'in_progress', daysAgo(1)); // 기본 임계 3 미달
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...KLOFF }), '');
  const out = run({ CLAUDE_BRIEF_REPO: r, CLAUDE_BRIEF_STALE_DAYS: '1', ...KLOFF });
  assert.match(out, /fresh-plan\(1d\)/);
});
ok('ⓣ STALE_DAYS 0·음수·비숫자 → 기본값(3) 흡수', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  writePlan(r, 'two-days', 'in_progress', daysAgo(2)); // 기본 3 미달
  for (const v of ['0', '-5', 'abc', '']) {
    assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, CLAUDE_BRIEF_STALE_DAYS: v, ...KLOFF }), '', `v=${v}`);
  }
});
ok('ⓤ STALE_OFF=1 로 해제 · SESSION_BRIEF_OFF=1 우선', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  writePlan(r, 'muted-plan', 'in_progress', daysAgo(5));
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...KLOFF, CLAUDE_BRIEF_STALE_OFF: '1' }), '');
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, CLAUDE_SESSION_BRIEF_OFF: '1' }), '');
});
ok('ⓥ plans 부재·루트 stray 파일(ENOTDIR)·frontmatter 불량 → 무음 + exit 0', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  const res1 = spawnSync('node', [BRIEF], { env: { ...process.env, CLAUDE_BRIEF_REPO: r, ...KLOFF } });
  assert.strictEqual(res1.status, 0);
  assert.strictEqual(res1.stdout.toString(), ''); // plans/ 없음
  fs.mkdirSync(path.join(r, 'plans'), { recursive: true });
  fs.writeFileSync(path.join(r, 'plans', 'stray.md'), '# not a plan dir\n'); // 디렉토리 아닌 파일
  fs.mkdirSync(path.join(r, 'plans', '2026-07-01-nofm'), { recursive: true });
  fs.writeFileSync(path.join(r, 'plans', '2026-07-01-nofm', 'nofm-plan.md'), 'no frontmatter here\n');
  const res2 = spawnSync('node', [BRIEF], { env: { ...process.env, CLAUDE_BRIEF_REPO: r, ...KLOFF } });
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
  const out = run({ CLAUDE_BRIEF_REPO: r, ...KLOFF });
  assert.match(out, /valid-one\(6d\)/);
});
// M 이 스캔 불가 상태여도 K 라인은 남는다. 단 이 경로는 stalePlanLine 내부 try 가 null 로
// 흡수하므로 main() 의 collect() catch 까지는 가지 않는다 — collect 의 try 는 미래 회귀 대비 방어물이고
// CLI 통합 테스트로는 관측할 수 없다(그 사실을 숨기지 않기 위해 이름을 이렇게 둔다).
ok('ⓧ M 스캔 불가(plans 가 디렉토리 아님) → M 무음 + K 라인 보존', () => {
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
  const out = run({ CLAUDE_BRIEF_REPO: r, ...KLOFF });
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
  const out = run({ CLAUDE_BRIEF_REPO: r, ...KLOFF });
  for (const [slug, d] of cases) assert.match(out, new RegExp(`${slug}\\(${d}d\\)`), `${slug} 미검출`);
});

ok('M-1 §10 정본 템플릿의 status 인라인 주석을 값으로 오인하지 않음', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  const dir = path.join(r, 'plans', '2026-07-01-tpl-plan-dir');
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(
    path.join(dir, 'tpl-plan.md'),
    `---\ntitle: tpl — t\nstatus: in_progress  # in_progress | blocked | done\nstarted: 2026-07-01\nupdated: ${daysAgo(6)}\n---\n\n# Goal\nt\n`,
  );
  assert.match(run({ CLAUDE_BRIEF_REPO: r, ...KLOFF }), /tpl\(6d\)/);
});
ok('M-2 CRLF frontmatter 도 파싱됨(text=auto 체크아웃)', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  const dir = path.join(r, 'plans', '2026-07-01-crlf');
  fs.mkdirSync(dir, { recursive: true });
  const lf = `---\ntitle: crlf — t\nstatus: in_progress\nstarted: 2026-07-01\nupdated: ${daysAgo(6)}\n---\n\n# Goal\nt\n`;
  fs.writeFileSync(path.join(dir, 'crlf-plan.md'), lf.replace(/\n/g, '\r\n'));
  assert.match(run({ CLAUDE_BRIEF_REPO: r, ...KLOFF }), /crlf\(6d\)/);
});
ok('M-3 오래된 done 이 MAX_PLANS 예산을 먹어도 최신 in_progress 는 스캔됨', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  fs.mkdirSync(path.join(r, 'plans'), { recursive: true });
  fs.writeFileSync(path.join(r, 'plans', '0000-stray.md'), 'x\n'); // 예산을 먹던 stray
  for (let i = 1; i <= 30; i++) {
    writePlan(r, `old${i}`, 'done', daysAgo(90), `2020-01-${String(i).padStart(2, '0')}-old${i}`);
  }
  writePlan(r, 'newest-open', 'in_progress', daysAgo(6), '2026-07-20-newest-open');
  assert.match(run({ CLAUDE_BRIEF_REPO: r, ...KLOFF }), /newest-open\(6d\)/);
});
ok('M-4 updated 불량·부재 → started 로 폴백(가장 방치된 plan 이 빠지지 않게)', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  const dir = path.join(r, 'plans', '2026-07-01-nofallback');
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(
    path.join(dir, 'badupd-plan.md'),
    `---\ntitle: badupd — t\nstatus: in_progress\nstarted: ${daysAgo(12)}\nupdated: 2026-7-20 (fix)\n---\n\n# Goal\nt\n`,
  );
  assert.match(run({ CLAUDE_BRIEF_REPO: r, ...KLOFF }), /badupd\(12d\)/);
});
ok('M-5 존재하지 않는 날짜(2026-02-31)는 롤오버로 오보고하지 않음', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  const dir = path.join(r, 'plans', '2026-07-01-roll');
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(
    path.join(dir, 'roll-plan.md'),
    '---\ntitle: roll — t\nstatus: in_progress\nstarted: 2026-02-31\nupdated: 2026-02-31\n---\n\n# Goal\nt\n',
  );
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...KLOFF }), '');
});
ok('M-6 origin/main 부재 → 브랜치 있으면 제외·없으면 보고(보수 폴백)', () => {
  const r1 = initRepo();
  commit(r1, 'base'); // origin/main 미설정
  writePlan(r1, 'no-remote-open', 'in_progress', daysAgo(6));
  assert.match(run({ CLAUDE_BRIEF_REPO: r1, ...KLOFF }), /no-remote-open\(6d\)/);
  const r2 = initRepo();
  commit(r2, 'base');
  writePlan(r2, 'has-branch', 'in_progress', daysAgo(6));
  git(r2, ['checkout', '-b', 'has-branch']);
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r2, ...KLOFF }), '');
});

// ---------- N: 자동 pull 이 밀린 이유 ----------
// 다른 신호를 끈 상태로 N 만 관찰. STALE_OFF 필수 — repoDir 의 plans/ 상태에 흔들리지 않게.
const NOFF = {
  CLAUDE_BRIEF_MERGE_OFF: '1',
  CLAUDE_BRIEF_IMPROVE_OFF: '1',
  CLAUDE_BRIEF_STALE_OFF: '1',
};
// origin/main 을 앞세운 뒤 로컬을 되감아 'behind n' 상태를 만든다.
// opts.touchBase: 원격 커밋이 **base 에 이미 있던 tracked 파일**을 고치게 한다(사고 원본 형태).
//   기본(false)은 원격이 새 파일을 추가하는 형태라, 로컬에서 같은 이름을 만들면 untracked 가 된다.
function behindRepo(n, opts) {
  const r = initRepo();
  fs.writeFileSync(path.join(r, 'base.txt'), 'v0');
  git(r, ['add', '-A']);
  git(r, ['commit', '-m', 'base'], { GIT_AUTHOR_DATE: '2026-01-01T00:00:00', GIT_COMMITTER_DATE: '2026-01-01T00:00:00' });
  const base = execFileSync('git', ['-C', r, 'rev-parse', 'HEAD']).toString().trim();
  for (let i = 0; i < n; i++) {
    if (opts && opts.touchBase) {
      fs.writeFileSync(path.join(r, 'base.txt'), `remote${i}`);
      git(r, ['add', '-A']);
      git(r, ['commit', '-m', `remote${i}`], { GIT_AUTHOR_DATE: '2026-01-02T00:00:00', GIT_COMMITTER_DATE: '2026-01-02T00:00:00' });
    } else {
      commit(r, `remote${i}`);
    }
  }
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  git(r, ['reset', '--hard', base]);
  return r;
}

ok('ⓝ1 최신이면 무음', () => {
  const r = initRepo();
  commit(r, 'base');
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...NOFF }), '');
});

ok('ⓝ2 behind 면 커밋 수를 알린다', () => {
  const out = run({ CLAUDE_BRIEF_REPO: behindRepo(3), ...NOFF });
  assert.match(out, /3커밋 뒤처짐/);
});

ok('ⓝ3 원격이 새로 추가하는 파일과 untracked 가 겹치면 지목한다', () => {
  const r = behindRepo(2);
  fs.writeFileSync(path.join(r, 'remote0.txt'), 'local-dirty'); // base 엔 없던 파일 = untracked
  const out = run({ CLAUDE_BRIEF_REPO: r, ...NOFF });
  assert.match(out, /remote0\.txt/);
});

// 사고 원본 경로: base 에 있던 tracked 파일을 원격도 고치고 로컬도 고친 경우.
// ⓝ3 은 untracked 만 덮으므로 이 둘이 없으면 diff/diff --cached 소스가 통째로 미검증이다.
ok('ⓝ3b tracked 파일 수정이 원격 변경과 겹치면 지목한다', () => {
  const r = behindRepo(1, { touchBase: true });
  fs.writeFileSync(path.join(r, 'base.txt'), 'local-dirty');
  assert.match(run({ CLAUDE_BRIEF_REPO: r, ...NOFF }), /base\.txt/);
});

ok('ⓝ3c staged 수정도 지목한다', () => {
  const r = behindRepo(1, { touchBase: true });
  fs.writeFileSync(path.join(r, 'base.txt'), 'local-dirty');
  git(r, ['add', 'base.txt']);
  assert.match(run({ CLAUDE_BRIEF_REPO: r, ...NOFF }), /base\.txt/);
});

ok('ⓝ4 무관한 파일만 더러우면 충돌로 지목하지 않는다', () => {
  const r = behindRepo(2);
  fs.writeFileSync(path.join(r, 'unrelated.txt'), 'x');
  git(r, ['add', '-A']);
  const out = run({ CLAUDE_BRIEF_REPO: r, ...NOFF });
  assert.match(out, /2커밋 뒤처짐/);
  assert.ok(!/unrelated\.txt/.test(out), out);
});

ok('ⓝ5 main 이 아니면 그 사실을 알린다', () => {
  const r = behindRepo(1);
  git(r, ['checkout', '-q', '-b', 'feature-x']);
  assert.match(run({ CLAUDE_BRIEF_REPO: r, ...NOFF }), /feature-x/);
});

ok('ⓝ6 detached HEAD 를 별도 사유로 구분한다', () => {
  const r = behindRepo(1);
  git(r, ['checkout', '-q', '--detach']);
  assert.match(run({ CLAUDE_BRIEF_REPO: r, ...NOFF }), /detached/i);
});

ok('ⓝ7 kill-switch 로 끌 수 있다', () => {
  const r = behindRepo(3);
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...NOFF, CLAUDE_BRIEF_AUTOPULL_OFF: '1' }), '');
});

// 아래 4개는 "스스로 낫지 않는 원인"이다. 폴백("원인 미확인")으로 뭉뚱그리면 사용자가
// 재시도되겠거니 하고 넘어가 무기한 stale 이 된다 — 이 신호가 없애려던 실패 모드 그 자체.
ok('ⓝ9 diverge 는 ff 불가라고 명시한다(재시도로 안 풀림)', () => {
  const r = behindRepo(2);
  commit(r, 'local-only');
  const out = run({ CLAUDE_BRIEF_REPO: r, ...NOFF });
  assert.match(out, /갈라져|ff-only/);
  assert.ok(!/원인 미확인/.test(out), out);
});

ok('ⓝ10 rebase/merge 진행 중이면 그 사실을 말한다', () => {
  const r = behindRepo(1);
  fs.mkdirSync(path.join(r, '.git', 'rebase-merge'), { recursive: true });
  assert.match(run({ CLAUDE_BRIEF_REPO: r, ...NOFF }), /rebase-merge/);
});

ok('ⓝ11 CLAUDE_AUTOPULL_OFF 로 꺼둔 상태를 구분한다', () => {
  const r = behindRepo(1);
  const out = run({ CLAUDE_BRIEF_REPO: r, ...NOFF, CLAUDE_AUTOPULL_OFF: '1' });
  assert.match(out, /CLAUDE_AUTOPULL_OFF/);
});

ok('ⓝ12 master 는 훅이 안 도는 브랜치임을 말한다(훅은 main 만)', () => {
  const r = behindRepo(1);
  git(r, ['branch', '-m', 'master']);
  const out = run({ CLAUDE_BRIEF_REPO: r, ...NOFF });
  assert.match(out, /master/);
  assert.ok(!/원인 미확인/.test(out), out);
});

ok('ⓝ13 로컬에 막는 요인이 없으면 원인을 단정하지 않는다', () => {
  assert.match(run({ CLAUDE_BRIEF_REPO: behindRepo(2), ...NOFF }), /원인 미확인/);
});

ok('ⓝ14 충돌 파일이 cap 을 넘으면 +N 으로 줄인다', () => {
  const r = initRepo();
  fs.writeFileSync(path.join(r, 'seed.txt'), 'v0');
  git(r, ['add', '-A']);
  git(r, ['commit', '-m', 'base']);
  const base = execFileSync('git', ['-C', r, 'rev-parse', 'HEAD']).toString().trim();
  for (let i = 0; i < 7; i++) fs.writeFileSync(path.join(r, `f${i}.txt`), 'remote');
  git(r, ['add', '-A']);
  git(r, ['commit', '-m', 'remote-many']);
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  git(r, ['reset', '--hard', base]);
  for (let i = 0; i < 7; i++) fs.writeFileSync(path.join(r, `f${i}.txt`), 'local');
  assert.match(run({ CLAUDE_BRIEF_REPO: r, ...NOFF }), /\+2/);
});

ok('ⓝ8 origin/main 이 없으면 무음(판정 불가)', () => {
  const r = initRepo();
  commit(r, 'base');
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...NOFF }), '');
});

// ---------- O: 현재 작업 repo(세션 cwd) ----------
// upstream 을 가진 fixture. behind 만큼 원격이 앞서고, ahead 만큼 로컬이 앞선다.
function upstreamRepo(behind, ahead) {
  const r = initRepo();
  commit(r, 'base');
  const base = execFileSync('git', ['-C', r, 'rev-parse', 'HEAD']).toString().trim();
  for (let i = 0; i < behind; i++) commit(r, `remote${i}`);
  git(r, ['update-ref', 'refs/remotes/origin/main', 'HEAD']);
  git(r, ['reset', '--hard', base]);
  // remote 를 실제로 등록하지 않고 upstream 만 세운다 — `--set-upstream-to` 는 remote 설정이 없으면
  // 거부하지만(exit 128), config 두 줄이면 `@{upstream}` 은 refs/remotes/origin/main 으로 해석된다.
  git(r, ['config', 'branch.main.remote', 'origin']);
  git(r, ['config', 'branch.main.merge', 'refs/heads/main']);
  for (let i = 0; i < ahead; i++) commit(r, `local${i}`);
  return r;
}
function ageFile(file, days) {
  const t = Date.now() / 1000 - days * 86400;
  fs.utimesSync(file, t, t);
}

ok('ⓞ1 세션 repo 가 upstream 보다 뒤처지면 repo 이름과 함께 1줄', () => {
  const r = upstreamRepo(2, 0);
  const out = run({ ...OOFF }, r);
  assert.match(out, new RegExp(path.basename(r)));
  assert.match(out, /2커밋 뒤처짐/);
  assert.doesNotMatch(out, /~\/\.claude/); // 라벨이 ~/.claude 로 새지 않는다(이번 수정의 핵심)
});

ok('ⓞ2 갈라져 있으면(ahead>0) ff 로 못 따라잡는다고 말한다', () => {
  const out = run({ ...OOFF }, upstreamRepo(2, 1));
  assert.match(out, /갈라/);
  assert.match(out, /rebase|push/);
});

ok('ⓞ3 동기화 + clean 이면 무음', () => {
  assert.strictEqual(run({ ...OOFF }, upstreamRepo(0, 0)), '');
});

ok('ⓞ4 임계 이상 방치된 미커밋은 알린다', () => {
  const r = upstreamRepo(0, 0);
  const f = path.join(r, 'stale-edit.txt');
  fs.writeFileSync(f, 'edited');
  ageFile(f, 5);
  const out = run({ ...OOFF }, r);
  assert.match(out, /미커밋/);
  assert.match(out, /stale-edit\.txt/);
});

ok('ⓞ5 방금 만든 미커밋은 무음(편집 중인 파일로 매 세션 울리지 않는다)', () => {
  const r = upstreamRepo(0, 0);
  fs.writeFileSync(path.join(r, 'fresh.txt'), 'edited');
  assert.strictEqual(run({ ...OOFF }, r), '');
});

ok('ⓞ6 upstream 이 없으면 밀림은 판정하지 않는다 — 그래도 묵은 미커밋은 알린다', () => {
  const r = initRepo();
  commit(r, 'base');
  assert.strictEqual(run({ ...OOFF }, r), ''); // 셀 기준도 없고 clean → 무음
  const f = path.join(r, 'x.txt');
  fs.writeFileSync(f, 'dirty');
  ageFile(f, 5);
  const out = run({ ...OOFF }, r);
  assert.match(out, /미커밋 5일/); // 미커밋은 원격과 무관한 사실이다
  assert.doesNotMatch(out, /뒤처짐/); // 기준이 없으면 숫자를 지어내지 않는다
});

ok('ⓞ7 세션 repo 가 감시 repo 자신이면 무음(N 과 중복하지 않는다)', () => {
  const r = upstreamRepo(2, 0);
  assert.strictEqual(run({ CLAUDE_BRIEF_REPO: r, ...OOFF }, r), '');
});

ok('ⓞ8 git repo 가 아니면 무음', () => {
  assert.strictEqual(run({ ...OOFF }, fs.mkdtempSync(path.join(os.tmpdir(), 'sb-nogit-'))), '');
});

ok('ⓞ9 kill switch 로 끌 수 있다', () => {
  const r = upstreamRepo(2, 0);
  assert.strictEqual(run({ ...OOFF, CLAUDE_BRIEF_CWD_OFF: '1' }, r), '');
});

ok('ⓞ10 stdin JSON 이 없으면 프로세스 cwd 로 폴백한다(터미널 직접 실행)', () => {
  const r = upstreamRepo(2, 0);
  assert.match(run({ ...OOFF }, null, r), /2커밋 뒤처짐/);
});

ok('격리: repo 를 안 주면 실 ~/.claude 가 아니라 빈 fixture 를 본다', () => {
  // 이게 깨지면 실 repo 상태(뒤처짐·미머지 브랜치·방치된 plan)가 무관한 테스트를 흔든다.
  assert.strictEqual(run({}), '');
});

console.log(`session-brief.test.js: ${n} tests passed`);
