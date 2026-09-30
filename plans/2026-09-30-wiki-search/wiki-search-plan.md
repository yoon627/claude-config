---
title: wiki-search — 공용 wiki 를 cwd 와 무관하게 찾는 검색 스크립트(#217)
status: done
started: 2026-09-30
updated: 2026-09-30
---

# Goal
`skills/wiki/wiki_search.py` 로 공용 wiki(`~/.claude/wiki`)와 현재 repo 의 `wiki/` 를 질의어로 검색해, 관련 페이지를 점수순으로 경로·제목·맞은 줄과 함께 보여 준다. `/wiki query` 와 dlc 의 계획 전 결정 조회가 이 스크립트를 먼저 부르게 문서를 잇는다. GitHub issue #217.

# Intent
- Problem: 결정 조회는 모델이 `index.md` 한 줄 요약을 키워드로 훑는 방식이라 페이지가 늘수록 놓친다. #216 뒤 공용 wiki 는 별도 clone 이어서 `~/.claude` 루트의 `rg`·Grep 이 건너뛰고, worktree 에는 사본이 없다 — 절대경로를 빠뜨리면 "없음"으로 조용히 넘어간다([[lesson-grep-absence-not-proof]] 와 같은 부류).
- Constraints: stdlib 만 쓴다. frontmatter·BOM·CRLF 처리는 같은 디렉터리의 `wiki_check.py` 를 import 해 재사용한다(파서 선례 미러링 — 두 번째 파서를 만들지 않는다). Python 3.9 이상. cwd 와 무관하게 동작한다. wiki 파일은 읽기만 한다.
- Out of scope: 임베딩·의미 검색, 검색을 자동으로 부르는 hook, frontmatter 별칭(`aliases`) 필드 도입, index 생성(#218).
- Open questions: 없음 — 이슈 #217 의 제안과 완료 기준을 따른다.
- 분할: 없음 — 스크립트와 문서 연결은 한 기능이다. 문서만 먼저 머지되면 없는 스크립트를 부르라고 적게 된다.

# Acceptance
각 항목: 무엇이 충족되나 — 어떻게 검증 — 통과 기준.

1. 단위 테스트(`skills/wiki/test_wiki_search.py`, fixture wiki — 실제 wiki 처럼 title 은 영문 stem 과 같고 한국어는 index 요약·본문에 둔다): 조사가 붙은 질의(`보관방식을`)가 index 요약에 `보관 방식` 이 든 페이지를 찾는다. `wiki_check` 가 `wiki`·`check` 로 나뉘어 맞는다. 영문·한글이 붙은 곳(`worktree에서`·`hook이`)에서 끊긴다. stem 일치 1회와 index 요약 일치 1회가 각각 같은 단어를 본문에만 6번 쓴 짧은 페이지보다 위다. BOM·CRLF 페이지를 읽고 맞은 줄 번호가 파일 기준이다. category 로 거른다. 공용과 repo wiki 가 resolve 한 경로로 같으면(심볼릭 링크 포함) 한 번만 찾는다. 모든 테스트는 시작 디렉터리·env 를 fixture 로 주입하고, 검색한 쪽수는 출력·대상·exit code 테스트가 확인한다 — Python 3.13·3.9 — 전부 통과.
2. exit code 와 대상 부재 — 단위 테스트 — 통과:
   - 결과 있음 0, 결과 없음 1(찾은 wiki 목록과 찾은 단어를 출력).
   - 2(stderr 에 이유): 찾을 wiki 가 하나도 없음, 질의에 찾을 단어가 없음(한 음절 한글·기호만), `--category` 로 거른 페이지가 0쪽(있는 category 목록을 보인다), `CLAUDE_SHARED_WIKI` 가 가리키는 곳이 없거나 wiki 가 아님, 읽기 오류(읽지 못한 하위 디렉터리 포함), argparse 사용 오류.
   - 기본 경로의 공용 wiki 가 없거나 wiki 가 아니고 repo wiki 는 있음: stderr 경고(경로·이유) + 헤더에 `공용 없음(<경로>)`, repo wiki 결과로 0 또는 1.
3. cwd 무관: `CLAUDE_SHARED_WIKI` 를 해제하고 스크립트 절대경로와 질의를 고정한 채 cwd 만 바꿔 실행한다 — 이 worktree(repo wiki 없음), 스크래치 디렉터리(repo 밖), 스크래치에 만든 임시 git repo(`wiki/` fixture 있음) — 세 곳 모두 헤더에 `~/.claude/wiki` 절대경로와 `(70쪽)` 이 보이고 공용에만 있는 페이지가 결과에 나온다. 임시 repo 에서는 repo wiki 도 헤더와 결과에 나온다.
4. 실제 공용 wiki 에서 기대 페이지가 상위 3위 안 — 실행(질의·정답은 # Progress 에 검색 전 고정):
   - 회귀 세트: 고정 질의 10개 — 9/10 이상.
   - 판별 세트: 아래 절차로 만든 증상형 질의 4개 — 3/4 이상이고, index 줄에 든 질의 토큰 개수만 세는 대조군보다 많이 맞힌다. 절차: 정렬한 stem 목록의 1·18·35·52번째 페이지를 고른다(본문에 index 줄에 없는 사실이 없으면 다음 stem). 그 페이지 본문에서 index 줄에 없는 사실 하나로 질의를 쓰고, 질의 토큰이 그 index 줄에 없음을 기계로 확인한다. 정답은 검색 전에 고정한다(같은 주제의 다른 페이지가 index 로 보이면 함께 정답).
   - 가중치·토큰화를 바꾸는 데 쓴 질의는 개발 세트로 옮기고 새 질의로 다시 잰다.
5. 속도: 실제 공용 wiki(70쪽)에서 `python3 <스크립트 절대경로> <질의>` 새 프로세스 전체 경과 5회(원시값 기록, `uv run` 포함 값은 참고) — 중앙값 0.5초 미만.
6. 문서: `skills/wiki/SKILL.md`(query 1단계·도구 목록, `${CLAUDE_SKILL_DIR}/wiki_search.py`), `skills/dlc/SKILL.md`(계획 전 결정 조회)와 `CLAUDE.md` §11(작업 시작 조회)은 `"$HOME/.claude/skills/wiki/wiki_search.py"`, README(skills/wiki 절·tree) — `rg -n wiki_search` 로 네 곳과 경로 형식 확인, dlc·§11 명령을 worktree 경로로 바꿔 다른 cwd 에서 1회 실행 — 네 곳 모두, 실행 exit 0.
7. `bash scripts/verify.sh` 마지막 줄이 main 과 같은 skip 만 둔 `ALL PASS`, `bash skills/improve/improve.sh --ci` exit 0 — 격리 runner — 통과.

# Progress
- 2026-09-30: `/wt` 로 worktree 생성(base `main@ab1a0a4`). Explore: `wiki_check.py` 의 `normalize`·`parse_frontmatter`·`body_lines`·`find_wiki`·`find_repo_root`·`read_texts` 를 재사용할 수 있다. `verify.sh` 는 추적 파일 `**/test_*.py` 를 모두 돌린다. 관련 결정: [[lesson-grep-absence-not-proof]], [[wiki-shared-layer]].
- 2026-09-30: Acceptance 4 의 대표 질의를 구현 전에 고정했다(가중치를 질의에 맞추지 않기 위해서다). dlc 조회처럼 "자산 이름 + 작업 종류"로 지었고, 기대 페이지 10개가 모두 index·pages 에 있다.
  - "CLAUDE.md 슬림화 결정" → `ops-doc-slimming`
  - "worktree 에서 git 명령이 가드에 거부됨" → `worktree-isolation-bash-guard`
  - "auto-compact 컨텍스트 비용" → `claude-code-context-cost`
  - "공용 wiki 계층 submodule" → `wiki-shared-layer`
  - "plan 핸드오프 Intent 섹션" → `plan-handoff`
  - "승인 가역성 확인 기준" → `risk-based-approval`
  - "codex 리뷰 병행" → `claude-codex-collaboration`
  - "tracked 설정에 머신 절대경로" → `lesson-tracked-config-machine-paths`
  - "grep 무매칭으로 부재 단정" → `lesson-grep-absence-not-proof`
  - "네이티브 중복 대장 재판정" → `native-overlap-ledger`
- 2026-09-30: plan 리뷰 반영 — Critical 0. 점수식을 확정했다(요약 가중 2.5, stem·title·요약은 있음/없음, 본문만 BM25). 공용 부재 정책과 테스트 주입을 정하고, Acceptance 4 에 판별 세트를 더했다. plan-reviewer 프로토타입은 옛 식으로 회귀 세트 10/10 이었지만, index·stem 토큰만 세는 대조군도 10/10 이었다.
- 2026-09-30: TDD Red(모듈 없음으로 import 실패) → 구현 → Green(3.13·3.9 18개). Acceptance 4 판별 세트를 검색 전에 고정했다. 정렬한 stem 의 1·18·35·52번째 페이지 본문에서 index 줄에 없는 사실로 질의를 썼고, 질의 토큰과 정답 index 줄의 겹침 0 을 기계로 확인했다(겹친 `상태`·`에서` 는 다른 말로 바꿨다). index 줄로 본 같은 주제의 다른 페이지는 없어 정답은 각 1쪽이다.
  - "SPA 문서를 WebFetch 로 읽으면 제목만 온다" → `ai-native-sdlc-playbook-intent`
  - "prettier 같은 hook 이 중간 단계를 고쳐 트리가 달라진다" → `commit-restructure-plumbing-cas`
  - "replace-text 로 바꾼 문자열이 REMOVED 로 남는다" → `github-sensitive-data-removal`
  - "headless 비교가 양쪽 다 만점이면 품질 차이를 말할 수 없다" → `lesson-verify-scaffold-purpose-before-removal`
- 2026-09-30: 실제 공용 wiki 측정. 가중치·토큰화는 측정 뒤 바꾸지 않았다.
  - Acceptance 4: 회귀 세트는 상위 3위 10/10(8개 1위, `ops-doc-slimming`·`plan-handoff` 2위)이고 대조군도 10/10 이다. 판별 세트는 4/4 가 모두 1위이고 대조군은 0/4 다.
  - Acceptance 3: `CLAUDE_SHARED_WIKI` 를 해제하고 worktree·스크래치·스크래치 임시 git repo(`wiki/` 1쪽)에서 실행했다. 세 곳 모두 헤더에 `공용 /Users/…/.claude/wiki (70쪽)` 이 나왔고 `wiki-shared-layer` 가 1위다. 임시 repo 는 헤더와 결과 3위에 repo wiki 가 나왔다. 모두 exit 0.
  - Acceptance 5: `python3` 직접 실행 0.056·0.055·0.055·0.056·0.056초(중앙값 0.056), `uv run` 포함 0.086초.
  - Acceptance 6: 문서 네 곳과 `docs/dlc-details.md` 가 스크립트를 가리킨다. dlc·§11 명령 형식을 worktree 경로로 바꿔 스크래치에서 실행해 exit 0 이 나왔다.
- 2026-09-30: 구현 리뷰 반영. architecture-reviewer 는 APPROVE(Minor 2), code-reviewer(Codex 병행)는 REQUEST CHANGES(Major 1·Minor 5)였다.
  - 고친 것: 읽지 못한 하위 디렉터리, 옵션 섞기, 없는 category, `~`, exit 2 문서, "cwd 무관" 범위 문구.
  - 테스트는 19개로 3.13·3.9 모두 통과했다(권한 테스트 포함). scratch 변이 14종은 전부 KILLED 다.
  - 3.9~3.12 argparse 가 섞인 파싱에서 `--` 를 거부하는 것을 버전별로 실행해 확인했고, 안내를 바꿨다.
  - 실제 wiki 에서 회귀 10/10·판별 4/4 가 유지된다. simplify 는 title 정규화 1곳이다.
- 2026-09-30: 격리 runner 결과 — verify.sh exit 0 `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 없음, 오늘 main 기록과 같다), improve --ci exit 0(error 0·warn 0). 수정 뒤 다시 잰 것:
  - Acceptance 3: 세 cwd 모두 `(70쪽)`·`wiki-shared-layer` 1위, 임시 repo 는 repo wiki 도 나온다.
  - Acceptance 5: 0.058·0.061·0.061·0.061·0.058초(중앙값 0.061), `uv run` 포함 0.090초.
  - Acceptance 6: 문서 명령 형식을 실행해 exit 0.
  - evidence gate 1~7 을 모두 증거로 충족해 판정은 DONE 이다(status 는 머지 때 done).
- 2026-09-30: `/e merge` — push 후 PR #219. 머지 뒤 main 세션에서 # Deferred 의 `/wiki ingest` 2건을 처리한다.

# Next

# Decisions
- 관련 결정을 따른다: [[lesson-grep-absence-not-proof]] — 결과 0건은 "없음"의 증거가 아니므로, 출력에 어느 wiki 를 몇 쪽 찾았는지 적고, wiki 를 못 찾은 경우(exit 2)와 결과 없음(exit 1)을 가른다. [[wiki-shared-layer]] — 두 계층을 함께 찾되 공용은 절대경로로 찾는다.
- 점수: 필드 가중 BM25(BM25F 를 단순화). 가중치는 stem·title 3, index 요약·tags 2, 본문 1. 기각: 단순 부분 문자열 개수(흔한 단어에 끌린다), 임베딩(stdlib 밖·범위 밖).
  - 아래 식으로 변경 (이유: plan-review Major 2·3 — 3/2/1 을 합쳐 포화시키면 본문 4회 반복이 제목 1회를 이겨 Acceptance 1 이 보장되지 않고, title==stem(70/70쪽)이면 제목 가중이 두 번 붙고, tags 는 0/70쪽이다).
  - `점수 = Σ_질의토큰 idf × (3·[stem·title 에 있음] + 2.5·[index 요약에 있음] + 본문 BM25)`. stem·title 과 요약은 있음/없음만 센다. 본문은 `tf·(k1+1) / (tf + k1·(1−b+b·길이/평균길이))`, k1=1.2, b=0.75 라 아무리 반복해도 2.2 를 넘지 않는다. 그래서 stem·title 일치(3)와 요약 일치(2.5)는 같은 단어의 본문 반복보다 항상 위다.
  - idf = ln(1 + (N−df+0.5)/(df+0.5)). N·df·평균길이는 이번에 찾는 페이지 전체(두 wiki 합산, category 로 거른 뒤)로 센다. 평균 본문 길이는 1 이상으로 둔다(0 나누기 방지). 질의 토큰은 중복을 뺀다. 동점은 대상 순서(공용 → repo) 다음 pages 기준 경로 순이다. tags 는 쓰지 않는다.
  - 기각: 정렬 키를 (제목·요약 일치 등급, BM25)로 나누는 방식 — 요약에 단어 하나만 맞은 페이지가 본문에서 질의 단어 여럿이 맞은 페이지보다 늘 위가 되어, Problem 이 말한 index 요약 훑기로 돌아간다.
- ⚠️ 요약 가중을 2 에서 2.5 로 올렸다 — 검색 전에 정한 가중치를 지키는 것과 "요약 일치가 본문 반복보다 위" 보장이 충돌한다 — 보장을 택했다(본문 상한 2.2 보다 커야 한다). 실제 wiki 에 돌리기 전에 정했고, 판별 세트는 아직 만들지 않았다.
- 토큰화: 영문·숫자는 소문자 단어로 나누고, `_`·`-`·`.` 가 든 식별자는 조각과 전체를 함께 넣는다. 한글은 연속 음절의 2-gram 으로 나눈다(조사가 붙어도 앞 음절 2-gram 이 맞는다). 한 음절 한글은 버린다(잡음). 기각: 형태소 분석기(stdlib 밖), 접미 조사 목록 제거(목록이 불완전하다).
  - 보강 (plan-review 11): 영문·숫자와 한글이 붙어 있으면 문자 종류가 바뀌는 곳에서 끊는다(`worktree에서` → `worktree`·`에서`). 영문 조각은 두 글자 이상만 넣는다. 한 음절 질의(`훅`·`키`)는 찾지 못한다 — 알려진 한계다. 질의가 전부 그런 단어면 exit 2 로 알린다(조용히 0건으로 끝내지 않는다).
- 재사용: `wiki_check.py` 를 import 한다. 기각: 검색 전용 파서(두 파서가 BOM·CRLF·주석을 다르게 읽으면 같은 페이지가 도구마다 달라진다 — 파서 선례 미러링).
  - 쓰는 것: `parse_frontmatter`·`body_lines`·`text_lines`·`read_texts`·`normalize`, repo wiki 는 `resolve_context(cwd, env=env).wiki_root` (arch Minor — `find_repo_root` 는 비공개 `_ceilings` 를 거쳐야 해서 직접 조합하지 않는다).
  - index 요약은 `wiki_check` 에 대응 파서가 없어 새로 읽는다. `- [[stem]] <요약>` 줄에서 링크는 `check_links.WIKILINK` 를 쓰고, 앞의 `—`·`-`·`:` 구분자를 뗀다. index 가 없거나 형식이 다르거나 등재되지 않은 페이지는 요약이 빈 값이다.
  - 링크 이름은 `wiki_check.STEM` 으로 변경 (이유: `check_links.py` 는 import 하는 순간 stdout·stderr 인코딩을 바꾼다. `wiki_check.STEM` 은 주석상 `WIKILINK` 가 읽는 이름과 같은 집합이고 이미 import 한다).
- 기본 대상: 공용 wiki 경로는 `CLAUDE_SHARED_WIKI` 가 있으면 그 값, 없으면 `~/.claude/wiki`. 테스트와 CI 는 이 변수로 fixture 를 가리킨다.
  - 보강 (arch Major 1·2, plan-review 4·5·12): 진입점은 `main(argv=None, *, env=None, cwd=None, home=None)` 이다. 테스트는 env·cwd 를 언제나 넘기고 `GIT_CEILING_DIRECTORIES` 를 fixture 루트로 둔다 — main 체크아웃(`~/.claude`)에서 돌리면 cwd 탐색이 실제 공용 clone 을 repo wiki 로 잡기 때문이다.
  - `CLAUDE_SHARED_WIKI=""` 는 설정하지 않은 것으로 본다. 값의 `~` 를 펼치고, 상대경로는 cwd 기준이다.
  - wiki 판정은 `find_wiki` 와 같다(`WIKI.md` 또는 `pages/`). 명시한 `CLAUDE_SHARED_WIKI` 가 wiki 가 아니면 설정 오류라 exit 2 다. 기본 경로가 wiki 가 아니면(이 머신에 clone 없음, #216 뒤 `raw/` 만 남은 경우 포함) 경고하고 repo wiki 로 계속한다. 찾을 wiki 가 하나도 없으면 exit 2.
  - 같은 wiki 판정은 두 경로를 `resolve()` 한 뒤 비교한다. 읽기 오류(OSError)는 조용히 건너뛰지 않고 exit 2 로 알린다.
  - 보강 (구현 리뷰): `read_texts` 의 `rglob` 이 읽지 못한 하위 디렉터리를 삼키므로 먼저 `os.walk(onerror=raise)` 로 건다. `~` 는 `expanduser` 가 아니라 주입한 home 기준으로 펼친다(`~user` 형태는 펼치지 않는다). `--category` 로 거른 페이지가 0쪽이면 exit 2 로 알린다 — 오타가 "결과 없음"(exit 1)으로 보이면 "wiki 에 없음"으로 읽힌다. 옵션은 `parse_intermixed_args` 로 질의어 사이 어디든 받는다.
- 출력 (arch Minor, plan-review 8): 첫 줄은 찾은 wiki 목록이다 — 계층·절대경로·쪽수, 없는 쪽은 이유. 결과마다 순위, `[공용]`/`[repo]`, `<category>/<stem>`(title 이 stem 과 다르면 title 도), 점수를 보인다. 이어서 Read 에 바로 넣을 절대경로, `index.md:<줄>: <요약>`, 질의 단어가 가장 많이 맞은 본문 줄 2개(`L<파일 기준 줄 번호>`)를 보인다. 기본 5개(`--limit`), `--category` 로 거른다. `__main__` 에서 stdout·stderr 를 UTF-8 로 맞춘다(`wiki_check.py` 선례 — Windows 콘솔).
- 문서의 호출 경로 (arch Minor, plan-review 10): wiki SKILL.md 는 `${CLAUDE_SKILL_DIR}/wiki_search.py`, dlc SKILL.md·CLAUDE.md §11 은 그 변수가 풀리지 않아 `"$HOME/.claude/skills/wiki/wiki_search.py"`(bash·PowerShell 둘 다 `$HOME` 을 편다).
- 커밋 단위: 1개 — 스크립트·테스트·문서가 한 기능이다.

# Key Files
- `skills/wiki/wiki_search.py` — 새 검색 스크립트
- `skills/wiki/test_wiki_search.py` — 단위 테스트(fixture wiki)
- `skills/wiki/SKILL.md` — query 1단계, 도구 목록
- `skills/dlc/SKILL.md` — 계획 전 결정 조회
- `CLAUDE.md` — §11 작업 시작 조회
- `README.md` — skills/wiki 절, tree
- `docs/dlc-details.md` — §C 1 Explore 의 wiki 조회(같은 조회를 서술해 함께 고친다)

# Blockers
없음

# Review Disposition
plan 리뷰(architecture-reviewer planning, plan-reviewer + Codex 병행) — Critical 0.
- arch Major 1 테스트 결정성(env·cwd 주입) — fix: Decisions 기본 대상 보강, Acceptance 1.
- arch Major 2 공용 부재 + repo wiki 있음 계약 — fix: Acceptance 2, Decisions 기본 대상 보강.
- arch Minor `resolve_context` 재사용 — fix. 출력의 계층·절대경로 — fix. 문서 호출 경로 — fix(Acceptance 6).
- arch Minor `CLAUDE_IMPROVE_WIKI` 와 경로 결정 중복 — defer: # Deferred.
- arch 위임 Windows 출력 인코딩 — fix: Decisions 출력.
- plan-review 1 Acceptance 4 판별력 — fix: 판별 세트·대조군·개발 세트 규칙.
- plan-review 2·3 순위 보장·점수식 미고정·title==stem·tags — fix: 점수식 확정, fixture 를 실제 형식(title==stem)과 본문 6회 반례로.
- plan-review 4·5·12 부재 정책·테스트 격리·resolve 비교 — fix.
- plan-review 6 Acceptance 3 관찰성 — fix: 헤더 쪽수·공용 전용 페이지·임시 repo.
- plan-review 7·8·9·10·11 — fix: 속도 측정 방식, 파일 기준 줄 번호, index 파서 명시, 호출 경로, 경계 토큰화 테스트와 한 음절 한계.
- ⚠️ self-flag(요약 가중 2 → 2.5) — accepted-risk: 가중치를 바꾼 이유가 평가 결과가 아니라 구조 보장이고, 실제 wiki 에 돌리기 전이다.

구현 리뷰 — architecture-reviewer(정밀) APPROVE, Critical 0·Major 0.
- arch Minor 1 `CLAUDE_SHARED_WIKI` 의 `~` 가 주입한 `home` 이 아니라 실제 HOME 으로 펼쳐진다 — fix: `~` 로 시작하면 `home` 기준으로 펼치고 테스트 1줄.
- arch Minor 2 `docs/dlc-details.md` 가 exit 2 를 "wiki 없음 → skip" 하나로 적어 설정·읽기 오류도 조용히 건너뛰게 한다 — fix: exit 2 는 stderr 이유를 보고 wiki 없음만 skip. 문서 4곳의 "두 wiki 를 cwd 와 무관하게" 는 공용만 cwd 무관·repo 는 cwd 에서 위로 찾는다로 바로잡는다.
- arch 위임(simplify) `Page`·`load_pages` 이름이 `wiki_check` 와 같다 — wontfix: 모듈로 구분돼 충돌이 없고, `wiki_check.load_pages` 는 frontmatter 만 엄격한 UTF-8 로 읽는 schema 용이라 재사용 대상이 아니다(검색은 `read_texts` 처럼 깨진 바이트를 바꿔 읽는다).

구현 리뷰 — code-reviewer(Codex 병행) REQUEST CHANGES, Critical 0·Major 1·Minor 5, refuted 3.
- Major 읽지 못한 하위 디렉터리를 `read_texts` 의 `rglob` 이 조용히 건너뛰어 exit 2 대신 페이지가 빠진 결과가 난다 — fix: `os.walk(onerror=raise)` 로 먼저 걸어 OSError 로 드러낸다. 권한 000 재현 테스트 추가(root·Windows 는 skip). `wiki_check` 쪽 같은 결함은 # Deferred.
- Minor dlc-details 의 exit 2 → skip — fix(arch Minor 2 와 같음).
- Minor 질의어 사이의 옵션이 exit 2 — fix: `parse_intermixed_args`. `-` 로 시작하는 단어의 `--` 안내는 3.9~3.12 argparse 가 섞인 파싱에서 `--` 를 거부해(3.13+ 는 받는다, 실행 확인) "앞의 `-` 를 떼고 넣는다"로 바꿨다 — 토큰이 영문·숫자부터라 결과가 같다.
- Minor 없는 category(오타)가 exit 1 — fix: 거른 뒤 0쪽이면 있는 category 목록과 함께 exit 2, 결과 없음 줄에 거른 쪽수를 적는다.
- Minor `~` 가 주입한 home 을 쓰지 않음 — fix(arch Minor 1 과 같음).
- Minor 테스트가 보장을 가르지 못함(가중치 3→1·2.5→1.8, resolve 생략, 빈 env, `~`, `--limit` 변이 생존) — fix: H1 없는 stem 페이지, 본문 200회 반복 페이지(BM25 가 상한 2.2 근처), `..` 가 든 공용 경로, 빈 env 값, `~`·`--limit 0`·없는 category·옵션 섞기 테스트. 변이 14종 전부 KILLED(가중치 2.0 포함).
- Minor Acceptance 1 의 "모든 테스트가 쪽수를 확인" 문구 — fix: plan 이 낡았다. 격리는 env·cwd 주입이 보장하고, 쪽수는 출력·대상·exit code 테스트가 확인한다고 고쳤다.
- Nit(Codex) `max(avg, 1)` 과 plan 의 "0 이면 1" — fix: plan 문구를 코드에 맞췄다.
- 재리뷰는 생략했다 — 수정이 지적 그대로이고 변이 검사로 확인했다. 사용자가 리뷰 반복을 줄이라고 했다.

# Deferred
- `~/.claude main 세션에서 /wiki ingest` 두 가지를 적립한다. 출처는 모두 공개다.
  - wiki_search 설계 결정: 점수식(stem·title 3·요약 2.5 는 있음/없음, 본문 BM25 는 상한 2.2 — 필드 일치가 본문 반복보다 늘 위), 공용 부재 정책, 판별 세트 만드는 법(index 어휘로 쓴 질의는 기존 방식도 맞힌다).
  - Python 실측: argparse `parse_intermixed_args` 는 3.9~3.12 에서 `--` 뒤의 `-` 인자를 거부하고 3.13+ 는 받는다. `Path.rglob` 은 읽지 못한 하위 디렉터리를 조용히 건너뛴다(3.9·3.13).
  - 근거는 이 PR 의 코드·테스트와 로컬 버전별 실행이다.
- `wiki_check.read_texts` 의 `Path.rglob` 이 읽지 못한 하위 디렉터리를 조용히 건너뛴다 — `smoke` 가 그 안의 페이지를 "파일 없음"으로, `forbid` 는 검사 없이 통과로 본다. wiki_search 는 호출 전에 `os.walk(onerror=raise)` 로 막았다 — Minor, `skills/wiki/wiki_check.py:1468`.
- `skills/improve/improve.sh` 6번 검사가 `CLAUDE_SHARED_WIKI` 를 먼저 읽게 통일(지금은 `CLAUDE_IMPROVE_WIKI` 만 본다 — clone 위치를 옮기면 변수 둘을 따로 바꿔야 한다) — Minor, `skills/improve/improve.sh:98`.
