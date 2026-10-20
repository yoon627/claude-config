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
// ⓥ 섹션 헤더 접미사 허용 ("# Decisions (설계)"·"# Next — 방안" 등도 유효)
ok('ⓥ "# Decisions (설계)" 접미사 → clean(누락 아님)', clean(V.replace('# Decisions', '# Decisions (설계)')));
// ⓦ Acceptance 섹션 접미사도 참조 무결성이 인식
ok('ⓦ "# Acceptance (완료기준)" 접미사 → 참조 정상 인식(clean)', clean(V.replace('# Acceptance', '# Acceptance (완료기준)')));

// ---- 새 형식(# Tasks) ----
const { planFormat } = require('./plan-lint.js');
const N = [
  '---',
  'title: t',
  'status: in_progress',
  'started: 2026-10-18',
  'updated: 2026-10-18',
  '---',
  '',
  '# Goal',
  'g',
  '- Why: w',
  '',
  '# Tasks',
  '- [x] 착수 (2026-10-18)',
  '- [ ] 구현 — `scripts/a.js`, Acceptance 2 확인',
  '',
  '# Acceptance',
  '1. one',
  '2. [ ] two',
  '',
  '# Decisions',
  'd',
  '',
  '# Blockers',
  'none',
  '',
].join('\n');

ok('N1 새 형식 valid(Tasks 의 "Acceptance 2" 참조 + `2. [ ]` 항목 포함) → clean', clean(N));
ok('N2 형식 판별: Tasks 만 → new, 옛 섹션만 → old, 둘 다 → mixed',
  planFormat(N) === 'new' && planFormat(V) === 'old' && planFormat(N.replace('# Blockers', '# Next\nn\n\n# Blockers')) === 'mixed');
ok('N3 # Tasks 도 옛 섹션도 없음 → 새 형식 기본값으로 # Tasks 누락',
  (() => { const vs = lintPlan(N.replace('# Tasks', '## Tasks')); return vs.some((v) => v.includes('# Tasks') && v.includes('새 형식')); })());
ok('N4 # Tasks 와 # Next 혼재 → 형식 혼재 위반', hasV(N.replace('# Blockers', '# Next\nn\n\n# Blockers'), '혼재'));
ok('N5 Tasks 에 체크박스 0개 → 위반', hasV(N.replace('- [x] 착수 (2026-10-18)\n- [ ] 구현 — `scripts/a.js`, Acceptance 2 확인', '착수함'), '체크박스'));
ok('N6 날짜 없는 체크된 Task → 위반', hasV(N.replace('- [x] 착수 (2026-10-18)', '- [x] 착수'), '날짜'));
ok('N7 체크박스 변형(* [X], 들여쓴 하위) → clean',
  clean(N.replace('- [x] 착수 (2026-10-18)', '* [X] 착수 (2026-10-18)\n  - [ ] 하위 항목')));
ok('N8 코드펜스 안 "# Tasks" 는 heading 아님 → 옛 형식 baseline clean',
  clean(V.replace('# Decisions\nd\n', '# Decisions\nd\n```\n# Tasks\n```\n')));
ok('N9 코드펜스 안 "# Next" 예시 → 새 형식 혼재 아님(clean)',
  clean(N.replace('# Decisions\nd\n', '# Decisions\nd\n~~~\n# Next\n~~~\n')));
ok('N10 반쯤 변환(Key Files 만 남고 Tasks 없음) → 옛 형식 누락 + 새 형식 안내',
  (() => {
    const half = V.replace('# Progress\n- 2026-07-16 작업함, Acceptance 2 참조\n\n', '').replace('# Next\nn\n\n', '');
    const vs = lintPlan(half);
    return vs.some((v) => v.includes('# Progress')) && vs.some((v) => v.includes('# Tasks'));
  })());
ok('N11 옛 형식 + # Intent → old 로 판별·clean', planFormat(V + '\n# Intent\n- Problem: p\n') === 'old' && clean(V + '\n# Intent\n- Problem: p\n'));
ok('N12 Tasks 안 코드펜스의 체크박스 예시는 항목 아님 → 날짜 없어도 clean',
  clean(N.replace('- [ ] 구현', '```\n- [x] 예시\n```\n- [ ] 구현'))
  && clean(N.replace('- [ ] 구현', '- [ ] 예시 달린 항목\n  ```\n  - [x] 들여쓴 예시\n  ```\n- [ ] 구현')));
ok('N13 ```` 펜스 안의 ``` 는 펜스를 닫지 않음 → 그 안 "# Next" 는 heading 아님(clean)',
  clean(N.replace('# Decisions\nd\n', '# Decisions\nd\n````\n```\n# Next\n```\n````\n'))
  && clean(N.replace('# Decisions\nd\n', '# Decisions\nd\n```\n```js\n# Next\n```\n')));
ok('N14 새 형식 plan 본문의 작업 기록 섹션(# Review Disposition·# Deferred·# Workflow Findings) → log 로 옮기라는 위반',
  ['Review Disposition', 'Deferred', 'Workflow Findings'].every((s) =>
    lintPlan(N + '\n# ' + s + '\n- x\n').some((v) => v.includes('# ' + s) && v.includes('-log.md'))));
ok('N15 옛 형식 plan 의 작업 기록 섹션은 그대로 허용(clean)',
  clean(V + '\n# Review Disposition\n- f1 — fix\n\n# Deferred\n- x\n\n# Workflow Findings\n- y\n'));

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
