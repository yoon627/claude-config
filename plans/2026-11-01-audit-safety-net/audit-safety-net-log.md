# Review Disposition
- plan-reviewer(CONDITIONAL, 2026-11-01)
  - S1 넓힌 pre-push 가 새 브랜치 push 에서 전체 이력을 훑어 fixture 토큰에 막힘(재현: 850커밋·18MB·10초·6패턴) — fix: 범위를 `pt_scan_pushed` 와 같게(`^origin/main` 제외).
  - S2 전체 파일 스캔이 fixture 토큰이 든 파일의 무관한 편집을 막음(재현) — fix: 추가된 줄만.
  - S3 모든 repo 로 범위가 번짐 — fix: `claude_repo=yes` 전용.
  - S4 bare allow 제거가 2026-10-08 결정(remote-control default 모드 `can_use_tool` 홍수)을 뒤집음 — fix: 정본에는 적되 이 머신 적용을 [post-merge] 사용자 결정으로, 근거(auto 모드 관측)와 함께. wiki 페이지 갱신은 그때.
  - S5 Acceptance 6 이 WebFetch 와 모순 — fix: WebFetch·WebSearch 는 유지로 결정, Acceptance 재작성.
  - S6 은퇴 불가·롤백 없음 — fix: `retireAsk` + 내장 백업.
  - S7 `echo null` Red 가 성립하지 않음(지금도 exit 0) — fix: Red 입력을 `bash -c "git push origin --delete feat"` 등 실제 allow→ask 전환으로; 예외 시 `ask`.
  - S8 `-c`/`eval` 문자열만 보는 것은 `git -C`·`env` 형태를 놓침 — fix: 모든 조각.
  - W1 넓은 glob(`git push -*f*`) — fix: 규칙은 좁게, 합친 플래그는 가드. W2 72개는 재구성 불가 — fix: `--check` 가 로컬 전용 규칙을 나열, README 는 개수 대신 정본 파일을 가리킴. W3 edge(파일 없음·JSON 오류·symlink·동시 쓰기) — fix: Task 1 에 명시. W4 setup.ps1 중단 — fix: node 없으면 warn. W5 바이너리 — fix: `--text` 일관. W6 출력 형식·CI sed — fix: `pt_patch_records` 재사용, sed 양성 테스트. W7 성능 — fix: 한 번의 diff 호출. W8 ps1 미검증 — accepted: CI 에서만. W9 문서 — fix: Task 에 추가. W10 Split 형식 — fix: 출처를 "점검 보고 §2(안전망)" 로 적고 묶음 intent 는 만들지 않음(세 plan 이 한 보고에서 나왔지만 각각 독립 머지 가능·서로 참조 없음 — 묶음 intent 트리거 2 의 "분할" 이 아니라 별개 요구 3개로 본다). W11 Task 순서·이 머신 적용 시점 — fix: [post-merge] main 에서. W12 README 519/520 충돌 — fix: rebase 때 손으로. W13 `--check` 상시 호출 없음 — Deferred(improve.sh 점검 후보).

- code-reviewer(NEEDS DISCUSSION — Critical/Major 없음, 2026-11-01)
  - ⚠️ (구현) (a) CI 의 `PRE_COMMIT_CHECK_CLAUDE_REPO=1` — accepted-risk(타당. 셸에 export 하면 모든 repo 가 넓은 스캔·private-terms 를 읽게 되지만 CI 만 inline 으로 쓴다).
  - ⚠️ (구현) (b) origin/main 포함 조건이 plan 문구보다 넓어 로컬 multi-ref push(`git push origin fresh other`)·`-f main:feat` 에서 이미 게시된 이력을 스캔(재현) — resolved: CI 전용 env `PRE_COMMIT_CHECK_KEEP_BASE=1` 아래에서만 제외를 건너뛴다(로컬은 HEAD 와 동일).
  - Minor 가드가 git 의 옵션 축약(`--dele`·`--m`·`--pru`)을 놓침(재현: `--dele` 가 실제로 삭제) — fix: 3자 이상 접두 일치도 ask.
  - Minor CI 에서 base 가 없고 HEAD == origin/main 이면 넓은 범위가 비는데 로그는 "whole history" — fix: 명시 문구 + 주석.
  - Minor [plan 대비] bootstrap 이 forbidAllow 를 무조건 적용 — plan 은 머신 적용을 사용자 결정으로 — fix: `--keep-allow`, bootstrap 은 그것으로 호출. 바뀐 쪽: 코드.
  - Minor CI main push 종단 테스트 없음 — fix: ci-secret-scan.test.sh 케이스.
  - PLAUSIBLE [plan 대비] 커밋 메시지는 토큰 스캔 안 함(Task 2(b) 의 "레코드" 는 M 도 포함) — fix: 메시지 스캔 추가. 바뀐 쪽: 코드.
  - PLAUSIBLE 토큰 위반 출력이 private term 이 든 경로를 그대로 찍음 — deferred: CI 에는 목록이 없어 공개 경로이고, 로컬은 pt 스캔이 복사된 용어를 잡는다. 토큰 스캔이 `pt_load` 앞에 돌아 순서 변경이 필요 — 별도 작업.
  - Nit 비-Failure 예외 exit 1 → 2 / ask∩retireAsk 겹침 검사 / 임시 파일+rename 원자 쓰기 / 테스트의 env unset — fix. Nit `rg -c "git push -f"` 가 `-c` 재파싱으로 ask — accepted-risk(README 452 의 기존 설계). Nit 기존 fixture 의 리터럴 토큰 5줄 — deferred(이력에 20회 — 재추가하면 막힌다; 실행 시 조립으로 바꾸는 후속). Nit `git clean -*f*` 가 `-n docs/foo` 에 묻음 — accepted-risk(추가 확인일 뿐).
  - 열린 질문 Bash 규칙 대소문자 구분(`checkout -B*` 가 `-b` 에도 묻는가) — [post-merge] 관찰.

# Deferred
- `--check` 를 `skills/improve/improve.sh` 점검에 넣어 settings drift 를 상시 관측(이 머신처럼 정본과 갈린 상태를 /improve 가 보고하게)
- `onFailure: "block"` 도입 여부 — fail-open 정책 변경이라 사용자 결정
- hook `ask` 와 규칙 `ask` 가 같은 명령에 겹칠 때 프롬프트 수 — 적용 뒤 관찰
- 토큰 위반 출력의 경로를 private-terms 와 대조해 "(hidden)" 으로 — 토큰 스캔을 `pt_load` 뒤로 옮기는 재배치, 심각도 낮음
- 기존 테스트 fixture 의 리터럴 토큰 모양 5줄(`pre-commit-check.test.sh`:19·153 등, `ci-secret-scan.test.sh`:9-10)을 실행 시 조립으로 — 그 줄을 다시 더하는 편집이 넓어진 스캔에 막힌다
- Bash 권한 규칙의 대소문자 구분 여부 관찰 — `git branch -D*` 가 `-d` 에 묻지 않는 것이 간접 증거
