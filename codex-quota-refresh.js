#!/usr/bin/env node
// ~/.claude/codex-quota-refresh.js
// Spawn-and-die helper: fetches Codex rate limits via `codex app-server`
// (JSON-RPC: initialize -> account/rateLimits/read) and writes the result
// to ~/.claude/cache/codex-quota.json. Designed to be invoked detached
// from statusline.js when the cache is stale.

"use strict";
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const CACHE_DIR = path.join(os.homedir(), ".claude", "cache");
const CACHE_FILE = path.join(CACHE_DIR, "codex-quota.json");
const LOCK_FILE = path.join(CACHE_DIR, "codex-quota.lock");
const TIMEOUT_MS = 20000;

process.on("exit", () => {
  try { fs.unlinkSync(LOCK_FILE); } catch (_) {}
});

// Negative cache: write fetchedAt even on failure so statusline.js stops
// re-spawning this script every 2s while codex is unreachable/unauth'd.
function writeNegativeCache(reason) {
  try {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
    const tmp = CACHE_FILE + ".tmp." + process.pid;
    fs.writeFileSync(tmp, JSON.stringify({ fetchedAt: Date.now(), error: String(reason || "unknown") }));
    fs.renameSync(tmp, CACHE_FILE);
  } catch (_) { /* swallow */ }
}

const proc = spawn("codex", ["app-server"], {
  stdio: ["pipe", "pipe", "pipe"],
  shell: true,
  windowsHide: true,
  cwd: os.homedir(),
});

let buf = "";
let nextId = 0;
let settled = false;
const pending = new Map();
const timer = setTimeout(() => {
  if (settled) return;
  settled = true;
  writeNegativeCache("timeout");
  try { proc.kill(); } catch (_) {}
  process.exit(1);
}, TIMEOUT_MS);

proc.stdout.on("data", (chunk) => {
  buf += chunk.toString();
  let nl;
  while ((nl = buf.indexOf("\n")) !== -1) {
    const line = buf.slice(0, nl).trim();
    buf = buf.slice(nl + 1);
    if (!line) continue;
    try {
      const msg = JSON.parse(line);
      const cb = pending.get(msg.id);
      if (cb) { pending.delete(msg.id); cb(msg); }
    } catch (_) {}
  }
});

proc.stderr.on("data", () => { /* drain to avoid backpressure */ });

proc.on("error", (err) => {
  if (settled) return;
  settled = true;
  clearTimeout(timer);
  writeNegativeCache("spawn-error: " + (err && err.message || err));
  process.exit(1);
});

proc.on("exit", (code, signal) => {
  if (settled) return;
  if (code === 0) return;
  settled = true;
  clearTimeout(timer);
  writeNegativeCache(`process-exit: code=${code} signal=${signal}`);
  process.exit(1);
});

function rpc(method, params = {}) {
  return new Promise((res, rej) => {
    const id = ++nextId;
    pending.set(id, (m) => (m.error ? rej(new Error(m.error.message)) : res(m.result)));
    proc.stdin.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n");
  });
}

(async () => {
  try {
    await rpc("initialize", { clientInfo: { name: "codex-quota-refresh", version: "0.1" } });
    const r = await rpc("account/rateLimits/read");
    if (settled) return;
    settled = true;
    clearTimeout(timer);
    const q = (r && r.rateLimits) || r;
    fs.mkdirSync(CACHE_DIR, { recursive: true });
    const tmp = CACHE_FILE + ".tmp." + process.pid;
    fs.writeFileSync(tmp, JSON.stringify({ fetchedAt: Date.now(), ...q }));
    fs.renameSync(tmp, CACHE_FILE);
    try { proc.kill(); } catch (_) {}
    process.exit(0);
  } catch (err) {
    if (settled) return;
    settled = true;
    clearTimeout(timer);
    writeNegativeCache("rpc-error: " + (err && err.message || err));
    try { proc.kill(); } catch (_) {}
    process.exit(1);
  }
})();
