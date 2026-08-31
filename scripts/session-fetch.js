#!/usr/bin/env node
// SessionStart hook(async) — 세션이 열린 repo 의 remote-tracking ref 를 갱신한다. **fetch 만 하고
// merge 하지 않는다**(로컬 커밋·작업트리 불변).
//
// 존재 이유: 브리프의 밀림 판정(신호 O)은 캐시된 remote-tracking ref 로만 하는데, `~/.claude` 밖에는
// 그 ref 를 갱신할 주체가 없었다. 그래서 "한 번도 fetch 하지 않은 채 밀린" 구간이 통째로 무음이었다 —
// 2026-08-31 실측: `refs/remotes/origin/dev` 가 08-28 17:43 부터 2.7일 얼어 있는 동안 원격은 37커밋
// 앞서 있었고, 그동안 어떤 신호도 그 사실을 말할 수 없었다.
//
// 계약: async(세션 시작을 네트워크에 묶지 않는다) · 인증 프롬프트 금지(매달리는 것이 최악) ·
//   최근에 fetch 했으면 skip · `~/.claude` 는 제외(그쪽은 기존 ff-only pull 훅이 담당) ·
//   전부 fail-open(무음 exit 0). ref 가 실제로 움직였을 때만 한 줄 낸다 — 안 그러면 사용자는
//   갱신된 사실을 한 세션 늦게 알게 된다.
'use strict';
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

let readHookCwd;
try {
  ({ readHookCwd } = require('./hook-cwd.js'));
} catch {
  readHookCwd = (cb) => cb(process.cwd()); // 모듈 부재 → 폴백(훅이 죽는 것보다 낫다)
}
let brief = null;
try {
  brief = require('./session-brief.js'); // 밀림 문장은 브리프가 단일 소스다(두 곳에서 만들면 갈라진다)
} catch {
  /* 브리프 부재·손상 → fetch 만 하고 조용히 */
}

const FETCH_MS = 20000; // 원격 왕복 상한. async 라 세션을 막지는 않지만 무한정 매달리지 않는다
const GIT_MS = 5000;

function git(dir, args, ms) {
  return execFileSync('git', ['-C', dir, ...args], {
    timeout: ms || GIT_MS,
    stdio: ['ignore', 'pipe', 'ignore'],
    env: {
      ...process.env,
      // 자격증명을 물어보는 순간 훅은 timeout 까지 매달린다. 물어볼 바에는 실패하는 게 낫다.
      GIT_TERMINAL_PROMPT: '0',
      GIT_ASKPASS: 'echo',
      GIT_SSH_COMMAND: 'ssh -oBatchMode=yes',
    },
  }).toString();
}

// 마지막 fetch 시각. git 은 fetch 할 때마다 FETCH_HEAD 를 다시 쓴다(가져온 게 없어도).
function minutesSinceFetch(commonDir) {
  try {
    return (Date.now() - fs.statSync(path.join(commonDir, 'FETCH_HEAD')).mtimeMs) / 60000;
  } catch {
    return Infinity; // 한 번도 fetch 안 함
  }
}

function run(cwd, env) {
  if (env.CLAUDE_SESSION_FETCH_OFF === '1') return '';
  if (!cwd) return '';

  let top;
  let commonDir;
  try {
    const out = git(cwd, ['rev-parse', '--show-toplevel', '--git-common-dir']).split('\n');
    top = (out[0] || '').trim();
    commonDir = path.resolve(cwd, (out[1] || '').trim());
  } catch {
    return ''; // 비 git → 무음
  }
  if (!top) return '';

  const claudeDir = path.join(os.homedir(), '.claude');
  // `~/.claude` 는 기존 pull 훅이 ff-only 로 담당한다. 여기서 또 건드리면 두 훅이 같은 ref 를 다툰다.
  if (path.resolve(commonDir).toLowerCase() === path.join(claudeDir, '.git').toLowerCase()) return '';

  const rawMin = Number(env.CLAUDE_SESSION_FETCH_MIN_MINUTES);
  const minMinutes = Number.isFinite(rawMin) && rawMin >= 0 ? rawMin : 15;
  if (minutesSinceFetch(commonDir) < minMinutes) return ''; // 방금 fetch 함 → 원격을 두드리지 않는다

  // upstream 이 없으면 무엇 대비인지 정할 수 없어 브리프도 밀림을 판정하지 않는다 → 네트워크를 쓸 이유가 없다.
  let upstream;
  try {
    upstream = git(cwd, ['rev-parse', '--abbrev-ref', '@{upstream}']).trim();
  } catch {
    return '';
  }
  if (!upstream || !upstream.includes('/')) return '';
  const remote = upstream.slice(0, upstream.indexOf('/'));

  const before = (() => {
    try {
      return git(cwd, ['rev-parse', upstream]).trim();
    } catch {
      return '';
    }
  })();

  try {
    git(cwd, ['fetch', '--quiet', '--no-tags', remote], FETCH_MS);
  } catch {
    return ''; // 오프라인·인증 실패·원격 없음 → 무음. 그 상태가 오래가면 브리프가 "fetch 안 함"으로 말한다
  }

  let after = '';
  try {
    after = git(cwd, ['rev-parse', upstream]).trim();
  } catch {
    return '';
  }
  if (!before || before === after) return ''; // 움직인 게 없으면 할 말도 없다

  if (!brief || typeof brief.currentRepoLine !== 'function') return '';
  const line = brief.currentRepoLine(cwd, claudeDir, env, new Date());
  return line ? line + '\n' : '';
}

if (require.main === module) {
  try {
    readHookCwd((cwd) => {
      let out = '';
      try {
        out = run(cwd, process.env);
      } catch {
        /* 어떤 예외도 세션 시작을 막지 않는다(fail-open) */
      }
      if (!out) {
        process.exit(0);
      } else {
        process.stdout.write(out, () => process.exit(0));
      }
    });
  } catch {
    process.exit(0);
  }
}

module.exports = { run };
