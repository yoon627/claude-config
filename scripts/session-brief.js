#!/usr/bin/env node
// SessionStart 브리프 — 세션 시작 시 1줄 리마인더 두 종(해당 시에만, 없으면 무음):
//   K 머지 대기: ~/.claude 의 origin/main 대비 ahead>0 로컬 브랜치(완성-미머지가 조용히 방치되는 것 가시화).
//   L /improve 권장: dlc-signal failure 축 신호가 마커(마지막 /improve) 이후 임계 세션 이상 누적.
// 계약: 판정 아님·표시만(telemetry emit 안 함) · 전부 fail-open(무음 exit 0) · ~/.claude 한정 ·
//   동기 hook(async 면 stdout 이 첫 턴 후 도달) · git stderr 억제 · child git timeout.
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
const MAX_BRANCHES = 100; // 스캔 상한(동기 hook 지연 방지 — 브랜치당 git 2 spawn)
const MAINLINE = new Set(['main', 'master']);

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

function main() {
  const env = process.env;
  if (env.CLAUDE_SESSION_BRIEF_OFF === '1') return;
  const repoDir = env.CLAUDE_BRIEF_REPO || path.join(os.homedir(), '.claude');
  const lines = [];
  if (env.CLAUDE_BRIEF_MERGE_OFF !== '1') {
    const l = mergePendingLine(repoDir);
    if (l) lines.push(l);
  }
  if (env.CLAUDE_BRIEF_IMPROVE_OFF !== '1') {
    const l = improveNudgeLine(env);
    if (l) lines.push(l);
  }
  if (lines.length) process.stdout.write(lines.join('\n') + '\n');
}

try {
  main();
} catch {
  /* 어떤 예외도 세션 시작을 막지 않는다(fail-open) */
}
process.exit(0);
