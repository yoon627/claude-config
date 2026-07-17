# dlc-details — dlc 절차 상세·엣지 (참조)

`/dlc` SKILL(`skills/dlc/SKILL.md`)의 **특정 분기에서만 찾는 상세**(요구사항 명확화 심화·조사 프로토콜 elaboration·wiki 연계 메커닉·Workflow Findings 기록 형식·격리 경계 runner 계약/simplify 체크리스트)를 담는다. SKILL 본문엔 진입 게이트·규모 gate·16단계 표·닫힌목록·트리거·안전 규칙만 남기고 세부는 여기로.

> 이 파일은 자동 로드되지 않는다 — dlc 가 **해당 분기에 실제로 들어갔을 때**(요구 공백이 넓을 때·디버깅·wiki 연계·workflow 실패 기록·13단계 simplify·검증 runner 위임) 이 파일을 Read 한다. 게이트·닫힌목록·단계 순서는 SKILL 본문이 단일 소스이고, 여기는 "어떻게/왜"만.

## A. 요구사항 명확화 심화 (SKILL 요구사항 명확화)
SKILL 은 체크리스트 4항 + fail-safe 질문 + silent + trivial 예외 + ≤2 라운드만 인라인. 질문을 **어떻게 구성/우선순위** 하나:
- **질문 vs 추천 경계** — **무엇(요구·목표·산출물)이 빠졌으면 질문**, **요구는 있고 구현 방법만 갈리면 분석 후 추천**. 둘 다면 acceptance 를 바꾸는 축(what) 먼저.
- **질문 우선순위** — 질문이 여럿이면 **답이 설계·acceptance 를 바꾸는 것부터**, 사용자가 배치 질문에 부담을 보이면 한 번에 하나씩(인터뷰식). 체크리스트 4항 불변.
- **blind-spot pass (낯선 영역)** — 요청 영역이 사용자에게 낯설다는 신호(사용자가 밝혔거나 질문으로도 공백이 안 좁혀질 때)면, 같은 질문을 반복하지 말고 **그 영역의 함정·"좋음"의 기준·과거 결정(wiki/코드)을 먼저 브리핑**한 뒤 그 위에서 질문을 재구성(사용자도 답 못 하는 질문 공회전 방지 — ≤2 라운드 안에서 수행, 새 단계 아님).
- **프로토타입-우선 (취향·시각 산출물)** — 취향·시각 판단이 큰 산출물이면 **구현 전 저비용 변형(mockup) 2~4종을 먼저 제시**해 반응(사용자도 못 밝히던 취향)을 끌어낸다. 강제 아님(고려 제안) — 모든 render 가 취향성은 아니라 판단은 모델. render 요청엔 `dlc-task-router` 가 turn-start 에 이 축을 조기 주입.

## B. 조사 프로토콜 elaboration (SKILL 조사 프로토콜 — 디버깅·장애)
SKILL 은 3스텝 이름(재현 → 가설 경쟁 3+ → 인과 사슬)과 "재현 없이 고쳤다 금지"만 인라인. CLAUDE.md §1(근본 원인·최소 3 Whys)의 dlc 구체화:
1. **재현**: 실패를 먼저 재현. 재현 없이 "고쳤다" 금지.
2. **가설 경쟁(3+)**: 원인 가설 최소 3개 경쟁, 첫 가설에 안주 금지.
3. **인과 사슬**: 증상 → 직접 원인 → 근본 원인까지 증거로 확정. 증상만 누르는 수정(에러 무시·무의미 retry) 금지.
- 가능하면 재현 테스트 먼저(TDD Red) — 수정 후 그 테스트가 green 이 되는 것이 acceptance 증거.

## C. wiki 연계 메커닉 (SKILL wiki 연계, CLAUDE.md §11)
두 판정(ingest·feedback memory) **누락 금지** 게이트는 SKILL 본문이 단일 소스 — 여기는 그 판정을 **어떻게** 수행하나(조건부·opt-in 2지점, 16단계 표 안 늘림, wiki 없으면 no-op):
- **1 Explore**: `wiki/index.md` 있으면 관련 `decision`/`entity` 페이지 read(과거 결정·검증된 외부 사실 재사용 → researcher 재검색 절감). 없으면 skip.
- **16 Report — ingest 판정 대상**: 재사용 지식 = 비자명 결정·교훈·확정한 외부 사실. trivial·일회성·이 작업 국한은 제외.
- plan→wiki **일방향 승격**(plans=일시적 핸드오프, wiki=영속 누적). 양방향 동기화 금지.

## D. Workflow Findings 기록 형식·hook 관계 (SKILL Workflow Findings)
SKILL 은 3-트리거·반복 2회+ 제안·자가수정 경계만 인라인. 기록 방법:
- **기록(2곳)**: ① plan `# Workflow Findings` 한 줄 ② **wiki `decision/workflow-failures.md` 누적**(영속·반복 추적). 형식 `깨진 규칙/단계 · 재발 조건 · 수정 후보 위치 · 발생 횟수`. 같은 실패면 기존 항목 횟수만 올린다.
- **자동 신호와 관계**: hook(`scripts/dlc-signal.js`)이 early-stop·doc-drift·guard 차단·plan-blocked 신호를 `~/.claude/telemetry/dlc-signals.jsonl` 자동 누적, `/improve` 가 집계·랭킹 제안. 이 수동 기록은 신호가 못 담는 **맥락**(원인·재발 조건·수정 후보 위치) — 상보(대체 아님).

## E. 격리 경계 상세 — runner 반환 계약·simplify 체크리스트 (SKILL 격리 경계)
SKILL 은 hub/spoke 역할·runner 위임 원칙·simplify 13단계 트리거만 인라인. 세부:
- **최종 검증 runner 반환 계약**: 실행 원칙(명령+cwd 문자열 그대로·재탐색 금지·cwd 누락 false-pass 경고)은 SKILL 격리 경계 인라인이 단일 소스. runner 는 빌트인 general-purpose(격리·Edit 없음, build/test 산출물·캐시는 생성). 지정 명령 실행 후 반환: **exit code + 통과/실패 + 실패 항목·로그 핵심(구조화)**. 실패 요약이 fix 에 불충분하면 메인이 재실행.
- **simplify 체크(13단계) diff 범위 점검 항목**: 중복(3회+ 반복만 추상화 검토) · 과한 추상화 · 불필요 옵션/죽은 분기 · 죽은 코드(rg 사용처 확인 후 삭제) · 과한 방어 코드 · 표준 라이브러리/기존 유틸 대체 · 깊은 nesting. 동작 보존 · 범위 내 · 불확실하면 보류(제안만 Report). substantive 수정 시 targeted test + 14 targeted 재리뷰 필수.
