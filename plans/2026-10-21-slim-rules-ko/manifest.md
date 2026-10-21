# CLAUDE.md 규칙 목록 (slim-rules-ko)

origin/main 5555fc6 의 CLAUDE.md(268줄·49,942B) 기준. 한 줄 = 한 조항(긴 불릿은 조항마다 나눈다 — "예외 없이"·"포함"·"항상" 같은 한정어도 조항의 일부).
등급 — 인라인: CLAUDE.md 에 명령형으로 남는다 · 세부: 규칙 줄은 CLAUDE.md 에 남고 세부는 적힌 다른 파일에 이미 있다 · 이력: 괄호 안의 근거 표시(버전 번호·측정값·"재현"·"선례"·"실측") — 지우고, wiki 에 없으면 Deferred · 이유: 규칙의 근거 문장 — 짧게 남기거나, 규칙만으로 적용할 수 있으면 지운다 · 신규: 이번에 더하는 규칙 · 중복: CLAUDE.md 다른 절에 같은 조항이 있어 한 곳만 남긴다.
새 위치(단위 2 뒤에 채움): `§N «인용»` — 인용은 새 CLAUDE.md 에서 글자 그대로 찾히는 구절. 다른 파일이면 `경로 «인용»`. CLAUDE.md 를 다시 가리키는 파일(예: `skills/dlc` 16단계 "조건과 금지는 §8 단일 소스")은 새 위치가 될 수 없다. 규칙이 적용되는 시점을 정하는 날짜는 이력이 아니라 규칙이다.
§8 과 §10 은 이관 없이 표현만 줄인다 — `skills/dlc` 가 §8 을 단일 소스로 가리키고, §10 은 c·e·dlc 가 가리킨다([[ops-doc-slimming]] 방향 역전 금지).

## 머리말
- H.1 실행 불가능한 지시는 추측 말고 이유를 명시 — 인라인 → 머리말

## §0 응답 언어·표기
- 0.1 한국어로 답, 식별자·파일명·함수명·라이브러리명·에러 메시지는 원문 — 인라인 → §0
- 0.2 인사말 없이 내용부터 — 인라인 → §0
- 0.3 보이는 텍스트: 첫 도구 호출 전 한 문장, 중요한 발견·방향 전환 때, 긴 도구 호출 중 짧은 업데이트, 끝나면 결론 요약 — 인라인 → §0
- 0.4 비유·수사 대신 직설(예: "다이얼" → "파라미터") — 인라인 → §0
- 0.5 원문자(①②③) 금지 — 나열 `1.`, 눈에 띄는 단계·선택지 `## 1) 제목`, 문장 중 `1)`·`(1)` — 인라인 → §0
- 0.6 원문자로 된 기존 문서(`skills/`·`wiki/docs/`·`plans/`) 인용은 원문 그대로 — 인라인 → §0
- 0.m0 사용자는 도구 출력 원문을 따라 읽지 않는다(0.3 의 이유) — 이유 → 짧게 유지
- 0.m1 원문자는 터미널에서 작게 렌더된다 · 수사는 독자를 더 일하게 한다 — 메모(이유) → 삭제, 규칙만으로 적용 가능

## §1 핵심 규칙
- 1.1 추측 금지, 모르면 모른다고 — 인라인 → §1
- 1.2 중요한 판단·원인 분석엔 확신도 ✅확실(파일·실행결과·공식문서)/⚠️추정(정황만)/❌모름 — 인라인 → §1
- 1.3 추천은 근거와 함께, 확인 못 한 안은 ⚠️추정으로 — 신규 → §1
- 1.4 코드베이스 답은 관련 파일을 read 한 뒤, 기억으로 답하지 않음, 못 찾으면 명시, 확인한 주요 파일을 짧게 — 인라인 → §1
- 1.5 근본 원인 수정, 증상 억제 금지(에러 무시·테스트 약화·`except: pass`·무의미한 retry) — 인라인 → §1
- 1.6 버그·장애엔 최소 3 Whys(오타·포맷은 생략) — 인라인 → §1
- 1.7 원인이 고칠 수 없는 외부 요소여도 촉발 계기까지 내려가 통제 가능한 대책 — 인라인 → §1
- 1.8 재부팅·재설치처럼 상태를 지우는 조치 전에 그 상태에서만 가능한 진단(위험하면 시점 조율) — 인라인 → §1
- 1.9 lint/typecheck/test/build 실행·통과 뒤에만 완료 — 인라인 → §1
- 1.10 명령이 없으면 README/CI 에서 찾는다 — 인라인 → §1
- 1.11 `~/.claude` 검증은 `bash scripts/verify.sh changed`(관련 없는 느린 테스트는 `[slow]` 로 건너뜀), 전 축은 CI·사용자 주기 실행 — 인라인 → §1
- 1.12 `ALL PASS (skip: …)` 를 통과로 읽지 않는다 — 인라인 → §1
- 1.13 검증 불가면 이유+수동 절차, 미검증이면 완료 금지 — 인라인 → §1
- 1.14 통과해도 목표 대비 충족 확인(통과 ≠ 완료) — 인라인 → §1
- 1.m1 전 축이 Windows 약 50분 이상 · `package.json` 없어 `npm test` 없음 · CI 도 같은 스크립트를 축별로 호출 — 메모 → wiki(Deferred)·README
- 1.15 사용자가 틀리면 정중히 반박, 아부 금지, 근거로 설명 — 인라인 → §1
- 1.16 내 추천은 새 근거가 있을 때만 바꾸고 그 근거를 말한다 — 사용자가 다시 묻는 것만으로 바꾸지 않는다 — 신규 → §1
- 1.16b 사용자가 결정하면 따르되(§8 의 금지는 그대로), 새 근거 없이 내 추천이 바뀐 것처럼 말하지 않는다 — 신규 → §1
- 1.17 작업 전 `git status --short`, 덮어쓰지 않음, 변경이 예상보다 많으면 멈추고 원인 확인 — 인라인 → §1
- 1.18 확인(`AskUserQuestion`)은 비가역·외부공개·파괴적에만: push·머지·원격/강제 삭제·배포·DB write·외부 전송·비용 — 인라인 → §1
- 1.19 로컬·한 명령으로 되돌림·데이터 안 지움(worktree/브랜치 생성·편집·로컬 실행)은 묻지 말고 실행, 되돌릴 정보를 보고 — 인라인 → §1
- 1.20 애매하면 확인 — 인라인 → §1
- 1.20b 예외: trivial·small 의 로컬 `--ff-only` 반영과 그 뒤 §8(a) 정리는 §8 대로 묻지 않는다 — 신규(모순 2) → §1
- 1.21 방향 합의(§3-3 plan 승인·요구 명확화)는 위험도와 무관 — 인라인 → §1
- 1.22 상세 [[risk-based-approval]] — 인라인(포인터) → §1
- 1.m2 무해한 단계마다 승인은 마찰만 늘린다 — 메모(이유) → 삭제, [[risk-based-approval]] 에 있음
- 1.23 운영 자산(CLAUDE.md·agents/·skills/·settings)은 명시 요청 없이 수정 금지, 요청 = active plan `# Goal`/`# Tasks`(옛 형식 `# Key Files`)에 그 자산 또는 자산명+변경 지시 — 인라인 → §1
- 1.24 발견한 개선점은 Report 제안(문제+근거+제안), 적용은 승인 후 별도 작업 — 인라인 → §1

## §2 컨텍스트 관리
- 2.0 세션이 길수록 성능이 떨어진다 — 컨텍스트가 가장 중요한 자원 — 인라인 → §2
- 2.1 진행 중 작업은 compaction 이 이어 주므로 길다는 이유로 정리를 권하지 않는다 — 인라인 → §2
- 2.2 `/clear`·`/rewind`·`Esc` 는 사용자 컨트롤 — 제안만 — 인라인 → §2
- 2.3 진행 중 작업엔 `/clear` 를 권하지 않음, 줄여야 하면 `/compact` — 인라인 → §2
- 2.4 `/clear` 제안은 (a) 무관한 작업 전환 (b) 같은 이슈 2회+ 교정 실패 뒤 학습 요약 재시작만, 직전 clear/compact 면 재권유 금지 — 인라인 → §2
- 2.5 조사·리서치는 subagent 가용·이득 클 때 위임, 아니면 직접 하되 읽는 파일 수 제한 — 인라인 → §2
- 2.6 잘못된 방향이면 즉시 중단, `Esc`/`/rewind` 제안 — 인라인 → §2
- 2.7 여러 줄·명령치환·체인이 많은 셸 명령은 `Write` 로 스크립트에 적고 한 줄로 실행 — 인라인 → §2
- 2.7b 이유: 인용 오류와 권한 프롬프트가 줄고 재실행이 쉽다 — 이유 → 짧게 유지
- 2.8 예외: Monitor·`run_in_background` 장기 루프는 명령에 직접 쓰거나 스스로 끝나는 조건(최대 실행 시간)을 두고, 재실행 전 이전 루프 확인 — 인라인 → §2
- 2.m1 Windows `bash <스크립트>.sh` 가 하네스 프로세스 트리에서 떨어져 남는다(재현) — 메모 → 이미 [[windows-bash-tool-orphan-processes]], 링크 유지
- 2.9 Bash 재귀 검색은 `grep -r` 대신 `rg`(Grep 도구도 가능) — 인라인 → §2
- 2.10 ignored 까지 찾을 때만 `rg -uu` — 인라인 → §2
- 2.11 `~/.claude` 의 `wiki/`(`wiki/docs/` 포함)는 ignored — 영향 범위 조사에서는 경로를 명시, 무매칭 ≠ 영향 없음 — 인라인 → §2
- 2.m2 rtk 가 단순 `grep` 을 시스템 grep 으로 바꿔 `.gitignore` 를 무시, 파이프 안은 ugrep, `rg` 는 `rtk rg` 로 `.gitignore` 를 따름 — 메모 → 이미 [[claude-code-bash-tool-shims]], 링크 유지
- 2.m3 독립 `rg` 실행 파일 필요(macOS bootstrap 설치, Windows 수동) — 메모 → README 확인 후 없으면 Deferred

## §3 작업 흐름
- 3.1.1 Setup 은 `git status --short` — 중복(1.17) → §1 한 곳, §3-1 은 참조
- 3.1.2 프로젝트 컨텍스트는 per-repo `CLAUDE.md`(또는 `.claude/CLAUDE.md`), 없으면 비어 있다 — 인라인 → §3-1
- 3.1.3 `.env`/key/token/cert 원문 출력 금지 — 중복(8.32) → §8 한 곳
- 3.1.4 코드/파일 변경은 규모 불문(trivial 포함) worktree 밖이면 `wt` 먼저, 그 안에서 dlc, main 직접 금지 — 인라인 → §3-1
- 3.1.5 `guard-worktree-edit.js` 는 main 추적파일 편집에 ask 를 걸지만 auto 모드에서는 걸지 않는다 — 인라인 → §3-1 (모순 4: 주어를 hook 으로)
- 3.1.5b 게이트가 안 걸렸다고 worktree 를 건너뛰지 않는다 — 인라인 → §3-1
- 3.1.6 이미 worktree 안이면 dlc self-check — 인라인 → §3-1
- 3.1.7 trivial 은 절차(리뷰·plan·TDD)만 통과, worktree 는 필요 — 인라인 → §3-1
- 3.1.8 worktree 를 만들지 않는 예외: 사본 없는 글로벌 상태(`projects/…/memory/`·`MEMORY.md`·`settings.local.json`·공용 wiki `wiki/`·`wiki/docs/`)·비-git — 인라인 → §3-1
- 3.1.9 worktree 세션 안에서는 네이티브 격리가 그 main 경로 편집을 거부 — memory 적립·공용 wiki 쓰기는 main 복귀 후(복귀는 `/e` 8단계, 적립은 복귀한 main 에서 직접) — 인라인 → §3-1
- 3.1.m1 거부 메시지가 "worktree 사본을 편집하라" 고 해도 그 사본은 없다 — 인라인(짧게) → §3-1 (잘못된 메시지를 따르지 않게)
- 3.1.m2 `guard-worktree-edit.js` 는 allow 하나 네이티브 격리가 그 위에 있다 — 이유 → 삭제
- 3.1.10 상세는 `skills/dlc/SKILL.md` — 인라인(포인터) → §3-1
- 3.2 Explore: 모호하면 질문 먼저, 관련 파일+호출부 read, 같은 레이어 스타일 확인 — 인라인 → §3-2
- 3.3 큰 변경(50줄+·다중 파일·public API·DB schema·migration·아키텍처/보안)은 계획 승인 먼저, 작은 변경은 즉시 — 인라인 → §3-3
- 3.4.1 작은 단계, 범위 밖 수정 금지, 빌드/테스트를 깨는 직접 원인은 고치고 이유 — 인라인 → §3-4
- 3.4.2 범위 밖 발견은 고치지 말고 plan log `# Deferred`(plan 없으면 Report)에 한 줄(내용·심각도·파일)로 남기고 진행 — 인라인 → §3-4
- 3.5.1 lint/typecheck/test 실행, 변경 함수/클래스 호출부를 `rg` 로 확인, 미실행은 "미검증" — 인라인 → §3-5
- 3.5.2 이번 변경이 깨뜨린 것만 수정, baseline failure 는 입증된 것만 Deferred, 입증 안 되거나 완료를 막으면 수정 또는 blocked/"미검증" — 인라인 → §3-5
- 3.5.3 주석·docstring·commit message 가 현재 동작과 맞는지(리팩토링·rename·fixup 뒤) — 인라인 → §3-5
- 3.5.4 비trivial 은 `# Acceptance` 를 증거로 대조한 뒤에만 완료 — 인라인 → §3-5 (모순 9: plan 없이 가는 small 은 Acceptance 가 없다 — "(plan 없이 가는 small 은 검증 결과로)" 를 더한다)
- 3.5.5 실행 산출물(render/CLI/서버)은 실제 실행·관찰 — 인라인 → §3-5
- 3.6.1 Report 항목: 변경 요약/수정 파일/검증 결과/영향 범위/남은 리스크 — 인라인 → §3-6
- 3.6.2 이어서 AskUserQuestion 선택지: 작업 확인 / 마무리·정리(`/e merge`·`/e` — 수동 대체 금지) / 다른 작업(`/wt` 신규) / 종료 — 인라인 → §3-6
- 3.6.3 최신 사용자 메시지에 명시적 다음 액션이 있으면 선택지 생략(중복 질문 금지) — 인라인 → §3-6
- 3.6.4 Stop hook 경고가 오탐이면 한 줄 응답(재종료는 통과) — 인라인 → §3-6
- 3.6.5 판단 과정 서술 금지 — 오탐 사유는 plan log `# Workflow Findings`(누적 시 공용 wiki `workflow-failures.md`, main 세션·다른 repo 는 §11 제안) — 인라인 → §3-6
- 3.7 문서 동기화: README 문서화 컴포넌트에 영향이면 같은 브랜치에서 README 갱신(acceptance 항목), `wiki/pages/` 변경은 `wiki/index.md` 동반, hook 은 보조 — 인라인 → §3 끝
- 3.8 subagent 병렬화: 파일 소유권 분리(spawn 시 범위 명시, 겹치면 순차), 통합은 메인 — 인라인 → §3 끝

## §4 웹 검색
- 4.1 컷오프 이후·외부 사실이면 "모르겠다/아마" 전에 WebSearch/WebFetch — 인라인 → §4
- 4.1b 검색 임계값을 의식적으로 낮춘다(로컬 코드에 빠져 검색을 잊기 쉽다) — 인라인 → §4
- 4.2 검색 신호: 버전별 동작·마이그레이션·최신 API · 정확한 에러 메시지 · release notes·알려진 버그 · CVE·RFC · 컷오프 이후 도구·정책 · 추천하려는 함수/플래그 실존 불확실 · 이름을 알아도 현재 상태가 불확실(모델·개발 도구처럼 수개월 단위로 바뀌는 영역) — 인라인 → §4
- 4.3 검색 안 함: 표준 언어 기능·정착된 패턴·코드베이스 내부 사실 — 인라인 → §4
- 4.4 우선순위: 공식 문서 > release notes/issue > SO > 블로그 — 인라인 → §4
- 4.5 이름은 사용자 표기 그대로 최소 1회 검색 — 인라인 → §4
- 4.m1 "부분 배경지식이 낡은 답을 그럴듯하게" · "재표현만 하면 엉뚱한 대상" — 이유 → 짧게 하나만 남기거나 삭제

## §5 Sub-agent
- 5.1 정의는 `.claude/agents/`(프로젝트 우선, 없으면 `~/.claude/agents/`), 없으면 지어내지 말고 같은 관점으로 직접 점검 — 인라인 → §5
- 5.2 Codex 검토는 §9 — 인라인(포인터) → §5
- 5.3 plan-reviewer: 비사소한 plan 직후, 묶음 경계는 묶음 모드로 1회 — 인라인 → §5
- 5.4 researcher: §4 신호 때 어느 단계든 — 인라인 → §5
- 5.5 code-reviewer: 코드 변경이 있는 모든 흐름 — 인라인 → §5 (모순 8: dlc trivial 행은 리뷰를 건너뛴다 — "trivial 이 아닌" 으로)
- 5.6 simplify 체크: 메인 직접, code-reviewer 통과·blocker 해소 뒤(dlc 13단계), 중복·과한 추상화·불필요한 복잡도·죽은 코드 제거, 동작 보존, 불확실하면 보류(제안만), 코드를 바꿨으면 검증 재실행 — 인라인 → §5
- 5.7 simplify 는 trivial 이 아닌 코드 변경에 필수, 못 했으면 사유를 Report — 인라인 → §5 (모순 1 수정)
- 5.8 architecture-reviewer: 트리거 기반 — public API/DB schema/auth·신규 service/repository/client·DI·2계층+·설계 의문 — 인라인 → §5
- 5.9 표준 순서 plan-reviewer → 구현 → code-reviewer → simplify → 최종 검증 — 인라인 → §5
- 5.10 Workflow `agent()` 는 `model` 생략(세션 상속), `effort` 항상 명시 — 생략하면 세션 레벨을 상속 — 인라인 → §5
- 5.11 effort: low 탐색·grep·목록·테스트 실행·기계적 변환 / medium 구현·단순 리팩토링 / high 검증·adversarial verify·judge·복잡한 디버깅 / xhigh·max 명시적으로 어려운 판정만 — 인라인 → §5
- 5.12 결과 통합·최종 판단은 스크립트가 아니라 메인 — 인라인 → §5
- 5.13 `agentType` 으로 정의를 쓰면 그 frontmatter `model` 이 세션 모델보다 우선 — 인라인 → §5
- 5.14 Agent 도구 effort 는 정의 frontmatter, 도구 `effort` 파라미터는 사용자·skill 이 명시했을 때만 — 인라인 → §5
- 5.m1 ultracode 는 세션 레벨을 두는 토글(v2.1.284+), `--effort ultracode`·SDK `effortLevel` — 메모 → wiki 확인 후 없으면 Deferred

## §6 코드 규칙
- 6.1 새 코드 전 같은 디렉토리·레이어 파일 read, 네이밍·에러 처리·로깅·import 순서 맞춤 — 인라인 → §6
- 6.2 새 의존성 전 기존/표준으로 가능한지, 추가하면 이유·대안·영향 — 인라인 → §6
- 6.3 Python production type hint, 데이터 경계는 Pydantic 또는 기존 검증 — 인라인 → §6
- 6.4 주석은 없는 게 기본, 코드에 안 드러나는 왜만 최소 줄, docstring·테스트 주석도 — 인라인 → §6
- 6.5 변경 경위는 주석이 아니라 커밋/PR — 인라인 → §6
- 6.6 임시 코드 `# TODO: <이유> (<제거 조건/이슈>)` — 인라인 → §6
- 6.7 죽은 코드는 삭제 — 인라인 → §6
- 6.8 부분 편집 우선(`Edit`), 통째 덮어쓰기는 신규·짧은 파일·대부분 바뀔 때 — 인라인 → §6
- 6.8b 결과가 같으면 출력 토큰·시간이 적은 쪽 — 인라인 → §6
- 6.9 추측한 API/함수/라이브러리 이름 금지 — 인라인 → §6
- 6.10 로그에 token/password/key/인증서/PII 금지 — 인라인 → §6

## §7 테스트
- 7.1 로직 추가/수정엔 테스트, 순서 작성 → Red → 구현 → Green → refactor — 인라인 → §7
- 7.2 예외는 사유를 명시 — 인라인 → §7
- 7.2b 사소한 변경: 1줄 수정·오타·주석·포매팅·import·로그 메시지 — 인라인 → §7
- 7.2c 기존 테스트로 회귀가 커버되는 단순 리팩토링(통과 확인 필수) — 인라인 → §7
- 7.2d UI 시각 확인·외부 인프라·훅/스크립트 → 수동 검증 절차 명시 — 인라인 → §7
- 7.3 버그는 가능하면 재현 테스트 먼저 — 인라인 → §7
- 7.4 테스트 약화/삭제는 이유, 기대값 낮추기 금지 — 인라인 → §7
- 7.5 테스트 규모는 인접 파일에 맞춤(동작당 1개 정도, 경계·오류는 그 동작의 일부), scratch 승격 금지, 덤 금지 — 인라인 → §7
- 7.6 flaky 는 원인·재현 조건·임시 대응 분리 기록 — 인라인 → §7
- 7.7 외부 API/DB/네트워크/시간 의존은 기존 mocking 패턴 — 인라인 → §7

## §8 Git / 보안 (이관 없이 표현만 줄인다)
- 8.1 `git reset --hard`·`git clean -fd`·강제 checkout·force push 는 명시 요청 없으면 금지 — 인라인 → §8
- 8.2 작업은 main/master 직접 말고 별도 브랜치/worktree — 인라인 → §8
- 8.3 main/master push 는 전역 `ask` 로 매번 확인이 뜬다 — 인라인 → §8
- 8.3b `allow` 로는 풀리지 않는다 — 풀려면 `ask` 규칙 자체를 지운다 — 인라인 → §8
- 8.3c 전역 `deny` 는 두지 않는다(프로젝트 범위 지정이 안 되고 allow 보다 우선해 `~/.claude` 도 막는다) — 인라인 → §8
- 8.m1 deny → ask → allow 평가 순서와 공식 문서 인용 — 이유 → 이미 `~/.claude/wiki/pages/decision/risk-based-approval.md` «deny → ask → allow»
- 8.4 다른 repo 의 main push 는 그 repo 에 `scripts/install-hooks.sh`(`.ps1`)로 훅을 설치했을 때만 `pre-push` 가 하드 차단(repo 별 opt-in) — 인라인 → §8
- 8.4b 전역 `core.hooksPath` 는 두지 않았고, `core.hooksPath` 가 다른 디렉토리를 가리키면 설치가 거부된다(`scripts/install-hooks.sh` «Not installing») — 인라인 → §8 (모순 10: 옛 문구 "설치해도 무효")
- 8.4c `pre-commit-check`(pre-push 모드)의 main push 차단은 repo 루트 `~/.claude` 만 면제 — 세부 → README «repo 루트가 `~/.claude` 면 면제»
- 8.4d 어느 repo 든 이 규약과 `permissions.ask` 의 `git push` 확인(rtk 재작성 형태 포함)이 겹친다 — 이유 → 삭제(8.3·8.4 로 충분)
- 8.5 코드/파일을 바꾸는 작업은 시작 시 별도 worktree(`/wt <요청사항>`), trivial 포함, 글로벌 상태·비-git 제외 — 중복(3.1.4·3.1.7·3.1.8) → §3-1 한 곳 + §8 에 참조 1구절
- 8.m3 main 에서는 커밋하지 않으므로 main 에서 고친 수정은 커밋될 길이 없다 — 이유 → 삭제
- 8.6 진행 중인 worktree 에 새 작업을 얹지 않는다(base·체크아웃 충돌, 변경 혼입, 동시 편집) — 인라인 → §8
- 8.6b 무관한 변경을 한 브랜치에 섞지 않는다 — 인라인 → §8
- 8.7 push 는 요청 시만 — 인라인 → §8 (skills/e 가 «push 는 요청 시만» 을 인용)
- 8.8 검증 통과한 작업 단위는 요청 없이 커밋한다 — 인라인 → §8
- 8.8b 하네스 기본값(`Commit or push only when the user asks.`)을 이 규약이 대체한다 — 인라인 → §8 (지우면 Bash 도구 설명의 기본값이 이긴다)
- 8.9 작업 브랜치에서 evidence gate·plan 업데이트를 마친 뒤 마지막에 1회가 기본 — 인라인 → §8
- 8.9b medium 이상·목적 2개 이상이면 dlc 가 목적 단위로 중간 커밋(각 단위 targeted 검증 뒤) — 인라인 → §8 (세부 `skills/dlc/SKILL.md` "커밋 단위")
- 8.9c 그 밖의 흐름에서도 검증된 중간 커밋은 막지 않는다 — 인라인 → §8
- 8.10 stage 는 이번 작업이 건드린 경로만 — 자동 커밋에서 `git add -A` 금지 — 인라인 → §8
- 8.10b 이유: 무관한 변경·산출물이 섞이고 `pre-commit-check` 시크릿 스캔은 `settings.json`·`plans/*.md` 만, 비공개 용어 검사는 목록에 적은 이름만 본다 — 이유 → 짧게 유지
- 8.10c `/e` WIP 체크포인트는 전량 보존이 목적이라 예외 — 인라인 → §8
- 8.11 커밋 직전 `git diff --cached --name-only` 로 index 확인, 작업 밖 항목이 이미 staged 면 보류·보고 — 인라인 → §8
- 8.12 커밋하지 않는 경우 1: 현재 브랜치가 main/master 또는 detached HEAD — 인라인 → §8
- 8.12b 그 예외: 공용 wiki repo `~/.claude/wiki` 의 페이지·문서는 main 에 직접 커밋(§11), 그 repo 의 코드 계층은 예외가 아니다 — 인라인 → §8
- 8.12c 이미 main 에서 편집했으면 `/wt` 로 옮겨 재적용한 뒤 그 절차를 보고, main 에 uncommitted 로 방치하지 않는다 — 인라인 → §8
- 8.12d 이유: 게이트가 auto 모드·untracked·fail-open 으로 안 걸렸을 때 도달할 수 있다 — 이유 → 짧게 유지
- 8.13 커밋하지 않는 경우 2: 검증 실패(§3-5 로 입증된 baseline failure 제외) — 인라인 → §8
- 8.13b 커밋하지 않는 경우 3: stage 할 변경 없음(빈 커밋 금지) — 인라인 → §8
- 8.14 커밋이 훅에 차단되면 `--no-verify` 금지 — 원인을 없애거나 보고 후 중단 — 인라인 → §8
- 8.15 확인·검증되지 않은 변경은 커밋하지 않는다 — 검증 수단은 실제 실행·관찰 / §7 예외의 수동 검증 절차 / 사용자 확인 — 인라인 → §8
- 8.15b 그 셋 중 하나로 검증하지 못했으면 커밋하지 않고 검증 방법을 묻는다 — 인라인 → §8
- 8.15c 커밋해 두고 보고에 "미검증" 을 적는 방식은 쓰지 않는다 — 인라인 → §8
- 8.15d 물을 수 없는 무인 흐름이면 커밋을 보류하고 보고 — 인라인 → §8
- 8.16 규칙·스킬 문구처럼 모델 행동을 바꾸는 변경은 사용자가 바뀐 문구(diff)를 확인했거나 실제 세션에서 관찰했을 때 검증된 것 — 인라인 → §8
- 8.17 대상은 작업 변경 — 검증을 마친 작업의 기록 파일(plan) 커밋과 사용자 승인으로 하는 `commit-check` 재구성은 따로 검증하지 않는다 — 인라인 → §8
- 8.17b 예외: `/e` 의 `wip:` 체크포인트(작업 브랜치 한정)와 공용 wiki repo 의 main 직접 커밋 — 인라인 → §8
- 8.18 자동인 것은 커밋까지, push 는 요청 시만 — 중복(8.7) → §8 한 곳
- 8.18b 절차 세부(메시지 형식·경로 확정·실행 폴백)는 `skills/dlc/SKILL.md` 16단계 — 인라인(포인터) → §8
- 8.19 커밋은 리뷰 가능한 하나의 목적 단위 — 인라인 → §8
- 8.19b 미push 커밋의 같은 작업 후속 수정(리뷰 반영·오타·단순 실수)은 대상 커밋에 합친다(쌓는 중이면 `git commit --fixup=<대상>`) — 인라인 → §8
- 8.19c 목적이 섞인 커밋은 나눈다 — 인라인 → §8
- 8.19d 이미 push 한 커밋은 고치지 않고 새 커밋(force-push 금지) — 인라인 → §8
- 8.20 메시지 형식 정본은 그 repo 의 AGENTS/CLAUDE 커밋 절 — 인라인 → §8
- 8.21 점검·재구성은 `commit-check` 스킬 — 미게시 커밋만, 사용자 승인 후, 코드 내용은 그대로(plumbing 재조립이라 `--no-verify` 가 아니다) — 인라인 → §8
- 8.22 worktree 의 worklog 는 그 worktree 를 지우기 전에 남긴다 — 지우면 이름으로 고를 수 없어 등록할 수 없다(표시만) — 인라인 → §8
- 8.22b `/e` 6단계(worklog)를 7단계 삭제보다 먼저 — 인라인 → §8
- 8.m5 AI 작업시간은 줄 단위 `cwd` 로 갈린다 · main 복귀 뒤 이름 인자로 돌려도 된다 — 세부 → `skills/e/SKILL.md` 6단계 «귀속은 줄 단위 cwd 기준»
- 8.23 `git worktree remove` 는 gitignored 파일(`.env` 등)을 경고 없이 함께 지운다 — 인라인 → §8
- 8.23b 삭제 전 `git status --porcelain --ignored` 점검 — 인라인 → §8
- 8.23c `plans/` 는 tracked 라 미커밋 plan 은 remove 가 거부하지만, 미커밋 plan·log 변경은 삭제 전 커밋·push 로 보존 — 인라인 → §8
- 8.23d 상세는 `skills/e/SKILL.md` — 인라인(포인터) → §8
- 8.24 trivial·small 의 종결은 push·PR 없이 로컬 `git merge --ff-only <slug>` 로 default 에 반영한 뒤 (a) 자동 정리 — 인라인 → §8
- 8.24b 이유: 오타 1줄에 PR 왕복을 붙이면 머지하지 않고 worktree 만 쌓여 (a) 의 merged 조건이 안 걸린다 — 이유 → 짧게 유지
- 8.25 ff 불가면 작업 브랜치가 미게시일 때 worktree 안에서 `git rebase <default>` → 검증 재실행 → `--ff-only` — 인라인 → §8
- 8.25b rebase 충돌은 `git rebase --abort` 로 되돌린다 — 인라인 → §8
- 8.25c 충돌·이미 게시됨·medium 이상·CI 검증·외부 공유가 필요하면 `/e merge`(push→PR→머지) — 인라인 → §8
- 8.25d `/e merge` 는 plan 이 있어야 하므로 plan 없는 small 이면 plan 을 먼저 만든다 — 인라인 → §8
- 8.25e push 는 요청 시만이라 로컬 default 가 origin 보다 앞설 수 있다 — 다음 push 때 반영 — 인라인 → §8
- 8.26 merged·안전하면 worktree 정리를 방치하거나 "선택사항" 으로만 말하지 않고 선택지로 올리지도 않는다 — 인라인 → §8
- 8.27 (a) merged + 안전조건 충족 → 확인 없이 worktree + 로컬 브랜치 자동 정리 — 인라인 → §8(a)
- 8.27b 조건 1) 대상 ≠ `main`/`master`/`origin/HEAD` — 인라인 → §8(a)
- 8.27c 조건 2) default 브랜치에 merged(`git branch --merged <default>`) — 로컬 main 머지도 포함, squash-merge 는 감지 못 해 (b) — 인라인 → §8(a)
- 8.27d 이유: push 하지 않는 워크플로우에서 `origin/<default>` 기준만 보면 영영 미머지로 오판 — 이유 → 짧게 유지
- 8.27e 조건 3) working tree clean(untracked 포함) — 인라인 → §8(a)
- 8.27f 조건 4) 미보존 `.env`/ignored/미커밋 plan·log 없음 — 인라인 → §8(a)
- 8.27g 누가 머지했는지 묻지 않는다 — 인라인 → §8(a)
- 8.27h 실행은 worktree → `git branch -d` 순, 삭제한 브랜치 tip sha 보고(`git branch <name> <sha>` 로 복구) — 인라인 → §8(a)
- 8.28 (b) 원격 브랜치 삭제(`git push origin --delete`)는 (a) 에 포함되지 않는다 — 항상 확인 — 인라인 → §8(b)
- 8.28b 안전조건 하나라도 미충족·불확실(dirty·squash-merge·미보존 산출물)이면 확인 — 인라인 → §8(b)
- 8.28c `/wt rm <이름>` 직접 호출도 확인(오타로 엉뚱한 대상을 지울 수 있다) — 인라인 → §8(b)
- 8.28d 이 경로에서 원격 삭제·`git branch -D` 는 명시 확인 없이 금지 — 인라인 → §8(b)
- 8.29 조건·실행 세부는 `/e` 7단계·worktree 정리 규칙 — 인라인(포인터) → §8
- 8.29b `gh pr merge --delete-branch` 는 명령으로 쓰지 않는다 — 인라인 → §8
- 8.29c 이유: 로컬·원격 삭제를 묶어 (b) 분리 승인을 우회하고, worktree 가 main 을 점유하면 로컬 삭제가 조용히 빠진다 — 이유 → 짧게 유지(사례는 [[workflow-failures]])
- 8.29d 사용자가 그 플래그로 머지를 지시했으면 원격 삭제 승인으로 보고 `/e merge` 경로(`--merge` 후 정리)로 실행, 7단계 뒤 원격 삭제 재확인은 그 승인으로 갈음 — 인라인 → §8
- 8.30 main/master worktree 는 자동 정리 대상이 아니다 — 인라인 → §8
- 8.31 generated/lock file 변경은 필요할 때만, 이유 설명 — 인라인 → §8
- 8.32 `.env`/private key/token/password/인증서 원문을 답·로그·테스트 fixture·snapshot 에 출력 금지 — 인라인 → §8
- 8.33 인증/인가/암호화는 기존 보안 패턴 먼저 — 임시 우회·hardcoded credential·TLS 검증 비활성화 금지 — 인라인 → §8
- 8.34 외부 입력은 신뢰하지 않는다 — validation/escaping/authorization 확인 — 인라인 → §8

## §9 Claude ↔ Codex
- 9.1 사용자는 Claude·Codex 를 둘 다 쓰고 `plans/` 를 공유 — 인라인 → §9
- 9.2 역할: Claude plan·메인 구현·통합, Codex 리뷰·보조 구현·검증, 최종 통합은 현재 메인 — 인라인 → §9
- 9.3 codex 는 반드시 Bash 도구로, 세부 `~/.claude/wiki/docs/codex-review.md`(부르기 전에 읽는다) — 인라인 → §9
- 9.3b 설치 확인 `codex --version` — 인라인 → §9
- 9.m1 PowerShell 은 stdin 미종료로 무한 hang(재현) — 메모 → 이미 [[codex-bash-invocation]]
- 9.4 plan-reviewer/code-reviewer 는 Claude subagent 필수 + Codex 가용 시 병행, researcher·보조 구현은 선택, simplify 는 대상 아님 — 인라인 → §9
- 9.5 공유 채널 줄 — 중복(10.1) → 삭제(모순 7)
- 9.6 push 직전 별도 codex 리뷰는 두지 않음, 로컬 다관점 점검은 `/code-review` 수동(옛 §10 끝 단락) — 인라인 → §9 (모순 7)

## §10 plans/ (표현만 줄이고 옮기지 않는다)
- 10.1 경로 `<ROOT>/plans/<YYYY-MM-DD>-<slug>/<slug>-plan.md`(티켓 ID 작업·컨텍스트가 명확한 단위) — 인라인 → §10
- 10.1b `<ROOT>` = `git rev-parse --show-toplevel`(c·e·dlc 와 같은 기준) — 인라인 → §10
- 10.1c `.claude/plans/` 로 적지 않는다(이 repo 는 루트가 `~/.claude` 라 double-nest 된 빈 경로) — 인라인 → §10
- 10.1d 파일명에 slug 가 있어야 `@` 자동완성에서 식별된다 — 이유 → 짧게 유지
- 10.2 slug `<TICKET>-<short-desc>` 또는 `<short-desc>` — 인라인 → §10
- 10.2b 디렉토리 prefix 는 시작일, 불변(rename 금지) — 인라인 → §10
- 10.3 매칭: branch 가 slug 에 포함된 dir 의 `*-plan.md` 1개 — 인라인 → §10
- 10.4 active plan 은 branch 매칭과 무관하게 계속 추적(branch 를 바꾸거나 범위가 넓어져도 동기화 대상) — 인라인 → §10
- 10.5 **시작**: 매칭 plan(과 plan log)을 read 해 컨텍스트 복원, 없으면 새로 생성(`status: in_progress`) — 인라인 → §10 (라벨 고정)
- 10.6 **진행 중 동기화**: plan 과 다른 결정·방향·스코프 변경은 즉시 반영, 턴 끝까지 미루지 않는다 — 인라인 → §10 (라벨 고정)
- 10.6b 스코프·접근·아키텍처 변경·새 제약 → `# Decisions` 의 그 결정을 고쳐 쓰고 이유를 붙인다 — 인라인 → §10
- 10.6c 밀려난 선택은 기각안으로 옮기고 기각 사유를 남긴다(plan 은 작업 끝에만 커밋돼 세션 안 이력이 git 에 없다) — 인라인 → §10
- 10.6d Acceptance 문구·통과 기준·검증 명령을 바꾸면 이전 값 → 새 값과 사용자 승인을 남긴다 — 인라인 → §10
- 10.7 할 일이 생기거나 끝나면 `# Tasks` 에 추가·체크(급한 다음 일은 미완료 맨 위) — 인라인 → §10
- 10.8 막힘 → `# Blockers` + `status: blocked` — 인라인 → §10
- 10.9 **턴 종료**: 끝낸 Task 체크(날짜), frontmatter `updated:` 오늘, 빠뜨린 동기화 보강 — 인라인 → §10 (라벨 고정)
- 10.10 **완료**: 머지·배포·승인 그 시점에 즉시 `status: done`, 미루지 않는다 — 인라인 → §10 (라벨 고정)
- 10.10b `/e merge` 는 done 을 머지 PR 에 실어 보내고 머지가 거부되면 `in_progress` 로 복구 — 인라인 → §10
- 10.11 plan 은 현재 상태의 단일 진실 소스(묶음이면 요구의 정본은 `intent.md`, plan 은 `intent:` 로 가리킨다), 합의는 항상 plan 에 먼저 — 인라인 → §10
- 10.12 `plans/` 는 tracked — 작업 브랜치와 함께 commit·push 하면 다른 머신·세션이 이어받는다 — 인라인 → §10
- 10.12b pre-commit-check 가 staged `plans/*.md` 토큰을 스캔, plan 에 raw token/credential/PII 금지 — 인라인 → §10
- 10.13 frontmatter `title`·`status`(`in_progress`|`blocked`|`done`)·`started`·`updated` 필수 — 인라인 → §10
- 10.14 `# Goal`·`# Tasks`·`# Decisions`·`# Blockers` 는 빈 채로라도 헤더 유지, `# Tasks` 만 항목 1개 이상, `# Acceptance` 는 비trivial 필수 — 인라인 → §10 (모순 5)
- 10.15 `# Goal`: 첫 문단에 목표 1~3줄 — 인라인 → §10
- 10.15b 라벨 불릿 `Why:`·`Constraints:`·`Out of scope:`·`Open questions:`(못 정한 것만)·`Split:`(medium 이상 — `none — <근거>` 또는 `bundle → <intent.md 경로>`) — 인라인 → §10
- 10.15c dlc 요구사항 명확화가 채운다(medium 이상은 항상), 사용자 확인 vs 모델 추론(⚠️) 구분 — 인라인 → §10
- 10.16 `# Tasks`: 첫 미완료 항목이 다음 즉시 액션 — 인라인 → §10
- 10.16b 형식 `- [ ] <할 일>` / `- [x] <할 일> (YYYY-MM-DD)[ — 한 줄 결과]`, 하위 항목 허용(체크하면 날짜도) — 인라인 → §10
- 10.16c 커밋 sha 는 적지 않는다(재구성으로 바뀐다 — sha 는 Report) — 인라인 → §10
- 10.16d 파일을 바꾸는 Task 는 그 경로를 backtick 으로 — 이것이 이 작업이 건드리는 파일 목록 — 인라인 → §10
- 10.16e 새로 생긴 급한 일(리뷰 반영·재실행)은 미완료 맨 위 — 인라인 → §10
- 10.16f 사용자 결정이 필요하면 `- [ ] NEEDS-HUMAN: <질문> — <선택지>`(`/c` 는 여기서 멈춘다) — 인라인 → §10
- 10.16g WIP 체크포인트는 그 미완료 Task 에 "브랜치 tip `wip:` 커밋 이어서" — 인라인 → §10
- 10.16h done plan 에는 `[post-merge]` 항목만 미완료로 남는다(`/e merge` 가 머지 전에 확인) — 인라인 → §10
- 10.16i 머지 대기는 Task 가 아니라 PR 상태로 본다 — 인라인 → §10
- 10.17 `# Acceptance`: test 가능한 완료 기준, 번호 항목 `1.`(`1. [ ]` 허용) `무엇 — 어떻게 확인 — 통과 기준`, 증거로 충족될 때만 완료 — 인라인 → §10
- 10.18 `# Decisions`: 현재 합의+이유, 진지하게 검토했다 기각한 대안과 사유, 바뀌면 고쳐 쓰고 밀려난 안은 기각안 — 인라인 → §10
- 10.18b 기각안이 없으면 다음 세션이 같은 안을 다시 꺼낸다 — 이유 → 짧게 유지("실측 재발 축" 은 이력 → 삭제)
- 10.19 `# Blockers`: 막힌 것 + 풀려면 필요한 것 — 인라인 → §10
- 10.20 작업 기록은 같은 폴더 `<slug>-log.md`(plan log): 절차가 요구할 때만 만들고 frontmatter 없음, plan-lint 대상 아님, plan 과 같이 커밋 — 인라인 → §10
- 10.20b 새 형식 plan 본문에 작업 기록 섹션을 두면 plan-lint 위반 — 인라인 → §10
- 10.20c `# Review Disposition` — dlc fix loop 처분 `fix`/`defer`/`false-positive`/`wontfix` — 인라인 → §10
- 10.20d 묶음 분할 리뷰의 처분은 첫 plan 의 log 에 `[묶음]` 접두 — 인라인 → §10
- 10.20e dlc ⚠️ self-flag 처분은 `resolved`/`accepted-risk`/`deferred` — 인라인 → §10
- 10.20f `# Deferred`(범위 밖 발견 — §3-4) · `# Workflow Findings`(확인된 workflow 실패, 최소형) — 인라인 → §10
- 10.20g `defer`(처분값) ≠ `# Deferred`(섹션) — 인라인 → §10
- 10.21 기계 검사는 `scripts/plan-lint.js`(필수 섹션·Tasks 체크박스와 날짜·Acceptance 참조·본문의 작업 기록 섹션) — 인라인 → §10
- 10.21b 2026-10-18 이전 형식(옛 섹션이 있고 `# Tasks` 가 없음)도 유효, 진행 중인 옛 형식 plan 은 끝날 때까지 옛 섹션에 — 인라인 → §10 (적용 시점 날짜는 규칙)
- 10.21c 대응표: 첫 미완료 Task ↔ `# Next`, 체크된 Task ↔ `# Progress`, Task 안 경로 ↔ `# Key Files`, Goal 라벨 불릿 ↔ `# Intent`, log 의 작업 기록 ↔ plan 본문의 같은 섹션 — 인라인 → §10 («대응표» 를 여러 skill 이 인용)
- 10.21d 새 plan 만 새 형식, 한 plan 에 두 형식을 섞지 않음, skill·agent 는 새 형식만 적고 옛 형식을 만나면 대응표 — 인라인 → §10
- 10.22 리뷰 단락 → §9 로(9.6), 단위 2
- 10.23 **묶음 intent**: 한 요구가 plan 여럿으로 갈라지면 `<ROOT>/plans/<YYYY-MM-DD>-<intent-slug>/intent.md` 한 파일, 각 plan 은 frontmatter `intent: plans/<dir>/intent.md`(스칼라 1개 — 두 묶음에 걸치지 않음) — 인라인 → §10 (제목 «묶음 intent» 고정)
- 10.23b intent dir 에는 `*-plan.md` 를 두지 않고 plan 은 자기 dir 에 — 매칭·`plan-match.js`·`session-brief.js`·plan-lint 가 그대로 동작, intent.md 는 plan-lint 대상 아님 — 인라인 → §10
- 10.24 **만드는 때(닫힌 목록)** 1) 사용자 지시 — 인라인 → §10 (번호 1)2)3) 고정 — dlc 가 "트리거 1·3 / 2" 로 인용)
- 10.24b 2) 각 단위가 순서대로 혼자 default 에 머지돼도 빌드·규약이 무모순인 복수 plan 으로 나뉠 때 — medium 이상은 dlc 분할 판정이 능동으로, small 은 예상될 때 — 인라인 → §10
- 10.24c 3) 기존 plan 의 Out of scope·plan log `# Deferred`·"별도 작업" 에서 새 plan 을 시작하면 소급 생성, 선행 plan 에는 `intent:` 1줄만(본문 손대지 않음) — 인라인 → §10
- 10.24d 그 항목이 이미 이슈로 넘어갔거나 선행 plan 이 다른 묶음이면 소급 생성하지 않고 이슈와 새 plan `# Decisions` 가 추적 — 인라인 → §10
- 10.24e 그 외 단발 작업은 plan `# Goal` 라벨 불릿만 — 인라인 → §10
- 10.24f 착수 전 `plans/*/intent.md` 중 `status: open` 을 훑어 기존 묶음이면 연결 — 인라인 → §10
- 10.25 형식: frontmatter `title`·`status: open|closed`·`started`·`updated`, 값 라인에 인라인 주석 금지 — 인라인 → §10 ("파서가 값으로 오인한 선례" 는 이력 → 삭제)
- 10.25b 본문 H1 6개 `# Problem`·`# Proposed outcome`·`# Constraints`(묶음 공통 제약) — 인라인 → §10
- 10.25c `# Out of scope` 는 하지 않을 경계만 — 이어서 할 후속은 `# Plans` 에 `(미착수)` — 인라인 → §10
- 10.25d `# Open questions`: 미처분 `(열림)`, 처분은 `(해소)`/`(이월 → <새 묶음 | #이슈 | plan 경로>)` — 인라인 → §10
- 10.25e `# Plans`: plan 경로 + 한 줄 메모, status 복제 금지(정본은 각 plan frontmatter), 폐기한 plan 은 메모에 `폐기` — 인라인 → §10
- 10.25f 착수 안 한 단위는 `<slug 후보> (미착수) — 메모`, 착수하는 dlc 가 실제 경로로 치환 — 인라인 → §10
- 10.26 plan `# Goal` 라벨 불릿은 intent.md 링크 1줄 + 이 plan 의 델타(제약·범위), 공통 제약 복제 금지, 델타가 없으면 `델타 없음 — <근거>` — 인라인 → §10
- 10.26b 공통 제약이 바뀌면 plan `# Decisions` 에 남기고 intent.md 를 갱신 — 인라인 → §10
- 10.27 **소유권**: 각 세션은 intent.md 에서 자기 plan 의 `# Plans` 줄과 자기가 연 Open question 만 고친다 — 인라인 → §10
- 10.27b 공통 Constraints 를 바꾸면 진행 중인 다른 plan 의 `# Decisions` 에 영향 통지 — 인라인 → §10
- 10.28 **수명**: plan `done` ≠ intent `closed` — 인라인 → §10
- 10.28b `closed` = `# Plans` 의 모든 plan 이 done(또는 폐기) 그리고 Open questions 전부 처분 — Out of scope 는 조건이 아니다(영구 경계) — 인라인 → §10
- 10.28c `/e` 가 plan done 을 쓰는 그 지점(체크포인트 확인 done / 머지 모드 M4 커밋)에서 판정해 같은 커밋에 담고, 조건 충족이면 확인 없이 닫는다, M4 복구 시 함께 되돌린다 — 인라인 → §10
- 10.29 **한계**: 선행 브랜치가 미머지면 후속 worktree 에 intent.md 가 없다 — 착수 스캔은 `git worktree list` 의 모든 worktree `plans/`, 찾으면 `git show <선행브랜치>:<경로>` 로 같은 경로에(동일 내용 추가는 머지 때 충돌 없음) — 인라인 → §10 (라벨 «한계» 를 skills 가 인용)
- 10.29b tracked·secret 스캔은 plan 과 같다(`plans/*.md`) — 인라인 → §10
- 10.30 적용 범위: 티켓·명확한 작업 컨텍스트만, 단순 질문·탐색·한 턴 명령 제외 — 인라인 → §10

## §11 LLM Wiki
- 11.1 두 계층: repo wiki `<ROOT>/wiki/`(같은 브랜치) · 공용 wiki `~/.claude/wiki/`(공개 가능한 사실·전역 자산 결정) — `[[…]]` 는 공용 — 인라인 → §11
- 11.2 공용 wiki 는 비공개 repo 의 별도 clone, worktree 사본 없음, 절대경로로 읽음, 루트 `rg` 는 건너뜀 — 인라인 → §11 (rg 부분은 2.11 과 중복 → 한 곳)
- 11.3 `wiki/docs/` 하네스 참조 문서는 직접 읽음(자동 로드 안 됨, `wiki_search` 는 `pages/` 만), 쓰기·공개 점검은 페이지와 같음 — 인라인 → §11
- 11.4 쓰기는 main 세션, 그 repo main 에 직접 커밋(push 요청 시), worktree 중 생긴 공용 적립은 plan log Deferred — 인라인 → §11
- 11.5 예외: 그 repo `WIKI.md` 가 worktree+PR 로 정한 코드 계층과 그 `plans/` 는 PR 로(상주 서버라 리뷰 없이 실행되면 안 됨) — 인라인 → §11
- 11.6 적는 기준은 공개 가능한 사실, 공개 점검 금지 목록을 wiki 에도 적용(private-terms 백스톱 없음) — 인라인 → §11
- 11.7 공개 점검: `~/.claude` 에서 커밋·push 하는 모든 것(작업 종류 불문 — 코드·문서·plan·브랜치/worktree 이름·커밋 메시지·PR 제목/본문)에 회사·조직명·내부 도메인/호스트/IP·고객/제품 코드명·티켓 키·비공개 repo 이름/경로/내부 도구명 금지(비공개 repo 는 "회사 repo") — 인라인 → §11
- 11.8 비공개(또는 불명) 출처 적립은 커밋 전 diff 확인 — 인라인 → §11
- 11.9 `private-terms.txt` 백스톱(목록 밖·PR 본문·웹 편집은 못 잡음 → 점검이 먼저), 걸리면 목록을 도구로 읽지 말고 표현을 바꿈 — 인라인 → §11
- 11.10 현재 repo 가 `~/.claude` 인지 판정 명령, 맞으면 이 repo 의 wiki = 공용 wiki — 인라인 → §11
- 11.11 작업 시작 시 `wiki_search.py` 로 조회(exit 2 는 stderr), 없거나 빗나가면 두 index 직접 — 인라인 → §11
- 11.12 재사용 지식은 대상 계층 판정 필수 → `/wiki ingest` 제안(자동 아님), 애매하면 repo wiki, repo wiki 없으면 비대상+사유 — 인라인 → §11
- 11.13 다른 repo 세션의 공용 대상은 적립하지 않고 Deferred·Report 에 제안 형식, 출처 칸 공개/비공개만, 근거는 공개 검증 가능한 것만 — 인라인 → §11
- 11.14 배치는 이 절, 형식은 `WIKI.md`, raw 읽기 전용·gitignored, 절차 `skills/wiki/SKILL.md` — 인라인 → §11

## §12 피드백 메모리
- 12.1 교정을 영속화하라는 지시("기억해/규칙으로/다음부턴")면 memory `type: feedback` — 목표는 다음 작업에서 반영 — 인라인 → §12
- 12.2 인덱스는 명령형 행동 규칙(예 ❌/✅), 본문엔 사례·Why·How — 인라인 → §12
- 12.3 저장은 파일 + `MEMORY.md` 인덱스 둘 다(인덱스는 직접 갱신 — 빠뜨리면 본문이 묻힌다) — 인라인 → §12
- 12.4 작업 시작 시(dlc Explore) 관련 인덱스 줄 확인, 필요하면 본문 — 인라인 → §12
- 12.5 보편·중대 규칙은 CLAUDE.md 로 승격 후 memory 정리, repo 한정은 그 repo CLAUDE.md·wiki decision — 인라인 → §12
- 12.6 같은 주제는 기존 파일 갱신, 모순이면 교체, 무효는 삭제 — 인라인 → §12

## §13 실수·교훈
- 13.1 내 실수·사용자가 지적한 실패는 적립 대상인지 판정 — 목표는 다음 구현에서 회피 — 인라인 → §13
- 13.2 무승인 자동 적립 금지 — Report 또는 plan log `# Workflow Findings`/`# Deferred` 에 제안, 승인 뒤 적립(§11 wiki ingest 와 같은 제안 게이트) — 인라인 → §13 (모순 3 수정)
- 13.3 상세는 대상 계층 wiki 교훈 페이지(공용 `pages/decision/lesson-<주제>.md`, 다른 repo 는 그 WIKI.md), 원인(3 Whys)·재현 조건·잘못된 방법·올바른 방법, `index.md`·`log.md` 동기화 — 인라인 → §13
- 13.4 자동 상기는 `MEMORY.md` feedback 인덱스 한 줄(명령형 + lesson 링크), `MEMORY.md` 는 repo 별, 다른 repo 에서 찾은 전역 교훈의 memory 줄은 공용 적립 뒤 `~/.claude` main 에서 — 인라인 → §13
- 13.5 저장·승격·재참고는 §11·§12 그대로, §13 의 증분은 내가 찾은 실수까지 포함하는 것, 적립은 판정·제안(승인된 인덱스 줄은 매 세션 주입), 반복되면 hook 게이트로 승격 — 인라인 → §13
- 13.m1 wiki 만으로는 자동으로 안 떠오르고 인덱스만으로는 원인이 묻힌다 · [[self-diagnosis-and-improvement-status]] 의 "무승인 기록 트리거 미채택" — 메모(이유) → 링크만 유지

## 끝
- E.1 `@RTK.md` import — 인라인 → 끝

## 다른 파일이 가리키는 표지 (Acceptance 3)
- 절: `## 0.`~`## 13.` 제목, §3 의 번호 항목 1~6(Setup·Explore·Plan·Implement·Verify·Report, 이 순서), §8 의 (a)·(b) 표지.
- 인용 — 글자 그대로: skills/e «push 는 요청 시만»(§8) · skills/dlc «모호하면 질문»(§3-2).
- 인용 — 뜻만(지금도 글자 그대로가 아님, 그 절에 해당 불릿 라벨이 남는지 본다): skills/c «시작: 매칭 plan read 후 컨텍스트 복원 / 진행 중 동기화»(§10 **시작**·**진행 중 동기화**) · skills/e «턴 종료 / 완료»(§10 **턴 종료**·**완료**) · skills/e «머지 시점에 done», scripts/session-brief.js «머지 시점에 즉시 done»(§10 **완료**).
- 짧은 이름: «§3-6 예외»(선택지 생략 조건) · «§1 단서»(방향 합의는 별개) · «§8(a) 안전조건» · «§8(b)».
- 짧은 이름 — 글자 그대로 남겨야 하는 것: «중복 질문 금지»(§3-6 — skills/e 46행·skills/dlc 16단계가 단위 1 에서 인용) · «대응표»(§10 — agents/plan-reviewer·skills/e·skills/jira-task·skills/c·skills/dlc) · **한계**(§10 — skills/c·skills/dlc) · **만드는 때(닫힌 목록)** 의 1)2)3) 번호(skills/dlc "트리거 1·3 / 2") · «공개 점검»(§11 — skills/dlc) · «자가 수정 금지»(§1)·«제안(자동 아님)»(§11)·«무승인 자동 적립 금지»(§13) — skills/improve · «force push»(§8 — skills/e 의 "§8 force-push 금지") · «### 묶음 intent»(§10 — wiki plan-handoff).
- 절 위치: worktree 규칙 8.2 는 §8 에도 남는다 — `scripts/guard-worktree-edit.js` 의 사용자에게 보이는 거부 사유와 `skills/wt/SKILL.md` 가 "CLAUDE.md §8" 로 가리킨다.
- 공용 wiki: `pages/decision/workflow-failures.md` 가 §8 «확인·검증되지 않은 변경은 커밋하지 않는다» 를 인용한다(글자 그대로 남긴다).
- `skills/improve/improve.sh` 3번 점검은 CLAUDE.md 의 굵은 agent 이름(`**plan-reviewer**` 등)을 grep 한다 — 굵게 남겨야 한다.

## 핵심 문구 검색 세트 (Acceptance 2 — 단위 2 전에 고정, 바꾸려면 사용자 승인)
✅·⚠️·❌·simplify·commit-check·intent.md·`# Deferred` 처럼 여러 번 나오는 문구는 하나만 남아도 통과하므로 약한 검사다 — 이 조항들은 Acceptance 1 의 조항별 인용이 지킨다.
AskUserQuestion · git status --short · verify.sh changed · ALL PASS (skip · 3 Whys · except: pass · ✅ · ⚠️ · ❌ · risk-based-approval · /compact · /rewind · run_in_background · grep -r · rg -uu · guard-worktree-edit · MEMORY.md · settings.local.json · # Deferred · # Acceptance · # Workflow Findings · /e merge · /wt · wiki/index.md · WebSearch · **plan-reviewer** · **code-reviewer** · **architecture-reviewer** · **researcher** · simplify · agentType · Pydantic · # TODO: · reset --hard · clean -fd · install-hooks · pre-push · git add -A · git diff --cached --name-only · --no-verify · Commit or push only when the user asks. · --fixup · commit-check · worklog · --porcelain --ignored · --ff-only · git rebase --abort · git branch -d · git push origin --delete · git branch -D · --delete-branch · TLS · codex --version · Bash 도구 · /code-review · .claude/plans/ · intent.md · plan-lint · NEEDS-HUMAN · [post-merge] · <slug>-log.md · open|closed · (미착수) · private-terms.txt · --git-common-dir · wiki_search.py · /wiki ingest · type: feedback · lesson- · push 는 요청 시만 · 모호하면 질문 · **시작** · **진행 중 동기화 · **턴 종료** · **완료** · 중복 질문 금지 · 자가 수정 금지 · 공개 점검 · 추측 금지 · 애매하면 확인 · 방향 합의는 별개 · force push · detached HEAD · 빈 커밋 · main 복귀 후 · 네이티브 격리 · baseline failure · 통과 ≠ 완료 · 대응표 · **한계** · **만드는 때(닫힌 목록)** · **소유권** · **수명** · ### 묶음 intent · 임계값 · 확인·검증되지 않은 변경은 커밋하지 않는다 · @RTK.md
