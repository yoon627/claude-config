---
title: jira-task-dated-items — jira-task description 항목을 날짜 줄 + bullet 항목으로
status: done
started: 2026-10-07
updated: 2026-10-07
---

# Goal
jira-task 가 Jira description 에 쓰는 항목을 `작업 내용: 1~3문장` 에서 `날짜 줄 + 작업 내용 bullet 목록` 으로 바꾼다.

# Intent
- Problem: 사용자 요청 — 작성할 때 날짜와 작업 내용을 항목화해서 추가.
- Constraints: marker 기반 upsert(같은 marker 재실행 시 중복 없음·그 항목만 갱신)와 기존 본문 보존을 유지한다. 이전 형식 항목(같은 marker)도 새 형식으로 교체돼야 한다.
- Out of scope: 없음 — 작업시간·변경 파일 목록을 본문에 넣지 않는 기존 규칙은 그대로.

# Progress
- 2026-10-07: 형식 변경(날짜 굵게 + `- 항목`) 구현·테스트, 작성 규칙을 jira-task SKILL.md·e/SKILL.md·README 에 반영. code-reviewer(+Codex) 지적 반영 후 unittest 21 OK, verify syntax·python 축 ALL PASS. Acceptance 4(CLI preview 실제 실행)는 사용자가 실행을 거부해 `main()` preview 단위 테스트로 대신했다.

# Next
- 없음 — main 에 로컬 ff-merge 로 종결(push 는 요청 시).

# Review Disposition
- [Major] 내용 없는 bullet(`-`·`1.`)이 항목으로 통과 — fix(정규식 `(?:\s+|$)`, 거부 테스트 추가).
- [Minor] `- 작업 내용: X` 접두 잔존 — fix(bullet 제거 뒤 heading 접두 재검사).
- [Minor] `2026. 10. 7` 같은 숫자 시작 항목이 잘림 — fix(번호 접두를 1~2자리로 제한, 테스트 추가).
- [Minor] 옛 형식 항목 교체 테스트 없음 — fix(fixture 테스트 추가).
- [Minor] 빈 요약 거부 테스트·오해 소지 메시지 — fix.
- [Nit] 저장 검증이 strong mark 를 보지 않음 — wontfix(텍스트 비교는 Jira 의 node 분할·attrs 추가에 견고하도록 일부러 고른 것, 피해는 서식뿐).
- [Nit] `elif line` 미사용 — fix. SKILL.md 벗기는 접두 목록 불일치 — fix.

# Decisions
- wiki 조회: jira-task 관련 decision 없음(아래 Progress 참조) — 따를 기존 결정 없음.
- 항목은 한 paragraph 안에 hardBreak 로 `날짜(strong)` / `- 항목`… / marker. ADF `bulletList` 는 기각 — 항목 하나가 여러 block 으로 쪼개져 marker block 단위 upsert·검증 로직을 다시 짜야 하고, 사람이 사이에 block 을 넣으면 교체 범위가 모호해진다.
- 날짜는 marker 의 `date=` 에서 꺼낸다 — marker 가 이미 항목의 identity 이고 `--date`/timezone 해석 결과를 담고 있어 시그니처를 늘리지 않는다.
- 요약 파일은 줄 하나 = 항목 하나. 입력 줄의 기존 bullet(`-`·`*`·`•`·`1.`)과 이전 형식 `작업 내용:` 접두는 벗겨 중복을 막는다.
- 작성 규칙 추가(2026-10-07 사용자 승인 — 실제 task 본문 예시에서 리베이스·테스트 정비가 항목으로 들어간 것을 보고): task 목표와 관련된 기능·동작 변경만, 구현 경위가 아니라 결과로 항목당 한 줄 1~4개, 적을 항목이 없으면 갱신 자체를 건너뛴다. 날짜 없는 단일 요약 덮어쓰기는 기각 — 날짜 표시 요청과 맞지 않고 이력이 사라진다.
- 커밋 단위: 1개 — 스크립트·테스트·문서가 같은 형식 변경 하나.

# Acceptance
1. 렌더: 요약 2줄 입력 → description 항목 줄이 `[날짜, "- 항목1", "- 항목2", marker]`. 검증: unittest. 통과: 테스트 green.
2. 입력 정규화: `- `/`* `/`1. `/`작업 내용:` 접두가 중복되지 않음. 검증: unittest.
3. upsert 불변: 같은 marker 재실행 unchanged, 다른 요약이면 updated, 다른 marker 는 같은 heading 아래 추가. 검증: 기존 DescriptionBody 테스트 green.
4. preview 실제 실행 출력에 날짜 줄과 bullet 이 보임. 검증: `--summary-file` 로 dry-run 실행 관찰.
5. 문서 동기화: jira-task SKILL.md, e/SKILL.md, README 의 `작업 내용:` 한 줄 설명이 새 형식으로. 검증: rg 로 옛 서술 0건.
6. `bash scripts/verify.sh` 의 관련 축 통과.

# Key Files
- skills/jira-task/jira_task.py — 항목 렌더(`_description_entry_lines`)
- skills/jira-task/test_jira_task.py — 형식 테스트
- skills/jira-task/SKILL.md, skills/e/SKILL.md, README.md — 요약 작성 규칙

# Blockers
