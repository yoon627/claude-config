#!/usr/bin/env node
// native-overlap-lint.js 회귀 테스트 — 순수 nativeOverlapStatus() + CLI. 무프레임워크·결정적.
// 오늘은 today("YYYY-MM-DD") 주입으로 고정 — 날짜 경계 테스트가 실행일·타임존에 흔들리지 않게.
'use strict';
const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { nativeOverlapStatus, compareVersions, localToday } = require('./native-overlap-lint.js');
const SCRIPT = path.join(__dirname, 'native-overlap-lint.js');

let fail = 0;
function ok(name, cond) { if (!cond) fail++; console.log(`${cond ? 'PASS' : 'FAIL'} ${name}`); }

const NOW = '2026-08-06';
function ledger(checked, checkedVersion) {
  return [
    '---',
    'title: native-overlap-ledger',
    'category: decision',
    ...(checked === null ? [] : [`checked: ${checked}`]),
    ...(checkedVersion === null || checkedVersion === undefined ? [] : [`checked_version: ${checkedVersion}`]),
    '---',
    '',
    '본문',
  ].join('\n');
}
function run(text, opts) {
  return nativeOverlapStatus({ text, today: NOW, installedVersion: '', maxAgeDays: undefined, deep: false, ...(opts || {}) });
}
function joined(text, opts) { return run(text, opts).join(' | '); }

// ---- 신선도 판정 ----
{
  ok('임계 내 → 최신', joined(ledger('2026-08-01', '2.1.222')).includes('최신(5일 전, 임계 45일)'));
  // 회귀: checked=오늘 이 "미래"로 판정되던 버그(로컬 달력 날짜 vs UTC instant 비교).
  ok('checked = 오늘 → 0일 전(미래 아님)', (() => {
    const s = joined(ledger(NOW, '2.1.222'));
    return s.includes('최신(0일 전') && !s.includes('미래');
  })());
  ok('checked = 어제 → 1일 전', joined(ledger('2026-08-05', '2.1.222')).includes('최신(1일 전'));
  ok('임계 초과 → 재판정 권고', joined(ledger('2026-05-01', '2.1.222')).includes('경과(임계 45일)'));
  ok('임계 경계(정확히 45일) → 최신', joined(ledger('2026-06-22', '2.1.222')).includes('최신(45일 전'));
  ok('임계 경계+1(46일) → 경과', joined(ledger('2026-06-21', '2.1.222')).includes('46일 경과'));
  ok('미래 날짜 → skip(경과 아님)', (() => {
    const s = joined(ledger('2027-01-01', '2.1.222'));
    return s.includes('미래') && s.includes('skip') && !s.includes('경과');
  })());
  // 회귀: 다머신 TZ 차로 하루 앞선 checked 는 미래가 아니라 오늘로 친다(리마인더 무음 방지).
  ok('checked = 내일(-1일) → 오늘로 흡수', (() => {
    const s = joined(ledger('2026-08-07', '2.1.222'));
    return s.includes('최신(0일 전') && !s.includes('미래');
  })());
  ok('checked = 모레(-2일) → 미래 skip', joined(ledger('2026-08-08', '2.1.222')).includes('미래'));
}

// ---- 불량 입력 fail-safe (전부 skip, 예외 없음) ----
{
  ok('frontmatter 없음 → skip', joined('본문만 있음').includes('frontmatter 없음'));
  ok('checked 키 없음 → 날짜 불량 skip', joined(ledger(null, '2.1.222')).includes('날짜 불량'));
  // 회귀: `^checked:` 가 `checked_version:` 을 오매치하면 안 된다. 값이 날짜라 오매치 시
  // "최신"이 나와 즉시 FAIL 된다(값이 버전 문자열이면 양쪽 다 '날짜 불량'이라 구분이 안 됨).
  ok('checked 없고 checked_version 이 날짜여도 오매치 안 함', (() => {
    const s = joined(ledger(null, '2026-08-01'));
    return s.includes('날짜 불량') && !s.includes('최신');
  })());
  ok('checked 형식 불량 → skip', joined(ledger('2026/08/01', '2.1.222')).includes('날짜 불량'));
  ok('checked 비날짜 문자열 → skip', joined(ledger('yesterday', '2.1.222')).includes('날짜 불량'));
  ok('존재하지 않는 날짜(2026-02-30) → skip', joined(ledger('2026-02-30', '2.1.222')).includes('날짜 불량'));
  ok('빈 text → skip(크래시 없음)', run('').length === 1);
  ok('null text → skip(크래시 없음)', run(null).length === 1);
  ok('today 불량 → skip', joined(ledger('2026-08-01', '2.1.222'), { today: 'nope' }).includes('오늘 날짜 판정 불가'));
  ok('CRLF 정규화', joined(ledger('2026-08-01', '2.1.222').replace(/\n/g, '\r\n')).includes('최신'));
  ok('BOM 정규화', joined('﻿' + ledger('2026-08-01', '2.1.222')).includes('최신'));
}

// ---- maxAgeDays env clamp ----
{
  // 규칙: 유효 = 1 이상 유한 정수. 그 외는 전부 기본 45(1로 clamp 하지 않는다 — 매 실행 리마인더 방지).
  const age = (v) => joined(ledger('2026-08-01', '2.1.222'), { maxAgeDays: v });
  ok('maxAgeDays=10 적용', joined(ledger('2026-07-01', '2.1.222'), { maxAgeDays: '10' }).includes('임계 10일'));
  ok('maxAgeDays=0 → 기본 45', age('0').includes('임계 45일'));
  ok('maxAgeDays 비숫자 → 기본 45', age('abc').includes('임계 45일'));
  ok('maxAgeDays 빈값 → 기본 45', age('').includes('임계 45일'));
  ok('maxAgeDays 음수 → 기본 45', age('-5').includes('임계 45일'));
  ok('maxAgeDays Infinity → 기본 45', age('Infinity').includes('임계 45일'));
  ok('maxAgeDays 소수 → 내림 정수', age('7.9').includes('임계 7일'));
  ok('maxAgeDays undefined → 기본 45', age(undefined).includes('임계 45일'));
}

// ---- deep: delta 창 ----
{
  const d = (opts) => joined(ledger('2026-08-01', opts && 'cv' in opts ? opts.cv : '2.1.200'), { deep: true, installedVersion: opts ? opts.iv : '' });
  ok('deep 아니면 delta 창 없음', !joined(ledger('2026-08-01', '2.1.200')).includes('delta 창'));
  ok('deep + 정상 → 구간 표시', d({ iv: '2.1.222' }).includes('delta 창: 2.1.200 → 2.1.222'));
  ok('deep + 동일 버전 → 변화 없음 + 경고문', (() => {
    const s = d({ iv: '2.1.200' });
    return s.includes('변화 없음') && s.includes('≠ 중복 없음');
  })());
  ok('deep + 설치 버전 미확인 → 전부 조회', d({ iv: '' }).includes('이후 전부 조회'));
  ok('deep + checked_version 없음 → 전수 조회', d({ cv: null, iv: '2.1.222' }).includes('전수 조회'));
  ok('deep + 버전 역전 → 사실 표기', (() => {
    const s = d({ cv: '2.1.222', iv: '2.1.200' });
    return s.includes('보다 낮음') && s.includes('최신분 기준');
  })());
  ok('deep + 비교 불가 버전 → 수동 판단', d({ cv: 'unknown', iv: '2.1.222' }).includes('비교 불가'));
  ok('deep 라인은 신선도 라인에 더해짐(2줄)', run(ledger('2026-08-01', '2.1.200'), { deep: true, installedVersion: '2.1.222' }).length === 2);
}

// ---- localToday (로컬 달력 — UTC 변환 아님) ----
{
  ok('localToday 로컬 필드 사용', localToday(new Date(2026, 0, 3, 1, 30)) === '2026-01-03');
  ok('localToday 0 패딩', localToday(new Date(2026, 8, 9, 23, 59)) === '2026-09-09');
}

// ---- compareVersions ----
{
  ok('compare 같음', compareVersions('2.1.222', '2.1.222') === 0);
  ok('compare 큼', compareVersions('2.1.223', '2.1.222') === 1);
  ok('compare 작음', compareVersions('2.1.221', '2.1.222') === -1);
  ok('compare minor 우선', compareVersions('2.2.0', '2.1.999') === 1);
  ok('compare 패치 생략 = 0', compareVersions('2.1', '2.1.0') === 0);
  ok('compare 불량 → null', compareVersions('x', '2.1.0') === null);
  ok('compare 빈값 → null', compareVersions('', '2.1.0') === null);
  ok('compare v 접두 허용', compareVersions('v2.1.222', '2.1.222') === 0);
  // 회귀: 앵커 없으면 suffix 가 잘려 "같음"으로 단정 → "변화 없음"이 되어 조회를 건너뛴다.
  ok('compare suffix → null(같음 단정 금지)', compareVersions('2.1.222-beta', '2.1.222') === null);
  ok('compare 4자리 → null', compareVersions('2.1.222.1', '2.1.222') === null);
}

// ---- CLI ----
{
  const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'nol-'));
  const writeF = (name, text) => { const p = path.join(TMP, name); fs.writeFileSync(p, text); return p; };
  const cli = (args, env) => {
    const r = spawnSync('node', [SCRIPT, ...args], { env: { ...process.env, ...(env || {}) }, encoding: 'utf8', timeout: 20000 });
    return { code: r.status, out: (r.stdout || '') + (r.stderr || '') };
  };

  // fixture 도 localToday 기준으로 만든다 — CLI 가 로컬 달력으로 비교하는데 fixture 를 UTC
  // 날짜로 만들면 UTC 음수 오프셋 TZ 의 특정 시간대에서만 age 가 1 어긋나 flaky 해진다.
  const daysAgo = (n) => localToday(new Date(Date.now() - n * 86400000));
  const fresh = writeF('fresh.md', ledger(daysAgo(2), '2.1.222'));
  const stale = writeF('stale.md', ledger('2020-01-01', '2.1.100'));

  ok('CLI 정상 → exit 0 · [info] 프리픽스', (() => {
    const r = cli([fresh]);
    return r.code === 0 && r.out.startsWith('[info] ') && r.out.includes('최신');
  })());
  ok('CLI 경과 → exit 0 · 권고문', (() => {
    const r = cli([stale]);
    return r.code === 0 && r.out.includes('경과') && r.out.includes('deep');
  })());
  ok('CLI 미존재 경로 → exit 0 · 대장 없음 안내', (() => {
    const r = cli([path.join(TMP, 'nope.md')]);
    return r.code === 0 && r.out.includes('대장 없음') && r.out.includes('/wiki ingest');
  })());
  ok('CLI 인자 0개 → exit 0(크래시 없음)', cli([]).code === 0);
  ok('CLI deep 인자 → delta 창 출력', (() => {
    const r = cli([fresh, 'deep'], { CLAUDE_IMPROVE_CC_VERSION: '2.1.230' });
    return r.code === 0 && r.out.includes('delta 창: 2.1.222 → 2.1.230');
  })());
  ok('CLI env 임계 반영', cli([fresh], { CLAUDE_IMPROVE_NATIVE_MAX_AGE_DAYS: '1' }).out.includes('경과(임계 1일)'));
  ok('CLI 출력 전부 [info] — error/warn 없음', (() => {
    const r = cli([stale, 'deep']);
    return !r.out.includes('[error]') && !r.out.includes('[warn]');
  })());

  fs.rmSync(TMP, { recursive: true, force: true });
}

// ---- improve.sh 점검 번호 계약 ----
// 기본 점검과 deep 전용 점검이 같은 번호를 쓰면 `== 9.` 이 두 번 찍혀 보고가 모호해진다 —
// 헤더 수열이 1..N 유일함을 CI 가 지킨다.
// 실행하지 않고 소스를 읽는다: 헤더가 전부 반복문 밖에서 한 줄에 하나씩 리터럴로 찍혀 소스 순서가
// deep 출력 순서다. 헤더처럼 보이는 줄이 그 모양(줄 전체가 `echo "== N. …"`)이 아니면 셀 수 없으니
// 실패시킨다. 반복문 안 헤더와 printf 인자로 쪼갠 헤더는 이 검사로 못 본다.
{
  const headerProblems = (src) => {
    const nums = [];
    const problems = [];
    for (const line of src.split(/\r?\n/)) {
      if (/^\s*#/.test(line) || !/== \d|["']== /.test(line)) continue;
      const m = /^\s*echo "== (\d+)\. [^"]*"\s*$/.exec(line);
      if (m) nums.push(Number(m[1]));
      else if (!/^\s*(\[[^\]]*\] && )?echo "== (요약|ci):[^"]*"\s*$/.test(line)) problems.push(`형식 밖 헤더: ${line.trim()}`);
    }
    if (nums.length === 0) problems.push('헤더 없음');
    else if (!nums.every((n, i) => n === i + 1)) problems.push(`번호가 1..N 이 아님: ${nums.join(',')}`);
    return { nums, problems };
  };
  const src = fs.readFileSync(path.join(__dirname, '..', 'skills/improve/improve.sh'), 'utf8');
  const real = headerProblems(src);
  ok(`improve.sh 점검 번호 1..N 유일 (${real.nums.join(',')})${real.problems.length ? ' — ' + real.problems.join('; ') : ''}`,
    real.problems.length === 0);

  const flags = (body) => headerProblems(body).problems.length > 0;
  const h = (n) => `echo "== ${n}. x =="`;
  ok('헤더 검사: 들여쓴 deep 헤더도 센다', !flags([h(1), `  ${h(2)}`].join('\n')));
  ok('헤더 검사: 같은 번호 두 번 → 실패', flags([h(1), h(9), h(9)].join('\n')));
  ok('헤더 검사: 번호 건너뜀 → 실패', flags([h(1), h(3)].join('\n')));
  ok('헤더 검사: 변수 번호 → 실패', flags([h(1), 'echo "== $n. x =="'].join('\n')));
  ok('헤더 검사: printf 헤더 → 실패', flags([h(1), "printf '== 2. x ==\\n'"].join('\n')));
  ok('헤더 검사: 작은따옴표 헤더 → 실패', flags([h(1), "echo '== 2. x =='"].join('\n')));
  ok('헤더 검사: 조건부 한 줄 헤더 → 실패', flags([h(1), `[ -n "$x" ] && ${h(2)}`].join('\n')));
  ok('헤더 검사: echo -e 헤더 → 실패', flags([h(1), 'echo -e "== 2. x =="'].join('\n')));
  ok('헤더 검사: 따옴표 없는 헤더 → 실패', flags([h(1), 'echo == 1. x ==', h(2)].join('\n')));
  ok('헤더 검사: 한 줄에 헤더 둘 → 실패', flags([`${h(1)}; ${h(1)}`, h(2)].join('\n')));
  ok('헤더 검사: 리다이렉션 헤더 → 실패', flags([h(1), `${h(2)} >&2`, h(3)].join('\n')));
  ok('헤더 검사: 요약 줄 뒤에 붙은 헤더 → 실패', flags([h(1), `echo "== 요약: x =="; ${h(1)}`].join('\n')));
  ok('헤더 검사: 주석 안 헤더는 세지 않음', !flags([h(1), `# ${h(1)}`].join('\n')));
  ok('헤더 검사: 요약·ci 줄은 허용', !flags([h(1), 'echo "== 요약: x =="', 'echo "== ci: x =="'].join('\n')));
  ok('헤더 검사: 헤더 0개 → 실패', flags('echo hi'));
}

console.log(fail === 0 ? 'ALL PASS' : `${fail} FAIL`);
process.exit(fail === 0 ? 0 : 1);
