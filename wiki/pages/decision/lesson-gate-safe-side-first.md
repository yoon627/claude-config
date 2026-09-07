---
title: lesson-gate-safe-side-first
category: decision
created: 2026-09-08
updated: 2026-09-08
sources:
  - 커밋 47b7064 (fix(dlc): 빈 .git 디렉토리를 repo 로 오판하던 evidence gate 판정)
  - plans/2026-09-07-ledger-empty-gitdir
  - codex 병행 리뷰 2라운드 (2026-09-08)
---

# lesson-gate-safe-side-first

**게이트의 판정 함수를 고칠 때는 "무엇이 옳은 답인가" 보다 "판정이 틀렸을 때 어느 쪽 오류가 덜 위험한가"를 먼저 확정한다.** 안전측을 정하지 않고 정확도만 올리려 들면, 오탐 하나를 없애면서 게이트를 조용히 꺼버리는 미탐을 넣게 된다. 미탐은 오탐과 달리 **아무 신호도 남기지 않아** 발견되지 않는다.

## 사례 (이 lesson 의 발단)

`scripts/dlc-evidence-ledger.js` 의 `insideSomeRepo` 는 `fs.existsSync(<dir>/.git)` 로 repo 안팎을 갈랐다. 이 머신에 **내용이 완전히 빈 `C:\Users\USER\.git`** 이 있어(2026-07-25 생성) 홈 아래 모든 임시 경로가 "repo 안"으로 판정됐고, `/tmp` 스크래치 편집이 `changed=true` 로 기록됐다. git 본체는 그 디렉토리를 `fatal: not a git repository` 로 거부한다 — `existsSync` 가 그걸 구분하지 못한 것이다.

**1차 수정(폐기)**: "유효한 repo 인가"를 `HEAD` 존재로 판정하게 바꿨다. 빈 `.git` 오탐은 사라졌다. 그런데 `.git/HEAD` 만 유실·접근불가인 **실제 손상 repo** 도 같이 "repo 밖"으로 판정된다:

- `git check-ignore` → exit 128
- `existsSync(.git/HEAD)` → false → `insideSomeRepo` → false
- `isIgnored` → true → **`changed=false`**

원 설계가 파일시스템 판정을 쓴 이유가 정확히 그 반대였다 — 주석에 "repo 안인데 실패(safe.directory·손상·env)면 **보수적으로 changed 유지**(게이트 안전측)" 라고 적혀 있었다. 내 수정은 그 불변식을 정반대로 뒤집었다. codex 병행 리뷰가 Critical 로 잡았고, 실증했다(손상 repo 에서 `hasRepoAt` 직전 `false` → 수정 `true`).

**채택안**: 판정 대상을 "정상 repo 인가"가 아니라 **"repo 였던 흔적이 있는가"** 로 바꿨다. `.git` 이 디렉토리면 비어 있을 때만 false, 그 외에는 true. 흔적을 한 번이라도 관찰한 뒤의 판정 불능(권한·경쟁 상태)은 전부 repo 안으로 친다.

## 근본 원인 (3 Whys)

1. **왜 안전 불변식을 깼나?** 문제를 "빈 `.git` 을 어떻게 걸러내나"로 잡고, 정확한 repo 판정을 만들려 했다.
2. **왜 그 프레이밍이 틀렸나?** 이 함수는 **git 이 이미 exit 128 로 실패한 뒤에** 불린다. 역할은 정확한 판정이 아니라 "repo 밖이라 실패했나, git 이 깨져서 실패했나"를 가르는 것이다 — 애초에 정보가 부족한 자리라 *기울일 방향*이 설계의 본체다.
3. **왜 그걸 놓쳤나?** 함수 본문만 보고 고쳤다. 바로 위 주석이 안전측을 명시하고 있었는데, 호출 맥락(`isIgnored` 의 128 분기)까지 읽지 않았다.

## 올바른 방법

- 게이트·가드·검증 판정을 고치기 전에 **두 방향의 오류 비용을 먼저 적는다**. 여기서는 오탐 = 불필요한 검증 요구(마찰), 미탐 = 검증 없이 통과(사고). 비대칭이면 정확도보다 방향이 우선이다.
- **판정 불능을 "아니오"로 접지 않는다.** 권한 오류·경쟁 상태·타임아웃은 "없음"이 아니라 "모름"이고, 안전측 게이트에서 "모름"은 "예"로 간다.
- 관찰을 이미 한 뒤의 후속 실패를 앞선 관찰과 **같은 `catch` 로 묶지 않는다** — `lstat` 성공 후 `readdir` 이 ENOENT 로 던졌다고 "없음"이 되면, 본 것을 못 본 것으로 되돌린다(codex 2라운드 Critical 2).
- 감수하기로 한 미탐은 **코드 주석과 plan `# Decisions` 에 근거와 함께 명시**한다. 여기서는 "내용이 통째로 비워진 `.git` 은 빈 디렉토리와 구분 불가 → 완화됨"을 적고, `git init` 이 언제나 HEAD·config·objects·refs 를 쓰므로 git 이 만들어내는 상태가 아니라는 근거를 남겼다.
- 안전측을 바꾸는 수정에는 **그 방향을 지키는 회귀 테스트**를 함께 넣는다. 오탐 테스트만 넣으면 미탐 회귀가 통과한다 — 이 건에서도 codex 가 "가장 위험한 새 회귀를 보호하는 테스트가 없다"를 Major 로 지적했다.
- 그 테스트가 **의도한 분기를 실제로 타는지 단언**한다. 손상 repo 테스트는 `check-ignore` 가 정말 128 인지 먼저 확인한다 — 0/1 이 나오면 fallback 을 안 타고 공허하게 통과한다.

## 연계

완료 게이트와 그 보조망은 [[evidence-gate]], 개발 사이클의 검증 단계는 [[dlc-development-cycle]], 리뷰가 자기 판단을 잡아준 다른 사례는 [[lesson-grep-absence-not-proof]], plan·code 리뷰 2단 구성의 근거는 [[dual-review-plan-and-code]].
