# LLM Wiki (Andrej Karpathy)

> LLM 이 raw 소스를 읽어 상호링크된 markdown wiki 를 **점진적으로 구축·유지**하는 개인 지식베이스 패턴.
> RAG 의 "매 쿼리마다 재검색·재합성 후 소멸" 대신, **한 번 컴파일해 누적되는(compounding) 지속 artifact** 를 만든다.

출처: Andrej Karpathy 가 2026-04-04 GitHub gist 로 공개한 "idea file". 정리일: 2026-06-15.

---

## 1. 한 줄 정의

> "Most people's experience with LLMs and documents looks like RAG ... Instead, with the LLM Wiki, the approach replaces retrieve-at-query-time RAG with a persistent, LLM-maintained knowledge base that compounds with every source you add."

- 인간 역할: **소스 큐레이션 · 좋은 질문 · 의미 사고**
- LLM 역할: **작성 · 상호참조 · 유지보수(bookkeeping)**
- 핵심 통찰: *"지식베이스 유지에서 고된 부분은 읽기·사고가 아니라 bookkeeping(상호참조·정리)이다."* → 이 bookkeeping 을 LLM 이 지치지 않고 처리한다.

---

## 2. 배경 — "idea file" 과 Memex

### idea file 철학
Karpathy 는 구현 코드(repo·npm·Docker)가 아니라 **아이디어 자체**를 gist 로 공유했다.

> "in this era of LLM agents, there is less of a point/need of sharing the specific code/app, you just share the idea, then the other person's agent customizes & builds it for your specific needs."

→ 문서는 **의도적으로 추상적**이다. 그대로 자신의 agent (Claude Code · Codex · OpenCode 등)에게 건네면, agent 가 사용자의 도메인에 맞춰 구체 구현을 함께 빚는다.

### 계보: Vannevar Bush 의 Memex (1945)
큐레이션된 개인 지식 저장소라는 아이디어는 Bush 의 Memex 로 거슬러 올라간다. Bush 가 풀지 못한 문제는 **"상호참조 유지보수를 누가 하는가"** 였다. LLM Wiki 는 그 유지보수를 LLM 이 자동으로 떠맡게 하여 이 문제를 해소한다.

---

## 3. RAG 와의 차이

| 항목 | RAG | LLM Wiki |
|---|---|---|
| 지식 누적 | 없음 — 매 쿼리마다 재합성 후 소멸 | **누적·복리** — 한 번 컴파일해 유지 |
| 쿼리 시 입력 | raw 문서 chunk | 전처리·구조화·상호링크된 wiki page |
| 모순 처리 | 충돌 chunk 를 정렬 없이 반환 | ingest 시점에 **flag** |
| 셋업 복잡도 | 중간 (vector DB, embedding) | 낮음 ("그냥 파일 + LLM") |
| 환각 리스크 | chat 에 머물고 사라짐 | **wiki 에 기록되면 근거로 재인용될 수 있음** → 인간 리뷰가 더 중요 |
| 적합 영역 | 대규모 문서 집합, FAQ 조회 | 능동적으로 관심 갖는 **수십~수백 개** 소스 |
| 스케일 | vector 로 확장 | ~150 소스 초과 시 context 한계로 미묘한 multi-page 연결 누락 가능 |

핵심 한 줄: RAG 의 근본 한계는 **"nothing accumulates"** — 매번 바닥부터 합성하고 사라진다. Wiki 는 합성을 **한 번 컴파일해 누적**한다.

---

## 4. 아키텍처 — 3개 레이어

1. **Raw sources** (사용자 소유, 불변)
   - 기사·논문·트랜스크립트를 markdown 으로 저장한 디렉토리.
   - LLM 은 **읽기만** 하고 절대 수정하지 않는다 → 원본 보존으로 나중에 wiki 의 해석과 원문을 대조 가능.

2. **The wiki** (LLM 소유)
   - 전부 LLM 생성 markdown. "You read it; the LLM writes it."
   - 구성: 소스 요약 page · entity page(인물·모델·조직·데이터셋) · concept page · overview/synthesis page · filed query 답변 · `index.md` · `log.md`.

3. **The schema** (설정)
   - `CLAUDE.md` (Claude Code) 또는 `AGENTS.md` (Codex). **이름은 무관, 내용이 연속성을 만든다.**
   - 일반 챗봇을 "disciplined wiki maintainer" 로 바꾼다: 디렉토리 layout · naming convention · frontmatter · workflow 정의 → **세션 간 일관성** 보장.

> 멘탈 모델: **"Obsidian 은 IDE, LLM 은 프로그래머, wiki 는 codebase."**

---

## 5. 3개 연산

### Ingest (수집)
`raw/` 에 소스를 넣고 처리를 지시. LLM 이 읽고 → 강조점을 사용자와 논의 → 요약 page 생성 → 관련 entity/concept/overview page 갱신 → `index.md` 갱신 → `log.md` append.
- 한 번의 ingest 가 보통 **10~15개 page 를 touch**.
- Karpathy 는 framing 을 맞추기 위해 **loop 에 남아 있는 것**(in-the-loop)을 선호.

### Query (질의)
RAG 와 달리 LLM 이 **전처리·구조화·상호링크된 wiki page** 를 읽는다(raw chunk 가 아님). 입력이 좋아서 답도 좋아진다.
- 좋은 답변은 **new query page 로 filed** → 합성 결과가 chat 히스토리에 묻혀 사라지지 않는다.

### Lint (정리/건강검진)
주기적(예: 2~4주)으로 실행. orphan page · 모순 · superseded(낡아 대체된) claim · 누락된 concept page 를 스캔해 수정안을 보고.
- 추가로 **새 질문 · 찾아볼 새 소스**도 제안 가능.

---

## 6. 보조 파일

- **`index.md`** — content catalog. 모든 page 가 1줄 요약 + 카테고리로 등재. ~100 소스까지는 embedding 없이 **index-first 탐색**이 가능. 더 커지면 옵션 도구 [`qmd`](https://github.com/tobi/qmd) 로 로컬 hybrid(BM25/vector) 검색 보조.
- **`log.md`** — append-only 시간순 기록. 모든 ingest · filed query · lint pass 를 남긴다. 엔트리는 `## [YYYY-MM-DD] operation | title` 형식이라 **greppable**. "스스로 쓰여지는 research diary".

---

## 7. 링크 규칙

- Obsidian 호환 `[[page-name]]` wiki link 사용.
- sample schema 의 규칙 예:
  - "모든 page 는 **최소 2개**의 관련 page 에 링크한다."
  - "모든 claim 은 소스를 인용한다."
- 모순 · open question 은 기존 claim 을 조용히 덮어쓰지 않고 **전용 callout block 으로 flag**.

---

## 8. 실전 워크플로우 팁

- 터미널(좌) + Obsidian(우) 두 창을 나란히 두고, 파일이 바뀌는 것을 **실시간으로** 읽는다.
- schema 에 처음 **~30분** 투자하고, 도메인을 알아가며 함께 진화(co-evolve)시킨다.
- 소스는 신선할 때 **같은 날 ingest**. 복리(compounding)는 **5번째 ingest 쯤** 체감되기 시작한다.
- wiki 는 git-tracked → 실수 복구 가능 + 무료 버전 히스토리.

---

## 9. 사용 사례

개인 추적 · 리서치 · 책 읽기(팬 wiki 처럼) · 비즈니스/팀 지식베이스 · 경쟁 분석 · 여행 계획 등. Karpathy 본인은 토픽별 **~100개 article** 규모의 wiki 를 운영.

---

## 10. 한계 / 주의

- **환각의 영속화**: RAG 의 환각은 chat 에 머물지만, Wiki 에서는 환각이 page 에 기록되어 이후 쿼리에서 **근거로 재인용**될 수 있다 → 인간 리뷰가 더 중요.
- **스케일 한계**: ~150 소스를 넘으면 context window 한계로 미묘한 multi-page 연결이 누락될 수 있다(인덱싱 보조 필요). "400,000 단어 부근에서 잘 동작하지만 그 이상은 indexing aid 없이는 흔들릴 수 있다"는 지적.
- 문서는 의도적으로 추상적 — 구체 구현은 각자 agent 와 함께 만든다(모든 것이 optional·modular).

---

## 11. 커뮤니티

- 여러 구현체가 등장 (예: `wpzero/karpathy-llm-wiki`).
- gist 코멘트에서 **context vs RAG tradeoff** 논쟁(코퍼스 크기 기준)이 이어짐.

---

## 출처

- 원문 gist — Karpathy, "llm-wiki": <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
- Full Breakdown (Nandigam Harikrishna): <https://nandigamharikrishna.substack.com/p/andrej-karpathys-llm-wiki-full-breakdown>
- 구현 예시 (wpzero): <https://github.com/wpzero/karpathy-llm-wiki>
- qmd (로컬 검색 도구, Tobi Lütke): <https://github.com/tobi/qmd>
- 배경 개념 — Vannevar Bush, "As We May Think" (1945), Memex
