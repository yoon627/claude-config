---
title: code-reviewer-absorb — 빌트인 /code-review 요소를 code-reviewer 자산에 흡수
status: in_progress
started: 2026-07-21
updated: 2026-07-22
---

# Goal
빌트인 `/code-review`(Workflow-backed, 바이너리 2.1.216에서 추출)의 4개 요소를 `agents/code-reviewer.md`에 흡수하되, 이 자산의 정체성(단일 비판 리뷰어 + Codex 모델 다양성)은 유지한다.
- A) report-everything / filter-downstream, B) finding별 failure_scenario, C) altitude/conventions angle, D) 같은 세션 내 find→self-verify 2-pass.
- Opus 4.8 릴리스노트의 code-review 하네스 튜닝 지침("only high-severity/conservative 필터를 문자대로 따라 recall↓") 반영.

# Progress
- 2026-07-21: 빌트인 /code-review 소스 추출(바이너리 2.1.216) — 5-phase, finder angle, report-everything, failure_scenario, verdict(CONFIRMED/PLAUSIBLE/REFUTED), 4.8 튜닝 노트 확인. Explore 완료. draft plan v1 작성.
- 2026-07-21: plan-reviewer(+codex medium 병행, 전 항목 독립 수렴) = **CONDITIONAL**. 핵심 결정 "verdict가 확신도 대체" 철회 — 아래 Decisions v2로 재설계(축 분리·REFUTED 감사로그·defect/recommendation 분리·공유규약 불변·fixture dry-run). 지적이 명확·반영 방향 확정적이라 plan-reviewer 재실행 생략, 구현 후 code-reviewer가 최종 점검.
- 2026-07-22: 구현(code-reviewer.md 6곳 + README) → plan-lint 통과 → fixture dry-run(acceptance8) 통과 → code-reviewer(+codex medium) = **REQUEST CHANGES**(Critical 1 실증: H3 heading 이 grep `^##?` 패턴에서 유실). fix loop 1회로 전 항목 반영(verdict collinear→반증결과만 재정의 · grep H2 복원 · ❌템플릿 제거 · failure_scenario 몰드 일반화 · Codex 독립입력 · 상태전이 고정 · 종합판단 매핑 · Opus4.8 모델비종속). C1 실증 재검증 통과(`## Critical` H2 매치, H3 잔재 0). 2회차 리뷰 생략(핵심 반영+실증). simplify 특이사항 없음(문서 지침).

# Next
최종 검증(plan-lint 통과 · markdown 추가 lint 없음) 후 Report — 사용자에 push/PR/머지 선택지.

# Decisions
> v2 = plan-reviewer 지적 반영 재설계. v1의 "verdict로 확신도 통합"은 **철회**.

- **[v1→v2 변경] verdict는 확신도 "대체"가 아니라 직교 필드로 추가 (이유: 축 혼동).** severity(머지 영향)·확신도(✅/⚠️/❌, 인식적 확신·CLAUDE.md §1)·verdict(CONFIRMED/PLAUSIBLE/REFUTED, self-verify 처분)는 **3개의 직교 축**. "✅확실하게 REFUTED"가 성립하므로 대체 불가. → 셋 다 유지·병기.
  - severity heading(Critical/Major/Minor/Nit) **유지** — grep 통합(code-reviewer.md:60, codex-review.md:61) backward compat.
  - 확신도 prefix(✅/⚠️/❌) **유지** — §1 의무. `❌모름`을 PLAUSIBLE로 **승격 금지**(정보 손실·§1 "모름을 모름으로" 위반) → 근거 부족 항목은 출력의 **Open questions**로 분리.
  - verdict는 각 finding의 **필드**(heading 아님) — code-reviewer 고유 추가. Codex 출력엔 verdict 없으므로 통합은 severity heading grep 유지, verdict는 필드로 병기.
- **[v2] REFUTED 계약**: self-refute는 **구체적 반증 증거 있을 때만** REFUTED(재현 실패·근거 못 찾음·심각도 낮음은 REFUTE 아님 → PLAUSIBLE/❌ 유지). REFUTED는 **삭제가 아니라** 출력의 `refuted 후보(감사 로그)`에 `candidate/failure_scenario/refutation_evidence/checked_files` 보존. 최종 제거·disposition은 **메인**(dlc fix/defer/false-positive/wontfix, SKILL.md:98) — subagent가 선점 금지. (A와 정합: report-everything로 다 올리고, REFUTE는 증거 있을 때만 하니 recall 안 낮춤.)
- **[v2] D는 Codex 병행을 대체 않고 계층**: self-verify(같은 모델 2-pass)와 codex(외부 모델)의 **correlated blind spot** 문제 → Codex엔 self-refute 후 verdict만 주지 말고 **독립 동일 입력(원 후보/번들)** 제공, 두 모델 동의만으로 CONFIRMED 금지(코드·실행·문서 증거 요구).
- **[v2] C(altitude/conventions) 경계는 "발견/정리"가 아니라 "영향"으로**: 기능·보안·계약 영향 있으면 code-review finding + 메인 fix loop(Major/Critical 가능), 동작 비영향 정리만 simplify(13단계). altitude는 **단일 함수/파일 수준**만(레이어·구조 altitude는 architecture-reviewer 몫 — 삼중 중복 회피).
- **[v2] B(failure_scenario)는 defect 한정**: 런타임 결함=`failure_scenario`(구체 입력/상태→잘못된 출력/크래시) 필수. recommendation(conventions·altitude·테스트누락·유지보수)=`cost`(무엇이 중복/취약/유지보수 어려움)로 분리 — "failure_scenario 없으면 finding 아님"은 defect에만 적용.
- **[v2] 범위·격리**: `docs/codex-review.md`는 전 reviewer 공유 규약(codex-review.md:3)이라 **불변**. report-everything/failure_scenario/verdict 문구는 **code-reviewer.md의 도메인 특화 프롬프트 블록에만** 격리(전 reviewer 누출 방지). 확신도 공통 계약(✅/⚠️/❌)은 안 바꾸므로 plan-reviewer와 divergence 없음.

# Key Files
- `agents/code-reviewer.md` — 주 대상(검토 관점·2-pass 프로세스·출력 형식·동작 규칙). 문구 격리처.
- `docs/codex-review.md` — **불변**(공유 규약). Codex에 독립 입력 제공은 code-reviewer.md의 병행 블록에서.
- `README.md` L271 — code-reviewer 검토 관점 요약(C 동기화 대상).

# Blockers
(없음)

# Acceptance
1. **A report-everything**: "finder(Pass1) self-censor 금지 / half-believed도 올림 / 심각도·필터는 보고 단계" 명시 + 4.8 튜닝 근거 1줄. 검증: 파일 grep + fixture dry-run(정황만 후보가 드롭 안 됨).
2. **B failure_scenario/cost**: defect엔 `failure_scenario` 필수, recommendation엔 `cost`. 검증: 출력 형식에 두 필드 + defect/recommendation 분리 규칙.
3. **C angle**: altitude(함수/파일 수준)·conventions 추가 + "영향" 경계 1줄 + architecture-reviewer/simplify 중복 회피. 검증: 관점 리스트에 2개 + 경계 문구.
4. **D 2-pass**: Find→Verify 2-pass, verdict(CONFIRMED/PLAUSIBLE/REFUTED) **필드** 정의, REFUTE는 증거 있을 때만, REFUTED 감사로그. 검증: 프로세스·출력에 존재.
5. **축 정합(핵심)**: severity·확신도·verdict 3축 병기, ❌모름 미승격(Open questions), Codex 독립입력·동의만으로 CONFIRMED 금지, 메인 disposition 선점 금지. 검증: 출력 형식·병행 블록에 문구.
6. **범위**: codex-review.md diff 없음(불변). 검증: `git diff --stat`에 docs/codex-review.md 미포함.
7. **README 동기화**: L271이 C 반영 갱신 or 불요 판정 1줄.
8. **fixture dry-run**: 고정 예시(실제 버그→CONFIRMED / 정황만→PLAUSIBLE / 정보부족→❌ / 구체반증→REFUTED / Codex-only 후보 보존 / severity+verdict 추출)로 행동 검증. 검증: dry-run 관찰 기록.
9. **리뷰 통과**: code-reviewer(자산 대상, +codex 병행) 통과, blocker 해소.

# Review Disposition
- plan-reviewer v1 findings: 전부 `fix`(Decisions v2에 반영). REFUTED-false-positive 이중 필터 경계 → v2에서 "메인 disposition 선점 금지"로 처리.
- code-reviewer(구현 후) findings: C1(grep H3 heading 유실, 실증) `fix`+실증 재검증 · M1(verdict↔확신도 collinear) `fix`(반증결과만 재정의) · M2(❌ 템플릿) `fix` · M3(무근거 defect 3중 불일치) `fix`(상태전이 고정) · M4(failure_scenario 몰드 협소→보안/race 누락) `fix` · M5(Codex "+원후보" 모순) `fix` · 반증 긍정기준·심각도충돌·Verify후 보존·구조 escalation·종합판단 매핑·Opus4.8 모델비종속·REFUTED 표기 `fix`. Nit(한영혼용·`## Minor / Nit` 한줄·codex `-A` 절단) `defer`→ # Deferred.

# Deferred
- plan-reviewer/architecture-reviewer로의 verdict·report-everything 확장 — 이번 범위 밖(code-reviewer 한정, 확신도 공통계약은 불변이라 divergence 없음). 심각도: 낮음. 파일: agents/plan-reviewer.md, agents/architecture-reviewer.md.
- Nit(code-reviewer 리뷰): 한영 혼용(altitude/설계고도) 최초 1회 정의 후 통일 · `## Minor / Nit` 개별 분리 · codex 출력 `-A 40` 절단→marker 추출. pre-existing·경미. 심각도: Nit.
