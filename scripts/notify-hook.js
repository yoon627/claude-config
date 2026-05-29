#!/usr/bin/env node
// notify-hook.js — cross-platform notification hook for Claude Code.
// Single entry used by every OS so settings.json stays OS-agnostic.
//   Usage: node notify-hook.js <Event> [sound]
//     Event: Stop | Notification
//     sound: optional override — macOS uses /System/Library/Sounds/<name>.aiff,
//            Windows uses a SystemSound name (Asterisk|Beep|Exclamation|Hand|Question).
//            An override invalid for the running OS falls back to the per-event default.
// macOS : afplay system sound + osascript banner (inline).
// Windows: delegates to notify-hook.ps1 (WinRT toast + taskbar flash), forwarding stdin.
// Linux : best-effort notify-send.
// Reads Claude Code hook JSON from stdin (.message, .cwd) — all best-effort, never throws.

const path = require('path');
const { spawn } = require('child_process');

const EVENT = process.argv[2] || 'Stop';
const SOUND_OVERRIDE = process.argv[3] || '';

function readStdin() {
  return new Promise((resolve) => {
    if (process.stdin.isTTY) { resolve(''); return; }
    let data = '';
    let settled = false;
    const done = () => { if (!settled) { settled = true; resolve(data); } };
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (c) => { data += c; });
    process.stdin.on('end', done);
    process.stdin.on('error', done);
    // Safety net: a hook must never hang the session waiting on stdin.
    const t = setTimeout(done, 1000);
    if (t.unref) t.unref();
  });
}

// Replace control chars (codepoint < 32: newlines, tabs, BEL...) with spaces so
// the banner text stays clean. Written without escape sequences on purpose.
function clean(s) {
  let out = '';
  for (const ch of s) out += ch.charCodeAt(0) < 32 ? ' ' : ch;
  return out;
}

function parse(raw) {
  try {
    const d = JSON.parse(raw || '{}');
    return {
      msg: clean((d.message || '').toString()),
      cwd: (d.cwd || '').toString(),
    };
  } catch {
    return { msg: '', cwd: '' };
  }
}

(async () => {
  const raw = await readStdin();
  const { msg: parsedMsg, cwd } = parse(raw);
  const msg = parsedMsg || (EVENT === 'Notification' ? '입력 대기' : '응답 완료');
  const title = (cwd && path.basename(cwd)) || 'Claude';

  try {
    if (process.platform === 'darwin') {
      const sound = SOUND_OVERRIDE || (EVENT === 'Notification' ? 'Ping' : 'Glass');
      const soundFile = `/System/Library/Sounds/${sound}.aiff`;
      const af = spawn('/usr/bin/afplay', [soundFile], { stdio: 'ignore', detached: true });
      af.on('error', () => {});
      af.unref();
      // JSON.stringify yields a valid double-quoted AppleScript string literal;
      // passing as a spawn arg avoids any shell interpolation / injection.
      const script = `display notification ${JSON.stringify(msg)} with title ${JSON.stringify(title)}`;
      const os = spawn('/usr/bin/osascript', ['-e', script], { stdio: 'ignore', detached: true });
      os.on('error', () => {});
      os.unref();
    } else if (process.platform === 'win32') {
      // notify-hook.ps1 validates -Sound against a fixed SystemSound set, so only
      // forward an override that is valid for Windows; otherwise use the default.
      const WIN_SOUNDS = ['Asterisk', 'Beep', 'Exclamation', 'Hand', 'Question'];
      const winSound = WIN_SOUNDS.includes(SOUND_OVERRIDE)
        ? SOUND_OVERRIDE
        : (EVENT === 'Notification' ? 'Exclamation' : 'Asterisk');
      const ps1 = path.join(__dirname, 'notify-hook.ps1');
      const child = spawn('powershell.exe',
        ['-NoProfile', '-File', ps1, '-Event', EVENT, '-Sound', winSound],
        { stdio: ['pipe', 'ignore', 'ignore'], detached: true, windowsHide: true });
      child.on('error', () => {});
      // Forward the original hook JSON so the .ps1 can extract cwd / session / tab title.
      try { child.stdin.end(raw); } catch {}
      child.unref();
    } else {
      const child = spawn('notify-send', [title, msg], { stdio: 'ignore', detached: true });
      child.on('error', () => {});
      child.unref();
    }
  } catch {}
})();
