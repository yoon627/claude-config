# Review Disposition

## 리뷰 4개 병렬 (2026-10-27, Codex 미가용) — 번역을 먼저 적용하고 계획 리뷰·독립 대조 2개·code-reviewer 를 함께 돌렸다
- 게이트 줄 대조: OK 57, CHANGED 1 — :131 "삭제 계열(아래 첫 bullet)" → "(the first bullet above)". 원문의 방향이 틀렸다(가리키는 bullet 은 위에 있다) — fix 아님(번역이 이미 바로잡았다), Decisions 에 기록.
- 조항 대조 + manifest 감사: OK 117, CHANGED 1(N.2 — 위와 같은 :131). 감사가 찾은 manifest 밖 세부 35개는 번역에 모두 있다. 문구 다듬기 2곳(:53 "If it returns a successful return" · :125 "no-op + warning only if…") → fix. manifest F.1 이 description 에 없는 "인자 없음=list" 를 적었다 → fix(manifest).
- code-reviewer APPROVE(Critical 0):
  - M1 :116 "a total" 이 jira-worklog 출력 글자 `합계`(jira_worklog.py:242-244)와의 연결을 끊는다 — fix: "a total (`합계 <duration>`)", check-wt 의 원문 그대로 둔 문자열에 추가.
  - M2 :114 "assumes no deletion when it cannot be detected" 의 대상이 모호 — fix: "if the merge state cannot be determined, the premise is not to delete".
  - M3 :131 바로잡음을 Decisions 에 — fix(plan).
  - N1 :21 "(ask section —" 이 없는 절을 가리킨다(원문부터) — fix: "(Question mode section —".
  - N2 :53 — fix(위 조항 대조와 같은 곳). N3 :50 "Main judgment" → "Main detection" — fix.
  - D1~D3 규칙 결함 — defer(Deferred).
- 계획 리뷰 CONDITIONAL:
  - S1 위치 인용이 조항 일부만 덮는다 — 인용 밖 구간 변형 8개가 모두 PASS, 문장 삭제 211개 중 21개를 놓쳤다(참조 포인터 :74·:76, 보고 시점 :80, dlc 진행 :79, `<default>` 정의, stderr 목록 등) — fix:
    - check-wt 5절 신설: 인용이 덮은 글자를 표시하고, 제목·frontmatter 틀을 뺀 나머지에서 덮이지 않은 구간(글자 12개 초과)이 있으면 FAIL. 인용이 파일 안에서 두 번 나오면 FAIL(1절).
    - 처음 돌려 24구간이 나왔다 — 빠진 조항 4개(R.3.4d·R.3.6c·R.4.1b·X.4f4)를 manifest 에 더하고 12개 조항의 문구·인용을 넓혔다(EC.8·RR.3 포함).
    - 변형 시험을 바꿨다(scratch `mut-wt.js`): A 손으로 고른 21개(리뷰어 8개 포함) 21/21 FAIL, B 모든 비제목 줄의 문장을 하나씩 지우는 228건 228/228 FAIL.
  - S2 wt 가 글자로 맞춰 읽는 git/OS stderr 가 핵심 문구에 없다 — fix: "modified or untracked files"·"use --force"·"Access is denied"·"being used by another process"·"Directory not empty"·"Invalid argument"·"Unable to find current revision" 을 추가. Decisions 에 원문 그대로의 문자열은 두 방향(스크립트 출력·stderr)이라고 적었다.
  - W `합계`·`등록 차단` 도 출력 글자 — fix: 둘 다 원문 그대로(backtick). 기각안(부재 판정에 쓰이는 것만 원문 유지)은 Decisions 에.
  - W :131 바로잡음 기록 — fix(위 M3). W :21 ask section — fix(위 N1).
  - W e 포인터가 단계 이름 없이 "condition 4" 만 — fix: "e blocks it with its step 7 condition 4 (merged) gate", check-wt 4절 문자열도 같이.
  - W :53 "no active worktree session" 은 하네스 반환 원문을 확인하지 못했다 — false-positive 아님, 설명으로 두고 핵심 문구에 넣지 않는다(❌ 원문 미확인).
  - W 같은 부분 인용 문제가 c 다음에 다시 나왔다 — fix: Workflow Findings.
- 앞 단위 Deferred 처리: translate-claude-md log·translate-skill-e log 의 "wt:114 조건5" 는 이 단위에서 고쳤다(그 log 들은 done plan 이라 손대지 않는다).

# Deferred
- D1 `skills/wt/SKILL.md` rm 인자 누락의 출력이 두 곳에서 다르다 — 인자 절(:22) "표 출력 후 종료" vs rm 1단계(:105) "사용법 안내 + list". 심각도 낮음 — 규칙 변경이라 별도 작업.
- D2 `skills/wt/SKILL.md` §4 near-miss 후보 집합에 방금 만든 slug 자신이 들어갈 수 있는지 정하지 않았다(생성 뒤 판정하면 정규화한 요청과 자기 branch 가 일치). 심각도 낮음 — 별도 작업.
- D3 `skills/wt/SKILL.md` rm 6단계·`references/rm-recovery.md` §C 의 파일 점유 stderr 목록(4종)이 `~/.claude/wiki/docs/worktree-lifecycle.md` §C 보다 좁다("Permission denied"·"Device or resource busy" 없음). 심각도 중간 — 규칙 변경이라 별도 작업.

# Workflow Findings
- 2026-10-27 번역 대조의 부분 인용 문제가 translate-skill-c(계획 리뷰 S1) 다음 단위에서 다시 나왔다 — c 에서는 개별 조항을 넓히기만 하고 기계 검사를 두지 않았고, 변형도 이미 인용한 문자열에서만 골랐다. 대책: 덮이지 않은 구간 검사(check-wt 5절)와 문장 삭제 sweep 을 다음 translate-repo 단위의 기본 방법으로 쓴다(intent `# Plans` 의 이 plan 줄에 적었다). 공용 wiki `workflow-failures` 적립은 main 세션에서 판정(동일 유형 2회).
- (2026-10-31 처리) D1·D2·D3 — `fix(wt)` 커밋 3개(wt-small-fixes). D2 는 near-miss 되돌리기 안내가 만든 slug(충돌 접미사 포함)를 가리키게도 고쳤다
- 공용 wiki `docs/worktree-lifecycle.md` §C 의 파일 점유 목록 — 삭제 실패의 "Permission denied" 는 Linux·macOS 에서 실제 권한 문제(root 소유 파일)일 수 있는데 점유로만 분류한다(근거는 Windows 실측). 문서·`skills/wt` 에 "또는 실제 권한 문제(소유자 확인)" 를 더하는 안 — main 세션에서. 심각도 낮음(wt-small-fixes code-reviewer)
