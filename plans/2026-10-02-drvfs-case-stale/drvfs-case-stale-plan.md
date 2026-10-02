---
title: drvfs-case-stale — 대소문자를 무시하는 FS 에서 wiki 경로를 디스크 표기로 맞춰 거짓 stale 을 없앤다
status: done
started: 2026-10-02
updated: 2026-10-02
intent: plans/2026-09-29-repo-context-kit/intent.md
---

# Goal
`skills/wiki/wiki_check.py` 의 `resolve_context` 가 wiki 루트의 repo 안쪽 이름들을 디스크 표기로 맞춘다 — 대소문자를 무시하는 파일시스템(WSL DrvFs 실측)에서 대소문자만 다른 wiki 인자나, 탐색이 찾은 `wiki` 와 디스크 이름 `Wiki` 의 차이가 판정을 바꾸지 않게. `open_repo` docstring 의 대소문자 서술도 맞춘다(사용자 지시 "남은거 진행해" → 2026-10-02 다음 작업으로 선택).

# Intent
- 묶음: `plans/2026-09-29-repo-context-kit/intent.md` — `wiki-tests-windows-fix` # Deferred [medium] 의 후속(묶음 `# Plans` 의 `drvfs-case-stale (미착수)` 를 이 plan 으로 바꾼다). 델타는 아래.
- Problem: WSL DrvFs(`/mnt/c`, fixture 를 `TMPDIR=/mnt/c/…` 에 둠)에서 `stale --branch Wiki` 가 `Wiki/pages/concept/api.md: covers 변경`·rc 1 을 낸다 — 올바른 표기(`wiki`)는 clean·rc 0(2026-10-02 재현). DrvFs 의 `resolve()`·`getcwd`·`git rev-parse --show-prefix` 가 모두 친 표기를 내서 `open_repo` 의 대조를 통과하고, 페이지 경로(`Wiki/…`)가 index 경로(`wiki/…`)와 어긋난다. macOS 는 `getcwd` 가 정규화해 그 대조에서 거부(exit 2)되고, Windows 는 `resolve()` 가 디스크 표기로 되돌려 같은 판정이 된다(공용 wiki `python-path-resolve-case`).
- Constraints: 대소문자를 가리는 FS 에서 `Wiki` 같은 오타를 조용히 `wiki` 로 바꾸지 않는다(친 경로가 실제로 있을 때만 바꾼다). git 을 부르지 않는다(`resolve_context` 는 git 없는 단계 — 섹션 머리 주석).
- Out of scope: hook 입력 `cwd`(시작점) 자체의 대소문자 — 선행 plan FP-6 (c) accepted-risk 그대로(macOS 에서 repo 루트 대조가 `systemMessage` 를 낸다). 유니코드 정규화(macOS NFD) — 지금처럼 `open_repo` 의 git 대조가 거부한다.

# Progress
- 2026-10-02: 착수. DrvFs 재현(위 Problem).
- 2026-10-02: 새 테스트 Red(DrvFs `'Wiki' != 'wiki'`, ext4 통과) → `disk_case` 구현 → Green(DrvFs 의 두 대소문자 테스트, ext4). skills/wiki 전체 Windows 3.13 189 OK(skip 16)·3.9 189 OK(skip 33)·WSL ext4 189 OK(skip 2). WSL DrvFs 전체는 5건 실패 — base `wiki_check.py` 로도 같은 5건(실행 비트·`chmod 0` 의 읽기·목록 막기·`mkfifo` — DrvFs 기본 마운트의 한계)이고 base 는 대소문자 2건이 더 실패. `open_repo` 의 prefix 불일치 문구에서 대소문자를 뺐다(이제 닿지 않는다).

- 2026-10-02: code-review APPROVE(Minor 5·Nit 3) → 반영(# Review Disposition). 확인 범위: `disk_case` 의 매핑 분기는 WSL DrvFs 에서(두 대소문자 테스트), Windows 에서는 새 직접 호출 단언으로 확인한다. ext4(CI)는 매핑에 닿지 않는다(가리는 FS 라 표기가 다른 이름은 없다) — 그쪽은 "오타를 고치지 않는다" 만 확인한다. macOS 는 실행하지 않았다.

- 2026-10-02: 반영 뒤 재검증 — Windows DiscoveryTest·StaleBranchTest 통과, 항등 `disk_case` 변이가 Windows 에서 실패(`'WIKI' != 'wiki'`), WSL DrvFs 20·ext4 20 통과. simplify — 변경 없음. 최종 검증(격리 runner, 단독) `bash scripts/verify.sh` exit 0 `ALL PASS (skip: install-hooks.test.js(case) record-verified.test.sh)`(기존 환경 skip). DONE → 로컬 ff-merge 로 닫는다(small, §8).

# Next

# Review Disposition
- [code] APPROVE. M1 매핑 분기가 CI·Windows 에서 안 돈다(항등 mutant 통과) — fix(`disk_case` 직접 호출 단언 — Windows 에서 매핑을 탄다) · M2 기존 대소문자 테스트 주석이 새 동작과 어긋남 — fix · M3 디스크 표기 ≠ 추적 표기면 거짓 stale(회귀 가능) — accepted-risk(Decisions ⚠️, docstring) + `ls-files` 기각 사유 정정 · M4 intent·Progress 의 macOS·확인 범위 — fix(intent 줄에 미실행, Progress 에 범위) · M5 공용 wiki `python-path-resolve-case` 가 낡는다 — defer(# Deferred, main 세션) · Nit1 docstring "대소문자만 같은" — fix · Nit2 드물게 남는 대소문자 거부에 문구가 원인을 안 말함 — fix(문구·docstring 에 대소문자 복원) · Nit3 wiki_search 의 공용·repo 같음 판정이 정규화 차이로 갈릴 수 있음 — defer · 범위 밖 `load_pages` 의 `pages` 리터럴 — defer

# Decisions
- wiki decision 조회: `python-path-resolve-case`("표기가 판정을 바꾸지 않는다" 하나를 지킨다 — 거부·정규화 둘 다 맞다) — 따른다. 선행 freshness-gate plan FP-6(macOS 는 git 대조로 exit 2) — 정규화로 바꾼다(아래 ⚠️).
- 디렉터리 목록으로 디스크 표기를 찾는다: wiki 루트가 repo 루트 후보 안이면, 그 아래 이름마다 그 이름이 실제로 있는데(`exists()`) 부모의 목록(`os.listdir`)에 똑같이 없으면 대소문자만 같은 목록 이름으로 바꾼다. 탐색(`find_wiki` 는 `wiki` 를 글자 그대로 붙인다)과 인자 둘 다 같은 함수를 거친다. 기각: `git ls-files --full-name` 으로 git 의 표기를 받기 — `resolve_context` 는 git 을 부르지 않는 단계이고, git 을 이미 부르는 stale 경로에서 맞추려 해도 `load_pages` 가 `open_repo` 전에 페이지 경로를 정하므로 경로를 다시 매핑해야 한다(code-review M3 가 짚은 실제 비용). 기각: 디스크 표기와 다르면 거부 — 디스크 이름이 `Wiki` 인 repo 에서 탐색 경로가 매 턴 hook 경고가 된다.
- ⚠️ 디스크 표기가 git 이 추적하는 표기와 다른 경우(대소문자만 바꾼 rename 을 받았는데 ignored 파일 때문에 옛 표기 디렉터리가 남음 — git 동작 추론, 재현 안 함)에는 이제 DrvFs 에서 거짓 stale 이 난다(전에는 탐색이 붙인 `wiki` 가 우연히 맞았다). macOS 는 그 경우 거부(exit 2)가 거짓 stale 로 바뀐다 — 흔한 경우(친 표기·디스크 이름 `Wiki`)를 고치는 것과 드문 경우의 회귀가 상충 — 흔한 쪽을 택하고 accepted-risk: 오류가 오탐 방향(페이지 경로는 "페이지도 바뀌었다" 판정과 표시에만 쓰여 놓치는 stale 은 생기지 않는다 — 공용 wiki `lesson-gate-safe-side-first` 의 안전측)이고 Windows 와 같은 한계다. docstring 에 적었다.
- ⚠️ macOS 의 대소문자만 다른 wiki 인자가 거부(exit 2)에서 정규화(올바른 판정)로 바뀐다 — 선행 결정(FP-6)과 상충 — 불변식("표기가 판정을 바꾸지 않는다")은 둘 다 지키고, 정규화는 디스크 이름이 `Wiki` 인 repo 의 탐색 경로까지 고치므로 정규화를 택했다. macOS 는 실행하지 않았다(APFS 가 대소문자를 보존하는 목록을 낸다는 데서 추론) — 보고에 미검증으로 적는다.
- 커밋 단위: 1개 — 함수·docstring·테스트가 한 목적이다.

# Acceptance
1. WSL DrvFs(fixture `TMPDIR=/mnt/c/…`): `StaleBranchTest.test_case_mismatched_wiki_argument_is_refused_or_judged_the_same` 가 수정 전 실패(rc 1 vs 0, 위 재현) → 수정 뒤 통과.
2. 새 테스트(인자 `Wiki` 와, 디스크 이름이 `Wiki` 인 wiki 의 탐색): 대소문자를 무시하는 FS 에서는 `wiki_root` 이름이 디스크 표기(`wiki`·`Wiki`)이고, 가리는 FS 에서는 바뀌지 않는다(`Wiki` 인자는 그대로, `Wiki` 디렉터리는 탐색되지 않음). 수정 전 DrvFs 에서 실패, ext4(CI 와 같은 쪽)·Windows 에서 전후 통과.
3. 회귀: skills/wiki 테스트가 Windows(3.13·3.9)·WSL ext4·WSL DrvFs 에서 통과(DrvFs 는 이번 테스트들 — 전체가 DrvFs 에서 도는지는 별도로 보고), 최종 `bash scripts/verify.sh` 가 Windows 에서 단독 실행으로 `ALL PASS`(skip 목록 그대로).
4. 문서: `open_repo` docstring 이 "대소문자만 다른 인자" 를 거부 사유로 말하지 않고, 정규화는 `resolve_context` 가 한다고 적는다. SKILL.md·README 에 대소문자 서술이 있으면 맞춘다(없으면 확인함).

# Key Files
- `skills/wiki/wiki_check.py` — `resolve_context`, 새 디스크 표기 함수, `open_repo` docstring
- `skills/wiki/test_wiki_check.py` — 새 테스트(DiscoveryTest 또는 StaleBranchTest 옆)
- `plans/2026-09-29-repo-context-kit/intent.md` — `# Plans` 의 `(미착수)` 줄 → 이 plan

# Deferred
- [wiki] `~/.claude main 세션에서 /wiki ingest` — 공용 `python-path-resolve-case` 의 "WSL DrvFs … wiki_check 의 거짓 stale"·"거부(macOS 식)" 서술을 갱신: wiki_check 는 `resolve_context` 의 `disk_case` 로 디스크 표기를 쓴다(DrvFs 실측, macOS 미실행), 디스크 표기 ≠ 추적 표기면 남는 한계 · 출처: 공개(이 repo).
- [low] wiki_search 의 공용·repo 같음 판정(`same`)이 정규화된 repo wiki 와 정규화하지 않은 공용 경로를 `==` 로 비교한다 — 공용 wiki 의 디스크 이름이 `wiki` 가 아닌 대소문자 무시 FS 에서 같은 wiki 를 두 번 검색할 수 있다(`os.path.samefile` 후보).
- [low] `load_pages` 는 `pages` 를 글자 그대로 붙인다 — 대소문자 무시 FS 에서 디스크 이름이 `Pages` 면 같은 계열의 거짓 stale(Windows 포함, 원래부터). WIKI.md 관례를 어긴 repo 만 해당.
- [low] WSL DrvFs(기본 마운트, `metadata` 없음)에 fixture 를 두면 실행 비트·`chmod 0`·FIFO 에 기대는 테스트 5건이 실패한다(`StaleReportTest.test_exec_bit_only_change_is_stale`·`test_page_read_error_exits_2`, wiki_search `test_unreadable_pages_directory_exit_2`, check_links `test_non_regular_md_entries_are_not_pages`·`test_unreadable_subdirectory_exits_2`) — base 에서도 같다. 그 환경의 skip 조건이 필요한지는 DrvFs 에서 테스트를 돌릴 일이 생길 때 판단한다(CI·Windows·ext4 는 해당 없음).

# Blockers
