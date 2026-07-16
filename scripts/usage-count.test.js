#!/usr/bin/env node
// usage-count.js 테스트 — 합성 transcript fixture 로 카운트 정확성 + 프라이버시(B4).
// 핵심: 진짜 tool_use 레코드만 집계(user content 의 "skill":"X" 문자열은 미집계),
//   출력에 PII·args·파일명·경로 절대 없음.
'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const SCRIPT = path.join(__dirname, 'usage-count.js');

let n = 0;
const ok = (name, fn) => { fn(); n++; };

const PII = 'SUPERSECRET_PII_abc123';
const SECRET_FNAME = 'SESSION_secretname_42.jsonl';
const asst = (blocks) => JSON.stringify({ type: 'assistant', message: { role: 'assistant', content: blocks } });
const tu = (name, input) => ({ type: 'tool_use', name, input });

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'uc-'));
  const proj = path.join(root, 'proj-encoded');
  fs.mkdirSync(proj, { recursive: true });
  const lines = [
    asst([tu('Skill', { skill: 'dlc', args: PII + ' sensitive request' })]),
    asst([tu('Skill', { skill: 'dlc', args: 'x' }), tu('Skill', { skill: 'dlc' })]),
    asst([tu('Skill', { skill: 'wt', args: 'hunter2 password' })]),
    asst([tu('Agent', { subagent_type: 'code-reviewer', prompt: PII }), tu('Task', { subagent_type: 'code-reviewer' })]), // Agent(현행)+Task(구) 둘 다
    asst([tu('Agent', { subagent_type: 'plan-reviewer' })]),
    asst([tu('Bash', { command: 'codex exec --sandbox read-only "review"' })]),
    asst([tu('Bash', { command: 'cd x && codex exec foo' })]),
    // 디코이: user content 에 tool_use 처럼 보이는 문자열 — schema-bound 라 미집계여야
    JSON.stringify({ type: 'user', message: { role: 'user', content: `${PII} "skill":"private-client" my password hunter2` } }),
    // 손상/비-JSON 라인 — 무시(파일명 노출 없음)
    '\x00\x01 not json "skill":"binary-leak"',
  ];
  fs.writeFileSync(path.join(proj, SECRET_FNAME), lines.join('\n') + '\n');
  return root;
}
function run(dir) {
  return execFileSync('node', [SCRIPT], { env: { ...process.env, CLAUDE_TRANSCRIPT_DIR: dir } }).toString();
}

ok('카운트 정확: tool_use 레코드만', () => {
  const out = run(fixture());
  assert.match(out, /dlc: 3/);
  assert.match(out, /wt: 1/);
  assert.match(out, /code-reviewer: 2/);
  assert.match(out, /plan-reviewer: 1/);
  assert.match(out, /codex exec 호출: 2/);
});
ok('B4: schema-bound — user content 의 "skill":"private-client" 미집계', () => {
  const out = run(fixture());
  assert.doesNotMatch(out, /private-client/);
  assert.doesNotMatch(out, /binary-leak/);
});
ok('B4: PII·args·비밀번호 미출현', () => {
  const out = run(fixture());
  assert.doesNotMatch(out, /SUPERSECRET_PII/);
  assert.doesNotMatch(out, /hunter2/);
  assert.doesNotMatch(out, /sensitive request/);
});
ok('B4: transcript 파일명 미출현', () => {
  const out = run(fixture());
  assert.doesNotMatch(out, /secretname|\.jsonl/);
});
ok('디렉토리 없음 → skip + 경로 미출력', () => {
  const secret = path.join(os.tmpdir(), 'uc-PRIVATE_CLIENT_' + process.pid);
  const out = run(secret);
  assert.match(out, /skip/);
  assert.doesNotMatch(out, /PRIVATE_CLIENT/); // 경로 누출 없음
});

console.log(`usage-count.test.js: ${n} tests passed`);
