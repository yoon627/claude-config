---
title: config-audit — 운영 자산 정합성 점검 스킬(/audit, 읽기전용·보고·제안)
status: done
started: 2026-06-19
updated: 2026-06-19
---

# Goal
운영 자산(skills·agents·CLAUDE.md·settings.json·MEMORY.md·README·wiki)의 **크로스-자산 정합성**을 읽기전용으로 점검해 심각도와 함께 보고하는 `/audit` 스킬. 기존 hook/lint 가 못 보는 영역(자산 간 참조 정합)을 메운다. **수정은 제안만**(§1 운영자산 자가수정 금지 — 자동 수정 안 함).

# Progress
- 2026-06-19: Explore — 현재 repo 정합(hooks↔scripts·MEMORY↔memory 전부 OK). audit 영역=크로스-자산 참조. draft plan.
- 2026-06-19: plan-reviewer(Claude+Codex) CONDITIONAL — 강한우려 3+약한 다수 반영: 죽은스크립트 info만(require 그래프·화이트리스트), 심각도 코드 명문화, MEMORY 절대경로 발견형, agents 단방향, 역할=집계+크로스참조(README↔surface 제외), settings.local·.bak·darwin inline 견고화.
- 2026-06-19: 구현 — audit.sh(6점검·심각도·read-only) + SKILL.md(절차·역할경계) + README/lint.yml dogfooding. 검증: bash -n OK, 현재 repo error=0(오탐 없음: dlc-ledger/dlc-doc-drift·*.ps1 안 뜸), 깨진케이스 모사 A3 PASS(없는 hook/agent·name누락 전부 탐지), A5 read-only. → code-reviewer.

# Next
1. audit.sh(기계 점검·심각도 prefix·read-only) 작성 → 실행 + 깨진케이스 모사 + 오탐 없음 확인
2. SKILL.md(절차·의미점검·역할분리·보고) 작성 → dogfooding 등록 → code-reviewer

# Decisions
- **역할 = 집계 + 크로스참조만**(plan-reviewer/Codex 반영): audit 은 ① 기존 점검 **집계**(`/wiki lint` 결과 요약·`dlc-doc-drift` hook 존재 안내 — 재구현 아님) + ② **아무도 안 보는 자산 간 참조 정합**만 신규 점검. **README↔surface drift 는 hook 영역이라 audit 이 안 본다**(이중 회피).
- **심각도 규칙 코드 명문화**(plan-reviewer 반영, 주관성 제거): `error`=실행경로 깨짐(없는 hook script 참조·고아 인덱스→파일 없음·문서가 참조한 agent 부재·SKILL name 누락), `warn`=미등록이나 수동 가능·인덱스 한쪽 누락, `info`=인벤토리·약한 참조 후보(단정 금지). audit.sh 가 라인 prefix 로 출력.
- **죽은 스크립트 = info 만, 단정 금지**(plan-reviewer 반영 — 오탐 위험): 4축 분류 후 *어디서도 안 보이는* 것만 후보로 나열. (a) settings/CI 등록 (b) **require/import 피호출**(`grep -rl "require.*<base>"`) (c) 문서 언급 (d) 수동/설치 유틸 화이트리스트(`*.ps1`·`*.py`·`install-*`·`pre-commit-check*`). 하나라도 걸리면 살아있음. dlc-ledger·dlc-doc-drift 는 (b)로 살아있음 확인.
- **MEMORY 경로 = 절대경로 발견형**(plan-reviewer 반영): worktree 상대경로·gitignored 라 못 찾음 → `$HOME/.claude/projects/`*`*--claude/memory/` glob 으로 발견. 없으면 그 점검 skip(보고 명시).
- **agents 점검 = 단방향**(plan-reviewer 반영): §5 전수나열 가정 폐기(architecture-reviewer 1회뿐). "문서(CLAUDE.md·README)에 이름이 나온 agent 가 실제 `agents/*.md` 로 존재하는가"(추측 참조 방지)만. 역방향(§5 미언급=고아) 안 함.
- **settings 스캔 견고화**(plan-reviewer 반영): `settings.json` + `settings.local.json` 둘 다. command 에서 `scripts/*.js` 만 추출(inline darwin `rtk-rewrite.sh`·SessionStart git pull 은 파일 아니라 제외). `*.bak` 제외.
- **기계 점검=`skills/audit/audit.sh`**(평문·read-only, e 의 collect-state.sh 패턴), **의미 점검=SKILL 절차**(문서 모순·중복 trigger·개선점은 LLM 판단). audit.sh 에 수정/파괴 명령 없음 — 수정은 제안 + 승인 시 별 작업(wt→dlc).
- **스킬 구조**: c/e/wiki 동일 형식(frontmatter name+description, 절차 산문). 호출 `/audit`.
- **rollback**: `skills/audit/` 삭제 + **README dogfooding 동기화분도 revert**(디렉토리 삭제만으론 README 편집 잔존).

# Key Files
- `skills/audit/SKILL.md` (신규) — 점검 절차·역할분리·보고형식
- `skills/audit/audit.sh` (신규) — 기계 정합 점검(평문, read-only)
- `README.md`·`CLAUDE.md`(§5 부근 해당시)·lint.yml — dogfooding 동기화

# Acceptance
- A1 점검 항목: audit.sh 실행 → 평문 + 심각도 prefix(error/warn/info)로 (1)settings(+local) hooks↔scripts 실존 (2)MEMORY 인덱스↔파일 양방향(절대경로 발견; 없으면 skip 명시) (3)문서↔agents 실존 단방향 (4)SKILL frontmatter name (5)죽은스크립트 **info 후보**(4축 통과분만) (6)wiki index↔pages 개수. 각 라인이 심각도로 분류됨. (실행 관찰)
- A2 심각도 정확: error=실행경로 깨짐만, warn/info 가 error 로 과대분류 안 됨. 규칙이 코드에 박혀 재현.
- A3 깨진케이스 탐지: 없는 hook script 참조·고아 MEMORY 인덱스 줄 모사 → 각각 error/warn 으로 보고(미탐 없음).
- A4 오탐 없음(현재 repo): 실제 실행에서 dlc-ledger·dlc-doc-drift 가 죽은스크립트로 안 뜸(require 피호출), `*.ps1`/`*.py` 가 죽음으로 안 뜸(화이트리스트), darwin inline 명령이 missing 으로 안 뜸. Explore 확인 정합과 일치.
- A5 read-only: audit.sh 에 수정/파괴 명령(rm·git commit/add·worktree remove·sed -i·`>`/`>>` 파일 리다이렉트 등) 없음(grep 확인).
- A6 역할 분리: SKILL 이 wiki lint 위임·drift hook 보완을 명시하고 README↔surface drift 는 안 본다고 경계 명시. 의미 점검(모순·중복·개선)은 절차 포함.
- A7 dogfooding: 새 스킬을 README(skills 섹션·Layout)에 동기화 → drift hook 무경고. audit 자기 실행이 새 자산(skills/audit, audit.sh)을 정합으로 봄.
- A8 검증: `bash -n` + shellcheck + 실제 실행 관찰.

# Blockers
(없음)

# Review Disposition
plan-reviewer(Claude+Codex) 강한우려 3+약한 다수 → 설계 반영(info만·심각도·MEMORY절대·단방향·역할경계). code-reviewer(Claude 단독 — Codex stdin hang §9) REQUEST CHANGES:
- Major① cwd 의존 거짓통과 → **fix**: 선두 self-cd(../.. = repo root, git 비의존 + CLAUDE.md·skills 가드). 비-repo 면 exit 2.
- Major② 점검5 require 부분일치+정규식 미이스케이프 → **fix**: `.js` 경계 매칭 + stem 이스케이프(`.`→리터럴). foo↔foobar 오인 차단.
- Minor SC2012 ls → **fix**: glob for. Nit .test.js → **fix**: 명시 제외.
- Minor 점검3 화이트리스트 하드코딩(새 네이밍 agent 미탐) → **defer**: 현 agent 네이밍 안정·info 한계로 수용. 후속 시 agents/ 인벤토리 역참조로 보강.
2회 한도 내 1회로 Major 해소 → fix loop 종료. code-simplifier 메인 직접(80줄·함수통일·중복없음) — 단순화 항목 없음.

# Deferred
- audit 점검3 agent 참조가 화이트리스트(reviewer|simplifier|researcher) 휴리스틱 — 새 네이밍 agent 미탐. agents/ 인벤토리 기준 역참조로 보강 여지(범위 밖·심각도 낮음).

# Progress (재검증)
- 2026-06-19: code-reviewer Major 2 + Minor fix → bash -n OK, A3 깨진케이스 PASS(error=3), 현재 repo error=0 오탐 없음, self-cd(/tmp 모사도 점검).
