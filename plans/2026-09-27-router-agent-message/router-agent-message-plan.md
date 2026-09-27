---
title: router-agent-message — 라우터가 subagent hand-back 턴을 사용자 턴으로 보지 않게
status: done
started: 2026-09-27
updated: 2026-09-27
intent: plans/2026-09-27-improve-followups/intent.md
---

# Goal
`scripts/dlc-task-router.js` 가 subagent 보고(hand-back) 턴에 라우팅 힌트를 주입하고 evidence 장부를 리셋하지 않게 한다.

# Intent
- 묶음: `plans/2026-09-27-improve-followups/intent.md` 의 router-agent-message 단위.
- 델타: 없음 — 묶음 줄의 문제·제약(실물 fixture, 출처 판별 후보) 그대로다. 실물 hook stdin 은 이 세션에서 캡처할 수 없어(debug 로그 없음, hook 설정은 세션 시작 때 고정) transcript 원문 형태로 fixture 를 뜨고, 머지 뒤 실제 hand-back 턴으로 재확인한다.

# Acceptance
1. Red→Green: hand-back 턴 fixture(transcript 실측 형태 — `Another Claude session sent a message:` + 개행 + `<agent-message from="…">`·`[Subagent hand-back]`·본문(재현·failing 포함)·`</agent-message>` + 뒤따르는 하니스 안내 문단)가 수정 전 `[dlc:investigation]` 을 내고, 수정 후 빈 출력. 확인: `node scripts/dlc-task-router.test.js` 를 수정 전·후 실행.
2. hand-back 턴이 장부를 리셋하지 않는다(`changed`·`readmeDirty` 유지). 접두어 없이 `<agent-message` 로 시작하는 형태도 같다. 확인: 같은 테스트.
3. 기존 동작 유지 — 사용자 프롬프트·reminder 가 붙은 사용자 프롬프트는 그대로 라우팅·리셋. 확인: 기존 테스트 전부 통과.
4. README `dlc-task-router.js` 설명(`README.md:422`)이 hand-back 턴 건너뛰기를 서술. 확인: 파일 read.
5. `bash scripts/verify.sh` 마지막 줄 `ALL PASS`.
6. - [x] [post-merge] 실제 hook stdin 경로 확인. 전제: 세션이 auto mode, 로컬 main working tree 에 수정이 반영됨(ff-merge — hook 은 `~/.claude/scripts/` 를 매 턴 읽는다). 절차: (a) 코드 파일을 한 번 편집해 장부 `$TMPDIR/dlc-evidence-<session>.json` 을 `changed: true` 로 만든다 (b) 본문에 "재현·failing" 이 든 보고를 내는 subagent 를 띄운다 (c) positive control — 그 턴이 transcript 에서 `Another Claude session sent a message:\n<agent-message` 형태이고 소문자 본문이 DBG 에 맞는지(수정 전이면 발동했을 턴) 확인 (d) 그 턴에 `[dlc:investigation]` 주입이 없고, telemetry 에 `router-investigation` 이 새로 없고, 장부가 여전히 `changed: true`. 실패하면 다음은 hook stdin 캡처(일회성 capture hook)로 간다.
7. wiki 가 코드와 맞는다 — `workflow-failures` 라우터 행 상태(hand-back 경로 fixed), hook-notification 페이지의 수정 서술, `wiki/index.md`·`wiki/log.md` 동기화, `check_links.py wiki` clean. 확인: 파일 read + 명령.

# Progress
- 2026-09-27: worktree 생성(base `origin/main@bd09d9b`). transcript 전체의 hand-back 턴 213건 형태 확인 — 전부 접두어 + 개행 + 태그 + 닫는 태그 뒤 하니스 안내 문단. debug 로그 없음. Red: hand-back 테스트가 `[dlc:investigation]` 주입으로 실패(의도한 이유). 구현 뒤 Green 17건. 실물 대조: 판별식이 transcript hand-back 턴 213/213 을 잡고 다른 user 텍스트 턴 1,888건은 0건(hand-back 턴은 전부 `isMeta: true`). README 422행 갱신, `verify.sh` ALL PASS. code-reviewer APPROVE(Codex 크레딧 소진으로 생략) — minor 4·nit 4 처분(Review Disposition), wiki 상태 동기화. simplify: 판별식 1줄·조건 1곳이라 줄일 것 없음. 격리 runner 최종 검증이 메인 판정과 일치(A1~A5·A7, 변경 파일 집합) — DONE. 로컬 ff-merge 로 main 반영.

- 2026-09-27 (머지 뒤): Acceptance 6 통과 — 장부를 `changed: true` 로 만든 뒤 본문에 "재현·failing" 이 든 보고를 내는 subagent 를 띄웠다. 그 턴은 transcript 에서 `Another Claude session sent a message:\n<agent-message` 형태(auto mode·2.1.281·`isMeta`)이고 수정 전 식이면 라우팅됐을 턴(positive control)인데, hook 주입 기록 없음·telemetry `router-investigation` 50 → 50·장부 `changed: true` 유지. 건너뛴 경로는 기록을 남기지 않아 "hook 이 돌고 건너뜀"과 "hook 이 안 돎"을 직접 구분하지는 못한다 ⚠️ — 이전 hand-back 턴마다 hook 이 돌았던 기록(130건)으로 새 코드의 결과로 본다. 실측용 장부 상태는 되돌렸다.

# Next


# Decisions
- 텍스트를 걷어내는 대신 **턴 출처로 판별**한다: 기존 reminder·notification 제거 뒤 앞머리가 (선택적) `another claude session sent a message:` + `<agent-message` 면 턴 전체를 건너뛴다(라우팅·리셋 둘 다). 기각안: `<agent-message>` 블록만 제거 — 태그 뒤 하니스 안내 문단이 남아 리셋이 계속된다(transcript 213/213). 기각안: 안내 문단까지 문구로 제거 — 하니스 문구가 바뀌면 조용히 깨진다(3주 사이 턴 형식이 두 번 바뀜).
- 앞머리 판별로 둔다(문장 중간의 `<agent-message` 는 판별하지 않음): 사용자가 hand-back 을 붙여넣은 프롬프트는 사용자 턴이다. 한 턴에 hand-back 과 사용자 입력이 합쳐져 오면 라우팅 힌트가 빠지고 리셋이 생략되는데, 리셋 생략은 early-stop 이 더 경고하는 쪽이라(장부 유지) fail-safe 로 본다.
- ⚠️ 판별이 평문 접두어 `another claude session sent a message:` 문구에 기대는 것은 기각한 "안내 문단 문구 매칭"과 같은 등급의 약점이다 — 텍스트 제거 없이 앞머리를 보는 방식 중에서는 이것이 최소 의존이라 택했다(접두어 없이 `<agent-message` 로 시작해도 잡는다). 문구가 바뀌면 옛 오발동으로 조용히 돌아가지만 이전보다 나빠지지 않고 telemetry `router-investigation` 급증으로 드러난다.
- 알려진 트레이드오프: 사용자가 hand-back 을 프롬프트 **맨 앞**에 붙여넣고 뒤에 질문을 쓰면 그 턴도 건너뛴다(라우팅 힌트 없음, 리셋 생략 → 앞 작업의 `planTouched` 가 새 작업으로 이어짐). 드물고 경고가 늘어나는 방향이라 감수한다. 이 동작을 테스트로 고정하지는 않는다(개선할 때 테스트를 뒤집지 않도록).
- `<agent-message>` 로 시작하는 턴은 subagent 보고뿐 아니라 다른 세션·teammate 메시지도 같이 건너뛴다 — 모두 사용자 발화가 아니라 라우팅을 건너뛰는 게 맞고, 리셋 생략도 편집마다 ledger 가 경고 조건을 다시 켜므로(`dlc-evidence-ledger.js:171-188`) 대체로 무해하다(code-reviewer 반증).
- 커밋 단위: 1개 — 스크립트·테스트·README·wiki·plan 이 한 동작 변경이다.
- 범위에 wiki 상태 갱신을 넣는다 (이유: 머지하면 `workflow-failures` 라우터 행 "proposed"·hook-notification 페이지 "수정 대기" 서술이 코드와 어긋난다).
- 규모 small — 스크립트 1곳, 테스트, README 한 줄.

# Review Disposition
- [code] minor Acceptance 6 이 결함이 있어도 통과할 수 있음(auto mode 아님·main 미반영·키워드 없는 본문이면 원래 신호 없음) — fix(전제·positive control·장부 `changed` 유지 확인·실패 시 stdin 캡처로).
- [code] minor 맨 앞에 붙여넣은 hand-back 뒤 사용자 질문도 건너뜀 — fix(Decisions 에 트레이드오프 명시, 테스트로 고정하지 않음).
- [code] minor 머지 시 wiki 상태가 코드와 어긋남 — fix(workflow-failures·hook-notification·index·log 같은 브랜치에서 갱신, Acceptance 7).
- [code] minor plan Next·Progress 동기화 — fix(리뷰 시점에 이미 갱신 중이었다).
- [code] nit 접두어 문구 의존 — fix(Decisions ⚠️ 로 같은 등급 명시). nit README 서술이 코드보다 좁음 — fix. nit 하니스/하네스 표기 — fix(하네스). nit `\b` 가 `<agent-message-x` 에도 맞음 — wontfix(관측된 적 없고 결과도 건너뛰기라 무해).

# Key Files
- `scripts/dlc-task-router.js` — hand-back 턴 판별
- `scripts/dlc-task-router.test.js` — hand-back fixture 테스트
- `README.md` — 라우터 설명(422행)
- `plans/2026-09-27-improve-followups/intent.md` — 묶음 `# Plans` 줄 치환
- `wiki/pages/decision/workflow-failures.md` · `wiki/pages/entity/claude-code-hook-notification-turns.md` · `wiki/index.md` · `wiki/log.md` — 상태 갱신

# Blockers
없음
