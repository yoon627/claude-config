#!/usr/bin/env node
// branch → §10 plan 매칭 — 순수 모듈(hook 아님). session-brief·dlc-early-stop 이 require.
//
// 왜 모듈인가: 같은 매칭 규칙이 여러 곳에 재서술되면 한쪽만 고쳐져 어긋난다(이 repo 의
// 반복 실패 유형). 규칙의 단일 소스는 CLAUDE.md §10 이고, 코드 쪽 단일 소스는 여기다.
'use strict';
const fs = require('fs');
const path = require('path');

// §10: "현재 git branch 가 slug 에 포함된 dir". worktree- prefix 는 EnterWorktree 가 붙인다.
function anchorMatches(branch, slug) {
  if (!slug || !branch) return false;
  return branch === slug || branch === `worktree-${slug}` || branch.endsWith(`-${slug}`);
}

// <root>/plans/<YYYY-MM-DD>-<slug>/<slug>-plan.md 중 branch 와 매칭되는 첫 경로(없으면 null).
// **branch 매칭만 본다** — §10 의 "세션 내 active 추적"(브랜치를 바꿔도 따라오는 plan)은
// hook 이 알 수 없다. 그 경우를 놓치는 false negative 를 감수하는 설계다(오탐보다 낫다).
function activePlanPath(root, branch) {
  if (!root || !branch) return null;
  const plansDir = path.join(root, 'plans');
  let entries;
  try {
    entries = fs.readdirSync(plansDir, { withFileTypes: true });
  } catch {
    return null; // plans/ 없음 → 매칭 없음
  }
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    let files;
    try {
      files = fs.readdirSync(path.join(plansDir, e.name));
    } catch {
      continue;
    }
    for (const f of files) {
      if (!f.endsWith('-plan.md')) continue;
      if (anchorMatches(branch, f.slice(0, -'-plan.md'.length))) {
        return path.join(plansDir, e.name, f);
      }
    }
  }
  return null;
}

module.exports = { anchorMatches, activePlanPath };
