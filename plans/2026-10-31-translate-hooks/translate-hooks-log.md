# 문구 대조
hook 이 모델에게 보내는 문구의 원문(한국어)과 번역(영어). 리뷰어는 문구마다 조건·행동 지시·통과 방법이 그대로인지 본다. 줄 번호는 바뀐 뒤 기준. `${…}` 는 템플릿 변수로 그대로 두었다.

채널: SS = SessionStart stdout(`session-brief.js` — O 줄은 `session-fetch.js` 가 같은 함수로 다시 낸다) · UPS = UserPromptSubmit additionalContext · Stop = Stop block reason · deny = PreToolUse `deny` reason.

`plural(n, unit)` (`session-brief.js:38`) — 영어 단·복수(`1 commit`·`2 commits`). 한국어 원문에는 없던 함수라 새로 들였다. 숫자·조건은 바뀌지 않는다.

## session-brief.js (SS)
| 줄 | 신호 | 원문 | 번역 |
|---|---|---|---|
| 116 | K | `머지 대기(미머지 로컬): ${shown}${more}` | `Merge pending (unmerged local branches): ${shown}${more}` |
| 157 | L | `/improve 권장 — failure 신호 ${n}세션 누적 (마커 이후)` | `/improve recommended — failure signals accumulated in ${plural(n, 'session')} (since the marker)` |
| 284 | M | `닫히지 않은 plan: ${shown}${more}` | `Unclosed plans: ${shown}${more}` |
| 317 | N(`check`) | `확인: gh run list -w Lint -b main -L 3` | `check: gh run list -w Lint -b main -L 3` |
| 318 | N(`once`) | ``급하면 1회 `git -C ${where} pull --ff-only` `` | ``If urgent, pull once with `git -C ${where} pull --ff-only` `` |
| 321 | N 보류 | ``로컬 추적 ref refs/remotes/origin/ci 가 ci/verified 와 경로가 겹쳐 fetch 가 CI 검증 기록을 못 받는다(`git -C ${where} update-ref -d refs/remotes/origin/ci` 로 풀린다)`` | ``the local tracking ref refs/remotes/origin/ci overlaps the path of ci/verified, so fetch cannot receive the CI verification record (`git -C ${where} update-ref -d refs/remotes/origin/ci` clears it)`` |
| 324 | N 보류 | `마지막 fetch 기준 CI 검증 기록(origin/ci/verified)이 없어 자동 pull 이 보류된다 — main push 의 CI 가 통과하면 생긴다(${check}). 원격에서 지웠다면 의도된 정지다. fork·CI 없는 clone 은 CLAUDE_AUTOPULL_VERIFY=0 으로 검증을 끈다` | `as of the last fetch there is no CI verification record (origin/ci/verified), so auto pull is paused — it appears once CI passes for a main push (${check}). If it was deleted on the remote, this is an intended stop. A fork or a clone without CI turns verification off with CLAUDE_AUTOPULL_VERIFY=0` |
| 337 | N 보류 | `마지막 fetch 기준 CI 검증 기록의 내용이 커밋 이름 형식이 아니어서 자동 pull 이 보류된다(origin/ci/verified 를 확인)` | `as of the last fetch the CI verification record's content is not in commit-name format, so auto pull is paused (check origin/ci/verified)` |
| 340 | N 보류 | `마지막 fetch 기준 CI 검증 기록이 origin/main 밖을 가리켜(이력 재작성 직후) 자동 pull 이 보류된다 — 다음 main push 의 CI 가 새로 기록한다. ${once}` | `as of the last fetch the CI verification record points outside origin/main (right after a history rewrite), so auto pull is paused — CI on the next main push records a new one. ${once}` |
| 344 | N 보류 | `마지막 fetch 기준 CI 검증 기록이 HEAD 까지라 그 뒤 커밋은 보류 중이다 — CI 진행 중·실패·[skip ci] 중 하나(${check}), 이번 세션 pull 이 따라잡을 수도 있다. ${once}` | `as of the last fetch the CI verification record only reaches HEAD, so the commits after it are waiting — CI is running, failed, or was skipped with [skip ci] (${check}); this session's pull may catch up. ${once}` |
| 393-395 | N fetch 실패 | `자동 pull 의 fetch 가 ${days}일째 성공하지 못했다(마지막 성공 ${lastOk} \| 성공 기록 없음) — 뒤처짐 판정이 그 시점에 멈춰 있다. 재현: GIT_TERMINAL_PROMPT=0 git -C ${where} -c credential.helper= fetch origin main (오프라인이었다면 무시). 새 fetch 만 깨졌으면 CLAUDE_AUTOPULL_VERIFY=0` | `auto pull fetch has not succeeded for ${plural(days, 'day')} (last success ${lastOk} \| no success on record) — the behind count is frozen at that point. Reproduce: GIT_TERMINAL_PROMPT=0 git -C ${where} -c credential.helper= fetch origin main (ignore if you were offline). If only the new fetch is broken, CLAUDE_AUTOPULL_VERIFY=0` |
| 396 | N 머리 | `${label} ${behind}커밋 뒤처짐` | `${label} ${plural(behind, 'commit')} behind` |
| 402 | N 게이트 | `CLAUDE_AUTOPULL_OFF=1 로 자동 pull 을 꺼 둔 상태` | `auto pull is turned off with CLAUDE_AUTOPULL_OFF=1` |
| 403 | N 게이트 | `.autopull-off 파일로 자동 pull 을 꺼 둔 상태` | `auto pull is turned off by the .autopull-off file` |
| 406 | N 게이트 | `detached HEAD 라 자동 pull 이 돌지 않는다` | `auto pull does not run on a detached HEAD` |
| 408 | N 게이트 | `브랜치가 ${branch} 라 자동 pull 이 돌지 않는다(훅은 main 에서만)` | `auto pull does not run because the branch is ${branch} (the hook runs only on main)` |
| 413 | N 게이트 | `${busy} 진행 중이라 자동 pull 이 skip 된다(끝내면 풀린다)` | `auto pull is skipped while ${busy} is in progress (finishing it clears this)` |
| 421 | N 갈라짐 | `${head}·로컬 ${ahead}커밋 앞섬 — 갈라져서 ff-only pull 이 불가능하다(rebase 나 push 필요)` | `${head}, local is ${plural(ahead, 'commit')} ahead — diverged, so an ff-only pull is impossible (rebase or push needed)` |
| 444 | N 충돌 | `${head} — 로컬 변경과 충돌해 pull 거부됨: ${shown}${more} (커밋하거나 되돌리면 풀린다)` | `${head} — pull refused due to conflicts with local changes: ${shown}${more} (commit, restore or move them to clear this)` |
| 447 | N 폴백 | `${head} — 원인 미확인(마지막 pull 이 실패했거나 아직 안 돌았다)` | `${head} — cause unknown (the last pull failed or has not run yet)` |
| 547 | O 밀림 | `${ref} 대비 ${behind}커밋 뒤처짐` | `${plural(behind, 'commit')} behind ${ref}` |
| 550 | O 갈라짐 | `${fact}·로컬 ${ahead}커밋 앞섬 — 갈라져서 ff-only pull 이 불가능하다(rebase 나 push 필요)` | `${fact}, local is ${plural(ahead, 'commit')} ahead — diverged, so an ff-only pull is impossible (rebase or push needed)` |
| 551 | O 밀림 | `${fact} — 이 repo 에는 자동 pull 이 없다(직접 pull 해야 한다)` | `${fact} — this repo has no auto pull (it must be pulled manually)` |
| 596 | O 미커밋 | `미커밋 ${oldest}일: ${shown}${more}` | `uncommitted for ${plural(oldest, 'day')}: ${shown}${more}` |
| 613 | O fetch 신선도 | `${stale}일째 fetch 하지 않았다 — ${ref} 대비 밀렸는지 알 수 없다` | `not fetched for ${plural(stale, 'day')} — cannot tell whether it is behind ${ref}` |

## dlc-task-router.js (UPS)
| 줄 | 원문 | 번역 |
|---|---|---|
| 51 | `[dlc:investigation] 디버깅/장애로 보입니다. 고치기 전에 실패를 재현하고 증상→직접원인→근본원인을 증거로 확정하세요. 원인이 불확실하면 다른 원인 후보를 반증한 근거도 남기세요. 재현이 사라진 것을 확인한 뒤에만 '고쳤다'고 보고하세요. (skills/dlc/SKILL.md 조사 프로토콜)` | `[dlc:investigation] This looks like debugging or an incident. Before fixing, reproduce the failure and confirm symptom → direct cause → root cause with evidence. If the cause is uncertain, also record the evidence that rules out the other candidate causes. Report 'fixed' only after confirming the reproduction is gone. (skills/dlc/SKILL.md Investigation protocol)` |
| 57 | `[dlc:grounding] 실행되는 산출물(render/executable)로 보입니다. 정적 점검(파싱 OK)으로 끝내지 말고 실제 실행해 출력을 관찰한 증거를 acceptance 에 남기세요. 'well-formed ≠ correct'. 취향·시각 판단이 큰 산출물이면 구현 전 저비용 변형 2~4종을 먼저 제시해 반응을 받는 것을 고려하세요(취향 발견이 구현 후로 밀리면 비쌈). (skills/dlc/SKILL.md verification grounding + 요구사항 명확화 '프로토타입-우선')` | `[dlc:grounding] This looks like a running artifact (render/executable). Do not stop at static inspection (parse OK); actually run it, observe the output, and put that evidence in acceptance. 'well-formed ≠ correct'. If the artifact depends heavily on taste or visual judgment, consider showing 2-4 low-cost variants before implementing and getting a reaction (finding out the taste only after implementation is expensive). (skills/dlc/SKILL.md verification grounding + Requirement clarification 'prototype-first')` |

절 이름은 translate-skill-dlc 의 영어 SKILL.md 와 맞췄다 — `## Investigation protocol (debugging·incidents)`(102줄), `## Requirement clarification`(41줄)·`prototype-first`(50줄), `verification grounding`(74줄).

## dlc-early-stop.js (Stop)
| 줄 | 원문 | 번역 |
|---|---|---|
| 62-64 | `파일을 변경했는데 검증(test/lint/typecheck/build 또는 실행·관찰) 기록이 없습니다. 변경이 의도대로 동작하는지 검증을 실행하고 결과를 확인하세요. trivial(오타·로그 1줄)이라 검증이 불필요하면 그대로 다시 종료하면 통과합니다.` | `Files were changed, but there is no record of verification (test/lint/typecheck/build, or running and observing). Run verification for the change and confirm the result shows it works as intended. If the change is trivial (a typo, one log line) and needs no verification, stopping again as is passes.` |
| 174-177 | ``소스를 변경했는데 이 브랜치의 plan(${basename})을 한 번도 갱신하지 않았습니다. CLAUDE.md §10 은 결정·방향·스코프 변경을 그때그때 반영하라고 요구합니다 — 끝낸 Task 체크·다음 할 일(`# Tasks`, 옛 형식 plan 이면 `# Progress`/`# Next`)만이라도 실제 상태로 맞추세요. 갱신할 것이 정말 없으면 그대로 다시 종료하면 통과합니다.`` | ``Source files were changed, but this branch's plan (${basename}) was never updated. CLAUDE.md §10 requires reflecting decision, direction and scope changes as they happen — at least check off the finished Tasks and bring the next action (`# Tasks`, or `# Progress`/`# Next` in an old-format plan) in line with the actual state. If there is really nothing to update, stopping again as is passes.`` |
| 190 | `(dlc evidence gate 보조)` | `(dlc evidence gate backstop)` |

## dlc-doc-drift.js (Stop — early-stop 이 같은 reason 에 넣는다)
| 줄 | 원문 | 번역 |
|---|---|---|
| 172-173 | `README.md 가 문서화 표면(scripts/·agents/·skills/**/SKILL.md·CLAUDE.md) 변경과 함께 갱신되지 않았습니다 — README 동기화를 검토하세요. (불필요하면 그대로 재종료 시 통과)` | `README.md was not updated together with changes to the documented surface (scripts/, agents/, skills/**/SKILL.md, CLAUDE.md) — review the README sync. (If not needed, stopping again as is passes)` |
| 175 | `wiki/index.md 가 wiki/pages 변경과 함께 갱신되지 않았습니다 — index 동기화를 검토하세요. (불필요하면 재종료 시 통과)` | `wiki/index.md was not updated together with wiki/pages changes — review the index sync. (If not needed, stopping again passes)` |

## guard-worktree-edit.js (deny)
| 줄 | 원문 | 번역 |
|---|---|---|
| 145-146 | `worktree 세션(${wtRoot})인데 worktree 밖 main checkout 의 추적 파일(${fp})을 수정하려 합니다. 같은 파일의 worktree 경로(${wtFp})를 Edit/Write 하세요.` | `This is a worktree session (${wtRoot}), but you are about to modify a tracked file in the main checkout outside the worktree (${fp}). Edit/Write the same file at its worktree path (${wtFp}).` |
| 147-148 | `worktree 세션(${wtRoot})인데 worktree 밖 main checkout 에 새 파일(${fp})을 만들려 합니다. 브랜치에 담기도록 worktree 경로(${wtFp})에 만드세요.` | `This is a worktree session (${wtRoot}), but you are about to create a new file (${fp}) in the main checkout outside the worktree. Create it at the worktree path (${wtFp}) so it lands on the branch.` |

## 한국어로 둔 것 (사용자에게만 보인다)
- `guard-worktree-edit.js:111-113` `ask` reason · `guard-push-delete.js:116-117` `ask` reason · `notify-hook.js:59`/`notify-hook.ps1:20` `입력 대기`·`응답 완료`.
- `dlc-task-router.js:20-21` 의 한국어 키워드 정규식 — 사용자 입력을 맞추는 쪽이라 번역 대상이 아니다.

# Review Disposition
- Red — 테스트 5개 파일의 영어 문구 assertion 을 먼저 바꿔 50개 실패 확인(session-brief 39·session-fetch 3·dlc-early-stop 4·dlc-task-router 2·guard-worktree-edit 2, 각자 새 영어 문구가 없어서). 한 테스트의 둘째 assertion(ⓝ17 "If urgent"·ⓝ21 충돌 줄·plan 이유 둘째)은 첫째에서 멈춰 따로 관찰하지 못했고 Green 에서 통과.
- code-reviewer — APPROVE(조건·행동 지시·통과 방법 유지, 게이트 완화 없음)
  - Minor `ask` reason 이 "사용자에게만" 이라는 전제가 틀렸다 — headless `claude -p` 에서는 아무도 답할 수 없어 거부되고 모델이 그 이유를 읽는다(hooks 문서) — fix(plan·terms): 한국어로 두는 결정은 유지(대화형 세션의 사용자가 주 독자, 모델은 한국어도 읽는다), 근거 문장을 "대화형 세션에서는 사용자 확인 창, `-p` 실행에서는 모델이 거부 이유로 읽는다" 로 고쳤다.
  - Minor `dlc-early-stop.js` plan 갱신 안내 "bring the checked-off Tasks" 가 "끝낸 Task 체크" 를 약하게 옮겼다 — fix: "check off the finished Tasks and bring the next action … in line with the actual state".
  - Minor [plan 대비] intent Open question 이 아직 (open) — fix: `plans/2026-10-21-ops-docs-rework/intent.md` 를 (resolved) 로. 바뀐 쪽: plan.
  - Minor [plan 대비] Acceptance 3 의 대조표 위치(plan log)와 실제(strings.md)가 다르다 — fix: 대조표를 이 log 의 `# 문구 대조` 로 옮겼다. 바뀐 쪽: plan(기록 위치).
  - Minor router 가 가리키는 dlc 절 이름이 이 worktree base 에는 없다 — fix: main(dlc 영어) 위로 rebase.
  - Minor `session-brief.js` 머리 주석의 신호 이름이 옛 한국어 출력 — fix: 영어 출력 이름으로.
  - Nit "(pull it manually)" 명령형 — fix: "(it must be pulled manually)". Nit "commit or revert them" — fix: "commit, restore or move them". Nit VERIFY_MISSING "check" 반복 — fix.
  - Nit 테스트의 겹치는 assertion(ⓓ `/5 sessions/`, ⓞ1 `/2 commits behind/`) — false-positive: 앞 줄 전체 대조가 이미 덮어 해가 없고, 리뷰어도 고칠 필요를 적지 않았다.
- simplify 점검(메인) — `plural` 은 8곳에서 쓰여 둘 만하다. diverged 문구가 N·O 두 곳에 같은 글로 있는 것은 원래부터의 중복이라 이번 범위 밖(동작·문구 불변 리팩터는 별도).

# Deferred
- `session-brief.js` 의 diverged 문구 중복(N 420·O 549) — 한 상수로 모으는 리팩터, 심각도 낮음
- 공용 wiki `pages/decision/lesson-fix-scoped-to-one-repo.md` 26행이 옛 한국어 N 줄 출력을 인용한다 — 과거 기록이라 그대로(필요하면 main 세션에서 주석)
