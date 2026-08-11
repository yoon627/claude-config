---
title: lesson-parser-precedent-partial-mirror
category: decision
created: 2026-07-26
updated: 2026-07-26
sources:
  - PR #105 (session-brief stalePlanLine — code-review CONFIRMED Major 2건)
  - scripts/plan-lint.js (미러링 대상 선례 파서)
  - CLAUDE.md §10 frontmatter 템플릿
---

# lesson-parser-precedent-partial-mirror

같은 데이터를 읽는 파서를 새로 쓸 때 **"기존 선례를 참고했다"는 정규식 한 줄을 옮겨왔다는 뜻이 아니다**. 선례의 **전처리**(정규화)와 **관용 범위**(값이 실제로 취할 수 있는 형태)까지 옮겨야 한다. 둘 중 하나만 빠져도 파서는 **에러 없이 조용히 무음**이 되고, 그 무음은 "해당 없음"과 구분되지 않는다.

## 사례 (이 lesson 의 발단)
`session-brief.js` 에 세 번째 신호 M(닫히지 않은 plan)을 붙이며 plan frontmatter 파서를 새로 썼다. plan 은 `plan-lint.js` 가 이미 파싱하고 있었고, plan 문서에도 "`plan-lint.js:98-111` 선례를 미러링"이라고 명시했다. 그런데 실제로 옮긴 것은 `^---\n([\s\S]*?)\n---` 블록 스코프뿐이었고 **두 가지가 빠졌다**:

1. **전처리 누락 — CRLF 정규화.** 선례는 `String(text||'').replace(/\r\n/g,'\n')` 로 정규화한 뒤 같은 정규식을 쓴다. 이 repo 의 `.gitattributes` 는 `* text=auto` 라 Windows 체크아웃에서 `plans/*.md` 가 CRLF 가 된다 → `---\r\n` 이 정규식에 불일치 → 모든 plan skip → **M 신호 전체가 무음 exit 0** 으로 "정상"처럼 보인다.
2. **관용 범위 누락 — YAML 인라인 주석.** 선례는 `^status:\s*(\S+)` 로 첫 토큰만 취한다. 새 파서는 `(.+)$` 로 줄 전체를 캡처했다. **CLAUDE.md §10 의 정본 템플릿이 `status: in_progress  # in_progress | blocked | done`** 이므로, 그 템플릿을 그대로 복사해 만든 plan 은 값이 `"in_progress  # in_progress | blocked | done"` 이 되어 **영구 무음**이 된다. plan-lint 는 첫 토큰만 보니 통과시켜서 어떤 게이트도 이걸 못 잡는다.

둘 다 code-reviewer 가 실행 실증으로 잡았다(CONFIRMED Major). 자체 테스트는 LF·주석 없는 fixture 만 생성해 전부 통과하고 있었다.

## 근본 원인 (3 Whys)
1. **왜 무음 결함?** 새 파서가 선례의 정규식 *모양*만 가져오고 전처리·토큰 관용을 안 가져왔다.
2. **왜 안 가져왔나?** "미러링한다"를 plan `# Decisions` 에 *선언*했을 뿐, 선례 함수를 **끝까지 읽고 대조하지 않았다** — 정규식이 있는 줄만 보고 그 앞의 정규화 줄과 캡처 그룹 차이를 넘겼다.
3. **왜 테스트가 못 잡았나?** fixture 를 내 파서의 가정(LF·주석 없음)대로 만들었다. **입력의 정본은 내 가정이 아니라 문서화된 템플릿과 체크아웃 실물**인데, 그쪽에서 fixture 를 뜨지 않았다.

## 올바른 방법
- 선례를 미러링한다고 쓸 거면 **그 함수 전체를 읽고 항목별로 대조**한다 — 전처리(개행·BOM·trim), 캡처 범위, 실패 시 반환값. "참고했다"는 plan 선언이 아니라 대조 결과로 뒷받침한다.
- **fixture 는 실제 입력 정본에서 뜬다.** 문서화된 템플릿(`CLAUDE.md` §10 frontmatter 블록)을 **그대로 복사해** 케이스로 넣고, 플랫폼 변형(CRLF·BOM)도 별도 케이스로 만든다. 내 구현 가정대로 만든 fixture 는 자기 자신만 검증한다.
- **무음이 정상 동작인 기능은 실패도 무음이다.** fail-open·"해당 없으면 출력 없음" 계약을 가진 코드는 결함이 관측되지 않으므로, 정상 경로 테스트만으로는 살아 있는지 알 수 없다 — "이 입력이면 반드시 뜬다"는 양성 케이스를 입력 형태별로 깔아야 한다.
- 새 파서를 만들기 전에 **선례를 호출로 재사용할 수 있는지 먼저 검토**한다. 이번엔 `plan-lint.js` 가 값 추출 API 없이 `lintPlan` 만 export 하고(재사용 불가), fail-open 계약상 외부 모듈 의존이 부담이라 자체 구현이 맞았지만 — 그 판단은 export 목록을 확인한 뒤에 내려야 한다.

## 연계
무매칭을 부재로 단정하는 인접 실패는 [[lesson-grep-absence-not-proof]], 증거 기반 완료 판정은 [[evidence-gate]], 반복 workflow 실패 추적은 [[workflow-failures]], 리뷰 이중화(plan+code)는 [[dual-review-plan-and-code]].

같은 "형식은 맞는데 무음으로 틀린 값" 계열의 후속 실패가 [[lesson-test-after-implementation]] — 그쪽은 선례 미러링이 아니라 **경계값 열거를 구현 뒤로 미뤄서** 같은 결과가 났다.
