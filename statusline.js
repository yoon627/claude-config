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

const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  let input = {};
  try { input = JSON.parse(Buffer.concat(chunks).toString()); } catch (_) {}

  const parts = [];

  // 1. 5-hour rate limit: remaining % and reset clock as "53%(20:30)"
  const fiveHour = input.rate_limits && input.rate_limits.five_hour;
  if (fiveHour) {
    const usedFivePct = fiveHour.used_percentage;
    const resetsAt = fiveHour.resets_at;

    let pctStr = '';
    let timeStr = '';
    if (usedFivePct != null) {
      const remainingPct = Math.max(0, 100 - usedFivePct);
      pctStr = Math.round(remainingPct) + '%';
    }
    if (resetsAt != null) {
      const d = new Date(resetsAt * 1000);
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      timeStr = hh + ':' + mm;
    }

    // 레이블 'claude' 대신 현재 모델명(stdin 의 model.display_name). 없으면 'claude' 폴백.
    const label = (input.model && input.model.display_name) || 'claude';
    const piece = pctStr && timeStr ? label + ' ' + pctStr + '(' + timeStr + ')'
                : pctStr ? label + ' ' + pctStr
                : timeStr ? label + ' (' + timeStr + ')'
                : '';
    if (piece) parts.push(piece);
  }

  // 1b. Codex 5-hour limit (cached; refreshed in background when stale).
  //     Cache populated by ~/.claude/codex-quota-refresh.js.
  try {
    const CDX_CACHE = path.join(os.homedir(), '.claude', 'cache', 'codex-quota.json');
    const CDX_REFRESH = path.join(os.homedir(), '.claude', 'codex-quota-refresh.js');
    const CDX_LOCK = path.join(os.homedir(), '.claude', 'cache', 'codex-quota.lock');
    const CDX_TTL_MS = 5 * 60 * 1000;
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

    if (cdx && cdx.primary) {
      const usedPct = cdx.primary.usedPercent;
      const resetsAt = cdx.primary.resetsAt;
      let pct = '', tm = '';
      if (usedPct != null) {
        pct = Math.round(Math.max(0, 100 - usedPct)) + '%';
      }
      if (resetsAt != null) {
        const d = new Date(resetsAt * 1000);
        tm = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
      }
      // 레이블 'codex' 대신 codex 설정 모델명. 못 읽으면 'codex' 폴백.
      const label = readCodexModel() || 'codex';
      const piece = pct && tm ? label + ' ' + pct + '(' + tm + ')'
                  : pct ? label + ' ' + pct
                  : tm ? label + ' (' + tm + ')'
                  : '';
      if (piece) parts.push(piece);
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

  // 5. Background task indicator — scan Claude Code's tasks output dir.
  //    Heuristic: a .output file whose mtime was touched within the last 30s
  //    is considered an active background job. Elapsed time is taken from
  //    the oldest active file's ctime.
  try {
    const sessionId = input.session_id;
    if (cwd && sessionId) {
      const slug = cwd.replace(/[:\\\/]/g, '-');
      const tasksDir = path.join(os.tmpdir(), 'claude', slug, sessionId, 'tasks');
      if (fs.existsSync(tasksDir)) {
        const now = Date.now();
        const ACTIVE_WINDOW_MS = 30 * 1000;
        const files = fs.readdirSync(tasksDir).filter(f => f.endsWith('.output'));
        const active = [];
        for (const f of files) {
          let stat;
          try { stat = fs.statSync(path.join(tasksDir, f)); } catch (_) { continue; }
          if (now - stat.mtimeMs <= ACTIVE_WINDOW_MS) {
            active.push({ ctimeMs: stat.ctimeMs });
          }
        }
        if (active.length > 0) {
          active.sort((a, b) => a.ctimeMs - b.ctimeMs);
          const elapsedSec = Math.max(0, Math.floor((now - active[0].ctimeMs) / 1000));
          const mins = Math.floor(elapsedSec / 60);
          const secs = elapsedSec % 60;
          const elapsedStr = mins > 0 ? mins + 'm' + secs + 's' : secs + 's';
          parts.push('✻ ' + active.length + ' bg ' + elapsedStr);
        }
      }
    }
  } catch (_) { /* swallow — never break the statusline */ }

  process.stdout.write(parts.join(' | '));
});
