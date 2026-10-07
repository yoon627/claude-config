---
title: jira-task-drop-marker — description 항목에서 [jira-task] marker 줄을 없애고 날짜 줄로 식별
status: done
started: 2026-10-07
updated: 2026-10-07
---

# Goal
Jira description `작업 내용` 항목에 보이던 `[jira-task] ticket=… date=… worktree=… session=…` 줄을 없앤다. 항목 식별은 섹션 안의 날짜 줄로 한다.

# Intent
- Problem: 사용자 요청 — marker 줄은 읽는 사람에게 필요 없는 내용이다.
- Constraints: 같은 날 재실행에 중복이 생기지 않아야 한다. 같은 날 기존 항목은 **읽은 뒤에만** 교체한다(지문으로 강제). 기존 항목을 새 요약에 담는 것은 에이전트 책임이고, 사용자는 승인 전에 preview 에서 교체 전·후를 본다. 사용자가 쓴 본문(섹션 밖)은 건드리지 않는다. 이미 marker 가 붙은 옛 항목은 그 날짜를 갱신할 때 marker 를 걷어낸다.
- Out of scope: 항목 삭제·수정 기능(사람이 Jira 에서 직접 편집). 섹션 밖 본문 정리.
- 분할: 없음 — 식별 방식 교체와 marker 제거는 한쪽만 머지되면 중복 생성 또는 식별 불가가 돼 한 머지에서만 유효하다.

# Progress
- 2026-10-07: 착수. 직전 작업 `jira-task-dated-items`(7b20092, main 로컬) 위. 사용자 요청으로 "그날 기존 항목을 읽고 다시 요약"하는 방식으로 설계를 바꿨다. plan-reviewer·code-reviewer 2회(재리뷰 APPROVE)의 지적을 반영했다. unittest 28 OK, verify syntax·python ALL PASS. 실제 Jira 를 읽는 preview 출력을 관찰했다. 사용자의 실제 Jira 티켓은 원문을 백업한 뒤 09-18·10-06 을 재게시했고, 다시 읽어 marker 0줄과 본문 보존을 확인했다. TDD 순서: 구현을 테스트보다 먼저 썼다(Red 확인 없음). Major 재현 테스트는 리뷰어가 옛 코드에서 probe 로 재현을 확인했다.

# Next
- 없음 — main 로컬 ff-merge 로 종결(push 는 요청 시).

# Decisions
- wiki 조회: 직전 작업에서 jira-task 관련 decision 없음 확인 — 따를 기존 결정 없음.
- 식별 키 = `작업 내용` heading 뒤 paragraph 중 첫 줄이 날짜인 것(옛 형식은 `date=<날짜>` 가 든 `[jira-task]` 줄을 가진 것). heading 앞 사용자 본문에서는 찾지 않는다.
- ~~같은 날짜가 있으면 기계적 병합(없는 항목만 덧붙임)~~ → **에이전트 재요약 + 교체**로 변경 (이유: 사용자 요청 2026-10-07 "그날 작성한 게 있으면 읽어보고 요약"). preview 가 자격증명이 있으면 Jira 를 GET 해 그날 기존 항목을 보여주고, 에이전트는 기존 항목과 이번 작업을 합쳐 1~4개로 다시 쓴 요약으로 preview 를 다시 돌린다. `--post` 는 그날 블록을 그 요약으로 교체한다. 기계적 병합 기각 — 문구만 다른 중복이 쌓이고 항목 수 상한(1~4)을 지킬 수 없다.
- 읽지 않은 교체 방지: `--post` 는 GET 한 그날 기존 항목의 지문을 `--expect-existing <지문>` 으로 받아야 한다(preview 가 지문을 출력). 기존 항목이 있는데 지문이 없거나 다르면(그 사이 다른 세션이 갱신) 중단한다. 기존 항목이 없으면 지문은 `none`.
- 섹션 = `type=heading` 이고 텍스트가 `작업 내용` 인 첫 블록부터, 같은 레벨 이하의 다음 heading 또는 문서 끝까지. 새 날짜 항목은 섹션 끝에 넣는다(문서 끝이 아님). 섹션이 없으면 문서 끝에 heading 과 함께 만든다.
- 그날 블록 = 섹션 안에서 첫 줄이 정확히 그 날짜(`^\d{4}-\d{2}-\d{2}$`, strong 불요)인 블록부터 다음 날짜 블록 직전까지(사람이 Enter 로 쪼갠 항목 포함) + 옛 형식으로 `[jira-task] … date=<그 날짜>` 줄을 가진 블록. 여러 개면 전부 새 블록 1개로 교체된다.
- 지문 = 그날 블록들의 `_adf_node_text` 를 순서대로 이은 텍스트(marker 줄 포함)의 sha256 앞 12자, 없으면 `none`. ADF JSON 을 해시하지 않는 이유: Jira 가 attrs 를 붙여 GET 마다 달라질 수 있다(⚠️추정).
- preview 는 Jira 를 읽어 그날 기존 블록·지문·교체 후를 출력한다. 자격증명이 없거나 GET 실패면 그 사실과 지문 `unknown` 을 출력하고 종료코드 0(preview 는 막지 않는다). `--post` 는 `--expect-existing` 이 **필수**이고 현재 지문과 다르면(`unknown` 포함) 쓰지 않고 중단한다. 결과가 기존과 같으면 쓰지 않는다(unchanged).
- PUT 후 검증: 섹션 안 그날 블록이 정확히 1개이고 텍스트가 렌더 결과와 같으며 `[jira-task]` 줄이 없다. 다른 날짜의 옛 marker 는 그 날짜를 갱신할 때 걷힌다.
- 남은 리스크(accepted): post 안의 GET→PUT 사이 다른 편집은 막지 못한다(기존 동작과 같다).
- `_summary_from_args` 의 `[jira-task]` 예약 검사는 유지 — 요약이 옛 marker 로 오인되지 않게.
- `--session-id`·`JIRA_TASK_SESSION`·`TaskContext.session`·`make_marker` 제거 — marker 에만 쓰였다. `--worktree` 는 티켓 추출에 쓰여 유지.
- 커밋 단위: 1개 — 식별 방식 교체 하나.

# Acceptance
1. 새 항목에 `[jira-task]` 줄이 없다: 렌더 결과가 `[날짜, - 항목…]`. 검증: unittest.
2. 같은 날짜 재실행: 같은 요약이면 unchanged, 다른 요약이면 그날 블록만 교체. preview 가 그날 기존 항목과 지문을 출력하고, `--post` 는 지문 불일치·누락 시 중단. 검증: unittest.
3. 옛 형식(marker 포함, 세션별 여러 블록) 같은 날짜 → 한 블록으로 합쳐지고 marker 줄이 사라진다. 검증: unittest.
4. 섹션 앞·뒤(다음 heading 이후) 사용자 본문의 날짜 문단은 건드리지 않고, 새 항목은 섹션 끝(뒤 heading 앞)에 들어간다. 검증: unittest.
5. 저장 후 검증, 지문 불일치·`unknown` 에서 PUT 없음, attrs 만 다른 같은 텍스트는 같은 지문. 검증: unittest(mock).
6. 문서(jira-task SKILL.md·e/SKILL.md·README): marker·session 서술 제거, preview→재요약→preview→승인→`--post --expect-existing` 절차. 검증: rg + 읽기.
7. verify syntax·python 축 ALL PASS.
8. (가장 위험 — 맨 마지막, GET 원문을 scratchpad 에 백업한 뒤) 사용자의 실제 Jira 티켓에서 기존 두 날짜 항목을 새 도구로 `--date` 별 재게시해 marker 를 걷고, 다시 읽어 marker 0개·항목 유지 확인. 사용자 요청("이런 내용도 안붙여도 될 것 같네") 범위.

# Review Disposition
- [plan] Constraint 와 교체 결정 모순 → fix(읽은 뒤에만 교체 + preview 전후 표시로 재서술). 섹션 범위·지문 정의·unknown 처리·`/e` 절차 → fix(Decisions 반영).
- [code] Major: 다른 날짜 옛 marker 블록이 그날 범위에 들어가 삭제 → fix(`_legacy_marker_date`, 재현 테스트 2배치).
- [code] 섹션 안 하위 heading 까지 교체 → fix(heading 에서 범위 종료, 테스트).
- [code] preview/post 날짜 미고정 → fix(문서에서 `--date <preview 날짜>` 고정).
- [code] `/e`·SKILL 의 지문 불일치 대응 불일치 → fix(`/e` 는 재시도 없이 "게시하지 않음" 보고).
- [code] 깨진 ADF 에서 preview exit 2 → fix(계산을 try 안으로).
- [re-review] APPROVE. `TypeError`(content: null) 가 preview 밖으로 나감 → defer(이번 변경 전부터 있던 문제).
- [re-review] 한 문단에 여러 날짜가 섞인 옛 항목 → wontfix(이 도구가 만든 적 없는 배치, preview 에 그대로 보인다).

# Deferred
- `_adf_node_text` 가 `content` 가 list 가 아닌 노드에서 `TypeError` — preview 가 traceback 으로 끝남. 심각도 낮음. skills/jira-task/jira_task.py.

# Key Files
- skills/jira-task/jira_task.py — 식별·병합·검증
- skills/jira-task/test_jira_task.py
- skills/jira-task/SKILL.md, skills/e/SKILL.md, README.md

# Blockers
