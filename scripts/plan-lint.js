#!/usr/bin/env node
// plan-lint — §10 plan 참조 무결성 순수 판정 + CLI (hook 아님, CI·/improve·/c·/e 가 호출).
// 기계적 불변식만 검증(의미 판정 title↔Goal 정합 등은 LLM 몫):
//   1 frontmatter 필수키(title/status/started/updated) non-empty
//   2 status ∈ {in_progress, blocked, done}
//   3 6 H1 섹션 헤더 존재(# Goal/Progress/Next/Decisions/Key Files/Blockers)
//   4 Acceptance 참조 무결성: 본문의 "Acceptance <N>"(N=숫자 또는 ①-⑳) 참조 ↔ # Acceptance top-level 항목 수
// kill-switch: CLAUDE_PLAN_LINT_OFF=1 → CLI no-op exit 0.
'use strict';

const REQUIRED_KEYS = ['title', 'status', 'started', 'updated'];
const STATUS_VALUES = ['in_progress', 'blocked', 'done'];
const REQUIRED_SECTIONS = ['Goal', 'Progress', 'Next', 'Decisions', 'Key Files', 'Blockers'];
const COUNTERS = ['개', '종', '줄']; // 계량사 — 뒤따르면 참조 아님

// H1(`# Title`) 섹션들을 {title, bodyStart, bodyEnd}(라인 인덱스, bodyEnd 배타) 로.
// fmEnd 이하(frontmatter 블록) 라인은 제외 — YAML 내 `# ...` 주석이 본문 H1 로 오인되지 않게.
function h1Sections(lines, fmEnd) {
  const heads = [];
  for (let i = 0; i < lines.length; i++) {
    if (i <= fmEnd) continue;
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

function lintPlan(text) {
  const t = String(text || '').replace(/\r\n/g, '\n');
  const lines = t.split('\n');
  const violations = [];

  // 1·2 frontmatter
  const fm = t.match(/^---\n([\s\S]*?)\n---/);
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

  // 3 6 H1 섹션 (frontmatter 블록 이후만)
  const fmEnd = fm ? t.slice(0, fm.index + fm[0].length).split('\n').length - 1 : -1;
  const sections = h1Sections(lines, fmEnd);
  const titles = new Set(sections.map((s) => s.title));
  for (const s of REQUIRED_SECTIONS) {
    if (!titles.has(s)) violations.push(`# ${s} 섹션 누락(H1)`);
  }

  // 4 Acceptance 참조 무결성
  const acc = sections.find((s) => s.title === 'Acceptance');
  const itemCount = acceptanceItemCount(lines, acc);
  const { nums, unsupported } = acceptanceRefs(scannableText(lines, sections, fmEnd));
  if (unsupported) violations.push('미지원 Acceptance 참조 형식(①-⑳ 밖의 원문자)');
  for (const n of [...nums].sort((a, b) => a - b)) {
    if (!acc) violations.push(`Acceptance ${n} 참조하나 # Acceptance 섹션 없음`);
    else if (n > itemCount) violations.push(`Acceptance ${n} 참조하나 항목 ${itemCount}개뿐`);
  }

  return violations;
}

module.exports = { lintPlan };

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
