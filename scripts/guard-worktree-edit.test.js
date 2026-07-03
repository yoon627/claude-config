#!/usr/bin/env node
// guard-worktree-edit.js 회귀 테스트 — cwd 독립(가짜 절대경로로 로직만 검증).
'use strict';
const { execFileSync } = require('child_process');
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
console.log(fail === 0 ? 'ALL PASS' : `${fail} FAIL`);
process.exit(fail === 0 ? 0 : 1);
