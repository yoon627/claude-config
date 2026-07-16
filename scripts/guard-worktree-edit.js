#!/usr/bin/env node
// PreToolUse guard — worktree 세션에서 그 worktree 밖의 main repo 소스 파일을
// Edit/Write 하려는 호출을 차단한다. (jq 미설치 환경이라 node 로 stdin JSON 파싱)
//
// 판정 (cwd 가 .../.claude/worktrees/<name>/ 하위인 worktree 세션일 때만):
//   file_path ∈ 현재 worktree            → allow
//   file_path ∈ <repo>/.claude/...        → allow (메타 — 일반 프로젝트)
//   repo-root==~/.claude: 직하 plans/(tracked·§10 핸드오프)·projects/·settings.local.json → allow (글로벌/핸드오프 메타)
//   file_path ∈ <repo>/...(worktree 밖)   → DENY  (main repo 소스/추적 자산 — 실수 케이스)
//   그 외 (repo 밖: 홈/다른 경로)          → allow
//
// 비-worktree 세션(cwd 가 worktree 밖): cwd repo 가 main/master 이고 fp 가 그 repo 의 추적
//   파일이면 → ask (worktree/브랜치 규약 우회 방지, CLAUDE.md §8). 그 외 전부 allow.
//   전 repo 적용, CLAUDE_MAIN_EDIT_GUARD_OFF=1 로 전역 해제. git 판정 실패는 모두 fail-open.
'use strict';

const path = require('path');
const { execFileSync } = require('child_process');

// 비-worktree 세션의 main/master 직접-편집 판정. ask 대상이면 브랜치명, 아니면 null.
// branch·tracked 판정 모두 cwd repo 기준(fp 가 cwd repo 밖이면 ls-files 128 → null → allow).
function mainTrackedEditBranch(fp, cwd) {
  if (process.env.CLAUDE_MAIN_EDIT_GUARD_OFF === '1') return null;
  if (!fp || !path.isAbsolute(fp) || !cwd) return null;
  let branch;
  try {
    branch = execFileSync('git', ['branch', '--show-current'], {
      cwd,
      timeout: 2000,
      stdio: ['ignore', 'pipe', 'ignore'],
    })
      .toString()
      .trim();
  } catch {
    return null; // git 부재·repo 밖 등 → allow
  }
  if (branch !== 'main' && branch !== 'master') return null; // detached(빈 문자열) 포함 → allow
  try {
    execFileSync('git', ['ls-files', '--error-unmatch', '--', fp], { cwd, timeout: 2000, stdio: 'ignore' });
  } catch {
    return null; // untracked/gitignored/repo 밖(128) → allow
  }
  return branch;
}

let sig = null;
try {
  sig = require('./dlc-signal.js');
} catch {
  /* 신호 기록만 skip — 차단 본연 동작은 유지(fail-open) */
}

let raw = '';
process.stdin.on('data', (c) => (raw += c));
process.stdin.on('end', () => {
  let input;
  try {
    input = JSON.parse(raw);
  } catch {
    process.exit(0); // 파싱 실패 시 정상 흐름 방해하지 않음
  }
  const norm = (p) => (p || '').replace(/\\/g, '/');
  const ti = input.tool_input || {};
  const rawFp = norm(ti.file_path || ti.notebook_path); // NotebookEdit 는 notebook_path
  // `..` 정규화 — `projects/../scripts/x` 처럼 메타 prefix 로 위장해 추적 자산 deny 를 우회하는 것 차단
  const fp = rawFp ? path.posix.normalize(rawFp) : '';
  const cwd = norm(input.cwd);
  const MARK = '/.claude/worktrees/';

  if (!fp) process.exit(0);
  if (!cwd.includes(MARK)) {
    // 비-worktree 세션 → main/master 직접-편집 가드(③)
    const branch = mainTrackedEditBranch(fp, cwd);
    if (branch) {
      if (sig) sig.emit('main-edit-ask', { session_id: input.session_id, cwd: input.cwd, detail: fp });
      process.stdout.write(
        JSON.stringify({
          hookSpecificOutput: {
            hookEventName: 'PreToolUse',
            permissionDecision: 'ask',
            permissionDecisionReason:
              `main/master 브랜치(${branch})에서 추적 파일(${fp})을 직접 수정하려 합니다. ` +
              `작업은 worktree/별도 브랜치에서 하는 게 규약입니다(CLAUDE.md §8). ` +
              `의도한 편집이면 승인하세요. (이 가드 끄기: CLAUDE_MAIN_EDIT_GUARD_OFF=1)`,
          },
        })
      );
    }
    process.exit(0);
  }

  const repoRoot = cwd.split(MARK)[0];
  const wtName = cwd.split(MARK)[1].split('/')[0];
  const wtRoot = repoRoot + MARK + wtName;

  if (fp === wtRoot || fp.startsWith(wtRoot + '/')) process.exit(0); // worktree 안
  if (fp.startsWith(repoRoot + '/.claude/')) process.exit(0); // repo .claude 메타 (일반 프로젝트)
  // repo-root 자체가 ~/.claude 인 레이아웃: 글로벌 메타가 repoRoot 직하에 있다.
  // plans/ 는 방안 A 로 tracked 지만 §10 핸드오프 문서라 worktree 세션이 main 의 상위/umbrella
  // plan 을 갱신하는 것이 정상 → allow (커밋된 plan 의 main 직접편집 마찰은 mainTrackedEditBranch
  // ask 가드가 담당). projects/memory·settings.local 은 gitignored 글로벌 상태라 worktree 복사본이
  // 없어 역시 main 경로 편집이 정상. 그 외 추적 자산(settings.json·CLAUDE.md·wiki·scripts 등)은
  // worktree 복사본 편집이 정답이라 deny 유지.
  if (repoRoot.endsWith('/.claude')) {
    const rel = fp.slice(repoRoot.length + 1);
    const seg = rel.split('/')[0];
    if (seg === 'plans' || seg === 'projects' || rel === 'settings.local.json') process.exit(0);
  }
  if (fp.startsWith(repoRoot + '/')) {
    if (sig) sig.emit('guard-worktree-deny', { session_id: input.session_id, cwd: input.cwd, detail: fp });
    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason:
            `worktree 세션(${wtRoot})인데 worktree 밖 main repo 소스(${fp})를 ` +
            `수정하려 합니다. 같은 파일의 worktree 경로(${wtRoot}/... 하위)로 ` +
            `다시 Edit/Write 하세요.`,
        },
      })
    );
    process.exit(0);
  }
  process.exit(0); // repo 밖 → allow
});
