---
title: repo-context-kit — consumer repo 마다 LLM 이 코드를 이해할 맥락을 세우고 코드와 어긋나지 않게 유지하는 공용 킷
status: open
started: 2026-09-29
updated: 2026-09-30
---

# Problem

`~/.claude` 를 받아 쓰는 repo 에서 세션은 매번 코드를 처음 본다. 이 repo 가 주는 공용 장치는 wiki 운영 절차(`skills/wiki` 의 ingest·query·lint)와 링크 점검(`check_links.py`)뿐이다. repo 마다 필요한 맥락 — 지켜야 할 결정·불변식·교훈, 검증 명령, 경로별 주의 — 을 세우는 수단과, 그 맥락이 **코드와 어긋나지 않게 유지하는** 수단이 없다.

그래서 consumer repo 두 곳이 같은 종류의 장치를 각자 만들었다. 회사 repo 는 페이지가 감시할 코드 경로(`covers`)와 마지막으로 대조한 commit(`verified_at`)을 frontmatter 에 두고, Stop hook 으로 같은 브랜치 안의 페이지 갱신을 강제한다. coin-trading-bot 은 frontmatter 형식 검사(`wiki/verify.sh`)와 대표 질문 검사(`wiki/smoke.sh`)를 만들었다. 공용화되지 않은 장치는 repo 마다 다시 만들어지고, 결함도 따로 고쳐진다.

2026-09-29 조사(세션 transcript 표본 — 표본 수치다)에서 코드 탐색 도구의 결과가 도구 결과 문자 수의 48–72% 였다. 세션이 맥락 없이 매번 코드를 다시 읽는다. 과거에 들인 장치 둘은 쓰이지 않았다. 코드 그래프 색인은 보존된 로그 기간(2026-08-06 ~ 09-15) 안에서 성공 호출 0회로 은퇴했다(공용 wiki `codegraph`). Pyright LSP plugin 은 2026-07-26 lifetime 사용 0 으로 한 번 꺼졌다(README `enabledPlugins` 항목). 같은 표본의 LSP 호출 0건은, 표본 기간에 plugin 이 켜져 있었는지 확인하지 않아 사용 여부의 근거로 쓰지 않는다.

# Proposed outcome

consumer repo 가 한 번의 초기화로 맥락 킷을 세우고, 킷이 코드와 어긋나면 기계가 알린다. 킷은 네 층이다.

1. **상시** — 세션 시작에 로드되는 짧은 진입 문서: 빌드·검증 명령, 금지 사항, 무엇을 어디서 찾는지. 공식 권장 크기는 파일당 200줄 미만이다(memory 문서 "target under 200 lines per CLAUDE.md file").
2. **경로 한정** — 해당 파일을 읽을 때만 로드되는 규칙(`.claude/rules` 의 `paths:` — memory 문서 "Path-scoped rules trigger when Claude reads files matching the pattern"). wiki 의 `covers` 에서 만든다.
3. **요청 시** — repo wiki(결정·교훈·불변식). 형식·`covers` 신선도·대표 질문 검사로 유지한다.
4. **피드백** — 편집 직후 틀린 것과 함께 봐야 할 것을 알게 한다: 검증 명령, LSP 진단, 함께 바뀌어 온 파일(git 이력).

공용 `~/.claude` 에는 메커니즘(스크립트·템플릿·스킬)만 두고, 내용은 각 repo 에 둔다.

# Constraints

- 공개 repo 다. 회사 repo 의 내용·이름·경로는 가져오지 않는다. 장치의 메커니즘만 일반화하고 예시는 일반 경로로 새로 쓴다(CLAUDE.md §11 공개 점검). 회사 repo 와의 대조 실행 결과는 수치만 적는다.
- 이 묶음의 plan 은 consumer repo 파일을 고치지 않는다. 적용·이관은 그 repo 세션의 일이고, 여기서는 read-only 대조 실행만 한다.
- 기존 호출과 호환을 유지한다. consumer repo 문서가 `~/.claude/skills/wiki/check_links.py` 를 지금 경로·인자로 부르므로, 그 호출 계약(경로·인자·출력 형식·exit code 의 의미)을 바꾸지 않는다. 판정을 정확하게 하는 수정(예: 별칭 링크 인식 — check-links-alias)은 계약 변경이 아니다.
- 스크립트는 stdlib 만 쓰고 `uv run --no-project python <script>` 로 돈다(`check_links.py` 와 같은 실행 방식). 파일 하나만 복사해도 동작해야 한다 — Open questions 의 배포 형태가 vendoring 으로 정해져도 막히지 않게.
  - 예외: `wiki_search.py` 는 frontmatter·본문 파서를 두 벌로 두지 않으려고 `wiki_check.py` 를 import 한다(#219). vendoring 할 때는 두 파일을 함께 옮긴다.
- Stop hook 모드는 fail-open 이다(도구 오류로 세션을 막지 않는다). 다만 도구 실패는 사용자에게 보이게 알린다 — 조용히 넘기면 config 오타나 Python 버전 문제로 게이트가 꺼져도 아무도 모른다. 보고·CI 모드는 fail-closed 다(검사할 수 없는 상태를 통과로 보고하지 않는다).
- 실행해 볼 수 없는 플랫폼(Windows)의 동작에는 추정 스위치를 넣지 않고 미검증으로 적는다.
- 전역 등록은 머지로 전달되지 않는다. `settings.json` 은 추적하지 않고(`.gitignore`, `README.md:7`) bootstrap 은 rtk hook 만 등록한다(`scripts/bootstrap/README.md` settings.json 행). hook·plugin 을 켜는 단위는 머신마다 할 절차를 문서로 내고, 켜기 전 상태에서도 문서끼리 모순되지 않게 한다.
- 쓰이지 않아 걷어낸 장치(코드 그래프 색인, LSP plugin)를 되살리는 단위는 착수 전에 0회의 원인을 밝히거나 context-eval 로 필요를 보인다. 새 장치를 더하는 단위는 plan 에 사용 여부를 잴 방법(transcript 집계 등)을 적는다. 쓰이지 않는 장치가 매 세션 지침 토큰만 드는 일을 되풀이하지 않기 위해서다(공용 wiki `codegraph`).

# Out of scope

- 코드 그래프·임베딩 색인 재도입 — 이 묶음의 단위로 두지 않는다. 은퇴 결정(공용 wiki `codegraph`)이 인덱스 재생성 후 유지안을 "코드 repo 에서 값을 한다는 증거 0" 으로 기각했다. 되살리려면 Constraints 의 조건을 채운 뒤 새 묶음으로 한다.
- 코드 의미 문서(파일·함수별 요약)의 생성·유지 — 코드 옆 주석·docstring 의 몫이다. wiki 는 결정·교훈·불변식만 둔다.

# Open questions

- (열림) 배포 형태 — consumer repo 가 `~/.claude/skills/wiki/*.py` 를 직접 부르나, repo 안에 복사(vendoring)하나. consumer repo 의 CI 에는 `~/.claude` 가 없어 직접 호출이 불가능하다. — 결정: wiki-init 착수 전.
- (열림) 정본 파일 — 상시 진입 문서를 무엇으로 두나. Claude Code v2.1.277+ 는 CLAUDE.md 가 없으면 AGENTS.md 를 직접 읽고, 둘 다 있으면 CLAUDE.md 만 읽는다. CLAUDE.md 가 `@AGENTS.md` 로 import 하거나 AGENTS.md 로 심링크하면 한 번만 읽는다(공용 wiki `claude-code-agents-md-loading`). 이 repo 의 선례는 Codex 용 `~/.codex/AGENTS.md` 를 CLAUDE.md 심링크로 둔 것이다(2026-06-10 결정, 2026-09-25 복원). Windows 에서의 심링크 동작은 미검증. — 결정: repo-init 착수 전.
- (열림) pilot repo — 킷을 처음 적용할 consumer repo. 적용 자체는 그 repo 세션의 일이다(Constraints). — 결정: context-eval 착수 전.
- (열림) eval 예산 — context-eval 의 규모와 비용 상한. — 결정: context-eval 착수 전.
- (열림) 게이트 등록 위치 — `stale --stop-hook` 을 전역 `~/.claude/settings.json` 에 두나(머신마다 손으로 등록, 모든 repo 에서 돌고 wiki·`covers` 가 없으면 무동작 — wiki 경로·`--config` 를 넘기지 않을 때만. 넘기면 그 경로가 없는 repo 마다 매 턴 `systemMessage` 가 뜬다), consumer repo 의 project settings 에 두나(opt-in, 그 repo 세션이 등록한다). 자체 게이트가 이미 있는 repo 에서 전역 등록이 겹치면 같은 변경을 두 번 알린다 — 첫 단위의 config `[stale] stop_hook = false` 로 끌 수 있다. — 결정: wiki-init 착수 전.
- (열림) path-scoped-context 의 전달 방식. 두 안이 있다(#220).
  - B: `covers` 에서 `.claude/rules` 의 `paths:` 규칙을 생성한다.
  - C: PostToolUse(Read) hook 이 wiki-covers-query 의 조회 결과를 `additionalContext` 로 넣는다.

  비교 항목:
  - Read 트리거와 compaction 뒤 유지: B 는 다시 Read 하면 재로드되고, C 의 hook 주입분은 요약된다. 공식 문서(context-window 의 "what survives compaction") 기준이고, 로컬에서는 재현하지 않았다.
  - 관리 비용: B 는 생성 파일을 관리해야 하고, C 는 자작 hook 을 유지해야 한다.
  - 등록 비용: C 는 hook 등록이 필요한데 `settings.json` 은 머지로 전달되지 않는다(Constraints). B 는 생성 파일을 consumer repo 에 커밋해야 한다.
  - Read 한 번마다 드는 비용: C 는 hook 프로세스 실행 지연과 반복 주입 토큰이 든다. B 는 규칙 로드 토큰이 든다.
  - 사용 측정 방법(Constraints 마지막 항목).
  - Edit·Write 가 규칙을 트리거하는지: 공식 문서에 없고, anthropics/claude-code 이슈 #38487·#88565 가 상충한다. 로컬 재현이 필요하다.

  결정: wiki-covers-query 착수 전. C 로 정하면 covers 조회의 출력 계약과 지연 예산을 그 단위에서 함께 정해야 해서, path-scoped-context 착수 전으로는 늦다.
- (열림) 공용 wiki 페이지가 `~/.claude` 코드를 `covers` 로 가리키는 방법.
  - `covers` 는 페이지가 속한 git 최상위 기준이다(`wiki_check.py` 의 `covers_match` — covers 문법의 유일한 정의).
  - 공용 wiki 는 별도 clone(#216)이라 git 최상위가 `~/.claude/wiki` 이고, `~/.claude` 코드를 가리킬 수 없다(공용 wiki `wiki-shared-layer` 한계). 지금 공용 wiki 에 covers 페이지는 0개다.
  - 선택지 1: 비대상으로 유지한다. `~/.claude` 코드의 결정은 코드 옆 주석과 커밋에 둔다.
  - 선택지 2: 기준 repo 를 명시하는 키를 두고 `wiki_check`·`wiki_search` 가 함께 따르게 한다.
  - 결정: wiki-covers-query 착수 전.
- (열림) wiki-graph-search 사용 측정 — 머지 뒤 2주(2026-10-14 무렵부터) transcript 로 잰다. 제외·중복 제거·신호·임계값은 그 plan 의 `# Decisions` 에 있다. 처분: 측정 결과를 적고, 임계값 미만이면 문서 안내를 고치거나 되돌림을 검토한다.
- (열림) 후순위 후보(용어집, repo 전용 skill, 외부 사실 자동 생성)를 이 묶음에 넣을지. — 결정: context-eval 결과를 본 뒤. 빈틈이 보이면 새 단위, 아니면 이월하거나 Out of scope 로 옮긴다.

# Plans

- `plans/2026-09-29-wiki-freshness-gate/wiki-freshness-gate-plan.md` — 첫 단위. frontmatter 형식 검사, `covers` 신선도 검사(보고·브랜치·Stop hook 모드), 대표 질문 검사를 `skills/wiki/wiki_check.py` 로 일반화한다. 설정 템플릿과 `covers`·`verified_at` 규약의 정본 문서(`skills/wiki/SKILL.md`)를 둔다. 대표 질문 형식(`[[smoke.questions]]`)의 정본이다. 등록(hook·CI)은 하지 않는다.
- wiki-init (미착수) — `/wiki init`: consumer repo 에 wiki 뼈대(WIKI.md·index·log 템플릿과 검사 config)를 만들고, 첫 단위의 검사를 등록하는 절차(Stop hook·CI 예시)를 낸다. WIKI.md 템플릿은 `covers` 규약을 다시 쓰지 않고 SKILL.md 를 가리킨다. consumer 파일을 쓰는 새 명령이라 structural 후보이고 규모는 착수 때 판정한다. 선행: wiki-freshness-gate. 배포 형태·게이트 등록 위치가 정해져야 한다. 등록 전에 확인할 항목(스크립트 부재 guard, CI `fetch-depth`, 인터프리터 고정, 다른 Stop hook 과의 출력 합쳐짐, vendoring 버전 차이)은 첫 단위 plan 의 `# Deferred` 에 있다.
- repo-init (미착수) — `/repo-init` 과 점검(`check`): 상시 진입 문서, 검증 명령 식별, 킷 상태 점검. `check` 는 그 시점에 머지된 층만 보고, 뒤 단위가 자기 층의 점검 항목을 더한다. 정본이 AGENTS.md 로 정해지면 전역 CLAUDE.md §3-1 의 "per-repo CLAUDE.md" 문구를 같은 plan 에서 맞춘다. 정본 파일이 정해져야 한다.
- lsp-first (미착수) — 탐색에서 LSP 진단·심볼 조회를 먼저 쓰게 한다(plugin 활성, 언어 서버 설치 점검). 이력: 2026-07-26 lifetime 사용 0 으로 끔 → 2026-09-03 되돌림 → 2026-09-26 바이너리 없음으로 끔(사용자 결정) → 2026-09-28 `/doctor` 로 제거. 착수 전에 0회의 원인을 밝히거나 context-eval 로 필요를 보인다(Constraints). plugin 활성은 `settings.json` 이라 머지로 전달되지 않는다. README `enabledPlugins` 서술 drift 는 `plans/2026-09-28-push-colon-delete-hook` 의 `# Deferred` 에 있다.
- context-eval (미착수) — 맥락이 실제로 도움이 되는지 LLM 응답으로 잰다. 첫 단위의 `[[smoke.questions]]` 를 질문 세트로 재사용하고 과거 작업 replay 를 더한다. 킷 없는 기준선을 먼저 잰다. pilot repo 와 eval 예산이 정해져야 한다.
- path-scoped-context (미착수) — 해당 파일을 읽을 때만 관련 결정을 로드한다. 전달 방식(B: `covers` 에서 `.claude/rules` 의 `paths:` 규칙 생성 / C: Read 시점 hook 주입, #220)은 Open question 이다.
  - B 로 가면 두 가지를 함께 한다. `covers` 는 fnmatch(`*` 가 `/` 를 넘는다)이고 `paths:` 는 glob 이라 변환 규칙이 필요하다. 생성한 규칙이 `covers` 와 어긋나는지 보는 검사도 이 단위가 가진다.
  - 선행: wiki-freshness-gate(`covers` 형식). C 로 가면 wiki-covers-query 도 선행이다.
- git-impact (미착수) — git 이력에서 함께 바뀌어 온 파일을 뽑아 변경 영향 범위를 제시한다(피드백 층).
- `plans/2026-09-30-wiki-graph-search/wiki-graph-search-plan.md` — #221 첫 단위, "요청 시" 층. 규모는 medium.
  - `wiki_search.py` 가 wiki 를 섹션 트리·`[[링크]]`(별칭 포함)·`[!open]`/`[!conflict]` 구조로 읽는다.
  - 결과에 섹션 위치와 관련 페이지를 붙이고, `--links-to`·`--open` 질의를 둔다.
- wiki-covers-query (미착수) — #221 둘째 단위. 규모는 착수 때 판정한다(예비값 medium).
  - covers 간선을 두고 `--covers <파일>` 질의(그 파일에 걸린 결정)를 둔다.
  - covers 가 가리키는 파일이 없는 경우는 새로 판정하지 않는다. `wiki_check.py` 의 판정("covers 매칭 0건")을 재사용해 질의 출력에 표시만 한다.
  - 공용 wiki 의 covers 기준은 Open question 이다.
  - 쓰는 곳: CLI, 그리고 C 안이면 path-scoped-context·#220.
  - 선행: wiki-graph-search.
- wiki-multi-search (미착수) — #221 셋째 단위. 규모는 착수 때 판정한다(예비값 medium).
  - 머신 로컬 목록(추적하지 않는 파일)으로 여러 repo wiki 를 함께 검색한다. 결과마다 출처를 표시한다.
  - 공개 경계는 fail-closed 다. 공개 repo 세션, 판정할 수 없는 세션, 공개 여부 표시가 없는 wiki 는 모두 비공개 wiki 를 빼는 쪽으로 다룬다.
  - 선행: wiki-graph-search. 같은 파일을 고치고, 질의 모드가 wiki 여러 개에서 어떻게 동작할지 정해야 한다(stem 겹침, 링크는 같은 wiki 안에서만).
  - 기각: 여러 repo wiki 를 한 repo(공용 clone)로 모으기. 2026-09-30 사용자 질문으로 다시 검토했고, 공용 wiki `wiki-shared-layer` 의 기각 절 사유가 그대로다.
    - 공개 범위가 섞인다.
    - 같은 브랜치 갱신과 covers 신선도 검사가 멈춘다.
    - `[[링크]]` 이름 공간이 겹친다.
    - consumer repo 의 CI 와 다른 사람은 `~/.claude` 아래를 볼 수 없다.
  - 사용자 목적은 "한 곳에서 보고 검색하기"로 확인했다.
- `plans/2026-09-30-check-links-alias/check-links-alias-plan.md` — wiki-graph-search # Deferred 후속, 규모 small. `check_links.py` 가 별칭 링크 `[[a|b]]` 도 링크로 읽는다. 호출 계약은 그대로이고 판정만 정확해진다(Constraints 첫째 항목의 문구를 이때 분명히 했다).
