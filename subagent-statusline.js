#!/usr/bin/env node
// ~/.claude/subagent-statusline.js — Claude Code subagentStatusLine command (Windows/Node)

const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  let input = {};
  try { input = JSON.parse(Buffer.concat(chunks).toString()); } catch (_) {}

  const parts = [];

  // status
  const status = input.status || '';
  if (status) parts.push(status);

  // token count (use current_usage input_tokens if available, else total)
  let tokens = null;
  if (input.context_window) {
    const cu = input.context_window.current_usage;
    if (cu && cu.input_tokens != null) {
      tokens = cu.input_tokens + (cu.output_tokens || 0);
    } else {
      const ti = input.context_window.total_input_tokens;
      const to = input.context_window.total_output_tokens;
      if (ti != null) tokens = ti + (to || 0);
    }
  }
  if (tokens != null) {
    parts.push(tokens >= 1000
      ? (tokens / 1000).toFixed(1) + 'k tok'
      : tokens + ' tok');
  }

  // elapsed time
  const durationMs = input.cost && input.cost.total_duration_ms;
  if (durationMs != null) {
    const totalSec = Math.floor(durationMs / 1000);
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    parts.push(mins + 'm ' + secs + 's');
  }

  process.stdout.write(parts.join(' | '));
});
