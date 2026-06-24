---
title: lesson-grep-absence-not-proof
category: decision
created: 2026-06-24
updated: 2026-06-24
sources:
  - PR #65 (CLAUDE.md §13 실수·교훈 로그)
  - README.md Components — CLAUDE.md 절 나열
---

# lesson-grep-absence-not-proof

`grep` 무매칭(빈 출력)을 **"대상이 없음"으로 단정**하지 말 것. 무매칭은 "이 패턴이 안 맞았다"일 뿐, 부재의 증거가 아니다. 특히 **문서 동기화 필요 여부 판정**처럼 결론이 "불필요"로 빠질 때 위험하다 — 패턴이 빗나가면 필요한 동기화를 통째로 건너뛴다.

## 사례 (이 lesson 의 발단)
CLAUDE.md 에 §13 을 추가한 뒤 "README 동기화 필요한가?"를 `grep '## 1[0-3]' README.md` 로 점검 → 무매칭 → **"README 는 절 번호 미러링 안 함, 동기화 불필요"로 단정**. 실제로 README Components 의 `### CLAUDE.md` 절은 헤더(`##`)가 아니라 **본문 리스트**(`12. 피드백 메모리 …`)로 14개 절을 나열하고 있었다. 패턴이 그 형식을 못 잡았을 뿐, README 는 갱신 대상이었다. `dlc-early-stop` 의 doc-drift 경고가 포착해 바로잡음([[evidence-gate]] 보조망의 가치).

## 근본 원인 (3 Whys)
1. **왜 오판?** grep 한 줄 무매칭만 보고 "미러링 안 함" 결론.
2. **왜 무매칭?** 패턴 `## 1[0-3]` 은 마크다운 헤더만 노렸는데 README 의 절 나열은 본문 리스트 형식이라 구조가 달랐다.
3. **왜 검증 부족?** 동기화 필요 판정인데 **대상 파일(README) 구조를 직접 열어보지 않고** 단일 grep 신호로 단정 — 부정 증거를 약한 도구 신호로 확정.

## 올바른 방법
- "X 없음/불필요"를 grep·검색 무매칭으로 단정하지 않는다. 무매칭은 가설을 **반증 못 한 것**이지 입증한 게 아니다.
- 동기화·영향 판정은 대상 파일을 **Read 로 구조를 직접 확인**한 뒤 내린다(grep 은 위치 좁히기 용도, 결론 근거 아님).
- 부재를 주장하려면 **직접 증거**를 쓴다 — 예: gitignore 여부는 grep 대신 `git check-ignore`(이 PR 에서 memory 트래킹 판정에 실제로 적용).
- CLAUDE.md §1(추측 금지·코드 보고 답)·§3 Verify(문서 동기화는 evidence gate 항목)의 구체적 실패 양상이다.

## 연계
완료 게이트·doc-drift 보조망은 [[evidence-gate]], 반복 workflow 실패 추적은 [[workflow-failures]], 개발 사이클 검증 단계는 [[dlc-development-cycle]].
