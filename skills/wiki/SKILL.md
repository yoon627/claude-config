---
name: wiki
description: 영속 프로젝트 메모리(LLM Wiki)를 운영하는 ingest/query/lint 오케스트레이션. 두 계층 — 현재 repo 의 `wiki/`(그 repo 의 결정·교훈)와 공용 `~/.claude/wiki/`(여러 repo 에 쓸모 있는 공개 가능한 사실·전역 자산의 교훈). raw 소스·작업 지식을 상호링크 markdown 페이지로 누적하고(ingest), 누적 페이지로 답하고(query), 무결성을 점검한다(lint). `/wiki <ingest|query|lint>` 명시 호출 시 사용. 단순 질문·코드 변경에는 쓰지 않는다(dlc/직접의 몫).
---

# wiki — LLM Wiki 운영 (영속 프로젝트 메모리)

wiki 는 두 계층이다(CLAUDE.md §11 이 배치 규칙의 단일 소스):
- **repo wiki** `<ROOT>/wiki/` — 그 repo 의 결정·교훈. 운영 규약은 그 wiki 의 `WIKI.md`.
- **공용 wiki** `~/.claude/wiki/` — 여러 repo 에 쓸모 있는 공개 가능한 사실과 전역 자산의 결정·교훈. 규약은 `~/.claude/wiki/WIKI.md`. **공개 repo** 라 아래 "공개 점검"을 통과한 내용만.

**현재 repo 판정**: `[ "$(git rev-parse --path-format=absolute --git-common-dir)" -ef "$HOME/.claude/.git" ]` 가 참이면 `~/.claude`(worktree 포함, `-ef` 라 `C:/`·`/c/`·심볼릭 링크 같은 표기 차이에 무관) — 두 계층이 같고, 쓰는 위치는 현재 checkout 의 `wiki/` 다(worktree 세션이면 worktree 사본). 아니면 "다른 repo"(비-git 디렉토리 포함). `git -C ~/.claude …` 로 판정하지 않는다(worktree 격리 가드가 거부한다).

시작 시 **대상 wiki 의 `WIKI.md` 를 반드시 read**. 이 skill 은 그 규약을 강제하는 실행 절차다. 어느 wiki 에 둘지는 §11, 페이지 형식은 대상 wiki 의 WIKI.md 가 정한다. 페이지 write 는 **메인만**(single-writer, `plans/` 와 동일 원칙). 충돌 시 CLAUDE.md 우선.

## 적용
- `/wiki ingest|query|lint` 명시 호출.
- dlc 연계(CLAUDE.md §11): 작업 시작 시 두 index 조회(있는 것만), 작업 후 재사용 지식의 대상 계층 판정·ingest 제안(자동 아님).
- 코드 변경·단순 질문은 제외.

## 인자 해석
| 입력 | 동작 |
|---|---|
| `ingest <경로\|설명>` | raw/지식 → 대상 wiki 페이지 갱신 + index/log |
| `query <질문>` | 두 index 에서 페이지 read 후 답, 가치 있으면 filed |
| `lint` | 현재 repo 의 wiki 무결성 점검·보고 |
| (빈 인자) | 두 `index.md` 요약 + 사용법 |

첫 토큰으로 분기. 모르는 서브커맨드는 사용법 안내 후 종료.

## 공개 점검 (공용 적립 작업이 공개하는 모든 것)
공용 wiki 는 공개 repo 에 있고 push 된 이력은 revert 로 지워지지 않는다. 금지 목록과 점검 표면(페이지·`sources`·index·log·`source/` 요약·plan·브랜치/worktree 이름·커밋 메시지·PR 제목/본문)은 **CLAUDE.md §11** 이 단일 정의다 — token/key/PII 는 늘 금지.
- 근거는 공개 검증 가능한 것(공식 문서 URL·공개 이슈·비공개 코드 없이 되는 재현)만 `sources` 에 싣는다. 비공개 코드 경로를 근거로 옮기지 않는다.
- `/wt` 로 worktree 를 만들 때 slug 도 공개된다(merge 커밋 메시지에 남는다) — 요약 문장이 아니라 일반화한 주제로 짓는다.
- 제안의 출처가 `비공개` 이거나 **출처가 적혀 있지 않으면**(불명 = 비공개로 본다) 커밋 전에 최종 diff 를 보이고 `AskUserQuestion`(없는 환경이면 채팅)으로 확인받는다(CLAUDE.md §1 외부공개).
- 걸리면 공용에서 빼고 출처 repo 의 wiki 로 돌린다.

## ingest
1. **대상 계층 판정**(§11): repo 고유 → repo wiki / 여러 repo 에 쓸모 있는 공개 가능한 사실·전역 자산 교훈 → 공용 / 비대상(사유). 애매하면 repo wiki. repo wiki 대상인데 repo wiki 가 없거나 비-git 이면 비대상 + 사유(공용 대상은 여전히 2단계 제안).
2. **다른 repo 에서 공용 대상**이면 쓰지 않는다: Report 와 출처 plan `# Deferred`(없으면 Report 만)에 `~/.claude 에서 /wt → /wiki ingest <요약 · 공개 근거 · 출처(공개/비공개)>` 를 남기고 끝낸다(§11 과 같은 형식). 출처 칸에는 `공개`/`비공개` 만 쓴다(비공개 repo 이름은 적지 않는다). 요약·근거는 위 공개 점검을 이미 통과한 문장이어야 한다.
3. `~/.claude` 에서 쓰는 경우 tracked 파일이라 `/wt` 로 만든 worktree 안에서 한다(CLAUDE.md §3-1). 무관한 작업이 진행 중인 worktree 에 얹지 않는다(그 작업과 같은 브랜치에서 갱신하는 경우는 된다).
4. 대상 wiki 의 `WIKI.md` read(규약 확인).
5. 원문이 주어지면 대상 wiki 의 `raw/`(없으면 mkdir) 에 보존(최초 1회, 이후 불변 — 편집·삭제 안 함) → `git check-ignore <wiki>/raw/<f>` 로 ignored 확인. raw 적재는 사용자 큐레이션 또는 ingest 입력에서만. worktree 에 둔 raw 는 gitignored 라 worktree 정리 때 경고 없이 지워진다 — 보존이 필요하면 정리 전에 옮긴다.
6. 원문 기반이면 `pages/source/<name>.md` 1:1 요약 생성(공용이면 공개 점검 — 비공개 원문의 요약은 공용에 두지 않는다).
7. 관련 `entity`(외부사실·버전)/`decision`(결정·교훈)/`concept` 페이지 갱신·생성. 한 ingest 가 여러 페이지 touch. 같은 사실이 이미 있으면 새 페이지 대신 갱신.
8. 각 페이지 규칙 충족: frontmatter, ≥2 outbound `[[링크]]`(같은 wiki 안의 페이지만 — 계층을 넘는 참조는 경로 텍스트 `~/.claude/wiki/pages/<cat>/<stem>.md`), sources, 모순은 `> [!conflict]`. **raw 적재·페이지 write 전 token/key/PII 점검 → 발견 시 마스킹/중단**(경고 후 진행 금지), 공용이면 공개 점검까지.
9. `index.md` 등재 + `log.md` append(`## [YYYY-MM-DD] ingest | <title>`).
10. `check_links.py` 로 구조 점검 후 보고. 공용 적립이면 커밋 전 공개 점검을 한 번 더(비공개 출처면 diff 확인).

## query
1. 두 `index.md`(현재 repo wiki, 공용 wiki — `~/.claude` 에서는 하나)에서 관련 페이지 식별 → read.
2. 페이지 기반으로 답(raw chunk 아님). 근거 페이지를 **어느 wiki 의 것인지와 함께** 인용.
3. 재사용 가치 있으면 **현재 repo 의 wiki** 에 `pages/query/<slug>.md` 로 filed(frontmatter+링크) + 그 wiki 의 `log.md` append. 공용 페이지가 근거인 답을 다른 repo 에서 filed 할 가치가 있으면 ingest 2단계의 공용 제안으로 돌린다. 공용 페이지는 비공개 repo 의 페이지를 가리키지 않는다.
4. 관련 페이지가 없으면 "wiki 에 없음" 명시(추측 금지). 필요 시 ingest 제안.

## lint
현재 repo 의 wiki 만(`~/.claude` 에서는 공용 wiki). 점검만, 자동 수정 안 함(수정은 보고 후 사용자 승인). 점검 항목:
- dead `[[링크]]`(대상 부재) / orphan(`index.md` 외 어느 페이지도 안 가리킴, inbound=0) / outbound 링크 <2.
- `index.md` ↔ `pages/**` 불일치(누락·잉여).
- frontmatter 필수 키 누락.
- 모순(`[!conflict]` 미해소)·stale(오래된 entity 버전) 후보. 공용 wiki 면 공개 점검 위반 후보도.
- 구조 점검(dead link·orphan·outbound<2·index 동기화·frontmatter)은 `check_links.py`(`uv run --no-project python "${CLAUDE_SKILL_DIR}/check_links.py" [wiki 경로]` — 인자가 없으면 현재 repo 의 wiki), 의미 점검(모순·stale·공개)은 LLM.
결과를 분류해 보고 + 수정안 제시 + `log.md` append(`## [YYYY-MM-DD] lint | <요약>`).

## 경계
- 페이지 write 는 메인만. `raw/` 원문은 적재 후 편집·삭제하지 않음(불변).
- 다른 repo 세션은 공용 wiki 에 쓰지 않는다(제안만). 공용 wiki 의 모든 write 는 공개 점검을 통과해야 한다.
- 자동 수정 안 함(lint 는 보고까지). 근거 없는 단정·추측 페이지 금지(CLAUDE.md §1).
- 코드 변경 아님 — dlc 와 분리. 현재 repo 에 wiki 가 없어도 공용 wiki 조회는 한다(쓰기는 비대상 + 사유).
