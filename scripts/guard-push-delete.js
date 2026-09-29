#!/usr/bin/env node
// PreToolUse(Bash) guard — 콜론 refspec 원격 삭제(`git push <remote> :<ref>`, rtk 접두 포함)에 ask.
//
// permissions.ask 규칙으로는 표현할 수 없어서 hook 으로 둔다: 규칙 문자열이 `:*` 로 끝나면
// prefix 규칙이 돼 앞의 `*` 가 풀리지 않고, `:*` 가 중간에 있으면 매 세션 시작마다 안내가 뜬다.
// 권한 모드와 무관하게 ask — 대체한 ask 규칙이 auto 모드에서도 확인을 띄웠다(CLAUDE.md §8(b)).
// 셸 문법을 완전히 해석하지 않으므로 애매하면 ask 쪽으로 틀린다(주석·heredoc 본문도 명령으로 본다).
// stdin JSON 파싱 실패는 fail-open.
'use strict';

// git 전역 옵션 중 값을 다음 토큰으로 받는 것 — 그 값을 부속명령으로 오인하지 않게 건너뛴다.
const OPT_WITH_VALUE = new Set([
  '-C', '-c', '--git-dir', '--work-tree', '--namespace', '--exec-path', '--config-env', '--attr-source',
]);

// 셸 단어로 나누고 명령 경계(; & | 개행 괄호 단독 중괄호 $( 백틱)는 null 로 표시한다.
// 큰따옴표 안의 $( 와 백틱도 실행되므로 경계로 보고, 치환이 끝나면 그 전의 따옴표 상태로
// 돌아간다(`-m "$(cat <<'EOF' … )" && …` 의 닫는 `"` 가 새 따옴표를 열지 않게). 치환 직전 단어가
// `:`·`+:` 이면(`:$(git branch --show-current)`) 삭제 refspec 이 치환으로 이어지는 것이라 `:$` 로 남긴다.
// 짝 없는 작은따옴표(주석·heredoc 의 아포스트로피)는 글자로 둔다 — 끝까지 삼키면 뒤 명령을 못 본다.
function tokenize(cmd) {
  const out = [];
  const stack = []; // 열린 치환·서브셸: { close, dq }
  let cur = null;
  let dq = false;
  const flush = () => { if (cur !== null) out.push(cur); cur = null; };
  const add = (s) => { cur = (cur || '') + s; };
  const boundary = () => { flush(); out.push(null); };
  const open = (close) => {
    if (cur === ':' || cur === '+:') cur += '$';
    boundary();
    stack.push({ close, dq });
    dq = false;
  };
  const closeIf = (close) => {
    boundary();
    if (stack.length && stack[stack.length - 1].close === close) dq = stack.pop().dq;
  };
  for (let i = 0; i < cmd.length; i++) {
    const ch = cmd[i];
    const next = cmd[i + 1];
    if (ch === '\\' && next === '\n') { i++; continue; }
    if (dq) {
      if (ch === '"') dq = false;
      else if (ch === '\\' && next !== undefined && '"\\$`'.includes(next)) add(cmd[++i]);
      else if (ch === '$' && next === '(') { i++; open(')'); }
      else if (ch === '`') open('`');
      else add(ch);
      continue;
    }
    if (ch === '"') { dq = true; add(''); }
    else if (ch === "'" || (ch === '$' && next === "'")) { // $'…' 도 작은따옴표로 본다
      const q = ch === '$' ? i + 1 : i;
      const end = cmd.indexOf("'", q + 1);
      if (end < 0) { add(ch); continue; }
      add(cmd.slice(q + 1, end));
      i = end;
    } else if (ch === '\\' && next !== undefined) add(cmd[++i]);
    else if (ch === '$' && next === '(') { i++; open(')'); }
    else if (ch === '`') {
      if (stack.length && stack[stack.length - 1].close === '`') closeIf('`');
      else open('`');
    } else if (ch === '(') { boundary(); stack.push({ close: ')', dq: false }); }
    else if (ch === ')') closeIf(')');
    else if (ch === '&' && (cmd[i - 1] === '>' || cmd[i - 1] === '<' || next === '>')) add(ch); // 2>&1, &>
    else if (ch === '\n' || ';&|'.includes(ch)) boundary();
    else if ('{}'.includes(ch) && cur === null && (next === undefined || /[\s;]/.test(next))) out.push(null); // `{ …; }` 그룹 — `-I{}`·`:{}` 는 단어
    else if (/\s/.test(ch)) flush();
    else add(ch);
  }
  flush();
  return out;
}

const isGit = (w) => /^git(\.exe)?$/i.test(w.split(/[\\/]/).pop());

// 조각의 어느 위치든 git 이 나오면 검사한다 — do·then·xargs·env·sudo·rtk proxy 같은 앞말을
// 목록으로 관리하지 않기 위해서다. `-c`(`-lc` 등 결합 포함)·`eval` 뒤의 문자열은 그 자체를 명령으로 다시 본다.
function segmentDeletes(words) {
  for (let j = 0; j < words.length; j++) {
    if ((/^-[A-Za-z]*c$/.test(words[j - 1] || '') || words[j - 1] === 'eval') && isRemoteDelete(words[j])) return true;
    if (!isGit(words[j])) continue;
    let i = j + 1;
    while (i < words.length && words[i].startsWith('-')) i += OPT_WITH_VALUE.has(words[i]) ? 2 : 1;
    if (words[i] === 'push' && words.slice(i + 1).some((w) => /^\+?:./.test(w))) return true;
  }
  return false;
}

function isRemoteDelete(cmd) {
  let seg = [];
  for (const t of [...tokenize(cmd), null]) {
    if (t !== null) { seg.push(t); continue; }
    if (segmentDeletes(seg)) return true;
    seg = [];
  }
  return false;
}

let raw = '';
process.stdin.on('data', (c) => (raw += c));
process.stdin.on('end', () => {
  let cmd;
  try {
    cmd = JSON.parse(raw).tool_input.command;
  } catch {
    process.exit(0);
  }
  if (typeof cmd !== 'string' || !isRemoteDelete(cmd)) process.exit(0);
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'ask',
        permissionDecisionReason:
          '콜론 refspec(`:<ref>`)으로 원격 브랜치를 삭제하는 push 입니다. ' +
          '원격 브랜치 삭제는 항상 확인을 받습니다(CLAUDE.md §8(b)).',
      },
    })
  );
  process.exit(0);
});
