---
title: e-skill-speedup — e 마무리의 읽기전용 git 점검을 단일 배치 스크립트로
status: done
started: 2026-06-19
updated: 2026-06-19
---

# Goal
e(plan-end) 스킬이 마무리 시 느린 근본원인 — 읽기 전용 git 신호 수집이 SKILL.md 산문에 단계별로 분산돼 에이전트가 10+ 개별 Bash 호출(LLM 왕복)을 하는 것 — 을, 신호를 JSON 한 방에 반환하는 헬퍼 `skills/e/collect-state.sh` 로 묶어 왕복을 1회로 줄인다. **판정·삭제 결정·파괴 명령은 메인(SKILL) 그대로 보존**(스크립트=사실 수집, SKILL=정책).

# Progress
- 2026-06-19: 병목 코드 확정 — SKILL.md git 명령 ~20개, 읽기전용 신호가 1·2·5단계에 분산. draft plan.
- 2026-06-19: plan-reviewer(Claude+Codex) CONDITIONAL — 강한우려 4건 반영해 설계 정정: 호출 2회(재수집 invariant), 평문 출력(jq 미설치), raw 신호(mergedToBase·isMainWorktree bool 폐기), unknown vs false 분리, degrade 폴백.
- 2026-06-19: 구현 — collect-state.sh(평문·read-only·fail-safe) + SKILL.md 2·5단계 갱신(판정 보존+폴백 병기) + lint.yml shellcheck + README 동기화. 검증: bash -n OK, main/worktree 실행 신호가 수동 git 과 일치, A5 read-only 확인(파괴명령 0), upstream 미설정에서 unpushedStatus=allRemotes(false 아님). → code-reviewer.

# Next
(완료 — PR #59 squash 머지, CI lint pass. 단계당 개별 git 10+ → collect-state.sh 2회로 절감.)
1. collect-state.sh 작성(평문 출력) → 실제 main·worktree 실행 + 기존 git 명령과 대조
2. SKILL.md 2·5단계를 "collect-state.sh 호출 → 평문 판정, 실패 시 폴백"으로 갱신(판정 기준 불변)
3. README Layout 동기화 → code-reviewer → 검증

# Deferred
- `skills/c/SKILL.md`(:40-42)도 동일 git 완료여부 신호 사용 → collect-state.sh 공유 여지(이 작업 범위 밖, 심각도 낮음). 후속 고려.

# Decisions
- **헬퍼 스크립트(bash)**: §2(긴·복잡 명령은 Write 로 스크립트화) 부합. 한 Bash 에 git 10+ 인라인은 §2 위반·가독성↓ → 파일로.
- **호출 2회**(plan-reviewer 반영, 1회 아님): e 는 2단계에서 WIP 임시커밋·3단계에서 plan write 로 상태를 바꾼다. 5단계 "삭제 직전 재수집" invariant(SKILL:45) 보존하려면 ② 2단계 수집 1회 + ⑤ 삭제 직전 1회 = 총 2회. 개선 목표는 "단계당 개별 git 10+회 → 2회"(여전히 큰 절감).
- **평문 `key: value` 출력**(JSON 폐기 — plan-reviewer 반영): `jq` 미설치(실측). 메인(LLM)이 직접 읽으므로 JSON 불필요 → escape 지옥·깨진 JSON 위험 회피. list 는 들여쓰기 라인. 경로는 repo-relative.
- **raw 신호만, 판정은 SKILL**(plan-reviewer 반영): bool 평탄화 금지.
  - `mergedToBase` bool **폐기** → `base`·`baseValid`·`inBase`(log BASE..HEAD 빈지, baseValid 일 때만; 아니면 unknown) + `remoteContainingHead`(self **포함** raw). (a)base포함/(b)다른 원격·self 제외·"확정 아님 근거 명시"는 SKILL(:50-54) 그대로.
  - `isMainWorktree` bool **폐기** → `root`·`mainWorktree` raw path 만. 슬래시·대소문자 normalize 비교는 SKILL(:46) 메인 유지(Git Bash `/c/..` vs `C:/..` 차이).
- **unknown vs false 분리**(false-positive 삭제 차단 — plan-reviewer 반영): 실패를 false 로 뭉치지 않는다. `unpushedStatus: upstream|allRemotes|unknown`(upstream 없으면 폴백 `log <br> --not --remotes`=allRemotes, 원격 자체 없으면 unknown). SKILL 은 **unknown=항상 제안 생략(보수)**. `inBase` 도 baseValid=false 면 unknown.
- **dirty = tracked-only**(`status --porcelain`), ignored 는 별도 `ignored`(`--porcelain --ignored`). base 폴백은 `origin/HEAD`→`origin/main` 만 복제(과욕 금지).
- **각 점검 독립 fail-safe**: detached·upstream 없음·origin 없음에서 개별 git fatal 을 격리(`2>/dev/null`·조건 가드)해 그 필드만 none/unknown, 스크립트는 exit 0. 깨진 신호가 전체를 막지 않음.
- **런타임 degrade**(plan-reviewer 반영): SKILL 갱신은 기존 git 명령 절차를 지우지 않고 "collect-state.sh 1회로 대체, **실패·필드누락 시 삭제 제안 생략(보수)+기존 명령 폴백**"으로. revert 없이도 안전 degrade.
- **파괴 명령 분리 유지**: worktree remove·branch -d/-D·add/commit 은 스크립트 밖(AskUserQuestion·안전검사 뒤 메인). 스크립트 read-only.

# Key Files
- `skills/e/collect-state.sh` (신규) — 읽기전용 신호 JSON
- `skills/e/SKILL.md` — 2·5단계를 배치 호출로 갱신(판정 기준 보존)
- `README.md` — Layout 의 skills/e/ 에 헬퍼 반영(선택 — 정확성)

# Acceptance
- A1 출력: main worktree·이 worktree 에서 실행 → 평문 `key: value` 라인, 스키마 키 전부 존재(root·branch·detached·mainWorktree·dirty·status·upstreamStatus·upstream·unpushedStatus·unpushed·base·baseValid·inBase·remoteContainingHead·ignored). (실행 관찰)
- A2 정확성 대조: 각 신호가 기존 개별 git 명령 결과와 일치 — dirty(tracked-only)·upstream·unpushed·inBase·remoteContainingHead(self포함)·ignored 를 수동 git 과 대조.
- A3 unknown 분리: upstream 미설정 브랜치(이 worktree 가 실제 그러함)에서 `unpushedStatus`=allRemotes 또는 unknown 이지 **false 아님**. origin 없음 모사 시 unknown + exit 0.
- A4 판정 보존: SKILL 5단계 조건1~6·(a)/(b) self제외·임시커밋·정리 규칙의 **결정 로직 불변**(신호 출처만 교체). isMainWorktree·mergedToBase bool 을 스크립트가 계산하지 않음(raw path/inBase+remote raw). diff 로 판정 문구 보존 확인.
- A5 read-only: collect-state.sh 에 remove/branch -d·-D/commit/add/reset/push 없음(grep 확인).
- A6 왕복 감소: 기존 1·2·5단계 개별 git 호출 → collect-state.sh **2회**(2단계+5단계직전)로 대체됨을 SKILL 절차에서 확인. degrade 폴백 명문화 존재.
- A7 검증: `bash -n` + shellcheck + 실제 실행 관찰. README Layout 동기화 시 drift hook 무경고.

# Blockers
(없음)

# Review Disposition
plan-reviewer(Claude+Codex) 강한우려 4건 → 설계 반영(2회 호출·평문·raw·unknown). code-reviewer(Claude+Codex) REQUEST CHANGES:
- Major① awk `$2` 공백 경로 잘림 → **fix**: `substr($0,10)`. 회귀 테스트(`C:/some path/with spaces` 보존) 통과.
- Major② status/ignored 실패 평탄화 → **fix**: `if cmd; then..else unknown`. `dirty`∈{true,false,unknown}, `ignoredStatus`∈{known,unknown}, SKILL 조건3·6 에 unknown→제안생략 추가.
- Minor dirty 주석(tracked-only 틀림) → **fix**: "untracked 포함" 정정 + SKILL 조건3 문구 정합.
- Minor colon split 계약 → **fix**: SKILL 2단계에 "첫 `: ` 1회 split" 명시.
- Minor quotePath 따옴표 래핑 → **fix**: `-c core.quotePath=false`.
- Nit emit_list whitespace-only → **wontfix**(git 생산자가 공백-only 안 만듦, 무해).
2회 한도 내 1회로 Major 해소 → fix loop 종료. code-simplifier: 메인 직접 점검(bash 70줄·중복 없음·emit_list 통일) — 단순화 항목 없음.

# Progress (재검증)
- 2026-06-19: code-reviewer Major 2 + Minor 3 fix → bash -n OK, 실행 신호 정상, 공백경로 회귀 통과, ignoredStatus 출력 확인.
