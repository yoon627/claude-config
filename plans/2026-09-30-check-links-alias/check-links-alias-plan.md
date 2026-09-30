---
title: check-links-alias — check_links.py 가 별칭 링크 [[a|b]] 도 링크로 읽는다
status: done
started: 2026-09-30
updated: 2026-09-30
intent: plans/2026-09-29-repo-context-kit/intent.md
---

# Goal
`skills/wiki/check_links.py` 가 별칭 링크 `[[a|b]]` 를 `a` 로의 링크로 센다. 그래서 별칭의 dead link 를 잡고, 별칭으로만 이어진 페이지를 orphan·outbound 부족으로 잘못 내지 않는다. 출력 형식·인자·exit code 의미는 그대로다.

# Intent
- 묶음: `plans/2026-09-29-repo-context-kit/intent.md`. `plans/2026-09-30-wiki-graph-search/wiki-graph-search-plan.md` 의 # Deferred 후속이다.
- 델타 — Problem: `WIKILINK` 가 `|` 를 받지 않아, 별칭 간선이 dead link·outbound·orphan 판정과 index 의 dead link 판정에서 빠진다. 실제 공용 wiki 에도 별칭 링크가 있다(wiki-graph-search 실측: 출현 8, 별칭으로만 생긴 간선 5). 사용자 승인(2026-09-30, 남은 항목 처리).
- 델타 — Constraints: 묶음 제약(호출 계약 불변, 파일 하나만 복사해도 동작)을 따른다. 해석은 # Decisions 에 있고, 묶음 Constraints 문구도 이때 분명히 했다.
- 델타 — Out of scope:
  - stem 이름 규칙(`[a-z0-9-]+`) 변경.
  - index 등재 기준 변경 — 등재는 지금처럼 별칭 없는 `[[stem]]` 만 인정한다(# Decisions).
  - `[[a\|b]]`(표 안 escape)·`[[a#h]]`·`[[a#h|b]]` 형태. wiki_search 도 읽지 않고, 수정 전에도 같았으며, 공용 wiki 에 0건이다.
  - frontmatter 판정(정본은 `wiki_check.py schema`).
  - 공용 wiki 페이지 갱신(main 세션 — # Deferred).

# Acceptance
1. **단위 테스트**(`skills/wiki/test_check_links.py`) — Python 3.13·3.9 — 전부 통과. 새 테스트는 수정 전 동작에서 실패한다(Red — 직접 실행 또는 변이 사본).
   - 별칭 간선이 outbound·inbound 로 세진다: 별칭으로만 들어오는 페이지가 orphan 이 아니고, 별칭 1개 + 링크 1개인 페이지가 outbound 부족이 아니다.
   - 없는 대상을 가리키는 별칭은 `dead link: [[zzz]] in a (대상 페이지 없음)` 한 줄로 잡힌다(기존 문구 그대로).
   - 닫히지 않은 별칭(`[[x|열림 [[b]]`)이 뒤의 링크를 삼키지 않는다.
   - index 등재는 별칭 없는 `[[stem]]` 만 인정하고(별칭 등재는 `index 누락`), index 의 별칭 dead link 는 `index dead link: [[zzz]]` 로 잡힌다.
   - 규칙 대조: `check_links.WIKILINK.pattern == wiki_search.LINK.pattern`, 경계 표(`[[a|]]`→a, `[[a|b|c]]`→a, `[[a|b]c]]`→없음, 별칭 안 줄바꿈→없음).
2. **계약 불변**: 기존 테스트 7개가 그대로 통과하고, 실제 공용 wiki 실행 결과가 수정 전과 같다(`wiki link check: clean`, exit 0).
3. **그래프와 일치**: 실제 공용 wiki 에서 `wiki_search` 그래프 간선과 check_links 간선이 같다(나가는·들어오는 모두 차이 0) — 스크래치 대조 스크립트. 수정 전 차이는 별칭 간선 5 였다.
4. **문서**: `check_links.py` docstring·주석, `wiki_search.py` 의 "check_links.WIKILINK 는 별칭을 읽지 않는다" 주석, `skills/wiki/SKILL.md` lint 절의 check_links 줄, wiki-graph-search plan # Deferred 가 새 동작과 맞다 — `rg -n "별칭" skills/wiki` 대조.
5. `bash scripts/verify.sh` 마지막 줄이 main 과 같은 skip 만 둔 `ALL PASS`, `bash skills/improve/improve.sh --ci` exit 0 — 격리 runner.

# Progress
- 2026-09-30: `/wt` 로 worktree 생성(base `main@6f1d754`). 계획 전 조회로 공용 wiki `wiki-search-design`(check_links 를 묶음 제약 때문에 고치지 않았다는 결정)을 읽었다.
- 2026-09-30: TDD Red → 구현 → Green.
  - Red: 새 테스트 둘이 의도한 이유로 실패했다. 별칭 dead link 를 놓쳐 `[]` 가 나왔고, 별칭 간선이 빠져 outbound 부족 2·orphan 1 이 나왔다. 닫히지 않은 별칭 테스트는 경계 가드라 수정 전에도 통과한다.
  - Green: 10개, 3.13·3.9. 변이 3종(no-alias·naive-alias·alias-required) 모두 KILLED.
  - A2: 수정 전후 모두 `wiki link check: clean` exit 0. A3: check_links 간선 307 → 312 = 그래프 312, 나가는·들어오는 차이 0.
- 2026-09-30: 코드 리뷰(Codex 병행) APPROVE, Critical 0·Major 0·Minor 4·Nit 6. 처분은 # Review Disposition.
  - 반영 뒤 테스트 13개(3.13·3.9). 변이 9종(정규식 경계 4종·index 판정 2종 포함) 모두 KILLED. `index-entry-alias` 변이가 M1 이전 동작이라 새 index 테스트의 Red 증거다.
  - A2·A3 재측정 결과는 같다(clean·exit 0, 312 = 312, 차이 0).
- 2026-09-30: 격리 runner — `verify.sh` exit 0 `ALL PASS (skip: install-codex-skill.test.ps1)`(main 과 같은 skip), `improve --ci` exit 0. evidence gate 1~5 를 모두 증거로 충족해 판정은 DONE 이다(status 는 머지 때 done).
  - 대조 중 SKILL.md 의 "별칭도 링크로 센다"가 index 등재에는 맞지 않아, SKILL.md·docstring 에 "index 등재는 별칭 없는 `[[a]]` 만"을 더했다(문서만, 대상 테스트 재실행 OK).
- 2026-09-30: 커밋 1개, commit-check 이상 없음. small 이라 로컬 ff-merge(§8)로 main 에 반영한다. 묶음 intent 는 미착수 단위와 열린 질문이 남아 open 이다. 남은 것은 # Deferred 의 공용 wiki 갱신(main 세션)이다.

# Next

# Decisions
- 관련 결정 [[wiki-search-design]](공용 wiki)의 "묶음 제약 때문에 check_links 는 고치지 않는다"를 뒤집는다(사용자 승인 2026-09-30).
  - 근거: 제약이 막는 것은 호출 계약(경로·인자·출력 형식·exit code 의미)이다. 별칭 인식은 넷 다 그대로 두고 판정만 정확하게 한다.
  - 바뀌는 판정은 두 가지다.
    - 별칭의 dead link 가 새로 잡힌다(exit 0→1 가능). 지금 놓치고 있는 위반이다. 코드 예시에 ASCII 별칭(`[[foo|bar]]`)을 적은 경우도 잡히는데, 위키링크를 코드 예시로 쓰지 않는 규약(check_links 주석)과 맞다.
    - 별칭으로만 이어진 페이지의 orphan·outbound 위반이 사라진다(exit 1→0 가능).
  - 실제 공용 wiki 에서는 수정 전후 결과가 같다. consumer repo wiki 의 별칭 출현은 확인하지 않았다(❌모름).
- 정규식은 `wiki_search.LINK` 의 별칭 규칙(`(?:\|[^\[\]\n]*)?`)을 그대로 옮긴다. 별칭은 `[` 를 받지 않아 닫히지 않은 별칭이 뒤의 링크를 삼키지 않는다.
  - `wiki_search` 나 `wiki_check` 를 import 하지 않는다. 묶음 제약 "파일 하나만 복사해도 동작" 때문이다. 같은 규칙인지는 테스트가 pattern 문자열을 대조해 지킨다(테스트는 복사 제약의 대상이 아니다).
- index 등재 기준은 바꾸지 않는다(리뷰 M1). 등재는 별칭 없는 `[[stem]]` 만 인정한다.
  - smoke 의 등재 검사와 같은 기준이다. wiki_search 도 별칭 등재 줄에서는 index 요약을 읽지 않는다.
  - index 의 dead link 판정은 별칭도 본다.
- 묶음 intent # Constraints 첫째 항목 문구를 "호출 계약(경로·인자·출력 형식·exit code 의 의미)"으로 분명히 했다(리뷰 M4). 같은 묶음에 진행 중인 plan 이 없어 영향을 통지할 대상은 없다.
- Acceptance 1 을 리뷰 M1·M2 로 넓혔다(index 등재, 규칙 대조, 경계 표). 기준을 약하게 한 것이 아니라 더한 것이다.
- 커밋 단위: 1개 — 정규식·테스트·문서가 한 동작이다.

# Key Files
- `skills/wiki/check_links.py` — `WIKILINK`·`PLAIN_WIKILINK` 정규식, index 등재 판정, docstring·주석
- `skills/wiki/test_check_links.py` — 별칭·index·규칙 대조 테스트
- `skills/wiki/wiki_search.py` — LINK 옆 주석
- `skills/wiki/SKILL.md` — lint 절 check_links 줄
- `plans/2026-09-30-wiki-graph-search/wiki-graph-search-plan.md` — # Deferred 해소 표시
- `plans/2026-09-29-repo-context-kit/intent.md` — # Constraints 첫째 항목 문구, # Plans 줄

# Blockers
없음

# Review Disposition
코드 리뷰 — code-reviewer(Codex 병행) APPROVE, Critical 0·Major 0·Minor 4·Nit 6.
- M1 index 등재가 별칭을 받아 smoke·wiki_search 와 판정이 갈린다 — fix: 등재는 `PLAIN_WIKILINK` 로만, dead link 는 별칭까지. 테스트 `test_index_entry_needs_plain_link`.
- M2 복제한 정규식의 경계와 wiki_search 와의 일치가 고정되지 않았다(변이 4개 생존) — fix: pattern 대조 테스트와 경계 subTest 표. 같은 변이 4개가 이제 KILLED.
- M3 plan 이 실제 상태보다 뒤처졌다 — fix: Progress·Next·Acceptance 예시를 맞췄다.
- M4 intent Constraints 문구가 옛 해석으로 읽힐 수 있다 — fix: 문구를 호출 계약으로 분명히 했다.
- N1 코드 예시의 ASCII 별칭이 dead link 가 된다 — fix: # Decisions 에 적고, 공용 wiki 를 고칠 때 한글 placeholder 를 쓰라는 주의를 # Deferred 에 붙였다.
- N2 escape·anchor 형태 미인식 — fix: # Intent 의 Out of scope 에 적었다(회귀 아님).
- N3 dead alias 메시지가 stem 만 적는다 — wontfix: 출력 템플릿은 호출 계약이라 그대로 둔다.
- N4 테스트가 helper 대신 파일에 직접 덧쓴다 — fix: `_page` helper 로 같은 본문을 만든다.
- N5 done plan 의 당시 근거 문장("check_links 는 못 읽는다") — wontfix: 그때의 사실을 적은 기록이다. 해소 표시는 # Deferred 줄에 붙였다.
- N6 SKILL.md 편집이 README drift 경고를 부를 수 있다 — false-positive: README 는 링크 문법을 서술하지 않아 낡은 문장이 없다(`README.md:379,703` 확인).

# Deferred
- 공용 wiki `wiki-search-design` 의 "check_links 는 별칭을 못 읽는다" 서술과 index 요약을 머지 뒤 main 세션에서 고친다(공용 wiki 는 worktree 에 사본이 없다). 링크 문법 예시는 stem 규칙 밖의 한글 placeholder(`[[링크|표시]]`)로 적는다 — ASCII 예시는 이제 dead link 로 잡힌다.
