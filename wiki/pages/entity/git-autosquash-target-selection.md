---
title: git-autosquash-target-selection
category: entity
created: 2026-09-24
updated: 2026-09-24
sources:
  - git 2.54.0 (Apple Git-157) `rebase -i --autosquash` todo 실측 2회 (scratch autosquash_semantics.sh·autosquash_semantics2.sh, 2026-09-24)
  - git v2.54.0 sequencer.c `todo_list_rearrange_squash` (code-reviewer 소스 대조, L6645-6773)
  - man git-rebase `--autosquash`
---

# git-autosquash-target-selection

`git rebase -i --autosquash` 가 `fixup!`·`squash!`·`amend!` 커밋을 어느 커밋 뒤로 옮기는지(대상 선택) — git 2.54 실측. 문서(man)는 "title or hash" 정도만 말하고 세부 우선순위는 적혀 있지 않아, 대상을 스스로 계산하는 도구([[commit-restructure-plumbing-cas]] 의 `commit-check` `fixup_of`)는 이 실측을 기준으로 삼는다.

## 규칙 (git 2.54.0 실측)

1. **첫 접두는 `fixup! `(공백 한 칸) 리터럴**이어야 한다. `fixup!\t<제목>`(탭)은 fixup 으로 취급되지 않고 그냥 pick 된다.
2. 접두 뒤 공백과 반복 접두(`fixup! fixup! X`, `fixup!  X` 두 칸)는 건너뛰고 나머지 `X` 를 대상 문자열로 쓴다.
3. 대상 문자열 `X` 로 찾는 순서:
   1. 앞선 커밋 중 **제목이 정확히 `X`** 인 것.
   2. (공백 없는 `X`) **커밋 이름으로 해석** — sha 접두 등. 해석한 커밋이 todo 안에 있어야 한다.
   3. 앞선 커밋 중 **제목이 `X` 로 시작**하는 것.
4. 각 단계에서 후보가 여럿이면 **가장 앞(오래된) 커밋**을 고른다 — 같은 제목 두 개면 첫 번째.
5. **제목 일치가 sha 보다 먼저**다: `X` 가 어떤 커밋의 sha 이면서 다른 커밋의 제목과도 같으면 제목 쪽이 대상.
6. **fixup 류 커밋도 대상 후보**다: `fixup! <다른 fixup 커밋의 sha>` 는 그 fixup 커밋에, 접두 단계에서도 `fixup! orphan` 같은 fixup 커밋 제목이 선택될 수 있다.

## 근사할 때 주의

- 커밋 이름 해석은 ref 이름·`HEAD~n`·모호한 짧은 sha(repo 전체 기준 모호하면 해석 실패 → 3단계로)까지 포함한다. 범위 안 sha 접두만 보는 구현은 근사이며 문서에 그렇게 적는다.
- 같은 제목의 커밋을 두 개 만들면 `--fixup=<sha>` 로 만든 `fixup! <제목>` 도 **첫 번째** 커밋에 붙는다 — 목적 단위 커밋을 쓰는 흐름([[dlc-development-cycle]])은 단위 제목을 서로 다르게, 한쪽이 다른 쪽의 접두가 되지 않게 짓는다.
