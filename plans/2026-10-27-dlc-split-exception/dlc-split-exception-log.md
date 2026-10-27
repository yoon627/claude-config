# Review Disposition
- code-reviewer Major — 예외를 dlc 한 곳에만 넣어 plan-reviewer 14항이 예외를 쓸 때마다 지적한다 — fix: 14항이 예외 표지를 따로 반박(사용자 승인 "세 곳 함께 고치기")
- code-reviewer Major — CLAUDE.md §10 의 `Split:` 형식·트리거 2 가 예외와 모순 — fix: 형식에 예외 표지, 트리거 2 에 예외 언급
- code-reviewer Major(⚠️) — "결합 없음 등" 으로 열린 범위가 §8 "무관한 변경 섞지 않기" 와 충돌 — fix: 같은 출처(한 plan 의 # Deferred·Out of scope, 같은 open intent)로 한정
- code-reviewer Minor — 불가 조건 없음, 리뷰 이득 과장, 예비값 재판정 없음, "안 나뉘면" 절과 충돌, 15항 한국어 인용 — fix: 같은 파일 섞임·structural 이면 불가, "따로 revert" 만, 전제 붕괴 시 재판정, "안 나뉘면" 뒤로 옮기고 "아래 예외면 그 형식", 인용 삭제
- code-reviewer 재리뷰 Minor — plan-reviewer 의 "한 파일에 섞임" 이 "같은 파일을 건드림" 으로 읽혀 동기 사례(같은 파일을 커밋을 나눠 고침)를 거부할 수 있다 — fix
- code-reviewer 재리뷰 Minor — "작은/small" 이 정의 없음 — fix: 삭제(불가 조건이 structural 단위를 이미 막는다)
- code-reviewer 재리뷰 Minor — "같은 open intent" 출처가 넓다(우산형 intent) — wontfix: 리뷰어가 출처를 반박하고, §8 이탈이 보이면 그때 좁힌다
