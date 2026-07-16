#!/usr/bin/env node
// transcript 사용량 카운트 — /improve --deep 보조. skill/subagent/codex 호출 빈도.
// 프라이버시 계약(B4): JSONL 을 **파싱**해 진짜 tool_use 레코드만 집계 →
//   출력은 카운트 + 고정 slug 뿐. 파일명·경로·원문·args·사용자 컨텐츠 절대 미출력.
//   (raw grep 은 user content 의 "skill":"X" 문자열·binary 파일명까지 새므로 쓰지 않는다.)
// read-only. 디렉토리·파일 없거나 파싱 실패는 조용히 skip.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const SLUG = /^[\w:-]{1,40}$/; // 집계 대상 slug 형태 제한(비정상 값 차단)
const skills = new Map();
const agents = new Map();
let codex = 0;

function bump(m, k) {
  if (typeof k === 'string' && SLUG.test(k)) m.set(k, (m.get(k) || 0) + 1);
}

// content block 트리를 돌며 tool_use 레코드만 집계(그 외 노드는 값 안 읽음).
function walk(node, depth) {
  if (depth > 40 || node == null) return;
  if (Array.isArray(node)) {
    for (const x of node) walk(x, depth + 1);
    return;
  }
  if (typeof node !== 'object') return;
  if (node.type === 'tool_use' && typeof node.name === 'string') {
    const inp = node.input && typeof node.input === 'object' ? node.input : {};
    if (node.name === 'Skill') bump(skills, inp.skill);
    else if (node.name === 'Agent' || node.name === 'Task') bump(agents, inp.subagent_type); // 현행 Agent + 구 Task
    else if (node.name === 'Bash' && typeof inp.command === 'string' && /\bcodex\s+exec\b/.test(inp.command)) codex += 1;
  }
  if (node.message) walk(node.message, depth + 1);
  if (node.content) walk(node.content, depth + 1);
}

function scan(dir) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of entries) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      scan(p);
      continue;
    }
    if (!e.isFile() || !e.name.endsWith('.jsonl')) continue;
    let text;
    try {
      text = fs.readFileSync(p, 'utf8');
    } catch {
      continue;
    }
    for (const ln of text.split('\n')) {
      if (!ln.trim()) continue;
      let obj;
      try {
        obj = JSON.parse(ln);
      } catch {
        continue; // 비-JSON(바이너리·손상) 라인 → 무시(파일명·원문 노출 없음)
      }
      walk(obj, 0);
    }
  }
}

function printTally(label, m) {
  console.log(`[info] ${label}:`);
  const rows = [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, 15);
  if (!rows.length) {
    console.log('    (없음)');
    return;
  }
  for (const [name, c] of rows) console.log(`    ${name}: ${c}`);
}

const dir = process.env.CLAUDE_TRANSCRIPT_DIR || path.join(os.homedir(), '.claude', 'projects');
if (!fs.existsSync(dir)) {
  console.log('[info] transcript 디렉토리 없음 → 사용량 집계 skip'); // 경로 미출력(프라이버시)
  process.exit(0);
}
try {
  scan(dir);
  printTally('skill 호출 상위', skills);
  printTally('subagent 유형', agents);
  console.log(`[info] codex exec 호출: ${codex}`);
} catch {
  console.log('[info] 사용량 집계 실패 → skip');
}
process.exit(0);
