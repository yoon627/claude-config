---
title: remove-conclusion-block — 답변 끝 `## 결론` 블록 규칙과 Stop hook 검사 4 를 없앤다
status: in_progress
started: 2026-10-20
updated: 2026-10-21
---

# Goal
답변 끝의 `## 결론` 블록 형식 규칙과 그 강제(Stop hook 검사 4)를 없앤다. 무엇을 보고할지(§3-6 Report 항목)와 마지막 선택지(AskUserQuestion)는 남긴다.
- Why: 사용자 결정(2026-10-20, 선행 plan 의 도입 이유를 듣고 2026-10-21 재확인). 규칙이 정해진 모양(구분선·라벨·불릿)과 hook 강제를 더하면서 답변이 길어졌다.
- Constraints: 규칙 손실 0([[ops-doc-slimming]]) — 지우는 조항마다 "버림(사용자 결정)" 인지 "이관" 인지 `# Decisions` 에 적는다. hook 의 다른 축(검증·문서 drift·plan drift·대기 턴)은 동작을 바꾸지 않는다. 이 브랜치의 규칙 파일은 한국어(영어 번역은 다음 작업).
- Out of scope: `agents/researcher.md` 의 `## 결론`(조사 보고서 자체 구조 — 2026-10-07 plan 도 같은 이유로 제외) · 공용 wiki 문구(머지 후 main 세션, plan log `# Deferred`) · CLAUDE.md 줄이기·영어 번역(다음 작업) · `skills/e/SKILL.md` 의 "§3-6 1회 원칙" 참조가 원래부터 가리키는 문구가 없는 문제(plan log `# Deferred`).
- Split: none — 규칙 문구만 지우면 hook 이 계속 결론을 요구하고, hook 만 지우면 규칙이 남아 둘이 어긋난다. 한 머지에서만 일관된다.

# Tasks
- [x] 사용처 조사 (2026-10-20) — `CLAUDE.md` §3-6, `scripts/dlc-early-stop.js`·`scripts/dlc-ledger.js`·`scripts/dlc-evidence-ledger.js`·`scripts/dlc-signal.js` 와 테스트, `skills/e/SKILL.md`·`skills/dlc/SKILL.md`·`skills/improve/SKILL.md`, `README.md`
- [x] 계획 리뷰 (2026-10-20) — workflow `wf_502a2dc9-1a2`: plan-reviewer CONDITIONAL, 처분은 plan log
- [x] 사용자 재확인 (2026-10-21) — 선행 plan 2개의 도입 이유를 듣고 "그래도 완전 제거"
- [x] 테스트 먼저 (2026-10-20) — `scripts/dlc-early-stop.test.js` 의 결론 축 테스트를 "결론 없이 끝나도 막지 않는다" 1개로 교체, 구현 전 실패 확인
- [x] 나머지 테스트 정리 (2026-10-21) — 대기 턴 테스트의 마지막 답변도 일반 문장으로. `scripts/dlc-early-stop.test.js`(`UNVERIFIED` 의 `edited`, 대기 테스트 메시지, stop_hook_active 테스트에 장부 불변 단언), `scripts/dlc-evidence-ledger.test.js`(③d `edited` 테스트 3개 삭제, Bash plan 테스트의 `edited` 단언만 삭제), `scripts/dlc-signal.test.js`(`early-stop-conclusion` 줄 삭제, 개수 12 → 11)
- [x] hook 코드 (2026-10-21) — early-stop 26·ledger 92·signal 22 통과. `scripts/dlc-early-stop.js`(검사 4·`concluded()`·`endsWithConclusion()`·stop_hook_active 분기의 소비·`CONCLUSION_MISSING`·머리 주석, 대기 판정 순서는 유지하고 주석만 남는 이유로), `scripts/dlc-ledger.js`(DEFAULT 의 두 필드·주석), `scripts/dlc-evidence-ledger.js`(두 필드 설정), `scripts/dlc-signal.js`(`KINDS`)
- [x] 규칙 문구 (2026-10-21) — Acceptance 3 검색 0건. `CLAUDE.md` §3-6, `skills/e/SKILL.md` 46행(recap 줄), `skills/dlc/SKILL.md` 167·168행, `skills/improve/SKILL.md` 26행, `README.md` 335·336·348·460·530행(460행은 대기 턴 근거를 살려 다시 쓴다)
- [x] code-reviewer, fix loop (2026-10-21) — APPROVE, 지적 7개 처분은 plan log
- [x] simplify 점검, `bash scripts/verify.sh changed`, Acceptance 대조 최종 격리 검증 (2026-10-21) — simplify 변경 없음(삭제뿐). 격리 runner: Acceptance 1~4 충족, `ALL PASS (skip: install-codex-skill.test.ps1)` — PowerShell 미설치, 이 변경과 무관. 느린 테스트 중 `dlc-signal.js` 를 읽는 `session-brief.test.js` 는 따로 돌려 95개 통과
- [x] 사용자에게 바뀐 문구 확인받고 커밋, commit-check (2026-10-21) — 사용자 "커밋", 커밋 1개
- [ ] 머지 (`/e merge`)
- [ ] [post-merge] main 세션에서 공용 wiki 의 결론 블록 언급 갱신(plan log `# Deferred`)
- [ ] [post-merge] 머지 뒤 첫 세션에서 파일을 고친 턴이 `## 결론` 없이 끝나도 Stop hook 이 막지 않는지 관찰(Acceptance 5)

# Acceptance
1. Stop hook 이 결론 블록을 더는 요구하지 않는다 — `node scripts/dlc-early-stop.test.js` 통과. 그 안의 "결론 축 없음" 테스트는 구현 전에 실패했다. 다른 축 테스트는 그대로 통과한다.
2. 결론 축의 코드·장부 필드·신호가 남지 않는다 — `rg -n 'conclusionBlocks|early-stop-conclusion|CONCLUSION|endsWithConclusion|concluded\(|\bedited\b' scripts/ --glob '!*.test.js'` 결과가 없다. 테스트 파일의 결과는 옛 장부 호환을 보는 "결론 축 없음" 테스트와, 이 작업과 무관한 `scripts/session-brief.test.js` 의 `'edited'` 문자열뿐이다.
3. 규칙 문구에 `## 결론` 형식 요구가 없다 — `rg -n '## 결론|결론 블록|CONCLUSION' CLAUDE.md skills/*/SKILL.md README.md` 결과가 없다. §3-6 에 Report 항목 목록·AskUserQuestion 선택지와 생략 조건·오탐 한 줄 규칙·오탐 사유 기록처가 남고, §1 확신도 표시와 §3-5 "미실행은 '미검증' 명시" 문장은 그대로다(diff 대조).
4. `bash scripts/verify.sh changed` 가 `ALL PASS` 로 끝난다(skip 이 있으면 무관함을 보인다).
5. [post-merge] 머지 뒤 첫 세션에서 파일을 고친 턴이 `## 결론` 없이 끝나도 Stop hook 이 막지 않는다(실제 세션 관찰 — 작업 중에는 main 의 옛 hook 이 돌아서 볼 수 없다).

# Decisions
- wiki 결정: [[ops-doc-slimming]](규칙 손실 0·로드 등급 보존) → 따른다. 아래 "지우는 조항" 대조로 지킨다. [[workflow-failures]] 의 early-stop 결론 오탐 기록은 이 축이 없어지면서 끝난다.
- 선행 plan: `plans/2026-09-15-conclusion-block`(도입 — "작업 뒤 '뭐가 문제였고 어떻게 해결했는지'를 매번 다시 묻는다", 사용자 "결론만 확실하게 보고… 더 알고 싶으면 윗내용을")과 `plans/2026-10-07-conclusion-format`(형식 변경 — "결론을 읽고도 본문을 다시 읽어야"). 메인은 처음에 이 plan 들을 보지 않고 "기본 동작이 끝에 요약한다"를 근거로 제거를 추천했다 ⚠️. 리뷰가 찾아낸 뒤 사용자에게 다시 물었고(제거 취소를 추천), 사용자가 재발 위험을 알고 완전 제거를 택했다(2026-10-21). 감수: 그 문제를 막는 것은 이제 §3-6 Report 항목 목록과 기본 요약뿐이다.
- 기각(사용자가 완전 제거를 택함): 제거 취소하고 줄이기 작업에서 문구만 짧게(메인 추천) · hook 만 지우고 짧은 규칙 유지 · heading 을 언어별로 허용 · 본문 반복 금지 문구 추가 · hook 기본값 OFF.
- 지우는 조항과 처리:
  - 블록 형식(빈 줄·`━` 구분선·`## 결론`·라벨 순서·사실당 불릿·음슴체) — 버림.
  - "결론만으로 판단 가능 / 본문 참조 금지 / 영향 큰 것부터 / 과정 서술은 답이 아님" — 버림(블록과 함께).
  - 근거의 `미확인:` 불릿("§1 ❌ 를 대신한다") — 이관: §1 확신도 표시(중요한 판단·원인 분석) + §3-5 "미실행은 '미검증' 명시" + §3-6 Report 항목 "남은 리스크"가 나눠 맡는다.
  - `**다음**`(사용자가 결정·실행할 것) — 이관: §3-6 의 AskUserQuestion 선택지(유지).
  - "hook 은 마지막 텍스트 블록만 본다 → 마감 텍스트를 결론으로" · "결론 누락 경고가 맞으면 결론만 다시 출력" · 오탐 턴의 결론 면제 — 버림(검사가 없어짐). 오탐 한 줄 규칙 자체와 오탐 사유 기록처는 유지.
  - dlc 16 "읽을 곳" 의 위치("`## 결론` 바로 앞") — "보고 끝부분(선택지 앞)"으로. 출처 (2) 중 `resolved` 가 아닌 것과 출처 (3) 을 결론 `**다음**` 에 다시 올리던 것 — 이관: "읽을 곳" 블록 안에서 그 줄 앞에 `확인 필요:` 를 붙인다(사용자가 선택지를 고르기 전에 볼 항목을 구분하는 기능 유지).
  - `/e` 의 recap 줄 — 결론 블록 요구만 지우고, 작업 선택지 생략·Jira 승인 별도·머지 모드 done 확인 생략은 유지.
  - dlc 16 "recap 은 보고 형식일 뿐 새 단계를 더하지 않는다" — 버림(recap 이 없어져 대상이 사라짐).
  - §0 의 "끝나면 결론 요약"(일반 요약) — 그대로.
- `agents/researcher.md` 의 `## 결론`: 유지 — 조사 보고서의 내부 구조이고 hook·§3-6 과 무관. 기각: 함께 지우기(이번 결정의 대상이 아님).
- hook 의 판정 순서: 대기 턴 판정을 stop_hook_active 분기보다 먼저 두는 순서는 유지한다(재종료 턴에도 `early-stop-wait-shell` 신호를 남긴다). 주석은 "edited 소비 회피" 대신 이 이유로 고쳐 쓰고, stop_hook_active 테스트에 장부 불변 단언을 더한다.
- 옛 장부·옛 telemetry: tmp 장부에 남은 `edited`·`conclusionBlocks` 는 읽기만 하고 무시된다(테스트로 확인). telemetry 의 `early-stop-conclusion` 은 `summarize`·`session-brief` 가 `KINDS` 에 없는 종류를 건너뛰어 집계에서 빠진다 — 감수, 없어진 축이다. 이 서버 telemetry 기준 발동 0건(전체 52행·5세션, 2026-10-21 조회 — 다른 머신은 모름). 기각: `KINDS` 에 남기기(없는 축의 실패를 계속 센다).
- 환경변수 `CLAUDE_DLC_CONCLUSION_OFF`: 함께 없앤다(README 안내 포함). 설정에 남아 있어도 무해하다.
- 머지 시점에 떠 있는 세션: 시작할 때 읽은 CLAUDE.md 에는 옛 규칙이 남지만 hook 은 새 코드라 강제만 사라진다 — 무해. 반대 방향(규칙 없이 hook 만 요구)은 생기지 않는다.
- 롤백: PR 머지 커밋을 `git revert -m 1 <merge sha>` — 같은 PR 의 plan `status: done` 도 함께 되돌아간다.
- 커밋 단위: 1개 — 규칙과 hook 이 한 머지에서만 일관된다(Split 과 같은 이유).

# Blockers
