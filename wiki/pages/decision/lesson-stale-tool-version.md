---
title: lesson-stale-tool-version
category: decision
created: 2026-08-03
updated: 2026-08-03
sources:
  - wiki/pages/decision/workflow-failures.md (rtk 오재작성 항목, 6회)
  - https://github.com/rtk-ai/rtk/blob/master/CHANGELOG.md (0.35.0 · 0.39.0)
---

# lesson-stale-tool-version

외부 도구가 오작동하면 **동작을 우회하기 전에 설치 버전을 상류와 대조한다**. 이미 고쳐진 버그를 로컬에서 우회하는 건 증상 억제(CLAUDE.md §1)이고, 우회 코드는 업그레이드 후에도 남아 빚이 된다.

## 무슨 일이 있었나

`tail -160 <file>` 같은 평범한 명령이 `/usr/bin/read: read: -1: invalid option` 으로 실패하는 일이 **6회** 반복됐다. 매번 스크립트 파일로 우회하고 [[workflow-failures]] 에 횟수만 올렸다.

실제 사슬(2026-08-03 확정):
1. 증상 — `tail -160 f` 가 `/usr/bin/read` 오류로 실패.
2. 직접 원인 — rtk 가 `tail -N f` → `rtk read -N f` 로 재작성. 같은 rtk 가 `head -20 f` 는 `rtk read f --max-lines 20` 으로 **올바르게** 번역하는데 `tail` 은 플래그 번역이 없다.
3. 근본 원인 — `rtk read` 가 미지원 인자를 만나면 원본 명령이 아니라 **서브커맨드 이름**(`read`)으로 폴백해 `/usr/bin/read` 를 실행한다. 설치본 **0.28.2** 의 버그이며, 상류는 `0.35.0`(read/cat 다중 파일)·`0.39.0`(head/tail 다중 파일 native 폴백, #1362)에서 이미 고쳤다. 당시 상류 최신은 **0.44.2**.

## 왜 6회나 놓쳤나

[[workflow-failures]] 표의 "수정 후보 위치" 칸에 **검증되지 않은 추정**(`hooks/rtk-rewrite.sh` 재작성 조건 좁히기)이 적혀 있었다. 그 파일은 실제로는 rewrite 규칙이 하나도 없는 얇은 위임자이고(모든 로직은 rtk 바이너리 안), `.gitignore` 로 untracked·도구 관리 파일이라 고칠 수도 없었다. 표를 볼 때마다 "고치려면 hook 을 손봐야 하는데 도구가 덮어쓸 것" 이라는 잘못된 인상이 재생산됐다.

## 다음부터

- 도구발 오류는 **`<tool> --version` 을 상류 릴리스·CHANGELOG 와 대조**하는 것을 재현 다음 첫 단계로 둔다. 검색 신호는 CLAUDE.md §4 의 "라이브러리 버전별 동작·알려진 버그"에 이미 있다 — 로컬 코드에 빠져 있을 때 특히 놓친다.
- 실패 표의 **수정 위치는 확인된 것만 적는다.** 추정이면 `미확정` 으로 두는 편이 낫다 — 틀린 위치는 공백보다 나쁘다(잘못된 방향을 6회 재생산).
- 우회(스크립트로 감싸기)는 **그 세션을 넘기는 임시 조치**일 뿐이며, 반복되면 우회 자체가 신호다. 같은 우회를 2회 하면 도구 버전을 본다.

## 연계

누적 표는 [[workflow-failures]], 자기개선 경계는 [[self-diagnosis-and-improvement-status]], 증거 없는 단정 금지는 [[lesson-grep-absence-not-proof]] 와 같은 계열이다.
