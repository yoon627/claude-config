#!/usr/bin/env node
// ~/.claude/statusline.js — Claude Code statusLine command (Windows/Node)

const fs = require('fs');
const path = require('path');

const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null);

// "53%" — 남은 %(100 - used). 숫자가 아니면 ''.
function remainingPct(usedPct) {
  const used = num(usedPct);
  return used != null ? Math.round(Math.max(0, 100 - used)) + '%' : '';
}

// "53%(20:30)" — 남은 %와 리셋 시각(epoch 초, 로컬 시각). 숫자가 아닌 값은 없는 것으로 보고, 둘 다 없으면 ''.
function windowPiece(usedPct, resetsAt) {
  const pct = remainingPct(usedPct);
  const reset = num(resetsAt);
  const d = reset != null ? new Date(reset * 1000) : null;
  const tm = d && !Number.isNaN(d.getTime())
    ? String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
    : '';
  return pct && tm ? `${pct}(${tm})` : pct || (tm ? `(${tm})` : '');
}

// "<label> 53%(20:30) wk 72%" — 5시간 창 뒤에 주간 창(남은 % 만). 둘 다 비면 ''.
function quotaPiece(label, fiveHour, weekly) {
  const body = [fiveHour, weekly && 'wk ' + weekly].filter(Boolean).join(' ');
  return body ? `${label} ${body}` : '';
}

// 없는 경로만 null — 권한 오류 등은 던져서 부모 repo 로 넘어가지 않게 한다.
function statOrNull(p) {
  try { return fs.statSync(p); } catch (e) {
    if (e.code === 'ENOENT' || e.code === 'ENOTDIR') return null;
    throw e;
  }
}

// "main" / "feat @wt:<dir>" — cwd 에서 위로 .git 을 찾아 HEAD 를 직접 읽는다. 갱신마다 새로 뜨는
// 프로세스라 git 을 띄우면 프로세스 생성이 갱신 수만큼 곱해진다. detached HEAD·repo 밖이면 ''.
function gitLabel(cwd) {
  let dir;
  try { dir = fs.realpathSync.native(cwd); } catch (_) { dir = path.resolve(cwd); }
  for (; ; dir = path.dirname(dir)) {
    const dotGit = path.join(dir, '.git');
    const stat = statOrNull(dotGit);
    let gitDir = null;
    if (stat && stat.isFile()) {
      const m = /^gitdir:\s*(.+?)\s*$/m.exec(fs.readFileSync(dotGit, 'utf8'));
      if (!m) return '';
      gitDir = path.resolve(dir, m[1]);
    } else if (stat && stat.isDirectory() && statOrNull(path.join(dotGit, 'HEAD'))) {
      gitDir = dotGit; // HEAD 없는 빈 .git 디렉터리는 git 처럼 건너뛰고 계속 올라간다
    }
    if (gitDir) {
      const head = path.join(gitDir, 'HEAD');
      if (!fs.statSync(head).isFile()) return '';
      const ref = /^ref: refs\/heads\/(.+)$/.exec(fs.readFileSync(head, 'utf8').trim());
      // reftable 저장소의 HEAD 는 'refs/heads/.invalid' 자리표시자라 branch 를 알 수 없다.
      // 출력은 터미널이 그대로 렌더하므로 ref 이름에 올 수 없는 제어문자·공백이 있으면 버린다.
      if (!ref || ref[1] === '.invalid' || /[\x00-\x20\x7f]/.test(ref[1])) return '';
      // 연결된 worktree 의 gitdir 에만 commondir 가 있다(submodule 의 .git/modules/<name> 에는 없다).
      if (!fs.existsSync(path.join(gitDir, 'commondir'))) return ref[1];
      const wtName = path.basename(dir);
      return /[\x00-\x1f\x7f]/.test(wtName) ? ref[1] : `${ref[1]} @wt:${wtName}`;
    }
    if (path.dirname(dir) === dir) return '';
  }
}

// 하니스가 stdin 을 닫지 않고 떠나면 'end' 가 오지 않아 고아로 남아 그 cwd 를 잡는다 — 그릴 대상이 없으니 출력 없이 끝낸다.
const STDIN_MS = 3000;
const stdinTimer = setTimeout(() => process.exit(0), STDIN_MS);
const chunks = [];
process.stdin.on('data', d => chunks.push(d));
process.stdin.on('end', () => {
  clearTimeout(stdinTimer);
  let input = {};
  try { input = JSON.parse(Buffer.concat(chunks).toString()); } catch (_) {}
  if (!input || typeof input !== 'object') input = {};

  const parts = [];

  // 1. 5-hour + weekly rate limits: "Opus 53%(20:30) wk 72%"
  //    두 창은 서로 독립적으로 없을 수 있다 — Claude Code 는 최신 API 응답에 그 창의 헤더가 없거나
  //    리셋 시각이 지나면 그 창을 뺀다.
  const rl = input.rate_limits || {};
  const fiveHour = rl.five_hour || {};
  const sevenDay = rl.seven_day || {};
  // 레이블 'claude' 대신 현재 모델명(stdin 의 model.display_name). 없으면 'claude' 폴백.
  const model = input.model && input.model.display_name;
  const claudePiece = quotaPiece(typeof model === 'string' && model ? model : 'claude',
    windowPiece(fiveHour.used_percentage, fiveHour.resets_at),
    remainingPct(sevenDay.used_percentage));
  if (claudePiece) parts.push(claudePiece);

  // 2. Context usage percentage
  const usedPct = input.context_window && input.context_window.used_percentage;
  if (usedPct != null) {
    parts.push('ctx ' + Math.round(usedPct) + '%');
  }

  // 3. Git branch + worktree indicator from workspace.current_dir
  const cwd = (input.workspace && input.workspace.current_dir) || (input.cwd || '');
  if (typeof cwd === 'string' && cwd) {
    let label = '';
    try { label = gitLabel(cwd); } catch (_) { /* 읽을 수 없는 .git — branch 만 뺀다 */ }
    if (label) parts.push(label);
  }

  process.stdout.write(parts.join(' | '));
});
