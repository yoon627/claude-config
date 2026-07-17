#!/usr/bin/env node
// dlc evidence ledger — per-session 증거 장부(임시 파일).
// dlc-task-router(리셋) / dlc-evidence-ledger(기록) / dlc-early-stop(판정) 가 공유.
// 모든 I/O 는 fail-open: 실패해도 throw 하지 않아 hook 이 세션을 막지 않는다.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

// 단일 스키마 소스 — read 기본값·reset 둘 다 이걸 쓴다(한쪽 누락 시 새 필드 undefined 회귀 방지).
//   changed/verified/blocks: 검증 누락 추적(early-stop). readmeDirty/indexDirty/docBlocks: 문서 drift 추적(dlc-doc-drift).
// *Trigger: 마지막으로 해당 dirty/changed 를 유발한 파일(repo-relative rel · basename). 신호 detail 용 — /improve 가 오탐 패턴(예: readmeTrigger=CLAUDE.md 내부 dedup) 식별. dirty 해제 시 null.
const DEFAULT = { changed: false, verified: false, blocks: 0, readmeDirty: false, indexDirty: false, docBlocks: 0, readmeTrigger: null, indexTrigger: null, changedTrigger: null };

function ledgerPath(sessionId) {
  const id = String(sessionId || 'default').replace(/[^a-zA-Z0-9_-]/g, '_');
  return path.join(os.tmpdir(), `dlc-evidence-${id}.json`);
}
function read(sessionId) {
  try {
    return { ...DEFAULT, ...JSON.parse(fs.readFileSync(ledgerPath(sessionId), 'utf8')) };
  } catch {
    return { ...DEFAULT };
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
  write(sessionId, { ...DEFAULT });
}
module.exports = { read, write, reset, ledgerPath, DEFAULT };
