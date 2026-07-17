---
title: ops-doc-slimming
category: decision
created: 2026-07-14
updated: 2026-07-17
sources: [PR #73, 커밋 6b81a1a, plans/2026-07-04-doc-slim/doc-slim-plan.md, PR #89, PR #90, PR #91, PR #92, plans/giggly-petting-moonbeam.md]
---

# ops-doc-slimming — 항상 주입 운영 문서 토큰 최적화 규약

매 세션/작업마다 로드되는 운영 문서(CLAUDE.md·핵심 [[dlc-development-cycle]] SKILL·agent 정의)의 토큰을 줄일 때의 결정·교훈. doc-slim 작업(PR #73, 2026-07-05)에서 도출.

## 실측 상한 ~11%
규칙 손실 0(hard gate)을 지키면서 산문·중복·사례·괄호부연·경위서술을 **전부** 걷어내도, 규칙 밀도가 높은 항상-주입 문서의 압축 상한은 실측 **~11%**다. 4대 타깃 합계 70,596 → 62,706B(11.2%↓ — CLAUDE.md·skills/dlc·skills/e·agents/architecture-reviewer). 이 문서들이 이미 "압축된 규칙 명세"라 걷어낼 산문 자체가 적기 때문. 애초 목표였던 30%+ 는 규칙 밀도상 도달 불가로 판정.

## 30%+ 는 왜 불가한가
30%+ 감소는 다음 중 하나 없이는 불가하며, 둘 다 "슬림화"가 아니라 범위 확대다:
- **규칙 통합/재구조화** — 중복·과세분 규칙을 하나로. SKILL/agent/docs 는 내부 통합 허용, **CLAUDE.md 항상주입 규칙은 내부 표현 압축만**(의미·로드 등급 보존).
- **조건부-로드 문서로의 이관** — 항상주입(CLAUDE.md) → 조건부 로드(skill/docs/wiki). 그러나 이관은 로드 등급을 낮추는 것이라 안전/실행/트리거 규칙에는 그 자체가 손실(아래).

## "규칙 손실 0" 정의에 로드 등급 하락 포함
규칙 손실 0 은 텍스트 존재만이 아니라 **로드 등급 보존**을 포함한다. 안전/실행/트리거 규칙([[codex-bash-invocation]] codex=Bash 강제·dlc 필수·worktree 먼저·main 직접 금지 등)을 조건부-로드 문서로 옮기면 "항상 주입 → 조건부 로드"가 되어 손실이다. → CLAUDE.md 에 명령형 1문장을 반드시 잔존시키고 세부만 참조화(dangling 방지).

## 결정: bytes 목표를 hard gate 로 걸지 말 것
bytes 감소를 hard gate 로 두면 규칙을 배경위장·참조화로 밀어내는 **삭제 압력**이 생긴다. → **규칙 손실 0 을 hard gate**, bytes 감소는 **보조목표로 격하**한다(충돌 시 규칙 보존 우선, 미달해도 규칙 손실 0 이면 통과). [[evidence-gate]] 의 hard-gate 사고와 정합.

## 손실 방어 절차
- **사후탐지 3겹**: 삭제-diff manifest 1:1 대조 · 핵심 문구 grep 세트 · reviewer 전용 "삭제 원문 중 새 위치 없는 규칙만" + 완료 후 `git diff -U0` 삭제 라인 규칙 관점 재검토.
- [[claude-codex-collaboration]] code-reviewer(APPROVE) + codex 병행 — 실제로 codex 가 규칙 손실 3건(arch 실패 fallback 환경이슈 dangling·CLAUDE Setup "레포 작업"·dlc "16단계 표 불변")을 포착, 전부 fix.
- 이관을 통한 추가 압축은 [[deferred-and-scope-boundary]] 의 범위 경계를 넘으므로 별도 작업으로 분리한다.

## 후속 이관 실행 — thin skills slim (PR #89-92, 2026-07-17)
위에서 defer 한 "이관을 통한 추가 압축"을 실제 수행(e/wt/dlc SKILL·CLAUDE.md, PR 별 분리). 확립된 사실:

- **압축률은 규칙 밀도에 반비례**(실측): e SKILL −31% · wt −15% · dlc −9.7% · CLAUDE.md −1.1%. 게이트·트리거·닫힌목록이 조밀할수록 인라인 유지분이 커져 rule-loss-0 하 압축상한이 낮아진다. dlc·CLAUDE 는 게이트 보존 위해 보수적으로 멈춤(plan 의 byte 추정 미달을 감수 — bytes 는 보조목표).
- **이관 방향이 중요 — dependency inversion 금지**: 조건부-로드 skill(예 c/e)이 *참조하는* canonical always-injected 스펙(예 CLAUDE.md §10 plan frontmatter/6섹션)을 그 skill 로 "이관"하는 것은 방향 역전이다. 참조원이 조건부 로드라 그 skill 미호출 세션은 스펙을 잃는다(로드 등급 하락 = 손실). → §10 은 미변경 보존. plan 의 "c/e 가 §10 을 구현" 전제가 부정확했고(실제는 c/e→§10 참조), rule-loss-0 이 이를 잡아냈다. "로드 등급 하락 = 손실" 원칙(이 페이지 상단)의 특수 케이스.
- **이관 형태(선례 확립)**: 원본에 명령형 1문장 + 절대경로 포인터 + "언제 Read" 트리거 잔존, 이관 doc 상단에 "자동 로드 안 됨" 주의줄. 신규 참조 doc: `docs/worktree-lifecycle.md`·`docs/dlc-details.md`·`skills/wt/references/{env-copy,codegraph-worktree,rm-recovery}.md`.
- **방법론(매 PR 공통)**: 이관 전 rule manifest 작성 → `git diff -U0` 삭제 라인마다 새 위치(인라인 OR 이관doc+포인터) 대조 → (SKILL∪doc) 합집합 manifest grep **0 dangling** → [[claude-codex-collaboration]] code-reviewer(Claude)+codex 병행 dangling 관점. 4 PR 전건 양측 Critical/Major 0.
