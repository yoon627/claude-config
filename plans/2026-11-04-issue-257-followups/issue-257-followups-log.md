# Review Disposition
- code-reviewer 1차(REQUEST CHANGES, 2026-11-04)
  - Major [plan 대비] 점검 13 을 deep 전용 10~12 앞에 둬 머리말 번호 계약(`scripts/native-overlap-lint.test.js` — 파일 순서로 1..N)이 깨짐, `verify.sh changed` 가 `FAILED: 1` — fix: 블록을 deep 블록 뒤·요약 앞으로. 바뀐 쪽: 코드(Decision "13 으로 둔다" 는 유지).
  - Minor 점검 13 이 exit 2 가 아니면 모두 `[ok]` (node 부재 127·출력 형식 변경도) — fix: rc 0 만 ok, rc 1 인데 개수를 못 읽으면 warn, 그 밖의 exit 는 info skip. 테스트 2건 추가.
  - Minor ps1 이 추가된 줄마다 `Get-TokenPath` 를 부름(sh 는 걸린 자리만) — fix: `+++` 헤더마다 한 번.
  - Minor 주석 "토큰 보고는 비공개 용어를 찍지 않는다" 가 목록이 깨졌을 때는 거짓 — fix: "목록을 읽었을 때" 로 좁힘. 깨진 목록일 때 숨기지 않는 동작은 변경 전과 같고, 그 자체로 커밋·push 를 막는다.
  - Nit 숨긴 뒤 중복 제거라 서로 다른 숨긴 파일의 같은 줄·같은 패턴이 한 줄로 합쳐짐 — wontfix: 두 엔진이 같고 차단 결과는 그대로.
  - ⚠️ (구현) 숨긴 자리에 줄 번호를 남김 — accepted-risk(리뷰 반박 없음).
  - ⚠️ (구현) 목록이 깨지면 숨기지 않음 — accepted-risk(위 Minor 의 주석 수정으로 서술을 맞춤).

# Deferred
- `skills/jira-task/test_jira_task.py:20` 이 `Quoted secret assignment` 패턴에 걸린다(따옴표 친 `token` 대입 한 줄) — jira 스킬은 사용자 지시로 건드리지 않음. 그 줄을 다시 쓰는 편집은 넓은 토큰 스캔에 막힌다(낮음).
