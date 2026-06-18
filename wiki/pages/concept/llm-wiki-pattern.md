---
title: llm-wiki-pattern
category: concept
created: 2026-06-16
updated: 2026-06-16
sources:
  - https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
  - https://nandigamharikrishna.substack.com/p/andrej-karpathys-llm-wiki-full-breakdown
---

# llm-wiki-pattern

이 wiki 가 따르는 패턴. Andrej Karpathy 가 2026-04-04 공개. LLM 이 raw 소스를 읽어 상호링크 markdown wiki(영속·누적 지식베이스)를 점진적으로 구축·유지한다. RAG 의 "매 쿼리 재합성 후 소멸" 대신 한 번 컴파일해 누적. 이 인스턴스는 그 패턴을 [[project-memory]] 용도로 구현한 것.

## RAG 와의 차이
- RAG: 매 쿼리마다 raw chunk 검색·재합성, 누적 없음(nothing accumulates).
- Wiki: 전처리·상호링크된 페이지를 한 번 컴파일해 누적. 모순은 [[ingest-operation]] 시점에 flag.
- 환각 리스크: RAG 는 chat 에 머물지만, wiki 는 페이지에 기록돼 근거로 재인용될 수 있어 **인간 리뷰가 더 중요**.

## 3 레이어
- raw sources(불변, LLM 읽기만) / wiki pages(LLM 생성) / schema(운영 규약 — 이 repo 에선 `wiki/WIKI.md`).

## 3 연산
- [[ingest-operation]] · query · lint. 이 repo 의 운영 인터페이스는 `/wiki` skill.

## 보조 파일
- `index.md`(페이지 카탈로그) · `log.md`(append-only 로그). 상호참조는 위키링크 표기, 모든 페이지 ≥2 링크.

## 한계
- 환각이 페이지에 영속화될 수 있음 → 리뷰 필수.
- ~150 소스 초과 시 context 한계로 미묘한 연결 누락 가능(인덱싱 보조 필요).

## 배경
Vannevar Bush 의 Memex(1945) 계보. Bush 가 못 푼 "상호참조 유지보수는 누가 하나"를 LLM 이 자동화해 해결.
