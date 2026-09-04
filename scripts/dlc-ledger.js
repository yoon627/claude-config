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
// *Covered/*Pending: 이번 세션에 문서화된(= target 갱신으로 커버된) trigger 파일 / 아직 커버 안 된 것.
//   재편집 오탐 차단용(dlc-doc-drift). `{...DEFAULT}` 얕은 복사로 쓰이므로 소비자는 push 대신 concat 으로 새 배열을 할당한다.
// driftRoot: *Pending/*Covered 의 rel 이 어느 root 기준인가. Stop 시점 root 와 다르면 그 rel 로
//   파일을 stat 할 수 없다(다른 worktree·main 의 동명 파일을 재게 된다) → mtime 판정을 포기한다.
//   한 세션이 두 root 를 오가면 '' (mixed) 로 두어 어떤 root 와도 일치하지 않게 한다.
const DEFAULT = { changed: false, verified: false, blocks: 0, readmeDirty: false, indexDirty: false, docBlocks: 0, readmeTrigger: null, indexTrigger: null, changedTrigger: null, readmeCovered: [], readmePending: [], indexCovered: [], indexPending: [], driftRoot: null };

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
