#!/usr/bin/env node
// frontmatter-lint.js 회귀 테스트 — 순수 lintFrontmatter() + CLI. 무프레임워크·결정적.
'use strict';
const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { lintFrontmatter } = require('./frontmatter-lint.js');
const SCRIPT = path.join(__dirname, 'frontmatter-lint.js');

let fail = 0;
function ok(name, cond) { if (!cond) fail++; console.log(`${cond ? 'PASS' : 'FAIL'} ${name}`); }
function hasV(text, line, sub) {
  return lintFrontmatter(text).violations.some((v) => v.line === line && v.message.includes(sub));
}
function fieldsOf(text) {
  const r = lintFrontmatter(text);
  return r.violations.length ? null : r.fields;
}
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
// 2행 name, 3행부터 나머지 줄.
const fm = (...lines) => ['---', 'name: x', ...lines, '---', '', '본문'].join('\n');
const desc = (value) => fm(`description: ${value}`);
const BOM = String.fromCharCode(0xfeff);
const NBSP = String.fromCharCode(0xa0);
const IDEO = String.fromCharCode(0x3000);

// 0efce86 이전 skills/c/SKILL.md 3행 그대로.
const OLD_C = 'description: 현재 worktree/repo 의 진행 중인 plan(CLAUDE.md §10)을 찾아 남은 작업과 plan↔실제(git/코드) sync 상태를 진단하고, 어긋나면 plan 을 보정한 뒤 다음 액션이 명확하면 이어서 실행하는 plan 이어가기(plan-continue) 오케스트레이션. `/c` 명시 호출 또는 "진행하던 작업 이어가자"류 요청 시 사용. branch→plan dir 매칭, 실패 시 in_progress 목록 제시. 확인·sync 진단·보정 후 `# Next` 가 명확하면 이어서 실행한다(멈추는 예외 5종: blocked·plan 후보 다수·Next 재구성·파괴적/외부공개 액션·done). 그 브랜치 PR 의 사람 리뷰 코멘트도 intake 한다. 단순 질문·탐색·신규 작업 시작에는 쓰지 않는다(새 plan 생성은 dlc 몫).';
const OLD_C_FILE = ['---', 'name: c', OLD_C, '---', '', '# c'].join('\n');

// ---- 허용 (읽은 값까지) ----
ok('평문 → name·description', same(fieldsOf(desc('설명')), { name: 'x', description: '설명' }));
ok("작은따옴표 안 ': ' → 따옴표를 벗긴 값", fieldsOf(desc("'예외 5종: blocked'"))?.description === '예외 5종: blocked');
ok("큰따옴표 안 ': '·' #' → 따옴표를 벗긴 값", fieldsOf(desc('"PR #225: 머지"'))?.description === 'PR #225: 머지');
ok('-x·:x·?x 로 시작하는 평문', ['-x 옵션', ':x 뒤', '?x 물음'].every((v) => fieldsOf(desc(v))?.description === v));
const MID = "a [b] {c} 'q' \"d\" &e *f !g |h >i %j @k `/c` C# https://x.y/z a :b - c";
ok('값 중간의 지시자·따옴표·콜론·# → 그대로', fieldsOf(desc(MID))?.description === MID);
ok('agents 의 쉼표 평문(tools) → 문자열', fieldsOf(fm('description: d', 'tools: Read, Grep, Glob, Bash'))?.tools === 'Read, Grep, Glob, Bash');
ok('콜론 뒤 여러 공백·끝 공백 → 벗긴 값', fieldsOf(fm('description:   d   '))?.description === 'd');
ok('CRLF → LF 와 같은 값', same(fieldsOf(desc('설명').replace(/\n/g, '\r\n')), { name: 'x', description: '설명' }));
ok('BOM → 벗기고 같은 값', same(fieldsOf(BOM + desc('설명')), { name: 'x', description: '설명' }));
ok('본문의 --- 는 보지 않음', fieldsOf(desc('설명') + '\n---\n: #\n') !== null);
ok('camelCase 키(Claude Code agent 키)', same(fieldsOf(fm('description: d', 'permissionMode: plan', 'maxTurns: 20', 'disallowedTools: Write, Edit')),
  { name: 'x', description: 'd', permissionMode: 'plan', maxTurns: '20', disallowedTools: 'Write, Edit' }));
ok('평문 값 가운데의 NBSP·U+3000 → 그대로', fieldsOf(desc(`a${NBSP}b${IDEO}c`))?.description === `a${NBSP}b${IDEO}c`);
ok("name 의 'yes'·'1_000'·따옴표 숫자 → 허용", ['yes', '1_000', "'123'"].every((v) => fieldsOf(`---\nname: ${v}\ndescription: d\n---\n`) !== null));

// ---- 거부 ----
ok("옛 /c description(평문 안 ': ') → 3행", hasV(OLD_C_FILE, 3, "': '"));
ok("평문 끝 ':' → 3행", hasV(desc('끝:'), 3, "':' 로 끝"));
ok("평문 안 ' #' → 3행(주석으로 잘림)", hasV(desc('PR #225 기록'), 3, "' #'"));
for (const c of [',', '[', ']', '{', '}', '#', '&', '*', '!', '|', '>', '%', '@', '`']) {
  ok(`첫 글자 지시자 ${c} → 3행`, hasV(desc(`${c}x`), 3, '지시자'));
}
ok("'- '·'? '·': ' 로 시작 → 지시자", ['- x', '? x', ': x'].every((v) => hasV(desc(v), 3, '지시자')));
ok("'-'·'?'·':' 단독 값 → 지시자", ['-', '?', ':'].every((v) => hasV(desc(v), 3, '지시자')));
ok('닫히지 않은 따옴표', hasV(desc('"abc'), 3, '한 쌍') && hasV(desc("'"), 3, '한 쌍'));
ok('닫는 따옴표 뒤 글자', hasV(desc("'a' b"), 3, '한 쌍') && hasV(desc('"a" # c'), 3, '한 쌍'));
ok("따옴표 안 자기 따옴표·\\", hasV(desc("'it''s'"), 3, '따옴표 값 안') && hasV(desc('"a\\nb"'), 3, '따옴표 값 안'));
ok("줄 안의 '---'(따옴표 안도)", hasV(desc('a --- b'), 3, "'---'") && hasV(desc("'a---b'"), 3, "'---'"));
for (const code of [0x09, 0x07, 0x0d, 0x7f, 0x80, 0x85, 0x9f, 0x2028, 0x2029, 0xfeff, 0xfffe, 0xffff, 0xd800]) {
  const hex = code.toString(16).toUpperCase().padStart(4, '0');
  ok(`금지 문자 U+${hex} → 3행`, hasV(desc(`a${String.fromCharCode(code)}b`), 3, `U+${hex}`));
}
ok('빈 줄·주석 줄·들여쓴 줄 → 한 줄 key: 값 아님', hasV(fm('', 'description: d'), 3, "'key: 값'")
  && hasV(fm('# c', 'description: d'), 3, "'key: 값'") && hasV(fm('description: d', '  더'), 4, "'key: 값'"));
ok('블록 목록 → 빈 값 + 목록 줄', hasV(fm('description: d', 'tools:', '  - Read'), 4, '비었다') && hasV(fm('description: d', 'tools:', '  - Read'), 5, "'key: 값'"));
ok('빈 값·빈 따옴표', hasV(fm('description: d', 'model:'), 4, '비었다') && hasV(desc("''"), 3, '비었다'));
ok('key:값(공백 없음)·영문자로 시작하지 않는 키', ['model:opus', '1key: x', '_k: x', 'a b: x'].every((l) => hasV(fm('description: d', l), 4, "'key: 값'")));
ok('중복 키', hasV(fm('description: d', 'name: y'), 4, '중복 키'));
ok('YAML 1.1 불리언·null 키(대소문자 무관)', ['on', 'yes', 'no', 'off', 'y', 'n', 'true', 'false', 'null', 'Yes', 'ON', 'True', 'NULL'].every((k) => hasV(fm('description: d', `${k}: v`), 4, '불리언')));
ok('평문 값 앞뒤의 NBSP·U+3000 → 3행', hasV(desc(`설명${IDEO}`), 3, '앞뒤') && hasV(desc(`${NBSP}설명`), 3, '앞뒤'));
ok('닫는 --- 뒤 줄바꿈 없음 → 4행', hasV('---\nname: x\ndescription: d\n---', 4, '줄바꿈'));
ok('name 이 YAML 1.2 숫자·불리언 → 2행', ['123', 'true', '0777', '0o17', '0x1F', '-0x1F', '+0o17', '1e5', '.5', '-1', '.inf'].every((v) => hasV(`---\nname: ${v}\ndescription: d\n---\n`, 2, '문자열이 아니')));
ok('null 형태 값(모든 키)', ['~', 'null', 'Null', 'NULL'].every((v) => hasV(fm('description: d', `model: ${v}`), 4, 'null')));
ok("YAML 1.1 특수 태그 값 '='·'<<'", ['=', '<<'].every((v) => hasV(fm('description: d', `model: ${v}`), 4, '특수 태그')));
ok('날짜 형태 값(잘못된 날짜는 파싱 실패)', ['2026-13-45', '2026-10-01', '2026-1-1 10:20:30'].every((v) => hasV(desc(v), 3, '날짜')));
ok("'=x'·'<<x'·날짜 뒤 글자 → 평문 그대로", ['=x', '<<x', '2026-10-01 도입'].every((v) => fieldsOf(desc(v))?.description === v));
ok('frontmatter 없음', hasV('name: x\ndescription: d\n', 1, 'frontmatter 없음') && hasV('--- \nname: x\ndescription: d\n---\n', 1, 'frontmatter 없음'));
ok('닫힘 없음', hasV('---\nname: x\ndescription: d\n', 1, '닫힘 없음'));
ok('name·description 누락', hasV('---\nname: x\n---\n', 1, "'description' 이 없다") && hasV('---\ndescription: d\n---\n', 1, "'name' 이 없다"));

// ---- CLI ----
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'frontmatter-lint-'));
function writeF(name, content) { const p = path.join(TMP, name); fs.writeFileSync(p, content); return p; }
function cli(args) {
  const r = spawnSync('node', [SCRIPT, ...args], { encoding: 'utf8', timeout: 20000 });
  return { code: r.status, out: r.stdout || '', err: r.stderr || '' };
}
const goodF = writeF('good.md', desc('설명'));
const badF = writeF('bad.md', OLD_C_FILE);
const cp949F = writeF('cp949.md', Buffer.concat([Buffer.from('---\nname: x\ndescription: '), Buffer.from([0xc7, 0xd1]), Buffer.from('\n---\n')]));
ok('CLI 통과 → exit 0·무출력', (() => { const r = cli([goodF]); return r.code === 0 && r.out === '' && r.err === ''; })());
ok('CLI 위반 → exit 1·<파일>:<줄>:', (() => { const r = cli([badF]); return r.code === 1 && r.out.startsWith(`${badF}:3: `); })());
ok('CLI 여러 파일 → exit 1·위반 파일만', (() => { const r = cli([goodF, badF]); return r.code === 1 && r.out.includes(badF) && !r.out.includes(goodF); })());
ok('CLI 읽기 실패 → exit 1·<파일>:1:', (() => { const p = path.join(TMP, 'nope.md'); const r = cli([p]); return r.code === 1 && r.out.startsWith(`${p}:1: `); })());
ok('CLI 잘못된 UTF-8(CP949) → exit 1', (() => { const r = cli([cp949F]); return r.code === 1 && r.out.startsWith(`${cp949F}:1: `) && r.out.includes('UTF-8'); })());
ok('CLI 인자 0개 → exit 2·사용법', (() => { const r = cli([]); return r.code === 2 && r.err.includes('사용'); })());
const bom1F = writeF('bom1.md', BOM + desc('설명'));
const bom2F = writeF('bom2.md', BOM + BOM + desc('설명'));
ok('CLI BOM 1개 → exit 0, 2개 → exit 1·frontmatter 없음(Claude Code 는 하나만 벗긴다)',
  (() => { const a = cli([bom1F]); const b = cli([bom2F]); return a.code === 0 && b.code === 1 && b.out.includes('frontmatter 없음'); })());

fs.rmSync(TMP, { recursive: true, force: true });
console.log(fail === 0 ? 'ALL PASS' : `${fail} FAIL`);
process.exit(fail === 0 ? 0 : 1);
