#!/usr/bin/env node
// dlc-evidence-ledger.js 회귀 테스트 — isIgnored(cross-worktree/repo·non-git 오탐)·
// VERIFY_SCRIPT(검증 스크립트 인식/오인식) 게이트. 실 git repo fixture 위에서 hook 을
// spawn 하고 ledger 상태를 관찰한다. 신호는 SIGNAL_OFF 로 자기격리, 세션은 케이스별 unique.
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const ledger = require('./dlc-ledger.js');
const HOOK = path.join(__dirname, 'dlc-evidence-ledger.js');

let n = 0;
const ok = (name, fn) => { fn(); n++; };
let sidN = 0;
const sid = () => `led-test-${process.pid}-${sidN++}`;

function git(dir, ...args) {
  execFileSync('git', ['-C', dir, ...args], { stdio: 'ignore' });
}
function initRepo(branch) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-led-repo-'));
  execFileSync('git', ['init', '-b', branch || 'main', dir], { stdio: 'ignore' });
  git(dir, 'config', 'user.email', 't@t');
  git(dir, 'config', 'user.name', 't');
  git(dir, 'config', 'commit.gpgsign', 'false');
  return dir;
}
function W(dir, rel, body) {
  const f = path.join(dir, rel);
  fs.mkdirSync(path.dirname(f), { recursive: true });
  fs.writeFileSync(f, body == null ? 'x\n' : body);
  return f;
}
// hook 실행 후 ledger 상태. cwd 는 fp 의 repo 와 무관하게 둘 수 있다(dirname(fp) 기준 판정 검증).
function edit(fp, cwd, s) {
  const input = JSON.stringify({ session_id: s, cwd, tool_name: 'Edit', tool_input: { file_path: fp } });
  execFileSync('node', [HOOK], { input, env: { ...process.env, CLAUDE_DLC_SIGNAL_OFF: '1' } });
  return ledger.read(s);
}
function bash(command, s) {
  const input = JSON.stringify({ session_id: s, cwd: os.tmpdir(), tool_name: 'Bash', tool_input: { command } });
  execFileSync('node', [HOOK], { input, env: { ...process.env, CLAUDE_DLC_SIGNAL_OFF: '1' } });
  return ledger.read(s);
}

// ---- fixtures ----
const repoMain = initRepo();       // "main checkout" — plans/·*.log gitignored
W(repoMain, '.gitignore', 'plans/\n*.log\n');
W(repoMain, 'plans/x-plan.md', '# plan\n');
W(repoMain, 'src.js');             // 비-ignored 실소스
W(repoMain, 'doc.md');             // 비-plan 문서(.md)
W(repoMain, 'a.log');              // gitignored
const repoWt = initRepo();         // "worktree 세션 cwd" — 별개 repo
W(repoWt, '.gitignore', 'plans/\n');
W(repoWt, 'plans/y-plan.md', '# plan\n');
const nonGit = fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-led-nongit-'));
W(nonGit, 'main.py', 'print(1)\n'); // git init 전 실디렉토리 소스
const repoTracked = initRepo();    // 방안 A: plans/ 가 tracked(gitignore 에 없음)
W(repoTracked, '.gitignore', '*.log\n'); // plans/ 는 무시 안 함 → tracked
W(repoTracked, 'plans/z-plan.md', '# plan\n');
W(repoTracked, 'app.js');          // 비-plan 실소스

// ---- ① isIgnored: fp 자기 repo 기준(cross-worktree/repo 오탐 제거) ----
ok('① cross-worktree: 다른 repo cwd 에서 main 의 gitignored plans 편집 → changed=false', () => {
  assert.strictEqual(edit(path.join(repoMain, 'plans/x-plan.md'), repoWt, sid()).changed, false);
});
ok('① 거울방향: main cwd 에서 worktree repo 의 gitignored plans 편집 → changed=false', () => {
  assert.strictEqual(edit(path.join(repoWt, 'plans/y-plan.md'), repoMain, sid()).changed, false);
});
ok('② /tmp 비-git 스크래치 파일 편집 → changed=false (exit 128)', () => {
  const f = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-led-tmp-')), 'scratch.js');
  fs.writeFileSync(f, 'x');
  assert.strictEqual(edit(f, repoWt, sid()).changed, false);
});
ok('③ 같은 repo 비-ignored 실소스 편집 → changed=true (비회귀)', () => {
  assert.strictEqual(edit(path.join(repoMain, 'src.js'), repoMain, sid()).changed, true);
});
ok('③b 비-plan .md 문서 편집 → changed=false (verify 게이트 밖 — doc-only 오탐 방지)', () => {
  assert.strictEqual(edit(path.join(repoMain, 'doc.md'), repoMain, sid()).changed, false);
});
ok('③c 코드검증 후 .md 편집이 verified 를 리셋하지 않음 (문서≠코드 무효화)', () => {
  const s = sid();
  edit(path.join(repoMain, 'src.js'), repoMain, s); // changed=true, verified=false
  bash('node src.test.js', s); // VERIFY 매치 → verified=true
  const d = edit(path.join(repoMain, 'doc.md'), repoMain, s); // .md 편집 → verified 유지해야
  assert.strictEqual(d.verified, true);
});
ok('④ 같은 repo gitignored(*.log) 편집 → changed=false (비회귀)', () => {
  assert.strictEqual(edit(path.join(repoMain, 'a.log'), repoMain, sid()).changed, false);
});
ok('⑪ 방안 A: tracked plans/ 편집 → changed=false (isPlan 명시 제외, gitignore 무관)', () => {
  assert.strictEqual(edit(path.join(repoTracked, 'plans/z-plan.md'), repoTracked, sid()).changed, false);
});
ok('⑪ʹ 방안 A repo: 비-plan 실소스(app.js) 편집 → changed=true (isPlan 과대적용 아님)', () => {
  assert.strictEqual(edit(path.join(repoTracked, 'app.js'), repoTracked, sid()).changed, true);
});
ok('⑨ non-git 실디렉토리 소스(main.py) 편집 → changed=false (S3 완화 고정)', () => {
  assert.strictEqual(edit(path.join(nonGit, 'main.py'), repoMain, sid()).changed, false);
});
ok('⑩ repo 안 dir 부재(check-ignore 실패) → changed=true (broken 보수 분기)', () => {
  // dir(repoMain/nope) 부재 → check-ignore spawn 실패지만 .git 조상 존재 → 보수적 changed
  assert.strictEqual(edit(path.join(repoMain, 'nope/file.js'), repoMain, sid()).changed, true);
});
ok('⑩ʹ repo 밖 dir 부재 → changed=false (완화: 어떤 repo 조상도 없음)', () => {
  assert.strictEqual(edit('/no/such/dir/zzz/file.js', repoMain, sid()).changed, false);
});
ok('③ 편집 후 verified·blocks 리셋 유지(비회귀)', () => {
  const s = sid();
  edit(path.join(repoMain, 'src.js'), repoMain, s);
  const d = ledger.read(s);
  assert.strictEqual(d.verified, false);
  assert.strictEqual(d.blocks, 0);
});

// ---- ② VERIFY_SCRIPT: 검증 스크립트 래핑 인식 / 비검증 스크립트 오인식 차단 ----
const V = (cmd) => bash(cmd, sid()).verified;
ok('⑤ bash /tmp/x-verify.sh → verified=true', () => assert.strictEqual(V('bash /tmp/x-verify.sh'), true));
ok('⑤ bash verify.sh → verified=true', () => assert.strictEqual(V('bash verify.sh'), true));
ok('⑧ git add . && bash x-verify.sh → verified=true (체인 앵커)', () =>
  assert.strictEqual(V('git add . && bash x-verify.sh'), true));
ok('⑦ bash checkout.sh → verified 불변 (B1 오탐 회귀 락)', () =>
  assert.strictEqual(V('bash checkout.sh'), false));
ok('⑦ bash ./scripts/test-data-loader.sh → verified 불변 (B1)', () =>
  assert.strictEqual(V('bash ./scripts/test-data-loader.sh'), false));
ok('⑦ bash latest.sh → verified 불변', () => assert.strictEqual(V('bash latest.sh'), false));
ok('⑦ echo bash verify.sh → verified 불변 (NONVERIFY veto + 앵커)', () =>
  assert.strictEqual(V('echo bash verify.sh'), false));
ok('⑥ bash deploy.sh → verified 불변', () => assert.strictEqual(V('bash deploy.sh'), false));
ok('⑥ cat test.md → verified 불변', () => assert.strictEqual(V('cat test.md'), false));
ok('⑥ bash verify.sh.bak → verified 불변 (lookahead: .sh 뒤 . 거부)', () =>
  assert.strictEqual(V('bash verify.sh.bak'), false));
ok('기존 VERIFY 비회귀: npm test → verified=true', () => assert.strictEqual(V('npm test'), true));
ok('기존 VERIFY 비회귀: pytest → verified=true', () => assert.strictEqual(V('pytest -q'), true));
// node 테스트 인식(이 repo 방식) — VERIFY 미인식 오탐 수정
ok('node scripts/x.test.js → verified=true', () => assert.strictEqual(V('node scripts/dlc-signal.test.js'), true));
ok('node --test → verified=true', () => assert.strictEqual(V('node --test'), true));
ok('node a.test.mjs → verified=true', () => assert.strictEqual(V('node a.test.mjs'), true));
ok('node app.js → verified 불변 (테스트 아님)', () => assert.strictEqual(V('node app.js'), false));
ok('node --test-only server.js → verified 불변 (--test 완전 토큰만)', () =>
  assert.strictEqual(V('node --test-only server.js'), false));
ok('node -e "..x.test.js.." → verified 불변 (인용문 내 미매칭)', () =>
  assert.strictEqual(V('node -e "require(\'./x.test.js\')"'), false));

console.log(`dlc-evidence-ledger.test.js: ${n} tests passed`);
