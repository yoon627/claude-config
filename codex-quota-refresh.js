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
// app-server 가 끝난 뒤 남은 응답을 읽을 여유. 손자 프로세스가 파이프를 쥐고 있으면 close 가 늦으므로 이만큼만 기다린다.
const DRAIN_MS = 1000;

// lock 은 캐시를 쓴 경우에만 지운다. 캐시를 못 쓰면 statusline 이 refresh 주기(2초)마다 다시 spawn 하므로,
// lock 을 남겨 statusline 이 lock 을 쓴(=spawn 한) 시각부터 25초까지는 다시 띄우지 않게 한다.
let cacheWritten = false;
process.on("exit", () => {
  if (cacheWritten) try { fs.unlinkSync(LOCK_FILE); } catch (_) {}
});

function writeCache(data) {
  fs.mkdirSync(CACHE_DIR, { recursive: true });
  const tmp = CACHE_FILE + ".tmp." + process.pid;
  try {
    fs.writeFileSync(tmp, JSON.stringify({ fetchedAt: Date.now(), ...data }));
    fs.renameSync(tmp, CACHE_FILE);
  } catch (err) {
    try { fs.unlinkSync(tmp); } catch (_) {}
    throw err;
  }
  cacheWritten = true;
}

let settled = false;
let timer = null;
// 모든 종료 경로가 여기로 온다. 실패도 fetchedAt 을 담은 negative cache 로 남겨, codex 가 없거나
// 인증되지 않은 동안 statusline 이 매번 다시 spawn 하지 않게 한다.
function finish(result, error) {
  if (settled) return;
  settled = true;
  clearTimeout(timer);
  let code = error ? 1 : 0;
  try {
    writeCache(error ? { error: String(error) } : result);
  } catch (_) {
    code = 1;
  }
  try { proc.kill(); } catch (_) {}
  process.exit(code);
}

// POSIX 에선 셸 없이 띄운다 — `sh -c` 가 exec 하지 않는 셸(Ubuntu dash)이면 kill 이 셸에만 가서 app-server 가 남는다.
// Windows 의 codex 는 .cmd shim 이라 셸이 필요하고, 인자를 따로 넘기면 DEP0190 경고가 나므로 한 문자열로 준다.
const spawnOptions = { stdio: ["pipe", "pipe", "pipe"], windowsHide: true, cwd: os.homedir() };
const proc = process.platform === "win32"
  ? spawn("codex app-server", { ...spawnOptions, shell: true })
  : spawn("codex", ["app-server"], spawnOptions);

let buf = "";
let nextId = 0;
const pending = new Map();
timer = setTimeout(() => finish(null, "timeout"), TIMEOUT_MS);

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
// app-server 가 stdin 을 먼저 닫으면 write 가 EPIPE 로 실패한다 — 종료 판정은 close·exit 가 한다.
proc.stdin.on("error", () => {});

proc.on("error", (err) => finish(null, "spawn-error: " + (err && err.message || err)));
const exited = (code, signal) => finish(null, `process-exit: code=${code} signal=${signal}`);
proc.on("close", exited);
proc.on("exit", (code, signal) => setTimeout(() => exited(code, signal), DRAIN_MS));

function rpc(method, params = {}) {
  return new Promise((res, rej) => {
    const id = ++nextId;
    pending.set(id, (m) => (m.error ? rej(new Error(m.error.message)) : res(m.result)));
    proc.stdin.write(JSON.stringify({ jsonrpc: "2.0", id, method, params }) + "\n");
  });
}

(async () => {
  let rateLimits;
  try {
    await rpc("initialize", { clientInfo: { name: "codex-quota-refresh", version: "0.1" } });
    const r = await rpc("account/rateLimits/read");
    rateLimits = (r && r.rateLimits) || r;
  } catch (err) {
    return finish(null, "rpc-error: " + (err && err.message || err));
  }
  finish(rateLimits);
})();
