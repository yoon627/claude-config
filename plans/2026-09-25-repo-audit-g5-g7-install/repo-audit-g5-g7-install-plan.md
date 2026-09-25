---
title: repo-audit-g5-g7-install — install-hooks 설치 위치·백업, gwl 이중 마커, ps1 BOM
status: in_progress
started: 2026-09-25
updated: 2026-09-25
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

`install-hooks.{sh,ps1}` 가 linked worktree·`core.hooksPath`·비-git 디렉토리에서 제대로 동작하고 기존 훅 백업을 잃지 않게 한다. `gwl` 이 중첩 worktree 에서 한 행에만 `→` 를 붙이게 하고, `.editorconfig` 가 ps1 을 UTF-8 BOM 으로 저장하게 한다. (pre-push 가드의 원격 범위는 별도 단위 `push-remote-scope` 로 분리 — 사용자 결정 2026-09-25.)

# Intent

- 링크: `plans/2026-09-25-repo-audit-followups/intent.md` 의 `repo-audit-g5-g7-install` 단위. 항목 원본은 `plans/2026-09-25-repo-audit-remaining/repo-audit-remaining-plan.md` `# Deferred` G5·G6·G7.
- 규모: medium(설치 스크립트 2 + gwl 2 + 설정 1 + 테스트, 목적 3).
- 분할: 묶음 → `plans/2026-09-25-repo-audit-followups/intent.md` — pre-push 가드의 원격 범위(원래 G5 넷째 항목)를 `push-remote-scope (미착수)` 로 떼어 냈다(사용자 결정 2026-09-25). 이유: plan-reviewer 가 강한 우려 7건(래퍼 인자의 설치 시점 확장, 추적 ref≠push 대상[pushurl·`origin/<x>` 충돌], 인자 없는 옛 래퍼 호환과 fail-closed 모순, 공허해지는 기존 테스트, ps1 skip, dogfood·혼합 상태, rsha 검증)을 낸 라이브 보안 정책 변경이라 설치 스크립트 수정과 같은 PR 에서 검증하기에 크다. 남은 G5(설치)·G6·G7 은 각자 머지할 수 있지만 작은 수정 셋이라 한 PR 로 리뷰하고 되돌림은 커밋 단위로 한다(G1/G2·G3/G4 와 같은 선택).
- Constraints: ps1 은 PS 5.1 에서도 돈다 — PS7 전용 구문 금지. pwsh 7 로 검증하고 PS 5.1 은 미검증으로 남긴다(G2 와 같음). 래퍼 내용(pre-commit·pre-push)은 바꾸지 않는다 — 이미 설치된 repo 가 재설치 없이 그대로 동작한다.
- Out of scope: pre-push 가드의 원격 범위(→ `push-remote-scope`), post-checkout 의 Windows ~24s 상한(README 451 기록, 별도), 가드의 패턴 목록, bootstrap 의 훅 설치 자동화, 비ASCII 가 든 BOM 없는 ps1 의 변환(→ audit-low-batch 의 PS5.1 CP949 디코딩).

재현(2026-09-25, git 2.54, pwsh 7.6.6):
- `git rev-parse --path-format=absolute --git-path hooks` 는 linked worktree 에서 공용 `.git/hooks`, `core.hooksPath` 가 있으면 그 경로(`.husky/_`)를 준다. 현 sh 는 `$repo_root/.git/hooks` 라 linked worktree(`.git` 이 파일)에서 실패한다 — 착수 뒤 테스트로 확정.
- ps1 BOM: `gwl.ps1`·`notify-hook.ps1` 만 BOM. BOM 없는 ps1 중 비ASCII 가 든 것이 있다 — `pre-commit-check.ps1`(em dash)·`install-hooks.ps1`·`bootstrap/setup.ps1`(한글)·`bootstrap/install-codex-skill.ps1`·`run_worklog.ps1`. (처음 적은 "나머지는 순수 ASCII" 는 틀렸다 — 두 번째 grep 의 바이트 범위식이 잘못돼 0 이 나왔고 plan-reviewer 가 잡았다.)

# Acceptance

1. 설치 위치: `install-hooks.sh`·`.ps1` 이 `git rev-parse --git-path hooks` 에 설치한다 — linked worktree 에서도 공용 hooks, symlink 된 `.git/hooks` 는 그 대상. `core.hooksPath` 가 설정됐고(설정 위치 불문) 그 경로가 `<git-common-dir>/hooks` 와 다른 디렉토리면(sh `-ef`·문자열, ps1 대소문자 무시 문자열) 어떤 쓰기보다 먼저 거부하고 그 경로·이유를 알린 뒤 exit 1 — hooksPath 가 기본 디렉토리를 가리키면 설치. git 2.30 이하(`--path-format` 을 되풀이)면 거부하고 2.31 을 알린다. git 밖에서는 "Not inside a git repo." 로 exit 1 — ps1 은 git 을 Process 헬퍼(`Invoke-Git`)로 불러 PS 5.1 의 native stderr 종료 오류를 피한다. 검증: `install-hooks.test.js` sh·ps1(로컬·전역 hooksPath 거부, 기본 디렉토리·symlink 설치, 옛 git shim).
2. 백업: 내용이 다른 기존 훅은 `<hook>.bak.<UTC yyyyMMddTHHmmssZ>`(있으면 `.1`…)로 옮기고 덮지 않는다 — 두 번 설치해도 두 백업이 다 남는다. 같은 내용이면 백업하지 않는다. ps1 은 `Move-Item -Force` 를 쓰지 않는다. 검증: 테스트(백업 내용·이름 형식) + 기존 P4 는 `.bak*` 가 하나도 없는지로 강화.
3. ps1 실행 증거: `PWSH=~/.local/powershell/pwsh node scripts/install-hooks.test.js` 가 `ps1: ran` 을 출력하고 ALL PASS(`verify.sh` 는 PATH 에 pwsh 가 없으면 ps1 을 skip 하므로 별도 증거).
4. gwl: `gwl.ps1`·`prompt-gwl.py` 가 `git rev-parse --show-toplevel`(git 밖이면 cwd)과 일치하는 경로 중 가장 긴 한 행에만 `→`. 검증: `test_prompt_gwl.py`(parse 의 nest 판정 + 임시 repo·symlink cwd 로 `main()`) + pwsh 실측(옛 ps1 은 두 행에 `→`).
5. `.editorconfig` `[*.ps1]` 에 `charset = utf-8-bom`.
6. README install-hooks·gwl 절·permissions.deny 문장·트리 갱신. CLAUDE.md §8 의 "repo 로컬 `core.hooksPath` 가 있으면 설치해도 무효다" 는 새 동작(설치 거부 → 보호 없음)에서도 참이라 고치지 않는다. intent 에 이 plan 경로와 `push-remote-scope (미착수)`.
7. 전체: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음), plan-lint 통과.

# Progress

- 2026-09-25: 착수(`/wt`). Explore — 설치 스크립트·가드·gwl 3종·`.editorconfig`·기존 테스트 하네스(`pre-commit-check.test.sh` 는 pwsh 가 있으면 ps1 도 돈다), `--git-path hooks` 실측.
- 2026-09-25: plan-reviewer 전에 G6·G7 을 먼저 구현했다(절차 역순 — 기록). G6 Red: 새 `test_prompt_gwl.py` 가 옛 코드에서 `['.claude','feat']` 로 실패, pwsh 로 옛 `gwl.ps1` 이 중첩 worktree 에서 두 행에 `→`(scratchpad `g6_pwsh.sh`).
- 2026-09-25: plan-reviewer(+codex) CONDITIONAL — 강한 우려 7(모두 원격 범위) → 사용자 결정으로 `push-remote-scope` 분리. 약한 우려 반영: hooksPath 유효 경로 비교·쓰기 전 거부, 백업 형식·no-clobber, gwl `--show-toplevel`, G7 근거 정정, README 범위. TDD: 설치 테스트 8건 중 7건 Red(sh 의 git 밖만 기존에도 통과) → 구현 → sh·ps1 ALL PASS(`ps1: ran`).
- 2026-09-26: 단위 커밋 3개(install-hooks·gwl·editorconfig) → code-reviewer(+codex high) REQUEST CHANGES — Major 1(ps1 `2>$null`+EAP=Stop 이 PS 5.1 에서 종료 오류), Minor 7, Nit 8. fix loop 1: ps1 `Invoke-Git`, hooksPath 판정을 "설정됐고 다른 디렉토리일 때만"(symlink·대소문자 거짓 거부 해소), git 2.31 확인, 테스트 격리·케이스(전역 hooksPath·기본 디렉토리·symlink·옛 git shim·`main()` symlink), `Test-Path -LiteralPath`, InvariantCulture, gwl ReferenceEquals, README rollback 경로. 설치 테스트 sh·ps1 ALL PASS(`ps1: ran`), gwl OK.
- 2026-09-26: 재확인 APPROVE(원 finding 14 해결·1 wontfix·1 deferred), 신규 Nit 6 → fix loop 2: ps1 stderr 비동기 읽기·git 실패 사유 표시(sh 도)·나머지 git 호출 종료코드 확인, prompt-gwl 의 Windows git 부재 메시지, 테스트 fixture(hooks 디렉토리 없음·shim 경로 따옴표·Windows symlink skip). sh/ps1 symlink 판정 비대칭은 wontfix.

# Next

verify → fixup 커밋 → commit-check → `/e merge`.

# Decisions

- 거부 판정을 "`--git-path hooks` ≠ `<common>/hooks` 문자열" → **"`core.hooksPath` 가 설정됐고 그 경로가 다른 디렉토리일 때"** 로 변경 (이유: code-reviewer 실측 — symlink 된 `.git/hooks`(공유 훅 관행)와 대소문자 무시 FS 의 `.git/HOOKS` 를 hooksPath 탓으로 잘못 거부했고, 옛 코드는 둘 다 설치했다. symlink 대상 디렉토리에 쓰는 것은 옛 동작 그대로다).
- ⚠️ `core.hooksPath` — 감사 제안(`--git-path hooks` 로 그 경로에 설치)과 "사용자 도구가 관리하는 디렉토리를 덮지 않는다" 가 상충 — 설치 거부를 택했다(plan-reviewer 가 유지 판정). 판정은 `--local` 조회가 아니라 유효 경로 비교(`--git-path hooks` vs `<git-common-dir>/hooks`)로 한다 — 전역·include·worktree config 를 모두 잡고, hooksPath 가 기본 디렉토리를 가리키면 거부하지 않는다. 기각: 붙여 넣을 스니펫 출력·소유자 opt-in 플래그 — 지금 hooksPath 를 쓰는 대상 repo 가 없어(2026-09-25 감사: `~/Repos` 설치 0곳) 비용 대비 이득이 작다. 한계: `extensions.worktreeConfig` 로 한 worktree 에만 hooksPath 가 있으면 다른 worktree 에서 설치가 성공해도 그 worktree 는 보호되지 않는다. `--git-path hooks` 는 hooksPath 를 그대로 돌려줘 husky(`.husky/_`) 같은 도구의 래퍼를 백업하고 덮는다. `.git/hooks` 에 쓰면 git 이 읽지 않아 "설치됨" 이 거짓이 된다. 거부하고 그 도구에 훅을 추가하라고 알리는 것이 유일하게 조용히 틀리지 않는 선택이다. linked worktree 는 hooksPath 가 없을 때 `--git-path hooks`(공용 디렉토리)로 푼다.
- ~~원격 범위 설계~~ → **`push-remote-scope` 로 분리**(사용자 결정). 아래 두 줄은 분리 전 초안으로 그 단위의 출발점이다. 원격 범위: 설정된 원격 이름이면 `--remotes=<name>`(그 원격의 추적 ref), 아니면 추적 ref 를 전혀 빼지 않는다(fail-closed — URL 로 직접 push 하면 모든 추적 ref 를 빼던 지금 동작이 비공개 원격에만 있던 커밋을 공개 URL 로 흘릴 수 있다). 대신 stdin 의 원격 sha(0 이 아니고 로컬에 있으면)는 늘 뺀다 — 대상 브랜치가 이미 가진 커밋이다. 원격 이름에 glob 문자가 있으면 `--remotes=` 가 패턴으로 해석되므로 `^[A-Za-z0-9._-]+$` 가 아니면 이름이 없는 것으로 본다.
- 인자 전달은 옛 래퍼 호환을 유지한다: 인자가 없으면 `--remotes` 전체(지금 동작). 옛 래퍼는 재설치로 바뀐다(내용이 달라 백업 후 교체).
- 백업 이름에 UTC 시각(`yyyyMMddTHHmmssZ` — `:` 는 NTFS 금지 문자)을 넣고, 이미 있으면 번호를 붙인다. 존재 확인 루프로 고른다(`mv -n` 은 덮지 않았어도 0 을 돌려줘 원본이 사라질 수 있어 쓰지 않는다). ps1 은 `Move-Item -Force` 를 뺀다.
- (분리됨) ps1 래퍼는 `-Remote "$1"` 로 이름 붙여 넘긴다 — plan-reviewer: `@"…"@` 확장형 here-string 이라 설치 시점에 빈 값이 된다(이스케이프 필요), sh heredoc 의 `"$@"` 도 같은 함정.
- gwl: ps1·py 도 zsh 판처럼 `git rev-parse --show-toplevel` 을 기준으로 하고(git 밖이면 cwd), 일치하는 경로 중 가장 긴 한 행에만 `→` — 처음엔 cwd 의 가장 긴 prefix 만 봤으나 plan-reviewer 지적대로 symlink cwd(`/tmp`→`/private/tmp`)·드라이브 문자 대소문자에서 어긋나 toplevel 로 바꿨다(git 이 `worktree list` 와 같은 형식으로 준다).
- `.editorconfig`: `[*.ps1]` 전체에 `utf-8-bom` — PS 5.1 은 BOM 없는 UTF-8 을 ANSI 로 읽으므로, 비ASCII 가 든 BOM 없는 ps1(위 재현 목록)도 다음 편집 때 BOM 이 붙어 오히려 고쳐진다. 기존 파일을 지금 변환하지는 않는다(→ audit-low-batch).
- 커밋 단위: 1) `fix(install-hooks): install into the hooks git runs and keep every backup` — `scripts/install-hooks.{sh,ps1}`·`scripts/install-hooks.test.js`·README install-hooks 부분 2) `fix(gwl): mark only the current worktree when worktrees nest` — `scripts/gwl.ps1`·`scripts/prompt-gwl.py`·`scripts/test_prompt_gwl.py`·README gwl 부분 3) `chore(editorconfig): save PowerShell scripts with a BOM` — `.editorconfig`·intent·이 plan.

# Key Files

- `scripts/install-hooks.sh`, `scripts/install-hooks.ps1` — 설치 위치·hooksPath 거부·백업
- `scripts/install-hooks.test.js` — sh·ps1 설치 테스트
- `scripts/gwl.ps1`, `scripts/prompt-gwl.py`, `scripts/test_prompt_gwl.py` — 마커
- `.editorconfig`
- `README.md` — install-hooks·gwl 절, permissions.deny, 트리
- `plans/2026-09-25-repo-audit-followups/intent.md` — `# Plans` 자기 줄 + `push-remote-scope (미착수)`

# Review Disposition

- [plan] 강 S1~S7(원격 범위: 래퍼 인자 설치 시점 확장·추적 ref≠push 대상·인자 없음 모순·공허한 기존 테스트·ps1 skip·dogfood·rsha 검증) — deferred(`push-remote-scope` 단위로 분리, 사용자 결정). 그 단위의 출발 체크리스트로 intent 줄에 요약.
- [code] Major ps1 `2>$null`+EAP=Stop(PS 5.1) — fix(`Invoke-Git`, 코드페이지 문제도 흡수). Minor 경로 동일성 거짓 거부(분쟁: Codex Major / Claude Minor) — fix(hooksPath 설정 여부 + `-ef`). Minor git 2.31 — fix(출력이 `--` 로 시작하면 거부, README). Minor 테스트 격리 — fix(`commit.gpgsign`·`GIT_CONFIG_NOSYSTEM`·`XDG_CONFIG_HOME`). Minor 테스트 누락 — fix(전역 hooksPath·기본 디렉토리·symlink·`main()` symlink). Minor `Test-Path` 비리터럴 — fix. Minor PS 5.1 코드페이지 — fix(Invoke-Git). Minor plan Next — fix.
- [code] 재확인 Nit N1 stderr 순차 읽기 교착 — fix(`ReadToEndAsync`). N2 git 실패 사유 숨김 — fix(ps1·sh 둘 다 첫 줄 표시). N3 `.Code` 미확인 — fix(`Get-GitPath`). N4 sh `-ef` / ps1 문자열 비대칭(hooksPath 가 symlink 를 거쳐 같은 디렉토리) — wontfix(트리거 사실상 없음, PS 5.1 에 이식성 있는 realpath 없음). N5 Windows 의 git 부재 메시지 — fix. N6 테스트 fixture 가정 — fix.
- [code] Nit 백업 TOCTOU(분쟁: Codex Major / Claude Nit) — wontfix(같은 초에 같은 hooks 로 설치 둘이 동시에 도는 경우뿐, 옛 코드보다 개선). Nit gwl 대소문자 — fix(ReferenceEquals). Nit culture — fix(InvariantCulture). Nit Write-Error 뒤 exit — fix(새로 쓴 두 메시지는 `Write-Host` + `exit 1`, guard 부재 메시지는 기존 그대로). Nit README rollback 경로 — fix. Nit verify.sh 가 install-hooks 의 ps1 skip 을 숨김 — defer(`# Deferred`; CI runner 에는 pwsh 가 있어 돈다). Nit 커밋 제목 차이 — fix(Decisions 를 실제 제목으로). Nit prompt-gwl 예외·주석 언어 — fix.
- [plan] 약: hooksPath 판정·쓰기 전 거부 — fix. 스니펫·opt-in — wontfix(Decisions). 백업 형식·no-clobber·`-Force` — fix. pre-commit 래퍼 불변 — fix(래퍼 무변경). G7 근거 오류 — fix. gwl 대소문자·`--show-toplevel` — fix. README 범위 — fix(원격 범위 관련 114·186·438·442 는 분리 단위로). 분할 근거·PS5.1 제약 — fix. 절차 역순(G6·G7 선구현) — Progress 기록. CLAUDE.md:134 — 고치지 않음(여전히 참).
- ⚠️ self-flag(hooksPath 설치 거부) — resolved(리뷰가 유지 판정, 판정 방식은 유효 경로 비교로 보강).

# Deferred

- (low) `scripts/verify.sh` — 테스트가 성공 출력 안에서 `ps1: skipped` 를 내도 `ALL PASS` 만 보인다(pre-commit-check.test.sh 와 install-hooks.test.js 둘 다). PATH 에 pwsh 가 없는 로컬에서는 ps1 경로가 조용히 빠진다. skip 줄을 verify.sh 의 skip 목록으로 올리는 방안.

# Blockers

없음.
