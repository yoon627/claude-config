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
let ledger;
try {
  ledger = require('./dlc-ledger.js');
} catch {
  process.exit(0);
}

// gitignored/임시 파일(plans/·.commit-msg 등)은 검증 대상이 아니므로 changed 로 치지 않는다.
// (마무리 단계의 커밋 메시지 임시파일 Write 가 false positive block 을 유발한 사례 — wiki workflow-failures.)
// git check-ignore: exit 0 = ignored. 에러·git 미설치는 not-ignored 로 보아 changed 유지(gate 보수적).
function isIgnored(fp, cwd) {
  if (!fp) return false;
  try {
    execFileSync('git', ['check-ignore', '-q', '--', fp], {
      cwd: cwd || process.cwd(),
      stdio: 'ignore',
      timeout: 2000,
    });
    return true;
  } catch {
    return false;
  }
}

// 명백한 검증 명령만 좁게 — verified 오탐은 gate 를 헐겁게 하므로 보수적.
const VERIFY =
  /(\bpytest\b|\bjest\b|vitest|\bmocha\b|playwright|cypress|\bruff\b|eslint|flake8|\bmypy\b|\btsc\b|typecheck|cargo\s+(test|build|check|clippy)|go\s+(test|vet)|gradlew?\s+\S*(test|build|check)|mvn\s+\S*(test|verify|package)|check_links|npm\s+(test|run\s+(test|lint|build|typecheck|check|verify))|(pnpm|yarn)\s+(test|lint|typecheck|run\s+\S+)|python\s+-m\s+(pytest|unittest))/;
// 검증으로 오인되기 쉬운 비검증 시작 명령(cat README ... test, grep test, ls build 등)
const NONVERIFY_START = /^\s*(cat|grep|rg|ls|echo|printf|find|head|tail|sed|awk)\b/;

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
    const fp = (input.tool_input && input.tool_input.file_path) || '';
    if (fp && !isIgnored(fp, input.cwd)) {
      data.changed = true;
      data.verified = false; // 최종 변경 이후 재검증 강제
      data.blocks = 0; // 새 미검증 변경 → 경고 자격 회복(CAP 재적용)
    }
  }
  if (tool === 'Bash') {
    const cmd = String((input.tool_input && input.tool_input.command) || '').toLowerCase();
    if (!NONVERIFY_START.test(cmd) && VERIFY.test(cmd)) data.verified = true;
  }
  ledger.write(input.session_id, data);
  process.exit(0);
});
