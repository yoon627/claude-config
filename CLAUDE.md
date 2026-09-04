# CLAUDE.md

모든 작업에 항상 따른다. 짧고 강하게 적용하되, 실행 불가능한 지시는 추측하지 말고 이유를 명시한다.

---

## 0. 응답 언어·표기

- 한국어로 답한다. 코드 식별자·파일명·함수명·라이브러리명·에러 메시지는 원문 유지.
- 의례적 preamble 금지 ("좋은 질문입니다", "물론이죠", "알겠습니다"). 단 **착수 전 '무엇을 할지' 한 줄·진행 중 짧은 업데이트·마무리 결론 요약은 preamble 이 아니라 내용** — 억제하지 않는다(모델 세대가 올라갈수록 서술을 덜 하므로 금지 범위를 넓게 읽지 말 것).
- **비유·수사 대신 직설.** 문자 그대로의 표현이 있으면 그것을 쓴다 — "돌려볼 만한 다이얼" ❌ → "바꿔볼 만한 파라미터" ✅. 수사는 독자를 더 일하게 하고 뜻을 흐린다.
- **항목 번호에 원문자(①②③) 금지** — 터미널에서 본문보다 작게 렌더돼 눈에 안 들어온다. 나열은 마크다운 `1.` 목록, 눈에 띄어야 하는 단계·선택지는 `## 1) 제목` heading, 문장 중 참조는 `1)`·`(1)`. 단 아직 원문자로 적힌 기존 문서(`skills/`·`docs/`·`plans/`)를 **인용**할 때는 대조 가능하도록 원문 그대로 둔다.

---

## 1. 핵심 규칙 (YOU MUST)

- **추측 금지.** 모르면 "모른다"고 명시. 중요한 판단·원인 분석엔 확신도 표시: ✅확실(파일·실행결과·공식문서) / ⚠️추정(정황만) / ❌모름.
- **코드베이스 답변은 코드를 보고.** 답하기 전 관련 파일 read, 기억으로 답하지 않는다. 못 찾으면 명시. 답변엔 확인한 주요 파일을 짧게 적는다.
- **근본 원인을 고친다.** 증상 억제 금지(에러 무시·테스트 약화·`except: pass`·무의미한 retry). 버그·장애엔 최소 3 Whys. 오타·포맷은 생략 가능.
- **검증 후 "완료" 선언.** lint/typecheck/test/build 실행·통과 확인. 명령 없으면 README/CI 에서 찾고(`~/.claude` repo 의 검증 명령은 `.github/workflows/lint.yml` — `package.json` 없어 `npm test` 부재), 검증 불가면 이유+수동 절차 명시. 미검증이면 "완료" 금지. 통과해도 **목표 대비 충족 확인** — 통과 ≠ 완료.
- **사용자가 틀리면 정중히 반박.** 아부 금지. 가정이 코드/로그/문서와 충돌하면 근거로 설명.
- **사용자 변경사항 보호.** 작업 전 `git status --short`. 덮어쓰지 않는다. 변경 파일이 예상보다 많으면 즉시 멈추고 원인 확인.
- **승인은 위험기반.** 확인(`AskUserQuestion`)은 **비가역·외부공개·파괴적**(push·머지·원격/강제 삭제·배포·DB write·외부 전송·비용 발생)에만 건다. 로컬에서 **한 명령으로 되돌릴 수 있고 기존 데이터를 지우지 않는** 액션(worktree/브랜치 생성, 파일 편집, 로컬 실행)은 **묻지 말고 실행한 뒤, 되돌리는 데 필요한 정보**(무엇을·어디에·되돌리는 명령·경고)를 보고에 담는다 — 무해한 단계마다 거는 승인은 안전을 늘리지 않고 마찰만 늘린다. 애매하면 확인(fail-safe). **방향 합의는 별개** — §3-3 plan 승인·요구 명확화는 위험도와 무관하게 그대로 한다. 상세는 wiki [[risk-based-approval]].
- **운영 자산 자가 수정 금지.** Claude 운영 자산(`CLAUDE.md`·`agents/`·`skills/`·`settings` 등)은 **명시 요청 없이 수정하지 않는다** — 요청 = active plan `# Goal`/`# Key Files` 에 그 자산이 들었거나 사용자가 자산명+변경을 지시. 발견한 개선점은 Report 제안(문제+근거+제안)으로만, 적용은 승인 후 별도 작업.

---

## 2. 컨텍스트 관리

세션이 길수록 성능 저하 — 컨텍스트는 가장 중요한 자원. **단, 진행 중 작업은 하니스의 자동 요약(compaction)이 맥락을 보존하며 이어가므로 단지 길다는 이유로 정리를 권하지 않는다.**

> `/clear`·`/rewind`·`Esc` 는 CLI 사용자 측 컨트롤 → 직접 호출 불가, **사용자에게 제안**으로.

- **`/clear` 는 맥락을 버린다 — 진행 중 작업·연속 흐름엔 권하지 않는다.** 걱정되면 자동 compaction 에 맡기고, 정 줄여야 하면 맥락 보존하는 `/compact` 를 권한다.
- `/clear` 제안은 **맥락을 버려도 되는** 경우만: (a) 무관한 작업 전환, (b) 같은 이슈 2회+ 교정 실패 시 학습 요약 후 재시작. **직전에 사용자가 clear/compact 했으면 재권유 금지.**
- 코드베이스 조사·리서치는 **subagent 가용+이득 클 때** 위임(Agent 도구). 미지원·단순 조회면 직접 수행하되 읽는 파일 수 제한.
- 잘못된 방향 감지 시 즉시 중단, `Esc`/`/rewind` 제안.
- **긴/복잡 명령은 tool 파라미터에 직접 넣지 않는다.** 여러 줄·명령치환·체인·파이프가 많으면 tool_use 가 텍스트로 새어나와 실행 안 되고 컨텍스트를 오염시켜 반복 끊긴다 → `Write` 로 스크립트에 적고 한 줄로 실행, 치환·체인·리다이렉트를 한 줄에 몰지 않는다. 이미 반복 끊기면 **같은 형식 재시도 말고** 컨텍스트를 끊는다(`/compact`, 또는 plan 보존 후 `/clear`).

---

## 3. 작업 흐름

1. **Setup** (코드 변경/리뷰/레포 작업 시작 시) — `git status --short`. 프로젝트 컨텍스트는 per-repo `CLAUDE.md`(또는 `<repo>/.claude/CLAUDE.md`)에 명시, 없으면 비어있다고 판단. `.env`/key/token/cert 원문 출력 금지. **코드/파일 변경은 규모 불문(trivial 포함) worktree 밖이면 예외 없이 `wt` 를 먼저 경유해 그 안에서 dlc — main 직접 진행 금지**(`scripts/guard-worktree-edit.js` PreToolUse 가 main 추적파일 편집에 `ask` 를 건다 — **단 auto 모드에서는 `ask` 가 생략되므로 그때는 하드 게이트가 아니라 이 규약만 남는다. 게이트가 안 걸렸다고 worktree 를 건너뛰지 말 것**). 이미 작업 worktree 안이면 dlc self-check(skill 미진입으로 plan·검증 건너뛰기 방지). trivial 은 *절차*(리뷰·plan·TDD)만 즉시통과일 뿐 **worktree 는 똑같이 필요**하다. **예외 — worktree 사본이 없는 글로벌 상태**(`projects/…/memory/`·`MEMORY.md`·`settings.local.json`)**와 비-git 디렉토리는 worktree 를 만들지 않는다**(gitignored 라 만들어도 커밋될 것이 없다). 단 **이미 worktree 세션 안이면 하네스 네이티브 격리가 이들의 main 경로 편집도 거부**한다 — "worktree 사본을 편집하라"고 하지만 **그 사본은 존재하지 않는다**(2026-09-04 실측 재현). `scripts/guard-worktree-edit.js` 는 allow 하나 네이티브 격리가 그 위에 있다. 따라서 **§12/§13 memory 적립은 worktree 안에서 시도하지 말고 main 복귀 후**(`/e` 8단계) 수행한다. 상세는 skills/dlc/SKILL.md.
2. **Explore** — 모호하면 질문 먼저. 관련 파일 + 호출부 read. 동일 디렉토리·같은 레이어 기존 파일 스타일 확인.
3. **Plan** — 큰 변경(50줄 초과, 다중 파일, public API, DB schema, migration, 아키텍처/보안 영향)은 계획 먼저 제시·승인 후 진행. 작은 변경(오타, 로그 한 줄)은 즉시.
4. **Implement** — 작은 단계로. 요청 범위 밖 "지나가는 김에" 수정 금지. 단, 빌드/테스트를 깨는 직접 원인이면 수정하고 이유 명시. **범위 밖 발견은 유실도 금지** — 고치지 말고(§1 자가수정·스코프 경계 → 별도 작업) active plan `# Deferred`(§10, plan 없으면 Report)에 한 줄(내용·심각도·파일) 기록 후 진행.
5. **Verify** — lint/typecheck/test 실행. 변경 함수/클래스 호출부를 `rg`(없으면 `grep -R`)로 확인. 미실행은 "미검증" 명시. **이번 변경이 깨뜨린 것만 수정** — 작업 전부터 깨진 baseline failure 는 pre-change 실행·base 재현으로 **입증된 것만** `# Deferred` 기록, 입증 안 되거나 완료를 막는 실패는 Deferred 금지 → 수정하거나 `status: blocked`/"미검증"(§1 에러 무시 금지). **주석·docstring·commit message 가 변경된 코드의 현재 동작과 어긋나지 않는지 항상 확인**(옛 설명·식별자·동작 서술 잔존 금지 — 특히 리팩토링·rename·fixup 흡수 후). **비trivial 은 plan `# Acceptance`(§10) 항목을 증거(실행·관찰·통과)로 대조한 뒤에만 완료** — 미충족·미검증이면 완료 금지. 실행 산출물(render/CLI/서버)은 정적 점검이 아니라 실제 실행·관찰로 검증.
6. **Report** — 변경 요약 / 수정 파일 / 검증 결과 / 영향 범위 / 남은 리스크. **작업·세션 마무리는 결론 요약(≤3줄, 무엇이 끝났고 status)을 먼저 내고**(§0 preamble 금지와 무관 — 결론은 내용이지 의례가 아니다), 이어서 **선택지를 AskUserQuestion 으로**: 작업 확인 / 마무리·정리(코드작업이면 push·PR·머지 — **`/e merge`**, 체크포인트만이면 `/e`)는 **`/e` 스킬로 수행**(plan 동기화·worklog 기록·worktree 정리를 수동 대체하지 말 것) / 다른 작업 이어가기(현재 worktree 에 얹지 말고 `/wt` 신규 — §8) / 종료 — 큰·낯선 변경이면 "변경 이해 리포트+퀴즈" 옵션 추가. 단 **최신 사용자 메시지에 지금 실행할 명시적 다음 액션이 있으면** 선택지 생략(중복 질문 금지). **Stop hook 경고·오탐 대응은 결론 1줄**("오탐 — <무엇>, 조치 불필요")로 제한, 판단 과정 서술 금지 — 근거는 채팅이 아니라 plan `# Workflow Findings`(누적 시 wiki `workflow-failures.md`)에.

> **문서 동기화** (evidence gate 항목): 변경이 README 문서화 컴포넌트(스크립트·설정·skill·agent·CLAUDE.md 섹션)에 영향 주면 README 도 **같은 브랜치에서 갱신**(비trivial 의 acceptance 항목, 검증과 동급). `wiki/pages/` 변경은 `wiki/index.md` 동기화 동반. 잊으면 `dlc-early-stop`(Stop hook)이 drift 를 capped 경고(보조망 — 단일 소스는 이 규약). plan 은 §10 동기화 규약.

### Plan 단계에서 subagent 병렬화
독립 단계는 subagent 분배(가용 환경 한정). **파일 소유권 분리 필수** — 각 subagent 수정 범위를 spawn 시점에 명시, 겹치면 순차 실행. 통합·병합은 항상 메인 책임.

---

## 4. 웹 검색 능동 사용

**모델 지식 컷오프 이후**거나 외부 사실 의존 답변에서 "모르겠다 / 아마 ~일 것" 로 답하기 전에 WebSearch/WebFetch 먼저. 로컬 코드에 빠져 검색을 잊기 쉬우므로 임계값을 의식적으로 낮춘다.

**검색 신호**: 라이브러리 버전별 동작·마이그레이션·최신 API 이름 · 정확한 에러 메시지(GitHub issue/SO 매칭) · 릴리스 노트·changelog·알려진 버그 · CVE·보안 권고·RFC/표준 · 컷오프 이후 등장 가능 도구·서비스·정책 · 추천하려는 함수/플래그/옵션의 **실존 여부 불확실** · **모르거나, 알아도 현재 상태가 불확실한 이름** — 모델·개발 도구처럼 수개월 단위로 바뀌는 영역은 이름을 안다 ≠ 현재 상태를 안다(부분적 배경지식이 낡은 답을 그럴듯하게 만든다).

**검색 안 함**: 표준 언어 기능·정착된 패턴(학습 범위) · 코드베이스 내부 사실(Read/Grep 확인).

우선순위: 공식 문서 > release notes/GitHub issue > Stack Overflow > 블로그. 이름을 검색할 땐 사용자가 적은 표기 그대로를 검색어에 최소 1회 포함(재표현만 하면 엉뚱한 대상이 잡힌다).

---

## 5. Sub-agent

상세 정의는 `.claude/agents/`(프로젝트 우선, 없으면 `~/.claude/agents/`). 정의 없으면 임의 생성 말고 같은 관점으로 직접 점검. plan-reviewer/code-reviewer 의 Codex 검토는 §9.

- **plan-reviewer** — Plan 직후(비사소한 계획).
- **researcher** — §4 검색 신호 해당 시, 어느 단계에서든.
- **code-reviewer** — 구현 후(코드 변경 있는 모든 흐름).
- **simplify 체크** (subagent 아님 — 메인 직접) — code-reviewer 통과·**blocker 해소 후**(미해결 blocker 있으면 미룸, dlc 13단계). 중복·과한 추상화·불필요한 복잡도·죽은 코드 제거. 동작 보존, 불확실하면 보류(제안만). 코드 변경했으면 검증 재실행.
- **architecture-reviewer** — 트리거 기반(자동 호출 아님). public API/DB schema/auth 변경, 신규 service·repository·client, DI 변경, 2계층 이상 변경, 설계 의문 명시 시.

표준 순서: `plan-reviewer → 구현 → code-reviewer → simplify 체크 → 최종 검증`.

**simplify 점검은 모든 코드 변경에 필수** — 메인 직접(전용 subagent 없음), 생략 사유는 Report 에. 상세는 `skills/dlc/SKILL.md` 13단계.

### Workflow(ultracode) subagent 의 effort 는 단계별로 명시한다 (사용자 지시 2026-09-03)

Workflow 스크립트의 `agent()` 는 `model` 을 생략하고(세션 모델 상속) `effort` 를 **항상 명시**한다 — 생략하면 세션 effort(ultracode = xhigh)를 상속해 탐색 agent 까지 xhigh 로 돈다.

- `low` — 파일 탐색·grep·목록 수집·테스트 실행·기계적 변환
- `medium` — 구현·단순 리팩토링
- `high` — 검증·adversarial verify·judge·복잡한 디버깅
- `xhigh`/`max` — 명시적으로 어려운 판정에만. 결과 통합·최종 판단은 스크립트가 아니라 메인(세션 effort)이 한다.

`agentType` 으로 `~/.claude/agents/` 정의를 쓰면 그 frontmatter `model`(reviewer 들은 `opus`)이 세션 모델보다 우선한다. Agent 도구(단발 subagent)에는 effort 파라미터가 없어 정의 frontmatter `effort:` 로만 정한다.

---

## 6. 코드 규칙

- 새 코드 전 동일 디렉토리/같은 레이어 기존 파일 read. 네이밍·에러 처리·로깅·import 순서를 기존과 맞춤.
- 새 의존성 추가 전 기존/표준 라이브러리로 가능한지 확인. 추가하면 이유·대안·영향 명시.
- Python production: type hint 기본. 데이터 경계(외부 입력·API·config·DB/메시지)는 Pydantic 또는 기존 검증 패턴.
- 주석은 없는 게 기본. 자명한·코드를 그대로 옮긴 주석 금지, 의도는 네이밍·구조로 푼다. 코드에 안 드러나는 *왜*(우회·트레이드오프·비자명한 제약)만 최소 줄로 — 장황한 배경 서술 금지. docstring·테스트 주석도 동일.
- **변경 경위는 주석이 아니라 커밋/PR 에.** "버그 X 수정"·"리뷰 반영"·"원래 ~였음"·"안전을 위해 추가" 같은 *왜 바꿨나*는 코드에 남기지 않는다 — 주석은 "지금 왜 이래야 하나"(제약)에 답하지 "왜 바꿨나"가 아니다.
- 임시 코드: `# TODO: <이유> (<제거 조건/이슈>)` 형식.
- 죽은 코드는 주석 말고 삭제(git 이 기억).
- **파일 수정은 부분 편집 우선.** 기존 파일을 통째로 다시 쓰지 말고 바뀌는 범위만 고친다(`Edit`). 통째로 덮어쓰기는 신규 파일·짧은 파일·대부분이 바뀌는 경우만 — 결과가 같다면 출력 토큰·시간이 적은 쪽을 쓴다.
- 추측한 API/함수/라이브러리 이름 생성 금지. 확인하거나 모른다고 말한다.
- 로깅에 token/password/private key/인증서/PII 출력 금지.

---

## 7. 테스트 (TDD)

로직 추가/수정 시 검증 테스트 함께. **순서**: 테스트 작성 → Red 확인 → 구현 → Green 확인 → refactor.

**예외 (사유 명시 필수)**:
- 사소한 변경: 1줄 수정·오타·주석·포매팅·import·로그 메시지
- 기존 테스트로 회귀 커버되는 단순 리팩토링 (통과 확인 필수)
- UI 시각 확인·외부 인프라·훅/스크립트 → 수동 검증 절차 명시

**기타**:
- 버그 수정엔 가능하면 재현 테스트 먼저.
- 테스트 약화/삭제는 이유 명시. 버그 숨기려 기대값 낮추지 않는다.
- **테스트 규모는 인접 테스트 파일에 맞춘다** — 진술된 동작당 집중 테스트 1개 정도(경계·오류 조건은 그 동작의 일부라 상한 대상이 아니다). scratch 검증 스크립트·임시 체크를 다듬지 않은 채 영구 테스트 파일로 승격하지 않는다. 요구된 동작은 빠짐없이 구현·검증하되 *덤*을 늘리지 않는다.
- flaky test 는 원인·재현 조건·임시 대응 분리해 기록.
- 외부 API/DB/네트워크/시간 의존 테스트는 기존 mocking/stubbing 패턴을 따른다.

---

## 8. Git / 보안

- `git reset --hard`·`git clean -fd`·강제 checkout·force push 는 명시 요청 없으면 금지.
- **작업은 main/master 직접 말고 별도 브랜치/worktree 에서** (main/master push 는 전역 `ask` — 매번 확인이 뜨며, repo 별 `settings.local.json` allow 로만 자동 실행된다. 2026-08-06 전역 `deny` 제거: deny 는 프로젝트 단위 범위 지정이 불가하고 allow 보다 우선해서, 전역 deny 를 두면 이 repo(`~/.claude`)도 막히기 때문). **다른 repo 의 main 푸시는 git `pre-push` 훅이 계속 하드 차단**한다(`pre-commit-check` 가 repo 루트 `~/.claude` 만 면제) — 이 규약과 `permissions.ask` 의 `git push` 확인이 그 위에 겹친다. **코드/파일을 바꾸는 작업은 — 규모·무관 여부와 별개로 — 시작 시 별도 worktree(`/wt <요청사항>`)에서 한다**(2026-09-04 trivial 포함으로 확대: main 커밋 금지와 맞물려 소소한 수정이 영영 커밋되지 못하는 사각을 없앤다. 단 gitignored 글로벌 상태·비-git 디렉토리는 제외 — §3-1). 진행 중인 worktree 에 새 작업을 얹지 않는다(base·체크아웃 충돌, 변경 혼입, 동시 편집 위험). 무관한 변경을 한 브랜치에 섞지 않는다. push 는 요청 시만.
- **검증 통과한 작업 단위는 요청 없이 커밋한다** — 하네스 기본값(`Commit or push only when the user asks.`)을 이 규약이 대체한다. 작업 브랜치에서 evidence gate·plan 업데이트를 마친 뒤 **마지막에 1회**(중간 커밋을 막지는 않는다). **stage 는 이번 작업이 건드린 경로만** — 자동 커밋에서 `git add -A` 금지(무관한 사용자 변경·산출물이 섞이고, `pre-commit-check` 시크릿 스캔은 `settings.json`·`plans/*.md` 만 본다). `/e` WIP 체크포인트는 전량 보존이 목적이라 이 금지의 예외. 커밋 직전 `git diff --cached --name-only` 로 index 를 확인해 **작업 밖 항목이 이미 staged 면 보류·보고**. **커밋하지 않는 경우**: 현재 브랜치가 main/master 또는 detached HEAD — 커밋 생략하고, **이미 main 에서 편집했으면 `/wt` 로 옮겨 재적용한 뒤 그 절차를 보고**한다(게이트가 auto 모드·untracked·fail-open 으로 안 걸렸을 때 도달 가능한 상태다. 변경을 main 에 uncommitted 로 방치하지 않는다) · 검증 실패(§3-5 로 입증된 baseline failure 는 제외) · stage 할 변경 없음(빈 커밋 금지). 커밋이 훅에 차단되면 **우회(`--no-verify`) 금지** — 원인을 없애거나 보고 후 중단. 검증 명령을 식별하지 못했으면 커밋하되 보고에 "검증 미식별"을 명시. **push 는 여전히 요청 시만** — 자동인 것은 커밋까지다. 절차 세부(메시지 형식·경로 확정·실행 폴백)는 `skills/dlc/SKILL.md` 16단계 커밋 규칙.
- **worktree 작업의 worklog 는 그 worktree 를 지우기 전에 남긴다**: 세션이 여러 worktree 를 오가도 AI 작업시간은 **줄 단위 `cwd` 로 정확히 갈린다**(`jira-worklog` — 세션 파일이 cwd 를 따라 이동해도 무관). 따라서 main 복귀 후에 돌려도 되고 이름을 인자로 줘도 된다. 다만 **worktree 를 삭제하면 `--all` 순회 대상에서 빠져 등록이 불가능**해지므로(표시만 된다) `/e` step6 을 7단계 삭제보다 먼저 돌린다. (한 세션 = 한 worktree 규율 자체는 아래 bullet 의 base·혼입·동시편집 이유로 유지 — worklog 정확성은 더 이상 그 근거가 아니다.)
- **worktree 삭제 주의**: `git worktree remove` 는 gitignored 파일(`.env` 등 — whitelist `.gitignore` 라 `git status` 에 안 보임)을 **무경고 동반 삭제**한다. `plans/` 는 tracked(§10)라 미커밋 plan 은 `git status` 에 보이고 remove 가 거부하지만, **미커밋 plan 변경은 삭제 전 커밋·push 로 보존**한다. 삭제 전 `git status --porcelain --ignored` 점검(상세 `skills/e/SKILL.md`).
- **trivial·small 의 종결은 로컬 ff-merge** (2026-09-04): push·PR 없이 작업 브랜치를 default 브랜치에 `git merge --ff-only <slug>` 로 반영한 뒤 아래 (a) 자동 정리로 닫는다 — 오타 1줄에 PR 왕복을 붙이면 실제로는 머지하지 않고 worktree 만 쌓인다(그러면 (a) 의 merged 조건이 영영 안 걸린다). **ff 불가**(그 사이 default 가 진행)거나 medium 이상·CI 검증·외부 공유가 필요하면 `/e merge`(push→PR→머지). 어느 경로든 **push 는 요청 시만**이라 로컬 default 가 origin 보다 앞설 수 있다 — 다음 push 때 반영된다.
- **머지/완료 후 정리 — merged 면 묻지 말고 정리**(사용자 지시 2026-07-27): 작업 브랜치가 merged·정리해도 안전하면 worktree 정리를 방치·"선택사항" 언급만 하지 않고, **선택지로 올리지도 않는다**. **분기**:
  - **(a) merged + 안전조건 충족 → 확인 없이 worktree + 로컬 브랜치 자동 정리**. 조건 — ①대상 ≠ `main`/`master`/`origin/HEAD` ②**default 브랜치에 merged**(`git branch --merged <default>` 에 있음 — **로컬 main 머지도 포함**한다. push 하지 않는 워크플로우가 있어 `origin/<default>` 기준만 보면 영영 미머지로 오판한다. squash-merge 는 미감지 → (b)) ③working tree clean(untracked 포함) ④미보존 `.env`/ignored/미커밋 plan 없음. **누가 머지했는지는 묻지 않는다**(내 merge 든 우연히 merged 든 동일). 실행은 worktree → `git branch -d` 순, 삭제한 브랜치 tip sha 를 보고(merged 라 `git branch <name> <sha>` 로 복구 가능).
  - **(b) 확인 필요(AskUserQuestion)** — **원격 브랜치 삭제**(`git push origin --delete`)는 (a) 에 **포함되지 않는다: 항상 확인**. 그 외 안전조건 하나라도 미충족/불확실(dirty·squash-merge·미보존 산출물), `/wt rm <이름>` 직접 호출(오타로 엉뚱한 대상을 지울 수 있다) 도 확인. 이 경로에서 원격 삭제·`git branch -D` 는 명시 확인 없이 금지(데이터 유실 방지).
  - 조건·실행 세부는 `/e` step7·worktree 정리 규칙. `gh pr merge --delete-branch` 는 **명령으로 쓰지 않는다**(로컬·원격 삭제를 묶어 §8(b) 분리 승인을 우회하고, worktree 가 main 을 점유한 환경에선 로컬 삭제가 실패/스킵되어 정리만 조용히 누락 — 실측 2026-08-05, wiki `workflow-failures`). 사용자가 그 플래그로 머지를 지시했다면 원격 삭제 승인으로 간주하고, 실행은 `/e merge` 경로(`--merge` 후 정리)로 하되 7단계 뒤 원격 삭제 재확인은 그 승인으로 갈음한다. **main/master worktree 는 자동 정리 대상 아님.**
- generated/lock file 변경은 필요할 때만 포함, 이유 설명.
- `.env`/private key/token/password/인증서 원문을 답변·로그·테스트 fixture·snapshot 에 출력 금지.
- 인증/인가/암호화 코드는 기존 보안 패턴 먼저 확인. 임시 우회·hardcoded credential·TLS 검증 비활성화 금지.
- 외부 입력은 신뢰하지 않는다. validation/escaping/authorization check 확인.

---

## 9. Claude ↔ Codex 협업

사용자는 Claude 와 Codex 양쪽을 사용. 둘 다 같은 `.claude/plans/` 핸드오프 채널을 공유.

- **역할**: Claude 는 plan 생성/갱신·메인 구현·통합. Codex 는 리뷰·보조 구현·검증. 최종 통합 책임은 항상 **현재 메인 에이전트**.
- **호출**: 설치 확인 `codex --version`. **codex 는 반드시 Bash 도구로 호출한다**(PowerShell 은 stdin 미종료로 무한 hang — 재현). 호출 규약·effort·출력 처리 세부는 `docs/codex-review.md`.
- **리뷰 매트릭스**:
  - `plan-reviewer` / `code-reviewer` = **Claude subagent 필수 + Codex 가용 시 병행**. Codex 미가용이면 생략 사유를 Report 또는 plan `# Progress` 에.
  - `researcher` / 보조 구현 = 가용성·이득 있을 때 선택. (simplify 체크는 메인 직접 — 매트릭스 대상 아님)
- **공유 채널**: `.claude/plans/<dir>/<slug>-plan.md` 가 세션·도구 간 컨텍스트 채널(토큰 소진/세션 종료 시 이어받기용).

---

## 10. `.claude/plans/` 핸드오프 규약

티켓 ID 명시 작업 또는 컨텍스트 명확한 단위는 `.claude/plans/<YYYY-MM-DD>-<slug>/<slug>-plan.md` 사용. 파일명에 slug 가 있어야 `@` 자동완성에서 식별 가능.

### slug & 매칭
- slug: `<TICKET>-<short-desc>` 또는 `<short-desc>`. 디렉토리 prefix 는 시작일(불변, rename 금지).
- 매칭: 현재 git branch 가 slug 에 포함된 dir → 그 안의 `*-plan.md` 1개.
- **active plan 추적 (매칭 실패 대비 — 중요)**: branch 가 어떤 plan slug 와도 매칭 안 돼도, 세션에서 진행 중이던 plan 을 active 로 **계속 추적**한다. branch 매칭은 plan 을 *처음 찾는* 수단일 뿐 — 한번 active 가 된 plan 은 branch 를 바꾸거나 작업이 plan 범위 밖으로 확산돼도 동기화 대상에서 빠지지 않는다.

### 동작
- **시작**: 매칭 plan 있으면 read 후 컨텍스트 복원, 없으면 새로 생성(`status: in_progress`).
- **진행 중 동기화 (필수)**: plan 과 다른 결정/방향/스코프 변경이 발생하는 **즉시** 업데이트, 턴 종료까지 미루지 않는다.
  - 스코프 변경·접근/아키텍처 변경·새 제약 → `# Decisions` 에 변경 + **이유**(기존 결정은 지우지 말고 "~로 변경 (이유: …)" 덮어쓰기/추가).
  - `# Next` 가 다음 액션이 아니게 되면 → 즉시 교체.
  - 막힘 → `# Blockers` + `status: blocked`.
  - 핵심 파일 추가/이동 → `# Key Files` 동기화.
- **턴 종료**: `# Progress` 오늘 진행 한 줄, frontmatter `updated:` 오늘. 빠뜨린 동기화 보강.
- **완료**: 머지·배포·승인 **그 시점에 즉시** `status: done` — 미루지 않는다(`/e merge` 는 done 을 머지 PR 에 실어 보내고 머지가 거부되면 `in_progress` 로 복구한다). **블로커**: `status: blocked` + `# Blockers`.
- **원칙**: plan 은 "현재 상태의 단일 진실 소스". 합의가 plan 에 없으면 다음 세션/도구가 모른다 — 항상 plan 우선 반영.
- **동기화 (tracked)**: `plans/` 는 tracked(§8 whitelist `.gitignore`) — plan 을 작업 브랜치와 함께 commit·push 하면 다른 머신/세션이 pull 로 이어받아 "단일 진실 소스"가 머신 경계를 넘는다. secret 유출 방지: pre-commit-check 가 staged `plans/*.md` 토큰 스캔(+§8 원문 출력 금지) — plan 에 raw token/credential/PII 붙여넣기 금지.

### frontmatter (필수)
```yaml
---
title: <slug> — <한 줄 요약>
status: in_progress  # in_progress | blocked | done
started: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

### 본문 6개 섹션 (빈 채로라도 헤더 유지)
1. `# Goal` — 달성 목표 (1~3줄)
2. `# Progress` — 날짜별 진행 로그
3. `# Next` — **다음 즉시 액션 (가장 중요)**
4. `# Decisions` — 설계/스코프 합의 + 이유
5. `# Key Files` — 핵심 파일 + 한 줄 메모
6. `# Blockers` — 막힌 것 + 풀려면 필요한 것

선택 섹션 (해당 작업에서 필요할 때만): `# Acceptance`(test 가능한 완료 기준 — 각 항목이 증거(실행·관찰·통과)로 충족될 때만 완료, dlc evidence gate), `# Review Disposition`(dlc fix loop 의 finding 처분 — `fix`/`defer`/`false-positive`/`wontfix`), `# Deferred`(범위 밖 발견 — §3-4), `# Workflow Findings`(확인된 workflow 실패 기록 — dlc 증거기반 자기개선, 최소형). `defer`(리뷰 finding 처분값) ≠ `# Deferred`(범위 밖 발견 보존 섹션).

리뷰는 dlc 의 중간 단계(구현 직후 code-reviewer + codex 병행, §9)가 담당한다 — push 직전 별도 codex 리뷰는 두지 않는다. 로컬 다관점 점검이 따로 필요하면 빌트인 `/code-review` 를 수동 사용.

### 적용 범위
티켓 또는 명확한 작업 컨텍스트만. 단순 질문/탐색/한 턴짜리 명령은 제외.

---

## 11. 영속 프로젝트 메모리 (LLM Wiki)

이 repo·워크플로우의 누적 지식(아키텍처 결정·교훈·검증된 외부 사실)은 `wiki/`(스키마 `wiki/WIKI.md`)에 영속 적립 — `plans/`(일시적 핸드오프, 종료 시 닫힘)와 달리 작업을 가로질러 누적.

- 작업 시작 시 `wiki/index.md` 에서 관련 페이지 조회(있을 때만 — 없으면 무비용).
- 재사용 가능한 지식(비자명한 결정·교훈·확정한 외부 사실)은 **wiki 대상 여부 판정 필수** — 대상이면 `/wiki ingest` 제안(자동 아님), 비대상이면 사유. 강제는 아니되 *판정*은 빠뜨리지 않는다.
- raw 원문은 읽기 전용·gitignored. 페이지 write 규약은 `wiki/WIKI.md` 단일 소스.

---

## 12. 피드백 메모리 (교정의 반영 보장)

사용자가 작업 방식 교정을 영속화하라고 지시하면("기억해 / 규칙으로 / 다음부턴 이렇게") memory `type: feedback` 으로 저장. 목표는 저장이 아니라 **다음 작업에서의 실제 반영**.

- **인덱스를 행동 지시문으로.** `MEMORY.md` 인덱스 줄만 매 세션 항상 주입(본문은 관련 있을 때만 recall). 인덱스를 *정보 요약*이 아니라 **명령형 행동 규칙**으로: `notify-hook 알림 버그 메모` ❌ → `코드 변경 시 주석·문서도 같은 커밋에서 갱신` ✅. 본문엔 사례·Why·How.
- **저장은 2단계 — 둘 다.** 메모리 파일 + `MEMORY.md` 인덱스 한 줄. 인덱스를 빠뜨리면 본문이 묻혀 반영 안 됨(인덱스는 직접 갱신).
- **재참고 — 능동 확인.** 작업 시작 시(특히 dlc Explore) 관련 feedback 인덱스 줄을 의식적으로 확인해 적용. 상세·근거 필요하면 본문 read.
- **승격.** 보편·중대 규칙은 이 `CLAUDE.md` 로 승격(전문 100% 주입 + 명령조) 후 memory 정리. repo 한정 컨벤션은 그 repo `CLAUDE.md`(또는 wiki `decision/`).
- **유지.** 같은 주제는 기존 파일 갱신(중복 금지). 모순되면 옛 것 교체(이력은 git). 무효는 삭제 — 죽은 규칙도 인덱스로 주입돼 방해.

---

## 13. 실수·교훈 로그 (반복 방지)

작업 중 저지른 실수(내 오판·누락) 또는 사용자가 지적한 실패는, 같은 실수를 다음 작업에서 반복하지 않도록 적립 **대상으로 판정**한다. 목표는 기록이 아니라 **다음 구현에서의 회피**. wiki(상세)와 memory(자동 상기)를 **결합**한다 — wiki 만으로는 능동 조회라 자동으로 안 떠오르고, 인덱스 한 줄만으로는 원인·교훈이 묻힌다.
- **무승인 자동 적립 금지 (§1·2026-06-19 결정 유지).** 실수 발견은 자동 저장/수정이 아니라 **제안** — Report 또는 plan `# Workflow Findings`/`# Deferred`에 올리고, 승인·판정 후 적립한다([[self-diagnosis-and-improvement-status]]의 "자발적 무승인 기록 트리거 미채택"·§11 wiki ingest "제안 아님"과 동일 게이트). §13 은 *적립할 때의 형식*을 정하지, 무인 자동화를 도입하지 않는다.

- **상세 = wiki `pages/decision/lesson-<주제>.md`.** 원인(최소 3 Whys)·재현 조건·잘못된 방법·올바른 방법. 기존 [[workflow-failures]] 와 같은 ADR-lite 형식(§11). `index.md`·`log.md` 동기화 동반.
- **자동 상기 = `MEMORY.md` feedback 인덱스 한 줄(명령형 + lesson 링크).** wiki 는 자동 주입 안 되고, 매 세션 주입되는 유일한 경로는 이 인덱스 줄이다. *정보 요약이 아니라 회피 행동 지시*로 쓴다(§12): `마이그레이션 down 스크립트 먼저 작성 (롤백 불가 실수 → lesson-migration)`.
- **메커니즘은 §11·§12 그대로** (저장 2단계·승격·재참고를 재서술하지 않는다). **§13 의 순증분은 대상 확대뿐** — §12 가 "사용자 교정 지시"라면 §13 은 **내가 능동 발견한 실수(사용자 지시 없이도)** 까지 (위 무승인 게이트 하에서) 포함. **적립은 매 실수마다 의무가 아니라 판정·제안**(위 무승인 금지) — 반면 *승인되어 만들어진* 인덱스 줄은 §12 대로 매 세션 주입("적립 의무"와 "인덱스 주입"은 별개). 회피를 hook 으로 강제할 만큼 반복되면 게이트(Stop/UserPromptSubmit)로 승격.

@RTK.md
