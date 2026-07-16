---
title: gwl-zsh-wt-main — gwl zsh 레포 관리 스크립트 + wt main 복귀
status: done
started: 2026-07-05
updated: 2026-07-05
---

# Goal
1. gwl 을 레포에서 관리: `scripts/gwl.zsh`(함수) + `scripts/install-gwl.zsh`(멱등 설치) 추가 — Windows 의 `gwl.ps1`/`install-gwl.ps1` 패턴 미러. `~/.zshrc` 의 수동 인라인 `gwl()` 을 marker 블록 source 로 교체.
2. `skills/wt/SKILL.md` switch 에 main worktree 복귀 경로 추가 — 대상이 main 이면 `EnterWorktree`(하위만 허용) 대신 `ExitWorktree(keep)`.
3. README 의 gwl 절 + scripts 트리 동기화.

# Progress
- 2026-07-05: 조사 완료 — 레포에 `prompt-gwl.py`(프롬프트 훅, 글로벌 미등록)·`gwl.ps1`/`install-gwl.ps1`(Windows) 존재, zsh 대응물만 gap. CI(lint.yml) 는 shellcheck 를 `scripts/*.sh` 만 대상 → `.zsh` 는 제외. 가드는 `~/.zshrc`(repo 밖) 편집 allow 확인. plan 작성.
- 2026-07-05: plan-review(Claude CONDITIONAL + codex) 반영 — 이중마커/merge순서/ExitWorktree 가정. 구현 완료: scripts/gwl.zsh(toplevel 정확일치), scripts/install-gwl.zsh(ps1 parity), skills/wt/SKILL.md(main→ExitWorktree 관찰 fallback), README(macOS 스텝+zsh 프로즈+트리). 검증: A1 worktree 안 `→`1개 ✓, A2 temp HOME 10/10 ✓, zsh -n ✓.
- 2026-07-05: code-review(Claude APPROVE, blocker/major 0 + codex) — minor 2건 fix(SKILL.md:25 노트 중립화, :52 cwd==main 판정법 명시), 나머지 wontfix/false-positive(disposition 기록). simplify: 제거 대상 없음. 최종검증 재통과. 커밋 `2c96d95` (4파일).
- 2026-07-05: push → PR #72 → **merge**(`18f2b07`, CI 통과). 로컬 main ff-pull(gwl.zsh·install-gwl.zsh main 반영). 활성화 완료: `~/.zshrc.bak` 백업 → 인라인 제거 → installer 실행(marker 블록) → 실 source 로 `gwl` `→`1개 실동작 + 멱등 재실행 확인. ⚠️ 현 Claude 세션 `!`/Bash 는 시작 스냅샷이라 `! gwl` 은 다음 세션/새 터미널부터.

# Next
(전부 완료 — merge·활성화 끝. 남은 것 없음)
- 선택: `~/.zshrc.bak` 백업 파일 정리(사용자 판단). worktree `gwl-zsh-wt-main` 은 `/wt rm` 로 정리 가능.
- 현 세션에서 `! gwl` 은 스냅샷 때문에 미동작 — 새 터미널/다음 세션부터 유효.

# Decisions
- **gwl.zsh 현재위치 판정 = `git rev-parse --show-toplevel` 정확일치** (ps1 의 `StartsWith` prefix 방식 미러 금지). 이유(codex blocker): 이 레포는 worktree 가 main 하위(`~/.claude/.claude/worktrees/<name>`)라 main path 가 worktree path 의 prefix → prefix 방식이면 worktree 안에서 main·worktree **두 줄 다** `→` 표시. toplevel 정확일치는 항상 1개만 매칭. `${line%% *}` 로 path 추출 후 trailing slash 제거해 비교.
- gwl.zsh zsh 가드레일: `emulate -L zsh`, `IFS= read -r`, `print -r --`, `[[ ]]` 양변 인용(리터럴 동등, glob 금지), 경로 공백 없음 가정 명시(주석).
- 인자 passthrough 안 함(`git worktree list` 고정 — `--porcelain` 등으로 split 깨짐 방지, ps1 과 동일).
- 인코딩: macOS/zsh 는 UTF-8 기본 → BOM 불필요(ps1 은 PS5.1 때문에 BOM).
- 설치 대상 프로필 = `~/.zshrc` (인터랙티브 sourced → Claude `!`/Bash snapshot 에도 반영). `.zshenv` 아님.
- installer 확장자 `.zsh`, shebang `#!/usr/bin/env zsh` — `.ps1` 쌍과 시각적 대칭 + shellcheck 제외. inline gwl 탐지 정규식은 zsh 스타일 `gwl() {` 과 `function gwl {` 둘 다 매치. `~/.zshrc` 없으면 append 로 생성.
- **source 대상 고정 = `~/.claude/scripts/gwl.zsh`** (ps1 이 `~/.claude` 문서상 위치로 고정하는 것 미러 — `git pull` 반영, worktree 배선 회피). ⇒ **실제 `~/.zshrc` 활성화는 merge 후**에만 정상(그 전엔 main 에 gwl.zsh 없어 source 실패). 세션 내에선 (a) worktree 사본 직접 source 로 gwl.zsh 동작 검증, (b) temp HOME 대상 installer 멱등성 검증. 실 활성화(인라인 제거+설치)는 merge 후 수동 단계로 Report 에 명시.
- Claude `!`/Bash 는 세션 시작 shell snapshot 사용 → `.zshrc` 변경은 **다음 세션/새 터미널부터** 반영(현 세션 무효). acceptance 는 이를 감안.
- settings.json 미변경 — Q1 에서 사용자가 "zsh 설치 스크립트"만 선택(prompt-gwl 글로벌 등록 제외).
- wt main 복귀: **대상 path == `git worktree list --porcelain` 첫 worktree(=main) path** 면(브랜치명 아님 — main/master 무관) `ExitWorktree(keep)`. `/wt 1`(정수)·`/wt <main브랜치명>`(정확일치) 양 경로 모두 이 분기 적용. 이미 main 이면 no-op(무해). 세션이 EnterWorktree 경유 아니면(worktree 안에서 시작) ExitWorktree no-op → main 복귀 불가, 사용자에게 안내.

# Key Files
- `scripts/gwl.zsh` (신규) — zsh gwl 함수
- `scripts/install-gwl.zsh` (신규) — ~/.zshrc 멱등 설치
- `scripts/gwl.ps1` / `scripts/install-gwl.ps1` — 미러 대상(참조)
- `skills/wt/SKILL.md` — switch 섹션(39-45줄) main 분기 추가
- `README.md` — 37-39(설치 안내), 357-364(gwl 절), 538-540(트리)
- `~/.zshrc` (repo 밖) — 36-37줄 인라인 제거 + marker 블록

# Workflow Findings
- **worktree 정리 미실행** (사용자 2회 지적): dlc 는 step16 Report 가 종점·정리 단계 없음(grep 확인), 정리는 `/e` step5 몫인데 dlc/수동merge→`/e` handoff 부재 → Report 에서 멈춰 worktree 방치. 부차: `e` step5 도 원격 브랜치 미포함(로컬만), `gh pr merge --delete-branch` 미사용. 수정 후보: dlc step16 에 "merge/done 이면 `/e` 정리 제안" handoff + `e` step5 원격 브랜치 옵션. 발생 1회. → feedback memory `worktree-cleanup-after-merge` 적립. (승인 시 wt→dlc 로 자산 수정)

# Blockers
- (설계로 해소) A3 활성화 merge 의존 → 실 `~/.zshrc` 설치는 merge 후 수동 단계(Report 안내). 세션 내 검증은 worktree 사본 source + temp HOME.
- (설계로 해소) 이중 마커 → toplevel 정확일치.
- (설계로 해소) ExitWorktree no-op fallback → 세션 이력 추측 대신 **툴 반환 관찰**로 분기(복귀 실패면 사용자 안내). 핵심 복귀 동작은 이 세션 실측(doc-slim exit → main) 으로 확인.

# Deferred
- gwl.ps1(`:16`)·prompt-gwl.py(`:29`)도 동일 이중 `→` 잠재버그(nested worktree 에서 main 도 prefix 매치). 범위 밖(Windows/훅, 별도 테스트 필요) — 이번엔 gwl.zsh 만 정본 구현. 심각도 minor(현 사용선 미노출). (§3-4)

# Acceptance
- A1 gwl.zsh: `zsh -n scripts/gwl.zsh` 통과 + **worktree 안에서** source 후 `gwl` 실행 시 worktree 목록 출력, `→` **정확히 1개**(현재 worktree). (실행·관찰 — main 아닌 worktree 에서)
- A2 install-gwl.zsh 멱등+parity: temp HOME 대상 — ① 1회 → marker 블록 1개 + source 라인; ② 2회 → "nothing to do", 블록 1개 유지; ③ 한쪽 marker 만 → error exit; ④ gwl.zsh 부재 → error exit; ⑤ 파일 끝 개행 없어도 안전 append; ⑥ `~/.zshrc` 부재 시 생성; ⑦ 기존 `gwl() {}` inline heads-up. (실행·관찰)
- A3 실 활성화(merge 후 수동): Report 에 절차 명시 — 백업(`cp ~/.zshrc ~/.zshrc.bak`) → 인라인 `gwl()` 제거 → `~/.claude/scripts/install-gwl.zsh` 실행 → 새 터미널서 `gwl` 동작. 세션 내 미실행(source 대상이 merge 후 존재).
- A4 skills/wt/SKILL.md: switch 에 main→`ExitWorktree(keep)` 분기(정수 N=1·정확일치 양 경로, path 로 main 판정, 이미 main 이면 no-op 보고, 복귀 실패 관찰 시 안내). 핵심 복귀 동작은 이 세션 실측으로 확인(스펙+실측).
- A5 README 동기화: gwl.zsh·install-gwl.zsh 가 ① gwl 프로즈절 ② scripts 트리 ③ **macOS Install 절(122-178) 설치 스텝** ④ 기존 Windows 절 옆 플랫폼 구분, no-space 한계·next-session 반영 주석 포함. (grep+정독)

# Review Disposition
- SKILL.md:25 노트 PowerShell-only (이 PR 이 zsh gwl 추가 → 자기 주제 doc drift) → **fix** (셸 gwl 함수(ps1/zsh) 로 중립화).
- SKILL.md:52 cwd==main 판정법 미명시 → **fix** (`git rev-parse --show-toplevel`==첫 porcelain worktree 명시).
- `${line%% *}` 공백경로 (codex major) → **wontfix**: 무공백 worktree scope 문서화(헤더+README), ps1 parity. `--porcelain -z` 는 pretty 출력 재구성 필요라 과함.
- inline 잔존 (codex major) → **wontfix**: installer heads-up + A3 활성화절차가 인라인 제거, ps1 parity(자동삭제는 사용자 커스텀 위험).
- symlink 정확일치 취약 (codex minor) → **false-positive**: code-reviewer 가 symlinked `/tmp` 에서 양쪽 physical 정규화 일치 실측(견고).
- 파이프 exit status·sourced `exit` footgun·.zsh CI 부재 (codex/claude minor) → **wontfix**: ps1 parity·헤더 용법 문서화·shellcheck 는 zsh 파싱 불가(불가피). sourced 는 execute 용도 문서로 완화.
