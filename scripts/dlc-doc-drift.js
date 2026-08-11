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

// 축별 ledger 필드명 — 오타로 축이 섞이지 않게 한 곳에 모은다.
const AXIS = {
  readme: { dirty: 'readmeDirty', trigger: 'readmeTrigger', covered: 'readmeCovered', pending: 'readmePending' },
  index: { dirty: 'indexDirty', trigger: 'indexTrigger', covered: 'indexCovered', pending: 'indexPending' },
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

// 현재 dirty 상태 → 경고 메시지 배열(빈 배열이면 drift 없음). capped/출력은 early-stop 이 관리.
function evaluate(data) {
  const msgs = [];
  if (data && data.readmeDirty) {
    msgs.push(
      'README.md 가 문서화 표면(scripts/·agents/·skills/**/SKILL.md·settings.json·CLAUDE.md) 변경과 ' +
        '함께 갱신되지 않았습니다 — README 동기화를 검토하세요. (불필요하면 그대로 재종료 시 통과)'
    );
  }
  if (data && data.indexDirty) {
    msgs.push(
      'wiki/index.md 가 wiki/pages 변경과 함께 갱신되지 않았습니다 — index 동기화를 검토하세요. (불필요하면 재종료 시 통과)'
    );
  }
  return msgs;
}

module.exports = { resolveRoot, classify, applyChange, evaluate };
