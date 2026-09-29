#!/usr/bin/env node
// 추적 중인 모든 .ps1 이 UTF-8 BOM 으로 시작하는지 잠근다(.editorconfig `charset = utf-8-bom`).
//
// Windows PowerShell 5.1 은 BOM 없는 파일을 시스템 코드페이지(한국어 Windows 는 CP949)로 읽어
// 비ASCII 문자 뒤의 따옴표를 놓치고 파싱에 실패한다. install-hooks 가 설치하는 훅은 가드를
// `powershell`(5.1)로 부르므로, 가드가 BOM 을 잃으면 그 repo 의 커밋·push 가 전부 막힌다.
// pwsh 7 은 BOM 없이도 UTF-8 로 읽어 ps1 테스트로는 드러나지 않고, 도구로 편집하면
// .editorconfig 가 적용되지 않아 BOM 이 조용히 빠진다.
'use strict';
const assert = require('assert');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
// --others: a new ps1 must be caught before it is added, as verify.sh's other axes do.
const files = execFileSync('git', ['-C', root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard', '--', '*.ps1'],
  { encoding: 'utf8' }).split('\0').filter((f, i, all) => f && all.indexOf(f) === i && fs.existsSync(path.join(root, f)));
assert.ok(files.length > 0, 'git ls-files 가 .ps1 을 하나도 찾지 못했다');

const missing = files.filter((f) => {
  const head = fs.readFileSync(path.join(root, f)).subarray(0, 3);
  return !(head[0] === 0xef && head[1] === 0xbb && head[2] === 0xbf);
});
assert.deepStrictEqual(missing, [], `UTF-8 BOM 없는 .ps1: ${missing.join(', ')}`);
console.log(`ps1-encoding.test.js: ${files.length} files have a UTF-8 BOM`);
