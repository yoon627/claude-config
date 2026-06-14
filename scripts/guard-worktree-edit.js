#!/usr/bin/env node
// PreToolUse guard — worktree 세션에서 그 worktree 밖의 main repo 소스 파일을
// Edit/Write 하려는 호출을 차단한다. (jq 미설치 환경이라 node 로 stdin JSON 파싱)
//
// 판정 (cwd 가 .../.claude/worktrees/<name>/ 하위인 worktree 세션일 때만):
//   file_path ∈ 현재 worktree            → allow
//   file_path ∈ <repo>/.claude/...        → allow (plans/memory/settings 등 메타)
//   file_path ∈ <repo>/...(worktree 밖)   → DENY  (main repo 소스 — 실수 케이스)
//   그 외 (repo 밖: 홈/다른 경로)          → allow
'use strict';

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
  const fp = norm(input.tool_input && input.tool_input.file_path);
  const cwd = norm(input.cwd);
  const MARK = '/.claude/worktrees/';

  if (!fp || !cwd.includes(MARK)) process.exit(0);

  const repoRoot = cwd.split(MARK)[0];
  const wtName = cwd.split(MARK)[1].split('/')[0];
  const wtRoot = repoRoot + MARK + wtName;

  if (fp === wtRoot || fp.startsWith(wtRoot + '/')) process.exit(0); // worktree 안
  if (fp.startsWith(repoRoot + '/.claude/')) process.exit(0); // repo .claude 메타
  if (fp.startsWith(repoRoot + '/')) {
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
