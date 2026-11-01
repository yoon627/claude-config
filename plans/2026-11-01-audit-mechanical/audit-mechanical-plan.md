---
title: audit-mechanical — 2026-11-01 점검의 기계적 수정(규칙 변경 없음)
status: done
started: 2026-11-01
updated: 2026-11-01
---

# Goal
2026-11-01 repo 점검(보고 페이지 §10-1)에서 나온, 규칙을 바꾸지 않는 수정을 한 plan에 목적 단위 커밋으로 묶어 반영한다 — 테스트 안전장치, verify.sh 축 선택, gitignore, 공개 점검 경로, 용어표, Codex TOML 머리말, 버전 바닥 문서화(사용자 2026-11-01 "기계적 수정 번들·안전망 보강·규칙 불일치 12건" 선택).
- Why: 전체 검증은 통과하지만 (1) bash 테스트 3개가 `mktemp -d` 실패 시 `/` 아래에 fixture 를 만들고 `record-verified.test.sh` 는 `/bin/gh` 를 덮어쓸 수 있다(감사 중 실제 발생) (2) CI 에서 도구가 없으면 축이 조용히 빠진다 (3) `verify.sh changed` 매핑 빈틈으로 `dlc-signal.js`·`plan-match.js` 변경이 `session-brief.test.js` 를 돌리지 않는다 (4) 2.1.314 부터 Claude Code 가 추적 폴더 `skills/` 안에 `.trash/` 를 만든다.
- Constraints: 규칙·게이트 문구를 바꾸지 않는다(그건 rules-align). `scripts/guard-push-delete.js`·`scripts/pre-commit-check.*`·`scripts/ci-secret-scan.*`·`scripts/bootstrap/setup.*` 는 audit-safety-net 소유 — 여기서 건드리지 않는다(단 `pre-commit-check.sh`·`.ps1` 의 "회사 repo" 한 글자 수정과 테스트 3개의 `mktemp` 줄은 여기 — 서로 다른 hunk 라 rebase 로 합쳐진다). `agents/plan-reviewer.md` 는 rules-align 소유. 공용 wiki 라벨 20곳과 `docs/codex-review.md` grep 은 main 세션에서 따로. jira skill 은 건드리지 않는다. 사용자 지시: 묻지 말고 끝까지, push 는 끝에 한 번.
- Out of scope: 테스트 위생(임시 파일 정리·env 스크럽·전역 gitconfig·시계 창 — 11개 파일) — 별도 단위. `notify-hook.js` 테스트(dry-run 스위치가 먼저 필요). hook canonical.
- Split: none — purpose-commit bundle: 2026-11-01 점검 보고 §10-1 · 단위 1)~8) · 모두 독립이지만 plan 고정비를 아끼려 한 plan, 커밋 단위로 따로 되돌릴 수 있다(단위가 같은 파일에서 섞이지 않음 — verify.sh 는 한 단위, README 는 두 단위가 다른 줄).

# Tasks
- [x] 1) 테스트 `mktemp` 확인 — `scripts/ci-secret-scan.test.sh`:7 · `scripts/pre-commit-check.test.sh`:24 · `scripts/record-verified.test.sh`:10 을 `T="$(mktemp -d)" || exit 1` 로(`skills/improve/improve.test.sh`:6 과 같은 형태). Red: `TMPDIR=/nonexistent bash <test>` 가 지금은 `/` 에 파일을 만들며 통과 → 수정 뒤 즉시 exit 1 (2026-11-01)
- [x] 2) `scripts/verify.sh` — (a) `${CI:-}` 가 비어 있지 않으면 축 단위 도구 부재(pwsh·python3·shellcheck·zsh)를 `[skip]` 이 아니라 FAIL 로 (b) python 테스트 출력의 `OK (skipped=N)` 을 `SKIP <file> — N unittest cases skipped` 줄로 올려 요약에 포함 (c) SLOW_TESTS 의 `session-brief.test.js` 줄에 `scripts/dlc-signal.js scripts/plan-match.js` 추가 (d) `*.zsh` → shell 축, shell 축에 `zsh -n`(zsh 부재는 shellcheck 와 같은 skip 처리) — `scripts/verify-changed.test.sh` 에 zsh 선택·매핑 케이스와 CI 도구 부재 FAIL 케이스(shellcheck 없는 PATH), 그 파일의 bare `mktemp` 도 `|| exit 1`, `README.md` 472행대 verify 설명 동기화, `.github/workflows/lint.yml` shell 단계에 zsh 설치(ubuntu-latest 에 zsh 가 없다 — 없으면 (a) 때문에 CI 가 빨개진다) (2026-11-01)
- [x] 3) `.gitignore` 에 `/skills/.trash/` (2026-11-01)
- [x] 4) `README.md` — 520행 `claudeMdExcludes` 예시의 사용자명 경로를 `/Users/<user>/…` 로; 15행대에 Node ≥ 18·Python ≥ 3.11 바닥 명시(근거: 테스트의 `fs.cpSync(verbatimSymlinks)`, `jira_kit/config.py` 의 `tomllib`) (2026-11-01)
- [x] 5) `scripts/pre-commit-check.sh`:454 · `scripts/pre-commit-check.ps1`:558 출력 예시 `"회사 repo"` → `"company repo"`(CLAUDE.md §11 표현) (2026-11-01)
- [x] 6) `plans/2026-10-21-ops-docs-rework/terms.md` 원문 유지 표에 누락 6개 — `[리뷰 미경유]`·`커밋 단위:`·`생략:`·`Codex 미가용`·`코드`/`둘 다`·codex grep 의 `결론` (2026-11-01)
- [x] 7) `scripts/bootstrap/sync_codex_agents.py` `preamble()` 영어로(Codex 프롬프트는 영어 — §0), `scripts/bootstrap/test_sync_codex_agents.py` 가 머리말 글자를 본다면 함께 (2026-11-01)
- [x] 8) `skills/e/collect-state.sh`:80 `grep -qx` → `grep -qxF`(브랜치 이름이 정규식으로 읽혀 `feat.x` 가 `featax` 에 맞음) + 새 `skills/e/collect-state.test.sh`(재현: 로컬 default 에 `featax` 만 머지된 repo 에서 `feat.x` 의 `mergedToLocalBase` 가 false). `scripts/guard-worktree-edit.js` 는 `JSON.parse` 뒤 비객체(`null`) 입력을 exit 0 으로(지금은 TypeError·exit 1) + `scripts/guard-worktree-edit.test.js` 케이스(exit 0 이고 출력 없음) (2026-11-01)
- [x] code-reviewer → simplify 점검 → `bash scripts/verify.sh changed` + 바뀐 테스트 직접 실행 (2026-11-01) — REQUEST CHANGES 1회(가드 catch-all·lint.yml apt update·bare mktemp 4번째·CRLF·README 문구) → 재검토(Git Bash 래퍼) → APPROVE; verify ALL PASS(skip 은 도구 부재·플랫폼 케이스)
- [x] 기록 커밋, ff-merge(push 는 세 단위 끝에 한 번) (2026-11-01)
- [ ] [post-merge] Codex 를 쓰는 머신에서 `python3 scripts/bootstrap/sync_codex_agents.py` 재실행 — 설치된 `~/.codex/agents/*.toml` 의 머리말은 재생성 전까지 한국어다(`scripts/bootstrap/README.md` 는 agents 변경 때만 재실행을 말한다)

# Acceptance
1. mktemp — `TMPDIR=/nonexistent/x bash scripts/record-verified.test.sh` 가 exit 1 로 즉시 끝나고 `/` 에 새 항목이 없다 — 세 파일 모두 — 전/후 비교
2. verify.sh — `CI=1 bash scripts/verify.sh shell` 이 shellcheck 없는 이 머신에서 비0 종료; `CI=` 이면 기존처럼 `[skip]`; `bash scripts/verify-changed.test.sh` 통과(새 케이스 포함: `scripts/gwl.zsh` → shell 축, `scripts/dlc-signal.js` 변경 시 session-brief 테스트가 skip 목록에 없음); python 축 출력에 `SKIP skills/wiki/test_check_links.py — 1 unittest cases skipped` 형태 줄
3. `git check-ignore -q skills/.trash/x` 가 0
4. `rg -n "/Users/[a-z]" README.md` 0건; README 에 Node·Python 바닥 1줄씩
5. `rg -n "회사 repo" scripts` 0건, `pre-commit-check.test.sh` 통과(sh 엔진)
6. terms.md 6행 추가 — `node plans/2026-10-21-ops-docs-rework/check-translation.js "$PWD" plans/2026-10-27-translate-agent-arch-reviewer/check.json` 이 여전히 PASS(용어표 블록은 바꾸지 않으므로)
7. `python3 scripts/bootstrap/test_sync_codex_agents.py` OK, 생성 TOML 머리말에 한글 0
8. `bash skills/e/collect-state.test.sh` 통과(수정 전에는 `feat.x` 케이스가 FAIL); `node scripts/guard-worktree-edit.test.js` 통과(새 null 케이스 포함, 수정 전 FAIL)
9. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 은 도구 부재와, 2(b) 가 새로 드러내는 플랫폼·root 조건의 unittest 케이스 skip 만)

# Decisions
- wiki 결정 [[ops-doc-slimming]]·[[workflow-failures]](검증 축 누락 2026-09-07) → 따른다.
- 커밋 단위: 1) `test: fail fast when mktemp cannot create the fixture root` — 테스트 3개 2) `fix(verify): fail CI on a missing tool, surface unittest skips, map and lint zsh` — verify.sh·verify-changed.test.sh·lint.yml·README verify 절 3) `chore: ignore the native skills/.trash directory` — .gitignore 4) `docs(readme): generic example path and runtime floors` — README 5) `fix(pre-commit): say company repo in the hint` — sh·ps1 6) `docs(terms): record six kept strings` — terms.md 7) `fix(codex-sync): English preamble for generated agents` — sync_codex_agents.py(+test) 8) `fix(e,guard): literal branch match in collect-state and a crash-free guard` — collect-state.sh·test, guard-worktree-edit.js·test
- 테스트: 1)·8) 은 재현 테스트 먼저(Red 확인). 2) 는 verify-changed.test.sh 케이스 먼저. 3)~7) 은 문서·문자열(§7 예외 — Acceptance 명령으로 검증).
- CI 에서 도구 부재를 FAIL 로 하는 기준은 `CI` 환경 변수(GitHub Actions 가 항상 설정) — 로컬은 그대로 skip. 기각: 항상 FAIL(PowerShell 없는 로컬 머신이 모두 빨개진다).
- unittest skip 노출은 verify.sh 가 출력 요약 줄을 읽는 방식 — 13개 테스트 파일에 TestResult 를 덮어쓰는 것보다 한 곳 변경. 기각: 파일별 `addSkip` 오버라이드.
- ⚠️ (구현) CI 의 shell 단계가 매 실행 `apt-get install zsh` 를 한다 — 다른 선택지: CI 에서 zsh 부재를 FAIL 로 세지 않기(그러면 `.zsh` 는 어디서도 검사되지 않는다), `zsh -n` 을 CI 에서 생략 — 택한 이유: `.zsh` 2개가 지금까지 한 번도 문법 검사를 받지 않았고 설치는 몇 초다 — `.github/workflows/lint.yml` shell step
- 가드의 `null` 처리는 try/catch 가 아니라 타입 검사 — code-reviewer: catch-all 은 가드가 깨졌을 때도 조용히 allow 가 되어 테스트 하네스의 크래시 감지(비0 종료 = crash)를 끈다. 기각: end 핸들러 전체 try/catch.
- 롤백: 단위별 `git revert`.

# Blockers
