#!/usr/bin/env node
// plan-lint.js 회귀 테스트 — 순수 lintPlan() + CLI. 무프레임워크·결정적.
'use strict';
const { execFileSync, spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { lintPlan } = require('./plan-lint.js');
const SCRIPT = path.join(__dirname, 'plan-lint.js');

let fail = 0;
function ok(name, cond) { if (!cond) fail++; console.log(`${cond ? 'PASS' : 'FAIL'} ${name}`); }
function hasV(text, sub) { return lintPlan(text).some((v) => v.includes(sub)); }
function clean(text) { return lintPlan(text).length === 0; }

// 유효 baseline: 6섹션 + # Acceptance 3항목 + Progress 에 "Acceptance 2" 참조.
const V = [
  '---',
  'title: t',
  'status: in_progress',
  'started: 2026-07-16',
  'updated: 2026-07-16',
  '---',
  '',
  '# Goal',
  'g',
  '',
  '# Progress',
  '- 2026-07-16 작업함, Acceptance 2 참조',
  '',
  '# Next',
  'n',
  '',
  '# Decisions',
  'd',
  '',
  '# Key Files',
  'k',
  '',
  '# Blockers',
  'none',
  '',
  '# Acceptance',
  '1. one',
  '2. two',
  '3. three',
  '',
].join('\n');

// ⓐ valid → clean
ok('ⓐ valid plan → clean', clean(V));
// ⓑ frontmatter 키 누락
ok('ⓑ frontmatter 키 누락 → 위반', hasV(V.replace('updated: 2026-07-16\n', ''), 'updated'));
// ⓒ status 값 오류
ok('ⓒ status 값 오류 → 위반', hasV(V.replace('status: in_progress', 'status: wip'), 'status'));
// ⓓ 6섹션 누락
ok('ⓓ # Blockers 누락 → 위반', hasV(V.replace('# Blockers\nnone\n', ''), 'Blockers'));
// ⓔ Acceptance 5 인데 3항목
ok('ⓔ Acceptance 5 인데 항목 3 → 위반', hasV(V.replace('Acceptance 2 참조', 'Acceptance 5 참조'), 'Acceptance 5'));
// ⓕ 원문자 ⑤ → 5 해석
ok('ⓕ Acceptance ⑤ → 5 로 해석(위반)', hasV(V.replace('Acceptance 2 참조', 'Acceptance ⑤ 참조'), 'Acceptance 5'));
// ⓖ Acceptance 2 인데 3항목 → clean (baseline 이 그 케이스)
ok('ⓖ Acceptance 2 인데 항목 3 → clean', clean(V));
// ⓗ # Acceptance 섹션 없는데 Acceptance 1 참조
{
  const noAcc = V.replace('\n# Acceptance\n1. one\n2. two\n3. three\n', '\n').replace('Acceptance 2 참조', 'Acceptance 1 참조');
  ok('ⓗ # Acceptance 없는데 참조 → 위반', hasV(noAcc, 'Acceptance 1'));
}
// ⓘ §N 참조 무시
ok('ⓘ §8 참조 → 무시(clean)', clean(V.replace('Acceptance 2 참조', '§8 참조, Acceptance 2 참조')));
// ⓙ # Acceptance 섹션 내부 자기참조 무시 (항목 설명에 "Acceptance 9" 써도 안전)
ok('ⓙ # Acceptance 내부 "Acceptance 9" 자기참조 → 무시', clean(V.replace('3. three', '3. three (Acceptance 9 형태 설명)')));
// ⓚ 연속 원문자 ⑤⑥ → 둘 다
{
  const t = V.replace('Acceptance 2 참조', 'Acceptance ⑤⑥ 참조');
  const vs = lintPlan(t);
  ok('ⓚ Acceptance ⑤⑥ → 5·6 둘 다 위반', vs.some((v) => v.includes('Acceptance 5')) && vs.some((v) => v.includes('Acceptance 6')));
}
// ⓛ ㉑ 미지원 형식
ok('ⓛ Acceptance ㉑ → 미지원 위반', hasV(V.replace('Acceptance 2 참조', 'Acceptance ㉑ 참조'), '미지원'));
// ⓜ "1x." 라인은 항목 미카운트 (Acceptance 3 참조인데 항목이 1,2 + "3x." 면 3항목 아님 → 위반)
{
  const t = V.replace('3. three', '3x. not-an-item').replace('Acceptance 2 참조', 'Acceptance 3 참조');
  ok('ⓜ "3x." 미카운트 → Acceptance 3 위반', hasV(t, 'Acceptance 3'));
}
// ⓝ 타 섹션 숫자 라인 미카운트 (Progress 의 "2026" 이 항목으로 안 셈)
ok('ⓝ # Progress 숫자라인 미카운트 → baseline clean 유지', clean(V));
// ⓞ CRLF 정상 처리
ok('ⓞ CRLF plan → clean', clean(V.replace(/\n/g, '\r\n')));
// ⓟ 빈 frontmatter 값
ok('ⓟ 빈 title 값 → 위반', hasV(V.replace('title: t', 'title:'), 'title'));
// ⓠ ## Goal (H2) → 섹션 누락
ok('ⓠ ## Goal(H2) → Goal 섹션 누락 위반', hasV(V.replace('# Goal', '## Goal'), 'Goal'));
// ⓡ 계량사 "Acceptance 3개" → 참조 아님
ok('ⓡ "Acceptance 3개 항목" 계량사 → clean', clean(V.replace('Acceptance 2 참조', 'Acceptance 3개 항목 있음')));
// ⓢ 한글-only frontmatter 값 non-empty → clean (Cm1)
ok('ⓢ 한글-only title → clean(non-empty)', clean(V.replace('title: t', 'title: 계획 정리')));
// ⓣ digit+원문자 혼합 run → 미지원 위반 (CM3, 숫자 조용히 안 버림)
ok('ⓣ "Acceptance 21①" 혼합 → 미지원 위반', hasV(V.replace('Acceptance 2 참조', 'Acceptance 21① 참조'), '미지원'));
// ⓤ apostrophe(소유격·축약) 사이 참조를 삼키지 않음 (code-review Major 회귀)
ok('ⓤ apostrophe 사이 Acceptance 5(항목3) → 위반(미삼킴)',
  hasV(V.replace('Acceptance 2 참조', "plan's bug, Acceptance 5 참조, wasn't done"), 'Acceptance 5'));

// ---- CLI ----
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'plan-lint-'));
function writeF(name, text) { const p = path.join(TMP, name); fs.writeFileSync(p, text); return p; }
function cli(args, env) {
  const r = spawnSync('node', [SCRIPT, ...args], { env: { ...process.env, ...(env || {}) }, encoding: 'utf8', timeout: 20000 });
  return { code: r.status, out: (r.stdout || '') + (r.stderr || '') };
}
const validF = writeF('valid.md', V);
const brokenF = writeF('broken.md', V.replace('status: in_progress', 'status: wip'));
ok('CLI valid → exit 0·무출력', (() => { const r = cli([validF]); return r.code === 0 && r.out.trim() === ''; })());
ok('CLI broken → exit 1·파일명+사유', (() => { const r = cli([brokenF]); return r.code === 1 && r.out.includes('broken.md') && r.out.includes('status'); })());
ok('CLI 인자 0개 → exit 0', (() => { const r = cli([]); return r.code === 0; })());
ok('CLI 다중(valid+broken) → exit 1·broken 만', (() => { const r = cli([validF, brokenF]); return r.code === 1 && r.out.includes('broken.md') && !r.out.includes('valid.md'); })());
ok('CLI 미존재 경로 → 크래시 없이 처리', (() => { const r = cli([path.join(TMP, 'nope.md')]); return r.code === 0 || r.code === 1; })());
ok('CLI CLAUDE_PLAN_LINT_OFF=1 → 무출력 exit 0', (() => { const r = cli([brokenF], { CLAUDE_PLAN_LINT_OFF: '1' }); return r.code === 0 && r.out.trim() === ''; })());

fs.rmSync(TMP, { recursive: true, force: true });
console.log(fail === 0 ? 'ALL PASS' : `${fail} FAIL`);
process.exit(fail === 0 ? 0 : 1);
