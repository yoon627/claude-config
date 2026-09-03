---
title: launcher-test-bash3 — test_launcher.sh 의 mapfile 을 bash 3.2 호환으로
status: in_progress
started: 2026-09-03
updated: 2026-09-03
---

# Goal
`skills/jira-worklog/test_launcher.sh:21` 의 `mapfile`(bash 4+)이 macOS 기본 `/bin/bash` 3.2 에서 exit 127 — CI(ubuntu, bash 5)는 통과하지만 로컬 전체 검증이 항상 1건 실패로 끝난다(plan router-notification-fp Deferred). `while read` 루프로 바꿔 양쪽에서 통과시킨다.

# Progress
- 2026-09-03: Red 는 격리 runner 실측(exit 127, `mapfile: command not found`). 2줄 교체 → 같은 bash 에서 exit 0, shellcheck 통과.

# Next
- code-reviewer(low) → `/e merge`.

# Decisions
- shebang 을 brew bash 로 바꾸지 않고 스크립트를 3.2 호환으로 (이유: 테스트는 `bash <script>` 로 호출돼 shebang 이 무시되며, CI·로컬 어느 쪽도 특정 bash 설치를 요구하지 않는 편이 낫다).

# Key Files
- `skills/jira-worklog/test_launcher.sh` — 21행

# Blockers
(없음)

# Acceptance
- [x] macOS `/bin/bash` 3.2 에서 `bash skills/jira-worklog/test_launcher.sh` exit 0 — 검증: 실행 관찰.
- [x] `shellcheck skills/jira-worklog/test_launcher.sh` 통과.
- [ ] CI lint.yml 통과 — 검증: PR checks.
