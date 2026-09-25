---
title: repo-audit-g8-g9-docs-ci — README 유출 대응 절, CLAUDE_REVIEW_CODEX_MODE 폐기, CI 비밀 스캔 백스톱
status: in_progress
started: 2026-09-26
updated: 2026-09-26
intent: plans/2026-09-25-repo-audit-followups/intent.md
---

# Goal

README 의 secret 유출 대응 절을 실제로 동작하는 절차(GitHub 공식 절차, 실측 검증)로 고치고, 쓰이지 않는 `CLAUDE_REVIEW_CODEX_MODE=external` 개념을 프롬프트 문구 하나로 통일한다. CI 가 main 을 향한 PR 과 main push 범위를 pre-push 가드로 다시 스캔해, 로컬 훅이 없거나 `--no-verify` 로 건너뛴 push 를 **사후에** 탐지하게 한다(막는 것은 아니고, PR 없이 push 한 feature 브랜치는 보지 않는다).

# Intent

- 링크: `plans/2026-09-25-repo-audit-followups/intent.md` 의 `repo-audit-g8-g9-docs-ci` 단위. 항목 원본은 `plans/2026-09-25-repo-audit-remaining/repo-audit-remaining-plan.md` `# Deferred` G8·G9.
- 사용자 결정(2026-09-25): `CLAUDE_REVIEW_CODEX_MODE` 는 폐기하고 프롬프트 문구로 통일(대안: 유지하고 대칭으로 / 이번엔 손대지 않음).
- 규모: medium(README 절, 운영 자산 3곳 + wiki 1곳, CI 스크립트 + 테스트 + workflow, 목적 3).
- 분할: 없음 — README 유출 대응 절(force push 로 이력 재작성)과 CI 백스톱은 결합돼 있다: 재작성 push 직후 CI 가 사라진 base 를 어떻게 다루는지가 절차의 일부다(plan-reviewer 강 1 — FAIL 이면 절차를 따르는 순간 main 이 빨개진다). 한쪽만 머지하면 README 가 CI 동작을 틀리게 서술하거나 CI 가 README 절차를 깬다. codex-mode 폐기는 독립이지만 같은 감사 항목이라 같은 PR 에 두고 되돌림은 커밋 단위로 한다.
- Constraints: 운영 자산(`agents/architecture-reviewer.md`·`skills/dlc/SKILL.md`·`docs/codex-review.md`) 편집은 위 사용자 결정 범위만. CI 백스톱은 가드 스크립트를 바꾸지 않는다(가드의 원격 범위는 `push-remote-scope` 단위). CI 가 실패하면 main push 도 빨갛게 되므로 기존 이력에서 거짓 차단이 없는지 먼저 확인한다.
- Out of scope: 가드 로직·패턴 변경, statusline 스모크(G9 선택 항목 — `scripts/statusline.test.js` 가 `verify.sh node` 로 이미 CI 에서 돈다), GitHub secret scanning 설정.

사실 확인(2026-09-26):
- ✅ `git filter-repo` 는 재작성 뒤 `origin` remote 를 지운다(공식 문서: 다시 push 하려면 `git remote add origin <url>`). README 의 `git push --force-with-lease origin main` 은 그대로는 실패한다.
- 이 repo 의 GitHub ruleset `main-guard` 는 non_fast_forward 를 막고 관리자는 bypass 한다(config-docs-sync 기록). `permissions.deny` 는 비어 있고 force push 는 `permissions.ask` 가 확인한다(README permissions 절).
- `CLAUDE_REVIEW_CODEX_MODE` 를 읽는 코드는 없다. Agent 도구는 subagent 에 환경변수를 넘기지 못한다 — 실제로 쓰인 것은 프롬프트 문구(이 세션의 리뷰 호출 전부).
- 가드 pre-push 는 `push 커밋 --not --remotes` 를 스캔한다. CI checkout(`fetch-depth: 0`)에서는 `refs/remotes/origin/<PR 브랜치>` 가 PR 커밋을 이미 담아 그대로 부르면 스캔 대상이 없다.

# Acceptance

1. README 유출 대응이 GitHub 공식 절차를 따른다 — fresh clone 에서 `git-filter-repo --sensitive-data-removal --replace-text`, `git push --force --mirror origin`(모든 브랜치·태그), ruleset `main-guard` 관리자 bypass, fresh clone 에는 로컬 훅이 없어 CI 스캔이 사후에 본다는 점, push 전 `git log -p --all -S` 로 제거 확인·First Changed Commit(s)·영향 PR 수 보존, 시작 전 다른 머신 push 중지, 끝나고 임시 파일 정리, PR ref·캐시는 GitHub Support, 옛 이력에서 딴 브랜치는 merge 가 아니라 rebase, `permissions.deny`→`permissions.ask` 서술 정정, `==>` 생략 시 `***REMOVED***`. 검증: 실제 filter-repo(uvx)로 bare remote 실측 — 작업 중 checkout 은 거부, fresh clone 에서 브랜치 2·태그 1 재작성 후 `--mirror` push 로 원격 모든 ref 에서 비밀 0건, `origin` 유지, `==>` 없는 줄은 `***REMOVED***`.
2. `CLAUDE_REVIEW_CODEX_MODE` 를 지시하는 문장이 살아 있는 문서(`agents/`·`skills/`·`docs/`·`wiki/pages/`·README)에서 사라지고(남는 것은 "폐기했다" 는 기록), owner 가 아닌 reviewer 는 `docs/codex-review.md` §7 문구를 프롬프트로 받는 한 가지 방식만 남는다. 세 reviewer 정의의 codex 헤더가 같은 목록(외부 codex 모드 포함)을 쓴다. 검증: `git grep -n CLAUDE_REVIEW_CODEX_MODE -- ':!plans'` 가 폐기 기록 줄만.
3. CI 백스톱 `scripts/ci-secret-scan.sh <base> [<head>]`: 이 checkout 의 객체를 alternates 로 빌리는 임시 bare repo 에 base 하나만 추적 ref 로 두고 가드를 pre-push 모드로 돈다. base..head 에 토큰을 추가한 커밋이 있으면 exit 1, 없으면 0, base 이전 토큰은 다시 보지 않는다. 빈·all-zero·checkout 에 없는 base 는 전체 이력(건너뛰지 않음). 가드가 찍는 매치 값(괄호가 든 패턴 이름 포함)과 `--no-verify` 안내는 CI 로그에서 가린다. checkout 의 ref 는 건드리지 않는다. PR 은 head 를 base tip 기준으로 본다(merge 커밋이 아님). 검증: `scripts/ci-secret-scan.test.sh` 9건(CI 모양 fixture·가림(PAT fine 포함)·ref 불변·base 3종은 가드 차단까지 확인·PR head vs main 쪽 토큰·merge 를 스캔하면 잡힌다는 대조).
4. `.github/workflows/lint.yml`: `fetch-depth: 0`, 스캔 스텝(PR: checkout 된 merge 의 `HEAD^1`·`pull_request.head.sha`, push: `before`·`github.sha`; 테스트 스텝 뒤, 테스트가 실패해도 도는 `!cancelled()`), plan-lint 스텝의 `--depth=1` 제거. 현재 main 전체 이력 rc=0. 이 PR 의 CI 로그에 `ci-secret-scan: <40hex>..<40hex>` 줄(`(whole history)` 가 아닌 것)이 나오고 스텝이 통과한다.
5. README CI 절·`--no-verify` 서술·트리, wiki 페이지(`sources:` 포함)·`wiki/log.md`, intent 자기 줄 치환 + Open question(push-remote-scope 의존).
6. 전체: `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음), plan-lint 통과, wiki link check clean.

# Progress

- 2026-09-26: 착수(`/wt`). Explore — README 568-592, lint.yml, `CLAUDE_REVIEW_CODEX_MODE` 참조 5곳(agents 1·docs 2·dlc 1·wiki 1), filter-repo 문서 확인.
- 2026-09-26: plan-reviewer 대기 중 TDD — `ci-secret-scan.test.sh` 6건 Red(스크립트 없음) → 구현(임시 bare repo + alternates + base 추적 ref 하나 — CI 의 detached merge 커밋이 브랜치에서 도달하지 않을 수 있어 clone 대신) → 6 통과. 이 repo main 전체 이력 스캔 rc=0(약 1초, 거짓 차단 없음). README 유출 절차 bare remote 실측. codex-mode 폐기 문서 반영.
- 2026-09-26: plan-reviewer(+codex) CONDITIONAL — 강 5(force push 뒤 없는 base → FAIL 로 main 빨개짐 · filter-repo 는 fresh clone 필요 · main 만 push 하면 다른 ref 에 비밀 · CI 로그에 토큰 앞 30자 · PR 은 merge 커밋을 스캔) 모두 반영. 실제 filter-repo(uvx)로 README 절차 실측, GitHub 공식 문서 확인. 테스트 8 통과.
- 2026-09-26: 단위 커밋 3개 → code-reviewer(+codex high) REQUEST CHANGES — Major 2(`GitHub PAT (fine)` 값이 가려지지 않음 · README 가 CI 를 제거 검증처럼 서술하고 push 전 확인 누락), Minor 4, Nit 7. fix loop 1: 가림 정규식 `[^:]*`·제어문자 앞에서 멈춤·`--no-verify` 줄 제거, README push 전 확인·다른 머신 중지·정리, CI 서술을 CI 커밋으로, PR base `HEAD^1`, 스텝 순서, 테스트 9(가드 차단 확인·merge 대조).
- 2026-09-26: 재확인 — 기존 13건 해소, 신규 Major 1(스캔 스텝이 테스트 실패 시 skip → main push 누출을 영구히 놓침)·Minor 1(가림이 탭에서 멈춤)·Nit 1(정리 단계가 Support 용 파일까지 지움) → fix loop 2: `if: ${{ !cancelled() }}`, 줄 끝까지 가리고 리셋 재부착 + 탭 fixture, 정리 순서. 테스트 9 통과.

# Next

verify → fixup 커밋 → commit-check → `/e merge`(PR CI 로그의 스캔 범위 줄 확인).

# Decisions

- CI 스캔은 ~~임시 clone~~ → **이 checkout 의 객체를 alternates 로 빌리는 임시 bare repo** 에서 한다(이유: `pull_request` checkout 은 merge 커밋을 detached 로 두어 clone 이 가져오는 브랜치 ref 에서 도달하지 않을 수 있다). 그 repo 에는 base 하나만 `refs/remotes/ci-base/base` 로 둬 가드의 `--not --remotes` 가 정확히 base 를 뺀다. 원본 checkout 의 ref 를 지우면 로컬에서 실수로 돌렸을 때 사용자 원격 ref 가 사라지므로 건드리지 않는다.
- 가드는 원격 이름 인자 없이 부른다(현재 동작: 모든 추적 ref 제외 — 임시 repo 에는 base 하나뿐). `push-remote-scope` 가 인자 없는 경로의 의미를 바꾸면 이 스크립트도 맞춰야 한다 — ~~그 단위의 intent 줄에 적는다~~ → intent `# Open questions` 에 `(열림)` 으로(이유: §10 소유권 — 다른 단위의 `# Plans` 줄은 고치지 않는다, plan-reviewer).
- 없는 base 는 FAIL → **전체 이력 스캔**으로 변경 (이유: README 대로 재작성 force push 를 하면 `before` 가 checkout 에 없어 main CI 가 빨개지고 ruleset `lint` 필수 check·autopull-verified-ff 에 걸린다. 전체 이력은 범위가 넓어지는 쪽이라 fail-closed 유지, 약 1초).
- PR 은 checkout 된 merge 커밋이 아니라 `pull_request.head.sha` 를 `base.sha` 기준으로 스캔한다(이유: 가드의 `-m` 이 merge 를 PR 부모와도 diff 해 main 쪽 추가분을 PR 탓으로 다시 스캔한다). 기각: merge 커밋 스캔을 인정하고 문구만 고치기 — 거짓 차단 가능성을 남긴다.
- CI 로그에서 매치 값을 가린다(가드 출력의 `token pattern (<이름>):` 뒤를 래퍼가 치환). 이유: public repo 의 Actions 로그는 공개이고 가드는 30자까지 찍는다(CLAUDE.md §6). 가드는 바꾸지 않는다.
- README 유출 대응은 GitHub 공식 절차로 교체(이유: filter-repo 는 fresh clone 에서만 돌고, `main` 만 push 하면 다른 브랜치·태그에 비밀이 남는다 — 실측). 이 계획에서 되돌리기가 가장 비싼 단계라(틀린 절차는 사고 대응 중에 드러나고 force push 는 되돌릴 수 없다) 실제 filter-repo 로 실측했다. 기각: `--force-with-lease=main:<old>` 로 main 만 push — 다른 ref 가 남고, 재작성 전 tip 기록이 절차를 복잡하게 한다.
- 기각: 모든 브랜치 push 에 도는 별도 workflow — 1인 repo 에서 PR 없이 feature 브랜치를 push 하는 경우가 드물고 CI 비용이 늘어 Goal 을 사후 탐지·PR/main 으로 좁혔다(`# Deferred`).
- PR base 를 payload `pull_request.base.sha` → checkout 된 merge 커밋의 `HEAD^1` 로 변경 (이유: code-reviewer — base.sha 는 이벤트 시점 스냅샷이라 rebase 뒤 옛 값일 수 있다는 보고, merge ref 의 첫 부모는 그 merge 를 만든 base tip 이다).
- 한계로 둔다: main push 범위의 merge 커밋은 가드의 `-m` 때문에 main 쪽에 이미 있던 토큰 줄을 다시 잡는다(main 에 토큰이 남아 있을 때만 — 재작성으로 지우는 것이 해법, README CI 절에 적음). 가드는 이 단위에서 바꾸지 않는다.
- accepted-risk: CI 는 그 PR 자신의 가드 스크립트로 검사한다 — 가드를 약화한 PR 은 스스로 통과한다(1인 소유, 리뷰 흐름에서 가드 변경은 별도로 본다).
- stdin 의 ref 이름은 `refs/heads/ci-scan` — 가드의 main/master 직접 push 차단을 타지 않게.
- 기각: PR diff 의 추가 줄을 별도 grep 으로 스캔 — 가드와 패턴·예외가 갈라져 두 곳을 유지해야 한다.
- 기각: `CLAUDE_REVIEW_CODEX_MODE` 유지·대칭화 — 전달 경로가 없어 문서만 늘고 동작은 문구 방식 그대로다(사용자 결정).
- 커밋 단위: 1) `docs(readme): follow GitHub's sensitive-data procedure for leak response` — README 유출 대응 절 2) `docs(codex-review): drop the unused CLAUDE_REVIEW_CODEX_MODE, keep the prompt phrase` — `docs/codex-review.md`·`agents/{architecture,code,plan}-reviewer.md`·`skills/dlc/SKILL.md`·wiki 페이지·log 3) `ci: scan the pushed range for secrets with the pre-push guard` — `scripts/ci-secret-scan.sh`·`.test.sh`·`.github/workflows/lint.yml`·README CI·`--no-verify` 서술·트리·intent·이 plan.

# Key Files

- `README.md` — Rollback / Incident Response 절, CI 절, 트리
- `docs/codex-review.md` §2·§7, `agents/{architecture,code,plan}-reviewer.md`, `skills/dlc/SKILL.md` — codex 생략 방식
- `wiki/pages/concept/claude-codex-collaboration.md`, `wiki/index.md`, `wiki/log.md`
- `scripts/ci-secret-scan.sh`, `scripts/ci-secret-scan.test.sh` — CI 백스톱
- `.github/workflows/lint.yml`
- `plans/2026-09-25-repo-audit-followups/intent.md` — `# Plans` 자기 줄

# Review Disposition

- [code] Major 괄호 이름 패턴 값 노출 — fix(`[^:]*`, 테스트). Major README 가 CI 를 제거 검증으로 서술·push 전 확인 누락 — fix(`git log -S`·First Changed Commit(s)·PR 수, CI 서술은 CI 커밋의 CI 절로 옮기고 "제거 확인 아님" 명시). Minor(분쟁: Codex Major / Claude Minor) `--mirror` 동시 push 유실 — fix(시작 전 push 중지 한 줄). Minor merge push 재스캔 — 한계 문서화 + `# Deferred`. Minor(PLAUSIBLE) base.sha 스냅샷 — fix(`HEAD^1`). Minor whole-history 테스트 약함 — fix(가드 차단까지 확인).
- [code] 재확인 Major 스캔 스텝 skip(테스트 실패 시) — fix(`if: ${{ !cancelled() }}`). Minor 가림이 탭에서 멈춤 — fix(줄 끝까지 + 리셋 재부착, 탭 fixture). Nit 정리 단계가 Support 파일 삭제 — fix(요청 뒤 정리).
- [code] Nit "아래 검증 절" 방향 — fix(해당 문장 삭제). Nit 커밋 1 의 CI 앞선 참조 — fix(CI 언급을 커밋 3 으로). Nit 장식용 merge fixture — fix(대조 assertion). Nit ANSI 리셋 유실·CI 의 `--no-verify` 안내 — fix. Nit /tmp 잔존 — fix(정리 단계). Nit 시그니처 표기 — fix. Nit 스텝 순서 — fix(테스트 뒤로).
- [plan] 강 1 없는 base → FAIL — fix(전체 이력). 강 2 filter-repo fresh clone·README 서술 오류 — fix(공식 절차, 실제 filter-repo 실측). 강 3 main 만 push·PR ref — fix(`--mirror`, Support). 강 4 CI 로그 토큰 노출 — fix(래퍼 가림, 테스트). 강 5 PR merge 커밋 스캔 — fix(head.sha, 테스트).
- [plan] 약: 브리프 문구·rebase — fix(GitHub 공식 권고는 rebase, merge 금지로 서술). pip PEP 668·`==>` 주석 — fix(uvx/brew, 실측). lease 기준값 — 해당 없음(`--mirror` 로 교체). Acceptance/Decisions 불일치 — fix. §10 소유권 — fix(intent 되돌림 + Open question). Acceptance 4 증거 — fix(CI 로그 범위 줄). Goal 과장 — fix(사후 탐지·PR/main). reviewer 헤더 비대칭 — fix. `~/.codex/agents` 잔존 — defer(audit-low-batch). README:127 — fix. 분할 근거 — fix(결합). PR 자신의 가드 — accepted-risk. 기각안·가장 위험한 단계 — fix. `--depth=1` fetch — fix(제거, 스캔 스텝을 앞으로). wiki sources — fix.

# Deferred

- (low) main push 범위에 merge 커밋이 있고 main 쪽에 토큰이 이미 있으면 가드의 `-m` 이 다시 잡는다 — 가드 수정이 필요하면 push-remote-scope 와 함께 본다.
- (low) 저장소 밖 `~/.codex/agents/architecture-reviewer.toml` 에 `CLAUDE_REVIEW_CODEX_MODE` 가 남아 있다 — audit-low-batch 의 `~/.codex/agents` 스냅샷 재생성에서 함께 정리.
- (low) PR 없이 push 한 feature 브랜치는 CI 비밀 스캔을 타지 않는다(`lint.yml` 은 main push·main 대상 PR 만) — 필요해지면 모든 브랜치 push 에 도는 가벼운 workflow.

# Blockers

없음.
