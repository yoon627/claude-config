# skills/dlc 규칙 목록 (translate-skill-dlc)

b5a3471 의 `skills/dlc/SKILL.md`(173줄) 기준. 한 줄 = 한 조항(한정어도 조항의 일부). 번역 대조는 `locations-en.txt`(`<id> | <영어 인용>`, 인용 여러 개는 ` ‖ `, `⏎` 는 줄바꿈, 각 인용은 파일 안에서 한 번, manifest 순서대로). 이 manifest 는 번역 초안 전에 만든다.

의도한 변경 1건: 격리 경계 절의 agent 출력 절 이름 — 원문은 "plan 반영용 요약"(영어로 옮긴 agent 는 "Summary for the plan") 두 이름을 함께 적지만, agent 4개(researcher·plan-reviewer·architecture-reviewer·code-reviewer)가 모두 영어가 된 뒤라 영어본은 "Summary for the plan" 만 남긴다(terms.md 임시 문자열 줄 — H.20).

## frontmatter
- F.1 description: 비자명한 코드 변경(버그 수정·기능 추가·리팩토링)을 시작할 때 적용하는 개발 사이클 오케스트레이션
- F.2 description: 규모를 판정해 trivial(오타·로그 1줄)은 절차를 즉시 통과(worktree 는 규모 불문 경유)
- F.3 description: structural(다계층·public API·DB·신규 service)은 explore→plan→리뷰→TDD→구현→리뷰→simplify→검증 전체 파이프라인을 돈다
- F.4 description: `/dlc` 명시 호출 또는 비자명한 코드 변경 시 자동 적용
- F.5 description: 단순 질문·탐색·읽기 전용 작업에는 쓰지 않는다

## 머리말
- P.1 메인이 hub, 리뷰/검토만 격리 subagent
- P.2 plan 파일(작업 기록은 같은 폴더 `<slug>-log.md`)이 유일한 공유 채널이고 메인만 쓴다
- P.3 경로는 `<ROOT>/plans/<YYYY-MM-DD>-<slug>/<slug>-plan.md`(CLAUDE.md §10 규약)
- P.4 CLAUDE.md §3 작업 흐름의 구체화 — 충돌 시 CLAUDE.md 우선

## 적용
- A.1 `/dlc` 명시 호출 또는 비자명한 코드 변경 시
- A.2 trivial 은 규모 gate 에서 절차가 즉시 통과되지만 worktree 는 똑같이 경유
- A.3 단순 질문·탐색·읽기 전용·한 턴 명령은 제외

## 진입 매트릭스
- M.1 요청 유형을 판정해 경로를 정한다
- M.2 기준은 "코드/파일을 바꾸는가" 단일 — 규모는 도는 단계를 정할 뿐 worktree 여부를 가르지 않는다
- M.3 표 머리: 입력 유형 / 경로
- M.4 질문·탐색·읽기 전용(파일 변경 없는 한 턴 명령 포함) → dlc 미적용, 현재 위치에서 직접
- M.5 trivial 변경(오타·로그 1줄) → wt 경유 worktree 에서 dlc trivial(절차만 즉시통과)
- M.6 비trivial 변경(small 이상) → wt 경유 worktree 에서 dlc 전체(아래)

## dlc → wt
- W.1 코드/파일을 바꾸는데 현재 작업 worktree 가 아니면(main 이거나 밖) dlc 는 다른 어떤 행동(Explore·구현 포함)보다 먼저, 예외 없이 `wt` 로 worktree 를 만들어 그 안에서 진행
- W.2 main 직접·우회 금지 — 필수 게이트
- W.3 판정: Setup(0단계)에서 worktree 위치를 가장 먼저 확인(코드 읽기·수정 전)
- W.4 `git worktree list --porcelain` 첫 worktree(=main)와 cwd 비교, main 이면 wt
- W.5 생성은 무확인: worktree/브랜치 생성은 로컬·가역이라 승인 대상이 아니다(위험기반 승인 — CLAUDE.md §1)
- W.6 절차·보고 형식의 단일 소스는 `skills/wt/SKILL.md` request §3~§4 — dlc 는 재서술하지 않는다
- W.7 순환 방지: wt 가 dlc 를 invoke 한 경우는 이미 worktree 안이라 skip(wt→dlc 정상, dlc→wt 보강은 위치로 구분)
- W.8 이미 worktree 안이면 self-check 만 하고 진행(CLAUDE.md §3-1)

## 0. 규모 gate
- S.1 표 머리: 규모 / 트리거 / 도는 단계
- S.2 trivial 트리거: 오타·주석·포맷·import·로그 1줄
- S.3 trivial 단계: 구현 → 검증 → 커밋 → Report (리뷰/plan/TDD 생략 — CLAUDE.md §7 예외)
- S.4 small 트리거: 단일 함수/파일, <50줄, 단일 모듈
- S.5 small 단계: Explore → (버그면 재현 TDD Red) → 구현 → Green → code-reviewer → simplify 체크 → 검증 → 커밋 → Report
- S.6 medium 트리거: 다중 함수/1 모듈, 50~150줄
- S.7 medium 단계: small + draft plan → plan-reviewer → simplify 체크(+재검증)
- S.8 structural 트리거: 다계층·public API·DB·migration·신규 service·150줄+
- S.9 structural 단계: 전체 파이프라인(아래)
- S.10 규모는 예비값 — Explore 후/구현 diff 후 재판정
- S.11 small 로 시작했다 public API·DB·2계층·150줄+ 되면 승급하고 skip 한 plan-review/arch 를 되살린다
- S.12 최종 검증 위임: 표의 '검증'(전 규모·structural 15단계·승급 합류)은 격리 runner 실행·메인 판단(아래 격리 경계)
- S.13 trivial 검증·10단계 Green·14단계 targeted 재검증은 메인 직접
- S.14 격리=완료 전 최종 검증, 메인=구현 중 최소·targeted
- S.15 최종 검증은 변경이 확정된 뒤 1회만 돌린다
- S.16 사용자 요청으로 변경이 이어질 수 있으면 확정을 기다린다 — 확정 전에 시작하면 다시 돌려야 한다
- S.17 repo 가 바뀐 파일로 축을 고르는 명령을 주면 그것을 쓴다(`~/.claude` 는 `bash scripts/verify.sh changed`)
- S.18 전 축 검증은 CI 와 사용자의 주기 실행이 맡는다

## 요구사항 명확화
- Q.1 규모 판정 후 Explore 전, 요구의 공백을 점검한다 — §3 "if ambiguous, ask first"의 판정 절차
- Q.2 임의 추론으로 메우지 않는다
- Q.3 체크리스트 1) 문제·왜 지금(Problem) 2) 제약·경계조건(Constraints) 3) 완료 기준 4) 대상 파일/기능 범위 5) 사용자-visible 산출물·문구 형태 6) 명시적 금지/제외 범위
- Q.4 빈 칸이 완료 판정(acceptance)에 영향 줄 가능성이 조금이라도 있으면 질문(`AskUserQuestion`), 불확실하면 질문(fail-safe)
- Q.5 명백히 결과무관일 때만 가정 + 1줄 명시 후 진행
- Q.6 결과는 plan `# Goal` 의 라벨 불릿에 남긴다(plan 이 있으면 그때, 없으면 3단계 draft plan 시)
- Q.7 대화로만 끝내면 증발해 다음 세션이 같은 것을 다시 묻고 이미 기각된 선택지가 되살아난다
- Q.8 섹션 정의는 CLAUDE.md §10 이 단일 소스(옛 형식 plan 은 §10 대응표) — 여기는 채우는 조건과 절차만
- Q.9 medium 이상은 공백 유무와 무관하게 항상 적는다(2026-09-09 도입)
- Q.10 선택지가 되살아나는 원인은 공백을 못 본 것이 아니라 제약이 어디에도 적히지 않은 것이라, 공백을 발견했을 때만 적는 규칙으로는 막지 못한다
- Q.11 small 은 plan 이 있고 공백을 발견했을 때만, trivial 은 `# Goal` 라벨 불릿 기록 대상이 아니다
- Q.12 이 규칙 도입(2026-09-09) 이전에 만들어진 plan·이어받는 plan 에는 소급하지 않는다
- Q.13 무엇을 적나: `Why:` 는 내용으로
- Q.14 Constraints·Out of scope 는 내용 또는 `없음 — <근거 한 구절>`, 맨 `없음` 금지
- Q.15 맨 없음 금지 이유: "고려했으나 없다"와 "잊었다"를 구분하고 리뷰어가 반박할 수 있게
- Q.16 self-flag 의 "해당 없으면 0줄"과 다른 이유: 라벨 불릿은 고정 항목이라 `없음` 이 상태 기록이지 발명이 아니다
- Q.17 Open questions 는 못 좁힌 질문이 있을 때만(다음 세션이 이어받는다)
- Q.18 사용자가 확인한 것과 모델이 추론한 것을 구분한다 — 추론분은 ⚠️ 표기 또는 Open questions 로
- Q.19 추론이 확정으로 박히면 다음 세션이 잘못된 근거로 선택지를 기각한다
- Q.20 묶음 intent(§10 `intent.md`): 체크리스트 전에 `git worktree list --porcelain` 의 모든 worktree `plans/*/intent.md` 중 `status: open` 을 훑는다
- Q.21 미머지 선행 브랜치의 묶음은 그 worktree 에만 있다 — 여기서 놓치면 같은 묶음을 중복 생성한다
- Q.22 이 요구가 그 묶음의 후속이면 새로 만들지 않고 연결하고, 파일이 이 worktree 에 없으면 §10 한계대로 가져온다
- Q.23 없는데 §10 생성 트리거 1·3 에 걸리면 intent.md 를 먼저 만든다(트리거 2 는 medium 이상이면 아래 분할 판정, small 은 §10 대로)
- Q.24 연결한 요구가 그 묶음 `# Plans` 의 `(not started)` 줄이면 그 줄을 이 plan 의 실제 경로로 치환한다
- Q.25 묶음에 속한 단위는 규모와 무관하게(trivial 포함) plan 파일을 만든다(치환할 경로가 있어야 한다)
- Q.26 연결된 plan 의 `# Goal` 라벨 불릿은 링크 1줄 + 델타만(트리거·형식·수명·소유권은 §10 이 단일 소스 — 여기서 재서술하지 않는다)
- Q.27 분할 판정(medium 이상, 2026-09-16 도입): 체크리스트 뒤에 이 요구가 각 단위가 순서대로 혼자 default 에 머지돼도 빌드·규약이 모순 없이 유효한 복수 plan 으로 나뉘는지 능동으로 본다(§10 트리거 2 의 절차)
- Q.28 기준은 크기가 아니라 머지 무모순(plan 마다 worktree·리뷰·머지 고정비가 붙는다)
- Q.29 문서 규약처럼 "빌드는 안 깨지지만 일부만 머지되면 규약끼리 모순"인 경우는 나뉘지 않는다
- Q.30 순차 의존은 분할을 막지 않는다(의존은 `# Plans` 메모에)
- Q.31 나뉘면 intent.md 를 만들고(이미 open 묶음의 후속이면 그 `# Plans` 에 줄을 더한다) 단위별 줄(첫 plan 만 착수, 나머지 `<slug candidate> (not started)`)을 적는다
- Q.32 그 초안을 다른 분할선 후보·기각 사유와 함께 plan-reviewer 에 묶음 모드로 1회 넘긴다(`agents/plan-reviewer.md` 15항, codex off)
- Q.33 묶음 리뷰는 새 경계에만 — 소급(트리거 3)은 제외
- Q.34 결과·처분은 3단계 첫 plan log 의 `# Review Disposition` 에 `[bundle]` 접두
- Q.35 경계·의존·공통 제약이 바뀌면 재검토
- Q.36 첫 plan `# Goal` 에 `Split: bundle → <intent.md 경로>` 1줄
- Q.37 나뉜 단위는 각자 plan 을 갖고(위 묶음 bullet) 규모는 각자 gate 로 독립 판정한다
- Q.38 분할은 규모 판정을 면제하지 않으며 structural 트리거(다계층·public API·DB·신규 service)를 가진 단위는 그 plan 이 structural 로 돈다
- Q.39 안 나뉘면 plan `# Goal` 에 `Split: none — <무엇을 나누려 했고 어떤 결합 때문에 못 나눴나>` 1줄, 맨 `none` 금지
- Q.40 단위 후보가 1개뿐이면 그렇게 적는다 — 무엇이 한 머지에서만 유효한지
- Q.41 아래 예외면 그 형식
- Q.42 예외 — 같은 출처의 후속은 한 plan 에 묶어 둘 수 있다
- Q.43 같은 출처(한 plan 의 `# Deferred`·Out of scope, 또는 같은 open intent)에서 온 단위들은 결합이 없어 나뉠 수 있어도, "커밋 단위" 절의 목적 단위 커밋으로 단위마다 따로 revert 할 수 있으면 plan 마다 붙는 고정비를 아끼려 한 plan 으로 둘 수 있다
- Q.44 분할 이득이 plan 고정비만 못하다는 판단 — 묶음 모드 리뷰의 기준과 같다
- Q.45 단위가 같은 파일 안에서 섞여 한 커밋 단위로 합쳐지거나 structural 트리거를 가진 단위가 있으면 이 예외를 쓰지 않는다
- Q.46 그때 `Split:` 줄은 `none — purpose-commit bundle: <공통 출처> · <단위들> · <한 plan 으로 둔 이유>`
- Q.47 이 판정은 예비값 — Explore 후 확정하고 뒤집히면 갱신한다
- Q.48 없음→나뉨이면 그때 intent.md·묶음 리뷰를 만들고 `Split:` 줄을 고친다
- Q.49 나뉨→하나로 합쳐지면 남은 plan 은 `intent:` 를 유지하고 `(not started)` 줄은 지운다(착수 전이라 폐기할 plan 이 없다 — 묶음 수명은 §10)
- Q.50 예외를 택한 뒤 그 전제(같은 파일에서 섞이지 않음·structural 단위 없음)가 깨지면 분할 판정을 다시 한다
- Q.51 2026-09-16 이후 새로 만든 plan 부터
- Q.52 silent: 공백 없으면 질문 없이 진행(명확한 요구엔 마찰 0)
- Q.53 질문 축에만 걸린다 — `# Goal` 라벨 불릿 기록은 위 규칙대로
- Q.54 질문 구성·우선순위 심화: 질문 vs 추천 경계(무엇이 빠졌으면 질문·방법만 갈리면 추천)
- Q.55 답이 설계·acceptance 를 바꾸는 것부터(부담 보이면 인터뷰식 1개씩)
- Q.56 낯선 영역이면 함정·기준·과거결정 blind-spot 브리핑 후 질문 재구성
- Q.57 취향·시각 산출물이면 프로토타입-우선(mockup 2~4종 먼저)
- Q.58 세부는 `~/.claude/wiki/docs/dlc-details.md` §A
- Q.59 render 요청엔 `dlc-task-router` 가 프로토타입 축을 turn-start 조기 주입
- Q.60 trivial 도 예외 아님 — 절차 생략이지 요구 불명확 허용 아님
- Q.61 산출물·문구 모호하면 먼저 질문
- Q.62 명확화 ≤2 라운드(fix loop 동형)
- Q.63 Explore 후 규모 재판정으로 범위 커지면 게이트 재평가

## ⚠️ self-flag
- K.1 이 repo 의 우려 장치는 전부 리뷰어 쪽에 있다(plan-reviewer 강한/약한 우려, code-reviewer, architecture-reviewer)
- K.2 리뷰어는 격리 spoke 라 메인이 어디서 확신이 낮았는지 알 방법이 없어, 그 지점이 리뷰에서 우연히 안 잡히면 그대로 통과한다
- K.3 구현 중 plan 이 정하지 않은 동작을 메인이 채운 지점도 어디에도 남지 않는다 — 사람이 코드를 읽어야 하는 바로 그 지점이다
- K.4 그래서 계획·구현하는 메인이 직접 신고한다
- K.5 닫힌 트리거 4종 — 이때만 적고, 아니면 침묵
- K.6 요구사항 명확화 silent 규약의 질문 축과 동형, "우려 없음"을 쓰지 않는다
- K.7 트리거 1: 두 제약을 동시에 만족시키지 못해 한쪽을 택했다
- K.8 트리거 2: 규약끼리 상충해 우선순위를 판단했다(precedence 가 명시되지 않은 동급끼리)
- K.9 트리거 3: ⚠️추정(정황만 있는 근거)에 의존해 설계를 정했다
- K.10 트리거 4: (구현 중 — 8~15단계, plan 파일이 있는 small 이상) plan·`# Goal`·`# Acceptance` 가 정하지 않은 관찰 가능한 동작을 정했다(테스트 assert 로 정한 것 포함)
- K.11 그 동작: 실패·예외 시 동작, 기본값·임계값·타임아웃, 경계 입력(빈 값·중복·동시 요청) 처리, 외부 부작용(쓰기·전송·삭제)의 순서·조건
- K.12 그럴듯한 선택지가 둘 이상이었고 고른 쪽이 관찰 가능한 결과를 바꿀 때만 적는다
- K.13 기존 코드·호출부 계약·같은 레이어 관례가 이미 정한 것, 선택지가 하나뿐이던 것, 동작이 불변인 내부 세부(이름·자료구조)는 침묵
- K.14 구현 중의 다른 신고도 같은 표시: plan 파일이 있는 small 이상에서 8~15단계에 트리거 1~3 에 해당하거나 §10 동기화로 `# Decisions` 의 결정을 고쳐 쓰면(plan 과 다른 결정) 그 줄도 `⚠️ (구현)` 으로 시작해 트리거 4 와 같은 처분·Report 경로를 탄다
- K.15 표시를 붙여도 아래 자기 진단 판정은 그대로다("~로 변경" 은 설계 변경)
- K.16 특히 Acceptance 통과 기준이나 사용자에게 보이는 산출물을 바꾸는 선택은 기록과 별개로 반드시 묻는다(AskUserQuestion)
- K.17 기록처는 `# Decisions` — 새 섹션을 만들지 않는다
- K.18 한 줄 형식: `⚠️ <우려> — <무엇과 상충> — <택한 쪽과 이유>`
- K.19 구현 중의 줄은 접두 `⚠️ (구현)` 만 공통이고 본문은 각 형식대로
- K.20 트리거 4 는 `⚠️ (구현) <정한 동작> — <다른 선택지> — <택한 쪽과 이유> — <파일·심볼>`(줄번호 대신 심볼 — 줄은 이후 수정으로 밀린다)
- K.21 wiki 의 `> [!conflict]` 관행(WIKI.md)을 plan 쪽으로 옮긴 것
- K.22 개수·형식 상한을 두지 않는다 — 항목 수를 정하면 [[self-diagnosis-and-improvement-status]] 가 기각한 "빈 체크리스트 의례"가 된다
- K.23 해당 없으면 0줄이 정답
- K.24 처분은 리뷰 지적과 같은 경로 — 트리거 1~3 은 6단계 plan-reviewer 호출 시 `⚠️` 줄을 "우선 검토" 로 명시 전달
- K.25 7단계에서 리뷰 finding 과 함께 먼저 처분해 plan log `# Review Disposition` 에 남긴다
- K.26 처분값은 리뷰 finding 과 구분해 `resolved`(해소) / `accepted-risk`(감수, 이유 필수) / `deferred` 만 쓴다
- K.27 `false-positive` 는 자기 신고에 의미가 없다
- K.28 `⚠️ (구현)` 의 처분: 6단계 뒤에 생기므로 11단계 code-reviewer 입력에 "우선 검토" 로 넘긴다
- K.29 arch·Codex 에는 넘기지 않는다 — Codex 는 독립 입력
- K.30 그 뒤에 생긴 줄은 12단계 fix loop·14단계 재리뷰에 함께 넘긴다
- K.31 처분값은 위와 같다 — 리뷰어가 타당하다고 본 선택은 `accepted-risk`(택한 쪽 유지 — 사람이 확인할 지점으로 남는다), 리뷰어 지적으로 다른 쪽으로 바꿨으면 `resolved`
- K.32 재리뷰를 거치지 않은 줄(15단계 검증 수리, 재리뷰 생략)은 `⚠️ (구현) [리뷰 미경유]` 로 적어 메인이 처분하고 16 Report "읽을 곳" 에 반드시 넣는다
- K.33 리뷰어가 신고되지 않은 결정을 찾아 메인이 받아들이면 `⚠️ (구현)` 줄을 더한다
- K.34 리뷰어가 반박해 finding 이 되면 ⚠️ 처분과 finding 처분을 한 줄에 함께 적는다

## Acceptance — 항목화 + evidence gate
- V.1 요구를 test 가능한 acceptance 항목으로 분해, 각 항목이 증거(실행·관찰·통과)로 충족될 때만 "완료"
- V.2 증거 없는 "완료" 금지
- V.3 항목화(draft plan 시): plan `# Acceptance` 에 `what is satisfied` + `how it is checked`(명령/관찰) + `pass criterion`
- V.4 관찰 가능하게(추상적 "잘 동작" 금지)
- V.5 테스트 식별자: 테스트를 작성할 때(늦어도 evidence gate 전) 그 테스트가 증거인 항목의 검증 칸에 식별자(`path::test_name`, 관찰이면 명령)를 채운다
- V.6 비어 있던 칸을 채우거나 적힌 명령에 식별자를 덧붙이는 것은 검증 수단의 구체화라 no-progress 의 승인 대상이 아니다
- V.7 검증 실패 수리 중(no-progress 카운터가 도는 동안) 이미 적힌 식별자·명령을 바꾸거나 빼는 것은 승인 대상이다
- V.8 16 Report "읽을 곳" 의 출처가 된다
- V.9 증거 게이트(Report 전): 전 항목 증거 대조
- V.10 미충족·미검증이면 완료 금지 → 수정 또는 `status: blocked`/"unverified"(CLAUDE.md §1)
- V.11 verification grounding: 실행되는 산출물(HTML·SVG·게임·차트·CLI·서버)은 정적 점검이 아니라 실제 실행·출력 관찰 증거를 넣는다("well-formed ≠ correct")
- V.12 trivial 은 항목화 면제(검증 자체가 acceptance) — 단 검증은 한다
- V.13 문서 동기화도 acceptance(CLAUDE.md §3): README 문서화 컴포넌트·`wiki/pages/` 를 건드리면 README/`wiki/index.md` 동기화를 acceptance 항목으로 같은 브랜치 갱신
- V.14 잊으면 완료 아님 — 공용 wiki 는 브랜치가 아니라 main 세션에서 그 repo 에 함께 커밋(§11)
- V.15 삼중 보조: Stop hook(`dlc-early-stop`)이 capped 경고(fail-open)
- V.16 보조 1: 비trivial 변경에 검증 기록 없음
- V.17 보조 2: 문서화 표면 바꿨는데 README/index 동기화 없음(`dlc-doc-drift`)
- V.18 보조 3: 소스를 바꿨는데 이 브랜치에 매칭되는 plan 을 안 건드림(`plan-match` — plan 이 실제로 있을 때만 발동, 없으면 침묵)
- V.19 hook 은 보조 — 이 규약이 단일 소스

## 판정 + 알림
- J.1 작업을 끝낼 때 evidence gate 결과를 세 값 중 하나로 명시 판정한다 — "대체로 됐다" 로 끝내지 않는다
- J.2 아직 고칠 수 있고 고치는 중이면 판정 대상이 아니다(계속 진행)
- J.3 DONE — `# Acceptance` 전 항목이 증거로 충족
- J.4 여기서 plan `status` 를 done 으로 만들지 않는다 — §10 대로 머지·배포·승인 시점이 done 이다
- J.5 acceptance 통과 ≠ 통합 완료, 미리 done 을 박으면 `/c` 가 통합 대기 작업을 종료된 것으로 보고 건너뛴다
- J.6 정식 완료 커밋(16단계 마지막 커밋)은 이 판정에서만 — 목적 단위 커밋은 "커밋 단위" 절대로 중간에 만든다
- J.7 BLOCKED — 다음에 필요한 것이 자원·사실의 제공(권한·자격증명·미배포 API·타인 작업)
- J.8 BLOCKED 는 `status: blocked` + `# Blockers` 에 풀려면 필요한 것
- J.9 NEEDS-HUMAN — 다음에 필요한 것이 선택·승인(대안 선택·리스크 감수·기각안 재개)
- J.10 NEEDS-HUMAN 은 `status: in_progress` 유지 + `# Tasks` 미완료 맨 위에 `- [ ] NEEDS-HUMAN: <question> — <options>`
- J.11 blocked 로 접지 않는 이유: blocked 전이는 `plan-blocked` failure telemetry 로 집계돼(`dlc-signal.js`) 정상적인 결정 대기가 workflow 실패로 남는다
- J.12 status 가 그대로 둘의 구분 키가 된다
- J.13 둘 다처럼 보이면(자격증명도 없고 mock 으로 갈지도 정해야 한다) 다음 한 걸음으로 가른다 — 받아야 하면 BLOCKED, 골라야 하면 NEEDS-HUMAN
- J.14 BLOCKED·NEEDS-HUMAN 은 정식 완료 커밋을 하지 않는다(CLAUDE.md §8 — 검증 실패는 커밋 금지)
- J.15 이미 만든 단위 커밋은 각자 targeted 검증을 통과한 상태라 되돌리지 않는다
- J.16 미완 변경 보존이 필요하면 `/e` 의 `wip:` 체크포인트
- J.17 no-progress 정지: 검증 실패 수리는 무한하지 않다 — 1회차 실패 뒤에는 가설·전략을 바꿔야 하고, 바꾸고도 관찰 가능한 개선이 없으면 2회차에서 멈추고 위 판정으로 간다
- J.18 세는 것은 코드 수정 실패뿐 — 네트워크·인프라 등 transient 실패는 카운트하지 않는다
- J.19 어느 acceptance 항목·어떤 실패·무엇을 시도했고 무엇이 안 변했나를 `# Blockers`(NEEDS-HUMAN 이면 그 `NEEDS-HUMAN:` Task)에 남긴다
- J.20 카운터 리셋 금지: 실패를 다른 이름으로 재분류하거나, 테스트를 약화시키거나, acceptance 문구·통과 기준·검증 명령을 바꿔 횟수를 되돌리지 않는다
- J.21 그 셋을 정말 바꿔야 하면 사용자 승인 + `# Decisions` 에 이전 값 → 새 값 기록이 먼저다(CLAUDE.md §7 테스트 약화 금지의 연장)
- J.22 acceptance 항목은 plan 의 항목 번호로 식별해 세션이 바뀌어도 횟수가 이어지게 한다
- J.23 훅이 대신 세지는 않는다 — 현재 ledger(`dlc-evidence-ledger`)는 tool response 를 소비하지 않고 안정적인 실패 signature·acceptance 매핑도 없다
- J.24 기계화하려면 그것부터가 별도 작업이다
- J.25 알림: terminal 전이는 `PushNotification` 의 필요조건이지 충분조건이 아니다
- J.26 사용자 주의가 실제로 필요할 때만, 전이당 최대 1회
- J.27 BLOCKED/NEEDS-HUMAN 은 물어야 할 것을 한 줄로
- J.28 DONE 은 오래 걸려 사용자가 자리를 떴을 법할 때만 — 짧은 작업은 Report 가 이미 눈앞에 있어 중복이다
- J.29 도구가 attached 라 skip 하면 정상이며 재시도하지 않는다
- J.30 trivial·즉답은 면제

## 커밋 단위
- U.1 목적이 둘 이상인 medium 이상 작업은 목적 단위로 중간 커밋하고, 커밋한 단위의 후속 수정은 `fixup!` 으로 쌓아 마지막에 `commit-check` 가 합친다
- U.2 목적이 한 파일 안에서 섞이기 전에 커밋해 두면 사후 hunk 분리(commit-check 미지원)가 필요 없다
- U.3 small·trivial 은 16단계 1회 커밋 그대로
- U.4 선언(3단계 draft plan): `# Decisions` 에 `커밋 단위: 1) <고유 커밋 제목> — <경로/범위> 2) …`
- U.5 목적이 1개면 `커밋 단위: 1개 — <근거>`
- U.6 제목은 단위끼리 겹치거나 한쪽이 다른 쪽의 접두가 되지 않게 — `fixup! <제목>` 매칭과 compaction 뒤 sha 재발견(`git log --format='%h %s' $(git merge-base HEAD <default 브랜치>)..HEAD`)이 제목에 기댄다
- U.7 구현 중 목적이 늘면: 섞인 변경이 경로로 떼어지면 앞 목적을 먼저 단위로 커밋
- U.8 같은 파일 안에서 섞였으면 한 단위로 두고 사유를 `# Decisions` 에
- U.9 단위 커밋(10단계 뒤): 한 단위의 구현과 그 단위의 targeted 검증(Green)이 통과하면 그 단위 경로만 stage 해 선언한 제목으로 커밋한다
- U.10 plan·log 파일은 넣지 않는다(매 단계 갱신돼 앞 단위에 넣으면 뒤 단위와 3-way 충돌 — 16단계 마지막 커밋에만)
- U.11 두 단위가 함께 고치는 파일은 앞 단위가 동작하는 데 필요한 변경까지 앞 단위에 넣는다(빼면 그 커밋만 checkout 했을 때 깨진다)
- U.12 한 파일 안에서 두 목적이 이미 섞여 경로로 떼어지지 않으면 두 단위를 하나로 합친다
- U.13 후속 수정(11~15단계 리뷰 반영·simplify·검증 수리): 커밋된 단위를 고치면 그 단위 경로만 `git commit --fixup=<단위 sha>` — 역시 targeted 검증 통과 뒤에만
- U.14 두 단위에 걸치면 단위별 fixup 으로 나눈다
- U.15 단 앞 단위 대상 수정이 뒤 단위도 고친 파일을 건드리면 앞 단위로 합칠 때 3-way 충돌하므로 그 수정은 뒤 단위 fixup 으로 보내고 Report 에 귀속 예외로 적는다
- U.16 새 목적이면 선언에 추가하고 새 단위로
- U.17 리뷰·simplify 범위: 단위 커밋이 있으면 기본 `git diff` 가 비므로 code-reviewer·architecture-reviewer·simplify 체크에 `git diff <작업 base>...HEAD` + 작업트리 변경을 범위로 명시해 넘긴다
- U.18 마무리(16단계): 남은 코드 변경은 후속 수정 규칙대로 귀속 단위의 fixup 으로, plan 등 기록 파일만 마지막 단위의 fixup 으로 커밋
- U.19 그 뒤 `commit-check` 가 `fixup_of` 로 합치기를 제안한다(승인 후 적용)
- U.20 충돌·보류로 `fixup!` 커밋이 남으면 DONE 은 되돌리지 않되 Report 리스크에 "남은 fixup! 커밋 — push·`/e merge` 전에 commit-check 재실행 또는 정리"를 적는다
- U.21 push 되면 commit-check 범위 밖이 돼 정리할 수 없다

## 조사 프로토콜
- I.1 버그·장애는 추측 수정 전에(CLAUDE.md §1 근본 원인·3 Whys 구체화)
- I.2 재현 — 재현 없이 "고쳤다" 금지
- I.3 인과 사슬 — 증상→직접원인→근본원인 증거 확정, 원인이 불확실하면 다른 원인 후보를 반증한 근거 포함, 증상만 누르는 수정 금지
- I.4 가능하면 재현 테스트 먼저(TDD Red) — green 이 acceptance 증거
- I.5 각 스텝 elaboration 은 `~/.claude/wiki/docs/dlc-details.md` §B

## structural 전체 파이프라인
- L.0 0 Setup: git status · 규모 판정 · plan 파일
- L.1 1 Explore
- L.2 2 researcher: 조건부 · 격리
- L.3 3 draft plan: 관련 decision 조회(먼저 — 아래 wiki 연계) · 테스트전략 · rollback · 영향범위 · 구조의도 · # Acceptance 항목화 · ⚠️ self-flag(해당 시) · `intent:` 링크(묶음이면) · 커밋 단위 선언
- L.3b 3 draft plan: 규모표의 단계를 Tasks 에 처음부터 전부(나중에 더하는 Task 는 이유를 적고, 조건부 단계가 해당 없거나 사용자가 생략을 정한 단계는 `- [x] <단계> (YYYY-MM-DD) — 생략: <사유>` 로 닫는다)
- L.4 4 arch planning: 격리 · structural 만 · codex off · 프롬프트 첫 줄 `mode: planning`
- L.5 5 plan 수정
- L.6 6 plan-reviewer: 격리 · codex owner
- L.7 7 지적 반영: ⚠️ self-flag 를 리뷰 지적과 함께 먼저 처분 · 구조 바뀌면 4~6 재실행
- L.8 8 TDD Red: 새 테스트가 의도한 이유로 실패하는지 확인 · 쓴 테스트의 식별자를 # Acceptance 검증 칸에
- L.9 9 구현: `⚠️ (구현)` 신고(8~15단계, 해당 시 — self-flag 절)
- L.10 10 Green: test/build/typecheck 최소 → 끝난 단위는 단위 커밋(목적 2+ 일 때)
- L.11 11 arch(정밀) + code-reviewer: 격리 · 병렬 · codex owner 1개 · arch 프롬프트 첫 줄 `mode: post-implementation` · 입력에 plan·(있으면) plan log 경로 · 단위 커밋이 있으면 범위 `<base>...HEAD`+작업트리 · code-reviewer 에 `⚠️ (구현)` 우선 검토 전달
- L.12 12 fix loop: 관련 reviewer 만 · ≤2회 · disposition · 커밋된 단위 수정은 fixup · `⚠️ (구현)` 처분(새 줄은 재리뷰에 전달)
- L.13 13 simplify 체크: 메인 직접 · blocker 없을 때만
- L.14 14 재리뷰: simplify 체크의 substantive edit 시 targeted · 새 `⚠️ (구현)` 전달
- L.15 15 최종 검증: lint / typecheck / test / build · 격리 runner · 실행만
- L.16 16 마무리: evidence gate(# Acceptance 전 항목 대조 · 통과 후에만 완료) → 판정(DONE/BLOCKED/NEEDS-HUMAN) → plan 업데이트 → 정식 완료 커밋(DONE 만) → commit-check → 알림(필요할 때 최대 1회) → Report

## wiki 연계
- Y.1 ingest 제안은 조건부·opt-in, 16단계 표 안 늘림
- Y.2 단 계획 전 decision 조회는 필수다 — draft plan(3단계, plan 없이 가는 small 은 구현 착수) 전에 이 작업의 대상 자산 이름과 작업 종류(slim·압축·이관·재구성·제거·설정 변경 등)로 두 wiki 를 조회해 걸린 decision·lesson 을 읽는다
- Y.3 명령 `uv run --no-project python "$HOME/.claude/skills/wiki/wiki_search.py" <자산 이름> <작업 종류>` — 공용 wiki 는 cwd 와 무관하게, repo wiki 는 cwd 에서 위로 찾고 첫 줄에 찾은 wiki·쪽수를 낸다
- Y.4 exit 2 처리 등 쓰는 법은 `skills/wiki/SKILL.md` query 1단계
- Y.5 같은 세션의 분석·조사에서 이어진 계획이라 1단계 조회를 거치지 않았어도 한다
- Y.6 걸린 decision 이 있으면 따를지 뒤집을지를 plan `# Decisions` 첫 줄에 적고, 뒤집으면 근거와 사용자 승인을 붙인다([[lesson-verify-scaffold-purpose-before-removal]] 사례 4)
- Y.7 wiki 는 두 계층(현재 repo 의 `wiki/`, 공용 `~/.claude/wiki/` — 배치 규칙은 §11)이라 현재 repo 에 wiki 가 없어도 공용 조회는 한다
- Y.8 index 를 직접 볼 때도 공용은 절대경로 `~/.claude/wiki/index.md` 로 읽는다 — `~/.claude` worktree 에는 `wiki/` 가 없어 상대경로로 찾으면 "없음"으로 조용히 넘어간다
- Y.9 16 Report 두 판정 누락 금지
- Y.10 판정 1: 재사용 지식(비자명 결정·교훈·확정 외부사실)이면 대상 계층까지 판정해 `/wiki ingest` 제안(자동 아님, trivial·일회성 제외)
- Y.11 다른 repo 에서 공용 대상이면 `in a ~/.claude main session: /wiki ingest <summary · public evidence · source (public/private)>` 제안을 Report 와 plan log `# Deferred` 에 남긴다(§11 공개 점검)
- Y.12 `~/.claude` worktree 세션에서도 공용 wiki 에 쓰지 않고 같은 제안을 plan log `# Deferred` 에 남겨 main 세션에서 적립한다
- Y.13 판정 2: 작업 중 사용자 교정·리뷰 지적이 있었으면 §12 feedback memory 저장 판정(대상이면 memory 파일 + `MEMORY.md` 인덱스 둘 다, 비대상이면 사유 1줄)
- Y.14 Explore wiki read·plan→wiki 일방향 승격 메커닉은 `~/.claude/wiki/docs/dlc-details.md` §C

## 격리 경계
- H.1 메인(hub): Setup, Explore(얇게 — 광범위 검색만 Explore agent 위임), draft plan, TDD Red, 구현, Green(구현 직후 최소 스모크), 통합, 검증 명령 식별·결과 판단·실패 fix, Report, 최종 판단
- H.2 격리 subagent(spoke, read-only): researcher, architecture-reviewer(planning/정밀), plan-reviewer, code-reviewer
- H.3 최종 검증 runner(격리·Edit 없음·검증 산출물은 생성): 빌트인 general-purpose — 소스 불변, build/test 산출물·캐시는 만듦
- H.4 메인이 식별한 검증 명령을 문자열 그대로 + worktree 절대 cwd 로 받아 지정 명령만 실행, 해석·수정·재탐색·수리 안 함
- H.5 명령 식별 책임은 메인 — '검증 명령 미식별'
- H.6 cwd 누락 시 silent false-pass 위험
- H.7 반환 계약(구조화 형식·불충분 시 재실행) 세부는 `~/.claude/wiki/docs/dlc-details.md` §E
- H.8 runner 에 `# Acceptance` 원문을 함께 넘긴다(있을 때)
- H.9 runner 는 `항목 → 관찰한 것 / 관찰하지 못한 것 / 어긋난 것` 으로만 매핑해서 되돌린다
- H.10 명령·cwd 는 받은 문자열 그대로이고 재탐색·자체 수리 금지는 그대로다(해석 여지를 주면 '실행만' 계약이 무너진다)
- H.11 메인의 evidence gate 판정이 runner 보고와 갈리면 멈추고 사유를 남긴다
- H.12 지금 evidence gate 는 코드를 쓴 컨텍스트의 자기 채점뿐이라 이것이 유일한 독립 대조다
- H.13 검증 실패는 12단계 fix loop 와 별개 — 객관적이라 disposition(false-positive/wontfix) 대상 아님, 통과까지 메인이 수정·재검증
- H.14 메인 직접 검증(격리 아님): 10단계 Green·14단계 targeted 재검증·trivial 검증 — 짧고 즉시 루프라 격리 오버헤드가 손해
- H.15 simplify 체크(13단계): 격리 아니라 메인 직접(모든 spoke read-only)
- H.16 diff 범위에서 중복·과한 추상화·불필요 옵션/죽은 분기·죽은 코드·과한 방어·표준 유틸 대체·깊은 nesting 을 점검(항목 나열은 `~/.claude/wiki/docs/dlc-details.md` §E)
- H.17 동작 보존 · 범위 내 · 불확실하면 보류(제안만 Report)
- H.18 substantive 수정 시 targeted test + 14 targeted 재리뷰 필수
- H.19 subagent 끼리 context 미공유
- H.20 입력은 메인이 번들 전달, 결과는 각 agent 의 출력 절로 수신 — 원문의 두 이름("plan 반영용 요약"·"Summary for the plan") 중 영어본은 "Summary for the plan" 만(의도한 변경, 머리말 참고)

## codex phase owner
- O.1 규약 `~/.claude/wiki/docs/codex-review.md`
- O.2 한 phase 에 reviewer 여럿이면 codex owner 1개만 지정, 나머지에는 프롬프트에 §7 문구("Codex review is already running externally. Do not invoke Codex.")
- O.3 계획 단계: `plan-reviewer`(arch planning 은 codex off)
- O.4 요구사항 명확화의 묶음 분할 리뷰(plan-reviewer 묶음 모드)는 codex off — 한 phase 에 owner 는 6단계 하나이고, codex 프롬프트는 구현 계획용이라 경계 검토에 맞지 않는다
- O.5 구현 후: 버그/보안 위주면 `code-reviewer`, 구조 위주면 `architecture-reviewer`
- O.6 한도 캐시: reviewer 를 띄우기 전에 `<scratch>/codex-unavailable`(규약 §1)이 있으면 owner 에게도 §7 의 "Codex is unavailable in this session" 문구를 넣어 시도 자체를 건너뛴다
- O.7 reviewer 보고의 `Codex 미가용: … out of credits` 를 봤는데 마커가 없으면 메인이 만든다(subagent 가 못 썼을 수 있다)

## fix loop / disposition
- X.1 최대 2회
- X.2 각 finding 을 plan log `# Review Disposition` 에 `fix / defer / false-positive / wontfix` 기록(메인만 씀)
- X.3 code-reviewer 의 `[plan 대비]` finding 은 처분 줄에 그 태그와 바뀐 쪽(`코드`/`plan`/`둘 다`/`없음`)을 함께 적는다
- X.4 `fix` 가 코드를 plan 에 맞춘 것인지 plan 을 코드에 맞춘 것인지는 처분값만으로 갈리지 않아, 16 Report "읽을 곳" 출처 (3)의 판정 근거가 된다
- X.5 12단계에서 처분하는 `⚠️ (구현)` 줄은 finding 과 별개로 self-flag 처분값(`resolved`/`accepted-risk`/`deferred`)으로 같은 표에 남긴다
- X.6 새로 생긴 줄은 다음 재리뷰에 넘기고, 재리뷰 없이 끝나면 `[리뷰 미경유]` 로 메인이 처분한다(경로는 self-flag 절)
- X.7 2회 후 같은 class 잔존 시 `status: blocked` 또는 명시적 risk accept
- X.8 여기 2회는 리뷰 finding 처분 상한 — 검증 실패 수리의 상한은 판정 섹션의 no-progress 정지로 별개 축이다

## 자기 진단
- D.1 plan 을 쓸 때(single writer re-read 시점) 지금 행동이 첫 미완료 Task·규모표와 맞는지, 아래 중대 신호에 해당하는지 본다
- D.2 중대 신호면 멈추고 `AskUserQuestion` 으로 결정을 받는다(승인 전 수정 금지 — CLAUDE.md §1)
- D.3 trivial 면제
- D.4 중대(닫힌 목록): 방향/요구/설계 변경 · plan/리뷰/검증 건너뜀 · 스코프 밖 파일 수정 · single writer·격리 경계 위반 · 동일 실패에 동일 전략 2회 재현 · "검증 완료" 허위 위험
- D.5 모호하면 중대(fail-safe)
- D.6 사소한 누락(순서·산출물·검증결과 불변, 회복 가능 — 예: 끝낸 Task 체크 빠뜨림)은 바로 보강하고 한 줄 보고
- D.7 기존과 연결: 방향 오류는 CLAUDE.md §2, 반복 실패는 fix loop(≤2회→blocked), 단계 누락은 규모표·승급 — 새 로직 만들지 말고 참조
- D.8 상한: 발동→대응 후 재진단 ≤1회
- D.9 잔존 시 `status: blocked` + 알림

## Workflow Findings
- G.1 작업 중 확인된 workflow 실패(dlc/규약 자체 문제로 작업이 샌 경우)만 기록 — 매 작업 회고 아님(빈 의례 방지)
- G.2 자동 수정 안 함
- G.3 기록 트리거(확인된 것만) 1: 중대 self-diagnosis 발동(스코프 이탈·단계 누락·격리 위반 등)
- G.4 기록 트리거 2: 동일 유형 실패 2회 재현
- G.5 기록 트리거 3: 사용자가 명시 지적한 workflow 마찰·오탐(예: hook false positive)
- G.6 트리거 3 은 §12 feedback(작업방식 즉시 교정)과 달리 운영 자산(dlc/hook/규약)을 고칠 반복 마찰
- G.7 기록(2곳): plan log `# Workflow Findings` 한 줄 + 공용 wiki `decision/workflow-failures.md` 누적(같은 실패면 횟수만 ↑)
- G.8 dlc 는 전역 자산이라 공용 계층
- G.9 main 세션에서 쓴다 — `~/.claude` worktree 세션이면 log 에 남기고 복귀 후, 다른 repo 세션이면 공용 기록은 §11 제안으로
- G.10 기록 형식·자동 hook 신호(`scripts/dlc-signal.js`→`/improve`)와의 상보 관계는 `~/.claude/wiki/docs/dlc-details.md` §D
- G.11 반복 시 제안: wiki 같은 finding 이 2회+ 누적되면 `AskUserQuestion` 으로 "N회 반복됐다 — `~/.claude` 에서 `wt` 로 고칠까?" 제안
- G.12 승인 시 `~/.claude` 에서 wt → dlc(운영 자산은 `~/.claude` 에 있고, 변경은 파일 변경이라 wt 필수), 거부 시 보존만
- G.13 자가수정 경계(§1): 승인 없이 운영 자산(dlc/CLAUDE.md 등)을 스스로 고치지 않는다
- G.14 harness 는 발견·기록·제안까지, 수정은 사용자 승인 후
- G.15 완전 무인 자동화는 두지 않는다(공용 wiki [[self-diagnosis-and-improvement-status]])

## 필수 산출물 / 핵심 규칙
- B.1 plan(CLAUDE.md §10): 매 턴 `# Tasks` 체크(날짜)·추가
- B.2 subagent 는 plan 안 씀 — 메인이 single writer, 쓰기 직전 re-read 후 외부 변경 merge
- B.3 커밋(16단계): 조건과 금지는 CLAUDE.md §8 단일 소스, 여기는 절차
- B.4 16단계의 정식 완료 커밋(목적 단위 커밋이 있으면 남은 변경을 담는 마지막 커밋 — "커밋 단위" 절)은 evidence gate 통과 + plan 업데이트 뒤에 한다
- B.5 순서를 바꾸면 plan 갱신이 uncommitted 로 남아 §8 자동 정리가 막히고 `/e` WIP 이중 커밋이 생긴다
- B.6 규칙·스킬·agent 문구처럼 모델 행동을 바꾸는 변경이 들어 있으면 커밋 전에 바뀐 문구(diff)를 사용자에게 보여 확인받는다
- B.7 그것은 CLAUDE.md §8 의 검증 수단 — 그 문구대로 동작하는 것을 실제 세션에서 이미 관찰했으면 그것으로 갈음
- B.8 단위 커밋·fixup 도 같다
- B.9 방향 승인은 문구 확인이 아니다
- B.10 단 CLAUDE.md §8 의 위임 예외에 해당하면 그 조건대로 확인 대신 최종 보고에 커밋 목록을 남긴다
- B.11 경로 확정: `git status --porcelain` 과 plan `# Tasks` 안 경로를 대조해 이번 작업이 건드린 경로를 열거
- B.12 편집 이력이 compaction 으로 흐려졌을 때의 폴백 — 추측으로 `add -A` 회귀 금지
- B.13 메시지: 그 repo 의 `git log` 관례(없으면 Conventional Commits `<type>(<scope>): <요약>`) + `Co-Authored-By` 트레일러, 본문에 왜(CLAUDE.md §6 — 경위는 주석이 아니라 커밋에)
- B.14 커밋 sha 는 plan 이 아니라 Report 에 적는다(plan 에 적으면 tree 가 다시 dirty 가 돼 순서 규칙이 무효화된다)
- B.15 fix loop 로 16 을 다시 돌아도 중복 커밋을 만들지 않는다
- B.16 커밋 명령이 worktree 격리 가드에 거부되면 체이닝·`git -C` 없이 단일 명령으로, 다른 도구 경로로 재시도(상세 wiki `worktree-isolation-bash-guard`)
- B.17 `/e` 의 `wip:` 체크포인트와 구분 — 여기 커밋은 검증 통과한 정식 커밋, `/e` WIP 는 미완·미검증 보존
- B.18 커밋 뒤 `commit-check` 스킬로 브랜치 커밋 단위를 점검한다(규모 무관 — 생략 판단·제안·승인·재구성 절차는 그 스킬이 단일 소스)
- B.19 재구성했다면 Report 의 sha 는 재구성 뒤 값이고 백업 ref·되돌리기 명령도 Report 에 적는다(plan 에 쓰지 않는다)
- B.20 거절·적용 실패는 DONE 을 되돌리지 않고 Report 리스크로 남긴다
- B.21 16 Report — 선택지로 닫기(CLAUDE.md §3-6): 증거 게이트 통과 → plan 업데이트 → 커밋(위) 후, 보고는 상세(변경 요약·수정 파일·검증·영향·리스크)를 적는다
- B.22 이어서 선택지를 AskUserQuestion 으로(작업 확인 / 마무리·정리(push·PR·머지·worktree 정리 — 선택 시 `/e merge` 로 invoke) / 다른 작업 이어가기(`/wt` 신규 — §8) / 종료)
- B.23 merged·완료면 "wrap up" 선택지는 아래 정리 판정 제안 그 자체(별도 2차 질문 아님 — 중복 질문 금지, CLAUDE.md §3-6)
- B.24 최신 사용자 메시지에 지금 실행할 명시 액션이 있으면 선택지 생략(중복 질문 금지)
- B.25 16 Report — 읽을 곳: medium 이상, 또는 `⚠️ (구현)` 줄이 있는 작업 — 판정이 BLOCKED·NEEDS-HUMAN 이어도
- B.26 사람이 diff 전체 대신 의도가 박힌 지점만 읽게, 보고 끝부분(선택지 앞)에 `## 읽을 곳` 블록을 둔다
- B.27 새 판단을 만들지 않고 닫힌 출처 3종에서만 모은다
- B.28 출처 (1) `# Acceptance` 각 항목 → 구현 위치 `file:line (심볼)` → 증거(테스트 식별자·명령) 한 줄
- B.29 구현 위치가 없는 항목(전체 검증·문서 동기화)은 증거만, 증거가 없는 항목은 `미충족`/`미검증`
- B.30 출처 (2) `⚠️ (구현)` 각 줄 → `file:line`(`[리뷰 미경유]` 유지)
- B.31 출처 (3) code-reviewer `[plan 대비]` finding 중 처분이 `false-positive` 가 아니고 바뀐 쪽이 `코드` 만은 아닌 것
- B.32 `file:line` 은 Report 시점 작업트리 기준이다(커밋했으면 HEAD 와 같다 — plan 에는 적지 않는다)
- B.33 출처 (2) 중 `resolved` 가 아닌 것과 출처 (3) 은 줄 앞에 `확인 필요:` 를 붙여, 사용자가 선택지를 고르기 전에 볼 항목을 구분한다
- B.34 0건이면 블록을 생략한다
- B.35 opt-in 선택지가 아니다 — [[unknowns-discovery]] 에 기록된 퀴즈 제거와 달리 상시 블록이고 기존 기록만 모은다
- B.36 정리 판정(CLAUDE.md §8, wiki 유무 무관·always): 작업이 default 브랜치에 merged 되고 완료면 Report 에서 worktree 정리를 처리한다(방치·"선택사항" 언급만 금지)
- B.37 §8(a) 안전조건 전부 충족이면 누가 머지했든 worktree + 로컬 브랜치는 확인 없이 자동 정리(삭제한 로컬 tip sha 1줄 보고)
- B.38 원격 브랜치 삭제는 항상 AskUserQuestion(§8(b) — 자동 정리에 포함하지 않는다)
- B.39 원격 브랜치가 이미 없으면 묻지 않는다 — `/e` 7단계
- B.40 안전조건 미충족/불확실(dirty·squash-merge·미보존 산출물)이면 능동 제안(AskUserQuestion) — §8(b)
- B.41 dlc 는 Report 가 종점이라 여기서 넘기거나 직접 실행
- B.42 trivial·small 은 로컬 `git merge --ff-only <slug>` 후 정리(§8, push·PR 없음 — ff 불가면 미게시 브랜치를 default 위로 rebase·재검증 후 ff, 충돌·게시됐으면 `/e merge`)
- B.43 medium 이상·CI 검증·외부 공유가 필요하면 `/e merge`(push·PR·머지·정리까지)
- B.44 미머지·미완이면 제안 안 함(정확한 조건은 §8·`/e` 7단계의 6조건)
- B.45 검증 명령 미식별: README/package/pyproject/Makefile/CI 확인해도 없으면 "미식별" 기록 + 추측 실행 금지
- B.46 이 상태에서 "검증 완료" 금지
- B.47 CLAUDE.md §8 의 다른 검증 수단(실제 실행·관찰 / §7 수동 검증 절차 / 사용자 확인)도 쓰지 못했으면 커밋하지 않고 검증 방법을 묻는다
- B.48 식별한 명령은 runner 에 문자열·worktree cwd 그대로 전달(runner 는 재탐색·수리 안 함)
- B.49 researcher 재진입: 어느 단계든 외부 사실(버전/API/CVE) 의문 시 호출
- B.50 TDD Red: 새 테스트가 의도한 이유로 실패하는지 확인(기존 baseline failure 와 분리)
- B.51 feedback memory 참고(§12): Explore 시 `MEMORY.md` 인덱스의 관련 feedback(행동지시문)을 확인해 적용

## 다른 파일이 가리키는 표지
번호·이름을 유지하거나, 바꾸면 그 영어 이름. 포인터 처분은 `pointers.md`.
* 단계 번호 0~16(파이프라인) — 유지. `CLAUDE.md` "dlc step 13"·"step 16 commit rules", `agents/architecture-reviewer.md` "dlc step 4"·"dlc step 13", `agents/plan-reviewer.md` "dlc step 3", `skills/commit-check/SKILL.md` "the step 16 commit", `agents/code-reviewer.md`(번역 중) "dlc 13단계"
* 절 "커밋 단위" → "Commit units" — `CLAUDE.md` §8 "procedure in `skills/dlc/SKILL.md`, commit units"
* "커밋(16단계 …)" → "Commit (step 16 …)" — `CLAUDE.md` §8 "`skills/dlc/SKILL.md` step 16 commit rules"
* 절 "요구사항 명확화" → "Requirement clarification", 그 안의 "분할 판정" → "Split judgment"·"예외" → "Exception" — `CLAUDE.md` §5·§10, `agents/plan-reviewer.md` 14·15항, `scripts/dlc-task-router.js`(한국어 hook 문구 "요구사항 명확화 '프로토타입-우선'")
* "규모표"·"규모 gate" → "size table"·"Size gate" — `CLAUDE.md` §5 "dlc size table"
* "evidence gate"·"fix loop"·"self-flag"·"self-check" — 원래 영어, 유지 — `CLAUDE.md` §8·§10
* 절 "조사 프로토콜" → "Investigation protocol" — `scripts/dlc-task-router.js` hook 문구, `~/.claude/wiki/docs/dlc-details.md` §B
* "verification grounding" — 원래 영어, 유지 — `scripts/dlc-task-router.js`
* "plan 반영용 요약" → "Summary for the plan" 만 — 공용 wiki `pages/concept/plan-handoff.md`·`pages/concept/hub-and-spoke-isolation.md`
* 원문자 ①②③(삼중 보조·wiki 연계 두 판정·기록 트리거) → 1) 2) 3)
* plan 파일 표지(원문 유지): `⚠️ (구현)`·`[리뷰 미경유]`·`[plan 대비]`·`커밋 단위:`·`커밋 단위: 1개`·`없음`·`생략:`·`코드`/`둘 다`(바뀐 쪽 값)·`[bundle]`·`NEEDS-HUMAN:`·`Split: none — …`·`none — purpose-commit bundle: …`
* reviewer 가 찍는 글자(원문 유지): `Codex 미가용: … out of credits` — `~/.claude/wiki/docs/codex-review.md` §1 이 정한 출력 줄

## 핵심 문구
`/dlc` · `<slug>-log.md` · `<ROOT>/plans/<YYYY-MM-DD>-<slug>/<slug>-plan.md` · `wt` · `git worktree list --porcelain` · `skills/wt/SKILL.md` · §3~§4 · `bash scripts/verify.sh changed` · `~/.claude` · `AskUserQuestion` · `# Goal` · `Why:` · `없음 — <one-phrase reason>` · `intent.md` · `plans/*/intent.md` · `status: open` · `# Plans` · `(not started)` · `<slug candidate> (not started)` · `agents/plan-reviewer.md` · `# Review Disposition` · `[bundle]` · `Split: bundle → <intent.md path>` · `Split: none — <what it tried to split and which coupling prevented it>` · `none` · `# Deferred` · `Split:` · `none — purpose-commit bundle: <shared source> · <units> · <reason for keeping one plan>` · `intent:` · `~/.claude/wiki/docs/dlc-details.md` · `dlc-task-router` · `# Acceptance` · `# Decisions` · `⚠️ (구현)` · `⚠️ <concern> — <what it conflicts with> — <chosen side and reason>` · `⚠️ (구현) <behavior decided> — <other options> — <chosen side and reason> — <file·symbol>` · `> [!conflict]` · [[self-diagnosis-and-improvement-status]] · `⚠️` · `resolved` · `accepted-risk` · `deferred` · `false-positive` · `⚠️ (구현) [리뷰 미경유]` · `what is satisfied` · `how it is checked` · `pass criterion` · `path::test_name` · `status: blocked` · "unverified" · "well-formed ≠ correct" · `wiki/pages/` · `wiki/index.md` · `dlc-early-stop` · `dlc-doc-drift` · `plan-match` · `status` · `/c` · `# Blockers` · `status: in_progress` · `# Tasks` · `- [ ] NEEDS-HUMAN: <question> — <options>` · `blocked` · `plan-blocked` · `dlc-signal.js` · `/e` · `wip:` · `NEEDS-HUMAN:` · `dlc-evidence-ledger` · `PushNotification` · `fixup!` · `commit-check` · `커밋 단위: 1) <unique commit title> — <paths/scope> 2) …` · `커밋 단위: 1개 — <reason>` · `fixup! <title>` · `git log --format='%h %s' $(git merge-base HEAD <default branch>)..HEAD` · `git commit --fixup=<unit sha>` · `git diff` · `git diff <work base>...HEAD` · `fixup_of` · `/e merge` · `- [x] <step> (YYYY-MM-DD) — 생략: <reason>` · `mode: planning` · `mode: post-implementation` · `<base>...HEAD` · `uv run --no-project python "$HOME/.claude/skills/wiki/wiki_search.py" <asset name> <work type>` · `skills/wiki/SKILL.md` · [[lesson-verify-scaffold-purpose-before-removal]] · `wiki/` · `~/.claude/wiki/` · `~/.claude/wiki/index.md` · `/wiki ingest` · `in a ~/.claude main session: /wiki ingest <summary · public evidence · source (public/private)>` · `MEMORY.md` · `item → observed / not observed / mismatched` · "Summary for the plan" · `~/.claude/wiki/docs/codex-review.md` · "Codex review is already running externally. Do not invoke Codex." · `plan-reviewer` · `code-reviewer` · `architecture-reviewer` · `<scratch>/codex-unavailable` · "Codex is unavailable in this session" · `Codex 미가용: … out of credits` · `fix / defer / false-positive / wontfix` · `[plan 대비]` · `코드` · `plan` · `둘 다` · `없음` · `fix` · `resolved`/`accepted-risk`/`deferred` · `[리뷰 미경유]` · `decision/workflow-failures.md` · `scripts/dlc-signal.js` · `/improve` · [[unknowns-discovery]] · `git status --porcelain` · `add -A` · `git log` · `<type>(<scope>): <summary>` · `Co-Authored-By` · `git -C` · `worktree-isolation-bash-guard` · `/wt` · `## Where to read` · `file:line (symbol)` · `file:line` · `unmet`/`unverified` · `Needs confirmation:` · `git merge --ff-only <slug>` · `mode: planning` · <50 · 50~150 · 150+ · 2026-09-09 · 2026-09-16 · ≤2 · 2~4 · ≤1 · 2+ · item 15 · §8(a) · §8(b) · §3-6 · §3-1 · §11 · §12 · §A · §B · §C · §D · §E
