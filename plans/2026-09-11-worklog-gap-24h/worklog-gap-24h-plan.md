---
title: worklog-gap-24h — 기본 간격 상한 24시간 및 집계 개선 조사
status: in_progress
started: 2026-09-11
updated: 2026-09-11
---

# Goal
jira-worklog 기본 max-gap을 24시간으로 변경하고 worktree 시간 계산 개선점을 조사한다.

# Progress
- 2026-09-11: origin/main@a01340d에서 worktree 생성. 기존 108개 테스트 통과. 24시간 경계 테스트를 먼저 수정해 0 != 86400 실패 확인 후 상수 1440 및 문서 수정.
- 2026-09-11: 변경 후 108개 통과, 설정 기본값 1440/명시 override 480 보존 확인. CSTP1-3000 dry-run은 24h와 8h 모두 세션 6개/항목 8개/5h 4m(이전 대화 이후 세션 추가). Codex 독립 리뷰 APPROVE. simplify 점검상 추가 추상화/정리 불필요.

# Next
검증된 변경을 로컬 main에 fast-forward 병합하고 개선 조사 결과를 사용자에게 제시한다.

# Decisions
- 사용자 요청에 따라 기본값만 1440분으로 변경한다. 명시적인 CLI/환경변수/TOML 설정은 보존한다.
- 시간 파서 개선은 조사와 제안까지 수행한다. 알고리즘 변경은 과거 Jira 시간에 영향을 주므로 별도 계획으로 제시한다.
- small 변경: 상수와 기존 테스트/문서 동기화. 새 의존성이나 API 변경 없음.
- EnterWorktree 도구가 없어 모든 명령에 worktree cwd를 명시한다. .gitmodules와 bootstrap이 없어 해당 셋업은 생략, codegraph init 성공.
- Codex 독립 code-reviewer APPROVE. Claude CLI code-reviewer도 실행했으나 응답이 없는 상태가 지속되어 중단했다(미검증). Codex 독립 리뷰 및 전체 실행 검증을 근거로 진행한다.

# Key Files
- skills/jira-worklog/jira_kit/session_time.py — 공통 기본값.
- skills/jira-worklog/test_session_time.py — 24시간 작업 구간 경계 테스트.
- skills/jira-worklog/SKILL.md — 기본값과 유휴시간 포함 한계.
- README.md — 사용자 안내 동기화.

# Blockers
없음.

# Acceptance
- [x] 기본 max-gap 1440분이며 24시간 작업 구간 포함, 상한 초과/사용자 대기 제외가 기존 테스트와 함께 통과한다 — unittest 108개 통과 및 resolve_config 기본값/override 실행 확인.
- [x] README와 SKILL의 현재 기본값이 24시간으로 일치한다 — diff와 독립 리뷰 확인.
- [x] 실행 검증 및 개선 조사 결과를 보고한다. Jira 쓰기는 수행하지 않는다 — 격리 runner scripts/verify.sh exit 0 ALL PASS(skip 없음), CSTP1-3000 dry-run 확인, Deferred에 조사 증거 보존.

# Deferred
- 이전 조사에서 발견한 인증 설정 override, URL 검증, 등록 동시성 문제는 이번 기본값 변경 범위 밖이다.
- Codex 질문 대기 과대계상: codex_session.py에서 모든 response_item을 assistant로 처리하여 request_user_input→2시간 후 output을 7200초로 계산(mock 재현). 원인: 대기 구간 포함 → 호출 종류 미분류 → user_message만 사용자 대기 신호로 구현. call_id 기반 대기 구간 제외를 우선 제안한다.
- Codex 작업 종료/재시작 공백: user_message 없이 response→task_complete→2시간 뒤 task_started→response를 7201초로 계산(mock 재현). 원인: 종료 공백 연결 → lifecycle 이벤트 무시 → 상태 없는 인접 간격 추정. 활성 turn 구간 제한과 구형 로그 fallback을 제안한다.
- Codex 부모/자식 중복: 현 sessions 1001개 중 source.subagent 292개. 필터 없이 탐색하고 세션별 합산하므로 부모 대기와 자식 실행이 겹칠 수 있음(구체 과대량 미측정). 부모/자식 구간의 worktree별 union 필요 여부를 합의한다.
- 현재 sessions 1001개에서 session_meta/turn_context cwd 복수 값 파일은 0개(archived 제외). 이동 지원은 여전히 미구현이며 shell 도구 workdir 변경은 이 메타데이터 통계로 검증할 수 없다.
- tzdata 미설치로 launcher가 시스템 로컬 시간대를 사용한다는 경고 확인. 이번 기본값 변경과 독립이다.
