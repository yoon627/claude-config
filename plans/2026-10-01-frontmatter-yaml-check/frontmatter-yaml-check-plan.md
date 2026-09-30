---
title: frontmatter-yaml-check — skill·agent frontmatter 를 모든 소비자가 같게 읽는 한 줄 형식으로 검사해 로컬 verify·CI 에서 실패시킨다
status: done
started: 2026-10-01
updated: 2026-10-01
---

# Goal
git 이 아는 `skills/*/SKILL.md`·`agents/*.md` 의 frontmatter 가 모든 소비자(Claude Code·YAML 파서·`sync_codex_agents.py`)에서 같게 읽히는 한 줄 `key: 값` 형식이 아니거나 `name`·`description` 이 비면 `bash scripts/verify.sh`(로컬·CI)와 `bash skills/improve/improve.sh --ci`(CI)가 실패한다.

# Intent
- Problem: `/doctor`(2026-10-01)가 `skills/c/SKILL.md` description 평문 값 안의 `: ` 를 YAML 파싱 실패로 보고했고 `0efce86` 에서 고쳤다. 그 뒤 확인한 사실:
  - Claude Code 2.1.285 는 엄격 파싱(`Bun.YAML.parse`)이 실패하면 특수문자·`: ` 가 든 값을 큰따옴표로 감싸 다시 파싱한다(plan-reviewer 가 번들 코드에서 확인). `claude plugin validate` 는 `: ` 형식을 보고하지 않고, fallback 이 못 살리는 형식(닫히지 않은 따옴표·탭 들여쓰기)만 "all frontmatter fields silently dropped" 로 보고한다(2026-10-01 실측, skill·agent, 세 레이아웃). 옛 `/c` 를 validate 로 재면 LF 파일은 보고가 없고(fallback 이 살린다), CRLF 파일은 skill·agent 모두 "failed to parse … all frontmatter fields silently dropped" 다 — fallback 정규식이 `\r` 을 넘지 못한다(2026-10-01 실측). 그래서 `0efce86` 커밋 메시지의 "필드가 전부 버려졌다"는 Windows(`* text=auto` → CRLF) checkout 에서만 맞고, 이 Mac(LF)에서는 틀리다. 앞선 세션 보고의 "수정 뒤 skill 목록이 바뀐 것" 은 새 frontmatter 가 읽힌다는 증거일 뿐 이전 결함의 증거가 아니었다.
  - 그래도 검사가 필요한 이유:
    - (a) fallback 이 못 살리는 형식은 필드가 전부 사라지고, `.claude/agents` 의 agent 는 로드되지 않는다(validate 문구).
    - (b) 어느 경로도 보고하지 않는 값 변형이 있다 — 평문 값 안 ` #` 는 YAML 주석이라 잘리고, Claude Code 의 추출 정규식은 닫는 `---` 를 줄 시작에 고정하지 않아 값 안의 `---` 에서 frontmatter 가 끝난다(번들 판독, validate 재현 — `name: n---x` 가 "No description in frontmatter").
    - (c) 엄격한 소비자가 있다 — `scripts/bootstrap/sync_codex_agents.py` 는 agents 의 모든 줄이 한 줄 `key: 비지 않은 값` 이어야 하고 따옴표를 unescape 하지 않는다. Codex 가 링크해 쓰는 skill 7종의 파서는 모른다(❌).
  - CI 가 돌리는 `improve.sh` 점검 4 는 `^name:` 줄만 grep 하고, `verify.sh` 에는 frontmatter 검사가 없다.
- Constraints:
  - 새 의존성 없이(CLAUDE.md §6) — CI 는 system python3 와 node 만 쓰고 두 표준 라이브러리에 YAML 파서가 없다. 파서 선택·배치·테스트·README 는 dlc 에서 정한다(사용자 위임, 2026-10-01).
  - 로컬 `bash scripts/verify.sh` 와 CI 가 같은 검사를 돈다. trivial·small 은 PR·CI 없이 로컬 ff-merge 되므로 로컬 verify 에서 잡혀야 한다.
  - 대상 발견은 verify.sh `repo_files` 와 같은 git 발견 — main checkout 의 gitignored 외부 skill(`skills/orca-cli` 는 `description: >-`)을 끌어오지 않는다.
  - Windows checkout 은 `.gitattributes` `* text=auto` 로 CRLF 일 수 있고, PowerShell 5.1 은 BOM 을 쓴다 — 둘 다 통과시킨다(아는 소비자가 모두 벗긴다).
  - 선례 `scripts/plan-lint.js` 의 모양(순수 판정 함수 + CLI)을 따르되, 출력은 `<파일>:<줄>: <메시지>` 이고 읽기 실패도 위반이다.
- Out of scope:
  - `name` 의 YAML 1.2 숫자·불리언을 뺀 타입 해석 차이(`yes`·`1:20`·`0b101` 등 — PyYAML 은 다른 타입으로 읽고 Claude Code·sync 는 문자열)와 밑줄 숫자 형태(`0x_`·`._` — PyYAML·ruamel 이 실패한다). 비현실적인 값이라 null 형태(`~`·`null`)만 모든 키에서 막는다.
  - `name` 과 디렉터리·파일 이름 일치, `sync_codex_agents` 의 name 문자 규칙(`test_sync_codex_agents.py` 가 실제 agents 로 CI 에서 본다), `tools`·`model` 의미 검사.
  - 다른 frontmatter(plan 은 plan-lint.js, wiki 는 wiki_check.py)와 gitignored 머신 로컬 skill(`skills/orca-cli`·`skills/synced/`)·다른 repo 의 skill.
- Open questions:
  - (열림) Codex 가 `~/.agents/skills` 로 읽는 skill 7종의 frontmatter 파서 엄격성·BOM 처리 — 한 줄 형식이면 어느 파서든 읽을 것으로 보고 조사하지 않는다(❌).
  - (해소) main checkout 에 `.gitignore` 에 없는 외부 skill 이 생기면 verify·`/improve` 가 실패한다 — verify.sh 가 아직 add 하지 않은 새 파일도 검사 대상으로 보는 것과 같은 규칙이라 의도대로 둔다(무시할 파일이면 `.gitignore` 에 넣는다). code-review open question, 2026-10-01.
- 분할: 없음 — 검사기, 연결(verify.sh·improve.sh), 문서는 한 머지에서만 유효하다. 검사기만 먼저 머지하면 CI 가 여전히 못 잡고, 연결은 검사기 없이 만들 수 없다.

# Acceptance
1. 옛 `/c` description(`0efce86^`)을 담은 파일에 `node scripts/frontmatter-lint.js <파일>` 이 exit 1 과 `<파일>:3: …` 한 줄을 낸다. 검증: 테스트 + 수동 실행.
2. 현재 skill 9개·agent 4개가 모두 통과한다. 검증: `bash scripts/verify.sh syntax` 의 frontmatter 줄 13개가 `ok`.
3. 되돌림 실험: `skills/c/SKILL.md` 에 옛 `: ` 를 임시로 되살리면 `bash scripts/verify.sh syntax` 가 FAIL·exit 1, `bash skills/improve/improve.sh --ci` 가 `[error]`·비0 exit. Edit 로 원복하고 `git diff --quiet -- skills/c/SKILL.md` 가 0 이면 둘 다 다시 통과한다.
4. 발견 범위: worktree 에 ignored `skills/orca-cli/SKILL.md`(`description: >-`)를 임시로 두어도 두 명령이 그 파일을 보지 않고 통과한다(뒤에 지운다). 대상이 0개인 repo(scratch 사본)에서는 두 명령 모두 실패한다.
5. 건전성(scratch 대조 스크립트, 로컬): 검사기가 통과시킨 모든 경우 — 현재 13개와 그 CRLF·BOM 변형, 테스트 fixture, 위험 문자 무작위 4000건 이상 — 에서
   - Claude Code 추출 정규식(`^---\s*\n([\s\S]*?)---\s*\n?`)으로 뽑은 본문을 PyYAML·ruamel(YAML 1.2)이 오류 없이 읽고, 문자열 값이 `lintFrontmatter().fields` 와 같다(타입이 바뀐 값은 따로 센다).
   - `sync_codex_agents.parse_frontmatter` 가 받아들이고 값이 같다.
   - `claude plugin validate` 가 오류도 "No frontmatter" 경고도 내지 않는다(대조군 2건은 보고돼야 한다).
   - 모든 경우에서 CLI(파일 디코딩·BOM 경로)의 판정이 순수 함수와 같다.
   불일치 0건. 이 대조는 표본의 성질이다 — Bun.YAML 이 읽는 값 자체(validate 는 오류만 낸다)와 과잉 거부는 재지 않는다.
6. 테스트 `scripts/frontmatter-lint.test.js` 가 거부 형식(평문 값 안 `: `·끝 `:`·` #`·앞뒤 NBSP·U+3000, 따옴표 밖 첫 글자 지시자 표, `- ` 로 시작·`-`·`?`·`:` 단독, 닫는 `---` 뒤 줄바꿈 없음, `name` 의 숫자·불리언, U+0080·U+009F·U+FFFE·U+FFFF·서로게이트, 닫히지 않은 따옴표·따옴표 뒤 글자·따옴표 안 자기 따옴표와 `\`, 값 안 `---`, 금지 문자 — 탭·제어문자·NEL·U+2028·lone CR, 빈 줄·주석·목록·여러 줄 값, 빈 값, 중복 키, YAML 1.1 불리언 키, `key:값`, frontmatter 없음·닫힘 없음, `name`·`description` 누락·빈 값·`~`·`null`, 특수 태그 값 `=`·`<<`, 날짜 형태 값)와 허용 형식(평문, `'…'`·`"…"`(안에 `: ` 포함), `-x`·`:x` 로 시작하는 평문, camelCase 키, CRLF, BOM — 허용은 `fields` 값까지)과 CLI 계약(통과 exit 0 무출력, 위반·읽기 실패·잘못된 UTF-8 은 exit 1 과 `<파일>:<줄>: …`, 인자 0개 exit 2, BOM 하나는 통과·둘은 위반)을 잠근다.
7. 문서: README 의 improve.sh 점검 목록·scripts 절·verify.sh 절, `skills/improve/SKILL.md` 1단계 `[error]` 설명, `verify.sh` 머리 주석과 syntax 헤더, `lint.yml` 점검 주석이 새 검사를 적는다. 허용 형식 목록은 `frontmatter-lint.js` 머리 주석과 README scripts 절에만 둔다.
8. `bash scripts/verify.sh` 전체가 `ALL PASS` — skip 이 있으면 이번 변경과 무관한 것만.

# Progress
- 2026-10-01 착수. base 는 로컬 `main@0efce86`(origin/main 보다 1커밋 앞 — `/c` 수정이 있어야 새 검사가 통과한다). Explore: verify.sh 축·lint.yml·plan-lint 선례·improve 점검 4·현재 frontmatter(13개 모두 한 줄 평문). plan-reviewer(CONDITIONAL)·architecture-reviewer(REQUEST CHANGES) 반영 — 형식을 한 줄 문법으로 좁히고 소비자·발견 규칙·반환 형태·건전성 대조를 다시 정했다. `claude plugin validate` fallback 실측(아래 Decisions).
- 2026-10-01 구현. TDD Red(검사기 없음 → `MODULE_NOT_FOUND`) → Green(59 PASS). 건전성 대조 1차에서 `=` 8건 불일치 → `=`·`<<`·날짜 규칙 추가(Red 2건 → Green) → 2차 5539건 중 통과 1629건 불일치 0, 타입만 바뀐 값 64건(감수 범위), validate 대조군 2/2 보고(레이아웃 실제 검사 확인). 그 뒤 verify.sh syntax 축·improve.sh 점검 4 연결과 문서. Acceptance 2(13개 ok)·3(되살리면 두 명령 exit 1, Edit 원복 뒤 `git diff --quiet` 0·재통과)·4(ignored orca-cli 무시, 대상 0개 scratch repo 에서 두 명령 exit 1) 관찰.
- 2026-10-01 리뷰 1회차 반영. architecture-reviewer(정밀) APPROVE(Minor 3), code-reviewer REQUEST CHANGES(Major 2). validate 로 직접 잼: 옛 `/c` 는 LF 보고 없음·CRLF 필드 유실, name 은 YAML 1.2 숫자·불리언이면 "name must be a string". 테스트 추가 → Red 9건 → 수정 → Green 72 PASS(대문자 키 거부 단언 1건은 camelCase 허용 결정에 맞춰 "영문자로 시작하지 않는 키" 거부로 바꿨다). 하네스 보강(CLI 판정 대조·validate 경고·이름·camelCase 키·밑줄·NBSP·U+FFFE·파일 끝 `---`) 뒤 5552건 중 통과 869건 불일치 0, 타입만 바뀐 값 167건, 밑줄 실패 0건, 대조군 2/2. simplify 체크: 키 정규식을 `KEY` 하나로 합친 것 말고 걷어낼 것 없음.

- 2026-10-01 최종 검증(격리 runner): `bash scripts/verify.sh` exit 0, `ALL PASS (skip: install-codex-skill.test.ps1)`(PowerShell 미설치 — 이번 변경과 무관), frontmatter 13개 ok. code-reviewer 2회차 APPROVE → Minor·Nit 반영(Red 1 → Green 72) 뒤 메인이 전체 재검증.

- 2026-10-01 전체 `bash scripts/verify.sh` 재확인(exit 0, 무관한 PowerShell skip 1건) → evidence gate DONE → 커밋 → commit-check 이상 없음 → `/e merge` PR #226.

# Next

# Decisions
- 계획 전 wiki 조회(`verify.sh improve frontmatter 검사`): 걸린 decision·lesson 없음 — 새로 정한다.
- 소비자(검사 기준): Claude Code(추출 정규식 `^---\s*\n([\s\S]*?)---\s*\n?`, BOM 하나 제거, `Bun.YAML.parse` → 실패 시 따옴표 fallback — CRLF 에서는 fallback 도 실패 — 끝내 실패하면 필드 유실, name 이 문자열이 아니면 오류), YAML 파서 일반(PyYAML 1.1·ruamel 1.2 로 대조), `scripts/bootstrap/sync_codex_agents.py`(agents — 모든 줄 한 줄 `key: 비지 않은 값`, 값은 `strip()`, 따옴표 한 쌍만 벗김·unescape 없음, 닫는 `---` 뒤 줄바꿈 필요), Codex skill 7종(파서 ❌).
- 형식: **한 줄 문법**으로 정의한다 — YAML 부분집합 파서가 아니다. 구분선 사이의 모든 줄이 `^[A-Za-z][A-Za-z0-9_-]*: 값$` 이고 값이 비지 않는다. 키를 처음 `^[a-z][a-z0-9_-]*` 로 정했다가 대문자를 허용하는 쪽으로 바꿨다(이유: Claude Code 가 camelCase agent 키 `permissionMode`·`maxTurns`·`disallowedTools` 등을 정의하고 대소문자를 구분해 읽는다 — code-review M2). 불리언·null 키 판정은 대소문자를 무시한다. 값은
  - 평문 — 첫 글자가 YAML 지시자(``, [ ] { } # & * ! | > % @ ` ``)가 아니고 `-`·`?`·`:` 로 시작하면 바로 뒤가 공백이거나 값의 끝이 아니다. 안에 `: `, ` #` 가 없고 `:` 로 끝나지 않으며, 앞뒤에 공백 문자(JS `\s` — NBSP·U+3000 등)가 없다(sync 의 `strip()` 은 벗기고 YAML 은 남긴다).
  - 또는 `'…'`·`"…"` — 값 전체가 한 쌍의 따옴표이고 안에 그 따옴표와 `\` 가 없다(escape 가 없으면 YAML 과 sync 가 같게 읽는다).
  - 공통 금지: 줄 어디에도 `---` 부분문자열(Claude Code 추출이 거기서 끝난다), 탭·C0/C1 제어문자·DEL·U+2028/2029·U+FEFF·U+FFFE·U+FFFF·서로게이트·lone CR(파서마다 판정이 갈린다 — PyYAML 은 탭·NEL·U+FFFE 거부, ruamel 은 일부 받음). 키는 중복 금지, YAML 1.1 에서 불리언·null 로 읽히는 키(`y n yes no on off true false null`, 대소문자 무관) 금지.
  - 파일은 fatal UTF-8 로 디코딩한다(관대한 `utf8` 은 CP949 를 U+FFFD 로 바꿔 통과시킨다). BOM 은 **하나만** 벗기고(Claude Code 의 `Qb` 와 같다 — CLI 디코더는 `ignoreBOM: true` 로 BOM 을 남겨 순수 함수에 넘긴다. 둘 다 벗기면 BOM 두 개가 통과했다 — code-review M1) CRLF 는 LF 로 바꾼다. 첫 줄은 정확히 `---`, 다음 정확한 `---` 줄에서 끝나고 그 뒤에 줄바꿈이 있다(sync 는 `\n---\n` 을 찾는다).
  - `name` 은 YAML 1.2 core 의 숫자·불리언 형태(`123`·`true`·`0777`·`0x1F`·`1e5`·`.5`·`-1`·`.inf` 등)와 부호 붙은 16진·8진(`-0x1F`·`+0o17` — core 명세 밖이지만 Claude Code 는 숫자로 읽는다, code-reviewer 2회차 validate 재현)이 아니다 — validate 실측(2026-10-01)에서 이 값들은 "name must be a string", `yes`·`on`·`1:20`·`1_000` 은 통과했고 description 은 어떤 값도 오류가 아니었다.
  - 모든 키: 값이 null 형태(`~`·`null`·`Null`·`NULL`)가 아니다 — YAML 은 null, sync 는 문자열 `"~"` 로 읽어 갈린다. 필수 키 `name`·`description` 은 반드시 있다.
  - 모든 키: 평문 값이 `=`·`<<`(YAML 1.1 value·merge 태그 — PyYAML·ruamel 모두 ConstructorError)이거나 YAML 1.1 timestamp 형태(옳은 날짜는 date 로, `2026-13-45` 는 ValueError)가 아니다. 건전성 대조의 무작위 값에서 `=` 가 걸려 찾았다(2026-10-01, 아래 Progress).
  - 이유: 모든 소비자의 교집합이라 통과하면 키 집합·줄 경계·값 문자열이 소비자 사이에서 같다(타입 해석 차이만 감수 — Out of scope). 현재 13개 파일이 모두 이 형식이다. 빈 줄·주석·목록·블록 스칼라·escape 는 쓰는 곳이 없고 sync 가 거부하거나 다르게 읽는다(plan-reviewer S2 — 처음 초안의 "YAML 부분집합(목록·주석 허용)"을 이 이유로 좁혔다).
  - 기각: PyYAML(`uv run --with pyyaml`·pip) — CI 에 새 의존성·네트워크, verify.sh 의 system python3 와 어긋남(미설치 로컬은 상시 skip), 1.1 이라 Claude Code 와 판정이 다르고 fallback·` #`·`---` 를 못 본다. 개발 중 대조(Acceptance 5)로만 쓴다.
  - 기각: `claude plugin validate` 를 게이트로 — fallback 까지 흉내 내서 `: `·` #`·`---` 를 보고하지 않고, CI 에 Claude Code 설치가 필요하다. 처음 "무보고라 기각"이라 적은 근거는 틀렸다 — 그때 넣은 결함이 fallback 으로 살아나는 형식뿐이었다(2026-10-01 재실측). 개발 중 대조(Acceptance 5)로 쓴다.
  - 기각: `wiki_check.py` 의 frontmatter reader 재사용 — 목록·주석을 받는 관대한 reader 라 목적(소비자 교집합)과 반대다. `sync_codex_agents.parse_frontmatter` 재사용 — agents 전용 규칙(name 문자)·첫 오류에서 멈춤·줄 번호 없음·` #`·`---`·`: ` 를 통과시킨다. 이 검사기의 허용 집합이 sync 의 부분집합이 되게 맞춘다(Acceptance 5).
  - 기각: grep 강화 — 따옴표 안 `: `(유효)를 오탐하고 다른 형식을 못 잡는다.
- 반환: `lintFrontmatter(text) → { fields, violations: [{ line, message }] }` — plan-lint 의 `string[]` 과 다른 이유는 줄 번호(Acceptance 1)와 검사기가 읽은 값(Acceptance 5 대조). 파일 단위 위반(없음·닫힘 없음·필수 키 누락)은 줄 1. CLI 가 `<파일>:<줄>: <메시지>` 로 찍는다.
- CLI: 위반·읽기 실패·잘못된 UTF-8 은 exit 1(plan-lint 는 읽기 실패를 skip — 게이트에서 skip 은 통과로 보인다), 인자 0개는 사용법과 exit 2. kill-switch env 는 두지 않는다(게이트의 조용한 우회로). 대상 자동 발견 모드·`--kind`·위반 코드 enum 은 만들지 않는다(과설계).
- 배치: `scripts/frontmatter-lint.js` + `scripts/frontmatter-lint.test.js`. verify.sh **syntax 축**에서 `== syntax (frontmatter) ==` 헤더 아래 git 발견 파일마다 CLI 를 돈다. 대상이 0개면 FAIL(verify.sh 의 git 작업트리 가드와 같은 원칙). CI "Syntax" 스텝이 부르므로 lint.yml 은 주석만 고친다.
  - 기각: 새 verify.sh 축 — 스텝 이름이 분명해지고 Syntax 실패가 뒤 스텝을 가리지 않는 이득이 있지만 lint.yml·README 축 목록이 바뀐다. 감수: frontmatter 위반이면 CI 뒤 스텝이 skip 된다(로컬 verify.sh 는 끝까지 돈다).
  - 기각: 테스트 파일 안에서 실제 파일 검사 — 콘텐츠 게이트가 단위 테스트에 숨는다. 선례 `scripts/ps1-encoding.test.js` 가 그 방식이지만, verify.sh 출력에서 파일별로 보이게 하려고 따르지 않았다.
- improve.sh 점검 4: 대상은 verify.sh `repo_files` 와 같은 git 발견(`ls-files --cached --others --exclude-standard` + `:(glob)` pathspec + 존재 검사) — 파일시스템 glob 은 main checkout 의 ignored `orca-cli`(`>-`)를 끌어와 `/improve` 에 상시 거짓 `[error]` 를 낸다. 판정은 CLI exit code(0 이면 OK, 비0 이면 출력 줄마다 E, 출력이 없으면 E 한 줄 — fail-closed). 대상 0개도 E. 이웃 점검의 `|| I skip` 관례는 쓰지 않는다. 헤더 번호 `== 4.` 는 유지한다(`native-overlap-lint.test.js` 가 1..N 연속을 본다). CI 에서는 Syntax 스텝과 발견·판정이 같아 더 잡는 것이 없고(Syntax 가 실패하면 뒤 스텝은 skip), 바꾸는 목적은 `/improve` 판정 일치다. 서로를 가리키는 주석은 verify.sh 의 `repo_files` 정의와 syntax 블록, improve.sh 점검 4 에 두고, improve.sh 머리 주석(6행 — 다른 파일이 줄 번호로 인용해 같은 줄 안에 적었다)에 점검 4 가 skip 규약의 예외임을 적는다.
- 순서: 검사기와 건전성 대조를 먼저 끝내고 verify.sh·improve.sh 연결은 그 뒤에 한다 — main 이 빨개지면 `record-verified` 가 멈춰 모든 머신의 자동 pull 이 멈춘다.
- 커밋 단위: 1개 — 검사기·연결·문서가 한 목적(frontmatter 검사 도입)이라 중간 커밋이 따로 의미가 없다.
- ⚠️ 유효한 YAML(빈 줄·주석·목록·블록 스칼라·escape)을 거부한다 — 완전성과 소비자 교집합을 함께 만족할 수 없다 — 교집합을 택했다. sync 가 이미 같은 형식을 거부하고 현재 파일이 모두 한 줄이다. 필요해지면 모든 소비자에서 확인한 뒤 넓힌다.
- 값 안 `---` 에서 Claude Code 추출이 끝나는 것은 번들 정규식 판독(plan-reviewer·code-reviewer)과 validate 재현(code-reviewer 2회차 — `name: n---x` 가 "No description in frontmatter", 뒤 줄이 잘렸다)으로 확인했다. description 안의 `---` 는 validate 로 보이지 않는다(잘린 값도 문자열이라 오류가 아니다). 처음엔 판독뿐이라 ⚠️ 로 적었다.

# Review Disposition
- [arch] M1 대상 발견이 호출자마다 다름(orca-cli 거짓 error) — fix(점검 4 git 발견, Acceptance 4)
- [arch] M2 반환 형태 미정 — fix(`{ fields, violations: [{line, message}] }`)
- [arch] m3 점검 4 판정 관례 — fix(exit code, fail-closed)
- [arch] m4 syntax 축 trade-off 기록 — fix(Decisions 배치, 별도 헤더)
- [arch] m5 허용 형식 목록 복제 — fix(스크립트 머리 주석·README scripts 절 두 곳, Acceptance 7)
- [arch] 과설계 경고 7건 — fix(kill-switch·자동 발견·`--kind`·enum·영구 PyYAML 테스트·공용 추출기·범용 상태기계 모두 만들지 않는다)
- [plan] ⚠️ 완전성 포기 — accepted-risk(소비자 교집합을 택함, 이유는 Decisions)
- [plan] ⚠️ Claude Code 파서 모름 — resolved(reviewer 번들 판독 + `plugin validate` fallback 실측)
- [plan] S1 값 안 `---` — fix(금지, 대조에 추출 정규식 사용)
- [plan] S2 sync_codex_agents 누락 — fix(한 줄 문법으로 좁힘, 따옴표 안 자기 따옴표·`\` 금지, 소비자 목록)
- [plan] S3 점검 4 파일 집합 — fix(arch M1 과 같음)
- [plan] S4 파서마다 갈리는 문자·잘못된 UTF-8 — fix(금지 문자, fatal 디코딩)
- [plan] S5 필수 키 판정과 타입 — fix(null 형태 = 누락) · accepted-risk(나머지 타입 해석 차이 — Out of scope)
- [plan] W1 Problem 이 fallback 과 충돌 — fix(Problem 재작성, `0efce86` 서술 정정은 Report 에)
- [plan] W2 BOM 거부 사유 틀림 — fix(벗기고 통과)
- [plan] W3 대조 범위 — fix(Acceptance 5: 추출 정규식 → PyYAML·ruamel + sync + validate + 무작위)
- [plan] W4 대상 0개 — fix(두 곳 FAIL)
- [plan] W5 kill-switch — fix(두지 않음)
- [plan] W6 위험 단계 — fix(순서 결정)
- [plan] W7 `== 4.` 번호 — fix(유지)
- [plan] W8 헤더·출력 형식·원복 방법·지시자 표·키 문법·lint.yml 주석 — fix
- [plan] W9 기각안 기록 — fix
- [plan] W10 Open questions — fix
- [plan] Q1 Codex skill 파서 — deferred(Open question, 조사 안 함) · Q2 목록·주석·빈 줄 — 쓰는 곳 없음 → 뺌 · Q3 BOM — 벗기고 통과 · Q4 타입 — null 만(구현 뒤 validate 실측으로 name 의 숫자·불리언 추가)
- [arch-post] APPROVE. m1 improve.sh:6 규약과 점검 4 fail-closed 예외 — fix(6행 같은 줄에 예외) · m2 발견 복제 상호참조 — fix(`repo_files` 정의 주석) · m3 README 사본 정본 표시 — fix("허용 형식 요약(정본은 스크립트 머리 주석)") · 제안: 머리 주석 호출자 — fix, ps1-encoding 선례 — fix(Decisions), "중복 백스톱" 표현 — fix
- [code] M1 CLI BOM 이중 제거 — fix(`ignoreBOM: true`, CLI 테스트 BOM 1·2개)
- [code] M2 camelCase 키 과잉 거부 — fix(`[A-Za-z]` 키, 불리언 키 대소문자 무시, 메시지에 키 규칙)
- [code] m CRLF 에서 fallback 실패(0efce86 서술은 CRLF 에서 사실) — fix(Intent·Decisions·README·머리 주석, Report 에 정정)
- [code] m 표본 밖 반례 — fix(U+FFFE·U+FFFF·서로게이트, 평문 앞뒤 공백 문자, 닫는 `---` 뒤 줄바꿈, name 숫자·불리언) · wontfix(밑줄 숫자 형태 `0x_`·`._` — 비현실적, 머리 주석·Out of scope 에 "보지 않는다")
- [code] m 하네스 사각지대 — fix(CLI 판정 대조·validate 경고·이름·키·알파벳·파일 끝 보강, Acceptance 5 에 "표본의 성질" 명시)
- [code] m 살아남은 변이 — fix(`-`·`?`·`:` 단독, U+0080·U+009F, CLI BOM, 따옴표 메시지 고유 부분 `한 쌍`)
- [code] nit improve.sh:6 — fix(arch m1 과 같음) · README↔머리 주석 목록 차이 — fix(arch m3) · 머리 주석 "바로 뒤가 공백" — fix("공백이거나 값의 끝") · 공백만 든 따옴표 값 — wontfix(소비자가 모두 같게 읽는다) · `process.exit` 뒤 stdout 잘림 — wontfix(호출부가 `$(…)` 로 즉시 읽고 plan-lint 선례와 같다)
- [code-2] APPROVE — 1회차 fix 전부 재현 확인(변이 34/34, CRLF validate 955건 오류 0, 하네스 재현 불일치 0). Minor name 정규식이 부호 붙은 16진·8진을 놓침 — fix(`[-+]?0o`·`[-+]?0x`, 테스트 `-0x1F`·`+0o17` Red → Green) · Nit `0777` 을 "보지 않는 타입" 예로 듦(실제로는 name 에서 거부) — fix(`yes`·`1:20`·`0b101` 로, 머리 주석·README·Out of scope) · Nit 키 메시지에 허용 문자 없음 — fix · Nit `---\r`·`--- ` 닫힘 메시지 부정확 — wontfix(거부 판정은 맞고 드물다)

# Key Files
- `scripts/frontmatter-lint.js` — 신규. 순수 판정 + CLI, 허용 형식 정본(머리 주석)
- `scripts/frontmatter-lint.test.js` — 신규. fixture·CLI 계약 테스트(verify.sh node 축이 자동 발견)
- `scripts/verify.sh` — syntax 축에 frontmatter 검사, 머리 주석
- `skills/improve/improve.sh` — 점검 4 를 git 발견 + CLI 호출로(agents 포함)
- `skills/improve/SKILL.md` — 1단계 `[error]` 설명
- `README.md` — improve.sh 점검 목록·scripts 절·verify.sh 절
- `.github/workflows/lint.yml` — 점검 주석(skill·agent frontmatter)
- `scripts/bootstrap/sync_codex_agents.py` — 읽기만(소비자 대조 기준)

# Blockers
