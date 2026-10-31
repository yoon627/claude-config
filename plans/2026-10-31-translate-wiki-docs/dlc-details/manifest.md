# docs/dlc-details.md 규칙 목록 (translate-wiki-docs)

공용 wiki 3eaa4f4 의 `docs/dlc-details.md`(35줄) 기준. 한 줄 = 한 조항(한정어도 조항의 일부). 번역 대조는 `locations-en.txt`(`<id> | <영어 인용>`, 인용 여러 개는 ` ‖ `, `⏎` 는 줄바꿈, 각 인용은 파일 안에서 한 번, manifest 순서대로). 이 manifest 는 번역 초안 전에 만든다. 제목 줄은 설정의 `headings` 가 지킨다.

## 머리말
- P.1 `/dlc` SKILL 의 특정 분기에서만 찾는 상세(요구사항 명확화 심화·조사 프로토콜 elaboration·wiki 연계 메커닉·Workflow Findings 기록 형식·격리 경계 runner 계약/simplify 체크리스트)를 담는다
- P.2 SKILL 본문엔 진입 게이트·규모 gate·16단계 표·닫힌목록·트리거·안전 규칙만 남기고 세부는 여기로
- P.3 자동 로드되지 않는다 — dlc 가 해당 분기에 실제로 들어갔을 때(요구 공백이 넓을 때·디버깅·wiki 연계·workflow 실패 기록·13단계 simplify·검증 runner 위임) Read
- P.4 게이트·닫힌목록·단계 순서는 SKILL 본문이 단일 소스, 여기는 "어떻게/왜"만

## A. 요구사항 명확화 심화
- A.0 SKILL 인라인 범위: 체크리스트 6항(문제·제약·완료기준·범위·산출물·제외) + plan `# Goal` 라벨 불릿 기록(medium 이상 항상) + 묶음 intent 스캔 + 분할 판정(medium 이상) + fail-safe 질문 + silent + trivial 예외 + ≤2 라운드, 여기는 질문을 어떻게 구성/우선순위 하나
- A.1 질문 vs 추천 경계 — 무엇(요구·목표·산출물)이 빠졌으면 질문, 요구는 있고 구현 방법만 갈리면 분석 후 추천
- A.1b 둘 다면 acceptance 를 바꾸는 축(what) 먼저
- A.2 질문 우선순위 — 여럿이면 답이 설계·acceptance 를 바꾸는 것부터
- A.2b 사용자가 배치 질문에 부담을 보이면 한 번에 하나씩(인터뷰식)
- A.2c 체크리스트 6항 불변
- A.3 blind-spot pass(낯선 영역) — 낯설다는 신호(사용자가 밝혔거나 질문으로도 공백이 안 좁혀질 때)면 같은 질문 반복 말고 그 영역의 함정·"좋음"의 기준·과거 결정(wiki/코드)을 먼저 브리핑한 뒤 질문 재구성
- A.3b 사용자도 답 못 하는 질문 공회전 방지 — ≤2 라운드 안에서 수행, 새 단계 아님
- A.4 프로토타입-우선(취향·시각 산출물) — 취향·시각 판단이 큰 산출물이면 구현 전 저비용 변형(mockup) 2~4종을 먼저 제시해 반응을 끌어낸다
- A.4b 강제 아님(고려 제안) — 모든 render 가 취향성은 아니라 판단은 모델
- A.4c render 요청엔 `dlc-task-router` 가 turn-start 에 이 축을 조기 주입

## B. 조사 프로토콜
- B.0 SKILL 은 2스텝 이름(재현 → 인과 사슬)·"재현 없이 고쳤다 금지"·대안 원인 반증 원칙을 인라인, CLAUDE.md §1(근본 원인·최소 3 Whys)의 dlc 구체화
- B.1 재현: 실패를 먼저 재현, 재현 없이 "고쳤다" 금지
- B.2 인과 사슬: 증상 → 직접 원인 → 근본 원인까지 증거로 확정
- B.2b 원인이 불확실하면 다른 원인 후보를 반증한 근거를 함께 남긴다(첫 가설에 안주하지 않는다 — 후보 개수는 정하지 않는다)
- B.2c 증상만 누르는 수정(에러 무시·무의미 retry) 금지
- B.3 가능하면 재현 테스트 먼저(TDD Red) — 수정 후 그 테스트가 green 이 되는 것이 acceptance 증거

## C. wiki 연계
- C.0 두 판정(ingest·feedback memory) 누락 금지 게이트는 SKILL 본문이 단일 소스 — 여기는 그 판정을 어떻게(조건부·opt-in 2지점, 16단계 표 안 늘림)
- C.0b wiki 는 두 계층(현재 repo 의 `wiki/`, 공용 `~/.claude/wiki/` — 공용은 절대경로로 읽고 main 세션에서 쓴다), 배치 규칙은 CLAUDE.md §11
- C.1 1 Explore: 두 wiki(있는 것만 — `~/.claude` 에서는 하나)를 작업 키워드로 검색해(`wiki_search.py`, 쓰는 법은 `skills/wiki/SKILL.md` query 1단계) 관련 `decision`/`entity` 페이지 read(과거 결정·검증된 외부 사실 재사용 → researcher 재검색 절감)
- C.1b exit 2 는 stderr 이유를 본다 — `찾을 wiki 가 없다` 일 때만 skip, 그 밖의 이유(단어·category·stem 없음, 질의 모드 사용 오류, 설정·읽기 오류)는 고쳐 다시 찾는다
- C.2 3 draft plan 전(필수 — 조건·기록 위치는 SKILL 본문이 단일 소스): 1 의 키워드 대신 대상 자산 이름·작업 종류로 다시 거른다(예: `CLAUDE.md` + slim·압축·이관)
- C.2b 분석에서 이어진 계획은 1 을 건너뛰기 쉬워 여기서 한 번 더 건다 — 이 조회가 없어 7월 결정(`ops-doc-slimming`)과 정면충돌한 슬림화 계획이 나온 실측(2026-09-28)
- C.3 16 Report — ingest 판정 대상: 재사용 지식 = 비자명 결정·교훈·확정한 외부 사실, trivial·일회성·이 작업 국한은 제외
- C.3b 대상이면 계층까지 — repo 고유는 repo wiki, 여러 repo 에 쓸모 있는 공개 가능한 사실·전역 자산 교훈은 공용
- C.3c 다른 repo 에서, 또는 `~/.claude` worktree 세션에서 공용 대상이면 적립하지 않고 `in a ~/.claude main session: /wiki ingest …` 제안을 Report 와 plan log `# Deferred` 에 `<summary · public evidence · source (public/private)>` 형식으로
- C.3d §11 공개 점검 — 출처가 빠지면 적립 쪽이 비공개로 보고 diff 확인을 거친다
- C.4 plan→wiki 일방향 승격(plans=일시적 핸드오프, wiki=영속 누적), 양방향 동기화 금지

## D. Workflow Findings
- D.0 SKILL 은 3-트리거·반복 2회+ 제안·자가수정 경계만 인라인, 여기는 기록 방법
- D.1 기록(2곳): plan log(`<slug>-log.md`) `# Workflow Findings` 한 줄
- D.1b 공용 wiki `decision/workflow-failures.md` 누적(영속·반복 추적 — dlc 는 전역 자산이라 공용 계층)
- D.1c main 세션에서 쓴다 — `~/.claude` worktree 세션이면 plan log 에 남기고 복귀 후, 다른 repo 세션이면 이 기록은 §11 공용 제안으로
- D.1d 형식 `깨진 규칙/단계 · 재발 조건 · 수정 후보 위치 · 발생 횟수`
- D.1e 같은 실패면 기존 항목 횟수만 올린다
- D.2 자동 신호와 관계: hook(`~/.claude/scripts/dlc-signal.js`)이 early-stop·doc-drift·guard 차단·plan-blocked 신호를 `~/.claude/telemetry/dlc-signals.jsonl` 에 자동 누적, `/improve` 가 집계·랭킹 제안
- D.2b 이 수동 기록은 신호가 못 담는 맥락(원인·재발 조건·수정 후보 위치) — 상보(대체 아님)

## E. 격리 경계 상세
- E.0 SKILL 은 hub/spoke 역할·runner 위임 원칙·simplify 13단계 트리거만 인라인
- E.1 최종 검증 runner 반환 계약: 실행 원칙(명령+cwd 문자열 그대로·재탐색 금지·cwd 누락 false-pass 경고)은 SKILL 격리 경계 인라인이 단일 소스
- E.1b runner 는 빌트인 general-purpose(격리·Edit 없음, build/test 산출물·캐시는 생성)
- E.1c 지정 명령 실행 후 반환: exit code + 통과/실패 + 실패 항목·로그 핵심(구조화)
- E.1d 실패 요약이 fix 에 불충분하면 메인이 재실행
- E.2 simplify 체크(13단계) diff 범위 점검 항목: 중복(3회+ 반복만 추상화 검토) · 과한 추상화 · 불필요 옵션/죽은 분기 · 죽은 코드(rg 사용처 확인 후 삭제) · 과한 방어 코드 · 표준 라이브러리/기존 유틸 대체 · 깊은 nesting
- E.2b 동작 보존 · 범위 내 · 불확실하면 보류(제안만 Report)
- E.2c substantive 수정 시 targeted test + 14 targeted 재리뷰 필수

## 핵심 문구
`/dlc` · `~/.claude/skills/dlc/SKILL.md` · `# Goal` · `dlc-task-router` · `wiki/` · `~/.claude/wiki/` · `~/.claude` · `"$HOME/.claude/skills/wiki/wiki_search.py"` · `skills/wiki/SKILL.md` · `decision` · `entity` · `찾을 wiki 가 없다` · `CLAUDE.md` · `ops-doc-slimming` · `in a ~/.claude main session: /wiki ingest …` · `# Deferred` · `<summary · public evidence · source (public/private)>` · `<slug>-log.md` · `# Workflow Findings` · `decision/workflow-failures.md` · `~/.claude/scripts/dlc-signal.js` · `~/.claude/telemetry/dlc-signals.jsonl` · `/improve` · CLAUDE.md §1 · CLAUDE.md §11 · §11 · 3 Whys · TDD Red · 2026-09-28 · ≤2 · 2~4 · 16 · 13 · 14 · general-purpose · Edit · rg · 6

## 다른 파일이 가리키는 표지
- 절 표지 `§A`~`§E`(`## A.`~`## E.`) — `skills/dlc/SKILL.md` 가 §A(질문 구성)·§B(조사 프로토콜)·§C(wiki 연계)·§D(Workflow Findings 기록 형식)·§E(runner 반환 계약·simplify 항목)로 가리킨다. 제목 낱말은 영어로, 글자 표지는 그대로.
- README 의 dlc 절이 이 파일의 내용 목록(요구사항 명확화 심화·조사 프로토콜 elaboration·wiki 연계 메커닉·Workflow Findings 기록형식·격리 runner 계약/simplify 체크리스트)을 적는다 — 절 이름 대응만 바뀐다.
