#!/usr/bin/env node
// guard-worktree-edit.js 회귀 테스트 — 추적 여부 판정이 git 을 쓰므로 tmp 에 실 repo fixture 를 만든다.
'use strict';
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const GUARD = path.join(__dirname, 'guard-worktree-edit.js');

function decide(cwd, toolInput, tool = 'Edit', extraEnv = {}) {
  const inp = JSON.stringify({ cwd, tool_name: tool, tool_input: toolInput });
  let out = '';
  // SIGNAL_OFF 자기격리: deny 케이스의 신호 emit 이 실제 ~/.claude/telemetry 를 오염하지 않게
  // 테스트 파일 자신이 env 를 명시한다(호출 방식·CI env 에 의존 금지).
  const env = { ...process.env, CLAUDE_DLC_SIGNAL_OFF: '1', ...extraEnv };
  // guard 가 비0 으로 죽으면 hook 은 판정 없이 흘러가 allow 처럼 보인다 — fail-open 케이스가 크래시로
  // 통과하지 않게 따로 센다.
  try { out = execFileSync('node', [GUARD], { input: inp, env }).toString(); }
  catch { return 'crash'; }
  return out.includes('"permissionDecision":"deny"') ? 'deny' : 'allow';
}
function put(root, rel, track) {
  fs.mkdirSync(path.dirname(path.join(root, rel)), { recursive: true });
  fs.writeFileSync(path.join(root, rel), 'x');
  if (track) git(root, 'add', '--', rel);
}

// ---- ② worktree 세션(cwd ∈ .claude/worktrees/<name>/)의 worktree 밖 편집 ----
// main checkout 의 추적 파일, 또는 아직 없고 gitignored 가 아닌 새 경로만 deny.
// repo-root 자체가 ~/.claude 인 레이아웃 (이 repo). worktree 는 그 직하 .claude/worktrees/.
// ignore 판정이 결과를 가르므로 이 repo 의 실물 whitelist .gitignore 를 그대로 쓴다.
const HOME = initRepo('main', path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-guard-home-')), '.claude'));
fs.copyFileSync(path.join(__dirname, '..', '.gitignore'), path.join(HOME, '.gitignore'));
for (const rel of ['scripts/foo.js', 'scripts/ac.js', 'scripts/x.ipynb', 'CLAUDE.md', 'plans/d/x-plan.md']) put(HOME, rel, true);
for (const rel of ['projects/p/memory/MEMORY.md', 'settings.local.json', 'settings.json', 'jobs/j1/tmp/commit-msg.txt', 'scripts/[ab]c.js', 'scripts/draft.js']) put(HOME, rel, false);
const WT = path.join(HOME, '.claude/worktrees/wt1');
fs.mkdirSync(WT, { recursive: true });
// 일반 repo 레이아웃 — plans/ 가 gitignored 인 repo 에서 worktree 세션이 main 의 plan 을 고치는 경우.
const PROJ = initRepo();
fs.writeFileSync(path.join(PROJ, '.gitignore'), 'plans/\n');
for (const rel of ['src/a.js', '.claude/settings.json']) put(PROJ, rel, true);
put(PROJ, 'plans/p/p-plan.md', false);
const PWT = path.join(PROJ, '.claude/worktrees/wt1');
fs.mkdirSync(PWT, { recursive: true });
const GONE = path.join(os.tmpdir(), `dlc-guard-gone-${process.pid}`, '.claude'); // 없는 디렉토리 → git spawn 실패
const PLAIN = fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-guard-plain-')); // git repo 아닌 디렉토리 → git 128
put(PLAIN, 'src/a.js', false);

const cases = [
  // 추적 자산 → worktree 복사본 편집이 정답이므로 main 편집 deny
  ['main scripts (추적)', WT, { file_path: HOME + '/scripts/foo.js' }, 'deny'],
  ['main CLAUDE.md (추적)', WT, { file_path: HOME + '/CLAUDE.md' }, 'deny'],
  // path traversal — 남은 prefix 예외(plans/)로 위장해도 정규화 후 추적 파일로 판정 → deny
  ['traversal plans/../scripts', WT, { file_path: HOME + '/plans/../scripts/foo.js' }, 'deny'],
  // NotebookEdit 는 notebook_path 키
  ['NotebookEdit main .ipynb (추적)', WT, { notebook_path: HOME + '/scripts/x.ipynb' }, 'deny', 'NotebookEdit'],
  // 새 경로(not-ignored) → worktree 에 만들어야 브랜치 커밋에 담기고 main ff 를 막지 않는다 → deny
  ['main 새 파일 (not-ignored)', WT, { file_path: HOME + '/scripts/new.js' }, 'deny'],
  // 추적 중이지만 §10 핸드오프 문서 → allow
  ['main plans (추적, 예외)', WT, { file_path: HOME + '/plans/d/x-plan.md' }, 'allow'],
  ['main plans 새 파일 (예외)', WT, { file_path: HOME + '/plans/d2/y-plan.md' }, 'allow'],
  // gitignored 는 대개 worktree 복사본이 없다 → allow (기존·새 파일 모두)
  ['main projects/MEMORY (ignored)', WT, { file_path: HOME + '/projects/p/memory/MEMORY.md' }, 'allow'],
  ['main settings.local.json (ignored)', WT, { file_path: HOME + '/settings.local.json' }, 'allow'],
  ['main settings.json (ignored)', WT, { file_path: HOME + '/settings.json' }, 'allow'],
  ['main jobs tmp (ignored) — 2026-07-16 오탐', WT, { file_path: HOME + '/jobs/j1/tmp/commit-msg.txt' }, 'allow'],
  ['main jobs 새 파일 (ignored)', WT, { file_path: HOME + '/jobs/j2/tmp/new.txt' }, 'allow'],
  ['main telemetry 새 파일 (whitelist 밖)', WT, { file_path: HOME + '/telemetry/x.jsonl' }, 'allow'],
  // main 에만 있는 기존 untracked 파일(not-ignored) → worktree 사본이 없다 → allow
  ['main scripts 기존 untracked', WT, { file_path: HOME + '/scripts/draft.js' }, 'allow'],
  // glob 문자가 든 기존 untracked 이름이 추적 파일(ac.js)에 pathspec 매칭되지 않는다
  ['main glob 이름 (기존 untracked)', WT, { file_path: HOME + '/scripts/[ab]c.js' }, 'allow'],
  ['worktree 안', WT, { file_path: WT + '/scripts/bar.js' }, 'allow'],
  ['repo 밖', WT, { file_path: path.join(os.tmpdir(), 'dlc-guard-elsewhere.txt') }, 'allow'],
  // 일반 repo
  ['일반 repo src (추적)', PWT, { file_path: PROJ + '/src/a.js' }, 'deny'],
  ['일반 repo src 새 파일 (not-ignored)', PWT, { file_path: PROJ + '/src/new.js' }, 'deny'],
  ['일반 repo plans (ignored) — 2026-09-14 오탐', PWT, { file_path: PROJ + '/plans/p/p-plan.md' }, 'allow'],
  ['일반 repo plans 새 파일 (ignored, 부모 없음)', PWT, { file_path: PROJ + '/plans/q/q-plan.md' }, 'allow'],
  ['일반 repo .claude 메타 (추적)', PWT, { file_path: PROJ + '/.claude/settings.json' }, 'allow'],
  // .git/ 은 모든 worktree 가 공유하는 common dir — worktree 사본이 없다 → allow (기존·새 파일 모두)
  ['일반 repo .git/config', PWT, { file_path: PROJ + '/.git/config' }, 'allow'],
  ['일반 repo .git/hooks 새 파일', PWT, { file_path: PROJ + '/.git/hooks/pre-push' }, 'allow'],
  // git 판정 실패 → fail-open
  ['cwd 디렉토리 없음(spawn 실패) → allow', GONE + '/.claude/worktrees/wt1', { file_path: GONE + '/scripts/x.js' }, 'allow'],
  ['git repo 아님(128) → allow', PLAIN + '/.claude/worktrees/wt1', { file_path: PLAIN + '/src/new.js' }, 'allow'],
  // 상속된 GIT_DIR 이 다른 repo 를 가리켜도 cwd 에서 얻은 main checkout 기준으로 판정
  ['상속 GIT_DIR 무시 (추적)', WT, { file_path: HOME + '/scripts/foo.js' }, 'deny', 'Edit', { GIT_DIR: path.join(PROJ, '.git') }],
];

let fail = 0;
for (const [name, cwd, ti, want, tool, env] of cases) {
  const got = decide(cwd, ti, tool || 'Edit', env);
  const ok = got === want; if (!ok) fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}: want=${want} got=${got}`);
}

// ---- ③ main-edit 가드: 비-worktree 세션에서 main/master 추적 파일 직접 편집 → ask ----
// 실 git repo fixture 필요(branch --show-current·ls-files spawn). cwd 는 worktree 밖(repo 루트/하위).
function git(dir, ...args) { execFileSync('git', ['-C', dir, ...args], { stdio: 'ignore' }); }
function initRepo(branch, at) {
  const dir = at || fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-guard-repo-'));
  execFileSync('git', ['init', '-b', branch || 'main', dir], { stdio: 'ignore' });
  git(dir, 'config', 'user.email', 't@t');
  git(dir, 'config', 'user.name', 't');
  git(dir, 'config', 'commit.gpgsign', 'false');
  return dir;
}
function decideMain(fp, cwd, extraEnv, permissionMode) {
  const inp = JSON.stringify({
    cwd, session_id: 's', tool_name: 'Edit', tool_input: { file_path: fp },
    ...(permissionMode ? { permission_mode: permissionMode } : {}),
  });
  const env = { ...process.env, CLAUDE_DLC_SIGNAL_OFF: '1', ...extraEnv };
  let out = '';
  try { out = execFileSync('node', [GUARD], { input: inp, env }).toString(); }
  catch { return 'crash'; }
  if (out.includes('"permissionDecision":"ask"')) return 'ask';
  if (out.includes('"permissionDecision":"deny"')) return 'deny';
  return 'allow';
}

const rMain = initRepo();          // branch main, tracked.js·a.log(ignored)
fs.writeFileSync(path.join(rMain, '.gitignore'), '*.log\n');
fs.writeFileSync(path.join(rMain, 'tracked.js'), 'x'); git(rMain, 'add', 'tracked.js');
fs.writeFileSync(path.join(rMain, 'untracked.js'), 'x');
fs.writeFileSync(path.join(rMain, 'a.log'), 'x');
fs.mkdirSync(path.join(rMain, 'sub'));
const rFeat = initRepo('feature'); // branch feature, tracked
fs.writeFileSync(path.join(rFeat, 'tracked.js'), 'x'); git(rFeat, 'add', 'tracked.js');
const rDet = initRepo();           // detached HEAD 재현용(커밋 필요)
fs.writeFileSync(path.join(rDet, 'f.js'), 'x'); git(rDet, 'add', 'f.js'); git(rDet, 'commit', '-m', 'i');
git(rDet, 'checkout', '--detach', 'HEAD');
const outside = path.join(os.tmpdir(), `guard-outside-${process.pid}.js`);

const mcases = [
  ['ⓐ main+tracked → ask', path.join(rMain, 'tracked.js'), rMain, {}, 'ask'],
  ['ⓑ feature+tracked → allow', path.join(rFeat, 'tracked.js'), rFeat, {}, 'allow'],
  ['ⓒ main+untracked → allow', path.join(rMain, 'untracked.js'), rMain, {}, 'allow'],
  ['ⓒ main+ignored → allow', path.join(rMain, 'a.log'), rMain, {}, 'allow'],
  ['ⓓ fp repo 밖 → allow', outside, rMain, {}, 'allow'],
  ['ⓔ OFF env → allow', path.join(rMain, 'tracked.js'), rMain, { CLAUDE_MAIN_EDIT_GUARD_OFF: '1' }, 'allow'],
  ['ⓗ cross-repo(cwd=main, fp∈feature) → allow (B2)', path.join(rFeat, 'tracked.js'), rMain, {}, 'allow'],
  ['ⓙ detached HEAD → allow', path.join(rDet, 'f.js'), rDet, {}, 'allow'],
  ['ⓚ cwd=repo 하위 디렉토리 → ask', path.join(rMain, 'tracked.js'), path.join(rMain, 'sub'), {}, 'ask'],
  ['ⓛ auto 모드 → allow', path.join(rMain, 'tracked.js'), rMain, {}, 'allow', 'auto'],
  ['ⓜ default 모드 → ask 유지', path.join(rMain, 'tracked.js'), rMain, {}, 'ask', 'default'],
  ['ⓝ plan 모드 → ask 유지', path.join(rMain, 'tracked.js'), rMain, {}, 'ask', 'plan'],
  // glob 문자가 든 untracked 이름이 tracked.js 에 pathspec 매칭되지 않는다
  ['ⓞ main+glob 이름 untracked → allow', path.join(rMain, '[st]racked.js'), rMain, {}, 'allow'],
];
for (const [name, fp, cwd, env, want, mode] of mcases) {
  const got = decideMain(fp, cwd, env, mode);
  const okc = got === want; if (!okc) fail++;
  console.log(`${okc ? 'PASS' : 'FAIL'} ${name}: want=${want} got=${got}`);
}

// ⓘ 신호 emit: ask 발생 시 main-edit-ask 1줄이 기록되는가 (SIGNAL_DIR 격리, OFF 해제)
{
  const sigDir = fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-guard-sig-'));
  decideMain(path.join(rMain, 'tracked.js'), rMain, { CLAUDE_DLC_SIGNAL_OFF: '0', CLAUDE_DLC_SIGNAL_DIR: sigDir });
  let rows = [];
  try {
    rows = fs.readFileSync(path.join(sigDir, 'dlc-signals.jsonl'), 'utf8')
      .trim().split('\n').filter(Boolean).map((l) => JSON.parse(l));
  } catch { /* 파일 없음 → 빈 배열 → FAIL */ }
  const okc = rows.length === 1 && rows[0].kind === 'main-edit-ask' && rows[0].axis === 'failure';
  if (!okc) fail++;
  console.log(`${okc ? 'PASS' : 'FAIL'} ⓘ main-edit-ask 신호 emit: got=${JSON.stringify(rows.map((r) => r.kind))}`);
}

console.log(fail === 0 ? 'ALL PASS' : `${fail} FAIL`);
process.exit(fail === 0 ? 0 : 1);
