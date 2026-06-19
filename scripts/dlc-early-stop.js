#!/usr/bin/env node
// Stop hook — evidence gate 보조. 두 가지 누락을 capped 1회 경고로 유도하고 그 뒤엔 통과(fail-open):
//   (1) 검증 누락: 파일을 변경했는데 test/lint/build 기록이 없는 채로 종료(blocks).
//   (2) 문서 drift: 문서화 표면(scripts/·agents/·skills/**/SKILL.md·settings.json·CLAUDE.md, wiki/pages)을
//       바꿨는데 README.md / wiki/index.md 동기화가 없는 채로 종료(docBlocks · dlc-doc-drift 판정).
// 두 판정을 한 hook 에서 하고 한 block 메시지로 합쳐 출력한다 — 별도 hook 이면 동시 block 시
//   한쪽 reason 이 노출 안 된 채 카운터만 소모돼 다시는 안 잡히는 false negative 가 난다.
//   그래서 카운터 증가는 reason 을 실제 출력하는 경우에만 한다(소모-노출 분리 금지).
// notify-hook(async) 와 같은 Stop 배열에서 공존.
//
// 안전장치:
//   - CLAUDE_DLC_EARLYSTOP_OFF=1 → 검증 누락 경고 비활성. CLAUDE_DLC_DOCDRIFT_OFF=1 → 문서 drift 경고 비활성(독립).
//   - stop_hook_active=true → 무한 루프 방지로 즉시 통과.
//   - capped(CAP=1): 각 누락당 1회만 block, 재종료 시 통과 → trivial·예외에 최소 마찰.
//   - 의존/파싱/ledger 오류 → exit 0(절대 막지 않음). doc-drift 모듈만 없으면 검증 경고는 유지.
'use strict';
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
  /* 문서 drift 판정만 skip — 검증 누락 경고는 유지 */
}
const CAP = 1;

const VERIFY_MISSING =
  '파일을 변경했는데 검증(test/lint/typecheck/build 또는 실행·관찰) 기록이 없습니다. ' +
  '변경이 의도대로 동작하는지 검증을 실행하고 결과를 확인하세요. ' +
  'trivial(오타·로그 1줄)이라 검증이 불필요하면 그대로 다시 종료하면 통과합니다.';

let raw = '';
const wd = setTimeout(() => process.exit(0), 1000); // stdin 미수신 안전망
process.stdin.on('data', (c) => (raw += c));
process.stdin.on('end', () => {
  clearTimeout(wd);
  let input;
  try {
    input = JSON.parse(raw);
  } catch {
    process.exit(0);
  }
  if (input.stop_hook_active === true) process.exit(0); // 무한 루프 방지

  const data = ledger.read(input.session_id);
  const reasons = [];

  // (1) 검증 누락
  if (
    process.env.CLAUDE_DLC_EARLYSTOP_OFF !== '1' &&
    data.changed &&
    !data.verified &&
    (data.blocks || 0) < CAP
  ) {
    data.blocks = (data.blocks || 0) + 1;
    reasons.push(VERIFY_MISSING);
  }

  // (2) 문서 drift
  if (drift && process.env.CLAUDE_DLC_DOCDRIFT_OFF !== '1' && (data.docBlocks || 0) < CAP) {
    const docMsgs = drift.evaluate(data);
    if (docMsgs.length) {
      data.docBlocks = (data.docBlocks || 0) + 1;
      reasons.push(...docMsgs);
    }
  }

  if (reasons.length) {
    ledger.write(input.session_id, data); // 카운터 증가는 출력과 함께만 — 미출력 소모 없음
    process.stdout.write(
      JSON.stringify({ decision: 'block', reason: reasons.join('\n\n') + '\n\n(dlc evidence gate 보조)' })
    );
  }
  process.exit(0); // 통과
});
