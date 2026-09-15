---
title: conclusion-block — 답변 끝 `## 결론` 고정 블록 규칙 + Stop hook 존재 검사
status: in_progress
started: 2026-09-15
updated: 2026-09-15
---

# Goal

파일을 바꾼 턴의 마지막 답변이 `## 결론`(문제/원인/조치/검증/남은 것) 블록으로 끝나게 한다 — 규칙은 CLAUDE.md §3-6, 강제는 `dlc-early-stop.js` 의 네 번째 축(capped 1회·fail-open).

# Intent

- Problem: 사용자가 작업 뒤 "뭐가 문제였고 어떻게 해결했는지"를 매번 다시 묻는다. 결론이 보고 산문에 섞여 구분이 안 되고, 기존 §3-6 "결론 요약 ≤3줄 먼저"는 형식·항목(문제/원인)·강제가 없다. (사용자 확인 2026-09-15, 선택지 B 채택)
- Constraints:
  - 블록은 답변 **맨 끝**(상세는 위, 결론은 아래 — 사용자: "결론만 확실하게 보고… 더 알고싶으면 윗내용을").
  - 항목 5개 고정: 문제 / 원인 / 조치 / 검증 / 남은 것. 해당 없으면 `해당 없음`.
  - hook 은 **존재만** 검사(`## 결론` heading). 내용 품질은 규칙의 몫. capped 1회·fail-open — 기존 세 축과 같은 패턴, 같은 hook 안에서 합산 출력.
  - 게이트 = 이 턴에 plan 외 파일 편집(Edit/Write/NotebookEdit, `.md` 포함) — 기존 `changed` 는 `.md` 를 빼므로 별도 `edited` 플래그 추가(⚠️ 모델 판단: 규칙 변경 같은 문서 작업도 결론이 필요하므로).
  - 운영 자산(CLAUDE.md·hook) 변경은 사용자 승인됨(B 선택). README 동기화 동반.
- Out of scope: 파일 변경 없는 답변(질문·조사)의 hook 강제 — 규칙만 적용. 결론 블록의 내용 검증. 기존 세 축의 동작 변경.
- Open questions: 없음 — `last_assistant_message`(string, 텍스트만)·`transcript_path` 둘 다 공식 hooks 문서에 존재 ✅(researcher 2026-09-15, https://code.claude.com/docs/en/hooks.md).

# Progress

- 2026-09-15: worktree 생성, Explore, draft plan, researcher(`last_assistant_message` 공식 문서 확인), plan-reviewer+codex CONDITIONAL → 전부 반영. 하네스 실증 2건(2.1.272: Stop stdin 필드 · `decision:block` 전달). TDD Red→Green(23 tests), 구현 4파일 + 문서 6곳 동기화, `dlc-signal.test.js` KINDS 개수 스냅샷 갱신. Acceptance 5 e2e 실증(`--setting-sources local --settings` 인라인 hook: (a) 합산 block→결론 재응답→통과, (b) 통과+`edited` 소비). 첫 e2e 시도는 사용자 settings 병합으로 main·worktree 사본 hook 이 같은 ledger 에 동시 write 해 JSON 이 깨진 probe 전용 race — `--setting-sources` 로 해결.

- 2026-09-15 (cont.): code-reviewer+codex(high) NEEDS DISCUSSION → Major(AskUserQuestion 뒤 마감 오탐)는 probe 로 `last_assistant_message` = 마지막 텍스트 블록만임을 실증 후 §3-6 규칙으로 처분, Minor 3 fix(펜스 무시·producer 테스트·재종료 경로 소비)·1 defer, Nit 2 fix. simplify: 4축 조건 중복 제거. 테스트 25·71 통과.

- 2026-09-15 (final): 격리 runner 최종 검증 — `verify.sh` ALL PASS(skip 없음), early-stop 25·evidence-ledger 71·signal 20 통과, 옛 문구 0건. evidence gate 전 항목 충족 → DONE. 커밋.

# Next

1. `/e merge`(medium — push→PR→머지→정리). 머지 후 실 세션에서 결론 축 1회 관찰(선택).

# Decisions

- 결론 블록 위치는 **끝**(기존 §3-6 "먼저"를 덮어씀). 이유: 사용자가 마지막 것만 보고 판단하고 싶어 함. 같은 문구를 가진 `skills/dlc/SKILL.md:153`·`skills/e/SKILL.md:48`·`README.md:314` 도 **같은 커밋**에서 "끝"으로 맞춘다(부분 revert 로 규칙·강제가 어긋나지 않게).
- §3-6 내부 우선순위: **Stop hook 경고·오탐 대응 턴은 결론 1줄 규칙이 우선**(결론 블록 면제) — 그 턴의 재종료는 `stop_hook_active` 로 통과하므로 hook 과도 충돌 없음.
- hook 게이트는 `changed`(코드만) 대신 새 `edited`(plan 외 모든 편집). 이유: 이 요구는 검증 게이트가 아니라 보고 형식 게이트라 문서 편집 턴도 대상. `changed` 의 `.md` 제외는 verify 오탐 방지 목적이라 건드리지 않음. **세팅 위치**는 evidence-ledger 의 `!isPlan && !isIgnored` 블록 안(gitignored·repo 밖 scratch 제외, `.md` 포함). `plans/` 만 고친 턴은 결론 불요. Bash `sed -i`·삭제·rename 은 미탐 감수(기존 축과 동일).
- **`edited` 수명 = 결론 축 통과 시 소비**(`edited=false`), 재편집 시 `edited=true`+`conclusionBlocks=0`. 이유: ledger 리셋은 UserPromptSubmit 1곳뿐이고 reminder-only 턴·AskUserQuestion 응답은 리셋이 없어(plan-reviewer 지적, `dlc-task-router.js:35-42`) 소비하지 않으면 후속 짧은 답변을 block 한다. 기존 3축 장부는 건드리지 않는다.
- 마지막 메시지 취득: `last_assistant_message` 만 사용. 실증 2026-09-15 Claude Code 2.1.272 `--settings` 인라인 hook 으로 Stop stdin 덤프 → 키 존재·텍스트 일치 ✅. **transcript 폴백은 삭제**(YAGNI + 공식 문서가 transcript 가 in-memory 보다 늦을 수 있다고 명시). 필드 부재 → 판정 포기(fail-open, 미탐 감수).
- block 메커니즘은 기존 3축과 같은 `{"decision":"block","reason"}` JSON. 실증 2026-09-15 같은 방식으로 reason 이 모델에 전달돼 지시대로 응답함 ✅.
- 존재 검사 = **마지막 `## ` heading 이 `## 결론`**(중간 위치·코드펜스 안 문자열은 오탐 가능성 낮은 쪽으로 감수). 5항목 내용은 규칙의 몫.
- OFF 스위치 `CLAUDE_DLC_CONCLUSION_OFF=1`(기존 축 명명 규칙). 신호 kind `early-stop-conclusion`(failure), **detail 없음**(답변 본문·transcript 경로를 telemetry 에 넣지 않는다 — §8).
- 4축은 자체 try/catch — 예외가 기존 축의 `reasons`·카운터를 삼키지 않게(파일 주석 6~8행의 false negative 금지).
- 기각: output style — deprecated 로 알려져 있어(⚠️) 비채택. UserPromptSubmit 주입 — Stop 이 결과를 직접 보는 쪽이 강함. transcript 폴백 — 위.

# Key Files

- `CLAUDE.md` §3-6 Report — 규칙 본문.
- `scripts/dlc-early-stop.js` — 4번째 축(결론 블록 누락).
- `scripts/dlc-early-stop.test.js` — 축 테스트.
- `scripts/dlc-ledger.js` — DEFAULT 필드 `edited`·`conclusionBlocks`.
- `scripts/dlc-evidence-ledger.js` — `edited` 세팅.
- `scripts/dlc-signal.js` — KINDS `early-stop-conclusion`. `scripts/dlc-signal.test.js` KINDS 개수 스냅샷.
- `scripts/dlc-evidence-ledger.test.js` — `edited` producer 3케이스.
- `README.md` — dlc-early-stop 설명(407행)·recap 줄(314행)·Stop 요약(469행) 갱신.
- `skills/dlc/SKILL.md` 16 Report(153행)·`skills/e/SKILL.md` recap(48행) — "먼저"→"끝" 동기화.

# Acceptance

1. `node scripts/dlc-early-stop.test.js` 결론 축 케이스 추가·통과: 블록 있음→통과+`edited` 소비 / 없음→1회 block+`conclusionBlocks=1`+signal(detail 없음) / 재종료 통과 / `edited=false` 침묵 / OFF / `last_assistant_message` 부재→통과 / `## 결론` 이 마지막 heading 아님→block / 검증 축과 동시 block 시 reason 합산·카운터 각각.
2. `bash scripts/verify.sh` 마지막 줄 `ALL PASS`(skip 없음).
3. CLAUDE.md §3-6 에 블록 형식·위치(끝)·5항목·hook 경고 턴 면제가 명시되고, `grep -rc "결론 요약.*먼저" CLAUDE.md skills README.md` 가 0건(이 환경에 `rg` 없음 — runner 확인).
4. README `dlc-early-stop.js` 항목에 ④ 축·`CLAUDE_DLC_CONCLUSION_OFF` 반영(doc-drift hook 무경고로 관찰).
5. 실 동작: `--settings` 인라인 hook 으로 worktree 사본 `scripts/dlc-early-stop.js` 를 등록한 `claude -p` 세션에서 (a) 편집 후 결론 없는 답변 → block 1회 (b) 결론 블록 답변 → 통과 관찰. (settings.json 의 등록 경로는 main 사본이라 이 worktree 세션 자체로는 관찰 불가 — plan-reviewer 지적.)

# Blockers

(없음)

# Deferred

- hooks 공식 문서의 Stop block 형식 기술이 researcher(exit 2+stderr 만)·codex(`decision:block` 명시 지원) 간 충돌. 실동작은 2.1.272 실증으로 JSON 방식 유효 ✅라 이 작업엔 영향 없음. 문서 원문 앵커 확인은 별도(심각도: 낮음). 파일: `docs/`(없음 — 참고용).

- `dlc-early-stop.js` 무경고 Stop 의 ledger write(`docSettled || conclusionSettled`)는 read-modify-write 라 늦게 끝난 background Bash 의 PostToolUse 기록을 되돌릴 수 있다 — 기존 `docSettled` 패턴과 동일한 창이 넓어진 것. 필드 단위 patch/merge-write 는 별도 작업(심각도: 낮음). 파일: `scripts/dlc-ledger.js`.

# Review Disposition

- code-reviewer(codex 병행 high, NEEDS DISCUSSION) Major 1: `결론→AskUserQuestion→짧은 마감` 오탐 → **fix** — probe 로 `last_assistant_message` 가 마지막 텍스트 블록만임을 실증, §3-6 에 "마감 텍스트 자체를 결론 블록으로" 명시. Minor: 코드펜스 오판 → fix(펜스 제거 + 테스트 2) / producer 테스트 공백 → fix(3케이스) / `stop_hook_active` 경로 소비 누락 → fix(+테스트) / ledger write 경합 창 → defer(`# Deferred`, 기존 패턴). Nit: README 407 표현·302 축 누락 → fix / H3 이후 느슨함 → wontfix(문서-구현 일치, 규칙 문구가 이미 "마지막 `## ` heading").

- plan-reviewer(codex 병행, CONDITIONAL) 강한 우려 6건: 하네스 실증 선행 → fix(실증 완료) / `edited` 수명 → fix(소비 방식) / 문서 3곳 동기화 → fix(Key Files·Acceptance 3) / §3-6 내부 충돌 → fix(hook 경고 턴 면제 명시) / 4축 try/catch → fix / Acceptance 5 실행 불가 → fix(`--settings` 인라인 등록으로 교체). 약한 우려: `edited` 위치 → fix(Decisions) / heading 위치 검사 → fix(마지막 heading) / signal detail 계약 → fix(없음+테스트) / transcript 폴백 → fix(삭제) / OFF 이름 → fix / Deferred 기술 → fix(정정).
