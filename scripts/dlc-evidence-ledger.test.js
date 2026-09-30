#!/usr/bin/env node
// dlc-evidence-ledger.js 회귀 테스트 — isIgnored(cross-worktree/repo·non-git 오탐)·
// VERIFY_SCRIPT(검증 스크립트 인식/오인식) 게이트. 실 git repo fixture 위에서 hook 을
// spawn 하고 ledger 상태를 관찰한다. 신호는 SIGNAL_OFF 로 자기격리, 세션은 케이스별 unique.
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync, spawnSync } = require('child_process');
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
function edit(fp, cwd, s, extraEnv) {
  const input = JSON.stringify({ session_id: s, cwd, tool_name: 'Edit', tool_input: { file_path: fp } });
  execFileSync('node', [HOOK], { input, env: { ...process.env, CLAUDE_DLC_SIGNAL_OFF: '1', ...extraEnv } });
  return ledger.read(s);
}
// doc-drift 판정은 root 가 `<home>/.claude` 일 때만 산다 → HOME 을 fixture 로 주입해 hook 을 돌린다.
function editInClaude(fp, cwd, s, home) {
  const input = JSON.stringify({ session_id: s, cwd, tool_name: 'Edit', tool_input: { file_path: fp } });
  const env = { ...process.env, HOME: home, USERPROFILE: home, CLAUDE_DLC_SIGNAL_OFF: '1' };
  execFileSync('node', [HOOK], { input, env });
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
ok('② 내용 없는 .git 디렉토리 아래 편집 → changed=false (git 도 repo 로 안 본다)', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-led-emptygit-'));
  fs.mkdirSync(path.join(root, '.git'));
  const f = W(root, 'sub/scratch.js');
  assert.strictEqual(edit(f, repoWt, sid()).changed, false);
});
ok('② 손상 repo(.git/HEAD 유실 → check-ignore 128)는 완화하지 않는다 → changed=true', () => {
  const broken = initRepo();
  const f = W(broken, 'src.js');
  fs.rmSync(path.join(broken, '.git', 'HEAD'));
  // 128(판정 불능) 로 fallback 분기를 타는 fixture 여야 회귀를 잡는다 — 0/1 이면 공허하게 통과한다.
  const probe = spawnSync('git', ['check-ignore', '-q', '--', f], { cwd: broken });
  assert.strictEqual(probe.status, 128);
  assert.strictEqual(edit(f, broken, sid()).changed, true);
});
ok('② 상대경로 fp 는 cwd 기준으로 절대화해 자기 repo 로 판정한다 → changed=true', () => {
  const rel = path.relative(nonGit, path.join(repoMain, 'src.js'));
  assert.ok(!path.isAbsolute(rel));
  assert.strictEqual(edit(rel, nonGit, sid()).changed, true);
});
ok('② GIT_DIR 이 걸린 채 git 이 실패하면 완화하지 않는다 → changed=true', () => {
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-led-gitdir-'));
  const f = W(scratch, 'src.js');
  const gitDir = path.join(scratch, 'no-such-git-dir');
  const probe = spawnSync('git', ['check-ignore', '-q', '--', f], { cwd: scratch, env: { ...process.env, GIT_DIR: gitDir } });
  assert.strictEqual(probe.status, 128);
  assert.strictEqual(edit(f, scratch, sid(), { GIT_DIR: gitDir }).changed, true);
});
ok('③ 같은 repo 비-ignored 실소스 편집 → changed=true (비회귀)', () => {
  assert.strictEqual(edit(path.join(repoMain, 'src.js'), repoMain, sid()).changed, true);
});
ok('③b 비-plan .md 문서 편집 → changed=false (verify 게이트 밖 — doc-only 오탐 방지)', () => {
  assert.strictEqual(edit(path.join(repoMain, 'doc.md'), repoMain, sid()).changed, false);
});
ok('③d .md 편집 → edited=true (결론 축은 문서 편집도 대상), changed 는 그대로 false', () => {
  const d = edit(path.join(repoMain, 'doc.md'), repoMain, sid());
  assert.strictEqual(d.edited, true);
  assert.strictEqual(d.conclusionBlocks, 0);
  assert.strictEqual(d.changed, false);
});
ok('③d plans/ 편집 → edited 불변 (plan 만 고친 턴은 결론 불요)', () => {
  assert.strictEqual(edit(path.join(repoTracked, 'plans/z-plan.md'), repoTracked, sid()).edited, false);
});
ok('③d gitignored(*.log) 편집 → edited 불변 (changed 와 같은 게이트)', () => {
  assert.strictEqual(edit(path.join(repoMain, 'a.log'), repoMain, sid()).edited, false);
});
ok('③c changed 파일은 changedTrigger 에 basename 기록 (신호 detail 용)', () => {
  assert.strictEqual(edit(path.join(repoMain, 'src.js'), repoMain, sid()).changedTrigger, 'src.js');
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

// ---- ③ doc-drift: 테스트 파일은 신규 추가일 때만 README dirty (기존 편집 오탐 제거) ----
const fakeHome = fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-led-home-'));
const claudeRepo = path.join(fakeHome, '.claude');
fs.mkdirSync(claudeRepo);
execFileSync('git', ['init', '-b', 'main', claudeRepo], { stdio: 'ignore' });
git(claudeRepo, 'config', 'user.email', 't@t');
git(claudeRepo, 'config', 'user.name', 't');
git(claudeRepo, 'config', 'commit.gpgsign', 'false');
W(claudeRepo, 'README.md', '# r\n');
W(claudeRepo, 'scripts/tracked.test.js');
git(claudeRepo, 'add', '-A');
git(claudeRepo, 'commit', '-m', 'init');
W(claudeRepo, 'scripts/fresh.test.js'); // 미커밋 = 신규 추가
W(claudeRepo, 'scripts/tool.js'); // 비-test 표면(미커밋)

ok('⑫ 커밋된 .test.js 편집 → readmeDirty=false (오탐 제거)', () => {
  assert.strictEqual(
    editInClaude(path.join(claudeRepo, 'scripts/tracked.test.js'), claudeRepo, sid(), fakeHome).readmeDirty,
    false
  );
});
ok('⑫ 신규 .test.js 추가 → readmeDirty=true (파일 트리 갱신 필요)', () => {
  const d = editInClaude(path.join(claudeRepo, 'scripts/fresh.test.js'), claudeRepo, sid(), fakeHome);
  assert.strictEqual(d.readmeDirty, true);
  assert.strictEqual(d.readmeTrigger, 'scripts/fresh.test.js');
});
ok('⑫ HEAD 없는 repo 의 .test.js → readmeDirty=false (fail-quiet)', () => {
  const h = fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-led-home0-'));
  const r = path.join(h, '.claude');
  fs.mkdirSync(r);
  execFileSync('git', ['init', '-b', 'main', r], { stdio: 'ignore' }); // 커밋 없음 → HEAD 부재
  W(r, 'scripts/x.test.js');
  W(r, 'scripts/x.js');
  assert.strictEqual(editInClaude(path.join(r, 'scripts/x.test.js'), r, sid(), h).readmeDirty, false);
  // 대조군 — root 해석 자체는 살아 있어야 "fail-quiet 이 동작했다"고 말할 수 있다
  assert.strictEqual(editInClaude(path.join(r, 'scripts/x.js'), r, sid(), h).readmeDirty, true);
});
ok('⑫ 비-test 표면 편집 → readmeDirty=true (비회귀)', () => {
  assert.strictEqual(
    editInClaude(path.join(claudeRepo, 'scripts/tool.js'), claudeRepo, sid(), fakeHome).readmeDirty,
    true
  );
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

// ---- 검증 래퍼: `bash|sh [옵션] <file>.sh` 의 본문을 한 단계만 본다(이름 규칙 VERIFY_SCRIPT 는 넓히지 않는다) ----
// 실제 사례 형태: scratch 의 일반 이름 래퍼 안에서 `./gradlew build -q > log 2>&1`.
// 디렉토리 이름에 대문자를 둔다 — 소문자화한 명령에서 경로를 뽑으면 대소문자를 가리는 파일시스템(Linux CI)에서 못 찾는다.
const wrapHome = fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-led-wraphome-'));
const wrapDir = path.join(wrapHome, 'Scratch-Dir');
const wrap = (name, body) => W(wrapDir, name, body);
function wrapperVerified(command, cwd) {
  const s = sid();
  const input = JSON.stringify({ session_id: s, cwd: cwd || os.tmpdir(), tool_name: 'Bash', tool_input: { command } });
  const env = { ...process.env, HOME: wrapHome, USERPROFILE: wrapHome, CLAUDE_DLC_SIGNAL_OFF: '1' };
  execFileSync('node', [HOOK], { input, env, timeout: 10000 });
  return ledger.read(s).verified;
}
const gradleWrap = wrap('x_final.sh', '#!/usr/bin/env bash\nset -e\ncd "$1"\n./gradlew build -q > build.log 2>&1\necho done\n');

ok('래퍼 본문에 검증 명령 → verified (대소문자 섞인 경로·cwd 기준 상대경로·~/·옵션)', () => {
  assert.strictEqual(wrapperVerified(`bash ${gradleWrap}`), true);
  assert.strictEqual(wrapperVerified('bash x_final.sh', wrapDir), true);
  assert.strictEqual(wrapperVerified('sh -e ~/Scratch-Dir/x_final.sh'), true);
  assert.strictEqual(wrapperVerified(`cd /tmp && bash -x ${gradleWrap} 2>&1 | tail -n 30`), true);
  assert.strictEqual(wrapperVerified(`set -e\nbash ${gradleWrap}`), true);
  assert.strictEqual(wrapperVerified(`bash ${wrap('run_all.sh', 'bash scripts/verify.sh\n')}`), true, '본문 줄도 VERIFY_SCRIPT 이름 규칙');
});
ok('CRLF 본문 — heredoc(<<- 의 탭 들여쓴 끝 줄)을 알아보고 그 뒤 검증 줄을 인식', () => {
  const f = wrap('crlf_run.sh', 'cat > notes.txt <<-EOF\r\n\tsee below\r\n\tEOF\r\nnpm test\r\n');
  assert.strictEqual(wrapperVerified(`bash ${f}`), true);
});
ok('래퍼는 명령마다 3개까지 본다', () => {
  const prep = wrap('prep.sh', 'mkdir -p out\n');
  assert.strictEqual(wrapperVerified(`bash ${prep} && bash ${gradleWrap}`), true);
  assert.strictEqual(wrapperVerified(`bash ${prep}; bash ${prep}; bash ${prep}; bash ${gradleWrap}`), false);
});
ok('본문에 검증 실행이 없으면 불변 — 주석·echo·heredoc 도움말·실제 deploy.sh', () => {
  const quiet = wrap('notes.sh', '# npm test 는 CI 에서\necho "run pytest later"\nmake build  # pytest next\n');
  const help = wrap('usage.sh', "cat <<-'EOF'\n\tusage: npm test\n\tEOF\n");
  const helpBs = wrap('usage_bs.sh', 'cat <<\\EOF\nusage: npm test\nEOF\n');
  const helpDash = wrap('usage_dash.sh', "cat <<'END-HELP'\nusage: npm test\nEND-HELP\n");
  const deploy = wrap('deploy.sh', 'set -e\nrsync -a dist/ web:/srv/app\nsystemctl restart app\n');
  const bom = wrap('bom_notes.sh', '﻿# npm test 는 CI 에서\n'); // BOM 뒤 주석도 주석 — JS \s 가 U+FEFF 를 공백으로 읽는다
  for (const f of [quiet, help, helpBs, helpDash, deploy, bom]) assert.strictEqual(wrapperVerified(`bash ${f}`), false, path.basename(f));
});
ok('읽지 않는 래퍼 — 16KB 초과·없는 파일·변수 경로(풀지 않는다)·일반 파일 아님·읽기 오류', () => {
  const big = wrap('big_run.sh', 'npm test\n' + '# pad\n'.repeat(3000));
  assert.strictEqual(wrapperVerified(`bash ${big}`), false);
  assert.strictEqual(wrapperVerified(`bash ${path.join(wrapDir, 'missing.sh')}`), false);
  assert.strictEqual(wrapperVerified('bash $HOME/Scratch-Dir/x_final.sh'), false);
  if (process.platform !== 'win32') {
    const fifo = path.join(wrapDir, 'pipe.sh');
    execFileSync('mkfifo', [fifo]);
    assert.strictEqual(wrapperVerified(`bash ${fifo}`), false);
    const locked = wrap('locked_run.sh', 'mkdir -p out\n'); // root 면 읽혀도 검증 줄이 없어 결과가 같다
    fs.chmodSync(locked, 0);
    assert.strictEqual(wrapperVerified(`bash ${locked}`), false, '읽기 오류(EACCES)도 exit 0');
    assert.strictEqual(wrapperVerified(`bash ${locked}; bash ${gradleWrap}`), true, '앞 래퍼의 읽기 오류가 뒤 래퍼 판정을 끊지 않는다');
  }
});

// ---- 생태계 커버리지: node/python/JVM 밖 검증기 인식 (early-stop-verify 오탐 축소) ----
// 근거(2026-08-13 telemetry 조사): `.md` 제외 fix 이후 남은 발동이 compose.yaml·*.css·*.sh 에
// 몰렸는데, 그 파일들의 표준 검증 명령(docker compose config·stylelint·shellcheck)이 전부 미인식이었다.
ok('docker compose config → verified=true', () => assert.strictEqual(V('docker compose config'), true));
ok('docker compose -f compose.yaml config -q → verified=true', () =>
  assert.strictEqual(V('docker compose -f compose.yaml config -q'), true));
ok('docker-compose config → verified=true', () => assert.strictEqual(V('docker-compose config'), true));
ok('shellcheck → verified=true', () => assert.strictEqual(V('shellcheck scripts/x.sh'), true));
ok('stylelint → verified=true', () => assert.strictEqual(V('npx stylelint "**/*.css"'), true));
ok('yamllint → verified=true', () => assert.strictEqual(V('yamllint compose.yaml'), true));
ok('make test → verified=true', () => assert.strictEqual(V('make test'), true));
ok('make lint → verified=true', () => assert.strictEqual(V('make lint'), true));
ok('make check → verified=true', () => assert.strictEqual(V('make check'), true));
ok('dotnet test → verified=true', () => assert.strictEqual(V('dotnet test'), true));
ok('swift test → verified=true', () => assert.strictEqual(V('swift test'), true));
ok('bundle exec rspec → verified=true', () => assert.strictEqual(V('bundle exec rspec'), true));
ok('phpunit → verified=true', () => assert.strictEqual(V('phpunit --testdox'), true));
ok('terraform validate → verified=true', () => assert.strictEqual(V('terraform validate'), true));
ok('hadolint → verified=true', () => assert.strictEqual(V('hadolint Dockerfile'), true));
ok('prettier --check → verified=true', () => assert.strictEqual(V('npx prettier --check .'), true));
ok('black --check → verified=true', () => assert.strictEqual(V('black --check .'), true));

// 음성 락 — 확장이 게이트를 헐겁게 하지 않는지. "verified 오탐은 gate 를 헐겁게 한다"(모듈 주석).
ok('docker compose up → verified 불변 (실행이지 검증 아님)', () =>
  assert.strictEqual(V('docker compose up -d'), false));
ok('docker compose down → verified 불변', () => assert.strictEqual(V('docker compose down'), false));
ok('docker build → verified 불변', () => assert.strictEqual(V('docker build -t x .'), false));
ok('make → verified 불변 (타겟 없는 빌드)', () => assert.strictEqual(V('make'), false));
ok('make install → verified 불변', () => assert.strictEqual(V('make install'), false));
ok('terraform apply → verified 불변 (파괴적, 검증 아님)', () =>
  assert.strictEqual(V('terraform apply'), false));
ok('prettier --write → verified 불변 (포맷 적용이지 검증 아님)', () =>
  assert.strictEqual(V('npx prettier --write .'), false));
ok('black . → verified 불변 (--check 없으면 적용)', () => assert.strictEqual(V('black .'), false));
ok('dotnet build → verified 불변', () => assert.strictEqual(V('dotnet build'), false));
ok('cat Makefile → verified 불변 (NONVERIFY veto)', () => assert.strictEqual(V('cat Makefile'), false));
ok('echo make test → verified 불변 (NONVERIFY veto)', () => assert.strictEqual(V('echo make test'), false));

// ---- Bash 편집(tool_response.bashEditDiff): 이 브랜치의 plan·README·index 편집은 경고를 끄는 쪽으로만 반영 ----
// 형태는 transcript 실측(v2.1.272~): files[{filePath(절대),hunks,deleted}]·moreFiles·changedFiles(문자열)·unavailable.
// 브랜치 x → plans/…-x/x-plan.md 가 이 브랜치의 plan(plan-match), y-plan 은 다른 작업의 plan.
const bashHome = fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-led-bashhome-'));
const bashRepo = path.join(bashHome, '.claude');
fs.mkdirSync(bashRepo);
execFileSync('git', ['init', '-b', 'x', bashRepo], { stdio: 'ignore' });
git(bashRepo, 'config', 'user.email', 't@t');
git(bashRepo, 'config', 'user.name', 't');
git(bashRepo, 'config', 'commit.gpgsign', 'false');
const bPlan = W(bashRepo, 'plans/2026-01-01-x/x-plan.md', '# plan\n');
const bClean = W(bashRepo, 'plans/2026-01-01-y/y-plan.md', '# plan\n');
const bReadme = W(bashRepo, 'README.md', '# r\n');
const bIndex = W(bashRepo, 'wiki/index.md', '# i\n');
const bPage = W(bashRepo, 'wiki/pages/p.md', '# p\n');
const bTool = W(bashRepo, 'scripts/tool.js', 'x\n');
git(bashRepo, 'add', '-A');
git(bashRepo, 'commit', '-m', 'init');

function diffOf(paths, extra) {
  return { files: paths.map((p) => ({ filePath: p, hunks: [], deleted: false })), moreFiles: 0, changedFiles: paths, ...extra };
}
function bashEdit(command, bashEditDiff, s) {
  const input = JSON.stringify({
    session_id: s, cwd: bashRepo, tool_name: 'Bash', tool_input: { command },
    tool_response: { stdout: '', stderr: '', interrupted: false, isImage: false, bashEditDiff },
  });
  execFileSync('node', [HOOK], { input, env: { ...process.env, HOME: bashHome, USERPROFILE: bashHome, CLAUDE_DLC_SIGNAL_OFF: '1' } });
  return ledger.read(s);
}
const editB = (fp, s) => editInClaude(fp, bashRepo, s, bashHome);

ok('HEAD 와 같은 plan(끝까지 간 git pull·merge 결과) → planTouched 불변', () => {
  assert.strictEqual(bashEdit('git fetch origin && git merge origin/main', diffOf([bPlan]), sid()).planTouched, false);
});
ok('Bash 로 고친 이 브랜치 plan(HEAD 와 다름) → planTouched=true, changed·edited 는 안 켜짐', () => {
  fs.appendFileSync(bPlan, 'progress\n');
  const d = bashEdit('python3 /tmp/edit_plan.py', diffOf([bPlan]), sid());
  assert.strictEqual(d.planTouched, true);
  assert.strictEqual(d.changed, false);
  assert.strictEqual(d.edited, false);
});
ok('다른 작업의 plan 이 HEAD 와 달라도(충돌로 멈춘 merge) planTouched 불변', () => {
  fs.appendFileSync(bClean, 'from main\n');
  assert.strictEqual(bashEdit('git fetch origin && git merge origin/main', diffOf([bClean]), sid()).planTouched, false);
  git(bashRepo, 'checkout', '--', 'plans/2026-01-01-y/y-plan.md');
});
ok('changedFiles 없이 files 만 있어도 반영', () => {
  const d = bashEdit('python3 /tmp/p.py', { files: [{ filePath: bPlan, hunks: [], deleted: false }], moreFiles: 0 }, sid());
  assert.strictEqual(d.planTouched, true);
});
ok('세션 root 밖 repo 의 plan·README 는 무변경', () => {
  const other = initRepo('x');
  const oPlan = W(other, 'plans/2026-01-01-x/x-plan.md', '# p\n');
  const oReadme = W(other, 'README.md', '# r\n');
  git(other, 'add', '-A');
  git(other, 'commit', '-m', 'init');
  fs.appendFileSync(oPlan, 'x\n');
  fs.appendFileSync(oReadme, 'x\n');
  const s = sid();
  editB(bTool, s); // 세션 root 의 readmeDirty=true
  const d = bashEdit('python3 /tmp/o.py', diffOf([oPlan, oReadme]), s);
  assert.strictEqual(d.planTouched, false);
  assert.strictEqual(d.readmeDirty, true);
});
ok('changedFiles 만 있고 files 가 잘림(moreFiles>0) → 나열된 plan 반영', () => {
  const d = bashEdit('python3 /tmp/many.py', { files: [], moreFiles: 3, changedFiles: [bPlan] }, sid());
  assert.strictEqual(d.planTouched, true);
});
ok('unavailable 이어도 나열된 경로는 반영, 경로 없으면 무변경', () => {
  assert.strictEqual(bashEdit('x', diffOf([bPlan], { unavailable: true }), sid()).planTouched, true);
  assert.strictEqual(bashEdit('x', { files: [], moreFiles: 0, unavailable: true }, sid()).planTouched, false);
});
ok('Edit 로 스크립트 → readmeDirty, 이어 Bash 로 README 수정 → readmeDirty 해소', () => {
  const s = sid();
  assert.strictEqual(editB(bTool, s).readmeDirty, true);
  fs.appendFileSync(bReadme, 'doc\n');
  assert.strictEqual(bashEdit("sed -i '' 's/a/b/' README.md", diffOf([bReadme]), s).readmeDirty, false);
});
ok('HEAD 와 같은 README 가 나열돼도 readmeDirty 유지', () => {
  const s = sid();
  git(bashRepo, 'checkout', '--', 'README.md');
  editB(bTool, s);
  assert.strictEqual(bashEdit('git fetch origin && git pull --ff-only origin main', diffOf([bReadme]), s).readmeDirty, true);
});
ok('Edit 로 wiki 페이지 → indexDirty, 이어 Bash 로 index 수정 → indexDirty 해소', () => {
  const s = sid();
  assert.strictEqual(editB(bPage, s).indexDirty, true);
  fs.appendFileSync(bIndex, 'line\n');
  assert.strictEqual(bashEdit('python3 /tmp/idx.py', diffOf([bIndex]), s).indexDirty, false);
});
ok('Bash 로 고친 스크립트는 경고를 켜지 않는다(changed·readmeDirty 불변)', () => {
  const d = bashEdit("sed -i '' 's/x/y/' scripts/tool.js", diffOf([bTool]), sid());
  assert.strictEqual(d.changed, false);
  assert.strictEqual(d.readmeDirty, false);
});
ok('bashEditDiff 형태 불량이어도 같은 명령의 검증 인식은 산다', () => {
  assert.strictEqual(bashEdit('bash scripts/verify.sh', 'not-an-object', sid()).verified, true);
  assert.strictEqual(bashEdit('bash scripts/verify.sh', { files: 'x', changedFiles: 7 }, sid()).verified, true);
});

// ---- 대기 턴: run_in_background Bash 의 backgroundTaskId → bgTaskIds (early-stop 이 Stop 의 background_tasks[].id 와 대조) ----
// 형태는 transcript 실측(2.1.285): 결과 stdout·stderr·interrupted·isImage·noOutputExpected·backgroundTaskId.
// timeout 으로 자동 background 되면 결과에 timedOutAfterMs 가 더해지고 입력에 run_in_background 가 없다.
function bashTool(s, toolInput, toolResponse) {
  const input = JSON.stringify({ session_id: s, cwd: os.tmpdir(), tool_name: 'Bash', tool_input: toolInput, tool_response: toolResponse });
  execFileSync('node', [HOOK], { input, env: { ...process.env, CLAUDE_DLC_SIGNAL_OFF: '1' } });
  return ledger.read(s);
}
const bgResult = (id, extra) => ({ stdout: '', stderr: '', interrupted: false, isImage: false, noOutputExpected: false, backgroundTaskId: id, ...extra });
const bgInput = (command) => ({ command, description: 'x', run_in_background: true });

ok('run_in_background Bash → bgTaskIds 에 backgroundTaskId 를 순서대로, 중복 없이', () => {
  const s = sid();
  bashTool(s, bgInput('gh run watch 1'), bgResult('b1'));
  bashTool(s, bgInput('sleep 30'), bgResult('b2'));
  assert.deepStrictEqual(bashTool(s, bgInput('sleep 30'), bgResult('b1')).bgTaskIds, ['b1', 'b2']);
});
ok('run_in_background 가 없으면 기록하지 않는다 — timeout 자동 background 도(경고 유지 쪽)', () => {
  const d = bashTool(sid(), { command: 'npm run e2e', description: 'x' }, bgResult('b3', { timedOutAfterMs: 120000 }));
  assert.deepStrictEqual(d.bgTaskIds, []);
});
ok('backgroundTaskId 가 없거나 빈 문자열·비문자열이면 기록하지 않는다', () => {
  const s = sid();
  for (const r of [{ stdout: '' }, bgResult(''), bgResult(7), null]) bashTool(s, bgInput('sleep 1'), r);
  assert.deepStrictEqual(ledger.read(s).bgTaskIds, []);
});
ok('bgTaskIds 는 최근 50개만 남긴다', () => {
  const s = sid();
  ledger.write(s, { ...ledger.DEFAULT, bgTaskIds: Array.from({ length: 50 }, (_, i) => `o${i}`) });
  const d = bashTool(s, bgInput('sleep 1'), bgResult('new'));
  assert.strictEqual(d.bgTaskIds.length, 50);
  assert.deepStrictEqual([d.bgTaskIds[0], d.bgTaskIds[49]], ['o1', 'new']);
});
ok('손상 장부(bgTaskIds 가 배열 아님)에서도 exit 0 · 같은 Bash 의 검증 기록 유지', () => {
  for (const bad of [null, 'b1', { b1: true }]) {
    const s = sid();
    ledger.write(s, { ...ledger.DEFAULT, bgTaskIds: bad });
    const d = bashTool(s, bgInput('npm test'), bgResult('b1'));
    assert.strictEqual(d.verified, true, JSON.stringify(bad));
    assert.deepStrictEqual(d.bgTaskIds, ['b1'], JSON.stringify(bad));
  }
});
ok('사용자 턴 리셋(ledger.reset)은 bgTaskIds 를 비운다', () => {
  const s = sid();
  bashTool(s, bgInput('sleep 1'), bgResult('b1'));
  ledger.reset(s);
  assert.deepStrictEqual(ledger.read(s).bgTaskIds, []);
});

console.log(`dlc-evidence-ledger.test.js: ${n} tests passed`);
