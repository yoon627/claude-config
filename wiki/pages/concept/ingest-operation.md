---
title: ingest-operation
category: concept
created: 2026-06-16
updated: 2026-06-16
sources:
  - https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
---

# ingest-operation

[[llm-wiki-pattern]] 의 3 연산 중 하나. raw 소스(또는 작업 산출 지식)를 wiki 에 반영하는 과정. 이 repo 에선 `/wiki ingest` 로 실행.

## 절차
1. raw/ 에 원문 저장(있으면) — `git check-ignore` 로 gitignored 확인.
2. `source/` 에 1:1 요약 페이지 생성(원문 기반일 때).
3. 관련 `entity`/`decision`/`concept` 페이지 갱신(없으면 생성). 한 ingest 가 보통 여러 페이지 touch.
4. `index.md` 등재 + `log.md` append.
5. 불변 규칙 준수: ≥2 `[[링크]]`, claim 마다 sources, 모순은 callout.

## [[project-memory]] 맥락
dlc 작업 후 재사용 가치 있는 지식만 ingest(opt-in). trivial·일회성은 제외.
