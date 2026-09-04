#!/usr/bin/env node
// dlc 문서 drift 판정 — 순수 모듈(hook 아님). dlc-early-stop(Stop)·dlc-evidence-ledger(PostToolUse)가 require.
// "문서화 표면(scripts/·agents/·skills/**/SKILL.md·settings.json·CLAUDE.md)을 바꿨는데
//  같은 작업에서 README.md(또는 wiki/pages↔wiki/index.md)를 안 고친" drift 를 ledger dirty flag 로 추적한다.
// 이 규칙은 ~/.claude repo 자산 문서화 전용 → root 를 .claude(또는 그 worktree)로 한정, 그 외 cwd 는 no-op.
'use strict';
const os = require('os');

// cwd 가 속한 이 repo(~/.claude) root. 글로벌 hook 이라 임의 프로젝트의 `.claude` 서브디렉토리를
// 오인하지 않도록 home(~/.claude) 기준으로만 인정한다. worktree(<root>/.claude/worktrees/<name>) 우선.
// home 은 테스트 주입용(기본 os.homedir()). 매칭 안 되면 null → 호출부 no-op(타 repo 무영향).
function resolveRoot(cwd, home) {
  const c = String(cwd || '').replace(/\\/g, '/');
  const base = String(home == null ? os.homedir() : home).replace(/\\/g, '/').replace(/\/+$/, '');
  if (!base) return null;
  const root = base + '/.claude';
  const esc = root.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const wt = c.match(new RegExp('^(' + esc + '/\\.claude/worktrees/[^/]+)(/|$)'));
  if (wt) return wt[1];
  if (c === root || c.startsWith(root + '/')) return root;
  return null;
}

// root 기준 정확 상대경로로 분류. 루트 README/CLAUDE 만 인정(per-repo·하위 README 는 null).
// 'readme-trigger-new' = README 가 파일의 **존재만** 문서화하는 부류(테스트는 `x.js (+ .test.js)` 표기)
//   → 신규 추가일 때만 trigger. 신규 여부는 호출부가 applyChange 의 isNewFile 로 주입(이 모듈은 순수).
function classify(fp, root) {
  if (!root) return null;
  const nf = String(fp || '').replace(/\\/g, '/');
  if (!nf.startsWith(root + '/')) return null;
  const rel = nf.slice(root.length + 1);
  // rel 은 이제 `path.join(root, rel)` 로 **파일 stat 에도 쓰인다**(mtime 판정). `..` 세그먼트가
  // 섞이면 repo 밖을 재게 되므로 여기서 거른다 — 문자열로만 쓰이던 시절엔 없던 요구다.
  if (rel.split('/').includes('..')) return null;

  if (rel === 'README.md') return 'readme-target';
  if (rel === 'wiki/index.md') return 'index-target';
  if (rel.startsWith('wiki/pages/')) return 'index-trigger';
  if (/^(scripts\/)?[^/]+\.(test|spec)\.js$/.test(rel)) return 'readme-trigger-new';
  if (/^[^/]+\.js$/.test(rel)) return 'readme-trigger'; // top-level 운영 스크립트(statusline.js 등)
  if (/^scripts\/[^/]+\.js$/.test(rel)) return 'readme-trigger';
  if (/^agents\/[^/]+\.md$/.test(rel)) return 'readme-trigger';
  if (/^commands\/[^/]+\.md$/.test(rel)) return 'readme-trigger';
  if (/^skills\/[^/]+\/SKILL\.md$/.test(rel)) return 'readme-trigger';
  if (rel === 'settings.json') return 'readme-trigger';
  if (rel === 'CLAUDE.md') return 'readme-trigger';
  return null;
}

// 축별 ledger 필드명 + 그 축의 target 경로(root 상대) — 오타로 축이 섞이지 않게 한 곳에 모은다.
const AXIS = {
  readme: { dirty: 'readmeDirty', trigger: 'readmeTrigger', covered: 'readmeCovered', pending: 'readmePending', target: 'README.md' },
  index: { dirty: 'indexDirty', trigger: 'indexTrigger', covered: 'indexCovered', pending: 'indexPending', target: 'wiki/index.md' },
};
const COVERED_CAP = 50; // ledger 는 세션당 JSON 파일 — 무한 증가 방지. 초과분은 종전 동작(재편집 시 dirty).

// covered = 이번 세션에 target(README·wiki index)을 갱신하며 이미 문서에 반영된 trigger 들.
// 그 파일을 다시 편집해도 dirty 로 만들지 않는다 — 문서 동기화는 *편집 순서*가 아니라 *상태*이고,
// 순서로 모델링하면 "동기화 후 같은 파일을 한 번 더 만졌다"가 미동기화로 뒤집힌다(오탐).
// 배열은 항상 concat 으로 새로 할당한다: ledger.DEFAULT 가 `{...DEFAULT}` 얕은 복사로 쓰이므로
// push 하면 모든 세션이 DEFAULT 의 같은 배열을 공유·오염한다.
// rel 은 여기 도달 시 항상 non-null — classify 가 카테고리를 주는 조건과 rel 이 채워지는 조건이 같다.
function markTrigger(data, axis, rel) {
  const f = AXIS[axis];
  const covered = data[f.covered] || [];
  if (covered.includes(rel)) return; // 이미 문서화됨 → 재편집은 drift 아님
  data[f.dirty] = true;
  data[f.trigger] = rel;
  const pending = data[f.pending] || [];
  if (!pending.includes(rel)) data[f.pending] = pending.concat(rel).slice(0, COVERED_CAP);
}

function markTarget(data, axis) {
  const f = AXIS[axis];
  data[f.dirty] = false;
  data[f.trigger] = null;
  const pending = data[f.pending] || [];
  if (pending.length) {
    const covered = data[f.covered] || [];
    data[f.covered] = covered.concat(pending.filter((p) => !covered.includes(p))).slice(0, COVERED_CAP);
  }
  data[f.pending] = [];
}

// 변경 1건을 dirty flag 에 반영. home 은 테스트 주입용.
// isNewFile(rel, root)→boolean 은 'readme-trigger-new' 부류에만 조회되는 선택 콜백(git 등 부수효과는
// 호출부 몫). 미제공이면 신규가 아닌 것으로 봐 trigger 하지 않는다 — 이 부류는 오탐 비용이 미탐보다 크다.
function applyChange(data, fp, cwd, home, isNewFile) {
  const root = resolveRoot(cwd, home);
  if (!root) return data;
  // rel 이 어느 root 기준인지 못 박는다 — Stop 시점 root 가 다르면 mtime 판정을 포기해야 한다.
  // 한 세션이 두 root 를 오가면 '' 로 두어 어떤 root 와도 일치하지 않게 만든다(보수).
  if (data.driftRoot == null) data.driftRoot = root;
  else if (data.driftRoot !== root) data.driftRoot = '';
  const nf = String(fp || '').replace(/\\/g, '/');
  const rel = nf.startsWith(root + '/') ? nf.slice(root.length + 1) : null; // 신호 detail 용(repo-relative)
  switch (classify(fp, root)) {
    case 'readme-trigger-new':
      if (typeof isNewFile !== 'function' || !isNewFile(rel, root)) break;
      markTrigger(data, 'readme', rel); break;
    case 'readme-trigger': markTrigger(data, 'readme', rel); break;
    case 'readme-target': markTarget(data, 'readme'); break;
    case 'index-trigger': markTrigger(data, 'index', rel); break;
    case 'index-target': markTarget(data, 'index'); break;
  }
  return data;
}

// dirty 인데 실제로는 이미 동기화됐는가를 **파일 상태**로 재확인한다.
// dirty 는 PostToolUse 의 `Edit|Write|NotebookEdit` 분기에서만 세워진다 — README 를 Bash
// (`node -e`·`sed`·heredoc)로 고치면 target 갱신이 장부에 안 잡혀 dirty 가 영영 안 풀리고
// "고쳤는데도 경고"가 난다(실측). mtime 비교는 편집 도구와 무관하므로 그 비대칭을 없앤다.
// 이 모듈은 순수하게 두고 stat 은 호출부가 `mtimeOf(rel)→ms|null` 로 주입한다(isNewFile 과 같은 패턴).
// **판정 불가는 전부 "경고 유지"** — 이 게이트는 보조망이라 미탐(조용히 통과)이 오탐보다 나쁘다.
// pending trigger 를 target mtime 기준으로 가른다.
//   { covered: target 보다 낡음(=문서에 반영됨), remaining: target 보다 새로움, undecidable }
// undecidable = 비교 자체가 불가 → 호출부는 경고를 유지한다(미탐이 오탐보다 나쁘다):
//   mtimeOf 미주입 · pending 없음 · pending 이 상한에 잘려 전수가 아님 · stat 실패/비유한값.
// `Number.isFinite` 로 거르는 이유: `typeof NaN === 'number'` 라 NaN 이 통과하면 모든 `m > NaN`
// 비교가 false 가 되어 **판정 불가가 미탐 쪽으로** 떨어진다(설계 원칙의 반대).
function partitionPending(data, axis, mtimeOf) {
  const f = AXIS[axis];
  const pending = (data && data[f.pending]) || [];
  const undecided = { covered: [], remaining: pending.slice(), undecidable: true };
  if (typeof mtimeOf !== 'function' || !pending.length) return undecided;
  if (pending.length >= COVERED_CAP) return undecided; // 잘린 목록으로는 전수 비교가 성립 안 한다
  try {
    const t = mtimeOf(f.target);
    if (!Number.isFinite(t)) return undecided;
    const covered = [];
    const remaining = [];
    for (const rel of pending) {
      const m = mtimeOf(rel);
      if (!Number.isFinite(m)) return undecided;
      (m > t ? remaining : covered).push(rel);
    }
    return { covered, remaining, undecidable: false };
  } catch {
    return undecided; // stat 실패는 판정 불가지 동기화가 아니다
  }
}

// mtime 으로 확인된 동기화를 ledger 에 반영한다(mutating). 반환: 무언가 바뀌었으면 true.
// **covered 로 옮기는 것이 핵심** — 안 옮기면 그 파일을 다시 편집할 때(dlc 의 구현→동기화→리뷰반영
// 순서상 흔하다) markTrigger 가 다시 dirty 를 세워, 2026-08-12 에 covered-set 으로 고쳤던
// "동기화 후 재편집" 오탐이 Bash 경로에서만 되살아난다.
function settle(data, mtimeOf) {
  let changed = false;
  for (const axis of Object.keys(AXIS)) {
    const f = AXIS[axis];
    if (!data || !data[f.dirty]) continue;
    const p = partitionPending(data, axis, mtimeOf);
    if (p.undecidable || !p.covered.length) continue;
    const covered = data[f.covered] || [];
    data[f.covered] = covered.concat(p.covered.filter((r) => !covered.includes(r))).slice(0, COVERED_CAP);
    data[f.pending] = p.remaining;
    if (!p.remaining.length) {
      data[f.dirty] = false;
      data[f.trigger] = null;
    } else {
      data[f.trigger] = p.remaining[p.remaining.length - 1];
    }
    changed = true;
  }
  return changed;
}

const MESSAGE = {
  readme:
    'README.md 가 문서화 표면(scripts/·agents/·skills/**/SKILL.md·settings.json·CLAUDE.md) 변경과 ' +
    '함께 갱신되지 않았습니다 — README 동기화를 검토하세요. (불필요하면 그대로 재종료 시 통과)',
  index:
    'wiki/index.md 가 wiki/pages 변경과 함께 갱신되지 않았습니다 — index 동기화를 검토하세요. (불필요하면 재종료 시 통과)',
};

// 현재 상태 → 경고 목록 `[{ axis, message }]`(빈 배열이면 drift 없음). capped/출력은 early-stop 이 관리.
// **축을 함께 돌려주는 이유**: 호출부가 신호(telemetry)를 dirty flag 로 emit 하면, 한 축만 억제된
// 경우 출력하지 않은 경고의 failure 신호를 남긴다(early-stop 헤더가 금지한 "소모-노출 분리"의
// 신호판). 메시지 문자열로 축을 역산하는 것도 취약하므로 축을 명시한다.
// mtimeOf 는 선택 — 미제공이면 종전 동작(장부 flag 만으로 판정). 비파괴(ledger 갱신은 settle).
function evaluate(data, mtimeOf) {
  const out = [];
  for (const axis of Object.keys(AXIS)) {
    const f = AXIS[axis];
    if (!data || !data[f.dirty]) continue;
    const p = partitionPending(data, axis, mtimeOf);
    if (!p.undecidable && !p.remaining.length) continue; // 전부 target 보다 낡음 → 동기화됨
    out.push({ axis, message: MESSAGE[axis] });
  }
  return out;
}

module.exports = { resolveRoot, classify, applyChange, partitionPending, settle, evaluate, MESSAGE };
