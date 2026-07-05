#!/usr/bin/env zsh
# gwl.zsh 를 ~/.zshrc 에 marker 블록으로 멱등 등록한다 (dot-source 한 줄).
# scripts/install-gwl.ps1 의 zsh 대응물 — 같은 marker·경고·멱등 규약.
#
# 실행: ~/.claude/scripts/install-gwl.zsh  (1회, 수동)
# 활성화: source ~/.zshrc  또는 새 터미널.
emulate -L zsh

# dot-source 대상은 문서상 clone 위치(~/.claude)로 고정한다 — worktree 가 아니라
# main 을 가리켜야 `git pull` 로 gwl.zsh 갱신이 반영되고 배선이 안정적이다.
claude_home="$HOME/.claude"
gwl_script="$claude_home/scripts/gwl.zsh"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [[ -n "$repo_root" && "${repo_root%/}" != "${claude_home%/}" ]]; then
  print -r -- "Warning: repo is at $repo_root, not ~/.claude."
  print -r -- "         gwl will be wired to $gwl_script regardless (the documented location)."
fi

if [[ ! -f "$gwl_script" ]]; then
  print -ru2 -- "Error: gwl.zsh not found at $gwl_script. Clone this repo to ~/.claude first."
  exit 1
fi

profile="$HOME/.zshrc"
source_line='source "$HOME/.claude/scripts/gwl.zsh"'
begin='# >>> claude-config gwl >>>'
end='# <<< claude-config gwl <<<'

# 멱등: 두 marker 모두 있으면 설치됨, 정확히 하나만 있으면 손상.
has_begin=0
has_end=0
if [[ -f "$profile" ]]; then
  grep -qF -- "$begin" "$profile" && has_begin=1
  grep -qF -- "$end" "$profile" && has_end=1
fi

if (( has_begin && has_end )); then
  print -r -- "gwl already installed in $profile - nothing to do."
  exit 0
fi
if (( has_begin || has_end )); then
  print -ru2 -- "Error: partial gwl marker block in $profile. Remove the stray marker line(s) and re-run."
  exit 1
fi

# 관리 블록 밖에 inline gwl 이 있으면 heads-up (zsh 형 `gwl() {}` 과 `function gwl {` 둘 다).
if [[ -f "$profile" ]] && grep -qE '^[[:space:]]*(function[[:space:]]+)?gwl[[:space:]]*(\(\))?[[:space:]]*\{' "$profile"; then
  print -r -- "Note: an inline 'gwl' function already exists in $profile."
  print -r -- "      The sourced copy is appended after it and wins; remove the old one to avoid confusion."
fi

# append 전 파일 끝 개행 보장 (파일이 개행으로 안 끝나면 marker 가 마지막 줄에 붙는다).
if [[ -s "$profile" && -n "$(tail -c 1 -- "$profile")" ]]; then
  print >> "$profile"
fi
{
  print -r -- "$begin"
  print -r -- "$source_line"
  print -r -- "$end"
} >> "$profile"

print -r -- "Installed gwl into $profile"
print -r -- "Activate now:  source ~/.zshrc   (or open a new terminal)"
