#!/usr/bin/env node
// dlc 신호 기록 — 자기개선 loop 의 수집 축(hook 아님, hook 들이 require).
// `~/.claude/telemetry/dlc-signals.jsonl` 에 append-only JSONL 로 누적, /improve 가 소비.
// emit 은 fail-open: 실패해도 throw 하지 않아 hook 본연 동작(경고·차단)을 막지 않는다.
// env 채널(spawn 방식 hook 테스트는 함수 파라미터 주입이 불가해 env 로 격리):
//   CLAUDE_DLC_SIGNAL_DIR   기록 디렉토리 override
//   CLAUDE_DLC_SIGNAL_OFF=1 emit 무력화
//   CLAUDE_DLC_SIGNAL_MAX_BYTES 회전 임계(기본 5MB — 초과 시 .1 단일 회전, best-effort)
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

// kind → axis 단일 소스. failure = 개선 효과 측정 대상, activity = 작업 유형·리뷰 활동량(실패 아님).
const KINDS = {
  'early-stop-verify': 'failure',
  'doc-drift-readme': 'failure',
  'doc-drift-index': 'failure',
  'guard-worktree-deny': 'failure',
  'plan-blocked': 'failure',
  'router-investigation': 'activity',
  'router-grounding': 'activity',
  'review-disposition': 'activity',
};

const DEFAULT_MAX_BYTES = 5 * 1024 * 1024;

// ---- 순수 판정 (파일 무접촉) ----

// 홈 prefix 를 ~ 로 축약 — 글로벌 telemetry 에 환경 식별자(username 경로) 축적 최소화.
function tildeify(p, home) {
  const norm = String(p || '').replace(/\\/g, '/');
  const h = String(home == null ? os.homedir() : home)
    .replace(/\\/g, '/')
    .replace(/\/+$/, '');
  if (h && (norm === h || norm.startsWith(h + '/'))) return '~' + norm.slice(h.length);
  return norm;
}

// 문자열 존재가 아니라 상태 전이만 신호로 친다 — plan 파일 자신이 `status: blocked` 예시
// 문자열이나 `# Review Disposition` 템플릿 헤더를 문서로 포함하기 때문(substring 감지는 템플릿을 센다).
const STATUS_LINE = /^status:\s*\w/m;
const BLOCKED_LINE = /^status:\s*blocked\b/m;
const DISPOSITION_LINE = /^\s*[-*|].*\b(fix|defer|false-positive|wontfix)\b/m;
// disposition 은 섹션 컨텍스트 없이는 안 찍는다 — fix/defer 는 Progress/Deferred 산문 bullet 에도
// 흔한 단어라, Edit fragment 에 헤더나 placeholder 가 보일 때만 인정(정밀도 우선, recall 손실 수용).
const DISPOSITION_CONTEXT = /(#+\s*Review Disposition|\(리뷰 후 기록\))/;

function frontmatterOf(content) {
  const m = /^---\r?\n([\s\S]*?)\r?\n---/.exec(String(content || ''));
  return m ? m[1] : '';
}

function reviewDispositionSectionOf(content) {
  const out = [];
  let inSection = false;
  for (const ln of String(content || '').split('\n')) {
    if (/^#{1,3}\s/.test(ln)) inSection = /^#{1,3}\s*Review Disposition/i.test(ln);
    else if (inSection) out.push(ln);
  }
  return out.join('\n');
}

// Edit/Write 의 plan 파일 변경에서 신호 kind 를 판정. 해당 없으면 null.
// Edit 는 old→new 전이로 판정(blocked 는 기존 status 라인의 교체일 때만 — 본문 인용 오탐 차단),
// Write 는 전문뿐이라 전이 판단 불가 — frontmatter 한정(blocked)·Review Disposition 섹션 내
// 값 라인(disposition)으로 판정하고 반복은 /improve 의 session-unique 집계가 흡수한다.
function detectPlanSignal(toolName, toolInput) {
  const ti = toolInput || {};
  const fp = String(ti.file_path || '').replace(/\\/g, '/');
  if (!/(^|\/)plans\//.test(fp) || !fp.endsWith('.md')) return null;
  if (toolName === 'Edit') {
    const oldT = String(ti.old_string || '');
    const newT = String(ti.new_string || '');
    if (BLOCKED_LINE.test(newT) && !BLOCKED_LINE.test(oldT) && STATUS_LINE.test(oldT)) return 'plan-blocked';
    if (
      (DISPOSITION_CONTEXT.test(oldT) || DISPOSITION_CONTEXT.test(newT)) &&
      DISPOSITION_LINE.test(newT) &&
      !DISPOSITION_LINE.test(oldT)
    )
      return 'review-disposition';
    return null;
  }
  if (toolName === 'Write') {
    const content = String(ti.content || '');
    if (BLOCKED_LINE.test(frontmatterOf(content))) return 'plan-blocked';
    if (DISPOSITION_LINE.test(reviewDispositionSectionOf(content))) return 'review-disposition';
    return null;
  }
  return null;
}

// ---- I/O (fail-open) ----

function signalDir(env) {
  const e = env || process.env;
  return e.CLAUDE_DLC_SIGNAL_DIR || path.join(os.homedir(), '.claude', 'telemetry');
}

function signalPath(env) {
  return path.join(signalDir(env), 'dlc-signals.jsonl');
}

// ctx 스키마는 여기서만 정규화한다(호출 hook 4곳이 제각각 필드를 넣지 않게).
// session_id 부재는 'default' 로 뭉개지 않고 null — unique-session 집계 왜곡 방지.
function emit(kind, ctx, env) {
  const e = env || process.env;
  try {
    if (e.CLAUDE_DLC_SIGNAL_OFF === '1') return false;
    if (!KINDS[kind]) return false;
    const c = ctx || {};
    const row = {
      ts: new Date().toISOString(),
      kind,
      axis: KINDS[kind],
      session_id: c.session_id || null,
      cwd: c.cwd ? tildeify(c.cwd) : null,
      detail: c.detail ? tildeify(c.detail) : null,
    };
    const dir = signalDir(e);
    const file = path.join(dir, 'dlc-signals.jsonl');
    fs.mkdirSync(dir, { recursive: true });
    const max = Number(e.CLAUDE_DLC_SIGNAL_MAX_BYTES) || DEFAULT_MAX_BYTES;
    try {
      if (fs.statSync(file).size > max) fs.renameSync(file, file + '.1');
    } catch {
      /* 파일 없음·회전 경쟁 — append 는 계속(best-effort) */
    }
    fs.appendFileSync(file, JSON.stringify(row) + '\n');
    return true;
  } catch {
    return false;
  }
}

// ---- 집계 (순수 — /improve 가 CLI 로 소비) ----

// JSONL 원문 → kind 별 { axis, raw, sessions(unique 수), first, last }.
// raw 와 session-unique 를 병기하는 이유: 같은 세션의 반복 발동(재시도·매 프롬프트 매칭)이
// 볼륨을 지배하지 않게 — 효과 측정은 unique 우선.
function summarize(text) {
  const byKind = {};
  const seen = {};
  for (const line of String(text || '').split('\n')) {
    const t = line.trim();
    if (!t) continue;
    let r;
    try {
      r = JSON.parse(t);
    } catch {
      continue;
    }
    if (!r || !KINDS[r.kind]) continue;
    const k =
      byKind[r.kind] ||
      (byKind[r.kind] = { axis: KINDS[r.kind], raw: 0, sessions: 0, first: r.ts, last: r.ts });
    const ids = seen[r.kind] || (seen[r.kind] = new Set());
    k.raw += 1;
    if (r.session_id) ids.add(r.session_id);
    k.sessions = ids.size;
    if (r.ts && (!k.last || r.ts > k.last)) k.last = r.ts;
    if (r.ts && (!k.first || r.ts < k.first)) k.first = r.ts;
  }
  return byKind;
}

module.exports = { KINDS, tildeify, detectPlanSignal, signalDir, signalPath, emit, summarize };

// CLI: `node scripts/dlc-signal.js summary` — improve.sh 가 호출하는 사람용 집계 출력.
// 회전분(.1)이 있으면 함께 읽어 관측 창을 넓힌다(.1 이 과거라 먼저).
if (require.main === module && process.argv[2] === 'summary') {
  let text = '';
  try {
    text = fs.readFileSync(signalPath() + '.1', 'utf8');
  } catch {
    /* 회전분 없음 */
  }
  try {
    text += fs.readFileSync(signalPath(), 'utf8');
  } catch {
    /* 파일 없음 → 빈 집계 */
  }
  const sum = summarize(text);
  const kinds = Object.keys(sum);
  if (!kinds.length) {
    console.log('신호 없음 (hook 이 발동하면 자동 누적됨)');
  } else {
    for (const axis of ['failure', 'activity']) {
      const rows = kinds.filter((k) => sum[k].axis === axis);
      if (!rows.length) continue;
      console.log(`[${axis}]`);
      for (const k of rows.sort((a, b) => sum[b].sessions - sum[a].sessions || sum[b].raw - sum[a].raw)) {
        const v = sum[k];
        console.log(
          `  ${k}: sessions=${v.sessions} raw=${v.raw} first=${(v.first || '').slice(0, 10)} last=${(v.last || '').slice(0, 10)}`
        );
      }
    }
  }
}
