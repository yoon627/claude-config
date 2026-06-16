# WIKI.md — 영속 프로젝트 메모리 운영 규약

이 `wiki/` 는 이 repo·워크플로우의 **누적 프로젝트 메모리**다. raw 원문은 읽기 전용, pages 는 LLM 이 생성·유지. `plans/`(일시적 작업 핸드오프)와 달리 작업을 가로질러 누적된다. 이 파일이 wiki 운영 규약의 **단일 진실 소스**다. 충돌 시 `CLAUDE.md` 우선.

## 레이어 · 디렉토리

| 경로 | 소유 | 역할 |
|---|---|---|
| `raw/` | 사용자 | 원문(불변, **gitignored**). 적재는 사용자 큐레이션 또는 ingest 입력. LLM 은 가공·수정·삭제하지 않는다. |
| `pages/` | LLM | 생성 페이지. 아래 5 카테고리. |
| `index.md` | LLM | 모든 페이지 1줄 요약 카탈로그(카테고리별). |
| `log.md` | LLM | append-only 연산 로그. |
| `WIKI.md` | 사람+LLM | 이 규약 파일. |

페이지 카테고리 — `pages/<category>/<kebab-name>.md`:
- `concept/` — 개념·패턴·방법론.
- `entity/` — 외부 사실: 라이브러리·모델·API·CVE. **버전/날짜 포함**.
- `decision/` — 이 repo 의 아키텍처 결정·교훈(ADR-lite). 이 인스턴스의 핵심.
- `source/` — raw 원문 1:1 요약.
- `query/` — filed query 답변.

## 네이밍
- 파일 `kebab-case.md`. 페이지 제목 = 파일명. 상호참조는 Obsidian 위키링크 표기(이중 대괄호).
- 카테고리는 위 표 고정. 새 카테고리는 이 표에 먼저 추가한 뒤 사용.

## 페이지 frontmatter (필수)
```yaml
---
title: <kebab-name>
category: concept|entity|decision|source|query
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [원문경로 | PR | 커밋 | URL]
---
```

## 불변 규칙
1. 모든 페이지는 최소 **2개**의 나가는(outbound) `[[링크]]`. (lint 의 orphan=inbound 부재 점검과 구분.)
2. 페이지는 frontmatter `sources` 로 근거(page-level provenance)를 단다. 핵심 claim 은 본문에 출처 표기. 근거 없는 단정 금지(CLAUDE.md §1).
3. 모순·미해결은 기존 서술을 조용히 덮지 말고 callout 으로 flag:
   `> [!conflict] <요약>` / `> [!open] <미해결 질문>`.
4. `raw/` 원문은 **불변** — 적재 후 LLM 이 편집·삭제하지 않는다(해석 대조용 원본 보존).
5. 모든 ingest·query·lint 는 `log.md` 에 append.

## 3 연산 (상세 절차는 `skills/wiki/SKILL.md`)
- **ingest**: raw 투입 → `source/` 요약 + 관련 `entity`/`decision`/`concept` 갱신 → `index.md` 등재 → `log.md` append.
- **query**: 관련 페이지 read 후 답. 재사용 가치 있으면 `query/` 로 filed + log.
- **lint**: orphan·dead `[[링크]]`·모순·stale·index 누락 점검 → 보고(자동 수정 안 함).

## 보안
- raw·pages 에 token/password/key/인증서/PII/내부 비밀 유입 금지(CLAUDE.md §8). **모든 raw 적재·페이지 write 전 점검**, 발견 시 마스킹/중단(경고 후 진행 금지).
- raw 는 gitignored — 적재 전 `git check-ignore wiki/raw/<f>` 로 확인.
