---
name: wiki
description: 이 repo 의 영속 프로젝트 메모리(LLM Wiki, `wiki/`)를 운영하는 ingest/query/lint 오케스트레이션. raw 소스·작업 지식을 상호링크 markdown 페이지로 누적하고(ingest), 누적 페이지로 답하고(query), 무결성을 점검한다(lint). `/wiki <ingest|query|lint>` 명시 호출 시 사용. 단순 질문·코드 변경에는 쓰지 않는다(dlc/직접의 몫).
---

# wiki — LLM Wiki 운영 (영속 프로젝트 메모리)

`wiki/` 는 이 repo·워크플로우의 누적 지식베이스. 운영 규약(schema)의 단일 진실 소스는 `wiki/WIKI.md` — **시작 시 반드시 read**. 이 skill 은 그 규약을 강제하는 실행 절차다. 페이지 write 는 **메인만**(single-writer, `plans/` 와 동일 원칙). 충돌 시 CLAUDE.md 우선.

## 적용
- `/wiki ingest|query|lint` 명시 호출.
- dlc 연계(CLAUDE.md §11): 작업 시작 시 query(있을 때만), 작업 후 재사용 지식 ingest 제안(자동 아님).
- 코드 변경·단순 질문은 제외.

## 인자 해석
| 입력 | 동작 |
|---|---|
| `ingest <경로\|설명>` | raw/지식 → 페이지 갱신 + index/log |
| `query <질문>` | 페이지 read 후 답, 가치 있으면 filed |
| `lint` | 무결성 점검·보고 |
| (빈 인자) | `index.md` 요약 + 사용법 |

첫 토큰으로 분기. 모르는 서브커맨드는 사용법 안내 후 종료.

## ingest
1. `wiki/WIKI.md` read(규약 확인).
2. 원문이 주어지면 `wiki/raw/`(없으면 mkdir) 에 보존(최초 1회, 이후 불변 — 편집·삭제 안 함) → `git check-ignore wiki/raw/<f>` 로 ignored 확인. raw 적재는 사용자 큐레이션 또는 ingest 입력에서만.
3. 원문 기반이면 `pages/source/<name>.md` 1:1 요약 생성.
4. 관련 `entity`(외부사실·버전)/`decision`(이 repo 결정)/`concept` 페이지 갱신·생성. 한 ingest 가 여러 페이지 touch.
5. 각 페이지 규칙 충족: frontmatter, ≥2 outbound `[[링크]]`, sources, 모순은 `> [!conflict]`. **raw 적재·페이지 write 전 token/key/PII 점검 → 발견 시 마스킹/중단**(경고 후 진행 금지).
6. `index.md` 등재 + `log.md` append(`## [YYYY-MM-DD] ingest | <title>`).
7. 구조 점검 후 보고(현재 LLM 수동).

## query
1. `index.md` 에서 관련 페이지 식별 → read.
2. 페이지 기반으로 답(raw chunk 아님). 근거 페이지를 인용.
3. 재사용 가치 있으면 `pages/query/<slug>.md` 로 filed(frontmatter+링크) + `log.md` append.
4. 관련 페이지가 없으면 "wiki 에 없음" 명시(추측 금지). 필요 시 ingest 제안.

## lint
점검만, 자동 수정 안 함(수정은 보고 후 사용자 승인). 점검 항목:
- dead `[[링크]]`(대상 부재) / orphan(`index.md` 외 어느 페이지도 안 가리킴, inbound=0) / outbound 링크 <2.
- `index.md` ↔ `pages/**` 불일치(누락·잉여).
- frontmatter 필수 키 누락.
- 모순(`[!conflict]` 미해소)·stale(오래된 entity 버전) 후보.
- 구조 점검(dead/orphan/링크수/index 동기화)은 수동, 의미 점검(모순·stale)은 LLM. 자동화 `check_links.py` 는 MVP-2 예정(TODO).
결과를 분류해 보고 + 수정안 제시 + `log.md` append(`## [YYYY-MM-DD] lint | <요약>`).

## 경계
- 페이지 write 는 메인만. `raw/` 원문은 적재 후 편집·삭제하지 않음(불변).
- 자동 수정 안 함(lint 는 보고까지). 근거 없는 단정·추측 페이지 금지(CLAUDE.md §1).
- 코드 변경 아님 — dlc 와 분리. wiki 없으면 no-op.
