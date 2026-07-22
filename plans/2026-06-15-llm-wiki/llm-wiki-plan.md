---
title: llm-wiki — 개발지식 프로젝트 메모리 인스턴스 + dlc/CLAUDE.md 통합
status: done
started: 2026-06-15
updated: 2026-06-19
---

# Goal

Karpathy의 LLM Wiki 패턴(LLM이 raw 소스를 읽어 상호링크 markdown wiki를 영속·누적 유지)을 이 `.claude` 글로벌 설정 repo에 **실제 인스턴스**로 도입한다. 목적: dlc 개발 사이클이 작업마다 새로 조사·재합성하는 대신, 아키텍처 결정·교훈·검증된 외부 사실(버전/API/CVE)을 wiki에 누적해 다음 작업이 재사용하는 **"프로젝트 메모리"**. plans/(일시적 작업 핸드오프, 작업 종료 시 닫힘)와 보완 — wiki는 작업을 가로질러 누적.

# Progress
- 2026-06-19 PR #39 머지 완료 (main). status: done — worktree 정리.

- 2026-06-15: karpathy gist + breakdown 조사 → `docs/llm-wiki.md` 개념 정리 작성·commit(140fb32). 사용자 요청으로 방향 전환 → "repo에 실제 wiki 구축 + dlc/CLAUDE.md 통합"으로 재정의. Explore(repo 구조)·Plan(설계) subagent 완료. CLAUDE.md divergence 실측. plan 작성. 설계 승인(docs 제거 방침 확정). **사용자가 이번 세션 구현 보류 — 설계·기록만 하고 마무리 결정. 구현은 다음 세션.**
- 2026-06-16: /c 로 이어받아 **MVP-1 완료·커밋(87239d9)**. wiki/ 골격+seed 이식(docs/llm-wiki.md 제거)·skills/wiki/SKILL.md·.gitignore(`!/wiki/`+`wiki/raw/`)·CLAUDE.md §11(@RTK 앞)·README 3곳. code-review(메인+Codex): blocker 0, Major 3 반영(raw 불변·orphan outbound/inbound 구분·시크릿 write전 차단). simplifier: 중복 축약+lint log append 보강. 검증 통과(dead link 0·orphan 0·≥2 outbound·raw gitignore·시크릿 0).
- 2026-06-16(이어서): **MVP-2·3 완료**. check_links.py+test(TDD 7케이스, 커밋 4744125), dlc 통합(wiki 연계 섹션, 커밋 541a8fb). 전체 검증: wiki clean·7 tests OK·tree clean. MVP 1-3 구현 완료.
- 2026-06-16: push(`origin/llm-wiki-notes`) + **PR #39** 생성(https://github.com/yoon627/claude-config/pull/39). 머지 대기.

# Next

**push + PR #39 완료.** 남은 것:
- **PR #39 리뷰·머지**(사용자). 머지되면 `/e` 로 plan done 처리 + worktree 정리 제안.
- 후속(선택): pre-commit/CI `git ls-files 'wiki/raw/**'` 금지(Codex 제안). dlc wiki 훅은 다음 dlc 작업 때 실동작 확인.

# Decisions

## 확정(사용자)
- wiki 주제 = **이 repo 개발 지식**(아키텍처 결정·교훈·외부 사실), dlc 직결. (대안 "범용 KB"·"둘 다" 기각.)
- **raw = gitignore**(저작권·용량), **wiki 페이지 = git 포함**. 첫 seed = `docs/llm-wiki.md` 이식.

## 설계(Plan agent 종합)
- **새 런타임/의존성 0** — "파일 + 규약 + skill 지시문"만. 기존 형틀(텍스트 가이드, 메인 single-writer, 격리 read-only) 계승.
- **디렉토리 = 루트 `wiki/`** (docs/ 하위 아님 — docs는 사람용 정적 문서라 성격 충돌, gitignore 제어도 루트가 깨끗):
  ```
  wiki/ WIKI.md index.md log.md raw/(gitignored) pages/{concept,entity,decision,source,query}/
  ```
  entity(외부사실: 버전/API/CVE)·decision(이 repo 결정·교훈) 분리가 이 인스턴스 핵심. overview는 concept 상위 페이지로 흡수(초기 과분할 방지).
- **schema = `wiki/WIKI.md`** (CLAUDE.md/AGENTS.md 이름충돌 회피). frontmatter(title/category/created/updated/sources) + 불변규칙 5개(≥2 `[[링크]]` / 모든 claim sources 인용 / 모순은 `> [!conflict]` callout / raw write 금지 / 모든 연산 log append).
- **운영 = skill `/wiki <ingest|query|lint>`** (`/wt` 서브커맨드 분기 선례). command/dlc통합 대신 skill 채택(dlc는 코드변경 사이클이라 지식관리와 분리). write는 메인만.
- **dlc 통합 = 조건부·opt-in 2지점**: ①1단계 Explore에서 wiki query(있을 때만, 없으면 no-op) ②16단계 Report 후 재사용 지식 있으면 `/wiki ingest` 제안(자동 아님). 16단계 표는 안 늘림. plan→wiki **일방향 승격만**(양방향 동기화 금지).
- **CLAUDE.md = 새 §11, 4~5줄 포인터만**(상세는 WIKI.md, `@import` 안 함 → 비대화 방지). §10 확장 아님(plans/wiki 경계 흐려짐 방지).
- **seed = 복사+가공**(이동 아님): docs/llm-wiki.md를 WIKI.md frontmatter+`[[링크]]`+sources 형태로 가공해 `pages/concept/llm-wiki-pattern.md` 생성. **docs/llm-wiki.md는 git rm 확정**(중복 진실소스 방지 — 사용자 승인 2026-06-15). 단 이번 세션엔 미실행(구현 보류), 다음 세션 이식과 함께 제거.
- **MVP 3단계 분리 커밋**: MVP-1 골격(독립·롤백 가능) → MVP-2 `check_links.py`+test(자동검증, TDD) → MVP-3 dlc 통합(타 컴포넌트 수정이라 격리).
- **진행: 이번 세션 구현 보류**(사용자 결정 2026-06-15) — 조사·설계·plan 기록까지만. 다음 세션에 위 설계대로 MVP-1부터 구현. (2026-06-16 "진행해"로 MVP-1 실행.)

## code-review 반영 (2026-06-16)
- **raw 규약 = 불변(immutable)**: "읽기만/안 씀" vs "원문 저장" 모순 제거 → 적재(사용자/ingest 입력)는 1회, LLM 은 가공·수정·삭제 안 함.
- **orphan 구분**: 작성규칙 = outbound ≥2 / lint = inbound 부재(index.md 제외). 별개 불변식.
- **시크릿**: raw 적재·페이지 write 전 점검 → 발견 시 마스킹/중단(경고-후-계속 아님). pages 도 raw 와 대칭.
- **§11 머지**: @RTK.md 앞 배치로 main CodeGraph 블록(@RTK 뒤·uncommitted)과 위치 분리 → origin/main 미존재라 비충돌(code-review 입증). divergence 동기화 불필요했음.

## MVP-2·3 구현 (2026-06-16)
- check_links.py: stdlib, TDD 7케이스. 코드블록 내 `[[ ]]` 미구분은 규약(pages 본문은 위키링크를 코드 예시로 안 씀)으로 수용·주석화.
- dlc 통합: 파이프라인 직후 'wiki 연계' 섹션(16단계 표 불변). 1 Explore query·16 Report ingest 제안 — 조건부·opt-in·wiki 없으면 no-op.

# Key Files

- 생성: `wiki/WIKI.md`, `wiki/index.md`, `wiki/log.md`, `wiki/pages/concept/llm-wiki-pattern.md`(+stub ≥2), `skills/wiki/SKILL.md`, (MVP-2) `skills/wiki/check_links.py`+`test_check_links.py`
- 수정: `.gitignore`(`!/wiki/`+`wiki/raw/`), `CLAUDE.md`(§11), `README.md`(Components+섹션목록+Layout), `skills/dlc/SKILL.md`(MVP-3 §1·§16)
- 제거: `docs/llm-wiki.md`(이식 후 — 보수안 택하면 유지)

# Blockers

- ~~CLAUDE.md divergence~~ **해소(2026-06-16)**: §11 을 @RTK.md 앞에 배치 → main CodeGraph 블록(@RTK 뒤·origin/main 미존재 uncommitted)과 위치 분리되어 머지 비충돌(code-review 입증). 동기화 불필요했음.
- repo에 md linter/CI 없음 → 검증은 자작 `check_links.py` + `git check-ignore`/`git status` + 수동(Obsidian 그래프). "미검증" 아님을 이 수단으로 충족.
