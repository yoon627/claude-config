#!/usr/bin/env node
// install-hooks.sh 회귀 테스트 — post-checkout(main-autopull ⓐ) + 마이그레이션 idempotency.
// hermetic: 임시 HOME(가짜 guard) + 로컬 bare origin. network 무의존, 결정적.
'use strict';
const { execFileSync, spawnSync } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

const INSTALL_SH = path.join(__dirname, 'install-hooks.sh');
let fail = 0;
function ok(name, cond) { if (!cond) fail++; console.log(`${cond ? 'PASS' : 'FAIL'} ${name}`); }

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'ma-hooks-'));
const HOME = path.join(TMP, 'home');
fs.mkdirSync(path.join(HOME, '.claude', 'scripts'), { recursive: true });
const guard = path.join(HOME, '.claude', 'scripts', 'pre-commit-check.sh');
fs.writeFileSync(guard, '#!/bin/sh\nexit 0\n'); fs.chmodSync(guard, 0o755);

const GENV = {
  GIT_AUTHOR_NAME: 't', GIT_AUTHOR_EMAIL: 't@t',
  GIT_COMMITTER_NAME: 't', GIT_COMMITTER_EMAIL: 't@t', GIT_TERMINAL_PROMPT: '0',
};
// scrub ambient vars that would leak into the hook and skew scenarios:
// the kill-switch (a dev with it exported would false-fail ①⑥) and git dir overrides.
const BASE_ENV = { ...process.env };
delete BASE_ENV.CLAUDE_AUTOPULL_OFF;
delete BASE_ENV.GIT_DIR;
delete BASE_ENV.GIT_WORK_TREE;
function git(dir, args, extraEnv) {
  return execFileSync('git', ['-C', dir, ...args], {
    env: { ...BASE_ENV, ...GENV, ...(extraEnv || {}) },
    stdio: ['ignore', 'pipe', 'pipe'], timeout: 30000,
  }).toString();
}
// checkout capturing combined stdout+stderr (git routes hook echo to either); tolerates non-zero exit.
function checkout(dir, ref, extraEnv, newBranch) {
  const args = newBranch ? ['checkout', '-q', '-B', ref] : ['checkout', '-q', ref];
  const r = spawnSync('git', ['-C', dir, ...args], {
    env: { ...BASE_ENV, ...GENV, ...(extraEnv || {}) },
    encoding: 'utf8', timeout: 30000,
  });
  return (r.stdout || '') + (r.stderr || '');
}
function sha(f) { return crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex'); }
function head(dir) { return git(dir, ['rev-parse', 'HEAD']).trim(); }
function install(cwd, extraEnv) {
  return execFileSync('bash', [INSTALL_SH], {
    cwd, env: { ...BASE_ENV, HOME, ...(extraEnv || {}) },
    stdio: ['ignore', 'pipe', 'pipe'], timeout: 30000,
  }).toString();
}

// ---- fixture: bare origin + work clone ----
const origin = path.join(TMP, 'origin.git');
execFileSync('git', ['init', '-q', '--bare', '-b', 'main', origin]);
const work = path.join(TMP, 'work');
execFileSync('git', ['clone', '-q', origin, work]);
git(work, ['config', 'user.email', 't@t']);
git(work, ['config', 'user.name', 't']);
git(work, ['config', 'commit.gpgsign', 'false']);
fs.writeFileSync(path.join(work, 'f.txt'), 'a\n');
git(work, ['add', 'f.txt']); git(work, ['commit', '-qm', 'init']);
git(work, ['push', '-q', 'origin', 'main']);
git(work, ['branch', '--set-upstream-to=origin/main', 'main']);

// origin/main 을 한 커밋 전진시키는 pusher (independent clone)
function advanceOrigin() {
  const p = fs.mkdtempSync(path.join(TMP, 'pusher-'));
  execFileSync('git', ['clone', '-q', origin, p]);
  git(p, ['config', 'user.email', 't@t']); git(p, ['config', 'user.name', 't']);
  git(p, ['config', 'commit.gpgsign', 'false']);
  fs.appendFileSync(path.join(p, 'f.txt'), 'x\n');
  git(p, ['commit', '-qam', 'advance']); git(p, ['push', '-q', 'origin', 'main']);
  return head(p);
}
// work 를 origin/main 최신으로 리셋(시나리오 사이 정리)
function syncWork() {
  git(work, ['checkout', '-q', '-B', 'main', 'origin/main']);
  git(work, ['fetch', '-q', 'origin']);
  git(work, ['reset', '-q', '--hard', 'origin/main']);
}

// ---- install ----
install(work);
const preCommit = path.join(work, '.git', 'hooks', 'pre-commit');
const prePush = path.join(work, '.git', 'hooks', 'pre-push');
const postCo = path.join(work, '.git', 'hooks', 'post-checkout');
ok('install: post-checkout 생성', fs.existsSync(postCo));
ok('install: pre-commit·pre-push 유지', fs.existsSync(preCommit) && fs.existsSync(prePush));

// ---- P4 마이그레이션/재실행 idempotency: byte-hash 불변 + .bak 미생성 ----
const hPre = fs.existsSync(preCommit) ? sha(preCommit) : 'x';
const hPush = fs.existsSync(prePush) ? sha(prePush) : 'y';
install(work); // 재실행
ok('P4 재실행: pre-commit sha 불변', fs.existsSync(preCommit) && sha(preCommit) === hPre);
ok('P4 재실행: pre-push sha 불변', fs.existsSync(prePush) && sha(prePush) === hPush);
ok('P4 재실행: .bak 미생성', !fs.existsSync(preCommit + '.bak') && !fs.existsSync(prePush + '.bak'));

// ---- ① feature→main checkout → 자동 ff ----
syncWork();
const at1 = advanceOrigin();
checkout(work, 'feature', {}, true);   // -B feature (from current main)
checkout(work, 'main');                // post-checkout → ff pull
ok('① feature→main: origin 으로 ff', head(work) === at1);

// ---- ⑤ kill-switch: CLAUDE_AUTOPULL_OFF=1 → no pull ----
syncWork();
const behind5 = head(work);
advanceOrigin();
checkout(work, 'feature', {}, true);
checkout(work, 'main', { CLAUDE_AUTOPULL_OFF: '1' });
ok('⑤ CLAUDE_AUTOPULL_OFF=1 → pull skip(behind 유지)', head(work) === behind5);

// ---- ② dirty → skip ----
syncWork();
const behind2 = head(work);
advanceOrigin();
checkout(work, 'feature', {}, true);
fs.appendFileSync(path.join(work, 'f.txt'), 'dirty\n'); // 수정된 tracked → dirty
checkout(work, 'main');                                 // dirty → hook skip
ok('② dirty → pull skip(behind 유지)', head(work) === behind2);
git(work, ['checkout', '-q', '--', 'f.txt']);           // clean up

// ---- ③ main 로컬 커밋(ff 불가) → 경고·미rebase ----
syncWork();
fs.appendFileSync(path.join(work, 'g.txt'), 'local\n');
git(work, ['add', 'g.txt']); git(work, ['commit', '-qm', 'local-only']);
const localHead = head(work);
advanceOrigin();                                        // origin 이 다르게 전진 → diverged
checkout(work, 'feature', {}, true);
const out3 = checkout(work, 'main');                    // ff 실패
ok('③ ff 불가 → HEAD 불변(미rebase)', head(work) === localHead);
ok('③ ff 실패 경고 출력', /post-checkout/.test(out3) && /(ff|fast-forward)/i.test(out3));

// ---- ④ worktree add(feature 브랜치) → 무영향 ----
syncWork();
const mainBefore4 = head(work);
advanceOrigin();
const wtPath = path.join(TMP, 'wt-extra');
// worktree add 는 post-checkout 을 branch=wtf 로 발동시킨다(recursion-check 에서 fire 실증). 게이트가 skip 해야.
git(work, ['worktree', 'add', '-q', '-b', 'wtf', wtPath]);
ok('④ worktree add: 기존 main 브랜치 무영향', head(work) === mainBefore4);
ok('④ worktree add: 새 worktree 는 분기점 유지(pull 안 됨)', head(wtPath) === mainBefore4);
git(work, ['worktree', 'remove', '--force', wtPath]);
git(work, ['branch', '-q', '-D', 'wtf']);

// ---- ⑥ 재귀 non-loop: 단일 checkout 이 걸리지 않고 정확히 1회 ff(내부 pull 재발동 없음) ----
// (계측 fire-count 는 recursion-check.sh 로 실증; 여기선 hang 없이 정확 ff 로 간접 확인)
syncWork();
const at6 = advanceOrigin();
checkout(work, 'feature', {}, true);
checkout(work, 'main');
ok('⑥ 단일 ff(loop 없이 origin 도달)', head(work) === at6);

// hook 을 직접 호출해 게이트 검증 (실제 rebase/file-checkout 은 재현이 번거로워 args 로 모의).
function runHook(oldRef, newRef, flag) {
  return spawnSync('sh', [postCo, oldRef, newRef, flag], {
    cwd: work, env: { ...BASE_ENV, ...GENV }, encoding: 'utf8', timeout: 30000,
  });
}
// ---- ⑦ merge/rebase 진행 중(MERGE_HEAD 존재) → skip ----
syncWork();
const before7 = head(work);
advanceOrigin();
fs.writeFileSync(path.join(work, '.git', 'MERGE_HEAD'), before7 + '\n');
runHook(before7, before7, '1');
fs.rmSync(path.join(work, '.git', 'MERGE_HEAD'), { force: true });
ok('⑦ merge 진행 중(MERGE_HEAD) → pull skip', head(work) === before7);
// ---- ⑧ file checkout(flag=0) → skip ----
syncWork();
const before8 = head(work);
advanceOrigin();
runHook(before8, before8, '0');
ok('⑧ file checkout(flag=0) → pull skip', head(work) === before8);
// ---- ⑨ 정상 flag=1·main·clean·behind → ff (게이트 통과 positive control) ----
syncWork();
const at9 = advanceOrigin();
runHook(head(work), head(work), '1');
ok('⑨ 직접 호출 flag=1·main·clean → ff', head(work) === at9);

fs.rmSync(TMP, { recursive: true, force: true });
console.log(fail === 0 ? 'ALL PASS' : `${fail} FAIL`);
process.exit(fail === 0 ? 0 : 1);
