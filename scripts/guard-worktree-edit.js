#!/usr/bin/env node
// PreToolUse guard — worktree 세션에서 그 worktree 밖 main checkout 의 추적 파일 편집과
// 새 파일 생성을 차단한다. (jq 미설치 환경이라 node 로 stdin JSON 파싱)
//
// 판정 (cwd 가 .../.claude/worktrees/<name>/ 하위인 worktree 세션일 때만):
//   file_path ∈ 현재 worktree            → allow
//   file_path ∈ <repo>/.claude/...        → allow (메타 — 일반 프로젝트)
//   file_path ∈ <repo>/.git/...           → allow (모든 worktree 가 공유하는 common dir — 사본 없음)
//   repo-root==~/.claude: 직하 plans/(tracked·§10 핸드오프) → allow
//   file_path ∈ <repo>/... 이고 main checkout 추적 파일 → DENY (worktree 복사본을 고쳐야 할 실수 케이스)
//   file_path ∈ <repo>/... 이고 아직 없고 gitignored 아님 → DENY (worktree 에 만들어야 브랜치에 담긴다)
//   그 외 (gitignored, main 에만 있는 기존 untracked, repo 밖) → allow — 대개 worktree 사본이 없다
//     (/wt 가 복사한 .env 처럼 사본이 있는 gitignored 파일도 allow — 사본 유무로 막으면 worktree 에도
//      있는 gitignored plan 을 main 에서 고치는 정상 편집까지 다시 막힌다)
// EnterWorktree 로 들어간 세션은 네이티브 격리가 이 hook 보다 먼저 worktree 밖 편집을 거부하므로,
// 이 판정이 실제로 걸리는 것은 격리되지 않은 채 cwd 가 worktree 안인 세션이다(worktree 디렉토리에서
// 바로 시작한 세션, ExitWorktree 뒤 Bash cd 로 cwd 가 돌아온 세션 등).
//
// 비-worktree 세션(cwd 가 worktree 밖): cwd repo 가 main/master 이고 fp 가 그 repo 의 추적
//   파일이면 → ask (worktree/브랜치 규약 우회 방지, CLAUDE.md §8). 그 외 전부 allow.
//   전 repo 적용, CLAUDE_MAIN_EDIT_GUARD_OFF=1 로 전역 해제. git 판정 실패는 모두 fail-open.
'use strict';

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

// repo-routing 변수 — session-brief.js 의 GIT_LOCAL_ENV 와 같은 목록(출처 `git rev-parse --local-env-vars`).
// 상속되면 cwd 가 아니라 그 변수가 가리키는 repo 를 판정한다. 편집마다 도는 hook 이라 SessionStart hook
// 모듈을 require 하지 않고 복제한다.
const GIT_LOCAL_ENV = [
  'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_CONFIG', 'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT',
  'GIT_OBJECT_DIRECTORY', 'GIT_DIR', 'GIT_WORK_TREE', 'GIT_IMPLICIT_WORK_TREE', 'GIT_GRAFT_FILE',
  'GIT_INDEX_FILE', 'GIT_NO_REPLACE_OBJECTS', 'GIT_REPLACE_REF_BASE', 'GIT_PREFIX',
  'GIT_INTERNAL_SUPER_PREFIX', 'GIT_SHALLOW_FILE', 'GIT_COMMON_DIR',
];

// { status, stdout } — spawn 실패·timeout 은 status null. core.fsmonitor 는 repo 설정의 명령을
// 실행하므로 끈다(편집 대상이 남의 repo 일 수 있다).
function git(cwd, args) {
  const env = { ...process.env };
  for (const k of GIT_LOCAL_ENV) delete env[k];
  const r = spawnSync('git', ['-c', 'core.fsmonitor=', ...args], {
    cwd,
    env,
    timeout: 2000,
    stdio: ['ignore', 'pipe', 'ignore'],
  });
  return r.error ? { status: null, stdout: '' } : { status: r.status, stdout: String(r.stdout) };
}

// cwd repo 의 추적 파일인가. untracked·gitignored·repo 밖(128)·git 실패는 false(fail-open).
// --literal-pathspecs: `[ab]c.js` 같은 이름이 추적 파일 `ac.js` 에 glob 매칭되지 않게.
const isTracked = (fp, cwd) => git(cwd, ['--literal-pathspecs', 'ls-files', '--error-unmatch', '--', fp]).status === 0;

// 아직 없고 gitignored 도 아닌 새 경로인가(check-ignore 1 = not ignored; git 실패는 false).
// check-ignore 는 경로를 그대로 받는다 — --literal-pathspecs 를 붙이면 128 로 거부돼 조용히 false 가 된다.
const isNewUnignored = (fp, cwd) => !fs.existsSync(fp) && git(cwd, ['check-ignore', '-q', '--', fp]).status === 1;

// 비-worktree 세션의 main/master 직접-편집 판정. ask 대상이면 브랜치명, 아니면 null.
// branch·tracked 판정 모두 cwd repo 기준(fp 가 cwd repo 밖이면 null → allow).
function mainTrackedEditBranch(fp, cwd) {
  if (process.env.CLAUDE_MAIN_EDIT_GUARD_OFF === '1') return null;
  if (!fp || !path.isAbsolute(fp) || !cwd) return null;
  const r = git(cwd, ['branch', '--show-current']);
  if (r.status !== 0) return null; // git 부재·repo 밖 등 → allow
  const branch = r.stdout.trim();
  if (branch !== 'main' && branch !== 'master') return null; // detached(빈 문자열) 포함 → allow
  return isTracked(fp, cwd) ? branch : null;
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
  // `..` 정규화 — `plans/../scripts/x` 처럼 예외 prefix 로 위장해 추적 자산 deny 를 우회하는 것 차단
  const fp = rawFp ? path.posix.normalize(rawFp) : '';
  const cwd = norm(input.cwd);
  const MARK = '/.claude/worktrees/';

  if (!fp) process.exit(0);
  if (!cwd.includes(MARK)) {
    // 비-worktree 세션 → main/master 직접-편집 가드(③)
    // auto 모드는 안전 분류기가 매 액션을 판정하므로 확인 프롬프트를 겹쳐 걸지 않는다
    // (사용자 지시 2026-08-06). 이 모드에서 worktree 규약은 CLAUDE.md §3-1 규약으로만 남는다.
    // worktree 세션의 worktree 밖 편집 deny(아래)는 프롬프트가 아니라 데이터 보호라 모드 무관하게 유지.
    const branch = input.permission_mode === 'auto' ? null : mainTrackedEditBranch(fp, cwd);
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
  if (fp.startsWith(repoRoot + '/.git/')) process.exit(0); // git common dir — worktree 사본 없음
  // repo-root 자체가 ~/.claude 인 레이아웃: plans/ 는 tracked 지만 §10 핸드오프 문서라 worktree
  // 세션이 main 의 상위/umbrella plan 을 갱신하는 것이 정상 → allow.
  if (repoRoot.endsWith('/.claude') && fp.startsWith(repoRoot + '/plans/')) process.exit(0);
  // gitignored(projects/memory·settings.local·jobs 등)와 main 에만 있는 기존 untracked 파일은 worktree
  // 사본이 없어 main 경로 편집이 정상. 추적 자산은 worktree 사본을 고치고, 새 파일은 worktree 에 만들어야
  // 브랜치에 담긴다(main 에 남으면 같은 경로를 들여오는 ff-merge·pull 이 untracked 충돌로 멈춘다).
  if (!fp.startsWith(repoRoot + '/')) process.exit(0); // repo 밖 → allow
  const tracked = isTracked(fp, repoRoot);
  if (!tracked && !isNewUnignored(fp, repoRoot)) process.exit(0);
  if (sig) sig.emit('guard-worktree-deny', { session_id: input.session_id, cwd: input.cwd, detail: fp });
  const wtFp = wtRoot + fp.slice(repoRoot.length);
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: tracked
          ? `worktree 세션(${wtRoot})인데 worktree 밖 main checkout 의 추적 파일(${fp})을 ` +
            `수정하려 합니다. 같은 파일의 worktree 경로(${wtFp})를 Edit/Write 하세요.`
          : `worktree 세션(${wtRoot})인데 worktree 밖 main checkout 에 새 파일(${fp})을 ` +
            `만들려 합니다. 브랜치에 담기도록 worktree 경로(${wtFp})에 만드세요.`,
      },
    })
  );
  process.exit(0);
});
