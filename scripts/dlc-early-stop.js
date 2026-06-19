#!/usr/bin/env node
// Stop hook — evidence gate 보조. "파일을 변경했는데 검증 기록이 없는" 채로
// 종료하려 하면 1회(capped) block 해 검증을 유도한다. 그 뒤엔 통과(fail-open).
// 최종 변경 이후 검증 누락도 잡는다(변경 시 evidence-ledger 가 verified·blocks 리셋).
// notify-hook(async) 와 같은 Stop 배열에서 공존.
//
// 안전장치:
//   - CLAUDE_DLC_EARLYSTOP_OFF=1 → 완전 비활성(holdout/A-B).
//   - stop_hook_active=true → 무한 루프 방지로 즉시 통과.
//   - capped(CAP=1): 미검증 변경당 1회만 block, 재종료 시 통과 → trivial·예외에 최소 마찰.
//   - 의존/파싱/ledger 오류 → exit 0(절대 막지 않음).
'use strict';
let ledger;
try {
  ledger = require('./dlc-ledger.js');
} catch {
  process.exit(0);
}
const CAP = 1;

let raw = '';
const wd = setTimeout(() => process.exit(0), 1000); // stdin 미수신 안전망
process.stdin.on('data', (c) => (raw += c));
process.stdin.on('end', () => {
  clearTimeout(wd);
  if (process.env.CLAUDE_DLC_EARLYSTOP_OFF === '1') process.exit(0);
  let input;
  try {
    input = JSON.parse(raw);
  } catch {
    process.exit(0);
  }
  if (input.stop_hook_active === true) process.exit(0); // 무한 루프 방지

  const data = ledger.read(input.session_id);
  if (data.changed && !data.verified && (data.blocks || 0) < CAP) {
    data.blocks = (data.blocks || 0) + 1;
    ledger.write(input.session_id, data);
    process.stdout.write(
      JSON.stringify({
        decision: 'block',
        reason:
          "파일을 변경했는데 검증(test/lint/typecheck/build 또는 실행·관찰) 기록이 없습니다. " +
          "변경이 의도대로 동작하는지 검증을 실행하고 결과를 확인하세요. " +
          "trivial(오타·로그 1줄)이라 검증이 불필요하면 그대로 다시 종료하면 통과합니다. (dlc evidence gate 보조)",
      })
    );
    process.exit(0);
  }
  process.exit(0); // 통과
});
