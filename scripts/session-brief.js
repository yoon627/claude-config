#!/usr/bin/env node
// SessionStart 브리프 — 세션 시작 시 1줄 리마인더 네 종(해당 시에만, 없으면 무음):
//   K 머지 대기: ~/.claude 의 origin/main 대비 ahead>0 로컬 브랜치(완성-미머지가 조용히 방치되는 것 가시화).
//   L /improve 권장: dlc-signal failure 축 신호가 마커(마지막 /improve) 이후 임계 세션 이상 누적.
//   M 닫히지 않은 plan: in_progress 인데 작업이 끝난 것으로 보이는 plan(§10 "머지 시점에 즉시 done" 누락).
//     K 의 정반대 축 — K 는 "코드는 됐는데 안 머지됨", M 은 "머지는 됐는데 plan 이 안 닫힘".
//   N 자동 pull 밀림: ~/.claude 가 origin/main 보다 뒤처졌을 때 **왜 자동 pull 이 못 따라잡았는지**.
//     pull 훅은 async 라 stdout 이 첫 턴 뒤에 도달 → 시작 시점에 알려면 동기인 이 브리프가 말해야 한다.
//   O 세션 repo 밀림: **지금 작업 중인 repo**(hook stdin 의 cwd)가 upstream 보다 뒤처졌거나 미커밋이
//     오래 방치됐을 때. N 과 나누는 이유는 처방이 다르기 때문 — ~/.claude 는 자동 pull 훅이 있어
//     "훅이 왜 못 따라잡았나"가 답이고, 다른 repo 는 훅이 없으니 "직접 pull 해야 한다"가 답이다.
// 계약: 판정 아님·표시만(telemetry emit 안 함) · 전부 fail-open(무음 exit 0) ·
//   동기 hook(async 면 stdout 이 첫 턴 후 도달) · git stderr 억제 · child git timeout ·
//   신호끼리 예외 격리(한 신호가 죽어도 나머지 라인은 살린다 — stdout write 가 마지막에 1회라서).
'use strict';
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
let readHookCwd;
try {
  ({ readHookCwd } = require('./hook-cwd.js'));
} catch {
  readHookCwd = (cb) => cb(process.cwd()); // 모듈 부재 → 폴백(브리프가 죽는 것보다 낫다)
}
let signal = null;
try {
  signal = require('./dlc-signal.js');
} catch {
  /* dlc-signal 부재/손상 → L 비활성(K 는 계속), 세션 시작 안 막음 */
}

const MERGE_CAP = 5;
const LIST_CAP = 5; // N 신호의 충돌 파일 나열 상한
const MAX_BRANCHES = 100; // 스캔 상한(동기 hook 지연 방지 — 브랜치당 git 2 spawn)
const MAINLINE = new Set(['main', 'master']);
const STALE_CAP = 5;
const MAX_PLANS = 200; // plans/ 는 done 도 계속 누적 → MAX_BRANCHES 와 대칭으로 상한
const FM_BYTES = 2048; // frontmatter 는 파일 맨 앞 몇 줄 → 전문 대신 head 만 read
// `git rev-parse --local-env-vars` 가 열거하는 repo-routing 환경변수. 하나라도 남으면 `-C` 가 진다.
const GIT_LOCAL_ENV = [
  'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_CONFIG', 'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT',
  'GIT_OBJECT_DIRECTORY', 'GIT_DIR', 'GIT_WORK_TREE', 'GIT_IMPLICIT_WORK_TREE', 'GIT_GRAFT_FILE',
  'GIT_INDEX_FILE', 'GIT_NO_REPLACE_OBJECTS', 'GIT_REPLACE_REF_BASE', 'GIT_PREFIX',
  'GIT_INTERNAL_SUPER_PREFIX', 'GIT_SHALLOW_FILE', 'GIT_COMMON_DIR',
];
const CWD_BUDGET_MS = 2000; // O 신호 전체 시간 상한(동기 hook — settings 의 timeout 10s 를 혼자 먹지 않게)
// stat 상한. "가장 오래된 것"을 찾는 게 목적이라 너무 낮으면 어질러진 repo 일수록 검출이 죽는다
// (사전순 앞 20개만 보면 21번째가 제일 오래돼도 못 찾는다). statSync 는 싸고, 진짜 상한은 예산이다.
const CWD_STAT_CAP = 200;
const STDIN_MS = 1000; // hook stdin 대기 상한. 형제 훅(dlc-early-stop.js)과 같은 값

function git(repoDir, args) {
  // 상속된 GIT_* 는 `-C` 를 이긴다 — GIT_DIR 이 남아 있는 셸에서 세션이 열리면 stdin 이 지목한 repo 가
  // 아니라 그쪽 repo 를 답한다(실측). 3개만 지우면 `GIT_COMMON_DIR` 로 그대로 새어나간다(이것도 실측) →
  // repo 를 가리키는 변수 전체를 지운다. 목록 출처: `git rev-parse --local-env-vars`(git 2.50).
  const env = { ...process.env };
  for (const k of GIT_LOCAL_ENV) delete env[k];
  return execFileSync(
    'git',
    // `core.fsmonitor` 는 repo 설정에 적힌 **명령을 실행**한다. 이 훅은 사용자가 아무 git 명령도 치기
    // 전에 임의 cwd 에서 자동으로 도니, 남의 repo 안에서 세션을 열었다는 이유만으로 그 repo 의 명령이
    // 실행돼선 안 된다(실측으로 실행되는 것을 확인했다). 빈 값으로 무력화한다.
    ['-c', 'core.fsmonitor=', '-C', repoDir, ...args],
    {
      timeout: 2000,
      // 기본 maxBuffer(1MiB)를 넘으면 ENOBUFS 로 **신호가 통째로 사라진다**. 조용히 사라지는 것이
      // 가장 나쁜 실패라, 목록이 큰 repo 에서도 판정이 살아 있도록 넉넉히 잡는다.
      maxBuffer: 16 * 1024 * 1024,
      stdio: ['ignore', 'pipe', 'ignore'], // stderr 억제(sandbox 캐시 경고 등 노이즈 차단)
      env,
    },
  ).toString();
}

// K: origin/main 대비 ahead 인 로컬 브랜치 목록 라인(없으면 null). fetch 안 함(cached origin/main).
function mergePendingLine(repoDir) {
  try {
    git(repoDir, ['rev-parse', '--verify', '--quiet', 'refs/remotes/origin/main']);
  } catch {
    return null; // origin/main 없음·비 git → 무음
  }
  let refs;
  try {
    refs = git(repoDir, ['for-each-ref', '--format=%(refname:short)', 'refs/heads']) // '*'/'+' 마커·worktree 중복 없음
      .split('\n')
      .filter(Boolean);
  } catch {
    return null;
  }
  const ahead = [];
  for (const b of refs.slice(0, MAX_BRANCHES)) {
    if (MAINLINE.has(b)) continue; // 머지 대상(main/master) 자체는 "미머지" 아님 → 제외
    let count;
    try {
      count = parseInt(git(repoDir, ['rev-list', '--count', `origin/main..${b}`]).trim(), 10);
    } catch {
      continue;
    }
    if (!count || count <= 0) continue;
    let ct = 0;
    try {
      ct = parseInt(git(repoDir, ['log', '-1', '--format=%ct', b]).trim(), 10) || 0;
    } catch {
      /* 커밋 시각 조회 실패 → 정렬 최상단(0) */
    }
    ahead.push({ b, count, ct });
  }
  if (!ahead.length) return null;
  ahead.sort((a, z) => a.ct - z.ct); // 오래된 커밋(가장 방치된 것) 먼저
  const shown = ahead.slice(0, MERGE_CAP).map((x) => `${x.b}(+${x.count})`);
  const more = ahead.length > MERGE_CAP ? ` +${ahead.length - MERGE_CAP}` : '';
  return `머지 대기(미머지 로컬): ${shown.join(', ')}${more}`;
}

// L: 마커 이후 failure 축 unique 세션 수가 임계 이상이면 nudge 라인(아니면 null).
// summarize 는 per-kind 집계라 cross-kind 세션 중복 집계됨 → raw jsonl 직접 파싱(+회전분).
function improveNudgeLine(env) {
  if (!signal) return null; // dlc-signal 로드 실패 → L skip
  const min = Math.max(1, Number(env.CLAUDE_BRIEF_IMPROVE_MIN) || 5);
  const dir = signal.signalDir(env);
  let since = 0;
  try {
    since = fs.statSync(path.join(dir, 'last-improve')).mtimeMs;
  } catch {
    since = 0; // 마커 없음 → 전체 누적
  }
  const sessions = new Set();
  for (const f of ['dlc-signals.jsonl.1', 'dlc-signals.jsonl']) {
    // 회전분(.1)이 과거라 먼저 — 마커가 회전 이전이면 undercount 방지
    let text;
    try {
      text = fs.readFileSync(path.join(dir, f), 'utf8');
    } catch {
      continue;
    }
    for (const ln of text.split('\n')) {
      if (!ln) continue;
      let r;
      try {
        r = JSON.parse(ln);
      } catch {
        continue;
      }
      if (!r || signal.KINDS[r.kind] !== 'failure') continue;
      if (typeof r.session_id !== 'string' || !r.session_id) continue; // 문자열 세션만(객체·null 오집계 방지)
      const t = r.ts ? Date.parse(r.ts) : NaN;
      if (!Number.isFinite(t)) continue; // ts 항상 유효 요구(불량·부재 행 제외 — emit 은 항상 ts 기록)
      if (since && t <= since) continue; // 마커 이후만
      sessions.add(r.session_id);
    }
  }
  if (sessions.size < min) return null;
  return `/improve 권장 — failure 신호 ${sessions.size}세션 누적 (마커 이후)`;
}

// frontmatter 는 파일 맨 앞이라 head 만 읽는다. `* text=auto`(.gitattributes) 때문에 플랫폼별로
// CRLF 로 체크아웃되므로 개행·BOM 을 정규화한다 — plan-lint.js 파서와 같은 전처리.
function readHead(file, bytes) {
  const fd = fs.openSync(file, 'r');
  try {
    const buf = Buffer.alloc(bytes);
    const n = fs.readSync(fd, buf, 0, bytes, 0);
    return buf.subarray(0, n).toString('utf8').replace(/^﻿/, '').replace(/\r\n/g, '\n');
  } finally {
    fs.closeSync(fd);
  }
}

// frontmatter(`---` 블록) 안에서만 key 값을 뽑는다 — 본문의 같은 이름 라인에 오염되지 않게.
// YAML 인라인 주석은 값이 아니다: §10 정본 템플릿이 `status: in_progress  # in_progress | ...` 형태다.
function frontmatterValue(head, key) {
  const block = head.match(/^---\n([\s\S]*?)\n---/);
  if (!block) return null;
  const hit = block[1].match(new RegExp(`^${key}:[ \\t]*(.+)$`, 'm'));
  return hit ? hit[1].replace(/\s+#.*$/, '').trim() : null;
}

// 달력 일수 차. `updated` 는 날짜만이라 시각 성분을 섞으면 오전에 음수가 되고, 로컬 자정 간
// ms 차분은 DST 전환(23시간 하루)에서 하루 작아진다 → 양쪽을 UTC 자정으로 옮겨 차분한다.
function daysSinceLocal(dateStr, now) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateStr);
  if (!m) return null;
  const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
  const then = new Date(Date.UTC(y, mo - 1, d));
  if (then.getUTCMonth() + 1 !== mo || then.getUTCDate() !== d) return null; // 2026-02-31 같은 롤오버 거부
  const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  const diff = Math.floor((today - then.getTime()) / 86400000);
  return diff < 0 ? 0 : diff; // 미래 날짜는 0 으로 클램프
}

// slug ↔ 브랜치 앵커 매칭. free substring 은 쓰지 않는다 — 항상 존재하는 `main` 이
// slug 에 main 이 든 plan(main-autopull 등)을 영구 억제하고, 무관 브랜치가 우연 매칭된다.
function anchorMatches(branch, slug) {
  if (!slug) return false;
  return branch === slug || branch === `worktree-${slug}` || branch.endsWith(`-${slug}`);
}

// M: in_progress 인데 작업이 끝난 것으로 보이는 plan 목록 라인(없으면 null).
// "끝난 것으로 보임" = 매칭 브랜치가 없음 OR 있어도 origin/main 대비 ahead 0(이미 머지됨).
function stalePlanLine(repoDir, env, now) {
  const rawDays = Number(env.CLAUDE_BRIEF_STALE_DAYS);
  const minDays = Number.isFinite(rawDays) && rawDays >= 1 ? Math.floor(rawDays) : 3;
  const plansDir = path.join(repoDir, 'plans');
  let entries;
  try {
    entries = fs.readdirSync(plansDir, { withFileTypes: true });
  } catch {
    return null; // plans/ 부재·비 git → 무음
  }
  let hasOriginMain = true;
  try {
    git(repoDir, ['rev-parse', '--verify', '--quiet', 'refs/remotes/origin/main']);
  } catch {
    hasOriginMain = false; // ahead 판정 불가 → "브랜치 있으면 제외"로 보수 동작
  }
  const branches = []; // rev-list 에 그대로 쓸 수 있는 ref 이름(로컬 short / origin/<name>)
  for (const ns of ['refs/heads', 'refs/remotes/origin']) {
    let out;
    try {
      out = git(repoDir, ['for-each-ref', '--format=%(refname:short)', ns]);
    } catch {
      continue;
    }
    for (const ref of out.split('\n').filter(Boolean).slice(0, MAX_BRANCHES)) {
      const name = ref.startsWith('origin/') ? ref.slice(7) : ref;
      // mainline 제외는 K 와 같은 이유(§ anchorMatches 주석). `origin` 은 refs/remotes/origin/HEAD 의
      // short 표기라 브랜치가 아니다.
      if (MAINLINE.has(name) || name === 'origin') continue;
      branches.push({ ref, name });
    }
  }
  const mergedCache = new Map();
  const isMerged = (ref) => {
    if (mergedCache.has(ref)) return mergedCache.get(ref);
    let merged = false;
    try {
      merged = parseInt(git(repoDir, ['rev-list', '--count', `origin/main..${ref}`]).trim(), 10) === 0;
    } catch {
      merged = false; // 판정 실패 → 미머지 취급(오탐보다 침묵)
    }
    mergedCache.set(ref, merged);
    return merged;
  };

  const stale = [];
  // plans/ 루트의 stray 파일(ENOTDIR)을 먼저 걸러낸 뒤 cap 을 적용한다 — 순서가 반대면 오래된 done
  // 디렉토리와 stray 파일이 예산을 소진해 최신 in_progress plan 이 스캔 밖으로 밀린다(readdir 오름차순).
  const dirs = entries.filter((e) => e.isDirectory()).slice(-MAX_PLANS);
  for (const e of dirs) {
    const dir = path.join(plansDir, e.name);
    let files;
    try {
      files = fs.readdirSync(dir);
    } catch {
      continue;
    }
    for (const f of files) {
      if (!f.endsWith('-plan.md')) continue;
      try {
        const slug = f.slice(0, -'-plan.md'.length);
        const head = readHead(path.join(dir, f), FM_BYTES);
        if (frontmatterValue(head, 'status') !== 'in_progress') continue; // blocked 는 의도적 정지라 제외
        // updated 가 불량·부재면 started 로 폴백한다 — frontmatter 관리가 끊긴 plan 이야말로
        // 가장 오래 방치된 쪽이라, 파싱 실패를 skip 으로 처리하면 목표와 정반대가 된다.
        const days =
          daysSinceLocal(frontmatterValue(head, 'updated') || '', now) ??
          daysSinceLocal(frontmatterValue(head, 'started') || '', now);
        if (days === null || days < minDays) continue;
        const matched = branches.filter((b) => anchorMatches(b.name, slug));
        if (matched.length && (!hasOriginMain || matched.some((b) => !isMerged(b.ref)))) continue; // 진행 중
        stale.push({ slug, days });
      } catch {
        continue; // 불량 plan 1건이 같은 디렉토리의 나머지 파일 평가를 막지 않는다
      }
    }
  }
  if (!stale.length) return null;
  stale.sort((a, z) => z.days - a.days); // 오래 방치된 것 먼저
  const shown = stale.slice(0, STALE_CAP).map((x) => `${x.slug}(${x.days}d)`);
  const more = stale.length > STALE_CAP ? ` +${stale.length - STALE_CAP}` : '';
  return `닫히지 않은 plan: ${shown.join(', ')}${more}`;
}

// N: ~/.claude 가 origin/main 보다 뒤처졌을 때 **왜 자동 pull 이 못 따라잡았는지** 한 줄.
// SessionStart 의 pull 훅은 async 라 그 stdout 이 첫 턴 뒤에야 도달한다 → 사용자가 세션 시작에
// 보려면 동기인 이 브리프가 말해야 한다. 네트워크는 쓰지 않는다(캐시된 origin/main 으로 판정).
// 판정이 성립하는 근거: `git pull` 은 fetch 를 먼저 하고 merge 만 거부하므로, pull 이 로컬 변경과
// 충돌해 실패해도 origin/main ref 는 갱신된다(실측 확인).
// 파일명은 `-z`(NUL 구분)로 받는다. 기본 core.quotePath 는 비ASCII 를 `"\355\225\234…"` 로
// 이스케이프해 표시가 깨지고, quotePath=false 만 끄면 개행 포함 경로가 줄 분리를 깨뜨린다.
function gitPaths(repoDir, args) {
  return git(repoDir, [...args, '-z']).split('\0').filter(Boolean);
}

function autopullStalledLine(repoDir, env) {
  let behind;
  try {
    behind = Number(git(repoDir, ['rev-list', '--count', 'HEAD..refs/remotes/origin/main']).trim());
  } catch {
    return null; // origin/main 없음·비 git → 판정 불가라 무음
  }
  if (!behind) return null; // 최신 = 정상 무음(매 세션 잡음 금지)

  // 라벨은 감시 대상에서 유도한다. 하드코딩하면 CLAUDE_BRIEF_REPO 로 다른 repo 를 겨눴을 때
  // "~/.claude 가 뒤처졌다"고 거짓 보고한다(실측으로 확인한 뒤 고쳤다).
  const label = samePath(repoDir, path.join(os.homedir(), '.claude')) ? '~/.claude' : path.basename(repoDir) || repoDir;
  const head = `${label} ${behind}커밋 뒤처짐`;
  // 아래 분기 순서 = 훅이 pull 을 포기하는 순서. 스스로 낫지 않는 원인을 "재시도하면 되겠지"로
  // 뭉뚱그리면, 이 신호가 없애려던 "조용히 밀리는데 괜찮은 줄 안다"를 문장만 바꿔 재생산한다.
  if (env.CLAUDE_AUTOPULL_OFF === '1') return `${head} — CLAUDE_AUTOPULL_OFF=1 로 자동 pull 을 꺼 둔 상태`;
  if (fs.existsSync(path.join(repoDir, '.autopull-off'))) {
    return `${head} — .autopull-off 파일로 자동 pull 을 꺼 둔 상태`;
  }

  const branch = git(repoDir, ['rev-parse', '--abbrev-ref', 'HEAD']).trim();
  if (branch === 'HEAD') return `${head} — detached HEAD 라 자동 pull 이 돌지 않는다`;
  // 훅 스크립트는 브랜치가 `main` 과 정확히 일치할 때만 돈다 — master 도 skip 대상이다.
  if (branch !== 'main') return `${head} — 브랜치가 ${branch} 라 자동 pull 이 돌지 않는다(훅은 main 에서만)`;

  const gitDir = git(repoDir, ['rev-parse', '--absolute-git-dir']).trim();
  const busy = ['rebase-merge', 'rebase-apply', 'MERGE_HEAD', 'BISECT_LOG'].find((n) =>
    fs.existsSync(`${gitDir}/${n}`),
  );
  if (busy) return `${head} — ${busy} 진행 중이라 자동 pull 이 skip 된다(끝내면 풀린다)`;

  // ahead>0 이면 갈라진 것이라 --ff-only 는 영원히 실패한다 — 재시도로는 안 풀린다.
  const ahead = Number(git(repoDir, ['rev-list', '--count', 'refs/remotes/origin/main..HEAD']).trim());
  if (ahead) {
    return `${head}·로컬 ${ahead}커밋 앞섬 — 갈라져서 ff-only pull 이 불가능하다(rebase 나 push 필요)`;
  }

  // 원격이 바꾼 파일을 로컬에서도 건드렸으면 ff 가 거부된다 — 그 파일이 곧 원인이다.
  // untracked 도 포함해야 한다: 원격이 *새로 추가*하는 파일과 이름이 겹치면 git 이
  // "Please move or remove them before you merge" 로 거부하는데, 이건 diff 에 안 잡힌다.
  const dirty = new Set([
    ...gitPaths(repoDir, ['diff', '--name-only']),
    ...gitPaths(repoDir, ['diff', '--cached', '--name-only']),
    ...gitPaths(repoDir, ['ls-files', '--others', '--exclude-standard']),
  ]);
  const blocking = gitPaths(repoDir, [
    'diff',
    '--name-only',
    'HEAD..refs/remotes/origin/main',
  ]).filter((f) => dirty.has(f));
  if (blocking.length) {
    const shown = blocking.slice(0, LIST_CAP).join(', ');
    const more = blocking.length > LIST_CAP ? ` +${blocking.length - LIST_CAP}` : '';
    return `${head} — 로컬 변경과 충돌해 pull 거부됨: ${shown}${more} (커밋하거나 되돌리면 풀린다)`;
  }
  // 여기까지 왔으면 로컬에 막는 요인이 없다 — 원인을 단정하지 않는다.
  return `${head} — 원인 미확인(마지막 pull 이 실패했거나 아직 안 돌았다)`;
}

// 경로 동일성. Windows 는 대소문자를 구분하지 않으므로 비교 전에 접는다.
function samePath(a, b) {
  const norm = (x) => {
    let r = path.resolve(x);
    // macOS 의 /var → /private/var, Windows 의 8.3 단축명·junction 처럼 같은 경로가 다른 문자열로
    // 오는 경우가 있다. 존재하지 않는 경로는 realpath 가 던지므로 resolve 결과로 둔다.
    try {
      r = fs.realpathSync.native(r);
    } catch {
      /* 없는 경로 → 문자열 비교로 */
    }
    return process.platform === 'win32' ? r.toLowerCase() : r;
  };
  return norm(a) === norm(b);
}

// mtime → `daysSinceLocal` 이 받는 로컬 달력 날짜 문자열. M 신호와 같은 시간 축을 쓴다.
function localDateString(ms) {
  const d = new Date(ms);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

// 추적 ref 하나에 대한 fetch 스탬프 파일명. 브리프와 fetch 훅이 **같은 함수**로 키를 만든다 —
// 키가 갈라지면 한쪽은 못 찾고 다른 쪽은 굶는다(그 실패는 조용해서 더 나쁘다).
function fetchStampName(fullRef) {
  return `claude-fetch-${fullRef.replace(/[^\w.-]/g, '_')}`;
}

// remote-tracking ref 가 마지막으로 갱신된 시각(ms). 없으면 null — **모르면 아무 말도 하지 않는다**.
// "한 번도 갱신 안 함"을 "오래됐다"로 단정하면 갓 clone 한 repo 에 거짓 경고를 낸다 → 근거가 없으면
// 아무 말도 하지 않는다(null). ref 파일·packed-refs 는 clone 시각에 만들어지므로, 새 clone 은 신선하고
// 오래 방치된 clone 은 오래된 것으로 잡힌다. 단 `packed-refs` 는 `git gc` 로도 다시 쓰이므로 오래
// 방치된 repo 를 신선한 것처럼 보이게 할 수 있다 — **경고를 없애는 쪽으로만 틀리는** 폴백이라 두었다
// (거짓 경고보다 낫다). fetch 훅이 도는 repo 는 매번 스탬프를 남기므로 이 폴백까지 오지 않는다.
function lastRefreshMs(commonDir, fullRef) {
  // 1순위는 session-fetch 훅이 남기는 **추적 ref 단위** 스탬프. `FETCH_HEAD` 는 쓰지 않는다 — repo
  // 전역이라 다른 remote·브랜치를 fetch 해도 갱신돼 이쪽이 신선한 것처럼 보인다(그 오판이 곧 침묵이다).
  // remote 단위 스탬프도 같은 이유로 안 된다: `main` 세션이 찍은 스탬프가 `feat` 세션의 판정을 덮는다.
  for (const rel of [fetchStampName(fullRef), fullRef, 'packed-refs']) {
    try {
      return fs.statSync(path.join(commonDir, rel)).mtimeMs;
    } catch {
      /* 다음 후보 */
    }
  }
  return null;
}

// O: 세션이 작업 중인 repo 가 upstream 보다 뒤처졌거나, 미커밋이 오래 방치됐으면 한 줄(없으면 null).
// N 과 달리 이쪽에는 자동 pull 훅이 없다 — 원인을 묻는 게 아니라 사람이 직접 당겨야 한다고 말한다.
// **한계**: N 과 마찬가지로 네트워크를 쓰지 않고 캐시된 remote-tracking ref 로만 판정한다. 그런데 이
// repo 에는 그 ref 를 갱신해 줄 자동 fetch 주체가 없다(N 은 SessionStart pull 훅이 갱신해 준다) —
// 한 번도 fetch 하지 않은 채 밀린 구간은 무음이다. 미커밋 파트는 원격과 무관해 그 구멍이 없다.
// 동기 hook 이라 시간 상한을 들고 다닌다: fail-open 은 예외 정책이지 시간 정책이 아니다.
function currentRepoLine(cwd, repoDir, env, now) {
  if (!cwd) return null;
  const deadline = Date.now() + CWD_BUDGET_MS;
  const spent = () => Date.now() > deadline;

  let top;
  let commonDir;
  try {
    // 한 번의 spawn 으로 둘 다 받는다. --git-common-dir 은 cwd 상대일 수 있어 resolve 한다.
    const out = git(cwd, ['rev-parse', '--show-toplevel', '--git-common-dir']).split('\n');
    top = (out[0] || '').trim();
    commonDir = path.resolve(cwd, (out[1] || '').trim());
  } catch {
    return null; // 비 git·경로 없음·git 실패 → 무음
  }
  if (!top) return null;

  const parts = [];

  // 기준 ref 는 **`@{upstream}` 뿐**이다. origin/HEAD·origin/main 으로 폴백하지 않는다 —
  // 이 워크플로우는 feature 브랜치를 push 하지 않는 것이 규약이라(글로벌 §8) upstream 없음이 정상이고,
  // 폴백을 두면 "main 에서 갈라진 지 오래됨"이라는 조치 불가능한 사실을 매 세션 낸다(실측: 한 repo 의
  // worktree 68개 중 60개가 그렇게 걸렸다). 그 잡음은 K 를 확장하지 않기로 한 이유와 같은 것이다.
  let ref = null; // 표시용 짧은 이름
  let fullRef = null; // 스탬프 키·rev-list 용 정식 이름
  try {
    fullRef = git(cwd, ['rev-parse', '--symbolic-full-name', '@{upstream}']).trim() || null;
    // `refs/remotes/origin/main` → `origin/main`. 로컬 브랜치가 upstream 이면(`branch.X.remote=.`)
    // 그 접두가 없으므로 정식 이름을 그대로 보여준다 — 문자열을 쪼개 추측하지 않는다.
    ref = fullRef && fullRef.startsWith('refs/remotes/') ? fullRef.slice('refs/remotes/'.length) : fullRef;
  } catch {
    ref = null; // upstream 미설정 → 밀림은 판정하지 않는다(무엇 대비인지 모르는 숫자는 만들지 않는다)
  }
  if (ref && !spent()) {
    try {
      const [behind, ahead] = git(cwd, ['rev-list', '--left-right', '--count', `${fullRef}...HEAD`])
        .trim()
        .split(/\s+/)
        .map((x) => parseInt(x, 10));
      if (Number.isFinite(behind) && behind > 0) {
        // 기준 ref 를 문장에 넣는다 — "무엇 대비"가 빠지면 사용자가 확인할 수 없다.
        const fact = `${ref} 대비 ${behind}커밋 뒤처짐`;
        parts.push(
          ahead > 0
            ? `${fact}·로컬 ${ahead}커밋 앞섬 — 갈라져서 ff-only pull 이 불가능하다(rebase 나 push 필요)`
            : `${fact} — 이 repo 에는 자동 pull 이 없다(직접 pull 해야 한다)`,
        );
      }
    } catch {
      /* 판정 실패 → 밀림 파트만 포기 */
    }
  }

  // 오래 방치된 미커밋. 편집 중인 파일로 매 세션 울리지 않도록 임계를 둔다.
  const rawDays = Number(env.CLAUDE_BRIEF_DIRTY_DAYS);
  const minDays = Number.isFinite(rawDays) && rawDays >= 1 ? Math.floor(rawDays) : 3;
  if (!spent()) {
    try {
      // --no-optional-locks: 배경 도구가 사용자의 활성 repo 에서 index.lock 을 잡지 않게 한다
      //   (이 helper 는 2s 후 SIGTERM 이라, 잡은 채 강제 종료되면 lock 잔재가 남는다).
      // -unormal 을 **명시**한다: `status.showUntrackedFiles` 설정에 판정이 흔들리지 않게 하고,
      //   `-uall` 은 쓰지 않는다 — untracked 트리를 파일 단위로 펼치면 gitignore 안 된 `venv/`·
      //   `node_modules/` 하나가 매 세션 같은 줄을 만들고(조치 불가능한 잡음), 목록이 크면 출력이
      //   버퍼를 넘겨 신호 자체가 사라진다(실측 24k 파일 ENOBUFS).
      // --no-renames: -z 의 rename 항목은 경로가 2개라 파서가 어긋난다. 나이만 볼 것이라 원경로면 충분.
      const entries = gitPaths(cwd, ['--no-optional-locks', 'status', '--porcelain', '-unormal', '--no-renames']);
      let oldest = null;
      const names = [];
      let seen = 0;
      for (const e of entries) {
        if (seen++ >= CWD_STAT_CAP || spent()) break; // 예산이 진짜 상한이다
        const rel = e.slice(3); // `XY <path>`
        if (!rel) continue;
        // 접힌 untracked 디렉토리(`?? dir/`)는 건너뛴다. 디렉토리 mtime 은 안쪽 파일 편집으로 바뀌지
        // 않아 나이가 거짓이 된다 — 없는 사실을 만드느니 이 경우만 못 보는 편이 낫다(알려진 사각).
        if (rel.endsWith('/')) continue;
        let st;
        try {
          st = fs.statSync(path.join(top, rel));
        } catch {
          continue; // 삭제된 파일 등 stat 불가 → 나이를 알 수 없다(알려진 사각)
        }
        const days = daysSinceLocal(localDateString(st.mtimeMs), now);
        if (days === null || days < minDays) continue;
        if (oldest === null || days > oldest) oldest = days;
        names.push(rel);
      }
      if (oldest !== null && names.length) {
        const shown = names.slice(0, LIST_CAP).join(', ');
        const more = names.length > LIST_CAP ? ` +${names.length - LIST_CAP}` : '';
        parts.push(`미커밋 ${oldest}일: ${shown}${more}`);
      }
    } catch {
      /* status 실패 → 미커밋 파트만 포기 */
    }
  }

  // (b) 밀림이 0 으로 보인다면, 그 0 이 **언제 기준인지**가 중요하다. 이 repo 의 remote-tracking ref 를
  // 갱신하는 자동 주체는 session-fetch 훅뿐이고, 그것이 실패하는 상황(오프라인·인증·원격 불가)은 남는다.
  // 그때 침묵하면 "밀리지 않았다"로 읽힌다 — 모르는 것은 모른다고 말한다.
  // 밀림 파트가 이미 있으면 내지 않는다(할 말을 이미 했다).
  if (ref && !parts.length && !spent()) {
    const rawFetch = Number(env.CLAUDE_BRIEF_FETCH_DAYS);
    const fetchDays = Number.isFinite(rawFetch) && rawFetch >= 1 ? Math.floor(rawFetch) : 3;
    const at = lastRefreshMs(commonDir, fullRef);
    const stale = at === null ? null : daysSinceLocal(localDateString(at), now);
    if (stale !== null && stale >= fetchDays) {
      parts.push(`${stale}일째 fetch 하지 않았다 — ${ref} 대비 밀렸는지 알 수 없다`);
    }
  }

  if (!parts.length) return null; // 동기화 + clean = 정상 무음
  // 감시 repo(N) 자신이면 O 는 침묵한다. 확인을 **낼 것이 있을 때만** 한다 — 무음이 대부분이라
  // 여기 두면 추가 spawn 이 그만큼 드물게 든다. `<repoDir>/.git` 문자열 비교로 먼저 거르고,
  // 어긋날 때만(worktree·submodule·gitfile·symlink) repoDir 쪽 common dir 을 실제로 물어본다.
  if (samePath(commonDir, path.join(repoDir, '.git'))) return null;
  if (spent()) return null; // 예산을 넘겼으면 확인 없이 조용히 — 중복 출력보다 무음이 안전하다
  try {
    const otherCommon = git(repoDir, ['rev-parse', '--git-common-dir']).trim();
    if (samePath(commonDir, path.resolve(repoDir, otherCommon))) return null;
  } catch {
    /* repoDir 이 비 git → 비교 불가, O 를 막지 않는다 */
  }

  // 라벨: worktree 이름만으로는 어느 repo 인지 모른다. 다르면 `<repo>/<worktree>` 로 둘 다 보여준다.
  const worktreeName = path.basename(top) || top;
  const repoName = path.basename(path.dirname(commonDir)) || worktreeName;
  const label = repoName === worktreeName ? worktreeName : `${repoName}/${worktreeName}`;
  return `${label} ${parts.join(' · ')}`;
}

function main(cwd) {
  const env = process.env;
  if (env.CLAUDE_SESSION_BRIEF_OFF === '1') return;
  const repoDir = env.CLAUDE_BRIEF_REPO || path.join(os.homedir(), '.claude');
  const lines = [];
  // 신호별 try — stdout write 가 마지막 1회라, 격리 없으면 한 신호의 예외가 이미 계산된 라인까지 삼킨다.
  const collect = (off, fn) => {
    if (env[off] === '1') return;
    try {
      const l = fn();
      if (l) lines.push(l);
    } catch {
      /* 이 신호만 포기, 나머지는 계속 */
    }
  };
  collect('CLAUDE_BRIEF_MERGE_OFF', () => mergePendingLine(repoDir));
  collect('CLAUDE_BRIEF_IMPROVE_OFF', () => improveNudgeLine(env));
  collect('CLAUDE_BRIEF_STALE_OFF', () => stalePlanLine(repoDir, env, new Date()));
  collect('CLAUDE_BRIEF_AUTOPULL_OFF', () => autopullStalledLine(repoDir, env));
  collect('CLAUDE_BRIEF_CWD_OFF', () => currentRepoLine(cwd, repoDir, env, new Date()));
  return lines.length ? lines.join('\n') + '\n' : '';
}

if (require.main === module) {
  try {
    // kill switch 는 stdin 을 기다리기 **전에** 본다. 뒤에 두면 꺼 둔 기능이 stdin 대기만큼
    // (최대 STDIN_MS) 세션 시작을 잡는다 — 껐는데 비용을 무는 모양은 계약과 어긋난다.
    if (process.env.CLAUDE_SESSION_BRIEF_OFF === '1') {
      process.exit(0);
    } else {
      readHookCwd((cwd) => {
        let out = '';
        try {
          out = main(cwd) || '';
        } catch {
          /* 어떤 예외도 세션 시작을 막지 않는다(fail-open) */
        }
        // write 는 파이프에서 비동기로 끝날 수 있다. 곧바로 exit 하면 브리프가 잘린 채 도착한다.
        if (!out) {
          process.exit(0);
        } else {
          const backstop = setTimeout(() => process.exit(0), 2000); // 콜백이 안 와도 세션을 잡지 않는다
          process.stdout.write(out, () => {
            clearTimeout(backstop);
            process.exit(0);
          });
        }
      });
    }
  } catch {
    process.exit(0);
  }
}

// session-fetch 훅이 fetch 직후 같은 문장을 내기 위해 가져다 쓴다 — 두 곳에서 만들면 갈라진다.
module.exports = { currentRepoLine, samePath, fetchStampName, GIT_LOCAL_ENV };
