#!/usr/bin/env node
// plan-lint — §10 plan 형식·참조 무결성 순수 판정 + CLI (hook 아님, CI·/improve·/c·/e 가 호출).
// 형식 정의의 정본은 CLAUDE.md §10, 이 파일은 기계로 검사할 수 있는 부분만 맡는다(의미 판정은 LLM 몫):
//   1 frontmatter 필수키(title/status/started/updated) non-empty
//   2 status ∈ {in_progress, blocked, done}
//   3 형식 판별(planFormat) 후 필수 H1 — 새 형식 # Goal/Tasks/Decisions/Blockers, 옛 형식 # Goal/Progress/Next/
//     Decisions/Key Files/Blockers. 옛 형식 전용 섹션과 # Tasks 가 함께 있으면 혼재 위반.
//   4 새 형식 # Tasks: 코드펜스 밖 체크박스 1개 이상, 체크된 항목(하위 항목 포함)은 (YYYY-MM-DD)
//     새 형식 본문의 작업 기록 섹션(LOG_SECTIONS)은 위반 — 같은 폴더의 <slug>-log.md 에 둔다
//   5 Acceptance 참조 무결성: 본문의 "Acceptance <N>"(N=숫자 또는 ①-⑳) 참조 ↔ # Acceptance top-level 항목 수
// kill-switch: CLAUDE_PLAN_LINT_OFF=1 → CLI no-op exit 0.
'use strict';

const REQUIRED_KEYS = ['title', 'status', 'started', 'updated'];
const STATUS_VALUES = ['in_progress', 'blocked', 'done'];
const SECTIONS = {
  new: ['Goal', 'Tasks', 'Decisions', 'Blockers'],
  old: ['Goal', 'Progress', 'Next', 'Decisions', 'Key Files', 'Blockers'],
};
// 옛 형식에만 있는 섹션 — 이것이 있고 # Tasks 가 없을 때만 옛 형식으로 본다(기본값은 새 형식).
const OLD_ONLY = ['Progress', 'Next', 'Key Files', 'Intent'];
// 작업 중 쌓이는 기록 — 새 형식은 plan 밖 log 파일에 둔다(옛 형식 plan 은 본문에 둔 채 끝낸다).
const LOG_SECTIONS = ['Review Disposition', 'Deferred', 'Workflow Findings'];
const COUNTERS = ['개', '종', '줄']; // 계량사 — 뒤따르면 참조 아님
const CHECKBOX = /^\s*[-*] \[([ xX])\] /;
const DATE = /\(\d{4}-\d{2}-\d{2}\)/;

// 코드펜스 라인(여는·닫는 줄 포함) 여부. 목록 아래 들여 쓴 펜스도 센다. 닫는 펜스는 같은 문자로
// 여는 펜스 이상 길이이고 info string 이 없어야 한다(```` 안의 ``` 나 ```js 예시가 펜스를 닫지 않게).
function fencedLines(lines) {
  const fenced = new Array(lines.length).fill(false);
  let open = null;
  for (let i = 0; i < lines.length; i++) {
    if (!open) {
      const f = lines[i].match(/^\s*(`{3,}|~{3,})/);
      if (f) open = f[1];
      fenced[i] = !!f;
      continue;
    }
    const c = lines[i].match(/^\s*(`{3,}|~{3,})\s*$/);
    if (c && c[1][0] === open[0] && c[1].length >= open.length) open = null;
    fenced[i] = true;
  }
  return fenced;
}

// H1(`# Title`) 섹션들을 {title, bodyStart, bodyEnd}(라인 인덱스, bodyEnd 배타) 로.
// fmEnd 이하(frontmatter 블록)와 코드펜스 안은 제외 — YAML 주석이나 붙여 넣은 형식 예시가
// 본문 H1 로 오인되면 형식 판별이 뒤집힌다.
function h1Sections(lines, fmEnd, fenced) {
  const heads = [];
  for (let i = 0; i < lines.length; i++) {
    if (i <= fmEnd || fenced[i]) continue;
    const m = lines[i].match(/^# (.+?)\s*$/);
    if (m) heads.push({ title: m[1].trim(), line: i });
  }
  return heads.map((h, idx) => ({
    title: h.title,
    bodyStart: h.line + 1,
    bodyEnd: idx + 1 < heads.length ? heads[idx + 1].line : lines.length,
    line: h.line,
  }));
}

// # Acceptance 섹션 내 top-level 번호 항목 수(`N. `). sub-item(ⓐ)·타섹션 숫자라인 제외.
function acceptanceItemCount(lines, accSection) {
  if (!accSection) return 0;
  let n = 0;
  for (let i = accSection.bodyStart; i < accSection.bodyEnd; i++) {
    if (/^\s*\d+\.\s+/.test(lines[i])) n++;
  }
  return n;
}

// 참조 스캔 대상 텍스트: frontmatter·헤더 라인·# Acceptance 섹션·백틱/따옴표 인용 제외.
// (인용/코드 span 은 예시 서술일 때가 많아 참조 오탐을 유발 → 제외; 메타-plan self-trap 방지.)
function scannableText(lines, sections, fmEnd) {
  const acc = sections.find((s) => s.title === 'Acceptance');
  const out = [];
  for (let i = 0; i < lines.length; i++) {
    if (i <= fmEnd) continue; // frontmatter 블록
    if (/^#{1,6} /.test(lines[i])) continue; // 모든 헤더 라인(H1~H6)
    if (acc && i >= acc.line && i < acc.bodyEnd) continue; // # Acceptance 섹션 전체
    out.push(lines[i]);
  }
  // 백틱·큰따옴표 인용(같은 줄 내 짝맞는 것만) 제거 — 예시/코드 span.
  // 작은따옴표는 산문 소유격·축약(plan's·wasn't)이라 delimiter 로 신뢰 불가 → 제거 안 함
  // (개행 넘는 매칭이 정당한 참조를 삼키는 silent false-negative 방지 — code-review Major).
  return out
    .join('\n')
    .replace(/`[^`\n]*`/g, ' ')
    .replace(/"[^"\n]*"/g, ' ');
}

// "Acceptance <run>" 에서 참조 번호 추출. digit run=단일 수, 원문자 run=문자별 수.
// ①-⑳(U+2460~U+2473)=1~20. 그 밖 원문자(㉑+ 등)는 unsupported.
function acceptanceRefs(scanText) {
  const nums = new Set();
  let unsupported = false;
  const re = /Acceptance[ \t]*([0-9①-⑳㉑-㉟㊱-㊿]+)([가-힣]?)/g;
  let m;
  while ((m = re.exec(scanText))) {
    const run = m[1];
    const nextKo = m[2];
    if (/^[0-9]+$/.test(run)) {
      if (COUNTERS.includes(nextKo)) continue; // "Acceptance 3개" → 계량사
      nums.add(parseInt(run, 10));
    } else if (/^[①-⑳]+$/.test(run)) {
      for (const ch of run) nums.add(ch.codePointAt(0) - 0x2460 + 1); // ①-⑳ 각각
    } else {
      unsupported = true; // ㉑+ 원문자 또는 digit+원문자 혼합 → 미지원(조용히 버리지 않음)
    }
  }
  return { nums, unsupported };
}

// 섹션 헤더 title 이 요구 섹션명인가 — 접미사(설명) 허용: "Decisions", "Decisions (설계)",
// "Decisions — 방안", "Decisions: foo" 모두 인정. 정확일치 강요는 실제 plan 관행과 어긋나 오탐.
function sectionIs(title, name) {
  const esc = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp('^' + esc + '(?:$|[\\s(:—–-])').test(title);
}

function parse(text) {
  const t = String(text || '').replace(/\r\n/g, '\n');
  const lines = t.split('\n');
  const fm = t.match(/^---\n([\s\S]*?)\n---/);
  const fmEnd = fm ? t.slice(0, fm.index + fm[0].length).split('\n').length - 1 : -1;
  const fenced = fencedLines(lines);
  return { lines, fm, fmEnd, fenced, sections: h1Sections(lines, fmEnd, fenced) };
}

// 'new' | 'old' | 'mixed' — # Tasks 가 없고 옛 형식 전용 섹션이 있을 때만 'old'.
function formatOf(sections) {
  const has = (name) => sections.some((sec) => sectionIs(sec.title, name));
  const oldOnly = OLD_ONLY.filter(has);
  if (has('Tasks')) return oldOnly.length ? 'mixed' : 'new';
  return oldOnly.length ? 'old' : 'new';
}

function planFormat(text) {
  return formatOf(parse(text).sections);
}

function lintPlan(text) {
  const { lines, fm, fmEnd, fenced, sections } = parse(text);
  const violations = [];

  // 1·2 frontmatter
  if (!fm) {
    violations.push('frontmatter(--- 블록) 없음');
  } else {
    const fmBody = fm[1];
    for (const key of REQUIRED_KEYS) {
      const km = fmBody.match(new RegExp('^' + key + ':(.*)$', 'm'));
      if (!km || !km[1].trim()) violations.push(`frontmatter '${key}' 누락 또는 빈 값`);
    }
    const sm = fmBody.match(/^status:\s*(\S+)/m);
    if (sm && !STATUS_VALUES.includes(sm[1])) {
      violations.push(`status 값 '${sm[1]}' 부적합 (${STATUS_VALUES.join('|')})`);
    }
  }

  // 3 형식별 필수 H1 (frontmatter 블록 이후·코드펜스 밖만)
  const format = formatOf(sections);
  if (format === 'mixed') {
    const found = OLD_ONLY.filter((name) => sections.some((sec) => sectionIs(sec.title, name)));
    violations.push(`형식 혼재: # Tasks 와 옛 형식 섹션(${found.map((n) => '# ' + n).join(', ')})이 함께 있음 — 새 형식은 옛 섹션을 쓰지 않는다`);
  } else {
    const label = format === 'new' ? '새 형식' : '옛 형식 — 새 형식으로 쓰려면 # Tasks 를 두고 옛 섹션을 지운다';
    for (const s of SECTIONS[format]) {
      if (!sections.some((sec) => sectionIs(sec.title, s))) violations.push(`# ${s} 섹션 누락(H1) [${label}]`);
    }
  }

  // 4 새 형식 # Tasks 체크박스
  const tasks = format === 'new' ? sections.find((sec) => sectionIs(sec.title, 'Tasks')) : null;
  if (tasks) {
    let boxes = 0;
    for (let i = tasks.bodyStart; i < tasks.bodyEnd; i++) {
      const m = !fenced[i] && lines[i].match(CHECKBOX);
      if (!m) continue;
      boxes++;
      if (m[1] !== ' ' && !DATE.test(lines[i])) violations.push(`# Tasks 의 체크된 항목에 날짜 (YYYY-MM-DD) 없음: ${lines[i].trim()}`);
    }
    if (!boxes) violations.push('# Tasks 에 체크박스 항목(- [ ] / - [x])이 없음');
  }
  if (format === 'new') {
    for (const s of LOG_SECTIONS) {
      if (sections.some((sec) => sectionIs(sec.title, s))) violations.push(`# ${s} 는 plan 이 아니라 같은 폴더의 <slug>-log.md 에 둔다 [새 형식]`);
    }
  }

  // 5 Acceptance 참조 무결성
  const acc = sections.find((s) => sectionIs(s.title, 'Acceptance'));
  const itemCount = acceptanceItemCount(lines, acc);
  const { nums, unsupported } = acceptanceRefs(scannableText(lines, sections, fmEnd));
  if (unsupported) violations.push('미지원 Acceptance 참조 형식(①-⑳ 밖의 원문자)');
  for (const n of [...nums].sort((a, b) => a - b)) {
    if (!acc) violations.push(`Acceptance ${n} 참조하나 # Acceptance 섹션 없음`);
    else if (n > itemCount) violations.push(`Acceptance ${n} 참조하나 항목 ${itemCount}개뿐`);
  }

  return violations;
}

module.exports = { lintPlan, planFormat };

// ---- CLI ----
if (require.main === module) {
  if (process.env.CLAUDE_PLAN_LINT_OFF === '1') process.exit(0);
  const fs = require('fs');
  const files = process.argv.slice(2);
  let bad = 0;
  for (const f of files) {
    let text;
    try {
      text = fs.readFileSync(f, 'utf8');
    } catch {
      console.error(`plan-lint: ${f} 읽기 실패 — skip`);
      continue;
    }
    const vs = lintPlan(text);
    if (vs.length) {
      bad++;
      for (const v of vs) console.log(`${f}: ${v}`);
    }
  }
  process.exit(bad ? 1 : 0);
}
