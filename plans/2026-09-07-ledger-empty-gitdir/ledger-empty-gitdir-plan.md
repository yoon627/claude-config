---
title: ledger-empty-gitdir — 빈 .git 을 repo 로 오판해 evidence gate 가 오작동하던 것 수정
status: done
started: 2026-09-07
updated: 2026-09-08
---

# Goal

`verify.sh` 의 선행 실패 1건(`dlc-evidence-ledger.test.js:82`)을 근본 원인까지 고친다. `insideSomeRepo` 가 내용 없는 `.git` 디렉토리를 repo 로 오판해, repo 밖 경로를 `changed=true` 로 기록하던 것.

# Progress

- 2026-09-07: `settings.json` pull 차단 문제를 처리하다 `bash scripts/verify.sh` 에서 선행 실패 1건 발견. pull 직후·무변경 상태에서 재현되어 baseline 확정.
- 2026-09-07: 3 Whys 로 원인 확정 — (1) `/tmp` 파일이 repo 안으로 판정 (2) `insideSomeRepo` 가 `fs.existsSync(<dir>/.git)` 로만 판정 (3) 이 머신에 **완전히 빈 `C:\Users\USER\.git`** 존재(2026-07-25 생성). git 본체는 `fatal: not a git repository` 로 거부하나 `existsSync` 는 구분 못 함.
- 2026-09-07: 1차 수정(HEAD 존재로 유효성 판정) → codex 리뷰가 Critical 지적, 폐기. `.git/HEAD` 유실 손상 repo 를 repo 밖으로 판정해 게이트를 조용히 끄는 false negative 였다(실증: 직전=false, 수정=true).
- 2026-09-08: 2차 수정(빈 디렉토리 여부로 판정) + codex 재검토 반영(ENOENT 경쟁 상태 catch 분리, fallback 진입 단언, 주석에 감수 명시). 회귀 테스트 2개 추가. `verify.sh node` ALL PASS.

# Next

완료. 머지 후 별도 작업 대상은 `# Deferred` 참고.

# Decisions

- **판정 기준을 "정상 repo 인가" → "repo 였던 흔적이 있는가" 로** (이유: 이 함수는 `git check-ignore` 가 이미 exit 128 로 실패한 뒤에 불린다. 역할은 "repo 밖이라 실패한 건가, git 이 깨져서 실패한 건가"를 가리는 것이므로, 판정 불능은 보수적으로 repo 안으로 쳐야 게이트가 꺼지지 않는다).
- **기각 — `insideSomeRepo` 를 `git rev-parse --is-inside-work-tree` 로 교체**: git 이 이미 실패한 상황에서 불리는 함수라 같은 이유로 또 실패한다. 그러면 완화 판정이 나와 게이트가 조용히 꺼진다. 파일시스템 판정을 유지해야 하는 이유가 그것이다.
- **기각 — 빈 `C:\Users\USER\.git` 삭제로 해결**: 방아쇠일 뿐 원인이 아니다. 지우면 같은 코드가 다음 머신에서 또 속는다.
- **기각 — `HEAD` 존재를 유효성 기준으로** (codex Critical): `.git/HEAD` 만 유실된 손상 repo를 repo 밖으로 판정해 안전 불변식을 정반대로 뒤집는다.
- **감수 — 내용이 통째로 비워진 `.git` 은 완화된다** (codex 재검토 Critical 1): 빈 디렉토리와 구분 불가. 다만 `git init` 은 언제나 HEAD·config·objects·refs 를 쓰므로 git 이 만들어내는 상태가 아니다. 관측되지 않는 가상 손상의 false negative 를 감수하고 실측된 false positive 를 없애는 쪽을 택했다. 주석에 명시.
- **기각 — `readdirSync` → `opendirSync` O(1) 화** (codex Major 3): `.git` 최상위 엔트리는 구조상 10개 안팎이라 실익이 없고, 지적된 네트워크 I/O 무기한 정지는 `opendirSync` 도 동일하다.

# Key Files

- `scripts/dlc-evidence-ledger.js` — `hasRepoAt`(신규) + `insideSomeRepo`. 판정 기준 교체.
- `scripts/dlc-evidence-ledger.test.js` — 회귀 2건 추가(빈 `.git` → changed=false / 손상 repo → changed=true).

# Review Disposition

- codex Critical 1 (1라운드, HEAD 기준의 false negative) — `fix`
- codex Critical 1 (2라운드, 비워진 `.git` 구분 불가) — `accepted-risk` (Decisions 에 근거·주석에 명시)
- codex Critical 2 (ENOENT 경쟁 상태) — `fix`
- codex Major 1 (`GIT_DIR` 재배치 작업트리 미발견) — `defer` → `# Deferred`
- codex Major 2 (상대경로 `fp` 는 `dirname(fp)` 전제 불성립) — `defer` → `# Deferred`
- codex Major 3 (`readdirSync` 비용) — `wontfix` (Decisions)
- codex Major 4 (테스트가 fallback 진입 미증명) — `fix`
- codex Minor (주석이 휴리스틱임을 명시) — `fix`

# Deferred

- `insideSomeRepo` 는 `GIT_DIR`/`GIT_WORK_TREE` 로 연결된 작업트리를 조상 탐색으로 발견하지 못한다. 그 repo 가 손상돼 `check-ignore` 가 128 이면 완화된다. 중간·선행 이슈(이번 변경 이전부터 존재) — `scripts/dlc-evidence-ledger.js`.
- `isIgnored` 는 상대경로 `fp` 에 대해 `cwd` 를 쓰므로 "`dirname(fp)` 에서 판정" 전제가 깨진다. 비-repo cwd 에서 `../repo/src.js` 를 편집하면 완화된다. 호출 계약상 hook 은 절대경로를 주지만 단언·테스트로 고정돼 있지 않다. 낮음·선행 이슈 — `scripts/dlc-evidence-ledger.js:72`.
- `scripts/verify.sh` 의 shellcheck 축이 이 머신에서 `[skip] shellcheck 미설치` 로 빠진다. 로컬 초록이 CI 실패를 못 잡는 구간. 낮음.

# Blockers

- 없음.
