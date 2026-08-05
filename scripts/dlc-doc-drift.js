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

// 변경 1건을 dirty flag 에 반영(순서 반영: trigger→dirty=true, target→dirty=false). home 은 테스트 주입용.
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
      data.readmeDirty = true; data.readmeTrigger = rel; break;
    case 'readme-trigger': data.readmeDirty = true; data.readmeTrigger = rel; break;
    case 'readme-target': data.readmeDirty = false; data.readmeTrigger = null; break;
    case 'index-trigger': data.indexDirty = true; data.indexTrigger = rel; break;
    case 'index-target': data.indexDirty = false; data.indexTrigger = null; break;
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
