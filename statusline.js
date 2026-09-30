#!/usr/bin/env node
// ~/.claude/statusline.js — Claude Code statusLine command (Windows/Node)

const fs = require('fs');
const os = require('os');
const path = require('path');

// Codex 의 설정 기본 모델을 ~/.codex/config.toml 의 top-level `model` 에서 읽는다.
// codex 세션의 /model 변경은 config 에 안 써져 어긋날 수 있으나, statusline 에서
// 읽을 수 있는 유일한 출처다. 읽기 실패·부재 시 null → 호출부에서 'codex' 로 폴백.
function readCodexModel() {
  try {
    const cfg = fs.readFileSync(path.join(os.homedir(), '.codex', 'config.toml'), 'utf8');
    // top-level(첫 [table] 헤더 이전) 영역에서만 찾는다 — `/m` 의 ^ 는 줄 시작일 뿐
    // 파일/섹션 시작이 아니라, 제한 없으면 [profiles.x] 안의 model 도 오매칭한다.
    const topLevel = cfg.split(/^\s*\[/m)[0];
    const m = topLevel.match(/^\s*model\s*=\s*["']([^"']+)["']/m);
    return m ? m[1] : null;
  } catch (_) {
    return null;
  }
}

const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null);

// "53%" — 남은 %(100 - used). 숫자가 아니면 ''.
function remainingPct(usedPct) {
  const used = num(usedPct);
  return used != null ? Math.round(Math.max(0, 100 - used)) + '%' : '';
}

// "53%(20:30)" — 남은 %와 리셋 시각(epoch 초, 로컬 시각). 숫자가 아닌 값은 없는 것으로 보고, 둘 다 없으면 ''.
function windowPiece(usedPct, resetsAt) {
  const pct = remainingPct(usedPct);
  const reset = num(resetsAt);
  const d = reset != null ? new Date(reset * 1000) : null;
  const tm = d && !Number.isNaN(d.getTime())
    ? String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
    : '';
  return pct && tm ? `${pct}(${tm})` : pct || (tm ? `(${tm})` : '');
}

// "<label> 53%(20:30) wk 72%" — 5시간 창 뒤에 주간 창(남은 % 만). 둘 다 비면 ''.
function quotaPiece(label, fiveHour, weekly) {
  const body = [fiveHour, weekly && 'wk ' + weekly].filter(Boolean).join(' ');
  return body ? `${label} ${body}` : '';
}

// primary·secondary 의 순서는 계정마다 달라(주간 창만 primary 로 오는 사례가 보고됐다) windowDurationMins 로
// 창을 고르고, 그 값이 없을 때만 위치(primary = 5시간, secondary = 주간)를 따른다. 다른 길이의 창은 표시하지 않는다.
function codexWindow(cdx, mins, pos) {
  const wins = [cdx.primary, cdx.secondary];
  const w = wins.find((x) => x && x.windowDurationMins === mins) || wins[pos];
  return w && (w.windowDurationMins == null || w.windowDurationMins === mins) ? w : {};
}

const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  let input = {};
  try { input = JSON.parse(Buffer.concat(chunks).toString()); } catch (_) {}
  if (!input || typeof input !== 'object') input = {};

  const parts = [];

  // 1. 5-hour + weekly rate limits: "Opus 53%(20:30) wk 72%"
  //    두 창은 서로 독립적으로 없을 수 있다 — Claude Code 는 최신 API 응답에 그 창의 헤더가 없거나
  //    리셋 시각이 지나면 그 창을 뺀다.
  const rl = input.rate_limits || {};
  const fiveHour = rl.five_hour || {};
  const sevenDay = rl.seven_day || {};
  // 레이블 'claude' 대신 현재 모델명(stdin 의 model.display_name). 없으면 'claude' 폴백.
  const model = input.model && input.model.display_name;
  const claudePiece = quotaPiece(typeof model === 'string' && model ? model : 'claude',
    windowPiece(fiveHour.used_percentage, fiveHour.resets_at),
    remainingPct(sevenDay.used_percentage));
  if (claudePiece) parts.push(claudePiece);

  // 1b. Codex 5-hour + weekly limits (cached; refreshed in background when stale).
  //     Cache populated by ~/.claude/codex-quota-refresh.js.
  try {
    const CDX_CACHE = path.join(os.homedir(), '.claude', 'cache', 'codex-quota.json');
    const CDX_REFRESH = path.join(os.homedir(), '.claude', 'codex-quota-refresh.js');
    const CDX_LOCK = path.join(os.homedir(), '.claude', 'cache', 'codex-quota.lock');
    const CDX_TTL_MS = 5 * 60 * 1000;
    // codex-quota-refresh.js 의 TIMEOUT_MS(20초)보다 길어야 한다 — refresh 가 도는 동안 다시 띄우지 않는다.
    const CDX_LOCK_MAX_MS = 25 * 1000;

    let cdx = null;
    let stale = true;
    try {
      cdx = JSON.parse(fs.readFileSync(CDX_CACHE, 'utf8'));
      stale = (Date.now() - (cdx.fetchedAt || 0)) > CDX_TTL_MS;
    } catch (_) { /* no cache yet */ }

    let inFlight = false;
    try {
      const lockStat = fs.statSync(CDX_LOCK);
      inFlight = (Date.now() - lockStat.mtimeMs) < CDX_LOCK_MAX_MS;
    } catch (_) { /* no lock */ }

    if (stale && !inFlight) {
      try {
        fs.mkdirSync(path.dirname(CDX_LOCK), { recursive: true });
        fs.writeFileSync(CDX_LOCK, String(process.pid));
        const { spawn } = require('child_process');
        const child = spawn(process.execPath, [CDX_REFRESH], {
          detached: true,
          stdio: 'ignore',
          windowsHide: true,
        });
        child.unref();
      } catch (_) { /* swallow */ }
    }

    if (cdx) {
      const fiveWin = codexWindow(cdx, 300, 0);
      const weekWin = codexWindow(cdx, 10080, 1);
      const five = windowPiece(fiveWin.usedPercent, fiveWin.resetsAt);
      const week = remainingPct(weekWin.usedPercent);
      // 레이블 'codex' 대신 codex 설정 모델명. 못 읽으면 'codex' 폴백 — 표시할 창이 없으면 config 를 읽지 않는다.
      if (five || week) parts.push(quotaPiece(readCodexModel() || 'codex', five, week));
    }
  } catch (_) { /* never break statusline */ }

  // 2. Context usage percentage
  const usedPct = input.context_window && input.context_window.used_percentage;
  if (usedPct != null) {
    parts.push('ctx ' + Math.round(usedPct) + '%');
  }

  // 3. Git branch + worktree indicator from workspace.current_dir
  const cwd = (input.workspace && input.workspace.current_dir) || (input.cwd || '');
  if (cwd) {
    const { execFileSync } = require('child_process');
    // execFileSync (no shell): cwd is passed as a literal argv element, so a
    // directory name containing shell metacharacters cannot inject commands.
    const gitCmd = (argv) => execFileSync('git', ['-C', cwd, '--no-optional-locks', ...argv], {
      stdio: ['ignore', 'pipe', 'ignore'],
      timeout: 2000
    }).toString().trim();
    try {
      const branch = gitCmd(['rev-parse', '--abbrev-ref', 'HEAD']);
      if (branch && branch !== 'HEAD') {
        let label = branch;
        // worktree 판별: --show-toplevel(현재 worktree root) vs
        // dirname(--git-common-dir)(main repo root) 비교.
        try {
          const toplevel = gitCmd(['rev-parse', '--show-toplevel']);
          const commonDir = gitCmd(['rev-parse', '--path-format=absolute', '--git-common-dir']);
          const mainRoot = path.dirname(commonDir);
          const norm = (p) => p.replace(/\\/g, '/').replace(/\/$/, '').toLowerCase();
          if (norm(toplevel) !== norm(mainRoot)) {
            const wtName = path.basename(toplevel);
            label = branch + ' @wt:' + wtName;
          }
        } catch (_) { /* worktree 감지 실패 — branch 만 */ }
        parts.push(label);
      }
    } catch (_) { /* not a git repo — omit */ }
  }

  process.stdout.write(parts.join(' | '));
});
