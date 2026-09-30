#!/usr/bin/env node
// frontmatter-lint.js — skill·agent frontmatter 가 모든 소비자에서 같게 읽히는 형식인지 판정한다(순수 함수 + CLI, hook 아님).
// scripts/verify.sh syntax 축과 skills/improve/improve.sh 점검 4 가 부른다.
//
// 소비자: Claude Code(엄격 YAML 파싱이 실패하면 값을 따옴표로 감싸 한 번 더 파싱하고 — CRLF 파일에서는 이 재시도도
// 실패한다 — 끝내 실패하면 필드를 경고 없이 버린다), YAML 파서 일반, scripts/bootstrap/sync_codex_agents.py(agents —
// 한 줄 `key: 값` 만 받고 따옴표를 unescape 하지 않는다). 표준 라이브러리에 YAML 파서가 없어 YAML 을 해석하지 않고,
// 모든 소비자가 같게 읽는 한 줄 형식만 통과시킨다 — 유효한 YAML 이어도 이 밖이면 거부한다. 허용 형식의 정본은 이 목록이다:
//   - 첫 줄이 정확히 `---` 이고 다음의 정확한 `---` 줄까지가 frontmatter 이며 그 뒤에 줄바꿈이 있다.
//     BOM 은 하나만 벗기고(Claude Code 와 같다) CRLF 는 LF 로 본다.
//   - 그 사이 모든 줄이 `key: 값` 이다. key 는 [A-Za-z][A-Za-z0-9_-]*, 값은 비지 않는다(빈 줄·주석·목록·여러 줄 값 없음).
//   - 값은 평문이거나 한 쌍의 '…'·"…" 이다. 따옴표 값 안에는 그 따옴표와 \ 가 없다.
//   - 평문은 YAML 지시자(, [ ] { } # & * ! | > % @ `)로 시작하지 않고, - ? : 로 시작하면 바로 뒤가 공백이거나 값의
//     끝이 아니다. 안에 ': '·' #' 가 없고(매핑으로 읽히거나 뒤가 주석으로 잘린다) ':' 로 끝나지 않으며, 앞뒤에
//     공백 문자(NBSP·U+3000 등 — sync 는 벗기고 YAML 은 남긴다)가 없다.
//   - 어느 줄에도 '---'(Claude Code 는 줄 가운데의 --- 에서도 frontmatter 를 끝낸다), 탭·제어문자·DEL·U+0085·
//     U+2028·U+2029·U+FEFF·U+FFFE·U+FFFF·서로게이트·lone CR(파서마다 다르게 읽는다)이 없다.
//   - 중복 키, YAML 1.1 에서 불리언·null 로 읽히는 키(대소문자 무관), null(~·null)·특수 태그(=·<<)·날짜로 읽히는
//     평문 값이 없고 name·description 이 있다. name 은 YAML 1.2 의 숫자·불리언 형태가 아니다(Claude Code 가
//     문자열이 아닌 name 을 거부한다). 그 밖의 타입 해석 차이(yes·1:20·0b101 — Claude Code 는 문자열, PyYAML 은
//     다른 타입)와 밑줄 숫자 형태(0x_·._ — PyYAML·ruamel 이 실패한다)는 보지 않는다.
'use strict';

const REQUIRED_KEYS = ['name', 'description'];
const KEY = /^([A-Za-z][A-Za-z0-9_-]*):/;
const KEY_LINE = new RegExp(`${KEY.source}(?: +(.*))?$`);
const BOOL_NULL_KEYS = new Set(['y', 'n', 'yes', 'no', 'on', 'off', 'true', 'false', 'null']);
const NULL_VALUES = new Set(['~', 'null', 'Null', 'NULL']);
const INDICATORS = new Set([',', '[', ']', '{', '}', '#', '&', '*', '!', '|', '>', '%', '@', '`']);
// YAML 1.1 value·merge 태그로 읽혀 PyYAML·ruamel 이 모두 실패하는 값.
const SPECIAL_TAG_VALUES = new Set(['=', '<<']);
// YAML 1.1 timestamp — 날짜로 읽히고, 없는 날짜(2026-13-45)면 파싱이 실패한다.
const TIMESTAMP = /^(?:\d{4}-\d\d-\d\d|\d{4}-\d\d?-\d\d?(?:[Tt]| +)\d\d?:\d\d:\d\d(?:\.\d*)?(?: *(?:Z|[-+]\d\d?(?::\d\d)?))?)$/;
// YAML 1.2 core 의 불리언·정수·실수(부호 붙은 16진·8진도 Claude Code 는 숫자로 읽는다).
const CORE_NON_STRING = /^(?:true|True|TRUE|false|False|FALSE|[-+]?[0-9]+|[-+]?0o[0-7]+|[-+]?0x[0-9a-fA-F]+|[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$/;

const hex = (c) => c.toString(16).toUpperCase().padStart(4, '0');

// 탭·C0 제어문자(lone CR 포함)·DEL·C1(NEL 포함)·U+2028·U+2029·U+FEFF·U+FFFE·U+FFFF·서로게이트 중
// 첫 글자의 코드 포인트, 없으면 null.
function forbiddenCode(line) {
  for (const ch of line) {
    const c = ch.codePointAt(0);
    if (c <= 0x1f || (c >= 0x7f && c <= 0x9f) || (c >= 0xd800 && c <= 0xdfff)
      || c === 0x2028 || c === 0x2029 || c === 0xfeff || c === 0xfffe || c === 0xffff) return c;
  }
  return null;
}

// 한 줄을 { key, value } 또는 { error } 로 읽는다.
function readLine(line) {
  const bad = forbiddenCode(line);
  if (bad !== null) return { error: `허용하지 않는 문자 U+${hex(bad)} — 파서마다 다르게 읽는다` };
  if (line.includes('---')) return { error: "줄 안의 '---' — Claude Code 는 여기서 frontmatter 가 끝난 것으로 읽는다" };
  const m = line.match(KEY_LINE);
  if (!m) {
    return { error: "한 줄 'key: 값' 이 아니다 — key 는 영문자로 시작해 영문자·숫자·_·- 만 쓰고 콜론 뒤에 공백이 온다. 빈 줄·주석·목록·여러 줄 값은 쓰지 않는다" };
  }
  const key = m[1];
  if (BOOL_NULL_KEYS.has(key.toLowerCase())) return { error: `YAML 1.1 에서 불리언·null 로 읽히는 키 '${key}'` };
  const value = (m[2] || '').replace(/ +$/, '');
  if (value === '') return { error: '값이 비었다' };

  const q = value[0];
  if (q === "'" || q === '"') {
    if (value.length < 2 || value[value.length - 1] !== q) {
      return { error: '따옴표 값은 한 쌍의 따옴표로 끝나야 한다 — 닫는 따옴표 뒤에 글자를 두지 않는다' };
    }
    const inner = value.slice(1, -1);
    if (inner.includes(q) || inner.includes('\\')) {
      return { error: '따옴표 값 안에 그 따옴표나 \\ 를 쓰지 않는다 — YAML 과 sync_codex_agents 가 다르게 읽는다' };
    }
    if (inner === '') return { error: '값이 비었다' };
    return { key, value: inner };
  }

  if (INDICATORS.has(q) || ('-?:'.includes(q) && (value.length === 1 || value[1] === ' '))) {
    return { error: `평문 값이 YAML 지시자 '${q}' 로 시작한다 — 따옴표로 감싼다` };
  }
  const edge = value.match(/^\s|\s$/);
  if (edge) return { error: `평문 값 앞뒤의 공백 문자 U+${hex(edge[0].codePointAt(0))} — sync_codex_agents 는 벗기고 YAML 은 남긴다` };
  if (value.includes(': ')) return { error: "평문 값 안의 ': ' — YAML 이 매핑으로 읽는다. 따옴표로 감싸거나 다른 문장부호를 쓴다" };
  if (value.endsWith(':')) return { error: "평문 값이 ':' 로 끝난다 — 따옴표로 감싼다" };
  if (value.includes(' #')) return { error: "평문 값 안의 ' #' — YAML 이 뒤를 주석으로 잘라낸다. 따옴표로 감싼다" };
  if (NULL_VALUES.has(value)) return { error: `null 로 읽히는 값 '${value}'` };
  if (SPECIAL_TAG_VALUES.has(value)) return { error: `YAML 1.1 특수 태그로 읽혀 파싱에 실패하는 값 '${value}' — 따옴표로 감싼다` };
  if (TIMESTAMP.test(value)) return { error: 'YAML 이 날짜로 읽는 값(없는 날짜면 파싱 실패) — 따옴표로 감싼다' };
  if (key === 'name' && CORE_NON_STRING.test(value)) {
    return { error: 'name 이 YAML 에서 숫자·불리언으로 읽혀 문자열이 아니다 — Claude Code 가 거부한다. 따옴표로 감싼다' };
  }
  return { key, value };
}

// → { fields: 읽은 값(위반 없는 줄만), violations: [{ line, message }] }. 파일 단위 위반은 1행.
function lintFrontmatter(text) {
  const fields = {};
  const violations = [];
  let src = String(text);
  if (src.charCodeAt(0) === 0xfeff) src = src.slice(1);
  const lines = src.replace(/\r\n/g, '\n').split('\n');
  if (lines[0] !== '---') {
    violations.push({ line: 1, message: 'frontmatter 없음 — 첫 줄이 정확히 --- 가 아니다' });
    return { fields, violations };
  }
  const end = lines.indexOf('---', 1);
  if (end === -1) {
    violations.push({ line: 1, message: 'frontmatter 닫힘 없음 — 두 번째 --- 줄이 없다' });
    return { fields, violations };
  }
  if (end === lines.length - 1) {
    violations.push({ line: end + 1, message: '닫는 --- 뒤에 줄바꿈이 없다 — sync_codex_agents 는 frontmatter 가 닫히지 않았다고 본다' });
  }
  const firstLine = new Map(); // key → 처음 나온 줄(값이 위반이어도 키는 있는 것으로 본다)
  for (let i = 1; i < end; i++) {
    const n = i + 1;
    const key = (lines[i].match(KEY) || [])[1];
    if (key !== undefined && firstLine.has(key)) {
      violations.push({ line: n, message: `중복 키 '${key}' (${firstLine.get(key)}행)` });
      continue;
    }
    if (key !== undefined) firstLine.set(key, n);
    const r = readLine(lines[i]);
    if (r.error) violations.push({ line: n, message: r.error });
    else fields[r.key] = r.value;
  }
  for (const key of REQUIRED_KEYS) {
    if (!firstLine.has(key)) violations.push({ line: 1, message: `'${key}' 이 없다` });
  }
  return { fields, violations };
}

module.exports = { lintFrontmatter };

// ---- CLI ----
if (require.main === module) {
  const fs = require('fs');
  const files = process.argv.slice(2);
  if (files.length === 0) {
    console.error('사용: node scripts/frontmatter-lint.js <파일>...');
    process.exit(2);
  }
  // 관대한 'utf8' 디코딩은 잘못된 바이트(CP949 등)를 U+FFFD 로 바꿔 통과시킨다. BOM 은 lintFrontmatter 가
  // 하나만 벗기므로 디코더는 남긴다(둘 다 벗기면 BOM 두 개 — Claude Code 는 frontmatter 를 못 찾는다 — 가 통과한다).
  const decoder = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true });
  let bad = 0;
  for (const f of files) {
    let text;
    try {
      text = decoder.decode(fs.readFileSync(f));
    } catch (e) {
      bad++;
      const why = e.code === 'ERR_ENCODING_INVALID_ENCODED_DATA' ? 'UTF-8 이 아니다' : `읽기 실패 — ${e.code || e.message}`;
      console.log(`${f}:1: ${why}`);
      continue;
    }
    const { violations } = lintFrontmatter(text);
    if (violations.length) bad++;
    for (const { line, message } of violations) console.log(`${f}:${line}: ${message}`);
  }
  process.exit(bad ? 1 : 0);
}
