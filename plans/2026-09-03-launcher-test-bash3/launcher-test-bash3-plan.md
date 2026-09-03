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
- `skills/jira-worklog/test_launcher.sh` — 21~22행

# Blockers
(없음)

# Review Disposition
code-reviewer(단독 — Codex 는 크레딧 소진으로 미가용, 호출은 새 정본으로 첫 시도 수용) APPROVE, CONFIRMED defect 0.
- fix — Key Files 행 표기, 이전 plan(router-notification-fp) Deferred 해소 표기 (Nit).
- defer — CI(ubuntu bash 5)+shellcheck 가 bash4-ism 회귀를 못 잡음 (Minor): 아래 Deferred.
- wontfix — 주석 어순 (Nit, §6 허용 범위) / pre-existing argv 개수·PATH 의 `/usr/bin/uv` 케이스 (범위 밖, 아래 Deferred).

# Deferred
- bash4-ism(`mapfile`·`declare -A`·`${x,,}` 등) 회귀 가드 없음 — README 에 "`*.sh` 는 bash 3.2 호환" 한 줄 또는 CI macos job(`/bin/bash` 명시 필요, runner PATH 의 bash 가 brew 5 일 수 있음 ❌모름). 심각도 minor.
- `test_launcher.sh` 가 PATH 를 `/usr/bin:/bin` 으로 고정하는데 `/usr/bin/uv` 가 있는 머신에선 스텁 대신 실제 uv 가 실행돼 테스트가 잘못된 이유로 깨짐(pre-existing). 심각도 minor.

# Acceptance
- [x] macOS `/bin/bash` 3.2 에서 `bash skills/jira-worklog/test_launcher.sh` exit 0 — 검증: 실행 관찰.
- [x] `shellcheck skills/jira-worklog/test_launcher.sh` 통과.
- [ ] [post-merge] CI lint.yml 통과 — 검증: PR checks(`/e merge` M5).
