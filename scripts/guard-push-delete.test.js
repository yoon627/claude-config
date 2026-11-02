#!/usr/bin/env node
// guard-push-delete.js 회귀 테스트 — 원격을 지우거나 덮어쓰는 push(콜론 refspec·--delete/-d·--force*/-f·
// 묶인 짧은 플래그·--mirror·--prune·+refspec)는 어느 조각에 있어도 ask, 나머지는 판정 없이 통과.
'use strict';
const { execFileSync } = require('child_process');
const path = require('path');
const GUARD = path.join(__dirname, 'guard-push-delete.js');

function decide(raw) {
  let out = '';
  // 비0 종료는 hook 이 판정 없이 흘러가 allow 처럼 보이므로 따로 센다.
  try { out = execFileSync('node', [GUARD], { input: raw, stdio: ['pipe', 'pipe', 'ignore'] }).toString(); }
  catch { return 'crash'; }
  if (!out) return 'allow';
  return JSON.parse(out).hookSpecificOutput.permissionDecision;
}
const bash = (command, mode = 'auto') => JSON.stringify({ tool_name: 'Bash', tool_input: { command }, permission_mode: mode });

const cases = [
  ['git push origin :feat', 'ask'],
  ['rtk git push origin :feat', 'ask'],
  ['git push origin +:feat', 'ask'],
  ['git push origin feat :old', 'ask'],
  ['git push origin :refs/heads/feat', 'ask'],
  ['cd /r && git push origin :feat', 'ask'],
  ['git status; git push origin :feat', 'ask'],
  ['GIT_TRACE=1 git push origin :feat', 'ask'],
  ['git -C /r push origin :feat', 'ask'],
  ['git -c k=v --no-pager push origin :feat', 'ask'],
  ['/usr/bin/git push origin :feat', 'ask'],
  ['echo $(git push origin :feat)', 'ask'],
  ['git push "origin" \':feat\'', 'ask'],
  // 앞말이 git 이 아닌 조각 — 조각 안 어느 위치든 git 을 찾는다.
  ['for b in x y; do git push origin :$b; done', 'ask'],
  ['while read b; do git push origin ":$b"; done < list', 'ask'],
  ['git branch -r --merged | xargs -I{} git push origin :{}', 'ask'],
  ['if git push origin :feat; then echo ok; fi', 'ask'],
  ['env git push origin :feat', 'ask'],
  ['sudo git push origin :feat', 'ask'],
  ['>/dev/null git push origin :feat', 'ask'],
  ['rtk proxy git push origin :feat', 'ask'],
  ['C:/Git/bin/git.exe push origin :feat', 'ask'],
  ["'C:\\Git\\bin\\git.exe' push origin :feat", 'ask'],
  ['{ git push origin :feat; }', 'ask'],
  ['git --attr-source HEAD push origin :feat', 'ask'],
  // 따옴표·치환·줄 이음·리다이렉트
  ['git commit -m "a\\"b" && git push origin :feat', 'ask'],
  ['echo "$(git push origin :feat)"', 'ask'],
  ['echo "`git push origin :feat`"', 'ask'],
  ['git push origin :$(git branch --show-current)', 'ask'],
  ['git push origin \\\n:feat', 'ask'],
  ['git \\\npush origin :feat', 'ask'],
  ['git push 2>&1 origin :feat', 'ask'],
  ['bash -c "git push origin :feat"', 'ask'],
  ['eval "git push origin :feat"', 'ask'],
  // 치환이 끝나면 따옴표 상태 복원 · 짝 없는 아포스트로피 · 결합 플래그 · ANSI-C 따옴표
  ['echo "$(date)"; git push origin :f', 'ask'],
  ['echo "`date`"; git push origin :f', 'ask'],
  ['echo "x $(date) y" && git push origin :f', 'ask'],
  ["git commit -m \"$(cat <<'EOF'\nmsg\nEOF\n)\" && git push origin :f", 'ask'],
  ["# don't forget\ngit push origin :f", 'ask'],
  ["git commit -F - <<EOF\ndon't\nEOF\ngit push origin :f", 'ask'],
  ["bash -lc 'git push origin :f'", 'ask'],
  ["git push origin $':f'", 'ask'],
  // 권한 모드와 무관하게 ask — 원래 ask 규칙은 auto 에서도 확인을 띄웠다.
  [['git push origin :feat', 'default'], 'ask'],
  // 삭제·force·mirror·prune — ask 규칙이 못 보는 조각(`bash -c`·`git -C`·`env`)과 형태(묶인 짧은 플래그)
  ['bash -c "git push origin --delete feat"', 'ask'],
  ['git -C /r push -uf origin x', 'ask'],
  ['env git push -f origin main', 'ask'],
  ['git push --mirror origin', 'ask'],
  ['git push --force-with-lease origin feat', 'ask'],
  ['git push --force-with-lease=feat:abc origin feat', 'ask'],
  ['git push --force-if-includes origin feat', 'ask'],
  ['git push --force origin feat', 'ask'],
  ['git push origin feat --force', 'ask'],
  ['git push -d origin feat', 'ask'],
  ['git push origin -d feat', 'ask'],
  ['git push --delete origin feat', 'ask'],
  ['git push -fu origin x', 'ask'],
  ['git push -df origin x', 'ask'],
  ['git push -nf origin x', 'ask'],
  ['git push origin --prune', 'ask'],
  ['git push --prune origin', 'ask'],
  ['git push origin +feat', 'ask'],
  ['git push origin -- +feat', 'ask'],
  ['git push origin -- :feat', 'ask'],
  ['rtk git push -f origin x', 'ask'],
  ['eval "git push -f origin x"', 'ask'],
  ['cd /r && git push origin --delete feat', 'ask'],
  ['echo "$(git push --prune origin)"', 'ask'],
  // git 은 모호하지 않은 축약 옵션을 받는다 — 세 글자 이상의 앞부분도 본다(모호한 것은 ask 쪽으로)
  ['git push --dele origin feat', 'ask'],
  ['git push --m origin', 'ask'],
  ['git push --pru origin', 'ask'],
  ['git push --forc origin feat', 'ask'],
  ['git push --d origin feat', 'ask'],
  // 값과 `--` 뒤의 refspec 은 플래그가 아니다 — 이 형태들은 통과
  ['git push --no-delete origin x', 'allow'],
  ['git push --porcelain origin x', 'allow'],
  ['git push --progress origin x', 'allow'],
  ['git push -o ci.skip origin x', 'allow'],
  ['git push -oci.skip origin x', 'allow'],
  ['git push -uo ci.skip origin x', 'allow'],
  ['git push -o -f origin x', 'allow'],
  ['git push --push-option=ci.skip origin x', 'allow'],
  ['git push --push-option ci.skip origin x', 'allow'],
  ['git push --repo -f origin x', 'allow'],
  ['git push --receive-pack -d origin x', 'allow'],
  ['git push --exec=-f origin x', 'allow'],
  ['git push origin -- -f', 'allow'],
  ['git push origin -- x:y', 'allow'],
  ['git push --no-force-with-lease origin x', 'allow'],
  ['git push -uq origin x', 'allow'],
  ['git push -4 origin x', 'allow'],
  ['git push --tags origin', 'allow'],
  ['git push --all origin', 'allow'],
  ['git push --dry-run origin x', 'allow'],
  ['git fetch --prune origin', 'allow'],
  ['git branch -d feat', 'allow'],
  ['git branch -f feat main', 'allow'],
  ['echo "git push -f origin x"', 'allow'],
  ['git push origin feat', 'allow'],
  ['git push origin :', 'allow'], // matching push — 삭제 아님
  ['git push origin HEAD:feat', 'allow'],
  ['git push -u origin HEAD', 'allow'],
  ['echo "git push origin :x"', 'allow'],
  ['echo \'git push origin :x\'', 'allow'],
  ['git log :x', 'allow'],
  ['git log --format=%H:%s', 'allow'],
  ['git push origin main: 2>&1', 'allow'],
  ["git commit -m \"$(cat <<'EOF'\nfix: a\n:note\nEOF\n)\" && git push origin feat", 'allow'],
  ['git -C push log :x', 'allow'], // -C 의 값이 push 라는 이름의 디렉토리
  ['ls -la', 'allow'],
];

let fail = 0;
for (const [cmd, want] of cases) {
  const [c, mode] = Array.isArray(cmd) ? cmd : [cmd];
  const got = decide(bash(c, mode));
  if (got !== want) { fail++; console.log(`FAIL [${c}] mode=${mode || 'auto'}: want ${want}, got ${got}`); }
}
for (const [label, raw, want] of [
  ['비JSON', 'not json', 'allow'],
  ['빈 입력', '', 'allow'],
  ['command 없음', JSON.stringify({ tool_name: 'Bash', tool_input: {} }), 'allow'],
  ['닫히지 않은 따옴표', bash('git push origin ":feat'), 'ask'],
]) {
  const got = decide(raw);
  if (got !== want) { fail++; console.log(`FAIL ${label}: want ${want}, got ${got}`); }
}
const total = cases.length + 4;
console.log(fail ? `${fail}/${total} failed` : `${total}/${total} passed`);
process.exit(fail ? 1 : 0);
