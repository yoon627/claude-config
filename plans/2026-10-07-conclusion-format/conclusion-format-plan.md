---
title: conclusion-format — `## 결론` 항목을 답·근거·다음 중심으로 바꾸고 "결론만으로 판단" 규칙 추가
status: done
started: 2026-10-07
updated: 2026-10-07
---

# Goal
사용자가 `## 결론` 블록만 읽고 판단·행동할 수 있게 한다. 항목을 과정 중심(문제/원인/조치/검증/남은 것)에서 답 중심(답·원인(버그만)·근거·주의(있을 때)·다음)으로 바꾸고, 본문 참조 금지·판단 정보 끌어올리기 규칙을 더한다.

# Intent
- Problem: 결론을 읽고도 본문을 다시 읽어야 하는 경우가 잦다(사용자 지적 2026-10-07). 진단(⚠️ 2026-10-07 세션의 결론 블록들로 추정): 1) 항목이 과정 중심이라 질문·조사 답변에서 "조치: 정리했다"만 남고 답 내용(목록·추천)은 본문에만 있다 2) "원인: 해당 없음" 고정칸 3) "위 표 참조"류 본문 참조 4) ⚠️추정·미검증이 본문에만 있고 "검증:"엔 확인한 것만.
- Constraints: 형식은 사용자가 선택(AskUserQuestion, 2026-10-07): `- 답:` / `- 원인:`(버그·장애일 때만) / `- 근거:`(확인+미확인) / `- 주의:`(없으면 생략) / `- 다음:`. heading `## 결론`·위치(끝)·hook 판정 로직(마지막 `## ` heading 검사)·hook 경고 턴 면제는 그대로. 별도 파일로 분리하지 않는다(사용자: "별도 파일 만들 정도는 아닌 것 같다").
- Out of scope: hook 의 항목 내용 검사(존재만 본다는 기존 결정 유지). `agents/researcher.md` 의 `## 결론`(subagent 반환 형식 — 사용자 대상 결론 블록이 아님). 과거 plan 본문.

# Progress
- 2026-10-07: worktree 생성, Explore(영향 6곳 확인 — rg 로 wiki·docs·plans 포함 검색), 선행 plan `2026-09-15-conclusion-block` 의 기각안·제약 확인. plan 작성. 구현 6파일(+README 457 "5항목" 잔존·test fixture 4곳 추가 정리 — Bash 인라인 sed 가 `\\` 를 접어 무매칭, Edit 로 재처리). targeted: 옛 형식 rg 무매칭, `dlc-early-stop.test.js` 35 통과. code-reviewer(+Codex high) APPROVE — 처분 반영(아래), 테스트 35 통과(새 단언 포함). simplify 체크: 문구·fixture 변경뿐이라 대상 없음. 격리 runner 로 verify.sh 실행.

- 2026-10-07 (cont.): 사용자 요청으로 형식 추가 변경(굵은 라벨+음슴체 불릿, `━` 40자 구분선) + scoped prompt-audit F1~F4·flag 2 반영. 1차 verify(형식 변경 전 코드) exit 0·FAIL 0, `ALL PASS (skip: install-hooks.test.js(case) record-verified.test.sh)` — skip 사유: jq 미설치, 구 git(≤2.30) case 를 Windows 에서 실행 불가. 최종본 2차 verify 실행 중.
- 2026-10-07 (final): 2차 verify(최종본) exit 0·FAIL 0, 같은 환경 skip 2건 → Acceptance 4(승인된 기준) 충족. Acceptance 1(§3-6 문구 7개 요소 rg 확인)·2(옛 형식 0건, 남은 1건은 의도된 부재 단언)·3(35 통과, 라벨 안내 단언) 충족. 판정 DONE.

# Next
(없음 — 로컬 ff-merge 로 종결. 후속은 `# Deferred` 의 audit 반영·§8 예외·검증 시간 개선을 새 worktree 에서.)

# Decisions
- 선행 decision 조회: 공용 wiki 에 결론 형식 decision 없음. 선행 plan `2026-09-15-conclusion-block` 의 제약 "항목 5개 고정, 해당 없으면 `해당 없음`"을 **뒤집는다** — 근거: 그 형식이 질문·조사 답변에서 답 내용을 담지 못해 본문 재독이 필요했다(위 Problem). 사용자 승인 2026-10-07.
- 위치(끝)·heading·hook 존재 검사·경고 턴 면제는 유지 — 사용자 불만은 내용 쪽이지 위치·강제 쪽이 아니다.
- 별도 파일(예: docs/conclusion-format.md) 기각 — 규칙은 §3-6 한 문단이면 충분하고 파일을 나누면 매 세션 주입되는 CLAUDE.md 에서 형식이 빠진다.
- hook 이 항목명을 검사하도록 확장하는 안 기각 — 선행 plan 결정(내용은 규칙의 몫) 유지, 항목이 조건부(원인·주의)라 기계 검사가 오탐을 낸다.
- 항목 표기를 `- 답: …` 한 줄에서 **굵은 라벨 줄 + 사실당 불릿**으로 변경(사용자 요청 2026-10-07 "항목이 구분되고 줄글이 아니게"). 이유: 한 줄 형식이 세미콜론·괄호로 사실을 몰아넣어 결론 안에서도 줄글을 읽게 했다. 라벨은 `###` heading 아닌 굵은 글씨 — 터미널 렌더 소음 회피(hook 정규식 `^##[ \t]+` 은 `###` 에 매치하지 않아 어느 쪽도 hook 은 통과). 미확인 사실은 근거 안에서 `미확인:` 접두로 구분.
- 구분선은 `---` → `━` 40자로 변경(사용자 2026-10-07: `---` 는 세 글자로만 보여 눈에 안 띈다 — Claude Code 터미널은 수평선을 가로줄로 렌더하지 않음). `━` 는 East Asian Ambiguous 폭이라 일부 CJK 설정 터미널에서 2칸씩(80칸) 보일 수 있음 — 40자로 제한한 이유.
- 결론 블록 앞 빈 줄 + 구분선(처음엔 `---`), 결론 불릿은 음슴체(사용자 요청 2026-10-07 "결론을 구분되게, 항목은 음슴체로 짧게"). heading 이모지(`## 📌 결론`) 기각 — hook 정규식·테스트 변경 필요, 터미널마다 이모지 폭이 달라 정렬 깨짐. 본문 문체는 그대로.
- Acceptance 4 를 "skip 없음" → "이번 변경과 무관한 환경 skip 만 허용(사유 기록)"으로 변경(사용자 승인 2026-10-07). 이유: 이 PC 의 skip 2건(`record-verified.test.sh` — jq 미설치, `install-hooks.test.js` 구 git(≤2.30) case — Windows 에서 sh shim 실행 불가)은 환경 사유이고, 덮는 경로(CI 기록 job, git hook 설치)가 이번 변경(결론 규칙 문구·hook 경고 문구)과 무관. 기각: jq 설치 후 재검증(시스템 변경, 구 git case 는 여전히 skip), 기준 유지(이 PC 에서 충족 불가).
- 커밋 단위: 1개 — 규칙·hook 문구·문서가 같은 형식을 가리켜 일부만 머지되면 서로 모순.

# Key Files
- `CLAUDE.md` §3-6 — 형식 정의 본문.
- `scripts/dlc-early-stop.js` — `CONCLUSION_MISSING` 문구·주석.
- `scripts/dlc-early-stop.test.js` — `WITH_CONCLUSION` fixture.
- `README.md` 마무리 recap 줄.
- `skills/dlc/SKILL.md` 16 Report · `skills/e/SKILL.md` recap 형식.

# Acceptance
1. CLAUDE.md §3-6 에 새 항목(답·원인 조건·근거 확인+미확인·주의 생략 가능·다음)과 "결론만으로 판단 가능 — 본문 참조 금지·판단 정보 끌어올리기" 규칙이 있고, 위치·hook 경고 턴 면제 문구는 남아 있다 — 관찰: 해당 줄 read.
2. 옛 형식 잔존 0건: `rg -n "5항목|5줄|- 문제:|남은 것:" CLAUDE.md README.md skills/dlc/SKILL.md skills/e/SKILL.md scripts/dlc-early-stop.js scripts/dlc-early-stop.test.js` 무매칭.
3. `node scripts/dlc-early-stop.test.js` 전부 통과, hook 이 block 시 새 문구를 출력(테스트 출력 또는 fixture 실행으로 관찰).
4. `bash scripts/verify.sh` 마지막 줄 `ALL PASS` — skip 은 이번 변경과 무관한 환경 skip 만 허용하고 사유 원문을 기록한다(2026-10-07 사용자 승인으로 "skip 없음"에서 변경, `# Decisions`).

# Blockers
(없음)

# Deferred
- prompt-audit(2026-10-07, 보고서·diff 는 세션 scratchpad — 휘발) 범위 밖 발견. 별도 `/wt` 작업 후보:
  - [높음·확인함] `skills/wt/SKILL.md:114` `<default>` = `git symbolic-ref --short` 출력(`origin/main`)이라 `origin/<default>` 가 `origin/origin/main` → rm 의 미머지 탐지가 조용히 실패. `skills/e/SKILL.md:52` 방식(`origin/` 제거)으로 맞출 것.
  - [중간·확인함] `CLAUDE.md:95` "Agent 도구에는 effort 파라미터가 없다" — 2.1.292 Agent 도구 스키마에 `effort` 있음.
  - [결정 필요] `skills/c/SKILL.md:42` 완료 판정이 `origin/main` 기준뿐 ↔ `CLAUDE.md` §8 로컬 머지 인정. §3-6 "마무리=`/e merge`" ↔ §8 "trivial·small 은 로컬 ff-merge".
  - [사용자 결정 2026-10-07] `CLAUDE.md` §8 "검증 명령을 식별하지 못했으면 커밋하되 보고에 '검증 미식별'" 예외 → "커밋하지 않고 검증 방법을 묻는다"로 변경(사용자 원칙: 확인·검증된 것만 커밋). `skills/dlc/SKILL.md` 16단계 커밋 규칙의 같은 문구도 동기화. audit 반영 worktree 에 포함.
- 검증 시간 개선(사용자 선택 2026-10-07, 세 가지 모두 — audit 과 별개 worktree 후보):
  - 전체 verify 는 변경 확정 후 1회, 작업 중엔 관련 테스트만 — dlc 규칙에 명시(이번 작업에서 형식 확정 전 verify 를 시작해 50분×2 낭비한 실측).
  - `verify.sh` 테스트별 소요 시간 출력 — 느린 테스트 식별.
  - 바뀐 축만 로컬 + 나머지는 CI(`lint.yml` 이 축별 실행) — 로컬 ff-merge(PR·CI 없음) 경로의 기준 설계 필요.
  - [낮음] `CLAUDE.md:142` 원문자 ①~④(§0 금지 표기), description 비대화(e·wt·c·code-reviewer), dlc 날짜 조건부 규칙·이력 서술, `docs/codex-review.md:56` repo 이름 §11 공개 점검.

# Review Disposition
- code-reviewer(+Codex high, APPROVE, Critical·Major 0, 옛 형식 잔존 0 — repo·공용 wiki 전수):
  - Minor hook 문구 "버그면" ≠ 규칙 "버그·장애" → fix.
  - Minor 새 문구 단언 없음 → fix(`- 답:/- 근거:/- 다음:` 포함·`- 문제:` 부재 단언).
  - Minor 근거/주의 경계 겹침 → fix(근거 = 확인 못한 사실, 주의 = 그것이 판단을 어떻게 바꾸나).
  - Minor 원인 줄 생략 불명 → fix("아니면 줄 생략").
  - Nit "근거" 단어 겹침(§3-6 끝 오탐 대응 문구) → fix("오탐 판정 사유").
  - Nit hook 항목 순서 → fix(§3-6 순서).
  - Nit fixture `조치 예시`·공백 불일치 → fix(Edit 가 new_string 끝 공백을 잘라 `- 답:a` 가 됐던 것 포함).
  - Nit `- 다음:` 과 AskUserQuestion 중복 → wontfix(사용자 승인 형식) → 아래 scoped audit flag 로 재검토해 fix(문구 1줄).
- scoped prompt-audit(바뀐 §3-6·hook 문구, 사용자 요청 "이번 작업도 audit"):
  - F1 High hook 경고 대응 "결론 1줄·블록 면제" ↔ 결론 누락 경고의 "블록 출력" 충돌 → fix(오탐이면 한 줄, 정탐이면 블록만 출력).
  - F2 Medium hook "붙이세요" 대상 모호 → fix(본문 반복 없이 블록만 출력).
  - F3 Medium 끌어올리기 상한 없음 → fix(꼭 필요한 사실만·영향 큰 것부터).
  - F4 Medium 불릿 길이 기준 없음 → fix(한 문장).
  - flag `미확인:` ↔ §1 ❌ 이중 표기 → fix(접두가 ❌ 대신). flag 다음 ↔ 선택지 중복 → fix(무엇을 정할지만 한 줄).
