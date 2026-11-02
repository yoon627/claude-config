---
title: audit-safety-net — 승인 규칙 정본·비밀 스캔 범위·원격 삭제 가드 보강
status: done
started: 2026-11-01
updated: 2026-11-02
---

# Goal
2026-11-01 점검(보고 페이지 §2 1~4, 10)에서 나온 안전망 빈틈을 닫는다. (1) `permissions.ask` 규칙의 추적되는 정본을 만들고 bootstrap 이 머신별 `settings.json` 에 병합한다(rtk 쌍 기계 생성, 은퇴 목록, 도구 이름만 쓴 `allow` 제거는 정본에 적되 이 머신 적용은 사용자 결정). (2) `~/.claude` 의 pre-commit·pre-push·CI 비밀 스캔을 추가된 줄 기준으로 모든 파일로 넓힌다. (3) `guard-push-delete.js` 가 모든 git 조각에서 삭제·force·mirror·prune push 형태를 보고 분석 예외에서는 `ask` 로 기운다(사용자 2026-11-01 "안전망 보강" 선택 — 커밋 전 diff 확인 조건).
- Why: `settings.json` 은 2026-09-07(9ef4717)부터 머신별 untracked 인데 README 519행이 설명하는 ask 규칙·rtk 쌍은 어디에도 정본이 없다 — 이 머신은 49개·rtk 쌍 0개. 비밀 스캔은 `settings.json`(untracked)·`plans/*.md` 만 보니 공개 repo 의 README·skills·scripts 는 토큰 스캔 없이 올라간다. `bash -c "git push origin --delete x"`·`git -C r push -uf` 는 ask 규칙도 가드도 못 본다.
- Constraints: `settings.json` 은 계속 untracked(9ef4717 의 이유가 그대로). 정본은 `ask`·`retireAsk`·`forbidAllow` 만 — hooks 정본은 Out of scope. 병합은 멱등이고 다른 키·사용자가 더한 규칙을 건드리지 않으며, 바꿀 때마다 타임스탬프 백업을 남긴다. 승인·안전 규칙을 만지므로 커밋 전 사용자 diff 확인(§8 위임 예외 밖) — 그때 "느슨해지는 것 없음·바뀌는 마찰" 을 함께 보인다. 넓어진 비밀 스캔은 `claude_repo=yes`(이 repo)일 때만(다른 repo 의 lockfile·번들·대형 이력에 비용을 전가하지 않는다 — plan-reviewer S3). pre-commit 은 **추가된 줄만**(기존 fixture 가 든 파일의 무관한 편집을 막지 않게 — S2), pre-push 는 `pt_scan_pushed` 와 같은 범위(`^origin/main` 제외 — 새 브랜치 push 가 전체 이력을 훑지 않게 — S1). 새 테스트의 토큰은 실행 시 조립(머지 뒤 CI 스캔이 자기 테스트에 걸리지 않게). `scripts/pre-commit-check.test.sh`:24 의 `mktemp` 줄과 `.sh`:454·`.ps1`:558 의 "회사 repo" 는 audit-mechanical 소유. README 519행 절은 이 plan, 520행은 audit-mechanical — 인접해 rebase 충돌이 예상되니 A 머지 뒤 rebase 에서 손으로 합친다. ps1 은 이 머신에 pwsh 가 없어 CI(ubuntu pwsh 7)에서만 검증된다 — Acceptance 에 그렇게 적는다. 사용자 지시: 묻지 말고 끝까지, push 는 끝에 한 번(이 단위는 diff 확인 1회).
- Out of scope: hooks 추적 정본 · `onFailure: "block"`(fail-open 정책 변경 — Deferred) · 비밀 패턴 추가 · ps1 대소문자 구분 차이 · 다른 repo 의 스캔 범위.
- Split: none — purpose-commit bundle: 2026-11-01 점검 보고 §2(안전망) · 단위 1)~3) · 같은 출처이고 서로 다른 파일을 고친다(README 만 공통, 다른 절). 커밋 단위로 따로 되돌릴 수 있다.

# Tasks
- [x] plan-reviewer (2026-11-01) — CONDITIONAL: S1~S8·W1~W13 반영해 아래로 고침(처분은 log)
- [x] 1) 승인 규칙 정본 — 새 `scripts/permission-rules.json`: `ask`(이 머신 49개의 base 형태 + 점검이 찾은 좁은 형태: `git restore *`·`git switch -f*`·`git switch --force*`·`git switch --discard-changes*`·`git switch -C*`·`git checkout -B*`·`git checkout --force*`·`git branch -f*`·`git branch --force*`·`git branch -M*`·`git branch --delete --force*`·`git branch -df*`·`git branch -fd*`·`git push --mirror*`·`git push * --mirror*`·`git push --prune*`·`git push * --prune*`·`gh pr close * -d*`·`gh pr close * --delete-branch*`·`gh pr close --delete-branch*`·`gh pr merge -d*`·`gh api --method=DELETE*`·`gh api * --method=DELETE*`·`gh release delete*`·`gh issue delete*`·`gh repo edit*` — 합친 짧은 플래그 `-uf` 류는 규칙이 아니라 가드(3)가 본다, W1), `retireAsk`(지금은 README 454행의 옛 `git push * :*` 형태), `forbidAllow`(`Bash`·`Edit`·`Write`·`NotebookEdit`·`Bash(*)` — `WebFetch`·`WebSearch` 는 두지 않음, Decisions) + 새 `scripts/sync-permissions.js`(정본을 읽어 대상 settings.json 에 ask 와 `Bash(rtk …)` 쌍을 더하고 retireAsk 와 그 쌍을 빼고 forbidAllow 를 `allow` 에서 지운다; 다른 키·모르는 규칙 유지; 멱등; 파일 없음 → `{permissions:{ask:[…]}}` 생성, JSON 오류 → exit 2 쓰기 없음, `permissions`/`ask` 없음 → 빈 것으로; 쓰기 직전 다시 읽고 symlink 는 제자리에 쓴다; 바꾸면 `<path>.bak-<YYYYMMDDTHHMMSS>` 저장; `--check` 는 drift 시 exit 1 + 정본에 없는 로컬 규칙 목록(info); `--dry-run`; `--settings <path>`) + `scripts/sync-permissions.test.js`(Red 먼저: 빈 파일·누락 규칙 추가·멱등·forbidAllow 제거·retireAsk 제거·사용자 규칙 보존·rtk 쌍 수 = base 수·`rtk rtk` 없음·`:*` 규칙 없음·JSON 오류 exit 2·백업 생성) · `scripts/bootstrap/setup.sh`·`setup.ps1` 에 rtk 단계(5) 앞 "permissions" 단계(`node scripts/sync-permissions.js`, dry-run 존중, `node` 없으면 warn 하고 계속 — W4) · README 519행 절(정본·병합·rtk 쌍·retire), 423행대 bootstrap 단계, 454행 옛 규칙 안내 → retireAsk, `scripts/bootstrap/README.md`:90 (2026-11-01)
- [x] 2) 비밀 스캔 — `scripts/pre-commit-check.sh`·`.ps1`: `claude_repo=yes` 일 때 (a) pre-commit: `pt_scan_staged` 가 읽는 추가된 줄(모든 staged 경로, `-z`·`core.quotePath=false`, `--text`)에 토큰 패턴도 적용, 결과는 "패턴 이름 + 경로:줄"(`pt_patch_records` 형식 재사용) (b) pre-push: `pt_scan_pushed` 의 범위·레코드에 토큰 패턴도 적용. 기존 `settings.json`(키+토큰)·`plans/*.md` 경로는 범위 가드 밖(claude_repo 아닌 repo)에서도 그대로. 샘플 출력(110~112·.ps1 184~186)은 앞글자를 찍지 않는다 — `ci-secret-scan.sh`:40 의 sed 를 새 형식에 맞추고 양성 테스트로 고정 · 테스트: `pre-commit-check.test.sh` 에 README·skills 파일의 추가 줄 토큰 → block(sh·ps1 `both`), 기존 fixture 파일의 무관한 한 줄 편집 → allow, 토큰이 기존 줄에만 있는 파일 → allow, 새 브랜치(remote sha 0) push 가 `^origin/main` 밖 커밋만 본다, 출력에 토큰 앞글자 없음 — 토큰은 실행 시 조립; `ci-secret-scan.test.sh` 케이스 1 · README 124·128행 (2026-11-01)
- [x] 3) `scripts/guard-push-delete.js` — 모든 git 조각(`-c`/`eval` 문자열 포함)에서 `push` 의 `--delete`·`-d`·`--force*`(`--force-with-lease` 포함)·`-f`·합친 짧은 플래그(`-uf`·`-fu`·`-df` — `-o<값>` 제외, `-o`/`--push-option`/`--repo`/`--receive-pack`/`--exec` 의 값과 `--` 뒤 refspec 은 플래그로 보지 않음)·`--mirror`·`--prune`·`+refspec`·`:ref` → `ask`(사유에 형태 명시); 명령이 문자열인데 분석이 예외를 내면 `ask`(통과 아님 — 가드 7행의 "확신 없으면 ask") · `scripts/guard-push-delete.test.js` Red 먼저: `bash -c "git push origin --delete feat"`·`git -C /r push -uf origin x`·`env git push -f origin main`·`git push --mirror` 가 지금은 allow → ask; `git push -o ci.skip origin x`·`git push origin -- +feat`(refspec 은 유지 — `+` 는 ask 가 맞다, 둘 구분) · README 450~454행 (2026-11-01)
- [x] code-reviewer(완화 여부 명시 요청) → simplify 점검 → `bash scripts/verify.sh changed` + 새 가드를 실제 push 두 모양에 미리 통과시키기(Acceptance 5) (2026-11-01)
- [x] 사용자 diff 확인(승인·안전 규칙) → 단위별 커밋 3개 (2026-11-02)
- [x] audit-mechanical 머지 뒤 rebase(README 519/520 손으로 합침) → 기록 커밋 → ff-merge(push 는 세 단위 끝에 한 번) (2026-11-02)
- [ ] [post-merge] main 에서 이 머신 적용 — `node scripts/sync-permissions.js --dry-run` 결과(ask 추가분·bare allow 제거)를 2026-10-08 결정([[claude-code-permission-prompt-sources]])과 함께 보이고 사용자가 고르면 실행(머신별 파일 — 커밋 아님) · 공용 wiki 그 페이지에 결과 기록

# Acceptance
1. `node scripts/sync-permissions.test.js` 통과(Red 기록) — 멱등(두 번째 실행 변경 0), 쌍 수 = base 수, `rtk rtk` 0, `:*` 규칙 0, JSON 오류 exit 2·쓰기 없음, 백업 파일 생성
2. 이 머신 `node scripts/sync-permissions.js --check --settings ~/.claude/settings.json` 이 exit 1 과 함께 추가될 규칙·제거될 allow 를 나열한다(적용은 [post-merge])
3. `bash scripts/pre-commit-check.test.sh` 통과(sh 엔진; ps1 은 CI) — 새 케이스 포함; `bash scripts/ci-secret-scan.test.sh` 통과
4. `node scripts/guard-push-delete.test.js` 통과(Red 기록) — Task 3 의 입력 7개
5. 새 가드가 실제 push 두 모양을 통과한다: (a) 이 worktree HEAD 를 remote sha = `origin/main` 으로 pre-push 실행 → rc 0 (b) remote sha 0(새 브랜치)으로 → rc 0 — `printf '<ref> <head> <ref> <sha>\n' | bash scripts/pre-commit-check.sh pre-push`
6. `bash scripts/verify.sh changed` 가 `ALL PASS`(skip 은 pwsh·shellcheck 부재만); README 4절(124·128·423·450~454·519)·`scripts/bootstrap/README.md` 동기화
7. 사용자가 diff 를 확인했다(AskUserQuestion 기록)

# Decisions
- wiki 결정 [[risk-based-approval]]·[[rtk-rewrite-permission-rules]](rtk 쌍)·[[claude-code-permission-prompt-sources]](2026-10-08 bare allow 추가) → 따른다/뒤집는다: bare allow 는 정본의 `forbidAllow` 에 적지만 **이 머신 적용은 사용자 결정으로 미룬다** — 2026-10-08 에 remote-control 세션이 default 모드로 시작해 호출마다 `can_use_tool` 을 띄워 추가한 것이고, 이 머신이 그 구성이다. 다만 이 세션(auto 모드)에서 auto 분류기가 Bash 명령을 거부한 사실(2026-11-01 Self-Modification 거부)은 **auto 모드에서는 bare `Bash` allow 가 사전 승인으로 작동하지 않음**을 보여준다(✅관측) — 제거해도 auto 에서는 변화가 없고 default 폴백에서만 마찰이 돈다.
- `WebFetch`·`WebSearch` 는 forbidAllow 에 넣지 않는다 — 읽기 도구이고 매 호출 확인은 조사 흐름을 막는다. 수용 위험: URL 로 정보가 나갈 수 있음(§1) — diff 확인 때 명시.
- 정본은 JSON 한 파일 + node 병합 — settings.json 재추적(9ef4717 세 번 실패)·템플릿 복사(머신별 값 덮음) 기각. `retireAsk` 로 정본 규칙을 은퇴시킬 수 있게 한다(README 454행이 손으로 지우라던 옛 규칙이 첫 항목).
- 규칙은 좁게, 정밀 판정은 가드에 — ask 규칙은 전역이고 repo 별로 풀 수 없어 `git push -*f*` 같은 넓은 glob 은 `-u origin feat/x` 까지 묻게 된다(W1).
- 비밀 스캔 범위: `claude_repo=yes` 전용 · 추가된 줄만 · pre-push 는 `^origin/main` 제외 — plan-reviewer 가 재현한 두 차단(새 브랜치 push 전체 이력 10초·6패턴, fixture 파일 무관 편집 차단)을 피한다. 기각: 전체 파일·전 이력(그 둘을 막는다), 모든 repo(비용 전가).
- 바이너리: `--text` 로 commit·push 둘 다 스캔(지금 pre-push 와 같음 — `.gitattributes` 로 숨길 수 없게). 기각: numstat `-` 제외(commit 과 push 가 갈린다).
- 가드 예외 시 `ask` — 가드의 원칙("확신 없으면 ask"). hook `ask` 와 규칙 `ask` 가 겹칠 때 프롬프트가 한 번인지 두 번인지는 ❌모름 — 적용 뒤 관찰, Deferred.
- `onFailure: "block"` 은 넣지 않는다(Deferred, 사용자 결정).
- ⚠️ (구현) CI 의 `ci-secret-scan.sh` 는 `PRE_COMMIT_CHECK_CLAUDE_REPO=1` 로 가드를 불러 넓힌 스캔을 강제한다 — CI checkout 은 `~/.claude` 아래가 아니라 `claude_repo` 판정이 no 가 되어 백스톱이 좁은 스캔만 하게 된다; 다른 선택지는 CI 에서 좁은 스캔 유지(그러면 넓힌 스캔의 서버측 백스톱이 없다) — `scripts/ci-secret-scan.sh`·`pre-commit-check.sh` env override
- ⚠️ (구현) `private_rev_input`/`Get-PrivateRevInput` 은 CI 전용 env `PRE_COMMIT_CHECK_KEEP_BASE=1`(ci-secret-scan.sh 만 설정)이 있고 remote sha 가 하나라도 있을 때만 `^origin/main` 제외를 건너뛴다 — CI 의 main push 는 origin/main == HEAD 라 범위가 비어 아무것도 스캔하지 않게 되기 때문. 로컬 push 는 HEAD 와 같다(새 브랜치·multi-ref·`-f main:feat` 모두 제외 유지 — S1). 기각: "origin/main 이 push 되는 커밋이고 remote sha 가 있으면" 조건(code-reviewer 재현 — 로컬 multi-ref push 가 이미 게시된 이력을 스캔) — `scripts/pre-commit-check.sh` `private_rev_input`
- ⚠️ (구현) bootstrap 은 sync 를 `--keep-allow` 로 부른다 — forbidAllow 제거는 머신별 사용자 결정(S4)이라 무인 bootstrap 이 지우면 안 된다; `--check`(플래그 없음)는 allow drift 를 계속 보고하고 `--check --keep-allow` 는 무시한다 — `scripts/sync-permissions.js`·`scripts/bootstrap/setup.*`
- ⚠️ (구현) 토큰 스캔은 pre-push 의 커밋 메시지(M 레코드)도 본다 — 출력 `token pattern (<name>): message <sha7>`; 신원(I 레코드)은 보지 않는다 — `scripts/pre-commit-check.sh` `tok_message_records`
- ⚠️ (구현) 가드는 `--delete`·`--mirror`·`--prune`·`--force` 의 접두(대시 포함 3자 이상)를 그 옵션으로 본다 — git 이 유일 접두를 받아 `--dele` 가 실제로 지운다(code-reviewer 재현); 모호한 접두는 git 이 거부하니 묻는 비용이 없다 — `scripts/guard-push-delete.js` `RISKY_LONG`
- 커밋 단위: 1) `feat(permissions): track a canonical ask-rule list and sync it into settings` 2) `fix(pre-commit): scan every added line of this repo for tokens` 3) `fix(guard): ask on delete, force, mirror and prune pushes in any segment`
- 롤백: 단위별 `git revert`. 머신 settings.json 은 sync 가 남긴 `.bak` 또는 `retireAsk` 로.

# Blockers
