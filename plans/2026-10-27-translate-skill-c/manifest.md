# skills/c/SKILL.md 규칙 목록 (translate-skill-c)

origin/main eaaf7d7 의 skills/c/SKILL.md(82줄·9,511B) 기준. 한 줄 = 한 조항(한정어도 조항의 일부). 번역 대조는 `locations-en.txt`(`<id> | <영어 인용>`).

## 머리말·frontmatter
- F.1 description: 진행 중 plan(§10)을 찾아 남은 작업과 plan↔실제(git/코드) sync 를 진단, 어긋나면 보정, 다음 액션이 명확하면 이어서 실행하는 plan-continue 오케스트레이션
- F.2 description: 그 브랜치 PR 의 사람 리뷰 코멘트도 intake
- F.3 description: `/c` 명시 호출 또는 "진행하던 작업 이어가자" 류 요청 시 사용, 단순 질문·탐색·신규 작업 시작엔 쓰지 않음(새 plan 생성은 dlc 몫)
- H.1 진행 중 §10 plan 을 찾아 남은 작업 + sync 상태 진단, 어긋난 plan 을 실제 상태로 보정, 첫 미완료 Task 가 명확하면 이어서 실행(예외 시 정지·제시)
- H.2 CLAUDE.md §10 **Start**·**In-progress sync** 의 자동화 버전, 충돌 시 CLAUDE.md 우선

## 적용
- A.1 `/c` 명시 호출, 또는 진행하던 plan 을 이어가려 할 때
- A.2 단순 질문·탐색·읽기 전용·신규 작업 시작은 제외
- A.3 plan 이 없으면 새로 만들지 않는다(dlc/작업 시작의 몫)

## 동작 제목
- D.1 3단계: 찾기 → 진단 → 보정·이어실행

## 1. plan 찾기
- 1.1 `ROOT = git rev-parse --show-toplevel`, `BR = git rev-parse --abbrev-ref HEAD`
- 1.2 탐색 위치(존재하는 것만, 중복 제거) 1) `<ROOT>/plans/`
- 1.3 2) cwd 가 worktree 면 main worktree 의 plans(porcelain 첫 `worktree <path>` → `<main>/plans/`), (1)과 같으면 생략
- 1.4 이유: plans/ 는 worktree(브랜치)별 독립이라 양쪽을 봐야 누락이 없다(tracked 지만 브랜치마다 내용이 다르다)
- 1.5 매칭(§10): `BR` 이 plan dir 이름(`<YYYY-MM-DD>-<slug>`)에 포함되는 dir → 그 안 `*-plan.md` 1개
- 1.6 1개 → 채택 / 2개+ → 후보 목록 제시 후 사용자 선택 / 0개 → fallback
- 1.7 fallback: 탐색 위치의 모든 plan(`*/*-plan.md` + 루트 직속 `*.md`) frontmatter 에서 `status: in_progress|blocked` 를 `updated` 내림차순으로 목록 제시 → 사용자 선택
- 1.8 추측으로 자동 선택하지 않는다
- 1.9 전부 done 이거나 없으면 "이어갈 plan 없음" 보고 후 종료

## 2. 진단
- 2.1 plan 을 read(같은 폴더 plan log 가 있으면 함께 — 이전 리뷰 처분·Deferred 를 이어받는다)
- 2.1b 두 축을 본다(남은 작업·sync 점검)
- 2.2 frontmatter `intent:` 가 있으면 그 `intent.md` 도 read — 이유: 공통 Constraints·Open questions·형제 plan 이 거기 있어 델타만으로는 요구가 복원되지 않는다
- 2.3 intent 파일이 없으면 보고에 "intent 링크 끊김" 1줄(3단계 보정 대상)
- 2.4 옛 형식 plan(`# Tasks` 없음)은 §10 대응표대로 읽고 보정
- 2.5 남은 작업: `status` + `# Tasks` 미완료(첫 항목 = 다음 액션) + `# Blockers`
- 2.6 `done` → "이미 done" 안내 후 이어갈지 확인
- 2.7 `blocked` → `# Blockers` 노출, 해소 가능 여부 판단
- 2.8 미완료 Task 가 없거나 첫 항목이 실효 → 3단계에서 실제 상태로 재구성
- 2.9 sync 점검 표 — 최신성(`updated` vs 최근 커밋 날짜, 한참 과거면 어긋남)
- 2.10 Task 경로 실재(미완료 Task 의 backtick 경로, 없는/이동된 파일)
- 2.11 커밋 반영(`git log --oneline origin/main..HEAD`, 체크된 Task 에 없는 커밋)
- 2.12 미반영 변경(`git status --short`, 어느 Task 에도 없는 uncommitted)
- 2.13 완료 여부(`origin/main..HEAD` 가 비었나 / `git branch --merged origin/main`, 머지됐는데 `status≠done`)
- 2.14 plan 무결성(`node scripts/plan-lint.js <채택 plan>`(있으면), §10 형식·끊긴 Acceptance 참조 위반)
- 2.15 점검 명령이 실패하면(origin 없음 등) 그 점검만 skip 하고 보고에 명시
- 2.16 plan-lint 위반은 노출·보정 대상(hard-stop 아님) — 3단계에 반영
- 2.17 PR 리뷰 intake 는 plan 이 매칭된 경우만, read-only — 그 브랜치 PR 의 사람 리뷰 지적(요약·conversation·인라인 line)을 수집해 3단계 처분으로
- 2.18 PR 식별: `gh pr list --head <BR> --state all --limit 3 --json number,state,title`
- 2.19 수집 3소스 — 인라인이 코드 지적의 주 형태라 필수
- 2.20 리뷰 요약·state: `gh pr view <n> --json reviews`(`reviews[].body`·`state`·`author`)
- 2.21 conversation: `gh pr view <n> --json comments`
- 2.22 인라인: `gh api repos/{owner}/{repo}/pulls/<n>/comments --jq '.[] | {user:.user.login, path, line, body}'`
- 2.23 ⚠️ `gh pr view --json reviews,comments` 는 인라인을 주지 않는다(cli/cli #11477) — 빠뜨리면 '없음' 오보(silent false-negative)
- 2.24 사람만: login(또는 `author.login`)이 현재 사용자(`gh api user --jq .login`)면 제외, `[bot]` 으로 끝나면 제외
- 2.25 fail-open: `gh` 미설치·미인증·원격/PR 없음 → 이 점검만 skip + "PR 리뷰: 확인 불가(<사유>)" 1줄
- 2.26 (네트워크 왕복 2-3회, plan 매칭 시에만)

## 3. 보정 + 다음 액션
- 3.1 sync 어긋남이 있으면 plan 파일을 먼저 보정(메인 single writer, §10 진행 중 동기화)
- 3.2 체크된 Task 에 없는 커밋 → 그 커밋이 끝낸 Task 를 체크(없으면 체크된 Task 로 추가) + 커밋 날짜, sha 는 적지 않는다
- 3.3 `wip:`·`fixup!` 커밋은 체크 근거가 아니다
- 3.4 uncommitted 변경 → 현황 반영
- 3.5 없어진/이동된 파일 → 미완료 Task 의 경로 갱신
- 3.6 실제와 다른 `status` → 정정(머지=done, 막힘=blocked + `# Blockers`)
- 3.7 머지=done 은 객관적 사실 기록 — done 이 되면 예외5 로 정지하므로 e 의 세션종료 done 확인과 구분되어 안전
- 3.8 실효된 미완료 Task → 고쳐 쓰고 실제 다음 액션을 미완료 맨 위에
- 3.9 frontmatter `updated:` 오늘로
- 3.10 끊긴 `intent:` 링크 → §10 한계대로 형제 worktree·선행 브랜치에서 `git show` 로 복원, 불가면 링크 제거 + 보고
- 3.11 실제와 다른 `# Decisions` → §10 방식(고쳐 쓰고 이유, 밀려난 안은 기각안)
- 3.12 PR 리뷰 처분 (a) 코드 지적 → 미완료 맨 위에 `- [ ] PR#n 리뷰 반영: <요지>` Task 추가
- 3.13 (a) 미해결은 코멘트 상태·후속 커밋으로 추정, 불확실하면 그대로 노출
- 3.14 (b) 작업방식 교정 → §12 feedback memory 저장 판정을 보고에 포함(대상이면 저장 제안, 저장은 사용자 확인 후 — intake 는 사용자 미지시라 저장 전 확인)
- 3.15 요약 보고: plan 위치·title·status / 남은 작업 / sync 진단·보정 / PR 리뷰 intake 결과 / 다음 액션
- 3.16 첫 미완료 Task 가 명확하면 "진행해도 되나?" 재확인 없이 곧장 진행
- 3.17 코드/파일을 바꾸는 구현이면 규모 불문 dlc 로 넘기고 dlc 의 wt-first 게이트로 worktree 격리 유지(우회 아님 — worktree 생성은 로컬·가역이라 확인 없이, 되돌릴 정보 보고 — §1)
- 3.18 예외면 멈추고 사용자 결정을 기다린다(닫힌 목록 5종)
- 3.19 예외 1: `status: blocked` 또는 미완료 Task 에 `NEEDS-HUMAN:` — 해소가 사용자 몫
- 3.20 예외 2: plan 매칭 실패로 fallback 선택이 필요 — 후보가 1개여도 사용자 선택
- 3.21 예외 3: 미완료 Task 가 없거나 실효돼 재구성한 경우 — 방향 확인 1회
- 3.22 예외 4: 다음 액션이 파괴적·비가역·외부공개(push·머지·삭제·배포·DB migration/write 등 §8 게이트와 그에 준하는 것, 분류 애매하면 멈춤) — 명시 확인
- 3.23 예외 5: `done` plan — 이어갈지 확인
- 3.24 예외 5 단서: 그 브랜치 PR 이 `OPEN` 이면(`/e` 머지 모드의 QUEUED/UNKNOWN) 머지 대기 중 — merge queue 면 끝날 때까지 기다리고 그 뒤 `/e merge` 재실행 안내(외부 쓰기라 예외 4 대로 확인)

## 경계
- B.1 파괴적·외부공개 액션은 이어서 실행하지 않음(push·머지·삭제·배포 — §8), 그 외 명확한 첫 미완료 Task 는 이어서 진행(예외 5종)
- B.2 PR 리뷰 intake 는 read-only — 수집·분류만, 자동 회신·comment·resolve 안 함
- B.3 plan 이 없으면 새로 만들지 않음 — "이어갈 plan 없음"만 보고
- B.4 매칭 실패 시 추측 자동 선택 안 함 — 항상 목록 제시
- B.5 subagent 위임 아님 — plan single writer 는 메인, 메인이 직접 read/보정
- B.6 plan 보정은 사실 기반만 — git/파일로 확인된 것만, 추측으로 Task 체크·Decisions 채우기 금지(CLAUDE.md §1)

## 다른 파일이 가리키는 표지
- 단계 번호 `### 1.`~`### 3.`, 예외 번호 1~5(e·dlc 가 "예외" 로 가리키지 않음 — c 내부의 "예외5"·"예외 4" 참조만), 표의 점검 6행.
- 저장소 안에서 c 를 글자로 인용하는 곳 없음: e "(c 1단계와 동일)"·CLAUDE.md "the skills c, e and dlc" 는 번호·이름. `scripts/frontmatter-lint.test.js` 의 OLD_C 는 0efce86 이전 description 을 고정한 테스트 입력이라 현재 파일과 무관.

## 핵심 문구 검색 세트
`/c` · git rev-parse --show-toplevel · --abbrev-ref HEAD · git worktree list --porcelain · *-plan.md · in_progress|blocked · intent: · intent.md · plan log · # Tasks · # Blockers · # Decisions · git log --oneline origin/main..HEAD · git status --short · git branch --merged origin/main · plan-lint.js · gh pr list --head <BR> --state all --limit 3 --json number,state,title · gh pr view <n> --json reviews · gh pr view <n> --json comments · gh api repos/{owner}/{repo}/pulls/<n>/comments · cli/cli #11477 · gh api user --jq .login · [bot] · fail-open · wip: · fixup! · git show · NEEDS-HUMAN: · QUEUED/UNKNOWN · /e merge · single writer · §8 · §10 · §12
