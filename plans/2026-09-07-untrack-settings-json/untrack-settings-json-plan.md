---
title: untrack-settings-json — settings.json 을 git 추적에서 제외해 머신별 값 재발 루프를 끊는다
status: done
started: 2026-09-07
updated: 2026-09-07
---

# Goal

`settings.json` 을 tracked 에서 제외한다. Claude Code 가 이 파일에 머신별 절대경로·사내 식별자를 자동으로 써넣기 때문에, tracked 인 한 `git pull` 이 주기적으로 막히는 재발이 구조적으로 예정돼 있다. 키 단위 제거(증상 억제)를 반복하지 않고 원인을 없앤다.

# Progress

- 2026-09-07: `git pull --rebase` 가 `M settings.json` 으로 거부됨 → 원인이 `/auto-mode-setup` 이 쓴 `autoMode` 블록임을 확인. 그 블록에 사내 IP(`192.168.62.48`)·도메인(`aigw.autocrypt.co.kr`)·조직명(`autocrypt`)·머신 절대경로가 포함되고 이 repo 는 **public**.
- 2026-09-07: 공식 문서로 `autoMode` 의 유효 스코프가 `~/.claude/settings.json` / managed settings / `--settings` 뿐임을 확인 — `settings.local.json` 이관은 조용히 무시되므로 불가.
- 2026-09-07: managed settings 경로(`C:\Program Files\ClaudeCode\`)는 사용자가 Administrators 그룹이 아니라 쓰기 불가 → 탈락.
- 2026-09-07: Explore 로 영향 범위 확정 — CI 2곳·가드 1곳이 "settings.json 이 tracked" 전제에 의존.
- 2026-09-07: 사용자 지적으로 재발 이력 확인 — 동일 실패 3회차(Orca 훅 → gitkraken → autoMode). `MEMORY.md` 인덱스에 lesson 링크가 없어 자동 상기가 성립한 적 없음이 재발의 구조적 원인.
- 2026-09-07: 구현 완료 — `.gitignore`·`git rm --cached`·CI·가드·doc-drift·README·wiki 16파일(커밋 `9ef4717`). 로컬 CI 동등 스위트 전부 통과(node --check 30, 단위테스트 13종, bash 3종, shellcheck, plan-lint).
- 2026-09-07: main 복귀 후 §13 짝 적립 완료 — `feedback-no-machine-values-in-tracked-config.md` + `MEMORY.md` 인덱스 줄(gitignored 라 이 브랜치에는 포함되지 않는다). 3회 재발의 근본 원인이 이 짝의 부재였다.
- 2026-09-07: main 작업트리의 `settings.json` 을 HEAD 로 되돌려 머지 경로를 확보(백업 스크래치패드 `settings.json.automode-backup`, 원본과 동일함 diff 확인). 머지 후 그 백업을 제자리에 복원해야 autoMode 가 살아난다.
- 2026-09-07: PR #161 (push → PR → checks → merge).

# Next

(없음 — PR #161 머지로 종료. 머지 후 main 의 `settings.json` 을 백업본으로 복원하는 것만 남는다.)

# Decisions

- **settings.local.json 이관 안 함** (이유: `autoMode` 가 그 파일에서 읽히지 않음 — 공식 문서 "The classifier doesn't read `autoMode` from project settings in `.claude/settings.json` or `.claude/settings.local.json`"). 기존 lesson 의 표준 remedy 가 이 키에는 통하지 않는다는 새 사실.
- **managed-settings.json 안 씀** (이유: `C:\Program Files\ClaudeCode\` 쓰기에 관리자 권한 필요, 사용자는 Administrators 그룹 아님).
- **sanitize 후 커밋 안 함** (이유: 로컬엔 실제 값이 있어야 auto mode 가 동작하므로 `settings.json` 이 영구 `M` 상태가 된다 — 사용자 지적).
- **skip-worktree 안 씀** (이유: 멀티머신 조용한 분기를 구조적으로 보장 — `lesson-tracked-config-machine-paths` 가 기록한 2026-08-12 사건의 재현).
- **untrack 채택** — 12파일 비용을 알고도 사용자가 재확인. 근본 원인 제거는 이 경로뿐.
- **subagent 리뷰 생략** — 이 세션 지침이 "사용자 요청 없이 Agent 도구 사용 금지"라 CLAUDE.md §5 의 plan-reviewer/code-reviewer 를 메인 직접 점검으로 대체(§9 의 미가용 시 사유 기록에 준함).

# Key Files

- `.gitignore` — 화이트리스트 19행 `!/settings.json`
- `.github/workflows/lint.yml` — JSON validation 스텝이 `settings.json` 직접 read
- `scripts/session-start-pull.test.js:26` — `settings.json` 을 읽어 SessionStart 훅 command 를 그대로 실행하는 회귀 테스트 (CI 등록됨)
- `scripts/guard-worktree-edit.js:110` — main 편집 허용목록(`plans`/`projects`/`settings.local.json`)
- `scripts/dlc-doc-drift.js:45` — `settings.json → readme-trigger`
- `README.md` — tracked 전제 서술 다수(7·44·67·79·129·160·434·574행 등)
- `wiki/pages/decision/lesson-tracked-config-machine-paths.md` — 재발 3회차 적립 대상

# Acceptance

1. `git ls-files settings.json` 이 빈 출력 — 검증: 명령 실행
2. `settings.json` 이 작업트리에 그대로 존재하고 `git status` 가 clean — 검증: 명령 실행
3. CI 스텝이 `settings.json` 부재에서 통과 — 검증: `lint.yml` 이 참조하는 명령을 로컬에서 파일 없는 조건으로 실행
4. `node scripts/session-start-pull.test.js` 통과 — 검증: 실행
5. `node scripts/guard-worktree-edit.test.js` 통과 + main `settings.json` 편집이 allow — 검증: 실행
6. `node scripts/dlc-doc-drift.test.js` 통과 — 검증: 실행
7. README 에 "settings.json 은 tracked" 취지의 서술이 남아있지 않음 — 검증: `grep -n tracked README.md` 로 잔존 확인
8. wiki lesson 페이지에 재발 3회차 + `MEMORY.md` 인덱스 부재가 재발 원인이라는 사실 기록, `wiki/index.md` 동기화 — 검증: 파일 확인

# Blockers

(없음)

# Acceptance 증거 (2026-09-07)

1. ✅ `git ls-files settings.json` 빈 출력
2. ✅ 파일 디스크 존재 + `git check-ignore` 가 `.gitignore:37:/settings.json` 로 매칭
3. ✅ 파일을 잠시 옮겨 CI 조건 재현 → 영향 테스트 전부 통과
4. ✅ `session-start-pull.test.js` 19 tests — settings 있을 때(WIRED, CANONICAL 일치 단언 포함)·없을 때 양쪽
5. ✅ `guard-worktree-edit.test.js` ALL PASS (main `settings.json` → allow 로 기대값 전환)
6. ✅ `dlc-doc-drift.test.js` 76 assertions (settings.json → null)
7. ✅ README 잔존 검사 — tracked 전제 서술 0건, "clone 한 그대로/별도 복사 단계 없음" 0건
8. ✅ lesson 페이지 "재발 2회" 절 + `wiki/index.md`·`wiki/log.md` 동기화
9. ✅ 로컬 CI 동등 스위트 OVERALL PASS (shellcheck 포함)

# Review Disposition

- 메인 직접 점검(subagent 미사용 — Decisions 참조)에서 추가 발견 2건, 둘 다 `fix`:
  - `README.md` 의 문서화 표면 열거에 `settings.json` 잔존 → 제거(doc-drift 코드와 불일치였음)
  - `install-hooks.{sh,ps1}` 의 사용자 출력 "Guards check settings.json" 이 실제로 못 하는 일을 알림 → `plans/*.md` 중심으로 정정
- simplify 체크: `.gitignore` 주석 6줄은 lesson 페이지가 명시 요구하는 "부재의 이유"라 유지. `guard-worktree-edit.js` 의 조건 2줄 분리는 seg 기준/rel 기준을 가르는 것이라 유지.

# Workflow Findings

- 동일 실패(tracked `settings.json` 에 머신별 값 자동 주입 → pull 차단) 3회 재발. wiki lesson 은 2026-08-12 부터 존재했으나 `MEMORY.md` 인덱스 줄이 없어 자동 상기 경로가 없었다 — CLAUDE.md §13 이 요구하는 wiki+인덱스 짝이 미성립. 세션마다 능동 grep 에 의존해 매번 처음부터 재판단했고, 사용자가 같은 지적을 반복하게 됐다.
