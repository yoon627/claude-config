#!/usr/bin/env node
// Stop hook — evidence gate 보조. 두 가지 누락을 capped 1회 경고로 유도하고 그 뒤엔 통과(fail-open):
//   (1) 검증 누락: 파일을 변경했는데 test/lint/build 기록이 없는 채로 종료(blocks).
//   (2) 문서 drift: 문서화 표면(scripts/·agents/·skills/**/SKILL.md·CLAUDE.md, wiki/pages)을
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
  /* 문서 drift 판정만 skip — 검증 누락 경고는 유지 */
}
let sig = null;
try {
  sig = require('./dlc-signal.js');
} catch {
  /* 신호 기록만 skip — 경고 본연 동작은 유지(fail-open) */
}
let planMatch = null;
try {
  planMatch = require('./plan-match.js');
} catch {
  /* plan drift 축만 skip */
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
  const sigCtx = { session_id: input.session_id, cwd: input.cwd };

  // (1) 검증 누락
  if (
    process.env.CLAUDE_DLC_EARLYSTOP_OFF !== '1' &&
    data.changed &&
    !data.verified &&
    (data.blocks || 0) < CAP
  ) {
    data.blocks = (data.blocks || 0) + 1;
    reasons.push(VERIFY_MISSING);
    if (sig) sig.emit('early-stop-verify', { ...sigCtx, detail: data.changedTrigger }); // 실제 block 출력과 동일 조건에서만
  }

  // (2) 문서 drift
  let docSettled = false;
  if (drift && process.env.CLAUDE_DLC_DOCDRIFT_OFF !== '1' && (data.docBlocks || 0) < CAP) {
    // 장부의 dirty flag 는 Edit/Write 로 고친 것만 본다 — README 를 Bash 로 고치면 dirty 가 안
    // 풀려 "고쳤는데도 경고"가 난다. 실제 파일 mtime 을 주입해 drift 가 상태로 재확인하게 한다.
    // **root 를 대조하는 이유**: pending 의 rel 은 *편집 시점* root 기준이다. 세션이 그 뒤 다른
    // worktree·main 으로 옮기면(§3-1·/e 8단계가 main 복귀를 시킨다) 같은 rel 이 **다른 파일**을
    // 가리키고, main 은 README 가 매 머지마다 재작성돼 거의 항상 최신이라 게이트가 통째로 꺼진다.
    const root = drift.resolveRoot(input.cwd);
    const mtimeOf =
      root && root === data.driftRoot
        ? (rel) => {
            try {
              return fs.statSync(path.join(root, rel)).mtimeMs;
            } catch {
              return null; // 부재·권한 실패 → 판정 불가(경고 유지)
            }
          }
        : null; // root 불일치·미해석 → 종전 동작(장부 flag 만)
    docSettled = drift.settle(data, mtimeOf); // 확인된 동기화를 covered 로 (재편집 오탐 차단)
    const docMsgs = drift.evaluate(data, mtimeOf);
    if (docMsgs.length) {
      data.docBlocks = (data.docBlocks || 0) + 1;
      reasons.push(...docMsgs.map((m) => m.message));
      // 신호는 **실제로 출력한 축만** — dirty flag 로 emit 하면 억제된 축의 failure 가 남아
      // /improve 집계·브리프 nudge 가 이미 고친 오탐을 계속 "반복 실패"로 센다.
      if (sig) {
        for (const m of docMsgs) {
          const kind = m.axis === 'readme' ? 'doc-drift-readme' : 'doc-drift-index';
          const trigger = m.axis === 'readme' ? data.readmeTrigger : data.indexTrigger;
          sig.emit(kind, { ...sigCtx, detail: trigger });
        }
      }
    }
  }

  // (3) plan drift — 소스를 바꿨는데 매칭되는 active plan 을 한 번도 안 건드리고 종료.
  // 발동 조건을 **좁게** 잡는다: branch 로 매칭되는 plan 파일이 실제로 있을 때만.
  // plan 이 없는 흐름(§10 적용범위 밖·plan 없는 trivial)에서는 아예 판정하지 않는다 —
  // 이 축의 최대 위험은 오탐이고, 못 잡는 쪽(§10 의 세션 내 active 추적)은 감수한다.
  if (
    planMatch &&
    process.env.CLAUDE_DLC_PLANDRIFT_OFF !== '1' &&
    data.changed &&
    !data.planTouched &&
    (data.planBlocks || 0) < CAP
  ) {
    let planPath = null;
    try {
      const root = drift ? drift.resolveRoot(input.cwd) : null;
      if (root) {
        const branch = require('child_process')
          .execFileSync('git', ['-C', root, 'rev-parse', '--abbrev-ref', 'HEAD'], {
            encoding: 'utf8',
            stdio: ['ignore', 'pipe', 'ignore'],
            timeout: 3000,
          })
          .trim();
        planPath = planMatch.activePlanPath(root, branch);
      }
    } catch {
      planPath = null; // git 없음·detached·타임아웃 → 판정 포기(fail-open)
    }
    if (planPath) {
      data.planBlocks = (data.planBlocks || 0) + 1;
      reasons.push(
        `소스를 변경했는데 이 브랜치의 plan(${path.basename(planPath)})을 한 번도 갱신하지 않았습니다. ` +
          'CLAUDE.md §10 은 결정·방향·스코프 변경을 그때그때 반영하라고 요구합니다 — ' +
          '`# Progress`/`# Next` 만이라도 실제 상태로 맞추세요. ' +
          '갱신할 것이 정말 없으면 그대로 다시 종료하면 통과합니다.'
      );
      if (sig) sig.emit('early-stop-plan-drift', { ...sigCtx, detail: data.changedTrigger });
    }
  }

  // settle 이 covered 를 옮겼으면 경고가 없어도 저장해야 한다 — 안 그러면 다음 Stop 에서
  // 같은 판정을 다시 하고, 그 사이 재편집이 오탐으로 되살아난다.
  if (!reasons.length && docSettled) ledger.write(input.session_id, data);

  if (reasons.length) {
    ledger.write(input.session_id, data); // 카운터 증가는 출력과 함께만 — 미출력 소모 없음
    process.stdout.write(
      JSON.stringify({ decision: 'block', reason: reasons.join('\n\n') + '\n\n(dlc evidence gate 보조)' })
    );
  }
  process.exit(0); // 통과
});
