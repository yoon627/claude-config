---
title: branch-merge-backlog — 쌓인 미머지 브랜치를 충돌 최소 순서로 정리
status: done
started: 2026-08-20
updated: 2026-08-20
---

# Goal
로컬에 쌓인 미머지 브랜치를 `git merge-tree` 실측 충돌 순서대로 정리한다. 동시에 이 repo 의 구조적 충돌 원인(공유 문서 파일 동시 편집)을 줄일 방향을 정한다.

# Progress

- 2026-08-20: **worktree 전면 정리 완료 — 남은 worktree 0개, 브랜치 main 만**.
  - `codex-jira-worklog-skill`: 막혀 있던 blocker 2건이 환경 변화로 해소돼(uv 0.11.7 정상·python PATH 존재) 잔여 검증을 끝냈다. launcher dry-run **exit 0** 확인 후 plan status done, squash 머지(`4e130ae`).
  - 그 머지가 CI 를 2번 깨뜨려 각각 근본 수정: ①`install-codex-skill.sh` 실행권한 없음(exit 126) → git mode 100755(`976e9f7`) ②shellcheck 3건 → 억제 대신 코드 수정(`9fccf55`). `$BASH_SOURCE`→`${BASH_SOURCE[0]}`(SC2128)는 실제 결함이었다.
  - `plan-done-cleanup`: 구현 없는 draft 라 plan 만 main 에 squash 보존(`a171b0a`)하고 worktree·브랜치 삭제. 설계 미결이라 착수하지 않았다.
  - 고아 디렉토리 `.claude/worktrees/code-reviewer-absorb/`(파일 0개, git 미추적) 제거 — 과거 `worktree remove` 가 디렉토리 삭제만 실패한 잔해.
  - 최종 CI success(`a171b0a`).
- 2026-08-20: 실측 조사. 겉보기 미머지 6건 중 `jira-task` ⊂ `jira-task-description` ⊂ 로컬 main 임을 `merge-base --is-ancestor` 로 확인 → 실제 미머지는 4건.
- 2026-08-20: **1번 완료** — 로컬 main 4커밋(jira-task 계열)을 `pull --rebase --autostash` 로 origin/main(97c16d0) 위에 올리고 push(`97c16d0..e4badc0`). CI lint success. dirty 하던 `settings.json`(orca agent-hooks 주입분)과 untracked plan 은 autostash 로 보존됨.
- 2026-08-20: **2번 제외 판정** — `plan-done-cleanup` 은 머지 대상 아님(아래 Decisions).
- 2026-08-20: **머지된 브랜치 정리 완료** — `jira-task`(tip b862ce1)·`jira-task-description`(tip b17aa5a) worktree 2개 + 로컬 브랜치 2개 삭제. rebase 로 SHA 가 바뀌어 `-d` 가 거부 → patch-id 로 전부 upstream 임을 입증한 뒤 사용자 확인받고 `-D`. 원격 브랜치는 애초에 없었음. `settings.local.json` 은 main 것과 바이트 동일이라 유실 없음.
- 2026-08-20: 추가 발견 — `numbering-style`(0 커밋, worktree 없음) 도 완전 머지 상태여서 `-d` 로 삭제(tip 19a4b56). `codex-jira-worklog-skill` 은 0 커밋이지만 **삭제 보류**(아래 Decisions).
- 2026-08-20: **4번·5번 폐기 판정 확정** — 둘 다 "이미 다른 PR 로 해결된 작업의 옛 사본"이었다. 4번은 PR #65 로 머지 완료(+`ced08ec` 로 추가 개선)라 그대로 머지하면 `## 13.` 섹션이 **2개**가 되는 것을 merge-tree 시뮬레이션으로 실증했고, lesson 파일은 main 것과 내용 동일. 5번은 PR #118(2026-08-04 머지)이 같은 Goal 을 먼저 해결했고 이 브랜치의 PR #120 은 closed — main 60테스트 vs 브랜치 7테스트로 main 이 앞선다. 양쪽 worktree + 브랜치 삭제(tip f15ffce / 7826953).
- 2026-08-20: 머지 커밋 `08a5632` push, **CI lint success**.
- 2026-08-20: **3번 `worktree-cleanup-auto` 머지 완료**(머지 커밋 `08a5632`, 미push). 충돌 4파일 — 예측 2개에서 늘었는데, 오늘 push 한 jira-task 4커밋이 `README.md`·`skills/e/SKILL.md` 를 건드렸기 때문(예고한 "순차 머지 시 충돌 증가"가 실현). 머지 후 브랜치는 merged·원격 없음이라 새 §8 규칙대로 확인 없이 `-d` 삭제(tip 1ac372c).
- 2026-08-20: **codex-jira-worklog-skill 미커밋 작업 보존 완료** — "이미 main 에 있지 않나" 확인 요청에 따라 대조: `a0edca6..origin/main` 에 `skills/jira-worklog`·`scripts/bootstrap` 을 건드린 커밋 **0건**, untracked 8파일 main 에 **전부 부재** → main 에 없음이 확정. WIP 커밋 `7680f0c`(16파일 +468/-16)로 보존, worktree clean. ignored 유출 없음.

# Next

브랜치·worktree 정리는 **완료**. 남은 것은 이 plan 의 부수 목표 2건으로 `# Deferred` 로 넘긴다.

# Decisions
- **머지 순서는 실측 충돌 오름차순** (`git merge-tree --write-tree origin/main <br>`):
  1. ~~로컬 main 4커밋~~ — CLEAN, **완료**
  2. `plan-done-cleanup` — CLEAN이나 **제외**
  3. `worktree-cleanup-auto` — 2파일 충돌 (`CLAUDE.md`, `skills/wt/SKILL.md`)
  4. `worktree-mistake-log-convention` — 2파일 충돌 (`wiki/index.md`, `wiki/log.md`)
  5. `jira-worklog-cwd-attribution` — 7파일 충돌, **머지 전 폐기 판정 선행**
- **`plan-done-cleanup` 제외 (이유)**: 커밋 메시지가 "구현 시 이 WIP 는 squash/amend 대상"이라 명시한 미완성 체크포인트. plan 본문 `status: in_progress`, `# Next` 가 "이어받기". main 에 넣으면 예정된 squash/amend 가 불가능해진다. → 브랜치로 유지하고 `/c` 로 이어받을 대상.
- **`jira-worklog-cwd-attribution` 은 머지 전 판정 (이유)**: PR #120 이 **CLOSED(미머지)** 이고, 이후 PR #142(`worklog-per-session`, "worklog 등록 단위를 worktree 에서 세션으로")가 MERGED. `test_session_time.py` 가 **add/add 충돌** = 양쪽이 같은 파일을 독립 생성 → #142 가 이 작업을 다른 방식으로 대체했을 가능성이 높다. 충돌 7개를 푸는 대신 두 구현을 비교해 폐기/재작업을 먼저 결정한다.
- **충돌 수치는 독립 측정값**: 각 브랜치를 origin/main 에 단독으로 붙였을 때 기준. 3·4 는 `CLAUDE.md`·`README.md` 를 계속 건드리므로 순차 머지 시 뒤로 갈수록 충돌이 커진다 → 한 건 머지할 때마다 다음 브랜치를 rebase 해 재측정한다.
- **4번·5번은 "옛 사본" 패턴 — 머지 대신 폐기**: 둘 다 `git rev-list` 로는 미머지로 보이지만 실제 작업은 다른 PR(#65 / #118)로 이미 main 에 있었다. **브랜치가 살아 있다는 사실은 미머지의 근거가 아니다** — PR 이력(`gh pr list --head`)과 내용 대조(파일 존재·동일성·머지 시뮬레이션)로 판정해야 한다. 이 판정을 건너뛰고 머지했다면 4번은 CLAUDE.md 에 §13 중복을, 5번은 7파일 충돌을 푸는 헛수고를 낳았을 것이다.
- **`codex-jira-worklog-skill` 삭제 보류 (이유)**: 브랜치 자체는 origin/main 대비 0 커밋이라 "머지 완료"로 보이지만, worktree 에 **미커밋 작업이 다수** 존재 — 수정 8파일(`.github/workflows/lint.yml`, `README.md`, `scripts/bootstrap/setup.{ps1,sh}`, `skills/e/SKILL.md`, `skills/jira-worklog/{SKILL.md,jira_worklog.py}` 등) + untracked `plans/2026-08-12-codex-jira-worklog-skill/`(미커밋 plan), `scripts/bootstrap/install-codex-skill.*` 4개, `skills/jira-worklog/run_worklog.{ps1,sh}`, `test_launcher.sh`. §8 상 미커밋 plan 은 삭제 전 커밋·push 로 보존해야 하며, `git worktree remove` 는 ignored 파일을 무경고 삭제한다. → 진행 중 작업으로 간주하고 유지. **후속 확인(2026-08-20)**: 이 변경들이 이미 main 에 반영됐는지 대조한 결과 전부 미반영으로 확정 → WIP 커밋 `7680f0c` 로 보존. 내용은 Codex 에서 `jira-worklog` 를 직접 호출 가능하게 하는 launcher(`run_worklog.{sh,ps1}`, uv 우선·Python fallback)와 `$HOME/.agents/skills/` junction 을 멱등 설치하는 bootstrap. 구현·테스트·code-review 반영은 끝났고 남은 것은 uv managed Python 권한 해결 후 Windows launcher dry-run 재검증 + Codex skill catalog 노출 확인.
- **브랜치 완전 머지 판정은 `git cherry`(patch-id)로 한다**: rebase·squash 후에는 `git rev-list origin/main..<br>` 이 비지 않아 `-d` 가 거부한다. SHA ancestry 가 아니라 patch-id 로 판정해야 실제 유실 여부를 알 수 있다. 단 **worktree 의 미커밋 상태는 별도 확인** — 브랜치가 0 커밋이어도 worktree 가 dirty 일 수 있다(`codex-jira-worklog-skill` 사례).
- **구조적 충돌 원인**: `README.md`(5개 브랜치), `skills/e/SKILL.md`(4), `docs/worktree-lifecycle.md`(3) 가 핫스팟. `.gitattributes` 의 `merge=union` 은 **해법이 아니다** — GitHub 서버 사이드 머지가 사용자 `.gitattributes` 의 merge 지시를 무시한다(community #9288). 파편 디렉토리 분리가 근본책.

- **3번 충돌 해결 판단(기록)**: ①`CLAUDE.md`·`README.md`·`skills/e/SKILL.md` 는 브랜치 채택 — 옛 규칙을 새 규칙으로 **교체**하는 변경이라 양쪽 병합 시 모순. ②`skills/wt/SKILL.md` 는 **줄별 분리** — `wt rm` 문구는 브랜치, "생성 전 확인은 묻지 않는다"는 main 유지. 브랜치가 위험기반 승인(§1) 도입 **전** 상태여서 통째로 채택하면 무확인 생성이 되돌아간다(regression). 커밋 메시지에도 생성 확인 언급이 없어 의도가 아님을 확인. ③`/e` 단계 번호를 브랜치 기준 6·7 → main 기준 7·8 로 재조정(main 에 "5. Jira task" 가 추가돼 한 칸 밀림). `CLAUDE.md` step 참조·`README.md` collect-state.sh 설명도 동반 수정.
- **`git checkout --theirs` 를 쓰지 않는다**: 충돌 파일 **전체**를 브랜치 버전으로 덮어, auto-merge 된 다른 변경(오늘 push 한 jira-task 내용)이 유실된다. 충돌 블록만 편집해야 한다.

# Key Files
- `plans/2026-07-22-plan-done-cleanup/plan-done-cleanup-plan.md` — 2번 브랜치의 미완성 plan. `/c` 이어받기 대상.
- `skills/jira-worklog/test_session_time.py` — 5번의 add/add 충돌 지점. #142 구현과 비교 대상.
- `CLAUDE.md`, `README.md`, `skills/e/SKILL.md` — 순차 머지 시 반복 충돌하는 핫스팟.

# Blockers
(없음)

# Deferred

- **핫스팟 파일 구조 개선 미결**(Acceptance 4) → **이슈 #145 로 이관**(2026-08-20, https://github.com/yoon627/claude-config/issues/145). `README.md`·`skills/e/SKILL.md` 를 파편 디렉토리로 나눌지 결정하지 않았다. 현재 worktree 가 0개라 당장 충돌은 없지만, 병렬 작업을 재개하면 같은 문제가 돌아온다.
- **리뷰 루프 구성 미확정** → **이슈 #144 로 이관**(2026-08-20, https://github.com/yoon627/claude-config/issues/144). orca Annotate AI Diff 기본 + PR 은 CI 필요할 때만. 조사 결론·확인된 제약(self-approve 불가·merge queue 불가·merge=union 무효)·claude-code-action 함정을 이슈 본문에 정리했다. 머지 직후 브랜치 정리 규약도 같이 다룬다.
- **`test_session_time.py` 1건 실패 — Windows 로컬 전용, baseline** (심각도: 낮음). `classify_cwd("/repo/\0bad", ...)` 가 `UNMATCHED` 대신 `MAIN` 반환. `origin/main`(97c16d0)에서 동일 재현되고 내 4커밋은 `jira-worklog` 파일을 전혀 안 건드림 → 이번 변경과 무관. CI(ubuntu)는 같은 커밋에서 success 이므로 null byte 경로 처리의 플랫폼 차이로 추정. 범위 밖이라 미수정.
- ~~`codex-jira-worklog-skill` 미커밋 작업 미처리~~ → **해소**(WIP 커밋 `7680f0c`). 다만 그 브랜치의 잔여 작업(uv 권한·dry-run 재검증)은 별도 세션에서 `/c` 로 이어받아야 한다.

# Acceptance
1. 미머지 브랜치 4건이 각각 머지·폐기 중 하나로 처분되고 근거가 기록된다.
2. 각 머지 후 CI lint 가 success.
3. main 에 완전 포함된 브랜치(worktree 포함)가 정리된다.
4. 핫스팟 파일의 구조적 충돌 완화 방향이 결정된다(파편 디렉토리 분리 여부).
