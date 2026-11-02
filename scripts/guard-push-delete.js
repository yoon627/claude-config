#!/usr/bin/env node
// PreToolUse(Bash) guard — 원격을 지우거나 덮어쓰는 push 에 ask: 콜론 refspec(`:<ref>`), `--delete`/`-d`,
// `--force*`(`--force-with-lease`·`--force-if-includes` 포함)/`-f`(`-uf` 처럼 묶인 짧은 플래그 포함),
// `--mirror`, `--prune`, `+<refspec>`. rtk 접두·`git -C <dir>`·`bash -c "…"`·`env` 등 어느 조각에 있어도 본다.
//
// permissions.ask 규칙만으로는 부족해서 hook 으로 둔다: `:*` 로 끝나는 규칙은 prefix 규칙이 돼 앞의 `*` 가
// 풀리지 않고 `:*` 가 중간에 있으면 매 세션 시작마다 안내가 뜨며, 규칙은 `git push …` 로 시작하는 문자열만
// 보므로 `git -C <dir> push`·`bash -c` 안의 push·`-uf` 같은 묶인 플래그를 못 본다(넓은 glob `git push -*f*`
// 은 `-u origin feat/x` 까지 묻게 된다). 규칙 정본은 scripts/permission-rules.json(좁은 형태만).
// 권한 모드와 무관하게 ask — 대체한 ask 규칙이 auto 모드에서도 확인을 띄웠다(CLAUDE.md §8(b)).
// 셸 문법을 완전히 해석하지 않으므로 애매하면 ask 쪽으로 틀린다(주석·heredoc 본문도 명령으로 본다).
// 명령 문자열을 분석하다 예외가 나면 통과가 아니라 ask. stdin JSON 파싱 실패·command 가 문자열이 아니면 fail-open.
'use strict';

// git 전역 옵션 중 값을 다음 토큰으로 받는 것 — 그 값을 부속명령으로 오인하지 않게 건너뛴다.
const OPT_WITH_VALUE = new Set([
  '-C', '-c', '--git-dir', '--work-tree', '--namespace', '--exec-path', '--config-env', '--attr-source',
]);
// push 옵션 중 값을 다음 토큰으로 받는 것 — 그 값(`-o ci.skip`·`--repo -f`)을 플래그나 refspec 으로 보지 않는다.
const PUSH_OPT_WITH_VALUE = new Set(['-o', '--push-option', '--repo', '--receive-pack', '--exec']);
// 원격을 지우거나 덮어쓰는 긴 옵션. git 은 모호하지 않은 축약(`--dele`·`--m`·`--pru`)도 받으므로 세 글자
// 이상의 앞부분이면 같은 것으로 본다 — git 에는 모호한 `--d`·`--fo` 도 ask 쪽으로 틀린다.
const RISKY_LONG = ['--delete', '--mirror', '--prune', '--force'];

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

// pushRisk(args) — `push` 뒤 인자에서 원격을 지우거나 덮어쓰는 형태를 찾아 그 이름을 돌려준다(없으면 null).
// `--` 뒤는 모두 refspec. 긴 옵션은 `=값` 을 떼고 본다. 짧은 플래그는 묶음(`-uf`)을 글자별로 보되
// `o` 부터는 값이다(`-oci.skip` 은 남은 글자가, `-uo ci.skip` 은 다음 단어가 값).
function pushRisk(args) {
  let refsOnly = false;
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (!refsOnly && a === '--') { refsOnly = true; continue; }
    if (!refsOnly && a.startsWith('--')) {
      const name = a.split('=')[0];
      if (PUSH_OPT_WITH_VALUE.has(name)) { if (!a.includes('=')) i++; continue; }
      if (name.startsWith('--force')) return name; // --force, --force-with-lease, --force-if-includes
      if (name.length >= 3) {
        const full = RISKY_LONG.find((o) => o.startsWith(name));
        if (full) return full;
      }
      continue;
    }
    if (!refsOnly && a.length > 1 && a[0] === '-') {
      const flags = a.slice(1);
      for (let k = 0; k < flags.length; k++) {
        const ch = flags[k];
        if (ch === 'o') { if (k === flags.length - 1) i++; break; }
        if (ch === 'd' || ch === 'f') return `-${ch}`;
      }
      continue;
    }
    if (/^\+?:./.test(a)) return ':ref';
    if (a.startsWith('+')) return '+refspec';
  }
  return null;
}

// 조각의 어느 위치든 git 이 나오면 검사한다 — do·then·xargs·env·sudo·rtk proxy 같은 앞말을
// 목록으로 관리하지 않기 위해서다. `-c`(`-lc` 등 결합 포함)·`eval` 뒤의 문자열은 그 자체를 명령으로 다시 본다.
function segmentRisk(words) {
  for (let j = 0; j < words.length; j++) {
    if (/^-[A-Za-z]*c$/.test(words[j - 1] || '') || words[j - 1] === 'eval') {
      const r = commandRisk(words[j]);
      if (r) return r;
    }
    if (!isGit(words[j])) continue;
    let i = j + 1;
    while (i < words.length && words[i].startsWith('-')) i += OPT_WITH_VALUE.has(words[i]) ? 2 : 1;
    if (words[i] === 'push') {
      const r = pushRisk(words.slice(i + 1));
      if (r) return r;
    }
  }
  return null;
}

function commandRisk(cmd) {
  let seg = [];
  for (const t of [...tokenize(cmd), null]) {
    if (t !== null) { seg.push(t); continue; }
    const r = segmentRisk(seg);
    if (r) return r;
    seg = [];
  }
  return null;
}

function reason(form) {
  const what = {
    ':ref': '콜론 refspec(`:<ref>`)으로 원격 브랜치를 삭제하는 push 입니다.',
    '--delete': '`--delete` 로 원격 브랜치를 삭제하는 push 입니다.',
    '-d': '`-d`(묶인 플래그 포함)로 원격 브랜치를 삭제하는 push 입니다.',
    '-f': '`-f`(묶인 플래그 포함)로 원격을 덮어쓰는 force push 입니다.',
    '--mirror': '`--mirror` 로 원격의 ref 전체를 로컬과 같게 덮어쓰고 지우는 push 입니다.',
    '--prune': '`--prune` 으로 로컬에 없는 원격 브랜치를 지우는 push 입니다.',
    '+refspec': '`+<refspec>` 으로 원격을 덮어쓰는 force push 입니다.',
    unparsed: '명령을 분석하다 오류가 나 push 형태를 판정하지 못했습니다 — 확신이 없으면 ask 로 기웁니다.',
  };
  const text = what[form] || `\`${form}\` 로 원격을 덮어쓰는 force push 입니다.`; // --force, --force-with-lease, --force-if-includes
  return `${text} 원격 브랜치 삭제와 force push 는 항상 확인을 받습니다(CLAUDE.md §8).`;
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
  if (typeof cmd !== 'string') process.exit(0);
  let form;
  try {
    form = commandRisk(cmd);
  } catch {
    form = 'unparsed';
  }
  if (!form) process.exit(0);
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'ask',
        permissionDecisionReason: reason(form),
      },
    })
  );
  process.exit(0);
});
