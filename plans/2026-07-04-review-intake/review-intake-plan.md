---
title: review-intake — c skill 개선 2건: (A) PR 리뷰 intake + (B) 자동 진행(예외 5종)
status: done
started: 2026-07-04
updated: 2026-07-14
---

# Goal
c skill 개선 2건(같은 파일 — 한 브랜치): **(A) PR 리뷰 intake** — plan 이어받기(`/c`) 시 그 브랜치의 PR 에 사용자가 남긴 리뷰 코멘트를 자동 수집해 ① 미해결 지적을 다음 액션(fix loop 입력)으로 제시하고 ② 작업방식 교정성 코멘트를 §12 feedback memory 판정으로 넘긴다 — "사용자 코드리뷰 → 개선 → 기억" 루프의 마지막 미연결 구간(2026-07-04 사용자 확인, 상위 plan Workstream D). **(B) 자동 진행** — `/c` 가 진단·보정 후 멈추지 않고 `# Next` 가 명확하면 바로 이어서 실행한다(2026-07-04 사용자 지시 "c 쓰면 알아서 진행했으면" — 매번 재확인이 실사용 마찰).

# Progress
- 2026-07-04: Fable 세션에서 설계·수용기준 확정(이 plan). 구현은 opus 세션 몫.
- 2026-07-04: opus 세션 /c 로 이어받음. sync 진단 — plan↔실제 완전 일치(브랜치=origin/main, 커밋 0, clean). 환경 확인: `gh` 설치·인증됨(yoon627). gh grounding 실행 — `gh pr list --head <BR> --state all --json number,state,title` 정상, `gh pr view <n> --json reviews,comments` 정상; 이 repo PR 표본(#50~#71) 전부 `reviews=0 comments=0`(self-merge 패턴) → Acceptance #2 "사람 리뷰 0건 경로" 관찰 충족. 구현은 미착수(코드 변경 없음). author/authorAssociation 하위필드로 bot·자기 제외 필터 확정은 미완(중단).
- 2026-07-05: /c 이어받기 — sync: 여전히 **구현 미착수**(origin/main..HEAD 커밋 0, clean). base 가 구 main(3386ec7)이라 그 뒤 머지된 새 main `18f2b07`(gwl 작업 — README·skills/wt 변경) 미포함 → 구현 시 **README 겹침 주의**(merge/rebase 시 충돌 가능). Key Files 3개 실재 확인. `# Next` 유효(구현 착수). **rebase onto `18f2b07` 완료(ff, 충돌 0)** → gwl 반영·README 겹침 해소. dlc 로 구현 착수.
- 2026-07-05: 구현 완료 — grounding(현재사용자 yoon627·reviews/comments 빈배열 관찰·bot 필터 `[bot]` 접미). skills/c/SKILL.md(frontmatter description·2단계 PR intake·3단계 처분 a/b+이어서실행+예외 5종·경계 절 narrowing), README 286·289 동기화, wiki feedback-memory(intake 경로+updated 2026-07-05+source). 검증: 제거문구(제시만/멈춤/자동실행안함) 0 잔존, intake·사람필터·예외5종 존재, improve.sh error=0. 다음: code-reviewer.
- 2026-07-05: code-review(Claude REQUEST CHANGES + codex) 수렴 — **Major: `gh pr view --json` 인라인 코멘트 미수집**(cli/cli #11477) → fix loop 1회로 인라인 `gh api .../pulls/<n>/comments` 3소스 수집 추가 + 잔여 "제시" 프레이밍(line 3·8·14) 정정 + 경계 read-only 명시 + 예외2 fallback 일반화·예외4 파괴 확장 + 비trivial→dlc wt/slug 게이트 명문화 + done 근거. disposition/Workflow Finding(빈배열 grounding) 기록. 재검증: 정합 통독 OK·improve.sh error=0. 커밋 `30fe13c`(3파일).
- 2026-07-14: (9일 경과) 새 main(`9a5da3b`)에 클린 rebase(main 이 skills/c·README·wiki 미변경) → **머지 #75 (`9a5da3b`)** → worktree·로컬·원격 브랜치 정리, plan 은 main/plans 로 보존. `/c` 스킬이 main 에서 활성. **done**.

# Next
(완료·머지 #75·정리 끝. 남은 것 없음)
1. push/PR → merge 결정 (`gh pr merge --delete-branch` 권장 — 원격 정리 동반).
2. merge 후 worktree/브랜치 정리(feedback `worktree-cleanup-after-merge` 대로 능동).
3. 향후: 인라인 코멘트 있는 PR 로 intake 라이브 실검증(현재는 REST API 문서·cli/cli #11477 로 확정).

# Decisions (설계)
- **수집 위치**: c SKILL 2단계(진단)에 "PR 리뷰 수집" 항목 추가. 명령(읽기 전용): `gh pr list --head <BR> --state all --limit 3 --json number,state,title` 로 브랜치 PR 식별 → 있으면 `gh pr view <n> --json reviews,comments` 로 리뷰·코멘트 수집. **bot/자기 코멘트 제외, 사람 코멘트만**.
- **fail-open**: `gh` 미설치·미인증·원격 없음·PR 없음 → 그 점검만 skip 하고 보고에 "PR 리뷰: 확인 불가(<사유>)" 1줄 (c 의 기존 "점검 명령 실패 시 skip 명시" 패턴 준수). 네트워크 왕복 1-2회라 부담 낮음 — 무조건 실행이 아니라 **plan 이 매칭된 경우에만**.
- **처분 (3단계 보정·제시에 연결)**: 수집된 사람 코멘트를 두 갈래로 분류해 제시 —
  - (a) **코드 지적**(버그·수정 요청): `# Next` 후보로 "PR#n 리뷰 반영: <요지>" 제시(자동 실행 안 함 — c 의 기존 경계 유지). 미해결 여부는 코멘트 resolved 상태·후속 커밋 존재로 추정하되 확정 불가면 그대로 노출.
  - (b) **작업방식 교정**(스타일·절차 지적): §12 feedback memory 저장 **판정**을 보고에 포함(대상이면 저장 제안, dlc Report 판정 의무와 동일 문구 — 저장 자체는 사용자 확인 후).
- **경계**: 새 스크립트·hook 없음(SKILL 서술만). 자동 회신·자동 resolve 없음. gh api 호출은 read-only 만.
- **(B) 자동 진행 규칙 (2026-07-04 Fable 세션 스코프 추가)**: c SKILL 3단계 "보정 + 다음 액션 제시 **(그리고 멈춤)**" → "보정 + **이어서 실행**". 경계 절의 "다음 액션 자동 실행 안 함" 항목 제거. **멈추는 예외(닫힌 목록 5종)**: ① `status: blocked`(해소가 사용자 몫) ② plan 후보 2개+(선택 필요 — 기존 유지) ③ `# Next` 가 비었거나 실효돼 재구성한 경우(방향 확인 1회) ④ 다음 액션이 파괴적·외부공개(push·머지·삭제 — §8 게이트 그대로) ⑤ done plan(이어갈지 확인 — 기존 유지). 그 외엔 sync 요약 1줄 보고 후 곧장 진행 — 비trivial 구현이면 dlc 파이프라인으로 이어진다. (A)의 처분 (a) "자동 실행 안 함" 은 **제시 문구가 아니라 실행 대상**이 되도록 (B) 기준과 정합화: 리뷰 반영도 명확하면 Next 로 채택 후 바로 진행.
- **(B) 문서 동기화**: c SKILL frontmatter description 의 "다음 액션은 제시만 하고 자동 실행하지 않는다" 문구 교체 + README skills/c 절("다음 액션은 제시만" 서술) 갱신. e SKILL 의 "/c 로 이어받기" 언급은 영향 없음(확인만).
- **(B) Acceptance 추가**: ⑤ SKILL·description·README 3곳에서 "제시만/멈춤" 문구가 사라지고 예외 5종이 명시됨 ⑥ 예외 케이스별 서술이 기존 규약(§8 push 게이트·done 확인·후보 다수 선택)과 모순 없음(문서 대조).
- **e(plan-end)에는 안 넣는다** — 마무리 시점엔 리뷰가 아직 없을 확률이 높고, intake 는 "이어받기" 시점이 맞다. 필요해지면 별도.

# Key Files
- skills/c/SKILL.md — 2단계 진단 표 PR 리뷰 행 + 3단계 처분·"이어서 실행" 전환 + 경계 절 + frontmatter description(B)
- README.md — skills/c 절 1-2줄 동기화
- wiki/pages/concept/feedback-memory.md — intake 경로 추가 서술(1줄, 해당 시)

# Blockers
(없음)

# Acceptance
1. c SKILL 에 수집(3소스: 리뷰 요약·conversation·**인라인 gh api**·사람 한정)·fail-open(사유 명시 skip)·처분 2갈래(a/b)·경계(**PR intake read-only — 자동 회신·resolve 없음**)가 전부 서술됨.
2. **실측 grounding**: `gh pr list/view` 실행으로 필드 실존·0건 경로 관찰(이 repo PR 은 전부 self-merge reviews=0 comments=0). ⚠️ **한계**: 빈배열만 관찰해 인라인 코멘트 미수집 갭을 못 걸렀음(code-review 가 잡음) → 인라인 수집 명령은 **GitHub REST API·cli/cli #11477 로 확정**(라이브 인라인 데이터 미보유). 인라인 있는 PR 실검증은 향후.
3. gh 부재 시뮬레이션(PATH 제한 또는 명령 실패)에서 skip 문구 경로 서술대로 동작 가능함을 확인.
4. README 동기화 diff 존재. improve.sh error=0 비회귀.
5. (B) c SKILL 본문·frontmatter description·README 3곳에서 "제시만/멈춤/자동 실행 안 함" 문구가 사라지고 **멈춤 예외 5종**(blocked·후보 다수·Next 재구성·파괴적/외부공개·done)이 명시됨 — grep + 통독.
6. (B) 예외 5종 서술이 기존 규약과 모순 없음을 문서 대조로 확인: §8 push/삭제 게이트 · done 전환 사용자 확인(e SKILL) · 후보 다수 선택(c 기존) · wt slug 확인(생성 게이트는 별개 유지).

# Review Disposition
- (Major, Claude+codex) intake 가 `gh pr view --json reviews,comments` 로 **인라인 line 코멘트 미수집**(cli/cli #11477 확인) → 조용한 false-negative → **fix**: `gh api .../pulls/<n>/comments` 3소스 수집 + 한계 명시.
- (minor, Claude) 잔여 "제시" 프레이밍 line 3·8·14 → **fix** (통독 정합).
- (minor, Claude+codex) 경계 절 "자동 회신/resolve 없음" 미명시 → **fix**.
- (minor, codex) 예외2 "2개+"→fallback 선택 일반화 → **fix**. 예외4 파괴 default 확장(migration/DB) → **fix**.
- (minor, codex) 비trivial→dlc 재확인 없음 ↔ wt slug 게이트 → **fix**: dlc 가 wt-first+slug 확인 적용함을 명시(전이적 보존을 명문화).
- (⚠️minor, Claude) c 가 done 을 write vs e done-확인 비대칭 → **fix(경미)**: 객관적 사실 기록+예외5 정지 근거 1줄. pre-existing 로직 자체는 유지.
- (nit) 처분(b) "dlc 판정과 동일" 부정확 → **fix**: 판정 의무 동일, intake 는 저장 전 확인.
- (⚠️nit, Claude) wiki/index.md 미갱신 → **no-change**: subsection 추가라 one-liner "사용자 교정의 영속화" 여전히 정확(concept 절 관례=terse). 근거 기록으로 갈음.

# Workflow Findings
- **degenerate-data grounding 이 거짓 acceptance 통과**: Acceptance #2 가 "코멘트 있는 PR 없으면 0건 경로로 충분"이라 빈배열(self-merge)만 보고 통과 → 정작 주 대상인 인라인 코멘트 수집 갭을 code-review 전까지 못 잡음. 재발조건: grounding 대상이 degenerate(빈/동형)인데 acceptance 가 '충분'으로 인정. 수정 후보: dlc Acceptance 규약에 "외부 API/실행 artifact 는 대상의 non-degenerate 실형태로 검증하거나 '문서로만 확정' 명시". 발생 1회.
