---
title: docs-untrack — 하네스 참조 문서를 공개 repo 에서 빼 비공개 wiki repo 의 docs/ 로 옮긴다
status: done
started: 2026-10-07
updated: 2026-10-07
---

# Goal
`~/.claude/docs/` 4개 문서를 공개 repo 추적에서 빼고 비공개 wiki repo(`~/.claude/wiki`)의 `docs/` 로 옮긴다. 하네스 참조를 `~/.claude/wiki/docs/<파일>` 절대경로로 바꿔 worktree·다른 머신에서도 깨지지 않게 하고, 백업·이력·동기화는 wiki repo 가 맡는다.

# Intent
- Problem: 처음 계기는 참조 문서 한 줄의 repo 이름이었으나, 사용자 확인(2026-10-07)으로 그 이름은 숨길 필요가 없다(같은 이름이 이미 push 된 plans 9개 파일에도 있다). 남은 목적은 사용자 결정대로 docs/ 를 공개 repo 추적에서 빼고, 백업·보관·머신 간 동기화를 비공개 wiki repo 로 맡기는 것(무료 cloud 비교 후 선택, 2026-10-07).
- Constraints: 문서 내용은 바꾸지 않는다(이름 일반화 불필요 — 위). wiki repo 쓰기는 main 세션에서(§11). history rewrite 는 하지 않는다.
- Out of scope: 문서 내용 개편, history rewrite, Google Drive 보조 백업.
- 분할: 없음 — `~/.claude` 쪽(추적 해제·참조 치환)과 wiki 쪽(파일 이전)은 별개 repo 커밋이지만, 앞쪽만 반영되면 참조가 없는 경로를 가리키므로 같은 세션에서 연달아 반영한다.

# Progress
- 2026-10-07: worktree 생성(base 로컬 main@dcec070), Explore — `.gitignore` whitelist(`!/docs/`), 스크립트·hook·CI 는 docs 내용에 의존 안 함, 참조 34곳 11파일. 1차 구현(로컬 untracked + `~/.claude/docs/` 절대경로 + 사후 복원 안내) → plan-reviewer CONDITIONAL 반영.
- 2026-10-07 (cont.): 사용자가 백업 수단으로 비공개 wiki repo 이전 선택 → 설계 변경. 참조 35곳 `~/.claude/wiki/docs/` 로, CLAUDE.md §3-1·§2 는 wiki 예외에 `wiki/docs/` 포함으로, README 는 wiki repo 안내로(사후 복원 절차 삭제 — pull 하면 wiki 에서 온다), `.gitignore` 주석·`improve.sh` 재추적 게이트 문구 갱신. wiki_check 는 `pages/` 만 검사(`wiki_check.py:324`)라 wiki 최상위 `docs/` 는 lint 대상 밖.

- 2026-10-07 (cont.): code-reviewer(+Codex high, 1차 설계 diff 대상) Critical·Major 0 — 유효 지적 반영(공개 텍스트 사유 중립화, bootstrap 표·README B 절에 docs 출처, 다른 머신 로컬 수정 시 pull 거부·자동 pull 무출력 정지 안내, improve 헤더·README 설명). 1차 설계 전용 지적(README 사후 복원 문단)은 설계 변경으로 소멸.
- 2026-10-07 (cont.): 재리뷰(Critical·Major 0) 반영. 사용자 확인 — repo 이름은 숨길 필요 없음 → 목적을 백업·동기화로 정리. 전체 verify 를 중단하고(사용자 승인) 바뀐 축 검증: syntax·shell ALL PASS, improve `--ci` error=0·`docs/ 비추적` OK. Acceptance 1·2·4·5·6 충족, 3 은 main 반영·이전 후 관찰.

# Next
전체 verify → ff 직전 `~/.claude/docs/` 를 scratchpad 로 복사 → 로컬 ff → main 세션에서 wiki repo 에 `docs/` 이전(내용 그대로, 문서 안 repo 상대 `skills/...` 는 `~/.claude/skills/...` 로)·WIKI.md 디렉토리 표·wiki 페이지의 `docs/` 참조 갱신 → wiki repo 커밋 → `sync_codex_agents.py` 재실행(`~/.codex/agents` 의 옛 참조) → 정리. push 할 때는 wiki repo 를 먼저, `~/.claude` 를 나중에(다른 머신이 옛 docs 삭제를 받기 전에 새 위치가 원격에 있게).

# Decisions
- 선행 decision 조회: 공용 wiki `decision/wiki-shared-layer`(wiki 를 비공개 repo 별도 clone 으로 분리) — **따른다**. 같은 방식으로 참조 문서도 그 repo 에 둔다.
- 커밋 단위: `~/.claude` 1개(추적 해제 + 참조 치환 — 한 머지에서만 유효) + wiki repo 1개(파일 이전·WIKI.md·페이지 참조).
- 백업 수단: 비공개 wiki repo(사용자 선택 2026-10-07). 기각: 새 비공개 GitHub repo(관리 repo 가 늘어남), Google Drive(이력·동기화 약함, 수동 — 보조로만 가능), 이메일(커넥터 없음·이력 없음). 앞선 1차 설계의 "로컬 untracked + 사후 복원"은 백업이 없어 대체됨.
- 기각한 대안(추적 해제 자체): (a) 문제의 한 줄만 일반화하고 추적 유지 — 사용자가 추적 제외를 택함. (b) history rewrite — 이름을 숨길 필요가 없어 불필요(사용자 확인 2026-10-07).
- 종결은 로컬 ff — 현행 §8 은 medium 을 `/e merge` 로 보내지만 사용자가 merge 커밋 없는 로컬 ff 를 원했다(2026-10-07, 머지 정책 plan 이 정식화 예정). ff 순간 main 의 `~/.claude/docs/` 가 지워지므로(추적 해제 커밋) ff 직전 scratchpad 로 복사하고 그 사본을 wiki 로 옮긴다. 다른 머신은 이 repo pull 로 옛 docs 가 지워지고 wiki pull 로 새 위치에 받는다 — 순서가 바뀌어도 이력에 원본이 있다.
- 최종 검증을 전체 verify(약 50분)에서 바뀐 축(`syntax`·`shell`)+`improve.sh --ci` 로 변경 — 사용자 승인(2026-10-07, "너무 오래 걸린다"). 근거: 변경은 문서·`.gitignore`·`improve.sh` 1곳뿐이고 node·python 코드 변경 없음(node·python 축 결과에 영향 없음 — 추정이지만 diff 범위로 확인). 검증 시간 개선 작업의 "바뀐 축만 로컬" 첫 적용 사례.
- 재추적 게이트: `skills/improve/improve.sh` 의 wiki 비추적 검사 옆에 docs 검사(.gitignore 는 이미 추적된 경로·`add -f`·잘못된 merge 해소를 못 막는다).
- `scripts/dlc-doc-drift.test.js:54` 의 `docs/codex-review.md` 는 분류 함수 입력 fixture 라 유지.

# Key Files
- `.gitignore` — `!/docs/` 제거 + 사유.
- `CLAUDE.md` §2(rg 안내)·§3-1(글로벌 상태 예외), `README.md`(설치 7단계·wiki 이전 안내·트리), `agents/{architecture,code,plan}-reviewer.md`, `skills/{dlc,e,wt}/SKILL.md`, `skills/wt/references/rm-recovery.md`, `scripts/bootstrap/README.md` — 참조 치환.
- `skills/improve/improve.sh` — docs 재추적 게이트(6번 축 헤더 포함). README improve 설명.
- (머지 후) `~/.codex/agents/*.toml` — `sync_codex_agents.py` 로 재생성.
- (wiki repo) `docs/*.md`, `WIKI.md` 디렉토리 표, `pages/**` 의 `docs/` 참조.

# Acceptance
1. `git ls-files docs` 가 비고 `git check-ignore docs/codex-review.md` 가 매칭한다.
2. 옛 참조 0건 — 상대 `docs/(codex-review|…)` 와 `~/.claude/docs/` 가 하네스 파일에 없다(README 의 "옛 경로는 지워진다" 안내 1줄 제외).
3. [post-merge] main 반영·이전 후 관찰: `~/.claude/wiki/docs/` 4파일 존재(사본과 내용 동일, repo 상대 `skills/` 참조만 절대경로로) + `git -C ~/.claude/wiki ls-files docs` 4개 + 참조된 `~/.claude/wiki/docs/<파일>` 모두 존재 + `~/.claude` main `git status --porcelain` 깨끗.
4. README·CLAUDE.md 에 참조 문서 위치(wiki repo `docs/`)·편집 경로(main 세션)·검색 시 경로 명시가 있다.
5. `bash skills/improve/improve.sh` 6번 축 `docs/ 비추적` OK.
6. 바뀐 축 검증 — `bash scripts/verify.sh syntax`·`bash scripts/verify.sh shell` `ALL PASS` + `improve.sh --ci` error=0(사용자 승인 2026-10-07로 전체 verify 에서 변경 — `# Decisions`).

# Blockers
(없음)

# Deferred
(없음 — 공용 wiki 페이지의 `docs/` 참조 갱신은 이번 작업의 wiki 커밋에 포함한다.)

# Review Disposition
- plan-reviewer(CONDITIONAL, 1차 설계 대상, codex off):
  - 강1 삭제 시점 오판 → fix(Decisions — ff 직전 사본, 다른 머신은 wiki pull).
  - 강2 "pull 전 복사" 불가능 → fix(설계 변경으로 해소 — 내용은 wiki 에서 온다).
  - 강3 사후 복원 → 대체(백업이 wiki repo 로 생겨 불필요).
  - 강4 docs 편집 경로 없음 → fix(§3-1 wiki 예외에 `wiki/docs/` 포함, main 세션 편집).
  - 강5 rg 가 docs 를 건너뜀 → fix(§2 안내).
  - 약1 재추적 게이트 → fix(improve.sh).
  - 약2 공용 wiki 참조 → fix(이번 wiki 커밋에 포함).
  - 약3 `~` 표기 → 확인(기존 관례).
  - 약4 Acceptance 3 무의미 → fix(main 반영·이전 후 관찰).
  - 약5 기존 worktree 영향 → 확인(남은 worktree 없음).
  - 약6 ignored 사본 → 정보.
  - 약7 기각 대안 → fix(Decisions).
- code-reviewer(+Codex high, NEEDS DISCUSSION, Critical·Major 0 — 1차 설계 diff 대상):
  - `.autopull-off` 예방 범위(Codex Major·리뷰어 Minor) → 소멸(설계 변경으로 문단 삭제).
  - 로컬 수정 시 삭제가 아니라 pull 거부·자동 pull 무출력 정지 → fix(README 안내).
  - PowerShell `~` 미확장 → 소멸(복원 명령 삭제, 남은 명령은 `"$HOME/.claude"`).
  - bootstrap 표·README B 절·Windows "(선택)" 위치 → fix(docs 는 wiki clone 으로 온다고 명시, 수동 복사 단계 삭제).
  - 공개 텍스트가 노출 사유를 적음 → fix(README·.gitignore·improve.sh 사유 중립화).
  - `~/.codex/agents` 옛 참조 → fix(머지 후 `sync_codex_agents.py` 재실행, `# Next`).
  - Key Files 불일치 → fix.
  - Nit improve 헤더·SKILL·README 설명 → fix(헤더·README; SKILL.md:16 은 wiki 내부 무결성 문단이라 무관).
  - Nit .gitignore 대칭 → fix(재추적 시 improve error 주석).
- code-reviewer 2회차(새 설계, codex 외부, Critical·Major 0, NEEDS DISCUSSION):
  - 다른 머신: 옛 docs 는 자동 pull 로 지워지고 wiki 는 수동 pull → fix(README 안내 + push 순서 wiki 먼저, `# Next`).
  - plan 이 노출 위치를 file:line 으로 짚음(PLAUSIBLE) → fix(Problem 일반화, README·.gitignore 사유 문구 축약).
  - §11 에 `docs/` 자리 없음 → fix(§11 bullet 추가 — 쓰기·공개 점검 동일).
  - `wiki_search` 가 docs 를 못 찾음 → fix(§11 bullet 에 명시).
  - Nit CLAUDE.md:12 원문자 예외의 상대 `docs/` → fix(`wiki/docs/`).
  - Nit 이전할 문서 안 repo 상대 `skills/...` → fix 예정(wiki 커밋 때, `# Next`).
  - Nit README 이전 안내 위치 → wontfix(A 절 안내가 E 절을 가리킴).
  - Open: 이전 사유("비공개")와 §11 "공개 가능한 것만" 의 표현 차 → 해소(사유 문구를 "비공개 wiki repo 로 옮겼다"로 축약). 이후 사용자 확인으로 그 이름은 숨길 필요가 없어 이전 시 일반화도 하지 않는다 — 이미 머지된 두 plan 의 file:line 표기 수정은 되돌렸다.
