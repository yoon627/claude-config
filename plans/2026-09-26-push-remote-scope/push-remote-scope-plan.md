---
title: push-remote-scope — pre-push 가드가 추적 ref 대신 push 대상 ref 의 실제 값으로 "이미 공개됨"을 판단
status: done
started: 2026-09-26
updated: 2026-09-26
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

pre-push 비밀 가드(`scripts/pre-commit-check.{sh,ps1}`)가 스캔에서 빼는 커밋을 "모든 remote-tracking ref 에 있는 것"에서 "push 대상 ref 가 지금 가진 것(stdin 의 remote sha)"으로 바꾼다. private 원격에서 받은 커밋을 public 원격으로 push 할 때 다시 보지 않던 G2 accepted-risk 를 푼다. 가드가 추적 ref 에 기대지 않게 되므로 CI 백스톱(`scripts/ci-secret-scan.sh`)의 임시 bare repo 를 없앤다.

# Intent

- 링크: `plans/2026-09-25-repo-audit-followups/intent.md` 의 `push-remote-scope` 단위. 출발 체크리스트는 `plans/2026-09-25-repo-audit-g5-g7-install/repo-audit-g5-g7-install-plan.md` `# Decisions`·`# Review Disposition`(강 S1~S7).
- 사용자 결정(2026-09-26): "push 대상 ref 값 기준". 대안 "원격 이름 기준(원래 초안)"·"하지 않음(wontfix)" 은 기각(아래 Decisions).
- 규모: medium(가드 sh·ps1, 테스트 2개, CI 스크립트, README·wiki 문서, 목적 1).
- 분할: 없음 — CI 단순화는 가드 변경에 의존한다(가드가 추적 ref 를 무시해야 임시 repo 가 필요 없어진다). 가드만 되돌리면 `ci-secret-scan.test.sh` 의 "추적 ref 에 이미 있는 PR 커밋 차단" 이 CI 를 빨갛게 만들고, CI 만 되돌리면 죽은 장치가 돌아온다 — 둘은 한 목적(추적 ref 의존 제거)이다.
- 델타(묶음 공통 제약 외): 가드는 보안 경계라 fail-closed 방향만 허용 — 판단할 수 없으면 더 넓게 스캔한다. 설치된 래퍼(`exec … pre-commit-check.sh "pre-push"`, 인자 없음)와 CI 호출 형태는 그대로 동작해야 한다(재설치 없음). ps1 은 PS 5.1 에서도 돈다 — PS7 전용 구문 금지, pwsh 7 로 검증하고 PS 5.1 은 미검증으로 남긴다.
- Out of scope: 가드 패턴 목록, push 커밋을 명령줄 대신 `--stdin` 으로 넘기기(Windows 32k 한계 — repo-audit-remaining `# Deferred`), 래퍼 내용 변경.

사실 확인(2026-09-26, git 2.54, scratch 실측):
- ✅ pre-push stdin 의 remote sha 는 원격이 알려 준 **실제 현재 값**이다. 추적 ref 를 옛 커밋으로 돌려 놓아도 원격 값(`3ec0eb9`)이 왔고, URL 로 직접 push 해도 같다. 새 ref 는 all-zero.
- ✅ pushurl 이 두 개면 훅이 URL 마다 따로 불리고 remote sha 도 URL 별 값이다(a.git=c1, b.git=zero). 옛 가드는 b.git 쪽에서도 `origin/*` 을 빼 fail-open 이었다.
- 가드가 설치된 repo: 이 머신은 `~/.claude` 하나(원격 `origin` 하나, pushurl 없음). Windows 머신은 여기서 확인 불가(❌).
- `~/.claude` 이력 전체 스캔: sh 1.21s·ps1 0.46s, clean(repo-audit-remaining dogfood). HEAD 505 커밋, `plans/*.md` 전체 이력 patch 2.5MB(plan-reviewer 측정) — 선형으로 자란다.
- `rev-parse --verify --quiet <blob>^{commit}` 는 rc 1 이면서 stderr 에 `error: … expected commit type` 를 찍는다. 로컬에 없는 sha 는 조용하다(plan-reviewer 실측).

# Acceptance

1. 가드(sh·ps1)의 스캔 범위는 `Reach(유효한 local sha) − Reach(로컬 커밋으로 풀리는 remote sha, 삭제 줄 포함)` 이고 remote-tracking ref 는 빼지 않는다. 검증: `bash scripts/pre-commit-check.test.sh`(sh·ps1), 케이스 —
   - (A) 토큰 커밋이 다른 브랜치의 추적 ref(`origin/other`)에만 있고 새 브랜치 push(remote sha zero) → 차단
   - (B) 토큰 커밋이 대상 ref 의 remote sha, 추적 ref 없음 → 허용(기존 149행 케이스에서 추적 ref 설정을 뺀 것)
   - (C) 재작성 뒤 오래된 추적 ref: 대상 추적 ref = 옛 토큰 커밋 T, remote sha = 재작성된 깨끗한 C′(T 의 자손이 아님), 로컬 브랜치는 T 위 → 차단
   - (D) remote sha 가 로컬에 없는 40자 sha → 제외 없이 스캔: 토큰 있으면 차단, 깨끗하면 출력 없이 허용
   - (E) sha 형식 오류 → malformed 로 차단: 16진수 아님, 짧은 16진수(`beef` — remote·local 모두), sha1 repo 의 64자 sha, 삭제 줄의 형식 오류(zero 건너뛰기보다 먼저 검증). sha256 repo 는 64자로 차단·허용 모두 동작
   - (F) remote sha 가 blob·tree(태그 ref) → 제외만 건너뛰고 출력 없이 허용(`error:` 줄 없음)
   - (G) remote sha 가 commit 을 가리키는 annotated tag(태그 재지정 push) → peel 해서 제외 → 허용
   - (H) 삭제 줄 `(delete) ZERO refs/heads/old T` + 새 브랜치 `feat`(T 의 자손, remote sha zero) → 허용, 줄 순서를 바꿔도 허용
   - (I) update 줄(remote sha=M, 토큰 커밋) + 새 브랜치 줄(M 의 자손) → 합집합으로 M 제외 → 허용
   - (J) replace: remote sha 인 태그 A 를 로컬에서 `git replace` 로 토큰 커밋을 가리키는 태그로 바꿔도 → 차단(replace 무시)
   - (K) 기존 rename 케이스(174행)는 추적 ref 설정을 빼고 remote sha 만으로 차단 유지
   - (L) pre-commit: staged blob 을 `git replace` 로 깨끗한 blob 으로 바꿔도 차단
   Red(옛 가드에서 실패, sh 기준 14): A·B·C·E(비16진수·짧은 remote·짧은 local·64자·삭제 줄)·G·H 두 가지·I·sha256 허용·L. D·F·J·K·sha256 차단은 회귀 잠금.
2. ps1 이 실제로 돈 증거: 출력 `ps1: ran N`(N = sh 케이스 수), `PWSH` 경로. ps1 diff 에 PS7 전용 구문(`??`·`?.`·삼항·파이프라인 체인 `&&`/`||`·`-Parallel`)이 없음을 정적 점검.
3. CI 스크립트는 임시 bare repo 없이 checkout 에서 가드를 부르고 base 를 stdin 의 remote sha 로 넘긴다. shallow checkout 이면 스캔하지 않고 실패한다. 검증: `bash scripts/ci-secret-scan.test.sh` — 기존 케이스(추적 ref 에 이미 있는 PR 커밋 차단, 로그 마스킹, zero·빈·없는 base 는 전체 이력, PR head vs merge) 통과, "checkout ref 불변" 은 쓰기 코드가 없어져 삭제, shallow clone 케이스 추가. PR 의 CI Secret scan step 로그에 `ci-secret-scan: <base>..<head>` 범위가 찍힌다.
4. 실제 `git push` E2E(scratch — 영구 테스트로 올리지 않는다): 가짜 HOME 의 `.claude/scripts` 를 이 worktree `scripts/` 로 링크하고 `install-hooks.sh` 로 래퍼를 설치한 fixture repo(브랜치 `feat`) + bare 원격 — 토큰 브랜치 push 차단, 원격이 이미 가진 토큰 커밋 위 push 허용, 오래된 추적 ref(C) 상태의 push 차단, pushurl 두 개 중 토큰 커밋이 없는 쪽에서 차단. dogfood: 이 worktree HEAD 를 새 브랜치로 push 하는 입력(remote sha zero)으로 sh·ps1 가드 실행 — 허용, 시간 기록.
5. 문서: 가드 머리 주석·`added_lines` 주석, `scripts/ci-secret-scan.{sh,test.sh}` 주석, README 114·186(가드 설명)·433(CI 절)·438(예외: 풀리지 않는 remote sha 는 차단이 아니라 제외 생략, 알려진 한계 교체)·442(커버리지 수)·595(유출 대응 4단계 — 옛 이력에서 딴 브랜치의 push 를 가드가 막음), 패턴을 바꿀 때 전체 이력 확인 필요, wiki `ci-secret-scan-backstop`(임시 repo 결정 대체)·`git-log-added-lines-hardening`(:35 실패 시 차단의 예외)·`wiki/index.md`·`wiki/log.md`, intent 의 Open question 처분.
6. 전체: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음), plan-lint 통과.

# Progress

- 2026-09-26: 착수. 설치 현황·remote sha 의미 실측, 사용자 설계 결정.
- 2026-09-26: plan-reviewer(+codex) CONDITIONAL — 강 3(테스트 설계·E2E 가 옛 가드를 부름·tag peel 이 replace 를 따름)·약 10. 전부 반영(아래 Review Disposition). pushurl 두 개 실측으로 S2 해소 확인.
- 2026-09-26: TDD — 옛 가드에서 엔진당 10건 Red(A·B·C·E×3·G·H×2·I, 예측과 일치) → 구현 → sh 59 + ps1 59 = 118/118. CI 테스트 9/9(ref 불변 삭제, shallow 추가). 실제 push E2E(scratch, 가짜 HOME → worktree 가드) 4/4, 같은 시나리오를 main 의 옛 가드로 돌리면 재작성 뒤 오래된 ref·pushurl 두 개에서 토큰이 원격에 올라감(2/4). dogfood: 이 repo 505 커밋 전체 재스캔 허용, sh 0.75s·ps1 0.47s. ps1 추가 줄에 PS7 전용 구문 없음. README·wiki·intent 동기화. local sha 도 전체 길이만 받도록 함께 좁힘(Decisions).
- 2026-09-26: code-reviewer APPROVE(Critical·Major 0, Minor 5·Nit 6, refuted 11). Codex 는 high effort 로 호출했으나 "workspace out of credits" 로 finding 0 — 세션 마커 `codex-unavailable` 작성됨. fix loop 1: sha 길이를 repo 해시 형식에 묶음, 테스트 4건 추가(pre-commit replace·짧은 local sha·sha1 repo 의 64자 sha·sha256 repo 2건 — 옛 가드에서 새 4건 모두 Red, 전체 14 Red), CI shallow 판정 실패 메시지·zero 폴백 길이, 주석·README 중복. 128/128(sh 64 + ps1 64), CI 9/9, shellcheck ok. E2E 3번을 (C) 형태(`push --force origin feat`, remote sha = 재작성된 값)로 고쳐 새 가드 4/4·옛 가드 2/4. simplify 체크: 변경 없음(아래 Disposition).
- 2026-09-26: 최종 검증(격리 runner, 명령 7개 모두 exit 0) — 가드 테스트 128/0·`ps1: ran 64`, CI 9/0, `verify.sh` 마지막 줄 `ALL PASS`(skip 없음), plan-lint 0, wiki link clean, E2E 4/0, dogfood 505 커밋 sh 0.79s·ps1 0.51s 허용. runner 대조에 어긋난 항목 없음. evidence gate: Acceptance 1·2·4·5·6 충족, 3 은 PR CI 로그 범위 확인만 남음(push 뒤에만 관찰 가능). 판정 DONE(통합 대기).
- 2026-09-26: 커밋 `4b432d9`, 사용자 선택 `/e merge` → PR #178. Acceptance 3 의 PR CI 로그 범위는 머지 보고에 기록.

# Next

(없음 — PR #178 머지로 종료. 머지 후 Windows 에서의 첫 push 가 PS 5.1 실검증 — 사용자 관찰)

# Decisions

- 제외 기준은 stdin 의 remote sha(push 대상 ref 의 현재 값)만. 이유: 원격이 알려 준 값이라 pushurl(URL 마다 따로 옴)·URL push·재작성 뒤 오래된 추적 ref 에 영향받지 않고, 원격 이름이 필요 없어 설치된 래퍼를 바꾸지 않는다(S1 설치 시점 확장·S3 인자 호환·S6 혼합 상태가 사라진다).
- 불변식: 스캔 = `Reach(유효 lsha) − Reach(풀리는 rsha, 삭제 줄 포함)`. git 이 보내는 것 = `Reach(push) − Reach(원격이 광고한 모든 ref)` 이고 rsha 는 광고된 ref 의 부분집합이므로 **스캔 ⊇ 전송**이다. 삭제 줄의 rsha 도 광고된 값이라 넣어도 이 방향을 지킨다(처음 ⚠️ 로 적었던 삭제 줄 결정은 이것으로 해소).
- ⚠️ 새 브랜치 push 는 base 이력 전체를 다시 스캔한다 — 속도·"이미 공개된 토큰 재차단" 과 상충 — 정확성을 택했다(사용자 결정). `~/.claude` 는 이력 전체가 clean 이고 약 1초. 원격 이력에 토큰이 남은 repo 는 재작성 전까지 새 브랜치 push 가 막힌다(README 유출 대응 절이 재작성을 요구하므로 같은 방향). 결과: 앞으로 가드 패턴을 추가·완화할 때는 과거 이력 전체에 매치가 없는지 먼저 확인해야 한다(README 에 적는다).
- sha 길이는 40/64 둘 다가 아니라 ~~전체 길이(40 또는 64)~~ → **repo 해시 길이**(`rev-parse --show-object-format` — sha1 40·sha256 64, 판정 실패 시 40)로 변경 (이유: code-reviewer 재현 — sha1 repo 에 64자 16진수가 오면 같은 이름의 ref 로 풀려 토큰 커밋이 제외됐다. 실제 push 로는 도달하지 않지만 주석이 막겠다는 경로 그대로다). CI 의 zero 폴백도 같은 길이로 만든다.
- local sha 도 같은 전체 길이 규칙으로 좁힌다(전에는 16진수 4자 이상). 이유: 같은 검증 줄이고, 짧은 이름이 ref 로 풀리는 문제는 스캔 대상 쪽에서도 같다. git 이 넘기는 값은 늘 전체 길이라 실사용 영향은 없다.
- remote sha 는 전체 길이(40 또는 64자 16진수)만 받고, 아니면 malformed 로 차단한다(S7 — 짧은 16진수는 rev-parse 가 같은 이름의 ref 로 풀 수 있다). 검증은 local sha zero 건너뛰기보다 먼저 해서 삭제 줄도 검증한다. 로컬에서 `^{commit}` 으로 풀리지 않으면(원격만 가진 커밋·blob·tree) 제외하지 않는다 — 더 넓게 스캔하는 쪽. 이 해석에서만 stderr 를 버린다(blob peel 이 `--quiet` 에도 `error:` 를 찍는다) — 스캔 실패를 숨기는 것이 아니라 "제외할 수 없음" 이라는 정상 분기라서.
- replace 는 스크립트 전체에서 끈다(`GIT_NO_REPLACE_OBJECTS=1`). 이유: 태그 객체의 `^{commit}` peel 이 replace 를 따라 원격에 없는 커밋을 제외 목록에 넣을 수 있다(Codex). 기존 lsha 의 태그 peel(`sh:150`·`ps1:166`)과 pre-commit 의 `git show :<path>` 도 같은 원인이라 한 줄로 함께 닫힌다.
- CI 스크립트는 임시 repo 를 없애고 checkout 에서 가드를 부른다. 이유: 임시 repo 는 가드의 `--not --remotes` 가 checkout 의 추적 ref 때문에 아무것도 스캔하지 않던 것을 피하려는 장치였다. 대신 shallow checkout 이면 실패한다 — 임시 repo 는 shallow 목록을 물려받지 않아 부모 누락이 `git log failed` 로 차단됐지만, 직접 호출은 shallow 경계를 root 로 보고 조용히 좁게 스캔한다(지금은 `fetch-depth: 0` 이 지킨다).
- Rollback: 커밋 1개 revert. 새 가드가 크래시하거나(특히 Windows PS 5.1) 과거 이력 매치로 새 브랜치 push 를 모두 막으면 revert 의 push 도 같은 가드를 탄다 — 탈출구는 `git push --no-verify` 또는 `.git/hooks/pre-push` 제거(README:127). 가장 비싼 단계는 main 머지다(SessionStart pull 로 두 머신의 모든 push 에 즉시 적용).
- 기각: 원격 이름 기준(원래 초안) — 래퍼 변경·두 머신 재설치·추적 ref 신뢰 조건(pushurl·url 여러 개·이름 접두 충돌·refspec) 판정이 필요하고, 재작성 뒤 오래된 추적 ref 문제는 남는다.
- 기각: 하지 않음 — 지금 이 머신에는 위험 경로가 없지만 Windows 머신은 확인할 수 없고, 재작성 뒤 오래된 추적 ref·pushurl 여러 개 경로는 단일 원격에서도 생긴다.
- 기각: 훅 안에서 `git ls-remote` 로 원격의 모든 ref 를 받아 제외 — 훅 안 네트워크·인증 프롬프트·hang 위험([[git-hook-network-safety]] 류), 느림.
- 기각: remote sha + `--remotes` 유지 — 추적 ref 신뢰 문제로 되돌아간다.
- 기각: 회수한 토큰 매치값의 지문 허용 목록 — 우회 장치를 가드에 넣는 것이라 필요가 생기면(회수했지만 재작성하지 않은 토큰이 새 브랜치 push 를 막을 때) 따로 검토.
- 커밋 단위: 1개 — `fix(pre-push): judge "already published" by the destination ref, not tracking refs`. 근거: 부분 revert 방지(위 분할 판단). 가드만 되돌리면 CI 가 빨개지고(조용히 무력화되지는 않는다 — 처음 적은 근거를 plan-reviewer 가 정정), CI 만 되돌리면 죽은 장치가 돌아온다.

# Key Files

- `scripts/pre-commit-check.sh`, `scripts/pre-commit-check.ps1` — 제외 기준·remote sha 검증·replace 끄기.
- `scripts/pre-commit-check.test.sh` — 케이스 A~K, `clean` 기대값(출력 없음).
- `scripts/ci-secret-scan.sh`, `scripts/ci-secret-scan.test.sh` — 임시 repo 제거, shallow 거부.
- `README.md` — 가드·CI·유출 대응 서술, 커버리지 수.
- `wiki/pages/decision/ci-secret-scan-backstop.md`, `wiki/pages/entity/git-log-added-lines-hardening.md`, `wiki/index.md`, `wiki/log.md`.
- `plans/2026-09-25-repo-audit-followups/intent.md` — 이 단위 줄·Open question.

# Review Disposition

- [plan] 강1 테스트 설계(Red 계산 오류·허용 짝 없음·합집합·삭제 줄 무검증) — fix(Acceptance 1 케이스 A~K, `clean` 기대값).
- [plan] 강2 E2E 가 main checkout 의 옛 가드를 부름(`install-hooks.sh:34,76`) — fix(가짜 HOME → worktree `scripts/`, scratch 로 둠).
- [plan] 강3 tag peel 이 replace 를 따름(Codex) — fix(`GIT_NO_REPLACE_OBJECTS=1` 스크립트 전체, 케이스 J).
- [plan] 약1 blob peel stderr — fix(해석에서만 stderr 버림, 케이스 F 출력 없음).
- [plan] 약2 짧은 16진수·검증 순서 — fix(40/64자, zero 건너뛰기보다 먼저).
- [plan] 약3 가장 비싼 단계·PS 5.1 — fix(Decisions Rollback, Acceptance 2 정적 점검, 머지 후 Windows 첫 push 확인).
- [plan] 약4 전체 이력 재스캔의 운영 결과 — fix(Decisions ⚠️ 줄, README). 지문 허용 목록 — 기각(Decisions). partial clone lazy fetch — 기록만(해당 repo 없음).
- [plan] 약5 CI shallow·공허한 "ref 불변"·PR 로그 확인 — fix(Acceptance 3).
- [plan] 약6 분할 근거 사실 오류 — fix(Intent 분할 줄·커밋 단위 근거 정정).
- [plan] 약7 문서 범위(README:438·442·595, wiki hardening) — fix(Acceptance 5).
- [plan] 약8 기각안 누락(ls-remote, rsha+`--remotes`) — fix(Decisions).
- [plan] 약9 ps1 세부(`$script:` 범위, 32k) — fix(구현 시), 32k 는 Deferred 에 한 줄.
- [plan] 약10 local-ref 에 공백(`HEAD@{1 day ago}`) 파싱 — defer(기존 결함, `# Deferred`).
- [plan] ⚠️ pushurl 여러 개 — 메인 실측으로 해소(Intent 사실 확인).
- [code] Minor1 짧은 local sha 테스트 없음 — fix(케이스 추가, 옛 가드 Red). Minor2 sha256 경로 테스트 없음 — fix(sha256 repo 차단·허용). Minor3 sha 길이가 object format 과 무관 — fix(repo 해시 길이, sha1 repo 의 64자 케이스). Minor4 pre-commit replace 테스트 없음 — fix(케이스 추가, 옛 가드 Red).
- [code] Minor5 partial clone 에서 remote sha peel 이 lazy fetch — defer. 이유: 그 peel 에 `GIT_NO_LAZY_FETCH=1` 을 주면 제외가 사라져 뒤따르는 `git log` 가 전체 이력의 blob 을 lazy fetch 하게 되어 네트워크가 오히려 늘 수 있다. 가드가 설치된 partial clone 은 없다(`# Deferred`).
- [code] Nit6 중복 `--no-replace-objects` — wontfix. 이유: `git log` 명령줄은 wiki hardening 표에 한 덩어리로 문서화되어 있고, 스크립트 머리의 env 줄이 옮겨져도 그 명령만으로 막히게 둔다.
- [code] Nit7 shallow 판정 실패도 "shallow" 로 안내 — fix. Nit8 주석 "local objects" — fix. Nit9 README 중복 문장 — fix. Nit10 줄마다 rev-parse — defer(측정 없음, `# Deferred`). Nit11 E2E 3번 형태 — fix((C) 형태로 재실행).
- [code] Codex 미가용 — high effort 호출이 크레딧 소진으로 finding 0. Claude code-reviewer 결과만으로 처분했다(§9 생략 사유).
- [simplify] 변경 없음 — 중복 후보는 Nit6(유지 사유 위), 두 엔진의 긴 주석은 보안 경계의 근거라 유지.

# Blockers

# Deferred

- (낮음) 가드가 ref 줄을 공백으로 4필드 분리해 `<local ref>` 에 공백이 있으면(`git push origin 'HEAD@{1 day ago}':x` — githooks(5) 는 입력 그대로 전달) malformed 로 잘못 차단한다. ref 이름에는 공백이 없으므로 오른쪽 세 필드부터 파싱하면 된다. `scripts/pre-commit-check.{sh,ps1}`.
- (낮음) partial clone(`--filter=blob:none`)에서 로컬에 없는 remote sha 를 peel 하면 promisor 원격으로 lazy fetch 가 일어난다(훅 안 네트워크, stderr 를 버려 보이지 않음 — code-reviewer 실측). 막으면 제외가 사라져 `git log` 가 더 많은 blob 을 가져올 수 있어 보류. 가드가 설치된 partial clone 이 생기면 다시 본다.
- (낮음) ref 줄마다 remote sha peel 에 `rev-parse` 가 하나씩 뜬다 — 많은 ref 를 push 할 때 Windows 프로세스 생성 비용. `cat-file --batch-check` 로 한 번에 푸는 안(측정 없음).
- (낮음) push 커밋과 제외 sha 를 한 명령줄로 넘겨 Windows 32k 한계에 닿는다(repo-audit-remaining Deferred 의 `--stdin` 항목) — 제외 sha 가 더해져 `--mirror` 류에서 더 빨리 닿는다.
