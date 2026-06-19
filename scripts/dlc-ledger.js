#!/usr/bin/env node
// dlc evidence ledger — per-session 증거 장부(임시 파일).
// dlc-task-router(리셋) / dlc-evidence-ledger(기록) / dlc-early-stop(판정) 가 공유.
// 모든 I/O 는 fail-open: 실패해도 throw 하지 않아 hook 이 세션을 막지 않는다.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

function ledgerPath(sessionId) {
  const id = String(sessionId || 'default').replace(/[^a-zA-Z0-9_-]/g, '_');
  return path.join(os.tmpdir(), `dlc-evidence-${id}.json`);
}
function read(sessionId) {
  try {
    return JSON.parse(fs.readFileSync(ledgerPath(sessionId), 'utf8'));
  } catch {
    return { changed: false, verified: false, blocks: 0 };
  }
}
function write(sessionId, data) {
  try {
    fs.writeFileSync(ledgerPath(sessionId), JSON.stringify(data));
  } catch {
    /* fail-open */
  }
}
function reset(sessionId) {
  write(sessionId, { changed: false, verified: false, blocks: 0 });
}
module.exports = { read, write, reset, ledgerPath };
