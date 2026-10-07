#!/usr/bin/env node
// settings.json 의 SessionStart 자동 pull 훅 회귀 테스트.
//
// 왜 필요한가: 이 훅은 **자기 자신의 업데이트 배포 경로**다. 경로 오타 하나로도 전 머신이
// 조용히 업데이트를 멈춘다 — 이 훅이 애초에 고치려던 "132커밋 밀렸는데 아무도 몰랐다" 사고의
// 상위 재현이다. 그래서 문자열을 눈으로 읽는 대신 fixture HOME 에 실제로 spawn 해 동작을
// 고정한다. (셸 훅을 fixture repo 로 spawn 하는 방식은 install-hooks.test.js 선례.)
//
// command 를 **그대로** 돌린다. 스크립트를 직접 실행하면 "설정이 엉뚱한 경로를 가리킨다"는
// 이 테스트의 존재 이유가 검증에서 빠지므로, fixture HOME 안에 스크립트를 복사해 두고
// command 가 스스로 그것을 찾아가게 한다.
//
// settings.json 은 untracked 라(머신별 값 자동 주입 — .gitignore 참조) CI checkout·새 worktree
// 에는 없다. 있으면 실제 배선까지 검증하고, 없으면 CANONICAL 로 스크립트 동작만 고정한다.
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync, spawnSync } = require('child_process');

for (const k of ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE']) delete process.env[k];
// 실행하는 셸의 자동 pull 스위치(CLAUDE_AUTOPULL_OFF·_VERIFY·_TIMEOUT)가 결과를 뒤집지 않게.
for (const k of Object.keys(process.env)) if (k.startsWith('CLAUDE_AUTOPULL_')) delete process.env[k];

let n = 0;
const ok = (name, fn) => { fn(); n++; };

const REPO = path.join(__dirname, '..');
const SCRIPT_REL = 'scripts/session-start-pull.sh';
const SCRIPT_ABS = path.join(REPO, SCRIPT_REL);

// settings.json 이 바뀌면 이 상수도 같이 고쳐야 한다 — 아래 첫 테스트가 둘의 일치를 잠근다.
const CANONICAL = {
  command: '[ -r ~/.claude/scripts/session-start-pull.sh ] && sh ~/.claude/scripts/session-start-pull.sh; true',
  timeout: 15,
  async: true,
};
const SETTINGS_PATH = path.join(REPO, 'settings.json');
const WIRED = fs.existsSync(SETTINGS_PATH);
const ENTRY = WIRED
  ? JSON.parse(fs.readFileSync(SETTINGS_PATH, 'utf8')).hooks.SessionStart[0].hooks[0]
  : CANONICAL;
const COMMAND = ENTRY.command;

function git(dir, args) {
  execFileSync('git', ['-C', dir, ...args], { stdio: 'ignore' });
}
function gitOut(dir, args, input) {
  return execFileSync('git', ['-C', dir, ...args], { input, stdio: ['pipe', 'pipe', 'ignore'] }).toString().trim();
}

// CI(record-verified job)가 만드는 모양의 기록을 origin 의 ci/verified 에 올린다: 파일 main-sha 하나,
// 부모 = 직전 기록(root 면 없음). 올리는 쪽은 other — client 의 추적 ref 를 건드리지 않아야 한다.
function pushRecord(other, content, { root = false } = {}) {
  const blob = gitOut(other, ['hash-object', '-w', '--stdin'], content);
  const tree = gitOut(other, ['mktree'], `100644 blob ${blob}\tmain-sha\n`);
  const parent = root ? '' : gitOut(other, ['ls-remote', 'origin', 'refs/heads/ci/verified']).split(/\s/)[0];
  const rec = gitOut(other, ['commit-tree', tree, '-m', 'record', ...(parent ? ['-p', parent] : [])]);
  git(other, ['push', '-q', '-f', 'origin', `${rec}:refs/heads/ci/verified`]);
  return rec;
}

// fixture HOME 에 <home>/.claude 를 만들고, origin 이 remoteCommits 만큼 앞선 상태로 둔다.
// record: 'tip'(기본 — CI 가 origin/main tip 을 통과시킨 상태) · 'none' · 원격 커밋 번호(0부터).
// command 가 `~/.claude` 를 쓰므로 HOME 만 갈아끼우면 실 repo 를 건드리지 않고 검증된다.
// 스크립트도 같은 상대경로에 복사해 둬야 command 가 실제로 찾아간다.
// 케이스마다 home 을 고치므로(dirty 파일·push·url 변경) 옵션 조합별 템플릿을 한 번 만들고 복사해 준다.
// 템플릿 자체는 넘기지 않는다. 복사는 상대 링크를 템플릿 안을 가리키는 절대 링크로 바꾸지 않고, 전역
// core.fsmonitor 가 띄운 데몬의 소켓·쿠키(cpSync 가 소켓에서 실패한다)는 옮기지 않는다.
const COPY = { recursive: true, verbatimSymlinks: true, filter: (src) => !path.basename(src).startsWith('fsmonitor--daemon') };
const homeTemplates = new Map();
function makeHome({ withScript = true, remoteCommits = 1, record = 'tip' } = {}) {
  const key = JSON.stringify({ withScript, remoteCommits, record });
  if (!homeTemplates.has(key)) homeTemplates.set(key, buildHome({ withScript, remoteCommits, record }));
  const t = homeTemplates.get(key);
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'ssp-home-'));
  fs.cpSync(t.home, home, COPY);
  const bare = path.join(home, 'origin.git');
  const repo = path.join(home, '.claude');
  const other = path.join(home, 'other');
  // 템플릿 origin 을 가리킨 채 남으면 케이스가 템플릿 bare 에 push 해 뒤 케이스가 오염된다.
  for (const dir of [repo, other]) {
    git(dir, ['config', 'remote.origin.url', bare]);
    const text = fs.readFileSync(path.join(dir, '.git', 'config'), 'utf8');
    assert.ok(!text.includes(path.basename(t.home)), `${dir} 의 설정이 아직 템플릿 ${t.home} 를 가리킨다`);
  }
  return { home, repo, other, commits: [...t.commits] };
}
// git config 가 쓰는 것과 같은 바이트를 직접 덧붙인다(프로세스 절약).
function setIdentity(dir) {
  fs.appendFileSync(path.join(dir, '.git', 'config'), '[user]\n\temail = t@t\n\tname = t\n[commit]\n\tgpgsign = false\n');
}
function buildHome({ withScript, remoteCommits, record }) {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'ssp-thome-'));
  const bare = path.join(home, 'origin.git');
  const repo = path.join(home, '.claude');
  execFileSync('git', ['init', '-q', '--bare', '-b', 'main', bare], { stdio: 'ignore' });
  execFileSync('git', ['clone', '-q', bare, repo], { stdio: 'ignore' });
  setIdentity(repo);
  fs.writeFileSync(path.join(repo, 'shared.txt'), 'a');
  fs.writeFileSync(path.join(repo, 'other.txt'), 'b');
  git(repo, ['add', '-A']);
  git(repo, ['commit', '-m', 'init']);
  git(repo, ['push', '-q', 'origin', 'HEAD:main']);
  git(repo, ['branch', '-M', 'main']);
  if (withScript) {
    fs.mkdirSync(path.join(repo, 'scripts'), { recursive: true });
    fs.copyFileSync(SCRIPT_ABS, path.join(repo, SCRIPT_REL));
  }
  // 원격을 remoteCommits 만큼 앞세운다(매번 shared.txt 변경).
  const other = path.join(home, 'other');
  execFileSync('git', ['clone', '-q', bare, other], { stdio: 'ignore' });
  setIdentity(other);
  const commits = [];
  for (let i = 0; i < remoteCommits; i++) {
    fs.writeFileSync(path.join(other, 'shared.txt'), `remote${i}`);
    git(other, ['add', '-A']);
    git(other, ['commit', '-m', `remote${i}`]);
    commits.push(gitOut(other, ['rev-parse', 'HEAD']));
  }
  git(other, ['push', '-q', 'origin', 'HEAD:main']);
  if (record === 'tip') pushRecord(other, commits[commits.length - 1]);
  else if (typeof record === 'number') pushRecord(other, commits[record]);
  return { home, repo, other, commits };
}

// timeout 은 필수다. 스크립트가 fetch 를 백그라운드로 돌리므로, stdio 를 제대로 끊지 못한 회귀가
// 들어오면 spawnSync 가 영원히 반환하지 않고 CI 가 통째로 멈춘다.
function runChain(home, extraEnv, opts = {}) {
  // 사용자 git 설정(이 Mac 의 전역 fetch.prune=true 등)이 새면 --prune 을 빼는 회귀가 초록이 된다.
  // HOME 을 바꿔 ~/.gitconfig 는 막히고, system·XDG 설정은 여기서 막는다.
  const env = { ...process.env, HOME: home, GIT_CONFIG_NOSYSTEM: '1', XDG_CONFIG_HOME: path.join(home, '.xdg'),
    GIT_CONFIG_GLOBAL: path.join(home, '.gitconfig'), ...extraEnv };
  for (const k of ['GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT']) delete env[k];
  const r = spawnSync('sh', ['-c', COMMAND], {
    env,
    encoding: 'utf8',
    timeout: opts.timeout || 30000,
  });
  assert.ok(!r.error, `spawn 실패: ${r.error && r.error.message}`);
  return { out: (r.stdout || '').trim(), code: r.status };
}
const head = (repo) => execFileSync('git', ['-C', repo, 'rev-parse', 'HEAD']).toString().trim();

// PATH 앞에 두는 `git` stub. fetch 만 매달리게 해 워치독을 결정적으로 검증한다
// (blackhole IP 는 환경 의존이고 10초를 잡아먹는다).
function makeGitStub({ grandchildMarker } = {}) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ssp-stub-'));
  const real = execFileSync('sh', ['-c', 'command -v git']).toString().trim();
  // 실제 git 은 fetch 중 ssh·git-remote-https 를 손자로 띄운다. 그 손자가 워치독 kill 뒤에도
  // 살아남는지 보려면 stub 도 손자를 띄워야 한다(마커를 계속 갱신해 생존을 드러낸다).
  // 손자 루프는 **유한**해야 한다. 무한이면 이 케이스가 실패할 때마다(= 회귀를 고치는 동안
  // 반복 실행할 때마다) 개발 머신에 루프가 하나씩 영구히 쌓인다.
  const spawnGrandchild = grandchildMarker
    ? `( _i=0; while [ $_i -lt 60 ]; do date +%s > "${grandchildMarker}"; sleep 0.3; _i=$((_i+1)); done ) &\n  `
    : '';
  fs.writeFileSync(
    path.join(dir, 'git'),
    `#!/bin/sh\nfor a in "$@"; do\n  if [ "$a" = fetch ]; then\n  ${spawnGrandchild}sleep 60\n  exit 0\n  fi\ndone\nexec "${real}" "$@"\n`,
    { mode: 0o755 },
  );
  return dir;
}
const sleepSync = (sec) => execFileSync('sh', ['-c', `sleep ${sec}`]);

// fetch 시도·성공 스탬프. 파일명은 브리프에서 가져온다 — 두 쪽 키가 갈라지면 한쪽이 조용히 굶는다.
const { AUTOPULL_STAMPS } = require('./session-brief.js');
const stamps = (repo) => ({
  attempt: path.join(repo, '.git', AUTOPULL_STAMPS.attempt),
  ok: path.join(repo, '.git', AUTOPULL_STAMPS.ok),
});
const mtimeSec = (file) => Math.round(fs.statSync(file).mtimeMs / 1000);
const setMtimeDaysAgo = (file, days) => {
  const t = Math.floor(Date.now() / 1000) - days * 86400;
  fs.utimesSync(file, t, t);
  return t;
};
// fetch 를 네트워크 없이 즉시 실패시킨다 — 없는 로컬 경로를 origin 으로.
const breakOrigin = (home, repo) => git(repo, ['remote', 'set-url', 'origin', path.join(home, 'missing.git')]);

ok('command 가 스크립트를 가리키고 그 파일이 repo 에 실존한다', () => {
  assert.ok(COMMAND.includes(SCRIPT_REL), `command 가 ${SCRIPT_REL} 를 참조하지 않는다: ${COMMAND}`);
  assert.ok(fs.existsSync(SCRIPT_ABS), `${SCRIPT_REL} 가 없다`);
  // settings.json 이 있는 머신에서는 실제 배선이 CANONICAL 과 갈라지지 않았는지까지 잠근다.
  // 갈라지면 CI(= CANONICAL 로만 도는 쪽)가 실물과 다른 것을 검증하게 된다.
  if (WIRED) {
    assert.strictEqual(ENTRY.command, CANONICAL.command,
      'settings.json 의 SessionStart command 가 바뀌었다 — CANONICAL 도 같이 갱신할 것');
  }
});

ok('훅은 async 로 남는다 — 동기로 바꿔도 CLAUDE.md 최신화는 못 얻고 세션 시작만 늦어진다', () => {
  // CLAUDE.md 로드는 SessionStart 훅과 **경합**한다(순서 보장 아님, 실측). 즉시 쓰는 훅은 이기고
  // 0.5초짜리 pull 은 진다 — 동기 전환은 비용만 남기므로 채택하지 않았다.
  assert.strictEqual(ENTRY.async, true);
  // 워치독(기본 8s)보다 하니스 timeout 이 커야 워치독이 먼저 작동해 고아가 안 남는다.
  assert.ok(ENTRY.timeout >= 15, `timeout 이 워치독 상한보다 작다: ${ENTRY.timeout}`);
});

ok('hang 방어(프롬프트·SSH·HTTP)가 스크립트에 있다', () => {
  const s = fs.readFileSync(SCRIPT_ABS, 'utf8');
  assert.match(s, /GIT_TERMINAL_PROMPT=0/);
  assert.match(s, /BatchMode=yes/);
  assert.match(s, /ConnectTimeout=10/);
  assert.match(s, /credential\.helper=/);
  assert.match(s, /core\.askpass=/i);
  assert.match(s, /http\.lowSpeedLimit=1000/);
  assert.match(s, /http\.lowSpeedTime=10/);
});

ok('워치독 상한이 wall-clock 이고 하니스 예산 안으로 clamp 된다', () => {
  // 이 둘은 동작만으로는 잠기지 않는다: iteration 카운트로 되돌려도 타이밍 단언 범위 안에
  // 들어와 초록이 된다(mutation 으로 확인). 그래서 설계 형태를 직접 고정한다.
  const s = fs.readFileSync(SCRIPT_ABS, 'utf8');
  assert.match(s, /_deadline=\$\(\(\s*\$\(date \+%s\)/, '상한을 wall-clock 으로 잡아야 한다');
  assert.doesNotMatch(s, /_n\s*\+\s*1|_n=\$\(\(/, 'iteration 카운터로 상한을 재면 안 된다');
  // 비숫자·과대값이 그대로 쓰이면 각각 "매번 즉시 kill"과 "하니스가 먼저 죽여 고아 잔존"이 된다.
  assert.match(s, /\*\[!0-9\]\*\)/, '비숫자 timeout 을 걸러야 한다');
  assert.match(s, /-gt 12/, '하니스 timeout(15) 안으로 clamp 해야 한다');
});

ok('① clean + behind → pull 하고 한 줄 알린다', () => {
  const { home, repo } = makeHome();
  const before = head(repo);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.match(out, /updated from origin\/main/);
  assert.notStrictEqual(head(repo), before);
});

ok('①-b 원격 추적 ref 도 갱신된다 (신호 N 이 이 ref 로 밀림을 잰다)', () => {
  const { home, repo } = makeHome();
  runChain(home);
  const tracking = execFileSync('git', ['-C', repo, 'rev-parse', 'refs/remotes/origin/main'])
    .toString().trim();
  assert.strictEqual(tracking, head(repo));
});

ok('② 무관 파일이 더러워도 pull 한다 (dirty 게이트 제거의 핵심)', () => {
  const { home, repo } = makeHome();
  const before = head(repo);
  fs.writeFileSync(path.join(repo, 'other.txt'), 'local-dirty');
  const { code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.notStrictEqual(head(repo), before);
  assert.strictEqual(fs.readFileSync(path.join(repo, 'other.txt'), 'utf8'), 'local-dirty');
});

ok('③ 충돌 파일이 더러우면 git 이 거부 — 무음·변경 보존', () => {
  const { home, repo } = makeHome();
  const before = head(repo);
  fs.writeFileSync(path.join(repo, 'shared.txt'), 'local-dirty');
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
  assert.strictEqual(fs.readFileSync(path.join(repo, 'shared.txt'), 'utf8'), 'local-dirty');
});

ok('④ 이미 최신이면 무음', () => {
  const { home } = makeHome();
  runChain(home);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
});

ok('⑤ main 이 아니면 skip', () => {
  const { home, repo } = makeHome();
  git(repo, ['checkout', '-q', '-b', 'feature']);
  const before = head(repo);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
});

ok('⑥ CLAUDE_AUTOPULL_OFF=1 이면 아무것도 안 한다', () => {
  const { home, repo } = makeHome();
  const before = head(repo);
  const { out, code } = runChain(home, { CLAUDE_AUTOPULL_OFF: '1' });
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
});

ok('⑥-b .autopull-off 파일이 있으면 아무것도 안 한다 (GUI 실행용 즉시 레버)', () => {
  const { home, repo } = makeHome();
  const before = head(repo);
  fs.writeFileSync(path.join(repo, '.autopull-off'), '');
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
});

ok('⑦ rebase/merge 진행 중이면 skip', () => {
  const { home, repo } = makeHome();
  fs.mkdirSync(path.join(repo, '.git', 'rebase-merge'), { recursive: true });
  const before = head(repo);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
});

ok('⑧ ~/.claude 가 git repo 가 아니어도 exit 0 (fail-open)', () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'ssp-nongit-'));
  fs.mkdirSync(path.join(home, '.claude', 'scripts'), { recursive: true });
  fs.copyFileSync(SCRIPT_ABS, path.join(home, '.claude', SCRIPT_REL));
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
});

ok('⑨ ~/.claude 가 아예 없어도 exit 0 (fail-open)', () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'ssp-nohome-'));
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
});

ok('⑩ 스크립트 파일이 없어도 세션을 막지 않는다 (배포 순환 fail-open)', () => {
  const { home } = makeHome({ withScript: false });
  const { code } = runChain(home);
  assert.strictEqual(code, 0);
});

// ---------- CI 검증 기록(origin/ci/verified)까지만 ff ----------
ok('(b) 검증 기록이 없으면 ff 하지 않는다 — origin/main 추적 ref 는 갱신(브리프가 밀림을 잰다)', () => {
  const { home, repo, commits } = makeHome({ record: 'none' });
  const before = head(repo);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
  assert.strictEqual(gitOut(repo, ['rev-parse', 'refs/remotes/origin/main']), commits[0]);
});

ok('(c) 기록이 tip 보다 뒤면(CI 진행 중) 기록까지만 ff 한다', () => {
  const { home, repo, commits } = makeHome({ remoteCommits: 2, record: 0 });
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.match(out, /updated from origin\/main/);
  assert.strictEqual(head(repo), commits[0]);
});

ok('(d) 원격이 지운 기록의 옛 추적 ref 로 ff 하지 않는다(--prune)', () => {
  const { home, repo, other } = makeHome();
  git(repo, ['fetch', '-q', 'origin', '+refs/heads/ci/*:refs/remotes/origin/ci/*']); // 옛 기록을 받아 둔다
  const before = head(repo);
  // 다른 clone 에서 지운다 — 같은 clone 에서 지우면 push 가 추적 ref 를 직접 지워 prune 없이도 통과한다.
  git(other, ['push', '-q', 'origin', '--delete', 'ci/verified']);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
});

ok('(e) 기록이 origin/main 밖을 가리키면(재작성 직후) ff 하지 않는다', () => {
  const { home, repo, other } = makeHome();
  // 기록된 커밋을 client 가 이미 받아 둔 상태 — 그래야 조상 확인이 없을 때 merge 가 실제로 된다.
  git(repo, ['fetch', '-q', 'origin', '+refs/heads/main:refs/remotes/origin/main', '+refs/heads/ci/*:refs/remotes/origin/ci/*']);
  const before = head(repo);
  // other 가 main 을 기록된 커밋의 형제로 재작성한다(기록 job 은 아직 돌지 않아 기록은 그대로).
  git(other, ['reset', '-q', '--hard', 'HEAD~1']);
  fs.writeFileSync(path.join(other, 'shared.txt'), 'rewritten');
  git(other, ['commit', '-qam', 'rewritten']);
  git(other, ['push', '-q', '-f', 'origin', 'HEAD:main']);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
});

ok('(f) 기록 내용이 sha 가 아니면(git 이 푸는 이름이라도) ff 하지 않는다', () => {
  const { home, repo, other } = makeHome({ record: 'none' });
  // sha 와 같은 40자이면서 git 이 origin/main tip 으로 푸는 이름 — 길이 확인만으로는 막히지 않는다.
  pushRecord(other, 'refs/remotes/origin/main~0~0~0~0~0~0~0~0');
  const before = head(repo);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), before);
});

ok('(f2) 기록이 짧은 16진수(축약 sha)면 ff 하지 않는다 — 길이도 HEAD 와 같아야 한다', () => {
  const { home, repo, other, commits } = makeHome({ record: 'none' });
  pushRecord(other, commits[0].slice(0, 12)); // git 은 이 축약을 그 커밋으로 풀어 버린다
  const before = head(repo);
  runChain(home);
  assert.strictEqual(head(repo), before);
});

ok('(g) 기록이 새 root 로 다시 만들어져도(정지 뒤 재기록) 받아서 따라간다', () => {
  const { home, repo, other, commits } = makeHome({ remoteCommits: 2, record: 0 });
  runChain(home);
  assert.strictEqual(head(repo), commits[0]);
  pushRecord(other, commits[1], { root: true });
  runChain(home);
  assert.strictEqual(head(repo), commits[1]);
});

ok('(h) HEAD 가 이미 기록보다 앞서면 되감지 않고 무음', () => {
  const { home, repo, commits } = makeHome({ remoteCommits: 2, record: 0 });
  git(repo, ['fetch', '-q', 'origin', 'main']);
  git(repo, ['merge', '-q', '--ff-only', 'FETCH_HEAD']); // /e·post-checkout 이 검증 없이 당겨 온 상태
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  assert.strictEqual(head(repo), commits[1]);
});

ok('(i) CLAUDE_AUTOPULL_VERIFY=0 이면 기록 없이 origin/main 으로 ff — 0 이 아닌 값은 검증 켜짐', () => {
  const off = makeHome({ record: 'none' });
  runChain(off.home, { CLAUDE_AUTOPULL_VERIFY: '0' });
  assert.strictEqual(head(off.repo), off.commits[0]);
  for (const value of ['off', 'false']) {
    const on = makeHome({ record: 'none' });
    const before = head(on.repo);
    runChain(on.home, { CLAUDE_AUTOPULL_VERIFY: value });
    assert.strictEqual(head(on.repo), before, `CLAUDE_AUTOPULL_VERIFY=${value}`);
  }
});

ok('(i2) 새 fetch 가 깨진 머신에서도 CLAUDE_AUTOPULL_VERIFY=0 은 예전 fetch 로 따라간다', () => {
  // 로컬 refs/remotes/origin/ci 가 기록 refspec 과 D/F 충돌 → 새 fetch 는 rc 1 로 매번 실패한다.
  const { home, repo, commits } = makeHome();
  git(repo, ['update-ref', 'refs/remotes/origin/ci', 'HEAD']);
  const before = head(repo);
  runChain(home);
  assert.strictEqual(head(repo), before, '검증 켜짐이면 fetch 실패로 보류');
  runChain(home, { CLAUDE_AUTOPULL_VERIFY: '0' });
  assert.strictEqual(head(repo), commits[0], 'VERIFY=0 은 기록 refspec 없이 main 만 받는다');
});

ok('Git Bash 의 경로 변환을 끄지 않는다 — 끄면 -C /c/Users/... 가 native git 에 그대로 가 fetch 가 매번 실패한다', () => {
  const code = fs.readFileSync(SCRIPT_ABS, 'utf8').split('\n').filter((l) => !l.trim().startsWith('#')).join('\n');
  assert.doesNotMatch(code, /MSYS_NO_PATHCONV|MSYS2_ARG_CONV_EXCL/);
});

ok('사용자 FETCH_HEAD 를 덮지 않는다', () => {
  const { home, repo, commits } = makeHome();
  const fetchHead = path.join(repo, '.git', 'FETCH_HEAD');
  fs.writeFileSync(fetchHead, 'user-owned\n');
  runChain(home);
  assert.strictEqual(head(repo), commits[0]);
  assert.strictEqual(fs.readFileSync(fetchHead, 'utf8'), 'user-owned\n');
});

ok('⑪ 워치독이 매달린 fetch 를 상한 안에 죽인다', () => {
  const { home, repo } = makeHome();
  const before = head(repo);
  const stub = makeGitStub();
  const t0 = Date.now();
  const { code } = runChain(
    home,
    { PATH: `${stub}${path.delimiter}${process.env.PATH}`, CLAUDE_AUTOPULL_TIMEOUT: '3' },
    { timeout: 30000 },
  );
  const elapsed = Date.now() - t0;
  assert.strictEqual(code, 0, '워치독 발동 후에도 fail-open 이어야 한다');
  // 하한은 "너무 일찍 죽지 않음"을 건다 — timeout 파싱이 깨져 deadline=now 가 되면 무음으로
  // 매번 즉시 kill 된다(그 경우 0.3s 안에 끝난다).
  // **N-1 초까지 내려갈 수 있다**: 마감이 `date +%s` 초 단위라 절삭된다. 시작이 X.99 초면
  // 마감 X+3 은 실제 2.01 초 뒤다. 이걸 몰라 1500ms 로 잡았다가 CI 가 1427ms 로 잡아냈다.
  assert.ok(elapsed >= 1800, `상한 전에 죽으면 안 된다 (실제 ${elapsed}ms)`);
  // 상한 쪽은 느린 파일시스템(네트워크 마운트·WSL /mnt)에서 사전 git 호출이 길어질 수 있어
  // 여유를 둔다. **설계(wall-clock)를 잠그는 것은 위 텍스트 단언**이고 여기서는 "워치독이 아예
  // 없다/카운트가 터무니없다"급 회귀만 잡는다(post-checkout 식 100회 루프면 ~23s 라 걸린다).
  assert.ok(elapsed < 12000, `상한 안에 끝나야 한다 (실제 ${elapsed}ms)`);
  // fetch 가 죽었으므로 merge 도 없다 — HEAD 불변.
  assert.strictEqual(head(repo), before);
  // kill 뒤에도 시도는 남고 성공은 남지 않아야 브리프가 지속 실패를 잰다.
  const s = stamps(repo);
  assert.ok(fs.existsSync(s.attempt), 'fetch 전에 시도 스탬프를 남겨야 한다');
  assert.ok(!fs.existsSync(s.ok), 'kill 된 fetch 는 성공이 아니다');
});

ok('⑪-b 워치독이 죽인 뒤 이전 세션의 fetch 결과로 머지하지 않는다', () => {
  // 앞선 세션이 fetch 는 성공했는데 merge 가 거부되면 그 결과(추적 ref)가 남는다. 그 상태에서
  // 네트워크가 죽어 fetch 가 kill 되면, 가드가 없는 구현은 **origin 과 한 번도 통신하지 않고**
  // 옛 결과로 ff 한 뒤 "updated" 알림까지 낸다 — 사용자는 최신화됐다고 믿는다.
  const { home, repo, commits } = makeHome();
  const shared = path.join(repo, 'shared.txt');

  // 1) 충돌 dirty 로 merge 를 거부시켜 fetch 결과만 남긴다.
  fs.writeFileSync(shared, 'local-dirty');
  const stale = runChain(home);
  assert.strictEqual(stale.out, '', 'merge 가 거부돼 무음이어야 한다');
  const before = head(repo);
  assert.strictEqual(gitOut(repo, ['rev-parse', 'refs/remotes/origin/main']), commits[0], 'fetch 는 성공했어야 한다');

  // 2) dirty 를 걷어내 이제는 ff 가 가능한 상태로 만든다.
  git(repo, ['checkout', '--', 'shared.txt']);

  // 3) fetch 를 매달리게 해 워치독이 죽이게 한다.
  const stub = makeGitStub();
  const { out, code } = runChain(home, {
    PATH: `${stub}${path.delimiter}${process.env.PATH}`,
    CLAUDE_AUTOPULL_TIMEOUT: '2',
  });

  assert.strictEqual(code, 0);
  assert.strictEqual(head(repo), before, '이전 fetch 결과로 ff 하면 안 된다');
  assert.strictEqual(out, '', '통신하지 않았는데 "updated" 를 알리면 안 된다');
});

ok('⑫ 워치독이 손자(ssh·git-remote-https)까지 거둔다 — 그룹 kill 회귀 락', () => {
  const { home } = makeHome();
  const marker = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'ssp-mark-')), 'alive');
  const stub = makeGitStub({ grandchildMarker: marker });
  runChain(
    home,
    { PATH: `${stub}${path.delimiter}${process.env.PATH}`, CLAUDE_AUTOPULL_TIMEOUT: '2' },
    { timeout: 30000 },
  );
  // 내용이 아니라 mtime 을 본다. `date > marker` 는 truncate 후 write 라, 그 틈에 내용을 읽으면
  // 손자가 죽었는데도 빈 문자열이 잡혀 결과가 흔들린다(실제로 한 번 겪었다).
  // 종료 직후 1초는 진행 중이던 write 가 끝나도록 두고 잰다.
  sleepSync(1);
  const settled = fs.statSync(marker).mtimeMs;
  sleepSync(2);
  assert.strictEqual(
    fs.statSync(marker).mtimeMs,
    settled,
    '손자가 살아남아 계속 쓰고 있다 — 워치독이 프로세스 그룹째 죽이지 않는다',
  );
});

// ---------- fetch 시도·성공 스탬프(브리프 N 이 "fetch 가 N일째 성공 못 함"을 잰다) ----------
ok('⑬ fetch 가 성공하면 성공 스탬프가 시도 스탬프보다 늦게 남는다(VERIFY=0 경로도)', () => {
  for (const extra of [{}, { CLAUDE_AUTOPULL_VERIFY: '0' }]) {
    const { home, repo } = makeHome();
    const { code } = runChain(home, extra);
    assert.strictEqual(code, 0);
    const s = stamps(repo);
    assert.ok(fs.existsSync(s.attempt), `시도 스탬프가 없다 ${JSON.stringify(extra)}`);
    assert.ok(fs.existsSync(s.ok), `성공 스탬프가 없다 ${JSON.stringify(extra)}`);
    assert.ok(fs.statSync(s.ok).mtimeMs >= fs.statSync(s.attempt).mtimeMs, '성공이 시도보다 앞설 수 없다');
  }
});

ok('⑭ fetch 가 실패하면 시도만 남고 성공은 없다 — exit 0', () => {
  const { home, repo } = makeHome();
  breakOrigin(home, repo);
  const { out, code } = runChain(home);
  assert.strictEqual(code, 0);
  assert.strictEqual(out, '');
  const s = stamps(repo);
  assert.ok(fs.existsSync(s.attempt));
  assert.ok(!fs.existsSync(s.ok));
});

// dash(Ubuntu 0.5.12)는 `[ a -nt 없는파일 ]` 이 거짓이다 — 부재를 -nt 에 맡기면 여기서 매번 새로 찍힌다.
ok('⑮ 성공 기록이 없는 채 다시 실패해도 시도 스탬프는 첫 실패 시각에 머문다', () => {
  const { home, repo } = makeHome();
  breakOrigin(home, repo);
  runChain(home);
  const s = stamps(repo);
  const t = setMtimeDaysAgo(s.attempt, 5);
  runChain(home);
  assert.strictEqual(mtimeSec(s.attempt), t, '시도 스탬프를 다시 찍으면 경과 일수가 0 으로 돌아간다');
  assert.ok(!fs.existsSync(s.ok));
});

ok('⑯ 성공한 적이 있는 머신에서 실패가 이어져도 시도 스탬프는 첫 실패 시각에 머문다', () => {
  const { home, repo } = makeHome();
  runChain(home);
  const s = stamps(repo);
  breakOrigin(home, repo);
  runChain(home);
  const okT = setMtimeDaysAgo(s.ok, 6);
  const attT = setMtimeDaysAgo(s.attempt, 5);
  runChain(home);
  assert.strictEqual(mtimeSec(s.attempt), attT, '시도 스탬프를 다시 찍으면 경과 일수가 0 으로 돌아간다');
  assert.strictEqual(mtimeSec(s.ok), okT, '실패는 성공 스탬프를 건드리지 않는다');
});

ok('⑰시도와 성공이 같은 시각이면 새 시도가 시도 스탬프를 찍는다(경계 — 엄밀히 새것만 유지)', () => {
  const { home, repo } = makeHome();
  runChain(home);
  const s = stamps(repo);
  const t = setMtimeDaysAgo(s.ok, 2);
  fs.utimesSync(s.attempt, t, t);
  breakOrigin(home, repo);
  runChain(home);
  assert.ok(fs.statSync(s.attempt).mtimeMs > fs.statSync(s.ok).mtimeMs, '이번 실패가 시도로 기록돼야 한다');
  assert.strictEqual(mtimeSec(s.ok), t, '실패는 성공 스탬프를 건드리지 않는다');
});

ok('⑱ 실패가 이어지다 복구되면 성공 스탬프가 시도 스탬프보다 새것이 된다', () => {
  const { home, repo } = makeHome();
  const url = gitOut(repo, ['remote', 'get-url', 'origin']);
  breakOrigin(home, repo);
  runChain(home);
  runChain(home);
  const s = stamps(repo);
  setMtimeDaysAgo(s.attempt, 1);
  git(repo, ['remote', 'set-url', 'origin', url]);
  runChain(home);
  assert.ok(fs.existsSync(s.ok));
  assert.ok(fs.statSync(s.ok).mtimeMs > fs.statSync(s.attempt).mtimeMs);
});

ok('⑲ fetch 를 시도하지 않는 skip 경로는 스탬프를 만들지 않는다', () => {
  const cases = [
    ['CLAUDE_AUTOPULL_OFF', (h) => runChain(h.home, { CLAUDE_AUTOPULL_OFF: '1' })],
    ['.autopull-off', (h) => { fs.writeFileSync(path.join(h.repo, '.autopull-off'), ''); runChain(h.home); }],
    ['feature 브랜치', (h) => { git(h.repo, ['checkout', '-q', '-b', 'feature']); runChain(h.home); }],
    ['rebase-merge', (h) => { fs.mkdirSync(path.join(h.repo, '.git', 'rebase-merge')); runChain(h.home); }],
  ];
  for (const [name, act] of cases) {
    const h = makeHome();
    act(h);
    const s = stamps(h.repo);
    assert.ok(!fs.existsSync(s.attempt) && !fs.existsSync(s.ok), `${name}: 스탬프가 생겼다`);
  }
});

console.log(`session-start-pull.test.js: ${n} tests passed`);
