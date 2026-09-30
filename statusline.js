#!/usr/bin/env node
// ~/.claude/statusline.js — Claude Code statusLine command (Windows/Node)

const path = require('path');

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
