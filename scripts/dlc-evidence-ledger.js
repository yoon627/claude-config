#!/usr/bin/env node
// PostToolUse hook (matcher: Edit|Write|NotebookEdit|Bash) — 증거 장부 갱신.
//   파일 변경(Edit/Write/NotebookEdit) → changed=true + verified·blocks 리셋
//     (최종 변경 이후 다시 검증해야 gate 통과 — verified 무효화, 경고 자격 회복).
//   Bash 검증 명령 → verified=true. 단 cat/grep/ls 등 비검증 시작 명령은 제외.
// 한계: hook 은 "검증 *명령 실행* 여부"의 거친 근사다. 검증 *성공* 판정은
//   plan # Acceptance(모델)가 단일 소스 — hook 은 "검증 시도조차 없음"을 잡는 누락 방지망.
// 도구는 이미 실행된 뒤라 차단하지 않는다. 의존/파싱 실패 시 fail-open(exit 0).
'use strict';
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
let ledger;
try {
  ledger = require('./dlc-ledger.js');
} catch {
  process.exit(0);
}
let drift = null;
try {
  drift = require('./dlc-doc-drift.js');
} catch {
  /* 문서 drift 추적만 skip — 검증 ledger 기록은 유지(fail-open 비대칭 방지) */
}
let sig = null;
try {
  sig = require('./dlc-signal.js');
} catch {
  /* 신호 기록만 skip — ledger 기록은 유지(fail-open) */
}

// dir 에서 위로 올라가며 .git(디렉토리 또는 worktree 의 .git 파일) 존재를 찾는다 — git 실행 없이
// "이 경로가 어떤 git 작업트리 안인가"를 판정. check-ignore 의 exit 128 이 outside-repo 인지
// git 오류(safe.directory·손상·GIT_DIR env·symlink)인지 구분하는 데 쓴다(128 단정은 게이트를 조용히 끔).
function insideSomeRepo(dir) {
  let d = dir;
  for (;;) {
    if (fs.existsSync(path.join(d, '.git'))) return true;
    const parent = path.dirname(d);
    if (parent === d) return false;
    d = parent;
  }
}

// gitignored/임시 파일(plans/·.commit-msg 등)은 검증 대상이 아니므로 changed 로 치지 않는다.
// (마무리 단계의 커밋 메시지 임시파일 Write 가 false positive block 을 유발한 사례 — wiki workflow-failures.)
// check-ignore 는 실행 cwd 의 repo 를 기준으로 판정하므로, 세션 cwd 가 아니라 dirname(fp) 에서
// 돌려야 fp 자기 repo 기준이 된다 — worktree 세션이 다른 worktree/repo 의 gitignored 파일을
// 편집할 때 세션 repo 기준 오판(cross-worktree changed 오탐)을 막는다.
//   exit 0 = ignored → changed 아님.  exit 1 = repo 안 비-ignored 실파일 → changed.
//   그 외(128·timeout·git 미설치): dir 이 어떤 repo 안에도 없을 때만 완화(/tmp scratch·git init 전) →
//     changed 아님. repo 안인데 실패(safe.directory·손상·env)면 보수적으로 changed 유지(게이트 안전측).
function isIgnored(fp, cwd) {
  if (!fp) return false;
  const dir = path.isAbsolute(fp) ? path.dirname(fp) : cwd || process.cwd();
  try {
    execFileSync('git', ['check-ignore', '-q', '--', fp], {
      cwd: dir,
      stdio: 'ignore',
      timeout: 2000,
    });
    return true;
  } catch (e) {
    if (e && e.status === 1) return false; // repo 안 확정 · 비-ignored → changed
    return !insideSomeRepo(dir); // repo 밖이면 not changed(완화), 안이면(broken) changed 유지
  }
}

// 명백한 검증 명령만 좁게 — verified 오탐은 gate 를 헐겁게 하므로 보수적.
const VERIFY =
  /(\bpytest\b|\bjest\b|vitest|\bmocha\b|playwright|cypress|\bruff\b|eslint|flake8|\bmypy\b|\btsc\b|typecheck|cargo\s+(test|build|check|clippy)|go\s+(test|vet)|gradlew?\s+\S*(test|build|check)|mvn\s+\S*(test|verify|package)|check_links|npm\s+(test|run\s+(test|lint|build|typecheck|check|verify))|(pnpm|yarn)\s+(test|lint|typecheck|run\s+\S+)|python\s+-m\s+(pytest|unittest)|node\s+(--test(?=$|\s)|\S*\.test\.[cm]?js\b))/;
// 검증으로 오인되기 쉬운 비검증 시작 명령(cat README ... test, grep test, ls build 등)
const NONVERIFY_START = /^\s*(cat|grep|rg|ls|echo|printf|find|head|tail|sed|awk)\b/;
// 검증 스크립트 래핑 인식(`bash /tmp/x-verify.sh`). 키워드가 .sh 직전 완전 세그먼트일 때만 —
// checkout.sh·test-data-loader.sh 처럼 키워드로 시작만 하는 비검증 스크립트를 verified 로 오인식하지 않게.
const VERIFY_SCRIPT = /(^|&&|;)\s*(?:bash|sh)\s+(?:\S*[\/._-])?(?:verify|check|test)\.sh(?=$|\s|[;&|])/;

let raw = '';
const wd = setTimeout(() => process.exit(0), 1000); // stdin 미수신 안전망(notify-hook 패턴)
process.stdin.on('data', (c) => (raw += c));
process.stdin.on('end', () => {
  clearTimeout(wd);
  let input;
  try {
    input = JSON.parse(raw);
  } catch {
    process.exit(0);
  }
  const tool = input.tool_name || '';
  const data = ledger.read(input.session_id);

  if (tool === 'Edit' || tool === 'Write' || tool === 'NotebookEdit') {
    const ti = input.tool_input || {};
    const fp = ti.file_path || ti.notebook_path || ''; // NotebookEdit 는 notebook_path
    // plan 신호는 isIgnored 게이트 *밖* — plans/ 는 gitignored 라 아래 블록이 항상 skip 한다.
    if (sig) {
      const kind = sig.detectPlanSignal(tool, ti);
      if (kind) sig.emit(kind, { session_id: input.session_id, cwd: input.cwd, detail: fp });
    }
    if (fp && !isIgnored(fp, input.cwd)) {
      data.changed = true;
      data.verified = false; // 최종 변경 이후 재검증 강제
      data.blocks = 0; // 새 미검증 변경 → 경고 자격 회복(CAP 재적용)
      // 문서 drift: 표면 변경 → *Dirty=true, 문서 변경 → false(순서 반영). 새로 dirty 면 경고 자격 회복.
      // isIgnored 블록 안 — tmp_*.js·*.bak 등 gitignored scratch 가 false dirty 를 유발하지 않게(검증 changed 와 동일 게이트).
      if (drift) {
        const beforeR = data.readmeDirty;
        const beforeI = data.indexDirty;
        drift.applyChange(data, fp, input.cwd);
        if ((!beforeR && data.readmeDirty) || (!beforeI && data.indexDirty)) data.docBlocks = 0;
      }
    }
  }
  if (tool === 'Bash') {
    const cmd = String((input.tool_input && input.tool_input.command) || '').toLowerCase();
    if (!NONVERIFY_START.test(cmd) && (VERIFY.test(cmd) || VERIFY_SCRIPT.test(cmd))) data.verified = true;
  }
  ledger.write(input.session_id, data);
  process.exit(0);
});
