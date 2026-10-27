# 가리키는 곳 (translate-skill-wt)

## 저장소 안
- wt 의 references 2개가 본문을 `## 주의`·`rm §6`·`request §3.4` 로 가리킨다 — 같은 머지에서 `## Cautions` 로 바꿨다(번호는 그대로).
- `skills/dlc/SKILL.md` "`skills/wt/SKILL.md` request §3~§4" — 절 이름 `request` 와 번호를 그대로 둬 맞다.
- CLAUDE.md `/wt <request>`·`/wt rm <name>`, `skills/e/SKILL.md` `/wt <name>`·`/wt rm <name>` — 명령 형태라 맞다.
- README 의 wt 설명 — 언어 정책 밖(그대로).

## 원문 그대로 둔 문자열
- `세션 활동 없음`·`ticket=(없음)` — `skills/jira-worklog/jira_worklog.py:236,243` 이 출력하는 문자열이라 wt 가 글자로 맞춰 읽는다. 자리표시자 `<이름>`·`<키>` 만 영어로.
- `"로그인 리다이렉트 버그 수정"` — 비ASCII 요청을 slug 로 바꾸는 예시라 입력 자체가 예시다.
- 인자 토큰 `rm`·`?`·정수는 원래 기호·영어.

## [post-merge] 공용 wiki — main 세션
- `~/.claude/wiki/docs/worktree-lifecycle.md` — wt 를 가리키는 곳이 있는지 확인하고(«파일 점유 류»·«부분 성공»·«별도 AskUserQuestion 후에만» 은 그 문서 자신의 문구일 수 있다) wt 문구를 인용한 곳만 영어로.
- 그대로(역사 기록): `pages/decision/dlc-wt-autoflow.md` «이름 오타로 인한 오생성» 등.
