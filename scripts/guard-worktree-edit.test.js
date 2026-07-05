#!/usr/bin/env node
// guard-worktree-edit.js 회귀 테스트 — cwd 독립(가짜 절대경로로 로직만 검증).
'use strict';
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const GUARD = path.join(__dirname, 'guard-worktree-edit.js');

// repo-root 자체가 ~/.claude 인 레이아웃 (이 repo). worktree 는 그 직하 .claude/worktrees/.
const REPO = '/home/u/.claude';
const WT = REPO + '/.claude/worktrees/wt1';

function decide(toolInput, tool = 'Edit') {
  const inp = JSON.stringify({ cwd: WT, tool_name: tool, tool_input: toolInput });
  let out = '';
  // SIGNAL_OFF 자기격리: deny 케이스의 신호 emit 이 실제 ~/.claude/telemetry 를 오염하지 않게
  // 테스트 파일 자신이 env 를 명시한다(호출 방식·CI env 에 의존 금지).
  const env = { ...process.env, CLAUDE_DLC_SIGNAL_OFF: '1' };
  try { out = execFileSync('node', [GUARD], { input: inp, env }).toString(); }
  catch (e) { out = e.stdout ? e.stdout.toString() : ''; }
  return out.includes('"permissionDecision":"deny"') ? 'deny' : 'allow';
}

const cases = [
  // gitignored 글로벌 메타 → worktree 밖 편집 allow (worktree 복사본 없음)
  ['main plans', { file_path: REPO + '/plans/x-plan.md' }, 'allow'],
  ['main projects/MEMORY', { file_path: REPO + '/projects/p/memory/MEMORY.md' }, 'allow'],
  ['main settings.local.json', { file_path: REPO + '/settings.local.json' }, 'allow'],
  // 추적 자산 → worktree 복사본 편집이 정답이므로 main 편집 deny
  ['main settings.json', { file_path: REPO + '/settings.json' }, 'deny'],
  ['main scripts', { file_path: REPO + '/scripts/foo.js' }, 'deny'],
  ['main CLAUDE.md', { file_path: REPO + '/CLAUDE.md' }, 'deny'],
  // worktree 안 → allow
  ['worktree 안', { file_path: WT + '/scripts/bar.js' }, 'allow'],
  // path traversal — projects/ prefix 로 위장해 추적 자산 deny 우회 시도 → 정규화 후 deny
  ['traversal projects/../scripts', { file_path: REPO + '/projects/../scripts/x.js' }, 'deny'],
  // NotebookEdit 는 notebook_path 키 → 추적 자산 deny 적용
  ['NotebookEdit main .ipynb', { notebook_path: REPO + '/scripts/x.ipynb' }, 'deny', 'NotebookEdit'],
  // repo 밖(홈 등) → allow
  ['repo 밖 home', { file_path: '/home/u/other.txt' }, 'allow'],
];

let fail = 0;
for (const [name, ti, want, tool] of cases) {
  const got = decide(ti, tool || 'Edit');
  const ok = got === want; if (!ok) fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}: want=${want} got=${got}`);
}

// ---- ③ main-edit 가드: 비-worktree 세션에서 main/master 추적 파일 직접 편집 → ask ----
// 실 git repo fixture 필요(branch --show-current·ls-files spawn). cwd 는 worktree 밖(repo 루트/하위).
function git(dir, ...args) { execFileSync('git', ['-C', dir, ...args], { stdio: 'ignore' }); }
function initRepo(branch) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'dlc-guard-repo-'));
  execFileSync('git', ['init', '-b', branch || 'main', dir], { stdio: 'ignore' });
  git(dir, 'config', 'user.email', 't@t');
  git(dir, 'config', 'user.name', 't');
  git(dir, 'config', 'commit.gpgsign', 'false');
  return dir;
}
function decideMain(fp, cwd, extraEnv) {
  const inp = JSON.stringify({ cwd, session_id: 's', tool_name: 'Edit', tool_input: { file_path: fp } });
  const env = { ...process.env, CLAUDE_DLC_SIGNAL_OFF: '1', ...extraEnv };
  let out = '';
  try { out = execFileSync('node', [GUARD], { input: inp, env }).toString(); }
  catch (e) { out = e.stdout ? e.stdout.toString() : ''; }
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
];
for (const [name, fp, cwd, env, want] of mcases) {
  const got = decideMain(fp, cwd, env);
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
