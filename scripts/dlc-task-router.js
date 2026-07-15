#!/usr/bin/env node
// UserPromptSubmit hook — 작업 유형(디버깅/render 산출물)을 키워드로 감지해 dlc
// discipline 을 context 로 주입 + 새 프롬프트이므로 evidence ledger 리셋.
// 강제 아님(suggest). 의존/파싱 실패 시 fail-open(exit 0).
'use strict';
let ledger;
try {
  ledger = require('./dlc-ledger.js');
} catch {
  process.exit(0);
}
let sig = null;
try {
  sig = require('./dlc-signal.js');
} catch {
  /* 신호 기록만 skip — 라우팅 주입은 유지(fail-open) */
}

// 증상 표현 위주로 좁힘 — "error handling 추가" 같은 기능 요청 오탐 완화.
const DBG = /(디버그|debugging|stack ?trace|스택\s?트레이스|재현|reproduce|회귀\s?버그|regression|crash|튕긴|튕겨|예외가\s?(발생|나)|exception\s?(발생|thrown)|안\s?돼|안\s?됨|동작\s?안|작동\s?안|버그가|에러가\s?(나|발생)|깨졌|깨진다|실패한다|failing)/;
const RENDER = /(렌더링|\brender\b|\bsvg\b|canvas|webgl|애니메이션|animation|차트를?\s?그|시각화|three\.?js|\bd3\.js\b|그래프를?\s?그|게임\s?화면|화면에\s?그)/;

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
  ledger.reset(input.session_id); // 새 턴 시작

  const prompt = String(input.prompt || '').toLowerCase();
  const ctx = { session_id: input.session_id, cwd: input.cwd };
  const out = [];
  if (DBG.test(prompt)) {
    if (sig) sig.emit('router-investigation', ctx);
    out.push(
      "[dlc:investigation] 디버깅/장애로 보입니다. 추측 수정 전: ① 실패 재현 ② 가설 3개+ 경쟁 ③ 증상→직접원인→근본원인 인과사슬을 증거로 확정. 재현 없이 '고쳤다' 금지. (skills/dlc/SKILL.md 조사 프로토콜)"
    );
  }
  if (RENDER.test(prompt)) {
    if (sig) sig.emit('router-grounding', ctx);
    out.push(
      "[dlc:grounding] 실행되는 산출물(render/executable)로 보입니다. 정적 점검(파싱 OK)으로 끝내지 말고 실제 실행해 출력을 관찰한 증거를 acceptance 에 남기세요. 'well-formed ≠ correct'. 취향·시각 판단이 큰 산출물이면 구현 전 저비용 변형 2~4종을 먼저 제시해 반응을 받는 것을 고려하세요(취향 발견이 구현 후로 밀리면 비쌈). (skills/dlc/SKILL.md verification grounding + 요구사항 명확화 '프로토타입-우선')"
    );
  }
  if (out.length === 0) process.exit(0);

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'UserPromptSubmit',
        additionalContext: out.join('\n'),
      },
    })
  );
  process.exit(0);
});
