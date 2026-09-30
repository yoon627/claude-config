---
title: wiki-private-repo — 공용 wiki 를 비공개 GitHub repo 로 옮기고 공개 repo(~/.claude)에서 추적 해제
status: done
started: 2026-09-30
updated: 2026-09-30
---

# Goal
공용 wiki(`~/.claude/wiki`)를 비공개 GitHub repo(이하 "비공개 wiki repo")로 이력째 옮기고 같은 경로에 별도 clone 으로 둔다. 공개 repo 는 `wiki/` 를 추적하지 않고, 다시 추적되면 CI 가 막는다. 이 전제를 적은 문서를 맞춘다. GitHub issue #206 의 "wiki 를 git 추적에서 빼기" 항목.

# Intent
- Problem: 2026-09-29 사용자가 "wiki 는 공개 repo 에 커밋하지 말고 이 노트북에만"을 원했고, 진행 중이던 wiki-freshness-gate(PR #215, 2026-09-30 머지) 뒤로 미뤘다. 2026-09-30 사용자가 보관 방식으로 "비공개 repo"를 골랐다(선택지: 로컬 전용 / 비공개 repo / 형식 수정만 커밋 / 보류). 이유는 백업·이력·다른 머신 동기화 유지. 선택지 문구에 "형식 위반 3쪽은 고른 보관 방식 안에서 함께 고친다"가 있었다.
- Constraints:
  - 공개 repo 의 과거 이력은 그대로 둔다(filter-repo·force push 안 함 — 2026-09-29 사용자 결정).
  - 공용 wiki 의 적립 기준("공개 가능한 사실")과 경로(`~/.claude/wiki`)는 바꾸지 않는다(# Decisions).
  - 비공개 wiki repo 의 이름·URL 은 공개 repo 의 어디에도(plan·문서·커밋·PR) 쓰지 않는다(CLAUDE.md §11 — 비공개 repo 이름 금지).
  - 범위는 요청의 핵심 동작으로 좁게(사용자 피드백 2026-09-30).
- Out of scope: 적립 기준 완화, SessionStart 자동 pull 에 wiki repo 동기화 추가, setup 스크립트의 자동 clone(URL 을 적을 수 없다 — README 절차로 대신), `skills/jira-worklog` 식별자, 미게시 커밋 `d58e913`(#206 의 다른 항목).
- Open questions: 없음 — 저장소 이름과 생성(외부 작업)은 plan 승인 때 확인한다.
- 분할: 없음 — 비공개 repo 준비, 공개 repo 추적 해제, 문서 갱신은 순서가 묶인 한 전환이다. 추적 해제만 먼저 머지되면 wiki 가 어디에도 없고, 문서만 먼저 머지되면 규약이 사실과 어긋난다.

# Acceptance
각 항목: 무엇이 충족되나 — 어떻게 검증 — 통과 기준.

1. 비공개 wiki repo 가 공개 repo 의 wiki 를 이력째 담는다 — `gh repo view <repo> --json visibility`, split 커밋의 tree 와 머지 직전 `origin/main:wiki` 의 tree 대조, split 커밋 subject 목록과 `git log --format=%s origin/main -- wiki` 대조 — `PRIVATE`, tree sha 같음, subject 목록 같음.
2. 비공개 wiki repo 의 후속 커밋이 검사를 통과한다 — 후속 커밋은 `.gitignore`(`raw/`), `.gitattributes`(`* text=auto`), `WIKI.md` 의 공개 문구 갱신, `pages/decision/wiki-shared-layer.md` 갱신, schema 위반 3쪽 형식 수정, `log.md` 기록 — `wiki_check.py schema`, `check_links.py`, main checkout 에서 `test_wiki_check.py` 의 WIKI.md 대조 테스트 — schema 위반 0, check_links 통과, 대조 테스트 통과(skip 아님).
3. 공개 repo 가 wiki 를 추적하지 않고, 다시 추적되면 CI 가 막는다 — 브랜치와 머지 뒤 main 에서 `git ls-files wiki`, `git check-ignore -v wiki/index.md`, 스크래치 repo 에서 wiki 파일을 추적시킨 뒤 `improve.sh --ci` — 0개, `.gitignore` 로 무시됨, 게이트가 error 로 exit ≠ 0.
4. 공개 repo 검증이 wiki 없이 통과한다 — 격리 runner 의 `bash scripts/verify.sh`, 이 브랜치를 wiki 없이 풀어 놓은 스크래치 checkout 에서 `bash skills/improve/improve.sh --ci` — verify 마지막 줄 `ALL PASS`(main 과 같은 skip 만), improve exit 0. `test_wiki_check.py` 의 WIKI.md 대조 테스트가 CI·worktree 에서 unittest skip 되는 것은 허용한다(2 에서 main 대조).
5. 문서가 새 전제와 맞는다 — `rg` 대상: CLAUDE.md, `skills/wiki/SKILL.md`, `skills/dlc/SKILL.md`, `docs/dlc-details.md`, `skills/improve/SKILL.md`, `skills/improve/improve.sh`, README.md, `scripts/bootstrap/README.md`. 통과 기준:
   - 다음 서술이 0줄이다: 공용 wiki 가 이 repo 에 추적된다, worktree 의 `wiki/`, "`/wt` → `/wiki ingest`", 공용 wiki 를 repo 상대경로 `wiki/` 로 읽는 조회.
   - 다음 서술이 있다: 공용 wiki 는 비공개 wiki repo 의 별도 clone 이다, 절대경로 `~/.claude/wiki` 로 읽는다(`rg` 는 경로를 명시해야 잡힌다), 쓰기는 main 세션에서 하고 wiki repo 의 main 에 직접 커밋한다(§8 예외), worktree 중에 생긴 공용 적립은 plan `# Deferred` 에 남겨 main 세션에서 처리한다, 머신별 전환 절차가 README 에 있다.
6. 이 머신 전환 — 머지 뒤 main 에서 `git -C ~/.claude/wiki remote -v`, `git -C ~/.claude/wiki status --porcelain`, `git -C ~/.claude status --porcelain`, `pages/**/*.md` 개수 — `~/.claude/wiki` 가 비공개 wiki repo clone 이고, 두 repo 모두 clean 이며, 페이지 70쪽(`pages/` 파일 74개 = 페이지 70 + `.gitkeep` 4).
7. 공개 점검 — 스크래치 금지어 목록(`private-denylist.txt`, 비공개·미커밋)과 비공개 wiki repo 이름으로 브랜치 diff·커밋 메시지·PR 본문을 스캔한다 — 0건.

# Progress
- 2026-09-30: `/wt` 로 worktree 생성(base `main@8802d6d`). Explore: 공개 repo 에서 `wiki/` 를 참조하는 파일 18개.
  - `improve.sh --ci` 의 wiki 개수 점검은 wiki 가 없으면 이미 건너뛴다. 9번 대장 lint 도 파일이 없으면 `[info]` 에 exit 0 이다(실측).
  - doc-drift·early-stop hook 은 git 이 아니라 도구 편집 경로로 판정한다.
  - main 의 wiki 에는 ignored 파일(raw 원문)이 없다.
  - 관련 결정 [[wiki-shared-layer]] 확인.
- 2026-09-30: plan 리뷰 — architecture-reviewer(planning) REQUEST CHANGES(Major 4·Minor 5), plan-reviewer CONDITIONAL(Major 6·Minor 8). 두 리뷰는 workflow 로 병렬 실행했고, Codex 는 미가용이었다(workspace out of credits). 처분은 # Review Disposition.
- 2026-09-30: 사용자 승인 뒤 실행(저장소 이름은 Report 에만 적는다).
  - 비공개 wiki repo 를 만들었다(PRIVATE). split 기준은 `8802d6d` 이고, split tree 가 `8802d6d:wiki` 와 같고 subject 109개가 다중집합으로 같다.
  - 이 repo 의 pre-push hook 이 원격과 관계없이 `refs/heads/main` push 를 막는다(`--no-verify` 는 §8 금지). 그래서 비공개 repo 는 스크래치 clone 에서 push 했다. repo-local hooksPath 라 중첩 clone 에는 걸리지 않는다.
  - 비공개 repo 후속 커밋 두 개(이관 기록, 형식 수정): schema clean(70쪽), check_links clean, PyYAML 로 고친 `sources` 항목 수 확인.
  - 이 브랜치에서 `.gitignore`(whitelist 제거, `/wiki/` 추가), `git rm -r -q wiki`(77개), 문서 8곳, `improve.sh` 6번 재추적 게이트·6·9번 절대경로·`--ci` 건너뛴 점검 표시를 고쳤다.
  - Acceptance 5 의 `rg` 대조에서 옛 전제 문장 0건. README 7·312·545행의 `wiki/pages/…` 는 근거 인용이라 그대로 둔다(clone 기준 경로로도 맞다).
- 2026-09-30: 구현 리뷰(code-reviewer)와 격리 runner 를 workflow 로 병렬 실행했다.
  - code-reviewer 는 REQUEST CHANGES(Major 2·Minor 4·plan 대조 2)였다. 처분은 # Review Disposition "[구현 리뷰]".
  - runner: `verify.sh` exit 0, 마지막 줄 `ALL PASS (skip: install-codex-skill.test.ps1)` — PowerShell 미설치로 main 과 같은 skip(PR #213 본문과 같음). `improve.sh --ci`·plan-lint 통과.
  - 리뷰 반영 뒤 메인이 다시 돌렸다. `verify.sh` 는 같은 결과(같은 skip 하나). shellcheck·`native-overlap-lint.test.js`(점검 번호 계약) 통과.
  - CI 흉내: `CLAUDE_IMPROVE_WIKI` 를 없는 경로로 두고 `improve.sh --ci` 를 돌렸다. `[ok] wiki/ 비추적`, 6·9 건너뜀, exit 0. 격리 가드가 HOME 변경을 막아 이 override 를 더했다.
  - 게이트 재현(스크래치 repo): 기준 exit 0, wiki 파일 `add -f` 뒤 `[error] … 추적됨` exit 1, 중첩 repo 를 gitlink(160000)로 넣어도 exit 1.
  - `git check-ignore -v wiki/index.md` → `.gitignore:42:/wiki/`.
- 2026-09-30: 커밋 뒤 머지 전에 사용자가 공개 유지를 다시 물었다. 이유는 "레포에 포함되니 수정할 때마다 충돌나서 번거로웠다" 였다.
  - 이력 근거: main 에서 `wiki/log.md`·`index.md` 를 건드린 merge 6개 중 5개가 두 부모와 다른 결합 diff hunk 를 가진다(08-05·08-11·09-28·09-29 ×2). 충돌 해소의 정황이고 확증은 아니다(Codex).
  - 사용자 요청으로 Codex 결정 리뷰를 받았다(effort medium, 크레딧 복구 확인). 결과: 분리(B)는 타당하다 — 충돌 감소는 쓰기 직렬화에서 나온다. A2(`merge=union`)는 PR 흐름에 부족하다(GitHub 머지 지원 추정 불가, index 부적합). Codex 권고는 원격 없는 로컬 전용이었다(근거 "이 노트북에만"). 다만 "사용자가 비공개 GitHub 보관·여러 머신 복제를 명시적으로 허용하면 B 원안"이라고 했고, 오늘 사용자 선택이 그 허용이다.
  - 사용자가 "비공개 GitHub 로 머지"를 확정했다.
- 2026-09-30: `/e merge` — 머지 직전 대조에서 `origin/main` 이 split 기준 그대로(wiki 차이 0)였다. `commit-check` 로 plan fixup 을 합쳤다(사용자 승인). PR #216. 머지 뒤 이 노트북의 `~/.claude/wiki` 를 비공개 clone 으로 바꾸는 일과 Acceptance 6 확인은 main 세션에서 한다(Report).

# Next

# Decisions
- 관련 결정 [[wiki-shared-layer]](2026-09-26)을 부분적으로 따른다.
  - 따르는 것: 경로 `~/.claude/wiki` 가 어느 repo 세션에서나 같다는 점. 그리고 submodule 기각 사유 두 가지다 — 새 worktree 마다 init 이 필요하고 DETACHED HEAD 가 되며, 공개 repo 의 CI 가 private submodule 을 받지 못한다.
  - 뒤집는 것: 그 결정은 "단일 wiki repo 를 고정 경로에 clone" 을 "코드와 같은 브랜치 갱신을 포기한다"는 이유로 기각했다. 이번에는 `~/.claude` 에 그 구조를 쓰고, 같은 브랜치 갱신 포기를 받아들인다.
  - 이유: 사용자가 비공개 보관을 명시적으로 골랐다(2026-09-30). 공개 repo 에 두는 한 같은 브랜치 갱신과 비공개 보관은 함께 성립하지 않는다.
  - 대가: `~/.claude` worktree 작업(dlc 등)에서 생긴 공용 wiki 적립 — 결정·교훈·`workflow-failures` — 은 코드 PR 에 실리지 않는다. plan `# Deferred` 에 남기고 `/e` 로 main 에 돌아온 세션에서 처리한다(memory 와 같은 흐름).
  - `wiki-shared-layer.md` 자체는 비공개 wiki repo 에서 갱신한다(Acceptance 2).
- 연결 방식: 비공개 wiki repo 를 `~/.claude/wiki` 에 별도 clone 하고, 공개 repo 는 `.gitignore` 의 whitelist(`!/wiki/`)를 빼서 무시한다. 기각: submodule(위 결정), 다른 경로(예 `~/wiki` — 모든 문서·스킬·hook 의 `~/.claude/wiki` 참조를 고쳐야 한다).
- 이력: `git subtree split --prefix=wiki` 로 wiki 의 커밋 이력을 그대로 옮긴다(wiki 경계를 넘는 rename 0건 — 리뷰 확인). 기각: 현재 파일로 새 초기 커밋 하나(비공개 repo 를 고른 이유인 이력이 끊긴다).
- 적립 기준은 유지한다: 공용 wiki 에는 계속 "공개 가능한 사실"만 적는다. 저장소가 비공개가 돼도 모든 repo 세션(공개 repo 포함)이 이 wiki 를 읽고 내용을 옮겨 적을 수 있다. CLAUDE.md §11 공개 점검 목록에서는 wiki 표면(페이지·`sources`·index·log)만 뺀다.
- 쓰기 위치와 §8 예외: worktree 에는 wiki 사본이 없다. 공용 wiki 는 절대경로 `~/.claude/wiki` 로 읽는다 — 부모 `.gitignore` 때문에 `~/.claude` 루트에서 돌린 `rg`·Grep 은 wiki 를 건너뛰므로 경로를 명시한다. 쓰기는 main 세션에서 하고, wiki repo 의 main 에 직접 커밋한다. worktree·PR 을 거치지 않는 문서 전용 저장소라 §8 "main 직접 작업 금지·main 에서는 커밋 생략"의 예외로 명시한다. push 는 §8 대로 요청 시만.
- 다시 추적되는 것 막기: `.gitignore` 는 이미 추적된 경로나 `git add -f`·gitlink 를 막지 못한다. 그래서 `improve.sh --ci` 에 "`git ls-files wiki` 가 비어 있지 않으면 error" 게이트를 둔다(CI 가 이미 부른다).
- 비공개 wiki repo 이름은 공개 repo 의 어디에도 쓰지 않는다(§11). README 의 clone 절차는 `<비공개 wiki repo URL>` 로 적고, setup 스크립트 자동 clone 은 두지 않는다.
- ⚠️ 저장소 이름은 추정 선택이다(공개 repo 와 짝이 되는 짧은 이름). 외부에 만드는 이름이라 승인 때 확인한다 — 이름은 이 plan 에 적지 않는다.
- `improve.sh` 6·9번은 repo 상대경로 `wiki/` 를 읽어 worktree 에서 조용히 건너뛴다. 9번은 "대장 없음 → 생성" 이라고 오도한다. 그래서 기본 경로를 `$HOME/.claude/wiki` 로 바꾸고, 환경변수 override 는 그대로 둔다. CI 는 그 경로가 없어 지금처럼 건너뛴다.
- 한계: 공용 wiki 가 별도 repo 가 되면 `wiki_check.py stale` 의 `covers` 로 `~/.claude` 코드를 감시할 수 없다(git 최상위가 달라진다). 지금 공용 wiki 의 covers 페이지는 0개다.
- 가장 비싼 단계는 공개 repo 머지다. SessionStart 자동 pull 로 모든 머신에 퍼져 wiki 파일을 지운다. 비공개 repo 생성·push 는 머지 전이라 되돌리기 쉽다.
- rollback:
  - 머지 전 실패: 비공개 wiki repo 를 지우거나 둔다. 공개 repo 는 그대로다.
  - 머지 후: 머신마다 `~/.claude/wiki` clone 을 다른 곳으로 옮긴다 → 공개 repo 에서 머지를 revert → pull(wiki 다시 추적) → 이동 뒤 비공개 repo 에만 한 커밋의 내용을 공개 repo 로 옮겨 적는다. clone 을 먼저 옮기지 않으면 pull 이 "untracked working tree files would be overwritten" 으로 멈춘다.
- 커밋 단위: 1개 — 추적 해제·게이트·문서 갱신은 한 전환이다. 나누면 중간 커밋이 모순 상태가 된다. 비공개 wiki repo 의 커밋은 다른 repo 라 여기 단위와 별개다.

# Key Files
- `.gitignore` — `!/wiki/` whitelist 와 `wiki/raw/` 줄 제거
- `CLAUDE.md` — §3-1(사본 없는 전역 상태에 공용 wiki, main 세션에서 쓰기), §3-6(Workflow Findings 누적 위치), §8(wiki repo main 직접 커밋 예외), §11(두 계층·절대경로·공개 점검 목록·적립 제안 형식), §13(공용 lesson 위치)
- `skills/wiki/SKILL.md` — 공용 계층의 위치·검색 경로·쓰기 위치·커밋 위치
- `skills/dlc/SKILL.md` — 계획 전 decision 조회(절대경로), Workflow Findings 공용 누적(main 세션)
- `docs/dlc-details.md` — ingest 제안 형식, workflow-failures 누적 위치
- `skills/improve/SKILL.md`·`skills/improve/improve.sh` — 공용 wiki 절대경로, 재추적 게이트
- `README.md` — wiki 절, 새 머신·다른 머신 전환 절차, tree
- `scripts/bootstrap/README.md` — 새 머신 설치에 wiki clone 안내
- 비공개 wiki repo: `.gitignore`, `.gitattributes`, `WIKI.md`, `pages/decision/wiki-shared-layer.md`, `pages/concept/plan-handoff.md`, `pages/decision/git-hook-network-safety.md`, `pages/decision/ops-doc-slimming.md`, `log.md`

# Blockers
없음

# Review Disposition
- [arch M1·plan M1] 머지 경쟁 — split 뒤 main 에 새로 생긴 wiki 파일은 추적된 채 남고 비공개 repo 에 없다 — fix: 머지 직전 `git diff --name-status <split 기준> origin/main -- wiki` 대조(Next 5). Acceptance 1 의 tree 대조 기준을 "머지 직전 origin/main:wiki" 로 바꾼다. Acceptance 3 을 머지 뒤 main 에서 다시 판정한다.
- [arch M1] 다시 추적되는 것을 막는 장치 없음 — fix: `improve.sh --ci` 에 `git ls-files wiki` 게이트(Acceptance 3).
- [arch M1] 다른 worktree·브랜치의 wiki 편집이 옮겨지지 않는다 — fix(점검): plan-reviewer 가 `git log main..<b>` 로 `claude-md-slim`·`autopull-verified-client` 에 wiki 커밋 0건을 확인했다. arch 가 본 `diff -rq` 차이는 base 차이다. 머지 직전 대조(Next 5)가 새로 생긴 것을 잡는다.
- [arch M2] split 시점과 머지 시점 사이의 차이 — fix: 위 M1 과 같은 조치.
- [arch M3·plan M6] 문서 범위 누락(dlc 의 decision 조회 상대경로, Workflow Findings, improve SKILL, CLAUDE.md §3-6·§13, bootstrap README) — fix: Key Files·Acceptance 5 확장. "절대경로로 읽고 main 세션에서 쓴다" 원칙.
- [arch M4·plan M2] 머신별 전환 순서 — fix: README 절차(깨끗한지 확인 → 백업 → pull → 빈 디렉터리 확인 → clone, 또는 임시 경로 clone 후 이동). 다른 머신은 머지 전 `.autopull-off` 권고. 이 머신은 임시 clone 을 먼저(Next 5·7).
- [plan M3] rollback 없음 — fix: # Decisions rollback.
- [plan M4] 새 쓰기 위치가 §8 main 커밋 금지와 모순 — fix: §8 에 wiki repo 예외를 명시한다(Acceptance 5).
- [plan M5] 기각된 대안(고정 경로 clone — 같은 브랜치 갱신 포기)의 비용을 다루지 않았다 — fix: # Decisions 에 뒤집는 이유와 대가. `wiki-shared-layer.md` 갱신(Acceptance 2).
- [plan m1] "77쪽"은 파일 수 — fix: 페이지 74 + clean 으로(Acceptance 6).
- [plan m2] 커밋 수 대조는 동어반복 — fix: tree sha + subject 목록 대조(Acceptance 1).
- [plan m3·arch m5] `improve.sh` 수정 불필요(대장 없으면 info·exit 0) / worktree 에서 오도하는 안내 — fix: 기본 경로를 `$HOME/.claude/wiki` 로(# Decisions). 재추적 게이트도 같은 파일이다.
- [plan m4·arch m8] WIKI.md 대조 테스트가 CI·worktree 에서 skip — fix: Acceptance 2·4 에 명시(main 에서 대조).
- [plan m5·arch m9] `covers` 한계 — fix: # Decisions 한 줄.
- [plan m6] worktree 에 ignored `wiki/` 사본이 남는다 — fix: `git rm -r -q wiki` 로 사본까지 지운다(Next 3).
- [plan m7] 3쪽 형식 수정은 범위 밖 — wontfix: 사용자가 고른 선택지의 질문 문구에 "형식 위반 3쪽은 고른 보관 방식 안에서 함께 고친다"가 있었다. 비공개 repo 안의 작은 수정이다.
- [plan m8] Acceptance 7 의 목록 출처가 정의되지 않았다 — fix: `private-denylist.txt`(스크래치) + 비공개 repo 이름으로 정의. 이 머신에는 `~/.claude/private-terms.txt` 가 없어 pre-commit 검사가 건너뛰어진다.
- [arch m6] 루트 `rg` 가 중첩 wiki 를 건너뛴다 — fix: 검색 경로 명시 원칙(# Decisions, Acceptance 5).
- [arch m7] 비공개 repo 에 `.gitattributes` 없음 — fix: Acceptance 2.
- [메인] draft plan 에 비공개 repo 이름을 적었다(공개 repo 에 커밋되는 파일) — fix: 이름을 plan·문서·커밋·PR 에서 뺀다(Constraints, Acceptance 7).
- [구현 리뷰] Major(CONFIRMED) README E 절 1단계가 push 안 한 로컬 wiki 커밋을 찾기만 하고 되돌릴 길이 없어, 사용자가 공개 repo 로 push 해서 풀 수 있다 — fix: 그 갈래를 두고 "공개 repo 로 push 해서 풀지 않는다" 경고를 넣었다.
- [구현 리뷰] Major(PLAUSIBLE) "Windows·macOS 공통" 명령의 `~` 를 PowerShell 5.1 이 확장하지 않는다 — fix: `$env:USERPROFILE` 로 바꾸라는 안내(Git Bash 는 그대로).
- [구현 리뷰] Minor §11 이 공개 점검 목록에서 wiki 표면을 빼, SKILL 이 "단일 정의"로 가리킨 곳에 wiki 가 없다 — fix: §11 공용 wiki bullet 에 "금지 목록은 wiki 페이지·sources·index·log·커밋 메시지에도 적용" 한 줄.
- [구현 리뷰] Minor README B 절(기존 머신)에 wiki clone 안내가 없다 — fix: Windows·macOS B 절에 E 절 안내 한 줄.
- [구현 리뷰] Minor `CLAUDE_IMPROVE_WIKI` 미문서, 9번 대장 기본값이 override 를 따르지 않는다 — fix: 대장 기본값을 `$WIKI/pages/…` 로, README·improve SKILL 에 문서화.
- [구현 리뷰] Minor(PLAUSIBLE) 재추적 게이트는 CI 에서의 사후 보고다(로컬 ff-merge 뒤 main push 는 막지 못한다) — defer: pre-push 에 같은 검사를 넣는 것은 다른 운영 자산 변경이다(# Deferred). PR 경로는 머지 전에 막힌다.
- [codex 결정 리뷰] 비공개 GitHub 는 "이 노트북에만" 이 아니다 → 로컬 전용 권고 — 사용자 결정으로 처리: 2026-09-30 사용자가 "비공개 repo"(백업·동기화 이유)를 골랐고, Codex 도 그 허용이면 B 원안이라고 했다.
- [codex 결정 리뷰] 남는 위험(머신 간 동시 편집, 같은 clone 의 동시 세션, 수동 동기화 누락, `# Deferred` 적립 누락, 코드·wiki 시점 불일치) — accepted-risk: README E 절의 "쓰기 전에 pull", main 세션 한 곳 쓰기 원칙으로 줄인다. 적립 누락 추적 장치는 # Deferred.
- [codex 결정 리뷰] Critical: 공개 plan 의 `# Deferred` 로 wiki 원문·비공개 식별자가 새는 경로 — fix(기존 규칙): §11 제안 형식이 이미 "공개 점검을 통과한 요약·공개 근거" 만 허용한다. 새 문구 불필요.
- [codex 결정 리뷰] push 전 차단 없음(CI 는 머지 전에만) — defer(기존 # Deferred "재추적을 push 전에 막기").
- [codex 결정 리뷰] `wiki_check.py` `open_repo()` 는 코드와 wiki 가 다른 repo 면 거부해 공용 wiki 의 covers 검사를 쓸 수 없다 — 기존 # Decisions 한계로 기록돼 있음(covers 페이지 0개).
- [구현 리뷰] plan 대조: `.autopull-off` 권고가 README 에 없다 — fix: E 절 0단계. README 545행 인용 — fix: Progress 의 근거 인용 목록에 더함.

# Deferred
- `scripts/dlc-evidence-ledger.js` 의 Bash 편집 대조(`bashEditDiff`)는 이 repo 의 git diff 로 plan·README·`wiki/index.md` 를 본다. wiki 가 빠지면 Bash 로 고친 wiki index 를 못 봐 문서 drift 경고가 한 번 더 날 수 있다(경고를 끄는 쪽 경로라 누락이 아니라 오탐). low.
- 다른 머신 전환 — 각 머신에서 README Install E 절(사용자). 그 머신에 밀린 wiki 편집이 "있을 수 있음/모름"(사용자 답)이라 E 절 1단계 확인이 먼저다.
- 재추적을 push 전에 막기 — `scripts/pre-commit-check.sh`·`.ps1` 의 pre-push 에 `git ls-files -- wiki` 검사를 더할지 판단한다. 지금은 CI(`improve.sh --ci`)가 PR 머지 전에만 막는다. 로컬 ff-merge 뒤 main 직접 push 는 CI 가 사후에 알린다. low(구현 리뷰).
- worktree 중 미룬 공용 wiki 적립의 처리 추적 — `# Deferred` 는 보존일 뿐 처리 보장이 아니다(Codex). main 복귀 시 미처리 항목을 보여 주는 장치(예: `/e` 복귀 단계 안내)를 검토한다. low.
- 다른 머신의 wiki 동기화 — SessionStart 자동 pull 은 `~/.claude` 만 본다. wiki repo 는 수동 `git -C ~/.claude/wiki pull` 이다. 불편하면 후속으로 hook 확장을 검토한다. low.
