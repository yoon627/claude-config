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
//   전부 fail-open(무음 exit 0). ref 가 움직였고 **그래서 할 말이 생겼을 때만** 한 줄 낸다
//   (움직였어도 뒤처지지 않았으면 낼 말이 없다).
// 출력 시점 주의: async 훅의 stdout 은 **첫 턴 뒤에** 도달한다(wiki [[git-hook-network-safety]] §1 —
//   "네트워크는 async, 사용자에게 보여야 할 판정은 동기로"). 세션 시작 시점의 판정은 동기인
//   session-brief 가 캐시된 ref 로 계속 담당하고, 이 훅의 한 줄은 그보다 늦게 도착하는 보완이다.
//   그래도 다음 세션까지 기다리는 것보다는 낫다.
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
  // 밀림 문장·스탬프 키·경로 비교를 브리프에서 가져온다. 두 곳에서 만들면 갈라지고, 갈라진 키는
  // "한쪽은 못 찾고 다른 쪽은 굶는" 조용한 실패가 된다.
  brief = require('./session-brief.js');
} catch {
  /* 브리프 부재·손상 → fetch 만 하고 조용히 */
}
const GIT_LOCAL_ENV = (brief && brief.GIT_LOCAL_ENV) || ['GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE'];

// settings 의 훅 timeout 은 30s 다. 러너가 30s 에 Node 를 죽이면 git·ssh 자식이 고아로 남아
// 세션이 끝난 뒤에도 계속 돈다 → 최악 합이 30s 안에 들어오게 잡는다.
// 실제 최악: stdin 1 + 사전 git 4회(rev-parse·symbolic-ref·for-each-ref·rev-parse) × 2 + fetch 8 +
// 사후 rev-parse 2 + currentRepoLine 자체 예산 4(진행 중 호출 포함) ≈ 23s.
const FETCH_MS = 8000;
const GIT_MS = 2000;

function git(dir, args, ms) {
  // 상속된 GIT_* 는 `-C` 를 이긴다. 3개만 지우면 `GIT_COMMON_DIR` 로 새어나가 **무관한 repo 를
  // fetch 하고 거기에 스탬프까지 남긴다**(실측) → repo 를 가리키는 변수 전체를 지운다.
  const env = { ...process.env };
  for (const k of GIT_LOCAL_ENV) delete env[k];
  // 자격증명을 물어보는 순간 훅은 timeout 까지 매달린다. 물어볼 바에는 실패하는 게 낫다.
  // `GIT_ASKPASS=echo` 는 쓰지 않는다 — 실패하는 helper 가 아니라 **프롬프트 문자열을 자격증명으로
  // 되돌려준다**(`Username for ...` 를 아이디로 보낸다). 대신 물어볼 경로 자체를 없앤다:
  // 터미널 프롬프트 차단 + credential helper·askPass 무력화 + ssh BatchMode.
  env.GIT_TERMINAL_PROMPT = '0';
  delete env.GIT_ASKPASS;
  delete env.SSH_ASKPASS;
  // ConnectTimeout 이 없으면 blackhole 로 향한 TCP connect 가 SSH 단계에서 통째로 매달린다
  // (wiki [[git-hook-network-safety]] §1 — 그 페이지가 지목한 정확한 함정이다).
  // 사용자의 `GIT_SSH_COMMAND`(`ssh -i <key> -o ProxyCommand=…`)를 통째로 덮으면 그 사람의 fetch 는
  // 전부 실패하고, 무음이라 원인도 안 보인다 → 보존하고 옵션만 덧댄다.
  env.GIT_SSH_COMMAND = `${process.env.GIT_SSH_COMMAND || 'ssh'} -oBatchMode=yes -oConnectTimeout=10`;
  return execFileSync(
    'git',
    [
      '-c', 'core.fsmonitor=',
      '-c', 'credential.helper=',
      '-c', 'core.askPass=',
      // fetch 는 ref 를 갱신하며 **그 repo 의 훅**(reference-transaction·pre-auto-gc)을 실행한다(실측).
      // 사용자가 아무 git 명령도 치지 않았는데 남의 repo 훅이 도는 것은 core.fsmonitor 와 같은 문제다.
      '-c', `core.hooksPath=${path.join(os.tmpdir(), 'claude-hooks-disabled-nonexistent')}`,
      // HTTP 는 connect 후 전송이 멈추는 경우가 따로 있다. execFileSync 의 timeout 이 마지막 방어지만
      // 그건 강제 종료라, git 이 스스로 포기할 수 있는 상한을 먼저 준다.
      '-c', 'http.lowSpeedLimit=1000',
      '-c', 'http.lowSpeedTime=10',
      '-C', dir,
      ...args,
    ],
    {
      timeout: ms || GIT_MS,
      maxBuffer: 16 * 1024 * 1024,
      stdio: ['ignore', 'pipe', 'ignore'],
      env,
    },
  ).toString();
}

// 이 훅이 **그 추적 ref** 를 마지막으로 건드린 시각. `FETCH_HEAD` 도, remote 단위 스탬프도 쓰지 않는다 —
// 둘 다 한 브랜치의 fetch 가 다른 브랜치의 판정을 덮어서, `main` 세션 뒤 15분 안의 `feat` 세션이
// 영영 굶는다(실측). 브리프와 **같은 함수**로 키를 만든다.
function stampPath(commonDir, fullRef) {
  const name = brief && brief.fetchStampName
    ? brief.fetchStampName(fullRef)
    : `claude-fetch-${fullRef.replace(/[^\w.-]/g, '_')}`;
  return path.join(commonDir, name);
}
function minutesSinceFetch(commonDir, fullRef) {
  try {
    return (Date.now() - fs.statSync(stampPath(commonDir, fullRef)).mtimeMs) / 60000;
  } catch {
    return Infinity; // 이 훅이 이 ref 를 건드린 적 없음
  }
}

// 성공이든 실패든 찍는다 — 실패에 backoff 가 없으면 닿지 않는 원격에 매 세션 재시도한다.
function stamp(commonDir, fullRef) {
  try {
    fs.writeFileSync(stampPath(commonDir, fullRef), '');
  } catch {
    /* .git 에 못 써도 fetch 자체는 끝났다 — 다음 세션에 한 번 더 할 뿐이다 */
  }
}

function run(cwd, env) {
  // 브리프의 kill switch 도 존중한다. 이 훅이 `currentRepoLine` 을 직접 부르므로 존중하지 않으면
  // README 가 "즉시 차단 레버"로 안내하는 `CLAUDE_BRIEF_CWD_OFF` 가 이 줄에는 안 듣는다(실측).
  if (env.CLAUDE_SESSION_FETCH_OFF === '1') return '';
  if (!cwd) return '';
  const briefOff = env.CLAUDE_SESSION_BRIEF_OFF === '1' || env.CLAUDE_BRIEF_CWD_OFF === '1';

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

  // 브리프가 감시하는 repo(기본 `~/.claude`)는 기존 pull 훅이 ff-only 로 담당한다. 여기서 또 건드리면
  // 두 훅이 같은 ref 를 다툰다. 판정은 브리프와 **같은 `samePath`** 로 한다(realpath·junction 정규화 —
  // 문자열 소문자 비교는 symlink 된 홈에서 제외가 빠진다).
  const claudeDir = env.CLAUDE_BRIEF_REPO || path.join(os.homedir(), '.claude');
  const same = brief && brief.samePath
    ? brief.samePath(commonDir, path.join(claudeDir, '.git'))
    : path.resolve(commonDir).toLowerCase() === path.join(claudeDir, '.git').toLowerCase();
  if (same) return '';

  // upstream 이 없으면 무엇 대비인지 정할 수 없어 브리프도 밀림을 판정하지 않는다 → 네트워크를 쓸 이유가 없다.
  // remote 이름·원격 브랜치·추적 ref 를 **한 번에** 받는다. `origin/feature/x` 를 문자열로 쪼개면
  // 어디까지가 remote 인지 알 수 없다(슬래시가 양쪽에 다 있다).
  let head;
  let remote;
  let remoteRef;
  let trackingRef;
  try {
    head = git(cwd, ['symbolic-ref', '-q', 'HEAD']).trim(); // detached 면 실패 → skip
    const f = git(cwd, [
      'for-each-ref',
      '--format=%(upstream:remotename)\t%(upstream:remoteref)\t%(upstream)',
      head,
    ]).split('\t');
    remote = (f[0] || '').trim();
    remoteRef = (f[1] || '').trim();
    trackingRef = (f[2] || '').trim();
  } catch {
    return '';
  }
  if (!remote || !remoteRef || !trackingRef) return '';

  const rawMin = Number(env.CLAUDE_SESSION_FETCH_MIN_MINUTES);
  const minMinutes = Number.isFinite(rawMin) && rawMin >= 0 ? rawMin : 15;
  if (minutesSinceFetch(commonDir, trackingRef) < minMinutes) return ''; // 방금 했다 → 두드리지 않는다

  const before = (() => {
    try {
      return git(cwd, ['rev-parse', trackingRef]).trim();
    } catch {
      return '';
    }
  })();

  try {
    // refspec 을 **명시**한다. `git fetch <remote>` 는 `remote.<name>.fetch` 설정을 따르므로,
    // 그 설정이 `+refs/heads/*:refs/heads/*` 같은 형태면 로컬 브랜치 ref 를 움직인다 —
    // "fetch 만 하므로 로컬 불변"이라는 이 훅의 계약이 설정에 따라 거짓이 된다.
    // 우리가 판정에 쓰는 추적 ref 하나만 갱신한다.
    git(
      cwd,
      [
        'fetch', '--quiet', '--no-tags',
        // 사용자의 FETCH_HEAD 를 덮지 않는다. 덮으면 사용자가 방금 `git fetch origin feature` 해 둔
        // 상태에서 이어 친 `git merge FETCH_HEAD` 가 **다른 브랜치를 머지**한다(실측).
        '--no-write-fetch-head',
        // "추적 ref 하나만 갱신한다"는 계약을 지킨다: submodule 재귀도, 자동 유지보수(gc — 그 결과가
        // 브리프 신선도 판정의 폴백인 packed-refs mtime 을 오염시킨다)도 하지 않는다.
        '--no-recurse-submodules', '--no-auto-maintenance',
        remote, `+${remoteRef}:${trackingRef}`,
      ],
      FETCH_MS,
    );
  } catch {
    // 오프라인·인증 실패·원격 없음 → 무음. 다만 **스탬프는 아래에서 실패해도 찍는다**:
    // 안 찍으면 닿지 않는 원격에 매 세션 재시도한다(직전 구현은 FETCH_HEAD 덕에 우연히 backoff 가
    // 있었는데 스탬프로 바꾸며 그 성질이 사라졌다 — 실측 회귀).
    stamp(commonDir, trackingRef);
    return '';
  }
  stamp(commonDir, trackingRef);

  let after = '';
  try {
    after = git(cwd, ['rev-parse', trackingRef]).trim();
  } catch {
    return '';
  }
  if (before === after) return ''; // 움직인 게 없으면 할 말도 없다(추적 ref 가 새로 생긴 경우는 통과)

  if (briefOff) return ''; // fetch 는 했고, 출력만 끈다
  if (!brief || typeof brief.currentRepoLine !== 'function') return '';
  const line = brief.currentRepoLine(cwd, claudeDir, env, new Date());
  // 주: 이 출력은 async 훅이라 첫 턴 뒤에 도달한다(파일 머리 계약).
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
        const backstop = setTimeout(() => process.exit(0), 2000);
        process.stdout.write(out, () => {
          clearTimeout(backstop);
          process.exit(0);
        });
      }
    });
  } catch {
    process.exit(0);
  }
}

module.exports = { run };
