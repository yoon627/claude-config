#!/usr/bin/env node
// SessionStart 브리프 — 세션 시작 시 1줄 리마인더 네 종(해당 시에만, 없으면 무음):
//   K 머지 대기: ~/.claude 의 origin/main 대비 ahead>0 로컬 브랜치(완성-미머지가 조용히 방치되는 것 가시화).
//   L /improve 권장: dlc-signal failure 축 신호가 마커(마지막 /improve) 이후 임계 세션 이상 누적.
//   M 닫히지 않은 plan: in_progress 인데 작업이 끝난 것으로 보이는 plan(§10 "머지 시점에 즉시 done" 누락).
//     K 의 정반대 축 — K 는 "코드는 됐는데 안 머지됨", M 은 "머지는 됐는데 plan 이 안 닫힘".
//   N 자동 pull 밀림: ~/.claude 가 origin/main 보다 뒤처졌을 때 **왜 자동 pull 이 못 따라잡았는지**.
//     pull 훅은 async 라 stdout 이 첫 턴 뒤에 도달 → 시작 시점에 알려면 동기인 이 브리프가 말해야 한다.
// 계약: 판정 아님·표시만(telemetry emit 안 함) · 전부 fail-open(무음 exit 0) · ~/.claude 한정 ·
//   동기 hook(async 면 stdout 이 첫 턴 후 도달) · git stderr 억제 · child git timeout ·
//   신호끼리 예외 격리(한 신호가 죽어도 나머지 라인은 살린다 — stdout write 가 마지막에 1회라서).
'use strict';
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
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

function git(repoDir, args) {
  return execFileSync('git', ['-C', repoDir, ...args], {
    timeout: 2000,
    stdio: ['ignore', 'pipe', 'ignore'], // stderr 억제(sandbox 캐시 경고 등 노이즈 차단)
  }).toString();
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

  const head = `~/.claude ${behind}커밋 뒤처짐`;
  // 아래 분기 순서 = 훅이 pull 을 포기하는 순서. 스스로 낫지 않는 원인을 "재시도하면 되겠지"로
  // 뭉뚱그리면, 이 신호가 없애려던 "조용히 밀리는데 괜찮은 줄 안다"를 문장만 바꿔 재생산한다.
  if (env.CLAUDE_AUTOPULL_OFF === '1') return `${head} — CLAUDE_AUTOPULL_OFF=1 로 자동 pull 을 꺼 둔 상태`;

  const branch = git(repoDir, ['rev-parse', '--abbrev-ref', 'HEAD']).trim();
  if (branch === 'HEAD') return `${head} — detached HEAD 라 자동 pull 이 돌지 않는다`;
  // 훅 체인은 `grep -qx main` 이라 **main 에서만** 돈다 — master 도 skip 대상이다.
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

function main() {
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
  if (lines.length) process.stdout.write(lines.join('\n') + '\n');
}

try {
  main();
} catch {
  /* 어떤 예외도 세션 시작을 막지 않는다(fail-open) */
}
process.exit(0);
