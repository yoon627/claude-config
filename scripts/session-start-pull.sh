#!/bin/sh
# SessionStart 자동 pull — `~/.claude` 를 origin/main 으로 fast-forward 한다.
#
# 계약: 어떤 경로에서도 exit 0. async 훅이라 세션 시작을 막지는 않지만, 비0 으로 새면 하니스가
# 경고를 띄우고 이 훅은 매 세션 도는 자기 배포 경로라 그 잡음이 영구화된다.
# 끄기: export CLAUDE_AUTOPULL_OFF=1  또는  touch ~/.claude/.autopull-off
#   (파일 스위치는 GUI 실행처럼 셸 env 를 못 거는 환경의 즉시 레버다. 이 훅은 자기 자신의 배포
#    경로라, 코드 revert 는 "고장난 그 pull 이 돌아야" 도달하므로 즉시 레버가 될 수 없다.)
#
# 상한: 네트워크 단계만 워치독으로 감싼다(CLAUDE_AUTOPULL_TIMEOUT 초, 기본 8).
#
# 본문을 함수로 감싸고 마지막 줄에서 호출한다: 이 스크립트는 아래 merge 로 **자기 자신을
# 갈아끼울 수 있고**, 셸은 스크립트를 fd offset 기반으로 이어 읽는다. 통째로 파싱된 뒤 실행되게
# 해야 교체 후 남은 바이트를 잘린 명령으로 읽지 않는다.

main() {
  [ "${CLAUDE_AUTOPULL_OFF:-}" = 1 ] && exit 0

  repo="$HOME/.claude"
  [ -e "$repo/.autopull-off" ] && exit 0

  git_dir="$(git -C "$repo" rev-parse --absolute-git-dir 2>/dev/null)" || exit 0
  for _st in rebase-merge rebase-apply MERGE_HEAD BISECT_LOG; do
    if [ -e "$git_dir/$_st" ]; then exit 0; fi
  done

  [ "$(git -C "$repo" rev-parse --abbrev-ref HEAD 2>/dev/null)" = main ] || exit 0
  before="$(git -C "$repo" rev-parse HEAD 2>/dev/null)" || exit 0

  # 상한을 먼저 정한다. 비숫자면 산술식이 0 으로 평가돼 deadline=now 가 되고, 자동 pull 이
  # 무음으로 매번 즉시 죽는다. 상한값이 하니스 timeout(15s)을 넘으면 하니스가 먼저 훅을 죽이는데
  # 하니스는 자손을 거두지 않으므로(wiki git-hook-network-safety) fetch 그룹이 고아로 남는다.
  _t="${CLAUDE_AUTOPULL_TIMEOUT:-8}"
  case "$_t" in ''|*[!0-9]*) _t=8 ;; esac
  [ "$_t" -lt 1 ] && _t=1
  [ "$_t" -gt 12 ] && _t=12

  # 물어볼 경로 자체를 없앤다. 자격증명 프롬프트나 죽은 네트워크에 걸리면 훅은 하니스 timeout
  # 까지 매달린다. `GIT_ASKPASS=echo` 는 쓰지 않는다 — 실패하는 helper 가 아니라 프롬프트
  # 문자열을 자격증명으로 되돌려준다(session-fetch.js 가 같은 이유로 피한다).
  export GIT_TERMINAL_PROMPT=0
  export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh} -o BatchMode=yes -o ConnectTimeout=10"

  # fetch 와 merge 를 쪼개는 이유: 워치독의 kill 이 ff-merge 도중에 떨어지면 `.git/index.lock`
  # 이 남고 워킹트리가 반만 갱신된다. 그 lock 은 이후 모든 pull 을 무음 실패시켜, 이 훅이
  # 없애려는 "조용히 안 도는" 상태를 스스로 만든다. kill 대상은 항상 네트워크 단계여야 한다.
  #
  # stdio 를 끊지 않으면 백그라운드 자식이 호출자의 파이프를 물고 있어, 이 스크립트를 파이프로
  # 읽는 쪽(테스트·CI)이 자식이 죽을 때까지 반환하지 못한다.
  #
  # `set -m` 은 백그라운드 job 을 자기 프로세스 그룹에 둔다. bash(Git Bash·macOS)에서는 이게
  # 그룹 kill 을 가능하게 해 git 이 띄운 ssh·git-remote-https 손자까지 거둔다(실측). dash 는
  # tty 없이 job control 을 켜지 않아 그룹 kill 이 거부되므로 아래 폴백이 받는다(실측).
  set -m
  git -C "$repo" \
    -c core.askpass= \
    -c credential.helper= \
    -c http.lowSpeedLimit=1000 \
    -c http.lowSpeedTime=10 \
    fetch --quiet origin main >/dev/null 2>&1 </dev/null &
  _pid=$!
  set +m

  # 상한은 iteration 수가 아니라 wall-clock 이다. Git Bash 에서 `sleep 0.2` 는 실제 ~235ms 라
  # 카운트로 재면 플랫폼마다 상한이 달라지고 Windows 에서 20% 넘게 초과한다(실측).
  # `date +%s` 는 초 단위라 마감이 절삭된다 — 실제 대기는 (_t-1, _t] 초다. 안전 상한이라
  # 짧아지는 쪽은 무해하다.
  _deadline=$(( $(date +%s) + _t ))
  while kill -0 "$_pid" 2>/dev/null; do
    if [ "$(date +%s)" -ge "$_deadline" ]; then
      # 그룹째 거두고, 그룹 kill 이 안 되는 셸(dash)에서는 직접 자식만이라도 죽인다.
      kill -- "-$_pid" 2>/dev/null || kill "$_pid" 2>/dev/null
      # TERM 을 무시하는 자식(소켓 I/O 에 묶인 native 프로세스)이 있으면 wait 가 상한 없이
      # 붙잡혀 워치독이 무의미해진다 — 짧게 기다린 뒤 KILL 로 승격한다.
      _grace=0
      while kill -0 "$_pid" 2>/dev/null && [ "$_grace" -lt 10 ]; do
        sleep 0.2
        _grace=$(( _grace + 1 ))
      done
      kill -9 -- "-$_pid" 2>/dev/null || kill -9 "$_pid" 2>/dev/null
      break
    fi
    sleep 0.2
  done
  # fetch 가 kill 됐거나 실패했으면 여기서 끝낸다. 그냥 지나가면 **이전 세션이 남긴 stale
  # FETCH_HEAD** 로 origin 과 한 번도 통신하지 않은 채 ff 하고 "updated" 까지 출력한다.
  wait "$_pid" 2>/dev/null || exit 0

  git -C "$repo" merge --ff-only --quiet FETCH_HEAD >/dev/null 2>&1 || exit 0

  after="$(git -C "$repo" rev-parse HEAD 2>/dev/null)" || exit 0
  if [ "$before" != "$after" ]; then
    # `~/.claude` 는 경로가 아니라 사용자에게 보여줄 이름이다 — 확장되면 안 된다.
    # shellcheck disable=SC2088
    echo "~/.claude updated from origin/main ($before -> $after); review pulled changes before relying on scripts/hooks this session."
  fi
  exit 0
}

main "$@"
