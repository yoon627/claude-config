# thin skills + prompt 슬림화 (이관=범위확대)

## Context
`/improve` 캡스톤 후 "thin prompt / thin skills / thick artifacts" 원칙을 실측하니 **thin skills 가 최약**: dlc 17KB·e 19KB·wt 15KB SKILL 이 상세 절차·메커닉·엣지 산문을 인라인에 안고 있어, 트리거 시 그 무게가 통째로 context 에 로드된다. 이건 doc-slim(#73)이 규칙손실0으로 ~11% 압축한 뒤 **명시적으로 defer 한 "이관을 통한 추가 압축 = 범위 확대"**([[ops-doc-slimming]]·[[deferred-and-scope-boundary]]) 작업이다.

**목표**: 각 SKILL/CLAUDE 의 *상세·메커닉·엣지*를 자동로드 안 되는 참조 doc 으로 이관하고, SKILL 은 얇은 오케스트레이션(게이트·닫힌목록·트리거)만 남긴다. **규칙 손실 0 = hard gate, bytes 감소 = 보조목표**(미달해도 규칙손실0 이면 통과).

## 핵심 제약 (ops-doc-slimming 교훈)
- **로드 등급 하락 = 손실.** SKILL 본문은 트리거 시 자동 로드되지만 `docs/*.md`·`references/*.md` 는 **모델이 명시 Read 할 때만** 로드된다. → **매 호출 조건판단 없이 적용돼야 하는 것(안전 게이트·트리거·닫힌 목록·단계 순서)은 인라인 유지**(이관하면 "Read 안 하면 조용히 누락"). **특정 분기에서만 찾는 상세(메커닉·폴백·엣지·예시)만 이관.**
- **이관 형태**(선례 `docs/codex-review.md`): 원본에 **명령형 1문장 + 절대경로 포인터 + "언제 Read"** 트리거 남김 → dangling 방지. 이관처 doc 상단에 **"이 파일은 자동 로드 안 됨 — <skill> 이 <조건>에서 Read"** 주의줄.
- CLAUDE.md 는 항상주입이라 위험 최고 — **안전/트리거 규칙 이관 금지**, 오직 *중복*(agents/·c/e SKILL 과 겹치는 스펙)만 참조화. `@import` 는 여전히 항상주입이라 토큰 절감 0(사용 안 함).

## Scope (사용자 확정: 스킬 3종 + prompt 안전 dedup)
자산별 **별도 PR**, 위험 낮은 순으로. 각 PR = wt→dlc + 규칙손실0 검증 + code-review(Claude+codex 병행).

### PR 1 — e SKILL → `docs/worktree-lifecycle.md` (최대 효과·저위험, ~7-8KB↓)
파일의 ~64%가 worktree/state 생명주기 메커닉.
- **인라인 유지(게이트/닫힌목록)**: 동작 6단계 개요 · `1.plan찾기` · `3.plan동기화` 필드 · `4.status판정`(done=사용자확인 게이트·recap) · **`임시 커밋 규칙` 안전게이트 전체**(main/master 직접커밋 금지 + `.env`/`.key`/`.pem`/`id_rsa` 위험파일 점검 — 절대 이관불가) · **`경계` 안전 닫힌목록** · `5.정리제안`의 **6조건 AND 닫힌목록 + "자동삭제 금지·항상 AskUserQuestion·collect-state 재수집 invariant·헬퍼실패면 생략(보수)"**.
- **이관(→ docs/worktree-lifecycle.md)**: `5.정리제안`의 merge 감지 메커닉(`inBase`/`patchInBase`/`git cherry`/`remoteContainingHead`/squash·rebase 한계/5(a)5(b) 폴백) · `worktree 정리 규칙` 실행 메커닉(값 캡처 순서·ExitWorktree no-op 폴백·`git worktree remove` stderr 분기) · `2.상태수집`의 17-필드 카탈로그·파싱 규칙(메커닉은 이미 `collect-state.sh`) · `6.복귀`의 main-autopull ⓑ 3-가드 상세.

### PR 2 — wt SKILL → `skills/wt/references/*.md` (저위험, ~2.3KB↓; doc-slim 미착수)
`request` 섹션(5.4KB, 파일의 36%)에 상세 집중.
- **인라인 유지**: `인자` 해석 순서(우선순위 단일소스) · `공통 규칙`(EnterWorktree path-only·slug 정규식) · `주의` · `rm` 안전검사 4종·미머지 탐지·"`--force`/`-D`/원격삭제 무확인 금지".
- **이관(→ skills/wt/references/)**: codegraph 문단(staleness 실측·projectPath 지침 → `codegraph-worktree.md`) · `.env` 복사 상세(ls-files 플래그·제외 정규식 → `env-copy.md`) · 생성 git 시퀀스·`rm` stderr 분기(→ `rm-recovery.md`). 잔존: 각 1줄 요약 + 포인터.

### PR 3 — dlc SKILL → `docs/dlc-details.md` (중위험·안전게이트 다수, ~5-6KB↓)
- **인라인 유지(절대)**: `진입 매트릭스` · **`dlc→wt` 필수 게이트(최고위험)** · `0.규모 gate` 표 · `structural 16단계 파이프라인` 표 · **`자기 진단` 중대 닫힌목록** · **`필수 산출물` recap+선택지 닫힌목록·정리 판정** · `codex phase owner`(이미 thin) · `요구사항 명확화` **4항 체크리스트 + fail-safe 트리거** · `Acceptance` 증거게이트 1줄 · `Workflow Findings` 3-트리거 + **자가수정 경계(§1)**.
- **이관(→ docs/dlc-details.md)**: 요구사항명확화 상세(blind-spot pass·프로토타입-우선·질문vs추천 경계·인터뷰식) · `조사 프로토콜`(디버깅 전용) · `wiki 연계` 상세(단 "판정 누락 금지" 1줄 잔존) · `Workflow Findings` 2곳 기록형식·hook 관계 · `Acceptance` verification-grounding 예시 · `격리 경계` runner 반환계약·cwd 경고·**simplify 체크리스트 나열**(13단계 도달 시만 봄).

### PR 4 — CLAUDE.md 안전 dedup (고위험·소효용, ~2KB↓; 게이트 전부 잔존)
**어떤 안전/트리거 규칙도 이관·삭제 안 함.** 오직 *중복 스펙*만 참조화:
- **§5 Sub-agent**: 4종 정의(plan/code/researcher/arch)는 `agents/*.md` 와 중복 → 이미 "상세는 agents/ 참조" 위임 중이니 정의 문장 감축, **트리거·표준순서 잔존**.
- **§10 plans 규약**: frontmatter 템플릿·6섹션 상세 스펙은 c/e SKILL 이 구현 → 스펙 세부 감축·참조, **"진행중 동기화 필수"·"완료 즉시 done"·secret 금지·6섹션 이름 잔존**.
- **§13**: §11·§12 를 재서술하는 중복 산문 순수 압축, **승인게이트·2단계저장·"대상 확대" 순증분 잔존**.
- **손대지 않음**: §1·§8 전체, §3 게이트 문장, §11·§12 판정 게이트.

## 규칙 손실 0 방법론 (매 PR 공통, doc-slim 손실방어 3겹)
1. **rule manifest**: 편집 전 그 자산의 모든 게이트·트리거·닫힌목록·안전규칙을 목록화(핵심 문구).
2. **1:1 대조**: `git diff -U0` 삭제 라인마다 → 새 위치(인라인 잔존 OR 이관 doc + 원본 포인터) 확인. **새 위치 없는 규칙 = dangling = 금지.**
3. **grep 세트**: manifest 핵심 문구가 (SKILL + 이관 doc) 합집합에 전부 존재하는지 grep.
4. **리뷰**: code-reviewer(Claude) + codex 병행 — 특히 "삭제 원문 중 새 위치 없는 규칙" 관점(doc-slim 에서 codex 가 dangling 3건 포착).

## Key Files
- 편집: `skills/{e,wt,dlc}/SKILL.md`, `CLAUDE.md`, `README.md`(문서 동기화)
- 신규 이관처: `docs/worktree-lifecycle.md`, `docs/dlc-details.md`, `skills/wt/references/{codegraph-worktree,env-copy,rm-recovery}.md`
- 참조 패턴 선례: `docs/codex-review.md`(형태 A), `skills/e/collect-state.sh`·`scripts/plan-lint.js`(형태 B)
- 제약 근거: `wiki/pages/decision/ops-doc-slimming.md`

## Verification (규칙손실0 = 완료 게이트)
- **기능 무손실 관찰**: 각 SKILL 흐름을 단계별로 짚어, 모든 분기가 (a) 규칙 인라인 OR (b) 이관 doc 로의 명시 포인터를 가지는지 확인. 포인터엔 "언제 Read" 트리거 명시.
- **manifest grep**: 각 자산의 안전/트리거/닫힌목록 문구가 편집 후 (SKILL+doc) 합집합에 100% 존재(0 dangling).
- **로직 불변 회귀**: 이관은 *문서만* — `collect-state.sh`·`plan-lint.js`·전 `scripts/*.test.js`·`improve.sh` 실행이 편집 전과 동일(스크립트 미변경). CI lint.yml 통과.
- **bytes(보조 관측)**: 각 SKILL·CLAUDE.md wc -c 전후 기록(하드 게이트 아님 — 규칙손실0 우선).
- **리뷰 통과**: PR 별 code-reviewer + codex, dangling 0 확인.
- 각 PR 머지 후 `/improve` 로 이관이 자산 정합(settings↔scripts·문서↔agents)을 안 깼는지 재확인.

## Progress
- 2026-07-17 **PR 1 done+merged (#89)**: `skills/e/SKILL.md` 19,118→13,132 B (−31%), 생명주기 메커닉 → `docs/worktree-lifecycle.md`(신규, 자동로드 안 됨). 규칙손실0 검증 = manifest grep 0 dangling + codex(Critical 없음) + Claude code-reviewer(안전게이트 16/16 인라인 잔존, APPROVE). README 리스트+트리 동기화. worktree/로컬·원격 브랜치 정리 완료, main=e7cda37.
- 2026-07-17 **PR 2 done+merged (#90)**: `skills/wt/SKILL.md` 14,975→12,687 B (−15%), request 생성/rm 메커닉 → `skills/wt/references/{env-copy,codegraph-worktree,rm-recovery}.md`(신규, 자동로드 안 됨). 규칙손실0 = manifest grep 0 dangling + codex(손실 없음) + Claude code-reviewer(인라인 8종 잔존·이관 baseline 완전 일치·안전규칙 doc-only 없음, APPROVE). README skills/wt 섹션+트리 동기화. worktree/로컬·원격 정리 완료, main=2bdb7a8.
- **사용자 승인 cadence**: 남은 PR3·4 는 각각 wt→dlc→리뷰(Claude+codex)→push→merge→정리 자동 진행(각 단계 보고, 문제 시 중단).
- 2026-07-17 **PR 3 done+merged (#91)**: `skills/dlc/SKILL.md` 17,146→15,482 B (−9.7%), 절차 상세(명확화 심화·조사 elaboration·wiki 메커닉·Workflow Findings 형식·격리 runner/simplify) → `docs/dlc-details.md` §A~§E(신규, 자동로드 안 됨). 규칙손실0 = manifest grep 0 dangling + codex(손실 없음) + Claude code-reviewer(인라인 16항 전수·이관 baseline 무왜곡, APPROVE). 두 리뷰 Minor(doc 게이트 중복) 반영해 doc §C/§E 를 how/why 로 좁힘. dlc 는 최다 게이트라 압축상한 낮음(ops-doc-slimming 교훈 일치). README 동기화. 정리 완료, main=cbadeb8.
- 2026-07-17 **PR 4 done+merged (#92)**: `CLAUDE.md` 23,584→23,326 B (−1.1%). §5 plan/code-reviewer 상세(agents/ 중복) 감축 + §13 §11/§12 재서술 압축. **§10 frontmatter/6섹션은 미변경** — c/e SKILL 이 참조하는 canonical always-injected 소스라(c/e 는 구현 안 하고 §10 을 가리킴) 트림 시 로드등급 하락 → plan 전제 부정확, rule-loss-0 우선으로 보존. 양측 리뷰 Critical/Major/Minor 0. 정리 완료, main=5372e88.

## Status: DONE (4/4 PR merged)
전 4 PR(#89 e·#90 wt·#91 dlc·#92 CLAUDE.md) 머지·정리 완료. **규칙 손실 0(hard gate) 전건 통과** — 각 PR manifest grep 0 dangling + code-reviewer(Claude)+codex 병행 양측 Critical/Major 0. 포인터 5종 전부 대상 실재. 총 감축: e −31%·wt −15%·dlc −9.7%·CLAUDE −1.1%(게이트 밀도↑ → 압축률↓, ops-doc-slimming 교훈 일치). bytes 는 보조목표였고 rule-loss-0 을 우선해 dlc/CLAUDE 는 보수적으로 멈춤.
