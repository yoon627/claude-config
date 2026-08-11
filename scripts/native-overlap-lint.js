#!/usr/bin/env node
// native-overlap-lint — 네이티브 중복 대장의 *신선도*만 판정하는 순수 함수 + CLI
// (hook 아님. `skills/improve/improve.sh` 점검 9 가 호출).
//
// 판정하는 것: 대장 frontmatter 의 `checked`(마지막 점검일) 가 임계를 넘었나, deep 이면 다음
// 조회에 쓸 delta 창(`checked_version` → 설치 버전)은 무엇인가.
// 판정하지 않는 것: 중복 여부 자체. 그건 changelog 를 읽는 LLM 몫(SKILL.md §6) — 여기는
// "언제 다시 볼까"만 답한다.
//
// 전 경로가 informational: 위반이 아니라 리마인더라 error/warn 을 만들지 않는다
// (improve.sh:3 심각도 정의 — warn 은 정합성 위반용). 불량 입력도 사실만 적고 skip.
'use strict';

const DEFAULT_MAX_AGE_DAYS = 45;
const DAY_MS = 86400000;

function frontmatterValue(fmBody, key) {
  const m = new RegExp('^' + key + ':[ \\t]*(\\S+)', 'm').exec(fmBody);
  return m ? m[1] : '';
}

// "YYYY-MM-DD" → epoch ms(UTC 자정). 불량이면 null.
// 왕복 대조가 필요한 이유: Date.parse('2026-02-30T00:00:00Z') 는 NaN 이 아니라 03-02 로
// 롤오버한다 — 오타 날짜가 조용히 다른 날로 통과해 신선도가 틀어진다.
function parseIsoDate(s) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return null;
  const ms = Date.parse(s + 'T00:00:00Z');
  if (Number.isNaN(ms)) return null;
  return new Date(ms).toISOString().slice(0, 10) === s ? ms : null;
}

// 로컬 달력 기준 오늘("YYYY-MM-DD").
// `checked` 는 사람이 로컬 달력으로 적는 값이라 UTC instant 와 직접 비교하면 안 된다 —
// UTC+9 에서 로컬 오늘 오전은 아직 UTC 어제라, 오늘 적은 날짜가 "미래"로 판정된다.
// 양쪽을 로컬 날짜 문자열 → UTC 자정으로 맞춰야 일수 차가 정확해진다.
function localToday(d) {
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

// "2.1.222"·"v2.1.222" 비교. 자리수 다르면 없는 자리는 0. 비교 불가면 null.
// 정규식을 끝까지 앵커하는 이유: 앵커가 없으면 "2.1.222-beta" 가 "2.1.222" 와 같다고 나와
// "변화 없음"을 단정한다 — 창이 있는데 changelog 조회를 건너뛰는 게 최악이라, 애매하면
// 0(같음)이 아니라 null(수동 판단)로 빠뜨린다.
function compareVersions(a, b) {
  const parse = (v) => {
    const m = /^v?(\d+)\.(\d+)(?:\.(\d+))?$/.exec(String(v || '').trim());
    return m ? [Number(m[1]), Number(m[2]), Number(m[3] || 0)] : null;
  };
  const pa = parse(a);
  const pb = parse(b);
  if (!pa || !pb) return null;
  for (let i = 0; i < 3; i++) {
    if (pa[i] !== pb[i]) return pa[i] < pb[i] ? -1 : 1;
  }
  return 0;
}

function deltaWindowLine(fmBody, installedVersion) {
  const checkedVersion = frontmatterValue(fmBody, 'checked_version');
  if (!checkedVersion) return 'delta 창: 대장에 checked_version 없음 → changelog 전수 조회 필요';
  if (!installedVersion) return `delta 창: 설치 버전 미확인 → 마지막 점검 ${checkedVersion} 이후 전부 조회`;

  const cmp = compareVersions(installedVersion, checkedVersion);
  if (cmp === null) return `delta 창: 버전 비교 불가(대장 ${checkedVersion} / 설치 ${installedVersion}) → 수동 판단`;
  if (cmp < 0) {
    // 다운그레이드·다머신·자동업데이트 꺼짐. 설치본이 뒤처졌다고 네이티브가 안 변한 건 아니다.
    return `delta 창: 설치 버전(${installedVersion})이 마지막 점검 버전(${checkedVersion})보다 낮음 ` +
      '— 다운그레이드/다머신/자동업데이트 꺼짐. changelog 최신분 기준으로 조회할 것';
  }
  if (cmp === 0) {
    return `delta 창: 없음 — 마지막 점검 이후 설치 버전 변화 없음(${checkedVersion}). ` +
      "단 '버전 변화 없음 ≠ 중복 없음'(설치본이 최신 릴리스보다 뒤처졌을 수 있음)";
  }
  return `delta 창: ${checkedVersion} → ${installedVersion} (이 구간 changelog 만 읽으면 됨)`;
}

// 반환: 사람이 읽을 메시지 배열(프리픽스 없음). 호출측이 [info] 를 붙인다.
// today 는 "YYYY-MM-DD"(로컬 달력) — 주입받아야 테스트가 실행 시각·타임존에 흔들리지 않는다.
function nativeOverlapStatus({ text, today, installedVersion, maxAgeDays, deep }) {
  // 유효한 임계 = 1 이상 유한 정수. 그 외(0·음수·비숫자·빈값·Infinity)는 전부 기본값으로 —
  // 오타 임계를 1일로 clamp 하면 매 실행 리마인더가 떠 오히려 무시하게 된다.
  const requested = Math.floor(Number(maxAgeDays));
  const max = Number.isFinite(requested) && requested >= 1 ? requested : DEFAULT_MAX_AGE_DAYS;
  const t = String(text || '')
    .replace(/^\uFEFF/, '')
    .replace(/\r\n/g, '\n');

  const fm = /^---\n([\s\S]*?)\n---/.exec(t);
  if (!fm) return ['대장 frontmatter 없음 → 신선도 판정 skip'];
  const fmBody = fm[1];

  const checked = frontmatterValue(fmBody, 'checked');
  const parsed = parseIsoDate(checked);
  if (parsed === null) {
    return [`대장 checked 날짜 불량('${checked}') → 신선도 판정 skip`];
  }

  const todayMs = parseIsoDate(today);
  if (todayMs === null) return [`오늘 날짜 판정 불가('${today}') → 신선도 판정 skip`];

  // -1 은 미래로 보지 않고 오늘로 친다: 대장을 UTC+n 머신에서 쓰고 UTC-n 머신에서 읽으면
  // 로컬 달력이 하루 어긋나, 방금 적은 날짜가 "미래 → skip" 이 되어 리마인더가 하루 무음이 된다.
  const rawAge = Math.round((todayMs - parsed) / DAY_MS);
  const age = rawAge === -1 ? 0 : rawAge;
  const lines = [];
  if (age < 0) {
    lines.push(`대장 checked 가 미래(${checked}) → 신선도 판정 skip`);
  } else if (age > max) {
    lines.push(
      `네이티브 중복 점검 ${age}일 경과(임계 ${max}일) → \`improve.sh deep\` + SKILL §6 으로 재판정 권고`,
    );
  } else {
    lines.push(`네이티브 중복 점검 최신(${age}일 전, 임계 ${max}일)`);
  }

  if (deep) lines.push(deltaWindowLine(fmBody, installedVersion));
  return lines;
}

module.exports = { nativeOverlapStatus, compareVersions, localToday };

// ---- CLI: native-overlap-lint.js <ledger-path> [deep] ----
// 항상 exit 0 — improve.sh 의 "부분 실패는 그 점검만 skip, 스크립트는 exit 0" 정책(improve.sh:6).
if (require.main === module) {
  const fs = require('fs');
  const [file, deepArg] = process.argv.slice(2);
  const emit = (m) => console.log(`[info] ${m}`);

  let text;
  try {
    text = fs.readFileSync(file, 'utf8');
  } catch {
    emit(`네이티브 중복 대장 없음(${file}) → skip. \`improve.sh deep\` 으로 초기 판정 후 승인·/wiki ingest 로 생성`);
    process.exit(0);
  }

  for (const line of nativeOverlapStatus({
    text,
    today: localToday(new Date()),
    installedVersion: process.env.CLAUDE_IMPROVE_CC_VERSION || '',
    maxAgeDays: process.env.CLAUDE_IMPROVE_NATIVE_MAX_AGE_DAYS,
    deep: deepArg === 'deep',
  })) {
    emit(line);
  }
  process.exit(0);
}
