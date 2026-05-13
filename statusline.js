#!/usr/bin/env node
// ~/.claude/statusline.js — Claude Code statusLine command (Windows/Node)

const fs = require('fs');
const os = require('os');
const path = require('path');

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

    if (pctStr && timeStr) parts.push(pctStr + '(' + timeStr + ')');
    else if (pctStr) parts.push(pctStr);
    else if (timeStr) parts.push('(' + timeStr + ')');
  }

  // 2. Context usage percentage
  const usedPct = input.context_window && input.context_window.used_percentage;
  if (usedPct != null) {
    parts.push('ctx ' + Math.round(usedPct) + '%');
  }

  // 3. Model name + effort level
  const modelName = (input.model && input.model.display_name) || '';
  if (modelName) {
    const effortLevel = input.effort && input.effort.level;
    parts.push(effortLevel ? modelName + ' [' + effortLevel + ']' : modelName);
  }

  // 4. Git branch + worktree indicator from workspace.current_dir
  const cwd = (input.workspace && input.workspace.current_dir) || (input.cwd || '');
  if (cwd) {
    const { execSync } = require('child_process');
    const gitCmd = (args) => execSync('git -C "' + cwd + '" --no-optional-locks ' + args, {
      stdio: ['ignore', 'pipe', 'ignore'],
      timeout: 2000
    }).toString().trim();
    try {
      const branch = gitCmd('rev-parse --abbrev-ref HEAD');
      if (branch && branch !== 'HEAD') {
        let label = branch;
        // worktree 판별: --show-toplevel(현재 worktree root) vs
        // dirname(--git-common-dir)(main repo root) 비교.
        try {
          const toplevel = gitCmd('rev-parse --show-toplevel');
          const commonDir = gitCmd('rev-parse --path-format=absolute --git-common-dir');
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
